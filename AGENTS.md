# AGENTS.md

For an AI agent (or any automated session) working in this repository.
Claude Code sessions also read [`CLAUDE.md`](CLAUDE.md), which says how the
work is paced; this file says what is safe to run.

## What this is

`vss` watches a hand-maintained list of companies: it fetches prices, reads
the companies' own reports, values a company from the cash it makes, and
tells the owner's phone when something changed. Two rules bind everything:

1. **The tool measures; the owner decides.** No command writes `status`,
   `fv_base`, `tier` or a sale. An agent does not either, unless the owner
   said so in this session. The tool places no orders and reads no broker
   account.
2. **DATA MISSING is a result.** A figure that is not there is never
   assumed, defaulted or estimated. If you cannot find a figure in the
   company's own filing, say so; do not fill it in.

## Setup

```bash
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m vss doctor        # exit 0, or 1 with the failed check named
```

Always use `.venv/bin/python`. Run from the repository root. Reports go to
stdout, logs to stderr.

## What a command may touch

[`docs/REFERENCE.md`](docs/REFERENCE.md) is generated from the code and
lists every command with its class, its flags, and the form that changes
nothing. It is the source of truth; the lists below are the short version.

### Safe: prints only

Each of these was run and the files it touched were listed: none.

```bash
.venv/bin/python -m vss doctor
.venv/bin/python -m vss run --dry-run                 # may exit 3: a stale close, no report printed
.venv/bin/python -m vss manual --ticker X             # exit 1 = section 5 refuses the store
.venv/bin/python -m vss strike --ticker X --dry-run   # exit 2 = refused, with the reason
.venv/bin/python -m vss history --ticker X
.venv/bin/python -m vss esef --ticker X
.venv/bin/python -m vss nordic --ticker X --reports
.venv/bin/python -m vss sales --dry-run
.venv/bin/python -m vss shadow --dry-run
.venv/bin/python -m vss checkin --no-send
.venv/bin/python -m vss refresh --due --dry-run
.venv/bin/python -m vss prepare --ticker X --dry-run
.venv/bin/python -m vss review --validate <file>
.venv/bin/python -m vss review --schema
.venv/bin/python -m vss screen --universe-report
.venv/bin/python -m vss overview --output /tmp/overview.html
.venv/bin/python tools/warren.py X
.venv/bin/python tools/rough_fv.py X
.venv/bin/python tools/build_queue.py                 # without --write: the diff summary
.venv/bin/python tools/master_list.py --short
.venv/bin/python tools/quotecheck.py                  # without --apply
.venv/bin/python tools/fetch_mfn.py X --dry-run
.venv/bin/python tools/build_manual_reference.py      # prints the reference
```

`.venv/bin/python -m pytest -q` is safe too: it sends nothing and writes
only its own cache and temporary directories.

### Nearly safe: read the note

| Command | What it still does |
|---|---|
| `vss queue --dry-run` | writes no report or state and sends nothing, but a NEW report found for a name is fetched and read into `data/autoread/` (the model is called) |
| `vss xbrl --ticker X` | logs its run in `data/vss.sqlite`; touches no store without `--write` |
| `vss earnings ...` | logs its run in `data/vss.sqlite` and calls the model; sends nothing |
| `vss screen --filter1` / `--filter2` | fetch nothing; write under `data/screener_runs/`. A comparison run sets `--runs-root` |
| `vss watch --no-send` | sends nothing but **advances its cursor**: the next real run will not repeat what it showed |

### Writes the record: only on a task that asks for it

These write under `config/`, `reference/` or `sources/`, which are tracked
in git. A backup is taken where a file is replaced.

- `vss xbrl --annual --write`, `vss appendix --write`,
  `vss manual --merge-draft`, `vss esef --draft`, `vss pdfdraft --write`,
  `vss reference-figures --write`, `vss refresh`, `vss prepare` -- the
  stores and drafts under `config/manual/`
- `vss history ... --write` -- `config/history/`
- `vss strike` -- a run record and a strike document
- `vss nordic --download`, `tools/fetch_mfn.py` -- documents and
  `sources/manifest.json`
- `tools/build_queue.py --write` -- `config/queue.yaml`
- `tools/quotecheck.py --apply X`, `tools/cross_verify.py --apply` -- flip a
  figure to `VERIFIED`
- `vss sales --reconcile` -- `config/sales_reconciled.yaml`

A figure enters a store through a route that records its source and page,
never typed in unchecked. A machine's reading lands as a draft with every
figure `UNVERIFIED`.

### Writes the watchlist: the owner's word only

- `vss screen --rank --write-pipeline` enters new `PIPELINE` names.
- `vss review --record` appends the owner's note and registers a growth
  view.
- Editing `config/watchlist.yaml` by hand: `status`, `fv_base`, `fv_bull`,
  `tier`, `run_record`, `sales:`.

### Reaches the owner's phone: never as a test

`vss run`, `vss queue`, `vss watch`, `vss checkin`, `vss newsdrop`,
`vss screen --weekly` and `tools/nordic_screen.py --notify` POST to ntfy
when they find something. Use the form that does not: `--dry-run`,
`--no-notify` or `--no-send`. The timers run the sending forms; do not start
a unit by hand to "see if it works".

## Never

- Never put a licensed vendor's data, or a figure computed from it, in the
  repository: not in a file, not in a comment, not in a commit message. The
  backtests and the Nordic screen read data under the owner's own licence
  from `data/`, which is gitignored.
- Never commit `~/.config/vss/vss.env` or anything from it.
- Never push, and never start or stop a timer, unless asked.
- Never weaken a test to make it pass, and never skip one that guards a
  generated file.

## Same-commit rules

Two files are generated from the code and a test holds each equal. Change
the code and the file in one commit:

```bash
.venv/bin/python tools/build_manual_reference.py > docs/REFERENCE.md   # a parser, a timer, a tool
.venv/bin/python -m pytest tests/test_manual_reference.py -q

.venv/bin/python -m vss review --schema > config/review/SCHEMA.md      # vss/review.py, review_steps.py
.venv/bin/python -m pytest tests/test_review.py -q
```

A new subcommand or tool needs a facts entry in
`tools/build_manual_reference.py` (what it reads, writes, calls and sends)
or the test fails. A tool that takes arguments exposes `build_parser()`.

## Where things are

| Path | What |
|---|---|
| `vss/` | the program. `rules.py` and `valuation.py` are pure: no I/O, no clock |
| `tools/` | scripts; `tools/backtest/` needs the owner's licensed data |
| `tests/` | `pytest`; fixtures that are vendor data are not shipped and their tests skip |
| `config/watchlist.yaml` | the owner's decisions, one entry per company |
| `config/queue.yaml` | every valued company with bear / base / bull |
| `config/manual/` | the stores: every figure with source, page and status |
| `reference/FRAMEWORK.md` | the rules, two pages. Rulings in `reference/archive/` |
| `reference/run-records/` | every input of every valuation |
| `docs/MANUAL.md` | how to do each task |
| `docs/REFERENCE.md` | every command, flag, timer, variable, file (generated) |
| `docs/EXPLANATION.md` | why each part behaves as it does |
| `data/`, `reports/` | gitignored, regenerable |

Exit codes: `0` completed, `2` a configuration error or a refusal, `130`
interrupted, and per command as `docs/REFERENCE.md` lists them (`vss run`:
`1` coverage short, `3` a dry run refused on a stale close).
