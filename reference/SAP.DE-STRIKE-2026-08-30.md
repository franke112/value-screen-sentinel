# SAP.DE -- struck from the store, end to end, 2026-08-30 21:59 CEST

**2026-08-30 21:59 CEST. `config/watchlist.yaml` IS NOT WRITTEN by this tool** -- the owner writes it from this printout with a dated backup beside it. The record is written to `reference/run-records/SAP.DE-2026-08-30.json`.

The prior record (`reference/run-records/SAP.DE-2026-08-26.json`, RESTRIKE-2026-08-26-b) replayed to 139.48 but the store could not rebuild it -- capex -735 and the consolidated borrowing line 10,507 were HAND inputs -- and **E87 nulled `fv_base`, `tier` and the derived MBP** on 2026-08-30. This strike runs under E84/E89 (ex-lease borrowing operands), E85 (NOT PRESENTED legs), E86 (capex from stated cumulative columns), E88 (the divisor is E41's annual diluted average; the E80 pair stays memo), after the owner's read-back of all fifteen 2026-08-30 entries the same evening.

Growth view: `reference/growth-views/SAP.DE.md`, registered by the owner 2026-08-26 (RULED A, Build 2 item 6) -- base 8%, bear 6%, bull 11% -- UNCHANGED (E28).

Tool: `tools/strike_sap_2026_08_30.py` at `SAP.DE strike, 2026-08-30, 8c3ac21`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

**BASIS: `TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2` -- the four consecutive quarters, the twelve months ending 2026-06-30** (E19, named quarter by quarter under E41). Store: `config/manual/SAP.DE.yaml`, money in whole EUR. Price: last SETTLED close **189.88 EUR** on 2026-08-27 (tool fetch, 2026-08-30 21:59 CEST).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED (E40), confirmed one at a time at the owner's read-back of 2026-08-30.

- record complete: **True**, with **ZERO hand inputs** -- every leg formed off the store; the eight declarations and declaration 3.1 (E70) are in the record below
- **FCF0: 7,399 EUR m** -- interest NOT in operating cash flow (E34: the filer classifies interest paid/received OUTSIDE operating activities from January 2025, `interest_in_ocf: no` -- no add-back), capex the CODE'S difference of E86's stated cumulative columns (-201, -180, -238, -116 = -735), equity-settled SBC 1,331 deducted (E36, E41 annual fill). Prior record: 7,399 EUR m -- the same figure, now formed without a hand input.
- **lease treatment (E70, declaration 3.1): the flow did NOT bear the lease principal** -- IFRS 16.50(b), `operating_leases_in_ocf: no`; the 1,735 EUR m lease total (note (E.2), p.39) sits in net debt and nothing is added back.
- **net CASH: 869 EUR m** -- borrowings 1,685,000,000 + 7,087,000,000 + leases 1,735,000,000 (E35: always in; finance leases beside operating, E65) + pension deficit 249,000,000 (E35.1) + asset retirement obligations 0 (E68) + prepaid delivery obligations 0 (E81) - cash 10,511,000,000 - other current financial assets 1,114,000,000. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). NOT PRESENTED (E85), entered at nil on a recorded search: asset_retirement_obligation, prepaid_delivery_obligation. Prior record: 869 EUR m -- the same bridge, now off the store: E84's ex-lease operands (1,478 + 207 / 6,726 + 361), the lease total 1,735, pension 249, E85's NOT PRESENTED ARO and prepaid legs at nil on recorded searches, cash 10,511 and other current financial assets 1,114.
- **divisor (E88): 1,175,000,000** -- FY2025's weighted-average diluted count under E41's annual-only rule, dated 2025-12-31, the basis mismatch (annual average against R12M flows) FLAGGED in declaration 1; the E80 pair at 6/30/2026 (1,228.5m - 74.3m = 1,154.2m) stays MEMO, never the divisor.

- **fv_base (Method C, E28): 139.48 EUR** (prior 139.48: +0.00%)
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **151.17 / 139.48 / 129.38 EUR** (prior 151.17 / 139.48 / 129.38)
- bear (g 6.0%): **120.27 EUR** (prior 120.27)
- bull (g 11.0%): **174.30 EUR** (prior 174.30)
- implied growth g* at the settled close 189.88 EUR: **12.15%** (E28; the view was fixed 2026-08-26, before any fair value and before g* -- UNCHANGED here)
- *r 9.5% flat; non-USD bias: conservative* (E37)

