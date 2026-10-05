"""`vss sales`: every closed position against the index from its own sale date.

FRAMEWORK-EDITS B45, implemented 2026-08-30 on the owner's instruction. The
framework sells on rules (C1-C4, E42) and this is the first place the
rules meet their own outcomes: each FILL the owner has booked in a
watchlist entry's `sales:` block is set against the last settled close,
against OMXS30 and the S&P 500 over the same window, and at fixed marks 30,
90 and 365 days after the sale.

WHAT IS NEVER DONE HERE. A fill with no price prints as DATA MISSING and
stays that way: the sale-day bar is a bar, not a fill, and a price read
off it would be a number the owner never received. The report is
read-only -- it writes a markdown file and touches nothing else.

WHAT THE COMPARISON IS. The name's change is FILL -> last settled close in
the quote currency; the index legs run from the index's close ON the sale
date (the last index close on or before it, where the sale date has no
index bar) to the last settled index close. SEK proceeds are printed as
booked and never blended with the price return: the two quantities differ
by FX and by the broker's charges, and MSFT's exit note keeps them apart
for that reason.
"""

from __future__ import annotations

import contextlib
import logging
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable

import pandas as pd

from . import metrics as M
from .config import SaleRecord, WatchlistEntry, load_watchlist
from .fetch import FetchResult, get_history
from .runner import CACHE_DIR, REPORTS_DIR, WATCHLIST_PATH

log = logging.getLogger("vss.sales")

#: The two comparison indices B45 names, always both: the SEK account's
#: home index and the USD account's. A name's own home index is not
#: fetched -- B45 leaves that to the owner.
INDICES: tuple[tuple[str, str], ...] = (("^OMX", "OMXS30"), ("^GSPC", "S&P 500"))
#: The fixed marks, in calendar days after the sale date. A mark prints
#: only once it has passed AND its close is settled.
MARK_DAYS: tuple[int, ...] = (30, 90, 365)
#: Below this many priced fills the report says, in words, that the
#: sample cannot distinguish rule from luck. Provisional: B45 leaves the
#: threshold to the owner, and the count is printed either way.
SAMPLE_FLOOR = 20
DASH = "--"
NOT_YET = "not yet"
DATA_MISSING = "DATA MISSING"


def num(value: float | None, dp: int = 2) -> str:
    return DASH if value is None else f"{value:,.{dp}f}"


def pct(value: float | None, dp: int = 1) -> str:
    """A signed percentage -- but NEVER a SIGN ON A ROUNDED ZERO.

    A baseline stored to two decimals against a vendor close carrying
    fifteen puts -2.6e-8 on a row where nothing moved, and `-0.0%` reads
    as a fall. A magnitude that rounds away prints unsigned, which is
    what it means: too small to have a direction at this precision.
    """
    if value is None:
        return DASH
    scaled = value * 100
    if abs(round(scaled, dp)) == 0:
        return f"{0.0:.{dp}f}%"
    return f"{scaled:+.{dp}f}%"


def settled_closes(frame: pd.DataFrame | None, settled: date,
                   column: str = "Close") -> pd.Series:
    """The frame's `column`, settled bars only, NaN values dropped.

    A vendor bar with no close (UNA.AS and SAP.DE both showed one for
    2026-08-28) is not a close, so it is dropped rather than read as zero.

    `column` exists for E114, which needs the SAME settling and the same
    NaN discipline on `Adj Close` to derive a total return. A frame that
    does not carry the column asked for returns empty rather than raising:
    the absence is DATA MISSING and the caller says so in its own words.
    """
    if frame is None or len(frame) == 0 or column not in frame.columns:
        return pd.Series(dtype=float)
    kept = M.drop_unsettled(frame, settled)
    closes = kept[column]
    closes = closes[~closes.isna()]
    return pd.Series(closes.to_numpy(dtype=float),
                     index=M.index_dates(closes.index))


def close_on_or_before(closes: pd.Series, day: date) -> tuple[float, date] | None:
    """The last close dated on or before ``day``, with its date, or None."""
    if closes is None or len(closes) == 0:
        return None
    prior = [(d, float(v)) for d, v in closes.items() if d <= day]
    if not prior:
        return None
    d, v = prior[-1]
    return v, d


def last_close(closes: pd.Series) -> tuple[float, date] | None:
    if closes is None or len(closes) == 0:
        return None
    return float(closes.iloc[-1]), closes.index[-1]


def change(start: float | None, end: float | None) -> float | None:
    if start is None or end is None or start == 0:
        return None
    return end / start - 1.0


@dataclass(frozen=True)
class IndexLeg:
    label: str
    at_sale: float | None
    at_sale_date: date | None
    later: float | None
    later_date: date | None

    @property
    def change(self) -> float | None:
        return change(self.at_sale, self.later)


@dataclass(frozen=True)
class Mark:
    days: int
    mark_date: date
    #: False until the mark date is settled; then the three legs are read.
    reached: bool
    name_close: float | None = None
    name_close_date: date | None = None
    name_change: float | None = None
    index_changes: tuple[tuple[str, float | None], ...] = ()


