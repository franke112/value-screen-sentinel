"""HANDOFF D: vss doctor is read-only and exits 0 or 1."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from vss import doctor as D


def _get(values):
    return lambda name: values.get(name)


def test_the_contact_is_checked_and_masked():
    c = D._sec_contact(_get({"VSS_SEC_CONTACT": "vss/1.0 (someone@example.com)"}))
    assert c.state == D.OK and "someone" not in c.detail and "s***@example.com" in c.detail
    assert D._sec_contact(_get({})).state == D.FAIL
    assert D._sec_contact(_get({"VSS_SEC_CONTACT": "vss/1.0"})).state == D.FAIL


def test_the_env_file_must_be_600(tmp_path):
    f = tmp_path / "vss.env"
    f.write_text("X=1\n")
    os.chmod(f, 0o644)
    assert D._env_file(f).state == D.FAIL
    os.chmod(f, 0o600)
    assert D._env_file(f).state == D.OK
    assert D._env_file(tmp_path / "none").state == D.WARN


def test_the_database_is_opened_read_only(tmp_path):
    db = tmp_path / "vss.sqlite"
    assert D._db_tables(db).state == D.WARN and not db.exists()      # nothing created
    sqlite3.connect(db).execute("CREATE TABLE run_metrics (x)").connection.commit()
    before = db.read_bytes()
    c = D._db_tables(db)
    assert c.state == D.WARN and "not yet made" in c.detail
    assert db.read_bytes() == before


def test_a_checkout_the_units_do_not_run_is_a_fail(tmp_path):
    unit = tmp_path / "vss.service"
    unit.write_text("[Service]\nWorkingDirectory=%h/vss\n")
    assert D._checkout(repo=tmp_path, unit=unit).state in (D.FAIL, D.OK)
    unit.write_text(f"[Service]\nWorkingDirectory={tmp_path}\n")
    assert D._checkout(repo=tmp_path, unit=unit).state == D.OK
    unit.write_text("[Service]\nWorkingDirectory=/nowhere/else\n")
    assert D._checkout(repo=tmp_path, unit=unit).state in (D.FAIL, D.WARN)


def test_a_checkout_elsewhere_without_installed_timers_is_only_a_hint(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    unit = tmp_path / "vss.service"
    unit.write_text("[Service]\nWorkingDirectory=/nowhere/else\n")
    assert D._checkout(repo=tmp_path, unit=unit).state == D.WARN
    installed = tmp_path / "home" / ".config" / "systemd" / "user"
    installed.mkdir(parents=True)
    (installed / "vss.service").write_text("x")
    assert D._checkout(repo=tmp_path, unit=unit).state == D.FAIL


def test_exit_code():
    assert D.exit_code([D.Check("a", D.OK, ""), D.Check("b", D.WARN, "")]) == 0
    assert D.exit_code([D.Check("a", D.FAIL, "")]) == 1


def test_warren_says_one_line_without_a_contact(monkeypatch, capsys):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "warren", Path(__file__).resolve().parents[1] / "tools" / "warren.py")
    W = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(W)
    from vss import env
    monkeypatch.setattr(env, "get", lambda name, default=None, **kw: None)
    assert W.main(["KO"]) == 2
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1 and "VSS_SEC_CONTACT" in out[0]
