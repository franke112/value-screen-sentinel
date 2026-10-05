"""The dead man's switch: a stale record points, a fresh one does not.

Three things are pinned here, and they are the three the build was asked
for:

1. a STALE completion produces the pointer;
2. a FRESH one does not;
3. a FAILING run reaches the `OnFailure=` path -- pinned at the level a
   test can honestly reach, which is the wiring: every scheduled unit names
   the notifier, the notifier exists, is executable, and posts what it is
   given. That the kernel then runs it was verified live on the VPS and is
   recorded in `reports/DEADMAN-2026-08-31.md`, not asserted here.
"""

from __future__ import annotations

import re
import stat
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from vss import heartbeat as HB

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEPLOY = PROJECT_ROOT / "deploy"

NOW = datetime(2026, 8, 31, 22, 30, tzinfo=timezone.utc)


@pytest.fixture()
def db(tmp_path: Path) -> Path:
    return tmp_path / "vss.sqlite"


def record(db: Path, *, finished: datetime | None, kind: str = HB.KIND_NIGHTLY,
           scope: str | None = None, dry_run: bool = False,
           expected: int = 22, covered: int = 22) -> int | None:
    started = (finished or NOW) - timedelta(minutes=3)
    row = HB.begin(db, kind=kind, started_at=started, as_of=started.date(),
                   scope=scope, dry_run=dry_run)
    if finished is not None:
        HB.finish(db, row, finished_at=finished, expected=expected,
                  covered=covered, errors=0, detail="test")
    return row


# --- 1. a stale completion produces the pointer ---------------------------


def test_stale_completion_produces_a_line(db: Path) -> None:
    record(db, finished=NOW - timedelta(hours=73))
    lines = HB.report_lines(db, now=NOW)
    assert len(lines) == 1
    assert "no completed nightly run for 73h" in lines[0]
    assert "22/22 covered" in lines[0]


def test_no_record_at_all_produces_its_own_line(db: Path) -> None:
    """Never folded into 'stale': a different cause, a different reading."""
    lines = HB.report_lines(db, now=NOW)
    assert len(lines) == 1
    assert "no completed nightly run is on record" in lines[0]
    assert "73h" not in lines[0]


def test_a_run_that_started_and_died_is_reported(db: Path) -> None:
    record(db, finished=NOW - timedelta(hours=2))          # a healthy one
    record(db, finished=None)                              # and one that died
    lines = HB.report_lines(db, now=NOW)
    assert len(lines) == 1
    assert "never reached its end" in lines[0]


# --- 2. a fresh completion does not ---------------------------------------


def test_fresh_completion_is_silent(db: Path) -> None:
    record(db, finished=NOW - timedelta(hours=24))
    assert HB.report_lines(db, now=NOW) == []


def test_exactly_at_the_bar_is_not_stale(db: Path) -> None:
    record(db, finished=NOW - timedelta(hours=72))
    assert HB.report_lines(db, now=NOW) == []


def test_one_hour_past_the_bar_is(db: Path) -> None:
    record(db, finished=NOW - timedelta(hours=72, minutes=1))
    assert HB.report_lines(db, now=NOW) != []


# --- what may NOT reset the clock -----------------------------------------


def test_a_scoped_run_does_not_reset_the_clock(db: Path) -> None:
    """A week of --ticker runs must not read as a week of healthy runs."""
    record(db, finished=NOW - timedelta(hours=100))
    record(db, finished=NOW - timedelta(hours=1), scope="SAP.DE")
    lines = HB.report_lines(db, now=NOW)
    assert lines and "100h" in lines[0]


def test_a_dry_run_does_not_reset_the_clock(db: Path) -> None:
    record(db, finished=NOW - timedelta(hours=100))
    record(db, finished=NOW - timedelta(hours=1), dry_run=True)
    lines = HB.report_lines(db, now=NOW)
    assert lines and "100h" in lines[0]


