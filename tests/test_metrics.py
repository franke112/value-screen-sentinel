"""Tests for the SCOPE 3 computations."""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

from vss import metrics as M
from tests._vendor_data import need


def series_from_deltas(start: float, deltas: list[float]) -> list[float]:
    closes = [start]
    for d in deltas:
        closes.append(closes[-1] + d)
    return closes


def frame(closes: list[float], volumes: list[float] | None = None, end: date | None = None):
    """Daily OHLCV frame ending on ``end``, one calendar day per row."""
    end = end or date(2026, 8, 20)
    index = pd.to_datetime(
        [end - timedelta(days=len(closes) - 1 - i) for i in range(len(closes))]
    )
    data = {"Close": closes}
    data["Volume"] = volumes if volumes is not None else [1000.0] * len(closes)
    return pd.DataFrame(data, index=index)


# --- RSI(14), Wilder's ----------------------------------------------------


def test_rsi_exactly_30():
    """6 gains of +1 vs 8 losses of -1.75 gives avg_gain/avg_loss = 3/7 -> RSI 30."""
    closes = series_from_deltas(100.0, [1.0] * 6 + [-1.75] * 8)
    assert M.wilder_rsi(closes) == pytest.approx(30.0)


def test_rsi_exactly_70():
    """8 gains of +1.75 vs 6 losses of -1 gives avg_gain/avg_loss = 7/3 -> RSI 70."""
    closes = series_from_deltas(100.0, [1.75] * 8 + [-1.0] * 6)
    assert M.wilder_rsi(closes) == pytest.approx(70.0)


def test_rsi_needs_15_closes():
    closes = series_from_deltas(100.0, [1.0] * 13)  # 14 closes
    assert len(closes) == 14
    assert M.wilder_rsi(closes) is None
    assert M.wilder_rsi(closes + [101.0]) is not None


def test_rsi_all_gains_is_100():
    assert M.wilder_rsi(series_from_deltas(100.0, [1.0] * 14)) == pytest.approx(100.0)


def test_rsi_all_losses_is_0():
    assert M.wilder_rsi(series_from_deltas(100.0, [-1.0] * 14)) == pytest.approx(0.0)


def test_rsi_uses_wilder_not_simple_mean():
    """With more than 15 closes the smoothing must diverge from a simple mean."""
    closes = series_from_deltas(100.0, [1.0] * 6 + [-1.75] * 8 + [3.0, -0.5, 2.0])
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [d for d in deltas[-14:] if d > 0]
    losses = [-d for d in deltas[-14:] if d < 0]
    simple = 100 - 100 / (1 + (sum(gains) / 14) / (sum(losses) / 14))
    assert M.wilder_rsi(closes) != pytest.approx(simple)


# --- SMA ------------------------------------------------------------------


def test_sma_is_mean_of_trailing_window():
    assert M.sma([1, 2, 3, 4, 5], 5) == pytest.approx(3.0)
    assert M.sma([1, 2, 3, 4, 5], 2) == pytest.approx(4.5)


def test_sma_insufficient_history_is_none_never_shorter_window():
    assert M.sma([1.0] * 49, 50) is None
    assert M.sma([1.0] * 199, 200) is None
    assert M.sma([1.0] * 200, 200) == pytest.approx(1.0)


def test_compute_reports_sma_data_missing_on_short_history():
    m = M.compute(frame([100.0] * 60), date(2026, 8, 20))
    assert m.sma50 is not None
    assert m.sma200 is None
    assert m.pct_vs_sma200 is None


# --- 52w high and drawdown ------------------------------------------------


def test_high_52w_uses_closing_high_within_window():
    closes = [50.0, 120.0, 80.0, 90.0]
    f = frame(closes, end=date(2026, 8, 20))
    assert M.high_52w(f["Close"], date(2026, 8, 20)) == pytest.approx(120.0)


def test_high_52w_excludes_closes_older_than_365_days():
    end = date(2026, 8, 20)
    index = pd.to_datetime([end - timedelta(days=400), end - timedelta(days=10), end])
    closes = pd.Series([999.0, 100.0, 90.0], index=index)
    assert M.high_52w(closes, end) == pytest.approx(100.0)


