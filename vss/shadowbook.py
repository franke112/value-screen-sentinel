"""`vss shadow`: every refusal against the market from the day it was written.

FRAMEWORK-EDITS E114, ruled 2026-09-08. B45 measures the positions the
framework SOLD; this measures the ones it never bought. A process that
only refuses, and never scores its refusals, cannot be falsified, and
FRAMEWORK section 0 rule 3 makes falsification the posture toward every
candidate rather than only the survivors.

WHAT THE BOOK HOLDS. Six fields per row, written when the verdict is:
ticker, verdict date, verdict and its standing, the settled close on that
date, the fair value if one was struck, and one line naming what decided
it. No thesis, no expectation, no target -- a row that argues is a row
that will be re-argued.

WHAT IS NEVER DONE HERE. A verdict date with no settled close is DATA
MISSING and stays so: the nearest bar is not the close on that date, and
that is B45's rule about a fill read off a bar, applied to a verdict. A
window that has not elapsed reports INCOMPLETE and is never filled with a
partial figure. A name whose dividends the vendor does not record is DATA
MISSING rather than a price return set against a total-return benchmark.
The report is read-only -- it writes one markdown file and touches
nothing else.

THE RECORDED FACT AND THE DERIVED COMPARISON ARE TWO NUMBERS (E114 limit
three, amended 2026-09-09). The book stores the UNADJUSTED settled close,
which never restates and is what a baseline has to be. Every comparison
is a TOTAL return derived at read time from the adjusted series, which
DOES restate on every dividend and split -- so a figure printed last year
may not be the figure printed this year, and that is the price of having
both legs be the same kind of quantity. The report re-reads the vendor's
unadjusted close for each verdict date and flags a stored baseline that
no longer matches it.

WHAT THIS IS NOT. It is not a signal. Nothing here arms an alert, enters
a name or reaches a valuation, and nothing else in the tool imports this
module. It measures what happened and never whether the verdict was
right: a dropped name that rose may have risen for the reasons the
verdict refused to underwrite, and a WATCH-GATED name that fell says
nothing until the gate's own event arrives. E114 is read once a year.
"""

from __future__ import annotations

import calendar
import contextlib
import csv
import logging
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Sequence

import pandas as pd

from . import metrics as M
from .config import ConfigError
from .fetch import FetchResult, get_history
from .fx import major_unit
from .runner import CACHE_DIR, PROJECT_ROOT, REPORTS_DIR
from .sales import (DASH, DATA_MISSING, change, close_on_or_before,
                    last_close, num, pct, settled_closes)

#: How far a stored baseline may sit from the vendor's unadjusted close
#: for that date before the row is called RESTATED. The book stores four
#: decimals, so the rounding gap is ~1e-8 relative; a split is 2x and a
#: vendor correction is not subtle either. Nothing real lives between.
RESTATEMENT_TOLERANCE = 1e-4

log = logging.getLogger("vss.shadowbook")

#: E114's book. Tracked, on the reasoning that put the watchlist in git.
SHADOW_BOOK_PATH = PROJECT_ROOT / "config" / "shadow_book.csv"

#: The six fields E114 names, plus the two that say where the row came
#: from. Provenance is not content: E40's posture is that a figure whose
#: source is not named is a figure nobody can check.
COLUMNS: tuple[str, ...] = (
    "ticker", "verdict_date", "verdict", "standing", "close", "currency",
    "fv_base", "decided_by", "source",
)
#: The three verdicts E114 admits. WATCH-PRICED, PIPELINE and HELD are
#: not refusals and are not in the book.
VERDICTS: tuple[str, ...] = ("DROPPED", "WATCH-GATED", "INTAKE")
#: STANDING holds until deliberately removed; EXPIRY is re-read when a
#: named event arrives; OPEN means nothing has been decided yet, which is
#: what INTAKE means under E111.
STANDINGS: tuple[str, ...] = ("STANDING", "EXPIRY", "OPEN")

