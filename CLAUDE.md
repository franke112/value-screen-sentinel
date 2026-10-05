# CLAUDE.md

Instructions for any Claude session working in this repository. Rules about the
INVESTMENT FRAMEWORK live in `reference/FRAMEWORK.md` and its rulings in
`reference/FRAMEWORK-EDITS.md`; this file is about how the work itself is done.

*Note for an analysis session: FRAMEWORK §11 binds analysis sessions only and
expressly does not bind engineering sessions (FRAMEWORK-EDITS A1).*

## Cost discipline

Effort follows what can go wrong, not what looks complex. A search that misses
something can be re-run; a ruling written into FRAMEWORK-EDITS governs
everything after it.

**LOW effort:** searches, summaries, reading reports, writing down a ruling I
have already dictated, handoffs. At most two searches per question, and say what
you could not find rather than searching around it.

**HIGH effort:** rulings that are still open, redesign of how §5 or the screener
works, code changes that touch how a figure is computed.

**SUBAGENTS.** Allowed, but on a cheaper model and a lower effort than the
session itself — Sonnet at medium or below, never Opus and never max. A subagent
is for fetching and reading, not for judgment. Two or three, not six.

A prompt with several numbered questions is ONE piece of work, not several.
Answer them in order in this session unless the work genuinely needs parallel
fetching.

If a task looks large enough that fanning out widely is tempting, say so and ask
rather than starting.

### Models -- 2026-10-05

Opus is the default and nothing switches automatically. The owner may switch
a clearly mechanical session to Sonnet by hand (`/model sonnet`): inkorg,
docs, playbook rebuilds, running tests for a decided change, fetching. The
commit trailer names the model, so `git log` records which one did what.

**A Sonnet session or subagent STOPS and hands back to Opus when:**

- a figure is about to enter `config/manual/`, the watchlist or FRAMEWORK-EDITS;
- the rules do not settle a case cleanly (the CPRT restricted cash, E129);
- a test fails and the cause is not obvious from the diff;
- output looks absurd -- a 100x number, far more rows than expected (the
  779 re-reported filings);
- the scope grows beyond what was asked;
- the change touches `rules.py`, `valuation.py`, `manual.py`,
  `runrecord.py`, or a guardrail: shadow mode, read-twice compare,
  notify-only, nothing written without the owner's acceptance.

## How to work in this repo

Read files with offset and limit rather than whole. Pipe long command output
through head, tail or grep. Never cat a large file. Do not re-read a file
already read in this session — if a different part is needed, read that part.

When a task touches several names, commit after each one rather than at the
end, so a long run that fails does not lose finished work.

Why: a pass on 2026-08-30 spent 1.2m tokens on reads and 222k on bash output
and took fifty minutes; the next pass with these habits took six. Reading less
is not reading worse — it is not reading the same thing five times.

### Bounded output, and when to ignore it — 2026-08-31

**Bound shell output before it enters context.** Pipe through `head`, `tail`
or `grep`; never `cat` a large file; read with offset and limit; summarise a
test run rather than pasting it whole — the count and the failures, not the
dots.

Why: context spent on raw output is context not available for the work, and
**a long session on a full context is where mistakes get made.** The cost is
not the tokens, it is what the tokens crowd out.

**THE EXCEPTION MATTERS MORE THAN THE RULE.** When you are looking for
something you cannot name in advance — a wrong figure, an unexpected unit, a
discrepancy between two things that should agree — **read the whole output.**
A grep finds what you already suspected; it cannot find what you did not
think to suspect.

Every real defect found in the week to 2026-08-31 came out of a full read,
not a targeted one:

- **the pence/pound divide** — AUTO.L reading **+12,791%** in a twenty-row
  dry-run table. Nothing was being grepped for; the number was absurd on
  sight, and only sight would have caught it;
- **the blind circle limb** — NHY.OL and EXE firing in that same table when
  E96 says they must never be watched at all;
- **the band event firing fourteen times of eighteen**, which is a fact
  about the shape of a whole column;
- **216 ranked against the original 202**, found by comparing two full
  listings rather than the twenty rows either of them was about;
