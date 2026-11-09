# Glossary

The words this project uses, in one place. The book explains them at length
([the-method](https://franke112.github.io/value-screen-sentinel/the-method/)).
This page is for looking a word up.

## Value

| Word | Meaning |
|---|---|
| **bear / base / bull** | Three values per share: a cautious, a central and a hopeful case. Each is a ten-year cash-flow valuation at a 9.5% required return. |
| **fair value, `fv_base`** | The base value. The other two are information, and the base is what a buy line is built on. |
| **strike** | One valuation run on one company (`vss strike`), written to `reference/<TICKER>-STRIKE-<date>.md` with every figure and its source. |
| **FCF0, owner earnings** | The cash the business throws off for its owners: operating cash flow less capital spending, averaged over three years with working-capital swings taken out. |
| **g\*** (implied growth) | The growth today's price already assumes. It comes from running the valuation backwards (a *reverse DCF*). |
| **growth view** | Your own bear / base / bull growth guess, written down **before** you see g\*. Later the method derives it from the company's own history. |
| **MBP** (maximum buy price) | The base value times the tier cushion. **Information since 2026-11-09 (E168):** the cushion did not separate later returns in the backtests, so it binds nothing; the queue says UNDER MBP, never "buy". |
| **tier** | How much margin of safety a name is shown with (it feeds only MBP, which is information). **Tier 1** is 0.85 of base (high conviction, fortress balance sheet), **tier 2** 0.75, **tier 3** 0.65. |
| **stop** | Removed 2026-11-08 (E162): there is no price stop. The backtests found that stops cost more than they saved. `stop_price: none` is that decision, written. |

## Quality

What was tested and removed in November 2026, and why: [reference/backtest/WHAT-WE-TESTED.md](reference/backtest/WHAT-WE-TESTED.md).

| Word | Meaning |
|---|---|
| **Q1-Q4** (would Warren own it?) | Four tests, **printed as information since 2026-11-09 (E168)**: as a rule for dropping names they did not hold in the backtests. **Q1** return on tangible capital of at least 15%. **Q2** owner earnings positive, and operating profit never below half its peak. **Q3** small debt. **Q4** acquisitions that earn more than they cost. `tools/warren.py` runs them on any US filer. |
| **ROIIC** | Return on incremental invested capital: what the new money put into the business earns. |
| **hard kill** (§4.2) | A red flag that ends the analysis whatever the price. Four are left, the ones the data could not test or that held: two outlook cuts within four quarters, three earnings misses in eight, covenant proximity, CEO **and** CFO leaving within a year. Falling revenue, a squeezed margin, swelling receivables (E163) and the 3.5x debt limit (E168) were removed when the backtests showed they did not separate returns. |
| **gates** (§3) | The old screening steps. Struck from FRAMEWORK on 2026-11-08; gates 2, 3 and 5 still run in code until a test decides them (`reference/archive/STRUCK-2026-11-08.md`). |
| **conviction score** (§4.4) | Struck 2026-11-08. The tier is now a hand field. |
| **tied working capital** (E166) | Working capital read row by row off the cash flow statement, with every row summing to the printed operating cash flow. A sum that does not tie is DATA MISSING. |
| **implied growth in the queue** | The queue prints "the price implies X % growth; the requirement is 9.5 %", and a table of base at g ± 1.5 points. |
| **void value** (`fv_void`) | A value the watchlist marks void. The queue never reads it. |

## Status of a name on the watchlist

| Status | Meaning |
|---|---|
| **INTAKE** | Read, not watched: the figures are in, but no decision is made yet. |
| **PIPELINE** | Entered by the owner. It is valued and waits for its price. |
| **WATCH-PRICED** | A good business that is too dear. A price level may wake it. |
| **WATCH-GATED** | Failed on something other than price. **No price can wake it.** Only the named event can, such as the next report. |
| **HELD** | Owned. |
| **DROPPED** | Out, with the reason on file. |

## The machine

| Word | Meaning |
|---|---|
| **the nightly run** | `vss run`, at 22:30: prices, figures and the lines for every watchlist name, written to `reports/<date>.md`. |
| **the queue** | `vss queue`, on weekdays at 22:50: every valued name held against its value and its look and sell lines, with one phone message per change. |
| **the screen** | `vss screen`, on Saturdays: sifts about two thousand companies, lists those that pass in a fixed random order (the ranking key was removed by E167) and enters none. |
| **the shadow book** | Every "no", measured against the index afterwards, so you learn whether the refusals were right. |
| **E-numbers** (E28, E90, ...) | Rulings: each change to the rules, with its date and reason, in `reference/archive/FRAMEWORK-EDITS-2026-11-08.md` (the binding ones are in `reference/FRAMEWORK.md`). [The ones that matter most](reference/README.md). |
| **§** (§3, §4.2, ...) | A section of the rulebook, `reference/FRAMEWORK.md`. |
| **blocker** | Data too stale or too uncertain to judge on. The tool says "cannot judge" rather than judge badly. |