#: The windows, in CALENDAR MONTHS from the verdict date.
WINDOW_MONTHS: tuple[int, ...] = (1, 3, 6, 12)
INCOMPLETE = "INCOMPLETE"

TOTAL_RETURN = "total return"
PRICE_RETURN = "price return"


@dataclass(frozen=True)
class Benchmark:
    """One comparison index, its currency, and what its level MEANS."""

    symbol: str
    label: str
    currency: str
    basis: str
    note: str = ""


#: E114's benchmark legs, BOTH set against a name measured on total
#: return. The S&P 500 is available as a total-return series; OMXS30 is
#: NOT -- `^OMXS30GI` returned a single bar and no history when it was
#: measured on 2026-09-08, so the price index stands in and is labelled
#: as such everywhere it appears. `tools/threshold_reachability.py` made
#: the same substitution and recorded the same caveat. E114 limit three:
#: a STATED substitution is honest, a SILENT mismatch is not.
BENCHMARKS: tuple[Benchmark, ...] = (
    Benchmark("^OMX", "OMXS30", "SEK", PRICE_RETURN,
              "^OMXS30GI carries no history at the vendor (one bar, "
              "2026-09-08); the price index understates OMXS30's total "
              "return by roughly 2-4pp/yr"),
    Benchmark("^SP500TR", "S&P 500", "USD", TOTAL_RETURN,
              "dividends reinvested"),
)

#: Below this many rows with BOTH a baseline close and an elapsed window,
#: the book cannot distinguish rule from luck. B45's floor, and for the
#: same reason: the count is printed either way.
SAMPLE_FLOOR = 20


# --- the book ----------------------------------------------------------------


@dataclass(frozen=True)
class Verdict:
    """One row of the shadow book, exactly as E114 specifies it."""

    ticker: str
    verdict_date: date
    verdict: str
    standing: str
    #: The SETTLED close on `verdict_date` in `currency`. None is DATA
    #: MISSING and stays so -- E114 forbids the nearest bar.
    close: float | None
    currency: str
    fv_base: float | None
    decided_by: str
    source: str

    @property
    def baseline_missing(self) -> bool:
        return self.close is None

    @property
    def quote_currency(self) -> str:
        """The MAJOR unit. A return is scale-invariant, so GBX and GBP
        give the same figure; the FX pair only exists for the major."""
        return major_unit(self.currency) or self.currency


def _row_float(raw: str, field: str, ticker: str) -> float | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        raise ConfigError(f"shadow book, {ticker}: {field} must be a number "
                          f"or blank, got {raw!r}") from None
    if value <= 0:
        raise ConfigError(f"shadow book, {ticker}: {field} must be positive, "
                          f"got {raw!r}. Blank is DATA MISSING; zero is not.")
    return value


def parse_book(rows: list[dict[str, str]]) -> tuple[Verdict, ...]:
    """Validate and build the book. Raises ConfigError on anything odd."""
    out: list[Verdict] = []
    seen: set[tuple[str, date]] = set()
    for n, raw in enumerate(rows, start=1):
        ticker = (raw.get("ticker") or "").strip()
        if not ticker:
            raise ConfigError(f"shadow book, row {n}: ticker is required")
        unknown = sorted(k for k in raw if k not in COLUMNS)
        if unknown:
            raise ConfigError(f"shadow book, {ticker}: unknown column(s) "
                              f"{', '.join(unknown)}. Allowed: "
                              f"{', '.join(COLUMNS)}")
        missing = [k for k in ("verdict_date", "verdict", "standing",
                               "currency", "decided_by", "source")
                   if not (raw.get(k) or "").strip()]
        if missing:
            raise ConfigError(f"shadow book, {ticker}: missing "
                              f"{', '.join(missing)}. Only close and "
                              f"fv_base may be blank, and blank means DATA "
                              f"MISSING.")
        try:
            when = date.fromisoformat(raw["verdict_date"].strip())
        except ValueError:
            raise ConfigError(f"shadow book, {ticker}: verdict_date must be "
                              f"YYYY-MM-DD, got "
                              f"{raw['verdict_date']!r}") from None
        verdict = raw["verdict"].strip().upper()
        if verdict not in VERDICTS:
            raise ConfigError(f"shadow book, {ticker}: verdict must be one of "
                              f"{'|'.join(VERDICTS)}, got {raw['verdict']!r}")
        standing = raw["standing"].strip().upper()
        if standing not in STANDINGS:
            raise ConfigError(f"shadow book, {ticker}: standing must be one "
                              f"of {'|'.join(STANDINGS)}, got "
                              f"{raw['standing']!r}")
        if (ticker, when) in seen:
            raise ConfigError(f"shadow book: {ticker} appears twice on "
                              f"{when.isoformat()}. One verdict, one row.")
        seen.add((ticker, when))
        out.append(Verdict(
            ticker=ticker, verdict_date=when, verdict=verdict,
            standing=standing,
            close=_row_float(raw.get("close", ""), "close", ticker),
            currency=raw["currency"].strip(),
            fv_base=_row_float(raw.get("fv_base", ""), "fv_base", ticker),
            decided_by=raw["decided_by"].strip(),
            source=raw["source"].strip(),
        ))
    out.sort(key=lambda v: (v.verdict_date, v.ticker))
    return tuple(out)


