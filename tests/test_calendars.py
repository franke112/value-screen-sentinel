"""The exchange calendar behind the staleness gate (E47 / C3, build item 3)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from vss import rules as R
from vss.calendars import CALENDARS_PATH, load_market_calendars
from vss.filters import run_filter1
from vss.universe import (
    Instrument,
    UniverseError,
    load_type_rules,
    load_universe,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def calendars():
    return load_market_calendars(ROOT / CALENDARS_PATH)


def test_christmas_in_stockholm_counts_the_sessions_stockholm_held(calendars):
    """SCREENER-REVIEW-3 Part 10: 12-24, 12-25 and 12-26 are closed weekdays
    on seven of eleven markets, and the naive count blocked a whole market
    after ONE real session. Stockholm 2026: the 24th and 25th are closed
    weekdays, the 28th is the next session."""
    closed = calendars.closed_weekdays("Stockholm", date(2026, 12, 24), date(2026, 12, 28))
    assert closed == frozenset({date(2026, 12, 25)})
    closed = calendars.closed_weekdays("Stockholm", date(2026, 12, 23), date(2026, 12, 28))
    assert closed == frozenset({date(2026, 12, 24), date(2026, 12, 25)})
    # From the 23rd's close to the 28th: ONE session held, three weekdays.
    assert R.trading_days_between(date(2026, 12, 23), date(2026, 12, 28)) == 3
    assert R.trading_days_between(date(2026, 12, 23), date(2026, 12, 28),
                                  holidays=closed) == 1
    # From the 24th (no close that day, but the owner's phrasing) to the 28th.
    assert R.trading_days_between(date(2026, 12, 24), date(2026, 12, 28),
                                  holidays=calendars.closed_weekdays(
                                      "Stockholm", date(2026, 12, 24), date(2026, 12, 28))) == 1


def test_the_gate_stays_at_three_sessions_on_the_calendar(calendars):
    """E47: the constant is unchanged at 3. What changes is that a closed
    weekday no longer counts against the feed. A close of 2026-12-23 read on
    the 30th is three Stockholm sessions old (28, 29, 30) and NOT stale;
    naive counting makes it five and blocks."""
    last, as_of = date(2026, 12, 23), date(2026, 12, 30)
    closed = calendars.closed_weekdays("Stockholm", last, as_of)
    assert R.MAX_CLOSE_AGE_TRADING_DAYS == 3
    assert R.trading_days_between(last, as_of, holidays=closed) == 3
    assert R.stale_close_blocker(last, as_of, holidays=closed) is None
    naive = R.stale_close_blocker(last, as_of)
    assert naive is not None and "5 trading days" in naive.reason
    # And the gate did not become permissive: the 31st is closed too, so a
    # read on 2027-01-04 is four sessions (28, 29, 30, 01-04) and blocks.
    closed = calendars.closed_weekdays("Stockholm", last, date(2027, 1, 4))
    blocked = R.stale_close_blocker(last, date(2027, 1, 4), holidays=closed)
    assert blocked is not None and "4 trading days" in blocked.reason


def test_us_labor_day_is_a_closed_weekday_on_new_york_only(calendars):
    day = date(2026, 9, 7)
    assert day in calendars.closed_weekdays("US", date(2026, 9, 4), date(2026, 9, 8))
    assert day not in calendars.closed_weekdays("Stockholm", date(2026, 9, 4), date(2026, 9, 8))


def test_an_ordinary_week_has_no_closed_weekdays(calendars):
    for market in ("US", "Stockholm", "London", "Xetra"):
        assert calendars.closed_weekdays(market, date(2026, 8, 17), date(2026, 8, 21)) == frozenset()


def test_an_unmapped_market_answers_none_never_an_empty_set(calendars):
    """DATA MISSING about the calendar is a third state: None, so the caller
    can name the fallback rather than pass an empty set and call it counted."""
    assert calendars.closed_weekdays("Eurex Deutschland", date(2026, 12, 23),
                                     date(2026, 12, 28)) is None
    assert calendars.closed_weekdays(None, date(2026, 12, 23), date(2026, 12, 28)) is None


def test_every_market_in_the_committed_universe_is_mapped(calendars):
    """Every instrument the loader keeps must count on its own exchange's
    calendar. A row excluded on instrument type (the STOXX fund's cash and
    derivative lines, market '-' or 'Eurex Deutschland') never reaches the
    gate and needs no mapping."""
    universe_dir = ROOT / "config" / "universe"
    load = load_universe(universe_dir, tiers=("A",),
                         type_rules=load_type_rules(universe_dir / "instrument_types.yaml"))
    markets = {i.marknad for i in load.instruments}
    unmapped = sorted(m for m in markets if calendars.mic(m) is None)
    assert unmapped == [], f"no exchange calendar for {unmapped}"


def test_a_missing_config_is_an_error(tmp_path: Path):
    with pytest.raises(UniverseError, match="no exchange calendar config"):
        load_market_calendars(tmp_path / "nope.yaml")


def test_a_malformed_config_is_an_error(tmp_path: Path):
    path = tmp_path / "cal.yaml"
    path.write_text("markets: [XSTO]\n", encoding="utf-8")
    with pytest.raises(UniverseError, match="mapping"):
        load_market_calendars(path)
    path.write_text("markets:\n  Stockholm:\n", encoding="utf-8")
    with pytest.raises(UniverseError, match="empty"):
        load_market_calendars(path)


# --- through filter 1 -------------------------------------------------------


def _instrument(ticker, market):
    return Instrument(ticker_yahoo=ticker, ticker_lokal=ticker.split(".")[0], isin=None,
                      namn=ticker, marknad=market, tier="A", listdatum=None,
                      valuta="SEK", instrumenttyp="Equity")


def _frame(last: date, days: int = 1600, tail: int = 140):
    """1600 business days is over six years -- past E52's five-year floor --
    and the step down sits in the last ``tail`` sessions so the peak stays
    inside the 365-day window `high_52w` reads."""
    import pandas as pd

    index = pd.bdate_range(end=last, periods=days)
    closes = [100.0] * (days - tail) + [75.0] * tail
    return pd.DataFrame({"Open": closes, "High": closes, "Low": closes,
                         "Close": closes, "Volume": [1000.0] * days}, index=index)


def test_filter_1_reads_the_calendar_of_the_universe_rows_market(calendars):
    """The Monday after Christmas 2026 in Stockholm: a close of the 23rd is
    one session old on the exchange calendar and passes; on the naive count
    it is three weekdays old, which passes too -- so the case that shows the
    difference is the 30th, five weekdays but three sessions."""
    stockholm = _instrument("X.ST", "Stockholm")
    frames = {"X.ST": _frame(date(2026, 12, 23))}
    as_of = date(2026, 12, 30)
    with_calendar = run_filter1([stockholm], frames, as_of,
                                holidays_for=calendars.closed_weekdays)
    assert [c.ticker for c in with_calendar.candidates] == ["X.ST"]
    assert with_calendar.naive_calendar == {}

    naive = run_filter1([stockholm], frames, as_of)
    assert naive.candidates == []
    assert naive.naive_calendar == {"Stockholm": 1}
    (rejected,) = naive.rejections
    assert "5 trading days" in rejected.reason


def test_an_unmapped_market_falls_back_to_the_naive_count_and_is_named(calendars):
    odd = _instrument("Y.XX", "Nowhere")
    result = run_filter1([odd], {"Y.XX": _frame(date(2026, 12, 23))}, date(2026, 12, 28),
                         holidays_for=calendars.closed_weekdays)
    assert result.naive_calendar == {"Nowhere": 1}
    assert [c.ticker for c in result.candidates] == ["Y.XX"]


def test_the_framework_texts_carry_e47_and_the_pointer():
    """Item 13: the three-way conflict Part 10.3 found is closed in the
    texts as well as the code -- FRAMEWORK-EDITS carries E47 and C3's
    DECIDED marker, and section 1.2 of the FRAMEWORK points at E47."""
    edits = (ROOT / "reference" / "FRAMEWORK-EDITS.md").read_text(encoding="utf-8")
    assert "### E47 — staleness is THREE trading days on the EXCHANGE CALENDAR" in edits
    c3 = edits[edits.index("### C3 —"):edits.index("### C4 —")]
    assert "DECIDED 2026-08-26" in c3
    framework = (ROOT / "reference" / "FRAMEWORK.md").read_text(encoding="utf-8")
    line = next(l for l in framework.splitlines() if l.startswith("- Prices, RSI, moving averages"))
    assert "E47" in line and "3 sessions" in line
    assert R.MAX_CLOSE_AGE_TRADING_DAYS == 3
