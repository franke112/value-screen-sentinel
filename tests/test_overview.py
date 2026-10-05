"""`reports/OVERVIEW.html` — the read-only page, and the four things it
must never do.

The page exists to remove one failure mode: **a row that is not there reads
as nothing to see.** So the tests that matter are the ones that catch it
putting a figure where a refusal belongs, dropping a row it could not fill,
choosing between two records nobody chose between, or writing anywhere but
`reports/`.

THE UNIT SEAM HAS ITS OWN TEST AND ITS OWN REASON. AUTO.L's close is quoted
in pence and its `fv_base` is written in pounds, and the first draft of this
page printed the distance between them as **+10,543%**. Nothing was being
grepped for; the number was absurd on sight. The test below pins the
refusal, and pins it as an INVARIANT over every row rather than on that one
name, so it still bites when the next London listing arrives.
"""

from __future__ import annotations

import html
import re
from dataclasses import replace
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path

import pytest

from vss import overview as O
from vss import render as RENDER
from vss.overview import (DISTANCE_TONES, SCALE_HIGH, SCALE_LOW,
                          SECTION_DROPPED, SECTION_LIVE, SECTION_OUTSIDE,
                          TONE_MUTED, TONE_NONE, Distance, Doc, Figure,
                          Position, QueueItem, collect, distance, documents,
                          position, run_records_for, rulings, store_tickers,
                          tone, write_overview)
from vss.render import render
from vss.sales import DATA_MISSING

#: After the New York close, so `settled_through` is the day itself.
NOW = datetime(2026, 9, 9, 23, 0).astimezone()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module", autouse=True)
def never_fetches():
    """THE PAGE IS GENERATED FROM THE REPOSITORY. A generation that fetched
    would make its contents depend on the network being up and on the hour
    it ran, and the nightly run has already written the cache it reads.

    The guard is module-scoped and autouse, so EVERY generation in this
    file proves it rather than one test doing so alone.
    """
    import vss.fetch as F

    def refuse(*args, **kwargs):
        raise AssertionError("the overview page fetched")

    saved = (F.fetch_live, F.get_history)
    F.fetch_live, F.get_history = refuse, refuse
    try:
        yield
    finally:
        F.fetch_live, F.get_history = saved


@pytest.fixture(scope="module")
def page():
    """The page built from the REAL repository, once.

    Built from the record rather than a fixture on purpose: every defect
    this page has had so far came from a real row, and a synthetic
    watchlist would have had none of them.
    """
    if not (Path(__file__).resolve().parents[1] / "data" / "cache").is_dir():
        pytest.skip("the real page needs your own price cache in data/cache -- "
                    "run `vss run` once to fetch it (see SETUP.md)")
    return collect(now=NOW)


@pytest.fixture(scope="module")
def markup(page):
    return render(page)


# --- the unit seam ---------------------------------------------------------


def test_a_distance_is_never_struck_across_two_currency_codes():
    """GBX and GBP are a hundred apart. The refusal names the seam."""
    across = distance(513.0, 4.82, "GBX", "GBP", what="fair value")
    assert across.value is None
    assert "UNIT SEAM" in across.why and "GBX" in across.why and "GBP" in across.why


def test_two_unstated_currencies_are_not_a_match():
    """Comparing an unknown with an unknown and finding them equal is how
    a seam gets crossed by a `!=` that happened to be False."""
    both = distance(10.0, 5.0, None, None, what="fair value")
    assert both.value is None and "states no currency" in both.why
    one = distance(10.0, 5.0, "USD", None, what="fair value")
    assert one.value is None and "states no currency" in one.why


def test_a_distance_is_struck_where_the_codes_match():
    same = distance(127.10, 133.48, "SEK", "SEK", what="fair value")
    assert same.value == pytest.approx(127.10 / 133.48 - 1.0)


def test_no_row_on_the_real_page_crosses_a_unit_seam(page):
    """THE INVARIANT, not the one name: a fair value in a currency that is
    not the quote currency never yields a distance."""
    for row in page.rows:
        if row.fv.amount is None or row.fv.currency is None:
            continue
        if row.fv.currency != row.currency:
            assert row.dist_fv.value is None, (
                f"{row.ticker}: a distance was struck between a "
                f"{row.currency} close and a {row.fv.currency} fair value")
            assert "UNIT SEAM" in row.dist_fv.why


def test_no_distance_on_the_real_page_is_absurd(page):
    """A cross-unit distance reads as roughly +10,500%, and nothing real
    does. Anything past ten-fold is a units bug until proven otherwise."""
    for row in page.rows:
        for dist, what in ((row.dist_fv, "fair value"), (row.dist_mbp, "MBP")):
            if dist.value is not None:
                assert abs(dist.value) < 10.0, (
                    f"{row.ticker}: {what} distance {dist.value:+.1%} is the "
                    f"shape of a unit error, not of a price")


# --- nothing is omitted ----------------------------------------------------


def test_every_name_with_an_entry_or_a_store_has_a_row(page):
    from vss.config import load_watchlist

    entries = {e.ticker for e in load_watchlist(O.WATCHLIST_PATH)}
    stores = set(store_tickers())
    assert {r.ticker for r in page.rows} == entries | stores


def test_a_row_with_no_price_survives_and_says_why(page):
    unpriced = [r for r in page.rows if r.price is None]
    assert unpriced, "the repository always has at least one unpriced store"
    for row in unpriced:
        assert DATA_MISSING in row.price_why


def test_a_row_with_no_fair_value_survives_and_says_why(page):
    for row in page.rows:
        if row.fv.amount is None:
            assert row.fv.why, f"{row.ticker}: absent fair value with no reason"


def test_the_template_is_not_a_store():
    """`config/manual/TEMPLATE.yaml` is the committed EMPTY schema. Read as
    a store it becomes a company with no name and no figures."""
    assert "TEMPLATE" not in store_tickers()


def test_a_backup_is_not_a_store(tmp_path):
    (tmp_path / "X.yaml").write_text("")
    (tmp_path / "X.yaml.bak-2026-09-01-pre-thing").write_text("")
    assert store_tickers(tmp_path) == ["X"]


# --- the page never chooses ------------------------------------------------


def test_two_run_records_and_no_named_one_is_a_refusal(tmp_path):
    """LII has a 2026-08-30 record and a 2026-08-30-e70 restrike of it.
    Which governs is E39's question, and a sort order must not answer it."""
    for name in ("X-2026-08-30.json", "X-2026-08-30-e70.json"):
        (tmp_path / name).write_text("{}")
    figure = O.provisional_value("X", directory=tmp_path)
    assert figure.amount is None
    assert "2 run records exist" in figure.why
    assert "X-2026-08-30-e70.json" in figure.why


def test_one_run_record_that_will_not_load_says_so(tmp_path):
    (tmp_path / "X-2026-08-30.json").write_text("{not json")
    figure = O.provisional_value("X", directory=tmp_path)
    assert figure.amount is None and "does not load" in figure.why


def test_a_run_record_replay_is_labelled_PROVISIONAL(page):
    """A record no entry names is arithmetic the owner has not adopted."""
    replays = [r for r in page.rows if r.fv.label]
    assert replays, "the repository always has at least one unadopted record"
    for row in replays:
        assert row.fv.label == "PROVISIONAL"
        assert "no fv_base is written on the entry" in row.fv.why


def test_a_struck_fair_value_carries_no_label(page):
    struck = [r for r in page.rows if r.fv.amount is not None and not r.fv.label]
    assert struck
    for row in struck:
        assert "replays to it" in row.fv.why


def test_run_records_for_matches_the_ticker_and_not_its_neighbours(tmp_path):
    for name in ("G-2026-08-30.json", "GDDY-2026-08-30.json",
                 "AG-2026-08-30.json", "G-notes.json"):
        (tmp_path / name).write_text("{}")
    assert [p.name for p in run_records_for("G", directory=tmp_path)] == [
        "G-2026-08-30.json"]


# --- the sections ----------------------------------------------------------


def test_outside_the_circle_names_are_not_interleaved(page):
    """E51 and E96 remove a name from section 5 entirely. It is on the page
    so its absence from the live list is visible, and nowhere near it."""
    outside = [r for r in page.rows if r.section == SECTION_OUTSIDE]
    assert outside, "E96 catches at least NHY.OL and EXE on today's record"
    for row in outside:
        assert row.circle is not None
        assert row.circle[0] in ("E51", "E96")
    live = {r.ticker for r in page.rows if r.section == SECTION_LIVE}
    assert live.isdisjoint({r.ticker for r in outside})


