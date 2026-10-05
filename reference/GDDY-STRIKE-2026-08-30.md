# GDDY -- first section 5 strike on the tool path, 2026-08-30

**2026-08-30 07:16 EDT. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The section 5 run record is written to `reference/run-records/GDDY-2026-08-30.json` so that linking it to a watchlist entry (`run_record:`) remains the owner's write.

Growth view: `reference/growth-views/GDDY.md`, pre-registered by the owner 2026-08-30, BEFORE this script ran and before g* was solved (E28's binding order).

Tool: `tools/strike_acn_gddy_nvr_ulta_2026_08_30.py` at `ACN/GDDY/NVR/ULTA first strikes, 2026-08-30, 179f2b4`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# GDDY -- section 5 strike, 2026-08-30 07:16 EDT

Store: `config/manual/GDDY.yaml`. **BASIS: `annual FY2025`, the twelve months ending 2025-12-31** (E19). The basis is FY2025, the twelve months to 2025-12-31, 242 days old; the Q1 and Q2 2026 10-Qs are passed over by the annual path. Price: last SETTLED close **97.70 USD** on 2026-08-28 (tool fetch, 2026-08-30 07:16 EDT).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED.

- record complete: **True**
- **FCF0: 1,406.4 USD m** -- accrual proxy (E34.1): net interest from the income statement: the income statement's net, 114.2 USD m ADDED BACK. Pre-tax, as E34 accepts.
- **share-based compensation (E36): 317.8 USD m deducted = 22.6% of FCF0** (18.4% of the flow before the deduction)
- lease principal (E70): 34.5 USD m added back (2.5% of FCF0); the lease liability stays in net debt
- **net debt: 2,781.7 USD m** -- borrowings 15,100,000 + 3,765,200,000 + leases 82,300,000 (E35: always in; finance leases beside operating, E65) + pension deficit 0 (E35.1) + asset retirement obligations 0 (E68) - cash 1,080,900,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1)
- **asset-retirement leg (E68): 0 -- a CAPTION ZERO under E68.1, not a figure.** The balance sheet presents no asset-retirement or decommissioning caption, neither term appears anywhere in the filing, and the business owns nothing requiring decommissioning; the captions with room are named on the field. Every other leg of the bridge is a tagged figure or a hand-read stated figure (declaration 8).
- divisor: 140,621,000 shares -- weighted-average DILUTED count for annual FY2025, the same window as the flows (E38) (`divisor_basis: weighted_average`)

- **fv_base (Method C, E28): 156.45 USD**
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **170.63 / 156.45 / 144.19 USD**
- bear (g 1.0%): **111.36 USD**
- bull (g 8.0%): **200.58 USD**
- implied growth g* at the settled close 97.70 USD: **-0.51%** (E28; the view in `reference/growth-views/GDDY.md` was fixed 2026-08-30, before this was solved)
- *r 9.5% flat* (E37)

- **tier: NOT SCORED. MBP: DATA MISSING** -- E28's MBP is the bear-case value times the tier cushion, and section 4.4 has not scored GDDY, so there is no tier to apply. **Not struck; not computed on a placeholder.** What it WOULD be against the bear case 111.36 USD, across E29's band, so the range is visible before scoring:
  - tier 1 (x0.80): **89.09 USD** (r 9.0% 96.93 / r 10.0% 82.29); price 97.70 is +9.7% against it
  - tier 2 (x0.70): **77.95 USD** (r 9.0% 84.81 / r 10.0% 72.01); price 97.70 is +25.3% against it
  - tier 3 (x0.60): **66.82 USD** (r 9.0% 72.70 / r 10.0% 61.72); price 97.70 is +46.2% against it

<details><summary>the run record -- every leg of the bridge (declaration 4, item by item) and every input with its provenance (declaration 8), including every proxy and every caption zero</summary>

# section 5 run record — GDDY — 2026-08-30T07:16:17-04:00

**Fair value 156.45 USD** at g 5.00%, r 9.50%.

*r 9.5% flat*

- **FCF0:** 1,406,400,000 USD whole — accrual proxy (E34.1): net interest from the income statement

- **basis (E19):** annual FY2025

