"""Orchestration: load watchlist -> fetch -> compute -> assess -> report.

All I/O lives here and in fetch/store/report. rules.py and metrics.py stay pure.
"""

from __future__ import annotations

import contextlib
import json
import logging
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from . import heartbeat as HB
from . import metrics as M
from . import series_sanity
from .config import WatchlistEntry, load_watchlist
from .fetch import FetchResult, get_history, safe_name
from .report import render
from .calendars import MarketCalendars, load_market_calendars
from .rules import (MAX_CLOSE_AGE_TRADING_DAYS_LEVEL, NO_DATA, PRICE_CORRECTION,
                    STALE_DATA, TickerAssessment, assess, carries_level,
                    compute_mbp_e90, trading_days_between, unchecked_levels)
from .refresh import needs_owner as refresh_needs_owner
from .refresh import notification_lines, post_needs_owner
from . import pricewatch as PW
from .runrecord import RecordError, RunRecord
from .store import persist, previous_mbps

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WATCHLIST_PATH = PROJECT_ROOT / "config" / "watchlist.yaml"
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
DB_PATH = PROJECT_ROOT / "data" / "vss.sqlite"
REPORTS_DIR = PROJECT_ROOT / "reports"


@dataclass(frozen=True)
class TickerRow:
    entry: WatchlistEntry
    metrics: M.Metrics
    assessment: TickerAssessment
    source: str
    fetched_at: datetime | None
    error: str | None
    pct_to_mbp: float | None
    pct_to_stop: float | None
    #: K4: why the price series cannot be measured, or None. Struck by
    #: `series_sanity.check` over the same window the drawdown reads. When
    #: set, the stop, MBP and dislocation checks are DATA MISSING -- this is
    #: the "one-call fix" REVIEW-4 report B #7 named and golden case G14
    #: pinned as NOT wired, now wired.
    series_finding: str | None = None
    #: Build 2 item 9: the fair value THIS RUN PRINTS -- the entry's
    #: `fv_base` when a complete run record replays to it, else None.
    fv_base: float | None = None
    #: Why `fv_base` is not printed, or None when it is (or none is set).
    fv_refused: str | None = None
    #: E28: the linked record struck at its PRE-REGISTERED bear case -- the
    #: base of the MBP that prints without E32's mark -- or None where no
    #: record prints or the record carries no bear case.
    fv_bear: float | None = None
    #: the exchange's closed weekdays between the newest close and the run
    #: date, or None when no calendar could answer (owner, 2026-09-19)
    closed_days: frozenset | None = frozenset()
    #: E122(e): set when THIS row's close is one the vendor dropped or
    #: blanked and we kept. It prints wherever the close prints.
    retained: object | None = None


#: The tolerance a replayed record must land within of the stored fv_base.
#: Two decimals is what the watchlist states; the record replays to more.
FV_REPLAY_TOLERANCE = 0.005


def load_run_record(entry: WatchlistEntry,
                    root: Path = PROJECT_ROOT) -> tuple["RunRecord | None", str | None]:
    """The entry's linked run record, or None with the reason (item 9).

    A RUN WITHOUT A COMPLETE RECORD DOES NOT PRINT A FAIR VALUE -- Phase 3's
    rule, now reaching `vss run` itself. The record is returned only when
    the entry names one that exists, loads, is complete (every one of the
    eight declarations), is this ticker's, and REPLAYS to the stored
    `fv_base` from its own inputs. Anything else is a number nobody can
    regenerate, and the row says so instead of printing it. An entry with
    no `fv_base` has nothing to check and returns (None, None).
    """
    if entry.fv_base is None:
        return None, None
    if not entry.run_record:
        return None, (f"fv_base {entry.fv_base:,.2f} names no run record "
                      f"(`run_record:`), so nothing can regenerate it -- a "
                      f"run without a complete record prints no fair value")
    path = Path(entry.run_record)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        return None, (f"run record `{entry.run_record}` is not on disk")
    try:
        record = RunRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError, RecordError) as exc:
        return None, f"run record `{entry.run_record}` does not load: {exc}"
    gaps = record.missing()
    if gaps:
        return None, (f"run record `{entry.run_record}` is INCOMPLETE -- "
                      f"absent: {'; '.join(gaps)}")
    try:
        replayed = record.strike()
    except (RecordError, ValueError) as exc:
        return None, f"run record `{entry.run_record}` does not replay: {exc}"
    if abs(replayed - float(entry.fv_base)) > FV_REPLAY_TOLERANCE:
        return None, (f"run record `{entry.run_record}` replays to "
                      f"{replayed:,.2f} and the entry says "
                      f"{entry.fv_base:,.2f}; the record is the record")
    if record.ticker != entry.ticker:
        return None, (f"run record `{entry.run_record}` is {record.ticker}'s, "
                      f"not {entry.ticker}'s")
    return record, None


def recorded_fair_value(entry: WatchlistEntry,
                        root: Path = PROJECT_ROOT) -> tuple[float | None, str | None]:
    """The entry's `fv_base`, or DATA MISSING with the reason (item 9)."""
    record, why = load_run_record(entry, root)
    return (float(entry.fv_base) if record is not None else None), why


def bear_case_value(record: "RunRecord | None") -> float | None:
    """The record struck at its PRE-REGISTERED bear case -- E28's MBP base.

    None where no record prints, or where the record carries no bear case:
    then the name has no E28 MBP and `assess` falls back to the superseded
    `fv_base x tier` with its mark. The bear rate is the record's own
    `growth.bear`, fixed in the growth view BEFORE implied growth was
    solved -- which is the ordering E32 said the three retained figures
    could not prove, and a record can.
    """
    if record is None or record.growth.bear is None:
        return None
    return record.strike(record.growth.bear)