def test_drawdown_is_positive_fraction():
    assert M.drawdown(78.0, 100.0) == pytest.approx(0.22)
    assert M.drawdown(100.0, 100.0) == pytest.approx(0.0)


def test_drawdown_exactly_15_and_50_percent():
    assert M.drawdown(85.0, 100.0) == pytest.approx(0.15)
    assert M.drawdown(50.0, 100.0) == pytest.approx(0.50)


def test_drawdown_missing_inputs():
    assert M.drawdown(None, 100.0) is None
    assert M.drawdown(85.0, None) is None
    assert M.drawdown(85.0, 0.0) is None


# --- distances ------------------------------------------------------------


def test_pct_distance_sign():
    assert M.pct_distance(90.0, 100.0) == pytest.approx(-0.10)
    assert M.pct_distance(110.0, 100.0) == pytest.approx(0.10)
    assert M.pct_distance(100.0, 100.0) == pytest.approx(0.0)


def test_pct_distance_missing_inputs():
    assert M.pct_distance(None, 100.0) is None
    assert M.pct_distance(100.0, None) is None
    assert M.pct_distance(100.0, 0.0) is None


# --- volume ---------------------------------------------------------------


def test_avg_volume_excludes_today():
    volumes = [100.0] * 20 + [9999.0]  # today is the spike
    assert M.avg_volume(volumes, window=20) == pytest.approx(100.0)


def test_avg_volume_needs_21_sessions():
    assert M.avg_volume([100.0] * 20, window=20) is None
    assert M.avg_volume([100.0] * 21, window=20) == pytest.approx(100.0)


def test_volume_ratio():
    assert M.volume_ratio(200.0, 100.0) == pytest.approx(2.0)
    assert M.volume_ratio(None, 100.0) is None
    assert M.volume_ratio(200.0, None) is None
    assert M.volume_ratio(200.0, 0.0) is None


# --- compute() end to end -------------------------------------------------


def test_compute_full_frame():
    # 400 rows, one per CALENDAR day, so the series reaches back past the
    # 52-week-plus-five-trading-days coverage bar (REVIEW-4 report B 7.2).
    closes = [100.0] * 399 + [85.0]
    volumes = [100.0] * 399 + [300.0]
    m = M.compute(frame(closes, volumes, end=date(2026, 8, 20)), date(2026, 8, 20))
    assert m.last_close == pytest.approx(85.0)
    assert m.last_close_date == date(2026, 8, 20)
    assert m.high_52w == pytest.approx(100.0)
    assert m.drawdown == pytest.approx(0.15)
    assert m.avg_volume_20 == pytest.approx(100.0)
    assert m.volume_ratio == pytest.approx(3.0)


def test_compute_empty_frame_is_all_data_missing():
    m = M.compute(pd.DataFrame(), date(2026, 8, 20))
    assert m.last_close is None and m.drawdown is None and m.rsi14 is None


# --- compute honours as_of -------------------------------------------------

SAP_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures" / "verdict-matrix" / "prices" / "SAP.DE.csv"
)


def read_fixture(path: Path) -> pd.DataFrame:
    need(path)
    frame = pd.read_csv(path, index_col=0)
    frame.index = pd.DatetimeIndex(
        [pd.Timestamp(v).tz_localize(None) if pd.Timestamp(v).tzinfo else pd.Timestamp(v)
         for v in frame.index]
    )
    return frame


def test_truncate_drops_rows_after_as_of():
    frame = read_fixture(SAP_FIXTURE)
    cut = M.truncate(frame, date(2026, 7, 27))
    assert len(cut) < len(frame)
    assert max(M.index_dates(cut.index)) <= date(2026, 7, 27)


def test_truncate_leaves_an_earlier_series_alone():
    frame = read_fixture(SAP_FIXTURE)
    assert len(M.truncate(frame, date(2027, 1, 1))) == len(frame)


def test_truncate_tolerates_an_empty_frame():
    empty = pd.DataFrame()
    assert len(M.truncate(empty, date(2026, 7, 27))) == 0