def test_a_started_but_unfinished_run_does_not_reset_the_clock(db: Path) -> None:
    record(db, finished=NOW - timedelta(hours=100))
    record(db, finished=None)
    lines = HB.report_lines(db, now=NOW)
    assert any("100h" in line for line in lines)


def test_the_weekly_is_measured_on_its_own_bar(db: Path) -> None:
    record(db, finished=NOW - timedelta(hours=100), kind=HB.KIND_WEEKLY)
    # 100h is four days: stale for a nightly, fine for a Saturday screen.
    assert HB.report_lines(db, now=NOW, kind=HB.KIND_WEEKLY,
                           threshold_hours=HB.WEEKLY_STALE_AFTER_HOURS) == []
    assert HB.report_lines(db, now=NOW, kind=HB.KIND_WEEKLY) != []


def test_a_never_yet_run_weekly_is_not_a_finding(db: Path) -> None:
    """It was scheduled 2026-08-31 and first fires 2026-09-05."""
    assert HB.report_lines(db, now=NOW, kind=HB.KIND_WEEKLY,
                           missing_is_finding=False) == []


def test_a_naive_timestamp_does_not_crash_the_switch(db: Path) -> None:
    """Old rows, or a machine whose clock reads naive, still measure."""
    naive = datetime(2026, 8, 20, 22, 30)
    row = HB.begin(db, kind=HB.KIND_NIGHTLY, started_at=naive,
                   as_of=naive.date())
    HB.finish(db, row, finished_at=naive, expected=22, covered=22)
    lines = HB.report_lines(db, now=NOW)
    assert lines and "no completed nightly run for" in lines[0]


# --- the check-in ---------------------------------------------------------


def fake_systemctl(states):
    """A `subprocess.run` stand-in returning canned is-enabled/is-active."""
    class Proc:
        def __init__(self, out): self.stdout, self.stderr, self.returncode = out, "", 0

    def run(argv, **_kwargs):
        _, _user, verb, unit = argv
        return Proc(states[unit]["enabled" if verb == "is-enabled" else "active"])
    return run


ALIVE = {"vss.timer": {"enabled": "enabled", "active": "active"},
         "vss-screen.timer": {"enabled": "enabled", "active": "active"}}


def test_checkin_is_silent_when_everything_is_alive(db: Path) -> None:
    record(db, finished=NOW - timedelta(hours=12))
    record(db, finished=NOW - timedelta(hours=12), kind=HB.KIND_WEEKLY)
    sent: list = []
    result = HB.checkin(db, now=NOW, runner=fake_systemctl(ALIVE),
                        poster=lambda lines, **kw: sent.append(lines) or "sent")
    assert result.healthy
    assert sent == []


def test_checkin_posts_when_the_run_is_stale(db: Path) -> None:
    record(db, finished=NOW - timedelta(hours=99))
    sent: list = []
    result = HB.checkin(db, now=NOW, runner=fake_systemctl(ALIVE),
                        poster=lambda lines, **kw: sent.append((lines, kw)) or "sent")
    assert not result.healthy
    assert sent and "99h" in sent[0][0][0]
    assert sent[0][1]["title"] == "vss: the run has gone quiet"


def test_checkin_catches_a_disabled_timer_a_run_never_could(db: Path) -> None:
    """The leg the run cannot provide: a timer that starts nothing."""
    record(db, finished=NOW - timedelta(hours=12))
    record(db, finished=NOW - timedelta(hours=12), kind=HB.KIND_WEEKLY)
    dead = {"vss.timer": {"enabled": "disabled", "active": "inactive"},
            "vss-screen.timer": {"enabled": "enabled", "active": "active"}}
    result = HB.checkin(db, now=NOW, runner=fake_systemctl(dead), notify=False)
    assert not result.healthy
    assert any("vss.timer is disabled/inactive" in line for line in result.lines)


def test_an_unavailable_systemctl_is_data_missing_not_fine() -> None:
    def boom(*_args, **_kwargs):
        raise FileNotFoundError("systemctl")
    lines = HB.timer_lines(runner=boom)
    assert lines and "DATA MISSING" in lines[0]


