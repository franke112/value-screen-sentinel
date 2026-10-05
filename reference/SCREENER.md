# `vss screen` — the candidate screener

**Status:** phases 1, 2, 3, 5 and 6 built. Phases 4 and 7 planned, not built.
**Branch:** `screener`, off `pdf-primary-sources`.

## What this tool is for

The screener generates **review work, never a purchase**. Its final output is
three to five names entered as `PIPELINE` in `config/watchlist.yaml` **without
`mbp` and without `fv_base`**. The whole FRAMEWORK §5 chain — fair value,
margin of safety, maximum buy price — is run by hand afterwards. No code path
in the screener may set a buy price or a fair value, and phase 1 does not write
to the watchlist at all.

Three rules are load-bearing and are enforced by tests in `tests/test_screen.py`:

1. **DD and Gate 1 logic is imported from `rules.py`, never reimplemented.**
   `test_framework_constants_are_imported_from_rules_never_redefined` fails if
   a screener module redefines `DISLOCATION_MIN`, `DISLOCATION_MAX` or
   `MAX_CLOSE_AGE_DAYS`.
2. **RSI and SMA50 are FIELDS, never filters.** SAP.DE was bought on
   2026-07-27, four days after the bottom of a −47% drawdown, below its SMA50,
   and later printed RSI 75. A timing filter on either measure would have
   discarded the best case in the book during the exact week it was worth
   buying. The rationale is a comment in `vss/screen.py` and a test asserts it
   is still there.
3. **DATA MISSING is a third state.** Every filter step reports rejections
   split into *rejected on a value* and *rejected on the absence of a value*.
   They are never summed. `Tally` in `vss/universe.py` has two counters for
   exactly this reason.

## Architecture — two-step fetching

Bulk price history is cheap and batchable; fundamentals are one call per ticker
and do not scale to thirteen thousand names.

| step | what | phase |
|---|---|---|
| 0 | the exclusion list: names owned or already decided | 2 (built) |
| 1 | price the ENTIRE universe, batches of ~50, backoff, retry | 1 (built) |
| 2 | the dislocation filter runs on that snapshot | 2 (built) |
| 3 | fundamentals for the SURVIVORS of step 2 only | 3 (built) |
| 4 | the fundamentals filter runs on those | 3 (built) |

Every step's raw data is snapshotted per run under
`data/screener_snapshots/<ASOF>/snapshot.sqlite`, so any candidate list is
reproducible afterwards.

## Modules

| file | role |
|---|---|
| `vss/universe.py` | CSV schema validation, instrument-type exclusion, ISIN/ticker dedup, floors config, yield report |
| `vss/prices.py` | batched yfinance retrieval, backoff, retry, four fetch statuses |
| `vss/snapshot.py` | sqlite snapshot: raw OHLCV plus manifest, universe, rejections, merges, tallies, fetch statuses |
| `vss/fundamentals.py` | per-ticker fundamentals retrieval, two status layers |
| `vss/filters.py` | step 0, filter 1 (dislocation) and filter 2 (coarse quality) |
| `vss/fx.py` | exchange rates, once per run per pair, and the minor-unit mapping |
| `vss/series_sanity.py` | can a price series be measured at all? Scale switches and uncorroborated breaks |
| `vss/ranking.py` | share-class collapse and the two-component key -- the only ordering |
| `vss/pipeline.py` | phase 6: the ONLY module permitted to write the watchlist |
| `vss/screen.py` | orchestration and the three reports |
| `tools/build_universe.py` | BUILD tool. Writes the dated CSVs. Never called at runtime |
| `tools/probe_ranking_fields.py` | BUILD tool. The field-coverage measurement behind E5 |
| `tools/freeze_ranking_acceptance.py` | BUILD tool. Freezes phase 5's acceptance fixture. Never called at runtime |
| `tools/fetch_fx_manifest.py` | BUILD tool. Fetches the rates OF A NAMED DATE into a replayable manifest. Never called at runtime |

`sqlite`, not parquet: no `pyarrow` in the venv, and phase 1 is not the place
to add a dependency. One file per run, openable by any client months later.

## Phase 1 — what exists

```
python -m vss screen --universe-report
python -m vss screen --snapshot-only --asof 2026-08-21
```

Optional: `--tier A|B|C` (repeatable, default A), `--universe-dir`,
`--snapshot-root`, `--batch-size`, `--limit N` (smoke test only — the report
says loudly that the run was partial).

### The universe files

`config/universe/` holds STATIC, dated CSVs with a nine-column schema:

```
ticker_yahoo, ticker_lokal, isin, namn, marknad, tier, listdatum, valuta, instrumenttyp
```

`instrumenttyp` is the **ninth column, added to the specified schema**. It has
to exist: the exclusion rule says exclusions happen on instrument type *from
the source list*, never guessed from the name string, and the eight-column
schema had nowhere to put that type. Each list's `.meta.json` records which
field of which source it came from.

`ticker_yahoo`, `isin`, `namn`, `listdatum`, `valuta` and `instrumenttyp` may
be empty — that is DATA MISSING, counted in the report. `ticker_lokal`,
`marknad` and `tier` may not. A broken row aborts the run; nothing is skipped
silently.

Every CSV has a sibling `.meta.json` with the source URL, retrieval date, row
count, expected row count, an `approximation` flag and a sha256. The snapshot
records the sha256 too, so `snapshot.verify()` can prove a replay is reading
the same lists.

### The two reports

`--universe-report` — rows per source file with provenance marks, the yield
table, count per market, count excluded per reason, count without a valid Yahoo
mapping, ISIN coverage, both dedup layers, unresolved dual-listing candidates,
and the tier floors.

`--snapshot-only` — the same yield table extended with the fetch step, plus
fetch-status distribution, coverage per market, every not-OK ticker by name,
the snapshot's size on disk, and a reproducibility check.

### Fetch statuses

| status | meaning | fix |
|---|---|---|
| `OK` | a usable series arrived | — |
| `THROTTLED` | refused for rate reasons | wait, retry |
| `NO_DATA` | request succeeded, ticker absent from it | repair the symbol mapping |
| `STALE` | series arrived, newest close older than the gate | not a fetch outcome; decided by `rules.stale_close_blocker` |

`THROTTLED` and `NO_DATA` are kept apart deliberately. Lumping them together is
how a screener quietly shrinks its own universe on a bad network day.

**Known edge, not yet fixed.** Classification is per BATCH: when a batch's
final attempt failed with something that reads as rate limiting, every ticker
missing from that batch is marked `THROTTLED`. A genuinely bad symbol sitting
inside a throttled batch is therefore mislabelled and will look retryable
indefinitely. The fix is a single-ticker re-probe of a throttled batch's
missing names once the rate limit clears; it is not worth the requests until a
run actually gets throttled.