@dataclass(frozen=True)
class FillRow:
    ticker: str
    name: str
    status: str
    sale: SaleRecord
    last: float | None
    last_date: date | None
    #: None where the fill has no price (DATA MISSING) or no close exists.
    price_change: float | None
    index_legs: tuple[IndexLeg, ...]
    marks: tuple[Mark, ...]
    error: str | None = None

    @property
    def priced(self) -> bool:
        return self.sale.price is not None


def index_leg(label: str, closes: pd.Series, sale_date: date) -> IndexLeg:
    at = close_on_or_before(closes, sale_date)
    end = last_close(closes)
    return IndexLeg(label, at[0] if at else None, at[1] if at else None,
                    end[0] if end else None, end[1] if end else None)


def mark(sale: SaleRecord, days: int, name_closes: pd.Series,
         index_closes: dict[str, pd.Series], settled: date) -> Mark:
    mark_date = sale.date + timedelta(days=days)
    if mark_date > settled:
        return Mark(days, mark_date, reached=False)
    at_mark = close_on_or_before(name_closes, mark_date)
    name_close = at_mark[0] if at_mark else None
    name_close_date = at_mark[1] if at_mark else None
    legs = []
    for label, closes in index_closes.items():
        start = close_on_or_before(closes, sale.date)
        end = close_on_or_before(closes, mark_date)
        legs.append((label, change(start[0] if start else None,
                                   end[0] if end else None)))
    return Mark(days, mark_date, reached=True, name_close=name_close,
                name_close_date=name_close_date,
                name_change=change(sale.price, name_close),
                index_changes=tuple(legs))


def fill_row(entry: WatchlistEntry, sale: SaleRecord, name_closes: pd.Series,
             index_closes: dict[str, pd.Series], settled: date,
             error: str | None = None) -> FillRow:
    end = last_close(name_closes)
    return FillRow(
        ticker=entry.ticker, name=entry.name, status=entry.status, sale=sale,
        last=end[0] if end else None, last_date=end[1] if end else None,
        price_change=change(sale.price, end[0] if end else None),
        index_legs=tuple(index_leg(label, closes, sale.date)
                         for label, closes in index_closes.items()),
        marks=tuple(mark(sale, d, name_closes, index_closes, settled)
                    for d in MARK_DAYS),
        error=error,
    )


# --- rendering ---------------------------------------------------------------


def _mark_cell(m: Mark, priced: bool) -> str:
    if not m.reached:
        return f"{NOT_YET} ({m.mark_date.isoformat()})"
    parts = [(DATA_MISSING if not priced else pct(m.name_change))]
    for label, chg in m.index_changes:
        parts.append(f"{label} {pct(chg)}")
    return " / ".join(parts)


def _fill_cell(row: FillRow) -> str:
    if not row.priced:
        return f"**{DATA_MISSING}**"
    price = row.sale.price
    # 482.425 is a real fill and prints as such; 482.43 must not grow a zero.
    dp = 3 if abs(round(price, 2) - price) > 1e-9 else 2
    return f"{num(price, dp)} {row.sale.currency or ''}".strip()


