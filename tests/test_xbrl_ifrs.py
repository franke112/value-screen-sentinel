"""The `ifrs-full` taxonomy: a 20-F filer reaches section 5.

`_entries` opened `facts["us-gaap"]` and nothing else, and `fiscal_year_end_
month` scanned us-gaap revenue spellings. Between them they made BOTH held
names unreachable by any code path: SAP.DE and UNA.AS file 20-Fs whose facts
are entirely `ifrs-full`, so every lookup returned an empty list and the run
raised *"no annual periods in the facts"* (REVIEW-4 report B 5.1 and #10,
RUN twice on `--cik 1000184` and `--cik 217410`).

THE FIXTURES HERE ARE SYNTHETIC. The SHAPES are real -- an issuer that tags
one combined capital-expenditure line and one that tags the split pair, a
filer whose facts carry two currencies, a filer that states only a
consolidated borrowings line -- and the figures are not.
"""

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import yaml

from vss import manual as M
from vss import xbrl as X

EUR = "EUR"
RUN_TS = datetime(2026, 8, 26, 10, 0, tzinfo=ZoneInfo("Europe/Stockholm"))
FY24 = ("2024-01-01", "2024-12-31")
FY25 = ("2025-01-01", "2025-12-31")


def _fact(val, *, start=None, end=None, accn="0001104659-26-000001",
          form="20-F", filed="2026-02-26"):
    entry = {"val": val, "end": end, "accn": accn, "form": form, "filed": filed}
    if start:
        entry["start"] = start
    return entry


def _duration(tag_values, unit=EUR):
    return {"units": {unit: [
        _fact(v, start=w[0], end=w[1]) for w, v in tag_values]}}


def _instant(date_values, unit=EUR):
    return {"units": {unit: [_fact(v, end=d) for d, v in date_values]}}


def ifrs_facts(*, combined_capex=True, split_capex=False,
               borrowings_split=True, extra_usd=False,
               interest="financing", **extra):
    """An IFRS filer's two most recent years, in the shapes that matter."""
    tags = {
        "Revenue": _duration([(FY24, 30_000), (FY25, 33_000)]),
        "ProfitLossFromOperatingActivities": _duration([(FY24, 8_000), (FY25, 9_000)]),
        "ProfitLossAttributableToOwnersOfParent": _duration([(FY24, 6_000), (FY25, 6_600)]),
        "ProfitLoss": _duration([(FY24, 6_100), (FY25, 6_750)]),
        "DilutedEarningsLossPerShare": _duration(
            [(FY24, 6.0), (FY25, 6.6)], unit="EUR/shares"),
        "CashFlowsFromUsedInOperatingActivities": _duration([(FY24, 8_500), (FY25, 9_100)]),
        "PaymentsOfLeaseLiabilitiesClassifiedAsFinancingActivities":
            _duration([(FY24, 280), (FY25, 300)]),
        "CashAndCashEquivalents": _instant([("2024-12-31", 7_000), ("2025-12-31", 8_200)]),
        "Borrowings": _instant([("2024-12-31", 6_000), ("2025-12-31", 6_150)]),
        "LeaseLiabilities": _instant([("2024-12-31", 1_600), ("2025-12-31", 1_680)]),
        # E35.1: the recognised defined-benefit liability, a leg of net debt
        "RecognisedLiabilitiesDefinedBenefitPlan": _instant(
            [("2024-12-31", 241), ("2025-12-31", 249)]),
        "AdjustedWeightedAverageShares": _duration(
            [(FY24, 1_170_000_000), (FY25, 1_175_000_000)], unit="shares"),
        # E36: the EQUITY-SETTLED charge, not the total that includes the
        # cash-settled half operating cash flow has already borne.
        "ExpenseFromEquitysettledSharebasedPaymentTransactionsInWhichGoodsOr"
        "ServicesReceivedDidNotQualifyForRecognitionAsAssets": _duration(
            [(FY24, 1_591), (FY25, 1_331)]),
        "ExpenseFromSharebasedPaymentTransactionsInWhichGoodsOrServices"
        "ReceivedDidNotQualifyForRecognitionAsAssets": _duration(
            [(FY24, 2_385), (FY25, 1_695)]),
    }
    if combined_capex:
        tags["PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwill"
             "InvestmentPropertyAndOtherNoncurrentAssets"] = _duration(
                 [(FY24, 700), (FY25, 739)])
    if split_capex:
        tags["PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"] = \
            _duration([(FY24, 1_400), (FY25, 1_417)])
        tags["PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities"] = \
            _duration([(FY24, 170), (FY25, 174)])
    if borrowings_split:
        tags["CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings"] = \
            _instant([("2024-12-31", 1_500), ("2025-12-31", 1_600)])
        tags["LongtermBorrowings"] = _instant(
            [("2024-12-31", 4_500), ("2025-12-31", 4_550)])
    if interest == "financing":
        tags["InterestPaidClassifiedAsFinancingActivities"] = _duration(
            [(FY24, 550), (FY25, 574)])
        tags["InterestReceivedClassifiedAsInvestingActivities"] = _duration(
            [(FY24, 400), (FY25, 420)])
    elif interest == "operating":
        tags["InterestPaidClassifiedAsOperatingActivities"] = _duration(
            [(FY24, 220), (FY25, 211)])
        tags["InterestReceivedClassifiedAsOperatingActivities"] = _duration(
            [(FY24, 13), (FY25, 10)])
    elif interest == "both":
        tags["InterestPaidClassifiedAsFinancingActivities"] = _duration(
            [(FY25, 574)])
        tags["InterestPaidClassifiedAsOperatingActivities"] = _duration(
            [(FY25, 574)])
    if extra_usd:
        # A 2018-vintage convenience translation, as SAP's facts carry.
        tags["Revenue"]["units"]["USD"] = [
            _fact(28_205, start="2017-01-01", end="2017-12-31",
                  accn="0001104659-18-013050", form="20-F", filed="2018-02-28")]
    tags.update(extra)
    return {"facts": {"dei": {"EntityCommonStockSharesOutstanding":
                              _instant([("2026-02-01", 1_228_504_232)],
                                       unit="shares")},
                      "ifrs-full": tags}}


