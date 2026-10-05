"""E92: what a report-date refresh may do, and the four things it may not.

The refusals are the point of this file. A refresh that fetched, extracted
and reported correctly but also nudged one watchlist field would be a tool
that decides -- so the first test here is the one that says it cannot.
"""

from __future__ import annotations

import json
import urllib.error
from datetime import date, datetime
from pathlib import Path

import pytest
import yaml

from vss.manual import (KIND_TAGGED, STATUS_UNVERIFIED, STATUS_VERIFIED,
                        parse_manual)
from vss.refresh import (NO_ADAPTER, REFUSED, ROUTE_EDGAR, ROUTE_MANUAL,
                         SOURCE_DOCUMENT, SOURCE_TAGGED, Conflict, Due,
                         Extraction, NeedsOwner, RefreshError,
                         _insert_periods, _period_block,
                         assert_no_watchlist_write, due_names,
                         expected_period_end, figure_status,
                         notification_lines, ntfy_url, post_needs_owner,
                         record_refresh, render_refresh, route_for,
                         run_refresh, store_covers)

RUN_TS = datetime(2026, 10, 28, 22, 30).astimezone()
AS_OF = date(2026, 10, 28)


# --- fixtures ---------------------------------------------------------------


WATCHLIST = """\
tickers:
  - ticker: CTSH
    name: Cognizant Technology Solutions Corporation
    currency: USD
    status: WATCH-PRICED
    cik: 1058290
    fv_base: 89.38
    tier: 2
    catalyst_date: 2026-10-28
    catalyst_event: Q3 2026 results
  - ticker: SAP.DE
    name: SAP SE
    currency: EUR
    status: WATCH-PRICED
    tier: 1
    catalyst_date: 2026-10-21
    catalyst_event: Q3 2026 results
"""

STORE = """\
ticker: CTSH
name: Cognizant Technology Solutions Corporation
reporting_currency: USD
quote_currency: USD
sector: Technology
origin: sec-xbrl
money_unit: whole
share_unit: whole

annual:
  - fiscal_year: 2025
    period_end: 2025-12-31
    document: "10-K"
    figures:
      operating_cash_flow:
        value: 2883000000
        page: "us-gaap:NetCashProvidedByUsedInOperatingActivities [2025]"
        status: VERIFIED
        verified_kind: tagged
"""


class FakeFigure:
    """An xbrl.Figure's surface, without the fetch."""

    def __init__(self, value, end="2026-09-30", tag="us-gaap:Revenues"):
        self.value = value
        self.end = end
        self.provenance = f"{tag} [..{end}] 10-Q 0001058290-26-000044"


@pytest.fixture()
def repo(tmp_path):
    (tmp_path / "config" / "manual").mkdir(parents=True)
    (tmp_path / "reports").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "config" / "watchlist.yaml").write_text(WATCHLIST, encoding="utf-8")
    (tmp_path / "config" / "manual" / "CTSH.yaml").write_text(STORE, encoding="utf-8")
    return tmp_path


def entry_for(repo, ticker):
    from vss.config import load_watchlist

    entries = load_watchlist(repo / "config" / "watchlist.yaml")
    return next(e for e in entries if e.ticker == ticker)


# --- 1. A REFRESH CANNOT WRITE THE WATCHLIST --------------------------------


def test_a_refresh_leaves_the_watchlist_byte_for_byte_unchanged(repo):
    """E92's whole subject: it fetches, extracts and reports; it decides nothing."""
    watchlist = repo / "config" / "watchlist.yaml"
    before = watchlist.read_bytes()

    code, report = run_refresh(
        ticker="SAP.DE", watchlist_path=watchlist,
        manual_dir=repo / "config" / "manual",
        reports_dir=repo / "reports",
        state_path=repo / "data" / "refresh_state.json",
        now=RUN_TS)

    assert code == 0
    assert watchlist.read_bytes() == before
    # And nothing anywhere claims to have set one of the five fields.
    for forbidden in ("fv_base:", "tier:", "mbp:", "stop_price:", "status:"):
        assert f"wrote {forbidden}" not in report


def test_the_guard_stops_the_run_if_the_watchlist_ever_moves():
    """The rule is enforced by code, not only by the test above."""
    with pytest.raises(RefreshError) as exc:
        assert_no_watchlist_write(b"names: []\n", b"names: [tampered]\n")
    assert "E92 VIOLATED" in str(exc.value)