The retry and backoff path is verified by unit test only. The first full run
returned 1,370 of 1,370 OK on the first attempt, so `THROTTLED`, `NO_DATA` and
the backoff sleeps have never executed against live yfinance.

### `--asof` truncates, it does not merely label

yfinance answers with its latest session whatever date you ask about. Rows
dated after `--asof` are dropped before storage, so re-running
`--asof 2026-08-21` on the following Monday reproduces Friday instead of
quietly ingesting Monday.

---

## Phase 2 — what exists

```
python -m vss screen --filter1 --asof 2026-08-21
python -m vss screen --filter1 --asof 2026-07-27 --from-snapshot 2026-08-21
```

Reads a stored snapshot and fetches nothing. `--from-snapshot` defaults to the
oldest snapshot dated on or after `--asof`; a snapshot older than the run date
is refused rather than silently used, because it cannot hold that day's closes.
Candidates are written to `data/screener_runs/<ASOF>/filter1-candidates.csv`.

### Step 0 — the exclusion list

`config/screener_exclusions.csv`, four columns:

```
ticker_yahoo, skal, datum, kalla
```

Matched on `ticker_yahoo` exactly — never on name, never on ISIN. `skal` is
free text and is deliberately not validated against a vocabulary: the reasons
are the owner's and a new one must not need a code change. Every column is
required, a bad date is fatal, and one name may appear once — two rows mean the
file disagrees with itself about why.

Entries that match nothing are **reported as inert**. `UNA.AS` is exactly that
today: it is not in tier A, because the index carries Unilever's London line,
so both listings sit on the list and only `ULVR.L` actually fires. An inert
entry that reads as active is how an excluded name quietly comes back.

Its rejections count as **rejected on a value** — a dated decision is a value,
not missing data.

**Two kinds of row, and the difference is deliberate.** A row may state a
property that does not change between runs, or a property of one reporting
year. `UHS, E7, 2026-08-23` is the first kind: the quality leg overstates any
company that draws its cost-of-revenue line above its own production wages,
and where that line sits is the company's presentation choice, so the row
stands until someone deliberately removes it. `ROCK-B.CO, E8-REVIEW,
2026-08-23` is the second: ROCKWOOL's chosen EBIT label for FY2025 is stated
before a 392 MEUR value adjustment while the other label is stated after it,
and when FY2025 leaves the accounts the two may agree again and the exclusion
become wrong. **A dated row says so in its own reason, beginning `REVIEW
WHEN`, and carries `E8-REVIEW` rather than a bare edit number in `skal`** — so
the report prints the difference and a later reader does not have to go and
find out which kind a row is.

### Filter 1 — the dislocation band

`rules.in_dislocation_band`, imported. Nothing in `filters.py` restates the
band; a test asserts the module contains neither bound as a literal.

Rejection kinds, kept apart:

| step | on a value | on missing data |
|---|---|---|
| `price_coverage` | newest close older than the staleness gate | no series in the snapshot; no close at or before the run date |
| `series_sanity` | *(never)* | the series alternates between two scales, or carries a break the tape does not corroborate |
| `dislocation` | drawdown outside 15–50% | drawdown not computable (no 52-week high) |

#### Series sanity — the check that asks whether the number is a measurement

`snapshot.verify()` proves the **right file** was read. Nothing asked whether
the **contents** were plausible until this step existed. The case it exists for:

> **MNST**, July–August 2026, the closes actually stored: `07-31 48.19`,
> `08-03 93.55`, `08-05 94.46`, `08-06 47.08`, `08-07 90.36`, `08-11 45.53`…
> The feed alternates between the split-adjusted and unadjusted scale for four
> weeks. Read straight, that is a 52-week high of 99.94 on one scale against a
> last close of 47.79 on the other — **a 52.2% drawdown where the truth is
> about −4%.** The name was rejected as structurally damaged, for the right
> reason on the wrong grounds. Had the split been 3:2 the same corruption
> would have landed *inside* the band.

Two checks, over the same trailing 365 days the 52-week high reads:

- **Scale switch.** A move beyond 1.6× answered within 90 days by its
  near-reciprocal. **A corporate action happens once** — a split does not
  un-split, a spin-off does not re-merge — so only a feed quoting two scales
  goes back. This is the check that *proves* its claim.
- **Uncorroborated discontinuity.** A move beyond 1.6× on under **3× the
  name's own median volume**. A real repricing of that size trades; a split, a
  spin-off, a rights issue or a mis-scaled row does not. It does not claim the
  data is corrupt — Electrolux's spin-off and Ørsted's rights issue are real
  events correctly priced. It claims the narrower thing that holds for all
  three causes: **the 52-week high on the far side of the break is not
  comparable with today's close, so the drawdown across it is not a
  measurement.**

The volume test is what separates the two families, and the gap is wide.
Measured over the whole 1,370-ticker snapshot: every violent *repricing* came
on 8.8× to 96.7× its median volume — MRNA +177% on 23.8×, ABVX.PA −44% on
14.2×, VPLAY-A.ST −46% on 30.8×, SUS.ST −60% on 96.7× — while every *break*
came on 0.2× to 2.6×. A missing volume is an **absence of corroboration**,
never corroboration.

**A flagged name is rejected on MISSING data, never on value.** It did not
fail the band; the band could not be evaluated for it.

Measured on the 2026-08-21 run — the whole universe, reported by name:

| ticker | check | evidence |
|---|---|---|
| MNST | scale switch | 2026-07-20 −51% then 07-23 +96%, product 0.957 |
| ELUX-A.ST | uncorroborated | 2026-05-19 −48% on 0.2× median volume |
| ELUX-B.ST | uncorroborated | 2026-05-19 −46% on 1.4× |
| ORSTED.CO | uncorroborated | 2025-09-08 −45% on 1.1× |

**Four of 1,364, one of them inside the band** (ORSTED.CO), so the candidate
list goes 536 → 535. Nothing else in the universe is touched, and the tests
include the real stored MNST, MRNA and ELUX-A.ST rows rather than hand-built
ones — the review of 2026-08-22 noted that every fixture was well-formed and
that the MNST corruption would have passed all 954 tests.

*Not covered, and named: MRNA's 16.8% drawdown is measured against a peak set
two days earlier. Its +177% session came on 23.8× volume, so it is a real
repricing and this check passes it correctly. That the band calls a recoil a
dislocation is a different fault — it is K3, and it is open.*

