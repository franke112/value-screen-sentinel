---
description: Walk one name through the playbook's steps, one at a time, and record only what the owner says
argument-hint: TICKER
---

# /review $ARGUMENTS

You are running a REVIEW SESSION for `$ARGUMENTS`. The session is the
interface; the code is the guard. What you write goes into
`reference/reviews/$ARGUMENTS/<today>.yaml`, whose shape is
`config/review/SCHEMA.md` and whose refusals are `vss review --validate`.
Read that schema before the first question.

FRAMEWORK §11 binds this session. Effort is LOW for reading and
transcribing, and there is no HIGH step here: every judgement in this
session is the owner's.

## Before the first step

1. **Refuse to start without today's prepare report.** Look for
   `reports/prepare/$ARGUMENTS-<today>.json` and its `.md`. If neither is
   from today, say so and stop. Proceed without one ONLY if the owner says
   to, and then put the owner's words in the file as `prepare_waived`.
2. **Read the step list from code, never from memory.** Read
   `tools/playbook/steps.py` (the steps, their `question`, `sections`,
   `exits`), `tools/playbook/placement.py` (which rulings bind which step),
   `vss/review.py`'s `REVIEW_STEPS` (which steps this status walks) and the
   name's prepare report. Never improvise a step, a question or an enum:
   the step's outcome vocabulary is `vss review --schema`'s table.
