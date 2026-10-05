"""SEC XBRL as a primary source: no HTML, no PDF, no model in the loop.

The fixture is a real excerpt of NIKE's companyfacts, trimmed to the tags
this module maps and the periods it needs. It carries the two traps that
made the extraction path hard, both of them real:

  * NIKE tags no OperatingIncomeLoss, because it publishes no operating
    income line. The near neighbours are different quantities and this
    module must leave the field DATA MISSING rather than substitute one.
  * NIKE's financial year ends 31 May, so its quarters are not calendar
    quarters and the `frame` field would misdate every one of them.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from vss import xbrl as X
from vss.config import ConfigError

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "earnings" / \
    "nke-companyfacts-excerpt.json"
FACTS = json.loads(FIXTURE.read_text())

def by_period(facts=None, limit=8):
    return {q.period: q for q in X.build_quarters(facts or FACTS, limit=limit)}


WATCHLIST = """
tickers:
  - ticker: NKE
    name: Nike
    currency: USD
    status: WATCH-GATED
    cik: 320187
    exec_changes: []
    quarters: []
"""


@pytest.fixture
def project(tmp_path):
    wl = tmp_path / "watchlist.yaml"
    wl.write_text(WATCHLIST)
    return {"watchlist_path": wl, "db_path": tmp_path / "vss.sqlite"}


def run(project, **kw):
    params = dict(ticker="NKE", watchlist_path=project["watchlist_path"],
                  db_path=project["db_path"], now=None,
                  fetcher=lambda cik: FACTS)
    params.update(kw)
    return X.run_xbrl(**params)


# --- SEC's access policy -------------------------------------------------


def test_no_contact_means_no_call(monkeypatch):
    """SEC asks callers to declare themselves. vss will not invent one."""
    monkeypatch.delenv(X.CONTACT_ENV, raising=False)
    with pytest.raises(X.XbrlError, match="VSS_SEC_CONTACT is not set"):
        X.fetch_company_facts(320187)


@pytest.mark.parametrize("value", ["", "   "])
def test_a_blank_contact_is_no_contact(monkeypatch, value):
    monkeypatch.setenv(X.CONTACT_ENV, value)
    with pytest.raises(X.XbrlError, match="is not set"):
        X.fetch_company_facts(320187)


def test_the_declared_contact_is_sent_verbatim(monkeypatch):
    monkeypatch.setenv(X.CONTACT_ENV, "vss/1.0 (someone@example.com)")
    seen = {}

    class Response:
        def read(self, size=None): return json.dumps(FACTS).encode()
        def __enter__(self): return self
        def __exit__(self, *exc): return False

    def opener(request, timeout=None):
        seen["ua"] = request.headers["User-agent"]
        seen["url"] = request.full_url
        return Response()

    X.fetch_company_facts(320187, opener=opener)
    assert seen["ua"] == "vss/1.0 (someone@example.com)"
    assert seen["url"] == "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320187.json"


def test_the_cik_is_zero_padded_to_ten_digits():
    assert X.API_URL.format(cik=320187).endswith("CIK0000320187.json")


def test_a_refusal_points_at_the_contact_setting(monkeypatch):
    import urllib.error
    monkeypatch.setenv(X.CONTACT_ENV, "vss/1.0 (someone@example.com)")

    def opener(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, None)

    with pytest.raises(X.XbrlError, match="VSS_SEC_CONTACT"):
        X.fetch_company_facts(320187, opener=opener)


# --- fiscal periods, from the filer's own calendar -----------------------


def test_the_fiscal_year_end_is_read_from_the_facts():
    assert X.fiscal_year_end_month(FACTS) == 5          # NIKE: 31 May


@pytest.mark.parametrize("end,expected", [
    (date(2024, 11, 30), "2025-Q2"),      # Sep-Nov 2024 is fiscal Q2 of FY2025
    (date(2025, 2, 28), "2025-Q3"),
    (date(2025, 5, 31), "2025-Q4"),       # the year-end quarter
    (date(2025, 8, 31), "2026-Q1"),       # first quarter of the NEXT fiscal year
    (date(2026, 2, 28), "2026-Q3"),
])
def test_a_may_year_end_places_its_quarters(end, expected):
    period, basis = X.fiscal_period(end, 5)
    assert period == expected
    assert basis == "fiscal"


def test_a_december_year_end_is_calendar():
    period, basis = X.fiscal_period(date(2026, 6, 30), 12)
    assert period == "2026-Q2" and basis == "calendar"


def test_the_calendar_frame_is_not_used_as_the_period():
    """SEC frames NIKE's Sep-Nov quarter as CY2024Q4. It is fiscal Q2."""
    quarters = {q.period: q for q in X.build_quarters(FACTS, limit=8)}
    figure = quarters["2025-Q2"].figures["revenue"]
    assert figure.start == "2024-09-01" and figure.end == "2024-11-30"
    assert quarters["2025-Q2"].period_basis == "fiscal"