Fields carried, never filtered on: `rsi14`, `sma50`, `sma200`, `pct_vs_sma50`,
`pct_vs_sma200`, `volume_ratio`, the B1 metric, and — since E63 (2026-08-28) —
`low_52w`, `low_52w_date` and `pct_above_52w_low`: the 52-week closing low on
the same window and coverage bar as the high, and how far the close sits above
it. The band cannot tell a name that fell and stayed down from one that has
since recovered; this column can. Reported and never applied; whether it
becomes a filter is B41, open.

Candidates are ordered by ticker. That is an order, not a ranking.

`metrics.compute` truncates to the run date before measuring, so a replay is
priced at that date and not at the snapshot's edge — that fix is in `metrics`,
in its own commit, and it is what makes this honest. `rules.in_dislocation_band`
was extracted first, also in its own commit, with the baseline green across it.

The B1 metric — `(close_180d_ago − last_close) / (high_52w − last_close)` — is
computed and shown. Per FRAMEWORK-EDITS B1 as decided 2026-08-22 it is context,
not a limb: Gate 1 measures today's position.

### The acceptance test

`tests/test_filters.py::test_acceptance_filter1_replayed_on_2026_07_27_contains_sap`

It calls `run_filter1` **directly**, on the whole universe, not the chain —
SAP.DE is on the exclusion list, so a chain run would remove it at step 0 and
the test could not tell a broken filter from a working exclusion. It runs
against a snapshot built from the committed, frozen price fixtures, so it is
offline and only a code change can alter its answer.

A second test guards the way it could pass falsely: the snapshot runs to
2026-08-20, where SAP's drawdown is 23.3% — also inside the band. If truncation
regressed, the acceptance test would still pass while measuring the wrong day.
That test asserts July and August differ.

**Result: SAP.DE is present.** Close 151.28 as of 2026-07-27, 52-week high
254.75, drawdown 40.6%, B1 0.43, RSI 62.3, 5.0% above its SMA50.

---

## Phase 3 — what exists

```
python -m vss screen --fundamentals --asof 2026-08-21
python -m vss screen --filter2 --asof 2026-08-21
```

`--fundamentals` fetches only the survivors of filter 1, **one ticker at a
time**, two requests each: the quote summary, and the annual income statement
(a revenue trend is not a scalar, and the summary's `revenueGrowth` is a single
year-over-year number). It stores to
`data/screener_snapshots/<ASOF>/fundamentals.sqlite` — beside the price
snapshot, not inside it, because the price snapshot is the reproducibility
artefact and appending a later-dated fetch would make one file describe two
moments.

### Two status layers

Per ticker: `OK` / `THROTTLED` / `NO_DATA` / `STALE`. Per field: `OK` /
`NO_DATA`, and `THROTTLED` when the whole ticker was refused. A bank returns
cash and debt but no EBITDA at all, so a ticker-level `OK` would hide exactly
the gap that decides whether a limb can be evaluated.

`STALE` is again decided after the data arrives, from the newest reported
period rather than from the fetch.

### Filter 2 — coarse quality

Mechanism in `vss/filters.py`, **values in `config/screener_filter2.yaml`**,
each carrying the FRAMEWORK section it came from. A test asserts no threshold
is hardcoded. Decided 2026-08-22 as FRAMEWORK-EDITS E2, E3 and E4:

| limb | rule | source |
|---|---|---|
| `free_cash_flow` | TTM free cash flow > 0 | §3 Gate 3, coarsened — see below |
| `net_debt_to_ebitda` | ≤ 3.5x; NOT APPLICABLE for Financial Services and Real Estate | §4.2.5 hard kill (E2), exemption per E3 |
| `revenue_trend` | FLAG at 2 consecutive annual declines, never a kill | §4.2.1 softened per B9 |
| missing data | `pass_through`, counted apart | E4 |

**What an FCF pass means.** Gate 3 asks for FCF positive in ≥ 6 of 8 quarters.
That test is not computable from this source — quarterly cash-flow history
returns 5–7 columns for most names and none at all for some — so the limb tests
the sign of TTM free cash flow instead. Therefore: *a name passing here has NOT
passed Gate 3's FCF limb. It has failed to fail it, on one year rather than
eight quarters.* The manual chain still runs the real test.

**Which leverage cap.** 3.5x, the §4.2.5 hard kill, not Gate 3's 2.5x. A gate
is decided with the whole picture in view; a hard kill is not, and a step that
never reads the report may only enforce the latter. The margin is real: 2.5x
would have cut the survivor list from 402 to 333.

### The look-ahead limitation, printed not hidden

yfinance serves historical prices but only the **latest** fundamentals. Both
phase-3 reports carry a banner naming the two dates — the accounts' publication
date and the price date — and, when they differ, stating that the result is not
evidence of what a screener would have found on that day and that no
retroactive reading may be placed on it.

---

## Phase 5 — what exists

```
python -m vss screen --rank --asof 2026-08-21
```

Runs the whole chain, then ranks the survivors. Fetches only the exchange
rates it needs. Full list to `data/screener_runs/<ASOF>/ranking.csv`, FX to
`ranking-manifest.json`.

```
gross profitability = Gross Profit / Total Assets      (Novy-Marx 2013)
EY                  = EBIT / enterprise value
```

Ranked separately on each, the two placings summed, sorted ascending. No
weighting, no thresholds, no score. Decided as FRAMEWORK-EDITS E6.

**The quality leg was replaced on 2026-08-22.** E5 used Greenblatt's
`EBIT / (net working capital + net PP&E)`. That denominator is a difference
between large numbers, so it goes to zero for float-funded, asset-light
businesses, and for a given EBIT the ratio is monotone in `1/denominator` —
measured on the 2026-08-21 run, the **thirteen names whose capital employed was
under half a year's EBIT held quality placings 1 to 13, without exception.**
Total assets is present for every candidate (394 of 394) and cannot go to zero.
Rebuilding that run under the new leg replaced **all five** PIPELINE names; the
side-by-side top-20 is the measurement in E6. The price leg's *definition* is
unchanged; its rank *numbers* are not, because the two-legged population it is
ranked within grew from 314 to 329.

**This is the only place in the tool where an ordering arises.** Every other
step is a filter with a pass, a fail and a third state. It is still not a
recommendation: the output is review work, and the §5 chain is run by hand.

### Five rules the code may not soften

**EBIT comes from an alias set ordered on MEANING, with a year and a unit
attached** — `Total Operating Income As Reported`, then `Operating Income`,
then `EBIT`. Decided as FRAMEWORK-EDITS **E8**, reversing E5's order. E5
chose on coverage; tested against 32 US names' own 10-K filings the last of
those three labels matches the filed `us-gaap:OperatingIncomeLoss` for **6 of
32** and the first for **30 of 32**, and `EBIT` runs HIGHER than the filed
line for 67% of names — which is a higher earnings yield, which promotes.

