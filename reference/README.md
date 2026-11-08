# The rules, and where to start

This folder is the record: the rulebook, every change to it, and every
valuation and decision with its date and its reason. **It is long on
purpose**, because a method you cannot check is a story. You do not have to
read it front to back.

## Read in this order

1. **[`FRAMEWORK.md`](FRAMEWORK.md)**, two pages since 2026-11-08: the rules
   that bind, each naming its ruling.
2. **The rulings below**: the dozen changes that shaped the method most.
3. **[`archive/FRAMEWORK-EDITS-2026-11-08.md`](archive/FRAMEWORK-EDITS-2026-11-08.md)**,
   about 13,700 lines: every ruling, E1 onwards, each with its date, its reason
   and what it replaced. Search it by number. Don't read it. What was struck on
   2026-11-08 is in [`archive/STRUCK-2026-11-08.md`](archive/STRUCK-2026-11-08.md).

## The rulings that matter most

| Ruling | In one line |
|---|---|
| **E27** | "Watch" is two states. A name too dear may be woken by a price. A name that failed on a fact may only be woken by a new fact. |
| **E28** | Your growth view is written down and committed **before** the tool solves for the growth the price implies. |
| **E30** | Two invented quality bands were deleted rather than tuned. Revenue is read on an organic basis instead. |
| **E40** | A figure counts as verified only by its source, and the record says which kind of check it had. |
| **E90** | The buy line is the base value times a tier cushion (0.85 / 0.75 / 0.65). The cushion covers model error, not scenario risk. |
| **E93** | A scheduled job may rank and report. It never enters a name on its own. |
| **E99** | A test whose data has never existed scores DATA MISSING and does not count against a company. |
| **E111** | INTAKE means "read, not watched". Promotion is a decision, not a side effect. |
| **E122** | A price already held is not withdrawn because the data vendor goes silent. |
| **E140 / E142 / E143** | How owner earnings are measured: three years, working capital out, deals valued at the buyer's own track record, cyclicals over their cycle. |
| **E144** | The growth view is derived from the company's own history, not from hope. |
| **E145** | Would Warren own it: the four quality tests run on every record (`tools/warren.py`). |
| **E148 / E148.1** | One repaired bad year is forgiven, and the year it is measured against may lie before the ten-year window. |

## What else is here

| Pattern | What |
|---|---|
| `<TICKER>-STRIKE-<date>.md` | one valuation run, every figure with its source |
| `<TICKER>-GATED-*.md`, `<TICKER>-GATES-*.md` | why a name was stopped, or let through |
| `growth-views/` | the pre-registered growth views (E28) |
| `reviews/` | a name walked through the playbook, step by step |
| `run-records/` | the machine-readable record behind each strike |
| `events/` | the deals ledger per company |
| `backtest/` | the back-test, and its honest result |
| `HANDOFF-*.md` | notes from one working session to the next |