def test_checkin_does_not_post_with_no_send(db: Path) -> None:
    record(db, finished=NOW - timedelta(hours=99))
    result = HB.checkin(db, now=NOW, runner=fake_systemctl(ALIVE), notify=False)
    assert not result.healthy
    assert result.posted == "not sent: --no-send"


# --- 3. the OnFailure path ------------------------------------------------


SCHEDULED_UNITS = ("vss.service", "vss-screen.service", "vss-checkin.service")


@pytest.mark.parametrize("unit", SCHEDULED_UNITS)
def test_every_scheduled_unit_names_the_failure_notifier(unit: str) -> None:
    text = (DEPLOY / unit).read_text()
    assert "OnFailure=vss-failure@%n.service" in text, (
        f"{unit} can fail silently: nothing pages when it exits non-zero")


def test_the_notifier_unit_exists_and_runs_the_script() -> None:
    text = (DEPLOY / "vss-failure@.service").read_text()
    assert "vss-notify-failure.sh %I" in text
    assert "EnvironmentFile=-%h/.config/vss/vss.env" in text
    # A notifier that notifies about its own failure is a loop.
    assert "OnFailure=" not in re.sub(r"(?m)^#.*$", "", text)


def test_the_notifier_script_is_executable_and_needs_no_venv() -> None:
    script = DEPLOY / "vss-notify-failure.sh"
    assert script.stat().st_mode & stat.S_IXUSR, "not executable: systemd cannot run it"
    # Comments discuss the venv at length; the CODE must never touch it.
    code = re.sub(r"(?m)^\s*#.*$", "", script.read_text())
    assert ".venv" not in code and "python" not in code, (
        "the notifier must not share dependencies with the thing it watches")
    text = script.read_text()
    assert "exit 0" in text


def test_the_notifier_is_silent_without_a_topic(tmp_path: Path) -> None:
    """E92: an unset topic is silence, never an error."""
    proc = subprocess.run([str(DEPLOY / "vss-notify-failure.sh"), "vss.service"],
                          capture_output=True, text=True, timeout=30,
                          env={"PATH": "/usr/bin:/bin"})
    assert proc.returncode == 0
    assert "NTFY_TOPIC is not set" in proc.stderr


def test_the_notifier_posts_the_unit_name_and_exits_zero(tmp_path: Path) -> None:
    """Point it at a file:// -- curl writes the body where it can be read."""
    sink = tmp_path / "posted.txt"
    fake_curl = tmp_path / "curl"
    fake_curl.write_text("#!/bin/sh\ncat > %s\nexit 0\n" % sink)
    fake_curl.chmod(0o755)
    proc = subprocess.run([str(DEPLOY / "vss-notify-failure.sh"), "vss.service"],
                          capture_output=True, text=True, timeout=30,
                          env={"PATH": f"{tmp_path}:/usr/bin:/bin",
                               "NTFY_TOPIC": "a-test-topic"})
    assert proc.returncode == 0
    body = sink.read_text()
    assert "vss.service FAILED" in body
    assert "journalctl --user -u vss.service" in body


def test_a_failing_unit_would_trigger_it(tmp_path: Path) -> None:
    """The wiring end to end, without systemd: the unit's ExecStart, run.

    `vss-failure@.service` runs the script with the failing unit's name as
    its instance. This reproduces that call and asserts the phone would
    learn WHICH unit died -- the one thing a pointer has to carry.
    """
    sink = tmp_path / "posted.txt"
    fake_curl = tmp_path / "curl"
    fake_curl.write_text("#!/bin/sh\ncat > %s\nexit 0\n" % sink)
    fake_curl.chmod(0o755)
    exec_start = next(line for line in (DEPLOY / "vss-failure@.service").read_text().splitlines()
                      if line.startswith("ExecStart="))
    # %h/vss is systemd's specifier for the checkout; fill it in as systemd would.
    argv = (exec_start.removeprefix("ExecStart=").replace("%I", "vss-screen.service")
            .replace("%h/vss", str(DEPLOY.parent)).split())
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=30,
                          env={"PATH": f"{tmp_path}:/usr/bin:/bin",
                               "NTFY_TOPIC": "a-test-topic"})
    assert proc.returncode == 0
    assert "vss-screen.service FAILED" in sink.read_text()


