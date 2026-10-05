# vss — Review #4: does the chain reach an answer, and does the text still describe the program?

You are reviewing a private value-investing tool one person uses to place real money. Currently held: SAP.DE (fv_base 185, tier 1) and LIAB.ST (fv_base 102.66, tier 2). Every finding is ranked by its effect on those two numbers.

## Environment
- Network access: [YES / NO — fill in]. If NO, every claim needing SEC/Yahoo goes under HYPOTHESIS.
- You are running on [the working tree on disk / a clean clone — fill in]. config/watchlist.yaml, sources/ and reports/ are gitignored; say which of them you can actually see.
- Write the report incrementally to reports/REVIEW-4-<date>.md after each part, so a context cut loses nothing.
- This prompt is run as THREE sessions. Session A = Parts 1–4 (what the model measures; one chain of reasoning, run sequentially). Session B = Parts 5–8 (coverage, text vs code, data sources, competing definitions; parallelisable per name / per ruling). Session C = Parts 9–11 (tests, regression suite, reproducibility). Each later session starts by reading the previous session's report. Do not start a part that belongs to a later session.

## Reading order
1. vss/ source (valuation, store, xbrl, manual, ranking, rules).
2. reference/FRAMEWORK.md, then reference/FRAMEWORK-EDITS.md E1–E33.
3. reference/HANDOFF-2026-08-25.md LAST. It is my narrative and may carry the same misunderstanding as the code. Nothing in it is evidence.

## External figures used in this brief — provenance-tiered, not gospel
Rule: when you use one of these, cite the filing or document, not this brief. If your own read of the source disagrees, the source wins and you report the disagreement as a finding. Tier 1 = read from the filing or the issuing body's own text/API on 2026-08-25. Tier 2 = secondary source; confirm against the filing before relying on it.

- TIER 1 — DECK FY2026 10-K (FYE 31 Mar 2026, accn 0001628280-26-037664, values also returned by data.sec.gov companyconcept): weighted diluted 145,805k; weighted basic 145,498k; balance-sheet outstanding 31 Mar 2026 139,978k; cover-page dei count 138,880,957 as of 1 May 2026; SBC 44.8 MUSD pre-tax; FY2026 buybacks 10.5m shares for 1.075 bn USD. The number 136,414,227 appears in NONE of these. Likeliest source: the cover page of the Q1 FY2027 10-Q (as of ~July 2026). Find its provenance in the repo.
- TIER 2 — DECK FY2026 free cash flow: press release says "over one billion dollars", a results summary says "above $900 million"; read the cash-flow statement and settle it.
- TIER 2 — NKE FY2026 (FYE 31 May 2026): SBC ≈ 715 MUSD (data aggregator). Confirm from the 10-K. TIER 1 — Nike tags no OperatingIncomeLoss.
- TIER 1 (SEC developer docs + live JSON) — SEC companyfacts: per-fact objects carry end, val, accn, fy, fp, form, filed, frame — NO `decimals`, NO dimensioned facts. Every as-filed occurrence is present (one per accession), so restated/split-adjusted values appear as additional entries; the originals remain. The frames API returns one deduplicated fact per entity per period. CIK must be zero-padded to 10 digits. Rate limit 10 req/s; violations get 403 and a short block. www.sec.gov/files/company_tickers.json answers 200 with a compliant User-Agent — correct any repo note that says otherwise.
- TIER 1 (standards text) — ASC 230: interest paid is in OPERATING cash flow. IAS 7.31–34: IFRS filers may put it in operating OR financing. IFRS 16.50: lease principal is a FINANCING outflow. TIER 2 — "~76% of IFRS filers choose operating" is from a 2017 academic study; irrelevant for the review, read each filer's own statement.
- TIER 1 (standards text) — IAS 1.60/63: current/non-current split is required EXCEPT where liquidity-order presentation is more relevant (banks, insurers). IFRS 18 replaces IAS 1 for periods beginning 1 Jan 2027.
- TIER 1 (yfinance repo/changelog) — raises YFRateLimitError since 0.2.5x (not always silent); auto_adjust defaults to True since 0.2.51; with auto_adjust=False, Close is raw and Adj Close is split+dividend adjusted; truncated history can still return without error. Confirm against the version pinned in the repo.
- TIER 1 (his own papers and blog) — Damodaran's position on SBC: expense it, do not add back. "Add back + fully diluted shares" is NOT equivalent, because diluted shares capture existing grants only, not future ones. Any quoted "consistency rule" in the repo saying otherwise is not from him.

