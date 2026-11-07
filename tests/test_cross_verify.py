"""E151: a machine-read figure is VERIFIED only when a second, independent
machine reading prints the same digits. No model, no real report."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cross_verify as CV  # noqa: E402

STORE = """ticker: EXM.ST
name: Exempel
reporting_currency: EUR
money_unit: whole
share_unit: whole
origin: esef-ixbrl

annual:
  - fiscal_year: 2025
    period_end: 2025-12-31
    document: "ESEF"
    url: "sources/EXM.ST_x.zip"
    figures:
      net_income:
        value: 1062096000
        source: "esef-ixbrl: sources/EXM.ST_x.zip"
        page: "ESEF abcd1234 ifrs-full:ProfitLoss ctx c-1 2025-01-01..2025-12-31, displayed '1 062 096', decimals -3"
        status: UNVERIFIED
      operating_cash_flow:
        value: 1255217000
        source: "esef-ixbrl: sources/EXM.ST_x.zip"
        page: "ESEF abcd1234 ifrs-full:CashFlows ctx c-1 2025-01-01..2025-12-31, displayed '1 255 217', decimals -3"
        status: UNVERIFIED
      capex_ppe:
        value: -64599000
        source: "esef-ixbrl: sources/EXM.ST_x.zip"
        page: "ESEF abcd1234 ifrs-full:PPE ctx c-1 2025-01-01..2025-12-31, displayed '64 599', decimals -3"
        status: UNVERIFIED
"""


def test_agreeing_digits_verify_and_a_disagreement_does_not(tmp_path, monkeypatch):
    path = tmp_path / "EXM.ST.yaml"
    path.write_text(STORE)
    monkeypatch.setattr(CV, "annual_pdf", lambda t, y: Path(f"sources/EXM.ST_{y}-FY_ar.pdf"))
    monkeypatch.setattr(CV, "CACHE", tmp_path / "cache")
    kept = {"net_income": {"value": "1,062,096", "row": "Profit for the year 1,062,096 1,244,015",
                           "column": "2025", "page": 85},
            "operating_cash_flow": {"value": 1255218, "row": "Cash flow 1,255,218", "column": "2025", "page": 88},
            "capex_ppe": {"value": -64599, "row": "Acquisition of PPE –64,599", "column": "2025", "page": 88}}

    class R:
        record = {"model": "m", "responses_sha256": ["a", "b"]}

        class gated:
            figures = kept
            dropped = {}

    results = CV.check_store(path, runner=lambda *a, **k: R)
    got = {r["field"]: r for r in results}
    assert got["net_income"]["ok"] and got["capex_ppe"]["ok"]
    assert not got["operating_cash_flow"]["ok"] and "DISAGREE" in got["operating_cash_flow"]["why"]
    assert CV.apply(path, results) == 2
    doc = yaml.safe_load(path.read_text())
    figs = doc["annual"][0]["figures"]
    assert figs["net_income"]["status"] == "VERIFIED" and figs["net_income"]["verified_kind"] == "two_source"
    assert "E151 second reading" in figs["net_income"]["page"]
    assert figs["net_income"]["value"] == 1062096000                     # the value is never changed
    assert figs["operating_cash_flow"]["status"] == "UNVERIFIED"


def test_the_rules_of_comparison():
    d = CV.printed
    assert d("1 062 096") == d("1,062,096") == d("–1,062,096")
    assert d("5,23") == d("5.23")
    ok, why = CV.compare("capex_ppe", -1.0, d("64 599"), {"value": 64599, "row": "x", "page": 1})
    assert not ok and "positive" in why
    assert not CV.compare("net_income", 0, d("0"), {"value": 0, "row": "x", "page": 1})[0]
    assert not CV.compare("net_income", 5.0, d("5"), None)[0]
