"""E93: the weekly screen's change rule, its guard, and its silences.

The most important test in this file is the one that says a short run sends
NOTHING. A phantom "eight names left the top 10" from a throttled fetch would
cost the whole chain its credibility, and credibility is the only thing a
weekly pointer has.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from vss.refresh import RefreshError, assert_no_watchlist_write
from vss.screenwatch import (COVERAGE_TOLERANCE, ENTERED, JUMPED,
                             KEEP_SNAPSHOTS, LEFT, PROVENANCE_BACKFILL,
                             PROVENANCE_SCHEDULED, SECTION_RANKED, TOP_N,
                             UNRANKABLE, WATCH_N, Change, Coverage,
                             assess_coverage, baseline_is_genuine,
                             detect_changes, notification_lines, positions,
                             prune_snapshots, ranked_count, ranking_rows,
                             new_in_watch_band, render_screen_report,
                             weekly_message)
from vss.store import persist_ranking, previous_ranking, read_ranking

RUN_TS = datetime(2026, 9, 5, 8, 0).astimezone()
AS_OF = date(2026, 9, 5)


def rows(order, *, section=SECTION_RANKED, unrankable=()):
    """A stored ranking: `order` is the tickers in position order."""
    out = [{"ticker": t, "position": i, "section": section,
            "combined": 30 + i, "quality_rank": i, "ey_rank": 30,
            "operating_profitability": 0.2, "earnings_yield": 0.09,
            "quality_state": "ok", "ranked_count": len(order)}
           for i, t in enumerate(order, start=1)]
    out += [{"ticker": t, "position": None, "section": "unrankable",
             "combined": None, "quality_rank": None, "ey_rank": None,
             "operating_profitability": None, "earnings_yield": None,
             "quality_state": "no data", "ranked_count": len(order)}
            for t in unrankable]
    return out


TOP12 = [f"T{i:02d}" for i in range(1, 13)]      # T01..T12
WIDE = [f"T{i:02d}" for i in range(1, 26)]       # T01..T25


# --- THE ONE THAT MATTERS: a short run reports and sends nothing -----------


def test_a_throttled_fetch_makes_the_run_incomplete():
    """The DIRECT signal: the endpoint told us outright we did not get it all."""
    coverage = assess_coverage(rows(WIDE), rows(WIDE), throttled=3)
    assert coverage.short
    assert "THROTTLED" in coverage.reason
    assert "nothing to do with the market" in coverage.reason


def test_a_coverage_shortfall_makes_the_run_incomplete():
    before = rows([f"T{i:03d}" for i in range(200)])
    after = rows([f"T{i:03d}" for i in range(150)])      # 50 names vanished
    coverage = assess_coverage(before, after)
    assert coverage.short
    assert "150" in coverage.reason and "200" in coverage.reason


def test_ordinary_attrition_does_not_silence_a_real_move():
    """Two names out of 200 is a delisting, not a broken fetch."""
    before = rows([f"T{i:03d}" for i in range(200)])
    after = rows([f"T{i:03d}" for i in range(198)])
    assert not assess_coverage(before, after).short


def test_an_incomplete_run_computes_no_changes_and_sends_no_pointer(tmp_path):
    """E93: not 'computes them and withholds' -- it does not compute them.

    A number nobody may act on must not be printed beside numbers they may.
    """
    before = rows([f"T{i:03d}" for i in range(200)])
    # A throttled run in which the top 10 looks completely different.
    after = rows([f"X{i:03d}" for i in range(100)])
    coverage = assess_coverage(before, after, throttled=12)
    assert coverage.short

    # The run would have found a great many crossings had it been allowed to.
    would_have = detect_changes(before, after)
    assert len(would_have) > 5, "the fixture must be one that WOULD fire"

    report = render_screen_report(
        as_of=AS_OF, run_ts=RUN_TS, coverage=coverage,
        changes=[],                       # E93: none computed
        current=after, previous_as_of="2026-08-29")

    assert "RUN INCOMPLETE — NO CHANGE POINTER SENT" in report
    assert "credibility" in report
    # No crossing is named anywhere in it.
    for change in would_have:
        assert change.ticker not in report.split("## THE TOP")[0].split(
            "RUN INCOMPLETE")[1]
    assert "said only that the run was incomplete" in report


def test_the_first_run_is_not_short_it_simply_has_nothing_to_compare():
    coverage = assess_coverage([], rows(WIDE))
    assert not coverage.short
    assert detect_changes([], rows(WIDE)) == []


# --- the change rule -------------------------------------------------------


def test_entering_and_leaving_the_top_ten_both_fire():
    before = rows(TOP12)
    after = rows(["T11"] + TOP12[:9] + ["T10", "T12"])   # T11 in, T10 out
    changes = {(c.kind, c.ticker) for c in detect_changes(before, after)}
    assert (ENTERED, "T11") in changes
    assert (LEFT, "T10") in changes


def test_movement_inside_the_top_twenty_fires_nothing():
    """E11's finding in different clothes -- the ruling, not an omission."""
    before = rows(WIDE)
    # T12 and T18 swap; both stay outside the top 10, nothing crosses it.
    after = rows(WIDE[:11] + ["T18"] + WIDE[12:17] + ["T12"] + WIDE[18:])
    assert detect_changes(before, after) == []


