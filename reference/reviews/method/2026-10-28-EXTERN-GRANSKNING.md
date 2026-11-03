# Extern granskning: våra värderingar och metoden bakom dem

*Sammanställt 2026-10-28 ur repot `stocks` (bevakningslistan, FRAMEWORK, FRAMEWORK-EDITS, metodrapporterna och motorns strike-dokument). Allt under DEL A–E är kopierat ordagrant ur källfilerna, inte omskrivet; bara den här inledningen är ny.*

---

## Till dig som granskar (läs först)

Jag är en privat investerare som bygger en värderingsmotor tillsammans med en AI. Vi har haft fel förut: en hel metodombyggnad gjordes 2026-10-27 för att förra versionen räknade förvärv som ren kostnad, lät treårssnittet släpa ett år och lät bear-fallet bara sänka tillväxten. Jag vill att du **letar efter fel, inte bekräftar**. Ta ställning. Säg rakt ut var du tror att vi har fel och varför, och säg också när du tror att något håller.

**Vad metoden gör, i korthet** (detaljerna i DEL A–C):

1. **FCF0** = treårssnitt av fritt kassaflöde, rensat från rörelsekapitalets svängningar, med räntan återlagd efter skatt (E140), snittet rullat ett år framåt (E143). Förvärv dras **inte** av som kostnad — de värderas separat som ett "förvärvsprogram" till bolagets egen historiska avkastning på förvärvat kapital, ROIIC (E142).
2. **Bryggan** från företagsvärde till aktievärde: nettoskuld på senaste balansräkning + väntande affärer (i högsta änden) + neutraliserat rörelsekapital; pensionsunderskott efter skatt (E146). Hyra är en rörelsekostnad, leasingskulden läggs inte till (E117).
3. **Tillväxt** härleds ur bolagets egen organiska historik (E144) när fem år finns; annars en förregistrerad "vy" (bear/base/bull).
4. **Cykliska** bolag normaliseras över cykeln; **bear** sänker nivån till svagaste året, inte bara tillväxten (E143).
5. **Diskonteringsränta** r = 9,5 %. Ett ankare g* = den tillväxt som dagens kurs implicerar.
6. **"Would Warren own it" (E145)**: Q1 materiell ROIC ≥ 15 %, Q2 stabilitet, Q3 skuld ≤ 3× FCF0, Q4 kapitalallokering (ROIIC ≥ r), Q5 begriplig. Faller ett bolag här blir det DROPPED oavsett pris.
7. Utöver detta finns **grindar** (§4 hårda stopp, t.ex. två sänkta prognoser i rad, fallande omsättning) som kan hålla ett bolag i WATCH-GATED fast värdet ser bra ut.

**Statusord:** INTAKE = intagen för vidare arbete · PIPELINE = kandidat · WATCH-PRICED = godkänd, väntar på pris (MBP = högsta köpkurs) · WATCH-GATED = stoppad av en grind · HELD = vi äger den · DROPPED = struken.

## Översikt (kurs = stängning 2026-10-26/27, lokal valuta)

| Bolag | fv base | bear | bull | Kurs | Q1–Q5 | Status |
|---|---:|---:|---:|---:|---|---|
| ACAD.ST | 158.74 | 110.63 | 181.95 | 112.40 | se doc | WATCH-PRICED, tier 3, MBP 103.18 |
| ACN | 275.51 | 167.04 | 353.60 | 247.23 | P P P P P | INTAKE |
| ALV | 71.74 | −18.41 | 99.72 | 115.32 | P F F P P | DROPPED |
| AOS | 64.37 | 38.29 | 85.58 | 61.91 | P P P F P | INTAKE |
| AUTO.L | 4.99 | 3.68 | 6.46 | 5.28 | P P P P P | WATCH-PRICED |
| BOUV.OL | 54.42 | 46.07 | 69.34 | 51.70 | – P P F P | inte på listan |
| CENTA | 40.19 | 20.26 | 54.70 | 39.13 | F F F F P | **HELD — säljs vid 40.19** |
| CPRT | 26.96 | 18.33 | 35.84 | 29.15 | P P P P P | INTAKE |
| CROX | 171.83 | −18.94 | 250.10 | 118.85 | P F P P P | DROPPED |
| CTSH | 73.96 | 44.15 | 109.95 | 69.34 | P P P F P | **HELD**, tier 3 |
| DECK | 85.05 | 26.83 | 160.03 | 80.37 | P P P P P | WATCH-GATED |
| GDDY | 79.99 | 27.90 | 132.86 | 109.82 | P P P P P | WATCH-PRICED |
| HRB | 68.38 | −4.65 | 96.54 | 50.06 | P P P F P | WATCH-GATED |
| LIAB.ST | 66.68 | −5.29 | 123.14 | 129.50 | F P F F P | DROPPED |
| LII | 309.69 | 92.28 | 309.69 | 365.64 | P P P P P | INTAKE |
| LOPE | 136.56 | 4.96 | 146.29 | 160.71 | P F P P P | DROPPED |
| MC.PA | 392.95 | 239.77 | 398.90 | 385.40 | – P P F P | WATCH-PRICED |
| MEKKO.HE | 10.95 | 9.25 | 16.33 | 9.17 | – P P P P | WATCH-GATED |
| MUSA | 268.53 | 201.24 | 301.79 | 539.14 | P P F P P | DROPPED |
| NVR | 7,682.75 | 5,138.49 | 7,682.75 | 5,727.77 | P P P P P | WATCH-GATED (hårda stopp) |
| PEP | 65.28 | 52.55 | 84.85 | 135.46 | P P P F P | struken |
| PNDORA.CO | 903.81 | 222.68 | 933.93 | 838.40 | P F P F P | DROPPED |
| RBREW.CO | 195.97 | 83.63 | 299.50 | 435.40 | P P F F P | struken |
| RMV.L | 4.11 | 2.71 | 5.28 | 5.31 | – P P P P | PIPELINE |
| ULTA | 601.27 | 81.39 | 601.27 | 625.33 | P P P P P | INTAKE |
| GNTX | 27.45 | 15.71 | 29.62 | 20.21 | se doc | WATCH-GATED (hårt stopp) |
| SFM | 78.47 | 38.47 | 78.47 | 64.41 | se doc | WATCH-GATED (hårt stopp) |
| BKNG | 218.18 | −2.96 | 281.48 | 150.14 | Q2 F | ej intagen |
| TPR | 64.37 | 8.33 | 102.71 | 111.39 | se doc | över värdet |
| OLVAS.HE | – | – | – | – | – | WATCH-GATED (två prognossänkningar) |

*Q1–Q5 för de fem sista och ACAD.ST: se respektive dokument i DEL E. "–" i Q1 = inget investerat kapital tryckt, testet kan inte avgöras.*

## Det vi själva tvivlar mest på

1. **CENTA (vi äger den).** Faller Q1–Q4 och ska säljas vid base 40.19. Värdet vilar till stor del på hur två färska förvärv (TRIXIE, Burpee — pris ej publicerat, vårt intervall är en uppskattning) krediteras tillbaka till bolagets egen ROIIC 4,85 %. Är det rätt sätt att värdera en köpare vars ROIIC ligger under r?
2. **ULTA och LII** har bull = base, eftersom den härledda tillväxten (ULTA 8 %, LII ~4 %) slår i taket. ULTA:s värde steg från 400 till 601 bara av att tillväxten härleddes ur historiken i stället för en vy på 3,5 %. Är fem års organisk tillväxt en rimlig grund för tio år?
3. **ACAD.ST** — 6 % organisk tillväxt i tio år, i en bransch där politiken kan förbjuda vinstuttag i skolan. Siffrorna fångar inte den risken.
4. **NVR** — tioårsfönstret ser inte 2008, så en husbyggare ser inte cyklisk ut. Klarar Q1–Q5 och ligger 25 % under värdet, men står stilla på två hårda stopp.
5. **Organisk tillväxt saknas** för de flesta amerikanska förvärvare (ACN, CTSH, CENTA, GDDY, AOS, CPRT, HRB); där står vyn kvar och ROIIC räknas med vyn som organisk del.
6. **Bear-värden under noll** (ALV, CROX, HRB, LIAB, BKNG): rimligt utfall av "sänk nivån till svagaste året", eller ett tecken på att metoden överreagerar?

## Frågor vi vill ha svar på

1. Är **E140/E142-konstruktionen** (förvärv ut ur både flödet och tillväxten, sedan tillbaka som ett program värderat till egen ROIIC) försvarbar? Dubbelräknar eller missar den något?
2. Är **r = 9,5 %** och terminalantagandena rimliga för de här bolagen och valutorna (USD, SEK, EUR, GBP, DKK, NOK)?
3. Är **Q1–Q5-trösklarna** rätt satta (15 % materiell ROIC, 3× skuld, ROIIC ≥ r)? Stryker de bolag Buffett faktiskt skulle äga, eller släpper de igenom fel bolag?
4. **Bolag för bolag:** finns det något i DEL E där en siffra ser orimlig ut, ett förvärv eller en skuld saknas, fel räkenskapsår, fel valuta eller enhet, aktiesplit som inte tagits hänsyn till, eller en nyhet efter 2026-10-27 som ändrar bilden?
5. Vilka **köp/sälj-beslut** (CENTA sälj vid 40.19, CTSH behåll, ACAD MBP 103.18, NVR vänta) skulle du göra annorlunda, och varför?

*Svara gärna med: (a) de tre allvarligaste felen du hittar, (b) en rad per bolag: håller / tveksamt / fel + varför, (c) metodfrågorna ovan.*

---

## Innehåll

- **DEL A** — Ramverket §4–§5: validering och värdering (ordagrant)
- **DEL B** — Metodrulingarna E140–E147 (ordagrant)
- **DEL C** — Metodgenomgången 2026-10-27: felen vi hittade (F1–F5), regelboken, bear/base/bull-designen, pilot och resultat
- **DEL D** — Den oberoende kontrollen: tre namn räknade för hand, fyra fel bekräftade och rättade
- **DEL E** — Varje bolag: motorns fullständiga värderingskedja och, för ACAD.ST och NVR, hela genomgången steg för steg

---

# DEL A — Ramverket: värdering och kvalitet (FRAMEWORK.md §4–§5, ordagrant)

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

### §5 — PHASE 3: INTRINSIC VALUATION & MARGIN OF SAFETY (top 3 → buy zones)

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



# DEL B — Metodrulingarna E140–E147 (FRAMEWORK-EDITS.md, ordagrant)

### E140 — FCF0 is a three-year mean with working capital taken out, interest is added back after tax, and every deal after the basis enters the bridge

**RULED 2026-10-27 by the owner.** Two independent reviews of CENTA found
that the struck FCF0 was built on years swollen by inventory sell-down. The
owner then said:

> "fixa metodiken, och räkna om ... ingenting får missas som vi nu gjort
> FLERA gånger om burpee, trixie o champion"

He chose each part from options the session put to him, with each option's
effect stated:

- normal-year cash flow: **"3-årssnitt utan lager/rörelsekapital"**;
- interest: **"Lägg tillbaka efter skatt"**;
- deals after the basis: **"Priset i skulden, deras vinst bara om den står i
  dokument"**.

**THE CASE.**

- **CENTA's flows.** Operating working capital released USD 126.6m in FY2023,
  143.6m in FY2024 and 50.6m in FY2025, as the 2021-22 inventory build was
  sold down. A single-year FCF0 of 301.5m capitalised that release as if it
  would recur for ten years.
- **What the fix does to the value.** On the three-year mean with working
  capital out, FCF0 is 216.6m and fv_base falls from 61.83 to 43.06, before
  any deal.
- **Missed deals.** The strike of 2026-10-20 also missed four deals made
  after the basis: Champion, the Pet Distribution contribution, TRIXIE and
  Burpee. Burpee was announced the day before the strike.

**THE RULE.**

