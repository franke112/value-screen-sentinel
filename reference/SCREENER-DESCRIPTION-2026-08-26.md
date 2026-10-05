# The screener, as the code builds it — description for an external reviewer

**Written 2026-08-26 from the code alone** (`vss/` at commit `884f667` plus the
uncommitted working tree, which touches none of the screener modules). Not from
`reference/FRAMEWORK.md`, not from any HANDOFF. Where FRAMEWORK text and code
disagree, both are stated and nothing is resolved. Nothing was changed in the
course of writing this. Every claim carries `file:line`; line numbers are of
the files as they stand today.

The reviewer cannot see the repository, so the shape first. `python -m vss
screen` is one command with six exclusive modes, each a separate invocation
(`vss/__main__.py:207-296`, dispatched at `vss/screen.py:1701-1786`):

| mode | what it does | network |
|---|---|---|
| `--universe-report` | reads the committed universe CSVs, prints yield and exclusions | none |
| `--snapshot-only` | prices the whole universe, stores raw OHLCV in sqlite | yfinance prices |
| `--filter1` | step 0 (exclusion list) + filter 1 (dislocation band) against a stored snapshot | none |
| `--fundamentals` | fetches fundamentals for filter-1 survivors only, stores them | yfinance quote summary + statements |
| `--filter2` | step 0 + filter 1 + filter 2 (coarse quality) against stored data | none |
| `--rank` | the whole chain + the E6 two-component ranking; `--write-pipeline` appends the top N to the watchlist as PIPELINE | exchange rates only |

The chain is re-run from the stored snapshot at every later stage rather than
read from a results file (`vss/screen.py:665-673`, `879-886`, `1181-1191`), so
a stage cannot drift out of step with the stage before it.

---

## 1. Universe

### 1.1 Which files, how many names each

The universe is a set of static, dated CSVs under `config/universe/`, discovered
by `sorted(directory.glob("*.csv"))` (`vss/universe.py:592-595`). Index
membership is never fetched at runtime; the files are written by
`tools/build_universe.py` by hand and committed (`vss/universe.py:3-6`;
`tools/build_universe.py:1-8`). Five files exist today
(`vss screen --universe-report`, run 2026-08-26, no network):

| file | rows | tier | provenance recorded in its `.meta.json` |
|---|---:|---|---|
| `sp500-2026-08-22.csv` | 503 | A | Wikipedia "List of S&P 500 companies"; `expected_rows` 503; not an approximation |
| `stoxx600-2026-08-22.csv` | 617 | A | iShares STOXX Europe 600 UCITS ETF (DE) holdings CSV, "Fund Holdings as of 20/Aug/2026"; 600 expected; the 17 extra rows are the fund's own cash/FX/futures, written through so the type exclusion is exercised on real data; 17 rows without a Yahoo mapping at build time |
| `omxs-large-mid-2026-08-22.csv` | 316 | A | **APPROXIMATION**: the Yahoo equity screener for exchange STO cut at intraday market cap > SEK 1,658,399,963 (Nasdaq's Mid Cap floor of EUR 150m at EUR/SEK 11.0560, `EURSEK=X` close 2026-08-22). Not Nasdaq's official segment file, which is behind a login; does not separate the Main Market from First North. FRAMEWORK-EDITS E1 approves this on condition it is recorded |
| `tier-b-2026-08-22.csv` | 0 | B | schema only, "not populated in phase 1" |
| `tier-c-2026-08-22.csv` | 0 | C | schema only |

The CSV schema is nine columns, exact and ordered: `ticker_yahoo, ticker_lokal,
isin, namn, marknad, tier, listdatum, valuta, instrumenttyp`
(`vss/universe.py:44-54`). `isin` is empty on every row of every file: no free
source checked carries it, and a wrong ISIN would silently merge two companies
in dedup (`tools/build_universe.py:24-31`; every `.meta.json` carries
`isin_populated: 0` with that note). `instrumenttyp` comes from the source
list's own field — iShares "Asset Class" for STOXX, Yahoo `quoteType` for the
other two (`*.meta.json`, `instrumenttyp_source`).

### 1.2 How they are loaded

`load_universe` (`vss/universe.py:598-661`) reads every CSV, then applies four
steps, each recorded as a `Tally` with two rejection counters that are never
summed (`vss/universe.py:134-161`):

1. **read** (`read_list`, `vss/universe.py:312-337`): the header must equal
   the schema exactly, else the run aborts (`327-331`); a blank row or a row
   with the wrong field count is a hard error (`333-338`). Each row goes
   through `parse_row` (`259-310`): required columns must be non-empty; the
   optional ones (`ticker_yahoo, isin, namn, listdatum, valuta, instrumenttyp`,
   `69-72`) may be empty and are then DATA MISSING; `tier` must be A/B/C
   (`275-277`); an ISIN, if present, must be 12 alphanumerics starting with two
   letters and pass a Luhn check digit (`238-252`, `279-284`); `listdatum` must
   be ISO; `valuta` three letters; `ticker_yahoo` must carry no whitespace. A
   malformed row raises `UniverseError` — the module's rule 1 is "a broken row
   is a HARD ERROR, never a silent skip" (`9-12`). The file's sha256 is taken
   and compared with the `.meta.json`'s recorded digest (`613-627`, `340-353`).
2. **tier_select** (`632-637`): keeps the requested tiers; the CLI default is
   `("A",)` (`vss/__main__.py:264-267`, `vss/screen.py:1728`).
3. **instrument_type** (`apply_type_exclusions`, `405-432`): classifies on
   `instrumenttyp` against `config/universe/instrument_types.yaml`
   (`load_type_rules`, `356-380`; `TypeRules.classify`, `164-185`). The
   `include` vocabulary is equity spellings; `exclude` reasons are `etf, fund,
   preferred, spac, trust, adr, cash_and_derivatives, other_non_equity`; an
   unknown or empty type is a third state, `UNKNOWN`, kept and counted under
   `unknown_action: keep` (`instrument_types.yaml`, last block). The name
   string is never read (`vss/universe.py:16-22`).
4. **yahoo_mapping** (`require_yahoo_mapping`, `435-452`): a row with no
   `ticker_yahoo` is rejected ON MISSING data.
5. **dedup** (`dedupe`, `455-521`), two layers:
   - layer 1, identical `ticker_yahoo` in two source files: the first file in
     discovery order wins and the second is folded in (`477-494`). Discovery
     order is alphabetical, so `omxs-large-mid` beats `stoxx600` for the
     Swedish names both carry — the report shows exactly that (49 merges, all
     "omxs-large-mid kept, stoxx600 folded in").
   - layer 2, same ISIN on two venues: the higher median turnover wins; with
     no turnover the winner is picked by `(marknad, ticker_yahoo)` and the
     merge says so (`_pick_listing`, `524-541`). With ISIN empty everywhere
     this layer is **inert, not clean** — the universe report prints that
     sentence — and cross-venue dual listings survive as two rows.
   - `dual_listing_candidates` (`543-564`) reports same-name/different-market
     pairs without an ISIN and never merges them. Today: ABB.ST/ABBN.SW,
     AZN.L/AZN.ST, EQT/EQT.ST, HUM/HUM.ST, NOKIA-SEK.ST/NOKIA.HE,
     SAMPO-SEK.ST/SAMPO.HE. (EQT and HUM are different companies; the report
     says a name match is not evidence.)

Today's yield (`--universe-report`, 2026-08-26):

| step | in | out | rejected on value | rejected on missing |
|---|---:|---:|---:|---:|
| read | 1436 | 1436 | 0 | 0 |
| tier_select | 1436 | 1436 | 0 | 0 |
| instrument_type | 1436 | 1419 | 17 (`cash_and_derivatives`) | 0 |
| yahoo_mapping | 1419 | 1419 | 0 | 0 |
| dedup | 1419 | 1370 | 49 (duplicate `ticker_yahoo`) | 0 |

Per market: US 503, Stockholm 320, London 124, Xetra 70, Paris 69, Zurich 60,
Milan 40, Amsterdam 35, Madrid 28, Oslo 24, Copenhagen 23, Helsinki 19, Warsaw
18, Brussels 17, Vienna 9, Dublin 6, Lisbon 5 — 1,370 instruments.

### 1.3 What is excluded and why — market cap, liquidity, sector

- **Market cap.** No floor is applied at load time for tier A: `floors.yaml`
  says `A: {}` — "index membership IS the floor". The only market-cap cut in
  the universe is the one *baked into the OMXS file at build time* (SEK 1.66bn,
  above). Tier C's floors (market cap ≥ EUR 300m, median daily turnover ≥ SEK
  2m over 90 days, listing age ≥ 5 years; `floors.yaml`) are **loaded and
  printed, not applied**: `load_floors` (`vss/universe.py:383-402`) is called
  only by `universe_report` (`vss/screen.py:132`, `229-236`), and no filter
  reads a floor. `floors.yaml` also carries a `universal:` block
  (`min_trading_days_52w: 200`, `min_reported_quarters: 8`); `load_floors`
  reads the `tiers` key only (`385`) and a grep of `vss/` finds no consumer of
  either universal key.
- **Liquidity.** Nothing at the universe stage. Turnover enters later, once:
  median daily close×volume over 90 calendar days decides which of two share
  classes of one company survives the ranking (`vss/ranking.py:167`,
  `703-744`, `806-861`).
- **Sector.** Nothing at the universe stage. Sector (yfinance's own string) is
  read in filter 2 to mark the leverage limb NOT APPLICABLE for `Financial
  Services` and `Real Estate` (`config/screener_filter2.yaml`, `not_applicable_sectors`;
  `vss/filters.py:528-533`) and in the ranking to withhold the quality leg for
  the same two (`vss/ranking.py:155`, `973-974`).
- **Instrument type.** 17 rows today, all the STOXX fund's cash/FX/futures.
  The ADR and Swedish-preference-share exclusions cannot fire on the two
  Yahoo-typed lists because Yahoo reports an ADR as `quoteType EQUITY`
  (`sp500-2026-08-22.meta.json`, `instrumenttyp_caveat`;
  `instrument_types.yaml`, the `adr` comment); the universe report prints that
  as "NO DATA".
- **Step 0, the owner's exclusion list**, is applied by the chain, not the
  loader — see §3.1.

### 1.4 When the CSVs were last refreshed

Every `.meta.json` carries `"retrieved": "2026-08-22"`; the files were
committed in `6bd36b7` on 2026-08-22 ("Add `vss screen` phase 1") and
`git log -- config/universe` shows no commit since. The STOXX source line
inside the ETF file was "Fund Holdings as of 20/Aug/2026". The refresh is
manual: `python tools/build_universe.py --asof <date>` then commit
(`tools/build_universe.py:5-8`). The snapshot manifest records each file's
sha256 so a replay can prove it read the same lists (`vss/snapshot.py:19-26`,
`359-390`).

---

## 2. Data per name

### 2.1 Price history — what, how, stored where

- **Call.** `prices.default_download` (`vss/prices.py:136-149`):
  `yf.download(tickers, period=DEFAULT_PERIOD, interval="1d",
  auto_adjust=AUTO_ADJUST, group_by="ticker", threads=False, actions=False)`.
  `DEFAULT_PERIOD = "2y"` and `AUTO_ADJUST = False` are imported from
  `vss/fetch.py:30,35` — the same constants `vss run` uses for the watchlist.
- **Batching, retry, pacing.** 50 tickers per request (`vss/prices.py:63`;
  CLI `--batch-size`), 4 attempts per batch (`66`) with deterministic
  exponential backoff 2·2^(n−1) s capped at 60 s (`67-68`, `121-133`), 0.5 s
  between batches (`70`). A refusal whose text carries one of the throttle
  markers (`74-77`) is classified THROTTLED; any other failure NO_DATA
  (`236-239`).
- **Per-ticker status**, four values kept apart on purpose (`55-59`, `8-22`):
  OK, THROTTLED (retry later), NO_DATA (mapping probably wrong), STALE (a
  series arrived but its newest close is older than the staleness gate as of
  the run date). A ticker absent from a successful multi-ticker response, or
  present as an all-NaN block, is NO_DATA (`152-186`); rows with a null
  `Close` are dropped before storage (`178`, `183`).
- **Truncation.** Every frame is cut to rows dated ≤ `--asof`
  (`vss/prices.py:227`; `metrics.truncate`, `vss/metrics.py:183-193`) so a
  replay of an earlier date never sees later closes; a frame emptied by
  truncation is dropped and its status says so (`228-250`).
- **Staleness.** `rules.stale_close_blocker` (`vss/rules.py:280-304`) blocks
  when the newest close is more than `MAX_CLOSE_AGE_TRADING_DAYS = 3`
  (`vss/rules.py:76`) trading days old, counted Monday–Friday with **no
  holiday calendar** (`trading_days_between`, `247-277`, whose docstring states
  the cost). FRAMEWORK §1.2 (`reference/FRAMEWORK.md:41`) says prices must be
  **≤ 1 trading day** old; FRAMEWORK-EDITS C3 (line 981, DECIDED 2026-08-21)
  reads that as "the most recent session on the relevant exchange calendar".
  The code's constant is 3 trading days and its comment says "THE LIMIT IS
  UNCHANGED AT 3" (`vss/rules.py:73-76`). Both stand.
- **Storage.** One sqlite per as-of date, `data/screener_snapshots/<asof>/snapshot.sqlite`
  (`vss/snapshot.py:48-49`, `125-126`), tables `manifest, source_files,
  universe, rejections, merges, tallies, fetch_status, prices` (`51-122`).
  Raw OHLCV only, never computed metrics (`11-17`). Re-running a date
  **replaces** the file (`177-179`). The manifest carries `asof`, `period`,
  `auto_adjust`, `batch_size`, the universe file hashes and the row counts
  (`vss/screen.py:289-307`). No cache sits between runs on this path: every
  `--snapshot-only` refetches. (The `vss run` price cache under `data/cache`
  is a different path, `vss/runner.py:28`.)
- **The coverage rule now in force.** `metrics.compute` returns the 52-week
  high and the drawdown as DATA MISSING unless the series' first bar is on or
  before `coverage_start(as_of)` = as_of − 52 weeks − 5 trading days
  (`vss/metrics.py:76-77`, `80-93`, `307-309`). The reason is measured in the
  comment at `52-75`: 120 rows of DECK's cache read a 22.4% drawdown against a
  true 28.4%, and a short series passes the staleness gate because its newest
  close is fresh. A 2-year fetch clears the bar; a bare year of trading rows
  need not (`tests/test_metrics.py:337,344`).
- **The 52-week high, exactly.** The highest daily **close** among rows with
  `as_of − 365 days < date ≤ as_of` (`vss/metrics.py:209-221`, `LOOKBACK_DAYS
  = 365` at `29`); drawdown = (high − close)/high (`224-228`). Not the
  intraday high (`5-8`). FRAMEWORK-EDITS B2 (line 121) proposes exactly this
  reading for FRAMEWORK §3 Gate 1's "52-week high"; the item carries no
  DECIDED marker, but `vss/rules.py:493` cites it as the rule in force.
- **Settled vs live close.** `metrics.compute` can drop today's bar before New
  York's 16:00 close when a `settled` cutoff is passed (`vss/metrics.py:96-104`,
  `281-287`). The screener path never passes one: `run_filter1` calls
  `compute(frame, as_of)` (`vss/filters.py:275`), and `metrics.py:262-266`
  says "callers replaying a stored snapshot do not need to". So a
  `--snapshot-only --asof <today>` made during the session stores, and filter
  1 then reads, today's live print as the close of `as_of` (`vss/prices.py:227`
  truncates to ≤ as_of and nothing demotes the same-day bar). The run in §8
  was made at 11:19 CEST on 2026-08-26 with `--asof 2026-08-26`.

### 2.2 Fundamentals — which fields, from where, for whom

Fetched **only for the survivors of filter 1** (`vss/screen.py:653-708`; the
survivor list is recomputed from the snapshot, `665-680`), one ticker at a
time, 0.25 s apart (`vss/fundamentals.py:108`, `398-399`).

- **Call.** `fundamentals.default_reader` (`vss/fundamentals.py:224-237`):
  `yf.Ticker(t).info`, `.income_stmt`, `.balance_sheet` — three requests
  (`99`). The two statements are the **annual** ones; every income-statement
  point is stamped `period_months = 12` on that ground and every balance-sheet
  point `None` (`295-302`).
- **Scalar fields from the quote summary** (`58-64`): text `sector, industry,
  financialCurrency, currency, quoteType`; numeric `freeCashflow,
  operatingCashflow, totalRevenue, revenueGrowth, ebitda, totalDebt,
  totalCash, enterpriseValue, marketCap`.
- **Statement lines kept as dated series** (`72-89`): income — `Total
  Revenue, EBITDA, EBIT, Operating Income, Total Operating Income As Reported,
  Net Income, Gross Profit`; balance — `Total Assets, Current Assets, Total
  Current Assets, Current Liabilities, Total Current Liabilities, Net PPE, Net
  Property Plant And Equipment, Long Term Debt, Long Term Debt And Capital
  Lease Obligation, Ordinary Shares Number`.
- **Two status layers** (`9-19`): per ticker OK/THROTTLED/NO_DATA/STALE, per
  field OK/NO_DATA (THROTTLED when the whole ticker was refused). A bank is OK
  at ticker level and NO_DATA on `ebitda` and `Gross Profit`; the field layer
  is what the yield report's MISSING column reads.
