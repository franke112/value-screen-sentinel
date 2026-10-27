"""E140 / E140.1 in the engine: the normalised flow, the repeat buyer, the
after-tax interest, the events ledger and its cut, the roll-forward and
what it carries, and the tagged working-capital composite.

Ruled by the owner 2026-10-27 (FRAMEWORK-EDITS E140, E140.1).
"""
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
import yaml

from vss import events as EV
from vss import manual as M
from vss import runrecord as R
from vss import valuation as V
from vss import xbrl as X
from vss.ixbrl import facts_from_inline, merge_facts


def year(label, ocf, wc, capex, sbc, acq, lease=None):
    return V.NormalisedYear(label, ocf, wc, capex, sbc, acq, lease_cash=lease)


# --- the normalised flow (E140(1)-(2), E140.1(1)) -------------------------

def test_the_flow_is_the_three_year_mean_ex_working_capital():
    years = [year("FY23", 300.0, 120.0, -80.0, 20.0, 0.0),
             year("FY24", 320.0, 140.0, -70.0, 25.0, 0.0),
             year("FY25", 330.0, 50.0, -60.0, 25.0, 0.0)]
    flow = V.normalised_free_cash_flow_zero(
        years=years, interest_in_ocf=True, net_interest_paid=40.0,
        tax_rate=0.25, nci_dividends_paid=-2.0)
    assert flow.years == (80.0, 85.0, 195.0)
    assert flow.mean == pytest.approx(120.0)
    assert flow.interest_added_back == pytest.approx(30.0)     # after tax
    assert not flow.repeat_buyer
    assert flow.fcf0 == pytest.approx(120.0 + 30.0 - 2.0)


def test_a_repeat_buyer_deducts_the_mean_of_its_spend_and_a_receipt_is_zero():
    """E140.1(1): two years of three is a pattern; CPRT's FY2023 receipt
    (cash acquired above cash paid) counts as zero, never as income."""
    years = [year("a", 100.0, 0.0, 0.0, 0.0, 17.0),     # a receipt
             year("b", 100.0, 0.0, 0.0, 0.0, -30.0),
             year("c", 100.0, 0.0, 0.0, 0.0, -60.0)]
    flow = V.normalised_free_cash_flow_zero(
        years=years, interest_in_ocf=False, net_interest_paid=None,
        tax_rate=None, nci_dividends_paid=0.0)
    assert flow.repeat_buyer
    assert flow.acquisitions_mean == pytest.approx(30.0)
    assert flow.fcf0 == pytest.approx(70.0)


def test_one_deal_in_three_years_is_not_a_pattern():
    """ULTA paid for Space NK in one year of three: no deduction."""
    years = [year("a", 100.0, 0.0, 0.0, 0.0, 0.0),
             year("b", 100.0, 0.0, 0.0, 0.0, 0.0),
             year("c", 100.0, 0.0, 0.0, 0.0, -387.0)]
    flow = V.normalised_free_cash_flow_zero(
        years=years, interest_in_ocf=False, net_interest_paid=None,
        tax_rate=None, nci_dividends_paid=0.0)
    assert not flow.repeat_buyer and flow.fcf0 == pytest.approx(100.0)


def test_an_ifrs_year_deducts_its_lease_cash():
    years = [year(str(i), 100.0, 10.0, -20.0, 5.0, 0.0, lease=15.0) for i in range(3)]
    flow = V.normalised_free_cash_flow_zero(
        years=years, interest_in_ocf=False, net_interest_paid=None,
        tax_rate=None, nci_dividends_paid=0.0)
    assert flow.fcf0 == pytest.approx(100 - 10 - 20 - 5 - 15)


@pytest.mark.parametrize("years, message", [
    ([year("a", 1.0, 0.0, 0.0, 0.0, 0.0)] * 2, "mean of 3 fiscal years"),
    ([year("a", 1.0, None, 0.0, 0.0, 0.0)] * 3, "working capital change"),
    ([year("a", 1.0, 0.0, 0.0, 0.0, None)] * 3, "NAMED ZERO"),
])
def test_an_absent_leg_or_year_refuses(years, message):
    with pytest.raises(V.ValuationError) as exc:
        V.normalised_free_cash_flow_zero(
            years=years, interest_in_ocf=False, net_interest_paid=None,
            tax_rate=None, nci_dividends_paid=0.0)
    assert message in str(exc.value)