# --- the mapping ---------------------------------------------------------


def test_the_quarters_come_out_oldest_first():
    periods = [q.period for q in X.build_quarters(FACTS, limit=8)]
    assert periods == sorted(periods)


def test_revenue_matches_the_release_for_the_same_quarter():
    """The press release says 11,279 million; XBRL says 11,279,000,000."""
    q3 = by_period()["2026-Q3"]
    assert q3.value("revenue") == 11_279_000_000.0
    assert q3.value("eps") == 0.35


def test_a_balance_sheet_instant_attaches_to_the_quarter_it_closes():
    inventory = by_period()["2026-Q3"].figures["inventory"]
    assert inventory.start is None
    assert inventory.end == "2026-02-28"
    assert inventory.value == 7_487_000_000.0      # the release's "Inventories 7,487"


def test_an_untagged_field_is_data_missing_not_substituted():
    """NIKE tags no OperatingIncomeLoss. Nothing stands in for it."""
    for q in X.build_quarters(FACTS, limit=8):
        assert "op_income" in q.missing
        assert q.value("op_income") is None


def test_op_income_maps_to_one_tag_only():
    """The near neighbours are different quantities, and were taken before."""
    assert X.TAGS["op_income"] == ("OperatingIncomeLoss",)
    for forbidden in ("GrossProfit", "IncomeLossFromContinuingOperations"):
        assert not any(forbidden in t for tags in X.TAGS.values() for t in tags)


def test_a_dead_tag_does_not_shadow_a_live_one():
    """NIKE left InventoryNet in 2011 and has used finished-goods since.

    Preference is per PERIOD: a tag with data somewhere must not hide a
    tag with data here.
    """
    assert X.TAGS["inventory"][0] == "InventoryNet"
    for q in X.build_quarters(FACTS, limit=8):
        assert q.value("inventory") is not None


def test_computed_fields_are_never_invented():
    """op_margin has no tag. Computing it from op_income is the one thing
    this project does not do, so it stays blank."""
    q = X.as_quarter(X.build_quarters(FACTS, limit=8)[-1])
    assert q.op_margin is None and q.revenue_yoy is None
    assert q.eps_consensus is None


# --- provenance ----------------------------------------------------------


def test_every_figure_names_its_tag_period_and_filing():
    provenance = by_period()["2026-Q3"].figures["revenue"].provenance
    assert "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax" in provenance
    assert "2025-12-01..2026-02-28" in provenance
    assert "0000320187-26-000037" in provenance
    assert "10-Q" in provenance


def test_an_instant_reads_as_of_rather_than_a_span():
    figure = by_period()["2026-Q3"].figures["inventory"]
    assert "as of 2026-02-28" in figure.provenance


def test_a_restatement_is_reported_rather_than_silently_preferred():
    facts = json.loads(FIXTURE.read_text())
    entries = facts["facts"]["us-gaap"]["EarningsPerShareDiluted"]["units"]["USD/shares"]
    # the QUARTER ending 2026-02-28, not the year-to-date period that
    # ends on the same day
    original = next(e for e in entries
                    if e["end"] == "2026-02-28" and e.get("start") == "2025-12-01")
    entries.append({**original, "val": 0.31, "accn": "0000320187-26-000001",
                    "filed": "2026-01-01"})
    quarters = {q.period: q for q in X.build_quarters(facts, limit=8)}
    figure = quarters["2026-Q3"].figures["eps"]
    assert figure.value == 0.35                 # the later filing stands
    assert figure.restated_from == 0.31         # the earlier one is named


