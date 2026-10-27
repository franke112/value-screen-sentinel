# PEP — growth view

**Set by the owner, 2026-10-19.** Pre-registered under FRAMEWORK-EDITS
**E28**, before any fair value was struck for this name.

Base case FCF growth, 10 years: 2%
Bear: 1%
Bull: 4%

## The reasoning, in the owner's own words

**TRANSCRIBED VERBATIM AND NOT TIDIED**, as KO and BOUV.OL. Given
2026-10-19 in the message after the rates, on being asked for it, before
anything was computed.

> samma som coca cola de stabilt märke växer med inflationen

## Provenance and ordering, stated

- **Who set them:** the owner, 2026-10-19, in the session that took PEP
  through intake.
- **Order (E28):** the three rates are written **before** section 5 was
  run on this name. **No fair value and no g\* existed for PEP on any
  watchlist, in any run record or in any report before this file.**
- **What was in front of the owner:** the intake store `config/manual/PEP.yaml`
  (commits 549606d and the hand legs of 2026-10-19) and the interest-leg
  question (E137). Nothing valued.
- **Nothing in this file was computed.** No implied growth was solved, no
  discount rate applied, no multiple taken.

## Where it lives for the code, and why there is no watchlist block

As BOUV.OL and KO: E109 puts the machine-readable `growth:` block on the
watchlist entry, and PEP has no watchlist entry. Entering it would stamp
`dd_at_entry` and freeze Gate 1 under E12, and that write is the owner's.

## If this view changes

E76: a reading after a strike that changes the view re-registers it with
the reason, and the name is re-struck. The old view stays in the record,
superseded and never overwritten. This file is the first entry for PEP and
supersedes nothing.
