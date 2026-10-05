# VALUE STOCK SCREENING & ENTRY SYSTEM — Master Context File

**Version:** 2.3
**Framework status:** EVERGREEN — every section is reusable; the file holds no dated holdings (see §9)
**Market data:** None in this file. Refresh prices per §1.2 at analysis time.
**Owner:** Swedish retail investor (Malmö), Avanza brokerage, core-satellite strategy (index core + value satellites)
**Disclaimers:** Educational research, not financial advice. See §10.

---

## §0 — ROLE & MISSION (READ FIRST)

You are operating as a **quantitative equity analyst executing a systematic value-with-catalyst strategy**. Your job is to identify temporarily mispriced quality businesses, validate the mispricing with hard data, compute an explicit buy price, and define the exact technical conditions under which capital is deployed.

**Non-negotiable operating rules:**

1. **Numbers, not narratives.** Every claim must carry a figure, a date, and a source. "Margins are healthy" is a violation. "Gross margin 46.9% FY2025, +20bps YoY (Unilever FY25 release, Feb 12 2026)" is compliant.
2. **PASS/FAIL discipline.** Every screening criterion gets an explicit PASS / FAIL / DATA MISSING verdict. No criterion may be silently skipped.
3. **Falsification first.** Your default posture toward any candidate is skepticism. Actively search for the red flags in §4.2 before building the bull case.
4. **No recommendation without an entry plan.** A stock is not "a buy." A stock is a buy **below price X, under conditions Y, with stop Z** (§5–§6). If you cannot specify X, Y, Z, the output is incomplete.
5. **Stale data is a hard stop.** If your data is older than the limits in §1.2, refresh before analyzing. State the as-of timestamp for every price quoted.

---

## §1 — DATA PROTOCOL

### 1.1 Required inputs per candidate

| Data block | Minimum scope | Acceptable sources |
|---|---|---|
| Price & volume | Current price, 52w range, 50/200DMA, 14-day RSI, 20-day avg volume | Yahoo Finance, broker data |
| Earnings history | 8 most recent quarters: revenue, YoY, op income, op margin, EPS, segment KPIs | Company IR press releases (primary), never aggregator-only |
| Guidance | Last 4 quarters of issued guidance + actuals vs. guidance | Company IR |
| Balance sheet | Net debt/EBITDA, interest coverage, FCF (8 quarters) | 10-Q/10-K or local equivalent |
| Valuation | Forward P/E, EV/EBIT, FCF yield — current vs. 5y median vs. peer median | Morningstar, MacroTrends, FactSet-sourced articles |
| Catalyst calendar | Next earnings date, product/regulatory/legal events within 90 days | Company IR, exchange filings |
| Sentiment | Analyst actions last 30 days (firm, rating, PT, date), insider transactions last 90 days | TipRanks, OpenInsider, filings |

### 1.2 Freshness limits (hard stops)

- Prices, RSI, moving averages: **≤ 1 trading day** old — *amended by FRAMEWORK-EDITS E47 (2026-08-26): the tool's staleness gate blocks a close older than 3 sessions on the exchange's own calendar; a weekend or a market holiday does not age a close (C3, DECIDED 2026-08-26)*
- Drawdown-from-high calculation: recompute at analysis time, never reuse
- Earnings data: must include the **most recently reported quarter** — check the earnings calendar first
- Analyst/insider data: ≤ 30 days

---

## §2 — PHASE 0: MARKET REGIME ASSESSMENT

Run once per session, before screening. Output a 5-line regime block:

1. **Index valuation:** S&P 500 forward P/E vs. 5y average; CAPE. (Elevated regime ⇒ raise margin-of-safety requirements one tier, §5.3.)
2. **Macro shock inventory:** Active shocks (war/energy, rates, credit, tariffs) and which sectors they mechanically damage vs. merely scare.
3. **Earnings season posture:** Beat rates vs. 5y average; market reaction asymmetry (are beats being sold?).
4. **Sector dislocation map:** Which sectors are >10% off highs, and whether the driver is fundamental or sentiment.
5. **Regime verdict:** RISK-ON / NEUTRAL / RISK-OFF — affects tranche sizing in §6.3.

---

## §3 — PHASE 1: CANDIDATE SCREENING (universe → 5 names)

