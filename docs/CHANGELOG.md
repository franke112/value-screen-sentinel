# Changelog

What changed in how the tool behaves, newest first. A rule is named by its
E-number; its full text and reasons are in `reference/archive/`. A rule that
decides what is bought, held, sold or valued enters or leaves only on a test
registered before it ran (`reference/backtest/ATTEMPTS.md`, E164), and the
attempt is named beside it.

## 2026-11-09

**Documentation**

- The manual is rewritten in four parts: getting started, how-to, reference,
  explanation ([`MANUAL.md`](MANUAL.md), [`EXPLANATION.md`](EXPLANATION.md)).
- The command reference is generated from the code
  ([`REFERENCE.md`](REFERENCE.md), `tools/build_manual_reference.py`) and a
  test holds it equal: every command and flag, what each reads, writes,
  calls and sends, the timers, the environment variables, the files, the
  modules.
- [`AGENTS.md`](../AGENTS.md) at the repository root tells an AI agent which
  commands change nothing, which write, and which reach the phone.

**Found while auditing the manual against the code, and fixed**

- The nightly report said a stop was live and checked; there has been no
  price stop since E162. The sentences are gone, the stop column is labelled
  a note and prints `none` where no stop is the decision, and it left the
  ACTIONS table. The overview page no longer says it checked "every stop
  against its close".
- `vss screen --help` described a dislocation band and a two-component
  ranking key; it describes the staleness gate and the seeded order. The
  note `--write-pipeline` writes on a new entry says "place N in the seeded
  order", not "rank N".
- `tools/rough_fv.py` and `tools/quotecheck.py` had no argument parser:
  `--help` was read as a ticker. Every tool that takes arguments now has
  one.
- `vss queue --dry-run` said it wrote nothing; a new report it finds is
  still fetched and read into `data/autoread/`. The help text says so.
- `config/watchlist.example.yaml` documented cushions, flags and statuses
  that no longer exist.

**Behaviour**

- **A report is read, not only noticed.** `vss queue` fetches each queue
  name's new report (SEC, the Nordic and Oslo feeds), reads it twice,
  re-values the name on its last four quarters and sends `UTSIKT` only when
  the outcome changed. The `RAPPORT` message is gone.
- **The master list** (`reports/HUVUDLISTA.md`, `tools/master_list.py`):
  every company looked at, rebuilt nightly.
- **The screener's order is a seeded draw** with one fixed seed (E167,
  attempt #24: the ranking key did not sort returns by decile in either
  market). Its two legs are still written to `ranking.csv` as information.
- **MBP is information** (E168, attempt #25): a price at or under it did not
  separate returns. The queue says `UNDER MBP`, never "buy".
- **Q1-Q4 are printed and decide nothing** (E168). Q5, the sentence on what
  the company sells and why the customer returns, stays as the hand part.
- **Hard kills:** 4.2.5's net debt / EBITDA leg and the 4.3 soft flag are
  removed (E168). Four kills remain.
- **Filters:** the "below a year ago" test left filter 1 and the leverage
  limb left filter 2 (E168). Filter 1 is the staleness gate; filter 2 is
  positive free cash flow.
- **Risk filters are judged on the median and the share of large losses**,
  not on the mean alone (E169).

## 2026-11-08 -- the sweep

- **`reference/FRAMEWORK.md` is two pages.** The rulings, the old framework
  and the list of what was struck are archived in `reference/archive/`.
- **The price stop is removed** (E162, attempts #10 and #18): no stop
  verdict, no stop level in the staleness gate. A held name writes
  `stop_price: none`; a blank field blocks it.
- **The 15-50 % dislocation band is removed** as a filter and as a verdict
  (E161, attempts #12 and #21). The drawdown stays on the row.
- **Three hard kills are removed** (E163, attempt #24): falling revenue
  (4.2.1), a compressed margin (4.2.2), swelling receivables or inventory
  (4.2.7). They are information for the growth view.
- **Working capital is tied to the cash flow statement** (E166):
  `vss/cfrecon.py` reads it off the statement and ties it to the printed
  operating cash flow; a store that does not tie does not strike.
- **The queue** prints the growth the price implies and a sensitivity
  table, never reads a void value (`fv_void`), gives no line to a name whose
  bear case is absurd or to a declared cyclical with no downturn in its
  history.
- **One name is at most 6 % of the portfolio** (E157); the queue says
  `STORLEK` weekly while a position is above it.
- **Sales are reconciled** against an account export before the sales
  record is read (E165).
- **A rule for rules** (E164): a decision rule enters or leaves on a
  registered test; a data rule may be added freely.
- **Removed:** the decision playbook. The review's steps live in
  `vss/review_steps.py`.

## 2026-11-07

- The technical manual moved out of the README.
- **Drafts:** `vss esef` reads an issuer's ESEF report package and
  `vss pdfdraft` has a model read the statement pages twice, both into a
  draft that is never the store (E149). `tools/cross_verify.py` marks a
  machine-read figure verified only when a second, independent reading
  prints the same digits (E151).
- **Point in time:** a replay says when its snapshot is dated after the day
  it claims; the screener checks US survivors against SEC facts clipped to
  that day; every vendor field is kept as fetched, with its date.
- The Nordic screen and the backtests on a vendor's data under your own
  licence; none of that data is in the repository.

## 2026-11-05

- **`vss queue`**: every valued name against its lines every weekday night,
  one message when something changed.

## 2026-10-27

- **Free cash flow is normalised** (E140): the mean of three fiscal years,
  each less its working-capital change, with interest added back after tax.
- **Acquisitions leave both the flow and the growth** (E142) and are valued
  at the acquirer's own return on incremental capital. Growth is derived
  from the issuer's own organic history where there is enough of it (E144).

## 2026-09-19

- **A name carrying a level is held to one session.** A held name, or one
  with an MBP, is blocked when its close is more than one trading day old,
  and a dry run refuses (exit 3) rather than print a report on it.

## 2026-09-09

- The settings file `~/.config/vss/vss.env` is read by the commands
  themselves, not only by the timers. The environment still wins.

## 2026-08-30

- **MBP = the base value x the tier cushion** (E90): 0.85 / 0.75 / 0.65.

## 2026-08-25

- `config/watchlist.yaml` is tracked in git.
- The status `WATCH` is split into `WATCH-PRICED` and `WATCH-GATED` (E27);
  the bare word is rejected.

## 2026-08-20

- The repository's history was re-initialized and starts from a single
  commit.
