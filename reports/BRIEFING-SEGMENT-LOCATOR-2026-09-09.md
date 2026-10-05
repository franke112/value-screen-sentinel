# `vss briefing` section 1: the segment table is NOT LOCATED for six of six US filers — 2026-09-09

**A FINDING, NOT A FIX.** The change this describes was written, measured, and **reverted**. It is recorded here so the next session does not rediscover it, and so the owner can rule on whether it is worth doing properly.

## What was observed

Six US names were run through `vss briefing` on 2026-09-09 — **ACN, AOS, DECK, LII, NVR and ULTA**. Every one of them reported the same line in section 8:

> **Segment revenue: NOT LOCATED.** No segment revenue table was found in 10-K … under the headings this step looks for. A single-segment filer prints none, and that is the likeliest reason, but this step did not confirm it.

**Six of six is a fact about the patterns, not about six filers**, and it was visible only because all six were read in one pass. Each of these companies publishes a segment table; the fallback sentence's "likeliest reason" is wrong for all six.

## Why it misses

`business_section` (`vss/briefing.py`) tries four heading patterns. The catch-all is:

```
^(\d+\.\s*)?(OPERATING |REPORTABLE )?SEGMENTS?( AND GEOGRAPHIC INFORMATION)?$
```

The `$` requires the heading to **end** after the word SEGMENT(S). Measured against the 10-K text on disk, the actual note headings are:

| Filer | Note heading, as printed |
|---|---|
| ACN | `16. Segment Reporting` |
| AOS | `16. Operations by Segment` |
| LII | `3. Reportable Business Segments:` |

None ends after the word, so none matches. ACN additionally prints `Revenues by Segment/Geographic Market`, which no pattern covers either.

## What was tried, and why it was reverted

The anchor list was widened with a numbered-note pattern — `^\d+\.\s+[A-Za-z ]{0,40}Segments?\b` — and the lookup switched from `block_at` to `first_table`, so a heading alone would not suffice and the block would have to carry numeric rows. Measured against every 10-K in `sources/`:

| Filer | Result of the widened patterns |
|---|---|
| ACN | matched — and returned `Operating segments are components of an…`, the note's **prose preamble** |
| AOS | matched — and returned the **assets, depreciation and capital expenditure** table, not revenue |
| LII | matched — and returned `Description of Segments`, prose |
| CRUS | matched — and returned `We determine our operating segments in a…`, prose |
| CROX, EXE, GNTX, NKE | matched the correct revenue table (these already worked) |
| CTSH, DECK, GDDY, LOPE, MUSA, NVR, ULTA | still not located |

**So the widening converts four NOT LOCATED into four WRONG.** A prose preamble quoted under the heading *"Revenue by segment, as printed"* is precisely what E76's build rule forbids:

> **A SECTION THAT CANNOT BE FILLED IS NEVER FILLED WITH SOMETHING ADJACENT.**

`NOT LOCATED` with the accession named is the better of the two states, so the change was reverted and `vss/briefing.py` is untouched.

## What a real fix would have to do

The heading and the table are **not adjacent**. Every one of these filers opens the segment note with one to two paragraphs of accounting-policy prose and prints the revenue table below it. So the locator needs two steps rather than one:

1. find the segment NOTE by its heading — the widened pattern above does this correctly for all four filers that were missed;
2. then, **within that note**, find the first block that is a revenue table — enough tab-separated numeric rows, and containing at least one of the filer's own segment names, which section 1 does not currently know.

Step 2 is a design change to `first_table`'s contract, not a pattern edit, and the false positives above are what happens without it. **It is not attempted here.**

## What is affected today

Section 1 of every automated briefing still carries the filer's own Item 1 description, which is the part E76 asks for first. What is missing is the printed revenue split. For the six names above the split is available by hand from the 10-K already in `sources/`, and for four of them the note heading is named in the table above.