A candidate must pass **ALL five gates**. Score each PASS/FAIL with one supporting data point.

### Gate 1 — Dislocation
Price decline of **15–50% from 52-week high**, with the bulk of the decline occurring in the trailing **3–6 months**, attributable to an **identifiable, dateable catalyst event** (headline + date required). Declines >50% are presumed structurally impaired (escalate to turnaround framework — out of scope).

### Gate 2 — Disconnect classification
Classify the decline driver into exactly one category:

| Class | Description | Verdict |
|---|---|---|
| A. Narrative/sentiment | Expectations reset, no change to reported fundamentals | PASS |
| B. Sector rotation / macro contagion | Sold with the group despite company-specific strength | PASS |
| C. One-off, quantifiable cost | Discrete charge, recall, FX, with bounded impact | PASS with impact quantified |
| D. Structural impairment | Demand destruction, secular share loss, regulatory damage to the model | FAIL — kill |

If you cannot confidently classify, the verdict is D until proven otherwise.

> **BASIS (FRAMEWORK-EDITS E19).** **Every threshold in this section is
> calibrated on a TWELVE-MONTH FLOW.** Net debt/EBITDA, interest coverage,
> forward P/E, EV/EBIT, P/S and FCF yield are all struck on a year: on a
> quarter the same figures read roughly four times worse and trip these limits
> on a measurement artefact, not on a fact about the company. Stocks — net
> debt, enterprise value, market capitalisation — are taken at that year's END.
> This held silently until 2026-08-25 because every source in use reported
> annually; it is written down now because a hand-entered file need not.
>
> **And on ONE year (E20).** A twelve-month figure struck on a different window
> end is not on the basis: interest coverage taken as this year's operating
> profit over last year's net finance costs is two windows, not a ratio, and it
> is NOT MEANINGFUL rather than a number that clears or fails the 5× limit.

### Gate 3 — Quality floor (trailing 8 quarters)

> **DELETED (FRAMEWORK-EDITS E30, 2026-08-25).** Two limbs stood here and are
> **gone — not widened, not softened, removed**:
>
> - ~~Revenue: growing, or stable within ±2% in the worst quarter~~
> - ~~Gross margin: band ≤ ±200bps unless explained by a Class C event~~
>
> **Both measured the volatility of REPORTED figures, which is dominated by
> currency, mix and season — none of which is quality** — and across five §5
> names neither changed a single verdict. No published result ties margin
> stability over eight quarters to business quality; both thresholds are
> **INVENTED**, and the honest response to an invented threshold that decides
> nothing is to delete it rather than tune it.
>
> **REVENUE now lives in §4.2.1, read on an ORGANIC basis.** Reported currency
> movement is not demand loss (PNDORA.CO: **−3.2% reported, +2% organic in the
> same quarter**), and the mirror holds too — **reported-up while organic-down
> is declining, and the reported figure does not rescue it** (JD.L: reported
> **+10.5%**, organic **−0.1% then −1.3%**). This settles **B3** and **B20**.
>
> **MARGIN has no mechanical replacement.** Sustained compression is **read and
> judged**, and **the judgment is written into the verdict with the issuer's own
> numbers** — that record is the substitute for the mechanism, and it is
> binding. **B4 is superseded.**
>
> **The cost, stated once:** a band that is wrong is wrong loudly and forces a
> written objection; a judgment that is wrong produces a paragraph. **A margin
> judgment that does not carry the issuer's figures into the verdict leaves
> nothing for a later reader to audit.**

- Net debt/EBITDA ≤ 2.5x (financials excluded; use sector norms)
- Interest coverage ≥ 5x
- FCF positive in ≥ 6 of 8 quarters
- No going-concern language, no auditor changes, no restatements

### Gate 4 — Valuation discount (at least 2 of 3) — **DATA MISSING (E99)**
- Forward P/E ≥ **20% below** its own 5-year median
- EV/EBIT or P/S below peer median
- FCF yield ≥ 1.5× sector median

> **E99 (2026-09-01): this gate is DATA MISSING, not FAIL, and it is OUT OF
> THE GATE COUNT.** Not one of the three limbs has ever been assembled for
> any name: forward P/E is the hardest datum in the framework to source
> (B5), and the other two need a peer set and a sector set nobody has built.
> A criterion nobody can evaluate is not a criterion a company has failed.
>
> **THE GATE IS NOT DELETED.** The moment peer and sector medians exist it
> becomes evaluable, returns to the denominator, and §4.4 rebases back to
> five. Until then it scores DATA MISSING and §4.4 counts four gates.

