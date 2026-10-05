# RKT.L -- first section 5 strike on the tool path, 2026-08-30

**2026-08-30 19:16 CEST. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The section 5 run record is written to `reference/run-records/RKT.L-2026-08-30.json` so that linking it to a watchlist entry (`run_record:`) remains the owner's write.

Growth view: `reference/growth-views/RKT.L.md`, pre-registered by the owner 2026-08-30, BEFORE this script ran and before g* was solved (E28's binding order).

Tool: `tools/strike_rmv_rkt_pndora_deck_2026_08_30.py` at `RMV.L/RKT.L/PNDORA.CO/DECK first strikes, 2026-08-30, d4425b5`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# RKT.L -- section 5 strike, 2026-08-30 19:16 CEST

Store: `config/manual/RKT.L.yaml` (money_unit millions). **BASIS: `2025-FY`, the twelve months ending 2025-12-31** (E19), 242 days old; the Results for the Six Months Ended 30 June 2026 (2026-07-29) is the newer filed period the annual basis passes over (E31). Price: last SETTLED close **5116.00 GBX** (51.16 GBP at 100 GBX per GBP) on 2026-08-27 (tool fetch, 2026-08-30 19:16 CEST).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED.

- record complete: **True**
- **FCF0: 1,884.0 GBP m** -- net interest paid 303.0 GBP m added back (E34)
- **share-based compensation (E36): 101.0 GBP m deducted = 5.4% of FCF0** (5.1% of the flow before the deduction)
- lease principal (E70): 0.0 GBP m added back (0.0% of FCF0); the lease liability stays in net debt
- **net debt: 6,695.0 GBP m** -- borrowings 745 + 7,411 + leases 274 (E35: always in; finance leases beside operating, E65) + pension deficit 217 (E35.1) + asset retirement obligations 0 (E68) + prepaid delivery obligations 0 (E81) - cash 1,952 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1)
- **asset-retirement leg (E68): 0 -- a CAPTION ZERO, not a figure**; its form and its second read are on the field.
- divisor: 681,142,714 shares -- weighted-average DILUTED count for 2025-FY, the same window as the flows (E38) (`divisor_basis: weighted_average`)

- **fv_base (Method C, E28): 32.20 GBP**
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **35.46 / 32.20 / 29.37 GBP**
- bear (g 0.0%): **23.88 GBP**
- bull (g 5.0%): **38.91 GBP**
- implied growth g* at the settled close 51.16 GBP: **8.01%** (E28; the view in `reference/growth-views/RKT.L.md` was fixed 2026-08-30, before this was solved)
- *r 9.5% flat; non-USD bias: conservative* (E37)

- **tier: NOT SCORED. MBP: DATA MISSING** -- E28's MBP is the bear-case value times the tier cushion, and section 4.4 has not scored RKT.L, so there is no tier to apply. **Not struck; not computed on a placeholder.** What it WOULD be against the bear case 23.88 GBP, across E29's band, so the range is visible before scoring. **E77: the regime is ELEVATED, so whatever tier section 4.4 produces is applied one tier stricter** (a Tier 1 score takes the tier 2 line below, a Tier 2 score the tier 3 line):
  - tier 1 (x0.80): **19.10 GBP** (r 9.0% 21.08 / r 10.0% 17.39); price 51.16 is +167.8% against it
  - tier 2 (x0.70): **16.72 GBP** (r 9.0% 18.44 / r 10.0% 15.22); price 51.16 is +206.0% against it
  - tier 3 (x0.60): **14.33 GBP** (r 9.0% 15.81 / r 10.0% 13.04); price 51.16 is +257.1% against it

<details><summary>the run record -- every leg of the bridge (declaration 4, item by item) and every input with its provenance (declaration 8), including every proxy and every caption zero</summary>

# section 5 run record — RKT.L — 2026-08-30T19:16:25+02:00

**Fair value 32.20 GBP** at g 3.00%, r 9.50%.

*r 9.5% flat; non-USD bias: conservative*

- **FCF0:** 1,884 GBP millions

- **basis (E19):** 2025-FY

