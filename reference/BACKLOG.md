# Backlog — bugs and gaps, not framework questions

Things that are wrong in the code rather than undecided in the rules. A rule
question goes to `FRAMEWORK-EDITS.md` and gets a letter; a defect goes here and
gets fixed. Nothing in this file is a decision the owner owes an answer to.

Started 2026-08-23, out of the first §5 session run on a screener-chosen name
(LULU). Until then the backlog was carried in session notes.

---

## B-1 — phase 6 writes a PIPELINE name without its CIK

**Found:** 2026-08-23, running `vss xbrl --ticker LULU`.

`vss xbrl` needs a `cik:` on the watchlist entry. SEC identifies filers by CIK,
the ticker→CIK map lives on `www.sec.gov`, and the tool refuses to guess. But
`vss/pipeline.py` writes `ticker`, `name`, `currency`, `status` and `notes` and
nothing else — so **every screener-sourced US name hits this wall the first time
anyone runs §5 on it**, and the fix is a hand edit to the file phase 6 is
otherwise forbidden to touch twice.

**Shape of the fix:** carry the CIK through for US filers. It is obtainable at
write time from `data.sec.gov` — the same endpoint `vss xbrl` already calls —
and `cik` is not one of `FORBIDDEN_KEYS`; it is a fact about the issuer, not a
number nobody computed. A name whose CIK cannot be established gets none, and
`vss xbrl` says what it says today.

**Workaround until then:** `--cik NNNNNN` on the command line. LULU is 1397187,
verified against the `entityName` in the response.

---

## B-2 — "8 quarters" from `vss xbrl` is 8 TAGGED quarters, not 8 consecutive ones

**Found:** 2026-08-23, LULU.

The fourth quarter of a fiscal year is never tagged as a quarter. It exists only
inside the 10-K's annual figure, and the difference between the annual figure and
the three tagged quarters is what it is. So `vss xbrl --limit 8` on LULU returned
eight quarters spanning **2023-07-31 to 2026-05-03 — nearly three years, with a
hole in every year.**

A reader who takes those eight rows as "the trailing eight quarters" is reading
the wrong window, and that is exactly the window §3 Gate 3 and §4.2.1 ask for.

`untagged_tail()` already exists and reports the newest such gap. **It does not
report the interior ones**, and it does not derive them.

**Shape of the fix:** derive Q4 as `annual − Σ(the three tagged quarters)` and
emit it with a provenance marker saying so. FRAMEWORK §4.1 expressly permits the
derivation — *"derive quarterly figures from cumulative reports where necessary
and say so"* — so the requirement is the marker, not the arithmetic. Where the
three quarters or the annual figure are not all present, emit nothing.

**Worked by hand for LULU** in `lulu-scoring-evidence.md`; the three derived
quarters are marked **D** in the eight-quarter table there.

---

## B-3 — the fiscal period label is wrong for a year-end that straddles Jan/Feb

**Found:** 2026-08-23, LULU.

`fiscal_year_end_month()` takes the **mode** of the months in which the filer's
annual periods end. LULU's fiscal years end on the Sunday closest to 31 January,
so they fall on both sides of the boundary — 2024-01-28, 2025-02-02, 2026-02-01.
The mode picked **January**, and `fiscal_period()` then shifted every label.

> The quarter ending **2026-05-03** is LULU's **fiscal 2026 Q1**.
> `vss xbrl` labels it **`2027-Q2`** — wrong by one quarter and by one year.

The figures and their XBRL contexts are correct; only the labels are wrong. A
watchlist populated from the emitted YAML would carry the wrong `period:` on
every row, and the earnings module reads `period`.

**Shape of the fix:** the boundary is a 52/53-week retail calendar, and the mode
is the wrong statistic for it. Anchoring on the **most recent** annual period end
rather than the modal month would have given February and the right labels; so
would treating year-ends within a few days of a month boundary as one calendar
anchor. Either needs a test built on a 52/53-week filer — LULU is one, and its
facts are already the fixture.

---

## B-4 — one run can price two candidates on two different days

**Found:** 2026-08-23, comparing the stored snapshot against a live `vss run`.