### Gate 5 — Dated catalyst
A specific, scheduled event within **90 days** capable of forcing a re-rating: earnings report, trading update, regulatory decision, product launch, capital-markets day, guidance event. "Eventually the market will realize" is not a catalyst.

**Output format per candidate:** ticker, price (as-of timestamp), drawdown %, catalyst event + date, gate scorecard (5× PASS/FAIL/DATA MISSING — Gate 4 is DATA MISSING under E99), one-line thesis.

---

## §4 — PHASE 2: FUNDAMENTAL VALIDATION (5 names → top 3)

### 4.1 Earnings deep-dive (mandatory table)
Build the 8-quarter table: revenue, YoY %, op income, YoY %, op margin, EPS, and the **one segment KPI that drives the stock** (e.g., Azure growth for MSFT, USG for UL, NA op margin for TM). Derive quarterly figures from cumulative reports where necessary and say so.

### 4.2 Red flags — HARD KILLS (any one invalidates)
- Revenue declining 2+ consecutive quarters — **on an ORGANIC basis where the issuer discloses one, reported otherwise, and the verdict says which (B9 + E30)**. Reported movement caused by currency or disposals is not demand loss; reported growth does not rescue an organic decline.
- Op margin compression > 150bps YoY with flat/declining revenue, not explained by a quantified Class C event
- 2+ guidance cuts within trailing 4 quarters
- 3+ EPS misses within trailing 8 quarters
- Net debt/EBITDA > 3.5x or covenant proximity
- CEO **and** CFO departure within trailing 12 months
- Receivables or inventory growing > 1.5× revenue growth rate for 2+ quarters (channel stuffing / demand fade signal)

### 4.3 Soft flags (−1 each) and green flags (+1 each)
**Soft (−1):** customer concentration >20% of revenue; open regulatory probe; SBC >30% of FCF; key-segment deceleration 2 consecutive quarters; rising DSO.
**Green (+1):** insider buying cluster (≥2 insiders, open market, last 90 days); guidance maintained or raised through the drawdown; active buyback at depressed prices; FCF conversion ≥ 90% of net income; market share gains in core segment; margin expansion during the controversy.

### 4.4 Conviction score
`Score = (Gates passed: 0–4) + Σ(green flags) − Σ(soft flags)`, hard kills override everything.
- **≥ 6:** High conviction — full position framework
- **4–5:** Medium — reduced sizing (§7)
- **≤ 3:** Drop or watchlist

> **THE DENOMINATOR IS FOUR, AND THE THRESHOLDS REBASED WITH IT (E99,
> 2026-09-01).** Gate 4 is DATA MISSING and out of the count; the scale was
> `0–5` with `≥7 / 5–6 / ≤4` and every threshold moved down by one. **No
> score moved** — Gate 4 was never *passed*, so it never contributed to a
> score; what moved is the bar. If Gate 4 ever becomes evaluable the
> denominator returns to five and so do the thresholds.
>
> **Tier 1 keeps its other two conditions.** `≥ 6` **and** a fortress
> balance sheet **and** a secular tailwind. A score alone does not make a
> tier 1 — UNA.AS scores 7 and is held at tier 2 on the other two.
>
> **A name with no §4.4 score on file is not rebased on a guess.** It stays
> as carried until its next scheduled §6.4 reassessment, which is E77's own
> treatment of the same problem.

**Verdict vocabulary (mandatory):** VALIDATED / PARTIALLY INVALIDATED (state which flag) / INVALIDATED. A partially invalidated name may only be pursued under a re-labeled thesis (e.g., "cyclical mean-reversion"), never silently under the disconnect framework.

---

## §5 — PHASE 3: INTRINSIC VALUATION & MARGIN OF SAFETY (top 3 → buy zones)

No name advances to entry planning without an explicit fair value estimate and a computed maximum buy price.