def _posted_for(unit: str, tmp_path: Path) -> str:
    """Run the notifier for `unit` against a fake curl; return the body,
    whitespace-normalised so a wrapped sentence can be asserted whole."""
    sink = tmp_path / f"posted-{unit}.txt"
    fake_curl = tmp_path / "curl"
    fake_curl.write_text("#!/bin/sh\ncat > \"$(dirname \"$0\")/posted-%s.txt\"\nexit 0\n"
                         % unit)
    fake_curl.chmod(0o755)
    proc = subprocess.run([str(DEPLOY / "vss-notify-failure.sh"), unit],
                          capture_output=True, text=True, timeout=30,
                          env={"PATH": f"{tmp_path}:/usr/bin:/bin",
                               "NTFY_TOPIC": "a-test-topic"})
    assert proc.returncode == 0
    return " ".join(sink.read_text().split())


def test_the_notifier_says_what_stopped_for_the_unit_that_stopped(tmp_path: Path) -> None:
    """Backlog B-13: "no report was written for this date" is the nightly
    run's sentence, and it was posted for every unit. vss-overview.service
    dying writes no report because it never writes one; the phone must be
    told what actually stopped."""
    run_sentence = "no report was written for this date"
    assert run_sentence in _posted_for("vss.service", tmp_path)
    assert run_sentence in _posted_for("vss-screen.service", tmp_path)

    page = _posted_for("vss-overview.service", tmp_path)
    assert "vss-overview.service FAILED" in page
    assert run_sentence not in page
    assert "overview page server stopped" in page
    assert "nightly run" in page and "unaffected" in page

    checkin = _posted_for("vss-checkin.service", tmp_path)
    assert run_sentence not in checkin
    assert "check-in did not complete" in checkin

    unknown = _posted_for("vss-future.service", tmp_path)
    assert run_sentence not in unknown
    assert "vss-future.service is not a run unit" in unknown
    # E92 unchanged: the journal pointer still names the unit.
    assert "journalctl --user -u vss-future.service" in unknown


# --- the record the run writes -------------------------------------------


def test_the_run_records_priced_coverage_not_row_count(db: Path) -> None:
    """A night when every fetch failed must not record full coverage."""
    row = HB.begin(db, kind=HB.KIND_NIGHTLY, started_at=NOW, as_of=date(2026, 8, 31))
    HB.finish(db, row, finished_at=NOW, expected=22, covered=3, errors=19)
    last = HB.last_completion(db)
    assert last is not None
    assert last.coverage_line == "3/22 covered (14%)"


def test_finish_on_a_missing_row_is_not_an_error(db: Path) -> None:
    assert HB.finish(db, None, finished_at=NOW) is False


def test_the_readers_never_create_or_write_the_database(tmp_path: Path) -> None:
    """The check-in's unit has no ReadWritePaths. Its reads must not need any.

    Two failures are pinned. A read that CREATES the file breaks the promise
    `--dry-run` makes ("no database row"); a read that opens the file
    read-WRITE fails under `ProtectHome=read-only` and is then reported as
    "no record" -- a phantom outage, which is the one thing a dead man's
    switch may never invent.
    """
    import os
    missing = tmp_path / "absent.sqlite"
    assert HB.last_completion(missing) is None
    assert not missing.exists()

    db = tmp_path / "vss.sqlite"
    record(db, finished=NOW - timedelta(hours=1))
    os.chmod(db, 0o444)
    os.chmod(tmp_path, 0o555)
    try:
        last = HB.last_completion(db)
        assert last is not None and last.completed
        assert HB.report_lines(db, now=NOW) == []
    finally:
        os.chmod(tmp_path, 0o755)
        os.chmod(db, 0o644)