def test_dropped_names_are_their_own_section(page):
    dropped = [r for r in page.rows if r.section == SECTION_DROPPED]
    assert dropped
    for row in dropped:
        assert row.status == "DROPPED" and row.circle is None


def test_a_name_outside_the_circle_is_never_asked_for_SECTION_5_work(page):
    """Asking for a read-back or a growth view on a name E96 removes is
    asking for work the ruling forbids.

    A STOP IS NOT SECTION 5 WORK and is deliberately not on this list: a
    stop guards a POSITION, and a held name outside the circle still has
    one. No such name exists today; the rule is written for the day one
    does rather than discovered then.
    """
    from vss.overview import (Q_PROVISIONAL, Q_READBACK, Q_RECORD, Q_VIEW)

    section5 = {Q_VIEW, Q_READBACK, Q_PROVISIONAL, Q_RECORD}
    outside = {r.ticker for r in page.rows if r.section == SECTION_OUTSIDE}
    for item in page.queue:
        if item.kind in section5:
            assert item.ticker not in outside


def test_a_blind_industry_limb_is_printed_not_read_as_a_pass(page):
    """Fundamentals reach the survivors of filter 1 alone, so most names
    carry no vendor string and the limb cannot see them."""
    blind = [r for r in page.rows if r.circle_blind]
    assert blind, "some name on the watchlist has no stored industry string"
    for row in blind:
        assert row.circle is None


# --- the queue -------------------------------------------------------------


def test_the_queue_is_ordered_by_how_many_actions_would_clear_it(page):
    counted = [i.actions for i in page.queue if i.actions is not None]
    assert counted == sorted(counted)


def test_an_uncountable_item_sorts_last_not_first():
    known = QueueItem("k", "A", 9, "u", "d")
    unknown = QueueItem("k", "A", None, "u", "d")
    assert sorted([unknown, known], key=lambda i: i.sort_key) == [known, unknown]


def test_the_queue_never_names_a_dropped_name(page):
    dropped = {r.ticker for r in page.rows if r.section == SECTION_DROPPED}
    assert {i.ticker for i in page.queue}.isdisjoint(dropped)


def test_every_queue_item_says_what_one_action_unblocks(page):
    for item in page.queue:
        assert item.unblocks.strip() and item.detail.strip()


def test_the_read_back_counts_in_both_views_agree(page):
    """One gate, two readers. View 1 prints the count in the waiting cell
    and view 2 counts it into the queue; they are struck once."""
    from vss.overview import Q_READBACK

    queued = {i.ticker: i.actions for i in page.queue if i.kind == Q_READBACK}
    for row in page.rows:
        if row.gate is None:
            continue
        line = next((w for w in row.waiting
                     if w.startswith("read-backs:")), None)
        assert line is not None, f"{row.ticker}: no read-back line"
        assert f"read-backs: {len(row.gate.blocking)} ABOVE" in line
        if row.ticker in queued:
            assert queued[row.ticker] == len(row.gate.blocking)


def test_the_floor_line_names_both_counts_and_their_definitions(page):
    """`refresh.waits_for` counts every UNVERIFIED figure in the store and
    the gate counts the ones the basis reads after E108's floor. MEKKO.HE
    stands at 25 and 2. Printing one alone reads as contradicting the
    other."""
    for row in page.rows:
        line = next((w for w in row.waiting
                     if w.startswith("read-backs:")), None)
        if line is None:
            continue
        assert "ABOVE E108's floor" in line
        assert "UNVERIFIED in the store" in line
        assert "basis" in line


def test_an_absent_refresh_state_is_reported_not_silent(page, monkeypatch):
    """No `data/refresh_state.json` means no report-date refresh has ever
    run, which is not the same fact as nothing waiting."""
    if (PROJECT_ROOT / "data" / "refresh_state.json").exists():
        pytest.skip("a refresh state exists on this machine")
    assert any("NEEDS OWNER (E92)" in p for p in page.problems)


# --- the calendar ----------------------------------------------------------


def test_every_catalyst_date_reaches_the_calendar(page):
    from vss.config import load_watchlist

    dated = {e.ticker for e in load_watchlist(O.WATCHLIST_PATH)
             if e.catalyst_date is not None}
    assert {c.ticker for c in page.calendar} == dated


def test_the_calendar_is_ordered_by_date(page):
    assert [c.when for c in page.calendar] == sorted(c.when for c in page.calendar)


def test_a_calendar_row_carries_the_name_status(page):
    """A dangling catalyst on a DROPPED name is exactly what this page is
    for: it is visible, and it is visible as dropped."""
    for item in page.calendar:
        assert item.status


# --- the timeline ----------------------------------------------------------


def test_a_ruling_with_a_stated_date_is_marked_stated(tmp_path):
    path = tmp_path / "EDITS.md"
    path.write_text("### E1 — a thing\n\n**RULED 2026-09-04 by the owner.**\n")
    events, problems = rulings(path)
    assert not problems
    assert events[0].when == date(2026, 9, 4) and events[0].dated_by == "stated"


def test_a_ruling_whose_date_had_to_be_read_says_so(tmp_path):
    path = tmp_path / "EDITS.md"
    path.write_text("### B1 — a thing\n\nThe screen of 2026-08-22 showed it.\n")
    events, _ = rulings(path)
    assert events[0].when == date(2026, 8, 22)
    assert events[0].dated_by == "inferred from the text"


def test_an_undated_ruling_is_listed_and_counted_not_dropped(tmp_path):
    path = tmp_path / "EDITS.md"
    path.write_text("### A1 — a thing\n\nNo date anywhere in this section.\n")
    events, problems = rulings(path)
    assert len(events) == 1 and events[0].when is None
    assert events[0].dated_by == DATA_MISSING
    assert problems and "UNDATED rather than dropped" in problems[0]


def test_the_real_timeline_carries_rulings_strikes_and_verdicts(page):
    kinds = {e.kind for e in page.events}
    assert "ruling" in kinds and "strike" in kinds and "verdict" in kinds


def test_the_timeline_is_newest_first(page):
    dated = [e.when for e in page.events if e.when is not None]
    assert dated == sorted(dated, reverse=True)


# --- the shadow book -------------------------------------------------------


def test_every_verdict_in_the_book_is_measured(page):
    from vss.shadowbook import load_shadow_book

    book = load_shadow_book()
    assert len(page.shadow) == len(book)


def test_an_unelapsed_window_is_INCOMPLETE_and_never_a_partial_figure(page):
    from vss.shadowbook import INCOMPLETE

    unelapsed = [w for row in page.shadow for w in row.windows if not w.elapsed]
    assert unelapsed, "the book is young enough to have unelapsed windows"
    for window in unelapsed:
        assert window.name_change is None and window.close is None


def test_INCOMPLETE_windows_are_marked_as_such_on_the_page(markup, page):
    from vss.shadowbook import INCOMPLETE

    if any(not w.elapsed for row in page.shadow for w in row.windows):
        assert INCOMPLETE in markup


# --- what the page is ------------------------------------------------------


def test_the_page_carries_no_script_and_no_form(markup):
    """Nothing on it writes, decides or accepts anything, and that is
    enforced rather than intended: there is nothing on the page that could."""
    lowered = markup.lower()
    for forbidden in ("<script", "<form", "<button", "<input", "onclick",
                      "onload", "javascript:"):
        assert forbidden not in lowered


def test_the_page_is_one_file_with_no_second_request(markup):
    """It must open from disk and load instantly. Every external reference
    would be a request that a file:// page cannot always make."""
    assert "<link" not in markup.lower()
    for scheme in ("http://", "https://"):
        assert scheme not in markup