- **units:** money stated in whole, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 140,621,000 — weighted-average DILUTED count for annual FY2025, the same window as the flows (E38), as of 2025-12-31; divisor basis `weighted_average` (E75 / E75.1); memo (E38, never the divisor): 134,737,000 as of 2025-12-31 |
| 2 | share-based compensation | deducted, 317,800,000 |
| 3 | interest | interest paid is INSIDE operating cash flow; the filer states interest paid as cash but no interest received, so the net is the INCOME STATEMENT'S -- an ACCRUAL PROXY (E34.1): net interest EXPENSE of 114,200,000 is ADDED BACK, and net debt is then subtracted ONCE. Interest paid alone is never the net. Read from: SEC XBRL companyfacts for CIK 0001609711 (GoDaddy Inc.) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0001609711.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 230-10-45-17(d): under US GAAP interest paid is an OPERATING cash outflow for every filer, so this filer's `operating_cash_flow` already bears its interest. No tag states it because the standard leaves no choice to state |
| 3.1 | lease principal (E70) | the operating cash flow BEARS the operating lease payments (ASC 842-20-45-5(a)); 34,500,000 is ADDED BACK so the lease is charged once, in net debt (E70) -- leg: `operating_lease_payments` (cash paid for operating leases, the whole payment: principal under E70; its interest component under E34, being inside operating cash flow). Read from: SEC XBRL companyfacts for CIK 0001609711 (GoDaddy Inc.) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0001609711.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 842-20-45-5(a): a lessee classifies payments for operating leases within OPERATING activities, so this filer's `operating_cash_flow` already bears them; the stated cash paid is `us-gaap:OperatingLeasePayments`, written as `operating_lease_payments` where tagged. No filer-specific tag states the classification because the standard leaves no choice |
| 4 | bridge | net debt 2,781,700,000 — borrowings 15,100,000 + 3,765,200,000 + leases 82,300,000 (E35: always in; finance leases beside operating, E65) + pension deficit 0 (E35.1) + asset retirement obligations 0 (E68) - cash 1,080,900,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: split: capex_ppe + capex_intangibles, as the accounts print them |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 5.00% from `reference/growth-views/GDDY.md` (2026-08-30) |
| 7 | as-of dates | flows to 2025-12-31; balance sheet 2025-12-31; share count 2025-12-31; price 2026-08-28 — **THEY AGREE** |
| 8 | provenance | 14 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | **DATA MISSING** on this basis |
| `leases` | 82,300,000 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 0 (stated) |
| `current_financial_assets` | **DATA MISSING** on this basis |
| `asset_retirement_obligations` | 0 (stated) |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_ppe` | -2.39e+07 | store | VERIFIED (tagged) | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment [2025-01-01..2025-12-31] 10-K 0001609711-26-000010 filed 2026-02-25 |
| `capex_intangibles` | 0 | store | VERIFIED (tagged) | us-gaap:PaymentsToAcquireIntangibleAssets [2025-01-01..2025-12-31] 10-K 0001609711-26-000010 filed 2026-02-25 |
| `operating_cash_flow` | 1.599e+09 | store | VERIFIED (tagged) | us-gaap:NetCashProvidedByUsedInOperatingActivities [2025-01-01..2025-12-31] 10-K 0001609711-26-000010 filed 2026-02-25 |
| `sbc` | 3.178e+08 | store | VERIFIED (tagged) | us-gaap:ShareBasedCompensation [2025-01-01..2025-12-31] 10-K 0001609711-26-000010 filed 2026-02-25 |
| `net_finance_costs` | 1.142e+08 | store | VERIFIED (same_page) | E69 / E34.1: Item 8, Note 17, Segment Information, reconciliation of Total Segment EBITDA to net income, year ended December 31, 2025, 10-K 0001609711-26-000010 filed 2026-02-25 (in millions): 'Interest expense, net of interest income | (114.2)' (2024: (130.4); 2023: (155.4)); the same line in Item 7, Reconciliation of NEBITDA: 'Interest expense, net of interest income | 114.2'. The Consolidated Statements of Operations print the gross 'Interest expense | (151.0)' (tagged us-gaap:InterestExpenseNonoperating, on this file as `finance_costs_period`) and 'Other income (expense), net | 42.3', inside which the 36.8 of interest income sits untagged. A NET EXPENSE, entered positive; the accrual proxy E34 adds back. Not tagged in FY2025 under any element (the filer tagged InterestIncomeExpenseNonoperatingNet in FY2022-FY2024 and stopped). |
| `diluted_weighted_average_shares` | 1.406e+08 | store | VERIFIED (tagged) | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding [2025-01-01..2025-12-31] 10-K 0001609711-26-000010 filed 2026-02-25 |
| `shares_point_in_time` | 1.347e+08 | store | VERIFIED (tagged) | us-gaap:CommonStockSharesOutstanding [as of 2025-12-31] 10-Q 0001609711-26-000088 filed 2026-07-31 |
| `financial_liabilities_current` | 1.51e+07 | store | VERIFIED (tagged) | us-gaap:LongTermDebtCurrent [as of 2025-12-31] 10-Q 0001609711-26-000088 filed 2026-07-31 |
| `financial_liabilities_noncurrent` | 3.765e+09 | store | VERIFIED (tagged) | us-gaap:LongTermDebtNoncurrent [as of 2025-12-31] 10-Q 0001609711-26-000088 filed 2026-07-31 |
| `lease_liabilities` | 8.23e+07 | store | VERIFIED (same_page) | E65 -- operating and finance lease liabilities: us-gaap:OperatingLeaseLiability [as of 2025-12-31] 10-K 0001609711-26-000010 filed 2026-02-25 = 82,300,000 + finance lease liabilities 0 under E73 (zero_basis caption for the component): Note 2, Leases, states 'Assets and liabilities associated with finance leases are included in property and equipment, net, accrued expenses and other current liabilities and other long-term liabilities', and no amount for them appears anywhere in the filing -- the leases note is operating-only and no finance-lease element is tagged. The captions with room, named: Note 8's 'Other | 85.7' inside accrued expenses and other current liabilities 528.7, and 'Other long-term liabilities | 57.5'. = 82,300,000 |
| `pension_deficit` | 0 | store | VERIFIED (same_page) | E35.1: Item 8, Note 14, Defined Contribution Plan, 10-K 0001609711-26-000010 filed 2026-02-25: 'We maintain a defined contribution 401(k) plan covering eligible U.S. employees ... Expense for our matching contributions was $14.7 million, $15.1 million and $15.8 million during the years ended December 31, 2025, 2024 and 2023, respectively. We maintain defined contribution benefit plans covering eligible foreign employees. Expense related to such plans was not material in any period presented.' The filing's only benefit-plan note; 'defined benefit' appears nowhere in it (full-text search of gddy-20251231.htm, 2026-08-30); the balance sheet presents no retirement or pension caption. |
| `asset_retirement_obligation` | 0 | store | VERIFIED (same_page) | E68.1: Item 8, Consolidated Balance Sheets, December 31, 2025, 10-K 0001609711-26-000010 filed 2026-02-25 -- liabilities presented: 'Accounts payable', 'Accrued expenses and other current liabilities' (528.7), 'Deferred revenue', 'Long-term debt' (current 15.1); 'Deferred revenue, net of current portion', 'Long-term debt, net of current portion', 'Operating lease liabilities, net of current portion', 'Other long-term liabilities' (57.5), 'Deferred tax liabilities'. No asset retirement or decommissioning caption; 'asset retirement', 'decommission', 'dilapidation' and 'restoration obligation' appear nowhere in the filing (full-text search, 2026-08-30). Domain registration, hosting and commerce software delivered from leased data centres and offices: the absence is evidence. Captions with room (E25), named: Note 8 itemises accrued expenses as derivative liabilities 136.0, accrued payroll 135.9, tax-related 84.6, accrued hosting 34.1, accrued legal 32.1, current operating lease liabilities 20.3 and 'Other | 85.7'; 'Other long-term liabilities 57.5' is not itemised. Per Note 2 the filer's FINANCE LEASES sit inside those two captions, unsized (see the header, E65). |
| `cash_and_equivalents` | 1.081e+09 | store | VERIFIED (same_page) | E69: Item 8, Consolidated Balance Sheets, December 31, 2025, 10-K 0001609711-26-000010 filed 2026-02-25 (in millions): 'Cash and cash equivalents | $ | 1,080.9'; Consolidated Statements of Cash Flows 'Cash and cash equivalents, end of period | $ | 1,080.9'. Tagged by the filer as us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents [as of 2025-12-31] = 1,080,900,000 and NOT as CashAndCashEquivalentsAtCarryingValue, the map's alias; 'restricted cash' appears nowhere in the filing, so the caption and the tag are one figure. SHORT-TERM INVESTMENTS ARE NOT INCLUDED (A1): none are presented. |
| `operating_lease_payments` | 3.45e+07 | store | VERIFIED (tagged) | us-gaap:OperatingLeasePayments [2025-01-01..2025-12-31] 10-K 0001609711-26-000010 filed 2026-02-25 |

*Tool commit: `ACN/GDDY/NVR/ULTA first strikes, 2026-08-30, 179f2b4`.*


</details>

### GDDY -- the framework's own output on the price (NOT a recommendation)

- price 97.70 USD vs fv_base 156.45 USD: **-37.6%** -- price is BELOW fv_base
- price 97.70 USD vs FV_bull 200.58 USD: **-51.3%** -- price is BELOW the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': does not fire** (price < fv_base). A trim presupposes a position; none is held.
- **C4 (E42: no horizon -- above FV_bull the full position is sold at the next session): does not fire.** Price is below FV_bull. Expected return from 97.70 to FV_bull 200.58 is **+105.3%** against the index core's 7.0% a year (E29's anchor); read as ONE year, the bull-case gap is ABOVE the index.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are not written there.
- **It does not score tier.** Section 4.4 has not run for GDDY; MBP is printed as DATA MISSING, and the per-tier figures are the range, not a choice.
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.