def test_a_name_sliding_from_twelve_to_eighteen_fires_nothing():
    before = rows(WIDE)
    moved = [t for t in WIDE if t != "T12"]
    after = rows(moved[:17] + ["T12"] + moved[17:])
    assert detect_changes(before, after) == []


def test_a_one_step_jump_from_outside_twenty_is_its_own_kind():
    before = rows(WIDE)
    after = rows(["T25"] + [t for t in WIDE if t != "T25"])
    changes = detect_changes(before, after)
    jump = next(c for c in changes if c.ticker == "T25")
    assert jump.kind == JUMPED
    assert "outside 20" in jump.detail and "inside 10" in jump.detail


def test_a_name_entering_from_inside_twenty_is_an_ordinary_entry():
    before = rows(WIDE)
    after = rows(["T15"] + [t for t in WIDE if t != "T15"])
    entry = next(c for c in detect_changes(before, after) if c.ticker == "T15")
    assert entry.kind == ENTERED


def test_the_top_ten_is_position_not_combined_rank():
    """Ties in `combined` are broken alphabetically by ranking.py; position
    is what the boundary is drawn on, so it cannot wobble on a tie."""
    before = rows(WIDE)
    after = rows(WIDE)
    for row in after:                      # every combined identical
        row["combined"] = 48
    assert detect_changes(before, after) == []
    assert positions(after)["T01"] == 1 and positions(after)["T10"] == 10


# --- the three further events ---------------------------------------------


def test_an_entrant_already_on_the_watchlist_is_annotated():
    before, after = rows(TOP12), rows(["T11"] + TOP12[:9] + ["T10", "T12"])
    changes = detect_changes(before, after,
                             watchlist={"T11": "DROPPED"})
    entry = next(c for c in changes if c.ticker == "T11")
    assert entry.on_watchlist == "DROPPED"
    assert "[DROPPED on the watchlist]" in entry.line()


def test_a_previously_ranked_name_that_becomes_unrankable_fires():
    """A DATA event -- how a feed or tag-map breakage announces itself."""
    before = rows(WIDE)
    after = rows([t for t in WIDE if t != "T15"], unrankable=["T15"])
    change = next(c for c in detect_changes(before, after) if c.ticker == "T15")
    assert change.kind == UNRANKABLE
    assert "was #15" in change.detail


def test_the_data_event_is_not_limited_to_the_top_ten():
    """It does not announce itself politely at the top of the list."""
    before = rows(WIDE)
    after = rows([t for t in WIDE if t != "T24"], unrankable=["T24"])
    assert any(c.kind == UNRANKABLE and c.ticker == "T24"
               for c in detect_changes(before, after))


# --- the guard -------------------------------------------------------------


def test_the_watchlist_guard_stops_a_run_that_touched_it():
    with pytest.raises(RefreshError) as exc:
        assert_no_watchlist_write(b"tickers: []\n", b"tickers: [X]\n")
    assert "E92 VIOLATED" in str(exc.value)