#: E122(d): refused corrections wait HERE until the owner rules on them.
#: Beside the database, so a scratch run never touches the real one.
PRICE_CORRECTIONS = PROJECT_ROOT / "data" / "price_corrections.json"


def read_corrections(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        log.error("price corrections unreadable (%s: %s): a refused "
                  "correction cannot be reported", type(exc).__name__, exc)
        return {}


def record_corrections(path: Path, ticker: str, corrections, as_of: date) -> dict:
    """Add this run's REFUSED corrections to the pending file, and return it.

    An applied correction is reported and not stored: it is already in the
    series. A refused one blocks the name every night until the owner rules,
    which is E122(d)'s "blocks the name and asks".
    """
    pending = read_corrections(path)
    for c in corrections or ():
        if c.applied:
            continue
        rows = pending.setdefault(ticker, [])
        if any(r.get("when") == c.when.isoformat() for r in rows):
            continue
        rows.append({"when": c.when.isoformat(), "held": c.held,
                     "incoming": c.incoming, "level": c.crossed[0] if c.crossed else None,
                     "level_value": c.crossed[1] if c.crossed else None,
                     "first_refused": as_of.isoformat()})
    return pending


def pending_correction_text(pending: dict, ticker: str) -> str | None:
    """The blocker's words for a name with a refused correction (E122 d)."""
    rows = (pending or {}).get(ticker) or []
    if not rows:
        return None
    parts = []
    for r in rows:
        parts.append(f"{r.get('when')}: held {r.get('held'):,.4f}, vendor now "
                     f"{r.get('incoming'):,.4f}, which crosses {r.get('level')} "
                     f"{r.get('level_value'):,.2f} (refused since "
                     f"{r.get('first_refused')})")
    return ("A PRICE CORRECTION CROSSES A LEVEL and was NOT applied (E122 d); "
            "the held close stands and this name collects no verdict until you "
            "rule: " + "; ".join(parts) +
            ". Clear it by removing the entry from data/price_corrections.json.")


def entry_levels(entry: WatchlistEntry) -> dict[str, float]:
    """Every level this name carries, in the QUOTE unit (E122 d).

    Computed from the entry and its record alone -- no price series enters
    it -- so it can be handed to the fetch BEFORE a close is read.
    """
    record, _ = load_run_record(entry)
    levels: dict[str, float] = {}
    if entry.stop_price is not None:
        levels["stop"] = float(entry.stop_price)
    if record is None:
        return levels
    from .fx import to_quote_units
    base = to_quote_units(record.strike(), record.currency, entry.currency)
    if base is not None:
        levels["fv_base"] = float(base)
        mbp = compute_mbp_e90(base, entry.tier)
        if mbp is not None:
            levels["MBP"] = float(mbp)
    bear = to_quote_units(bear_case_value(record), record.currency, entry.currency)
    if bear is not None:
        levels["FV_bear"] = float(bear)
    # The STRUCK bull on the entry is the level; the record's replay is the
    # fallback for a name that carries none (owner, 2026-09-20).
    if entry.fv_bull is not None:
        levels["FV_bull"] = float(entry.fv_bull)
    elif record.growth.bull is not None:
        bull = to_quote_units(record.strike(record.growth.bull),
                              record.currency, entry.currency)
        if bull is not None:
            levels["FV_bull"] = float(bull)
    return levels


def build_row(entry: WatchlistEntry, fetched: FetchResult, as_of: date,
              settled: date | None = None,
              previous_mbp: float | None = None,
              calendars: "MarketCalendars | None" = None,
              use_calendar: bool = False,
              pending_correction: str | None = None) -> TickerRow:
    """Combine one entry with its price data into a fully assessed row.

    ``settled`` is the run's settlement cutoff (`metrics.settled_through`).
    Passing it is what keeps a LIVE PRINT out of `last_close`: the DECK
    hand run of 2026-08-25 priced 88.55 mid-session against a settled
    88.74 (REVIEW-4 report A 4.2).
    """
    computed = (M.compute(fetched.frame, as_of, settled)
                if fetched.frame is not None else M.Metrics())
    # K4, BEFORE ANY LEVEL IS COMPARED. Both held names carry live stops
    # (165 and 112); a feed quoting two scales must print DATA MISSING for
    # the stop check, never STOP BREACHED. The window is the drawdown's.
    finding = (series_sanity.check(fetched.frame, as_of)
               if fetched.frame is not None else None)
    series_finding = finding.detail if finding is not None else None
    # THE EXCHANGE CALENDAR (owner, 2026-09-19): no block for a session the
    # exchange never held. `use_calendar` is the nightly's; with no loaded
    # calendar, or a suffix it does not map, the days are None and the
    # block that results says it counted Monday to Friday.
    closed_days: frozenset | None = frozenset()
    if use_calendar:
        closed_days = None
        if calendars is not None and computed.last_close_date is not None:
            closed_days = calendars.closed_weekdays(
                calendars.market_of_ticker(entry.ticker),
                computed.last_close_date, as_of)
    # Item 9: a fair value reaches the assessment ONLY through a complete
    # run record that replays to it. Otherwise it is DATA MISSING here, and
    # the MBP and section 6.4 comparisons that hang off it say so. E28: the
    # same record, struck at its bear case, is what the MBP is built on.
    record, fv_refused = load_run_record(entry)
    fv_base = float(entry.fv_base) if record is not None else None
    # E90: the MBP stands on the record's UNROUNDED base-case replay -- the
    # cushion is applied before the single rounding, as E28's bear-value
    # arithmetic did. The row still shows the entry's stored 2dp figure.
    fv_unrounded = record.strike() if record is not None else None
    fv_bear = bear_case_value(record)
    # The bull case, on the same record and the same pre-registered view.
    # A HELD name without one has no C4 / E42 exit test (owner, 2026-09-20).
    fv_bull = (record.strike(record.growth.bull)
               if record is not None and record.growth.bull is not None else None)
    # THE GBX/GBP SEAM, CLOSED (G17, 2026-09-19): the record values the
    # share in its accounts' currency (AUTO.L: GBP) and the close arrives in
    # the quote unit (GBX, pence). Every level the assessment compares with
    # the close -- fv_base, the bear case, and so the MBP -- is moved into
    # the quote unit FIRST. The stop is already entered in the trading
    # currency (FRAMEWORK §8) and is not touched.
    if record is not None:
        from .fx import to_quote_units
        fv_unrounded = to_quote_units(fv_unrounded, record.currency, entry.currency)
        fv_bear = to_quote_units(fv_bear, record.currency, entry.currency)
        fv_bull = to_quote_units(fv_bull, record.currency, entry.currency)
    # E121(e), amended 2026-09-20: COMPLIANCE BY DETECTION. If the vendor
    # prints a close on a day this name's derived calendar calls closed, the
    # suffix is mapped to the wrong exchange -- and a wrong mapping is the
    # one case that can UNDER-state staleness. Sixty days is enough to catch
    # it within a trading day of the name going live, and costs one set
    # difference.
    mismatch = None
    if use_calendar and calendars is not None and fetched.frame is not None:
        market = calendars.market_of_ticker(entry.ticker)
        if market is not None:
            window = calendars.closed_weekdays(market, as_of - timedelta(days=60), as_of)
            if window:
                printed = {d.date() if hasattr(d, "date") else d
                           for d, close in zip(fetched.frame.index, fetched.frame["Close"])
                           if close == close and close is not None}   # not NaN
                clash = sorted(window & printed)
                if clash:
                    suffix = entry.ticker.rsplit(".", 1)[1] if "." in entry.ticker else "(none)"
                    mismatch = (
                        f"E121(e): the vendor printed a close on "
                        f"{', '.join(d.isoformat() for d in clash[:3])}"
                        f"{' and more' if len(clash) > 3 else ''}, which the "
                        f"calendar for suffix '{suffix}' ({market}) calls CLOSED. "
                        f"The mapping is wrong, so the session count may "
                        f"UNDER-state staleness. Correct the suffix in "
                        f"config/exchange_calendars.yaml (that is data, not a "
                        f"ruling) and this clears itself.")

    verdict = assess(
        ticker=entry.ticker,
        status=entry.status,
        last_close=computed.last_close,
        last_close_date=computed.last_close_date,
        drawdown=computed.drawdown,
        fv_base=fv_unrounded,
        tier=entry.tier,
        stop_price=entry.stop_price,
        catalyst_date=entry.catalyst_date,
        catalyst_resolved=entry.catalyst_resolved,
        catalyst_event=entry.catalyst_event,
        as_of=as_of,
        fetch_error=fetched.error,
        bear_value=fv_bear,
        series_finding=series_finding,
        # E12: a PIPELINE entry's frozen Gate 1 reading, read and applied.
        dd_at_entry=entry.dd_at_entry,
        peak_date=entry.peak_date,
        # E100: the MBP the previous full run recorded, so a crossing the
        # DEFINITION caused can be told from one the price caused.
        previous_mbp=previous_mbp,
        holidays=closed_days,
        pending_correction=pending_correction,
        calendar_mismatch=mismatch,
    )
    return TickerRow(
        entry=entry,
        metrics=computed,
        assessment=verdict,
        source=fetched.source,
        fetched_at=fetched.fetched_at,
        error=fetched.error,
        pct_to_mbp=M.pct_distance(computed.last_close, verdict.mbp),
        pct_to_stop=M.pct_distance(computed.last_close, entry.stop_price),
        series_finding=series_finding,
        fv_base=fv_base,
        fv_refused=fv_refused,
        fv_bear=fv_bear,
        closed_days=closed_days,
        retained=(fetched.retained or {}).get(computed.last_close_date),
    )


def to_record(
    row: TickerRow, run_ts: datetime, as_of: date, ticker_filter: str | None = None
) -> dict:
    m, e, a = row.metrics, row.entry, row.assessment
    return {
        "run_ts": run_ts.isoformat(timespec="seconds"),
        "as_of": as_of.isoformat(),
        "ticker": e.ticker,
        "name": e.name,
        "currency": e.currency,
        "status": e.status,
        "source": row.source,
        "error": row.error,
        "last_close": m.last_close,
        "last_close_date": m.last_close_date.isoformat() if m.last_close_date else None,
        # Whether that close had SETTLED when the run read it. NULL means
        # the run declared no cutoff, not that the price settled.
        "last_close_settled": (None if m.last_close_settled is None
                               else int(m.last_close_settled)),
        "live_bar_date": m.live_bar_date.isoformat() if m.live_bar_date else None,
        "high_52w": m.high_52w,
        "drawdown": m.drawdown,
        # E63: the other end of the window travels with the drawdown, so a
        # month of runs can be read back with both on every row.
        "low_52w": m.low_52w,
        "low_52w_date": m.low_52w_date.isoformat() if m.low_52w_date else None,
        "pct_above_52w_low": m.pct_above_52w_low,
        "rsi14": m.rsi14,
        "sma50": m.sma50,
        "sma200": m.sma200,
        "pct_vs_sma50": m.pct_vs_sma50,
        "pct_vs_sma200": m.pct_vs_sma200,
        "avg_volume_20": m.avg_volume_20,
        "volume_ratio": m.volume_ratio,
        # Item 9: the fair value the run PRINTED -- None where the entry's
        # fv_base had no complete record behind it -- and the reason.
        "fv_base": row.fv_base,
        "fv_refused": row.fv_refused,
        "tier": e.tier,
        "mbp": a.mbp,
        # E32: the number goes to the store with its basis beside it. A
        # figure read back out of this table months from now must not look
        # live because the report that marked it is gone.
        "mbp_superseded": 1 if a.mbp_superseded else 0,
        "mbp_struck": e.mbp_basis.struck if e.mbp_basis is not None else None,
        "stop_price": e.stop_price,
        "pct_to_mbp": row.pct_to_mbp,
        "pct_to_stop": row.pct_to_stop,
        "blocked": 1 if a.blocked else 0,
        "blockers": "; ".join(b.code for b in a.blockers) or None,
        "verdicts": "; ".join(v.code for v in a.verdicts) or None,
        "ticker_filter": ticker_filter,
        # K4: the series finding travels with the row, so a DATA MISSING
        # stop check read back later says why it was withheld.
        "series_finding": row.series_finding,
    }


def price_watch(*, run_ts: datetime, as_of: date, settled: date | None,
                cache_dir: Path, db_path: Path,
                dry_run: bool = False,
                top_n: int = PW.DEFAULT_TOP_N,
                state_path: Path | None = None,
                failures: list | None = None) -> tuple[list, list[str]]:
    """E97: the ranked list's price watch. Returns (rows, pointer lines).

    Reads the newest stored ranking, assesses each name once (E94), fetches
    the prices the watchlist does not carry, and asks which levels crossed
    TONIGHT. Writes only its own cursor, and not even that on a dry run.
    """
    from .readiness import assess
    from .store import read_ranking

    rows = read_ranking(db_path)
    if not rows:
        return [], []

    ranked = sorted(
        (r for r in rows if r.get("section") == "ranked" and r.get("position")),
        key=lambda r: r["position"])[:top_n]

    # E97 depends on this: without the vendor's industry string the
    # circle-of-competence STRING limb cannot reach a name, and E51/E96
    # names would be watched. NHY.OL and EXE were, on the first run.
    industries = PW.industry_strings()

    readiness, prices = {}, {}
    unassessed: list[str] = []
    with contextlib.redirect_stdout(sys.stderr):
        for row in ranked:
            ticker = row["ticker"]
            try:
                readiness[ticker] = assess(
                    ticker, industry=industries.get(ticker),
                    as_of=as_of, run_ts=run_ts)
            except Exception as exc:  # noqa: BLE001 -- one name never breaks it
                # D1: one name never breaks the watcher -- and the name that
                # broke is NAMED. A ticker that silently drops out of the
                # watch is a ticker nobody is watching, and the table below
                # would simply have twenty rows where nineteen were watched.
                log.warning("E97 readiness for %s: %s", ticker, exc)
                unassessed.append(f"{ticker} ({type(exc).__name__}: {exc})")
                continue
            fetched = get_history(ticker, cache_dir, now=run_ts,
                                  write=not dry_run)
            if fetched.frame is not None:
                prices[ticker] = M.compute(fetched.frame, as_of, settled)

    # The price is needed for the reference distance, so it is passed in
    # after the assessment rather than during it.
    for ticker, metrics in prices.items():
        item = readiness.get(ticker)
        if item is None or item.indicative is None:
            continue
        readiness[ticker] = assess(
            ticker, price=metrics.last_close,
            quote_currency=getattr(item, "quote_currency", None),
            industry=industries.get(ticker),
            as_of=as_of, run_ts=run_ts)

    if unassessed and failures is not None:
        failures.append(HB.ComponentFailure(
            HB.COMPONENT_READINESS,
            f"{len(unassessed)} of {len(ranked)} ranked name(s) could not be "
            f"assessed: {'; '.join(unassessed[:4])}"
            + ("…" if len(unassessed) > 4 else ""),
            "Those names are in the table below on their drawdown alone, "
            "with no reference distance -- which is what a name with no "
            "value also looks like."))
    watched = PW.watch_ranked(rows, prices=prices, readiness=readiness,
                              top_n=top_n, as_of=as_of, run_ts=run_ts)
    path = state_path or PW.STATE_PATH
    state = PW.load_state(path)
    for item in watched:
        PW.crossings(item, state, as_of=as_of)
    if not dry_run:
        PW.save_state(state, path)
    return watched, PW.notification_lines(watched)


#: Exit code of a dry run that refused on a stale close (see
#: rules.MAX_CLOSE_AGE_TRADING_DAYS_LEVEL). 1 is the coverage gate's, 2 an
#: unknown ticker.
EXIT_STALE_DRY_RUN = 3


def _level_blocked(r: TickerRow) -> bool:
    return r.assessment.blocked and carries_level(
        r.entry.status, r.assessment.mbp, r.entry.stop_price)


def stale_for_dry_run(rows: list[TickerRow], as_of: date) -> list[str]:
    """One line per name CARRYING A LEVEL that the staleness gate blocked.

    The SAME judgement the nightly makes (rules: one session for a name
    with a level, the exchange's closed days not counted) -- so a dry run
    refuses exactly when the nightly would block. Only a name with a level
    can refuse the run (owner, 2026-09-19): a dropped name blocking the
    whole report is how a block learns to be ignored.
    """
    del as_of   # judged in the assessment, against the run's own date
    out = []
    for r in rows:
        if not _level_blocked(r):
            continue
        for b in r.assessment.blockers:
            if b.code in (STALE_DATA, NO_DATA, PRICE_CORRECTION):
                out.append(f"{r.entry.ticker}: {b.reason}")
    return out


#: Where the nightly records whether its block push went, so the NEXT
#: report can say when it did not (owner, 2026-09-19).
BLOCK_PUSH_STATE = PROJECT_ROOT / "data" / "block_push_state.json"


def block_streaks(rows: list[TickerRow], previous: dict | None, as_of: date) -> dict:
    """Consecutive nights per ``TICKER|BLOCKER_CODE``, tonight included.

    (owner, 2026-09-20) A first night and a ninth night must not look
    alike. A code that did not block tonight is dropped, so the count is
    CONSECUTIVE nights and never a total. A SECOND run on the same `as_of`
    (a re-run) does not advance a night.
    """
    previous = previous or {}
    before = previous.get("streaks") or {}
    same_night = previous.get("as_of") == as_of.isoformat()
    out = {}
    for r in rows:
        if not _level_blocked(r):
            continue
        for b in r.assessment.blockers:
            key = f"{r.entry.ticker}|{b.code}"
            out[key] = int(before.get(key, 0)) if same_night else int(before.get(key, 0)) + 1
            out[key] = max(out[key], 1)
    return out


def block_push_lines(rows: list[TickerRow], as_of: date,
                     streaks: dict | None = None) -> list[str]:
    """One line per blocked name carrying a level: where it last stood.

    Every blocked name with an MBP, a stop or HELD status, whatever blocked
    it (owner, 2026-09-19: a missed MBP crossing is the same failure as a
    missed stop, only cheaper). Each line gives the last known close, its
    date and its age in sessions, and says the level was not checked.
    """
    out = []
    for r in rows:
        if not _level_blocked(r):
            continue
        m = r.metrics
        if m.last_close is not None and m.last_close_date is not None:
            age = trading_days_between(m.last_close_date, as_of,
                                       holidays=r.closed_days or frozenset())
            kept = (f", RETAINED (first seen {r.retained.first_seen.isoformat()})"
                    if r.retained is not None else "")
            where = (f"last close {m.last_close:,.2f} on "
                     f"{m.last_close_date.isoformat()}, {age} session(s) old{kept}")
        else:
            where = "no close at all"
        why = "; ".join(b.code for b in r.assessment.blockers)
        nights = max((int((streaks or {}).get(f"{r.entry.ticker}|{b.code}", 1))
                      for b in r.assessment.blockers), default=1)
        out.append(f"{r.entry.ticker}: night {nights} — {where} ({why}). "
                   f"{unchecked_levels(r.entry.status, r.assessment.mbp, r.entry.stop_price)}")
    return out


def read_previous_push(path: Path | None = None) -> dict | None:
    """The last nightly's push record, or None if there is none.

    An unreadable record is itself reported as a failure: silence about the
    push is exactly what the record exists to prevent.
    """
    path = path or BLOCK_PUSH_STATE
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"sent": False, "as_of": "unknown", "lines": [],
                "outcome": f"push record unreadable: {type(exc).__name__}: {exc}"}