- **Missing or failed.** A field absent, null, non-numeric, boolean or NaN is
  NO_DATA with `number=None` (`240-270`) — never zero. A ticker whose reader
  raises after 4 attempts (`312-343`, backoff shared with prices) is THROTTLED
  or NO_DATA with every field marked the same (`345-352`). A response carrying
  none of the fields and no series is NO_DATA (`358-362`). A record whose
  newest statement period is more than `MAX_REPORT_AGE_DAYS = 550` days
  before `as_of` is STALE — reported, but not recently enough to screen on
  (`101-103`, `364-371`). Downstream, `TickerFundamentals.value/text` return
  `None` for anything not `FIELD_OK` (`168-178`) and `latest()` returns `None`
  rather than zero for an absent line (`200-207`).
- **Look-ahead.** yfinance serves historical prices but only the **latest**
  fundamentals, and `enterpriseValue` is a price-dependent quantity carrying
  the fetch-day quote. The fundamentals manifest records both dates and every
  filter-2 and rank report prints a banner saying whether they agree
  (`vss/screen.py:802-848`, `1101-1142`).
- **Storage.** `data/screener_snapshots/<asof>/fundamentals.sqlite`, its own
  file beside the price snapshot so the price file's reproducibility guarantee
  is not diluted (`vss/snapshot.py:399-441`), tables `manifest,
  fundamentals_status, fundamentals_fields, fundamentals_series` (with
  `period_months`). Overwritten per date (`467-469`).

### 2.3 Exchange rates (ranking only)

`fx.default_lookup` (`vss/fx.py:158-171`) fetches `BASEQUOTE=X` with
`period="5d"` and takes the **last** close — the latest, whatever `--asof`
says; the module's docstring names this as the reason a rank run is auditable
but not reproducible (`13-25`). A pair that fails is recorded and the yields
needing it are withheld; a missing rate never becomes parity (`135-147`,
`250-268`). `--fx-from-manifest` replays a stored run's rates and **fails** on
a pair the manifest lacks rather than fetching it (`215-234`). Minor units
(`GBp, GBX, ZAc, ILA`) map to their major currency before any lookup
(`49-54`, `102-111`); the price series, quoted in the minor unit, is divided
by 100 only where turnover is computed from it (`67-76`).

---

## 3. Every gate and filter, in the order the code applies them

The chain, as `rank` composes it (`vss/screen.py:1181-1227`): exclusion list →
price coverage → series sanity → dislocation band → (fundamentals fetch) →
filter 2's three limbs → share-class collapse → the ranking's own refusals.
For each: threshold, field read, and where a DATA MISSING goes. "ON VALUE"
and "ON MISSING" are the two rejection counters (`vss/universe.py:74-75`).

### 3.0 Step 0 — the exclusion list (not in FRAMEWORK)

`config/screener_exclusions.csv`, schema `ticker_yahoo, skal, datum, kalla`
(`vss/filters.py:53`), loaded by `load_exclusions` (`81-138`): every column
required, `skal` free text and not validated, a ticker listed twice is a hard
error, `datum` must be ISO. `apply_exclusions` (`141-174`) matches on
`ticker_yahoo` exactly — never on name or ISIN — rejects ON VALUE with the
owner's reason and date, and returns the entries that matched nothing so an
inert row is printed rather than mistaken for an active one. Sixteen rows today
(HELD LIAB.ST and SAP.DE, DROPPED MSFT/HNSA.ST/LULU/JD.L/BETS-B.ST/ADBE/
SYNSAM.ST/NKE, SELLING UNA.AS and ULVR.L, E7 UHS, E8-REVIEW ROCK-B.CO,
WATCH-REVIEW DECK and PNDORA.CO). Note: SAP.DE is still `skal: HELD` in this
file although the watchlist now carries it as sold and WATCH-PRICED — the
file is hand-maintained and was not touched today.

### 3.1 Gate 1 — the level leg only (filter 1)

`run_filter1` (`vss/filters.py:243-376`) takes instruments and price frames
and nothing else; it does not know the exclusion list exists (`8-13`,
`248-252`). Three tallies in sequence:

**price_coverage** (`265-292`)
- no frame in the snapshot → ON MISSING, "no price series in the snapshot";
- `metrics.compute` yields no close at or before `as_of` → ON MISSING;
- newest close older than 3 trading days (`stale_close_blocker`) → **ON
  VALUE** — "a close we HAVE, judged too old" (`283-291`).

**series_sanity** (`303-316`; module `vss/series_sanity.py`, K4). Over the
same 365-day window the high reads, two checks: a *scale switch* — a
close-to-close move beyond `JUMP_FACTOR = 1.6` answered within
`ROUND_TRIP_WINDOW_DAYS = 90` by a near-reciprocal move (product within
`ROUND_TRIP_TOLERANCE = 0.15` of 1) — and an *uncorroborated discontinuity* — a
move beyond 1.6× on less than `CORROBORATING_VOLUME_MULTIPLE = 3.0` times the
name's own median volume (`75-95`). Fewer than `MIN_SESSIONS = 30` sessions:
no verdict. A flagged series is rejected **ON MISSING** — "it did not fail the
band; the band could not be evaluated" (`44-46`; `filters.py:296-302`).
Measured cost on the 2026-08-21 universe: MNST (round trip), ELUX-A.ST,
ELUX-B.ST, ORSTED.CO (`48-57`).

**dislocation** (`320-349`). `rules.in_dislocation_band(drawdown)`
(`vss/rules.py:484-504`): `True` for `0.15 ≤ drawdown ≤ 0.50`, both bounds
inclusive (`DISLOCATION_MIN/MAX`, `vss/rules.py:55-56`; B2), `None` when the
drawdown is None. `None` → ON MISSING, worded "series does not cover 52 weeks"
when `covers_52_weeks` is False, else "no 52-week high" (`334-341`); outside
the band → ON VALUE (`343-349`). The field read is `Metrics.drawdown`, i.e.
the closing-high definition of §2.1. The candidate row carries `last_close,
high_52w, drawdown, b1, rsi14, sma50, sma200, pct_vs_sma50, pct_vs_sma200,
volume_ratio` (`180-202`, `350-367`), sorted by ticker — "an ORDER, not a
ranking" (`370-373`).

**B1, the timing leg — reported, not applied.** `b1_metric` (`216-240`):
`(close 180 days ago − last close) / (52-week high − last close)`, the share of
the peak-to-current decline that happened in the trailing `B1_WINDOW_DAYS =
180` (`62`); `None` when no close is old enough or the close is the high. Its
docstring says "reported as CONTEXT and never as a pass/fail limb … per B1 as
decided 2026-08-22, Gate 1 measures today's position". FRAMEWORK §3 Gate 1
(`FRAMEWORK.md:65`) says the decline must have "the bulk … occurring in the
trailing 3–6 months"; FRAMEWORK-EDITS B1 (line 70) proposed ≥ 60% within 180
days and was DECIDED 2026-08-22 as "the timing clause is context". Both stand.

**The catalyst leg — not in code.** FRAMEWORK Gate 1 (`FRAMEWORK.md:65`)
requires the decline be "attributable to an identifiable, dateable catalyst
event (headline + date required)". No screener module reads a catalyst: a grep
of `vss/screen.py`, `vss/filters.py`, `vss/ranking.py` for `catalyst` returns
nothing. The watchlist's `catalyst_date/catalyst_resolved/catalyst_event`
fields feed `vss run`'s blocker (`vss/rules.py:307-320`), and `vss watch`
detects periodic reports and guidance changes for names already on the
watchlist (§5) — neither is a Gate 1 test on a screener candidate.

### 3.2 Gate 2 — not in code

FRAMEWORK §3 Gate 2 (`FRAMEWORK.md:67-77`) classifies the decline driver into
A/B/C/D with "if you cannot confidently classify, the verdict is D". No code
path classifies anything; the string "Gate 2" does not occur in the screener
modules. Filter 2's revenue-trend limb is the nearest mechanical relative and
it is a FLAG that never rejects (§3.3).

### 3.3 What remains of Gate 3 after E30 — and filter 2

FRAMEWORK §3 Gate 3 after E30 (`FRAMEWORK.md:93-127`): the revenue limb and
the gross-margin band are deleted; what remains in the text is net debt/EBITDA
≤ 2.5× (financials excluded), interest coverage ≥ 5×, FCF positive in ≥ 6 of 8
quarters, and no going-concern / auditor change / restatement.

Filter 2 (`run_filter2`, `vss/filters.py:587-635`) evaluates three limbs, with
every threshold read from `config/screener_filter2.yaml` (`status: DECIDED`,
2026-08-22) and none hardcoded (`381-384`; `tests/test_filter2.py:90`):

| limb | code | field read | rule | DATA MISSING |
|---|---|---|---|---|
| `free_cash_flow` | `fcf_limb`, `514-522` | quote summary `freeCashflow` (TTM) | PASS if > `min: 0.0`, FAIL otherwise (zero fails) | field absent → DATA MISSING |
| `net_debt_to_ebitda` | `leverage_limb`, `525-552` | `sector`, `totalDebt`, `totalCash`, `ebitda` | NOT APPLICABLE for `Financial Services`, `Real Estate` (E3); net debt = totalDebt − totalCash; net debt ≤ 0 → PASS without a ratio; EBITDA ≤ 0 → FAIL with net debt, PASS with net cash (config `non_positive_ebitda`); else PASS iff net debt/EBITDA ≤ `max: 3.5` | debt or cash absent → DATA MISSING; EBITDA absent → DATA MISSING |
| `revenue_trend` | `revenue_limb`, `555-584` | annual `Total Revenue` series, last 4 points | ≥ 2 consecutive annual declines → **FLAG**; never FAIL (`action: FLAG`, B9) | < 2 points → DATA MISSING |

A record absent from the fundamentals store is DATA MISSING on all three with
the wording "not in the fetch" (`511`, `516`, `527`, `564`). Then (`603-627`):
any FAIL → rejected ON VALUE; any DATA MISSING with `on_missing_action:
pass_through` (the decided value; E4) → the name survives, marked; under
`reject` it would be rejected ON MISSING. NOT APPLICABLE and FLAG never reject.

Where the code and the FRAMEWORK text part, both stated:
- leverage cap **3.5×** in code (config `max: 3.5`, "section 4.2.5 hard kill";
  FRAMEWORK-EDITS E2, line 1112, DECIDED 2026-08-22) against **2.5×** in Gate
  3's text (`FRAMEWORK.md:124`); the config keeps 2.5 under `not_chosen`;
- FCF **TTM sign** in code against **≥ 6 of 8 quarters** in the text
  (`FRAMEWORK.md:126`); the config states the deviation — quarterly cash-flow
  history is not obtainable from this source for a material share of the
  universe — and the report says a pass here "has NOT passed Gate 3's FCF
  limb. It has failed to fail it" (`vss/screen.py:992-1002`);
- **interest coverage ≥ 5×** and the **going-concern / auditor / restatement**
  limb: no code;
- revenue is tested by the screener as an **annual reported** trend and only
  flagged, while §4.2.1 (`FRAMEWORK.md:147`) is a hard kill on an **organic**
  basis where disclosed. FRAMEWORK-EDITS B9 (line 362, DECIDED 2026-08-22) is
  the reason the code flags rather than kills.

Filter 2 also carries a stale-statement pass-through: a record STALE at fetch
time survives filter 2 (its limbs read current quote-summary figures) and is
then excluded by the ranking (`vss/screen.py:1046-1069`).

### 3.4 Gate 4 — not in code; the A7 proxy is not computed anywhere

FRAMEWORK §3 Gate 4 (`FRAMEWORK.md:129-132`): at least 2 of 3 — forward P/E ≥
20% below its own 5-year median; EV/EBIT or P/S below peer median; FCF yield ≥
1.5× sector median. No screener code computes a peer median, a 5-year median
multiple or an FCF yield, and no test of "2 of 3" exists. The "A7 proxy" is
FRAMEWORK-EDITS B5's trailing-P/E stand-in for an unobtainable forward
multiple (line 177, DECIDED 2026-08-21), which belongs to §5 Method A in the
hand chain; in `vss/` the only references are field notes in the manual store
schema (`vss/manual.py:456-460`: "The A7 trailing-P/E proxy (FRAMEWORK-EDITS
B5) is built from five years of this line") — a description of what a hand
reader may do with five years of diluted EPS, not a computation. The
screener's `EBIT / enterprise value` (§4) is a ranking component with no
threshold and no peer comparison; it is not Gate 4.

### 3.5 The RSI veto — not a filter anywhere

FRAMEWORK §6.2 (`FRAMEWORK.md:318`): "No new tranche while RSI(14) > 70" — an
entry-timing rule. The screener computes RSI(14) with Wilder smoothing
(`vss/metrics.py:137-159`) and SMA50/200 and carries them as columns on every
candidate (`vss/filters.py:180-202`, `350-367`); the standing rule at
`vss/screen.py:20-49` says they "are FIELDS. THEY ARE NEVER FILTERS", with the
SAP.DE record that motivates it, and two tests hold the line
(`tests/test_screen.py:819`, `tests/test_filters.py:378`). `vss run` does not
implement the veto either (no `rsi` in `vss/rules.py`).

### 3.6 Filters not named in FRAMEWORK, in the order they act

1. Instrument-type exclusion and dedup (§1.2).
2. The exclusion list (§3.0).
3. Price coverage and the 3-trading-day staleness gate (§3.1).
4. Series sanity, K4 (§3.1).
5. The 52-weeks-plus-five-days coverage bar (§2.1).
6. Filter 2's NOT APPLICABLE sectors and pass-through (§3.3).
7. **Share-class collapse** (`vss/ranking.py:806-861`): two candidates whose
   `EBIT`-alias, `Total Revenue`/`Operating Revenue`, net PP&E and `Total
   Assets` are identical to the last digit, with the same `financialCurrency`
   and sector, are one company (`company_fingerprint`, `682-700`; a partial
   fingerprint never matches); the most traded listing survives by median
   daily turnover over 90 days (`703-744`), compared in the group's own
   currency when it has one and through an EUR rate otherwise (`767-803`);
   with no turnover the fallback is alphabetical and the merge says so
   (`837-844`). Rejection ON VALUE, "same company, less traded listing" (`857`).
8. **Stale accounts, two questions** (`score`, `951-1057`): the record's own
   fetch-time STALE flag (newest period > 550 days) excludes it before either
   leg is read (`963-969`); then, on the rows the key actually read, the
   oldest period fed into a computed component must be ≤ 550 days before
   `as_of` (`stale_note`, `923-948`, `1041-1057`). Excluded whole, counted ON
   VALUE, listed in its own section (`1092-1095`, `1122-1126`).
9. **Enterprise-value bound** (`implied_net_cash_note`, `867-920`): implied
   net cash = marketCap − enterpriseValue (both quote-currency major units,
   converted with the same rate the yield uses) may not exceed total assets;
   if it does the yield is withheld and the quality leg kept — a rejection ON
   MISSING data, never on value (`1015-1023`). With market cap, EV or total
   assets absent the question is not asked (`906-911`).
10. **Mixed periods** (K6): gross profit and total assets must carry the same
    period end, else the quality leg is DATA MISSING, counted apart from an
    absent line (`399-417`, `982-987`).
11. **Unit slip** (L3/E8): two EBIT labels for one period whose ratio is a
    round power of 1,000 within 1% are one figure in two units; EBIT is DATA
    MISSING, named (`476-499`, `577-584`).
12. **One period basis** (E13): a flow line is ranked only as an annual figure
    or as four consecutive quarters (80–100 days apart) summed; fewer, a gap,
    a half-year, or an unrecorded length is INPUT MISSING / NOT MEANINGFUL
    (`233-256`, `282-331`).

---

## 4. Scoring and ranking

### 4.1 §4.4 points — not computed by the screener

FRAMEWORK §4.4 (`FRAMEWORK.md:160`): `Score = (Gates passed: 0–5) + Σ green −
Σ soft`, hard kills override; ≥ 7 high, 5–6 medium, ≤ 4 drop or watchlist. No
screener module computes gates passed, green flags or soft flags; the strings
`4.4` and `conviction` do not occur in `vss/screen.py`, `vss/filters.py`,
`vss/ranking.py` or `vss/pipeline.py`. The conviction score is struck by hand
and enters the watchlist as `tier` (`vss/config.py`, `tier` key; the SAP.DE
entry's comment records "§4.4 score 7"). The PIPELINE note the screener writes
carries no score (`vss/pipeline.py:104-161`).

### 4.2 What the code ranks on — FRAMEWORK-EDITS E6

`rank_candidates` (`vss/ranking.py:1145-1160`) → `extract_inputs` → `score` →
`rank`. Two components, both "more is better":

- **Quality: gross profitability = `Gross Profit` / `Total Assets`**
  (`1001`). Numerator on the E13 basis via `flow_figure` (`618`, `282-331`);
  denominator the latest balance-sheet point (`619`, `604-613`). Exact labels,
  no alias set (`138-144`). Withheld as `sector exempt` for Financial Services
  and Real Estate (`155`, `973-974`); `period length not known` (`975-979`);
  `input missing` (`980-981`); `periods do not match` (`982-987`);
  `denominator not positive` (`988-994`). A negative gross profit is ranked,
  last (`995-1001`).
- **Price: earnings yield = EBIT / enterprise value**, EV converted from the
  quote currency into the reporting currency at the run's rate (`1007`,
  `1027-1030`). EBIT via `choose_ebit` (`516-586`): every alias in
  `EBIT_ALIASES = ("Total Operating Income As Reported", "Operating Income",
  "EBIT")` (`117-119`) is put on the basis first; the newest window end any
  alias reaches is settled first, then meaning decides within it; the unit
  check follows. `ebitda` is never read (`42-44`; AST test
  `tests/test_ranking.py:138`). Withheld for: no EV, no rate, impossible EV,
  no EBIT, EV ≤ 0 (`1008-1032`).

