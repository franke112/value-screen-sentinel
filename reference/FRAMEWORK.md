# FRAMEWORK

Rewritten 2026-11-08 (sweep D13). The rules below are what binds; every one
names its ruling in `reference/archive/FRAMEWORK-EDITS-2026-11-08.md`, where
the full text, the reasons and the history stay. The old framework is
`reference/archive/FRAMEWORK-2026-11-08.md`. What was struck is listed in
`reference/archive/STRUCK-2026-11-08.md`.

## 1. DATA MISSING

**DATA MISSING is a result, never a gap to fill.**

- Every figure carries its page and its status.
- A figure that is not there is not assumed, defaulted or substituted.
- A valuation whose leg is missing does not print. Section 5 refuses.
- A derived figure inherits the weakest status of its parts.

## 2. The value (Method C, **E28**)

- **Engine.** The fair value is a ten-year DCF with terminal growth of 2.5 %.
- **Rate (E29).** The owner's hurdle rate is **9.5 %**: the index core's
  expected return plus 2-3 points. It is flat across names.
- **Three cases.** Bear, base and bull are each struck at their own growth.
  The growth is pre-registered or derived (below).
- **FCF0 (E140, E140.1).** The mean of the last three fiscal years. Each
  year is operating cash flow, less the working-capital change, less capex,
  less SBC, less IFRS 16 lease cash. Interest is added back after tax at the
  statutory rate. Minority dividends are deducted.
- **Working capital (E154).** Where it consumed cash in all three years, it
  stays in FCF0.
- **Reading working capital (E166, data rule).** Working capital is read off
  the cash flow statement itself and tied to the printed operating cash
  flow. The classes come from `config/manual/maps/cashflow-tags.yaml`.
  E140(1)'s clarifications 1-2 decide what an operating balance is.
- **Bridge.** The bridge is the latest filed balance sheet, with its
  year-to-date working capital neutralised (E140.1(3)), plus every deal
  after the basis (E140(3)).
- **Acquisitions (E142).** Acquisitions leave both the flow and the growth.
  The deal programme and pending deals are valued at the acquirer's own
  ROIIC, as min(ROIIC, r) / r.
- **Level (E143).** The three-year mean is rolled one year forward.
- **Cycles (E143, with B7 and E148).**
  - A cyclical business is normalised over its cycle, and the bear case
    lowers the level.
  - Cyclical needs a downturn in the history. A business declared cyclical
    with none in its history has bear DATA MISSING and no buy line.
  - One year whose fall is repaired the next year is not a cycle.
- **Growth (E144).** Growth is derived from the issuer's own organic
  history, capped at 4 % (8 % where seven years support it). Where there
  are fewer than five organic years, the registered view stands.
- **Absurd values (B6).** A bear at or below zero, or above base, stops the
  name as absurd.
- **Void values (B5).** A value the watchlist marks void (`fv_void`) is
  never read.

## 3. Quality (**E145**, with **E148**)

| Test | Requirement |
|---|---|
| **Q1** | Median after-tax return on tangible invested capital ≥ 15 % |
| **Q2** | Owner earnings positive every year (one repaired year forgiven, E148); operating profit never below half its running peak unless regained within three years |
| **Q3** | Net debt ≤ 3 × FCF0, or 4.5 × where profit never fell more than 15 % |
| **Q4** | ROIIC ≥ r for a repeat buyer |
| **Q5** | The issuer's own sentence on what it sells, to whom, and why the customer returns |

- A watched name failing Q1-Q3 is dropped.
- A held name failing Q1-Q3 is sold once the price reaches base.
- Q4 lowers the tier one step.
- The tests never change a value.

## 4. Hard kills (§4.2, until ATTEMPTS #24 decides 4.2.1 / 4.2.2 / 4.2.7)

Any one invalidates:

1. Revenue declining in 2+ consecutive quarters: organic where disclosed,
   reported otherwise.
2. Operating margin down > 150 bps YoY on flat or declining revenue.
3. 2+ guidance cuts in the trailing 4 quarters.
4. 3+ EPS misses in the trailing 8 quarters.
5. Net debt / EBITDA > 3.5× or covenant proximity.
6. CEO **and** CFO departure within 12 months.
7. Receivables or inventory growing > 1.5× revenue for 2+ quarters.

## 5. Status, line and size

- **Status (E27).**
  - WATCH-PRICED: the name passed and is too expensive. A price line
    applies.
  - WATCH-GATED: the name failed something other than price. Re-entry needs
    a named information event, never a price.
- **MBP (E90).** MBP is the base value × the tier cushion: tier 1 × 0.85,
  tier 2 × 0.75, tier 3 × 0.65. The tier is a hand field. MBP is
  information; the owner buys as he likes.
- **Size (E157).** One name is at most 6 % of the whole portfolio.
- **Stop (E162).** There is no price stop, by decision (attempts #10, #18).
  `stop_price: none` is written; a blank field blocks.
- **Sales (E165).** `sales:` is reconciled against an account export before
  `vss sales` is read.

## 6. Rules about rules

- **Two kinds of rule (E164).**
  - A **decision rule** (what is bought, held, sold or valued) enters or
    leaves this file only on a test registered in
    `reference/backtest/ATTEMPTS.md` before it runs: both markets, both
    halves.
  - A **data rule** (how a figure is read) may be added freely.
- **Loosening (E155).** A ruling that loosens a test or raises a value is
  measured on every name. On a held name it waits for a second session.
- **Exceptions.** The owner may set a rule aside for one name.
  - The exception is written as his, never as a rule: `override: {rule:
    owner, overrides: E-number, reason, standing, expires}`.
  - What the rule would have done is recorded as a counterfactual fill.
    `vss sales` reports it apart and never totals it.
