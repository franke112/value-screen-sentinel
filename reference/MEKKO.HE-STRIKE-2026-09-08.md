# MEKKO.HE — section 5, 2026-09-08 — **STRUCK**

## THE GATE OPENS

`section5_gate` returns **0 refusals**. E21 refuses section 5 on an UNVERIFIED figure the basis reads; it refuses nothing here, and **this is a struck fair value rather than the arithmetic of one.**

**HOW IT OPENED, STATED PLAINLY — four read-backs and twenty waivers, not twenty-four read-backs.** The store carries **24 figures the basis reads. FOUR are VERIFIED by the owner against a rendered page on 2026-09-08 (E40)**: `operating_cash_flow` `cross_document` (audited annual report p.86 and the Bulletin p.26), `diluted_weighted_average_shares` `same_page` (p.31 and note 10 on p.96), `net_finance_costs` `same_page` (p.84), `shares_issued_period_end` `same_page` (p.24). **The other 20 were never read back and are exempt** — 12 under E108's measured floor, 8 under E113. They are named below so the waiver is visible rather than silent.

**WHAT THAT COSTS, SAID ONCE.** E94's second fence is *every figure the basis reads VERIFIED under E40*, and on its literal words this record does not clear it — twenty figures hold a page nobody has looked at. **E108 and E113 are the framework's own answer to that**: a leg that cannot move `fv_base` by 1%, or that `fv_base` never reads at all, is not a reason to refuse a value. **Both waive the READ-BACK and neither waives the PROVENANCE** — every one of the twenty keeps its page and every zero keeps its `zero_basis` under E25. The value below is struck on that basis and on no other.

**Growth view registered 2026-09-08 by the owner, in his own words, BEFORE this ran (E28).** bear 3% / base 5% / bull 10%, from `reference/growth-views/MEKKO.HE.md`. **Read off the FILE and not off a watchlist `growth:` block (E109)**: MEKKO.HE has no watchlist entry and E109 ruled that case — entering a name stamps `dd_at_entry` and freezes Gate 1 under E12.

Basis `annual FY2025`, ending 2025-12-31. Rate 9.5% (7.0% core + 2.5% premium, E29). Settled close 9.39 EUR on 2026-09-04.

## The value — STRUCK

| | EUR |
|---|---:|
| **fv_base** (g 5%) | **14.03** |
| E29 band, low — r 9.0% | 15.14 |
| E29 band, high — r 10.0% | 13.06 |
| FV_bear (g 3%) | 12.12 |
| FV_bull (g 10%) | 20.28 |

**E29 forbids reporting the middle alone**, and the band above is why: half a point of r moves this value by 2.08 EUR, 14.8% of fv_base.

## What the price implies

- settled close **9.39 EUR** on 2026-09-04
- **g\*, the growth the price implies at r 9.5%: -0.53%** — against the owner's registered base of 5%
- price vs fv_base: **-33.0%**
- price vs FV_bear: **-22.5%**
- price vs FV_bull: **-53.7%**

**g\* ACROSS E29's BAND, because the middle alone is not reportable here either:** r 9.0% → **-1.47%**, r 9.5% → **-0.53%**, r 10.0% → **0.38%**. **At every rate in the band the price implies LESS growth than the owner's BEAR case of 3%** — the market is pricing a slower company than his most pessimistic view.

## WHAT THE GATE EXEMPTED, AND ON WHICH GROUND

**Neither ground is a relaxation and both are visible here by rule.** E113 was ruled this morning and says in its own text that the gate must state which fields it exempted, so the exemption can be argued with rather than trusted.

**E108 — MEASURED: ±10% of the leg moves `fv_base` by less than 1% (12 fields).** `asset_retirement_obligation`, `capex_combined`, `cash_and_equivalents`, `finance_costs_paid`, `finance_income_received`, `financial_liabilities_current`, `financial_liabilities_noncurrent`, `lease_liabilities`, `nci_dividends_paid`, `pension_deficit`, `prepaid_delivery_obligation`, `sbc`.

*This limb had never fired on any name before today.* `RunRecord.sensitivity()` spoke the BRIDGE's vocabulary — `leases`, `pensions`, `net_debt`, `capex` — and the gate refused on STORE field names — `lease_liabilities`, `pension_deficit`, `cash_and_equivalents`. The intersection was empty on every store in the repo. That is a defect and it was fixed as one; the two sides now share a vocabulary and a test fails if a bridge key ever stops matching its store field.

**E113 — STRUCTURAL: the `fv_base` computation never reads the field at all (8 fields).** `depreciation_amortisation`, `diluted_eps`, `ebitda`, `lease_payments_capital`, `net_debt_ebitda`, `net_income`, `operating_income`, `revenue`.

