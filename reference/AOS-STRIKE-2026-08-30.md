# AOS -- first section 5 strike on the tool path, 2026-08-30

**2026-08-30 03:14 EDT. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The section 5 run record is written to `reference/run-records/AOS-2026-08-30.json` so that linking it to a watchlist entry (`run_record:`) remains the owner's write.

Growth view: `reference/growth-views/AOS.md`, pre-registered by the owner 2026-08-30, BEFORE this script ran and before g* was solved (E28's binding order).

Tool: `tools/strike_lii_aos_2026_08_30.py` at `LII/AOS first strikes, 2026-08-30, 871b861`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# AOS -- section 5 strike, 2026-08-30 03:14 EDT

Store: `config/manual/AOS.yaml`. **BASIS: `annual FY2025`, the twelve months ending 2025-12-31** (E19). Price: last SETTLED close **60.38 USD** (60.38 USD at 1:1) on 2026-08-28 (tool fetch, 2026-08-30 03:14 EDT).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED.

- record complete: **True**
- **FCF0: 545.7 USD m** -- proxy (E61 / E61.1): interest income not tagged, or not stated anywhere in the filing; add-back overstated by the unrecorded income (E61.1, applied by hand after the filing was read: bound **2.5% of FCF0**, 13.5 USD m added back)
- **net debt: 35.8 USD m** -- borrowings 42,300,000 + 112,700,000 + leases 47,900,000 (E35: always in; finance leases beside operating, E65) + pension deficit 7,400,000 (E35.1) + asset retirement obligations 0 (E68) - cash 174,500,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1)
- **asset-retirement leg (E68): 0 -- a CAPTION ZERO under E68.1, not a figure.** The balance sheet presents no asset-retirement or decommissioning caption and the business owns nothing requiring decommissioning (E68.1); the remediation accrual behind the deferred tax asset 'Environmental liabilities 1.3' is named on the field, not included. Every other leg of the bridge is a tagged figure (declaration 8).

- **fv_base (Method C, E28): 62.66 USD**
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **67.63 / 62.66 / 58.35 USD**
- bear (g 0.0%): **46.61 USD**
- bull (g 7.0%): **78.38 USD**
- implied growth g* at the settled close 60.38 USD: **3.50%** (E28; the view in `reference/growth-views/AOS.md` was fixed 2026-08-30, before this was solved)
- *r 9.5% flat* (E37)

- **tier: NOT SCORED. MBP: DATA MISSING** -- E28's MBP is the bear-case value times the tier cushion, and section 4.4 has not scored AOS, so there is no tier to apply. **Not struck; not computed on a placeholder.** What it WOULD be against the bear case 46.61 USD, across E29's band, so the range is visible before scoring:
  - tier 1 (x0.80): **37.29 USD** (r 9.0% 40.03 / r 10.0% 34.91); price 60.38 is +61.9% against it
  - tier 2 (x0.70): **32.63 USD** (r 9.0% 35.03 / r 10.0% 30.55); price 60.38 is +85.1% against it
  - tier 3 (x0.60): **27.97 USD** (r 9.0% 30.02 / r 10.0% 26.18); price 60.38 is +115.9% against it

<details><summary>the run record -- every leg of the bridge (declaration 4, item by item) and every input with its provenance (declaration 8), including the caption zero on the asset-retirement leg</summary>

# section 5 run record — AOS — 2026-08-30T03:14:24-04:00

**Fair value 62.66 USD** at g 4.00%, r 9.50%.

*r 9.5% flat*

- **FCF0:** 545,700,000 USD whole — proxy (E61 / E61.1): interest income not tagged, or not stated anywhere in the filing; add-back overstated by the unrecorded income (bound: 2.5% of FCF0)

- **basis (E19):** annual FY2025