3. **Start where the name stands.** The prepare report's "Where this name
   stands" section names the step: a name `already struck ... resume at
   tier-mbp` (or `verdict`) resumes THERE, and you say in one line why the
   earlier steps are not walked (the strike on record, its date, its run
   record). Write every earlier step into the file as `skipped: true` with
   that reason and set `started_at` and `resume_reason`. A name flagged
   `INCONSISTENT WITH E27` (fv_base set, status PIPELINE) is walked from
   the `verdict` step until its status is consistent: the verdict question
   is asked, and the review does not go back up the chain. A name with no
   resume point starts at the first step of its status's list.
4. Say, in one line, the name, the status at start, the step list (N steps)
   and the step you are starting on. Then ask the first question.

## Walking the steps

**ONE STEP AT A TIME.** For each step, print exactly this and then STOP
and wait for the owner:

- where we are: `step N of M — <id>: <title>`;
- what the machine already found for this step, from the prepare report
  only (its checks, its stands lines, its human-step context), quoted, not
  interpreted; say "the report has nothing for this step" when it has
  nothing;
- the governing rulings, from `placement.py`'s row for the step, each as a
  ONE-LINE Y statement with its number ("E27: WATCH is two states, and they
  carry opposite re-entry rules"); precedents are NOT shown here;
- the question, in one sentence, the step's own `question` from `steps.py`
  with its section filled in;
- the outcome vocabulary for the step, verbatim from the schema.

Then wait. The owner's reply is one of:

- an answer: record `outcome` (from the vocabulary), `text` (the owner's
  words VERBATIM, never your paraphrase), `answered_at` (now, ISO with
  zone), `documents_opened` and `rulings_cited` as the owner named them;
- `p`: show the precedents for this step from the playbook
  (`docs/playbook/<step>.html`'s "how we decided before", or
  `tools/playbook/sources.py`'s precedent sources) and ask the question
  again. Precedents are shown only when asked;
- `s: <reason>`: record `skipped: true`, `skip_reason` verbatim, `outcome`
  null. A skip without a reason is not a skip; ask for the reason.

**Write the file after every answer**, not at the end. A session that dies
mid-walk leaves a file that validates as far as it got.

## The verification step (`basis`)

Present the prepare report's verification list ONE FIGURE AT A TIME: field,
period, the value the store holds, the document and the page, as the report
states them. For each, the owner says VERIFIED or types the corrected
value. Record `{field, period, value, outcome: VERIFIED}` or
`{outcome: CORRECTED, corrected_value: <what the owner typed>}` on the
basis step's `verification` list -- on the owner's word only. Never mark a
figure VERIFIED because the report calls it so, and never fill a corrected
value yourself. The store (`config/manual/<TICKER>.yaml`) is NOT edited by
this session; a correction is recorded here and the owner applies it
through the store's own tools.

## The growth-view step -- THE ORDERING THAT MAKES EVERYTHING ELSE VALID

**Take base, bear and bull, with the owner's reasons, BEFORE any implied
number, fair value, MBP, tier or prior valuation of this name is shown,
computed or mentioned.** That includes: the entry's `fv_base`, `tier` and
the MBP; the run record's value; g\*; the prepare report's stands line
that quotes fv_base; any earlier strike document; any other name's
figures. Until `growth_view` is written you do not open those, you do not
quote them, and you do not say whether the market price is above or below
anything. The playbook's anchoring guard (`register your view first`) is
the same rule; it is yours here.

Ask for the three rates as fractions the owner types (0.025 for 2.5%) and
the reasons in the owner's words. Write `growth_view` with `registered_at`
= now, THEN write the growth-view step's answer with `answered_at` at or
after that instant. Only then may anything implied be shown.

A name whose entry already carries a registered view: ask whether it
stands. If it stands, write `growth_view` from the entry's rates with
`registered_at` = the entry's `registered` date and the reasons "standing
view of <date>, <file>"; `vss review --record` then leaves the registration
alone. If it changes, the new rates and reasons go in with `registered_at`
= now and `--record` supersedes the file under E76/E95.

## The strike and after

Run the section-5 strike through the EXISTING paths and show the output
AS PRINTED, unedited and uncommented:

    .venv/bin/python -m vss manual --ticker $ARGUMENTS --asof <today>

and, where the name has one, its `tools/strike_<name>_<date>.py`, or
`.venv/bin/python -m vss run --ticker $ARGUMENTS --dry-run` to replay the
run record on the entry. There is no `vss strike` subcommand; do not write
one and do not compute a fair value in the session yourself.

Then ask, each as its own question with a STOP between:

1. the tier (`tier-mbp` step): "Which tier, on which score and which
   reading?" -- the owner's words go in `text`;
2. the verdict (`verdict` step): "Which status do you write, and in which
   words?" -- outcome from the vocabulary;
3. for WATCH-PRICED: "What are the conditions, and what is the stop?" --
   appended to the verdict step's `text` in the owner's words.

## What you never do

- **Never propose, draft, suggest or hint at a verdict, a tier, a fair
  value, an MBP, a stop or a growth rate.** Not as an example, not as a
  range, not as "the record would suggest", not as a default in the
  question. If the owner asks "what would you do" or "what do you think",
  answer: "This is the owner's step. <the question again>." Nothing more.
- Never fill `text`, `reasons` or `note` with your own words. Empty is
  correct until the owner speaks.
- Never edit `config/watchlist.yaml`, `config/manual/`, `reference/growth-
  views/` or FRAMEWORK-EDITS in this session. The one writer is `vss
  review --record`, and the owner runs it.
- Never show a step's precedents unasked, never show two steps at once,
  never skip a step on your own.

## Ending

1. Take the owner's note for the watchlist entry, verbatim, into `note`.
2. Run `.venv/bin/python -m vss review --validate reference/reviews/$ARGUMENTS/<today>.yaml`
   and show its output as printed. Fix only shape errors the validator
   names (a missing field, a wrong key); never change an answer.
3. Only when it prints VALID, offer -- do not run --
   `.venv/bin/python -m vss review --record reference/reviews/$ARGUMENTS/<today>.yaml`.
   The owner runs it. It appends the note, registers the view, and
   stores nothing else: never status, fv_base, tier, mbp or stop.
4. End with the playbook step the name now sits on (`STATUS_STEP` of the
   status the owner wrote, or the step the walk stopped at), in one line,
   and the reminder that the playbook is rebuilt in the same commit as the
   record (CLAUDE.md, same-commit rule).
