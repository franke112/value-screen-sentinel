"""`vss watch`: the filter, the cursor, and what is NOT sent.

Every release below is SYNTHETIC except one -- Pandora's company
announcement 995 of 2026-01-09, whose category and headline are quoted
exactly because it is the case the filter exists for.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vss.config import ConfigError
from vss.nordic import Issuer, Release
from vss.watch import (
    PASS_GUIDANCE,
    PASS_PERIODIC,
    PASS_WARNING,
    STATE_VERSION,
    classify,
    cron_line,
    load_state,
    notify_line,
    post_ntfy,
    render,
    run_watch,
    save_state,
    watched_tickers,
)


def release(headline, *, category="Inside information", disclosure_id=1000,
            released="2026-01-09 06:30:00 +0000"):
    return Release(disclosure_id=disclosure_id, category_id=428,
                   category=category, headline=headline, language="en",
                   market="Main Market, Copenhagen", company="Pandora A/S",
                   released=released, message_url="https://example.invalid")


# --- the filter -------------------------------------------------------------


CA_995 = ("Pandora expects to deliver 6% organic growth and around 24% EBIT "
          "margin in 2025")


def test_the_pre_announcement_passes_although_its_category_says_nothing():
    """CA 995, 2026-01-09. Filed under `Inside information` -- the same
    category as a CFO appointment -- with no "guidance" in the title, and
    it moved the stock 13%. The filter must catch it on the headline."""
    decision = classify(release(CA_995), "PNDORA.CO")
    assert decision.passes
    assert decision.kind == PASS_GUIDANCE
    assert "expects" in decision.why or "organic growth" in decision.why


def test_the_categories_the_exchange_itself_calls_a_report_pass():
    for category in ("Interim report (Q1 and Q3)", "Half Year financial report",
                     "Annual Financial Report"):
        d = classify(release("Pandora delivers 3% organic growth in Q2",
                             category=category), "PNDORA.CO")
        assert d.passes and d.kind == PASS_PERIODIC, category


def test_a_report_filed_under_inside_information_still_passes_on_its_title():
    """The category is a filing choice: Pandora's H1 2026 report is filed
    under `Inside information`. The title carries the substance."""
    d = classify(release("Pandora delivers 3% organic growth in Q2 - guidance "
                         "upgraded"), "PNDORA.CO")
    assert d.passes and d.kind == PASS_GUIDANCE


def test_a_profit_warning_is_reported_as_the_warning_it_is():
    d = classify(release("Profit warning: full-year guidance withdrawn"),
                 "TEST.XX")
    assert d.passes and d.kind == PASS_WARNING


@pytest.mark.parametrize("headline,category", [
    ("Pandora appoints Paulo Garcia as new CFO as Anders Boyer will retire",
     "Inside information"),
    ("Transactions in connection with share buyback programme",
     "Changes in company's own shares"),
    ("Trading in Pandora A/S shares by Board members, Executives and Associates",
     "Managers' Transactions"),
    ("Major shareholder announcement", "Major shareholder announcements"),
    ("Notice of Annual General Meeting", "Notice to general meeting"),
    ("Course of Annual General Meeting", "Decisions of general meeting"),
    ("Reduction of Pandora A/S' share capital",
     "Total number of voting rights and capital"),
    ("Pandora acquires its distributor in Brazil", "Inside information"),
])
def test_everything_else_is_rejected(headline, category):
    """Leadership, M&A, buybacks, managers' transactions, shareholder
    notices. None of them changes a section 5 answer."""
    d = classify(release(headline, category=category), "PNDORA.CO")
    assert not d.passes, headline
    assert category in d.why


# --- the cursor -------------------------------------------------------------


def test_the_first_run_baselines_and_reports_nothing(tmp_path):
    """A first notification carrying a year of history is how a watcher
    gets muted on the day it is installed."""
    sent = []
    code, report = run_watch(**harness(tmp_path, [release(CA_995, disclosure_id=995)],
                                       sent))
    assert code == 0 and sent == []
    assert "First run" in report and "NOTHING NEW" in report
    state = json.loads((tmp_path / "state.json").read_text())
    assert state["seen"]["PNDORA.CO"]["last_id"] == 995


def test_the_second_run_reports_only_what_arrived_after_it(tmp_path):
    sent = []
    first = [release("Notice of Annual General Meeting",
                     category="Notice to general meeting", disclosure_id=900)]
    run_watch(**harness(tmp_path, first, sent))
    later = [release(CA_995, disclosure_id=995),
             release("Trading in Pandora A/S shares by Board members",
                     category="Managers' Transactions", disclosure_id=996),
             first[0]]
    code, report = run_watch(**harness(tmp_path, later, sent))
    assert code == 0
    assert sent == [[f"PNDORA.CO 2026-01-09 {CA_995}"]]
    # the rejected row is PRINTED, not hidden
    assert "Managers' Transactions" in report
    assert "REJECTED: 1 disclosure(s)" in report


def test_nothing_new_sends_nothing_and_exits_zero(tmp_path):
    sent = []
    rows = [release(CA_995, disclosure_id=995)]
    run_watch(**harness(tmp_path, rows, sent))          # baseline
    code, report = run_watch(**harness(tmp_path, rows, sent))
    assert code == 0 and sent == []
    assert "NOTHING NEW WORTH A RE-RUN" in report


def test_a_malformed_state_file_is_an_error_not_a_silent_reset(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ConfigError, match="not readable JSON"):
        load_state(path)


def test_state_round_trips(tmp_path):
    path = tmp_path / "s.json"
    save_state({"version": STATE_VERSION, "seen": {"X": {"last_id": 5}}}, path)
    assert load_state(path)["seen"]["X"]["last_id"] == 5


# --- the notifier -----------------------------------------------------------


def test_one_line_per_disclosure_ticker_date_title():
    line = notify_line(classify(release(CA_995), "PNDORA.CO"))
    assert line == f"PNDORA.CO 2026-01-09 {CA_995}"


def test_an_empty_list_posts_nothing():
    def explode(*a, **k):  # pragma: no cover - must never be called
        raise AssertionError("posted with nothing to say")
    assert post_ntfy([], url="https://ntfy.invalid/t", opener=explode) == \
        "nothing to send"


def test_a_missing_topic_url_is_reported_and_is_not_an_error(monkeypatch):
    monkeypatch.delenv("VSS_NTFY_URL", raising=False)
    said = post_ntfy(["X 2026-01-09 headline"])
    assert "NOT SENT" in said and "VSS_NTFY_URL" in said


def test_the_post_carries_the_lines_as_its_body():
    captured = {}

    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def opener(request, timeout=None):
        captured["url"] = request.full_url
        captured["body"] = request.data.decode("utf-8")
        return Response()

    said = post_ntfy(["A 2026-01-09 one", "B 2026-02-04 two"],
                     url="https://ntfy.invalid/topic", opener=opener)
    assert captured["url"] == "https://ntfy.invalid/topic"
    assert captured["body"] == "A 2026-01-09 one\nB 2026-02-04 two"
    assert "sent 2 line(s)" in said


# --- names the feed does not carry ------------------------------------------


def test_a_ticker_with_no_nordic_issuer_is_named_not_skipped(tmp_path):
    """DECK and MC.PA are on the watchlist and not on this feed. Silence
    about them would read as "nothing filed"."""
    watchlist = tmp_path / "w.yaml"
    watchlist.write_text(
        "tickers:\n"
        "  - ticker: DECK\n    name: Deckers\n    currency: USD\n"
        "    status: WATCH-GATED\n", encoding="utf-8")
    issuers = tmp_path / "issuers.yaml"
    issuers.write_text("issuers: {}\n", encoding="utf-8")
    code, report = run_watch(watchlist_path=watchlist, issuers_path=issuers,
                             state_path=tmp_path / "state.json", send=False,
                             fetch=lambda issuer: [], now="2026-08-25T00:00:00+00:00")
    assert code == 0
    assert "NOT CHECKED" in report and "not on this feed" in report


def test_the_cron_line_is_printed_and_nothing_is_installed():
    line = cron_line()
    assert line.startswith("7 7,17 * * 1-5")
    assert "-m vss watch" in line and "VSS_NTFY_URL" in line


# --- harness ----------------------------------------------------------------


def harness(tmp_path, releases, sent):
    watchlist = tmp_path / "w.yaml"
    watchlist.write_text(
        "tickers:\n"
        "  - ticker: PNDORA.CO\n    name: PANDORA\n    currency: DKK\n"
        "    status: WATCH-GATED\n", encoding="utf-8")
    issuers = tmp_path / "issuers.yaml"
    issuers.write_text(
        "issuers:\n"
        "  PNDORA.CO:\n"
        "    market: \"Main Market, Copenhagen\"\n"
        "    company: \"Pandora A/S\"\n"
        "    language: en\n"
        "    resolved: 2026-08-24\n", encoding="utf-8")

    def poster(lines, url=None):
        if lines:
            sent.append(list(lines))
        return f"test: {len(lines)} line(s)"

    return dict(watchlist_path=watchlist, issuers_path=issuers,
                state_path=tmp_path / "state.json", send=True,
                fetch=lambda issuer: list(releases), poster=poster,
                now="2026-08-25T00:00:00+00:00")


def test_e27_both_watch_statuses_are_watched():
    """FRAMEWORK-EDITS E27: the split did not narrow what `vss watch` reads.

    A WATCH-GATED name is woken BY an event -- this command is its only
    route back. A WATCH-PRICED name is woken by its limit alert, and is
    watched anyway because a periodic report or a changed outlook moves
    the fair value its MBP is computed from; an alert armed at a stale MBP
    is exactly what E27's "an alert level is NOT an MBP" clause refuses.
    """
    from vss import rules as R
    from vss.watch import WATCHED_STATUSES

    assert "WATCH" not in WATCHED_STATUSES
    for status in R.WATCH_STATUSES:
        assert status in WATCHED_STATUSES
    assert "PIPELINE" in WATCHED_STATUSES
    assert "HELD" not in WATCHED_STATUSES and "DROPPED" not in WATCHED_STATUSES