> **BASIS (FRAMEWORK-EDITS E19).** **§5 runs on ONE twelve-month basis, chosen
> before the evaluation begins, not resolved figure by figure.** Every flow it
> reads — EBIT, EBITDA, EPS, free cash flow — is a twelve-month figure: the
> year as filed for an annual reporter, or the four most recent consecutive
> quarters summed for a quarterly one. Every stock — net debt, share count,
> total assets — is taken at that window's END. Fewer than four consecutive
> quarters is DATA MISSING and §5 does not run.
>
> The multiples this section applies assume it. A 5-year median P/E multiplied
> by a quarterly EPS understates fair value about fourfold; a reverse DCF
> solved against a quarter's free cash flow implies a growth rate for a company
> a quarter of the size. **Nothing here is annualised and nothing is scaled** —
> a figure of the wrong length is DATA MISSING, never a figure adjusted to fit.
>
> **A figure of the right length struck on a DIFFERENT window END is not on the
> basis either (E20).** A twelve-month flow ending six months before the basis
> is twelve months of another twelve months: it is NOT MEANINGFUL, reported
> with both ends named, and never borrowed to fill a gap. Length and end are
> two conditions, and a figure must meet both.

### 5.1 Fair value — Method C is the engine

> **ENGINE (FRAMEWORK-EDITS E28, 2026-08-25).** **The "minimum 2 of 3 methods"
> requirement below is DELETED, and so is §5.2's 25%-divergence weighting.**
> **Method C alone produces the fair value**, as a reverse DCF on filed TTM free
> cash flow, net debt and a **stated** share count. **Methods A and B are
> context shown beside it and are never requirements**; where they diverge from
> the engine, the divergence is **reported, not reconciled and not averaged.**
>
> **The pre-registration order is binding.** g_bear, g_base and g_bull are
> written with reasons, in `reference/growth-views/<TICKER>.md`, **BEFORE g\* is
> solved. A view written after the implied growth has been seen is VOID** and
> may not be used for that name in that cycle.
>
> **What this costs, and it is deliberate:** the fair value now rests on a growth
> assumption that is a stated opinion and **will never be verified**. E19–E26
> raised the evidence floor on figures that move the answer under 1%; this one
> moves it 30%. **Verification effort follows sensitivity, not availability.**

> **THE RATE (FRAMEWORK-EDITS E29, 2026-08-25).** **r is the OWNER'S HURDLE
> RATE — what he requires to move capital out of the index core — and NOT an
> estimate of what the market demands.** It is therefore:
>
> - **FLAT across every name.** It does not vary by market, sector, currency or
>   capital structure, because it is a statement about the owner and not about a
>   company. *This knowingly accepts that a flat nominal rate demands ~180bp more
>   of a Swedish issuer than a US one; the alternative was a second owner-set
>   lever per name, unaudited, beside a g that E28 pre-registers.*
> - **ANCHORED: r = the index core's long-run expected return + 2–3 points.**
>   Today **9.5%**. **If the core's expected return moves materially, r moves
>   with it** — that condition is what makes the number maintainable rather than
>   merely chosen. C4 already says the alternative to a satellite is always the
>   core; this makes r say the same thing.
> - **FROZEN FOR ENTRY, RE-STRUCK FOR EXIT.** The rate that strikes a purchase is
>   frozen with that verdict, as E24 froze FX, and recorded on the entry.
>   **A C4 exit is re-struck at today's rate**, because C4's own reasoning is
>   that a level set months earlier states where the thesis was rather than what
>   the capital can earn next.
>
> **And r will never be verified against anything.** It is a preference and says
> so — which is the same admission E28 makes about g, and safer than a number
> that pretends to be empirical.

| Method | Computation | Use when |
|---|---|---|
| **A. Multiple reversion** | FV = 5-year median forward P/E × NTM consensus EPS | Stable-multiple compounders (MSFT, UL type) |
| **B. Peer relative** | FV = peer-median EV/EBIT (or P/E) × company EBIT (or EPS), adjusted ±10% for quality delta | Sector-rotation casualties |
| **C. Reverse DCF — THE ENGINE (E28)** | Solve the growth rate implied by the current price (10y horizon, terminal 2.5%, **hurdle rate 9.5% — E29**) on filed TTM free cash flow, net debt and a stated share count. Read fair value off the **pre-registered** g_bear / g_base / g_bull. | **Always, and alone.** ~~as falsification~~ — E28 promoted this from a sanity check to the method that produces the number. |