**The fiscal year is settled before the label.** The labels stop in different
years: 9 of 394 candidates carry the preferred label for a year end between
2021 and 2024 while both others carry 2025. The alias is chosen among those
reporting the **newest** year end any of the three has, and meaning decides
within it. Without that, eight of those nine would be scored on a figure up
to five years old and then excluded by the staleness gate — one of them NVR,
at place 20.

**Two labels for one year end a round power of a thousand apart are one
figure in two units**, and the EBIT is **DATA MISSING**, named. MONC.MI
carries `Operating Income` 913,356,000 and `Total Operating Income As
Reported` 913,356 for 2025-12-31: identical digits, ratio 1000.000. Measured
over every pairwise alias ratio of all 394 candidates this fires on MONC.MI
and on nothing else at every tolerance from 1e-9 to 1e-2; the recorded
tolerance is 1% and the next-nearest ratio in the set is 281.7×, a factor of
3.6 below the boundary. The right unit is inferable from revenue and is
deliberately **not** inferred — the price of refusing is one name of 394.

**`ebitda` is never a substitute** for any of them: it adds back D&A, which
flatters exactly the heaviest balance sheets. A test parses the module and
fails if any non-docstring string or identifier names an ebitda field.

**The quality leg's two lines have NO alias set** — the exact labels
`Gross Profit` and `Total Assets`. Measured: every candidate that presents the
concept presents it under those labels, so an alias set would exist to catch a
spelling that does not occur. A test asserts a variant spelling is *not* picked
up, because a silent fallback would look like a company not reporting gross
profit.

**An absent line is DATA MISSING, never zero.** ASM.AS has no `Long Term Debt`
line because it has no long-term debt; a bank has no `Gross Profit` line
because its accounts do not present the concept. Different facts, neither zero.

**A PRESENT line need not be the concept its label names — E7, a known
limitation, deliberately not fixed.** Where "cost of revenue" is drawn is an
accounting presentation choice. For UHS the feeder's cost of revenue is
`SuppliesExpense` alone — 1,659.0 of 15,370.8 MUSD of operating expenses,
with the 8,084.6 MUSD of wages a hospital actually runs on sitting *below*
the gross-profit line — which put a 90.4% gross margin and a 101.1% GP/TA at
**rank 1** of the 2026-08-21 run. On every defensible recomputation the name
leaves the top five. **No threshold is built**, and that is the finding, not
an omission: the signal `(GP − EBIT) / revenue` catches UHS at 78% and also
catches ADBE at 51% and PNDORA.CO at 55%, both of which are correct, and
nothing stored separates them. The plausibility test on gross margin belongs
to FRAMEWORK §5. The screener's part is to print the ratio — the top-20 table
and every row of `ranking.csv` carry it — and no code path judges it.

**A negative gross profit is RANKED, last — not excluded.** Cost of revenue
above revenue is a fact about the business; a non-positive denominator is a
fact about the arithmetic. One belongs at the bottom of the list, the other
belongs in the one-legged section. Measured on 2026-08-21: one name (VEFAB.ST,
−0.6%).

**The quality leg's two lines must come from one fiscal year-end.**
`TickerFundamentals.latest` is called once per line and nothing else makes
them agree. Two year-ends in one quotient is not a ratio of anything, so it is
**DATA MISSING**, counted apart from an absent line — *we have both and they
do not belong together* is a different fact from *one of them is not there*.

`newest_period` cannot catch it: that field is the **max over every stored
row**, so a record whose ranked lines are a year apart still carries the newer
date and still reads `OK`. SHL.DE did exactly that under E5. On 2026-08-21 the
guard fires on **2 of 327** — AUTO.L (gross profit 2024-03-31 against total
assets 2026-03-31) and BAB.L (2022-03-31 against 2026-03-31) — and AUTO.L was
standing at **12 in the top 20**. Both keep their earnings yield and move to
the one-legged section: the price leg is one line divided by one quote, and
there is nothing in it for two periods to disagree about.

The three periods are written into `ranking.csv` beside their figures
(`gross_profit_period`, `total_assets_period`, `ebit_period`), so the check is
auditable rather than merely asserted.

**A STALE record is excluded from the ranking, counted and named — and the
age is measured on the rows the key ACTUALLY READS (L4).** Two questions are
asked, both at 550 days. First the record's own flag: `fundamentals.py` marks
a record STALE when its newest reported period is older than the limit. Until
2026-08-22 the flag was computed, printed, and read by nothing — **BWY.L was
ranked on an EBIT from 2024-07-31 against an enterprise value from
2026-08-21**, 751 days in one quotient, and neither `ranking.csv` nor the
report said a word about it. A stale record is dangerous precisely because
every leg computes.

Second, the question that flag **cannot** answer. `newest_period` is the max
over every stored row, including rows no component touches.

> **SHL.DE.** Gross profit, total assets and EBIT were all from **2024-09-30**
> — **690 days** before the run — and the record read `OK` at rank 246,
> because the only rows carrying 2025-09-30 were **Net PPE and Ordinary Shares
> Number**, neither of which is in either quotient. **COLO-B.CO is the same
> 690 days old and was excluded.** Same age, opposite treatment, decided by a
> row no leg touches. This is the same mechanism the paragraph below cites as
> the reason K6's guard has to exist, and K5 was still resting on it.

**Only periods that fed a component that COMPUTED are measured.** A quality
leg the sector exemption never evaluated does not count; nor does a pair of
lines already refused for disagreeing — AUTO.L's gross profit is 873 days old
and its state is `periods do not match`, which is a statement about two lines
that do not belong together, not about their age. Measuring wider than the
rows that were read would make K6's finding disappear behind this one.

Excluded as a rejection **on a value** — figures we have, judged too old, the
same shape `prices.py` gives a stale close — and never folded into the "not
ranked" list, because *we chose not to use them* is a different fact from
*they were not there*. On 2026-08-21, **five names**: BWY.L (751 d),
COLO-B.CO (690 d), CSG.AS (598 d) from the record flag, plus **SHL.DE (690 d)
and ERIE (598 d)** from the rows actually read. ERIE is in the section the
review's own measurement did not cover: its 2025-12-31 EBIT row is empty, so
its yield was formed from a 2024-12-31 EBIT and it sat in the
earnings-yield-only list. `rank_candidates` takes the run date as a REQUIRED
argument for this reason — a default would let a caller drop the one argument
the gate needs and get a full ranking back with no sign a check was skipped.