def load_shadow_book(path: Path = SHADOW_BOOK_PATH) -> tuple[Verdict, ...]:
    if not path.exists():
        raise ConfigError(f"no shadow book at {path}. E114's record is a "
                          f"file the owner keeps; nothing here creates one.")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        if list(header) != list(COLUMNS):
            raise ConfigError(f"shadow book header must be exactly "
                              f"{','.join(COLUMNS)}, got {','.join(header)}")
        return parse_book([dict(row) for row in reader])


# --- the measurement ---------------------------------------------------------


def add_months(day: date, months: int) -> date:
    """`day` plus `months` calendar months, the day clamped to the month.

    2026-08-31 plus six months is 2027-02-28: a window is a month, not
    thirty-and-a-bit days, and the clamp is what makes it one.
    """
    total = day.month - 1 + months
    year, month = day.year + total // 12, total % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


@dataclass(frozen=True)
class NameSeries:
    """A name's two series: the FACT and the thing comparisons are made of.

    `price` is the unadjusted settled close -- what the book stores, what
    never restates, and what the restatement check reads. `total` is the
    dividend- and split-adjusted series every comparison uses, or None
    where the vendor gives no way to establish dividends at all; `why`
    then says which way it failed, in words the report prints.
    """

    price: pd.Series
    total: pd.Series | None
    why: str | None = None


def name_series(frame: pd.DataFrame | None, settled: date,
                error: str | None = None) -> NameSeries:
    """Split a fetched frame into the recorded fact and the comparison.

    E114 limit three: a name whose dividends cannot be established is DATA
    MISSING, never a price return set against a total-return benchmark.
    An ABSENT `Dividends` column is exactly that case -- it cannot be told
    from a name that paid nothing, and the difference is the whole of the
    measurement. A column of zeros is the opposite: E110's posture is that
    a stated zero is evidence, so a tracked series with no dividend events
    is a total return that happens to equal its price return.
    """
    price = settled_closes(frame, settled)
    if frame is None or len(frame) == 0:
        return NameSeries(price, None, error or "no data for the ticker")
    if "Adj Close" not in frame.columns:
        return NameSeries(price, None,
                          "the vendor served no Adj Close column, so no "
                          "total return can be derived")
    if "Dividends" not in frame.columns:
        return NameSeries(price, None,
                          "the vendor served no Dividends column, so a name "
                          "that paid nothing cannot be told from one whose "
                          "dividends are not recorded")
    total = settled_closes(frame, settled, "Adj Close")
    if len(total) == 0:
        return NameSeries(price, None,
                          "the vendor's Adj Close carries no settled bar")
    return NameSeries(price, total)


def exact(series: pd.Series | None, day: date) -> float | None:
    """The value ON `day`, or None. Never the nearest bar -- E114."""
    if series is None or len(series) == 0:
        return None
    hit = series[series.index == day]
    return float(hit.iloc[0]) if len(hit) else None


