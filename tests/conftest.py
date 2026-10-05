"""Fixtures every test in this directory gets.

THE POINT OF THE AUTOUSE FIXTURE BELOW. `screen.filter1` reads the vendor
SECTOR and INDUSTRY strings that E51's and E96's step-0 limbs decide on from
`data/vss.sqlite` (CODE-REVIEW-2026-09-01 D3), and that path is the REAL
database on this machine. A test that does not say otherwise would therefore
assert against 838 live classifications that change whenever the screener
runs — the coupling `CODE-REVIEW-2026-09-01` C2 names, arriving in a second
place the moment the fix landed.

So every test starts with an EMPTY durable table in `tmp_path`. A test that
wants strings in it puts them there itself and is explicit about it.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_env_file(tmp_path: Path, monkeypatch) -> Path:
    """Point `vss.env.ENV_FILE` at `tmp_path`, never at the owner's own.

    THE REASON IS THE TEST THAT WOULD HAVE GONE GREEN WRONGLY.
    `test_xbrl.py` deletes VSS_SEC_CONTACT from the environment and
    asserts the refusal. Once `user_agent` also consults
    `~/.config/vss/vss.env`, that test passes or fails depending on
    whether the MACHINE RUNNING IT happens to have a contact on disk --
    green on the owner's VPS, red in CI, and green for the wrong reason
    either way. The same file holds an API key, and no test should be
    able to read it.

    So every test starts with NO env file. A test that wants one writes
    it into `tmp_path` and passes the path explicitly.
    """
    from vss import env

    path = tmp_path / "vss.env"
    monkeypatch.setattr(env, "ENV_FILE", path)
    env._CACHE.clear()
    return path


@pytest.fixture(autouse=True)
def isolated_vendor_strings(tmp_path: Path, monkeypatch) -> Path:
    """Point the durable vendor-string table at `tmp_path`, not `data/`."""
    from vss import screen, vendorstrings

    path = tmp_path / "vendor-strings.sqlite"
    monkeypatch.setattr(vendorstrings, "DB_PATH", path)
    monkeypatch.setattr(screen, "DB_PATH", path)
    # `DB_PATH` was read at import time into each keyword-only default, so
    # rebinding the module attribute alone does not reach them. `setitem`
    # rather than assignment, so monkeypatch puts them back afterwards.
    for function in (screen.filter1, screen.filter2, screen.rank,
                     screen.fetch_fundamentals):
        monkeypatch.setitem(function.__kwdefaults__, "db_path", path)
    return path
