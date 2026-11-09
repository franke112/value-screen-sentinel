"""E140(1)'s working capital tied to the cash flow statement (vss/cfrecon.py;
data rule, owner 2026-11-08). Fixtures: the operating sections of GoDaddy's
and NVR's FY2025 10-Ks, cut by tests/fixtures/cfrecon/extract.py."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from vss import cfrecon as C

FIX = Path(__file__).parent / "fixtures" / "cfrecon"
GDDY = FIX / "GDDY-FY2025-10k-cashflow.htm"
NVR = FIX / "NVR-FY2025-10k-cashflow.htm"
FY25 = ("2025-01-01", "2025-12-31")


@pytest.fixture(scope="module")
def cmap():
    return C.load_map()


def recon(path, ticker, cmap, window=FY25, html=None):
    return C.reconcile(html if html is not None else path.read_bytes(),
                       ticker=ticker, document=path.name,
                       start=window[0], end=window[1], cmap=cmap)


# --- GDDY: the 195.1 / 103.0 case ------------------------------------------

def test_gddy_fy2025_is_the_statement_not_the_tag_list(cmap):
    r = recon(GDDY, "GDDY", cmap)
    assert r.working_capital == pytest.approx(103_000_000)      # never 195.1m
    assert r.ocf == pytest.approx(1_599_400_000)
    tags = {p.tag for p in r.parts}
    # the two lines the companyfacts sum lost
    assert "gddy:IncreaseDecreaseinPrepaidExpenseRegistryFees" in tags
    assert "us-gaap:IncreaseDecreaseInOtherOperatingCapitalNet" in tags
    assert r.status == "VERIFIED" and r.verified_kind == "tagged"


def test_gddy_all_three_years(cmap):
    got = {(x.start, x.end): round(x.working_capital / 1e5) / 10
           for x in C.reconcile_file(GDDY, ticker="GDDY", cmap=cmap)}
    assert got == {("2025-01-01", "2025-12-31"): 103.0,
                   ("2024-01-01", "2024-12-31"): 61.2,
                   ("2023-01-01", "2023-12-31"): 130.5}


def test_printed_sign_not_the_tag_polarity(cmap):
    r = recon(GDDY, "GDDY", cmap)
    by = {p.tag: p.shown for p in r.parts}
    # an asset increase printed in parentheses is a cash outflow
    assert by["gddy:IncreaseDecreaseinPrepaidExpenseRegistryFees"] == pytest.approx(-35_100_000)
    assert by["us-gaap:IncreaseDecreaseInContractWithCustomerLiability"] == pytest.approx(206_800_000)


# --- NVR: inventory and land deposits stay in the flow -----------------------

NVR_OTHER_NET = -9_528_000      # "Other, net", under the changes heading
NVR_LOANS = -6_045_981_000 + 5_994_849_000   # E140(1) clarification (2)


def test_nvr_inventory_and_land_deposits_stay_in_the_flow(cmap):
    r = recon(NVR, "NVR", cmap)
    assert r.working_capital == pytest.approx(-273_352_000 + NVR_OTHER_NET + NVR_LOANS)
    tags = {p.tag for p in r.parts}
    assert "us-gaap:IncreaseDecreaseInInventories" not in tags
    assert "us-gaap:IncreaseDecreaseInDepositsOutstanding" not in tags
    kept = {x.tag: x.klass for x in r.rows}
    assert kept["us-gaap:IncreaseDecreaseInInventories"] == C.STAYS
    assert kept["us-gaap:IncreaseDecreaseInDepositsOutstanding"] == C.STAYS


def test_land_deposits_unclassed_for_another_filer(cmap):
    """IncreaseDecreaseInDepositsOutstanding is classed only for NVR: the
    same section read as another ticker stops on DATA MISSING."""
    with pytest.raises(C.ReconError, match="IncreaseDecreaseInDepositsOutstanding"):
        recon(NVR, "PHM", cmap)


def test_inventory_is_working_capital_without_the_override(cmap):
    bare = copy.deepcopy(cmap)
    bare["overrides"]["NVR"] = {"us-gaap:IncreaseDecreaseInDepositsOutstanding":
                                cmap["overrides"]["NVR"]["us-gaap:IncreaseDecreaseInDepositsOutstanding"]}
    r = recon(NVR, "NVR", bare)
    assert r.working_capital == pytest.approx(-273_352_000 + NVR_OTHER_NET + NVR_LOANS + 335_147_000)


# --- fail-closed --------------------------------------------------------------

def test_unknown_tag_is_data_missing(cmap):
    short = copy.deepcopy(cmap)
    del short["tags"]["us-gaap:IncreaseDecreaseInOtherOperatingCapitalNet"]
    with pytest.raises(C.ReconError, match="not in the map"):
        recon(GDDY, "GDDY", short)


def test_a_sum_that_misses_is_data_missing(cmap):
    html = GDDY.read_bytes().replace(b">206.8<", b">216.8<", 1)
    assert html != GDDY.read_bytes()
    with pytest.raises(C.ReconError, match="sum to"):
        recon(GDDY, "GDDY", cmap, html=html)


def test_half_a_parenthesis_is_data_missing(cmap):
    raw = GDDY.read_bytes()
    i = raw.index(b'name="gddy:IncreaseDecreaseinPrepaidExpenseRegistryFees"')
    j = raw.index(b"</ix:nonFraction>)", i)
    html = raw[:j] + b"</ix:nonFraction>" + raw[j + len(b"</ix:nonFraction>)"):]
    with pytest.raises(C.ReconError, match="cannot be read"):
        recon(GDDY, "GDDY", cmap, html=html)


def test_no_section_for_the_window(cmap):
    with pytest.raises(C.ReconError, match="no operating cash flow"):
        recon(GDDY, "GDDY", cmap, window=("2019-01-01", "2019-12-31"))


# --- the committed map ---------------------------------------------------------

def test_committed_map_loads_and_every_entry_has_class_and_note():
    m = C.load_map()
    for table in [m["tags"], *m["overrides"].values()]:
        for tag, e in table.items():
            assert e["class"] in C.CLASSES + (C.FOLLOWS,), tag
            assert e["section"] in C.SECTIONS, tag
            assert str(e["note"]).strip(), tag


def test_map_entry_without_note_refuses(tmp_path):
    p = tmp_path / "m.yaml"
    p.write_text("tags:\n  us-gaap:X:\n    section: changes\n    class: rörelsekapital\n",
                 encoding="utf-8")
    with pytest.raises(C.ReconError, match="no note"):
        C.load_map(p)


def test_map_entry_with_unknown_class_refuses(tmp_path):
    p = tmp_path / "m.yaml"
    p.write_text("tags:\n  us-gaap:X:\n    section: changes\n    class: swing\n    note: x\n",
                 encoding="utf-8")
    with pytest.raises(C.ReconError, match="no class"):
        C.load_map(p)


def test_provision_follows_only_a_statement_row(cmap):
    """A provision follows a stripped receivable only as a ROW of the
    statement: GoDaddy prints none, so none is in the figure."""
    r = recon(GDDY, "GDDY", cmap)
    assert not any(p.follows_receivable for p in r.parts)


# --- sections (owner, 2026-11-08) ----------------------------------------------

def test_every_row_carries_the_section_the_filing_prints(cmap):
    r = recon(NVR, "NVR", cmap)
    by = {x.tag: x.section for x in r.rows}
    assert by["us-gaap:DepreciationDepletionAndAmortization"] == C.ADJUSTMENTS
    assert by["us-gaap:IncreaseDecreaseInInventories"] == C.CHANGES
    assert by["us-gaap:OtherOperatingActivitiesCashFlowStatement"] == C.CHANGES


def test_catch_all_follows_its_section(cmap):
    nvr = {x.tag: x.klass for x in recon(NVR, "NVR", cmap).rows}
    assert nvr["us-gaap:OtherOperatingActivitiesCashFlowStatement"] == C.WC
    gddy = {x.tag: x.klass for x in recon(GDDY, "GDDY", cmap).rows}
    assert gddy["us-gaap:OtherNoncashIncomeExpense"] == C.NONCASH


def test_a_row_in_another_section_than_the_map_says_is_data_missing(cmap):
    moved = copy.deepcopy(cmap)
    moved["tags"]["us-gaap:IncreaseDecreaseInAccountsPayable"]["section"] = C.ADJUSTMENTS
    with pytest.raises(C.ReconError, match="section differs"):
        recon(GDDY, "GDDY", moved)


def test_no_changes_heading_reads_every_row_under_adjustments(cmap):
    """No changes heading (MUSA's layout): every row stands under the
    adjustments heading, so GDDY's working-capital entries no longer match
    the section the filing prints them in -- DATA MISSING, never guessed."""
    html = GDDY.read_bytes().replace(b"Changes in operating assets and liabilities",
                                     b"Movements", 1)
    with pytest.raises(C.ReconError, match="section differs"):
        recon(GDDY, "GDDY", cmap, html=html)


def test_two_changes_headings_cannot_be_sectioned(cmap):
    html = GDDY.read_bytes().replace(b"Adjustments to reconcile net income",
                                     b"Changes in assets and liabilities", 1)
    with pytest.raises(C.ReconError, match="cannot be sectioned|no operating section"):
        recon(GDDY, "GDDY", cmap, html=html)


def test_start_row_is_the_row_above_the_adjustments_heading(cmap):
    r = recon(GDDY, "GDDY", cmap)
    assert r.net_income.tag in C.START_TAGS
    assert "net income" in r.net_income.caption.lower()


def test_pending_tag_is_data_missing_with_the_proposal(cmap):
    waiting = copy.deepcopy(cmap)
    entry = waiting["tags"].pop("us-gaap:IncreaseDecreaseInAccountsPayable")
    waiting["pending"]["us-gaap:IncreaseDecreaseInAccountsPayable"] = {
        "proposal": "rörelsekapital", "note": "test"}
    with pytest.raises(C.ReconError, match="waiting for the owner.*proposed: rörelsekapital"):
        recon(GDDY, "GDDY", waiting)
    assert entry["class"] == C.WC


def test_unknown_tag_asks_the_owner(cmap):
    short = copy.deepcopy(cmap)
    del short["tags"]["us-gaap:IncreaseDecreaseInAccountsPayable"]
    with pytest.raises(C.ReconError, match="ASK THE OWNER.*Accounts payable"):
        recon(GDDY, "GDDY", short)


def test_changes_entry_outside_wc_must_name_its_exception(tmp_path):
    p = tmp_path / "m.yaml"
    p.write_text("tags:\n  us-gaap:X:\n    section: changes\n    class: kvar-i-flödet\n"
                 "    note: x\n", encoding="utf-8")
    with pytest.raises(C.ReconError, match="e140_exception"):
        C.load_map(p)
    p.write_text("tags:\n  us-gaap:X:\n    section: changes\n    class: kvar-i-flödet\n"
                 "    e140_exception: tax\n    note: x\n", encoding="utf-8")
    assert "us-gaap:X" in C.load_map(p)["tags"]


def test_entry_without_section_refuses(tmp_path):
    p = tmp_path / "m.yaml"
    p.write_text("tags:\n  us-gaap:X:\n    class: rörelsekapital\n    note: x\n",
                 encoding="utf-8")
    with pytest.raises(C.ReconError, match="no section"):
        C.load_map(p)


def test_provision_entry_names_the_filings_it_was_read_in():
    """1(b): a tag is classed only once it is read in a filing. The
    speculative entry of the first map was removed; the tag came back in
    the sweep because CPRT, CROX, DECK, LII and TPR print it."""
    e = C.load_map()["tags"]["us-gaap:ProvisionForDoubtfulAccounts"]
    assert "CPRT" in e["note"] and e["följer_fordran"] is True


def test_nvr_mortgage_loans_held_for_sale_are_working_capital(cmap):
    """E140(1) clarification (2): funded by a facility under financing,
    turned over within the cycle -- working capital, though printed above
    the changes heading."""
    r = recon(NVR, "NVR", cmap)
    by = {p.tag: (p.section, p.klass) for p in r.parts}
    assert by["us-gaap:PaymentsForOriginationOfMortgageLoansHeldForSale"] == (C.ADJUSTMENTS, C.WC)
    assert by["us-gaap:ProceedsFromSaleOfMortgageLoansHeldForSale"] == (C.ADJUSTMENTS, C.WC)


def test_catch_all_follows_its_section_even_where_the_map_saw_the_other(cmap):
    """MUSA prints "Other operating activities - net" among the adjustments;
    NVR prints "Other, net" under the changes heading. A catch-all is not
    checked against the map's section -- it takes the one it stands in."""
    moved = copy.deepcopy(cmap)
    moved["tags"]["us-gaap:OtherNoncashIncomeExpense"]["section"] = C.CHANGES
    r = recon(GDDY, "GDDY", moved)
    assert {x.tag: x.klass for x in r.rows}["us-gaap:OtherNoncashIncomeExpense"] == C.NONCASH


def test_nothing_pending_and_every_sweep_entry_says_who_classed_it():
    m = C.load_map()
    assert m["pending"] == {}
    for table in [m["tags"], *m["overrides"].values()]:
        for tag, e in table.items():
            if "classified_by" in e:
                assert e["classified_by"].startswith(("owner", "session")), tag
            if e.get("classified_by") == "session":
                assert "beslutat av sessionen 2026-11-08" in e["note"], tag


# --- E166: the store and the gate ----------------------------------------------

STORE = """ticker: X
annual:
  - fiscal_year: 2025
    period_end: 2025-12-31
    figures:
      operating_cash_flow:
        value: 10
      working_capital_change:
        value: 195100000
        page: "old tag sum"
        status: VERIFIED
        verified_kind: tagged

      capex:
        value: -1
roll_forward:
  period_end: 2026-06-30
  from_year_end: 2025-12-31
  figures:
    working_capital_change:
      value: 209100000
      page: "old"
      status: VERIFIED
      verified_kind: tagged
"""


def test_fill_replaces_only_working_capital_and_keeps_the_date(cmap):
    r = recon(GDDY, "GDDY", cmap)
    tied = {"2025-12-31": r, "2026-01-01..2026-06-30": r}
    new, done = C.fill_store_text(STORE, tied, ("2026-01-01", "2026-06-30"))
    assert done == ["2025-12-31: 103,000,000", "roll_forward: 103,000,000"]
    assert "195100000" not in new and "209100000" not in new
    assert new.count("verified_kind: tied_statement") == 2
    assert "period_end: 2026-06-30" in new and "capex:" in new and "value: -1" in new
    assert C.TIED_PREFIX in new


def test_fill_leaves_a_window_it_cannot_answer(cmap):
    new, done = C.fill_store_text(STORE, {}, ("2026-01-01", "2026-06-30"))
    assert new == STORE and done == []


def test_a_us_store_whose_working_capital_is_not_tied_does_not_strike(tmp_path):
    """E166: section 5 refuses a sec-xbrl store whose working capital is the
    old companyfacts sum, not the figure tied to the statement."""
    import shutil
    from datetime import datetime, timezone
    from vss import strike as S
    manual = tmp_path / "manual"
    shutil.copytree(Path("config/manual"), manual)
    store = manual / "CTSH.yaml"
    store.write_text(store.read_text().replace("verified_kind: tied_statement",
                                               "verified_kind: tagged"))
    records = tmp_path / "records"
    records.mkdir()
    for path in S.RECORDS_DIR.glob("CTSH-*.json"):
        (records / path.name).write_bytes(path.read_bytes())
    code, report = S.run_strike(ticker="CTSH", stamp="t", manual_dir=manual,
                                records_dir=records, docs_dir=tmp_path,
                                now=datetime(2026, 11, 1, tzinfo=timezone.utc))
    assert code != 0 and report.startswith("REFUSED")
    assert "working capital change for annual FY2023 is DATA MISSING" in report
    assert not (records / "CTSH-t.json").exists()
