# CTSH -- re-struck under E70, 2026-08-30

**2026-08-30 04:18 EDT.** E70 (2026-08-30) counts a lease once, in net debt, never also in the flow. The prior strike (`reference/run-records/CTSH-2026-08-28.json`) was made before the ruling existed and charged the lease twice; this strike carries declaration 3.1 and is written to `reference/run-records/CTSH-2026-08-30-e70.json`. the CTSH entry in `config/watchlist.yaml` is the OWNER'S write, made by hand from this printout with a dated backup beside it.

Growth view: `reference/growth-views/CTSH.md`, registered by the owner 2026-08-27, UNCHANGED (E28).

Tool: `tools/restrike_e70_2026_08_30.py` at `E70 re-strike, 2026-08-30, d171724`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# CTSH -- section 5 strike under E70, 2026-08-30 04:18 EDT

Store: `config/manual/CTSH.yaml`. **BASIS: `annual FY2025`, the twelve months ending 2025-12-31** (E19). Price: last SETTLED close **64.04 USD** (64.04 USD at 1:1) on 2026-08-28 (tool fetch, 2026-08-30 04:18 EDT).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED.

- record complete: **True** -- eight declarations and declaration 3.1 (E70)
- **FCF0: 2,643.0 USD m** -- proxy (E61 / E61.1): interest income not tagged, or not stated anywhere in the filing; add-back overstated by the unrecorded income (bound: 1.4% of FCF0, 37.0 USD m added back)
- **FCF0 BEFORE the lease add-back: 2,451.0 USD m; AFTER: 2,643.0 USD m** -- leg `operating_lease_payments` 192.0 USD m added back (E70, declaration 3.1: the operating cash flow bears the operating lease payments, ASC 842-20-45-5(a); the lease liability 598.0 USD m is in net debt under E35, so the flow no longer charges it a second time). The correction RAISES FCF0 by +7.8%.
- prior strike (2026-08-28, before E70): FCF0 2,451.0 USD m -- EQUALS the BEFORE figure: nothing but the add-back moved.
- **net debt: -467.0 USD m** -- borrowings 33,000,000 + 543,000,000 + leases 598,000,000 (E35: always in; finance leases beside operating, E65) + pension deficit 260,000,000 (E35.1) + asset retirement obligations 0 (E68) - cash 1,901,000,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1) (UNCHANGED by E70: the lease was already in)