The run dated **2026-08-21** priced `LULU` on its **2026-08-21** close and
`PNDORA.CO` on its **2026-08-20** close. `PNDORA.CO`'s newest stored row is
08-20: the snapshot has no 08-21 bar for that ticker, although its `asof` is
08-21 and Copenhagen had closed.

The staleness gate passes a one-day-old close and is right to —
`MAX_CLOSE_AGE_DAYS` exists for genuinely dead series, not for this. But
**Gate 1's band has hard edges**, and PNDORA.CO sat six tenths of a percentage
point inside one of them while being measured on a different day from the name
beside it. The drawdown, the 52-week high and the B1 metric are all struck on
whatever the newest row happens to be, per ticker.

**Shape of the fix:** it is a reporting gap before it is a filtering one. The
snapshot knows each ticker's newest close date — `filter1-candidates.csv`
already carries `last_close_date` per row — but **nothing aggregates it**, so no
report says "this run priced 1,364 candidates across two dates" or names the
stragglers. Count and name them, the way the fetch-status distribution is
counted and named. Whether a candidate a day behind should be held back is a
rule question and belongs in `FRAMEWORK-EDITS.md`, not here.

*Related but separate: E11, where the same comparison showed a 52-week high
ageing out of its rolling window.*

---

## B-5 — a stock split enters the EPS series unflagged and breaks the valuation

**Found:** 2026-08-23, DECK. **The largest of these so far, because it silently
changes a number §5 multiplies by.**

DECK split **6-for-1 on 2024-09-17** (`StockholdersEquityNoteStockSplitConversion
Ratio1` = 6, 10-K `0000910521-25-000017`). The annual diluted-EPS series that
comes out of companyfacts is:

```
    FY2021  13.47   28,406,000 shares    PRE-split
    FY2022  16.26   27,789,000 shares    PRE-split
    FY2023   3.23  160,111,000 shares    post-split
    FY2024   4.86  156,285,000 shares    post-split
```

**One series, a 6x step in the middle, and nothing flags it.** The reason is
that nothing was restated: a 10-K carries three years of income statement, so
FY2022 had already dropped out of the comparatives before the split happened.
No later filing re-reported it, so the newest-accession rule correctly returns a
figure on the old basis. **The record is right and the series is unusable.**

The price series is split-adjusted throughout, so pairing them divides one year's
P/E by six.

> **What it costs.** FRAMEWORK-EDITS **B5**'s A7 proxy is the five-year median
> trailing P/E, and §5.1 Method A multiplies NTM EPS by it. Taken as filed,
> DECK's FY2022 P/E reads **4.09** and the median comes out **16.38**. On the
> post-split basis it is **24.55**. **A 33% understatement of the multiple every
> Method A fair value is built on**, from a number that is correct, unflagged,
> and in the wrong unit.

**And the QUARTERLY case fires a notice that names the arithmetic, not the
cause.** `vss xbrl` reported *"RESTATED SINCE FIRST FILED — 2025-Q1
EarningsPerShareDiluted: 4.52 -> 0.75"*. That is 4.52 / 6. The notice is
literally true and sends the reader looking for an accounting problem that does
not exist.

**Shape of the fix, two parts:**

1. **Detect it.** `StockholdersEquityNoteStockSplitConversionRatio1` is tagged by
   the filer with the effective date, and it is in companyfacts already. Read it,
   and mark every per-share figure whose period **ends before the split date** as
   being on a different basis. That is a fact from the filer, not a heuristic.
2. **Say which kind a restatement is.** When a restated per-share value differs
   from the original by the split ratio (or a power of it) to within rounding,
   the notice should say **SPLIT-ADJUSTED**, not RESTATED. Same shape as E8's
   unit check: a round factor is a change of unit, not a change of measurement.

*Whether to rescale the old figures or merely to refuse them is a judgement and
belongs in `FRAMEWORK-EDITS.md`. Detecting and naming the break is not.*

*Not tested on LULU: it has had no split in the window, so its five-year EPS
series is on one basis and the A7 proxy of 31.35 is unaffected.*

---

## B-6 — B7's inventory materiality floor is not in `rules.py`

*Carried in from the session notes of 2026-08-22, not found tonight. Listed so
the file starts complete; delete it if it has since been done.*

FRAMEWORK-EDITS **B7** (decided 2026-08-21) exempts the inventory limb of §4.2's
seventh hard kill for companies whose inventory is under 2% of annual revenue.
The rule is decided and applied by hand; it is not implemented.

