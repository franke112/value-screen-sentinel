# Handoff, 2026-10-27 afternoon: E140 is in the engine; what is left

Read this first in a fresh session. It supersedes `reference/HANDOFF-2026-10-27.md`
for everything after step 1. That file still holds the original error list
(items 1-13) and the dates table, which stay valid.

## Done, committed on branch pdf-primary-sources

| Commit | What |
|---|---|
| 5485e11 | **E140.1** (owner): acquisition spend is capex for a repeat buyer (2 of 3 years, no threshold); GDDY deferred revenue stays out; the bridge rolls to the latest filed balance sheet with the year-to-date working capital neutralised and the events ledger cut at that date; fv_base only from NEW records |
| 0b3e325 | E140.1 correction: the test decides, not the list. It catches ACN, AOS, CENTA, CPRT, CTSH, HRB, LII, PEP. **Not ULTA** (one year of three). A net receipt year counts as zero |
| 9214dcb | **E140 / E140.1 native in the engine** (step 2, part 1) |

**What 9214dcb contains:**

- **`vss/valuation.py`:** `normalised_free_cash_flow_zero`, `NormalisedYear`, `STATUTORY_TAX_RATE`.
- **`vss/runrecord.py`:**
  - the `E140Block` on the record, with `fcf0()` and `legs()` using it and `at_deal_end("low")`;
  - `missing()` requires the block on records from 2026-10-27 07:00 UTC;
  - `from_store(..., ledger=)` builds the block. **The roll happens only when a ledger is given**: the pre-E140 construction and the golden tests stay on their own balance sheet.
- **`vss/manual.py`:**
  - fields `working_capital_change` and `acquisitions_paid`, both needing E25 zero evidence;
  - a `roll_forward:` block and `roll_forward_basis()`. The basis carries pension and ARO from the year-end, named zeros, and the lease pair when the 10-Q states neither;
  - `fiscal_year_bases()` and `working_capital_since()`.
- **`vss/events.py`:** ledger loader. It refuses on no ledger, a ledger older than 7 days, a missing `closed:` date, low > high, or a unit mismatch.
- **`vss/strike.py`:** refusal 4 (the ledger); the doc prints the E140 parts, the bridge and both deal ends.
- **`vss/xbrl.py`:**
  - `e140_working_capital` (the E140(1) composite; provision AS TAGGED with its sign; one net line as fallback);
  - `apply_e140`, `build_roll_forward`;
  - `fill_e140` / **`vss xbrl --ticker X --e140-fill [--write]`**, which fills an EXISTING store and touches nothing else;
  - `latest_filing_facts`, which reads the newest 10-Q's own inline XBRL when companyfacts lags.
- **`vss/ixbrl.py`:** the inline XBRL reader.
- **`tools/quotecheck.py --apply X`:** marks E131 PASSes; it now reads `roll_forward` too.
- **Ledgers:** all 27 gained `money_unit:` and a per-deal `closed:` date (null = pending, always in the bridge).
- **Stores:** 16 US stores filled. All 48 annual WC rows equal the side tool exactly.
- **Hand reads, all E131 machine-verified:**
  - ALV FY2023 SBC 11m and FY2024 13m (Statement of Total Equity in the FY2025 10-K);
  - GDDY roll-forward cash 1,155.5m (Q2 10-Q);
  - NVR roll-forward cash 1,144,674k (homebuilding + mortgage, restricted cash excluded);
  - NVR senior notes 908,162k.
- **Tests:**
  - new `tests/test_e140.py` (30 tests);
  - `test_strike.py` moved to AS_OF 2026-10-27, struck against pre-E140 records;
  - two stale pins fixed: HELD is now [CTSH, CENTA]; DECK's FY2026 `acquisitions_paid` searched zero is flagged as exempt (E108), never refused;
  - the last full run was 2873 passed and 2 failed. Both failures were fixed afterwards; the full suite was **not re-run** after those fixes.

## Dry-run values (16 US names, nothing written)

Each pair is old base -> E140.