def us_facts():
    from tests.test_xbrl_annual import facts as nke_facts
    return nke_facts()


# --- which vocabulary, and which currency ---------------------------------


def test_the_taxonomy_comes_from_the_facts_not_from_the_form():
    assert X.pick_taxonomy(ifrs_facts()) is X.IFRS_TAXONOMY
    assert X.pick_taxonomy(us_facts()) is X.US_GAAP_TAXONOMY


def test_a_filer_reporting_in_neither_vocabulary_is_refused_not_guessed():
    with pytest.raises(X.XbrlError, match="neither"):
        X.pick_taxonomy({"facts": {"dei": {}, "srt": {}}})


def test_the_reporting_currency_is_measured_not_assumed():
    """`manual_yaml` wrote `reporting_currency: USD` as a literal.

    SAP's facts carry EUR and USD on most tags -- the USD entries are
    convenience translations from a 2018 20-F -- so "the first money unit
    found" picks whichever the JSON listed first.
    """
    assert X.reporting_currency(ifrs_facts(extra_usd=True), X.IFRS_TAXONOMY) == "EUR"
    assert X.reporting_currency(us_facts(), X.US_GAAP_TAXONOMY) == "USD"


def test_the_year_end_is_placed_from_the_taxonomy_s_own_revenue_tag():
    """Opening `ifrs-full` in `_entries` was NOT enough on its own.

    `fiscal_year_end_month` scanned `TAGS["revenue"]`, a us-gaap spelling,
    so an IFRS filer still raised "no annual periods in the facts" -- the
    exact refusal reports A and B measured on `--cik 1000184`.
    """
    facts = ifrs_facts()
    assert X.fiscal_year_end_month(facts, X.IFRS_FULL, "EUR") == 12
    with pytest.raises(X.XbrlError, match="no annual periods"):
        X.fiscal_year_end_month(facts, X.US_GAAP)


def test_naming_the_currency_is_what_makes_a_euro_only_filer_readable():
    """Unilever's facts are EUR alone, so the money-unit fallback -- which
    looks for a unit called USD -- returned nothing for it."""
    facts = ifrs_facts()
    assert X._entries(facts, "Revenue", taxonomy=X.IFRS_FULL) == []
    assert len(X._entries(facts, "Revenue", "EUR", taxonomy=X.IFRS_FULL)) == 2


# --- the map ---------------------------------------------------------------


def test_every_method_c_leg_resolves_for_a_filer_that_tags_the_split_borrowings():
    years, _ = X.build_annual(ifrs_facts())
    newest = years[-1]
    assert newest.fiscal_year == 2025
    assert newest.value("operating_cash_flow") == 9_100
    assert newest.value("capex_combined") == -739        # sign flipped, E23's one line
    assert newest.value("cash_and_equivalents") == 8_200
    assert newest.value("financial_liabilities_current") == 1_600
    assert newest.value("financial_liabilities_noncurrent") == 4_550
    assert newest.value("lease_liabilities") == 1_680
    assert newest.value("diluted_weighted_average_shares") == 1_175_000_000
    assert newest.value("lease_payments_capital") == -300


def test_a_consolidated_borrowings_line_leaves_both_fields_DATA_MISSING():
    """E14, and it is Unilever's case: 26,038 stated as one line, no split.

    The consolidated figure is NOT written into either field -- under
    IFRS 16 the face-of-balance-sheet line may contain the leases.
    """
    years, _ = X.build_annual(ifrs_facts(borrowings_split=False))
    newest = years[-1]
    assert newest.value("financial_liabilities_current") is None
    assert newest.value("financial_liabilities_noncurrent") is None
    assert "financial_liabilities_current" in newest.missing
    assert any(row[0] == "Borrowings" for row in X.IFRS_NOT_WRITTEN)


