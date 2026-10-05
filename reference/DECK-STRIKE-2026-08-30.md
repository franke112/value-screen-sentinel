# DECK -- first section 5 strike on the tool path, 2026-08-30

**2026-08-30 19:16 CEST. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The section 5 run record is written to `reference/run-records/DECK-2026-08-30.json` so that linking it to a watchlist entry (`run_record:`) remains the owner's write.

Growth view: `reference/growth-views/DECK.md`, pre-registered by the owner 2026-08-25, BEFORE this script ran and before g* was solved (E28's binding order).

Tool: `tools/strike_rmv_rkt_pndora_deck_2026_08_30.py` at `RMV.L/RKT.L/PNDORA.CO/DECK first strikes, 2026-08-30, d4425b5`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# DECK -- section 5 strike, 2026-08-30 19:16 CEST

Store: `config/manual/DECK.yaml` (money_unit whole). **BASIS: `annual FY2026`, the twelve months ending 2026-03-31** (E19), 152 days old; the FY2027 Q1 10-Q is passed over by the annual path. Price: last SETTLED close **87.76 USD** on 2026-08-28 (tool fetch, 2026-08-30 19:16 CEST).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED.

- record complete: **True**
- **FCF0: 1,084.2 USD m** -- accrual proxy (E34.1): net interest from the income statement: the income statement's net, -61.1 USD m REMOVED (a net interest INCOME). Pre-tax, as E34 accepts.
- **share-based compensation (E36): 44.8 USD m deducted = 4.1% of FCF0** (4.0% of the flow before the deduction)
- lease principal (E70): 92.8 USD m added back (8.6% of FCF0); the lease liability stays in net debt
- **net debt: -1,495.3 USD m (NET CASH)** -- borrowings 0 + 0 + leases 375,194,000 (E35: always in; finance leases beside operating, E65) + pension deficit 0 (E35.1) + asset retirement obligations 36,790,000 (E68) + prepaid delivery obligations 0 (E81) - cash 1,907,249,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1)
- **asset-retirement leg (E68): 36,790,000.0 (store unit)**, a stated figure (declaration 8): us-gaap:AssetRetirementObligationsNoncurrent [as of 2026-03-31] 10-K 0001628280-26-037664 filed 2026-05-22 -- an element the tag map does not read, entered by h
- divisor: 145,805,000 shares -- weighted-average DILUTED count for annual FY2026, the same window as the flows (E38) (`divisor_basis: weighted_average`)

- **fv_base (Method C, E28): 127.49 USD**
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **136.68 / 127.49 / 119.54 USD**
- bear (g 0.0%): **100.88 USD**
- bull (g 8.0%): **174.10 USD**
- implied growth g* at the settled close 87.76 USD: **-2.16%** (E28; the view in `reference/growth-views/DECK.md` was fixed 2026-08-25, before this was solved)
- *r 9.5% flat* (E37)

- **tier: NOT SCORED. MBP: DATA MISSING** -- E28's MBP is the bear-case value times the tier cushion, and section 4.4 has not scored DECK, so there is no tier to apply. **Not struck; not computed on a placeholder.** What it WOULD be against the bear case 100.88 USD, across E29's band, so the range is visible before scoring. **E77: the regime is ELEVATED, so whatever tier section 4.4 produces is applied one tier stricter** (a Tier 1 score takes the tier 2 line below, a Tier 2 score the tier 3 line):
  - tier 1 (x0.80): **80.71 USD** (r 9.0% 86.01 / r 10.0% 76.10); price 87.76 is +8.7% against it
  - tier 2 (x0.70): **70.62 USD** (r 9.0% 75.26 / r 10.0% 66.59); price 87.76 is +24.3% against it
  - tier 3 (x0.60): **60.53 USD** (r 9.0% 64.51 / r 10.0% 57.08); price 87.76 is +45.0% against it

<details><summary>the run record -- every leg of the bridge (declaration 4, item by item) and every input with its provenance (declaration 8), including every proxy and every caption zero</summary>

# section 5 run record — DECK — 2026-08-30T19:16:25+02:00

**Fair value 127.49 USD** at g 3.50%, r 9.50%.

*r 9.5% flat*

- **FCF0:** 1,084,237,000 USD whole — accrual proxy (E34.1): net interest from the income statement

- **basis (E19):** annual FY2026