def test_interest_in_ocf_with_no_country_rate_refuses():
    with pytest.raises(V.ValuationError) as exc:
        V.normalised_free_cash_flow_zero(
            years=[year("a", 1.0, 0.0, 0.0, 0.0, 0.0)] * 3, interest_in_ocf=True,
            net_interest_paid=5.0, tax_rate=None, nci_dividends_paid=0.0)
    assert "statutory tax rate is DATA MISSING" in str(exc.value)


def test_the_country_comes_off_the_listing():
    assert R.tax_country("CENTA") == "US"
    assert R.tax_country("LIAB.ST") == "SE" and R.tax_country("MC.PA") == "FR"
    assert R.tax_country("UMG.AS") is None          # not in E140(2)'s table


# --- the ledger and its cut (E140(3)-(4), E140.1(3)) ----------------------

def write_ledger(directory: Path, ticker: str, **over) -> Path:
    raw = {"ticker": ticker, "dated": "2026-10-27", "money_unit": "whole",
           "searched": ["press releases", "every filing since the basis", "news"],
           "deals": [
               {"name": "Old", "status": "closed", "closed": "2026-04-01",
                "low": 10.0, "high": 10.0, "source": "10-Q"},
               {"name": "New", "status": "closed", "closed": "2026-09-30",
                "low": 90.0, "high": 260.0, "source": "release"},
               {"name": "Pending", "status": "pending", "closed": None,
                "low": 580.0, "high": 580.0, "source": "8-K"}],
           "none_found": False}
    raw.update(over)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{ticker}.yaml"
    path.write_text(yaml.safe_dump(raw))
    return path


def test_a_deal_closed_on_or_before_the_balance_sheet_is_not_added_again(tmp_path):
    write_ledger(tmp_path, "TST")
    ledger = EV.load_ledger("TST", directory=tmp_path)
    assert [d.name for d in ledger.in_bridge(date(2026, 6, 27))] == ["New", "Pending"]
    assert [d.name for d in ledger.in_bridge(date(2026, 3, 31))] == ["Old", "New", "Pending"]


@pytest.mark.parametrize("over, message", [
    ({"dated": None}, "`dated` is required"),
    ({"money_unit": "SEK m"}, "money_unit must be one of"),
    ({"searched": []}, "`searched` is empty"),
    ({"deals": [], "none_found": False}, "states one or the other"),
    ({"deals": [{"name": "x", "status": "closed", "closed": None, "low": 1,
                 "high": 1, "source": "s"}]}, "status `closed` with no `closed` date"),
    ({"deals": [{"name": "x", "status": "pending", "closed": None, "low": 5,
                 "high": 1, "source": "s"}]}, "is above high"),
    ({"deals": [{"name": "x", "status": "pending", "low": 1, "high": 1,
                 "source": "s"}]}, "`closed` is required"),
])
def test_a_ledger_that_does_not_say_enough_refuses(tmp_path, over, message):
    write_ledger(tmp_path, "TST", **over)
    with pytest.raises(EV.EventsError) as exc:
        EV.load_ledger("TST", directory=tmp_path)
    assert message in str(exc.value)


def test_the_age_limit_is_a_week_and_a_ledger_from_the_future_refuses(tmp_path):
    write_ledger(tmp_path, "TST")
    ledger = EV.load_ledger("TST", directory=tmp_path)
    EV.check_fresh(ledger, date(2026, 11, 3))
    with pytest.raises(EV.EventsError):
        EV.check_fresh(ledger, date(2026, 11, 4))
    with pytest.raises(EV.EventsError):
        EV.check_fresh(ledger, date(2026, 10, 26))


def test_every_committed_ledger_loads():
    for path in sorted(EV.EVENTS_DIR.glob("*.yaml")):
        EV.load_ledger(path.stem)


