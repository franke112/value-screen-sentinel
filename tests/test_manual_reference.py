"""docs/REFERENCE.md is generated, and this file holds it equal to the code.

The command reference is read off the argument parsers and deploy/, with a
hand-written table per command (what it reads, writes, calls and sends) in
tools/build_manual_reference.py. Before this the manual described 16 of 25
subcommands, named a queue message the code no longer sent and listed four
of ten timers (audit 2026-11-09). A page nobody regenerates goes wrong the
same way again, so:

* the file must be exactly what the tool prints;
* a subcommand or a tool without a facts entry fails, and so does an entry
  for something that is gone;
* a flag a facts entry names must exist on that command;
* every argument must say what it does.

The same-commit rule (CLAUDE.md):

    .venv/bin/python tools/build_manual_reference.py > docs/REFERENCE.md
    .venv/bin/python -m pytest tests/test_manual_reference.py -q
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _tool():
    name = "build_manual_reference"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "tools" / "build_manual_reference.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


REF = _tool()
COMMANDS = REF.vss_commands()
TOOL_FILES = REF.tool_files()


def test_the_file_is_what_the_tool_prints():
    assert REF.OUTPUT.exists(), (
        "docs/REFERENCE.md is missing: run "
        ".venv/bin/python tools/build_manual_reference.py > docs/REFERENCE.md")
    assert REF.OUTPUT.read_text(encoding="utf-8") == REF.render(), (
        "docs/REFERENCE.md is not what the code generates. Regenerate it in "
        "the same commit: .venv/bin/python tools/build_manual_reference.py "
        "> docs/REFERENCE.md")


def test_every_subcommand_has_a_facts_entry_and_none_is_orphaned():
    defined = {name for name, _, _ in COMMANDS}
    assert defined - set(REF.COMMANDS) == set(), "a command nobody documented"
    assert set(REF.COMMANDS) - defined == set(), "facts for a command that is gone"


def test_every_tool_has_a_facts_entry_and_none_is_orphaned():
    on_disk = {p.name for p in TOOL_FILES}
    assert on_disk - set(REF.TOOLS) == set(), "a tool nobody documented"
    required = {name for name, facts in REF.TOOLS.items() if not facts.optional}
    assert required - on_disk == set(), "facts for a tool that is gone"


@pytest.mark.parametrize("path", TOOL_FILES, ids=lambda p: p.name)
def test_a_tool_that_takes_arguments_exposes_its_parser(path):
    """`--help` on a tool with no parser was read as a ticker (rough_fv.py)."""
    source = path.read_text(encoding="utf-8")
    if "argparse" in source or "sys.argv" in source:
        assert "def build_parser" in source, (
            f"tools/{path.name} reads arguments without a build_parser(): "
            f"the reference cannot list its flags")


def _parsers():
    for name, _, parser in COMMANDS:
        yield f"vss {name}", parser, REF.COMMANDS.get(name)
    for path in TOOL_FILES:
        parser = REF.tool_parser(path)
        if parser is not None:
            yield f"tools/{path.name}", parser, REF.TOOLS.get(path.name)


PARSERS = list(_parsers())


@pytest.mark.parametrize("label,parser,facts", PARSERS, ids=[p[0] for p in PARSERS])
def test_every_argument_says_what_it_does(label, parser, facts):
    for action in parser._actions:
        if isinstance(action, argparse._HelpAction):
            continue
        assert action.help and action.help.strip(), (
            f"{label}: {action.option_strings or action.dest} has no help")


@pytest.mark.parametrize("label,parser,facts", PARSERS, ids=[p[0] for p in PARSERS])
def test_a_flag_the_facts_name_exists_on_that_command(label, parser, facts):
    """A renamed flag must not survive in the prose beside the table."""
    assert facts is not None, label
    known = {s for a in parser._actions for s in a.option_strings}
    prose = " ".join((facts.reads, facts.writes, facts.network, facts.sends,
                      facts.exits, facts.safe))
    named = set(re.findall(r"(?<![\w-])--[a-z][a-z0-9-]*", prose))
    assert named - known == set(), f"{label}: the facts name a flag it lacks"


def test_every_command_says_what_it_sends_and_what_changes_nothing():
    for name, facts in {**REF.COMMANDS, **REF.TOOLS}.items():
        assert facts.what and facts.reads and facts.writes and facts.network, name
        assert facts.sends, name
        assert facts.classes, name
        if REF.SENDS in facts.classes:
            assert facts.sends != "nothing", f"{name} is classed as sending"
        if facts.classes == (REF.READ_ONLY,):
            assert facts.safe == "always", name


def test_every_timer_names_a_service_that_runs_something():
    rows = REF.timers()
    assert rows, "no timer found under deploy/"
    for unit, when, commands, _ in rows:
        assert when, f"{unit} has no OnCalendar"
        assert commands, f"{unit}'s service has no ExecStart"


def test_the_page_carries_no_absolute_path():
    """The page must be the same on any checkout, private or public."""
    page = REF.render()
    assert str(ROOT) not in page
    assert "/home/" not in page
