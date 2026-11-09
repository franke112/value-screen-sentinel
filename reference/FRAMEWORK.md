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
- **Cycles (E143, with S-B7 and E148; S-B7 as amended by E169).**
  - A cyclical business is normalised over its cycle, and the bear case
    lowers the level.
  - Cyclical needs a downturn in the history. A business declared cyclical
    with none in its history has bear DATA MISSING and no buy line.
  - One year whose fall is repaired the next year is not a cycle **only
    where the history declares that year with a non-economic cause**
    (`one_year_forgiven`; HRB FY2020, the moved filing deadline). A
    repaired year alone, such as a COVID year, stays a cycle.
- **Growth (E144).** Growth is derived from the issuer's own organic
  history, capped at 4 % (8 % where seven years support it). Where there
  are fewer than five organic years, the registered view stands.
- **Absurd values (S-B6).** A bear at or below zero, or above base, stops the
  name as absurd.
- **Void values (S-B5).** A value the watchlist marks void (`fv_void`) is
  never read.

## 3. Quality (**E145**, with **E148**; **E168**: Q1-Q4 information only)

| Test | Requirement |
|---|---|
| **Q1** | Median after-tax return on tangible invested capital ≥ 15 % |
| **Q2** | Owner earnings positive every year (one repaired year forgiven, E148); operating profit never below half its running peak unless regained within three years |
| **Q3** | Net debt ≤ 3 × FCF0, or 4.5 × where profit never fell more than 15 % |
| **Q4** | ROIIC ≥ r for a repeat buyer |
| **Q5** | The issuer's own sentence on what it sells, to whom, and why the customer returns |

- **Q1-Q4 are printed and decide nothing** (E168, attempt #25: neither the
  drop rule Q1-Q3 nor Q4's tier step separated returns in both markets and
  both halves). A failing name is not dropped, not sold at base, and its
  tier is not lowered.
- **Q5 stays** as the hand part: a name without the sentence is not struck.
- The tests never change a value.
- **Held names** (E155(2), read by the second session 2026-11-09, E169):
  CTSH's and ACAD.ST's tier steps stand as written; they feed only MBP,
  which is information. CENTA's sell at base is gone; its exit stands as the
  owner's decision of 2026-10-27, without a price.

## 4. Hard kills (§4.2, **E163**: 4.2.1, 4.2.2 and 4.2.7 removed by attempt #24; **E168**: 4.2.5's 3.5× leg removed by attempt #25)

Any one invalidates:

1. 2+ guidance cuts in the trailing 4 quarters (4.2.3).
2. 3+ EPS misses in the trailing 8 quarters (4.2.4).
3. Covenant proximity (4.2.5). Its net debt / EBITDA > 3.5× leg is gone
   (E168); whether it returns is attempt #26, on the April 2027 data.
4. CEO **and** CFO departure within 12 months (4.2.6).

Falling revenue, a compressed margin or swelling receivables or inventory
is information for Gate 2 and the growth view, never a kill (E163; #24:
none of the three sorted returns in both markets and both halves).

## 5. Status, line and size

- **Status (E27).**
  - WATCH-PRICED: the name passed and is too expensive. A price line
    applies.
  - WATCH-GATED: the name failed something other than price. Re-entry needs
    a named information event, never a price.
- **MBP (E90, E168).** MBP is the base value × the tier cushion:
  tier 1 × 0.85, tier 2 × 0.75, tier 3 × 0.65. The tier is a hand field. MBP is
  information and binds nothing: attempt #25 found that a price at or below
  0.85 × fv did not separate returns in both markets and both halves. The
  queue says UNDER MBP, never KÖP; the owner buys as he likes.
- **Size (E157).** One name is at most 6 % of the whole portfolio.
- **Stop (E162).** There is no price stop, by decision (attempts #10, #18).
  `stop_price: none` is written; a blank field blocks.
- **Sales (E165).** `sales:` is reconciled against an account export before
  `vss sales` is read.

## 6. Rules about rules

- **Risk filters (E169).** A filter whose job is to avoid losses (debt,
  a kill) is tested on the median and on the share of names losing more
  than 75 %, not on the mean alone: a mean is carried by a few large
  winners.
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
