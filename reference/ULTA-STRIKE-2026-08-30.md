# ULTA -- first section 5 strike on the tool path, 2026-08-30

**2026-08-30 07:16 EDT. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The section 5 run record is written to `reference/run-records/ULTA-2026-08-30.json` so that linking it to a watchlist entry (`run_record:`) remains the owner's write.

Growth view: `reference/growth-views/ULTA.md`, pre-registered by the owner 2026-08-30, BEFORE this script ran and before g* was solved (E28's binding order).

Tool: `tools/strike_acn_gddy_nvr_ulta_2026_08_30.py` at `ACN/GDDY/NVR/ULTA first strikes, 2026-08-30, 179f2b4`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# ULTA -- section 5 strike, 2026-08-30 07:16 EDT

Store: `config/manual/ULTA.yaml`. **BASIS: `annual FY2026`, the twelve months ending 2026-01-31** (E19). The basis is the twelve months to 2026-01-31 -- the filer's FISCAL 2025, which the store keys FY2026 on the calendar year of its end -- 211 days old; the Q1 and Q2 fiscal-2026 10-Qs (to 2026-05-02 and 2026-08-01) are passed over by the annual path. Price: last SETTLED close **517.50 USD** on 2026-08-28 (tool fetch, 2026-08-30 07:16 EDT).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED.

- record complete: **True**
- **FCF0: 1,471.1 USD m** -- accrual proxy (E34.1): net interest from the income statement: the income statement's net, 1.8 USD m ADDED BACK. Pre-tax, as E34 accepts.
- **share-based compensation (E36): 37.4 USD m deducted = 2.5% of FCF0** (2.5% of the flow before the deduction)
- lease principal (E70): 438.8 USD m added back (29.8% of FCF0); the lease liability stays in net debt
- **net debt: 1,757.8 USD m** -- borrowings 62,287,000 + 0 + leases 2,119,774,000 (E35: always in; finance leases beside operating, E65) + pension deficit 0 (E35.1) + asset retirement obligations 0 (E68) - cash 424,243,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1)
- **asset-retirement leg (E68): 0 -- a CAPTION ZERO under E68.1, not a figure.** The balance sheet presents no asset-retirement or decommissioning caption, neither term appears anywhere in the filing, and the business owns nothing requiring decommissioning; the captions with room are named on the field. Every other leg of the bridge is a tagged figure or a hand-read stated figure (declaration 8).
- divisor: 44,991,000 shares -- weighted-average DILUTED count for annual FY2026, the same window as the flows (E38) (`divisor_basis: weighted_average`)

- **fv_base (Method C, E28): 476.45 USD**
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **516.84 / 476.45 / 441.46 USD**
- bear (g 0.0%): **359.43 USD**
- bull (g 6.5%): **605.14 USD**
- implied growth g* at the settled close 517.50 USD: **4.53%** (E28; the view in `reference/growth-views/ULTA.md` was fixed 2026-08-30, before this was solved)
- *r 9.5% flat* (E37)

- **tier: NOT SCORED. MBP: DATA MISSING** -- E28's MBP is the bear-case value times the tier cushion, and section 4.4 has not scored ULTA, so there is no tier to apply. **Not struck; not computed on a placeholder.** What it WOULD be against the bear case 359.43 USD, across E29's band, so the range is visible before scoring:
  - tier 1 (x0.80): **287.55 USD** (r 9.0% 310.86 / r 10.0% 267.31); price 517.50 is +80.0% against it
  - tier 2 (x0.70): **251.60 USD** (r 9.0% 272.01 / r 10.0% 233.89); price 517.50 is +105.7% against it
  - tier 3 (x0.60): **215.66 USD** (r 9.0% 233.15 / r 10.0% 200.48); price 517.50 is +140.0% against it

<details><summary>the run record -- every leg of the bridge (declaration 4, item by item) and every input with its provenance (declaration 8), including every proxy and every caption zero</summary>

# section 5 run record — ULTA — 2026-08-30T07:16:17-04:00

**Fair value 476.45 USD** at g 3.50%, r 9.50%.

*r 9.5% flat*

- **FCF0:** 1,471,119,000 USD whole — accrual proxy (E34.1): net interest from the income statement

- **basis (E19):** annual FY2026

