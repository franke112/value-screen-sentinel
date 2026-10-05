"""Operational settings: the ENVIRONMENT first, then `~/.config/vss/vss.env`.

WHY THIS EXISTS. The nightly units are started by systemd with
`EnvironmentFile=%h/.config/vss/vss.env`, so `VSS_SEC_CONTACT`,
`NTFY_TOPIC` and `VSS_OPENROUTER_KEY` are set for every scheduled run and
for nothing else. An interactive shell does not read that file, so a
session at a terminal saw them unset, and every session asked the owner
for them again. **The file was never missing; only systemd was reading
it.** This module makes the tool read it too.

PRECEDENCE, AND IT IS THE ENVIRONMENT'S. A variable that IS set in the
environment wins outright and the file is not opened. The file answers
only where the variable is unset or empty, which makes it a default and
never an override: `VSS_SEC_CONTACT=... vss xbrl ...` still does exactly
what it says, and a systemd unit's own EnvironmentFile still wins over a
stale copy in a home directory.

WHAT IS NEVER DONE HERE. **Nothing in this module is written, logged or
printed.** The file holds an API key; it is read, the value is handed to
the caller, and it does not reach a log line, an exception message or a
report. It is also NEVER written: `~/.config/vss/vss.env` is the owner's
file, outside the repository, and deliberately outside every tracked
path -- `deploy/vss.env.example` is the tracked thing and it carries no
values.

A MISSING OR UNREADABLE FILE IS NOT AN ERROR. It means the variable is
unset, which is the state the caller already knows how to describe. This
module raises nothing.
"""

from __future__ import annotations

import os
from pathlib import Path

#: The file systemd already reads. Same path, and the only one.
ENV_FILE = Path.home() / ".config" / "vss" / "vss.env"

#: (resolved path, mtime_ns, size) -> parsed mapping. `user_agent` is
#: called once per HTTP request in a fetch loop, and re-reading a file
#: per request to answer the same question is waste. The stat triple is
#: the key, so editing the file takes effect within the same process.
_CACHE: dict[tuple[str, int, int], dict[str, str]] = {}


def parse(text: str) -> dict[str, str]:
    """Parse a systemd `EnvironmentFile`, which is also shell-sourceable.

    The file's own header documents both uses -- systemd reads it, and a
    shell may `set -a; . vss.env; set +a` -- so both spellings are
    accepted: a bare `KEY=VALUE` and an `export KEY=VALUE`. Surrounding
    single or double quotes are stripped, as systemd strips them.

    NO VARIABLE EXPANSION IS PERFORMED. `$HOME` stays four characters; a
    file that wanted expansion would be a shell script and this would be
    an interpreter for it.
    """
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        if not key or not key.replace("_", "").isalnum():
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        out[key] = value
    return out


def from_file(path: Path | None = None) -> dict[str, str]:
    """The file's mapping, or an empty one. Never raises, never logs."""
    target = Path(path) if path is not None else ENV_FILE
    try:
        stat = target.stat()
        key = (str(target), stat.st_mtime_ns, stat.st_size)
        cached = _CACHE.get(key)
        if cached is None:
            cached = parse(target.read_text(encoding="utf-8"))
            _CACHE.clear()          # one file, one entry; never grows
            _CACHE[key] = cached
        return cached
    except OSError:                 # absent, unreadable, a directory
        return {}
    except Exception:               # noqa: BLE001 -- a decode error is "unset"
        return {}


def get(name: str, default: str | None = None, *,
        path: Path | None = None) -> str | None:
    """`name` from the environment, else from the env file, else `default`.

    An empty or whitespace-only value counts as UNSET in both places: a
    variable exported as "" is the shape a half-written unit file leaves
    behind, and treating it as a value would send an empty User-Agent to
    the SEC rather than saying the contact is missing.
    """
    value = os.environ.get(name)
    if value and value.strip():
        return value
    value = from_file(path).get(name)
    if value and value.strip():
        return value
    return default