*It did not bite on LULU: inventory is **15.3%** of FY2025 revenue, far above the
floor, so the limb applied and was evaluated.*

---

## B-7 — the eight-quarter rule does not exist for a half-yearly reporter

**Raised:** 2026-08-24, by the owner, on the schema session for manually
entered fundamentals.

**The window conversion is already built. What the window contains is not.**
`rules.py` converts every §4.2 window by TIME — `PERIODS_PER_YEAR`,
`periods_for`, `period_unit` — so "trailing 8 quarters" reads as four
half-years on a `half_yearly` ticker and "2+ consecutive quarters" as one.
That machinery is not the gap. The gap is that **three of the rules stated in
eight-quarter terms have no code at all**, so there is nothing for the
conversion to convert, and each of them breaks differently when the
observation count halves:

| Rule | Implemented? | What halving the observations does to it |
|---|---|---|
| **B4** — §3 Gate 3, gross margin: every quarter within ±200bps of the 8-quarter mean | **No code.** Decided 2026-08-21, applied by hand. | The band was calibrated on **quarterly** dispersion. Four half-year observations are a different population — half-yearly figures average away the intra-half seasonality the ±200bps was sized against, so the same band is materially SLACKER on a half-yearly name than on a quarterly one. Converting the window leaves the threshold measuring something else. |
| **B9** — §4.2.1 measures demand, not portfolio change | **No code.** Decided 2026-08-22 on UNA.AS, applied by hand. `config/screener_filter2.yaml` cites it as the reason the revenue limb is a FLAG and not a KILL. | Needs the organic / constant-currency bridge from the filing. A half-yearly reporter publishes that bridge twice a year at most, and its Q1/Q3 trading statements are turnover-only. "Positive in every period of the window" is being asked of a series that has half as many points and a different disclosure behind each. |
| **Gate 3's FCF leg** — FCF positive in ≥ 6 of 8 quarters | **No code, and the coarse stand-in already deviates.** `config/screener_filter2.yaml` replaces it with the SIGN OF TTM FREE CASH FLOW, saying so, because quarterly cash-flow history comes back with 5–7 columns for most names and zero for some. | **The sharpest of the three.** A half-yearly reporter frequently publishes **no cash-flow statement at Q1 or Q3 at all** — `scratch/build_una_valuation_xlsx.py`'s README records that every R12M cash figure for UNA.AS had to be STITCHED from three filed columns (FY2025 − H1 2025 + H1 2026) because Q1/Q3 are turnover-only trading statements. "6 of 8" has no half-yearly analogue that preserves its meaning: 3 of 4 is a different test, and there is no honest way to say which. |

**Why this is a backlog entry and not only a rule question.** The defect is
that the code gap and the rule gap are the same gap and neither file records
it: `rules.py` looks like it has handled half-yearly reporting because the
window arithmetic is there, and `FRAMEWORK-EDITS.md` records B4 and B9 as
DECIDED with no note that the decisions were taken on quarterly names and do
not carry over. A reader of either file alone concludes the case is covered.

**Shape of the fix, in two parts, and only the first belongs here:**

1. **Here.** Nothing implements B4, B9 or Gate 3's FCF leg. Say so where a
   reader will look — B4 and B9 should carry a scope line naming the names
   they were decided on, and `screener_filter2.yaml`'s FCF deviation note
   should say that its own stand-in degrades further on a half-yearly name.
2. **Not here.** Whether ±200bps, "positive in every period" and "6 of 8"
   should be restated for a half-yearly reporter — and at what numbers — is a
   RULE question and belongs in `FRAMEWORK-EDITS.md` under the next free
   letter, **B12** — B11 was taken on 2026-08-24 by B-8's question, on the
   owner's instruction. Proposed, not decided: state the three rules in TIME
   rather than in observation counts (a trailing 24 months; positive in ≥ 75%
   of the periods that window contains), and record for each the population
   its threshold was calibrated on. **The owner decides; this entry does not.**

**Scope note — this is not only a UK problem.** It was raised on UK issuers,
where the DTR half-yearly regime makes it universal, but it is a reporting
FREQUENCY problem and `reporting_frequency: half_yearly` is already carried
per ticker rather than per market. UNA.AS is Dutch-listed and hits it in full.

