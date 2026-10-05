# NVR -- first section 5 strike on the tool path, 2026-08-30

**2026-08-30 07:16 EDT. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The section 5 run record is written to `reference/run-records/NVR-2026-08-30.json` so that linking it to a watchlist entry (`run_record:`) remains the owner's write.

Growth view: `reference/growth-views/NVR.md`, pre-registered by the owner 2026-08-30, BEFORE this script ran and before g* was solved (E28's binding order).

Tool: `tools/strike_acn_gddy_nvr_ulta_2026_08_30.py` at `ACN/GDDY/NVR/ULTA first strikes, 2026-08-30, 179f2b4`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# NVR -- section 5 strike, 2026-08-30 07:16 EDT

Store: `config/manual/NVR.yaml`. **BASIS: `annual FY2025`, the twelve months ending 2025-12-31** (E19). The basis is FY2025, the twelve months to 2025-12-31, 242 days old; the Q1 and Q2 2026 10-Qs are passed over by the annual path. Price: last SETTLED close **6396.27 USD** on 2026-08-28 (tool fetch, 2026-08-30 07:16 EDT).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED.

- record complete: **True**
- **FCF0: 987.3 USD m** -- accrual proxy (E34.1): net interest from the income statement: the income statement's net, -73.2 USD m REMOVED (a net interest INCOME). Pre-tax, as E34 accepts.
- **share-based compensation (E36): 69.2 USD m deducted = 7.0% of FCF0** (6.6% of the flow before the deduction)
- lease principal (E70): 32.9 USD m added back (3.3% of FCF0); the lease liability stays in net debt
- **net debt: -821.1 USD m (NET CASH)** -- borrowings 0 + 909,160,000 + leases 186,207,000 (E35: always in; finance leases beside operating, E65) + pension deficit 0 (E35.1) + asset retirement obligations 0 (E68) - cash 1,916,486,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1)
- **asset-retirement leg (E68): 0 -- a CAPTION ZERO under E68.1, not a figure.** The balance sheet presents no asset-retirement or decommissioning caption, neither term appears anywhere in the filing, and the business owns nothing requiring decommissioning; the captions with room are named on the field. Every other leg of the bridge is a tagged figure or a hand-read stated figure (declaration 8).
- divisor: 3,069,103 shares -- weighted-average DILUTED count for annual FY2025, the same window as the flows (E38) (`divisor_basis: weighted_average`)

- **fv_base (Method C, E28): 4,978.10 USD**
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **5,340.45 / 4,978.10 / 4,664.06 USD**
- bear (g -3.0%): **3,422.77 USD**
- bull (g 6.5%): **6,605.52 USD**
- implied growth g* at the settled close 6396.27 USD: **6.05%** (E28; the view in `reference/growth-views/NVR.md` was fixed 2026-08-30, before this was solved)
- *r 9.5% flat* (E37)

- **tier: NOT SCORED. MBP: DATA MISSING** -- E28's MBP is the bear-case value times the tier cushion, and section 4.4 has not scored NVR, so there is no tier to apply. **Not struck; not computed on a placeholder.** What it WOULD be against the bear case 3,422.77 USD, across E29's band, so the range is visible before scoring:
  - tier 1 (x0.80): **2,738.21 USD** (r 9.0% 2,910.49 / r 10.0% 2,588.34); price 6396.27 is +133.6% against it
  - tier 2 (x0.70): **2,395.94 USD** (r 9.0% 2,546.67 / r 10.0% 2,264.80); price 6396.27 is +167.0% against it
  - tier 3 (x0.60): **2,053.66 USD** (r 9.0% 2,182.86 / r 10.0% 1,941.25); price 6396.27 is +211.5% against it

<details><summary>the run record -- every leg of the bridge (declaration 4, item by item) and every input with its provenance (declaration 8), including every proxy and every caption zero</summary>

# section 5 run record — NVR — 2026-08-30T07:16:17-04:00

**Fair value 4,978.10 USD** at g 2.50%, r 9.50%.

*r 9.5% flat*

- **FCF0:** 987,320,000 USD whole — accrual proxy (E34.1): net interest from the income statement

- **basis (E19):** annual FY2025