def test_sap_measures_differently_on_two_dates_from_one_series():
    """The whole point of truncating, on real prices.

    Before the fix, ``as_of`` sized the 52-week window but ``last_close``
    stayed the frame's final row, so both dates reported the same close. A
    replay of 2026-07-27 would then have been scored at the 2026-08-20 price
    -- and the phase 2 acceptance test would have passed for the wrong
    reason.
    """
    frame = read_fixture(SAP_FIXTURE)
    july = M.compute(frame, date(2026, 7, 27))
    august = M.compute(frame, date(2026, 8, 21))

    assert july.last_close != august.last_close
    assert july.last_close_date == date(2026, 7, 27)
    assert august.last_close_date == date(2026, 8, 20)   # the fixture's last row
    assert july.high_52w != august.high_52w
    assert july.rsi14 != august.rsi14
    assert july.sma50 != august.sma50


def test_a_truncated_frame_and_a_pre_cut_frame_agree():
    frame = read_fixture(SAP_FIXTURE)
    as_of = date(2026, 7, 27)
    whole = M.compute(frame, as_of)
    pre_cut = M.compute(M.truncate(frame, as_of), as_of)
    assert whole == pre_cut


def test_an_as_of_before_the_series_starts_yields_data_missing():
    frame = read_fixture(SAP_FIXTURE)
    metrics = M.compute(frame, date(2020, 1, 1))
    assert metrics.last_close is None
    assert metrics.high_52w is None
    assert metrics.drawdown is None


# --- a settled close is not a live print (REVIEW-4 report A 4.2) ----------


def test_settled_through_demotes_todays_bar_during_the_new_york_session():
    """The DECK hand run: 2026-08-25 17:13 CEST = 11:13 New York."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    hand = datetime(2026, 8, 25, 17, 13, tzinfo=ZoneInfo("Europe/Stockholm"))
    assert M.settled_through(hand) == date(2026, 8, 24)


def test_settled_through_accepts_todays_bar_after_the_new_york_close():
    """The scheduled run: deploy/vss.timer fires 22:30 Stockholm = 16:30 NY."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    cron = datetime(2026, 8, 25, 22, 30, tzinfo=ZoneInfo("Europe/Stockholm"))
    assert M.settled_through(cron) == date(2026, 8, 25)


def test_the_live_bar_is_dropped_and_the_settled_close_is_read():
    """88.55 was the live print; 88.74 the settled close of the day before it.

    The frame carries both; a run made during the session must read the
    older one and SAY that it saw the newer.
    """
    df = frame([88.10, 88.74, 88.55], end=date(2026, 8, 25))
    live = M.compute(df, date(2026, 8, 25), date(2026, 8, 24))
    assert live.last_close == pytest.approx(88.74)
    assert live.last_close_date == date(2026, 8, 24)
    assert live.live_bar_date == date(2026, 8, 25)
    assert live.last_close_settled is True


def test_the_same_frame_after_the_close_reads_the_settled_bar_for_today():
    df = frame([88.10, 88.74, 88.55], end=date(2026, 8, 25))
    settled = M.compute(df, date(2026, 8, 25), date(2026, 8, 25))
    assert settled.last_close == pytest.approx(88.55)
    assert settled.last_close_date == date(2026, 8, 25)
    assert settled.live_bar_date is None
    assert settled.last_close_settled is True


def test_no_cutoff_declared_is_DATA_MISSING_not_a_claim_that_it_settled():
    df = frame([88.10, 88.74, 88.55], end=date(2026, 8, 25))
    unknown = M.compute(df, date(2026, 8, 25))
    assert unknown.last_close == pytest.approx(88.55)
    assert unknown.last_close_settled is None
    assert unknown.live_bar_date is None


def test_the_drawdown_and_the_52w_high_are_struck_on_the_settled_close_too():
    """One price, one date: the live bar must not reach any metric."""
    df = frame([100.0] * 398 + [90.0, 80.0], end=date(2026, 8, 25))
    live = M.compute(df, date(2026, 8, 25), date(2026, 8, 24))
    assert live.last_close == pytest.approx(90.0)
    assert live.high_52w == pytest.approx(100.0)
    assert live.drawdown == pytest.approx(0.10)


# --- 52 weeks of coverage, or DATA MISSING (REVIEW-4 report B 7.2) --------