# --- the block on the record ----------------------------------------------

def block(**over):
    raw = dict(years=tuple(year(f"FY{y}", 100.0, 0.0, 0.0, 0.0, 0.0)
                           for y in (2023, 2024, 2025)),
               tax_country="US", tax_rate=0.25, ledger="x", ledger_dated=date(2026, 10, 27),
               cut=date(2026, 6, 30),
               deals=(R.DealLeg("D", None, 10.0, 30.0),),
               rolled_from=date(2025, 12, 31), wc_since_year_end=-5.0)
    raw.update(over)
    return R.E140Block(**raw)


def test_added_debt_is_the_deals_at_one_end_plus_the_neutralised_wc():
    b = block()
    assert b.added_debt("high") == pytest.approx(25.0)
    assert b.added_debt("low") == pytest.approx(5.0)
    assert block(wc_since_year_end=None).added_debt() is None


def test_a_record_struck_after_E140_without_the_block_is_incomplete():
    from tests.test_runrecord import _fully_populated_record
    from dataclasses import replace
    rec = replace(_fully_populated_record(), e140=None,
                  run_ts=datetime(2026, 10, 28, tzinfo=timezone.utc))
    assert any("the E140 block" in g for g in rec.missing())
    old = replace(rec, run_ts=datetime(2026, 10, 20, tzinfo=timezone.utc))
    assert not any("the E140 block" in g for g in old.missing())


# --- the store: the roll-forward and what it carries -----------------------

def store(tmp_path, rf_figures, annual_figures=None):
    def fig(v, **k):
        return {"value": v, "source": "s", "page": "p.1", "status": "VERIFIED",
                "verified_kind": "tagged", **k}
    annual = {"cash_and_equivalents": fig(10), "financial_liabilities_current": fig(0, zero_basis="caption"),
              "financial_liabilities_noncurrent": fig(100),
              "lease_liabilities": fig(20), "operating_lease_liabilities": fig(18),
              "pension_deficit": fig(7), "asset_retirement_obligation": fig(0, zero_basis="caption"),
              "prepaid_delivery_obligation": fig(0, zero_basis="caption")}
    annual.update(annual_figures or {})
    doc = {"ticker": "TST", "name": "Test", "reporting_currency": "USD",
           "money_unit": "whole", "share_unit": "whole",
           "annual": [{"fiscal_year": 2025, "period_end": "2025-12-31",
                       "figures": annual}],
           "roll_forward": {"period_end": "2026-06-30", "from_year_end": "2025-12-31",
                            "figures": {k: (fig(v, zero_basis="caption") if v == 0 else fig(v))
                                        for k, v in rf_figures.items()}}}
    return M.parse_manual(doc, path=tmp_path / "TST.yaml")


def test_a_roll_forward_refuses_a_flow(tmp_path):
    with pytest.raises(M.ManualError) as exc:
        store(tmp_path, {"operating_cash_flow": 5})
    assert "is a flow" in str(exc.value)


def test_annual_legs_and_named_zeros_are_carried_and_a_nonzero_stream_is_not(tmp_path):
    parsed = store(tmp_path, {"cash_and_equivalents": 30, "financial_liabilities_current": 0,
                              "financial_liabilities_noncurrent": 90,
                              "lease_liabilities": 21, "operating_lease_liabilities": 19})
    basis = M.section5_basis(parsed)
    rf = M.roll_forward_basis(parsed, basis)
    assert rf.end == date(2026, 6, 30)
    got = {n: M.resolve_on_basis(parsed, rf, n).value for n in M.NET_DEBT_LEGS}
    assert got["pension_deficit"] == 7                    # carried, E41
    assert got["prepaid_delivery_obligation"] == 0        # a named zero, carried
    assert got["cash_and_equivalents"] == 30              # the interim's own
    assert "CARRIED from the fiscal year-end" in rf.periods[0].figures["pension_deficit"].page
    nonzero = store(tmp_path, {"cash_and_equivalents": 30},
                    {"prepaid_delivery_obligation": {"value": 5, "source": "s", "page": "p",
                                                     "status": "VERIFIED", "verified_kind": "tagged"}})
    rf2 = M.roll_forward_basis(nonzero, M.section5_basis(nonzero))
    assert M.resolve_on_basis(nonzero, rf2, "prepaid_delivery_obligation").value is None


