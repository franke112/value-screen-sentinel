# Quick reference

The commands a review day uses, in order. Everything runs from the
repository root with `.venv/bin/python -m vss ...`.

| when | command | writes |
|---|---|---|
| the night before, or the morning | `vss prepare --ticker X` | `reports/prepare/X-<date>.{json,md}`, stores under `config/manual/` (backed up first); never the watchlist |
| the session | `/review X` in Claude Code | `reference/reviews/X/<date>.yaml`, after every answer |
| a step's precedents | type `p` at the step | nothing |
| skip a step | type `s: <reason>` at the step | the skip and its reason |
| the strike | `vss manual --ticker X --asof <date>`, then `tools/strike_*.py` or `vss run --ticker X --dry-run` | nothing |
| the end of the session | `vss review --validate reference/reviews/X/<date>.yaml` | nothing; prints every refusal |
| the owner's record | `vss review --record reference/reviews/X/<date>.yaml` | the note verbatim onto the entry's `notes` (backup first); the growth view where the code keeps growth views, if new or changed; nothing else |
| the schema | `vss review --schema` | prints `config/review/SCHEMA.md`; the file is regenerated from it in the same commit as any change to `vss/review.py` |
| the same commit | `python tools/build_playbook.py && pytest tests/test_playbook.py tests/test_review.py -q` | `docs/playbook/` (gitignored) |

What no command writes: `status`, `fv_base`, `tier`, `mbp`, `stop_price`.
Those are the owner's, by hand, after the record.

The step lists per status and each step's outcome vocabulary are in
`config/review/SCHEMA.md`. The session's rules are `.claude/commands/
review.md`; the walk is `docs/manual/02-workflow.md`.
