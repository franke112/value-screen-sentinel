# The workflow: prepare, review, record

This page is the order things happen in when a name is reviewed. The
playbook (`docs/manual/playbook.md`) is the map; this is the walk.

## 1. `vss prepare` -- the machine's work before the owner sits down

    .venv/bin/python -m vss prepare --ticker NVR

Route, fetch, fill, compute, verification list, human-step context, and a
"Where this name stands" section that names the playbook step the name is
on and, for a name already struck, the step to resume at. The report is
`reports/prepare/<TICKER>-<date>.json` and `.md`. It never writes the
watchlist and never writes fv_base, tier, mbp, stop_price or status.

## 2. `/review TICKER` -- the review session

A Claude Code slash command (`.claude/commands/review.md`). It refuses to
start without today's prepare report unless the owner says to proceed
without it. It reads the step list from `tools/playbook/steps.py`, the
rulings per step from `tools/playbook/placement.py` and the status's walk
from `vss/review.py`, and then asks the steps ONE AT A TIME:

- where we are (step N of M), what the prepare report found for the step,
  the governing rulings as one-line Y statements, the question in one
  sentence -- then it stops and waits;
- `p` shows the precedents for the step; `s: <reason>` skips it;
- the verification step presents the report's list one figure at a time,
  with file and page, and records VERIFIED or the corrected value on the
  owner's word only;
- the growth-view step takes base, bear and bull with reasons BEFORE any
  implied number, fair value, MBP or prior valuation of the name is shown,
  and writes `growth_view.registered_at` at that instant;
- the strike is run through `vss manual` and the name's `tools/strike_*.py`
  or `vss run --dry-run`, shown as printed; then tier, verdict, and for
  WATCH-PRICED the conditions and stop are asked one by one;
- the session never proposes a verdict, tier, fair value or growth rate.
  Asked "what would you do", it restates the question.

A name the prepare report says is already struck resumes at `tier-mbp` or
`verdict`, with the earlier steps recorded as skipped and the reason
stated. A name flagged INCONSISTENT WITH E27 is walked from the verdict
step until its status is consistent.

The file it writes after every answer is
`reference/reviews/<TICKER>/<date>.yaml`, shape in
`config/review/SCHEMA.md`.

## 3. `vss review --validate`, then `--record`

    .venv/bin/python -m vss review --validate reference/reviews/NVR/2026-09-13.yaml
    .venv/bin/python -m vss review --record   reference/reviews/NVR/2026-09-13.yaml

`--validate` prints every refusal (SCHEMA.md lists them) and writes
nothing. `--record` validates, backs up `config/watchlist.yaml`, appends
the owner's note verbatim to the entry's `notes`, registers the growth
view where the code keeps growth views (`reference/growth-views/
<TICKER>.md` and the entry's `growth:` block) when it is new or changed,
re-reads the file, and restores the backup if anything else moved. It
never writes status, fv_base, tier, mbp or stop_price: the owner writes
those by hand, after the record.

## 4. The same commit

The playbook reads `reference/reviews/` as a precedent source, so each
answered step lands on its own step page with the owner's text. Rebuild
it in the same commit as the review file and the record (CLAUDE.md,
same-commit rule):

    .venv/bin/python tools/build_playbook.py && .venv/bin/python -m pytest tests/test_playbook.py tests/test_review.py -q
