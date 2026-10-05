"""`vss.env`: the environment first, then the file systemd already reads.

The bug this closes is not a crash. VSS_SEC_CONTACT was in
`~/.config/vss/vss.env` the whole time, systemd read it, an interactive
shell did not, and so every session at a terminal was told the variable
was unset and asked the owner for it again.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from vss import env
from vss import xbrl as X


@pytest.fixture(autouse=True)
def clear_cache():
    env._CACHE.clear()
    yield
    env._CACHE.clear()


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    env._CACHE.clear()
    return path


# --- precedence --------------------------------------------------------------


def test_the_environment_wins_and_the_file_is_not_even_opened(tmp_path, monkeypatch):
    """A set variable is the answer. The file is a DEFAULT, never an
    override -- `VSS_SEC_CONTACT=x vss xbrl` must do what it says."""
    path = tmp_path / "vss.env"
    write(path, "VSS_SEC_CONTACT=from-the-file\n")
    monkeypatch.setenv("VSS_SEC_CONTACT", "from-the-environment")
    assert env.get("VSS_SEC_CONTACT", path=path) == "from-the-environment"


def test_the_file_answers_when_the_variable_is_unset(tmp_path, monkeypatch):
    path = write(tmp_path / "vss.env", "VSS_SEC_CONTACT=vss/1.0 (a@b.com)\n")
    monkeypatch.delenv("VSS_SEC_CONTACT", raising=False)
    assert env.get("VSS_SEC_CONTACT", path=path) == "vss/1.0 (a@b.com)"


def test_an_empty_variable_counts_as_unset_in_both_places(tmp_path, monkeypatch):
    """A variable exported as "" is what a half-written unit file leaves
    behind. Reading it as a value sends an EMPTY User-Agent to the SEC."""
    path = write(tmp_path / "vss.env", "VSS_SEC_CONTACT=from-the-file\n")
    monkeypatch.setenv("VSS_SEC_CONTACT", "   ")
    assert env.get("VSS_SEC_CONTACT", path=path) == "from-the-file"

    write(path, "VSS_SEC_CONTACT=\n")
    monkeypatch.delenv("VSS_SEC_CONTACT", raising=False)
    assert env.get("VSS_SEC_CONTACT", "fallback", path=path) == "fallback"


def test_a_missing_or_unreadable_file_means_unset_and_never_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("VSS_SEC_CONTACT", raising=False)
    assert env.get("VSS_SEC_CONTACT", path=tmp_path / "nowhere.env") is None
    # A directory where a file is expected is an OSError, not a crash.
    assert env.get("VSS_SEC_CONTACT", path=tmp_path) is None
    assert env.from_file(tmp_path / "nowhere.env") == {}


# --- the file's own dialect --------------------------------------------------


def test_it_parses_what_systemd_and_a_shell_both_accept():
    parsed = env.parse(
        '# a comment\n'
        '\n'
        'NTFY_TOPIC=https://ntfy.sh/abc\n'
        'export VSS_SEC_CONTACT="vss/1.0 (a@b.com)"\n'
        "VSS_OPENROUTER_KEY='sk-or-v1-xyz'\n"
        '  SPACED = value with spaces  \n'
        'not a variable line\n'
        '# VSS_COMMENTED=nope\n'
    )
    assert parsed == {
        "NTFY_TOPIC": "https://ntfy.sh/abc",
        "VSS_SEC_CONTACT": "vss/1.0 (a@b.com)",
        "VSS_OPENROUTER_KEY": "sk-or-v1-xyz",
        "SPACED": "value with spaces",
    }


def test_no_variable_expansion_is_performed():
    """A file that wanted expansion would be a shell script, and this
    would have to be an interpreter for it."""
    assert env.parse("A=$HOME/x\n") == {"A": "$HOME/x"}


def test_a_quote_is_only_stripped_when_it_is_a_PAIR():
    assert env.parse("A=\"unbalanced\n") == {"A": '"unbalanced'}
    assert env.parse("A='a\"b'\n") == {"A": 'a"b'}


# --- the cache ---------------------------------------------------------------


def test_editing_the_file_takes_effect_within_the_same_process(tmp_path, monkeypatch):
    """`user_agent` is called once per HTTP request, so the read is
    cached -- but on the stat, so an edit is never served stale."""
    monkeypatch.delenv("NTFY_TOPIC", raising=False)
    path = tmp_path / "vss.env"
    path.write_text("NTFY_TOPIC=first\n", encoding="utf-8")
    assert env.get("NTFY_TOPIC", path=path) == "first"
    import os
    import time

    path.write_text("NTFY_TOPIC=second\n", encoding="utf-8")
    os.utime(path, (time.time() + 1, time.time() + 1))
    assert env.get("NTFY_TOPIC", path=path) == "second"


def test_the_cache_holds_one_entry_and_does_not_grow(tmp_path, monkeypatch):
    monkeypatch.delenv("NTFY_TOPIC", raising=False)
    for n in range(5):
        path = tmp_path / f"{n}.env"
        path.write_text(f"NTFY_TOPIC=t{n}\n", encoding="utf-8")
        assert env.get("NTFY_TOPIC", path=path) == f"t{n}"
    assert len(env._CACHE) == 1


# --- what it is wired into ---------------------------------------------------


def test_user_agent_reads_the_file_when_the_variable_is_unset(tmp_path, monkeypatch):
    """The whole point: an interactive session no longer has to be told."""
    path = write(tmp_path / "vss.env", "VSS_SEC_CONTACT=vss/1.0 (a@b.com)\n")
    monkeypatch.delenv(X.CONTACT_ENV, raising=False)
    monkeypatch.setattr(env, "ENV_FILE", path)
    assert X.user_agent() == "vss/1.0 (a@b.com)"


def test_an_explicit_argument_still_beats_both(tmp_path, monkeypatch):
    path = write(tmp_path / "vss.env", "VSS_SEC_CONTACT=from-the-file\n")
    monkeypatch.setenv(X.CONTACT_ENV, "from-the-environment")
    monkeypatch.setattr(env, "ENV_FILE", path)
    assert X.user_agent("explicit") == "explicit"


def test_the_refusal_still_fires_with_neither_and_names_both_places(tmp_path, monkeypatch):
    monkeypatch.delenv(X.CONTACT_ENV, raising=False)
    monkeypatch.setattr(env, "ENV_FILE", tmp_path / "nowhere.env")
    with pytest.raises(X.XbrlError) as caught:
        X.user_agent()
    message = str(caught.value)
    assert "VSS_SEC_CONTACT is not set" in message
    assert "vss.env" in message, message
    assert "will not invent one" in message


def test_no_module_reads_these_variables_behind_the_readers_back():
    """Every operational variable in that file goes through `vss.env`.
    A stray `os.environ.get` is the bug coming back."""
    root = Path(__file__).resolve().parent.parent / "vss"
    offenders = []
    for path in sorted(root.glob("*.py")):
        if path.name == "env.py":
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "os.environ.get" in line:
                offenders.append(f"{path.name}:{n}: {line.strip()}")
    assert offenders == [], offenders
