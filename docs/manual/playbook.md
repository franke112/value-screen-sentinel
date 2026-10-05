# The decision playbook

`docs/playbook/` is a generated static site: one HTML file per step of
the decision chain, one per name, an index that is the funnel as
navigation, a rulings page and a git-log page. It opens from disk
(`file://`), needs no server and no network, works with JavaScript off,
and reads on a phone. It is gitignored; the generator, its templates and
its tests are tracked.

## Build

    .venv/bin/python tools/build_playbook.py            # writes docs/playbook/
    .venv/bin/python tools/build_playbook.py --out DIR  # somewhere else
    make playbook                                       # the same, where make exists

The build takes a few seconds and is idempotent. Open
`docs/playbook/index.html`.

## When to rebuild

After ANY of these, in the same commit (CLAUDE.md, "same-commit rule"):

- a ruling written into `reference/FRAMEWORK-EDITS.md` or an edit to
  `reference/FRAMEWORK.md`;
- a verdict: a status, `notes:`, `fv_base`, `tier` or `growth:` change on
  `config/watchlist.yaml`, or a row in `config/shadow_book.csv`;
- a CLI change: a subcommand, a flag or a help string in `vss/__main__.py`;
- a new strike, intake, briefing, reading or run record under `reports/`
  or `reference/`.

A new numbered entry in FRAMEWORK-EDITS fails `tests/test_playbook.py`
until it is placed in `tools/playbook/placement.py` -- on exactly one
step, or in `CROSS_CUTTING`. That is deliberate: a ruling nobody has placed
is a ruling the playbook would hide.

## What it reads, and what it never does

| Source | Used for |
|---|---|
| `reference/FRAMEWORK.md` | the sections quoted on each step |
| `reference/FRAMEWORK-EDITS.md` | every E, B, C, F and settled B as a Y-statement, at the step where it binds; superseded ones under a fold |
| `config/watchlist.yaml` | which name sits at which step; the owner's notes, verbatim; the registered growth view (the anchoring guard reads this) |
| `config/shadow_book.csv`, `reports/`, `reference/`, the git log | precedents: one line per prior name at a step, linking to the file |
| the CLI's own argparse help | every command shown, so a flag is never stale |
| `vss/rules.py`, `vss/overview.py`, module docstrings | the code's own sequence and constants, for the disagreement panel |

The generator composes no verdict. Where a verdict appears it is the
owner's, quoted. Where FRAMEWORK.md and the code disagree, the index shows
both and flags it; it does not pick.

## The anchoring guard

On the seven section-5 and pre-registration steps (`basis`, `flow`,
`net-debt`, `divisor`, `growth-view`, `strike`, `tier-mbp`) no prior fair
value, growth view, MBP or tier is shown -- not another name's, not the
current name's own, not one quoted inside a ruling -- until the current
name's watchlist entry carries a `growth:` block with a `registered` date.
Without one the page says "register your view first" and nothing else in
those places. The plain step page (no name) is always guarded; open the
step from a name whose view is registered. `tests/test_playbook.py` holds
this with a fixture.

## A missing source

On a fresh clone `reports/` and `config/shadow_book.csv` may be absent and
the git log may be unavailable. The build still succeeds; the index lists
what is missing under "What is missing on this machine".
