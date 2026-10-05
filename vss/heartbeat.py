"""THE DEAD MAN'S SWITCH: a run that does not happen must not look like a
quiet one.

WHY THIS EXISTS. Until this module, **a nightly run that failed and a
nightly run with nothing to say were indistinguishable.** Both produced
silence on the phone. The E92 pointer fires only when there is a name
waiting; no pointer therefore meant *either* "nothing needs you" *or* "the
run died at 22:30 and has been dead ever since", and nothing anywhere told
the two apart. A monitor whose failure mode is silence is a monitor that
stops being believed the first time you find out the hard way.

THREE LEGS, and they cover different things. None of them covers everything,
and the third exists only because the first two share a fate.

1. **THE RUN RECORDS ITSELF** (`run_completions`, written here). A row is
   inserted when the run starts and updated when it reaches the end. The
   next run reads the newest COMPLETED full run and, if that is older than
   `STALE_AFTER_HOURS`, says so in its report and in its pointer. This
   catches a run that died -- but only once a *later* run succeeds, so on
   its own it cannot report an outage that is still happening.

2. **`OnFailure=` ON THE UNIT** (`deploy/vss-failure@.service`). systemd
   posts the moment a run exits non-zero or times out. This is the fast leg,
   and it is the only one that fires while the outage is happening. It is
   deliberately a plain `curl` in a shell script and NOT this package: the
   failure being reported may well BE this package.

3. **A CHECK-IN ON ITS OWN TIMER** (`vss-checkin.timer`, `vss checkin`).
   Legs 1 and 2 both need the run to at least *start*. A timer that was
   disabled, masked, or never re-enabled after a reboot starts nothing, so
   neither fires -- and that is precisely the failure that looks most like
   an ordinary quiet week. The check-in is a SEPARATE timer, so
   `vss.timer` cannot silence it, and it checks two things the run cannot
   check about itself: whether a completed run is on record at all, and
   whether the timers are still enabled and running.

WHAT IS NOT COVERED, stated plainly because implying otherwise is worse
than not building it: **a dead VPS cannot page itself.** If the machine is
off, the network is down, the user manager is not running, or the check-in
timer is itself disabled, every leg above is silent, and the silence is
indistinguishable from a quiet week. Closing that needs an OUTSIDE observer
-- a service that expects a ping and alerts on its ABSENCE. ntfy has no such
facility, so it is not built here; see the report and `deploy/README.md`.

OUTBOUND ONLY, like everything else that touches the topic (E92). Nothing
here reads from ntfy, and a failed POST is logged and never fails the run.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Sequence

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "vss.sqlite"

#: How long the switch tolerates before it says so. The nightly run is
#: daily, so 72 hours is three missed runs -- late enough that a single
#: reboot or a one-off network failure does not cry wolf, early enough that
#: an outage is caught in the same week it started.
STALE_AFTER_HOURS = 72

#: The weekly screen's own bar. It runs on Saturday, so 10 days is one
#: missed Saturday plus enough slack that a `Persistent=true` catch-up on
#: Sunday is not reported as an outage.
WEEKLY_STALE_AFTER_HOURS = 24 * 10

KIND_NIGHTLY = "nightly"
KIND_WEEKLY = "weekly"

#: The units the check-in expects to find enabled and loaded. A timer that
#: is disabled starts nothing, and nothing else in this system would notice.
WATCHED_TIMERS = ("vss.timer", "vss-screen.timer")

#: HOW MUCH OF THE WATCHLIST A NIGHTLY RUN MUST ACTUALLY PRICE.
#:
#: **WHY THIS EXISTS** (CODE-REVIEW-2026-09-01 D2). The switch measured
#: whether a run HAPPENED and never whether it GOT ANYTHING. A night on which
#: every fetch failed returned exit code 0, recorded `completed = 1` with
#: `covered = 0`, reset the 72-hour clock -- and fired `ExecStartPost=`,
#: telling healthchecks.io the run had succeeded. `runner.run` was careful to
#: record PRICED coverage rather than row count, for exactly this reason, and
#: nothing read the column. The weekly screen has had `assess_coverage` and a
#: tolerance since E93; the nightly had no equivalent.
#:
#: **A CHOSEN NUMBER, AND THE OWNER'S TO MOVE**, in the shape
#: `screenwatch.COVERAGE_TOLERANCE` and `pricewatch.REARM_MARGIN` already
#: take. What is measured is the distribution it sits under: the thirteen
#: full nightly runs on record (2026-08-22 to 2026-08-31, 7 to 22 names)
#: priced **100% with zero fetch errors, every one**. So the floor sits below
#: every observation this project has, and 0.90 on a 22-name watchlist means
#: ONE name may go dark without a finding and TWO may not -- loose enough
#: that a single delisting does not page nightly, tight enough that a bad
#: feed cannot pass as a quiet evening.
#:
#: Every run PRINTS the comparison it was applied to, so a wrong figure shows
#: up in the report rather than silently swallowing a week.
NIGHTLY_COVERAGE_FLOOR = 0.90

#: What `vss run` exits with when the run reached its end and did not cover
#: enough. NOT zero, and that is the point: `ExecStartPost=` runs only after
#: a successful `ExecStart=`, so a short run cannot ping the outside observer,
#: and `OnFailure=` reports it while it is happening.
EXIT_COVERAGE_SHORT = 1


#: The names a report gates a section on, so a FAILED component and a
#: component with NOTHING TO SAY are told apart by the reader and not only by
#: the journal (CODE-REVIEW-2026-09-01 D1).
COMPONENT_PRICE_WATCH = "RANKED WATCH (E97)"
COMPONENT_NEEDS_OWNER = "NEEDS OWNER (E92)"
COMPONENT_CONTINUITY = "RUN CONTINUITY"
COMPONENT_READINESS = "E94 readiness"


@dataclass(frozen=True)
class ComponentFailure:
    """A part of the run that raised, and what the reader is NOT seeing.

    **WHY THIS EXISTS** (CODE-REVIEW-2026-09-01 D1). `runner.run` wraps the
    E97 watcher and the E92 pointer so that neither can cost the nightly
    report -- which is right -- and then set the result to an empty list.
    `report.render` gates both sections on truthiness, so a watcher that had
    been broken for a month produced a report INDISTINGUISHABLE from a month
    in which it ran and found nothing. Verified: a render with an empty watch
    list contained no occurrence of the string "E97" anywhere. The only
    signal was a `log.warning` in the journal, which nobody reads.

    That is the same failure-looks-like-silence shape the dead man's switch
    was built to close, one section further down the same file. So a
    component that fails is CARRIED, not dropped: it appears in its own
    section of the report and the section it would have filled says DATA
    MISSING and names the reason.
    """

    name: str
    detail: str
    #: What the reader is not being shown, in their terms rather than the
    #: exception's. A stack trace says what broke; this says what is missing.
    consequence: str = ""

    def line(self) -> str:
        return (f"**{self.name}** did not run — {self.detail}"
                + (f". {self.consequence}" if self.consequence else ""))


def find_failure(failures: "Sequence[ComponentFailure]",
                 name: str) -> "ComponentFailure | None":
    """The failure recorded for ``name``, or None if that component ran."""
    return next((f for f in failures if f.name == name), None)


@dataclass(frozen=True)
class Coverage:
    """Did a run that reached its end actually cover the list? (D2)

    THREE STATES, and the middle one is the whole point: a run that DIED, a
    run that ran and got almost nothing, and a run that worked. Only the
    third resets the clock and pings the outside observer.
    """

    expected: int
    covered: int
    short: bool
    reason: str = ""

    @property
    def line(self) -> str:
        if not self.expected:
            return f"{self.covered} priced; nothing was expected"
        return (f"priced {self.covered}/{self.expected} "
                f"({self.covered / self.expected:.0%})")


def assess_coverage(*, expected: int, covered: int,
                    floor: float = NIGHTLY_COVERAGE_FLOOR) -> Coverage:
    """Is this a run, or a run-shaped silence? (D2)

    TWO QUESTIONS, and only one of them needs a number:

    * **nothing was priced at all** -- that is not a run, at any floor, and
      it is the case the whole finding was about;
    * **some of the list is missing** -- judged against ``floor``.

    A run that expected nothing (an empty watchlist) is NOT short: it covered
    everything asked of it, and inventing a finding there would be a phantom.
    """
    if expected <= 0:
        return Coverage(expected, covered, False)
    if covered <= 0:
        return Coverage(expected, covered, True,
                        f"NOTHING WAS PRICED: 0 of {expected} watchlist "
                        f"entries got a close. The run reached its end and "
                        f"got nothing, which is not a run that worked")
    fraction = covered / expected
    if fraction < floor:
        return Coverage(expected, covered, True,
                        f"priced {covered} of {expected} entries "
                        f"({fraction:.0%}), below the {floor:.0%} floor")
    return Coverage(expected, covered, False)


@dataclass(frozen=True)
class Completion:
    """One recorded run. `finished_at` is None for a run that died."""

    id: int
    kind: str
    started_at: str
    finished_at: str | None
    completed: bool
    as_of: str
    scope: str | None
    dry_run: bool
    expected: int | None
    covered: int | None
    errors: int | None
    detail: str | None
    #: D2: it reached its end and did not cover enough. A THIRD state, kept
    #: apart from "died" and from "worked".
    short: bool = False

    @property
    def finished(self) -> datetime | None:
        return _parse(self.finished_at)

    @property
    def coverage_line(self) -> str:
        if self.expected is None or self.covered is None:
            return "coverage not recorded"
        if not self.expected:
            return f"{self.covered} covered"
        return (f"{self.covered}/{self.expected} covered "
                f"({self.covered / self.expected:.0%})")


def _read_only(db_path: Path):
    """A connection that CANNOT write, and never creates or migrates.

    `store.connect` runs the schema and the migrations on every call. That is
    right for a run; it is wrong for the check-in, whose whole claim is that
    it writes nothing -- its unit has no `ReadWritePaths` at all and runs
    under `ProtectHome=read-only`, so a schema write there would fail and be
    reported as "no record", which is a phantom outage rather than a real
    one. `mode=ro` makes the guarantee the sandbox already asserts.
    """
    import sqlite3

    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


# --- writing the record ----------------------------------------------------


def begin(db_path: Path, *, kind: str, started_at: datetime, as_of: date,
          scope: str | None = None, dry_run: bool = False) -> int | None:
    """Record that a run STARTED. Returns the row id, or None on failure.

    Never raises: a switch that can break the thing it guards is worse than
    no switch. A None return means the run simply goes unrecorded, and the
    NEXT run reports the gap -- which is exactly the state this module is
    for, arrived at honestly.
    """
    from .store import connect

    try:
        conn = connect(db_path)
        try:
            with conn:
                cur = conn.execute(
                    "INSERT INTO run_completions "
                    "(kind, started_at, finished_at, completed, as_of, scope, "
                    " dry_run, expected, covered, errors, detail) "
                    "VALUES (?, ?, NULL, 0, ?, ?, ?, NULL, NULL, NULL, NULL)",
                    (kind, started_at.isoformat(), as_of.isoformat(), scope,
                     1 if dry_run else 0))
                return int(cur.lastrowid)
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 -- never fails the run
        log.warning("dead man's switch: could not record the start: %s: %s",
                    type(exc).__name__, exc)
        return None


def finish(db_path: Path, row_id: int | None, *, finished_at: datetime,
           expected: int | None = None, covered: int | None = None,
           errors: int | None = None, detail: str | None = None,
           short: bool = False) -> bool:
    """Mark the run as having REACHED ITS END. Never raises.

    ``short`` (D2) means it reached the end and did not cover enough of what
    it set out to cover. It is recorded rather than folded into `completed`,
    because "died at hour three" and "ran and priced nothing" have different
    causes and want different reading -- but a short run does NOT count as a
    completed one for the staleness clock, and `last_completion` excludes it.
    """
    from .store import connect

    if row_id is None:
        return False
    try:
        conn = connect(db_path)
        try:
            with conn:
                conn.execute(
                    "UPDATE run_completions SET finished_at = ?, completed = 1, "
                    "expected = ?, covered = ?, errors = ?, detail = ?, "
                    "short = ? WHERE id = ?",
                    (finished_at.isoformat(), expected, covered, errors,
                     detail, 1 if short else 0, row_id))
        finally:
            conn.close()
        return True
    except Exception as exc:  # noqa: BLE001 -- never fails the run
        log.warning("dead man's switch: could not record the finish: %s: %s",
                    type(exc).__name__, exc)
        return False


# --- reading it back -------------------------------------------------------


def last_completion(db_path: Path, *, kind: str | None = None,
                    exclude_id: int | None = None) -> Completion | None:
    """The newest COMPLETED, FULL, NON-DRY run, or None.

    Three exclusions, each deliberate:

    * `completed = 0` -- a run that started and died is not a run that ran;
    * `dry_run = 1` -- a dry run wrote nothing and proves nothing;
    * `scope IS NOT NULL` -- a `--ticker` run examined ONE name. Letting it
      reset the clock would mean a week of one-ticker runs reads as a week
      of healthy full runs, which is the exact confusion this module exists
      to remove;
    * `short = 1` -- D2. A run that reached its end and priced nothing is
      run-shaped silence. Letting it reset the clock would mean a week of
      dead feeds reads as a healthy week, which is the SAME confusion
      arriving through the one door that was still open.
    """
    if not Path(db_path).exists():
        # A READ NEVER CREATES THE DATABASE. `sqlite3.connect` would, and a
        # dry run promises "no database row" -- reading the switch must not
        # be the thing that breaks that promise. An absent file is an
        # honest "no record", which is what the caller is told.
        return None

    sql = ("SELECT id, kind, started_at, finished_at, completed, as_of, "
           "scope, dry_run, expected, covered, errors, detail, short "
           "FROM run_completions "
           "WHERE completed = 1 AND dry_run = 0 AND scope IS NULL "
           "AND short = 0")
    params: list = []
    if kind is not None:
        sql += " AND kind = ?"
        params.append(kind)
    if exclude_id is not None:
        sql += " AND id <> ?"
        params.append(exclude_id)
    sql += " ORDER BY finished_at DESC, id DESC LIMIT 1"
    try:
        conn = _read_only(db_path)
        try:
            row = conn.execute(sql, params).fetchone()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 -- never fails the run
        log.warning("dead man's switch: could not read the record: %s: %s",
                    type(exc).__name__, exc)
        return None
    if row is None:
        return None
    return Completion(id=row[0], kind=row[1], started_at=row[2],
                      finished_at=row[3], completed=bool(row[4]), as_of=row[5],
                      scope=row[6], dry_run=bool(row[7]), expected=row[8],
                      covered=row[9], errors=row[10], detail=row[11],
                      short=bool(row[12]))


def died_since(db_path: Path, *, since: datetime, kind: str | None = None,
               exclude_id: int | None = None) -> list[Completion]:
    """Runs of ``kind`` that STARTED since `since` and never recorded an end.

    A run that crashed leaves one of these. The `OnFailure=` leg reports it
    at the time; this is how the NEXT run sees it, in case the POST never
    landed or the topic was unset that night.

    ``kind`` IS NOT OPTIONAL IN PRACTICE (CODE-REVIEW-2026-09-01 D6). Without
    it this returned every kind, and `checkin` calls `report_lines` twice --
    once for `nightly`, once for `weekly` -- so a single crashed nightly run
    was POSTED TO THE PHONE TWICE. Worse, the weekly pass uses a 240-hour
    window, so that one crash was re-posted every day for ten days, long
    after the nightly leg had moved past it. A monitor that buzzes twice a
    day about a crash already dealt with is a monitor that gets muted.
    """
    if not Path(db_path).exists():
        # A READ NEVER CREATES THE DATABASE. `sqlite3.connect` would, and a
        # dry run promises "no database row" -- reading the switch must not
        # be the thing that breaks that promise. An absent file is an
        # honest "no record", which is what the caller is told.
        return []

    # A CRASH A LATER RUN RECOVERED IS NOT REPORTED (2026-09-19). The weekly
    # screen was OOM-killed on 09-17 and 09-19 and re-run by hand both times;
    # each re-run completed, yet the two dead rows were posted to the phone
    # every morning for the whole 240-hour window. The `OnFailure=` leg has
    # already told of the crash; once a full run of the same kind has since
    # completed, the continuity it threatened is restored. A SHORT run does
    # not count as the recovery -- it reached its end with nothing.
    sql = ("SELECT id, kind, started_at, finished_at, completed, as_of, "
           "scope, dry_run, expected, covered, errors, detail, short "
           "FROM run_completions AS d "
           "WHERE completed = 0 AND dry_run = 0 AND scope IS NULL "
           "AND started_at >= ? "
           "AND NOT EXISTS (SELECT 1 FROM run_completions AS r "
           "WHERE r.kind = d.kind AND r.completed = 1 AND r.short = 0 "
           "AND r.dry_run = 0 AND r.scope IS NULL "
           "AND r.started_at > d.started_at)")
    params: list = [since.isoformat()]
    if kind is not None:
        sql += " AND kind = ?"
        params.append(kind)
    if exclude_id is not None:
        sql += " AND id <> ?"
        params.append(exclude_id)
    sql += " ORDER BY started_at"
    try:
        conn = _read_only(db_path)
        try:
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 -- never fails the run
        log.warning("dead man's switch: could not read the record: %s: %s",
                    type(exc).__name__, exc)
        return []
    return [Completion(id=r[0], kind=r[1], started_at=r[2], finished_at=r[3],
                       completed=bool(r[4]), as_of=r[5], scope=r[6],
                       dry_run=bool(r[7]), expected=r[8], covered=r[9],
                       errors=r[10], detail=r[11], short=bool(r[12]))
            for r in rows]


# --- the judgement ---------------------------------------------------------


def staleness_line(last: Completion | None, *, now: datetime,
                   threshold_hours: int = STALE_AFTER_HOURS,
                   kind: str = KIND_NIGHTLY,
                   missing_is_finding: bool = True) -> str | None:
    """One line if the gap is too long, None if it is not.

    THREE OUTCOMES, and "no record at all" is not folded into "stale". It
    has a different cause and a different reading: the first run after this
    module was built has no record and never will have had one, and so does
    a machine whose `data/vss.sqlite` was replaced. Both are worth a line;
    neither is "the run has been dead for four days".
    """
    if last is None:
        if not missing_is_finding:
            # The weekly screen was scheduled on 2026-08-31 and first fires
            # 2026-09-05. "Never yet run" is an ORDINARY state for it, and
            # its timer being enabled is checked separately; complaining
            # daily until Saturday would train the reader to ignore the
            # pointer, which is E93's argument about rank wobble applied to
            # the switch itself.
            return None
        return (f"RUN CONTINUITY: no completed {kind} run is on record. "
                f"Expected once -- on the first run after the dead man's "
                f"switch was built -- and otherwise means data/vss.sqlite "
                f"was replaced or emptied.")
    finished = last.finished
    if finished is None:
        return (f"RUN CONTINUITY: the newest {kind} record is marked complete "
                f"but carries no finish time; the switch cannot measure the "
                f"gap.")
    if finished.tzinfo is None and now.tzinfo is not None:
        finished = finished.replace(tzinfo=now.tzinfo)
    elif finished.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=finished.tzinfo)
    gap = now - finished
    if gap <= timedelta(hours=threshold_hours):
        return None
    hours = gap.total_seconds() / 3600.0
    return (f"RUN CONTINUITY: no completed {kind} run for {hours:.0f}h "
            f"(last {finished.strftime('%Y-%m-%d %H:%M')}, "
            f"{last.coverage_line}); the bar is {threshold_hours}h.")


def short_runs(db_path: Path, *, since: datetime, kind: str | None = None,
               exclude_id: int | None = None) -> list[Completion]:
    """Runs of ``kind`` that reached their end since `since` and covered
    almost nothing (D2).

    These are invisible to `last_completion` on purpose -- they do not reset
    the clock -- so this is how they reach the report at all. Without it a
    week of dead feeds would show only as "no completed run for 168h", which
    is true and says nothing about why.
    """
    if not Path(db_path).exists():
        return []
    sql = ("SELECT id, kind, started_at, finished_at, completed, as_of, "
           "scope, dry_run, expected, covered, errors, detail, short "
           "FROM run_completions "
           "WHERE completed = 1 AND short = 1 AND dry_run = 0 "
           "AND scope IS NULL AND started_at >= ?")
    params: list = [since.isoformat()]
    if kind is not None:
        sql += " AND kind = ?"
        params.append(kind)
    if exclude_id is not None:
        sql += " AND id <> ?"
        params.append(exclude_id)
    sql += " ORDER BY started_at"
    try:
        conn = _read_only(db_path)
        try:
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 -- never fails the run
        log.warning("dead man's switch: could not read the record: %s: %s",
                    type(exc).__name__, exc)
        return []
    return [Completion(id=r[0], kind=r[1], started_at=r[2], finished_at=r[3],
                       completed=bool(r[4]), as_of=r[5], scope=r[6],
                       dry_run=bool(r[7]), expected=r[8], covered=r[9],
                       errors=r[10], detail=r[11], short=bool(r[12]))
            for r in rows]


def short_lines(runs: Sequence[Completion]) -> list[str]:
    """A line per run that ran to the end and did not cover the list."""
    return [f"RUN COVERAGE: the {c.kind} run of {c.as_of} reached its end and "
            f"{c.coverage_line} -- {c.detail or 'below the floor'}. It did "
            f"NOT reset the staleness clock and sent no healthcheck ping."
            for c in runs]


def crash_lines(deaths: Sequence[Completion]) -> list[str]:
    """A line per run that started and never finished."""
    return [f"RUN CONTINUITY: the {c.kind} run started "
            f"{(_parse(c.started_at) or datetime.min).strftime('%Y-%m-%d %H:%M')} "
            f"never reached its end."
            for c in deaths]


def report_lines(db_path: Path, *, now: datetime, kind: str = KIND_NIGHTLY,
                 exclude_id: int | None = None,
                 threshold_hours: int = STALE_AFTER_HOURS,
                 missing_is_finding: bool = True) -> list[str]:
    """Everything the switch has to say about continuity, as lines.

    Empty is the healthy answer, and it is the common one. Never raises.
    """
    try:
        last = last_completion(db_path, kind=kind, exclude_id=exclude_id)
        lines: list[str] = []
        stale = staleness_line(last, now=now, kind=kind,
                               threshold_hours=threshold_hours,
                               missing_is_finding=missing_is_finding)
        if stale:
            lines.append(stale)
        window = now - timedelta(hours=threshold_hours)
        # D6: `kind` reaches `died_since` now. Without it the weekly pass
        # reported the nightly's crashes as well as its own, so `checkin`
        # posted every crash twice and the 240-hour weekly window re-posted
        # it daily for ten days.
        lines.extend(crash_lines(died_since(db_path, since=window, kind=kind,
                                            exclude_id=exclude_id)))
        # D2: a run that ran and got nothing is invisible to
        # `last_completion` by design, so this is how it reaches the report.
        lines.extend(short_lines(short_runs(db_path, since=window, kind=kind,
                                            exclude_id=exclude_id)))
        return lines
    except Exception as exc:  # noqa: BLE001 -- never fails the run
        # D1: EMPTY MEANS HEALTHY HERE, so returning [] on an exception told
        # the reader the opposite of what had happened. The switch failing is
        # itself a finding, and it is the one finding this module can least
        # afford to report as silence.
        log.warning("dead man's switch: could not assess continuity: %s: %s",
                    type(exc).__name__, exc)
        return [f"RUN CONTINUITY: THE SWITCH ITSELF COULD NOT BE READ "
                f"({type(exc).__name__}: {exc}). Whether a completed {kind} "
                f"run is on record is DATA MISSING -- not 'fine'."]


# --- the check-in: what the run cannot check about itself ------------------


def _systemctl(args: Sequence[str],
               runner: Callable | None = None) -> tuple[int, str]:
    """`systemctl --user ...`, or (127, "") when it cannot be run at all."""
    runner = runner or subprocess.run
    try:
        proc = runner(["systemctl", "--user", *args], capture_output=True,
                      text=True, timeout=15)
    except Exception as exc:  # noqa: BLE001 -- an absent systemctl is DATA MISSING
        log.warning("check-in: systemctl unavailable: %s: %s",
                    type(exc).__name__, exc)
        return 127, ""
    return proc.returncode, (proc.stdout or "").strip()


def timer_lines(units: Sequence[str] = WATCHED_TIMERS,
                runner: Callable | None = None) -> list[str]:
    """A line per timer that is not both ENABLED and ACTIVE.

    THIS IS THE LEG THE RUN CANNOT PROVIDE. A disabled timer starts no run,
    so it writes no record, so the completion check sees only silence and
    the `OnFailure=` hook sees nothing at all -- and a disabled timer is the
    single most likely way this stops working, because it survives a
    `systemctl --user disable` typo and a user manager that was never
    lingered across a reboot.

    An unavailable `systemctl` is DATA MISSING and says so; it is never read
    as "the timers are fine".
    """
    lines: list[str] = []
    for unit in units:
        code, enabled = _systemctl(["is-enabled", unit], runner)
        if code == 127:
            return [f"CHECK-IN: systemctl could not be run, so the state of "
                    f"{', '.join(units)} is DATA MISSING -- not 'fine'."]
        code_active, active = _systemctl(["is-active", unit], runner)
        if enabled != "enabled" or active != "active":
            lines.append(f"CHECK-IN: {unit} is "
                         f"{enabled or 'unknown'}/{active or 'unknown'} "
                         f"(expected enabled/active) -- it will start nothing.")
    return lines


@dataclass
class CheckinResult:
    lines: list[str]
    posted: str = "nothing to send"

    @property
    def healthy(self) -> bool:
        return not self.lines


def checkin(db_path: Path = DB_PATH, *, now: datetime | None = None,
            units: Sequence[str] = WATCHED_TIMERS,
            threshold_hours: int = STALE_AFTER_HOURS,
            notify: bool = True,
            runner: Callable | None = None,
            poster: Callable | None = None) -> CheckinResult:
    """The independent check-in. Silence when healthy; a pointer when not.

    Run by `vss-checkin.timer`, which is DELIBERATELY A DIFFERENT TIMER from
    `vss.timer`. If they shared one, the failure that stops the run would
    stop the check on the run, and the whole thing would be a switch wired
    to its own power supply.

    It posts only when something is wrong. A periodic "still alive" post
    would be honest only if something OUTSIDE this machine were counting
    them, and nothing is -- see the module docstring.
    """
    from .refresh import post_needs_owner

    now = now or datetime.now().astimezone()
    lines = report_lines(db_path, now=now, kind=KIND_NIGHTLY,
                         threshold_hours=threshold_hours)
    lines.extend(report_lines(db_path, now=now, kind=KIND_WEEKLY,
                              threshold_hours=WEEKLY_STALE_AFTER_HOURS,
                              missing_is_finding=False))
    lines.extend(timer_lines(units, runner))
    result = CheckinResult(lines=lines)
    if lines and notify:
        poster = poster or post_needs_owner
        result.posted = poster(lines, title="vss: the run has gone quiet")
    elif lines:
        result.posted = "not sent: --no-send"
    return result
