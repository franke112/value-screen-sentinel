"""Fundamentals retrieval for the survivors of filter 1 (screener step 3).

This is the expensive half of the two-step architecture. Prices batch fifty at
a time; fundamentals do not batch at all, so they are fetched ONE TICKER AT A
TIME and only for names that already cleared the price filter. Fetching them
for the whole universe would be some 13,000 serial requests to answer a
question most of those names have already failed.

TWO STATUS LAYERS, and they are not the same question:

  * per TICKER  -- did we reach Yahoo for this name at all?
        OK / THROTTLED / NO_DATA / STALE, the same four as prices.py.
  * per FIELD   -- did this particular number come back?
        OK / NO_DATA, and THROTTLED when the whole ticker was refused.

A company can report free cash flow and no EBITDA -- every bank in the
universe does exactly that -- and a ticker-level "OK" would hide it. The
field layer is what makes the missing-data column of the yield report mean
something on a limb-by-limb basis.

STALE is not a fetch outcome here either. It is decided after the data
arrives, from the newest fiscal period end: a company whose last reported
year is older than the limit has answered, but not recently enough to screen
on.

Currency: ``financialCurrency`` frequently differs from the quote currency --
Equinor reports in USD and trades in NOK. Every limb filter 2 evaluates is a
sign or a ratio of two figures from the SAME statement, so the currency
cancels and phase 3 needs no FX source. Tier C's floors still do; those
compare a company's size against an absolute amount.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable, Iterable, Mapping, Sequence

import pandas as pd

from .prices import (
    BACKOFF_CAP_SECONDS,
    MAX_ATTEMPTS,
    STATUS_NO_DATA,
    STATUS_OK,
    STATUS_STALE,
    STATUS_THROTTLED,
    backoff_delay,
    is_throttle,
)
from .universe import ON_MISSING, ON_VALUE, Tally

log = logging.getLogger(__name__)

#: Scalar fields taken from the quote summary. Text fields first.
TEXT_FIELDS: tuple[str, ...] = (
    "sector", "industry", "financialCurrency", "currency", "quoteType",
)
#: ``regularMarketPrice`` is THE QUOTE THE VENDOR'S ``marketCap`` EMBEDS at
#: the moment of the fetch. The ranking divides the two to recover the
#: vendor's own share count, then re-prices that count at the SETTLED close
#: of the run date (SCREENER-REVIEW-3 CLOSE, item 1): ``enterpriseValue`` is
#: NOT a function of the fetch-day price -- between two fetches eleven hours
#: apart marketCap moved for 450 of 473 names and enterpriseValue for 3 --
#: so it is kept as a memo and read by nothing.
NUMERIC_FIELDS: tuple[str, ...] = (
    "freeCashflow", "operatingCashflow", "totalRevenue", "revenueGrowth",
    "ebitda", "totalDebt", "totalCash", "enterpriseValue", "marketCap",
    "regularMarketPrice",
)
ALL_FIELDS: tuple[str, ...] = TEXT_FIELDS + NUMERIC_FIELDS

#: Income-statement lines kept as an annual series. Revenue is what filter 2's
#: revenue-trend limb needs -- a trend is not a scalar, and the quote summary's
#: ``revenueGrowth`` is a single year-over-year number. EBIT and its aliases
#: are what the ranking key needs; ``ebitda`` is carried for reporting only and
#: is NEVER a substitute for EBIT (FRAMEWORK-EDITS E5).
INCOME_LINES: tuple[str, ...] = (
    "Total Revenue", "EBITDA", "EBIT", "Operating Income",
    "Total Operating Income As Reported", "Net Income", "Gross Profit",
)

#: Balance-sheet lines. The ranking key's quality denominator is total assets
#: (FRAMEWORK-EDITS E6); the current-asset, current-liability and net PP&E
#: lines are kept because E5 used them, because net PP&E is one of the four
#: figures the share-class fingerprint matches on, and because dropping a
#: stored line would make an old run unreadable. Long-term debt is carried for
#: reporting.
BALANCE_LINES: tuple[str, ...] = (
    "Total Assets", "Current Assets", "Total Current Assets",
    "Current Liabilities", "Total Current Liabilities",
    "Net PPE", "Net Property Plant And Equipment",
    "Long Term Debt", "Long Term Debt And Capital Lease Obligation",
    "Ordinary Shares Number",
)

#: QUARTERLY STATEMENTS (E13 as written; SCREENER-REVIEW-3 build item 8).
#: The ranking key is struck on trailing twelve months, and until 2026-08-26
#: the vendor path stored annual statements only, so every ranked name was
#: on a fiscal year that -- for three of the six would-be PIPELINE names --
#: predated the fall that admitted it (report A 4.4: BUCN.SW #2 on FY2025,
#: #17 on the twelve months its interim reports). The quarterly income
#: statement and quarterly balance sheet are now fetched beside the annual
#: ones, under their OWN statement names: a Q4 row and the annual row share
#: a period end, and the store's key is (ticker, statement, line, period_end).
#:
#: THE KNOWN INSTABILITY (yfinance issue #1345): the quarterly endpoint
#: returns holes -- a missing quarter, a NaN value, an empty frame for a
#: half-yearly reporter (BUCN.SW, FGR.PA, HWDN.L on 2026-08-26), or a
#: failure on one call. Each is DATA MISSING for THAT ticker's twelve-month
#: basis, never a zero and never filled: the ranking then falls back to the
#: annual figure and says so in the basis column.
#: THE ANNUAL CASH FLOW STATEMENT, added 2026-09-04. Two lines and no more:
#: the operating cash flow and the capital expenditure, which between them
#: are free cash flow -- there is no free cash flow LINE to store, in this
#: vendor's frame or in any taxonomy, because it is a non-GAAP APM.
#:
#: WHY A LINE NOTHING GATED ON IS NOW STORED. The rule this file kept was
#: that *a stored line nothing reads is a line nobody checks*, and the cash
#: flow statement was the example. `vss/medians.py` reads these two, for the
#: `fcf_vs_5y_median` column on every ranked row -- a PRINTED column that
#: filters nothing. The rule is not weakened: the lines are read, and by
#: something a reader sees.
CASHFLOW_LINES: tuple[str, ...] = (
    "Operating Cash Flow", "Cash Flow From Continuing Operating Activities",
    "Capital Expenditure", "Purchase Of PPE",
)

SERIES_LINES: dict[str, tuple[str, ...]] = {
    "income": INCOME_LINES,
    "balance": BALANCE_LINES,
    "income_quarterly": INCOME_LINES,
    "balance_quarterly": BALANCE_LINES,
    "cashflow": CASHFLOW_LINES,
}

#: Months in a period this basis knows: the annual statements are twelve,
#: the quarterly ones three, a stock line has no length. ONE place for the
#: two numbers; the ranking imports them.
ANNUAL_MONTHS = 12
QUARTER_MONTHS = 3

#: How long a FLOW line from each statement covers, by the endpoint that was
#: called -- a fact about the request, not a guess about the figure.
STATEMENT_MONTHS: dict[str, int | None] = {
    "income": ANNUAL_MONTHS,
    "income_quarterly": QUARTER_MONTHS,
    "balance": None,
    "balance_quarterly": None,
    # A FLOW, and twelve months of one: the ANNUAL statement is fetched and
    # the quarterly one still is not.
    "cashflow": ANNUAL_MONTHS,
}

#: Which yfinance attribute each statement name is read from.
STATEMENT_ATTRIBUTES: tuple[tuple[str, str], ...] = (
    ("income", "income_stmt"),
    ("balance", "balance_sheet"),
    ("income_quarterly", "quarterly_income_stmt"),
    ("balance_quarterly", "quarterly_balance_sheet"),
    ("cashflow", "cashflow"),
)

#: Requests per ticker. SIX, all per-ticker: the quote summary, the annual
#: income statement, balance sheet and CASH FLOW STATEMENT, and the
#: quarterly income statement and balance sheet. This is the cost the
#: two-step architecture exists to contain, and the sixth was added
#: 2026-09-04 knowingly: it is a fifth of the run again on a ~540-name
#: universe, and it is what `fcf_vs_5y_median` is built from.
#:
#: THE QUARTERLY CASH-FLOW STATEMENT IS STILL NOT FETCHED, and the rule that
#: kept it out is unchanged: no ruled limb reads it (the revenue kill of E45
#: reads the income statement), and a stored line nothing reads is a line
#: nobody checks. The ANNUAL one is now read -- by `vss/medians.py`, for a
#: printed column -- which is the condition the rule always stated.
REQUESTS_PER_TICKER = 6

#: A company whose newest annual period ended more than this long before the
#: fetch has reported, but not recently enough to screen on.
MAX_REPORT_AGE_DAYS = 550

#: Politeness pause between tickers. Measured at 0.47s/ticker without one;
#: this keeps a 536-name run near seven minutes while staying well inside
#: what the endpoint tolerated.
INTER_TICKER_SECONDS = 0.25

FIELD_OK = "OK"
FIELD_NO_DATA = "NO_DATA"
FIELD_THROTTLED = "THROTTLED"


@dataclass(frozen=True)
class FieldValue:
    ticker: str
    name: str
    status: str
    number: float | None = None
    text: str | None = None


@dataclass(frozen=True)
class SeriesPoint:
    ticker: str
    line: str
    period_end: date
    value: float | None
    #: Which statement the line came from. "Total Assets" and "EBIT" do not
    #: collide today, but a reader should not have to know that to be right.
    #: It is also what says whether the line is a FLOW (income: a quantity
    #: measured OVER a period) or a STOCK (balance: a quantity AT an
    #: instant), which decides whether ``period_months`` applies at all.
    statement: str = "income"
    #: HOW LONG A PERIOD THIS FIGURE COVERS, in months, for a FLOW line.
    #: None on a stock line, where it does not apply, and None on a flow
    #: line whose length nobody recorded -- which FRAMEWORK-EDITS E13 calls
    #: NOT MEANINGFUL and refuses to rank, rather than assuming a basis.
    #:
    #: It exists because the ranking key compares figures ACROSS COMPANIES
    #: and a quarter's gross profit against a year's is a factor of four
    #: with nothing saying so (backlog B-8, first found on PNDORA.CO).
    period_months: int | None = None


@dataclass(frozen=True)
class TickerFundamentals:
    ticker: str
    status: str
    attempts: int
    requests: int
    fields: tuple[FieldValue, ...] = ()
    series: tuple[SeriesPoint, ...] = ()
    error: str | None = None
    newest_period: date | None = None
    #: WHICH PATH SUPPLIED THIS RECORD. Default is the quote vendor, which
    #: is the only source this module fetches. `vss/manual.py` builds the
    #: same object out of hand-entered figures and stamps its own, so a
    #: reader of any downstream output can see which path a figure came
    #: from without having to know which command produced it.
    origin: str = "yfinance"
    #: WHEN THIS RECORD'S STATUS AND FIELDS WERE FETCHED. Stamped by the
    #: store, not by the fetch: under FRAMEWORK-EDITS E49 one store holds
    #: several fetches, and the date `totalDebt` and `totalCash` carry is
    #: this record's, not the file's latest. None on a record that has not
    #: been through the store.
    fetched_at: datetime | None = None

    @property
    def ok(self) -> bool:
        return self.status == STATUS_OK

    def value(self, name: str) -> float | None:
        for item in self.fields:
            if item.name == name and item.status == FIELD_OK:
                return item.number
        return None

    def text(self, name: str) -> str | None:
        for item in self.fields:
            if item.name == name and item.status == FIELD_OK:
                return item.text
        return None

    def revenue_series(self) -> list[tuple[date, float]]:
        """The ANNUAL revenue points, oldest first -- the annual fallback of
        the revenue limb and the coverage histogram. A quarterly point is
        never in it: a year and a quarter in one trend differ by a factor
        of four."""
        return self.annual_series("Total Revenue")

    def annual_series(self, *aliases: str) -> list[tuple[date, float]]:
        """Dated ANNUAL values for the first alias that has any. A point of
        unrecorded length counts as annual here: every such row was written
        by the annual endpoint before lengths were stored."""
        return self.line_series(*aliases, months=(ANNUAL_MONTHS, None))

    def quarterly_series(self, *aliases: str) -> list[tuple[date, float]]:
        """Dated QUARTERLY values for the first alias that has any, oldest
        first. Holes -- a missing quarter, a NaN -- are simply absent: the
        caller decides what four consecutive quarters means (E13)."""
        return self.line_series(*aliases, months=(QUARTER_MONTHS,))

    def line_series(self, *aliases: str,
                    months: tuple[int | None, ...] | None = None) -> list[tuple[date, float]]:
        """Dated values for the FIRST alias that has any, oldest first.

        Aliases are tried in order and never mixed: a company reporting both
        ``Current Liabilities`` and ``Total Current Liabilities`` must not have
        its series stitched together from whichever happened to be present in
        each year. ``months`` restricts the points to those period lengths;
        None takes every point of every length, which is what a STOCK line
        wants and what a flow line must NOT be read with.
        """
        for alias in aliases:
            points = sorted(
                (p.period_end, p.value) for p in self.series
                if p.line == alias and p.value is not None
                and (months is None or p.period_months in months)
            )
            if points:
                return points
        return []

    def latest(self, *aliases: str) -> tuple[date, float] | None:
        """Most recent value, of ANY period length, for the first alias that
        has one -- E13's "latest period end" for a stock line.

        Returns None -- DATA MISSING -- when no alias is present. An absent
        line is never read as zero (FRAMEWORK-EDITS E5).
        """
        points = self.line_series(*aliases)
        return points[-1] if points else None

    def at(self, period_end: date, *aliases: str) -> tuple[date, float] | None:
        """The value of a STOCK line AT one period end, or None.

        K6 in E13's terms: a flow to 30 June is a ratio with total assets AT
        30 June and with nothing else, so the denominator is looked up at
        the window's end rather than taken as the newest point. Read across
        statements: the annual and the quarterly balance sheet both carry a
        year-end, and either may be the one that has it.
        """
        for alias in aliases:
            for p in self.series:
                if p.line == alias and p.period_end == period_end and p.value is not None:
                    return (p.period_end, p.value)
        return None


@dataclass
class FundamentalsOutcome:
    records: list[TickerFundamentals] = field(default_factory=list)
    tally: Tally = field(default_factory=lambda: Tally("fundamentals_fetch"))
    requests: int = 0
    fetched_at: datetime | None = None

    def by_ticker(self) -> dict[str, TickerFundamentals]:
        return {r.ticker: r for r in self.records}


# --- the fetch -------------------------------------------------------------


def default_reader(ticker: str) -> tuple[Mapping, Mapping[str, pd.DataFrame | None], int]:
    """One ticker, five requests. Replaced wholesale in tests.

    A statement that fails to arrive is None -- no rows, DATA MISSING for
    that ticker on that statement, never an empty frame read as zeros. The
    quarterly endpoints fail and return holes more often than the annual
    ones (yfinance #1345); the fallback is the ranking's, not this reader's.
    """
    import yfinance as yf

    handle = yf.Ticker(ticker)
    info = handle.info or {}
    statements: dict[str, pd.DataFrame | None] = {}
    for name, attribute in STATEMENT_ATTRIBUTES:
        try:
            statements[name] = getattr(handle, attribute)
        except Exception as exc:  # noqa: BLE001 - one statement failing is not fatal
            log.debug("%s: %s unavailable (%s)", ticker, attribute, exc)
            statements[name] = None
    return info, statements, REQUESTS_PER_TICKER


def _numeric(value) -> float | None:
    if value is None:
        return None
    try:
        if isinstance(value, bool):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def extract_fields(ticker: str, info: Mapping) -> list[FieldValue]:
    out: list[FieldValue] = []
    for name in TEXT_FIELDS:
        raw = info.get(name)
        text = str(raw).strip() if raw not in (None, "") else None
        out.append(
            FieldValue(ticker, name, FIELD_OK if text else FIELD_NO_DATA, text=text)
        )
    for name in NUMERIC_FIELDS:
        number = _numeric(info.get(name))
        out.append(
            FieldValue(
                ticker, name, FIELD_OK if number is not None else FIELD_NO_DATA,
                number=number,
            )
        )
    return out


def extract_series(ticker: str, statements) -> list[SeriesPoint]:
    """Every wanted line from every statement, as dated points that know
    how long a period they cover.

    Accepts a mapping of statement name to frame. A bare frame is read as the
    income statement, so older callers and fixtures keep working. A NaN cell
    is a point with ``value`` None -- a hole the ranking sees as a missing
    quarter, never a zero.
    """
    if statements is None:
        return []
    if not isinstance(statements, Mapping):
        statements = {"income": statements}
    out: list[SeriesPoint] = []
    for name, frame in statements.items():
        if frame is None or getattr(frame, "empty", True):
            continue
        for line in SERIES_LINES.get(name, ()):
            if line not in frame.index:
                continue
            for column in frame.columns:
                period = pd.Timestamp(column).date()
                out.append(
                    SeriesPoint(ticker, line, period,
                                _numeric(frame.loc[line, column]), name,
                                # THE LENGTH IS A FACT ABOUT THE ENDPOINT THAT
                                # WAS CALLED, not a guess about the figure:
                                # `income_stmt` IS the annual statement and
                                # `quarterly_income_stmt` the quarterly one.
                                # A stock line has no length and gets none.
                                STATEMENT_MONTHS.get(name))
                )
    return out


def newest_period(series: Sequence[SeriesPoint]) -> date | None:
    periods = [p.period_end for p in series if p.value is not None]
    return max(periods) if periods else None


def fetch_one(
    ticker: str,
    *,
    as_of: date,
    reader: Callable[[str], tuple[Mapping, pd.DataFrame | None, int]] = default_reader,
    sleep: Callable[[float], None] = time.sleep,
    max_attempts: int = MAX_ATTEMPTS,
    max_report_age_days: int = MAX_REPORT_AGE_DAYS,
) -> TickerFundamentals:
    """One ticker, with retry and backoff. Never raises."""
    attempts, requests, last_error = 0, 0, None
    info: Mapping | None = None
    statements = None
    throttled = False

    while attempts < max_attempts:
        attempts += 1
        try:
            info, statements, made = reader(ticker)
            requests += made
            last_error, throttled = None, False
            break
        except Exception as exc:  # noqa: BLE001 - classified, then retried
            requests += 1
            last_error = f"{type(exc).__name__}: {exc}"
            throttled = is_throttle(exc)
            if attempts >= max_attempts:
                break
            delay = backoff_delay(attempts)
            log.warning("%s: attempt %d failed (%s); retrying in %.1fs",
                        ticker, attempts, last_error, delay)
            sleep(min(delay, BACKOFF_CAP_SECONDS))

    if last_error is not None:
        status = STATUS_THROTTLED if throttled else STATUS_NO_DATA
        fields = tuple(
            FieldValue(ticker, name, FIELD_THROTTLED if throttled else FIELD_NO_DATA)
            for name in ALL_FIELDS
        )
        return TickerFundamentals(ticker, status, attempts, requests, fields,
                                  error=last_error)

    fields = tuple(extract_fields(ticker, info or {}))
    series = tuple(extract_series(ticker, statements))
    period = newest_period(series)

    if all(f.status == FIELD_NO_DATA for f in fields) and not series:
        return TickerFundamentals(
            ticker, STATUS_NO_DATA, attempts, requests, fields, series,
            error="the response carried none of the requested fields",
        )

    status = STATUS_OK
    error = None
    if period is not None and (as_of - period).days > max_report_age_days:
        # Reported, but not recently enough to screen on. A VALUE we have,
        # judged too old -- the same shape as a stale close.
        status = STATUS_STALE
        error = (f"newest reported period {period.isoformat()} is "
                 f"{(as_of - period).days} days before {as_of.isoformat()}")

    return TickerFundamentals(ticker, status, attempts, requests, fields, series,
                              error=error, newest_period=period)


def fetch_many(
    tickers: Sequence[str],
    *,
    as_of: date,
    reader: Callable[[str], tuple[Mapping, pd.DataFrame | None, int]] = default_reader,
    sleep: Callable[[float], None] = time.sleep,
    max_attempts: int = MAX_ATTEMPTS,
    inter_ticker_seconds: float = INTER_TICKER_SECONDS,
    on_progress: Callable[[int, int, TickerFundamentals], None] | None = None,
    now: datetime | None = None,
) -> FundamentalsOutcome:
    outcome = FundamentalsOutcome(fetched_at=now or datetime.now())
    outcome.tally = Tally("fundamentals_fetch", count_in=len(tickers))

    for index, ticker in enumerate(tickers, start=1):
        record = fetch_one(ticker, as_of=as_of, reader=reader, sleep=sleep,
                           max_attempts=max_attempts)
        outcome.records.append(record)
        outcome.requests += record.requests
        if on_progress:
            on_progress(index, len(tickers), record)
        if index < len(tickers) and inter_ticker_seconds:
            sleep(inter_ticker_seconds)

    for record in outcome.records:
        if record.status == STATUS_OK:
            continue
        if record.status == STATUS_STALE:
            outcome.tally.reject(ON_VALUE, "newest reported period older than the limit")
        else:
            outcome.tally.reject(ON_MISSING, f"no fundamentals ({record.status})")
    outcome.tally.count_out = sum(1 for r in outcome.records if r.status == STATUS_OK)
    return outcome


# --- coverage --------------------------------------------------------------


def field_coverage(records: Iterable[TickerFundamentals]) -> dict[str, dict[str, int]]:
    """Per FIELD: how many tickers carry it, and how many do not.

    This is the table that says where coverage breaks. A ticker counted OK at
    the ticker level can still be NO_DATA on the one field a limb needs.
    """
    table: dict[str, dict[str, int]] = {
        name: {FIELD_OK: 0, FIELD_NO_DATA: 0, FIELD_THROTTLED: 0} for name in ALL_FIELDS
    }
    for record in records:
        for item in record.fields:
            row = table.setdefault(
                item.name, {FIELD_OK: 0, FIELD_NO_DATA: 0, FIELD_THROTTLED: 0}
            )
            row[item.status] = row.get(item.status, 0) + 1
    return table


def status_counts(records: Iterable[TickerFundamentals]) -> dict[str, int]:
    counts = {s: 0 for s in (STATUS_OK, STATUS_THROTTLED, STATUS_NO_DATA, STATUS_STALE)}
    for record in records:
        counts[record.status] = counts.get(record.status, 0) + 1
    return counts


def quarterly_coverage(records: Iterable[TickerFundamentals],
                       line: str = "Total Revenue") -> dict[int, int]:
    """How many QUARTERLY points of ``line`` each ticker carries, as a
    histogram. Zero is a real bucket: a half-yearly reporter, or a ticker
    whose quarterly endpoint returned nothing (#1345)."""
    histogram: dict[int, int] = {}
    for record in records:
        count = len(record.quarterly_series(line))
        histogram[count] = histogram.get(count, 0) + 1
    return dict(sorted(histogram.items()))


def series_coverage(records: Iterable[TickerFundamentals]) -> dict[int, int]:
    """How many annual revenue points each ticker carries, as a histogram."""
    histogram: dict[int, int] = {}
    for record in records:
        count = len(record.revenue_series())
        histogram[count] = histogram.get(count, 0) + 1
    return dict(sorted(histogram.items()))