*Related: `vss/manual.py`'s schema (2026-08-24) stores one entry per fiscal
period at whatever resolution the company reports, so a half-yearly file is a
first-class citizen there. That makes the input side ready and leaves the
three rules above as the whole of the remaining gap.*

---

## B-8 — the ranking key reads one period, and does not ask how long it is

**Found:** 2026-08-24, on the first `vss appendix` run, PNDORA.CO.

The E6 key's quality leg is `Gross Profit / Total Assets`. `latest()` returns
the newest stored value of each line and **nothing anywhere asks what LENGTH of
period that value covers.** It has never had to: the vendor path stores
`income_stmt`, which is annual, so every ranked name has been on one basis by
construction.

A hand-entered or appendix-read file need not be. `config/manual/PNDORA.CO.yaml`
now holds **fourteen QUARTERS**, and the key reads the newest of them:

```
    gross profit 5,808 (2026-Q2)  /  total assets 29,232  =  19.9%
    the 2026-08-21 screener run, on the vendor's ANNUAL figures  =  87.0%
```

**Same company, same ratio, a factor of four apart, and neither number is
wrong.** One is a quarter's gross profit over the balance sheet; the other is a
year's. Ranked in one list they are not comparable, and nothing in the CSV says
which is which — the new `origin` column says where a row came from, not what
period length it was struck on.

**The earnings-yield leg has the same shape and is worse**, because the
denominator is not a period at all: `EBIT / enterprise value` divides one
quarter's operating profit into a market value of the whole company, which
understates the yield by roughly four.

**Shape of the fix, and only the first half belongs here:**

1. **Here. DONE 2026-08-24**, with E13, since both touch the same read.
   `SeriesPoint.period_months` carries the length, `fundamentals_series`
   stores it, and `ranking.csv` names the basis and the periods summed. The
   original text follows.

   Nothing records the period LENGTH beside a ranked figure.
   `SeriesPoint` carries `period_end` and `statement` and not the span;
   `ranking.Inputs` carries three period dates and no duration. Carry it, and
   name it in `ranking.csv` beside `origin`, so a reader can see a quarter
   sitting in a list of years. That is the same fix as E11's peak date: a fact
   the arithmetic depends on that nothing currently writes down. **This half is
   not waiting on B11** — the CSV cannot say which rows are on which basis
   whatever B11 decides.
2. **Not here.** What the key should DO about it — rank annual only and exclude
   the rest; sum four quarters into a trailing twelve months (which this project
   does not do, and `vss/appendix.py` is expressly forbidden from doing);
   require an annual column in a manual file before the name may be ranked — is
   a RULE question. **Written up as FRAMEWORK-EDITS B11 on 2026-08-24 and
   SETTLED THE SAME DAY BY E13: trailing twelve months, flow lines summed over
   four consecutive quarters and stock lines at the latest period end.** Not
   implemented yet.

*Not a defect introduced by the appendix path: it is true of any manual file
whose periods are quarters, and `config/manual/TEMPLATE.yaml` has always
permitted that. The appendix run is simply the first time a quarterly file has
existed.*

*Section 5 is unaffected — it refuses on UNVERIFIED figures and reads the period
it is handed, whose label is on the entry. This is the RANKING key's problem
alone.*

---

## B-12 — tier C's floors are CONFIG that nothing applies, so tier C cannot be populated

**Found:** 2026-08-31, widening the universe to tier B. **Confirmed by the
owner 2026-09-01: tier C stays empty until the floors are implemented.
A separate build, not started.**

`config/universe/floors.yaml` has carried tier C's floors since phase 1:

```yaml
  C:
    market_cap:            {min: 300000000, currency: EUR}
    median_daily_turnover: {min: 2000000, currency: SEK, window_days: 90}
    listing_age:           {min: 5, unit: years}
```

`vss/universe.py` **loads and reports them and applies none of them**. That
was correct and harmless while tier C was empty — the file's own comment says
"phase 1 loads and reports the floors, phase 3 applies them", and phase 3
avoided it because applying a EUR floor across fifteen quoting currencies
needs an FX source at universe-load time, which the load path does not have.