# --- the command ---------------------------------------------------------


def test_the_report_leads_with_the_api_url_and_the_units(project):
    code, report = run(project)
    assert code == 0
    body = [l for l in report.splitlines() if l.strip()]
    assert "PRIMARY SOURCE" in body[1]
    assert "data.sec.gov/api/xbrl/companyfacts/CIK0000320187.json" in body[1]
    assert "UNITS:" in report and "1,000,000x step" in report


def test_the_report_proposes_entries_and_writes_nothing(project):
    before = project["watchlist_path"].read_bytes()
    _, report = run(project)
    assert "PROPOSED quarters: ENTRIES -- NOT WRITTEN" in report
    assert "vss will never write these" in report
    assert project["watchlist_path"].read_bytes() == before


def test_the_report_names_what_the_filer_did_not_tag(project):
    _, report = run(project)
    assert "## DATA MISSING" in report
    assert "`op_income`" in report and "OperatingIncomeLoss" in report


def test_the_proposed_entries_would_load(project):
    """No op_margin AND no op_income: nothing to reconcile, nothing blocked."""
    _, report = run(project)
    assert "THESE ENTRIES WILL NOT LOAD" not in report


def test_the_provenance_table_covers_every_figure(project):
    _, report = run(project)
    table = report.split("## PROVENANCE")[1]
    assert table.count("us-gaap:") >= 4 * 6      # 4 fields x 6 quarters
    assert "0000320187-26-000037" in table


def test_the_run_is_logged_with_no_model(project):
    import sqlite3
    run(project)
    conn = sqlite3.connect(project["db_path"])
    row = conn.execute("SELECT ticker, source_url, model, uncertainty_reasons "
                       "FROM earnings_runs").fetchone()
    conn.close()
    assert row[0] == "NKE"
    assert "data.sec.gov" in row[1]
    assert row[2] is None                        # no model read XBRL
    assert "op_income" in row[3]


def test_a_ticker_without_a_cik_is_refused(project, tmp_path):
    wl = tmp_path / "no-cik.yaml"
    wl.write_text(WATCHLIST.replace("    cik: 320187\n", ""))
    with pytest.raises(ConfigError, match="has no cik"):
        run(project, watchlist_path=wl)


def test_the_cik_flag_overrides_the_watchlist(project):
    seen = {}

    def fetcher(cik):
        seen["cik"] = cik
        return FACTS

    run(project, cik=999, fetcher=fetcher)
    assert seen["cik"] == 999


def test_an_unreachable_api_reports_rather_than_crashing(project):
    def boom(cik):
        raise X.XbrlError("HTTP 403 fetching data.sec.gov")

    code, report = run(project, fetcher=boom)
    assert code == 1
    assert "SOURCE UNAVAILABLE" in report and "403" in report


# --- the watchlist schema ------------------------------------------------


def test_cik_is_an_allowed_key():
    from vss.config import ALLOWED_KEYS
    assert "cik" in ALLOWED_KEYS


@pytest.mark.parametrize("value", ["not-a-number", "12x"])
def test_a_malformed_cik_fails_the_run(value):
    from vss.config import parse_watchlist
    with pytest.raises(ConfigError, match="cik must be a number"):
        parse_watchlist({"tickers": [{"ticker": "X", "name": "X", "currency": "USD",
                                      "status": "WATCH-GATED", "cik": value}]})


def test_a_zero_padded_cik_is_read_as_its_number():
    from vss.config import parse_entry
    e = parse_entry({"ticker": "X", "name": "X", "currency": "USD",
                     "status": "WATCH-GATED", "cik": "0000320187"}, 0)
    assert e.cik == 320187


# --- source: xbrl on every proposed entry --------------------------------