| Names | Values |
|---|---|
| ACN, ALV, AOS | 261.91->143.21; 134.34->85.89; 63.00->56.87 |
| CENTA, CPRT, CROX | 61.83->**28.60** (31.35 with deals at the low end); 25.45->23.62; 151.64->188.39 |
| CTSH, DECK, GDDY | 84.16->57.89; 120.03->110.18; 129.03->77.03 |
| HRB, LII, LOPE | 82.24->67.32; 285.07->207.99; 125.98->131.16 |
| MUSA, NVR, PEP | 217.03->261.05; 4,867.82->6,614.83; 56.82->51.60 |
| ULTA | 369.79->399.95 |

## CENTA: what we learned (the owner's lesson, and mine)

**How the value moved:**

| Step | Value |
|---|---:|
| Old record (single year FCF0 301.5m) | 61.83 |
| Three-year mean ex working capital | ~47 |
| Acquisitions as capex | 42.16 |
| TRIXIE 580m + Burpee 90-260m as debt with zero cash flow | 28.60 |

**What we found:**

- **TRIXIE's filed accounts:** 2021-2024 are in `sources/CENTA-TRIXIE_*`. 2021 and 2022 are text the owner pasted.
  - TRIXIE files under PublG § 9(2): **no profit in any year**.
  - Revenue 316.2 / 296.8 / 276.7 / 266.5 m EUR (2021-24), down 16% from the pandemic peak.
  - Debt-free since 2023.
  - Equity grew 14.5 / 18.2 / 6.8 / 1.4 m (profit minus withdrawals, a floor only).
- **Management says ~8x EBITDA** (Canaccord conference), so ~EUR 50m EBITDA. This is not in a filed document.
- **TRIXIE's full audited figures** will probably come in an 8-K/A after closing (S-X 3-05; the deal is ~23% of Central's market cap), around spring 2027.
- **Burpee** is private, owned by George Ball. There are no figures; Central gives details on the FY2026 call (~2026-11-23..30).
- **Champion USA** (cattle fly control, 57m, 2025-12-12) is already in the June balance sheet.
- **Central's acquisition record (10-Ks 2015-2025):**
  - ~$1.4bn spent; only ~$60m written down (live fish twice, pet durables 12.8m in 2024, one garden trade name);
  - op income 129m (FY16) -> 250m (FY25), ~8-9% pre-tax on what they spent;
  - $821m bought at the 2021 peak, and revenue has fallen since (3.30bn -> 3.13bn);
  - TRIXIE repeats that pattern: a pandemic winner, now shrinking.
- **Working value** with TRIXIE credited cautiously: **~34**, against a price of 39.13.

**OWNER OPEN (CENTA):**

- (a) TRIXIE treatment: rule as is (28.60) or credit it via management's multiple (~34-37);
- (b) **a stop level, still unset**;
- (c) hold, or trim after the FY2026 10-K. The owner chose to wait for the report and to drop CENTA as the focus for now.
- (d) The owner, 2026-10-27: TRIXIE is to be counted "som Warren hade räknat det" -- the price as capital spent, earnings credited at a conservative owner-earnings level. To be written as an E140 amendment only on his word. He will probably sell much of the holding.
- The headless 10-K auto-run on hel1 works again (OAuth fixed by 2026-10-24). `~/stocks-auto/centa-prompt.md` was rewritten for E140; the old version is in `centa-prompt.pre-e140.md`.

**Lessons, also in memory (`lessons-centa-e140`):**

