# vss -- the technical manual

`vss` watches a hand-maintained list of companies. Every night it fetches
prices, reads new reports, holds each valued company against its value and
tells your phone only when something changed. What a company is worth is
decided in a review, by a person, with every figure traced to the company's
own filings.

Its defining rule: **stale or unresolved data produces a blocker, never a
verdict.** The tool would rather say it cannot judge than judge on bad data.

This manual has four parts, and you rarely need more than one at a time.

| Part | Read it when |
|---|---|
| [1. Getting started](#part-1----getting-started) | once, to install and make the first run |
| [2. How to](#part-2----how-to) | you have a task: take a name in, value it, read a report |
| [3. Reference](#part-3----reference) | you need the exact fields, messages and states |
| [4. Explanation](#part-4----explanation) | you want to know *why* a command behaves as it does |

Beside it: **[`REFERENCE.md`](REFERENCE.md)** lists every command, flag,
timer, environment variable and file -- it is generated from the code and a
test holds it equal, so where this manual and that page disagree, that page
is right. [`CHANGELOG.md`](CHANGELOG.md) says what changed and when. New
here? Start with the [README](../README.md) and the
[glossary](../GLOSSARY.md). An AI agent working in the repository reads
[`AGENTS.md`](../AGENTS.md).

Every command below is run from the repository root with the virtual
environment's interpreter: `.venv/bin/python -m vss ...` or
`.venv/bin/python tools/<tool>.py ...`.

---

## Part 1 -- Getting started

Do this once. From a fresh clone it takes about five minutes: on 2026-11-07
(Debian 13, Python 3.13) clone and install took 29 seconds and the first
full run over 43 names 14 seconds.

### 1.1 Install

Linux, Python 3.11 or later, a network connection. `vss` is built and tested
on Python 3.13.

```bash
git clone https://github.com/franke112/value-screen-sentinel.git ~/vss
cd ~/vss
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Clone to **`~/vss`** if you mean to use the timers: the units in `deploy/`
name that path (`%h/vss`).

If `python3 -m venv` fails with *"ensurepip is not available"* (Debian
splits it into its own package), either `sudo apt install python3-venv`, or
without root:

```bash
python3 -m venv --without-pip .venv
curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
.venv/bin/python /tmp/get-pip.py
.venv/bin/python -m pip install -r requirements.txt
```

### 1.2 Settings

```bash
mkdir -p ~/.config/vss
cp deploy/vss.env.example ~/.config/vss/vss.env
chmod 600 ~/.config/vss/vss.env
$EDITOR ~/.config/vss/vss.env
```

Only `VSS_SEC_CONTACT` is needed to begin: SEC asks every automated caller
for a contact address, and without one the US routes are not called. A model
key (`VSS_OPENROUTER_KEY`) is needed only for reading reports with a model;
a phone topic (`NTFY_TOPIC`) only for messages. Every variable is in
[REFERENCE.md, Environment variables](REFERENCE.md#environment-variables).
The file is read by the commands themselves and by the timers; a variable
set in the shell wins over it.

### 1.3 The first run

Nothing below sends a message or changes a decision. (The one side effect:
if a queue name has published a new report, `vss queue --dry-run` fetches
and reads it into `data/autoread/`, which needs the model key.)

```bash
.venv/bin/python -m vss doctor             # can this machine run vss? exit 0 or 1
.venv/bin/python -m vss run --dry-run      # the nightly report, on the author's watchlist
.venv/bin/python tools/warren.py KO AAPL   # quality tests and a value for any US filer
.venv/bin/python -m vss queue --dry-run    # every valued name against its lines
```

What to expect:

- `vss doctor` prints one line per check and exits `1` if anything FAILs. A
  missing ntfy topic is a warning, not a failure.
- `vss run --dry-run` prints `DRY RUN — nothing written` and then the
  report. It still fetches prices. **It can refuse:** if a held name, or one
  with a buy line, has a close more than one session old, it prints no
  report and exits `3` -- a trigger check on a stale close is the one
  failure that loses money silently. Run it again after the market's data
  has settled.
- `tools/warren.py` prints bear / base / bull per share and four quality
  tests. It is a *screen*: a name that passes is worth a hand read, never a
  buy.

### 1.4 Make it yours

The watchlist and the queue in the repository are **the author's**, kept as
a worked example. Start your own:

```bash
cp config/watchlist.example.yaml config/watchlist.yaml
cp config/queue.example.yaml config/queue.yaml
$EDITOR config/watchlist.yaml
```

**The example's two entries are dummies.** No vendor knows `EXMPL.ST` or
`DUMMY.AS`; a run on the file as it stands fetches nothing, and a dry run
refuses with exit `3`. Replace them with real symbols first. The fields are
in [3.2 The watchlist](#32-the-watchlist); taking a real company in is
[2.3](#23-take-a-us-company-in) or [2.4](#24-take-a-nordic-company-in).

### 1.5 Run it every night

Optional. User-level systemd, no root except the last line:

```bash
mkdir -p ~/.config/systemd/user
cp deploy/*.service deploy/*.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now vss.timer vss-queue.timer vss-watch.timer \
    vss-mfn.timer vss-screen.timer vss-checkin.timer
sudo loginctl enable-linger $USER          # so the timers fire when you are logged out
```

What each timer runs, and when, is in
[REFERENCE.md, Timers](REFERENCE.md#timers). Enable only what you use:
`vss-newsdrop.timer` is a shadow screen, and `vss-eodhd*.timer` and
`vss-nordic-screen.timer` need a paid data licence of your own
([2.14](#214-the-nordic-screen-and-the-backtests)). More in
[2.11](#211-schedule-it-and-reach-your-phone).

---

## Part 2 -- How to

Each task is a short sequence of commands. Flags not shown here are in
[REFERENCE.md](REFERENCE.md); the reasons are in
[EXPLANATION.md](EXPLANATION.md).

### 2.1 Read the nightly report

```bash
.venv/bin/python -m vss run                      # fetch, report, persist
.venv/bin/python -m vss run --dry-run            # print the report, write nothing
.venv/bin/python -m vss run --ticker VOLV-B.ST   # one name only
.venv/bin/python -m vss run > today.md 2> today.log
```

The report goes to stdout and every log line to stderr. A full run writes
`reports/<date>.md`, one row per name in `data/vss.sqlite`, and regenerates
`reports/OVERVIEW.html`. A `--ticker` run is a **partial run** and says so
throughout; it writes `reports/<date>.<TICKER>.md` and can never overwrite
the day's full report.

Read it top down: **NEEDS OWNER** (what a report-date refresh left waiting),
the data-freshness line, **BLOCKERS** (names that got no verdict, and why),
**ACTIONS** (every verdict that fired), then the full table. The states are
in [3.5](#35-the-nightly-report).

| Exit code | Meaning |
|---|---|
| `0` | the run completed. A ticker that errored is an ERROR row, not a failure |
| `1` | coverage short: too few names were priced. The run does not reset the staleness clock and sends no healthcheck ping |
| `2` | the watchlist is missing or malformed, or `--ticker` is not on it |
| `3` | a `--dry-run` refused: a held name, or one with an MBP, has a close more than one session old |
| `130` | interrupted |

### 2.2 Look at a company quickly

```bash
.venv/bin/python tools/warren.py KO PEP CTSH         # any US filer, from SEC's tagged facts
.venv/bin/python tools/rough_fv.py EVO.ST UMG.AS     # any listing Yahoo covers
```

Both print bear / base / bull per share and write nothing. `warren.py` adds
the four quality tests (Q1-Q4) and the hard kills the tagged quarters can
show. Both are **screens**: no normalisation of working capital, no deal
programme, no cycle, no growth derived from the company's own history. A
value from either is a reason to do the full read below, never a value to
buy on. The master list marks them `[maskin]` and `[grov]` for that reason.

### 2.3 Take a US company in

A US filer's figures come from SEC as tagged facts: no PDF, no model.

```bash
# 1. the store: annual cash flow, capex, shares, net debt -> config/manual/CPRT.yaml
.venv/bin/python -m vss xbrl --ticker CPRT --cik 900075 --annual --quote-currency USD
.venv/bin/python -m vss xbrl --ticker CPRT --cik 900075 --annual --quote-currency USD --write

# 2. the multi-year history the growth and quality rules read
.venv/bin/python -m vss history --ticker CPRT --xbrl --cik 900075 --write

# 3. may section 5 read the store? exit 0 yes, 1 refused (and it says why)
.venv/bin/python -m vss manual --ticker CPRT
```

Then, by hand, **register your growth view before any value is struck**:
write `reference/growth-views/CPRT.md` in your own words, and enter the name
on the watchlist as `INTAKE` with its `growth:` block ([3.2](#32-the-watchlist)).
The order matters: a growth rate chosen after seeing what it implies is not
a view. Then value it ([2.5](#25-value-a-company)).

`--quote-currency` is for a ticker that is *not* on the watchlist yet. The
CIK is the filer's number at SEC; find it on SEC's company search.

### 2.4 Take a Nordic company in

There is no tagged-facts endpoint for most Nordic issuers, so the figures
come out of the issuer's own reports. Three routes, best first.

```bash
# the documents: annual and interim reports as PDF, and the ESEF package
.venv/bin/python tools/fetch_mfn.py EVO.ST --kinds annual,interim
.venv/bin/python -m vss nordic --ticker EVO.ST --reports        # or the exchange feed

# route A -- the annual report's own tagged facts (ESEF), into a DRAFT
.venv/bin/python -m vss esef --ticker EVO.ST --draft
.venv/bin/python -m vss manual --ticker EVO.ST --merge-draft --dry-run
.venv/bin/python -m vss manual --ticker EVO.ST --merge-draft

# route B -- a model reads the statement pages twice, into a DRAFT (needs the model key)
.venv/bin/python -m vss pdfdraft --ticker ZZ-B.ST --period 2026-Q2 \
    --pdf sources/<the report>.pdf --write
.venv/bin/python -m vss manual --ticker ZZ-B.ST --merge-draft --origin llm-pdf

# route C -- the issuer's figures workbook (xlsx) through a committed cell map
.venv/bin/python -m vss appendix --ticker PNDORA.CO --xlsx sources/<the workbook>.xlsx
```

A draft is never the store: every drafted figure is `UNVERIFIED`, and
section 5 refuses to value on an unverified figure. Verification is
mechanical, not by eye:

```bash
.venv/bin/python tools/cross_verify.py EVO.ST --apply   # a second, independent reading agrees
.venv/bin/python tools/quotecheck.py --apply EVO.ST     # a hand-read figure stands in its document
.venv/bin/python -m vss manual --ticker EVO.ST          # exit 0: section 5 may run
```

Then the history (`vss history --ticker EVO.ST --esef --write`), the growth
view and the watchlist entry as in [2.3](#23-take-a-us-company-in).

A first use of the exchange feed needs the issuer mapped once:
`vss nordic --ticker PNDORA.CO --resolve "Pandora" --write`. A download
needs the fiscal period stated by hand (`--period 2026-Q2`): nothing in the
feed says which period a document covers.

### 2.5 Value a company

```bash
.venv/bin/python -m vss strike --ticker CPRT --dry-run     # the table and the document, nothing written
.venv/bin/python -m vss strike --ticker CPRT               # the run record and the strike document
```

`vss strike` needs a store that section 5 may read and a registered growth
view. It prints bear, base and bull, the growth today's price implies, and
which leg moved since the last strike. It writes
`reference/run-records/<TICKER>-<stamp>.json` and
`reference/<TICKER>-STRIKE-<stamp>.md`.

**It never writes the watchlist.** `fv_base`, `fv_bull`, `tier`, `status`
and the `run_record:` pointer are yours to enter, after reading the strike
document. A value prints in the nightly report only when the entry names a
run record that replays to it.

Exit `2` means it refused, and nothing was written. The reasons: no store;
no registered growth view; the store's events ledger (deals and other
events since the accounts) is dated more than seven days ago -- search the
company's press releases and filings again, then date it; or the section 5
gate refuses. `--ignore-gate` strikes past the last of these and writes the
refusal into the record.

### 2.6 Review a company in a Claude Code session

The review is where judgment is recorded. The machine prepares; you answer.

```bash
.venv/bin/python -m vss prepare --ticker NVR         # the night before: fetch, fill, compute, list what is open
# in Claude Code:  /review NVR                       # one step at a time; your answers are recorded verbatim
.venv/bin/python -m vss review --validate reference/reviews/NVR/<date>.yaml
.venv/bin/python -m vss review --record reference/reviews/NVR/<date>.yaml
```

`--record` appends your note to the watchlist entry and registers the growth
view; it writes no status and no value. The full walk is
[`manual/02-workflow.md`](manual/02-workflow.md), the commands in order
[`manual/00-quick-ref.md`](manual/00-quick-ref.md), and the step list
`config/review/SCHEMA.md`. `/granska` runs an independent review of the
whole method and code, and changes nothing.

### 2.7 Read a report when it comes out

By hand, for one document:

```bash
.venv/bin/python -m vss earnings --ticker MSFT --url https://<the company's own release>
.venv/bin/python -m vss earnings --ticker MSFT --text-file ./q4.pdf --compare
```

It extracts the stated figures with the sentence each came from, tests the
hard kills, and prints an alert that says `VERIFY AGAINST SOURCE`, never
"sell". Nothing is sent and nothing reaches `quarters:` -- the figures are
proposed as a YAML block for you to enter. `--compare` reads the source
twice and blanks any field the two readings disagree on. The source is
always the company's own filing, never a news article. A host that refuses
automated requests (it answers 403) is read from a browser-downloaded file
with `--text-file`.

Automatically, every night: `vss queue` finds each queue name's new report
(SEC, or the Nordic / Oslo feed), reads it the same way twice, re-values the
name on its last four quarters and sends `UTSIKT` only if the outcome
changed ([3.4](#34-the-queue)). `vss watch` tells the phone when a
*watched* name files a report, a guidance change or a profit warning.

### 2.8 Screen for candidates

```bash
.venv/bin/python -m vss screen --weekly --no-notify      # the whole chain; never writes the watchlist
```

or one step at a time, each reading what the previous one stored:

```bash
.venv/bin/python -m vss screen --universe-report
.venv/bin/python -m vss screen --snapshot-only --asof 2026-08-21
.venv/bin/python -m vss screen --filter1 --asof 2026-08-21
.venv/bin/python -m vss screen --fundamentals --asof 2026-08-21
.venv/bin/python -m vss screen --filter2 --asof 2026-08-21
.venv/bin/python -m vss screen --rank --asof 2026-08-21
.venv/bin/python -m vss screen --rank --write-pipeline --dry-run --asof 2026-08-21
```

The chain: the universe lists, a price snapshot, the exclusion list and the
staleness gate, fundamentals for the survivors, one coarse test (positive
free cash flow), and what is left **in a seeded random order with one fixed
seed**. The order is not a ranking: the key that used to order the list did
not sort returns in the tests, so the list no longer pretends to know which
name is best. Its two legs are still printed as information.

Only `--rank --write-pipeline` writes the watchlist: new `PIPELINE` entries
with no value, no tier and no line, after a backup, never touching an
existing entry. The output is review work, never a purchase.

A comparison run on a scratch snapshot **must** set `--runs-root` as well
as `--snapshot-root`, or it writes its ranking over the real one for that
date.

### 2.9 Keep the queue

`config/queue.yaml` holds every company that has been valued, with its bear
/ base / bull and its lines.

```bash
.venv/bin/python tools/build_queue.py            # what a rebuild would change
.venv/bin/python tools/build_queue.py --write    # after a new strike
.venv/bin/python -m vss queue --dry-run          # tonight's table; no report, no state, nothing sent
.venv/bin/python tools/master_list.py            # rebuild reports/HUVUDLISTA.md
```

`kind: strike` rows are harvested from the newest
`reference/<TICKER>-STRIKE-*.md`. `machine` and `rough` rows (from
`tools/warren.py` and `tools/rough_fv.py`) and the hand fields are yours and
are kept across rebuilds. Values are in the trading unit: a London listing
quoted in pence carries its value in pence.

### 2.10 Record a sale, and read the record

Add one item per executed transaction to the entry's `sales:` block
([3.6](#36-sales-and-the-shadow-book)), then:

```bash
.venv/bin/python -m vss sales --reconcile <the broker's transaction export>.csv
.venv/bin/python -m vss sales              # every closed position against the indices
.venv/bin/python -m vss shadow             # every refusal against the indices
```

Reconcile first (E165): it matches every sell row of the export against the
booked fills and exits `1` on any difference, so the record is not read on
fills that were never checked. The reader expects Avanza's transaction
export; another broker's file needs its columns mapped in
`vss/sales_reconcile.py`. The shadow book reads
`config/shadow_book.csv`, one row per company refused. Neither report is a
signal; the shadow book is meant to be read once a year.

### 2.11 Schedule it and reach your phone

Install the timers as in [1.5](#15-run-it-every-night). Then:

```bash
systemctl --user list-timers 'vss*'            # what runs next
systemctl --user start vss.service             # run the nightly now
journalctl --user -u vss.service -n 50         # its last output
systemctl --user disable --now vss.timer       # stop it
```

The nightly unit runs with `Persistent=true`, so a run missed while the
machine was off happens at the next opportunity. It is sandboxed
(`ProtectSystem=strict`, `ProtectHome=read-only`) with write access to
`data/` and `reports/` only.

**Messages.** Set `NTFY_TOPIC` to a long random [ntfy](https://ntfy.sh)
topic name -- anyone who knows the name can read it -- and subscribe to it
on the phone. Messages are outbound only; nothing ever reads from the topic.
Unset is silence, not an error.

**Silence must mean healthy.** Three things make a dead run visible:
`vss checkin` every morning says when no completed run is on record or a
timer is not enabled; the units name `vss-failure@.service`, which posts
that a unit failed; and `HEALTHCHECK_URL`, if set, is pinged only after a run
that succeeded, so an outside service notices when the machine itself is
off.

### 2.12 Open every session with the master list

`reports/HUVUDLISTA.md` is every company looked at -- owned, candidates,
watched, to review, no -- with price, values, the kind of value and the next
event. `vss queue` rebuilds it every night. To have a Claude Code session
open with the short version, add a SessionStart hook to
`.claude/settings.json` (the file is not shipped; it is yours):

```json
{
  "hooks": {
    "SessionStart": [
      {"hooks": [{"type": "command", "timeout": 60,
                  "command": "cd \"$CLAUDE_PROJECT_DIR\" && .venv/bin/python tools/master_list.py --short"}]}
    ]
  }
}
```

### 2.13 Check a rule change against every company

```bash
.venv/bin/python tools/rule_impact.py --save /tmp/before.json    # the code as it stands
# ... change the rule ...
.venv/bin/python tools/rule_impact.py --diff /tmp/before.json    # every name whose value or test moved
```

A ruling that loosens a test or raises a value is measured on every name,
not only the one that asked for it (E155).

### 2.14 The Nordic screen and the backtests

These read a commercial vendor's data that you fetch under **your own
licence**. None of it, and nothing computed from it, is in this repository.

```bash
# key in ~/.config/eodhd/env (EODHD_API_KEY=..., chmod 600); the vendor's
# symbol lists (active and delisted) in data/eodhd/symbols.csv
.venv/bin/python tools/fetch_eodhd.py --check            # quota and one test file, nothing stored
.venv/bin/python tools/fetch_eodhd.py --budget 90000     # statements into data/eodhd/fundamentals/
.venv/bin/python tools/eodhd_pit.py --build              # when each period became known
.venv/bin/python tools/nordic_screen.py --no-refresh     # value and rank every active Nordic company
.venv/bin/python -m tools.backtest.nordic                # the Nordic backtest
```

The backtest modules are listed in
[REFERENCE.md, The backtests](REFERENCE.md#the-backtests). A test is
registered in `reference/backtest/ATTEMPTS.md` before it runs; what the
tests found is in the README and in
[the book](the-method/index.html).

### 2.15 Run the tests

```bash
.venv/bin/python tools/fetch_test_fixtures.py     # once: the price files the tests read
.venv/bin/python -m pytest -q
```

The price fixtures are not shipped (the vendor's terms allow personal use,
not redistribution); without them the tests that need them skip and say so.
More in [3.7](#37-tests).

---

## Part 3 -- Reference

### 3.1 Commands, flags, timers, variables, files, modules

All in **[`REFERENCE.md`](REFERENCE.md)**, generated from the code:

- [every `vss` command](REFERENCE.md#the-vss-commands) with its flags, what
  it reads, writes, calls and sends, its exit codes and the form of it that
  changes nothing;
- [every tool](REFERENCE.md#the-tools) under `tools/`;
- [the timers](REFERENCE.md#timers), read off `deploy/`;
- [the environment variables](REFERENCE.md#environment-variables);
- [the files](REFERENCE.md#files) each command writes;
- [the modules](REFERENCE.md#modules) under `vss/`.

### 3.2 The watchlist

`config/watchlist.yaml`: one entry per company under `tickers:`. **Every
field is entered by hand**; the tool never computes, guesses, defaults or
back-fills one. See `config/watchlist.example.yaml`.

| Field | Required | Meaning |
|---|---|---|
| `ticker` | yes | the Yahoo symbol, e.g. `VOLV-B.ST`, `RHM.DE`, `MSFT` |
| `name` | yes | display name |
| `currency` | yes | the trading currency. `fv_base`, `fv_bull` and `stop_price` are in this currency; a London listing quoted in pence says `GBX` |
| `status` | yes | one of the six below |
| `cik` | no | the filer's number at SEC, for the US routes |
| `reporting_frequency` | no | `quarterly` (default) or `half_yearly`: sets the period labels the name stores and the unit its kill windows are counted in |
| `fv_base` | for a value | the base-case value per share. Printed only where `run_record` names a complete record that replays to it |
| `fv_bull` | on `HELD` | the bull-case value; a HELD entry without one does not load |
| `fv_void` | no | a reason, in words, why the value is void. While set, nothing reads `fv_base` as a value |
| `tier` | for an MBP | `1`, `2` or `3`; sets the cushion. A hand field |
| `run_record` | for a value | `reference/run-records/<TICKER>-<stamp>.json`, written by `vss strike` |
| `growth` | for a strike | the pre-registered view: `base`, `bear`, `bull` (fractions), `view` (the file with your words), `registered` (the date) |
| `mbp_basis` | no | `definition` and `struck`: under which MBP definition an older stored figure was struck, so it is marked where it prints |
| `hurdle` | no | the hurdle rate frozen on a purchase: `rate`, `core_expected_return`, `premium`, `rate_as_of` -- all four or none |
| `fx` | no | the exchange rate frozen with a verdict whose value was struck in another currency |
| `dd_at_entry`, `peak_date` | no | the drawdown and the date of the 52-week high when the name was entered; both or neither |
| `stop_price` | on `HELD` | there is no price stop (E162). A HELD entry writes `stop_price: none`; a **blank** field on a HELD name blocks it (`NO_STOP`). A number is kept as your own note and no rule reads it |
| `catalyst_date` | no | `YYYY-MM-DD`, when the next dated event is due |
| `catalyst_resolved` | no | the day you ingested its outcome. Once `catalyst_date` has passed, an empty one blocks the name |
| `catalyst_event` | no | what the event is |
| `quarters` | no | hand-entered quarterly figures the hard kills read. `eps_consensus` is manual only: it is never extracted |
| `exec_changes` | no | CEO and CFO departures. Absent means "not recorded"; an empty list means "checked, none" |
| `sales` | no | the fills of a closed or reduced position ([3.6](#36-sales-and-the-shadow-book)) |
| `notes` | no | free text. No rule reads it |

**`mbp` is not a field.** It is computed -- the record's base value times
the tier cushion, 0.85 / 0.75 / 0.65 for tier 1 / 2 / 3 -- and writing an
`mbp:` key fails the run. It is information: it binds nothing.

| Status | Meaning |
|---|---|
| `HELD` | owned |
| `WATCH-PRICED` | passed, and is too expensive. A price line applies |
| `WATCH-GATED` | failed something other than price. Re-entry needs a named information event, never a price |
| `PIPELINE` | review work with a dated starting point |
| `INTAKE` | read, not watched. It may carry `cik` and `growth`, and none of `tier`, `stop_price`, `dd_at_entry`, `peak_date`, `mbp_basis` |
| `DROPPED` | refused, and kept as a record |

**Validation is strict and fatal to the whole run.** An unknown key, a bad
tier, a non-numeric price, a duplicate ticker, a retired status (the bare
`WATCH`), overlapping periods or a quarter whose operating income and margin
do not reconcile stops everything, rather than skipping one entry. A
silently dropped ticker is a worse failure than a crash.

### 3.3 The store

`config/manual/<TICKER>.yaml` holds the figures a valuation reads. Start
from `config/manual/TEMPLATE.yaml`, or let a route in
[2.3](#23-take-a-us-company-in) / [2.4](#24-take-a-nordic-company-in) fill
it.

- **Blocks.** `periods:` holds one entry per fiscal period at the resolution
  the company reports. `annual:` holds what it publishes once a year.
  `roll_forward:` holds the latest balance sheet for the bridge. Where a
  figure is in both `periods:` and `annual:`, `periods:` wins and the load
  says so.
- **Every figure** carries `value`, a `source` (the period's `document:`
  unless it names its own), a `page`, and a `status`. A bare `revenue: 1234`
  is refused.
- **Status.** `UNVERIFIED` or `VERIFIED`. Section 5 refuses to value on an
  unverified figure. `verified_kind` says how: by hand, `machine_read_back`
  (`tools/quotecheck.py`), or `two_source` (`tools/cross_verify.py`).
- **Origin.** `manual`, `sec-xbrl`, `nordic-xlsx`, `esef-ixbrl`, `llm-pdf`.
  A file may mix them; each figure says which it is.
- **Drafts.** `config/manual/drafts/<TICKER>.<origin>.yaml` is a machine
  pre-fill, never read as the store until merged with
  `vss manual --merge-draft`, which adds what the store lacks and never
  overwrites a figure.

`vss manual --ticker X` runs four checks -- units, one scale, staleness, and
every ratio's legs from one fiscal period -- and exits `1` when section 5
may not read the file.

### 3.4 The queue

`config/queue.yaml`: `portfolio_sek` (the securities in the portfolio, for
the size ceiling) and one row per valued company under `names:`.

| Field | Meaning |
|---|---|
| `ticker`, `name`, `ccy` | the company and its trading currency |
| `kind` | `strike` (the full valuation), `machine` (`tools/warren.py`) or `rough` (`tools/rough_fv.py`). Only a strike is a value to buy on |
| `bear`, `base`, `bull` | value per share, in the trading unit |
| `source` | the strike document or the tool run the values came from |
| `status`, `tier` | from the watchlist, or `OFF-WATCHLIST` |
| `gate_until`, `gate_event` | a gated name's date and the event that lifts it |
| `sell_at` | hand-set sell lines: a list of `{price, action}` |
| `look_at` | a hand-set revisit level; replaces base times the cushion |
| `shares`, `entry` | a held position, for the size ceiling |
| `exit_pending` | a sell decided and not yet carried out: `{since, why}` |
| `override` | a rule the owner set aside for this name: `{rule, overrides, reason, standing, expires, since}`; printed beside the line it touches |
| `base_cap`, `bear_cap`, `bull_cap` | a lower value a later ruling gives before the next strike |
| `correction` | a value correction to be told once: `{since, text}` |
| `note` | free text |

Every night `vss queue` puts each name in one zone and compares it with the
zone it was in the night before. **A change is said once.**

| Message | When | Sent |
|---|---|---|
| `UNDER MBP` | a struck name with a tier, at or under base times the tier cushion. Information: a reading is needed before any order | on entering the zone |
| `TITTA` (look) | a name with no tier, at or under base x 0.85 (a strike) or x 0.75 (machine, rough), or under its `look_at`. Means "value it properly now", never "buy" | on entering the zone |
| `SÄLJ` (sell) | a held name at a hand-set sell line or at its bull value | on entering the zone |
| `SPÄRR` (gate) | a gated name's event date has come | once |
| `UTSIKT` (outlook) | a new report changed the outcome: the four-quarter value moved 10 % or more, the reading found a hard kill or a guidance cut, or a headline names a profit warning, a guidance change, a CEO or CFO leaving, a bid or a delisting | once per report or headline |
| `RÄTTELSE` (correction) | a value in the queue was corrected | once |
| `RAPPORTKONTROLL FELADE` | the nightly check for new reports failed for a name; it is searched again the next night from the same date | once per streak |
| `STORLEK` (size) | a held position is above 6 % of the portfolio (E157) | weekly while it lasts |
| `SÄLJ EJ UTFÖRD` | a decided sell (`exit_pending`) has not been carried out | weekly while it lasts |

A gated name in a price zone is shown in the report and not sent until its
gate lifts: what failed was not the price, so no price may wake it. A name
whose value is void, whose bear case is at or below zero or above its base,
or which is declared cyclical with no downturn in its history, gets no
line. A report that was read and changed nothing is a line in
`reports/QUEUE-<date>.md`, not a message.

### 3.5 The nightly report

**Metrics, per name.** Last close and its date, the 52-week high and low,
the drawdown and the distance above the low, RSI(14), SMA50, SMA200 and the
price against each, the 20-day average volume and today's ratio to it, and
the distance to the MBP.

- The 52-week high and low are the highest and lowest daily *close* in the
  trailing 365 calendar days, not the intraday extreme. A series that does
  not reach back 52 weeks plus five trading days gives `DATA MISSING`, never
  a smaller number struck off a shorter window.
- Drawdown is `(high - close) / high`, a positive fraction.
- RSI(14) uses Wilder's smoothing and needs 15 closes; SMA50 and SMA200
  need their full window. Fewer is `DATA MISSING`, never a partial estimate.
- The volume ratio is today's volume over the mean of the *previous* 20
  sessions.
- RSI, the moving averages and the drawdown are **printed and decide
  nothing**.

**The staleness gate.** A name is BLOCKED, and gets no verdict, when any of
these hold. All that apply are listed, not only the first.

| Blocker | Condition |
|---|---|
| `NO_DATA` | the fetch failed and no cached data exists |
| `STALE_DATA` | the newest close is more than **3 trading days** old on the name's own exchange -- or more than **1** for a `HELD` name or one with an MBP. The exchange's closed days are not counted |
| `CATALYST_UNRESOLVED` | `catalyst_date` has passed and `catalyst_resolved` is empty |
| `NO_STOP` | a `HELD` entry's `stop_price` is blank. Write `stop_price: none` |
| `PRICE_CORRECTION` | the vendor restated a close across a level the name carries. The held close stands until you rule |
| `CALENDAR_MISMATCH` | the vendor printed a close on a day the name's exchange calendar calls closed: the symbol is mapped to the wrong exchange |

A blocked name that carries a level says `LEVEL NOT CHECKED`, with the last
known close and its age, and is pushed to the phone once a night.

**Verdicts,** for names that are not blocked. They are collected, not
first-match-wins.

| Verdict | Condition |
|---|---|
| `AT/BELOW MBP` | `close <= mbp`. Information since E168 |
| `APPROACHING MBP` | `mbp < close <= mbp x 1.05` |
| `DROPPED`, `INTAKE` | the name's status; it collects no other verdict |
| `DATA MISSING` | a field the check needs is absent, or the price series failed its sanity check |
| `NO ACTION` | nothing above fired |

Boundaries are inclusive: exactly at the MBP is `AT/BELOW MBP`. A crossing
that happened because the MBP moved, not the price, is marked as
definition-caused and arms nothing.

There is no `STOP BREACHED` and no `OUTSIDE DISLOCATION BAND`: the price
stop went with E162 and the drawdown band with E161, each after a
registered test. `Stop (note)` remains as a column and is a note.

**History.** Each run appends one row per name to `run_metrics` in
`data/vss.sqlite`: every metric, the manual inputs in force, the MBP, the
blockers and the verdicts, and `ticker_filter` (empty for a full run). It is
read back in two places: `vss strike` reads the tier in force for its
before/after table, and the definition-crossing test compares tonight's MBP
with the one the previous run recorded.

### 3.6 Sales and the shadow book

One item per executed transaction, in the entry's `sales:` block:

```yaml
    sales:
      - date: 2026-08-26
        price: 178.06          # optional: absent is DATA MISSING, never read off a bar
        currency: EUR          # defaults to the entry's currency
        shares: 5
        account: "ACCOUNT-A"
        rule: C4               # C1 | C2 | C3 | C4 | owner
        run_record: reference/run-records/SAP.DE-2026-08-26.json
        proceeds_sek: 9841.22  # what landed, net of charges and exchange
        note: "..."
```

`config/shadow_book.csv`, one row per verdict, nine columns:

```csv
ticker,verdict_date,verdict,standing,close,currency,fv_base,decided_by,source
DECK,2026-08-24,WATCH-GATED,EXPIRY,92.08,USD,,"Gate 1's catalyst limb ...","config/watchlist.yaml note (WATCH 2026-08-24)"
```

`verdict` is `DROPPED`, `WATCH-GATED` or `INTAKE`; `standing` is `STANDING`
(holds until deliberately removed), `EXPIRY` (re-read when a named event
arrives) or `OPEN`. `close` is the settled close on the verdict date, never
the nearest bar; a verdict written on a weekend is dated to the last weekday
on or before it.

### 3.7 Tests

```bash
.venv/bin/python -m pytest -q
```

- `tests/fixtures/verdict-matrix/` drives every verdict path at once: six
  tickers whose synthetic fields place each close on a chosen side of a
  threshold, on frozen prices read offline. Its values are fabricated and
  must never be copied into a real watchlist.
- `tests/fixtures/earnings/berkshire-10q-2025-q2-excerpt.pdf` is three
  pages of a real public filing: four period columns under a stacked header,
  which is the hazard a statement page carries and an invented one does not.
- The rules layer is tested at its boundaries: exactly at the MBP and at
  MBP x 1.05, a blank and a `none` stop on a held name, a close one and
  three sessions old across an exchange holiday, every missing field, a
  blocked name never receiving a verdict.
- Two tests enforce that `rules.py` imports nothing beyond the standard
  library's value types and never reads the clock.
- `tests/test_manual_reference.py` holds `REFERENCE.md` equal to the code;
  `tests/test_review.py` does the same for `config/review/SCHEMA.md`.

Without the price fixtures (`tools/fetch_test_fixtures.py`) the tests that
need them skip and say so. The screener's acceptance snapshot is vendor data
that cannot be refetched; its tests stay skipped.

---

## Part 4 -- Explanation

**[`EXPLANATION.md`](EXPLANATION.md)** says why each part behaves as it
does, and what was measured to make it so:

1. [DATA MISSING is a result](EXPLANATION.md#1-data-missing-is-a-result)
2. [What is computed and what is entered by hand](EXPLANATION.md#2-what-is-computed-and-what-is-entered-by-hand)
3. [Reading a report](EXPLANATION.md#3-reading-a-report-vss-earnings) -- the provenance rule: a quote must contain the figure it claims to source
4. [Tagged facts from SEC](EXPLANATION.md#4-tagged-facts-from-sec-vss-xbrl)
5. [The Nordic feeds](EXPLANATION.md#5-the-nordic-feeds-vss-nordic) -- what each feed does that a naive client gets wrong
6. [A figures appendix](EXPLANATION.md#6-a-figures-appendix-vss-appendix)
7. [The store](EXPLANATION.md#7-the-store-vss-manual)
8. [Drafts](EXPLANATION.md#8-drafts-report-pdfs-esef-packages-and-a-second-reading) -- why a machine's reading is never the store
9. [The screener](EXPLANATION.md#9-the-screener), and what "point in time" means here
10. [The queue and the outlook check](EXPLANATION.md#10-the-queue-and-the-outlook-check)
11. [The shadow book](EXPLANATION.md#11-the-shadow-book)
12. [The overview page](EXPLANATION.md#12-the-overview-page)
13. [The staleness gate](EXPLANATION.md#13-the-staleness-gate)
14. [Repository history](EXPLANATION.md#14-repository-history)

The rules themselves are two pages: `reference/FRAMEWORK.md`. Each names its
ruling in `reference/archive/`, where the full text and the reasons stay.
The story of how the rules were tested, and why most of them were removed,
is [the book](the-method/index.html).