def unsent_nights(record: dict | None) -> list[dict]:
    """EVERY night whose push did not go since the last one that did.

    (owner, 2026-09-20) Two failures in a row must not lose the first
    night's names: that is the same class of silent loss as a close that
    was seen and then overwritten. The backlog is carried forward on each
    failure and cleared only by a push that sends.
    """
    if record is None:
        return []
    backlog = [n for n in (record.get("unsent") or []) if isinstance(n, dict)]
    return backlog


def previous_push_failure(record: dict | None) -> dict | None:
    """The most recent unsent night, or None. Kept for the older callers;
    `unsent_nights` is what the report prints."""
    nights = unsent_nights(record)
    return nights[-1] if nights else None


def write_push_record(*, as_of: date, run_ts: datetime, lines: list[str],
                      outcome: str, path: Path | None = None,
                      previous: dict | None = None,
                      streaks: dict | None = None) -> None:
    """``sent`` is True, False (a push was due and did not go) or None
    (nothing was due). A topic that is not set is a push that did not go.

    The UNSENT BACKLOG carries every night that did not go, oldest first,
    and only a push that sends clears it (owner, 2026-09-20).
    """
    path = path or BLOCK_PUSH_STATE
    sent = None if not lines else outcome.startswith("sent")
    backlog = [n for n in (previous or {}).get("unsent") or [] if isinstance(n, dict)]
    if sent:
        backlog = []
    elif sent is False:
        backlog = [n for n in backlog if n.get("as_of") != as_of.isoformat()]
        backlog.append({"as_of": as_of.isoformat(), "run_ts": run_ts.isoformat(),
                        "outcome": outcome, "lines": lines})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"as_of": as_of.isoformat(),
                                "run_ts": run_ts.isoformat(),
                                "sent": sent, "outcome": outcome,
                                "lines": lines, "unsent": backlog,
                                "streaks": streaks or {}}, indent=2) + "\n",
                    encoding="utf-8")