def test_every_proposed_entry_declares_its_source(project):
    _, report = run(project)
    block = report.split("```yaml")[1].split("```")[0]
    periods = block.count("- period:")
    assert periods == len(by_period())
    assert block.count("source: xbrl") == periods


def test_the_entries_load_without_a_margin(project):
    """The point of the marker: op_income with no op_margin, and no block."""
    _, report = run(project)
    assert "THESE ENTRIES WILL NOT LOAD" not in report


def test_op_margin_is_still_never_computed(project):
    _, report = run(project)
    block = report.split("```yaml")[1].split("```")[0]
    for line in block.splitlines():
        if line.strip().startswith("op_margin:"):
            assert line.strip() == "op_margin:", f"a margin was written: {line!r}"


def test_a_proposed_entry_round_trips_through_the_loader(project, tmp_path):
    """What vss xbrl proposes, the loader accepts -- verbatim."""
    import yaml as pyyaml
    from vss.config import parse_watchlist

    _, report = run(project)
    block = report.split("```yaml")[1].split("```")[0]
    quarters = pyyaml.safe_load(block)
    entry = {"ticker": "NKE", "name": "Nike", "currency": "USD",
             "status": "WATCH-GATED", "cik": 320187, "quarters": quarters}
    parsed = parse_watchlist({"tickers": [entry]})[0]
    assert len(parsed.quarters) == len(quarters)
    assert all(q.source == "xbrl" for q in parsed.quarters)


# --- the quarter no filing states ----------------------------------------
#
# A 10-K states the full year; the Q3 10-Q states nine months. The fourth
# quarter is the difference and is tagged by nobody -- filers stopped
# reporting discrete Q4 figures when the SEC dropped the Selected
# Quarterly Financial Data requirement in 2021. MICROSOFT last tagged one
# for the year ended 30 June 2020.


def _with_annual(end="2026-06-30", start="2025-07-01"):
    facts = json.loads(FIXTURE.read_text())
    facts["facts"]["us-gaap"]["RevenueFromContractWithCustomerExcludingAssessedTax"] \
        ["units"]["USD"].append({
            "start": start, "end": end, "val": 331_839_000_000,
            "accn": "0001193125-26-999999", "form": "10-K", "filed": "2026-07-30"})
    return facts


def test_a_year_reported_past_the_newest_quarter_is_named():
    facts = _with_annual()
    quarters = X.build_quarters(facts, limit=8)
    gap = X.untagged_tail(facts, quarters)
    assert gap is not None
    assert gap["covers_to"] == "2026-06-30"
    assert gap["form"] == "10-K"


def test_the_gap_is_reported_and_never_computed(project):
    _, report = run(project, fetcher=lambda cik: _with_annual())
    assert "A PERIOD THE FILER DID NOT TAG AS A QUARTER" in report
    assert "vss does not compute it" in report
    assert "Waiting will not produce it" in report
    # the difference between the annual and nine-month figures, unstated
    assert "90,007" not in report and "90007" not in report


def test_the_same_gap_exists_for_nike(project):
    """Not a Microsoft quirk: NIKE's own Q4 FY26 is untagged as well.

    Its newest tagged quarter ends 2026-02-28 while the year ending
    2026-05-31 is filed, so the March-May quarter is missing for exactly
    the same reason.
    """
    _, report = run(project)
    assert "A PERIOD THE FILER DID NOT TAG AS A QUARTER" in report
    assert "2026-05-31" in report


def test_no_gap_when_nothing_is_reported_past_the_newest_quarter():
    facts = json.loads(FIXTURE.read_text())
    for tag, node in facts["facts"]["us-gaap"].items():
        for unit, entries in node["units"].items():
            node["units"][unit] = [e for e in entries if e["end"] <= "2026-02-28"]
    quarters = X.build_quarters(facts, limit=8)
    assert X.untagged_tail(facts, quarters) is None


def test_the_annual_figure_never_becomes_a_quarters_revenue():
    """A 364-day period is not a quarter, however recent it is.

    The year ending 2026-05-31 states revenue of 331,839,000,000. The
    quarter that closes on the same day carries a balance sheet and no
    revenue at all -- never the year's.
    """
    q4 = by_period(_with_annual(end="2026-05-31", start="2025-06-01"))["2026-Q4"]
    assert q4.balance_sheet_only is True
    assert q4.value("revenue") is None


