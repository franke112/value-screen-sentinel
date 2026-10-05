# AUTO.L -- first section 5 strike on the tool path, 2026-08-27

**2026-08-27 22:07 BST. `config/watchlist.yaml` IS NOT WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a stop.** The section 5 run record is written to `reference/run-records/AUTO.L-2026-08-27.json` so that linking it to a watchlist entry (`run_record:`) remains the owner's write.

Growth view: `reference/growth-views/AUTO.L.md`, pre-registered by the owner 2026-08-27, BEFORE this script ran and before g* was solved (E28's binding order).

Tool: `tools/strike_auto_l_2026_08_27.py` at `AUTO.L first strike, 2026-08-27, d179600`. r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year discounting.

# AUTO.L -- section 5 strike, 2026-08-27 22:07 BST

Store: `config/manual/AUTO.L.yaml`. **BASIS: `2026-FY`, the twelve months ending 2026-03-31** (E19). Price: last SETTLED close **536.20 GBX** (5.36 GBP at 100:1) on 2026-08-27 (tool fetch, 2026-08-27 22:07 BST).

**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure the basis reads is VERIFIED; six remain UNVERIFIED but unread at this basis (E21, E60), named below.

| Figure | Value | Why it does not block |
|---|---:|---|
| `finance_costs_paid` | 2.8 | section 5 does not read `finance_costs_paid` on this file: it is DECLARED 5.1C, but `interest_in_ocf: no` -- operating cash flow is already pre-interest, and FCF0 adds nothing back (FRAMEWORK-EDITS E34, E60) |
| `income_tax_paid` | -95.2 | section 5 does not read `income_tax_paid` on this file: it is DECLARED 5.1C, but no live code path ever resolves it -- not a leg of any ratio and not a parameter of FCF0 (FRAMEWORK-EDITS E60) |
| `net_ppe` | 73 | section 5 does not read `net_ppe` at all: it is read by rank, and no method of section 5 touches it |
| `op_margin` | 0.63 | section 5 does not read `op_margin` at all: it is read by check, and no method of section 5 touches it |
| `proceeds_from_disposals_ppe` | 4.5 | section 5 does not read `proceeds_from_disposals_ppe` on this file: it is DECLARED 5.1C, but no live code path ever resolves it -- not a leg of any ratio and not a parameter of FCF0 (FRAMEWORK-EDITS E60) |
| `revenue_yoy` | 0.04 | section 5 does not read `revenue_yoy` at all: it is read by check, and no method of section 5 touches it |

- record complete: **True**
- **FCF0: 286 GBP m** (interest_in_ocf: no -- nothing added back, E34)

- **fv_base (Method C, E28): 4.82 GBP**
- band across E29's +/-0.5% (r 9.0% / 9.5% / 10.0%): **5.21 / 4.82 / 4.48 GBP**
- bear (g 0.0%): **3.83 GBP**
- bull (g 6.0%): **6.08 GBP**
- implied growth g* at the settled close 5.36 GBP: **4.37%** (E28; the view in `reference/growth-views/AUTO.L.md` was fixed 2026-08-27, before this was solved)
- *r 9.5% flat; non-USD bias: conservative* (E37)

- **tier: NOT SCORED.** Section 4.4 has not scored AUTO.L, so E28's MBP -- the bear-case value times the tier cushion -- has no tier to apply. **MBP is not struck here; this is DATA MISSING, not a computed absence.**

<details><summary>the run record</summary>

# section 5 run record — AUTO.L — 2026-08-27T22:07:10+01:00

**Fair value 4.82 GBP** at g 3.00%, r 9.50%.

*r 9.5% flat; non-USD bias: conservative*

- **FCF0:** 286 GBP millions

- **basis (E19):** 2026-FY

- **units:** money stated in millions, the count in thousands; the division normalises both to whole units on the store's declaration

## The eight declarations

| # | declaration | this run |
|---|---|---|
| 1 | share-count basis | 862,666.250 thousands — weighted-average DILUTED count for 2026-FY, the same window as the flows (E38), as of 2026-03-31; memo (E38, never the divisor): — |
| 2 | share-based compensation | deducted, 9 |
| 3 | interest | interest paid is OUTSIDE operating cash flow, so FCF0 is already a flow to the FIRM and nothing is added back (E34). Read from: Annual Report and Financial Statements 2026 (audited) p.105, consolidated statement of cash flows: 'Payment of interest on borrowings 31 (2.8)' sits inside Cash flows from FINANCING activities, and 'Interest received on cash and cash equivalents 1.3' sits inside Cash flows from INVESTING activities -- both OUTSIDE 'Net cash generated from operating activities 322.8', which is computed from 'Cash generated from operations 418.0' less 'Income taxes paid (95.2)' alone, with no interest line in operating activities at all |
| 4 | bridge | net debt 188 — borrowings 0 + 163 + leases 43 (E35: always in) + pension deficit 0 (E35.1) - cash 18 - other current financial assets DATA MISSING, so nothing is subtracted for them: omitting an ASSET raises net debt and lowers the value, which is the safe direction. No NCI, associate, preferred or convertible leg exists in this schema (E35); a separately presented pension ASSET is not netted (E35.1). Capex legs: split: capex_ppe + capex_intangibles, as the accounts print them |
| 5 | DCF conventions | 10 explicit years; terminal 2.5%; END-OF-YEAR discounting; first-year flow FCF0 * (1 + g); Gordon on year 10, discounted 10 full years |
| 6 | r and g | r 9.50%, 7.0% core expected return + 2.5% single-company premium (E29); g 3.00% from `reference/growth-views/AUTO.L.md` (2026-08-27) |
| 7 | as-of dates | flows to 2026-03-31; balance sheet 2026-03-31; share count 2026-03-31; price 2026-08-27 — **THEY AGREE** |
| 8 | provenance | 10 input(s), below |

## Bridge items (declaration 4, item by item)

| item | in the bridge? |
|---|---|
| `short_term_investments` | **DATA MISSING** on this basis |
| `leases` | 43 |
| `non_controlling_interests` | no field in this schema (E35) |
| `pensions` | 0 (stated) |
| `current_financial_assets` | **DATA MISSING** on this basis |

## Inputs (declaration 8)

| input | value | entered by | verified (E40) | provenance |
|---|---:|---|---|---|
| `capex_ppe` | -27.3 | store | VERIFIED (cross_document) | p.105: 'Purchases of property, plant and equipment (27.3)' -- the PDF text layer extracts this as '(27 .3)'; cross-checked against the ESEF/iXBRL package, tag ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities, context P04_01_2025To03_31_2026, unit Unit_GBP, scale 6: 27.3, sign attribute absent. Not a discrepancy: this concept is inherently an outflow, tagged as a positive magnitude by iXBRL convention, while the printed statement (and this field) sign cash outflows negative. Same £27.3m either way -- the sign was reconciled by convention, not by value. |
| `capex_intangibles` | -0.1 | store | VERIFIED (cross_document) | p.105: 'Purchases of intangible assets (0.1)'; cross-checked against the ESEF/iXBRL package, tag ifrs-full:PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities, context P04_01_2025To03_31_2026, unit Unit_GBP, scale 6: 0.1, sign attribute absent. Not a discrepancy: same convention gap as capex_ppe above -- iXBRL tags the outflow as a positive magnitude, this field signs it negative. Same £0.1m either way. |
| `operating_cash_flow` | 322.8 | store | VERIFIED (cross_document) | p.105, consolidated statement of cash flows: 'Net cash generated from operating activities 322.8'; cross-checked against the ESEF/iXBRL package, tag ifrs-full:CashFlowsFromUsedInOperatingActivities, context P04_01_2025To03_31_2026, unit Unit_GBP, scale 6: 322.8 |
| `sbc` | 9.2 | store | VERIFIED (cross_document) | note 28, p.126, cash generated from operations reconciliation: 'Share-based payments charge (excluding associated NI) 9.2'; reconciles exactly to note 29, p.126, share-based payments: 'Total charge 9.7' less 'NI and apprenticeship levy on applicable schemes 0.5' = 9.2 -- the same charge decomposed in the separately-prepared remuneration note (FRAMEWORK-EDITS E59) |
| `diluted_weighted_average_shares` | 8.627e+05 | store | VERIFIED (cross_document) | note 11, p.117, earnings per share: 'Diluted EPS 862,666,250' weighted average number of ordinary shares (entered in thousands, share_unit: E53); reconciles to rounding against p.101, consolidated income statement: net_income 293.9 / diluted_eps 34.07p = 862,635,750 point estimate (30,500 shares off stated, 0.0035%), within the band [862,362,436-862,909,144] implied by both inputs' own printed rounding -- see SHARE COUNT ARITHMETIC CHECKS in the header. A reconciliation against the separately-prepared primary statement, not an exact digit match, per FRAMEWORK-EDITS E59 |
| `financial_liabilities_current` | 0 | store | VERIFIED (cross_document) | note 21, p.121, borrowings repayment schedule: 'Less than one year – –'; reconciles exactly to note 31, p.131, net debt roll-forward: 'Debt due within one year – – – –' -- the same zero balance independently stated in the separately-prepared net debt reconciliation (FRAMEWORK-EDITS E59). EXCLUDES the £5.0m vehicle stocking loan (note 20, p.121) under FRAMEWORK-EDITS E55 -- inventory finance, presented inside trade and other payables, not borrowings |
| `financial_liabilities_noncurrent` | 163.4 | store | VERIFIED (cross_document) | p.103, consolidated balance sheet: 'Borrowings 21 163.4'; note 21, p.121: 'Total borrowings 163.4' (£165.0m gross of the Syndicated RCF less £1.6m unamortised debt issue costs); cross-checked against the ESEF/iXBRL package, tag ifrs-full:LongtermBorrowings, context PAsOn03_31_2026, unit Unit_GBP, scale 6: 163.4 |
| `lease_liabilities` | 42.6 | store | VERIFIED (cross_document) | note 14, p.119, 'Lease liabilities in the balance sheet at 31 March': 'Current 0.6' + 'Non-current 42.0' = 'Total 42.6'; cross-checked against the ESEF/iXBRL package, tags ifrs-full:CurrentLeaseLiabilities (context PAsOn03_31_2026: 0.6) + ifrs-full:NoncurrentLeaseLiabilities (context PAsOn03_31_2026: 42.0), unit Unit_GBP, scale 6: sum 42.6 |
| `pension_deficit` | 0 | store | VERIFIED (same_page) | note 24, p.123-124: the Scheme's buy-in was converted to a full buy-out on 2025-09-12 and accounted for as a Settlement; 'it was not necessary to derive assumptions as at 31 March 2026 since there were no benefits to be valued'; the note's own balance-sheet reconciliation states, for 2026, 'Present value of funded obligations –', 'Fair value of plan assets –', 'Net asset recognised in the Consolidated balance sheet –' -- all nil. The £2,000 IFRIC 14 residual named on the same page is an ASSET, immaterial at this file's £0.1m rounding, and not the LIABILITY E35.1's field is (FRAMEWORK-EDITS E35.1, resolved 2026-08-27 -- see header PENSION DEFICIT note) |
| `cash_and_equivalents` | 18.2 | store | VERIFIED (cross_document) | p.103, consolidated balance sheet: 'Cash and cash equivalents 19 18.2'; note 19, p.121 confirms; cross-checked against the ESEF/iXBRL package, tag ifrs-full:CashAndCashEquivalents, context PAsOn03_31_2026, unit Unit_GBP, scale 6: 18.2 |

*Tool commit: `AUTO.L first strike, 2026-08-27, d179600`.*


</details>

### AUTO.L -- the framework's own output on the price (NOT a recommendation)

- price 5.36 GBP vs fv_base 4.82 GBP: **+11.2%** -- price is ABOVE fv_base
- price 5.36 GBP vs FV_bull 6.08 GBP: **-11.8%** -- price is BELOW the bull case
- **section 6.4, 'At FV_base, trim 25-50%; reassess': FIRES** (price >= fv_base).
- **C4, 'exit when even the bull case does not beat the index': does not fire.** Expected return from 5.36 to FV_bull 6.08 is **+13.4%**; the index core's expected return is 7.0% a year (E29's anchor). C4 states no horizon: on the reading applied to MSFT and UNA.AS (price above/below FV_bull, expected return positive or negative) it does not fire outright here since price is below FV_bull; read as ONE year against 7.0%, the bull-case gap is ABOVE the index. Which horizon C4 means is the owner's to say.

*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on the fragility, and nothing here does.*

---

## What this run does NOT do

- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are not written there.
- **It does not score tier.** Section 4.4 has not run for AUTO.L; MBP is printed as DATA MISSING rather than computed on a placeholder tier.
- **It does not authorise a purchase.** S0 rule 4 stands: below price X, under conditions Y, with stop Z -- none of which this run sets.