def test_the_lease_pair_is_carried_together_or_not_at_all(tmp_path):
    neither = store(tmp_path, {"cash_and_equivalents": 30})
    rf = M.roll_forward_basis(neither, M.section5_basis(neither))
    assert M.resolve_on_basis(neither, rf, "lease_liabilities").value == 20
    one = store(tmp_path, {"cash_and_equivalents": 30, "operating_lease_liabilities": 19})
    rf = M.roll_forward_basis(one, M.section5_basis(one))
    assert M.resolve_on_basis(one, rf, "lease_liabilities").value is None


def test_working_capital_since_reads_the_roll_forward_year_to_date(tmp_path):
    parsed = store(tmp_path, {"working_capital_change": -50})
    assert M.working_capital_since(parsed, date(2025, 12, 31), date(2026, 6, 30))[0] == -50
    assert M.working_capital_since(parsed, date(2025, 12, 31), date(2025, 12, 31))[0] == 0.0
    assert M.working_capital_since(parsed, date(2025, 12, 31), date(2026, 9, 30))[0] is None


# --- the tagged composite --------------------------------------------------

def facts(entries):
    out = {"facts": {"us-gaap": {}}}
    for tag, val in entries.items():
        out["facts"]["us-gaap"][tag] = {"units": {"USD": [
            {"start": "2025-01-01", "end": "2025-12-31", "val": val,
             "accn": "0000000000-26-000001", "form": "10-K", "filed": "2026-02-01"}]}}
    return out


def test_the_composite_signs_drops_a_combined_tag_and_deducts_the_provision():
    f = facts({"IncreaseDecreaseInAccountsReceivable": 10.0,
               "IncreaseDecreaseInInventories": -20.0,
               "IncreaseDecreaseInAccountsPayable": 5.0,
               "IncreaseDecreaseInAccruedLiabilities": 3.0,
               "IncreaseDecreaseInAccountsPayableAndAccruedLiabilities": 8.0,
               "ProvisionForDoubtfulAccounts": -6.0})
    fig, _ = X.e140_working_capital(f, "2025-12-31", "USD", X.US_GAAP_TAXONOMY)
    # -10 + 20 + 5 + 3, the combined 8 dropped, the release -6 as tagged
    assert fig.value == pytest.approx(12.0)
    inv, _ = X.e140_working_capital(f, "2025-12-31", "USD", X.US_GAAP_TAXONOMY,
                                    inventory_is_business=True)
    assert inv.value == pytest.approx(-8.0)


def test_one_net_line_is_the_fallback_and_says_tax_is_inside():
    f = facts({"IncreaseDecreaseInOtherCurrentAssetsAndLiabilitiesNet": 97.1})
    fig, _ = X.e140_working_capital(f, "2025-12-31", "USD", X.US_GAAP_TAXONOMY)
    assert fig.value == pytest.approx(-97.1) and "ONE NET LINE" in fig.provenance


def test_a_searched_zero_needs_a_zero_year_end_leg():
    sheet = X.RollForwardSheet(end=date(2026, 6, 30), from_year_end=date(2025, 12, 31),
                               form="10-Q", accession="a")
    for leg in ("financial_liabilities_current", "financial_liabilities_noncurrent"):
        sheet.figures[leg] = X.Figure(value=0.0, tag="", start=None, end="2026-06-30",
                                      accession="a", form="10-Q", filed="",
                                      zero_basis="searched", composite="search")

    class YearEnd:
        def value(self, name):
            return {"financial_liabilities_current": 0.0,
                    "financial_liabilities_noncurrent": 909_160_000.0}[name]
    X._searched_zero_only_where_zero(sheet, YearEnd())
    assert "financial_liabilities_current" in sheet.figures
    assert "financial_liabilities_noncurrent" not in sheet.figures   # NVR's notes
    assert any("READ IT off the balance sheet" in m for m in sheet.missing)


