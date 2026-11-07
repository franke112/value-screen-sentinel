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
| **MBP** (maximum buy price) | The base value times the tier cushion. You do not pay above it. |
| **tier** | How much margin of safety a name needs. **Tier 1** is 0.85 of base (high conviction, fortress balance sheet), **tier 2** 0.75, **tier 3** 0.65. |
| **stop** | The price at which a held position is sold to limit the loss. It is set at entry. |

## Quality

| Word | Meaning |
|---|---|
| **Q1-Q4** (would Warren own it?) | Four tests before price matters. **Q1** return on tangible capital of at least 15%. **Q2** owner earnings positive, and operating profit never below half its peak. **Q3** small debt. **Q4** acquisitions that earn more than they cost. `tools/warren.py` runs them on any US filer. |
| **ROIIC** | Return on incremental invested capital: what the new money put into the business earns. |
| **hard kill** (§4.2) | A red flag that ends the analysis whatever the price: revenue falling two quarters in a row, margins collapsing on flat sales, two outlook cuts within four quarters, too much debt, and a few more. |
| **gates 1-5** (§3) | The screening steps. 1: the price has fallen 15-50% for a dateable reason. 2: why it fell (sentiment, sector, a one-off cost, or a broken business). 3: a balance-sheet floor. 4: valuation multiples (not yet measurable). 5: a dated event within 90 days. |
| **conviction score** (§4.4) | Gates passed, plus green flags, minus soft flags. It decides the tier. |

## Status of a name on the watchlist

| Status | Meaning |
|---|---|
| **INTAKE** | Read, not watched: the figures are in, but no decision is made yet. |
| **PIPELINE** | Passed the gates. It is valued, has a tier, and waits for its price. |
| **WATCH-PRICED** | A good business that is too dear. A price level may wake it. |
| **WATCH-GATED** | Failed on something other than price, usually a hard kill. **No price can wake it.** Only the named event can, such as the next report. |
| **HELD** | Owned. |
| **DROPPED** | Out, with the reason on file. |

## The machine

| Word | Meaning |
|---|---|
| **the nightly run** | `vss run`, at 22:30: prices, figures and the lines for every watchlist name, written to `reports/<date>.md`. |
| **the queue** | `vss queue`, on weekdays at 22:50: every valued name held against its buy, look and sell lines, with one phone message per change. |
| **the screen** | `vss screen`, on Saturdays: ranks about two thousand companies and enters none. |
| **the shadow book** | Every "no", measured against the index afterwards, so you learn whether the refusals were right. |
| **E-numbers** (E28, E90, ...) | Rulings: each change to the rules, with its date and reason, in `reference/FRAMEWORK-EDITS.md`. [The ones that matter most](reference/README.md). |
| **§** (§3, §4.2, ...) | A section of the rulebook, `reference/FRAMEWORK.md`. |
| **blocker** | Data too stale or too uncertain to judge on. The tool says "cannot judge" rather than judge badly. |