- **fv_base (Method C, E28): 89.38 USD** (prior 83.01: **+7.7%**). E70 alone on the prior record gives 89.43; the rest is the bridge, which moved between the strikes from net debt -489.0 to -467.0 USD m (leases 576.0 -> 598.0: E65's finance leases beside operating, applied to the file after the prior strike).
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **96.38 / 89.38 / 83.33 USD** (prior 89.49 / 83.01 / 77.39)
- bear (g 0.0%): **66.83 USD** (prior 62.09)
- bull (g 7.0%): **111.48 USD** (prior 103.50)
- implied growth g* at the settled close 64.04 USD: **-0.59%** (E28; the view in `reference/growth-views/CTSH.md` was fixed 2026-08-27, before any fair value and before g* -- UNCHANGED here)
- *r 9.5% flat* (E37)

- **tier 2 (section 4.4, scored 2026-08-29, NOT re-scored here). MBP (E28): 46.78 USD** = bear 66.83 x 0.70 (band r 9.0% 50.15 / r 10.0% 43.85); prior MBP 43.46 USD (band 46.59 / 40.75) against the prior bear 62.09. Price 64.04 is +36.9% against the new MBP.

<details><summary>the run record -- every declaration, 3.1 among them, and every input with its provenance</summary>

# section 5 run record — CTSH — 2026-08-30T04:18:17-04:00

**Fair value 89.38 USD** at g 4.00%, r 9.50%.

*r 9.5% flat*

- **FCF0:** 2,643,000,000 USD whole — proxy (E61 / E61.1): interest income not tagged, or not stated anywhere in the filing; add-back overstated by the unrecorded income (bound: 1.4% of FCF0)

- **basis (E19):** annual FY2025

- **units:** money stated in whole, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 489,000,000 — weighted-average DILUTED count for annual FY2025, the same window as the flows (E38), as of 2025-12-31; memo (E38, never the divisor): 479,000,000 as of 2025-12-31 |
| 2 | share-based compensation | deducted, 181,000,000 |
| 3 | interest | interest paid is INSIDE operating cash flow; the filer tags gross interest expense but no net and no interest-received figure, so the add-back is the TAGGED INTEREST EXPENSE ALONE, 37,000,000 -- a PROXY (E61), bounded and one-sided: interest income is never negative, so this can only OVERSTATE FCF0, by no more than the unrecorded interest income, and net debt is then subtracted ONCE. Read from: SEC XBRL companyfacts for CIK 0001058290 (Cognizant Technology Solutions Corporation) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0001058290.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 230-10-45-17(d): under US GAAP interest paid is an OPERATING cash outflow for every filer, so this filer's `operating_cash_flow` already bears its interest. No tag states it because the standard leaves no choice to state |
| 3.1 | lease principal (E70) | the operating cash flow BEARS the operating lease payments (ASC 842-20-45-5(a)); 192,000,000 is ADDED BACK so the lease is charged once, in net debt (E70) -- leg: `operating_lease_payments` (cash paid for operating leases, the whole payment: principal under E70; its interest component under E34, being inside operating cash flow). Read from: FRAMEWORK-EDITS E70, applied 2026-08-30 to a us-gaap filer ASC 842-20-45-5(a): a lessee classifies payments for operating leases within OPERATING activities, so this filer's `operating_cash_flow` already bears them; the stated cash paid is `us-gaap:OperatingLeasePayments` ('cash paid for amounts included in the measurement of operating lease liabilities'), written as `operating_lease_payments` where tagged. No filer-specific tag states the classification because the standard leaves no choice |
| 4 | bridge | net debt -467,000,000 — borrowings 33,000,000 + 543,000,000 + leases 598,000,000 (E35: always in; finance leases beside operating, E65) + pension deficit 260,000,000 (E35.1) + asset retirement obligations 0 (E68) - cash 1,901,000,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: combined: capex_combined, the one line the issuer prints |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 4.00% from `reference/growth-views/CTSH.md` (2026-08-27) |
| 7 | as-of dates | flows to 2025-12-31; balance sheet 2025-12-31; share count 2025-12-31; price 2026-08-28 — **THEY AGREE** |
| 8 | provenance | 13 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | **DATA MISSING** on this basis |
| `leases` | 598,000,000 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 260,000,000 |
| `current_financial_assets` | **DATA MISSING** on this basis |
| `asset_retirement_obligations` | 0 (stated) |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_combined` | -2.88e+08 | store | VERIFIED (tagged) | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment [2025-01-01..2025-12-31] 10-K 0001058290-26-000008 filed 2026-02-12 |
| `operating_cash_flow` | 2.883e+09 | store | VERIFIED (tagged) | us-gaap:NetCashProvidedByUsedInOperatingActivities [2025-01-01..2025-12-31] 10-K 0001058290-26-000008 filed 2026-02-12 |
| `sbc` | 1.81e+08 | store | VERIFIED (tagged) | us-gaap:ShareBasedCompensation [2025-01-01..2025-12-31] 10-K 0001058290-26-000008 filed 2026-02-12 |
| `finance_costs_period` | 3.7e+07 | store | VERIFIED (tagged) | us-gaap:InterestExpenseNonoperating [2025-01-01..2025-12-31] 10-K 0001058290-26-000008 filed 2026-02-12 |
| `diluted_weighted_average_shares` | 4.89e+08 | store | VERIFIED (tagged) | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding [2025-01-01..2025-12-31] 10-K 0001058290-26-000008 filed 2026-02-12 |
| `shares_point_in_time` | 4.79e+08 | store | VERIFIED (tagged) | us-gaap:CommonStockSharesOutstanding [as of 2025-12-31] 10-Q 0001058290-26-000016 filed 2026-04-29 |
| `financial_liabilities_current` | 3.3e+07 | store | VERIFIED (tagged) | us-gaap:ShortTermBorrowings [as of 2025-12-31] 10-Q 0001058290-26-000016 filed 2026-04-29 |
| `financial_liabilities_noncurrent` | 5.43e+08 | store | VERIFIED (tagged) | us-gaap:LongTermDebtNoncurrent [as of 2025-12-31] 10-Q 0001058290-26-000016 filed 2026-04-29 |
| `lease_liabilities` | 5.98e+08 | store | VERIFIED (tagged) | E65 -- operating and finance lease liabilities: us-gaap:OperatingLeaseLiability [as of 2025-12-31] 10-K 0001058290-26-000008 filed 2026-02-12 = 576,000,000 + E65 -- finance lease liability from two stated parts (E66's precedence): us-gaap:FinanceLeaseLiabilityCurrent [as of 2025-12-31] 10-K 0001058290-26-000008 filed 2026-02-12 = 10,000,000 + us-gaap:FinanceLeaseLiabilityNoncurrent [as of 2025-12-31] 10-K 0001058290-26-000008 filed 2026-02-12 = 12,000,000 = 22,000,000 = 22,000,000, added in full = 598,000,000 |
| `pension_deficit` | 2.6e+08 | store | VERIFIED (same_page) | FRAMEWORK-EDITS E62 (ruled 2026-08-27): the SUM of two defined-benefit plans presented under the SAME note. (1) $55,000,000 -- Note 15, Employee Benefits, 10-K 0001058290-26-000008 filed 2026-02-12: 'Defined Benefit Pension Plans... the net liability recognized on the balance sheet for our pension plans was $55 million'; tagged us-gaap:DefinedBenefitPensionPlanLiabilitiesNoncurrent [as of 2025-12-31]. (2) $205,000,000 -- the same Note 15, 'Other Defined Benefit Plans': 'we offer a gratuity plan in India that is a statutory defined benefit plan... the amount accrued under the gratuity plan was $205 million... which is net of fund assets of $250 million' -- NOT TAGGED under any us-gaap concept in this filer's facts (checked against the full companyfacts JSON); sits inside the balance sheet's 'Other noncurrent liabilities' ($847m) with no reconciling note splitting it out. ONE-OFF NOTED: the India leg was $80 million at 2024-12-31; the note states the $125m increase is driven by 'the Labor Code reforms implemented by the Government of India' in Q4 2025, a $147 million charge 'recognized as a component of other comprehensive income' -- a regulatory reform, not an operating deterioration, and a later-year comparison must read the base effect accordingly, not as debt getting worse. |
| `asset_retirement_obligation` | 0 | store | VERIFIED (same_page) | E68.1: Item 8, CONSOLIDATED STATEMENTS OF FINANCIAL POSITION as of December 31, 2025, 10-K 0001058290-26-000008 filed 2026-02-12 -- liabilities presented: 'Accounts payable', 'Deferred revenue', 'Short-term debt', 'Operating lease liabilities', 'Accrued expenses and other current liabilities', 'Deferred revenue, noncurrent', 'Operating lease liabilities, noncurrent', 'Deferred income tax liabilities, net', 'Long-term debt', 'Other noncurrent liabilities'; no asset retirement or decommissioning caption, and neither term appears anywhere in the filing (full-text search of the primary document, 2026-08-29). An IT-services business owning nothing that requires decommissioning: the absence is evidence. 'Other noncurrent liabilities' $847m is a caption with room (E25), named here. |
| `cash_and_equivalents` | 1.901e+09 | store | VERIFIED (tagged) | us-gaap:CashAndCashEquivalentsAtCarryingValue [as of 2025-12-31] 10-Q 0001058290-26-000016 filed 2026-04-29 |
| `operating_lease_payments` | 1.92e+08 | store | VERIFIED (tagged) | us-gaap:OperatingLeasePayments [2025-01-01..2025-12-31] 10-K 0001058290-26-000008 filed 2026-02-12 |

*Tool commit: `E70 re-strike, 2026-08-30, d171724`.*


</details>

### CTSH -- the framework's own output on the price (NOT a recommendation)

- price 64.04 USD vs fv_base 89.38 USD: **-28.4%** -- price is BELOW fv_base
- price 64.04 USD vs FV_bull 111.48 USD: **-42.6%** -- price is BELOW the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': does not fire** (price < fv_base).
- **C4, 'exit when even the bull case does not beat the index': does not fire.** Expected return from 64.04 to FV_bull 111.48 is **+74.1%**; the index core's expected return is 7.0% a year (E29's anchor). C4 states no horizon: on the reading applied to MSFT and UNA.AS (price above/below FV_bull, expected return positive or negative) it does not fire outright here since price is below FV_bull; read as ONE year against 7.0%, the bull-case gap is ABOVE the index. Which horizon C4 means is the owner's to say.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It does not touch the growth view.** g_base, g_bear and g_bull are the registered ones.
- **It does not score tier.** CTSH's tier 2 is section 4.4's score of 2026-08-29, carried; LII and AOS have none, and MBP is DATA MISSING for them.
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.