- **LII not being on the watchlist at all**, found by printing all
  twenty-two entries instead of grepping for the one.

**Bounded output is the default for a KNOWN LOOKUP. Unbounded reading is
correct when HUNTING.** Never let the habit narrow what you look at during a
review, a dry run, or the first run of anything new — those are exactly the
moments the habit would cost the most.

**This is a habit, not a ruling.** It constrains HOW a session works and
never WHAT it may conclude. No finding is weaker for having been expensive
to reach, and none is safer for having been cheap.


## Same-commit rule — 2026-09-13

The decision playbook (`docs/playbook/`, gitignored; `docs/manual/playbook.md`)
is generated from the repo's own sources. **Rebuild it in the same commit as
any ruling, verdict or CLI change** — an entry in FRAMEWORK-EDITS, a status
or note on the watchlist, a shadow-book row, a subcommand or flag:

    .venv/bin/python tools/build_playbook.py && .venv/bin/python -m pytest tests/test_playbook.py -q

(`make playbook` does the same where `make` is installed; the VPS has none.)

A new numbered entry in FRAMEWORK-EDITS fails the test until it is placed in
`tools/playbook/placement.py`. Place it; do not skip the test.

## The review session's files -- same-commit rule, 2026-09-14

`config/review/SCHEMA.md` is generated from `vss/review.py` and a test
holds the two equal; `.claude/commands/review.md` is the session's
instructions and a test holds its three load-bearing clauses (never
propose, the view before any implied number, resume where the name
stands). **Any change to `vss/review.py`, to `tools/playbook/steps.py`
or to the command file lands in one commit with:**

    .venv/bin/python -m vss review --schema > config/review/SCHEMA.md
    .venv/bin/python tools/build_playbook.py && .venv/bin/python -m pytest tests/test_review.py tests/test_playbook.py -q

A review file under `reference/reviews/` and the `vss review --record`
that follows it are a verdict for the same-commit rule above: rebuild the
playbook in that commit.

## inkorg -> the right place -> utkorg -- 2026-10-05

Same inbox/outbox system the owner uses elsewhere. **First thing in every session: look in
`inkorg/`.** If anything but the README is there, sort it before other work
(or right after an urgent question). The owner does not rename or sort --
the session does.

1. **In:** read each file, decide what it is, `mv` it per the table below
   (rename to `YYYY-MM-DD-<description>.<ext>` if the name says nothing).
   Nothing stays in `inkorg/`. Unclear -> ask and leave that file there.
2. **Out:** anything the owner is meant to use (a brief, a sell order, a
   deck) is made in its real place and **copied** to
   `utkorg/YYYY-MM-DD-<subject>/` with a `LÄNK.txt` naming the original.
   Text to paste can go straight into the chat.
3. **Used:** when the owner says a delivery is done with, move it to
   `arkiv/utkorg/`.
4. **Nothing is deleted** -- it goes to `arkiv/`.

| What comes in | Where it goes |
|---|---|
| Annual / interim report, 10-K, 10-Q, press release (PDF/HTML) | `sources/`, named like its neighbours (`<TICKER>_<period>_<kind>_<date>_<lang>_a0.<ext>`) |
| Figures read by hand from a report | `config/manual/<TICKER>.yaml` -- through `vss manual` validation, never typed in unchecked |
| Broker statement, contract note, deposit, withdrawal, cash | `konto/` (private, gitignored); a sale also goes into the watchlist's `sales:` block on the owner's word |
| The owner's own notes on a name (a growth view, a reading) | `reference/growth-views/` or `reference/reviews/<TICKER>/`, per the review process |
| Old, duplicate, unknown but not junk | `arkiv/YYYY-MM-DD-<description>/` |

**`reports/` stays as it is.** The nightly run writes into it, and rulings and
watchlist notes cite its files by path (109 citations). Do not move,
rename or sub-folder anything in it.

The old loose root files are in `arkiv/evidens/`; a ruling that cites one by
bare filename is followed through `arkiv/evidens/INDEX.md`. Config `.bak-*`
copies go to `arkiv/config-bak/` with their relative path kept.