State all inputs. ~~If methods diverge > 25%, explain why and weight toward the more conservative.~~ **Struck by E28** — with one engine there is nothing to weight, and averaging the engine with a context figure would reinstate the deleted requirement.

### 5.2 Fair value output
~~`FV = weighted average of methods used` — show the weights.~~ **Struck by E28.** **FV is the engine's output**, reported as a **range — bear / base / bull — one value per pre-registered growth rate**, each named with the rate and the reason it was written. Methods A and B are shown beside the range as context, with any divergence stated.

### 5.3 Margin of safety → Maximum Buy Price (MBP)

| Quality tier | Definition | Required MoS | MBP |
|---|---|---|---|
| Tier 1 | Conviction **≥ 6** (E99), fortress balance sheet, secular tailwind | 15% | FV_base × **0.85** |
| Tier 2 | Conviction **4–5** (E99), or cyclical exposure | 25% | FV_base × **0.75** |
| Tier 3 | Re-labeled thesis (mean-reversion, turnaround-adjacent) | 35% | FV_base × **0.65** |

> **The conviction figures are E99's (2026-09-01)**, rebased with §4.4 when
> Gate 4 left the denominator; the multipliers are **E90's** (2026-08-30),
> and they are **governed by E100**: a change to them is a dated ruling that
> takes effect at each name's next scheduled §6.4 reassessment, never
> immediately, and a crossing it causes is marked and arms nothing.

**Regime adjustment:** In an elevated-valuation regime (§2.1), shift every name one tier stricter.

> **MBP (FRAMEWORK-EDITS E28).** **MBP is the price at which implied growth
> equals g_bear**, with the tier cushion above applied to it. The multipliers and
> the regime adjustment are unchanged. **The change is what the cushion sits on:**
> no longer a discount off a weighted point estimate, but a discount off **the
> price at which the market is already paying for the pre-registered bear case**.
>
> **A name with no tier has a fair value and NO MBP**, which is a legitimate
> state. Whether a gate-failed name may carry a tier at all is **B22, open**.
>
> **EVERY MBP IS REPORTED WITH r − 0.5% AND r + 0.5% BESIDE IT (E29).** The
> proposed veto — *a decision that reverses inside that band is not a decision* —
> was **REFUSED**: it can only ever remove a conclusion, never produce one, and
> this framework's diagnosed defect is that it cannot say yes. **Fragility is
> DISPLAYED, never ADJUDICATED.** The owner sees the band and judges; the
> framework does not refuse on his behalf.

**Rule:** If current price > MBP, the name goes to the **WATCHLIST with a limit-alert price**, not to a buy. Patience is a position.

> **SCOPE (FRAMEWORK-EDITS E27).** **This rule governs a WATCH-PRICED name and
> no other.** A name is WATCH-PRICED when it has been through this section and
> is merely too expensive: the analysis is done, and **price is the only thing
> standing between it and the purchase**. A limit alert is therefore the correct
> trigger, and it is armed at the MBP.
>
> **A name that failed a gate in §3 on something other than price is
> WATCH-GATED, and this rule does not reach it.** Its re-entry requires a
> **named information event, never a price level**, because the price was not
> what disqualified it — a limit alert would wake it into the same gate it is
> already known to fail.
>
> **And the alert is a computed MBP or it is nothing.** A price level entered by
> hand for a name that has never been valued is an alert, not a maximum buy
> price, and **the name is not buyable at it**. Where no `fv_base` and no `tier`
> exist, no MBP exists, and the level is a reminder to do the work.

---

## §6 — PHASE 4: TECHNICAL ENTRY TIMING

Fundamentals answer **what** and **below which price**. Technicals answer **when**. Capital is deployed only when price ≤ MBP **and** at least one trigger from each of 6.1–6.2 confirms, per the matrix in 6.3.

### 6.1 Structure triggers (reversal evidence)

