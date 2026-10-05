"""Daily OHLCV retrieval with an on-disk cache (SCOPE 2).

The cache exists so a yfinance outage degrades to STALE data rather than NO
data. Two files per ticker under data/cache/:

    <TICKER>.csv        the raw daily frame as returned by yfinance
    <TICKER>.meta.json  fetch timestamp, row count, and the period requested

Failure is always loud and always per-ticker: a ticker that errors comes back
with ``error`` set and is reported as an ERROR row. It is never dropped.

IMPORTANT: ``fetched_at`` describes when we last *talked to* yfinance. It is
never used for the staleness gate -- that gate reads the newest close DATE out
of the price series itself, so serving a stale cache cannot look fresh.
"""

from __future__ import annotations

import json
import math
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Mapping

import pandas as pd

log = logging.getLogger(__name__)

#: FRAMEWORK-EDITS E52 (2026-08-27) raised this from "2y". The listing-age
#: floor is five years and is measured from the STORED SERIES, so a two-year
#: fetch would reject the entire universe on its own fetch parameter. Every
#: consumer truncates to its own `as_of`, so a longer window is never a
#: longer answer -- only a series that can be asked how old it is.
#:
#: SIX, NOT FIVE, AND THE EXTRA YEAR IS A MARGIN RATHER THAN A PREFERENCE.
#: The vendor measures its window from TODAY and `as_of` is at or before
#: today, so a "5y" fetch reaches exactly five years back from today and is
#: SHORT of five years back from any earlier `as_of`. Measured 2026-08-27:
#: a 5y fetch began 2021-08-27, the floor for `--asof 2026-08-26` was
#: 2021-08-26, and all 1,328 names that reached the step were rejected --
#: by one day, on the run's own fetch parameter. This is the same margin
#: `metrics.COVERAGE_MARGIN_TRADING_DAYS` exists for: a window that exactly
#: reaches a bar does not cover it.
DEFAULT_PERIOD = "6y"

#: auto_adjust=False keeps Close split-adjusted but NOT dividend-adjusted, so
#: last_close matches the quote the user sees in their broker -- which is the
#: basis on which they hand-set stop_price and fv_base.
AUTO_ADJUST = False

SOURCE_LIVE = "live"
SOURCE_CACHE = "cache"
SOURCE_NONE = "none"


@dataclass(frozen=True)
class FetchResult:
    ticker: str
    frame: pd.DataFrame | None
    source: str
    fetched_at: datetime | None = None
    error: str | None = None
    #: E122(e): rows kept although the latest response dropped or blanked
    #: them, by date.
    retained: "Mapping[date, Retained]" = field(default_factory=dict)
    #: E122(c)/(d): what the vendor restated this run, applied or refused.
    corrections: tuple = ()

    @property
    def ok(self) -> bool:
        return self.frame is not None and len(self.frame) > 0

    @property
    def degraded(self) -> bool:
        """Live fetch failed but cached data was available."""
        return self.source == SOURCE_CACHE and self.error is not None


