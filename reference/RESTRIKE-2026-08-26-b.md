# Build 2 -- SAP.DE and LIAB.ST re-struck on the TOOL PATH, after the eight rulings of 2026-08-26

**2026-08-26 09:00 CEST. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The two section 5 run records are written to `reference/run-records/` so that item 9's gate can be satisfied by linking them (`run_record:`), which is the owner's write.

Tool: `tools/restrike_2026_08_26_b.py` at `Build 2 after REVIEW-4, 2026-08-26, 3189211`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting (declaration 5).

## SAP.DE

Store: `config/manual/SAP.DE.yaml`. Basis **TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2** (R12M to 2026-06-30), named quarter by quarter (E41). Price: last SETTLED close **187.20 EUR** on 2026-08-24 (tool fetch, 2026-08-26 09:00 CEST).

**The store's gate refuses:** `FCF0 DATA MISSING` free cash flow, FCF0 (E34); `PERIODS DO NOT MATCH` net debt; `PERIODS DO NOT MATCH` FCF conversion. The record below fills what the store cannot hold BY HAND, each input with its page, and says so in declaration 4 and 8.

- record complete: **True** (and ADMISSIBLE: E40)
- **FCF0: 7,399 EUR m**
- **fv_base (Method C, E28): 139.48 EUR**
- band across E29's +/-0.5%: 151.17 / 139.48 / 129.38
- bear (g 6.0%): **120.27**
- bull (g 11.0%): **174.30**
- implied growth g* at 187.20: **11.96%** (E28; the view was fixed on 2026-08-26 before this was solved)
- *r 9.5% flat; non-USD bias: conservative* (E37)

- **tier: 1** -- item 5, carried from pre-REVIEW-4 scoring; section 4.4 untouched by the review
- **mbp (E28: bear-case value x tier cushion 0.80): 96.21 EUR** (band 104.03 / 96.21 / 89.45)
- stop_price 165 -- UNTOUCHED (E39)

### The g each run used (item 6)

| | base | bear | bull |
|---|---:|---:|---:|
| RESTRIKE-2026-08-26 | 8.0% | 6.0% | 11.0% |
| this run, from `reference/growth-views/SAP.DE.md` | 8.0% | 6.0% | 11.0% |

### The delta against 133.20

| step | value | item |
|---|---:|---|
| stored (RESTRIKE-2026-08-26, FY2025 basis) | 133.20 |  |
| E41 (item 3): the WINDOW -- flows R12M to 2026-06-30, OCF 9,465 and capex 735 (hand, four cumulative columns) for FY2025's 9,156 / 739; the FY2025 bridge still | 139.07 | item 3 |
| E41 (item 3): the BALANCE SHEET at 2026-06-30 -- consolidated financial liabilities 10,507 (hand), cash 10,511, other current financial assets 1,114 -> net CASH 1,118 for the 20-F's 386 (which had no current financial assets at all) | 139.69 | item 3 |
| E35.1 (item 8): pension deficit 249 (20-F, 2025-12-31, E41 annual-only) -> net cash 869 | 139.48 | item 8 |
| E40 (item 2): every tagged figure VERIFIED -- moves NOTHING, and is what makes the run ADMISSIBLE (the first re-strike was refused on 12 UNVERIFIED) | 139.48 | item 2 |
| item 6: g 8% base -- the SAME g the first re-strike used; nothing moves | 139.48 | item 6 |
| this run | 139.48 |  |

<details><summary>the run record</summary>

# section 5 run record — SAP.DE — 2026-08-26T09:00:00+02:00

**Fair value 139.48 EUR** at g 8.00%, r 9.50%.

*r 9.5% flat; non-USD bias: conservative*

- **FCF0:** 7,399,000,000 EUR