def test_the_parent_s_profit_is_written_and_the_group_total_is_not():
    """They differ by exactly the non-controlling interests."""
    years, _ = X.build_annual(ifrs_facts())
    assert years[-1].value("net_income") == 6_600        # not 6_750
    assert any(row[0] == "ProfitLoss" for row in X.IFRS_NOT_WRITTEN)


# --- E23, both shapes ------------------------------------------------------


def test_the_issuer_s_own_combined_capex_element_is_read_as_the_one_line():
    years, _ = X.build_annual(ifrs_facts(combined_capex=True, split_capex=False))
    newest = years[-1]
    assert newest.value("capex_combined") == -739
    assert newest.value("capex_ppe") is None
    assert "issuer's OWN single capital-expenditure element" in newest.capex_shape


def test_the_split_pair_is_read_where_the_filer_tags_it():
    years, _ = X.build_annual(ifrs_facts(combined_capex=False, split_capex=True))
    newest = years[-1]
    assert newest.value("capex_ppe") == -1_417
    assert newest.value("capex_intangibles") == -174
    assert newest.value("capex_combined") is None
    assert newest.capex_shape.startswith("split:")


def test_a_filer_tagging_BOTH_shapes_gets_the_split_and_never_a_mix():
    """E23: the split pair or the one line, never a mix. The combined
    element is DROPPED rather than added to the split."""
    years, _ = X.build_annual(ifrs_facts(combined_capex=True, split_capex=True))
    newest = years[-1]
    assert newest.value("capex_ppe") == -1_417
    assert newest.value("capex_intangibles") == -174
    assert newest.value("capex_combined") is None
    assert "is NOT used" in newest.capex_shape


# --- provenance and the emitted file ---------------------------------------


def test_the_page_reference_names_the_taxonomy_the_tag_belongs_to():
    """`Revenue` means one thing in `ifrs-full` and nothing in `us-gaap`."""
    years, _ = X.build_annual(ifrs_facts())
    assert years[-1].figures["revenue"].provenance.startswith("ifrs-full:Revenue [")
    us, _ = X.build_annual(us_facts())
    assert us[-1].figures["revenue"].provenance.startswith("us-gaap:")


def test_the_emitted_file_carries_the_measured_currency_and_loads():
    facts = ifrs_facts(extra_usd=True)
    taxonomy = X.pick_taxonomy(facts)
    currency = X.reporting_currency(facts, taxonomy)
    years, _ = X.build_annual(facts, taxonomy=taxonomy, currency=currency)
    text = X.manual_yaml(ticker="TEST.DE", name="Test SE", cik=1000184,
                         quote_currency="EUR", years=years, run_ts=RUN_TS,
                         facts=facts, taxonomy=taxonomy, currency=currency)
    assert "reporting_currency: EUR" in text
    assert "ifrs-full:Revenue" in text
    assert "us-gaap" not in text
    assert "interest_in_ocf:" in text and "value: no" in text
    parsed = M.parse_manual(yaml.safe_load(text), path=Path("TEST.DE.yaml"))
    gate = M.section5_gate(parsed, as_of=date(2026, 3, 31))
    assert gate.period == "annual FY2025"
    # Every leg Method C reads resolves, and under E40 a tagged fact is
    # VERIFIED by provenance, so the gate refuses NOTHING.
    states = {r.name: r for r in gate.ratios}
    assert states["free cash flow, basis 1"].state == M.RATIO_OK
    # E68 (2026-08-29): the asset-retirement leg is required and this
    # SAP-shaped filer tags none, so net debt is `input missing` ON THAT LEG
    # ALONE -- every other leg resolves -- and it is not a refusal.
    assert states["net debt"].state == M.RATIO_MISSING
    assert states["net debt"].detail.startswith("asset_retirement_obligation, prepaid_delivery_obligation is not on the basis")   # E68 and E81 legs
    # E117 (2026-09-19): an IFRS 16 filer's FCF0 deducts its principal AND
    # lease interest. The taxonomy tags the interest only as an EXPENSE, so
    # the path writes no `lease_interest_paid` and FCF0 is DATA MISSING on
    # that leg ALONE -- entered by hand from the lease note, never guessed.
    assert [r.kind for r in gate.refusals] == ["FCF0 DATA MISSING"]
    assert "lease_interest_paid" in gate.refusals[0].detail


def test_the_us_gaap_path_is_unchanged_by_any_of_this():
    """The regression that matters: NIKE's numbers do not move."""
    years, _ = X.build_annual(us_facts())
    newest = years[-1]
    assert newest.value("operating_cash_flow") == 2_868_000_000
    assert newest.value("capex_combined") == -684_000_000
    assert newest.value("diluted_weighted_average_shares") == 1_481_000_000