def test_the_fill_keeps_every_other_line_and_is_idempotent():
    text = "\n".join([
        "# a comment", "ticker: TST", "annual:", "  - fiscal_year: 2025",
        "    period_end: 2025-12-31", "    figures:", "      revenue:",
        "        value: 1", "        page: \"p\"", "market:", "  as_of: 2026-01-01", ""])
    y = X.AnnualYear(fiscal_year=2025, end=date(2025, 12, 31))
    y.figures["working_capital_change"] = X.Figure(
        value=5.0, tag="T", start="2025-01-01", end="2025-12-31", accession="a",
        form="10-K", filed="f")
    once = X.fill_e140_text(text, [y], None, document="d", url="u")
    twice = X.fill_e140_text(once, [y], None, document="d", url="u")
    assert once == twice
    assert once.count("working_capital_change:") == 1
    assert "# a comment" in once and "market:" in once and "  as_of: 2026-01-01" in once
    assert once.index("working_capital_change") < once.index("market:")


# --- inline XBRL, for a filing companyfacts has not compiled ---------------

INLINE = b"""<html xmlns="http://www.w3.org/1999/xhtml"
 xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
 xmlns:xbrli="http://www.xbrl.org/2003/instance"
 xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
 xmlns:xbrldi="http://xbrl.org/2006/xbrldi"><body>
<ix:header><ix:resources>
<xbrli:context id="i"><xbrli:entity><xbrli:identifier scheme="s">1</xbrli:identifier></xbrli:entity>
 <xbrli:period><xbrli:instant>2026-06-30</xbrli:instant></xbrli:period></xbrli:context>
<xbrli:context id="d"><xbrli:entity><xbrli:identifier scheme="s">1</xbrli:identifier>
 <xbrli:segment><xbrldi:explicitMember dimension="x">y</xbrldi:explicitMember></xbrli:segment></xbrli:entity>
 <xbrli:period><xbrli:instant>2026-06-30</xbrli:instant></xbrli:period></xbrli:context>
<xbrli:context id="y"><xbrli:entity><xbrli:identifier scheme="s">1</xbrli:identifier></xbrli:entity>
 <xbrli:period><xbrli:startDate>2026-01-01</xbrli:startDate><xbrli:endDate>2026-06-30</xbrli:endDate></xbrli:period></xbrli:context>
<xbrli:unit id="usd"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
</ix:resources></ix:header>
<ix:nonFraction name="us-gaap:CashAndCashEquivalentsAtCarryingValue" contextRef="i" unitRef="usd" scale="6" decimals="-5" format="ixt:num-dot-decimal">1,155.5</ix:nonFraction>
<ix:nonFraction name="us-gaap:CashAndCashEquivalentsAtCarryingValue" contextRef="d" unitRef="usd" scale="6">9.9</ix:nonFraction>
<ix:nonFraction name="us-gaap:IncreaseDecreaseInInventories" contextRef="y" unitRef="usd" scale="6" sign="-">22.3</ix:nonFraction>
<ix:nonFraction name="us-gaap:LongTermDebtCurrent" contextRef="i" unitRef="usd" format="ixt:fixed-zero">-</ix:nonFraction>
</body></html>"""


def test_inline_facts_are_read_scaled_signed_and_never_dimensional():
    got = facts_from_inline(INLINE, accession="0001-26-000031", form="10-Q",
                            filed="2026-07-29")["facts"]["us-gaap"]
    cash = got["CashAndCashEquivalentsAtCarryingValue"]["units"]["USD"]
    assert [e["val"] for e in cash] == [1_155_500_000.0]          # the segment is not read
    assert got["IncreaseDecreaseInInventories"]["units"]["USD"][0]["val"] == -22_300_000.0
    assert got["LongTermDebtCurrent"]["units"]["USD"][0]["val"] == 0.0
    merged = merge_facts({"facts": {"us-gaap": {}}}, {"facts": got and {"us-gaap": got}})
    assert merge_facts(merged, {"facts": {"us-gaap": got}}) == merged