def test_a_series_short_of_52_weeks_gives_no_52_week_high_at_all():
    """NEVER A LOWER NUMBER. 120 rows of DECK's own cache read a 22.4%
    drawdown against the 28.4% its full 501 rows produce, and nothing said
    so: `high_52w` is the maximum of the rows PRESENT."""
    short = M.compute(frame([100.0] * 120 + [80.0], end=date(2026, 8, 20)),
                      date(2026, 8, 20))
    assert short.last_close == pytest.approx(80.0)     # the price is fine
    assert short.high_52w is None                       # the window is not
    assert short.drawdown is None
    assert short.covers_52_weeks is False
    assert short.first_bar_date == date(2026, 4, 22)


def test_the_bar_is_52_weeks_plus_five_trading_days():
    """The five days are the margin that makes "52 weeks" mean a window
    that is COVERED rather than one exactly reached."""
    as_of = date(2026, 8, 20)                          # a Thursday
    assert M.coverage_start(as_of) == date(2025, 8, 14)
    assert as_of - M.coverage_start(as_of) == timedelta(days=371)
    assert M.covers_52_weeks(date(2025, 8, 14), as_of) is True
    assert M.covers_52_weeks(date(2025, 8, 15), as_of) is False
    assert M.covers_52_weeks(None, as_of) is False


def test_a_bare_year_of_trading_rows_does_not_clear_the_bar():
    """About 250 trading rows span a bare 52 weeks and may be missing the
    first days of the window they claim to measure."""
    as_of = date(2026, 8, 21)
    assert M.covers_52_weeks(date(2025, 8, 22), as_of) is False


def test_a_two_year_cache_clears_it_and_that_is_what_the_run_fetches():
    """The fetched window clears the 52-week bar with room to spare.

    `fetch.DEFAULT_PERIOD` was "2y" until 2026-08-27; E52 raised it to "5y"
    because the listing-age floor is measured from the stored series and a
    two-year fetch would reject the whole universe on its own fetch
    parameter. Two years still clears the 52-week bar, which is what this
    test has always been about, and five years clears it by more.
    """
    from vss.fetch import DEFAULT_PERIOD
    # "6y", not "5y": the vendor measures its window from TODAY, so a 5y
    # fetch is short of five years back from any earlier --asof. Measured
    # 2026-08-27, that one day rejected all 1,328 names at E52's floor.
    assert DEFAULT_PERIOD == "6y"
    assert M.covers_52_weeks(date(2024, 8, 21), date(2026, 8, 21)) is True
    assert M.covers_52_weeks(date(2021, 8, 21), date(2026, 8, 21)) is True


# --- the date of the 52-week high (E11/E12, build item 5) -------------------


def test_the_high_52w_date_is_the_session_the_high_was_set():
    closes = [50.0, 120.0, 80.0, 90.0]
    f = frame(closes, end=date(2026, 8, 20))
    assert M.high_52w_date(f["Close"], date(2026, 8, 20)) == date(2026, 8, 18)


def test_a_tied_high_takes_the_latest_session():
    """The later print is the one whose ageing-out ends the drawdown, which
    is the question E11 asked and nothing could answer."""
    closes = [120.0, 80.0, 120.0, 90.0]
    f = frame(closes, end=date(2026, 8, 20))
    assert M.high_52w_date(f["Close"], date(2026, 8, 20)) == date(2026, 8, 19)


def test_the_high_date_respects_the_window_and_travels_with_compute():
    closes = [200.0] + [100.0] * 379
    f = frame(closes, end=date(2026, 8, 20))
    # The 200 printed 379 days before as_of, outside the 365-day window;
    # the series still clears the 52-weeks-plus-five-days coverage bar.
    assert M.high_52w_date(f["Close"], date(2026, 8, 20)) != f.index[0].date()
    computed = M.compute(f, date(2026, 8, 20))
    assert computed.high_52w == pytest.approx(100.0)
    assert computed.high_52w_date == date(2026, 8, 20)
    assert M.compute(pd.DataFrame(), date(2026, 8, 20)).high_52w_date is None


# --- the 52-week LOW and the distance above it (FRAMEWORK-EDITS E63) --------


