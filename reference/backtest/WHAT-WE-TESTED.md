# What we tested, what we removed, and why

*Written 2026-11-09. The method in this repository is not a theory taken
on trust. Between 29 October and 9 November 2026 every mechanical rule in
it was put through a test on history that was registered **before** it
ran. A rule that did not hold was taken out of the code and the documents.
This page tells that story: 26 attempts, in order, the faults we found in
our own data along the way, and what is left.*

## The short version

- We started with a method of about 150 rulings, built over three months
  from books, papers and reasoning.
- We tested it on history: the US 2016-2020 and the Nordics 2010-2021,
  with every figure entering only on the day it became public and with the
  companies that later went bust or were bought put back in.
- **Most of the mechanical rules did not hold.** The price stop, the
  drawdown band, the screener's ranking key, three hard kills, the debt
  limits, the quality tests as a drop rule, the buy-price cushion as a
  binding line and the "fallen over a year" test are gone from the code.
- **What stayed** is what is either a reading of facts (data rules) or
  could not be tested and is done by hand: the valuation itself, the
  growth view written before the price is seen, the reading of reports,
  the issuer's own sentence on what it sells (Q5), positive free cash flow,
  and a 6 % ceiling on one name.
- **No edge has been shown.** A broad index fund is the base for the
  owner's money; this method is the part that is studied, not trusted.

## How a test is run here

1. **Registered first.** Each attempt is written into an attempt log
   before it runs: the hypothesis, the data, the exact measure, the bar and
   what happens to the rule on either outcome. The private repository
   records each registration as its own commit, ahead of the commit with
   the result.
2. **One bar for every rule.** A rule counts as holding only if it helps
   in **both** markets (the Nordics and the US) **and** in **both** halves
   of each (Nordic 2010-15 / 2016-21, US 2016-18 / 2019-20). From attempt
   #25 also above the 95th percentile of 1,000 random relabellings within
   each date.
3. **Every look is counted.** Every run whose result was seen is logged,
   bad ones too, and data corrections made after a result was seen are
   logged as attempts of their own. A result is read against how many
   tries it cost. After about 25 runs and 50 bars, a lone pass is what
   chance gives.
4. **A rule that does not hold goes.** Since ruling E164 (2026-11-08) a
   decision rule (what is bought, held, sold or valued) enters or leaves
   the method only on such a registered test. A data rule (how a figure is
   read) may be added freely.
