# SPEC.md — machine-facing rules for `vss`

**Scope:** this file governs what the *code* does. `FRAMEWORK.md` governs what
the *analyst* does. Where they disagree, FRAMEWORK.md wins for judgment and this
file wins for arithmetic.

**This file is not an instruction to perform analysis.** Nothing here asks you
to produce a regime block, a pipeline table, or an action list. If you are a
coding agent reading this repo, your job is to implement the rules below, not
to execute them against live data.

**Status: describes v1 as built.** Every rule below is implemented and covered
by the pytest suite. This file was revised after the build to match the code —
where an earlier draft of this spec disagreed with the delivered behaviour, the
code is authoritative and this file was corrected, not the code.

---

## 1. Field provenance — who supplies what

The single most important table in this file. A field marked MANUAL is never
computed, estimated, inferred, defaulted or back-filled by code. If it is
absent, the dependent check returns `DATA MISSING`.

| Field | Provenance | Notes |
|---|---|---|
| `ticker`, `name`, `currency` | MANUAL | required |
| `hurdle` | MANUAL | E29's frozen hurdle rate, present only where a PURCHASE verdict was struck: `rate`, `core_expected_return`, `premium`, `rate_as_of` — **all four or none**. The rate must reconcile to its anchor (`rate == core_expected_return + premium`) and the premium must sit in E29's 2–3 point band. Absent everywhere else: an exit under C4 is re-struck at today's rate, not read from here. |
| `revenue_yoy_organic` | MANUAL | the issuer's own ORGANIC / constant-currency growth rate, per quarter. **E30 makes this the basis §4.2.1 reads**: organic where disclosed for the whole window, reported otherwise, and the result names which. A window mixing the two is CANNOT EVALUATE. **Not like-for-like** — PNDORA disclosed organic +2% and LFL 0% in the same quarter, and E30 names organic. |
| `status` | MANUAL | required; `HELD` \| `WATCH-PRICED` \| `WATCH-GATED` \| `PIPELINE` \| `DROPPED`. The bare `WATCH` was split by FRAMEWORK-EDITS E27 (2026-08-25) and is REJECTED with a message naming both successors: `WATCH-PRICED` passed §5 and is only too expensive (§5.3 applies — a limit alert computed from MBP); `WATCH-GATED` failed a §3 gate on something other than price (re-entry on a named information event, never a price level). |
| `fv_base` | MANUAL | output of FRAMEWORK §5.1–5.2 |
| `tier` | MANUAL | `1` \| `2` \| `3` per FRAMEWORK §5.3; see §4 |
| `dd_at_entry`, `peak_date` | MANUAL | FRAMEWORK-EDITS **E12**: Gate 1 is evaluated once, when a name enters PIPELINE, and is then frozen. `dd_at_entry` is that drawdown as a **fraction** in `[0, 1]`; `peak_date` is the date of the 52-week closing high it was struck against. **A pair** — either alone fails the run, because a frozen reading whose peak is not named cannot be told from one whose peak has since aged out of the rolling window (E11). Never recomputed: a name that leaves the band because the peak aged out has produced no new information and stays. |
| `mbp` | COMPUTED from `fv_base` × tier multiplier | Never entered by hand — a hand-entered `mbp:` key is a provenance conflict and **fails the run** |
| `stop_price` | MANUAL | per FRAMEWORK §6.4; absent ⇒ BLOCKED if HELD, otherwise flagged, see §3 |
| `catalyst_date`, `catalyst_event` | MANUAL | |
| `catalyst_resolved` | MANUAL | the date the outcome was ingested; the catalyst gate reads this and nothing else |
| `notes` | MANUAL | free text, prose only — **never parsed**, see §3 |
| last close, close date | COMPUTED | yfinance |
| 52w high, drawdown | COMPUTED | see §2 |
| RSI(14), SMA50, SMA200 | COMPUTED | RSI is reported only; no verdict uses it |
| 20d avg volume, volume ratio | COMPUTED | |
| distance to MBP, distance to stop | COMPUTED | |

`ALLOWED_KEYS` in `vss/config.py` is the authoritative schema. **Any key not in
that set fails the run**, so a typo such as `stop:` for `stop_price:` cannot
silently vanish.

`dd_at_entry` is the one place a drawdown is stored rather than computed, and
the distinction is deliberate: the COMPUTED `drawdown` in §2 reads today's
level and is what FRAMEWORK-EDITS **B1** continues to use for holdings. E12
freezes the PIPELINE reading and does not touch B1 — a holding is an open
position, a pipeline name is a piece of review work.

Not implemented in v1, and therefore not accepted as watchlist keys:
`fv_bear`, `fv_bull`, `entry_price`, `position_pct`, `conviction`, `cyclical`,
a regime flag, and everything in FRAMEWORK §4.

---

## 2. Computation semantics

Ambiguity here is what makes two implementations disagree. These are binding.

**52-week high.** Highest *daily close* in the trailing 365 calendar days,
inclusive of today. Not the intraday high. Rationale: intraday highs make
drawdown jumpy and depend on the data vendor's tick handling.

**Drawdown.** `(high_52w - last_close) / high_52w`, expressed as a positive
fraction. A stock 22% off its high has `drawdown = 0.22`.

**Dislocation band.** `0.15 <= drawdown <= 0.50`, both bounds **inclusive**.
Exactly 15.0% passes. Exactly 50.0% passes. Above 0.50 is out of scope per
FRAMEWORK §3 Gate 1.

**RSI(14).** Wilder's smoothing (not simple moving average of gains/losses).
Requires at least 15 closes; fewer than that returns `DATA MISSING`, never a
partial estimate. RSI is **reported only** — no verdict in §3 consumes it.

**SMA50 / SMA200.** Simple mean of the trailing 50 / 200 daily closes.
Insufficient history returns `DATA MISSING`, not a shorter-window substitute.