def test_a_refresh_never_scores_a_gate(repo):
    """No gate, no kill, no flag, no score -- the words are not even printed."""
    entry = entry_for(repo, "CTSH")
    due = Due(entry=entry, catalyst=date(2026, 10, 28),
              expects=date(2026, 9, 30), newest_on_file=date(2025, 12, 31),
              route=route_for(entry))
    extraction = Extraction(periods_added=["2026-Q3"], fields_added=3)
    text = render_refresh(entry=entry, due=due, extraction=extraction,
                          as_of=AS_OF, run_ts=RUN_TS, written=None,
                          store_path=repo / "config" / "manual" / "CTSH.yaml")
    lowered = text.lower()
    for word in ("gate 1", "gate 2", "hard kill", "conviction", "strengthens",
                 "weakens", "bullish", "bearish"):
        assert word not in lowered
    assert "no gate was scored" in lowered or "nothing here scores a gate" in lowered


# --- 2. PROVENANCE: tagged is VERIFIED, a rendered document is not ----------


def test_a_tagged_fact_enters_verified_tagged():
    """E40 rule 1, carried into the refresh unchanged."""
    assert figure_status(SOURCE_TAGGED) == (STATUS_VERIFIED, KIND_TAGGED)


def test_a_pdf_sourced_figure_lands_unverified_and_carries_no_kind():
    """E92: a transcription is exactly what a read-back exists to check."""
    assert figure_status(SOURCE_DOCUMENT) == (STATUS_UNVERIFIED, None)

    block, count = _period_block(
        period="2026-Q3", period_end=date(2026, 9, 30), period_basis="calendar",
        document="Q3 2026 report (PDF), p.7", url="sources/X_2026-Q3.pdf",
        figures={"revenue": FakeFigure(5_500_000_000)},
        source_kind=SOURCE_DOCUMENT)

    assert count == 1
    assert "status: UNVERIFIED" in block
    assert "verified_kind" not in block

    # And it survives the loader as UNVERIFIED -- the gate will refuse on it
    # until the owner reads it back.
    document = yaml.safe_load(
        STORE.replace("annual:", "periods:\n" + block + "\n\nannual:"))
    parsed = parse_manual(document, path=Path("config/manual/CTSH.yaml"))
    figure = parsed.periods[0].figures["revenue"]
    assert figure.status == STATUS_UNVERIFIED
    assert figure.verified_kind is None
    assert figure in parsed.unverified()


def test_a_tagged_block_survives_the_loader_as_verified_tagged():
    block, _ = _period_block(
        period="2026-Q3", period_end=date(2026, 9, 30), period_basis="calendar",
        document="SEC XBRL companyfacts", url="https://data.sec.gov/x.json",
        figures={"revenue": FakeFigure(5_500_000_000)},
        source_kind=SOURCE_TAGGED)
    document = yaml.safe_load(
        STORE.replace("annual:", "periods:\n" + block + "\n\nannual:"))
    parsed = parse_manual(document, path=Path("config/manual/CTSH.yaml"))
    figure = parsed.periods[0].figures["revenue"]
    assert figure.status == STATUS_VERIFIED
    assert figure.verified_kind == KIND_TAGGED


# --- 3. A CLOSED ROUTE: the report, and NO partial store write --------------


def test_sap_is_never_attempted_and_the_report_names_the_document(repo):
    """sap.com returns 403 on record. A refusal is a finding, not a retry."""
    entry = entry_for(repo, "SAP.DE")
    route = route_for(entry)
    assert route.kind == ROUTE_MANUAL
    assert route.manual.kind == REFUSED
    assert "403" in route.manual.reason

    store = repo / "config" / "manual" / "SAP.DE.yaml"
    code, _ = run_refresh(ticker="SAP.DE",
                          watchlist_path=repo / "config" / "watchlist.yaml",
                          manual_dir=repo / "config" / "manual",
                          reports_dir=repo / "reports",
                          state_path=repo / "data" / "refresh_state.json",
                          now=RUN_TS)

    assert code == 0
    # NO PARTIAL STORE WRITE: the file was never created.
    assert not store.exists()

    report = (repo / "reports" / "REFRESH-SAP.DE-2026-10-28.md").read_text()
    assert "THE ROUTE IS CLOSED" in report
    assert "SAP Quarterly Statement Q3 2026" in report
    assert "https://www.sap.com/investors/en/reports.html" in report
    assert "nothing was written to the store" in report.lower()


