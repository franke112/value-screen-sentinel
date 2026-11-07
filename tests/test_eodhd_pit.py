"""tools/eodhd_pit.py: when an EODHD period became known. Synthetic rows."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import eodhd_pit as E  # noqa: E402


def test_known_date_rules():
    # a real US filing date wins
    assert E.known("2026-06-30", "2026-08-05", "2026-07-25") == ("2026-08-05", "filing_date")
    # Nordic: filing_date == period end is no date; the report date + one weekday
    assert E.known("2026-09-30", "2026-09-30", "2026-10-22") == ("2026-10-23", "report_date+1")
    assert E.known("2026-09-30", "2026-09-30", "2026-10-23") == ("2026-10-26", "report_date+1")  # Fri -> Mon
    # a report date before the period end, or absurdly late, is not believed
    assert E.known("2026-09-30", None, "2026-09-01") == (None, "unknown")
    assert E.known("2026-09-30", None, "2027-09-01") == (None, "unknown")
    assert E.known("2026-09-30", None, None) == (None, "unknown")


def test_rows_for_takes_dates_from_the_earnings_history():
    d = {"Earnings": {"History": {"2026-09-30": {"date": "2026-09-30", "reportDate": "2026-10-22",
                                                 "epsActual": 5.42, "epsEstimate": 5.55,
                                                 "surprisePercent": -2.34}}},
         "Financials": {"Income_Statement": {"currency_symbol": "SEK", "quarterly": {
             "2026-09-30": {"date": "2026-09-30", "filing_date": "2026-09-30",
                            "totalRevenue": "119525000000.00", "ebit": None}}}}}
    per, fig, rep = E.rows_for("VOLV-B.ST", d)
    assert per == [("VOLV-B.ST", "quarterly", "2026-09-30", "2026-10-23", "report_date+1", "SEK")]
    assert fig == [("VOLV-B.ST", "quarterly", "2026-09-30", "Income_Statement", "totalRevenue", 119525000000.0)]
    assert rep[0][2:] == ("2026-10-22", 5.42, 5.55, -2.34)