def converted(levels: pd.Series, rates: pd.Series | None,
              day: date) -> float | None:
    """The index level on or before `day`, in the target currency.

    `rates` is None where the benchmark is already quoted in the name's
    currency. Either leg absent is DATA MISSING, never one leg alone.
    """
    level = close_on_or_before(levels, day)
    if level is None:
        return None
    if rates is None:
        return level[0]
    rate = close_on_or_before(rates, day)
    return None if rate is None else level[0] * rate[0]


@dataclass(frozen=True)
class Leg:
    """One benchmark's change over one window, in the name's currency."""

    label: str
    change: float | None


@dataclass(frozen=True)
class Window:
    months: int
    ends: date
    #: False until `ends` is settled. E114: never a partial figure.
    elapsed: bool
    close: float | None = None
    close_date: date | None = None
    name_change: float | None = None
    legs: tuple[Leg, ...] = ()

    def excess(self, label: str) -> float | None:
        if self.name_change is None:
            return None
        leg = next((l for l in self.legs if l.label == label), None)
        if leg is None or leg.change is None:
            return None
        return self.name_change - leg.change


@dataclass(frozen=True)
class Row:
    verdict: Verdict
    #: The last settled UNADJUSTED close -- the fact, not the comparison.
    last: float | None
    last_date: date | None
    #: TOTAL return from the verdict date, derived from the adjusted
    #: series. None is DATA MISSING and `why` says which kind.
    since: float | None
    since_legs: tuple[Leg, ...]
    windows: tuple[Window, ...]
    #: Why the baseline is absent, in words, where it is.
    baseline_why: str | None = None
    #: Why no total return could be derived, where none could.
    total_why: str | None = None
    #: The same window on the UNADJUSTED closes. Printed nowhere as a
    #: comparison -- it exists so the report can say what reinvesting the
    #: dividends was worth, which is the whole point of the amendment.
    since_price: float | None = None
    #: The vendor's unadjusted close for the verdict date as read TODAY,
    #: where it disagrees with the stored baseline.
    restated_to: float | None = None
    error: str | None = None

    @property
    def measurable(self) -> bool:
        return self.since is not None

    @property
    def dividend_gap(self) -> float | None:
        """Total return less price return over the same window."""
        if self.since is None or self.since_price is None:
            return None
        return self.since - self.since_price


def _legs(benchmarks: dict[str, pd.Series], rates: dict[str, pd.Series | None],
          start: date, end: date) -> tuple[Leg, ...]:
    out = []
    for bench in BENCHMARKS:
        levels = benchmarks.get(bench.label)
        if levels is None:
            out.append(Leg(bench.label, None))
            continue
        out.append(Leg(bench.label, change(converted(levels, rates.get(bench.label), start),
                                           converted(levels, rates.get(bench.label), end))))
    return tuple(out)


