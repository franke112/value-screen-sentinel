"""A run that got nothing is not a run that worked (D2), and a component
that failed is not a component with nothing to say (D1).

CODE-REVIEW-2026-09-01, findings D2 and D1. Both are the same shape — a
failure that is indistinguishable from silence — arriving in two places, and
both were inside the module built the week before to close exactly that.

D2. `runner.run` recorded PRICED coverage with a comment explaining why row
count would not do, and nothing read the column. A night on which every fetch
failed exited 0, recorded `completed = 1` with `covered = 0`, reset the
72-hour clock, and fired `ExecStartPost=` — which tells healthchecks.io the
run succeeded, and healthchecks alarms on a ping's ABSENCE.

D1. `runner.run` wraps the E97 watcher and the E92 pointer so neither can
cost the report, then set the result to `[]`; `report.render` gated both on
truthiness. A watcher broken for a month rendered a report containing no
occurrence of the string `E97` anywhere.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from vss import heartbeat as HB
from vss import report as REP
from vss import runner as R

AS_OF = date(2026, 9, 1)
RUN_TS = datetime(2026, 9, 1, 22, 30).astimezone()


# --- the judgement itself --------------------------------------------------


def test_a_full_run_is_not_short():
    assert not HB.assess_coverage(expected=22, covered=22).short


def test_one_missing_name_of_twenty_two_is_not_short():
    """0.90 on 22 names: ONE may go dark without a finding. A single
    delisting must not page nightly -- that is how a pointer gets muted."""
    assert not HB.assess_coverage(expected=22, covered=21).short


def test_two_missing_names_of_twenty_two_is_still_inside_the_floor():
    """90.9%. The floor tolerates two, which is the loose end of the trade:
    a delisting and a renamed ticker in one week must not page nightly."""
    assert not HB.assess_coverage(expected=22, covered=20).short


def test_three_missing_names_of_twenty_two_IS_short():
    verdict = HB.assess_coverage(expected=22, covered=19)
    assert verdict.short
    assert "below the 90% floor" in verdict.reason


def test_pricing_NOTHING_is_short_at_any_floor():
    """The case the whole finding was about, and the one that needs no
    threshold argument: a run that reached its end and priced nothing."""
    verdict = HB.assess_coverage(expected=22, covered=0, floor=0.0)
    assert verdict.short
    assert "NOTHING WAS PRICED" in verdict.reason


def test_an_empty_watchlist_is_not_short():
    """It covered everything asked of it. Inventing a finding here would be
    the phantom the incomplete-run clause exists to prevent."""
    assert not HB.assess_coverage(expected=0, covered=0).short


def test_the_floor_is_below_every_run_on_record():
    """MEASURED, not chosen blind: the thirteen full nightly runs of
    2026-08-22 to 2026-08-31 priced 100% with zero fetch errors, every one.
    A floor above any of them would fire on history."""
    assert HB.NIGHTLY_COVERAGE_FLOOR < 1.0
    assert not HB.assess_coverage(expected=7, covered=7).short
    assert not HB.assess_coverage(expected=22, covered=22).short


# --- a short run does not reset the clock ---------------------------------


def _record(db: Path, *, covered: int, expected: int, short: bool,
            finished: datetime, kind: str = HB.KIND_NIGHTLY):
    row = HB.begin(db, kind=kind, started_at=finished - timedelta(minutes=5),
                   as_of=finished.date())
    HB.finish(db, row, finished_at=finished, expected=expected,
              covered=covered, errors=0, short=short, detail="test")
    return row


def test_a_short_run_does_not_reset_the_staleness_clock(tmp_path: Path):
    """**THE ONE THAT MATTERS FOR D2.** Four nights of runs that priced
    nothing must read as four nights without a run, because that is what
    they are. Before the fix each of them reset the clock."""
    db = tmp_path / "vss.sqlite"
    now = datetime(2026, 9, 5, 9, 30).astimezone()
    _record(db, covered=22, expected=22, short=False,
            finished=now - timedelta(hours=100))
    for hours in (76, 52, 28, 4):
        _record(db, covered=0, expected=22, short=True,
                finished=now - timedelta(hours=hours))

    last = HB.last_completion(db, kind=HB.KIND_NIGHTLY)
    assert last is not None and not last.short
    assert last.covered == 22, "a short run was allowed to be the last one"

    lines = HB.report_lines(db, now=now, kind=HB.KIND_NIGHTLY)
    assert any("no completed nightly run for" in line for line in lines)
    # Three of the four are inside the 72-hour window the switch reports on;
    # the fourth is older than it, and the staleness line above covers it.
    assert sum("RUN COVERAGE" in line for line in lines) == 3
    assert any("did NOT reset the staleness clock" in line for line in lines)


def test_a_full_run_after_short_ones_resets_the_clock(tmp_path: Path):
    """The clock restarts, and the short night is STILL reported while it is
    inside the window -- the same shape `crash_lines` takes, and for the same
    reason: the pointer that should have gone out that night may not have."""
    db = tmp_path / "vss.sqlite"
    now = datetime(2026, 9, 5, 9, 30).astimezone()
    _record(db, covered=0, expected=22, short=True,
            finished=now - timedelta(hours=30))
    _record(db, covered=22, expected=22, short=False,
            finished=now - timedelta(hours=4))

    lines = HB.report_lines(db, now=now, kind=HB.KIND_NIGHTLY)
    assert not any("no completed nightly run" in line for line in lines)
    assert sum("RUN COVERAGE" in line for line in lines) == 1


def test_once_the_short_night_ages_out_the_switch_is_silent(tmp_path: Path):
    db = tmp_path / "vss.sqlite"
    now = datetime(2026, 9, 5, 9, 30).astimezone()
    _record(db, covered=0, expected=22, short=True,
            finished=now - timedelta(hours=100))
    _record(db, covered=22, expected=22, short=False,
            finished=now - timedelta(hours=4))
    assert HB.report_lines(db, now=now, kind=HB.KIND_NIGHTLY) == []


def test_a_short_run_is_kept_apart_from_a_crashed_one(tmp_path: Path):
    """THREE STATES. `completed = 0` is a run that DIED; `short = 1` is a run
    that ran to the end and got nothing. Folding either into the other loses
    the distinction the switch exists to make."""
    db = tmp_path / "vss.sqlite"
    now = datetime(2026, 9, 5, 9, 30).astimezone()
    HB.begin(db, kind=HB.KIND_NIGHTLY, started_at=now - timedelta(hours=20),
             as_of=now.date())                       # died: never finished
    _record(db, covered=0, expected=22, short=True,
            finished=now - timedelta(hours=4))

    deaths = HB.died_since(db, since=now - timedelta(hours=72))
    shorts = HB.short_runs(db, since=now - timedelta(hours=72))
    assert len(deaths) == 1 and len(shorts) == 1
    assert deaths[0].id != shorts[0].id
    assert "never reached its end" in HB.crash_lines(deaths)[0]
    assert "reached its end and" in HB.short_lines(shorts)[0]


# --- 2026-09-19: a crash a later full run recovered is not re-posted -------


def test_a_crash_recovered_by_a_later_full_run_is_not_reported(tmp_path: Path):
    """The weekly screen was OOM-killed on 09-17 and 09-19 and re-run by hand
    both times. Each re-run completed, yet the dead rows were posted to the
    phone every morning for the whole 240-hour window."""
    db = tmp_path / "vss.sqlite"
    now = datetime(2026, 9, 19, 9, 34).astimezone()
    HB.begin(db, kind=HB.KIND_WEEKLY, started_at=now - timedelta(minutes=90),
             as_of=now.date())                       # OOM-killed
    _record(db, covered=2011, expected=2011, short=False, kind=HB.KIND_WEEKLY,
            finished=now - timedelta(minutes=37))    # the re-run

    assert HB.died_since(db, since=now - timedelta(hours=240),
                         kind=HB.KIND_WEEKLY) == []
    assert HB.report_lines(db, now=now, kind=HB.KIND_WEEKLY,
                           threshold_hours=240) == []


def test_a_crash_with_no_full_run_after_it_is_still_reported(tmp_path: Path):
    """A full run BEFORE the crash, or a SHORT run after it, recovers
    nothing: the crash stays on the phone."""
    db = tmp_path / "vss.sqlite"
    now = datetime(2026, 9, 19, 9, 34).astimezone()
    _record(db, covered=2011, expected=2011, short=False, kind=HB.KIND_WEEKLY,
            finished=now - timedelta(hours=48))
    HB.begin(db, kind=HB.KIND_WEEKLY, started_at=now - timedelta(minutes=90),
             as_of=now.date())
    _record(db, covered=0, expected=2011, short=True, kind=HB.KIND_WEEKLY,
            finished=now - timedelta(minutes=37))

    deaths = HB.died_since(db, since=now - timedelta(hours=240),
                           kind=HB.KIND_WEEKLY)
    assert len(deaths) == 1


def test_another_kinds_success_does_not_recover_a_crash(tmp_path: Path):
    db = tmp_path / "vss.sqlite"
    now = datetime(2026, 9, 19, 9, 34).astimezone()
    HB.begin(db, kind=HB.KIND_WEEKLY, started_at=now - timedelta(hours=12),
             as_of=now.date())
    _record(db, covered=22, expected=22, short=False,
            finished=now - timedelta(hours=1))       # a nightly

    assert len(HB.died_since(db, since=now - timedelta(hours=240),
                             kind=HB.KIND_WEEKLY)) == 1


# --- D6: a crash is reported once, not twice, and only under its own kind --


def test_a_nightly_crash_is_not_reported_by_the_weekly_leg(tmp_path: Path):
    """`died_since` had no `kind` filter, so `checkin` -- which calls
    `report_lines` twice -- posted every crash TWICE, and the weekly pass's
    240-hour window re-posted it daily for ten days."""
    db = tmp_path / "vss.sqlite"
    now = datetime(2026, 9, 5, 9, 30).astimezone()
    HB.begin(db, kind=HB.KIND_NIGHTLY, started_at=now - timedelta(hours=20),
             as_of=now.date())

    assert len(HB.died_since(db, since=now - timedelta(hours=72),
                             kind=HB.KIND_NIGHTLY)) == 1
    assert HB.died_since(db, since=now - timedelta(hours=72),
                         kind=HB.KIND_WEEKLY) == []

    result = HB.checkin(db, now=now, notify=False,
                        runner=lambda argv, **kw: type("P", (), {
                            "returncode": 0,
                            "stdout": "enabled" if argv[2] == "is-enabled"
                                      else "active"})())
    crashes = [line for line in result.lines if "never reached its end" in line]
    assert len(crashes) == 1, f"reported {len(crashes)} times: {result.lines}"


# --- the switch failing is itself a finding, never silence ----------------


def test_a_switch_that_cannot_be_read_says_so_rather_than_returning_nothing(
        tmp_path: Path, monkeypatch):
    """EMPTY MEANS HEALTHY in `report_lines`, so swallowing an exception to
    `[]` told the reader the opposite of what had happened."""
    db = tmp_path / "vss.sqlite"
    _record(db, covered=22, expected=22, short=False,
            finished=datetime(2026, 9, 1, 22, 30).astimezone())

    def boom(*args, **kwargs):
        raise sqlite_error()

    def sqlite_error():
        return RuntimeError("database disk image is malformed")

    monkeypatch.setattr(HB, "last_completion", boom)
    lines = HB.report_lines(db, now=RUN_TS, kind=HB.KIND_NIGHTLY)
    assert lines, "a broken switch reported as a healthy one"
    assert "THE SWITCH ITSELF COULD NOT BE READ" in lines[0]
    assert "DATA MISSING" in lines[0]


# --- the report says it --------------------------------------------------


def test_the_report_carries_a_SHORT_banner_and_says_what_follows_from_it():
    out = REP.render([], run_ts=RUN_TS, as_of=AS_OF,
                     coverage=HB.assess_coverage(expected=22, covered=0))
    assert "## RUN COVERAGE — SHORT" in out
    assert "NOTHING WAS PRICED" in out
    assert "did NOT reset the staleness clock" in out
    assert "no healthcheck ping" in out


def test_a_healthy_run_gets_no_coverage_banner():
    out = REP.render([], run_ts=RUN_TS, as_of=AS_OF,
                     coverage=HB.assess_coverage(expected=22, covered=22))
    assert "RUN COVERAGE" not in out


# --- D1: a component that failed is not a component with nothing to say ---


def _failed(name: str) -> HB.ComponentFailure:
    return HB.ComponentFailure(name, "KeyError: 'position'",
                               "Nothing was watched tonight.")


def test_a_crashed_watcher_is_VISIBLE_in_the_report():
    """**THE ONE THAT MATTERS FOR D1.** Before the fix this rendered a report
    with no occurrence of the string `E97` anywhere at all."""
    out = REP.render([], run_ts=RUN_TS, as_of=AS_OF,
                     failures=[_failed(HB.COMPONENT_PRICE_WATCH)])
    assert "E97" in out
    assert "## COMPONENTS THAT DID NOT RUN — 1" in out
    assert "## RANKED WATCH (E97) — DATA MISSING" in out
    assert "KeyError: 'position'" in out


def test_a_crashed_needs_owner_is_VISIBLE_in_the_report():
    out = REP.render([], run_ts=RUN_TS, as_of=AS_OF,
                     failures=[_failed(HB.COMPONENT_NEEDS_OWNER)])
    assert "## NEEDS OWNER — DATA MISSING" in out
    assert "KeyError: 'position'" in out


def test_a_watcher_that_RAN_and_found_nothing_says_a_DIFFERENT_thing():
    """The third state. `price_watch_ran` is CLAIMED by the caller and never
    inferred from an empty list: only the code that called the watcher knows
    whether it was called."""
    ran = REP.render([], run_ts=RUN_TS, as_of=AS_OF, price_watch_ran=True)
    assert "## RANKED WATCH (E97) — no ranked names to watch" in ran
    assert "DATA MISSING" not in ran.split("RANKED WATCH")[1][:400]

    not_attempted = REP.render([], run_ts=RUN_TS, as_of=AS_OF)
    assert "RANKED WATCH" not in not_attempted


def test_the_three_states_are_three_different_reports():
    failed = REP.render([], run_ts=RUN_TS, as_of=AS_OF, price_watch_ran=True,
                        failures=[_failed(HB.COMPONENT_PRICE_WATCH)])
    empty = REP.render([], run_ts=RUN_TS, as_of=AS_OF, price_watch_ran=True)
    assert failed != empty
    assert "DID NOT RUN" in failed and "DID NOT RUN" not in empty


# --- and it reaches the real run ------------------------------------------


def _watchlist(path: Path, tickers) -> Path:
    rows = "\n".join(
        f"  - ticker: {t}\n    name: {t}\n    currency: USD\n"
        f"    status: PIPELINE" for t in tickers)
    path.write_text(f"tickers:\n{rows}\n", encoding="utf-8")
    return path


def _frame(days: int = 400) -> pd.DataFrame:
    index = pd.to_datetime([AS_OF - pd.Timedelta(days=days - 1 - i)
                            for i in range(days)])
    return pd.DataFrame({"Open": [10.0] * days, "High": [11.0] * days,
                         "Low": [9.0] * days, "Close": [10.0] * days,
                         "Volume": [1000.0] * days}, index=index)


def test_a_run_that_prices_NOTHING_exits_non_zero_and_records_short(
        tmp_path: Path, monkeypatch):
    """End to end. The exit code is what stops systemd reaching
    `ExecStartPost=`, which is what stops the healthcheck ping, which is what
    lets the outside observer alarm on the ping's absence."""
    from vss import fetch as F

    def unreachable(ticker, period=F.DEFAULT_PERIOD):
        raise RuntimeError("Max retries exceeded: connection refused")

    monkeypatch.setattr(F, "fetch_live", unreachable)
    db = tmp_path / "vss.sqlite"
    code = R.run(watchlist_path=_watchlist(tmp_path / "w.yaml", ["AAA", "BBB"]),
                 cache_dir=tmp_path / "cache", db_path=db,
                 reports_dir=tmp_path / "reports", now=RUN_TS)

    assert code == HB.EXIT_COVERAGE_SHORT != 0
    assert HB.last_completion(db, kind=HB.KIND_NIGHTLY) is None, (
        "a run that priced nothing reset the staleness clock")
    shorts = HB.short_runs(db, since=RUN_TS - timedelta(hours=1))
    assert len(shorts) == 1 and shorts[0].covered == 0
    report = (tmp_path / "reports" / f"{AS_OF.isoformat()}.md").read_text()
    assert "## RUN COVERAGE — SHORT" in report