def test_a_market_with_no_adapter_is_reported_as_a_gap_not_a_wall():
    """One is a wall, the other is a gap, and only the second is worth building."""
    class E:
        ticker, cik = "MC.PA", None
    route = route_for(E())
    assert route.manual.kind == NO_ADAPTER
    assert "no EU OAM adapter" in route.manual.reason.lower() or \
           "no eu oam adapter" in route.manual.reason.lower()


def test_a_us_filer_routes_to_edgar():
    class E:
        ticker, cik = "CTSH", 1058290
    assert route_for(E()).kind == ROUTE_EDGAR


# --- 4. NTFY: unset is silence ---------------------------------------------


def test_an_unset_topic_is_a_silent_no_op(monkeypatch):
    monkeypatch.delenv("NTFY_TOPIC", raising=False)
    assert ntfy_url() is None

    posted = []
    result = post_needs_owner(["CTSH — tier — reports/x.md"],
                              opener=lambda *a, **k: posted.append(a))
    assert "not sent" in result.lower()
    assert posted == []          # nothing was even attempted


def test_an_empty_pointer_list_sends_nothing(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "vss-test")
    posted = []
    assert post_needs_owner([], opener=lambda *a, **k: posted.append(a)) == \
        "nothing to send"
    assert posted == []


def test_a_bare_topic_becomes_an_ntfy_sh_url_and_a_full_url_is_kept():
    assert ntfy_url("vss-refresh") == "https://ntfy.sh/vss-refresh"
    assert ntfy_url("https://ntfy.example.net/x") == "https://ntfy.example.net/x"


# --- 5. NTFY: a failing POST never fails the run ----------------------------


def test_a_refused_post_is_logged_and_swallowed(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "vss-test")

    def refuse(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 500, "boom", {}, None)

    result = post_needs_owner(["CTSH — tier"], opener=refuse)
    assert result.startswith("NOT SENT")


def test_a_timeout_is_logged_and_swallowed(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "vss-test")

    def hang(request, timeout=None):
        raise TimeoutError("timed out")

    assert post_needs_owner(["CTSH — tier"], opener=hang).startswith("NOT SENT")