def test_the_scheduled_unit_never_passes_write_pipeline():
    """E12: entering a name freezes Gate 1, and a clock may not do that."""
    unit = Path("deploy/vss-screen.service").read_text()
    exec_lines = [ln for ln in unit.splitlines() if ln.startswith("ExecStart=")]
    assert len(exec_lines) == 1
    assert "--weekly" in exec_lines[0]
    assert "--write-pipeline" not in exec_lines[0]
    # And config/ is not writable by the unit at all.
    rw = next(ln for ln in unit.splitlines() if ln.startswith("ReadWritePaths="))
    assert "/config" not in rw
    assert rw.endswith("/data %h/vss/reports")


def test_the_timer_fires_saturday_morning():
    timer = Path("deploy/vss-screen.timer").read_text()
    assert "OnCalendar=Sat *-*-* 08:00:00" in timer
    assert "Persistent=true" in timer


# --- storage and retention -------------------------------------------------


def test_a_ranking_round_trips_through_the_table(tmp_path):
    db = tmp_path / "vss.sqlite"
    persist_ranking(db, [dict(r, run_ts="t", as_of="2026-08-29",
                              snapshot_date="2026-08-28")
                         for r in rows(TOP12)])
    stored = read_ranking(db)
    assert [r["ticker"] for r in stored][:3] == ["T01", "T02", "T03"]
    assert ranked_count(stored) == 12


def test_previous_ranking_is_strictly_earlier(tmp_path):
    """So re-running a date never diffs a run against itself."""
    db = tmp_path / "vss.sqlite"
    persist_ranking(db, [dict(r, run_ts="a", as_of="2026-08-29") for r in rows(TOP12)])
    persist_ranking(db, [dict(r, run_ts="b", as_of="2026-09-05") for r in rows(TOP12)])
    assert previous_ranking(db, "2026-09-05")[0]["as_of"] == "2026-08-29"
    assert previous_ranking(db, "2026-08-29") == []


def test_pruning_keeps_the_last_four_and_touches_nothing_else(tmp_path):
    root = tmp_path / "screener_snapshots"
    for day in ("2026-08-01", "2026-08-08", "2026-08-15", "2026-08-22",
                "2026-08-29", "2026-09-05"):
        (root / day).mkdir(parents=True)
        (root / day / "snapshot.sqlite").write_text("x")
    (root / "notes.txt").write_text("not a snapshot")
    (root / "keep-me").mkdir()

    pruned = prune_snapshots(root, keep=KEEP_SNAPSHOTS)

    assert {p.name for p in pruned} == {"2026-08-01", "2026-08-08"}
    survivors = {p.name for p in root.iterdir()}
    assert "2026-09-05" in survivors and "2026-08-15" in survivors
    # Anything that is not a dated snapshot directory is left alone.
    assert "notes.txt" in survivors and "keep-me" in survivors


def test_a_dry_run_prune_deletes_nothing(tmp_path):
    root = tmp_path / "s"
    for day in ("2026-08-01", "2026-08-08", "2026-08-15", "2026-08-22",
                "2026-08-29"):
        (root / day).mkdir(parents=True)
    doomed = prune_snapshots(root, keep=4, dry_run=True)
    assert [p.name for p in doomed] == ["2026-08-01"]
    assert (root / "2026-08-01").exists()


# --- the report and the pointer -------------------------------------------


def test_no_change_says_so_and_explains_the_silence():
    report = render_screen_report(
        as_of=AS_OF, run_ts=RUN_TS,
        coverage=Coverage(False, "", 200, 200), changes=[],
        current=rows(WIDE), previous_as_of="2026-08-29")
    assert "## NO CHANGE" in report
    assert f"INSIDE the top {WATCH_N} is not reported" in report
    assert "is not an omission" in report


def test_the_report_states_the_ruling_in_its_own_words():
    report = render_screen_report(
        as_of=AS_OF, run_ts=RUN_TS, coverage=Coverage(False, "", 1, 1),
        changes=[Change(ENTERED, "T11", "#11 → #7")],
        current=rows(TOP12), previous_as_of="2026-08-29")
    assert "does not write `config/watchlist.yaml`" in report
    assert "freezes Gate 1" in report
    assert "no name was entered as PIPELINE" in report