- **units:** money stated in millions, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 681,142,714 — weighted-average DILUTED count for 2025-FY, the same window as the flows (E38), as of 2025-12-31; divisor basis `weighted_average` (E75 / E75.1); memo (E38, never the divisor): — |
| 2 | share-based compensation | deducted, 101 |
| 3 | interest | interest paid is INSIDE operating cash flow, so 303 is ADDED BACK, as printed and PRE-TAX, and net debt is then subtracted ONCE (E34). The pre-tax add-back is the generous end of E34's own band. Read from: Annual Report and Accounts 2025 (audited); Results for the six months ended 30 June 2026 (unaudited) AR p.136, Group Cash Flow Statement: 'Cash generated from continuing operations 3,501', then 'Interest paid (344)', 'Interest received 41', 'Tax paid (897)', 'Net cash flows attributable to discontinued operations (4)', 'Net cash generated from operating activities 2,297' -- both interest lines INSIDE operating activities. H1 p.22 the same placement: 'Interest paid (152)', 'Interest received 48' above 'Net cash generated from operating activities 614' |
| 3.1 | lease principal (E70) | the operating cash flow does NOT bear the lease principal (IFRS 16.50(b): in financing), so nothing is added back -- the lease is charged once, in net debt (E35, E65, E70). Read from: FRAMEWORK-EDITS E70, applied 2026-08-30 to an IFRS 16 filer IFRS 16.50(b): lease principal is a financing flow; Reckitt presents lease liabilities inside borrowings (AR note 17 p.164: 'Lease liabilities 19 | 65' current and '209' non-current within total borrowings) and repays them inside 'Repayment of borrowings' (p.136) with no separate lease line; lease interest 13 is in 'Interest paid' (note 6 p.147 'Interest payable on leases (13)') |
| 4 | bridge | net debt 6,695 — borrowings 745 + 7,411 + leases 274 (E35: always in; finance leases beside operating, E65) + pension deficit 217 (E35.1) + asset retirement obligations 0 (E68) + prepaid delivery obligations 0 (E81) - cash 1,952 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: split: capex_ppe + capex_intangibles, as the accounts print them |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 3.00% from `reference/growth-views/RKT.L.md` (2026-08-30) |
| 7 | as-of dates | flows to 2025-12-31; balance sheet 2025-12-31; share count 2025-12-31; price 2026-08-27 — **THEY AGREE** |
| 8 | provenance | 13 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | **DATA MISSING** on this basis |
| `leases` | 274 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 217 |
| `current_financial_assets` | **DATA MISSING** on this basis |
| `asset_retirement_obligations` | 0 (stated) |
| `prepaid_delivery_obligations` | 0 (stated) |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_ppe` | -536 | store | VERIFIED (cross_document) | p.136, cash flows from investing activities, 2025: 'Purchase of property, plant and equipment (536)' (2024: (370)); cross-checked against the ESEF/iXBRL package, tag ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities, context c-1 (2025-01-01 to 2025-12-31), unit GBP, scale 6: 536 -- same magnitude; the concept is inherently an outflow tagged as a positive magnitude by iXBRL convention while this field signs outflows negative, a convention difference and not a discrepancy (E58 precedent) (E40 cross_document) |
| `capex_intangibles` | -79 | store | VERIFIED (cross_document) | p.136, cash flows from investing activities, 2025: 'Purchase of intangible assets 9 | (79)' (2024: (95)); cross-checked against the ESEF/iXBRL package, tag ifrs-full:PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities, context c-1 (2025-01-01 to 2025-12-31), unit GBP, scale 6: 79 -- same magnitude; the concept is inherently an outflow tagged as a positive magnitude by iXBRL convention while this field signs outflows negative, a convention difference and not a discrepancy (E58 precedent) (E40 cross_document) |
| `operating_cash_flow` | 2,297 | store | VERIFIED (cross_document) | p.136, Group Cash Flow Statement, 2025: 'Net cash generated from operating activities 2,297' (2024: 2,682) -- after interest paid (344), interest received 41, tax paid (897) and discontinued operations (4); cross-checked against the ESEF/iXBRL package, tag ifrs-full:CashFlowsFromUsedInOperatingActivities, context c-1 (2025-01-01 to 2025-12-31), unit GBP, scale 6: 2,297 -- agrees (E40 cross_document) |
| `sbc` | 101 | store | VERIFIED (cross_document) | p.136, adjustments to operating profit, 2025: 'Share-based payments 25 | 101'; note 25 p.174: 'All awards under these plans are equity settled. The total expense recognised in respect of share-based payments for the year was £101 million (2024: £85 million).'; note 5 p.147 'Share-based payments 25 | 101' inside employee costs; cross-checked against the ESEF/iXBRL package, tag ifrs-full:AdjustmentsForSharebasedPayments, context c-1 (2025-01-01 to 2025-12-31), unit GBP, scale 6: 101 -- agrees (E40 cross_document) |
| `net_interest_paid` | 303 | store | VERIFIED (cross_document) | E18: finance_costs_paid - finance_income_received, both on 2025-FY |
| `diluted_weighted_average_shares` | 6.811e+08 | store | VERIFIED (cross_document) | note 8, p.149, Earnings Per Share: 'On a basic basis 679,416,359', 'Dilution for Executive Share Awards 1,480,042', 'Dilution for Employee Sharesave Scheme Options 246,313', 'On a diluted basis 681,142,714' (2024: 701,742,260). E59 (2026-08-30), the AUTO.L shape: the count reconciles to rounding against the separately-prepared income statement, both inputs ESEF-tagged -- ifrs-full:ProfitLossAttributableToOwnersOfParent 3,182,000,000 / ifrs-full:DilutedEarningsLossPerShare 4.672 GBP (decimals 3) = 681,078,767, inside the band [681,005,885 to 681,151,664] implied by 467.2p's half-tenth rounding, and the continuing-operations pair (3,203 - 5 = 3,198,000,000 / ifrs-full:DilutedEarningsLossPerShareFromContinuingOperations 4.695) = 681,150,160, inside [681,077,628 to 681,222,707]; both bands contain 681,142,714. No share count is tagged in the package (units GBP and GBP/shares only, no xbrli:shares unit); cross_document under E59 |
| `financial_liabilities_current` | 745 | store | VERIFIED (cross_document) | note 17, p.164, Financial Liabilities - Borrowings, current: 'Bank loans and overdrafts 7' + 'Commercial paper -' + 'Bonds 738' + 'Senior notes -' = 745, the stated parts of 'Total short-term borrowings 810' EXCLUDING 'Lease liabilities 19 | 65' (E14, E71); note 17 p.165 maturity table: 'Within one year or on demand 7', 'Within one year: Bonds 738'. Cross-checked against the ESEF/iXBRL package under E59 (2026-08-30): the package tags only the INCLUSIVE caption, ifrs-full:CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings 810 (instant 2025-12-31, scale 6), and no lease liability; 745 + note 19's separately-stated current lease liability 65 = 810 EXACTLY, so note 17's ex-lease parts and note 19's lease split reconcile to the tagged balance-sheet caption; cross_document under E59 |
| `financial_liabilities_noncurrent` | 7,411 | store | VERIFIED (cross_document) | note 17, p.164, non-current: 'Bonds 7,012' + 'Senior notes 393' + 'Other non-current borrowings 6' = 7,411, the stated parts of 'Total long-term borrowings 7,620' EXCLUDING 'Lease liabilities 19 | 209' (E14, E71); p.165 'Gross borrowings (unsecured) 8,156' = 745 + 7,411 exactly, the issuer's own ex-lease total. Cross-checked against the ESEF/iXBRL package under E59 (2026-08-30): the package tags only the inclusive ifrs-full:LongtermBorrowings 7,620 (instant 2025-12-31, scale 6); 7,411 + note 19's non-current lease liability 209 = 7,620 EXACTLY, and 745 + 7,411 = the p.165 'Gross borrowings (unsecured) 8,156' -- two separately-prepared notes reconcile to the tagged caption; cross_document under E59 |
| `lease_liabilities` | 274 | store | VERIFIED (cross_document) | note 19, p.166: 'Lease liabilities included in the Statement of Financial Position at 31 December 274' -- 'Current 65', 'Non-current 209'; presented inside borrowings on p.134 (E65; one IFRS 16 liability). Cross-checked against the ESEF/iXBRL package under E59 (2026-08-30): no lease liability is tagged, but the tagged inclusive borrowings captions less note 17's ex-lease parts leave exactly note 19's split -- ifrs-full:CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings 810 - 745 = 65 and ifrs-full:LongtermBorrowings 7,620 - 7,411 = 209, 65 + 209 = 274 -- so note 19's total reconciles to the tagged balance sheet through a separately-prepared note; cross_document under E59 |
| `pension_deficit` | 217 | store | VERIFIED (cross_document) | p.134, non-current liabilities, 31 December 2025: 'Retirement benefit obligations 23 | (217)' (2024: 235) -- the recognised net defined-benefit LIABILITY; the separately presented 'Retirement benefit surplus 23 | 284' is not netted (E35.1); cross-checked against the ESEF/iXBRL package, tag ifrs-full:NoncurrentRecognisedLiabilitiesDefinedBenefitPlan, context c-2 (instant 2025-12-31), unit GBP, scale 6: 217 -- agrees; the surplus is tagged apart as ifrs-full:NoncurrentRecognisedAssetsDefinedBenefitPlan 284 and, as here, is not netted (E40 cross_document) |
| `asset_retirement_obligation` | 0 | store | VERIFIED (cross_document) | note 18, p.165, Provisions for Liabilities and Charges: two columns only, 'Legal provisions' (108 at 31 December 2025) and 'Other provisions' (37), total 145 (current 90, non-current 55); no decommissioning, restoration or dilapidations provision; the balance sheet p.134 presents 'Provisions for liabilities and charges' and nothing of that kind. E68.2, NOT E68.1: note 18 states 'Other provisions include environmental and other obligations throughout the Group, the majority of which are expected to be utilised within five years' -- a remediation accrual inside 'Other provisions 37', UNQUANTIFIED, so the leg is a caption zero with the accrual NAMED (E68.2); no sentence states that no such obligation exists, so E78 does not reach it. Cross-checked against the ESEF/iXBRL package under E59 (2026-08-30, component sum): the tagged provision captions are ifrs-full:CurrentProvisions 90 and ifrs-full:NoncurrentProvisions 55 (instant 2025-12-31), 145 in total, which is EXACTLY note 18's 'Legal provisions 108' + 'Other provisions 37'; no decommissioning or restoration concept is tagged anywhere in the package. The absence is read a second time from the tagged balance sheet; the E68.2 naming of the unquantified environmental obligations inside 'Other provisions' is unchanged; cross_document |
| `prepaid_delivery_obligation` | 0 | store | VERIFIED (cross_document) | E81 (2026-08-30): p.134, Group Balance Sheet at 31 December 2025, liabilities presented: short-term borrowings 810, provisions 90 / 55, trade and other payables 5,072, derivative financial instruments 51 / 95, share repurchase liability 101, current tax liabilities 526, long-term borrowings 7,620, deferred tax liabilities 2,565, retirement benefit obligations 217, other non-current liabilities 85 -- no streaming, prepaid-offtake or prepaid-delivery caption; a consumer-health and hygiene manufacturer sells from inventory. A caption zero. Cross-checked against the ESEF/iXBRL package under E59 (2026-08-30, component sum): at instant 2025-12-31 the tagged current liabilities CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings 810 + CurrentProvisions 90 + TradeAndOtherCurrentPayables 5,072 + CurrentDerivativeFinancialLiabilities 51 + reckittbenckiser:ShareRepurchaseLiability 101 + CurrentTaxLiabilitiesCurrent 526 = CurrentLiabilities 6,650 EXACTLY, and LongtermBorrowings 7,620 + NoncurrentProvisions 55 + NoncurrentDerivativeFinancialLiabilities 95 + NoncurrentRecognisedLiabilitiesDefinedBenefitPlan 217 + DeferredTaxLiabilities 2,565 + OtherNoncurrentLiabilities 85 = NoncurrentLiabilities 10,637 EXACTLY (Liabilities 17,287 = 6,650 + 10,637) -- the tagged captions exhaust the totals, leaving no room for a prepaid-delivery caption; cross_document |
| `cash_and_equivalents` | 1,952 | store | VERIFIED (cross_document) | p.134, 31 December 2025: 'Cash and cash equivalents 16 | 1,952'; note 16 p.164: cash at bank 557 + short-term bank deposits 408 + money market fund investments 987 = 1,952, of which £182 million restricted but available on demand; cross-checked against the ESEF/iXBRL package, tag ifrs-full:CashAndCashEquivalents, context c-2 (instant 2025-12-31), unit GBP, scale 6: 1,952 -- agrees (E40 cross_document) |

*Tool commit: `RMV.L/RKT.L/PNDORA.CO/DECK first strikes, 2026-08-30, d4425b5`.*


</details>

### RKT.L -- the framework's own output on the price (NOT a recommendation)

- price 51.16 GBP vs fv_base 32.20 GBP: **+58.9%** -- price is ABOVE fv_base
- price 51.16 GBP vs FV_bull 38.91 GBP: **+31.5%** -- price is ABOVE the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': FIRES** (price >= fv_base). A trim presupposes a position; none is held.
- **C4 (E42: no horizon -- above FV_bull the full position is sold at the next session): FIRES.** Price is above FV_bull. Expected return from 51.16 to FV_bull 38.91 is **-23.9%** against the index core's 7.0% a year (E29's anchor).

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are not written there.
- **It does not score tier.** Section 4.4 has not run for RKT.L; MBP is printed as DATA MISSING, and the per-tier figures are the range, not a choice (E76: the reading comes before the tier, not before this strike).
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.
