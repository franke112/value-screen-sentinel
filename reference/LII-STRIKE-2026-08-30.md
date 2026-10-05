# LII -- first section 5 strike on the tool path, 2026-08-30

**2026-08-30 03:14 EDT. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The section 5 run record is written to `reference/run-records/LII-2026-08-30.json` so that linking it to a watchlist entry (`run_record:`) remains the owner's write.

Growth view: `reference/growth-views/LII.md`, pre-registered by the owner 2026-08-30, BEFORE this script ran and before g* was solved (E28's binding order).

Tool: `tools/strike_lii_aos_2026_08_30.py` at `LII/AOS first strikes, 2026-08-30, 871b861`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# LII -- section 5 strike, 2026-08-30 03:14 EDT

Store: `config/manual/LII.yaml`. **BASIS: `annual FY2025`, the twelve months ending 2025-12-31** (E19). Price: last SETTLED close **393.39 USD** (393.39 USD at 1:1) on 2026-08-28 (tool fetch, 2026-08-30 03:14 EDT).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED.

- record complete: **True**
- **FCF0: 650.6 USD m** -- accrual proxy (E34.1): net interest from the income statement: E18's pair, `finance_costs_period` less `finance_income_period` on the basis, 40.9 USD m added back
- **net debt: 1,755.2 USD m** -- borrowings 244,300,000 + 1,144,100,000 + leases 382,300,000 (E35: always in; finance leases beside operating, E65) + pension deficit 18,700,000 (E35.1) + asset retirement obligations 0 (E68) - cash 34,200,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1)
- **asset-retirement leg (E68): 0 -- a CAPTION ZERO under E68.2, not a figure.** The filer discloses environmental remediation accruals inside captions with room and states no balance-sheet amount; Note 5 and the 10.9m charged in 2025 are named on the field (E68.2). Every other leg of the bridge is a tagged figure (declaration 8).

- **fv_base (Method C, E28): 274.27 USD**
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **300.32 / 274.27 / 251.73 USD**
- bear (g 0.0%): **174.40 USD**
- bull (g 8.0%): **355.35 USD**
- implied growth g* at the settled close 393.39 USD: **9.20%** (E28; the view in `reference/growth-views/LII.md` was fixed 2026-08-30, before this was solved)
- *r 9.5% flat* (E37)

- **tier: NOT SCORED. MBP: DATA MISSING** -- E28's MBP is the bear-case value times the tier cushion, and section 4.4 has not scored LII, so there is no tier to apply. **Not struck; not computed on a placeholder.** What it WOULD be against the bear case 174.40 USD, across E29's band, so the range is visible before scoring:
  - tier 1 (x0.80): **139.52 USD** (r 9.0% 152.63 / r 10.0% 128.15); price 393.39 is +182.0% against it
  - tier 2 (x0.70): **122.08 USD** (r 9.0% 133.55 / r 10.0% 112.13); price 393.39 is +222.2% against it
  - tier 3 (x0.60): **104.64 USD** (r 9.0% 114.47 / r 10.0% 96.11); price 393.39 is +275.9% against it

<details><summary>the run record -- every leg of the bridge (declaration 4, item by item) and every input with its provenance (declaration 8), including the caption zero on the asset-retirement leg</summary>

# section 5 run record — LII — 2026-08-30T03:14:24-04:00

**Fair value 274.27 USD** at g 5.00%, r 9.50%.

*r 9.5% flat*

- **FCF0:** 650,600,000 USD whole — accrual proxy (E34.1): net interest from the income statement

- **basis (E19):** annual FY2025