def test_the_pointer_is_short_and_names_the_report():
    changes = [Change(ENTERED, f"T{i}", "#11 → #7") for i in range(9)]
    lines = notification_lines(changes, Path("reports/SCREEN-2026-09-05.md"))
    assert len(lines) == 8               # 6 changes + "and 3 more" + the path
    assert "and 3 more" in lines[-2]
    assert lines[-1] == "reports/SCREEN-2026-09-05.md"


def test_ranking_rows_number_positions_from_one():
    class S:
        def __init__(self, t):
            self.ticker, self.operating_profitability = t, 0.2
            self.earnings_yield, self.quality_state = 0.09, "ok"

    class R:
        def __init__(self, t, i):
            self.scored, self.quality_rank = S(t), i
            self.ey_rank, self.combined = 30, 30 + i

        @property
        def ticker(self):
            return self.scored.ticker

    class Result:
        main = [R("A", 1), R("B", 2)]
        yield_only: list = []
        unrankable: list = []
        stale: list = []

    out = ranking_rows(Result(), run_ts=RUN_TS, as_of=AS_OF,
                       snapshot_date=date(2026, 9, 4))
    assert [r["position"] for r in out] == [1, 2]
    assert out[0]["snapshot_date"] == "2026-09-04"
    assert all(r["section"] == SECTION_RANKED for r in out)


def test_the_weekly_run_isolates_runs_root(monkeypatch, tmp_path):
    """A caller that isolates the snapshot root must isolate the ranking
    output too.

    `rank()` writes `ranking.csv` under `runs_root`, which defaults to the
    real `data/screener_runs`. A smoke run on 2026-08-31 pointed at a scratch
    snapshot root but left runs_root alone and overwrote the real 2026-08-29
    ranking with its own six-ticker result. This pins the fix.
    """
    import vss.screen as screen_mod
    from vss import screenwatch

    seen = {}

    class Result:
        main = yield_only = unrankable = stale = []

    class Upstream:
        class upstream:
            snapshot_date = date(2026, 9, 4)

    class Ranked:
        result, report, upstream = Result(), "", Upstream()

    monkeypatch.setattr(screen_mod, "snapshot_only", lambda **kw: None)
    monkeypatch.setattr(screen_mod, "fetch_fundamentals",
                        lambda **kw: type("F", (), {"outcome": type(
                            "O", (), {"records": []})()})())

    def fake_rank(**kw):
        seen.update(kw)
        return Ranked()

    monkeypatch.setattr(screen_mod, "rank", fake_rank)

    screenwatch.run_weekly(
        as_of=AS_OF, now=RUN_TS, db_path=tmp_path / "db.sqlite",
        reports_dir=tmp_path / "reports", snapshot_root=tmp_path / "snaps",
        runs_root=tmp_path / "runs", notify=False)

    assert seen["runs_root"] == tmp_path / "runs"
    assert "write_pipeline" not in seen        # E93: never passed


def test_an_unrankable_name_stores_with_a_null_position(tmp_path):
    """The first cut of the schema had `position INTEGER NOT NULL` and the
    backfill died on it. A name without a position is the whole mechanism of
    E93's data event, so the column must accept one."""
    db = tmp_path / "vss.sqlite"
    persist_ranking(db, [dict(r, run_ts="t", as_of="2026-08-29")
                         for r in rows(["A", "B"], unrankable=["C"])])
    stored = read_ranking(db, "2026-08-29")
    assert len(stored) == 3
    null_row = next(r for r in stored if r["ticker"] == "C")
    assert null_row["position"] is None
    assert null_row["section"] == "unrankable"
    # And it sorts last, after the positioned rows.
    assert [r["ticker"] for r in stored] == ["A", "B", "C"]