def test_a_run_that_prices_everything_exits_zero(tmp_path: Path, monkeypatch):
    from vss import fetch as F

    monkeypatch.setattr(F, "fetch_live",
                        lambda t, period=F.DEFAULT_PERIOD: _frame())
    db = tmp_path / "vss.sqlite"
    code = R.run(watchlist_path=_watchlist(tmp_path / "w.yaml", ["AAA", "BBB"]),
                 cache_dir=tmp_path / "cache", db_path=db,
                 reports_dir=tmp_path / "reports", now=RUN_TS)

    assert code == 0
    last = HB.last_completion(db, kind=HB.KIND_NIGHTLY)
    assert last is not None and last.covered == 2 and not last.short
    report = (tmp_path / "reports" / f"{AS_OF.isoformat()}.md").read_text()
    assert "RUN COVERAGE" not in report


def test_a_crashed_watcher_reaches_the_real_report(tmp_path: Path, monkeypatch):
    """The wrapping stays -- a broken watcher must never cost the report --
    and what changes is that the report says so."""
    from vss import fetch as F

    monkeypatch.setattr(F, "fetch_live",
                        lambda t, period=F.DEFAULT_PERIOD: _frame())

    def boom(**kwargs):
        raise RuntimeError("the ranking table is unreadable")

    monkeypatch.setattr(R, "price_watch", boom)
    code = R.run(watchlist_path=_watchlist(tmp_path / "w.yaml", ["AAA"]),
                 cache_dir=tmp_path / "cache", db_path=tmp_path / "vss.sqlite",
                 reports_dir=tmp_path / "reports", now=RUN_TS)

    assert code == 0, "a broken watcher must not fail the run"
    report = (tmp_path / "reports" / f"{AS_OF.isoformat()}.md").read_text()
    assert "COMPONENTS THAT DID NOT RUN" in report
    assert "the ranking table is unreadable" in report
    assert "RANKED WATCH (E97) — DATA MISSING" in report


def test_a_ranked_name_that_cannot_be_assessed_is_NAMED(tmp_path: Path,
                                                        monkeypatch):
    """`price_watch` swallowed a per-name failure with `continue`, so a
    ticker silently dropped out of the watch and the table simply had one
    fewer row than the ranking it was built from."""
    from vss import readiness as RD
    from vss.store import persist_ranking

    db = tmp_path / "vss.sqlite"
    persist_ranking(db, [{"run_ts": "t", "as_of": "2026-08-29",
                          "ticker": "AAA", "position": 1, "section": "ranked",
                          "provenance": "scheduled"}])
    monkeypatch.setattr(RD, "assess",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("store is malformed")))
    monkeypatch.setattr("vss.pricewatch.industry_strings", lambda **k: {"AAA": "x"})

    failures: list = []
    R.price_watch(run_ts=RUN_TS, as_of=AS_OF, settled=AS_OF,
                  cache_dir=tmp_path / "cache", db_path=db, dry_run=True,
                  failures=failures)
    assert len(failures) == 1
    assert failures[0].name == HB.COMPONENT_READINESS
    assert "AAA" in failures[0].detail and "store is malformed" in failures[0].detail
