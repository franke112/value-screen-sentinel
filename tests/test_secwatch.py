"""`vss watch --sec` -- publication detection for US filers.

Built 2026-09-20 on the owner's instruction: notify-only, never touching
the store; 8-K Item 2.02 included, because "learning about the quarter days
late because the release is not a 10-Q defeats the purpose"; state keyed on
the accession number; same ntfy delivery, its own state namespace.
"""
import json
from dataclasses import dataclass
from pathlib import Path

from vss import secwatch as SW

REPO = Path(__file__).resolve().parents[1]
STAMP = "2026-09-20T12:00:00+00:00"


@dataclass
class Filing:
    form: str
    accession: str
    filed: str
    period_end: str = ""
    items: str = ""
    document: str = "x.htm"


TENQ = Filing("10-Q", "000082241626000036", "2026-07-22", "2026-06-30")
RELEASE = Filing("8-K", "000082241626000034", "2026-07-22", "2026-07-22", "2.02,9.01")
CREDIT = Filing("8-K", "000082241626000038", "2026-08-12", "2026-08-11", "1.01,2.03,9.01")
VOTE = Filing("8-K", "000082241626000026", "2026-05-01", "2026-04-29", "5.07")


# --- the filter ----------------------------------------------------------

def test_a_periodic_report_passes_on_its_form():
    assert SW.classify(TENQ, "PHM").passes


def test_the_earnings_release_passes_because_it_beats_the_10Q():
    d = SW.classify(RELEASE, "PHM")
    assert d.passes
    assert "2.02" in d.why and "before the 10-Q" in d.why


def test_every_other_8K_is_rejected_WITH_ITS_ITEM_NUMBER():
    """'An 8-K arrived' is not information; 'an 8-K Item 5.07 arrived' is."""
    for filing, item in ((CREDIT, "1.01"), (VOTE, "5.07")):
        d = SW.classify(filing, "PHM")
        assert not d.passes
        assert item in d.why and "not Item 2.02" in d.why


def test_a_form_this_does_not_watch_is_named_not_silently_dropped():
    d = SW.classify(Filing("4", "x", "2026-09-11"), "PHM")
    assert not d.passes and "4 is not a form this watches" in d.why


# --- the first run is a baseline ----------------------------------------

def _run(tmp_path, filings, **kw):
    state = tmp_path / "state.json"
    sent = {}

    def poster(lines, url=None):
        sent["lines"] = list(lines)
        return f"sent {len(lines)}"

    wl = kw.pop("watchlist_path", REPO / "config" / "watchlist.yaml")
    code, report = SW.run_secwatch(
        watchlist_path=wl, state_path=state, poster=poster, now=STAMP,
        fetch=lambda cik: filings, **kw)
    return code, report, state, sent


def test_the_first_run_records_a_baseline_and_reports_nothing(tmp_path):
    code, report, state, sent = _run(tmp_path, [TENQ, RELEASE, CREDIT])
    assert code == 0
    assert "PASSED -- 0" in report and "FIRST RUN" in report
    assert sent.get("lines") in (None, [])
    saved = json.loads(state.read_text())
    assert saved["sec"]["PHM"]["accessions"][:3] == [
        TENQ.accession, RELEASE.accession, CREDIT.accession]


def test_the_second_run_reports_only_what_is_new(tmp_path):
    _run(tmp_path, [CREDIT])                       # baseline holds the 8-K
    state = tmp_path / "state.json"
    sent = {}

    def poster(lines, url=None):
        sent["lines"] = list(lines)
        return "sent"

    code, report = SW.run_secwatch(
        watchlist_path=REPO / "config" / "watchlist.yaml", state_path=state,
        poster=poster, now=STAMP, fetch=lambda cik: [TENQ, RELEASE, CREDIT])
    assert code == 0
    assert "PASSED -- " in report
    lines = sent["lines"]
    assert any("10-Q" in l for l in lines) and any("Item 2.02" in l for l in lines)
    assert not any(CREDIT.filed in l and "1.01" in l for l in lines)


