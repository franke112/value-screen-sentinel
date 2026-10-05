# Intake: BOUV.OL — Bouvet ASA, Oslo — 2026-09-08

Read **before** it is watched (E111). **Nothing was entered as PIPELINE and
BOUV.OL is not on the watchlist.**

**AMENDED LATER THE SAME DAY.** Sections 1-6 were written before any growth
view existed and say so in the present tense; they are left as written. The
owner then registered a view and the name was struck and PARKED at INTAKE
— **section 7 is the amendment and governs where the two differ.**

BOUV.OL came off the 2026-09-05 ranking at **#5** — operating profitability
24.3%, earnings yield 8.4%, rank 67 — and was `NO STORE / hand download` on
that run's readiness column. It has a store now.

| | |
|---|---|
| basis | **TTM 2025-Q3 + 2025-Q4 + 2026-Q1 + 2026-Q2, ending 2026-06-30** — 70 days before today, inside the 550-day limit |
| FCF0 | **NOK 223,851 thousand** (NOK 223.9m) |
| net debt | **NOK 162,122 thousand** — leases 321,855 less cash 159,733; no borrowings of any kind |
| divisor | **103,695,316** — E91's day-weighted average of four stated per-quarter diluted counts |
| state | **complete but for the read-backs.** No leg is DATA MISSING |
| growth view | registered by the owner 2026-09-08, bear 2 / base 3 / bull 6 — §7 |
| value | **PROVISIONAL, fv_base 31.24** against a close of 48.85, **+56.4%** — §7 |
| status | **INTAKE, and PARKED there by the owner 2026-09-08** — §7 |

---

## 1. The route: Oslo is now in the fetcher, and that was the first problem

`vss nordic` refused a `.OL` ticker outright — *"Oslo Børs is operated by
Euronext, not by Nasdaq, and this service publishes no Oslo market"* — and
the only Norwegian name on file, NHY.OL, had been fetched by hand off
hydro.com in August with the NewsWeb record named beside it. So the first
act of this intake was to build the door.

`vss/oslo.py` now serves Euronext Oslo's **NewsWeb**, the Norwegian
Officially Appointed Mechanism, and `vss nordic` dispatches to it on the
suffix. Same command, same `sources/manifest.json`, same manual `--period`.
Four things were measured and each is coded because of what was measured:

1. **This service HAS a company directory and Nasdaq's has none.** `POST
   /v1/newsreader/issuers` returns all 1,622 issuers with `issuerSign`,
   `issuerId` and name, so `--resolve` here is a LOOKUP rather than a
   full-text search over release bodies. `BOUV.OL` → sign `BOUV`, issuerId
   8307, **one candidate, exact.**
2. **An issuer sign the service does not know is SILENTLY IGNORED**, and
   the whole market's feed comes back under HTTP 200 — 601 rows from
   250-odd companies, looking exactly like this company's history. This is
   `nordic`'s rule 2 in a new costume and it is worse, because the answer
   looks like data rather than like nothing. Every row's sign is checked
   and a page carrying anybody else is **refused**, never filtered down.
3. **`fromDate`/`toDate` are required** — omitting them returns an empty
   list, which reads as "published nothing" — and **there is no `start`,
   `offset` or `limit`.** A window caps at ~601 rows and says
   `overflow: true`; a longer history is a narrower window.
4. **Every report is filed twice, Norwegian and English, as two separate
   messages with no language field on either.** So `--language` on an Oslo
   download is a MANUAL LABEL, like `--period`, recorded in the manifest as
   stated by the owner and never a filter.

**AND A CORRECTION TO THE RECORD.** The NHY.OL manifest entries of
2026-08-30 say NewsWeb's attachment endpoint *"answers HTTP 400 to every
automated request"*, which is why Hydro's reports came off hydro.com.
Measured again 2026-09-08, `api3.oslo.oslobors.no/v1/newsreader/attachment`
answers **HTTP 200** and serves the PDF; the `obsvc` path on the
`newsweb.oslobors.no` host — a different endpoint — returns an HTML page and
is the likely subject of the old note. **The old entries were not
rewritten:** a provenance record says what was measured on its own day.

**A LATENT BUG THIS SURFACED, AND IT HAD BEEN STRANDING DOCUMENTS.**
`save_manifest` sorted on `r.get("released", "")`, and the EDGAR and
issuer-website routes write `released: null` — **16 such records were
already in the file.** The default never fires, `str < None` raises, and
**every `vss nordic --download` failed AFTER writing the file and BEFORE
writing its entry.** That is precisely how a document this tool fetched
comes to read as PROVENANCE NOT RECORDED for ever. Fixed; `download`'s own
repair path wrote back the two entries this run had stranded.

**Five documents on the record**, all `primary_source`, origin
`euronext-oslo-newsweb`, `figures_read: false` at fetch time:

| period | document | NewsWeb | released | bytes |
|---|---|---:|---|---:|
| 2025-FY | Annual Report 2025 (audited) | 670820 a0 | 2026-04-16 | 3,113,619 |
| 2025-Q3 | Q3 report 2025 | 659260 **a1** | 2025-11-11 | 838,838 |
| 2025-Q4 | Q4 Report 2025 | 665740 a0 | 2026-02-13 | 782,372 |
| 2026-Q1 | Q1 Report 2026 | 673265 a0 | 2026-05-13 | 983,706 |
| 2026-Q2 | Q2 Report 2026 | 680129 a0 | 2026-08-19 | 841,764 |

*Q3 2025 is attachment **1**: attachment 0 of that message is the analyst
presentation. The route refused to guess and named both.*

Not fetched: the ESEF/iXBRL package (670820 attachment 1,
`bouvetasa-2025-12-31-1-no.zip`, the Norwegian tagged copy), and the
`Presentasjon` deck attached to every results release.

---

## 2. The store: 132 figures, all UNVERIFIED, and the issuer's own R12M column checks the stitch

Extraction was **the PDF path** — text layer read into
`config/manual/BOUV.OL.yaml` by hand — so **everything is UNVERIFIED as E40
requires** and section 5 is REFUSED. 132 figures entered, **52 read at the
basis**, none DATA MISSING among the legs section 5 needs.

**THE STRONGEST CHECK WAS FREE.** The Q2 2026 report prints a
`Jul 2025-Jun 2026` column on p.2, and every sum of the four separately-read
quarters lands on it:

| | sum of the four quarters | the issuer's R12M column |
|---|---:|---:|
| revenue | 3,880,893 | 3,880.9 |
| EBIT | 444,301 | 444.3 |
| profit for the period | 332,074 | 332.1 |
| operating cash flow | 272,440 | 272.4 |

Four documents read independently, one column, four agreements.

### What the basis needs, and what is filled

| leg | value (NOK 1 000) | where it came from |
|---|---:|---|
| operating cash flow | 272,440 | four stated quarterly totals |
| capex (PPE + intangibles) | −25,967 | E23: the statement prints the split |
| share-based compensation | 22,622 | four stated add-backs |
| interest add-back | **none** | `interest_in_ocf: no` — proved, see below |
| operating lease add-back | **none** | `operating_leases_in_ocf: no` — IFRS 16 |
| NCI dividends | 0 | E105, a determined zero |
| **FCF0** | **223,851** | |
| cash | 159,733 | balance sheet, 30.06.2026 |
| lease liabilities | 321,855 | two stated parts, both named |
| borrowings, current and non-current | 0, 0 | E25 `note`, said in all five documents |
| pension deficit | 0 | E25 `note`, AR note 06 |
| asset retirement obligation | 0 | E25 `caption` + an E107 search |
| prepaid delivery obligation | 0 | E25 `caption`, E81's own exclusion |
| **net debt** | **162,122** | |
| divisor | 103,695,316 | E91 |

**Nothing is missing and nothing is blocked.** That is unusual on a first
intake and it is because Bouvet's balance sheet is short: no borrowings, no
minority, no defined-benefit plan, no decommissioning, and a lease it splits
current from non-current on the face of the sheet.

### E34, and it is PROVED rather than assumed

`interest_in_ocf: no`, and the reasoning belongs in the record because a
literal reading of the statement gives the opposite answer.

Bouvet presents interest received under INVESTING and every interest paid
under FINANCING, with `Net cash flow from operating activities` struck above
all three. The operating section carries one reversal line, `Interest income
and interest expenses`, and **on its face that line removes only the interest
income and the NON-LEASE interest expense**: FY2025 −23,942 + 1,093 =
−22,849, exactly as printed, and the same identity holds in all four
quarters. Read literally, the lease interest (FY2025: 24,386) would be
charged inside operating AND paid again in financing.

**It cannot be.** The three sections sum to `Net changes in liquid assets`
−162,037, and the balance sheet's liquid assets move 834,341 → 672,304 — the
same 162,037. A double charge of 24,386 would break that tie by 24,386 and
it does not break. So the add-back sits inside `Changes in other accruals`
(−7,542), unnamed but necessarily present, and **the operating total is
stated before ALL interest.** Nothing is added back to FCF0 and
`net_interest_paid` is never read.

Had it gone the other way, FCF0 would be 248,237 rather than 223,851 — a
10.9% difference. It is worth the paragraph.

### Two things the issuer disagrees with itself about

**1. The Q1 2026 report's EBITDA is on a different definition from the Q2
2026 report's and from the annual report's.** It prints EBITDA 134,659
against EBIT 127,037 — a gap of 7,622, which is `Depreciation fixed assets
5,426` + `Amortisation 2,196` and **excludes `Depreciation of right-of-use
assets 17,849`** — against its own printed definition, *"Operating profit +
depreciation fixed assets and intangible assets"*. The Q2 2026 report's
Jan-Jun 2026 EBITDA of 300,361 against EBIT 249,347 gives 51,014 = 25,471 +
25,543, which **does** include right-of-use depreciation in both quarters,
putting Q1 2026 at 152,508. Two documents, **17,849 apart on one quarter.**
`ebitda` for 2026-Q1 is entered as DATA MISSING with both figures named —
E104's posture, that a figure two readings do not agree on is withdrawn, not
chosen between. Nothing in section 5 reads `ebitda`; §5.3's leverage test
does, and there is no leverage to test.

**2. `Ordinary profit before tax` differs by a few thousand between the
income statement and the cash flow statement** in three of the five
documents (Q4 2025: 102,121 vs 102,117; Q1 2026: 125,660 vs 125,654; Q3 2025
Jan-Sep: 370,423 vs 370,427). Nothing entered reads that line.

### And one the accounts never explain

`Other provisions for obligations` stood at **5,545** inside LONG-TERM DEBT
at 31.12.2024 and 30.09.2025, and went to **0** in Q4 2025. The AR 2025
balance sheet points the caption at **note 14 (Intangible assets)** and note
14 never mentions it; the words `contingent`, `earn-out` and `conditional
consideration` do not occur anywhere in the annual report. **It does not
reach the basis** — net debt is a stock at 2026-06-30, where the caption is
zero — but it is an open question about the accounts.

### One thing the schema refused, and was right to

A NAMED ZERO on `other_current_financial_assets` was attempted, on note 17's
exhaustive classification of the group's financial assets (work in progress,
trade receivables, liquid assets — and nothing else). **E25 refuses it:** an
absent caption there is NOT PRESENTED, and the field must stay blank. The
bridge omits the asset instead, which raises net debt and lowers the value —
the safe direction, and the loader said so.

---

## 3. E108's floor: seven read-backs, not fifty-two

**The zero limb ran in the code and exempted nine legs** — every determined
zero at the basis moves `fv_base` by exactly 0.0%: the four
`nci_dividends_paid`, 2025-Q3's `capex_intangibles`, and 2026-Q2's
`asset_retirement_obligation`, `financial_liabilities_current`,
`financial_liabilities_noncurrent` and `pension_deficit`.

**The measured limb could not run in the code**, because E108 measures
against *"that record's own `fv_base`"* and `fv_base` needs the growth view,
which is the owner's and which this session may not write. **So it was
measured by hand against the arithmetic instead**, which is fv_base-free for
every flow leg: a ±10% move in a leg L moves `fv_base` by
(0.1·|L| / FCF0) × (1 + net debt / equity value), and the second factor is
**1.032** at the current price and never above about 1.08 for any plausible
value. The 1% question is therefore settled by the first factor alone.

### ABOVE THE FLOOR — read these seven back

| leg | value | ±10% moves `fv_base` by |
|---|---:|---:|
| **2025-Q4 `operating_cash_flow`** | 363,443 | **16.7%** |
| 2026-Q2 `operating_cash_flow` | −54,600 | 2.5% |
| 2026-Q1 `operating_cash_flow` | −48,547 | 2.2% |
| 2025-Q4 `diluted_weighted_average_shares` | 103,841,034 | 2.46% |
| 2025-Q3 `diluted_weighted_average_shares` | 103,413,458 | 2.45% |
| 2026-Q2 `diluted_weighted_average_shares` | 103,372,896 | 2.43% |
| 2026-Q1 `diluted_weighted_average_shares` | 104,160,484 | 2.42% |

**One leg carries two thirds of the sensitivity of the whole store.**
2025-Q4's operating cash flow of 363,443 is larger than the whole TTM total
of 272,440, because the other three quarters are 12,144, −48,547 and
−54,600. Bouvet's working capital unwinds in Q4 and builds through the
year — `Changes in work in progress, accounts receivable and accounts
payable` is +176,253 in Q4 2025 against −40,337, −156,271 and −5,819 in the
others. If one figure in this store is worth reading back against the
rendered page, it is that one.

### CONDITIONAL ON `fv_base` — read these two back only if the value comes out low

| leg | value | ±10% at NOK 48.85 | crosses 1% only if `fv_base` is below |
|---|---:|---:|---:|
| 2026-Q2 `lease_liabilities` | 321,855 | 0.64% | **NOK 31.04 a share** |
| 2026-Q2 `cash_and_equivalents` | 159,733 | 0.32% | **NOK 15.40 a share** |

*Recomputed on any change of basis, as E108 requires.*

### BELOW THE FLOOR — the other 43

Every `capex_ppe`, `capex_intangibles` and `sbc` figure at the basis (the
largest, 2026-Q2's capex of −9,634, moves `fv_base` by 0.44%), and 2025-Q3's
operating cash flow of 12,144 (0.56%).

### AND A GAP IN THE CODE THAT IS THE OWNER'S TO RULE ON

**`vss manual` lists 52 UNVERIFIED figures as blocking, and 23 of them
cannot move `fv_base` at all.** `revenue`, `operating_income`, `net_income`,
`diluted_eps`, `net_finance_costs`, `depreciation_amortisation`,
`lease_payments_capital` (an explicit E70 MEMO), `shares_issued_period_end`
and `treasury_shares_period_end` (explicit E88 MEMOs) and FY2025's
`diluted_weighted_average_shares` (superseded by E91) are **read by the
basis for other sections and enter no fair value**. Under E108's own words —
*perturb the leg, and if the larger move is below 1% of `fv_base` it is
exempt* — a leg `fv_base` never reads moves it by 0.0% and is exempt. **The
code implements only the zero limb**, so these still block.

Extending it would relax a gate, and this session did not. Recorded as a
question: *does E108's exemption reach a leg the fair value does not read at
all, or only a leg it reads and that is small?*

---

## 4. E103 and E101's three checks

`vss reference-figures` could not run its model route — no
`VSS_OPENROUTER_KEY` on this host — so the five reference figures were **read
off the page by eye**, which E103 permits and which is stronger provenance
than the route it replaces. All UNVERIFIED, all fenced: the store still reads
the same 52 figures at the basis.

**Bouvet DOES publish a free cash flow. It does NOT publish a net debt.**

`Net free cash flow` is in the key figures of every quarterly, an ESMA APM
the issuer defines on the same page: *"Net free cash flow is calculated as
net cash flow from operations plus net cash flow from investing
activities."* 11,363 / 361,506 / −47,410 / −61,008 across the four basis
quarters, **TTM 264,451**; FY2025 343,125, which ties to the audited
statements (347,111 − 3,986).

| E101 check | this record | the issuer | measure |
|---|---:|---:|---|
| 1. FCF0 vs the issuer's own free cash flow | 223,851 | 264,451 | **−40,600, −15.4%** |
| 2. net debt vs the issuer's own net debt | 162,122 | — | **DATA MISSING** |
| 3. FCF0 / net income | 0.674x | band 0.2–3.0x | **INSIDE** |

**CHECK 1'S GAP RECONCILES TO THE KRONE, and every part of it is one of the
two differences E101 predicts by design.** The issuer's investing half
carries interest RECEIVED (19,815) and disposal proceeds (73) less financial
receivables (1,912), and its construction deducts no share-based
compensation (22,622):

    19,815 + 73 − 1,912 + 22,622 = 40,598,  against a gap of 40,600

Two of rounding. **Nothing to escalate.**

**CHECK 2 IS AN ABSENCE OF A CHECK, NOT A PASSED ONE.** Bouvet has no
borrowings and publishes no net-debt reconciliation, so there is nothing to
disagree with. The first construction check on this leg happens when a
comparator exists, and on this issuer there may never be one.

---

## 5. The briefing

`reports/BRIEFING-BOUV.OL-2026-09-08.md`, E76's eight sections, built by
hand — `vss briefing` runs off EDGAR and Bouvet has no CIK, no 10-K and no
Form 4. It carries no judgement, no growth rate and no fair value, and
`briefing.judgement_in` over the finished text returns **0 problems**.

Two things in it the owner asked for by name:

**AI AND CONSULTING DEMAND, IN BOUVET'S OWN WORDS.** Section 3b is verbatim
quotation and section 3a is the numbers. The one place a filing addresses
AI-based development tools and Bouvet's own delivery directly is the Q2 2026
outlook: *"The accelerating emergence of AI-based software development tools
is of particular significance to Bouvet, and is both impacting how projects
are delivered and increasing the group's need for in-house AI developers."*
The CEO's Q1 2026 framing is the sharpest: *"using AI within Bouvet is not
how we will secure truly significant competitive advantage… We are already
seeing how AI is strengthening our delivery capacity."* And on what clients
expect: *"There is also a further expectation that AI can help reduce
development and operating costs."*

**The numbers beside the words**, from the bridge Bouvet publishes every
quarter:

| | Q3 2025 | Q4 2025 | Q1 2026 | Q2 2026 |
|---|---:|---:|---:|---:|
| hourly rates, year-on-year | +2.9% | +2.8% | +2.1% | +2.3% |
| billing ratio, year-on-year | −2.1pp | −2.3pp | −1.8pp | −0.9pp |
| sub-consultants, % of revenue | 7.7% (8.3%) | 7.2% (8.2%) | 6.6% (8.1%) | 5.5% (8.1%) |

**Rates up in every quarter, utilisation down in every quarter, and
sub-consultants cut first.** Bouvet never connects any of the three to AI:
the causes it names for the billing-ratio fall are holidays, project
progress and sick leave. **There is no figure of any kind attached to AI
anywhere in the five documents** — no AI revenue, no AI cost, no
productivity number.

**WHY THE PRICE FELL — and the general search found nothing because the
events are the results days themselves.** 52-week high 72.90 (2025-08-22),
low 42.55 (2026-06-22), last 48.85 (2026-09-04): −41.6% peak to trough.
**Every one of the five largest single-day falls of the last two years is
the day Bouvet published a quarterly report, and so is the largest single-day
rise.**

| date | move | what Bouvet published that morning |
|---|---:|---|
| 2026-02-13 | −9.7% | Q4 2025, *"GOOD PROFITABILITY IN A CHALLENGING MARKET"* |
| 2025-11-11 | −8.2% | Q3 2025, *"Strong results for Bouvet"* |
| 2025-02-18 | −5.0% | Q4 2024, *"HISTORICALLY STRONG YEAR FOR BOUVET"* |
| 2025-04-04 | −4.4% | only a buyback status notice — the global tariff sell-off |
| 2026-05-13 | −4.4% | Q1 2026, *"STRONG PROFITABILITY IN A SOMEWHAT CHALLENGING MARKET"* |
| 2026-08-19 | **+16.4%** | Q2 2026, *"Strong momentum and robust profitability"* — the largest rise in the whole series |

Three of them carry **42% of the entire peak-to-trough fall** on three of
about 210 trading days. The other NOK 17.65 arrived without a single day of
−4% or worse: a drift, not an event.

**INSIDERS.** In the trailing twelve months: **three open-market purchases,
all by Tove Raanes, deputy chair** (3,000 at 59.73 on the −8.2% day; 5,920 at
47.00 on the −4.4% day; 5,000 at 47.54 on the +16.4% day), and **two sales —
400,000 shares by board member Egil Dahl at 60.15 on 2025-11-27**, after
300,000 at 75.70 in April 2025, and 3,200 by the Swedish regional director.
Dahl was still signing the accounts on 2026-05-12 and was off the board by
2026-08-18; the filings do not say why.

---

## 6. What remains

**Nothing is blocked for want of a figure.** What is outstanding is:

1. **Seven read-backs** (section 3), of which 2025-Q4's operating cash flow
   is worth more than the other six together.
2. ~~**The growth view**, which is E28's and the owner's, and which nothing
   here may write.~~ **CLOSED the same day** — registered by the owner and
   struck; see section 7.
3. **The E108 question** in section 3: does the exemption reach a leg the
   fair value never reads?
4. **Two things the filings cannot answer** and that the briefing names in
   full: what `Other provisions for obligations` was, and why Egil Dahl left
   the board. Neither reaches the basis.
5. **`vss refresh` has no route for this name.** `NO_ADAPTER_ISSUERS` still
   carries NHY.OL with the reason *"Oslo Bors is not on the Nasdaq Nordic
   feed this project reaches; no Euronext adapter is built"* — which is now
   false, and was left alone because changing a WATCHED name's refresh route
   is the owner's call, not a side effect of an intake. BOUV.OL is not on
   the watchlist and `refresh` never sees it.

**BOUV.OL is INTAKE. It is not watched, not in the pipeline, and has no
value of any kind attached to it.**

---

## 7. The view was registered and struck, and then the name was PARKED — 2026-09-08

**The owner registered a growth view the same day** — bear 2 / base 3 / bull
6, `reference/growth-views/BOUV.OL.md`, in his own words and committed
before the solver existed (E28). It was struck:
`reference/BOUV.OL-STRIKE-2026-09-08.md`.

| | NOK |
|---|---:|
| fv_base (g 3%) | **31.24** |
| E29 band, r 9.0% / r 10.0% | 33.78 / 29.03 |
| FV_bear (g 2%) / FV_bull (g 6%) | 28.90 / 39.41 |
| settled close, 2026-09-04 | **48.85** |
| price vs fv_base | **+56.4%** |
| g\*, at r 9.0 / 9.5 / 10.0% | 7.70% / **8.78%** / 9.82% |

**THE DECISION, RECORDED AS THE OWNER'S.** *"Nothing more on BOUV.OL — it
stays INTAKE, no watchlist entry, no Gate 1 stamp. The distance is 56% and
the value is provisional on 52 unverified figures; the seven read-backs
happen if it ever approaches, not before."*

**The two grounds, and each is an existing rule rather than a new one.**

**FIRST, THE DISTANCE — and this is E76's ordering, not an exception to it.**
E76 puts the expensive work *after* the value says it is worth the hours:
*"only if the price is within reach of the bear case does the reading
happen… 'Within reach' is the owner's judgement, not a threshold — a name
at twice fair value is not read; a name near or below it is."* At 48.85
against a base of 31.24 and a bear of 28.90, the price is **above the BULL
case of 39.41 by 23.9%**, and g\* exceeds the owner's bull at every rate in
E29's band. The read-backs are the same kind of spend E76 defers, so they
are deferred.

**SECOND, NO GATE 1 STAMP.** Entering a name on the watchlist stamps
`dd_at_entry` and **freezes Gate 1 under E12**. E109 already declined that
trade for five names whose views are registered and unwatched — ACN, AOS,
LII, RKT.L, ULTA — on exactly this ground. BOUV.OL is the sixth, and
freezing a catalyst window on a name 56% above its own provisional value
would buy nothing and cost the window.

**WHAT THIS DOES NOT DO.** It does not withdraw the value, retract the view
or supersede anything. The view stands as registered; the strike page stands
as PROVISIONAL; the seven read-backs in section 3 stand as the work that
would convert it. **What is deferred is the verification, not the record.**

**WHAT WOULD REOPEN IT.** The owner's *"if it ever approaches"*, which is
his judgement and not a number this file may set. Two mechanical notes for
whoever picks it up:

- **The floor is recomputed on any change of basis** (E108), so a new
  quarter re-decides which seven legs need reading — it does not inherit
  this list. Bouvet's next report is due around mid-November 2026 on its
  own quarterly cadence, and Q4 2025's operating cash flow leaves the
  window after the Q3 2026 report.
- **Nothing watches this name.** `vss run` reads the watchlist and BOUV.OL
  is not on it; `vss refresh` never sees it; only a screener run puts it in
  front of anybody, and it was #5 on 2026-09-05. **A name parked at INTAKE
  is a name nobody is alerted about**, which is the intended consequence of
  not stamping it and is stated here so it is not later mistaken for an
  oversight.
