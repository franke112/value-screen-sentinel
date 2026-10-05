# CROX — the whole chain, 2026-09-04

**Growth view registered by the owner 2026-09-04, in his own words, before
this ran (E28 / E109):** bear **−1%** / base **1%** / bull **3%**.

> Tror inte på Crocs — det är de där plastskorna, jag ser inte mycket
> tillväxt där. Och det gör inte deras egna insiders heller: alla säljer.
> Bolaget guidar själv 1-2 % för året.

`reference/growth-views/CROX.md`. The reasoning was amended the same day to
add the final sentence; the numbers did not move and the earlier
transcription is kept in the file.

**THE LAST SENTENCE CHECKS OUT AGAINST THE FILING.** Crocs' Q2 2026 release
(8-K 0001334036-26-000050, exhibit 99.1, 2026-07-30): *"Revenues to be up
approximately **1% to 2%** compared to full year 2025, **up from our previous
guidance of down 1% to up 1%**."*

---

## 1. The strike

Basis `annual FY2025`, ending 2025-12-31. r 9.5% (7.0% core + 2.5%
premium). Settled close **116.01** on 2026-09-03.

| | USD |
|---|---:|
| **fv_base** (g 1%) | **169.79** |
| E29 band, g 0.5% | 157.02 |
| E29 band, g 1.5% | 184.52 |
| **FV_bear** (g −1%) | **143.01** |
| **FV_bull** (g 3%) | **201.08** |

- FCF0 **815,061,000** · net debt **1,483,495,000** · divisor **54,208,000**
- **g\*, the growth the price implies at r 9.5%: −3.39%** — against the
  owner's registered base of +1% and bear of −1%
- price vs fv_base **−31.7%** · vs FV_bear **−18.9%** · vs FV_bull **−42.3%**

**The price is below the bear case.** At 116.01 the market is paying for
−3.4% growth for ten years; the owner's most pessimistic registered rate is
−1%.

## 2. Promotion, and E12's freeze

**INTAKE → PIPELINE, ruled by the owner 2026-09-04.** E111 says promotion is
what stamps E12's entry, and it is stamped:

```
dd_at_entry: 0.1783
peak_date:   2026-08-04
```

52-week closing high **141.19 on 2026-08-04**; settled close **116.01 on
2026-09-03**; −17.83%. **Frozen: `rules.frozen_gate_1` returns True**, so
the dislocation verdict is struck on this reading from here on and today's
drawdown is context only. Leaving PIPELINE takes an information event.

**Nothing else was written.** No `fv_base`, no `tier`, no `mbp`, no
`stop_price`.

## 3. The gates

### Gate 1 — Dislocation: **LEVEL MET, CATALYST NOT MET**

| leg | reading | rests on |
|---|---|---|
| decline 15–50% from the 52-week high | **MET, 17.83%** | settled closes: 141.19 (2026-08-04) → 116.01 (2026-09-03) |
| bulk of the decline in the trailing 3–6 months | **NEEDS OWNER** | the peak is **one month old**. The whole decline is inside the window; whether a one-month fall is "the bulk of the decline occurring in the trailing 3–6 months" or too fresh to be one is a reading of the words, not a measurement |
| an identifiable, dateable catalyst event | **NOT MET on the evidence** | see below |

**There is no dateable catalyst behind THIS drawdown, and the measurement
says so.** Since the 2026-08-04 peak: 23 sessions, of which **2 fell 3% or
more**; the largest is **−4.69% on 2026-08-11**, then −4.24% on 2026-09-01.
It is a drift, not an event.

**The obvious candidate is disqualified by its own date.** The briefing found
one session in 260 that fell ≥7% — **2026-07-30, −7.4%**, on a soft Q3
outlook. **That was five days BEFORE the 52-week high was set.** The shares
recovered from it to a new high on 2026-08-04, so it cannot be the cause of
a decline that began afterwards.

### Gate 2 — Disconnect classification: **NEEDS OWNER**

The framework is explicit: *"If you cannot confidently classify, the verdict
is D until proven otherwise."* **I am not classifying it.** What the filings
put on both sides:

**Toward C (one-off, quantifiable):** FY2025 income from operations
**149,515** carries a **307,000 goodwill impairment** and **431,115 of asset
impairments** — **738,115 of non-cash charges**, both stated on the face of
the income statement, both attributable to HEYDUDE.

**Toward D (structural):** HEYDUDE revenue **949,393 → 824,141 → 714,840**
across FY2023–FY2025 — **−24.7% over two years**, and the FY2026 guidance is
for it to fall again (down 4% to 2%).

**Toward A (narrative):** the Crocs Brand grew in the same years —
**3,012,954 → 3,277,967 → 3,325,807** — and the company **raised** full-year
guidance on 2026-07-30.

*All figures: 10-K 0001334036-26-000006, consolidated income statement and
segment note; guidance from 8-K 0001334036-26-000050 ex-99.1.*

### Gate 3 — Quality floor: **ONE LIMB FAILS, TWO ARE DATA MISSING, ONE PASSES**

| limb | reading | rests on |
|---|---|---|
| net debt / EBITDA ≤ 2.5× | **DATA MISSING** | the 10-K states **no EBITDA figure** — the word appears only inside impairment assumptions. The store carries none either (`ebitda` DATA MISSING); deriving one is E22's forbidden operation. Net debt is 1,483,495,000 |
| interest coverage ≥ 5× | **FAILS: 1.69×** | income from operations **149,515** over interest expense **88,287**, both on the FY2025 income statement, same window. **AND THE REASON IT FAILS IS THE 738,115 OF IMPAIRMENTS** — without them the numerator would be about 887,630 and the ratio about 10×. Adding them back is a derivation and a judgement about what this limb's EBIT means. **NEEDS OWNER** |
| FCF positive in ≥ 6 of 8 quarters | **DATA MISSING, and nameably so** | Crocs tags its cash-flow statement **cumulatively**: of every three-month duration in its facts, **only Q1s exist** — 14 of them, back to 2019, and every one negative because Q1 is its seasonal trough. Six of eight cannot be counted from what is tagged. E86's operand form would close it |
| no going-concern, no auditor change, no restatement | **MET** | searched 2026-09-04 across the FY2025 10-K: `going concern` 0, `substantial doubt` 0, `change in accountants` 0. `restated` appears 19 times and **every one is the restated certificate of incorporation**, not a financial restatement |

### Gate 5 — Dated catalyst: **NEEDS OWNER**

No date is announced in any filing on EDGAR. **What the pattern says**, from
the 8-K record: Q3 results were filed **2025-10-30**, Q4 **2026-02-12**, Q1
**2026-04-30**, Q2 **2026-07-30**. A Q3 2026 release in the last week of
October 2026 is about **55 days out**, inside the 90.

**A pattern is not a scheduled event.** The framework asks for *"a specific,
scheduled event within 90 days"*, and I am not converting four historical
dates into one. Confirming the announced date closes this.

### Gate 4 — **DATA MISSING and out of the count** (E99), unchanged.

## 4. The E76 gap section 8 named: buybacks against fv_base

**This is the measurement that could not be made until a fair value
existed.** Every share Crocs bought in the trailing four reported quarters,
at the prices it printed, against **fv_base 169.79**:

| quarter | shares | average price paid | spent | vs fv_base |
|---|---:|---:|---:|---:|
| Q3 2025 | 2,443,300 | 83.03 | 202.9m | **−51.1%** |
| Q4 2025 | 2,154,285 | 83.63 | 180.2m | **−50.7%** |
| Q1 2026 | **0** | — | — | **no repurchases** |
| Q2 2026 | 2,345,329 | 106.87 | 250.6m | **−37.1%** |
| **total** | **6,942,914** | **91.27** | **633.7m** | **−46.2%** |

*Sources: 10-K 0001334036-26-000006 Item 5 (Q4 2025); 10-Q
0001334036-25-000101 (Q3 2025); 10-Q 0001334036-26-000052 (Q2 2026); 10-Q
0001334036-26-000032 cash-flow statement, `Repurchases of common stock —`
against 60,866 in the prior-year quarter, which is why Q1 2026 shows none.*