- **units:** money stated in whole, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 35,400,000 — weighted-average DILUTED count for annual FY2025, the same window as the flows (E38), as of 2025-12-31; memo (E38, never the divisor): — |
| 2 | share-based compensation | deducted, 29,100,000 |
| 3 | interest | interest paid is INSIDE operating cash flow; the filer states interest paid as cash but no interest received, so the net is the INCOME STATEMENT'S -- an ACCRUAL PROXY (E34.1): net interest EXPENSE of 40,900,000 is ADDED BACK, and net debt is then subtracted ONCE. Interest paid alone is never the net. Read from: SEC XBRL companyfacts for CIK 0001069202 (LENNOX INTERNATIONAL INC) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0001069202.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 230-10-45-17(d): under US GAAP interest paid is an OPERATING cash outflow for every filer, so this filer's `operating_cash_flow` already bears its interest. No tag states it because the standard leaves no choice to state |
| 4 | bridge | net debt 1,755,200,000 — borrowings 244,300,000 + 1,144,100,000 + leases 382,300,000 (E35: always in; finance leases beside operating, E65) + pension deficit 18,700,000 (E35.1) + asset retirement obligations 0 (E68) - cash 34,200,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: combined: capex_combined, the one line the issuer prints |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 5.00% from `reference/growth-views/LII.md` (2026-08-30) |
| 7 | as-of dates | flows to 2025-12-31; balance sheet 2025-12-31; share count 2025-12-31; price 2026-08-28 — **THEY AGREE** |
| 8 | provenance | 11 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | **DATA MISSING** on this basis |
| `leases` | 382,300,000 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 18,700,000 |
| `current_financial_assets` | **DATA MISSING** on this basis |
| `asset_retirement_obligations` | 0 (stated) |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_combined` | -1.188e+08 | store | VERIFIED (tagged) | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment [2025-01-01..2025-12-31] 10-K 0001069202-26-000028 filed 2026-02-17 |
| `operating_cash_flow` | 7.576e+08 | store | VERIFIED (tagged) | us-gaap:NetCashProvidedByUsedInOperatingActivities [2025-01-01..2025-12-31] 10-K 0001069202-26-000028 filed 2026-02-17 |
| `sbc` | 2.91e+07 | store | VERIFIED (tagged) | us-gaap:ShareBasedCompensation [2025-01-01..2025-12-31] 10-K 0001069202-26-000028 filed 2026-02-17 |
| `net_finance_costs` | 4.09e+07 | store | VERIFIED (tagged) | E18: finance_costs_period - finance_income_period, both on annual FY2025 |
| `diluted_weighted_average_shares` | 3.54e+07 | store | VERIFIED (tagged) | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding [2025-01-01..2025-12-31] 10-K 0001069202-26-000028 filed 2026-02-17 |
| `financial_liabilities_current` | 2.443e+08 | store | VERIFIED (tagged) | E66 -- two stated current-borrowing captions, added: us-gaap:LongTermDebtCurrent [as of 2025-12-31] 10-K 0001069202-26-000028 filed 2026-02-17 -- E67: tagged EQUAL to `LongTermDebtAndCapitalLeaseObligationsCurrent` 18,300,000, the inclusive caption, so this ex-lease element was tagged INCLUSIVE of its finance lease: 18,300,000 of it is `FinanceLeaseLiabilityCurrent` and E65 does not add that again = 18,300,000 + us-gaap:CommercialPaper [as of 2025-12-31] 10-Q 0001069202-26-000054 filed 2026-04-29 -- CONCEPT: commercial paper outstanding, read as the current borrowing because this filer tags neither a current-maturities nor a short-term-borrowings element at this year end = 226,000,000 = 244,300,000 |
| `financial_liabilities_noncurrent` | 1.144e+09 | store | VERIFIED (tagged) | us-gaap:LongTermDebtAndCapitalLeaseObligations [as of 2025-12-31] 10-Q 0001069202-26-000054 filed 2026-04-29 -- E67: borrowings AND finance leases as one non-current caption, read whole because the filer tags no borrowings-only element; 50,600,000 of it is `FinanceLeaseLiabilityNoncurrent` and E65 does not add that again |
| `lease_liabilities` | 3.823e+08 | store | VERIFIED (tagged) | E65 -- operating and finance lease liabilities: us-gaap:OperatingLeaseLiability [as of 2025-12-31] 10-K 0001069202-26-000028 filed 2026-02-17 = 382,300,000 + us-gaap:FinanceLeaseLiability [as of 2025-12-31] 10-K 0001069202-26-000028 filed 2026-02-17 = 68,900,000, of which 18,300,000 already inside `financial_liabilities_current` (E67) and 50,600,000 already inside `financial_liabilities_noncurrent` (E67), so 0 is added = 382,300,000 |
| `pension_deficit` | 1.87e+07 | store | VERIFIED (tagged) | us-gaap:DefinedBenefitPensionPlanLiabilitiesNoncurrent [as of 2025-12-31] 10-Q 0001069202-26-000054 filed 2026-04-29 |
| `asset_retirement_obligation` | 0 | store | VERIFIED (same_page) | E68.2: Item 8, Consolidated Balance Sheets as of December 31, 2025, 10-K 0001069202-26-000028 filed 2026-02-17 -- liabilities presented: 'Commercial paper', 'Current maturities of long-term debt', 'Current operating lease liabilities', 'Accounts payable', 'Accrued expenses', 'Income taxes payable', 'Long-term debt', 'Long-term operating lease liabilities', 'Pensions', 'Other liabilities'; no asset retirement or decommissioning caption, and neither term appears anywhere in the filing (full-text search of the primary document, 2026-08-29). NAMED, UNQUANTIFIED: Note 5, Commitments and Contingencies -- Environmental: 'Total environmental accruals are included in Accrued expenses and Other liabilities on the accompanying Consolidated Balance Sheets' and 'we do not believe that any future remediation related to those facilities will be material to our results of operations'; Item 7: 'Environmental liabilities and special litigation charges 10.9' for 2025, which 'relate to estimated remediation costs at some of our facilities and outstanding legal settlements including asbestos. Refer to Note 5' -- a CHARGE, not a balance; no balance-sheet amount is stated anywhere. The accrual sits inside 'Accrued expenses' / 'Other liabilities', captions with room (E25). Zero here BY RULING (E68.2), with the omission named, not because it is nil. |
| `cash_and_equivalents` | 3.42e+07 | store | VERIFIED (tagged) | us-gaap:CashAndCashEquivalentsAtCarryingValue [as of 2025-12-31] 10-Q 0001069202-26-000054 filed 2026-04-29 |

*Tool commit: `LII/AOS first strikes, 2026-08-30, 871b861`.*


</details>

### LII -- the framework's own output on the price (NOT a recommendation)

- price 393.39 USD vs fv_base 274.27 USD: **+43.4%** -- price is ABOVE fv_base
- price 393.39 USD vs FV_bull 355.35 USD: **+10.7%** -- price is ABOVE the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': FIRES** (price >= fv_base).
- **C4, 'exit when even the bull case does not beat the index': FIRES.** Expected return from 393.39 to FV_bull 355.35 is **-9.7%**; the index core's expected return is 7.0% a year (E29's anchor). C4 states no horizon: on the reading applied to MSFT and UNA.AS (price above/below FV_bull, expected return positive or negative) it fires outright here since price is above FV_bull; read as ONE year against 7.0%, the bull-case gap is BELOW the index, though C4 already fires outright. Which horizon C4 means is the owner's to say.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are not written there.
- **It does not score tier.** Section 4.4 has not run for LII; MBP is printed as DATA MISSING, and the per-tier figures are the range, not a choice.
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.