## Evidence rules
File and line for every claim. Smallest input that shows the defect — RUN it, paste actual output. Unexecuted claims go under a heading HYPOTHESIS. Per finding: can it fire on data in the repo today (yes/no, which name)? Direction of the error (overstates / understates fv_base). Do NOT fix. Do NOT refactor. ~1,500 tests pass; passing tests are not evidence — several were written from the same misunderstanding as the code. Where a test asserts something you believe wrong, name it and show why.

---

## PART 1 — What does FCF0 measure? (largest expected impact; do this first)

FCF0 = operating cash flow − capex. Under ASC 230 that is a POST-INTEREST number. Establish with file and line:
- Does Method C treat FCF0 as cash flow to the firm or to equity?
- After discounting, does it subtract net debt / add net cash to reach equity? If FCF0 is already post-interest and net debt is also subtracted, interest is charged twice. Net-debt name (LIAB.ST): understates equity. Net-cash name (SAP.DE, DECK): adding cash to a post-interest-income FCF overstates it.
- For each IFRS filer in the store (SAP.DE, LIAB.ST, PNDORA.CO, BETS-B.ST, UNA.AS) read the cash-flow statement and record where interest paid, interest received and dividends received are classified. The same formula means different things per filer; say whether the code knows that.
- IFRS 16: OCF for an IFRS filer excludes lease principal; E14 stores leases outside financial liabilities. Is net debt (with or without leases) consistent with what OCF already excludes? Direction and rough size for SAP.DE.

MEASURE IT on SAP.DE and LIAB.ST: equity value (a) as coded, (b) with interest handled consistently — FCFF at a firm rate minus net debt, OR FCFE at an equity rate with no net-debt step. Report the fv_base difference in EUR/SEK and %. Say plainly whether 185 and 102.66 move, and by how much.

## PART 2 — Discount rate, DCF specification, dates

- E29: flat 9.5% for every name and currency, input recorded nowhere. State: is 9.5% applied to equity cash flows or firm cash flows, and is that the matching rate? For each non-USD name, does a rate set from a USD index on EUR/SEK/DKK cash flows create a currency/inflation mismatch, and what sign?
- Pin the DCF spec from code, not from FRAMEWORK: horizon, terminal growth, terminal-value rate, mid-year convention or not, base = TTM FCF0 or normalised. List every convention the code applies that FRAMEWORK.md does not state. A mid-year convention alone shifts value by ≈ (1+r)^0.5 − 1 ≈ 4.6% at 9.5% — most of the 6.99% DECK gap.
- Re-derive DECK: reproduce 131.74 from the store, then re-run under each of the four verified share counts (145,805k / 145,498k / 139,978k / 138,881k) and with/without mid-year. Show which combination gives 140.95, if any. If none does, the hand-struck number used an input not in the FY2026 10-K — find it.
- Three as-of dates in one per-share number: net debt at window end (E19), price today, share count at its own date. DECK bought back 10.5m shares for 1.075 bn USD during FY2026 and kept buying after; a July 2026 share count paired with a March/June 2026 cash balance overstates per-share value. Quantify for DECK. State whether any run records all three dates.

## PART 3 — SBC (demoted; measure, do not assume it is large)

Prior: DECK SBC is ~4.5–5% of FCF (44.8 MUSD vs ~0.9–1.0 bn); NKE is ~20–30%. For NKE, DECK, SAP.DE and LIAB.ST report from the store or filings: SBC as % of FCF0; fair value with SBC added back (as coded) vs deducted; the delta in fv_base. Report the result under EACH share count — do not assume a pairing rule. Say whether any fair value the tool has produced changes materially, and by how much.

## PART 4 — Enterprise-to-equity bridge and price inputs

- Bridge items the code applies or omits: minority interest (material for UNA.AS), preferred, pension deficit, equity-accounted stakes, convertibles, short-term investments (in or out of net debt), leases (E10 vs E14 consistency). Per item: handled / omitted, sign of the error.
- Price: GBX vs GBP for .L names; quote currency vs reporting currency (BETS-B.ST); currentPrice vs last close; stale price on a holiday; which FX rate date E24 freezes and whether the frozen rate is the one the run actually used.

## PART 5 — Coverage