5. **Then the history is closed.** After attempt #25 the owner closed
   these years: the method is not trimmed further on data it has already
   been fitted to. The next test (#26) is registered now and runs only on
   new data, in April 2027.

## The data, and why most results here are in words

US filings come from SEC EDGAR (public). For prices that include the
delisted, and for the whole Nordic test, we bought a licence from a
commercial vendor, [EODHD](https://eodhd.com): daily prices for 25,854 US
and Nordic common stocks, 18,336 of them later delisted, and their
financial statements, each dated to when it became public. Outside
benchmarks: Ken French's country portfolios and the JKP factors (Jensen,
Kelly and Pedersen, *Journal of Finance* 2023, CC BY-NC 4.0).

**The vendor's licence is private.** Its data, and the figures computed
from it, are not published here: what follows are verdicts in words. What
*is* published is everything needed to check us: the test scripts
(`tools/backtest/`), the engine they call (`vss/`), and the exact rule each
test was held to. With your own data licence you can run them and get our
numbers or show that we were wrong.

## The attempts, in order

### Round 0: the first run, and survivorship (#1-#2)

- **#1, 29 Oct.** US, survivors only (SEC filings, Yahoo prices),
  2016-2020, the design's pre-registered run. The method's portfolio
  failed its criteria on all five dates and trailed the S&P 500 by about
  2 points over three years.
- **#2, 7 Nov.** The same valuations re-priced with the delisted put back.
  The gap widened sharply. **Lesson: a backtest on today's list flatters
  any method, and ours most.**

### Round 1: the Nordics (#3-#9, #14)

- **#3-#9.** The same engine on the Nordics. The cheap companies by the
  method's fair value beat the dear ones in most years, though less
  clearly each time a data fault was found and fixed (see below).
- **#6b, the confirmation.** Registered before it ran, on 2022 and 2023,
  years never looked at: **NOT CONFIRMED** (one year held, one reversed).
  A currency fault found afterwards was fixed, but the confirmation was
  deliberately **not** re-run: a fix made after seeing a result cannot
  confirm anything.
- **#8.** The live screener's ranking key (EBIT/assets + EBIT/EV) and its
  15-50 % drawdown band were measured for the first time. The key sorted
  somewhat; its best fifth still trailed the index; the band added
  nothing.

### Round 2: the method's own pieces (#10-#22, #20b)

- **#10, stops** (8/12/20/30 % under entry, with and without buying back):
  **no stop helped any selection**, in either market or half. Without
  buying back, every stop cost heavily.
- **#11, concentration.** Fewer names did not raise the median outcome;
  they only widened the spread. Three names are a lottery ticket on the
  same mean.
- **#12, the band and momentum.** The 15-50 % band did not help in the
  Nordics either, and dropping the weakest-momentum tenth did not help
  the ranking.
- **#13, F-score and accruals.** The F-score passed once. Later checks
  weakened it (#15, #19, #21), so it is **not** a rule, only a candidate
  for new data. Accruals did not sort.
- **#15, the price-break guard.** A data guard added after results were
  seen was itself tested: it had been removing winners on bad single-day
  prints. Fixed; the verdicts above did not change, except the F-score's.
- **#16, benchmarks.** Where the fair-value sort worked, it worked by
  avoiding the dearest names, not by finding winners: the cheapest fifth
  did not beat the whole universe.
- **#17, the hard-kill thresholds.** Only one kill (three or more earnings
  misses in eight reports) separated returns. Falling revenue, a margin
  drop and swelling receivables did not.
- **#18, stops with Avanza's trading costs.** Even the mildest stop cost
  money once the courtage, currency exchange and spread were counted.
- **#19, against the JKP factors.** Some of our Nordic sorts agreed with
  the published factors; our fair value against price did not agree with
  book-to-market, and nothing agreed in the US.
- **#20b, against real value funds**, in SEK and after costs. Our sort
  beat the world value funds, but so did the unsorted universe, by about
  as much: the gain was the market, not the sort.
- **#21, ablation and competitors.** The full chain of rules bought almost
  nothing (a handful of names in twelve Nordic years). Against the Magic Formula,
  Quantitative Value, O'Shaughnessy's Value Composite and Piotroski, ours
  beat **none** of twelve pairs. No result cleared t > 3 once the
  overlapping windows were allowed for.
- **#22, a restated price series** (SCA after the Essity spin-off): no
  verdict changed.

**Removed after round 2:** the price stop (E162; the owner writes "no
stop" explicitly), the drawdown band (E161), the kills on falling revenue,
margin and receivables (E163), the screener's revenue limb.

### Round 3: everything still untested (#23-#25)

- **#23, does the derived growth overestimate?** No: realised growth came
  in *above* the derived figure on every US date and in both Nordic
  halves. The planned haircut (E160) was struck.
- **#24, deciles.** Neither the ranking key, nor fair value against price,
  nor a quality composite sorted returns by decile in both markets. The
  ranking key was removed (E167) and the screener's order is now a seeded
  draw: the filters select, the order does not pretend to.
- **#25, ten filters at once**, through against stopped, with a
  permutation bar. **None held:** the "below a year ago" price test, the
  screener's debt limit, the 3.5x debt kill, the sequential-decline flag,
  the quality tests Q1-Q3 as a drop rule, Q4 as a tier step, the buy-price
  cushion as a binding line and both "green flags". All removed (E168).
  Positive free cash flow could not be tested (every valued name has it)
  and stays.

### Next: #26, on new data only

An after-the-fact look at #25's rows (not a test, and it decides nothing)
suggested the debt limits and Q1-Q3 may cut the *loss tail* even where they
do not lift the *mean*. That is registered now as #26, measured on the
median and on the share of names losing more than 75 %, and it runs only
on the April 2027 data, dates no earlier attempt has read. If it holds,
those filters come back; if not, they stay out.

## The faults we found in our own data

Each was found by reading full output or by an independent review, logged,
fixed, and the affected runs redone as new attempts:

- share counts restated for later splits next to unadjusted prices;
- Nordic "filing dates" that were only the period end;
- figures reported in another currency than the share trades in, and a
  vendor label that switched currency where the company had not;
- a currency correction carried back past a company's real switch;
- one security under two tickers, and tickers reused after a takeover;
- the vendor's single-day bad prints read as a company going bust;
- Nordic quarters read as third quarters only;
- IFRS 16 leases making rent-heavy companies look cheap.

## What could not be tested, and stays by hand

The reading of reports, the growth view, Gate 2 (the business is
understood), the catalyst, Q5 (the issuer's own sentence on what it sells),
guidance cuts and a CEO-and-CFO departure (no data). Their test is the
shadow book: every "no" is priced and measured against the index, so in a
few years the hand parts get a verdict too.

## What it means for someone reading this repository

The tool measures and the owner decides. It is shown here as a method
that was taken apart honestly, not as one that beats the market. The
lesson that cost the most to learn: **an idea that sounds right is not
evidence.** Most of what is written in value-investing books, applied
mechanically to these markets and years, did not survive a test set up in
advance.
