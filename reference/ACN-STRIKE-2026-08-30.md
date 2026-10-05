# ACN -- first section 5 strike on the tool path, 2026-08-30

**2026-08-30 07:16 EDT. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The section 5 run record is written to `reference/run-records/ACN-2026-08-30.json` so that linking it to a watchlist entry (`run_record:`) remains the owner's write.

Growth view: `reference/growth-views/ACN.md`, pre-registered by the owner 2026-08-30, BEFORE this script ran and before g* was solved (E28's binding order).

Tool: `tools/strike_acn_gddy_nvr_ulta_2026_08_30.py` at `ACN/GDDY/NVR/ULTA first strikes, 2026-08-30, 179f2b4`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# ACN -- section 5 strike, 2026-08-30 07:16 EDT

Store: `config/manual/ACN.yaml`. **BASIS: `annual FY2025`, the twelve months ending 2025-08-31** (E19). **THE ACCOUNTS ARE 364 DAYS OLD.** The basis is FY2025, the twelve months to 2025-08-31, and FY2026 CLOSES TOMORROW, 2026-08-31; its 10-K is due about 2026-10-09 and will supersede this basis. The three FY2026 10-Qs (to 2025-11-30, 2026-02-28 and 2026-05-31) are passed over by the annual path. Inside `MAX_REPORT_AGE_DAYS` 550; B24 (the basis-to-price distance) is open, and this is the widest gap on the books. Price: last SETTLED close **189.61 USD** on 2026-08-28 (tool fetch, 2026-08-30 07:16 EDT).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED.

- record complete: **True**
- **FCF0: 9,417.4 USD m** -- accrual proxy (E34.1): net interest from the income statement: the income statement's net, -107.8 USD m REMOVED (a net interest INCOME). Pre-tax, as E34 accepts.
- **share-based compensation (E36): 2,093.9 USD m deducted = 22.2% of FCF0** (18.2% of the flow before the deduction)
- lease principal (E70): 744.7 USD m added back (7.9% of FCF0); the lease liability stays in net debt
- **net debt: -1,437.4 USD m (NET CASH)** -- borrowings 114,484,000 + 5,034,169,000 + leases 3,034,213,000 (E35: always in; finance leases beside operating, E65) + pension deficit 1,858,499,000 (E35.1) + asset retirement obligations 0 (E68) - cash 11,478,729,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1)
- **asset-retirement leg (E68): 0 -- a CAPTION ZERO under E68.1, not a figure.** The balance sheet presents no asset-retirement or decommissioning caption, neither term appears anywhere in the filing, and the business owns nothing requiring decommissioning; the captions with room are named on the field. Every other leg of the bridge is a tagged figure or a hand-read stated figure (declaration 8).
- divisor: 632,435,108 shares -- weighted-average DILUTED count for annual FY2025, the same window as the flows (E38) (`divisor_basis: weighted_average`)

- **fv_base (Method C, E28): 255.10 USD**
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **275.27 / 255.10 / 237.65 USD**
- bear (g 0.0%): **183.75 USD**
- bull (g 7.5%): **318.35 USD**
- implied growth g* at the settled close 189.61 USD: **0.43%** (E28; the view in `reference/growth-views/ACN.md` was fixed 2026-08-30, before this was solved)
- *r 9.5% flat* (E37)

- **tier: NOT SCORED. MBP: DATA MISSING** -- E28's MBP is the bear-case value times the tier cushion, and section 4.4 has not scored ACN, so there is no tier to apply. **Not struck; not computed on a placeholder.** What it WOULD be against the bear case 183.75 USD, across E29's band, so the range is visible before scoring:
  - tier 1 (x0.80): **147.00 USD** (r 9.0% 157.62 / r 10.0% 137.78); price 189.61 is +29.0% against it
  - tier 2 (x0.70): **128.63 USD** (r 9.0% 137.92 / r 10.0% 120.56); price 189.61 is +47.4% against it
  - tier 3 (x0.60): **110.25 USD** (r 9.0% 118.21 / r 10.0% 103.34); price 189.61 is +72.0% against it

<details><summary>the run record -- every leg of the bridge (declaration 4, item by item) and every input with its provenance (declaration 8), including every proxy and every caption zero</summary>

# section 5 run record — ACN — 2026-08-30T07:16:17-04:00

**Fair value 255.10 USD** at g 4.50%, r 9.50%.

*r 9.5% flat*

- **FCF0:** 9,417,407,000 USD whole — accrual proxy (E34.1): net interest from the income statement

- **basis (E19):** annual FY2025