**Ranks and the head order** (`rank`, `1087-1142`). Stale rows out first
(`1094-1095`). Among the rest, names with **both** components form the main
list; names with a yield only form a separate section, never interleaved; names
with no yield are unrankable (`1097-1101`). Within the main list each component
gets a competition rank — highest value rank 1, equal values share the better
rank, 1-2-2-4 (`competition_ranks`, `1070-1084`) — the two ranks are summed
(`1108`) and the list is sorted ascending on `(sum, ticker)` (`1113`): **the
tie-break is alphabetical on the ticker**, stated in the code as "a stated
arbitrary rule rather than an unstated one". The yield-only section sorts on
`(ey_rank, ticker)` (`1119`). The report prints the top `TOP_N = 20`
(`vss/screen.py:1159`, `1572-1586`); `--write-pipeline` takes the top `--top`
(default 5) **of the main list only** (`vss/__main__.py:246-249`;
`vss/pipeline.py:258-265`). Nothing weights, thresholds or scores the two
components (`13-17`).

So what decides the head is: survive to filter 2, carry both a computable
gross-profit/total-assets ratio on one period end and a computable EBIT/EV on
one basis with a rate and a possible EV, be under 550 days old on those rows,
and then the sum of two competition ranks, ties by ticker.

---

## 5. Schedule and outputs

### 5.1 The timer