def build_row(verdict: Verdict, series: NameSeries,
              benchmarks: dict[str, pd.Series],
              rates: dict[str, pd.Series | None], settled: date,
              error: str | None = None) -> Row:
    """One row: the recorded facts, and the TOTAL returns beside them."""
    end = last_close(series.price)
    why = None
    if verdict.baseline_missing:
        if verdict.verdict_date > settled:
            why = "the verdict date is not yet settled"
        elif verdict.verdict_date.weekday() >= 5:
            why = (f"{verdict.verdict_date.strftime('%A')} is not a trading "
                   f"day and the row has not been re-dated (E114 limit four)")
        else:
            why = (f"{verdict.verdict_date.strftime('%A')} is a weekday and "
                   f"the vendor serves no settled bar for it -- an exchange "
                   f"holiday and a vendor gap look the same from here, so "
                   f"E114 limit four does NOT walk the date back further")

    # The baseline for every comparison is the ADJUSTED value on the
    # verdict date, exactly -- E114 moves a date, it never moves a bar.
    # A row with no RECORDED close is not measured whatever the adjusted
    # series says: a blank baseline is the book's own DATA MISSING.
    base_total = (None if verdict.baseline_missing
                  else exact(series.total, verdict.verdict_date))
    total_why = series.why
    if total_why is None and base_total is None and not verdict.baseline_missing:
        total_why = ("the adjusted series carries no bar on the verdict "
                     "date, though the unadjusted one does")

    windows: list[Window] = []
    for months in WINDOW_MONTHS:
        ends = add_months(verdict.verdict_date, months)
        if ends > settled:
            windows.append(Window(months, ends, elapsed=False))
            continue
        # The window END is a computed date, not a decision date, so the
        # last close on or before it IS the window's close -- B45 reads
        # its index legs the same way.
        at = close_on_or_before(series.total, ends)
        fact = close_on_or_before(series.price, ends)
        windows.append(Window(
            months, ends, elapsed=True,
            close=fact[0] if fact else None,
            close_date=fact[1] if fact else None,
            name_change=change(base_total, at[0] if at else None),
            legs=_legs(benchmarks, rates, verdict.verdict_date, ends),
        ))

    end_total = last_close(series.total) if series.total is not None else None
    vendor_now = exact(series.price, verdict.verdict_date)
    restated = None
    if (verdict.close is not None and vendor_now is not None
            and abs(vendor_now - verdict.close) > RESTATEMENT_TOLERANCE
            * max(abs(verdict.close), 1.0)):
        restated = vendor_now

    return Row(
        verdict=verdict,
        last=end[0] if end else None, last_date=end[1] if end else None,
        since=change(base_total, end_total[0] if end_total else None),
        since_legs=(_legs(benchmarks, rates, verdict.verdict_date, end[1])
                    if end else ()),
        windows=tuple(windows), baseline_why=why, total_why=total_why,
        since_price=change(verdict.close, end[0] if end else None),
        restated_to=restated, error=error,
    )


# --- rendering ---------------------------------------------------------------