**Volume ratio.** `today_volume / mean(trailing 20 sessions' volume)`,
excluding today from the denominator.

**Price basis.** yfinance is called with `auto_adjust=False`, so `Close` is
split-adjusted but not dividend-adjusted. This keeps the last close equal to
the quote shown in the broker, which is the basis on which `stop_price` and
`fv_base` were set by hand.

**`vss earnings` accepts every status.** FRAMEWORK §4.2 is evaluated
identically whatever the ticker's status; only the alert's framing differs.
`HELD` reads as thesis invalidation (`4.2 POSSIBLE TRIP`), the `WATCH` pair and
`PIPELINE` as the §4 Phase 2 validation gate (`4.2 FAILS VALIDATION`), since a
candidate has no thesis to invalidate. The rule results, the figures and the
proposed `quarters:` entry are byte-identical across statuses — a test asserts
it. Restricting the command to `HELD` made it impossible to work a candidate up
to a buy decision, which is the step §4.2 exists to inform.

**Quarter figure units.** Binding, and the one contract every layer obeys.
A ratio is stored as a **FRACTION, never a percentage**: an operating margin of
6.6 per cent is `0.066`, and revenue growth of 2 per cent is `0.02`. The
affected fields are `op_margin`, `revenue_yoy` and `covenant_headroom`.

The rules layer depends on this arithmetically — 4.2.2 computes compression as
`(prior - latest) * 10_000` to get basis points, and 4.2.5 formats headroom as
`{:.1%}` — so a percentage-valued entry does not merely read oddly, it makes
every threshold in §4.2 wrong by a factor of 100.

Everything else is in the unit the report itself uses: `revenue`, `op_income`,
`receivables`, `inventory` and `class_c_impact` in the report's currency and
scale (Lindab reports SEK millions, so `3306` is SEK 3,306m); `eps` per share;
`net_debt_ebitda` as a multiple, so 2.7x is `2.7`, not a fraction.

Both sides obey it. `vss earnings` instructs the model to convert a quoted
percentage to a fraction, and drops any ratio that arrives outside its band.
`vss/config.py` rejects the watchlist outright when a ratio falls outside
`rules.FRACTION_BANDS`:

| Field | Band | Why that band |
|---|---|---|
| `op_margin` | `[-10.0, 1.0]` | Operating income above revenue is not a thing, so the ceiling is 100%. The floor is generous because a pre-revenue name can lose many times its revenue. |
| `revenue_yoy` | `[-1.0, 1.0]` | Revenue cannot fall by more than 100%. Growth above 100% is possible but rare; the error message says to write it as a fraction, and a rare false positive beats a check that misses the case it exists for. |
| `covenant_headroom` | `[-1.0, 1.0]` | A fraction of the covenant limit. |

The band is a **hard load error**, not a flag. A margin of `6.6` is not a
margin to evaluate; it is a unit error, and evaluating it would produce a
verdict about a number nobody entered.

**A figure may be read from a later filing.** `vss earnings --period YYYY-Qn`
extracts one named period, taking it from a comparative column when the
document is about another quarter. The recorded source is then the document
that contains the figure, not the period's own release. SAP's Q2 2024
restructuring is stated in the Q2 2025 statement and in no earlier one, so that
is where it was read and that is what the record says. The comparative column
must be named in `period_column`, and falling back to the document's own period
is forbidden outright.

**`class_c_impact`** is a quantified one-off stated on its own line —
restructuring, impairment, a provision or its release, a settlement, a disposal
gain. Its sign is the effect on REPORTED operating profit, copied from the
statement: a charge is negative, a release positive. It is never inferred from
the difference between a reported and an adjusted figure; that difference is a
computation and bundles other adjustments in with the one-off.

**Reporting frequency and the overlap guard.** A watchlist entry may declare
`reporting_frequency: quarterly | half_yearly` (absent = `quarterly`). The
frequency fixes two things. *Labels:* a quarterly ticker stores `YYYY-Qn`
periods; a half_yearly ticker stores `YYYY-H1`, `YYYY-H2` or `YYYY-FY`
(`rules.PERIOD_KINDS_BY_FREQUENCY`); a label of the other kind fails the load,
because the §4.2 windows must be counted in one unit. *Windows:* FRAMEWORK §4.2
states its windows in quarters; for a half_yearly ticker every
quarter-denominated window is converted by TIME and rounded up
(`rules.periods_for`): trailing 8 quarters → 4 half-years, 4 → 2, 3 → 2, 2 → 1,
and the YoY look-back is `PERIODS_PER_YEAR` = 2 periods. The conversion is
literal, so "2+ consecutive quarters" becomes one half-year and the run-length
rules (4.2.1, 4.2.7) fire on a single half-year observation; `rules.py` states
this beside the constants so it can be overruled deliberately. 4.2.5 and 4.2.6
are unaffected.

The **overlap guard** applies to every ticker and is period-label arithmetic
(`rules.periods_overlap`): no two loaded periods of one ticker may cover the
same month — `YYYY-FY` contains both halves and all four quarters, `YYYY-H1`
contains Q1 and Q2, `YYYY-H2` contains Q3 and Q4. Where two overlap, the finest
resolution stays and the coarser goes, and the history never holds both; where
only the coarse figures exist, the coarse period stays. In `config.py` an
overlap is a fatal `ConfigError` naming the label to remove. In `vss earnings`
the extracted period is put to `rules.admit_period`: a malformed label or the
wrong kind for the frequency is **rejected** (not proposed, not evaluated; the
figures are still shown as the record); the same label as a loaded row is
**admitted and displaces** that row for the evaluation (a re-read never sits
beside the row it re-reads — that counted one guidance cut twice); a label
overlapping a loaded *finer* period is rejected; a label finer than loaded
*coarser* periods is admitted, displaces them for the evaluation, and the alert
says they must be removed before the entry is pasted. `--period` accepts all
four label kinds.