`deploy/vss.timer` fires `OnCalendar=*-*-* 22:30:00`, `Persistent=true`, and
starts `deploy/vss.service`, whose `ExecStart` is
`~/vss/.venv/bin/python -m vss run` — the **watchlist monitor**,
not the screener. There is no unit for the screener: `deploy/` holds
`vss.service` and `vss.timer` only, and `reference/SCREENER.md:850` ("Phase 7
— its own systemd timer … Separate unit") describes a unit that does not
exist. On this machine, today, `systemctl --user list-timers --all` lists **0
timers** and `~/.config/systemd/user/` holds neither file, so even the
watchlist run is not scheduled here. Every screener phase runs by hand, one
mode per invocation (`vss/screen.py:1701-1786`).

### 5.2 The watcher

`vss watch` (`vss/watch.py`) reads the watchlist entries whose status is
`WATCH-PRICED`, `WATCH-GATED` or `PIPELINE` (`95`, `246-253`; both halves of
E27's split, for the reason at `86-94`), asks the Nasdaq Nordic disclosure
feed for each one that `config/nordic_issuers.yaml` resolves (`270-284`; a US
or Paris listing is reported "not on this feed"), and classifies each new
release (`147-165`): a periodic report by the exchange's own category
(`nordic.REPORT_CATEGORIES`), otherwise by title regexes for guidance changes
and profit warnings (`113-129`). Everything else is rejected and **printed**
(`350-364`). The cursor lives in `data/watch_state.json` (`75`); the first
run for a name baselines and reports nothing (`299-303`). Passing lines are
POSTed to an ntfy topic read from `VSS_NTFY_URL` (`80`, `203-230`). It
downloads nothing and reads no document (`7-8`, `41`). `vss watch --cron`
prints `7 7,17 * * 1-5 … python -m vss watch >>
data/watch.log` and installs nothing (`384-388`); the user crontab on this
machine carries no such line.

### 5.3 What PIPELINE means

`PIPELINE` is a watchlist `status` (`vss/pipeline.py:41`; one of
`VALID_STATUSES`, `vss/rules.py:103`) written by exactly one path: `vss screen
--rank --write-pipeline` (`vss/screen.py:1239-1251`). The entry written is
`ticker, name, currency, status, notes` and nothing else (`WRITABLE_KEYS`,
`vss/pipeline.py:45`, `62-72`); `mbp, fv_base, tier, stop_price` are forbidden
and the write refuses if any would appear (`48`, `210-215`). Only the top
`--top` (default 5) of the **both-legs** list is eligible (`248-265`). The
note is assembled from measured figures — rank of N, sector, market, drawdown
from the 52-week closing high, gross profitability, earnings yield, a pence
warning where the quote is in a minor unit — and ends "No fv_base, no tier
and no mbp — section 5 has not been run. This entry is review work, not a
buy" (`104-161`). The file is backed up to
`config/watchlist.yaml.bak-<date>-pre-pipeline` (`184-187`, `223-225`), the
block is **appended as text** after a dated header so hand comments survive
(`227-234`), an existing ticker is never touched (`206-208`), and the file is
re-parsed with the real loader and restored from the backup if it no longer
loads (`236-244`).

In `vss run` a PIPELINE name is not HELD, so it raises no missing-stop
blocker (`vss/rules.py:338-350`) but carries the `NO STOP DEFINED` flag
(`420-437`) and is otherwise assessed like any entry. FRAMEWORK-EDITS E12
(line 2448, DECIDED 2026-08-24) rules that Gate 1 is frozen at PIPELINE entry
and `dd_at_entry` plus the peak date are stored: the watchlist schema accepts
`dd_at_entry` and `peak_date` and validates them as a pair in [0, 1]
(`vss/config.py:65-66`, `317-345`), but **no code writes them** (the pipeline
writer's key list above) and **no code reads them** (a grep of `vss/` for
`dd_at_entry` finds only `vss/config.py`). `vss watch` watches PIPELINE names
(§5.2).

### 5.4 What is written where

| artefact | written by | contents |
|---|---|---|
| `data/screener_snapshots/<asof>/snapshot.sqlite` | `--snapshot-only` (`vss/screen.py:288-307`; `vss/snapshot.py:163-266`) | manifest (asof, period, auto_adjust, batch_size, universe file sha256s, counts), universe rows, rejections, merges, tallies, per-ticker fetch status, raw daily OHLCV |
| `data/screener_snapshots/<asof>/fundamentals.sqlite` | `--fundamentals` (`vss/screen.py:695-704`; `vss/snapshot.py:458-513`) | manifest (fundamentals_asof, filter1_asof, requests_per_ticker), per-ticker status, per-field values with status, dated statement series with `period_months` |
| `data/screener_runs/<asof>/filter1-candidates.csv` | `--filter1` (`vss/screen.py:455-490`) | one row per band survivor: close, 52w high, drawdown, B1, RSI, SMAs, volume ratio |
| `data/screener_runs/<asof>/filter2-candidates.csv` | `--filter2` (`889-922`) | survivors with the three limb states and details |
| `data/screener_runs/<asof>/ranking.csv` | `--rank` (`1232-1344`) | every scored name in four sections — `ranked`, `earnings_yield_only`, `unrankable`, `stale` — with both ratios, ranks, the figures, their period ends, basis and periods summed, fx pair and rate, origin |
| `data/screener_runs/<asof>/ranking-manifest.json` | `--rank` (`1346-1370`) | asof, key, section counts, quality-state counts, every fx rate with its date and source, failures, whether rates were fetched or replayed |
| stdout | every mode | the human report, including the yield table, look-ahead banner, fx table, sections, top 20 |
| `config/watchlist.yaml` | `--rank --write-pipeline` only (§5.3) | appended PIPELINE entries |

`data/` and `reports/` are gitignored (`.gitignore`, "run artifacts"), so **no
screener run is committed**. The committed reference for the ranking is the
frozen 2026-08-21 candidate set under `tests/fixtures/ranking-acceptance/`
(`fields-`, `series-`, `status-`, `fx-2026-08-21.*`, written by
`tools/freeze_ranking_acceptance.py`) with its expected head pinned in
`tests/test_ranking_acceptance.py:146-207`. The sqlite at `data/vss.sqlite` is
`vss run`'s store (`vss/runner.py:29`, `vss/store.py`) and the screener never
writes to it.

### 5.5 What §5 reads from it

Nothing mechanically. Section 5 runs on a hand-built (or `vss xbrl` /
`vss appendix`-written) `config/manual/<TICKER>.yaml` and on the watchlist
entry (`vss/manual.py`, `vss/runrecord.py`); the screener's fundamentals store
is not an input to it, and the screener writes no `fv_base`, `tier`, `mbp` or
`stop_price` (`vss/pipeline.py:7-10`, `48`). The only screener output that
reaches the §5 side is the PIPELINE row itself — its status and the measured
figures quoted as prose in `notes` (`vss/pipeline.py:122-134`) — which a person
then works up by hand. The report's own words: "the whole FRAMEWORK section 5
chain is then run by hand. No code path in this module, or any module it
calls, may set a buy price or a fair value" (`vss/screen.py:3-8`; asserted by
`tests/test_screen.py:829` and `tests/test_ranking.py:533`).

---

## 6. Tests that cover the screener

One line per test: `file:line name — what it asserts` (the docstring's first
line where there is one; otherwise the test's own name, which in this suite is
the assertion). Generated from the test files' AST on 2026-08-26.


**`tests/test_universe.py`** — universe loading, exclusions, dedup, floors (34 tests)

- `tests/test_universe.py:81` `test_reads_a_well_formed_row` — reads a well formed row
- `tests/test_universe.py:91` `test_reordered_header_is_rejected` — reordered header is rejected
- `tests/test_universe.py:99` `test_extra_column_is_rejected` — extra column is rejected
- `tests/test_universe.py:105` `test_short_row_is_a_hard_error_not_a_skip` — short row is a hard error not a skip
- `tests/test_universe.py:115` `test_blank_row_is_a_broken_row` — blank row is a broken row
- `tests/test_universe.py:125` `test_missing_required_field_names_the_column_and_the_line` — missing required field names the column and the line
- `tests/test_universe.py:132` `test_malformed_isin_is_a_hard_error` — malformed isin is a hard error
- `tests/test_universe.py:138` `test_isin_check_digit` — isin check digit
- `tests/test_universe.py:144` `test_bad_date_and_bad_currency_and_bad_tier` — bad date and bad currency and bad tier
- `tests/test_universe.py:156` `test_optional_columns_may_be_empty` — optional columns may be empty
- `tests/test_universe.py:168` `test_missing_file_is_an_error` — missing file is an error
- `tests/test_universe.py:173` `test_empty_file_without_a_header_is_an_error` — empty file without a header is an error
- `tests/test_universe.py:180` `test_header_only_file_loads_as_zero_rows` — header only file loads as zero rows
- `tests/test_universe.py:198` `test_classification_is_case_and_space_insensitive` — classification is case and space insensitive
- `tests/test_universe.py:205` `test_exclusion_reads_the_type_never_the_name` — exclusion reads the type never the name
- `tests/test_universe.py:216` `test_excluded_types_are_counted_on_value` — excluded types are counted on value
- `tests/test_universe.py:226` `test_unknown_type_is_kept_and_counted_by_default` — unknown type is kept and counted by default
- `tests/test_universe.py:234` `test_unknown_type_can_be_excluded_and_lands_in_the_missing_column` — unknown type can be excluded and lands in the missing column
- `tests/test_universe.py:248` `test_a_type_in_both_lists_is_a_config_error` — a type in both lists is a config error
- `tests/test_universe.py:255` `test_unknown_action_must_be_valid` — unknown action must be valid
- `tests/test_universe.py:265` `test_missing_yahoo_symbol_is_a_missing_data_rejection` — missing yahoo symbol is a missing data rejection
- `tests/test_universe.py:277` `test_same_ticker_in_two_lists_collapses_to_one` — same ticker in two lists collapses to one
- `tests/test_universe.py:294` `test_same_isin_on_two_venues_keeps_the_higher_turnover` — same isin on two venues keeps the higher turnover
- `tests/test_universe.py:307` `test_isin_dedup_without_turnover_says_so` — isin dedup without turnover says so
- `tests/test_universe.py:320` `test_rows_without_isin_are_never_merged` — rows without isin are never merged
- `tests/test_universe.py:330` `test_dual_listing_candidates_are_reported_not_merged` — dual listing candidates are reported not merged
- `tests/test_universe.py:340` `test_same_name_on_one_market_is_not_a_dual_listing` — same name on one market is not a dual listing
- `tests/test_universe.py:351` `test_floors_load_and_expose_currency` — floors load and expose currency
- `tests/test_universe.py:363` `test_a_money_floor_without_a_currency_is_rejected` — a money floor without a currency is rejected
- `tests/test_universe.py:370` `test_unknown_tier_in_floors_is_rejected` — unknown tier in floors is rejected
- `tests/test_universe.py:380` `test_load_universe_selects_tiers_and_reports_every_step` — load universe selects tiers and reports every step
- `tests/test_universe.py:402` `test_load_universe_rejects_an_unknown_tier` — load universe rejects an unknown tier
- `tests/test_universe.py:408` `test_yield_table_never_sums_the_two_rejection_kinds` — yield table never sums the two rejection kinds
- `tests/test_universe.py:423` `test_committed_lists_load_cleanly` — The real files in config/universe/ must parse.

**`tests/test_screen.py`** — the modes, the reports, the chain, structural rules (62 tests)

- `tests/test_screen.py:71` `test_universe_report_counts_per_market` — universe report counts per market
- `tests/test_screen.py:78` `test_universe_report_shows_exclusions_by_reason` — universe report shows exclusions by reason
- `tests/test_screen.py:84` `test_universe_report_counts_the_unmapped` — universe report counts the unmapped
- `tests/test_screen.py:90` `test_universe_report_splits_value_from_missing` — universe report splits value from missing
- `tests/test_screen.py:96` `test_universe_report_states_the_isin_coverage` — universe report states the isin coverage
- `tests/test_screen.py:101` `test_universe_report_shows_the_tier_floors_with_currency` — universe report shows the tier floors with currency
- `tests/test_screen.py:107` `test_tier_b_is_only_loaded_when_asked` — tier b is only loaded when asked
- `tests/test_screen.py:117` `test_snapshot_only_fetches_stores_and_reports` — snapshot only fetches stores and reports
- `tests/test_screen.py:131` `test_snapshot_only_filters_nothing` — Both survivors are stored whatever their prices look like.
- `tests/test_screen.py:143` `test_a_ticker_that_did_not_arrive_is_named_in_the_report` — a ticker that did not arrive is named in the report
- `tests/test_screen.py:153` `test_the_report_carries_the_yield_table` — the report carries the yield table
- `tests/test_screen.py:162` `test_limit_is_flagged_as_a_partial_run` — limit is flagged as a partial run
- `tests/test_screen.py:171` `test_asof_truncation_is_visible_in_the_manifest` — asof truncation is visible in the manifest
- `tests/test_screen.py:209` `test_filter1_runs_step_0_then_the_band` — filter1 runs step 0 then the band
- `tests/test_screen.py:221` `test_filter1_report_carries_the_yield_table_with_both_columns` — filter1 report carries the yield table with both columns
- `tests/test_screen.py:235` `test_filter1_names_an_inert_exclusion_entry` — filter1 names an inert exclusion entry
- `tests/test_screen.py:246` `test_filter1_writes_the_candidate_table` — filter1 writes the candidate table
- `tests/test_screen.py:259` `test_filter1_says_the_order_is_not_a_ranking` — filter1 says the order is not a ranking
- `tests/test_screen.py:270` `test_a_replay_from_a_later_snapshot_declares_the_survivorship_caveat` — a replay from a later snapshot declares the survivorship caveat
- `tests/test_screen.py:282` `test_a_snapshot_older_than_the_run_date_is_refused` — a snapshot older than the run date is refused
- `tests/test_screen.py:292` `test_no_snapshot_at_all_is_a_clear_error` — no snapshot at all is a clear error
- `tests/test_screen.py:301` `test_filter1_fetches_nothing` — Structural: the filter path must not reach the network.
- `tests/test_screen.py:359` `test_fundamentals_are_fetched_only_for_filter1_survivors` — fundamentals are fetched only for filter1 survivors
- `tests/test_screen.py:370` `test_the_fundamentals_report_carries_the_look_ahead_banner` — The user made this a hard requirement: it must be in the output.
- `tests/test_screen.py:383` `test_the_filter2_report_carries_the_look_ahead_banner_naming_both_dates` — the filter2 report carries the look ahead banner naming both dates
- `tests/test_screen.py:396` `test_the_banner_says_contemporaneous_when_the_dates_agree` — Reachable: snapshot, fetch and run all on the same day.
- `tests/test_screen.py:414` `test_filter2_report_states_the_decided_thresholds_and_their_source` — filter2 report states the decided thresholds and their source
- `tests/test_screen.py:426` `test_filter2_report_reconciles_the_survivor_set_against_the_store` — filter2 report reconciles the survivor set against the store
- `tests/test_screen.py:436` `test_filter2_names_a_survivor_the_store_never_saw` — Drift is what this check exists for, so it is provoked.
- `tests/test_screen.py:451` `test_filter2_without_a_fundamentals_store_says_what_to_run` — filter2 without a fundamentals store says what to run
- `tests/test_screen.py:462` `test_filter2_writes_its_own_candidate_table` — filter2 writes its own candidate table
- `tests/test_screen.py:474` `test_the_yield_report_gains_a_filter2_row` — the yield report gains a filter2 row
- `tests/test_screen.py:493` `test_rank_produces_two_sections_and_saves_the_full_list` — rank produces two sections and saves the full list
- `tests/test_screen.py:518` `test_the_rank_report_states_what_the_quality_leg_is_and_what_it_replaced` — E6 superseded E5's leg. A report that printed only the new definition
- `tests/test_screen.py:532` `test_the_rank_report_prints_every_exchange_rate_it_used` — E5(b)'s binding condition, carried into E6: saved per run AND reported.
- `tests/test_screen.py:582` `test_the_fx_chain_fixture_actually_ranks_something` — Guards every assertion below from passing on an empty list.
- `tests/test_screen.py:593` `test_a_rank_run_says_it_is_auditable_and_NOT_reproducible` — SCREENER.md claimed the stronger word until 2026-08-22.
- `tests/test_screen.py:613` `test_a_replayed_run_reproduces_the_stored_run_rate_for_rate` — K7's actual claim: run it, replay it, get the same numbers.
- `tests/test_screen.py:639` `test_a_fresh_lookup_would_have_changed_the_answer` — So the test above is measuring the replay and not a coincidence.
- `tests/test_screen.py:656` `test_the_look_ahead_banner_says_enterprise_value_is_a_PRICE` — It sits among the fundamentals and is not one. A replay divides EBIT by
- `tests/test_screen.py:669` `test_the_rank_report_says_it_is_the_only_ordering_and_not_advice` — the rank report says it is the only ordering and not advice
- `tests/test_screen.py:680` `test_the_rank_report_carries_the_look_ahead_banner` — the rank report carries the look ahead banner
- `tests/test_screen.py:689` `test_rank_writes_nothing_to_the_watchlist` — rank writes nothing to the watchlist
- `tests/test_screen.py:702` `test_cli_parses_the_rank_flag` — cli parses the rank flag
- `tests/test_screen.py:708` `test_cli_parses_the_pipeline_flags` — cli parses the pipeline flags
- `tests/test_screen.py:714` `test_rank_collapses_share_classes_before_ranking` — rank collapses share classes before ranking
- `tests/test_screen.py:724` `test_the_rank_report_says_the_yield_only_names_are_not_written` — the rank report says the yield only names are not written
- `tests/test_screen.py:734` `test_write_pipeline_is_off_unless_asked` — write pipeline is off unless asked
- `tests/test_screen.py:747` `test_cli_parses_the_screen_flags` — cli parses the screen flags
- `tests/test_screen.py:757` `test_cli_parses_the_phase3_flags` — cli parses the phase3 flags
- `tests/test_screen.py:766` `test_cli_parses_the_filter1_flags` — cli parses the filter1 flags
- `tests/test_screen.py:775` `test_screen_without_a_mode_explains_itself_and_fails` — screen without a mode explains itself and fails
- `tests/test_screen.py:785` `test_a_broken_universe_exits_with_a_code_not_a_traceback` — a broken universe exits with a code not a traceback
- `tests/test_screen.py:802` `test_framework_constants_are_imported_from_rules_never_redefined` — framework constants are imported from rules never redefined
- `tests/test_screen.py:813` `test_the_staleness_gate_is_the_one_rules_py_owns` — the staleness gate is the one rules py owns
- `tests/test_screen.py:819` `test_rsi_and_sma_are_never_filters_and_the_reason_stays_on_the_record` — rsi and sma are never filters and the reason stays on the record
- `tests/test_screen.py:829` `test_the_screener_never_touches_the_watchlist_or_prices_a_position` — No path to watchlist.yaml, no buy price, no fair value.
- `tests/test_screen.py:887` `test_no_ai_in_the_screener` — no ai in the screener
- `tests/test_screen.py:894` `test_insider_data_is_not_a_ranking_input_yet` — insider data is not a ranking input yet
- `tests/test_screen.py:903` `test_a_replay_into_another_date_is_called_CROSS_DATED` — REPRODUCIBLE was true and misleading at once: the run repeats exactly
- `tests/test_screen.py:920` `test_a_replay_on_its_own_date_is_just_REPRODUCIBLE` — a replay on its own date is just REPRODUCIBLE
- `tests/test_screen.py:933` `test_a_manifest_with_no_date_is_reported_as_uncheckable` — Absence of the field is a reason to say so, not to assume agreement.

**`tests/test_filters.py`** — the exclusion list, filter 1, B1, the phase-2 acceptance test (38 tests)

- `tests/test_filters.py:84` `test_a_well_formed_list_loads` — a well formed list loads
- `tests/test_filters.py:93` `test_a_wrong_header_is_rejected` — a wrong header is rejected
- `tests/test_filters.py:101` `test_every_column_is_required` — every column is required
- `tests/test_filters.py:109` `test_a_bad_date_is_a_hard_error` — a bad date is a hard error
- `tests/test_filters.py:115` `test_a_short_row_is_a_hard_error` — a short row is a hard error
- `tests/test_filters.py:125` `test_one_name_one_reason` — one name one reason
- `tests/test_filters.py:134` `test_skal_is_free_text_and_not_validated` — The reasons are the owner's. A new one must not need a code change.
- `tests/test_filters.py:143` `test_a_missing_list_is_an_error` — a missing list is an error
- `tests/test_filters.py:151` `test_excluded_names_are_removed_and_counted_on_value` — excluded names are removed and counted on value
- `tests/test_filters.py:167` `test_the_reason_is_carried_into_the_tally_so_it_can_be_grouped` — the reason is carried into the tally so it can be grouped
- `tests/test_filters.py:179` `test_an_entry_matching_nothing_is_reported_as_inert` — An inert entry that reads as active is how a name quietly comes back.
- `tests/test_filters.py:191` `test_matching_is_on_ticker_never_on_name` — matching is on ticker never on name
- `tests/test_filters.py:200` `test_an_empty_exclusion_list_removes_nothing` — an empty exclusion list removes nothing
- `tests/test_filters.py:224` `test_a_name_inside_the_band_becomes_a_candidate` — a name inside the band becomes a candidate
- `tests/test_filters.py:231` `test_an_unmeasurable_series_is_rejected_ON_MISSING_never_on_value` — K4. The name did not fail the band -- the band could not be evaluated.
- `tests/test_filters.py:254` `test_the_unmeasurable_name_would_otherwise_have_been_a_candidate` — Without the halving-and-back the same shape passes, so the test above
- `tests/test_filters.py:264` `test_a_shallow_decline_is_rejected_on_a_value` — a shallow decline is rejected on a value
- `tests/test_filters.py:273` `test_a_collapse_beyond_the_band_is_rejected_too` — a collapse beyond the band is rejected too
- `tests/test_filters.py:279` `test_both_bounds_are_inclusive_through_the_imported_predicate` — both bounds are inclusive through the imported predicate
- `tests/test_filters.py:286` `test_no_series_is_rejected_on_missing_data_not_on_a_value` — no series is rejected on missing data not on a value
- `tests/test_filters.py:294` `test_a_series_that_starts_after_the_run_date_is_missing_not_failing` — a series that starts after the run date is missing not failing
- `tests/test_filters.py:302` `test_a_stale_series_is_rejected_on_a_value` — a stale series is rejected on a value
- `tests/test_filters.py:310` `test_a_single_close_is_DATA_MISSING_not_a_drawdown_of_zero` — RE-RULED after REVIEW-4 (report B 7.2), and the old name said it all.
- `tests/test_filters.py:332` `test_a_fresh_close_says_nothing_about_how_far_back_the_series_reaches` — RE-RULED after REVIEW-4 (report B 7.2). The old invariant was false.
- `tests/test_filters.py:359` `test_filter1_does_not_know_the_exclusion_list_exists` — Structural: the acceptance test depends on this separation.
- `tests/test_filters.py:378` `test_rsi_and_sma_are_carried_but_never_decide` — rsi and sma are carried but never decide
- `tests/test_filters.py:391` `test_the_band_comes_from_rules_and_is_not_restated` — Not as a number, and not as prose either.
- `tests/test_filters.py:405` `test_the_band_text_tracks_the_constants` — the band text tracks the constants
- `tests/test_filters.py:411` `test_a_rejection_message_quotes_the_live_band` — a rejection message quotes the live band
- `tests/test_filters.py:422` `test_b1_measures_the_share_of_the_decline_in_the_last_180_days` — b1 measures the share of the decline in the last 180 days
- `tests/test_filters.py:429` `test_b1_is_none_when_the_close_is_the_high` — b1 is none when the close is the high
- `tests/test_filters.py:435` `test_b1_is_none_without_an_old_enough_close` — b1 is none without an old enough close
- `tests/test_filters.py:441` `test_b1_can_be_negative_when_the_last_180_days_are_net_up` — SAP's own case in FRAMEWORK-EDITS B1: metric -0.27, gate still PASS.
- `tests/test_filters.py:481` `test_acceptance_filter1_replayed_on_2026_07_27_contains_sap` — THE PHASE 2 ACCEPTANCE TEST.
- `tests/test_filters.py:508` `test_acceptance_is_measured_at_the_replay_date_not_the_snapshot_edge` — Guards the reason the acceptance test could pass falsely.
- `tests/test_filters.py:527` `test_the_chain_removes_sap_because_it_is_held` — The complement: step 0 works, which is why the acceptance test
- `tests/test_filters.py:541` `test_the_committed_exclusion_list_is_well_formed_and_covers_the_book` — the committed exclusion list is well formed and covers the book
- `tests/test_filters.py:549` `test_the_committed_exclusion_list_carries_no_position_figures` — A reason column names the decision and its date, never its price.

**`tests/test_filter2.py`** — filter 2's config and limbs (35 tests)

- `tests/test_filter2.py:69` `test_the_committed_config_matches_what_the_owner_decided` — The three decisions of 2026-08-22, recorded as FRAMEWORK-EDITS E2-E4.
- `tests/test_filter2.py:83` `test_gate_3s_cap_is_recorded_as_the_road_not_taken` — E2 keeps 2.5x visible in the file so the choice stays legible.
- `tests/test_filter2.py:90` `test_no_threshold_is_hardcoded_in_the_module` — Change 2.5 to 3.5 in the config and nothing should recompile.
- `tests/test_filter2.py:99` `test_a_missing_limb_in_the_config_is_fatal` — a missing limb in the config is fatal
- `tests/test_filter2.py:107` `test_a_bad_on_missing_action_is_fatal` — a bad on missing action is fatal
- `tests/test_filter2.py:116` `test_a_missing_config_is_fatal` — a missing config is fatal
- `tests/test_filter2.py:124` `test_positive_free_cash_flow_passes` — positive free cash flow passes
- `tests/test_filter2.py:128` `test_negative_free_cash_flow_fails` — negative free cash flow fails
- `tests/test_filter2.py:132` `test_zero_free_cash_flow_fails_because_positive_means_positive` — zero free cash flow fails because positive means positive
- `tests/test_filter2.py:136` `test_absent_free_cash_flow_is_data_missing_not_a_failure` — absent free cash flow is data missing not a failure
- `tests/test_filter2.py:144` `test_leverage_inside_the_cap_passes` — leverage inside the cap passes
- `tests/test_filter2.py:149` `test_leverage_above_the_cap_fails` — leverage above the cap fails
- `tests/test_filter2.py:154` `test_the_cap_boundary_passes` — the cap boundary passes
- `tests/test_filter2.py:159` `test_the_una_margin_is_not_decided_by_this_filter` — FRAMEWORK-EDITS E2's own case.
- `tests/test_filter2.py:173` `test_net_cash_passes_without_computing_a_ratio` — net cash passes without computing a ratio
- `tests/test_filter2.py:178` `test_a_financial_is_not_applicable_not_failed_and_not_missing` — FRAMEWORK Gate 3 excludes financials. Precedent: FRAMEWORK-EDITS B7.
- `tests/test_filter2.py:185` `test_a_non_financial_without_ebitda_is_data_missing` — a non financial without ebitda is data missing
- `tests/test_filter2.py:190` `test_absent_debt_or_cash_is_data_missing` — absent debt or cash is data missing
- `tests/test_filter2.py:195` `test_non_positive_ebitda_with_net_debt_fails` — non positive ebitda with net debt fails
- `tests/test_filter2.py:200` `test_non_positive_ebitda_with_net_cash_passes` — non positive ebitda with net cash passes
- `tests/test_filter2.py:208` `test_a_rising_revenue_series_passes` — a rising revenue series passes
- `tests/test_filter2.py:212` `test_one_down_year_does_not_flag` — one down year does not flag
- `tests/test_filter2.py:216` `test_two_consecutive_declines_flag` — two consecutive declines flag
- `tests/test_filter2.py:222` `test_the_revenue_limb_never_rejects` — FRAMEWORK 4.2.1 is a hard kill; FRAMEWORK-EDITS B9 makes it a flag here.
- `tests/test_filter2.py:237` `test_too_few_revenue_points_is_data_missing` — too few revenue points is data missing
- `tests/test_filter2.py:245` `test_a_failing_name_is_rejected_on_a_value` — a failing name is rejected on a value
- `tests/test_filter2.py:254` `test_an_untested_name_passes_through_marked_by_default` — DATA MISSING is a third state: not tested is not failed.
- `tests/test_filter2.py:262` `test_rejecting_on_missing_data_is_counted_in_its_own_column` — rejecting on missing data is counted in its own column
- `tests/test_filter2.py:275` `test_a_value_failure_beats_a_missing_limb` — A name that failed one limb is rejected on the value, not on the gap.
- `tests/test_filter2.py:283` `test_a_financial_is_judged_on_its_other_limbs` — a financial is judged on its other limbs
- `tests/test_filter2.py:291` `test_the_limb_matrix_separates_all_five_states` — the limb matrix separates all five states
- `tests/test_filter2.py:305` `test_filter2_sets_no_price_and_no_fair_value` — filter2 sets no price and no fair value
- `tests/test_filter2.py:321` `test_a_never_fetched_ticker_says_so_rather_than_blaming_the_company` — "We did not fetch this" is not "the company reported nothing".
- `tests/test_filter2.py:332` `test_a_reported_gap_is_worded_as_the_company_s` — a reported gap is worded as the company s
- `tests/test_filter2.py:342` `test_the_store_size_is_reported_so_drift_is_visible` — the store size is reported so drift is visible

**`tests/test_ranking.py`** — the E6 key, staleness, share classes, the EV bound, E13 (94 tests)

- `tests/test_ranking.py:101` `test_the_ebit_alias_set_is_ordered_on_MEANING_not_on_coverage` — L3. The as-filed operating income first, the strict EBIT label last:
- `tests/test_ranking.py:111` `test_the_as_filed_label_wins_over_the_strict_ebit_line` — the as filed label wins over the strict ebit line
- `tests/test_ranking.py:119` `test_ebitda_is_never_read_as_ebit` — ebitda is never read as ebit
- `tests/test_ranking.py:138` `test_the_ranking_module_never_names_an_ebitda_field` — FRAMEWORK-EDITS E5 forbids the substitution; this holds the line.
- `tests/test_ranking.py:157` `test_an_absent_line_is_none_never_zero` — an absent line is none never zero
- `tests/test_ranking.py:162` `test_the_quality_lines_are_read_under_their_exact_labels` — E6 chose NO alias set, so a second spelling must NOT be picked up.
- `tests/test_ranking.py:178` `test_no_record_yields_all_none` — no record yields all none
- `tests/test_ranking.py:183` `test_currency_pairs_are_quote_to_reporting` — currency pairs are quote to reporting
- `tests/test_ranking.py:194` `test_two_fiscal_year_ends_in_one_quotient_are_DATA_MISSING` — AUTO.L on the 2026-08-21 run: gross profit from 2024-03-31 against
- `tests/test_ranking.py:202` `test_mixed_periods_are_counted_apart_from_a_missing_line` — 'We have both and they do not belong together' is not 'one is absent'.
- `tests/test_ranking.py:215` `test_the_newest_period_flag_cannot_catch_this_and_the_test_says_so` — SHL.DE is why the guard is here rather than in the staleness check.
- `tests/test_ranking.py:231` `test_matching_periods_pass_and_the_periods_travel_with_the_figures` — matching periods pass and the periods travel with the figures
- `tests/test_ranking.py:238` `test_a_mixed_period_name_keeps_its_earnings_yield_and_its_own_section` — The price leg is one line divided by one quote -- there is nothing in
- `tests/test_ranking.py:248` `test_the_period_question_is_asked_after_the_line_is_known_to_exist` — An absent line has no period to disagree with; reporting it as a
- `tests/test_ranking.py:266` `test_a_stale_record_is_excluded_although_every_leg_would_compute` — That is exactly what makes it dangerous.
- `tests/test_ranking.py:283` `test_a_stale_name_reaches_no_section_of_the_ranking` — a stale name reaches no section of the ranking
- `tests/test_ranking.py:292` `test_stale_is_a_rejection_ON_VALUE_never_on_missing` — Figures we HAVE, judged too old -- the same shape prices.py gives a
- `tests/test_ranking.py:303` `test_stale_is_never_folded_into_unrankable` — 'We chose not to use them' is not 'they were not there'.
- `tests/test_ranking.py:312` `test_staleness_outranks_the_sector_exemption_and_the_missing_line` — Whichever other gap it also has, the reason reported is the oldest one:
- `tests/test_ranking.py:320` `test_the_reason_counts_carry_the_stale_bucket` — the reason counts carry the stale bucket
- `tests/test_ranking.py:329` `test_gross_profitability_is_gross_profit_over_total_assets` — gross profitability is gross profit over total assets
- `tests/test_ranking.py:335` `test_the_quality_leg_never_reads_ebit` — E6's numerator is gross profit. EBIT belongs to the price leg alone.
- `tests/test_ranking.py:350` `test_earnings_yield_is_ebit_over_enterprise_value` — earnings yield is ebit over enterprise value
- `tests/test_ranking.py:355` `test_a_sector_exempt_name_gets_no_quality_leg_but_keeps_its_yield` — E6 kept E3/E5's exemption on the ECONOMIC ground, not the mechanical one.
- `tests/test_ranking.py:369` `test_utilities_are_not_exempt` — Greenblatt excludes them; E6 did not import the exclusion without the
- `tests/test_ranking.py:376` `test_a_non_positive_denominator_is_not_meaningful_never_clamped` — a non positive denominator is not meaningful never clamped
- `tests/test_ranking.py:382` `test_a_zero_denominator_is_not_meaningful` — a zero denominator is not meaningful
- `tests/test_ranking.py:387` `test_a_negative_gross_profit_is_RANKED_not_excluded` — The distinction E6 turns on: a negative NUMERATOR is a fact about the
- `tests/test_ranking.py:401` `test_a_missing_input_is_distinguished_from_the_sector_exemption` — a missing input is distinguished from the sector exemption
- `tests/test_ranking.py:409` `test_negative_ebit_gives_a_negative_yield_and_ranks_last` — negative ebit gives a negative yield and ranks last
- `tests/test_ranking.py:417` `test_enterprise_value_is_converted_into_the_reporting_currency` — enterprise value is converted into the reporting currency
- `tests/test_ranking.py:426` `test_a_pence_quoted_name_is_not_divided_by_a_hundred` — The bug that does the most damage and shows the least.
- `tests/test_ranking.py:441` `test_a_missing_rate_blocks_the_yield_rather_than_assuming_parity` — a missing rate blocks the yield rather than assuming parity
- `tests/test_ranking.py:447` `test_a_missing_enterprise_value_blocks_the_yield` — a missing enterprise value blocks the yield
- `tests/test_ranking.py:455` `test_competition_ranking_shares_the_better_rank` — competition ranking shares the better rank
- `tests/test_ranking.py:459` `test_highest_value_is_rank_one` — highest value is rank one
- `tests/test_ranking.py:463` `test_the_two_placings_are_summed_and_sorted_ascending` — B wins both legs, C loses both, A is in between -- no tie to resolve.
- `tests/test_ranking.py:478` `test_an_equal_sum_breaks_alphabetically` — an equal sum breaks alphabetically
- `tests/test_ranking.py:489` `test_one_legged_names_go_to_their_own_section_never_interleaved` — one legged names go to their own section never interleaved
- `tests/test_ranking.py:501` `test_the_yield_only_section_is_ranked_on_its_own_yields` — the yield only section is ranked on its own yields
- `tests/test_ranking.py:511` `test_a_name_with_neither_component_is_unrankable_and_named` — a name with neither component is unrankable and named
- `tests/test_ranking.py:518` `test_the_reason_counts_keep_the_three_causes_apart` — the reason counts keep the three causes apart
- `tests/test_ranking.py:533` `test_the_ranking_sets_no_price_and_no_fair_value` — Checked on the code, not the prose: the docstring must be able to say
- `tests/test_ranking.py:575` `test_two_share_classes_are_identified_by_identical_accounts` — two share classes are identified by identical accounts
- `tests/test_ranking.py:597` `test_identity_is_not_a_ticker_string_guess` — EQT (US gas) and EQT.ST (Swedish private equity) share a stem and are
- `tests/test_ranking.py:612` `test_a_partial_fingerprint_never_matches` — An absent line must not make two companies look alike.
- `tests/test_ranking.py:627` `test_a_different_sector_or_currency_breaks_the_group` — a different sector or currency breaks the group
- `tests/test_ranking.py:635` `test_without_turnover_the_fallback_says_so` — without turnover the fallback says so
- `tests/test_ranking.py:648` `test_a_lone_listing_is_untouched` — a lone listing is untouched
- `tests/test_ranking.py:668` `test_turnover_is_close_times_volume_in_the_target_currency` — turnover is close times volume in the target currency
- `tests/test_ranking.py:677` `test_a_pence_quoted_series_is_divided_to_pounds_first` — Without the divisor a London line looks a hundred times the size it is
- `tests/test_ranking.py:688` `test_a_missing_rate_yields_no_turnover_rather_than_a_wrong_one` — a missing rate yields no turnover rather than a wrong one
- `tests/test_ranking.py:696` `test_turnover_ignores_sessions_outside_the_window` — turnover ignores sessions outside the window
- `tests/test_ranking.py:705` `test_an_empty_series_has_no_turnover` — an empty series has no turnover
- `tests/test_ranking.py:732` `test_an_enterprise_value_implying_more_net_cash_than_assets_loses_its_yield` — LISP.SW's shape: EV far below market cap on a small balance sheet.
- `tests/test_ranking.py:742` `test_a_refused_enterprise_value_keeps_its_quality_leg_and_records_the_figure` — The bound judges one quoted number, not the business -- and the number
- `tests/test_ranking.py:753` `test_net_cash_exactly_equal_to_total_assets_still_passes` — The bound is generous BY CONSTRUCTION and is not a tolerance: it fires
- `tests/test_ranking.py:761` `test_net_debt_never_trips_the_bound` — An enterprise value ABOVE the market cap implies net debt. Wrong in
- `tests/test_ranking.py:769` `test_the_bound_compares_in_ONE_currency` — PLUS.L's shape, and the reason the review's own count was one short.
- `tests/test_ranking.py:787` `test_a_missing_market_cap_asks_no_question_rather_than_answering_one` — DATA MISSING is a third state here too: with nothing to bound against,
- `tests/test_ranking.py:795` `test_a_missing_total_assets_asks_no_question_either` — a missing total assets asks no question either
- `tests/test_ranking.py:801` `test_a_refused_yield_is_counted_on_MISSING_data_never_on_value` — The owner's binding condition on this check, executed.
- `tests/test_ranking.py:839` `test_a_key_read_entirely_from_old_rows_is_stale_although_the_record_is_OK` — a key read entirely from old rows is stale although the record is OK
- `tests/test_ranking.py:853` `test_two_names_of_the_same_age_are_treated_the_same_way` — The whole of L4 in one assertion. Before the fix one was ranked and the
- `tests/test_ranking.py:868` `test_a_one_legged_name_is_judged_on_the_one_row_it_was_ranked_on` — ERIE's shape: sector exempt, so only EBIT is read -- and its newest EBIT
- `tests/test_ranking.py:878` `test_a_quality_leg_the_exemption_never_evaluated_does_not_make_a_name_stale` — The mirror of the test above: a bank whose EBIT is current is not
- `tests/test_ranking.py:888` `test_the_gate_does_not_swallow_the_mixed_period_finding` — AUTO.L's shape. Two year-ends in one quotient is a statement about the
- `tests/test_ranking.py:898` `test_an_old_row_the_key_never_reads_does_not_make_a_name_stale` — The other direction of the same rule: a fresh key with a stale
- `tests/test_ranking.py:908` `test_rank_candidates_will_not_rank_without_a_run_date` — No default: a caller that drops the run date gets an error, not a
- `tests/test_ranking.py:915` `test_the_limit_is_the_one_fundamentals_uses_and_is_not_restated` — One number, one place. A second copy is how two gates drift apart.
- `tests/test_ranking.py:928` `test_the_stale_note_is_measured_not_asserted` — The sentence carries the date and the age, so the report names both.
- `tests/test_ranking.py:942` `test_the_year_is_settled_before_the_label` — The preferred label is two years older; the fallback is current.
- `tests/test_ranking.py:959` `test_meaning_still_decides_within_the_newest_year` — meaning still decides within the newest year
- `tests/test_ranking.py:969` `test_the_strict_label_is_used_when_it_is_the_only_one_for_the_newest_year` — The reorder is a preference, not an exclusion: coverage becomes a
- `tests/test_ranking.py:976` `test_two_labels_that_are_one_figure_in_two_units_are_DATA_MISSING` — MONC.MI's shape, to the digit.
- `tests/test_ranking.py:991` `test_the_unit_conflict_is_not_resolved_by_preferring_the_larger_figure` — Revenue would tell us which unit is meant. Inferring it is a choice,
- `tests/test_ranking.py:1004` `test_an_ordinary_economic_gap_between_two_labels_is_not_a_unit_slip` — IP carries EBIT -2,817M against Operating Income -10M -- 281.7x, the
- `tests/test_ranking.py:1017` `test_the_unit_check_only_compares_figures_from_one_year_end` — Two labels a thousand apart in DIFFERENT years are not one figure in
- `tests/test_ranking.py:1041` `test_is_unit_slip_on_the_cases_that_define_it` — is unit slip on the cases that define it
- `tests/test_ranking.py:1047` `test_the_unit_tolerance_is_stated_and_the_answer_does_not_depend_on_it` — the unit tolerance is stated and the answer does not depend on it
- `tests/test_ranking.py:1059` `test_a_single_currency_group_is_decided_without_any_rate` — Six of the eight groups on 2026-08-21 are two Stockholm lines of one
- `tests/test_ranking.py:1078` `test_the_alphabetical_fallback_would_have_reversed_that_contest` — The direction of the fallback, executed. For a Nordic A/B pair the A
- `tests/test_ranking.py:1097` `test_a_cross_currency_group_still_needs_a_rate_and_says_so` — AZN.L against AZN.ST, NOKIA.HE against NOKIA-SEK.ST. Two of eight.
- `tests/test_ranking.py:1122` `test_a_pence_line_is_divided_before_it_is_compared_with_a_pound_one` — Same major unit, different quote unit -- no rate needed, but the minor
- `tests/test_ranking.py:1139` `test_median_turnover_major_applies_no_rate_and_still_divides_the_minor_unit` — median turnover major applies no rate and still divides the minor unit
- `tests/test_ranking.py:1182` `test_four_consecutive_quarters_are_summed_and_the_stock_line_is_not` — four consecutive quarters are summed and the stock line is not
- `tests/test_ranking.py:1191` `test_an_annual_figure_is_taken_as_it_stands_and_nothing_is_summed` — Nothing is derived that does not need to be. The vendor path is here.
- `tests/test_ranking.py:1198` `test_a_gap_in_the_four_quarters_is_input_missing` — `2025-Q2, 2025-Q4, 2026-Q1, 2026-Q2` overlaps nothing and is not four
- `tests/test_ranking.py:1209` `test_a_flow_line_of_unrecorded_length_is_not_meaningful` — E13: never ranked on an ASSUMED basis. Distinct from an absent line.
- `tests/test_ranking.py:1218` `test_not_meaningful_is_counted_apart_from_an_absent_line` — not meaningful is counted apart from an absent line
- `tests/test_ranking.py:1225` `test_a_half_yearly_series_is_not_ranked_and_says_why` — E13 taken literally: a half-yearly reporter has no quarters, so it has
- `tests/test_ranking.py:1237` `test_staleness_is_measured_on_the_end_of_the_window` — A trailing twelve months is as old as the day it STOPS. Its oldest
- `tests/test_ranking.py:1246` `test_the_ranking_csv_names_the_basis_and_the_periods_summed` — the ranking csv names the basis and the periods summed
- `tests/test_ranking.py:1256` `test_an_annual_row_names_its_basis_and_summs_nothing` — an annual row names its basis and summs nothing

**`tests/test_ranking_acceptance.py`** — the frozen 2026-08-21 run, pinned head and sections (23 tests)

- `tests/test_ranking_acceptance.py:117` `test_the_frozen_candidate_set_is_the_one_the_run_ranked` — the frozen candidate set is the one the run ranked
- `tests/test_ranking_acceptance.py:126` `test_the_fixture_carries_the_alias_alternatives_and_the_forbidden_line` — Otherwise a swap in EBIT_ALIASES would change nothing here and this
- `tests/test_ranking_acceptance.py:210` `test_the_top_five_is_what_it_was` — The names phase 6 would enter as PIPELINE. This is the whole point.
- `tests/test_ranking_acceptance.py:215` `test_every_placing_and_both_ratios_in_the_top_five` — The names alone would survive a change that moved every number.
- `tests/test_ranking_acceptance.py:231` `test_the_top_twenty_is_what_it_was` — Places 13 and 14 share a sum of 88, and 18, 19 and 20 share 115 -- all
- `tests/test_ranking_acceptance.py:242` `test_the_sections_are_the_sizes_they_were` — the sections are the sizes they were
- `tests/test_ranking_acceptance.py:249` `test_every_reason_a_candidate_has_no_quality_leg_is_the_count_it_was` — every reason a candidate has no quality leg is the count it was
- `tests/test_ranking_acceptance.py:253` `test_the_stale_names_are_the_ones_whose_own_ranked_lines_are_too_old` — Three the record-level flag caught, two the key-level gate caught (L4).
- `tests/test_ranking_acceptance.py:271` `test_the_stale_gate_does_not_swallow_the_mixed_period_finding` — AUTO.L's gross profit is from 2024-03-31, 873 days before the run, and
- `tests/test_ranking_acceptance.py:280` `test_the_two_mixed_period_names_are_the_two_that_were_mixed` — the two mixed period names are the two that were mixed
- `tests/test_ranking_acceptance.py:289` `test_putting_the_strict_ebit_label_back_in_front_changes_this_answer` — The regression, executed rather than asserted -- now in the direction
- `tests/test_ranking_acceptance.py:326` `test_the_alias_is_chosen_at_the_newest_year_end_any_label_reports` — L3 part two, and the reason a blind reorder was not the fix.
- `tests/test_ranking_acceptance.py:345` `test_the_first_label_would_have_been_years_older_for_those_names` — Otherwise the test above proves nothing about the rule.
- `tests/test_ranking_acceptance.py:355` `test_one_figure_in_two_units_is_DATA_MISSING_and_says_so` — MONC.MI: Operating Income 913,356,000 and Total Operating Income As
- `tests/test_ranking_acceptance.py:371` `test_the_unit_check_fires_on_this_one_name_and_no_other` — The measured claim behind UNIT_TOLERANCE: over every pairwise alias
- `tests/test_ranking_acceptance.py:380` `test_the_unit_check_does_not_move_with_its_tolerance` — If the answer depended on the tolerance, the tolerance would be a
- `tests/test_ranking_acceptance.py:410` `test_substituting_ebitda_for_ebit_changes_the_top_five` — E5 forbade it and an AST test stops the module NAMING the field. This
- `tests/test_ranking_acceptance.py:421` `test_reading_total_revenue_where_gross_profit_belongs_changes_it` — The quality leg's numerator, mis-picked from the line above it.
- `tests/test_ranking_acceptance.py:431` `test_reading_current_assets_where_total_assets_belongs_changes_it` — A mis-picked balance post, executed the same way.
- `tests/test_ranking_acceptance.py:441` `test_a_missing_exchange_rate_does_not_silently_become_parity` — Held here as well as in test_fx, because here it would move the answer.
- `tests/test_ranking_acceptance.py:454` `test_the_names_whose_enterprise_value_is_impossible_lose_their_yield` — L2, executed on the real 394 rather than on a hand-built record.
- `tests/test_ranking_acceptance.py:479` `test_the_enterprise_value_bound_rejects_on_missing_data_never_on_value` — The column it lands in is the whole of the owner's condition on it.
- `tests/test_ranking_acceptance.py:491` `test_lifting_the_enterprise_value_bound_puts_lisp_sw_back_in_the_top_twenty` — The cost of the check, executed rather than asserted.

**`tests/test_prices.py`** — batching, backoff, statuses, truncation (24 tests)

- `tests/test_prices.py:64` `test_batches_preserve_order_and_lose_nothing` — batches preserve order and lose nothing
- `tests/test_prices.py:71` `test_batch_size_must_be_positive` — batch size must be positive
- `tests/test_prices.py:76` `test_fetch_universe_batches_the_request` — fetch universe batches the request
- `tests/test_prices.py:93` `test_backoff_is_exponential_and_capped` — backoff is exponential and capped
- `tests/test_prices.py:100` `test_backoff_rejects_a_zero_attempt` — backoff rejects a zero attempt
- `tests/test_prices.py:105` `test_a_failing_batch_is_retried_with_growing_delays` — a failing batch is retried with growing delays
- `tests/test_prices.py:123` `test_retries_stop_at_max_attempts` — retries stop at max attempts
- `tests/test_prices.py:144` `test_throttling_is_recognised` — throttling is recognised
- `tests/test_prices.py:148` `test_a_plain_failure_is_not_throttling` — a plain failure is not throttling
- `tests/test_prices.py:152` `test_throttled_and_no_data_are_never_merged` — throttled and no data are never merged
- `tests/test_prices.py:164` `test_a_ticker_missing_from_a_good_response_is_no_data_not_dropped` — a ticker missing from a good response is no data not dropped
- `tests/test_prices.py:172` `test_every_requested_ticker_gets_exactly_one_status` — every requested ticker gets exactly one status
- `tests/test_prices.py:180` `test_an_old_series_is_stale_and_that_is_a_value_rejection` — an old series is stale and that is a value rejection
- `tests/test_prices.py:191` `test_a_weekend_run_on_fridays_close_is_not_stale` — a weekend run on fridays close is not stale
- `tests/test_prices.py:198` `test_missing_data_statuses_are_counted_apart_from_stale` — missing data statuses are counted apart from stale
- `tests/test_prices.py:207` `test_status_counts_covers_all_four` — status counts covers all four
- `tests/test_prices.py:213` `test_coverage_by_market_splits_by_market` — coverage by market splits by market
- `tests/test_prices.py:225` `test_truncate_drops_rows_after_asof` — truncate drops rows after asof
- `tests/test_prices.py:232` `test_a_series_entirely_after_asof_is_no_data_and_leaves_no_frame` — a series entirely after asof is no data and leaves no frame
- `tests/test_prices.py:240` `test_asof_truncation_reaches_the_stored_frame` — asof truncation reaches the stored frame
- `tests/test_prices.py:250` `test_split_frame_handles_a_single_ticker_flat_frame` — split frame handles a single ticker flat frame
- `tests/test_prices.py:255` `test_split_frame_ignores_an_empty_response` — split frame ignores an empty response
- `tests/test_prices.py:260` `test_split_frame_drops_a_session_with_no_close` — split frame drops a session with no close
- `tests/test_prices.py:268` `test_an_all_nan_block_counts_as_absent` — an all nan block counts as absent

**`tests/test_snapshot.py`** — the snapshot store and its reproducibility checks (14 tests)

- `tests/test_snapshot.py:93` `test_snapshot_path_is_dated` — snapshot path is dated
- `tests/test_snapshot.py:97` `test_every_table_is_written` — every table is written
- `tests/test_snapshot.py:114` `test_manifest_records_what_a_replay_needs` — manifest records what a replay needs
- `tests/test_snapshot.py:125` `test_raw_ohlcv_is_stored_not_computed_metrics` — raw ohlcv is stored not computed metrics
- `tests/test_snapshot.py:134` `test_a_stored_series_can_be_read_back_and_measured` — a stored series can be read back and measured
- `tests/test_snapshot.py:144` `test_metrics_match_between_the_live_frame_and_the_snapshot` — metrics match between the live frame and the snapshot
- `tests/test_snapshot.py:156` `test_fetch_status_round_trips` — fetch status round trips
- `tests/test_snapshot.py:164` `test_rewriting_a_date_replaces_rather_than_appends` — rewriting a date replaces rather than appends
- `tests/test_snapshot.py:176` `test_a_fresh_snapshot_verifies_clean` — a fresh snapshot verifies clean
- `tests/test_snapshot.py:181` `test_an_edited_universe_file_is_caught` — an edited universe file is caught
- `tests/test_snapshot.py:189` `test_a_deleted_universe_file_is_caught` — a deleted universe file is caught
- `tests/test_snapshot.py:195` `test_a_close_after_asof_is_caught` — a close after asof is caught
- `tests/test_snapshot.py:205` `test_reading_a_snapshot_that_is_not_there` — reading a snapshot that is not there
- `tests/test_snapshot.py:210` `test_nan_prices_are_stored_as_null_not_as_a_number` — nan prices are stored as null not as a number

**`tests/test_fundamentals.py`** — the fundamentals fetch, both status layers, the store (26 tests)

- `tests/test_fundamentals.py:62` `test_every_requested_field_gets_a_status` — every requested field gets a status
- `tests/test_fundamentals.py:68` `test_a_missing_field_is_no_data_not_zero` — a missing field is no data not zero
- `tests/test_fundamentals.py:76` `test_a_none_field_is_no_data` — a none field is no data
- `tests/test_fundamentals.py:81` `test_a_non_numeric_value_does_not_become_a_number` — a non numeric value does not become a number
- `tests/test_fundamentals.py:86` `test_a_nan_is_no_data` — a nan is no data
- `tests/test_fundamentals.py:91` `test_series_extraction_keeps_period_ends` — series extraction keeps period ends
- `tests/test_fundamentals.py:98` `test_an_empty_statement_yields_no_series` — an empty statement yields no series
- `tests/test_fundamentals.py:106` `test_a_good_ticker_comes_back_ok_with_both_layers` — a good ticker comes back ok with both layers
- `tests/test_fundamentals.py:115` `test_a_bank_is_ok_at_ticker_level_and_missing_at_field_level` — The reason the two layers exist.
- `tests/test_fundamentals.py:129` `test_throttling_is_distinguished_from_absence` — throttling is distinguished from absence
- `tests/test_fundamentals.py:140` `test_a_failed_ticker_still_reports_every_field` — a failed ticker still reports every field
- `tests/test_fundamentals.py:146` `test_retry_and_backoff_fire_with_growing_delays` — retry and backoff fire with growing delays
- `tests/test_fundamentals.py:161` `test_an_empty_response_is_no_data` — an empty response is no data
- `tests/test_fundamentals.py:167` `test_an_old_newest_period_is_stale_and_counted_on_value` — an old newest period is stale and counted on value
- `tests/test_fundamentals.py:176` `test_no_fundamentals_is_counted_on_missing` — no fundamentals is counted on missing
- `tests/test_fundamentals.py:183` `test_fetch_many_visits_every_ticker_once_and_counts_requests` — fetch many visits every ticker once and counts requests
- `tests/test_fundamentals.py:197` `test_fetch_many_pauses_between_tickers_but_not_after_the_last` — fetch many pauses between tickers but not after the last
- `tests/test_fundamentals.py:207` `test_field_coverage_counts_per_field_not_per_ticker` — field coverage counts per field not per ticker
- `tests/test_fundamentals.py:218` `test_status_counts_covers_all_four` — status counts covers all four
- `tests/test_fundamentals.py:223` `test_series_coverage_is_a_histogram` — series coverage is a histogram
- `tests/test_fundamentals.py:240` `test_the_store_lives_beside_the_price_snapshot_not_inside_it` — the store lives beside the price snapshot not inside it
- `tests/test_fundamentals.py:248` `test_records_round_trip` — records round trip
- `tests/test_fundamentals.py:260` `test_field_statuses_survive_the_round_trip` — field statuses survive the round trip
- `tests/test_fundamentals.py:270` `test_the_manifest_records_both_dates` — The look-ahead warning is written from these two.
- `tests/test_fundamentals.py:280` `test_rewriting_replaces_rather_than_appends` — rewriting replaces rather than appends
- `tests/test_fundamentals.py:290` `test_reading_a_store_that_is_not_there` — reading a store that is not there

**`tests/test_fx.py`** — minor units, rates, manifests, replay (31 tests)

- `tests/test_fx.py:29` `test_gbp_pence_resolves_to_pounds` — gbp pence resolves to pounds
- `tests/test_fx.py:34` `test_pounds_stay_pounds` — pounds stay pounds
- `tests/test_fx.py:38` `test_the_mapping_is_case_sensitive_because_the_codes_are` — "GBp" and "GBP" are different codes meaning different units.
- `tests/test_fx.py:44` `test_other_minor_units_resolve_too` — other minor units resolve too
- `tests/test_fx.py:49` `test_an_ordinary_currency_is_returned_unchanged` — an ordinary currency is returned unchanged
- `tests/test_fx.py:54` `test_whitespace_does_not_defeat_the_mapping` — whitespace does not defeat the mapping
- `tests/test_fx.py:58` `test_no_currency_is_none_not_a_guess` — no currency is none not a guess
- `tests/test_fx.py:63` `test_a_pence_quoted_name_needs_no_conversion_against_pounds` — The whole point: GBp and GBP are the same currency, not a 100x pair.
- `tests/test_fx.py:72` `test_a_pence_to_dollars_pair_is_fetched_as_pounds_to_dollars` — a pence to dollars pair is fetched as pounds to dollars
- `tests/test_fx.py:84` `test_pence_and_pounds_collapse_to_one_fetch` — pence and pounds collapse to one fetch
- `tests/test_fx.py:91` `test_identity_pairs_are_never_fetched` — identity pairs are never fetched
- `tests/test_fx.py:95` `test_pairs_are_deduplicated_and_sorted` — pairs are deduplicated and sorted
- `tests/test_fx.py:100` `test_a_pair_with_a_missing_side_is_dropped` — a pair with a missing side is dropped
- `tests/test_fx.py:104` `test_a_fetched_rate_carries_its_date_and_source` — a fetched rate carries its date and source
- `tests/test_fx.py:113` `test_conversion_applies_the_rate` — conversion applies the rate
- `tests/test_fx.py:118` `test_a_failed_pair_is_recorded_and_never_becomes_parity` — A missing rate treated as 1.0 is an error the size of the rate.
- `tests/test_fx.py:128` `test_a_non_positive_rate_is_refused` — a non positive rate is refused
- `tests/test_fx.py:134` `test_the_manifest_carries_every_rate_and_every_failure` — the manifest carries every rate and every failure
- `tests/test_fx.py:146` `test_describe_reports_rates_and_failures` — describe reports rates and failures
- `tests/test_fx.py:162` `test_pence_is_written_as_gbx_not_gbp` — pence is written as gbx not gbp
- `tests/test_fx.py:167` `test_the_safe_code_is_a_fixed_point_under_upper` — the safe code is a fixed point under upper
- `tests/test_fx.py:173` `test_the_safe_code_never_promotes_a_minor_unit_to_its_major` — The whole point: GBp must not become GBP by any route.
- `tests/test_fx.py:181` `test_an_ordinary_code_is_simply_upper_cased` — an ordinary code is simply upper cased
- `tests/test_fx.py:186` `test_no_currency_stays_none` — no currency stays none
- `tests/test_fx.py:211` `test_a_stored_run_can_be_replayed_rate_for_rate` — a stored run can be replayed rate for rate
- `tests/test_fx.py:221` `test_the_replayed_rate_keeps_its_OWN_date_not_the_replay_date` — The 2026-08-21 run carries two pairs dated 08-22. Stamping the replay
- `tests/test_fx.py:233` `test_a_pair_the_manifest_lacks_FAILS_and_is_never_quietly_fetched` — A reproduction that is partly a new run is neither.
- `tests/test_fx.py:245` `test_the_replayed_source_says_it_was_replayed` — A report that could not tell a replay from a fetch would let one be
- `tests/test_fx.py:254` `test_the_default_lookup_takes_the_LATEST_close_whatever_asof_says` — Checked on the source, because the behaviour is a network call.
- `tests/test_fx.py:277` `test_a_manifest_says_which_day_its_rates_belong_to` — a manifest says which day its rates belong to
- `tests/test_fx.py:288` `test_a_manifest_without_the_field_answers_None_not_a_guess` — a manifest without the field answers None not a guess

**`tests/test_fetch_fx_manifest.py`** — tools/fetch_fx_manifest.py (6 tests)

- `tests/test_fetch_fx_manifest.py:43` `test_the_weekend_row_is_not_what_gets_recorded` — The whole fault, in one assertion: the LAST close is 08-23's.
- `tests/test_fetch_fx_manifest.py:51` `test_a_pair_with_no_row_on_the_date_fails_and_says_what_it_saw` — a pair with no row on the date fails and says what it saw
- `tests/test_fetch_fx_manifest.py:60` `test_a_pair_the_feed_does_not_know_fails_rather_than_returning_something` — a pair the feed does not know fails rather than returning something
- `tests/test_fetch_fx_manifest.py:65` `test_the_pair_list_comes_from_a_stored_manifest_and_nowhere_else` — the pair list comes from a stored manifest and nowhere else
- `tests/test_fetch_fx_manifest.py:72` `test_the_written_manifest_replays_through_the_real_reader` — It is only useful if ``vss.fx`` can read it back, so read it back.
- `tests/test_fetch_fx_manifest.py:89` `test_a_failed_pair_is_named_in_the_file_and_the_exit_code_says_so` — a failed pair is named in the file and the exit code says so

**`tests/test_pipeline.py`** — PIPELINE writing (23 tests)

- `tests/test_pipeline.py:52` `test_the_summary_is_measured_and_carries_no_assessment` — the summary is measured and carries no assessment
- `tests/test_pipeline.py:67` `test_the_summary_names_the_minor_unit_when_there_is_one` — the summary names the minor unit when there is one
- `tests/test_pipeline.py:75` `test_a_pence_quoted_entry_stores_gbx_so_the_report_cannot_say_gbp` — A pence figure labelled GBP invites a hundredfold error on a stop.
- `tests/test_pipeline.py:101` `test_an_ordinary_currency_adds_no_unit_note` — an ordinary currency adds no unit note
- `tests/test_pipeline.py:108` `test_a_missing_figure_says_data_missing_rather_than_nothing` — a missing figure says data missing rather than nothing
- `tests/test_pipeline.py:115` `test_the_summary_states_that_section_5_has_not_been_run` — the summary states that section 5 has not been run
- `tests/test_pipeline.py:122` `test_no_width_of_figures_can_fold_the_note_into_a_pseudo_key` — The note is a FOLDED scalar, so the wrap points move with the numbers.
- `tests/test_pipeline.py:161` `test_an_entry_is_pipeline_and_nothing_else` — an entry is pipeline and nothing else
- `tests/test_pipeline.py:168` `test_a_name_with_yaml_punctuation_is_quoted` — a name with yaml punctuation is quoted
- `tests/test_pipeline.py:176` `test_a_write_appends_and_preserves_every_earlier_byte` — a write appends and preserves every earlier byte
- `tests/test_pipeline.py:187` `test_the_file_is_backed_up_before_a_byte_is_written` — the file is backed up before a byte is written
- `tests/test_pipeline.py:195` `test_an_existing_ticker_is_never_touched` — an existing ticker is never touched
- `tests/test_pipeline.py:203` `test_a_duplicate_inside_one_batch_is_written_once` — a duplicate inside one batch is written once
- `tests/test_pipeline.py:210` `test_the_written_file_still_loads` — the written file still loads
- `tests/test_pipeline.py:221` `test_the_written_entry_has_no_computed_buy_price` — the written entry has no computed buy price
- `tests/test_pipeline.py:230` `test_a_write_that_breaks_the_file_is_rolled_back` — a write that breaks the file is rolled back
- `tests/test_pipeline.py:241` `test_a_dry_run_writes_nothing_and_makes_no_backup` — a dry run writes nothing and makes no backup
- `tests/test_pipeline.py:249` `test_writing_nothing_makes_no_backup` — writing nothing makes no backup
- `tests/test_pipeline.py:256` `test_a_missing_watchlist_is_an_error` — a missing watchlist is an error
- `tests/test_pipeline.py:261` `test_existing_tickers_are_read_without_parsing_yaml` — existing tickers are read without parsing yaml
- `tests/test_pipeline.py:265` `test_the_backup_name_carries_the_date` — the backup name carries the date
- `tests/test_pipeline.py:293` `test_only_the_top_n_of_the_both_legs_list_are_taken` — only the top n of the both legs list are taken
- `tests/test_pipeline.py:302` `test_the_rank_in_the_note_is_the_position_in_that_list` — the rank in the note is the position in that list

**`tests/test_series_sanity.py`** — K4 (15 tests)

- `tests/test_series_sanity.py:55` `test_the_mnst_series_that_fooled_the_screener_is_refused` — The case K4 exists for, on the rows that produced it.
- `tests/test_series_sanity.py:85` `test_a_real_repricing_that_the_tape_confirms_is_NOT_refused` — MRNA closed +177% on 2026-08-19, on 23.8x its own median volume.
- `tests/test_series_sanity.py:101` `test_a_spin_off_day_is_refused_as_uncorroborated_not_as_a_scale_switch` — ELUX-A.ST fell 48% on 2026-05-19 on 0.2x its median volume.
- `tests/test_series_sanity.py:121` `test_a_split_that_stays_split_is_not_a_scale_switch` — A corporate action happens once. Halving and STAYING halved is a
- `tests/test_series_sanity.py:130` `test_halving_and_coming_back_is_a_scale_switch` — halving and coming back is a scale switch
- `tests/test_series_sanity.py:136` `test_a_round_trip_of_ordinary_volatility_is_not_a_scale_switch` — Up 30% and back down 23% is a small cap having a week, not two scales.
- `tests/test_series_sanity.py:146` `test_the_two_halves_must_point_in_opposite_directions` — Two doublings are a name that quadrupled, not a series that flipped.
- `tests/test_series_sanity.py:154` `test_a_return_trip_outside_the_window_is_not_paired` — a return trip outside the window is not paired
- `tests/test_series_sanity.py:166` `test_a_big_move_the_volume_confirms_passes` — a big move the volume confirms passes
- `tests/test_series_sanity.py:173` `test_the_same_move_one_notch_below_the_volume_bar_is_refused` — The threshold is a threshold, and the test says which side is which.
- `tests/test_series_sanity.py:182` `test_a_missing_volume_is_absence_of_corroboration_never_corroboration` — a missing volume is absence of corroboration never corroboration
- `tests/test_series_sanity.py:191` `test_a_move_just_inside_the_jump_factor_is_not_examined_at_all` — Below the factor the volume is never consulted: an ordinary session on
- `tests/test_series_sanity.py:201` `test_a_series_too_short_to_hold_a_median_gets_no_verdict` — Silence, not a verdict. A series this short has no 52-week high worth
- `tests/test_series_sanity.py:208` `test_a_break_older_than_the_window_is_not_examined` — The check reads the window the drawdown reads. Refusing a name for a
- `tests/test_series_sanity.py:216` `test_an_empty_frame_is_not_a_finding` — an empty frame is not a finding

**`tests/test_metrics.py`** — the metrics the screener reads (only the 52-week, truncation and settlement tests are screener-relevant; all listed) (37 tests)

- `tests/test_metrics.py:33` `test_rsi_exactly_30` — 6 gains of +1 vs 8 losses of -1.75 gives avg_gain/avg_loss = 3/7 -> RSI 30.
- `tests/test_metrics.py:39` `test_rsi_exactly_70` — 8 gains of +1.75 vs 6 losses of -1 gives avg_gain/avg_loss = 7/3 -> RSI 70.
- `tests/test_metrics.py:45` `test_rsi_needs_15_closes` — rsi needs 15 closes
- `tests/test_metrics.py:52` `test_rsi_all_gains_is_100` — rsi all gains is 100
- `tests/test_metrics.py:56` `test_rsi_all_losses_is_0` — rsi all losses is 0
- `tests/test_metrics.py:60` `test_rsi_uses_wilder_not_simple_mean` — With more than 15 closes the smoothing must diverge from a simple mean.
- `tests/test_metrics.py:73` `test_sma_is_mean_of_trailing_window` — sma is mean of trailing window
- `tests/test_metrics.py:78` `test_sma_insufficient_history_is_none_never_shorter_window` — sma insufficient history is none never shorter window
- `tests/test_metrics.py:84` `test_compute_reports_sma_data_missing_on_short_history` — compute reports sma data missing on short history
- `tests/test_metrics.py:94` `test_high_52w_uses_closing_high_within_window` — high 52w uses closing high within window
- `tests/test_metrics.py:100` `test_high_52w_excludes_closes_older_than_365_days` — high 52w excludes closes older than 365 days
- `tests/test_metrics.py:107` `test_drawdown_is_positive_fraction` — drawdown is positive fraction
- `tests/test_metrics.py:112` `test_drawdown_exactly_15_and_50_percent` — drawdown exactly 15 and 50 percent
- `tests/test_metrics.py:117` `test_drawdown_missing_inputs` — drawdown missing inputs
- `tests/test_metrics.py:126` `test_pct_distance_sign` — pct distance sign
- `tests/test_metrics.py:132` `test_pct_distance_missing_inputs` — pct distance missing inputs
- `tests/test_metrics.py:141` `test_avg_volume_excludes_today` — avg volume excludes today
- `tests/test_metrics.py:146` `test_avg_volume_needs_21_sessions` — avg volume needs 21 sessions
- `tests/test_metrics.py:151` `test_volume_ratio` — volume ratio
- `tests/test_metrics.py:161` `test_compute_full_frame` — compute full frame
- `tests/test_metrics.py:175` `test_compute_empty_frame_is_all_data_missing` — compute empty frame is all data missing
- `tests/test_metrics.py:197` `test_truncate_drops_rows_after_as_of` — truncate drops rows after as of
- `tests/test_metrics.py:204` `test_truncate_leaves_an_earlier_series_alone` — truncate leaves an earlier series alone
- `tests/test_metrics.py:209` `test_truncate_tolerates_an_empty_frame` — truncate tolerates an empty frame
- `tests/test_metrics.py:214` `test_sap_measures_differently_on_two_dates_from_one_series` — The whole point of truncating, on real prices.
- `tests/test_metrics.py:235` `test_a_truncated_frame_and_a_pre_cut_frame_agree` — a truncated frame and a pre cut frame agree
- `tests/test_metrics.py:243` `test_an_as_of_before_the_series_starts_yields_data_missing` — an as of before the series starts yields data missing
- `tests/test_metrics.py:254` `test_settled_through_demotes_todays_bar_during_the_new_york_session` — The DECK hand run: 2026-08-25 17:13 CEST = 11:13 New York.
- `tests/test_metrics.py:262` `test_settled_through_accepts_todays_bar_after_the_new_york_close` — The scheduled run: deploy/vss.timer fires 22:30 Stockholm = 16:30 NY.
- `tests/test_metrics.py:270` `test_the_live_bar_is_dropped_and_the_settled_close_is_read` — 88.55 was the live print; 88.74 the settled close of the day before it.
- `tests/test_metrics.py:284` `test_the_same_frame_after_the_close_reads_the_settled_bar_for_today` — the same frame after the close reads the settled bar for today
- `tests/test_metrics.py:293` `test_no_cutoff_declared_is_DATA_MISSING_not_a_claim_that_it_settled` — no cutoff declared is DATA MISSING not a claim that it settled
- `tests/test_metrics.py:301` `test_the_drawdown_and_the_52w_high_are_struck_on_the_settled_close_too` — One price, one date: the live bar must not reach any metric.
- `tests/test_metrics.py:313` `test_a_series_short_of_52_weeks_gives_no_52_week_high_at_all` — NEVER A LOWER NUMBER. 120 rows of DECK's own cache read a 22.4%
- `tests/test_metrics.py:326` `test_the_bar_is_52_weeks_plus_five_trading_days` — The five days are the margin that makes "52 weeks" mean a window
- `tests/test_metrics.py:337` `test_a_bare_year_of_trading_rows_does_not_clear_the_bar` — About 250 trading rows span a bare 52 weeks and may be missing the
- `tests/test_metrics.py:344` `test_a_two_year_cache_clears_it_and_that_is_what_the_run_fetches` — `fetch.DEFAULT_PERIOD` is 2y, for the watchlist and the screener.

**`tests/test_watch.py`** — vss watch (17 tests)

- `tests/test_watch.py:49` `test_the_pre_announcement_passes_although_its_category_says_nothing` — CA 995, 2026-01-09. Filed under `Inside information` -- the same
- `tests/test_watch.py:59` `test_the_categories_the_exchange_itself_calls_a_report_pass` — the categories the exchange itself calls a report pass
- `tests/test_watch.py:67` `test_a_report_filed_under_inside_information_still_passes_on_its_title` — The category is a filing choice: Pandora's H1 2026 report is filed
- `tests/test_watch.py:75` `test_a_profit_warning_is_reported_as_the_warning_it_is` — a profit warning is reported as the warning it is
- `tests/test_watch.py:95` `test_everything_else_is_rejected` — Leadership, M&A, buybacks, managers' transactions, shareholder
- `tests/test_watch.py:106` `test_the_first_run_baselines_and_reports_nothing` — A first notification carrying a year of history is how a watcher
- `tests/test_watch.py:118` `test_the_second_run_reports_only_what_arrived_after_it` — the second run reports only what arrived after it
- `tests/test_watch.py:135` `test_nothing_new_sends_nothing_and_exits_zero` — nothing new sends nothing and exits zero
- `tests/test_watch.py:144` `test_a_malformed_state_file_is_an_error_not_a_silent_reset` — a malformed state file is an error not a silent reset
- `tests/test_watch.py:151` `test_state_round_trips` — state round trips
- `tests/test_watch.py:160` `test_one_line_per_disclosure_ticker_date_title` — one line per disclosure ticker date title
- `tests/test_watch.py:165` `test_an_empty_list_posts_nothing` — an empty list posts nothing
- `tests/test_watch.py:172` `test_a_missing_topic_url_is_reported_and_is_not_an_error` — a missing topic url is reported and is not an error
- `tests/test_watch.py:178` `test_the_post_carries_the_lines_as_its_body` — the post carries the lines as its body
- `tests/test_watch.py:201` `test_a_ticker_with_no_nordic_issuer_is_named_not_skipped` — DECK and MC.PA are on the watchlist and not on this feed. Silence
- `tests/test_watch.py:218` `test_the_cron_line_is_printed_and_nothing_is_installed` — the cron line is printed and nothing is installed
- `tests/test_watch.py:253` `test_e27_both_watch_statuses_are_watched` — FRAMEWORK-EDITS E27: the split did not narrow what `vss watch` reads.

**`tests/test_nordic.py`** — the Nordic feed the watcher reads (download tool; listed for completeness) (44 tests)

- `tests/test_nordic.py:153` `test_the_query_carries_market_company_and_nothing_that_lies` — the query carries market company and nothing that lies
- `tests/test_nordic.py:163` `test_the_query_never_sends_cnscategory_or_a_date_filter` — Both are accepted by the service and one of them lies.
- `tests/test_nordic.py:178` `test_pagination_is_start_and_only_appears_when_asked_for` — pagination is start and only appears when asked for
- `tests/test_nordic.py:183` `test_asking_for_more_than_the_service_gives_fails_loudly` — It answers 400 with 200 rows and says nothing. Say something.
- `tests/test_nordic.py:192` `test_attachments_keep_their_index_and_their_declared_type` — attachments keep their index and their declared type
- `tests/test_nordic.py:200` `test_a_single_item_is_not_read_as_a_list_of_its_keys` — The service returns a bare mapping when one row matches.
- `tests/test_nordic.py:208` `test_an_empty_feed_is_named_rather_than_read_as_no_reports` — an empty feed is named rather than read as no reports
- `tests/test_nordic.py:217` `test_oslo_is_told_it_is_the_wrong_exchange_not_handed_nothing` — Oslo Børs is Euronext. An empty result would read as "no reports".
- `tests/test_nordic.py:224` `test_an_unmapped_ticker_says_how_to_map_it` — an unmapped ticker says how to map it
- `tests/test_nordic.py:229` `test_the_mapping_loads_and_rejects_a_key_it_does_not_know` — the mapping loads and rejects a key it does not know
- `tests/test_nordic.py:242` `test_a_mapping_without_a_company_is_refused` — a mapping without a company is refused
- `tests/test_nordic.py:248` `test_writing_a_mapping_backs_up_and_never_replaces` — writing a mapping backs up and never replaces
- `tests/test_nordic.py:269` `test_resolution_groups_on_the_feeds_own_company_field` — Full-text search returns issuers that merely MENTION the term.
- `tests/test_nordic.py:293` `test_the_period_is_shape_checked_against_the_shared_vocabulary` — the period is shape checked against the shared vocabulary
- `tests/test_nordic.py:300` `test_a_quarterly_reporter_may_label_its_annual_report_FY` — `rules.period_kind_allowed` must NOT be applied here.
- `tests/test_nordic.py:317` `test_the_filename_leads_with_ticker_period_category_and_date` — the filename leads with ticker period category and date
- `tests/test_nordic.py:325` `test_the_filename_carries_the_category_the_exchange_filed_it_under` — Not a category this tool inferred. `inside-information` on an interim
- `tests/test_nordic.py:334` `test_language_and_attachment_index_are_what_make_the_name_unique` — Betsson files every report twice and its annual filing carries two
- `tests/test_nordic.py:345` `test_slug_is_filename_safe` — slug is filename safe
- `tests/test_nordic.py:353` `test_the_extension_follows_the_bytes_not_the_promise` — the extension follows the bytes not the promise
- `tests/test_nordic.py:359` `test_a_matching_declaration_raises_no_note` — a matching declaration raises no note
- `tests/test_nordic.py:371` `test_a_download_lands_on_disk_and_in_the_manifest` — a download lands on disk and in the manifest
- `tests/test_nordic.py:394` `test_the_manifest_says_a_file_it_never_fetched_is_not_recorded` — Provenance NOT RECORDED is a third state, not "secondary".
- `tests/test_nordic.py:405` `test_the_note_claims_only_what_the_flag_actually_means` — `figures_read` says nothing was taken INTO config/manual. It does not
- `tests/test_nordic.py:423` `test_a_saved_manifest_refreshes_the_note_from_the_constant` — So a reworded note reaches files written before the rewording.
- `tests/test_nordic.py:433` `test_re_downloading_identical_bytes_is_a_skip_not_an_overwrite` — re downloading identical bytes is a skip not an overwrite
- `tests/test_nordic.py:446` `test_a_changed_document_fails_rather_than_overwriting` — The issuer replaced the file, or two filings collided on one name.
- `tests/test_nordic.py:461` `test_an_esef_package_is_saved_as_a_zip_not_as_a_pdf` — an esef package is saved as a zip not as a pdf
- `tests/test_nordic.py:470` `test_nothing_is_read_out_of_a_downloaded_document` — The line this module does not cross, asserted rather than asserted-to.
- `tests/test_nordic.py:502` `test_the_default_listing_shows_every_release_carrying_a_document` — the default listing shows every release carrying a document
- `tests/test_nordic.py:512` `test_the_reports_filter_says_how_many_rows_it_hid_and_why` — the reports filter says how many rows it hid and why
- `tests/test_nordic.py:523` `test_a_multi_file_disclosure_refuses_to_guess_which_one` — a multi file disclosure refuses to guess which one
- `tests/test_nordic.py:533` `test_a_download_without_a_period_is_refused` — a download without a period is refused
- `tests/test_nordic.py:540` `test_a_release_with_no_attachment_says_so_rather_than_scraping` — a release with no attachment says so rather than scraping
- `tests/test_nordic.py:547` `test_an_id_the_feed_does_not_carry_says_how_much_was_read` — an id the feed does not carry says how much was read
- `tests/test_nordic.py:558` `test_the_download_report_names_the_url_the_bytes_and_the_digest` — the download report names the url the bytes and the digest
- `tests/test_nordic.py:592` `test_a_download_reaches_a_report_several_pages_back` — Backfilling eight periods means reports the first page does not hold.
- `tests/test_nordic.py:615` `test_the_walk_stops_at_the_end_of_the_feed` — Bounded by the feed's own count, so a missing id terminates.
- `tests/test_nordic.py:625` `test_an_empty_feed_names_the_language_filter_as_a_possibility` — An issuer that files only in English has no Swedish edition.
- `tests/test_nordic.py:641` `test_a_file_on_disk_with_no_manifest_entry_gets_one` — Otherwise a document this tool fetched reads as PROVENANCE NOT
- `tests/test_nordic.py:663` `test_a_repaired_record_says_the_same_things_as_a_fresh_one` — One definition of an entry, so the two paths cannot disagree.
- `tests/test_nordic.py:680` `test_the_year_end_release_and_the_annual_report_do_not_collide` — Betsson files BOTH for 2025, and both are honestly `2025-FY`.
- `tests/test_nordic.py:708` `test_the_committed_map_holds_every_nordic_name_section_5_has_priced` — REVIEW-4 report B 5.1 / #5: LIAB.ST was absent from the map.
- `tests/test_nordic.py:723` `test_every_mapped_issuer_states_where_and_when_it_was_resolved` — every mapped issuer states where and when it was resolved

523 tests across the sixteen files.

---

## 7. Open items — every B/C/E entry in FRAMEWORK-EDITS that touches the screener

Status is the item's own marker where it carries one; "no marker" means the
item's text carries no DECIDED/OPEN/SETTLED line. Line numbers are of
`reference/FRAMEWORK-EDITS.md`.

| item | line | status | what it touches in the code |
|---|---:|---|---|
| B1 — Gate 1 "bulk of the decline" | 70 | DECIDED 2026-08-22: Gate 1 measures today's position, timing is context | `b1_metric` reported, never applied (`vss/filters.py:216-240`) |
| B2 — band boundaries and which "high" | 121 | no marker (proposed inclusive bounds, closing high) | implemented as if decided: `vss/rules.py:493`, `vss/metrics.py:5-8, 209-221` |
| B3 — Gate 3 "revenue stable within ±2%" | 131 | settled by E30 (`FRAMEWORK.md:112`) | never coded; the config's revenue limb cites B3 as "undecided" (`config/screener_filter2.yaml`, `blocked_on`) — that line predates E30 |
| B4 — Gate 3 gross-margin band | 149 | SUPERSEDED 2026-08-25 by E30 | never coded |
| B5 — Gate 4 missing input; the A7 proxy | 177 | DECIDED 2026-08-21 | not in the screener (§3.4); `vss/manual.py:456-460` field note only |
| B6 — §4.4: how Gate 3 counts as passed | 253 | no marker | no §4.4 code (§4.1) |
| B7 — materiality floor, inventory limb | 266 | DECIDED 2026-08-21 | precedent for NOT APPLICABLE (`vss/filters.py:530-533`) |
| B9 — the revenue kill measures demand | 362 | DECIDED 2026-08-22 | revenue limb is a FLAG (`vss/filters.py:555-584`) |
| B11 — the ranking key reads one period and does not ask how long | 408 | SETTLED by E13 | `vss/ranking.py:202-331` |
| B19 — the ranked list's Consumer Cyclical overweight | 2953 | settled by measurement 2026-08-25, no ruling, no code change | — |
| B20 — Gate 3's revenue limb names no basis | 3120 | SETTLED 2026-08-25 by E30 | — |
| B22 — may a gate-failed name carry a tier? | 3846 | OPEN | the PIPELINE → tier route; nothing in the screener assigns a tier |
| B24 — distance between basis end and price date | 4415 | OPEN | `MAX_REPORT_AGE_DAYS = 550` (`vss/fundamentals.py:103`) is the only age bound the screener applies |
| B25 — E31's collision with Gate 1 | 4440 | OPEN | Gate 1 admits on a recent fall; a fiscal-year basis may predate it |
| C3 — §1.2 vs practical freshness | 981 | DECIDED 2026-08-21 | staleness gate 3 trading days (`vss/rules.py:76, 280-304`) against §1.2's "≤ 1 trading day" |
| E1 — omxs-large-mid is an approximation | 1077 | DECIDED 2026-08-22 | the file's `.meta.json`; universe report prints APPROXIMATION |
| E2 — filter 2 uses §4.2.5's 3.5× | 1112 | DECIDED 2026-08-22 | `config/screener_filter2.yaml` `max: 3.5`, `not_chosen: 2.5` |
| E3 — Real Estate NOT APPLICABLE on leverage | 1140 | DECIDED 2026-08-22 | config `not_applicable_sectors`; `vss/filters.py:528-533` |
| E4 — a limb with no data passes the name through | 1170 | DECIDED 2026-08-22 | config `on_missing_action: pass_through`; `vss/filters.py:619-626` |
| E5 — Greenblatt two-component key | 1188 | SUPERSEDED 2026-08-22 by E6 (E5(a) separate section and E5(d) tie rule kept) | `vss/ranking.py:1087-1120` |
| E6 — the quality leg is gross profitability | 1435 | DECIDED 2026-08-22 | `vss/ranking.py:143-155, 971-1001` |
| E7 — `Gross Profit` is a presentation choice | 1721 | DECIDED 2026-08-23 as a known limitation, no mechanical fix | UHS excluded by hand (`config/screener_exclusions.csv`) |
| E8 — EBIT alias set ordered on meaning, year, unit | 1877 | DECIDED 2026-08-23 | `vss/ranking.py:117-135, 476-586` |
| E9 — §4.2.2 "flat/declining revenue" carries no number | 2105 | RECORDED 2026-08-23, OPEN | no code |
| E10 — the earnings yield double-counts leases | 2166 | RECORDED 2026-08-23, measured, nothing changed | the EY leg (`vss/ranking.py:1027-1030`) |
| E11 — a PIPELINE name can leave the band while it sits there | 2342 | SETTLED by E12 for PIPELINE names | — |
| E12 — Gate 1 frozen at entry; store `dd_at_entry` and the peak date | 2448 | DECIDED 2026-08-24 | schema validates the pair (`vss/config.py:317-345`); no writer, no reader (§5.3) |
| E13 — the ranking key is struck on trailing twelve months | 2473 | DECIDED 2026-08-24 | `vss/ranking.py:202-331`; `period_months` on every stored point |
| E24 — price legs in the quote currency, rate frozen | 3230 | DECIDED 2026-08-25 | pence note and GBX currency on a written entry (`vss/pipeline.py:137-148`; `vss/fx.py:84-99`) |
| E27 — WATCH was two states | 3724 | DECIDED 2026-08-25 | the watcher reads both halves (`vss/watch.py:83-95`) |
| E30 — Gate 3's revenue limb and gross-margin band are deleted | 4157 | DECIDED 2026-08-25 | no change in the screener: its FCF and leverage limbs predate E30 and stand; its revenue trend is §4.2.1's flag, not Gate 3's limb |

Not in FRAMEWORK-EDITS but governing the code: the K-findings of
`reports/screener-review-2026-08-22.md` (K4 series sanity, K5/L4 staleness on
rows read, K6 mixed periods, K7 fx reproducibility) and the L-findings of
`reports/screener-review-2-2026-08-23.md` (L2 EV bound, L3 alias order, L5
cross-dating, L6 turnover in the group's own currency), each cited in the
code at the lines named above; the reports themselves are gitignored.

---

## 8. RUN IT — the full universe, 2026-08-26

Three invocations, in sequence, from a clean shell (`--asof 2026-08-26`,
tier A, defaults everywhere), started 11:19:38 CEST and finished 11:35:56
CEST — **978 s wall-clock, 16 min 18 s**:

| step | command | wall-clock | result |
|---|---|---:|---|
| prices | `python -m vss screen --snapshot-only --asof 2026-08-26` | 236 s | 1,370 tickers, 28 batches of 50; 1,370 OK, 0 THROTTLED, 0 NO_DATA, 0 STALE; no retry fired |
| fundamentals | `python -m vss screen --fundamentals --asof 2026-08-26` | 730 s | 485 filter-1 survivors, 1,455 requests (3 per ticker per `vss/fundamentals.py:99`; the report sentence at `vss/screen.py:717-719` still names only two of them); 483 OK, 2 STALE; no retry fired |
| ranking | `python -m vss screen --rank --asof 2026-08-26` | 12 s | 12 pairs fetched, every rate dated 2026-08-26; fundamentals and price dates agree ("contemporaneous") |

Nothing was written to `config/watchlist.yaml` (`--write-pipeline` not
passed). Outputs: `data/screener_snapshots/2026-08-26/{snapshot,fundamentals}.sqlite`,
`data/screener_runs/2026-08-26/{ranking.csv,ranking-manifest.json}` — all
gitignored.

### 8.1 The head (top 20 on both components; the top 5 is what `--write-pipeline` would enter)

| # | ticker | sector | sum | GP/TA rank | EY rank | GP/TA | EY | EBIT label | basis |
|---:|---|---|---:|---:|---:|---:|---:|---|---|
| 1 | FGR.PA | Industrials | 48 | 34 | 14 | 53.6% | 11.3% | Total Operating Income As Reported | annual |
| 2 | BUCN.SW | Industrials | 52 | 33 | 19 | 54.2% | 10.0% | Total Operating Income As Reported | annual |
| 3 | NREST.ST | Consumer Cyclical | 56 | 4 | 52 | 85.1% | 7.9% | Total Operating Income As Reported | annual |
| 4 | ZZ-B.ST | Consumer Defensive | 58 | 31 | 27 | 54.4% | 9.3% | Total Operating Income As Reported | annual |
| 5 | AFRY.ST | Industrials | 64 | 8 | 56 | 75.7% | 7.8% | Total Operating Income As Reported | annual |
| 6 | HWDN.L | Consumer Cyclical | 79 | 16 | 63 | 64.4% | 7.5% | Total Operating Income As Reported | annual |
| 7 | RVRC.ST | Consumer Cyclical | 85 | 3 | 82 | 86.1% | 6.7% | Total Operating Income As Reported | annual |
| 8 | WKL.AS | Industrials | 89 | 52 | 37 | 47.0% | 8.9% | Total Operating Income As Reported | annual |
| 9 | AD.AS | Consumer Defensive | 91 | 46 | 45 | 49.9% | 8.2% | Total Operating Income As Reported | annual |
| 10 | HCA | Healthcare | 91 | 44 | 47 | 51.7% | 8.2% | Operating Income | annual |
| 11 | NOVO-B.CO | Healthcare | 95 | 57 | 38 | 46.1% | 8.8% | Total Operating Income As Reported | annual |
| 12 | BEI.DE | Consumer Defensive | 96 | 62 | 34 | 44.6% | 8.9% | Total Operating Income As Reported | annual |
| 13 | KEMIRA.HE | Basic Materials | 98 | 58 | 40 | 45.7% | 8.7% | Total Operating Income As Reported | annual |
| 14 | AOS | Industrials | 99 | 51 | 48 | 47.3% | 8.1% | Operating Income | annual |
| 15 | NVR | Consumer Cyclical | 99 | 76 | 23 | 40.8% | 9.9% | Operating Income | annual |
| 16 | ERIC-B.ST | Technology | 102 | 78 | 24 | 40.4% | 9.8% | Operating Income | annual |
| 17 | NHY.OL | Basic Materials | 102 | 101 | 1 | 35.9% | 19.5% | Operating Income | annual |
| 18 | IT | Technology | 103 | 30 | 73 | 55.0% | 7.2% | Total Operating Income As Reported | annual |
| 19 | ADS.DE | Consumer Cyclical | 109 | 19 | 90 | 63.2% | 6.5% | Total Operating Income As Reported | annual |
| 20 | REJL-B.ST | Industrials | 112 | 15 | 97 | 65.4% | 6.3% | Total Operating Income As Reported | annual |

Ties: AD.AS/HCA at 91, AOS/NVR at 99 and ERIC-B.ST/NHY.OL at 102 are in
alphabetical order, per `vss/ranking.py:1113`. Every row's flow figures are
on the `annual` basis with period end 2025-12-31 (2025-11-30 and fiscal
year-ends elsewhere in the list).

### 8.2 Names passing each gate, in sequence

| step (code name) | in | out | rejected on VALUE | rejected on MISSING |
|---|---:|---:|---:|---:|
| CSV rows read (`read`) | 1436 | 1436 | 0 | 0 |
| tier A (`tier_select`) | 1436 | 1436 | 0 | 0 |
| instrument type (`instrument_type`) | 1436 | 1419 | 17 | 0 |
| Yahoo symbol (`yahoo_mapping`) | 1419 | 1419 | 0 | 0 |
| dedup (`dedup`) | 1419 | 1370 | 49 | 0 |
| price fetch (`price_fetch`) | 1370 | 1370 | 0 | 0 |
| **step 0, exclusion list** (`exclusion_list`) | 1370 | 1355 | 15 | 0 |
| price coverage / 3-trading-day gate (`price_coverage`) | 1355 | 1355 | 0 | 0 |
| series sanity (`series_sanity`) | 1355 | 1351 | 0 | 4 |
| **Gate 1 level leg, 15–50% band** (`dislocation`) | 1351 | 485 | 849 | 17 |
| fundamentals fetched (`fundamentals_fetch`) | 485 | 483 OK | 2 STALE | 0 |
| **filter 2, three limbs** (`filter2`) | 485 | 361 | 124 | 0 |
| share-class collapse (`share_class`) | 361 | 353 | 8 | 0 |
| ranking (`rank`) | 353 | 288 both legs + 49 yield-only | 4 stale | 12 unrankable |
| head | | 20 printed; 5 would be written | | |

Filter 2's 124 value rejections: 52 on leverage alone, 48 on free cash flow
alone, 24 on both. Step 0 matched 15 of the 16 rows in
`config/screener_exclusions.csv` (ADBE, BETS-B.ST, DECK, HNSA.ST, JD.L,
LIAB.ST, LULU, MSFT, NKE, PNDORA.CO, ROCK-B.CO, SAP.DE, SYNSAM.ST, UHS,
ULVR.L); the `UNA.AS` row is **inert** — Unilever's Amsterdam line is not in
any universe file (the STOXX file carries `ULVR.L`), so the chain prints it
as matching nothing.

### 8.3 DATA MISSING per gate, and the field responsible

| gate | DATA MISSING | field / reason | what happened to the name |
|---|---:|---|---|
| step 0 | 0 | — | — |
| price coverage | 0 | every name had a series with a close ≤ 3 trading days old | — |
| series sanity | 4 | the `Close`/`Volume` series: ELUX-A.ST (−48% on 2026-05-19 on 0.1× median volume), ELUX-B.ST (−46%, 1.4×), ORSTED.CO (−45% on 2025-09-08, 1.1×) — uncorroborated discontinuity; MNST — scale switch (−51% 2026-07-20, +96% 2026-07-23, product 0.957) | rejected ON MISSING |
| Gate 1 band | 17 | `high_52w` / `drawdown` withheld: the first stored bar is later than `coverage_start(2026-08-26)` = 2025-08-20 — AMV0.DE, COFFEE-B.ST, CSG.AS, FDXF, HONA, KMAR.OL (first bar 2026-04-23, 87 rows), MICC.AS, NOBA.ST, OCTV-SDB.ST, PUBLI.ST, Q, SALIX.ST, SAMPO-SEK.ST, SILEX.ST, SNM-SDB.ST, VSURE.ST (first bar today), WSG.ST | rejected ON MISSING |
| fundamentals fetch | 2 STALE | newest annual period: BWY.L 2024-07-31 (756 days), COLO-B.CO 2024-09-30 (695 days) | passed through filter 2, excluded ON VALUE at the ranking |
| filter 2 — `free_cash_flow` | 12 | `freeCashflow` absent | passed through, marked (`on_missing_action: pass_through`) |
| filter 2 — `net_debt_to_ebitda` | 2 | `ebitda` absent on a non-financial with net cash | passed through, marked |
| filter 2 — `net_debt_to_ebitda` | 66 NOT APPLICABLE | `sector` Financial Services / Real Estate | not a DATA MISSING; passes |
| filter 2 — `revenue_trend` | 1 | one annual `Total Revenue` point | passed through; 110 more carry FLAG (≥ 2 consecutive annual declines), which never rejects |
| ranking — earnings yield | 7 | no EBIT under any of the three aliases: BX, CMBN.SW, COF, ENITY.ST, III.L, SQN.SW, VATN.SW | unrankable |
| ranking — earnings yield | 4 | `enterpriseValue` implies more net cash than `Total Assets`: CVNA 4.1×, LISP.SW 1.9×, PLUS.L 1.2×, PLTR 1.0× | unrankable (yield withheld) |
| ranking — earnings yield | 1 | one figure in two units: MONC.MI, `Total Operating Income As Reported` 913,356 beside `Operating Income` 913,356,000 for 2025-12-31 | unrankable |
| ranking — quality leg | 3 | `Gross Profit` or `Total Assets` absent | yield-only section |
| ranking — quality leg | 2 | `Gross Profit` and `Total Assets` from different period ends | yield-only section |
| ranking — quality leg | 52 | sector exempt (not a DATA MISSING) | yield-only section |
| ranking — staleness on rows read | 2 | ERIE (EBIT row 2024-12-31, 603 days), SHL.DE (all three rows 2024-09-30, 695 days) | excluded ON VALUE, with the two record-level STALE names |

Fifteen of the 485 filter-2 entrants carry at least one untested limb; none
was rejected on it. **Which day was priced:** the price fetch ran at 11:19
CEST with European sessions open and New York closed. The snapshot's
`fetch_status.last_date` is 2026-08-26 for 864 tickers and 2026-08-25 for
506; among the 485 band candidates, 307 carry a 2026-08-26 last close — a
live intraday print, per §2.1 — and 178 the settled close of 2026-08-25.

### 8.4 The head against the last committed run

The committed reference is the frozen 2026-08-21 candidate set and its
pinned top twenty (`tests/test_ranking_acceptance.py:146-180`): UHS, LULU,
DECK, PNDORA.CO, BETS-B.ST, ROCK-B.CO, JD.L, NREST.ST, FGR.PA, BUCN.SW,
AFRY.ST, ADBE, SYNSAM.ST, ZZ-B.ST, HWDN.L, RVRC.ST, NOVO-B.CO, AD.AS, HCA,
KMAR.OL.

**Left the head — 10.** Nine by **step 0**: rows added to the exclusion list
after the fixture was frozen — UHS (E7, 2026-08-23), LULU (DROPPED,
2026-08-23), ROCK-B.CO (E8-REVIEW, 2026-08-23), DECK (WATCH-REVIEW,
2026-08-24), JD.L (DROPPED, 2026-08-24), PNDORA.CO (WATCH-REVIEW,
2026-08-25), BETS-B.ST (DROPPED, 2026-08-25), ADBE (DROPPED, 2026-08-25),
SYNSAM.ST (DROPPED, 2026-08-25). One by **filter 1, DATA MISSING**: KMAR.OL
— its stored series starts 2026-04-23 (87 rows), so under the 52-weeks-plus-
five-days coverage bar ruled after REVIEW-4 (`vss/metrics.py:70-77`) it has
no 52-week high; that bar did not exist when the fixture was frozen, and on
2026-08-21 the name was ranked on the maximum of the rows it had.

**Stayed — 10**, every one moved up as the names above it left: NREST.ST
8→3, FGR.PA 9→1, BUCN.SW 10→2, AFRY.ST 11→5, ZZ-B.ST 14→4, HWDN.L 15→6,
RVRC.ST 16→7, NOVO-B.CO 17→11, AD.AS 18→9, HCA 19→10.

**Entered the head — 10.** Their accounts are unchanged (every one's EBIT
and gross-profit period is still 2025-12-31); what moved is (i) the ten
departures above them, (ii) the two-legged population the competition ranks
are computed over — 322 in the fixture, 288 today, so every placing is
renumbered — and (iii) the enterprise value, which carries today's quote and
today's rate. Place on the local 2026-08-21 ranking (file of 2026-08-24, the same
exclusions save the rows added 2026-08-25: PNDORA.CO, BETS-B.ST, ADBE,
SYNSAM.ST, NKE) → today, with the rank sum:

| ticker | 2026-08-21 place, sum (q, ey) | today place, sum (q, ey) | why it is here |
|---|---|---|---|
| WKL.AS | 15, 105 (61, 44) | 8, 89 (52, 37) | departures above; both placings renumbered upward |
| BEI.DE | 17, 107 (71, 36) | 12, 96 (62, 34) | same |
| KEMIRA.HE | 21, 110 (67, 43) | 13, 98 (58, 40) | same |
| AOS | 24, 116 (60, 56) | 14, 99 (51, 48) | same |
| NVR | 19, 109 (84, 25) | 15, 99 (76, 23) | same. The fixture disagrees with itself about NVR: its comment at `tests/test_ranking_acceptance.py:182-183` says the L2 bound "put NVR in at 20", while the pinned list at `164-180` has KMAR.OL at 20 and no NVR; both are stated, neither resolved here |
| ERIC-B.ST | 22, 112 (86, 26) | 16, 102 (78, 24) | same; ERIC-A.ST folded into it on turnover today as on 08-21 |
| NHY.OL | 23, 112 (110, 2) | 17, 102 (101, 1) | EY rank 1 today because BETS-B.ST, the fixture's EY rank 1, is excluded |
| IT | 25, 121 (37, 84) | 18, 103 (30, 73) | departures above |
| ADS.DE | 28, 130 (25, 105) | 19, 109 (19, 90) | departures above |
| REJL-B.ST | 26, 127 (20, 107) | 20, 112 (15, 97) | departures above |

Two names that sat in the local 2026-08-21 file's top twenty but not in the
committed fixture's are out of the band today, not excluded: LUG.ST (drawdown
13.7%) and KCR.HE (12.7%), both rejected ON VALUE at filter 1 — the price
recovered past the 15% edge.

---

## What the reviewer should look at first

The screener prices Gate 1 on whatever bar yfinance returns up to `--asof`:
`run_filter1` calls `metrics.compute(frame, as_of)` with no settlement cutoff
(`vss/filters.py:275`), while `vss run` demotes today's bar until New York
closes (`vss/metrics.py:96-104`; `vss/runner.py:256` passes `settled_through(run_ts)` to every row). Today's run stamped a live
11:19-CEST print as the close for 864 of 1,370 names and 307 of the 485 band
candidates, and the 15% edge of the band — the one threshold that actually
removes names, 849 of them today — was decided on that number for every
European name. Around that, the shape worth holding in mind: the code is
Gate 1's level leg, three coarse limbs, and E6's two-rank sum; Gates 2, 4 and
5, the catalyst leg, the RSI veto and the §4.4 score exist only on paper,
and `dd_at_entry` (E12) is validated but never written or read. The single
largest mover of the head between the committed run and today is not any
of that machinery but the hand-maintained exclusion list — nine of ten
departures — a file that still calls SAP.DE HELD after its sale and carries
one row (UNA.AS) that matches nothing. Whether the head is a measurement of
the market or of the exclusion file's edit history is the question I would
put first.