- **units:** money stated in whole, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 141,914,840 — weighted-average DILUTED count for annual FY2025, the same window as the flows (E38), as of 2025-12-31; memo (E38, never the divisor): — |
| 2 | share-based compensation | deducted, 13,800,000 |
| 3 | interest | interest paid is INSIDE operating cash flow; the filer tags gross interest expense but no net and no interest-received figure, so the add-back is the TAGGED INTEREST EXPENSE ALONE, 13,500,000 -- a PROXY (E61), bounded and one-sided: interest income is never negative, so this can only OVERSTATE FCF0, by no more than the unrecorded interest income, and net debt is then subtracted ONCE. Read from: SEC XBRL companyfacts for CIK 0000091142 (SMITH A O CORP) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0000091142.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 230-10-45-17(d): under US GAAP interest paid is an OPERATING cash outflow for every filer, so this filer's `operating_cash_flow` already bears its interest. No tag states it because the standard leaves no choice to state |
| 4 | bridge | net debt 35,800,000 — borrowings 42,300,000 + 112,700,000 + leases 47,900,000 (E35: always in; finance leases beside operating, E65) + pension deficit 7,400,000 (E35.1) + asset retirement obligations 0 (E68) - cash 174,500,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: combined: capex_combined, the one line the issuer prints |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 4.00% from `reference/growth-views/AOS.md` (2026-08-30) |
| 7 | as-of dates | flows to 2025-12-31; balance sheet 2025-12-31; share count 2025-12-31; price 2026-08-28 — **THEY AGREE** |
| 8 | provenance | 11 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | **DATA MISSING** on this basis |
| `leases` | 47,900,000 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 7,400,000 |
| `current_financial_assets` | **DATA MISSING** on this basis |
| `asset_retirement_obligations` | 0 (stated) |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_combined` | -7.08e+07 | store | VERIFIED (tagged) | us-gaap:PaymentsToAcquireProductiveAssets [2025-01-01..2025-12-31] 10-K 0000091142-26-000008 filed 2026-02-10 -- CONCEPT: the filer's ONE capital-expenditure line, tagged under the broader 'productive assets' element and not the PP&E one; E23's combined line, a record of the issuer's presentation and not a claim about what is inside it |
| `operating_cash_flow` | 6.168e+08 | store | VERIFIED (tagged) | us-gaap:NetCashProvidedByUsedInOperatingActivities [2025-01-01..2025-12-31] 10-K 0000091142-26-000008 filed 2026-02-10 |
| `sbc` | 1.38e+07 | store | VERIFIED (tagged) | us-gaap:AllocatedShareBasedCompensationExpense [2025-01-01..2025-12-31] 10-K 0000091142-26-000008 filed 2026-02-10 -- CONCEPT: the INCOME-STATEMENT share-based compensation CHARGE, taken because this filer tags no `ShareBasedCompensation` (the cash-flow statement's non-cash add-back). E36 subtracts the cost either way; the two elements state one charge from two statements and can differ by any capitalised or discontinued portion |
| `finance_costs_period` | 1.35e+07 | store | VERIFIED (same_page) | E69: Item 8, CONSOLIDATED STATEMENTS OF EARNINGS, year ended December 31, 2025, 10-K 0000091142-26-000008 filed 2026-02-10: 'Interest expense | 13.5' (dollars in millions); the same line in Item 7, Results of Operations. Tagged by the filer as us-gaap:InterestExpense, an element the map does not read (NOT_WRITTEN: it carries a NET line for Lennox and a GROSS line here); read by hand as the GROSS expense. INTEREST INCOME APPEARS NOWHERE IN THE FILING AS A FIGURE: the statement prints 'Other income, net | (0.6)', which Item 7 describes as 'lower foreign currency translation losses compared to the prior year and lower interest income from lower average cash balances', and the segment note says only 'Other expense (income), net consists primarily of interest income' -- a composite, not a net finance figure, so it is NOT entered as net_finance_costs and no E18 pair forms. Under E61.1 (2026-08-30) the stated expense alone is the add-back -- interest_source: interest_expense_only on this file, the bound printed as a percentage of FCF0. |
| `diluted_weighted_average_shares` | 1.419e+08 | store | VERIFIED (tagged) | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding [2025-01-01..2025-12-31] 10-K 0000091142-26-000008 filed 2026-02-10 |
| `financial_liabilities_current` | 4.23e+07 | store | VERIFIED (tagged) | us-gaap:LongTermDebtCurrent [as of 2025-12-31] 10-Q 0000091142-26-000098 filed 2026-07-30 |
| `financial_liabilities_noncurrent` | 1.127e+08 | store | VERIFIED (tagged) | us-gaap:LongTermDebtNoncurrent [as of 2025-12-31] 10-Q 0000091142-26-000098 filed 2026-07-30 |
| `lease_liabilities` | 4.79e+07 | store | VERIFIED (tagged) | us-gaap:OperatingLeaseLiability [as of 2025-12-31] 10-K 0000091142-26-000008 filed 2026-02-10 |
| `pension_deficit` | 7.4e+06 | store | VERIFIED (tagged) | us-gaap:DefinedBenefitPensionPlanLiabilitiesNoncurrent [as of 2025-12-31] 10-K 0000091142-26-000008 filed 2026-02-10 |
| `asset_retirement_obligation` | 0 | store | VERIFIED (same_page) | E68.1: Item 8, Consolidated Balance Sheets as of December 31, 2025, 10-K 0000091142-26-000008 filed 2026-02-10 -- liabilities presented: 'Trade payables', 'Accrued payroll and benefits', 'Accrued liabilities', 'Product warranties', 'Long-term debt due within one year', 'Long-term debt', 'Product warranties', 'Pension liabilities', 'Long-term operating lease liabilities', 'Other liabilities'; no asset retirement or decommissioning caption, and neither term appears anywhere in the filing (full-text search of the primary document, 2026-08-29). A water-heater and boiler manufacturer owning nothing that requires decommissioning: the absence is evidence. NAMED, NOT INCLUDED: the income-tax note lists a deferred tax asset on 'Environmental liabilities 1.3', i.e. a remediation accrual (ASC 410-30) inside 'Accrued liabilities' / 'Other liabilities' -- a remediation liability, not an asset retirement obligation, outside E68 as ruled. |
| `cash_and_equivalents` | 1.745e+08 | store | VERIFIED (tagged) | us-gaap:CashAndCashEquivalentsAtCarryingValue [as of 2025-12-31] 10-Q 0000091142-26-000098 filed 2026-07-30 |

*Tool commit: `LII/AOS first strikes, 2026-08-30, 871b861`.*


</details>

### AOS -- the framework's own output on the price (NOT a recommendation)

- price 60.38 USD vs fv_base 62.66 USD: **-3.6%** -- price is BELOW fv_base
- price 60.38 USD vs FV_bull 78.38 USD: **-23.0%** -- price is BELOW the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': does not fire** (price < fv_base).
- **C4, 'exit when even the bull case does not beat the index': does not fire.** Expected return from 60.38 to FV_bull 78.38 is **+29.8%**; the index core's expected return is 7.0% a year (E29's anchor). C4 states no horizon: on the reading applied to MSFT and UNA.AS (price above/below FV_bull, expected return positive or negative) it does not fire outright here since price is below FV_bull; read as ONE year against 7.0%, the bull-case gap is ABOVE the index. Which horizon C4 means is the owner's to say.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are not written there.
- **It does not score tier.** Section 4.4 has not run for AOS; MBP is printed as DATA MISSING, and the per-tier figures are the range, not a choice.
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.

---

## Addendum, 2026-08-30 (evening) — this figure is HISTORICAL (owner's bookkeeping instruction, Part E)

The 62.66 above is a dated historical figure struck under since-superseded
rulings: it predates E70 (the lease is charged twice here — the 47.9m
liability in net debt and the payments inside operating cash flow), E90
(the per-tier range printed above is the E28-era bear-value x 0.80/0.70/0.60
arithmetic) and E88/E91. AOS is OFF the watchlist and carries NO MBP;
nothing above is a live threshold. A re-strike under current rulings still
waits on the E70 lease question the handover names — no cash-paid lease
figure is stated in the 10-K or either 2026 10-Q, and accepting the filer's
"materially consistent with the expense recorded" sentence as a marked
proxy would need a ruling. Recorded 2026-08-30; the strike text above is
unedited.
