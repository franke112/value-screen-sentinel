"""tools/fetch_mfn.py: a report's kind and period come from MFN's tags and the title."""
from __future__ import annotations

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "fetch_mfn", Path(__file__).resolve().parents[1] / "tools" / "fetch_mfn.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

INT = [":regulatory", "sub:report", "sub:report:interim"]
ANN = [":regulatory", "sub:report", "sub:report:annual"]


def test_a_swedish_interim_is_not_an_annual_report():
    # "delårsrapport" contains "årsrapport": the trap that misnamed 56 files
    assert M.kind_of(INT, "ZINZINO AB (PUBL.): DELÅRSRAPPORT Q1 2026") == "interim-report-q1-and-q3"


def test_the_kinds():
    assert M.kind_of(INT, "INTERIM REPORT Q2 2026") == "half-year-financial-report"
    assert M.kind_of(ANN + ["sub:report:interim", "sub:report:interim:q4"],
                     "YEAR-END REPORT 2025") == "financial-statement-release"
    assert M.kind_of(ANN, "Year-End Report 1st January - 31st December 2015") == "financial-statement-release"
    assert M.kind_of(INT + ["sub:report:interim:q4"], "ANNUAL REPORT ENGLISH 2022") == "annual-financial-report"
    assert M.kind_of([":regulatory"], "Annual Report 2021 Zinzino AB (PUBL)") == "annual-financial-report"


def test_the_periods():
    assert M.period_of("INTERIM REPORT Q2 2026", "half-year-financial-report") == "2026-Q2"
    assert M.period_of("Interim Report for the third quarter of 2025", "interim-report-q1-and-q3") == "2025-Q3"
    assert M.period_of("Delårsrapport tredje kvartalet 2025", "interim-report-q1-and-q3") == "2025-Q3"
    assert M.period_of("ANNUAL REPORT 2024", "annual-financial-report") == "2024-FY"
    assert M.period_of("A strong quarter", "interim-report-q1-and-q3") == "UNKNOWN"


def test_local_symbol():
    assert M.local_symbol("ZZ-B.ST") == "ZZ B" and M.local_symbol("EVO.ST") == "EVO"
