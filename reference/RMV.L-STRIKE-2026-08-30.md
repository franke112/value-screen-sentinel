# RMV.L -- first section 5 strike on the tool path, 2026-08-30

**2026-08-30 19:16 CEST. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The section 5 run record is written to `reference/run-records/RMV.L-2026-08-30.json` so that linking it to a watchlist entry (`run_record:`) remains the owner's write.

Growth view: `reference/growth-views/RMV.L.md`, pre-registered by the owner 2026-08-30, BEFORE this script ran and before g* was solved (E28's binding order).

Tool: `tools/strike_rmv_rkt_pndora_deck_2026_08_30.py` at `RMV.L/RKT.L/PNDORA.CO/DECK first strikes, 2026-08-30, d4425b5`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# RMV.L -- section 5 strike, 2026-08-30 19:16 CEST

Store: `config/manual/RMV.L.yaml` (money_unit thousands). **BASIS: `2025-FY`, the twelve months ending 2025-12-31** (E19), 242 days old; the Half-year Financial Report to 2026-06-30 (RNS, 2026-07-31) is the newer filed period the annual basis passes over (E31). Price: last SETTLED close **513.60 GBX** (5.14 GBP at 100 GBX per GBP) on 2026-08-27 (tool fetch, 2026-08-30 19:16 CEST).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED.

- record complete: **True**
- **FCF0: 215.7 GBP m** -- net interest paid -1.9 GBP m added back (E34)
- **share-based compensation (E36): 8.5 GBP m deducted = 4.0% of FCF0** (3.8% of the flow before the deduction)
- lease principal (E70): 0.0 GBP m added back (0.0% of FCF0); the lease liability stays in net debt
- **net debt: -34.0 GBP m (NET CASH)** -- borrowings 0 + 0 + leases 7,184 (E35: always in; finance leases beside operating, E65) + pension deficit 0 (E35.1) + asset retirement obligations 1,717 (E68) + prepaid delivery obligations 0 (E81) - cash 37,223 - other current financial assets 5,683. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1)
- **asset-retirement leg (E68): 1,717.0 (store unit)**, a stated figure (declaration 8): note 20 PROVISIONS, p.133: 'The dilapidations provision is in respect of any of the Group's leased properties where the Group has obligations to make good dilap
- divisor: 775,356,560 shares -- weighted-average DILUTED count for 2025-FY, the same window as the flows (E38) (`divisor_basis: weighted_average`)

- **fv_base (Method C, E28): 4.27 GBP**
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **4.60 / 4.27 / 3.99 GBP**
- bear (g 0.0%): **3.43 GBP**
- bull (g 6.0%): **5.32 GBP**
- implied growth g* at the settled close 5.14 GBP: **5.51%** (E28; the view in `reference/growth-views/RMV.L.md` was fixed 2026-08-30, before this was solved)
- *r 9.5% flat; non-USD bias: conservative* (E37)

- **tier: NOT SCORED. MBP: DATA MISSING** -- E28's MBP is the bear-case value times the tier cushion, and section 4.4 has not scored RMV.L, so there is no tier to apply. **Not struck; not computed on a placeholder.** What it WOULD be against the bear case 3.43 GBP, across E29's band, so the range is visible before scoring. **E77: the regime is ELEVATED, so whatever tier section 4.4 produces is applied one tier stricter** (a Tier 1 score takes the tier 2 line below, a Tier 2 score the tier 3 line):
  - tier 1 (x0.80): **2.75 GBP** (r 9.0% 2.95 / r 10.0% 2.58); price 5.14 is +87.0% against it
  - tier 2 (x0.70): **2.40 GBP** (r 9.0% 2.58 / r 10.0% 2.25); price 5.14 is +113.7% against it
  - tier 3 (x0.60): **2.06 GBP** (r 9.0% 2.21 / r 10.0% 1.93); price 5.14 is +149.3% against it

<details><summary>the run record -- every leg of the bridge (declaration 4, item by item) and every input with its provenance (declaration 8), including every proxy and every caption zero</summary>

# section 5 run record — RMV.L — 2026-08-30T19:16:25+02:00

**Fair value 4.27 GBP** at g 3.00%, r 9.50%.

*r 9.5% flat; non-USD bias: conservative*

- **FCF0:** 215,681 GBP thousands

- **basis (E19):** 2025-FY