- **tier 1 (carried; section 4.4 NOT re-scored -- E77's one-tier-stricter applies at the next re-score, catalyst 2026-10-21). MBP (E28): 96.21 EUR** = bear 120.27 x 0.80 (band r 9.0% 104.03 / r 10.0% 89.45). Price 189.88 is +97.4% against it. stop_price null (sold 2026-08-26, E42) -- UNTOUCHED.

## The run record, in full -- every declaration and every bridge leg named

# section 5 run record — SAP.DE — 2026-08-30T21:59:16+02:00

**Fair value 139.48 EUR** at g 8.00%, r 9.50%.

*r 9.5% flat; non-USD bias: conservative*

- **FCF0:** 7,399,000,000 EUR whole

- **basis (E19):** TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2

- **units:** money stated in whole, the count in whole; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 1,175,000,000 — weighted-average DILUTED count for annual FY2025 (E41: annual-only, year-end 2025-12-31 inside the window), NOT the flows' own window TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2 -- E88: an ANNUAL average divides twelve months of flows ending 2026-06-30, the basis mismatch flagged, taken under E41's annual-only rule because no window average exists and a window-end count is never promoted, as of 2025-12-31; divisor basis `weighted_average` (E75 / E75.1 / E88); memo (E38, never the divisor): — |
| 2 | share-based compensation | deducted, 1,331,000,000 — for annual FY2025 (E41: annual-only, year-end 2025-12-31 inside the window) |
| 3 | interest | interest paid is OUTSIDE operating cash flow, so FCF0 is already a flow to the FIRM and nothing is added back (E34). Read from: SEC XBRL companyfacts for CIK 0001000184 (SAP SE) -- https://data.sec.gov/api/xbrl/companyfacts/CIK0001000184.json. The filing each figure came out of is named on the figure itself, with its tag and context period. ifrs-full:InterestPaidClassifiedAsFinancingActivities [2025-01-01..2025-12-31] 20-F 0001104659-26-020058 |
| 3.1 | lease principal (E70) | the operating cash flow does NOT bear the lease principal (IFRS 16.50(b): in financing), so nothing is added back -- the lease is charged once, in net debt (E35, E65, E70). Read from: FRAMEWORK-EDITS E70, applied 2026-08-30 to an IFRS 16 filer IFRS 16.50(b): a lessee classifies cash payments for the principal portion of the lease liability within FINANCING activities, so this filer's `operating_cash_flow` never bore the principal; the interest portion follows the filer's IAS 7 policy, which `interest_in_ocf` records. The standard leaves no choice on the principal |
| 4 | bridge | net debt -869,000,000 — borrowings 1,685,000,000 + 7,087,000,000 + leases 1,735,000,000 (E35: always in; finance leases beside operating, E65) + pension deficit 249,000,000 (E35.1) + asset retirement obligations 0 (E68) + prepaid delivery obligations 0 (E81) - cash 10,511,000,000 - other current financial assets 1,114,000,000. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). NOT PRESENTED (E85), entered at nil on a recorded search: asset_retirement_obligation, prepaid_delivery_obligation. Capex legs: combined: capex_combined, the one line the issuer prints |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 8.00% from `reference/growth-views/SAP.DE.md` (2026-08-26) |
| 7 | as-of dates | flows to 2026-06-30; balance sheet 2026-06-30; share count 2025-12-31; price 2026-08-27 — **THEY DO NOT AGREE** (share count 2025-12-31 against flows to 2026-06-30), and the difference is inside the number |
| 8 | provenance | 12 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | 1,114,000,000 |
| `leases` | 1,735,000,000 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 249,000,000 |
| `current_financial_assets` | 1,114,000,000 |
| `asset_retirement_obligations` | 0 (stated) |
| `prepaid_delivery_obligations` | 0 (stated) |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_combined` | -7.35e+08 | store | VERIFIED (cross_document/same_page) | E86: -559,000,000 [sap-q32025.pdf p.13, Consolidated Statements of Cash Flows, Q1-Q3 2025 column: 'Purchase of intangible assets and property, plant, and equipment -559' (EUR millions); the same -559 on p.18, free cash flow reconciliation] - -358,000,000 [sap-q22025.pdf p.13, Consolidated Statements of Cash Flows, Q1-Q2 2025 column: 'Purchase of intangible assets and property, plant, and equipment -358' (EUR millions); the same -358 on p.18, and restated as the comparative column in sap-q22026.pdf p.15] = -201,000,000 -- the difference is the code's, both columns printed; E86: -739,000,000 [sap-q42025.pdf p.14, Consolidated Statements of Cash Flows, Q1-Q4 2025 column: 'Purchase of intangible assets and property, plant, and equipment -739' (EUR millions); the same -739 on p.19; the 20-F tags the year as ifrs-full:PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwill... -739,000,000 (annual FY2025 entry below)] - -559,000,000 [sap-q32025.pdf p.13, Consolidated Statements of Cash Flows, Q1-Q3 2025 column: 'Purchase of intangible assets and property, plant, and equipment -559' (EUR millions); the same -559 on p.18] = -180,000,000 -- the difference is the code's, both columns printed; sap-q12026.pdf p.9, Consolidated Statements of Cash Flows, Q1 2026 column: 'Purchase of intangible assets and property, plant, and equipment -238' (EUR millions); the same -238 on p.12, free cash flow reconciliation; E86: -354,000,000 [sap-q22026.pdf p.11, Consolidated Statements of Cash Flows, Q1-Q2 2026 column: 'Purchase of intangible assets and property, plant, and equipment -354' (EUR millions); the same -354 on p.15; restated in the Half-Year Report 2026 (sources/sap-2026-half-year-report.pdf) p.27 and p.46] - -238,000,000 [sap-q12026.pdf p.9, Consolidated Statements of Cash Flows, Q1 2026 column: 'Purchase of intangible assets and property, plant, and equipment -238' (EUR millions); the same -238 on p.12] = -116,000,000 -- the difference is the code's, both columns printed |
| `operating_cash_flow` | 9.465e+09 | store | VERIFIED (cross_document) | p.2 Financial Performance, Q3 2025 column: Net cash flows from operating activities 1,502 (EUR millions); the same 1,502 stands in the Q4 2025 statement's multi-quarter table, p.9; p.2 Financial Performance, Q4 2025 column: Net cash flows from operating activities 1,297 (EUR millions); FY2025 9,156 (20-F tag CashFlowsFromUsedInOperatingActivities, and p.14) less Q1-Q3 2025 7,859 (Q3 2025 statement p.13) = 1,297; p.2 Financial Performance, Q1 2026 column: Net cash flows from operating activities 3,513 (EUR millions); Q2 2026 statement p.11 Q1-Q2 2026 6,666 less its p.2 Q2 2026 3,153 = 3,513; p.2 Financial Performance, Q2 2026 column: Net cash flows from operating activities 3,153 (EUR millions); p.11 Q1-Q2 2026 6,666 less the Q1 2026 statement's p.2 3,513 = 3,153 |
| `sbc` | 1.331e+09 | store | VERIFIED (tagged) | ifrs-full:ExpenseFromEquitysettledSharebasedPaymentTransactionsInWhichGoodsOrServicesReceivedDidNotQualifyForRecognitionAsAssets [2025-01-01..2025-12-31] 20-F 0001104659-26-020058 filed 2026-02-26 |
| `diluted_weighted_average_shares` | 1.175e+09 | store | VERIFIED (tagged) | ifrs-full:AdjustedWeightedAverageShares [2025-01-01..2025-12-31] 20-F 0001104659-26-020058 filed 2026-02-26 |
| `financial_liabilities_current` | 1.685e+09 | store | VERIFIED (same_page) | Half-Year Report 2026 (sources/sap-2026-half-year-report.pdf), note (E.2) Liquidity, p.39, 6/30/2026 carrying amounts, current column: 'Financial debt 1,478' + 'Other financial liabilities 207' (EUR millions) = 1,685, the stated operands of the note's 'Financial liabilities 1,966' less its 'Lease liabilities 281' (E84 / E71: financial liabilities ex-leases; the issuer presents the operands inside one line on the balance sheet p.25 and totals them here). Financial debt is bonds 980 + commercial paper 498 (private placements 0, bank loans 0) |
| `financial_liabilities_noncurrent` | 7.087e+09 | store | VERIFIED (same_page) | Half-Year Report 2026, note (E.2) Liquidity, p.39, 6/30/2026 carrying amounts, non-current column: 'Financial debt 6,726' + 'Other financial liabilities 361' (EUR millions) = 7,087, the stated operands of the note's 'Financial liabilities 8,541' less its 'Lease liabilities 1,454' (E84 / E71). Financial debt is bonds 6,726 alone |
| `lease_liabilities` | 1.735e+09 | store | VERIFIED (same_page) | Half-Year Report 2026, note (E.2) Liquidity, p.39, 6/30/2026: 'Lease liabilities 281 (current) 1,454 (non-current) 1,735 (total)' (EUR millions) -- the stated total (E26 satisfied); presented inside 'Financial liabilities' on the balance sheet p.25 |
| `pension_deficit` | 2.49e+08 | store | VERIFIED (tagged) | ifrs-full:RecognisedLiabilitiesDefinedBenefitPlan [as of 2025-12-31] 20-F 0001104659-26-020058 filed 2026-02-26 |
| `asset_retirement_obligation` | 0 | store | NOT PRESENTED (E85) | NOT PRESENTED (E85: searched SAP Half-Year Report 2026 (sources/sap-2026-half-year-report.pdf, 50 pages, approved 2026-07-22) (all 50 pages by text search: the statement of financial position p.25 and every note A.1-G.4; the terms 'asset retirement', 'decommissioning', 'restoration' and 'dilapidation' occur nowhere (reports/E41-SAP-2026-08-30.md, addendum section 4)) on 2026-08-30) -- Half-Year Report 2026 p.25, Consolidated Statement of Financial Position at 6/30/2026, liabilities presented: 'Provisions 119' (current) and '611' (non-current), undecomposed; no provisions note exists in the report (contents p.2-3: notes A.1-A.2, B.1-B.3, C.1-C.3, D.1-D.3, E.1-E.2, F.1, G.1-G.4). The 20-F tags CurrentProvisions 537 / NoncurrentProvisions 550 at 12/31/2025 and no decommissioning element |
| `prepaid_delivery_obligation` | 0 | store | NOT PRESENTED (E85) | NOT PRESENTED (E85: searched SAP Half-Year Report 2026 (sources/sap-2026-half-year-report.pdf, 50 pages, approved 2026-07-22) (all 50 pages by text search: p.25 and every note A.1-G.4; no note on contract liabilities exists (the only other mention is the cash-flow line 'Increase/decrease in contract liabilities 2,990', p.27) and 'prepay' occurs nowhere (reports/E41-SAP-2026-08-30.md, addendum section 4)) on 2026-08-30) -- Half-Year Report 2026 p.25, Consolidated Statement of Financial Position at 6/30/2026, liabilities presented: trade and other payables 2,747 / 1, tax liabilities 1,359 / 670, financial liabilities 1,966 / 8,541, other non-financial liabilities 3,699 / 456, provisions 119 / 611, deferred tax liabilities 211, contract liabilities 9,843 / 136 -- no streaming, prepaid-offtake or prepaid-delivery caption; the contract liabilities are subscriptions billed in advance, E81's ordinary kind (the RMV.L and EXE precedents), named here and not this leg |
| `cash_and_equivalents` | 1.051e+10 | store | VERIFIED (same_page) | p.10 Consolidated Statements of Financial Position as at 6/30/2026: Cash and cash equivalents 10,511 (EUR millions) |
| `other_current_financial_assets` | 1.114e+09 | store | VERIFIED (same_page) | p.10 Consolidated Statements of Financial Position as at 6/30/2026, current assets: Other financial assets 1,114 (EUR millions) |

*Tool commit: `SAP.DE strike, 2026-08-30, 8c3ac21`.*


### SAP.DE -- the framework's own output on the price (NOT a recommendation)

- price 189.88 EUR vs fv_base 139.48 EUR: **+36.1%** -- price is ABOVE fv_base
- price 189.88 EUR vs FV_bull 174.30 EUR: **+8.9%** -- price is ABOVE the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': FIRES** (price >= fv_base). A trim presupposes a position; none is held -- the position was SOLD 2026-08-26 under C4 (E42, fourth application).
- **C4, 'exit when even the bull case does not beat the index': FIRES.** Expected return from 189.88 to FV_bull 174.30 is **-8.2%**; the index core's expected return is 7.0% a year (E29's anchor). A sale presupposes a position; none is held. The WATCH-PRICED entry's re-entry line is the MBP below.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** The owner writes fv_base and tier from this printout; `mbp` is derived by the tool (E28), never written by hand.
- **It does not touch the growth view** -- base 8%, bear 6%, bull 11% are the registered ones (2026-08-26).
- **It does not re-score tier.** Tier 1 is carried as the owner ruled it 2026-08-26 (RULED A, Build 2 item 5); no E76 reading is on file, and E77 applies one tier stricter at the next section 4.4 re-score.
- **It does not authorise a purchase or a sale.** S0 rule 4 stands.

*Replay check: `SAP.DE-2026-08-30.json` reloaded and replayed to 139.48 EUR -- the same figure.*
