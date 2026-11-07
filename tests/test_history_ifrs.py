"""HANDOFF A5: an ifrs-full history from ESEF facts in companyfacts shape.
Synthetic facts only."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from vss import history as H


def _e(end, val, start=None):
    e = {"end": end, "val": val, "form": "ESEF", "filed": "2026-03-20", "accn": "esef:x:r.xhtml"}
    if start:
        e["start"] = start
    return e


def _dur(vals, unit="SEK"):
    return {"units": {unit: [_e(f"{y}-12-31", v, f"{y}-01-01") for y, v in vals.items()]}}


def _inst(vals, unit="SEK"):
    return {"units": {unit: [_e(f"{y}-12-31", v) for y, v in vals.items()]}}


def facts(**extra):
    f = {
        "Revenue": _dur({2023: 900e6, 2024: 1000e6, 2025: 1100e6}),
        "ProfitLossFromOperatingActivities": _dur({2023: 90e6, 2024: 100e6, 2025: 120e6}),
        "CashFlowsFromUsedInOperatingActivities": _dur({2023: 80e6, 2024: 95e6, 2025: 110e6}),
        "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities": _dur({2024: 20e6, 2025: 25e6}),
        "PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities": _dur({2023: 3e6, 2024: 5e6, 2025: 6e6}),
        "CashAndCashEquivalents": _inst({2023: 50e6, 2024: 60e6, 2025: 70e6}),
        "LongtermBorrowings": _inst({2024: 200e6, 2025: 180e6}),
        "CurrentPortionOfLongtermBorrowings": _inst({2025: 40e6}),
        "AdjustedWeightedAverageShares": _dur({2023: 10e6, 2024: 10e6, 2025: 10e6}, unit="shares"),
    }
    f.update(extra)
    return {"facts": {"ifrs-full": f}}


def _rows(raw, field):
    return [r for r in raw["rows"] if r["field"] == field]


def test_the_ifrs_rows_in_the_facts_own_currency():
    raw = H.from_companyfacts("EXM.ST", facts(), taxonomy="ifrs-full",
                              source={"kind": "esef-ixbrl"})
    assert raw["currency"] == "SEK" and raw["sources"]["xbrl"]["kind"] == "esef-ixbrl"
    h = H.parse(raw, path="t")
    assert h.series("revenue") == {2023: 900e6, 2024: 1000e6, 2025: 1100e6}
    # capex: PP&E + intangibles, two rows summed -- and NOT 2023, where only
    # the intangible line is tagged
    assert h.series("capex") == {2024: 25e6, 2025: 31e6}
    assert H.owner_earnings(h) == {2024: 70e6, 2025: 79e6}
    assert h.series("shares")[2025] == 10e6


def test_net_debt_is_missing_rather_than_nil():
    h = H.parse(H.from_companyfacts("EXM.ST", facts(), taxonomy="ifrs-full",
                                    source={"kind": "esef-ixbrl"}), path="t")
    nd = h.series("net_debt")
    assert nd == {2024: 140e6}          # 200 - 60
    # 2023: neither leg tagged -> DATA MISSING, not -50 (no debt)
    # 2025: CurrentPortionOfLongtermBorrowings is outside the legs -> missing


def test_the_us_gaap_path_still_reads_usd_10k_only():
    us = {"facts": {"us-gaap": {"NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [
        {"end": "2025-12-31", "start": "2025-01-01", "val": 5.0, "form": "10-K", "fp": "FY", "filed": "2026-02-01"},
        {"end": "2024-12-31", "start": "2024-01-01", "val": 4.0, "form": "ESEF", "filed": "2026-02-01"}]}}}}}
    raw = H.from_companyfacts("X", us)
    assert raw["currency"] == "USD"
    assert [r["years"] for r in _rows(raw, "operating_cash_flow")] == [[2025]]   # the ESEF entry is not a 10-K
    assert H.parse(raw, path="t").span == (2025, 2025)


class _Pkg:
    def __init__(self, ext):
        self.extensions = ext
        self.path = Path("sources/EXM.ST_x.zip")
        self.sha256 = "0" * 64
        self.filed = "2026-03-20"
        self.lei = "L"


def test_extension_concepts_withhold_capex_and_net_debt(monkeypatch):
    from vss import esef
    pk = _Pkg({"exm:InvestmentsInEquipment": 2, "exm:ConvertibleLoan": 1})
    monkeypatch.setattr(esef, "packages_for", lambda t: ([pk], []))
    monkeypatch.setattr(esef, "merged_facts", lambda p: facts())
    raw, refused = H.esef_raw("EXM.ST")
    assert not _rows(raw, "capex") and not _rows(raw, "net_debt")
    src = raw["sources"]["xbrl"]
    assert "exm:InvestmentsInEquipment" in src["capex_withheld"]
    assert "exm:ConvertibleLoan" in src["net_debt_withheld"]
    assert "owner_earnings_before_window" not in raw


def test_a_merge_keeps_the_old_files_unit_on_its_rows(monkeypatch, tmp_path):
    from vss import esef
    (tmp_path / "EXM.ST.yaml").write_text(yaml.safe_dump({
        "ticker": "EXM.ST", "currency": "SEK", "money_unit": "millions",
        "sources": {"ar": {"kind": "pdf", "file": "sources/x.pdf"}},
        "rows": [{"field": "revenue", "source": "ar", "years": [2020, 2021],
                  "values": [800, 850], "quote": "Net sales 800 850"}]}))
    monkeypatch.setattr(esef, "packages_for", lambda t: ([_Pkg({})], []))
    monkeypatch.setattr(esef, "merged_facts", lambda p: facts())
    code, _ = H.run_history(ticker="EXM.ST", esef=True, write=True, directory=tmp_path)
    assert code == 0
    h = H.load("EXM.ST", directory=tmp_path)
    assert h.series("revenue")[2020] == 800e6          # still millions, not 800 kronor
    assert h.series("revenue")[2025] == 1100e6
    assert h.money_unit == "whole"


def test_the_acquisition_element_is_the_manual_maps():
    from vss import xbrl
    assert H.IFRS_TAGS["acquisitions_paid"] == xbrl.IFRS_E140_ACQUISITION_TAGS
    assert set(H.IFRS_DEBT_CURRENT) == {f for spec in xbrl.IFRS_ANNUAL_FIELDS
                                        if spec.field == "financial_liabilities_current"
                                        for f in spec.tags}