- **units:** money stated in thousands, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 775,356,560 — weighted-average DILUTED count for 2025-FY, the same window as the flows (E38), as of 2025-12-31; divisor basis `weighted_average` (E75 / E75.1); memo (E38, never the divisor): — |
| 2 | share-based compensation | deducted, 8,539 |
| 3 | interest | interest paid is INSIDE operating cash flow, so -1,900 is ADDED BACK, as printed and PRE-TAX, and net debt is then subtracted ONCE (E34). The pre-tax add-back is the generous end of E34's own band. Read from: Annual report and accounts 2025 (audited); Half-year Financial Report 2026 (RNS, unaudited) p.117, consolidated statement of cash flows: 'Financial expenses paid (535)' sits INSIDE cash flows from operating activities, between 'Cash generated from operating activities 308,015' and 'Net cash from operating activities 236,299' (beside 'Income taxes paid (71,181)'); 'Interest received on cash and cash equivalents 2,435' sits in cash flows used in INVESTING activities, outside. So the operating cash flow already bears every finance cost PAID (note 8, p.128: the £557k charge is 'Bank charges 455', 'Interest unwind on lease liabilities 90', 'Interest unwind on dilapidations 12') and does not contain the interest RECEIVED -- the conservative side. The interim keeps the placement: 'Financial expenses paid (272)' in operating, 'Interest received on cash and cash equivalents 1,116' in investing |
| 3.1 | lease principal (E70) | the operating cash flow does NOT bear the lease principal (IFRS 16.50(b): in financing), so nothing is added back -- the lease is charged once, in net debt (E35, E65, E70). Read from: FRAMEWORK-EDITS E70, applied 2026-08-30 to an IFRS 16 filer IFRS 16.50(b): a lessee classifies cash payments for the principal portion of the lease liability within FINANCING activities; p.117 shows exactly that, 'Payment of principal portion of lease liabilities 19 (3,146)' under cash flows used in financing activities. The interest portion follows the filer's IAS 7 policy, which `interest_in_ocf` records (80 inside 'Financial expenses paid'). The standard leaves no choice on the principal |
| 4 | bridge | net debt -34,005 — borrowings 0 + 0 + leases 7,184 (E35: always in; finance leases beside operating, E65) + pension deficit 0 (E35.1) + asset retirement obligations 1,717 (E68) + prepaid delivery obligations 0 (E81) - cash 37,223 - other current financial assets 5,683. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: split: capex_ppe + capex_intangibles, as the accounts print them |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 3.00% from `reference/growth-views/RMV.L.md` (2026-08-30) |
| 7 | as-of dates | flows to 2025-12-31; balance sheet 2025-12-31; share count 2025-12-31; price 2026-08-27 — **THEY AGREE** |
| 8 | provenance | 14 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | 5,683 |
| `leases` | 7,184 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 0 (stated) |
| `current_financial_assets` | 5,683 |
| `asset_retirement_obligations` | 1,717 |
| `prepaid_delivery_obligations` | 0 (stated) |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_ppe` | -903 | store | VERIFIED (cross_document) | p.117, cash flows used in investing activities: 'Acquisition of property, plant and equipment 12 (903)'; note 12, p.130: 'Additions ... 903' (leased asset additions 4,159 are separate, non-cash); cross-checked against the ESEF/iXBRL package, tag ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities, context c-1, scale 3: 903, sign attribute absent -- same magnitude, sign by convention (outflow tagged positive; this field signs it negative), not a discrepancy. E40 cross_document |
| `capex_intangibles` | -9,276 | store | VERIFIED (cross_document) | p.117, cash flows used in investing activities: 'Acquisition of intangible assets 13 (9,276)'; note 13, p.130: 'Additions – 6,509 2,767 – 9,276' (computer software 6,509, software development 2,767); cross-checked against the ESEF/iXBRL package, tag ifrs-full:PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities, context c-1, scale 3: 9,276, sign attribute absent -- same magnitude, sign by convention, not a discrepancy. E40 cross_document |
| `operating_cash_flow` | 2.363e+05 | store | VERIFIED (cross_document) | p.117, consolidated statement of cash flows: 'Net cash from operating activities 236,299' (2024: 211,270) -- after 'Financial expenses paid (535)' and 'Income taxes paid (71,181)'. operating_cash_flow_pretax is deliberately NOT entered: the statement presents the flow after tax, and its pre-tax subtotal 'Cash generated from operating activities 308,015' is also pre-interest, so pretax-plus-tax would not reproduce this line; cross-checked against the ESEF/iXBRL package, tag ifrs-full:CashFlowsFromUsedInOperatingActivities, context c-1, scale 3: 236,299 -- agrees (E40 cross_document) |
| `sbc` | 8,539 | store | VERIFIED (cross_document) | p.117, adjustments to profit: 'Share-based payments 23 8,539'; note 23, p.135: 'The Group recognised a total share-based payments charge for the year of £8,539,000' -- Sharesave 500, PSP 336, DSP 3,244, SIP 1,606, RSP 2,853 = 'Total share-based payments charge 8,539'; the 'NI on applicable share-based incentives at 15.0% 1,276' that lifts it to the income statement's 9,815 is a cash cost the flow already bears and is excluded (E36; AUTO.L convention). All schemes equity-settled (p.123); cross-checked against the ESEF/iXBRL package, tag ifrs-full:AdjustmentsForSharebasedPayments, context c-1, scale 3: 8,539 -- agrees; the package tags the income-statement line separately as ifrs-full:ExpenseFromSharebasedPaymentTransactionsWithEmployees 9,815, the charge plus NI, which this field deliberately does not enter (E40 cross_document) |
| `net_interest_paid` | -1,900 | store | VERIFIED (cross_document) | E18: finance_costs_paid - finance_income_received, both on 2025-FY |
| `diluted_weighted_average_shares` | 7.754e+08 | store | VERIFIED (cross_document) | note 10, p.129, 'Weighted average number of ordinary shares (diluted)': basic 772,382,123 + 'Dilutive impact of share-based incentives outstanding 2,974,437' = 775,356,560 (2024: 792,601,981); p.115 'Diluted 10 28.0' pence reconciles (217,067 / 775,356.56 = 28.0). E59 (2026-08-30), the AUTO.L precedent: the count reconciles to rounding against the separately-prepared primary statement, both of whose inputs are ESEF-tagged -- ifrs-full:ProfitLoss 217,067,000 / ifrs-full:DilutedEarningsLossPerShare 0.280 (u-2 GBP/shares, decimals 3) = 775,239,286 point estimate, 117,274 shares (0.015%) off the stated count, inside the band [773,857,398 to 776,626,118] implied by 28.0p's own half-tenth rounding. No share COUNT is tagged anywhere in the package (units u-1 GBP and u-2 GBP/shares only, no xbrli:shares unit), so this is the only second read available; cross_document under E59 |
| `financial_liabilities_current` | 0 | store | VERIFIED (caption_statement) | p.116, current liabilities: 'Trade and other payables 18 (32,568)', 'Lease liabilities 19 (3,562)', 'Contract liabilities 4 (3,485)', 'Income tax payable (501)', 'Other current liabilities 17 (428)' -- no borrowings caption. The 428 is the deferred consideration for HomeViews Platform Limited payable February 2026 (note 17 p.132), NAMED here and not a leg of E35's net debt; p.59 (Investment case): 'no external debt' |
| `financial_liabilities_noncurrent` | 0 | store | VERIFIED (caption_statement) | p.116, non-current liabilities: 'Other non-current liabilities 17 –', 'Lease liabilities 19 (3,622)', 'Provisions 20 (1,717)' -- no borrowings caption; there is no borrowings note in the report |
| `lease_liabilities` | 7,184 | store | VERIFIED (cross_document) | note 19, p.132, 'Lease liabilities included in the statement of financial position': 'Current 3,562', 'Non-current 3,622', '7,184' -- the stated total; p.116 carries the two parts as 'Lease liabilities 19 (3,562)' and 'Lease liabilities 19 (3,622)'; note 19 p.133 reconciliation 'Balance as at 31 December 7,184'. E65: one IFRS 16 lessee liability, no finance/operating split exists to size; cross-checked against the ESEF/iXBRL package: no total is tagged, but ifrs-full:CurrentLeaseLiabilities 3,562 and ifrs-full:NoncurrentLeaseLiabilities 3,622 (context c-3, scale 3) sum to 7,184 exactly -- agrees on both stated parts (E40 cross_document) |
| `pension_deficit` | 0 | store | VERIFIED (caption_statement) | p.123, note 2 material accounting policy information, Employee benefits (i) Pensions: 'The Group provides access to stakeholder pension schemes (defined contribution pension plans). Obligations for contributions to defined contribution pension plans are recognised as an employee benefit expense in the income statement when they are incurred.' No pension caption on p.116; note 6, p.128: 'Pension costs 3,730'. E35.1's note form |
| `asset_retirement_obligation` | 1,717 | store | VERIFIED (cross_document) | note 20 PROVISIONS, p.133: 'The dilapidations provision is in respect of any of the Group's leased properties where the Group has obligations to make good dilapidations' -- 'At 1 January 853', 'Charged 852', 'Unwinding of discount 12', 'At 31 December 1,717', 'Current –', 'Non-current 1,717'; p.116 'Provisions 20 (1,717)'. Entered under E68 via E69 on AUTO.L's dilapidations precedent (E68.1 applications table); cross-checked against the ESEF/iXBRL package, tag ifrs-full:NoncurrentProvisions, context c-3, scale 3: 1,717 -- agrees; note 20 states the dilapidations provision is the only provision (Current –, Non-current 1,717), so the tagged caption IS this figure (E40 cross_document) |
| `prepaid_delivery_obligation` | 0 | store | VERIFIED (cross_document) | E81 (2026-08-30): p.116, consolidated statement of financial position at 31 December 2025, liabilities presented: 'Trade and other payables (32,568)', 'Lease liabilities (3,562)', 'Contract liabilities (3,485)', 'Income tax payable (501)', 'Other current liabilities (428)', 'Other non-current liabilities -', 'Lease liabilities (3,622)', 'Provisions (1,717)' -- no streaming, prepaid-offtake or prepaid-delivery caption. 'Contract liabilities 3,485' is subscription revenue billed in advance (note 4), the ordinary contract liability of a property portal, working capital and NOT this leg, named here. A caption zero. Cross-checked against the ESEF/iXBRL package (E59, component sum): the tagged liability captions at context c-3 are TradeAndOtherCurrentPayables 32,568, CurrentLeaseLiabilities 3,562, CurrentContractLiabilities 3,485, CurrentTaxLiabilities 501, OtherCurrentLiabilities 428 (= CurrentLiabilities 40,544 exactly), NoncurrentLeaseLiabilities 3,622, NoncurrentProvisions 1,717, OtherNoncurrentFinancialLiabilities – (= NoncurrentLiabilities 5,339 exactly), Liabilities 45,883 = 40,544 + 5,339 -- the tagged captions exhaust the total, leaving no room for a prepaid-delivery caption. The absence is read a second time from the tagged balance sheet; cross_document |
| `cash_and_equivalents` | 3.722e+04 | store | VERIFIED (cross_document) | p.116, consolidated statement of financial position: 'Cash and cash equivalents 17 37,223'; note 17, p.132, confirms, and names £101,000 restricted under the EBT deeds, £5,598,000 in a 30-day deposit account and £428,000 ringfenced for the HomeViews deferred consideration; cross-checked against the ESEF/iXBRL package, tag ifrs-full:CashAndCashEquivalents, context c-3, scale 3: 37,223 -- agrees (E40 cross_document) |
| `other_current_financial_assets` | 5,683 | store | VERIFIED (cross_document) | p.116: 'Money market deposits 17 5,683'; note 17, p.132: original maturity of more than three months and less than a year, weighted average rate 3.6%. Assumption A1 decides whether it counts as cash; cross-checked against the ESEF/iXBRL package, issuer extension tag rightmoveplc:MoneyMarketDeposits, context c-3, scale 3: 5,683 -- agrees (E40 cross_document) |

*Tool commit: `RMV.L/RKT.L/PNDORA.CO/DECK first strikes, 2026-08-30, d4425b5`.*


</details>

### RMV.L -- the framework's own output on the price (NOT a recommendation)

- price 5.14 GBP vs fv_base 4.27 GBP: **+20.3%** -- price is ABOVE fv_base
- price 5.14 GBP vs FV_bull 5.32 GBP: **-3.5%** -- price is BELOW the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': FIRES** (price >= fv_base). A trim presupposes a position; none is held.
- **C4 (E42: no horizon -- above FV_bull the full position is sold at the next session): does not fire.** Price is below FV_bull. Expected return from 5.14 to FV_bull 5.32 is **+3.7%** against the index core's 7.0% a year (E29's anchor); read as ONE year, the bull-case gap is BELOW the index.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are not written there.
- **It does not score tier.** Section 4.4 has not run for RMV.L; MBP is printed as DATA MISSING, and the per-tier figures are the range, not a choice (E76: the reading comes before the tier, not before this strike).
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.
