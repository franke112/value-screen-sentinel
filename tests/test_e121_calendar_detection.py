"""E121(e), amended by the owner 2026-09-20: compliance BY DETECTION.

A MISSING mapping over-states staleness, which is the safe direction. A
WRONG one under-states it, and no guarantee was available -- but the price
series already in hand settles it: a close printed on a day the derived
calendar calls closed proves the suffix is mapped to the wrong exchange.
"""
from datetime import date, datetime

import pandas as pd

from vss import rules as R
from vss.calendars import load_market_calendars
from vss.config import WatchlistEntry
from vss.fetch import FetchResult
from vss.runner import build_row


def _fetched(ticker: str, days: list[str], close: float = 100.0) -> FetchResult:
    idx = pd.DatetimeIndex([pd.Timestamp(d) for d in days])
    frame = pd.DataFrame({"Open": close, "High": close, "Low": close,
                          "Close": close, "Volume": 1_000}, index=idx)
    frame.index.name = "Date"
    return FetchResult(ticker, frame, "live", datetime(2026, 1, 8, 22, 30))


def _row(ticker, days, *, as_of=date(2026, 1, 8)):
    entry = WatchlistEntry(ticker=ticker, name="Ex", currency="SEK",
                           status="WATCH-GATED")
    return build_row(entry, _fetched(ticker, days), as_of,
                     calendars=load_market_calendars(), use_calendar=True)


def test_epiphany_is_a_session_on_no_stockholm_calendar_so_the_mapping_is_wrong():
    """2026-01-06 is Epiphany: Stockholm is shut, New York is open. A close
    printed for a `.ST` ticker on that day means the suffix is mapped to the
    wrong exchange."""
    row = _row("EXMPL.ST", ["2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08"])
    codes = [b.code for b in row.assessment.blockers]
    assert R.CALENDAR_MISMATCH in codes
    reason = next(b.reason for b in row.assessment.blockers
                  if b.code == R.CALENDAR_MISMATCH)
    assert "2026-01-06" in reason and "'ST'" in reason and "Stockholm" in reason
    assert "UNDER-state" in reason
    assert not row.assessment.verdicts          # blocked names collect none


def test_a_series_that_respects_the_calendar_raises_nothing():
    row = _row("EXMPL.ST", ["2026-01-05", "2026-01-07", "2026-01-08"])
    assert R.CALENDAR_MISMATCH not in [b.code for b in row.assessment.blockers]


def test_an_unmapped_suffix_is_never_accused_of_a_mismatch():
    """It has no calendar to contradict; it is counted Monday to Friday and
    says so (E121 b)."""
    row = _row("EXMPL.ZZ", ["2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08"])
    assert R.CALENDAR_MISMATCH not in [b.code for b in row.assessment.blockers]
