"""`vss doctor` -- is this machine able to run vss? Read-only. Exit 0 or 1.

HANDOFF 2026-11-07 part D. One line per check, OK / WARN / FAIL; any FAIL
exits 1. Nothing is written, created, migrated or fetched: the database is
opened read-only, the snapshot stores are only read, and a secret is never
printed (the SEC contact is shown with its address masked).
"""
from __future__ import annotations

import importlib
import os
import re
import sqlite3
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

OK, WARN, FAIL = "OK", "WARN", "FAIL"
MIN_PYTHON = (3, 11)
REPO = Path(__file__).resolve().parents[1]


@dataclass
class Check:
    name: str
    state: str
    detail: str


def _python() -> Check:
    v = sys.version_info
    ok = (v.major, v.minor) >= MIN_PYTHON
    return Check("python", OK if ok else FAIL,
                 f"{v.major}.{v.minor}.{v.micro}" + ("" if ok else f" (needs {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+)"))


def _imports() -> list[Check]:
    out = []
    for mod, why in (("pypdf", "PDF reading"), ("cryptography", "pypdf's AES (encrypted IR PDFs)"),
                     ("lxml", "inline XBRL / ESEF"), ("openpyxl", "figures appendices"),
                     ("exchange_calendars", "settled closes"), ("requests", "MFN / Nordic feeds"),
                     ("yaml", "config"), ("pandas", "prices")):
        try:
            m = importlib.import_module(mod)
            out.append(Check(f"import {mod}", OK, f"{getattr(m, '__version__', '')} -- {why}".strip(" -")))
        except Exception as exc:  # noqa: BLE001
            out.append(Check(f"import {mod}", FAIL, f"{type(exc).__name__}: {exc} -- {why}"))
    return out


_CONTACT = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def _mask(text: str) -> str:
    return _CONTACT.sub(lambda m: m.group(0)[0] + "***@" + m.group(0).split("@")[1], text)


def _sec_contact(get: Callable[[str], str | None]) -> Check:
    from .xbrl import CONTACT_ENV
    value = get(CONTACT_ENV)
    if not value or not value.strip():
        return Check("VSS_SEC_CONTACT", FAIL, "not set (environment or vss.env); SEC refuses the call")
    if not _CONTACT.search(value):
        return Check("VSS_SEC_CONTACT", FAIL, f"set but holds no email address: {_mask(value)!r}")
    return Check("VSS_SEC_CONTACT", OK, _mask(value.strip()))


def _env_file(path: Path) -> Check:
    if not path.exists():
        return Check("vss.env", WARN, f"{path} does not exist (only the environment is read)")
    st = path.stat()
    mode = stat.S_IMODE(st.st_mode)
    problems = []
    if mode != 0o600:
        problems.append(f"mode {mode:o}, not 600")
    if st.st_uid != os.getuid():
        problems.append(f"owner uid {st.st_uid}, not {os.getuid()}")
    return Check("vss.env", FAIL if problems else OK,
                 "; ".join(problems) if problems else f"{path} mode 600, owned by this user")


def _ntfy(get: Callable[[str], str | None]) -> Check:
    topic = get("NTFY_TOPIC")
    return Check("ntfy", OK if topic else WARN,
                 "NTFY_TOPIC set" if topic else "NTFY_TOPIC not set: no phone notifications (a warning only)")


def _db_tables(db: Path) -> Check:
    from .store import SCHEMA
    want = set(re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", SCHEMA))
    if not db.exists():
        return Check("vss.sqlite", WARN, f"{db} does not exist yet (made by the first run)")
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        have = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
    except sqlite3.Error as exc:
        return Check("vss.sqlite", FAIL, f"{db}: not readable ({exc})")
    missing = sorted(want - have)
    # a table the store would create on its next connect is not a fault;
    # it is reported so a reader knows the file predates it
    return Check("vss.sqlite", WARN if missing else OK,
                 (f"{len(have & want)}/{len(want)} tables; not yet made (the next run makes them): "
                  + ", ".join(missing)) if missing else f"{len(want)} tables as the store declares")


def _snapshots(root: Path) -> Check:
    from . import snapshot as S
    try:
        days = S.available_snapshots(root)
    except Exception as exc:  # noqa: BLE001
        return Check("snapshots", FAIL, f"{root}: {type(exc).__name__}: {exc}")
    if not days:
        return Check("snapshots", WARN, f"{root}: none yet")
    newest = days[-1]
    try:
        S.read_manifest(S.snapshot_path(newest, root))
        fpath = S.fundamentals_path(newest, root)
        note = ""
        if fpath.exists():
            S.read_fundamentals_manifest(fpath)
            note = ", fundamentals store reads"
    except Exception as exc:  # noqa: BLE001
        return Check("snapshots", FAIL, f"{newest}: not readable ({type(exc).__name__}: {exc})")
    return Check("snapshots", OK, f"{len(days)} stored, newest {newest} reads{note}")


def _timers(runner=None) -> Check:
    from .heartbeat import timer_lines
    try:
        lines = timer_lines(runner=runner) if runner else timer_lines()
    except Exception as exc:  # noqa: BLE001
        return Check("timers", WARN, f"cannot ask systemd: {type(exc).__name__}: {exc}")
    return Check("timers", WARN if lines else OK,
                 "; ".join(lines) if lines else "every watched timer enabled and active")


def _checkout(repo: Path = REPO, unit: Path | None = None) -> Check:
    unit = unit or repo / "deploy" / "vss.service"
    if not unit.exists():
        return Check("checkout", WARN, f"{unit} not found")
    m = re.search(r"^WorkingDirectory=(.+)$", unit.read_text(encoding="utf-8"), re.M)
    if not m:
        return Check("checkout", WARN, f"{unit.name} names no WorkingDirectory")
    wd = Path(m.group(1).strip().replace("%h", str(Path.home())))
    ok = wd.resolve() == repo.resolve()
    return Check("checkout", OK if ok else FAIL,
                 f"{repo} is where {unit.name} runs" if ok
                 else f"the units run in {wd}, this checkout is {repo}: the timers run other code")


def run(*, get=None, env_file: Path | None = None, db: Path | None = None,
        snapshot_root: Path | None = None, timer_runner=None, repo: Path = REPO) -> list[Check]:
    from . import env as E
    from .snapshot import SNAPSHOT_ROOT
    get = get or E.get
    checks = [_python(), *_imports(), _sec_contact(get), _env_file(env_file or E.ENV_FILE),
              _ntfy(get), _db_tables(db or repo / "data" / "vss.sqlite"),
              _snapshots(snapshot_root or SNAPSHOT_ROOT), _timers(timer_runner), _checkout(repo)]
    return checks


def render(checks: list[Check]) -> str:
    out = [f"{c.state:4s}  {c.name:22s} {c.detail}" for c in checks]
    fails = sum(c.state == FAIL for c in checks)
    warns = sum(c.state == WARN for c in checks)
    out.append(f"\n{len(checks)} checks: {fails} FAIL, {warns} WARN")
    return "\n".join(out)


def exit_code(checks: list[Check]) -> int:
    return 1 if any(c.state == FAIL for c in checks) else 0