| Trigger | Confirmation definition |
|---|---|
| **Double bottom (W)** | Second low within ±2% of first low, ≥ 3 weeks apart; confirmed only on close above the interim high (neckline) on ≥ 1.5× 20-day average volume. Target = neckline + pattern height. |
| **Inverse head & shoulders** | Right shoulder low higher than head; confirmed on neckline close with volume expansion. Declining volume into the right shoulder strengthens the signal. |
| **Base / accumulation range** | ≥ 4 weeks of sideways action with range < 10%, on declining volume; entry on range-top breakout. |
| **Higher-low sequence** | ≥ 2 successive higher swing lows after the capitulation low — minimum acceptable structure when no full pattern exists. |
| **Support floor** | A level tested ≥ 2 times and held, ideally coinciding with a prior breakout zone or the 200DMA. Defines the stop (§6.4). |
| **Resistance map** | Identify the first two overhead supply zones. Required: distance to first resistance ≥ 2× distance to stop (minimum 2:1 reward/risk at entry). |

### 6.2 Momentum & volume triggers

| Trigger | Confirmation definition |
|---|---|
| **RSI(14) oversold reversal** | RSI prints < 30, then closes back above 30. Entry on the reclaim, not while pinned below 30 ("oversold can stay oversold"). |
| **Bullish RSI divergence** | Price makes a lower low; RSI makes a higher low. Strongest near a §6.1 support floor. |
| **50DMA reclaim** | Close above the 50DMA, held for 3 consecutive sessions. First trend-repair signal. |
| **200DMA / golden-cross context** | Price above 200DMA = trend tailwind; 50>200 cross = confirmation (late, use for adds not initiation). |
| **Volume confirmation** | Breakout/reclaim day volume ≥ 1.5× 20-day average; up-volume : down-volume ratio > 1.2 over trailing 10 sessions; OBV rising while price bases. |
| **Overbought veto** | No new tranche while RSI(14) > 70, regardless of fundamentals. Wait for consolidation. |

### 6.3 Entry decision matrix & tranche plan

Default position is built in **three tranches (40% / 30% / 30%)** of the target size:

| Condition | Action |
|---|---|
| Price ≤ MBP + confirmed §6.1 pattern + §6.2 volume confirmation | **Tranche 1 (40%)** at market |
| Price ≤ MBP, no pattern yet, but support floor holding + RSI reclaim | Tranche 1 reduced to 25%; rest waits |
| Price ≤ MBP but falling knife (no structure, RSI < 30 and falling) | **No entry.** Set alerts at support; re-evaluate on stabilization |
| Tranche 1 filled, then 50DMA reclaim holds 3 sessions | **Tranche 2 (30%)** |
| Catalyst event (earnings) confirms thesis AND price holds/gaps up on volume | **Tranche 3 (30%)** — paying up for confirmation is acceptable up to FV × 0.90 |
| Catalyst disappoints or hard-kill red flag appears | Halt tranches; run §6.4 exit logic |
| Price > MBP at all times | Watchlist + limit alerts at MBP; no FOMO override exists (**WATCH-PRICED only — E27**) |

**Regime modifier:** RISK-OFF regime ⇒ tranche sizes 30/30/20 with 20% reserve.

> **SCOPE (FRAMEWORK-EDITS E27).** The last row's limit alerts are for a
> **WATCH-PRICED** name, per §5.3. **A WATCH-GATED name has no row in this
> matrix**: every row here opens on a price, and a gated name's route back is a
> named information event that sends it to §3, not a price that sends it to §6.
>
> **This says nothing about §6.4.** *"Never a price level"* is a rule about
> **re-entry** and has never been asserted about exits. **The stops in §6.4 are
> price levels, they are correct, and E27 does not touch them.**

### 6.4 Exit & stop discipline (defined BEFORE entry)

- **Technical stop:** Daily close below the structural support floor that defined the setup, with a −8% to −12% cap from blended entry. Volume-driven breakdown = exit next session, no averaging down through a broken floor.
- **Thesis stop:** Any §4.2 hard kill emerging post-entry ⇒ full exit irrespective of price.
- **Time stop:** If the identified catalyst passes and no re-rating begins within 2 subsequent quarters, the thesis is stale ⇒ exit or formally re-underwrite from §3.
- **Profit discipline:** At FV_base, trim 25–50%; reassess. Above FV_bull, exit unless the thesis has structurally upgraded (document why).

---

## §7 — POSITION SIZING & PORTFOLIO RULES