Filter 2 still passes a stale name through, and its report used to say *"only
the revenue-trend limb reads the annual statement."* **Phase 5 made that
untrue** — the whole ranking key is read from the same statement — and the
paragraph now says so, and says that the name is excluded one step later
instead.

**A name with no yield is NOT RANKED, and the report no longer calls that
"not rankable at all".** Without an earnings yield a name is not on the
two-legged list, and the one-legged section is the *earnings-yield* one, so
neither will take it — including names whose quality leg computed perfectly
well and whose enterprise value the bound above refused. The two causes are
counted apart in the tally rather than summed.

**One-legged names get their own section.** Financial Services and Real Estate
(E3's reasoning, narrowed by E6 to the economic ground alone — gross profit
over total assets is *computable* for a bank and not *comparable*), names whose
total assets are not positive (NOT MEANINGFUL, never clamped or sign-flipped),
and names missing a quality input are ranked on earnings yield alone, listed
separately, never interleaved and never given a synthesised quality placing.
The three causes are counted apart.

**Enterprise value is converted before the yield is formed.** See below.

**The yield double-counts capitalised leases — E10, measured and NOT
repaired.** `totalDebt` from the quote summary includes lease liabilities, while
`EBIT` is struck after the lease has been charged, so the same lease sits in both
halves of the ratio. Measured over the 291 ranked names whose balance sheet
separates the two lines — the other 27 cannot be measured and are excluded, see
E10 — lease is a median **0.9%** of enterprise value, above 10% for **12 of
291**, and up to **35.2%**: JD.L, at **place 5** and in PIPELINE. It is a
two-sector effect — Consumer Defensive 17% of names above 10%, Consumer Cyclical
13%, Technology, Healthcare, Basic Materials and Utilities **zero**. The
direction is one-way: it makes a lease-heavy company look **dearer**, never
cheaper, so it can bury a name but never promote one. Removing the lease from EV
moves 232 of 318 places, leaves the top-5 intact — **and leaves the top 25's
Consumer Cyclical count unchanged at 9**, which refutes the hypothesis it was
measured to test. Not repaired: the
clean fix needs the lease expense in the numerator, and `INCOME_LINES` does not
fetch it. See E10.

**Enterprise value is BOUNDED against figures the store already holds (L2).**
`enterpriseValue` was read straight out of the quote summary and nothing
checked it. Enterprise value is market capitalisation plus net debt, so
`marketCap − enterpriseValue` is the net cash it implies, and **no company
holds more net cash than it holds assets**. That is not a threshold, a
tolerance or a view about how much cash is plausible — it is the one
comparison the arithmetic forbids, and it is generous by construction: net
cash equal to the entire balance sheet still passes. Market cap is in the
quote currency and total assets in the reporting one, so **the same rate the
yield uses is applied before they are compared**; without that the check is
wrong by the exchange rate for one candidate in seven.

> **LISP.SW**, rank 14 of the 2026-08-21 run and the **highest earnings yield
> in the whole ranked list**: market cap CHF 21,179,160,576 against an
> `enterpriseValue` of CHF 3,539,840,512 — CHF 17,639,320,064 of implied net
> cash against **total assets of CHF 9,098,700,000**, 1.9× the entire balance
> sheet in a company reporting 54.5% equity. `marketCap + totalDebt −
> totalCash` gives EV 22,614,660,640 and a yield of **4.3% rather than
> 27.6%**. Too low an enterprise value always promotes; too high a one buries
> a name and nobody looks.

Measured on the 2026-08-21 candidate set: **four of 394** — CVNA (3.8×),
LISP.SW (1.9×), PLUS.L (1.2×), SILEX.ST (1.2×). The review of 2026-08-23
counted three; **PLUS.L is the fourth and it is the only one of the four
quoted in a currency it does not report in**, so a comparison made without
converting reads its GBP 810m of implied net cash against USD 944m of total
assets and finds nothing wrong. Converted it is USD 1,106m against USD 944m.

A flagged name **keeps its quality leg and loses its yield**, and the refused
enterprise value is still written into `ranking.csv` in converted form — the
number is named, not dropped. It is a rejection **on MISSING data** — a
figure we refused to form — and **never on value**: nothing in the check
judges the business. Cost, measured against the same run: two-legged list
325 → 322, top-5 **5/5**, top-10 **10/10**, top-20 **19 of 20** — LISP.SW
leaves place 14 and NVR takes place 20.

### FX, and the minor-unit trap

The earnings yield is the first ratio in the screener that does not cancel its
own currency — EBIT is in `financialCurrency`, enterprise value in the quote
currency. They differ for 60 of the 402 candidates.

Rates are fetched **once per run, per pair** (~10 pairs), carry the date of the
close they came from, and are written into the run manifest *and* printed in
the report. A pair that fails withholds the yield; **parity is never assumed**,
because a missing rate silently treated as 1.0 is an error the size of the rate.

#### Auditable is not reproducible — and this file said the wrong one

This section used to read *"Every ranking is then exactly reproducible from its
own record."* **That was false, and the proof was already inside the record it
was talking about.** `fx.default_lookup` asks yfinance for `period="5d"` and
takes the **last** close, whatever `--asof` says, so re-running
`--rank --asof 2026-08-21` on any later day silently uses that day's rates.
The `2026-08-21` manifest carries **ten pairs dated 08-21 and two dated
08-22** — NOK→USD and SEK→USD — so one run already bore two currency dates,
and no line of output mentioned it.

| | what it means | how |
|---|---|---|
| **Auditable** | you can see afterwards which rate was used | always — the manifest and the report |
| **Reproducible** | you can re-run it and get the same answer | only with `--fx-from-manifest PATH` |

#### A clean manifest, and why the old one is not one

`--fx-from-manifest` replays a stored record faithfully, **including its
defects**. The 2026-08-21 manifest carries ten pairs at 08-21 and two at
08-22, and the cause is now measured rather than guessed at: fetched on
Sunday 2026-08-23, `SEKUSD=X` and `NOKUSD=X` return a **weekend row** —
`… 08-20 0.105924, 08-21 0.105542, 08-23 0.105789` — while `EURUSD=X` in the
same minute stops at 08-21. Those two currencies are quoted through the
weekend by whoever feeds Yahoo; the euro is not. `default_lookup` takes the
LAST close, so it took the weekend one.

`tools/fetch_fx_manifest.py` (BUILD tool, never called at runtime) fetches the
rates **of a named date**: it selects the row whose date IS the requested one,
and a pair with no row on that date **FAILS and is named** rather than being
filled from the session next door. Run for 2026-08-21 it returns **twelve of
twelve pairs, every one dated 2026-08-21**, into
`ranking-manifest-fx-asof-2026-08-21.json`, which `--fx-from-manifest` replays
unchanged.