# --- leg 4: the outside observer (owner, 2026-09-01) ---------------------


def test_the_nightly_unit_pings_only_when_the_run_succeeded() -> None:
    """ExecStartPost, not ExecStart= nor OnSuccess=: it runs only after a
    successful ExecStart, which is the whole semantic of the ping."""
    text = (DEPLOY / "vss.service").read_text()
    assert "ExecStartPost=-%h/vss/deploy/vss-ping-healthcheck.sh" in text, (
        "the healthcheck ping is missing, or is not marked `-`")


def test_a_failed_ping_cannot_fail_the_run() -> None:
    """The leading `-` is load-bearing: without it a network blip turns a
    good run into a failed unit and fires the OnFailure pointer."""
    line = next(l for l in (DEPLOY / "vss.service").read_text().splitlines()
                if l.startswith("ExecStartPost="))
    assert line.startswith("ExecStartPost=-")


def test_the_ping_script_is_executable_and_needs_no_venv() -> None:
    script = DEPLOY / "vss-ping-healthcheck.sh"
    assert script.stat().st_mode & stat.S_IXUSR
    code = re.sub(r"(?m)^\s*#.*$", "", script.read_text())
    assert ".venv" not in code and "python" not in code
    assert "exit 0" in code


def test_the_ping_is_silent_without_a_url() -> None:
    """E92: unset is silence, never an error."""
    proc = subprocess.run([str(DEPLOY / "vss-ping-healthcheck.sh")],
                          capture_output=True, text=True, timeout=30,
                          env={"PATH": "/usr/bin:/bin"})
    assert proc.returncode == 0
    assert "HEALTHCHECK_URL is not set" in proc.stderr


def test_the_ping_sends_a_bare_GET_and_no_body(tmp_path: Path) -> None:
    """What leaves the machine is one opaque UUID. Nothing else may."""
    sink = tmp_path / "argv.txt"
    fake_curl = tmp_path / "curl"
    fake_curl.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > {sink}\nexit 0\n')
    fake_curl.chmod(0o755)
    proc = subprocess.run(
        [str(DEPLOY / "vss-ping-healthcheck.sh")], capture_output=True, text=True,
        timeout=30, env={"PATH": f"{tmp_path}:/usr/bin:/bin",
                         "HEALTHCHECK_URL": "https://hc-ping.com/a-uuid"})
    assert proc.returncode == 0
    argv = sink.read_text()
    assert "https://hc-ping.com/a-uuid" in argv
    # No -d/--data of any kind, and no hostname.
    for forbidden in ("-d", "--data", "--data-binary", "-X", "POST"):
        assert f"\n{forbidden}\n" not in argv, f"the ping must not carry {forbidden}"


def test_a_failure_suffix_reaches_the_far_end(tmp_path: Path) -> None:
    """`/fail` is healthchecks.io's own convention; the script passes it
    through so a future caller can signal a failure explicitly."""
    sink = tmp_path / "argv.txt"
    fake_curl = tmp_path / "curl"
    fake_curl.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > {sink}\nexit 0\n')
    fake_curl.chmod(0o755)
    subprocess.run([str(DEPLOY / "vss-ping-healthcheck.sh"), "/fail"],
                   capture_output=True, text=True, timeout=30,
                   env={"PATH": f"{tmp_path}:/usr/bin:/bin",
                        "HEALTHCHECK_URL": "https://hc-ping.com/a-uuid"})
    assert "https://hc-ping.com/a-uuid/fail" in sink.read_text()


def test_the_weekly_unit_loads_tier_B() -> None:
    """Owner, 2026-09-01. A default nobody can see is not a decision."""
    line = next(l for l in (DEPLOY / "vss-screen.service").read_text().splitlines()
                if l.startswith("ExecStart="))
    assert "--tier A --tier B" in line
    assert "--write-pipeline" not in line, "E93: a timer enters no name"