1. A single-year FCF0 capitalised a one-off inventory release. Fixed by E140.
2. Deals after the basis were not looked for. Fixed by the ledgers and the 7-day age refusal.
3. **Before trusting an acquired business:** check its revenue trend and the acquirer's record of past deals. TRIXIE peaked in 2021; Central bought at the 2021 peak before.
4. A private target may have NO public profit (PublG § 9(2), a private US company). Say so at once, and name where the figures will come from (S-X 3-05 8-K/A, the earnings call).
5. **Engineering:**
   - never write a searched zero where the year-end leg is non-zero (NVR's notes sit under an extension element);
   - companyfacts lags filings by months (CTSH and LII Q2), so check the EDGAR filing list;
   - a provision is deducted as tagged, sign included (ALV, LII, CROX).
6. **Show the waterfall** whenever a value moves a lot. 61.83 -> 28.60 printed bare looked like an error to the owner.

## To do, in order

1. **Finish step 2:**
   - run the full suite in the background (~3 min);
   - re-strike the 16 US names for real (`vss strike --ticker X`; the ledgers are dated 2026-10-27, so this must happen by 2026-11-03 or the ledgers must be re-swept first);
   - commit with the same-commit playbook rebuild.
2. **Step 3, non-US names:** ACAD.ST, AUTO.L, BOUV.OL, LIAB.ST, MC.PA, MEKKO.HE, PNDORA.CO, RBREW.CO, RKT.L, RMV.L, SAP.DE.
   - Put `working_capital_change` and `acquisitions_paid` into 3 annual entries per name from `reference/normalized/inputs/<T>.json`. It has quotes and pages; the files are in `arkiv/2026-10-27-e140-underlag/`, so read the old /tmp paths there. Enter UNVERIFIED, then `tools/quotecheck.py --apply X`.
   - **For a TTM or interim balance sheet:** `working_capital_change` for each quarter since the year-end, or a `roll_forward:` block holding the YTD figure. LIAB's Q3 (2026-10-23) has not been read.
   - **Gaps:**
     - BOUV FY2023 is missing (try once more, else BOUV cannot be struck);
     - SAP is a sec-xbrl store with an extension payables line (WC by hand);
     - PNDORA has no net debt on its record;
     - MEKKO's FY2023 lease interest is a stand-in;
     - RBREW's FY2023 intangibles capex is blank.
   - Then re-strike, one commit per name.
3. **Step 4:**
   - write fv_base from the NEW records on the owner's word (E140.1(4)), with the playbook rebuild in the same commit;
   - rebuild the overview page;
   - `config/watchlist.yaml` holds an UNCOMMITTED owner change (UMG.AS PIPELINE -> WATCH-GATED). Ask the owner before committing it with anything else.
4. **Step 5, `~/vss-public`:**
   - port E140/E140.1, the engine changes, the ledgers and the results;
   - scrub per memory `public-repo.md`;
   - README holdings: CTSH and CENTA (148) HELD, CRUS SOLD;
   - the owner pushes.
5. **Step 6:** the owner pushes the private repo (~113 commits ahead).

## Kickoff prompt for the next session

> Läs reference/HANDOFF-2026-10-27-PM.md. Släpp CENTA tills vidare. Fortsätt i ordning: avsluta steg 2 (full testsvit, slå om de 16 US-namnen, commit), sedan steg 3 namn för namn med commit efter varje, sedan steg 4-6. Fråga mig bara om sådant som verkligen är mitt beslut, och visa alltid nedbrytningen när ett värde rör sig mycket.

## Session 2026-10-27 (later): steps 2 and 3 done as far as they go

- **Step 2 DONE** (6341f0f): suite 2875 passed; the 16 US names re-struck, values as the dry-run table.
- **Step 3**, one commit per name: ACAD.ST 152.32->25.91 (d451650), AUTO.L 4.84->4.84 (a4dec36),
  BOUV.OL 21.21->52.45 (2e75359; AR 2024 found on NewsWeb 643617), LIAB.ST 68.97->-33.97 (f4c7cbc,
  DROPPED), MC.PA 321.94->342.63 (d495062, rolled to H1, ledger re-cut), MEKKO.HE 10.54->10.46
  (f1bb5a4), PNDORA.CO -- ->761.40 (e7e9941), RMV.L 4.22->3.99 (d9263bd).
- **NOT struck:** RBREW.CO (df79339, June debt split is the owner's: negative every way),
  SAP.DE (7f446ea, lease interest stated nowhere -- pre-existing E120 block),
  RKT.L (nothing entered: FY2023 lease principal needs the 2022 lease liability, AR 2023;
  reckitt.com refuses automated download -- the owner to drop it in inkorg/ or allow FCA NSM).
- Non-US halves now roll via a `roll_forward:` block (MC, MEKKO, RMV, RBREW, SAP); quarterly
  TTM stores via each 2026 quarter's `working_capital_change` (BOUV, LIAB, PNDORA).
- Steps 4-6 wait on the owner (fv_base, UMG.AS commit, then vss-public and pushes).