> **(1) FCF0** is the MEAN of the last three fiscal years of:
>
> > operating cash flow, LESS the cash effect of the change in operating
> > working capital, LESS capex, LESS SBC where SBC is deducted.
>
> - **What counts as operating working capital:** receivables,
>   inventories, prepaid and other operating assets, payables, accrued
>   liabilities, and deferred revenue or contract liabilities.
> - **What stays in the flow:** income-tax lines, lease lines and
>   long-term lines. A tax-reserve release is not a swing. HRB's discrete
>   FY2026 benefit of 84.1m is reversed on its tax line, so it never
>   reached operating cash flow.
> - **A loan book's receivable.** Where a stripped receivable is a loan
>   book whose provision for losses is added back above it, the provision
>   is deducted with it. Otherwise the credit loss is counted as cash
>   earned (HRB's Emerald Advance).
> - **A combined tag.** Where a combined tag and one of its own components
>   are both stated, the combined tag is dropped. Otherwise the movement is
>   counted twice (ALV FY2023).
> - **E123's shape.** Where the operating asset is inventory (NVR, PHM),
>   the inventory line stays in the flow, because buying it is the business.
>
> **(2) The interest add-back** of E34, E34.1 and E115 is taken **after
> tax**, at the statutory rate of the filer's home country:
>
> | Country | Rate |
> |---|---|
> | US (federal and typical state) | 25% |
> | SE | 20.6% |
> | GB | 25% |
> | DK | 22% |
> | NO | 22% |
> | FI | 20% |
> | FR | 25.8% |
> | DE | 30% |
>
> E105's deduction of dividends paid to minorities stands unchanged.
>
> **(3) Every acquisition, divestiture or partnership contribution after
> the basis's balance-sheet date enters the net-debt bridge** at its
> price:
>
> - cash paid;
> - earn-out at its MAXIMUM;
> - a put on a retained stake at its pro-rata value;
> - LESS cash received.
>
> The acquired business's cash flow enters FCF0 **only where the issuer
> has filed figures for it**. Otherwise it is zero, and the zero is named.
> An undisclosed price is a **LOW-HIGH range** and is never left out. The
> value is printed at both ends.
>
> **(4) No value is struck or printed without an EVENTS LEDGER,**
> `reference/events/<TICKER>.yaml`. The ledger lists every deal after the
> basis, or states that none was found. It also records what was searched:
>
> - the issuer's press releases;
> - every 8-K, 10-Q and 10-K, or the local equivalent, filed after the
>   basis;
> - a news search.
>
> It is dated. `tools/normalize_e140.py` refuses a name without one.

**WHAT THIS DOES NOT DO, stated so nobody assumes it:**

- **It does not rewrite any run record.** Records are statements made on
  the rules of their date (E87). The E140 value is printed beside the
  record's value, from `tools/normalize_e140.py`, until the engine carries
  it natively.
- **It does not write any `fv_base`.** Writing one is the owner's act.
- **It does not decide that deferred-revenue growth is a swing for a
  subscription business.** For GDDY the rule takes it out, which is the
  conservative reading. The value with it kept in is printed as
  sensitivity.
- **It does not settle the CENTA/CENT price gap.** Since 2024 the two
  classes have traded at a ratio of 0.85-0.89. That ratio is reported
  beside the value, never netted into it.

**WHICH EARLIER RULINGS THIS AMENDS.**

- **E31 and E41**, for FCF0: the single basis-year flow is replaced by
  the three-year mean.
- **E34, E34.1 and E115**: the add-back is taken after tax.
- **E35's bridge**: post-basis deals are added.

### E140.1 — the four questions E140 left open: acquisition spend is capex for a repeat buyer, deferred revenue stays a swing, the bridge rolls to the latest balance sheet with its working capital neutralised, and fv_base is rewritten from new records

**RULED 2026-10-27 by the owner**, in the session after E140, on the four
questions E140's results left open (HANDOFF-2026-10-27 items 6-9) and one
follow-up the session put to him on the third. Each was put once, with its
effect on the values stated, and he took the recommended option each time.

**THE RULE.**

> **(1) A repeat buyer's acquisition spend is capex.** Where the filer paid
> cash for acquisitions in **at least two of the three fiscal years** of
> E140(1), FCF0 is also reduced by the **three-year mean** of cash paid for
> acquisitions, net of cash acquired. Every year counts toward the mean,
> including a year with no spend, which counts as zero.
>
> - **No threshold.** The test is whether the spend recurs, not how big it is,
>   and the test decides, not a list. The question put to the owner listed
>   shares of FCF0 (ACAD 69%, ACN 46%, LII 30%, CTSH 29%, PEP 14%, ULTA 12%,
>   AOS 10%, CENTA 10%). On E140's tagged figures the test **catches** ACN,
>   AOS, CENTA, CPRT, CTSH, HRB, LII and PEP. It does **not** catch ULTA,
>   which paid in one year of three (Space NK, FY2025). Non-US names are
>   tested on their stores the same way.
> - **A year whose net figure is a receipt** (cash acquired exceeding cash
>   paid, as in CPRT's FY2023 at -17.7m) counts as zero. It is neither
>   spend nor recurring income.
> - **Divestiture proceeds are not credited** to FCF0. Proceeds received
>   after the basis enter the bridge under E140(3).
> - **Deals after the basis stay in the bridge** under E140(3). The overlap
>   of about one year is accepted as the conservative side.
> - **One deal in three years** is not a pattern. It stays where it is:
>   inside net debt if it was paid before the basis, or in the bridge if it
>   was paid after.
>
> **(2) GDDY's deferred-revenue growth stays out of FCF0**, as E140(1)
> takes it out. No rule changes. The value with it kept in is printed as
> sensitivity. No decision hung on it: the price is above the value either
> way, and the framework changes only when a name is blocked.
>
> **(3) The bridge rolls to the latest filed balance sheet.**
>
> - **Which balance sheet.** At strike time, net debt, every other bridge
>   leg and the share count are taken from the latest filed balance sheet:
>   a 10-Q, an interim report or the annual report, whichever is latest. All
>   are read from that one date. FCF0 stays on the three fiscal years of
>   E140(1).
> - **Working capital is neutralised.** The cash effect of the change in
>   operating working capital between the fiscal year-end and that balance
>   sheet is added back to net debt, with the sign that undoes it. This uses
>   E140(1)'s definition and is read from the interim cash-flow statement's
>   year-to-date lines. Only cash earned without working capital is
>   credited, so a seasonal trough in net debt does not enter the value.
> - **The ledger is cut at that date.** A deal closed on or before the
>   balance-sheet date is already in it, and is not added again. A deal
>   closed after it, or announced and not yet closed, enters under E140(3).
>
> **(4) fv_base is rewritten from a NEW RECORD, never from a side table.**
>
> - **The order.** Once the engine carries E140 and (1)-(3) natively, every
>   struck name is re-struck as a new run record (E87). Its fv_base is then
>   written from that record, on the owner's word given here.
> - **Old records stand.** They are statements on the rules of their date,
>   and are not rewritten.
> - **The side tool's figures.** `reference/normalized/E140-ALL-2026-10-27.md`
>   and `tools/normalize_e140.py` stay as the evidence of 2026-10-27. Nothing
>   is ever typed from them into fv_base.

**WHICH EARLIER RULINGS THIS AMENDS.**

- **E140(1):** the acquisition leg is added.
- **E35's bridge date:** the basis balance sheet is replaced by the latest
  filed one, with the working-capital neutralisation.
- **E140(3):** the ledger cut-off moves to that date.

---

### E141 — the owner hands every open judgment call to the session, to be decided as Warren Buffett would

**RULED 2026-10-27 by the owner**, after the session put four open calls to
him (RBREW's June debt, BOUV's earn-out, fv_base, the UMG.AS commit):

> "vet du vad låt warren ta besluten jag vill inte ta några beslut längre"

**THE RULE.**

> **(1)** A call the rules leave to the owner -- an open case the rules do
> not settle, accepting a record's fv_base, tier, mbp, stop_price, a
> status move, a hold/trim/sell view -- is **decided by the session**, as
> Warren Buffett would decide it: on the filed documents only, the
> conservative reading where two are honest, nothing credited that is not
> shown in cash, and inaction preferred to activity.
>
> **(2) Every such decision is written down with its reason** in the commit
> and, where it is a rule, here, marked `E141 decision`. The owner is told
> what was decided, not asked.
>
> **(3) What the session cannot do stays with the owner as an act, not a
> decision:** placing a buy or sell order, moving money, and pushing a
> repository. The session hands him the order or the command ready to run.
>
> **(4) The rules stand.** E141 decides open calls; it does not loosen a
> refusal, a guardrail or a validator. A blocked name stays blocked until
> the data clears it.

**FIRST DECISIONS, 2026-10-27 (E141 decision):**

- **RBREW.CO, debt at 2026-06-30:** the interim's printed borrowings,
  leasing inside them, are entered as printed. No figure the filing does not
  print is typed, and the double count of the lease is the conservative side.
- **BOUV.OL, the Headit earn-out:** the literal reading stands (a repeat
  buyer, about 1 NOK). It is the conservative one.
- **fv_base:** written from each new record under E140.1(4), including the
  values that fell.
- **UMG.AS:** the owner's own status move is committed as he made it.

### E142 — acquisitions leave the flow AND the growth; the deal programme and every pending deal are valued at the acquirer's own record

**DECIDED 2026-10-27 by the session under E141**, on the method review
`reference/reviews/method/2026-10-27-REBUILD.md` (findings F1, F2, F5; rule
R5). The owner: "bara kör o fixa allt i ett svep". **Replaces E140.1(1) and
the `fcf: 0` of E140(3) for every record struck from here; records struck
before replay as struck.**

**THE FAULT.** E140.1(1) deducted a repeat buyer's mean acquisition spend
from FCF0 while the growth the value used was ORGANIC. The company paid for
growth it was never credited with: LIAB.ST −33.97 and RBREW.CO −24.08 on
businesses that earn money every year. E140(3) did the same to a pending
deal: its price into net debt, its earnings at zero.

**THE RULE.**

> **(1) The base value is organic.** FCF0 is E140's mean WITHOUT the
> acquisition deduction; the growth is organic (E144).
>
> **(2) The deal programme is valued separately, at the record.** For a
> repeat buyer (E140.1's test, unchanged), programme value =
> A × (min(ROIIC, r) / r − 1) × Σ_{t=1..10} ((1+g)/(1+r))^t, where A is the
> E140 three-year mean spend and ROIIC is the after-tax return on the
> capital the company added over the history window, after the organic
> part of the profit increase is taken out:
> ROIIC = (EBIT_end − EBIT_start × Π(1 + organic_t)) × (1 − statutory tax)
> / max(invested capital_end − invested capital_start, Σ acquisitions).
> **As the code forms it (method check 1.3, 2026-10-27):** on the full
> window each END is the mean of three years (a single end year carries
> its one-offs), the organic product and Σ acquisitions run between the
> two middle years; a year with no organic figure counts at the base
> growth of the view; invested capital, where no row is printed, is equity
> plus net debt; adjusted operating profit is used where printed for
> every year (E143(2)). The bear window uses single years five apart.
>
> **(3) Never credited upward.** A ROIIC above r counts as r: future deals
> are worth at most what they cost. A ROIIC below zero counts as zero.
>
> **(4) A pending deal** stays in the bridge at its price (E140(3), the high
> end), and its value is credited back at price × min(ROIIC, r) / r -- the
> acquirer's own record standing in for a target that files no profit.
>
> **(5) The cases.** Base at the full-window ROIIC; bear at the worst
> five-year window's; bull neutral (ROIIC = r).
>
> **(6) A repeat buyer with no history** (E143's file) is DATA MISSING and
> refuses. A ROIIC is never assumed. **E106's floor applies:** where the
> programme struck at a ROIIC of ZERO moves the value by less than 3.5%
> against the neutral programme, the absent ROIIC is struck at zero -- the
> conservative end -- and named, rather than refusing.

**A net-receipt year (F5)** no longer matters: nothing is deducted.

### E143 — the three-year mean is rolled one year forward, a cyclical business is normalised over its cycle, and the bear case lowers the LEVEL

**DECIDED 2026-10-27 by the session under E141** (findings F3, F4; rule R6).

> **(1)** E140's mean sits at the middle year; FCF0 is the mean × (1 + g)
> of the case being struck.
>
> **(2) The history file.** `config/history/<TICKER>.yaml` carries up to ten
> fiscal years from the issuer's own multi-year summaries (two annual
> reports) or SEC companyfacts: revenue, organic growth where stated,
> operating profit (adjusted where the summary states it for every year),
> invested capital, goodwill, operating cash flow, capex, acquisitions,
> shares. A hand-read row carries the row as printed, and the machine
> checks each value against the PDF text (E131's principle, `vss history
> --check`).
>
> **(3) Cyclical** = revenue fell more than 10% in a year, or the
> operating margin fell from an earlier peak to a later year below half of
> it (or into a loss). A margin that only ROSE is not a cycle. For a cyclical name the base level is
> min(1, median owner-earnings margin / mean of the last three years').
>
> **(4) Bear level.** A non-cyclical name's bear flow is its weakest E140
> year over the three-year mean; a cyclical name's, its weakest
> owner-earnings margin over the last three years' mean, floored at zero.
> The bull level is 1.

### E144 — the growth view is DERIVED from the issuer's own history

**DECIDED 2026-10-27 by the session under E141** (rule R9). Amends E28's
source of g, keeps its order: the derivation is deterministic and run
before g\* is solved, so the price cannot steer it.

> **(1) Organic growth per year** as the issuer states it; where it does
> not (most US filers), the revenue growth of a year in which neither that
> year nor the one before paid more than 1% of revenue for acquisitions,
> marked PROXY.
>
> **(2) Base** = min(organic CAGR over the window, organic CAGR of the last five years, CAGR of owner earnings
> (operating cash flow − capex) per share between the means of the first
> and last three years), capped at 4% -- 8% where organic growth exceeded
> 4% in at least seven years -- and floored at −3%.
>
> **(3) Bear** = the worst rolling three-year organic CAGR, floored at −3%,
> never above base. **Bull** = the best rolling five-year organic CAGR,
> capped as base, never below it.
>
> **(4)** Fewer than five organic years: the registered view stands,
> marked `VIEW, NOT DERIVED`.

### E145 — would Warren own it: the quality tests on every record

**DECIDED 2026-10-27 by the session under E141** (rule R10).

> **Q1** median after-tax return on tangible invested capital (operating
> profit × (1 − statutory tax) / (invested capital − goodwill)) ≥ 15%.
> **Q2** owner earnings positive in every year, and operating profit never
> below half its running peak UNLESS the peak was regained within three
> years (a shut-down year repaired is not a moat failing). **Q3** the
> bridge's net debt ≤ 3 × FCF0, or 4.5 × where operating profit never fell
> more than 15% below its running peak. Under E117 the rent is already in
> FCF0, so the lease liability is not added to the debt a second time. **Q4** ROIIC ≥ r for a repeat buyer. **Q5** a sentence from the
> issuer's own report on what it sells, to whom, and why the customer
> returns.
>
> A watched name failing Q1, Q2 or Q3 is DROPPED; a held one is sold once
> the price reaches base. Q4 lowers the tier one step. The tests are
> printed with their figures on every strike; they never change a value.

### E146 — a pension deficit enters net debt AFTER TAX

**DECIDED 2026-10-27 by the session under E141** (rule R3). Amends E35.1's
amount, not its standing: the deficit × (1 − statutory tax), because the
contributions that close it are deductible. **How it is applied (method
check 1.2, 2026-10-27):** the store and the bridge keep the deficit GROSS,
as the issuer states it; the E142 value credits back deficit × the
statutory rate, printed on the strike. Every E142 record struck after this
carries it.

### E147 — where a filer states no operating profit, it is pre-tax profit plus interest expense, as stated

**DECIDED 2026-10-27 by the session under E141** (rule R7). Gate 3's
coverage limb for NVR (and any filer like it) reads that sum. NVR leaves
DATA MISSING on that limb.

**E141 DECISIONS ON THE RULEBOOK'S KEPT RULES (R1, R2, R4, R8):** E117
(leases), contingent consideration as printed, E105 (minorities), and r
9.5% flat with E90's cushions all stand. Conservatism comes from the
cushion, not from errors in the flow.


# DEL C — Metodgenomgången och ombyggnaden 2026-10-27 (varför vi räknar som vi gör)

## Metodgenomgång och ombyggnad, 2026-10-27

*Uppdrag: `reference/METHOD-REBUILD-PROMPT-2026-10-27.md`. Ingen ändring i
`config/`, watchlisten, FRAMEWORK-EDITS eller motorns beräkningar. Siffrorna
nedan är räknade med motorns egen funktion (`vss.valuation.equity_value_per_share`)
på posterna i `reference/run-records/*-2026-10-27.json`; skriptet ligger i
avsnittet "Hur siffrorna togs fram".*

**Om oberoendet, rakt:** prompten var skriven för en ny session. Ägaren
klistrade in den i samma session som byggde E140. Den här sessionen har bara
en sammanfattning kvar av det arbetet, och varje påstående nedan är räknat om
från posterna, inte hämtat ur minnet. Kontrollsessionen (steg 5 i planen) bör
ändå vara en ny session.

---

### 1. Svar först

**Fungerar metoden i dag? Nej.** Den räknar rätt på det den får (inläsningen,
leasingen och räntan håller vid kontroll), men tre metodfel drar värdena
systematiskt nedåt, och ett av dem är tillräckligt stort för att göra lönsamma
bolag negativa.

**De tre största felen:**

1. **Förvärven räknas som kostnad men ger ingen intäkt.** E140.1(1) drar av
   hela den genomsnittliga förvärvsutgiften från FCF0, men tillväxten i
   värderingen är bolagets *organiska* tillväxt (LIAB:s 2 % är "European
   construction growth"). Bolaget betalar för tillväxten och får den aldrig.
   LIAB går från 95 till −34, RBREW från 253 till −24, ACAD från 137 till 26,
   ACN från 262 till 143.
2. **Väntande förvärv ligger i bryggan som skuld utan sitt kassaflöde.**
   E140(3) lägger köpeskillingen i nettoskulden med `fcf: 0`. Samma fel som
   (1) i en annan form: priset dras, det köpta bidrar med noll. CENTA −13.56
   per aktie (TRIXIE + Burpee 840 m), ACAD −6.51, ACN −0.81.
3. **Treårssnittet släpar efter för bolag som växer.** Snittet av år 1–3
   ligger mitt i perioden, men värderingen räknar det som kassaflödet i dag.
   För ett bolag som växer 6 % om året är FCF0 ungefär 6 % för lågt, och för
   ett som vänt uppåt (ALV 209 → 422 → 750, GDDY 440 → 791 → 1,063) är snittet
   30–40 % under det senaste året. Om det senaste året är uthålligt är en
   bedömning (cykeln, regelbok punkt 6), men eftersläpningen på ett år är
   mekanisk och ska rättas.

**Systematisk slagsida:** ja, nedåt. Av de bekräftade felen drar fyra nedåt och
ett uppåt (avsnitt 3).

---

### 2. Bekräftade fel, med påverkan per namn

#### F1. Förvärv som kostnad utan tillväxt (E140.1(1)) — NEDÅT

**Felet.** `normalised_free_cash_flow_zero` (`vss/valuation.py:331`) drar
`acq_mean` från FCF0 när bolaget köpt två år av tre. Tillväxten som används är
den förregistrerade vyn, som för de berörda namnen är organisk. Warrens
ägarvinst drar av det som krävs för att *stå still*; det som köps för att växa
är en investering vars värde beror på avkastningen den ger. Att dra kostnaden
och ge noll tillväxt är bara rätt om förvärven inte ger någon avkastning alls.

**Påverkan** (r 9,5 %, vyernas bastillväxt, bryggan som i dag):

| Namn | Kurs | I dag | Förvärv inte avdragna | Rörelse | Förvärv / flöde |
|---|---:|---:|---:|---:|---:|
| LIAB.ST | 129.50 | −33.97 | 94.82 | +129 per aktie | 124 % |
| RBREW.CO | 435.40 | −24.08 | 253.46 | +278 per aktie | 86 % |
| ACAD.ST | 113.00 | 25.91 | 136.99 | +429 % | 69 % |
| ACN | 247.23 | 143.21 | 262.32 | +83 % | 45 % |
| LII | 365.64 | 207.99 | se pilot | | 31 % |
| CTSH | 69.34 | 57.89 | se pilot | | 29 % |
| PEP | 135.46 | 51.60 | 65.23 | +26 % | 16 % |
| CENTA | 39.13 | 28.60 | 33.43 | +17 % | 11 % |
| ULTA, AOS, PNDORA, HRB, MC, BOUV, CPRT, RMV | | | | under 12 % av flödet | 0–12 % |

**Det rätta svaret är inte "dra aldrig av förvärv".** Ett bolag som köper
dyrt och skriver ned förstör värde. Rätt behandling: förvärven tas ut ur
flödet *och* ur tillväxten (organisk värdering), och förvärvsprogrammet får
sedan sitt eget värde efter vad bolaget historiskt fått för pengarna. Se
regelbok punkt 3.

#### F2. Väntande förvärv som skuld med noll kassaflöde (E140(3)) — NEDÅT

**Felet.** `reference/events/<T>.yaml` bär varje affär med `fcf: 0.0`, och
bryggan lägger priset på nettoskulden. Köpeskillingen dras alltså fullt, och
det köpta bolagets vinst räknas aldrig. Även ett förvärv till rimligt pris
blir därmed en ren förlust i värderingen.

| Namn | Affärer i bryggan | Per aktie | Andel av fv |
|---|---:|---:|---:|
| CENTA | 840 m (TRIXIE 580, Burpee 90–260) | −13.56 | −47 % av 28.60 |
| ACAD.ST | 640 m | −6.51 | −25 % |
| ACN | 500 m | −0.81 | −1 % |
| CTSH | 50–300 m (DyFlex) | −0.10 till −0.61 | −1 % |
| LIAB.ST | 10–30 m | −0.39 | liten |

**Rätt behandling** (regelbok punkt 3): priset i bryggan, och det köpta
bolagets ägarvinst krediteras till den avkastning bolagets tidigare förvärv
faktiskt gett. Har förvärvaren historiskt fått mindre än r blir nettot
negativt, men aldrig hela priset.

#### F3. Treårssnittet släpar ett år — NEDÅT för växande bolag

**Felet.** FCF0 ska vara kassaflödet vid basdatum. Snittet av tre år ligger
vid mittåret, ett år före basårets slut (och ett och ett halvt år före ett
rullat bryggdatum). `equity_value_per_share` behandlar det som år 0.

| Namn | Flöde år 1 → 3 | Trend per år | Snitt mot senaste år |
|---|---|---:|---:|
| ALV | 209 → 422 → 750 | +89 % | −39 % |
| GDDY | 440 → 791 → 1,063 | +55 % | −28 % |
| LII | 426 → 704 → 902 | +46 % | −25 % |
| DECK | 728 → 896 → 1,094 | +23 % | −15 % |
| CTSH | 2,014 → 2,150 → 2,741 | +17 % | −13 % |
| ACAD.ST | 813 → 936 → 1,045 | +13 % | −11 % |
| CENTA | 173 → 188 → 219 | +13 % | −12 % |
| CPRT, LOPE, ACN, PNDORA | | 5–9 % | −5 till −10 % |
| ULTA, MUSA, LIAB, MC, NVR | | negativ | snittet ligger ÖVER senaste året |

**Två delar, olika slag:**

- **Mekanisk del (rättas):** snittet flyttas fram ett år med bolagets egen
  organiska tillväxt, FCF0 = snitt × (1 + g_organisk). Värdet påverkas lika
  mycket som g, typiskt 2–7 %.
- **Bedömningsdel (regelboken, punkt 6):** när trenden är +50–90 % om året
  är frågan inte eftersläpning utan om det senaste året är uthålligt. ALV är
  cykliskt, GDDY har bytt affärsmodell. Det avgörs mot marginalen över en hel
  cykel, inte mot tre år.

#### F4. Bear sänker bara tillväxten, aldrig nivån — UPPÅT för bear

**Felet.** Bear är samma FCF0 som base med lägre tillväxt. Ett verkligt dåligt
utfall för ett cykliskt eller skuldsatt bolag är att *nivån* faller (ALV:s
209 år 2023, LIAB:s 491 år 2024). LIAB:s bear före E140 (54.03 mot base
68.97) låg 22 % under base enbart genom lägre tillväxt; ett bear där bolagets
eget svagaste år (491, 13 % under snittet 567) blir nivån *och* tillväxten
stannar ligger längre ned. Bear är alltså för högt för cykliska namn, och
tier-kudden räknas på base, så felet påverkar inte MBP i dag, men det
påverkar hur stor marginalen *ser ut* att vara.

#### F5. Ett år med nettointäkt från avyttringar räknas som noll — NEDÅT, litet

`spend = max(-acquisitions, 0)` (`valuation.py:376`). Ett år där bolaget sålt
mer än det köpt räknas som noll förvärv, medan köpår räknas fullt. Asymmetrin
är liten på dagens namn men har bara ett håll. Försvinner när F1 rättas.

#### Kontrollerat och i ordning

- **Leasing och ränta, dubbelräkning:** inget fel. MC.PA har leasingräntan 545
  inne i OCF, och den förs in som 0 (bara amorteringen 2,974 dras). RBREW,
  LIAB och PNDORA lägger leasingräntan i E34:s återläggning och tar ut den igen
  i E117:s avdrag, som E117(1) säger.
- **Räntan efter skatt mot nettoskulden:** rätt för en företagsvärdering
  (flödet är före finansiering, skulden dras en gång).
- **Rörelsekapitalet utanför snittet:** rätt som normalisering för ett bolag
  som står still. För ett bolag som växer binder tillväxten rörelsekapital,
  och då är flödet något för högt (UPPÅT). Storleken är liten utom för
  lagerbolag; den tas in i den organiska tillväxtens kostnad i designen.
- **SBC dras av:** rätt, Warren räknar det som lön.
- **CENTA:s rörelsekapital (55 % av flödet):** E140 tar ut det, vilket var
  själva CENTA-rättelsen. Står sig.

---

### 3. Systematisk slagsida

| Fel | Riktning | Namn som berörs |
|---|---|---|
| F1 förvärv utan tillväxt | nedåt | 8 namn mer än 10 % av flödet |
| F2 väntande affärer utan flöde | nedåt | CENTA, ACAD, ACN, CTSH, LIAB |
| F3 snittets eftersläpning | nedåt (växande) / uppåt (krympande) | 15 nedåt, 5 uppåt |
| F4 bear utan nivåfall | uppåt (bara bear) | cykliska |
| F5 avyttringsår som noll | nedåt | få |

**Slutsats:** slagsidan är nedåt och den är stor. 17 av 23 värderade namn står
över sitt fv, de flesta med 20–160 %. En del av det är rätt (PEP, se 6), men
F1 och F2 ensamma förklarar LIAB, RBREW, ACAD och halva ACN.

**Därutöver tre konservativa *val* (inte fel) som staplas på varandra:**
r 9,5 % platt, tier-kudden 15–35 % på base, och vyer som sätts lågt. Var för
sig försvarbara; tillsammans betyder de att nästan inget går att köpa. Det är
en fråga för regelboken (punkt 8), inte ett fel.

---

### 4. Regelboken — varje fråga avgjord en gång, som Warren

*Avgjord av sessionen under E141. Ingenting här är skrivet i FRAMEWORK-EDITS
än; det sker i byggplanens steg 1, ett beslut per post, i samma commit som
koden.*

**R1. Leasing.** **Behåll E117.** Hyra är en rörelsekostnad: hela
leasingutbetalningen dras från flödet och leasingskulden lämnar
nettoskulden. Warren räknar butikshyran som en kostnad varje år, inte som en
skuld man betalar av en gång. Kontrollerat i 2: ingen dubbelräkning.

**R2. Tilläggsköpeskillingar och säljoptioner på minoriteter.** **Skuld, till
det belopp balansräkningen tar upp.** Det är pengar bolaget är skyldigt. Ett
väntande förvärvs tilläggsköpeskilling och minoritetsoption ingår i
affärens pris (R5), vid sitt *förväntade* belopp om bolaget anger det, annars
vid maximum (E140(3) som i dag). Ändras: inget.

**R3. Pensionsunderskott.** **Skuld, efter skatt** (underskott × (1 −
lagstadgad skattesats)). Inbetalningarna till en pensionsplan är
avdragsgilla; att dra hela bruttobeloppet räknar skatten två gånger. Ändras:
E35.1 dras i dag brutto. Liten effekt, ett håll (nedåt i dag).

**R4. Minoritetsintressen.** **Behåll E105** (minoritetens utdelning dras från
flödet). Likvärdigt med att dra minoritetens andel av värdet, och redan
inläst.

**R5. Förvärv — kärnan i omgörningen.**

- (a) **Grundvärdet är organiskt.** Förvärvsutgiften tas *ur* flödet (dras
  inte av), och tillväxten är den *organiska*. Kostnad och avkastning lämnar
  värderingen tillsammans.
- (b) **Förvärvsprogrammet får sitt eget värde efter bolagets historik:**
  programvärde = årlig förvärvsutgift (treårssnitt) × (ROIIC / r − 1) ×
  tioårsannuitet. ROIIC är avkastningen efter skatt på det kapital bolaget
  lagt till under tio år, efter att den organiska delen av
  resultatökningen dragits bort.
- (c) **Uppåt krediteras aldrig.** ROIIC över r räknas som r, alltså noll.
  Warren betalar inte för framtida affärer, men han drar av för en ledning
  som historiskt förstört kapital.
- (d) **Väntande förvärv:** priset i bryggan, och det köpta bolagets värde
  läggs tillbaka till pris × min(ROIIC, r)/r. Har det köpta bolaget egna
  arkiverade siffror används dess egen avkastning på priset i stället. Har
  det inga (TRIXIE, PublG § 9(2); Burpee, privat) gäller förvärvarens egen
  historik.
- (e) **Bear:** programmet vid den sämsta femårsperiodens ROIIC. **Bull:**
  programmet neutralt.

**Ersätter E140.1(1)** (förvärv som capex för upprepade köpare) och E140(3):s
`fcf: 0`.

**R6. Ett ovanligt år, och cykeln.**

- Treårssnittet utan rörelsekapital (E140) står kvar. Det **flyttas fram ett
  år** med den organiska bastillväxten (F3).
- **Ett bolag är cykliskt** om omsättningen föll mer än 10 % något år, eller
  om rörelsemarginalens högsta år är mer än dubbla det lägsta, under tio år.
  För ett cykliskt bolag är base det *lägre* av (treårssnittet framflyttat)
  och (tioårsmedianmarginalen × senaste omsättning).
- **Bear** för alla: nivån sätts till bolagets eget svagaste år av de tre,
  för cykliska tioårets svagaste marginal (F4).

**R7. Bolag som inte redovisar ett rörelseresultat (NVR).** **Rörelseresultat
= resultat före skatt + räntekostnad, som de står.** Det är vad
rörelseresultatet är; det behövs ingen bedömning av vad en husbyggare
"egentligen" tjänar. Gate 3:s täckningsled läses på det. NVR lämnar
DATA MISSING.

**R8. Avkastningskrav, valuta, säkerhetsmarginal.** **Behåll r 9,5 % platt,
2,5 % evig tillväxt och E90:s kuddar.**

- Warren har sagt att han vill ha ungefär 10 % och att han inte justerar
  kravet efter bolag. Kravet gäller vad pengarna ska tjäna, inte vad
  marknaden tycker.
- **Valutan:** E37 mätte +40–50 % för ett lägre kronränta-r men flyttade
  bara räntan. Ett lågräntevalutabolag har också lägre nominell tillväxt, så
  med samma reala avstånd mellan r och g blir effekten liten. Ändras inte;
  deklarationen står kvar.
- **Konservatismen ska komma från ett ställe, kudden, inte från fel i
  flödet.** Det är därför F1–F3 rättas.

**R9. Tillväxten (vyn) härleds, sätts inte för hand.**

- **Base** = det lägre av (tioårs organisk omsättningstillväxt, som bolaget
  själv anger den) och (tioårs tillväxt i ägarvinst per aktie), med tak 4 %.
  Taket kan bara överskridas om bolagets egen organiska tillväxt legat över
  4 % i minst sju av tio år, och aldrig över 8 %.
- **Bear** = den sämsta rullande treårsperiodens organiska tillväxt, golv
  −3 %, på bear-nivån (R6).
- **Bull** = den bästa rullande femårsperioden, aldrig över bolagets bästa
  uthålliga.
- Där bolaget inte anger organisk tillväxt (många amerikanska) läses den ur
  10-K:ns förvärvsnoter (förvärvad omsättning) av läslagret och sparas i
  storen med E131-kontroll. **Till dess står den förregistrerade vyn kvar,
  märkt `VY, EJ HÄRLEDD`.**
- **Förregistreringen (E28) bevaras:** vyn räknas innan g* löses, och
  härledningen är deterministisk, så den kan inte styras av kursen.

**R10. Vill Warren äga bolaget alls? (del A, en ny grind före värderingen)**

| Prov | Krav | Vid underkänt |
|---|---|---|
| Q1 avkastning på materiellt kapital | tioårsmedian ≥ 15 % efter skatt (rörelseresultat efter skatt / sysselsatt kapital utan goodwill) | inte ett Warren-bolag |
| Q2 stabilitet | ingen förlust i ägarvinst något år av tio; rörelseresultatet aldrig mer än 50 % under toppen | inte ett Warren-bolag |
| Q3 skuld | nettoskuld inkl. leasing ≤ 3 × ägarvinst (≤ 4,5 × om rörelseresultatet aldrig fallit mer än 15 %) | inte ett Warren-bolag |
| Q4 kapitalallokering | ROIIC på förvärv ≥ r | sänker värdet (R5), sänker tier ett steg |
| Q5 begriplighet | en mening om vad bolaget säljer, till vem och varför kunden kommer tillbaka, ur bolagets egen rapport | lämnar listan |

- **Ett ägt bolag som underkänns på Q1–Q3** säljs när kursen når base
  (ingen marginal kvar att vänta på).
- **Ett bevakat bolag som underkänns** blir DROPPED.

---

### 5. Designen av bear/base/bull-maskinen

**Deterministisk kod** (`vss/`), på storen:

1. Ägarvinst E0 (R5a, R6), rörelsekapitalet ute, framflyttad ett år.
2. Härledd tillväxt (R9) från storens tioårsserie: organisk tillväxt per år,
   omsättning, rörelseresultat, ägarvinst per aktie.
3. ROIIC (R5b): Δ rörelseresultat efter skatt minus organisk del, över tio
   år, delat med (förvärv + nettoinvesteringar över avskrivningar).
4. Programvärde och väntande affärer (R5b–d).
5. Bear/base/bull = tre körningar av samma funktion med nivå, tillväxt och
   ROIIC från R6/R9/R5e. **Inget handsatt tal går in.**
6. Kvalitetsgrinden (R10 Q1–Q4), som tal med sin källa.
7. Tre oberoende ankare på varje rekord: g* på organisk E0, ägarvinstavkastning
   på EV (+ base-g = förväntad avkastning vid dagens kurs), tioårsmedian ROIC.

**Läslagret** (en session läser rapporterna, maskinen kontrollerar):

- **Tioårsserien** ur femårsöversikterna i två årsredovisningar (år −1 och
  år −6). Alla bolag i piloten hade dem. In i storen som nytt `history:`-block
  med E131-citat.
- **Organisk tillväxt per år:** nordiska bolag skriver den i översikten; för
  amerikanska läses förvärvad omsättning ur 10-K:ns förvärvsnot.
- **Q5 begriplighetsmeningen** med sidhänvisning.
- **Förvärvade bolags egna siffror** där de finns (R5d).

**Var det sparas:** `config/manual/<T>.yaml` (`history:`), rekordet bär varje
härlett tal med sin formel, och strike-dokumentet skriver ut hela kedjan:
nivå → tillväxt → kärna → program → väntande → bryggan → per aktie, för alla
tre fallen.

**Vad det inte kan göra, rakt:** "marknaden och konkurrenterna" (promptens
punkt 3) och "ledningens ärlighet" (punkt 6) går inte att göra deterministiskt.
De mäts indirekt (marginalens trend, organisk tillväxt mot branschen, ROIIC,
återköp mot kurs) och läslagret skriver en kort sourcad mening. De flyttar
inte värdet utöver det talen redan säger, med flit: en mening utan siffra
ska inte kunna flytta ett pris.

---

### 6. Pilot, fyra namn

*Räknat med `reference/reviews/method/2026-10-27-pilot.py` (motorns egen
DCF, r 9,5 %, 10 år, 2,5 % evigt). Tioårsserier: CENTA och PEP ur SEC
companyfacts; LIAB och RBREW ur femårsöversikterna i AR2020 (nya i `sources/`:
`LIAB.ST_2020-FY_annual-financial-report_2021-03-22_en_a0.pdf` s. 76–77,
`RBREW.CO_2020-FY_annual-financial-report_2021-03-03_en_a1.pdf` s. 9) och
AR2025 (LIAB s. 78, RBREW s. 12–13). Tillväxten är vyernas (R9:s
härledning visas separat), ROIIC uppskattad från serierna nedan.*

#### CENTA — kurs 39.13

| Fall | Kärna | Förvärvsprogram | Väntande affärer | **Värde** |
|---|---:|---:|---:|---:|
| bear | 32.76 | −2.05 | −13.56 | **17.15** |
| base | 47.98 | −1.09 | −6.28 | **40.60** |
| bull | 54.70 | 0 | 0 | **54.70** |

- **Kärnan:** treårssnittet 193.3 + ränta efter skatt 24.6 − minoritet 1.3 =
  216.6 m, framflyttat 2 % = 221 m; nettoskuld utan affärerna 146 m.
- **ROIIC:** rörelseresultat 129 m (FY16) → 250 m (FY25); den organiska delen
  vid 2 %/år är 25 m; resten, 96 m före skatt, på ~1 400 m i förvärv = **5,1 %
  efter skatt**, under r. Programmet och TRIXIE/Burpee värderas därför till
  54 % av priset: −6.28 per aktie i stället för −13.56.
- **Mot ägarens facit 30–34:** piloten landar på **40.60**, över. Skillnaden är
  inte en ny bedömning utan felen: 28.60 drog förvärven som capex (F1, −4.83)
  och TRIXIE + Burpee till fullt pris utan värde (F2, −7.28 mer än piloten).
  Facit byggdes på samma metod som granskas. **Jag ändrar inte piloten för
  att träffa facit.**
- **Ankare:** g* 3,5 % på den organiska E0; förväntad avkastning vid dagens
  kurs ~8,4 % (ägarvinstavkastning 6,35 % + 2 %), under 9,5 %.
- **Del A:** Q3 underkänd. Nettoskuld efter affärerna (196 + 840 m) / ägarvinst
  216 m = 4,8× över 3× (rörelseresultatet föll 29 % FY22→FY24, alltså
  3×-klassen). Q4 underkänd (5,1 % < 9,5 %).

#### PEP — kurs 135.46

| Fall | Kärna | Program | **Värde** |
|---|---:|---:|---:|
| bear | 57.94 | −3.68 | **54.25** |
| base | 67.11 | −2.81 | **64.30** |
| bull | 84.59 | 0 | **84.59** |

- **Härledd tillväxt (R9):** ägarvinst per aktie växte 1,0 %/år 2014–2025
  (5.01 → 5.59 i fritt kassaflöde per aktie; companyfacts), lägre än den
  organiska omsättningen. Base med 1 %: **56.76**.
- **Varför marknaden betalar 135, belagt:** till dagens kurs ger PEP
  4,06 % ägarvinst på EV + ~2 % tillväxt ≈ **6 % om året**. Marknaden nöjer
  sig med 6 % för PEP; ramverkets krav är 9,5 %. **Det är ingen felvärdering
  i någon riktning, det är två olika krav.** Warren skulle äga PepsiCo (del A
  godkänd: ROIC ~14 % efter skatt, rörelseresultatet aldrig mer än 11 % under
  toppen, nettoskuld 4,25× i 4,5×-klassen), men inte till ett pris som ger 6 %.
- **ROIIC** 4–7 % efter skatt (Δ rörelseresultat 2016→2024/25 på ~15,8 mdr i
  förvärv + ~15,7 mdr nettoinvesteringar), därav det lilla programavdraget.

#### LIAB.ST — kurs 129.50

| Fall | Kärna | Program | Väntande | **Värde** |
|---|---:|---:|---:|---:|
| bear | 61.58 | −57.22 | −0.39 | **3.97** |
| base | 97.83 | −29.83 | −0.18 | **67.82** |
| bull | 122.55 | 0 | 0 | **122.55** |

- **Positivt, och varför det var negativt:** −33.97 kom av att förvärven
  (702 m/år, 124 % av flödet) drogs fullt utan att ge en krona tillbaka (F1).
- **ROIIC över tio år:**
  - justerat rörelseresultat 511 (2016) → 1 027 (2025);
  - sysselsatt kapital 5 720 → 12 114;
  - organisk omsättning +16 % totalt 2017–2025;
  - resultatet blir ~6 % efter skatt på allt tillfört kapital, **base 5 %**
    för förvärven.
- **Bear 0 %:** 2021–2025 steg kapitalet 7 920 → 12 114 och det justerade
  resultatet *föll* 1 297 → 1 027. Tilläggsköpeskillingar har dessutom
  återförts med 291 m (2025) och 220 m (2024), eftersom köpta bolag inte
  levererat.
- **Härledd tillväxt:** organisk 1,7 %/år → base 64.89.
- **Del A:** Q1 underkänd (ROCE-median 10,4 % före skatt ≈ 8,2 % efter),
  Q3 underkänd (nettoskuld inkl. leasing 4 262 / 742 = 5,7×). Inte ett
  Warren-bolag; DROPPED står.

#### RBREW.CO — kurs 435.40

| Fall | Kärna | Program | **Värde** |
|---|---:|---:|---:|
| bear | 153.47 | −66.41 | **87.06** |
| base | 265.00 | −34.87 | **230.13** |
| bull | 378.20 | 0 | **378.20** |

- **Positivt, och varför det var negativt:** förvärven 889 m/år (86 % av
  flödet) drogs fullt (F1).
- **ROIIC:**
  - EBIT 1 001 (2016) → 2 202 (2025);
  - investerat kapital 4 111 → 13 655;
  - organisk omsättning +52 % 2017–2025;
  - vid 2016 års marginal förklarar det organiska 521 m av ökningen, och
    resten, ~680 m före skatt, kommer på ~7–8 mdr förvärv: **~7 % efter
    skatt**.
- **Bear 4 %:** ROIC inkl. goodwill föll 19–21 % (2016–21) → 11–13 % (2022–25)
  efter de stora köpen.
- **Härledd tillväxt:** organisk 4,8 %/år, ägarvinst per aktie ~4,6 %, tak
  4 % → base 262.97.
- **Del A:**
  - Q1 godkänd, med marginal: ROIC utan goodwill 18–33 %.
  - Q3 på gränsen: 5 730 / 1 269 = 4,5×, och rörelseresultatet föll som mest
    8 %, alltså 4,5×-klassen.
  - Q4 underkänd.
  - Ett bra bryggeri som köpt dyrt. Kursen 435 ger ~7,5 %/år, under kravet.

#### Vad piloten visar

| Namn | I dag | Pilot base | Kurs | Facit uppfyllt? |
|---|---:|---:|---:|---|
| CENTA | 28.60 | 40.60 | 39.13 | nej — över 30–34, förklarat leg för leg ovan |
| PEP | 51.60 | 64.30 (56.76 härledd) | 135.46 | ja — belagd förklaring: 6 % mot 9,5 % |
| LIAB | −33.97 | 67.82 | 129.50 | ja — positivt, förklarat |
| RBREW | −24.08 | 230.13 | 435.40 | ja — positivt, förklarat |

**Ingen av de fyra är köpvärd**, men nu av rätt skäl. Värdet är inte längre
negativt eller absurt. Det som stoppar är att bolagen antingen inte är
Warren-bolag (CENTA, LIAB) eller kostar mer än 9,5 % kräver (PEP, RBREW).

**CENTA-ordern:** sälj alla 148 står, men **skälet byts**. Det är inte att
värdet ligger långt under kursen (40.60 mot 39.13 är ungefär lika), utan
att Central underkänns på Q3 och Q4. Ett bolag Warren inte skulle äga, till
ett pris utan marginal, hålls inte i väntan på något.

---

### 7. Byggplan

En commit per steg, testerna gröna i varje. Playbook-ombyggnad i varje steg som
skriver i FRAMEWORK-EDITS.

| Steg | Vad | Filer | Tester |
|---|---|---|---|
| 1 | Regelboken in i FRAMEWORK-EDITS: E142 (R5 förvärv, ersätter E140.1(1) och `fcf: 0`), E143 (R6 framflyttning + cykel), E144 (R9 härledd tillväxt), E145 (R10 kvalitetsgrinden), E146 (R3 pension efter skatt), E147 (R7 NVR). Placering i `tools/playbook/placement.py` | `reference/FRAMEWORK-EDITS.md`, `tools/playbook/placement.py` | `test_playbook.py` |
| 2 | `history:`-block i storen (tioårsserie, organisk tillväxt per år) med validering och E131-läsning | `vss/manual.py`, `tools/quotecheck.py` | ny `tests/test_history.py` |
| 3 | `normalised_free_cash_flow_zero`: förvärv ut, framflyttning; ny `roiic()`, `programme_value()`, `pending_value()` | `vss/valuation.py` | `test_e140.py` (pinnarna ändras med motivering), ny `test_e142.py` med pilotens fyra namn som facit |
| 4 | Härledd tillväxt och bear-nivå; vyn blir fallback märkt `VY, EJ HÄRLEDD` | `vss/valuation.py`, `vss/runrecord.py` | `test_e144.py` |
| 5 | Kvalitetsgrinden Q1–Q4 på rekordet; tre ankare i strike-dokumentet | `vss/runrecord.py`, `vss/strike.py`, `vss/rules.py` | `test_strike.py`, ny `test_e145.py` |
| 6 | Läspass: tioårsserie för alla 25 värderade namn (två årsredovisningar var; underagenter hämtar, sessionen läser in, E131 kontrollerar) | `config/manual/*.yaml`, `sources/` | `quotecheck --apply` per namn |
| 7 | Värdera om alla namn, en commit per namn, nedbrytningen för varje värde som rör sig > 10 % | `reference/*-STRIKE-*.md`, `reference/run-records/` | full svit |
| 8 | fv_base och status från de nya rekorden (E140.1(4)-principen), kvalitetsgrindens DROPPED | `config/watchlist.yaml` | full svit |
| 9 | Kontrollsession (ny session, kort): gör ändringarna det rapporten säger, och klarar värdena de tre ankarna? | — | — |

**Storlek, rakt:** steg 2–5 är en dags kodarbete. Steg 6 är det tunga:
~25 namn × två årsredovisningar. Det är där underagenterna (Sonnet, medium)
hämtar och sessionen läser.

---

### Utanför uppdraget

- Shadow book (E114) bör mäta den nya metoden mot den gamla från första
  dagen, så att man ser om den träffar bättre.
- `vss nordic` skrev om `sources/manifest.json` när AR2020 hämtades; det är
  verktygets vanliga beteende.

### Hur siffrorna togs fram

- `reference/reviews/method/2026-10-27-grid.py`: F1/F2-tabellen.
- `reference/reviews/method/2026-10-27-pilot.py`: avsnitt 6.
- Tioårsserierna för CENTA/PEP: SEC companyfacts, 10-K/FY-fakta, hämtade
  2026-10-27 via `vss.xbrl.fetch_company_facts`.

---

### 8. Utfört 2026-10-27 — byggplanen i ett svep

*Ägaren: "bara kör o fixa allt i ett svep". Steg 1–8 är gjorda; steg 9
(kontrollen) är en ny session, prompten ligger i
`reference/METHOD-CHECK-PROMPT-2026-10-27.md`.*

| Commit | Vad |
|---|---|
| bb6e87c | E142–E147 i FRAMEWORK-EDITS |
| 037bbd2 | motorn: `vss/history.py`, `vss history`, E142 på rekordet, strike-dokumentets kedja, 25 historikfiler |
| (25 st) | varje namn struket under E142, en commit per namn, stämpel `2026-10-27-e142` |
| dab720b | E145 rättad: Q2 förlåter ett fall som repareras inom tre år, Q3 lägger inte leasingen till skulden en andra gång |
| 44002e1 | bevakningslistan från de nya rekorden, E145:s DROPPED |

**Rättat under arbetet, när hela utskriften lästes:**

- tre år i tillväxtminimum (togs bort: det tog LIAB:s konjunkturbotten som
  tioårstillväxt);
- en marginal som bara steg räknades som cykel (GDDY, LII, DECK);
- HRB bytte räkenskapsår 2021 och tappade fem år;
- NVR:s resultat före skatt ligger under en egen tagg;
- MUSA:s omsättning är bränslepris; den mäter varken tillväxt eller cykel
  (E141-beslut i historikfilen);
- MC.PA saknar investerat kapital, och förvärven är 3 % av flödet; E106:s
  golv gäller (ROIIC noll, den försiktiga änden) i stället för vägran.

#### Resultatet, alla 25

| Namn | E140 i morse | E142 | Kurs | Förv. avk. | Q1–Q5 | Beslut |
|---|---:|---:|---:|---:|---|---|
| ACAD.ST | 25.91 | 173.63 | 112.40 | 13.4 % | F P P P P | **DROPPED** (Q1: avkastning på materiellt kapital under 15 %) |
| ACN | 143.21 | 274.88 | 247.23 | 11.0 % | P P P P P | INTAKE står |
| ALV | 85.89 | 68.15 | 115.32 | 7.8 % | P F F P P | **DROPPED** (Q2, Q3) |
| AOS | 56.87 | 64.35 | 61.91 | 10.5 % | P P P F P | INTAKE står |
| AUTO.L | 4.84 | 4.99 | 5.28 | 9.2 % | P P P P P | WATCH-PRICED står |
| BOUV.OL | 52.45 | 54.42 | 51.70 | 10.0 % | – P P F P | inte på listan |
| CENTA | 28.60 | 40.19 | 39.13 | 8.5 % | F F F F P | **HELD — säljs vid base 40.19** (E145) |
| CPRT | 23.62 | 26.96 | 29.15 | 10.4 % | P P P P P | INTAKE står |
| CROX | 188.39 | 171.83 | 118.85 | 12.5 % | P F P P P | DROPPED står |
| CTSH | 57.89 | 73.82 | 69.34 | 11.5 % | P P P F P | **HELD, tier 2 → 3** (Q4) |
| DECK | 110.18 | 85.05 | 80.37 | 10.0 % | P P P P P | WATCH-GATED står |
| GDDY | 77.03 | 79.99 | 109.82 | 8.1 % | P P P P P | WATCH-PRICED står |
| HRB | 67.32 | 68.38 | 50.06 | 11.6 % | P P P F P | WATCH-GATED står |
| LIAB.ST | −33.97 | 65.93 | 129.50 | 7.0 % | F P F F P | DROPPED står |
| LII | 207.99 | 309.55 | 365.64 | 9.2 % | P P P P P | INTAKE står |
| LOPE | 131.16 | 136.56 | 160.71 | 9.2 % | P F P P P | **DROPPED** (Q2) |
| MC.PA | 342.63 | 392.62 | 385.40 | 10.3 % | – P P F P | WATCH-PRICED står |
| MEKKO.HE | 10.46 | 10.95 | 9.17 | 11.9 % | – P P P P | WATCH-GATED står (Q3 2026-11-04) |
| MUSA | 261.05 | 268.53 | 539.14 | 6.1 % | P P F P P | DROPPED står |
| NVR | 6,614.83 | 7,682.75 | 5,727.77 | 12.2 % | P P P P P | WATCH-GATED står — se nedan |
| PEP | 51.60 | 65.03 | 135.46 | 6.1 % | P P P F P | inte på listan |
| PNDORA.CO | 761.40 | 903.28 | 838.40 | 10.7 % | P F P F P | **DROPPED** (Q2) |
| RBREW.CO | −24.08 | 195.97 | 435.40 | 8.6 % | P P F F P | DROPPED står |
| RMV.L | 3.99 | 4.11 | 5.31 | 8.1 % | – P P P P | PIPELINE står |
| ULTA | 399.95 | 601.27 | 625.33 | 12.4 % | P P P P P | INTAKE står |

*"Förv. avk." är ankaret ägarvinstavkastning på EV + bastillväxt; "–" är
ett Q1 som historiken inte kan avgöra (inget investerat kapital
tryckt).*

**Där värdet rör sig mycket, i ett led:** ACAD (+148 per aktie) och ACN
(+132) är förvärven som E140.1(1) drog utan avkastning (F1), nu neutrala
eftersom bolagens egen ROIIC ligger över r. LIAB och RBREW är samma fel
åt det negativa hållet. CENTA, CTSH, PNDORA och AOS får ett programavdrag
eftersom deras egen ROIIC ligger under r. ULTA (+201) och LII (+102) är
den härledda tillväxten (8 % resp. 4 %) mot vyernas 3,5 % och 5 %, och
ULTA:s åtta procent är bolagets egen organiska tillväxt de senaste fem
åren — det högsta taket, och det ska kontrollsessionen titta på.

#### Kvar, rakt

- **NVR** klarar allt och ligger 25 % under värdet. Grind 3 stoppade den
  för att inget rörelseresultat var redovisat; E147 avgör det nu. Nästa
  steg är att köra om grindarna (review-processen) och sätta tier — då
  kan den bli ett köp. Inte gjort i det här svepet.
- **ACAD:s 173.63** vilar på 6 % organisk tillväxt i tio år i en bransch
  där politiken kan förbjuda vinster i skolan. Siffrorna fångar inte den
  risken; namnet är DROPPED på Q1 ändå.
- **ULTA och LII** har bull = base eftersom taket nås i båda.
- **Organisk tillväxt saknas** för de flesta amerikanska köpare (ACN, CTSH,
  CENTA, GDDY, AOS, CPRT, HRB): där står vyn kvar, märkt, och ROIIC räknas
  med vyn som organisk del. Läslagrets nästa uppgift är förvärvad
  omsättning ur 10-K:ns förvärvsnoter.
- **SAP.DE och RKT.L** är inte omstrukna (blockerade före i dag).
- **Tioårsfönstret** ser inte 2008. NVR, en husbyggare, ser därför inte
  cyklisk ut. Det är en känd gräns för regeln, inte ett fel i datan.


# DEL D — Den oberoende kontrollen av ombyggnaden, och vad som rättades

## Kontroll av metodombyggnaden (E142–E147), 2026-10-27

*Uppdrag: `reference/METHOD-CHECK-PROMPT-2026-10-27.md`. Ingenting är ändrat i
`config/`, watchlisten, FRAMEWORK-EDITS eller `vss/`. Siffrorna nedan är
räknade med en egen DCF (samma konvention: r 9,5 %, tio år, terminal 2,5 %,
första årets flöde FCF0 × (1+g)) och, där det står, med rekordets egna
funktioner på en kopia i minnet. Skripten ligger i sessionens scratchpad och
sparas inte.*

### Svar först

**Ja, ombyggnaden fungerar.** Koden gör i allt väsentligt vad E142–E145
säger, och de tre namnen räknas om för hand till motorns värden: CENTA
40.18 (motorn 40.19), LIAB.ST 66.09 på dokumentets avrundade flöde (motorn
65.93; skillnaden är avrundningen av räntetillägget) och ULTA 601.27 exakt.
Alla 25 historikfiler klarar `--check`, och fem rader stämmer med PDF:en,
både siffran och året.

**Men fyra bekräftade fel ska rättas av nästa session:**

| # | Fel | Namn | Värde i dag → rättat | Spelar roll nu? |
|---|---|---|---|---|
| 1 | Historikfilen saknar den justerade EBIT som AcadeMedia trycker för varje år (E143(2)); EBIT-serien går över IFRS 16-bytet | ACAD.ST | base **173.63 → 158.75**, bear 138.28 → 118.18; Q4 PASS → **FAIL** (ROIIC 19,41 % → 7,20 %) | Nej: DROPPED på Q1, ingen position |
| 2 | Nattkörningen räknar bull utan att ange fallet; när bull-tillväxten är lika med base räknas bull med base-fallets nivå och ROIIC (strider mot E142(5)) | CROX, LOPE, MC.PA, PNDORA.CO, RBREW.CO | MC.PA bull 392.62 → 398.56 i nattrapporten | Bara MC.PA lever (WATCH-PRICED); inget innehav berörs |
| 3 | E146 har ingen kod: pensionsunderskottet läggs fortfarande till brutto | alla med ett pensionsben | ALV, LIAB.ST m.fl. ≲1 % för lågt | Nej i dag; nästa ändring i en store tar inte med regeln |
| 4 | ALV trycker organisk försäljningstillväxt, men historikfilen använder PROXY (E144(1)) | ALV | ej räknat | Nej: DROPPED på Q2, Q3 |

Ankarna (fråga 3): **inget namn ligger långt från både g\* och den
förväntade avkastningen utan förklaring.** RBREW.CO är det enda som ligger
långt från båda, och dokumentet förklarar det mesta (programmet, −103.54 per
aktie). Själva ankaret med förväntad avkastning är däremot skevt för namn
med hög tillväxt (se 3.2). Det rör ankaret, inte värdena.

---

### 1. Gör koden det reglerna säger?

Läst: E142–E147 (`reference/FRAMEWORK-EDITS.md` rad 12876–13007);
`vss/history.py` (organic_years, derived_growth, roiic_window, roiic, cycle,
quality); `vss/valuation.py:406–430`; `vss/runrecord.py` (E142Params,
case_of, e142_parts, _strike_unchecked, strike, normalised_flow);
`vss/strike.py:411–476` (apply_e142) och anchor_lines; `vss/runner.py`
(bear_case_value, fv_bull); `vss/manual.py` (interest_coverage, net debt).

#### Det som stämmer

- **E142(1)** `normalised_flow` sätter `deduct_acquisitions=False` när
  rekordet bär E142 (`runrecord.py:1161`, `valuation.py:400`).
- **E142(2)–(3)** `deal_programme_value` = |A| × (min(ROIIC, r)/r − 1) ×
  Σ((1+g)/(1+r))^t; `roiic_fraction` sätter ett tak vid r och ett golv vid 0.
  Stämmer med texten.
- **E142(4)** Den väntande affären ligger kvar i bryggan till det höga
  priset, och krediteras med pris × fraktion (`e142_parts`). Dokumentet
  skriver ut både låg och hög ände.
- **E142(5)** Base räknas på hela fönstret, bear på det sämsta
  femårsfönstret och bull på ROIIC = r (`E142Params.roiic`). Strike-vägen
  skickar `case=` uttryckligen (`strike.py:243, 250, 636`).
- **E142(6)** `missing()` vägrar när en serieköpare saknar ROIIC
  (`runrecord.py:1122`). E106:s golv i `apply_e142` jämför programmet vid
  noll med det neutrala programmet mot 3,5 %. Det slår in för MC.PA och
  BOUV.OL (ROIIC 0).
- **E143(1)** FCF0 = flöde × nivå × (1+g), innan DCF:en räknar upp år 1. Det
  rullar medlet ett år framåt, som regeln säger.
- **E143(3)–(4)** Cykeltestet: omsättningen föll mer än 10 % på ett år,
  eller marginalen föll under halva en tidigare topp. Base-nivå = min(1,
  median/senaste tre). Bear = lägsta ägarvinstmarginal/senaste tre (cykliskt),
  annars svagaste E140-år/medel. Allt stämmer.
- **E144(1)–(4)** Proxyn används bara för år där varken året självt eller
  året före betalade mer än 1 % av omsättningen för förvärv. Base =
  min(fönstret, de senaste fem, ägarvinst per aktie), med tak på 4 % eller
  8 % (sju år över 4 %) och golv på −3 %. Bear är det sämsta rullande
  treårsvärdet och bull det bästa rullande femårsvärdet. Färre än fem år:
  vyn står. Allt stämmer.
- **E145** Q1–Q5 med konstanterna 15 %, 50 %, 3,0×/4,5×, 15 %, och Q3 på
  bryggans nettoskuld utan leasingskulden. Stämmer.
- **E147** finns redan i `manual.interest_coverage` (E126 steg 2: resultat
  före skatt + tryckt räntekostnad när inget rörelseresultat är redovisat),
  och i `history.py:716` för companyfacts. Jag har inte kontrollerat att
  NVR:s store bär de två raderna.

#### Avvikelser

**1.1 BEKRÄFTAT — bull räknas med base-fallet i nattkörningen (E142(5)).**
`vss/runner.py:228` och `:280` anropar `record.strike(record.growth.bull)`
utan `case=`. `RunRecord.case_of` (`runrecord.py:1241`) kallar en tillväxt
"bull" bara när den skiljer sig från base. När taket nås är bull = base, och
då räknas bull med base-fallets nivå och ROIIC i stället för nivå 1 och
ROIIC = r. Kört på de 25 rekorden:

| Namn | bull utan case | bull med case (strike-dokumentet) |
|---|---:|---:|
| CROX | 171.83 | 250.10 |
| LOPE | 136.56 | 146.29 |
| MC.PA | 392.62 | 398.56 |
| PNDORA.CO | 903.28 | 933.40 |
| RBREW.CO | 195.97 | 299.50 |

`fv_bull` matar C4/E42-exittestet för ett innehav (`runner.py:276–292`) och
FV_bull-nivån när watchlisten saknar `fv_bull` (`:227`). Inget av de fem
namnen innehas; MC.PA är WATCH-PRICED. `bear_case_value` (`:143`) har samma
fel, men det är latent: inget av de 25 namnen har bear = base. **Rättning:**
skicka `case="bull"` och `case="bear"` i runner, eller låt `case_of` ta
emot fallet.

**1.2 BEKRÄFTAT — E146 saknar kod.** I `manual.py:4936` läggs
`legs["pension_deficit"]` till nettoskulden brutto. Ingenstans i `vss/`
nämns E146 eller (1 − skatt) på pensionsbenet. Regeln säger "applied from
the next store change", men ingen kod gör det när storen ändras. Storlek i
dag: ALV 197m USD × 25 % ≈ 49m (~0,6/aktie, ~0,9 %); LIAB.ST 280 SEKm ×
20,6 % ≈ 58m (0,75/aktie, ~1,1 %). Under E106:s 3,5 %, så E146:s "no
material pension leg" håller för 2026-10-27-uppsättningen.

**1.3 Text ≠ kod, inget värdefel — ROIIC-formeln (E142(2)).** Koden gör
fyra saker som texten inte säger:

- (a) Varje ände är **medlet av tre år** (hela fönstret), inte EBIT_end och
  EBIT_start. Bearfönstret använder enskilda år.
- (b) Förvärven summeras **mellan mittåren** (m0+1..m1), inte över hela
  historiken.
- (c) Ett år utan organisk siffra räknas med **vyns base-tillväxt**
  (CENTA: 7 av 8 år, HRB: 8 av 8).
- (d) Investerat kapital faller tillbaka på **eget kapital + nettoskuld**
  när ingen rad finns (CENTA, ULTA och de flesta amerikanska namnen).

Docstringen motiverar (a), och skälet är bra: ett enskilt slutår bär sina
engångsposter. Texten bör ändå skrivas om så att den säger vad koden gör.

**1.4 Dataglapp — Σ förvärv saknas för fem serieköpare.** ACAD.ST,
LIAB.ST, PNDORA.CO, RBREW.CO och BOUV.OL har ingen rad `acquisitions_paid`
i historikfilen. Då blir max(kapitaltillskott, Σ förvärv) bara
kapitaltillskottet, och ROIIC blir en övre gräns. Alla fem är DROPPED eller
står inte på listan.

**1.5 Kosmetiskt.** `roiic_base` sparas negativ (CTSH −1,9 %, PNDORA.CO
−22,0 %), medan bear sätts till minst noll i `apply_e142`. Värdet sätter
golvet ändå (`roiic_fraction`), så ingen effekt.

### 2. Tre namn räknade för hand

#### CENTA (dokument `reference/CENTA-STRIKE-2026-10-27-e142.md`, historik `config/history/CENTA.yaml`)

- **Nivå.** E140-åren 173,101,000 / 187,542,000 / 219,406,000 ger medlet
  193,349,667. Plus ränta efter skatt 24,609,000, minus minoritetens
  utdelning 1,346,000, blir **216,612,667** ✓.
- **Tillväxt.** Bara ett organiskt år (2023, PROXY −0,85 %; de andra åren
  har förvärv över 1 %), så vyn står: 2 / −1 / 3,5 % ✓.
- **ROIIC base.** Rörelseresultatets medel 2015–17 är 125.6m och 2023–25
  215.4m. Organisk faktor 1,02⁷ × 0,9915 = 1,139. Vinst = (215.36 − 125.64 ×
  1,139) × 0,75 = **54.2m**. Kapital (EK + nettoskuld): medlet 903m → 2,012m
  = +1,109m. Förvärv 2017–2024 = 103.9 + 91.2 + 41.2 + 0 + 820.5 + 0 + 0 +
  60.2 = **1,117m** (det större, och det som används). ROIIC = **4,85 %** ✓.
- **ROIIC bear.** 2019 → 2024: 152.07 → 185.39, faktor 1,0732, vinst 16.6m,
  förvärv 880.7m = **1,89 %** ✓.
- **Kärna, program, affärer, per aktie.**

| Fall | FCF0 | Program | Affärer | Hand | Motor |
|---|---:|---:|---:|---:|---:|
| bear | 191,988,490 | −1.64 | +2.70 | **20.26** | 20.26 |
| base | 220,944,920 | −1.16 | +6.92 | **40.18** | 40.19 |
| bull | 224,194,110 | 0 | +13.56 | **54.70** | 54.70 |

Nettoskuld 986,187,000 (balansräkning 196.3m + affärer 840m − rörelsekapital
50.2m), divisor 61,947,000. Skillnaden på 0.01 i base kommer från
avrundningen av ROIIC (4,85 %).

#### LIAB.ST (dokument, `config/history/LIAB.ST.yaml`)

- **Nivå.** E140-åren 1711−415−294−365 = 637; 1438−285−229−433 = 491;
  1347+9−331−453 = 572; medel 566.7. Plus ränta 160 (avrundad) ger 726 ✓.
- **Tillväxt.** Organisk 4, 4, 8, 3, −6, 17, 10, −9, −5, −4 %. CAGR över
  tio år 1,91 %, de senaste fem (2021–25) 1,0681^(1/5) − 1 = **1,33 %**,
  ägarvinst per aktie ~17,7 %. Base = 1,33 % ✓. Sämsta treårsvärdet
  2023–25 är −6,03 %, golvat till **−3 %** ✓. Bästa femårsvärdet 2018–22 är
  6,12 %, med tak **4 %** ✓.
- **ROIIC base** (justerat rörelseresultat, eftersom det finns för varje
  år). Medel 552 → 1,083, faktor 1,08·1,03·0,94·1,17·1,10·0,91·0,95 =
  1,163. Vinst (1,083 − 642.2) × 0,794 = 350. Sysselsatt kapital +6,105
  (inga förvärv i filen, se 1.4). ROIIC = **5,73 %** ✓.
- **ROIIC bear.** Alla sex femårsfönster räknade; 2020 → 2025 är sämst:
  916 → 1,027, faktor 1,068, 38.6 / 4,691 = **0,82 %** ✓.

| Fall | FCF0 | Program/aktie | Affärer/aktie | Hand | Motor |
|---|---:|---:|---:|---:|---:|
| bear | 611 | −45.38 | +0.03 | **−6.01** | −6.03 |
| base | 737 | −24.20 | +0.23 | **66.09** | 65.93 |
| bull | 756 | 0 | +0.39 | **122.55** | 122.39 |

Nettoskuld 2,959, divisor 77.036. Skillnaden är genomgående ~0.16 per aktie
och kommer av att dokumentet trycker räntetillägget avrundat (160). Ett
flöde på 726.4 i stället för 727 ger exakt motorns siffror.

#### ULTA (dokument, `config/history/ULTA.yaml`)

- **Nivå.** Medel 1,078,315,333 + ränta 1,340,250 = **1,079,655,583** ✓.
- **Tillväxt.** Nio PROXY-år 2017–2025; 2026 räknas inte, eftersom Space NK
  kostade 3,1 % av omsättningen. De senaste fem åren: 0,832 · 1,403 · 1,183
  · 1,098 · 1,008 = 1,528, alltså **8,83 %**. Sju år över 4 % ger taket
  8 %. Base = bull = **8 %** ✓, bear = sämsta treårsvärdet **1,49 %** ✓.
- **Cykel.** Omsättningen föll 17 % (2021), så namnet är cykliskt.
  Ägarvinstmarginalen de tre senaste åren är i medel 8,81 %. Lägsta
  marginalen är 2016:s, (375.9 − 299.2) / 3,924 = 1,95 %, vilket ger
  bear-nivån **0,222** ✓. Medianen 9,3 % ger base-nivå 1 ✓.
- **Program.** Ingen serieköpare: inget program och inga affärer ✓.

| Fall | FCF0 | Hand | Motor |
|---|---:|---:|---:|
| bear | 243,254,824 | **81.45** | 81.39 (nivån avrundad i dokumentet) |
| base | 1,166,028,030 | **601.27** | 601.27 |
| bull | = base | **601.27** | 601.27 |

Nettokassa 200,943,000, divisor 43,062,000.

**Kedjan stämmer i alla tre: nivå → tillväxt → kärna → program → affärer →
per aktie.**

### 3. Klarar värdena ankarna?

#### 3.1 Listan

Jag läste ankarna så här:

- **Långt från g\*:** värdet ligger minst 25 % från kursen.
- **Långt från den förväntade avkastningen:** det värde ankaret själv ger
  (ägarvinst/(r − g) plus nettokassa, alltså vad "ägarvinstavkastning + g"
  motsvarar vid r) ligger på andra sidan kursen, eller mycket närmare den.

Alla 25:

| Namn | Kurs | fv | fv/kurs | Ankarets värde | ankare/kurs | Program/aktie | Affärer/aktie |
|---|---:|---:|---:|---:|---:|---:|---:|
| ACAD.ST | 112.40 | 173.63 | +54 % | 282.08 | +151 % | 0 | +6.51 |
| ACN | 247.23 | 274.88 | +11 % | 337.12 | +36 % | 0 | +0.81 |
| ALV | 115.32 | 68.15 | −41 % | 78.14 | −32 % | 0 | 0 |
| AOS | 61.91 | 64.35 | +4 % | 76.63 | +24 % | −1.59 | 0 |
| AUTO.L | 5.28 | 4.99 | −6 % | 5.21 | −1 % | 0 | 0 |
| BOUV.OL | 51.70 | 54.42 | +5 % | 57.06 | +10 % | −0.46 | 0 |
| CENTA | 39.13 | 40.19 | +3 % | 32.59 | −17 % | −1.16 | +6.93 |
| CPRT | 29.15 | 26.96 | −8 % | 38.19 | +31 % | 0 | +2.04 |
| CROX | 118.85 | 171.83 | +45 % | 201.54 | +70 % | 0 | 0 |
| CTSH | 69.34 | 73.82 | +6 % | 98.09 | +41 % | −11.02 | 0 |
| DECK | 80.37 | 85.05 | +6 % | 87.79 | +9 % | 0 | 0 |
| GDDY | 109.82 | 79.99 | −27 % | 84.35 | −23 % | 0 | 0 |
| HRB | 50.06 | 68.38 | +37 % | 66.76 | +33 % | −1.12 | 0 |
| LIAB.ST | 129.50 | 65.93 | −49 % | 80.01 | −38 % | −24.20 | +0.23 |
| LII | 365.64 | 309.55 | −15 % | 357.60 | −2 % | 0 | +5.89 |
| LOPE | 160.71 | 136.56 | −15 % | 157.06 | −2 % | 0 | 0 |
| MC.PA | 385.40 | 392.62 | +2 % | 462.68 | +20 % | −5.94 | 0 |
| MEKKO.HE | 9.17 | 10.95 | +19 % | 14.30 | +56 % | 0 | 0 |
| MUSA | 539.14 | 268.53 | −50 % | 254.66 | −53 % | 0 | 0 |
| NVR | 5727.77 | 7682.75 | +34 % | 8875.67 | +55 % | 0 | 0 |
| PEP | 135.46 | 65.03 | −52 % | 63.62 | −53 % | −2.09 | 0 |
| PNDORA.CO | 838.40 | 903.28 | +8 % | 1096.19 | +31 % | −30.12 | 0 |
| **RBREW.CO** | 435.40 | 195.97 | **−55 %** | 366.59 | **−16 %** | **−103.54** | 0 |
| RMV.L | 5.31 | 4.11 | −23 % | 4.29 | −19 % | 0 | 0 |
| ULTA | 625.33 | 601.27 | −4 % | 1954.27 | +213 % | 0 | 0 |

**Bara RBREW.CO ligger långt från båda.** Värdet är −55 % mot kursen, medan
ankaret säger −16 %. Dokumentet förklarar det mesta: base-raden trycker
programmet −103.54 per aktie, och utan det är värdet 299.50. Resten (299.50
mot 366.59) är avtrappningen i 3.2, och den står inte i dokumentet. Namnet
är DROPPED.

LIAB.ST är samma sak i mindre skala: programmet −24.20 tar värdet från
89.89 till 65.93, och ankaret ligger på 80.01. Övriga namn som ligger långt
från kursen (ACAD.ST, ALV, CROX, HRB, MUSA, NVR, PEP, GDDY) har ankaret på
samma sida och ungefär lika långt bort.

#### 3.2 Ankaret självt är skevt vid hög tillväxt

Ankaret "ägarvinstavkastning på EV + base-tillväxt" (`strike.py:662`) är en
evig Gordon-formel på base-tillväxten. DCF:en håller den tillväxten i tio
år och går sedan ner till 2,5 %. När g är över 2,5 % säger ankaret därför
"billigt" mer än värdet kan. Mest i:

- ULTA (8 %): ankaret 1954 mot DCF 601;
- ACAD.ST (6 %);
- CPRT (6 %): värdet ligger under kursen, men ankaret ligger 31 % över;
- MEKKO.HE (5 %).

Inget dokument säger detta. Ankaret räknar inte heller med programmet eller
krediten för väntande affärer, medan EV tar med affärerna till fullt pris
(så CENTA:s 8,5 % ligger under r, trots att värdet ligger över kursen).

**ULTA**, som ombyggnaden bad kontrollen titta på: base ligger på g\*
(8,00 % mot 8,47 %), så marknaden prisar redan de 8 procenten. Ankarets
12,4 % är ankarets fel, inte värdets. De 8 procenten är också bolagets egen
utveckling: omsättningen gick från 7,40 till 11,30 mdr mellan räkenskapsår
2020 och 2025, genom hela covid-dalen.

### 4. Historikfilerna

**`vss history --ticker X --check` på alla 25:** alla svarar "every
hand-read row PASSES against its PDF".

Kontrollen ser två saker: att citatet finns i PDF:ens text och att siffrorna
finns i citatet. Den ser inte **vilken kolumn som är vilket år**, och den
hoppar över XBRL-rader helt (`check`, `history.py:253`). Det är därför
stickproven nedan läser rubrikraden.

| # | Namn | Rad | PDF, sida | Tryckt | Fil | År |
|---|---|---|---|---|---|---|
| 1 | LIAB.ST (SE) | organisk tillväxt, total operations | AR2025 s. 78 | 2025…2021: –4 –5 –9 10 17 | −4 −5 −9 10 17 | ✓ (även EBIT 2021 841, sysselsatt kapital 12,114…7,920) |
| 2 | ACAD.ST (SE) | EBIT | AR2020/21 s. 112 | 2020/21…2015/16: 1,169 973 635 622 615 535 | samma, år 2021…2016 (räkenskapsåret slutar 30/6, märkt efter slutåret) | ✓, men se 4.1 |
| 3 | PNDORA.CO (DK) | organisk tillväxt | AR2025 s. 14; AR2020 s. 9 | 6 13 8 7 23 (2025–21); −11 −8 −2 11 N/A (2020–16) | samma; 2016 utelämnat | ✓ |
| 4 | AUTO.L (GB) | rörelseresultat | AR2026 s. 143 (tryckt 141); AR2018 s. 90 | 392.7 376.8 348.7 277.6 303.6 (2026–22); 220.6 / 203.1 (2018 / 2017) | samma; 2018 = 220.6 | ✓ |
| 5 | CENTA (US) | rörelseresultat FY2025 (XBRL) | 10-K FY2025, "Income from operations" | 250,042 (tusen USD) | 250,042,000 | ✓ (även FY2024 185,387) |

#### 4.1 BEKRÄFTAT — ACAD.ST saknar den justerade EBIT som E143(2) kräver

Båda AcadeMedias femårssammanställningar trycker **"Adjusted EBIT, SEK m."**
för varje år:

- AR2020/21 s. 112: 934, 728, 634, 670, 638, 567;
- AR2025/26 s. 121: 1,487, 1,281, 1,097, 964, 1,001, 939.

Adjusted EBIT räknas utan IFRS 16 och utan jämförelsestörande poster.
E143(2) säger "operating profit (adjusted where the summary states it for
every year)". Historikfilen har bara EBIT. Den serien går över IFRS 16:
EBITDA hoppar från 931 till 2,486 mellan 2018/19 och 2019/20, och EBIT från
635 till 973. Hoppet hamnar i ROIIC:s vinst, medan det sysselsatta kapitalet
inte hoppar (7,386 → 7,250). Under E117 är hyran en rörelsekostnad, så det
justerade måttet är också det som hänger ihop med flödet.

Omräknat på justerad EBIT, med samma organiska faktor 1,593 och samma
kapital:

- **Base.** Medel 625.0 (2016–18) → 1,288.3 (2024–26). Vinst (1,288.3 −
  995.6) × 0,794 = 232.4, på 3,226.3 = **7,20 %** (i dag 19,41 %).
- **Bear.** 2021 → 2026: 939 → 1,487, faktor 1,339, vinst 182.1, på 2,898 =
  **6,28 %** (i dag 10,26 %).

Effekt, räknad med rekordets egen `strike` på en kopia med de två
ROIIC-värdena:

- base **173.63 → 158.75**;
- bear **138.28 → 118.18**;
- bull oförändrad 181.95;
- Q4 **FAIL** (7,2 % mot 9,5 %).

ACAD.ST är redan DROPPED på Q1, så ingen order påverkas. **Nästa session:**
lägg till raden `operating_profit_adjusted` i `config/history/ACAD.ST.yaml`
från de två sidorna och stryk om.

#### 4.2 BEKRÄFTAT — ALV använder PROXY fast bolaget trycker organisk tillväxt

ALV:s 10-K för FY2025 (`sources/ALV_FY2025_annual-report-10k_2026-02-19_en_a0.htm`)
redovisar "organic sales growth (Non-GAAP measure)". Historikfilen har ingen
sådan rad, så alla åtta åren är omsättningsproxy, och den tar med valuta.
E144(1) använder proxyn bara där bolaget inte själv trycker en organisk
siffra. Effekten på värdet är inte räknad. ALV är DROPPED på Q2 och Q3,
och de testen beror inte på tillväxten.

#### 4.3 SANNOLIKT — IFRS 16-sömmen i övriga IFRS-serier

Samma söm finns i LIAB.ST: det sysselsatta kapitalet går från 5,848 till
7,383 mellan 2018 och 2019, och det justerade rörelseresultatet från 634
till 915. Här rör sig både täljaren och nämnaren, så riktningen på ROIIC-felet
är okänd tills leasingbeloppen är lästa. LIAB.ST är DROPPED.

PNDORA.CO:s ROIIC är redan under noll, och sömmen kan bara göra den lägre,
så den ändras inte. RBREW.CO har små leasingbelopp. Inte räknat vidare.

---

### Utanför uppdraget (noterat, inte följt)

- AcadeMedias organiska tillväxt är "incl. minor acquisitions" (AR2025/26
  s. 121). E144(1) tar den som tryckt, så base 6,02 % innehåller förvärvad
  tillväxt från småköp.
- ULTA:s cykliska bear-nivå 0,222 vilar på räkenskapsår 2016:s
  ägarvinstmarginal, 1,95 %. Det var ett år med tung butiksexpansion, inte
  en konjunkturbotten.
- CROX:s "cykel" (marginalen från 29,5 % till 3,7 %) är ett
  nedskrivningsår för HEYDUDE, inte en efterfrågecykel.
- Q1 skriver "inf%" eller tusentals procent där det materiella kapitalet är
  noll eller negativt (HRB, GDDY, ACN, LII). Utfallet PASS är rimligt, men
  det ser konstigt ut i utskriften.
- `vss history --check` kontrollerar inte årsmappningen. En kolumnförskjutning
  i en tryckt rad med samma siffror skulle passera.

---

### Åtgärdat samma kväll (commit 8308452 och de 25 omstrykningarna `2026-10-27-check`)

| # | Fel | Rättning | Effekt |
|---|---|---|---|
| 1 | ACAD.ST utan justerad EBIT | raderna `operating_profit_adjusted` från AR2020/21 s. 112 och AR2025/26 s. 121, maskinkontrollerade | base 173.63 → **158.74**, bear 138.28 → 110.63, Q4 FAIL (ROIIC 7,20 %) |
| 2 | bull/bear utan fall i nattkörningen | `runner.py` och strike-tabellen anger `case=` | nattrapportens bull = dokumentets |
| 3 | E146 utan kod | E142-värdet krediterar underskott × skattesats; flagga på posten så att äldre poster spelas upp som strukna | CTSH +0.14, LIAB.ST +0.75, PEP +0.25, ACN +0.63, MC.PA +0.33 |
| 4 | ALV på PROXY | organisk försäljningstillväxt 2019–2025 ur sju 10-K | base 68.15 → **71.74**; fortfarande DROPPED (Q2, Q3) |
| 1.3 | E142(2) text ≠ kod | texten skriven om efter koden | — |
| 3.2 | ankaret skevt vid hög tillväxt | "förväntad avkastning" är nu räntan där base-fallet möter kursen | ULTA 12,4 % → 9,3 %, ACAD 13,4 % → 11,3 % |
| 1.5 / utskrift | Q1 "inf%" | skrivs "above any rate" | — |

Ingen status ändras av rättningarna. Bevakningslistan pekar på `-check`-posterna.




# DEL E — Bolag för bolag: senaste värdering (strike-dokument) och beslut

*Varje block är motorns egen utskrift av hela kedjan: FCF0, brygga, tillväxt, cykel, förvärvsprogram, bear/base/bull och kvalitetstesterna Q1–Q5. Status = bevakningslistan 2026-10-28.*


## ACAD.ST

**Status på listan:** WATCH-PRICED · tier 3 · fv_base 158.74  
*Källa: `reference/ACAD.ST-STRIKE-2026-10-27-goodwill.md`*

#### ACAD.ST -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/ACAD.ST.yaml` on the growth DERIVED from the issuer's history (E144) 6.02% / 5.20% / 6.53%, carried from ACAD.ST-2026-10-27-check.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2026
- **fv_base:** 158.74 -> **158.74** (bear 110.63, bull 181.95)
- **FCF0:** 931
- **net debt:** 1,710 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2024 813; annual FY2025 936; annual FY2026 1,045 = 931; acquisitions mean 643 NOT deducted -- valued as the deal programme (E142); + interest after tax 0 at 0.206 (SE); - minority dividends 0
- **bridge (E140(3), deals at the HIGH end):** net debt 1,710 on the balance sheet + deals 640 + working capital neutralised 0 = 2,350
- **growth (E144):** E144: organic 6.28%/yr over 11 years, last five 6.02% (2016-2026); owner earnings per share not derivable; cap 8%; worst 3-year 5.20%, best 5-year 6.53%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.873: the weakest E140 year 813 over the mean 931 (E143(4))
- **deal programme (E142):** repeat buyer, A = 643/yr; ROIIC base 7.20% -- adjusted operating profit 625,000,000 (2016-2018 mean) -> 1,288,333,333 (2024-2026 mean); organic x1.593; after tax 20.6%: 232,330,886 on capital added 3,226,333,333 = 7.20%; bear 5.07% -- adjusted operating profit 670,000,000 (2018) -> 964,000,000 (2023); organic x1.326; after tax 20.6%: 59,775,151 on capital added 1,178,000,000 = 5.07%
- **bear:** flow 931 x level 0.873 x (1 + 5.20%) = FCF0 855; programme -2,419 (-24.62/sh); deals 640 credited back 342 at ROIIC 5.07% (+3.48/sh); pension deficit after tax (E146) +0 (+0.00/sh) -> **110.63**
- **base:** flow 931 x level 1.000 x (1 + 6.02%) = FCF0 987; programme -1,308 (-13.32/sh); deals 640 credited back 485 at ROIIC 7.20% (+4.94/sh); pension deficit after tax (E146) +0 (+0.00/sh) -> **158.74**
- **bull:** flow 931 x level 1.000 x (1 + 6.53%) = FCF0 992; programme 0 (+0.00/sh); deals 640 credited back 640 at ROIIC 9.50% (+6.51/sh); pension deficit after tax (E146) +0 (+0.00/sh) -> **181.95**
- **events ledger** `reference/events/ACAD.ST.yaml` dated 2026-10-27, cut at 2026-06-30: Kindernet (NL, 40 preschools, 2025 sales ~EUR 18.4m); Florencius (NL, ~EUR 3m); Kids&Co (PL, 34 preschools, ~PLN 99m) -- prices NOT DISCLOSED; range is the session estimate at ~0.5-1.0x sales 265..640
- **divisor:** 98,237,000
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 2,557 is DEDUCTED -- principal 1,888 + lease interest 669; the lease liability 12,244 LEFT net debt
- **close 2026-10-26:** 112.40; g* 2.53%
- **store's newest period:** --
- **anchors:** g* 2.53%; the base case returns ~11.3% a year at today's price against r 9.5%; tangible ROIC median 48.1% over 6 years (goodwill taken out) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 48.1% over 6 years (goodwill taken out) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; adjusted operating profit at most 5% below its running peak
  - Q3 debt: **PASS** -- net debt 2.4x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **FAIL** -- ROIIC 7.2% against r 9.5%
  - Q5 understandable: **PASS** -- AcadeMedia runs preschools, compulsory and upper secondary schools and adult education, mainly in Sweden.

```
ACAD.ST — strike 2026-10-27   against ACAD.ST-2026-10-27-check.json

                                               before           after     move
fv_base                                        158.74          158.74    +0.0%
  bear                                         110.63          110.63    +0.0%
  bull                                         181.95          181.95    +0.0%
MBP (E90)  tier -- -> --                           --              --         
g*                                                              2.53%         
  fv_base, deals at LOW end (E140(3))                          159.66         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-06-30 -> 2026-06-30
  settled close           2026-10-26 -> 2026-10-26  (112.40)
  store's newest period, today: --
```

Record: `reference/run-records/ACAD.ST-2026-10-27-goodwill.json`

**Genomgång steg för steg (`reference/reviews/ACAD.ST/2026-10-27.yaml`):**

```yaml
schema: vss/review v1
ticker: ACAD.ST
date: '2026-10-27'
status_at_start: PIPELINE
prepare_report: reports/prepare/ACAD.ST-2026-10-27.json
prepare_waived: null
steps:
- step: gate-1
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). NOT PASSED,
    and it does not bar the name. ACAD entered on value under E139 at its 52-week high (dd_at_entry 0.0%,
    2026-10-19); today''s drawdown 2.1%. E139 left open how a value entry''s tier treats Gate 1: it scores
    0 in section 4.4 and the name may still carry a tier -- the owner''s own words at entry were "vi skiter
    i gate 1 o vi skiter i ras vi vill ha värdebolag".'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - reports/prepare/ACAD.ST-2026-10-27.md
  rulings_cited:
  - E139
  - E12
  verification: []
- step: gate-2
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). NOT PASSED (scores
    0): there is no decline to classify. Not class D either: the filings show no damage to the model --
    every quarter of 2025/26 grew (organic incl. bolt-ons 6.2%, 4.5%, 5.7%, 6.0%). THE POLITICAL RISK
    IS NAMED HERE AND CARRIED, NOT SCORED: the election of 2026-09-13 went 176-173 to the opposition and
    Kristersson resigned; the Tidö proposal of May 2026 bars value transfers from NEW schools, schools
    with NEW owners and sanctioned schools from 2027-07-01 (SVT, Skolledaren). It does not touch the existing
    schools, and seven of the year''s eight acquisitions were outside Sweden. A new government''s line
    on profits in tax-funded schools is not known on the record; it is the event that would move this
    to D.'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - sources/ACAD.ST_2026-Q1_interim-report-q1-and-q3_2025-11-03_en_a0.pdf
  - sources/ACAD.ST_2026-Q2_half-year-financial-report_2026-02-02_en_a0.pdf
  - sources/ACAD.ST_2026-Q3_interim-report-q1-and-q3_2026-05-11_en_a0.pdf
  - sources/ACAD.ST_2026-Q4_financial-statement-release_2026-08-31_en_a0.pdf
  - reports/prepare/ACAD.ST-2026-10-27.md
  rulings_cited:
  - E139
  - B1
  verification: []
- step: gate-3
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). PASS on its
    evaluable limbs. Net debt / EBITDA 0.95x (E119 derived, rent-bearing, against 2.5x). FCF positive
    in 6 of 8 quarters on the rent-bearing flow (E117): operating cash flow less lease principal and lease
    interest -- Q1 2024/25 -167, Q2 642, Q3 189, Q4 553, Q1 2025/26 -62, Q2 754, Q3 288, Q4 393 (SEK m,
    before capex of about 85-100 a quarter, which turns no positive quarter negative); the two negatives
    are the summer quarters, when no school fees fall. Interest coverage DATA MISSING (no right-of-use
    depreciation on the basis, E117 clause 5). Auditor Öhrlings PricewaterhouseCoopers; no going-concern
    language and no restatement in the 2025/26 annual report.'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - sources/ACAD.ST_2026-FY_annual-financial-report_2026-10-22_en_a0.pdf
  - sources/ACAD.ST_2026-Q1_interim-report-q1-and-q3_2025-11-03_en_a0.pdf
  - sources/ACAD.ST_2026-Q2_half-year-financial-report_2026-02-02_en_a0.pdf
  - sources/ACAD.ST_2026-Q3_interim-report-q1-and-q3_2026-05-11_en_a0.pdf
  - sources/ACAD.ST_2026-Q4_financial-statement-release_2026-08-31_en_a0.pdf
  - reports/prepare/ACAD.ST-2026-10-27.md
  rulings_cited:
  - E117
  - E119
  - E99
  verification: []
- step: gate-4
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). DATA MISSING
    for every name (E99); out of the count.'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened: []
  rulings_cited:
  - E99
  verification: []
- step: gate-5
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). PASS: the Q1
    2026/27 interim report (July-September 2026) is dated 2026-11-02 in the issuer''s financial calendar,
    six days out.'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened: []
  rulings_cited: []
  verification: []
- step: hard-kills
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). NO HARD KILL
    TRIPS. 4.2.1: net sales grew in all four quarters -- 4,101 vs 3,842 (+6.7%), 5,231 vs 5,025 (+4.1%),
    5,371 vs 5,037 (+6.6%), 5,658 vs 5,118 (+10.6%). 4.2.2: EBIT rose every quarter -- 292 vs 272, 450
    vs 402, 539 vs 499, 666 vs 578; FY EBIT margin 9.6% vs 9.2%. 4.2.3: the 2025-11-03 revision kept 5-7%
    growth and moved the margin target from adjusted EBIT to adjusted EBITA 7-8% "to better reflect the
    company''s focus on acquisition-driven growth" -- the measure loosened (EBITA leaves out the amortisation
    of acquired intangibles) but no number was cut; noted, not a kill. 4.2.4 DATA MISSING (no consensus
    on file). 4.2.5 0.95x against 3.5x. 4.2.6: only the Deputy CEO left (2026-01-31); CEO Marcus Strömberg
    and CFO Petter Sylvan in post. 4.2.7: receivables 371 vs 330 (+12.4%) on sales +7.0% is 1.8x on the YEAR -- above the 1.5x line on one annual point; the kill needs 2+ quarters and the quarterly receivables are not on file, so DATA MISSING, watched at the 2026-11-02 report.'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - sources/ACAD.ST_2026-Q1_interim-report-q1-and-q3_2025-11-03_en_a0.pdf
  - sources/ACAD.ST_2026-Q2_half-year-financial-report_2026-02-02_en_a0.pdf
  - sources/ACAD.ST_2026-Q3_interim-report-q1-and-q3_2026-05-11_en_a0.pdf
  - sources/ACAD.ST_2026-Q4_financial-statement-release_2026-08-31_en_a0.pdf
  - sources/ACAD.ST_2026-Q1_investor-news_2025-11-03_en_a0.pdf
  - sources/ACAD.ST_2026-FY_annual-financial-report_2026-10-22_en_a0.pdf
  rulings_cited:
  - E45
  - B9
  - E119
  verification: []
- step: conviction
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). SCORE 4 (medium
    band, 4-5). Gates passed 2 (Gate 3, Gate 5; Gate 1 and Gate 2 score 0, Gate 4 out). Green +2: FCF
    conversion 109% (rent-bearing FY2025/26 free cash flow 1,045 against profit for the year 955); margin
    expansion through the political controversy (adjusted EBIT 1,487 on 20,360 = 7.3% against 1,281 on
    19,021 = 6.7%). Not taken: guidance through a drawdown (there was none), buyback at depressed prices
    (the price stood at its high), insider cluster (no Swedish insider register on file -- DATA MISSING),
    market share (no market series). Soft 0: no regulatory PROBE is open; the profit-limitation proposal
    is legislation, carried at Gate 2.'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - sources/ACAD.ST_2026-FY_annual-financial-report_2026-10-22_en_a0.pdf
  - reports/prepare/ACAD.ST-2026-10-27.md
  rulings_cited:
  - E99
  - E76
  verification: []
- step: basis
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). annual FY2026
    (July 2025 - June 2026), one twelve-month window; the prepare report lists 0 UNVERIFIED figures the
    basis reads.'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - reports/prepare/ACAD.ST-2026-10-27.md
  rulings_cited:
  - E19
  - E21
  verification: []
- step: flow
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). FCF0 is E140''s
    three-year mean, rent-bearing (E117: lease principal and interest deducted): FY2024 813, FY2025 936,
    FY2026 1,045 = 931; acquisitions are valued as the deal programme at the acquirer''s ROIIC (E142).'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - sources/ACAD.ST_2026-FY_annual-financial-report_2026-10-22_en_a0.pdf
  rulings_cited:
  - E140
  - E117
  - E142
  verification: []
- step: net-debt
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). Net debt 1,710
    on the balance sheet of 2026-06-30, IFRS 16 lease liabilities out (E117(3)); the post-basis deals
    Kindernet, Florencius and Kids&Co enter the bridge at the high end, 640 (E140(3)); additional purchase
    considerations as printed.'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - sources/ACAD.ST_2026-FY_annual-financial-report_2026-10-22_en_a0.pdf
  rulings_cited:
  - E117
  - E140
  verification: []
- step: divisor
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). the weighted-average
    DILUTED count for FY2026, the same window as the flows (E38).'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - reports/prepare/ACAD.ST-2026-10-27.md
  rulings_cited:
  - E38
  verification: []
- step: growth-view
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). The registered
    view of 2026-10-20 (4.5% / 3.5% / 7%) stands as the record; the strike reads the E144 growth derived
    from the history file, which the rules put first.'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened: []
  rulings_cited:
  - E28
  - E144
  verification: []
- step: strike
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). Struck 2026-10-27
    (reference/ACAD.ST-STRIKE-2026-10-27-goodwill.md): base 158.74, bear 110.63, bull 181.95; g* 2.53%;
    the base case returns about 11.3% a year at 112.40. E145: Q1 PASS (tangible ROIC 48.1% with goodwill
    out), Q2 PASS, Q3 PASS (2.4x), Q4 FAIL (ROIIC 7.2% against 9.5%), Q5 PASS.'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - reference/ACAD.ST-STRIKE-2026-10-27-goodwill.md
  rulings_cited:
  - E142
  - E144
  - E145
  verification: []
- step: tier-mbp
  outcome: verdict
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). TIER 3. Score
    4 is the medium band -> Tier 2; E145 Q4 (the acquisitions earn 7.2%, below the 9.5% hurdle, and the
    company has just made acquisition-driven growth its stated strategy) lowers it one step -> Tier 3;
    E77''s regime shift has nowhere further to go (Tier 3 is the floor, C2). MBP = 158.74 x 0.65 = 103.18
    SEK (E90).'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened: []
  rulings_cited:
  - E90
  - E77
  - E145
  - C2
  verification: []
- step: verdict
  outcome: watch-priced
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). WATCH-PRICED,
    tier 3, MBP 103.18 SEK against 112.40 (the price is 8.9% above the line). Warren''s reading: a steady,
    cash-generative school operator, priced fairly rather than cheaply once the acquisition habit and
    the political risk are counted; buy only with the cushion. CONDITIONS: the price at or below 103.18
    on a settled close; no change in Swedish law or a new government''s programme that limits profits
    in EXISTING schools (that is a Gate 2 class D event and gates the name at once); the Q1 2026/27 report
    of 2026-11-02 read before any order. STOP: set at entry under FRAMEWORK §6.4, not before.'
  answered_at: '2026-10-27T21:22:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened: []
  rulings_cited:
  - E27
  - E90
  - E141
  verification: []
growth_view:
  base: 0.045
  bear: 0.035
  bull: 0.07
  registered_at: '2026-10-20T00:00:00+02:00'
  reasons: 'standing view of 2026-10-20, reference/growth-views/ACAD.ST.md (E141 decision: it stands;
    the strike reads the E144 growth derived from the history file)'
note: '2026-10-27 (E141 decision, full walk reference/reviews/ACAD.ST/2026-10-27.yaml): PIPELINE -> WATCH-PRICED,
  tier 3, MBP 103.18 SEK (158.74 x 0.65) against 112.40. Score 4: Gate 3 and Gate 5 passed (Gate 1 and
  2 score 0 on a value entry, E139), green flags FCF conversion 109% and margin expansion. No hard kill:
  every quarter of 2025/26 grew 4-11% with EBIT up. Tier 2 lowered to 3 by E145 Q4 (acquisitions earn
  7.2% against 9.5%). Carried risk: the 2026-09-13 election went to the opposition; a law limiting profits
  in EXISTING schools gates the name at once. Read the Q1 2026/27 report (2026-11-02) before any order.'
```

## ACN

**Status på listan:** INTAKE · tier – · fv_base –  
*Källa: `reference/ACN-STRIKE-2026-10-27-check.md`*

#### ACN -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/ACN.yaml` on the pre-registered growth view 4.50% / 0.00% / 7.50%, carried from ACN-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** TTM 2026-Q1+2026-Q2+2026-Q3+2026-Q4
- **fv_base:** 274.88 -> **275.51** (bear 167.04, bull 353.60)
- **FCF0:** 9,500,796,333
- **net debt:** -1,167,236,000 on the balance sheet of 2026-08-31
- **E140 FCF0:** mean of annual FY2024 8,945,894,000; annual FY2025 9,530,579,000; annual FY2026 10,171,821,000 = 9,549,431,333; acquisitions mean 4,331,613,667 NOT deducted -- valued as the deal programme (E142); + interest after tax -44,856,000 at 0.25 (US); - minority dividends 3,779,000
- **bridge (E140(3), deals at the HIGH end):** net debt -1,167,236,000 on the balance sheet + deals 500,000,000 + working capital neutralised 0 = -667,236,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/ACN.yaml; the registered view reference/growth-views/ACN.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.937: the weakest E140 year 8,945,894,000 over the mean 9,549,431,333 (E143(4))
- **deal programme (E142):** repeat buyer, A = 4,331,613,667/yr; ROIIC base 9.98% -- operating profit 5,300,208,667 (2016-2018 mean) -> 10,409,157,000 (2024-2026 mean); organic x1.422 (8 of 8 years at the view's 4.5%); after tax 25.0%: 2,153,795,255 on acquisitions 21,585,711,000 = 9.98%; bear 7.14% -- operating profit 6,305,074,000 (2019) -> 9,595,847,000 (2024); organic x1.246 (5 of 5 years at the view's 4.5%); after tax 25.0%: 1,303,933,249 on acquisitions 18,263,839,000 = 7.14%
- **bear:** flow 9,500,796,333 x level 0.937 x (1 + 0.00%) = FCF0 8,900,332,800; programme -6,758,032,315 (-10.94/sh); deals 500,000,000 credited back 375,759,257 at ROIIC 7.14% (+0.61/sh); pension deficit after tax (E146) +389,693,750 (+0.63/sh) -> **167.04**
- **base:** flow 9,500,796,333 x level 1.000 x (1 + 4.50%) = FCF0 9,928,332,168; programme 0 (+0.00/sh); deals 500,000,000 credited back 500,000,000 at ROIIC 9.98% (+0.81/sh); pension deficit after tax (E146) +389,693,750 (+0.63/sh) -> **275.51**
- **bull:** flow 9,500,796,333 x level 1.000 x (1 + 7.50%) = FCF0 10,213,356,058; programme 0 (+0.00/sh); deals 500,000,000 credited back 500,000,000 at ROIIC 9.50% (+0.81/sh); pension deficit after tax (E146) +389,693,750 (+0.63/sh) -> **353.60**
- **events ledger** `reference/events/ACN.yaml` dated 2026-10-27, cut at 2026-08-31: Mjolner Informatics, Sagacity, McCoy (pending), NetRise/IndX (status unconfirmed) -- prices NOT DISCLOSED; range is the session estimate 50,000,000..500,000,000
- **divisor:** 617,498,483
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 3,285,232,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 247.23; g* 3.19%
- **store's newest period:** 2026-08-31
- **anchors:** g* 3.19%; the base case returns ~10.2% a year at today's price against r 9.5%; tangible ROIC median 2309.6% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 2309.6% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 6% below its running peak
  - Q3 debt: **PASS** -- net debt -0.1x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **PASS** -- ROIIC 10.0% against r 9.5%
  - Q5 understandable: **PASS** -- Accenture sells consulting, managed services, proprietary platforms and software to large companies and governments, who return because it embeds in their technology and operations.

```
ACN — strike 2026-10-27   against ACN-2026-10-27-e142.json

                                               before           after     move
fv_base                                        274.88          275.51    +0.2%
  bear                                         166.41          167.04    +0.4%
  bull                                         352.97          353.60    +0.2%
MBP (E90)  tier -- -> --                           --              --         
g*                                                              3.19%         
  fv_base, deals at LOW end (E140(3))                          275.51         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-08-31 -> 2026-08-31
  settled close           2026-10-26 -> 2026-10-26  (247.23)
  store's newest period, today: 2026-08-31
```

Record: `reference/run-records/ACN-2026-10-27-check.json`

## ALV

**Status på listan:** DROPPED · tier – · fv_base 71.74  
*Källa: `reference/ALV-STRIKE-2026-10-27-check.md`*

#### ALV -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/ALV.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / -1.70% / 4.00%, carried from ALV-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 68.15 -> **71.74** (bear -18.41, bull 99.72)
- **FCF0:** 529,083,333
- **net debt:** 1,912,000,000 on the balance sheet of 2026-09-30
- **E140 FCF0:** mean of annual FY2023 209,000,000; annual FY2024 422,000,000; annual FY2025 750,000,000 = 460,333,333; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 69,750,000 at 0.25 (US); - minority dividends 1,000,000
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-09-30; year-to-date working capital -135,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 1,912,000,000 on the balance sheet + deals 0 + working capital neutralised -135,000,000 = 1,777,000,000
- **growth (E144):** E144: organic 4.58%/yr over 8 years, last five 8.55% (2018-2025, 1 of them PROXY from deal-free years); owner earnings per share 7.37%/yr; cap 4%; worst 3-year -1.70%, best 5-year 8.55%
- **cycle and level (E143):** CYCLICAL (revenue fell -14% in a year; operating margin fell from 10.6% to 5.1%): owner-earnings margin median 3.9%, last three 5.0%, lowest 0.4% -> base level x0.773, bear x0.070
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 529,083,333 x level 0.070 x (1 + -1.70%) = FCF0 36,326,209; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh); pension deficit after tax (E146) +43,750,000 (+0.60/sh) -> **-18.41**
- **base:** flow 529,083,333 x level 0.773 x (1 + 4.00%) = FCF0 425,583,249; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -64.52% (+0.00/sh); pension deficit after tax (E146) +43,750,000 (+0.60/sh) -> **71.74**
- **bull:** flow 529,083,333 x level 1.000 x (1 + 4.00%) = FCF0 550,246,667; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh); pension deficit after tax (E146) +43,750,000 (+0.60/sh) -> **99.72**
- **events ledger** `reference/events/ALV.yaml` dated 2026-10-27, cut at 2026-09-30: no deal in the bridge
- **divisor:** 72,900,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 154,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 115.32; g* 8.48%
- **store's newest period:** --
- **anchors:** g* 8.48%; the base case returns ~7.4% a year at today's price against r 9.5%; tangible ROIC median 22.2% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 22.2% over 11 years against 15%
  - Q2 stability: **FAIL** -- owner earnings negative in no year; operating profit at most 56% below its running peak, not regained within three years after [2020]
  - Q3 debt: **FAIL** -- net debt 4.2x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Autoliv makes airbags, steering wheels and seatbelts for car makers, who keep buying because safety systems are designed in for each vehicle platform.

```
ALV — strike 2026-10-27   against ALV-2026-10-27-e142.json

                                  before           after     move
fv_base                            68.15           71.74    +5.3%
  bear                            -19.01          -18.41    -3.2%
  bull                             99.12           99.72    +0.6%
MBP (E90)  tier -- -> --              --              --         
g*                                                 8.48%         

WHICH LEG MOVED
  growth view        3.62% / -2.91% / 4.00% -> 4.00% / -1.70% / 4.00%           E144: derived from the issuer's history
  unchanged: FCF0, net debt, divisor (shares), basis, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (115.32)
  store's newest period, today: --
```

Record: `reference/run-records/ALV-2026-10-27-check.json`

## AOS

**Status på listan:** INTAKE · tier – · fv_base –  
*Källa: `reference/AOS-STRIKE-2026-10-27-check.md`*

#### AOS -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/AOS.yaml` on the pre-registered growth view 4.00% / 0.00% / 7.00%, carried from AOS-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 64.35 -> **64.37** (bear 38.29, bull 85.58)
- **FCF0:** 555,858,333
- **net debt:** 463,600,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 570,300,000; annual FY2024 482,100,000; annual FY2025 584,800,000 = 545,733,333; acquisitions mean 54,233,333 NOT deducted -- valued as the deal programme (E142); + interest after tax 10,125,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -97,100,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 463,600,000 on the balance sheet + deals 0 + working capital neutralised -97,100,000 = 366,500,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/AOS.yaml; the registered view reference/growth-views/AOS.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.883: the weakest E140 year 482,100,000 over the mean 545,733,333 (E143(4))
- **deal programme (E142):** repeat buyer, A = 54,233,333/yr; ROIIC base 4.45% -- operating profit 515,266,667 (2015-2017 mean) -> 727,266,667 (2023-2025 mean); organic x1.351 (7 of 8 years at the view's 4.0%); after tax 25.0%: 23,510,154 on acquisitions 528,400,000 = 4.45%; bear 0.00% -- operating profit 577,900,000 (2017) -> 362,000,000 (2022); organic x1.217 (5 of 5 years at the view's 4.0%); after tax 25.0%: -255,827,784 on acquisitions 322,600,000 = -79.30%
- **bear:** flow 555,858,333 x level 0.883 x (1 + 0.00%) = FCF0 491,044,410; programme -340,520,147 (-2.47/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh); pension deficit after tax (E146) +1,850,000 (+0.01/sh) -> **38.29**
- **base:** flow 555,858,333 x level 1.000 x (1 + 4.00%) = FCF0 578,092,667; programme -219,556,421 (-1.59/sh); deals 0 credited back 0 at ROIIC 4.45% (+0.00/sh); pension deficit after tax (E146) +1,850,000 (+0.01/sh) -> **64.37**
- **bull:** flow 555,858,333 x level 1.000 x (1 + 7.00%) = FCF0 594,768,417; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh); pension deficit after tax (E146) +1,850,000 (+0.01/sh) -> **85.58**
- **events ledger** `reference/events/AOS.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge; already in the balance sheet: Leonard Valve
- **divisor:** 137,862,584
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 47,900,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 61.91; g* 3.56%
- **store's newest period:** --
- **anchors:** g* 3.56%; the base case returns ~9.8% a year at today's price against r 9.5%; tangible ROIC median 39.5% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 39.5% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 47% below its running peak
  - Q3 debt: **PASS** -- net debt 0.6x FCF0 against 3.0x
  - Q4 capital allocation: **FAIL** -- ROIIC 4.4% against r 9.5%
  - Q5 understandable: **PASS** -- A. O. Smith makes water heaters, boilers and water treatment products for homes and businesses; replacement need and installer loyalty bring repeat sales.

```
AOS — strike 2026-10-27   against AOS-2026-10-27-e142.json

                                  before           after     move
fv_base                            64.35           64.37    +0.0%
  bear                             38.28           38.29    +0.0%
  bull                             85.57           85.58    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 3.56%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (61.91)
  store's newest period, today: --
```

Record: `reference/run-records/AOS-2026-10-27-check.json`

## AUTO.L

**Status på listan:** WATCH-PRICED · tier 3 · fv_base 4.99  
*Källa: `reference/AUTO.L-STRIKE-2026-10-27-check.md`*

#### AUTO.L -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/AUTO.L.yaml` on the pre-registered growth view 3.00% / 0.00% / 6.00%, carried from AUTO.L-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** 2026-FY
- **fv_base:** 4.99 -> **4.99** (bear 3.68, bull 6.46)
- **FCF0:** 285
- **net debt:** 149 on the balance sheet of 2026-03-31
- **E140 FCF0:** mean of annual FY2024 277; annual FY2025 290; 2026-FY 287 = 285; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 0 at 0.25 (GB); - minority dividends 0
- **bridge (E140(3), deals at the HIGH end):** net debt 149 on the balance sheet + deals 0 + working capital neutralised 0 = 149
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/AUTO.L.yaml; the registered view reference/growth-views/AUTO.L.md
- **cycle and level (E143):** CYCLICAL (revenue fell -29% in a year): owner-earnings margin median 52.8%, last three 49.0%, lowest 47.0% -> base level x1.000, bear x0.958
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 285 x level 0.958 x (1 + 0.00%) = FCF0 273; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 107.05% (+0.00/sh) -> **3.68**
- **base:** flow 285 x level 1.000 x (1 + 3.00%) = FCF0 293; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 53.22% (+0.00/sh) -> **4.99**
- **bull:** flow 285 x level 1.000 x (1 + 6.00%) = FCF0 302; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **6.46**
- **events ledger** `reference/events/AUTO.L.yaml` dated 2026-10-27, cut at 2026-03-31: no deal in the bridge
- **divisor:** 862,666
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 2 is DEDUCTED -- principal 2 + lease interest 0; the lease liability 43 LEFT net debt
- **MBP (E90, tier 3):** 3.24 -> 3.24
- **close 2026-10-26:** 5.28; g* 3.66%
- **store's newest period:** 2026-03-31
- **anchors:** g* 3.66%; the base case returns ~9.1% a year at today's price against r 9.5%; tangible ROIC median 48.7% over 6 years (no goodwill row: on all invested capital) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 48.7% over 6 years (no goodwill row: on all invested capital) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 38% below its running peak
  - Q3 debt: **PASS** -- net debt 0.5x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Auto Trader runs the UK's largest automotive marketplace, earning mostly subscription revenue from car retailers and manufacturers.

```
AUTO.L — strike 2026-10-27   against AUTO.L-2026-10-27-e142.json

                                before           after     move
fv_base                           4.99            4.99    +0.0%
  bear                            3.68            3.68    +0.0%
  bull                            6.46            6.46    +0.0%
MBP (E90)  tier 3 -> 3            3.24            3.24    +0.0%
g*                                               3.66%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-03-31 -> 2026-03-31
  settled close           2026-10-26 -> 2026-10-26  (5.28)
  store's newest period, today: 2026-03-31
```

Record: `reference/run-records/AUTO.L-2026-10-27-check.json`

## BOUV.OL

**Status på listan:** inte på listan · tier – · fv_base –  
*Källa: `reference/BOUV.OL-STRIKE-2026-10-27-check.md`*

#### BOUV.OL -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/BOUV.OL.yaml` on the pre-registered growth view 3.00% / 2.00% / 6.00%, carried from BOUV.OL-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2
- **fv_base:** 54.42 -> **54.42** (bear 46.07, bull 69.34)
- **FCF0:** 335,307
- **net debt:** -159,733 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 304,182; annual FY2024 378,272; annual FY2025 323,468 = 335,307; acquisitions mean 6,571 NOT deducted -- valued as the deal programme (E142); + interest after tax 0 at 0.22 (NO); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -284,001 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -159,733 on the balance sheet + deals 0 + working capital neutralised -284,001 = -443,734
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/BOUV.OL.yaml; the registered view reference/growth-views/BOUV.OL.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.907: the weakest E140 year 304,182 over the mean 335,307 (E143(4))
- **deal programme (E142):** repeat buyer, A = 6,571/yr; ROIIC base 0.00% -- ROIIC NOT DERIVABLE (the history has no profit and capital pair); struck at ZERO, the conservative end: the programme at zero moves the value 0.8%, inside E106's 3.5% (E142(6)); bear 0.00% -- ROIIC NOT DERIVABLE (the history has no profit and capital pair); struck at ZERO, the conservative end: the programme at zero moves the value 0.8%, inside E106's 3.5% (E142(6))
- **bear:** flow 335,307 x level 0.907 x (1 + 2.00%) = FCF0 310,266; programme -45,408 (-0.44/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **46.07**
- **base:** flow 335,307 x level 1.000 x (1 + 3.00%) = FCF0 345,367; programme -47,659 (-0.46/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **54.42**
- **bull:** flow 335,307 x level 1.000 x (1 + 6.00%) = FCF0 355,426; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **69.34**
- **events ledger** `reference/events/BOUV.OL.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 103,695,316
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 89,629 is DEDUCTED -- principal 65,089 + lease interest 24,540; the lease liability 321,855 LEFT net debt
- **close 2026-10-26:** 51.70; g* 2.33%
- **store's newest period:** 2026-06-30
- **anchors:** g* 2.33%; the base case returns ~9.9% a year at today's price against r 9.5%; tangible ROIC no profit and capital years
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **n/a** -- no profit and capital years
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 3% below its running peak
  - Q3 debt: **PASS** -- net debt -1.3x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **FAIL** -- ROIIC 0.0% against r 9.5%
  - Q5 understandable: **PASS** -- Bouvet is a Scandinavian IT and digital communication consultancy serving private and public clients.

```
BOUV.OL — strike 2026-10-27   against BOUV.OL-2026-10-27-e142.json

                                  before           after     move
fv_base                            54.42           54.42    +0.0%
  bear                             46.07           46.07    +0.0%
  bull                             69.34           69.34    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 2.33%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-06-30 -> 2026-06-30
  settled close           2026-10-26 -> 2026-10-26  (51.70)
  store's newest period, today: 2026-06-30
```

Record: `reference/run-records/BOUV.OL-2026-10-27-check.json`

## CENTA

**Status på listan:** HELD · tier – · fv_base 40.19  
*Källa: `reference/CENTA-STRIKE-2026-10-27-check.md`*

#### CENTA -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/CENTA.yaml` on the pre-registered growth view 2.00% / -1.00% / 3.50%, carried from CENTA-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 40.19 -> **40.19** (bear 20.26, bull 54.70)
- **FCF0:** 216,612,667
- **net debt:** 196,348,000 on the balance sheet of 2026-06-27
- **E140 FCF0:** mean of annual FY2023 173,101,000; annual FY2024 187,542,000; annual FY2025 219,406,000 = 193,349,667; acquisitions mean 21,181,333 NOT deducted -- valued as the deal programme (E142); + interest after tax 24,609,000 at 0.25 (US); - minority dividends 1,346,000
- **bridge rolled (E140.1(3)):** 2025-09-27 -> 2026-06-27; year-to-date working capital -50,161,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 196,348,000 on the balance sheet + deals 840,000,000 + working capital neutralised -50,161,000 = 986,187,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/CENTA.yaml; the registered view reference/growth-views/CENTA.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.895: the weakest E140 year 173,101,000 over the mean 193,349,667 (E143(4))
- **deal programme (E142):** repeat buyer, A = 21,181,333/yr; ROIIC base 4.85% -- operating profit 125,635,000 (2015-2017 mean) -> 215,358,333 (2023-2025 mean); organic x1.139 (7 of 8 years at the view's 2.0%); after tax 25.0%: 54,205,982 on acquisitions 1,116,964,000 = 4.85%; bear 1.89% -- operating profit 152,068,000 (2019) -> 185,387,000 (2024); organic x1.073 (4 of 5 years at the view's 2.0%); after tax 25.0%: 16,641,193 on acquisitions 880,679,000 = 1.89%
- **bear:** flow 216,612,667 x level 0.895 x (1 + -1.00%) = FCF0 191,988,490; programme -101,602,582 (-1.64/sh); deals 840,000,000 credited back 167,079,246 at ROIIC 1.89% (+2.70/sh) -> **20.26**
- **base:** flow 216,612,667 x level 1.000 x (1 + 2.00%) = FCF0 220,944,920; programme -71,599,269 (-1.16/sh); deals 840,000,000 credited back 429,105,147 at ROIIC 4.85% (+6.93/sh) -> **40.19**
- **bull:** flow 216,612,667 x level 1.000 x (1 + 3.50%) = FCF0 224,194,110; programme 0 (+0.00/sh); deals 840,000,000 credited back 840,000,000 at ROIIC 9.50% (+13.56/sh) -> **54.70**
- **events ledger** `reference/events/CENTA.yaml` dated 2026-10-27, cut at 2026-06-27: TRIXIE 80% (EUR 340m cash + earn-out max EUR 60m + put on 20% pro rata EUR 100m = EUR 500m at 1.16) 580,000,000..580,000,000; Burpee (price NOT DISCLOSED; range is the session estimate: retail spend 242m implies ~110-130m wholesale sales) 90,000,000..260,000,000; already in the balance sheet: Champion USA (acquired); Pet Distribution contributed to Phillips partnership (cash 31m + note 5m received; 20% stake 26.1m kept)
- **divisor:** 61,947,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 215,535,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 39.13; g* 1.74%
- **store's newest period:** --
- **anchors:** g* 1.74%; the base case returns ~9.6% a year at today's price against r 9.5%; tangible ROIC median 12.6% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **FAIL** -- median 12.6% over 11 years against 15%
  - Q2 stability: **FAIL** -- owner earnings negative in [2022]; operating profit at most 29% below its running peak
  - Q3 debt: **FAIL** -- net debt 4.5x FCF0 against 3.0x
  - Q4 capital allocation: **FAIL** -- ROIIC 4.9% against r 9.5%
  - Q5 understandable: **PASS** -- Central Garden & Pet sells branded pet supplies and lawn and garden consumables to retailers and consumers; consumables and trusted brands drive repeat purchases.

```
CENTA — strike 2026-10-27   against CENTA-2026-10-27-e142.json

                                               before           after     move
fv_base                                         40.19           40.19    +0.0%
  bear                                          20.26           20.26    +0.0%
  bull                                          54.70           54.70    +0.0%
MBP (E90)  tier -- -> --                           --              --         
g*                                                              1.74%         
  fv_base, deals at LOW end (E140(3))                           41.53         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-09-27 -> 2025-09-27
  settled close           2026-10-26 -> 2026-10-26  (39.13)
  store's newest period, today: --
```

Record: `reference/run-records/CENTA-2026-10-27-check.json`

## CPRT

**Status på listan:** INTAKE · tier – · fv_base –  
*Källa: `reference/CPRT-STRIKE-2026-10-27-check.md`*

#### CPRT -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/CPRT.yaml` on the pre-registered growth view 6.00% / 1.00% / 10.00%, carried from CPRT-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2026
- **fv_base:** 26.96 -> **26.96** (bear 18.33, bull 35.84)
- **FCF0:** 1,059,154,750
- **net debt:** -4,487,076,000 on the balance sheet of 2026-07-31
- **E140 FCF0:** mean of annual FY2024 1,112,739,000; annual FY2025 1,141,735,000; annual FY2026 1,332,317,000 = 1,195,597,000; acquisitions mean 2,075,667 NOT deducted -- valued as the deal programme (E142); + interest after tax -136,442,250 at 0.25 (US); - minority dividends 0
- **bridge (E140(3), deals at the HIGH end):** net debt -4,487,076,000 on the balance sheet + deals 1,950,000,000 + working capital neutralised 0 = -2,537,076,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/CPRT.yaml; the registered view reference/growth-views/CPRT.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.931: the weakest E140 year 1,112,739,000 over the mean 1,195,597,000 (E143(4))
- **deal programme (E142):** repeat buyer, A = 2,075,667/yr; ROIIC base 23.70% -- operating profit 406,470,000 (2016) -> 716,475,000 (2019); organic x1.191 (3 of 3 years at the view's 6.0%); after tax 25.0%: 174,272,045 on capital added 735,455,000 = 23.70%; bear 23.70% -- operating profit 406,470,000 (2016) -> 716,475,000 (2019); organic x1.191 (3 of 3 years at the view's 6.0%); after tax 25.0%: 174,272,045 on capital added 735,455,000 = 23.70%
- **bear:** flow 1,059,154,750 x level 0.931 x (1 + 1.00%) = FCF0 995,610,080; programme 0 (+0.00/sh); deals 1,950,000,000 credited back 1,950,000,000 at ROIIC 23.70% (+2.04/sh) -> **18.33**
- **base:** flow 1,059,154,750 x level 1.000 x (1 + 6.00%) = FCF0 1,122,704,035; programme 0 (+0.00/sh); deals 1,950,000,000 credited back 1,950,000,000 at ROIIC 23.70% (+2.04/sh) -> **26.96**
- **bull:** flow 1,059,154,750 x level 1.000 x (1 + 10.00%) = FCF0 1,165,070,225; programme 0 (+0.00/sh); deals 1,950,000,000 credited back 1,950,000,000 at ROIIC 9.50% (+2.04/sh) -> **35.84**
- **events ledger** `reference/events/CPRT.yaml` dated 2026-10-27, cut at 2026-07-31: ACV Auctions ($10.50/share tender; aggregate per secondary sources ~1.9bn; low/high bound the share count) 1,800,000,000..1,950,000,000
- **divisor:** 956,860,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 85,641,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 29.15; g* 7.12%
- **store's newest period:** --
- **anchors:** g* 7.12%; the base case returns ~8.9% a year at today's price against r 9.5%; tangible ROIC median 31.3% over 4 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 31.3% over 4 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 3% below its running peak
  - Q3 debt: **PASS** -- net debt -2.3x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **PASS** -- ROIIC 23.7% against r 9.5%
  - Q5 understandable: **PASS** -- Copart runs online auctions of salvage and used vehicles for insurers and sellers, with buyers worldwide; its yard network and bidder base keep sellers coming.

```
CPRT — strike 2026-10-27   against CPRT-2026-10-27-e142.json

                                               before           after     move
fv_base                                         26.96           26.96    +0.0%
  bear                                          18.33           18.33    +0.0%
  bull                                          35.84           35.84    +0.0%
MBP (E90)  tier -- -> --                           --              --         
g*                                                              7.12%         
  fv_base, deals at LOW end (E140(3))                           26.96         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-07-31 -> 2026-07-31
  settled close           2026-10-26 -> 2026-10-26  (29.15)
  store's newest period, today: --
```

Record: `reference/run-records/CPRT-2026-10-27-check.json`

## CROX

**Status på listan:** DROPPED · tier – · fv_base –  
*Källa: `reference/CROX-STRIKE-2026-10-27-check.md`*

#### CROX -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/CROX.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / -0.07% / 4.00%, carried from CROX-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 171.83 -> **171.83** (bear -18.94, bull 250.10)
- **FCF0:** 784,693,250
- **net debt:** 1,137,382,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 657,093,000; annual FY2024 834,033,000; annual FY2025 664,308,000 = 718,478,000; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 66,215,250 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -197,438,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 1,137,382,000 on the balance sheet + deals 0 + working capital neutralised -197,438,000 = 939,944,000
- **growth (E144):** E144: organic 10.12%/yr over 8 years, last five 16.74% (2016-2025, 8 of them PROXY from deal-free years); owner earnings per share 53.80%/yr; cap 4%; worst 3-year -0.07%, best 5-year 18.53%
- **cycle and level (E143):** CYCLICAL (operating margin fell from 29.5% to 3.7%): owner-earnings margin median 14.0%, last three 19.8%, lowest -0.8% -> base level x0.709, bear x0.000
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 784,693,250 x level 0.000 x (1 + -0.07%) = FCF0 0; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **-18.94**
- **base:** flow 784,693,250 x level 0.709 x (1 + 4.00%) = FCF0 578,653,537; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 21.65% (+0.00/sh) -> **171.83**
- **bull:** flow 784,693,250 x level 1.000 x (1 + 4.00%) = FCF0 816,080,980; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **250.10**
- **events ledger** `reference/events/CROX.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 49,628,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 381,544,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 118.85; g* 0.10%
- **store's newest period:** --
- **anchors:** g* 0.10%; the base case returns ~12.1% a year at today's price against r 9.5%; tangible ROIC median 33.4% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 33.4% over 11 years against 15%
  - Q2 stability: **FAIL** -- owner earnings negative in [2015]; operating profit at most 86% below its running peak, not regained within three years after [2025]
  - Q3 debt: **PASS** -- net debt 1.6x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Crocs sells casual footwear and accessories (Crocs and HEYDUDE brands) to consumers worldwide; comfort, price and brand appeal bring repeat buyers.

```
CROX — strike 2026-10-27   against CROX-2026-10-27-e142.json

                                  before           after     move
fv_base                           171.83          171.83    +0.0%
  bear                            -18.94          -18.94    +0.0%
  bull                            250.10          250.10    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 0.10%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (118.85)
  store's newest period, today: --
```

Record: `reference/run-records/CROX-2026-10-27-check.json`

## CTSH

**Status på listan:** HELD · tier 3 · fv_base 73.96  
*Källa: `reference/CTSH-STRIKE-2026-10-27-check.md`*

#### CTSH -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/CTSH.yaml` on the pre-registered growth view 4.00% / 0.00% / 7.00%, carried from CTSH-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 73.82 -> **73.96** (bear 44.15, bull 109.95)
- **FCF0:** 2,329,416,667
- **net debt:** 782,000,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 2,014,000,000; annual FY2024 2,150,000,000; annual FY2025 2,741,000,000 = 2,301,666,667; acquisitions mean 674,666,667 NOT deducted -- valued as the deal programme (E142); + interest after tax 27,750,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -984,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 782,000,000 on the balance sheet + deals 300,000,000 + working capital neutralised -984,000,000 = 98,000,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/CTSH.yaml; the registered view reference/growth-views/CTSH.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.875: the weakest E140 year 2,014,000,000 over the mean 2,301,666,667 (E143(4))
- **deal programme (E142):** repeat buyer, A = 674,666,667/yr; ROIIC base -1.90% -- operating profit 2,304,000,000 (2015-2017 mean) -> 2,990,000,000 (2023-2025 mean); organic x1.369 (8 of 8 years at the view's 4.0%); after tax 25.0%: -122,387,319 on acquisitions 6,428,000,000 = -1.90%; bear 0.00% -- operating profit 2,801,000,000 (2018) -> 2,689,000,000 (2023); organic x1.217 (5 of 5 years at the view's 4.0%); after tax 25.0%: -539,133,585 on acquisitions 3,486,000,000 = -15.47%
- **bear:** flow 2,329,416,667 x level 0.875 x (1 + 0.00%) = FCF0 2,038,281,752; programme -4,236,095,740 (-9.09/sh); deals 300,000,000 credited back 0 at ROIIC 0.00% (+0.00/sh); pension deficit after tax (E146) +65,000,000 (+0.14/sh) -> **44.15**
- **base:** flow 2,329,416,667 x level 1.000 x (1 + 4.00%) = FCF0 2,422,593,333; programme -5,137,383,634 (-11.02/sh); deals 300,000,000 credited back 0 at ROIIC -1.90% (+0.00/sh); pension deficit after tax (E146) +65,000,000 (+0.14/sh) -> **73.96**
- **bull:** flow 2,329,416,667 x level 1.000 x (1 + 7.00%) = FCF0 2,492,475,833; programme 0 (+0.00/sh); deals 300,000,000 credited back 300,000,000 at ROIIC 9.50% (+0.64/sh); pension deficit after tax (E146) +65,000,000 (+0.14/sh) -> **109.95**
- **events ledger** `reference/events/CTSH.yaml` dated 2026-10-27, cut at 2026-06-30: DyFlex Solutions (Australia; price NOT DISCLOSED; range is the session estimate) 50,000,000..300,000,000; already in the balance sheet: 3Cloud; Astreya Partners (incl. contingent 25m)
- **divisor:** 466,000,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 534,000,000 LEFT net debt; finance leases stay in net debt
- **MBP (E90, tier 3):** 55.37 -> 48.07  -- THE TIER MOVED 2 -> 3
- **close 2026-10-26:** 69.34; g* 3.28%
- **store's newest period:** 2026-06-30
- **anchors:** g* 3.28%; the base case returns ~9.9% a year at today's price against r 9.5%; tangible ROIC median 35.6% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 35.6% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 25% below its running peak
  - Q3 debt: **PASS** -- net debt 0.0x FCF0 against 3.0x
  - Q4 capital allocation: **FAIL** -- ROIIC -1.9% against r 9.5%
  - Q5 understandable: **PASS** -- Cognizant sells IT consulting, systems integration and outsourcing services to large enterprises; embedded delivery teams keep clients renewing.

```
CTSH — strike 2026-10-27   against CTSH-2026-10-27-e142.json

                                               before           after     move
fv_base                                         73.82           73.96    +0.2%
  bear                                          44.01           44.15    +0.3%
  bull                                         109.81          109.95    +0.1%
MBP (E90)  tier 2 -> 3                          55.37           48.07   -13.2%
  of which the tier                                                     -13.3%
g*                                                              3.28%         
  fv_base, deals at LOW end (E140(3))                           74.50         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (69.34)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/CTSH-2026-10-27-check.json`

## DECK

**Status på listan:** WATCH-GATED · tier – · fv_base –  
*Källa: `reference/DECK-STRIKE-2026-10-27-check.md`*

#### DECK -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/DECK.yaml` on the growth DERIVED from the issuer's history (E144) 2.94% / 2.52% / 8.00%, carried from DECK-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2026
- **fv_base:** 85.05 -> **85.05** (bear 26.83, bull 160.03)
- **FCF0:** 860,201,083
- **net debt:** -1,565,799,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2024 728,388,000; annual FY2025 895,690,000; annual FY2026 1,093,962,000 = 906,013,333; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax -45,812,250 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2026-03-31 -> 2026-06-30; year-to-date working capital -138,667,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -1,565,799,000 on the balance sheet + deals 0 + working capital neutralised -138,667,000 = -1,704,466,000
- **growth (E144):** E144: organic 11.30%/yr over 10 years, last five 16.54% (2017-2026, 10 of them PROXY from deal-free years); owner earnings per share 2.94%/yr; cap 8%; worst 3-year 2.52%, best 5-year 18.51%
- **cycle and level (E143):** CYCLICAL (operating margin fell from 8.6% to -0.1%): owner-earnings margin median 15.4%, last three 20.4%, lowest 3.2% -> base level x0.752, bear x0.156
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 860,201,083 x level 0.156 x (1 + 2.52%) = FCF0 137,261,905; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 56.53% (+0.00/sh) -> **26.83**
- **base:** flow 860,201,083 x level 0.752 x (1 + 2.94%) = FCF0 666,229,199; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -- (+0.00/sh) -> **85.05**
- **bull:** flow 860,201,083 x level 1.000 x (1 + 8.00%) = FCF0 929,017,170; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **160.03**
- **events ledger** `reference/events/DECK.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 138,559,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 472,334,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 80.37; g* 2.15%
- **store's newest period:** 2026-06-30
- **anchors:** g* 2.15%; the base case returns ~10.0% a year at today's price against r 9.5%; tangible ROIC median 62.2% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 62.2% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 101% below its running peak, regained within three years
  - Q3 debt: **PASS** -- net debt -2.6x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Deckers sells HOKA, UGG and Teva footwear and apparel through retailers and directly to consumers; brand strength brings repeat purchases.

```
DECK — strike 2026-10-27   against DECK-2026-10-27-e142.json

                                  before           after     move
fv_base                            85.05           85.05    +0.0%
  bear                             26.83           26.83    +0.0%
  bull                            160.03          160.03    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 2.15%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-03-31 -> 2026-03-31
  settled close           2026-10-26 -> 2026-10-26  (80.37)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/DECK-2026-10-27-check.json`

## GDDY

**Status på listan:** WATCH-PRICED · tier 3 · fv_base 79.99  
*Källa: `reference/GDDY-STRIKE-2026-10-27-check.md`*

#### GDDY -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/GDDY.yaml` on the pre-registered growth view 3.00% / 1.00% / 8.00%, carried from GDDY-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 79.99 -> **79.99** (bear 27.90, bull 132.86)
- **FCF0:** 850,250,000
- **net debt:** 2,618,900,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 440,200,000; annual FY2024 791,000,000; annual FY2025 1,062,600,000 = 764,600,000; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 85,650,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital 209,100,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 2,618,900,000 on the balance sheet + deals 0 + working capital neutralised 209,100,000 = 2,828,000,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/GDDY.yaml; the registered view reference/growth-views/GDDY.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.576: the weakest E140 year 440,200,000 over the mean 764,600,000 (E143(4))
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 850,250,000 x level 0.576 x (1 + 1.00%) = FCF0 494,406,030; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 6.42% (+0.00/sh) -> **27.90**
- **base:** flow 850,250,000 x level 1.000 x (1 + 3.00%) = FCF0 875,757,500; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 6.42% (+0.00/sh) -> **79.99**
- **bull:** flow 850,250,000 x level 1.000 x (1 + 8.00%) = FCF0 918,270,000; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **132.86**
- **events ledger** `reference/events/GDDY.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 130,994,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 82,300,000 LEFT net debt; finance leases stay in net debt
- **MBP (E90, tier 3):** 51.99 -> 51.99
- **close 2026-10-26:** 109.82; g* 6.07%
- **store's newest period:** 2026-06-30
- **anchors:** g* 6.07%; the base case returns ~7.9% a year at today's price against r 9.5%; tangible ROIC median above any rate (tangible capital at or below zero) over 4 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median above any rate (tangible capital at or below zero) over 4 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 0% below its running peak
  - Q3 debt: **PASS** -- net debt 3.2x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- GoDaddy sells domains, hosting, website and commerce tools to small businesses and individuals; subscriptions and switching costs keep them.

```
GDDY — strike 2026-10-27   against GDDY-2026-10-27-e142.json

                                before           after     move
fv_base                          79.99           79.99    +0.0%
  bear                           27.90           27.90    +0.0%
  bull                          132.86          132.86    +0.0%
MBP (E90)  tier 3 -> 3           51.99           51.99    +0.0%
g*                                               6.07%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (109.82)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/GDDY-2026-10-27-check.json`

## HRB

**Status på listan:** WATCH-GATED · tier – · fv_base –  
*Källa: `reference/HRB-STRIKE-2026-10-27-check.md`*

#### HRB -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/HRB.yaml` on the pre-registered growth view 2.00% / -4.00% / 5.00%, carried from HRB-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2026
- **fv_base:** 68.38 -> **68.38** (bear -4.65, bull 96.54)
- **FCF0:** 711,559,333
- **net debt:** 725,187,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2024 689,188,000; annual FY2025 584,803,000; annual FY2026 688,049,000 = 654,013,333; acquisitions mean 45,505,000 NOT deducted -- valued as the deal programme (E142); + interest after tax 57,546,000 at 0.25 (US); - minority dividends 0
- **bridge (E140(3), deals at the HIGH end):** net debt 725,187,000 on the balance sheet + deals 0 + working capital neutralised 0 = 725,187,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/HRB.yaml; the registered view reference/reviews/HRB/2026-09-17.yaml (registered 2026-09-18 20:03:01+02:00)
- **cycle and level (E143):** CYCLICAL (revenue fell -15% in a year; operating margin fell from 24.0% to 3.5%): owner-earnings margin median 16.8%, last three 17.8%, lowest 1.0% -> base level x0.945, bear x0.058
- **deal programme (E142):** repeat buyer, A = 45,505,000/yr; ROIIC base 5.15% -- operating profit 706,261,000 (2016-2018 mean) -> 878,472,333 (2024-2026 mean); organic x1.172 (8 of 8 years at the view's 2.0%); after tax 25.0%: 38,231,255 on acquisitions 742,860,000 = 5.15%; bear 0.00% -- operating profit 869,192,000 (2021) -> 934,499,000 (2026); organic x1.104 (5 of 5 years at the view's 2.0%); after tax 25.0%: -18,869,401 on acquisitions 220,681,000 = -8.55%
- **bear:** flow 711,559,333 x level 0.058 x (1 + -4.00%) = FCF0 39,736,426; programme -236,781,518 (-1.84/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **-4.65**
- **base:** flow 711,559,333 x level 0.945 x (1 + 2.00%) = FCF0 685,947,295; programme -144,104,786 (-1.12/sh); deals 0 credited back 0 at ROIIC 5.15% (+0.00/sh) -> **68.38**
- **bull:** flow 711,559,333 x level 1.000 x (1 + 5.00%) = FCF0 747,137,300; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **96.54**
- **events ledger** `reference/events/HRB.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 128,866,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 610,860,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 50.06; g* -1.40%
- **store's newest period:** --
- **anchors:** g* -1.40%; the base case returns ~11.8% a year at today's price against r 9.5%; tangible ROIC median above any rate (tangible capital at or below zero) over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median above any rate (tangible capital at or below zero) over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 88% below its running peak, regained within three years
  - Q3 debt: **PASS** -- net debt 1.1x FCF0 against 3.0x
  - Q4 capital allocation: **FAIL** -- ROIIC 5.1% against r 9.5%
  - Q5 understandable: **PASS** -- H&R Block prepares taxes (assisted and DIY) and offers financial and small-business services to consumers; trust and annual habit bring clients back.

```
HRB — strike 2026-10-27   against HRB-2026-10-27-e142.json

                                  before           after     move
fv_base                            68.38           68.38    +0.0%
  bear                             -4.65           -4.65    +0.0%
  bull                             96.54           96.54    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                -1.40%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-06-30 -> 2026-06-30
  settled close           2026-10-26 -> 2026-10-26  (50.06)
  store's newest period, today: --
```

Record: `reference/run-records/HRB-2026-10-27-check.json`

## LIAB.ST

**Status på listan:** DROPPED · tier 2 · fv_base 66.68  
*Källa: `reference/LIAB.ST-STRIKE-2026-10-27-check.md`*

#### LIAB.ST -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/LIAB.ST.yaml` on the growth DERIVED from the issuer's history (E144) 1.33% / -3.00% / 4.00%, carried from LIAB.ST-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2
- **fv_base:** 65.93 -> **66.68** (bear -5.29, bull 123.14)
- **FCF0:** 726
- **net debt:** 3,126 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 637; annual FY2024 491; annual FY2025 572 = 567; acquisitions mean 702 NOT deducted -- valued as the deal programme (E142); + interest after tax 160 at 0.206 (SE); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -197 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 3,126 on the balance sheet + deals 30 + working capital neutralised -197 = 2,959
- **growth (E144):** E144: organic 1.91%/yr over 10 years, last five 1.33% (2016-2025); owner earnings per share 17.66%/yr; cap 4%; worst 3-year -6.03%, best 5-year 6.12%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.866: the weakest E140 year 491 over the mean 567 (E143(4))
- **deal programme (E142):** repeat buyer, A = 702/yr; ROIIC base 5.73% -- adjusted operating profit 552,000,000 (2016-2018 mean) -> 1,083,000,000 (2023-2025 mean); organic x1.163; after tax 20.6%: 349,993,844 on capital added 6,108,666,667 = 5.73%; bear 0.82% -- adjusted operating profit 916,000,000 (2020) -> 1,027,000,000 (2025); organic x1.068; after tax 20.6%: 38,599,477 on capital added 4,695,000,000 = 0.82%
- **bear:** flow 726 x level 0.866 x (1 + -3.00%) = FCF0 610; programme -3,495 (-45.37/sh); deals 30 credited back 3 at ROIIC 0.82% (+0.03/sh); pension deficit after tax (E146) +58 (+0.75/sh) -> **-5.29**
- **base:** flow 726 x level 1.000 x (1 + 1.33%) = FCF0 736; programme -1,864 (-24.20/sh); deals 30 credited back 18 at ROIIC 5.73% (+0.23/sh); pension deficit after tax (E146) +58 (+0.75/sh) -> **66.68**
- **bull:** flow 726 x level 1.000 x (1 + 4.00%) = FCF0 755; programme 0 (+0.00/sh); deals 30 credited back 30 at ROIIC 9.50% (+0.39/sh); pension deficit after tax (E146) +58 (+0.75/sh) -> **123.14**
- **events ledger** `reference/events/LIAB.ST.yaml` dated 2026-10-27, cut at 2026-06-30: Connaught Ventilation Supplies (IE, sales ~EUR 2m; price NOT DISCLOSED, range estimate) 10..30; already in the balance sheet: Lindab SRL Romania divested (SEK 42m, instalments over 3 years)
- **divisor:** 77
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 452 is DEDUCTED -- principal 386 + lease interest 66; the lease liability 1,410 LEFT net debt
- **MBP (E90, tier 2):** 49.45 -> 50.01
- **close 2026-10-26:** 129.50; g* 6.52%
- **store's newest period:** 2026-06-30
- **anchors:** g* 6.52%; the base case returns ~7.4% a year at today's price against r 9.5%; tangible ROIC median 8.5% over 10 years (no goodwill row: on all invested capital) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **FAIL** -- median 8.5% over 10 years (no goodwill row: on all invested capital) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; adjusted operating profit at most 24% below its running peak
  - Q3 debt: **FAIL** -- net debt 4.0x FCF0 against 3.0x
  - Q4 capital allocation: **FAIL** -- ROIIC 5.7% against r 9.5%
  - Q5 understandable: **PASS** -- Lindab makes and distributes ventilation and indoor-climate products, sold mainly to installers in Europe.

```
LIAB.ST — strike 2026-10-27   against LIAB.ST-2026-10-27-e142.json

                                               before           after     move
fv_base                                         65.93           66.68    +1.1%
  bear                                          -6.03           -5.29   -12.4%
  bull                                         122.39          123.14    +0.6%
MBP (E90)  tier 2 -> 2                          49.45           50.01    +1.1%
g*                                                              6.52%         
  fv_base, deals at LOW end (E140(3))                           66.78         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-06-30 -> 2026-06-30
  settled close           2026-10-26 -> 2026-10-26  (129.50)
  store's newest period, today: 2026-06-30
```

Record: `reference/run-records/LIAB.ST-2026-10-27-check.json`

## LII

**Status på listan:** INTAKE · tier – · fv_base –  
*Källa: `reference/LII-STRIKE-2026-10-27-check.md`*

#### LII -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/LII.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / -1.82% / 4.00%, carried from LII-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 309.55 -> **309.69** (bear 92.28, bull 309.69)
- **FCF0:** 708,375,000
- **net debt:** 1,549,900,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 426,200,000; annual FY2024 704,500,000; annual FY2025 902,400,000 = 677,700,000; acquisitions mean 213,300,000 NOT deducted -- valued as the deal programme (E142); + interest after tax 30,675,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -269,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 1,549,900,000 on the balance sheet + deals 205,000,000 + working capital neutralised -269,000,000 = 1,485,900,000
- **growth (E144):** E144: organic 4.50%/yr over 7 years, last five 4.21% (2016-2022, 7 of them PROXY from deal-free years); owner earnings per share 14.51%/yr; cap 4%; worst 3-year -1.82%, best 5-year 4.21%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.629: the weakest E140 year 426,200,000 over the mean 677,700,000 (E143(4))
- **deal programme (E142):** repeat buyer, A = 213,300,000/yr; ROIIC base 39.67% -- operating profit 409,766,667 (2015-2017 mean) -> 957,800,000 (2023-2025 mean); organic x1.401 (2 of 8 years at the view's 4.0%); after tax 25.0%: 287,657,724 on capital added 725,200,000 = 39.67%; bear 8.28% -- operating profit 494,500,000 (2017) -> 656,200,000 (2022); organic x1.229; after tax 25.0%: 36,389,869 on capital added 439,500,000 = 8.28%
- **bear:** flow 708,375,000 x level 0.629 x (1 + -1.82%) = FCF0 437,397,351; programme -157,841,748 (-4.54/sh); deals 205,000,000 credited back 178,670,094 at ROIIC 8.28% (+5.13/sh); pension deficit after tax (E146) +5,025,000 (+0.14/sh) -> **92.28**
- **base:** flow 708,375,000 x level 1.000 x (1 + 4.00%) = FCF0 736,710,000; programme 0 (+0.00/sh); deals 205,000,000 credited back 205,000,000 at ROIIC 39.67% (+5.89/sh); pension deficit after tax (E146) +5,025,000 (+0.14/sh) -> **309.69**
- **bull:** flow 708,375,000 x level 1.000 x (1 + 4.00%) = FCF0 736,710,000; programme 0 (+0.00/sh); deals 205,000,000 credited back 205,000,000 at ROIIC 9.50% (+5.89/sh); pension deficit after tax (E146) +5,025,000 (+0.14/sh) -> **309.69**
- **events ledger** `reference/events/LII.yaml` dated 2026-10-27, cut at 2026-06-30: Heat Controller 205,000,000..205,000,000
- **divisor:** 34,800,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 443,400,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 365.64; g* 5.79%
- **store's newest period:** --
- **anchors:** g* 5.79%; the base case returns ~8.5% a year at today's price against r 9.5%; tangible ROIC median 712.5% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 712.5% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 27% below its running peak
  - Q3 debt: **PASS** -- net debt 2.0x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- ROIIC 39.7% against r 9.5%
  - Q5 understandable: **PASS** -- Lennox makes heating, cooling and refrigeration equipment sold through dealers and distributors to homes and buildings; installer relationships and replacement demand recur.

```
LII — strike 2026-10-27   against LII-2026-10-27-e142.json

                                               before           after     move
fv_base                                        309.55          309.69    +0.0%
  bear                                          92.14           92.28    +0.2%
  bull                                         309.55          309.69    +0.0%
MBP (E90)  tier -- -> --                           --              --         
g*                                                              5.79%         
  fv_base, deals at LOW end (E140(3))                          309.69         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (365.64)
  store's newest period, today: --
```

Record: `reference/run-records/LII-2026-10-27-check.json`

## LOPE

**Status på listan:** DROPPED · tier – · fv_base –  
*Källa: `reference/LOPE-STRIKE-2026-10-27-check.md`*

#### LOPE -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/LOPE.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / -2.14% / 4.00%, carried from LOPE-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 136.56 -> **136.56** (bear 4.96, bull 146.29)
- **FCF0:** 217,789,000
- **net debt:** -171,060,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 194,041,000; annual FY2024 227,536,000; annual FY2025 231,790,000 = 217,789,000; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 0 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital 40,997,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -171,060,000 on the balance sheet + deals 0 + working capital neutralised 40,997,000 = -130,063,000
- **growth (E144):** E144: organic 4.51%/yr over 8 years, last five 5.55% (2016-2025, 8 of them PROXY from deal-free years); owner earnings per share 22.09%/yr; cap 4%; worst 3-year -2.14%, best 5-year 5.55%
- **cycle and level (E143):** CYCLICAL (revenue fell -13% in a year): owner-earnings margin median 20.7%, last three 22.3%, lowest -2.5% -> base level x0.931, bear x0.000
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 217,789,000 x level 0.000 x (1 + -2.14%) = FCF0 0; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **4.96**
- **base:** flow 217,789,000 x level 0.931 x (1 + 4.00%) = FCF0 210,913,830; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -10.06% (+0.00/sh) -> **136.56**
- **bull:** flow 217,789,000 x level 1.000 x (1 + 4.00%) = FCF0 226,500,560; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **146.29**
- **events ledger** `reference/events/LOPE.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 26,221,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 104,212,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 160.71; g* 6.01%
- **store's newest period:** --
- **anchors:** g* 6.01%; the base case returns ~8.4% a year at today's price against r 9.5%; tangible ROIC median 27.0% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 27.0% over 11 years against 15%
  - Q2 stability: **FAIL** -- owner earnings negative in [2015]; operating profit at most 16% below its running peak
  - Q3 debt: **PASS** -- net debt -0.6x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Grand Canyon Education provides services to universities, chiefly Grand Canyon University, for a share of revenue; long-term contracts keep the partnership.

```
LOPE — strike 2026-10-27   against LOPE-2026-10-27-e142.json

                                  before           after     move
fv_base                           136.56          136.56    +0.0%
  bear                              4.96            4.96    +0.0%
  bull                            146.29          146.29    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 6.01%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (160.71)
  store's newest period, today: --
```

Record: `reference/run-records/LOPE-2026-10-27-check.json`

## MC.PA

**Status på listan:** WATCH-PRICED · tier – · fv_base 392.95  
*Källa: `reference/MC.PA-STRIKE-2026-10-27-check.md`*

#### MC.PA -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/MC.PA.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / 3.22% / 4.00%, carried from MC.PA-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** 2025-FY
- **fv_base:** 392.62 -> **392.95** (bear 239.77, bull 398.90)
- **FCF0:** 11,975
- **net debt:** 8,924 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 12,564; annual FY2024 12,212; 2025-FY 11,744 = 12,173; acquisitions mean 386 NOT deducted -- valued as the deal programme (E142); + interest after tax 215 at 0.258 (FR); - minority dividends 414
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -2,446 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 8,924 on the balance sheet + deals 0 + working capital neutralised -2,446 = 6,478
- **growth (E144):** E144: organic 9.53%/yr over 5 years, last five 9.53% (2016-2025, 2 of them PROXY from deal-free years); owner earnings per share not derivable; cap 4%; worst 3-year 3.22%, best 5-year 9.53%
- **cycle and level (E143):** CYCLICAL (revenue fell -17% in a year): owner-earnings margin median 15.7%, last three 15.4%, lowest 10.3% -> base level x1.000, bear x0.670
- **deal programme (E142):** repeat buyer, A = 386/yr; ROIIC base 0.00% -- ROIIC NOT DERIVABLE (the history has no profit and capital pair); struck at ZERO, the conservative end: the programme at zero moves the value 1.5%, inside E106's 3.5% (E142(6)); bear 0.00% -- ROIIC NOT DERIVABLE (the history has no profit and capital pair); struck at ZERO, the conservative end: the programme at zero moves the value 1.5%, inside E106's 3.5% (E142(6))
- **bear:** flow 11,975 x level 0.670 x (1 + 3.22%) = FCF0 8,279; programme -2,832 (-5.72/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh); pension deficit after tax (E146) +165 (+0.33/sh) -> **239.77**
- **base:** flow 11,975 x level 1.000 x (1 + 4.00%) = FCF0 12,453; programme -2,942 (-5.94/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh); pension deficit after tax (E146) +165 (+0.33/sh) -> **392.95**
- **bull:** flow 11,975 x level 1.000 x (1 + 4.00%) = FCF0 12,453; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh); pension deficit after tax (E146) +165 (+0.33/sh) -> **398.90**
- **events ledger** `reference/events/MC.PA.yaml` dated 2026-10-27, cut at 2026-06-30: Divestments pending at the 2026-06-30 cut (DFS Greater China completed March 2026 and is in the H1 balance sheet): DFS LA/SF concessions and DFS Okinawa (completion planned H2 2026, H1 report p.28), Marc Jacobs to WHP (agreement May 2026; ~USD 850-925m press), DFS Japan/Indonesia stakes -- proceeds NOT VERIFIED; credited only at the low end -1,200..0; already in the balance sheet: Minority-interest purchases (H1 2026)
- **divisor:** 494,957,592
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 2,974 is DEDUCTED -- principal 2,974 + lease interest 0; the lease liability 16,261 LEFT net debt
- **close 2026-10-26:** 385.40; g* 3.78%
- **store's newest period:** 2026-06-30
- **anchors:** g* 3.78%; the base case returns ~9.6% a year at today's price against r 9.5%; tangible ROIC no profit and capital years
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **n/a** -- no profit and capital years
  - Q2 stability: **PASS** -- owner earnings negative in no year; adjusted operating profit at most 28% below its running peak
  - Q3 debt: **PASS** -- net debt 0.5x FCF0 against 3.0x
  - Q4 capital allocation: **FAIL** -- ROIIC 0.0% against r 9.5%
  - Q5 understandable: **PASS** -- LVMH is a luxury group with six business groups: wines and spirits, fashion and leather goods, perfumes and cosmetics, watches and jewelry, selective retailing, and other.

```
MC.PA — strike 2026-10-27   against MC.PA-2026-10-27-e142.json

                                               before           after     move
fv_base                                        392.62          392.95    +0.1%
  bear                                         239.43          239.77    +0.1%
  bull                                         398.56          398.90    +0.1%
MBP (E90)  tier -- -> --                           --              --         
g*                                                              3.78%         
  fv_base, deals at LOW end (E140(3))                          395.38         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (385.40)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/MC.PA-2026-10-27-check.json`

## MEKKO.HE

**Status på listan:** WATCH-GATED · tier – · fv_base –  
*Källa: `reference/MEKKO.HE-STRIKE-2026-10-27-check.md`*

#### MEKKO.HE -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/MEKKO.HE.yaml` on the pre-registered growth view 5.00% / 3.00% / 10.00%, carried from MEKKO.HE-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 10.95 -> **10.95** (bear 9.25, bull 16.33)
- **FCF0:** 23
- **net debt:** -21 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 22; annual FY2024 22; annual FY2025 22 = 22; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 1 at 0.2 (FI); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -4 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -21 on the balance sheet + deals 0 + working capital neutralised -4 = -25
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/MEKKO.HE.yaml; the registered view reference/growth-views/MEKKO.HE.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.987: the weakest E140 year 22 over the mean 22 (E143(4))
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 23 x level 0.987 x (1 + 3.00%) = FCF0 23; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -- (+0.00/sh) -> **9.25**
- **base:** flow 23 x level 1.000 x (1 + 5.00%) = FCF0 24; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -- (+0.00/sh) -> **10.95**
- **bull:** flow 23 x level 1.000 x (1 + 10.00%) = FCF0 25; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **16.33**
- **events ledger** `reference/events/MEKKO.HE.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 40,509,915
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 10 is DEDUCTED -- principal 9 + lease interest 1; the lease liability 29 LEFT net debt
- **close 2026-10-26:** 9.17; g* 2.74%
- **store's newest period:** --
- **anchors:** g* 2.74%; the base case returns ~10.9% a year at today's price against r 9.5%; tangible ROIC no profit and capital years
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **n/a** -- no profit and capital years
  - Q2 stability: **PASS** -- owner earnings negative in no year; adjusted operating profit at most 3% below its running peak
  - Q3 debt: **PASS** -- net debt -1.1x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Marimekko is a Finnish design company selling its own-print clothing, bags, accessories and home decor.

```
MEKKO.HE — strike 2026-10-27   against MEKKO.HE-2026-10-27-e142.json

                                  before           after     move
fv_base                            10.95           10.95    +0.0%
  bear                              9.25            9.25    +0.0%
  bull                             16.33           16.33    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 2.74%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (9.17)
  store's newest period, today: --
```

Record: `reference/run-records/MEKKO.HE-2026-10-27-check.json`

## MUSA

**Status på listan:** DROPPED · tier – · fv_base –  
*Källa: `reference/MUSA-STRIKE-2026-10-27-check.md`*

#### MUSA -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/MUSA.yaml` on the pre-registered growth view 2.00% / 1.00% / 3.00%, carried from MUSA-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 268.53 -> **268.53** (bear 201.24, bull 301.79)
- **FCF0:** 491,875,000
- **net debt:** 2,065,100,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 491,800,000; annual FY2024 368,400,000; annual FY2025 365,900,000 = 408,700,000; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 83,175,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital 33,700,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 2,065,100,000 on the balance sheet + deals 0 + working capital neutralised 33,700,000 = 2,098,800,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/MUSA.yaml; the registered view reference/growth-views/MUSA.md
- **cycle and level (E143):** not cyclical on profit (revenue is a pass-through: E141 decision 2026-10-27: Murphy USA sells motor fuel at the pump price; its revenue moves with the price of gasoline (2020 -20%, 2022 +), not with how much business it does, so revenue growth and margin on revenue measure neither growth nor the cycle); bear level x0.895: the weakest E140 year 365,900,000 over the mean 408,700,000 (E143(4))
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 491,875,000 x level 0.895 x (1 + 1.00%) = FCF0 444,768,371; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 11.85% (+0.00/sh) -> **201.24**
- **base:** flow 491,875,000 x level 1.000 x (1 + 2.00%) = FCF0 501,712,500; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 47.10% (+0.00/sh) -> **268.53**
- **bull:** flow 491,875,000 x level 1.000 x (1 + 3.00%) = FCF0 506,631,250; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **301.79**
- **events ledger** `reference/events/MUSA.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 18,552,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 576,300,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 539.14; g* 8.40%
- **store's newest period:** --
- **anchors:** g* 8.40%; the base case returns ~6.6% a year at today's price against r 9.5%; tangible ROIC median 67.6% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 67.6% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 31% below its running peak
  - Q3 debt: **FAIL** -- net debt 4.2x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Murphy USA sells motor fuel and convenience merchandise to drivers at about 1,800 stores, often next to Walmart; low prices and convenience bring repeat visits.

```
MUSA — strike 2026-10-27   against MUSA-2026-10-27-e142.json

                                  before           after     move
fv_base                           268.53          268.53    +0.0%
  bear                            201.24          201.24    +0.0%
  bull                            301.79          301.79    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 8.40%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (539.14)
  store's newest period, today: --
```

Record: `reference/run-records/MUSA-2026-10-27-check.json`

## NVR

**Status på listan:** WATCH-GATED · tier – · fv_base 7682.75  
*Källa: `reference/NVR-STRIKE-2026-10-27-check.md`*

#### NVR -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/NVR.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / -0.65% / 4.00%, carried from NVR-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 7,682.75 -> **7,682.75** (bear 5,138.49, bull 7,682.75)
- **FCF0:** 1,267,713,917
- **net debt:** -194,038,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 1,363,520,000; annual FY2024 1,303,391,000; annual FY2025 1,300,951,000 = 1,322,620,667; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax -54,906,750 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital 127,690,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -194,038,000 on the balance sheet + deals 0 + working capital neutralised 127,690,000 = -66,348,000
- **growth (E144):** E144: organic 7.18%/yr over 10 years, last five 6.50% (2016-2025, 10 of them PROXY from deal-free years); owner earnings per share 20.44%/yr; cap 4%; worst 3-year -0.65%, best 5-year 10.79%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.984: the weakest E140 year 1,300,951,000 over the mean 1,322,620,667 (E143(4))
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 1,267,713,917 x level 0.984 x (1 + -0.65%) = FCF0 1,238,897,070; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -- (+0.00/sh) -> **5,138.49**
- **base:** flow 1,267,713,917 x level 1.000 x (1 + 4.00%) = FCF0 1,318,422,473; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -- (+0.00/sh) -> **7,682.75**
- **bull:** flow 1,267,713,917 x level 1.000 x (1 + 4.00%) = FCF0 1,318,422,473; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **7,682.75**
- **events ledger** `reference/events/NVR.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 2,816,295
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 143,733,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 5,727.77; g* 0.47%
- **store's newest period:** 2026-06-30
- **anchors:** g* 0.47%; the base case returns ~11.8% a year at today's price against r 9.5%; tangible ROIC median 67.7% over 6 years (no goodwill row: on all invested capital) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 67.7% over 6 years (no goodwill row: on all invested capital) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 15% below its running peak
  - Q3 debt: **PASS** -- net debt -0.1x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- NVR builds and sells single-family homes, townhomes and condos to homebuyers, mostly pre-sold, with mortgage and title services.

```
NVR — strike 2026-10-27   against NVR-2026-10-27-e142.json

                                  before           after     move
fv_base                         7,682.75        7,682.75    +0.0%
  bear                          5,138.49        5,138.49    +0.0%
  bull                          7,682.75        7,682.75    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 0.47%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (5,727.77)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/NVR-2026-10-27-check.json`

**Genomgång steg för steg (`reference/reviews/NVR/2026-10-27.yaml`):**

```yaml
schema: vss/review v1
ticker: NVR
date: '2026-10-27'
status_at_start: WATCH-GATED
prepare_report: reports/prepare/NVR-2026-10-27.json
prepare_waived: null
steps:
- step: gate-1
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). PASS. Gate 1
    is frozen at the screener reading of 2026-08-26 (drawdown 25.5%, E12); today''s level leg reads 29.3%
    off the 52-week closing high 8,097.25 of 2026-02-11, inside 15-50%. Dated events: Q4 2025 results
    2026-01-28 and the 10-K 2026-02-11 (-7.27% on 2026-02-13), Q1 2026 results 2026-04-22 (-4.65%), Q3
    2026 results 2026-10-22.'
  answered_at: '2026-10-27T19:32:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - reports/prepare/NVR-2026-10-27.md
  - reports/BRIEFING-NVR-2026-10-27.md
  rulings_cited:
  - E12
  - B1
  - B2
  verification: []
- step: gate-2
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). CLASS B -- sector
    / macro: the US housing market on affordability, rates and consumer sentiment, in the issuer''s own
    words for Q3 2026: gross margin 18.3% from 21.0% on "higher lot costs, pricing pressure due to continued
    affordability challenges and weak consumer sentiment, and by contract land deposit impairments totaling
    approximately $24.8 million" (Class C component, bounded at 24.8m). Not D on the filing: new orders
    -7% in units, backlog +10% in units and +4% in dollars, average active communities 454 against 450,
    lots controlled 185,300 against 175,300. The class does not survive the hard-kill step below.'
  answered_at: '2026-10-27T19:32:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - data/autoread/2026-10-22-NVR-000090616326000099.htm
  rulings_cited:
  - B1
  verification: []
- step: gate-3
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). PASS on its
    evaluable limbs. Interest coverage 62.1x on E126 step 2 / E147 (income before taxes 1,761,932k + stated
    interest expense 28,835k) and net finance income (E118). FCF positive in 7 of the last 8 quarters
    (Q3 2024-Q2 2026 from tagged year-to-date operating cash flow; Q2 2026 negative, -151.5m, on inventory
    build). Net debt / EBITDA DATA MISSING (E119) on a net-cash balance sheet (senior notes 907.7m against
    1,125.4m homebuilding and mortgage cash at 2026-09-30). No going-concern language; KPMG LLP, auditor
    since 1987, clean opinion of 2026-02-11; no restatement.'
  answered_at: '2026-10-27T19:32:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - sources/NVR_FY2025_annual-report-10k_2026-02-11_en_a0.htm
  - data/autoread/2026-10-22-NVR-000090616326000099.htm
  - reports/prepare/NVR-2026-10-27.md
  rulings_cited:
  - E112
  - E118
  - E119
  - E126
  - E147
  verification: []
- step: gate-4
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). DATA MISSING
    for every name (E99); out of the count.'
  answered_at: '2026-10-27T19:32:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened: []
  rulings_cited:
  - E99
  verification: []
- step: gate-5
  outcome: next
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). PASS on the
    10-Q: the Q3 2026 10-Q falls due inside 90 days (around 2026-11-05; last year 2025-11-05), and the
    Q4 2026 release follows in late January 2027 (2026-01-28 last year), at the edge of the window. The
    GDDY precedent scores Gate 5 on the 10-Q deadline.'
  answered_at: '2026-10-27T19:32:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened: []
  rulings_cited:
  - E77
  verification: []
- step: hard-kills
  outcome: watch-gated
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). TWO HARD KILLS
    TRIP on the issuer''s own figures, and they decide the name. §4.2.1: revenue declined year on year
    in FOUR consecutive quarters -- Q4 2025 2,712.6m vs 2,845.6m (-4.7%), Q1 2026 1,881.1m vs 2,403.0m
    (-21.7%), Q2 2026 2,326.4m vs 2,598.8m (-10.5%), Q3 2026 2,402.4m vs 2,609.5m (-7.9%; homebuilding
    revenues 2,349,284k + mortgage banking fees 53,146k, the tagged definition). NVR makes no acquisitions,
    has no disposals and reports in dollars, so reported IS organic and B9''s carve-out cannot apply.
    §4.2.2: operating margin (E147: pre-tax + interest expense) Q3 2026 341.6m / 2,402.4m = 14.2% against
    451.3m / 2,609.5m = 17.3% in Q3 2025, -307bps on declining revenue; the quantified Class C item (contract
    land deposit impairments ~24.8m) explains 103bps of it, leaving -204bps, above the 150bps line. The
    rule applies as written (the owner on MEKKO.HE, 2026-09-08: "Regeln galler"). Warren''s reading: an
    excellent business -- tangible ROIC median 67.7%, net cash, no land risk, buybacks 9M 2026 at an average
    6,742 -- at a moment its own figures still fall; the rules ask for the turn to show in the accounts,
    not in the price. WATCH-GATED; no price level may wake it. RE-ENTRY EVENT: the Q4 2026 results release
    (late January 2027): Q4 2026 revenue against Q4 2025''s 2,712.6m. If it is not lower, the revenue
    kill clears; the margin kill is then read on the same release against Q4 2025''s operating margin.'
  answered_at: '2026-10-27T19:32:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened:
  - data/autoread/2026-10-22-NVR-000090616326000099.htm
  - sources/NVR_FY2025_annual-report-10k_2026-02-11_en_a0.htm
  - reports/BRIEFING-NVR-2026-10-27.md
  rulings_cited:
  - B9
  - E45
  - E147
  - E141
  verification: []
- step: conviction
  outcome: null
  text: ''
  answered_at: null
  skipped: true
  skip_reason: 'the walk stopped at hard-kills (watch-gated, E141 decision): a §4.2 hard kill overrides
    §4.4 and §5.3, so no score, tier or MBP is formed (MEKKO.HE precedent, 2026-09-08)'
  documents_opened: []
  rulings_cited: []
  verification: []
- step: basis
  outcome: null
  text: ''
  answered_at: null
  skipped: true
  skip_reason: 'the walk stopped at hard-kills (watch-gated, E141 decision): a §4.2 hard kill overrides
    §4.4 and §5.3, so no score, tier or MBP is formed (MEKKO.HE precedent, 2026-09-08)'
  documents_opened: []
  rulings_cited: []
  verification: []
- step: flow
  outcome: null
  text: ''
  answered_at: null
  skipped: true
  skip_reason: 'the walk stopped at hard-kills (watch-gated, E141 decision): a §4.2 hard kill overrides
    §4.4 and §5.3, so no score, tier or MBP is formed (MEKKO.HE precedent, 2026-09-08)'
  documents_opened: []
  rulings_cited: []
  verification: []
- step: net-debt
  outcome: null
  text: ''
  answered_at: null
  skipped: true
  skip_reason: 'the walk stopped at hard-kills (watch-gated, E141 decision): a §4.2 hard kill overrides
    §4.4 and §5.3, so no score, tier or MBP is formed (MEKKO.HE precedent, 2026-09-08)'
  documents_opened: []
  rulings_cited: []
  verification: []
- step: divisor
  outcome: null
  text: ''
  answered_at: null
  skipped: true
  skip_reason: 'the walk stopped at hard-kills (watch-gated, E141 decision): a §4.2 hard kill overrides
    §4.4 and §5.3, so no score, tier or MBP is formed (MEKKO.HE precedent, 2026-09-08)'
  documents_opened: []
  rulings_cited: []
  verification: []
- step: growth-view
  outcome: null
  text: ''
  answered_at: null
  skipped: true
  skip_reason: 'the walk stopped at hard-kills (watch-gated, E141 decision): a §4.2 hard kill overrides
    §4.4 and §5.3, so no score, tier or MBP is formed (MEKKO.HE precedent, 2026-09-08)'
  documents_opened: []
  rulings_cited: []
  verification: []
- step: strike
  outcome: null
  text: ''
  answered_at: null
  skipped: true
  skip_reason: 'the walk stopped at hard-kills (watch-gated, E141 decision): a §4.2 hard kill overrides
    §4.4 and §5.3, so no score, tier or MBP is formed (MEKKO.HE precedent, 2026-09-08)'
  documents_opened: []
  rulings_cited: []
  verification: []
- step: tier-mbp
  outcome: null
  text: ''
  answered_at: null
  skipped: true
  skip_reason: 'the walk stopped at hard-kills (watch-gated, E141 decision): a §4.2 hard kill overrides
    §4.4 and §5.3, so no score, tier or MBP is formed (MEKKO.HE precedent, 2026-09-08)'
  documents_opened: []
  rulings_cited: []
  verification: []
- step: verdict
  outcome: watch-gated
  text: 'E141 decision (the session decides; owner 2026-10-27: "låt warren ta besluten"). WATCH-GATED,
    now on the §4.2 hard kills (four consecutive year-on-year revenue declines; Q3 margin -307bps, -204bps
    after the land-deposit impairments) instead of Gate 3''s DATA MISSING, which E147 cleared. No tier,
    no MBP, no price alert. fv_base stays on the entry as struck (2026-10-27-check record); catalyst:
    the Q4 2026 results release, late January 2027.'
  answered_at: '2026-10-27T19:32:00+01:00'
  skipped: false
  skip_reason: null
  documents_opened: []
  rulings_cited:
  - E27
  - E141
  verification: []
growth_view:
  base: 0.025
  bear: -0.03
  bull: 0.065
  registered_at: '2026-08-30T00:00:00+02:00'
  reasons: 'standing view of 2026-08-30, reference/growth-views/NVR.md (E141 decision: it stands; the
    strike reads the E144 growth derived from the history file)'
note: '2026-10-27 (E141 decision, full walk reference/reviews/NVR/2026-10-27.yaml): Gate 3 now forms under
  E147 and PASSES (coverage 62.1x, FCF positive 7 of 8 quarters, net cash, clean KPMG opinion). But two
  §4.2 hard kills trip on the issuer''s own figures: revenue down year on year in four consecutive quarters
  (Q4 2025 -4.7%, Q1 2026 -21.7%, Q2 2026 -10.5%, Q3 2026 -7.9%; no deals or currency, so reported is
  organic) and the Q3 2026 operating margin down 307bps (204bps after the 24.8m land-deposit impairments).
  Stays WATCH-GATED, now on the kills; no tier, no MBP. Re-entry: the Q4 2026 results release (late January
  2027) -- Q4 revenue against 2,712.6m and the margin against Q4 2025.'
```

## PEP

**Status på listan:** inte på listan · tier – · fv_base –  
*Källa: `reference/PEP-STRIKE-2026-10-27-check.md`*

#### PEP -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/PEP.yaml` on the pre-registered growth view 2.00% / 1.00% / 4.00%, carried from PEP-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 65.03 -> **65.28** (bear 52.55, bull 84.85)
- **FCF0:** 9,119,750,000
- **net debt:** 42,578,000,000 on the balance sheet of 2026-09-05
- **E140 FCF0:** mean of annual FY2023 8,191,000,000; annual FY2024 8,182,000,000; annual FY2025 8,596,000,000 = 8,323,000,000; acquisitions mean 1,320,333,333 NOT deducted -- valued as the deal programme (E142); + interest after tax 840,750,000 at 0.25 (US); - minority dividends 44,000,000
- **bridge rolled (E140.1(3)):** 2025-12-27 -> 2026-09-05; year-to-date working capital -3,043,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 42,578,000,000 on the balance sheet + deals 0 + working capital neutralised -3,043,000,000 = 39,535,000,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/PEP.yaml; the registered view reference/growth-views/PEP.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.983: the weakest E140 year 8,182,000,000 over the mean 8,323,000,000 (E143(4))
- **deal programme (E142):** repeat buyer, A = 1,320,333,333/yr; ROIIC base 6.53% -- operating profit 9,477,666,667 (2015-2017 mean) -> 12,123,666,667 (2023-2025 mean); organic x1.144 (6 of 8 years at the view's 2.0%); after tax 25.0%: 961,256,554 on capital added 14,724,666,667 = 6.53%; bear 1.08% -- operating profit 10,276,000,000 (2017) -> 11,512,000,000 (2022); organic x1.104 (5 of 5 years at the view's 2.0%); after tax 25.0%: 124,849,250 on acquisitions 11,519,000,000 = 1.08%
- **bear:** flow 9,119,750,000 x level 0.983 x (1 + 1.00%) = FCF0 9,054,904,775; programme -7,703,648,678 (-5.64/sh); deals 0 credited back 0 at ROIIC 1.08% (+0.00/sh); pension deficit after tax (E146) +343,000,000 (+0.25/sh) -> **52.55**
- **base:** flow 9,119,750,000 x level 1.000 x (1 + 2.00%) = FCF0 9,302,145,000; programme -2,854,188,040 (-2.09/sh); deals 0 credited back 0 at ROIIC 6.53% (+0.00/sh); pension deficit after tax (E146) +343,000,000 (+0.25/sh) -> **65.28**
- **bull:** flow 9,119,750,000 x level 1.000 x (1 + 4.00%) = FCF0 9,484,540,000; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh); pension deficit after tax (E146) +343,000,000 (+0.25/sh) -> **84.85**
- **events ledger** `reference/events/PEP.yaml` dated 2026-10-27, cut at 2026-09-05: no deal in the bridge
- **divisor:** 1,367,000,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 3,846,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 135.46; g* 8.61%
- **store's newest period:** --
- **anchors:** g* 8.61%; the base case returns ~6.6% a year at today's price against r 9.5%; tangible ROIC median 28.6% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 28.6% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 11% below its running peak
  - Q3 debt: **PASS** -- net debt 4.3x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **FAIL** -- ROIIC 6.5% against r 9.5%
  - Q5 understandable: **PASS** -- PepsiCo makes and sells snacks and beverages to retailers and consumers worldwide; strong brands and distribution drive repeat buying.

```
PEP — strike 2026-10-27   against PEP-2026-10-27-e142.json

                                  before           after     move
fv_base                            65.03           65.28    +0.4%
  bear                             52.30           52.55    +0.5%
  bull                             84.59           84.85    +0.3%
MBP (E90)  tier -- -> --              --              --         
g*                                                 8.61%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-27 -> 2025-12-27
  settled close           2026-10-26 -> 2026-10-26  (135.46)
  store's newest period, today: --
```

Record: `reference/run-records/PEP-2026-10-27-check.json`

## PNDORA.CO

**Status på listan:** DROPPED · tier – · fv_base –  
*Källa: `reference/PNDORA.CO-STRIKE-2026-10-27-check.md`*

#### PNDORA.CO -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/PNDORA.CO.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / -3.00% / 4.00%, carried from PNDORA.CO-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2
- **fv_base:** 903.28 -> **903.81** (bear 222.68, bull 933.93)
- **FCF0:** 4,742
- **net debt:** 9,764 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 3,694; annual FY2024 4,421; annual FY2025 4,095 = 4,070; acquisitions mean 305 NOT deducted -- valued as the deal programme (E142); + interest after tax 672 at 0.22 (DK); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -1,133 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 9,764 on the balance sheet + deals 0 + working capital neutralised -1,133 = 8,631
- **growth (E144):** E144: organic 4.73%/yr over 9 years, last five 11.23% (2017-2025); owner earnings per share not derivable; cap 4%; worst 3-year -7.07%, best 5-year 11.23%
- **cycle and level (E143):** CYCLICAL (revenue fell -13% in a year; operating margin fell from 36.5% to 14.1%): owner-earnings margin median 23.4%, last three 19.5%, lowest 11.9% -> base level x1.000, bear x0.608
- **deal programme (E142):** repeat buyer, A = 305/yr; ROIIC base -22.01% -- operating profit 7,206,333,333 (2016-2018 mean) -> 7,598,666,667 (2023-2025 mean); organic x1.289; after tax 22.0%: -1,317,465,445 on capital added 5,986,666,667 = -22.01%; bear 0.00% -- operating profit 7,404,000,000 (2016) -> 5,839,000,000 (2021); organic x1.096; after tax 22.0%: -1,772,509,755 on capital added 642,000,000 = -276.09%
- **bear:** flow 4,742 x level 0.608 x (1 + -3.00%) = FCF0 2,798; programme -1,664 (-21.56/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh); pension deficit after tax (E146) +41 (+0.53/sh) -> **222.68**
- **base:** flow 4,742 x level 1.000 x (1 + 4.00%) = FCF0 4,931; programme -2,325 (-30.12/sh); deals 0 credited back 0 at ROIIC -22.01% (+0.00/sh); pension deficit after tax (E146) +41 (+0.53/sh) -> **903.81**
- **bull:** flow 4,742 x level 1.000 x (1 + 4.00%) = FCF0 4,931; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh); pension deficit after tax (E146) +41 (+0.53/sh) -> **933.93**
- **events ledger** `reference/events/PNDORA.CO.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 77,189,151
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 1,764 is DEDUCTED -- principal 1,333 + lease interest 431; the lease liability 6,291 LEFT net debt
- **close 2026-10-26:** 838.40; g* 3.21%
- **store's newest period:** 2026-06-30
- **anchors:** g* 3.21%; the base case returns ~10.0% a year at today's price against r 9.5%; tangible ROIC median 37.7% over 10 years (no goodwill row: on all invested capital) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 37.7% over 10 years (no goodwill row: on all invested capital) against 15%
  - Q2 stability: **FAIL** -- owner earnings negative in no year; operating profit at most 66% below its running peak, not regained within three years after [2019, 2020]
  - Q3 debt: **PASS** -- net debt 1.8x FCF0 against 3.0x
  - Q4 capital allocation: **FAIL** -- ROIIC -22.0% against r 9.5%
  - Q5 understandable: **PASS** -- Pandora designs, makes and sells jewellery, sold mainly through its own and partner stores worldwide.

```
PNDORA.CO — strike 2026-10-27   against PNDORA.CO-2026-10-27-e142.json

                                  before           after     move
fv_base                           903.28          903.81    +0.1%
  bear                            222.15          222.68    +0.2%
  bull                            933.40          933.93    +0.1%
MBP (E90)  tier -- -> --              --              --         
g*                                                 3.21%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-06-30 -> 2026-06-30
  settled close           2026-10-26 -> 2026-10-26  (838.40)
  store's newest period, today: 2026-06-30
```

Record: `reference/run-records/PNDORA.CO-2026-10-27-check.json`

## RBREW.CO

**Status på listan:** inte på listan · tier – · fv_base –  
*Källa: `reference/RBREW.CO-STRIKE-2026-10-27-check.md`*

#### RBREW.CO -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/RBREW.CO.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / 2.21% / 4.00%, carried from RBREW.CO-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** 2025-FY
- **fv_base:** 195.97 -> **195.97** (bear 83.63, bull 299.50)
- **FCF0:** 1,232
- **net debt:** 6,610 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 961; annual FY2024 954; 2025-FY 1,186 = 1,034; acquisitions mean 889 NOT deducted -- valued as the deal programme (E142); + interest after tax 198 at 0.22 (DK); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -225 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 6,610 on the balance sheet + deals 0 + working capital neutralised -225 = 6,385
- **growth (E144):** E144: organic 4.80%/yr over 10 years, last five 7.14% (2016-2025); owner earnings per share not derivable; cap 4%; worst 3-year 2.21%, best 5-year 7.14%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.923: the weakest E140 year 954 over the mean 1,034 (E143(4))
- **deal programme (E142):** repeat buyer, A = 889/yr; ROIIC base 2.43% -- operating profit 1,136,333,333 (2016-2018 mean) -> 1,936,000,000 (2023-2025 mean); organic x1.464; after tax 22.0%: 212,900,248 on capital added 8,772,333,333 = 2.43%; bear 0.00% -- operating profit 1,339,000,000 (2018) -> 1,638,000,000 (2023); organic x1.267; after tax 22.0%: -45,307,557 on capital added 7,507,000,000 = -0.60%
- **bear:** flow 1,232 x level 0.923 x (1 + 2.21%) = FCF0 1,162; programme -6,205 (-127.50/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **83.63**
- **base:** flow 1,232 x level 1.000 x (1 + 4.00%) = FCF0 1,281; programme -5,038 (-103.54/sh); deals 0 credited back 0 at ROIIC 2.43% (+0.00/sh) -> **195.97**
- **bull:** flow 1,232 x level 1.000 x (1 + 4.00%) = FCF0 1,281; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **299.50**
- **events ledger** `reference/events/RBREW.CO.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 48,661,324
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 189 is DEDUCTED -- principal 177 + lease interest 12; the lease liability 447 LEFT net debt
- **close 2026-10-26:** 435.40; g* 9.88%
- **store's newest period:** 2026-06-30
- **anchors:** g* 9.88%; the base case returns ~7.1% a year at today's price against r 9.5%; tangible ROIC median 17.6% over 10 years (no goodwill row: on all invested capital) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 17.6% over 10 years (no goodwill row: on all invested capital) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 8% below its running peak
  - Q3 debt: **FAIL** -- net debt 5.0x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **FAIL** -- ROIIC 2.4% against r 9.5%
  - Q5 understandable: **PASS** -- Royal Unibrew brews and sells beer, soft drinks and other beverages, mainly in the Nordic and Baltic countries, Italy, France and Canada.

```
RBREW.CO — strike 2026-10-27   against RBREW.CO-2026-10-27-e142.json

                                  before           after     move
fv_base                           195.97          195.97    +0.0%
  bear                             83.63           83.63    +0.0%
  bull                            299.50          299.50    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 9.88%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (435.40)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/RBREW.CO-2026-10-27-check.json`

## RMV.L

**Status på listan:** PIPELINE · tier – · fv_base –  
*Källa: `reference/RMV.L-STRIKE-2026-10-27-check.md`*

#### RMV.L -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/RMV.L.yaml` on the pre-registered growth view 3.00% / 0.00% / 6.00%, carried from RMV.L-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** 2025-FY
- **fv_base:** 4.11 -> **4.11** (bear 2.71, bull 5.28)
- **FCF0:** 196,712
- **net debt:** -32,628 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 195,496; annual FY2024 186,982; 2025-FY 211,933 = 198,137; acquisitions mean 2,517 NOT deducted -- valued as the deal programme (E142); + interest after tax -1,425 at 0.25 (GB); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital 2,373 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -32,628 on the balance sheet + deals 0 + working capital neutralised 2,373 = -30,255
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/RMV.L.yaml; the registered view reference/growth-views/RMV.L.md
- **cycle and level (E143):** CYCLICAL (revenue fell -29% in a year): owner-earnings margin median 59.8%, last three 53.6%, lowest 45.1% -> base level x1.000, bear x0.841
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 196,712 x level 0.841 x (1 + 0.00%) = FCF0 165,509; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -- (+0.00/sh) -> **2.71**
- **base:** flow 196,712 x level 1.000 x (1 + 3.00%) = FCF0 202,613; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -- (+0.00/sh) -> **4.11**
- **bull:** flow 196,712 x level 1.000 x (1 + 6.00%) = FCF0 208,515; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **5.28**
- **events ledger** `reference/events/RMV.L.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 756,031,940
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 3,226 is DEDUCTED -- principal 3,146 + lease interest 80; the lease liability 5,361 LEFT net debt
- **close 2026-10-26:** 5.31; g* 6.08%
- **store's newest period:** 2026-06-30
- **anchors:** g* 6.08%; the base case returns ~7.9% a year at today's price against r 9.5%; tangible ROIC no profit and capital years
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **n/a** -- no profit and capital years
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 37% below its running peak
  - Q3 debt: **PASS** -- net debt -0.1x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Rightmove runs the UK's largest property portal, earning fees from estate agents and developers who advertise homes on it.

```
RMV.L — strike 2026-10-27   against RMV.L-2026-10-27-e142.json

                                  before           after     move
fv_base                             4.11            4.11    +0.0%
  bear                              2.71            2.71    +0.0%
  bull                              5.28            5.28    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 6.08%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (5.31)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/RMV.L-2026-10-27-check.json`

## ULTA

**Status på listan:** INTAKE · tier – · fv_base –  
*Källa: `reference/ULTA-STRIKE-2026-10-27-check.md`*

#### ULTA -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/ULTA.yaml` on the growth DERIVED from the issuer's history (E144) 8.00% / 1.49% / 8.00%, carried from ULTA-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2026
- **fv_base:** 601.27 -> **601.27** (bear 81.39, bull 601.27)
- **FCF0:** 1,079,655,583
- **net debt:** 181,127,000 on the balance sheet of 2026-08-01
- **E140 FCF0:** mean of annual FY2024 1,166,504,000; annual FY2025 1,075,754,000; annual FY2026 992,688,000 = 1,078,315,333; acquisitions mean 128,937,667 NOT deducted -- valued as the deal programme (E142); + interest after tax 1,340,250 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2026-01-31 -> 2026-08-01; year-to-date working capital -382,070,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 181,127,000 on the balance sheet + deals 0 + working capital neutralised -382,070,000 = -200,943,000
- **growth (E144):** E144: organic 12.47%/yr over 9 years, last five 8.83% (2017-2025, 9 of them PROXY from deal-free years); owner earnings per share 25.15%/yr; cap 8%; worst 3-year 1.49%, best 5-year 12.20%
- **cycle and level (E143):** CYCLICAL (revenue fell -17% in a year; operating margin fell from 13.5% to 3.8%): owner-earnings margin median 9.3%, last three 8.8%, lowest 2.0% -> base level x1.000, bear x0.222
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 1,079,655,583 x level 0.222 x (1 + 1.49%) = FCF0 243,022,074; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **81.39**
- **base:** flow 1,079,655,583 x level 1.000 x (1 + 8.00%) = FCF0 1,166,028,030; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.36% (+0.00/sh) -> **601.27**
- **bull:** flow 1,079,655,583 x level 1.000 x (1 + 8.00%) = FCF0 1,166,028,030; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **601.27**
- **events ledger** `reference/events/ULTA.yaml` dated 2026-10-27, cut at 2026-08-01: no deal in the bridge
- **divisor:** 43,062,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 2,184,453,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 625.33; g* 8.47%
- **store's newest period:** --
- **anchors:** g* 8.47%; the base case returns ~9.3% a year at today's price against r 9.5%; tangible ROIC median 45.8% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 45.8% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 74% below its running peak, regained within three years
  - Q3 debt: **PASS** -- net debt -0.2x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Ulta Beauty retails cosmetics, fragrance, skin and hair care and salon services to beauty enthusiasts; breadth, loyalty program and services bring repeat visits.

```
ULTA — strike 2026-10-27   against ULTA-2026-10-27-e142.json

                                  before           after     move
fv_base                           601.27          601.27    +0.0%
  bear                             81.39           81.39    +0.0%
  bull                            601.27          601.27    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 8.47%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-01-31 -> 2026-01-31
  settled close           2026-10-26 -> 2026-10-26  (625.33)
  store's newest period, today: --
```

Record: `reference/run-records/ULTA-2026-10-27-check.json`

## GNTX

**Status på listan:** WATCH-GATED · tier – · fv_base 27.45  
*Källa: `reference/GNTX-STRIKE-2026-10-27.md`*

#### GNTX -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/GNTX.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / -2.02% / 4.00% (first strike, from the entry). Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** -- -> **27.45** (bear 15.71, bull 29.62)
- **FCF0:** 351,057,500
- **net debt:** -229,737,249 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 330,836,777; annual FY2024 360,960,903; annual FY2025 361,374,819 = 351,057,500; acquisitions mean 59,366,418 NOT deducted -- valued as the deal programme (E142); + interest after tax 0 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital 25,533,484 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -229,737,249 on the balance sheet + deals 0 + working capital neutralised 25,533,484 = -204,203,765
- **growth (E144):** E144: organic 4.60%/yr over 9 years, last five 4.47% (2016-2024, 9 of them PROXY from deal-free years); owner earnings per share 5.21%/yr; cap 4%; worst 3-year -2.02%, best 5-year 4.62%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.942: the weakest E140 year 330,836,777 over the mean 351,057,500 (E143(4))
- **deal programme (E142):** repeat buyer, A = 59,366,418/yr; ROIIC base -20.98% -- operating profit 497,955,909 (2015-2017 mean) -> 476,464,460 (2023-2025 mean); organic x1.378; after tax 25.0%: -157,234,815 on capital added 749,417,905 = -20.98%; bear 0.00% -- operating profit 511,742,935 (2016) -> 409,781,978 (2021); organic x1.031; after tax 25.0%: -88,414,120 on capital added 133,604,638 = -66.18%
- **bear:** flow 351,057,500 x level 0.942 x (1 + -2.02%) = FCF0 324,147,715; programme -338,759,964 (-1.62/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **15.71**
- **base:** flow 351,057,500 x level 1.000 x (1 + 4.00%) = FCF0 365,099,800; programme -452,057,407 (-2.17/sh); deals 0 credited back 0 at ROIIC -20.98% (+0.00/sh) -> **27.45**
- **bull:** flow 351,057,500 x level 1.000 x (1 + 4.00%) = FCF0 365,099,800; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **29.62**
- **events ledger** `reference/events/GNTX.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 208,585,726
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 7,491,139 LEFT net debt; finance leases stay in net debt
- **close 2026-10-27:** 20.21; g* 0.31%
- **store's newest period:** --
- **anchors:** g* 0.31%; the base case returns ~11.9% a year at today's price against r 9.5%; tangible ROIC median 24.4% over 11 years (goodwill taken out) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 24.4% over 11 years (goodwill taken out) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 29% below its running peak
  - Q3 debt: **PASS** -- net debt -0.6x FCF0 against 3.0x
  - Q4 capital allocation: **FAIL** -- ROIIC -21.0% against r 9.5%
  - Q5 understandable: **PASS** -- Gentex makes automatic-dimming mirrors and other vision and electronics for car makers, plus premium audio, dimmable aircraft windows and fire-protection devices.

```
GNTX — strike 2026-10-27   (first strike: no prior record)

                                  before           after     move
fv_base                               --           27.45         
  bear                                --           15.71         
  bull                                --           29.62         
MBP (E90)  tier -- -> --              --              --         
g*                                                 0.31%         

WHICH LEG MOVED
  FCF0                                   -- -> 351,057,500                   
  net debt                               -- -> -229,737,249                  
  divisor (shares)                       -- -> 208,585,726                   
  basis                                  -- -> annual FY2025                 
  growth view                            -- -> 4.00% / -2.02% / 4.00%           E144: derived from the issuer's history
  discount rate                          -- -> 0                             
  lease treatment                        -- -> RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease paymen        

WHAT THE TWO SIDES STAND ON
  basis window end        -- -> 2025-12-31
  settled close           -- -> 2026-10-27  (20.21)
  store's newest period, today: --
```

Record: `reference/run-records/GNTX-2026-10-27.json`

## SFM

**Status på listan:** WATCH-GATED · tier – · fv_base 78.47  
*Källa: `reference/SFM-STRIKE-2026-10-27.md`*

#### SFM -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/SFM.yaml` on the growth DERIVED from the issuer's history (E144) 8.00% / 4.44% / 8.00% (first strike, from the entry). Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** -- -> **78.47** (bear 38.47, bull 78.47)
- **FCF0:** 305,291,500
- **net debt:** -110,104,000 on the balance sheet of 2026-06-28
- **E140 FCF0:** mean of annual FY2023 198,891,000; annual FY2024 297,397,000; annual FY2025 425,495,000 = 307,261,000; acquisitions mean 4,344,000 NOT deducted -- valued as the deal programme (E142); + interest after tax -1,969,500 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-28 -> 2026-06-28; year-to-date working capital -33,718,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -110,104,000 on the balance sheet + deals 0 + working capital neutralised -33,718,000 = -143,822,000
- **growth (E144):** E144: organic 12.68%/yr over 8 years, last five 8.06% (2014-2025, 8 of them PROXY from deal-free years); owner earnings per share 22.17%/yr; cap 8%; worst 3-year 4.44%, best 5-year 12.48%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.647: the weakest E140 year 198,891,000 over the mean 307,261,000 (E143(4))
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 305,291,500 x level 0.647 x (1 + 4.44%) = FCF0 206,384,689; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **38.47**
- **base:** flow 305,291,500 x level 1.000 x (1 + 8.00%) = FCF0 329,714,820; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 8.18% (+0.00/sh) -> **78.47**
- **bull:** flow 305,291,500 x level 1.000 x (1 + 8.00%) = FCF0 329,714,820; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **78.47**
- **events ledger** `reference/events/SFM.yaml` dated 2026-10-27, cut at 2026-06-28: no deal in the bridge
- **divisor:** 94,410,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 1,992,469,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-27:** 64.41; g* 5.59%
- **store's newest period:** --
- **anchors:** g* 5.59%; the base case returns ~10.9% a year at today's price against r 9.5%; tangible ROIC median 38.1% over 11 years (goodwill taken out) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 38.1% over 11 years (goodwill taken out) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 15% below its running peak
  - Q3 debt: **PASS** -- net debt -0.4x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Sprouts runs specialty grocery stores selling fresh, natural and organic food to US shoppers.

```
SFM — strike 2026-10-27   (first strike: no prior record)

                                  before           after     move
fv_base                               --           78.47         
  bear                                --           38.47         
  bull                                --           78.47         
MBP (E90)  tier -- -> --              --              --         
g*                                                 5.59%         

WHICH LEG MOVED
  FCF0                                   -- -> 305,291,500                   
  net debt                               -- -> -110,104,000                  
  divisor (shares)                       -- -> 94,410,000                    
  basis                                  -- -> annual FY2025                 
  growth view                            -- -> 8.00% / 4.44% / 8.00%            E144: derived from the issuer's history
  discount rate                          -- -> 0                             
  lease treatment                        -- -> RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease paymen        

WHAT THE TWO SIDES STAND ON
  basis window end        -- -> 2025-12-28
  settled close           -- -> 2026-10-27  (64.41)
  store's newest period, today: --
```

Record: `reference/run-records/SFM-2026-10-27.json`

## BKNG

**Status på listan:** inte på listan · tier – · fv_base –  
*Källa: `reference/BKNG-STRIKE-2026-10-27.md`*

#### BKNG -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/BKNG.yaml` on the pre-registered growth view 5.00% / 0.00% / 8.00% (first strike, from the entry). Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** -- -> **218.18** (bear -2.96, bull 281.48)
- **FCF0:** 9,204,416,667
- **net debt:** 2,972,000,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 7,475,000,000; annual FY2024 7,591,000,000; annual FY2025 8,909,000,000 = 7,991,666,667; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 1,212,750,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -690,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 2,972,000,000 on the balance sheet + deals 0 + working capital neutralised -690,000,000 = 2,282,000,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/BKNG.yaml; the registered view reference/growth-views/BKNG.md
- **cycle and level (E143):** CYCLICAL (revenue fell -55% in a year; operating margin fell from 36.8% to -9.3%): owner-earnings margin median 33.3%, last three 33.3%, lowest -3.0% -> base level x1.000, bear x0.000
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 9,204,416,667 x level 0.000 x (1 + 0.00%) = FCF0 0; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **-2.96**
- **base:** flow 9,204,416,667 x level 1.000 x (1 + 5.00%) = FCF0 9,663,482,133; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 169.01% (+0.00/sh) -> **218.18**
- **bull:** flow 9,204,416,667 x level 1.000 x (1 + 8.00%) = FCF0 9,940,770,000; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **281.48**
- **events ledger** `reference/events/BKNG.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 770,000,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 672,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-27:** 150.14; g* 0.60%
- **store's newest period:** --
- **anchors:** g* 0.60%; the base case returns ~12.4% a year at today's price against r 9.5%; tangible ROIC median 60.6% over 11 years (goodwill taken out) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 60.6% over 11 years (goodwill taken out) against 15%
  - Q2 stability: **FAIL** -- owner earnings negative in [2020]; operating profit at most 112% below its running peak, regained within three years
  - Q3 debt: **PASS** -- net debt 0.2x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Booking sells hotel rooms, flights, car rentals and restaurant bookings online to travellers through Booking.com, Priceline, Agoda, KAYAK and OpenTable, earning a commission from the providers.

```
BKNG — strike 2026-10-27   (first strike: no prior record)

                                  before           after     move
fv_base                               --          218.18         
  bear                                --           -2.96         
  bull                                --          281.48         
MBP (E90)  tier -- -> --              --              --         
g*                                                 0.60%         

WHICH LEG MOVED
  FCF0                                   -- -> 9,204,416,667                 
  net debt                               -- -> 2,972,000,000                 
  divisor (shares)                       -- -> 770,000,000                   
  basis                                  -- -> annual FY2025                 
  growth view                            -- -> 5.00% / 0.00% / 8.00%            E28: the view is the prior record's, unchanged by a strike
  discount rate                          -- -> 0                             
  lease treatment                        -- -> RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease paymen        

WHAT THE TWO SIDES STAND ON
  basis window end        -- -> 2025-12-31
  settled close           -- -> 2026-10-27  (150.14)
  store's newest period, today: --
```

Record: `reference/run-records/BKNG-2026-10-27.json`

## TPR

**Status på listan:** inte på listan · tier – · fv_base –  
*Källa: `reference/TPR-STRIKE-2026-10-27.md`*

#### TPR -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/TPR.yaml` on the growth DERIVED from the issuer's history (E144) 3.60% / -1.60% / 4.00% (first strike, from the entry). Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2026
- **fv_base:** -- -> **64.37** (bear 8.33, bull 102.71)
- **FCF0:** 1,352,400,000
- **net debt:** 1,421,900,000 on the balance sheet of 2026-06-27
- **E140 FCF0:** mean of annual FY2024 888,600,000; annual FY2025 1,042,300,000; annual FY2026 1,582,700,000 = 1,171,200,000; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 181,200,000 at 0.25 (US); - minority dividends 0
- **bridge (E140(3), deals at the HIGH end):** net debt 1,421,900,000 on the balance sheet + deals 0 + working capital neutralised 0 = 1,421,900,000
- **growth (E144):** E144: organic 3.60%/yr over 8 years, last five 6.85% (2017-2026, 8 of them PROXY from deal-free years); owner earnings per share 15.46%/yr; cap 4%; worst 3-year -1.60%, best 5-year 7.16%
- **cycle and level (E143):** CYCLICAL (revenue fell -18% in a year; operating margin fell from 17.5% to -11.1%): owner-earnings margin median 12.4%, last three 18.5%, lowest 4.1% -> base level x0.672, bear x0.220
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 1,352,400,000 x level 0.220 x (1 + -1.60%) = FCF0 292,615,701; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 7.39% (+0.00/sh) -> **8.33**
- **base:** flow 1,352,400,000 x level 0.672 x (1 + 3.60%) = FCF0 941,444,629; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 8.59% (+0.00/sh) -> **64.37**
- **bull:** flow 1,352,400,000 x level 1.000 x (1 + 4.00%) = FCF0 1,406,496,000; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **102.71**
- **events ledger** `reference/events/TPR.yaml` dated 2026-10-27, cut at 2026-06-27: no deal in the bridge
- **divisor:** 210,200,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 1,574,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-27:** 111.39; g* 9.65%
- **store's newest period:** --
- **anchors:** g* 9.65%; the base case returns ~6.8% a year at today's price against r 9.5%; tangible ROIC median 34.4% over 11 years (goodwill taken out) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 34.4% over 11 years (goodwill taken out) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 167% below its running peak, regained within three years
  - Q3 debt: **PASS** -- net debt 1.5x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Tapestry sells Coach and kate spade handbags, accessories and clothing to consumers through its own stores, online and wholesale.

```
TPR — strike 2026-10-27   (first strike: no prior record)

                                  before           after     move
fv_base                               --           64.37         
  bear                                --            8.33         
  bull                                --          102.71         
MBP (E90)  tier -- -> --              --              --         
g*                                                 9.65%         

WHICH LEG MOVED
  FCF0                                   -- -> 1,352,400,000                 
  net debt                               -- -> 1,421,900,000                 
  divisor (shares)                       -- -> 210,200,000                   
  basis                                  -- -> annual FY2026                 
  growth view                            -- -> 3.60% / -1.60% / 4.00%           E144: derived from the issuer's history
  discount rate                          -- -> 0                             
  lease treatment                        -- -> RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease paymen        

WHAT THE TWO SIDES STAND ON
  basis window end        -- -> 2026-06-27
  settled close           -- -> 2026-10-27  (111.39)
  store's newest period, today: --
```

Record: `reference/run-records/TPR-2026-10-27.json`

## OLVAS.HE

**Status:** WATCH-GATED · inget värde struket

```
OLVAS.HE taken in WATCH-GATED (E141 decision): two FY2026 outlook cuts in four reports, a 4.2.3 hard kill

H1 2026 report 2026-08-14 (EUR 84-92m -> 84-90m) and the update of
2026-10-13 (84-90m -> 80-85m). No store and no fv yet: the kill decides
first. Re-entry with the H1 2027 report, when the August cut leaves the
window. Issuer resolved on the Nasdaq Nordic feed; six reports fetched.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
```