def test_the_migration_makes_an_existing_not_null_column_nullable(tmp_path):
    """A database created by the first cut must survive the fix."""
    import sqlite3

    from vss.store import connect

    db = tmp_path / "old.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE screen_rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_ts TEXT NOT NULL, as_of TEXT NOT NULL, snapshot_date TEXT,
            ticker TEXT NOT NULL, position INTEGER NOT NULL,
            section TEXT NOT NULL, combined INTEGER, quality_rank INTEGER,
            ey_rank INTEGER, operating_profitability REAL,
            earnings_yield REAL, quality_state TEXT, coverage_short INTEGER,
            ranked_count INTEGER, fx_source TEXT);
        INSERT INTO screen_rankings (run_ts, as_of, ticker, position, section)
        VALUES ('t', '2026-08-22', 'KEEP', 1, 'ranked');
    """)
    conn.commit()
    conn.close()

    connect(db).close()                      # runs the migration

    persist_ranking(db, [dict(r, run_ts="t", as_of="2026-08-29")
                         for r in rows(["A"], unrankable=["C"])])
    stored = read_ranking(db, "2026-08-29")
    assert any(r["position"] is None for r in stored)
    # The pre-existing row survived the rebuild.
    assert read_ranking(db, "2026-08-22")[0]["ticker"] == "KEEP"


# --- a diff is only notified when BOTH sides are genuine runs -------------


def scheduled(order, **kw):
    kw.setdefault("tiers", "A")
    return [dict(r, provenance=PROVENANCE_SCHEDULED, **kw) for r in rows(order)]


def backfilled(order, **kw):
    return [dict(r, provenance=PROVENANCE_BACKFILL, **kw) for r in rows(order)]


def test_a_scheduled_baseline_is_genuine():
    assert baseline_is_genuine(scheduled(TOP12))


def test_a_backfilled_baseline_is_not_genuine():
    assert not baseline_is_genuine(backfilled(TOP12))


def test_a_baseline_with_no_recorded_provenance_is_not_genuine():
    """NULL is read as 'cannot be vouched for', which is the safe direction:
    a baseline nobody can vouch for does not license a notification."""
    assert not baseline_is_genuine(rows(TOP12))          # no provenance key


def test_an_empty_baseline_is_not_genuine():
    assert not baseline_is_genuine([])


def test_the_first_run_against_a_regenerated_baseline_sends_no_pointer(
        monkeypatch, tmp_path):
    """The 2026-09-05 case, end to end: it reports and stores, and notifies
    nothing, because its baseline was regenerated under later code."""
    import vss.screen as screen_mod
    from vss import screenwatch

    posted = []
    # run_weekly imports post_needs_owner from .refresh INSIDE the function,
    # so the name that actually gets called is vss.refresh's. Patching it on
    # screenwatch would never bind and the assertion below would be vacuous.
    monkeypatch.setattr("vss.refresh.post_needs_owner",
                        lambda *a, **k: posted.append(a) or "sent")

    db = tmp_path / "vss.sqlite"
    # A BACKFILLED baseline, exactly as 2026-08-29 sits on disk.
    persist_ranking(db, [dict(r, run_ts="t", as_of="2026-08-29")
                         for r in backfilled(TOP12)])

    class S:
        def __init__(self, t):
            self.ticker, self.operating_profitability = t, 0.2
            self.earnings_yield, self.quality_state = 0.09, "ok"

    class R:
        def __init__(self, t, i):
            self.scored, self.quality_rank, self.ey_rank = S(t), i, 30
            self.combined = 30 + i

        @property
        def ticker(self):
            return self.scored.ticker

    # T11 enters the top 10 -- a change that WOULD be notified normally.
    order = ["T11"] + TOP12[:9] + ["T10", "T12"]

    class Result:
        main = [R(t, i) for i, t in enumerate(order, start=1)]
        yield_only = unrankable = stale = []

    class Upstream:
        class upstream:
            snapshot_date = date(2026, 9, 4)

    class Ranked:
        result, report, upstream = Result(), "", Upstream()

    monkeypatch.setattr(screen_mod, "snapshot_only", lambda **kw: None)
    monkeypatch.setattr(screen_mod, "fetch_fundamentals",
                        lambda **kw: type("F", (), {"outcome": type(
                            "O", (), {"records": []})()})())
    monkeypatch.setattr(screen_mod, "rank", lambda **kw: Ranked())

    run = screenwatch.run_weekly(
        as_of=date(2026, 9, 5), now=RUN_TS, db_path=db,
        reports_dir=tmp_path / "reports", snapshot_root=tmp_path / "snaps",
        runs_root=tmp_path / "runs", notify=True)

    # The change WAS found and IS reported...
    assert any(c.ticker == "T11" for c in run.changes)
    assert "T11" in run.report
    # ...and the pointer was withheld, with the reason. E116: the status
    # line still goes out, and it names no name.
    assert not run.genuine_baseline
    assert len(posted) == 1
    assert not any("T11" in line for line in posted[0][0])
    assert any("Comparison withheld" in line for line in posted[0][0])
    assert "SUPPRESSED" in run.notified
    assert "not produced by a scheduled run" in run.notified
    assert "NOT STRUCK THE SAME WAY" in run.report
    assert "carried only the run's status" in run.report
    assert "d171724" in run.report

    # And this run stores itself as SCHEDULED, so the NEXT one notifies.
    stored = read_ranking(db, "2026-09-05")
    assert stored and all(r["provenance"] == PROVENANCE_SCHEDULED
                          for r in stored)
    assert baseline_is_genuine(stored)


# --- the comparison basis, generalised (owner, 2026-09-01) ---------------
#
# "Mark the ranking's provenance on a tier change so the next diff refuses to
# compare across it, rather than me remembering to treat one Saturday as a
# baseline. Same rule as the seeded-baseline case; make it general."


from vss import screenwatch  # noqa: E402  -- the module handle, beside the names


def test_two_runs_struck_the_same_way_are_comparable():
    assert screenwatch.basis_mismatches(scheduled(TOP12), scheduled(TOP12)) == []


def test_a_tier_change_refuses_the_comparison():
    """The 2026-09-05 widening. Nothing about GDDY changed when it went from
    #14 to #21 on 2026-08-31; the field it was placed in did."""
    before = scheduled(TOP12, tiers="A")
    after = scheduled(TOP12, tiers="A,B")
    reasons = screenwatch.basis_mismatches(before, after)
    assert len(reasons) == 1
    assert "the universe changed" in reasons[0]
    assert "`A`" in reasons[0] and "`A,B`" in reasons[0]
    assert "TIER CHANGE" in reasons[0]