Year-over-year comparators are matched **by label**, not by position:
`rules._year_ago` looks for the entry labelled one year earlier with the same
kind (2026-H1 → 2025-H1, 2026-Q2 → 2025-Q2) and returns None — hence
CANNOT EVALUATE — when it is absent. Positional look-back would pair unlike
periods across a gap, or pair a `YYYY-FY` with a `YYYY-H1` in a half_yearly
history that holds both kinds (which the guard permits, since 2024-FY and
2025-H1 do not overlap). The trailing windows still count *periods*, so a
history mixing FY and H rows counts twelve-month and six-month rows alike; a
clean half_yearly history is all H1/H2 rows, with FY rows only where no half is
stated.

**Quarter source.** A `quarters:` entry may declare where its figures came
from: `source: xbrl` or `source: release`. Blank means the same as `release`,
so every existing entry keeps its behaviour.

`source: xbrl` exempts the entry from the op_margin reconciliation, and from
that alone. The reconciliation exists to establish WHICH LINE `op_income` came
from — a question `us-gaap:OperatingIncomeLoss` answers outright, and more
exactly than a margin ever did. XBRL has no margin tag, so requiring one would
force a computed figure into the record purely to satisfy a checker, which is
the opposite of what the check is for. An `xbrl` entry that *does* state a
margin is still reconciled: the exemption covers an absent margin, never a
contradictory one, and the band check and the unit-mix guard apply unchanged.

`vss xbrl` writes `source: xbrl` into every entry it proposes and never writes
`op_margin`.

**One ticker, one unit.** A `quarters:` history must be in a single unit
throughout. `vss xbrl` reports whole units where a press release reports
millions, and a row from each is internally consistent — so the band check, the
reconciliation check and every §4.2 rule pass while the history is out by a
factor of a million. Only a comparison across rows can see it. When
`revenue`, `receivables` or `inventory` differs by `rules.SCALE_JUMP_FACTOR`
(1,000×) or more between two quarters of one ticker, the load fails as a UNIT
MIX. `op_income` and `class_c_impact` are excluded: they cross zero and can
genuinely swing orders of magnitude, so a jump there evidences nothing. The
remedy is to re-read the odd quarters from one source, never to rescale a
figure by hand.

**Margin reconciliation.** When a quarter states `revenue`, `op_income` and
`op_margin`, then `op_income / revenue` must equal `op_margin` to within
**0.1pp** (`rules.MARGIN_RECONCILIATION_TOLERANCE`, 0.001 as a fraction) or the
watchlist fails to load. The check is skipped when `revenue` or `op_income` is
absent, and when `revenue` is zero.

It is **not** skipped when only `op_margin` is absent. `op_margin` is what
cross-checks `op_income`, so a quarter carrying revenue and operating income
with no margin is `UNRECONCILED` — nothing establishes which line the operating
income came from, which is exactly how NIKE's "Income before income taxes" of
1,416 was recorded where EBIT was 1,392. A blank that disables a check is not
the same kind of blank as one reporting DATA MISSING, and it is not waved
through. The fix is to record the margin the source states, or to leave
`op_income` blank as well — never to compute a margin to satisfy the check. Its purpose is not arithmetic hygiene: it catches a
quarter whose three figures come from *different measures* — an adjusted margin
beside a reported operating income — which is otherwise invisible once the
numbers are in the file.

**The Class C exemption is magnitude-aware.** FRAMEWORK 4.2 exempts margin
compression "explained by a quantified Class C event", and explaining is a
matter of size: a 2 MSEK one-off does not explain a 400bps collapse. Rule 4.2.2
therefore removes each quarter's one-off from its margin and applies the 150bps
threshold to what is left:

```
margin_ex_one_off = op_margin - class_c_impact / revenue
compression_ex    = (prior.margin_ex_one_off - latest.margin_ex_one_off) * 10_000
```

`class_c_impact` is the one-off's effect on *reported* operating profit, so
removing it is a subtraction. Lindab's 2025-Q4 reports a 3.1% margin with a
−106 MSEK one-off on 3,134 MSEK of revenue, which is 6.5% ex one-off — the
adjusted margin the report itself states.

**Both** quarters are adjusted, not only the latest. A one-off that flattered
the year-ago base manufactures compression that never happened; a one-off that
flatters the latest quarter hides compression that did. The threshold reads the
ex-one-off figure in both directions, so a gain in the latest quarter can now
cause a trip that the reported margins conceal. Both figures appear in the
output — a reader must be able to see what the one-off did, not merely be told
it was handled.

A quarter carrying a `class_c_impact` but no `revenue` cannot express that
one-off as margin points at all. That is `CANNOT EVALUATE`, not an exemption
granted on the strength of a number whose effect nobody can measure.

**XBRL facts are a primary source with filing-level provenance.** For a US
filer, `vss xbrl` reads `data.sec.gov/api/xbrl/companyfacts/CIK{10-digit}.json`
and maps tags to the `quarters:` schema. Each figure records its tag, its
context period and the accession number of the filing — provenance that does
not depend on a quoted sentence, because no sentence was read.

The DATA MISSING and reconciliation rules are unchanged. A field whose tags the
filer does not use is blank: `op_income` maps to `OperatingIncomeLoss` and
nothing else, so an issuer that reports no operating income line yields none.
`op_margin` has no tag and is never computed from `op_income ÷ revenue`.

Periods come from the filer's own fiscal year end, never from SEC's `frame`
field, which is calendar-based and would misdate every quarter of a non-December
filer. Tag preference is per period, so a superseded tag cannot shadow a live
one. Values are recorded in the units XBRL states — whole units, not the
millions a press release uses — and are never rescaled; the report warns
against mixing the two sources in one history.