- **units:** money stated in whole, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 44,991,000 — weighted-average DILUTED count for annual FY2026, the same window as the flows (E38), as of 2026-01-31; divisor basis `weighted_average` (E75 / E75.1); memo (E38, never the divisor): 44,166,000 as of 2026-01-31 |
| 2 | share-based compensation | deducted, 37,426,000 |
| 3 | interest | interest paid is INSIDE operating cash flow; the filer states interest paid as cash but no interest received, so the net is the INCOME STATEMENT'S -- an ACCRUAL PROXY (E34.1): net interest EXPENSE of 1,787,000 is ADDED BACK, and net debt is then subtracted ONCE. Interest paid alone is never the net. Read from: SEC XBRL companyfacts for CIK 0001403568 (Ulta Beauty, Inc.) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0001403568.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 230-10-45-17(d): under US GAAP interest paid is an OPERATING cash outflow for every filer, so this filer's `operating_cash_flow` already bears its interest. No tag states it because the standard leaves no choice to state |
| 3.1 | lease principal (E70) | the operating cash flow BEARS the operating lease payments (ASC 842-20-45-5(a)); 438,807,000 is ADDED BACK so the lease is charged once, in net debt (E70) -- leg: `operating_lease_payments` (cash paid for operating leases, the whole payment: principal under E70; its interest component under E34, being inside operating cash flow). Read from: SEC XBRL companyfacts for CIK 0001403568 (Ulta Beauty, Inc.) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0001403568.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 842-20-45-5(a): a lessee classifies payments for operating leases within OPERATING activities, so this filer's `operating_cash_flow` already bears them; the stated cash paid is `us-gaap:OperatingLeasePayments`, written as `operating_lease_payments` where tagged. No filer-specific tag states the classification because the standard leaves no choice |
| 4 | bridge | net debt 1,757,818,000 — borrowings 62,287,000 + 0 + leases 2,119,774,000 (E35: always in; finance leases beside operating, E65) + pension deficit 0 (E35.1) + asset retirement obligations 0 (E68) - cash 424,243,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: combined: capex_combined, the one line the issuer prints |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 3.50% from `reference/growth-views/ULTA.md` (2026-08-30) |
| 7 | as-of dates | flows to 2026-01-31; balance sheet 2026-01-31; share count 2026-01-31; price 2026-08-28 — **THEY AGREE** |
| 8 | provenance | 13 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | **DATA MISSING** on this basis |
| `leases` | 2,119,774,000 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 0 (stated) |
| `current_financial_assets` | **DATA MISSING** on this basis |
| `asset_retirement_obligations` | 0 (stated) |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_combined` | -4.348e+08 | store | VERIFIED (tagged) | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment [2025-02-02..2026-01-31] 10-K 0001104659-26-035243 filed 2026-03-26 |
| `operating_cash_flow` | 1.503e+09 | store | VERIFIED (tagged) | us-gaap:NetCashProvidedByUsedInOperatingActivities [2025-02-02..2026-01-31] 10-K 0001104659-26-035243 filed 2026-03-26 |
| `sbc` | 3.743e+07 | store | VERIFIED (tagged) | us-gaap:ShareBasedCompensation [2025-02-02..2026-01-31] 10-K 0001104659-26-035243 filed 2026-03-26 |
| `net_finance_costs` | 1.787e+06 | store | VERIFIED (tagged) | us-gaap:InterestIncomeExpenseNonoperatingNet [2025-02-02..2026-01-31] 10-K 0001104659-26-035243 filed 2026-03-26 |
| `diluted_weighted_average_shares` | 4.499e+07 | store | VERIFIED (tagged) | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding [2025-02-02..2026-01-31] 10-K 0001104659-26-035243 filed 2026-03-26 |
| `shares_point_in_time` | 4.417e+07 | store | VERIFIED (tagged) | us-gaap:CommonStockSharesOutstanding [as of 2026-01-31] 10-Q 0001104659-26-102442 filed 2026-08-27 |
| `financial_liabilities_current` | 6.229e+07 | store | VERIFIED (tagged) | us-gaap:ShortTermBorrowings [as of 2026-01-31] 10-Q 0001104659-26-102442 filed 2026-08-27 |
| `financial_liabilities_noncurrent` | 0 | store | VERIFIED (same_page) | Item 7, Interest expense (income), net, 10-K 0001104659-26-035243 filed 2026-03-26: 'The increase in interest expense was primarily due to increased borrowings on our credit facilities in fiscal 2025. As of January 31, 2026, we had $62.3 million outstanding under our credit facilities.' Consolidated Balance Sheets, January 31, 2026 (in thousands), liabilities presented: 'Accounts payable', 'Accrued liabilities', 'Deferred revenue', 'Current operating lease liabilities', 'Accrued income taxes', 'Short-term debt | 62,287' (the whole of the borrowings, carried on this file as `financial_liabilities_current`, tagged ShortTermBorrowings / LineOfCredit), then 'Non-current operating lease liabilities', 'Deferred income taxes', 'Other long-term liabilities | 59,632' -- no long-term debt caption. Other long-term liabilities hold the non-qualified deferred compensation liability of 42,470 (Note 14), not borrowings. The cash-flow statement's 'Borrowings from short-term debt 2,214,888' and 'Payments on short-term debt (2,182,316)' are the revolver's turnover. |
| `lease_liabilities` | 2.12e+09 | store | VERIFIED (tagged) | us-gaap:OperatingLeaseLiability [as of 2026-01-31] 10-K 0001104659-26-035243 filed 2026-03-26 |
| `pension_deficit` | 0 | store | VERIFIED (same_page) | E35.1: Item 8, Note 17, Employee benefit plans, 10-K 0001104659-26-035243 filed 2026-03-26: 'The Company provides a 401(k) retirement plan covering all U.S. associates who qualify as to age and length of service. The plan is funded through employee contributions and a Company match of 100% of the first 3% of eligible compensation and an additional 50% match for the next 2% of eligible compensation.' The filing's only retirement plan; the non-qualified deferred compensation plan (Note 14: liabilities of 42,470 in other long-term liabilities, plan assets of 53,391) is a funded deferral, not a defined-benefit obligation. 'Defined benefit' appears nowhere in the filing (full-text search of ulta-20260131x10k.htm, 2026-08-30); the balance sheet presents no pension caption. |
| `asset_retirement_obligation` | 0 | store | VERIFIED (same_page) | E68.1: Item 8, Consolidated Balance Sheets, January 31, 2026, 10-K 0001104659-26-035243 filed 2026-03-26 -- liabilities presented: 'Accounts payable', 'Accrued liabilities' (551,380), 'Deferred revenue', 'Current operating lease liabilities', 'Accrued income taxes', 'Short-term debt'; 'Non-current operating lease liabilities', 'Deferred income taxes', 'Other long-term liabilities' (59,632, of which deferred compensation 42,470). No asset retirement or decommissioning caption; 'asset retirement', 'decommission', 'dilapidation' and 'restoration obligation' appear nowhere in the filing (full-text search, 2026-08-30). A specialty beauty retailer operating from leased stores and distribution centres, owning nothing that requires decommissioning: the absence is evidence. 'Accrued liabilities' and 'Other long-term liabilities' are captions with room (E25) and are named here. |
| `cash_and_equivalents` | 4.242e+08 | store | VERIFIED (tagged) | us-gaap:CashAndCashEquivalentsAtCarryingValue [as of 2026-01-31] 10-Q 0001104659-26-102442 filed 2026-08-27 |
| `operating_lease_payments` | 4.388e+08 | store | VERIFIED (tagged) | us-gaap:OperatingLeasePayments [2025-02-02..2026-01-31] 10-K 0001104659-26-035243 filed 2026-03-26 |

*Tool commit: `ACN/GDDY/NVR/ULTA first strikes, 2026-08-30, 179f2b4`.*


</details>

### ULTA -- the framework's own output on the price (NOT a recommendation)

- price 517.50 USD vs fv_base 476.45 USD: **+8.6%** -- price is ABOVE fv_base
- price 517.50 USD vs FV_bull 605.14 USD: **-14.5%** -- price is BELOW the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': FIRES** (price >= fv_base). A trim presupposes a position; none is held.
- **C4 (E42: no horizon -- above FV_bull the full position is sold at the next session): does not fire.** Price is below FV_bull. Expected return from 517.50 to FV_bull 605.14 is **+16.9%** against the index core's 7.0% a year (E29's anchor); read as ONE year, the bull-case gap is ABOVE the index.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are not written there.
- **It does not score tier.** Section 4.4 has not run for ULTA; MBP is printed as DATA MISSING, and the per-tier figures are the range, not a choice.
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.