def test_a_tier_set_the_baseline_never_recorded_refuses_too():
    """NULL is UNKNOWN, never 'the same as ours'. The safe direction."""
    before = [dict(r, tiers=None) for r in scheduled(TOP12)]
    reasons = screenwatch.basis_mismatches(before, scheduled(TOP12, tiers="A"))
    assert reasons and "unrecorded" in reasons[0]


def _tiny_result():
    class S:
        def __init__(self, t):
            self.ticker, self.operating_profitability = t, 0.2
            self.earnings_yield, self.quality_state = 0.09, "ok"

    class R:
        def __init__(self, t, i):
            self.scored, self.quality_rank = S(t), i
            self.ey_rank, self.combined = 30, 30 + i

        @property
        def ticker(self):
            return self.scored.ticker

    class Result:
        main = [R("A", 1), R("B", 2)]
        yield_only: list = []
        unrankable: list = []
        stale: list = []

    return Result()


def test_the_tier_order_is_not_a_tier_change():
    """`--tier B --tier A` and `--tier A --tier B` are the same run."""
    rows_ab = ranking_rows(_tiny_result(), run_ts=RUN_TS, as_of=AS_OF,
                           snapshot_date=None, tiers=("b", "A"))
    rows_ba = ranking_rows(_tiny_result(), run_ts=RUN_TS, as_of=AS_OF,
                           snapshot_date=None, tiers=("A", "B"))
    assert rows_ab[0]["tiers"] == "A,B" == rows_ba[0]["tiers"]
    assert screenwatch.basis_mismatches(rows_ab, rows_ba) == []


def test_a_run_that_records_no_tiers_writes_null_not_an_empty_string():
    out = ranking_rows(_tiny_result(), run_ts=RUN_TS, as_of=AS_OF,
                       snapshot_date=None)
    assert out[0]["tiers"] is None


