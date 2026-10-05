# MEKKO.HE — growth view

**Set by the owner, 2026-09-08.** Pre-registered under FRAMEWORK-EDITS
**E28**, before any fair value was struck for this name.

Base case FCF growth, 10 years: 5%
Bear: 3%
Bull: 10%

## The reasoning, in the owner's own words

**TRANSCRIBED VERBATIM AND NOT TIDIED**, on his instruction. It is in
Swedish because that is how he wrote it, and translating it would be a
second person's words standing in for his.

> Bear 3 är att de knappt växer och missar sina egna mål med bred marginal. Base 5 är ungefär hälften av vad de siktar på — jag tror export tar längre tid än de säger, och hemmamarknaden krympte 4 % senaste halvåret. Bull 10 är deras eget medelfristiga mål, alltså att de faktiskt levererar det de lovat.

## The three figures he names are all in the filings, and each checks out

**This is not commentary on the view — it is a check that the facts it rests
on are the issuer's own, made after the rates were fixed and changing none
of them.**

- **"deras eget medelfristiga mål" — the bull of 10% is Marimekko's own
  medium-term goal, exactly.** The H1 2026 report, p.6, prints a two-column
  goal table: **Medium-term (3–5 years): annual growth in net sales 10%**;
  Long-term: 15%. The same page states *"Marimekko's long-term financial
  goals, set in 2022, remain unchanged."* **The bull is therefore "they
  deliver what they promised" on the nearer of the two horizons, which is
  what the owner says it is.** Note that secondary coverage of the same
  result described this as a target *"revised down from 15% to 10%"*; the
  filing does not say that, and `reports/BRIEFING-MEKKO.HE-2026-09-08.md` §8
  records the difference.
- **"hemmamarknaden krympte 4 % senaste halvåret" — Finland, 1–6/2026:
  EUR 42.2m against 44.0m, printed as −4%.** H1 2026 report, p.9, Net sales
  by market area. In the quarter alone it is −7%.
- **"export tar längre tid än de säger" — international sales are 46% of
  2025 net sales**, and the issuer prints the trend itself as a stated goal
  line: 43% (2023), 45% (2024), 46% (2025). Three points, three percentage
  points.

## Provenance and ordering, stated

- **Who set them:** the owner, 2026-09-08, dictated in the session that took
  MEKKO.HE through intake.
- **Order (E28):** the three rates were written **before** section 5 was run
  on this name. **No fair value existed for MEKKO.HE on any watchlist, in
  any run record, or in any report before this file** — the intake earlier
  the same day built the store, ran E101's checks and measured E108's floor,
  and struck nothing. This file was committed before the solver was called,
  and the git history is the evidence E28 asks for.
- **Nothing in this file was computed.** No implied growth was solved, no
  discount rate applied, no multiple taken.

## Where it lives for the code — CHANGED 2026-09-08, LATER THE SAME DAY

**AS WRITTEN, AND KEPT because the ordering is the record:** E109 puts the
machine-readable `growth:` block on the WATCHLIST ENTRY, and when these rates
were registered **MEKKO.HE had no watchlist entry.** E109 ruled that case on
the day it was written: five names with registered views were not watchlist
entries — ACN, AOS, LII, RKT.L, ULTA — and they were **left there**, because
entering a name stamps `dd_at_entry` and **freezes Gate 1 under E12**.
BOUV.OL became the sixth on 2026-09-08 and **MEKKO.HE was the seventh**, on
the owner's own instruction in the same message that dictated these rates:
*"Write nothing to the watchlist; MEKKO.HE stays INTAKE."*

**THAT HELD UNTIL THE GATE CHAIN WAS RUN AND RULED, LATER ON 2026-09-08.**
MEKKO.HE is now **WATCH-GATED** (`reference/MEKKO.HE-GATED-2026-09-08.md`),
so it has a watchlist entry and **E109's block is on it** — `base` 0.05,
`bear` 0.03, `bull` 0.10, pointing at this file and at the 2026-09-08
registration date. **NOT ONE RATE MOVED and not a word of the reasoning
above was touched**; what changed is where a machine can read them.

**THE E12 CONCERN THE PARAGRAPH ABOVE RESTS ON DOES NOT ARISE FOR THIS
STATUS.** `rules.frozen_gate_1` fires for **PIPELINE alone**, and E111 rules
that promotion to PIPELINE is what writes E12's stamp. **The entry carries
no `dd_at_entry` and no `peak_date`**, so Gate 1 is not frozen and stays
readable on today's level.

**WHAT THIS CLOSES.** `readiness.read_growth_view` parses **this file**, so
`vss screen`'s readiness limb could always see the view with no watchlist
write. **`vss manual`'s E108 gate reads the WATCHLIST and could not** — which
is why the floor for this name was measured by hand into
`config/manual/MEKKO.HE.yaml`'s header and the strike record. **It can read
it now.** E109 is stricter without a block, never looser: a name with no
block has no view, so adding one can only ask for this name to be measured.

## What the owner had in front of him before he wrote these three numbers

`reports/BRIEFING-MEKKO.HE-2026-09-08.md`, built the same day. Beyond the
three facts checked above, the parts the view speaks to:

- **The margin has fallen three years running** — comparable operating
  margin 18.4% (2023), 17.5% (2024), 17.1% (2025) — against a goal of 20%
  on both horizons, and the first half of 2026 ran at 12.2%.
- **The 2026 guidance band of "approximately some 16–19 percent" is
  numerically the same band guided for 2025**, so it is not a cut; the
  −14.15% of 2026-02-12 was on the delivered quarter.
- **Asia-Pacific is EUR 40.0m of the EUR 87.2m of international sales** and
  grew 16% in Q2 2026 while North America fell 6% — the export story is
  concentrated rather than broad.

**THAT IS E76 WORKING IN THE ORDER E28 REQUIRES:** the reading informs the
view, and the view is written down before anything is solved.

## If this view changes

E76 is explicit: **where a reading happens after a strike and changes the
view, the view is re-registered with the reason and the name is re-struck —
the old view stays in the record, superseded, never overwritten.** This file
is the first entry for MEKKO.HE and supersedes nothing.