def run(
    *,
    dry_run: bool = False,
    only_ticker: str | None = None,
    watchlist_path: Path = WATCHLIST_PATH,
    cache_dir: Path = CACHE_DIR,
    db_path: Path = DB_PATH,
    reports_dir: Path = REPORTS_DIR,
    now: datetime | None = None,
    push_state_path: Path | None = None,
    corrections_path: Path | None = None,
) -> int:
    run_ts = now or datetime.now().astimezone()
    as_of = run_ts.date()
    # A bar dated today is a live print until New York has closed.
    settled = M.settled_through(run_ts)

    entries = load_watchlist(watchlist_path)
    watchlist_size = len(entries)
    log.info("loaded %d watchlist entries from %s", watchlist_size, watchlist_path)

    # THE DEAD MAN'S SWITCH, leg 1. The row goes in BEFORE any fetching, so
    # a run that dies mid-fetch leaves a record saying it started and never
    # finished. `begin` never raises: the switch may not be able to break
    # the run it guards.
    # A DRY RUN WRITES NO ROW AT ALL -- "no report file, no cache write, no
    # database row" is the promise the flag makes, and the switch does not
    # get an exemption from it. It still READS the record below, because
    # reporting the gap costs nothing and a dry run is a fine way to ask.
    completion_id = None
    if not dry_run:
        completion_id = HB.begin(db_path, kind=HB.KIND_NIGHTLY,
                                 started_at=run_ts, as_of=as_of,
                                 scope=only_ticker, dry_run=False)
    # What the switch has to say about the runs BEFORE this one. Read here,
    # before this run's own row could ever be mistaken for the answer --
    # `exclude_id` makes that impossible rather than merely unlikely.
    continuity = HB.report_lines(db_path, now=run_ts, kind=HB.KIND_NIGHTLY,
                                 exclude_id=completion_id)

    resolved_filter: str | None = None
    if only_ticker:
        wanted = only_ticker.strip().upper()
        entries = [e for e in entries if e.ticker.upper() == wanted]
        if not entries:
            log.error("ticker %s is not in %s", only_ticker, watchlist_path)
            return 2
        resolved_filter = entries[0].ticker
        log.warning(
            "PARTIAL RUN: restricted to %s; the other %d watchlist entries are "
            "not being evaluated",
            resolved_filter,
            watchlist_size - 1,
        )

    # E100: what each name's MBP was on the previous FULL run. Read BEFORE
    # this run writes its own rows, or the comparison would be against
    # tonight.
    try:
        prior_mbp = previous_mbps(db_path)
    except Exception as exc:  # noqa: BLE001 -- never fails the run
        log.warning("E100: previous MBPs unreadable (%s: %s); a crossing "
                    "cannot be attributed and none will be marked",
                    type(exc).__name__, exc)
        prior_mbp = {}

    # THE EXCHANGE CALENDARS (owner, 2026-09-19). A calendar that cannot be
    # loaded does not stop the run: every name is then counted Monday to
    # Friday, and each block that results says so.
    try:
        calendars = load_market_calendars(PROJECT_ROOT / "config" / "exchange_calendars.yaml")
    except Exception as exc:  # noqa: BLE001
        log.error("exchange calendars not loaded (%s: %s): every name is "
                  "counted Monday to Friday tonight", type(exc).__name__, exc)
        calendars = None

    # Whether LAST night's block push went. Read before this run writes its
    # own, so the report can say so when it did not.
    # The record lives beside the database, so a run on a scratch database
    # (every test) never touches the real one.
    push_state_path = push_state_path or db_path.parent / BLOCK_PUSH_STATE.name
    corrections_path = corrections_path or db_path.parent / PRICE_CORRECTIONS.name
    pending_corrections = read_corrections(corrections_path)
    applied_corrections: list[str] = []
    push_record = read_previous_push(push_state_path)
    previous_push = unsent_nights(push_record)

    rows: list[TickerRow] = []
    # yfinance occasionally writes to stdout; stdout belongs to the report.
    with contextlib.redirect_stdout(sys.stderr):
        for entry in entries:
            # E122(d): the levels go WITH the request, so a correction that
            # moves a close across one is refused inside the merge.
            try:
                levels = entry_levels(entry)
            except Exception as exc:  # noqa: BLE001 -- never fails the run
                log.warning("%s: levels for the correction test could not be "
                            "computed (%s: %s); a correction would apply "
                            "unchecked, so none is applied tonight",
                            entry.ticker, type(exc).__name__, exc)
                levels = {"__unknown__": float("nan")}
            fetched = get_history(
                entry.ticker, cache_dir, now=run_ts, write=not dry_run,
                levels=levels,
            )
            pending_corrections = record_corrections(
                corrections_path, entry.ticker, fetched.corrections, as_of)
            applied_corrections += [f"{entry.ticker}: {c.line()}"
                                    for c in (fetched.corrections or ())]
            rows.append(build_row(entry, fetched, as_of, settled,
                previous_mbp=prior_mbp.get(entry.ticker),
                calendars=calendars, use_calendar=True,
                pending_correction=pending_correction_text(pending_corrections,
                                                           entry.ticker)))

    # A DRY RUN REFUSES ON A STALE CLOSE (owner, 2026-09-19): error, not a
    # report. Judged before anything is rendered so no figure is printed.
    if dry_run:
        stale = stale_for_dry_run(rows, as_of)
        if stale:
            log.error("DRY RUN REFUSED: %d name(s) carrying a level have a close "
                      "more than %d session(s) old as of %s -- no trigger "
                      "was checked",
                      len(stale), MAX_CLOSE_AGE_TRADING_DAYS_LEVEL, as_of)
            for line in stale:
                log.error("  %s", line)
            return EXIT_STALE_DRY_RUN

    # D2: judged HERE, before the report is rendered, so the report can say
    # it. The same verdict is recorded on the run below and decides the exit
    # code -- one assessment, read three times, rather than three.
    priced = sum(1 for r in rows if r.metrics.last_close is not None)
    coverage = HB.assess_coverage(expected=len(rows), covered=priced)

    # E126 (2026-09-20): A TIER REQUIRES AT LEAST FOUR EVALUABLE GATES.
    # The nightly cannot re-score a name, but it CAN say where a tier is
    # carried against a denominator that no longer supports one -- which is
    # the case the ruling says must not exist. Read only for names that
    # carry a tier; a store that will not load is skipped, never guessed.
    tier_holds: list[str] = []
    if not resolved_filter:
        for entry in entries:
            if entry.tier is None:
                continue
            try:
                from .manual import (MANUAL_DIR, load_manual, section5_basis,
                                     tier_hold)
                parsed = load_manual(entry.ticker, directory=MANUAL_DIR)
                held = tier_hold(parsed, section5_basis(parsed))
            except Exception:  # noqa: BLE001 -- no store, nothing to say
                continue
            if held:
                tier_holds.append(f"{entry.ticker} (tier {entry.tier}): {held}")

    # E92: what a report-date refresh left waiting. Recomputed live off the
    # store and the watchlist, so an item the owner has dealt with is gone on
    # the next run without anyone clearing a flag. A scoped run does not
    # print it: a one-ticker report must never read like the whole list.
    # D1: a component that fails is CARRIED, not dropped. Wrapping these so
    # they cannot cost the nightly report is right; setting the result to an
    # empty list and letting the renderer gate on truthiness is what made a
    # broken component indistinguishable from a quiet one.
    failures: list[HB.ComponentFailure] = []

    pending = []
    if not resolved_filter:
        try:
            pending = refresh_needs_owner(entries)
        except Exception as exc:  # noqa: BLE001 -- never fails the run
            log.warning("NEEDS OWNER could not be computed: %s: %s",
                        type(exc).__name__, exc)
            failures.append(HB.ComponentFailure(
                HB.COMPONENT_NEEDS_OWNER, f"{type(exc).__name__}: {exc}",
                "No name is being reported as waiting on you tonight, and "
                "that is because the check did not run -- not because "
                "nothing waits."))

    # E97: price-watch the ranked list. A ranked name is NOT on the
    # watchlist, so its price is fetched here -- the run already has the
    # cache and the settlement cutoff, and E97 adds no timer. Wrapped
    # whole: a watcher that broke must never cost the nightly report.
    watched: list = []
    watch_fired: list[str] = []
    watch_ran = False
    if not resolved_filter:
        try:
            watched, watch_fired = price_watch(
                run_ts=run_ts, as_of=as_of, settled=settled,
                cache_dir=cache_dir, db_path=db_path, dry_run=dry_run,
                failures=failures)
            watch_ran = True
        except Exception as exc:  # noqa: BLE001 -- never fails the run
            log.warning("E97 price watch skipped: %s: %s",
                        type(exc).__name__, exc)
            failures.append(HB.ComponentFailure(
                HB.COMPONENT_PRICE_WATCH, f"{type(exc).__name__}: {exc}",
                "No ranked name was price-watched tonight. A crossing that "
                "happened would not have been pointed at, and the table "
                "below that would have shown it is absent for that reason."))

    markdown = render(
        rows,
        run_ts=run_ts,
        as_of=as_of,
        dry_run=dry_run,
        ticker_filter=resolved_filter,
        watchlist_size=watchlist_size,
        needs_owner=pending,
        price_watch=watched,
        continuity=continuity,
        coverage=coverage,
        failures=failures,
        price_watch_ran=watch_ran,
        previous_push=previous_push,
        corrections=applied_corrections,
        tier_holds=tier_holds,
    )

    # E122(d): the pending file is the record a refused correction waits in.
    if not dry_run:
        try:
            corrections_path.parent.mkdir(parents=True, exist_ok=True)
            corrections_path.write_text(
                json.dumps(pending_corrections, indent=2) + "\n", encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            log.error("the pending price corrections were not written "
                      "(%s: %s)", type(exc).__name__, exc)

    if dry_run:
        log.warning("dry run: no report file, no cache write, no database row")
        print("DRY RUN — nothing written")
        print()
    else:
        reports_dir.mkdir(parents=True, exist_ok=True)
        # A scoped run gets its own filename so it can never overwrite the
        # day's full report with a one-ticker file.
        stem = as_of.isoformat()
        if resolved_filter:
            stem += f".{safe_name(resolved_filter)}"
        report_path = reports_dir / f"{stem}.md"
        report_path.write_text(markdown + "\n", encoding="utf-8")
        log.info("wrote %s", report_path)
        persist(db_path, [to_record(r, run_ts, as_of, resolved_filter) for r in rows])
        # The overview page, regenerated from the repository every night.
        #
        # TWO CONDITIONS, both of them about what the page IS. It is a view
        # of the WHOLE record, so a SCOPED run does not write it -- a
        # `--ticker` run priced one name, and a forty-name page built beside
        # it would show the other thirty-nine at whatever the cache last
        # held without saying so. And it is a view of THIS repository, so a
        # run pointed at another reports directory -- a replay, or a test --
        # does not write it either: it would overwrite the live page with a
        # partial view of files it was not reading.
        #
        # A FAILURE HERE NEVER FAILS THE RUN. The page is a view of files
        # that are themselves the record; the report on disk and the
        # database row are the run's job and are already done. The failure
        # is logged at WARNING, which is where the journal keeps problems
        # (`journalctl --user -t vss -p warning`).
        if not resolved_filter and reports_dir == REPORTS_DIR:
            try:
                from .overview import write_overview

                write_overview(now=run_ts,
                               watchlist_path=watchlist_path,
                               cache_dir=cache_dir, db_path=db_path)
            except Exception as exc:      # noqa: BLE001 -- see above
                log.warning("the overview page was not regenerated: %s: %s",
                            type(exc).__name__, exc)
        # E92: the pointer goes out AFTER the report is on disk, and only
        # when there is something to point at. A failed POST is logged and
        # never fails the run -- the report is the record, the notification
        # is a convenience laid beside it. Outbound only: nothing here, or
        # anywhere in this project, ever reads from the topic.
        if pending:
            log.info("ntfy: %s", post_needs_owner(notification_lines(pending)))
        # E97: the same topic, the same shape. A pointer, not a valuation.
        if watch_fired:
            log.info("ntfy (E97): %s", post_needs_owner(watch_fired))
        # The dead man's switch: its own POST, with its own title, and NOT
        # folded into the NEEDS OWNER pointer above. That one fires only
        # when a name is waiting; a gap in the runs has to be able to reach
        # the phone on a night when no name is. A scoped run reports the gap
        # in its report but posts nothing -- it is not the run whose absence
        # is being measured.
        # THE BLOCK PUSH (owner, 2026-09-19): one per night, every blocked
        # name carrying a level, with where each last stood. Its outcome is
        # RECORDED, so a push that did not go is said by the next report --
        # a failed push is itself a failure to surface. Full runs only: a
        # scoped run is not the night.
        if not resolved_filter:
            streaks = block_streaks(rows, push_record, as_of)
            block_lines = block_push_lines(rows, as_of, streaks)
            outcome = "nothing to send"
            if block_lines:
                nights = max(streaks.values(), default=1)
                outcome = post_needs_owner(
                    block_lines,
                    title=f"vss: {len(block_lines)} name(s) BLOCKED (night "
                          f"{nights}) -- level not checked")
                log.warning("block push: %s", outcome)
            try:
                write_push_record(as_of=as_of, run_ts=run_ts, lines=block_lines,
                                  outcome=outcome, path=push_state_path,
                                  previous=push_record, streaks=streaks)
            except Exception as exc:  # noqa: BLE001
                log.error("the block push record was not written (%s: %s): "
                          "tomorrow's report cannot say whether tonight's "
                          "push went", type(exc).__name__, exc)
        if continuity and not resolved_filter:
            log.warning("dead man's switch: %s", " | ".join(continuity))
            log.info("ntfy (continuity): %s",
                     post_needs_owner(continuity,
                                      title="vss: the run has gone quiet"))

    print(markdown)

    blocked = sum(1 for r in rows if r.assessment.blocked)
    actions = sum(1 for r in rows if r.assessment.actionable)
    errored = sum(1 for r in rows if r.error)
    log.info(
        "done: %d tickers, %d blocked, %d actionable, %d with fetch errors",
        len(rows), blocked, actions, errored,
    )
    # THE END OF THE RUN, and the only place the switch is allowed to say so.
    # PRICED coverage, not row count: a row with a fetch error is a row, and
    # counting it would let a night when every fetch failed record itself as
    # full coverage.
    #
    # AND THE COVERAGE IS NOW JUDGED, NOT MERELY RECORDED (D2). Until
    # 2026-09-01 this column was written with care and read by nothing, so a
    # night on which every fetch failed exited 0, reset the 72-hour clock and
    # pinged healthchecks.io to say the run had succeeded. A run that reached
    # its end and got nothing is run-shaped silence, and the three things
    # that follow from saying so are all mechanical:
    #
    #   * `short=1` keeps it out of `last_completion`, so the clock does not
    #     reset and the next run reports the gap;
    #   * a non-zero exit means systemd never reaches `ExecStartPost=`, so
    #     the OUTSIDE observer is not told the run worked -- and healthchecks
    #     alarms on the ping's absence, which is the alarm we want;
    #   * `OnFailure=` fires, which is the only leg that reports while the
    #     outage is happening.
    #
    # A SCOPED run is judged the same way against its own one name. It never
    # reset the clock anyway (`scope IS NOT NULL`), but a `--ticker` run whose
    # single fetch failed should still not exit 0.
    HB.finish(db_path, completion_id, finished_at=datetime.now().astimezone(),
              expected=watchlist_size, covered=priced, errors=errored,
              short=coverage.short,
              detail=((f"COVERAGE SHORT: {coverage.reason}" if coverage.short
                       else f"{blocked} blocked, {actions} actionable")
                      + (f", SCOPED to {resolved_filter}" if resolved_filter
                         else "")))
    if coverage.short:
        log.error("RUN COVERAGE: %s. This run did not reset the staleness "
                  "clock and sends no healthcheck ping.", coverage.reason)
        return HB.EXIT_COVERAGE_SHORT
    return 0