def test_the_nightly_run_survives_a_dead_topic(monkeypatch, repo):
    """The report is the record; the notification is laid beside it."""
    monkeypatch.setenv("NTFY_TOPIC", "vss-test")
    monkeypatch.setattr("vss.refresh.urllib.request.urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("no dns")))
    # post_needs_owner is what the runner calls; it must not raise.
    assert post_needs_owner(["CTSH — tier"]).startswith("NOT SENT")


def test_the_pointer_stays_short_enough_for_a_lock_screen():
    items = [NeedsOwner(ticker=f"T{i}", report="reports/x.md",
                        waits=("tier",), refreshed="2026-10-28")
             for i in range(9)]
    lines = notification_lines(items)
    assert len(lines) == 7                      # 6 names + the "and N more"
    assert "and 3 more" in lines[-1]
    assert "`" not in "\n".join(lines)


# --- what is due, and what the store already covers -------------------------


def test_a_catalyst_reports_the_period_that_ended_before_it():
    assert expected_period_end(date(2026, 10, 28)) == date(2026, 9, 30)
    assert expected_period_end(date(2026, 11, 9)) == date(2026, 9, 30)
    assert expected_period_end(date(2026, 1, 15)) == date(2025, 12, 31)
    assert expected_period_end(date(2026, 10, 21), "half_yearly") == date(2026, 6, 30)


def test_due_selects_a_passed_catalyst_the_store_does_not_cover(repo):
    from vss.config import load_watchlist

    entries = load_watchlist(repo / "config" / "watchlist.yaml")
    due = due_names(entries, as_of=AS_OF, manual_dir=repo / "config" / "manual")
    assert {d.entry.ticker for d in due} == {"CTSH", "SAP.DE"}
    ctsh = next(d for d in due if d.entry.ticker == "CTSH")
    assert ctsh.expects == date(2026, 9, 30)
    assert ctsh.newest_on_file == date(2025, 12, 31)


def test_a_store_that_already_holds_the_period_is_not_due(repo):
    from vss.config import load_watchlist

    store = repo / "config" / "manual" / "CTSH.yaml"
    store.write_text(STORE.replace("fiscal_year: 2025", "fiscal_year: 2026")
                          .replace("period_end: 2025-12-31",
                                   "period_end: 2026-09-30")
                          .replace("[2025]", "[2026]"), encoding="utf-8")
    covered, newest = store_covers("CTSH", date(2026, 9, 30),
                                   manual_dir=repo / "config" / "manual")
    assert covered and newest == date(2026, 9, 30)

    entries = load_watchlist(repo / "config" / "watchlist.yaml")
    due = due_names(entries, as_of=AS_OF, manual_dir=repo / "config" / "manual")
    assert "CTSH" not in {d.entry.ticker for d in due}


def test_a_future_catalyst_is_not_due(repo):
    from vss.config import load_watchlist

    entries = load_watchlist(repo / "config" / "watchlist.yaml")
    due = due_names(entries, as_of=date(2026, 10, 1),
                    manual_dir=repo / "config" / "manual")
    assert due == []          # both catalysts (10-21, 10-28) are still ahead

    # ...and the day SAP's catalyst passes, it and only it is due.
    due = due_names(entries, as_of=date(2026, 10, 21),
                    manual_dir=repo / "config" / "manual")
    assert {d.entry.ticker for d in due} == {"SAP.DE"}


# --- the merge: additive, never destructive ---------------------------------


def test_new_periods_are_appended_and_every_comment_survives():
    """A YAML round-trip would throw away the rulings these files carry."""
    original = ("# THE COMMENT THAT CARRIES E62\nticker: CTSH\n\n"
                "periods:\n  - period: 2026-Q2\n    period_end: 2026-06-30\n\n"
                "annual:\n  - fiscal_year: 2025\n")
    block = "  - period: 2026-Q3\n    period_end: 2026-09-30\n"
    merged = _insert_periods(original, block)

    assert "# THE COMMENT THAT CARRIES E62" in merged
    assert merged.index("2026-Q2") < merged.index("2026-Q3")
    assert merged.index("2026-Q3") < merged.index("annual:")
    assert "fiscal_year: 2025" in merged


def test_a_file_with_no_periods_block_gets_one_opened():
    merged = _insert_periods("ticker: CTSH\n\nannual:\n  - fiscal_year: 2025\n",
                             "  - period: 2026-Q3\n")
    assert "periods:" in merged
    assert "fiscal_year: 2025" in merged
    assert yaml.safe_load(merged)["periods"][0]["period"] == "2026-Q3"


def test_a_conflict_reports_and_the_store_keeps_what_it_has():
    conflict = Conflict(period="2026-Q2", field="revenue", held=5_400_000_000.0,
                        held_status="VERIFIED (tagged)", fetched=5_450_000_000.0)
    line = conflict.line()
    assert "the store keeps what it has" in line
    assert "5,400,000,000" in line and "5,450,000,000" in line


def test_a_missed_tag_is_data_missing_and_never_e85(repo):
    """E85 stands on a searched report; a fetch searched a tag map."""
    entry = entry_for(repo, "CTSH")
    due = Due(entry=entry, catalyst=date(2026, 10, 28),
              expects=date(2026, 9, 30), newest_on_file=date(2025, 12, 31),
              route=route_for(entry))
    extraction = Extraction(periods_added=["2026-Q3"], fields_added=2,
                            missing_concepts=["asset_retirement_obligation"])
    text = render_refresh(entry=entry, due=due, extraction=extraction,
                          as_of=AS_OF, run_ts=RUN_TS, written=None,
                          store_path=Path("config/manual/CTSH.yaml"))
    assert "DATA MISSING, not NOT PRESENTED" in text
    assert "NOT PRESENTED**" not in text.replace("not NOT PRESENTED", "")


def test_the_report_says_what_a_restrike_would_read_and_writes_nothing(repo):
    entry = entry_for(repo, "CTSH")
    due = Due(entry=entry, catalyst=date(2026, 10, 28),
              expects=date(2026, 9, 30), newest_on_file=date(2025, 12, 31),
              route=route_for(entry))
    text = render_refresh(entry=entry, due=due,
                          extraction=Extraction(periods_added=["2026-Q3"],
                                                fields_added=2),
                          as_of=AS_OF, run_ts=RUN_TS, written=None,
                          store_path=Path("config/manual/CTSH.yaml"))
    assert "information, not a write" in text
    assert "no fair value is re-struck" in text.lower()
    assert "E39" in text and "E87" in text


# --- NEEDS OWNER ------------------------------------------------------------


def test_needs_owner_is_recomputed_live_and_clears_itself(repo):
    from vss.config import load_watchlist
    from vss.refresh import needs_owner

    state = repo / "data" / "refresh_state.json"
    record_refresh("CTSH", report=repo / "reports" / "REFRESH-CTSH.md",
                   as_of=AS_OF, route=ROUTE_EDGAR, periods=["2026-Q3"],
                   conflicts=0, path=state)
    entries = load_watchlist(repo / "config" / "watchlist.yaml")

    # Tier is set and the store holds nothing UNVERIFIED, so nothing waits.
    assert needs_owner(entries, state_path=state,
                       manual_dir=repo / "config" / "manual") == []

    # Add an UNVERIFIED figure: the read-back is now owed, and it shows.
    store = repo / "config" / "manual" / "CTSH.yaml"
    store.write_text(store.read_text().replace(
        "        status: VERIFIED\n        verified_kind: tagged",
        "        status: UNVERIFIED"), encoding="utf-8")
    items = needs_owner(entries, state_path=state,
                        manual_dir=repo / "config" / "manual")
    assert len(items) == 1
    assert items[0].ticker == "CTSH"
    assert "read-back" in items[0].waits[0]


def test_a_closed_route_waits_on_the_hand_download(repo):
    from vss.config import load_watchlist
    from vss.refresh import needs_owner

    state = repo / "data" / "refresh_state.json"
    run_refresh(ticker="SAP.DE",
                watchlist_path=repo / "config" / "watchlist.yaml",
                manual_dir=repo / "config" / "manual",
                reports_dir=repo / "reports", state_path=state, now=RUN_TS)
    entries = load_watchlist(repo / "config" / "watchlist.yaml")
    items = needs_owner(entries, state_path=state,
                        manual_dir=repo / "config" / "manual")
    sap = next(i for i in items if i.ticker == "SAP.DE")
    assert "hand download" in sap.waits[0]
    assert "SAP Quarterly Statement" in sap.waits[0]


def test_the_nightly_report_prints_the_pointer_at_the_top(repo):
    """A real row through the real renderer -- no hand-built stand-in."""
    from vss.fetch import FetchResult
    from vss.report import render
    from vss.runner import build_row

    entry = entry_for(repo, "CTSH")
    row = build_row(entry, FetchResult(ticker="CTSH", frame=None, source="none",
                                       fetched_at=None, error="no fetch"),
                    AS_OF)
    item = NeedsOwner(ticker="CTSH", report="reports/REFRESH-CTSH-2026-10-28.md",
                      waits=("read-back (3 UNVERIFIED)", "tier"),
                      refreshed="2026-10-28")
    text = render([row], run_ts=RUN_TS, as_of=AS_OF, needs_owner=[item])

    assert "## NEEDS OWNER — 1" in text
    # It is at the TOP: before BLOCKERS and before the table.
    assert text.index("NEEDS OWNER") < text.index("## BLOCKERS")
    assert "reports/REFRESH-CTSH-2026-10-28.md" in text
    assert "read-back (3 UNVERIFIED)" in text


def test_an_empty_needs_owner_prints_no_section(repo):
    """No heading, no empty table -- a pointer to nothing is noise."""
    from vss.fetch import FetchResult
    from vss.report import render
    from vss.runner import build_row

    row = build_row(entry_for(repo, "CTSH"),
                    FetchResult(ticker="CTSH", frame=None, source="none",
                                fetched_at=None, error="no fetch"), AS_OF)
    assert "NEEDS OWNER" not in render([row], run_ts=RUN_TS, as_of=AS_OF)


def test_the_state_file_is_a_pointer_and_holds_no_decision(repo):
    state = repo / "data" / "refresh_state.json"
    record_refresh("CTSH", report=Path("reports/REFRESH-CTSH.md"), as_of=AS_OF,
                   route=ROUTE_EDGAR, periods=["2026-Q3"], conflicts=1,
                   path=state)
    document = json.loads(state.read_text())
    held = document["refreshed"]["CTSH"]
    assert set(held) == {"date", "report", "route", "periods", "conflicts",
                         "waiting"}
    for forbidden in ("fv_base", "tier", "mbp", "stop_price", "status"):
        assert forbidden not in held


# --- the dry run ------------------------------------------------------------


def test_a_dry_run_fetches_nothing_and_writes_nothing(repo):
    state = repo / "data" / "refresh_state.json"
    code, report = run_refresh(
        due=True, dry_run=True,
        watchlist_path=repo / "config" / "watchlist.yaml",
        manual_dir=repo / "config" / "manual",
        reports_dir=repo / "reports", state_path=state, now=RUN_TS)

    assert code == 0
    assert "DRY RUN" in report
    assert not state.exists()
    assert list((repo / "reports").iterdir()) == []
    assert (repo / "config" / "manual" / "CTSH.yaml").read_text() == STORE


def test_a_dropped_name_is_not_refreshed(repo):
    """DROPPED is a record, not a stage: it is out of the process."""
    from vss.config import load_watchlist

    watchlist = repo / "config" / "watchlist.yaml"
    watchlist.write_text(
        WATCHLIST.replace("status: WATCH-PRICED\n    cik: 1058290",
                          "status: DROPPED\n    cik: 1058290"),
        encoding="utf-8")
    entries = load_watchlist(watchlist)
    due = due_names(entries, as_of=AS_OF, manual_dir=repo / "config" / "manual")
    assert "CTSH" not in {d.entry.ticker for d in due}

    # But naming it is the owner asking, and that still works.
    code, report = run_refresh(
        ticker="CTSH", dry_run=True, watchlist_path=watchlist,
        manual_dir=repo / "config" / "manual", reports_dir=repo / "reports",
        state_path=repo / "data" / "refresh_state.json", now=RUN_TS)
    assert code == 0 and "CTSH" in report


def test_a_refusing_ir_host_does_not_suppress_the_sec_route():
    """A refusal is about a HOST. sap.com turns us away; data.sec.gov does not.

    SAP is a 20-F filer whose tagged facts E41 already reads. The refusal is
    carried BESIDE the automatic route as hand work -- the quarterly
    statement a 20-F filer never files with the SEC -- and never instead of
    it.
    """
    class E:
        ticker, cik = "SAP.DE", 1000184
    route = route_for(E())
    assert route.kind == ROUTE_EDGAR
    assert route.automatic
    assert route.manual is not None and route.manual.kind == REFUSED
    assert "Quarterly Statement" in route.manual.document


def test_the_report_carries_both_the_fetch_and_the_hand_download(repo):
    class E:
        ticker, cik, name = "SAP.DE", 1000184, "SAP SE"
        catalyst_event = tier = fv_base = run_record = None
    entry = E()
    due = Due(entry=entry, catalyst=date(2026, 10, 21),
              expects=date(2026, 9, 30), newest_on_file=date(2026, 6, 30),
              route=route_for(entry))
    text = render_refresh(entry=entry, due=due,
                          extraction=Extraction(periods_added=["2026-Q3"],
                                                fields_added=4),
                          as_of=date(2026, 10, 21), run_ts=RUN_TS,
                          written=None, store_path=Path("config/manual/SAP.DE.yaml"))
    assert "ALSO NEEDED BY HAND" in text
    assert "THE ROUTE IS CLOSED" not in text
    assert "https://www.sap.com/investors/en/reports.html" in text
    assert "THE FIGURES AS FILED" in text


def test_a_tagged_extraction_never_lands_in_a_hand_read_store(repo, monkeypatch):
    """The unit trap: whole units into a millions file is a ruined history."""
    store = repo / "config" / "manual" / "CTSH.yaml"
    store.write_text(STORE.replace("origin: sec-xbrl", "origin: manual"),
                     encoding="utf-8")
    before = store.read_text()

    class Q:
        period, period_basis, balance_sheet_only = "2026-Q3", "calendar", False
        figures = {"revenue": FakeFigure(5_500_000_000)}
        missing: list = []

    monkeypatch.setattr("vss.xbrl.build_quarters", lambda facts, limit=8: [Q()])
    monkeypatch.setattr("vss.xbrl.fiscal_year_end_month", lambda facts: 12)

    from vss.refresh import extract_edgar
    out = extract_edgar(entry_for(repo, "CTSH"), expects=date(2026, 9, 30),
                        manual_dir=repo / "config" / "manual",
                        fetcher=lambda cik: {})

    assert out.periods_added == [] and out.text == ""
    assert "NOTHING IS WRITTEN" in out.note
    assert "whole units" in out.note
    assert store.read_text() == before