# --- the year-end quarter that has a balance sheet but no income statement


def _with_year_end_instants(end="2026-05-31"):
    """NIKE's FY26 balance sheet, without a fourth-quarter income statement."""
    facts = json.loads(FIXTURE.read_text())
    gaap = facts["facts"]["us-gaap"]
    for tag, value in (("AccountsReceivableNetCurrent", 5_400_000_000),
                       ("InventoryFinishedGoodsNetOfReserves", 7_900_000_000)):
        gaap[tag]["units"]["USD"].append({
            "end": end, "val": value, "accn": "0000320187-26-000088",
            "form": "10-K", "filed": "2026-07-24"})
    return facts


def test_a_year_end_balance_sheet_opens_its_quarter():
    quarters = X.build_quarters(_with_year_end_instants(), limit=8)
    latest = quarters[-1]
    assert latest.period == "2026-Q4"
    assert latest.balance_sheet_only is True
    assert latest.value("receivables") == 5_400_000_000.0
    assert latest.value("inventory") == 7_900_000_000.0


def test_that_quarter_carries_no_derived_income_statement():
    latest = X.build_quarters(_with_year_end_instants(), limit=8)[-1]
    for name in ("revenue", "op_income", "eps"):
        assert latest.value(name) is None
        assert name in latest.missing


def _without_instants_after(cutoff="2026-02-28"):
    facts = json.loads(FIXTURE.read_text())
    for node in facts["facts"]["us-gaap"].values():
        for unit, entries in node["units"].items():
            node["units"][unit] = [e for e in entries
                                   if e.get("start") or e["end"] <= cutoff]
    return facts


def test_an_instant_that_is_not_a_quarter_boundary_invents_nothing():
    """A subsequent-event date must not become a quarter of its own.

    NIKE's quarters end in Feb, May, Aug and Nov; 15 July is none of
    them, so no quarter opens for it.
    """
    facts = _without_instants_after()
    assert not any(q.balance_sheet_only for q in X.build_quarters(facts, limit=8))
    gaap = facts["facts"]["us-gaap"]
    gaap["AccountsReceivableNetCurrent"]["units"]["USD"].append(
        {"end": "2026-07-15", "val": 1, "accn": "x", "form": "8-K", "filed": "2026-07-20"})
    quarters = X.build_quarters(facts, limit=8)
    assert not any(q.balance_sheet_only for q in quarters)


def test_the_window_slides_to_the_most_recent_eight():
    """The year-end quarter joins the window, oldest first as always."""
    without = [q.period for q in X.build_quarters(_without_instants_after(), limit=8)]
    with_q4 = [q.period for q in X.build_quarters(FACTS, limit=8)]
    assert "2026-Q4" not in without
    assert with_q4[-1] == "2026-Q4"
    assert with_q4 == sorted(with_q4)
    assert len(with_q4) <= 8


def test_the_report_says_what_that_quarter_does_and_does_not_carry(project):
    _, report = run(project, fetcher=lambda cik: _with_year_end_instants())
    assert "carrying receivables and inventory and nothing" in report
    assert "DATA MISSING, not zeroes" in report


def test_a_balance_sheet_only_quarter_still_loads(project):
    """No op_income, so there is nothing for the reconciliation to check."""
    import yaml as pyyaml
    from vss.config import parse_watchlist

    _, report = run(project, fetcher=lambda cik: _with_year_end_instants())
    assert "THESE ENTRIES WILL NOT LOAD" not in report
    block = report.split("```yaml")[1].split("```")[0]
    quarters = pyyaml.safe_load(block)
    parsed = parse_watchlist({"tickers": [{"ticker": "NKE", "name": "Nike",
                                           "currency": "USD", "status": "WATCH-GATED",
                                           "quarters": quarters}]})[0]
    assert parsed.quarters[-1].period == "2026-Q4"
    assert parsed.quarters[-1].revenue is None
    assert parsed.quarters[-1].receivables == 5_400_000_000.0