def test_state_is_keyed_on_the_accession_not_the_date(tmp_path):
    """EDGAR's same-day ordering is not guaranteed stable, so a cursor of
    one date would re-notify or skip."""
    _run(tmp_path, [TENQ, RELEASE])
    state = tmp_path / "state.json"
    before = json.loads(state.read_text())["sec"]["PHM"]["accessions"]
    sent = {}
    SW.run_secwatch(watchlist_path=REPO / "config" / "watchlist.yaml",
                    state_path=state, now=STAMP,
                    poster=lambda lines, url=None: sent.setdefault("lines", list(lines)),
                    fetch=lambda cik: [RELEASE, TENQ])     # same two, reordered
    assert sent.get("lines") in (None, [])                 # nothing re-notified
    assert set(json.loads(state.read_text())["sec"]["PHM"]["accessions"]) == set(before)


def test_it_keeps_its_own_namespace_and_leaves_the_nordic_cursor_alone(tmp_path):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"version": 1, "seen": {"LIAB.ST": {"last_id": 999}}}))
    SW.run_secwatch(watchlist_path=REPO / "config" / "watchlist.yaml",
                    state_path=state, send=False, now=STAMP,
                    fetch=lambda cik: [TENQ])
    saved = json.loads(state.read_text())
    assert saved["seen"]["LIAB.ST"]["last_id"] == 999     # untouched
    assert "PHM" in saved["sec"]                          # its own namespace


# --- notify only ---------------------------------------------------------

def test_it_writes_NEITHER_the_store_NOR_the_watchlist(tmp_path):
    watchlist = (REPO / "config" / "watchlist.yaml").read_bytes()
    stores = {p: p.read_bytes() for p in (REPO / "config" / "manual").glob("*.yaml")}
    _run(tmp_path, [TENQ, RELEASE])
    assert (REPO / "config" / "watchlist.yaml").read_bytes() == watchlist
    assert all(p.read_bytes() == raw for p, raw in stores.items())


def test_a_name_without_a_cik_is_reported_not_skipped(tmp_path):
    _, report, _, _ = _run(tmp_path, [TENQ])
    assert "NOT WATCHED" in report and "no cik" in report
    assert "B-1" in report            # the backlog item it belongs to


def test_the_rejected_table_is_printed_so_the_filter_can_be_argued_with(tmp_path):
    _run(tmp_path, [CREDIT])                                  # baseline
    state = tmp_path / "state.json"
    code, report = SW.run_secwatch(
        watchlist_path=REPO / "config" / "watchlist.yaml", state_path=state,
        send=False, now=STAMP, fetch=lambda cik: [CREDIT, VOTE, TENQ])
    assert "REJECTED" in report and "5.07" in report


def test_a_filer_with_more_filings_than_REMEMBER_is_quiet_after_the_baseline(tmp_path):
    """The first scheduled run (2026-10-05) reported 779 old filings as new:
    EDGAR lists hundreds per filer and the cursor kept forty. The same list
    fetched twice must report nothing the second time."""
    many = [Filing("10-Q", f"0000822416{i:08d}", "2020-01-01", "2019-12-31")
            for i in range(SW.REMEMBER + 60)]
    _run(tmp_path, many)                           # baseline
    state = tmp_path / "state.json"
    code, report = SW.run_secwatch(
        watchlist_path=REPO / "config" / "watchlist.yaml", state_path=state,
        poster=lambda lines, url=None: "sent", now=STAMP,
        fetch=lambda cik: many)
    assert code == 0
    assert "PASSED -- 0" in report


def test_a_HELD_name_is_watched():
    """CTSH became HELD on 2026-10-05 and dropped out of the SEC arm the
    same morning -- the one name the owner owns."""
    assert "HELD" in SW.SEC_WATCHED_STATUSES
    assert "CTSH" in [t for t, _cik, _s in SW.watched_filers()]