`VSS_SEC_CONTACT` must be set: SEC requires automated callers to declare a real
contact address, and the API is not called without one.

**Flattening keeps a table row on one line**, cells separated by spaces, and
both entry points flatten identically. `--url` flattened HTML while
`--text-file` handed the file over raw, which meant a saved EDGAR exhibit was
read as markup rather than as a report. A row whose cells are concatenated
(`1,3921,900`) or split across lines cannot evidence its own figures, so the
provenance rule could not be satisfied from a real statement table at all.

**Operating income when the issuer reports none.** Some issuers never state
an "Operating income" line. NIKE's income statement runs from gross profit and
overhead straight to "Income before income taxes", and its operating profit
appears only in a non-GAAP table headed EARNINGS BEFORE INTEREST AND TAXES at
the foot of the release. Where there is no Operating income line but such a
table exists, the total EBIT row is `op_income` and "EBIT margin" is
`op_margin`, both recorded with `measure: adjusted` — the release's own
footnote calls them non-GAAP.

Two lines are never substitutes and the extraction says so explicitly.
"Income before income taxes" is struck after interest — 650 against an EBIT of
635 in NIKE's Q3 FY26 — and "Gross margin" is a different line entirely, 40.2%
where EBIT margin is 5.6%. Both were taken by the extractor before this rule
existed.

**Adjusted versus reported.** When a report states both an adjusted (also
"underlying", "like-for-like", "before items") figure and an unadjusted one for
the same line, the **unadjusted** figure is the one extracted, and which was
taken is recorded per figure. Lindab's Q4 2025 states an adjusted operating
margin of 6.5% and a reported one of 3.1%; the reported figure is the one §4.2
evaluates. Where a report publishes only an adjusted figure, that figure is
taken and the run is marked uncertain, because it is not the measure the rule
was written against.

**Freshness.** A close is STALE when it is more than **3 calendar days** old
relative to the run date. Calendar days, deliberately — no holiday calendar
and no exchange calendar in v1. The consequence is accepted and documented: a
Tuesday run after a Monday market holiday blocks on Friday's close. The gate
errs toward flagging.

---

## 3. Verdict semantics

**Three outcomes, never two.** Every check returns exactly one of
`PASS` / `FAIL` / `DATA MISSING`. There is no fourth state and no silent skip.

**`DATA MISSING` is not `FAIL`.** A missing input means the check could not be
evaluated. Never treat absence as failure, and never substitute a default,
sector average, or last-known value to avoid the state.

**Blocking beats everything.** A ticker is `BLOCKED` if any of these hold:

| Blocker | Condition |
|---|---|
| `NO_DATA` | the fetch failed and no cached data exists |
| `STALE_DATA` | the newest close is STALE per §2 |
| `CATALYST_UNRESOLVED` | `catalyst_date` is strictly in the past and `catalyst_resolved` is not set |
| `NO_STOP` | `status == HELD` **and** `stop_price` is absent — "no stop defined (FRAMEWORK §0.4 / §6.4)" |

A `BLOCKED` ticker emits its blocker reasons and **no verdict of any kind** —
not `NO ACTION`, not `HOLD`, not `DATA MISSING`. **All** applicable blockers
are listed, not merely the first. Blockers are listed before actions in the
report. A catalyst dated *today* has not yet passed. A ticker with no
`catalyst_date` is never blocked by that rule.

**The catalyst gate reads `catalyst_resolved` only; it never parses `notes`.**
The earlier mechanism matched any notes line beginning `outcome:`, which meant
arbitrary prose could satisfy the gate — including a placeholder reading
`outcome: ... NOT YET INGESTED`. Resolution is now a structured date: the day
the outcome was actually ingested. `catalyst_resolved` earlier than
`catalyst_date` is a data error and **fails the run**, since an outcome cannot
be ingested before the event occurs. Notes may still carry prose `outcome:`
lines as a human record; they carry no machine meaning.

**Verdicts are COLLECTED, not first-match-wins.** A ticker carries every
verdict it triggers, so a stop breach can never be masked by another rule
firing first.

| Verdict | Condition |
|---|---|
| `STOP BREACHED` | `status == HELD` and `last_close <= stop_price` |
| `AT/BELOW MBP` | `last_close <= mbp` |
| `APPROACHING MBP` | `mbp < last_close <= mbp * 1.05` |
| `OUTSIDE DISLOCATION BAND` | drawdown outside `[0.15, 0.50]` |
| `NO STOP DEFINED` | `status != HELD` and `stop_price` is absent — a flag, not a verdict on price |
| `NO ACTION` | none of the above fired |

All comparison boundaries are inclusive. `AT/BELOW MBP` and `APPROACHING MBP`
are mutually exclusive: exactly at MBP yields `AT/BELOW MBP` alone.

**Missing manual fields.** If a manual field a check needs is absent, that
check yields `DATA MISSING` and every other check still evaluates. A missing
`fv_base` or `tier` makes `mbp` `DATA MISSING`, which makes both MBP verdicts
`DATA MISSING`, while the stop check and the dislocation check evaluate
normally. A `DATA MISSING` verdict is not `NO ACTION`, so the ticker appears in
the ACTIONS section rather than disappearing into the quiet majority.

**`DROPPED` is a record, not a stage.** A name rejected at some phase, kept so
it is not screened again from scratch and so the reason survives in `notes`. It
collects exactly one verdict — `DROPPED` — and no others: there is no position
to exit and no entry to prepare for, so the pre-entry stop flag and the MBP
checks would both answer questions nobody is asking. It stays out of the
ACTIONS table and keeps its row in ALL TICKERS. Blockers still apply, so the
record stays honest about its own data freshness. `vss earnings` reads it as a
candidate, since a rejected name has no thesis to invalidate.