def test_the_low_52w_is_the_lowest_close_in_the_window_and_its_latest_session():
    closes = [50.0, 30.0, 80.0, 30.0, 90.0]
    f = frame(closes, end=date(2026, 8, 20))
    assert M.low_52w(f["Close"], date(2026, 8, 20)) == pytest.approx(30.0)
    # A tied low takes the LATEST session: it is the one after which any
    # recovery is counted, the same reason the high takes its latest print.
    assert M.low_52w_date(f["Close"], date(2026, 8, 20)) == date(2026, 8, 19)


def test_the_low_respects_the_365_day_window():
    closes = [10.0] + [100.0] * 379          # the 10 printed 379 days before as_of
    f = frame(closes, end=date(2026, 8, 20))
    assert M.low_52w(f["Close"], date(2026, 8, 20)) == pytest.approx(100.0)
    assert M.low_52w_date(f["Close"], date(2026, 8, 20)) == date(2026, 8, 20)
    assert M.low_52w(pd.Series(dtype=float), date(2026, 8, 20)) is None
    assert M.low_52w_date(pd.Series(dtype=float), date(2026, 8, 20)) is None


def test_pct_above_low_is_the_distance_above_the_low():
    """CTSH 2026-08-27: close 63.78 against the 2026-06-30 low of 38.73."""
    assert M.pct_above_low(63.78, 38.73) == pytest.approx(0.6467, abs=1e-4)
    assert M.pct_above_low(38.73, 38.73) == 0.0
    assert M.pct_above_low(None, 38.73) is None
    assert M.pct_above_low(63.78, None) is None
    assert M.pct_above_low(63.78, 0.0) is None


def test_compute_carries_the_low_its_date_and_the_distance_beside_the_drawdown():
    closes = [100.0] * 390 + [40.0] + [60.0] * 9        # 400 rows clears the bar
    m = M.compute(frame(closes, end=date(2026, 8, 20)), date(2026, 8, 20))
    assert m.covers_52_weeks is True
    assert m.drawdown == pytest.approx(0.40)
    assert m.low_52w == pytest.approx(40.0)
    assert m.low_52w_date == date(2026, 8, 11)
    assert m.pct_above_52w_low == pytest.approx(0.50)


def test_the_low_is_struck_on_the_settled_close_too():
    """One price, one date: a live print below every settled close must
    not become the low."""
    df = frame([100.0] * 398 + [90.0, 70.0], end=date(2026, 8, 25))
    live = M.compute(df, date(2026, 8, 25), date(2026, 8, 24))
    assert live.last_close == pytest.approx(90.0)
    assert live.low_52w == pytest.approx(90.0)
    assert live.low_52w_date == date(2026, 8, 24)
    assert live.pct_above_52w_low == pytest.approx(0.0)


def test_a_series_short_of_52_weeks_gives_no_52_week_low_either_never_a_partial_reading():
    """The SAME bar, both ends of the window, together. A low struck off a
    shorter window is a HIGHER low and a SMALLER distance -- the wrong
    direction, exactly as the high's bar exists to refuse."""
    as_of = date(2026, 8, 20)
    short = M.compute(frame([100.0] * 120 + [80.0], end=as_of), as_of)
    assert short.last_close == pytest.approx(80.0)     # the price is fine
    assert short.covers_52_weeks is False
    assert short.low_52w is None
    assert short.low_52w_date is None
    assert short.pct_above_52w_low is None

    # And the boundary is the high's boundary: a first bar ON coverage_start
    # clears it and both ends are read; one day later, neither is.
    exact = (as_of - M.coverage_start(as_of)).days + 1
    on = M.compute(frame([100.0] * (exact - 1) + [80.0], end=as_of), as_of)
    assert on.first_bar_date == M.coverage_start(as_of)
    assert on.covers_52_weeks is True
    assert on.high_52w == pytest.approx(100.0)
    assert on.low_52w == pytest.approx(80.0)
    assert on.low_52w_date == as_of
    assert on.pct_above_52w_low == pytest.approx(0.0)

    off = M.compute(frame([100.0] * (exact - 2) + [80.0], end=as_of), as_of)
    assert off.first_bar_date == M.coverage_start(as_of) + timedelta(days=1)
    assert off.covers_52_weeks is False
    assert (off.high_52w, off.high_52w_date, off.drawdown) == (None, None, None)
    assert (off.low_52w, off.low_52w_date, off.pct_above_52w_low) == (None, None, None)
    assert off.last_close == pytest.approx(80.0)