For every name the tool can be asked about — watchlist, config/manual/*.yaml, screener universe head — can §5 produce a fair value end to end? Table: name / runnable / EXACT field or step that stops it / origin of that field (xbrl, manual, nordic-xlsx, yfinance). Verify by running, not by reading HANDOFF.

## PART 6 — Text versus code, E1–E33

Report ONLY rulings where (a) text and code disagree, (b) the code implements something the text does not state, or (c) the text states a single case rather than a rule and would break on a filer type it has not met. Named candidates: E26 (IAS 1.60/63 exception for liquidity-order presenters; IFRS 18 from 2027), E29 (no recorded input), E33 (written on IFRS 16, wrong for US GAAP), E14 vs E10 (leases in and out of net debt), E19/E20 (TTM basis vs half-yearly and annual-only reporters), E23 (capex_combined vs split), E24 (frozen FX vs re-struck). For each: implemented? as written? general rule or one case? filer types it would break on.

## PART 7 — Data sources, corrected premises

SEC XBRL:
- `_pick`: how does it deduplicate the multiple as-filed occurrences of one fact (by end date? latest filed? first filed?) — show the code path and one real example from a stored name where the choices differ (a split-restated share count or EPS). Would the frames API be a cleaner route? Say why or why not from the code.
- Scale errors: `decimals` is not in companyfacts. What magnitude checks exist (unit-mix guard ≥1000×, band checks)? Would a filer whose `val` is off by 1000× pass into §5?
- CIK padding, 10 req/s, 403 handling, retry — file and line.
- ifrs-full tag map for 20-F filers (SAP.DE CIK 1000184, UNA.AS CIK 217410 — confirm UNA still files 20-F). Would `vss xbrl` reach them?
- Capex sign flip — file and line.
- Correct every note that says company_tickers.json is closed.

yfinance:
- Which version is pinned? Does the code read Close or Adj Close, and with which auto_adjust value? Is YFRateLimitError caught, and what happens on truncated history (row count / date-coverage check)?
- Phantom gap at a split: is anything checking?
- Universe CSVs are today's constituents (survivorship), AND yfinance fundamentals are latest-restated with no as-of date (look-ahead). State what both mean for every backward measurement, including B34.

Hand-entered:
- VERIFIED means different things (SYNSAM.ST: 20 figures cross-checked against a second document, 52 re-extracted from the same page, one flag). Is the distinction recordable in the schema? What would §5's refusal gate do with each kind?

## PART 8 — Every place two definitions compete

Where two defensible definitions of one quantity exist and the code picks one silently. For each: which the code uses / does FRAMEWORK state a choice / direction of the error / which stored name it changes today. Check at least: share count (basic, diluted, balance-sheet, cover-page, treasury-stock at current price); FCF basis 1/2/3; capex all vs maintenance vs capex_combined; net debt ± short-term investments ± leases; revenue net sales vs total (SYNSAM ruling); interest classification per filer; TTM vs FY vs H1 basis; EBIT alias order (E8); gross margin definition; price close vs current; FX rate date; SBC in or out.

## PART 9 — Tests

Method, not opinion: (1) grep tests that assert a fair-value NUMBER (NKE 22.15 etc.) and list them. (2) Flip one concept at a time — share-count basis, SBC add-back, mid-year convention, net-debt-with-leases — and run the suite. This is the ONE exception to "do not modify code": do it in a throwaway git worktree, one flip at a time, SEQUENTIALLY (never parallel flips in one tree), record the diff and the failing-test list per flip, then delete the worktree. Nothing from it is committed. Any concept whose flip breaks zero tests is unpinned; report those. (3) Name every test that asserts something you believe wrong, with the reason.

## PART 10 — Regression suite (propose, do not build)

The NKE case (22.15 / 17.72 / 25.73, r 9.5%, band 20.64–23.89) reproduces a hand calculation that shares the code's concept choices. Label it "pins arithmetic given stated assumptions", never "known-correct". Propose the smallest set of golden cases that would catch the classes above. Each case must state its concept choices explicitly (share-count basis, SBC treatment, interest treatment, DCF conventions, all three as-of dates) so a future change to a choice fails the case loudly. Per case: what it pins, which defect it catches. A list I will maintain.

## PART 11 — Reproducibility

Does a §5 run record every input needed to regenerate its output — price and date, share count and its basis and date, net debt components and date, FX rate and date, SBC treatment, r, g, DCF conventions? Can DECK 131.74 be regenerated from the run record alone? If not, name the missing fields.

---

## Close
Rank all findings by expected effect on SAP.DE 185 and LIAB.ST 102.66 in SEK. Name the ONE finding you would fix first and why that one.
