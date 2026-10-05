# CTSH -- first section 5 strike on the tool path, 2026-08-28

**2026-08-28 04:08 EDT. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The section 5 run record is written to `reference/run-records/CTSH-2026-08-28.json` so that linking it to a watchlist entry (`run_record:`) remains the owner's write.

Growth view: `reference/growth-views/CTSH.md`, pre-registered by the owner 2026-08-27, BEFORE this script ran (2026-08-28) and before g* was solved (E28's binding order).

Tool: `tools/strike_ctsh_2026_08_28.py` at `CTSH first strike, 2026-08-28, 729e4a3`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# CTSH -- section 5 strike, 2026-08-28 04:08 EDT

Store: `config/manual/CTSH.yaml`. **BASIS: `annual FY2025`, the twelve months ending 2025-12-31** (E19). Price: last SETTLED close **63.76 USD** (63.76 USD at 1:1) on 2026-08-27 (tool fetch, 2026-08-28 04:08 EDT).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED.

- record complete: **True**
- **FCF0: 2,451 USD m** -- proxy (E61): interest income not tagged, add-back overstated by the unrecorded income (bound: 1.5% of FCF0)

- **fv_base (Method C, E28): 83.01 USD**
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **89.49 / 83.01 / 77.39 USD**
- bear (g 0.0%): **62.09 USD**
- bull (g 7.0%): **103.50 USD**
- implied growth g* at the settled close 63.76 USD: **0.37%** (E28; the view in `reference/growth-views/CTSH.md` was fixed 2026-08-27, before this was solved)
- *r 9.5% flat* (E37)

- **tier: NOT SCORED.** Section 4.4 has not scored CTSH, so E28's MBP -- the bear-case value times the tier cushion -- has no tier to apply. **MBP is not struck here; this is DATA MISSING, not a computed absence.**

<details><summary>the run record -- includes the E61 proxy bound (declaration 3, interest) and the E62 pension composition (declaration 8, provenance for `pension_deficit`)</summary>

# section 5 run record — CTSH — 2026-08-28T04:08:38-04:00

**Fair value 83.01 USD** at g 4.00%, r 9.50%.

*r 9.5% flat*

- **FCF0:** 2,451,000,000 USD whole — proxy (E61): interest income not tagged, add-back overstated by the unrecorded income (bound: 1.5% of FCF0)

- **basis (E19):** annual FY2025

- **units:** money stated in whole, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 489,000,000 — weighted-average DILUTED count for annual FY2025, the same window as the flows (E38), as of 2025-12-31; memo (E38, never the divisor): 479,000,000 as of 2025-12-31 |
| 2 | share-based compensation | deducted, 181,000,000 |
| 3 | interest | interest paid is INSIDE operating cash flow; the filer tags gross interest expense but no net and no interest-received figure, so the add-back is the TAGGED INTEREST EXPENSE ALONE, 37,000,000 -- a PROXY (E61), bounded and one-sided: interest income is never negative, so this can only OVERSTATE FCF0, by no more than the unrecorded interest income, and net debt is then subtracted ONCE. Read from: SEC XBRL companyfacts for CIK 0001058290 (Cognizant Technology Solutions Corporation) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0001058290.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 230-10-45-17(d): under US GAAP interest paid is an OPERATING cash outflow for every filer, so this filer's `operating_cash_flow` already bears its interest. No tag states it because the standard leaves no choice to state |
| 4 | bridge | net debt -489,000,000 — borrowings 33,000,000 + 543,000,000 + leases 576,000,000 (E35: always in) + pension deficit 260,000,000 (E35.1) - cash 1,901,000,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: combined: capex_combined, the one line the issuer prints |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 4.00% from `reference/growth-views/CTSH.md` (2026-08-27) |
| 7 | as-of dates | flows to 2025-12-31; balance sheet 2025-12-31; share count 2025-12-31; price 2026-08-27 — **THEY AGREE** |
| 8 | provenance | 11 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | **DATA MISSING** on this basis |
| `leases` | 576,000,000 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 260,000,000 |
| `current_financial_assets` | **DATA MISSING** on this basis |

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
| `lease_liabilities` | 5.76e+08 | store | VERIFIED (tagged) | us-gaap:OperatingLeaseLiability [as of 2025-12-31] 10-K 0001058290-26-000008 filed 2026-02-12 |
| `pension_deficit` | 2.6e+08 | store | VERIFIED (same_page) | FRAMEWORK-EDITS E62 (ruled 2026-08-27): the SUM of two defined-benefit plans presented under the SAME note. (1) $55,000,000 -- Note 15, Employee Benefits, 10-K 0001058290-26-000008 filed 2026-02-12: 'Defined Benefit Pension Plans... the net liability recognized on the balance sheet for our pension plans was $55 million'; tagged us-gaap:DefinedBenefitPensionPlanLiabilitiesNoncurrent [as of 2025-12-31]. (2) $205,000,000 -- the same Note 15, 'Other Defined Benefit Plans': 'we offer a gratuity plan in India that is a statutory defined benefit plan... the amount accrued under the gratuity plan was $205 million... which is net of fund assets of $250 million' -- NOT TAGGED under any us-gaap concept in this filer's facts (checked against the full companyfacts JSON); sits inside the balance sheet's 'Other noncurrent liabilities' ($847m) with no reconciling note splitting it out. ONE-OFF NOTED: the India leg was $80 million at 2024-12-31; the note states the $125m increase is driven by 'the Labor Code reforms implemented by the Government of India' in Q4 2025, a $147 million charge 'recognized as a component of other comprehensive income' -- a regulatory reform, not an operating deterioration, and a later-year comparison must read the base effect accordingly, not as debt getting worse. |
| `cash_and_equivalents` | 1.901e+09 | store | VERIFIED (tagged) | us-gaap:CashAndCashEquivalentsAtCarryingValue [as of 2025-12-31] 10-Q 0001058290-26-000016 filed 2026-04-29 |

*Tool commit: `CTSH first strike, 2026-08-28, 729e4a3`.*


</details>

### CTSH -- the framework's own output on the price (NOT a recommendation)

- price 63.76 USD vs fv_base 83.01 USD: **-23.2%** -- price is BELOW fv_base
- price 63.76 USD vs FV_bull 103.50 USD: **-38.4%** -- price is BELOW the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': does not fire** (price < fv_base).
- **C4, 'exit when even the bull case does not beat the index': does not fire.** Expected return from 63.76 to FV_bull 103.50 is **+62.3%**; the index core's expected return is 7.0% a year (E29's anchor). C4 states no horizon: on the reading applied to MSFT and UNA.AS (price above/below FV_bull, expected return positive or negative) it does not fire outright here since price is below FV_bull; read as ONE year against 7.0%, the bull-case gap is ABOVE the index. Which horizon C4 means is the owner's to say.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are not written there.
- **It does not score tier.** Section 4.4 has not run for CTSH; MBP is printed as DATA MISSING rather than computed on a placeholder tier.
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.