- **units:** money stated in whole, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 145,805,000 — weighted-average DILUTED count for annual FY2026, the same window as the flows (E38), as of 2026-03-31; divisor basis `weighted_average` (E75 / E75.1); memo (E38, never the divisor): 139,978,000 as of 2026-03-31 |
| 2 | share-based compensation | deducted, 44,835,000 |
| 3 | interest | interest paid is INSIDE operating cash flow; the filer states interest paid as cash but no interest received, so the net is the INCOME STATEMENT'S -- an ACCRUAL PROXY (E34.1): net interest INCOME of 61,083,000 is REMOVED, and net debt is then subtracted ONCE. Interest paid alone is never the net. Read from: SEC XBRL companyfacts for CIK 0000910521 (Deckers Brands) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0000910521.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ASC 230-10-45-17(d): under US GAAP interest paid is an OPERATING cash outflow for every filer, so this filer's `operating_cash_flow` already bears its interest. No tag states it because the standard leaves no choice to state |
| 3.1 | lease principal (E70) | the operating cash flow BEARS the operating lease payments (ASC 842-20-45-5(a)); 92,823,000 is ADDED BACK so the lease is charged once, in net debt (E70) -- leg: `operating_lease_payments` (cash paid for operating leases, the whole payment: principal under E70; its interest component under E34, being inside operating cash flow). Read from: FRAMEWORK-EDITS E70, applied 2026-08-30 to a us-gaap filer ASC 842-20-45-5(a): a lessee classifies payments for operating leases within OPERATING activities, so this filer's `operating_cash_flow` already bears them; the stated cash paid is `us-gaap:OperatingLeasePayments` ('cash paid for amounts included in the measurement of operating lease liabilities'), written as `operating_lease_payments` where tagged. No filer-specific tag states the classification because the standard leaves no choice |
| 4 | bridge | net debt -1,495,265,000 — borrowings 0 + 0 + leases 375,194,000 (E35: always in; finance leases beside operating, E65) + pension deficit 0 (E35.1) + asset retirement obligations 36,790,000 (E68) + prepaid delivery obligations 0 (E81) - cash 1,907,249,000 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: combined: capex_combined, the one line the issuer prints |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 3.50% from `reference/growth-views/DECK.md` (2026-08-25) |
| 7 | as-of dates | flows to 2026-03-31; balance sheet 2026-03-31; share count 2026-03-31; price 2026-08-28 — **THEY AGREE** |
| 8 | provenance | 14 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | **DATA MISSING** on this basis |
| `leases` | 375,194,000 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 0 (stated) |
| `current_financial_assets` | **DATA MISSING** on this basis |
| `asset_retirement_obligations` | 36,790,000 |
| `prepaid_delivery_obligations` | 0 (stated) |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_combined` | -8.462e+07 | store | VERIFIED (tagged) | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment [2025-04-01..2026-03-31] 10-K 0001628280-26-037664 filed 2026-05-22 |
| `operating_cash_flow` | 1.182e+09 | store | VERIFIED (tagged) | us-gaap:NetCashProvidedByUsedInOperatingActivities [2025-04-01..2026-03-31] 10-K 0001628280-26-037664 filed 2026-05-22 |
| `sbc` | 4.484e+07 | store | VERIFIED (tagged) | us-gaap:ShareBasedCompensation [2025-04-01..2026-03-31] 10-K 0001628280-26-037664 filed 2026-05-22 |
| `net_finance_costs` | -6.108e+07 | store | VERIFIED (tagged) | E18: finance_costs_period - finance_income_period, both on annual FY2026 |
| `diluted_weighted_average_shares` | 1.458e+08 | store | VERIFIED (tagged) | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding [2025-04-01..2026-03-31] 10-K 0001628280-26-037664 filed 2026-05-22 |
| `shares_point_in_time` | 1.4e+08 | store | VERIFIED (tagged) | us-gaap:CommonStockSharesOutstanding [as of 2026-03-31] 10-Q 0000910521-26-000022 filed 2026-07-30 |
| `financial_liabilities_current` | 0 | store | VERIFIED (caption_statement) | E25 / E78: Consolidated Balance Sheets as of March 31, 2026 (10-K 0001628280-26-037664), current liabilities presented: 'Trade accounts payable 384,529', 'Accrued payroll 119,597', 'Operating lease liabilities 83,931', 'Other accrued expenses 171,173', 'Income tax payable 36,475', 'Value added tax payable 8,369' -- no borrowings caption; no us-gaap debt element (DebtCurrent, LongTermDebt, LineOfCredit) is tagged at 2026-03-31. Note 6, Revolving Credit Facilities, Borrowing Activity, states the absence in words for the Primary Credit Facility (quoted) and the China Credit Facility (quoted on financial_liabilities_noncurrent) |
| `financial_liabilities_noncurrent` | 0 | store | VERIFIED (caption_statement) | E25 / E78: the same balance sheet, long-term liabilities presented: 'Long-term operating lease liabilities 291,263', 'Income tax liability 26,313', 'Other long-term liabilities 66,477' -- no borrowings caption; nothing drawn under either facility (Note 6, Borrowing Activity: 'During the year ended March 31, 2026, the Company made no borrowings or repayments under' each facility) |
| `lease_liabilities` | 3.752e+08 | store | VERIFIED (tagged) | us-gaap:OperatingLeaseLiability [as of 2026-03-31] 10-K 0001628280-26-037664 filed 2026-05-22 |
| `pension_deficit` | 0 | store | VERIFIED (caption_statement) | E35.1 / E78: 10-K 0001628280-26-037664, Note 1, Retirement Plan -- defined contribution only; no defined-benefit obligation is described anywhere in the filing and no retirement caption is presented on the balance sheet |
| `asset_retirement_obligation` | 3.679e+07 | store | VERIFIED (tagged) | us-gaap:AssetRetirementObligationsNoncurrent [as of 2026-03-31] 10-K 0001628280-26-037664 filed 2026-05-22 -- an element the tag map does not read, entered by hand from the companyfacts fact (E68; E40: verified by provenance, tag + accession + filing date). The 10-K's Note 1, Asset Retirement Obligations (AROs), roll-forward for the year ended March 31, 2026: 'Beginning balance $ 28,118', 'Additions and changes in estimate 8,152', 'Liabilities settled during the period (735)', 'Accretion expenses 1,122', 'Foreign currency translation gains 133', 'Ending balance $ 36,790' (thousands); 'The Company is contractually obligated under certain of its lease agreements to restore certain retail, office, and warehouse facilities back to their original conditions'; 'The Company's AROs are recorded in other long-term liabilities in the consolidated balance sheets' (us-gaap:OtherLiabilitiesNoncurrent 66,477 has the room) |
| `prepaid_delivery_obligation` | 0 | store | VERIFIED (cross_document) | E81 (2026-08-30): Consolidated Balance Sheets as of March 31, 2026, liabilities presented -- the six current and three long-term captions named on financial_liabilities_current / _noncurrent above; no streaming, prepaid-offtake or prepaid-delivery caption. Cross-checked against the 10-K's own tags under E59.1 (component sum): us-gaap:AccountsPayableTradeCurrent 384,529 + EmployeeRelatedLiabilitiesCurrent 119,597 + OperatingLeaseLiabilityCurrent 83,931 + OtherAccruedLiabilitiesCurrent 171,173 + AccruedIncomeTaxesCurrent 36,475 + deck:ValueAddedTaxPayable 8,369 (an issuer extension tagged in the 10-K's inline XBRL, not carried by companyfacts) = LiabilitiesCurrent 804,074 EXACTLY; OperatingLeaseLiabilityNoncurrent 291,263 + AccruedIncomeTaxesNoncurrent 26,313 + OtherLiabilitiesNoncurrent 66,477 = LiabilitiesNoncurrent 384,053 EXACTLY -- the tagged captions exhaust both totals, leaving no room for a prepaid-delivery caption. The wholesale sales return liability and the loyalty / gift-card contract liabilities inside 'Other accrued expenses' are E81's ordinary contract liabilities, named here and not this leg |
| `cash_and_equivalents` | 1.907e+09 | store | VERIFIED (tagged) | us-gaap:CashAndCashEquivalentsAtCarryingValue [as of 2026-03-31] 10-Q 0000910521-26-000022 filed 2026-07-30 |
| `operating_lease_payments` | 9.282e+07 | store | VERIFIED (tagged) | us-gaap:OperatingLeasePayments [2025-04-01..2026-03-31] 10-K 0001628280-26-037664 filed 2026-05-22 |

*Tool commit: `RMV.L/RKT.L/PNDORA.CO/DECK first strikes, 2026-08-30, d4425b5`.*


</details>

### DECK -- the framework's own output on the price (NOT a recommendation)

- price 87.76 USD vs fv_base 127.49 USD: **-31.2%** -- price is BELOW fv_base
- price 87.76 USD vs FV_bull 174.10 USD: **-49.6%** -- price is BELOW the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': does not fire** (price < fv_base). A trim presupposes a position; none is held.
- **C4 (E42: no horizon -- above FV_bull the full position is sold at the next session): does not fire.** Price is below FV_bull. Expected return from 87.76 to FV_bull 174.10 is **+98.4%** against the index core's 7.0% a year (E29's anchor); read as ONE year, the bull-case gap is ABOVE the index.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are not written there.
- **It does not score tier.** Section 4.4 has not run for DECK; MBP is printed as DATA MISSING, and the per-tier figures are the range, not a choice (E76: the reading comes before the tier, not before this strike).
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.