def test_the_page_is_well_formed(markup):
    class Check(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack: list[str] = []
            self.bad: list[str] = []

        def handle_starttag(self, tag, attrs):
            if tag not in ("meta", "br", "img", "hr", "link", "input"):
                self.stack.append(tag)

        def handle_endtag(self, tag):
            if self.stack and self.stack[-1] == tag:
                self.stack.pop()
            else:
                self.bad.append(tag)

    check = Check()
    check.feed(markup)
    assert check.bad == [] and check.stack == []


def test_every_document_link_is_relative_and_on_disk(page):
    reports = PROJECT_ROOT / "reports"
    for row in page.rows:
        for doc in row.docs:
            assert not doc.href.startswith("/")
            assert (reports / doc.href).resolve().exists(), doc.href


def test_no_briefing_is_summarised_on_the_page(markup):
    """A summary of a sourced document is a judgement without its sources.
    The page links briefings; it must not lift sentences out of them."""
    briefings = sorted((PROJECT_ROOT / "reports").glob("BRIEFING-*.md"))
    assert briefings
    for path in briefings[:8]:
        for line in path.read_text(encoding="utf-8").splitlines():
            sentence = line.strip().strip("*#-> ")
            # Long prose only: a short line can be a shared heading or a
            # field name and proves nothing either way.
            if len(sentence) > 90:
                assert sentence not in markup, f"{path.name}: {sentence[:60]}"






def test_no_percentage_carries_a_sign_on_a_rounded_zero(markup):
    """`-0.0%` on a row where nothing moved reads as a fall. `sales.pct`
    already refused it and the page uses that and not an f-string."""
    assert "-0.0%" not in markup and "+0.0%" not in markup


def test_the_waiting_cell_does_not_restate_its_own_read_back_count(page):
    """`waits_for` writes "read-back (N UNVERIFIED)" and the floor line
    carries the same N with the narrower count beside it. Printing both
    puts a number directly above its own restatement."""
    for row in page.rows:
        shorter = [w for w in row.waiting if w.startswith("read-back (")]
        longer = [w for w in row.waiting if w.startswith("read-backs:")]
        assert not (shorter and longer), row.ticker




def test_text_from_the_record_is_escaped():
    out = RENDER.code_spans("<script>alert(1)</script> & `co`")
    assert "<script>" not in out and "&lt;script&gt;" in out
    assert "&amp;" in out and "<code>co</code>" in out


# --- 1: does anything need me today ----------------------------------------


def _row(**kw) -> O.NameRow:
    base = dict(ticker="X", name="Ex plc", status="WATCH-PRICED",
                section=SECTION_LIVE, currency="USD")
    base.update(kw)
    return O.NameRow(**base)


def _cal(**kw) -> O.CalendarItem:
    base = dict(when=date(2026, 9, 12), ticker="X", status="WATCH-PRICED",
                event="Q3 results", decides="Q3 results", resolved=None)
    base.update(kw)
    return O.CalendarItem(**base)


AS_OF = date(2026, 9, 9)


def test_nothing_needing_you_is_an_answer_not_an_absence(page):
    """*Nothing needs you* and *nobody looked* are the same silence until
    the page says which. It says which."""
    block = RENDER.attention_block(replace(page, attention=[]))
    assert "Nothing needs you today." in block
    for check in O.ATTENTION_CHECKS:
        assert check in block, check


def test_the_checks_are_named_whether_or_not_anything_was_found(page):
    found = RENDER.attention_block(page)
    quiet = RENDER.attention_block(replace(page, attention=[]))
    for check in O.ATTENTION_CHECKS:
        assert check in found and check in quiet


def test_a_crossed_maximum_buy_price_reaches_the_top_line():
    items = O.attention(
        [_row(verdicts=(O.AT_BELOW_MBP,), price=59.92, mbp=67.04)],
        [], as_of=AS_OF)
    assert [i.kind for i in items] == [O.A_AT_BELOW_MBP]
    assert "59.92" in items[0].sentence and "67.04" in items[0].sentence


def test_a_crossing_the_definition_caused_says_so_and_replaces_the_plain_one():
    """E100: the MBP moved, not the price, and it arms nothing. A top line
    that read it as a buy signal would be the page arming it."""
    items = O.attention(
        [_row(verdicts=(O.DEFINITION_CROSSING, O.AT_BELOW_MBP),
              price=59.92, mbp=67.04)], [], as_of=AS_OF)
    assert [i.kind for i in items] == [O.A_DEFINITION]
    assert "arms nothing" in items[0].sentence


def test_a_stale_block_on_a_name_with_a_level_reaches_the_top_line():
    """Owner, 2026-09-19: a blocked name carrying a level says its level
    was NOT CHECKED and where it last stood."""
    from datetime import date
    items = O.attention([_row(status="HELD", blockers=(O.STALE_DATA,),
                              price=123.40, price_date=date(2026, 9, 16),
                              stop_price=112.0, mbp=51.73)], [], as_of=AS_OF)
    assert [i.kind for i in items] == [O.A_UNCHECKABLE]
    assert "NOT CHECKED" in items[0].sentence and "2026-09-16" in items[0].sentence
    assert "stop 112.00" in items[0].sentence


def test_a_holding_with_no_stop_reaches_the_top_line():
    items = O.attention([_row(status="HELD", blockers=(O.NO_STOP,))], [],
                        as_of=AS_OF)
    assert [i.kind for i in items] == [O.A_HELD_NO_STOP]


def test_a_buy_line_crossed_with_no_stop_says_the_buy_is_not_actionable():
    """"not YET actionable" was the wording before the qualifying clause
    arrived, and it implied the stop was the only thing outstanding. It
    may not be."""
    items = O.attention(
        [_row(verdicts=(O.AT_BELOW_MBP, O.NO_STOP_PRE_ENTRY),
              price=59.92, mbp=67.04)], [], as_of=AS_OF)
    assert "no stop set" in items[0].sentence
    assert "not actionable" in items[0].sentence


def test_a_level_that_could_not_be_checked_is_not_a_level_that_held():
    """A missing close on a name that HAS an MBP means the crossing was
    not checked either way, and silence would read as "it held"."""
    items = O.attention([_row(mbp=67.04, price=None)], [], as_of=AS_OF)
    assert [i.kind for i in items] == [O.A_UNCHECKABLE]
    assert "could not be checked" in items[0].sentence


def test_a_dated_event_inside_the_horizon_reaches_the_top_line():
    items = O.attention([], [_cal(when=AS_OF + timedelta(days=3))],
                        as_of=AS_OF)
    assert [i.kind for i in items] == [O.A_CATALYST]
    assert "in 3 days" in items[0].sentence


def test_a_dated_event_beyond_the_horizon_does_not():
    far = AS_OF + timedelta(days=O.ATTENTION_HORIZON_DAYS + 1)
    assert O.attention([], [_cal(when=far)], as_of=AS_OF) == []


def test_a_resolved_or_dropped_date_never_reaches_the_top_line():
    soon = AS_OF + timedelta(days=2)
    assert O.attention([], [_cal(when=soon, resolved=AS_OF)], as_of=AS_OF) == []
    assert O.attention([], [_cal(when=soon, status="DROPPED")],
                       as_of=AS_OF) == []


def test_a_dropped_or_outside_name_never_reaches_the_top_line():
    """The top line is what to do today. A name the framework has refused
    and a name it cannot value are not that."""
    assert O.attention([_row(status="DROPPED", verdicts=(O.AT_BELOW_MBP,),
                             price=1.0, mbp=2.0)], [], as_of=AS_OF) == []
    assert O.attention([_row(section=SECTION_OUTSIDE,
                             verdicts=(O.AT_BELOW_MBP,),
                             price=1.0, mbp=2.0)], [], as_of=AS_OF) == []


def test_the_top_line_is_ordered_most_urgent_first():
    items = O.attention(
        [_row(ticker="A", verdicts=(O.AT_BELOW_MBP,), price=1.0, mbp=2.0),
         _row(ticker="B", status="HELD", blockers=(O.NO_STOP,)),
         _row(ticker="C", verdicts=(O.STOP_BREACHED,), stop_price=9.0,
              price=8.0)],
        [_cal(ticker="D", when=AS_OF + timedelta(days=1))], as_of=AS_OF)
    assert [i.ticker for i in items] == ["C", "B", "A", "D"]


def test_the_kinds_the_top_line_admits_are_a_closed_list(page):
    """A top line that grew a fourth and a fifth category would be a
    second report, and the page already has one below."""
    for item in page.attention:
        assert item.kind in O.ATTENTION_ORDER


# --- a buy-side condition is never stated bare ------------------------------


def test_the_page_never_states_a_buy_side_condition_without_its_conditions(page):
    """**THE RULE.** CTSH's close sat below its maximum buy price and the
    top line said so and stopped — while the entry's own note said the
    same buy price is scheduled to fall to 58.10, which the close of
    59.92 is ABOVE. A price condition met is information; the conditions
    that qualify it are what make it an action or not."""
    for item in page.attention:
        if item.kind not in O.BUY_SIDE_KINDS:
            continue
        row = next(r for r in page.rows if r.ticker == item.ticker)
        assert O.STATUS_MEANING[row.status].split(" —")[0] in item.sentence
        if row.catalyst_date is not None and row.catalyst_resolved is None:
            assert row.catalyst_date.isoformat() in item.sentence, item.ticker
        if row.rescore.ok:
            assert f"{row.rescore.to:,.2f}" in item.sentence, item.ticker


def test_a_crossing_on_a_gated_name_says_the_gate_is_shut_in_the_same_breath():
    row = _row(status="WATCH-GATED", verdicts=(O.AT_BELOW_MBP,),
               price=59.92, mbp=67.04, catalyst_date=date(2026, 10, 28),
               catalyst_event="Q3 results")
    sentence = O.attention([row], [], as_of=AS_OF)[0].sentence
    assert "WATCH-GATED" in sentence
    assert "NAMED INFORMATION EVENT" in sentence
    assert "never on a price level" in sentence
    assert "2026-10-28" in sentence and "Q3 results" in sentence


def test_a_crossing_the_definition_caused_is_qualified_too():
    row = _row(status="WATCH-GATED", verdicts=(O.DEFINITION_CROSSING,),
               price=59.92, mbp=67.04, catalyst_date=date(2026, 10, 28),
               catalyst_event="Q3 results")
    sentence = O.attention([row], [], as_of=AS_OF)[0].sentence
    assert "E100 arms nothing" in sentence and "WATCH-GATED" in sentence


def test_a_name_with_no_catalyst_says_so_rather_than_going_quiet():
    row = _row(verdicts=(O.AT_BELOW_MBP,), price=1.0, mbp=2.0)
    sentence = O.attention([row], [], as_of=AS_OF)[0].sentence
    assert "no catalyst date" in sentence and DATA_MISSING in sentence


def test_every_status_the_schema_knows_carries_a_meaning():
    from vss.rules import VALID_STATUSES

    for status in VALID_STATUSES:
        assert status in O.STATUS_MEANING, status
        assert O.STATUS_MEANING[status].strip()


# --- the scheduled re-score, read and never derived --------------------------


def _entry(**kw):
    from vss.config import WatchlistEntry

    base = dict(ticker="X", name="Ex", currency="USD", status="WATCH-PRICED")
    base.update(kw)
    return WatchlistEntry(**base)


CTSH_NOTE = ("Q3 2026 results, due 2026-10-28 -- the next scheduled "
             "reassessment. Re-scored then under E77 (regime elevated, one "
             "tier stricter): tier 2 would become tier 3 and MBP (E90: base "
             "x cushion, unrounded replay) 67.04 -> 58.10 USD; until then "
             "the tier-2 figure stands as carried. (Arithmetic corrected "
             "2026-08-30 at E90; the E28-era prediction here read 46.78 -> "
             "40.10.)")


def test_the_rescore_is_read_off_the_entry():
    move = O.rescore(_entry(catalyst_event=CTSH_NOTE,
                            catalyst_date=date(2026, 10, 28)), 67.04)
    assert move.ok
    assert move.frm == 67.04 and move.to == 58.10
    assert move.when == date(2026, 10, 28)


def test_the_rescore_takes_the_live_pair_and_not_the_superseded_one():
    """CTSH's note carries TWO arrows: the live `67.04 -> 58.10` and, in a
    trailing parenthesis, the E28-era `46.78 -> 40.10` it supersedes.
    Reconciling the left-hand figure against the computed MBP is what
    tells them apart, and it is a check rather than a guess."""
    move = O.rescore(_entry(catalyst_event=CTSH_NOTE), 67.04)
    assert (move.frm, move.to) == (67.04, 58.10)
    assert 46.78 != move.frm and 40.10 != move.to


def test_a_rescore_that_does_not_reconcile_is_DATA_MISSING_not_a_guess():
    move = O.rescore(_entry(catalyst_event=CTSH_NOTE), 99.99)
    assert not move.ok
    assert DATA_MISSING in move.why and "do not reconcile" in move.why


def test_a_note_that_mentions_the_mbp_and_states_no_move_says_so():
    move = O.rescore(_entry(catalyst_event="the MBP stands as carried"), 10.0)
    assert not move.ok and DATA_MISSING in move.why


def test_a_note_that_never_mentions_the_mbp_is_not_a_gap():
    move = O.rescore(_entry(catalyst_event="Q3 2026 results"), 10.0)
    assert not move.ok and not move.why, "no move stated is not DATA MISSING"


def test_nothing_derives_a_rescored_buy_price():
    """E90's cushion is the owner's arithmetic. A page that recomputed the
    one-tier-stricter figure would be striking a buy price at render
    time."""
    source = (PROJECT_ROOT / "vss" / "overview.py").read_text(encoding="utf-8")
    block = source.split("def rescore(", 1)[1].split("\ndef ", 1)[0]
    for arithmetic in ("MBP_TIER_CUSHION", "compute_mbp", "* 0.65", "* 0.75"):
        assert arithmetic not in block, arithmetic


def test_the_real_ctsh_rescore_reconciles(page):
    row = next((r for r in page.rows if r.ticker == "CTSH"), None)
    if row is None or row.mbp is None:
        pytest.skip("CTSH is not on the watchlist with an MBP today")
    assert row.rescore.ok, row.rescore.why
    assert row.rescore.frm == pytest.approx(row.mbp)


# --- the card carries what qualifies it -------------------------------------


def test_every_name_with_an_open_catalyst_carries_it_on_its_card(page, markup):
    for ticker, chunk in _cards(markup):
        row = next(r for r in page.rows if r.ticker == ticker)
        open_catalyst = (row.catalyst_date is not None
                         and row.catalyst_resolved is None)
        assert ('class="waiting"' in chunk) == open_catalyst, ticker
        if open_catalyst:
            assert row.catalyst_date.isoformat() in chunk


def test_a_card_with_an_open_catalyst_always_answers_the_rescore(page, markup):
    """Three states and each is printed as itself: a move, a move this
    page could not reconcile, or no move stated."""
    for ticker, chunk in _cards(markup):
        row = next(r for r in page.rows if r.ticker == ticker)
        if row.catalyst_date is None or row.catalyst_resolved is not None:
            continue
        assert "scheduled re-score" in chunk, ticker
        if row.rescore.ok:
            assert f"{row.rescore.to:,.2f}" in chunk
        elif row.rescore.why:
            assert DATA_MISSING in chunk
        else:
            assert "states no scheduled move" in chunk, ticker


def test_the_full_catalyst_note_is_on_the_card_uncut(page, markup):
    """The top line carries the note's first sentence; the card carries
    all of it. Nothing on this page truncates a record.

    COMPARED AS TEXT, not as a substring of the markup: a long note is
    FOLDED — lead sentence, then the remainder inside a `<details>` — and
    folding is not truncating. Reading the card's text content is what
    tells the two apart.
    """
    for ticker, chunk in _cards(markup):
        row = next(r for r in page.rows if r.ticker == ticker)
        if row.catalyst_date is None or row.catalyst_resolved is not None:
            continue
        assert row.catalyst_event is not None
        text = html.unescape(re.sub(r"<[^>]+>", " ", chunk))
        text = re.sub(r"\s+", " ", text.replace("the rest of the note", " "))
        for sentence in row.catalyst_event.split(". "):
            trimmed = re.sub(r"\s+", " ", sentence.strip())
            assert trimmed in text, f"{ticker}: {trimmed[:60]}"


# --- 2: the value scale -----------------------------------------------------


def test_the_fair_value_sits_dead_centre():
    at_fv = position(100.0, 100.0, None)
    assert at_fv.ok and at_fv.price_at == pytest.approx(50.0)


def test_the_maximum_buy_price_sits_where_its_cushion_puts_it():
    """E90's tier-2 cushion is 0.75 of the base value, which on a scale
    running 50% to 150% of fair value is a quarter of the way across."""
    pos = position(100.0, 100.0, 75.0)
    assert pos.mbp_at == pytest.approx(25.0)


def test_a_price_past_either_end_sits_ON_the_end_and_says_so():
    high = position(300.0, 100.0, None)
    assert high.price_at == pytest.approx(100.0)
    assert "past the right end" in high.clipped
    low = position(10.0, 100.0, None)
    assert low.price_at == pytest.approx(0.0)
    assert "below the left end" in low.clipped


def test_the_scale_never_rescales_per_name():
    """Two names at the same fraction of fair value sit in the same place,
    or the rows cannot be read against each other."""
    a = position(80.0, 100.0, None)
    b = position(4000.0, 5000.0, None)
    assert a.price_at == pytest.approx(b.price_at)


def test_every_position_states_its_band_in_words():
    """Colour never carries a meaning on its own here."""
    for price, fv, mbp, expected in (
            (70.0, 100.0, 75.0, O.BAND_BELOW_MBP),
            (77.0, 100.0, 75.0, O.BAND_NEAR_MBP),
            (90.0, 100.0, 75.0, O.BAND_UNDER_FV),
            (120.0, 100.0, 75.0, O.BAND_OVER_FV),
            (90.0, 100.0, None, O.BAND_UNDER_FV_NO_MBP),
            (120.0, 100.0, None, O.BAND_OVER_FV_NO_MBP)):
        assert position(price, fv, mbp).band == expected


def test_a_name_with_no_buy_price_never_claims_to_have_one():
    """"above the buy price" of a price nobody struck is a sentence about
    a level that does not exist. A tier is what makes an MBP (E90)."""
    assert "buy price is struck" in position(90.0, 100.0, None).band


def test_a_unit_seam_yields_no_position_and_keeps_the_seam_as_its_reason():
    seam = distance(513.0, 4.82, "GBX", "GBP", what="fair value")
    pos = position(513.0, 4.82, None, why=seam.why)
    assert not pos.ok and "UNIT SEAM" in pos.why


def test_no_fair_value_yields_no_position_and_says_so():
    pos = position(100.0, None, None)
    assert not pos.ok and DATA_MISSING in pos.why


def test_every_row_on_the_real_page_either_has_a_position_or_says_why(page):
    for row in page.rows:
        assert row.pos.ok or row.pos.why, row.ticker


def test_every_placed_row_on_the_real_page_prints_its_band(page, markup):
    placed = [r for r in page.rows if r.pos.ok]
    assert placed
    for row in placed:
        assert row.pos.band
        assert row.pos.band in markup


def test_the_track_is_drawn_only_where_a_position_exists(page):
    for row in page.rows:
        drawn = RENDER.track(row)
        if row.pos.ok:
            assert 'class="dot' in drawn and 'class="track"' in drawn
        else:
            assert "track-missing" in drawn and "dot" not in drawn


def test_a_name_is_in_exactly_one_bucket_of_the_value_section(page, markup):
    """NOVO-B.CO is DROPPED and outside the circle, and the first draft put
    it among the names being measured. Outside outranks a status."""
    outside = {r.ticker for r in page.rows if r.section == SECTION_OUTSIDE}
    dropped = {r.ticker for r in page.rows if r.section == SECTION_DROPPED}
    live = {r.ticker for r in page.rows
            if r.section not in (SECTION_OUTSIDE, SECTION_DROPPED)}
    assert outside and dropped and live
    assert outside.isdisjoint(dropped) and outside.isdisjoint(live)
    assert dropped.isdisjoint(live)


# --- the cards --------------------------------------------------------------


def test_every_name_gets_a_card_and_not_a_table_row(page, markup):
    """A table is for comparing forty things; a card is for recognising
    one. Every name on the page is an <article>, and the only tables left
    are the shadow book's archive."""
    cards = re.findall(r'<article class="card">', markup)
    assert len(cards) == len(
        [r for r in page.rows if r.section not in (SECTION_OUTSIDE,
                                                   SECTION_DROPPED)])
    assert markup.count("<table>") == 1, "only the shadow book is a table"


def test_each_card_leads_with_the_price_and_labels_it_small(page, markup):
    """Typography does the ranking: the number that matters is large and
    its label is small and muted."""
    css = markup.split("<style>", 1)[1].split("</style>", 1)[0]

    def size(selector: str) -> float:
        block = css.split(selector, 1)[1].split("}", 1)[0]
        return float(re.search(r"font-size: ([\d.]+)rem", block).group(1))

    assert size(".price {") > size(".badge, .asof, dt {")
    assert size(".price {") > size("dl.levels dd {")


def test_every_figure_is_monospace_and_tabular(markup):
    """Digits line up down the grid, or the grid cannot be scanned."""
    css = markup.split("<style>", 1)[1].split("</style>", 1)[0]
    block = css.split(".figure {", 1)[1].split("}", 1)[0]
    assert "var(--mono)" in block
    assert "tabular-nums" in block
    assert "--mono:" in css


def test_surfaces_separate_things_and_not_rules(markup):
    """No visible table grid and no row borders. The one hairline left is
    under the footer, which is a boundary rather than a division.

    SPLIT ON DECLARATIONS, not lines: `border: 1px solid x; border-radius:
    12px;` on one line passed a line-level filter that excluded anything
    mentioning a radius, which is how this test first went green against a
    card that had grown a border.
    """
    css = markup.split("<style>", 1)[1].split("</style>", 1)[0]
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    drawn = [d.strip() for d in css.replace("{", ";").replace("}", ";").split(";")
             if re.match(r"border(-top|-bottom|-left|-right)?\s*:", d.strip())
             and "none" not in d]
    assert drawn == ["border-top: 1px solid var(--groove)"], drawn
    assert "background: var(--card)" in css


def test_a_card_that_cannot_be_drawn_still_carries_every_figure(page, markup):
    """A picture never replaces a figure. Where the sparkline is refused
    the card still prints the close, the fair value and the MBP."""
    for row in page.rows:
        if row.spark.ok or row.price is None:
            continue
        assert row.price_why or row.fv.why


# --- the sparkline ----------------------------------------------------------


def test_the_sparkline_is_inline_svg_with_no_second_request(markup):
    assert "<svg class=\"spark\"" in markup
    svgs = re.findall(r"<svg class=\"spark\".*?</svg>", markup, re.S)
    assert svgs
    for svg in svgs:
        assert "<polyline" in svg
        for forbidden in ("<image", "xlink:href", "<script"):
            assert forbidden not in svg
        # `url(#below-CTSH)` is a FRAGMENT: it names a clipPath in this
        # same document and makes no request. Any other `url(` would.
        assert not re.search(r"url\((?!#)", svg), svg[:200]


def test_every_sparkline_says_in_words_what_it_draws(page, markup):
    """The description is part of the picture, not decoration on it: the
    card survives a screen reader, a greyscale print and a browser that
    will not render the SVG."""
    svgs = re.findall(r"<svg class=\"spark\".*?</svg>", markup, re.S)
    assert svgs
    for svg in svgs:
        assert 'aria-label="' in svg and "<title>" in svg
        assert "52 weeks of closes" in svg


def test_the_two_level_lines_are_told_apart_by_dash_and_not_by_colour(markup):
    css = markup.split("<style>", 1)[1].split("</style>", 1)[0]
    fv = css.split("svg.spark .lvl.fv {", 1)[1].split("}", 1)[0]
    mbp = css.split("svg.spark .lvl.mbp {", 1)[1].split("}", 1)[0]
    assert "stroke-dasharray" in fv and "stroke-dasharray" in mbp
    assert fv.strip() != mbp.strip()
    shared = css.split("svg.spark .lvl {", 1)[1].split("}", 1)[0]
    assert "stroke: var(--faint)" in shared
    assert "stroke:" not in fv and "stroke:" not in mbp


def test_a_series_too_short_to_show_a_shape_is_refused_not_drawn(page):
    """"if the series is short or missing, the card says so instead of
    drawing a lie"."""
    refused = [r for r in page.rows if not r.spark.ok]
    assert refused, "some name on the record has no cached series"
    for row in refused:
        assert DATA_MISSING in row.spark.why
        assert not row.spark.points


def test_a_sparkline_never_drops_the_newest_close():
    """Sampling every Nth can drop the last bar, and a picture whose
    right-hand end is not today's price disagrees with the figure printed
    beside it.

    The last bar is the only high in each series, so a dropped one puts
    the drawn line at the BOTTOM of the box instead of the top. Asserting
    on the last point's x proves nothing — x is 1.0 by construction
    whichever bar it is.

    SWEPT ACROSS LENGTHS on purpose. `window[::step]` happens to land on
    the final index for some lengths and not others, and a single length
    that lands on it tests the sampling rather than the guard.
    """
    import pandas as pd

    for extra in range(8):
        days = pd.date_range(end="2026-09-08", periods=460 + extra)
        closes = [10.0] * (len(days) - 1) + [20.0]
        frame = pd.DataFrame({"Close": closes}, index=days)
        sp = O.spark(frame, as_of=date(2026, 9, 9), settled=date(2026, 9, 8))
        assert sp.ok and sp.high == 20.0
        assert sp.points[-1][1] == pytest.approx(1.0), (
            f"the newest close was dropped at {len(days)} bars")
        assert sp.last == date(2026, 9, 8)


def test_the_real_sparklines_all_end_on_a_settled_bar(page):
    for row in page.rows:
        if row.spark.ok:
            assert row.spark.last is not None
            assert row.spark.last <= page.settled


def test_a_level_inside_the_year_is_drawn_and_one_outside_is_said(page):
    for row in page.rows:
        sp = row.spark
        if not sp.ok:
            continue
        if sp.fv_y is not None:
            assert 0.0 <= sp.fv_y <= 1.0 and not sp.fv_off
        if sp.mbp_y is not None:
            assert 0.0 <= sp.mbp_y <= 1.0 and not sp.mbp_off
        for off in (sp.fv_off, sp.mbp_off):
            if off:
                assert "below everything" in off or "above everything" in off


def test_a_level_outside_the_range_never_stretches_it(page):
    """MUSA's fair value is a third of its 52-week low. A chart including
    it would show a year of trading as a flat smear at the top."""
    for row in page.rows:
        if row.spark.ok and row.price is not None:
            assert row.spark.low <= row.price <= row.spark.high


def test_the_unit_seam_reaches_the_picture_too(page):
    """A fair value in pounds drawn across a chart of pence would be a
    line at one hundredth of its height."""
    for row in page.rows:
        if row.dist_fv.value is None:
            assert row.spark.fv_y is None and not row.spark.fv_off, row.ticker
        if row.dist_mbp.value is None:
            assert row.spark.mbp_y is None and not row.spark.mbp_off


def test_the_sparkline_is_flipped_for_svg_once(tmp_path):
    """`Spark` counts y upward from the low and SVG counts down. A rising
    series must end HIGHER on the card, which is a smaller y."""
    frame = _rising_frame()
    sp = O.spark(frame, as_of=date(2026, 9, 9), settled=date(2026, 9, 8))
    assert sp.ok
    assert sp.points[0][1] < sp.points[-1][1], "the datum rises"
    svg = RENDER.sparkline(sp, "USD")
    coords = re.search(r'points="([^"]+)"', svg).group(1).split()
    first_y = float(coords[0].split(",")[1])
    last_y = float(coords[-1].split(",")[1])
    assert last_y < first_y, "SVG y grows downward, so a rise draws upward"


def _rising_frame():
    import pandas as pd

    days = pd.bdate_range("2025-08-01", "2026-09-08")
    return pd.DataFrame({"Close": [10.0 + i * 0.1 for i in range(len(days))]},
                        index=days)


def test_a_missing_series_is_refused_by_the_collector(tmp_path):
    sp = O.spark(None, as_of=date(2026, 9, 9), settled=date(2026, 9, 8))
    assert not sp.ok and DATA_MISSING in sp.why


def test_a_series_that_does_not_cover_a_year_is_refused(tmp_path):
    import pandas as pd

    days = pd.bdate_range("2026-04-01", "2026-09-08")
    frame = pd.DataFrame({"Close": [10.0] * len(days)}, index=days)
    sp = O.spark(frame, as_of=date(2026, 9, 9), settled=date(2026, 9, 8))
    assert not sp.ok
    assert "does not cover 52 weeks" in sp.why


# --- green and red: a measurement, never a verdict --------------------------


def test_the_distance_ladder_runs_from_at_or_below_to_far_above():
    assert tone(-0.50)[0] == "d-at"
    assert tone(0.0)[0] == "d-at", "the level itself is at or below it"
    assert tone(0.05)[0] == "d-near", "5% is rules' own APPROACHING band"
    assert tone(0.0501)[0] == "d-mid"
    assert tone(0.25)[0] == "d-mid"
    assert tone(0.2501)[0] == "d-far"
    assert tone(0.75)[0] == "d-far"
    assert tone(5.0)[0] == "d-remote"
    assert tone(None)[0] == TONE_NONE


def test_every_tone_carries_its_words():
    """A scale whose only carrier is hue says nothing to a red-green
    colourblind reader."""
    for bound, name, words in DISTANCE_TONES:
        assert words.strip(), name
    for value in (-0.5, 0.0, 0.03, 0.1, 0.5, 3.0):
        name, words = tone(value)
        assert name != TONE_NONE and words.strip()
    assert tone(0.0, muted=True)[1].strip()


def test_the_bands_are_ordered_and_the_last_one_catches_everything():
    bounds = [b for b, _, _ in DISTANCE_TONES if b is not None]
    assert bounds == sorted(bounds)
    assert DISTANCE_TONES[-1][0] is None


def test_a_gate_closed_name_is_muted_whatever_its_number_says():
    """A name that is cheap and gate-closed must not read as an
    invitation."""
    for value in (-0.9, 0.0, 0.5, 9.0):
        assert tone(value, muted=True)[0] == TONE_MUTED


def test_which_names_count_as_gate_closed(page):
    for row in page.rows:
        closed = row.gate_closed
        if row.section == SECTION_OUTSIDE:
            assert closed and "circle of competence" in closed
        elif row.status == "DROPPED":
            assert closed and "DROPPED" in closed
        elif row.status == "WATCH-GATED":
            assert closed and "WATCH-GATED" in closed
        else:
            assert not closed, row.ticker


def _cards(markup: str) -> list[tuple[str, str]]:
    """(ticker, markup) for every card on the page.

    Matched on `<article`, for the reason
    `test_the_whole_card_is_never_toned` records: a pattern that pins the
    exact class attribute stops matching the moment a defect changes it,
    and a loop over nothing passes.
    """
    import re as _re

    found = [(_re.search(r'class="tick">([^<]+)', chunk).group(1), chunk)
             for chunk in _re.findall(r"<article[^>]*>.*?</article>",
                                      markup, _re.S)]
    assert found, "there are no cards on the page at all"
    return found


def test_no_gate_closed_card_ever_wears_a_live_tone(page, markup):
    """DECK is 35% below fair value and its Gate 1 catalyst limb failed.
    A green figure on that card is the page arguing for a trade the
    framework has already refused."""
    for ticker, chunk in _cards(markup):
        row = next(r for r in page.rows if r.ticker == ticker)
        if not row.gate_closed:
            continue
        for live in ("d-at", "d-near", "d-mid", "d-far", "d-remote"):
            assert live not in chunk, f"{ticker} wears {live}"
        assert 'class="under"' not in chunk, (
            f"{ticker} draws a below-fair-value segment while gate-closed")


def test_a_muted_card_states_the_status_in_words(page, markup):
    for ticker, chunk in _cards(markup):
        row = next(r for r in page.rows if r.ticker == ticker)
        toned = row.pos.ok or row.dist_fv.value is not None
        if row.gate_closed and toned:
            assert "Distance shown muted" in chunk, ticker
            assert row.gate_closed in html.unescape(chunk), ticker


def test_every_toned_figure_keeps_its_sign_and_its_number(markup):
    """Colour never carries meaning alone."""
    import re as _re

    spans = _re.findall(r'<span class="figure d-[a-z]+"[^>]*>([^<]+)</span>',
                        markup)
    assert spans
    for text in spans:
        assert _re.fullmatch(r"[+-]?[\d,]+\.\d%", text), text


def test_every_toned_figure_carries_its_band_as_a_title(markup):
    import re as _re

    spans = _re.findall(r'<span class="figure d-[a-z]+"([^>]*)>', markup)
    assert spans
    for attrs in spans:
        assert 'title="' in attrs


def test_the_whole_card_is_never_toned(markup):
    """A green card reads as approval. The tone is on figures and marks.

    MATCHED ON `<article`, NOT ON `class="card"`. A first cut searched for
    `<article class="card"[^>]*>`, which a card carrying `class="card
    d-at"` does not match at all — the loop found nothing and the test
    passed on the defect it was written to catch. Three tests in this file
    have now gone green that way; the shape to distrust is a `findall`
    whose pattern the defect deletes.
    """
    import re as _re

    tags = _re.findall(r"<article[^>]*>", markup)
    assert tags, "there are no cards on the page at all"
    for tag in tags:
        assert tag == '<article class="card">', tag


def test_the_shadow_book_is_never_toned(markup):
    """Its columns are RETURNS since a verdict, not distances to a level:
    a dropped name that rose is not green."""
    table = markup.split('<div class="scroll">', 1)[1]
    assert "figure d-" not in table


def test_the_accent_and_the_distance_scale_never_share_a_role(markup):
    """The accent is a SURFACE, filling the block at the top; the distance
    scale is INK on cards. Neither takes the other's role, which is what
    stops a red figure being read as "this needs you"."""
    css = markup.split("<style>", 1)[1].split("</style>", 1)[0]
    accent = [line.strip() for line in css.splitlines()
              if "var(--accent)" in line]
    assert len(accent) == 1 and "background:" in accent[0]
    # No distance tone inside any `.attention` rule.
    for block in re.findall(r"\.attention[^{]*\{([^}]*)\}", css):
        assert "--d-" not in block, block
    # ... and no accent inside any distance rule.
    for block in re.findall(r"\.d-[a-z]+[^{]*\{([^}]*)\}", css):
        assert "--accent" not in block, block


def test_green_is_not_the_accent_and_needs_nothing_by_itself():
    """A name can be green and need nothing. The two scales are computed
    from different things and the top line never reads a tone."""
    green = _row(price=50.0, mbp=None, dist_fv=Distance(-0.4))
    assert tone(green.dist_fv.value)[0] == "d-at"
    assert O.attention([green], [], as_of=AS_OF) == []


def test_a_name_that_needs_you_may_wear_any_tone():
    """The thing that needs the owner can be red: a breached stop is an
    attention item whatever the distance says."""
    row = _row(status="HELD", verdicts=(O.STOP_BREACHED,), stop_price=9.0,
               price=8.0, dist_fv=Distance(2.0))
    assert tone(row.dist_fv.value)[0] == "d-remote"
    assert [i.kind for i in O.attention([row], [], as_of=AS_OF)] == [
        O.A_STOP_BREACHED]


# --- the sparkline's below-fair-value segment --------------------------------


def test_below_fair_value_is_the_level_where_the_level_is_in_range():
    import pandas as pd

    days = pd.date_range(end="2026-09-08", periods=460)
    frame = pd.DataFrame({"Close": [10.0 + (i % 11) for i in range(len(days))]},
                         index=days)
    sp = O.spark(frame, as_of=date(2026, 9, 9), settled=date(2026, 9, 8),
                 fv=15.0)
    assert sp.fv_y is not None
    assert sp.below_fv_y == pytest.approx(sp.fv_y)


def test_a_fair_value_above_the_whole_year_means_all_of_it_was_below():
    """CTSH is the case: its fair value is above its 52-week high, so the
    entire year traded below fair value and the whole line is drawn so."""
    import pandas as pd

    days = pd.date_range(end="2026-09-08", periods=460)
    frame = pd.DataFrame({"Close": [10.0 + (i % 11) for i in range(len(days))]},
                         index=days)
    sp = O.spark(frame, as_of=date(2026, 9, 9), settled=date(2026, 9, 8),
                 fv=500.0)
    assert sp.fv_y is None, "there is no line to draw inside the box"
    assert sp.below_fv_y == 1.0
    assert "above everything" in sp.fv_off


def test_a_fair_value_below_the_whole_year_means_none_of_it_was():
    import pandas as pd

    days = pd.date_range(end="2026-09-08", periods=460)
    frame = pd.DataFrame({"Close": [10.0 + (i % 11) for i in range(len(days))]},
                         index=days)
    sp = O.spark(frame, as_of=date(2026, 9, 9), settled=date(2026, 9, 8),
                 fv=1.0)
    assert sp.fv_y is None and sp.below_fv_y is None
    assert "below everything" in sp.fv_off


def test_no_fair_value_means_no_segment():
    import pandas as pd

    days = pd.date_range(end="2026-09-08", periods=460)
    frame = pd.DataFrame({"Close": [10.0] * len(days)}, index=days)
    sp = O.spark(frame, as_of=date(2026, 9, 9), settled=date(2026, 9, 8))
    assert sp.below_fv_y is None


def test_the_segment_is_drawn_only_where_the_record_says_it_should_be(page,
                                                                     markup):
    for ticker, chunk in _cards(markup):
        row = next(r for r in page.rows if r.ticker == ticker)
        drawn = 'class="under"' in chunk
        should = row.spark.below_fv_y is not None and not row.gate_closed
        assert drawn == should, ticker


def test_every_clip_path_id_is_unique(markup):
    import re as _re

    ids = _re.findall(r'<clipPath id="([^"]+)"', markup)
    assert ids and len(ids) == len(set(ids))
    for ident in ids:
        assert f'url(#{ident})' in markup


# --- 3: what is coming ------------------------------------------------------


def _forward_rows(markup: str) -> list[str]:
    """The forward list's rows, one string each.

    Split PER ROW and not searched as one blob: CTSH and UNA.AS share the
    date 2026-10-28, so a test asking "is this date in the block" answers
    yes for the one that must not be there.
    """
    section = markup.split('id="ahead"', 1)[1].split("</section>", 1)[0]
    ahead = section.split('class="rest"', 1)[0]
    return ahead.split('<div class="crow">')[1:]


def test_the_forward_list_holds_only_unresolved_dates_from_today(page, markup):
    rows = _forward_rows(markup)
    for item in page.calendar:
        shown = any(item.when.isoformat() in row
                    and f">{item.ticker}</b>" in row for row in rows)
        should = (item.resolved is None and item.when >= page.as_of
                  and item.status != "DROPPED")
        assert shown == should, item.ticker


def test_a_dropped_name_never_appears_as_something_that_is_coming(page, markup):
    """UNA.AS was sold in August and its entry still carries a Q3 date. In
    the forward list it reads as a report the owner is waiting for."""
    rows = _forward_rows(markup)
    for item in page.calendar:
        if item.status == "DROPPED":
            assert not any(f">{item.ticker}</b>" in row for row in rows)


def test_a_long_note_is_folded_and_never_truncated():
    """An ellipsis on a record is a record nobody can read."""
    body = ("First sentence. " + "x" * 400)
    out = RENDER._decides(body)
    assert "First sentence." in out and "x" * 400 in out
    assert "…" not in out and "..." not in out
    assert "<details" in out


def test_a_short_note_is_not_folded():
    assert "<details" not in RENDER._decides("Q3 2026 results")


# --- the fold ---------------------------------------------------------------


def test_the_timeline_shows_ten_and_folds_the_archive(page, markup):
    """230 events is an archive, not a view."""
    assert len(page.events) > RENDER.TIMELINE_SHOWN
    section = markup.split('id="history"', 1)[1]
    shown = section.split('class="rest"', 1)[0]
    for event in page.events[:RENDER.TIMELINE_SHOWN]:
        assert event.title in shown or esc_in(event.title, shown)
    hidden = page.events[RENDER.TIMELINE_SHOWN:]
    folded = section.split('class="rest"', 1)[1]
    assert any(e.title in folded or esc_in(e.title, folded) for e in hidden)


def esc_in(text: str, blob: str) -> bool:
    import html as H
    return H.escape(text, quote=True) in blob


def test_the_queue_shows_the_single_action_items_and_folds_the_rest(page, markup):
    section = markup.split('id="queue"', 1)[1].split("</details>\n<details",
                                                     1)[0]
    head = section.split('class="rest"', 1)[0]
    one = [i for i in page.queue if i.actions == 1]
    rest = [i for i in page.queue if i.actions != 1]
    assert one and rest
    assert "One action each" in head
    for item in one:
        assert item.ticker in head


def test_everything_below_the_scan_is_behind_a_disclosure(markup):
    """The queue, the timeline, the shadow book and the per-name links are
    all one click away, and each summary says what is inside."""
    for anchor in ('id="queue"', 'id="history"', 'id="docs"'):
        assert f"<details {anchor}" in markup or f'<details id=' in markup
        head = markup.split(anchor, 1)[1][:400]
        assert "<summary>" in head


def test_the_page_uses_no_javascript_at_all(markup):
    """Disclosure is `details`/`summary`, which the browser gives free."""
    assert "<details" in markup and "<summary>" in markup
    for forbidden in ("<script", "javascript:", "onclick", "onload",
                      "ontoggle", "onchange"):
        assert forbidden not in markup.lower()


# --- colour ------------------------------------------------------------------


def test_one_accent_colour_and_it_means_one_thing(markup):
    """The accent appears in the top block and nowhere else. A second use
    teaches the reader it means "notable", which is how it stops meaning
    "this needs you"."""
    css = markup.split("<style>", 1)[1].split("</style>", 1)[0]
    uses = [line.strip() for line in css.splitlines()
            if "var(--accent)" in line]
    assert len(uses) == 1, uses
    assert ".attention.needed" in uses[0]


def test_the_page_declares_a_dark_scheme(markup):
    assert 'name="color-scheme" content="dark"' in markup
    css = markup.split("<style>", 1)[1].split("</style>", 1)[0]
    assert "--bg: #" in css and "background: var(--bg)" in css


def test_every_accented_item_carries_its_meaning_in_words(page, markup):
    """A status that is red must also say what it is."""
    if not page.attention:
        pytest.skip("nothing needs the owner on today's record")
    block = markup.split('class="attention', 1)[1].split("</section>", 1)[0]
    for item in page.attention:
        assert item.kind in block, item.kind


def test_the_page_is_readable_on_a_phone(markup):
    """Phone first: the base rules are the narrow ones and the media query
    ADDS to them, so a browser that never matches it still gets a layout."""
    assert 'name="viewport" content="width=device-width' in markup
    css = markup.split("<style>", 1)[1].split("</style>", 1)[0]
    assert "@media (min-width:" in css, "the layout is phone-first"
    assert re.search(r"max-width: \d+rem", css), "the page is not unbounded"


def test_the_card_grid_reflows_to_one_column(markup):
    """`minmax(min(20rem, 100%), 1fr)` is what keeps a 20rem minimum from
    overflowing a 360px phone: the track collapses to the viewport."""
    css = markup.split("<style>", 1)[1].split("</style>", 1)[0]
    grid = [line for line in css.splitlines()
            if "grid-template-columns: repeat(auto-fill" in line]
    assert grid, "the cards are not an auto-fill grid"
    assert "min(" in grid[0], grid[0]


# --- the footer --------------------------------------------------------------


def test_the_footer_says_when_and_from_which_run(page, markup):
    """A page generated by hand at noon on a machine whose timer died on
    Tuesday is a Tuesday page with today's timestamp on it."""
    foot = markup.split("<footer>", 1)[1]
    assert page.generated.isoformat(timespec="seconds") in foot
    if page.stamp.completion is not None:
        assert page.stamp.completion.finished.strftime("%Y-%m-%d %H:%M") in foot
        assert page.stamp.completion.as_of in foot
    else:
        assert DATA_MISSING in foot


def test_the_footer_never_claims_a_run_it_has_no_record_of(page):
    blind = O.RunStamp(None, "", None,
                       "no completed nightly run is on record")
    foot = RENDER.footer(replace(page, stamp=blind))
    assert DATA_MISSING in foot
    assert "no completed nightly run is on record" in foot


def test_the_footer_states_the_price_age_separately_from_the_run(page, markup):
    """A hand fetch moves the cache stamp without moving the run. Saying
    "prices come from the run of X" would be a claim about causation the
    page cannot check."""
    foot = markup.split("<footer>", 1)[1]
    if page.stamp.cache_written is not None:
        assert page.stamp.cache_written.strftime("%Y-%m-%d %H:%M") in foot
    assert page.settled.isoformat() in foot


def test_a_stale_run_is_named_in_the_footer(page):
    stale = O.RunStamp(page.stamp.completion,
                       "RUN CONTINUITY: no completed nightly run for 96h",
                       page.stamp.cache_written)
    assert "96h" in RENDER.footer(replace(page, stamp=stale))


def test_the_header_carries_the_generation_time_in_iso_8601(page, markup):
    """F1 limb (c) requirement 1: ISO 8601 with timezone, visible without
    scrolling. It sits in <body> before the first card, as a <time>."""
    head = markup.split("<body>", 1)[1].split("<h1>", 1)[0]
    when = page.generated.isoformat(timespec="seconds")
    assert f'<time datetime="{when}">{when}</time>' in head


def test_the_footer_first_sentence_carries_the_same_generation_time(page, markup):
    """ONE FACT, TWO PLACES: the header stamp and the footer's first
    sentence render the same ov.generated the same way."""
    foot = markup.split("<footer>", 1)[1]
    first = foot.split(".", 1)[0]
    when = page.generated.isoformat(timespec="seconds")
    assert first.startswith("<p>Page generated <b>")
    assert when in first


# --- nothing is written outside reports/ -----------------------------------


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    """TWO real generations and a census of the repository around them.

    One fixture rather than four tests, because a generation reads every
    store on disk and the point being tested -- that it writes one file and
    changes nothing else -- is the same point each time.
    """
    directory = tmp_path_factory.mktemp("overview")
    before = _snapshot(PROJECT_ROOT)
    first = write_overview(output=directory / "nested" / "a.html", now=NOW)
    second = write_overview(output=directory / "b.html", now=NOW)
    return first, second, before, _snapshot(PROJECT_ROOT)


def _snapshot(root: Path) -> dict[str, tuple[int, float]]:
    """Size and mtime of every file the page must not touch.

    `__pycache__` is excluded and nothing else is. Bytecode is not the
    record: CPython writes a `.pyc` the first time it imports a module,
    which under a full test run can land inside the window this fixture
    measures and has nothing to do with what the page wrote. Everything
    that IS the record -- the watchlist, the stores, the growth views, the
    run records, the rulings, the shadow book, the price cache, the
    database -- stays in scope.

    ONE KNOWN FALSE POSITIVE, and it is worth the census: the count is
    taken either side of a real generation, so EDITING THE REPOSITORY
    WHILE THE SUITE RUNS trips it. The failure names the file, so the
    cause is obvious when it happens; the alternative is a guarantee with
    a hole in it exactly where a bug would hide.
    """
    out: dict[str, tuple[int, float]] = {}
    for directory in ("config", "reference", "data", "vss", "tools", "tests"):
        base = root / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                stat = path.stat()
                out[str(path)] = (stat.st_size, stat.st_mtime_ns)
    return out


def test_generating_the_page_writes_nothing_outside_reports(generated):
    _, _, before, after = generated
    appeared = sorted(set(after) - set(before))
    vanished = sorted(set(before) - set(after))
    changed = sorted(k for k in before if k in after and before[k] != after[k])
    assert not (appeared or vanished or changed), (
        f"created: {appeared}; removed: {vanished}; modified: {changed}")


def test_the_output_must_be_an_html_file(tmp_path):
    with pytest.raises(ValueError):
        write_overview(output=tmp_path / "OVERVIEW.md", now=NOW)


def test_the_page_is_written_where_it_is_asked_for(generated):
    first, _, _, _ = generated
    assert first.name == "a.html" and first.parent.name == "nested"
    assert first.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


def test_two_generations_of_the_same_record_agree(generated):
    """The page holds no state. Same inputs, same bytes."""
    first, second, _, _ = generated
    assert first.read_bytes() == second.read_bytes()


# --- the nightly run -------------------------------------------------------


def test_a_scoped_run_does_not_write_the_page():
    """`--ticker` priced one name. A forty-name page built beside it would
    show the rest at whatever the cache last held, without saying so."""
    source = (PROJECT_ROOT / "vss" / "runner.py").read_text(encoding="utf-8")
    assert "if not resolved_filter and reports_dir == REPORTS_DIR:" in source


def test_a_failed_generation_never_fails_the_run():
    """The report on disk and the database row are the run's job and are
    already done when the page is built. A view of the record must not be
    able to fail the run that wrote the record."""
    source = (PROJECT_ROOT / "vss" / "runner.py").read_text(encoding="utf-8")
    hook = source.split("from .overview import write_overview", 1)[1][:600]
    assert "except Exception" in hook and "log.warning" in hook
    assert "raise" not in hook