def render(rows: list[FillRow], *, run_ts: datetime, settled: date,
           written_to: Path | None) -> str:
    out: list[str] = []
    out.append(f"# vss sales -- every closed position against the index -- "
               f"{run_ts.date().isoformat()}")
    out.append("")
    out.append(f"Run {run_ts.isoformat(timespec='minutes')}; closes settled "
               f"through {settled.isoformat()}. Prices and index levels come "
               f"from the tool's own price path (`vss.fetch.get_history`), "
               f"settled bars only. Fills are the watchlist's `sales:` "
               f"blocks as the owner booked them (FRAMEWORK-EDITS B45): a "
               f"fill with no price is DATA MISSING and is never read off a "
               f"bar. Index legs run from the index's close on the sale date "
               f"(the last close on or before it) to its last settled close. "
               f"SEK proceeds are as booked, net of the broker's charges and "
               f"FX, and are not blended with the price return.")
    out.append("")
    if not rows:
        out.append("No `sales:` block on any watchlist entry -- nothing to report.")
        return "\n".join(out)

    labels = [label for _, label in INDICES]
    head = (["Name", "Sale date", "Rule", "Shares", "Fill", "Proceeds SEK",
             "Last settled close", "Change since fill"] + labels
            + [f"{d}d" for d in MARK_DAYS] + ["Run record", "Account"])
    out.append("## Every fill")
    out.append("")
    out.append("| " + " | ".join(head) + " |")
    out.append("|" + "---|" * len(head))
    for r in rows:
        legs = {leg.label: leg for leg in r.index_legs}
        cells = [
            f"`{r.ticker}` {r.name} ({r.status})",
            r.sale.date.isoformat(),
            r.sale.rule,
            num(r.sale.shares, 0),
            _fill_cell(r),
            num(r.sale.proceeds_sek, 2) if r.sale.proceeds_sek is not None else DASH,
            (f"{num(r.last)} ({r.last_date.isoformat()})" if r.last is not None
             else (r.error or DATA_MISSING)),
            (f"**{DATA_MISSING}**" if not r.priced else pct(r.price_change)),
        ]
        for label in labels:
            leg = legs.get(label)
            if leg is None or leg.change is None:
                cells.append(DASH)
            else:
                cells.append(f"{pct(leg.change)} ({num(leg.at_sale)} on "
                             f"{leg.at_sale_date.isoformat()} -> "
                             f"{num(leg.later)} on {leg.later_date.isoformat()})")
        for m in r.marks:
            cells.append(_mark_cell(m, r.priced))
        cells.append(f"`{r.sale.run_record}`" if r.sale.run_record else DASH)
        cells.append(r.sale.account or DASH)
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    out.append(f"Mark cells read: name change / {' / '.join(labels)} over "
               f"the same window; `{NOT_YET}` until the mark date has settled.")
    out.append("")

    unpriced = [r for r in rows if not r.priced]
    if unpriced:
        out.append("## Fills with no price on file")
        out.append("")
        for r in unpriced:
            out.append(f"- `{r.ticker}` {r.sale.date.isoformat()}, "
                       f"{num(r.sale.shares, 0)} shares, rule {r.sale.rule}: "
                       f"{DATA_MISSING} -- enter the fill on the watchlist; "
                       f"nothing here reads it off a bar."
                       + (f" Note: {r.sale.note}" if r.sale.note else ""))
        out.append("")

    out.append("## By rule")
    out.append("")
    out.append("| Rule | Fills | Priced | Positions | Mean change since fill | "
               + " | ".join(f"Mean vs {label}" for label in labels) + " |")
    out.append("|---|---|---|---|---|" + "---|" * len(labels))
    for rule in sorted({r.sale.rule for r in rows}):
        group = [r for r in rows if r.sale.rule == rule]
        priced = [r for r in group if r.priced and r.price_change is not None]
        positions = len({r.ticker for r in group})
        mean_change = (sum(r.price_change for r in priced) / len(priced)
                       if priced else None)
        cells = [rule, str(len(group)), str(len(priced)), str(positions),
                 pct(mean_change)]
        for label in labels:
            diffs = []
            for r in priced:
                leg = next((l for l in r.index_legs if l.label == label), None)
                if leg is not None and leg.change is not None:
                    diffs.append(r.price_change - leg.change)
            cells.append(pct(sum(diffs) / len(diffs)) if diffs else DASH)
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    priced_total = sum(1 for r in rows if r.priced)
    out.append(f"**Sample: {len(rows)} fill(s) across "
               f"{len({r.ticker for r in rows})} position(s), {priced_total} "
               f"priced.** "
               + (f"Below {SAMPLE_FLOOR} priced fills nothing here can "
                  f"distinguish rule from luck; the table is a record, not "
                  f"evidence." if priced_total < SAMPLE_FLOOR else
                  f"Read the rule rows against their marks, not the to-date "
                  f"column alone."))
    out.append("")
    out.append(f"Written to `{written_to}`." if written_to
               else "DRY RUN -- nothing written.")
    return "\n".join(out)


# --- the command ---------------------------------------------------------------


Fetcher = Callable[[str], FetchResult]


def run_sales(*, watchlist_path: Path = WATCHLIST_PATH,
              cache_dir: Path = CACHE_DIR, reports_dir: Path = REPORTS_DIR,
              now: datetime | None = None, dry_run: bool = False,
              fetch: Fetcher | None = None) -> tuple[int, str]:
    """Build the sales record. Returns (exit code, markdown)."""
    run_ts = now or datetime.now().astimezone()
    settled = M.settled_through(run_ts)
    entries = [e for e in load_watchlist(watchlist_path) if e.sales]
    log.info("%d watchlist entries carry a sales block", len(entries))

    if fetch is None:
        def fetch(ticker: str) -> FetchResult:  # pragma: no cover - network
            return get_history(ticker, cache_dir, now=run_ts, write=not dry_run)

    index_closes: dict[str, pd.Series] = {}
    with contextlib.redirect_stdout(sys.stderr):
        for symbol, label in INDICES:
            fetched = fetch(symbol)
            index_closes[label] = settled_closes(fetched.frame, settled)
            if fetched.frame is None:
                log.error("%s (%s): %s", symbol, label, fetched.error)
        rows: list[FillRow] = []
        for entry in entries:
            fetched = fetch(entry.ticker)
            closes = settled_closes(fetched.frame, settled)
            error = None if fetched.frame is not None else (fetched.error or "no data")
            for sale in entry.sales:
                rows.append(fill_row(entry, sale, closes, index_closes,
                                     settled, error=error))
    rows.sort(key=lambda r: (r.sale.date, r.ticker))

    written: Path | None = None
    if not dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        written = reports_dir / f"SALES-RECORD-{run_ts.date().isoformat()}.md"
    markdown = render(rows, run_ts=run_ts, settled=settled, written_to=written)
    if written is not None:
        written.write_text(markdown + "\n", encoding="utf-8")
        log.info("wrote %s", written)
    return 0, markdown
