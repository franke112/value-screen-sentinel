"""Numeric computations for vss (SCOPE 3).

Pure functions: no network, no files, no clock. ``as_of`` is always passed in.

Semantics follow reference/SPEC.md 2, which does not conflict with SCOPE:
  * 52-week high is the highest daily CLOSE over the trailing 365 calendar
    days inclusive of today -- not the intraday high, which is jumpy and
    vendor-dependent.
  * Insufficient history returns None (DATA MISSING) rather than a
    shorter-window substitute.
  * The 52-week LOW (FRAMEWORK-EDITS E63) is the lowest daily CLOSE over
    the same window, under the same coverage bar, and the distance above
    it is a FIELD that no filter and no ranking key reads.
  * The 12-month return (FRAMEWORK-EDITS E127) is the close against the
    latest close on or before as_of - 365 days, under the same coverage
    bar. Filter 1 reads it; see `rules.fell_over_year`.
  * Volume ratio excludes today from its denominator.
  * Rows dated after ``as_of`` are dropped before anything is measured, so
    ``compute(df, as_of)`` answers for ``as_of`` whatever the frame carries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Sequence
from zoneinfo import ZoneInfo

import pandas as pd

RSI_PERIOD = 14
SMA_SHORT = 50
SMA_LONG = 200
VOLUME_WINDOW = 20
LOOKBACK_DAYS = 365

#: A SETTLED CLOSE IS NOT A LIVE PRINT (REVIEW-4 report A 4.2).
#:
#: `yfinance.history()` returns a bar for TODAY the moment the session
#: opens, and that bar carries the last trade as its `Close`. Nothing in the
#: frame distinguishes it from a settled close: both are dated today. The
#: cost is measured -- the DECK hand run of 2026-08-25 17:13 CEST priced the
#: name at 88.55 and the settled close that evening was 88.74; NKE's note
#: says 39.41 against a settled 39.48.
#:
#: The tool cannot ask the frame, so it asks the CLOCK. vss prices names on
#: NYSE/Nasdaq, Xetra, Stockholm, Copenhagen, Paris and London; the last of
#: those to settle is New York at 16:00 local. A run made before that instant
#: gets today's bar demoted for EVERY name -- including the European ones
#: whose own market has closed -- because one rule that is never wrong in
#: the dangerous direction beats six that are each right about one exchange.
#: The scheduled run (`deploy/vss.timer`, 22:30 Europe/Stockholm = 16:30 New
#: York) is unaffected; a hand run during the session loses one day of price
#: freshness, which the trading-day staleness gate absorbs.
LAST_MARKET_TZ = "America/New_York"
LAST_MARKET_CLOSE_HOUR = 16

#: HOW FAR BACK A SERIES MUST REACH BEFORE A 52-WEEK HIGH MEANS ANYTHING.
#:
#: `high_52w` is the maximum of the rows PRESENT in the trailing 365 days,
#: and nothing measured whether the rows covered it. REVIEW-4 report B 7.2,
#: RUN on DECK's own cache (501 rows, high 123.91, drawdown 28.4%):
#:
#:     rows served   52-week high   drawdown
#:     250           123.91         28.4%
#:     120           114.37         22.4%
#:      60           114.37         22.4%
#:      20           103.54         14.3%
#:
#: A short series passes the staleness gate -- its newest close is fresh --
#: and returns a SMALLER drawdown with nothing saying so. Gate 1's
#: dislocation band is a range, so understating a drawdown drops a name out
#: of it; and the 52-week high E11/E12 FREEZE at entry is struck off the
#: same number.
#:
#: The rule (ruled by the owner after REVIEW-4): 52 weeks PLUS five trading
#: days of date coverage. The five days are the margin that makes "52 weeks"
#: mean a window that is covered rather than one that is exactly reached --
#: a series of about 250 trading rows spans a bare year and may be missing
#: the first days of the window it claims to measure. Below the bar the
#: 52-week high and the drawdown are DATA MISSING. **Never a lower number.**
COVERAGE_WEEKS = 52
COVERAGE_MARGIN_TRADING_DAYS = 5


def coverage_start(as_of: date) -> date:
    """The LATEST first bar a series may carry and still measure 52 weeks."""
    day = as_of - timedelta(weeks=COVERAGE_WEEKS)
    remaining = COVERAGE_MARGIN_TRADING_DAYS
    while remaining:
        day -= timedelta(days=1)
        if day.weekday() < 5:
            remaining -= 1
    return day


def covers_52_weeks(first_bar: date | None, as_of: date) -> bool:
    """Does a series starting at ``first_bar`` cover the 52-week window?"""
    return first_bar is not None and first_bar <= coverage_start(as_of)


#: HOW LONG A LISTING MUST HAVE EXISTED BEFORE THIS FRAMEWORK CAN JUDGE IT.
#:
#: FRAMEWORK-EDITS E52, ruled by the owner 2026-08-27. Five years is the
#: shortest history in which this framework's own questions have answers:
#: 5.1 Method A reads a 5-YEAR median multiple, Gate 3 and E45 read eight
#: quarters, and a reverse DCF struck on a company that has never been
#: through a full cycle is a growth rate fitted to one regime.
#:
#: MEASURED ON THE SAME AXIS AS THE COVERAGE BAR ABOVE -- how far back the
#: first bar of the truncated series reaches -- and simply further. So every
#: series that fails `covers_52_weeks` also fails this, and NOT the reverse:
#: three years of history passes the coverage bar and fails here. The bar
#: above is NOT deleted; it governs what `high_52w` MEANS, inside this
#: function, and `vss run` prices the live watchlist through it without
#: passing filter 1 at all (E11/E12 freeze a drawdown against that high).
#:
#: This constant removes a NAME and lives at filter 1, not here: see
#: `filters.STEP_LISTING_AGE`. What lives here is only the measurement.
LISTING_AGE_YEARS = 5


def listing_age_start(as_of: date) -> date:
    """The LATEST first bar a series may carry and still be five years old.

    Calendar years, not trading days: the question is how long the listing
    has EXISTED, and a market's holiday count is not evidence about that.
    A 29 February start date lands on 28 February, which is the earlier of
    the two readings and so the stricter one.
    """
    try:
        return as_of.replace(year=as_of.year - LISTING_AGE_YEARS)
    except ValueError:                      # 29 February in a non-leap year
        return as_of.replace(year=as_of.year - LISTING_AGE_YEARS,
                             day=as_of.day - 1)


def covers_listing_age(first_bar: date | None, as_of: date) -> bool:
    """E52: does a series starting at ``first_bar`` reach five years back?"""
    return first_bar is not None and first_bar <= listing_age_start(as_of)


def settled_through(now: datetime) -> date:
    """The newest date whose bar may be read as a settled CLOSE at ``now``.

    Pure: it reads the clock it is HANDED, never `datetime.now()`.
    """
    local = now.astimezone(ZoneInfo(LAST_MARKET_TZ))
    if local.hour >= LAST_MARKET_CLOSE_HOUR:
        return local.date()
    return local.date() - timedelta(days=1)


@dataclass(frozen=True)
class Metrics:
    """Everything SCOPE 3 asks for. Any field may be None = DATA MISSING."""

    last_close: float | None = None
    last_close_date: date | None = None
    high_52w: float | None = None
    #: THE DATE THE 52-WEEK HIGH WAS SET (E11/E12). A drawdown is struck
    #: against a peak that leaves the rolling window a year and a day after
    #: it was set; PNDORA.CO left Gate 1's band on no new information when
    #: its 2025-08-22 peak aged out. Nothing recorded that date until
    #: 2026-08-26. Where the high printed more than once, the LATEST such
    #: session, because that is the one whose ageing-out ends the drawdown.
    high_52w_date: date | None = None
    drawdown: float | None = None
    #: THE OTHER END OF THE SAME WINDOW (FRAMEWORK-EDITS E63). The drawdown
    #: cannot tell a name that fell and stayed down from one that fell and
    #: has since recovered: CTSH on 2026-08-27 read 26.5% below its high and
    #: 64.7% above its 2026-06-30 low. `pct_above_52w_low` is
    #: (close - low) / low. All three are DATA MISSING together below the
    #: coverage bar -- a low struck off a shorter window is a HIGHER low and
    #: a SMALLER distance, the wrong direction. REPORTED, NEVER APPLIED:
    #: B41 was decided by E127: no threshold on the low, ever.
    low_52w: float | None = None
    low_52w_date: date | None = None
    pct_above_52w_low: float | None = None
    #: E127: THE CLOSE A YEAR AGO, and the return since. The drawdown is
    #: struck against a peak, so a name that went up fifteenfold and gave
    #: back 15% reads "dislocated" (HUNT.OL, 2026-09-26: 15.5% below a high
    #: set five days earlier, +1150% on the year). The latest close on or
    #: before as_of - LOOKBACK_DAYS; DATA MISSING below the coverage bar,
    #: never a return struck off a later, shorter window.
    close_year_ago: float | None = None
    close_year_ago_date: date | None = None
    return_12m: float | None = None
    rsi14: float | None = None
    sma50: float | None = None
    sma200: float | None = None
    pct_vs_sma50: float | None = None
    pct_vs_sma200: float | None = None
    avg_volume_20: float | None = None
    volume_ratio: float | None = None
    last_volume: float | None = None
    #: True when the run declared a settlement cutoff and `last_close` is a
    #: settled close; None when no cutoff was declared, which is DATA
    #: MISSING about the price's own standing and never a claim it settled.
    last_close_settled: bool | None = None
    #: The date of the newest bar DROPPED as a live print, or None. Printed
    #: so a reader can see that today's number was seen and not used.
    live_bar_date: date | None = None
    #: The oldest bar the series carries, and whether it reaches back far
    #: enough for a 52-week high to mean anything. False is why `high_52w`
    #: and `drawdown` are None -- a fact about the SERIES, not the company.
    first_bar_date: date | None = None
    covers_52_weeks: bool | None = None


def wilder_rsi(closes: Sequence[float], period: int = RSI_PERIOD) -> float | None:
    """RSI using Wilder's smoothing.

    Needs at least ``period + 1`` closes; fewer returns None rather than a
    partial estimate. An unbroken run of gains returns 100.0.
    """
    values = [float(c) for c in closes]
    if len(values) < period + 1:
        return None
    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def sma(closes: Sequence[float], window: int) -> float | None:
    """Simple mean of the trailing ``window`` closes, or None if too short."""
    values = [float(c) for c in closes]
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def index_dates(index) -> list[date]:
    """Exchange-local calendar date for each row of a price frame.

    Tolerant of tz-aware, tz-naive and plain-string indexes, including the
    MIXED UTC offsets a CSV cache produces when its series spans a daylight
    saving change (+02:00 rows and +01:00 rows in the same file). Reading
    such a file back with pd.to_datetime raises; converting to UTC would be
    worse, since it can shift a close onto the previous calendar day. We
    take each timestamp's own wall-clock date instead.
    """
    return [pd.Timestamp(value).date() for value in index]


def truncate(frame: pd.DataFrame, as_of: date) -> pd.DataFrame:
    """Drop every row dated after ``as_of``.

    Lives here, next to ``compute``, because it is the same idea: every
    number this module produces is a statement about a date, and a row the
    market printed after that date is not evidence about it.
    """
    if frame is None or len(frame) == 0:
        return frame
    keep = [d <= as_of for d in index_dates(frame.index)]
    return frame[pd.Series(keep, index=frame.index)]


def drop_unsettled(frame: pd.DataFrame, settled: date | None) -> pd.DataFrame:
    """Drop every row dated after ``settled``. ``None`` drops nothing.

    Separate from ``truncate`` because it answers a different question:
    ``truncate`` asks WHICH DAY we are speaking about, this asks whether the
    market has finished speaking about it.
    """
    if frame is None or len(frame) == 0 or settled is None:
        return frame
    keep = [d <= settled for d in index_dates(frame.index)]
    return frame[pd.Series(keep, index=frame.index)]


def high_52w(closes: pd.Series, as_of: date, lookback_days: int = LOOKBACK_DAYS) -> float | None:
    """Highest daily close in the trailing 365 calendar days inclusive of today."""
    if closes is None or len(closes) == 0:
        return None
    cutoff = as_of - timedelta(days=lookback_days)
    window = [
        float(v)
        for v, d in zip(closes.to_numpy(), index_dates(closes.index))
        if cutoff < d <= as_of and pd.notna(v)
    ]
    if not window:
        return None
    return max(window)


def high_52w_date(closes: pd.Series, as_of: date,
                  lookback_days: int = LOOKBACK_DAYS) -> date | None:
    """The session on which `high_52w` was set -- the latest one, on a tie."""
    if closes is None or len(closes) == 0:
        return None
    cutoff = as_of - timedelta(days=lookback_days)
    best: tuple[float, date] | None = None
    for v, d in zip(closes.to_numpy(), index_dates(closes.index)):
        if not (cutoff < d <= as_of) or pd.isna(v):
            continue
        value = float(v)
        if best is None or value > best[0] or (value == best[0] and d > best[1]):
            best = (value, d)
    return best[1] if best else None


def low_52w(closes: pd.Series, as_of: date, lookback_days: int = LOOKBACK_DAYS) -> float | None:
    """Lowest daily close in the trailing 365 calendar days inclusive of today (E63)."""
    if closes is None or len(closes) == 0:
        return None
    cutoff = as_of - timedelta(days=lookback_days)
    window = [
        float(v)
        for v, d in zip(closes.to_numpy(), index_dates(closes.index))
        if cutoff < d <= as_of and pd.notna(v)
    ]
    if not window:
        return None
    return min(window)


def low_52w_date(closes: pd.Series, as_of: date,
                 lookback_days: int = LOOKBACK_DAYS) -> date | None:
    """The session on which `low_52w` was set -- the latest one, on a tie.

    The latest for the same reason the high takes its latest print: it is
    the session after which any recovery is counted.
    """
    if closes is None or len(closes) == 0:
        return None
    cutoff = as_of - timedelta(days=lookback_days)
    best: tuple[float, date] | None = None
    for v, d in zip(closes.to_numpy(), index_dates(closes.index)):
        if not (cutoff < d <= as_of) or pd.isna(v):
            continue
        value = float(v)
        if best is None or value < best[0] or (value == best[0] and d > best[1]):
            best = (value, d)
    return best[1] if best else None


def close_year_ago(closes: pd.Series, as_of: date,
                   lookback_days: int = LOOKBACK_DAYS) -> tuple[float, date] | None:
    """The latest close on or before ``as_of - lookback_days``, with its date (E127).

    On or before, never after: a close from inside the year would shorten
    the window the return is measured over.
    """
    if closes is None or len(closes) == 0:
        return None
    cutoff = as_of - timedelta(days=lookback_days)
    best: tuple[float, date] | None = None
    for v, d in zip(closes.to_numpy(), index_dates(closes.index)):
        if d > cutoff or pd.isna(v):
            continue
        if best is None or d >= best[1]:
            best = (float(v), d)
    return best


def pct_above_low(last_close: float | None, low: float | None) -> float | None:
    """(close - low) / low, as a fraction. 64.7% above the low = 0.647 (E63)."""
    if last_close is None or low is None or low <= 0:
        return None
    return (float(last_close) - float(low)) / float(low)


def drawdown(last_close: float | None, high: float | None) -> float | None:
    """(high - close) / high, as a positive fraction. 22% off the high = 0.22."""
    if last_close is None or high is None or high <= 0:
        return None
    return (float(high) - float(last_close)) / float(high)


def pct_distance(value: float | None, reference: float | None) -> float | None:
    """(value - reference) / reference. Negative means value is below reference."""
    if value is None or reference is None or reference == 0:
        return None
    return (float(value) - float(reference)) / float(reference)


def avg_volume(volumes: Sequence[float], window: int = VOLUME_WINDOW) -> float | None:
    """Mean volume over the ``window`` sessions BEFORE the most recent one."""
    values = [float(v) for v in volumes]
    if len(values) < window + 1:
        return None
    prior = values[-(window + 1) : -1]
    return sum(prior) / window


def volume_ratio(last_volume: float | None, average: float | None) -> float | None:
    if last_volume is None or average is None or average == 0:
        return None
    return float(last_volume) / float(average)


def compute(df: pd.DataFrame, as_of: date,
            settled: date | None = None) -> Metrics:
    """Compute every SCOPE 3 metric from a daily OHLCV frame.

    ``df`` is indexed by date and must carry Close and Volume columns.
    An empty or column-less frame yields an all-None Metrics.

    ``settled`` is the newest date whose bar may be read as a settled close
    (`settled_through`). Rows after it are dropped and the newest of them is
    recorded on `Metrics.live_bar_date`. Passing None leaves the historic
    behaviour and says so on the result: `last_close_settled` is None, which
    is DATA MISSING about the price's standing -- NOT a claim that it
    settled. Callers with a clock (`vss run`) pass it; callers replaying a
    stored snapshot do not need to.
    """
    if df is None or len(df) == 0 or "Close" not in df.columns:
        return Metrics()

    # Truncate FIRST. Without this, ``as_of`` sizes the 52-week window but
    # ``last_close`` is still the frame's final row, so replaying an old date
    # against a longer series silently prices the past at today's close --
    # a 52-week high measured to July beside an August close. Everything
    # below is a statement about ``as_of`` and must be computed from rows
    # that existed by then.
    frame = truncate(df, as_of)
    if frame is None or len(frame) == 0:
        return Metrics()

    live_bar_date: date | None = None
    if settled is not None:
        dropped = [d for d in index_dates(frame.index) if d > settled]
        live_bar_date = max(dropped) if dropped else None
        frame = drop_unsettled(frame, settled)
        if frame is None or len(frame) == 0:
            return Metrics(last_close_settled=None, live_bar_date=live_bar_date)

    frame = frame.dropna(subset=["Close"])
    if len(frame) == 0:
        return Metrics()

    closes = frame["Close"]
    close_list = [float(c) for c in closes.to_numpy()]
    last_close = close_list[-1]
    last_close_date = index_dates(frame.index[-1:])[0]

    if "Volume" in frame.columns:
        volume_list = [0.0 if pd.isna(v) else float(v) for v in frame["Volume"].to_numpy()]
        last_volume: float | None = volume_list[-1]
    else:
        volume_list = []
        last_volume = None

    # THE 52-WEEK HIGH IS DATA MISSING BELOW THE COVERAGE BAR, never a
    # smaller number struck off whatever rows happened to arrive.
    first_bar_date = index_dates(frame.index[:1])[0]
    covered = covers_52_weeks(first_bar_date, as_of)
    high = high_52w(closes, as_of) if covered else None
    high_date = high_52w_date(closes, as_of) if covered else None
    # E63: the same bar governs the low. Never a higher low off fewer rows.
    low = low_52w(closes, as_of) if covered else None
    low_date = low_52w_date(closes, as_of) if covered else None
    # E127: the same bar again. Below it there may be no close a year back.
    year_ago = close_year_ago(closes, as_of) if covered else None
    sma50 = sma(close_list, SMA_SHORT)
    sma200 = sma(close_list, SMA_LONG)
    avg_vol = avg_volume(volume_list) if volume_list else None

    return Metrics(
        last_close=last_close,
        last_close_date=last_close_date,
        high_52w=high,
        high_52w_date=high_date,
        drawdown=drawdown(last_close, high),
        low_52w=low,
        low_52w_date=low_date,
        pct_above_52w_low=pct_above_low(last_close, low),
        close_year_ago=year_ago[0] if year_ago else None,
        close_year_ago_date=year_ago[1] if year_ago else None,
        return_12m=pct_distance(last_close, year_ago[0]) if year_ago else None,
        rsi14=wilder_rsi(close_list),
        sma50=sma50,
        sma200=sma200,
        pct_vs_sma50=pct_distance(last_close, sma50),
        pct_vs_sma200=pct_distance(last_close, sma200),
        avg_volume_20=avg_vol,
        volume_ratio=volume_ratio(last_volume, avg_vol),
        last_volume=last_volume,
        last_close_settled=None if settled is None else True,
        live_bar_date=live_bar_date,
        first_bar_date=first_bar_date,
        covers_52_weeks=covered,
    )