**Read plainly:** management bought 6.9m shares — about 12.8% of the
54.2m-share divisor — at an average **46% below** what this framework now
thinks they are worth, **paused entirely in Q1 2026**, and resumed in Q2 at
prices 29% higher than the quarter before. E76 calls this one of the few
places management's judgement is directly measurable against the owner's.

## 5. §6 timing

Settled close 116.01, 2026-09-03.

| | reading | §6.2 trigger |
|---|---:|---|
| RSI(14) | **34.76** | **not oversold** — above 30, so no reclaim to trade. The overbought veto does not apply either |
| 50-day SMA | 128.76 | price is **−9.9%** below it. **No 50DMA reclaim** |
| 200-day SMA | 103.10 | price is **+12.5%** above it — trend tailwind present |
| 52-week low | 73.39 (2025-11-14) | price is **+58.1%** above it |
| volume vs 20-day | 0.79× | **below** the 1.5× a confirmation needs |

**No §6.2 trigger is confirmed.** §6.3's own matrix has nothing to fire on:
price is above every MBP a tier would produce (below), and neither an RSI
reclaim nor a 50DMA reclaim is present.

## 6. What a score would be under E99 — **AND NO TIER IS WRITTEN**

**Score = (gates passed, 0–4) + green flags − soft flags.** Gate 4 is out of
the denominator (E99).

**Gates passed: 0 or 1, and which depends on the owner.**

| gate | contribution | why |
|---|---|---|
| Gate 1 | **0 as it stands** | the level leg is met; the catalyst leg is not, and a gate needs all its legs |
| Gate 2 | **unscored** | the owner's classification. D would be a hard kill |
| Gate 3 | **0** | interest coverage fails at 1.69× on the stated figures; two limbs are DATA MISSING |
| Gate 5 | **unscored** | no announced date |

**Green flags (+1 each)**

| flag | fires? |
|---|---|
| active buyback at depressed prices | **YES, +1** — 6.9m shares at 46% below fv_base |
| guidance maintained or raised through the drawdown | **NEEDS OWNER** — guidance was **raised** 2026-07-30, but the drawdown began 2026-08-04, five days later. Raised *into* the fall, not *through* it |
| insider buying cluster | **NO** — 28 Form 4s over twelve months, **every open-market line a sale**, not one purchase, none under a 10b5-1 plan |
| FCF conversion ≥ 90% of net income | **NOT MEANINGFUL** — net income is **−81,198** |
| margin expansion during the controversy | **NO** — gross margin 58.8% (FY2024) → 58.3% (FY2025) |
| market share gains in core segment | **NEEDS OWNER** — not stated in the filing |

**Soft flags (−1 each)**

| flag | fires? |
|---|---|
| customer concentration > 20% | **NO** — *"There were no customers who represented 10% or more of consolidated revenues"* |
| open regulatory probe | **NO** — nothing matched in the 10-K |
| SBC > 30% of FCF | **NO** — 36,701 / 815,061 = **4.5%** |
| key-segment deceleration, 2 consecutive quarters | **NEEDS OWNER, leaning YES** — HEYDUDE has fallen two consecutive **years** (−13.2%, then −13.3%) and is guided down again. The flag is written in quarters and the tagged quarterly series does not reach them |
| rising DSO | **NEEDS OWNER** — receivables 278,191 (2025) against 257,657 (2024), +8.0%, on revenue −1.5%. Directionally rising; DSO itself is not stated |

**Where that leaves the score:** on what is decided, **0 gates + 1 green − 0
soft = 1**, which is E99's `≤ 3: drop or watchlist`. Three of the four gates
and three flags are the owner's, and the realistic range is **1 to 4**.

**NO TIER IS WRITTEN.** §5.3's tiers all begin at conviction ≥ 4, and no
tier means no MBP. What the MBP *would* be at each tier (E90's cushion on
the base case), printed so the range is visible before scoring — **none of
these is the MBP**:

| tier | MBP would be | vs price 116.01 |
|---|---:|---:|
| 1 (×0.85) | 144.33 | price is 19.6% below |
| 2 (×0.75) | 127.35 | price is 8.9% below |
| 3 (×0.65) | 110.37 | price is 5.1% **above** |
