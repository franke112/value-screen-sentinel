# KO — growth view

**Set by the owner, 2026-10-18.** Pre-registered under FRAMEWORK-EDITS
**E28**, before any fair value was struck for this name.

Base case FCF growth, 10 years: 3%
Bear: 1%
Bull: 5%

## The reasoning, in the owner's own words

**TRANSCRIBED VERBATIM AND NOT TIDIED**, on his standing instruction (as
BOUV.OL). It is in Swedish because that is how he wrote it.

> stabilt varumärke växer med inflation ungefär

## Provenance and ordering, stated

- **Who set them:** the owner, 2026-10-18, dictated in the session that
  took KO through intake. The rates came first; the reason was given on
  being asked for it, in the next message, before anything was computed.
- **Order (E28):** the three rates were written **before** section 5 was
  run on this name. **No fair value and no g\* existed for KO on any
  watchlist, in any run record or in any report before this file.** The
  intake the same day wrote `config/manual/KO.yaml` from SEC XBRL (commit
  14bb3c8) and struck nothing. This file was committed before the solver
  was called, and the git history is the evidence E28 asks for.
- **One number was in front of him that he should know was there:** earlier
  in the same session the assistant said, *from memory and computing
  nothing*, that KO "trades at around 23-25x earnings". It is recorded here
  so a later reader knows the view was not set blind to that remark.
- **Nothing in this file was computed.** No implied growth was solved, no
  discount rate applied, no multiple taken.

## Where it lives for the code, and why there is no watchlist block

As BOUV.OL: E109 puts the machine-readable `growth:` block on the watchlist
entry, and KO has no watchlist entry. Entering it would stamp `dd_at_entry`
and freeze Gate 1 under E12, and that write is the owner's.

## The basis the strike waits for

The owner chose, 2026-10-18, to wait for the Q3 2026 10-Q and strike on the
trailing twelve months, rather than on annual FY2025. FY2025 operating cash
flow (7,408m) carries the **6,173m** fairlife contingent-consideration
payment of March 2025, and FY2024 (6,805m) carries the IRS Tax Litigation
Deposit (10-K FY2025, Note 21). A TTM ending 2026-09-30 no longer contains
the fairlife payment. No exception to E22 is taken: the wait takes the place
of one.

## If this view changes

E76: a reading after a strike that changes the view re-registers it with
the reason, and the name is re-struck. The old view stays in the record,
superseded and never overwritten. This file is the first entry for KO and
supersedes nothing.
