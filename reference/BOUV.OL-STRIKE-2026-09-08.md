# BOUV.OL — section 5 arithmetic, 2026-09-08 — **PROVISIONAL**

## THE GATE REFUSES THIS NAME, AND EVERY FIGURE BELOW IS PROVISIONAL

`section5_gate` returns **27 refusals**, **26** of them `UNVERIFIED`. The store was built this morning from five PDFs and **not one figure has been read back against a rendered page (E40)**. E21 refuses section 5 on an UNVERIFIED figure the basis reads, and it is right to.

**So this is not a struck fair value.** It is the arithmetic of section 5, run on an unverified store at the owner's instruction. It is not E94's INDICATIVE value either — E94's second fence is *every figure the basis reads VERIFIED under E40*, and that fence fails. **Seven read-backs would make it a strike**, and they are named in `reference/INTAKE-BOUV.OL-2026-09-08.md` §3.

**Growth view registered 2026-09-08 by the owner, in his own words, BEFORE this ran (E28).** bear 2% / base 3% / bull 6%, from `reference/growth-views/BOUV.OL.md`. **Read off the FILE and not off a watchlist `growth:` block (E109)**: BOUV.OL has no watchlist entry and E109 ruled that case — entering a name stamps `dd_at_entry` and freezes Gate 1 under E12.

Basis `TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2`, ending 2026-06-30. Rate 9.5% (7.0% core + 2.5% premium, E29). Settled close 48.85 NOK on 2026-09-04.

## The value — PROVISIONAL

| | NOK |
|---|---:|
| **fv_base** (g 3%) | **31.24** |
| E29 band, low — r 9.0% | 33.78 |
| E29 band, high — r 10.0% | 29.03 |
| FV_bear (g 2%) | 28.90 |
| FV_bull (g 6%) | 39.41 |

**E29 forbids reporting the middle alone**, and the band above is why: half a point of r moves this value by 4.75 NOK, 15.2% of fv_base.

## What the price implies

- settled close **48.85 NOK** on 2026-09-04
- **g\*, the growth the price implies at r 9.5%: 8.78%** — against the owner's registered base of 3%
- price vs fv_base: **+56.4%**
- price vs FV_bear: **+69.0%**
- price vs FV_bull: **+23.9%**

**g\* ACROSS E29's BAND, because the middle alone is not reportable here either:** r 9.0% → **7.70%**, r 9.5% → **8.78%**, r 10.0% → **9.82%**. **At every rate in the band the price implies more growth than the owner's BULL case of 6%.**

### A price note, reported and not used

The nightly run of 2026-09-07 reported a settled close of **49.25** for this name. The vendor now serves that bar with its Open, High, Low and Volume intact and its **Close as NaN**, so `metrics.compute` falls back to 2026-09-04 and this run is struck on 48.85. At 49.25 the implied growth would be **8.89%** instead of 8.78%. Nothing is adjusted; both are printed.

## The legs

- FCF0 **223,851,000 NOK**
- net debt **162,122,000 NOK**
- divisor **103,695,316** shares — E91: the coded DAY-WEIGHTED average of the four stated per-quarter diluted counts for TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2 -- (2025-Q3 103,413,458 x 92d; 2025-Q4 103,841,034 x 92d; 2026-Q1 104,160,484 x 90d; 2026-Q2 103,372,896 x 91d) / 365d = 103,695,316. The window's own average, so the dates agree; stated operands, the arithmetic the code's (E86's pattern), superseding E88's annual fall-back for this issuer

## Construction checks (E101) — DETECTORS, NOT VERDICTS

| check | this record | the issuer | measure | |
|---|---:|---:|---:|---|
| FCF0 vs the issuer's own free cash flow | 223,851 | 264,451 | -15.4% **LOOK** | E34's construction against the issuer's; the two definitions differ by design (interest, leases), so a gap is a PROMPT — `free_cash_flow_reported` is an UNVERIFIED automatic figure (E103 REFERENCE FIGURE -- compared against section 5's own construction and NEVER used to build one; the section 5 gate refuses if it ever reaches a basis. Bouvet's OWN APM, defined on p.32 of the same report: 'Net free cash flow is calculated as net cash flow from operations plus net cash flow from investing activities', and on p.34: 'Net cash flow operations - Net cash flow investments'. It is NOT E34's construction: it deducts no share-based compensation, adds back no interest, and carries interest RECEIVED inside the investing half. HAND-READ 2026-09-08 off the page named -- E103's automatic model route could not run on this host (no VSS_OPENROUTER_KEY), and a page read by eye is stronger provenance than the route it replaces, not weaker. p.33, Key figures Group, Jul-Sep 2025 column: 'Net free cash flow 11 363' (Jul-Sep 2024: 135 341)). **E104: it is re-extracted before this reaches you** — run `vss reference-figures --confirm`. Two readings agreeing make this CONSTRUCTION and yours; two disagreeing withdraw the figure and nothing reaches you at all. |
| net debt vs the issuer's own net debt | 162,122 | DATA MISSING | — | the issuer publishes none on this basis, or none is entered — never a disagreement of zero |
| FCF0 / net income (conversion) | 223,851 | 332,074 | 0.67x | inside the 0.2-3x band -- both figures are on the same kind of basis |

*E101: E40 verifies that a figure was correctly TRANSCRIBED from the page it names; nothing in this project has ever checked that it was CONSTRUCTED right. These three do — and **none of them is authoritative and none adjudicates.** The issuer's definitions are not this project's (interest under E34, the pension leg under E35.1), so a gap is a prompt to look and never a finding that either figure is wrong. **Nothing here adjusts, refuses or blocks anything.** A comparator the issuer does not publish is DATA MISSING, never a disagreement of zero.*

*E103: the comparators are REFERENCE figures — compared against a valuation, never used to build one — so they are fetched automatically and entered UNVERIFIED, and no §5 basis may read them. Where a check disagrees, the line names the ONE figure to read back. **The read-back moves from every figure in advance to the figure that actually blinked.***

## NO MBP, and that is E111 and B22 rather than an omission

This name is **INTAKE**: read, not watched. It carries no tier, and the MBP is `fv_base` × the tier cushion — so **no maximum buy price exists and none is written here.** What it *would* be at each tier (E90's cushion on the BASE case) is printed so the owner sees the range before scoring; **none of them is the MBP, and all of them inherit this page's PROVISIONAL label.**

| tier | MBP would be |
|---|---:|
| 1 | 26.55 NOK |
| 2 | 23.43 NOK |
| 3 | 20.30 NOK |

## What was written

`reference/BOUV.OL-STRIKE-2026-09-08.md` (this file) and `reference/run-records/BOUV.OL-2026-09-08.json` — every leg, every page, zero hand inputs. **`config/watchlist.yaml` was not touched**, and this script asserts its SHA-256 is unchanged before it exits.