*The rates are not identical to the ten that were already stamped 08-21 —
CHF→EUR 1.069942 against 1.068400, SEK→EUR 0.090270 against 0.089940. The
stored ones were a live snapshot taken while the session was open; these are
that session's finalised close. Both are 08-21; only one of them is the close.*

`--fx-from-manifest` reads the rates back out of a stored
`ranking-manifest.json` and fetches nothing. Each replayed rate **keeps its own
`as_of`**, not the replay date: stamping the replay date onto it would erase
exactly the evidence the flag exists to show. A pair the manifest does not
carry **fails and is named** — it is never quietly fetched, because a
reproduction that is partly a new run is neither. The manifest records which of
the two a run was, under `fx_source`, and lists every distinct rate date under
`fx_rate_dates`.

**And a replay into another date is called what it is (L6's sibling, L5).**
The manifest's own `asof` field was written from the first run and read by
nothing, so replaying 2026-08-21's rates into `--asof 2026-07-27` was accepted
in silence under the word REPRODUCIBLE — which was **true and misleading at
once**: the run does repeat exactly, and it also pairs one day's rates with
another day's prices, the same cross-dating the look-ahead banner warns about
for the accounts and does not cover for the exchange rate. The field is now
read, and the headline becomes:

```
  REPRODUCIBLE, AND CROSS-DATED -- rates replayed from …
  THE MANIFEST SAYS ITS RATES ARE OF 2026-08-21. THIS RUN IS PRICED AT
  2026-07-27. …Nothing is refused…
```

**Nothing is refused, deliberately.** Holding one rate set still across dates
is a legitimate way to isolate a variable, and E6's own side-by-side
measurement was made exactly that way. A manifest carrying no `asof` is
reported as *uncheckable* rather than assumed to agree.

#### enterpriseValue is a price, and it sits among the fundamentals

The look-ahead banner said the fundamentals carry no as-of date. It did not say
that **one of them carries the wrong one.** `enterpriseValue` is market
capitalisation plus net debt — a price-dependent quantity — but it arrives in
the quote summary and is stored with the fundamentals with the *fetch date's*
quote already baked in. So every earnings yield in a replay pairs a **fetch
date's enterprise value** with a **replay date's drawdown**: two prices from
different days in one candidate row. For the 2026-08-21 run the two coincide
and it changes nothing; for `--rank --asof 2026-07-27` it does not. The banner
now says so, and names the exchange rate as the third date.

Market cap and enterprise value come back in the **major** unit of the quote
currency, so a London name quoted in GBp carries an EV in GBP. Reading it as
pence would divide the EV by a hundred and multiply the yield by a hundred,
floating every British name to the top — 39 of the 402 are quoted in GBp. GBp
and GBP resolve to one currency and convert at identity. This has its own tests.

### The acceptance test for phase 5

`tests/test_ranking_acceptance.py`

Filter 1 has had one since phase 2. **Phase 5 — the step that turns 402
candidates into the three to five names entered in the watchlist — had none
until 2026-08-22.** A refactoring that quietly reordered `EBIT_ALIASES`, or
picked `Total Current Liabilities` where `Current Liabilities` was present,
passed all 954 tests, and what changed was exactly which five names get the
hours.

**Frozen: the inputs.** `tests/fixtures/ranking-acceptance/` holds the
statement lines and quote-summary fields of all **394 post-collapse candidates**
of the 2026-08-21 run, the three ticker statuses, and the **twelve exchange
rates that run recorded** — so the price leg is replayed rather than re-fetched
and the answer does not drift with the market. `marketCap` is frozen for the
same reason `EBITDA` is: it is not an input to either component, it is what
bounds one of them, and without it the fixture cannot exercise the
enterprise-value check.

*The fixture's rates are the ORIGINAL twelve, ten dated 08-21 and two 08-22 —
that split is the evidence K7 was found on and a test asserts it. The re-run
of 2026-08-23 replayed a clean single-date manifest, so the live run's top
twenty and this test's differ at places 16–19. Both are right; the difference
is the exchange rate and nothing else, and neither is a regression in the
other. `tools/freeze_ranking_acceptance.py` says which manifest to re-freeze
from.* The fixture reproduces the live
store's full 325-name ordering name for name.

**Not frozen: the expected output.** The top twenty and their placings are
written out longhand in the test, and `tools/freeze_ranking_acceptance.py`
deliberately does not generate them. *A test whose expectation is regenerated
from the code it tests proves only that the code agrees with itself.*

**Why twenty and not five.** Measured: reordering `EBIT_ALIASES` to put
`Operating Income` ahead of the strict label moves **298 of the 325 places** and
rewrites the top twenty — **and leaves the top five untouched.** 382 of the 394
candidates carry both labels and **357 carry different numbers under the two**,
so it is a live risk, not a hypothetical one. A net drawn at five would have let
the review's own example straight through.

Four substitutions are executed rather than asserted, each shown to change the
answer: the alias reorder, `ebitda` for EBIT, `Current Assets` for
`Total Assets`, and `Total Revenue` for `Gross Profit`. A fifth check runs the
whole set with an empty FX table and asserts names *lose* their yield — parity
is never assumed where it would rewrite one candidate in seven.

### One company, two listings

Collapsed before ranking. Identity is **measured, never guessed from the ticker
string**: two share classes of one issuer file one set of accounts, so their
EBIT, revenue, net PP&E and total assets agree exactly, along with reporting
currency and sector. That separates EQT (US gas) from EQT.ST (Swedish private
equity), which a stem match would not. A fingerprint missing any line is no
fingerprint — an absent line must never make two companies look alike.

The survivor is the **most traded listing**, by median daily turnover over 90
days from the stored price series. Reported in the phase 1 dedup shape. On
2026-08-21 it folded in 8: six Swedish A/B pairs plus `AZN.ST`→`AZN.L` and
`NOKIA-SEK.ST`→`NOKIA.HE`.

**The comparison is made in the group's own currency when it has one (L6).**
An exchange rate is asked for only where a group spans two currencies — **two
of the eight** on 2026-08-21, `AZN.L` (GBp) against `AZN.ST` (SEK) and
`NOKIA.HE` (EUR) against `NOKIA-SEK.ST` (SEK). The other six are two Stockholm
lines of one Swedish company, and turning two SEK figures into two EUR figures
cannot change which is larger.

That is not a tidiness point. Turnover used to be converted for every listing
before any group was formed, so **one missing Swedish rate made six computable
comparisons fail** — and the fallback that then took over is alphabetical by
ticker, which for a Nordic A/B pair means the **illiquid voting class**.
Measured by removing `SEK→EUR` and `SEK→USD` from the manifest: **seven of the
eight winners reversed** — ERIC-**A**, HUSQ-**A**, NCC-**A**, SAGA-**A**,
SWEC-**A**, TEL2-**A** and `NOKIA-SEK.ST` — and the ranked list went 319 → 313.
`AZN.L` survived only because it sorts before `AZN.ST`.

The fallback is kept, said to be a fallback, and now fires only where the
question genuinely cannot be answered: a group spanning two currencies with a
rate missing, or a listing with no turnover at all. **It is not reversed to
"last by ticker"** — that would be a better coin, not a measurement.

**The minor unit cuts the other way here.** Quote-summary figures arrive in the
major unit, so an enterprise value needs no division; the *price series*
arrives in the minor unit, so turnover from it does. Missing that would make a
pence-quoted London line look a hundred times more traded and hand it every
contest it entered. Both directions have tests.

---

## Phase 6 — what exists

```
python -m vss screen --rank --write-pipeline --asof 2026-08-21
python -m vss screen --rank --write-pipeline --dry-run   # writes nothing
```

Writes the top `--top` (default 5) of the **BOTH-legs list** into
`config/watchlist.yaml` as `PIPELINE`.

`vss/pipeline.py` is the only module in the screener permitted to touch that
file, and a test enforces it. Its rules:

- **PIPELINE only.** No `mbp`, no `fv_base`, no `tier`, no `stop_price`. §5 is
  run by hand; a screener that pre-filled any of it would hand the owner a
  number nobody computed.
- **An existing ticker is never touched** — not updated, not reordered. It is
  reported as already present and skipped.
- **Backup before, re-parse after.** If the file no longer loads, the backup is
  restored and the run fails loudly.
- **Entries are appended as text.** The watchlist is hand-maintained and full of
  comments; a YAML dumper would silently discard them.

The one-line note is assembled from figures the run measured — rank, sector,
market, drawdown, gross profitability, earnings yield — and contains **no
assessment**. A test
asserts the absence of judgement words.

**The earnings-yield-only section is not eligible.** For its sector-exempt
majority, enterprise value is not a meaningful construct either — a bank's cash
and debt are what it trades in, not how it is financed — so the one leg they
carry is itself compromised and they are in practice not ranked.

---

## Phases 4 and 7 — planned, not built

### Phase 3 — fundamentals for the survivors, filter 2 (BUILT)

FCF positive, net debt/EBITDA, revenue trend.

**Look-ahead limitation, to be printed in the output rather than hidden:**
yfinance serves historical *prices* but only the *latest* fundamentals. A
replay against an old date therefore cannot run filter 2 honestly — it would
be scoring a 2026-07-27 price against 2026-08 accounts. Phase 3's replay mode
must refuse to run filter 2 and say why, rather than producing a number that
looks like history.

Tier C's floors need an FX source before they can be applied; each threshold in
`floors.yaml` already carries its own currency so the requirement is explicit.

### Phase 4 — insider annotation

FI's insider register covers Swedish issuers, EQS covers German ones, and
neither covers the US or Canada. The flag is an **annotation, never a ranking
input**: ranked, it would push Nordic names up purely because the data exists
there. Markets with no source are written `NO DATA`, explicitly.

### Phase 5 — the ranking key (BUILT, see above)

Proposed as text in `FRAMEWORK-EDITS.md` and approved before a line of it was
coded, per standing rule 6. Decided 2026-08-22 as E5.

### Phase 6 — PIPELINE writing (BUILT, see above)

### Phase 7 — its own systemd timer

Separate unit. `vss.service` / `vss.timer` (22:30 daily, `vss run`) are not
touched. The screener needs no API key — yfinance requires none.


---

## Measurements from the full runs (asof 2026-08-21)

**Prices, phase 1**

| | |
|---|---:|
| tier A instruments after exclusions and dedup | 1,370 |
| fetch statuses | 1,370 OK, 0 THROTTLED, 0 NO_DATA, 0 STALE |
| price rows stored | 679,676 |
| snapshot size on disk | 77.3 MB |
| wall clock, 28 batches of 50 | ~4.5 min |

**Fundamentals, phase 3**

| | |
|---|---:|
| tickers fetched (filter-1 survivors) | 536 |
| requests | 1,072 (2 per ticker) |
| fetch statuses | 531 OK, 0 THROTTLED, 0 NO_DATA, 5 STALE |
| retries needed | 0 — the backoff path still has not fired live |
| field coverage | freeCashflow 96.5%, ebitda 96.8%, totalDebt 99.8% |
| store size | ~0.9 MB |
| wall clock | ~8 min |

**Yield through the whole chain**

| step | in | out | rejected on value | on missing |
|---|---:|---:|---:|---:|
| read | 1436 | 1436 | 0 | 0 |
| tier_select | 1436 | 1436 | 0 | 0 |
| instrument_type | 1436 | 1419 | 17 | 0 |
| yahoo_mapping | 1419 | 1419 | 0 | 0 |
| dedup | 1419 | 1370 | 49 | 0 |
| exclusion_list | 1370 | 1364 | 6 | 0 |
| price_coverage | 1364 | 1364 | 0 | 0 |
| dislocation | 1364 | 536 | 828 | 0 |
| filter2 | 536 | 402 | 134 | 0 |

Extrapolated, a tier B+C universe of ~13,000 names would store roughly 730 MB
per run and take some 45 minutes. That is a real number to decide storage
policy on — retention, pruning, or a narrower stored window — rather than an
estimate.

## Open findings — measured, NOT fixed

From `reports/screener-review-2026-08-22.md`. K1/K2, K4, K5, K6, K7 and K9 were
repaired on 2026-08-22 and are described in their sections above. **These three
were deliberately left alone.** They are recorded with their size so that
nobody has to re-derive it before deciding whether to act, and so that no
later reader mistakes silence for absence.

### K3 — the band selects "recently down", not "cheap" — OPEN

The 15–50% band measures distance to the highest close in a rolling 365 days.
**It does not ask when that high was set**, so a name that tripled and pulled
back reads as dislocated. FRAMEWORK §3 Gate 1 asks for a fall *"with the bulk
of the decline occurring in the trailing 3–6 months"*; the screener implements
the level limb only.

Measured on the 2026-08-21 run, over the **325 names ranked on both legs**, using
the B1 metric the tool already computes and prints:

| B1 over the ranked list | |
|---|---:|
| median | **0.27** |
| bulk of the fall **older than six months** (B1 < 0.5) | 201 of 323 — **62%** |
| price **HIGHER** than 180 days ago (B1 ≤ 0) | 118 of 323 — **37%** |

> **MRNA is still in the ranked list.** It closed 62.96 on 2026-08-18 and
> 174.38 on 08-19, and 145.13 on 08-21 — so its 52-week high is a peak set two
> days earlier, its measured drawdown is 16.8%, and its **B1 is −3.26**. The
> price-series check (K4) passes it correctly: the +177% session traded on
> 23.8× its median volume, so it is a real repricing and not broken data. The
> fault is the band's, not the data's.

Two further parts of the same finding, unmeasured here:

- **Dividends widen the band toward high payers.** `AUTO_ADJUST = False` gives
  split-adjusted but **not** dividend-adjusted closes — correct for the
  watchlist path, where the price must match what the broker shows when a stop
  is entered by hand, and wrong for a drawdown. The wedge is the dividends paid
  *between the peak day and today*, so it scales from near zero when the peak
  is recent up to roughly the trailing yield when the peak is a year back. Not
  quantifiable from the stored data: `actions=False`, so no dividend is fetched.
- **B1 is computed, printed and not used.** That is the owner's decision of
  2026-08-22 and is not reopened here. The consequence — that the candidate list
  does not satisfy Gate 1's second limb for six names in ten — is what was not
  written down, and now is.

### K8 — four things a value investor would say — OPEN

1. **The band picks fallers; the key then picks high yields among them.** That
   is the classic value trap, and nothing in the tool looks forward. No estimate
   revision, no forward number: EBIT is a year-end figure divided into today's
   enterprise value. FRAMEWORK §4.2 does look, but only after five names have
   been chosen. *(E6 narrowed this: the two legs' rank correlation fell from
   +0.25 to +0.14, so the key is less inclined to stack both bets on the same
   quantity. It did not remove it.)*
2. **The quality leg measures the balance sheet, not the business.** Largely
   answered by E6 — a pole at the top of the leg is gone and the denominator is
   present for every company — but gross profitability is still an accounting
   ratio and not a judgement about the franchise.
3. **No size or liquidity floor in tier A.** `floors.yaml` carries `A: {}` with
   the comment that index membership *is* the floor. Median daily turnover **is**
   computed — but only to decide which share class survives the collapse, never
   as a filter. Greenblatt has explicit floors (USD 50m market cap, USD 5
   price). For a ~77k SEK satellite this matters little in practice; it is
   absent in principle.
4. **No sector-concentration check before phase 6, AND IT NOW BINDS.** FRAMEWORK
   §7 allows at most two sectors in the sleeve. The 2026-08-21 top five is
   **four Consumer Cyclical and one Healthcare** — two distinct sectors, so the
   letter of §7 holds, while four of the five names sit in one sector. Phase 6
   writes the top five without looking at sector at all; §7 is presently a hope
   that the ordering behaves. **This is the one of the four that changed with
   E6** and it is the one to look at first.

### K10 — two label slips — OPEN, and one of them is not where the review put it

- **The S&P 500 source.** FRAMEWORK-EDITS **E1** (not `SCREENER.md`, which the
  review named) says *"`sp500` (503/503 from the index constituent list)"*.
  `sp500-2026-08-22.meta.json` records
  `source_url: en.wikipedia.org/wiki/List_of_S%26P_500_companies`. The metafile
  is honest; E1's calibration note is not — 503 of 503 is right, but Wikipedia
  is not a constituent list from the index provider, and E1's whole purpose is
  to forbid exactly that kind of drift. `SCREENER.md`'s own "constituent list"
  phrase, at open question 1, is about the **iShares EXSA holdings file for
  STOXX 600**, and that one is accurate.
- **`SCREENER.md` contradicts itself about look-ahead.** The phase 3 section
  says the limitation is *"printed not hidden"*, which is what the code does.
  The "Phases 4 and 7 — planned, not built" section still carries the older
  requirement that *"Phase 3's replay mode **must refuse** to run filter 2 and
  say why."* Both describe the same step. One occurrence of each phrase remains
  in this file.

## Open questions for the owner

1. **STOXX 600 source.** Currently the iShares EXSA holdings CSV: it is the
   physically replicating full-size ETF, so its 600 Equity rows are the
   constituent list, and it carries Asset Class, exchange and currency. The
   alternative considered and rejected was Wikipedia, which had 467 of 600.
   Keep iShares, or prefer STOXX's own selection list?
2. **OMXS Large+Mid source.** Currently an APPROXIMATION: the Yahoo equity
   screener for exchange STO cut at Nasdaq's own Mid Cap floor of EUR 150m,
   giving 316 names against roughly 270 in the official segment. Nasdaq's
   segment file is behind a login at indexes.nasdaqomx.com. The list is marked
   `"approximation": true` in its metadata and the universe report prints it.
3. **ISIN.** Zero coverage today. No free source checked carries it: Yahoo's
   ISIN lookup returns `-`, the European iShares files omit the column, and
   Wikidata's 7,251 (isin, exchange, ticker) triples attach ADR and ordinary
   ISINs to the same listing, which would produce false merges. Options:
   Avanza's own instrument API — which would also give tradability and
   instrument type, and is the natural source for an "everything Avanza can
   trade" universe, but is a private API; Wikidata as a low-confidence fill
   requiring manual review; or a registered/paid source.

   **Concrete cost of zero coverage:** every watchlist name is in tier A
   except `UNA.AS`. The index carries Unilever's London line, `ULVR.L`, while
   the position sits in Amsterdam. With no ISIN, nothing links the two, and the
   screener would one day surface `ULVR.L` as a fresh candidate for a company
   already held. FRAMEWORK section 8 treats that listing choice as a real
   decision; the screener currently cannot see it.
4. **The ninth column.** `instrumenttyp` was added to the specified eight-column
   schema. Exclusions must read an instrument type from the source list and the
   eight columns had nowhere to hold one.
5. **Unknown instrument type.** Default policy is `keep`, counted separately —
   excluding an unknown type would be guessing it is a fund. Switchable to
   `exclude` in `config/universe/instrument_types.yaml`, where it lands in the
   "rejected on MISSING data" column, never mixed with the value-based ones.
6. **ADR and preference-share exclusion is NO DATA on Yahoo-typed lists.**
   Yahoo reports both as `quoteType: EQUITY`, so those two exclusion categories
   have nothing to fire on for the S&P 500 and OMXS lists. `HEIM-PREF.ST` is in
   the universe as an equity for exactly this reason. The report says so; it is
   not patched over by matching "PREF" in the ticker string.