**An absent `stop_price` is status-dependent.** For a `HELD` name it is a
blocker: there is an open position and no defined exit, so no verdict is
issued. For `WATCH-PRICED`, `WATCH-GATED` and `PIPELINE` there is no position to exit, so the name is
*not* blocked — it receives its normal MBP and dislocation verdicts plus the
`NO STOP DEFINED` flag, which records that FRAMEWORK §0.4 rule 4 is unmet: a
name is a buy below price X, under conditions Y, **with stop Z**. A buy verdict
carrying that flag is not yet actionable. The flag is emitted exactly once and
never alongside a `DATA MISSING` for the same field.

---

## 4. Tier and MBP

`tier` is a MANUAL input in v1. Code does not derive it, and does not compute
`conviction` or `cyclical`. The FRAMEWORK §5.3 decision order below is recorded
for the analyst who sets the field by hand:

1. If the thesis is re-labeled (mean-reversion / turnaround-adjacent) → **Tier 3**
2. Else if conviction ≤ 6 **or** the name is cyclical → **Tier 2**
3. Else (conviction ≥ 7, non-cyclical) → **Tier 1**

Multipliers, applied by code: Tier 1 = 0.80, Tier 2 = 0.70, Tier 3 = 0.60.
`mbp = fv_base * multiplier`, rounded to 2dp in the trading currency. A tier
outside `{1, 2, 3}` fails the run; a non-integral tier such as `2.5` fails the
run rather than truncating to 2.

If `fv_base` or `tier` is absent, `mbp` is `DATA MISSING`. Code never
substitutes a multiplier, a default tier, or a fallback fair value.

**Regime adjustment** (FRAMEWORK: shift one tier stricter in an elevated
regime, Tier 3 being the floor) is **not implemented in v1**. Apply it by hand
when setting `tier`.

---

## 5. Failure behaviour

- A ticker whose data fetch errors produces an `ERROR` row carrying the
  exception summary. It is never silently dropped from the table. A missing
  row is a worse failure than a visible error.
- A malformed `watchlist.yaml` entry fails the whole run loudly. Do not skip
  the bad entry and continue. This includes unknown keys, bad enum values,
  non-numeric prices, unparseable dates and duplicate tickers.
- Cached data is used when a live fetch fails, and the report says so on the
  freshness line. Cached data still counts against the staleness gate: the gate
  reads the newest close **date** out of the price series, never the cache
  file's fetch timestamp, so stale data can never be made to look fresh.
- An unreadable or empty cache file is ignored rather than half-used.
- A `--ticker` run is a **partial run** and must declare itself as one. It is
  marked in the report title, in a `PARTIAL RUN` banner and in the section
  headings; no section may generalise about "every ticker"; it writes
  `reports/YYYY-MM-DD.<TICKER>.md` so it cannot overwrite the day's full
  report; and its rows carry `ticker_filter` so partial coverage is
  distinguishable when the history is read back.
- The report's freshness line leads with the **oldest** close across the run,
  never the newest. One fresh ticker must not make a stale watchlist read as
  current.

---

## 4b. The ranking key's period basis (FRAMEWORK-EDITS E13)

The key compares figures **across companies**, so every ranked figure is struck
on one length of period.

| Line kind | Decided by | Basis |
|---|---|---|
| **FLOW** — revenue, gross profit, EBIT | `SeriesPoint.statement == "income"` | Trailing twelve months: an annual figure as it stands, else the **sum of the four most recent consecutive quarters**. |
| **STOCK** — total assets, net PP&E | `statement == "balance"` | The latest period end. A position AT an instant has no length. |

`SeriesPoint.period_months` carries the length. The **vendor path declares 12**
because `default_reader` asks for `income_stmt` and `balance_sheet`, which *are*
the annual statements — a fact about the endpoint called, not a guess. A
**manual file takes it from the period label** (`2026-Q2` → 3, `2025-FY` → 12).
`fundamentals_series` stores it; a NULL in a snapshot written before the column
existed reads as 12, because the vendor path is the only thing that wrote those
rows.

**Three refusals, and they are counted apart:**

- **INPUT MISSING** — fewer than four consecutive quarters, or a gap between
  them. Contiguity is a window of `80..100` days between ends, the same bounds
  `vss/xbrl.py` uses to decide a tagged duration is a quarter; the overlap guard
  cannot see a *hole*, and four rows with one in them are not twelve months.