def _window_cell(w: Window, row: Row) -> str:
    if not w.elapsed:
        return f"{INCOMPLETE} ({w.ends.isoformat()})"
    if row.verdict.baseline_missing or w.name_change is None:
        return f"**{DATA_MISSING}**"
    # Every figure below is a TOTAL return on both sides. E114 limit three.
    parts = [pct(w.name_change)]
    for leg in w.legs:
        parts.append(f"{leg.label} {pct(leg.change)}")
    return " / ".join(parts)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def render(rows: list[Row], *, run_ts: datetime, settled: date,
           written_to: Path | None, book_path: Path) -> str:
    labels = [b.label for b in BENCHMARKS]
    out: list[str] = []
    out.append(f"# vss shadow -- the shadow book: every refusal against the "
               f"market -- {run_ts.date().isoformat()}")
    out.append("")
    out.append(f"Run {run_ts.isoformat(timespec='minutes')}; closes settled "
               f"through {settled.isoformat()}. The book is `{book_path}` "
               f"(FRAMEWORK-EDITS E114) and this report reads it and nothing "
               f"else. Prices and index levels come from the tool's own "
               f"price path (`vss.fetch.get_history`), settled bars only.")
    out.append("")
    out.append("**THIS IS NOT A SIGNAL.** Nothing here may arm an alert, "
               "enter a name or reach a valuation, and E114 has it read "
               "once a year. **It measures what happened, never whether the "
               "verdict was right**: a dropped name that rose may have risen "
               "for the reasons the verdict refused to underwrite, and a "
               "WATCH-GATED name that fell says nothing until the gate's own "
               "event arrives.")
    out.append("")
    out.append("**The measurement basis (E114 limit three, amended "
               "2026-09-09).** **Every comparison here is a TOTAL return on "
               "both sides**: the name's dividends are reinvested, derived "
               "at read time from the vendor's adjusted series, and a name "
               "whose dividends the vendor does not record is "
               f"**{DATA_MISSING}** rather than a price return set against a "
               "total-return benchmark. "
               + " ".join(f"{b.label} is `{b.symbol}`, a {b.basis}"
                          + (f" -- {b.note}" if b.note else "") + "."
                          for b in BENCHMARKS)
               + " The OMXS30 leg is the one remaining mismatch and is "
               "labelled a price index everywhere it appears: a stated "
               "substitution is honest, a silent one is not. Both index "
               "legs are converted into the name's own quote currency at "
               "the daily rate on each end of the window.")
    out.append("")
    out.append("**What this gives up.** The book STORES the unadjusted "
               "settled close, which never restates and is the recorded "
               "fact; the total return is DERIVED beside it from a series "
               "that **does** restate on every dividend and split. A figure "
               "printed here last year may not be the figure printed this "
               "year, and that is the price of both legs being the same "
               "kind of quantity. Every row's stored baseline is re-read "
               "against the vendor's unadjusted close for that date, and a "
               "row that no longer matches is listed below.")
    out.append("")
    if not rows:
        out.append(f"The book at `{book_path}` is empty -- nothing to report.")
        return "\n".join(out)

    head = (["Name", "Verdict", "Standing", "Verdict date",
             "Close at verdict (recorded)", "Fair value",
             "Last settled close", "Since verdict (TR)"] + labels
            + [f"{m}m" for m in WINDOW_MONTHS] + ["What decided it"])
    out.append("## Every verdict")
    out.append("")
    out.append("| " + " | ".join(head) + " |")
    out.append("|" + "---|" * len(head))
    for r in rows:
        v = r.verdict
        legs = {leg.label: leg for leg in r.since_legs}
        cells = [
            f"`{v.ticker}`",
            v.verdict,
            v.standing,
            v.verdict_date.isoformat(),
            (f"{num(v.close)} {v.currency}" if v.close is not None
             else f"**{DATA_MISSING}**"),
            num(v.fv_base) if v.fv_base is not None else DASH,
            (f"{num(r.last)} ({r.last_date.isoformat()})"
             if r.last is not None else (r.error or DATA_MISSING)),
            (f"**{DATA_MISSING}**" if r.since is None else pct(r.since)),
        ]
        # An index leg is the index's own fact and prints whether or not
        # the name has a baseline; it is never subtracted from nothing.
        for label in labels:
            leg = legs.get(label)
            cells.append(DASH if leg is None or leg.change is None
                         else pct(leg.change))
        for w in r.windows:
            cells.append(_window_cell(w, r))
        cells.append(v.decided_by)
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    out.append(f"Window cells read: name TOTAL return / "
               f"{' / '.join(labels)} over the same window, all in the "
               f"name's quote currency. "
               f"`{INCOMPLETE}` until the window has elapsed AND its close "
               f"is settled -- E114 never fills a window with a partial "
               f"figure, and the date in brackets is when it closes.")
    out.append("")

    blank = [r for r in rows if r.verdict.baseline_missing]
    if blank:
        out.append("## Verdicts with no baseline close")
        out.append("")
        out.append("E114 forbids the nearest bar. These rows carry no close "
                   "on their verdict date and measure nothing until one "
                   "exists.")
        out.append("")
        for r in blank:
            out.append(f"- `{r.verdict.ticker}` "
                       f"{r.verdict.verdict_date.isoformat()} "
                       f"({r.verdict.verdict}): {DATA_MISSING} -- "
                       f"{r.baseline_why}.")
        out.append("")

    undated = [r for r in rows
               if r.total_why is not None and not r.verdict.baseline_missing]
    if undated:
        out.append("## Verdicts whose total return could not be derived")
        out.append("")
        out.append("E114 limit three: a name whose dividends cannot be "
                   "established is DATA MISSING, never a price return set "
                   "against a total-return benchmark. These rows keep their "
                   "recorded close and measure nothing.")
        out.append("")
        for r in undated:
            out.append(f"- `{r.verdict.ticker}` "
                       f"{r.verdict.verdict_date.isoformat()}: "
                       f"{DATA_MISSING} -- {r.total_why}.")
        out.append("")

    restated = [r for r in rows if r.restated_to is not None]
    out.append("## Stored baselines re-read against the vendor")
    out.append("")
    if not restated:
        out.append(f"All {len(rows)} stored baselines still match the "
                   f"vendor's unadjusted close for their verdict date, "
                   f"within {RESTATEMENT_TOLERANCE:.2%}. The recorded fact "
                   f"is still a fact.")
    else:
        out.append("**These stored closes no longer match what the vendor "
                   "serves for that date.** A split restates an unadjusted "
                   "series and so does a vendor correction; the book is not "
                   "rewritten automatically, because which of the two it is "
                   "is a question for a person.")
        out.append("")
        for r in restated:
            out.append(f"- `{r.verdict.ticker}` "
                       f"{r.verdict.verdict_date.isoformat()}: book says "
                       f"{num(r.verdict.close)}, vendor now serves "
                       f"{num(r.restated_to)}.")
    out.append("")

    paid = [r for r in rows if r.dividend_gap is not None
            and abs(round(r.dividend_gap * 100, 1)) > 0]
    out.append("## What reinvesting the dividends was worth")
    out.append("")
    if not paid:
        out.append("No name has gone ex-dividend since its verdict, so "
                   "every total return above equals its own price return. "
                   "**The basis still matters** -- it is what stops the "
                   "comparison drifting as the windows lengthen, and the "
                   "12-month windows are where it will show.")
    else:
        out.append("Total return less price return over the same window, "
                   "for every name that has gone ex-dividend since its "
                   "verdict. This is the gap the 2026-09-09 amendment "
                   "closed, and it grows with the window.")
        out.append("")
        out.append("| Name | Since verdict (TR) | Price return | Dividends worth |")
        out.append("|---|---|---|---|")
        for r in sorted(paid, key=lambda r: -abs(r.dividend_gap)):
            out.append(f"| `{r.verdict.ticker}` | {pct(r.since)} | "
                       f"{pct(r.since_price)} | "
                       f"{r.dividend_gap * 100:+.2f}pp |")
    out.append("")

    out.append("## By verdict")
    out.append("")
    out.append("| Verdict | Rows | Measurable | Mean since verdict | "
               + " | ".join(f"Mean excess vs {label}" for label in labels)
               + " |")
    out.append("|---|---|---|---|" + "---|" * len(labels))
    for verdict in sorted({r.verdict.verdict for r in rows}):
        group = [r for r in rows if r.verdict.verdict == verdict]
        live = [r for r in group if r.measurable]
        cells = [verdict, str(len(group)), str(len(live)),
                 pct(_mean([r.since for r in live]))]
        for label in labels:
            diffs = []
            for r in live:
                leg = next((l for l in r.since_legs if l.label == label), None)
                if leg is not None and leg.change is not None:
                    diffs.append(r.since - leg.change)
            cells.append(pct(_mean(diffs)) if diffs else DASH)
        out.append("| " + " | ".join(cells) + " |")
    out.append("")

    measurable = [r for r in rows if r.measurable]
    elapsed = sum(1 for r in rows for w in r.windows if w.elapsed
                  and w.name_change is not None)
    earliest = min(r.verdict.verdict_date for r in rows)
    age = (settled - earliest).days
    out.append(f"**Sample: {len(rows)} verdict(s), {len(measurable)} with a "
               f"baseline close, earliest {earliest.isoformat()} — "
               f"{age} days ago. {elapsed} of "
               f"{len(rows) * len(WINDOW_MONTHS)} fixed windows have "
               f"elapsed.**")
    out.append("")
    # NOT str.capitalize() -- it lower-cases the whole rest of the string,
    # and the rest of this one is INCOMPLETE.
    reasons = []
    if elapsed == 0:
        reasons.append(f"**Not one fixed window has elapsed** — every "
                       f"1/3/6/12-month cell reads {INCOMPLETE}")
    if len(measurable) < SAMPLE_FLOOR:
        reasons.append(f"there are fewer than {SAMPLE_FLOOR} measurable rows")
    if reasons:
        out.append(" and ".join(reasons)
                   + ", so **nothing here can distinguish rule from luck.** "
                   f"The since-verdict column is {age} days of price and is "
                   f"a record, not evidence. E114 has this read once a year "
                   f"for that reason.")
    else:
        out.append("Read the verdict rows against their elapsed windows, "
                   "never against the since-verdict column alone.")
    out.append("")
    out.append(f"Written to `{written_to}`." if written_to
               else "DRY RUN -- nothing written.")
    return "\n".join(out)