def test_both_grounds_are_reported_together_not_one_at_a_time():
    before = backfilled(TOP12, tiers="A")
    after = scheduled(TOP12, tiers="A,B")
    reasons = screenwatch.basis_mismatches(before, after)
    assert len(reasons) == 2
    assert any("scheduled run" in r for r in reasons)
    assert any("universe changed" in r for r in reasons)


def test_the_rule_stops_applying_by_itself():
    """Two consecutive runs struck the same way, and it is silent again --
    with nobody having remembered to do anything."""
    week1 = scheduled(TOP12, tiers="A")            # the last tier-A Saturday
    week2 = scheduled(TOP12, tiers="A,B")          # the widening
    week3 = scheduled(TOP12, tiers="A,B")          # the one after it
    assert screenwatch.basis_mismatches(week1, week2)      # refused
    assert screenwatch.basis_mismatches(week2, week3) == []  # and done


def test_a_refused_comparison_still_reports_the_changes():
    """The pointer is withheld; the reading is not. A number nobody may act
    on is still a number worth the owner's eye -- E93's own distinction."""
    report = screenwatch.render_screen_report(
        as_of=date(2026, 9, 5), run_ts=RUN_TS,
        coverage=Coverage(False, previous_ranked=12, current_ranked=12),
        changes=[], current=scheduled(TOP12, tiers="A,B"),
        previous_as_of="2026-08-29", genuine_baseline=True,
        basis_reasons=["the universe changed: the baseline was struck on "
                       "tiers `A` and this run on `A,B`"])
    assert "NOT STRUCK THE SAME WAY" in report
    assert "carried only the run's status" in report
    assert "nobody has to remember anything" in report
    # The regeneration paragraph belongs to the PROVENANCE clause and must
    # not print when a tier change is what fired.
    assert "d171724" not in report


def test_nothing_expires_on_a_date():
    """The rule is about the baseline, not the calendar: a run in 2027 with a
    backfilled baseline is still suppressed, and 2026-09-12 is not special."""
    assert not baseline_is_genuine(backfilled(TOP12))
    assert baseline_is_genuine(scheduled(TOP12))


def test_a_genuine_baseline_reports_no_suppression_banner():
    report = render_screen_report(
        as_of=AS_OF, run_ts=RUN_TS, coverage=Coverage(False, "", 12, 12),
        changes=[Change(ENTERED, "T11", "#11 → #7")], current=rows(TOP12),
        previous_as_of="2026-09-05", genuine_baseline=True,
        baseline_provenance=PROVENANCE_SCHEDULED)
    assert "REGENERATED BASELINE" not in report
    assert "CHANGES — 1" in report


def test_ranking_rows_stamp_scheduled_by_default():
    class Result:
        main = yield_only = unrankable = stale = []

    out = ranking_rows(Result(), run_ts=RUN_TS, as_of=AS_OF,
                       snapshot_date=None)
    assert out == []
    # and with one row:
    class S:
        ticker, operating_profitability = "A", 0.2
        earnings_yield, quality_state = 0.09, "ok"

    class R:
        scored, quality_rank, ey_rank, combined = S(), 1, 2, 3
        ticker = "A"

    class Result2:
        main = [R()]
        yield_only = unrankable = stale = []

    out = ranking_rows(Result2(), run_ts=RUN_TS, as_of=AS_OF, snapshot_date=None)
    assert out[0]["provenance"] == PROVENANCE_SCHEDULED