*E113 is NARROWER than the sentence that names it.* "fv_base never reads it" is necessary and **not sufficient**: `net_finance_costs` and its operands are read by E25's zero-coverage denominator outside FCF0 entirely, and the point-in-time share counts are operands of E54/E80's subtraction — both are excluded from the exemption, and `net_finance_costs` and `shares_issued_period_end` were read back by hand on 2026-09-08 for exactly that reason.

**A REFUSAL THAT NEVER AROSE, for completeness.** Five further figures in this store are UNVERIFIED and appear on neither list — `free_cash_flow_reported`, `total_assets`, `net_ppe`, `op_margin` and `revenue_yoy`. The gate never considered them because **the basis does not read them**: the first is an E103 REFERENCE figure, which §5 is forbidden to read, and the rest are section 4 furniture. Nothing was exempted there because nothing was ever at stake.

## E108's floor on this record's own fv_base, leg by leg

E108 exempts a leg whose ±10% perturbation moves `fv_base` by less than 1%. **The floor is measured here against the 14.03 EUR above**, which is what E108 requires and what the intake could not do, having no `fv_base` to measure against.

| leg | value | ±10% moves `fv_base` by | |
|---|---:|---:|---|
| `operating_cash_flow` | 34.50 | **10.68%** | **VERIFIED (cross_document)** |
| `diluted_weighted_average_shares` | 40,571,380 | **9.09%** | **VERIFIED (same_page)** |
| `capex_combined` | -2.90 | **0.90%** | exempt (E108) |
| `cash_and_equivalents` | 36.60 | **0.64%** | exempt (E108) |
| `lease_liabilities` | 29.70 | **0.52%** | exempt (E108) |
| `finance_costs_paid` | 1.30 | **0.40%** | exempt (E108) |
| `sbc` | 0.50 | **0.15%** | exempt (E108) |
| `finance_income_received` | 0.50 | **0.15%** | exempt (E108) |

**Both legs above the floor were read back by the owner on 2026-09-08 and are VERIFIED.** Everything else in this table is under 1%. **E108 waives the READ-BACK and never the PROVENANCE** — every figure keeps its page, and every zero keeps its `zero_basis` under E25.

*Recomputed on any change of basis, as E108 requires: a new year re-decides this list rather than inheriting it.*

## The legs

- FCF0 **31,900,000 EUR**
- net cash **6,900,000 EUR**
- divisor **40,571,380** shares — weighted-average DILUTED count for annual FY2025, the same window as the flows (E38)

## Construction checks (E101) — DETECTORS, NOT VERDICTS

| check | this record | the issuer | measure | |
|---|---:|---:|---:|---|
| FCF0 vs the issuer's own free cash flow | 32 | 32 | +0.9% | E34's construction against the issuer's; the two definitions differ by design (interest, leases), so a gap is a PROMPT |
| net debt vs the issuer's own net debt | -7 | DATA MISSING | — | the issuer publishes none on this basis, or none is entered — never a disagreement of zero |
| FCF0 / net income (conversion) | 32 | 24 | 1.31x | inside the 0.2-3x band -- both figures are on the same kind of basis |

*E101: E40 verifies that a figure was correctly TRANSCRIBED from the page it names; nothing in this project has ever checked that it was CONSTRUCTED right. These three do — and **none of them is authoritative and none adjudicates.** The issuer's definitions are not this project's (interest under E34, the pension leg under E35.1), so a gap is a prompt to look and never a finding that either figure is wrong. **Nothing here adjusts, refuses or blocks anything.** A comparator the issuer does not publish is DATA MISSING, never a disagreement of zero.*

*E103: the comparators are REFERENCE figures — compared against a valuation, never used to build one — so they are fetched automatically and entered UNVERIFIED, and no §5 basis may read them. Where a check disagrees, the line names the ONE figure to read back. **The read-back moves from every figure in advance to the figure that actually blinked.***

## NO MBP, and that is E111 and B22 rather than an omission

This name is **INTAKE**: read, not watched. It carries no tier, and the MBP is `fv_base` × the tier cushion — so **no maximum buy price exists and none is written here.** What it *would* be at each tier (E90's cushion on the BASE case) is printed so the owner sees the range before scoring; **none of them is the MBP.**

| tier | MBP would be |
|---|---:|
| 1 | 11.92 EUR |
| 2 | 10.52 EUR |
| 3 | 9.12 EUR |

## What was written

`reference/MEKKO.HE-STRIKE-2026-09-08.md` (this file) and `reference/run-records/MEKKO.HE-2026-09-08.json` — every leg, every page, zero hand inputs. **`config/watchlist.yaml` was not touched**, and this script asserts its SHA-256 is unchanged before it exits.

