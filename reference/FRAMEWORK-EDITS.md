# Proposed edits to FRAMEWORK.md v2.1

Each item is a place where a human reading it knows what you mean and a machine
does not. I have **not** applied any of these — every one changes a rule, and
they are your rules. Decide each, then hand this file plus FRAMEWORK.md to
Claude Code and tell it to apply the accepted items verbatim.

**2026-08-25 — D2 IS CLOSED.** All three changes are ruled — **E27** (WATCH
split), **E28** + **E29** (Method C as the engine, and the hurdle rate it runs
on), **E30** (Gate 3's two bands deleted). **The measurement freeze has lifted
and the 2026-09-08 deadline is moot.** The original directive follows.

**2026-08-25 — D2 GOVERNED the rebuild**, and is at the end of this file. It caps
the rebuild after the method review at **three changes and no more**, bars new
measurements while they are open, and sets a deadline of **2026-09-08**. It
supersedes **B3, B4 and B20**, each of which now carries a note pointing here.
Every other entry stands exactly as it did — D2 limits what may be OPENED next,
not what the entries above it say.

Items are ordered by how much damage the ambiguity causes.

---

## A. Structural (do these regardless)

### A1 — Scope §11 so it doesn't hijack build sessions

**Problem.** §11 opens "BINDING ON ANY AI USING THIS FILE". A coding agent that
reads this file in your repo will attempt to produce a regime block and action
list instead of writing code.

**Change the heading to:**

> ## §11 — OUTPUT CONTRACT (binding on ANALYSIS sessions)
>
> Applies when this file is used to conduct an analysis. It does **not** apply
> to engineering sessions that read this file as a specification. If you are
> building or modifying software, ignore §11 entirely.

### A2 — Remove the embedded standing instruction from §1.2

**Problem.** The line beginning "On receiving this file: Immediately list every
event in §9 marked 'pending catalyst'…" is a command to an analyst sitting
inside a document you now also use as a spec.

**Action.** Delete that paragraph from §1.2. Move it into your session prompt
where it belongs — it's a thing you ask for at the start of an analysis, not a
property of the framework.

### A3 — Move §9 out of the file entirely

**Problem.** §9 is a June 11 snapshot. It is now over two months stale and it is
the single most likely source of an agent asserting something false about your
current positions.

**Action.** Delete §9 from FRAMEWORK.md. Its contents become `watchlist.yaml`
(the live per-name fields) plus a dated `snapshots/2026-06-11.md` if you want
the history. Replace §9 with:

> ## §9 — PORTFOLIO STATE
>
> Not stored in this file. Live state lives in `config/watchlist.yaml`.
> Historical snapshots live in `snapshots/`. This section exists only to say
> so — never reintroduce dated holdings into the evergreen framework.

---

## B. Real ambiguities in the gates

### B1 — §3 Gate 1: "bulk of the decline"

**Problem.** "with the bulk of the decline occurring in the trailing 3–6 months"
— "bulk" has no number. Every implementation invents a different one.

**Proposed:**

> ≥ 60% of the peak-to-current decline occurred within the trailing 180
> calendar days, measured as
> `(close_180d_ago − last_close) / (high_52w − last_close) ≥ 0.60`.

*(Recommended default. Adjust the 0.60 if you have a view.)*

**DECIDED 2026-08-22 — Gate 1 is measured on TODAY's position; the timing
clause is context, not a third pass/fail limb.**

> Gate 1 PASSES when (a) the current close sits 15–50% below the 52-week
> closing high (bounds inclusive, per B2) and (b) the decline is attributable
> to an identifiable, dateable catalyst (headline + date). The "bulk of the
> decline in the trailing 3–6 months" clause is reported as context — the B1
> metric above is computed and shown — but does not by itself fail the gate.

Precedent: MSFT, 2026-08-21, **failed** Gate 1 on level (−11.2% on the day's
close) although it had printed a −34.9% trough three months earlier — the gate
measured the day's position then, and it measures the day's position now. The
0.60 rule proposed above is therefore **not adopted** as a pass/fail test.

*First applied: SAP.DE, 2026-08-22. Close 188.12 vs 52-week closing high 242.00
(2025-10-23) = −22.3%, inside the band; dateable catalysts: 2026-01-29 Q4 2025
results/2026 outlook (−16.1% on the day), the Feb–Apr 2026 US-software sell-off
(SAP −42.4% vs IGV −35.0% from 2025-10-23 to 2026-04-10), 2026-04-23 Q1 2026
(−6.1%). B1 metric −0.27 (the trailing 180 days are net up). Gate 1 = PASS.*

### B8 — §4.3 green flag: "active buyback at depressed prices"

**DECIDED 2026-08-22 — read by its spirit: a programme that executes at a
material discount to the 52-week high earns the flag.**

> The flag is awarded when an authorised programme is active and has executed
> purchases at a material discount to the 52-week closing high, even if
> purchases paused at the very lows. It is withheld when the pattern is the
> reverse — heaviest buying near the high, lightest at the low.

*Applied both ways. MSFT, 2026-08-21: **0** — the anti-pattern: the largest
quarter ($7,415m) was Oct–Dec 2025 near the $542.07 high, the smallest
($4,579m) was Apr–Jun 2026 containing the $352.83 low. SAP.DE, 2026-08-22:
**+1** — €10bn programme (Jan 2026 – Dec 2027), first tranche 16,280,097 shares
at average €161.16 ≈ €2.6bn completed by 2026-04-01, i.e. 33% below the
2025-10-23 high of 242.00; no purchases were reported for April–June (lows
128–168), which is noted but does not reverse the reading.*

### B2 — §3 Gate 1: band boundaries and which "high"

**Problem.** "15–50% from 52-week high" — is 15.0% a pass? Is the high the
intraday high or the closing high? The two differ by enough to flip a gate.

**Proposed:** append to Gate 1:

> Bounds are inclusive: exactly 15% and exactly 50% both PASS. The 52-week high
> is the highest daily **close** in the trailing 365 days, not the intraday high.

### B3 — §3 Gate 3: "revenue stable within ±2%"

> **CLOSED 2026-08-25 by E30 — the limb is DELETED**, so the question this
> entry asked never needed an answer. Demand fade moved to §4.2.1 on an organic
> basis. Kept as the record of a question the framework ran on for a month
> unanswered. See **E30** at the end of this file.

**Problem.** ±2% of what, over what comparison? YoY? Sequential? The worst
single quarter against the 8-quarter mean?

**Proposed:**

> Revenue: year-over-year growth ≥ 0% in at least 6 of the trailing 8 quarters,
> and no single quarter worse than −2% YoY.

*(This is a guess at your intent. If you meant sequential, say so — the
difference is large for seasonal names.)*

### B4 — §3 Gate 3: "gross margin band ≤ ±200bps"

> **SUPERSEDED 2026-08-25 by E30 — the band is DELETED and NOTHING mechanical
> replaces it.** The reversal of a four-day-old decision is real and is not
> softened; what survives is its OUTCOME, since no margin rule of any kind now
> fails MSFT. The 2026-08-21 decision below stays as the record of what was
> replaced and of the limb it flipped. See **E30** at the end of this file.

**Problem.** Each quarter within ±200bps of the mean (a 400bps total span), or a
total span of 200bps across all eight? Both readings are defensible.

**Proposed:**

> Gross margin: every one of the trailing 8 quarters within ±200bps of the
> 8-quarter mean, unless the deviation is explained by a quantified Class C
> event.

**DECIDED 2026-08-21 — the proposal above is adopted as written.** The band is
±200bps measured against the 8-quarter mean, per quarter, with a quantified
Class C event the only permitted exception. The rejected reading was a total
span of 200bps across all eight quarters.

*First applied: MSFT, 2026-08-21. 8-quarter mean gross margin 68.41%; largest
single-quarter deviation 121bps (FY26 Q4, 67.20%). Gate 3's margin limb PASSES.
Under the rejected span reading it would have FAILED — the span was 216bps
(69.35% FY25 Q1 to 67.20% FY26 Q4) — so this decision flipped the limb, and
with it Gate 3 and the §4.4 score, from 3 to 4.*

### B5 — §3 Gate 4: what happens when a discount input is missing

**Problem.** Gate 4 requires "at least 2 of 3". Forward P/E vs its own 5-year
median is the hardest datum in the entire framework to source. Today the file is
silent on whether a missing input counts as a failed one.

**This is the item I'd most want you to decide deliberately.** Proposed:

> A discount criterion with unavailable data is `DATA MISSING`, not FAIL.
> Gate 4 = PASS if ≥ 2 criteria are satisfied. Gate 4 = DATA MISSING if fewer
> than 2 are satisfied **and** ≥ 1 is DATA MISSING (i.e. the gate could still
> pass with better data). Gate 4 = FAIL only when ≥ 2 criteria were evaluated
> and not satisfied.

Without this, the default behaviour will be to treat your hardest-to-source
number as a failure and quietly kill good candidates.

**DECIDED 2026-08-21 — trailing-P/E proxy for an unobtainable forward multiple.**

When a historical forward P/E series cannot be retrieved, §5.1 Method A uses the
**5-year median of trailing P/E** in place of the 5-year median forward P/E.

Binding conditions on every use:

> The substituted multiple must be labelled **"proxy: trailing"** wherever it
> appears — in the workbook cell, in any output table, and in the §11 report.
> It carries a known **generous bias**: for a company with rising EPS a trailing
> multiple is mechanically higher than the forward multiple it stands in for, so
> the resulting fair value is biased **upward**. The bias must be quantified
> against a realised-forward comparator (same measurement dates, priced on the
> next fiscal year's actual EPS) and stated alongside the proxy, not left as a
> general caveat.
>
> Construction: diluted EPS from the primary filing (SEC XBRL for US filers) for
> five fiscal years, priced at five calendar year-end closes from a retrievable
> free source. Where the current calendar year is incomplete, the latest settled
> close substitutes for that year's year-end and must be labelled as such.
> Report all five (date, close, fiscal year, EPS, P/E) before taking the median.

**Scope note — this does not decide B5's original proposal.** B5 as written
above asks a different question: whether a missing Gate 4 discount input scores
as `DATA MISSING` or as `FAIL` (§3 Gate 4). The decision recorded here concerns
§5.1 Method A's *multiple* and does not answer it. Both stem from the same root
cause — forward P/E being the hardest datum in the framework to source — but
they are separate rules in separate sections. **B5's Gate 4 proposal remains
undecided.**

*First applied: MSFT, 2026-08-21. Five-year median trailing P/E **35.46**
(FY2022–FY2026 diluted EPS × calendar year-end closes 2022–2025 plus the
2026-08-20 settled close). Realised-forward comparator median 28.92, so the
proxy runs **+22.6%** high. Entered as workbook A7 labelled "proxy: trailing".*

*Second application: SAP.DE, 2026-08-22. Five-year median trailing P/E
**34.16** (FY2021–FY2025 IFRS diluted EPS from SEC 20-F XBRL × Xetra year-end
closes 2021–2025; all five fiscal years complete, so no settled-close
substitution). Realised-forward comparator median 45.69, so here the proxy runs
**25.2% BELOW** it — the bias is conservative, the opposite sign to MSFT,
because SAP's EPS path was not monotonic (4.46 → 1.94 → 5.20 → 2.65 → 6.10).
The owner attached a double note to the workbook cell: conservative against
realised forward, BUT the depressed FY2022/FY2024 earnings inflate the historical
multiples (49.7× and 89.2×) the median is drawn from — both readings stand.
Entered as workbook A7 labelled "proxy: trailing".*

*Third application: UNA.AS, 2026-08-22. Two constructions were possible because
FY2025 total diluted EPS (4.32) carries €1.73/share of non-cash demerger gain:
the literal reading (total EPS as first reported, each year-end price on the
same share basis as its EPS — the December-2025 8-for-9 consolidation is not in
the price series) gives a median of 17.41 with bias +0.6%; the
continuing-operations reading (FY2025 at 2.59) gives **20.61** with bias
**+8.3%** against the realised-forward comparator. The owner chose **20.61**,
the continuing-operations reading, for consistency with the SAP method (where
continuing-ops EPS was the robustness check), labelled "proxy: trailing" with
the +8.3% generous bias attached. Entered as workbook A7.*

---

### B6 — §4.4: how Gate 3 contributes to "gates passed"

**Problem.** Conviction = "(Gates passed: 0–5) + greens − softs". But Gate 3 is
six sub-rules. Does 5-of-6 count as a passed gate, or is Gate 3 all-or-nothing?

**Proposed:**

> Gate 3 counts as passed only if all six quality criteria PASS. A single FAIL
> fails the gate. Sub-criteria in `DATA MISSING` leave Gate 3 as DATA MISSING,
> which contributes 0 to the score and blocks a VALIDATED verdict.

---

### B7 — §4.2: materiality floor on the inventory limb

**DECIDED 2026-08-21.**

§4.2's seventh hard kill reads "Receivables **or** inventory growing > 1.5×
revenue growth rate for 2+ quarters". Applied literally, the inventory limb
fires on companies that carry almost no inventory, where the ratio is arithmetic
noise on a rounding-error balance.

> **The inventory limb of §4.2's receivables/inventory test applies only to
> companies whose inventory exceeds 2% of annual revenue.** Below that
> threshold the inventory limb is not evaluated and is recorded as
> NOT APPLICABLE — not as PASS and not as DATA MISSING. The receivables limb
> is unaffected and always applies.

**Rationale.** The rule exists to catch channel stuffing and demand fade at
product companies, where inventory is a real claim on working capital and a
real signal of sell-through. It is not informative where inventory is
immaterial to the business model.

**Worked both ways, so the threshold can be seen to bite in one direction only:**

| | Inventory | Annual revenue | Inventory / revenue | Limb applies? |
|---|---:|---:|---:|---|
| MSFT, FY2026 | 1,397m | 331,839m | **0.4%** | No — exempt |
| NIKE, FY2026 | 7,501m | 46,398m | **16.2%** | **Yes — still tested** |

NIKE's ratio has run 14.6%–18.0% across FY2022–FY2026 (SEC XBRL,
`us-gaap:InventoryFinishedGoodsNetOfReserves` over
`RevenueFromContractWithCustomerExcludingAssessedTax`). The exemption is
roughly eight times too small to reach it, so this amendment would **not** have
excused NIKE from the inventory test.

*Correction to the rationale as first stated: NIKE's inventory was given as
"~25% of revenue". On the revenue basis this rule uses it is **16.2%**
(FY2026). ~25% is close to the inventory/COGS ratio (~29%). The conclusion is
unchanged and not close — 16.2% clears the 2% floor by a wide margin.*

**First applied:** MSFT, 2026-08-21. FY26 Q3 and Q4 showed inventory growing
2.39× and 2.76× revenue growth — two consecutive quarters over the 1.5×
threshold, which under the unamended rule was a hard kill. Under this
amendment the limb is NOT APPLICABLE at 0.4% of revenue. The receivables limb
was tested and did not trigger (max 1.31×).

---

## C. Money-relevant ambiguities

### C1 — §6.4: which end of the −8% to −12% stop cap

**Problem.** "Daily close below the structural support floor, with a −8% to −12%
cap from blended entry." If the support floor sits 15% below entry, is the stop
at −8% or −12%? That's a material difference on a 5% position.

**Proposed:**

> The stop is the **higher** of (structural support floor) and (blended entry
> × 0.88) — i.e. the cap tightens the stop, never loosens it. If the support
> floor sits more than 12% below entry, the setup fails the 2:1 reward/risk
> test in §6.1 and should not be entered at that size.

*(This is the conservative reading. The alternative — cap at −12%, giving the
structure more room — is defensible; pick one and write it down.)*

**DECIDED 2026-08-22 — for volatile names the cap is read at its WIDE end.**

> For a name whose trailing-year drawdown has reached the order of 40–50%, the
> §6.4 cap is applied at **−12%**, not −8%.

Owner's rationale, verbatim: *"snäv stopp i namn med 47 %-drawdowns skakas ur av
brus; 165 ligger över entry 154"* — a tight stop in a name that has just shown
a 47% drawdown is shaken out by noise.

Scope note: this fixes only which end of the −8%/−12% band applies to a volatile
name. C1's general question — whether the stop is the higher of the support
floor and entry × 0.88 — remains undecided.

*First applied: SAP.DE, 2026-08-22. Trigger **165** = 188.12 (Xetra close
2026-08-21) × 0.88 = 165.55, rounded down. SAP's 52-week close-to-close drawdown
reached −47.0% on 2026-07-23 (242.00 → 128.32). The stop was set against the
current close rather than the ~154 blended entry (Jul 2026), so it sits above
entry. Entered as `stop_price: 165` in config/watchlist.yaml, clearing the
NO_STOP blocker on a HELD name.*

*Second application of B1 (Gate 1 on today's position): UNA.AS, 2026-08-22 —
close 54.59 vs 52-week closing high 62.92 (2026-02-24) = −13.2%, outside the
15–50% band, although the trough was −25.1% on 2026-06-04 and the decline is
recent (B1 metric 0.86). Gate 1 = FAIL on level, the MSFT precedent.*

*Second application, the complement: UNA.AS, 2026-08-22 — a LOW-volatility
name (1y annualised vol ≈21% vs SAP ≈41%; trough −25.1%; price within 1% of
both SMA50 and SMA200) takes the **tight** end: 54.30 (2026-08-20 close) × 0.92
= 49.96 → trigger **50.00** (Avanza). The wide-end alternative 47.80 would have
sat 0.65 above the 52-week low of 47.15 (2026-06-04), a support-floor reading;
not chosen. Entered as `stop_price: 50.00`.*

### B9 — §4.2.1: the revenue kill measures demand, not portfolio change

**DECIDED 2026-08-22.**

> The §4.2.1 hard kill ("revenue declining 2+ consecutive quarters") measures
> a loss of demand. A reported-revenue decline that is driven by disposals,
> demergers or currency translation, while organic / constant-currency
> growth is positive in every period of the window, does NOT trigger it. The
> decline and its components must be cited from the filing, and the organic
> growth series shown beside it.

**Rationale.** A company that sells or demerges a business reports lower
revenue by construction; so does one whose trading currencies weaken. Neither
is the demand fade the rule exists to catch, and killing on it would reject
every name in the middle of a portfolio reshaping.

*First applied: UNA.AS, 2026-08-22. Reported turnover fell year on year in four
consecutive quarters (Q2 2025 −4.6%, Q3 2025 −3.5%, Q4 2025 −2.7%, Q1 2026
−3.3%) and FY2025 −3.8%, stated as "(5.9)% from currency and (1.2)% from
disposals net of acquisitions" (FY2025 release p.3) after the Ice Cream
demerger of 2025-12-06; underlying sales growth was positive in all eight
quarters (3.0%–5.8%) and H1 2026 reported turnover was +0.5% with currency
−4.9%. 4.2.1 = NOT TRIGGERED. The same reading carries into §3 Gate 3's
revenue limb.*

### B10 — §4.2.7: a receivables jump explained by a disclosed gross-up

**DECIDED 2026-08-22.**

> Where the filing itself states that receivables (and payables) are grossed
> up by a transitional service arrangement, agency collection or similar
> pass-through, the §4.2.7 receivables limb does NOT trigger on that jump.
> The footnote must be cited, and the resulting DSO is recorded as a
> WATCH POINT, re-tested each period until the arrangement ends.

*First applied: UNA.AS, 2026-08-22. Trade and other current receivables
€10,201m at 30 June 2026 vs €7,691m a year earlier (+32.6%) against turnover
+0.5%; the H1 2026 cash-flow statement footnote (b): "Net working capital
includes the gross-up impact in receivables and payables arising due to the
transitional service arrangement between Unilever and The Magnum Ice Cream
Company" (trade payables +18.5% in the same period; the TSA runs "for a
maximum period of two years from the demerger", FY2025 release p.28). 4.2.7 =
NOT TRIGGERED. WATCH POINT: DSO 72 days at 30 June 2026 vs 53 at 31 December
2025 — re-test at the FY2026 results and until the TSA / Foods separation is
complete.*

### B11 — the ranking key reads one period and does not ask how long it is

**RAISED 2026-08-24 by the owner, out of backlog B-8. SETTLED BY E13
(2026-08-24) — choice (c), trailing twelve months.** Everything below is the
question as it stood; **E13 is the rule.**

**Problem.** The E6 key's two legs are `Gross Profit / Total Assets` and
`EBIT / enterprise value`. `latest()` returns the newest stored value of each
line and **nothing asks what LENGTH of period that value covers.** It has never
had to: the vendor path stores annual statements, so every ranked name has been
on one basis by construction. A hand-entered or appendix-read file need not be.

**The case that raised it.** `config/manual/PNDORA.CO.yaml`, written by
`vss appendix` from Pandora's Q2 2026 figures appendix, holds **fourteen
QUARTERS**. The quality leg reads:

| basis | gross profit | total assets | ratio |
|---|---:|---:|---:|
| the file's newest QUARTER (2026-Q2) | 5,808 | 29,232 | **19.9%** |
| the 2026-08-21 screener run, vendor ANNUAL figures | | | **87.0%** |

**Same company, same ratio, a factor of four apart, and neither number is
wrong.** One is a quarter's gross profit over the balance sheet; the other is a
year's. **The earnings-yield leg is worse**, because its denominator is not a
period at all: a quarter's EBIT divided into a market value of the whole
company understates the yield by roughly the same factor.

**The choices, and none is free:**

> **(a) Rank annual figures only.** A name whose store holds no annual period
> is not ranked, and is counted and named as such — the shape E6 already uses
> for a stale record and for a sector-exempt one. Costs coverage: PNDORA.CO
> would drop out of the ranking it currently sits at place 4 of.
>
> **(b) Require an annual period in a manual file before the name may be
> ranked.** The same outcome as (a), enforced at load rather than at rank, so
> the owner sees it when writing the file rather than when reading the CSV.
>
> **(c) Sum four quarters into a trailing twelve months.** **This project does
> not do it and `vss/appendix.py` is expressly forbidden from doing it** — a
> derived figure is a figure no filing states. FRAMEWORK §4.1 permits the
> derivation for quarterly figures *"where necessary, and say so"*, so this is
> not settled by precedent either way; it is a choice about whether the ranking
> key may hold a number nobody published.
>
> **(d) Rank them together and mark the basis.** The cheapest, and the one that
> puts a quarter and a year in one ordering. Only defensible if the ordering is
> read as review work rather than as a comparison — which is what E6 says it is,
> and is exactly the argument that would need testing before it is relied on.

**What is NOT in question.** That the period LENGTH must be RECORDED beside a
ranked figure is a defect, not a judgement, and is backlog **B-8** — nothing
today writes it down, so the CSV cannot say which rows are on which basis
whatever is decided here. B-8 gets fixed regardless.

**Section 5 is unaffected.** It reads the period it is handed, whose label is on
the entry, and refuses on unverified figures. This is the RANKING key's question
alone.

### B13 — do the borrowing fields exclude lease liabilities, or contain them?

**RAISED 2026-08-24 by the owner, out of the same PNDORA.CO run as B11 and
separate from B12. SETTLED BY E14 (2026-08-24) — choice (a), the borrowing
fields EXCLUDE leases.** Everything below is the question as it stood;
**E14 is the rule.**

**Problem.** `config/manual/<TICKER>.yaml` carries
`financial_liabilities_current` and `financial_liabilities_noncurrent`, each
documented as nothing more than *"Balance sheet."*, **and** `lease_liabilities`
as a field of its own. Having the third field at all IMPLIES the first two
exclude leases. Nothing says so.

**And the two readings are both already in the file.** The appendix map fills
the borrowing fields from the balance sheet's `Loans and borrowings` line,
which under IFRS 16 CONTAINS the lease liabilities — Pandora states it in as
many words, Note 3.3, p.123 of the 2025 annual report: *"Lease liabilities are
recognised in loans and borrowings."* The owner's reading of the same annual
report takes the notes' own split instead, where the two are stated apart
(Section 4 overview, p.129: `Loans and borrowings, non-current 7,729` above
`Lease liabilities, non-current 4,193`).

The arithmetic is not in doubt, and it is the whole of the problem:

| | non-current | current | source |
|---|---:|---:|---|
| what the appendix map put in the fields (2025-Q4) | 11,922 | 3,102 | balance sheet `Loans and borrowings` |
| what the annual-report reading would put there | 7,729 | 1,627 | notes, borrowings alone |
| the difference | 4,193 | 1,475 | `Total lease liabilities 5,668`, note 3.3 |

7,729 + 1,627 + 5,668 = **15,024** = 11,922 + 3,102. **The same two fields hold
figures on one definition, and the reading that was about to be written into
them is on the other.**

**WHAT IS NOT IN QUESTION: one field cannot carry two definitions inside one
file.** Whichever way this goes, a file holding both is not a file anything can
compute a net debt from — and §5.1 C's net-debt bridge is what both fields exist
to feed.

**The choice, and it is open:**

> **(a) The borrowing fields EXCLUDE leases.** Then `lease_liabilities` is a
> figure in its own right and the three add up to the balance-sheet line. The
> appendix map for PNDORA.CO is **WRONG** and must be re-pointed at the notes'
> split rather than at the consolidated balance-sheet line.
>
> **(b) The borrowing fields INCLUDE leases**, as the balance sheet presents
> them. Then `lease_liabilities` becomes a **MEMO** field — recorded so the
> composition is visible, and it **must never be added to** the borrowing
> fields, because it is already inside them.

**This reaches every IFRS 16 filer with material leases, not PNDORA.CO alone.**
Any issuer whose balance sheet consolidates borrowings and leases into one line
presents the same choice, and **the appendix map may be wrong for any of them**
— the mapping was made against one company's sheet and the ambiguity is in the
SCHEMA, not in that company.

**What turns on it.** Section 5 assumption **A2** — *"do lease liabilities count
as debt?"* — is a switch the owner throws per name. It can only be thrown if the
two quantities are separable in the file. Under (b) they are separable only
where the issuer also discloses the lease total; under (a) they always are, at
the cost of a mapping that must find the notes rather than the balance sheet.

**Neither the schema nor the map settles it today.** The schema says of
`lease_liabilities` only that *"Assumption A2 decides whether they count as
debt. One line under IFRS 16"*, which is true on both readings. The map says of
the borrowing fields that *"UNDER IFRS 16 THIS FIGURE ALREADY CONTAINS THE LEASE
LIABILITIES"*, which records what it did without claiming it was right.

### B14 — a figure a company publishes only once a year has nowhere to go

**RAISED 2026-08-24, out of the attempt to record PNDORA.CO's FY2025 figures.
SETTLED BY E15 (2026-08-24) — an `annual:` block beside `periods:`.** Everything
below is the question as it stood; **E15 is the rule.**

**Problem.** A manual file's `periods:` holds one entry per fiscal period at the
resolution the company reports. `config/manual/PNDORA.CO.yaml` holds fourteen
QUARTERS. But a company does not publish everything quarterly, and the figures
it publishes once a year are exactly the ones §5 is short of.

**The case.** The owner read nine FY2025 figures out of Pandora's 2025 annual
report — diluted EPS 67.9 (note 4.2, p.131), the diluted weighted average share
count 77,189,151 (same note), shares outstanding 79,000,000 (note 4.1, p.130),
total lease liabilities 5,668 (note 3.3, p.123), the borrowings split 7,729 /
1,627 (note 4.3, p.132), EBITDA 10,316 (five-year summary, p.14), finance costs
1,149 (p.100) and the leverage ratio 1.3x (p.38) — and **none of them could be
written down.**

**Two independent refusals, both correct.**

```
period 2025-FY: 2025-FY is a 12-month period but the ticker reports
quarterly, which stores Q1/Q2/Q3/Q4 periods only
```

and, even had the label been allowed, the **overlap guard** forbids `2025-FY`
beside `2025-Q1..Q4`. Flipping `reporting_frequency` to `half_yearly` to admit
the label invalidates all fourteen quarters instead.

**And splitting the figures does not rescue it.** Six of the nine are
balance-sheet INSTANTS at 31 December 2025 and would sit correctly on the
existing `2025-Q4` entry, whose `period_end` already is that date. **Three are
annual flows** — diluted EPS, EBITDA, finance costs — and have nowhere at all.
A file cannot hold them by rearrangement.

**WHAT WAS NOT IN QUESTION.** The overlap guard is right. A `2025-FY` entry
inside `periods:` alongside its own quarters would count those months twice in
every trailing window, which is precisely what E13's trailing twelve months
reads. Nothing here proposed relaxing it.

**The choices as they stood:** put the annual figures on the newest quarter and
accept that a quarter entry holds year figures; drop the quarters and keep the
year, losing the TTM basis; keep them in a second file, which the ticker-name
check and the one-file-per-ticker read forbid; or **give the schema somewhere
else to put them** — which is what E15 does.

### B15 — a net share count the accounts never print

**RAISED 2026-08-24 out of the PNDORA.CO annual-report reading. SETTLED BY E16
(2026-08-25) — the subtraction is permitted, under conditions.** Everything
below is the question as it stood; **E16 is the rule.**

**Problem.** The schema field `shares_outstanding_period_end` is defined in
three words — *"Net of treasury shares."* — and a company may state only the
ISSUED count and the TREASURY count separately, **never their difference**.
The field's own definition then names a figure that appears nowhere in the
accounts, and the schema says nothing about what to do.

**The case.** Pandora, note 4.1 of the 2025 annual report, p.130:

| | at 31 December 2025 |
|---|---:|
| shares issued (`Balance at 31 December`) | **79,000,000** |
| treasury shares (`Balance at 31 December`) | **4,415,553** |
| **net of treasury** | **printed nowhere** |

The note corroborates itself — *"At 31 December 2025, treasury shares accounted
for 5.6% of the"* share capital, and 4,415,553 / 79,000,000 is 5.59% — but the
net count, 74,584,447, is not a figure the report states.

**And it had already bitten.** On 2026-08-24 the owner supplied 79,000,000 for
`shares_outstanding_period_end`. That is the ISSUED count, wrong against the
field's own definition by 4,415,553 shares — about 5.6% on every per-share
figure §5 would divide by it.

**Three options and the schema preferred none:** enter the issued count and be
wrong against the definition; compute issued minus treasury, which is a
derivation, and `vss/appendix.py` is forbidden from deriving while a hand entry
is forbidden nowhere; or leave it DATA MISSING, which is what E14 prescribes for
the analogous liability case. **There was also no field to hold the treasury
count**, so the second option lost its own working: the result would have no
page it is printed on, which the `page:` requirement assumes every figure has.

**Not the same as B13.** There the ambiguity was what a field MEANS. Here the
meaning is clear and the figure is absent.

### B16 — E15's shadowing rule compares field names alone

**RAISED 2026-08-25, out of the first PNDORA.CO file to carry both blocks.
SETTLED BY E17 (2026-08-25) — a quarter never displaces a year.** Everything
below is the question as it stood; **E17 is the rule.**

**Problem.** E15 settles that where a figure exists in both `annual:` and
`periods:`, **`periods:` wins**. The rule as implemented compares FIELD NAMES
and nothing else. It cannot tell a quarter from a year.

**The case.** `config/manual/PNDORA.CO.yaml`, 2026-08-25, the first file to
carry both blocks:

| | figure | covers |
|---|---:|---|
| `ebitda` in `periods:`, 2026-Q2, from the xlsx appendix | **2,133** | three months |
| `ebitda` in `annual:`, FY2025, from the annual report | **10,316** | twelve months |
| what the load reports | *"the annual entry is ignored; `2026-Q2` supplies it"* | |

**A quarter displaces a year, and the two differ by 4.84×.** Worse, the entry
beside it — `net_debt_ebitda` **1.3**, read from the management review, p.38 —
is a leverage ratio struck on the ANNUAL figure. So the file answers `ebitda`
with a quarter and `net_debt_ebitda` with a year, and nothing says the two
stand on different bases.

**This is B-8's finding in a new place.** There the ranking key read one period
and never asked how long it was; E13 settled that with a trailing twelve months
and a recorded period length. The section 5 layer has the same blindness in its
own shape: E15's rule reasons about names where it needs to reason about
lengths.

**WHAT WAS NOT IN QUESTION.** That `periods:` should generally win. E15's
reason holds — a file must not be able to answer the same question twice — and
nothing here proposed reversing it.

### B17 — two more nets the accounts do not print

**RAISED 2026-08-25, holding PNDORA.CO's finance figures. SETTLED BY E18
(2026-08-25) — both follow E16's rule.** Everything below is the question as it
stood; **E18 is the rule.**

**Problem.** `net_finance_costs` **carries no definition at all** — its
`FieldSpec` states only who reads it, *"Gate 3's interest-coverage limb"*.
`net_interest_paid` carries one that defines a net **by subtraction**,
*"Interest paid less interest received"*, **with no operand fields either**.
Both are B15's shape: a net the accounts do not print.

**The case.** Pandora's 2025 annual report states each pair, and neither net:

| | printed | where |
|---|---:|---|
| Finance costs | **1,149** | income statement p.100; note 4.6 p.138 |
| Finance income | **279** | income statement p.100; note 4.6 p.138 |
| → `net_finance_costs` wants | **870** | **printed nowhere** |
| Finance costs paid | **1,009** | cash flow statement p.104 |
| Finance income received | **174** | cash flow statement p.104 |
| → `net_interest_paid` wants | **835** | **printed nowhere** |

**And the two are not each other.** One is what was CHARGED, on the income
statement, read by §3 Gate 3's interest-coverage limb. The other is what was
PAID, on the cash flow, deducted by §5.1 C's FCF basis 3. Different figures
from different statements, 35 apart here, and neither derivable from the other.

**`net_interest_paid` had been in the schema since the start**, defining a net
by subtraction of two figures the schema gave it no fields for. It was
invisible because nobody had tried to fill it.

### B18 — a §5 expression may straddle the two blocks, and nothing looks

**RAISED 2026-08-25, measuring every §5 expression against PNDORA.CO's file.
SETTLED BY E19 (2026-08-25) — one twelve-month basis for the whole run.** The
drafted ruling below was a PROPOSAL and was NOT what was adopted: E19 replaces
"both legs must match" with a single basis from which matching follows. **The
five measurements are kept because E19's reasoning refers to them.**

**Problem.** Three expressions the §5 workbook forms combine a `periods:` leg
with an `annual:` leg. All three are **three months against twelve, six months
apart on the end date**, and nothing in the project looks at them.

| expression | `periods:` leg | `annual:` leg |
|---|---|---|
| **interest coverage** (§3 Gate 3) | `operating_income` · 2026-Q2 · 3m | `net_finance_costs` · FY2025 · 12m |
| **FCF basis 3**, interest leg (§5.1 C) | `operating_cash_flow` · 2026-Q2 · 3m | `net_interest_paid` · FY2025 · 12m |
| **EBITDA reconciliation** | `depreciation_amortisation` · 2026-Q2 · 3m | `ebitda` · FY2025 · 12m |

**Neither existing rule reaches them.** `ratio_states`' one-period rule governs
the SIX ratios formed in code, and holds for all six; it does not reach a
workbook expression. **E17 does not reach them either**: E17 governs a field
present in BOTH blocks, and these are fields present in ONE block each,
combined across the boundary.

**MEASURED CONSEQUENCE, and it straddles a hard kill.** PNDORA.CO's interest
coverage reads **1.7×** — a quarter's operating profit of 1,463 over a year's
net finance costs of 870 — against §3 Gate 3's threshold of **≥ 5×**. On
matched FY2025 bases it is **8.9×** (operating profit 7,783 over the same 870).
**One reading fails the gate and the other passes it comfortably**, and the
difference is entirely which period each leg came from.

#### The drafted ruling — PROPOSED, NOT DECIDED

> **Every §5 expression, workbook as well as code, requires both legs on the
> same period basis — the same LENGTH and the same PERIOD END.**
>
> Where they differ the expression is **NOT MEANINGFUL**: never annualised and
> never scaled. **§5 derives nothing** — E13's trailing-twelve-months exception
> stays confined to the ranking key, which is the only place in this project
> that may sum periods at all.
>
> **The report names the two bases when it refuses**, so a reader sees which
> two the expression could not be formed from rather than only that it was not
> formed.

#### What each of the three would need to form on a matched FY2025 basis

Every field below is already in the file for **all four 2025 quarters**, so
nothing has to be sourced afresh — but under this draft §5 may not sum them,
so each has to be entered in `annual:` as the figure the annual report prints.

| expression | already annual | would have to ENTER `annual:` FY2025 |
|---|---|---|
| interest coverage | `net_finance_costs` (computed from its pair) | `operating_income` |
| FCF basis 3 | `net_interest_paid` (computed from its pair) | `operating_cash_flow`, `capex_ppe`, `capex_intangibles`, `proceeds_from_disposals_ppe`, `lease_payments_capital` |
| EBITDA reconciliation | `ebitda` | `operating_income`, `depreciation_amortisation` |

**And moving `operating_income` has a consequence worth seeing first.** Under
E17 a year beats a quarter wherever §5 resolves a field, so an FY2025
`operating_income` would be preferred EVERYWHERE — including the operating
margin and §5.1 Method B, whose other leg (`revenue`) is a 2026-Q2 figure.
Fixing interest coverage would put two expressions that agree today into the
straddle this entry is about, unless `revenue` enters `annual:` with it.

#### What stays untestable even if all of them are entered

- **The whole net-debt family, and with it §3 Gate 3's leverage limb and §5.3's
  tier test.** `financial_liabilities_current`, `financial_liabilities_noncurrent`
  and `lease_liabilities` are in the file for **one period only** — 2025-Q4,
  where the owner entered them from the annual report's notes — and §5 reads
  2026-Q2, so all three are DATA MISSING today. They would have to enter
  `annual:` as well.
- **Assumption A2**, *do lease liabilities count as debt*, for the same reason:
  E14 made it answerable by splitting the line, and the split is in a period §5
  does not read.
- **The net share count.** `shares_issued_period_end` and
  `treasury_shares_period_end` are also in 2025-Q4 only, so E16's subtraction
  does not fire and every per-share figure §5 divides by is DATA MISSING.
- **`other_current_financial_assets`** is **nowhere in the file** — Pandora's
  balance sheet does not present the concept — so assumption A1 has no answer
  from this source at all, on any basis.
- **`operating_income_adjusted`, `diluted_eps_adjusted`, `revenue_yoy`,
  `operating_cash_flow_pretax`, `noncurrent_derivative_assets_on_debt`** are
  likewise absent everywhere: not stated by this issuer in the documents read.

#### SECOND MEASUREMENT — the proposal's larger consequence

**The draft above is not a rule about three expressions. It is a rule about the
WHOLE EVALUATION.** If every expression needs both legs on one basis, and
expressions share fields, then a §5 run needs **ONE BASIS FOR THE WHOLE
EVALUATION, CHOSEN UP FRONT** — not resolved field by field as it is today.
Resolving per field is what produced the three straddles, and no per-field rule
removes them: fixing interest coverage by moving `operating_income` to the
annual block moves operating margin and Method B INTO a straddle, because they
share that field. **The basis is a property of the run, not of a figure.**

So the question the owner faces is not *"how should these three be repaired"*
but *"which basis does a §5 run on PNDORA.CO stand on"*. Measured on the file
as it stands, with **stock lines resolving at the basis period end** and **flow
lines from the stated period of that length**:

| | **(a) FY2025** — 12m to 2025-12-31 | **(b) 2026-Q2** — 3m to 2026-06-30 |
|---|---|---|
| §5 expressions that FORM | **11 of 22** | **8 of 22** |
| DATA MISSING | 11 | 14 |
| §3 Gate 3, leverage (ND/EBITDA) | **forms** — 2025-Q4 stocks + FY2025 EBITDA | missing |
| assumption **A2** (leases in or out of debt) | **forms** — 2025-Q4 | missing |
| **E16** net share count | **forms** — 2025-Q4 | missing |
| §3 Gate 3, interest coverage | missing (`operating_income`) | missing (`net_finance_costs`) |
| §5.1 Method A (multiple × EPS) | **forms** — FY2025 | missing (`diluted_eps`) |
| §5.1 Method B (peer × EBIT) | missing (`operating_income`) | **forms** — 2026-Q2 |
| §5.1 C, FCF bases 1 and 2 | missing | **form** — 2026-Q2 |
| §5.1 C, net debt and equity value | **form** — 2025-Q4 | missing |

*(22, not 23: gross profitability is the RANKING key's leg, not a §5
expression.)*

**The two bases are close to complements.** (a) answers the BALANCE SHEET and
the per-share questions — net debt, A2, the share count, Method A — because the
owner's annual-report reading landed at 2025-12-31, which is also 2025-Q4's
period end. (b) answers the CASH FLOW and margin questions, because the
appendix carries those quarterly and the annual report's figures were not
entered as annual flows. **Neither basis answers Gate 3's interest coverage**,
and each is missing the other's half.

**AND THE FRESHNESS RULE CUTS THE OTHER WAY.** §1.2 is a hard stop: *"Earnings
data: must include the most recently reported quarter."*

| | newest income statement | age at 2026-08-25 | includes 2026-Q2, the most recently reported quarter? | §1.2 |
|---|---|---:|---|---|
| (a) FY2025 | ends 2025-12-31 | 237 days | **NO** | **FAILS the hard stop** |
| (b) 2026-Q2 | ends 2026-06-30 | 56 days | YES | passes |

Both are inside `fundamentals.MAX_REPORT_AGE_DAYS` (550), which is the
screener's staleness gate and a different question.

**So the basis that answers most of §5 is the one §1.2 forbids**, and the basis
§1.2 requires answers eight expressions of twenty-two and neither Gate 3 limb.
That tension is the finding; nothing here resolves it.

*Corroboration, recorded 2026-08-25: the H1 2026 report carries an **FY 2025
column** beside its Q2 and H1 columns, and it reproduces the annual report's
figures EXACTLY -- revenue 32,549, operating profit 7,783, finance costs 1,149,
finance income 279, finance costs paid 1,009, finance income received 174. The
FY2025 figures already in `annual:` therefore stand on two independent
documents. They were NOT re-entered from this one: a figure is recorded once,
from the document the owner read it in.*

#### THIRD MEASUREMENT — E17 is too broad

Writing the H1 2026 report's Q2 column into the file produced a state in which
**the operands and the net they make disagree**:

```
finance_costs_period    1,149     annual FY2025, preferred by E17
finance_income_period     279     annual FY2025, preferred by E17
net_finance_costs         291     computed from 2026-Q2's 325 − 34
```

1,149 − 279 is **870**, not 291. The same for `net_interest_paid`: the operands
read 1,009 and 174, the net computes **460** from the quarter's pair.

**This is NOT an implementation gap. It is evidence that E17 is too broad.**
E17 says a year ALWAYS displaces a quarter, and that holds only when THE OTHER
LEG IS A YEAR. Now that the H1 report prints a Q2 column, **325 and 34 are
stated figures AT THE §5 PERIOD**, and 1,149 / 279 are not the preferred basis
— they are **the wrong one**. E17 was ruled when the quarter was the only thing
in `periods:` and the year the only thing that could answer; it reads the
collision as *which figure is better* when the question is *which figure
belongs to the period being evaluated*.

**Proposed correction, NOT DECIDED:**

> **`periods:` is used whenever it can answer at the §5 basis; `annual:` fills
> only what `periods:` cannot.**

That inverts E17's default without discarding it: where `periods:` has nothing
at the basis, the annual entry still answers, which is what E15 was for. What
goes is the preference for a year over a quarter that IS the period under
evaluation.

#### FOURTH MEASUREMENT — a stock has no length, and the drafted rule cannot see it

**The draft requires both legs on the same period LENGTH. A stock has no
length**, so every stock-over-flow ratio passes the test trivially, whatever
the flow is. Net debt at 2026-06-30 over a THREE-MONTH EBITDA passes the
drafted rule and reads **7.33×** against §3 Gate 3's cap of 2.5× and §4.2.5's
hard kill at 3.5×. **It trips a hard kill on a measurement artefact.**

Net debt, E14 form, at 2026-06-30: 1,076 + 9,184 + 6,291 − 908 = **15,643** —
which the report itself corroborates on p.37, *"NIBD, incl. capitalised leases,
amounted to DKK 15.6 billion at the end of Q2"*.

| EBITDA used | length | net debt / EBITDA | Gate 3 ≤ 2.5× | §4.2.5 kill > 3.5× |
|---|---|---:|---|---|
| 2026-Q2 as stated | **3m** | **7.33×** | **FAIL** | **TRIPS** |
| 2026-Q2 × 4 | 3m annualised | 1.83× | pass | no |
| four quarters to 2026-06-30 | 12m, not a stated figure | 1.50× | pass | no |
| FY2025 | 12m | 1.52× | pass | no |
| *the figure the file states* | *FY2025, at 2025-12-31* | *1.3×* | *pass* | *no* |

**Every §5 expression that divides a stock by a flow, or is compared to a
threshold calibrated on an ANNUAL flow:**

| expression | stock leg | flow leg, current length | what it reads |
|---|---|---|---|
| **net debt / EBITDA** — §3 Gate 3 (≤2.5×), §4.2.5 (>3.5× kill), §5.3 tier | net debt at 2026-06-30 | `ebitda`, **12m** today via E17; **3m** under the draft | **1.52× today; 7.33× under the draft** |
| **EV / EBIT** — §5.1 Method B's peer multiple | `enterprise_value` | `operating_income`, **3m** | not computable: the market block is EMPTY in this file |
| **market cap / FCF** — §3 Gate 4, FCF yield ≥ 1.5× sector median | `market_cap` | FCF basis 1, **3m** (1,831 − 324 − 130 = 1,377) | not computable: market block empty. At 3m the yield would read a quarter of the annual one |
| **market cap vs discounted FCF stream** — §5.1 C reverse DCF | `market_cap` | FCF basis 1, **3m** | the implied growth solves against a stream a quarter of its true size |
| **multiple × EPS** — §5.1 Method A | the A7 multiple, a 5-year median trailing **P/E** | `diluted_eps`, **12m** today (FY2025) | correct today by accident: the multiple is annual by construction (FRAMEWORK-EDITS B5) and the EPS happens to be annual too |

**And flow-over-flow is not safe either, only less unsafe.** Interest coverage
is a ratio of two flows, so it survives a change of length approximately — but
not exactly, and here it straddles its own threshold:

| | operating profit | net finance costs | coverage | Gate 3 ≥ 5× |
|---|---:|---:|---:|---|
| both 3m (2026-Q2) | 1,463 | 291 | **5.0×** | passes by 0.03 |
| both 12m (FY2025) | 7,783 | 870 | **8.9×** | passes |

**The contrast worth seeing: the RANKING KEY already solved this and §5 has
not.** E13 forces every flow leg to a trailing twelve months and takes the
stock at the window's end, precisely so that `gross profit / total assets` and
`EBIT / enterprise value` cannot be read on a quarter. §5 has no equivalent
rule, and the draft in this entry does not supply one — matching LENGTHS is
not the same requirement as matching a stock to an ANNUAL flow.

#### FIFTH MEASUREMENT — the framework's thresholds are annual, and it never says so

**Searched FRAMEWORK.md for the words `annual`, `annualised`, `annualized`,
`TTM`, `LTM`, `trailing twelve` and `twelve month`. ZERO OCCURRENCES, in the
entire file.** Every threshold below assumes a twelve-month flow, and not one
section states the assumption. It has held only because the vendor path stores
annual statements and §4's windows are counted in quarters, so nothing has ever
handed §3 or §5 a flow of another length. A manual file can.

**A consistent quarterly basis does not rescue them.** It makes all of the
stock-over-flow thresholds wrong by the same factor — roughly four — which is
worse than an inconsistency, because it is invisible: every name fails together
and the ordering between them looks untouched.

| § | threshold | shape | only meaningful against a 12-month flow? | does the section say so? |
|---|---|---|---|---|
| 3 Gate 3 | **Net debt/EBITDA ≤ 2.5×** | STOCK / flow | **YES** — 7.33× on a quarter, 1.52× on a year | **NO** |
| 4.2.5 | **Net debt/EBITDA > 3.5×** (hard kill) | STOCK / flow | **YES** — same figures trip the kill on a quarter | **NO** |
| 3 Gate 3 | **Interest coverage ≥ 5×** | flow / flow | **Calibrated annually.** Scale-invariant in principle, but measured 5.0× on the quarter against 8.9× on the year — it straddles its own threshold | **NO** |
| 3 Gate 4 | **Forward P/E ≥ 20% below its 5-year median** | STOCK / flow | **YES** — a P/E on a quarterly EPS is four times the annual one | **NO.** B5's A7 proxy specifies annual EPS; §3 Gate 4 itself does not |
| 3 Gate 4 | **EV/EBIT or P/S below peer median** | STOCK / flow | **YES** | **NO** |
| 3 Gate 4 | **FCF yield ≥ 1.5× sector median** | STOCK / flow | **YES** | **NO** |
| 5.1 B | **peer-median EV/EBIT × company EBIT, ±10%** | STOCK / flow, then × flow | **YES** — and the error enters TWICE, in the multiple and in what it multiplies | **NO** |
| 5.1 C | **reverse DCF: 10y horizon, terminal 2.5%, discount 9–10%** | STOCK vs a flow STREAM | **YES** — the rates are annual by construction, so the first-year FCF must be too | **NO.** The rates are given as annual; the FCF's length is not mentioned |
| 5.1 A | **5-year median forward P/E × NTM consensus EPS** | multiple × flow | **YES** | **NO** in §5.1. Only FRAMEWORK-EDITS **B5** fixes the proxy to annual EPS, and that is a note about the substitute, not about the method |
| 4.3 | **SBC > 30% of FCF**; **FCF conversion ≥ 90% of net income** | flow / flow | scale-invariant IF both legs share a length — which nothing requires | **NO** |
| 4.3 | **customer concentration > 20% of revenue** | flow / flow | scale-invariant, same caveat | **NO** |

**Thresholds that are NOT exposed**, and why, so the list is not read as wider
than it is: §3 Gate 3's *revenue stable within ±2%* and *FCF positive in ≥6 of
8 quarters*, §4.2's *2+ consecutive declining quarters*, *2+ guidance cuts in 4
quarters*, *3+ EPS misses in 8 quarters*, *CEO and CFO within 12 months*, and
*receivables growing >1.5× revenue growth for 2+ quarters* are **counts, signs
or growth-rate comparisons whose window the section states in quarters**. §3
Gate 3's *gross margin band ≤ ±200bps* is a margin, so scale-invariant, but its
band is calibrated on quarterly dispersion — which backlog **B-7** already
records, for the half-yearly case. §5.3's tiers and margins of safety, §6's
technical triggers and §7's sizing rules contain no flow.

**SO THE DRAFT NEEDS A SECOND LIMB.** Requiring both legs to match is
necessary and not sufficient: matched at three months, `net debt / EBITDA`
reads 7.33× and trips a hard kill written for a year. The draft as it stands
would make that state legal. **Naming the length is the missing half** — and
naming it in the FRAMEWORK, not only in the manual loader, since it is §3 and
§5's numbers that carry the assumption.


### C2 — §5.3: tier decision order

**Problem.** Tier 1 requires conviction ≥ 7 **and** fortress balance sheet
**and** secular tailwind. Tier 2 is conviction 5–6 **or** cyclical. A name with
conviction 8 that is cyclical matches neither definition cleanly.

**Proposed:** replace the tier table's prose with an ordered test:

> Evaluate in order, first match wins:
> 1. Re-labeled thesis (mean-reversion / turnaround-adjacent) → Tier 3
> 2. Conviction ≤ 6 **or** cyclical exposure → Tier 2
> 3. Conviction ≥ 7 and non-cyclical → Tier 1
>
> Regime adjustment shifts one tier stricter; Tier 3 is the floor and does not
> shift further.

### C3 — §1.2 vs practical freshness

**Problem.** §1.2 requires prices ≤ 1 trading day old. Strictly implemented
against a naive calendar, every Monday morning run blocks on Friday's close.

**Proposed:** append to §1.2:

> "≤ 1 trading day" means the most recent session on the relevant exchange
> calendar. Weekends and market holidays do not make a close stale.

**DECIDED 2026-08-26 — ruled by the owner after REVIEW-4, as the proposal
reads: sessions on the relevant exchange calendar, and the gate's limit stays
at THREE such sessions (`rules.MAX_CLOSE_AGE_TRADING_DAYS`).** The ruling
replaced a calendar-day count that blocked every held name's stop check on
the first trading day after any two-day holiday (REVIEW-4 report A 4.2).
Implemented in commit `da9d34d` (2026-08-26 00:39, trading days, naive
calendar) and completed by the SCREENER-REVIEW-3 build, item 3 (the exchange
calendar itself, `vss/calendars.py`, `config/exchange_calendars.yaml`); the
three-on-calendar reading and its relation to §1.2's "≤ 1 trading day" are
recorded as **E47**.

*Correction of record: `reference/SCREENER-DESCRIPTION-2026-08-26.md` §2.1
and §7 dated this decision 2026-08-21. No record supports that date — the
REVIEW-4 reports of 2026-08-25 still call C3 undecided, and the commit that
implements it says "ruled by the owner after REVIEW-4". This entry, the code
comment at `vss/rules.py` and E47 all carry 2026-08-26.*

### C4 — §6.4: exit on a fair-value gap, not only on reversion

**DECIDED 2026-08-21.**

§6.4's profit discipline is written entirely in terms of reversion to fair
value: trim 25–50% at FV_base, exit above FV_bull. It has no rule for the case
where price runs so far past the triangulated range that the *forward* return
from here is worse than the index — regardless of whether a pre-set reversion
level has been touched.

> **Exit when the fair-value gap makes expected return worse than the index
> even in the bull scenario.** This complements the reversion exit in §6.4; it
> does not replace it. The test is forward-looking: compare expected return
> from the current price to the index alternative, using FV_bull — not
> FV_base — as the numerator. If even the bull case does not beat the index,
> the reversion level is irrelevant and the position is sold.

**Rationale.** A reversion level set months earlier is a statement about where
the thesis was, not about what the capital can earn next. Once price exceeds
FV_bull, holding is a bet that the valuation work was wrong, which is not a
thesis. The index is the relevant benchmark because this framework governs a
satellite sleeve sitting beside an index core (§7) — the alternative to holding
a satellite is always the core, never cash.

**First applied: MSFT, 2026-08-21 — and it superseded a live reversion level.**
The standing reversion exit for MSFT was 510–530. This rule fired below that
band and closed the position anyway. The §5.2 weighted range (method C 0.90 /
method A 0.10) was:

| | FV | 
|---|---:|
| bear (conv 50% + g 7%; A8 17.90) | 222 |
| base (conv 62.5% + g 10%; A8 19.96) | **323** |
| bull (conv 75% + g 13%; A8 23.60) | **465** |

MSFT traded at 478.53–486.36 on the day of the exit. **The price was above
FV_bull of 465**, so expected return was negative on the framework's own most
optimistic scenario, with the 510–530 reversion band still untouched. §4.4 had
also scored the name at 4 — "drop or watchlist" — with no §5.3 tier qualifying
and therefore no maximum buy price in existence.

*This item retires the 510–530 reversion level for MSFT; it is not carried
forward.*

*Second application — TEST REPORTED, DECISION THE OWNER'S: UNA.AS, 2026-08-22.
§5.2 weighted range (method C 0.90 at FCF growth 2/4/6%, r 9.5%, on FCF basis 1
6,987, net debt 25,961; method A 0.10 at 70.49): bear 37.0 / base 43.5 / bull
51.0. Price 54.59 (2026-08-21 close) is **+7.0% above FV_bull** at the
framework's 9.5% — the C4 condition (even the bull case does not beat the
index) is met at that rate; at r 9.0% FV_bull is 55.5 and the price sits 1.6%
below it; at r 10.0% FV_bull is 47.2. The owner's margin note stands: a uniform
9.5% is the least flattering rate for a defensive name. No exit decision is
recorded here; the owner takes it. Tier 2 MBP 30.45 and fv_base 43.5 both sit
below the 50.00 stop.*

*Third application: SAP.DE, 2026-08-22 — tested in the §6.4 reassessment and
did NOT fire (188.12 was 15% below the then FV_bull 220). Fourth application:
SAP.DE, 2026-08-26 — FIRED on the re-strike (187.20 vs FV_bull 174.30); sold in
full. The horizon this item left unstated is settled by E42.*

---

## D. Small consistency fixes

- **§0 rule 2** says every criterion gets PASS / FAIL / **DATA MISSING**, but
  §3 says only "Score each PASS/FAIL". Make §3 say all three.
- **§5.1 Method A** needs "NTM consensus EPS" flagged as a MANUAL input — it is
  not obtainable free and code must never estimate it.
- ~~**§7** caps at "max 5 concurrent satellite positions" and §3 screens
  "universe → 5 names". Different fives; worth a parenthetical so nobody
  conflates the screening shortlist size with the portfolio position cap.~~
  **CLOSED 2026-08-21 by v2.3**, which removed the max-5-positions rule. Only
  one five remains — §3's screening shortlist — so there is nothing left to
  conflate and no parenthetical needed.
- **Version block:** bump to 2.2 and add a changelog line noting the §9 removal,
  so a future you knows why the portfolio state vanished.

---

## E. Tooling deviations (the screener)

Items here are not ambiguities in the framework. They are places where a tool
built against the framework carries a label that is not exactly what the label
says, recorded so the gap is visible in the same file as the rules rather than
only in a machine-readable sidecar.

### E1 — `omxs-large-mid` is an APPROXIMATION of Nasdaq Stockholm Large+Mid

**DECIDED 2026-08-22 — approved as an approximation, on condition that the
deviation is recorded here and not only in the file's metadata.**

> The universe list `config/universe/omxs-large-mid-<date>.csv` is **not**
> Nasdaq's official Large Cap + Mid Cap segment membership. It is the Yahoo
> equity screener for exchange STO, cut at Nasdaq's own Mid Cap floor of
> **EUR 150m** (Large Cap is >= EUR 1bn, Mid Cap EUR 150m-1bn), converted to
> SEK at an EUR/SEK rate read at build time and recorded in the file's
> `.meta.json`. The label "OMXS Large+Mid" is therefore approximate and must
> be read as such wherever it appears.

**The size of the gap, as built 2026-08-22: 316 names against roughly 270 in
the official segment.** The surplus is Small Cap names whose market cap has
risen through the EUR 150m floor without Nasdaq having moved them between
segments — Nasdaq reviews segment membership annually, whereas a market-cap cut
re-decides every time it is run. The cut also does not separate the Main Market
from First North, both of which carry the `.ST` suffix on Yahoo.

**Why not the official list.** Nasdaq's segment file sits behind a login at
`indexes.nasdaqomx.com`; the old `nasdaqomxnordic.com` data feed now redirects
to marketing pages. No free machine-readable source for the official segmentation
was found.

**Rationale for recording it here.** A silent drift between a label and its
contents is exactly what this framework is built to disallow. The file's
`.meta.json` carries `"approximation": true` and `vss screen --universe-report`
prints `APPROXIMATION` beside the file, but a metadata flag is read by the tool,
not by the person deciding. This entry is for the person.

*Contrast, for calibration: `sp500` (503/503 from the index constituent list)
and `stoxx600` (600/600 Equity rows from the physically replicating full-size
iShares EXSA holdings file) are NOT approximations and carry no such entry.*

### E2 — screener filter 2 uses §4.2.5's hard kill, not Gate 3's cap

**DECIDED 2026-08-22 — the coarse filter tests at 3.5x. Gate 3's 2.5x is
still applied by hand, where it belongs.**

> The screener's filter 2 rejects a name on leverage only above
> **net debt/EBITDA 3.5x**, the §4.2.5 hard kill. It does NOT apply §3
> Gate 3's 2.5x cap. Gate 3 remains unchanged and is evaluated manually in
> the §3 chain with the whole picture in view, including the sector norms it
> refers to.

**Rationale, in the owner's words:** 2.5x was the single place in the
proposed configuration where the coarse filter could lose a name the manual
chain would have kept. Gate 3's cap is a *gate*, decided with the full
picture; §4.2.5's 3.5x is a *hard kill* — unambiguously too much — and a hard
kill is the right altitude for a step that never reads the report.

**The case that decided it: UNA.AS ran net debt/EBITDA of 2.27–2.48x**,
squeezing just under 2.5. That margin must not be settled by a filter with no
access to the filing. Under a 2.5x screening cap a name sitting a few
hundredths inside the gate would be lost before anyone looked at it.

*This is a rule about the SCREENER, not about the framework. §3 Gate 3's cap
is untouched at 2.5x and §4.2.5's hard kill is untouched at 3.5x; E2 only
records which of the two a coarse pre-screen is allowed to enforce.*
Entered as `max: 3.5` in `config/screener_filter2.yaml`, which also records
2.5x under `not_chosen`.

### E3 — Real Estate joins financials as NOT APPLICABLE on the leverage limb

**DECIDED 2026-08-22 — recorded in B7's form, as a dated exemption with a
stated reason, rather than as a silent line in a config file.**

> The net debt/EBITDA limb is **NOT EVALUATED** for issuers whose source-list
> sector is `Financial Services` or `Real Estate`. The outcome is
> **NOT APPLICABLE** — not PASS, not FAIL, and not DATA MISSING.

**Rationale.** §3 Gate 3 already excludes financials from this limb and sends
the analyst to sector norms, which a machine has none of. Real Estate is
added on the same logic: property is borrowed against asset value, not
against EBITDA, so the ratio measures the wrong thing rather than measuring
it badly. The exemption is about what the metric *means* for the business
model, exactly as B7's inventory exemption is.

**Precedent.** FRAMEWORK-EDITS B7, decided 2026-08-21, established the third
outcome. Its shape is followed here: a named scope, a stated reason, and a
recorded application.

**Discriminator.** The source list's own sector string, never a guess from
the name — the same rule the universe exclusions follow. A row whose sector
is absent is not exempt; it is evaluated, and lands in DATA MISSING if the
figures are not there.

*Worked in one direction, for calibration: the exemption removes an
unanswerable question, it does not excuse a leveraged operating company. An
industrial at 4.0x is still FAILED by E2's 3.5x; only the two named sectors
skip the limb.*

### E4 — a screener limb with no data passes the name through

**DECIDED 2026-08-22.**

> When filter 2 cannot evaluate a limb, the name is **passed through and
> marked**, never dropped. The count of untested names is reported in its own
> column, separately from the value-based rejections.

**Rationale.** DATA MISSING is a third state throughout this system. Gate 3's
real FCF test — positive in ≥ 6 of 8 quarters — is not computable from the
screener's source for a material share of the universe, so rejecting on
absence would discard names on **yfinance's coverage rather than on company
quality**. The manual chain fetches the figure from the filing.

*Entered as `on_missing_action: pass_through`. The alternative, `reject`,
remains available and lands such names under "rejected on MISSING data",
never mixed with the value-based rejections.*

### E5 — the screener's ranking key: Greenblatt, two components

> **SUPERSEDED 2026-08-22 by E6.** The QUALITY LEG defined below —
> `ROIC = EBIT / (net working capital + net PP&E)` — was replaced by gross
> profitability after the review in `reports/screener-review-2026-08-22.md`
> found that it carried a name it did not implement (K1) and that its top was
> a set of near-zero denominators rather than a set of good businesses (K2).
> **The price leg, the rank sum, the tie rule, the separate one-legged section
> and the DATA MISSING rule are unchanged and still in force** — sub-questions
> (a), (b) and (d) below are live text, not history. Only (c) and the ROIC
> definition are superseded.
>
> **This item is not deleted, and that is deliberate.** It records what the key
> was between 2026-08-22 and the same day's re-decision, which is what a reader
> of `data/screener_runs/2026-08-21/` needs in order to understand the numbers
> in it. See E6.

**PROPOSED 2026-08-22. DECIDED 2026-08-22** — the key below is adopted as
written, with the four open sub-questions answered as recorded at the end of
this item. Standing rule 6 of the screener brief was met: the text existed and
was approved before any of it was coded.

---

#### The key

For each candidate surviving filter 2, compute two numbers:

> **Return on capital**
> `ROIC = EBIT / (net working capital + net tangible fixed assets)`
> where `net working capital = current assets − current liabilities`
> and `net tangible fixed assets = net PP&E`
>
> **Earnings yield**
> `EY = EBIT / enterprise value`

Rank the candidates **separately** on each — highest ROIC is rank 1, highest
earnings yield is rank 1 — **sum the two ranks**, and sort ascending. Lowest
combined rank first.

**No weighting. No thresholds. No score.** The sum of two ordinal positions is
the whole key.

---

#### Why two components and not Piotroski's nine

The probe of 2026-08-22 (`tools/probe_ranking_fields.py`) established that
every Piotroski input is available: net income, operating cash flow, gross
margin, revenue, total assets, long-term debt and shares outstanding all
return at 93–100% for the latest annual year, and year-over-year barely
degrades — the only YoY-specific loss is long-term debt, 96.7% → 93.3%. So
Piotroski is not rejected for want of data. It is rejected for want of
legibility.

**A 0–9 score cannot be debugged.** When a name the owner recognises as
rubbish appears near the top, a nine-limb integer gives no way to see which
limb carried it. Two components can be judged by eye: one number for how
efficiently the business turns capital into operating profit, one for how
cheaply that profit is being sold. Each is separately checkable against the
company's own accounts.

**The quality leg may be widened later**, once the key has been watched in
practice and there is evidence about how it behaves. Widening a leg that has
been observed is a different act from starting with nine unobserved ones.

---

#### EBIT: the alias set, and the substitution that is forbidden

> **THE ORDER BELOW IS SUPERSEDED 2026-08-23 BY E8.** The three labels are
> still the alias set and `ebitda` is still forbidden; what changed is that
> the order is now set on what the labels MEAN rather than on which is most
> often present, that the fiscal year is settled before the label, and that
> two labels for one year end differing by a round power of a thousand make
> the EBIT DATA MISSING. The paragraph is kept as written because
> `data/screener_runs/2026-08-21/ranking-2026-08-22-E6.csv` was produced under
> it.

> EBIT is taken from the annual income statement, from the FIRST of these
> labels present: **`EBIT`**, then **`Operating Income`**, then
> **`Total Operating Income As Reported`**.

The strict `EBIT` label is not universal. Measured: 14 of 15 US candidates
carry it; **ACN does not**, and ACN is in the candidate set. The alias set
returned 100% on both samples probed.

*That measurement is about COVERAGE, and coverage was the only question asked.
E8 records what happened when someone asked what the three labels mean.*

> **`ebitda` from the quote summary is NEVER a substitute for EBIT.**

It is a different number — it adds back depreciation and amortisation, which
for a capital-intensive business is most of the gap between the two — and
substituting it would silently change the numerator of ROIC and of the
earnings yield alike, in a direction that flatters exactly the heaviest
balance sheets. A test holds this line: the ranking code may not read the
`ebitda` field at all.

---

#### An absent line is not a zero

> Where a line item is missing from the statement, the quantity is
> **DATA MISSING**. It is never read as zero, anywhere in the ranking code.

The case that establishes it: **ASM.AS carries no `Long Term Debt` line
because the company has no long-term debt.** Absence there happens to mean
zero. But absence of `Current Liabilities` on a bank means the balance sheet
is not classified, and absence of `Gross Profit` on an infrastructure owner
means the concept is not presented — neither of those is zero, and code that
cannot tell the three apart will produce a confident number from nothing.

A candidate missing an input its component needs does not get a zero for that
component; it gets no rank on it, and is handled under the exemption rule
below.

---

#### Financials and Real Estate: NOT APPLICABLE on ROIC

> The ROIC component is **NOT EVALUATED** for issuers whose source-list sector
> is `Financial Services` or `Real Estate`. Those candidates are ranked on the
> **earnings yield alone**.

Same reasoning as E3 gives for the leverage limb: net working capital and net
PP&E do not describe how a bank or a property owner is capitalised, so the
ratio measures the wrong thing rather than measuring it badly. The probe
confirmed the mechanical side — MANTA.HE returns neither current assets nor
current liabilities, because a bank does not present a classified balance
sheet.

**This affects 61 of the 402 candidates — 15.2%: 33 Real Estate and 28
Financial Services.** That is not a corner case, and the report must say so on
every run and mark every affected row. Ranking a name on one leg is worse than
ranking it on two. It is stated, never hidden.

---

#### Open sub-questions, which the owner must decide with the rest

**(a) How a one-legged candidate joins a two-legged list.**

**DECIDED 2026-08-22 — a SEPARATE SECTION.**

> A candidate that cannot be ranked on ROIC is ranked among the other
> one-legged candidates on earnings yield alone, and printed as its own list.
> It is never interleaved with the two-legged ranking and never given a
> synthesised ROIC placing.

Owner's rationale: the alternative invents an assumption about where the name
would have placed on ROIC, and **an invented number inside the one ordering
this tool produces is exactly what must not exist**. A separate section also
serves as a standing reminder that those names are less well judged than the
others.

*The rejected reading was: combined rank = 2 × the earnings-yield rank.*

**(b) Currency. This one blocks the earnings yield as written.** EBIT comes
from the statements in `financialCurrency`. Market capitalisation and
enterprise value come from the quote summary in the **quote currency's major
unit** — verified by `marketCap / sharesOutstanding` reproducing price ÷ 100
for a London name quoted in pence. **The two currencies differ for 60 of the
402 candidates (14.9%)**, and 39 candidates are quoted in GBp against accounts
in GBP or USD.

`EBIT / EV` therefore crosses two currencies for one candidate in seven and is
wrong by the exchange rate. It does **not** cancel the way filter 2's limbs
did — those compared two figures from one statement.

Three ways out, none of them free:

  1. **Convert, with the rate recorded.** One FX rate per currency pair
     (roughly ten pairs, not one per ticker), fetched at run time and written
     into the run's manifest, exactly as `tools/build_universe.py` records
     EUR/SEK. Cheap, auditable, and introduces the first FX dependency in the
     screener — the one phase 1 flagged for tier C's floors and phase 3 avoided.
  2. **Rank within currency.** Rank candidates only against others reporting
     in the same currency, then merge on percentile. No FX, but it changes what
     the ranking means.
  3. **Exempt the mismatched.** Rank them on ROIC alone. Loses 15% of the list
     to a data-plumbing problem rather than to anything about the businesses.

Recommended: **(1)**, with the rate and its date printed in the report.

**DECIDED 2026-08-22 — CONVERT, with the rate in the manifest.**

> Enterprise value is converted into the reporting currency at a rate fetched
> **once per run, per currency pair** — about ten pairs, not one per ticker —
> written into the run's manifest and printed in the report. Every ranking is
> then exactly reproducible from its own record.

Owner's rationale: merging on percentile within currency compares apples with
pears, and exempting the mismatched throws away a seventh of the list over a
plumbing problem.

**Two binding conditions, both from the owner:**

> 1. The rate is **saved per run** and **reported in the output**. A ranking
>    whose FX basis is not on the record is not reproducible.
> 2. The **GBp/GBP scaling gets its own test.**

On the second: market capitalisation and enterprise value are quoted in the
**major** unit of the quote currency, so a London name quoted in GBp carries
an EV in GBP, not in pence. Treating it as pence would divide the enterprise
value by a hundred and multiply the earnings yield by the same, sending every
British name to the top of the list. In the owner's words, *that is the bug
that does the most damage and shows the least.* 39 of the 402 candidates are
quoted in GBp.

**(c) A non-positive ROIC denominator.** Net working capital is routinely
negative for retailers and other float-funded businesses, so
`NWC + net PP&E` can be zero or negative, at which point the ratio is not a
return on anything.

**DECIDED 2026-08-22 — adopted as written.** A denominator ≤ 0 makes ROIC
**NOT MEANINGFUL**; the candidate is handled under the same rule as the sector
exemption and appears in the separate earnings-yield section. The count is
reported. It is never clamped, floored or sign-flipped.

**(d) Ties.**

**DECIDED 2026-08-22 — adopted as written.** Equal values share the better
rank (competition ranking, 1-2-2-4), and an equal combined rank is broken by
ticker alphabetically — a stated arbitrary rule rather than an unstated one.

---

#### What this key is, and what it is not

> **This is the only place in the entire tool where an ordering arises.**

Every other step is a filter with a pass, a fail, or a third state, and every
report so far has said in as many words that its output is an order and not a
ranking. Here it genuinely is a ranking, and it performs the 100:1 selection:
402 candidates to the 3–5 names that become PIPELINE.

It is still not a recommendation. The output is **review work**: names entered
as PIPELINE **without `mbp` and without `fv_base`**, after which the whole §5
chain — fair value, margin of safety, maximum buy price — is run by hand. A
high rank means the name is worth the hours, nothing more.

The look-ahead limitation of phase 3 carries through unchanged: EBIT and the
balance-sheet figures are the accounts as published at fetch time, while the
price and market capitalisation belong to their own date. Any replay pairs
them across time and the report must keep saying so.

### E6 — the quality leg is gross profitability, not Greenblatt's ROIC

**PROPOSED 2026-08-22. DECIDED 2026-08-22, superseding E5's ROIC component.**
Standing rule 6 was met again: this text and its measurement were shown and
approved before a line of it was coded. The review of
`reports/screener-review-2026-08-22.md` (findings K1 and K2) is accepted. E5
stays in this file in full, marked SUPERSEDED: the history is the point.

---

#### What changes

> **Quality leg.** For each candidate surviving filter 2,
> `gross profitability = Gross Profit / Total Assets`,
> after Novy-Marx (2013), *The Other Side of Value*, JFE 108(1).
> Both figures are taken from the annual statements, from the strict labels
> `Gross Profit` and `Total Assets`. There is no alias set: unlike EBIT and
> unlike current liabilities, these two labels were present for every name in
> the store that presented the concept at all.
>
> **Price leg.** `EY = EBIT / enterprise value`, unchanged, with the EBIT alias
> set unchanged, the FX conversion unchanged and the forbidden `ebitda`
> substitution unchanged.
>
> **Aggregation.** Rank separately on each, highest first, sum the two
> placings, sort ascending. Ties, the separate one-legged section and the
> DATA MISSING rule are all unchanged from E5(a)–(d).

Everything E5 decided about *how the two numbers are combined* survives. Only
what the first number **is** changes.

---

#### Why — K1 and K2, and why K1 alone would not have been enough

**K1: the label was not the contents.** E5 defined `NWC = current assets −
current liabilities` and called the result Greenblatt's return on capital.
Greenblatt excludes excess cash from working capital and short-term
interest-bearing debt from current liabilities. The word "Greenblatt" stood in
`ranking.py`'s docstring, in E5's heading, in `SCREENER.md`, in the run
manifest and in the note written into `watchlist.yaml`. Recomputing the same
run with cash outside the denominator replaces the whole top-5. **This is the
same failure E1 exists to forbid — a silent drift between a label and its
contents — occurring at the one step where it costs the most.**

**K2 is why the repair is not "subtract the cash".** The denominator is a
difference between large numbers and goes to zero for float-funded,
asset-light businesses. Measured over the 314 names ranked on both legs:

> The **13 names whose capital employed is less than half a year's EBIT hold
> ROIC placings 1 through 13**, without exception. Not a coincidence — for a
> given EBIT, ROIC is monotone in `1/denominator`, so ranking on ROIC is in
> part ranking on how small the denominator is. OTIS: current assets 6,501,
> current liabilities 7,656, net PP&E 1,297 MUSD → denominator **142 MUSD**
> against EBIT 2,219 MUSD, ROIC 1563%, placing 1 of 314. A **1.9% increase in
> its current liabilities** moves it from placing 1 to disqualified.

Excluding cash makes that worse, not better: it pushes 37–45 further names
toward the pole. The pole is in the *shape* of the denominator, and the only
repair is a different denominator.

**Total assets is always large and always positive.** Measured over all 394
post-collapse candidates: **0 have a non-positive total assets figure**,
against **19 of 334 non-exempt names (5.7%) whose capital employed was ≤ 0**
and therefore NOT MEANINGFUL under E5(c). The cash question stops mattering:
cash sits inside total assets for every company, on one side only, and no
longer pushes a name in one direction on the quality leg while pulling it the
other way through EV on the price leg.

Range, same population, as a measure of how far the tail reaches:

| leg | lowest | highest |
|---|---:|---:|
| ROIC (E5) | −680.8% | **+1562.7%** |
| GP/TA (E6) | −0.6% | +104.9% |

A **negative numerator is still ranked, not excluded**: VEFAB.ST at −0.6% is a
business whose cost of revenue exceeded its revenue, which is a fact about the
business and belongs at the bottom of the list. That is the opposite of a
negative denominator, which is a fact about the arithmetic. E5(c)'s
NOT MEANINGFUL rule is kept in the code for a total-assets figure ≤ 0; it did
not fire on this run.

**On the evidence for the leg itself.** The review's part 1 measured that the
Magic Formula's surviving premium comes from the price leg — Gray & Carlisle
(2012) and Davydov, Tikkanen & Äijö (2016) both find EBIT/EV *alone* beating
the two-factor formula. Gross profitability is the quality measure with the
strongest independent evidence behind it and, for our purposes, the one whose
denominator cannot be driven to zero. This entry is not a claim that the new
leg adds return. It is a claim that it measures something, which the old one
did not.

---

#### Coverage — measured on the actual candidate set, not on the earlier probe

The earlier field probe (`tools/probe_ranking_fields.py`, 93.3%) sampled a
different population. Measured over the **394 candidates this run actually
ranked**, and over the **334 of them that are not sector-exempt**:

| line | all 394 | non-exempt 334 |
|---|---:|---:|
| **Total Assets** | 394 (100.0%) | 100.0% |
| **Gross Profit** | 376 (95.4%) | **330 (98.8%)** |
| EBIT (alias set) | 386 (98.0%) | — |
| Current Assets / Current Liabilities | 382 (97.0%) | — |
| Net PPE | 394 (100.0%) | — |

**The new leg is better covered than the old one, not worse.** Four non-exempt
names lose the quality leg to a missing `Gross Profit` line — ITV.L, RMV.L,
SWEC-B.ST, ULTA — against nineteen that lost it under E5 to a non-positive
denominator. Those four fall into the earnings-yield-only section under E5(a),
exactly as the nineteen did. Nothing new is needed to handle them.

*The 18 of 394 that lack `Gross Profit` are 13 Financial Services, 4 of the
non-exempt names above, and 1 Real Estate — the concentration is in the sector
where the concept is not presented, which is E5's own ASM.AS argument:
absence there is not zero.*

---

#### Financials and Real Estate: the exemption stays, on a narrower ground

E3 and E5 exempted `Financial Services` and `Real Estate` for two reasons that
now come apart.

**The mechanical reason is gone.** E5 cited MANTA.HE returning neither current
assets nor current liabilities, because a bank does not present a classified
balance sheet. Total assets is presented by every name in the store — 394 of
394, banks included. Nothing is now uncomputable.

**The economic reason stands, and it is measurable.** For a bank, total assets
*is* the loan book and gross profit is not the concept the accounts present;
for a property owner, total assets is the portfolio at fair value and gross
profit is rent less direct property cost. The ratio is computable and not
comparable. Dropping the exemption and ranking all 374 names on one scale:

| sector | on the two-legged list | best GP/TA placing | median placing | in the quality top-50 |
|---|---:|---:|---:|---:|
| Real Estate | 31 | 273 of 374 | 354 | **0** |
| Financial Services | 14 | 159 of 374 | 322 | **0** |

**Not one of those 45 names reaches the quality leg's top 50.** Including them
would not be judging them, it would be sorting them last as a class on a ratio
that does not describe them — and then letting that artefact decide that no
bank and no REIT is ever worth review work. The exemption keeps them where E5
put them: in their own section, ranked on the price leg alone, and said to be
less well judged.

**The literature runs the same way.** Novy-Marx's own gross-profitability
tests are run on a sample that excludes financial firms — the standard
convention of dropping one-digit SIC 6, which removes both banks and real
estate. Greenblatt excludes financials outright.

**And the choice costs almost nothing either way, which is why it should be
made on meaning rather than on outcome.** Retaining the exemption against
dropping it: **top-5 identical (5/5), top-20 19 of 20**. The one difference is
BEI.DE against RVRC.ST at the twentieth place.

*Utilities are NOT added to the exemption here. Greenblatt excludes them; the
reason he gives is regulated return, not an unmeasurable denominator, and
gross profit over total assets is a perfectly ordinary quantity for a utility.
Adding them would be a new judgement, not a consequence of this one, and it
belongs in its own entry if it is wanted.*

---

#### THE MEASUREMENT — top 20 under both legs, same run, same data

Same snapshot (`2026-08-21`), same 394 post-collapse candidates, same twelve FX
rates read back out of `data/screener_runs/2026-08-21/ranking-manifest.json`
rather than re-fetched, so **the only variable is the quality leg**. The
reproduction was checked first: recomputing the old key from the store returns
the run's own ranking name-for-name and its earnings yields to a relative
difference of `0.00e+00`.

```
    # | OLD (E5: ROIC)                              new# | NEW (E6: GP/TA)                            old#
      |  ticker       sum  Qr EYr     ROIC     EY         |  ticker       sum  Qr EYr  GP/TA     EY
    1 | TE.PA          26  24   2    121%   24.4%    165  | UHS            12   2  10   101%  13.5%     57
    2 | BATS.L         37   4  33    446%    9.6%    137  | LULU           22  13   9    74%  15.4%     37
    3 | RKT.L          39  10  29    285%   10.1%     44  | DECK           23   6  17    86%  11.7%     22
    4 | EVD.DE         47  20  27    143%   10.2%    133  | PNDORA.CO      31   4  27    87%  10.5%     10
    5 | ERIC-B.ST      56  45  11     85%   13.4%     17  | BETS-B.ST      43  40   3    57%  22.2%      6
    6 | BETS-B.ST      57  54   3     78%   22.2%      5  | JD.L           56  36  20    61%  11.0%    125
    7 | DG.PA          59  27  32    116%    9.9%     49  | KMAR.OL        57  25  32    65%  10.0%     19
    8 | FGR.PA         59  43  16     91%   12.0%      8  | FGR.PA         63  47  16    54%  12.0%      8
    9 | AUTO.L         60   7  53    332%    8.5%     12  | NREST.ST       67   7  60    85%   8.4%     23
   10 | PNDORA.CO      65  40  25     95%   10.5%      4  | BUCN.SW        68  46  22    54%  10.9%    117
   11 | ADBE           66   5  61    419%    8.1%     11  | ADBE           78  14  64    72%   8.1%     11
   12 | GSK.L          71  23  48    131%    8.8%     37  | AUTO.L         84  28  56    64%   8.5%      9
   13 | ZZ-B.ST        77  36  41     99%    9.2%     13  | ZZ-B.ST        87  44  43    54%   9.2%     13
   14 | ACN            81  47  34     84%    9.6%     50  | AFRY.ST        92  12  80    76%   7.7%     34
   15 | RMV.L          81   3  78    638%    7.6%     --  | LISP.SW        94  93   1    41%  27.6%     54
   16 | CTSH           85  70  15     62%   12.2%     34  | HWDN.L        101  26  75    64%   7.8%    138
   17 | IT             86  12  74    259%    7.7%     27  | ERIC-B.ST     106  95  11    40%  13.4%      5
   18 | NOVO-B.CO      86  49  37     82%    9.4%     18  | NOVO-B.CO     112  73  39    46%   9.4%     18
   19 | KMAR.OL        94  64  30     68%   10.0%      7  | RVRC.ST       113   5 108    86%   6.7%     42
   20 | CMCSA         104  97   7     49%   16.9%     41  | AD.AS         115  61  54    50%   8.6%    113
```

`new#`/`old#` is where that name lands on the other leg. `--` means it is no
longer on the both-legs list at all.

| overlap | |
|---|---|
| **top-5** | **0 of 5** |
| top-10 | 3 of 10 — BETS-B.ST, FGR.PA, PNDORA.CO |
| top-20 | 9 of 20 — ADBE, AUTO.L, BETS-B.ST, ERIC-B.ST, FGR.PA, KMAR.OL, NOVO-B.CO, PNDORA.CO, ZZ-B.ST |

**The five current PIPELINE names are the five in the left column's top five,
and none of them survives.** That is the size of this edit, stated in the one
unit that matters.

**Read the movements, not just the overlap.** The names that fall furthest are
exactly the ones K2 named: RMV.L (ROIC 638%, quality placing 3) leaves the
list; BATS.L 2 → 137; TE.PA 1 → 165, a name whose EUR 3bn net cash was raising
its earnings yield to placing 2 while the same cash pushed its ROIC placing to
24. The names that rise — UHS, LULU, DECK, JD.L, HWDN.L — are ordinary
operating businesses with high gross margins on modest balance sheets, which is
what the leg is supposed to find.

**Population, and an honest correction to "the price leg is unchanged":**

| | E5 | E6 |
|---|---:|---:|
| ranked on both legs | 314 | **329** |
| earnings yield alone | 70 | 55 |
| not rankable at all | 10 | 10 |

`competition_ranks` is computed over the two-legged population, so a
**population that grows from 314 to 329 moves the earnings-yield placings even
though the earnings-yield definition did not change.** The movement is small
and it is one-directional — TE.PA 2 → 2, BETS-B.ST 3 → 3, CMCSA 7 → 7,
BATS.L 33 → 35, IT 74 → 78 — but the sentence "the price leg is unchanged" is
true of the *definition* and false of the *numbers*, and this file should not
be the place where that distinction is left to the reader.

The 15 net additions are the **19 names E5 sent to NOT MEANINGFUL** — among
them IMB.L, the tobacco name the review paired against BATS.L to show that the
sign of a small difference was deciding PIPELINE eligibility — **less the four
that lose the quality leg to a missing `Gross Profit` line** (ITV.L, RMV.L,
SWEC-B.ST, ULTA).

**The two legs agree less than before**, which is what a second leg is for:
Spearman rank correlation between the quality placing and the earnings-yield
placing is **+0.25 under E5 and +0.14 under E6**. The review's observation
still holds and is worth keeping in view — no name is good on both legs, so the
key selects "middling on quality and cheap", not "good and cheap".

---

#### What this measurement is not

**It is not the list the re-run will produce.** Four repairs from the same
review are scheduled after this one, and every one of them can move names:

- **K6 (same period in one ratio).** `latest()` is called independently per
  line, so `Gross Profit` and `Total Assets` can come from different fiscal
  years — measured, **2 of 374**: AUTO.L (GP 2024-03-31 against TA 2026-03-31)
  and BAB.L (GP 2022-03-31 against TA 2026-03-31). AUTO.L stands at **12 in
  the new top-20 above and the guard will remove it**. The table above is
  taken *without* that guard, because the guard is not built yet.
- **K5 (STALE must block).** COLO-B.CO and BWY.L are STALE and are on the
  two-legged list under both legs. Neither is in either top 20, so this table
  is not affected — but the re-run's counts will be.
- **K4 (price-series sanity).** Flags fall in filter 1, upstream of the whole
  candidate set, so the re-run's population may differ from these 394.
- **K7 (FX from the manifest).** This measurement already reads the rates back
  out of the manifest, which is how the coming `--fx-from-manifest` will work;
  a live re-run without that flag will fetch fresh rates and move the price leg
  slightly.

**Novy-Marx has a lagged-assets variant. It is not used here.** Gross profit
and total assets are taken from the same statement date — the plain reading —
and K6 will make that a requirement rather than a coincidence.

---

*Calibration, in one direction: this entry does not claim the new key picks
better companies. It claims the old key's quality leg ranked closeness to a
division by zero, and that the new one ranks a ratio whose denominator is
present for every company in the universe and cannot go to zero. Whether the
names it produces are worth the hours is still decided by hand in §5, on every
one of them, exactly as before.*

### E7 — `Gross Profit` is a presentation choice, not a standard

**DECIDED 2026-08-23 — recorded as a KNOWN LIMITATION of E6's quality leg, and
NOT given a mechanical fix.** The review of
`reports/screener-review-2-2026-08-23.md` (finding L1) is accepted. E6 is not
superseded and the leg is not changed: gross profitability stays
`Gross Profit / Total Assets`, with the same strict labels and the same
sector exemption. What is added is the sentence E6 did not contain.

---

#### The limitation

> **Where the line called "cost of revenue" is drawn is an accounting
> presentation choice, not a standard.** E6 assumes `Gross Profit` names one
> concept across the universe. It does not. For a labour-intensive service
> business whose income statement presents no cost of goods sold at all, the
> feeder's answer to "gross profit" is *revenue minus something small*, and
> the resulting GP/TA is not comparable with a manufacturer's or a software
> company's. The number is arithmetically correct and economically not the
> same quantity.

This is E5's *an absent line is not a zero* one step further out. There the
danger was a line that is not there; here it is **a line that is there and is
not the concept its label names.** E1 exists to forbid a silent drift between
a label and its contents, and this is one — not in our code, but in the data
our code reads, which is the harder half to see.

---

#### The case: UHS, rank 1 of the 2026-08-21 run, against its own 10-K

From `data.sec.gov` XBRL, `us-gaap`, fiscal 2025 (CIK 0000352915):

| the line, as UHS itself tags it | MUSD |
|---|---:|
| net revenues | 17,364.8 |
| **labour and related** | **8,084.6** |
| supplies | 1,659.0 |
| other operating | 4,860.2 |
| operating lease | 148.2 |
| residual (D&A and the rest) | 618.7 |
| **total operating expenses** | **15,370.8** |
| operating income | 1,994.0 |
| total assets | 15,527.6 |

The store's `Gross Profit` for UHS is 15,705.8 MUSD, so the feeder's "cost of
revenue" is **exactly 1,659.0 MUSD — `SuppliesExpense`, and nothing else.**
The figure agrees to the last digit. **Materials are 10.8% of what it costs to
run the company.** The 8,084.6 MUSD of wages that are a hospital's actual
production cost sit BELOW the gross-profit line. A hospital operator with a
90.4% gross margin does not exist.

**The size, as an interval rather than a point.** There is no single correct
GP/TA for UHS, so the review gave the ceiling and the floor of every defensible
computation, and the placing at each end:

| numerator | GP/TA | overall placing | top 5 |
|---|---:|---:|---|
| **the feeder's (revenue − materials)** | **101.1%** | **1** | UHS, LULU, DECK, PNDORA.CO, BETS-B.ST |
| generous: "other operating" counted entirely as SG&A | 49.1% | **10** | LULU, DECK, PNDORA.CO, BETS-B.ST, **JD.L** |
| revenue − every cash operating cost | 17.8% | **134** | LULU, DECK, PNDORA.CO, BETS-B.ST, **JD.L** |

**The feeder's figure lies above the ceiling.** At BOTH ends of the interval
UHS leaves the top five and JD.L enters it, so this is not a question about
where inside a range the name belongs — it is outside the range at rank 1.

---

#### Why there is no threshold here, which is itself part of the finding

The natural signal is how much of revenue sits BELOW the gross-profit line,
`(GP − EBIT) / revenue`. Over the 311 profitable ranked names: median 28.1%,
and 22 names above 60%. Among them:

| | below the line | gross margin | EBIT margin | verdict |
|---|---:|---:|---:|---|
| UHS | 78.2% | 90.4% | 12.2% | artefact |
| AFRY.ST | 74.2% | 79.5% | 5.3% | artefact — consultancy, the wages |
| FGR.PA | 73.6% | 84.0% | 10.3% | artefact — construction |
| **PNDORA.CO** | **55%** | 79.1% | 24.0% | **correct** — jewellery brand with its own stores |
| **ADBE** | **51%** | 89.3% | 37.6% | **correct** — R&D and sales |

**The threshold that catches UHS also catches Adobe and Pandora, and those two
are right.** The difference between them is economic, not arithmetic: Adobe's
marginal cost really is near zero, and UHS's nurses are not. Nothing in what is
stored — revenue, gross profit, EBIT, EBITDA, the balance-sheet lines —
separates the two families. The review looked for a non-arbitrary rule and did
not find one, and **the failure to find one is the reason no threshold is
built.** A cut-off that fires on three artefacts and two correct names would
not be a measurement; it would be a guess wearing a number.

*Twenty-three of the 325 ranked names carry a gross margin above 80%. In the
quality leg's top 25 there are four: BONEX.ST (92.6%, quality placing 1), UHS
(90.4%, placing 2), ADBE (89.3%, placing 14) and SECT-B.ST (88.6%, placing 17)
— the top two among them. That is the shape of the exposure, and it is stated
rather than filtered.*

---

#### The consequence, decided

> **A plausibility test on gross margin belongs in FRAMEWORK §5, not in the
> screener.** The screener EXPOSES and the analyst JUDGES: the report prints
> GP/TA per name in the top-20 table, and `ranking.csv` carries
> `gross_profitability` for every ranked name beside `gross_profit`,
> `total_assets` and their periods. Whoever runs §5 therefore sees that UHS's
> 101.1% is what it is, and decides whether that is possible for the industry.
> **No code decides it.** No threshold, no detector, no sector rule beyond the
> one E6 already carries.

This is the same posture the rest of the tool takes towards a fact it cannot
adjudicate: name it, count it, and refuse to net it away. A screener that
silently down-weighted UHS would be making a judgement about hospital
accounting on the owner's behalf, in the one step where a wrong judgement
costs five names' worth of hours.

---

#### What was done to the run of 2026-08-21

**UHS was removed from `config/watchlist.yaml` and JD.L, the next name in the
same ordering, was entered in its place.** The file was backed up first
(`config/watchlist.yaml.bak-2026-08-23-pre-E7-uhs-removal`), and JD.L's note
carries the reason and the date in the same line as the measured figures, so a
reader of the watchlist alone can see why that name is there and this one is
not. `vss/pipeline.py` did not and could not perform the swap: it appends and
never touches an existing ticker, which is a rule worth more than the
convenience of automating a one-off correction.

**And the removal is durable, because deleting a name from the watchlist does
not keep it out.** `pipeline.write()` skips a ticker that is ALREADY in the
file; UHS no longer was, so the next `--rank --write-pipeline` would have
appended it again as rank 1, with the 101.1% note. UHS is therefore entered in
`config/screener_exclusions.csv` — the list of *names owned or already
decided* — as `UHS, E7, 2026-08-23`, which removes it at step 0.

> **The exclusion is not "wrong on this list". It is EVERY list.** The quality
> leg overstates any company that draws its cost-of-revenue line above its own
> production wages, and where that line sits is the company's presentation
> choice and does not change between runs. Excluding on "this run's ranking
> was wrong" would be a judgement about one day; excluding on the property of
> the metric is a judgement about the metric, which is what this entry is.
>
> **Removing the row is how the name comes back**, deliberately and by hand,
> which is exactly the shape of every other row in that file. The rejection is
> counted **on a value** — a dated decision is a value, not missing data.

*Calibration: this entry does not say the quality leg is wrong, and it does not
say UHS is a bad business. It says that one input to the leg is not the same
quantity for every company, that the difference is economic and therefore not
detectable from the stored figures, and that the judgement it requires is
already owed to §5 on every name. The cost of the limitation is bounded and
stated: it can promote a name whose gross margin its industry does not support,
and the only defence is a person reading the printed ratio.*

### E8 — the EBIT alias set is ordered on meaning, and carries a year and a unit

**PROPOSED 2026-08-23 as text, with the measurement, before a line of it was
coded. DECIDED 2026-08-23, superseding E5's alias ORDER.** Standing rule 6 was
met a third time. The review of `reports/screener-review-2-2026-08-23.md`
(finding L3) is accepted; the proposal as approved is
`reports/L3-forslag-2026-08-23.md`. E5 stays in this file with the old order
marked superseded: the run of 2026-08-22 was produced under it.

---

#### What changes

> **The order.** EBIT is taken from **`Total Operating Income As Reported`**,
> then **`Operating Income`**, then **`EBIT`** — the reverse of E5's.
>
> **The year, first.** The alias is chosen among those carrying the **newest
> fiscal year end any of the three reports**. Meaning decides within that
> year, never across years.
>
> **The unit, last.** Two labels for that one year end whose ratio is a round
> power of a thousand are **one figure in two units**. Which unit the
> statement meant is not readable off anything stored, so the EBIT is
> **DATA MISSING**, named and counted apart — never a number, and never the
> other label chosen on a guess.

The `ebitda` prohibition is untouched, the FX conversion is untouched, and the
price leg's *definition* — `EBIT / enterprise value` — is untouched. Only what
the numerator's three words mean changes.

---

#### Why the order — the labels are not synonyms

E5 chose its order on a **coverage** argument: *"14 of 15 US candidates carry
it; ACN does not."* Nobody asked what the labels mean. They are three different
numbers: of the **323 candidates carrying all three, only 10 carry the same
figure under all of them**, and where they differ the max/min ratio has median
1.07× and p90 1.46×.

Tested against the companies' own filings, `us-gaap:OperatingIncomeLoss`, over
the 32 US names in the ranked list:

| alias | matches the company's filed operating income |
|---|---:|
| **`Total Operating Income As Reported`** — E5 put it LAST | **30 of 32** |
| `Operating Income` | 19 of 32 |
| **`EBIT`** — E5 put it FIRST, and it is what was used | **6 of 32** |

The direction is one-way: `EBIT` is **higher** than the as-filed line for 183
of 275 names (67%), more than 10% higher for 48 and more than 50% for 9. WDC
10,070 against 4,453 (2.26×); CMCSA 30,175 against 20,672 (1.46×); TPR 301.5
against **415.0**, where 415.0 is exactly what the company tags as
`OperatingIncomeLoss`. **A too-high EBIT is a too-high earnings yield**, which
promotes.

*Coverage does not vanish, it becomes a fallback chain. Over the 394
candidates the set resolves to the first label for 314 names, the second for
67 and the third for 4.*

---

#### Why the year is settled first — the part the review did not have

`TickerFundamentals.latest` answers per label, and **the labels stop in
different years.** Nine of the 394 candidates:

| | EBIT | Operating Income | Total Operating Income As Reported |
|---|---|---|---|
| **NVR** | 2025-12-31 | 2025-12-31 | **2024-12-31** |
| UMI.BR, NEXI.MI | 2025-12-31 | 2025-12-31 | 2024-12-31 |
| BKW.SW | 2025-12-31 | 2025-12-31 | 2023-12-31 |
| FRES.L, GPG.ST | 2025-12-31 | 2025-12-31 | 2022-12-31 |
| CATE.ST, G24.DE | 2025-12-31 | 2025-12-31 | 2021-12-31 |
| MONC.MI | 2025-12-31 | 2025-12-31 | 2025-12-31 |

Taking the first label present *at whatever year it ends in* would hand eight
of them a figure up to five years old **with a current one sitting beside it
in the same store** — and since the staleness gate now measures the rows the
key actually reads (L4, 2026-08-23), **all eight would then be excluded as
stale.** One of the eight is **NVR, place 20**. Measured: a blind reorder gives
314 ranked and 13 stale; with the year settled first, **320 ranked and 5
stale**, unchanged from before the reorder.

*This is the same shape as K6 and as L4: the right figure for the right year.
A label whose series ends in 2021 is not another measurement of 2025.*

---

#### Why the unit check is not a threshold

MONC.MI, from the store, all three for **2025-12-31**:

| label | value |
|---|---:|
| `EBIT` | 929,977,000 |
| `Operating Income` | **913,356,000** |
| `Total Operating Income As Reported` | **913,356** |

The last two are the **same digits with exactly a factor of 1,000** between
them. That is not two measurements of operating profit; it is one number in
two units. *(The review's "1018×" is against `EBIT`, which differs
economically. Against `Operating Income` the ratio is 1000.000.)*

A unit slip multiplies one figure by a round power of a thousand and leaves
its digits alone, so the test asks that exact question rather than "are these
very different". **Measured over every pairwise alias ratio, same year end, of
all 394 candidates: MONC.MI and nothing else — at every tolerance from 1e-9 to
1e-2.** The recorded tolerance is 1%, and the gap around it is wide: the
second-largest alias ratio in the whole set is **281.7×** (IP, `EBIT`
−2,817M against `Operating Income` −10M), a real economic difference sitting a
factor of **3.6 below** the boundary, against a median of 1.083× and a p90 of
1.784×. This is the same form `series_sanity` uses: a stated cut with the
measured gap printed beside it.

**The rejected alternative, and its price.** The right unit *is* inferable —
MONC.MI's revenue is 3,132,128,000, so 913,356,000 is the coherent figure, and
choosing it would keep the name at place 54 instead of removing it from the
list. It is not chosen. It is an inference about a number we cannot read, and
the price of refusing is measured and small: **one name of 394**, on no
watchlist, in nobody's top twenty.

---

#### THE MEASUREMENT — what it moves, through the whole chain

Same snapshot, the twelve rates of 2026-08-21, L1's exclusion of UHS not yet
applied so the populations are comparable:

| | before E8 | with E8 | blind reorder only |
|---|---:|---:|---:|
| ranked on both legs | 321 | **320** | 314 |
| earnings yield alone | 55 | 55 | 53 |
| not ranked | 13 | 14 | 14 |
| STALE | 5 | **5** | **13** |

**Top-5 unchanged, 5 of 5, same order.** Top-10 9 of 10 by membership, top-20
17 of 20. 291 of 320 places change occupant. Out of the top twenty: ERIC-B.ST,
BEI.DE, NVR — to 28, 23 and 25. In: ROCK-B.CO, SYNSAM.ST, HCA.

**The yields fall across the board** — UHS 13.5% → 12.7%, DECK 11.7% → 11.1%,
JD.L 11.0% → 10.6% — which is the whole point: it is the as-filed operating
income instead of a label that runs higher for two names in three.

---

#### A KNOWN LIMITATION of the second rung — recorded in E7's form, and NOT
#### given a mechanical fix

**DECIDED 2026-08-23, in the same shape as E7.** The measurement above is about
the FIRST rung. The second — `Operating Income` ahead of `EBIT` — rests on a
much weaker number, and the first re-run under E8 produced the case that shows
why.

> **The evidence for the second rung is 19 of 32, and it was measured only on
> US filers.** `us-gaap:OperatingIncomeLoss` exists because those companies
> file under US GAAP. A Danish or Norwegian issuer has no such tag, was never
> in the sample, and there is nothing in the store that says which of its two
> labels is the operating profit its accounts present.

**The case: ROCK-B.CO, which the re-run put at place 5 from place 101.**
ROCKWOOL presents no `Total Operating Income As Reported`, so it falls to the
second rung. For 2025-12-31, in EUR:

| label | value |
|---|---:|
| `EBIT` — what E5's order used | 211 M |
| `Operating Income` — what E8's order uses | **594 M** |

The company's own annual report settles it: **EBIT margin 14.7% before the
value adjustment of the Russian business and 4.6% after, on an impairment of
392 MEUR.** Against revenue of 3,877 M that is 570 M and 178 M. So
`Operating Income` 594 M is the result **before** the loss and `EBIT` 211 M is
the result **after** it — 594 − 392 = 202. **The label E8 chooses for this name
is the one that leaves out a 392 MEUR loss, and it is what lifts the name into
the top five.**

**No mechanical fix, and the alternatives were measured rather than argued.**

| | ROCK-B.CO | ranked | top-20 against E8 | what it costs |
|---|---:|---:|---:|---|
| E8 as it stands | **5** | 319 | 20/20 | the name is in |
| narrow E8 to the first rung | 89 | 319 | 18/20 | **KMAR.OL to place 5** |
| any second-rung disagreement is DATA MISSING | out | 279 | — | 40 of 319 names |

*Narrowing moves the fault instead of removing it.* Putting `EBIT` back ahead
of `Operating Income` sends ROCK-B.CO to 89 and brings **KMAR.OL (Kongsberg
Maritime) from 19 to 5** — on an `EBIT` of 4,802 MNOK against an
`Operating Income` of 3,455 MNOK, **39% higher**. That is the higher of two
disagreeing labels promoting a name into the top five, which is the thing E8
exists to stop. ERIC-B.ST does the same (35% higher, 27 → 14); NHY.OL goes the
other way (60% lower). **Of the 42 second-rung names, all carry `EBIT` for the
same year end; the two labels are identical for 2 and differ for 40 — `EBIT`
higher for 26 and lower for 14.** There is no direction to select against, and
the swap costs 238 of 319 placings.

*And there is no threshold to find.* "Any second-rung disagreement is DATA
MISSING" removes 40 of 319, including HCA at place 18 whose two lines are
12,080 against 11,965 MUSD — **0.96% apart**. A narrower cut needs a number,
and the differences run smoothly from 0.96% (HCA) through 14% (HOC.L), 18%
(NDX1.DE) and 26% (TXT) to 28,070% (IP). **There is no gap to put a cut in.**
This is L1's situation exactly, and it gets L1's answer: write the limitation
down, build no detector.

**What was done instead.** ROCK-B.CO is entered in
`config/screener_exclusions.csv` as `ROCK-B.CO, E8-REVIEW, 2026-08-23`, and
**that row is not the same kind as E7's.**

> **Two kinds of exclusion row, and the difference is now on the record.**
> E7's UHS row states a property of the METRIC — where a company draws its
> cost-of-revenue line — which does not change between runs, so the row
> stands until someone deliberately removes it. This row states a property of
> ONE REPORTING YEAR: when FY2025 leaves the accounts the two labels may agree
> again and the exclusion become wrong. **A dated row says so in its own
> reason, beginning `REVIEW WHEN`, and its `skal` is `E8-REVIEW` rather than a
> bare edit number.** A future reader must be able to tell the two apart
> without reading this file.

*Calibration: this entry does not claim the key now picks better companies. It
claims the numerator was named after a concept it was not measuring for 26 of
32 US names where the filing could be checked, that the label with the best
claim to the concept is sometimes years out of date and must not be taken on
that account, that one candidate reports the same figure in two units and the
honest answer there is that we do not know which — and that on the second rung,
where the evidence is 19 of 32 and none of it non-US, the tool cannot tell a
result stated before a large write-down from one stated after it. The last of
those is not fixed. It is named, and one name is kept out by hand.*

### E9 — §4.2.2's "flat/declining revenue" carries no number

**RECORDED 2026-08-23. OPEN — not decided.** Found while running the §5 chain on
LULU, the first name the screener chose that the manual chain has been run on.

*This is a FRAMEWORK ambiguity of the B family rather than a tooling deviation.
It is numbered E9 because that is the number the owner assigned, so the sequence
stays continuous and the entry stays where the session that found it put it.*

---

#### The gap

§4.2's second hard kill reads:

> Op margin compression > 150bps YoY with **flat/declining revenue**, not
> explained by a quantified Class C event

**"Flat/declining" has no number anywhere in FRAMEWORK or in this file.** B3 gave
Gate 3's revenue limb a ±2% band; §4.2.1's decline limb was narrowed by B9 to
mean demand rather than portfolio change. The word "flat" in §4.2.2 was never
given either treatment, and the limb is a **hard kill** — the altitude at which
an undefined term costs the most.

#### The case that found it

LULU, fiscal 2026 Q1, quarter ending 2026-05-03 (10-Q accession
`0001397187-26-000078`):

| | |
|---|---:|
| revenue | 2,471.6 MUSD, **+4.3% YoY** |
| operating income | 276.9 MUSD against 438.6 a year earlier |
| operating margin | 11.20% against 18.50% |
| **compression** | **−730bp**, 4.9× the 150bp threshold |
| Class C event disclosed | **none** |

The compression limb is met several times over. Whether the revenue limb is met
depends entirely on a word:

- **On a ±2% reading**, borrowed from B3, +4.3% is growth and **the kill does
  not fire**.
- **On a "not meaningfully accelerating" reading** — LULU's eight-quarter YoY
  series is +7.3, +8.7, +12.7, +7.3, +6.5, +7.1, +0.8, +4.3 — the trend is a
  deceleration to a third of its own rate, and a reader could call that flat.

**Both readings are available today and the file does not choose.** Two
analysts running §4.2 on the same filing reach opposite verdicts on a hard kill.

#### What is NOT recorded here

**No number is proposed.** The population effect is also **unmeasured**: testing
which candidates would flip under each reading needs eight quarters of margin
history per name, and the screener stores one annual figure. The size of this is
therefore known for one name and unknown for the list.

*Calibration: this entry does not say LULU should or should not be killed by
§4.2.2. It says the rule cannot be applied to LULU without the reader supplying
a number the rule does not contain, and that a hard kill is the wrong place for
that.*

### E10 — the earnings yield double-counts leases, and it is a retail effect

**RECORDED 2026-08-23. Measured over the whole candidate set before the entry
was written, at the owner's instruction, because the hypothesis on the table was
that it had shaped the sector mix of the list.** It had not. The measurement is
below and it refutes the hypothesis it was run to test.

---

#### The inconsistency

> The price leg is `EBIT / enterprise value`. Enterprise value is taken from the
> quote summary as `marketCap + totalDebt − totalCash`, and **yfinance's
> `totalDebt` includes capitalised lease liabilities**. `EBIT` is
> `OperatingIncomeLoss`, which is struck **after** the lease has been charged.
> **The same lease is therefore counted in both halves of the ratio** — as
> financing in the denominator and as an operating cost in the numerator.

**The case: LULU.** `totalDebt` 2,136.0 MUSD is **entirely** the operating lease
liability — 357.0 current plus 1,779.0 non-current at 2026-05-03. The company's
borrowings are **zero**: `ShortTermBorrowings` 0.0 and `OtherBorrowings` 0.0 at
every quarter end, and no long-term debt element exists in its facts at all.

**The accounting standard decides how much of it is a double count, and the two
answers differ:**

- **US GAAP operating leases (ASC 842):** the entire single lease cost sits in
  operating expenses, so EBIT is after the whole rent. Adding the liability to
  EV is a **full** double count. This is LULU.
- **IFRS 16:** every lease is a finance lease. Right-of-use depreciation is in
  operating expenses and the lease interest is below EBIT. Adding the liability
  to EV double-counts the **depreciation component only** — the interest half is
  legitimately a financing item the numerator excludes. This is JD.L, AD.AS,
  PNDORA.CO and every other European name in the list.

The direction is the same in both cases and it is worth stating plainly: **the
double count makes a lease-heavy company look DEARER, never cheaper.** It
inflates the denominator of a yield. It cannot promote a name; it can only bury
one.

---

#### THE MEASUREMENT — 318 ranked candidates

**First, what the store can and cannot tell us, because it decides the answer.**
The lease is not stored as a line. It is inferred from two balance-sheet lines
that are: `Long Term Debt And Capital Lease Obligation` minus `Long Term Debt`.
That splits the population three ways, and **only the first is a measurement**:

| | names | what the difference means |
|---|---:|---|
| **A** — both lines present | **291** | `LTDCL − LTD` is a genuine **lower bound** on the lease (non-current only) |
| **B** — only the combined line | 22 | **the split is DATA MISSING.** Reading the whole line as lease is an UPPER bound, not a figure |
| C — no lease line at all | 5 | nothing to say |

> **Group B is where a first pass of this measurement went wrong, and the trap
> is worth recording.** Reading the whole combined line as lease put **TPE.WA
> (Tauron Polska Energia) at 45.3% of enterprise value** and made it the
> headline maximum. A Polish utility does not fund 11.9bn PLN of its balance
> sheet with leases; yfinance simply did not populate the separate debt line.
> **An absent line is not a zero and it is not a lease either** — E5's own rule,
> arriving from a direction E5 did not anticipate. Group B is excluded from
> every figure below.
>
> **LULU is the one exception, and only because its filing was read.** It is in
> group B, and `ShortTermBorrowings` 0.0 and `OtherBorrowings` 0.0 at every
> quarter end in its own facts establish that its entire "debt" is lease. That
> is a verified figure, not an inference from a missing line.

**Group A — lease as a share of enterprise value, n = 291:**

| | |
|---|---:|
| median | **0.9%** |
| mean | 2.3% |
| p90 | 5.5% |
| above 5% of EV | 33 of 291 |
| above 10% of EV | **12 of 291** |
| above 20% of EV | 4 of 291 |
| maximum | **35.2%** — JD.L, **place 5**, and in PIPELINE |

**It is concentrated, and in two sectors:**

| sector | in group A | lease > 10% of EV | rate |
|---|---:|---:|---:|
| **Consumer Defensive** | 23 | 4 | **17%** |
| **Consumer Cyclical** | 38 | 5 | **13%** |
| Communication Services | 21 | 1 | 5% |
| Industrials | 83 | 2 | 2% |
| Technology | 71 | **0** | 0% |
| Healthcare | 25 | **0** | 0% |
| Basic Materials | 20 | **0** | 0% |
| Utilities | 5 | **0** | 0% |
| Energy | 5 | **0** | 0% |

**The names it bites hardest, with their PLACE in the ranked list:**

```
    35.2%  JD.L        Consumer Cyclical       place    5   <- PIPELINE
    25.2%  RUSTA.ST    Consumer Cyclical       place   54
    24.4%  AD.AS       Consumer Defensive      place   16
    23.0%  JMT.LS      Consumer Defensive      place   38
    16.0%  BRBY.L      Consumer Cyclical       place  151
    15.9%  AAF.L       Communication Services  place   58
    15.3%  AXFO.ST     Consumer Defensive      place  120
    15.2%  TSCO        Consumer Cyclical       place   55
    14.1%  ZAL.DE      Consumer Cyclical       place   33
    11.4%  KR          Consumer Defensive      place  116
  --------------------------------------------------------------
    10.4%  LULU        Consumer Cyclical       place    1   <- verified from
                                                              the filing, group B
```

---

#### What it does to the order — and the hypothesis it refutes

Recomputed with group A's lease removed from enterprise value — plus LULU's,
which is verified — and nothing else changed:

| | |
|---|---:|
| places whose occupant changes | **232 of 318** |
| top-5 in common | **5 of 5** |
| top-10 in common | 9 of 10 |
| top-20 in common | 18 of 20 |

The movements are the lease-heavy names rising, exactly as the direction
predicts: **RUSTA.ST 54 → 31, JMT.LS 38 → 16, TSCO 55 → 40, ZAL.DE 33 → 21,
AD.AS 16 → 10.**

> **THE HYPOTHESIS UNDER TEST WAS THAT THIS EFFECT MADE THE LIST
> SINGLE-SECTORED. IT DID NOT.**
>
> Sector mix of the top 25:
>
> | | Consumer Cyclical | Industrials | Cons. Defensive | Healthcare | Basic Mat. | Technology |
> |---|---:|---:|---:|---:|---:|---:|
> | as it stands | 9 | 6 | 3 | 3 | 3 | 1 |
> | lease out of EV | **9** | 5 | 3 | 3 | 3 | 2 |
>
> **Consumer Cyclical does not move at all, and neither does Consumer
> Defensive.** The penalty falls on those two sectors and correcting it lifts
> individual names inside them — RUSTA.ST by 23 places, JMT.LS by 22 — without
> changing how many of them reach the top. The concentration survives the
> correction intact, so it is not caused by it. E6's own sector measurement
> already named the cause: the intersection of a margin-based quality leg with a
> price leg on a list already sifted for falls.

#### Decided: NOTHING IS CHANGED IN THE KEY

**The inconsistency is recorded, not repaired.** Three reasons, in order:

1. **It is conservative.** It can only make a name look dearer. A key that
   understates a yield does not promote a name into review work it does not
   deserve, and that is the only error this tool's ordering can make expensively.
2. **The clean repair needs a figure the store does not hold.** Consistency is
   restored either by removing the lease from EV — which understates the
   financing of a company that genuinely rents its whole estate — or by adding
   the lease charge back to EBIT and ranking on EBITDAR. **The lease expense is
   not in `INCOME_LINES` and is not fetched.** Choosing the first repair because
   it is the one the data allows would be choosing on convenience.
3. **The standard decides the size and the standard is not stored either.** A
   full double count under ASC 842 and a partial one under IFRS 16 are different
   corrections, and `accounting: gaap|ifrs` is a watchlist field, not a screener
   one.

**What follows instead:** the effect is named here with its size, so that whoever
runs §5 on a lease-heavy retailer knows the screener's yield is understated for
that name and by roughly how much. For JD.L that is a third of enterprise value.

*Calibration: this entry does not claim the key is wrong. It claims one figure
enters both halves of a ratio, that the error is bounded and one-directional,
that it falls almost entirely on two sectors — and that it is not the reason
those two sectors dominate the list, which is what it was measured to find out.*

### E11 — a PIPELINE name can leave the band while it sits there

**RECORDED 2026-08-23. SETTLED BY E12 (2026-08-24) FOR PIPELINE NAMES.** Found
by protocol step 0 — `vss run --dry-run` over the whole watchlist — on the first
§5 session after the screener wrote to it. Everything below is the finding as it
stood on 2026-08-23; **E12 is the rule.** What E12 does not reach is in *What is
still not decided*, at the end.

---

#### What happened

`PNDORA.CO` was written to PIPELINE off the 2026-08-21 run at a drawdown of
**15.6%**, inside Gate 1's 15–50% band by six tenths of a percentage point. Two
days later the same watchlist reports it **OUTSIDE the band at 13.0%**.

**Nothing revisits a name phase 6 has written.** `vss/pipeline.py` appends and
never touches an existing ticker — by design, and the design is right. But it
means the band is tested once, on the snapshot date, and a PIPELINE entry can be
out of the band before anyone opens it.

#### And the reason is not the one it looks like

Decomposed, from the stored snapshot and the live run:

| | screener, 2026-08-21 run | `vss run`, 2026-08-23 |
|---|---:|---:|
| last close | 769.40 **(2026-08-20)** | 783.00 (2026-08-21) |
| 52-week closing high | **912.00** | 900.20 |
| drawdown | **15.64%** | **13.02%** |

**The 52-week high fell.** The 912.00 was set on **2025-08-22** — and a rolling
365-day window stops containing it the moment the measurement date passes
2026-08-22. It did so on the Saturday between the two readings.

- price effect alone (783.00 against the old high): 14.14%
- **high effect alone** (769.40 against the new high): **14.53%**
- both together: 13.02%

> **Roughly half of the move out of the band is the denominator ageing.** The
> peak did not become less relevant because anything happened; it became a year
> and a day old. **A name can leave Gate 1's band on no new information at all.**

#### This is K3 seen from the other side

`SCREENER.md`'s open finding **K3** says the band measures distance to the
highest close in a rolling 365 days and **does not ask WHEN that high was set**.
E11 is the same rolling maximum failing in the opposite direction: the band does
not ask **whether the high is still inside the window**, and it does not notice
when one falls out.

| | the peak is | the band |
|---|---|---|
| **K3** | old, and still inside the window | reads a stale fall as a fresh dislocation |
| **E11** | old, and just left the window | drops a name out of the band with no market event |

**Same denominator, two failure modes, and neither is measured.** K3 at least has
a computed companion — the **B1 metric**, `(close_180d_ago − last_close) /
(high_52w − last_close)` — which is printed beside every candidate. E11 has none:
**nothing anywhere records the DATE of the high the drawdown was struck against**,
so nothing can say that a drawdown is about to expire, or that it just did.

**And PNDORA.CO is the same name in both findings.** The review of 2026-08-23
named it under K3 as one of two PIPELINE names that fail Gate 1's second limb
outright — **B1 = −1.56**, the price higher than 180 days ago, the worst of the
five written. Two days later it failed the **first** limb as well, by arithmetic
that was fixed the moment the 2025-08-22 peak was set. K3 said the fall was old;
E11 is that fall reaching its first birthday. **One name, one rolling maximum,
and the two findings are one finding.**

*What would close both is the same field: carry the DATE of the 52-week high
beside the drawdown, in `filter1-candidates.csv` and on the PIPELINE note. B1
answers "how much of the fall is recent"; the peak date answers "how long has
this drawdown got left". Neither is a threshold and neither decides anything —
they are two dates a reader currently has to reconstruct.*

#### A second thing the same comparison shows

The snapshot's newest close for `PNDORA.CO` is **2026-08-20** while the run is
dated 2026-08-21 and `LULU`'s newest close in the same snapshot is 2026-08-21.
**One run priced two candidates on two different days.** The staleness gate
passes a one-day-old close, correctly — but Gate 1's band has hard edges, and a
name six tenths of a point inside it was measured on a different day from the
name beside it.

#### What is still not decided

**E12 decided the rest.** Of the four choices this section listed on 2026-08-23,
three are now settled: re-testing the band on every watchlist read and demoting
on failure is **rejected** — leaving PIPELINE requires an information event;
recording the drawdown **and its reference peak's date** on the entry is
**adopted**, as `dd_at_entry` and `peak_date`; and doing nothing is superseded
by both. One choice E12 does not reach remains open:

> **Require a margin inside the band before writing a name to PIPELINE** — a
> threshold, and L1's objection applies. E12 freezes Gate 1 at entry; it says
> nothing about how close to an edge a name may be when it enters.

*Calibration: the flag worked. The screener wrote a name, the watchlist run
caught it two days later and said so in the report. What is missing is not a
detector — it is that nothing records WHEN a PIPELINE name's drawdown was
measured, so the flag reads as news rather than as arithmetic that was always
going to happen on 2026-08-22.*

---

### E12 — Gate 1 is frozen at entry for a PIPELINE name

**DECIDED 2026-08-24 — the owner's ruling, recorded as given.**

> Gate 1 is evaluated **once**, when a name enters PIPELINE, and is then
> **frozen**. Store `dd_at_entry` and the **date of the reference peak**
> alongside it.
>
> Leaving PIPELINE requires an **information event**, not a re-reading of the
> band. A name that drifts out of the band because the 52-week high aged out
> of the rolling window has produced **no new information** and **stays**.

**This settles E11 for PIPELINE names.**

**It does not change B1**, which continues to read **today's** level for
holdings. The two differ because a holding is an open position and a pipeline
name is a piece of review work.

*Applied to PNDORA.CO, 2026-08-24: it **stays in PIPELINE**, eligible for §5,
with `dd_at_entry` recorded from the 2026-08-21 screener run — drawdown
**15.64%**, last close 769.40 (2026-08-20) against a 52-week closing high of
912.00 set on **2025-08-22**, the reference peak's date.*

---

### E13 — the ranking key is struck on trailing twelve months

**DECIDED 2026-08-24 — the owner's ruling on B11, recorded as given.
B11 is settled as (c).**

> The ranking key compares figures **across companies** and therefore requires
> **one period basis**.
>
> The basis is **trailing twelve months**:
>
> * **flow lines** — revenue, gross profit, EBIT — are **summed over the four
>   most recent consecutive quarters**;
> * **stock lines** — total assets, net PP&E — take the **latest period end**.
>
> A name with **fewer than four consecutive quarters** is **INPUT MISSING** and
> is **not ranked**.
>
> A figure whose **period length is unknown** is **NOT MEANINGFUL** and is
> **never ranked on an assumed basis**.

**On the objection recorded under (c).** The rule that this project does not
derive figures **holds for the manual reader and stands unchanged** —
`appendix.py` still derives nothing. The exception is **confined to the ranking
key**, where a TTM sum is written to no file, carries no page reference, and
never reaches §5. The per-period figures in `config/manual/<TICKER>.yaml` stay
**exactly as filed**.

**(a) and (b) were rejected** because they drop every quarterly reporter from
the ranking, which is most of the Nordic surface.

**(d) was rejected** because a name ranked four times worse for measurement
reasons is not review work, it is a **wrong ordering**, and labelling the basis
does not undo a rank sum already taken.

**The vendor path's annual figures are the same basis by construction, so no
vendor-sourced figure changes.**

---

### E14 — the borrowing fields exclude lease liabilities, and the three are additive

**DECIDED 2026-08-24 — the owner's ruling on B13, recorded as given.
B13 is settled as (a).**

> `financial_liabilities_current` and `financial_liabilities_noncurrent`
> **EXCLUDE** lease liabilities. `lease_liabilities` holds the lease portion,
> and **the three fields are additive**.
>
> The schema **documents both borrowing fields accordingly, in words**, so the
> ambiguity cannot recur.
>
> Where an issuer states only the consolidated line and does not split it
> anywhere in the filing, **all three fields are DATA MISSING** — never the
> consolidated figure in the borrowing fields, and never zero in
> `lease_liabilities`. Section 5's **A2** is then **untestable for that name**,
> which is a fact about the disclosure, not a value to estimate.

**(b) was rejected** because it makes `lease_liabilities` a memo field that must
never be added to the other two — a rule that is **silent when broken** — and
that would leave A2 untestable for **every** filer rather than only for those
who do not split.

**The PNDORA.CO appendix map is therefore WRONG on both fields** and must be
re-pointed at the notes' split. **Every other appendix map must be checked for
the same error before use.**

---

### E15 — a manual file may carry an `annual:` block beside `periods:`

**DECIDED 2026-08-24 — the owner's ruling, recorded as given.**

*Raised 2026-08-24, when FY2025 figures read out of PNDORA.CO's annual report
— diluted EPS, share counts, the lease split, the leverage ratio — had nowhere
to go: `reporting_frequency: quarterly` forbids a `2025-FY` label outright, and
the overlap guard forbids it beside `2025-Q1..Q4` in any case. The question is
**B14**.*

> A manual file may carry an **`annual:` block beside `periods:`**. It holds
> figures a company publishes **only once a year** — diluted EPS, share counts,
> leverage ratios, and anything else whose only stated basis is the full year.
>
> The `annual:` block is **excluded from every trailing window by
> construction**. It is **never summed**, **never combined with a period
> entry**, and **never reaches the ranking key**, which under E13 reads TTM
> from `periods:` alone.
>
> Each annual entry carries its **fiscal year**, the **period end**, the
> **document**, and per-figure **source, page and VERIFIED flag**, exactly as a
> period entry does.
>
> **Section 5 reads the `annual:` block** where the figure it needs is annual by
> nature. Where a figure exists in **both** places, **`periods:` wins** and the
> annual entry is ignored — a file must not be able to answer the same question
> twice.
>
> **The overlap guard is unchanged and correct:** a `2025-FY` entry inside
> `periods:` alongside `2025-Q1..Q4` would double-count those months in every
> window, and stays forbidden.

**NOT IMPLEMENTED at the time of writing.** `manual.ALLOWED_TOP_KEYS` does not
accept `annual:`, so a file carrying one fails to load today.

**THE QUESTION THIS SETTLES IS B14**, assigned by the owner on 2026-08-24. It
was ruled on as *B12* in the first instance; **B12 stays RESERVED** by backlog
B-7 for a different question — whether B4, B9 and §3 Gate 3's FCF leg should be
restated in TIME rather than in observation counts for a half-yearly reporter —
and the five places that point at it in that sense stay correct:
`reference/BACKLOG.md`, `reference/SPEC.md`, `vss/ranking.py`,
`tests/test_ranking.py`, and B13 above.

---

### E16 — the net share count may be subtracted, from two stated figures

**DECIDED 2026-08-25 — the owner's ruling on B15, recorded as given.**

> **The subtraction is permitted for a hand entry**, and **only** when both
> components are entered from the accounts **with their own page references**.
>
> Add a field **`treasury_shares_period_end`** to the schema.
>
> * Where an issuer **prints the net count directly**, enter it in
>   `shares_outstanding_period_end` and leave `treasury_shares_period_end`
>   **DATA MISSING**.
> * Where an issuer **prints issued and treasury separately**, enter **both** —
>   issued in a new field **`shares_issued_period_end`**, treasury in
>   `treasury_shares_period_end` — and **the store computes the net**.
>
> **The store's computation is not a derivation of the kind `appendix.py` is
> forbidden.** Both operands are figures printed in the accounts, each carrying
> its own page, and the arithmetic is the subtraction of two stated counts
> rather than a judgement about what a line means. **That is the distinction
> from E14**, where the lease portion of a consolidated line is not stated
> anywhere and therefore cannot be recovered.
>
> **`appendix.py` remains forbidden from computing it.** The xlsx reader fills
> only what the sheet states; if a sheet carries both components it fills both
> fields and the store does the rest.
>
> **Where only one of the two is available, all three fields are DATA MISSING**
> — an issued count alone is not a net count, and entering it in the net field
> would be wrong against the field's own definition.

**NOT IMPLEMENTED at the time of writing.** The schema has 32 fields and neither
`treasury_shares_period_end` nor `shares_issued_period_end` is among them;
`shares_outstanding_period_end`'s `FieldSpec` still reads *"Net of treasury
shares."* and nothing more.

---

### E17 — a quarter never displaces a year

**DECIDED 2026-08-25 — the owner's ruling on B16, recorded as given.**

> **`periods:` wins over `annual:` ONLY where the period entry covers the same
> length as the annual one.** A quarter never displaces a year.
>
> Where the period figure is **shorter** than the annual entry, **the annual
> entry is used** and **the report names both** — the field, the annual value
> used, and the period figure NOT used, **with its length**. Silently
> preferring either would leave the reader unable to see which basis the answer
> stands on.

**This is E13's finding in the section 5 layer:** a figure's period length is
part of what it is, and a rule that compares only names cannot tell a quarter
from a year.

> **AMENDED BY E19, 2026-08-25 — NARROWED.** E17 as written prefers a year over
> a quarter ALWAYS. That holds only when the other leg is a year. Once the H1
> 2026 report printed a Q2 column, PNDORA.CO's `finance_costs_period` read
> 1,149 from FY2025 while the net computed 291 from the quarter's own 325 − 34
> — the operands and their net disagreeing, because E17 read the collision as
> *which figure is better* when the question is *which figure belongs to the
> period being evaluated* (B18, third measurement).
>
> **The narrowed rule: `periods:` answers whenever it can answer AT THE §5
> BASIS, and `annual:` fills only what `periods:` cannot.**
>
> **E17's original case is unaffected:** one field present in both blocks at
> unequal length, where `periods:` cannot answer at the basis, still resolves to
> the year. What goes is the preference for a year over a quarter that IS the
> period under evaluation.

**E15 is otherwise unchanged.** The annual block still reaches no trailing
window and no ranking key.

**NOT IMPLEMENTED at the time of writing.** `manual.ManualFile.shadowed()`
compares field names and nothing else, so PNDORA.CO's FY2025 EBITDA of 10,316
is still displaced by a 2026-Q2 figure of 2,133 covering three months.

---

### E18 — both finance nets follow E16's rule

**DECIDED 2026-08-25 — the owner's ruling on B17, recorded as given.**

> **Both fields follow E16's rule.** Four new fields:
> **`finance_costs_period`**, **`finance_income_period`** for the income
> statement pair, and **`finance_costs_paid`**, **`finance_income_received`**
> for the cash flow pair. **Each carries its own page.**
>
> **The store subtracts**, only when **both operands of a pair are present**,
> only **at one period**, and only from **figures printed in the accounts**.
> Where an issuer prints the net directly it goes in the net field and the
> operand fields stay **DATA MISSING**. Where only one operand is available,
> **that field and its net are DATA MISSING**.
>
> **Neither net is ever written back to the file**, neither carries a page of
> its own, and **the report names both operands with their pages** when it uses
> one — as E16 already does for the share count.
>
> **Both `FieldSpec`s state in words what the field IS**, not only who reads
> it. `net_finance_costs` is the income statement's finance costs less finance
> income; `net_interest_paid` is interest paid less interest received, from the
> cash flow. **They are different figures from different statements and neither
> substitutes for the other.**
>
> **`appendix.py` stays forbidden from computing either.**

---

### E19 — §5 runs on one twelve-month basis, and stocks at its end

**DECIDED 2026-08-25 — the owner's ruling on B18, recorded as given.**

> **Every flow §5 reads is a TWELVE-MONTH figure; every stock is taken at that
> window's end.**
>
> * For an **annual reporter**, the year as filed.
> * For a **quarterly reporter**, the **four most recent consecutive quarters
>   summed**, with the stock legs at the **newest of those four period ends**.
> * **Fewer than four consecutive quarters is INPUT MISSING and §5 does not
>   run.**

**This EXTENDS E13's trailing-twelve-months exception from the ranking key to
§5, and SUPERSEDES E13's clause confining it to the key.** E13's reasoning
carries over unchanged — a figure's period length is part of what it is, and a
quarter against a year is a factor of four with nothing saying so. **The
extension is deliberate, not a correction of E13:** E13 confined the exception
because the ranking key was the only consumer that then needed it, and B18's
five measurements are what showed §5 needs it too.

**Two limits on the extension:**

> 1. **Nothing is written back to the file.** A TTM figure has **no entry, no
>    page and no VERIFIED flag of its own**; the four quarters it summed each
>    keep theirs, and **a TTM figure is usable only if all four are VERIFIED**.
> 2. **The report names the four periods beside every TTM figure it uses**, as
>    `ranking.csv`'s basis column already does. A §5 figure the accounts do not
>    print must say what it was built from, **every time it appears**.

**B18 is settled by this.** Matched legs follow from a single basis rather than
being required separately — which is why the drafted "both legs the same
length" was not adopted: B18's fourth measurement showed a stock has no length,
so that draft would have licensed net debt over a three-month EBITDA at 7.33×
against a 2.5× cap.

**E17 is NARROWED by the same ruling**, and the amendment is recorded beside
E17's own text: `periods:` answers whenever it can answer at the §5 basis, and
`annual:` fills only what `periods:` cannot.

**`appendix.py` stays forbidden from summing anything.** The xlsx reader fills
only what the sheet states; the summing lives in the consumers.

#### One case E19 does not name — SETTLED BY E20 (2026-08-25)

**The owner ruled it on 2026-08-25 and the conservative reading below STANDS.** What was a default pending a ruling is now a rule: see E20.

E19 says stocks come from the window's end and is **silent on whether an annual
flow from a DIFFERENT year may fill a gap** `periods:` cannot answer. E17's
narrowing grants permission to fill and says nothing about the end.

Taken permissively, PNDORA.CO's interest coverage would read **8.97×** — a TTM
operating profit of 7,805 to 2026-06-30 over a net finance cost of 870 struck on
**FY2025, six months earlier**. Both legs twelve months, both ends different:
**B18's first measurement, re-created**.

**Implemented conservatively, therefore:** a flow the basis cannot supply from
`periods:` is filled from `annual:` **only where that entry's `period_end`
equals the basis end**; otherwise it is **NOT MEANINGFUL**, with both window
ends named. Under that reading PNDORA.CO's interest coverage is NOT MEANINGFUL
rather than 8.97×. **The owner has since ruled, and ruled for that reading: E20.**

---

### E20 — an annual flow from another window end may not fill a §5 gap

**DECIDED 2026-08-25 — the owner's ruling on the question E19 left open,
recorded as given.**

> **An annual flow from a DIFFERENT window end may NOT fill a gap at the §5
> basis.** The conservative reading stands: such a leg is **NOT MEANINGFUL**,
> with **both window ends named in the report**.
>
> **A flow figure belongs to the window it was earned in.** Borrowing one
> across six months re-creates exactly the straddle B18's first measurement
> found, and **E19 exists to remove that class of error rather than to relocate
> it**.
>
> **E17's narrowing is unaffected** — `annual:` still fills what `periods:`
> cannot at the **SAME** basis end. **E20 governs a different END, not a
> different block.**

**This is what the code already did in the case E19 measured**, chosen as a
default while the question was open; the ruling makes it a rule.
`resolve_on_basis` fills from `annual:` only where that entry's `period_end`
**equals** the basis end, and otherwise returns NOT MEANINGFUL naming both ends.

**Writing the rule down found one place the code did not keep it.** The
fallback searched the annual block newest-first and let the first entry that
HELD the field decide: an entry closing elsewhere refused a leg an OLDER entry
closing **on** the basis end could have filled. The loop already skipped past
an entry that lacked the field, so the intent to search was there; it stopped
on the wrong condition. **Fixed with the ruling** — a mismatched end no longer
ends the search, and the refusal is reached only when NO entry in the block
closes where the basis does, naming the newest entry that holds the figure.
Two annual entries in one file is the shape that shows it, which is why neither
E19's tests nor E20's first two reached it. **PNDORA.CO's report is unchanged**:
its block holds one entry.

**Where the line falls, in one sentence each:**

| case | answer | by |
|---|---|---|
| `periods:` answers at the basis | the period figure | E17 as narrowed by E19 |
| `periods:` cannot, `annual:` ends **at** the basis end | the annual figure, named as such | E17 as narrowed |
| `periods:` cannot, `annual:` ends **elsewhere** | **NOT MEANINGFUL**, both ends named | **E20** |

#### Consequence, as PNDORA.CO's §5 report prints it on 2026-08-25

**Annotation, 2026-08-25, later the same day:** the finance lines for all
four quarters of the window were entered from the Q3 2025, Q4 2025 and Q1
2026 reports after this ruling was made, and both nets now subtract on the
basis. **What follows is the state E20 was ruled against, kept as it was
written.**


Basis `TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2`, the twelve months ending
**2026-06-30**. Two states appear, at two layers, and both are in the report:

- **NOT MEANINGFUL — another twelve months, to 2025-12-31**:
  `finance_costs_period` (1,149), `finance_income_period` (279),
  `finance_costs_paid` (1,009) and `finance_income_received` (174). The file
  HOLDS all four, in `annual:` FY2025, at a window end six months before the
  basis. E20 refuses them there.
- **DATA MISSING**: `net_finance_costs` (read by §5.3 and by §3 Gate 3's
  interest-coverage limb) and `net_interest_paid` (read by §5.1 C). The
  accounts print neither and E18 writes neither to any file, so nothing carries
  them at all; the store cannot subtract either, because neither operand pair
  resolves on the basis.

**Interest coverage and FCF basis 3 therefore do not compute**, and the number
E20 refuses is the one the permissive reading would have produced: TTM
operating profit **7,805** to 2026-06-30 over net finance costs **870** struck
on FY2025 — **8.97×**, comfortably clear of §3 Gate 3's ≥ 5× limit, on two
windows six months apart.

**What would clear it: the finance lines for EVERY quarter of the window.** Of
the four — 2025-Q3, 2025-Q4, 2026-Q1, 2026-Q2 — **only 2026-Q2 carries them**
(H1 2026 report, income statement p.29 and cash flow p.32, Q2 column). **FY2025
is not one of the four**: it is a year covering two of them inseparably, which
is exactly why it cannot stand in for either, and **2025-Q4 is not entered as a
standalone quarter's finance figures**. A flow must be present in every quarter
of the window under E19 — three of four is not a year and the missing one is
not zero.

#### The refusal speaks in the terms the figure has — FIXED 2026-08-25

The refusal E20 governs shares its branch with a case E20 does not govern. A
**STOCK** the basis cannot take at its own end fell through to the same
sentence and was told it was *"twelve months of a DIFFERENT twelve months"* — a
length claimed for a figure that has none, which is **B18's fourth measurement
in the prose** rather than in the arithmetic, and it survived E19 unnoticed
because no file in the project showed it.

**The refusal was always right** — E19 puts stocks at the window's end, and a
balance struck on another date is not on the basis. **Only the sentence was
wrong, and the sentence is now the figure's own:**

| the basis cannot take | and the report says |
|---|---|
| a **flow** from another year | *covers the twelve months to X; the basis ends Y* |
| a **stock** from another date | *states it at X and the basis ends Y. A stock is taken at the window's END (E19) and this is another date* |

The input block's status column says `another twelve months, to X` for the one
and `stated at X, not the window end` for the other, and the two kinds are
listed under two headings rather than one. **A stated ratio keeps the flow
wording** — `net_debt_ebitda` is struck over a twelve-month denominator, so a
figure from another year IS another year's ratio; the line E20 draws is at a
STOCK, not at everything read from the newest entry.

**ONE state, two wordings.** `QUALITY_BASIS_MISMATCH` was not split in two: a
second constant would turn every comparison into a set test and let the next
site added miss one flavour silently — the drift the contiguity test is
imported rather than restated to avoid. The state means *the file holds it and
the basis cannot take it*; how that is said depends on what the figure is.

**PNDORA.CO's report is unchanged**, byte for byte: every figure it refuses
today is a flow or a stated ratio, and its share counts sit in `periods:`
2025-Q4 and read DATA MISSING rather than NOT MEANINGFUL.

---

### E21 — the gate refuses on what the basis READS

**DECIDED 2026-08-25 — the owner's ruling, recorded as given.**

> **`section5_gate` refuses on UNVERIFIED figures the CURRENT BASIS READS —
> not on every entered figure.**
>
> **Measured:** PNDORA.CO carries **238** UNVERIFIED, of which **52** are read
> at the basis and **186** sit in quarters outside the window, where they
> cannot affect any number §5 produces. **Requiring them is work that buys
> nothing, and a gate that never opens is one that gets worked around.**
>
> **Three conditions, all binding:**
>
> 1. **The report NAMES every UNVERIFIED figure outside the window** —
>    visible, not blocking. Same shape as **E7**: print the figure and let §5
>    judge.
> 2. **Verification is a property of the FIGURE, not of the run.** A quarter
>    that leaves the window keeps its VERIFIED flags and is never re-verified
>    when it returns.
> 3. **The gate prints the basis it tested against, every time.** The same
>    file may go from MAY RUN to REFUSED when the basis changes, and the
>    reason must be on the page.

**The old rule's reasoning is KEPT AND ANSWERED, not deleted.** The gate's
docstring said that a half-checked file is one the reader audits by hand
anyway, which is why the flag existed. That holds — **for the figures a run
reads.** It does not reach the figures a run cannot reach. Both sentences are
now in the docstring, in that order, so the next reader sees the argument and
its limit rather than an unexplained narrowing.

#### What "reads" means, and why it is measured rather than listed

**The blocking set is derived from `resolve_on_basis`, not restated beside
it.** `Resolved` now carries the stored figures its answer was built from, and
`basis_reads()` is the union of those over every §5 field. Whatever the
resolver takes — four quarters of a flow, the newest quarter of a stock, an
annual entry filling a gap at the basis end — is exactly what a run can be
wrong about. Two consequences follow that a list of periods would have missed:

* **A STOCK in an earlier quarter OF the window does not block.** E19 takes it
  at the window's END, so an unverified `cash_and_equivalents` in the oldest
  quarter of the four is read by nothing.
* **A field §5 never reads does not block at all**, in any quarter. `op_margin`
  is a check field and `gross_profit`, `total_assets` and `net_ppe` are ranking
  key legs; no method of §5 touches them, and the ranking key has its own
  rules. This is what E7 already does one layer down.

**Which is why the ruling's count and the code's differ by three, and both are
right.** The ruling counted **52** — every §5 field in the four window quarters
— and the resolver reads **49**: `cash_and_equivalents` is a STOCK, taken at
the window's END, so the three earlier window quarters' copies of it are in the
file and read by nothing. The 186 outside the window becomes **189 named** for
the same three.

**MARKET FIGURES STILL BLOCK.** They belong to a date rather than to the
window, so no basis "reads" them in the resolver's sense, and §5 divides them
into its own results all the same. Excluding them would have been a reading of
the word rather than of the rule.

#### Measured consequence on PNDORA.CO

Before: **238 refusals**, and §5 could not run until every quarter back to
2023-Q1 had been read back by hand. After: **49 refusals** — twelve flows in
each of the four window quarters, plus the one stock the window's end supplies
— and **189 UNVERIFIED figures are named in their own section** with why each
does not block. The file still refuses; what changed is that the work it asks
for is now the work that matters, and it is finite and visible.

**Nothing about the figures changed.** No status was written back, and the
same 238 flags are in the file. What changed is which of them the answer
depends on — which is why condition 3 puts the basis on the page beside the
verdict.

---

### B19 — the ranked list's Consumer Cyclical overweight

**RAISED AND SETTLED THE SAME DAY, 2026-08-25, BY MEASUREMENT. NOT A RULING —
nothing changes in code.** The measurements are in
`reports/SCREENER-VALIDATION-2026-08-25.md`, sections 1, 4 and 5, on the
`2026-08-21` snapshot: the 1,370-name universe, the 533 that passed filter 1,
the 402 that passed filter 2 and the 315 ranked rows.

**The question.** Six of the top six and eight of the top thirteen of the
2026-08-23 list were Consumer Cyclical. Does that come from the market, or from
the key — and if from the key, is E6's gross-profitability leg broken?

#### 1. The overweight enters at the RANKING, not at the universe

| stage | Consumer Cyclical |
|---|---:|
| universe (1,370) | **10.9%** — third, behind Industrials 20.0% and Financial Services 16.0% |
| filter 1 (533) | 14.6% |
| filter 2 (402) | 11.4% |
| ranked pool (315) | **12.4%** |
| top 20 / 13 / 6 | 6 / 5 / 3 names |

Filter 1 does favour the sector and **that part is the market**: 52.3% of
Consumer Cyclical names survive the dislocation filter against 38.9% overall, a
fact about where prices stood on 2026-08-21 rather than a property of the
sector. **Filter 2 gives it back.** Measured against the pool the key can order
— E6 exempts Financial Services and the ranked pool holds no Real Estate, so
1,047 names are eligible — Consumer Cyclical is **14.2% of the eligible universe
against 12.4% of the pool: slightly UNDERWEIGHT.** Every stage before the
ordering is flat or adverse.

*Closing this needed one field the store did not hold: `sector` for the 834
universe rows that never reached a fundamentals fetch. It was fetched once and
written to a new `universe_sector` table beside `universe` in the snapshot —
with the universe rows, not with the fundamentals, so it survives a filter
change. No existing row was touched.*

#### 2. E6's quality leg is NOT broken as a measure

| | |
|---|---:|
| η², sector share of GP/TA variance | **11.2%** (SS between 1.130, within 8.919) |
| Kruskal-Wallis | H = 34.2, p = 3.7 × 10⁻⁵, ε² = 0.086 |
| spread of sector MEDIANS | 26.8pp |
| Consumer Cyclical's own IQR | **35.4pp** |

**Within-sector variation dominates.** Sector explains about a ninth of the
variation in gross profitability and the sector gap, while real, is smaller than
the dispersion one sector already carries: Consumer Cyclical's IQR is wider than
the entire spread of sector medians. A random Technology name beats a random
Consumer Cyclical name on this leg 35% of the time, Healthcare 50%, and of the
83 names above Consumer Cyclical's own median, **64 are not Consumer Cyclical**.

**The tilt belongs to BOTH legs.** On the ranks the key actually sums, η² is
**10.9% for the quality placing and 12.8% for the earnings-yield placing** — two
point estimates 1.9pp apart on 315 rows in nine groups, with no interval
computed. **Too close to call the tilt a defect of either.** What surfaces the
sector is the rank SUM: Consumer Cyclical is the only sector in the upper half
of both columns, while Energy and Basic Materials are cheap and score badly on
quality and Technology is the reverse. That is a property of summing two ranks.

#### 3. The head of the list is robust

**PNDORA.CO, FGR.PA, BUCN.SW, ADBE, AFRY.ST, BETS-B.ST, NREST.ST, ZZ-B.ST and
SYNSAM.ST survive every sector-neutral variant tried** — both legs neutralised
with slots allocated by pool share, and the quality leg alone neutralised.
Twelve of the current top twenty survive either way. **The Consumer Cyclical
names at the top sit at the EXTREMES of their own sector, not in its middle:**
they hold positions 1, 2, 3, 4, 5 and 7 of 39, and PNDORA.CO's 87.0% is the
highest gross profitability any Consumer Cyclical name in the pool has. They are
not sector-average companies carried up by a tilt.

What the tilt decides is **depth, not membership**: HWDN.L, RVRC.ST and NVR hold
places 10, 11 and 19 that a sector-proportional list gives elsewhere.

#### What follows, and what does not

- **E6's leg STANDS UNCHANGED.** The measurement was run to find a defect and
  did not find one.
- **Sector-neutral ranking is a DIFFERENT KEY encoding a different question, not
  a repair.** It changes 8 of 20 either way, and which 8 depends entirely on
  which leg is neutralised: Technology and Communication Services when both are,
  Basic Materials and Energy when only quality is. Neither variant is more
  correct than the other, and nothing here proposes one.
- **E7 REMAINS AS WRITTEN.** It is a property of individual companies — what a
  filer puts above its own gross-profit line — and the sector-wide effect it
  might have been read to imply is now measured and small: 11.2%.
- **Nothing was changed by this entry.** No code, no config, no key, no
  exclusion.

#### Queue item 3 stays OPEN

This measures the **screener's** sector behaviour: the universe, the filters,
the ranked pool and the ordering. It does **not** measure the **live sleeve**
against §7's two-sector limit, which is a different population — the held and
pending positions in `config/watchlist.yaml`, each assigned a sector and counted
against the limit. **Nothing in this entry closes that, and this entry must not
be read as having done so.**

---

### E22 — a share count is DATA MISSING unless the count is stated

**DECIDED 2026-08-25 — the owner's ruling, recorded as given.**

> **A share count is DATA MISSING unless the COUNT ITSELF is stated.** Share
> capital divided by par value is **not a count**, and a treasury holding stated
> in money is **not a count**. **Neither may be entered, at any basis.**

**The case: PNDORA.CO at 2026-06-30.** The H1 2026 report states share capital
of **DKK 75m** (balance sheet p.30) and the Annual Report 2025 states a par
value of **DKK 1** (note 4.1, p.130), which together would imply **75,000,000
shares issued** — an inference from a nominal value, not a figure the accounts
print. The last **stated** treasury count is **199,368 at 2026-04-13** (company
announcement 1011), eleven weeks before the basis end, and `Equity_appendix`
shows a further **DKK 11m of purchases in Q2 2026** which the accounts state in
money only.

#### Consequence, recorded

**§5.1 A — Method A, a multiple × EPS — and every per-share figure are DATA
MISSING for PNDORA.CO at this basis.** There is no share count at the window's
end, so there is no per-share denominator, and a fair value per share cannot be
struck however good the other inputs are.

**Gate 3, the FCF bases and Method B are unaffected.** Interest coverage reads
8.45× and net debt / EBITDA 0.90× on figures that need no share count; §5.1 C's
free-cash-flow bases are cash-flow lines; §5.1 B is a multiple applied to EBIT.
**The refusal is confined to what actually depends on the missing figure.**

#### Why the arithmetic was refused although the error would be small

**Treasury shares are about 0.27% of issued** — 199,368 against 75,000,000 — so
the implied count would have been within a third of a percent of the truth, and
the missing Q2 purchases smaller still. The rule does not turn on the size of
the error:

> **A figure the accounts do not state is not a figure.** A small error is still
> an error, and it enters by a door the framework otherwise keeps shut — the
> same door E16 closed when it refused to estimate the second half of a pair,
> and E14 when it refused a lease portion stated nowhere. A tolerance here would
> be a tolerance everywhere: once a derivation is admitted because it is nearly
> right, the question stops being *what do the accounts say* and becomes *how
> wrong is acceptable*, which is not a question this project answers.

#### What this rule does NOT do

**It stops being binding the moment an issuer states the count.** It removes
nothing from a name that reports one: an issuer printing issued and treasury
counts at the period end is served exactly as before, E16 subtracts them, and
§5.1 A runs. **The rule bites only where the count is absent** — and there it
was already DATA MISSING; what E22 forbids is filling it in from a par value.

#### Implementation

**Nothing in the code derived a count and nothing does now** — `share_capital`
and par value are not schema fields, so no automatic derivation was ever
possible, and a test now pins that. **E22 governs the hand that fills the file**,
so it is written where that hand looks: the note on ALL THREE count FieldSpecs
(`shares_outstanding_period_end`, `shares_issued_period_end`,
`treasury_shares_period_end`), and in `config/manual/TEMPLATE.yaml` beside the
three fields. The sentence is defined once, as `manual.STATED_COUNT_ONLY`, and
appended to each spec — one rule, three fields, and no chance of the three
drifting apart in prose.

---

### B20 — §3 Gate 3's revenue limb names no basis

> **SETTLED 2026-08-25 by E30: the basis is ORGANIC**, and the question moved
> out of Gate 3 — the limb it was asked about is deleted, and §4.2.1 now carries
> it, naming the basis it read. The case below stands as the evidence the answer
> rests on. See **E30** at the end of this file.

**RAISED 2026-08-25, measuring PNDORA.CO's eight quarters against the limb.
NOT SETTLED — this entry states the question and the case, and rules nothing.**

**The text, in full:** *"Revenue: growing, or stable within ±2% in the worst
quarter."*

**It names no basis.** Not reported or organic. Not a currency. Not whether
"worst quarter" is year-on-year or sequential. Every other period question in
this project has been ruled — E13 and E19 on the twelve-month window, E20 on the
window's end — and **none of them reaches this sentence**: they govern §5 and
the ranking key, and this is a §3 gate limb read off a quarterly series.

#### The case: PNDORA.CO, the eight quarters to 2026-06-30

| quarter | revenue, DKK m | reported DKK Y/Y | organic | LFL |
|---|---:|---:|---:|---:|
| 2024-Q3 | 6,103 | +9.5% | +11% | +7% |
| 2024-Q4 | 11,973 | +10.7% | +11% | +6% |
| 2025-Q1 | 7,347 | +7.5% | +7% | +6% |
| 2025-Q2 | 7,075 | +4.5% | +8% | +3% |
| 2025-Q3 | 6,269 | +2.7% | +6% | +2% |
| 2025-Q4 | 11,859 | **−1.0%** | +4% | 0% |
| 2026-Q1 | 7,109 | **−3.2%** | +2% | 0% |
| 2026-Q2 | 7,219 | +2.0% | +3% | +1% |

**Worst quarter: −3.2% reported, +2% organic, 0% LFL.** The limb's ±2% band
therefore fails on one column, passes on another, and sits exactly on the edge
of the third. **Two of the eight quarters are negative on reported DKK and none
is negative on either of the other two.**

**The wedge is foreign exchange, and the issuer quantifies it every quarter:**
−5.4% in 2025-Q4 (DKK 0.64bn), −5.4% in 2026-Q1 (DKK 0.4bn), −0.9% in 2026-Q2
(DKK 0.1bn). It is not a modelling choice — it is a disclosed number, in the
same reports the revenue comes from.

#### Why this is not the same question E13/E19/E20 answered

Those rulings are about **period length and period end** — what twelve months
means and where they stop. This is about **which measure of revenue a limb
means** when the accounts print three and the issuer's own headline uses the one
the accounts do not print in the income statement. A rule that fixed the window
says nothing about the currency the window is measured in.

**What the answer would change, stated so the cost is visible.** Reported DKK
makes a currency movement a quality failure and would fail a company whose
volumes grew; organic makes the gate blind to the currency the shareholder is
actually paid in; LFL narrows it further to a same-store measure the gate never
mentions. **Each reading has a defensible case and they give different verdicts
on this name.**

**Not settled here.** PNDORA.CO's own entry in `config/watchlist.yaml` records
Gate 3 as NOT ruled for exactly this reason, and its WATCH verdict rests on
Gate 1's catalyst limb, which does not depend on this question.

---

### E23 — the capex line an issuer prints as one

**DECIDED 2026-08-25 — the owner's ruling, recorded as given.**

> **A field `capex_combined`** for the single line an issuer prints when it does
> not split property, plant and equipment from intangibles. **It is a stated
> figure, not a derivation.**
>
> **§5 reads `capex_ppe` + `capex_intangibles` when BOTH are present at the
> basis, and `capex_combined` when they are not. Never both, and never a mix of
> one separate line with the combined one.** The report **names which it used,
> every time**. Where an issuer prints the split, **entering the combined field
> instead is wrong and the separate fields win.**

**The case.** BETS-B.ST's interim reports print **`Investments in
intangibles/tangibles` as one line** and never split it — Q1 2026 **−14.6**
(p.17), Q3 2025 **−12.4** (p.18), H1 2026 **−14.2** (p.18) — while the annual
report splits the same spend into **−3.8** and **−60.8** (AR 2025 p.117). The
split exists once a year and the quarters do not have it.

**Recorded consequence.** Without this field, **FCF basis 1 is DATA MISSING for
BETS-B.ST on any quarterly basis**, and §5.1 C's Method C with it: E19 needs
four quarters, the quarters print one line, and the schema had no home for it.
The alternative — entering a combined figure in `capex_ppe` — is a false
statement about which line it is, which is why the field exists rather than the
practice.

#### How it is implemented, and the two things that are NOT allowed

`capex_legs()` chooses at the basis and returns the legs **with a sentence
naming which**; the ratio table holds a marker rather than a fixed pair, so the
choice is made where the basis is known and the ratio is never listed twice
under two spellings of one input. Two arrangements are refused by construction:

* **The split plus the combined line.** Both entered means the same money
  twice; the split wins, and the report says the combined figure was **not
  used**.
* **One split leg plus the combined line.** That is not a sum — it is one line
  added to a total that already contains it. The lone leg is **not used**, and
  the report says so by name.

**PNDORA.CO is unaffected** and its report proves the naming works in the other
direction: *"CAPEX ON THE BASIS (E23): split: capex_ppe + capex_intangibles, as
the accounts print them."*

---

### E24 — the price legs are in the quote currency, and the rate is frozen

**DECIDED 2026-08-25 — the owner's ruling, recorded as given.**

> Where reporting currency and quote currency differ, **§5's price legs are
> struck in the QUOTE currency**: `fv_base`, `mbp` and `stop_price` are in the
> currency of the quote they will be compared against, **because
> `rules.compute_mbp` and `rules.mbp_verdict` compare them to `last_close` with
> no conversion anywhere in the code**. The accounts stay in the reporting
> currency; **the conversion happens at or before `fv_base` is written and never
> after.**
>
> **The rate is FROZEN WITH THE VERDICT, not re-struck each run** — the same
> choice E12 made for Gate 1. **A stop that moves 5% because the exchange rate
> moved, with nothing changed in the business, is the currency selling for you
> rather than the analysis.**
>
> **Six things are recorded beside any converted figure:** the pair **with its
> direction**, the rate, **the rate's own as-of date** (not the date of the
> calculation), the source, **which side was converted**, and **the price date
> the result is meant to be compared against**.

**Why six and not four.** `fx.Rate` already carries value, pair, `as_of` and
source — and **wrote them down nowhere outside a screener run manifest**, which
a §5 verdict is not. The other two are the ones a reader cannot reconstruct: a
rate applied to the price rounds differently from the same rate applied to a
per-share value built from the accounts, and a converted figure is only
comparable to the quote it was struck against. **A partial record is refused:**
five of six is not a record, because a rate without its own as-of date cannot be
re-struck and a rate without a direction is as likely to be its reciprocal.

**Where it lives.** `config.FxRecord`, an optional `fx:` block on a watchlist
entry, validated on load; `vss run`'s report prints it under **CONVERTED PRICE
LEGS** with the rate's **age in days** beside it.

#### The cost, stated plainly

**A frozen rate ages, and nothing today says when it has aged enough to
re-strike the verdict.** The report shows the age and acts on it in no way. That
question — how stale a rate may be before a verdict built on it stops meaning
what it said — **is open, and is left open here** rather than answered by a
default nobody chose.

#### A limit on Method A this ruling does NOT solve

**A7's five-year median forward P/E cannot be built for a name whose price
history and EPS are in different currencies without a five-year rate series,
and the store has no such series** — `fx.default_lookup` fetches a current pair
and rates are recorded per run, never as history. A single end-date rate applied
to a five-year price history does not produce that history's multiple; it
produces today's rate applied to the past, which is a different number with the
same name. **This is a limit on Method A for such names**, recorded so it is not
rediscovered as a bug, and **E24 does not address it.**

---

### E25 — a zero is a claim about the company

**DECIDED 2026-08-25 — the owner's ruling, recorded as given.**

> **A zero is a claim about the company and requires evidence, not merely
> absence.** An entered zero carries a **`zero_basis`** field naming which of
> three forms the reader saw:
>
> * **`caption`** — the issuer lists the line and shows nil or a dash
> * **`note`** — a sentence states there is none, cited to its page
> * **`subtotal`** — the components shown sum to the subtotal shown, leaving no
>   room for the line
>
> **Any other zero is refused on load. A figure the reader could not find is
> DATA MISSING, never zero: absence in a search is a fact about the search.**

#### The third reading, and why only one form excludes it

An absent line has **three** possible meanings, not two: the amount is **nil**,
the reader **did not find it / the issuer does not present the concept**, or
**the line is subsumed in a caption the issuer does present** — Betsson's capex
inside *Investments in intangibles/tangibles*, current borrowings inside *Other
current liabilities*, short-term investments inside *Other receivables*.

**`subtotal` is the only form that excludes the third**, because it is the only
one that reads the arithmetic of what IS presented. And it stops working exactly
where the third reading is live: **where a combined line exists, the subtotal has
room, and that form is unavailable.** `_check_subtotal_form` refuses it by name —
*"a combined line is a caption WITH ROOM IN IT."*

#### Bound only where it matters

**The fields a wrong zero carries through a gate require `zero_basis`:**
`financial_liabilities_current`, `financial_liabilities_noncurrent`,
`lease_liabilities`, `finance_costs_period`, `net_finance_costs`, `capex_ppe`,
`capex_intangibles`, `capex_combined`, `lease_payments_capital`,
`net_interest_paid`. Each improves a ratio: understated net debt, an interest
coverage struck on nothing, free cash flow with no capital spending in it.

*The ruling says nine fields and lists ten. The list governs; the count is
recorded as given and corrected here rather than silently.*

**The other direction is left alone.** A wrong zero in
`proceeds_from_disposals_ppe`, `other_current_financial_assets`,
`noncurrent_derivative_assets_on_debt` or `finance_income_period` **fails a gate
the name should pass — it costs an opportunity, not money — and is not worth the
friction.** No evidence is demanded there.

#### Where a zero is refused outright

Three groups, one rule: **a zero there asserts something about the company the
accounts never say.**

* **The counts (E22)** — `shares_issued_period_end`,
  `shares_outstanding_period_end`, `treasury_shares_period_end`,
  `diluted_weighted_average_shares`. A listed company has shares.
* **Concept not presented** — `gross_profit` for a bank or a property company
  (E6), `other_current_financial_assets` for Pandora,
  `operating_cash_flow_pretax` for Betsson. **The issuer's FORMAT is not the
  issuer's AMOUNT.**
* **The non-GAAP memos** — `diluted_eps_adjusted`, `operating_income_adjusted`,
  `free_cash_flow_reported`. A zero would claim the issuer **reported** zero,
  which is a different and false statement from publishing no such measure.

**One cost of the counts rule, recorded rather than discovered later.** A
company holding **no treasury shares** cannot say so in this schema: the field
stays DATA MISSING, and E16's `issued − treasury` cannot complete, so such a
name needs the issuer to print the net count directly for §5.1 A to run. The
ruling is taken as given; this is what it costs.

#### EBIT / 0 is refused outright

**An undefined ratio that any code reads as "very large" passes Gate 3 silently,
and that is the exact failure mode E19 was ruled to remove**, one gate over.
`section5_gate` now refuses on `ZERO DENOMINATOR` when `net_finance_costs`
resolves to zero at the basis — whether entered with evidence or arrived at by
E18's subtraction. It is refused **where the figure is formed, not where it is
divided**, because nothing in this project does the dividing: §3's coverage limb
is struck by hand in the workbook, and a refusal that waits for the division
would never fire.

**Observed and NOT ruled:** two other divisions have the same shape —
`net_debt_ebitda` over a zero EBITDA, and `op_margin` over a zero revenue. The
ruling names coverage; those two are recorded here and left.

#### What the report now says

Every entered zero is listed under **ZEROS, AND WHAT THE READER SAW (E25)** with
its period, its form and its page. A zero in a field that needs no evidence is
named too, with the reason it needs none — so a reader sees which zeros were
argued for and which were merely allowed.

---

### B21 — E25's `subtotal` form can be claimed where a caption has room

**RAISED 2026-08-25, while hand-reading BETS-B.ST's four quarters against
E25. NOT SETTLED — this entry states the hole and the case, and rules
nothing.**

**E25 gives three forms of evidence for a zero and says of the third:** the
components shown sum to the subtotal shown, **leaving no room for the line**.
That form is the only one that also excludes the third reading of an absent
line — that it is **subsumed in a caption the issuer does present**.

**The loader can only check it in one place.** `_check_subtotal_form` refuses
`subtotal` on `capex_ppe` / `capex_intangibles` when `capex_combined` carries a
value, and it can do that **because the schema holds both the parts and the
whole and can compare them**. Everywhere else the loader sees one field and has
no way to know whether some presented caption has room in it.

#### The case

**BETS-B.ST's `financial_liabilities_current` at 2026-06-30.** The balance sheet
(H1 2026 p.17) presents, under current liabilities, `Lease liabilities 4.3` and
`Other current liabilities 315.7`, totalling the stated `320.0`. **The
arithmetic closes.** A reader could enter zero on the `subtotal` form and the
loader would accept it — measured, not supposed.

**And it would be wrong.** `Other current liabilities` is a caption with room in
it: a current borrowing could sit inside that 315.7 and the subtotal would still
close. The honest form here is `note` — p.10's *"The external financing at the
end of the period consisted of bonds amounting to EUR 173.6 million"*, with the
bond table showing maturities in 2027 and 2029 — and that is what the file
entered.

**The same hole exists for at least:** `lease_liabilities` inside a financing
line, `other_current_financial_assets` inside `Other receivables`,
`proceeds_from_disposals_ppe` netted into an investing subtotal. In each, an
arithmetic check on presented captions proves nothing about a line that could be
inside one of them.

#### What the shapes of an answer look like, none of them chosen

* **Do nothing.** The form is documented and the reader is responsible; the
  loader catches the one case it can. The cost is that `subtotal` reads as
  machine-checked when it is checked in one field pair only.
* **Require the caption to be named.** `zero_basis: subtotal` could carry the
  subtotal it closes and the captions it is composed of, so the claim is
  auditable by a person even where the loader cannot compute it.
* **Restrict the form.** Allow `subtotal` only where the schema holds the parts
  and the whole — that is, exactly where the loader can check it — and require
  `caption` or `note` elsewhere.

**Not settled here.** The file as built uses `note` for every zero it entered,
so nothing currently rests on the hole; this entry exists so that the next
reader who reaches for `subtotal` finds it named.

---

### E26 — a total the issuer never totals is DATA MISSING

**DECIDED 2026-08-25 — the owner's ruling, recorded as given.**

> **Where an issuer presents a total in TWO CAPTIONS and states no total, the
> schema field for that total is DATA MISSING and both components are named.**
> Adding two presented captions is **a sum no rule authorises** — the same
> reasoning as E23's refusal to mix a split leg with a combined line.

**The symmetry with E23 is exact and worth stating in one line:** E23 refuses to
add a part to a whole that already contains it; E26 refuses to add two parts
into a whole the issuer never wrote down. Both say the same thing — **this
project enters figures the accounts state, and the arithmetic between them
happens only where a rule says it may** (E16's share count, E18's finance nets,
E19's four-quarter sum).

**Where the issuer DOES state the total, that stated total is the figure.**
Pandora's note 7 prints `Total lease liabilities 6,291` and the field takes it.
The rule bites only on silence.

#### Consequence for BETS-B.ST, recorded

**`lease_liabilities` is DATA MISSING for all four quarters.** The balance sheet
carries `Lease liabilities` twice — non-current and current, **18.9 and 4.3 at
2026-06-30**, 11.0 and 4.3 at 2025-12-31, 17.8 and 1.1 at 2026-03-31, 5.7 and
4.6 at 2025-09-30 — and totals them nowhere in any interim report. Both
components are named in the comment beside each period in
`config/manual/BETS-B.ST.yaml`.

**So the lease-inclusive leverage reading cannot be formed for this name**, and
**§3 Gate 3's leverage limb rests on the ex-lease figure alone: net debt of
−136.4 against a TTM EBITDA of 260.3, i.e. −0.52×** — net cash, which the
company's own KPI page states as −0.5×. **It does not bind either way**: a
company with net cash passes a ≤ 2.5× cap on any reading, and the missing lease
figure would have to exceed roughly 787 to change that answer, against a lease
liability of about 23. The limb is unaffected in substance and incomplete in
form, and both are true at once.

*The annual report's note 30 does give a lease total for the year end — 15,359
thousand EUR at 2025-12-31 — in a currency scale the file does not use. It is
not entered: rescaling a figure to fit a file is the kind of quiet
transformation E19 refused for periods, and the annual figure is in any case
one date of the four.*

---

### The `op_margin` defect, fixed the same day

**Not a ruling — a defect, found while building BETS-B.ST's file and fixed
under E19's existing rule.** `op_margin` was omitted from
`STATED_RATIO_FIELDS`, so `resolve_on_basis` treated it as a flow and **summed
it**: BETS-B.ST read **0.6560** for four quarterly margins of about 0.14, and
PNDORA.CO read **0.8870** the same way. A margin is not a quantity that
accumulates over a window. It is now a stated ratio and reads 0.1360 from
2026-Q2.

**What that does NOT fix, left visible rather than papered over:** the value now
taken is the newest quarter's margin, which the issuer struck on **three
months**, standing at a **twelve-month** basis. That is E13's own objection in
a new place. The field's other use is unaffected — the margin reconciliation
runs **per period at load** and never on the basis — and nothing in §5 divides
by it, `op_margin` being a `check` field. **Whether a stated ratio struck on a
shorter window may stand at the basis at all is not settled here.**

**The sweep, reported rather than acted on.** Four other fields whose kind is a
ratio, a per-share figure or a count still resolve as flows and would be summed:

| field | kind | summing it gives | is that right? |
|---|---|---|---|
| `diluted_eps` | per_share | the sum of four quarterly EPS | **arguably yes** — that IS a trailing-twelve-month EPS, subject to the share count moving inside the window |
| `diluted_eps_adjusted` | per_share | same | same |
| `diluted_weighted_average_shares` | count | **four times the share count** | **no, and plainly so** |
| `revenue_yoy` | ratio | four year-on-year rates added together | **no** |

**A test pins the list**, so the next field added to the schema cannot join it
unnoticed. Three of the four are a decision rather than a typo, and none was
changed.

---

### D2 — the limits of this rebuild

**DECIDED 2026-08-25 — the owner's ruling, recorded as given. It GOVERNS the
rebuild that follows the method review** (`reports/METHOD-REVIEW-2026-08-25.md`,
gitignored, on disk): the three changes below are the whole of it, and every
other finding waits, named here.

*Section D above holds unnumbered small consistency fixes and **no D1 appears in
this file**. D2 is not a consistency fix — it is a governing directive, carrying
the owner's own label, recorded under it unrenumbered rather than given a letter
that would file it as one more open question.*

> **D2, 2026-08-25 — the limits of this rebuild.**
>
> THREE changes, not ten: (1) settle §6.1, the contradiction between §5.3's
> limit-alert price and the DECK/PNDORA "never a price level" convention;
> (2) make Method C the engine, with MBP struck where implied growth equals a
> pre-registered bear case; (3) replace Gate 3's revenue and margin bands with
> the organic-basis decline kill and the explained-compression rule. Everything
> else in the method review waits, named in the backlog.
>
> NO NEW MEASUREMENTS while these three are open. Twenty-six E rulings and five
> §5 runs produced zero purchases because every ruling bred a measurement and
> every measurement bred a ruling. A question that arises during the rebuild is
> written down, not chased.
>
> A DEADLINE: 2026-09-08. When it passes the next name goes through the chain
> whatever is unfinished.
>
> AND THE THING THIS FRAMEWORK HAS NEVER ACCEPTED: the growth assumptions are
> guesses. g_bear, g_base and g_bull are written in advance with reasons and are
> never verified, because there is nothing to verify them against — they are my
> view, recorded so that being wrong is visible afterwards. E19–E26 raised the
> evidence floor on figures that move fair value less than 1% while the three
> inputs that move it more than 10% carry no evidence requirement at all. That
> inversion ends here: verification effort follows sensitivity, not
> availability.
>
> Record plainly what this costs: I will buy a company without knowing it is
> right, and no amount of work removes that. The framework's job is to make the
> error legible afterwards, not to prevent it.

#### The three changes, and the lines each one moves

The owner's labels are kept as given. The FRAMEWORK.md text that actually
changes is named beside each so the change is actionable, not because the label
is wrong.

**(1) The §6.1 contradiction — a limit-alert price against a dated event.**
Two lines carry the price-level convention: **§5.3's closing rule**, *"If
current price > MBP, the name goes to the WATCHLIST with a limit-alert price"*,
and **§6.3's last matrix row**, *"Price > MBP at all times | Watchlist + limit
alerts at MBP"*. Against them stand the DECK and PNDORA.CO verdicts, which say
**re-entry at a dated event, never a price level**. No B- or E-entry authorises
the reversal, and it currently governs both live WATCH names. This is queue
item 1 and the smallest in scope.

> **CLOSED 2026-08-25 by E27**, at the end of this file — **and it closed
> differently from the way this paragraph predicted, in two ways.**
>
> **The two lines named above do not move.** E27 leaves §5.3's rule and §6.3's
> row **standing as written** and narrows their **SCOPE** instead: both govern a
> **WATCH-PRICED** name and no other, and a **WATCH-GATED** name is outside
> them. **There was never a contradiction** — one status word carried two states
> whose re-entry rules are opposite. Both lines now carry a `SCOPE
> (FRAMEWORK-EDITS E27)` note in FRAMEWORK.md, and §6.3's says in terms that
> §6.4's stops are untouched.
>
> **And "both live WATCH names" was wrong: there were THREE.** `MC.PA` has
> carried *"Alert at 440 EUR. Not yet run through §3."* unchanged since before
> 2026-08-21 — so the price convention never stopped running, and the file held
> both conventions at once. It is the WATCH-PRICED instance, and its 440 is
> recorded as an **unvalidated alert, not an MBP**.
>
> **Two changes remain open**, and D2's bar on new measurements stands until
> they close.

**(2) Method C as the engine.** §5.1's **"minimum 2 of 3 methods"** and the
Method A and B rows are what a reverse-DCF engine displaces; §5.3's **MoS
tier table** (FV_base × 0.80 / 0.70 / 0.60) is what an MBP struck at the bear
case replaces. The order is binding and is the point of the change:
**g_bear, g_base and g_bull are written with reasons BEFORE g\* is solved for.**
This is queue item 2.

> **CLOSED 2026-08-25 by E28**, at the end of this file. §5.1's minimum-of-two
> rule and §5.2's divergence weighting are **deleted**; Methods A and B become
> context beside the engine, never requirements. **MBP is the price at which
> implied growth equals the pre-registered bear case**, with the tier cushion.
> The pre-registration order is binding and **a view written after the solve is
> void**. **One change remains open — (3), Gate 3's limbs — and D2's bar on new
> measurements stands until it closes.**

**(3) Gate 3's revenue and margin limbs.**

> **CLOSED 2026-08-25 by E30 — DELETED rather than replaced.** The organic-basis
> decline kill moved to §4.2.1; **no mechanical margin rule replaces the band at
> all**, and the reviewer's "bounded" wording was considered and rejected. B3,
> B4 and B20 are closed. **With this, ALL THREE of D2's changes are ruled — the
> measurement freeze lifts and the 2026-09-08 deadline is moot.**

§3 Gate 3's first two lines —
*"Revenue: growing, or stable within ±2% in the worst quarter"* and *"Gross
margin: band ≤ ±200bps unless explained by a Class C event"* — are replaced by
an **organic-basis decline kill** and an **explained-compression rule**. This
one is not on the old queue; D2 adds it.

**It absorbs three lettered items, and a reader arriving at any of them should
come here first:**

- **B3** (proposed, never decided) asked what ±2% is measured against. Change
  (3) removes the band the question was about.
- **B20** (raised 2026-08-25, not settled) asked which basis the revenue limb
  runs on — reported, organic or LFL — and showed PNDORA.CO passing on one
  column and failing on another. **The organic-basis decline kill is that
  answer**, and B20 is no longer independently open: it is inside change (3).
- **B4** was **DECIDED 2026-08-21** — ±200bps per quarter against the 8-quarter
  mean, Class C the only exception — and change (3) supersedes it. B4's entry
  stays where it is as the record of what was replaced and of the MSFT limb it
  flipped; it is not deleted, and until change (3) is written B4 is still the
  rule in force.

#### What D2 rules on directly, beyond the three changes

**Method-review finding 7 — verification effort follows availability, not
sensitivity — is DECIDED by the fourth paragraph above, not deferred.** It is
the only finding D2 settles outright. Its consequence is stated in the same
breath and is unusual enough to repeat: **the three growth inputs are exempt
from the evidence standard E19–E26 built**, because there is nothing to verify a
forward view against. They are pre-registered with reasons instead, and the
reason-writing IS the requirement.

**Finding 1 — the framework cannot say yes by construction — is engaged, not
deferred.** Change (2) removes the 2-of-3 rule that blocked all five §5 runs;
change (1) settles the event-only re-entry limb. The evidence-hardening limb of
finding 1 is what the paragraph above rules on.

**Finding 8 — no policy for idle sleeve cash — needs no ruling.** The handoff
disposes of it outside the repo: move the idle sleeve cash to the index core,
per C4's own rationale, *"the alternative to holding a satellite is always the
core, never cash"*. No code, no framework text.

#### What waits — named here, deliberately unlettered

Six method-review findings are deferred. **They are given no letter on purpose:**
a letter in this file is a live rule question the owner owes an answer to, and
D2's whole content is that these do not become that until the three changes
close. Each is restated in full below rather than cited by number, because
`reports/METHOD-REVIEW-2026-08-25.md` is gitignored and the numbering does not
survive the file.

1. **The uniform 9.5% discount rate is the largest unexamined number in the
   system** — and C4 turns it straight into sell orders. The UNA exit fired at
   9.5% and would not have fired at 9.0%. *This one is upstream of change (2):
   a reverse DCF solved for implied growth uses the same rate, so closing (2)
   without touching it moves the unexamined number from the exit rule to the
   engine.* Named as a consequence, not chased.
2. **The −8% to −12% stops fight mean-reversion entries** — the stop evidence
   supports stops under momentum only.
3. **Gate 1's catalyst leg plus Gate 2's default-to-D** admit only crowded,
   headline dislocations and refuse quiet derates (DECK), on the wrong side of
   post-earnings drift.
4. **The funnel is one-way and nothing measures the refusals** — no shadow book,
   so the process cannot learn from what it declines.
5. **§7's "at most 2 sectors" is a breadth cap, not a risk cap** — v2.3 replaced
   a sector ceiling with a sector floor.
6. **Roughly a third of FRAMEWORK.md is deadweight** — §2, the §6 pattern
   taxonomy, §4.4's arithmetic, Gate 4, the tranche matrix.

**Two cautions travel with these, and they are the owner's own.** They are
repeated here rather than left in the handoff because a later session will read
this list and not that one:

- **The live stops — SAP 165, LIAB 112 — are NOT to be changed on the strength
  of the method review alone.** This binds deferred item 2 above. The stop
  argument is sound; its key citation (Kaminski & Lo) is marked *medium
  confidence* in the review's own legend.
- **The review's §6.2 — "every krona of profit came from purchases the framework
  would have refused" — is four names in a rising market. Anecdote, not
  evidence.** It may not be used as support for any of the six.

**The old queue's remaining items wait too.** The code review (queue item 3) was
deferred deliberately, since a third of the code may be deleted depending on how
(1) and (2) are ruled. **The 52-week-range position measurement (queue item 4) is
expressly barred** by the no-new-measurements clause — it is a measurement, and
it does not run until the three changes close.

**And the open questions already in this file stay open and unchased** — B21,
and B18's successors: the aged frozen FX rate, the three-month stated ratio
standing at a twelve-month basis, the summable non-flows, the zero-denominator
cousins, and E22's cost. D2 does not close them and does not permit chasing
them. A question that arises during the rebuild is written down, not chased.

#### The deadline, and what it costs

**2026-09-08.** When it passes, **the next name goes through the chain whatever
is unfinished** — with the three changes in whatever state they are in. The
deadline is not a target for finishing; it is a limit on how long the chain may
stay stopped.

*And the cost is recorded in D2's own words rather than softened: **the owner
will buy a company without knowing it is right, and no amount of work removes
that.** The framework's job is to make the error legible afterwards, not to
prevent it. This entry exists so that when a purchase made under the three
changes goes wrong, what was assumed, what was verified and what was
deliberately left unverifiable are all readable in one place.*

---

### E27 — WATCH was two states, and they carry opposite re-entry rules

**DECIDED 2026-08-25 — the owner's ruling, recorded as given. This closes D2's
change (1) and queue item 1.** The basis document is
`reports/QUEUE-1-6.1-CONTRADICTION-2026-08-25.md`, gitignored and on disk; every
fact it rests on is restated here, because the ruling must survive the report.

> **WATCH has been doing two jobs and the two carry opposite re-entry rules.
> Split it.**
>
> **WATCH-PRICED** — the name passed §5 and is merely too expensive. **§5.3
> applies as written: a limit-alert price, armed, computed from MBP.** A price
> trigger is the correct trigger, because price is the only thing standing
> between the analysis and the purchase.
>
> **WATCH-GATED** — the name failed a gate in §3 and the failure was not about
> price. **Re-entry requires a named information event, never a price level**,
> because the price was not what disqualified it.
>
> **There was never a contradiction.** §5.3 and the DECK/PNDORA convention
> govern different situations and collided only because one word carried both.

#### The two states, and the living instances

| | WATCH-PRICED | WATCH-GATED |
|---|---|---|
| **Why it is waiting** | passed §5; price above MBP | failed a §3 gate, on something other than price |
| **What §5.3 does** | applies as written | does not reach it |
| **Trigger** | **a limit-alert price, computed from MBP** | **a named information event, never a price level** |
| **Instance** | `MC.PA` | `DECK`, `PNDORA.CO` |

**MC.PA is the living instance of the priced state** and has carried an alert at
**440 EUR since before 2026-08-21** — through twenty-six rulings and both
verdicts that say a price level is never a trigger. It was never reconciled with
them because nobody noticed the file held both conventions at once.

**DECK (2026-08-24) and PNDORA.CO (2026-08-25) are the living instances of the
gated state; both failed Gate 1's catalyst leg.** Their notes stand unchanged
and **both remain unbuyable on price alone.**

#### The convention accreted, and E12 ruled the OPPOSITE direction

Recorded because the ruling should not be read as ratifying how the convention
arrived. **It was never ruled before today.** The trail, with what each step did
and did not decide:

- **B1, DECIDED 2026-08-22** split Gate 1 into a level limb and a catalyst limb
  and made the level limb a reading of today's close. That is what creates the
  state "the price is right and the reason is missing" — the state both gated
  names are in. **B1 says nothing about re-entry.**
- **E11, RECORDED 2026-08-23** measured PNDORA.CO leaving the band because a
  2025-08-22 peak turned a year and a day old: *"A name can leave Gate 1's band
  on no new information at all."* An argument that a price reading alone is not
  information — **and not a rule about triggers.**
- **E12, DECIDED 2026-08-24, ruled the OPPOSITE DIRECTION.** Its text: *"Leaving
  PIPELINE requires an information event, not a re-reading of the band."*
  **E12 says a price move may not push a name OUT.**
- **The DECK note, written the same day, inverted it: a price move may not pull
  a name IN.** The inversion is plausible and was **not entailed** — E12's own
  text distinguishes an open position from a piece of review work and declines
  to generalise, and its justification is one ageing denominator, not price
  levels as such.
- **The PNDORA note, 2026-08-25, cited DECK** — *"This is DECK's test on
  2026-08-24 applied to a clearer case"* — and the convention then entered
  `config/screener_exclusions.csv` for both names and acquired an implementation
  in `vss/watch.py`.

**Four carriers, one implementation, zero rulings. That inversion is now ruled,
not assumed.**

#### An alert level is NOT an MBP

**The distinction is the owner's own, written on the NKE row on 2026-08-21** and
still in the file:

> Alert at 40 USD. **An alert level is NOT an MBP — compute properly.**

**An alert on a WATCH-PRICED name is a computed MBP or it is nothing.**

**MC.PA's 440 predates any §5 run on the name** — LVMH has no `fv_base`, no
`tier`, and its own note says *"Not yet run through §3."* It is therefore an
**UNVALIDATED ALERT**: it **stays as an alert**, it is **labelled as
not-an-MBP**, and **the name is not buyable at it.** The label is carried on the
entry itself, not only here, so that a reader of the watchlist cannot mistake
440 for a maximum buy price.

*So WATCH-PRICED admits two kinds of alert — a computed MBP, which is
actionable, and an unvalidated level, which is a reminder to do the work. The
status does not distinguish them; the presence of `fv_base` and `tier` does, and
`vss` says which it is reading.*

#### The schema

**`VALID_STATUSES` gains the two and loses the bare `WATCH`.** Every existing
`WATCH` row is migrated **with its reason stated on the row**. Anything that
reads `WATCH` in code is updated, and **a test pins that no bare `WATCH`
survives** — in the vocabulary, in the shipped watchlist, and in the example
file.

Bare `WATCH` is **rejected by the validator**, not silently accepted or
auto-migrated. A file that still carries it is a file whose author has not yet
said which of the two states the name is in, and that is a question only a
person can answer.

#### Two things this ruling does NOT do

**Stated so they are not read into it.**

1. **It does not decide whether a gate-failed name may carry a tier.** MBP needs
   a tier; a tier follows the §4.4 conviction score; §3 says a failed gate
   disqualifies; and **no rule answers.** Recorded as **B22**, below, because it
   is what WATCH-PRICED would need if a gated name were ever promoted. It does
   not bind today: no gated name is being promoted, and MC.PA's problem is that
   it has never been through §3 at all, not that it failed a gate.
2. **It does not touch §6.4's stops.** **SAP.DE 165 and LIAB.ST 112 are price
   levels, they are live, and they are outside this ruling entirely.** "Never a
   price level" is a rule about **re-entry** and has never been asserted about
   exits. Read as a general principle it would take the stops with it; it is not
   one.

---

### B22 — may a gate-failed name carry a tier?

**RAISED 2026-08-25 by E27, which expressly does not decide it. OPEN.**

**The question.** §5.3's MBP is `fv_base × tier multiplier`, and the tier follows
the §4.4 conviction score. §3's opening line is *"A candidate must pass ALL five
gates."* §4.4's scale ends *"≤ 4: Drop or watchlist."* **So the framework both
disqualifies a gate-failed name and provides a route by which one lands on the
watchlist — and says nothing about whether it may then carry a tier, which is
what an MBP, and therefore a WATCH-PRICED alert, requires.**

**Why it is not academic.** DECK's green flags are on record — revenue growth in
all eight trailing quarters, net cash 1,131m, interest coverage 499×, guidance
**raised** on 2026-07-23 through the drawdown, §4.2 untouched. A §4.4 score of
5–6 is reachable on greens even with a gate lost, depending on **how "gates
passed" is counted — which is B6, also open.** So the answer decides whether a
name like DECK can ever move from WATCH-GATED to WATCH-PRICED, or whether the
gated state is terminal until the gate itself passes.

**Not settled here, and not chased.** D2 bars chasing it: a question that arises
during the rebuild is written down. **Nothing today depends on the answer** —
both gated names are gated on Gate 1's catalyst limb, and MC.PA is
WATCH-PRICED without ever having been through §3, so no name is currently
waiting on this ruling.

---

### E28 — Method C is the engine

**DECIDED 2026-08-25 — the owner's ruling, recorded as given. This closes D2's
change (2) and queue item 2.**

> **Method C is the engine.** §5.1's **minimum-of-two rule** and the
> **25%-divergence weighting** are **DELETED**. A reverse DCF on **filed TTM
> free cash flow, net debt and a stated share count** produces the fair value on
> its own; **Methods A and B become context shown beside it, never
> requirements.**
>
> **MBP is the price at which implied growth equals the pre-registered bear
> case**, with the tier cushion applied.
>
> **The pre-registration order is binding:** g_bear, g_base and g_bull are
> written with reasons **BEFORE g\* is solved**, and **a view written after
> seeing the implied growth is VOID.**

#### What this deletes, and why it had to go

**§5.1's "minimum 2 of 3 methods" is struck.** It was the rule that stopped the
chain five times: **LULU, DECK, JD.L, PNDORA.CO and BETS-B.ST all reached §5 and
none produced a fair value**, every time for the same reason — Method A needs an
NTM consensus EPS the framework bars from auto-fill, Method B needs a peer set
and peer median that have never been assembled, and two of three could therefore
never be met. **A rule that has refused every name it has ever seen is not a
standard; it is a stop.**

**§5.2's divergence weighting goes with it.** *"If methods diverge > 25%, explain
why and weight toward the more conservative"* presupposes two or more methods to
weight. With one engine there is nothing to weight, and a weighted average of an
engine and a context figure would smuggle the deleted requirement back in.

**Methods A and B are NOT deleted — they are demoted.** They are shown beside
the fair value as context, and **a divergence between them and the engine is
reported, not reconciled.** DECK is the standing example: Method A gave 180–184
on a trailing proxy multiplied into company guidance, which is a fact worth
seeing beside the engine's answer and never a fact to average into it.

#### What MBP now is

**MBP = the price at which implied growth equals g_bear, with the tier cushion
applied.** The MoS tiers keep their multipliers (T1 0.80 / T2 0.70 / T3 0.60)
and §5.3's regime adjustment is unchanged.

**The change of meaning is the point.** The old MBP was a discount off a
weighted-average point estimate — a cushion against a number nobody could
defend. **The new MBP is the price at which the market is already paying for the
bear case**, so the cushion sits on top of an assumption that was written down
in advance, with reasons, and can be read back afterwards.

#### The pre-registration order, and the void rule

**Binding, and the reason it is binding is that it is trivially cheatable.**
Solving for g\* first and then writing a bear case just below it produces a fair
value above the price every time, with every appearance of rigour.

**So: a growth view written after the implied growth has been seen is VOID** —
not weak, not to be discounted, but void. It may not be used for that name in
that cycle. The remedy is a new pre-registration written before the next solve,
dated, in `reference/growth-views/<TICKER>.md`.

*The mechanics: `reference/growth-views/` holds one file per name; the three
rates are never edited; a changed view is a new dated entry beneath the old one.
`reference/growth-views/DECK.md`, written 2026-08-25 before any search and
before any solve, is the pattern.*

#### What this costs, recorded rather than softened

**The fair value now rests on a growth assumption that is a stated opinion and
will never be verified.** There is nothing to verify it against.

**That is deliberate.** E19–E26 raised the evidence floor on figures that move
the answer **under 1%** — a lease liability the issuer never totals, a share
count derived from par value, a zero without a stated basis — while **this one
moves it 30%**. D2 named that inversion and ended it: **verification effort
follows sensitivity, not availability.** E28 is where the consequence lands.

**Stated plainly:** the engine is exact arithmetic over an input that is a
guess. The exactness is real and it is not evidence. **What the framework buys
with this is not a better estimate — it is a legible error**, one that can be
read back afterwards against what actually happened.

#### What E28 does NOT do

- **It does not touch the discount rate.** r remains the uniform 9.5%, which the
  method review named as the largest unexamined number in the system
  (**deferred finding 1 under D2**, still open). **E28 makes it matter more, not
  less** — the engine is now the only method, so r moves every fair value the
  framework produces. Recorded here so the exposure is visible and so nobody
  reads E28 as having settled it.
- **It does not decide B22** — whether a gate-failed name may carry a tier. MBP
  needs one, and the question is open. A name with no tier has an implied-growth
  fair value and **no MBP**, which is a legitimate state.
- **It does not change §3, §4 or §6.** A fair value is not an entry, and
  **E27's split stands**: a WATCH-GATED name is not woken by a price, whatever
  the engine says about it.
- **It does not authorise a purchase on the engine alone.** §0 rule 4 is
  unchanged — below price X, under conditions Y, with stop Z.

---

### E29 — r is the owner's hurdle rate

**DECIDED 2026-08-25 — the owner's ruling, recorded as given.** The basis is
`reports/DISCOUNT-RATE-2026-08-25.md`, gitignored and on disk; every fact the
ruling turns on is restated here so the entry survives the report.

> **r is MY hurdle rate, not an estimate of what the market demands.**

**That settles the question the report found underneath all four it was asked:
the framework never said which of the two r was.** FRAMEWORK's only mention was
a parenthetical — *"discount 9–10%"* in §5.1's Method C row — with no
derivation, no source and no note anywhere in the file. The single written
reason in the whole repository was a margin note about a different name
(*"uniform 9.5% is the least flattering for a defensive — noted, not
changed"*, `una-scoring-evidence.md`, 2026-08-22).

#### 1. FLAT ACROSS ALL NAMES

> **A hurdle rate is a statement about what I require to move capital out of the
> index core, not about a company or a currency, so it does not vary by market,
> sector or capital structure.**

**This deliberately declines the report's own strongest technical objection**,
and the objection is recorded here rather than dropped, because a later reader
must be able to see what was knowingly accepted:

> A flat nominal rate demands **~180bp more risk premium of a Swedish issuer
> than of a US one** — 10-year government yields on 2026-08-25 were **US 4.66%**,
> **German Bund ~3.2%** (DKK is pegged to the euro) and **Sweden ~2.90%** — for
> no reason connected to either business. The model is also an **enterprise**
> DCF, which by construction wants a WACC, and DECK carries zero borrowings
> while JD.L carries £2,827m of net debt after leases.

**The owner's ground for accepting the asymmetry:** *"the alternative adds a
second owner-set lever per name at the moment E28 made g the single one, and E28
makes g pre-registered and auditable while r would not be."*

**That is the decisive asymmetry between the two numbers and it is worth stating
plainly.** E28 requires g to be written with reasons **before** g\* is solved,
and voids a view written afterwards. **No comparable discipline exists or is
proposed for r**, so a per-name r would be an unaudited continuous dial on the
most sensitive input in the model — worth **about 13.65 on DECK's Tier 1 MBP per
100bp**, which is larger than the gap between any recent price and any recent
threshold.

#### 2. ANCHORED, NOT INVENTED

> **r = the long-run expected return of the index core plus 2–3 percentage
> points**, the premium being what I require for carrying single-company risk
> instead of doing nothing.

**Today that lands at 9.5%, so nothing computed changes** — the DECK run of this
evening stands unaltered. **What changes is that the number now has a reason
and, more importantly, a condition under which it should change.**

> **Record my own words: 9.5% is fine for me today, but it depends on what index
> is expected to return, and in a market priced for much more it would be too
> low.**

**C4 already says the alternative to a satellite is always the core, never cash.
This makes r say the same thing.** The two rules now rest on one premise instead
of contradicting each other by silence.

**The trigger is therefore explicit: if the index core's expected return moves
materially, r moves with it.** A hurdle rate anchored to nothing is a number; a
hurdle rate anchored to the core is a number with a maintenance rule.

#### 3. FROZEN FOR ENTRY, RE-STRUCK FOR EXIT

**The report's third way, adopted.**

- **The rate used to strike a PURCHASE is frozen with that verdict**, as E24
  froze FX. It is recorded on the entry with the facts that make it
  re-derivable, and a partial record is refused.
- **An exit under C4 is RE-STRUCK at today's rate.**

**The reason the two differ is C4's own text:** *"A reversion level set months
earlier is a statement about where the thesis was, not about what the capital
can earn next."* **Running C4 against a stale hurdle rate is exactly that
error** — C4 asks what the capital can earn next, and a hurdle rate is the
answer to that question as of now.

*This also gives E24's open successor — when a frozen rate has aged too far to
stand — a partial answer for r and only for r: **the entry rate never ages,
because it is a record of a commitment rather than a live input; the exit rate
is never frozen, so it cannot age at all.***

#### 4. NO SENSITIVITY VETO

> **The ±0.5% rule is NOT adopted.**

**Grounds, recorded because refusing a proposed safeguard needs them more than
accepting one would:**

- **It can only remove a conclusion, never produce one**, and this framework's
  diagnosed defect is that it cannot say yes — **five §5 runs, zero fair
  values, PIPELINE empty.** A rule whose only possible output is NO is a serious
  thing to add to a system that has never said yes.
- **It would have struck the one reading that made DECK buyable tonight** —
  Tier 1's MBP of 89.30 against a price of 88.55 reverses at r = 10.0% — while
  leaving Tier 2 and Tier 3, which are invariant, untouched.
- **It would have refused the UNA.AS sale of 2026-08-22**, where C4's condition
  was met at 9.5% and not at 9.0%.

**Instead:**

> **Every MBP is REPORTED with its value at r − 0.5% and r + 0.5% beside it, so
> I can see when a threshold comparison is fragile and judge it myself.
> Fragility is DISPLAYED, never ADJUDICATED.**

**The distinction is the whole content of this clause.** The same three numbers
the vetoed rule would have computed are still computed and still shown; what is
refused is the automatic conclusion drawn from them. **The owner sees the band
and decides; the framework does not decide on the owner's behalf by refusing.**

*Implementation note, so the rule cannot be followed by accident: the valuation
module has **no scalar MBP function**. An MBP is only obtainable as a triple at
(r − 0.5%, r, r + 0.5%), so a caller cannot report a bare threshold without
having gone out of its way.*

#### What this costs

> **r is now explicitly a preference rather than a measurement, and it will
> never be verified against anything.**

**That is the same admission E28 made about g, and it is deliberate.** The
owner's ground: **an owner-set number that says so is safer than one that
pretends to be empirical.**

**Stated in the terms D2 set:** verification effort follows sensitivity, not
availability. **The two inputs that move the answer most are now both declared
opinions** — g pre-registered with reasons and auditable afterwards, r anchored
to the core with a stated condition for changing. **Neither is evidence, both
say so, and that is the point.**

*What the framework gives up by this ruling, recorded once: it can no longer
claim its fair values are estimates of what a company is worth to the market.
They are estimates of what it is worth **to this owner, at this hurdle**. Two
people running this framework with different core expectations would get
different fair values from identical filings, and that is now correct behaviour
rather than a defect.*

#### What E29 does NOT do

- **It does not change any computed figure today.** 9.5% was the rate before and
  is the rate after; the DECK numbers of 2026-08-25 stand.
- **It does not touch g, the terminal rate or the ten-year horizon.**
- **It does not reconcile `mbp`'s DERIVATION with E28.** The schema still
  computes `mbp = fv_base × tier multiplier`, while E28 defines MBP as the price
  at which implied growth equals g_bear, with the cushion on that. **Three live
  HELD rows carry the old derivation.** Recorded as an open item rather than
  changed on a ruling about the discount rate — see **B23**.

---

### B23 — `mbp`'s derivation in the schema does not match E28

**RAISED 2026-08-25 by E29, which expressly does not decide it.
SETTLED 2026-08-25 by E32 — see below. The text is kept as it was written,
because what it got wrong is the finding: it framed this as two definitions
competing, and E32's ruling is that they never were.**

**The gap.** `vss/rules.py` derives `mbp = fv_base × tier multiplier`, which is
FRAMEWORK §5.3 as written before E28. **E28 redefined MBP as the price at which
implied growth equals the pre-registered g_bear, with the tier cushion applied
to that** — a different quantity, since `fv_base` is the BASE case and the new
MBP is struck off the BEAR case.

**What depends on it.** Three HELD rows carry `fv_base` and `tier` and therefore
a computed `mbp` on the old basis: **UNA.AS (43.5, Tier 2), LIAB.ST (102.66,
Tier 2), SAP.DE (185, Tier 1)**. Changing the derivation changes all three, and
C4 reads the same figures.

**Not settled here, and deliberately not changed on a turn about the discount
rate.** The new engine in `vss/valuation.py` computes E28's MBP correctly and is
not yet wired to the watchlist's derived field; the two definitions coexist,
which is visible rather than hidden. **D2's change (3) is still open and its bar
on new measurements stands**, so re-striking three live positions is not a step
to take incidentally.

---

### E30 — Gate 3's revenue limb and gross-margin band are DELETED

**DECIDED 2026-08-25 — the owner's ruling, recorded as given. This closes D2's
change (3) and queue item 3, and with it D2 itself.** The material is
`reports/QUEUE-3-GATE-3-BANDS-2026-08-25.md`, gitignored and on disk; the facts
it turns on are restated here.

> **Gate 3's revenue limb and gross-margin band are DELETED. Not widened, not
> replaced with a softer number — removed.**

#### Why

**Three grounds, in the owner's words:**

1. **"Neither has ever decided anything."** Across the five §5 names the
   proposed replacement **changes no verdict** — LULU, DECK, JD.L, PNDORA.CO and
   BETS-B.ST all end where they ended. **The bands were never load-bearing.**
2. **"Both measure the volatility of REPORTED figures, which is dominated by
   currency, mix and season, none of which is quality."** The three cases are on
   record: DECK's two breaches are **both upward and both the Oct–Dec quarter**
   when UGG's mix peaks; PNDORA's revenue limb reads **−3.2% reported against
   +2% organic in the same quarter**; BETS's fall is two causes the band cannot
   tell apart.
3. **"I know of no research showing that margin stability over eight quarters
   separates good businesses from bad."** §8 of the method review rates both
   **INVENTED** and could find no ancestor for either; its guess is that **200bp
   is §4.2.2's 150bp rounded up** and ±2% a round number. **"The honest response
   to an invented threshold that decides nothing is to delete it rather than to
   tune it."**

#### What replaces the revenue limb

> **§4.2.1's demand-fade kill on an ORGANIC basis. This settles B20 and B3.**
>
> **Reported currency movement is not demand loss** — PNDORA.CO's case, where
> the same quarter read **−3.2% reported and +2% organic**.
>
> **And the mirror JD.L exposed also holds: reported-up while organic-down is
> declining, and the reported figure does not rescue it.**

**This completes B9 rather than contradicting it.** B9 ruled the first half on
UNA.AS — *reported down, organic up, NOT a kill*. **E30 rules the second half on
JD.L — reported up, organic down, IS a kill.** One rule, both directions:
**§4.2.1 measures demand, and organic is the measure of demand.**

*JD.L's figures, for the record: reported revenue **+10.5%**, organic **−0.1%
then −1.3%**, LFL **−2.5% then −3.1%**. Under the deleted revenue limb JD.L
**passed**; under §4.2.1 on an organic basis it is a hard kill.*

**Organic is not LFL.** PNDORA disclosed organic **+2%** and LFL **0%** in the
same quarter, and E30 names organic. Where an issuer discloses only a
like-for-like figure, that is not an organic figure and the basis falls back to
reported, **with the report saying which it read** — which is B20's actual
requirement and the reason B20 does not simply vanish with the limb.

#### What replaces the margin band

> **Nothing mechanical. Sustained compression is read and judged, and the
> judgment is written into the verdict with the issuer's own numbers.**

**The owner's ground is a worked case, not a preference:**

> **"I have already done this without a rule and done it better than a rule
> would: on BETS-B.ST I separated a structural tax effect from a Turkish
> enforcement collapse, and no threshold made that distinction — I did."**

**B4 is superseded.**

#### What this costs, recorded plainly because it is the strongest argument against it

> **"A band that is wrong is wrong loudly and forces a written objection; a
> judgment that is wrong produces a paragraph. I am removing a mechanical check
> in a framework whose whole purpose is to make my errors legible afterwards,
> and I am relying instead on the record — every margin judgment goes into the
> verdict with the figures, so a future reader can see what I concluded and from
> what."**

**That last clause is the substitute for the mechanism and should be read as
binding:** a margin judgment that does not carry the issuer's figures into the
verdict text leaves nothing for a later reader to audit, and the deletion of the
band is what makes it load-bearing.

#### The reviewer's own version, considered and REJECTED

**Recorded so nobody reinstates it later believing it was overlooked.** The
method review proposed keeping a judgment rule with thresholds: *"sustained
compression (>150bp YoY for 2+ quarters, or >300bp cumulative over four) that
the issuer does not explain and quantify is a kill; compression fully attributed
in the filing to a named, dated, **bounded** driver… is recorded, not killed."*

> **"It kept a judgment rule turning on whether compression is 'bounded', and
> BETS-B.ST dies on a strict reading of that word and survives on a loose one.
> A rule that reverses on a word is not a rule, so no such wording enters
> FRAMEWORK."**

**The demonstration is exact.** BETS's regulated revenue share went **59% to
75.5% in five quarters** and the verdict records that *"no source gives a level
where it plateaus"* — **named yes, quantified yes, bounded expressly no.**
Strict reading: killed on the tax mix, the very component the review says the
band caught wrongly. Loose reading: excused, and the drop rests on Turkey, which
no rule encodes. **Same rule, same filing, opposite outcomes.**

*Note also what the rejected version would have done by side effect: it dropped
§4.2.2's "flat/declining revenue" condition, which would have decided **E9**
without ruling on it. **E30 adds no mechanical margin rule at all, so §4.2.2 is
untouched and E9 remains open.***

#### What is closed, and what is untouched

**CLOSED BY E30:**

- **B3** — proposed 2026-08-20, never decided. It asked how to read a limb that
  no longer exists. **Closed without ever being ruled**, and the entry stays as
  the record of a question the framework ran on for a month unanswered.
- **B4** — DECIDED 2026-08-21, **superseded**. *The reversal is real and is not
  softened: a decided entry is being undone four days later.* **What survives is
  its outcome** — MSFT's gross-margin YoY moves were −180, +33, −137, −100, −31,
  −66, −108, −139bp, so **no margin rule of any kind now fails MSFT**, which is
  the answer B4 gave. **The instrument goes; the verdict it produced does not
  change.**
- **B20** — raised 2026-08-25, **settled**: the basis is **organic**, and it now
  lives in §4.2.1 rather than in Gate 3.

**UNTOUCHED:** Gate 3's **leverage, coverage, FCF and integrity** limbs stand
exactly as written. **E9, B22 and B23 remain open** and E30 decides none of them.

---

### D2 IS CLOSED

**All three changes are ruled.** For the record, in one place:

| D2's change | closed by | date |
|---|---|---|
| **(1)** the §6.1 contradiction | **E27** — WATCH split into WATCH-PRICED and WATCH-GATED | 2026-08-25 |
| **(2)** Method C as the engine | **E28**, with **E29** settling the rate it runs on | 2026-08-25 |
| **(3)** Gate 3's revenue and margin bands | **E30** — deleted | 2026-08-25 |

**Three consequences follow immediately and are recorded here so nobody has to
infer them:**

1. **The measurement freeze LIFTS.** D2's *"NO NEW MEASUREMENTS while these
   three are open"* is spent. Measuring is permitted again.
2. **The deadline of 2026-09-08 is MOOT.** It existed to stop the rebuild
   running indefinitely, and the rebuild is finished fourteen days early.
3. **D2's deferred six are still deferred**, and lifting the freeze does not
   promote them. They are: the discount rate *(now partly answered by E29 — the
   rate is a declared preference, though the review's separate objection that it
   is unexamined as a market estimate is retired rather than met)*, the
   −8/−12% stops, Gate 1's catalyst leg with Gate 2's default-to-D, the shadow
   book, §7's sector cap, and the deadweight sections. **The two cautions still
   ride with them:** the live stops (SAP 165, LIAB 112) are not to be moved on
   the method review's authority, and §6.2's four-names-in-a-rising-market
   argument may not be used as support.

**What is open after D2:** **E9** (§4.2.2's undefined "flat"), **B21** (E25's
subtotal form), **B22** (may a gate-failed name carry a tier), **B23** (`mbp`'s
derivation against E28), and B18's remaining successors. **None of them blocks a
name from going through the chain.**

---

### E31 — a fiscal-year basis is acceptable for a half-yearly reporter, and the report names what it passed over

**DECIDED 2026-08-25 — the owner's ruling on R0, recorded as given.**

> **A fiscal-year basis IS acceptable for a half-yearly reporter. Section 5 runs
> on the year as filed. But the report MUST NAME every filed period in the file
> that falls inside a twelve-month window NEWER than the basis and that the
> basis did not read — naming the period label, its window end, and the fact
> that it was not read. No staleness cap is set here.**

#### What this settles, and what it expressly does not

E19 named two reporter kinds — annual and quarterly — and was silent on the
third. **E31 answers the half-yearly case at the level of the BASIS: the year as
filed is a twelve-month window and §5 may stand on it.** That was already what
the code did; a `YYYY-FY` row in `periods:` takes `section5_basis`'s first
branch and an `annual:` entry takes its third, and neither branch asks what
frequency the ticker reports at. **The ruling makes the behaviour a rule rather
than an accident of two length tests.**

**It does NOT settle R1.** Whether a twelve-month basis may be BUILT from
half-year periods — two tiling halves summed, the way four quarters are — is a
separate question and is **not ruled here**. `section5_basis` still has no
half-yearly branch, `period_months` of a half-year is 6, and six is neither the
twelve the first branch tests for nor the three the second does. A file of four
tiling half-years still supplies **no basis at all**, and §5 still does not run
on it. That remains B12's question, now carried into §5 by E19's extension of
E13.

**It does NOT set a staleness cap**, and `MAX_REPORT_AGE_DAYS` is untouched at
550. What the cap should be is **B24**, raised below.

#### Why the naming is the price, and not a courtesy

A fiscal-year basis is the OLDEST twelve months the file can stand on, not the
newest. A half-yearly reporter that has filed its H1 holds six months of
published figures the basis does not read, and after its H2 or a second H1 it
holds a full twelve months that the basis still does not read — **the company's
own newer accounts, sitting in the file, invisible to the run.** E19 already
established the shape of the answer for a different case: *"the report names the
four periods beside every TTM figure it uses… A §5 figure the accounts do not
print must say what it was built from, every time it appears."* E21 established
the other half: a figure the basis does not reach is **named in the report
rather than hidden**, visible and not blocking.

**E31 applies both to periods rather than to figures.** The run is not weakened
and nothing is refused; the reader is told what the basis passed over, so that a
number struck on a year that closed six months ago cannot be read as though it
were current without the file having said so.

#### Implemented, 2026-08-25 — the disclosure limb only

- **`newer_filed_periods(parsed, basis)`** in `vss/manual.py`, beside
  `section5_basis`. The window is the twelve months ending at the **newest filed
  period end**, and it exists only where that end is **newer than the basis
  end** — otherwise the file holds nothing the basis has not reached.
  Membership is decided **on ENDS alone**, because a fiscal filer's label says
  nothing reliable about the day its period opened. **The consequence is that a
  period which ENDS inside the newer window but BEGINS before the basis end is
  still named** — a half-year closing on the basis end itself, whose whole span
  the basis year already covers, appears in the list. **Over-naming is the
  deliberate direction**: a period named that the basis in fact read through its
  annual entry costs the reader a line, and a period silently omitted costs them
  the thing E31 exists to show. Periods the basis read are excluded **by label**,
  which the overlap guard makes unique within a file, so a `ttm` basis is never
  told it skipped the four quarters it summed.
- **`Section5Gate.newer_filed`**, carrying `ManualPeriod` objects. It is **not**
  `Section5Gate.unread`, which is E21's unverified FIGURES; the two sit next to
  each other in the report and are different things.
- **The report prints `## FILED, NEWER THAN THE BASIS, AND NOT READ`** with the
  period label, its window end and `NOT READ`, **whether or not §5 is refused** —
  the naming is the condition attached to the basis and does not depend on
  whether some other reason refuses the run. **If there are none it prints
  nothing.**
- **`section5_basis` is UNCHANGED.** Which basis is chosen is exactly what it
  was before this ruling.

**The rule is FREQUENCY-BLIND, and deliberately so.** E31's words are *"every
filed period"*, not "every filed half-year", and the implementation asks nothing
about `reporting_frequency`. It therefore also fires on a QUARTERLY file whose
basis has fallen back to `annual:` — two filed quarters and a year, say, where
four consecutive quarters are not there yet: the two quarters are named exactly
as two halves would be. A quarterly file standing on a `ttm` basis is silent,
not because it is quarterly but because its basis already ends at the newest
filed period end and there is nothing newer to name.

**One wording fix went with it, and nothing more.** The `NO TWELVE-MONTH BASIS`
refusal counted quarters and nothing else, so a file holding four tiling
half-years — twenty-four months of filed figures — was described as
**`0 quarter(s)`**, which reads as an empty file. It still counts quarters,
because that is what the basis rule needs, and it now also names the periods the
file actually holds. **No new unit logic was added**, and no half-yearly branch
was written.

---

### B24 — the distance between the basis end and the price date

**RAISED 2026-08-25 by E31, which expressly sets no cap. OPEN.**

**The gap.** E19's basis takes flows **and** stocks at the window's end.
`MAX_REPORT_AGE_DAYS` is **550**, so a fiscal-year basis stays non-STALE for up
to roughly **eighteen months** after the year closed — and E31 has just made a
fiscal-year basis the ordinary case for a half-yearly reporter rather than a
fallback. Every §5 output is a quantity from that window divided into a price
from today.

**What is not decided.** What the cap should be. **It should be set from
MEASUREMENT rather than by choosing a number now** — what the distribution of
basis-end-to-price-date distances actually looks like across the names the chain
has run, and where a quotient starts to mean something different. Nothing here
proposes a figure.

*Note the two clocks that already disagree: `staleness()` measures on
`parsed.newest_period_end` — the newest row in the FILE — while `section5_gate`
measures age on `basis.end`. On a half-yearly file holding an H1 the file reads
fresher than the basis it runs on, and E31's new section is where that gap
becomes visible.*

---

### B25 — E31's collision with Gate 1

**RAISED 2026-08-25 by E31. OPEN, and related to B24 without being the same
question.**

**The gap.** §3 Gate 1 admits a name **because it recently fell**. A fiscal-year
basis can be dated **BEFORE the fall**. Section 5 would then measure the company
as it was **before the reason for admission existed** — the drawdown that put
the name in front of the framework is a fact the basis has not seen.

**Why this is not B24.** **B24 is about AGE**: how far a basis may sit from the
price before the quotient stops meaning anything. **B25 is about ORDERING**: a
basis can be well inside any age cap and still predate the event the name was
admitted on. A tighter cap would narrow this but would not answer it, and a name
admitted on a fall three months old sits inside every plausible cap.

**Not decided here**, and E31 does not decide it. What E31 does supply is the
material to see it: the periods the basis passed over are now named, so a reader
comparing them against the catalyst date has both on the page.

---

**WHAT IS OPEN, as of E31 (2026-08-25):** **E9** (§4.2.2's undefined "flat"),
**B21** (E25's subtotal form), **B22** (may a gate-failed name carry a tier),
**B23** (`mbp`'s derivation against E28), **B24** (basis end to price date),
**B25** (E31 against Gate 1), B18's remaining successors, and **R1 / B12** —
whether a twelve-month basis may be built from half-year periods, which E31
expressly leaves unruled. **None of them blocks a name from going through the
chain**, and R1 blocks only the two half-yearly names from reaching §5 on
anything newer than their own fiscal year.

---

### E32 — there were never two MBP definitions, and E28's governs

**DECIDED 2026-08-25 — the owner's ruling on B23, recorded as given. This
SETTLES B23.**

> **There are not two competing MBP definitions. E28 states one and the code
> implements the other, and only the code computes anything. E28's definition
> governs from here: MBP is the price at which implied growth equals the
> PRE-REGISTERED bear case, with the tier cushion applied. The schema's
> `fv_base × tier multiplier` is superseded as a definition.**
>
> **The three MBP figures already stored — SAP.DE 148.00, LIAB.ST 71.86,
> UNA.AS 30.45 — are NOT recomputed and NOT deleted.** They were struck under
> the superseded definition and **cannot be restruck**: E28 requires the bear
> case to be pre-registered BEFORE implied growth is solved, and for all three
> the bear rate was decided after. **That is a missing proof of ordering, not a
> missing figure, and no amount of reading reports supplies it.** Each keeps
> its number, carrying the definition it was struck under and the date.
> **A figure struck under a superseded definition is a record of what I
> decided, not a live buy price.**
>
> **This ruling does NOT settle what happens to `fv_base` itself.** SAP.DE's
> 185 and UNA.AS's 43.5 are weighted blends of Methods C and A — the weighting
> E28 deleted — so those inputs are artefacts of a struck rule. **Opened as
> B26; it is not decided here.**

#### What B23 got wrong, which is the finding

B23 was raised as *"two MBP definitions are live side by side"*. **They were
never side by side.** `vss/valuation.py`'s `maximum_buy_price` — E28's
definition, correct, tested — **is called by no production code**, only by
`tests/test_valuation.py`. `config.py` imports that module for `anchored_rate`
and nothing else. So the count was never two: **one definition was written down
in the framework and a different one was doing all the arithmetic.**

E28's own text is the corroboration. It names what it deletes — §5.1's
minimum-of-two, §5.2's weighting — and the derived field is not among them. Its
section contains **no occurrence** of `rules.py`, `compute_mbp`, "schema",
"watchlist" or "supersede". It did not fail to supersede the derivation; it
never addressed it. **E32 is that missing sentence.**

#### Why the three are kept rather than restruck

Not sentiment, and not cost. **The inputs E28 needs do not exist for any of the
three and cannot be recovered by reading:**

- **`g_bear` must be PRE-REGISTERED.** `reference/growth-views/` holds `DECK.md`
  and `ADBE.md` — nothing for SAP.DE, LIAB.ST or UNA.AS. E28: *"a view written
  after seeing the implied growth is VOID."* SAP.DE's implied growth (`A18`,
  0.0960) and its bear case (`A22`, 6%) were **both decided 2026-08-22**, with
  no dated pre-registration and no recorded ordering.
- **`fcf0`, `net_cash` and `shares`** are in no file the chain reads: there is
  no `config/manual/SAP.DE.yaml`, `LIAB.ST.yaml` or `UNA.AS.yaml`.

**So the gap is evidentiary, not arithmetic.** The bear-case fair value for
SAP.DE is recorded (144.07, at 6% growth, r 9.5%, terminal 2.5%, ten years), and
144.07 × 0.80 = **115.26** against the stored **148.00** — 22.1% lower. **That
number is not adopted here**, because the 6% it rests on has no proof of
ordering, and a figure that looks restruck but is not is worse than one openly
marked superseded.

#### Implemented, 2026-08-25

- **The watchlist schema gains `mbp_basis:`** — `definition:`
  (`fv_base_x_tier` | `e28_bear_case`) and `struck:` — both or neither, on
  `HurdleRecord`'s precedent. `struck` has **exactly two grammars**:
  `YYYY-MM-DD`, or **`on or before YYYY-MM-DD`** where the day is not
  recoverable. **There is no third form and a day is never invented.**
  LIAB.ST is why the second exists: its figure predates the oldest backup on
  disk and the watchlist was untracked in git then.
- **Filled for the three.** SAP.DE and UNA.AS `struck: 2026-08-22` — each
  absent from `config/watchlist.yaml.bak-2026-08-22-pre-sap` / `-pre-una` and
  present in `-post-sap` / `-post-una`. LIAB.ST **`on or before 2026-08-21`**,
  and no more precise than that.
- **ABSENCE DOES NOT MEAN LIVE.** `rules.compute_mbp` **is** the superseded
  definition and `maximum_buy_price` is wired to nothing, so **every `mbp` the
  chain can produce today is superseded whether or not a row says so.**
  `assess` marks on `mbp_definition != e28_bear_case`, which is true by default.
  **Over-marking is the deliberate direction — the same reasoning as E31's
  over-naming, and it is a pattern rather than an accident.**
- **Marked wherever it prints, from ONE flag.** `TickerAssessment.mbp_superseded`
  feeds `report._mbp_cell` (the actions table and the full table) and
  `rules.mbp_verdict`'s sentences. The mark is **appended, not substituted**:
  the arithmetic is unchanged and the old sentence still describes it truly;
  what is added is that the definition behind it no longer governs.
- **It travels to the STORE too**, as `mbp_superseded` and `mbp_struck` columns
  on `run_metrics`, migrated in. A number read back out of that table months
  from now must not look live because the report that marked it is gone.
- **`compute_mbp` and `mbp_verdict` keep working unchanged.** No verdict flips:
  all three names trade far above both candidate figures.

#### The wiring is DEFERRED, deliberately

**`valuation.maximum_buy_price` is NOT wired into the live chain in this turn.**
It waits on inputs that exist for **no held name**: a pre-registered `g_bear` in
`reference/growth-views/<TICKER>.md`, plus `fcf0`, `net_cash` and `shares` from
a `config/manual/<TICKER>.yaml`. It also has **no scalar form** and must not
grow one — E29 requires every MBP to be reported across the ±0.5% band, so it
returns a `Sensitivity`, and `TickerAssessment.mbp` is a float. **Wiring it
before the inputs exist would produce a number from defaults nobody chose**,
which is the failure this whole section is built to prevent.

#### How a held name regains a live MBP

**By a growth view written BEFORE its implied growth is next solved**, and by no
other route. For **SAP.DE** that means before the **Q3 report on 2026-10-21**,
which is already its `catalyst_date` and its §6.4 reassessment point. **No
growth view is written here** — inventing one is the one thing E28's void rule
exists to prevent, and it is the owner's to write.

---

### B26 — `fv_base` itself is an artefact of a struck rule

**RAISED 2026-08-25 by E32, which expressly does not decide it. OPEN.**

**The gap.** E32 retains three MBP figures as records. But **two of the three
`fv_base` inputs behind them are §5.2 weighted blends — the weighting E28
DELETED.**

| | `fv_base` | how it was built |
|---|---|---|
| **SAP.DE** | 185 | `0.85 × fv_C 167.07 + 0.15 × Method A 285.92 = 184.90`, entered as 185 — *"§5.2 / §5.3 LOCKED 2026-08-22: Method B unused; weights C 0.85 / A 0.15; tier 1"* |
| **UNA.AS** | 43.5 | `0.90 × fv_C 40.47 + 0.10 × Method A` → *"fv_base 43.47, entered as 43.5"* |
| LIAB.ST | 102.66 | not established here |

Both quoted from the builders in `scratch/`.

**Why this is not E32.** E32 rules on the **MBP** — the number the chain
computes and prints — and marks it. **`fv_base` is an INPUT the owner entered
by hand**, it is not derived by any rule, and E28 deleted the weighting that
produced it without saying what becomes of a figure already struck that way.
**A retained MBP marked as superseded still rests on an input built by a rule
that no longer exists**, and E32's marking does not reach one layer down.

**Not decided here.** What is open: whether `fv_base` on those rows should be
marked in the same way, restated as the Method C figure alone, or left exactly
as it is on the same reasoning E32 uses for the MBP — that it is a record of a
decision rather than a live input. **LIAB.ST's derivation was not established**
and would need to be before anything is ruled.

---

**WHAT IS OPEN, as of E32 (2026-08-25):** **E9** (§4.2.2's undefined "flat"),
**B21** (E25's subtotal form), **B22** (may a gate-failed name carry a tier),
**B24** (basis end to price date), **B25** (E31 against Gate 1), **B26**
(`fv_base` as an artefact of §5.2's deleted weighting), B18's remaining
successors, and **R1 / B12** — whether a twelve-month basis may be built from
half-year periods. **B23 is SETTLED by E32.** Of these only **R1/B12** blocks a
name from going through the chain, and only the two half-yearly ones.

---

### E33 — operating lease payments are an OPERATING COST, and basis 2 is the retailer's default

**DECIDED 2026-08-25 — the owner's ruling, recorded as given. Raised by the
SYNSAM.ST §5 run, where the choice of FCF basis inverted the answer.**

> **Operating lease payments are an OPERATING COST, not a financing item.
> Section 5's FCF basis deducts lease capital repayments for any issuer whose
> business cannot run without the leased assets — a retailer's shop rent is as
> compulsory as its wages, and IFRS 16 moving it onto the balance sheet is a
> presentation change, not an economic one. The leases do not end: contracts
> expire and are renewed, so a ten-year DCF that does not deduct them assumes
> the premises become free. Basis 2 is the default for store-based retailers.
> Where the leased assets are incidental to the business, basis 1 may still be
> used, and the choice is named in the verdict.**
>
> **This does not reopen any locked valuation. UNA.AS was struck on basis 1
> under the earlier reading; that figure stands as struck, like any other
> superseded-definition figure.**

#### What made the question unavoidable

SYNSAM.ST's §5 run, 2026-08-25, on a VERIFIED manual file at the basis
`TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2`. The two bases are not a rounding
difference on a store-based retailer:

| | FCF₀ | fair value at g_base 2.5%, r 9.5% | implied growth at 59.50 |
|---|---|---|---|
| **basis 1** — OCF less cash capex | 1,033 | **84.14** | **−1.09%** |
| **basis 2** — basis 1 less lease capital | 569 | **36.29** | **+6.99%** |

**464 MSEK of lease capital a year against 1,033 of pre-lease free cash flow.**
Same company, same window, same pre-registered rates: on one reading the price
carries a shrinking business, on the other a business growing near seven
percent. **A framework that leaves that choice unstated does not have a
valuation; it has two.**

#### The reasoning, restated

The ruling turns on what the payment IS rather than on where the cash flow
statement puts it. IFRS 16 files the capital element under financing, which is
where basis 1's silence comes from — but the classification is an accounting
presentation and the obligation is not optional. **A retailer without its shops
is not the same business at a lower cost; it is not the business.** And the
ten-year horizon is what makes it bite: a DCF that runs to year ten while
deducting no lease payment is pricing a company whose leases all expire and are
never replaced.

**The exemption is deliberately narrow and is a JUDGEMENT, not a test.** "Where
the leased assets are incidental to the business" covers an issuer whose leases
are office space and vehicles rather than its selling estate. **The choice is
NAMED IN THE VERDICT** — which is the enforcement: a basis chosen silently is
the failure this ruling exists to end.

#### Not retroactive, and the shape of that is E32's

**UNA.AS's `fv_base` of 43.5 was struck on basis 1 and stands as struck.**
E32 established the pattern one ruling earlier: a figure struck under a reading
the framework has since superseded is **a record of what the owner decided, not
a live buy price**, and is neither recomputed nor deleted. The same applies
here. *B26 is where `fv_base`'s own basis is open, and E33 does not decide it.*

**No code changed.** `vss/valuation.py` takes `fcf0` as an argument and has never
chosen a basis; the choice was always the owner's and is now written down.

---

### B33 — how E33 applies to a US GAAP filer

**RAISED 2026-08-25 by the NKE re-read, which applied it as a judgement and
expressly does not decide it. OPEN.**

**The gap.** E33 rules that operating lease payments are an OPERATING COST and
makes FCF basis 2 — basis 1 less lease capital repayments — the default for a
store-based retailer. **It was written on SYNSAM.ST, an IFRS 16 filer**, where
the capital element of a lease sits in FINANCING and basis 1 genuinely misses
it. **E33 says nothing about a filer whose accounting already puts it in
operating.**

**Under US GAAP ASC 842, operating lease payments are an operating cash
outflow.** They are already inside the reported operating cash flow. So for such
a filer, basis 1 has ALREADY made the deduction E33 requires, and **deducting
the payments a second time double counts them**.

**NKE is the worked case.** FY2026 operating cash flow 2,868 already contains
the 668 of `OperatingLeasePayments` the filer tags; `FinanceLeasePrincipalPayments`
is absent for Nike entirely. Basis 1 gives FCF 2,184; a mechanical basis-2
deduction would give 1,516 and price the same obligation twice. **The verdict
uses basis 1 and says so** — not on E33's "leased assets are incidental" clause,
which would be the wrong reason, but because the accounting framework already
performed the deduction.

**What is open.** Whether E33's rule should be restated in terms of the
ECONOMIC deduction rather than the cash-flow line — "the FCF basis deducts lease
payments once, wherever the filer's framework classifies them" — or whether the
IFRS/GAAP distinction should be named explicitly with a test for which regime a
filer is under. **Not decided here.** *A related question E33 also leaves open,
noted where it arose: if basis 2 deducts the lease payments as an operating
cost, counting the lease LIABILITY as debt under assumption A2 deducts the same
obligation twice — E33 and A2 now interact and neither text says how.*

---

### B34 — is Method C's single twelve-month window systematically depressed?

**RAISED 2026-08-25 by measurement, which was too thin to rule on. OPEN.**

**The question.** §5's Method C takes FCF₀ from ONE twelve-month window and
compounds it for ten years. §3 Gate 1 selects names that have recently FALLEN,
so the entry window might be systematically a depressed one — which would make
every fair value the chain produces too low.

**Measured 2026-08-25, and the result runs the OTHER WAY.** Three names carry
enough FCF history in this repo to compare the newest twelve months against a
multi-year average:

| | (a) newest 12m | (b) 3-year mean | (c) 5-year median | b vs a |
|---|---|---|---|---|
| **JD.L** | 956.0 | 760.1 | 735.0 | **−20.5%** |
| **PNDORA.CO** | 6,228 | 6,128.7 | — | **−1.6%** |
| **DECK** | 1,117.9 | 999.8 | — | **−10.6%** |

**In all three, the newest twelve months reads 1.6% to 20.5% ABOVE the
multi-year mean.** On this evidence Method C's single window looks **generous,
not depressed.** The mechanism that explains the sign: **Gate 1 selects on a
fall in PRICE, not a fall in CASH FLOW**, and a name can be far off its high
while its free cash flow is at a multi-year peak — which is what JD.L and DECK
are. *On DECK the spread is worth 13.65 per share at g_base, the same magnitude
E29 records for a 100bp move in r.*

**Why it stays open: THREE CONSUMER NAMES IN ONE EIGHTEEN-MONTH WINDOW IS TOO
THIN.** Choice (c) rests on a single name — JD.L — and that name has an extreme
capital-expenditure cycle (PP&E purchases 227 → 327 → **500** → 487 → 367),
which makes it the observation most likely to be unrepresentative. Three names
cannot separate a framework effect from a sector-and-vintage effect, and a
sample drawn from another part of the cycle could show the opposite sign.

**What the measurement was limited BY, which is the thing to fix first.**
Nothing in this repo stores multi-year cash flow. The screener's fundamentals
store carries **536 tickers and no cash-flow statement at all** — only `balance`
and `income`. `vss xbrl` reads only the §4.2 quarter shape and requests no
cash-flow tag. The manual schema holds cash flow but only three files exist, and
only PNDORA.CO's is deep. Everything else on disk yields two years per issuer,
below the threshold for (b) and far below it for (c).

*SEC companyfacts does carry `NetCashProvidedByUsedInOperatingActivities` and
`PaymentsToAcquirePropertyPlantAndEquipment` with full annual history for every
CIK-bearing name — measured on NKE 2026-08-25. **Nothing here proposes building
that reader**; it is recorded because it is what the sample size depends on.*

---

### B35 — rounding must not make a figure look like it has crossed a limit it has not

**RAISED 2026-08-25 by the NKE re-read. OPEN.**

**The case, exactly as it printed.** NKE's row in the ALL TICKERS table on
2026-08-25 read **`50.0%`** in the drawdown column. The figure is
**49.9746%**. §3 Gate 1's structural-impairment line is **50%**, and the limb
had **NOT** been crossed — it was short by **0.0254pp**.

**A reader scanning that row sees a threshold met.** The number is rounded to
one decimal by `report._pct_abs`, which is the right display width for
everything else in the table; the defect is not the width but that **this
particular column has a hard limit sitting exactly on a rounding boundary**.
The same applies wherever a printed figure is compared against a stated
threshold — the dislocation band's 15% and 50% bounds, both INCLUSIVE, and
§3 Gate 3's limits.

**What is open.** Whether the fix is to widen the column, to print the raw
figure alongside, to mark a value within half a display-unit of a named
threshold, or to round AWAY from any threshold it is near — and whether the
rule should be general to every threshold-compared figure or specific to the
ones §3 names. **Not decided here, and no code is changed.**

*Note what this is NOT: the stored figure is correct, `dislocation_verdict`
compares the unrounded value, and no verdict was wrong. The defect is
entirely in what the page shows a person. That is the same class as E20's
"the refusal speaks in the terms the figure has" fix — the arithmetic was
right and the sentence was wrong — and it is worth fixing for the same
reason: this framework's purpose is to make its own reasoning legible
afterwards.*

*Note also that NKE's drawdown is converging on 50% from below while the peak
it is measured against is dated to the rolling window's first day and ages
out within days, after which the same price reads 47.70%. So the row was
about to show a figure that looked crossed, immediately before the reference
that produced it disappeared.*

---

### B36 — a weighted average is not a period-end count, and the difference is not random

**RAISED 2026-08-25 by the annual XBRL path. OPEN, and it is the one entry
on this page that MOVES A NUMBER TODAY.**

**The two figures, on DECK's FY2026.** The path writes
`diluted_weighted_average_shares` **145,805,000**, which is
`us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding` — a tagged fact. The
2026-08-25 hand run used **136,414,227**, the count stated on the Q1 FY27 10-Q
cover page. **They are 9,390,773 apart, 6.4%**, and Method C's fair value moves
**140.81 → 131.74** between them, at one growth rate and one hurdle.

**THEY ARE DIFFERENT CONCEPTS, NOT TWO READINGS OF ONE.** A weighted average
is a *flow* — the average count in issue across the twelve months. A period-end
outstanding count is a *stock*, the count on one day. Nothing reconciles them
and neither is a better reading of the other.

**THE BIAS HAS A DIRECTION AND IT IS SYSTEMATIC.** For any filer that
repurchases, the count falls through the year, so **the weighted average sits
ABOVE the period-end count** — always, by construction, not sometimes.
Dividing by the larger figure lowers value per share. So this choice
**systematically depresses Method C in exactly the names that buy back stock**,
which is a population the framework has no reason to want to under-value, and
the depression is invisible because both figures are defensible in isolation.

**E19 POINTS ONE WAY.** *Every flow is the whole window and every stock is taken
at its END.* A share count is the divisor on a per-share figure struck at the
window's end, which reads as a stock. Against that: E22 requires a count to be
**STATED**. **A19/A6 was written as the owner's assumption to throw and has
never been thrown.**

**CORRECTION OF RECORD, 2026-08-26 (REVIEW-4 report A 2.3, report C 9.2).**
This entry said the period-end count *"is stated on a cover page in prose — not
a tagged fact — so the XBRL path cannot reach it and a manual file can"*.
**BOTH HALVES ARE WRONG.**

- `us-gaap:CommonStockSharesOutstanding` is tagged at **every quarter end**:
  DECK 139,978,000 at 2026-03-31 and 136,725,000 at 2026-06-30.
- `dei:EntityCommonStockSharesOutstanding` is tagged on **every cover page**:
  seven values for DECK from 151,773,639 on 2025-01-16 to **136,414,227 on
  2026-07-09** — which is the very figure the hand run used, and it is a
  tagged fact with an accession behind it.

**The path could not reach them because it never asked.** `xbrl._entries`
opened `facts["us-gaap"]` alone and never the `dei` block, and `ANNUAL_FIELDS`
mapped the weighted average and no other count. **A reader's choice, not a
source's limit** — and the same sentence stood as a comment in `xbrl.py` beside
the field, where it has also been corrected.

**What this changes about the question.** It removes the only argument that
was doing work for the weighted average: *"the fetched path cannot supply a
period-end count"*. It is not an argument for a period-end count either — the
two are still different concepts (a flow and a stock) and A6 is still the
owner's. What is now true is that **both are reachable from the same fetch**,
so the choice can be made on its merits and recorded rather than inherited
from what a reader happened to map. **Settled by E38** (2026-08-26), which
takes the weighted-average diluted count for the same window as the flows and
keeps a tagged point-in-time count as a dated memo.

**What is open.** Nothing on reachability. E38 answers the divisor; whether a
name may be re-struck on the period-end count as a stated variant stays with
A6.

---

### B37 — `_pick` takes the newest FILING, and a proxy statement can be newer than the 10-K

**RAISED 2026-08-25 by the annual XBRL path. OPEN. NOTHING IS WRONG IN THE
FIGURES.**

**What it looks like in the file.** `config/manual/NKE.yaml` cites, for
`net_income` on FY2026:

> `us-gaap:NetIncomeLoss [2025-06-01..2026-05-31] DEF 14A 0000320187-26-000089
> filed 2026-07-15`

Every line beside it cites the 10-K, `0000320187-26-000088`. DECK is the same
shape, `0000910521-26-000018`.

**Why.** `xbrl._pick` orders candidate entries on `(filed, accn)` and takes the
last — *"the latest filing is the current official figure"*. NIKE filed its
proxy statement the same day as its 10-K with a **higher accession number**, so
the proxy wins the tie. The tie-break was never chosen; it fell out of sorting
a tuple.

**The value is right and the reference is truthful** — the fact IS in that
filing, under that tag, for that period. The defect is that a reader coming to
the file cold sees net income sourced to a proxy statement and reasonably reads
it as an error. `net_income` is read by §5.1 C.

**What is open.** Whether `_pick` should prefer a form (10-K, then 10-Q, then
the rest) on an equal filing date, or leave the ordering alone and let the
reference speak. **`_pick` was NOT changed**: it governs the quarter shape too,
and a preference introduced here would silently re-source figures on a path
this work did not verify.

---

### B38 — NKE now carries two units in two stores, and rule 3 cannot see it

**RAISED 2026-08-25. OPEN.**

`config/watchlist.yaml` holds NKE's quarters **in millions**, read from press
releases. `config/manual/NKE.yaml` holds its fiscal years **in whole units**,
from tagged facts. Both are correct in their own file and **neither is
rescaled**.

**Rule 3 is not violated.** The two are different stores with different readers:
§4.2's hard kills read the watchlist quarters, §5's basis reads the manual file,
and no arithmetic in this project puts a figure from one beside a figure from
the other.

**But this is the condition rule 3 exists to prevent, arrived at from a
direction the refusal does not look in.** `xbrl.write_manual_file` refuses to
write beside a file of another origin — SAME-FILE mixing, which it sees. It has
nothing to say about the same ticker held in two files at two scales, because
nothing looks across the two.

**What is open.** Whether a name may be carried in both stores at once; whether
a check should compare the scale of a ticker's watchlist quarters against its
manual file; or whether the separation is sound and only wants writing down.
**Nothing is changed and both files stand.**

---

### B39 — `newest_period_end` scans `periods:` only, so an annual-only file reads fresh

**RAISED 2026-08-25. OPEN. NARROW, AND NEW WITH THE XBRL PATH.**

`manual.ManualFile.newest_period_end` returns `self.periods[-1].period_end` and
**never looks at `annual:`**. `manual.staleness` measures on it, and
`as_record` hands the result to the store as the record's `newest_period`. So a
file with **no `periods:` block at all** — which is exactly what
`vss xbrl --annual` writes — has `newest_period_end` of `None`, and
`staleness` returns `STATUS_OK` **whatever the fiscal years in it say**. A file
of years ending 2019 would read as fresh.

**Section 5 IS NOT AFFECTED and that is why this is narrow.**
`section5_gate` measures age on `basis.end`, which for an annual basis is the
fiscal year end, and it refuses correctly — NKE's FY2026 is 86 days old and
inside the limit, measured properly. The gap is in the STORE record and in
`staleness`, which the ranking key reads.

**It could not fire before today.** Every manual file in the project has had a
`periods:` block; an annual-only file did not exist until this path wrote one.

**What is open.** Whether `newest_period_end` should take the max across both
blocks, or whether the ranking key should decline an annual-only file outright
(it already emits no series point from `annual:`, so such a file reaches the key
with nothing in it). **Not changed here** — it touches every consumer of
`newest_period`, and the path that exposed it does not need it fixed to be
correct.

---

### B40 — CORRECTION OF RECORD: the ticker→CIK map is NOT closed to us

**RAISED 2026-08-25 by the owner, correcting his own earlier note. THE
CORRECTION IS SETTLED; the question behind it is open.**

**Three places in this project stated that the SEC's ticker→CIK mapping refuses
automated callers.** `vss/config.py`'s `cik` field comment, and the same
sentence in both `run_xbrl` and `run_xbrl_annual`. **The claim was false.**

`https://www.sec.gov/files/company_tickers.json` **answers HTTP 200 to a caller
that declares a real contact.** It was fetched successfully during the FGR.PA
source work on the evening of 2026-08-25 — **794,966 bytes** — and re-measured
independently the same night: **HTTP 200, 794,966 bytes, 10,388 rows**, the
first keyed `NVDA → 1045810`. The access policy is the same one `data.sec.gov`
is held to and `vss` already satisfies it through `VSS_SEC_CONTACT`.

**All three sentences are corrected** in the same commit as the annual path.
The gap is now recorded as what it is: **NO CIK RESOLUTION STEP IS BUILT.**
That is a thing this project has not written, not a door somebody closed.

**Why it matters more than a wording fix.** It was the stated reason the
XBRL path reaches so few names, and the count it produced is the finding of
2026-08-25: **zero of the screener universe's 1,370 rows carry a CIK** — the
`universe` table has no such column — and of the watchlist's 13 entries
**two** do, MSFT and NKE, both typed by hand. **503 universe rows are
US-listed.** A foreign suffix was never the barrier either: `manual.py`'s own
docstring records SAP.DE and UNA.AS reaching SEC XBRL through 20-F CIKs.

**What is open.** Whether to build the resolution step — fetch the map, cache
it, and resolve a ticker to a CIK at run time — and if so **what it must do
about ambiguity**: the file is keyed on ticker, a ticker is not unique across
time or across share classes, and a wrong CIK is a whole different company's
accounts arriving with perfect provenance. **That is the reason to build it
carefully rather than the reason not to build it.**

---

### E34 — where a filer books its interest is a FACT ABOUT THE FILER, and FCF0 depends on it

**RULED 2026-08-26 by the owner after REVIEW-4. This closes the largest ERROR
the review found — the only entry on its list where the same quantity is
charged twice.**

**THE RULE.**

1. **Every filer carries `interest_in_ocf: yes | no`**, read from its CASH
   FLOW STATEMENT and recorded on the file with the page it was read from. It
   is not inferred from the accounting regime, not guessed from the ticker
   suffix, and never defaulted.
2. **Where it is `yes`** — the filer's operating cash flow already bears its
   interest — **FCF0 = operating cash flow − capex + NET INTEREST PAID**. The
   add-back is the figure **AS PRINTED, PRE-TAX**.
3. **Where it is `no`**, FCF0 = operating cash flow − capex, unchanged.
4. **Net debt is subtracted ONCE, after discounting, in BOTH cases.** There is
   no second bridge and no FCFE path. The engine's `(enterprise + net_cash) /
   shares` is right; what was wrong was the flow handed to it.
5. **Absent → DATA MISSING for FCF0, and section 5 does not run.** A file that
   does not say where its filer books interest cannot produce a fair value.
   This is the same shape as E26 and E22: a fact the accounts state, or
   nothing.

**THE DIRECTION OF THE ERROR IT REMOVES.** IAS 7.31–34 lets a filer put
interest paid in operating **or** in financing; ASC 230 puts it in operating
**always**. The code had one field, `operating_cash_flow`, with one note about
tax and nothing about interest, so it discounted a flow to the FIRM for one
filer and a flow to EQUITY for the next, and subtracted net debt from both.
**For a net-debt name whose operating cash flow carries its interest, that
charges the same interest twice and UNDERSTATES the company. For a net-cash
name it overstates, slightly.** Measured on the held name: LIAB.ST's operating
cash flow bears net interest paid of 201 MSEK over the R12M to 2026-06-30
(interim p.17), and 4,497 MSEK of lease-inclusive net debt is then subtracted
from a flow that has already paid the interest on it. **102.66 → 139.48**, on
the same growth rate, the same hurdle and the same share count.

**THE BIAS THIS RULING KNOWINGLY ACCEPTS, STATED.** The add-back is pre-tax.
Interest is deductible, so the after-tax cost to equity is lower than the
printed figure and a pre-tax add-back is **GENEROUS**. At Sweden's 20.6% the
after-tax add-back gives **131.89** where the pre-tax one gives **139.48** —
**the ruling is +7.59 SEK a share more generous on LIAB.ST than the arithmetic
report A ran.** It is chosen anyway, for the reason E29 chose a flat rate: an
effective tax rate is a second estimated lever per name, it is not printed on
the cash flow statement, and a figure the accounts state beats a figure the
reader computes. **The number to remember is that this ruling's own answer is
the generous end of its band.**

**ONE FILER CAN BE ON BOTH SIDES, AND ONE ALREADY IS.** SAP tags
`InterestPaidClassifiedAsFinancingActivities` 574 for FY2025 and the FY2024
20-F tagged the identical amounts as `…ClassifiedAsOperatingActivities`: it
reclassified in January 2025 and re-tagged the comparatives. **`interest_in_ocf`
describes the BASIS YEAR and says so on the field.** Section 5 reads the basis
year and nothing else, so a file-level attribute is enough for it — but B5's
five-year trailing-P/E proxy reads five years, and for a filer that
reclassified mid-history the attribute is not true of all of them. **That is a
limit of the attribute, not of the ruling**, and it is recorded here rather
than solved: a per-period attribute is the fix if a per-period consumer ever
needs one.

**IFRS 18 MOVES EVERY IFRS FILER IN 2027.** Interest paid goes to the
financing category, so `interest_in_ocf` flips from `yes` to `no` across one
year boundary inside one file for Pandora, Betsson, Lindab and every other
IFRS name. The attribute is what makes that visible instead of silent.

**WHICH EARLIER RULING THIS AMENDS.** None directly, and that is worth saying.
It **SUPERSEDES the schema note at `manual.py`'s `net_interest_paid`**, which
said "FCF basis 3 deducts it" with no precondition and was corrected on
2026-08-26 to state one; E34 makes the precondition structural rather than
textual. It **answers the interest half of B33**, which named the interaction
between what operating cash flow already contains and what the bridge then
subtracts, and settled neither half. E33 is untouched: lease payments are
still an operating cost and basis 2 is still the retailer's default.

---

### E35 — leases are in net debt, always

**RULED 2026-08-26 by the owner after REVIEW-4.**

**THE RULE.** Net debt, wherever section 5's gate or its valuation READS one,
is

    financial liabilities (current + non-current)
      + lease liabilities
      − cash and equivalents
      − other current financial assets

Assumption A2 is no longer thrown per name for the purpose of this
calculation: leases are debt.

**WHICH EARLIER RULING THIS AMENDS.** **E14, and only in what the gate and the
valuation READ.** E14's storage rule is untouched and remains the reason this
is possible at all: the three fields stay separate and additive, a
consolidated `Loans and borrowings` line is still never entered in a borrowing
field, and where an issuer splits it nowhere all three fields are still DATA
MISSING. What changes is that the code no longer forms a net debt WITHOUT the
lease leg while claiming to have read E14's fields.

**THE DIRECTION OF THE ERROR IT REMOVES.** `manual.RATIOS` defined net debt as
`financial_liabilities_current + financial_liabilities_noncurrent +
cash_and_equivalents` — **`lease_liabilities` was not a leg, and neither was
`other_current_financial_assets`**. So the gate declared net debt *computable*
for a file whose lease liability is DATA MISSING, and it threw A2 to N
silently, every time it printed the ratio table. **Under IFRS 16 the operating
cash flow of every filer EXCLUDES lease principal** — it sits in financing —
so leaving the liability out of the bridge prices the premises as free after
the contracted term ends. **It OVERSTATES every IFRS filer, by the lease
liability over the share count.** Pandora: 6,291m over 74.6m shares ≈ 84 DKK a
share. SAP: +1.45 on its Method C. And it contradicted every valuation the
owner has actually struck — SAP, Unilever, Lindab and Pandora were all struck
with leases IN.

**WHAT THE FORMULA DOES NOT REACH, MEASURED AND NAMED.** On Lindab's own
components at 2026-06-30 the four legs give **4,217 MSEK**, and Lindab's stated
net debt is **4,497**. The 280 is its **pension provisions**, and the manual
schema has no field for them — nor for non-controlling interests, associates,
preferred stock or convertibles (REVIEW-4 report A 4.1, "Structural finding").
**The formula is not back-fitted to 4,497 and the gap is not closed by a
plug.** What E35 fixes is the 1,410 of leases: without them the same legs give
**2,807**, and on LIAB.ST that is **106.29 against 120.96** — a 14.67 SEK
difference on one held name, in the direction that flatters it. A schema field
for pensions is open and is not opened here.

---

### E36 — share-based compensation is a COST

**RULED 2026-08-26 by the owner after REVIEW-4.**

**THE RULE.** FCF0 is reduced by share-based compensation for the same twelve
-month window as the flows. The share count is the weighted-average diluted
count for that window (E38). The manual schema carries `sbc`; the SEC path
reads `us-gaap:ShareBasedCompensation`, and for an IFRS filer the
**equity-settled** element. **Absent → DATA MISSING for FCF0**, on the same
terms as E34.

**THE DIRECTION OF THE ERROR IT REMOVES.** Under both ASC 230 and IAS 7 an
equity-settled award is a NON-CASH charge added back inside operating cash
flow, so `OCF − capex` contains it and **every stored fair value has treated
share-based compensation as free**. It is not free: it is a transfer of
ownership from the holder to the employee, paid in the same currency as the
thing being valued. **It OVERSTATES every filer that pays in stock, in
proportion to how much of the pay is stock.** Measured (REVIEW-4 report A 3.1,
from the filings' own tags): **NKE 715m = 32.7% of FCF0** — the fair value
falls 22.15 → 14.81; **SAP equity-settled 1,331m = 15.2%** — Method C falls
167.07 → 141.74 and `fv_base` 185 → 163.4; **DECK 44.8m = 4.1%**; Unilever
284m = 4.1%.

**THE CASH-SETTLED HALF IS ALREADY BORNE, AND MUST NOT BE DEDUCTED TWICE.** A
cash-settled award flows through operating cash flow as CASH when it is paid,
so FCF0 already carries it. SAP's FY2025 charge is 1,695m of which **364m is
cash-settled**; the figure E36 deducts for SAP is the **equity-settled 1,331m**,
not the headline. Deducting the total gives 134.82 against 141.74 — the
difference is the double count. For the same reason the IFRS map reads
`ExpenseFromEquitysettledSharebasedPaymentTransactions…` and NOT
`AdjustmentsForSharebasedPayments`, which is the operating-cash-flow add-back
line and contains both.

**NO OFFSET AGAINST THE DILUTED COUNT.** The two are not each other's mirror:
a diluted count captures EXISTING grants, and the gap between basic and
diluted is 0.2–0.4% for the names here against a charge worth 4–33% of FCF0.
The deduction and the count are decided separately and both are declared.

**WHICH EARLIER RULING THIS AMENDS.** **FRAMEWORK §4.3's soft flag**, which
read share-based compensation as a FLAG when it exceeds 30% of free cash flow
and never as a deduction. The flag stays; what changes is that the charge now
reaches the arithmetic instead of only the commentary.

---

### E37 — the discount rate stays flat at 9.5% in every currency, and the bias is PRINTED

**RULED 2026-08-26 by the owner after REVIEW-4. NO CODE CHANGE BEYOND A
PRINTED LINE.**

**THE RULE.** `r` remains one flat nominal 9.5% for every name in every
currency. **Every non-USD fair value is printed with the sentence
`r 9.5% flat; non-USD bias: conservative` beside it** — in the section 5 run
record, and on the report row of a `vss run` for an entry whose currency is
not USD.

**THE DIRECTION OF THE ERROR IT DOES NOT REMOVE, WHICH IS THE POINT.** A
single nominal rate applied to USD, EUR, SEK and DKK cash flows is a HIGHER
REAL hurdle for a low-inflation, low-risk-free currency. It therefore
**UNDERSTATES every non-USD name relative to a currency-matched rate**, by a
known and one-directional amount. Measured against the sovereign gap on
2026-08-25 (US 10-year 4.66%, Bund ~3.2%, Sweden ~2.90%): **SAP.DE's Method C
167.07 → 215.17 at 8.04%, worth +40.9 on `fv_base` 185; LIAB.ST 102.66 →
156.21 at 7.74%, +53.5.** These are the two largest per-share effects REVIEW-4
found on either held name, and they are the effect of a ruling rather than of
a defect.

**WHY IT IS NOT CHANGED.** E29's own reasoning stands: `r` is a statement
about the OWNER — what he requires to move capital out of the index core — and
not an estimate of what a market demands. A per-currency rate is a second
owner-set lever per name at the moment E28 made `g` the single one, and `g` is
pre-registered and auditable where `r` would not be. **What E29 did not record
was the SIZE, and a bias nobody has measured is indistinguishable from a bias
nobody has.** E37 changes that and nothing else.

**WHICH EARLIER RULING THIS AMENDS.** **E29**, by adding the printed
declaration. The rate, the band, the anchor and the asymmetric-in-time rule
are untouched.

---

### E38 — the divisor is the weighted-average DILUTED count for the window

**RULED 2026-08-26 by the owner after REVIEW-4.**

**THE RULE.** The share count section 5 divides by is the **weighted-average
diluted count for the SAME twelve-month window as the flows**, from the
filing. A tagged point-in-time count — `dei:EntityCommonStockSharesOutstanding`
on a cover page, `us-gaap:CommonStockSharesOutstanding` at a quarter end — **IS
"the count itself" under E22** and may be stored and printed as a dated MEMO,
in `shares_point_in_time` with its own date. **It is never the divisor.**

**THE DIRECTION OF THE ERROR IT REMOVES.** Not a bias in one direction — a
MISMATCH. DECK's 140.95 divided a flow window ending 2026-06-30 and a balance
sheet at 2026-06-30 by a count stated as of **2026-07-09**: nine days of
buybacks counted in the divisor and not in the cash. The consistent pair gives
140.63; B36's pairing of a JULY divisor with MARCH cash gives 140.81 against
the consistent March pair's 137.22, **a 3.59 overstatement out of a date
mismatch alone**. And the reverse error is systematic in the other direction:
for any filer that repurchases, the weighted average sits ABOVE the period-end
count by construction, so **taking the period-end count would systematically
FLATTER every name that buys back stock** — a population the framework has no
reason to want to over-value.

E38 takes the mismatch out by making the count the same KIND of quantity as
the flow it divides: a window figure for a window figure. It accepts, and
states, that the divisor is then above the count outstanding on the last day
for a repurchaser — which is conservative, in the direction this framework
prefers to be wrong.

**THE MEMO IS KEPT BECAUSE IT IS EVIDENCE.** The point-in-time count is what
tells a reader that the company bought back 3,253k shares in the quarter, and
it is a tagged fact with an accession. Storing it and refusing to divide by it
is not a contradiction: E22 asks that a count be STATED, and this one is.

**WHICH EARLIER RULING THIS AMENDS.** **B36 is SETTLED by it** — the entry is
also corrected, because its stated reason for preferring the weighted average
("the period-end count is not a tagged fact, so the XBRL path cannot reach
it") was false; both counts are tagged and the path simply never asked. **E22
is narrowed**: "the count itself, as stated" still governs what may be
entered, and E38 governs which of two stated counts is the divisor. **A6 is
answered for the divisor** and stays open for whether a name may be re-struck
on a period-end count as a declared variant.

---

### E39 — a fair value struck on a superseded method is NULLED, not left standing

**RULED 2026-08-26 by the owner after REVIEW-4.**

**THE RULE.** Where the method behind a stored fair value has been superseded
or the figure has been shown to rest on an arithmetic that a later ruling
removes, **`fv_base`, `tier` and `mbp` are set to `null`** with the note
*"superseded by \<review\>; re-strike after \<ruling\>"*. **`stop_price` is
untouched.**

**THE DIRECTION OF THE ERROR IT REMOVES.** A stored number that no longer has
a method behind it is not a stale number — it is a number that reads as
current. Section 6.4 compares a price with `fv_base` and says *trim* or *hold*
on the strength of it, and the E32 marker on the MBP does not reach the
`fv_base` beneath it. **Leaving it standing therefore produces a live
instruction from a dead calculation, and the failure is silent in both
directions:** LIAB.ST's 102.66 sits 19% BELOW the price and reads as a name to
trim, while every consistent treatment of its interest puts the price at or
below fair value.

**WHY `stop_price` SURVIVES.** A stop is a statement about how much the owner
will lose on a position, not about what the company is worth. It was struck
against a price and it still is; nulling it would remove the only protection
on a held name at the moment the analysis behind it is being rebuilt. **The
one thing that must not happen while a fair value is being re-struck is that
the position goes unwatched.**

**APPLIED IMMEDIATELY TO TWO NAMES.**

- **SAP.DE.** `fv_base` 185 is **not a Method C number**: it is 0.85 × Method C
  167.07 + 0.15 × Method A 285.92, under the §5.2 weighting **E28 DELETED**.
  Fifteen per cent of it rests on an undated vendor `forwardEps` of 8.37 that
  yfinance will not serve again. Superseded by E28; re-strike after E34–E38.
- **LIAB.ST.** `fv_base` 102.66 charges Lindab's interest twice (E34) and rests
  on the issuer's own "adjusted free cash flow" KPI rather than the schema's
  basis 1. Superseded by REVIEW-4; re-strike after E34.

**WHICH EARLIER RULING THIS AMENDS.** **E32**, which superseded the
`fv_base × tier` MBP definition AS A DEFINITION and KEPT the three stored
figures as VALUES, marking them wherever they print. E32 was right about an
MBP, whose provenance is a decision the owner made on a date. E39 says the
same treatment does not extend to a `fv_base` whose METHOD has gone: an MBP
marked superseded is a record of a decision, and a `fv_base` left standing is
an input to the next one.

**WHAT E39 DOES NOT DO.** It does not delete history — the prose block on each
entry, with every input of the superseded calculation, stays exactly where it
is. It does not touch `catalyst_date`, `status` or the position. And it never
writes a replacement: a re-struck fair value is a new §5 run with its own run
record, and this ruling only clears the ground.

---

### E34.1 — the US sub-case: where interest paid is stated and interest received is not, the add-back is the INCOME STATEMENT'S NET, printed as an accrual proxy

**RULED A 2026-08-26 by the owner, on the sub-case E34's commit left open.**

**THE RULE.** Where a US-GAAP filer states interest PAID as a cash figure
(`us-gaap:InterestPaidNet`) but no interest RECEIVED as a cash figure —
which is every US filer, because ASC 230 requires the paid disclosure and
nothing requires the received one — **the add-back E34 makes for a
`interest_in_ocf: yes` filer is the NET interest from the INCOME STATEMENT**:
the line a filer prints as *"Interest expense (income), net"* (Nike), or the
net of a stated interest expense and a stated interest income (Deckers), both
formed by E18's subtraction where the net itself is not printed. It is stored
on the file as **`interest_source: income_statement_net`** beside
`interest_in_ocf`, the leg it expands to is `net_finance_costs` rather than
`net_interest_paid`, and **it is printed as "accrual proxy" beside FCF0**
wherever FCF0 is printed. **Interest paid alone is NEVER used as the net.**

**THE DIRECTION, AND WHY IT IS NOT ALWAYS AN ADD-BACK.** The income statement's
net is signed. For a filer whose interest income exceeds its interest expense
the net is an INCOME, and E34's "add back the interest the operating cash flow
already bore" then REMOVES it — FCF0 falls, because a cash flow that contains
interest earned on a cash pile is not the firm's operating flow either. The
sign is taken from the element as the standard defines it, not from the
caption: `InterestIncomeExpenseNonoperatingNet` is POSITIVE for a net income,
and Nike's own history proves the reading — FY2022 −205m in the year its
statement printed a net expense of 205, FY2024 +161m in the year it printed
*(161)*.

**MEASURED ON THE TWO US FILES.**

- **NKE FY2026.** `InterestPaidNet` 323m; `InvestmentIncomeInterest` 278m;
  `InterestIncomeExpenseNonoperatingNet` **+50m — a net interest INCOME.**
  FCF0 moves by **50m, downward**, not by 323m: 2,868 − 684 − 715 − 50 =
  **1,419m** against the 1,469m of E36 alone. (The 45m the ruling was written
  with is the cash pair, 323 − 278; the income statement's net is 50 and it is
  income, so the direction is the opposite of an add-back.)
- **DECK FY2026.** No net is tagged; `InterestExpenseNonoperating` 2.53m and
  `InvestmentIncomeInterest` 63.6m are, so E18 forms **−61.1m** — a net
  income, removed. The first build's record carried the 2.49m of interest
  PAID as the net by hand, declared as generous; **E34.1 retires that input**,
  and the DECK golden case moves from 124.58 to the figure the store now
  gives.

**WHY THE INCOME STATEMENT AND NOT THE CASH PAIR.** E18's cash pair cannot
form: a US filer states no interest received as a cash figure, and
`InvestmentIncomeInterest` is what was EARNED, not what arrived. Using
interest PAID alone would add back the gross expense and leave the interest
INCOME inside the flow — the largest and most one-sided misstatement
available, and on Nike it is 323m against a true net of −50m. The accrual net
is the wrong KIND of figure (charged, not paid) but the right SIZE and SIGN,
and the record says which kind it is. **That is the trade E34.1 makes, and
"accrual proxy" is printed so nobody mistakes it for cash.**

**WHAT IT DOES NOT TOUCH.** IFRS filers keep E34 as written: their cash flow
statements state both halves, or classify interest outside operating cash
flow altogether. A file that says `interest_source: income_statement_net`
with `interest_in_ocf: no` is refused at the load — an accrual proxy is an
add-back, and a filer whose operating cash flow bears no interest has nothing
to add back.

**WHICH EARLIER RULING THIS AMENDS.** **E34**, by settling the sub-case its
commit named ("the fetched path produces no FCF0 for ANY us-gaap filer").
**E18 is applied, not changed**: the net is still formed from two stated
operands where the net is not itself stated.

---

### E40 — a tagged fact is VERIFIED by provenance, and the VERIFIED flag says WHICH KIND of verification it carries

**RULED A 2026-08-26 by the owner, closing report C's G13.**

**THE RULE.**

1. **A tagged SEC fact is VERIFIED by its provenance** — tag + accession +
   filing date, which every figure the annual XBRL path writes already
   carries on its `page:` line. No second read is required: there is no
   transcription to have got wrong, and the tag map (`xbrl.ANNUAL_FIELDS`,
   `IFRS_ANNUAL_FIELDS`) is itself the committed, diffable record of WHICH
   TAG answers which field.
2. **The VERIFIED flag gains a `verified_kind` with three values**, so that
   report B §7's distinction — *"three kinds exist on disk, distinguishable
   only in comments"* — is recorded in the schema rather than in prose:
   - **`tagged`** — verified by provenance, as in (1). Written by the XBRL
     path; regenerable by the same path.
   - **`cross_document`** — read back against a SECOND document (SYNSAM's
     twenty figures against the Q2 2026 report's p.29 quarterly table;
     Pandora's quarterly finance and share-based-payment lines against the
     interim PDFs beside the appendix workbook).
   - **`same_page`** — read back against the page it was entered from: the
     owner's rendered-page read-backs (BETS-B.ST), a second extraction of
     the same page (SYNSAM's other fifty-two), the appendix cell against
     the appendix (PNDORA.CO's forty-nine). **The weakest of the three, and
     the one every flag set before E40 was.**
3. **Migration.** Every VERIFIED flag on disk that names no kind is read as
   `same_page` — the parser states the default and the report prints it —
   **unless the file's own notes state a second document, in which case
   the file is edited to say `cross_document`.** Done for SYNSAM.ST's
   twenty (revenue, operating income, net income, `op_margin`, diluted EPS
   × four quarters; HANDOFF-2026-08-25 lines 399–406); nothing else on disk
   claims a second document.
4. **§5's gate accepts all three.** E21 asks that a figure the basis reads
   be VERIFIED; it does not rank the kinds. **The report prints the kind
   beside every figure** — the manual report's input block, the UNVERIFIED
   lists, and the run record's inputs table — so a reader can see whether
   a number stands on a tag, a second document, or a re-read of one page.
5. A `verified_kind` on an UNVERIFIED figure is refused at the load: a kind
   is a property of a verification that happened.

**WHAT IT CHANGES ON DISK.** `config/manual/SAP.DE.yaml`, `NKE.yaml` and
`DECK.yaml` are regenerated by `vss xbrl --annual --write` and every figure
now lands `VERIFIED` / `tagged`. **SAP.DE becomes runnable**: on its FY2025
basis every Method C leg resolves and the gate refuses nothing (E41 then
moves the basis). The writer's refusal to overwrite a file holding VERIFIED
readings counts only `cross_document` and `same_page` flags — a tagged flag
is provenance the same path will write again, not work a person did.

**WHICH EARLIER RULING THIS AMENDS.** **E21** — narrowed on what VERIFIED
means, not on what it gates. E21's rule that a figure read by the basis
must be VERIFIED is unchanged; E40 says a tagged fact IS, and says which
kind everything else is.

---

### E41 — a 20-F filer's flows come from its quarterly periods at the TTM basis, and the 20-F fills only the ANNUAL-ONLY fields

**RULED B 2026-08-26 by the owner, settling R1 / B12 for the four-quarter
case.**

**THE RULE.** For a filer whose SEC path is annual-only — a 20-F filer, whose
companyfacts carry fiscal years and no quarters — **section 5's FLOWS come
from the quarterly `periods:` the issuer's own releases state, at E19's TTM
basis: four consecutive quarters summed, stocks at the newest quarter end.**
The 20-F fills **only the ANNUAL-ONLY fields** — the ones a filer states once
a year and the interims do not: the weighted-average diluted share count
(E38), share-based compensation (E36), the interest classification (E34,
already file-level), and the pension deficit (E35.1). **E17's periods-first
rule applies unchanged**: where the quarters carry a field, the quarters
answer it; the annual entry answers only what they cannot.

**THE MECHANISM, and where it departs from E20.** An annual-only field
resolves from the newest `annual:` entry **whose fiscal year-end falls INSIDE
the twelve-month window** — FY2025, ending 2025-12-31, inside the R12M to
2026-06-30. E20 refused an annual figure from a year that does not close on
the basis end, and for a FLOW that is still right: twelve months of another
twelve months is a different figure. E41 carves the exception for the four
fields above because the alternative is not a better figure but NO figure:
no interim states SAP's equity-settled share-based payment or its pension
liability, and E38's own count is stated on the 20-F. **The record declares
the departure**: the share count's as-of date is the annual entry's, the
as-of line prints THEY DO NOT AGREE and names which date differs, and the
share-based compensation's window is printed beside its amount.

**A WEIGHTED AVERAGE IS NEVER SUMMED (B27, settled).** A quarterly average
count is a quarter's, not the window's; four of them added together are
SYNSAM's 572,025,536, which is not a count of anything. On a TTM basis
`diluted_weighted_average_shares` resolves from an annual entry under this
ruling or is DATA MISSING with the reason — never from the quarters' sum.
Share-based compensation IS a flow and IS summed where all four quarters
state it (Pandora's appendix does); the annual fill is for the filer whose
interims do not.

**SAP.DE, APPLIED.** `config/manual/SAP.DE.yaml` gains four `periods:` from
the Quarterly Statements Q3 2025, Q4 2025, Q1 2026 and Q2 2026, in the file's
one unit (whole EUR, from the statements' "€ millions"): operating cash flow
1,502 + 1,297 + 3,513 + 3,153 = **9,465 — the workbook's own R12M**; cash
10,511 and other current financial assets 1,114 at 2026-06-30. The basis
becomes **R12M to 2026-06-30**, named quarter by quarter on the basis line,
and FY2025's 1,175m diluted count, 1,331m equity-settled SBC and interest
classification fill from the 20-F.

**WHAT THE STATEMENTS DO NOT STATE, AND THIS RULING DOES NOT INVENT.** Two
legs are DATA MISSING on the R12M basis and stay so in the store:

- **Capex.** SAP prints capital expenditure CUMULATIVELY (Q1, Q1–Q2, Q1–Q3,
  Q1–Q4) and never as a standalone quarter, so no `periods:` entry can carry
  a stated quarterly capex, and E19's sum cannot form. The R12M figure —
  FY2025 739 − H1 2025 358 + H1 2026 354 = **735** — is arithmetic over four
  stated cumulative columns, which is E19's own summation read backwards; it
  enters the RE-STRIKE as a HAND input with all four columns named, and the
  record says so. Whether a cumulative-minus-cumulative quarter may live in
  the store is **open**, and is not decided here.
- **Borrowings and leases.** The interim balance sheet presents ONE
  `Financial liabilities` line per side (1,966 current, 8,541 non-current at
  2026-06-30), leases and derivatives inside, and no note splits it. Under
  E14 the three fields stay DATA MISSING. E35 needs only their SUM, which the
  consolidated line IS (plus derivatives), so the re-strike takes the
  consolidated line as a HAND input with its page, and the bridge note says
  "consolidated line, split not stated, derivatives inside".

**WHAT STAYS OPEN.** The HALF-YEAR shape — Unilever's FY − H1 + H1 — is a
subtraction E41 does not license; G12 stays skipped on it. Betsson's interest
paid, disclosed once a year beneath the cash flow statement, is a FLOW and is
not on E41's annual-only list; its FCF0 on a quarterly basis is DATA MISSING
until the owner extends the list or the issuer discloses it quarterly.

**WHICH EARLIER RULING THIS AMENDS.** **E20**, narrowed for four named
annual-only fields on a TTM basis. **E17 unchanged. E19 unchanged. B27
settled. R1 / B12 settled for the four-quarter case and left open for the
half-year one.**

---

### E35.1 — the pension deficit is a leg of net debt, and an absent one is DATA MISSING

**RULED A 2026-08-26 by the owner, on the gap E35 named and did not close.**

**THE RULE.** Net debt, wherever section 5's gate or its valuation READS one,
is

    financial liabilities (current + non-current)
      + lease liabilities
      + pension deficit
      − cash and equivalents
      − other current financial assets

The manual schema gains **`pension_deficit`**: the PROVISION FOR PENSIONS
AND SIMILAR OBLIGATIONS as the balance sheet presents it — the recognised
net defined-benefit LIABILITY. A separately presented pension ASSET (a plan
in surplus) is NOT netted here: the schema holds no field for it, omitting
an asset raises net debt and lowers the value, and that is E35's safe
direction. **Absent → DATA MISSING for net debt**, on the same terms as the
lease leg: a file that does not say what the filer owes its pensioners
cannot produce a bridge.

**MEASURED.** On Lindab's own components at 2026-06-30 the four legs of E35
gave 4,217 and Lindab's stated net debt is 4,497; **the 280 is the pension
provision (interim p.15 and p.25), and with it the formula reaches 4,497 —
on the components the first re-strike used.** On the store file written in
Build 2 the same page gives 5 + 3,378 + 1,410 + 280 − 527 − 10 = **4,536**,
39 above Lindab's own, because the 39 of NON-current interest-bearing
assets Lindab nets (including its 21 of pension-related assets) has no field
and is omitted in the conservative direction. SAP tags
`RecognisedLiabilitiesDefinedBenefitPlan` 249m at 2025-12-31 beside
`RecognisedAssetsDefinedBenefitPlan` 19m; the 249 is the leg, the 19 is the
omitted asset, and E41 carries the 249 onto the R12M basis as an annual-only
field (no interim states it).

**THE DIRECTION OF THE ERROR IT REMOVES.** A defined-benefit deficit is a
debt to employees that the operating cash flow does not service in full —
the service cost runs through operating cash flow, the deficit does not — so
leaving it out of the bridge OVERSTATES every filer that carries one, by the
deficit over the share count: Lindab 280 / 77.036m = 3.6 SEK a share; SAP
249m / 1,175m = 0.21 EUR. Small on these two, and named rather than plugged.

**WHAT E35.1 DOES TO THE US FILES.** Neither Nike nor Deckers tags a
defined-benefit liability, and absence of a tag is DATA MISSING, not zero.
The DECK golden record carries a HAND zero on E25's `note` form, cited to
the 10-K's employee-benefit note ("The Company has various defined
contribution plans"; a 401(k)), which is the weakest form of the evidence
and is labelled so; NKE's gate reads net debt as input missing until the
owner enters the same kind of sentence. The us-gaap map reads
`PensionAndOtherPostretirementDefinedBenefitPlansLiabilitiesNoncurrent`
where a filer tags it.

**WHICH EARLIER RULING THIS AMENDS.** **E35**, by the fifth leg it said was
open. The run record's bridge item `pensions` is a VALUE now, not "no field
in this schema"; non-controlling interests, associates, preferred and
convertibles remain fields the schema does not have, and the record still
says so.

---

### E42 — C4 has no horizon: above FV_bull, the full position is sold at the next session

**RULED 2026-08-26 by the owner, settling the question
`reference/RESTRIKE-2026-08-26-b.md` left open on SAP.DE ("C4 states no
horizon ... Which horizon C4 means is the owner's to say").**

> **C4 has no horizon: when price exceeds FV_bull the full position is sold
> at the next session; no trim, no wait for the next report. Ruled by owner
> 2026-08-26; fourth application (MSFT, UNA.AS, SAP.DE).**

**APPLIED: SAP.DE, 2026-08-26.** Price 187.20 EUR (last settled close,
2026-08-24) against FV_bull 174.30 — RESTRIKE-2026-08-26-b, Method C on the
R12M to 2026-06-30 basis, bull g 11.0% pre-registered 2026-08-26 under item 6,
r 9.5% — is +7.4% above the bull case; expected return to FV_bull −6.9%. The
whole position, 6 shares at entry 154.06, sold 2026-08-26; the sell price is
to be entered on the watchlist entry. §6.4's "at FV_base, trim 25–50%" fired
on the same printout and is NOT applied: once C4 fires there is nothing left
to trim. The 2026-08-22 §6.4 decision — "reassessment points: the Q3 2026
report on 2026-10-21, or price reaching FV_bull 220, whichever comes first" —
is retired; the next report is not waited for.

**THE TALLY.** First: MSFT, 2026-08-21 (fired; sold). Second: UNA.AS,
2026-08-22 (condition met at r 9.5%; the owner decided the exit). Third:
SAP.DE, 2026-08-22 (tested in the §6.4 reassessment; did NOT fire). Fourth:
SAP.DE, 2026-08-26 (fired; sold). Three names, four applications.

**AFTER THE SALE.** SAP.DE is WATCH-PRICED (E27): it has been through
section 5 and is merely too expensive. Re-entry line **96.21 EUR** — E28's
MBP, the bear-case value 120.27 (g 6.0%) × the tier-1 cushion 0.80, struck
2026-08-26 with the bear case pre-registered before implied growth was solved
(item 6), from `reference/run-records/SAP.DE-2026-08-26.json`. `stop_price`
null. The figure is recorded on the entry as the owner's decision, with
`mbp_basis: e28_bear_case / 2026-08-26`: `rules.compute_mbp` still computes
only `fv_base × tier` (E32's finding — E28's engine is wired to nothing), so
the tool cannot derive 96.21, and `fv_base` is left blank because 139.48
beside tier 1 would print 111.58, which is not the line. Wiring E28's MBP
into `vss run` stays on the backlog.

*Wired the same day, in the commit after this ruling: `rules.compute_mbp_e28`
strikes the linked run record at its pre-registered bear case and applies the
tier cushion; SAP.DE's entry links `reference/run-records/SAP.DE-2026-08-26.json`
with `fv_base` 139.48, and the 96.21 is COMPUTED by `vss run`, unmarked. The
`fv_base × tier` path remains only for names whose record carries no bear case,
and prints E32's mark — a row's `mbp_basis` claim no longer clears it; the bear
case does. LIAB.ST's record (bear 107.23 × 0.70 = 75.06) was linked by the
owner later the same day, `fv_base` 133.48, stop 112 untouched; `vss run
--dry-run` printed both figures live.*

**WHICH EARLIER RULING THIS AMENDS.** **C4**, by the horizon sentence it
lacked. §6.4's reversion trim is unchanged where C4 has not fired.

---

### E43 — the quality leg is OPERATING profitability: EBIT / total assets

**RULED 2026-08-26 by the owner after SCREENER-REVIEW-3 (ruling 1 of five).**

> **THE RULE.** The quality leg of the ranking key is
>
>     operating profitability = EBIT / total assets
>
> where EBIT is the SAME figure the price leg divides — the E8 alias order
> (`Total Operating Income As Reported`, then `Operating Income`, then
> `EBIT`) on the E13 basis (four consecutive quarters where the vendor has
> them, else the filed year; build item 8) — and total assets is the
> balance sheet AT the end of that window (K6). `Gross Profit` leaves the
> ranking ENTIRELY: no component reads it, and an AST test holds the line
> the way one already holds it for `ebitda`. The sector exemption stays as
> E6 ruled it (Financial Services, Real Estate); E46 adds the investment
> companies by list.

**WHY.** SCREENER-REVIEW-3 measured the vendor's `Gross Profit` against the
annual reports of the five names §5 would have received on 2026-08-26, and
it reconciled to a line of the report for NONE of them (A 3.1). The vendor
MANUFACTURES a gross profit for a by-nature filer — net sales less the one
line it calls cost of revenue — so AFRY's is 25,758 − 5,289 of purchased
services with 15,817 of personnel BELOW the line (75.7% of total assets
for an engineering consultancy), Eiffage's leaves 11,254 of subcontracting
out, and for the two that publish a gross profit the vendor carries a
different number: Zinzino 953.8 against the company's 1,119.1, Truecaller
1,019.0 against 1,443.1. B §5.3: the placement bias is real and sector-
robust — not one of 26 US industrials held a top-40 quality rank while 10
of 51 European ones did, three of them in the head, all by-nature filers.
E7 recorded this as a known limitation and built no detector because no
threshold separated the artefacts from the correct cases (UHS from Adobe).
The answer is not a threshold; it is a numerator every filer states.
Operating profit is a line of every income statement in the universe, by
nature or by function, and E8 already measured which vendor label carries
it: `Total Operating Income As Reported` matched the filed operating income
for 30 of 32 US names, to the unit for all six names of report A 4.1.

**THE EVIDENCE FOR THE LEG.** Ball, Gerakos, Linnainmaa & Nissim, *Accruals,
cash flows, and operating profitability in the cross section of expected
stock returns*, Journal of Financial Economics 121(1), 2016: operating
profitability — revenue less the costs the firm incurs to earn it, before
financing and tax — predicts returns at least as strongly as Novy-Marx's
gross profitability and subsumes it once accruals are separated. E6 chose
its leg for a denominator that cannot go to zero; that denominator is kept.
What changes is the numerator, from a line the vendor draws to a line the
company reports.

**WHAT IT MOVES — measured on the frozen 2026-08-21 acceptance fixture (394
names, everything else held still).** The top five goes from UHS, LULU,
DECK, PNDORA.CO, ROCK-B.CO to LULU, DECK, PNDORA.CO, AUTO.L, NVR. UHS,
E7's own case, falls from 1 to 24 (EBIT / total assets 12.8% against the
101.1% of the vendor's gross profit); AFRY.ST from 11 to 190 (5.1%; on the
2026-08-26 accounts 1,387 / 27,040 = 5.1%, quality rank 8 → below the
head); FGR.PA from 8 to 123 (6.2%); BUCN.SW from 10 to 50. Four names the
vendor carried NO gross profit for regain a quality leg — RMV.L (place 9),
ULTA (40), ITV.L (76), SWEC-B.ST (127) — and K6's two mixed-period
refusals resolve, because EBIT and total assets now come from one
statement date: AUTO.L enters at 4, BAB.L at 217. Population 322 → 328 on
both legs, 56 → 50 on yield alone. The 2026-08-26 settled re-run is in the
build report (item 14).

**WHAT IT DOES NOT FIX, stated.** The denominator is the same total assets
on three accounting bases (A 3.3): Nordrest's K3 balance sheet carries no
right-of-use assets and amortises goodwill, Bucher's FER offsets goodwill
against equity, and the goodwill tilt B19 named is unchanged. The
numerator is struck under the same three standards (A 4.1). And the two
legs now SHARE a numerator: a name's quality rank and yield rank both rise
with the same EBIT, so the rank sum is no longer two independent readings
and the Spearman correlation between the legs will sit above E6's 0.14.
That is accepted as the price of a numerator the reports support, and it
is stated here so the sum is not mistaken for a second signal. RMV.L at
225% of total assets is what an asset-light business looks like on this
leg; E6's argument holds — the denominator is never near zero — and the
ratio is printed rather than capped.

**WHICH EARLIER RULING THIS AMENDS.** **E6**, in what the quality leg's
NUMERATOR is; E6's denominator, aggregation, tie rule, one-legged section
and DATA MISSING rule are unchanged. **E7**'s limitation is retired with
the line it described, and E7 stays as the record of why the line had to
go. The UHS row in `config/screener_exclusions.csv` (E7) stands until the
owner removes it: the metric that overstated the name is gone, but the row
is the owner's to lift.

---

### E44 — filter 2's leverage cap is Gate 3's 2.5×

**RULED 2026-08-26 by the owner after SCREENER-REVIEW-3 (ruling 2 of five).
Amends E2.**

> **THE RULE.** The screener's filter 2 rejects a name on leverage above
> **net debt/EBITDA 2.5×** — §3 Gate 3's own cap, inclusive — and no
> longer at §4.2.5's 3.5× hard kill. `config/screener_filter2.yaml`
> carries `max: 2.5` and records 3.5× under `not_chosen`, with E2's reason
> beside it, so the reversal stays legible.

**WHY.** E2 chose the hard kill on the principle that a coarse filter must
not lose a name the manual chain would keep, and cited UNA.AS at 2.27–2.48×.
SCREENER-REVIEW-3 Part 6 measured what the principle cost on the other side:
**72 names passed the code's 3.5× and failed the framework's own 2.5×** on
2026-08-26, four of them in the head-20 and two of them the would-be
PIPELINE entrants — FGR.PA (#1, 2.60×) and AFRY.ST (#5, 3.30×), with HCA
(3.20×) and AD.AS (2.98×) behind them. The screener FEEDS Gate 3. A name at
3.3× fails the hand chain regardless of anything the filing adds, because
Gate 3's cap is 2.5× and the hand chain applies it; passing the name here
only spends section 5 hours on a name the next step removes. E2's UNA.AS
case is unharmed: 2.48× is inside an inclusive 2.5×.

**WHAT THE RATIO HERE IS, stated.** `totalDebt − totalCash` over the
vendor's `ebitda`, all from the quote summary. Report B 6.2 measured the net
debt leg to the unit against E35's legs (leases in, pensions out) on LIAB.ST
and PNDORA.CO, and found the EBITDA leg to be the vendor's own construction
on its own period: LIAB.ST read 3.75× here against the issuer's stated 2.70×.
So this limb is a coarse reading of the gate, not the gate, and the error
runs both ways — it can fail a name the filing would pass as readily as the
reverse. The name it fails is rejected ON VALUE with the ratio printed, so
the owner can see the number and, as with every exclusion, override it by
hand in section 3.

**WHICH EARLIER RULING THIS AMENDS.** **E2**, which stays in this file as the
record of the 3.5× choice and the reason for it. §3 Gate 3 and §4.2.5 are
untouched; E44 only records which of the two a coarse pre-screen enforces.

---

### E45 — the revenue decline is measured on QUARTERS, and it KILLS

**RULED 2026-08-26 by the owner after SCREENER-REVIEW-3 (ruling 3 of five).
Amends B9.**

> **THE RULE.** Filter 2's revenue limb reads the last eight QUARTERS of
> `Total Revenue` from the vendor's quarterly income statement (build item
> 8) and compares each quarter with the same quarter a year earlier. **Two
> or more consecutive year-on-year declines, counted from the newest
> quarter, FAIL the name** — §4.2.1's hard kill, applied at the altitude the
> framework states it. The name is rejected ON VALUE with the declines
> printed. Where the quarters are unavailable — a half-yearly reporter, an
> empty quarterly endpoint, a hole that leaves fewer than two comparisons
> at the newest end — the limb falls back to the ANNUAL series and there it
> only FLAGS, as B9 had it, and the detail says which basis it read and why.

**WHY.** SCREENER-REVIEW-3 Part 8: the limb read annual points only and
never rejected, so a name could decline for six quarters and pass on the
strength of the year before; three head names carried the FLAG on three
consecutive ANNUAL declines with a negative latest quarter — BUCN.SW at #2
and a would-be PIPELINE entrant, with the H1 2026 operating profit −41%
that report A read in its interim — and the flag reached nothing the write
path reads. §4.2.1 is written in quarters and is a kill; the screener now
applies it as written, on the reported basis, because that is the basis
the store holds.

**WHAT THIS COSTS, stated.** B9 carved disposals, demergers and currency
out of §4.2.1 on the organic series, and was decided on UNA.AS: four
consecutive quarters of reported decline while underlying sales grew in
all eight. The screener cannot read the organic series — it is in the
filing, not the quote summary — so **a name in UNA.AS's shape is now
removed at filter 2 on its reported quarters.** That is the price of a
kill the framework states in quarters, and it is paid knowingly: the
organic reading remains B9's rule for the HAND chain, and a name the owner
wants reviewed despite its reported decline is entered by hand, as every
override in this system is. The screener's rejection prints the four
year-on-year changes, so the shape is visible where the decision is made.

**WHAT THE VENDOR'S QUARTERS ALLOW, measured 2026-08-26.** The quarterly
endpoint is patchy (yfinance #1345): BUCN.SW, FGR.PA and HWDN.L return no
quarterly income statement at all; KEMIRA.HE and AFRY.ST lack 2025-09-30;
TRUE-B.ST carries 2025-09-30 as NaN; ERIC-B.ST's 2025-03-31 revenue is NaN.
So of the three FLAG names in report B 8.2, **KEMIRA.HE fails on value**
(Q2 2026 −0.1%, Q1 2026 −4.4% year on year); **BUCN.SW falls to the annual
basis and is FLAGGED** (no quarters at the vendor; summing its two
half-years is R1/B12, which E31 leaves unruled); **ERIC-B.ST falls to the
annual basis and is FLAGGED** (one measurable comparison at the newest end,
the second DATA MISSING on a NaN prior). The rule is as ruled; the vendor
decides which names it can reach, and the detail column says so per name.

**WHICH EARLIER RULING THIS AMENDS.** **B9**, in where the organic carve-out
applies: it governs the hand chain and no longer softens the screener's
limb. §4.2.1 is untouched. E30 (Gate 3's revenue limb deleted) is
untouched: this is §4.2.1's kill, not Gate 3's stability band.

---

### E46 — investment companies are exempt on both legs, by an owner-maintained LIST

**RULED 2026-08-26 by the owner after SCREENER-REVIEW-3 (ruling 4 of five).
Amends E3 and E6 in what decides the exemption.**

> **THE RULE.** An investment company is exempt on BOTH legs the sector
> exemption reaches — filter 2's leverage limb (NOT APPLICABLE) and the
> ranking's quality leg (its own state, `investment company (E46)`, in the
> yield-only section that is never written) — and **membership is decided
> by `config/screener_investment_companies.yaml`, which the owner
> maintains, never by the vendor's sector string.** The Financial Services
> and Real Estate exemptions of E3/E6 stand beside it, on their own string.

**WHY.** SCREENER-REVIEW-3 Part 7.3: the exemption was a rule about a vendor
string, and the vendor splits the Swedish investment companies two ways.
Investor, EQT, Kinnevik, Industrivärden, Bure, Creades and Svolder come back
`Financial Services / Asset Management` and are exempt; **Latour and
Lundbergs come back `Industrials / Conglomerates` and were ranked as
operating companies on consolidated accounts** — Latour at place 263 on
both legs, its EBIT over the total assets of a holding company's
consolidated subsidiaries, its net debt over the same. The string is the
vendor's classification of a listing, not a fact about what the company is,
and III.L's `NO_DATA` sector (1 of 487) showed an exemption that can simply
be absent. A list the owner writes is a decision; a string the vendor
returns is not.

**THE LIST, as entered 2026-08-26.** The eleven Swedish names the owner
named: Investor (INVE-A/B), EQT, Kinnevik (KINV-A/B), Industrivärden
(INDU-A/C), Latour (LATO-B), Lundbergs (LUND-B), Svolder (SVOL-B), Bure,
Creades (CRED-A), Öresund, Traction (TRAC-B). And the STOXX 600 holding
companies the §3.3 logic would otherwise rank, found by name in the STOXX
file and checked against the vendor's string on 2026-08-26 — each in the
file with the reason, the vendor's string, and an `unsure` mark where the
owner should look:

| ticker | company | vendor sector | listed as |
|---|---|---|---|
| EXO.AS | Exor NV | Financial Services | sure — an investment holding (Ferrari, Stellantis, Philips stakes) |
| GBLB.BR | Groupe Bruxelles Lambert | Financial Services | sure |
| SOF.BR | Sofina | Financial Services | sure |
| PRX.AS | Prosus NV | **Consumer Cyclical** | sure — an investment holding (Tencent) the string would RANK |
| AKER.OL | Aker ASA | **Industrials / Conglomerates** | sure — an industrial investment company, Latour's shape |
| ACKB.BR | Ackermans & van Haaren | **Industrials** | **unsure** — a diversified holding that consolidates its contracting arm (DEME) |
| BOL.PA | Bolloré SE | **Communication Services** | **unsure** — a holding (UMG, Vivendi stakes) that still consolidates operating businesses |
| HEIO.AS | Heineken Holding NV | **Consumer Defensive** | **unsure** — a single-asset holding whose consolidated accounts ARE Heineken NV's; the share-class collapse may fold it into HEIA.AS on the fingerprint first |

Considered and NOT listed: Indutrade (INDT.ST) and Lifco (LIFCO-B.ST) —
acquisitive industrial groups that own and OPERATE their subsidiaries; their
consolidated EBIT over their consolidated assets is the operating ratio the
key means. HAL Trust (HAL.AS) is an investment holding but is not in the
STOXX file today and is not listed; add it when it is. A name listed here
that is not in any universe file is inert and the filter-2 report says so.

**WHAT IT MOVES.** On the frozen 2026-08-21 fixture two listed names sat on
the two-legged list, LATO-B.ST and PRX.AS; both move to the yield-only
section and every placing below them renumbers by one on each leg (the
build commit records the pins). Latour is NOT ranked; an industrial with
the same vendor string is.

**WHICH EARLIER RULING THIS AMENDS.** **E3** and **E6**, in what DECIDES
the exemption for an investment company: the list, not the string. Their
sector exemptions stand for banks, insurers, asset managers and property
companies the vendor classifies as such, on E6's ground — the ratio does
not describe them.

---

### E47 — staleness is THREE trading days on the EXCHANGE CALENDAR

**RULED 2026-08-26 by the owner after SCREENER-REVIEW-3 (ruling 5 of five).
Records C3's decision and closes the three-way conflict Part 10.3 found.**

> **THE RULE.** A close is stale when it is older than **three sessions on
> the exchange calendar of the market the row belongs to** —
> `rules.MAX_CLOSE_AGE_TRADING_DAYS = 3`, counted by
> `rules.trading_days_between` with the exchange's closed weekdays
> supplied by `vss/calendars.py` from `config/exchange_calendars.yaml`
> (the universe row's `marknad` mapped to the exchange's MIC). A weekend or
> a market holiday does not age a close. A market the config does not map
> is counted Monday to Friday and NAMED in the report, never silently.

**WHAT THIS CLOSES.** SCREENER-REVIEW-3 Part 10.3 found three statements of
the limit that agreed with none of the others: FRAMEWORK §1.2 said prices
≤ 1 trading day old; C3 proposed "the most recent session on the relevant
exchange calendar" and carried no DECIDED marker; the code said 3 trading
days on a naive Monday-to-Friday count. **The limit is 3, on the calendar.**
§1.2 now carries a one-line pointer to this entry; C3 carries its DECIDED
marker (2026-08-26) and the correction of record against the description's
2026-08-21; and the code supplies the calendar (build item 3).

**WHY THREE, NOT ONE.** §1.2's "≤ 1 trading day" describes the freshness an
ANALYSIS runs on — the next session's close is the price. The tool's gate
is a different question: when is a feed so old that no verdict may be
struck on it? A limit of one session blocks every held name's stop check
on the first morning a fetch is late, which is the failure REVIEW-4 report
A 4.2 measured under the calendar-day rule. Three sessions is the tightness
the gate has always had on an ordinary week, and the calendar removes the
one case where it over-blocked: Christmas Eve to Boxing Day is three closed
weekdays on seven of eleven markets, which collapsed the gate to ONE real
session and removed a whole market on value the first morning after
(Part 10.2, measured off the price table for 63 holiday clusters).

**WHAT IT DOES NOT REACH, stated.** `vss run`'s gate for the watchlist
still counts Monday to Friday: a watchlist entry names no market, and a
calendar guessed from a ticker suffix would be a guess. That path is one
mapping away and is left for the owner to rule on (an entry-level
`market:` field, or the suffix read as a fact about the listing).

**WHICH EARLIER RULING THIS AMENDS.** **C3**, by deciding it; **FRAMEWORK
§1.2**, by the pointer. `MAX_CLOSE_AGE_TRADING_DAYS` is unchanged at 3.

---

### E48 — a German Vorzugsaktie is EQUITY; the ticker rule reaches only the Nordic PREF and D lines

**RULED 2026-08-27 by the owner, after the SCREENER-REVIEW-3 build. Narrows
build item 4 (2026-08-26).**

> **THE RULE.** The universe's `preferred` ticker rule
> (`config/universe/instrument_types.yaml`, `exclude_tickers`) excludes the
> Stockholm `-PREF.ST` and `-D.ST` lines and nothing else. The German
> Vorzugsaktien — the "3"-suffix Xetra lines **VOW3.DE, HEN3.DE, SRT3.DE,
> P911.DE, PAH3.DE, FPE3.DE** — are ordinary shares without a vote, not
> fixed-dividend preference shares, and are **equity in the universe**. The
> `tickers:` list under the rule is empty; a ticker enters it by the owner's
> hand and for a stated reason, never by the loader.

**WHY.** Build item 4 answered SCREENER-REVIEW-3 Part 14.3 — sixteen lines
the sources type as equity reached the band while the type vocabulary said
`preferred` was unwanted — by naming all sixteen, and over-reached on six. A
Swedish preferensaktie carries a fixed dividend and a capped claim, and a
D-share is a common share with its dividend capped to the preference line:
both are economically preference lines and a screener that ranked one as
the company would be valuing a coupon. A Vorzugsaktie is the other thing:
the full residual claim on the company, a dividend preference of a few
cents a share, and no vote. Volkswagen's, Henkel's, Sartorius's, Porsche
AG's, Porsche SE's and Fuchs's preference lines are how the market owns
those companies — for five of the six it is the only listed line, and for
VOW3.DE the ordinary is not a STOXX constituent — so excluding them removed
five companies from the universe entirely and Volkswagen in all but name.
Universe 1,354 → 1,360; `preferred` rejections 16 → 10.

**WHAT IS UNCHANGED, stated.** The rule still reads the TICKER, never the
name string; the type exclusion still beats a ticker rule; a pattern that
does not compile is still a config error. The ten Stockholm lines
(VOLO-PREF, CORE-PREF, NAVIGO-PREF, NP3-PREF, ALM-PREF; SAGA-D, CORE-D,
FPAR-D, SBB-D, INTEA-D) are excluded ON VALUE, reason `preferred`, exactly
as item 4 had them, and their B or A lines stay. Test: HEN3.DE is in the
universe, SBB-D.ST is not (`tests/test_universe.py`).

**WHICH EARLIER RULING THIS AMENDS.** Build item 4 (commit `76cd868`), in
what the `tickers:` list holds. No E-entry is amended; E46's list is a
different list and untouched.

---

### E49 — the fundamentals store RETAINS every period it has ever fetched

**RULED 2026-08-27 by the owner, after the SCREENER-REVIEW-3 build (handoff
item 2, "whether the store should RETAIN quarters across fetches"). Amends
nothing; gives E45 the window it is written for.**

> **THE RULE.** The fundamentals store (`data/screener_snapshots/<date>/
> fundamentals.sqlite`) keeps every period it has ever fetched per ticker.
> A write never unlinks the file. **A re-fetch replaces only the periods it
> returns**; a period it does not return stays, stamped with the fetch that
> supplied it; a returned hole (a NaN quarter, yfinance #1345) never
> overwrites a stored figure; and between two figures for one period the
> NEWER fetch wins, in whatever order the two were written. A new date's
> store is seeded from every earlier-dated store under the same root
> before its own fetch is written, so **E45's eight-quarter window fills
> over time from a vendor that serves five.** Test: two fetches with
> overlapping quarters yield the union (`tests/test_fundamentals.py`,
> `test_e49_*`; `tests/test_screen.py`, `test_e49_*`).

**WHY.** E45 measures the revenue kill on eight quarters and the vendor
serves at most five (392 of 483 names on 2026-08-26): from the newest
quarter, 135 names had two year-on-year comparisons, 259 one, 89 none, so
the two-decline kill could fire only where a hole or a sixth column left
an older quarter in the window. Every fetch until now overwrote the file,
so a quarter the vendor served in May and dropped in August was gone. The
vendor's instability is also the reason for the hole rule: a quarter
present in one fetch and NaN in the next is the endpoint failing, not the
company restating, and E13's "never filled" forbids inventing a figure,
not keeping one the vendor itself supplied and dated.

**WHAT THE FILE NOW SAYS ABOUT ITSELF, stated.** `fundamentals_status` and
`fundamentals_fields` are one row per ticker and describe the fetch that
wrote them (`fetched_at` on the status row). `fundamentals_series` carries
`fetched_at` per row. The manifest's `fetched_at` is the LATEST fetch,
`first_fetched_at` the earliest, `fetches` the history, and `tickers` the
store's count rather than the last fetch's. A file written before this
entry — the 2026-08-21 and 2026-08-26 stores — is migrated in place on the
first write into it: every row gets that file's one fetch as its stamp and
every unlengthed income row the vendor's twelve months; reading never
alters a file. A ticker whose periods were carried in but which this
store's fetch never visited has series rows and no status row: the chain
does not see it until a fetch does, and the `--fundamentals` report counts
such names under RETENTION.

**WHAT MOVES DOWNSTREAM.** The net-debt date each ranking row carries
(`ranking.csv`, `net_debt_date`) is now each record's OWN fetch, not the
file's latest — one store holds several fetches and the manifest's date
would misdate a name fetched earlier. The look-ahead banner names both the
first and the latest fetch when they differ. A later-dated store is never
read backwards into an earlier one: a period it holds may postdate the run.

**WHICH EARLIER RULING THIS AMENDS.** None. E45 is applied as written;
E13's basis rule is untouched (a hole inside the four newest is still DATA
MISSING for the basis — retention supplies figures the vendor served, never
figures it did not).

---

### E51 — pharmaceuticals and biotech are OUTSIDE THE CIRCLE OF COMPETENCE

**RULED 2026-08-27 by the owner. Amends nothing; adds a step-0 exclusion
beside the owner's own list. First application NOVO-B.CO, entered PIPELINE
2026-08-27 on the 2026-08-26 ranking and DROPPED by this ruling.**

> **THE RULE.** A pharmaceutical or biotechnology company — one whose cash
> flow beyond the next patent expiry depends on **clinical trial outcomes
> and regulatory approval** — is **outside the circle of competence, and
> §5 cannot be run on it.** The pre-registered growth rate E28 requires
> would be a guess about drug approvals, not an estimate of a business.
> **The name is removed at STEP 0, with the reason recorded**, and the rule
> **applies regardless of screener rank**.
>
> **Membership is decided two ways, and BOTH are recorded in
> `config/screener_pharma_biotech.yaml`:**
>
> 1. **The vendor's industry string**, where one is stored for the ticker —
>    today `Biotechnology`, `Drug Manufacturers - General` and
>    `Drug Manufacturers - Specialty & Generic`. The strings are listed in
>    the file, never hardcoded.
> 2. **An owner-maintained ticker list**, which reaches a name the string
>    misses or does not describe.
>
> A name the string limb catches and the owner has ruled back IN goes in
> that file's `exempt:` block, **by ticker, with the reason**. The block
> exists so the decision is written down; **nothing is exempted by a
> session.**

**WHY THE STRING IS NOT ENOUGH, AND WHY THE LIST IS NOT ENOUGH EITHER.**
E46 already established that a vendor's classification of a listing is not
a fact about what the company is — Latour comes back `Industrials /
Conglomerates` and is an investment company. The same failure runs both
ways here. `Biotechnology` is what the vendor calls **Financière de Tubize
(TUB.BR)**, a holding company whose one asset is a stake in UCB, and
**Flerie AB (FLERIE.ST)**, a life-science *investment* company: neither
runs a trial. And `Drug Manufacturers - Specialty & Generic` is what it
calls **Siegfried Holding (SFZN.SW)**, a contract manufacturer that makes
other companies' molecules and carries no pipeline of its own. A list
without the string would miss most of the sector; a string without the
list catches businesses the rule's own reasoning does not reach. **Both,
and the disagreements printed rather than resolved silently.**

**WHAT THE STRING LIMB CANNOT SEE, STATED.** The sector and industry
strings are the vendor's, and the screener fetches fundamentals **only for
the survivors of filter 1** — 485 of 1,370 names carried a sector string on
2026-08-26. **The string limb is therefore blind to a name that has never
reached the fundamentals fetch**, and its silence about such a name is a
fact about the fetch, not about the company. This is the same third state
DATA MISSING is everywhere else here. The owner's ticker list is the limb
that does not depend on it, and E49's retention makes the string coverage
grow rather than shrink.

**WHAT IT CATCHES ON THE 2026-08-26 STORE, as ruled.** Fifteen names on the
string limb:

| industry | names |
|---|---|
| `Biotechnology` | ABVX.PA, ALK-B.CO, CAMX.ST, FLERIE.ST, TUB.BR, UCB.BR, VICO.ST, ZEAL.CO |
| `Drug Manufacturers - General` | AZN.L, AZN.ST, GRF.MC, GSK.L, **NOVO-B.CO** |
| `Drug Manufacturers - Specialty & Generic` | ALVO-SDB.ST, SFZN.SW |

**NOT caught, and correctly:** every `Medical Devices` name (ABT, GEHC,
NOLA-B.ST, PHIA.AS, SECT-B.ST, SHL.DE, SN.L, SYK, VITR.ST), every
`Medical Instruments & Supplies` name (ALGN, ALIF-B.ST, BONEX.ST,
COLO-B.CO, DYVOX.ST, ISRG, RMD, STIL.ST), every `Diagnostics & Research`
name (BIM.PA, IDXX, QIA.DE), and `Medical Distribution`,
`Medical Care Facilities`, `Health Information Services` and
`Pharmaceutical Retailers`. **A device or a diagnostic sells a product
whose approval is behind it; that is a different business from a pipeline,
and this rule does not reach it.**

**THREE THE OWNER SHOULD LOOK AT, FLAGGED AND NOT DECIDED.** TUB.BR and
FLERIE.ST are holding companies the string calls biotech — TUB.BR is also
an E46 candidate. SFZN.SW is a CDMO. **All three are excluded as the rule
is written; none is exempted, because that is the owner's call and the
`exempt:` block is where it would be recorded.** GRF.MC (plasma-derived
products) and ALVO-SDB.ST (biosimilars) sit nearer the line than the rest
and are named here for the same reason.

**WHICH EARLIER RULING THIS AMENDS.** None. It sits beside E46 as a second
owner-maintained list at a different step, and beside the exclusion list
(`config/screener_exclusions.csv`), which stays what it is: names already
owned or already decided one at a time.

---

### E52 — a listing younger than five years is REJECTED at filter 1, on MISSING data

**RULED 2026-08-27 by the owner. Amends nothing; raises a bar E11/E12's
freeze already depended on. First application NREST.ST, entered PIPELINE
2026-08-27 on the 2026-08-26 ranking and DROPPED by this ruling.**

> **THE RULE.** A name whose **price history does not reach five years back
> from the run date** is rejected at **filter 1, ON MISSING DATA** — not
> enough reported history to judge. It did not fail a limb; the limbs could
> not be evaluated on it.
>
> **Measured from the STORED PRICE SERIES**, on the oldest bar the snapshot
> carries for the ticker (`metrics.first_bar_date`), and **never from the
> universe CSV's `listdatum`**, which is empty on most rows and would
> reject the whole universe on a field the vendor does not fill.
>
> **The price fetch period is raised from `2y`** so the series can answer the
> question at all (`vss/fetch.py`, `DEFAULT_PERIOD`).

**CORRECTION, SAME DAY, BEFORE THE FIRST RUN: THE FETCH IS `6y`, NOT `5y`.**
The ruling as dictated said `5y`, and a `5y` fetch **cannot serve a 5-year
floor**. The vendor measures its window from **today**, while `as_of` is at
or before today, so five years back from today is **short of** five years
back from any earlier run date. Measured on 2026-08-27: the fetch began
**2021-08-27**, the floor for `--asof 2026-08-26` was **2021-08-26**, and
**all 1,328 names that reached the step were rejected — by one day, on the
run’s own fetch parameter.** The extra year is a **margin**, and it is the
same margin `metrics.COVERAGE_MARGIN_TRADING_DAYS` already exists for: a
window that exactly reaches a bar does not cover it. **The RULE is five
years and is unchanged; only the means is.**

**WHY.** Five years is the shortest history in which this framework's own
questions have answers. §5.1 Method A reads a **5-year median** multiple;
§3's Gate 3 quality floor reads eight quarters; E45 reads eight quarters of
revenue; and a reverse DCF struck on a company that has never been through
a full cycle is a growth rate fitted to one regime. A two-year series
answers the dislocation band and nothing above it, and the band is the
cheapest gate in the chain.

**HOW THIS RELATES TO THE 52-WEEK COVERAGE BAR, at file and line.** The two
rules measure the **same quantity on the same axis** — how far back the
first bar of the truncated series reaches — and differ only in how far they
demand it reach:

| | coverage bar | E52 |
|---|---|---|
| constant | `vss/metrics.py:76-77` — `COVERAGE_WEEKS = 52`, `COVERAGE_MARGIN_TRADING_DAYS = 5` | `vss/metrics.py` — `LISTING_AGE_YEARS = 5` |
| cutoff | `vss/metrics.py:80`, `coverage_start(as_of)` | `vss/metrics.py`, `listing_age_start(as_of)` |
| predicate | `vss/metrics.py:91`, `covers_52_weeks(first_bar, as_of)` | `vss/metrics.py`, `covers_listing_age(first_bar, as_of)` |
| read at | `vss/metrics.py:330-333` — gates `high_52w`, `high_52w_date` and hence `drawdown` to None | `vss/filters.py`, the `listing_age` step of `run_filter1` |
| effect | the 52-week high is **DATA MISSING**, and filter 1 turns that into an ON_MISSING *dislocation* rejection at `vss/filters.py:370-378` | the name is rejected at its **own step**, ON_MISSING, before the band is reached |

> **ONE SUBSUMES THE OTHER IN ONE DIRECTION ONLY, AND NEITHER IS DELETED.**
> Five years is strictly longer than 52 weeks plus five trading days, so
> **every series that fails the coverage bar also fails E52** and, with E52
> running first, no name will reach `vss/filters.py:370-378` on the
> `series does not cover 52 weeks` branch again. **The converse is false**:
> a series of three years passes the coverage bar and fails E52.
>
> **The coverage bar STAYS, for two reasons that are not about the
> screener.** First, it is a rule about what `high_52w` MEANS, enforced
> inside `metrics.compute`, and `vss run` prices the live watchlist through
> that same function without passing filter 1 at all — E11/E12 freeze a
> drawdown against a 52-week high, and the bar is what stops that freeze
> being struck off 120 rows (REVIEW-4 report B 7.2: DECK read 22.4% against
> a true 28.4%). Second, a rule that returns DATA MISSING for a figure and
> a rule that removes a NAME are different acts, and collapsing them would
> put the screener's admission policy inside a metrics function.
>
> **So the `covers_52_weeks` branch in filter 1 becomes unreachable from
> the screener and is KEPT anyway**, because reachability here is a
> property of E52's constant and not of the code, and a branch deleted on
> today's constant is a silent failure the day the constant moves.

**WHAT IT COSTS, stated.** A young listing is removed on a fact about the
DATA, not about the company, and a genuinely good business that IPO'd four
years ago is unreachable until its fifth anniversary. That is the trade the
rule makes deliberately: this framework's defect is that it cannot say yes,
and the answer to that is not to say yes on less evidence.

**A SECOND EFFECT OF THE LONGER FETCH, and it is not E52's.** Extending the
window to five years gives `vss/series_sanity.py` three more years of tape
to find a break in, so a name may become unmeasurable that was measurable
on two years. That is the sanity check working on more evidence, and the
run report counts it under its own step — **it is not an E52 rejection and
must not be reported as one.**

**WHICH EARLIER RULING THIS AMENDS.** None. The coverage bar stands
unchanged at `vss/metrics.py:76-77`; E47's staleness gate is untouched (it
asks how NEW the last bar is, this asks how OLD the first one is, and a
name can fail either alone).

---

### E52.1 — a spin-off is a NEW LISTING, and the floor does not care that the business is older

**RULED 2026-08-27 by the owner, on the first run E52 governed. Amends
nothing; CLOSES a question E52's own removals raised, so that it is not
reopened.**

> **THE RULE.** **E52 stands exactly as written.** A company whose price
> series is shorter than five years is rejected **regardless of whether its
> business is older than its listing.** A spin-off, a demerger, a carve-out
> and a first-time IPO are **one case** to this floor, and there is **no
> exemption, no list and no per-name judgement.**

**WHY, AND THE REASON IS THE FLOOR'S OWN PURPOSE.** An exemption would have
to be decided **per carve-out**: whether the parent's history transfers,
which segment of it, how much of the cost base moved, whether the audited
carve-out accounts describe the entity that now trades. **That is exactly
the work the floor exists to avoid** — E52's stated ground is *not enough
reported history to judge*, and adjudicating each carve-out is judging. A
rule that removes a name on a fact about the DATA becomes, the moment it
takes exemptions, a rule that removes a name on an opinion.

**AND THE PRICE SERIES IS NOT A FORMALITY.** What the floor is short of is
not the company's operating record but **the market's record of pricing
it**: no full cycle of this security, no multiple history for §5.1 Method A,
no peak that a 52-week high can be struck against for more than one
rotation. A carve-out's pre-spin financials, however audited, were never
priced. **That is the missing thing, and a spin-off is missing it exactly
as an IPO is.**

**WHAT THIS KNOWINGLY KEEPS OUT, on the 2026-08-26 run.** The spin-offs,
demergers and carve-outs among E52's 81 removals, all with real operating
histories longer than their tapes:

| ticker | company | first bar |
|---|---|---|
| GEV | GE Vernova | 2024-03-27 |
| GEHC | GE HealthCare | 2022-12-15 |
| KVUE | Kenvue | 2023-05-04 |
| HLN.L | Haleon | 2022-07-18 |
| SDZ.SW | Sandoz Group | 2023-10-03 |
| DTG.DE | Daimler Truck | 2021-12-10 |
| P911.DE | Porsche AG (pref) | 2022-09-30 |
| ALLEI.ST | Alleima | 2022-08-31 |
| ACLN.SW | Accelleron | 2022-09-30 |
| SYENS.BR | Syensqo | 2023-12-11 |
| VLTO | Veralto | 2023-10-04 |
| SOLV | Solventum | 2024-03-26 |
| SNDK | Sandisk | 2025-02-13 |
| Q | Qnity Electronics | 2025-10-27 |
| FDXF | FedEx Freight | 2026-05-27 |
| HONA | Honeywell Aerospace | 2026-06-15 |
| AMV0.DE | Aumovio | 2025-09-18 |
| MICC.AS | Magnum Ice Cream | 2025-12-08 |
| IVG.MI | Iveco Group | 2022-01-03 |
| MANTA.HE | Mandatum | 2023-10-02 |

**TWO CASES THAT ARE NEITHER SPIN-OFF NOR IPO, NAMED AS KNOWN COLLATERAL
AND ACCEPTED.** These are not carve-outs at all — they are **an existing
company acquiring a new line**, and the floor removes them on the same fact:

| ticker | what it actually is | first bar |
|---|---|---|
| **SAMPO-SEK.ST** | Sampo Oyj — a Finnish insurer over a century old — on a **new SEK-denominated Stockholm line** listed 2026 | 2026-03-31 |
| **EXO.AS** | **Exor NV moving its listing** from Milan to Amsterdam in 2022; the company is the same one | 2022-08-12 |

**Accepted, not overlooked.** Curing them would need a rule that identifies
one issuer across two tickers and inherits the older tape — the machinery
`ranking.py`'s share-class fold already has in one narrow form, and
extending it to cross-border relistings and new currency lines is a project,
not an exemption. **Until someone builds it, these two are the price of the
floor, and this entry is where that price is written down.** (EXO.AS is
also on E46's investment-company list and would have been yield-only in any
case; SAMPO-SEK.ST would not.)

**WHICH EARLIER RULING THIS AMENDS.** **None.** E52 is confirmed as
written. This entry adds no mechanism and no code — **it exists so that the
question is answered in the record rather than re-argued at each run.**

---

### E51.1 — two exemptions, and a holding company belongs on E46's list, not in E51's escape hatch

**RULED 2026-08-27 by the owner, on the three names E51's first run flagged.
Amends E51 in its `exempt:` block and E46 in its list. Neither rule's
GROUND moves.**

> **THE RULE, in three parts.**
>
> 1. **SFZN.SW — Siegfried Holding AG — is EXEMPT from E51.** A CDMO:
>    it manufactures other companies' molecules under contract and carries
>    **no pipeline of its own**, so nothing about its cash flow beyond a
>    patent expiry turns on a trial reading out. The vendor's
>    `Drug Manufacturers - Specialty & Generic` describes what it makes,
>    not what it bears.
> 2. **FLERIE.ST — Flerie AB — is EXEMPT from E51.** A life-science
>    **investment company**; it holds positions in developers and is not
>    one. The vendor's `Biotechnology` describes its holdings.
> 3. **TUB.BR — Financière de Tubize SA — is NOT exempt, and is added to
>    E46's investment-company list instead.** A holding company whose sole
>    asset is a stake in another listed company (UCB) **belongs where the
>    other such holdings are.** Putting it in E51's `exempt:` block would
>    have said *"this is not pharma"* and stopped there; E46's list says
>    what it **is**.

**WHY THE THIRD IS NOT SYMMETRICAL WITH THE FIRST TWO, AND WHY IT MATTERS
THAT IT IS NOT.** E51's `exempt:` block is a NEGATIVE statement — it can only
ever say *this name is not what the string called it*. For Siegfried and
Flerie that is the whole of the correction: one is a manufacturer, the other
an investor, and neither needs a second classification to be handled
correctly. **Tubize does.** Its consolidated accounts are UCB's economics
seen through a stake, and E46 exists precisely because *"EBIT over the total
assets of a holding company's consolidated subsidiaries"* is not the
operating ratio the ranking key means (E46, on Latour at place 263).
**Exempting it from E51 alone would have handed the key a name it cannot
rank, with nothing left to catch it.**

**WHAT THIS DOES NOT DO, AND THE ORDER IS THE REASON.** **TUB.BR is still
removed by E51, at step 0, before anything reads E46's list.** Step 0's
second limb runs on the vendor string, the string is still `Biotechnology`,
and the owner declined to exempt it. So **the E46 entry is INERT today** and
the filter-2 report will say so under its own inert-entry line. **That is
the intended state, not an oversight:** the classification is written down
now, correctly, and takes effect the day E51's catch on this name is ever
lifted. A classification recorded only at the moment it is needed is a
classification made under pressure.

**WHAT MOVES ON THE 2026-08-26 RUN.** Nothing in the ranking. The two
exemptions return SFZN.SW and FLERIE.ST to a chain that removes them a step
later anyway. **The exemptions are recorded for what they will do, not for
what they did** — and the run report now prints them, which is the point of
the block.

> **CORRECTION, same day, on the re-run this ruling was made for.** The
> paragraph above first said the three names were *"outside the dislocation
> band and none reached filter 2"*. **The first half was wrong.** SFZN.SW
> and FLERIE.ST are **inside the band and are filter-1 candidates** — the
> candidate count goes 440 → 442 on exactly these two. What removes them is
> **filter 2, on a value**, and it is worth naming because it is a stronger
> statement than the band would have been:
>
> | ticker | free cash flow | net debt / EBITDA | revenue trend |
> |---|---|---|---|
> | SFZN.SW | **FAIL** — TTM FCF −137,695,248 | **FAIL** — 2.59× against E44's 2.5× cap | PASS |
> | FLERIE.ST | **FAIL** — TTM FCF −27,487,000 | PASS — EBITDA −40,300,000 not positive, net debt −304,000,000 | PASS |
>
> TUB.BR is the one that never becomes a candidate, because E51 removes it
> at step 0 and it never reaches a price series at all. **The conclusion —
> nothing moves in the ranking — is unchanged; the reason for two of the
> three was not what this entry first said it was.**

**WHICH EARLIER RULINGS THIS AMENDS.** **E51**, in its `exempt:` block —
the first two rows it has ever carried, each with its reason, as E51
requires. **E46**, in its list — one ticker added, on E46's own stated
ground and not on E51's.

---

### E51.2 — the owner's ticker list is filled, and ROG.SW does not resolve

**RULED 2026-08-27 by the owner, closing the gap E51's first run measured.
Amends E51 in its `tickers:` block only. The ground does not move.**

> **THE RULE.** `config/screener_pharma_biotech.yaml`'s **`tickers:` block
> is filled with the pharmaceutical and biotechnology names the vendor's
> industry string cannot reach today**, because fundamentals — and so the
> strings — are fetched **for the survivors of filter 1 alone**. The list is
> **owner-maintained**. **The string limb remains the PRIMARY catch**; this
> block is the second limb, for names the vendor has not classified in this
> store.

**WHY IT WAS NEEDED, measured.** On the 2026-08-26 run **794 of the 1,345
names offered to step 0 carried no vendor string at all** — 59% of the
universe. Every large-cap pharmaceutical major was among them, none of them
because it is not pharma but because none had ever survived filter 1 and so
none had ever been fetched. **A name entering the dislocation band for the
first time would have ranked once before the string caught it**, and E51
says section 5 cannot be run on these names at all.

**TWENTY NAMES ENTERED, one per line with its market, all checked against
the universe files:** PFE, MRK, MRK.DE, LLY, NOVN.SW, SAN.PA, BAYN.DE,
ABBV, AMGN, GILD, BIIB, REGN, VRTX, GMAB.CO, ARGX.BR, SOBI.ST, HIK.L,
IPN.PA, REC.MI, ORNBV.HE.

> **ONE DID NOT RESOLVE, AND NOTHING WAS SUBSTITUTED FOR IT.**
> **`ROG.SW` IS NOT IN ANY UNIVERSE FILE.** It is Roche's *registered
> share* (Namenaktie). **The only Roche line this universe carries is
> `ROP.SW`** — `ROCHE PS PAR AG`, the *Genussschein* participation
> certificate, in `stoxx600-2026-08-22.csv`.
>
> **`ROG.SW` is entered as the owner wrote it and is INERT**: it matches
> nothing, and the step-0 report names it under its inert-entry line every
> run, as E46's list does for a name outside the universe. **`ROP.SW` was
> NOT added.** Substituting a ticker the owner did not name — even the
> obviously intended one, even in the same issuer — would make the file
> say something the owner did not, and the standing instruction was **not
> to invent a ticker to make the list complete.**
>
> **THE CONSEQUENCE, STATED PLAINLY: ROCHE IS NOT EXCLUDED TODAY.**
> `ROP.SW` carries no vendor string in this store either, so neither limb
> reaches it. **It is one line in the file away from being covered, and
> that line is the owner's to write.**

**WHAT THE LIST IS NOT.** It is not a claim that these twenty are the only
pharma in the universe, and it must not be read as one. It is the set the
owner named after seeing a name-based scan of the 794 unclassified names,
and **a scan by NAME is evidence about names**. The string limb is what
generalises; this block is what covers the vendor's silence in the meantime,
and **E49's retention makes the string coverage grow rather than shrink**,
so the list should get shorter over time, not longer.

**WHAT MOVES ON THE 2026-08-26 RUN.** Nothing in the ranking. Every one of
the twenty was outside the dislocation band, exactly as expected — the gap
this closes is **prospective**, and the entry is the reason it was closed
before it cost anything rather than after.

**WHICH EARLIER RULING THIS AMENDS.** **E51**, in its `tickers:` block. The
string limb, the `exempt:` block and the counting of unclassified names are
untouched.

---

### E53 — a share count printed ROUNDED is still a STATED count, and it is entered at its own rounding

**RULED 2026-08-27 by the owner, first application AUTO.L. Amends nothing in
E22's rule; narrows how it is satisfied where the exact figure is not
printed.**

> **THE RULE.** Where the exact share count at a period end is not printed
> but a **rounded** one is, **the rounded figure is entered, with the
> `share_unit` that matches the rounding, and the rounding is recorded on
> the field.** This does **not** relax E22: **a stated count, however
> rounded, is still a stated count. A DERIVED one is not**, and the line
> between the two is exactly where it always was — subtraction and division
> remain forbidden, rounding by the ISSUER is not.

**AUTO.L, AS RULED.** `shares_issued_period_end: 827,503` with
`share_unit: thousands`, per AR p.125 note 25: *"Total 8 2 7, 5 0 3"*
thousand shares (the PDF text layer inserts spaces inside the numeral; the
printed figure is 827,503). **Exact to ±500 shares** — a rounded thousand
can sit anywhere from 827,502,500 to 827,503,499.

**WHAT WAS NOT DONE, AND WHY.** Note 11 (AR p.117) states the opening issued
count as 884,700,426 and note 25 states the year's cancellation as
57,197,994; their difference, 827,502,432, is **one shares figure more
precise than the one printed** — and is exactly the derivation E22 already
forbids: *"share capital divided by a par value is not a count… A count is
the count, as stated."* A subtraction of two stated figures is no different
in kind from a division, for this purpose: **neither is what note 25 prints,
and the file states what the accounts state, not what a reader can compute
from them.**

**THE UNIT CONFLICT, NAMED RATHER THAN SILENTLY RESOLVED.** AUTO.L's own
annual report is **not internally consistent** on this point: **note 25
prints thousands** (*"827,503"*, a five-figure number with a header stating
the column is in thousands) while **notes 11 and 26 print whole units**
(*"884,700,426"*; *"4,412,082"*). **The file's `share_unit` follows note
25** — the field this ruling fills — and the whole-unit figures in the other
two notes are entered as whole units on their own fields, because
`share_unit` is declared **once per file** (E16's schema) and this is the
one line among the three that cannot be exact.

**WHAT THIS COSTS, STATED.** A count entered to ±500 shares carries that
imprecision into every per-share figure the store computes from it — around
0.00006% of AUTO.L's share base. Recorded because E13's own rule is that a
small error is still an error, not because this one moves anything.

**WHICH EARLIER RULING THIS AMENDS.** None. E22 is unchanged; this rules on
a case E22's text did not already resolve on its face — a rounded, stated
figure — and resolves it in E22's own direction, not against it.

> **CORRECTION, same day, before the file was written: `share_unit` IS ONE
> SCALE FOR THE WHOLE FILE, not per-field, and the entry above did not say
> so.** `vss/runrecord.py` reads exactly one `shares.unit` and multiplies
> the WHOLE record's share count by `UNIT_SCALE[shares.unit]` — there is no
> per-field unit, and a sentence reading *"the whole-unit figures in the
> other two notes are entered as whole units on their own fields"* describes
> a mechanism the schema does not have.
>
> **THE FIX IS A CONVERSION, NOT A CONTRADICTION.** `share_unit: thousands`
> is declared once, and **every** share-count figure is expressed in
> thousands: note 25's 827,503 enters AS PRINTED (already in thousands, and
> the one line whose ±500-share imprecision is the ISSUER's rounding, not
> this file's); note 11's 884,700,426 and note 26's 4,412,082 and 282,389
> enter as **4,412.082**, **282.389** and **862,666.25** (note 11's diluted
> weighted-average count) — an EXACT division by 1,000 of a whole-unit
> figure, losing no precision, in the same sense `config/manual/LIAB.ST.yaml`
> already converts "77,036 thousand" to `77.036` under `share_unit: millions`.
> **This is declaring one unit and re-expressing every count in it, which
> is what `money_unit`/`share_unit` are FOR** — not the cross-period
> "rescale by hand" TEMPLATE.yaml forbids, which guards against papering
> over a suspected reporting error between two DIFFERENT periods, not
> against restating one period's own figures in one chosen scale.

---

### E54 — an employee benefit trust is excluded from the divisor alongside treasury, and gets its OWN field

**RULED 2026-08-27 by the owner, first application AUTO.L. Amends E16: the
schema gains a fourth share-count field.**

> **THE RULE.** Where an issuer excludes BOTH treasury shares and shares
> held by an **employee benefit trust** (an ESOT, ESOP or equivalent) from
> its own basic EPS count, **the tool's divisor does the same.** The trust
> leg gets **its own schema field**, `employee_trust_shares_period_end`,
> and is **never folded into `treasury_shares_period_end`** — a combined
> figure there would enter under a field whose own definition it does not
> meet, misnaming what was found.

**AUTO.L, AS RULED.** Note 11 (AR p.117): basic EPS uses the weighted
average *"excluding those held in treasury and by the Employee Share
Option Trust ('ESOT')."* Note 25 and note 26 (AR p.125) print the two
counts **separately** at the period end: treasury **4,412,082**, ESOT
**282,389**. `employee_trust_shares_period_end: 282,389`, page
"note 26, p.125".

**THE MECHANISM, AND WHY IT IS NOT SYMMETRIC WITH THE ISSUED/TREASURY
PAIR.** E16's original rule is strict: *"Where only ONE of the pair is
available, all three stay DATA MISSING"* — issued and treasury are a pair,
and half a pair proves nothing. **The trust leg is not a member of that
pair and does not carry its rule.** It is optional in a way issued and
treasury are not: **most issuers carry no employee trust at all**, and its
absence must never block the subtraction E16 already performs. Where it is
present, the store subtracts it a third time; where it is absent, the net
is issued minus treasury alone, exactly as before E54. `vss/manual.py`'s
`Subtraction` dataclass carries this as `optional_subtrahend` — present on
the share-count rule alone, `None` on both finance-cost nets, which
therefore behave exactly as they did before this ruling.

**WHAT THE FIELD IS NOT.** It is not a general "other exclusions" bucket.
It exists for **one shape**: a holding the issuer itself states is excluded
from ITS OWN EPS count, stated as a count, separately from treasury.
Anything else the schema does not already reach stays DATA MISSING under
E22, as before.

**Implemented and tested**: `vss/manual.py` (`FieldSpec`, `ZERO_REFUSED`,
`SECTION5_SCALE_FIELDS`, `STOCK_FIELDS`, `Subtraction.optional_subtrahend`,
`NetShares.optional`, `subtract()`, `basis_subtraction()`,
`section5_subtractions()`), `vss/runrecord.py` (`leg()`'s provenance
string, unreached by this leg today — nothing in the run record divides by
`shares_outstanding_period_end`; A6 reads
`diluted_weighted_average_shares` instead — handled anyway so a future
caller cannot silently drop the leg's evidence), `config/manual/TEMPLATE.yaml`.
Tests: `tests/test_manual.py`, `test_e54_*` (nine cases: schema presence,
optional absence leaving the pair-only net unchanged, presence subtracting
a third time, the report printing all three legs, the report unchanged
with no trust stated, the folded-vs-separate arithmetic agreeing while the
provenance differs, no write-back, outright zero refusal matching the
other three count fields, `appendix.py` never computing it).

**WHICH EARLIER RULING THIS AMENDS.** **E16**, by adding a field E16 did
not have. E16's own pair rule — issued and treasury, all-or-nothing — is
untouched.

---

### E55 — inventory finance is WORKING CAPITAL, not net debt

**RULED 2026-08-27 by the owner, first application AUTO.L's vehicle
stocking loan. Amends nothing; resolves a case the net-debt fields did not
already settle on their face.**

> **THE RULE.** A facility that (1) can **only** fund goods held for
> resale, (2) **self-liquidates on their sale**, and (3) is **presented by
> the issuer inside trade payables rather than borrowings**, is working
> capital, not financing, and is **OUT OF NET DEBT.**

**AUTO.L, AS RULED.** The £5.0m vehicle stocking loan meets all three
conditions on the documents' own words. **(1) Purpose, restricted by the
facility itself**: *"This financing arrangement can only be used to fund
the purchase of new and used vehicles prior to re-sale"* (AR p.113, note
3). **(2) Self-liquidating**: *"has a maturity of 180 days or less. The
loan is repayable on the earliest of the vehicle delivery date or the
maturity date"* (AR p.113) — it does not survive the sale of the vehicle
it funded. **(3) Presentation**: the issuer books it inside **trade and
other payables** — *"Vehicle stocking loan 5.0"* (AR p.121, note 20) — and
**excludes it from both of its own net-debt figures**, the £146.8m "net
bank debt" (AR p.23) and note 31's £188.3m net debt (AR p.131).

**`financial_liabilities_current` therefore takes `zero_basis: caption` on
the printed dash**: *"Less than one year – "* (borrowings, AR p.121, note
21) and *"Debt due within one year – "* (note 31, AR p.131) — both captions
the issuer prints with a dash rather than an omission, which is exactly
what E25's `caption` form requires.

**THE COUNTER-EVIDENCE, RECORDED RATHER THAN OMITTED.** The facility is not
free money and this ruling does not pretend otherwise: it **bears
interest** at *"the prevailing Bank of England Base Rate plus a 2% margin"*
(AR p.113); **£0.3m was paid** on it in the year (AR p.131, note 30); and
**note 30's own maturity analysis lists it as a financial liability** —
*"Due within one year… Vehicle stocking loan £5.0m"* (AR p.131). **All of
that is true, and none of it is what governs here.** The rule turns on
*purpose and self-liquidation*, not on whether a balance bears interest —
a bank overdraft bears interest too, and inventory financed at cost is not
made a claim on the enterprise's general assets by carrying a rate.

**WHAT WOULD CHANGE THE ANSWER, STATED SO THE RULING IS FALSIFIABLE.** A
facility that could be drawn for purposes OTHER than financing inventory
held for resale, or that survived the sale of the vehicles it funded
(rolling working capital rather than a matched, self-liquidating draw),
would not meet condition (1) or (2) and this ruling would not reach it.
Autotrader's own covenant language treats the facility as distinct from
its Syndicated RCF throughout the filing, which is further (if secondary)
evidence it is not being treated by the issuer as general financing.

**WHICH EARLIER RULING THIS AMENDS.** None. It is a first application of
E25's `caption` form and of the net-debt fields' own scope; no net-debt
ruling previously reached a purpose-restricted, self-liquidating inventory
facility.

---

### E56 — net debt includes lease liabilities, confirmed against an issuer's own NARROWER figure

**RULED 2026-08-27 by the owner, first application AUTO.L. Confirms E35
("leases are in net debt, always") on a case that tested it directly: an
issuer that publishes its OWN leverage ratio on a net-debt definition that
excludes leases.**

> **THE RULE.** Where an issuer publishes a leverage ratio struck on a
> net-debt definition that **excludes leases**, **the tool does not adopt
> it.** E35 governs regardless of what the issuer's own headline ratio
> uses.

**AUTO.L PRINTS THREE NET-DEBT-SHAPED FIGURES, and this ruling says which
one is `net_debt` here and which two are not:**

| figure | £m | source | leases in it? |
|---|---|---|---|
| "Net bank debt" | 146.8 | AR p.23; five-year record p.141 | **No** |
| Note 31 net debt | **188.3** | AR p.131, note 31 | **Yes** — 163.4 borrowings + 42.6 leases + 0.5 accrued interest − 18.2 cash |
| Balance-sheet components, no accrual | 187.8 | AR p.103 | Yes, but omits the £0.5m accrued interest leg |

**RULED: 188.3, note 31's figure, is `net_debt`.** It is the issuer's OWN
line stated to be *"total borrowings and lease liabilities, less cash and
cash equivalents"* (AR p.131) — the definition E35 already requires, in the
company's own words, not a reconstruction. £146.8m is the company's
narrower "net bank debt", used for its own covenant and leverage
disclosure; E35 was ruled precisely so that an issuer's choice of headline
ratio does not become the tool's.

**THE £0.5M ACCRUED INTEREST — RULED IN.** Note 31's own reconciliation
carries it as a named leg of the total (*"Accrued interest… 0.5"*, AR
p.131) and its year-end total, 188.3, already includes it — the 187.8
figure is what remains if that leg is dropped, and nothing in the
documents supports dropping a leg the issuer's own total counts. **The
accrued interest stays in, because it is part of the ONE figure the issuer
states as its net debt, not a separate item this ruling is adding to it.**

> **`net_debt_ebitda` IS LEFT DATA MISSING, and the printed 0.3x IS NOT THE
> FIELD'S VALUE.** The 0.3x is struck on a **different numerator** — the
> £146.8m "net bank debt" this ruling has just declined, not 188.3 — **and**
> a **non-standard EBITDA**: *"earnings before interest, taxation,
> depreciation and amortisation, share-based payments and associated NI,
> share of profit from joint ventures and exceptional items"* (AR p.122,
> note 21) — a covenant EBITDA that strips share-based pay and joint-venture
> profit, which is not what this schema's `ebitda` field means and which
> the documents do not in any case state as an amount (only the ratio).
> **Importing 0.3x would enter a figure struck on two departures from the
> field's own definition at once, under a name that claims it is neither.**
> `net_debt_ebitda: null`, and the report says why rather than leaving the
> silence to be misread as an oversight.

**WHICH EARLIER RULING THIS AMENDS.** **None — this CONFIRMS E35** against
the strongest test it has faced so far: an issuer that not only excludes
leases from ITS OWN headline ratio, but uses that narrower figure to set
its leverage covenant and its capital-return guidance. E35 holds anyway,
because it is a rule about what net debt IS, not about what a covenant is
struck on.

---

### E58 — an ESEF/iXBRL package is a SECOND DOCUMENT: a tagged fact that agrees makes the field `cross_document`

**RULED 2026-08-27 by the owner, first application AUTO.L (commit
7156986). Written into this file on 2026-08-30 from that commit and from
`config/manual/AUTO.L.yaml`'s header, without change: four files (RMV.L,
RKT.L, IMB.L, APN.L) had come to cite it by number while it had no
heading here.**

**THE RULE (the owner's words, 2026-08-30).** An ESEF package is the same
annual report rendered as inline XBRL, so its tagged facts are an
independent second read of the same document. Where a hand-entered figure
agrees exactly with an `ix:nonFraction` fact for the same period, the
field takes **`verified_kind: cross_document`** (E40's second kind),
citing the package, the tag and its context on the field's `page:` line.
Where the tagged fact DIFFERS, the figure is left as entered, the
difference is noted inline, and nothing is resolved either way — **never
change a figure to make the two agree.** Where the package carries no tag
for a concept, the field keeps whatever verification it had (E59 is then
the route).

**SIGN IS A CONVENTION, NOT A DISCREPANCY.** iXBRL tags an outflow concept
(`PurchaseOf…ClassifiedAsInvestingActivities`, `IncomeTaxesPaid…`,
`PaymentsOfLeaseLiabilities…`) as a positive magnitude; the printed
statement and the manual file sign outflows negative. Same figure either
way. The 2026-08-27 commit left AUTO.L's two capex lines "noted inline,
value and status left untouched, not resolved either way"; the file's
header, updated after, records them as matching "on magnitude only after
reconciling a SIGN CONVENTION, not a discrepancy", and the owner's
instruction of 2026-08-30 settles it that way: reconciled by convention,
said once per name, and never reported as a disagreement.

**WHAT A PACKAGE DOES NOT CARRY.** AUTO.L's package defines only two units
in the whole document (GBP and GBP-per-share); no bare `xbrli:shares` unit
exists, so **no share COUNT is ever tagged** — only the monetary
IssuedCapital / TreasuryShares captions and the EPS ratios themselves —
and no current-borrowings concept was tagged at all. Every UK package read
since (RMV.L, RKT.L, IMB.L, APN.L) has the same shape. Such fields stay on
whatever verification they had; the three PDF-only share fields at AUTO.L
were checked by ARITHMETIC against other entered figures instead, which
E59 then promoted.

**APPLIED, AUTO.L, 2026-08-27.** The inline-XBRL report inside
`sources/AUTO.L_2026-FY_annual-financial-report_2026-06-08_xx_a0.zip`
(326 `ix:nonFraction` facts) was compared field by field. Nine fields
agreed exactly and took `cross_document` — revenue, operating_income,
net_income, total_assets, cash_and_equivalents,
financial_liabilities_noncurrent, lease_liabilities, operating_cash_flow,
diluted_eps — with capex_ppe and capex_intangibles agreeing on magnitude
under the sign convention above. Four had no tag (financial_liabilities_
current, shares_issued_period_end, treasury_shares_period_end,
diluted_weighted_average_shares) and stayed `same_page` until E59. Section
5 remained refused, on 16 of 19 UNVERIFIED figures, down from all of them.
**2026-08-30:** RMV.L (21 fields on the tag), RKT.L (18), IMB.L (20),
APN.L (16, under E58.1) — no tagged fact differed from an entered figure
on any of the four.

**WHICH EARLIER RULING THIS AMENDS.** **None.** An application of E40 §2's
`cross_document` kind: the package is the second document.

---

### E59 — an INTERNAL CROSS-CHECK is a second read: a figure that reconciles to a different, separately-prepared note of the same document takes `cross_document`

**RULED 2026-08-27 by the owner, first application AUTO.L (commit
0d973d8). Written into this file on 2026-08-30 from
`config/manual/AUTO.L.yaml`'s header, where the ruling was recorded, and
from that commit, without change.**

**THE RULE (the header's words).** Where a figure entered from one page
reconciles to a DIFFERENT note in the same document (a roll-forward, a
component sum, a segmental restatement) prepared separately from the
entered figure's own source, that is an independent confirmation and the
field takes **`verified_kind: cross_document`**, citing both pages — a
transcription error would break the tie, the same test cross-document
verification applies across two filings. **It does NOT extend to a figure
that merely appears twice on the same page.**

**WHAT COUNTS, from the first application.**

- **A component sum:** note 28's depreciation and amortisation lines
  summing to note 4's total; note 9's components summing to p.101's net
  finance costs; note 29's share-based payment components netting to note
  28's charge.
- **A roll-forward:** note 26's own roll-forwards reproducing note 25's
  treasury and employee-trust counts exactly; note 31's net-debt
  roll-forward restating p.105's lease payment.
- **A restatement in a separately-prepared note:** note 9 restating
  p.105's finance income received; note 31 restating note 21's zero
  current borrowings; note 28 restating p.105's cash generated from
  operations.
- **A reconciliation TO ROUNDING against a separately-prepared primary
  statement:** p.101's net_income / diluted_eps reproducing note 11's
  diluted count within the band both inputs' own printed rounding implies
  (30,500 shares off the stated count, 0.0035%) — *a reconciliation, not
  an exact digit match*; and note 11's exact opening count less note 25's
  own cancellation narrative reproducing the issued count to 568 shares,
  with the par-value check beside it. Both were the file's SHARE COUNT
  ARITHMETIC CHECKS, promoted from CHECK to `cross_document` by this
  ruling. E22 is untouched by that: a check confirms a stated figure and
  never supplies one — the printed count remains the entered figure
  regardless.

**WHAT DOES NOT, from the same application.** Three stayed UNVERIFIED
with the reason at the field: finance_costs_paid (note 30 gives £2.7m
against the cash flow's £2.8m — a real £0.1m gap between two figures each
already rounded to £0.1m, not one rounding absorbs); income_tax_paid (note
10's current tax CHARGE is an accrual, not the cash actually paid — the
numerical tie at this rounding may be coincidence, not a reconciliation);
proceeds_from_disposals_ppe (no reconciling note found at all — note 13's
disposal schedule does not decompose into proceeds cleanly). **A tie that
could be coincidence is not a reconciliation.**

**APPLIED.** AUTO.L 2026-08-27: eleven fields — section 5 refused on
three, down from fourteen. ZZ-B.ST 2026-08-30 (commit 93fe9e4): 50 of the
57 figures the basis reads, seven remaining (the E25/E36 zeros, the E71
lease sum, the share count); no ESEF package exists for a First North
issuer. RMV.L, RKT.L, IMB.L, APN.L 2026-08-30: every field the ESEF
package does not tag — the share counts (restated in a Directors' Report,
a Remuneration Report, a parent company's note, or another note's
roll-forward), the diluted averages (profit / diluted EPS to rounding, the
AUTO.L shape), the APM EPS and ratios at the issuer's printed precision
(E79), RKT.L's ex-lease borrowings and lease total (note 17's parts + note
19's split = the tagged inclusive captions), the D&A parts (notes summing
to the tagged combined line), the leverage APMs (the issuers' own APM
tables) — and, under E59.1, the caption zeros. One field was NOT reached
and stays UNVERIFIED with the reason on the field: IMB.L's employee-trust
3.0 million, stated once.

**WHICH EARLIER RULING THIS AMENDS.** **E40** — widens what
`cross_document` may stand on: a second document, or a separately-prepared
note of the same document. E22 is untouched, as above.

---

### E61 — where a US filer tags no net interest figure, gross interest expense may serve as the E34 add-back, marked as a proxy

**RULED 2026-08-27 by the owner, first application CTSH. Amends E34.1.**

**THE RULE.** Where `interest_in_ocf: yes` and the filer tags NEITHER
`InterestIncomeExpenseNonoperatingNet` (E34.1's net) NOR a tagged
interest-RECEIVED figure, **the add-back is the tagged interest expense
ALONE** (`InterestExpenseNonoperating`, the schema's `finance_costs_period`).
It is stored as `interest_source: interest_expense_only` and printed
beside FCF0 as **"proxy — interest income not tagged, add-back overstated
by the unrecorded income."** The overstatement is BOUNDED and the bound is
reported as a percentage of FCF0 in the run record, every time the proxy
fires — the same discipline E34's own pre-tax bias gets.

**THE DIRECTION OF THE ERROR IT REMOVES, AND THE ONE IT ACCEPTS.** Before
E61, a US filer with no net-interest tag and no gross-interest tag either
was DATA MISSING for FCF0 outright — correct, but it is also DATA MISSING
for a filer that tags the GROSS expense and simply never tags the net,
which is a real and common shape (CTSH: `InterestExpenseNonoperating` is
tagged every year FY2022-2025, `InterestIncomeExpenseNonoperatingNet` is
tagged NEVER). Refusing FCF0 outright in that shape throws away a
figure that is bounded, not unbounded: gross interest expense is always
GREATER THAN OR EQUAL TO the true net, because interest income is never
negative, so adding back the gross figure can only OVERSTATE FCF0, never
understate it, and by no more than the unrecorded interest income itself.
**That is a one-sided, bounded error, not a guess** — the same shape E34's
own pre-tax add-back already accepted for the tax leg, stated here for the
income leg instead.

**CTSH, MEASURED, by the store's own arithmetic (`vss.valuation.free_cash_flow_zero`).**
FY2025: `finance_costs_period` (`InterestExpenseNonoperating`) $37m —
NOT `finance_costs_paid` (`InterestPaidNet`, $36m, a different tagged
figure one dollar off and not this leg — E34.1's leg is the EXPENSE, not
the cash paid). `InterestIncomeExpenseNonoperatingNet` untagged in every
year on file. FCF0 = operating cash flow $2,883m + capex ($288m) − sbc
$181m + $37m = **$2,451m**. The $37m add-back is 1.5% of that FCF0 —
**the proxy's MAXIMUM possible error, and the true error is smaller than
that, because interest income is positive and the true net add-back is
somewhere below $37m, not above it.**

**WHAT E61 DOES NOT DO.** It does not touch IFRS filers, which state both
halves of the cash pair and never reach E34.1 or this ruling at all. It
does not touch a US filer that tags neither the net nor the gross expense
— that filer is still DATA MISSING for FCF0, on E34.1's own terms,
because there is nothing bounded left to add back. And it does not
change the SIGN convention: `InterestExpenseNonoperating` is a cost by
construction and is always ADDED, never removed — unlike E34.1's net,
which is signed and can go the other way for a filer earning more
interest than it pays.

**WHICH EARLIER RULING THIS AMENDS.** **E34.1**, by settling the sub-case
its own rule left as an outright refusal: "a filer whose income statement
prints no net" is not one shape but two — no net AND no gross (still
refused), or no net BUT a tagged gross (now a bounded proxy). E34 and
E34.1's other terms are unchanged: `interest_in_ocf` is still required,
the add-back is still pre-tax, and net debt is still subtracted once,
after discounting, regardless of which of the three shapes supplied FCF0's
interest leg.

---

### E62 — pension_deficit is every defined-benefit obligation the issuer discloses, not only the one captioned "pension"

**RULED 2026-08-27 by the owner, first application CTSH.**

**THE RULE.** Where a filer presents MORE THAN ONE defined-benefit plan
under the same note and the same accounting treatment, `pension_deficit`
is their SUM. The field is E35.1's "recognised net defined-benefit
LIABILITY" — the plan's NAME does not decide membership, the OBLIGATION
does. A statutory lump-sum plan captioned "gratuity", "termination
indemnity" or "long-service award" is a defined-benefit obligation on the
issuer's own accounting treatment whether or not the word "pension"
appears in its caption.

**CTSH, AS RULED.** FY2025 10-K, Note 15 — Employee Benefits presents TWO
defined-benefit plans, both statutory, both under this one note:

| Plan | Basis | 2025-12-31 | Tag |
|---|---|---:|---|
| Defined Benefit Pension Plans (primarily Switzerland) | *"the net liability recognized on the balance sheet for our pension plans was $55 million"* | $55m | `us-gaap:DefinedBenefitPensionPlanLiabilitiesNoncurrent` (a tag-map gap this session found and fixed, not a true absence — see the CTSH tag-map bug fix, same date) |
| Other Defined Benefit Plans — India gratuity | *"the amount accrued under the gratuity plan was $205 million... which is net of fund assets of $250 million"* | $205m | none — no us-gaap element carries this figure anywhere in the filer's tagged facts; it sits inside "Other noncurrent liabilities" ($847m) with no reconciling note |

`pension_deficit` FY2025 = 55 + 205 = **$260m**, entered `verified_kind:
same_page` — the WEAKER of the two components' provenance governs the
combined claim (E40's own logic, applied to a sum rather than a single
figure): the $55m leg is `tagged`, the $205m leg is a single read of the
10-K's own sentence with no tag and no reconciling disclosure to check it
against, and a reader of the combined $260m is entitled to know it is only
as strong as its weakest addend.

**THE ONE-OFF, RECORDED SO A FUTURE READ DOES NOT MISTAKE IT.** The India
leg was $80m at 2024-12-31 and is $205m at 2025-12-31 — a $125m jump — but
the note states the mechanism directly: *"During the fourth quarter of
2025, the Labor Code reforms implemented by the Government of India
caused our gratuity liability for prior services to increase by $147
million, which we recognized as a component of OTHER COMPREHENSIVE
INCOME."* A regulatory reform recognized through OCI is not an operating
deterioration, and a FY2026 comparison that reads FY2025's $260m against a
smaller FY2026 figure as "net debt improved" without knowing this would
be reading a base effect as an operating fact. The entry says so inline.

**WHAT E62 DOES NOT DO.** It does not reach a plan the issuer presents
under a DIFFERENT note or a different accounting treatment — a
share-based long-service award measured at fair value under a
compensation note is not this field regardless of its name, and neither
is a termination-indemnity ACCRUAL that the issuer itself does not
account for as a defined-benefit obligation (undiscounted, no actuarial
assumptions, no OCI remeasurement). The test is the accounting TREATMENT
the note describes, not the presence of a second dollar figure near the
word "benefit."

**WHICH EARLIER RULING THIS AMENDS.** **E35.1**, by settling a scope
question its own text left open: E35.1 named "the recognised net
defined-benefit LIABILITY" and every prior application (AUTO.L, a stated
zero; Lindab, SAP) happened to have exactly one such plan, so "the" never
had to mean "the sum of." CTSH is the first filer on the books with two,
and E62 settles that the field was always the OBLIGATION's sum, not the
CAPTION's singular.

---

### E63 — the distance from the 52-week LOW is a FIELD: reported on every row, applied by nothing

**RULED 2026-08-28 by the owner, after CTSH. Written 2026-08-29, before the
code.**

**THE GAP.** Gate 1's band measures how far a name has fallen from its own
52-week closing high. It cannot tell a name that fell and STAYED DOWN from
one that fell and has since RECOVERED — both read the same drawdown, and
the drawdown is the only price fact the band sees. The owner's two cases:

| Name | Read | Below the 52-week high | Above its own 52-week low |
|---|---|---:|---|
| CTSH | 2026-08-27 | 26.5% | 64.7% above the 2026-06-30 trough of $38.73 |
| AUTO.L | 2026-08-27 | 34% | roughly 28% above the May low |

Both had already turned before the screener saw them, and the drawdown
alone did not say so. A name approaching its MBP is worth knowing whether
it is still falling.

**THE MEASURE.** `pct_above_52w_low` = (close − 52-week closing low) /
52-week closing low, on the SAME window and the SAME coverage rule the
52-week high already uses — `metrics.LOOKBACK_DAYS` (365 calendar days,
closes only, never the intraday low) and `metrics.covers_52_weeks` (52
weeks plus five trading days of date coverage, the REVIEW-4 bar). `low_52w`
and `low_52w_date` are recorded beside it, as the high and its date are
already recorded (E11/E12); on a tied low the LATEST session is the date,
for the same reason the high takes its latest print — it is the session
after which any recovery is counted. Below the coverage bar all three are
DATA MISSING together, **never a partial reading** — a low struck off a
shorter window is a HIGHER low and a SMALLER distance, the same wrong
direction the high's bar exists to refuse.

**IT IS A FIELD, NOT A FILTER.** It travels under the standing rule that
already governs RSI and the SMAs (`vss/screen.py`, "RSI AND SMA50 ARE
FIELDS. THEY ARE NEVER FILTERS."): carried on every candidate row, printed
in the filter-1 report and the rank report, written to
`filter1-candidates.csv` and `ranking.csv`, and read by no filter and by
nothing in the ranking key. `vss run` prints it on the watchlist report
beside the drawdown, names it for HELD and WATCH-PRICED entries, which is
where it matters most, and writes all three to the run store
(`run_metrics.low_52w`, `low_52w_date`, `pct_above_52w_low`; an older
database gains the columns on its next connect). No threshold is implemented anywhere. A test
holds the line the way the RSI/SMA test does.

**WHY REPORTED AND NOT APPLIED.** The intent is to SEE, for a month,
whether the head of the ranking is systematically made of names that have
already recovered. Whether the measure becomes a filter, and at what
threshold, is a decision to be made on that evidence and not before —
recorded as **B41**, open. Nothing in E63 decides it, and no reading of a
single run may be placed on it.

**WHICH EARLIER RULINGS THIS TOUCHES.** None are amended. E11/E12 (the
high and its date, frozen at entry) are unchanged — E63 records the OTHER
end of the same window and freezes nothing. The REVIEW-4 coverage bar is
reused, not restated: one constant, one function, both ends of the window.

**FIRST MEASUREMENT — the record starts here. 2026-08-26 snapshot, settled
closes, the chain re-run 2026-08-29 with the run's own exchange rates
replayed (`ranking-manifest-pre-e63-2026-08-29.json`); the ordering
reproduced exactly on every pre-existing column, 252 rows.** The head-20
and the five PIPELINE names written 2026-08-27, which on this run are
ranks 1 to 5. CTSH reads 28.4% / 60.3% here against the 26.5% / 64.7% in
the ruling above because this is the prior session's close.

| # | ticker | drawdown from 52w high | above 52w low | low | low date |
|---:|---|---:|---:|---:|---|
| 1 | AUTO.L | 34.1% | 26.2% | 427.20 | 2026-05-28 |
| 2 | NHY.OL | 22.3% | 44.1% | 64.36 | 2025-09-02 |
| 3 | RMV.L | 33.2% | 26.0% | 404.00 | 2026-05-15 |
| 4 | NVR | 25.5% | 14.5% | 5563.62 | 2026-05-15 |
| 5 | ZZ-B.ST | 27.3% | 30.2% | 112.40 | 2025-11-05 |
| 6 | CTSH | 28.4% | 60.3% | 38.73 | 2026-06-30 |
| 7 | LUG.ST | 15.9% | 39.3% | 509.60 | 2026-07-16 |
| 8 | KAR.ST | 33.6% | 29.7% | 62.00 | 2026-06-18 |
| 9 | WKL.AS | 40.7% | 23.7% | 55.82 | 2026-06-25 |
| 10 | LII | 32.2% | 1.2% | 389.06 | 2026-08-25 |
| 11 | LOGN.SW | 21.0% | 20.0% | 66.64 | 2026-01-30 |
| 12 | ACN | 37.1% | 45.8% | 124.44 | 2026-06-30 |
| 13 | RVRC.ST | 23.5% | 20.2% | 45.12 | 2025-09-02 |
| 14 | AOS | 22.4% | 12.0% | 55.78 | 2026-06-01 |
| 15 | AAF.L | 19.2% | 57.8% | 215.20 | 2025-09-03 |
| 16 | EXE | 21.4% | 11.1% | 86.95 | 2026-07-20 |
| 17 | GDDY | 35.8% | 27.4% | 74.99 | 2026-06-22 |
| 18 | ULTA | 23.2% | 20.5% | 450.75 | 2026-06-17 |
| 19 | HOC.L | 18.5% | 141.7% | 272.60 | 2025-08-28 |
| 20 | IT | 26.9% | 53.5% | 125.73 | 2026-06-22 |

PIPELINE: AUTO.L (rank 1) 34.1% / 26.2% above the 2026-05-28 low; NHY.OL
(2) 22.3% / 44.1%, 2025-09-02; RMV.L (3) 33.2% / 26.0%, 2026-05-15; NVR (4)
25.5% / 14.5%, 2026-05-15; ZZ-B.ST (5) 27.3% / 30.2%, 2025-11-05.

**One line, and no conclusion from one run:** 15 of the head-20 sit more
than 20% above their own 52-week closing low (the five that do not: NVR
14.5%, LII 1.2%, AOS 12.0%, EXE 11.1%, LOGN.SW 20.0% exactly); 11 of the
20 lows were set on or after 2026-06-01. The next runs add to this table;
B41 is decided on the month, not on this row.

---

### B41 — whether E63's distance from the 52-week low becomes a filter, and at what threshold

**RAISED 2026-08-28 by E63, which expressly does not decide it. DECIDED
2026-09-28 by E127: no threshold is drawn on the low. What the month
showed was answered by a different measure, the 12-month return.**

E63 reports `pct_above_52w_low` on every candidate row so that a month of
runs can show whether the head of the ranking is systematically made of
names that fell and have since recovered. If it is, the question is
whether Gate 1 should also ask how far a name sits above its own low —
and if so, at what distance, and whether that is a rejection or a flag.
The decision is to be made on the recorded evidence, not before, and not
on one run. Until then the field decides nothing, and a threshold written
into any module is a breach of E63.

---

### B42 — finance lease liabilities have no leg in E35's net debt, and operating leases do

**RAISED 2026-08-29 by the LII tag-map work. OPEN — not decided.**

**The inconsistency, stated.** E35 rules that *leases are in net debt,
always*, and E14 rules that the two borrowing fields *exclude* lease
liabilities while `lease_liabilities` holds the lease portion. Under the
us-gaap map, `lease_liabilities` reads `OperatingLeaseLiability` — the
OPERATING lease total — and nothing reads a FINANCE lease. So a finance
lease is in neither field: E14 keeps it out of the borrowing fields by
definition, and the lease field never asks for it. The ruling says every
lease is in net debt; the map carries the operating ones only.

**LII, measured, at 2025-12-31 (10-K `0001069202-26-000028`).**
`FinanceLeaseLiability` **68.9m** (current 18.3m, non-current 50.6m) sits
beside `OperatingLeaseLiability` 382.3m. The filer folds it into
`LongTermDebtAndCapitalLeaseObligations` 1,144.1m and
`DebtAndCapitalLeaseObligations` 1,388.4m — the debt totals — and the map
reads neither of those either (they include the lease, so they are not
E14's borrowings-alone). The map's `financial_liabilities_current` for LII
is `LongTermDebtCurrent` 18.3m, which **is** the current finance-lease
liability under another caption: the one finance-lease leg the file does
carry is carried as a borrowing, by accident of the filer's tagging.

**What a ruling has to settle.** Whether `lease_liabilities` means ALL
lease liabilities (add `FinanceLeaseLiability` as a second stated figure —
which is a sum of two captions the issuer never totals, E26) or whether a
finance lease is a borrowing (it is presented inside debt by this filer,
and ASC 842 treats it as debt-like) and belongs in the borrowing fields —
against E14's words. Either way the map changes how net debt is computed,
so it is not an alias fix. **Nothing is implemented.**

---

### B43 — asset retirement obligations have no leg in net debt

**RAISED 2026-08-29 by the EXE file. OPEN — not decided.**

E35 names its legs — borrowings, leases, the pension deficit — and an
asset retirement obligation is none of them. For an E&P it is a
debt-like obligation of a size that moves the answer: **Expand Energy tags
`AssetRetirementObligation` 724m at 2025-12-31** (688m non-current, 36m
current; 10-K `0000895126-26-000011`) against `LongTermDebtNoncurrent`
5,009m — **14.5% of its borrowings**, and 36% of its FY2025 FCF0 of
2,028m. It is discounted, accreted through the income statement (30m in
FY2025), and settled in cash over the life of the wells.

**What a ruling has to settle.** Whether E35's list is closed, or whether a
recognised, discounted, cash-settled obligation the issuer presents as a
liability belongs in the bridge for the sectors that carry one — and if
so, whether the current portion, the total, or a tax-effected figure. It
is an E35 amendment, not an alias. **Nothing is implemented**; the EXE
file carries no ARO field and its net debt, once its pension leg is
entered, will be 724m lighter than the obligations the filer states.

---

### E65 — finance lease liabilities are in net debt, alongside operating leases

**RULED 2026-08-29 by the owner, on B42. Amends E35 and E14. Written before
the code.**

**THE RULE.** E35 says leases are in net debt, always. A finance lease is
the same obligation as an operating lease under a different accounting
treatment, and the us-gaap map read only `OperatingLeaseLiability`, so a
finance lease fell in no leg (B42). **`lease_liabilities` is the sum of
the operating and the finance lease liabilities where both are tagged,
each stated separately in the field's provenance so the composition is
visible.** Where only operating leases are tagged the field is the
operating total, as before; the finance leg's absence is a fact about the
filer's tagging and is named in the report.

**THE FINANCE LIABILITY ITSELF, as read.** `FinanceLeaseLiability` (the
stated total) is the figure. Where the filer tags no total but tags BOTH
`FinanceLeaseLiabilityCurrent` and `FinanceLeaseLiabilityNoncurrent`, the
two stated parts are added on E66's precedence — a stated total wins, two
stated parts are added with both named, one part alone is not the
liability — and the provenance names both (CTSH: 10m + 12m = 22m at
2025-12-31, no total tagged). One part alone leaves the finance leg DATA
MISSING, and `lease_liabilities` with it -- a liability known to exist and
impossible to size is refused, not understated -- and the report says
which part is present.

**NO DOUBLE COUNT, and how it is proved rather than assumed.** A finance
lease can already sit inside a borrowing leg — E67 reads a combined
borrowings-and-finance-lease caption whole, and a filer can tag an
"ex-lease" current element inclusive of its lease. **E65 adds only the
finance-lease liability not already captured in a borrowing leg:**
`added = finance lease liability − (lease inside the current leg) −
(lease inside the noncurrent leg)`, each term named with its tag in the
provenance, and the field is the operating total plus that residual. A
residual below zero is an inconsistency between the filer's own captions
and REFUSES the field rather than clamping.

**LII, at 2025-12-31 (10-K `0001069202-26-000028`).** `FinanceLeaseLiability`
68.9m (current 18.3m, non-current 50.6m). Its current portion 18.3m is
tagged as `LongTermDebtCurrent` — and `LongTermDebtAndCapitalLeaseObligations
Current`, the inclusive element, is tagged at the SAME 18.3m: an "ex-lease"
element equal to its "incl-lease" twin was tagged inclusive, and
`LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths` is 0. So
the current leg holds 18.3m of finance lease; the non-current leg (E67,
`LongTermDebtAndCapitalLeaseObligations` 1,144.1m) holds 50.6m. **Added
by E65: 68.9 − 18.3 − 50.6 = 0.0. `lease_liabilities` = 382.3m operating +
0.0.** Every lease dollar is in exactly one leg, and the proof is the
filer's own total: current 244.3m (E66) + non-current 1,144.1m = 1,388.4m =
`DebtAndCapitalLeaseObligations`, the line the filer prints.

**WHAT E65 DOES NOT DO.** It does not reach the IFRS map: IFRS 16 has one
lessee model and `LeaseLiabilities` is already every lease. It does not
change E14's words — the borrowing fields still exclude leases — except
where E67 reads a combined caption whole and says how much lease is inside.

---

### E66 — two stated borrowing captions are added, not chosen between

**RULED 2026-08-29 by the owner. Amends the one-tag-per-field convention
for `financial_liabilities_current` only. Written before the code.**

**THE RULE.** Where a filer tags more than one current-borrowing element
and neither is a subtotal of the other, **the field is their sum, with
every component and its tag listed in the provenance.** This is not E22's
forbidden derivation: both figures are stated, and the alternative —
reading one and silently dropping the other — understates debt. It
applies only to captions the filer presents as separate balance-sheet
lines.

**PRECEDENCE — a subtotal wins and its components are memo.** Read in
this order at the year end:

1. `DebtCurrent` — the taxonomy's subtotal of every current borrowing.
   Where tagged it is the field, and the components tagged beside it are
   named as memo and never added to it.
2. Otherwise the sum of the distinct captions: `LongTermDebtCurrent`
   (current maturities) plus ONE of `ShortTermBorrowings` or
   `CommercialPaper` — `ShortTermBorrowings` is by the element's own
   definition a subtotal that includes commercial paper, so where both
   are tagged the paper is memo inside it. One caption alone is the field,
   as before.

**LII, at 2025-12-31.** `LongTermDebtCurrent` 18.3m + `CommercialPaper`
226.0m = **244.3m** (no `DebtCurrent`, no `ShortTermBorrowings` at the year
end). Before: 18.3m, the paper unread. **NKE, at 2026-05-31:** the filer
tags `LongTermDebtCurrent` 2,000m and nothing else — its `ShortTermBorrowings`
is tagged at 2025-05-31 and at every quarter end through 2026-02-28 but
not at 2026-05-31, and its `CommercialPaper` element was last tagged at
2015-05-31. **Before and after: 2,000m at the basis; unchanged.** At the
FY2025 history year (2025-05-31) the sum now includes the short-term
borrowings beside the zero current maturity.

**WHAT E66 DOES NOT DO.** It does not reach the non-current leg (one
element, `LongTermDebtNoncurrent`, or E67's combined caption) and it does
not reach the IFRS map, whose first alias is already a stated subtotal
(`CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings`).

---

### E67 — a combined borrowings-and-finance-leases caption may be read whole once E65 puts leases in

**RULED 2026-08-29 by the owner. Written before the code.**

**THE RULE.** Where a filer tags no borrowings-only non-current element
and presents borrowings and finance leases as one line
(`LongTermDebtAndCapitalLeaseObligations`), **that line is the non-current
borrowing leg, and the finance-lease component inside it is NOT added
again by E65.** The provenance names the combined element and states the
lease amount inside it. **The lease component must be STATED by the
filer** (`FinanceLeaseLiabilityNoncurrent` tagged at the same year end);
where the combined line is tagged and the lease inside it is not, the
leg is REFUSED — DATA MISSING, the caption named — rather than guessed.
The same reading applies to the current caption
(`LongTermDebtAndCapitalLeaseObligationsCurrent` with
`FinanceLeaseLiabilityCurrent`) where no `LongTermDebtCurrent` is tagged,
and to a `LongTermDebtCurrent` tagged EQUAL to the inclusive current
caption, which is the filer stating the ex-lease element inclusive.

**LII, the arithmetic, explicitly.**

| leg | element | amount | finance lease inside |
|---|---|---:|---:|
| current | `LongTermDebtCurrent` 18.3 (= inclusive twin 18.3 = `FinanceLeaseLiabilityCurrent` 18.3) + `CommercialPaper` 226.0 (E66) | 244.3 | 18.3 |
| non-current | `LongTermDebtAndCapitalLeaseObligations` (E67) | 1,144.1 | 50.6 (`FinanceLeaseLiabilityNoncurrent`) |
| leases | `OperatingLeaseLiability` 382.3 + (`FinanceLeaseLiability` 68.9 − 18.3 − 50.6 = 0.0) (E65) | 382.3 | — |

Finance lease 68.9 = 18.3 + 50.6, both already inside borrowing legs, so
E65 adds nothing; borrowings 244.3 + 1,144.1 = 1,388.4 =
`DebtAndCapitalLeaseObligations` as printed. **No dollar is counted twice
and no dollar is dropped.** Before E65–E67 the non-current leg was DATA
MISSING and net debt could not form; after, every leg but E68's forms.

---

### E68 — asset retirement obligations are in net debt

**RULED 2026-08-29 by the owner, on B43. Amends E35. Written before the
code.**

**THE RULE.** A legally required future cash outflow to decommission
assets is debt in substance: it is not optional, it is measured and
discounted, and for extractive and utility businesses it is material.
**New leg `asset_retirement_obligation` in E35's net debt**, read from
`us-gaap:AssetRetirementObligation` — the stated total — with the
non-current and current elements named as memo where they are tagged
beside it. Where the filer tags no total but BOTH
`AssetRetirementObligationsNoncurrent` and `AssetRetirementObligationCurrent`,
the two stated parts are added on E66's precedence with both named. **A
lone non-current element is not the obligation** — the current portion
sits untagged inside accrued liabilities — and leaves the leg DATA
MISSING with the part named (DECK: `AssetRetirementObligationsNoncurrent`
36.8m at 2026-03-31, no total, no current element). **DATA MISSING where
untagged, never zero:** a filer with no such obligation says so, and the
sentence is entered on E25's `note` form with its page, as E35.1 settled
for the pension leg. For the IFRS map the leg reads
`ProvisionForDecommissioningRestorationAndRehabilitationCosts`; no filer
on file tags it, so it has never supplied a figure.

**EXE, at 2025-12-31 (10-K `0000895126-26-000011`).** `AssetRetirementObligation`
**724m** (non-current 688m, current 36m as memo) — 14.5% of its 5,009m of
borrowings. Net debt ex-pension moves from 4,492m to 5,216m.

**THE CONSEQUENCE, STATED ONCE.** Every manual file that carries no
asset-retirement figure — which is every file but EXE's — has net debt
DATA MISSING on this leg from this ruling on, exactly as E35.1 did for the
pension leg. That includes names whose fair value has already been
struck (AUTO.L, LIAB.ST, SAP.DE, CTSH): the leg does not MOVE those values
— it is absent, not a number — but their bridges are incomplete under
this rule until a hand entry with the issuer's own statement closes the
leg. Nothing is re-struck here.

---

### E68.1 — a filer with no decommissioning obligation takes a caption-based zero

**RULED 2026-08-29 by the owner. Amends E68. Written before the code.**

**THE RULE.** Where an issuer's balance sheet presents no asset retirement
or decommissioning provision, `asset_retirement_obligation` is **zero with
`zero_basis: caption`**, not DATA MISSING — the same form E35.1 settled for
the pension leg. Absence of the caption in a business that owns nothing
requiring decommissioning is evidence, not a gap. The page names the
balance sheet and the provisions or other-liabilities note that were read.

**WHERE ABSENCE IS NOT EVIDENCE.** Where the business plausibly has such an
obligation and the caption is absent, the leg is REFUSED rather than
assumed: **extractive, utility, mining, shipping, chemical and heavy
industrial filers get DATA MISSING until the figure is read by hand from
the filing** (E69). A caption that is absent from the face of the balance
sheet but present inside a provisions note is a stated figure, not an
absence, and is entered under E69.

**THE APPLICATIONS are recorded beneath this entry, each with its balance
sheet or note.**


**APPLIED 2026-08-29, each against its balance sheet or note.**

| Name | Read | Result |
|---|---|---|
| **AUTO.L** | AR 2026 balance sheet p.103 presents `Provisions 22` (non-current 3.7, current 1.2); **note 22 Provisions, p.122, carries a `Dilapidations provision` column: 1.6 at 31 March 2025, utilised (1.0), *"Recognised under IFRS 16 3.6"*, released (0.5), **3.7 at 31 March 2026**.** Note 28 p.126 corroborates: *"Dilapidation provision release (0.5)"*. | **NOT a zero.** A lessee's obligation to restore leased premises, recognised with the right-of-use asset, is a decommissioning-type provision inside E68's leg and is a stated figure — entered under **E69** as `asset_retirement_obligation` **3.7** (GBP m, `same_page`). Net debt 187.8 → **191.5**. *Judgement to confirm: that E68's "asset retirement or decommissioning provision" includes a lessee's dilapidations provision (ASC 410-20 and IAS 37 both treat it so).* |
| **CTSH** | 10-K `0001058290-26-000008`, Consolidated Statements of Financial Position: no asset-retirement or decommissioning caption; neither term appears anywhere in the filing. IT services. | **Zero, `caption`.** `Other noncurrent liabilities` $847m is a caption with room (E25) and is named as such. Net debt completes. |
| **LIAB.ST** | AR 2025 statement of financial position p.74: `Provisions for pensions and similar obligations` (note 26) and `Other provisions` (note 27); note 27 p.115 splits SEK 248m into restructuring 167, warranty 5 and *"Other provisions amounted to SEK 76 m (10)"*, undescribed. No decommissioning, restoration, dismantling or environmental provision anywhere in the report. Ventilation and building products. | **Zero, `caption`**, on the FY2025 annual entry (E41 reaches it inside the TTM window). The undescribed `Other 76` is a caption with room and is named. Net debt completes at **4,536**. |
| **AOS** | 10-K `0000091142-26-000008`, Consolidated Balance Sheets: no asset-retirement or decommissioning caption; neither term anywhere in the filing. Water heaters and boilers. The income-tax note lists a deferred tax asset on *"Environmental liabilities 1.3"* — a remediation accrual (ASC 410-30) inside `Accrued liabilities`/`Other liabilities`. | **Zero, `caption`.** The remediation accrual is a different liability from an asset retirement obligation and is outside E68 as ruled; named, not included. Net debt completes at **35.8m**. |
| **LII** | 10-K `0001069202-26-000028`, Consolidated Balance Sheets: no asset-retirement or decommissioning caption; neither term anywhere in the filing. Note 5 Commitments and Contingencies: *"Total environmental accruals are included in Accrued expenses and Other liabilities"*, unquantified; the income statement charged *"Environmental liabilities and special litigation charges 10.9"* in 2025 (remediation at facilities, asbestos settlements). HVAC manufacturing — heavy industrial. | **REFUSED — DATA MISSING.** The balance sheet carries no such caption, but the filer carries environmental remediation accruals of unstated size inside captions with room, and E68.1 puts heavy industrial on the refuse-until-read list. Whether a remediation accrual belongs in E68's leg is not decided here; the accruals are named for that ruling. |
| **CPRT** (2026-10-05) | 10-K `0001193125-26-405731` filed 2026-09-29, Consolidated Balance Sheets at 2026-07-31: no asset-retirement or decommissioning caption; 'asset retirement' and 'decommission' appear nowhere in the filing. Item 1A: *"We have incurred expenses for environmental remediation in the past"*, and insurance is bought for *"acquired facilities with known environmental risks"*. Vehicle salvage auctions on owned and leased yards -- not on E69's refuse-until-read list. | **Zero, `caption`** (owner, 2026-10-05: *"It's expensed as it occurs and there's no provision. It's a risk, not a liability on the balance sheet."*). The AOS reading: remediation is a different liability from an ARO and is named, not included. |

---

### E69 — a stated figure the filer does not tag may be hand-read from the filing

**RULED 2026-08-29 by the owner. Written before the code.**

**THE RULE.** Where a section-5 field is DATA MISSING because no XBRL
element carries it, but the figure is printed in the filing itself, **it is
entered by hand with the item or note reference as provenance and
`verified_kind: same_page`.** Absence of a tag is not absence of the
figure — that was the CTSH pension case (E62) and it recurs. **The hand
read must quote the caption verbatim.** A figure derived from other
figures is still refused under E22; a subtraction of two stated figures at
one period end remains permitted under E18.

**WHAT IT DOES NOT OPEN.** It does not let a reader net, sum, scale or
infer: the figure entered is the figure printed, at the caption printed.
It does not let E61's gross-only proxy stand in where the filing states
interest income somewhere the tags do not reach — the stated figure is
read, and where the filing states only a net, the net is entered as
`net_finance_costs` and said so; where interest income genuinely appears
nowhere in the filing, the reader says so and stops.

**THE APPLICATIONS are recorded beneath this entry.**

**APPLIED 2026-08-29 — AOS, 10-K `0000091142-26-000008` (filed 2026-02-10).**

- **Interest expense — entered.** Item 8, Consolidated Statements of
  Earnings, year ended December 31, 2025: *"Interest expense | 13.5"*
  (dollars in millions); the same line in Item 7, Results of Operations.
  The filer tags it as `us-gaap:InterestExpense`, an element the map does
  not read because it carries a NET line for Lennox and a GROSS line here.
  Entered as `finance_costs_period` **13,500,000**, `same_page`, caption
  quoted.
- **Interest income — appears nowhere in the filing as a figure.** The
  statement of earnings prints *"Other income, net | (0.6)"*, which Item 7
  describes as foreign-currency translation and interest income together
  (*"lower foreign currency translation losses compared to the prior year
  and lower interest income from lower average cash balances"*), and the
  segment note says only that *"Other expense (income), net consists
  primarily of interest income"*. That is a composite, not a net finance
  figure: it is NOT entered as `net_finance_costs`, and no E18 pair forms.
- **FCF0 stays refused on the interest leg**, and E61's gross-only proxy is
  NOT applied, per this ruling's own last sentence. Basis-1 FCF 546.0m and
  net debt 35.8m are computable; a fair value is not.

---

### E68.2 — an unquantified remediation accrual is a zero with the accrual named

**RULED 2026-08-30 by the owner. Amends E68.1. Written before the code.**

**THE RULE.** Where a filer discloses environmental remediation or similar
obligations but states no balance-sheet amount for them — the liability
sitting inside a caption with room — `asset_retirement_obligation` takes
**zero with `zero_basis: caption`, and the disclosure is named on the
field** so the omission is visible rather than silent. The alternative,
refusing the whole bridge, is the wrong proportion: it blocks a fair value
over a figure the issuer itself does not consider material enough to
state. This amends E68.1's refuse-until-read rule **for the case where the
read has happened and found no figure.** Where an amount IS stated, it is
entered under E69 as normal.

**APPLIED 2026-08-30 — LII, 10-K `0001069202-26-000028` (filed 2026-02-17).**
The read: the Consolidated Balance Sheets carry no asset-retirement or
decommissioning caption; Note 5, Commitments and Contingencies —
*Environmental*: *"Total environmental accruals are included in Accrued
expenses and Other liabilities on the accompanying Consolidated Balance
Sheets"*, unquantified, with *"we do not believe that any future
remediation related to those facilities will be material to our results
of operations"*; the income statement charged *"Environmental liabilities
and special litigation charges 10.9"* in 2025 — *"estimated remediation
costs at some of our facilities and outstanding legal settlements
including asbestos"* — sized as a charge, not as a balance. **Zero,
`caption`, with Note 5 and the 2025 charge named on the field.** Net debt:
244.3 + 1,144.1 + 382.3 + 18.7 + 0 − 34.2 = **1,755.2m; the bridge
completes.**

---

### E61.1 — the interest-expense-only proxy extends to a filer that states no interest income anywhere

**RULED 2026-08-30 by the owner. Amends E61, which was written against a
specific tag. Written before the code.**

**THE RULE.** Where `interest_in_ocf` is yes, an interest expense is
stated, and **no interest income figure appears in the filing under any
element or in any note** — as distinct from appearing under an element the
map does not read — the add-back is the stated interest expense alone,
with `interest_source: interest_expense_only` and the bound printed as a
percentage of FCF0. **The distinction that matters is between "the filer
does not state it" and "we did not look in the right place": E61.1
applies only after the filing has been read and the figure is genuinely
absent.** The tool never fires it on its own — E61's automatic proxy stays
on `InterestExpenseNonoperating` — and the file records the read.

**APPLIED 2026-08-30 — AOS, 10-K `0000091142-26-000008`.** The read (E69,
2026-08-29): interest expense **13.5m** is stated on the Consolidated
Statements of Earnings (*"Interest expense | 13.5"*); interest income
appears nowhere as a figure — *"Other income, net | (0.6)"* is, per Item 7,
foreign-currency translation and interest income together (*"lower foreign
currency translation losses … and lower interest income from lower average
cash balances"*), and the segment note says only that it *"consists
primarily of interest income"*; no note states the amount. Not a net
finance figure, so not `net_finance_costs`. **`interest_source:
interest_expense_only` on the file, the read recorded.** FCF0 = OCF 616.8
− capex 70.8 − SBC 13.8 + 13.5 = **545.7m; the bound is 13.5 / 545.7 =
2.5% of FCF0**, the most the unrecorded interest income could overstate
it by.

**NOT applied to LII**: its pair resolves under E18 (46.4 − 5.5 = 40.9) and
needs no proxy.

---

### E70 — a lease is counted once, in net debt, never also in the flow

**RULED 2026-08-30 by the owner. Amends E33 for the flow; E35 and E65 stand.
Written before the code.**

**THE ERROR.** E33 makes FCF basis 2 the default for a retailer, which
deducts lease payments from the flow. E35 and E65 put the lease liability
in net debt. Together they charge the same obligation twice — once as a
payment out of the flow being discounted, once as a claim subtracted from
the discounted value. This is the same class of error E34 corrected for
interest, and it is measured: AD.AS's market-implied perpetual growth
reads **1.34% on borrowings-only net debt against 5.29% on the 14.7bn
lease-inclusive figure** (reports/AD-AS-INVESTIGATION-2026-08-30.md §7).

**THE RULE.** Leases belong in net debt (E35, E65 stand). **FCF0 therefore
does not deduct the lease principal payment.** Where basis 2 or any other
basis subtracts it — and under ASC 842 a filer's OPERATING cash flow
already bears its operating lease payments, so the deduction is inside
`operating_cash_flow` before any basis is chosen — **the amount is added
back, recorded on the run record as `lease_principal_added_back` with the
leg named**, exactly as E34's interest add-back is recorded. Lease
interest follows the interest rule already in force for the filer (E34,
E34.1, E61, E61.1), not a separate one, and the record states which.

**PER FILER, WHAT THE FLOW BEARS.** Every file carries
`operating_leases_in_ocf: yes | no` with its page, beside E34's
`interest_in_ocf`:

- **IFRS 16 filer — `no`.** IFRS 16.50(b) puts the principal in financing,
  so `operating_cash_flow` never bore it; `lease_payments_capital` is a
  memo the flow does not deduct. Nothing is added back and the record
  says so. The lease interest is wherever the filer's IAS 7.31–34 policy
  puts it, which `interest_in_ocf` already records.
- **US GAAP filer — `yes`.** ASC 842-20-45-5(a) puts operating lease
  payments in operating activities, so `operating_cash_flow` is after the
  whole payment. The add-back is the stated cash paid for operating
  leases (`us-gaap:OperatingLeasePayments`, "cash paid for amounts
  included in the measurement of operating lease liabilities"), read into
  the new field `operating_lease_payments`. The payment carries its own
  interest component inside it (a single lease cost); that component
  follows the filer's interest rule — under ASC 230 interest is in
  operating cash flow and is added back (E34), so the whole payment is
  added back and the record names both halves. Finance lease principal
  is in financing (`FinanceLeasePrincipalPayments`) and was never in the
  flow; finance lease interest is inside the filer's interest expense and
  E34's rule already covers it.

**THE DIRECTION, STATED PLAINLY.** **This correction RAISES FCF0, and
therefore raises fair value, for every lease-heavy name.** That is the
opposite direction from most of the recent rulings (E35.1, E36, E65,
E68), and it must not be mistaken for a loosening: it is the removal of a
double charge, the same removal E34 made for interest. A lease-heavy
retailer valued before E70 was charged for its estate twice.

**THE RECORD.** A run record struck before this ruling carries no lease
declaration and is **complete as struck** (the E68 mechanism,
`RECORD_DECLARATIONS_SINCE`); its rendering says the declaration
postdates it. Every record struck from 2026-08-30 08:00 UTC declares it.
Nothing is re-struck here; what would move is printed below.

**WHAT MOVES — measured on the files as they stand, nothing re-struck.**
Code run 2026-08-30. Declaration 3.1 (`operating_leases_in_ocf`) is now in
every manual file; the five US filers that tag `us-gaap:OperatingLeasePayments`
carry the payment per year with the accession on it. The correction RAISES
FCF0 wherever the flow bore the payment — a double charge removed, not a
loosening.

| file | 3.1 | FCF0 before | FCF0 after | Δ | struck fair value | run record |
|---|---|---|---|---|---|---|
| AUTO.L | no, IFRS 16.50(b) | 286.2m GBP | 286.2m | 0 | 2026-08-27 strike unchanged | struck 2026-08-27, before E70 — exempt |
| LIAB.ST | no, IFRS 16.50(b) | 1,050m SEK | 1,050m | 0 | 2026-08-26 strike unchanged | struck 2026-08-26 — exempt |
| PNDORA.CO | no, IFRS 16.50(b) | 7,041m DKK | 7,041m | 0 | unchanged | none |
| SAP.DE | no, IFRS 16.50(b) | 7,399m EUR (record) | 7,399m | 0 | 2026-08-26 strike unchanged; the file's own gate refuses on capex as before | struck 2026-08-26 — exempt |
| BETS-B.ST, SYNSAM.ST | no, IFRS 16.50(b) | gate refused | gate refused | — | none | none |
| CTSH | yes, ASC 842-20-45-5(a); 192m tagged | 2,451m USD | 2,643m | +192m (+7.8%) | 83.01 (2026-08-28) would replay to ≈89.43 — NOT re-struck | struck 2026-08-28 — exempt |
| LII | yes; 90.6m tagged | 650.6m USD | 741.2m | +90.6m (+13.9%) | 274.27 (2026-08-30 03:14 EDT) would replay to ≈319.37 — NOT re-struck | struck 2026-08-30 07:14 UTC, before the 08:00 UTC line — exempt |
| AOS | yes; payment NOT stated (the 10-K gives expense 23.2m and a 2026 maturity of 14.3m, neither is cash paid) | 545.7m USD | **DATA MISSING** on the lease leg | bound +14.3m to +23.2m | 62.66 (2026-08-30 03:14 EDT) stands; a fresh run refuses on the leg | struck 2026-08-30 07:14 UTC — exempt |
| DECK | yes; 92.8m tagged | 991.4m USD | 1,084.2m | +92.8m (+9.4%) | the test-pinned replay 117.71 → 127.75 (B36's 131.74 reconstructed with no add-back, as struck) | no watchlist strike rewritten |
| NKE | yes; 668m tagged | 1,419m USD (test-fixture record) | 2,087m | +668m (+47%) | none struck; the fixture's 12.21 → 19.07 | none |
| EXE | yes; 32m tagged | 2,028m USD | 2,060m | +32m (+1.6%) | none | none |
| ZZ-B.ST, AD.AS | no manual file | — | — | — | — | — |

Records struck before 2026-08-30 08:00 UTC (`RECORD_DECLARATIONS_SINCE`)
replay without declaration 3.1 and are not INCOMPLETE for its absence; any
record struck after it is. Struck values are not rewritten by this ruling —
each moves only when its name is next struck under the framework.

---

### E71 — stated components an issuer never totals are added, where the issuer itself treats them as one quantity

**RULED 2026-08-30 by the owner, on the class the ACN / GDDY / NVR / ULTA /
ZZ-B.ST build surfaced. Amends E66, which allowed the addition for current
borrowings only, and NARROWS E26. Written before the code.**

**THE RULE.** Where a filer presents two or more captions that are parts
of one balance-sheet quantity, states each, and never prints their sum,
**the field is their sum, with every component and its tag (or page) named
in the provenance.** The evidence that they belong together must come from
the issuer — a reconciliation elsewhere in the filing, a note that presents
them as one line, or a subtotal that includes both. This is not E22's
forbidden derivation: E22 forbids inferring a figure the accounts do not
contain; here every figure is stated and only the addition is ours. **Where
the issuer prints a subtotal, the subtotal wins and the components are
memo** (E66's precedence, now general).

**WHAT IT NARROWS.** E26's "a sum no rule authorises" was written when no
rule did. This is the rule. E26 still governs where the issuer's own
evidence that the captions are one quantity is ABSENT — two lines that
merely sit near each other are not added — and E23 is untouched: a part
is still never added to a whole that already contains it.

**APPLIED 2026-08-30.**

- **NVR, cash.** The segmented balance sheet prints `Cash and cash
  equivalents | 1,883,844` (Homebuilding) and `Cash and cash equivalents |
  32,642` (Mortgage Banking) and never their sum; beside them `Restricted
  cash` 34,348 and 6,047. The issuer's evidence: its cash-flow statement
  reconciles to **1,956,881 of "cash, restricted cash and cash
  equivalents"** (tagged `CashCashEquivalentsRestrictedCashAndRestrictedCash
  Equivalents`), which is exactly 1,883,844 + 32,642 + 34,348 + 6,047.
  **`cash_and_equivalents` = 1,883,844 + 32,642 = 1,916,486** (thousands).
  **The restricted portion is NOT cash and equivalents and is excluded:**
  the issuer presents it under its own caption on both segments'
  balance sheets (homebuilding customer deposits held in escrow;
  mortgage-banking escrow), it is not available to service debt, and the
  schema field is the balance sheet's cash caption — the same reason the
  us-gaap map refuses short-term investments (A1). The 40,395 is named on
  the field. The tagged total is therefore NOT this field for any filer
  whose restricted cash is non-zero; GoDaddy's, where 'restricted cash'
  appears nowhere and the tag equals the caption, was entered under E69.
- **NVR, interest.** The Consolidated Statements of Income print
  `Interest expense | (27,578)` under Homebuilding and `Interest income |
  17,886` / `Interest expense | (1,257)` under Mortgage Banking; the
  84,158 of corporate interest income sits inside Homebuilding `Other
  income | 96,260` and is stated as `Corporate interest income | 84,158`
  in the segment note's reconciliation to consolidated profit before
  taxes — the issuer's own reconciliation. **`finance_costs_period` =
  27,578 + 1,257 = 28,835; `finance_income_period` = 84,158 + 17,886 =
  102,044; E18 subtracts: net interest −73,209 thousand, a net INCOME**
  that E34's add-back removes from FCF0. `interest_source:
  income_statement_net` (E34.1). E61's gross-only proxy does not reach a
  filer whose interest income is stated.
- **ZZ-B.ST, leases at 2026-06-30.** The Q2 2026 balance sheet (p.23)
  prints `Lease liabilities 37,637` (long-term) and `Lease liabilities
  24,582` (current). The issuer's evidence that they are one quantity:
  the annual report's note 22 (p.115) presents `Lease liabilities: Long
  term 19,985 / Current 22,005 / Total 41,990`, note 3's maturity table
  (p.97) carries `Leasing liabilities` as ONE financial-liability line,
  and note 37 (p.122) rolls the one liability forward. **`lease_liabilities`
  = 37,637 + 24,582 = 62,219** (thousands) at the basis end.
- **BETS-B.ST, leases at 2026-06-30.** `Lease liabilities` 18.9
  (non-current) and 4.3 (current), H1 2026 interim p.17; the issuer's
  evidence is the annual report's note 30, which presents the lease
  liability as one total at 2025-12-31 (15,359 thousand EUR — E26's own
  entry records it), and the cash-flow statement's single `Amortisation
  of lease liabilities` line. **`lease_liabilities` = 18.9 + 4.3 = 23.2**
  (EUR millions) — the components are the owner's own 2026-08-25 read-back
  of p.17 (named in the file's comments since then); the addition is this
  ruling's, carried `same_page`.

**WHICH NAMES' NET DEBT NOW FORMS.** **NVR** — every leg on the basis:
0 + 909,160 + 186,207 + 0 + 0 − 1,916,486 = **−821,119 thousand, net
cash**; and with the interest sum FCF0 forms too (E34's leg was the last
gap). **ZZ-B.ST** — the lease leg was the last gap; the bridge's
arithmetic now completes (0 + 0 + 62,219 + 0 + 0 − 841,991 = −779,772,
net cash), but every figure on the file is UNVERIFIED, so section 5
still refuses on E21 until the owner's second read. **BETS-B.ST** — the
lease leg forms; net debt still waits on `pension_deficit` and
`asset_retirement_obligation` (E35.1, E68), which its file does not
carry, and FCF0 on the interest pair its interims never state.

**WHAT THE CODE DOES.** The manual loader needed no change: a sum entered
as the field's value with its components on the page line was always
loadable, and the FieldSpec note that said otherwise (`TOTAL_NOT_STATED`)
now states this rule. **The XBRL path applies E71 to one class on its
own:** where `OperatingLeaseLiability` is untagged and BOTH
`OperatingLeaseLiabilityCurrent` and `OperatingLeaseLiabilityNoncurrent`
are, `apply_debt_rulings` writes their sum with both tags named — the
issuer's evidence being that it chose two elements the taxonomy defines
as the current and non-current portions of that one liability. That is
the same shape E65 and E68 already add for finance leases and asset
retirement obligations. No committed file was on that shape on
2026-08-30. Every other E71 addition is a hand entry under E69, the
components and the issuer's reconciliation quoted on the field.

---

### E72 — a combined caption whose lease component is stated only approximately is read whole

**RULED 2026-08-30 by the owner. Amends E67, which required the lease
amount inside a combined line to be STATED. Written before the code.**

**THE RULE.** Where the issuer describes the component without sizing it
exactly — "primarily finance lease liabilities", "no material finance
leases" — **the combined caption is the leg and the issuer's wording is
quoted on the field.** The alternative, reading the borrowings alone,
silently drops a stated liability. **Where the component is material
enough that the wording matters to the outcome, say so rather than
assuming.**

**APPLIED 2026-08-30 — ACN, 10-K `0001467373-25-000217`.** `Long-term
debt | 5,034,169` read whole: Note 10 states it as senior notes carrying
4,967,226 plus `Other (2) 66,943` — *"(2) Amounts primarily include
finance lease liabilities"* — and the leases note states *"As of August
31, 2025 and 2024, we had no material finance leases."* Both are quoted
on `financial_liabilities_noncurrent`. **Materiality, stated:** the
66,943 is 1.3% of the caption and 0.11 USD a share on 632m shares;
whichever way the wording is read, the outcome does not move. The current
caption is read the same way (`DebtCurrent` 114,484 = commercial paper
99,963 + `Other (2) 14,521`). No finance-lease element is tagged, so E65
adds nothing: every dollar of both captions is in exactly one leg.

**WHAT THE CODE DOES.** `apply_debt_rulings` reads a combined non-current
or current caption WHOLE where the filer tags **no finance-lease element
of any kind**, writing on the figure that the lease inside is untagged and
that the issuer's wording must be quoted by hand under this ruling. Where
a finance-lease element IS tagged but not the part inside the caption,
E67's refusal stands — the component is sized somewhere and reading the
caption whole beside E65's addition would count it twice.

---

### E73 — finance leases disclosed but unsized are a named zero

**RULED 2026-08-30 by the owner. Amends E65. Written before the code.**

**THE RULE.** Where a filer states that finance leases exist but gives no
amount anywhere in the filing, **the finance lease component of
`lease_liabilities` is zero with `zero_basis: caption` and the disclosure
named on the field**, in the same form E68.2 settled for unquantified
remediation accruals. Refusing the whole leg over an amount the issuer
does not consider material enough to state is the wrong proportion.

**APPLIED 2026-08-30 — GDDY, 10-K `0001609711-26-000010`.** Note 2,
Leases: *"Assets and liabilities associated with finance leases are
included in property and equipment, net, accrued expenses and other
current liabilities and other long-term liabilities."* No amount is stated
anywhere in the filing, no finance-lease element is tagged, and the
leases note is operating-only. **`lease_liabilities` = 82,300,000
operating (`OperatingLeaseLiability`, tagged) + 0 finance (E73, Note 2
quoted).** The captions with room are named: `Other | 85.7` inside
accrued expenses (Note 8) and `Other long-term liabilities 57.5`. The
figure's verification kind is `same_page`: the weaker component governs
the combined claim (E62's logic).

**WHAT THE CODE DOES.** Nothing automatic — the tool cannot read the
sentence. Where no finance-lease element is tagged, its report now says
that a disclosed-but-unsized finance lease is entered as this named zero
by hand.

---

### E74 — a liability's current portion embedded in another caption is named, not added

**RULED 2026-08-30 by the owner. Amends E35.1 in application. Written
before the code.**

**THE RULE.** Where a note discloses that part of a long-term obligation
sits inside a different balance-sheet line — accrued payroll, other
current liabilities — **that portion is recorded on the field as a note
and NOT added to the leg**, because it is already inside a caption the
bridge either reads or deliberately excludes. Adding it would
double-count against the balance sheet's own arithmetic. **State on the
field which caption holds it.**

**APPLIED 2026-08-30 — ACN.** `pension_deficit` is the balance sheet's
`Retirement obligation | 1,858,499` (non-current, tagged). The retirement
note's *"Amounts recognized in the Consolidated Balance Sheets"* also
shows current liabilities of 10,855 + 63,117 + 1,058 = **75,030 thousand
inside `Accrued payroll and related benefits`**, a caption the bridge does
not read. Named on the field; not added. The plan ASSETS of 171,859 in
non-current assets are not netted either (E35.1).

**WHAT THE CODE DOES.** Nothing: the FieldSpec note on `pension_deficit`
states the rule so the next hand carries it.

---

### E75 — where no weighted average share count exists for the window, the count outstanding at the window end is the divisor

**RULED 2026-08-30 by the owner. Amends E38, and E41's count route on a
TTM basis. Written before the code.**

**THE RULE.** Where a filer reports a TTM window stitched from interims
that state no weighted average, using the prior year's average understates
the count and therefore overstates value per share by the drift. **The
divisor is then shares outstanding at the window end, recorded as
`divisor_basis: period_end` with the drift against the prior average
stated.** E22 stands: the count must be stated as a count, never derived
— E16's issued-minus-treasury of two stated counts is a subtraction the
framework already permits, and it serves here.

**THE ORDER, as coded.** (1) A weighted-average diluted count stated for
the window itself — a twelve-month period entry, or an annual entry
closing on the basis end — is the divisor (E38, unchanged). (2)
Otherwise, on a TTM basis, **the net count outstanding at the window
end** — `shares_outstanding_period_end` as printed, or E16's issued less
treasury (less an employee trust, E54) — is the divisor, `divisor_basis:
period_end`, and the record prints the drift against E41's annual
average where one exists. (3) Where no count at the window end is stated
either, E41's annual average stands, declared as before. (4) Otherwise
DATA MISSING. A point-in-time MEMO (`shares_point_in_time`) is still
never the divisor.

**A CONSEQUENCE RECORDED, NOT HIDDEN.** E38's count is DILUTED; a count
outstanding is BASIC. Where the issuer states no diluted count at the
window end, E75's divisor carries none of the dilution E38 wanted in —
Zinzino's 3,293,314 outstanding warrants (8.4% of the capital, Q2 2026
p.20) fall out of the divisor entirely. The drift E75 removes (4.4%) and
the dilution it drops (up to 8.4%) pull in opposite directions on this
name, and the record says which count it divided by. Whether a stated
diluted count at the window end should be preferred where an issuer
prints one is not decided here.

**APPLIED 2026-08-30 — ZZ-B.ST.** Divisor **39,165,998**, the count
outstanding at 2026-06-30 (Q2 2026 p.19), against the FY2025 weighted
diluted average 37,530,107 that E41 supplied before: **a drift of
+4.36%** after the ItWorks!, Sanki, Bodē Pro, Xion and Truvy share
issues and the warrant exercises of H1 2026. (Q2 2026's own quarterly
diluted average, 39,528,665, is 5.33% above the FY2025 figure; neither
quarterly average is ever the window's, B27.)

**WHICH OTHER FILES IT TOUCHES.** **LIAB.ST**: 77.036 → 77.036 — the
count at 2026-06-30 equals the E41 average, drift 0.00%; only the
declaration changes, and the 2026-08-30 run record (struck on E41's
count) stands as struck. **SYNSAM.ST**: DATA MISSING → 141,980,111 (the
Q2 2026 period-end count; the four quarterly averages were never
summable, B27) — the file gains a divisor. **BETS-B.ST**: DATA MISSING →
135,305,282 (E16: 139,635,838 issued − 4,330,556 treasury at 2026-06-30)
— gains a divisor. **PNDORA.CO** and **SAP.DE**: no count is stated at
2026-06-30 (Pandora's treasury is stated in money, E22; SAP's interims
state none), so E41's annual average stands for both, declared. Every
annual-basis file (the US names, AUTO.L) is on E38 and untouched.

**WHAT THE CODE DOES.** `manual.share_divisor_on_basis` returns the count,
its basis kind and the drift; `share_count_on_basis` keeps its
(count, sentence) shape for every caller. The run record's declaration 1
gains `divisor_basis` (`weighted_average` | `period_end`) and prints the
drift; records struck before this ruling replay with `weighted_average`
and are complete as struck.

---

### E75.1 — a stated diluted period-end count beats a basic one

**RULED 2026-08-30 by the owner, on the consequence E75 recorded. Amends
E75. Written before the code.**

**THE RULE.** Where E75 puts the count outstanding at the window end in
the divisor because no weighted average exists for the window, and the
issuer states BOTH a basic count and a diluted one at that date, **the
diluted count is the divisor.** E38's reason for preferring diluted has
not changed — a claim on the equity is a claim whether or not it has been
exercised — and E75's purpose was to fix the period, not to drop the
dilution. **Record `divisor_basis: period_end_diluted` where it applies
and `period_end_basic` where only a basic count is stated, so the two are
never confused.**

**APPLIED 2026-08-30 — ZZ-B.ST.** E75 moved the divisor from FY2025's
weighted diluted average 37,530,107 to 39,165,998 outstanding at
2026-06-30, which removed a +4.36% drift but dropped 3,293,314 warrants —
about 8.4% of the capital — pulling value per share the other way. **THE
READ: Zinzino states NO diluted count at any period end.** The Q2 2026
interim prints `Number of outstanding shares` 39,165,998 (p.19, a basic
count), `Average number of issued shares for the period with full
dilution` (p.6 and note 4 p.34 — AVERAGES, quarterly and half-yearly),
earnings per share after dilution, and on p.20 the warrant programmes with
their sum: *"If all outstanding warrants that have not yet been exercised
... are exercised for new subscriptions, a total of 3,293,314 Class B
shares will be issued, corresponding to a total dilution of the share
capital amounting to approximately 8.4%."* The annual report states the
same shapes at 2025-12-31 (p.5, note 36 p.122, note 39 p.123) and no
diluted period-end count either. **So the divisor stays the basic count,
`divisor_basis: period_end_basic`, and the dropped dilution is named on
the field** — 3,293,314 potential shares, 8.4%, none of it in the
divisor; the diluted average the store no longer divides by (37,530,107,
FY2025) carried the dilution of an earlier capital and is not a
substitute (E22: the count is the count as stated, and 39,165,998 +
3,293,314 is a sum the accounts do not print as a count).

**WHICH OTHER FILES IT TOUCHES.** Every file E75 reached carries a basic
count only and becomes `period_end_basic`: **LIAB.ST** (77.036 million
`Number of shares outstanding`; the issuer prints diluted EPS equal to
basic EPS and states the 2026 plan "had no impact on diluted earnings per
share", so the dilution dropped is nil by the issuer's own word),
**SYNSAM.ST** (141,980,111 `Number of shares at end of period`),
**BETS-B.ST** (135,305,282, E16's issued less treasury). No file on disk
states a diluted period-end count, so `period_end_diluted` fires nowhere
today; the schema field that would carry one exists from this ruling.
PNDORA.CO and SAP.DE stay on E41's annual average, unchanged.

**WHAT THE CODE DOES.** The manual schema gains `shares_diluted_period_end`
— the DILUTED count the issuer states AT a period end, a stock, a count
as stated (E22), zero refused like every count. `share_divisor_on_basis`
takes it first on a TTM basis with no window average (`period_end_diluted`),
then `shares_outstanding_period_end` or E16's net (`period_end_basic`),
then E41's annual average (`weighted_average`, declared on its own
date). The run record's declaration 1 prints which; a record carrying
E75's short-lived `period_end` label reads back as `period_end_basic`.

---

### E76 — the qualitative reading is required before a tier is scored, not before a fair value is struck

**RULED 2026-08-30 by the owner, on where the reading belongs in the
order of work. Recorded as given.**

**THE RULE.** A fair value without a tier produces no MBP and therefore
authorises no purchase, so a name can be valued cheaply and only worked
up properly when the value says it is worth the hours. The reading takes
an evening; a strike takes minutes. Spending the evening on a name that
turns out to trade at twice its fair value is the wrong order.

**The order is therefore: manual file → growth view → section 5 strike →
and only if the price is within reach of the bear case does the reading
happen, then the section 4.4 score, then the tier and the MBP.** "Within
reach" is the owner's judgement, not a threshold — a name at twice fair
value is not read; a name near or below it is.

**But the growth view is still registered BEFORE the strike, per E28, and
where the reading has already happened it informs that view.** That is
not a contradiction: the reading changes what growth you believe, and
belief must be recorded before the number is seen. **Where a reading
happens after a strike and changes the view, the view is re-registered
with the reason and the name is re-struck — the old view stays in the
record, superseded, never overwritten.**

**WHAT THE READING MUST COVER.** Five sections, each answered from a named
source or marked DATA MISSING. It is written to
`reports/<TICKER>-reading-<date>.md`.

1. **The business and the industry:** what is sold and to whom, the
   revenue split, and how the industry itself is placed — growing,
   consolidating, in structural decline. From the filings for the
   company, from external sources for the industry, each labelled.
2. **Competitors:** who they are, what this company's edge is and where
   it is weak against them, and what is genuinely different about its
   model rather than what its marketing says. State which claims are the
   company's own about itself.
3. **Insider transactions:** every Form 4 or director-dealing disclosure
   in the trailing twelve months, buys and sells reported separately,
   with dates, prices, and whether each was open-market or under a
   pre-scheduled plan. Never netted. A cluster of open-market purchases
   during a drawdown is evidence; a scheduled sale is not.
4. **Management, and this is the section that shapes the growth view.**
   Who the CEO and CFO are, when they arrived, what they did before, and
   what happened at those companies on their watch. Then the judgement
   the owner makes, recorded as his: what KIND of executive this is. A
   cost-cutter brought in to restructure implies margin expansion without
   volume — a higher base and a lower bull. A builder implies the
   opposite. A caretaker implies continuity. The type says what phase the
   business is in, and that is an input to growth that no figure in the
   accounts carries. Where the tenure is too short or the record too thin
   to judge, say so rather than inventing a type.
5. **Capital allocation:** what the cash has been spent on over the last
   three years — buybacks and at what average price against the fair
   value now struck, dividends, acquisitions and what they cost, debt
   raised or repaid. Whether management has bought its own shares above
   or below what the tool thinks they are worth is one of the few places
   their judgement is directly measurable against yours.

**The reading ends with the five things a reader still would not know
that a valuation needs, ranked, and with the section 4.4 evidence
assembled — gates, hard kills, green and soft flags — so the score
follows from it rather than being struck separately.**

**WHICH EARLIER RULING THIS AMENDS.** None in its text. It ORDERS E28's
pre-registration, the section 5 strike and section 4.4's score, and it
gives the reading a form and a home. §11's output contract is untouched.

#### The BRIEFING, built 2026-09-04 — the research the reading stands on

**BUILT ON THE OWNER'S INSTRUCTION, AND IT CHANGES NO RULE.** E76's reading
is his and stays his; what was missing was the material it stands on, which
was being gathered by hand every time. `vss briefing --ticker X` now
assembles it into `reports/BRIEFING-<TICKER>-<date>.md` for any name whose
store supplies a basis.

**IT MAY MAKE NO JUDGEMENT, and a check over the FINISHED TEXT refuses it
if it does** — no thesis, no growth rate, no valuation. The check is run on
the output rather than trusted to the author, because a research note
sliding into a thesis is exactly the failure an author does not notice
himself committing, and the web route can commit it on his behalf.
**VERBATIM QUOTES ARE EXEMPT AND NOTHING ELSE IS:** a filer is entitled to
write *"we do not believe that we compete directly with any single
company"*, and reproducing that sentence is reporting rather than
asserting.

**EVERYTHING IS A TAGGED FACT OR A VERBATIM QUOTE.** Nothing is
summarised — a summary is a judgement wearing a fact's clothes, and two
readers cannot check it against the page. The eight sections are E76's
five, plus the three the owner added on 2026-09-04: what has happened
quarter by quarter in management's own words, why the price fell with dated
events, and **what the filings do not answer, named in one place** — which
is the part the reading actually consumes.

**ONE SECTION CANNOT COME FROM A FILING and says so on its face.** A 10-K
does not say why the shares fell on a Thursday. The price series says WHEN,
to the day, off the cache this project already holds; the reason is asked
of the web, the block is labelled WEB-SOURCED, and **every claim kept
carries the URL the route returned — a claim with no citation is dropped
rather than printed.**

**A SECTION THAT CANNOT BE FILLED IS NEVER FILLED WITH SOMETHING
ADJACENT.** Three filers taught this build what a heading is worth: Crocs
names `Summary Compensation Table` four times and only one is the table;
Murphy USA splits `Total Number of Shares Purchased` across five lines so
the phrase never appears whole; every 10-K names each Item twice, once in
the contents. So a block is accepted only when it looks like what it
claims to be — enough rows carrying numbers for a table, enough length for
prose — and otherwise the section says NOT LOCATED and names the filing it
read.

**RUN 2026-09-04 for CROX, LOPE and MUSA**, the three INTAKE names whose
records are complete but for a growth view.

#### The state on 2026-08-30, recorded beneath the ruling

**Seventeen manual files exist; twelve are live names** (the other five:
BETS-B.ST, NKE and SYNSAM.ST are DROPPED, DECK and PNDORA.CO are
WATCH-GATED on a §4.2 event, not a price). **Readings in E76's sense exist
for two: AUTO.L (2026-08-27) and CTSH (2026-08-28)**, both written before
this ruling and both short of its five sections — CTSH carries the
business, insiders (Forms 4, twelve months, buys and sells apart), the
gates and the five unknowns, but no capital-allocation section and no
management type; AUTO.L carries the business, the Gate 2 decline driver,
the quality read, capital allocation and the five unknowns, but no
insider section and no management type. **SAP.DE and DECK have §4
scoring-evidence files (2026-08-21 and -25) that are evidence assembly,
not readings.** The other thirteen have none.

**Distance to the bear case, on the latest run record and the settled
close of 2026-08-28 (Stockholm and London 2026-08-27):**

| name | status | fv_base | bear | close | vs bear | vs fv_base | reading |
|---|---|---:|---:|---:|---:|---:|---|
| GDDY | not on the watchlist | 156.45 | 111.36 | 97.70 | **−12.3%** | −37.6% | none |
| CTSH | WATCH-PRICED | 89.38 | 66.83 | 64.04 | **−4.2%** | −28.4% | 2026-08-28 |
| ACN | not on the watchlist | 255.10 | 183.75 | 189.61 | **+3.2%** | −25.7% | none |
| LIAB.ST | HELD | 133.48 | 107.23 | 131.60 | +22.7% | −1.4% | none |
| AOS | not on the watchlist | 62.66 | 46.61 | 60.38 | +29.5% | −3.6% | none |
| AUTO.L | PIPELINE | 4.82 | 3.83 | 5.36 | +40.2% | +11.2% | 2026-08-27 |
| ULTA | not on the watchlist | 476.45 | 359.43 | 517.50 | +44.0% | +8.6% | none |
| SAP.DE | WATCH-PRICED (sold) | 139.48 | 120.27 | 189.88 | +57.9% | +36.1% | evidence only |
| NVR | PIPELINE | 4,978.10 | 3,422.77 | 6,396.27 | +86.9% | +28.5% | none |
| LII | not on the watchlist | 274.27 | 174.40 | 393.39 | +125.6% | +43.4% | none |
| EXE | not on the watchlist | — | — | 98.16 | no strike: no growth view | | none |
| ZZ-B.ST | PIPELINE | — | — | 138.50 | no strike: 57 figures UNVERIFIED | | none |

(LII's record is the 2026-08-30 03:14 strike; E70's replay of it, ≈319,
was printed and not struck. GDDY's fair value stands on E69's stated net
interest; ACN's on E72's whole caption; NVR's on E71's segment sums.)

**Which warrant a reading now — an observation for the owner's
judgement, not a threshold applied:** the two names BELOW their bear case
and the one within a few percent of it — **GDDY (−12.3%), CTSH (−4.2%,
already read; the reading wants E76's two missing sections), ACN
(+3.2%)** — are the ones where the price says the evening is worth
spending. LIAB.ST at +22.7% is HELD, so the reading there serves the
thesis rather than an entry; AOS at +29.5% is the next nearest. AUTO.L
(+40.2%, read), ULTA (+44.0%), SAP.DE (+57.9%), NVR (+86.9%) and LII
(+125.6%) are, on this ruling's own words, not read. EXE and ZZ-B.ST
cannot be placed until a growth view is registered for the one and the
owner's second read verifies the other. **No reading was started under
this entry.**

---

### E77 — the regime is ELEVATED, and §5.3's one-tier-stricter adjustment applies from here

**RULED 2026-08-30 by the owner, on scoring GDDY. The first application of
FRAMEWORK §5.3's regime adjustment ("In an elevated-valuation regime
(§2.1), shift every name one tier stricter"). Recorded as given.**

**THE RULE.** §2.1's regime verdict is **ELEVATED** as of 2026-08-30, on the
owner's judgement: global indices at all-time highs. **§5.3's adjustment
therefore applies to every name scored from here until the regime is
re-assessed:** the tier the section 4.4 score and the §5.3 definitions
produce is shifted one tier stricter — Tier 1 to Tier 2, Tier 2 to Tier 3
— and the MBP is the pre-registered bear case times THAT tier's cushion
(E28). The regime verdict is the owner's and is not derived from any
figure this project computes; §2.1's own evidence lines (index forward
P/E against its five-year average, CAPE) were DATA MISSING on every
evidence sheet written here (MSFT, 2026-08-21, and since), and this
ruling does not fill them. **Re-assessment is a dated act by the owner,
recorded as a new entry beneath this one; until one is recorded, the
regime stands as elevated.**

**FIRST APPLICATION — GDDY, 2026-08-30.** Section 4.4 scored **6** (4
gates passed — 1, 2 as Class A, 3, 5; Gate 4 not passed on the evidence —
plus 3 green flags — guidance held through the drawdown, FCF conversion
161%, margin expansion — less 1 soft flag, A&C deceleration; the buyback
green flag WITHHELD by the owner: the Q1 2025 ASR at 176.02, 33% above
the fv_base now struck, beside 2026's repurchases at ~87, is a fixed
budget executed regardless of price, a habit rather than capital
allocation). 6 is the medium band → **Tier 2 → shifted to Tier 3 under
this ruling.** MBP = bear 111.36 × 0.60 = **66.82 USD** (band 72.70 / 66.82
/ 61.72 across r 9.0–10.0%, E29), against 77.95 at Tier 2. Price 97.70
(2026-08-28) is +46.2% above it: WATCH-PRICED (E27), the limit alert
armed at 66.82.

**WHAT IT WOULD DO TO THE TIERS ALREADY CARRIED — reported, NOT applied.**
Two names carry a tier today, both Tier 2:

| name | status | bear (record) | tier 2 MBP, as carried | tier 3 MBP under E77 | armed alert would move |
|---|---|---:|---:|---:|---:|
| LIAB.ST | HELD | 107.23 (2026-08-30 record) | 75.06 | **64.34** | −10.72 SEK |
| CTSH | WATCH-PRICED | 66.83 (2026-08-30-e70 record) | 46.78 | **40.10** | −6.68 USD |

**Retrospective or from now — the owner's question, answered with a
recommendation and not a decision:** **from now.** The tier adjustment is
a statement about the regime at the moment a name is scored; both tiers
were struck (2026-08-26 for LIAB.ST, 2026-08-29 for CTSH) when no regime
verdict existed, and nothing about either NAME has changed — a re-tier
would move a re-entry line (LIAB.ST) and an armed limit alert (CTSH)
on no new information about the company, which is the shape E12's
freeze exists to prevent. The asymmetry is stated so it is not missed:
CTSH's alert at 46.78 sits 6.68 above what today's rule would arm, and a
purchase there would be made at a cushion the regime rule now calls too
thin. If the owner wants consistency over the freeze, the re-tier is one
line each on the watchlist and is his write; **neither entry is touched
by this ruling.**

**WHICH EARLIER RULING THIS AMENDS.** None. §5.3's adjustment existed
unused; E77 records the verdict that switches it on, the date, and the
scope. E28's MBP arithmetic is unchanged — the cushion is Tier 3's 0.60.

---

### B44 — whether non-plan officer sales inside a drawdown should be a soft flag

**RAISED 2026-08-30 by the owner, on the GDDY reading. OPEN — not decided,
and NOT applied to GDDY's score.**

**The gap.** §4.3's soft-flag list — customer concentration, an open
regulatory probe, SBC over 30% of FCF, key-segment deceleration, rising
DSO — carries no entry for insider SELLING; the only insider item is the
green flag for an open-market BUYING cluster, whose absence scores zero.
So the GDDY record — **zero open-market purchases in twelve months against
44 sales, and the CEO's 34,148 and CFO's 17,406 shares sold on 2026-03-04
at 88.99, a week after the 25 February fall, without a Rule 10b5-1 plan
indicator on the Form 4** — is evidence with no flag to attach to under
the framework as written, and it entered GDDY's score at zero.

**What a ruling has to settle.** Whether non-plan sales by the CEO or CFO
inside a drawdown (a price below the 52-week high by Gate 1's band) are a
soft flag (−1); what size clears de-minimis (the quarterly same-day sales
on grant dates that look like tax withholding are coded S on the form,
not F); whether a 10b5-1 plan flag exempts a sale as E76 treats it for
the reading ("a scheduled sale is not" evidence); and whether the flag
is symmetric with the existing buying green flag (≥2 insiders, 90 days)
or fires on the CEO or CFO alone. **Nothing is implemented.**

#### E77 — the application to the tiers already carried, DECIDED by the owner 2026-08-30 (supersedes the recommendation above)

**FROM NOW ONLY — the owner's decision, recorded as given.** The asymmetry
is known and accepted. LIAB.ST at tier 2 and CTSH at tier 2 were both
scored before any regime verdict existed, and re-tiering them would move
a held name's re-entry line and an armed alert on no new information about
either company — the shape E12's freeze exists to prevent. But it does
mean two yardsticks are live at once: CTSH's alert sits at 46.78 while
today's rule would arm 40.10.

**The resolution is timing, not exception.** Both are re-scored at their
next scheduled reassessment — **LIAB.ST at the Q3 report on 2026-10-23,
CTSH at Q3 on 2026-10-28** — and E77 applies then. That way the regime
adjustment reaches them on new information rather than on a rule change.

**Recorded on the entries:** LIAB.ST already carried `catalyst_date:
2026-10-23` / `catalyst_event: Q3 2026 report` (set 2026-08-30); CTSH's
2026-10-28 stood in its notes only and is now on its catalyst fields
(`catalyst_date: 2026-10-28`, `catalyst_event: Q3 2026 results — the
next scheduled section 6.4 reassessment; E77 applies at the re-score`).
Until those dates, 75.06 SEK and 46.78 USD stand as carried, and GDDY's
66.82 is the first MBP struck under the adjustment.

---

### B45 — a standing sales record: every closed position against the index from its sale date

**PROPOSED 2026-08-30, from `reports/SALES-RECORD-2026-08-30.md` (MSFT,
UNA.AS, SAP.DE). A proposal, not an implementation; nothing in the code
changes until the owner rules.**

**Problem.** The framework sells on rules (C1–C4, E42) but keeps no record
of what happened after a sale, so the rules are never tested against their
own outcomes. The first hand-built record found that two of three sales
had no sale price on file at all (SAP.DE `[fyll i]`; UNA.AS an unbooked
order, still `HELD`), and the third (MSFT) is recorded to the dollar. A
comparison that has to be rebuilt by hand each time will not be rebuilt.

**Proposed: a `vss sales` report.**

1. **A structured `sales:` block on the watchlist entry**, alongside the
   prose the SOLD/EXITED notes carry today — one item per fill:
   `date`, `price`, `currency`, `shares`, `account`, `rule` (C1 | C2 | C3 |
   C4 | owner), `run_record` (the strike the rule fired against), `note`.
   The prose stays; the block is what the command reads. A fill the owner
   has not entered is DATA MISSING and prints as such — the command never
   fills a price from a bar.
2. **One table, every closed position, from its sale date to the last
   settled close**: sale price, last settled close and date, % change, and
   the same-window change of the comparison indices — `^OMX` (OMXS30) for
   a name held in the SEK account and `^GSPC` (S&P 500) for the USD account,
   with the name's own home index (DAX, AEX, FTSE 100, OBX …) as a third
   column where the owner wants it. Comparison in the QUOTE currency; the
   SEK total return including FX (the second quantity MSFT's exit note
   keeps apart) is a separate column or not shown, never blended.
3. **Fixed horizons beside "to date"**: the same comparison at 30, 90 and
   365 calendar days after the sale, each printed only once the horizon has
   passed and the close is settled — so a one-week reading like today's is
   visibly a one-week reading.
4. **The rule column is the evidence column.** Grouping the table by `rule`
   is what eventually says whether C4 sells too early, whether C1 stops
   are set too tight, and so on. Until the count is large — dozens of
   exits over a year or more — the report prints the count and says the
   sample is too small to read; the owner decides the threshold.
5. **Placement.** A section in the daily report (`vss run`) for the last
   90 days' sales, and the full history on demand (`vss sales --all`).
   Read-only: it never writes the watchlist.

**Open for the owner.** (a) Whether the comparison index is fixed per
account or per name. (b) Whether a partial trim under §6.4 is a "sale" in
this table or only a full exit. (c) Whether the record should also carry
the fair value in force at the sale (fv_base / FV_bull from the linked run
record) so the table can show how far above FV_bull each C4 sale was.


**IMPLEMENTED 2026-08-30 on the owner's instruction, as described above,
with the open points settled this way:** (a) both indices are always
printed, `^OMX` (OMXS30) and `^GSPC` (S&P 500), no per-name home index;
(b) the block is per FILL, so a §6.4 trim books exactly like an exit and
the status column says which; (c) the run record is carried on the fill
(`run_record`), and where the sale predates run records the note says
what it was struck in. The block: `sales:` on the watchlist entry, one
item per executed transaction -- `date`, `price` (optional; absent is
DATA MISSING and stays so), `currency` (defaults to the entry's),
`shares`, `account`, `rule` (C1 | C2 | C3 | C4 | owner), `run_record`,
`proceeds_sek` (what landed, net of charges and FX, never blended with
the price return), `note`. The command: `vss sales` writes
`reports/SALES-RECORD-<date>.md` -- every fill against the last settled
close and against both indices from the index's close on the sale date,
plus the 30/90/365-day marks once each has settled, and a by-rule table;
below 20 priced fills (provisional floor) it says in words that the
sample cannot distinguish rule from luck. Code: `vss/config.py`
(`SaleRecord`, `_parse_sales`), `vss/sales.py`, the `sales` subcommand;
tests in `tests/test_config.py` and `tests/test_sales.py`. First run
2026-08-30 on the five fills booked the same day (MSFT x2, UNA.AS,
SAP.DE x2).

---

### B46 — the operating-margin reconciliation refuses a hand-read EBIT whenever the issuer states no margin, or states one to the whole percent

**PROPOSED 2026-08-30, met on RMV.L and NHY.OL. A proposal, not an
implementation.**

**Problem.** `config.unit_problem` (the loader's unit contract, applied to
every manual period and annual entry by `manual._check_units`) refuses an
`operating_income` that has no `op_margin` beside it ("UNRECONCILED"), and
refuses the pair when they differ by more than 0.1pp. The check exists for
a good reason — NKE's "Income before income taxes" 1,416 was once recorded
where EBIT was 1,392 — and the `source: xbrl` exemption is deliberately
withheld from the manual path. But two ordinary IFRS filers cannot pass it:

- **Rightmove** states its operating margin to the whole percent ("Operating
  margin 68%", AR 2025 p.25; "66%", H1 2026). Its EBIT/revenue is 67.71%
  and 65.60%: gaps of 0.29pp and 0.40pp, over the tolerance, from the
  issuer's own rounding.
- **Norsk Hydro** states no operating margin anywhere in five reports (it
  presents EBIT and adjusted EBITDA), so the only lawful entries are an
  EBIT with a blank margin — refused — or no EBIT at all.

Both files therefore carry the printed EBIT in a comment and leave
`operating_income` blank, as the check's own message instructs. That
keeps Method B (EV/EBIT) and the E6 operating-profitability leg unreadable
from these files for no reason of the accounts.

**Proposed, for the owner to choose between.**

1. **Tolerance follows the stated precision.** A margin stated as a whole
   percent is entered as a whole percent and reconciled at ±0.5pp; one
   stated to a decimal at ±0.05pp; the 0.1pp default stays for a margin
   whose precision is not marked. The entry says which (`op_margin_precision:
   1 | 0.1`), so nothing is inferred.
2. **A caption declaration as the alternative reconciliation.** What the
   check wants to know is which line the figure came from. A new key
   `operating_income_line:` holding the caption verbatim ("Earnings before
   financial items and tax (EBIT)") satisfies the check where the issuer
   states no margin — the reader has named the line, which is what NKE's
   error was missing. Without either a margin or a caption the refusal
   stands as today.
3. **Nothing changes**, and the two files stay as they are — the printed
   EBIT in a comment, `operating_income` DATA MISSING on the file.

Option 2 is the one that answers the check's question directly; option 1
alone would still leave Hydro unreadable.

### E78 — a caption zero standing on a clear sentence is VERIFIED without a second document

**RULED 2026-08-30 by the owner. Written before the code.**

**THE RULE.** Where a field is zero because the issuer states IN WORDS that
the thing does not exist — no interest-bearing debt, defined contribution
only, no decommissioning obligation — the zero takes **`verified_kind:
caption_statement`** with the sentence quoted verbatim on the field.
Requiring a second source for the absence of a thing is a standard nothing
can meet: an absence is stated once, in one place, and there is no
roll-forward or component sum to reconcile it against. **This does not
relax E40 for figures** — a number still needs its second read; it settles
that a stated nothing is not a number.

**WHAT THE CODE DOES.**

1. A fourth `verified_kind`, **`caption_statement`**, beside E40's three.
   The gate accepts it as it accepts the others (E21 does not rank kinds);
   the report prints it beside the figure and beside the zero in the E25
   zeros table.
2. A figure key **`statement:`** holding the issuer's sentence verbatim. A
   `caption_statement` flag without one is refused at the load — the
   sentence IS the evidence, and a kind that names none has nothing to
   stand on. A `statement:` on any other kind is refused too: it belongs
   to this one.
3. The kind is accepted **only on a ZERO** carrying E25's `caption` or
   `note` form. A non-zero figure so flagged is refused (E40 governs
   numbers); a `subtotal` zero is refused (a subtotal is arithmetic, not a
   sentence — E59's shape, and it is verified on its own terms).
4. The XBRL writer's refusal to overwrite hand work (E40 §5's guard) counts
   this kind with `cross_document` and `same_page`: a sentence a person
   found and quoted is a reading the writer cannot redo.

**HOW IT IS APPLIED, so the applications below are checkable.** The
sentence must be the PERIOD'S OWN DOCUMENT'S, or the period's document
must itself say its policies are those of the document that carries it
("The accounting policies have been applied consistently to all periods
presented", an interim's usual line). A sentence in an OLDER document
that the newer one does not adopt is not this kind — RVRC.ST's pension
zero on a year-old AR 2024/25 sentence stays UNVERIFIED and stays the
owner's question. A printed dash with NO sentence anywhere (RKT.L's,
IMB.L's, RVRC.ST's, ZZ-B.ST's decommissioning captions; LUG.ST's lease
and borrowing captions at 30 June 2026) is a caption zero E25 accepts and
E78 does not reach: there is nothing to quote. A printed `-0` (RVRC's
capex) is a NUMBER under 0.5 million, not an absence, and E40 governs it.

**APPLIED 2026-08-30.** Read at the basis = counted by `section5_gate` as
UNVERIFIED figures the basis reads.

| name | before (UNVERIFIED read at basis) | after | what cleared | what did not, and why |
|---|---:|---:|---|---|
| ZZ-B.ST | 7 | 3 | 2026-Q2 borrowings ×2 (Q2 p.17: "The Group has an unutilised overdraft facility of SEK 80 (80) million" — the group's only facility, undrawn; AR p.64's "no interest-bearing loans" is the fuller sentence and is older); FY2025 pension (note 2.7.2 "The Group companies only have defined contribution pension plans"); FY2025 sbc (note 39: options subscribed "at an estimated market value through Black & Scholes calculations" — no IFRS 2 cost); FY2025 borrowings ×2 (p.64), not read at the basis | FY2025 decommissioning caption (no sentence); 2026-Q2 lease sum (E71, a number); 2026-Q2 share count (a number) |
| APN.L | 18 | 14 | 2025-FY borrowings ×2 (note 23: "The Group's financial instruments comprise cash and cash equivalents, lease liabilities and items such as trade and other receivables and trade and other payables"); 2025-FY pension (policy 2.19 "The Group operates a defined contribution pension scheme"); 2025-FY sbc (note 6 "a share-based payment expense of £nil was recognised in the year ended 31 July 2025"); the same three legs on 2026-H1 (interim note 9's sentence; "The accounting policies have been applied consistently to all periods presented"), not read at the basis | — |
| RMV.L | 25 | 22 | 2025-FY borrowings ×2 (p.59 "no external debt"); 2025-FY pension (p.123 "The Group provides access to stakeholder pension schemes (defined contribution pension plans)") | 2026-H1's three (no sentence in the RNS; not read at the basis) |
| RVRC.ST | 57 | 54 | 2026-Q4 borrowings ×2 and FY2026 borrowings ×2 (p.19 "Interest-bearing debt * 15 … * Is composed of leasing liabilities"); FY2026 sbc (note 5 "The warrants have been transferred to the participants at market price") — of these, the two Q4 legs and sbc are read at the basis | FY2026 pension (AR 2024/25 sentence, not adopted by the year-end report — the owner's question stands); decommissioning caption (no sentence); five `-0` capex lines (numbers) |
| LUG.ST | 27 | 27 | 2025-Q3 finance costs paid and charged (Q3 MD&A: "With the Company in a debt free position, no derivative gains or losses are recognized"); FY2025 finance costs and borrowings ×2 (FY MD&A: "and no debt"; "debt free position") — none of them read at the basis: the 2025-Q4 package carries no finance-cost line, so the TTM interest net cannot form and E60 reads neither leg | 2026-Q2 borrowings ×2 and lease (no sentence in the Q2 report); FY2025 lease |
| RKT.L, IMB.L | 22, 20 | 22, 20 | — | the decommissioning captions (no sentence; RKT.L's is E68.2's form — note 18's "Other provisions include environmental and other obligations", unquantified — and its page now says so) |
| NHY.OL | 43 | 43 | — | the E67 lease zero is a `subtotal` form, arithmetic not a sentence |

**WHICH EARLIER RULING THIS AMENDS.** **E40** — a fourth kind. **E25** is
unchanged: the zero still needs its form, and `caption_statement` sits on
top of the form, never instead of it. E59 is unchanged: a figure that
reconciles is `cross_document`; a nothing that is stated is this.

---

### E79 — the margin check compares at the precision the issuer printed

**RULED 2026-08-30 by the owner, settling B46. Written before the code.**

**THE RULE.** Where an issuer states an operating margin rounded to the
whole per cent and the computed margin agrees at that precision, there is
no conflict and `operating_income` is entered. RMV.L prints 68% against a
computed 67.71%, which rounds to 68%: the check was protecting against a
DERIVED margin and was firing on ROUNDING instead. **Compare at the stated
precision; refuse only where the figures genuinely disagree once both are
rounded the same way.** Where the issuer states no margin at all, the check
has nothing to compare and does not fire.

**WAS THAT ALREADY THE BEHAVIOUR? No.** Before this ruling
`config.unit_problem` refused an `operating_income` with a blank
`op_margin` as `UNRECONCILED` on every path but `source: xbrl` — the
NKE safeguard B46 describes (income-before-tax 1,416 once recorded where
EBIT 1,392 belonged). E79 withdraws that refusal: a stated EBIT with no
stated margin ENTERS, and what now guards the line it came from is the
page reference, which on the manual path must quote the caption. The
NKE case is therefore caught by the reader's citation and by nothing
mechanical; the owner accepted that trade in ruling this.

**WHAT THE CODE DOES.**

1. The precision is READ FROM THE ENTERED MARGIN: `0.68` is a whole
   percent, `0.297` a tenth. Decimals are floored at two (a margin typed
   `0.7` for a printed 70% is still a whole percent, not a tenth of a
   unit) and capped at three (`rules.MARGIN_PRECISION_DECIMALS`). The
   band is HALF A UNIT of that precision — a computed margin within it
   rounds to the printed one — so a whole-percent margin may sit 0.5pp
   from `op_income / revenue`.
2. `MARGIN_RECONCILIATION_TOLERANCE` (0.1pp, absolute) is retired as the
   rule and kept as a FLOOR (`rules.MARGIN_TOLERANCE_FLOOR`): the band is
   never tighter than 0.1pp. Half a unit of a tenth-of-a-percent margin
   would be 0.05pp, and the components such a margin is struck from are
   printed rounded too — SYNSAM.ST's 2026-Q1 EBIT/revenue is 10.33%
   against a printed 10.4%, a 0.07pp gap that passed before this ruling
   and would fail without the floor, for the issuer's rounding, which is
   the thing E79 exists to stop. So: whole percent, ±0.5pp; a tenth,
   ±0.1pp; a hundredth, ±0.1pp. No file that passed before fails now.
3. The `UNRECONCILED` branch is removed; the `source: xbrl` exemption it
   carried is moot and goes with it. `FRACTION_BANDS` is unchanged: an
   `op_margin` outside [-10, 1] is still a unit error.
4. The XBRL annual writer's `OMITTED_FIELDS` note on `operating_income`
   named the UNRECONCILED check as its reason; the note now records that
   E79 removed the obstacle and that WRITING the field is a separate
   decision this ruling does not take.

**APPLIED 2026-08-30.**

| name | period | operating income, as printed | stated margin | computed | enters? |
|---|---|---:|---:|---:|---|
| RMV.L | 2025-FY | 287,874 (GBP k) | 68% (p.25) | 67.71% → 68% | **yes** |
| RMV.L | 2026-H1 | 148,168 | 66% | 65.60% → 66% | **yes** |
| RKT.L | 2025-FY | 4,217 (GBP m) | 29.7% | 29.69% → 29.7% | already entered |
| RKT.L | 2026-H1 | 1,166 | none stated (the 18.7% is another grouping) | 18.2% | **yes**, margin blank |
| NHY.OL | 2025-Q3 / Q4 / 2026-Q1 / Q2 / FY2025 | 3,491 / (1,480) / 4,396 / 8,609 / 14,401 (NOK m) | none stated anywhere | — | **yes**, margin blank |
| APN.L | 2025-FY / 2026-H1 | 28.1 / 20.7 (GBP m) | none (only an EBITDA margin APM) | 26.2% / 27.8% | **yes**, margin blank |
| IMB.L | 2025-FY / 2026-H1 | 3,490 / 925 (GBP m) | none (adjusted margins only) | 10.8% / 6.3% | **yes**, margin blank |
| KAR.ST | 2025-Q4 | 895.7 (MSEK) | 134.7% (p.2; the EHS divestment gain inside EBIT) | 134.7% | **no** — the margin agrees exactly but `FRACTION_BANDS` refuses an `op_margin` above 1; entering the EBIT with the margin blank would misstate a margin the issuer prints. Residual: whether the band's ceiling of 1 should admit a stated margin above 100% (a gain inside EBIT), the owner's |
| RVRC.ST | 2026-Q1 / Q3 | 75 / 105 (MSEK) | 19.0% / 21.4% (to a tenth) | 19.13% → 19.1% / 21.56% → 21.6% | **no** — a genuine disagreement at the stated precision, from the issuer's WHOLE-MILLION rounding of the components, not of the margin (75 is 74.5–75.5 on 391.5–392.5, a range that contains 19.0%). A SEAM, stated: Q1's printed 19.0% can only be typed `0.19`, which the code reads as a whole percent, so the LOADER would accept Q1 (0.13pp inside ±0.5pp) while refusing Q3 (0.16pp over ±0.1pp); the reader, who can see the printed tenth, entered neither. Residuals for the owner: whether component rounding earns a band of its own, and whether a `precision:` key should carry a trailing zero the float cannot |

**WHICH EARLIER RULING THIS AMENDS.** Settles **B46** (option 1's shape,
with the precision read from the entry rather than declared). The NKE
safeguard's mechanical half is withdrawn, as stated above.

---

### E80 — a net share count is issued less treasury where both are stated

**RULED 2026-08-30 by the owner. Written before the code.**

**THE RULE.** Where an issuer prints the issued count and the treasury
count at the same date but never their difference, the net count is the
subtraction, with both components and their pages named in the
provenance. This is E16 and E18's shape, not E22's forbidden derivation:
both figures are stated and only the subtraction is ours. Where an
employee trust holds shares that the issuer excludes from its own
earnings-per-share count, E54 applies and those come out too.

**WHAT THE CODE DOES.** Nothing new: E16's `Subtraction(NET_SHARES,
ISSUED_SHARES, TREASURY_SHARES, optional_subtrahend=TRUST_SHARES)` has
subtracted the pair on the basis since E16, and E75 takes that net as the
divisor at a TTM window end where no window average is stated. E80
RECORDS that this is lawful against E22, and the three field
descriptions now cite it. What E80 changes is the READER'S duty: a file
that prints the pair and leaves the net blank is incomplete, and a net
the accounts DO print goes in `shares_outstanding_period_end` as printed
(E22), with the pair named on its page rather than entered beside it.

**APPLIED 2026-08-30.**

| name | date | issued | treasury | trust (E54) | net | how |
|---|---|---:|---:|---:|---:|---|
| RKT.L | 2025-12-31 | 702,089,339 | 29,709,130 | not counted (the ESOT's holding is not sized anywhere in the report; only its purchases, £3m, are) | **672,380,209** | PRINTED: directors' report p.113 "issued share capital consisted of 702,089,339 ordinary shares of 10 pence each of which 672,380,209 carried voting rights and 29,709,130 ordinary shares were held in Treasury" — entered as printed under E22, the pair named on its page |
| RKT.L | 2026-06-30 | 674,005,752 | 38,950,759 | as above | **635,054,993** | E80: the pair entered from H1 note 9 p.26 ("issued ordinary shares were 674,005,752 … of which 38,950,759 ordinary shares were held as Treasury shares"), the net subtracted by the store |
| IMB.L | 2025-09-30 | 869,890,634 | 62,600,000 (note 28, "62.6" million — stated to 0.1m, the count is the issuer's precision) | 3,000,000 (note 27, "3.0" million; "the shares held by the Trusts are excluded from the calculation of basic earnings per share") | **804,290,634** (±100,000 from the two rounded parts) | E80 + E54: the pair and the trust entered, the net subtracted by the store |
| IMB.L | 2026-03-31 | 844,313,254 | not stated in the interim | not stated | DATA MISSING | the pair is incomplete (E16): an issued count alone is not a net |

**WHICH OTHER FILES GAIN A DIVISOR.** None change: every file that
carried the pair (AUTO.L, PNDORA.CO, BETS-B.ST, SYNSAM.ST, KAR.ST,
RMV.L) was already subtracting it under E16, and RKT.L's and IMB.L's
bases are twelve-month years that state a weighted average, which E38
takes ahead of any period-end count. The nets above are on the record
for E75's day — a TTM window ending on a date whose average is not
stated — and for the buyback arithmetic a reader wants beside the count.

**WHICH EARLIER RULING THIS AMENDS.** None; it confirms **E16** against
**E22** and restates **E54**'s third leg.

---

### E81 — a prepaid delivery obligation is net debt

**RULED 2026-08-30 by the owner. Written before the code.**

**THE RULE.** Where an issuer has received cash in advance against a
future obligation to deliver product — a streaming agreement, a prepaid
offtake, a metals stream — the outstanding balance is a leg of net debt.
The company has the money and must perform; that it is settled in metal
rather than currency does not make it less of a claim. **New leg
`prepaid_delivery_obligation`**, read from the balance sheet caption,
DATA MISSING where the issuer carries one and states no balance, and a
caption zero where no such arrangement exists. Same reasoning as E68 for
decommissioning: an obligation that is not optional, is measured, and is
material.

**WHAT THE CODE DOES.**

1. `manual.FIELDS` gains `prepaid_delivery_obligation` (money, 5.1C). It
   joins `NET_DEBT_LEGS` on E68's terms — absent is DATA MISSING for net
   debt, never silently zero — and `ZERO_NEEDS_BASIS` (a wrong zero
   understates net debt by the whole stream). It is a STOCK field and
   deliberately **not** annual-only (E41): a stream sits on every interim
   balance sheet, so the newest quarter must carry it.
2. `net_debt_on_basis` adds it and names it; the run record carries it as
   bridge item `prepaid_delivery_obligations` (declaration 4).
3. **A record is a statement made on a date under the rules of that date
   (E68's mechanism).** `BRIDGE_ITEMS_SINCE` now accepts a DATETIME: the
   leg exists from **2026-08-30 15:00 UTC**, after the morning's strikes
   (LII 08:18, LIAB.ST 08:26, NVR and ULTA 11:16 UTC), which stay complete
   AS STRUCK and say the leg postdates them; every record struck from that
   hour on must declare it.
4. The reader's scope, stated so the zeros below are checkable: the leg is
   a FINANCING — cash received against product at agreed terms, carried
   apart from working capital and accreting (LunR's stream is *"a
   derivative financial liability, to be measured at fair value"*). The
   ordinary contract liabilities of a subscription or services business,
   customer deposits, billings in advance and prepaid income are working
   capital the flow already carries and are NOT this leg; where a file's
   balance sheet shows one, it is NAMED on the zero so the reading is
   visible, not silent. That scoping is the reader's; the owner may draw
   the line elsewhere.

**APPLIED 2026-08-30 — LUG.ST, the stream.** 2026-Q2 statement of
financial position p.30: *"Current portion of silver stream obligation
26,355"* + *"Silver stream obligation 663,990"* = **690,345 US$k**, two
stated parts added, both named (E66's precedence). Note 8 p.37: sold to
LunR Royalties Corp. on 28 May 2026 for cash up front, a life-of-mine
silver stream on Fruta del Norte. Earlier dates carry caption zeros
(31 March 2026 p.27 and 31 December 2025 p.51 present none; the 2020
stream credit facility was repaid in full in 2024).

| LUG.ST net debt at 2026-06-30 (US$k) | before E81 | after E81 |
|---|---:|---:|
| borrowings (current + non-current) | 0 + 0 | 0 + 0 |
| leases | 0 | 0 |
| pension deficit | **DATA MISSING** (no caption, no sentence) | DATA MISSING |
| asset retirement obligation (E68) | 8,910 | 8,910 |
| prepaid delivery obligation (E81) | — | **690,345** |
| cash | 507,130 | 507,130 |
| **net debt** | **DATA MISSING** on the pension leg | **DATA MISSING** on the pension leg |
| *if the pension leg were a zero (illustration only; not entered)* | *−498,220 (net cash)* | ***+192,125 (net debt)*** |

The leg moves Lundin Gold from net cash of about half a billion to net
debt of about two hundred million, on the owner's reading of what the
stream is. The pension leg is the owner's next question: the filing has
no caption and no sentence, and E78 has nothing to quote.

**WHICH OTHER FILES CARRY SUCH AN ARRANGEMENT.** None. Every other file
that reads its balance sheet takes a caption zero on the same page read
for `asset_retirement_obligation`, with the nearest caption named where
one exists: ACN, CTSH, GDDY, ULTA *deferred revenue* (services and
subscriptions billed in advance); NVR *customer deposits* (earnest money
on homes under contract); AUTO.L *deferred income 6.6*; KAR.ST *prepaid
income 1,132.2* (legal-information subscriptions); RVRC.ST *prepaid
income and accrued expenses* (orders paid before dispatch); RMV.L
*contract liabilities 3,485*; LIAB.ST *advance payments from customers
86*. **EXE is the one to look at:** its balance sheet carries *"Long-term
contract liabilities 975"* and *"Contract liabilities 253"* (note 6,
inside other current liabilities), **1,228 US$m together**, which the
10-K explains nowhere. They arrived as *"Long-term contract liabilities
1,287"* among the fair value of liabilities assumed in the Southwestern
merger (note 2), and Southwestern's own FY2023 10-K stated it had *"no
contract assets or contract liabilities associated with its revenues from
contracts with customers"* at 2023-12-31 — so they arose in purchase
accounting as the fair value of assumed contracts, not as cash received
against future delivery, and on that reading are not this leg. A caption
zero, the 1,228 named on the field and here, for the owner to confirm or
overturn. The XBRL files and the two earlier hand files (AUTO.L, LIAB.ST)
carry the zero VERIFIED `same_page` on the balance-sheet read already on
file (E68.1's enumeration, re-read for LIAB.ST's Q2 2026 p.15 and AUTO.L's
p.103 today); this session's files carry it UNVERIFIED like everything
else in them. **Six files carry no `asset_retirement_obligation` either
(BETS-B.ST, DECK, NKE, PNDORA.CO, SAP.DE, SYNSAM.ST)**: their net debt
was DATA MISSING on E68's leg before this ruling and stays so on both;
nothing was added to them.

**WHICH EARLIER RULING THIS AMENDS.** **E35** — a sixth liability leg
beside E35.1's and E68's. E68's date mechanism is generalised to a
datetime, not changed.

---

### E82 — depreciation mixed with impairment is DATA MISSING, not the line

**RULED 2026-08-30 by the owner. Written before the code.**

**THE RULE.** Where the only printed line combines depreciation and
amortisation with impairment charges, the field is DATA MISSING with the
combined line and its amount named on the field. An impairment is a
one-off write-down of an asset's value; depreciation is the recurring
cost of using it. A measure meant to show the recurring cost is wrong if
a one-off sits inside it, and the error runs the wrong way — it makes a
bad year look like a high-cost year rather than a year with a write-down.
Refusing is the honest answer; entering the combined line is not. **A
decomposition elsewhere in the filing is an E69 hand read, not a
refusal:** where the notes state the depreciation and amortisation
charges apart from the impairments, their sum is the figure, every part
named.

**WHAT THE CODE DOES.**

1. A figure may be entered with **`value: null` and a `page:`** — a NAMED
   ABSENCE. The loader keeps it; it is not present, so it is neither a
   value the basis reads nor an UNVERIFIED figure the gate refuses on.
2. The report's DATA MISSING section prints the named line beside the
   field: *"named (E82) — 2026-H1: p.22 'Depreciation, amortisation,
   impairment and remeasurement of disposal group held for sale 391' …"*,
   so the reader sees why the field is blank rather than a bare gap.
3. `depreciation_amortisation`'s description carries the rule.

**WHAT THIS BLOCKS — the leverage limb.** Less than the question
implies, and the exact answer is: **nothing mechanical today.**
`depreciation_amortisation` is read by no formula in the engine; its
FieldSpec has always said *"only to reconcile a stated EBITDA against
operating income; nothing here derives one from the other"*. Section 5's
leverage ratio (`net debt / EBITDA`, 5.3) reads the `ebitda` field, which
neither RKT.L nor IMB.L carries (both state only an adjusted EBITDA, an
APM); Filter 2's leverage limb (`filters.statement_ebitda`) reads the
vendor record's EBITDA series, not the manual file. So on both names the
leverage limb was DATA MISSING before this ruling and stays so; what E82
blocks is the RECONCILIATION a stated EBITDA would have needed, and the
temptation to form one from a line with a write-down inside it. Rule
4.2.5 stands on the issuer's own `net_debt_ebitda` (1.6x / 2.5x; 2.0x /
2.4x), which is unaffected.

**APPLIED 2026-08-30 — where the notes decompose the line, and where
they do not.**

| name | period | the combined line | decomposed? | result |
|---|---|---|---|---|
| RKT.L | 2025-FY | cash flow p.136 'Depreciation, amortisation and impairment 756' | **YES** — note 9 p.150: 'Amortisation 143' and 'Impairment 256' (Biofreeze); note 10 p.155: 'Charge for the year 356' and 'Impairment 1'; 143 + 256 + 356 + 1 = 756 exactly | **499 entered under E69**, all four parts named |
| RKT.L | 2026-H1 | p.22 'Depreciation, amortisation, impairment and remeasurement of disposal group held for sale 391' | **NO** — the interim's notes do not split it; the APM table's 'adjusted depreciation & amortisation' is an adjusted figure, not the statement's | **DATA MISSING, the line named** |
| IMB.L | 2025-FY | cash flow p.141 'Depreciation, amortisation and impairment 781' | **PARTLY** — note 12 p.159: 'Amortisation charge for the year 419', 'Impairment 6'; note 13 p.162: 'Depreciation charge for the year 155', 'Impairment 100'; note 14 p.163: right-of-use 'Depreciation and impairment (101)' — ITSELF COMBINED; 419 + 6 + 155 + 100 + 101 = 781 exactly, but the 101 cannot be split, so the recurring charge is somewhere in 574–675 | **DATA MISSING, every part named** — the owner may rule that a right-of-use line whose impairment is unstated is read whole (E72's shape), which would give 675 |
| IMB.L | 2026-H1 | p.25 'Depreciation, amortisation and impairment 326' | **NO** — the APM note states amortisation and impairment of intangibles 209 (173 acquired, 36 internally generated); depreciation is not stated apart | **DATA MISSING, the line named** |
| ZZ-B.ST | FY2025 | income statement p.77 'Depreciation/amortisation and write-downs of tangible and intangible fixed assets 33,337' | **YES** — notes 19–22 state 'The year's depreciation' 4,316 + 6,765 + 3,980 + 18,275 (right-of-use) = 33,336 and no write-down row in 2025 (1 of rounding) | the entered 33,337 stands (not read at the basis — the quarters carry the field); the decomposition is now on its page |
| NHY.OL | all | 'Depreciation and amortization expense' is a SEPARATE income-statement line; the cash flow's 'Depreciation, amortization and impairment' was never the one entered | n/a | unchanged |

**WHICH EARLIER RULING THIS AMENDS.** None; it applies **E5** (as
presented) with **E69** (a stated figure may be hand-read) to a line E5
would otherwise have taken whole, and names the case E72 might one day
be read to cover.

---

### E68.1 / E35.1 — second application, 2026-08-30: LUG.ST's pension leg is a caption zero on absence alone

**RULED 2026-08-30 by the owner.** Lundin Gold's balance sheet carries no
pension or post-employment caption and no sentence says there is none.
Under E68.1's shape — a caption absent in a business that plausibly has
no such obligation — an Ecuadorian single-mine operator with no
defined-benefit caption takes **`pension_deficit: 0`, `zero_basis:
caption`**, and the field records that this rests on ABSENCE ALONE, with
no sentence to quote: weaker than E78's `caption_statement`, and to be
revisited if the annual report carries a policy note. **The weakest zero
on the books, and named as such.**

**LUG.ST net debt at 2026-06-30 (US$k), every leg, once it forms:**
borrowings 0 + 0 (caption), leases 0 (caption), pension **0 (this
ruling)**, asset retirement obligation 8,910 (E68), prepaid delivery
obligation 690,345 (E81), less cash 507,130 = **net debt 192,125**. Before
E81 and this ruling the same legs would have read net cash of 498,220.

---

### E81 — second application, 2026-08-30: EXE's 1,228 US$m of contract liabilities are not this leg

**RULED 2026-08-30 by the owner.** The caption zero stands, for the reason
the reader gave: the balance was assumed at 1,287 in the Southwestern
merger (10-K note 2, fair value of liabilities assumed) and Southwestern's
FY2023 10-K stated it had *"no contract assets or contract liabilities
associated with its revenues from contracts with customers"*, so this is
purchase-accounting fair value of assumed contracts, not cash received
against a future delivery. **E81 reaches money received in advance; this
is not that.** The reasoning is on the field so a future reader does not
reopen it; **if a 10-K ever explains the balance as prepaid volumes, it
becomes an E81 leg** and the zero is wrong by 1,228.

---

### E83 — a stated margin outside the plausible band is accepted where the issuer prints it and the accounts explain it

**RULED 2026-08-30 by the owner. Written before the code.**

**THE RULE.** `FRACTION_BANDS` refuses an `op_margin` outside [-10, 1]
because it exists to catch a mistyped or derived margin (6.6 for 6.6%),
not to refuse an issuer's own stated figure that the accounts explain.
Karnov's Q4 2025 operating margin is 134.7% because the EHS divestment
gain sits in operating profit. **A stated margin outside the band is
accepted where the issuer prints it and the statements identify the
cause, with the cause named on the field; a margin outside the band that
the issuer does not print is still refused.**

**WHAT THE CODE DOES.** A figure key **`cause:`** on `op_margin` (manual
path), holding the statement's own explanation; `config.unit_problem`
skips the band for `op_margin` when a cause is supplied and refuses it as
before when none is. The cause never reaches any other banded field. The
watchlist quarter path is unchanged (its margins come from releases and
tags, and `cause:` is not in its schema); a release margin above 100%
still refuses there until the owner extends the key.

**APPLIED 2026-08-30 — KAR.ST 2025-Q4.** Operating income **895.7** MSEK
(p.11 'Operating profit (EBIT) 895.7') enters beside `op_margin` 1.347
(p.2 'EBIT margin, % 134.7%'), cause: *'Other operating income and
expenses 723.6'*, the EHS divestment gain, with 895.7 / 664.9 = 134.71%
agreeing at the printed tenth (E79). The TTM EBIT to 2026-06-30 now
forms from four quarters, so the **`PERIODS DO NOT MATCH` refusal on the
operating margin clears** — KAR.ST is refused on UNVERIFIED alone.

**WHICH EARLIER RULING THIS AMENDS.** The unit contract's band (SPEC.md
§2, FRACTION_BANDS) gains an exception for a stated, explained margin.

---

### E79.1 — a stated tenth keeps its precision: the `precision:` key

**RULED 2026-08-30 by the owner. Written before the code.**

**THE SEAM.** E79 reads precision from the entered margin's decimals, and
a printed 19.0% can only be typed `0.19`, which reads as a whole percent —
so RVRC's Q1 would have been accepted and its Q3 refused on the same
component rounding.

**THE RULE.** A figure key **`precision:`** on `op_margin`, in percentage
points as the issuer prints them — `1` (a whole percent), `0.1` (a
tenth), `0.01` (a hundredth) — overrides the decimals read from the
value. Where it is absent E79's reading stands. The band is still half a
unit, floored at 0.1pp (E79).

**APPLIED 2026-08-30 — RVRC.ST 2026-Q1 and 2026-Q3.** With `precision:
0.1` read correctly, 75 / 392 = 19.13% against 19.0% (0.13pp) and 105 /
487 = 21.56% against 21.4% (0.16pp) both **still disagree at the printed
tenth** — the whole-million rounding of the components, not the margin's
— so **neither enters**; both are left out and say so. The seam is closed;
the component-rounding question is unchanged and is the owner's.

---

### E78.1 — a policy sentence from the latest annual report serves until the issuer restates or contradicts it

**RULED 2026-08-30 by the owner, on RVRC.ST's pension zero.** E78's
application rule required the sentence to be the period's own document's
or adopted by it. Amended: **the most recent statement the issuer has
made serves** — RVRC's AR 2024/25 p.100 sentence stands for the 30 June
2026 zero because the year-end report of 2026-08-11 neither contradicts
nor restates it. The zero is entered `caption_statement` with the sentence
quoted and **its document and date named on the field**, so the age of the
evidence is visible there rather than hidden in a verdict.

**APPLIED 2026-08-30.** RVRC.ST FY2026 `pension_deficit` 0 → VERIFIED
(caption_statement): *"The group's pension obligations only include
contribution defined plans."* — Annual Report 2024/25, published
2025-10-15, for the year to 30 June 2025. RVRC.ST's UNVERIFIED count read
at the basis falls by one.

---

### E82 / E72 — second application, 2026-08-30: IMB.L's right-of-use line is read whole

**RULED 2026-08-30 by the owner.** Note 14's *"Depreciation and
impairment expense of right of use assets 101"* is a combined caption
whose impairment component is stated only approximately (that is, not at
all) — E72's shape, which reads such a caption whole. So IMB.L's FY2025
`depreciation_amortisation` = amortisation 419 (note 12) + depreciation
155 (note 13) + right-of-use 101 (note 14, whole) = **675**, an E69 hand
read with the combination named on the field. **The honest range is
574–675 and 675 is its upper end**; the impairments stated apart (6 + 100)
stay out. The half-year's 326 remains a named absence.

---

### E58.1 — a tag read of a SPACED xhtml is an honest second reader where the figures came from a separately published document: APN.L

**RULED 2026-08-30 by the owner, accepting the session's reasoning. First
application APN.L (commit dc3fa87).**

**THE QUESTION.** APN.L's annual report exists on the NSM only as the ESEF
package, whose text layer inserts spaces inside numerals ('107 .1', '(57
.8)', '250 ,000,000' — the AUTO.L defect). Its figures were therefore read
from the Final Results RNS of 2025-11-10, which carries the audited
statements and notes as clean text. Is the ESEF then an independent second
reader of what was read, or the document the figures could not be read
from?

**THE ANSWER: a second reader, on four grounds.**

1. The RNS (2025-11-10) and the ESEF annual report (2025-11-27) are **two
   separately published documents** carrying the same audited statements —
   more separation than AUTO.L had, where one report was compared against
   its own second rendering.
2. What is compared is not the text layer read by eye but the package's
   `ix:nonFraction` facts **parsed mechanically** — concept, context, unit,
   scale and the digits of the value string with every inserted space
   removed — extracted BEFORE any comparison, so nothing is read knowing
   the RNS number. 187 facts at APN.L.
3. The spacing defect **can only produce disagreement, never false
   agreement**: a dropped or doubled digit disagrees with the RNS, and no
   de-spacing choice exists for a string like '(57 .8)'. It can cost an
   agreement; it cannot manufacture one.
4. The file's own record had already named the tag-map as "a tag-map
   second reader for a later pass".

**THE FALLBACK.** E59 inside the RNS's own notes remains the route if this
judgement is ever struck: the RNS carries the notes, and their component
sums, roll-forwards and restatements are E59's shape. Reverting commit
dc3fa87 alone overturns the pass.

**APPLIED.** APN.L 2025-FY: 16 fields `cross_document` on the tag (three
on magnitude under E58's sign convention), three under E59 (the two
250,000,000 counts — the Directors' Report, the parent company's note and
note 11 restate note 21 — and the prepaid caption zero under E59.1); 16
UNVERIFIED read at the basis → 0. The package also tags Assets 75.0 and
PropertyPlantAndEquipment 2.0, which the file never entered — named, not
added.

**WHICH EARLIER RULING THIS AMENDS.** **E58** — extends the second-document
reading to a package whose text layer is defective, when the figures come
from another published document and the facts are parsed rather than
eye-read.

---

### E59.1 — a component sum that closes EXACTLY against a tagged total verifies a CAPTION ZERO

**RULED 2026-08-30 by the owner. First applications RMV.L, RKT.L, IMB.L,
APN.L (commits acef5ff, 4d6fcc0, f0086ed, dc3fa87).**

**THE RULE.** Where the tagged liability and provision captions sum
exactly to the tagged total, there is no room left for an untagged
caption, and that is an independent second read of the absence. An E25
caption zero — no borrowings caption, no decommissioning or restoration
provision, no prepaid-delivery caption — takes **`verified_kind:
cross_document`** under E59, citing the captions and the total they
exhaust. The captions are the ESEF package's (E58): a second rendering.
The printed balance sheet's own captions summing to its own printed total
is the same page checking itself, which E59 excludes.

**THE DISTINCTION FROM E22, named so a future reader does not reopen it.**
E22 forbids inferring a NUMBER the accounts do not contain — share capital
over par is not a count. A component sum that closes establishes that a
number DOES NOT EXIST: nothing is missing from the total. That is the
opposite operation — one derives a figure that is not stated, the other
proves an absence — and E22 is untouched by it.

**WHAT IT DOES NOT DO.** It verifies the ABSENCE OF A CAPTION, not the
classification of what the captions hold: RKT.L's 'Other provisions 37'
still carries E68.2's unquantified environmental obligations, IMB.L's
factory-closure and market-exit provisions stay named on the field, and
E68.2's and E81's own questions stand as they were. A sum that does not
close exactly verifies nothing. E78 is unchanged: a stated nothing is
`caption_statement`; a proven nothing is this.

**APPLIED 2026-08-30, every one read at its basis.**

| name | field | the captions and the total they exhaust |
|---|---|---|
| RMV.L | prepaid_delivery_obligation | current 32,568 + 3,562 + 3,485 + 501 + 428 = CurrentLiabilities 40,544; non-current 3,622 + 1,717 + 0 = 5,339; Liabilities 45,883 (£000) |
| RKT.L | asset_retirement_obligation | CurrentProvisions 90 + NoncurrentProvisions 55 = 145 = note 18's legal 108 + other 37 (£m) |
| RKT.L | prepaid_delivery_obligation | six current captions = 6,650; six non-current = 10,637; Liabilities 17,287 |
| IMB.L | asset_retirement_obligation | 55 + 197 = 252 = note 25's restructuring 101 + claims 91 + other 60 |
| IMB.L | prepaid_delivery_obligation | six current = 11,854; seven non-current = 11,429; Liabilities 23,283 |
| APN.L | prepaid_delivery_obligation | 0.6 + 17.1 = 17.7; 0.3 + 2.4 + 0.3 = 3.0; Liabilities 20.7 |

Without this ruling all four names would refuse again on these six.

**WHICH EARLIER RULING THIS AMENDS.** **E59** — extends the component sum
from a stated figure to a stated absence. E25's forms are unchanged: the
zero still needs its `caption` form, and this ruling sits on top of it, as
E78 does.

---

### E84 — SAP.DE's borrowing legs at 2026-06-30 are financial liabilities EX-LEASES, formed from the stated operands of note (E.2)

**RULED 2026-08-30 by the owner, on `reports/E41-SAP-2026-08-30.md` and
its addendum. Written before the code.**

**THE RULE.** For SAP.DE at 2026-06-30, E35's `financial_liabilities_current`
and `financial_liabilities_noncurrent` mean **financial liabilities other
than leases**, formed per E71 from the stated operands of the Half-Year
Report 2026's note (E.2) Liquidity, p.39: **current 1,478 (financial debt)
+ 207 (other financial liabilities); non-current 6,726 + 361.**
`lease_liabilities` is the note's stated total **1,735** (281 + 1,454).
Each field's provenance names both operands and the page.

**WHY.** E35 says *financial liabilities*, not *financial debt*; the 568 of
other financial liabilities is a claim on the company and counts as debt,
which is the conservative side; and the operands reproduce the 2026-08-26
record's consolidated 10,507 exactly, while the note's printed total
10,508 is the issuer's rounding — the reading explains the discrepancy
rather than leaving it open. E71's condition is met: the issuer presents
the operands inside one line, "Financial liabilities", on the face of the
balance sheet (p.25) and totals them in the note.

**WHAT IT DOES NOT DECIDE.** The FY2025 annual entry held the 20-F's
borrowings tags, which the same note shows to be NOMINAL volumes (1,600 /
4,550 against carrying 1,598 / 4,194). On the owner's instruction those
legs are corrected to the carrying basis of the same quantity — financial
debt 1,598 / 4,194, cited to the note's 12/31/2025 columns — and whether
this ruling's ex-lease reading extends to that entry (1,598 + 198 / 4,194
+ 397) is named on the field, not decided.

**WHICH EARLIER RULING THIS AMENDS.** None — an application of E35, E14
and E71 to one filer at one date. E41's consolidated-line hand input is
retired for this date: the store carries the split.

---

### E85 — a leg is NOT PRESENTED, distinct from a zero, when a full report has been searched for the concept and the search is recorded

**RULED 2026-08-30 by the owner. Written before the code.**

**THE RULE.** Where a full report — the statements and every note — has
been searched for a concept and the concept appears nowhere, the leg is
**NOT PRESENTED**: it enters the bridge at nil, and the run record records
the search — **document, scope, date**. This is not an E25 zero. E25's zero
is a claim the issuer's page supports (a caption shown as nil, a sentence,
a subtotal that leaves no room); NOT PRESENTED is a fact about a search,
recorded so that the search can be repeated on the next report. **E25 is
unchanged for actual zeros**: where the issuer states the thing exists, or
states that it does not, E25's forms govern and this state is refused.

**THE FORM.** `not_presented:` on the field, with `document`, `scope` and
`date`, beside a `page:` naming what the balance sheet presents instead;
no `value`, no `status`, no `zero_basis`. The gate does not refuse on it —
there is no figure to verify; the report prints it in the E25 table as
NOT PRESENTED with the search; the run record's input carries the search
in its provenance and its verification column reads NOT PRESENTED.

**APPLIED 2026-08-30 — SAP.DE at 2026-06-30.** `asset_retirement_obligation`
(E68) and `prepaid_delivery_obligation` (E81): the E41 report's addendum §4
establishes that the Half-Year Report 2026's fifty pages — the statement
of financial position p.25 and notes A.1–G.4 — carry neither concept
(Provisions 119 / 611 undecomposed; contract liabilities 9,843 / 136 are
E81's ordinary kind).

**WHICH EARLIER RULING THIS AMENDS.** **E25** — a fourth state beside its
three zero forms, for a concept absent from a whole report rather than a
line the issuer shows as nil. **E68.1 / E68.2 and E81** — where their
caption zero on an interim would have been UNVERIFIED and refused, NOT
PRESENTED may stand instead once the whole report has been searched.

---

### E86 — a cumulative year-to-date column is stored as operands, and the store computes the quarter as a coded transform

**RULED 2026-08-30 by the owner, settling E41's open question. Written
before the code.**

**THE RULE.** Where an issuer prints a flow only cumulatively (Q1, Q1–Q2,
Q1–Q3, Q1–Q4), a quarter's figure may be stored as its two stated
columns — the cumulative column and the prior cumulative column — **each
with its own page reference**, and the store computes the difference as a
coded, tested transform: the E16 / E18 pattern. **A hand-computed
difference remains forbidden** (E22): the operands are what the accounts
state, the arithmetic is the code's, and both are printed. A first-quarter
column is the quarter itself and is entered as `value`. A cumulative
column stored without its prior is an operand on file and no quarter —
DATA MISSING for the quarter, the column named.

**THE FORM.** `cumulative:` and `cumulative_prior:` with
`cumulative_prior_page:`, on a quarterly `periods:` flow only; never
beside `value:`. The report prints "cumulative − prior = quarter" with
both pages.

**APPLIED 2026-08-30 — SAP.DE `capex_combined`.** 2025-Q3: −559 (Q1–Q3
2025, `sources/sap-q32025.pdf` p.13 and p.18) less −358 (Q1–Q2 2025,
`sources/sap-q22025.pdf` p.13 and p.18; restated `sap-q22026.pdf` p.15);
2025-Q4: −739 (Q1–Q4 2025, `sap-q42025.pdf` p.14 and p.19; the 20-F tags
the same) less −559; 2026-Q1: −238 stated (`sap-q12026.pdf` p.9 and p.12);
2026-Q2: −354 (Q1–Q2 2026, `sap-q22026.pdf` p.11 and p.15) less −238. The
2026-08-26 record's hand input `capex_combined` −735 is retired: the four
quarters sum under E19, off the store. The H1 2026 equity-settled
share-based payment expense **706** (Half-Year Report note (B.3), p.31) is
stored on 2026-Q2 as a cumulative operand without a prior — the Q1 2026
statement states only the total 285 — and `sbc` keeps filling from FY2025
under E41 until the first-quarter equity-settled figure is stated.

**WHICH EARLIER RULING THIS AMENDS.** **E41** — closes "whether a
cumulative-minus-cumulative quarter may live in the store": as operands,
yes; as a hand-computed difference, no. **E22** unchanged in substance —
nothing is inferred; **E16 / E18** extended from a net of two figures to a
difference of two columns.

---

### E87 — a fair value the store cannot rebuild is superseded under E39

**RULED 2026-08-30 by the owner. Written before the watchlist edit.**

**THE RULE.** Where the store can no longer form the figure a run record
replays to — a leg the record carried by hand, or a leg later rulings
added that the store lacks — the fair value is treated as **superseded
under E39**: `fv_base`, `tier` and `mbp` are set to null with the note
*"superseded: the store cannot rebuild it; re-strike when it forms end to
end"*; `stop_price` is untouched. The run record stays linked as history
and still replays. **Replay is not re-strikeability**, and a number the
runner prints from a record nobody can strike again is E39's "live
instruction from a dead calculation" by another route.

**APPLIED 2026-08-30 — SAP.DE.** `fv_base` 139.48, `tier` 1 and the derived
MBP 96.21 nulled; `stop_price` was already null (sold 2026-08-26, E42).
Re-strike only when the store forms the number from a complete run record
with zero hand inputs. AOS's 62.66 is not on the watchlist and nothing is
nulled there; its record stands as struck and its E70 block is named in
the handover.

**WHICH EARLIER RULING THIS AMENDS.** **E39** — extends its trigger from
"method superseded" to "store cannot rebuild". **E32**'s marker is
unchanged.

---

### E88 — where the §5 window has no weighted-average diluted count, the divisor is the most recent ANNUAL weighted-average diluted count; a period-end count is never promoted

**RULED 2026-08-30 by the owner, deciding the divisor question
`reports/TRIAGE-2026-08-30.md` Part A surfaced. Written before the code.**

**THE RULE.** Where no weighted-average diluted share count exists for the
§5 window, the divisor is the **most recent annual weighted-average
diluted count under E41's annual-only rule**, and the run record **flags
the basis mismatch** — an annual average dividing R12M flows — beside the
divisor, dated to the annual window it belongs to. A count at the window
end — stated, or formed as E80's issued-less-treasury pair — **stays memo
per E38 and is never promoted to divisor.** For SAP.DE at the R12M to
2026-06-30 the divisor is FY2025's **1,175,000,000**
(`ifrs-full:AdjustedWeightedAverageShares`, 20-F 0001104659-26-020058);
the Half-Year Report's pair (issued 1,228.5m − treasury 74.3m, note (E.1)
p.38) remains on file as the memo it is.

**RATIONALE, recorded with the ruling.** The point-in-time pair gives
fewer shares and a higher fair value — 142.00 against the 139-range on
the same store. Promoting it would relax a rule in the direction that
flatters the number.

**WHICH EARLIER RULING THIS AMENDS.** **E75 / E75.1 — reversed.** The
window-end count, diluted or basic, is no longer a divisor of any kind;
records struck under E75 remain complete as struck, and their
`divisor_basis` labels stay readable on replay (E39's line: replay is
history, not licence). **E38** — unchanged and extended in scope: the E80
pair joins `shares_point_in_time` as memo, never the divisor. **E41** —
its annual-only rule governs the divisor again wherever no window average
exists.

---

### E89 — E84's ex-lease operand reading applies at every date: a field means the same stated line at every date

**RULED 2026-08-30 by the owner, deciding what E84 named and left open.
Written before the store correction.**

**THE RULE.** The ex-leases operand reading E84 gave SAP.DE's
`financial_liabilities_current` / `financial_liabilities_noncurrent` at
2026-06-30 applies at **every date**, not only 2026-06-30. A field means
the same stated line at every date; one field may not carry one quantity
at the interim date and another at the annual date.

**APPLIED 2026-08-30 — SAP.DE FY2025.** The annual entry is corrected to
the same shape from the Half-Year Report 2026's note (E.2) Liquidity,
p.39, 12/31/2025 carrying-amount columns: current **1,598 (financial
debt) + 198 (other financial liabilities) = 1,796**; non-current **4,194
+ 397 = 4,591**; each operand cited to its stated line. `lease_liabilities`
stays the tagged 1,684 (the note's 254 + 1,430). The E59 component check
still closes: the note's carrying components sum to its printed 2,050
current and 6,021 non-current exactly; their total 8,071 beside the
note's printed 8,070 is the issuer's rounding, the same discrepancy E84
recorded at 6/30/2026 (10,507 against 10,508).

**WHICH EARLIER RULING THIS AMENDS.** **E84** — decides its named-open
extension to the FY2025 entry. E35, E71 and E14 are unchanged; the
2026-08-26 run record is history under E87 and is not edited.

---

### E90 — the MBP is the BASE-case value × the tier cushion; the cushion covers model and input error, not scenario risk

**RULED 2026-08-30 by the owner, on `reports/THRESHOLD-REACHABILITY-2026-08-30.md`.
Written before the code.**

**THE RULE.** The maximum buy price is the **BASE-case value × the tier
cushion: tier 1 × 0.85, tier 2 × 0.75, tier 3 × 0.65** (tier 3 continues
the 0.10 step; decided by the owner at this ruling's read-back). This
supersedes E28's bear-value arithmetic. **The cushion's job is named:** it
covers **model and input error** — the class of fault REVIEW-4 actually
found (double-charged interest, a wrong divisor, missed SBC; typically
5–15% of value) — and **NOT scenario risk, which the pre-registered
growth views carry.** Bear and bull values continue to be computed and
printed with every strike — they become information, not the buy line.

**RATIONALE, recorded from the threshold report.** At the old MBP the
bear case alone returns 10.0–16.1% — above the 9.5% hurdle in every case
measured — so a cushion on the bear value answers the same question
twice: the price already assumed the bear case, and then discounted it
again. And the only prices that reached the old thresholds on current
cash flows (ACN and CTSH, May–July 2026) sat at 47–59% drawdowns from
the 52-week high, at or beyond Gate 1's own 50% ceiling.

**WHAT STANDS.** Records struck earlier stand — MBP is computed, never
stored, so no record is invalidated; the runner derives the new figure
from the same linked records. E28's engine, the pre-registration order
and g* are untouched. E32's superseded-definition mark is unchanged: the
retained `fv_base_x_tier` history keeps its old multipliers as the record
it is. E77's one-tier-stricter shift applies to the tier before the
cushion, as before.

**WHICH EARLIER RULING THIS AMENDS.** **E28** — its MBP definition
(bear-case value × tier cushion) is superseded; everything else in E28
stands. **§5.3's multipliers** (0.80 / 0.70 / 0.60) are replaced by
0.85 / 0.75 / 0.65, applied to the base-case value.

---

### E91 — where all four basis quarters state a per-quarter weighted-average diluted count, the divisor is the coded day-weighted average of the four

**RULED 2026-08-30 by the owner, deciding the E-candidate recorded on
SAP.DE's divisor field at the read-back. Written before the code.**

**THE RULE.** Where the issuer's quarterly statements print a per-quarter
weighted-average DILUTED share count for **all four quarters of the §5
basis**, the divisor is the **coded day-weighted average of those four
stated figures** — the E86 pattern: stated operands, computed result,
each operand with its own page reference; the weights are each quarter's
own day count off its period bounds, and the arithmetic is the code's,
never a hand's. This supersedes **E88's annual fall-back for such
issuers**; **E88 remains the rule where the quarterly figures do not
exist.** E38 is unchanged: a stated window average still wins outright;
a period-end count stays memo, never the divisor.

**APPLIED 2026-08-30 — SAP.DE.** The four EPS footnotes state diluted
**1,172 / 1,172 / 1,168 / 1,158 million** (Q3 2025 `sap-q32025.pdf` p.10
fn.1; Q4 2025 `sap-q42025.pdf` p.11 fn.1; Q1 2026 `sap-q12026.pdf` p.7
fn.1; Q2 2026 `sap-q22026.pdf` p.8 fn.1). Day weights off the period
bounds: 92 / 92 / 90 / 91.

**WHICH EARLIER RULING THIS AMENDS.** **E88** — demoted to the fall-back
for issuers whose statements do not state the four quarterly averages;
its memo rule for window-end counts is unchanged. **E41** — its
"quarterly averages are never summed" stands: nothing here is summed by
hand; the operands are stated and the transform is coded and tested
(E86's licence). The open E-candidate on `config/manual/SAP.DE.yaml`'s
divisor field is DECIDED by this ruling.

---

### E60 — a field no method reads does not block section 5; the read set follows the file's own chain

**HEADING WRITTEN 2026-08-30 from the ruling's implementation in
`vss/manual.py` (`NEVER_A_SECTION5_LEG`, `INTEREST_MARKER_FIELDS`,
`interest_read_names`, `unread_by_e60`, `section5_reads`); the ruling's
original prose is NOT on file — this entry records its content, not its
dictation, and says so.**

**THE RULE, as the code carries it.** E21's refusal set follows what
section 5 ACTUALLY reads for THIS file, not `FieldSpec`'s blanket
declaration. Two declared fields are read by no live path for any file —
`income_tax_paid` (still read by the scale gate; its role inside FCF0 was
never wired) and `proceeds_from_disposals_ppe` — so both stay UNVERIFIED
on the figure and NAMED in the run record, and neither refuses. The
interest marker's six fields are read dynamically (E34 chooses one shape
per filer): the shapes not chosen leave the read set — a filer whose
operating cash flow bears no interest never forms `net_interest_paid` —
while `net_finance_costs` and its own operands stay read regardless
(E25's coverage denominator; E61's leg is `finance_costs_period`).

**WHERE IT STANDS.** Applied throughout `section5_reads` /
`unread_reason`. E91 (2026-08-30) extended the same principle in the
opposite direction: operands the chain DOES read (the divisor's four
quarterly counts) are ADDED to the read set. E57 remains headingless —
searched 2026-08-30 across FRAMEWORK-EDITS, FRAMEWORK, vss/, tests/ and
reports/: no citation and no content survives to write a heading from,
and a heading invented from nothing would be worse than the gap.

---
### E92 — a report-date refresh FETCHES, EXTRACTS and REPORTS; it never decides

**RULED 2026-08-31 by the owner, on building the report-date refresh.
Written before the code.**

**THE RULE.** On a name's catalyst date — the dated event §3's Gate 5
names and the entry carries in `catalyst_date` — the tool may go and get
the filing. It may do **three things and no fourth**:

1. **FETCH** the filing by whatever route the issuer allows.
2. **EXTRACT** its figures into the store, under the provenance rules
   below.
3. **WRITE A REPORT** — `reports/REFRESH-<TICKER>-<date>.md`.

**IT MAY NEVER** write `fv_base`, `tier`, `mbp`, `stop_price` or `status`
to `config/watchlist.yaml`, and **it never scores a gate**. Not Gate 1's
dislocation, not Gate 2's classification, not §4.2's kills, not §4.3's
flags, not §4.4's score. A refresh that fetched a quarter in which
revenue fell twice **reports the two figures and says nothing about
§4.2.1** — the kill is a verdict, and a verdict is the owner's.

**THE PROVENANCE IS THE ORDINARY PROVENANCE, and this ruling invents
none.**

- **A tagged SEC fact enters VERIFIED / `tagged`** — E40 rule 1 exactly:
  verified by provenance, tag + accession + filing date on the figure's
  own page line, because there is no transcription to have got wrong.
- **Anything read from a PDF enters UNVERIFIED** and **waits for the
  owner's read-back**. It is a figure a machine transcribed off a
  rendered page; E40's three kinds all record a reading that a person or
  a second document did, and a refresh is neither. The read-back that
  promotes it is unchanged: E40's `same_page`, E58/E58.1's second
  document, E59/E59.1's separately-prepared note.
- **A refresh may NOT claim E85's NOT PRESENTED.** That state stands on a
  whole report having been SEARCHED — document, scope, date — and a
  fetch that fails to find a tag has searched a tag map, not a report. An
  absent concept is **DATA MISSING** in a refresh, and the report says
  which concepts it did not find so the owner's search knows where to go.

**WHAT IT MAY NOT DISTURB.** A refresh **never overwrites an existing
VERIFIED figure** — of any kind, `tagged` included. **New periods are
ADDED**; where a fetch returns a different value for a figure the store
already holds, the difference is **REPORTED as a conflict and the store
keeps what it has**. E39/E87 are untouched: a refresh does not re-strike
and does not null a fair value. A fair value struck before the refresh
**stands as it is** until the owner re-strikes it, and the report may say
what a re-strike WOULD give — **marked as information, and not written.**

**WHERE A ROUTE IS CLOSED.** For an issuer whose site refuses automated
requests — `sap.com` returns 403 to this tool, the finding recorded in
`reference/FETCHER-SURVEY.md` §5 — **nothing is attempted and nothing is
dressed up as a browser.** The refusal is a finding, as that survey
already says: the report **names the document needed and its expected
URL where one is known**, so the owner can download it by hand, and **no
partial figure is written to the store** from a route that did not
complete.

**HOW IT SURFACES.** A refresh that changes a name's numbers appears as
**NEEDS OWNER at the top of the nightly output** — ticker, report path,
and what each waits on (a read-back, a tier, the owner's write). It is a
**pointer, not a summary**: the report holds the figures. **Nothing
downstream moves until the owner acts** — no MBP is re-derived off a
refreshed figure, because an MBP is derived from a linked run record and
a refresh links none.

**THE NOTIFICATION IS OUTBOUND-ONLY.** Where a topic is configured, the
run posts the same few lines to it after the nightly report. **Nothing
reads from the topic, ever** — not a reply, not a command, not an
acknowledgement. A tool that took instruction from a channel anyone can
publish to would be a tool that decides on a stranger's word, and this
ruling's whole subject is that it decides on nobody's. An unset topic is
**silence, not an error**, and a failed post is **logged and never fails
the run**: a notification is a convenience laid beside the report, and
the report is the record.

**WHICH EARLIER RULING THIS AMENDS.** **None.** It ORDERS work that had
no order: E40 already said what a tagged fact is worth, E58/E59 what
promotes a read figure, E85 what a recorded search is, and E39/E87 what a
fair value rests on. E92 says WHO may do which of them and WHEN — and
that the fetching half of the work is allowed to run unattended precisely
because the deciding half is not.

---
#### E92 — the refresh is NOT SCHEDULED, decided by the owner 2026-08-31

**DECIDED at the build's read-back. Recorded as given, beneath the ruling
it qualifies.**

**THE DECISION. `vss refresh` runs BY HAND and is not on a timer.** The
owner runs `vss refresh --due` himself on report weeks. No systemd unit,
no cron line, no wrapper that calls it from the nightly run.

**THE REASON, in the owner's terms:** a refresh WRITES INTO
`config/manual/`, which is a **git-tracked configuration directory**, and
unattended writes into tracked config are not something to have running
while he sleeps. The nightly `vss run` is a different animal and stays on
its 22:30 timer: it writes only `data/` and `reports/`, and its
`ReadWritePaths` says exactly that.

**WHAT A FUTURE SESSION MUST DO BEFORE SCHEDULING IT.** Nothing here is a
technical obstacle — a timer would work, and `deploy/vss.service` would
need `ReadWritePaths` widened to `config/manual` for it to. **That
widening is the decision, not the plumbing.** So: **do not add a timer,
a cron line or a nightly call to `refresh` on the ground that it would be
convenient.** It is decided, and re-deciding it is the owner's act,
recorded as a new dated entry beneath this one.

**What is scheduled, and remains so:** the nightly run surfaces NEEDS
OWNER from whatever a hand-run refresh last left, and posts the pointer.
That is the automatic half, and it decides nothing either.

---

### E93 — a scheduled screen may SNAPSHOT, RANK and REPORT; it never enters a name

**RULED 2026-08-31 by the owner, deciding the six questions
`reports/SCREEN-SCHEDULE-PROPOSAL-2026-08-31.md` put. Written before the
code. E92's shape, and for a related but distinct reason.**

**THE RULE.** The screener may run unattended, weekly. It may **snapshot**
the universe's prices, **fetch** the fundamentals its ranking key needs,
**rank** them, **store the ranking**, and **write a report and a pointer**.

**IT MAY NEVER WRITE `config/watchlist.yaml`, and it never enters a name as
PIPELINE.** The scheduled unit does not pass `--write-pipeline`, and a guard
compares the watchlist's bytes either side of the run and stops it if they
differ — the rule enforced by code, as E92's is.

**WHY `--write-pipeline` IS THE LINE, and why it is a harder line than
E92's.** Entering a name as PIPELINE **stamps `dd_at_entry` and
`peak_date`, and E12 FREEZES Gate 1 at that moment.** The frozen reading is
what the dislocation verdict is struck on from then on, and leaving PIPELINE
takes a named information event. **So a timer passing `--write-pipeline`
would freeze a catalyst window on an arbitrary Saturday, at whatever the
previous close happened to be** — a dated analytical judgement made by a
clock.

And it is worse than E92's case in one specific respect, which is the reason
this ruling exists rather than an extension of that one: **a fair value
written in error is undone by re-striking it; a frozen Gate 1 is not.** E12
exists precisely to stop the band being re-read, so the ordinary correction
is unavailable. The entry would have to be removed and re-made, and the
record of the first stamp would remain. **An irreversible write is not a
thing to schedule.**

**WHY THE SCREEN MAY BE SCHEDULED WHERE THE REFRESH MAY NOT.** The two look
alike and are not. `vss refresh` writes into `config/manual/`, a
**git-tracked configuration directory** holding figures with VERIFIED flags
— which is why it stays a hand act (the owner, 2026-08-31, beneath E92). The
screen writes **`data/` and `reports/` only**: exactly what
`deploy/vss.service`'s existing `ReadWritePaths` already permits, needing no
widening of anything. **Its inputs are fetched vendor figures, not tagged
facts:** they live in the screener's own sqlite, never enter
`config/manual/`, and never acquire a VERIFIED flag of any kind — E40's
three kinds do not reach them, and E7 already records what a vendor's
`Gross Profit` is worth. **The screen produces a CANDIDATE LIST, not a
figure store**, and that is the whole of why a clock may run it.

**WHAT CHANGE IS WORTH A POINTER — decided, with what was REFUSED recorded
beside it.**

- **A name ENTERING or LEAVING the top 10** — by POSITION in the ranked
  list, not by the value of the combined rank, which is a sum of two
  placings and ties freely. Ties break alphabetically, which `vss/ranking.py`
  already does and states as a deliberately arbitrary rule, so the ordering
  is reproducible and the boundary does not wobble on sort instability.
- **A name crossing from OUTSIDE the top 20 into the top 10 in one step** —
  a jump that size is not noise.
- **REFUSED: any pointer on movement INSIDE the top 20.** The key sums two
  placings across ~200 ranked candidates; a name moves several places on a
  price move alone, with nothing in its accounts changed, and a weekly
  cadence samples exactly that. **This is E11's finding in different
  clothes** — a name left the dislocation band while sitting still, because
  the window moved under it. **A pointer that fires on wobble trains its
  reader to ignore the pointer**, which costs more than the information it
  carries. Decided by the owner on that reasoning.

**THREE FURTHER EVENTS, all firing:**

1. a name entering the top 10 **that is already on the watchlist** — the
   action differs entirely from a new name, and for a **DROPPED** one it is
   a contradiction worth seeing;
2. a name **ranked last week and now unrankable or stale** — a DATA event,
   not a market one, and how a feed or tag-map breakage announces itself;
3. **the run not completing.**

**AND THE THIRD SUPPRESSES THE OTHER TWO AND THE CROSSINGS.** The
fundamentals step fetches one ticker at a time with backoff; a throttled or
partial fetch drops names out of the ranking for reasons that have nothing
to do with the market. **A run whose ranked coverage falls short of the
previous run's sends NO change pointer at all** — it reports that it was
incomplete, names the shortfall, and stops. **A phantom "eight names left
the top 10" would cost the whole chain its credibility**, and a chain nobody
believes is worse than no chain.

**RETENTION.** The last **four** snapshots are kept and older ones pruned;
**every ranking is kept forever** — the rankings are kilobytes and are the
only thing a later comparison can stand on, while the price snapshots are
~235 MB apiece. Pruning deletes only `data/screener_snapshots/<date>/`
directories, never a ranking, never a manifest, and never anything under
`config/` or `reports/`.

**THE NOTIFICATION** follows E92 unchanged: **the same topic**, outbound
only, **nothing ever read from it**; an unset topic is silence rather than
an error; a failed POST is logged and never fails the run.

**WHICH EARLIER RULING THIS AMENDS.** **None.** It stands beside E92 —
same shape, different subject and a different reason for the same posture:
E92's line is that a figure's meaning is the owner's; **E93's is that an
irreversible stamp is not a thing a clock may make.** **E12** is untouched
and is the reason for the line. **E5/E6**'s ranking key, **E7**'s finding on
vendor gross profit and **E11**'s on a moving window are all read here and
none is changed.

---

#### E93 — the coverage tolerance is 2%, accepted by the owner 2026-08-31

**DECIDED at the build's read-back. Recorded as given.**

E93 ruled that a run whose ranked coverage falls short of the previous
run's **sends no change pointer**, and deliberately put **no figure** on
"short" — the build chose 2% and said at its own definition that the
number was chosen rather than derived.

**The owner accepts 2% and rules it as his, in his terms: 2% of ~216
ranked names is FOUR NAMES — tight enough to catch a throttled fetch,
loose enough not to go silent on ordinary attrition.** It carries his
authority from here, not the build's.

`COVERAGE_TOLERANCE` in `vss/screenwatch.py`, and every run prints the
comparison it was applied to.

---

### E94 — the ranked screen may print g\* and a §5 READINESS; an INDICATIVE value needs every leg VERIFIED, and is never a strike

**RULED 2026-08-31 by the owner. Written before the code. E93's shape, and
its subject is the step between a ranked name and a valued one.**

**THE PROBLEM IT SOLVES.** The ranked list says which names are cheap on
two vendor ratios. It says nothing about **what it would cost to value one
properly**, and that cost is the whole of the work: a name whose store is
complete is an evening's reading away from a fair value, and a name with no
store at all is a week away. **Today the owner cannot tell those two apart
by looking at the list**, so the cheap wins are invisible.

**WHAT THE SCREEN MAY NOW COMPUTE AND PRINT, per ranked name:**

1. **g\*, the market-implied growth at the current price** — E28's own
   figure, solved by `valuation.implied_growth` against the store's legs.
   **A g\* ABOVE r is a number, not a refusal**: the old cap at the hurdle
   rate was removed after REVIEW-4 (report C 9.3 #1) because a ten-year
   explicit horizon with a terminal rate fixed below r is finite and
   strictly increasing in g, so every price above the g=0 value has an
   answer. The solver refuses only at its own bounds — beyond
   `SOLVER_MAX_GROWTH`, or below a company shrinking 90% a year — and
   **that refusal is an INPUT fault, reported as one, never a verdict about
   the company.**
2. **A §5 READINESS ASSESSMENT** — which legs the store already holds,
   which are **DATA MISSING**, which are **UNVERIFIED and therefore
   blocking under E21**, and **whether a complete run record could form
   with ZERO HAND INPUTS**. Beside it, **which route the issuer's figures
   come through** — automatic (SEC XBRL, the Nordic feed) or a hand
   download (E92's registry).

**AN INDICATIVE FAIR VALUE — the narrow permission, and its four fences.**

The screen may compute and print a fair value **ONLY** where:

- **every leg §5 reads is PRESENT**, and
- **every one of those figures is VERIFIED by provenance under E40** — a
  tagged fact, a second document, a separately-prepared note, a caption
  statement. **A single UNVERIFIED figure the basis reads forbids it**, and
  a PDF-sourced figure awaiting the owner's read-back is exactly that
  (E92).
- **It is NEVER formed from screener or Yahoo fundamentals.** Those are the
  vendor figures the ranking key runs on; E7 already records what a
  vendor's `Gross Profit` is worth, and they never enter `config/manual/`
  and never carry a VERIFIED flag. **The indicative value comes off the
  STORE or it does not exist.**
- **It requires the owner's PRE-REGISTERED growth view** (E28). Where none
  is registered the name prints **READY — NEEDS GROWTH VIEW and nothing
  more.**

**AND THE GROWTH VIEW IS NEVER INFERRED, DEFAULTED OR BORROWED FROM A
PEER.** Not from a sector median, not from the name's own history, not from
a comparable already registered — RMV.L's view is on file as having been
carried across from AUTO.L's by analogy and is marked PROVISIONAL for that
reason, which is the closest this project has come and is already flagged.
**g is the owner's judgement about a business, and a screen that supplied
one would be answering the question the framework exists to make him
answer.** A view the code cannot read is **NOT a missing view**: it is
reported as *a view file exists that this parser could not read*, so the
owner sees the difference between "you have not written one" and "I could
not read the one you wrote".

**WHAT AN INDICATIVE VALUE IS NOT.** It is **printed and nothing else**:

- it is **never written to `config/watchlist.yaml`** — not `fv_base`, not
  anything;
- it **never gets an MBP**. E90's MBP is base value × tier cushion, and a
  **tier follows a §4.4 score, which follows the E76 reading** — none of
  which a screen has done. A price with no tier has no MBP (E28), and that
  is a legitimate state, not a gap to fill;
- **it never becomes a strike.** A real fair value is struck on the owner's
  pre-registered view, through the tool path, into a linked run record he
  writes. **The indicative figure is a signpost saying the strike is now
  cheap to make** — and E39/E87 are untouched: nothing here supersedes,
  nulls, or replaces a struck value.

**WHY THIS IS SAFE WHERE THE SCREEN'S OTHER OUTPUTS ARE NOT.** E93 let a
clock run the screen because it produces a candidate list rather than a
figure store. This ruling lets it produce a FIGURE — and the fence that
makes that safe is that **the figure is computed from figures a person has
already verified**, by the same engine, on the same basis, with the owner's
own growth rate. **It adds no new evidence and takes no new liberty; it
only saves the owner from running the strike by hand to find out whether
it was worth running.** Where any of that is untrue, the name gets g\* and
a readiness line, which are facts about a STORE and not claims about a
company.

**WHICH EARLIER RULING THIS AMENDS.** **None.** **E28**'s
pre-registration order is untouched and is the reason for the fourth
fence. **E40** supplies the verification test. **E21** supplies the
blocking rule. **E90** is untouched — no MBP is computed here. **E93** is
extended in subject, not relaxed: the screen still writes nothing to the
watchlist and still enters no name.

---

### E95 — a superseded growth view is marked `## SUPERSEDED` and stops being READ; it does not stop being KEPT

**RULED 2026-08-31 by the owner, on GDDY's view file reading UNREADABLE.
Written before the code.**

**THE PROBLEM.** E76 requires that a changed growth view be re-registered
**with the old view left in the record, superseded, never overwritten** —
and GDDY's file does exactly that: `Base case FCF growth, 10 years: **3%**
(was 5%)` on line 8, and the first view's `Base case FCF growth, 10 years:
5%` further down. **Two rates under one label, both correctly present, and
E94's parser refuses to choose between them** — rightly, because picking by
position would be inventing a convention nobody ruled.

So the file obeys one rule and is unreadable under another. **This ruling
supplies the convention, rather than letting a parser guess at one.**

**THE RULE.** In a file under `reference/growth-views/`:

- **A superseded block opens with a `## SUPERSEDED` heading.**
- **A reader skips everything beneath that heading until the next `##`
  heading**, at any level of the same depth.
- **The live rates are the ones OUTSIDE such a block.**

**E76 IS UNCHANGED AND THIS IS THE POINT.** The superseded view **stays in
the file**, verbatim, with its date and its reasons. It simply **stops
being read**. Nothing is deleted, nothing is edited, and the record of what
the owner believed on an earlier date remains exactly where E76 put it —
which is the whole reason that requirement exists and the reason this
ruling marks rather than removes.

**WHAT IT DOES NOT LICENSE.** The skip is the ONLY disambiguation
permitted. **Where a label still appears twice with different values
outside a superseded block, the view remains UNREADABLE and refuses** —
E94's rule is untouched. A parser may never resolve an ambiguity by
position, by recency, by picking the first, or by any other convention that
has not been ruled here. **A file this rule cannot disambiguate is reported
as unreadable, and the owner edits it.**

**APPLIED 2026-08-31 — GDDY.** Its file already carried
`## SUPERSEDED — the first view, 2026-08-30 (kept in the record, never
edited)`; the convention was in practice before it was in writing, and this
ruling only makes the parser honour what the file already said.

**WHICH EARLIER RULING THIS AMENDS.** **E94** — narrowed on what a reader
does with a file, not on what an indicative value requires: every fence
stands. **E76** — untouched in substance; its retention requirement is
restated and given the marker that makes retention compatible with being
read. **E28**'s pre-registration order is not reached.

---

### E96 — a company whose revenue is a WORLD PRICE it does not set is OUTSIDE THE CIRCLE OF COMPETENCE

**RULED 2026-08-31 by the owner, in E51's shape and on E51's ground: the
same limit of the method, a different unknowable. Written before the code.**

> **THE RULE.** A company whose revenue is **a world market price it does
> not set, multiplied by a volume**, cannot be given a pre-registered growth
> view under E28, and **§5 cannot be run on it.**
>
> **The reason is arithmetic, not distaste.** For such a business **the bear
> case is not slower growth — it is a halved price**, and a halved price is
> not a lower `g` on the same cash flow but a different cash flow
> altogether. §5 discounts **a durable free cash flow that such a company
> does not have**: E28 makes us write g_bear, g_base and g_bull before the
> solve, and for a producer those three numbers would be three guesses about
> a commodity market, not three estimates of a business.
>
> **This is a limit of the METHOD, and it is not a judgement about the
> industry** — exactly as E51 says of clinical outcomes. A gas producer may
> be an excellent company and a fine investment; it is not a company this
> framework can value, and the honest response is to say so at STEP 0 rather
> than to produce a fair value whose growth rate nobody can defend.
>
> **The name is removed at STEP 0, with the reason recorded**, and the rule
> **applies regardless of screener rank.**
>
> **Membership is decided the two ways E51 uses, both recorded in
> `config/screener_commodity_price.yaml`:** the vendor's **industry string**
> where one is stored, and an **owner-maintained ticker list** that reaches
> what the string misses. **Exemptions are the owner's to write and never a
> session's**, in that file's `exempt:` block, by ticker, with the reason.

**NEVER A BARE SECTOR STRING, and the reason is the same one E51 gives for
refusing `Healthcare`.** `Energy` would take **utilities and renewables**
with it — the store carries `Utilities - Renewable`, `Utilities - Regulated
Electric`, `Utilities - Regulated Water` — and those sell a *regulated or
contracted* revenue base, which is the opposite of the fault this rule
names. `Basic Materials` would take **specialty chemicals** with it — ALB,
JMAT.L, LYB, DOW, KEMIRA.HE — which sell formulated products at negotiated
prices, and **building materials** (CRH, HEI.DE, MLM, VMC), which sell into
local markets with freight moats. **The `sectors:` block exists in the file
and is EMPTY on purpose.**

**WHAT IS IN SCOPE, as ruled:**

- **upstream oil and gas / E&P**, and **oilfield services where revenue
  tracks the rig cycle**;
- **mining and basic metals** — copper, iron ore, aluminium, gold, coal;
- **steel**, **pulp and paper**, and **bulk shipping where freight rates set
  revenue**.

**WHAT IS EXPRESSLY NOT SWEPT IN, and is NAMED for the owner rather than
decided here:**

- **Integrated and midstream** oil and gas. An integrated major carries
  refining and marketing margins that move against the crude price, and a
  midstream operator is often a toll on volume under contract. **Neither is
  the fault this rule names**, and neither is in the file today.
- **Anything where a regulated or contracted revenue base dominates** —
  utilities of every kind, and a producer whose output is sold forward on
  long-dated contracts rather than at spot.
- **Semiconductors, including memory.** Memory pricing is commodity-LIKE
  and MU sits at rank 20 of the 2026-08-29 ranking, but a memory maker sets
  its own capacity, differentiates on process node, and sells a manufactured
  product rather than a substance out of the ground. **It is NOT in this
  limb**, and whether it should be is the owner's separate decision.

**THE STRING LIMB IS BLIND WHERE THE FETCH HAS NOT REACHED**, exactly as
E51 records: fundamentals are fetched for the survivors of filter 1 alone,
so a name that never got that far carries no industry string and this limb
cannot see it. **That silence is a fact about the fetch, not about the
company**, and the owner's ticker list is the limb that does not depend on
it.

**AND THE STRING WILL BE WRONG ABOUT SOME NAMES, which is why the exempt
block exists.** Two are already visible in the 2026-08-31 application and
are flagged there rather than resolved here: **TPL**, which the vendor calls
`Oil & Gas E&P` and which is a **land and royalty** business that operates
nothing, and **TGS.OL**, called `Oil & Gas Equipment & Services` and which
sells **seismic data licences**. E51 met the same shape in TUB.BR and
FLERIE.ST. **A session never exempts either; it reports them and stops.**

**WHICH EARLIER RULING THIS AMENDS.** **None.** It sits beside **E51** as a
second circle-of-competence limb at STEP 0, with its own file and the same
two-limb membership test. **E46**'s investment-company list and **E3/E43**'s
sector exemptions are untouched and are a different mechanism — an exemption
from a LIMB, not a removal from the run.

---

### E96.1 — two exemptions, semiconductors DECLINED, and no partial exemption for a smelter

**RULED 2026-08-31 by the owner, on the three questions E96's first
application flagged. Amends E96 in its `exempt:` block and settles the two
it left open. E96's GROUND does not move.**

> **THE RULE, in three parts.**
>
> 1. **TPL — Texas Pacific Land — is EXEMPT from E96.** It **owns land and
>    takes royalties**, operating nothing and carrying **no production
>    volume** of its own. E96's ground is a world price *times a volume the
>    company does not control*; a royalty holder has no volume leg at all.
>    It is caught by the vendor's string `Oil & Gas E&P`, **not by E96's
>    mechanism**.
> 2. **TGS.OL — TGS ASA — is EXEMPT from E96.** It **licenses seismic
>    data**: a data business whose **customers** are producers, and which is
>    not one. The string `Oil & Gas Equipment & Services` describes who buys
>    from it, not what it sells. Same shape as E51.1's FLERIE.ST, where the
>    vendor's `Biotechnology` described the holdings and not the company.
> 3. **SEMICONDUCTORS, MEMORY INCLUDED, ARE DECLINED — CONSIDERED AND LEFT
>    OUT, NOT OVERLOOKED.** `MU` sat at rank 20 of the 2026-08-29 ranking
>    and the question was put squarely. **The answer is no**, on the
>    owner's own reasoning: **a memory maker SETS ITS OWN CAPACITY,
>    DIFFERENTIATES ON PROCESS NODE, and SELLS A MANUFACTURED PRODUCT.**
>    E96's ground is **a halved price on a volume you cannot influence**,
>    and a memory maker can and does cut capacity into a downturn. Memory
>    pricing is commodity-LIKE; that is not the same fact.
>
> **PART 3 IS RECORDED SO IT IS NOT RE-OPENED AS AN OVERSIGHT.** A later
> session finding `Semiconductors` absent from
> `config/screener_commodity_price.yaml` must read this entry and **not**
> conclude the string was forgotten. **It was considered and declined on
> 2026-08-31.** Re-opening it takes a new dated entry beneath this one.

**AND NO PARTIAL EXEMPTION FOR A SMELTER — the part with the sharpest
reasoning, recorded in the owner's terms.**

**BOL.ST (Boliden) and NHY.OL (Norsk Hydro) STAY IN THE LIMB.** Both were
flagged as integrated smelters with downstream product businesses — Hydro's
extrusions arm sells fabricated profiles at negotiated prices — and both
remain caught.

> **Downstream or not, the revenue is still the LME price.** And **a partial
> exemption would require ruling HOW MUCH DOWNSTREAM IS ENOUGH, which is
> exactly the guess E96 exists to refuse.** A threshold on the share of
> revenue that must be fabricated rather than smelted would be a number
> nobody could defend, applied to a split the issuers report inconsistently
> — the same shape as the invented thresholds E30 deleted. **The limb is
> binary because the alternative is a fabricated cut-off.**

**WHAT THIS COSTS, stated rather than softened.** Hydro and Boliden are real
businesses with real fabrication earnings, and this rule declines to value
them on the strength of a leg it will not size. **That is a cost accepted**,
and it is the same one E51 accepts for a CDMO's neighbours: a rule that
draws a line in a defensible place will always exclude something on the far
side that a finer rule would have kept.

**WHICH EARLIER RULING THIS AMENDS.** **E96** — its `exempt:` block gains
two rows, and the two questions it named for the owner are answered. Its
ground, its two limbs and its refusal of a bare sector string are unchanged.
**E51.1** is the precedent this follows in form. **E46** is not reached:
neither exemption is an investment company.

---

### E97 — the ranked list may be PRICE-WATCHED; it points once per crossing and writes nothing

**RULED 2026-08-31 by the owner, in E92/E93's shape. Written before the
code.**

**THE PROBLEM.** E94 tells the owner **what it would take to value** a
ranked name, and for eight of the top twenty it produces an INDICATIVE
value. But a value with no price beside it says nothing about **when to
look again**, and the nightly run watches only the twenty-two names already
on the watchlist. **A ranked name that halved would go unnoticed until the
next weekly screen.**

**THE RULE.** The nightly run may watch the **top N ranked names** (N
configurable, **default 20**) and **point when one crosses a stated level.**
It **never writes `config/watchlist.yaml`, never enters a name as PIPELINE,
never scores a gate, and an INDICATIVE value stays INDICATIVE** — E94's
fences are carried here unchanged and none is loosened by a price moving.

**WHAT IS WATCHED, and it is two different things:**

1. **A name with an INDICATIVE value and a registered growth view** is
   watched on its **REFERENCE DISTANCE**: the distance from today's close to
   the MBP that value would imply **at the tier-1 cushion (E90: base ×
   0.85)**.

   **THE TIER IS A REFERENCE AND NOT A TIER, and the label says so
   everywhere it is printed.** Almost no ranked name has a §4.4 score, and
   E90's MBP needs a tier the screen has not earned — a tier follows a score,
   which follows the E76 reading. **Tier 1 is chosen because it is the
   LOOSEST cushion and therefore the EARLIEST warning**: any real tier would
   sit lower, so a name that has not reached the tier-1 reference has not
   reached any MBP it could ever be given. **It is a distance, not a buy
   line, and nothing may be bought at it.**

   **E77's one-tier-stricter regime shift is NOT applied**, and for the same
   reason: it adjusts a tier that has been scored, and there is none here.

2. **A name with NO indicative value** is watched on its **DRAWDOWN from the
   52-week high** — where it sits against **Gate 1's 15–50% band**. That is
   the only thing the framework can say about a name it cannot value, and it
   is said as a position in a band rather than as a verdict.

**WHEN IT POINTS — three events, and each fires ONCE PER CROSSING:**

- an indicative-value name comes **within 25% of its reference distance**
  (price ≤ reference × 1.25);
- the same name **reaches the reference itself** (price ≤ reference);
- a name with no value **ENTERS Gate 1's band** (drawdown reaching 15%).

**ONCE PER CROSSING IS THE RULE, NOT A CONVENIENCE.** A pointer that repeats
every night while a name sits below a level is a pointer the owner stops
reading, and a pointer that is not read is worse than none — the same
argument E93 makes for refusing to fire on movement inside the top 20. **A
fired level stays fired until the price leaves it and comes back**, and the
state that remembers this is a cursor, never a decision.

**RE-ARMING TAKES A MARGIN, and the margin is stated rather than assumed.**
A level that re-arms the instant the price ticks back over it would fire
again on the next tick down — the oscillation this rule exists to prevent,
arriving one day later. **The price must rise a stated margin above the
level before that level can fire again.** The margin is a chosen number, it
is named at its definition in the code, and it is the owner's to move.

**WHAT IT MAY NOT DO.** No watchlist write of any kind, checked on the
file's bytes either side of the run. No `fv_base`, no `tier`, no `mbp`. **A
name outside the circle of competence — E51's or E96's — is NEVER WATCHED AT
ALL**, not even on its drawdown: §5 cannot be run on it, so there is no
level it could cross that would mean anything, and pointing at one would
invite exactly the work the ruling forbids.

**THE TABLE IS PRINTED EVERY NIGHT, whether anything fires or not.** The
pointer is for a crossing; the **state** is for reading, and a watcher whose
output is visible only when it fires cannot be checked for being wrong.

**WHICH EARLIER RULING THIS AMENDS.** **None.** **E94**'s fences are
carried unchanged — an indicative value is still never written, never given
a real MBP and never a strike. **E90** supplies the cushion arithmetic and
is not touched: no MBP is stored here, only a distance computed for display.
**E92/E93** supply the shape — outbound-only pointer, same topic, unset is
silence, a failed POST never fails the run. **E12** is not reached: nothing
here enters a name, so no Gate 1 reading is frozen.

---

#### E97.1 — the Gate 1 band event is DROPPED for a ranked name; the figure stays, the pointer goes

**DECIDED 2026-08-31 by the owner, on E97's first dry run. Amends E97's
event set; nothing else in it moves.**

**WHAT THE DRY RUN SHOWED.** `ENTERED GATE 1 BAND` fired for **fourteen of
the eighteen watched names on the first night**, and the reason is
structural: **filter 1 already rejects any name outside 15–50%**
(`rules.DISLOCATION_MIN` / `DISLOCATION_MAX`). **Every ranked name is in the
band by construction**, so the event announced what the ranking had already
said.

**THE DECISION: the band event is REMOVED, not re-thresholded.** A deeper
line — 35%, or a nearing of the 50% floor — was offered and **REFUSED**, in
the owner's words:

> **A deeper fall is still just a price, and this framework does not act on
> price without a named event.** That is exactly what DECK and CTSH were
> both judged on: DECK's re-entry needs *"a dated event that explains the
> decline, or a quarter that breaks the pattern — never a price level"*
> (E27), and CTSH's whole 2026-08-31 verdict turned on whether the catalyst
> behind its drawdown had resolved. **A number that falls further tells me
> nothing the ranking has not.**
>
> **What I want to hear about a valueless name is that it now HAS a value**
> — and E94's readiness already tells me that.

**THE FIGURE STAYS, THE POINTER GOES.** The drawdown is still computed and
still printed in the nightly table **as information**, so the state of a
valueless name is readable. **It simply never fires.** E97's table-every-night
rule is what makes that useful: a figure nobody is paged about is still a
figure a reader can check.

**WHAT REMAINS FIREABLE.** The two reference rungs, and only those: a name
**within 25% of its reference distance**, and a name **at the reference**.
Both require an indicative value, which requires a complete store, every
figure VERIFIED, and a registered growth view (E94) — so **every pointer E97
can now send rests on a name the framework can actually value.**

**WHICH EARLIER RULING THIS AMENDS.** **E97** — one of its three events is
struck; the once-per-crossing rule, the re-arm margin, the reference
arithmetic, the never-watched rule for E51/E96 names and the nightly table
are unchanged. **E27** is the precedent quoted and is untouched.

---

### E98 — a converted figure names its RATE and its DATE, and a UNIT is not a RATE

**RULED 2026-08-31 by the owner, on E97's reference distance being unusable
for half the names that had earned one. Written before the code. Extends
E24, which froze the rate on a verdict and never said how one is obtained.**

**THE SEAM THIS CLOSES.** Three bugs have now come out of comparing a price
with a per-share value: `"GBp".upper() == "GBP"` in the readiness path
(fixed 93b7472), the same divide in the price watcher (+12,791% for AUTO.L,
fixed 586f5c2), and the four names E97 could not watch on their reference at
all. **E24 says the conversion happens and what must be recorded beside it;
it does not say where the number comes from.**

**THE RULE, AND ITS FIRST HALF IS THAT THERE ARE TWO CASES.**

**1. A MINOR UNIT IS NOT A CURRENCY, AND ITS CONVERSION IS NOT A RATE.**
`GBX`/`GBp` and `GBP` are **the same currency in different units**: pence and
pounds, **exactly one hundred to one, for ever**. The conversion is a
**DIVISOR** — `fx.MINOR_UNITS_PER_MAJOR`, already on file — and it is
**exact, dateless and sourceless.** There is no rate to fetch, no as-of date
to match and no staleness to worry about. **A minor-unit conversion is
never refused for want of a rate**, and calling it an exchange rate would
invent a question that has no answer. *This is the case all four of E97's
blocked names are in.*

**2. A DIFFERENT CURRENCY NEEDS A REAL RATE, AND THE RATE IS DATED.**

- **THE SOURCE** is the project's own FX lookup (`vss/fx.py`), and the
  figure records **which source answered**, as `fx.Rate.source` already
  carries.
- **THE DATE IS THE PRICE'S OWN DATE. NEVER A STALE RATE.** A value compared
  against a close of 2026-08-28 is converted at the rate of **2026-08-28**.
  The existing `default_lookup` takes the newest close of a five-day window
  and is therefore **NOT ADMISSIBLE** for this purpose: it answers "the
  latest rate", which on a Monday is a different question from "the rate on
  Friday's close".
- **WHERE NO RATE FOR THAT DATE EXISTS, THE CONVERSION IS REFUSED.** **It is
  not interpolated, not carried forward from the previous session, and not
  approximated from a neighbouring day.** The figure is DATA MISSING with
  the pair and the date named, and whatever depended on it says so. *A rate
  invented for a date is the same class of error as a zero invented for an
  absent tag (E25), and this project refuses those.*
- **THE CONVERTED FIGURE IS PRINTED WITH THE RATE AND THE DATE IT USED**, so
  the arithmetic is checkable by hand from what is on the page. E24 already
  requires six things beside a converted figure on a VERDICT; this extends
  the same discipline to a figure that is merely **displayed**, because a
  displayed number that cannot be checked is one a reader must either trust
  or ignore.

**WHAT THIS DOES NOT DO.** It does not re-strike anything. **E24's freeze
stands**: a rate frozen with a verdict stays frozen, and this rule governs
how a rate is OBTAINED, not when a struck figure may be revisited. No
`fv_base`, `mbp` or `stop_price` moves because of it, and E97's reference
distance remains **a distance and not a buy line**.

**WHICH EARLIER RULING THIS AMENDS.** **E24** — extended, not altered: it
said what is recorded beside a converted figure and froze the rate on a
verdict; this says which rate, of which date, from where, and what happens
when there is none. **E25**'s refusal to invent a number from an absence is
the precedent for the refusal clause. **E97** gains usable reference
distances for the names whose only obstacle was a unit.

---

### B47 — E51's pharma/biotech circle limb is a HAND LIST OF 21 TICKERS against a universe of 2,011, and it removed ZERO of the 651 mid caps

**FOUND 2026-08-31, widening the universe to tier B. RESTED BY THE OWNER
2026-09-01 — "it is a circle question and I'll rule it rested, not at
midnight." Recorded so it is not lost, not so it is acted on.**

**The finding, measured.** The universe went from 1,360 to 2,011 instruments
on 2026-08-31 (the S&P MidCap 400, and the Oslo / Copenhagen / Helsinki mid
caps). Running the identical code over the identical snapshot with and
without tier B attributes each step-0 limb's removals to the 651 new names
exactly:

| limb | removed from the 651 new names |
|---|---:|
| **E51 — pharma/biotech, OWNER TICKER LIST** | **0** |
| E51 — pharma/biotech, industry string | 3 |
| **E96 — commodity price, industry string** | **20** |

**Why the difference is structural and not luck.**
`config/screener_pharma_biotech.yaml` carries **21 hand-entered tickers** and
3 industry patterns; every one of the 21 is a tier-A large cap, so the owner
list **cannot by construction reach anything added on 2026-08-31**.
`config/screener_commodity_price.yaml` carries **no ticker list at all** — 16
industry patterns and nothing else — which is precisely why it reached 20 new
names where E51 reached 3.

**So the two circle limbs are not equivalent, and the difference now
matters.** E96 scales with the universe because it is written as a rule about
what a business IS; E51 scales with the owner's typing because half of it is
written as a list of who. That was invisible while the universe was 1,360
large caps the owner had read about; it is not invisible at 2,011.

**This is a CIRCLE OF COMPETENCE question, which is why it is a B and not a
backlog item.** Nothing in the code is broken — the limb does exactly what
E51 says. What is open is whether E51's *shape* is right at this size:

1. **Leave it.** The industry patterns catch the clear cases and the owner
   list is what it says it is — a list of exceptions the strings get wrong.
   The cost is that mid-cap pharma reaches the ranked list unremarked.
2. **Extend the owner list to the mid caps by hand.** Accurate, and it is
   work, and it is work that repeats at every widening.
3. **Widen E51's INDUSTRY PATTERNS toward E96's shape** and let the ticker
   list shrink to genuine exceptions. This is the only option that scales,
   and it is the one that risks over-reach — E96.1 already had to DECLINE a
   semiconductor exemption, which is what over-reach looks like from the
   inside.

**One bound on all three numbers above.** E51 and E96's industry limbs read
the vendor's sector and industry strings out of the fundamentals stores, and
fundamentals are fetched for the survivors of filter 1 alone. The string
limbs can therefore see 699 names out of 2,011 and are structurally blind to
the rest. **The counts are floors, not totals** — which cuts against option 1
rather than for it.

*Evidence: `reports/UNIVERSE-WIDENING-2026-08-31.md`, Part 2. The split by
source list is there too: the limb that DOES bite the new names hardest is
E52's five-year bar, at 17.1% of the Nordic mid caps against 6.3% of tier A —
correct rather than over-reaching, but it is where the widening loses most.*

---

### E99 — a gate criterion whose data has NEVER EXISTED scores DATA MISSING and does not count against the gate count; §4.4 rebases to four

**RULED 2026-09-01 by the owner, deciding B5's original proposal, open since
2026-08-21 and raised again by `reports/METHOD-REVIEW-2026-09-01.md` Part
1.2. Written before the code.**

**B5 ASKED THIS IN AUGUST AND ONLY HALF OF IT WAS ANSWERED.** The 2026-08-21
decision recorded under B5 settled §5.1 Method A's *multiple* — the trailing
proxy — and said in terms that it did **not** answer B5's Gate 4 question.
That half stayed open for eleven days and has been costing money the whole
time.

**THE RULE.**

> **A §3 gate criterion for which the data has never been obtainable is
> DATA MISSING. It is not a FAIL, and it does not sit in the denominator of
> the gate count.**
>
> **§4.4's scale rebases to a denominator of FOUR:**
>
> `Score = (Gates passed: 0–4) + Σ(green flags) − Σ(soft flags)`
>
> | | old | new |
> |---|---|---|
> | Tier 1 — high conviction | ≥ 7 | **≥ 6** |
> | Tier 2 — medium | 5–6 | **4–5** |
> | Tier 3 — drop or watchlist | ≤ 4 | **≤ 3** |
>
> The tier-1 line keeps its other two conditions unchanged: **conviction ≥ 6
> AND a fortress balance sheet AND a secular tailwind.** A score that clears
> the bar does not by itself make a tier 1, and UNA.AS is the standing
> example — score 7, held at tier 2 on the fortress and domain conditions,
> and unmoved by this ruling.

**WHY, AND THE NUMBER IS THE ARGUMENT.** Gate 4 requires a forward P/E
against its own five-year median, a peer-median EV/EBIT or P/S, and an FCF
yield against a sector median. **Not one of the three has ever been
assembled for any name in this framework's history.** B5 said in August that
forward P/E is "the hardest datum in the entire framework to source", and
the two limbs that need peer and sector medians need a peer set and a sector
set that nobody has ever built.

So Gate 4 has scored a permanent zero, for every name, for ever — and
because it sat in the denominator, **that zero was silently costing one
point of conviction on every name in the framework.** One point of
conviction is one tier, and one tier is **10 percentage points of cushion
under E90** — 13–24% of every buy price, depending on where the name sits.
It has been doing that since E90 was applied on 2026-08-30, twelve days
after the gate was first scored.

**A criterion nobody can evaluate is not a criterion a company has failed.**
That is E25's argument about an absent tag, and E4's about a pass-through,
applied to a gate.

**GATE 4 IS NOT DELETED, AND THAT IS THE POINT.** It stays in §3 exactly as
written. **The moment peer and sector medians exist, it becomes evaluable,
returns to the denominator, and the scale rebases back to five.** What is
ruled here is what happens to a criterion whose data has never existed —
not that this particular criterion is a bad idea. A gate that is DATA
MISSING is a gate waiting for data; a gate that is deleted is a judgement
nobody can revisit.

**WHAT THIS DOES NOT DO.** It does not re-score anything. **No §4.4 score
moves**, because Gate 4 was never *passed* and therefore never contributed
to a score — what moves is the THRESHOLD, by one, in the same direction for
every name. It does not touch Gate 1, 2, 3 or 5, and it does not touch the
green and soft flag lists. A name with no §4.4 score on file is **not
rebased on a guess**: it stays as carried until its next scheduled §6.4
reassessment, which is E77's own treatment of the same problem.

**AND THE CROSSING IT CAUSES IS E100's.** Applying this moves exactly one
name — GDDY, tier 3 → tier 2 — and its MBP from 85.91 to 99.13, which puts
a close of 97.88 **below a buy line it was 13.9% above the day before, on a
rule change and no price movement.** That is precisely the sequence E100
was ruled on the same day to stop, so **the crossing is marked as
definition-caused and arms nothing.** The two rulings were made together and
the first one's first consequence is the second one's first case.

> **CORRECTION, 2026-09-19 (owner).** The paragraph above is wrong in its
> application, not in its rule. Applying E99 moves **no** name: GDDY's score
> of 6 clears the rebased tier-1 bar but not tier 1's other two conditions,
> which this ruling itself keeps (a fortress balance sheet and a secular
> tailwind, both found absent on 2026-08-30), so it is tier 2 on the new
> scale → E77 → tier 3, as before. Moving it 3 → 2 was a misreading of §5.3.
> GDDY was corrected to tier 3, MBP 83.87, on 2026-09-19. The rule text is
> unchanged and blocks no name. The original paragraph stands as written.

**WHICH EARLIER RULING THIS AMENDS.** **B5** — its original Gate 4 proposal,
decided at last, in the form B5 itself proposed and generalised from "a
missing discount input" to "a criterion whose data has never existed".
**FRAMEWORK §3 Gate 4** — unchanged in substance, re-scored as DATA MISSING.
**FRAMEWORK §4.4** — the scale rebases. **E90** — unchanged; the cushion is
untouched and only the tier that selects it moves.

---

### E100 — the tier cushion comes under E28's discipline: a change is DATED, applies at the next scheduled reassessment, and the crossing it causes arms nothing

**RULED 2026-09-01 by the owner, on `reports/METHOD-REVIEW-2026-09-01.md`
finding H1. Written before the code.**

**THE MULTIPLIERS DO NOT MOVE. 0.85 / 0.75 / 0.65 STAND.** What is ruled is
**how they may be changed**, and it is the discipline E28 already imposes on
the other lever.

**THE SEQUENCE THAT PROMPTED IT, RECORDED RATHER THAN SUMMARISED.** On
2026-08-30 CTSH's maximum buy price rose from 46.78 to 67.04 — **+43%** — on
**two rule changes made the same day**: E90 recalibrated the cushion, and
E77's "from now only" preserved tier 2 where a re-score would have given
tier 3. **The price did not move.** Four days earlier
`reports/THRESHOLD-REACHABILITY-2026-08-26.md` had measured the old line as
close to unreachable and **expressly recommended no change**. The result was
**this framework's first and only BUY signal**, and it was manufactured by
the denominator.

**THE POINT OF PRINCIPLE.** §5's fair value has two levers on it: `g`, the
growth rate, and the cushion. E28 makes `g` **pre-registered before the
solve** and E28's void rule throws out a growth view written afterwards,
for exactly one reason — *a rate chosen once the answer is visible is not an
estimate, it is a target*. **The cushion is the same lever wearing a
different name, and it had none of that discipline.** A cushion widened
after seeing where the price is does the same work as a growth rate raised
after seeing where the value needs to land.

**THE RULE.**

> **1. A CHANGE TO THE CUSHION IS A DATED RULING.** It is written down,
> numbered, and carries its reasoning — never a quiet edit to a constant.
>
> **2. IT TAKES EFFECT AT EACH NAME'S NEXT SCHEDULED §6.4 REASSESSMENT, AND
> NEVER IMMEDIATELY.** This is **E77's treatment of itself**, made general:
> the regime adjustment reaches a name on new information rather than on a
> rule change. A change ruled today does not move a single MBP today.
>
> **3. AN MBP CROSSING CAUSED BY A CHANGE IN THE DEFINITION IS MARKED AS
> SUCH AND DOES NOT ARM AN ALERT.** Where a name is at or below its MBP
> tonight and **would not have been at last night's MBP**, the crossing is
> the DENOMINATOR moving, not the price. The report says so, in those terms,
> and no alert is armed on it. **The report already knows the MBP's
> derivation and can tell the numerator from the denominator**; it simply
> never asked.

**HOW THE THIRD CLAUSE IS DECIDED, so it is a test and not a judgement.** A
crossing is **definition-caused** when tonight's close is at or below
tonight's MBP **and strictly above the MBP the previous run recorded for
that name**. The price did not reach the old line; the line came to the
price. Both figures are already in `run_metrics` — this needs no new input
and no one to remember anything.

**WHAT THIS DOES NOT DO.** It does not re-strike anything, it does not move
a stop, and **it does not forbid changing the cushion** — E90's
recalibration stands and was right to be made. It governs the *manner* and
the *timing*. It does not apply to the FAIR VALUE moving: a name that
crosses because a re-strike lowered `fv_base` has crossed on a change to the
numerator, which is §5 doing its job and is a real crossing.

**ITS FIRST CASE IS E99's, ON THE SAME DAY.** E99 rebases the gate scale and
moves GDDY to tier 2, lifting its MBP from 85.91 to 99.13 and putting a
close of 97.88 below it with no price movement at all. **That is a
definition-caused crossing under clause 3, it is marked, and it arms
nothing.** The first rule of this kind is tested by the first change made
after it, which is the strongest evidence available that it was needed.

**WHICH EARLIER RULING THIS AMENDS.** **E90** — the multipliers are
unchanged and now governed. **E28** — its discipline is extended from `g` to
the cushion, on E28's own reasoning. **E77** — its "from now only" timing
stops being an exception and becomes the general rule. **E27** — a
WATCH-PRICED name's alert is armed on a price event; this says a definition
change is not one.

---

### E101 — the cushion's SIZE stands; the gap to the measured error is closed by SHRINKING THE ERROR, and the construction-error detector is what does it

**RULED 2026-09-01 by the owner, on `reports/METHOD-REVIEW-2026-09-01.md`
finding H2. Written before the code.**

**THE FINDING, ACCEPTED.** E90 states that the cushion covers "model and
input error… typically 5–15% of value". This repo's own week produced
corrections of **+36%** (E34, LIAB.ST), **−33%** (E36, NKE), **+56%** (E70,
NKE) and **+29%** (E37's measured currency bias on SAP.DE). The observed
error distribution of this framework is **29–56%**; the protection against
it is 15–35%. The review is right that these do not meet.

**THE DECISION: THE CUSHION DOES NOT WIDEN. 0.85 / 0.75 / 0.65 STAND.**

**WHY, AND IT IS THE WHOLE RULING.** A cushion wide enough to cover a 56%
construction error is a cushion that buys nothing, ever — and it would be
**paying for a defect with opportunity instead of fixing it.** Every one of
those four corrections was a *transcription or construction* error found by
hand: a leg read from the wrong line, an add-back missed, a conversion not
made. **They are findable.** An error that a check could have caught is not
a risk to be insured against; it is a bug to be caught. **So the gap is
closed by shrinking the error, and the cushion is left to do the job it was
sized for.**

**WHAT VERIFICATION HAS NEVER PROVIDED.** E40's read-back verifies that a
figure was **correctly transcribed from the page it names**. It cannot see
that the right figure was read from the wrong page, that a leg is missing
entirely, or that a bridge does not balance — because every one of those is
*correctly transcribed*. **Every rule in this repo checks transcription and
none checks construction**, which is Blind Spot 1 of the method review and
the root of all four corrections above.

**THE RULE: THREE DISAGREEMENT CHECKS, PRINTED WITH EVERY STRIKE.**

> **1. FCF0 against the issuer's own stated free cash flow**, where one is
> published. The store already carries `free_cash_flow_reported` — entered,
> in its own words, "so the derived bases can be compared against the figure
> the company publishes" — and nothing has ever compared them.
>
> **2. NET DEBT against the issuer's own stated net debt.** `LIAB.ST`'s file
> does exactly this by hand, in prose, and **it is what found the missing
> pension leg** (E35.1, +6.3%). This makes the hand practice mechanical and
> gives it a field of its own.
>
> **3. THE FCF-TO-NET-INCOME CONVERSION RATIO against a plausible band.** A
> conversion far outside it means one of the two figures is on a different
> basis from the other — a quarter against a year, a segment against a
> group, a per-share figure against a total.

> **NONE OF THE THREE IS AUTHORITATIVE, AND NONE ADJUDICATES.** The issuer's
> own free cash flow is on the issuer's definition, which is usually NOT
> E34's; the issuer's net debt usually excludes the pension leg E35.1
> includes. **A disagreement is not a verdict that this project's figure is
> wrong** — LIAB.ST's +6.3% disagreement was the *issuer* being narrower,
> and the project's figure stood. **They are DETECTORS: they are printed,
> the size and direction of each disagreement is stated, and nothing is
> adjusted, refused or blocked on them.** A check that adjudicates would
> import the vendor's or the issuer's definition through the back door,
> which is the error E5 and E35 both exist to prevent.

**WHERE A COMPARATOR IS ABSENT, THE CHECK IS DATA MISSING AND SAYS SO.** An
issuer that publishes no free cash flow line is not a disagreement of zero.

**WHAT THIS DOES NOT DO.** It moves no figure, blocks no strike, and changes
no fair value. It does not re-open E90's arithmetic. It does not make the
cushion smaller either — the size stands until the measured error moves,
and **whether it may then be revisited is E100's question**, not this one.

**WHICH EARLIER RULING THIS AMENDS.** **E90** — its stated basis for the
cushion is left standing and the gap to it is addressed on the other side.
**E40** — extended in kind: E40 verifies transcription, this detects
construction, and the two answer different questions. **E34, E35/E35.1, E36,
E70** — the four corrections that motivate it; check 2 is E35.1's own
discovery method, generalised.

---

### E102 — LIAB.ST's stop stays at 112; a stop and a buy price are permitted to collide

**RULED 2026-09-01 by the owner, on `reports/METHOD-REVIEW-2026-09-01.md`
finding H4 and closing the item raised 2026-08-25. CLOSED BY THIS DECISION,
NOT DEFERRED AGAIN.**

**THE FACTS, WHICH ARE NOT IN DISPUTE.** LIAB.ST: fair value 133.48, stop
112, maximum buy price 100.11, last close 130.70. The framework is committed
to **selling this position at 84% of what it says the company is worth**,
and will not buy more until 75%. Between 112 and 100.11 there is a corridor
in which the rules say sell and the rules say do not yet buy.

**THE DECISION, IN THE OWNER'S OWN TERMS.**

> **The stop stays at 112.**
>
> **The stop protects capital and the MBP expresses valuation. They are
> permitted to collide.** They are answers to two different questions — *how
> much am I willing to lose on a position I hold* and *what is this worth* —
> and there is no reason two different questions must produce two levels in
> a tidy order.
>
> **I accept being stopped out above my own buy price.** That is not an
> inconsistency to be engineered away; it is what a stop IS. A stop that is
> moved down to sit below the buy price is a stop that has been widened
> because the analysis says the company is cheap — which is precisely the
> reasoning a stop exists to overrule.

**WHAT WAS CONSIDERED AND REJECTED.** Moving the stop below the MBP would
have made the two levels consistent by making the stop worse: 100 is a 25%
loss from a 133 valuation and the position would carry it. Widening the MBP
to meet the stop is the E100 lever and is now governed. **Doing neither, and
saying so, is the decision.**

**WHAT THIS DOES NOT DO.** It does not generalise into a rule that every
stop stands wherever it is. It is a decision about **this** stop, on **this**
name, and the reasoning is recorded so the next collision can be argued
against it rather than from nothing. §6.4's reassessment at the 2026-10-23
Q3 report may move the stop on new information, which is a different act
from moving it to resolve a tension with the buy price.

**WHICH EARLIER RULING THIS AMENDS.** None. It closes the open item of
2026-08-25 and records the reasoning that had never been written down.

---

#### E101 — both thresholds ACCEPTED BY THE OWNER 2026-09-01

**Ruled as his, not merely as numbers the code chose.** E101 named two
figures and left them to be argued with; they are argued no longer.

> **`FCF_CONVERSION_BAND` = 0.2–3.0×.** *"The conversion band is
> deliberately wide because §4.3 already reads high conversion as a green
> flag, so what is detected is a figure on the wrong basis, not a business
> that converts well."*
>
> **`DISAGREEMENT_TOLERANCE` = 5%.** *"5% allows for rounding and
> definitional differences without hiding a missing leg."*

**Both are load-bearing in one direction each, and the reasoning says which.**
A band tight enough to argue with §4.3 would be a second and contradictory
quality test wearing a detector's clothes. A tolerance loose enough to
swallow LIAB.ST's +6.3% pension leg would have swallowed the one finding
this detector exists to have made.

**The "chosen, not derived" hedge is struck from both definitions.** They
carry the owner's authority now, and a session that wants to move one is
asking him, not editing a constant.

---

### E103 — the issuer's own free cash flow and net debt are REFERENCE FIGURES, may be fetched AUTOMATICALLY and entered UNVERIFIED, and may never reach a §5 basis

**RULED 2026-09-01 by the owner, on E101's first live reading — three
checks built, and DATA MISSING on every store because nobody had entered
the comparators. Written before the code.**

**THE DISTINCTION THIS RULING MAKES, AND EVERYTHING FOLLOWS FROM IT.**

> **A BASIS FIGURE enters a valuation. A REFERENCE FIGURE is only ever
> compared against one.**

E40's read-back exists because a basis figure that is wrong makes the
answer wrong, silently and for ever. **That is not true of a reference
figure, and the asymmetry is total:**

- **A wrong basis figure produces A WRONG VALUE.** Nothing downstream can
  detect it, which is why every one of them is read back by hand before it
  is trusted.
- **A wrong reference figure produces A FALSE BLINK.** The detector says
  "these two disagree", the owner looks, and the disagreement turns out to
  be the comparator rather than the record. **The cost is one look. The
  cost of the alternative — a comparator nobody enters — is the detector
  not existing at all**, which is exactly where E101 stood on the day it
  was built.

**THE RULE.**

> **1. `free_cash_flow_reported` and `net_debt_reported` ARE REFERENCE
> FIGURES.** They exist to be compared against §5's own construction and
> for nothing else.
>
> **2. THEY MAY BE FETCHED AND EXTRACTED AUTOMATICALLY, AND ENTERED
> UNVERIFIED.** SEC XBRL tags where they exist; the PDF path via DeepSeek
> where they do not. No hand read-back is required BEFORE they are entered,
> because nothing depends on them being right.
>
> **3. E101's CHECKS MAY READ THEM. NO §5 BASIS MAY EVER READ THEM.** This
> is the fence and it is mechanical, not a matter of care: **the §5 gate
> REFUSES — loudly, naming the field — if a reference figure is ever wired
> into a basis.** A reference figure that reached a valuation would be an
> UNVERIFIED number inside a fair value, which is the one thing E40 exists
> to prevent, arriving through the door this ruling opens.
>
> **4. WHERE A CHECK DISAGREES, THE REPORT SAYS TO VERIFY THAT ONE FIGURE
> BEFORE THE DISAGREEMENT IS TREATED AS REAL.** The comparator is
> UNVERIFIED and is the more likely of the two to be wrong; it is named,
> with its page, and the owner reads back one line.

**WHAT THIS BUYS, AND IT IS THE POINT OF THE WHOLE RULING.** **The
read-back moves from EVERY FIGURE IN ADVANCE to THE ONE FIGURE THAT
ACTUALLY BLINKED.** E40 asks the owner to verify everything before anything
can be trusted; this asks him to verify one figure, after something has
already told him where to look. That is a different and far cheaper
discipline, and it is only available because a reference figure cannot
corrupt an answer.

**WHAT THIS DOES NOT DO.** It does not weaken E40 by an inch — every BASIS
figure is verified exactly as before, and clause 3 is the guarantee that the
boundary holds. It does not make an automatically-entered figure
authoritative: it is UNVERIFIED, it says so, and E101 already forbids any
check from adjudicating on it. It does not extend to any other field, and a
session that wants to add one to the reference set is asking for a ruling.

**WHICH EARLIER RULING THIS AMENDS.** **E40** — unchanged for basis figures;
this carves out a class E40 was never about, and fences it. **E101** — its
two comparators become obtainable, which is what turns it from a built
detector into a working one. **E92** — a refresh may now write these two
fields automatically where it may write nothing else; the store is still
never a decision.

---

### B48 — the screener cannot see organic revenue at all, so E45's kill is permanently on the reported series

**RAISED 2026-09-01, after B9/E30's carve-out was made reachable in the hand
chain and found to be structurally unavailable to the screener. RECORDED AS
AN OPEN QUESTION BY THE OWNER, to be ruled another day. Nothing changes
until he does.**

**THE FACT, MEASURED.** §4.2.1's revenue kill and E45's revenue limb are two
different implementations of one idea, and only one of them can see organic
revenue:

| | §4.2.1 (`rules.revenue_decline_kill`) | E45 (`filters.revenue_limb`) |
|---|---|---|
| reads | the watchlist's `quarters:` | the vendor's `Total Revenue` series |
| organic leg | `revenue_yoy_organic`, **live since 2026-09-01** | none, and none possible |
| B9's carve-out | applies | **cannot apply** |
| kills | the hand chain | the universe, before a name is ever read |

`revenue_decline_kill` is called from exactly one place — `rules.py`'s
hard-kill evaluator — and `filters.revenue_limb` never calls it. The
screener's store carries seven income lines (`Total Revenue`, `EBITDA`,
`EBIT`, `Operating Income`, `Total Operating Income As Reported`,
`Net Income`, `Gross Profit`) and **not one of them is an organic measure**.
`screen.py` has stated this in its own report text since E45 was applied:
*"the screener cannot read the organic series, and E45 states that cost."*

**WHY IT MATTERS MORE NOW THAN IT DID.** E49's retention is filling the
quarterly window, and the measurement of 2026-09-01 expects **~73 names to
flip FLAG → FAIL** as the second year-on-year comparison becomes measurable
— **~41 of them live candidates**, AOS among them. Every one of those kills
will be struck on REPORTED revenue with no organic series to test it
against. B9's own case (UNA.AS: four consecutive reported declines of
−4.6%, −3.5%, −2.7%, −3.3% against underlying growth of 3.0–5.8%
throughout) is exactly the shape that would be killed silently at the
screener, before any hand chain could apply the carve-out that exists for
it.

**THE ASYMMETRY IS THE WHOLE PROBLEM.** The hand chain now refuses to kill
on reported revenue without saying so. The screener kills on reported
revenue and the name never appears again — there is no verdict to read,
because a name removed at filter 2 is not a name with a verdict.

**WHAT I WOULD PROPOSE, and each option is priced.**

1. **A SECOND REVENUE SOURCE — the only thing that actually closes it.**
   Organic growth is a non-GAAP APM: it is in the issuer's release and in
   no vendor feed and no XBRL taxonomy. Getting it for ~700 candidates
   means the E103 machinery (fetch the release, read it with the model,
   store it UNVERIFIED) run at universe scale rather than at watchlist
   scale. **Cost: one model call per name per quarter — roughly 700 calls a
   week against the ~25 E103 makes today, plus the document fetch for
   markets whose archives have no adapter (`FETCHER-SURVEY` section 6).**
   This is a change of order in what the screener spends, and it is the
   honest price of the carve-out applying where the kills actually happen.

2. **REQUIRE THREE CONSECUTIVE DECLINES INSTEAD OF TWO, while the basis is
   reported.** The method review proposed this independently. It does not
   see organic; it buys tolerance for the currency and disposal cases by
   demanding a longer run. **Cost: ~5 lines and a config value. It weakens
   the kill for every name rather than sparing the ones the carve-out
   would have spared** — a blunt instrument aimed at a specific error.

3. **EXEMPT A DECLINE INSIDE THE PERIOD'S FX MOVE.** The screener already
   fetches FX. A reported decline smaller than the currency move against
   the reporting currency over the same window is not evidence of demand
   loss. **Cost: ~40 lines. It catches the CURRENCY half of B9's ground and
   not the DISPOSAL half** — UNA.AS's own decline was −5.9% currency and
   −1.2% disposals, so this would have caught most but not all of it.

4. **DO NOTHING, AND SAY SO IN THE RUN.** Make the screener's report state,
   per killed name, that the kill was struck on reported revenue with no
   organic series available — the same visibility clause §4.2.1 now
   carries. **Cost: ~10 lines. It changes no verdict** and makes the
   population of possibly-wrongly-killed names countable, which is what
   any of options 1–3 would need in order to be judged.

**MY RECOMMENDATION, and it is a sequence rather than a choice.** **Option 4
first**, because none of the others can be argued for without knowing how
many names are affected and by how much — and because it is the only one
that costs nothing and forecloses nothing. Then **option 3**, which is
cheap, targeted, and uses data already in hand. **Option 1 is the only
complete answer and I would not spend it until options 4 and 3 have shown
what is left over.** Option 2 I would not take at all: it trades the kill's
accuracy on every name for tolerance on a few, which is the shape of trade
E44 was criticised for making in the other direction.

**WHAT IS NOT IN QUESTION.** E45's rule stands as ruled — this is about what
the rule can SEE, not about whether it is right. And §4.2.1's carve-out is
now live and needs no further decision.

*Evidence: `reports/CODE-REVIEW-2026-09-01.md` addendum item 2 for the ~73
and the 84% base rate; `vss/screen.py`'s own filter-1 report text; the
measurement of 2026-09-01 that no watchlist quarter carried an organic
figure and that B9's own case TRIPS without one.*

---

### E104 — a disagreeing check is RE-EXTRACTED before it is escalated; two independent readings agreeing is what makes it the owner's

**RULED 2026-09-01 by the owner, on E103's first full run. Written before
the code.**

**THE DEFECT IN E103's OWN CLAUSE 4, IN THE OWNER'S WORDS.** *"E103 lets a
reference figure be entered automatically because a misread produces a false
blink, not a wrong value — but the report then asks me to read back every
disagreement, which is the read-back the ruling was meant to avoid."*

That is exactly right and it is E103 half-finished. The ruling moved the
read-back from every figure in advance to the figure that blinked; it did
not ask whether the machine could answer that one itself. **It can, and the
first full run proved the need: eight checks disagreed, and the report asked
for eight read-backs.**

**THE RULE.**

> **1. A DISAGREEING CHECK IS RE-EXTRACTED BEFORE IT IS ESCALATED.** Where
> an E101 check disagrees and its comparator is an UNVERIFIED figure this
> project entered automatically, the machine reads the figure again — a
> SECOND PASS over a NARROW EXCERPT around the line the first pass quoted,
> asking for that one field.
>
> **2. THE SECOND PASS IS NOT TOLD THE FIRST ANSWER.** It is given the
> passage and the question, never the number. A second reading shown the
> first is not a second reading. The first pass's quote is used only to
> LOCATE the passage — a hint about WHERE to look, never about WHAT to find,
> and the difference is the whole of the independence.
>
> **3. TWO READINGS THAT AGREE SETTLE THE TRANSCRIPTION.** The figure is
> what the report says. The disagreement is therefore a difference of
> CONSTRUCTION between this project's arithmetic and the issuer's, which is
> what E101 exists to surface — **and only then is it the owner's, as
> JUDGEMENT and never as a read-back.**
>
> **4. TWO READINGS THAT DISAGREE CONVICT THE EXTRACTION.** Neither can be
> trusted: two transcriptions of one printed line that differ mean the line
> was not read. **The figure is WITHDRAWN — replaced by a NAMED ABSENCE
> carrying both readings — and nothing reaches the owner at all.** The check
> returns to DATA MISSING, which is honest, and the next run may try again.
> **This corrects itself with no involvement from him.**

**WHY THIS IS SOUND AND NOT MERELY CHEAPER.** The two failure modes E103
distinguishes have different signatures, and a second reading separates
them:

| | first pass | second pass | what it means |
|---|---|---|---|
| the line was misread | value A | value B | **transcription** — withdraw |
| the line was read right | value A | value A | **construction** — the owner's |

A misread arises from the model picking the wrong column of a multi-column
row, the wrong period, or the wrong one of two similarly-named lines — and
every one of those is a choice made across a WIDE excerpt that a NARROW one
removes. Two passes over the same narrow passage agreeing is therefore
strong evidence about the transcription and no evidence at all about the
construction, which is precisely the split wanted.

**WHAT THIS DOES NOT DO.** It does not touch a figure the owner has
VERIFIED — a hand-read figure is already settled and a second machine
reading adds nothing to it. *SAP.DE (−13.5%) and PNDORA.CO (+22.7%) are
both of that kind and stay the owner's to judge.* It does not adjudicate
the disagreement: E101 still never decides who is right. It does not widen
what may be entered automatically — E103's fence stands, and a reference
figure still may never reach a §5 basis.

**WHICH EARLIER RULING THIS AMENDS.** **E103** — its clause 4 is replaced.
A disagreement no longer says "verify this one figure"; it says either
"this is construction, and it is yours" or nothing at all, because the
figure withdrew itself. **E101** — unchanged in what it detects; what
changes is what happens after it detects. **E25** — the precedent for the
withdrawal: two readings that disagree are not a figure, and a number
nobody can reproduce is not entered.

---

### E105 — dividends paid to NON-CONTROLLING INTERESTS are deducted in the FLOW; the minority is never carried as a liability

**RULED 2026-09-04 by the owner, on the reconciliation
`reports/FCF-RECONCILIATION-2026-09-04.md`. Written before the code.**

**THE RULE.**

> **FCF0 is reduced by the DIVIDENDS ACTUALLY PAID to non-controlling
> interests over the basis window, as the cash flow statement states them.**
> A cash figure, on the same window and the same footing as every other leg
> §5 reads.

**THE GROUND.** That cash **leaves the group and can never reach the
owner.** Both constructions agree it is gone — the issuer deducts it and we
did not — and only one of them counted it. It is not a difference of
definition, of the kind E101 exists to surface and leave alone; it is a
leakage that one of the two arithmetics simply omitted.

**HOW IT WAS FOUND, because the method matters.** E101's construction check
against **Imperial Brands** reconciled to the pound and left this line
standing in the issuer's build and absent from ours:

```
Cash flows from operating activities                          3,627
Net capital expenditure                                        (338)
Cash interest                                                  (384)
Minority interest dividends                                    (156)
Free cash flow                                                2,749
```

**£156m a year — 4.9% of FCF0 on that name.** Nothing in this project would
have found it: E40 verifies that a figure was correctly transcribed and
cannot see a leg that was never entered, which is precisely the blind spot
E101 was built for. **It is structural across every name with minorities,
not a fact about Imperial.**

**WHAT ARGUES AGAINST IT, RECORDED AS DECIDED RATHER THAN OVERLOOKED.**
**A single year's distribution is not necessarily what the minority is
worth.** A subsidiary may pay nothing for years and then a large special
distribution; a minority may be worth far more or far less than the cash it
happens to draw. **So this is a CASH MEASURE and is not, and does not claim
to be, a valuation of the minority stake.** It measures what left, on the
window §5 already reads, and nothing more.

**THE ALTERNATIVE WAS CONSIDERED AND DECLINED.** Carrying the minority as a
**liability in the net-debt bridge** — at book, or at a multiple, or at a
share of enterprise value — is the textbook treatment and it is refused
here **because it would add another unaudited valuation lever beside the
pre-registered growth view.** E29 declines exactly that for the discount
rate, on exactly this ground: a second dial nobody has pre-registered is a
second place to arrive at the answer you wanted. A cash figure the filing
states has no dial on it.

**WHERE THERE IS NO MINORITY, THE ZERO IS NAMED (E25).** A company with no
non-controlling interests states so, and the leg is **ZERO on E25's note or
caption basis, with the evidence cited** — never an inferred zero. An
absent field is not a zero: it is **DATA MISSING, and §5 does not run**,
like any other leg FCF0 is built from. A record that coerced this to zero
would report itself complete while overstating the flow by the whole of a
group's distributions to its minorities.

**WHAT THIS DOES NOT DO.** It does not re-value any minority stake. It does
not touch the net-debt bridge, which continues to carry financial debt,
leases and the E35/E35.1 legs and **no equity claim of any kind**. It does
not change E34's interest treatment, E36's SBC deduction or E70's lease
rule. And **it writes no fair value**: every affected name is re-struck
only when the owner writes it.

**WHICH EARLIER RULING THIS AMENDS.** **E34** — FCF0 gains a leg, and it is
a deduction. **E35/E35.1** — unchanged, and expressly so: the bridge is
where this was NOT put. **E29** — its refusal of an unaudited second lever
is the precedent for declining the liability treatment. **E25** — governs
the zero. **E101** — this is its first structural finding, and the answer
to "does a disagreement ever mean our construction is wrong" is: this time,
yes.

---

### E106 — a leg whose absence cannot move fv_base by more than 3.5% does not refuse the valuation

**RULED 2026-09-04 by the owner, on what E105 cost. Written before the code.**

**THE PROBLEM E105 EXPOSED.** Today any missing leg refuses the whole
valuation regardless of its size. E105 added one field and **seventeen names
went from a complete record to DATA MISSING** — on a leg that is **zero for
most of them**. A framework that cannot tell a leg worth 5% of the answer
from a leg worth nothing is not being strict; it is being indiscriminate,
and the two are not the same virtue.

**THE RULE.**

> **1. A LEG WHOSE ABSENCE CANNOT MOVE `fv_base` BY MORE THAN 3.5% ON ANY
> PLAUSIBLE VALUE DOES NOT REFUSE THE VALUATION.** The value is struck, and
> struck **COMPLETE** — not marked, not provisional — with the leg **NAMED AS
> UNDETERMINED and its bound stated** wherever the figure appears.
>
> **2. A LEG ABOVE THAT BOUND REFUSES, exactly as now.**
>
> **3. A LEG WHOSE SIZE CANNOT BE BOUNDED AT ALL REFUSES REGARDLESS.** **An
> unbounded absence is not a small one.** "We do not know what this is" and
> "we know this is at most X" are different states, and only the second is
> tolerable. A bound is itself a figure and needs its evidence like any
> other.
>
> **4. THE UNDETERMINED LEGS ARE SUMMED.** If their **combined worst case**
> exceeds 3.5%, the valuation **REFUSES even though no single leg does.** A
> tolerance applied leg by leg is not a tolerance; it is a way of admitting
> any number of them.
>
> **5. A LEG THE ACCOUNTS SHOW DOES NOT EXIST IS BOUNDED AT ZERO AND DOES
> NOT COUNT TOWARD THE TOLERANCE AT ALL.** No non-controlling interest line
> in the balance sheet, no such caption anywhere in a searched report: that
> is **E85's shape — a SEARCHED absence, recorded with WHAT WAS SEARCHED**,
> and it is a fact about the accounts rather than about the reader. It is
> not an undetermined leg; it is a determined zero, and the tolerance is
> left free for legs that are genuinely unknown.

**THE REASONING, AND IT IS MINE.** *This framework is strict everywhere else,
and it should not lose a candidate on a formality when the leg in question
cannot move the answer by more than a fraction of the cushion.* The tier-1
cushion alone is 15% and the tightest is 35%; a leg bounded at 3.5% is at
most a fifth of the loosest of them.

**3.5% IS MY NUMBER, CHOSEN AND NOT DERIVED.** It is **not a statement about
the market and it does not move when conditions do** — unlike the regime
adjustment (E77) or the dislocation band, it is a property of how much
missing arithmetic this framework will carry, and it changes only when I say
so.

**WHAT THIS GIVES UP, STATED PLAINLY RATHER THAN DISCOVERED LATER.** **A
struck value may now carry a known unquantified gap of up to 3.5%** — and
3.5% is **large enough to move a name across its buy line.** A name at
MBP + 2% is, on the worst case of its undetermined legs, a name below its
MBP. That is accepted knowingly, and it is the whole of what is traded for
not losing seventeen names to a leg that is usually zero.

**NOTHING ELSE ABOUT THE BUY CHAIN CHANGES.** The gates still apply, the E76
reading still applies, the §4.4 score and the tier still apply, and **the
owner's write is still what puts a figure on the watchlist.** This rule
governs one question only: whether §5 may produce a number at all.

**WHICH EARLIER RULING THIS AMENDS.** **E19/E21** — a basis with an absent
leg no longer refuses unconditionally; it refuses on SIZE. **E105** — its
first beneficiary, and the case that produced this. **E85** — its searched
absence becomes a determined zero here, not merely a recorded one. **E25** —
untouched: an absent figure is still never read as zero, and clause 5 is a
statement the ACCOUNTS make, not one the reader infers. **E40** — untouched:
every leg that IS present is verified exactly as before.

---

**APPLIED 2026-09-04 — clause 1's "ON ANY PLAUSIBLE VALUE" DECIDES A
DIRECTION, and the first implementation had it wrong for half the cases.**
The code perturbed every bounded leg DOWNWARD. That is right for E105's
shape — a DEDUCTION struck at zero, whose plausible values are all below
the struck one — and wrong for E70's, an ADD-BACK struck at zero, whose
plausible values are all **above** it. Perturbing an add-back downward
measures a move that cannot happen and misses the one that can. The store
now records `bound_direction` (`reduces` | `raises` | `either`), the two
directions are **summed separately** and the larger absolute move taken —
netting them would let two unknowns cancel, and two unknowns pointing
opposite ways are not one smaller unknown. Nothing in the ruling changes;
this is what clause 1 already said.

**APPLIED 2026-09-04 — A. O. SMITH, and the answer is NO.** AOS is the
first name to reach clause 3 on a leg that is not E105's. It tags no
`us-gaap:OperatingLeasePayments` and prints no supplemental cash-flow lease
line, so E70's add-back cannot be made present by any search. Note 4 bounds
it — operating lease expense **6.4** (cost of products sold) + **16.8**
(SG&A) = **23.2**, a ceiling because it also carries the 1.8 short-term and
5.8 variable lease costs ASC 842 keeps out of the liability, and because
the note states cash and expense are materially consistent. **23.2 moves
`fv_base` by 4.27%, past 3.5%, so AOS REFUSES** — clause 2, exactly as
before the ruling. The bound is not the failure; it is the measurement, and
a name that used to read "a leg is absent" now reads "the leg is worth at
most 4.27% of the answer and that is too much".

**AND THE GATE ASKS CLAUSE 4 TOO.** A bounded leg lets its ratio form —
clause 3's whole point is that a ceiling is not INPUT MISSING — so without
the gate asking, `vss manual` would print MAY RUN over a record that
refuses. **Where no pre-registered growth view exists the gate REFUSES
rather than passing:** there is no `fv_base` to take 3.5% OF, and an
unmeasured bound is not a small one.

---

### E107 — `zero_basis` accepts a fourth kind: `searched`

**RULED 2026-09-04 by the owner, to make E106's clause 5 statable. Written
before the code.**

**THIS IS NOT A NEW PRINCIPLE.** It is **E85's NOT PRESENTED evidence form
applied to a field where it was missing.** E85 already distinguishes a
concept the filer did not tag from a concept a *searched report* does not
contain, and rests the second on the search. `zero_basis` never carried that
form: it accepted `caption` (the issuer lists the line and shows nil),
`note` (a sentence says there is none) and `subtotal` — all of which need
the issuer to have *said something*. **A filing that is simply silent about
a concept could not be recorded at all**, and E106 clause 5 turns on exactly
that silence.

**THE RULE.**

> **`zero_basis: searched` — a RECORDED SEARCH of a NAMED DOCUMENT for a
> NAMED CONCEPT, finding it absent.**
>
> It carries **E85's requirements**, on the field:
>
> * **the DOCUMENT** searched, named as a document and not as a company;
> * **the SCOPE** of the search — the terms looked for, so a later reader
>   can tell a thorough search from a lucky one;
> * **the DATE** the search was made.

**AND THE REASON THE THREE ARE REQUIRED, which is the owner's own sentence:**
*a search that found nothing is a fact about the SEARCH until it is
recorded; recorded, it is a fact about the FILING.* Without the document it
is not repeatable; without the scope it cannot be judged; without the date
it cannot be superseded by a later filing. **A `searched` zero with any of
the three absent is not evidence, and the loader refuses it.**

**WHAT IT DOES NOT DO.** It does not weaken E25 by an inch. E25's rule is
that **an absent figure is never read as zero**, and that stands: a
`searched` zero is not an absence, it is a **finding** — somebody looked, in
a named place, on a named day, and recorded what was not there. Nor does it
license a search of the wrong document: a concept absent from a press
release is not a concept absent from the accounts, and the document named
must be one where the concept would appear if it existed.

**WHICH EARLIER RULING THIS AMENDS.** **E25** — its `zero_basis` vocabulary
gains a fourth value, and only that. **E85** — its evidence form is
generalised from the XBRL path to any field. **E106** — its clause 5 becomes
statable, which is the whole reason this was raised.

---

### E108 — the SENSITIVITY FLOOR: a leg that cannot move `fv_base` by 1% is exempt from READ-BACK, and never from PROVENANCE

**RULED 2026-09-04 by the owner, in the same instruction that landed E105,
E106 and E107. Written before the code.**

**THE RULE.**

> **PERTURB EACH LEG BY ±10%. IF THE LARGER OF THE TWO MOVES IS BELOW 1% OF
> `fv_base`, THE LEG IS `VERIFIED-EXEMPT`:** section 5 runs on it without
> the owner's read-back.
>
> * It is **RECOMPUTED ON ANY CHANGE OF BASIS.** The exemption is a
>   property of the leg *at this window*, exactly as E21's blocking set is,
>   and a new quarter re-decides it rather than inheriting it.
> * It is **EXEMPT FROM READ-BACK AND NEVER FROM PROVENANCE.** The figure
>   still carries its source, its page and — where it is a zero — its
>   `zero_basis` under E25. What is waived is the second pair of eyes, not
>   the evidence.

**THE GROUND, AND IT IS E21's OWN.** E21 already refused to gate on figures
a run cannot read, on the argument that *requiring them bought nothing*.
This is the same argument one step further in: a figure the run READS but
whose exactness cannot move the answer by a hundredth also buys nothing,
and a gate that never opens is a gate somebody works around. KAR.ST stands
at **63 blocking figures** on a store nobody has read back; the cost of
that is not rigour, it is a name that never gets valued at all.

**WHAT THE FLOOR CANNOT SEE, STATED RATHER THAN DISCOVERED.** *Perturbing an
entered figure by ±10% cannot catch a figure that is entered WRONG* — a
transcription off by a factor of ten, a quarter read out of the wrong
column, and above all **a ZERO that should not be there**, which perturbs to
zero and looks immovable. That is why the exemption is from READ-BACK ONLY.
**E25 still requires a zero to name its evidence** (`zero_basis`, with the
caption, note, subtotal or E107 search behind it), and **E40 still requires
every figure to carry its page.** The floor decides how much SCRUTINY a leg
earns; it decides nothing about whether the leg needs EVIDENCE.

**A ZERO LEG IS EXEMPT WITHOUT A VALUATION, AND THIS IS NOT A SHORTCUT.**
±10% of zero is zero, so a leg entered at zero on the basis moves `fv_base`
by exactly 0.0% — which is below 1% of any `fv_base` there is, whatever the
growth view, the rate or the bridge. The store alone settles it, and the
gate may therefore exempt a zero leg without building a record. **Every
other leg's exemption is MEASURED, on the record, against that record's own
`fv_base`** — never assumed from the leg looking small.

**1% IS THE OWNER'S NUMBER AND IT IS NOT E106's 3.5%.** They answer
different questions and must not be confused. **E106's 3.5% is what a
MISSING leg may be worth** and still let the valuation run; **E108's 1% is
what a PRESENT leg may move** and still skip the read-back. The second is
deliberately the tighter of the two: an absent leg is known to be absent,
and an unread one is not known to be anything.

**APPLIED 2026-09-04.** On the E105 legs: every determined zero — AOS, DECK,
EXE, LII, ULTA, NVR, CTSH, GDDY, APN.L, KAR.ST, LIAB.ST, ZZ-B.ST, AUTO.L,
RMV.L — is exempt on the zero limb. ACN's −3,492,000 needs no exemption: it
is VERIFIED by provenance (E40 `cross_document`) because the filer tags it
and the equity statement states it. RKT.L's −6 and SAP.DE's four quarters
are measured on the record.

**WHICH EARLIER RULING THIS AMENDS.** **E21** — its blocking set gains an
exemption, on the same reasoning that built it. **E40** — untouched on
provenance; a `VERIFIED-EXEMPT` figure carries its page like any other, and
`verified_kind` remains a property of a verification that HAPPENED. **E25**
— untouched, and expressly so: this is where the floor is blind, and E25 is
what covers the blind spot. **E106** — its tolerance is a different question
with a different number; neither reads the other's.

---

**APPLIED 2026-09-04 — TWO QUESTIONS THE BOUND MACHINERY RAISED, BOTH
ANSWERED BY THE OWNER THE SAME DAY.**

**(a) A BOUND MAY BE FORMED BY LOOSENING ARITHMETIC AND NEVER BY TIGHTENING
ARITHMETIC.** Adding two stated figures to reach a wider ceiling is
allowed; subtracting stated figures to reach a narrower one is not.
*The owner's ground, and it is the asymmetry E35 already uses:* **a bound
that is too wide costs nothing, and a bound that is too tight lets a
valuation run that should not.** AOS is the case — its stated 6.4 + 16.8 =
**23.2** stands and refuses at 4.27%, while 23.2 − 1.8 − 5.8 = **15.6**
would have cleared at about 2.9% and is not taken. E22 is unchanged and
this does not weaken it: a bound is still never a value, and neither
operation may produce one.

**(b) AN UNVERIFIED BOUND DOES NOT BLOCK SECTION 5, and E21 answers this
itself.** E21 refuses on *"an UNVERIFIED figure THE CURRENT BASIS READS"* —
no ratio takes a bound's value, and the leg enters the arithmetic at zero,
so the basis reads nothing there. What binds a bound is clause 3's own
condition, *a bound is itself a figure and needs its evidence like any
other*, and the loader enforces it: **a bound with no page is refused at
the load.** E40 is untouched.

---

### E109 — the pre-registered growth view lives in a MACHINE-READABLE block on the watchlist entry

**RULED 2026-09-04 by the owner, choosing between the watchlist and the
store: *"It belongs with the name I'm watching, not with the store of
figures."***

**THE PROBLEM.** E28 requires the three growth rates to be written before
any fair value is solved, and they were — in
`reference/growth-views/<TICKER>.md`, in prose, and then **copied by hand
into whichever `tools/` script struck the name.** No code could read either.
The cost showed the day E108 arrived: the sensitivity floor is defined
against `fv_base`, `fv_base` needs the view, and `vss manual` could not get
one — so the floor's measured limb existed and could never run from the
command that gates every store.

**THE RULE.**

> **The watchlist entry carries a `growth:` block: `base`, `bear`, `bull`,
> the `view:` file the reasoning was written in, and the `registered:`
> date it was written on.** `base`, `view` and `registered` are required;
> `bear` and `bull` come as a pair or not at all.
>
> **THE NUMBERS ARE STILL THE OWNER'S AND NOTHING COMPUTES ONE.** This
> moves where the rates are written; it does not change who writes them or
> when. **E28's ordering is untouched and becomes CHECKABLE for the first
> time** — a view whose file and date are on the entry can be shown to
> predate the value it produced, which prose in a second directory never
> could.
>
> **A NAME WITH NO BLOCK HAS NO VIEW, AND THAT IS E28's ANSWER, NOT A
> GAP.** It is never read as zero growth: no view, no fair value.

**WHY NOT THE STORE.** `config/manual/<TICKER>.yaml` holds **figures the
accounts state**. A growth view is a judgement about the future that no
filing contains, and putting it there would make it look like one more
thing read off a page.

**WHAT IT MAKES STRICTER, WHICH IS THE OPPOSITE OF WHAT A NEW READER MIGHT
EXPECT.** A name with no registered block gets **no** E108 exemption and
**no** answer to E106 clause 4 — so the gate refuses where it previously
could not even ask. Adding the block can only ever be asked for by a name
that wants to be measured.

**TRANSCRIBED 2026-09-04, and transcription is not authorship:** LIAB.ST,
SAP.DE, NKE, DECK, PNDORA.CO, AUTO.L, RMV.L, NVR, CTSH, GDDY — each with
the rates, the file and the registration date it already carried. **Five
names with registered views are NOT watchlist entries** — ACN, AOS, LII,
RKT.L, ULTA — and their views stay unreadable by code, which is a
consequence of this choice and is recorded rather than worked around.

**AND THE FIVE ARE LEFT WHERE THEY ARE — ruled 2026-09-04, on the owner's
own ground: entering a name on the watchlist stamps `dd_at_entry` and
FREEZES GATE 1 UNDER E12.** Adding ACN, AOS, LII, RKT.L and ULTA so that
five prose files become machine-readable would freeze five catalyst windows
for no reason, and a frozen drawdown is a harder thing to undo than an
unread growth view. **They stay struck-but-unmeasured, and the gate says so
rather than passing.**

**WHICH EARLIER RULING THIS AMENDS.** **E28** — its location, and only
that; the pre-registration requirement, the ordering and the authorship are
unchanged. **E108** — its measured limb becomes runnable. **E106** — its
clause 4 becomes askable by the gate. **E12** — untouched, and the reason
the five are not simply added.

---

### E110 — an issuer's own words that an item is IMMATERIAL, NOT SIGNIFICANT or NIL are evidence of the same class as a stated zero

**RULED 2026-09-04 by the owner, on CROX's asset retirement obligations and
MUSA's loyalty deferred revenue, and ruled GENERALLY so it stops coming
back.**

**THE PROBLEM.** US filers dispose of small balances in words rather than
in figures. Crocs: *"Asset retirement obligations were **not significant**
to the consolidated balance sheets in the years ended December 31, 2025, or
2024."* Murphy USA: *"The deferred revenue balances at December 31, 2025 and
2024 were **immaterial**."* Neither is a stated nil, and neither is a
number — so under E25 it was not a zero and under E106 it was not a bound,
and two otherwise complete records refused on a sentence the issuer had
already answered.

**THE RULE.**

> **WHERE AN ISSUER STATES IN ITS OWN WORDS THAT AN ITEM IS IMMATERIAL, NOT
> SIGNIFICANT, OR NIL, THAT STATEMENT IS EVIDENCE OF THE SAME CLASS AS A
> STATED ZERO.** It is quoted with its page and it **RESOLVES THE LEG**, on
> E25's `note` basis.
>
> **NO PERCENTAGE AND NO THRESHOLD OF MINE.** There is no dial here and none
> is being added: the filer's own words are the evidence, and nothing in
> this framework sets a number the words have to beat.
>
> **IT APPLIES WHEREVER IT OCCURS**, on any leg, not only to the two names
> that produced it.

**THE GROUND, AND IT IS E25's OWN DISTINCTION.** E25 rests on the line
between a **SILENCE** and a **CLAIM**. *An absent figure is never read as
zero* because absence says nothing. **An issuer writing "immaterial" has
said something**: it has asserted that the item falls below its own
materiality threshold, which is a claim about its own accounts made in a
document it signed. That is the same kind of evidence as a caption showing
a dash — the company speaking about its books — and it is a different kind
from the framework guessing.

**WHAT IT GIVES UP, RECORDED RATHER THAN DISCOVERED.** **Materiality is the
ISSUER'S threshold and it is not published.** A filer's number for it is a
matter of judgement, applied to its own scale, and this rule accepts that
judgement **in place of a figure**. For the companies §5 reads, an item
below a filer's own materiality is far under 3.5% of anything §5 forms —
but that is the reason the trade is acceptable, **not a test the rule
applies**, and no such test is written here.

**WHAT IT IS NOT.** It is not a licence to read "immaterial" onto a leg the
issuer did not use the word about: the sentence must be about **the concept
the field holds**, and it is quoted so a reader can see that it is. Nor
does it reach a filer that says nothing — that is still DATA MISSING, and
E106 clause 3 is still where a bound would have to come from.

**WHICH EARLIER RULING THIS AMENDS.** **E25** — its `note` basis gains this
form of sentence explicitly; the rule that an ABSENT figure is never a zero
is untouched, because this is not an absence. **E106** — clause 3 is not
reached where the issuer has spoken, and is unchanged where it has not.
**E85 / E107** — a search is what a reader does; this is what the FILER
said, and the second outranks the first.

---

### E111 — `INTAKE`: a status meaning READ, NOT WATCHED

**RULED 2026-09-04 by the owner, closing the deadlock E109 created.**

**THE DEADLOCK.** E109 put the machine-readable growth view on the WATCHLIST
ENTRY, because a view belongs with the name being watched. But **E12 stamps
`dd_at_entry` and freezes Gate 1 the moment a name is entered** — so the only
way to give a name a readable view was to start its clock. Five names with
registered views were left unreadable for exactly that reason, and three
newly intaken ones had nowhere to put a view they were waiting for.

**THE RULE.**

> **`INTAKE` is a sixth status: READ, NOT WATCHED.**
>
> It **MAY** carry a `growth:` block, a store, and a struck value.
>
> It carries **NO `dd_at_entry`, NO `peak_date`, NO `stop_price`, NO `tier`
> — and therefore NO MBP**, since `compute_mbp` is `fv_base` × the tier
> multiplier. The loader **REFUSES** an INTAKE entry carrying any of them.
>
> It collects **NO VERDICTS** and is never `actionable`.
>
> **PROMOTION TO PIPELINE IS WHAT STAMPS E12's ENTRY, and that promotion is
> the owner's act.**

**THE GROUND, IN THE OWNER'S WORDS.** *E12 freezes Gate 1 because a pipeline
name is review work with a dated starting point. A name I have only read the
figures of has no such starting point and should not get one by accident —
but its growth view has to live where a machine can read it, or E108 and
E106 clause 4 cannot run for it.*

**IT IS DROPPED's ARGUMENT, FOR THE OPPOSITE REASON.** DROPPED collects no
verdicts because there is nothing left to decide; INTAKE collects none
because nothing has been decided yet. In both cases the entry checks would
be answering a question nobody is asking.

**APPLIED 2026-09-04 to eight names.** ACN, AOS, LII, RKT.L and ULTA — which
had registered views and no entry, and whose views are now transcribed;
CROX, LOPE and MUSA — intaken the same day, **and carrying NO view, because
the views are the owner's and he writes them after reading the business.**

**WHICH EARLIER RULING THIS AMENDS.** **E109** — its block now has somewhere
to live for a name nobody has entered, which is what it was missing.
**E12** — untouched, and the reason this status exists: its clock still
starts at PIPELINE and nowhere else. **E27** — the status vocabulary gains a
sixth value; the WATCH split is unchanged.

---

### E112 — Gate 3's interest-coverage numerator is OPERATING INCOME AS STATED, impairments included

**RULED 2026-09-08 by the owner, on the question CROX's 1.69× raised, and
ruled GENERALLY because it will recur on every filer with an impairment.**

**THE RULE.**

> **For §3 Gate 3's interest-coverage limb the numerator is OPERATING INCOME
> AS THE ACCOUNTS STATE IT, with impairments and every other charge left
> in.** Nothing is added back. The denominator is unchanged
> (`net_finance_costs`, E25's guarded one).

**THE REASONING, AND IT IS THE OWNER'S.** *An impairment is the company
writing down what it paid for something, and a coverage ratio asks whether
the business as reported can service its debt. Adjusting it out would
substitute my judgement of what counts as recurring for the accounts' own
figure* — **which is the substitution E22 and the adjusted-versus-reported
rule both refuse.**

**WHAT THIS GIVES UP, STATED PLAINLY RATHER THAN DISCOVERED LATER.** **A
company with one large genuine one-off will fail a limb it would pass on any
normalised basis.** CROX is the case that produced this: FY2025 income from
operations **149,515** over interest expense **88,287** is **1.69×**, and the
numerator carries **738,115** of HEYDUDE impairments — **307,000** of
goodwill and **431,115** of assets. Without them the ratio is about **10×**.
Under this rule **it is 1.69× and the limb fails.** That is accepted
knowingly, in exchange for **a numerator nobody has to argue about.**

**WHERE THE DIFFERENCE IS MATERIAL, THE REPORT PRINTS BOTH AND NAMES THE
ADJUSTMENT, AS INFORMATION.** The adjusted figure is never the verdict and
never enters a gate; it is printed so a reader can see the size of what the
rule is refusing to net out, and decide for himself what it means.

**THE ASYMMETRY THIS CREATES IS ONE-DIRECTIONAL, and it is worth naming
because it bounds the rule's whole effect.** Not adjusting can only make the
numerator SMALLER, so this rule can only ever move a name DOWN through the
5× line and never up. **A name above 5× on stated operating income is above
it on any adjusted basis too** — so the rule can change no verdict except
for a name already failing.

**APPLIED 2026-09-08 ACROSS EVERY STORED NAME.** Eleven stores can form the
ratio at all; the rest carry no `operating_income`, because the SEC XBRL
path deliberately writes none (`OMITTED_FIELDS`). Of the eleven **only
SYNSAM.ST is below 5×** (4.36×) — and its interim reports carry **no
impairment in EBIT**, so it fails on ordinary trading and is on the same
side under either reading. **NO STORED NAME CHANGES SIDE.** CROX is the only
name the rule bites, and CROX was dropped the same day on Gate 2.

**WHICH EARLIER RULING THIS AMENDS.** **E22** — this is its principle
applied to a ratio's numerator rather than to a figure. **E25** — the
denominator's zero guard is untouched. **E30** — Gate 3's surviving limbs
are unchanged in substance; this settles how one of them is READ. **E83** —
consistent and not in tension: there a stated figure outside a band was
ACCEPTED because the issuer printed it and the accounts explained it, and
here a stated figure is likewise accepted over an adjustment nobody printed.

---

---

### E113 — a field the `fv_base` COMPUTATION NEVER READS cannot block section 5

**RULED 2026-09-08 by the owner, on the residue E108's repaired measured
limb left behind. Written as an extension of E108's own ground, not as a
new principle.**

**THE OWNER'S GROUND, in his own terms:** *E108's ground already covers it —
a leg that cannot move the value by any amount is below any floor — and the
gate refusing on a field the valuation does not read is the inverse of the
rule's own purpose.*

**THE RULE.**

> **A FIELD THAT THE `fv_base` COMPUTATION NEVER READS IS
> `VERIFIED-EXEMPT`.** It is not a leg of the flow, not a leg of the
> bridge and not the divisor; perturbing it moves the value by nothing at
> all, which is below E108's 1% for any `fv_base` there is.
>
> **THE GATE MUST NAME THEM.** A field exempted on this ground is printed
> with the ground stated, in the same flag block E108's other limbs use.
> **An exemption nobody can see is the failure this whole area already
> had** — the measured limb sat dark for four days because a lookup that
> misses looks exactly like an exemption that was not earned.

**WHAT IT GIVES UP, and the owner named it himself.** **Such a field keeps
its PROVENANCE and its PAGE.** E40 is untouched: the figure still carries
the document and the line it was read from, and a zero still carries its
`zero_basis` under E25. What is given up is a READ-BACK — a second pair of
eyes on a number that cannot change the answer being gated. **It is simply
not a reason to refuse a value it has no part in.**

**AND WHAT THAT COSTS, STATED RATHER THAN DISCOVERED.** These fields are
not worthless — `revenue`, `operating_income` and `net_income` are read by
§4.2's hard kills, §4.3's flags and E101's conversion check, and
`ebitda` by §5.3. **This ruling does not exempt them from anything those
sections require.** It says only that the SECTION 5 READ-BACK GATE, whose
whole subject is the fair value, may not refuse on them. A name whose
revenue is wrong still fails §4.2 on the wrong revenue; it just does not
fail §5 on it.

**THE IMPLEMENTATION IS AN EXPLICIT LIST AND DELIBERATELY NOT A
SUBTRACTION.** `manual.NON_VALUATION_FIELDS` names the fields by hand, and
the exemption requires BOTH that a field be on it AND that the measured
limb say nothing about it. **The reason is the asymmetry of the two
failure modes.** The bug E108's repair fixed made the gate too STRICT,
which is safe; the same bug under this rule would make it too LOOSE, which
is not — a leg that stopped being emitted would be silently exempted
rather than loudly refused. A hand-maintained list cannot fail that way:
a field has to be put on it.

**FOUR FIELDS ARE NOT ON THE LIST THOUGH NO STORE TODAY USES THEM**, and
they are the ruling's own worked example of why an empirical list would
have been wrong:

- **`net_finance_costs`** is the interest leg for an E34.1 filer
  (`interest_source: income_statement_net`);
- **`finance_costs_period`** is the leg for an E61 filer
  (`interest_source: interest_expense_only`) — which is CRUS;
- **`income_tax_paid` and `operating_cash_flow_pretax`** form the operating
  cash flow for a filer that presents it before tax;
- **`noncurrent_derivative_assets_on_debt`** is a bridge leg wherever an
  issuer's own net-debt reconciliation carries one.

**Each is absent from every record built on 2026-09-08 and each would have
been swept into a list derived from what was observed.** The list is
reasoned from what the arithmetic READS, and
`tests/test_manual.py::test_no_field_that_ever_reaches_a_valuation_is_exempt_under_E113`
holds it to that across every committed store.

**WHAT THIS DOES NOT DO.** It does not touch **residual 2**, left standing
by the owner in the same instruction: on a TTM basis the sensitivity map is
BASIS-LEVEL and the gate applies it PER PERIOD, so a quarter's leg is
refused on the summed leg's sensitivity. *"I would rather it refuse too
much there than too little."* That stays.

**A FIELD ANOTHER GATE LIMB READS IS NOT ONE E113 MAY EXCUSE, and the
implementation was narrowed twice on the day it was written — by tests
going red, which is the only reason it is right.** `fv_base` is not the
only thing `section5_gate` computes, and a field out of the VALUATION can
still be in the GATE:

- **`net_finance_costs` and its two operands** are read by E25's
  zero-coverage-denominator limb, DIRECTLY and outside FCF0 entirely,
  whatever interest shape E34 picked for the flow. The first cut subtracted
  `interest_legs` and exempted them; `interest_read_names` — E60's own
  function, which already knew this — is what the rule subtracts now.
- **The point-in-time SHARE COUNTS** are not on the list at all. E88 keeps
  them MEMO and never promotes one to the divisor, so `fv_base` does not
  read them — but `share_count_on_basis` reads E80's issued-less-treasury
  pair for its own purposes, and E54's rule that *a computed net's OPERANDS
  are what a person has to check* has held since it was written.

**So the rule is narrower than its own first sentence suggests, and the
sentence is left standing because the narrowing is the interesting part:
"the `fv_base` computation never reads it" is necessary and NOT
sufficient. The field must also be read by no other limb of the gate.**

**WHICH EARLIER RULING THIS AMENDS.** **E108** — extended to its own limit:
the floor exempts a leg that moves `fv_base` by less than 1%, and this
names the case where the move is not small but ZERO BY CONSTRUCTION. **E40**
— untouched, and expressly: provenance is not waived, only the read-back.
**E25** — untouched; a zero still names its evidence, and its
zero-coverage limb keeps every field it reads. **E54** — untouched; a
computed net's operands still refuse. **E60** — its `interest_read_names`
becomes the thing this rule subtracts. **E21** — its blocking set loses a
class it should never have held, and keeps every class another limb needs.


---

### E114 — the SHADOW BOOK: every refusal measured against the market from the day it was written

**RULED 2026-09-08 by the owner. Adds a record; amends no rule, gates
nothing, and may not reach a price.**

**THE PROBLEM.** This framework has evaluated names and **refused all of
them**, and nothing in it measures what a refusal cost or saved. **A
process that only refuses, and never scores its refusals, cannot be
falsified** — and **§0 rule 3** makes falsification the default posture
toward *every* candidate, not only the ones that survive. **B45's sales
record measures EXITS only**, and there are no entries to measure. This
closes the other half.

**THE RULE.**

> **A SHADOW BOOK is kept, one row per name, written at the moment a
> verdict is written. It records exactly six things and NOTHING ELSE:**
>
> 1. **the ticker**;
> 2. **the date the verdict was written**;
> 3. **the verdict and its standing** — `DROPPED`, `WATCH-GATED` or
>    `INTAKE`, and whether that verdict is `STANDING` (holds until
>    deliberately removed), `EXPIRY` (re-read when a named event arrives)
>    or `OPEN` (nothing has been decided yet);
> 4. **the SETTLED CLOSE on that date, in the name's own quote currency**;
> 5. **the fair value, IF ONE WAS STRUCK** — blank where none was;
> 6. **ONE LINE naming what decided it.**
>
> **NO THESIS. NO EXPECTATION. NO TARGET.** A row that argues is a row
> that will be re-argued, and the book exists to be read against the
> market, not against itself.
>
> **THE BASELINE IS NEVER SUBSTITUTED.** Where no settled close exists on
> the verdict date — the date fell on a Saturday, the date is today and
> the bar has not settled, the vendor carries no bar — the close is
> **DATA MISSING** and stays so. **The nearest bar is not the close on
> that date**, and B45's rule that a price is never read off a bar the
> owner did not transact on is the same rule.

**WHAT IT THEN MEASURES, from the nightly run's own price path.** The
price today against the price at the verdict, and **the same interval for
a benchmark — OMXS30 and the S&P 500, in the NAME'S OWN QUOTE CURRENCY** —
at **1, 3, 6 and 12 months** from the verdict date.

> **A WINDOW THAT HAS NOT ELAPSED REPORTS `INCOMPLETE` AND IS NEVER FILLED
> WITH A PARTIAL FIGURE.** This is the threshold report's own rule
> (`reports/THRESHOLD-REACHABILITY-2026-08-30.md`), and it is what stops a
> three-week reading being quoted as a one-year one.

**FOUR LIMITS, STATED HERE RATHER THAN LEFT IMPLICIT.** The first two were dictated with the rule on 2026-09-08; the third and fourth were ruled on 2026-09-09, and the third REPLACES a weaker clause of the same number.

**ONE — IT MEASURES WHAT HAPPENED, NEVER WHETHER THE VERDICT WAS RIGHT.**
A dropped name that rose **may have risen for exactly the reasons the
verdict refused to underwrite**: BETS-B.ST and CRUS were both refused
because a question about someone else's decision could not be judged
better than the market, and a favourable answer to that question is not
evidence the refusal was wrong. A `WATCH-GATED` name that fell **says
nothing at all until the gate's own event arrives** — the gate is a
statement about information, not about price, and E12 freezes it for that
reason.

**TWO — IT IS NOT A SIGNAL.** **Nothing in the shadow book may arm an
alert, enter a name, or reach a valuation.** It is not read by `vss run`,
it is not read by `pricewatch`, and no figure in it is an input to
anything. **It is read ONCE A YEAR, deliberately.** A book consulted more
often than that becomes a scoreboard, and a scoreboard is a reason to
change a rule for the wrong reason.

**THREE — BOTH LEGS ARE THE SAME KIND OF RETURN, AND A NAME WHOSE
DIVIDENDS CANNOT BE ESTABLISHED IS `DATA MISSING`.**

**AMENDED 2026-09-09 by the owner. The first version of this clause, one
day old, is STRUCK.** It measured the name on a PRICE return against a
TOTAL-return S&P 500, named the bias, and let it stand. **The owner's
ruling: *a shadow book exists to be able to say the method does not work,
and one that systematically flatters the refusals cannot do that.***
Naming a bias is not the same as removing one, and a caveat in a header
does not survive being read once a year.

> **THE NAME IS MEASURED ON TOTAL RETURN.** Dividends are reinvested on
> both sides of every comparison, so the name's leg and the benchmark's
> leg are the same kind of quantity.
>
> **WHERE A NAME'S DIVIDENDS CANNOT BE ESTABLISHED, THE COMPARISON IS
> `DATA MISSING` — never a price return set against a total return.** A
> series whose vendor carries no dividend record cannot be told from one
> that paid nothing, and the difference is the whole of the measurement.
> **`DATA MISSING` is the answer, and the row keeps its recorded close.**
>
> **THE RECORDED FACT AND THE DERIVED COMPARISON ARE BOTH NAMED, AND THEY
> ARE NOT THE SAME NUMBER.** The book stores the **UNADJUSTED settled
> close** — a fact that never restates, which is what a baseline has to
> be. The total return is **DERIVED BESIDE IT** at read time from the
> adjusted series. **What this gives up is stated rather than hidden: an
> adjusted series RESTATES on every dividend and split, so the derived
> comparison is weaker evidence than the stored close, and a figure this
> book printed last year may not be the figure it prints this year.**
> The report says so on its face, and it re-reads the vendor's unadjusted
> close for each verdict date and flags any row whose stored baseline no
> longer matches.

**OMXS30 KEEPS `^OMX`, WITH THE CAVEAT.** `^OMXS30GI` returned **one bar
and no history** when it was measured on 2026-09-08, so the total-return
series cannot be built from the tool's own price path at all. The price
index understates OMXS30's total return by roughly 2–4pp/yr and is
labelled a price index everywhere it appears — the substitution
`tools/threshold_reachability.py` already made and recorded. **A STATED
SUBSTITUTION IS HONEST; A SILENT MISMATCH IS NOT**, and that is the line
this clause draws: the S&P leg was a silent mismatch and is fixed, the
OMXS30 leg is a stated one and stands.

**Both index legs are converted into the name's quote currency** at the
daily rate on each end of the window, so a USD name is not measured
against a Stockholm index through a currency move neither of them made.
A return is scale-invariant, so `GBX` and `GBP` give the same figure and
the minor unit is not a source of error here.

**FOUR — A VERDICT WRITTEN ON A WEEKEND IS RE-DATED, NOT PRICED OFF THE
NEAREST BAR.**

**RULED 2026-09-09 by the owner**, on the four rows the first backfill
left blank. *A verdict written on a Saturday was struck against Friday's
close.*

> **A verdict written on a SATURDAY or a SUNDAY is re-dated to the last
> weekday on or before it**, and the row says **which date it moved FROM
> and TO**.
>
> **THIS IS NOT THE PROHIBITION IT LOOKS LIKE.** The rule against the
> nearest bar stands untouched: nothing reads Friday's close as *"the
> close on Saturday"*. **The DATE moves and the PRICE is then an exact
> match on it**, which is a different act — and the window arithmetic
> runs from the session the decision was actually struck against rather
> than from an administrative date.
>
> **THE WALK-BACK CROSSES WEEKENDS AND NOTHING ELSE, and the narrowness
> is the rule rather than a limitation of it.** A WEEKDAY with no bar is
> **`DATA MISSING`**. The tool cannot tell an exchange holiday from a
> vendor that has simply lost a day, and a rule that walked back until it
> found a price would turn the second into the first silently — which is
> the whole of what this book must not do.
>
> **A verdict written on a session that has not yet settled is NOT
> re-dated.** It waits, and its close is filled when that session
> settles. Moving it backwards would be a substitution.

**THE NARROWING WAS FORCED BY THE FIRST RUN, AND THAT IS WHY IT IS
RIGHT.** As first written the rule said *the last settled session on or
before* the written date, with no bound. On the 2026-09-09 backfill it
moved **MEKKO.HE from 2026-09-08 to 2026-09-04** — a Tuesday to the
Friday before it. Helsinki was open on both intervening days; **the
vendor is missing MEKKO.HE's 2026-09-07 and 2026-09-08 bars**, which is
the same gap that showed on 2026-09-08 across BETS-B.ST, PNDORA.CO,
NOVO-B.CO and SYNSAM.ST. The unbounded rule read a vendor outage as a
market holiday and re-dated a verdict four days for it. **MEKKO.HE is
`DATA MISSING` and waits**, which is the answer.

**The first application is its own evidence.** LULU's verdict was dated
2026-08-23, a Sunday; re-dated to 2026-08-21 its close is **121.07**, and
the watchlist note LULU was dropped on reads *"close 121.07 USD on
2026-08-21"*. The date the record carried was the day the note was
written; the date it carries now is the day the decision was struck.

**WHERE IT LIVES.** `config/shadow_book.csv`, tracked — the record belongs
in git, on the same reasoning that put the watchlist there. `vss shadow`
reads it and writes `reports/SHADOW-BOOK-<date>.md`. The command is the
B45 shape exactly: read-only, one markdown file, and no other effect.

**BACKFILLED 2026-09-08 from the record.** Every `DROPPED`, `WATCH-GATED`
and `INTAKE` name in `config/watchlist.yaml` and
`config/screener_exclusions.csv`, with the verdict date taken from the
watchlist note where the note carries one, from the exclusion CSV's
`datum` where it does not, and the source named on every row. **Three
rows — MSFT, UNA.AS and HNSA.ST — are EXITS that B45 already measures
from their FILL, and are marked so the two records are not read as one
sample.**

**CORRECTED 2026-09-09.** As first written this paragraph said four rows
carried no baseline close. **It was seven** — four verdict dates that
fell on a weekend and three written on the day of the ruling itself — and
the sentence was drafted before the backfill ran rather than from it.
**Limit four re-dates the four weekend rows and they now carry a close**;
the three written on 2026-09-08 waited for that session to settle and
were filled on 2026-09-09, which is the only way this rule ever fills
one.

**WHAT IS DELIBERATELY NOT IN THE BOOK.** `UHS` (E7), `ROCK-B.CO`
(E8-REVIEW) and `ULVR.L` (SELLING) sit in `screener_exclusions.csv` under
a `skal` that is not a verdict on the business: E7 and E8 are findings
about a METRIC, and ULVR.L is a second listing of a held line. **They are
refusals of a kind and a later ruling may put them in; this one does
not**, and the omission is recorded rather than left to be noticed.

---

## F. Rulings on the overview page

No section of FRAMEWORK.md and no ruling A1 to E114 mentions the overview
page. Items here govern it, and each states what it costs.

### F1 — the overview page may leave the VPS, behind Access, and the server that serves it is constrained

**RULED 2026-09-13 by the owner.**

No ruling governs the overview page's shape. FRAMEWORK.md v2.3 does not
mention it — its section 4 runs 4.1 to 4.4 and concerns the earnings
deep-dive — and FRAMEWORK-EDITS A1 to E114 do not mention it either. The
page was built in August 2026 under the project brief's description of it,
which describes the software and does not govern it. Two daemons now run on
the VPS to serve that page, they survive reboot, and they are committed at
`0cd8a8f`. F1 is the FIRST ruling to govern the page. It is not an amendment
and it repeals nothing.

An earlier draft of this ruling, and the commit message at `0cd8a8f`, cite
"FRAMEWORK v2.3 4.7" as prohibiting a server. That section does not exist.
The citation was asserted without reading the file and is withdrawn here.
`0cd8a8f`'s message is pushed and immutable; this paragraph is the correction
of record.

**LIMB (a) — the book may leave the VPS.**

> `reports/OVERVIEW.html` may be served over a Cloudflare Tunnel at a
> hostname gated by Cloudflare Access. The file does not leave the machine;
> the bytes do, and they pass through infrastructure I do not control.

**WHAT THIS COSTS.** Cloudflare terminates the TLS. The page is plaintext at
their edge: holdings, states, gate results, MBPs and stops, readable by
Cloudflare and by anyone who compels or breaches Cloudflare. This is not
mitigable within this architecture. It is the price of reading the book on a
phone from an arbitrary network, and I am paying it knowingly.

The gate is Access with one-time PIN to one address. It is SINGLE FACTOR.
Access MFA methods are off. Whoever controls that mailbox controls the page.
Verified 2026-09-13: two addresses other than the owner's received no PIN at
all — the policy refuses before a code is issued.

> **An Access Bypass policy on this application is PROHIBITED.** Cloudflare's
> own text: *"Access evaluates Bypass and Service Auth policies first."* One
> Bypass rule makes the book public instantly and silently.

**LIMB (b) — the server is constrained, narrowly.**

> A static file server may run on the VPS for the sole purpose of serving
> `reports/OVERVIEW.html` to the tunnel. It binds 127.0.0.1 only. No inbound
> port is opened and the firewall is not changed. The page itself remains
> read-only with no JavaScript and no framework, and that is now RULED
> rather than merely described — the page has no forms, no buttons, no
> scripts, and the server has no upload path, no directory listing and no
> execution.
>
> **The permission is exactly this wide and no wider.** It does not permit:
>
> - binding any interface other than loopback
> - serving any path other than `/` (`OVERVIEW.html`)
> - an admin API, a log endpoint, or any second route
> - any second name behind the same tunnel without its own ruling

**WHAT THIS COSTS.** A second and third daemon on a box that previously ran
one timer-driven CLI, plus a config file whose regression is silent.
`/etc/caddy/vss-overview.Caddyfile` returns 404 for every path but `/`.
`reports/` held 93 files on 2026-09-13 — SHADOW-BOOK, CTSH-PREBUY,
SALES-RECORD, BRIEFING, every daily run. Deleting the `handle { respond 404 }`
block serves all of them and nothing would alarm. That block is the boundary;
`deploy/TUNNEL-NOTES.md` says so, and any change to it is a ruling, not a
merge.

**Second cost, accepted:** `vss-tunnel.service` is a SYSTEM unit while every
other `vss-*` unit is a USER unit, because the tunnel credential stays
`root:cloudflared` 640. A system unit cannot invoke
`OnFailure=vss-failure@%n.service`. If the tunnel dies permanently the phone
stays silent and the page simply does not load. The nightly run and its
alerting do not depend on it.

**LIMB (c) — the served page states its own age.**

> **RULED: the page must render its own generation timestamp, and must mark
> itself when that timestamp is older than 26 hours.**

The page is the thing I act on. `reports/YYYY-MM-DD.md` and the
healthchecks.io observer both catch a FAILED RUN; neither catches a STALE
PAGE. A run that fails writes nothing, the server keeps serving the last good
file, and the page looks identical to a fresh one. I read the states
believing they are today's. That failure mode is indistinguishable from
success and this limb removes it.

**REQUIRED:**

1. The page renders its generation timestamp, ISO 8601 with timezone, in the
   header, visible without scrolling on a phone.
2. When now minus generated exceeds 26 hours, the page marks itself stale in
   a way that cannot be missed at a glance.

**WHY 26.** `vss.timer` fires 22:30 CEST. A healthy page read at 22:00,
before that night's run, is 23.5h old. N must exceed that or the mark is a
false positive. 26 gives 2.5h of margin and flags a single missed run by the
following morning.

**WHAT THIS COSTS.** The stale mark is the page rendering a judgement about
itself, and this project's design is that the page measures and I decide. This limb
permits exactly one such judgement — the age of the file — and no other. The
page still renders no verdict about any NAME. E-series rulings on what the
page may and may not say are unchanged.

**Second cost:** 26 is a fixed number and the timer's schedule is not in the
ruling. If `vss.timer`'s schedule ever changes, 26 must be re-ruled or the
mark becomes wrong in one direction or the other.

**This limb is a REQUIREMENT on the generator, not a permission. Until it is
implemented the page is non-compliant with F1.**

### F2 — F1 limb (c) requirement 2 is withdrawn as unbuildable

**RULED 2026-09-13 by the owner.**

F1 limb (c) required the page to mark itself stale when its generation
timestamp is more than 26 hours old. That is not buildable and the ruling
was made without knowing it.

The page is a static file. Its generation timestamp is set at the instant it
is written, so at render time the age is always zero. The comparison F1
requires happens when the page is READ — hours or days later — and a static
HTML file evaluates nothing at read time. Doing it would need JavaScript in
the page, and F1 limb (b) prohibits JavaScript. Limb (b) and limb (c)
requirement 2 contradict each other; limb (b) stands and requirement 2
falls.

> **WITHDRAWN: F1 limb (c) requirement 2.** The 26-hour threshold is
> withdrawn with it and is not a live number anywhere.
>
> **UNCHANGED: F1 limb (c) requirement 1.** The page renders its generation
> timestamp, ISO 8601 with offset, in the header and in the footer's first
> sentence. Implemented 2026-09-13.

**WHAT THIS COSTS.** The failure mode limb (c) named is not closed. A page
served after a failed run still looks like a fresh one, and the reader must
read the timestamp and do the subtraction. What remains is that the page
cannot be SILENT about its age — it states it twice, in ISO 8601, without
being asked. The alternatives were rejected on their prices: server-side
logic in Caddy breaks limb (b)'s "no second route" and is invisible to a
local reader; JavaScript breaks limb (b) outright the day after it was
ruled.

**NOT CLOSED BY THIS.** A run that fails to write the page at all is caught
elsewhere — `vss-failure@` on the unit, and the healthchecks.io observer
alarming on a missing ping. Neither is a substitute for reading the
timestamp.

---

### E115 — where a filer states interest PAID and nothing else, the add-back is interest paid ALONE, named as a one-sided proxy

**RULED 2026-09-18 by the owner, during HRB's review, on the question the
`flow` step raised. Recorded as given.**

**THE GAP.** E34 forms the add-back from E18's cash pair, interest paid minus
interest received. **E34.1** covers the filer that states interest paid but no
interest received: the add-back becomes the income statement's net, an accrual
proxy, and that ruling says in terms that **interest paid alone is never the
net** — on Nike FY2026 it would add back 323m against a true net of −50m, an
income. **E61** covers the filer that tags neither the net nor an
interest-received figure: the add-back is the tagged GROSS interest expense
alone, bounded and one-sided.

**HRB FY2026 fits none of the three, and this was searched before it was
ruled.** The owner's instruction was to search the CONCEPT, not the caption,
and to record the search:

- **full text of the 10-K** (0000012659-26-000026, filed 2026-08-14) for
  *interest income*, *investment income*, *interest earned*, *interest
  received* — **one hit, and it is REVENUE**: the recognition policy for
  *"Interest and fee income on Emerald Advance®"*, the consumer loan product,
  inside Financial services revenue (30,653);
- **the other-income line** — *"Other income (expense), net 26,813"*, a single
  aggregate, no breakdown given;
- **cash-flow supplemental disclosures** — *"Interest paid on borrowings
  76,728 / 74,639 / 75,694"*. **No interest-received line**;
- **every interest-income element in the us-gaap taxonomy** —
  `InterestIncomeOther`, `InterestIncomeOperating`,
  `InterestAndDividendIncomeOperating`, `OtherInterestAndDividendIncome`,
  `InvestmentIncomeInterest`: **none carries an FY2026 value.** The only
  interest facts tagged for FY2026 are `InterestPaidNet` 76,728,000 and
  `InterestExpenseDebt` 80,611,000.

So interest income is **NOT PRESENTED** (E85's documented absence, not E25's
zero), E34's pair cannot form, no income-statement net exists for E34.1, and
E61's leg cannot form either because this filer's gross expense is filed under
`InterestExpenseDebt`, an element `finance_costs_period` does not read.

**THE RULE.**

> Where a filer books interest INSIDE operating cash flow, **states interest
> PAID as a cash figure**, and states **no interest received, no
> income-statement net, and no gross expense the schema reads** — the absence
> of the income established by a RECORDED SEARCH of the filing's text and of
> the taxonomy, not by the silence of one tag — **FCF0's add-back is INTEREST
> PAID ALONE.**
>
> It is entered as `interest_source: cash_paid_only` and the leg is the
> stated `finance_costs_paid`. It is **UNSIGNED and always ADDED**, as E61's
> leg is.
>
> **IT IS NOT THE NET, AND THE COLLISION WITH E34.1 IS NAMED RATHER THAN
> HIDDEN.** E34.1's sentence stands: interest paid alone is never the net.
> This ruling does not make it the net; it admits it as a **named one-sided
> proxy** in E61's class, on E61's reasoning — **interest income is never
> negative, so the figure is greater than or equal to the true net and FCF0
> is OVERSTATED by the unstated income, never understated** — and **the bias
> is PRINTED beside FCF0 as a percentage**, exactly as E61's bound is.
>
> **WHY THE ORDER MATTERS.** The search comes first. A tag-map addition on
> one name's account is refused: the owner's instruction was explicit that
> `InterestExpenseDebt` is **not** to be added to the map to clear this name,
> because that would change every filer's gross-expense leg to settle one
> filer's add-back.

**THE BIAS, ON HRB FY2026.** The add-back is 76,728,000. The unstated interest
income can only sit inside *"Other income (expense), net"* = 26,813,000, itself
an aggregate of undisclosed composition — **a ceiling on the VISIBLE CONTAINER
and not a bound on the received amount**, which is why the printed figure is
the add-back as a percentage of FCF0 and not a claimed error bar.

**WHAT THIS DOES NOT DO.** It does not touch E34's pair where a filer states
both halves, does not disturb E34.1's accrual proxy or E61's gross-expense
proxy, and does not widen `finance_costs_period`. A filer that states interest
received still forms E34's net, and a later filing by this filer that states it
moves HRB back onto E34 without amending this entry.

### E116 — the weekly screen's message: a status line EVERY run, and names new to the top 20 as one informational line

**RULED 2026-09-19 by the owner, after the check-in posted two recovered
crashes of the weekly screen as if live. Recorded as given.**

**AMENDS E93's notification, and only that.** E93's change set — ENTERED and
LEFT the top 10, the one-step jump from outside the top 20, the watchlist
entrant, the data event — is unchanged, and is still sent in full.

**THE RULE.**

> 1. **Every weekly run that reaches its end sends one message**, titled
>    `OK` or `INCOMPLETE`. A crash is still E93's third event and is sent by
>    the `OnFailure=` leg; a quiet week is no longer silence.
> 2. After E93's changes, **one line names every name inside the top 20
>    that was outside it last run** — `Also new in top 20: AON #17, FOXA #19`
>    — leaving out any name E93 already carries.
> 3. **E93's suppressions govern the names, not the status line.** An
>    incomplete run, or one not struck the same way as its baseline, names
>    no name at all — it says only why nothing was compared.

**THE WOBBLE RISK, WRITTEN DOWN AND ACCEPTED.** E93 refused pointers on
movement inside the top 20 because a name moves several places on price
alone. Crossing the 20 boundary is exposed to the same wobble: measured
on the stored rankings, AON and HLNE were new in the top 20 on 2026-09-05,
fell out, and came back as "new" on 09-17 and 09-19. The line is therefore
**informational — a reason to look, never an event** — and is kept to ONE
line under E93's changes so it cannot crowd them.

### E117 — rent is an operating cost: the lease payment is deducted from the flow and the operating lease liability leaves net debt

**RULED 2026-09-19 by the owner, on the E34 lease question queued at HRB's
review of 2026-09-17. Recorded as given. Amends E70's flow rule and E35 /
E65 for operating leases. Written before the code.**

**THE QUESTION.** E70 adds lease payments back to FCF0 in perpetuity while
net debt deducts only the lease liability — the present value of the
leases signed today. With M the value multiple on FCF0, the struck value
exceeds the rent-bearing one by (M × annual lease payments − lease
liability) / shares, and **that is positive wherever the liability is
shorter than M years of payments — every lease-holding name measured**
(14–22× against 2.3–9.2 years; AUTO.L's single long lease, 23.7 years, the
one exception). A is exact only for a company that never renews a lease.
An IFRS 16 filer's flow never bore the principal, so the IFRS names carried
the same asymmetry before E70 made the US names match them.

**THE RULE — option B.**

> 1. **Rent is an operating cost.** FCF0 is after the TOTAL LEASE CASH
>    OUTFLOW — principal AND interest — for every name, whatever the filer's
>    classification of interest. A US GAAP filer's operating cash flow
>    already bears its operating lease payments (ASC 842-20-45-5(a)), so
>    E70's add-back is REVERSED and nothing further is deducted. An IFRS 16
>    filer's principal (financing, IFRS 16.50(b)) and its lease interest are
>    DEDUCTED; where the filer's interest rule (E34) has added the lease
>    interest back, the deduction takes it out again. **No IFRS value is
>    printed as an upper bound** for want of the interest leg: without it
>    the flow is DATA MISSING.
> 2. **The operating lease liability leaves net debt.** It is the same
>    obligation as the rent now in the flow, and E70's ground stands: a
>    lease is counted ONCE.
> 3. **Finance leases stay in net debt**, and their principal is NOT
>    deducted from the flow. The split is the US GAAP standard's own
>    (ASC 842). **IFRS 16 has one lessee model and no split, so every IFRS
>    lease liability leaves net debt and all of its cash is deducted**
>    (owner, 2026-09-19).
> 4. **Uniform.** Every name, AUTO.L included. No threshold on the length
>    of the liability.
> 5. **The tests follow the flow.** Leverage and coverage are formed on
>    RENT-BEARING earnings, with net debt excluding operating leases, and a
>    return on capital excludes right-of-use assets from the capital base.
>    Now: §3 Gate 3's interest coverage and net debt/EBITDA, and the 4.2.5
>    kill. **The screener's leverage limb and its EBIT/total-assets leg are
>    a separate pass** (owner, 2026-09-19): they run on vendor data that
>    carries no lease figures for most of the universe.
> 6. **LIAB.ST and RKT.L:** the total lease cash outflow is read from each
>    filer's IFRS 16 lease note. Until it is on file, their struck values
>    are marked UNVERIFIED UNDER E117.

**REFUSED.** **A**, E70 as it stood: the known upward bias. **C**, B below a
threshold of liability length: the bias exists at every length below M, so
a threshold is arbitrary. **D**, new right-of-use assets deducted as capex
with the liability left in net debt: no name carries the data. **D is
recorded as a possible future refinement**; it agrees with B for a lease
estate in steady state and departs from it for one growing or shrinking.

**THE RE-STRIKE.** Every name with a run record is re-struck under this
entry in one pass. New run records and strike reports are written; the
watchlist's `fv_base`, `tier`, `mbp` and `stop_price` remain the owner's
write, by hand, after the printout (the E70 precedent).

**GDDY** (owner, 2026-09-19): its close sat just below the MBP before this
ruling and just above the MBP B implies. It is read as **AT THE LINE**, not
as a changed signal.

**WHAT MOVED — the re-strike of 2026-09-19** (`tools/restrike_e117_2026_09_19.py`;
records `reference/run-records/<TICKER>-2026-09-19-e117.json`, one commit per
name). Each name struck again off its store on the PRIOR record's growth view,
rate, conventions and hand inputs, unchanged (E28): the lease treatment is the
only thing that moved. **Nothing was written to the watchlist.** MBP is fv_base ×
E90's tier cushion, shown only where the watchlist carries a tier.

| Ticker | Status | fv_base before | E117 | Move | MBP before → E117 | Outcome |
|---|---|---:|---:|---:|---|---|
| ULTA | INTAKE | 476.45 | 369.79 | −22.4% | | struck |
| MEKKO.HE | WATCH-GATED | 14.03 | 10.54 | −24.8% | | struck; gate refuses on figures UNVERIFIED before E117 |
| BOUV.OL | — | 31.24 | 21.21 | −32.1% | | struck; gate refuses on figures UNVERIFIED before E117 |
| HRB | WATCH-GATED | 104.94 | 82.24 | −21.6% | | struck — the value the 09-17 review's memo reached by hand |
| CROX | DROPPED | 169.79 | 151.64 | −10.7% | | struck |
| LII | INTAKE | 319.37 | 285.07 | −10.7% | | struck |
| MUSA | INTAKE | 232.42 | 217.03 | −6.6% | | struck |
| ACN | INTAKE | 255.10 | 239.81 | −6.0% | | struck |
| DECK | WATCH-GATED | 127.49 | 120.03 | −5.9% | | struck |
| CTSH | WATCH-PRICED | 89.38 | 84.14 | −5.9% | 67.04 → 63.10 | struck; its 22m of finance leases stay in net debt |
| LOPE | INTAKE | 131.43 | 125.98 | −4.1% | | struck |
| GDDY | WATCH-PRICED | 132.18 | 129.03 | −2.4% | 99.13 → 96.77 | struck; **AT THE LINE** (owner, above) |
| NVR | PIPELINE | 4,978.10 | 4,867.82 | −2.2% | | struck; its 42.5m of finance leases stay |
| RMV.L | PIPELINE | 4.27 | 4.22 | −1.3% | | struck |
| AUTO.L | PIPELINE | 4.82 | 4.84 | +0.3% | | struck — the one liability longer than M years (23.7) |
| AOS | INTAKE | refused (E70 lease leg, E106 tolerance) | 63.00 | | | struck: E117 reads no US lease flow, so the bound on E70's leg bounds nothing |
| LIAB.ST | HELD | 133.48 | — | | | **UNVERIFIED UNDER E117**: lease interest stated for FY2025 only (note 30: 66), not on the TTM basis |
| SAP.DE | WATCH-PRICED | 140.37 | — | | | **UNVERIFIED UNDER E117**: lease interest never isolated, annual or quarterly |
| RKT.L | INTAKE | 32.20 | — | | | **UNVERIFIED UNDER E117**: no separate principal line, no IFRS 16.53(g) total |
| PNDORA.CO | WATCH-GATED | refused (no net-debt declaration) | refused | | | its lease tables are complete; the record refuses as before, now also on the lease leg |

**APPLIED ON THE DATA, 2026-09-19** (each on the figure's own page):

- **RMV.L** and **BOUV.OL** state lease interest PAID; entered as stated.
- **MEKKO.HE** states only the income-statement EXPENSE on lease liabilities
  (1.0); it is entered as an ACCRUAL STAND-IN for the cash figure and named so.
- **AUTO.L** states a total cash outflow for leases (IFRS 16.53(g)) of 1.8,
  the same figure as its single financing line "Payment of lease
  liabilities"; the interest is inside that line, so `lease_interest_paid` is
  a NAMED ZERO and the deduction is the stated total, once.
- The twelve US names carry `operating_lease_liabilities` off SEC companyfacts
  (`us-gaap:OperatingLeaseLiability`, tagged); the XBRL path now emits it.

**WHAT E117 DOES TO E101's NET-DEBT CHECK.** Issuers publish net debt
*including* leases (Lindab 4,497, Pandora 15,643). Ours now excludes the
operating part by rule, so the comparison carries a structural gap of about
the lease liability; the gap is expected and is not a finding.

**CLAUSE 5 IS NOT YET APPLIED.** No store carries EBITDA or right-of-use
depreciation, so neither a rent-bearing leverage nor a rent-bearing coverage
can be formed for any name, and the 4.2.5 kill still reads the issuer's own
stated ratio. What to collect and how the kill reads meanwhile is open.

**THE OWNER'S ANSWERS, 2026-09-19, after the re-strike.**

- **Clause 5 is a SEPARATE PASS.** EBITDA, D&A and (IFRS 16) right-of-use
  depreciation are collected and the rent-bearing leverage and coverage built
  in their own pass. **Until then the 4.2.5 kill reads the issuer's STATED
  ratio as before**, printed as issuer-stated and lease-inclusive under IFRS
  16 — a held name's leverage kill is never left blind for want of the new
  figure.
- **The data applications stand:** MEKKO.HE's interest expense as a named
  stand-in for cash paid; AUTO.L's stated total lease cash (1.8) deducted
  once, the interest inside it.

### E118 — Gate 3 interest coverage where the filer earns net finance INCOME: PASS, with gross interest cover still required

**RULED 2026-09-19 by the owner, during CTSH's review. Recorded as given.
Amends E112 (a negative net was NOT MEANINGFUL) and, for coverage, E25's
"EBIT / 0 is undefined".**

> **Where net finance costs are zero or negative, Gate 3 interest coverage
> records PASS** — there is no interest burden to cover. **Where gross
> interest expense is on file, PASS also requires operating income / gross
> interest expense ≥ 5x**, and **both figures are recorded**: the net, and
> the gross cover.

Applies today to **CTSH** (net −68m: expense 37m, income 105m) and **RMV.L**.
E112's numerator stands: operating income as stated.

### E119 — where a filer states no EBITDA and no leverage ratio, EBITDA is DERIVED, and Gate 3 leverage and 4.2.5 run on it

**RULED 2026-09-19 by the owner, during CTSH's review. Recorded as given.
Amends E82 and the `depreciation_amortisation` field note ("nothing here
derives one from the other") for this purpose only. Stated figures take
precedence.**

> Where a filer states **no EBITDA and no leverage ratio**, EBITDA is
> **derived as operating income plus D&A from tagged facts, marked
> DERIVED**, and **Gate 3 leverage and the 4.2.5 kill run on it**.
>
> (a) **The ruled ratio uses ONE WINDOW**: EBITDA and net debt from the
> same period — TTM where quarterly records exist, otherwise annual (E19).
>
> (b) **An information line** shows the LATEST QUARTER's net debt over that
> EBITDA; **if it exceeds the threshold, the gate records REVIEW**.
>
> (c) **For IFRS 16 names, derived EBITDA SUBTRACTS the total lease cash
> outflow** (E117: rent is an operating cost).
>
> (d) **Net debt includes finance leases and the pension deficit** — E117's
> net debt, as section 5 forms it.

Thresholds: Gate 3 leverage 2.5x (FRAMEWORK §3); 4.2.5 3.5x (FRAMEWORK
§4.2.5). A stated EBITDA (`ebitda`) or a stated quarterly `net_debt_ebitda`
wins wherever it exists.

### E120 — where quarterly lease interest is not stated, the latest annual note figure stands in, marked STAND-IN

**RULED 2026-09-19 by the owner, on the draft laid out after LIAB.ST's A2.
Recorded as given. Amends E19 (one window) for this leg alone, and E106's
bound where an annual figure exists.**

> Where a filer states its lease interest ANNUALLY but not by quarter, **the
> latest annual note figure stands in** for the lease interest on a
> trailing-twelve-month basis, **marked STAND-IN**, and the E106 bound it
> replaces is dropped. The figure's own date is printed beside it, so the
> window mismatch is never hidden.

**APPLIED 2026-09-19, LIAB.ST.** Note 30 of the 2025 annual report: *"of
which SEK 66 m (58) relates to interest expenses recognised in cash flow from
operating activities"* stands in for the 2025-Q3 → 2026-Q2 window; the E117
strike on the record is **68.97** (FV_bull 86.42). **This does not reopen the
exit decided 2026-09-19** (owner): the close 119.70 is above FV_bull either way.

**WHAT IT DOES NOT REACH.** SAP.DE states lease interest in no period, not
even annually: it stays E106-bounded. RKT.L states no lease principal: it
stays UNVERIFIED UNDER E117.

---

### E121 — a name's exchange calendar may be DERIVED FROM THE VENDOR'S TICKER SUFFIX; the staleness count is the only thing it may govern

**RULED by the owner, 2026-09-20.** The exchange calendar for a name may be
derived from the vendor's ticker suffix. **The suffix is a listing code
assigned by the vendor, not an inference drawn by us**, so deriving a
calendar from it is a READ, not a guess, and `vss/calendars.py`'s warning
about a calendar "guessed from a ticker suffix" does not apply to it.

**THE CONDITIONS, ALL BINDING:**

- **(a) The mapping table is DATA.** Adding or correcting an entry in
  `config/exchange_calendars.yaml` is not a ruling and takes no entry here.
- **(b) An unmapped suffix falls back to the Monday-to-Friday count, and the
  block text must SAY SO BY NAME** ("no exchange calendar for this name:
  counted Monday to Friday").
- **(c) A ticker with NO suffix is a US listing on the NYSE calendar.** This
  is the one weak leg: it rests on the vendor's convention that only non-US
  listings carry a suffix. **Intake must therefore refuse a name whose
  unsuffixed ticker is not US-listed, and say which check failed.**
- **(d) The derived calendar governs SESSION COUNTING ONLY.** It may not
  enter a valuation, a strike period, a catalyst date or a level test.
- **(e) THE ERROR DIRECTION IS FIXED:** where the mapping is wrong or
  missing, the count must OVER-state staleness, never under-state it.

**WHY IT WAS NEEDED.** The staleness gate blocks a name whose newest close is
too old, and on 2026-09-19 that gate tightened to ONE session for a name
carrying a level. Counted Monday to Friday, a name is then blocked on the
first night after any two closed weekdays in a row -- Good Friday into Easter
Monday, Christmas into Boxing Day -- on which no close was missed because
there was no session. A block that fires on a quiet market is noise, and
**noise beside a push is how a push gets muted.**

**WHAT IS IN PLACE, 2026-09-20.** (a) `config/exchange_calendars.yaml` grew a
`suffixes:` map. (b) and (d) hold as committed: the derived days reach
`rules.stale_close_blocker` and the push's age line, and nothing else. (c) is
enforced in `config.load_watchlist`: an unsuffixed ticker not quoted in USD
is refused, naming E121(c). (e) holds for a MISSING mapping, which can only
subtract holidays it does not know and so over-states the age; **it is NOT
guaranteed for a WRONG mapping**, which would subtract closed days the
exchange never had and under-state it by that many sessions. The mapping is
pinned by test and the table is small, seventeen markets.

---

### E122 — a price we have held is NOT RETRACTABLE by the vendor's silence

**RULED by the owner, 2026-09-20**, on the finding that the nightly's own
cache write destroyed closes it had already seen, stored and printed.

**WHAT HAPPENED.** `fetch.write_cache` did `frame.to_csv(path)` — a blind
whole-file overwrite with whatever the vendor last returned. On 2026-09-19
yfinance returned **no 2026-09-17 row and a NaN close on 2026-09-18** for
every continental-European name, and the overwrite took the good rows with
it. The 2026-09-18 nightly had **already seen and used** those closes:
LIAB.ST at 119.70 and SAP.DE at 183.12 are in that night's database rows and
in its report. **The scan of 2026-09-20 found 22 (ticker, date) pairs lost
across twelve names, all on 09-17 and 09-18, none older**; the exposure
window opens at `write_cache`'s first commit, 2026-08-20 (bf8162b), and the
database's own coverage begins 2026-08-22.

**THE RULES, ALL BINDING:**

- **(a) The cache is a UNION BY DATE.** A date once held is never removed by
  a later response that omits it.
- **(b) A blank, NaN or absent close NEVER overwrites a held close.** Ever,
  under any path.
- **(c) A DIFFERING NON-BLANK close for a held date is a CORRECTION, not
  silence, and it DOES apply.** It replaces the held value, and both values,
  both dates and the source go to the log and into the next report.
- **(d) EXCEPTION TO (c):** a correction that moves a close **across a level
  the name carries** (MBP, stop, FV_bull, fv_base) in either direction **does
  not apply silently. It blocks the name and asks.** A revision that quietly
  un-crosses an MBP is the one thing this whole mechanism exists to stop.
- **(e)** A row retained after the vendor dropped or blanked it is **marked
  retained, with the date first seen, wherever the close appears** — report,
  push, overview, packet.
- **(f) Staleness is measured against the newest close HELD**, not the newest
  in the last response.
- **(g)** `frame.to_csv(path)` **goes.** Removed, not wrapped, not guarded.
  No write path may replace a file of dated rows wholesale.

**WHAT IS IN PLACE, 2026-09-20.** `fetch.merge_series` is the union and is
the only thing that builds a cached series; `fetch.write_cache` writes what
it returns and is the only `to_csv` on a cache path, pinned by test. The
levels a name carries are computed WITHOUT the price series
(`runner.entry_levels`) and handed to the fetch, so (d) is decided inside the
merge; a refused correction waits in `data/price_corrections.json` and blocks
the name every night until the owner rules. Retention marks live in a sidecar
beside the series. **The 22 lost rows were put back from the database**
(`tools/seed_cache_from_db.py`), each marked retained with the run date it
was first recorded on; LIAB.ST 2026-09-17 (123.80) was recoverable, as were
SAP.DE's 09-17 (188.00) and 09-18 (183.12).

**WHAT THE SCAN CANNOT SEE, AND IT IS SAID HERE RATHER THAN LEFT OUT.** The
database holds ONE close per ticker per night — the newest of that run. A row
dropped from the MIDDLE of a series, which was never the newest close on any
run, leaves no trace to compare against and is invisible to this scan. The
union stops such a loss from here on; it cannot prove none happened before.

---

### E121(e), AMENDED — compliance BY DETECTION: a close printed on a day the calendar calls closed

**RULED by the owner, 2026-09-20**, amending E121(e). The original clause
required that a wrong or missing suffix mapping **over-state** staleness and
never under-state it. A MISSING mapping does exactly that. A WRONG one does
not, and no guarantee was available — but a check is: **the price series
already in hand settles it.** If a row comes back for a day the derived
calendar calls closed, the mapping is wrong.

**So (e) reads: compliance is by DETECTION, not by guarantee.** A price row
on a day the calendar calls closed raises a blocker naming the suffix and the
date. Over-stated staleness from a missing mapping stays acceptable;
under-stated staleness from a wrong mapping becomes **loud within one trading
day of the name being live**. The network check at intake stays deferred;
this removes the reason to hurry it.

Wired the same day: `runner.build_row` compares the sixty days before the run
against the derived calendar's closed days and raises `CALENDAR_MISMATCH`,
which names the suffix, the market and the first dates that clash. Correcting
the suffix is data, not a ruling (E121 a), and clears it.

---

### B49 — OPEN: §5.3's E27 note says a WATCH-GATED name has no row in the alert matrix; `mbp_verdict` gives it one

**RAISED 2026-09-20, LEFT OPEN by the owner the same day. No code change, no
test change, and no date — a TRIGGER CONDITION instead.**

**THE DISAGREEMENT.** FRAMEWORK §5.3's E27 note reads: *"A WATCH-GATED name
has no row in this matrix: every row here opens on a price, and a gated
name's route back is a named information event, not a price that sends it to
§6."* `rules.mbp_verdict` has never consulted the status. A gated name that
carries a tier therefore still prints **AT/BELOW MBP** or **APPROACHING MBP**,
and both are actionable verdicts.

**WHY IT IS NOT BEING CLOSED NOW.** Wiring the suppression was tried on
2026-09-20 and reverted. It failed 33 pinned tests, including the verdict
matrix, which encodes the present behaviour for every gated name — so closing
it is a framework-wide change to what fires, and it was being made inside one
name's move (SAP.DE to WATCH-GATED). **The owner's reason for holding it:
no gated name is anywhere near its MBP** — SAP.DE, the only gated name with
one, closes 53.5% above it — **so the suppression changes no printed line
today. A behaviour change with no live exposure does not belong inside a
single name's decision.**

**THE TRIGGER.** Revisit when **any WATCH-GATED name's close comes within 15%
of its MBP**. Until then the disagreement stands recorded, and a gated name's
buy line is held non-actionable by status convention and by what its entry
says, not by the engine.

---

### E123 — where the OPERATING ASSET IS INVENTORY and its purchase runs through operating cash flow, Gate 3's FCF limb and its leverage limb are DATA MISSING, and §4.4 rebases

**RULED by the owner, 2026-09-20**, on the homebuilder gap that blocked PHM
and NVR together. **Option C of the four put to him, drawn narrowly.**

> **THE RULE.** Where **the operating asset is INVENTORY and its purchase
> runs through OPERATING CASH FLOW**, Gate 3's **FCF-positivity limb** and
> its **leverage limb** are **DATA MISSING** — not FAIL, and out of the
> count — and **§4.4 rebases**, exactly as E99 does for Gate 4.
>
> **THE TRIGGER IS THAT FACTUAL TEST, NOT A JUDGMENT ABOUT A NAME.** It is
> answered from the accounts: is the operating asset inventory, and does its
> purchase run through operating cash flow? Nothing about the industry's
> prospects, the cycle or the quality of the business enters it.

**WHY THE TWO LIMBS INVERT.** The FCF limb asks whether reported profit
turns into cash repeatedly without outside funding; the leverage limb asks
whether the fixed claim is small against recurring cash-generating capacity.
For a filer of this shape, **buying the operating asset IS an operating
outflow**, so:

- **growth drives FCF negative and contraction drives it positive.** The
  sign tracks the direction of the inventory book, not the quality of the
  business. PHM's own five years show it: the strongest year, 2,104.6 USD m
  in FY2023, follows the 2022 rate shock, and the weakest, 555.8 USD m in
  FY2022, is the boom year. **Read literally the limb rewards contraction.**
- **EBITDA is the wrong denominator**: it excludes the inventory spend that
  is the real capital cycle, so net debt / EBITDA flatters the filer exactly
  while the book is run down and looks worst while it is restocked.

**WHAT IS PRINTED INSTEAD.** When those limbs read DATA MISSING, the report
prints **DEBT TO TOTAL CAPITALISATION as a figure with NO THRESHOLD attached
— measured, never deciding, in E7's shape** (and E63's, which reports a
distance and applies nothing). No band is invented for it, because §3 has
been here: **E30 deleted two limbs rather than tune invented thresholds**,
and a new industry-specific number would repeat what that ruling refused.

**THE COST, RECORDED BECAUSE IT IS REAL.** **The conviction bands were
calibrated on FOUR gates** (E99, after Gate 4 left the denominator), and
this **shortens the denominator again for an industry**. A name of this
shape scoring 5 on a shorter count is **not the same evidence** as a name
scoring 5 with Gate 3 fully evaluable, and §4.4's bands do not say so.

**DATED FROM NOW — E77 and E100 treatment.** It applies to readings struck
from today; it does **NOT** move a standing gate reading. **NVR's standing
WATCH-GATED reading is not moved by this**, and **NVR also needs B-15** (a
filer that states no operating income) before anything about it changes:
**NVR stays parked.** PHM has no §3 reading on file, so a first reading of
it is made under this ruling.

**WHAT IS NOT RULED HERE.** Whether housing's cycle is forecastable at §5's
ten-year horizon — the argument that would have made E96's exclusion the
right answer instead — is **not decided**, and the owner refused the
exclusion route on the ground that the defect is in two proxies rather than
in the method.

---

#### E123, AMENDED 2026-09-20 by the owner — the measured figure is TWO figures, and neither decides anything

The ruling above printed one figure. **It prints two**, a middle position
rather than a choice between the operating borrowings and the captive
finance arm's debt:

```
debt to total capitalisation, homebuilding only   11.16%
same, including captive finance debt              14.28%
```

and **below them the net position on each basis** — for PulteGroup at
2025-12-31, **net cash 349,771** on the first and **net debt 182,567** on
the second. **No threshold is attached to any of the four**, and none of
them can pass or fail.

**THE SPREAD BETWEEN THE TWO RATIOS IS ITSELF THE INFORMATION: small means
the captive-finance question does not matter for that filer, large means it
does.** Neither line is the answer; the distance between them says whether
there is a question at all.

**WHERE THE CAPTIVE FINANCE DEBT CANNOT BE READ FROM ANY DOCUMENT, THE
SECOND LINE READS DATA MISSING WITH THE REASON — NEVER OMITTED**, because an
omitted line and a zero look identical in a packet.

**AND THE REASON IS RECORDED ON THE FIELD ITSELF:** PulteGroup's 'Financial
Services debt 532,338' is **absent from the SEC companyfacts API under every
namespace** (searched 2026-09-20 by exact value across `us-gaap`, `dei` and
`srt`), so **a tag-built store cannot reach it**: the figure comes from the
filing or the line is DATA MISSING.

---

### E124 — `NotesPayable` enters the tag map for an UNCLASSIFIED balance sheet; `LongTermDebt` is excluded by name; a captive finance arm's debt is unreachable by tag

**RULED by the owner, 2026-09-20**, after the FY2025 10-K was read rather
than inferred (`sources/PHM_FY2025_annual-report-10k_2026-02-04_en_a0.htm`,
accession 0000822416-26-000007, in the manifest as a primary source).

- **(1) `NotesPayable` is read into `financial_liabilities_noncurrent`, WHOLE.**
  A filer with an unclassified balance sheet states one debt caption and no
  current / non-current split. PulteGroup's 'Notes payable 1,631,098' is a
  **stated subtotal** that note 5 reconciles exactly — total senior notes
  1,583,913 (five issues, net premiums, discounts and issuance costs −5,231)
  plus other notes payable 47,185 — so **E26's two-captions-and-no-total
  problem does not arise and E71's summing is not needed.** The current leg
  **stays absent**: inventing a split would be fabrication, and **nothing in
  §5 or Gate 3 reads the split** — net debt adds the two legs. The absence is
  deliberate and is stated on the figure's own page line.
- **(2) `us-gaap:LongTermDebt` is EXCLUDED BY NAME for this shape.**
  PulteGroup tags **43,900,000** under it and the filing says what it is:
  *"aggregate outstanding debt of unconsolidated joint ventures"* — **off
  balance sheet, generally non-recourse, not the filer's borrowing.** A
  generic reach for that element would import someone else's liability.
- **(3) A CAPTIVE FINANCE SUBSIDIARY's debt is UNREACHABLE BY TAG, and that
  is recorded rather than worked around.** 'Financial Services debt 532,338'
  — Pulte Mortgage's master repurchase facility, secured by the loans it
  funds — sits on the face of the balance sheet beside Notes payable and is
  **absent from companyfacts under every namespace**. It is carried in the
  new store field `captive_finance_debt`, **read from the filing**, and where
  no document supplies it E123's second line reads DATA MISSING.
- **(4) E14's "borrowings alone" is NOT widened.** The captive arm's debt is
  not added to net debt, does not enter §5, and decides nothing. It appears
  only in E123's second measured figure, beside the first.

**THE CORROBORATION, RECORDED BECAUSE IT IS UNUSUAL.** PulteGroup states the
ratio itself: *"Our ratio of debt-to-total capitalization, excluding our
Financial Services debt, was 11.2% at December 31, 2025."* The figure this
store computes from the same balance sheet is **11.16%**. The framework and
the filer agree to a rounding, and **the issuer's own convention is the one
E123's first line uses.**

---

### E125 — PER-ISSUER CAPTION MAPS FOR PDF AND HTML REPORTS ARE DECIDED AGAINST, and the reason is the failure they would produce

**DECIDED by the owner, 2026-09-20**, on the design report of the same day.
Recorded here so it is **not re-proposed**.

**WHAT WAS PROPOSED AND REFUSED.** Extending the xlsx path's principle — a
committed per-issuer map naming the ROW LABEL, never the index
(`config/manual/maps/<TICKER>.yaml`, Pandora's) — to PDF and HTML reports,
so a quarter's figures could be matched on captions and table headings
written once and reused every quarter.

**THE FIRST REASON: THE WRONG KIND OF FAILURE.** A Nordic interim prints
the quarter column and the year-to-date column **under the same captions**.
A map that takes the wrong one produces a figure that is **right in units,
plausible on its page citation, and three or four times too large**. The
xlsx path is protected from this by cells, by column headers that are text,
and by a cross-sheet reconciliation that proves the columns were matched to
the same quarter; **a PDF gives none of those**, and the failure it would
produce is silent, specific and expensive. This project has spent its
rulings making failures loud (E30 deleted invented thresholds rather than
tuning them; E122 refuses a blank close; E121(e) detects a wrong calendar
within a trading day). A mechanism whose characteristic failure is a
plausible wrong number is the opposite of that.

**THE SECOND REASON: IT MOVES THE EVENING RATHER THAN SAVING IT.** **E21
stands**: a figure the basis reads that is UNVERIFIED refuses section 5, and
a caption-matched figure is not a tagged fact — it would enter UNVERIFIED
and **wait for the owner's read-back exactly as a hand-typed figure does**.
The map would replace typing with reviewing, which is the same evening in a
different chair, plus a map to maintain per issuer.

**WHAT IS NOT DECIDED HERE.** Nothing about the xlsx path, which stands and
works (PNDORA.CO). Nothing about SEC tagged facts, which are VERIFIED by
provenance under E40 and are a different mechanism entirely. And nothing
about a future in which a caption-matched figure could be *verified* without
the owner's eye — **that would be a ruling about E21 and E40, and it is the
ruling that decides whether such a map is ever worth building.** Until
someone asks for that ruling, this is closed.

---

### E126 — B-15 RULED: where a filer states no subtotal before financing cost, Gate 3's coverage limb reads a STAIRCASE; and below four evaluable gates a name carries NO TIER

**RULED by the owner, 2026-09-20**, on the design report of the same day.
**B-15 is closed for the NUMERATOR. It was three faults, and this rules
one of them** — see the last section.

> **THE STAIRCASE, IN ORDER. A step is taken only where the step above it
> cannot be.**
>
> **STEP 1 — THE STATED SUBTOTAL.** Where the income statement states a
> subtotal before financing cost, that line is the numerator. Unchanged,
> and it is what every ordinary filer takes.
>
> **STEP 2 — PRE-TAX INCOME PLUS THE STATED INTEREST EXPENSE.** Where no
> such subtotal is stated but the filing states an interest expense line,
> the numerator is **INCOME BEFORE INCOME TAXES plus THAT STATED INTEREST
> EXPENSE**, and both lines are named on the figure.
>
> **THIS IS PERMITTED BECAUSE BOTH TERMS ARE PRINTED LINES IN THE SAME
> COLUMN AND THE ADDITION RESTORES ONE STATED DEDUCTION. NO NEW QUANTITY
> IS CREATED.**
>
> **THE TWO LINES ARE NAMED, AND EVERY OTHER RECONSTRUCTION IS FORBIDDEN:
> not EBITDA, not gross profit less selling and administrative expenses,
> not revenue less cost of sales, not a segment subtotal summed across
> segments, not pre-tax income plus a note's interest INCURRED, and not
> pre-tax income plus any interest figure that is not the income
> statement's own charge for the period. ONLY the pre-tax line and the
> stated interest expense line.**
>
> **E5 STANDS UNTOUCHED: EBITDA IS STILL NOT A SUBSTITUTE** for operating
> income, here or anywhere. Step 2 is not a different profit measure with
> different content — it excludes nothing an operating line would include;
> it undoes one deduction the statement itself prints.
>
> **STEP 3 — DATA MISSING, AND THE DENOMINATOR REBASES.** Where no
> subtotal is stated AND no interest expense line exists to add back —
> a filer that CAPITALISES its interest, so the charge reaches the income
> statement inside cost of sales — the limb is **DATA MISSING, out of the
> gate count, and §4.4 rebases**, as E99 does for Gate 4 and E123 for the
> two cash limbs.

**THE CONDITION, AND IT IS THE PRICE OF THE THIRD REMOVAL (owner,
2026-09-20).** **A TIER REQUIRES AT LEAST FOUR EVALUABLE GATES.** Where the
denominator falls below four, a name **may carry a §4.4 score but NO TIER,
and therefore NO MBP.**

**THIS IS A HOLD, NOT A THRESHOLD.** §4.4's bands — `≥6` / `4–5` / `≤3` —
were calibrated on FOUR gates (E99, after Gate 4 left the denominator) and
**have not been restated per denominator**. A score of 5 out of three
evaluable gates is not the same evidence as a 5 out of four, and nothing in
§4.4 says so. **The hold lifts when the bands are restated, and that is
B50, opened by this ruling.**

**WHAT THE TWO FILINGS SHOW, because the fault is not the same for both.**

- **NVR is a CAPTION problem, and step 2 answers it.** Its FY2025 statement
  is segmented and states every term: Homebuilding revenues 10,094,269,
  cost of sales (7,953,401), SG&A (599,667), **interest expense (27,578)**
  → Homebuilding income 1,609,883; Mortgage banking states its own
  **interest expense (1,257)** → income before taxes 1,761,932. **The
  subtotal above financing cost is the only thing missing**, and step 2
  restores it from two printed lines.
- **PHM is an ACCOUNTING POLICY, and only step 3 fits.** It capitalises
  ALL homebuilding interest into inventory — *"we capitalized all
  Homebuilding interest costs into inventory because the level of our
  active inventory exceeded our debt levels"* — so the charge arrives as
  **cost of revenues when houses close**: interest capitalised 104,479,
  interest expensed through cost of revenues 122,112, interest in
  inventory at year end 122,327, cash interest paid net of amounts
  capitalised 17,248. **There is no interest line to add back**, and
  adding the note's figure would double-count against a cost of sales that
  already carries it. For such a filer the separation the limb assumes —
  trading above, financing below — **is not a quantity the accounts
  contain.**
- **HRB states no operating subtotal either**, and has not since fiscal
  2014; its `OperatingIncomeLoss` tag is a fossil of that year. It falls to
  **step 2**, not step 3, wherever its interest lines are stated.

**WHAT PRINTS AT STEP 3 — MEASURED, NEVER DECIDING (E7's shape, and
E63's).** No threshold is attached to any of it and none of it can pass or
fail: **interest incurred; interest expensed through cost of revenues;
cash interest paid net of amounts capitalised; interest carried in
inventory at the period end** — and, beside them, **THE MATURITY WALL**:
the next scheduled repayment against cash and undrawn facilities. For
PulteGroup at 2025-12-31 that is **251.9 m due March 2026 against 1,980.9 m
of cash and 892.9 m undrawn** on a revolver maturing June 2027. **A
builder's debt is serviced by selling inventory, not out of a quarter's
trading margin**, which is why the filer's own MD&A quotes debt to total
capitalisation and a maturity profile rather than a coverage multiple.

**DATED FROM NOW — E77 and E100's treatment.** It reaches **no recorded
gate reading**. **NVR has none to preserve**: it is WATCH-GATED *because
Gate 3 could not form*, so there is no scorecard to overturn — **its next
reading is a FIRST SCORE, not a re-score.**

**WHAT B-15 STILL HOLDS, AND IS NOT RULED HERE.** B-15 is three faults and
this is the numerator's. The other two are **denominator** questions and
stand open: **AOS**, which prints interest expense and folds interest
income inside "Other income, net"; and **LOPE**, which carries no debt and
prints only "Investment interest and other". Neither is touched by this
ruling.

---

### B50 — OPEN: §4.4's conviction bands are calibrated on four gates and have not been restated per denominator

**OPENED 2026-09-20 by E126, which holds a tier below four evaluable
gates rather than guess at the answer.**

Three rulings now remove a gate or a limb from the count where it cannot be
evaluated — **E99** (Gate 4, never assembled for any name), **E123** (Gate
3's FCF and leverage limbs where the operating asset is inventory) and
**E126** (Gate 3's coverage limb where no subtotal before financing cost is
stated). Each is defensible alone. **Together they mean a name can be
scored against three gates, and §4.4's bands — `≥6` high, `4–5` medium,
`≤3` drop — do not say what a score means when the denominator moves.**

The question: **what are the bands, per denominator?** A 5 out of four
evaluable gates and a 5 out of three are not the same evidence, and the
scale as written cannot tell them apart.

**Until it is answered, E126's hold stands: below four evaluable gates a
name carries a score and no tier.** Nothing is proposed here; this is the
record that the question is open and why.

---

### E127 — B41 DECIDED: filter 1 rejects a name whose price is NOT BELOW its close of a year ago; the 52-week low stays a field

**RULED 2026-09-28 by the owner, after HUNT.OL and CF.**

**THE CASE.** The weekly screen of 2026-09-26 put two names into the top
10 that had not fallen in any sense the owner means by the word:

| Name | Rank | Below 52w high | High set | Above 52w low | 12-month return |
|---|---:|---:|---|---:|---:|
| HUNT.OL | 1 | 15.5% | 2026-09-21, five days earlier | 1406.9% | +1150% |
| CF | 4 | 17.7% | 2026-09-02 | 50.7% | +24.5% |

Gate 1's band measures the distance from a PEAK. A name that runs up and
gives back 15% reads exactly like a name that has fallen for a year, and
the band cannot tell them apart. E63 recorded the same blindness from the
other side and left the remedy to B41.

**THE THREE MEASURES WEIGHED, on the 2026-09-26 top 25.**
1. *A cap on the distance above the 52-week low* (B41 as raised). Any cap
   low enough to remove CF (50.7%) also removes HRB (48.9%), CTSH (48.0%)
   and ACN (41.5%), which are down 15.5%, 14.4% and 26.3% on the year:
   fallen names that have partly recovered. Declined.
2. *A minimum age for the 52-week high* (60 days tried). It catches HUNT.OL
   and CF, removes HRB (high 45 days old, down 15.5% on the year), and
   misses AAF.L (+29.9%) and HAS (+16.5%). Declined.
3. **The 12-month return.** It asks the owner's question directly: is the
   price below where it was a year ago? **Ruled.**

**THE RULE.** `return_12m` = (close − close a year ago) / close a year
ago, where the close a year ago is the LATEST settled close on or before
`as_of − 365` calendar days (`metrics.LOOKBACK_DAYS`), under the SAME
coverage bar as the 52-week high and low (`metrics.covers_52_weeks`).
Below the bar it is DATA MISSING, never a return struck off a shorter
window. **Filter 1 keeps a name only if `return_12m < 0`.** Zero is not
a fall. The step is `trailing_year` and runs after the band, with its own
tally: at or above zero is a rejection ON VALUE; no close a year back is
ON MISSING. The predicate is `rules.fell_over_year`. The close a year
ago, its date and the return travel on every candidate row
(`filter1-candidates.csv`) and the return on every ranked row
(`ranking.csv`).

**A REJECTION, NOT A FLAG.** The owner chose to reject at filter 1 rather
than rank and mark. A name up on the year never reaches the ranking.

**SCREENER ONLY.** `vss run` does not read it, and Gate 1 on the
watchlist is unchanged. A PIPELINE or HELD name that rallies is not
removed by this ruling.

**WHAT IT DOES NOT TOUCH.** E63's `pct_above_52w_low` stays a field,
read by nothing. B41 is decided *against* a threshold on it. The band
(E2, B2) and the listing-age floor (E52) are unchanged.

**FIRST MEASUREMENT.** The 2026-09-26 run replayed on its own snapshot
and its own exchange rates, with the step in place: the band passed 822
names, and `trailing_year` rejected **257 on value** (31%) and none on
missing data, leaving 565. The ranking went from 474 candidates to 318,
and from 339 ranked on both components to 208. Gone from the top 25:
HUNT.OL, CF, RVRC.ST (+1.7%), FOXA (+3.1%), TPR (+4.4%), AAF.L (+29.9%),
HAS (+16.5%). The new #1 is HRB.

### E128 — short-term government securities held to maturity count as cash; nothing wider does

**RULED 2026-10-05 by the owner, on CPRT.**

**THE RULE.** **Government** securities that the issuer classifies as
**held to maturity** and that **mature within 12 months** of the balance
sheet date are entered in `other_current_financial_assets`, and section 5
subtracts them from net debt beside cash (E35's asset side, which the code
already subtracts wherever the field is present). The figure entered is
the balance-sheet carrying value at the caption printed (E69), not the
fair value beside it.

**WORDED NARROWLY ON PURPOSE.** In the owner's words: *"Corporate bonds,
longer-dated paper and equity stakes don't. The argument against: it adds
about 10% to fair value on a judgment call, so the narrow wording is what
keeps it honest."* So: **NOT** corporate bonds or commercial paper,
**NOT** government paper maturing after 12 months, **NOT** available-for-
sale or trading portfolios, **NOT** equity stakes or funds. Each of those
stays out of net debt until a ruling of its own. All three conditions --
government issuer, held to maturity, within 12 months -- must be stated by
the filer; one that is not stated is not assumed.

**WHAT IT DOES NOT OPEN.** Assumption A1 (short-term investments in
general) stays undecided outside this one class. E35's asymmetry is
unchanged: the asset is never REQUIRED, so its absence still only makes a
value conservative.

**APPLIED 2026-10-05, CPRT.** 10-K `0001193125-26-405731`, Consolidated
Balance Sheets at 2026-07-31: `Investment in held to maturity securities
2,581,901` (thousands). Note 10: *"The Company has investments in U.S.
Treasury Bills ... carried at amortized cost and classified as held to
maturity as the Company has the intent and the ability to hold them until
they mature"*; Note 1: *"The held to maturity securities mature within the
next 12 months."* All three conditions stated. Entered 2,581,901,000 USD
(fair value 2,596,886 named, not used).

### E129 — a cash caption that includes an unstated restricted part is entered whole, and named

**RULED 2026-10-05 by the owner, on CPRT.**

**THE RULE.** Where the balance sheet prints one caption for *cash, cash
equivalents and restricted cash* and the filing **nowhere states the
restricted part**, `cash_and_equivalents` is the caption **entered whole**
(E69, `same_page`), and the page names that it contains an unstated
restricted portion. **Where the filing states the restricted amount, it
is subtracted** -- the NVR application of E71 stands and governs.

**WHY.** The owner: *"A block over a probably-small number is worse than
a noted figure. If the 10-K note on cash ever states the restricted
amount, subtract it."* The error is one-sided -- it can only overstate
cash -- and it is named on the figure so a reader can see it.

**APPLIED 2026-10-05, CPRT.** Consolidated Balance Sheets at 2026-07-31:
`Cash, cash equivalents, and restricted cash $ 1,907,901` (thousands).
The 10-K was searched for the restricted amount; every mention of
restricted cash sits in that combined caption, the cash-flow
reconciliation (same 1,907,901) or the fair-value and credit-risk
boilerplate -- no figure. Entered 1,907,901,000 USD.