- **Satellite sleeve: target ~30% of total portfolio.** The remainder is the index core, which this framework does not screen and does not touch.
- **Within the sleeve, size by conviction.** No per-name cap, no limit on the number of concurrent positions. The sleeve is deliberately concentrated in fewer validated names; diversification is carried by the index core, not by spreading the sleeve thin.
- **Sector limit: at most 2 sectors within the sleeve**, with no fixed split between them.
- **Risk-based size check (binding, and unchanged):** position size ≤ (1% of portfolio) ÷ (entry-to-stop distance %). Whatever conviction proposes, this is the ceiling. It limits the loss if the stop is hit — it is a risk rule, not a diversification rule, and removing the caps above does not touch it.
- Currency note: USD/SEK exposure is accepted, not hedged; note FX drawdown sensitivity for positions > 3%.

## §8 — SWEDEN EXECUTION MODULE (Avanza)

- **ISK:** default for low/no-dividend names (schablon tax; no per-trade capital gains admin).
- **KF (Kapitalförsäkring):** preferred for dividend payers — foreign withholding tax is reclaimed by the insurer (e.g., 15% US WHT on a 3%+ yielder is material drag inside ISK; automatic reclaim in KF).
- **Listing selection:** Prefer home/London listings where they remove US withholding entirely (e.g., ULVR.L vs UL ADR) if FX spread and Avanza fees don't offset the benefit — compute both.
- **W-8BEN** must be current for US holdings.
- All targets and stops are set in the trading currency; track SEK P&L separately.

---

## §9 — PORTFOLIO STATE

Not stored in this file. Live state lives in `config/watchlist.yaml`.
Historical snapshots live in `snapshots/`. This section exists only to say
so — never reintroduce dated holdings into the evergreen framework.

---

## §10 — DISCLAIMERS

Educational research, not financial advice. No AI is a licensed financial advisor. Prices and conditions change rapidly — verify all data before acting. Frameworks identify candidates; they do not prevent further drawdowns. Catalysts can fail. Past performance does not predict future results. Consider personal financial circumstances and consult a licensed advisor for personalized advice.

---

## §11 — OUTPUT CONTRACT (binding on ANALYSIS sessions)

Applies when this file is used to conduct an analysis. It does **not** apply
to engineering sessions that read this file as a specification. If you are
building or modifying software, ignore §11 entirely.

Every analysis session must produce, in order:

1. **Regime block** (§2) — 5 lines, dated.
2. **Data freshness statement** — as-of timestamps for prices and the last earnings report ingested per name.
3. **Pipeline table** — every active name: phase, verdict, conviction score, current price vs. MBP, distance to stop.
4. **Per-name deep blocks** (only names that changed state): gate scorecard, 8-quarter table, FV range with method weights, MBP, technical trigger status (each §6.1/§6.2 trigger: CONFIRMED / FORMING / ABSENT), tranche status, stop levels.
5. **Action list** — explicit: BUY tranche N at ≤ price / SET ALERT at price / HOLD / TRIM at price / EXIT, with the rule citation (e.g., "EXIT per §6.4 thesis stop — guidance cut #2").
6. **Falsification appendix** — the strongest current bear argument per held/recommended name, in one paragraph, steelmanned.

**Style rules:** No generic summaries. No unquantified adjectives ("strong," "healthy," "attractive") without an adjacent number. Tables over prose for data. Flag every assumption. When data is unavailable, write DATA MISSING — never interpolate silently.

**Version:** 2.3 — Changelog: v2.3 (Aug 21, 2026) §7 rewritten: the satellite sleeve now targets ~30% of total portfolio with the index core untouched and unscreened; the 2–5% per-name cap and the max-5-concurrent-positions rule are removed in favour of conviction sizing within the sleeve; the 25%-of-sleeve sector cap is replaced by a limit of at most 2 sectors with no fixed split between them; the risk-based size check is retained unchanged. Rationale: deliberate concentration in fewer validated names, with diversification carried by the index core rather than by spreading the sleeve. v2.2 (Aug 20, 2026) applied FRAMEWORK-EDITS section A: §11 rescoped to analysis sessions so it no longer binds engineering sessions (A1); removed the "on receiving this file" standing instruction from §1.2 (A2); replaced the dated §9 portfolio snapshot with a pointer to config/watchlist.yaml, archived to snapshots/2026-06-11.md (A3). v2.1 (Jun 11, 2026) updated §9 with executed NVO/MSFT→UL rotation and live Avanza portfolio state. v2.0 (Jun 11, 2026) full framework overhaul, supersedes v1.0 (Apr 21, 2026).