- **`period length not known`** (E13's NOT MEANINGFUL) — the figure is there and
  its length is not recorded. Never ranked on an assumed basis, and never merged
  with an absent line.
- A series of any other resolution — half-years, months — is INPUT MISSING.
  E13's count is taken **literally**: a half-yearly reporter has no quarters, so
  it has fewer than four. Whether the rules should be restated in TIME for such
  a reporter is B12's open question and is not decided in code. A half-yearly
  file carrying a `YYYY-FY` period is rankable with no summing at all.

**Staleness is measured on the END of the window** — a trailing twelve months is
as old as the day it stops. `quality_periods_agree` asks whether the flow window
ends where the stock line was measured; on an annual record that is the question
it always asked.

**`company_fingerprint` is NOT on this basis.** It is an identity test between
two listings of one issuer, not a comparison across companies, so it reads
`latest()` — otherwise a name with under four quarters would become
unfingerprintable and its share classes would silently stop collapsing.

**`ranking.csv` carries `basis` and `basis_periods`** — the basis each row was
computed on, and for a `ttm` row the four period ends summed.

**The sum lives in `vss/ranking.py` and nowhere else.** It is written to no
file, carries no page reference and never reaches §5, whose figures stay exactly
as filed. A test asserts that neither `vss/manual.py` nor `vss/appendix.py`
mentions `flow_figure` or `BASIS_TTM`.

---

## 5a. Report downloads — `vss nordic`

`vss/nordic.py`. Fetches the documents an issuer filed with its Nordic
exchange and records their provenance. **It parses nothing out of them**: a
test asserts the module never calls `source.pdf_to_text` or
`source.html_to_text`, and every manifest entry carries `figures_read: false`.

**The mapping is stored, not resolved per call.** `config/nordic_issuers.yaml`
maps ticker → `market` + `company` (+ optional `language`). The service has no
company directory; resolution is a full-text search, so doing it per call
would mean re-deciding — silently, and possibly differently — which issuer a
ticker means. `--resolve` proposes; `--write` appends, after a backup, and
never replaces an existing entry (phase 6's contract with the watchlist).

**`--period` is MANUAL.** Same vocabulary as `quarters:` and
`config/manual/<TICKER>.yaml`, validated on SHAPE ONLY.
`rules.period_kind_allowed` is deliberately **not** applied: it governs which
labels a ticker may *store in its history*, where the overlap guard needs one
resolution per ticker, and a quarterly reporter still publishes an annual
report. `2025-FY` is the right label for PNDORA.CO's annual accounts.

**What the request never sends, and why.** `cnscategory` filters correctly
with ONE value and silently returns the unfiltered feed with several —
indistinguishable from "every release is a report". `fromDate`/`toDate` are
accepted and ignored. Both are omitted; selection happens on rows the caller
can see. `limit` caps at 200 and pagination is `start`, not `offset`. A listing
shows one page; `--download` WALKS the feed until it finds the id,
bounded by the feed's own `count`, because backfilling a history means
reaching reports several pages back.

**Category is not content.** `--reports` filters on the exchange's category,
which is the issuer's filing choice: Pandora's H1 2026 report is filed under
`Inside information`. The filter therefore prints how many rows it hid and
names that case. The default listing shows every release carrying a document.

**Filenames** are `{ticker}_{period}_{category-slug}_{released}_{lang}_a{N}.{ext}`.
The four requested fields lead; language and attachment index follow because
without them the name is not unique — Betsson files every report twice and its
2026 annual filing carries two documents. The extension follows the bytes that
arrived, not the declared type.

**The manifest** is `sources/manifest.json`, the one file in `sources/` git
tracks (`sources/*` plus `!sources/manifest.json` — git cannot re-include a
file whose parent *directory* is excluded). Per download: URL, disclosure id,
message URL, market, company, category, headline, language, release time,
attachment index and filename, declared vs actual content type, byte count,
SHA-256, and `downloaded_at`. A file with no entry is **PROVENANCE NOT
RECORDED** — a third state, not "secondary"; nothing is back-filled.
Re-downloading identical bytes skips; differing bytes **fail** and name both
digests. A file present with no entry (deleted manifest, or a run that
died between the two writes) has its entry written back from the feed
record and the bytes on disk, marked `recorded_after_the_fact` —
`_record_for` is the single definition both paths build, so a repaired
entry cannot say something different from a fresh one.

**Two documents may honestly share a period.** Betsson files a year-end
report (category 73, Feb) and an annual report (category 270, Apr) for
the same `2025-FY`; the category slug and the release date in the
filename separate them.

**Not served:** `.OL`. Oslo Børs is Euronext, and a `.OL` ticker is told so
rather than handed an empty result set that reads as "no reports".

---

## 5d. The disclosure watcher — `vss watch`

`vss/watch.py`. Asks the Nordic feed what the **WATCH-PRICED, WATCH-GATED and PIPELINE** names have
filed since the last run, and notifies **only** on what would make the owner
re-run §5. It downloads nothing and reads no document; it decides on the
exchange's category and the headline.

**Three kinds pass and no others:** periodic reports (recognised by
`nordic.REPORT_CATEGORIES`, imported and not restated), guidance changes
including pre-announcements, and profit warnings. Leadership changes, M&A,
buybacks, managers' transactions, shareholder notices and AGM material are
rejected.

**The case the filter exists for.** Pandora's company announcement 995 of
2026-01-09 — *"Pandora expects to deliver 6% organic growth and around 24% EBIT
margin in 2025"* — carries the category **Inside information**, the same
category as its CFO appointment, and the word "guidance" appears nowhere in it.
**The title matching catches it**, on `expects to deliver`. **What title
matching cannot do:** a guidance change published under a bland title is
invisible to it, and the filter does not widen to cover that — passing every
*Inside information* release would pass CFO appointments too, which is the same
as no filter. **Every rejected disclosure is therefore printed**, with its
category and headline, so a run says what it did not tell you.

**State lives in a file, not in the watchlist** — `data/watch_state.json`, a
cursor per ticker. A cursor is not a decision. **The first run for a ticker
records where the feed stands and reports nothing**: a first notification
carrying a year of history is how a watcher gets muted on the day it is
installed. A malformed state file is an error, never a silent reset.

**Notification** is a POST to an ntfy topic read from `VSS_NTFY_URL`, one line
per disclosure — ticker, date, title. **Nothing is sent when nothing is new**,
and the command exits 0 either way. A watched ticker with no entry in
`config/nordic_issuers.yaml` — a US or Paris listing — is **named as not on
this feed** rather than silently skipped. `--cron` prints the crontab line;
**the command installs nothing.** No model, no inference, no AI: categories,
regular expressions and a cursor.

## 5c. The figures appendix — `vss appendix`

`vss/appendix.py`. Reads an issuer's xlsx figures appendix through a committed
cell map and emits a filled `config/manual/<TICKER>.yaml`. **Not PDF
extraction** — a cell is a number — but *which* cell is a judgement, so the
mapping is a file rather than a runtime inference.

**`config/manual/maps/<TICKER>.yaml`.** Per schema field: `sheet`, `label`,
optional `section`, `after` and `note`. A field name the manual schema does not
have fails at map load, not at emit.

**Matching is on the label, never the row index.** Exact comparison after
stripping surrounding whitespace only. Resolution order:

1. rows whose label matches exactly;
2. of those, rows carrying a figure in at least one period column — a label row
   blank across every period is a **heading**, not a line (Pandora's margin
   sheet has `EBITDA` as a heading directly above `EBITDA` the line);
3. `section:` — the heading of the period block the row sits under. A
   PERIOD-HEADER ROW is any row whose first cell has text and whose every
   populated remaining cell parses as a period; it defines both the section and
   the columns for everything below it until the next one;
4. `after:` — the first match strictly after the **sole** occurrence of an
   anchor label. An anchor occurring other than once is **refused**: it would
   move the ambiguity rather than resolve it.

A label still matching more than once **fails**, naming every row it matched. A
label the sheet does not carry fails, naming near misses without taking one.

**Column headers** parse as `Q2 2026` → `2026-Q2` (also `H1`/`H2`/`FY`). One
that does not parse **fails the run** — a silently dropped column is a quarter
silently missing. **Periods are keyed by label across sheets**, never by
position.

**`period_end`** is required by the manual schema and the appendix does not
state it. On a declared `period_basis: calendar` it is derived from the column
LABEL (2026-Q2 → 30 June) and the emitted file says so on every period — that is
arithmetic on a heading, not on a figure. On `fiscal` **nothing is derived**:
the map must state `period_ends:`, because where a fiscal year ends is a fact
about the company (backlog B-3).

**Nothing is derived, summed, inferred or rescaled.** A `-`, a blank, `n/a` and
the unicode dashes are `DATA MISSING`, never zero; any other non-numeric cell
**fails** rather than being interpreted.

**Every figure lands `UNVERIFIED`**, `page` is `"<sheet> · <row label>"`, and
the file declares `origin: nordic-xlsx` — a value of `manual.VALID_ORIGINS`,
carried to `TickerFundamentals.origin`, `ranking.Inputs.origin` and
`ranking.csv`.

**Validation is the manual path's own**, imported not repeated: the emitted
text is parsed back through `manual.parse_manual` **before** anything is
written, so the unit contract, the one-scale check, the period labels and the
overlap guard all apply. Because `op_margin` is mapped from a different sheet
than `revenue` and `operating_income`, the margin reconciliation is also a live
check that the two sheets' columns were paired to the same quarter.

**Output is deterministic** (schema field order, oldest period first) so a
re-run against a later appendix is a readable diff. **Writing refuses when the
target exists**, naming how many `VERIFIED` figures it holds; `--force`
replaces it after a backup. Whether a re-run should MERGE is a rule question and
is **not decided here**.

---

## 5b. Manually entered fundamentals — `config/manual/<TICKER>.yaml`

The third source, beside the quote vendor and SEC XBRL. `vss/manual.py`
loads it; `vss manual --ticker X` validates it and gates §5 on it.

**Why.** `vss xbrl` needs a CIK. On the 2026-08-21 screener run **347 of the
533 filter-1 candidates carry a foreign listing suffix**, and for most of a
Nordic or continental list there is no SEC endpoint at all.

**A foreign suffix does not by itself mean no CIK.** A foreign private issuer
files a 20-F and is on `data.sec.gov` — SAP.DE and UNA.AS (CIK 217410) both
are, and both had their §5 A7 proxies built from SEC XBRL. `vss xbrl --cik` is
the first thing to try; this path is for the names that have no CIK to try.
The share of the 347 that is has not been counted, because SEC's ticker→CIK
file lives on `www.sec.gov`, which refuses this host.

**Provenance.** Every figure is MANUAL and carries three things beside its
value: the `source` document (the period's `document:` unless the figure
names its own), a `page`, and a `status` of `UNVERIFIED` or `VERIFIED`. A
value with no page **fails the load**; a bare scalar (`revenue: 1234`) is
refused rather than read, because it could carry neither.

**Shape.** One entry per fiscal period, oldest first, at whatever resolution
the company reports (`reporting_frequency: quarterly | half_yearly`). Each
period states `period_end` — the date the accounts closed, which is what
STALE is measured on; a label alone cannot say how old a figure is.

**The four checks, and the first three are the SEC path's own:**

| Check | Rule | Where it comes from |
|---|---|---|
| **Unit** | `config.unit_problem`, imported not reimplemented: ratio fields inside `rules.FRACTION_BANDS`, and `op_income / revenue` reconciled against `op_margin` to 0.1pp. | Same function the watchlist calls. `source: xbrl`'s exemption from the reconciliation is **NOT** extended to this path: a us-gaap tag says which line an operating income is, and a pair of eyes on a PDF does not. |
| **One scale** | A stable money line jumping by ≥ 1,000× between two periods is a UNIT MIX and fails the load. | `config._check_one_scale`, same factor. Only a comparison ACROSS periods can see it. |
| **STALE** | Newest `period_end` more than `fundamentals.MAX_REPORT_AGE_DAYS` before the as-of date. Not a load failure — the figures are there and are judged too old. | `fundamentals.fetch_one`, same limit, same sentence. **The gate measures it on the rows §5 actually reads**, not on the newest entry: a period carrying only `net_ppe` — a fingerprint line no method touches — must not make an old file read fresh. That is `ranking.py` rule 5 / SHL.DE. |
| **One fiscal period per ratio** | Every ratio §5 forms takes all its legs from ONE period entry. A leg present in an earlier period is **not borrowed**. | `ranking.py` rule 3, generalised. Two periods are not one ratio. |

**A zero carries its evidence (E25).** An entered zero is a claim about the
company, so in the ten fields where a wrong zero improves a ratio — the debt and
lease lines, the capex lines, the finance-cost lines and their nets — the figure
carries `zero_basis: caption|note|subtotal`, naming what the reader saw. Any
other zero there fails the load, and a line the reader could not find is DATA
MISSING rather than zero. `subtotal` is refused where a combined line exists,
because a combined caption has room for the split figures inside it. A zero is
refused outright in the share counts (E22), in a concept the issuer does not
present, and in the non-GAAP memos. §5 is refused with `ZERO DENOMINATOR` when
`net_finance_costs` is zero at the basis: EBIT / 0 is undefined, not large, and
Gate 3's coverage limb would pass on it in silence.

**Capex, split or combined (E23).** §5.1 C reads `capex_ppe` +
`capex_intangibles` when **both** resolve at the basis and `capex_combined` —
the single line some issuers print — when they do not. Never both, and never one
split leg added to the combined line, which would be one figure added to a total
containing it. `manual.capex_legs()` chooses at the basis and returns the reason
with the legs; the report prints **CAPEX ON THE BASIS** every time it shows an
input block. Where an issuer prints the split, the split wins and a combined
figure entered beside it is named as unused.

**Currency, where the accounts and the quote differ (E24).** `fv_base`, `mbp`
and `stop_price` are in the **quote** currency — `rules.compute_mbp` and
`rules.mbp_verdict` compare them to `last_close` and nothing in the code
converts. The conversion happens at or before `fv_base` is written. The rate is
**frozen with the verdict**, and six facts are recorded beside it in the
watchlist's optional `fx:` block — pair with direction, rate, the rate's own
as-of date, source, which side was converted, and the price date it is compared
against. A partial block fails the load. `vss run` prints them under CONVERTED
PRICE LEGS with the rate's age; **nothing acts on that age, and when a frozen
rate is too old to stand is an open question.**

**The §5 gate.** `vss manual` exits **1** and prints `SECTION 5 IS REFUSED`
when a figure **the current basis reads** is still `UNVERIFIED` (E21 — the
others are named under `UNVERIFIED, AND NOT READ AT THIS BASIS` and do not
block, and the basis tested against is printed either way), when the accounts §5 reads are
STALE, when a market figure is priced more than `rules.MAX_CLOSE_AGE_DAYS`
before the run, when a ratio's legs exist but sit in different periods, or
when the file holds no period at all.

**Two things it does NOT refuse on, and both were deliberate:**

- **An absent leg.** A ratio with a leg that is in no period of the file is
  `input missing`, reported and not refused. Absence is the ordinary third
  state: a company with no lease liabilities has none to report, and a
  fortress balance sheet is exactly what §5.3 Tier 1 rewards. Only
  `periods do not match` — every leg present, no single period holding them
  all — is a refusal. The two are counted apart, as `ranking.py` counts
  `QUALITY_MISSING` apart from `QUALITY_MIXED_PERIODS`.
- **The ranking key's quality leg.** `gross profitability` appears in the
  ratio table marked `ranking key` and never produces a refusal. §5 does not
  read it, and gating on it would bar every bank and every property company
  permanently — their accounts present no gross profit by design, which is
  why E6 exempts them. **`UNVERIFIED` is not the same state as absent:** an absent figure is
`DATA MISSING` and has nothing to check, while an unverified one is a number
somebody entered — so it is named in the report with its period, its source
and its page, or the flag gives the owner no way to clear it.

**The `annual:` block (FRAMEWORK-EDITS E15).** A file may carry `annual:`
beside `periods:`, holding figures a company publishes only once a year —
diluted EPS, share counts, leverage ratios. Each entry carries `fiscal_year`,
`period_end`, `document`, `url` and per-figure `value`/`source`/`page`/`status`,
the same shape a period entry has, and is keyed on the **fiscal year rather
than a period label** — a label is what the overlap guard reasons about, and
this block must never enter that reasoning. A fiscal year closing in the next
calendar year (a retailer's 2025 ending 2026-01-31) is an ordinary entry here.

It obeys the same unit contract and the same one-scale check; E15 gave it a
home, not an exemption. It is **excluded from every trailing window by
construction**: `as_record` emits **no series point** from it, so it can never
be summed into a window and can never stand in for a quarter that is not there.
A ratio never straddles the two blocks. **Where a figure is in both, `periods:`
wins** and the annual entry is ignored — *ignored, not absent*: it keeps its
status, so an unverified one still refuses §5, and the load names every figure
it is not using. §5 reads the block where `periods:` does not answer.

**The overlap guard on `periods:` is unchanged.** A `2025-FY` entry beside
`2025-Q1..Q4` would double-count those months in every trailing window and
stays forbidden.

**The ranking key is NOT gated on the status flag.** It is a different
consumer: it produces review work rather than a price, and it reports
`DATA MISSING` for itself. `manual.as_record()` returns a
`fundamentals.TickerFundamentals` speaking the store's own line names, so
`ranking.py` runs on a manual record unchanged.

**Origin.** `TickerFundamentals.origin` is `yfinance` by default and `manual`
on this path; `ranking.Inputs.origin` carries it, and `ranking.csv` has an
`origin` column. `rules.VALID_SOURCES` gains `manual` for a `quarters:` row
the owner read themselves — again without xbrl's reconciliation exemption.

**Not implemented, deliberately.** This module computes no fair value. §5.1's
three methods stay by hand, in the per-name workbook. It decides only whether
their inputs may be handed over.

**Not covered.** Filter 2's limbs read quote-summary scalars
(`freeCashflow`, `totalDebt`, `totalCash`, `ebitda`) that this schema does not
carry, so a manual record feeds the ranking key but not filter 2.

---

## 6. Out of scope for v1

Explicitly not implemented. Do not add these speculatively:

- Anything in FRAMEWORK §4 (8-quarter tables, red/green flags, conviction scoring)
- Anything in FRAMEWORK §5.1 (fair value triangulation)
- FRAMEWORK §6.1 chart pattern detection (double bottoms, H&S, bases)
- FRAMEWORK §2 regime assessment, including the §4 regime tier shift
- Any RSI-driven verdict — RSI is computed and reported only
- Exchange or holiday calendars for the freshness gate
- Broker integration of any kind
- Any LLM or API call
