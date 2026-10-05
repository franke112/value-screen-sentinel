# vss — value-screen sentinel

**A value-investing method that one person can actually keep to, run together
with [Claude Code](https://claude.com/claude-code).**

About two thousand listed companies you could buy a piece of. One person, a
few evenings a week. And no reliable way to know whether you are reading a
company carefully or just talking yourself into it. vss is the tool I built
to handle that last part.

It screens the market, reads the companies' own reports, works out what
growth today's price is assuming, and watches the names you care about every
night. **It never tells you to buy anything.** It measures. You decide, and
it keeps the record of what you decided and why.

> **The full story -- how the method works and why, in 23 short chapters:**
> **[franke112.github.io/value-screen-sentinel/the-method/](https://franke112.github.io/value-screen-sentinel/the-method/)**

## Four habits it enforces

1. **Figures come only from the company's own filings.** Every number
   carries the filing, the period and the line it was read from. If there's
   no source, the number doesn't go in.
2. **You write down your view before you see the market's.** Your growth
   expectation (base, bear, bull, with reasons) is registered and
   timestamped *before* the tool solves for what the price implies. A view
   written after seeing the price doesn't count.
3. **A failed test is final.** A company that fails on something other than
   price does not come back because the price fell. Only a new fact brings
   it back: a new filing, a profit warning, a changed forecast.
4. **Every refusal is tracked.** Most companies get a "no". Each one is
   recorded with the price and the reason, then measured against the index
   at 1, 3, 6 and 12 months. So you find out whether your no's were right.

## What it looks like in practice

- **Cirrus Logic** passed every mechanical check. I dropped it anyway,
  because 91% of its sales go to Apple, and whether Apple keeps buying is a
  question I can't judge better than the market. The reasoning is on file in
  my own words, and the shadow book keeps measuring what that refusal cost
  or saved.
- **Copart** fell 57% from its high. I wrote down my growth view (6% base),
  and then the tool found that the price was already assuming 7%. The price
  is above my own fair value, so I passed and set an alert. The tool didn't
  stop me; my own numbers did.
- **Accenture's results** came in overnight. The watcher saw the SEC filing,
  read the press release twice, kept only the figures both readings agreed
  on, dropped one the model couldn't quote a source for, and checked my
  warning rules. No session had to be opened.

## What it is not

- **Not financial advice**, and not a recommendation to buy or sell
  anything. This is one private investor's method, shared as it is.
- **Not a trading bot.** It places no orders and has no view on next week.
- **Not a website.** It's a command-line tool and a set of rules, designed
  to be worked through in Claude Code sessions. Some setup is needed.

## Disclosure

**I own shares in Cognizant (CTSH) and Cirrus Logic (CRUS)** as of
2026-10-05, and the record in this repository shows when I bought and sold
others. The fair values, buy limits (MBP) and stops in
`config/watchlist.yaml` are my personal working notes, written for my own
decisions. **Nothing here is a recommendation to buy, sell or hold any
security.** If my holdings change, this line may be out of date -- the
watchlist's `status: HELD` entries are the current record.

## Who it might be useful for

A private investor who already uses Claude Code, likes the idea of value
investing, and wants **rules and a record** instead of gut feeling: someone
who has accepted that most of the time the right answer is no, and wants to
be able to check afterwards whether it was.

## The record is public too

My watchlist, my growth views, the rulings that shaped the method (E1–E129)
and the trades are in this repo as they are, including the ones that went
against my own rules. A method you can't check is a story.

## Where the data comes from

No market data is shipped. The screener's universe lists in
`config/universe/` hold only tickers, names, ISINs and listing facts:
the S&P 400 and S&P 500 lists come from Wikipedia
([S&P 500](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies),
[S&P 400](https://en.wikipedia.org/wiki/List_of_S%26P_400_companies),
CC BY-SA 4.0), the STOXX Europe 600 list from the iShares fund holdings file,
and the Nordic lists from Yahoo's equity screener; each file's source is in
its `.meta.json`. Prices come from Yahoo Finance via yfinance and filings
from SEC EDGAR and the Nasdaq Nordic disclosure feed -- fetched by you, at
run time.

## Read more

- **The full story, 23 short chapters:** [the website](https://franke112.github.io/value-screen-sentinel/the-method/) (source in [`docs/the-method/`](docs/the-method/))
  covers why the method needed a machine, the reverse DCF, pre-registration
  and the shadow book.
- **How to run it:** [`SETUP.md`](SETUP.md), then the technical manual
  below (what you need: Python, Claude Code, an SEC contact
  e-mail; optionally an OpenRouter key for the report reader and an ntfy
  topic for phone alerts).
- **The rules:** [`reference/FRAMEWORK.md`](reference/FRAMEWORK.md) and every
  ruling since, with its date and reason, in
  [`reference/FRAMEWORK-EDITS.md`](reference/FRAMEWORK-EDITS.md).

## Questions?

**Shared as-is. I don't take issues or pull requests.** I built this for
myself and had fun doing it; take what's useful. If you have questions,
open the repository in [Claude Code](https://claude.com/claude-code) and ask
it -- `CLAUDE.md` tells it how the project works, and it can explain any
part of it for as long as you like.

---

*Built by Veljko Radan, with Claude. MIT licence — use it, change it, share it; just keep the credit. See [`LICENSE`](LICENSE).*

---

# The technical manual


A small CLI that watches a hand-maintained value-investing watchlist. Every
run fetches daily OHLCV, computes a fixed set of metrics, applies a staleness
gate, and emits a markdown report to `reports/YYYY-MM-DD.md` and to stdout.

Its defining rule: **stale or unresolved data produces a blocker, never a
verdict.** The tool would rather tell you it cannot judge than judge on bad
data.

---

## What it does and does not do

`vss` computes **market data only**. Everything requiring judgment is a
MANUAL field you fill in by hand in `config/watchlist.yaml`; the tool never
computes, guesses, defaults or back-fills any of it.

The one derived exception is `mbp`, which is computed from two manual inputs:

```
mbp = fv_base * tier_multiplier        tier 1 = 0.80, tier 2 = 0.70, tier 3 = 0.60
```

`mbp` is therefore **not** a watchlist field. Writing an `mbp:` key by hand
fails the run with a provenance conflict. If `fv_base` or `tier` is absent,
`mbp` is `DATA MISSING` and every MBP-dependent verdict reports `DATA
MISSING` rather than a guess.

---

## Repository history

This repo's history was re-initialized on 2026-08-20 and starts from a single
initial commit. The original history carried a dated portfolio snapshot --
holdings, position values and P/L -- inside `reference/FRAMEWORK.md` §9 and
later in `snapshots/`. That history was discarded rather than carried into any
future remote.

`snapshots/` is gitignored, so the dated portfolio snapshots -- holdings,
position values and P/L -- stay on disk and outside git. **`config/watchlist.yaml`
is TRACKED as of 2026-08-25**, on the owner's decision: the repository is private
and the verdict history belongs in git rather than only in `.bak` files. What
that file carries is decisions -- status, `fv_base`, `tier`, `stop_price`, notes
and hand-entered quarterly figures -- and not quantities, cost basis or P/L.
Note the one-way property: committing a file puts it in history permanently, and
ignoring it later stops future commits without removing what is already there.

---

## Install

Requires Python 3.11+ and a working network connection.

> **Note on the Python version.** This box is Debian 13, which ships Python
> 3.13.5 and does not package 3.11 at all. `vss` is built and tested on
> 3.13.5. Nothing in the code depends on a version-specific feature, so a
> 3.11 venv works identically if you install one later.

```bash
cd ~/stocks
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

If `python3 -m venv` fails with **"ensurepip is not available"** (the case on
this machine -- Debian splits it into a separate package), either install the
package:

```bash
sudo apt install python3.13-venv
```

or, without root, bootstrap pip into the venv by hand:

```bash
cd ~/stocks
python3 -m venv --without-pip .venv
curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
.venv/bin/python /tmp/get-pip.py
.venv/bin/python -m pip install -r requirements.txt
```

Then create your watchlist:

```bash
cp config/watchlist.example.yaml config/watchlist.yaml
$EDITOR config/watchlist.yaml
```

`config/watchlist.yaml` is tracked (since 2026-08-25) and so is the example.
Its dated `.bak-` copies are ignored -- git keeps the history now.

---

## Usage

```bash
cd ~/stocks

.venv/bin/python -m vss run                    # fetch, report, persist
.venv/bin/python -m vss run --dry-run          # print the report, write nothing
.venv/bin/python -m vss run --ticker VOLV-B.ST # restrict to one ticker

.venv/bin/python -m vss screen --universe-report              # what the universe holds
.venv/bin/python -m vss screen --snapshot-only --asof 2026-08-21

.venv/bin/python -m vss overview               # regenerate reports/OVERVIEW.html
```

The **report goes to stdout** and **all logs go to stderr**, so they split
cleanly:

```bash
.venv/bin/python -m vss run > today.md 2> today.log
```

`--dry-run` prints a `DRY RUN — nothing written` banner as the first line of
stdout, then writes no report file, no database row and no price cache entry.
(It does still fetch, and yfinance maintains its own HTTP/timezone cache under
`data/yf-cache/`.)

`--ticker` produces a **partial run**, and the report says so throughout: the
title is marked `SCOPED to X`, a `PARTIAL RUN — 1 of N tickers` banner sits at
the top, and no section generalises about "every ticker". A scoped run writes
`reports/YYYY-MM-DD.<TICKER>.md` rather than the day's full report, so it can
never overwrite it, and its database rows carry `ticker_filter` so partial
history is distinguishable from full coverage.

Exit codes: `0` a run completed (even if individual tickers errored -- those
appear as ERROR rows), `2` the watchlist is missing or malformed, `130`
interrupted.

---

## Earnings: `vss earnings`

Reads a **primary source** quarterly/annual report for any ticker on the
watchlist and flags FRAMEWORK §4.2 trips.

**Status changes the framing, never the rules.** §4.2 is read in two
situations. On a `HELD` name it is thesis invalidation — the alert says `4.2
POSSIBLE TRIP - VERIFY AGAINST SOURCE`. On a waiting candidate — `WATCH-PRICED`,
`WATCH-GATED` or `PIPELINE` — it
is the §4 Phase 2 VALIDATION gate that decides whether the name may become a
position at all — the alert says `4.2 FAILS VALIDATION - VERIFY AGAINST
SOURCE`, because there is no thesis to invalidate yet. Same rules, same
figures, same arithmetic; what differs is what a trip *means*, and the alert
states the status it read. Clearing §4.2 on a candidate is one gate of Phase 2,
not a decision — the alert says that too.

```bash
export VSS_OPENROUTER_KEY=...          # required; never embedded in the repo
export VSS_OPENROUTER_MODEL=...        # optional, defaults to deepseek/deepseek-v4-flash

.venv/bin/python -m vss earnings --ticker MSFT --url https://microsoft.com/ir/...
.venv/bin/python -m vss earnings --ticker MSFT --text-file ./q4.txt
.venv/bin/python -m vss earnings --ticker MSFT --url ... --no-shadow
```

**You supply the URL.** vss has no news feed and never guesses at IR page
layouts, so "primary source, never a news article" holds by construction. The
daily report nags you instead: any HELD ticker whose `catalyst_date` has passed
with `catalyst_resolved` empty gets an EARNINGS TO INGEST line with the exact
command to run.

**Shadow mode is ON by default** — every decision is logged to
`earnings_runs` in sqlite and nothing is sent. The alert carries a SHADOW
banner, and each row records its own `shadow` flag so history can never imply
an alert went out when it did not. `--no-shadow` drops the banner.

**What the LLM does and does not do.** It extracts stated figures and the
verbatim sentence each came from, flags reported-vs-constant-currency and
GAAP-vs-non-GAAP, and returns `null` for anything not stated. It never derives,
estimates or reconciles a figure, never decides materiality, and never writes
prose. Every §4.2 judgement is a pure function in `rules.py`.

**Three hard boundaries**, each enforced by a test:

- `eps_consensus` is MANUAL ONLY. It is absent from the extraction schema; if a
  model returns it anyway the value is discarded and the run marked uncertain.
  Rule 4.2.4 reports CANNOT EVALUATE until you enter consensus yourself.
- Extracted figures **never** reach `quarters:`. They are proposed as a YAML
  block in the alert; you enter them. Same for `exec_changes` and
  `catalyst_resolved`.
- Any extraction failure, null figure, missing basis or model-flagged ambiguity
  marks the run **EXTRACTION UNCERTAIN** and alerts anyway. It never degrades
  silently.
- **A quote must contain the figure it claims to source.** `"Inventories"` does
  not evidence `1397`, and an allowance-for-doubtful-accounts sentence does not
  evidence a receivables balance. A figure whose quote lacks the number is set
  to null and reported as `PROVENANCE UNVERIFIABLE`. Magnitudes are never
  reconciled — a quote saying "80.9 billion" does not support `80876`, because
  inferring the scale would be deriving the figure. Table-sourced figures also
  record `period_column`, the verbatim column heading read, since a balance
  sheet carries more than one period column. An explicit scale word is honoured
  as a unit conversion — `"$90.0 billion"` does support `90000` stated in
  millions — but a *different* quantity still fails, so it never supports
  `90007`.
- **The quote must come from wherever the number was read.** A release states
  the same figure twice, in a summary sentence and in a statement table, at
  different precisions. Reporting the table's number while quoting the prose
  cites two different sources. Read a table row → quote the row including the
  number and name the column; read prose → report the prose's own precision
  and quote the sentence. The prompt carries worked correct-and-wrong examples
  of both.
- **Negative claims need provenance too.** `guidance_action: none` is a claim
  about the source. Without a quote it becomes null, not `"none"` — otherwise
  it is indistinguishable from the model not looking.
- **Ratios are fractions, on both sides.** An operating margin of 6.6 per cent
  is `0.066`, never `6.6` — the rules layer multiplies by 10,000 for basis
  points, so a percentage makes every §4.2 threshold wrong by 100×. The prompt
  converts the quoted percentage; the loader rejects a ratio outside its band
  (`rules.FRACTION_BANDS`) as a **hard error**, not a flag. A figure in the
  wrong units is not a figure to evaluate. It is never silently rescaled: `6.6`
  could be a misreported 6.6% or a real 660%, and picking one would be vss
  deciding what the source said. The bands are asymmetric where the arithmetic
  is — a margin cannot exceed 100%, but a pre-revenue name can lose many times
  its revenue. Full contract in `reference/SPEC.md` §2.
- **`op_income / revenue` must equal `op_margin`** to within 0.1pp, or the
  watchlist fails to load. This is not arithmetic hygiene: it catches a quarter
  assembled from two different *measures*, which is otherwise invisible once
  the numbers are in the file. It is also the only check that catches a
  negative percentage margin, since `-3.1` sits inside a band that must stay
  open for genuine deep losses.
- **A table row survives flattening as a row.** Two faults made the provenance
  rule unsatisfiable from a real EDGAR statement table: cells were joined with
  nothing between them (`1,3921,900`, in which 1,392 is not a number under any
  reading), and a cell holding a `<div>` split the row across two lines, so the
  label had no figure and the figures had no name. A `<tr>` is now one line,
  cells separated by spaces.
- **`--text-file` flattens markup, exactly as `--url` does.** The two paths had
  diverged, so a saved EDGAR exhibit passed to `--text-file` reached the model
  as 286KB of tag soup and the figures were whatever survived it. Both go
  through one function now, and a test asserts the two produce identical text
  for the same document.
- **No Operating income line? Use EBIT.** NIKE never reports one — its
  statement goes from gross profit and overhead to "Income before income
  taxes", with operating profit only in a non-GAAP EBIT table at the foot of
  the release. The prompt takes the total EBIT row as `op_income` and "EBIT
  margin" as `op_margin`, marks both `adjusted`, and names the two lines that
  are never substitutes: "Income before income taxes" is struck after interest
  (650 against EBIT 635 in Q3 FY26) and "Gross margin" is a different line
  (40.2% against EBIT margin 5.6%). The extractor took both before the rule
  existed. It also says to quote the label line *and* the number line together,
  because these tables flatten with the row label on one line and its figures
  on the next.
- **`--period YYYY-Qn` reads a comparative column.** A figure is sometimes
  stated only in a *later* filing: SAP's Q2 2024 restructuring of −631 appears
  in the Q2 2025 statement's comparative column and nowhere in the Q2 2024
  release, because the line was not broken out at the time. The flag tells the
  extraction which period to take, requires the comparative column to be named,
  and forbids falling back to the document's own quarter. The alert's PRIMARY
  SOURCE is then the filing that actually contains the figure — which is the
  point: attributing it to a release that does not state it would be a
  provenance fiction.
- **A ticker declares how often it reports, and its periods may not overlap.**
  `reporting_frequency: half_yearly` on a watchlist entry (default
  `quarterly`) means the ticker stores `YYYY-H1`, `YYYY-H2` and `YYYY-FY`
  periods instead of `YYYY-Qn`, and FRAMEWORK §4.2's windows — stated in
  quarters because US names report quarterly — are counted in half-years,
  converted by *time*: trailing 8 quarters → 4 half-years, trailing 4 → 2,
  the YoY look-back is 2 periods, and "2+ consecutive quarters" is the same
  six months, i.e. one half-year (so the run-length kills fire on a single
  half-year observation; `rules.py` says so where it happens). The
  **overlap guard** applies to every ticker: no two loaded periods may cover
  the same month — `2025-FY` contains `2025-H1`, `2025-H1` contains
  `2025-Q1` — and the guard keeps the *finest* resolution and never both.
  In the loader an overlap is fatal and the message names the label to
  remove; in `vss earnings` an extracted period is **admitted, displaces**
  a loaded coarser period for the evaluation (the alert says what to
  remove before pasting), or is **rejected** and not proposed when a finer
  period is already loaded or the label kind does not match the ticker's
  frequency. A re-read of an already-loaded period now displaces the
  stored row instead of sitting beside it — appending it counted one SAP
  guidance cut twice. Year-over-year comparators are found **by label**
  (2026-H1 ↔ 2025-H1), so a gap or a mixed FY/H history yields CANNOT
  EVALUATE rather than a comparison of unlike periods.
- **`class_c_impact` is defined in the prompt**, with its sign convention. Ten
  SAP extractions captured no restructuring line at all because the field was
  listed but never explained. It is a quantified one-off stated on its own
  line; the sign is its effect on reported operating profit, copied from the
  statement — a charge negative (`−2,242`), a release positive (`+52`). It is
  never inferred from the gap between reported and adjusted figures, because
  that gap is a computation bundling other adjustments in with the one-off.
- **A quarter may declare its source.** `source: xbrl` on a `quarters:` entry
  exempts it from the op_margin reconciliation — and from that alone. The
  reconciliation existed to establish which line `op_income` came from, which
  `us-gaap:OperatingIncomeLoss` answers outright; XBRL has no margin tag, so
  demanding one would force a computed figure into the record to satisfy a
  checker. An `xbrl` entry that states a contradictory margin still fails, and
  the band check and unit-mix guard apply regardless. `source: release`, or
  blank, keeps every existing entry exactly as it was.
- **One ticker, one unit.** A history mixing XBRL rows (whole units) with
  release rows (millions) is out by 10⁶ while every per-row check passes,
  because each row is internally consistent. A 1,000× or larger jump in
  `revenue`, `receivables` or `inventory` between two quarters of one ticker
  fails the load as a UNIT MIX. `op_income` is excluded — it crosses zero and
  swings by orders of magnitude for real reasons.
- **`op_income` without `op_margin` is UNRECONCILED**, and fails the load.
  `op_margin` is what cross-checks `op_income`; without it nothing establishes
  which line the operating income came from, which is how 1,416 (income before
  taxes) was recorded where EBIT was 1,392. Record the margin the source
  states, or leave `op_income` blank too — never compute one to satisfy the
  check.
- **Adjusted vs reported: take the reported one, and say which.** Lindab's Q4
  2025 states an adjusted operating margin of 6.5% and a reported one of 3.1%.
  Where a report gives both, the unadjusted figure is extracted; where it gives
  only an adjusted one, that is taken and the run says so, because §4.2 was
  written against the reported figure. Each figure carries its `measure`.
- **Periods record `fiscal` or `calendar`.** Microsoft's fiscal Q4 2026 ended
  30 June 2026; calendar Q4 2026 is October–December. The label alone does not
  say which, so a period without a basis is flagged, and a watchlist mixing
  bases within one ticker fails the run — quarter ordering would otherwise
  break.

**`--compare` reads the source twice.** Same text, same model, two calls; any
field the two runs disagree on is set to null and both readings are shown. Two
readings that disagree are not a figure, and a guess that survives because it
was made first is worse than a blank — a blank says DATA MISSING, the guess
says nothing at all. Values and claims are compared, not quotes: two runs may
cite the same figure from the summary and from the statement and both be right.
Where they agree on a number but name a different column or measure for it, the
figure stands and the attribution is flagged. When they agree on everything the
alert says so, and calls it corroboration rather than verification — both runs
read the same text with the same model, and both can be wrong together.

Alerts say `4.2 POSSIBLE TRIP - VERIFY AGAINST SOURCE`, never "sell", and the
primary source URL is always the first fact in the alert.

**PDFs are read, and the text is labelled as a reconstruction.** Half the
holdings publish quarterly reports as PDF only, so `--url` and `--text-file`
both accept one (pypdf, text layer only). A PDF is recognised by its content
type, its magic bytes or a `.pdf` path — Lindab serves its interim reports from
a Cision endpoint with no extension in the URL, and that is still a PDF. A PDF
stores glyphs at coordinates, not rows, so every alert built on one carries a
source warning saying its table rows were reconstructed. A PDF with no text
layer — a scan — is refused rather than read as an empty release, as is one
that needs a password. A permissions-encrypted PDF, which is most IR PDFs, is
read normally — including AES-encrypted ones, which is why `requirements.txt`
asks for `pypdf[crypto]`: SAP's quarterly statement is AES-encrypted and bare
pypdf refuses it. Filings run long, so PDFs get their own size cap rather than
the press-release one.

**One host still needs a hand.** `sap.com` answers an automated request for its
own quarterly statement with `403`, whatever user agent is sent. vss does not
answer that by impersonating a browser; a `401`, `403` or `429` now says the
host refused a robot and points at `--text-file`, which reads a
browser-downloaded PDF the same way `--url` reads a fetched one. Lindab, whose
reports come from a Cision endpoint, fetches fine.

How well this works is a property of the file, not of the tool. A typeset
report comes out clean — Lindab's interim report gives up
`Net sales, SEK m 3,306 3,253 2 6,309 6,467 -2 12,696 12,854`, eight period
columns on one row, and a 10-Q's statement pages read the same way. A results
*slide deck* comes out as loose labels and half-numbers, and its figures are
dropped. Pass the report, not the deck.

The provenance rule does not soften for PDFs. When a table reconstructs badly
the number comes away from its label, the quote is a bare label again, and the
figure is dropped as `PROVENANCE UNVERIFIABLE`. Garbled input reaches the check
rather than being repaired ahead of it: a repaired row is the tool's reading of
the report, not the report.

Whitespace inside a flattened row means two different things — `4 120` is one
number in Stockholm and two columns in Omaha — so both readings are offered as
candidates, joined only where a thousands separator could sit (before exactly
three digits). That answers whether the quote *contains* the figure. *Which*
column it sits in stays a separate question, answered by `period_column`, and a
tabular figure without one is flagged `NOT RECORDED` whatever the file format.

## XBRL: `vss xbrl`

For a US filer, SEC publishes every tagged fact as JSON. No HTML to flatten, no
PDF to reconstruct, no model in the loop.

```bash
export VSS_SEC_CONTACT='vss/1.0 (you@example.com)'    # required; see below
.venv/bin/python -m vss xbrl --ticker NKE             # all 8 quarters, one call
```

**Provenance becomes stronger, not weaker.** Every figure arrives attached to
the tag it was filed under, the context period it covers and the accession
number of the filing that reported it — `us-gaap:RevenueFromContractWith
CustomerExcludingAssessedTax [2025-12-01..2026-02-28] 10-Q 0000320187-26-000037
filed 2026-04-01`. Nothing is quoted, summarised or inferred, so there is no
sentence to verify and no column to name.

**Everything else is unchanged.** DATA MISSING is still DATA MISSING: a field
whose tags the filer does not use stays blank. NIKE tags no
`OperatingIncomeLoss` — it publishes no operating income line — and this path
will no more substitute `IncomeLossFromContinuingOperations…` or `GrossProfit`
than the extraction prompt will. `op_margin` has no tag at all and is left
blank rather than computed from `op_income ÷ revenue`. The reconciliation and
band checks run on the proposed entries exactly as they do on extracted ones.

**SEC's access policy is followed, not worked around.** They require every
automated caller to declare a real contact address. `VSS_SEC_CONTACT` supplies
it and the API is not called without it — vss neither invents one nor pretends
to be a browser. (`www.sec.gov` refuses this host outright, whatever the agent;
`data.sec.gov` is a different edge and answers normally.)

**Where the operational settings come from (`vss/env.py`).** `VSS_SEC_CONTACT`,
`NTFY_TOPIC` and `VSS_OPENROUTER_KEY` are read from **the environment first,
then from `~/.config/vss/vss.env`** — the same file the systemd units already
name in `EnvironmentFile=`. Until 2026-09-09 only systemd read it, so a session
at a terminal was told the variables were unset and asked for them again every
time; they were on disk the whole time. **The environment still wins**, so the
file is a default and never an override, and it is never written, logged or
printed. A missing or unreadable file means "unset", which is the state the
caller already knows how to describe.

**Two things the mapping handles that a naive one gets wrong.** SEC's `frame`
field is calendar-based — it labels NIKE's September–November quarter
`CY2024Q4` — so periods are derived from the filer's own year end (31 May)
instead, giving fiscal `2025-Q2`. And tag preference is per *period*, not per
company: NIKE left `InventoryNet` in 2011 for the finished-goods element, so a
tag with data somewhere must not shadow a tag with data here.

**Units differ from the press release** and are not rescaled: XBRL says
`11,279,000,000` where the release says `11,279` million. Both are what their
source states. Do not mix the two within one ticker's history — the report says
so at the top, every time.

The `cik:` watchlist key supplies the filer's CIK. It is MANUAL, because SEC's
ticker→CIK file lives on `www.sec.gov`, which will not answer.

### FRAMEWORK §4.2 coverage

| Rule | Needs |
|---|---|
| 4.2.1 revenue declining 2+ quarters (YoY) | `revenue_yoy` |
| 4.2.2 op margin −150bps YoY, flat/declining revenue | `op_margin`, plus `class_c_impact` + `revenue` to exempt **to the extent it explains** |
| 4.2.3 2+ guidance cuts in 4 quarters | `guidance_action` |
| 4.2.4 3+ EPS misses in 8 quarters | `eps` + `eps_consensus` (manual only) |
| 4.2.5 net debt/EBITDA > 3.5x or covenant proximity | `net_debt_ebitda`, `covenant_headroom` |
| 4.2.6 CEO **and** CFO departure in 12 months | `exec_changes` |
| 4.2.7 receivables/inventory > 1.5× revenue growth, 2+ quarters | `receivables`, `inventory` |
| 4.3 soft flag: 3+ sequential declines | `revenue` |

Every rule returns TRIP, NO_TRIP or **CANNOT_EVALUATE naming the field it
lacked** — absent history is never silence. A YoY comparison that would mix
constant-currency with reported figures refuses with BASIS MISMATCH rather than
computing a number that means neither.

The 4.3 sequential soft flag exists because YoY alone misses a name eroding
quarter on quarter while lapping a weak base. It is reported separately and
labelled, so it can never read as a hard kill.

---

## Nordic reports: `vss nordic`

Downloads the documents an issuer filed with its exchange, and records where
each one came from. **It reads nothing out of them.** The figures come out by
hand, into `config/manual/<TICKER>.yaml`, each carrying the page it was read
from — between an automatic downloader and an automatic extractor lies the
whole difference between "the tool fetched the report" and "the tool decided
what the report says".

```bash
# once per issuer: the service has no company directory, so the mapping is
# established by search, confirmed by eye and stored.
.venv/bin/python -m vss nordic --ticker PNDORA.CO --resolve "Pandora" --language en --write

.venv/bin/python -m vss nordic --ticker PNDORA.CO                       # every release with a document
.venv/bin/python -m vss nordic --ticker PNDORA.CO --reports             # report categories only
.venv/bin/python -m vss nordic --ticker PNDORA.CO --download 1457989 --attachment 1 --period 2026-Q2
```

**`config/nordic_issuers.yaml` is the mapping**, resolved once and stored — a
ticker is not re-resolved on every call, because resolution is a full-text
search whose answer a human has to confirm. The watchlist calls `PNDORA.CO`
"PANDORA"; the service calls it `Pandora A/S`. A search for "Pandora" on
Copenhagen also returns Royal UNIBREW, Bang & Olufsen and — the market filter
being loose once `freeText` is present — Boozt AB from Stockholm. Candidates
are shown with hit counts; the owner picks. `--write` backs the file up first
and never replaces an entry.

**`--period` is MANUAL and required to download.** Nothing in the feed says
which fiscal period a document covers: the category is a filing choice, the
headline is prose, and the release date is when it was published. It uses the
same labels as the watchlist's `quarters:` and `config/manual/<TICKER>.yaml`,
so a document and the figures read out of it carry one label between them.
(Only the *shape* is checked — a quarterly reporter still publishes an annual
report, so `2025-FY` is right for PNDORA.CO.)

**Four things the feed does that a naive client gets wrong**, all measured and
all encoded (see `reference/FETCHER-SURVEY.md`):

- **The category is the issuer's filing choice, not a statement about
  content.** Pandora's H1 2026 report — *"Pandora delivers 3% organic growth
  in Q2"*, 2026-08-12 — is filed under `Inside information`. A category
  whitelist misses it, so `--reports` prints how many rows it hid and says
  why. The default listing shows everything carrying a document.
- **`cnscategory` takes one value and silently ignores several**, returning
  the unfiltered feed — which reads as "every release is a report".
  `fromDate`/`toDate` are accepted and ignored outright. Neither is ever sent;
  filtering happens on rows you can see.
- **`limit` caps at 200 and pagination is `start`, not `offset`.** A
  listing shows one page; `--download` walks the whole feed until it
  finds the id, bounded by the feed's own count and logging each page.
  Backfilling eight periods means reaching reports several pages back —
  Pandora's feed carries 1,027 releases — and guessing `--start` until
  an id appears would make the one thing this exists for a manual search.
- **One disclosure can carry several files and the first is not the report.**
  Betsson's 2026 annual filing puts an ESEF/iXBRL package at index 0 and the
  PDF at index 1; Pandora's attachment order varies between filings. Where
  there is more than one, `--attachment N` is required and nothing is guessed.

**`sources/manifest.json` is the provenance record** and is the one file in
`sources/` that git tracks — the documents are large and re-downloadable from
the URL each entry names. Per download: the URL, the disclosure id and message
URL, the exchange's category, byte count, SHA-256, and when it was fetched. A
file with **no** entry has `PROVENANCE NOT RECORDED` — a third state, not
"secondary", and the `sources/` documents that predate this command are not
back-filled with guesses. Re-downloading identical bytes is a skip; bytes that
**differ** fail the run and name both digests rather than overwriting. A
file on disk whose manifest entry is missing — deleted record, or a run
that died between writing the file and writing the entry — has the entry
written back rather than being left to read as unrecorded for ever.

### Oslo: `.OL` goes to Euronext's NewsWeb, not to Nasdaq

Oslo Børs is Euronext and is not on the Nasdaq service. `vss nordic`
**dispatches on the suffix** — a `.OL` ticker is served by `vss/oslo.py`
against **NewsWeb**, the Norwegian Officially Appointed Mechanism, so the
document fetched is the one the issuer filed and not a copy of it on an IR
page. Same command, same `sources/manifest.json`, same `--period` discipline.

```bash
.venv/bin/python -m vss nordic --ticker BOUV.OL --resolve "Bouvet" --write
.venv/bin/python -m vss nordic --ticker BOUV.OL --reports
.venv/bin/python -m vss nordic --ticker BOUV.OL --download 659260 --attachment 1 \
    --period 2025-Q3 --language en
```

**`config/oslo_issuers.yaml` is the mapping, and it is a SEPARATE file from
`config/nordic_issuers.yaml` on purpose.** That file answers "is this name on
the Nasdaq Nordic feed", which `vss refresh` asks in order to pick a route; an
Oslo name in it would make that question answer yes about a service that has
never heard of the company.

**Four things this feed does differently**, all measured 2026-09-08 and all
encoded (`vss/oslo.py`'s docstring carries the measurements):

- **It has a company directory and Nasdaq's has none.** `POST
  /v1/newsreader/issuers` returns every issuer — 1,622 rows — with its
  `issuerSign`, `issuerId` and name. So `--resolve` here is a LOOKUP against
  the exchange's own list rather than a full-text search over release bodies.
  The owner still confirms and stores it.
- **An issuer sign the service does not know is SILENTLY IGNORED**, and the
  whole market's feed comes back under HTTP 200 — 601 rows from 250-odd
  companies, looking exactly like this company's history. Every row's sign is
  checked against the one asked for and a page carrying anybody else is
  **refused**, never filtered down.
- **There is no `start`, `offset` or `limit`; a window is the page.** It caps
  at ~601 rows and says `overflow: true`. A longer history is a narrower
  window, and the truncation is printed rather than swallowed.
- **Every report is filed twice, in Norwegian and English, as two separate
  messages, and no field says which is which.** So `--language` on an Oslo
  download is a **manual label** — like `--period` — recorded in the manifest
  as stated by the owner and not read off the feed. It is never a filter.

**Correcting a note in `sources/manifest.json`:** the NHY.OL entries of
2026-08-30 say NewsWeb's attachment endpoint *"answers HTTP 400 to every
automated request"*, and Norsk Hydro's reports were taken from hydro.com
instead. Measured again on 2026-09-08, `api3.oslo.oslobors.no/v1/newsreader/
attachment` answers **HTTP 200** and serves the PDF; the `obsvc` path on the
`newsweb.oslobors.no` host — a different endpoint — returns an HTML page and
is the likely subject of the old note. **The old entries are not rewritten:**
they record what was measured on the day they were written.

## Figures appendix: `vss appendix`

Some Nordic issuers attach a spreadsheet of the numbers to every interim
release — Pandora's runs to ten sheets and the consolidated statements quarter
by quarter. **A cell is a number**, so this is not PDF extraction. But *which*
cell answers which field is a judgement, and a close one: Pandora's balance
sheet says `Cash` while its cash-flow statement says `Cash and cash
equivalents, end of period`, and the two are different figures.

So the mapping is a committed file, `config/manual/maps/<TICKER>.yaml`, one
entry per schema field naming the sheet and the **row label** — with a `note:`
wherever the choice is not obvious.

```bash
.venv/bin/python -m vss appendix --ticker PNDORA.CO     --xlsx sources/PNDORA.CO_2026-Q2_inside-information_2026-08-12_en_a0.xlsx
# ... then --write to put it in config/manual/PNDORA.CO.yaml
```

**The label, never the index.** Nothing counts rows, so a row inserted next
year breaks the run loudly instead of shifting every figure by one. Labels
compare exactly after stripping surrounding whitespace and nothing else — this
workbook appends footnote markers to some labels, and a marker appearing on a
mapped label is a change that should stop the run. Where one label matches
twice, `section:` (the heading of the period block) and `after:` (a label that
occurs once, above) disambiguate; an anchor that is itself ambiguous is
refused, and a label still matching twice stops the run naming every row.

**Nothing is derived.** No row is summed with another, no missing line is
inferred from its neighbours, nothing is rescaled. Pandora states `Finance
income received` and `Finance costs paid` separately, so `net_interest_paid`
stays absent. A `-` or a blank cell is `DATA MISSING`, never zero.

**Periods are matched across sheets by label, not by column position** — and
because `op_margin` comes from a different sheet than `revenue` and
`operating_income`, `config.unit_problem`'s margin reconciliation then checks,
every period, that the two sheets were paired to the same quarter. That is the
strongest validation this path gets and it is free. The emitted file is parsed
back through the manual loader *before* anything is written.

**Every figure lands `UNVERIFIED`** and `origin: nordic-xlsx`, distinct from
`manual` and from `xbrl`, carried through to `ranking.csv`. Section 5 still
refuses until you have read each figure back. Writing **refuses when the file
exists**, naming how many `VERIFIED` figures would have been lost; `--force`
replaces it after a backup. Whether a re-run should *merge* is a rule question
and not decided here.

## Manual fundamentals: `vss manual`

`vss xbrl` needs a CIK. **On the 2026-08-21 screener run 347 of the 533
filter-1 candidates carry a foreign listing suffix**, and for most of a
Stockholm or Copenhagen list there is no SEC endpoint at all — so the §5 chain
has no primary-source input and the ranking key has only what the quote vendor
returned. This is the third source: figures the owner read out of the
company's own report and typed in.

**Not every foreign name is one of them.** A foreign private issuer files a
20-F and *is* on `data.sec.gov`: SAP.DE's A7 proxy was built from its 20-F
XBRL and UNA.AS's from CIK 217410, accession `0000217410-26-000007`. **Try
`vss xbrl --cik` first** — this path is for the remainder, the names that have
no CIK to try. How many of the 347 that is has not been counted: SEC's
ticker→CIK file lives on `www.sec.gov`, which refuses this host.

```bash
cp config/manual/TEMPLATE.yaml config/manual/PNDORA.CO.yaml   # then fill it in
.venv/bin/python -m vss manual --ticker PNDORA.CO --asof 2026-08-24
```

**Every figure carries a page and a status.** `source` (the period's
`document:` unless the figure names its own), `page`, and `UNVERIFIED` or
`VERIFIED`. A value with no page fails the load, and a bare `revenue: 1234` is
refused rather than read — it could carry neither.

**The same three checks the SEC path gets**, plus a fourth that only a
hand-entered file needs:

- **unit** — `config.unit_problem`, the watchlist's own function: ratio fields
  inside their bands, and `op_income ÷ revenue` reconciled against `op_margin`.
  `source: xbrl`'s exemption from the reconciliation is **not** extended here:
  a us-gaap tag says which line an operating income is, and a pair of eyes on
  a PDF does not.
- **one scale** — a stable money line jumping a round thousandfold between two
  periods is a unit mix, not a business event.
- **STALE** — on `fundamentals.MAX_REPORT_AGE_DAYS`, in the same sentence the
  fetch uses, and measured **on the rows §5 actually reads**: a period entry
  carrying only `net_ppe` must not make an old file read fresh (`ranking.py`
  rule 5).
- **one fiscal period per ratio** — every ratio §5 forms takes all its legs
  from ONE period entry; a leg present in an earlier period is not borrowed.
  Two periods are not one ratio.

A leg that is in **no** period is `input missing` — reported, not refused,
because absence is the ordinary third state. Only legs that exist and sit
apart refuse. And the ranking key's own quality leg never refuses §5: gating
on it would bar every bank, whose accounts present no gross profit by design.

**Two blocks hold figures.** `periods:` holds one entry per fiscal period at
the resolution the company reports. `annual:` holds what it publishes only once
a year — diluted EPS, share counts, leverage ratios (FRAMEWORK-EDITS E15). The
annual block is excluded from every trailing window: never summed, never
combined with a period entry, and it never reaches the ranking key, which reads
a trailing twelve months from `periods:` alone. Where a figure is in **both**,
`periods:` wins and the annual entry is ignored — the load says which ones.

**Section 5 refuses to run on an unverified figure** — the command exits 1 and
says so. `UNVERIFIED` is not the same state as absent: an absent figure is
`DATA MISSING` and has nothing to check, so an unverified one is named in the
report with its period, its source and its page. The **ranking key is not
gated on it**: it is a different consumer, it produces review work rather than
a price, and it says `DATA MISSING` for itself.

**Nothing here computes a fair value.** §5.1's three methods stay by hand in
the per-name workbook. This decides only whether their inputs may be used.

**Origin is stamped on every path.** `manual` here, `yfinance` on the vendor
fetch; `ranking.csv` carries an `origin` column, and `source: manual` is a
valid `quarters:` marker for a row the owner read themselves.

## Screener: `vss screen`

Phases 1 to 3, 5 and 6: it builds the universe, snapshots its prices, runs the
exclusion list and the dislocation band, fetches fundamentals for the
survivors, applies a coarse quality filter, and ranks what is left on
Greenblatt's two components. It never writes to `config/watchlist.yaml`. The
design and the plan for phases 4, 6 and 7 are in `reference/SCREENER.md`.

```bash
python -m vss screen --universe-report
python -m vss screen --snapshot-only --asof 2026-08-21
python -m vss screen --filter1 --asof 2026-08-21
python -m vss screen --fundamentals --asof 2026-08-21
python -m vss screen --filter2 --asof 2026-08-21
python -m vss screen --rank --asof 2026-08-21
python -m vss screen --rank --write-pipeline --asof 2026-08-21
```

The screener produces **review work, never a purchase**. Its eventual output is
three to five `PIPELINE` names carrying neither `mbp` nor `fv_base`, after
which the FRAMEWORK section 5 chain is run by hand.

`config/universe/` holds static, dated CSVs -- index membership is never
fetched at runtime. Nine columns:

```
ticker_yahoo, ticker_lokal, isin, namn, marknad, tier, listdatum, valuta, instrumenttyp
```

A malformed row aborts the run, exactly as a malformed watchlist entry does.
`ticker_yahoo`, `isin`, `namn`, `listdatum`, `valuta` and `instrumenttyp` may be
empty; that is DATA MISSING and it is counted, not ignored.

Exclusions (ETF, fund, preference share, SPAC, trust, ADR) read `instrumenttyp`
-- the source list's own field -- and never the name string. The vocabulary and
the policy for an unknown type live in `config/universe/instrument_types.yaml`.
Tier floors live in `config/universe/floors.yaml`, and every monetary threshold
carries its own currency because the universe spans some fifteen of them.

Every run writes `data/screener_snapshots/<ASOF>/snapshot.sqlite` holding raw
daily OHLCV -- never computed metrics -- plus the universe, the rejections, the
merges, the per-step tallies and a fetch status for every ticker. The manifest
records the sha256 of each universe file, so a later replay can prove it is
reading the same lists. `--asof` truncates the series, so re-running a Friday
on the following Monday reproduces Friday.

Every ticker leaves the fetch with one of four statuses, and `THROTTLED` and
`NO_DATA` are deliberately not merged: the first means retry later, the second
means the symbol mapping is wrong. `STALE` is decided afterwards by
`rules.stale_close_blocker`, the same gate `vss run` uses.

`--filter1` reads a stored snapshot and fetches nothing. Step 0 is
`config/screener_exclusions.csv` -- names already owned or already decided,
matched on `ticker_yahoo` exactly, never on name. Entries matching nothing are
reported as inert, since an inert entry that reads as active is how an excluded
name quietly comes back. Filter 1 is the dislocation band, imported from
`rules.in_dislocation_band`; candidates land in
`data/screener_runs/<ASOF>/filter1-candidates.csv` ordered by ticker, which is
an order and not a ranking.

`--fundamentals` fetches only the survivors of filter 1, one ticker at a time,
and stores them beside the price snapshot. Status is recorded per ticker AND
per field: a bank returns cash and debt but no EBITDA, and a ticker-level `OK`
would hide the gap. `--filter2` then applies coarse quality -- positive free
cash flow, net debt/EBITDA, revenue trend -- with the thresholds in
`config/screener_filter2.yaml` rather than in code, each citing its FRAMEWORK
section.

`--rank` then applies the ranking key of FRAMEWORK-EDITS E6: gross
profitability (gross profit / total assets, after Novy-Marx 2013) and earnings
yield, ranked separately, the placings summed. It is the only ordering the tool
produces, and it is still review work rather than advice. Names that cannot be
ranked on the quality leg -- financials, property, and any name missing a line
-- are ranked on earnings yield alone in their own section, never interleaved.
E6 replaced E5's Greenblatt ROIC because that denominator went to zero for
asset-light businesses and its top thirteen placings were held by the thirteen
names closest to the pole. Exchange rates are fetched once per run per pair and printed in
the report; a London name quoted in GBp carries its enterprise value in GBP,
and that scaling has its own tests.

`--write-pipeline` enters the top names as `PIPELINE` with no `mbp`, no
`fv_base`, no `tier` and no stop. It backs the file up first, appends as text
so the hand-written comments survive, re-parses afterwards and restores the
backup if the file stopped loading, and never touches a ticker already there.
Share classes of one company are collapsed before ranking on measured identity
-- one set of accounts means one company -- keeping the most traded listing.

Both phase-3 reports carry a look-ahead banner: yfinance serves historical
prices but only the LATEST fundamentals, so a replay pairs today's accounts
with an older price and is not evidence of what a screener would have found
that day.

**RSI and SMA50 are fields, never filters.** Recomputed on the frozen SAP.DE fixture: on the
2026-07-23 low SAP closed 128.32 with RSI 34.1, 10.9% below its SMA50; on the
2026-07-27 purchase 151.28 with RSI 62.3, 5.0% above it. An SMA50 filter
discards one of those two days whichever way it is pointed, and no RSI band
catches both.

---

## Sales record: `vss sales`

FRAMEWORK-EDITS B45. Every fill booked in a watchlist entry's `sales:`
block, set against the last settled close and against OMXS30 (`^OMX`) and
the S&P 500 (`^GSPC`) from the index's close on the sale date, plus fixed
30/90/365-day marks once each has settled, and a by-rule table.

```bash
.venv/bin/python -m vss sales              # writes reports/SALES-RECORD-<date>.md
.venv/bin/python -m vss sales --dry-run    # print only
```

One item per executed transaction:

```yaml
    sales:
      - date: 2026-08-26
        price: 178.06          # optional: absent is DATA MISSING, never read off a bar
        currency: EUR          # defaults to the entry's currency
        shares: 5
        account: "ACCOUNT-A"
        rule: C4               # C1 | C2 | C3 | C4 | owner
        run_record: reference/run-records/SAP.DE-2026-08-26.json
        proceeds_sek: 9841.22  # what landed, net of charges and FX -- not blended with the price return
        note: "..."
```

## Shadow book: `vss shadow`

FRAMEWORK-EDITS E114. `vss sales` measures the positions the framework
SOLD; this measures the ones it never bought. Every `DROPPED`,
`WATCH-GATED` and `INTAKE` verdict in `config/shadow_book.csv`, set
against OMXS30 (`^OMX`, a PRICE index -- `^OMXS30GI` carries no history
at the vendor) and the S&P 500 (`^SP500TR`, total return), both converted
into the name's own quote currency, at 1, 3, 6 and 12 months from the
verdict date.

**Every comparison is a TOTAL return on both sides** (limit three, amended
2026-09-09): the name's dividends are reinvested, and a name whose
dividends the vendor does not record is DATA MISSING rather than a price
return set against a total-return benchmark. The book STORES the
unadjusted close, which never restates and is the recorded fact; the
total return is DERIVED beside it from a series that does restate, and
the report says so and re-reads every stored baseline against the vendor.
The OMXS30 leg is the one remaining mismatch and is labelled a price
index wherever it appears -- a stated substitution is honest, a silent
one is not.

**It is not a signal.** Nothing in it arms an alert, enters a name or
reaches a valuation, and no other module imports it. E114 has it read
once a year.

```bash
.venv/bin/python -m vss shadow             # writes reports/SHADOW-BOOK-<date>.md
.venv/bin/python -m vss shadow --dry-run   # print only
```

One row per verdict, and exactly nine columns -- E114's six facts plus the
two that say where the row came from:

```csv
ticker,verdict_date,verdict,standing,close,currency,fv_base,decided_by,source
DECK,2026-08-24,WATCH-GATED,EXPIRY,92.08,USD,,"Gate 1's catalyst limb ...","config/watchlist.yaml note (WATCH 2026-08-24)"
```

`verdict` is `DROPPED` | `WATCH-GATED` | `INTAKE`; `standing` is
`STANDING` (holds until deliberately removed) | `EXPIRY` (re-read when a
named event arrives) | `OPEN` (nothing decided yet, which is what E111's
INTAKE means). **`close` is the SETTLED close on the verdict date and is
never the nearest bar.** A verdict written on a **weekend** is re-dated
to the last weekday on or before it and the row says which date it moved
from and to (limit four); a **weekday** with no bar is left where it is
and prints DATA MISSING, because an exchange holiday and a vendor gap
look the same from here. `tools/backfill_shadow_book_2026_09_08.py` built
the first book, applies the re-dating rule, and fills a blank on a re-run
once the session settles.

## The overview page: `vss overview`

`reports/OVERVIEW.html` — **the state of the book on one page**, regenerated
by the nightly run and by hand on demand. One file, no server, no framework,
**no JavaScript at all**. It opens from disk with a `file://` URL and loads
instantly, and it is built to be read on a phone.

**A PAGE SCANNED IN TEN SECONDS, THEN READ INTO.** It answers three
questions in order and puts everything else below them or behind a plain
`<details>`:

1. **Does anything need me today?** One block at the very top, in plain
   sentences: *nothing*, or the two or three things that do — a maximum buy
   price crossed, a stop breached, a holding with no stop, a dated event
   inside the next seven days. **The list of kinds is closed**: a top line
   that grew a fourth and a fifth category would be a second report. Beside
   it, always, **what was checked** — *nothing needs you* and *nobody
   looked* are the same silence otherwise. A level that could not be
   checked (an MBP with no settled close) says so rather than passing as
   held.
2. **Where is everything against its value?** **One card per name**, in a
   grid that reflows to one column on a phone — a table is for comparing
   forty things, a card is for recognising one. Ticker and company small at
   the top, **the price large**, fair value and the maximum buy price beside
   it in smaller type, then two pictures:
   * **a sparkline** — 52 weeks of settled closes as inline SVG, drawn from
     the cache and never fetched, with the fair value as a dashed line and
     the MBP as a dotted one. A level is drawn **only where it falls inside
     the year's range**; one outside is said in words underneath instead,
     because stretching the range to reach it would show a year of trading
     as a flat smear (MUSA's fair value is a third of its 52-week low). A
     series that is short or missing says so rather than drawing a lie.
   * **the value track** — the price as a position between **half the fair
     value and half again**, fair value dead centre, a short mark where the
     MBP is struck. The scale never rescales per name, so the cards read
     against each other; a price past either end sits **on** the end and
     the card says which end.

   **A picture never replaces a figure**: the close, the fair value, the
   MBP and both distances are printed on every card, small but exact.
3. **What is coming?** The unresolved `catalyst_date`s from today onward,
   nearest first, with what each decides. A long note shows its first
   sentence and folds the rest — **never truncated**, because an ellipsis
   on a record is a record nobody can read.

**Behind a click:** the full queue (single-action items first, the rest
folded), the timeline (**the last ten of 230** — an archive is not a view),
the shadow book, per-name document links, and anything that could not be
read. Every disclosure's summary states the count, so nothing is hidden
without saying how much.

**TYPOGRAPHY DOES THE RANKING, AND SURFACES DO THE SEPARATING.** The number
that matters is large and its label is small and muted; every figure is
monospace with tabular numerals so digits line up down the grid. Things are
told apart by background and space — **no card borders, no row rules, no
visible table grid.** The one hairline on the page is above the footer,
which is a boundary rather than a division, and a test enumerates every
`border` declaration in the stylesheet and fails at a second.

**GREEN AND RED ARE A MEASUREMENT OF DISTANCE, NEVER A VERDICT.** Green is
at or below the level, red is far above it, neutral between — five bands
whose boundaries are the framework's own (0% is the level; 5% is `rules`'
APPROACHING band; then 25% and 75%). **It says how far, not whether to
act.** It is applied to the distance figures, to the dot on the value track,
and to the stretch of the sparkline that traded below fair value — and
**never to the whole card**, because a green card reads as approval.

**A CHEAP GATE-CLOSED NAME MUST NOT READ AS AN INVITATION.** A DROPPED or
WATCH-GATED name's distance is drawn muted whatever the number says, and
the card states the status in words beside it: *Distance shown muted:
WATCH-GATED — re-entry is on a named information event, never on a price
level.* Names E51 or E96 put outside the circle are muted on the same
ground, recorded as an extension of it. The **shadow book is never toned**:
its columns are returns since a verdict, not distances to a level, and a
dropped name that rose is not green.

**THE ACCENT AND THE DISTANCE SCALE NEVER TAKE EACH OTHER'S ROLE.** The
accent is a **surface** — it fills the block at the top of the page and
nothing else, and a test counts its uses in the stylesheet and fails at
two. The distance scale is **ink**, colouring figures and marks on cards.
A name can be green and need nothing (ACN is), and a name that needs the
owner can be red (a breached stop would be). No `.attention` rule mentions
a distance tone and no distance rule mentions the accent, and a test
asserts both.

**NO COLOUR ANYWHERE CARRIES MEANING ON ITS OWN.** Every toned figure keeps
its sign and its number and carries its band as a title; every card states
its band and its mute in words; the sparkline's two level lines are told
apart by **dash pattern** and it carries an `aria-label` saying in words
what the drawing says in shape; every refusal prints `DATA MISSING` with
its reason. A red-green colourblind reader loses nothing.

**READ-ONLY, AND THAT IS THE WHOLE DESIGN.** No form, no button, no request
and no script — tests assert each is absent. Disclosure is
`<details>`/`<summary>`, which the browser gives for free. Every decision
this project makes is a dictated ruling in a session, and a page that could
take one would be a second place decisions come from.

**THE FOOTER SAYS WHEN AND FROM WHICH RUN**, so a stale page cannot read as
current: when the page was generated, when the last **completed** nightly
run finished and what it covered, and separately when the prices on the page
were cached. The two are separate facts — a hand fetch moves the second
without moving the first — and where the dead man's switch says the run has
gone quiet, that line is in the footer too.

**IT SHOWS THE STATE; THE DOCUMENTS CARRY THE EVIDENCE.** Per name it links
the briefing, the reading, the strike document, the run record, the growth
view and the store, and it **never summarises one** — a summary of a sourced
document is a judgement without its sources. A test reads the briefings and
asserts none of their prose appears on the page.

**EVERY FIGURE IS READ AT GENERATION TIME AND NOTHING IS STORED TWICE.**
`config/`, `reference/` and `data/` are the record; the page is a view of
them and holds no state. It **never fetches** — prices come from the cache
the nightly run writes, settled bars only.

**A FIGURE THAT CANNOT BE READ PRINTS `DATA MISSING` AND KEEPS ITS ROW**,
with the reason where the figure would have been. An absent row reads as
*nothing to see*, and that is the failure mode the page exists to remove.

**NO ARITHMETIC CROSSES A UNIT SEAM.** AUTO.L's `fv_base` is written in GBP
to match its linked run record while its close is quoted in GBX, and the
watchlist records that seam as OPEN. The first draft printed the distance
between them as **+10,543%**. Where the two currencies are not the same code
— or either is unstated — no distance and no position is struck, the seam is
named, and nothing converts: a conversion needs a rate, a rate needs a date,
and E24 freezes both onto the verdict rather than inventing them at render
time.

**IT NEVER CHOOSES.** Where several run records exist for a name and no
entry names one — LII has a `2026-08-30` record and a `2026-08-30-e70`
restrike of it — the value is `DATA MISSING` and both are linked. Which one
governs is E39's question and a filename sort must not answer it.

**WHAT IT WRITES:** `reports/OVERVIEW.html`, and nothing else, anywhere. A
test takes a census of `config/`, `reference/`, `data/`, `vss/`, `tools/`
and `tests/` either side of a real generation and asserts not one byte
moved. The nightly run regenerates it after the report is on disk; a
**scoped** (`--ticker`) run does not, and a failure there is logged at
WARNING and never fails the run.

`vss/overview.py` reads the record and produces the figures;
`vss/render.py` is the HTML and the stylesheet, and nothing else imports it.

## The watchlist

One entry per ticker. All fields MANUAL. See
`config/watchlist.example.yaml`.

| Field | Required | Meaning |
|---|---|---|
| `ticker` | yes | yfinance symbol, e.g. `VOLV-B.ST`, `RHM.DE`, `MSFT` |
| `name` | yes | display name |
| `currency` | yes | trading currency, display only |
| `hurdle` | no | E29's frozen hurdle rate on a purchase verdict — `rate`, `core_expected_return`, `premium`, `rate_as_of`, all four or none |
| `status` | yes | `HELD` \| `WATCH-PRICED` \| `WATCH-GATED` \| `PIPELINE` \| `DROPPED` — the bare `WATCH` was split by FRAMEWORK-EDITS E27 and is rejected |
| `reporting_frequency` | no | `quarterly` (default) \| `half_yearly` — sets the period labels the ticker stores and the unit its §4.2 windows are counted in |
| `fv_base` | for MBP | base-case fair value |
| `tier` | for MBP | `1` \| `2` \| `3` |
| `stop_price` | yes* | *absent = BLOCKED if HELD, flagged otherwise* |
| `catalyst_date` | no | `YYYY-MM-DD`, when the catalyst is/was due |
| `catalyst_resolved` | no | `YYYY-MM-DD`, the day you ingested the outcome |
| `catalyst_event` | no | what the catalyst is |
| `notes` | no | free text, prose only — the gate never reads it |

Validation is strict and always fatal to the whole run -- an unknown key, a
bad tier, a non-numeric price or a duplicate ticker stops everything rather
than silently skipping one entry. A silently dropped ticker is a worse
failure than a crash.

---

## Rules

### Metrics computed per ticker

Last close and its date, 52-week high, drawdown, RSI(14), SMA50, SMA200,
price vs each SMA, 20-day average volume, today's volume ratio, and percent
distance to both MBP and stop.

- **52-week high** is the highest daily *close* in the trailing 365 calendar
  days -- not the intraday high, which is jumpy and vendor-dependent.
- **Drawdown** = `(high_52w - close) / high_52w`, a positive fraction.
- **RSI(14)** uses Wilder's smoothing and needs at least 15 closes; fewer
  returns `DATA MISSING`, never a partial estimate.
- **SMA50/200** return `DATA MISSING` on insufficient history, never a
  shorter-window substitute.
- **Volume ratio** = today's volume over the mean of the *previous* 20
  sessions (today is excluded from the denominator).
- RSI is **reported only**. No verdict depends on it.

### The staleness gate

A ticker is BLOCKED when any of these hold:

| Blocker | Condition |
|---|---|
| `NO_DATA` | fetch failed and no cached data exists |
| `STALE_DATA` | newest close is older than **3 calendar days** |
| `CATALYST_UNRESOLVED` | `catalyst_date` is in the past and `catalyst_resolved` is not set |
| `NO_STOP` | `stop_price` is not set **and** the ticker is `HELD` |

**A blocked ticker prints its blocker reasons and no verdict, ever.** All
applicable blockers are listed, not just the first.

The 3-day window is *calendar* days, as specified. A run on a Tuesday
following a Monday market holiday will therefore block on Friday's close.
That is the gate erring toward flagging, by design.

### Verdicts

For non-blocked tickers only. Verdicts are **collected, not first-match-wins**
-- a holding under both its stop and its MBP reports both, so a stop breach
can never be masked by another rule firing first.

| Verdict | Condition |
|---|---|
| `STOP BREACHED` | `status == HELD` and `close <= stop_price` |
| `AT/BELOW MBP` | `close <= mbp` |
| `APPROACHING MBP` | `mbp < close <= mbp * 1.05` |
| `OUTSIDE DISLOCATION BAND` | drawdown outside `[0.15, 0.50]` |
| `NO STOP DEFINED` | not `HELD` and no `stop_price` — required before entry |
| `DATA MISSING` | a manual field the check needs is absent |
| `NO ACTION` | nothing above fired |

Boundaries are inclusive: exactly at MBP is `AT/BELOW MBP`; exactly at the
stop is `STOP BREACHED`; drawdown of exactly 0.15 or exactly 0.50 is *inside*
the band. `AT/BELOW MBP` and `APPROACHING MBP` are mutually exclusive.

A missing `stop_price` is treated by status. A `HELD` name is blocked --
there is an open position with no defined exit. A waiting name
has nothing to exit, so it is not blocked: it gets its normal MBP and
dislocation verdicts plus a `NO STOP DEFINED` flag, so a buy verdict is never
acted on before the §6.4 stop decision is made.

`DATA MISSING` is never `FAIL` and never `NO ACTION`. A missing input means
the check could not be evaluated -- the tool never substitutes a default to
avoid the state, and a check is never skipped silently. A missing field only
suppresses the checks that need it: an absent `fv_base` leaves the stop check
and the dislocation check fully evaluated.

### Data availability

Every fetch is cached under `data/cache/` as a CSV plus a JSON sidecar. When
yfinance fails, the cached frame is used and the freshness line says
**degraded**. Cached data still counts against the staleness gate -- the gate
reads the newest close *date* out of the price series, never the cache file's
fetch timestamp, so old data can never look fresh.

A ticker that errors with no cache gets an `ERROR` row in the table and a
`NO_DATA` blocker. It is never silently dropped.

The freshness line leads with the **oldest** close across the watchlist, not
the newest, so a single fresh ticker cannot make a mostly-stale watchlist read
as current.

---

## Scheduling (user-level systemd, 22:30 daily)

```bash
mkdir -p ~/.config/systemd/user
cp ~/stocks/deploy/vss.service ~/.config/systemd/user/
cp ~/stocks/deploy/vss.timer   ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now vss.timer
```

So the timer fires when you are not logged in:

```bash
sudo loginctl enable-linger $USER
```

Check and inspect:

```bash
systemctl --user list-timers vss.timer     # next scheduled run
systemctl --user start vss.service         # run once, now
journalctl --user -u vss.service -n 50     # last run's output
journalctl --user -t vss -f                # follow
```

Disable:

```bash
systemctl --user disable --now vss.timer
```

The unit runs `python -m vss run` from `~/stocks` with `Persistent=true`, so a
run missed while the machine was off happens at the next opportunity rather
than being skipped. It is sandboxed (`ProtectSystem=strict`,
`ProtectHome=read-only`) with write access only to `data/` and `reports/`;
this was verified with a real run, not just assumed.

---

## Tests

```bash
cd ~/stocks
.venv/bin/python -m pytest -q
```

`tests/fixtures/verdict-matrix/` holds an end-to-end verdict matrix: six
tickers whose synthetic manual fields place each close on a specific side of a
threshold, driving every verdict path at once. Its prices are frozen CSVs
captured 2026-08-20 and read offline, so a market move can never break it --
only a code change can. The fv_base and stop values in it are fabricated and
must never be copied into a real watchlist.

`tests/fixtures/earnings/berkshire-10q-2025-q2-excerpt.pdf` is the PDF path's
fixture: pages 2, 4 and 32 of a real public SEC filing (Berkshire Hathaway's
Form 10-Q for the quarter ended 30 June 2025). A real statement page carries a
hazard an invented one does not -- four period columns under a two-line stacked
header -- so the tests hold both halves of the provenance rule to it: the row
evidences the figures it contains, and a figure taken from it without a named
column is flagged. Two more shapes are pinned as strings observed live: an
eight-column row from Lindab's interim report, and the loose labels and
half-numbers a results slide deck extracts to.

The rest covers every rule in the metrics, staleness-gate and verdict layers
with fixture data, including the boundaries: exactly at MBP, exactly at the stop,
drawdown at exactly 0.15 and 0.50, RSI at exactly 30 and exactly 70, every
missing manual field, blocked tickers never receiving a verdict, and the
cache round-trip across a daylight-saving change.

---

## Layout

```
vss/
  rules.py     verdict + blocker logic -- PURE, zero I/O, no clock access
  metrics.py   numeric computations -- pure, pandas in, scalars out
  config.py    watchlist loading and strict validation
  fetch.py     yfinance + on-disk cache with outage fallback
  source.py    primary-source retrieval: HTML and PDF to text
  extract.py   LLM figure extraction + the provenance check
  earnings.py  `vss earnings` -- extraction to 4.2 evaluation to alert
  store.py     sqlite persistence of each run
  report.py    markdown rendering
  overview.py  `vss overview` -- the READ-ONLY page's figures, from the record
  render.py    the overview page's HTML and stylesheet -- no other importer
  runner.py    orchestration (all I/O lives here)
  universe.py  screener: the static universe -- schema, exclusions, dedup
  filters.py   screener: exclusion list, dislocation band, coarse quality
  fx.py        screener: exchange rates, once per run per pair
  ranking.py   screener: share-class collapse + the Greenblatt key
  pipeline.py  screener: phase 6 -- the only module that writes the watchlist
  fundamentals.py  screener: per-ticker fundamentals, two status layers
  manual.py    hand-entered fundamentals: schema, four checks, the 5 gate
  appendix.py  `vss appendix` -- an xlsx figures appendix through a cell map
  nordic.py    `vss nordic` -- report downloads from the exchange feed
  prices.py    screener: batched price retrieval, backoff, fetch statuses
  snapshot.py  screener: per-run sqlite snapshot of raw OHLCV
  screen.py    `vss screen` -- universe report and price snapshot
  __main__.py  CLI
tools/         build-time only: build_universe.py writes the universe CSVs
config/        watchlist.yaml (yours, tracked) + the committed example
config/manual/ TEMPLATE.yaml + one filled <TICKER>.yaml per hand-entered name
config/manual/maps/  <TICKER>.yaml -- which cell of the appendix answers which field
config/nordic_issuers.yaml  ticker -> the exchange feed's market/company key
sources/       downloaded documents (gitignored) + manifest.json (tracked)
config/universe/  static dated constituent lists + instrument-type and floor config
config/screener_exclusions.csv  names the screener may never propose
config/screener_filter2.yaml    filter 2 thresholds, each citing FRAMEWORK
data/          price cache, yfinance cache, vss.sqlite   (gitignored)
reports/       YYYY-MM-DD.md + OVERVIEW.html             (gitignored)
deploy/        systemd user service + timer
reference/     SPEC.md -- machine-facing rules, kept in sync with the code
               SCREENER.md -- the screener's design and its phase plan
tests/         pytest suite
```

`rules.py` holds the verdict logic as pure functions taking plain scalars and
returning verdict objects, with `as_of` always passed in so no rule reads the
clock. `metrics.py` is separate because its inputs are DataFrames rather than
plain scalars; it is equally pure. Two tests enforce that `rules.py` imports
nothing beyond stdlib value types and never calls `now()` or `today()`.

## History

Each run appends one row per ticker to `data/vss.sqlite` (table
`run_metrics`): every computed metric, the manual inputs in force at the
time, the resolved MBP, the blockers and verdicts that fired, and
`ticker_filter` (NULL for a full run, the ticker for a `--ticker` run).
Nothing reads it back yet -- it accumulates for later. New columns are added
to an existing database by a migration on connect, so the file survives
upgrades.