# --- the command -------------------------------------------------------------


Fetcher = Callable[[str], FetchResult]


def shadow_rows(book: Sequence[Verdict], *, settled: date,
                fetch: Fetcher) -> list[Row]:
    """Measure every verdict in ``book`` against the benchmarks.

    SPLIT OUT OF `run_shadow` so the shadow book has ONE implementation and
    two readers: the markdown report, and `vss.overview`'s third view. A
    second copy of this loop is a second set of benchmark legs, a second FX
    assembly, and the first place the two would silently disagree.

    `fetch` is injected, so a caller with no network (the overview page,
    which reads the repository and never the vendor) hands it a cache
    reader and gets the same rows, with DATA MISSING wherever the cache is
    short. Nothing here writes.
    """
    rows: list[Row] = []
    with contextlib.redirect_stdout(sys.stderr):
        levels: dict[str, pd.Series] = {}
        for bench in BENCHMARKS:
            fetched = fetch(bench.symbol)
            if fetched.frame is None:
                log.error("%s (%s): %s", bench.symbol, bench.label,
                          fetched.error)
                continue
            levels[bench.label] = settled_closes(fetched.frame, settled)

        # One FX series per (benchmark currency -> quote currency) pair the
        # book actually needs. A pair whose legs match needs no series at
        # all, and None is what says so.
        pairs = {(b.currency, v.quote_currency) for b in BENCHMARKS
                 for v in book}
        fx: dict[tuple[str, str], pd.Series | None] = {}
        for base, quote in sorted(pairs):
            if base == quote:
                fx[(base, quote)] = None
                continue
            fetched = fetch(f"{base}{quote}=X")
            if fetched.frame is None:
                log.error("%s%s=X: %s", base, quote, fetched.error)
                continue
            fx[(base, quote)] = settled_closes(fetched.frame, settled)

        for verdict in book:
            fetched = fetch(verdict.ticker)
            error = (None if fetched.frame is not None
                     else (fetched.error or "no data"))
            series = name_series(fetched.frame, settled, error)
            rates: dict[str, pd.Series | None] = {}
            usable = dict(levels)
            for bench in BENCHMARKS:
                key = (bench.currency, verdict.quote_currency)
                if key not in fx:
                    usable.pop(bench.label, None)  # no FX = DATA MISSING
                    continue
                rates[bench.label] = fx[key]
            rows.append(build_row(verdict, series, usable, rates, settled,
                                  error=error))
    return rows


def run_shadow(*, book_path: Path = SHADOW_BOOK_PATH,
               cache_dir: Path = CACHE_DIR, reports_dir: Path = REPORTS_DIR,
               now: datetime | None = None, dry_run: bool = False,
               fetch: Fetcher | None = None) -> tuple[int, str]:
    """Build the shadow book report. Returns (exit code, markdown)."""
    run_ts = now or datetime.now().astimezone()
    settled = M.settled_through(run_ts)
    book = load_shadow_book(book_path)
    log.info("%d verdict(s) in the shadow book", len(book))

    if fetch is None:
        def fetch(ticker: str) -> FetchResult:  # pragma: no cover - network
            return get_history(ticker, cache_dir, now=run_ts, write=not dry_run)

    rows = shadow_rows(book, settled=settled, fetch=fetch)

    written: Path | None = None
    if not dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        written = reports_dir / f"SHADOW-BOOK-{run_ts.date().isoformat()}.md"
    markdown = render(rows, run_ts=run_ts, settled=settled,
                      written_to=written, book_path=book_path)
    if written is not None:
        written.write_text(markdown + "\n", encoding="utf-8")
        log.info("wrote %s", written)
    return 0, markdown