- **units:** money stated in whole, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 3,069,103 — weighted-average DILUTED count for annual FY2025, the same window as the flows (E38), as of 2025-12-31; divisor basis `weighted_average` (E75 / E75.1); memo (E38, never the divisor): 2,799,387 as of 2025-12-31 |
| 2 | share-based compensation | deducted, 69,213,000 |
| 3 | interest | interest paid is INSIDE operating cash flow; the filer states interest paid as cash but no interest received, so the net is the INCOME STATEMENT'S -- an ACCRUAL PROXY (E34.1): net interest INCOME of 73,209,000 is REMOVED, and net debt is then subtracted ONCE. Interest paid alone is never the net. Read from: SEC XBRL companyfacts for CIK 0000906163 (NVR, Inc.) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0000906163.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 230-10-45-17(d): under US GAAP interest paid is an OPERATING cash outflow for every filer, so this filer's `operating_cash_flow` already bears its interest. No tag states it because the standard leaves no choice to state |
| 3.1 | lease principal (E70) | the operating cash flow BEARS the operating lease payments (ASC 842-20-45-5(a)); 32,930,000 is ADDED BACK so the lease is charged once, in net debt (E70) -- leg: `operating_lease_payments` (cash paid for operating leases, the whole payment: principal under E70; its interest component under E34, being inside operating cash flow). Read from: SEC XBRL companyfacts for CIK 0000906163 (NVR, Inc.) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0000906163.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 842-20-45-5(a): a lessee classifies payments for operating leases within OPERATING activities, so this filer's `operating_cash_flow` already bears them; the stated cash paid is `us-gaap:OperatingLeasePayments`, written as `operating_lease_payments` where tagged. No filer-specific tag states the classification because the standard leaves no choice |
| 4 | bridge | net debt -821,119,000 — borrowings 0 + 909,160,000 + leases 186,207,000 (E35: always in; finance leases beside operating, E65) + pension deficit 0 (E35.1) + asset retirement obligations 0 (E68) - cash 1,916,486,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: combined: capex_combined, the one line the issuer prints |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 2.50% from `reference/growth-views/NVR.md` (2026-08-30) |
| 7 | as-of dates | flows to 2025-12-31; balance sheet 2025-12-31; share count 2025-12-31; price 2026-08-28 — **THEY AGREE** |
| 8 | provenance | 13 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | **DATA MISSING** on this basis |
| `leases` | 186,207,000 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 0 (stated) |
| `current_financial_assets` | **DATA MISSING** on this basis |
| `asset_retirement_obligations` | 0 (stated) |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_combined` | -2.451e+07 | store | VERIFIED (tagged) | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment [2025-01-01..2025-12-31] 10-K 0000906163-26-000018 filed 2026-02-11 |
| `operating_cash_flow` | 1.121e+09 | store | VERIFIED (tagged) | us-gaap:NetCashProvidedByUsedInOperatingActivities [2025-01-01..2025-12-31] 10-K 0000906163-26-000018 filed 2026-02-11 |
| `sbc` | 6.921e+07 | store | VERIFIED (tagged) | us-gaap:ShareBasedCompensation [2025-01-01..2025-12-31] 10-K 0000906163-26-000018 filed 2026-02-11 |
| `net_finance_costs` | -7.321e+07 | store | VERIFIED (same_page) | E18: finance_costs_period - finance_income_period, both on annual FY2025 |
| `diluted_weighted_average_shares` | 3.069e+06 | store | VERIFIED (tagged) | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding [2025-01-01..2025-12-31] 10-K 0000906163-26-000018 filed 2026-02-11 |
| `shares_point_in_time` | 2.799e+06 | store | VERIFIED (tagged) | us-gaap:CommonStockSharesOutstanding [as of 2025-12-31] 10-K 0000906163-26-000018 filed 2026-02-11 |
| `financial_liabilities_current` | 0 | store | VERIFIED (same_page) | Item 7, Liquidity and Capital Resources, 10-K 0000906163-26-000018 filed 2026-02-11: 'There were no borrowings outstanding under the Credit Agreement as of December 31, 2025' ($300,000 revolving commitments; letters of credit of approximately $9,700 outstanding); Note 7: 'As of both December 31, 2025 and 2024, there was no debt outstanding under the Repurchase Agreement' (NVRM's $150,000 non-recourse mortgage repurchase facility); the Senior Notes mature in May 2030. Consolidated Balance Sheets, December 31, 2025, liabilities presented: Homebuilding 'Accounts payable', 'Accrued expenses and other liabilities', 'Customer deposits', 'Operating lease liabilities', 'Senior notes'; Mortgage Banking 'Accounts payable and other liabilities', 'Operating lease liabilities' -- no current-debt caption. E55 is not reached while the repurchase facility is undrawn. |
| `financial_liabilities_noncurrent` | 9.092e+08 | store | VERIFIED (same_page) | E69: Item 8, Consolidated Balance Sheets, December 31, 2025, 10-K 0000906163-26-000018 filed 2026-02-11 (in thousands), Homebuilding liabilities: 'Senior notes | 909,160' (2024: 911,118); Item 7, Capital Resources: 'As of December 31, 2025, we had a total of $900,000 in outstanding Senior Notes which mature in May 2030.' BORROWINGS ALONE (E14): the operating lease liabilities are separate captions and the finance leases sit in 'Accrued expenses and other liabilities'. No us-gaap element carries this figure at 2025-12-31 -- the filer tags it under an extension element the map cannot read. |
| `lease_liabilities` | 1.862e+08 | store | VERIFIED (tagged) | E65 -- operating and finance lease liabilities: us-gaap:OperatingLeaseLiability [as of 2025-12-31] 10-K 0000906163-26-000018 filed 2026-02-11 = 143,733,000 + us-gaap:FinanceLeaseLiability [as of 2025-12-31] 10-Q 0000906163-26-000093 filed 2026-08-05 = 42,474,000, added in full = 186,207,000 |
| `pension_deficit` | 0 | store | VERIFIED (same_page) | E35.1: Item 8, Note 10, Equity-Based Compensation, Profit Sharing and Deferred Compensation Plans, 10-K 0000906163-26-000018 filed 2026-02-11: 'We have a trustee-administered, profit sharing retirement plan (the Profit Sharing Plan) and an Employee Stock Ownership Plan (ESOP) covering substantially all employees. The Profit Sharing Plan and the ESOP provide for annual discretionary contributions in amounts as determined by our Board of Directors. The combined plan contribution for the years ended December 31, 2025, 2024 and 2023 equaled approximately $29,400, $30,200 and $26,200' -- discretionary defined-contribution plans; the nonqualified deferred compensation plan is funded by a trust holding 106,697 NVR shares, presented within shareholders' equity ('Deferred compensation trust (16,710)' / 'Deferred compensation liability 16,710'). 'Defined benefit' appears nowhere in the filing (full-text search of nvr-20251231.htm, 2026-08-30); the balance sheet presents no pension caption. |
| `asset_retirement_obligation` | 0 | store | VERIFIED (same_page) | E68.1: Item 8, Consolidated Balance Sheets, December 31, 2025, 10-K 0000906163-26-000018 filed 2026-02-11 -- liabilities presented: Homebuilding 'Accounts payable', 'Accrued expenses and other liabilities' (376,976), 'Customer deposits', 'Operating lease liabilities', 'Senior notes'; Mortgage Banking 'Accounts payable and other liabilities' (53,738), 'Operating lease liabilities'. No asset retirement or decommissioning caption; 'asset retirement', 'decommission', 'dilapidation' and 'restoration obligation' appear nowhere in the filing (full-text search, 2026-08-30). A homebuilder that builds on lots it acquires finished from developers under lot purchase agreements, owning no plant requiring decommissioning: the absence is evidence. 'Accrued expenses and other liabilities' is a caption with room (E25) -- it holds the warranty reserve, accrued interest on unrecognised tax benefits (8,600) and the finance lease liabilities -- and is named here. |
| `cash_and_equivalents` | 1.916e+09 | store | VERIFIED (same_page) | E71 / E69: Item 8, Consolidated Balance Sheets, December 31, 2025, 10-K 0000906163-26-000018 filed 2026-02-11 (in thousands): Homebuilding 'Cash and cash equivalents | 1,883,844' + Mortgage Banking 'Cash and cash equivalents | 32,642' = 1,916,486. The issuer's own reconciliation: the Consolidated Statements of Cash Flows close on 'cash, restricted cash and cash equivalents' 1,956,881 (tagged us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents [as of 2025-12-31]) = 1,883,844 + 32,642 + 'Restricted cash | 34,348' (Homebuilding) + 'Restricted cash | 6,047' (Mortgage Banking). THE RESTRICTED CASH, 40,395, IS EXCLUDED: presented under its own caption on both segments, escrowed, not available to service debt; the field is the balance sheet's cash caption. No us-gaap element carries either segment's cash on its own. |
| `operating_lease_payments` | 3.293e+07 | store | VERIFIED (tagged) | us-gaap:OperatingLeasePayments [2025-01-01..2025-12-31] 10-K 0000906163-26-000018 filed 2026-02-11 |

*Tool commit: `ACN/GDDY/NVR/ULTA first strikes, 2026-08-30, 179f2b4`.*


</details>

### NVR -- the framework's own output on the price (NOT a recommendation)

- price 6396.27 USD vs fv_base 4,978.10 USD: **+28.5%** -- price is ABOVE fv_base
- price 6396.27 USD vs FV_bull 6,605.52 USD: **-3.2%** -- price is BELOW the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': FIRES** (price >= fv_base). A trim presupposes a position; none is held.
- **C4 (E42: no horizon -- above FV_bull the full position is sold at the next session): does not fire.** Price is below FV_bull. Expected return from 6396.27 to FV_bull 6,605.52 is **+3.3%** against the index core's 7.0% a year (E29's anchor); read as ONE year, the bull-case gap is BELOW the index.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are not written there.
- **It does not score tier.** Section 4.4 has not run for NVR; MBP is printed as DATA MISSING, and the per-tier figures are the range, not a choice.
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.