def safe_name(ticker: str) -> str:
    """Filesystem-safe cache stem, e.g. 'BRK-B' -> 'BRK-B', 'A/B' -> 'A_B'."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", ticker).strip("._") or "_"


def cache_paths(cache_dir: Path, ticker: str) -> tuple[Path, Path]:
    stem = safe_name(ticker)
    return cache_dir / f"{stem}.csv", cache_dir / f"{stem}.meta.json"



# =========================================================================
# E122 (owner, 2026-09-20) -- A PRICE WE HAVE HELD IS NOT RETRACTABLE BY
# THE VENDOR'S SILENCE.
#
# The cache was a BLIND WHOLE-FILE OVERWRITE (`frame.to_csv(path)`), and on
# 2026-09-19 that destroyed closes the 2026-09-18 nightly had already seen,
# stored and printed: no 2026-09-17 row and a NaN close on 2026-09-18 came
# back for twelve continental-European names, and the overwrite took the
# good rows with it. The scan of that morning: 22 (ticker, date) pairs lost,
# all on 09-17 and 09-18, none older.
#
# The rules, all binding:
#   (a) the cache is a UNION BY DATE -- a date once held is never removed by
#       a later response that omits it;
#   (b) a blank, NaN or absent close NEVER overwrites a held close, under
#       any path;
#   (c) a DIFFERING NON-BLANK close for a held date is a CORRECTION, not
#       silence, and it DOES apply -- both values, both dates and the source
#       go to the log and into the next report;
#   (d) EXCEPT where the correction moves the close ACROSS A LEVEL the name
#       carries, in either direction: that one does not apply silently. It
#       blocks the name and asks. A revision that quietly un-crosses an MBP
#       is what this mechanism exists to stop;
#   (e) a row retained after the vendor dropped or blanked it is MARKED
#       retained, with the date first seen, wherever the close appears;
#   (f) staleness is measured against the newest close HELD;
#   (g) no write path may replace a file of dated rows wholesale.
# =========================================================================


@dataclass(frozen=True)
class Correction:
    """A held close that the vendor now states differently (E122 c/d)."""

    when: date
    held: float
    incoming: float
    applied: bool
    #: the level it moved across, and its value, where it did (E122 d)
    crossed: tuple[str, float] | None = None

    def line(self) -> str:
        what = (f"crosses {self.crossed[0]} {self.crossed[1]:,.2f}"
                if self.crossed else "crosses no level")
        did = "applied" if self.applied else "NOT APPLIED -- the name is blocked and asks"
        return (f"{self.when.isoformat()}: held {self.held:,.4f} -> vendor "
                f"{self.incoming:,.4f} ({what}); {did}")


@dataclass(frozen=True)
class Retained:
    """A row kept although the latest response dropped or blanked it."""

    when: date
    first_seen: date
    since: date
    source: str = "cache"

    def line(self) -> str:
        return (f"{self.when.isoformat()} close retained (first seen "
                f"{self.first_seen.isoformat()}; the vendor has not carried "
                f"it since {self.since.isoformat()})")


def _as_date(value) -> date:
    stamp = pd.Timestamp(value)
    return stamp.date()


def _blank(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value)


def crossed_level(held: float, incoming: float,
                  levels: "Mapping[str, float] | None") -> tuple[str, float] | None:
    """The first level the move from ``held`` to ``incoming`` crosses (E122 d).

    A level exactly touched at either end counts: a close AT the MBP is a
    crossing in this framework, so a revision onto or off the line is the
    case the rule is about.
    """
    if not levels:
        return None
    low, high = min(held, incoming), max(held, incoming)
    for name, level in sorted((levels or {}).items()):
        if level is None:
            continue
        if low <= float(level) <= high:
            return name, float(level)
    return None


def merge_series(held: "pd.DataFrame | None", incoming: pd.DataFrame, *,
                 levels: "Mapping[str, float] | None" = None,
                 retained_before: "Mapping[str, Retained] | None" = None,
                 as_of: date | None = None
                 ) -> tuple[pd.DataFrame, dict[date, Retained], tuple[Correction, ...]]:
    """E122's union. Returns the merged frame, its retained rows and the
    corrections the vendor made, applied or refused."""
    as_of = as_of or date.today()
    retained_before = retained_before or {}
    if held is None or len(held) == 0:
        return incoming, {}, ()

    held_rows = {_as_date(i): row for i, row in held.iterrows()}
    incoming_rows = {_as_date(i): row for i, row in incoming.iterrows()}
    retained: dict[date, Retained] = {}
    corrections: list[Correction] = []

    out_rows: dict[date, object] = {}
    for when, row in incoming_rows.items():
        held_row = held_rows.get(when)
        if held_row is None:
            out_rows[when] = row
            continue
        held_close, incoming_close = held_row.get("Close"), row.get("Close")
        if _blank(incoming_close) and not _blank(held_close):
            # (b) a blank never overwrites a held close.
            row = row.copy()
            row["Close"] = held_close
            out_rows[when] = row
            mark = retained_before.get(when)
            retained[when] = Retained(when, mark.first_seen if mark else when,
                                      mark.since if mark else as_of,
                                      mark.source if mark else "cache")
            continue
        if not _blank(held_close) and not _blank(incoming_close) and \
                abs(float(held_close) - float(incoming_close)) > _CORRECTION_EPSILON:
            crossed = crossed_level(float(held_close), float(incoming_close), levels)
            if crossed is not None:
                # (d) it does NOT apply; the held close stands and the name
                #     is blocked until the owner rules.
                row = row.copy()
                row["Close"] = held_close
                corrections.append(Correction(when, float(held_close),
                                              float(incoming_close), False, crossed))
            else:
                corrections.append(Correction(when, float(held_close),
                                              float(incoming_close), True, None))
        out_rows[when] = row

    for when, row in held_rows.items():
        if when in out_rows:
            continue
        # (a) a date once held is never removed by a response that omits it.
        out_rows[when] = row
        mark = retained_before.get(when)
        retained[when] = Retained(when, mark.first_seen if mark else when,
                                  mark.since if mark else as_of,
                                  mark.source if mark else "cache")

    order = sorted(out_rows)
    frame = pd.DataFrame([out_rows[w] for w in order],
                         index=pd.DatetimeIndex([pd.Timestamp(w) for w in order]))
    frame.index.name = incoming.index.name or "Date"
    return frame, retained, tuple(corrections)


#: Below this, two closes are the same print, not a correction.
_CORRECTION_EPSILON = 5e-5


def retained_paths(cache_dir: Path, ticker: str) -> Path:
    return cache_dir / f"{safe_name(ticker)}.retained.json"


def read_retained(cache_dir: Path, ticker: str) -> dict[date, Retained]:
    """The retention marks beside the cached series (E122 e).

    A SIDECAR rather than a column: the cached CSV is read by several
    callers as a numeric frame, and a text column in it would be a change
    every one of them has to survive.
    """
    path = retained_paths(cache_dir, ticker)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 -- a mark is never load-bearing
        log.warning("%s: retention marks unreadable (%s)", ticker, exc)
        return {}
    # KEYED BY DATE, like the merge's own marks: `build_row` looks a mark up
    # by the close's date, and string keys here meant the RETAINED mark
    # silently vanished on a CACHE-SERVED run (2026-09-20).
    out = {}
    for when, item in (raw or {}).items():
        try:
            out[date.fromisoformat(when)] = Retained(date.fromisoformat(when),
                                 date.fromisoformat(item["first_seen"]),
                                 date.fromisoformat(item["since"]),
                                 item.get("source", "cache"))
        except Exception:  # noqa: BLE001
            continue
    return out


def write_retained(cache_dir: Path, ticker: str, marks: "Mapping[date, Retained]") -> None:
    path = retained_paths(cache_dir, ticker)
    if not marks:
        path.unlink(missing_ok=True)
        return
    cache_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {w.isoformat(): {"first_seen": m.first_seen.isoformat(),
                         "since": m.since.isoformat(), "source": m.source}
         for w, m in sorted(marks.items())}, indent=2) + "\n", encoding="utf-8")


def write_cache(cache_dir: Path, ticker: str, frame: pd.DataFrame,
                fetched_at: datetime, *, levels: "Mapping[str, float] | None" = None,
                as_of: date | None = None
                ) -> tuple[pd.DataFrame, dict[date, Retained], tuple[Correction, ...]]:
    """MERGE ``frame`` into the cached series and write the union (E122).

    THIS IS THE ONLY WRITER OF A CACHED SERIES, and it never replaces a file
    of dated rows wholesale: what it writes is `merge_series` of what is
    held with what arrived. `frame.to_csv` on a cache path appears here and
    nowhere else, by test.
    """
    csv_path, meta_path = cache_paths(cache_dir, ticker)
    held, _ = read_cache(cache_dir, ticker)
    merged, retained, corrections = merge_series(
        held, frame, levels=levels,
        retained_before=read_retained(cache_dir, ticker),
        as_of=as_of or fetched_at.date())
    cache_dir.mkdir(parents=True, exist_ok=True)
    merged.to_csv(csv_path)
    write_retained(cache_dir, ticker, retained)
    meta_path.write_text(
        json.dumps(
            {
                "ticker": ticker,
                "fetched_at": fetched_at.isoformat(timespec="seconds"),
                "rows": int(len(merged)),
                "period": DEFAULT_PERIOD,
                "auto_adjust": AUTO_ADJUST,
                "retained": len(retained),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return merged, retained, corrections


def read_cache(cache_dir: Path, ticker: str) -> tuple[pd.DataFrame | None, datetime | None]:
    csv_path, meta_path = cache_paths(cache_dir, ticker)
    if not csv_path.exists():
        return None, None
    try:
        frame = pd.read_csv(csv_path, index_col=0)
        # Rebuild the index as naive local dates. A CSV that spans a DST
        # change carries mixed UTC offsets, which parse_dates=True cannot
        # handle; keeping each row's own wall-clock date is what we want.
        frame.index = pd.DatetimeIndex(
            [pd.Timestamp(v).tz_localize(None) if pd.Timestamp(v).tzinfo else pd.Timestamp(v)
             for v in frame.index]
        )
    except Exception as exc:  # a corrupt cache must not be silently reused
        log.warning("%s: cached file unreadable (%s)", ticker, exc)
        return None, None

    if len(frame) == 0 or "Close" not in frame.columns:
        log.warning("%s: cached file has no usable rows, ignoring it", ticker)
        return None, None

    fetched_at = None
    if meta_path.exists():
        try:
            fetched_at = datetime.fromisoformat(
                json.loads(meta_path.read_text(encoding="utf-8"))["fetched_at"]
            )
        except Exception:  # metadata is a convenience, never load-bearing
            fetched_at = None
    return frame, fetched_at


_yf_cache_configured = False


def configure_yf_cache(base_dir: Path, create: bool = True) -> None:
    """Point yfinance's timezone/cookie cache inside the project.

    yfinance defaults to ~/.cache/py-yfinance. Under the hardened systemd
    unit -- or any cron job with a different HOME -- that path is not
    writable, and yfinance then silently runs with no timezone cache and no
    cookie reuse, which means more requests and a higher chance of being
    rate-limited. Keeping it beside our own cache makes runs identical
    however they are launched.
    """
    global _yf_cache_configured
    if _yf_cache_configured:
        return
    target = base_dir / "yf-cache"
    try:
        if create:
            target.mkdir(parents=True, exist_ok=True)
        if target.is_dir():
            import yfinance as yf

            yf.set_tz_cache_location(str(target))
            _yf_cache_configured = True
    except Exception as exc:  # never let a cache preference break a run
        log.debug("could not set yfinance cache location: %s", exc)


def fetch_live(ticker: str, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
    """Ask yfinance for daily OHLCV. Raises on failure or empty response."""
    import yfinance as yf

    frame = yf.Ticker(ticker).history(period=period, interval="1d", auto_adjust=AUTO_ADJUST)
    if frame is None or len(frame) == 0:
        raise RuntimeError("yfinance returned no rows (unknown, delisted or rate-limited ticker)")
    if "Close" not in frame.columns:
        raise RuntimeError(f"yfinance response missing Close column: {list(frame.columns)}")
    return frame


def get_history(
    ticker: str,
    cache_dir: Path,
    *,
    now: datetime,
    allow_network: bool = True,
    write: bool = True,
    period: str = DEFAULT_PERIOD,
    #: E122(d): the levels this name carries, so a correction that moves a
    #: close ACROSS one is refused rather than applied silently.
    levels: "Mapping[str, float] | None" = None,
) -> FetchResult:
    """Live data if we can get it, cached data if we cannot, an error if neither."""
    if not allow_network:
        frame, fetched_at = read_cache(cache_dir, ticker)
        if frame is not None:
            log.info("%s: offline, serving cache from %s", ticker, fetched_at)
            return FetchResult(ticker, frame, SOURCE_CACHE, fetched_at,
                               retained=read_retained(cache_dir, ticker))
        log.error("%s: offline and no cached data", ticker)
        return FetchResult(ticker, None, SOURCE_NONE, None, "offline and no cached data")

    configure_yf_cache(cache_dir.parent, create=write)

    try:
        frame = fetch_live(ticker, period)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        log.error("%s: live fetch failed -- %s", ticker, error)
        frame, fetched_at = read_cache(cache_dir, ticker)
        if frame is not None:
            log.warning("%s: falling back to cache fetched %s", ticker, fetched_at)
            return FetchResult(ticker, frame, SOURCE_CACHE, fetched_at, error,
                               retained=read_retained(cache_dir, ticker))
        return FetchResult(ticker, None, SOURCE_NONE, None, error)

    # E122: the response is MERGED into what is held -- always, whether or
    # not the cache is written. A dry run that read the vendor's ragged
    # frame straight would report a staleness the merged series does not
    # have, which is the defect this ruling closes.
    held, _ = read_cache(cache_dir, ticker)
    merged, retained, corrections = merge_series(
        held, frame, levels=levels,
        retained_before=read_retained(cache_dir, ticker),
        as_of=now.date())
    if write:
        try:
            merged, retained, corrections = write_cache(
                cache_dir, ticker, frame, now, levels=levels)
        except Exception as exc:  # a cache write failure must not lose the run
            log.warning("%s: could not write cache (%s)", ticker, exc)
    for mark in retained.values():
        log.info("%s: %s", ticker, mark.line())
    for correction in corrections:
        log.warning("%s: PRICE CORRECTION %s", ticker, correction.line())
    log.info("%s: fetched %d rows (%d retained)", ticker, len(merged), len(retained))
    return FetchResult(ticker, merged, SOURCE_LIVE, now,
                       retained=retained, corrections=corrections)