def test_a_genuine_baseline_DOES_send_the_pointer(monkeypatch, tmp_path):
    """The control for the test above: with the patch bound correctly and a
    scheduled baseline, the same change DOES go out. Without this, that test
    could pass because nothing was ever wired up."""
    import vss.screen as screen_mod
    from vss import screenwatch

    posted = []
    monkeypatch.setattr("vss.refresh.post_needs_owner",
                        lambda lines, **k: posted.append(list(lines)) or "sent")

    db = tmp_path / "vss.sqlite"
    persist_ranking(db, [dict(r, run_ts="t", as_of="2026-09-05")
                         for r in scheduled(TOP12)])

    class S:
        def __init__(self, t):
            self.ticker, self.operating_profitability = t, 0.2
            self.earnings_yield, self.quality_state = 0.09, "ok"

    class R:
        def __init__(self, t, i):
            self.scored, self.quality_rank, self.ey_rank = S(t), i, 30
            self.combined = 30 + i

        @property
        def ticker(self):
            return self.scored.ticker

    order = ["T11"] + TOP12[:9] + ["T10", "T12"]

    class Result:
        main = [R(t, i) for i, t in enumerate(order, start=1)]
        yield_only = unrankable = stale = []

    class Upstream:
        class upstream:
            snapshot_date = date(2026, 9, 11)

    class Ranked:
        result, report, upstream = Result(), "", Upstream()

    monkeypatch.setattr(screen_mod, "snapshot_only", lambda **kw: None)
    monkeypatch.setattr(screen_mod, "fetch_fundamentals",
                        lambda **kw: type("F", (), {"outcome": type(
                            "O", (), {"records": []})()})())
    monkeypatch.setattr(screen_mod, "rank", lambda **kw: Ranked())

    run = screenwatch.run_weekly(
        as_of=date(2026, 9, 12), now=RUN_TS, db_path=db,
        reports_dir=tmp_path / "reports", snapshot_root=tmp_path / "snaps",
        runs_root=tmp_path / "runs", notify=True)

    assert run.genuine_baseline
    assert run.notified == "sent"
    assert len(posted) == 1
    assert any("T11" in line for line in posted[0])
    assert "REGENERATED BASELINE" not in run.report


# --- E116: a status line every Saturday, plus names new to the top 20 -----


def test_new_in_the_top_20_names_only_what_was_outside_it_last_run():
    before = rows(TOP12 + [f"U{i:02d}" for i in range(13, 26)])   # U13..U25
    # U21 comes in at #15, U25 at #3; U13 moves inside the band and is NOT new.
    order = TOP12[:2] + ["U25"] + TOP12[2:] + ["U13", "U21"]
    got = new_in_watch_band(before, rows(order))
    assert got == [("U25", 3), ("U21", 15)]


def test_a_name_E93_already_carries_is_not_repeated():
    before = rows(TOP12 + [f"U{i:02d}" for i in range(13, 26)])
    order = ["U25"] + TOP12 + ["U21"]
    changes = [Change(JUMPED, "U25", "was #25, now #1")]
    assert new_in_watch_band(before, rows(order), changes=changes) == [("U21", 14)]


def test_the_ok_message_carries_e93_changes_then_the_top_20_line():
    title, lines = weekly_message(
        as_of=AS_OF, coverage=Coverage(False, current_ranked=216),
        changes=[Change(ENTERED, "BRO", "#14 → #8")],
        also_new=[("AON", 17), ("FOXA", 19)], basis_reasons=[],
        first_run=False, report=Path("reports/SCREEN-2026-09-05.md"))
    assert title == "vss weekly screen 2026-09-05: OK"
    assert lines == ["Ranked 216.", "ENTERED TOP 10: BRO — #14 → #8",
                     "Also new in top 20: AON #17, FOXA #19",
                     "reports/SCREEN-2026-09-05.md"]


def test_a_quiet_week_still_says_the_run_worked():
    title, lines = weekly_message(
        as_of=AS_OF, coverage=Coverage(False, current_ranked=216), changes=[],
        also_new=[], basis_reasons=[], first_run=False, report=Path("r.md"))
    assert title.endswith(": OK")
    assert "Nothing new in the top 20." in lines


def test_an_incomplete_run_says_so_and_names_no_name():
    title, lines = weekly_message(
        as_of=AS_OF, coverage=Coverage(True, "3 ticker(s) were THROTTLED"),
        changes=[Change(ENTERED, "BRO", "#14 → #8")], also_new=[("AON", 17)],
        basis_reasons=[], first_run=False, report=Path("r.md"))
    assert title.endswith(": INCOMPLETE")
    assert not any("BRO" in l or "AON" in l for l in lines)