- **basis (E19):** TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 1,175,000,000 — weighted-average DILUTED count for annual FY2025 (E41: annual-only, year-end 2025-12-31 inside the window), NOT the flows' own window TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2 -- the count the 20-F states, taken under E41 because no interim states the window's, as of 2025-12-31; memo (E38, never the divisor): — |
| 2 | share-based compensation | deducted, 1,331,000,000 — for annual FY2025 (E41: annual-only, year-end 2025-12-31 inside the window) |
| 3 | interest | interest paid is OUTSIDE operating cash flow, so FCF0 is already a flow to the FIRM and nothing is added back (E34). Read from: SEC XBRL companyfacts for CIK 0001000184 (SAP SE) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0001000184.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ifrs-full:InterestPaidClassifiedAsFinancingActivities [2025-01-01..2025-12-31] 20-F 0001104659-26-020058 |
| 4 | bridge | net debt -869,000,000 — CONSOLIDATED financial liabilities 10,507,000,000 BY HAND (E41: one line per side, leases and derivatives inside, split not stated -- E14's three fields stay DATA MISSING in the store) + pension deficit 249,000,000 (E35.1) - cash 10,511,000,000 - other current financial assets 1,114,000,000. Capex legs: combined BY HAND (E41): the issuer prints capex cumulatively and states no standalone quarter, so the window's figure is netted from stated cumulative columns and entered on the record with all of them named |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 8.00% from `reference/growth-views/SAP.DE.md` (2026-08-26) |
| 7 | as-of dates | flows to 2026-06-30; balance sheet 2026-06-30; share count 2025-12-31; price 2026-08-24 — **THEY DO NOT AGREE** (share count 2025-12-31 against flows to 2026-06-30), and the difference is inside the number |
| 8 | provenance | 8 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | 1,114,000,000 |
| `leases` | inside the consolidated line 10,507,000,000 -- not split (E14), and IN net debt with it (E35) |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 249,000,000 |
| `current_financial_assets` | 1,114,000,000 |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_combined` | -7.35e+08 | hand | hand | R12M to 2026-06-30 = FY2025 -739 [Quarterly Statement Q4 2025 p.19] - Q1-Q2 2025 -358 [Q2 2026 statement p.15, comparative column] + Q1-Q2 2026 -354 [Q2 2026 p.15]. Per quarter: Q3 2025 -201 (Q1-Q3 2025 -559 [Q3 2025 p.18] less Q1-Q2 2025 -358); Q4 2025 -180 (FY -739 less Q1-Q3 -559); Q1 2026 -238 [Q1 2026 p.12, STATED]; Q2 2026 -116 (Q1-Q2 -354 less Q1 -238). SAP prints 'Purchase of intangible assets and property, plant, and equipment' CUMULATIVELY and never as a standalone quarter, so the window's figure is four stated columns netted -- E19's summation read backwards -- and enters the record BY HAND (E41). EUR millions as printed, entered in whole EUR. The workbook's own R12M capex was the same 735 |
| `operating_cash_flow` | 9.465e+09 | store | VERIFIED (cross_document) | p.2 Financial Performance, Q3 2025 column: Net cash flows from operating activities 1,502 (EUR millions); the same 1,502 stands in the Q4 2025 statement's multi-quarter table, p.9; p.2 Financial Performance, Q4 2025 column: Net cash flows from operating activities 1,297 (EUR millions); FY2025 9,156 (20-F tag CashFlowsFromUsedInOperatingActivities, and p.14) less Q1-Q3 2025 7,859 (Q3 2025 statement p.13) = 1,297; p.2 Financial Performance, Q1 2026 column: Net cash flows from operating activities 3,513 (EUR millions); Q2 2026 statement p.11 Q1-Q2 2026 6,666 less its p.2 Q2 2026 3,153 = 3,513; p.2 Financial Performance, Q2 2026 column: Net cash flows from operating activities 3,153 (EUR millions); p.11 Q1-Q2 2026 6,666 less the Q1 2026 statement's p.2 3,513 = 3,153 |
| `sbc` | 1.331e+09 | store | VERIFIED (tagged) | ifrs-full:ExpenseFromEquitysettledSharebasedPaymentTransactionsInWhichGoodsOrServicesReceivedDidNotQualifyForRecognitionAsAssets [2025-01-01..2025-12-31] 20-F 0001104659-26-020058 filed 2026-02-26 |
| `diluted_weighted_average_shares` | 1.175e+09 | store | VERIFIED (tagged) | ifrs-full:AdjustedWeightedAverageShares [2025-01-01..2025-12-31] 20-F 0001104659-26-020058 filed 2026-02-26 |
| `pension_deficit` | 2.49e+08 | store | VERIFIED (tagged) | ifrs-full:RecognisedLiabilitiesDefinedBenefitPlan [as of 2025-12-31] 20-F 0001104659-26-020058 filed 2026-02-26 |
| `cash_and_equivalents` | 1.051e+10 | store | VERIFIED (same_page) | p.10 Consolidated Statements of Financial Position as at 6/30/2026: Cash and cash equivalents 10,511 (EUR millions) |
| `other_current_financial_assets` | 1.114e+09 | store | VERIFIED (same_page) | p.10 Consolidated Statements of Financial Position as at 6/30/2026, current assets: Other financial assets 1,114 (EUR millions) |
| `financial_liabilities_consolidated` | 1.051e+10 | hand | hand | Quarterly Statement Q2 2026 p.10, Consolidated Statements of Financial Position as at 6/30/2026: 'Financial liabilities' 1,966 (current) + 8,541 (non-current) = 10,507 EUR millions -- ONE consolidated line per side, leases AND derivatives inside, and no note that splits it. E14 keeps it out of the borrowing fields; E35 needs only the SUM; so it enters the record by hand (E41). For scale: at 2025-12-31 the 20-F split the same lines (2,050 + 6,021 = 8,071) into borrowings 1,600 + 4,550, leases 1,684 and 237 of derivatives and other -- the derivatives are hedges, not borrowings, and counting them understates by about 0.2-0.4 EUR a share (report A 4.1) |

*Tool commit: `Build 2 after REVIEW-4, 2026-08-26, 3189211`.*


</details>

### SAP.DE -- the framework's own output on the price (NOT a recommendation)

- price 187.20 vs fv_base 139.48: **+34.2%** -- price is ABOVE fv_base
- price 187.20 vs FV_bull 174.30: **+7.4%** -- price is ABOVE the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': FIRES** (price >= fv_base).
- **C4, 'exit when even the bull case does not beat the index': FIRES.** Expected return from 187.20 to FV_bull 174.30 is **-6.9%**; the index core's expected return is 7.0% a year (E29's anchor). C4 states no horizon: on the reading applied to MSFT (price above FV_bull, expected return negative) it fires; read as ONE year against 7.0%, the bull-case gap is BELOW the index. Which horizon C4 means is the owner's to say.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

## LIAB.ST

Store: `config/manual/LIAB.ST.yaml`. Basis **TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2** (R12M to 2026-06-30), named quarter by quarter (E41). Price: last SETTLED close **123.60 SEK** on 2026-08-24 (tool fetch, 2026-08-26 09:00 CEST).

**The store's gate refuses nothing** (E40: every figure the basis reads is VERIFIED, and its kind is printed).

- record complete: **True** (and ADMISSIBLE: E40)
- **FCF0: 1,050 SEK m**
- **fv_base (Method C, E28): 133.48 SEK**
- band across E29's +/-0.5%: 148.13 / 133.48 / 120.77
- bear (g 0.0%): **107.23**
- bull (g 4.0%): **164.12**
- implied growth g* at 123.60: **1.28%** (E28; the view was fixed on 2026-08-26 before this was solved)
- *r 9.5% flat; non-USD bias: conservative* (E37)

- **tier: 2** -- item 5, carried from pre-REVIEW-4 scoring; section 4.4 untouched by the review
- **mbp (E28: bear-case value x tier cushion 0.70): 75.06 SEK** (band 83.57 / 75.06 / 67.68)
- stop_price 112 -- UNTOUCHED (E39)

### The g each run used (item 6)

| | base | bear | bull |
|---|---:|---:|---:|
| RESTRIKE-2026-08-26 | 2.0% | 1.0% | -- |
| this run, from `reference/growth-views/LIAB.ST.md` | 2.0% | 0.0% | 4.0% |

### The delta against 137.62

| step | value | item |
|---|---:|---|
| stored (RESTRIKE-2026-08-26, hand inputs, SBC entered as a placeholder zero, borrowings split a HYPOTHESIS; struck on 77.036m shares) | 137.62 |  |
| E35.1 (item 8): pension deficit 280 -> net debt 4,497, Lindab's own | 133.98 | item 8 |
| item 7: the STORE FILE reads the page -- cash 527 (the first re-strike's 506 was Sep 30, 2025's), other interest-bearing receivables 10, borrowings 5 + 3,378 STATED (no hypothesis); Lindab's 39 of non-current interest-bearing assets omitted -> net debt 4,536 | 133.48 | item 7 |
| item 7 / E41: share count 77.036m -- FY2025's average = the R12M average to 2026-06-30 (both 77,036 thousand); the same count, nothing moves | 133.48 | item 7 |
| E36 (item 7): SBC ZERO on E25's note form (AR 2025 p.96, p.112) for the placeholder zero -- the same 0, and the run now STANDS | 133.48 | item 7 |
| item 6: g 2% base -- the same; bear 0% for the 1% the first re-strike read from the prose; bull 4% struck for the first time | 133.48 | item 6 |
| this run | 133.48 |  |

<details><summary>the run record</summary>

# section 5 run record — LIAB.ST — 2026-08-26T09:00:00+02:00

**Fair value 133.48 SEK** at g 2.00%, r 9.50%.

*r 9.5% flat; non-USD bias: conservative*

- **FCF0:** 1,050 SEK

- **basis (E19):** TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 77 — weighted-average DILUTED count for annual FY2025 (E41: annual-only, year-end 2025-12-31 inside the window), NOT the flows' own window TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2 -- the count the 20-F states, taken under E41 because no interim states the window's, as of 2025-12-31; memo (E38, never the divisor): — |
| 2 | share-based compensation | deducted, 0 — for annual FY2025 (E41: annual-only, year-end 2025-12-31 inside the window) |
| 3 | interest | interest paid is INSIDE operating cash flow, so 201 is ADDED BACK, as printed and PRE-TAX, and net debt is then subtracted ONCE (E34). The pre-tax add-back is the generous end of E34's own band. Read from: Lindab Interim Report January-June 2026 (Nasdaq release 1454549, 2026-07-17), sources/LIAB.ST_2026-Q2_half-year-financial-report_2026-07-17_en_a0.pdf p.17, consolidated cash flow statement, OPERATING ACTIVITIES: 'Interest received 1 3 2 5 10 13' and 'Interest paid -48 -52 -98 -107 -211 -220' (Apr-Jun 2026, Apr-Jun 2025, Jan-Jun 2026, Jan-Jun 2025, R12M, Jan-Dec 2025) ABOVE 'Cash flow from operating activities before changes in working capital' |
| 4 | bridge | net debt 4,536 — borrowings 5 + 3,378 + leases 1,410 (E35: always in) + pension deficit 280 (E35.1) - cash 527 - other current financial assets 10. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: split: capex_ppe + capex_intangibles, as the accounts print them |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 2.00% from `reference/growth-views/LIAB.ST.md` (2026-08-26) |
| 7 | as-of dates | flows to 2026-06-30; balance sheet 2026-06-30; share count 2025-12-31; price 2026-08-24 — **THEY DO NOT AGREE** (share count 2025-12-31 against flows to 2026-06-30), and the difference is inside the number |
| 8 | provenance | 12 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | 10 |
| `leases` | 1,410 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 280 |
| `current_financial_assets` | 10 |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_ppe` | -185 | store | VERIFIED (same_page) | p.13, cash flow statement, INVESTING ACTIVITIES, Jul-Sep 2025 column: 'Investments in tangible fixed assets -50'; p.13, cash flow statement, INVESTING ACTIVITIES, Oct-Dec 2025 column: 'Investments in tangible fixed assets -47'; p.15, cash flow statement, INVESTING ACTIVITIES, Jan-Mar 2026 column: 'Investments in tangible fixed assets -43'; p.17, cash flow statement, INVESTING ACTIVITIES, Apr-Jun 2026 column: 'Investments in tangible fixed assets -45'; R12M column -185 = 50 + 47 + 43 + 45 |
| `capex_intangibles` | -142 | store | VERIFIED (same_page) | p.13, cash flow statement, INVESTING ACTIVITIES, Jul-Sep 2025 column: 'Investments in intangible assets -31'; p.13, cash flow statement, INVESTING ACTIVITIES, Oct-Dec 2025 column: 'Investments in intangible assets -41'; p.15, cash flow statement, INVESTING ACTIVITIES, Jan-Mar 2026 column: 'Investments in intangible assets -27'; p.17, cash flow statement, INVESTING ACTIVITIES, Apr-Jun 2026 column: 'Investments in intangible assets -43'; R12M column -142 = 31 + 41 + 27 + 43 |
| `operating_cash_flow` | 1,176 | store | VERIFIED (cross_document) | p.13, consolidated cash flow statement, Jul-Sep 2025 column: 'Cash flow from operating activities 335'; Q2 2026 report p.19 quarterly table restates 335; p.13, consolidated cash flow statement, Oct-Dec 2025 column: 'Cash flow from operating activities 521'; Q2 2026 report p.19 quarterly table restates 521; p.15, consolidated cash flow statement, Jan-Mar 2026 column: 'Cash flow from operating activities 45'; Q2 2026 report p.19 quarterly table restates 45; p.17, consolidated cash flow statement, Apr-Jun 2026 column: 'Cash flow from operating activities 275'; p.19 quarterly table 275; the R12M column 1,176 = 335 + 521 + 45 + 275 |
| `sbc` | 0 | store | VERIFIED (same_page) | p.96, Incentive program: the long-term incentive programmes 2023-2025 are 'long-term variable cash remuneration ... presumed to be invested in shares or share related instruments in Lindab Group on market terms' (cash, not IFRS 2 equity-settled); p.112, share option programme: 'The program is thus based on a market transaction with related parties, and no part of the program should be seen as share-based remuneration' |
| `net_interest_paid` | 201 | store | VERIFIED (same_page) | E18: finance_costs_paid - finance_income_received, both on TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2 |
| `diluted_weighted_average_shares` | 77.04 | store | VERIFIED (cross_document) | p.18, five-year table, Jan-Dec 2025 column: 'Average number of shares outstanding R12M, thousands 77,036'; Q2 2026 interim p.20, Jan-Jun 2026 column, R12M average 77,036 |
| `financial_liabilities_current` | 5 | store | VERIFIED (same_page) | p.15, consolidated balance sheet, Jun 30, 2026, current liabilities: 'Other interest-bearing liabilities 5'; net debt note p.25 'Current interest-bearing liabilities 397' = this 5 + current lease liabilities 392 |
| `financial_liabilities_noncurrent` | 3,378 | store | VERIFIED (same_page) | p.15, consolidated balance sheet, Jun 30, 2026, non-current liabilities: 'Liabilities to credit institutions 3,378'; net debt note p.25 restates 3,378. BORROWINGS ALONE (E14): leases and pensions are separate lines |
| `lease_liabilities` | 1,410 | store | VERIFIED (same_page) | p.25, net debt note, Jun 30, 2026: 'Lease liabilities -1,410' -- the STATED TOTAL (E26); the balance sheet p.15 presents it as non-current 1,018 + current 392 and never totals it there |
| `pension_deficit` | 280 | store | VERIFIED (same_page) | p.15, consolidated balance sheet, Jun 30, 2026, non-current liabilities: 'Provisions for pensions and similar obligations 280'; net debt note p.25: 'Non-current interest-bearing provisions for pensions and similar obligations 280' and 'Pension-related liabilities -280' |
| `cash_and_equivalents` | 527 | store | VERIFIED (same_page) | p.15, consolidated balance sheet, Jun 30, 2026: 'Cash and cash equivalents 527'; net debt note p.25 restates 527. NOT the 506 the first re-strike used, which is Sep 30, 2025's figure |
| `other_current_financial_assets` | 10 | store | VERIFIED (same_page) | p.15, consolidated balance sheet, Jun 30, 2026, current assets: 'Other interest-bearing receivables 10'; net debt note p.25 restates 10 |

*Tool commit: `Build 2 after REVIEW-4, 2026-08-26, 3189211`.*


</details>


---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp stay as item 4 and item 5 left them (null / 1 and 2 / null).
- **It does not link the records.** `run_record:` on each entry, with the fv_base beside it, is the owner's write; until then `vss run` prints DATA MISSING for both fair values (item 9), which is the rule working.
- **SAP.DE stands on two HAND inputs** the store cannot hold -- the R12M capex (four cumulative columns) and the consolidated financial-liabilities line -- both declared in the record with their pages (E41). Whether either may live in the store is open.
- **The share counts are E41 fills**: SAP's 1,175m is FY2025's (the interim states 1,163m diluted for H1 2026 and 1,158m for Q2 2026; the R12M average is not stated), Lindab's 77.036m is FY2025's and equals the R12M average the interim states. The as-of line says THEY DO NOT AGREE for SAP, and that is inside the number.