**Why it matters now.** Tiers A and B are index membership, and *membership
is the floor* — that is why they need no numeric one. **Tier C is "everything
else Avanza can trade", where the floors do all the work.** Putting a single
name into tier C today would put it into the screen with **no market-cap floor
and no liquidity floor at all**, and the owner's words on 2026-09-01 are the
reason that is not a small thing: *"screening without a market-cap or
liquidity floor would admit names where half the method does not apply."* A
name that trades EUR 40k a day cannot be exited at anything like the price a
screen prints for it, and Gate 1's drawdown is noise on a series that gaps.

**Nothing was lost by leaving C alone on 2026-08-31.** The Nordic mid caps
belong in tier B by `floors.yaml`'s own definition ("OBX / OMXC / OMXH
Large+Mid"), so the widening needed no part of tier C.

**Shape of the fix, when it is built:**

1. an FX source available at universe-load time, or floors expressed per
   quoting currency and converted at BUILD time with the rate and its date
   recorded in the meta (E98) — the second is what `nordic-mid` already does
   for its EUR 150m cut, and it needs no runtime FX at all;
2. median daily turnover over 90 sessions, which needs the price snapshot —
   so this floor cannot run at universe-load time and belongs in filter 1
   beside the series checks, as its own countable step;
3. the listing-age floor is **already implemented** as E52's five-year bar
   and applies to every tier, so tier C needs nothing new for it;
4. every floor a countable step in the yield table, rejecting ON VALUE where
   a figure says so and ON MISSING where there is no figure — never one
   number for both, the rule the rest of `universe.py` already keeps.

**Until then `tier-c-*.csv` stays empty and the loader keeps being exercised
against an empty tier**, which is what its meta has said since 2026-08-22.

---

## B-13 — `vss-notify-failure.sh` says "no report was written" whichever unit failed

**DONE 2026-09-13.** The script branches on the unit name `vss-failure@.service`
passes in: `vss.service` and `vss-screen.service` keep the run sentence;
`vss-overview.service` and `vss-checkin.service` say what they are; an
unknown unit says only that it is not a run. Nothing about the topic, the
POST or the exit code moved (E92). Tested in `tests/test_heartbeat.py`. The
original entry follows.

**Found:** 2026-09-13 12:06, when `vss-overview.service` restart-looped seven
times and sent seven ntfy alerts (TUNNEL-NOTES, bug 2).

`deploy/vss-notify-failure.sh` reports *"no report was written for this
date"* regardless of which unit triggered it. That is false for
`vss-overview.service` — a static server dying writes no report because it
never writes one — and false for any future non-run unit. The body is written
once for the nightly run and every other caller inherits its wording.

**Shape of the fix:** branch on the `%n` instance name passed in by
`vss-failure@.service`. The run units keep the "no report was written"
sentence; any other unit gets a body that says what actually stopped.

---

## B-14 — the overview generator renders no generation timestamp and never marks the page stale

**DONE 2026-09-13.** Requirement 1 is implemented in `vss/render.py`: the
header and the footer's first sentence both render `ov.generated` as ISO 8601
with offset. Requirement 2 was **withdrawn by F2** as unbuildable — a static
file cannot compare its own age at read time without JavaScript, which F1
limb (b) prohibits. See FRAMEWORK-EDITS **F2**. The original entry follows.

**Found:** 2026-09-13. Required by ruling F1 limb (c), FRAMEWORK-EDITS.

The overview generator does not render a generation timestamp and does not
mark the page stale. Two parts:

1. render the generation time, ISO 8601 with timezone, in the page header,
   visible without scrolling on a phone;
2. when now minus generated exceeds 26 hours, mark the page stale so it
   cannot be missed at a glance.

**Until both are done the page is non-compliant with F1.**

**Do not implement it from this entry without reading F1 limb (c) first** —
the 26 is tied to `vss.timer` firing at 22:30 CEST and is not a free
parameter.

---

## B-15 — Gate 3 interest coverage is DATA MISSING on 13 stores

**Found:** 2026-09-19, CTSH's review (the owner: "log the 13 coverage DATA
MISSING names as a backfill item; it doesn't block CTSH").

`manual.interest_coverage` cannot form on the section 5 basis because
`operating_income` and/or `net_finance_costs` (or its two halves,
`finance_costs_period` / `finance_income_period`) are not on file:

| name | status | missing on the basis |
|---|---|---|
| LIAB.ST | HELD | operating_income, net_finance_costs |
| SAP.DE | WATCH-PRICED | operating_income, net_finance_costs |
| GDDY | WATCH-PRICED | operating_income |
| DECK | WATCH-GATED | operating_income |
| HRB | WATCH-GATED | operating_income, net_finance_costs |
| NVR | PIPELINE | operating_income |
| ZZ-B.ST | PIPELINE | operating_income |
| ACN | INTAKE | operating_income |
| AOS | INTAKE | operating_income, net_finance_costs |
| LII | INTAKE | operating_income |
| LOPE | INTAKE | operating_income, net_finance_costs |
| MUSA | INTAKE | operating_income, net_finance_costs |
| ULTA | INTAKE | operating_income |

**Shape of the fix:** the US names' figures are tagged (`OperatingIncomeLoss`,
`InterestExpense*`, `InvestmentIncomeInterest*`) and go on file as CTSH's did
on 2026-09-19; the IFRS names' come from the income statement by hand. MC.PA
has no store at all. The five ratios that DO form on IFRS names (PNDORA.CO,
AUTO.L, NHY.OL, MEKKO.HE, RKT.L) are not yet rent-bearing: E117 clause 5.

---

## B-16 — screener newcomers: intake deferred until the watchlist's open decisions are cleared

**Logged:** 2026-09-19 (owner, C4: "not now. Log to backlog; no new names until
section A is cleared").

New in the screener's top 20 and not on the watchlist: MAS, TPR, FOXA, WKL.AS,
BKNG, G, GAP, GNTX, RVRC.ST (the 2026-09-19 screen; BOUV.OL has a store and a
record but no entry). **No store is built and no entry written until the
section-A decisions of 2026-09-19 are closed.**

## B-15 addendum, 2026-09-19 — what C3 could and could not fill

Filled from tagged 10-K facts (or read back): GDDY, ACN, DECK, LII, ULTA
(coverage forms), AOS and LOPE (leverage forms). Still DATA MISSING, and NOT
derived: **HRB** and **NVR** state no operating income (HRB goes straight to
pre-tax income; NVR is segmented, homebuilding and mortgage banking);
**AOS** prints interest expense 13.5 as its only finance line (interest income
is inside "Other income, net"); **LOPE** has no debt and prints only
"Investment interest and other 13,941". Each is a ruling question, not a gap
a fill can close.

---

## DECIDED 2026-09-20 — not defects, and not to be re-proposed

Three things surfaced while `vss strike` and `vss watch --sec` were built.
The owner decided each of them the same day. **They are recorded here so a
later session does not raise them again as gaps.**

**1. `tier_before` reads the nightly database, and may differ from the tier
in force at the strike date.** `strike._tier_in_force` takes the tier from
the newest `run_metrics` row, because a run record carries no tier — the
tier is a §4.4 score on the watchlist. Where the database has nothing it
prints `--`. **That is the correct behaviour**: writing the tier into the
record would need a precedence rule for a conflict between the record's
tier and the entry's, **and that conflict has not occurred.** A rule
written for a conflict nobody has seen is a rule nobody can test.

**2. MC.PA, AUTO.L and RMV.L have no publication detection, and will not
get any.** The Nordic arm reaches Copenhagen, Stockholm and Helsinki; the
SEC arm reaches every filer with a CIK. Paris and London are neither.
**Those three names are covered by `catalyst_date`, maintained by hand**,
and **a Euronext or RNS route is not worth building for three names** —
the fetcher survey already priced it (FETCHER-SURVEY §3 and §4: the UK
answer is HTML rather than PDF, and the rest of Europe is twenty-seven
front doors with no common API). Revisit if the count grows, not before.

**3. CTSH's basis sitting a quarter behind its store is E19 working as
designed.** `vss strike` prints "the store's newest period is NEWER THAN
THE BASIS: a quarter has landed that this strike did not read", and that
is **the line doing its job, not a defect it found**. E19 chooses ONE
twelve-month window and a strike reads that window; a store holding a
newer quarter is the ordinary state between a filing and a re-basis. The
line exists so the distance is visible when a value is read.
