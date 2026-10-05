# LIAB.ST -- re-struck under E34, E35/E35.1, E65-E68, E70, 2026-08-30 10:26 CEST

**2026-08-30 10:26 CEST.** The prior record (`reference/run-records/LIAB.ST-2026-08-26.json`, RESTRIKE-2026-08-26-b) already stood under E34 and E35/E35.1; the rulings since -- E65-E68 and E70 -- are applied here off the store file as it stands, and the record is written to `reference/run-records/LIAB.ST-2026-08-30.json`. `config/watchlist.yaml` is the OWNER'S write, made by hand from this printout with a dated backup beside it.

Growth view: `reference/growth-views/LIAB.ST.md`, registered by the owner 2026-08-26 -- base 2% (Euroconstruct's ~2%/yr to 2028), bear 0%, bull 4% -- UNCHANGED (E28).

Tool: `tools/restrike_liab_2026_08_30.py` at `LIAB.ST re-strike, 2026-08-30, 9c9eed3`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

**BASIS: `TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2` -- the four consecutive quarters 2025-Q3, 2025-Q4, 2026-Q1 and 2026-Q2, the twelve months ending 2026-06-30** (E19, named quarter by quarter under E41). Store: `config/manual/LIAB.ST.yaml`, money in millions of SEK. Price: last SETTLED close **131.60 SEK** on 2026-08-27 (tool fetch, 2026-08-30 10:26 CEST).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED (E40).

- record complete: **True** -- the eight declarations and declaration 3.1 (E70)
- **FCF0: 1,050 SEK m** -- interest INSIDE operating cash flow (E34): net interest paid 201 SEK m (paid 211 - received 10, R12M, Q2 2026 interim p.17) ADDED BACK, pre-tax, and net debt subtracted once. Prior record: 1,050 SEK m -- the same.
- **lease treatment (E70, declaration 3.1): the flow did NOT bear the lease principal** -- `no`, IFRS 16.50(b): principal repayments are FINANCING outflows, so `operating_cash_flow` never charged the 1,410 SEK m lease liability that net debt carries; nothing is added back, FCF0 before = after = 1,050 SEK m. The interest portion sits inside the 211 of interest paid and follows E34 above. For this IFRS filer E70 changes NOTHING and is DECLARED.
- **net debt: 4,536 SEK m** -- borrowings 5 + 3,378 + leases 1,410 (E35: always in; finance leases beside operating, E65) + pension deficit 280 (E35.1) + asset retirement obligations 0 (E68) - cash 527 - other current financial assets 10. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Prior record: 4,536 SEK m -- the same total; E65 names the finance leases as inside the stated lease total, E66/E67 the two borrowing captions (5 current + 3,378 non-current), E68 the asset-retirement leg at 0 (E68.1 caption zero) -- legs NAMED, nothing MOVED.

- **fv_base (Method C, E28): 133.48 SEK** (prior 133.48: +0.00%)
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **148.13 / 133.48 / 120.77 SEK** (prior 148.13 / 133.48 / 120.77)
- bear (g 0.0%): **107.23 SEK** (prior 107.23)
- bull (g 4.0%): **164.12 SEK** (prior 164.12)
- implied growth g* at the settled close 131.60 SEK: **1.87%** (E28; the view was fixed 2026-08-26, before any fair value and before g* -- UNCHANGED here)
- *r 9.5% flat; non-USD bias: conservative* (E37)

- **tier 2 (carried; section 4.4 NOT re-scored). MBP (E28): 75.06 SEK** = bear 107.23 x 0.70 (band r 9.0% 83.57 / r 10.0% 67.68). Price 131.60 is +75.3% against it. stop_price 112 -- UNTOUCHED.

## The run record, in full -- every declaration and every bridge leg named

# section 5 run record — LIAB.ST — 2026-08-30T10:26:29+02:00

**Fair value 133.48 SEK** at g 2.00%, r 9.50%.

*r 9.5% flat; non-USD bias: conservative*

- **FCF0:** 1,050 SEK millions

- **basis (E19):** TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2

- **units:** money stated in millions, the count in millions; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 77.036 millions — weighted-average DILUTED count for annual FY2025 (E41: annual-only, year-end 2025-12-31 inside the window), NOT the flows' own window TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2 -- the count the 20-F states, taken under E41 because no interim states the window's, as of 2025-12-31; memo (E38, never the divisor): — |
| 2 | share-based compensation | deducted, 0 — for annual FY2025 (E41: annual-only, year-end 2025-12-31 inside the window) |
| 3 | interest | interest paid is INSIDE operating cash flow, so 201 is ADDED BACK, as printed and PRE-TAX, and net debt is then subtracted ONCE (E34). The pre-tax add-back is the generous end of E34's own band. Read from: Lindab Interim Report January-June 2026 (Nasdaq release 1454549, 2026-07-17), sources/LIAB.ST_2026-Q2_half-year-financial-report_2026-07-17_en_a0.pdf p.17, consolidated cash flow statement, OPERATING ACTIVITIES: 'Interest received 1 3 2 5 10 13' and 'Interest paid -48 -52 -98 -107 -211 -220' (Apr-Jun 2026, Apr-Jun 2025, Jan-Jun 2026, Jan-Jun 2025, R12M, Jan-Dec 2025) ABOVE 'Cash flow from operating activities before changes in working capital' |
| 3.1 | lease principal (E70) | the operating cash flow does NOT bear the lease principal (IFRS 16.50(b): in financing), so nothing is added back -- the lease is charged once, in net debt (E35, E65, E70). Read from: FRAMEWORK-EDITS E70, applied 2026-08-30 to an IFRS 16 filer IFRS 16.50(b): a lessee classifies cash payments for the principal portion of the lease liability within FINANCING activities, so this filer's `operating_cash_flow` never bore the principal; the interest portion follows the filer's IAS 7 policy, which `interest_in_ocf` records. The standard leaves no choice on the principal |
| 4 | bridge | net debt 4,536 — borrowings 5 + 3,378 + leases 1,410 (E35: always in; finance leases beside operating, E65) + pension deficit 280 (E35.1) + asset retirement obligations 0 (E68) - cash 527 - other current financial assets 10. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: split: capex_ppe + capex_intangibles, as the accounts print them |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 2.00% from `reference/growth-views/LIAB.ST.md` (2026-08-26) |
| 7 | as-of dates | flows to 2026-06-30; balance sheet 2026-06-30; share count 2025-12-31; price 2026-08-27 — **THEY DO NOT AGREE** (share count 2025-12-31 against flows to 2026-06-30), and the difference is inside the number |
| 8 | provenance | 13 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | 10 |
| `leases` | 1,410 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 280 |
| `current_financial_assets` | 10 |
| `asset_retirement_obligations` | 0 (stated) |

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
| `asset_retirement_obligation` | 0 | store | VERIFIED (same_page) | Consolidated statement of financial position, p.74: provisions presented are 'Provisions for pensions and similar obligations' (note 26; 265) and 'Other provisions' (note 27; non-current 13, current 235) -- no decommissioning, restoration, dismantling or environmental provision is presented. Note 27 Other provisions, p.115: 'Restructuring reserve 167', 'Warranty provision 5', 'Other 76', 'Total 248'; 'Other provisions amounted to SEK 76 m (10)', not further described -- a caption with room (E25), named here. No such provision is named anywhere in the report (full-text search of the annual report, 2026-08-29). E68.1: the absence is evidence for this business. |
| `cash_and_equivalents` | 527 | store | VERIFIED (same_page) | p.15, consolidated balance sheet, Jun 30, 2026: 'Cash and cash equivalents 527'; net debt note p.25 restates 527. NOT the 506 the first re-strike used, which is Sep 30, 2025's figure |
| `other_current_financial_assets` | 10 | store | VERIFIED (same_page) | p.15, consolidated balance sheet, Jun 30, 2026, current assets: 'Other interest-bearing receivables 10'; net debt note p.25 restates 10 |

*Tool commit: `LIAB.ST re-strike, 2026-08-30, 9c9eed3`.*


### LIAB.ST -- the framework's own output on the price (NOT a recommendation)

- price 131.60 SEK vs fv_base 133.48 SEK: **-1.4%** -- price is BELOW fv_base
- price 131.60 SEK vs FV_bull 164.12 SEK: **-19.8%** -- price is BELOW the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': does not fire** (price < fv_base).
- **C4, 'exit when even the bull case does not beat the index': does not fire.** Expected return from 131.60 to FV_bull 164.12 is **+24.7%**; the index core's expected return is 7.0% a year (E29's anchor). C4 states no horizon: on the reading applied to MSFT, UNA.AS and SAP.DE (price above/below FV_bull, expected return positive or negative) it does not fire outright here since price is below FV_bull; read as ONE year against 7.0%, the bull-case gap is ABOVE the index. Which horizon C4 means is the owner's to say.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It does not touch the growth view** -- base 2%, bear 0%, bull 4% are the registered ones.
- **It does not re-score tier.** Tier 2 is carried as the owner ruled it 2026-08-26 (RULED A, Build 2 item 5).
- **It does not touch stop_price.** 112 stands (E39: a stop is about the loss, not the worth).
- **It does not authorise a purchase or a sale.** S0 rule 4 stands.
