# BOUV.OL — growth view

**Set by the owner, 2026-09-08.** Pre-registered under FRAMEWORK-EDITS
**E28**, before any fair value was struck for this name.

Base case FCF growth, 10 years: 3%
Bear: 2%
Bull: 6%

## The reasoning, in the owner's own words

**TRANSCRIBED VERBATIM AND NOT TIDIED**, on his instruction. It is in
Swedish because that is how he wrote it, and translating it would be a
second person's words standing in for his.

> Jag tror att de har väldigt tråkiga och stabila kunder, och att de kunderna har svårt att göra sig av med dem. Bear på 2 är i princip ren inflation. Om AI-frågan slår in hårt är det för högt, men jag tror inte den träffar norsk offentlig sektor och energi lika hårt som den träffar generisk kodning.

## Provenance and ordering, stated

- **Who set them:** the owner, 2026-09-08, dictated in the session that
  took BOUV.OL through intake.
- **Order (E28):** the three rates were written **before** section 5 was
  run on this name. **No fair value existed for BOUV.OL on any watchlist,
  in any run record, or in any report before this file** — the intake of
  the same morning built the store, ran E101's construction checks and
  measured E108's floor, and struck nothing. This file was committed
  before the solver was called, and the git history is the evidence E28
  asks for.
- **Nothing in this file was computed.** No implied growth was solved, no
  discount rate applied, no multiple taken.

## Where it lives for the code, and why there is no watchlist block

**E109 puts the machine-readable `growth:` block on the WATCHLIST ENTRY, and
BOUV.OL has no watchlist entry.** That is not an omission and it is not a
gap in E109 — **E109 ruled this exact case on the day it was written**:

> **TRANSCRIBED 2026-09-04 … Five names with registered views are NOT
> watchlist entries** — ACN, AOS, LII, RKT.L, ULTA — **and their views stay
> unreadable by code, which is a consequence of this choice and is recorded
> rather than worked around.**
>
> **AND THE FIVE ARE LEFT WHERE THEY ARE** — ruled 2026-09-04, on the
> owner's own ground: **entering a name on the watchlist stamps
> `dd_at_entry` and FREEZES GATE 1 UNDER E12.**

**BOUV.OL is the sixth such name**, and the owner said so himself in the
same instruction that dictated these rates: *"Write nothing to the watchlist
— BOUV.OL stays INTAKE and that write is mine."* Entering it to make a block
readable would freeze a catalyst window under E12 for no reason other than
the convenience of a parser, which is precisely the trade E109 declined.

**One thing IS readable, and it is worth naming.** `readiness.read_growth_view`
parses **this file**, not the watchlist block — so `vss screen`'s readiness
limb can see this view without any watchlist write. What cannot see it is
`vss manual`'s E108 gate, which reads the watchlist. **E108's measured limb
therefore still cannot run from the command that gates the store**, and the
floor for this name was measured by hand and written into
`reference/INTAKE-BOUV.OL-2026-09-08.md` §3.

## What the owner had in front of him before he wrote these three numbers

`reports/BRIEFING-BOUV.OL-2026-09-08.md`, built the same morning, and
`reference/INTAKE-BOUV.OL-2026-09-08.md`. What the view names is in both:

- **The client base the bear rate rests on.** Public sector (100% owned) was
  44.0% of Q2 2026 revenue and oil, gas and renewables 41.2%; clients who
  were also customers a year earlier were **95.3%** of revenue, and Bouvet
  has been a supplier to the Norwegian Coastal Administration since 2012 and
  has just won a Norwegian Mapping Authority framework agreement *"for a
  term of up to eight years"*.
- **The AI question the bull and bear both turn on.** Bouvet's own quarterly
  bridge shows hourly rates up (+2.9 / +2.8 / +2.1 / +2.3%) and the billing
  ratio down (−2.1 / −2.3 / −1.8 / −0.9pp) in every quarter of the basis,
  and Bouvet attributes the utilisation fall to holidays, project progress
  and sick leave and **attaches no figure of any kind to AI**. Finansavisen
  attributes the sector's de-rating to AI compressing billable hours,
  naming coding tools. **The owner read both accounts before writing
  these rates**, and his sentence about *"generisk kodning"* is his answer
  to that disagreement.

**THAT IS E76 WORKING IN THE ORDER E28 REQUIRES:** the reading informs the
view, and the view is written down before anything is solved.

## If this view changes

E76 is explicit: **where a reading happens after a strike and changes the
view, the view is re-registered with the reason and the name is re-struck —
the old view stays in the record, superseded, never overwritten.** This file
is the first entry for BOUV.OL and supersedes nothing.
