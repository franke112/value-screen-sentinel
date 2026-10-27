import pytest
"""The mechanical read-back: quotes found or not, values in them or not."""
from vss import quotecheck as Q


def _doc(text):
    return Q.Doc("x", text, Q._flat(text), Q._spaced(text),
                 Q._flat(text.replace("-\n", "")))


DOC = _doc("Consolidated balance sheet\nLiquid assets 20 672 304 579 884\n"
           "Revenue 624.3 601.1 4%\nInterest on lease liabil-\nities 1.0\n"
           "Cash paid for interest $ — $ 4\nOperating profit 1,256 1,188")


def test_a_quote_is_found_through_whitespace_and_dashes():
    assert Q.find_quote("Cash paid for interest $ --", DOC) == Q.EXACT
    assert Q.find_quote("Interest on lease liabilities 1.0", DOC) == Q.EXACT


def test_a_table_row_with_a_column_between_is_near():
    assert Q.find_quote("Operating profit 1,188", DOC) == Q.NEAR


def test_a_paraphrase_is_missing():
    assert Q.find_quote("Operating profit for the year was 1,256", DOC) == Q.MISSING


def test_nordic_and_english_numbers_both_read():
    assert Q.value_in(672304, ["Liquid assets 20 672 304"])
    assert Q.value_in(0.04, ["Revenue 624.3 601.1 4%"])
    assert not Q.value_in(0.05, ["Revenue 624.3 601.1 4%"])
    assert Q.value_in(1256e6, ["Operating profit 1,256"])  # $m to whole


def test_a_total_of_stated_parts_matches():
    assert Q.value_in(73568, ["Office equipment 45 732", "Vehicles 6 333",
                              "IT equipment 21 503"])
    assert not Q.value_in(73569, ["Office equipment 45 732", "Vehicles 6 333",
                                  "IT equipment 21 503"])


def test_a_recorded_zero_search_is_counted():
    claims, terms = Q._search_claims(
        "Searched 2026-10-11 for 'asset retirement' -- ZERO occurrences")
    assert claims == [("asset retirement", 0)] and "asset retirement" in terms
    assert Q._count("asset retirement", DOC) == 0
    assert Q._count("Revenue", DOC) == 1


def test_a_filing_is_found_by_path_by_bare_name_and_by_accession():
    from pathlib import Path
    if not Path("sources/AOS_FY2025_annual-report-10k_2026-02-10_en_a0.htm").exists():
        pytest.skip("needs the filed documents in sources/, which are not "
                    "published (see SETUP.md)")
    assert Q._docs_named("x sources/RMV.L_2026-H1_half-year-financial-report"
                         "_2026-07-31_xx_a0.html (79") == [
        "sources/RMV.L_2026-H1_half-year-financial-report_2026-07-31_xx_a0.html"]
    assert Q._docs_named("Document: AOS_FY2025_annual-report-10k_2026-02-10"
                         "_en_a0.htm (the") == [
        "sources/AOS_FY2025_annual-report-10k_2026-02-10_en_a0.htm"]
    assert Q._docs_named("10-K 0000772406-26-000018 filed") == [
        "sources/_briefing_0000772406-26-000018_crus-20260328.htm.txt"]


def test_a_worked_out_figure_passes_only_on_printed_operands():
    """E132: RKT.L's lease principal, written out on the page."""
    quotes = ["Lease liabilities at 31 December 274 300",
              "New lease liabilities (71) (70)"]
    page = "Principal repaid = opening 300 + new 71 - closing 274 = 97; FX unstated"
    assert not Q.value_in(97, quotes)
    assert Q.stated_arithmetic(-97, page, quotes)
    # an operand the quotes do not print, or a sum that does not come out
    assert not Q.stated_arithmetic(97, page.replace("71", "72"), quotes)
    assert not Q.stated_arithmetic(98, page.replace("= 97", "= 98"), quotes)