- **units:** money stated in whole, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 632,435,108 — weighted-average DILUTED count for annual FY2025, the same window as the flows (E38), as of 2025-08-31; divisor basis `weighted_average` (E75 / E75.1); memo (E38, never the divisor): — |
| 2 | share-based compensation | deducted, 2,093,878,000 |
| 3 | interest | interest paid is INSIDE operating cash flow; the filer states interest paid as cash but no interest received, so the net is the INCOME STATEMENT'S -- an ACCRUAL PROXY (E34.1): net interest INCOME of 107,769,000 is REMOVED, and net debt is then subtracted ONCE. Interest paid alone is never the net. Read from: SEC XBRL companyfacts for CIK 0001467373 (Accenture plc) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0001467373.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 230-10-45-17(d): under US GAAP interest paid is an OPERATING cash outflow for every filer, so this filer's `operating_cash_flow` already bears its interest. No tag states it because the standard leaves no choice to state |
| 3.1 | lease principal (E70) | the operating cash flow BEARS the operating lease payments (ASC 842-20-45-5(a)); 744,694,000 is ADDED BACK so the lease is charged once, in net debt (E70) -- leg: `operating_lease_payments` (cash paid for operating leases, the whole payment: principal under E70; its interest component under E34, being inside operating cash flow). Read from: SEC XBRL companyfacts for CIK 0001467373 (Accenture plc) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0001467373.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 842-20-45-5(a): a lessee classifies payments for operating leases within OPERATING activities, so this filer's `operating_cash_flow` already bears them; the stated cash paid is `us-gaap:OperatingLeasePayments`, written as `operating_lease_payments` where tagged. No filer-specific tag states the classification because the standard leaves no choice |
| 4 | bridge | net debt -1,437,364,000 — borrowings 114,484,000 + 5,034,169,000 + leases 3,034,213,000 (E35: always in; finance leases beside operating, E65) + pension deficit 1,858,499,000 (E35.1) + asset retirement obligations 0 (E68) - cash 11,478,729,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: combined: capex_combined, the one line the issuer prints |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 4.50% from `reference/growth-views/ACN.md` (2026-08-30) |
| 7 | as-of dates | flows to 2025-08-31; balance sheet 2025-08-31; share count 2025-08-31; price 2026-08-28 — **THEY AGREE** |
| 8 | provenance | 12 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | **DATA MISSING** on this basis |
| `leases` | 3,034,213,000 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 1,858,499,000 |
| `current_financial_assets` | **DATA MISSING** on this basis |
| `asset_retirement_obligations` | 0 (stated) |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_combined` | -6e+08 | store | VERIFIED (tagged) | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment [2024-09-01..2025-08-31] 10-K 0001467373-25-000217 filed 2025-10-10 |
| `operating_cash_flow` | 1.147e+10 | store | VERIFIED (tagged) | us-gaap:NetCashProvidedByUsedInOperatingActivities [2024-09-01..2025-08-31] 10-K 0001467373-25-000217 filed 2025-10-10 |
| `sbc` | 2.094e+09 | store | VERIFIED (tagged) | us-gaap:ShareBasedCompensation [2024-09-01..2025-08-31] 10-K 0001467373-25-000217 filed 2025-10-10 |
| `net_finance_costs` | -1.078e+08 | store | VERIFIED (same_page/tagged) | E18: finance_costs_period - finance_income_period, both on annual FY2025 |
| `diluted_weighted_average_shares` | 6.324e+08 | store | VERIFIED (tagged) | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding [2024-09-01..2025-08-31] 10-K 0001467373-25-000217 filed 2025-10-10 |
| `financial_liabilities_current` | 1.145e+08 | store | VERIFIED (tagged) | us-gaap:DebtCurrent [as of 2025-08-31] 10-Q 0001467373-26-000032 filed 2026-06-18 -- E66: the taxonomy's SUBTOTAL of current borrowings, read whole; tagged beside it as memo and never added: `CommercialPaper` 99,963,000 |
| `financial_liabilities_noncurrent` | 5.034e+09 | store | VERIFIED (same_page) | E67 / E69: Item 8, Consolidated Balance Sheets, August 31, 2025, 10-K 0001467373-25-000217 filed 2025-10-10, NON-CURRENT LIABILITIES: 'Long-term debt | 5,034,169' (in thousands) -- the caption the filer tags as us-gaap:LongTermDebtAndCapitalLeaseObligations [as of 2025-08-31] = 5,034,169,000, which the tool REFUSED under E67 because no FinanceLeaseLiability element is tagged at this year end. Note 10, Borrowings and Indebtedness, states the composition: 'Senior notes – 3.90% due 2027 | 1,100,000; Senior notes – 4.05% due 2029 | 1,200,000; Senior notes – 4.25% due 2031 | 1,200,000; Senior notes – 4.50% due 2034 | 1,500,000; Total principal amount (3) | 5,000,000; Less: unamortized debt discount and issuance costs | (32,774); Total carrying amount | 4,967,226; Other (2) | 66,943; Total long-term debt | 5,034,169', with footnote '(2) Amounts primarily include finance lease liabilities'; the leases note: 'As of August 31, 2025 and 2024, we had no material finance leases.' THE FINANCE LEASE INSIDE THE CAPTION IS STATED ONLY APPROXIMATELY -- 'primarily' the 'Other' line of 66,943, and 'no material finance leases' -- so under E72 (2026-08-30) the combined caption is the leg, read WHOLE, with the issuer's wording quoted here: senior notes carrying 4,967,226 and 'Other (2) 66,943, primarily finance lease liabilities' both named. No finance-lease element is tagged, so E65 adds nothing to `lease_liabilities` (the operating total alone): every dollar of the caption is in exactly one leg, nothing counted twice and nothing dropped. MATERIALITY, STATED (E72): the 66,943 is 1.3% of the caption and 0.11 USD a share on 632m diluted shares -- the wording does not matter to the outcome. The current leg is read the same way: 'Current portion of long-term debt and bank borrowings | 114,484' = 'Commercial paper (1) 99,963' + 'Other (2) 14,521', tagged us-gaap:DebtCurrent and read whole under E66. |
| `lease_liabilities` | 3.034e+09 | store | VERIFIED (tagged) | us-gaap:OperatingLeaseLiability [as of 2025-08-31] 10-K 0001467373-25-000217 filed 2025-10-10 |
| `pension_deficit` | 1.858e+09 | store | VERIFIED (tagged) | us-gaap:PensionAndOtherPostretirementDefinedBenefitPlansLiabilitiesNoncurrent [as of 2025-08-31] 10-Q 0001467373-26-000032 filed 2026-06-18 |
| `asset_retirement_obligation` | 0 | store | VERIFIED (same_page) | E68.1: Item 8, Consolidated Balance Sheets as of August 31, 2025, 10-K 0001467373-25-000217 filed 2025-10-10 -- CURRENT LIABILITIES presented: 'Current portion of long-term debt and bank borrowings', 'Accounts payable', 'Deferred revenues', 'Accrued payroll and related benefits', 'Income taxes payable', 'Lease liabilities', 'Other accrued liabilities' (1,954,418); NON-CURRENT: 'Long-term debt', 'Deferred revenues', 'Retirement obligation', 'Deferred tax liabilities', 'Income taxes payable', 'Lease liabilities', 'Other non-current liabilities' (1,197,742). No asset retirement or decommissioning caption; 'asset retirement', 'decommission' and 'dilapidation' appear nowhere in the filing and 'restoration' only in the income-tax note (full-text search of the primary document acn-20250831.htm, 2026-08-30). Professional services (SIC 7389) delivered from leased offices, owning nothing that requires decommissioning: the absence is evidence. 'Other accrued liabilities' and 'Other non-current liabilities' are captions with room (E25) and are named here; the filing discloses no remediation or restoration obligation inside them (E68.2 has nothing to name). |
| `cash_and_equivalents` | 1.148e+10 | store | VERIFIED (tagged) | us-gaap:CashAndCashEquivalentsAtCarryingValue [as of 2025-08-31] 10-Q 0001467373-26-000032 filed 2026-06-18 |
| `operating_lease_payments` | 7.447e+08 | store | VERIFIED (tagged) | us-gaap:OperatingLeasePayments [2024-09-01..2025-08-31] 10-K 0001467373-25-000217 filed 2025-10-10 |

*Tool commit: `ACN/GDDY/NVR/ULTA first strikes, 2026-08-30, 179f2b4`.*


</details>

### ACN -- the framework's own output on the price (NOT a recommendation)

- price 189.61 USD vs fv_base 255.10 USD: **-25.7%** -- price is BELOW fv_base
- price 189.61 USD vs FV_bull 318.35 USD: **-40.4%** -- price is BELOW the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': does not fire** (price < fv_base). A trim presupposes a position; none is held.
- **C4 (E42: no horizon -- above FV_bull the full position is sold at the next session): does not fire.** Price is below FV_bull. Expected return from 189.61 to FV_bull 318.35 is **+67.9%** against the index core's 7.0% a year (E29's anchor); read as ONE year, the bull-case gap is ABOVE the index.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are not written there.
- **It does not score tier.** Section 4.4 has not run for ACN; MBP is printed as DATA MISSING, and the per-tier figures are the range, not a choice.
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.
