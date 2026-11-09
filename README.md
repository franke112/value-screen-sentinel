# vss -- value-screen sentinel

**A value-investing method one person can actually keep to, and the machine
that keeps it honest.** It runs together with [Claude Code](https://claude.com/claude-code).

There are about two thousand companies you could buy a piece of, and one
person with a few evenings a week. vss screens them, reads the companies' own
reports, works out what a business is worth and what today's price already
assumes, and watches every name you have valued, every night.
**It never tells you to buy anything.** It measures, you decide, and it keeps
the record of what you decided and why.

> **How it works and why, in 24 short chapters (or a ten-minute route):**
> **[franke112.github.io/value-screen-sentinel/the-method](https://franke112.github.io/value-screen-sentinel/the-method/)**
> *(på svenska: [the-method/sv](https://franke112.github.io/value-screen-sentinel/the-method/sv/))*

## In ten seconds

- **Values any US company from its SEC filings** in one command: bear, base
  and bull per share, and the growth today's price assumes.
- **Reads Nordic reports too**: the issuers' own PDFs and ESEF packages,
  every figure with the sentence it came from.
- **Watches everything you have valued, every night.** New reports are
  fetched, read and the company valued again; your phone hears only when the
  outcome changes.
- **One master list** of every company you have ever looked at: owned,
  candidates, watched, to review, and every "no" with its reason.
- **Prices every "no"** against the index, so you learn whether your
  refusals were right.
- **Tested, not trusted.** Every mechanical rule went through a backtest
  written down before it ran; the ones that failed were taken out of the
  code.

## Who it is for

One private investor who wants **discipline, not tips**: a method written
down, figures only from the companies themselves, and a record that shows
afterwards whether the decisions were good. If you want signals to trade on,
this is not it.

## What it looks like

Ask whether Warren Buffett would own a company. Any US company works,
straight from its SEC filings:

```
$ .venv/bin/python tools/warren.py KO

== KO  price 95.67  |  bear 12.38  base 28.11  bull 41.62  |  price/base 3.40x
   Q1 PASS  return on tangible capital >= 15%: median 17.2% over 11 years (goodwill taken out)
   Q2 PASS  owner earnings positive, operating profit never below half its peak
   Q3 PASS  net debt <= 3x FCF0: net debt 2.4x FCF0 against 4.5x (stable class)
   Q4 PASS  acquisitions return >= 9.5% (repeat buyers only): not a repeat buyer
   -> the business passes, the price does not (3.40x base) -- wait
```

Coca-Cola is a fine business at three times what the method thinks it is
worth, so the answer is **wait**. That is the most common answer, and on
purpose.

Every Claude Code session opens with the master list. This is the author's
own, on 2026-11-09 (prices in each listing's currency; the holdings are
disclosed below):

```
HUVUDLISTAN 2026-11-09: 106 bolag -- ägda 3, kandidater 2, bevakas 14, att granska 13, nej 74
ÄGDA: ACAD.ST 129.4 (base 158.74); CENTA 41.84 (base 40.19); CTSH 63.96 (base 58.03)
KANDIDATER: SF.ST 6.29 (bear 4.42 / base 13.42); PACT.ST 139.8 (bear 148 / base 189)
ATT GRANSKA, billigast: ZZ-B.ST 1.49 [grov]; MMS 1.45 [maskin]; STG.CO 1.31 [grov]; ...
BEVAKAS under linjen: SFM 1.53; HRB 1.40; GNTX 1.37; DECK 1.35
KOMMANDE: 2026-11-11 PACT.ST Capital Markets Day; 2026-11-17 ZZ-B.ST Q3 2026 interim report; ...
```

*ägda* = owned, *kandidater* = candidates, *bevakas* = watched, *att granska*
= to review, *nej* = no. The number after a name is base value over price;
*grov* (rough) and *maskin* (machine) say the value is a screen, not yet a
full valuation.

A message reaches your phone only when something changes the outcome
(*titta* = look, *utsikt* = outlook):

```
TITTA DHI 152.28 <= 156.86 (0.83x base 184.54, strike) -- value it properly now
UTSIKT GNTX: värdet på fyra kvartal 27.10 -> 23.80 (-12%) efter kvartalet till 2026-09-30 -- läs rapporten
```

*(The second line illustrates the format; it is not a real reading.)*

## Try it in five minutes

Linux, Python 3.11+. Tested from a fresh clone: 29 seconds to install, 14
seconds for the first run.

```bash
git clone https://github.com/franke112/value-screen-sentinel.git ~/vss && cd ~/vss
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
export VSS_SEC_CONTACT='mytool/1.0 (you@example.com)'   # SEC asks every caller for a contact
.venv/bin/python -m vss doctor               # checks Python, packages, settings; says what is missing
.venv/bin/python -m vss run --dry-run        # the nightly report, writes nothing
.venv/bin/python tools/warren.py KO AAPL     # would Warren own it?
```

Reading reports with a model (the nightly reading, `vss earnings`,
`vss pdfdraft`) needs an [OpenRouter](https://openrouter.ai) key in
`VSS_OPENROUTER_KEY`. That costs a little per report read; everything else
runs without it. **[`SETUP.md`](SETUP.md)** covers the settings, your own
watchlist and queue, phone alerts (ntfy) and the nightly timers.

## How it works

```
 screen  ──>  read  ──>  value  ──>  queue  ──>  you decide
 weekly       the        bear /      nightly,    in a Claude Code
 sift of      company's  base /      one         session, every
 ~2,000       own        bull per    message     reason written
 companies    reports    share       on change   down
```

1. **Screen.** Every Saturday it sifts the market down to companies with
   positive free cash flow and enough history to read, in a fixed random
   order: the ranking key it used to apply did not hold in our tests, so the
   order no longer pretends to know which is best.
2. **Read.** Figures come only from the company's own filings: SEC for the
   US, the issuers' own reports for the Nordics. Every number carries its
   source.
3. **Value.** A bear, base and bull value per share from the cash the
   business makes, at a 9.5 % required return. Four quality tests are
   printed beside it as information.
4. **Queue.** Every valued company is held against its value every night
   (next section).
5. **You decide.** The machine writes no verdict, no fair value and no buy
   price on its own. A person does that, in a session, with the reasons
   written down.

## Every night, without you

1. **It finds new reports.** SEC EDGAR for US filers (10-Q, 10-K, 8-K item
   2.02), the Nasdaq Nordic and Oslo feeds for Nordic issuers, the report
   date elsewhere.
2. **It reads them.** The document is fetched and read twice by a model
   ([`vss/reportread.py`](vss/reportread.py)). A figure the two readings
   disagree on is dropped, and every figure kept carries the sentence it
   came from.
3. **It values the company again** on its last four quarters
   ([`vss/outlook.py`](vss/outlook.py)) and compares with its own reading
   before the report, so a bias in the method cancels and what is left is
   what the report changed.
4. **It tells you only if the outcome changed**: the value moved 10 % or
   more, guidance was cut, a rule fired, or a headline says profit warning,
   guidance change, CEO or CFO leaving, a bid or a delisting. The price
   reaching a value line is a message too. Everything else is a line in the
   night's report: "read: nothing changed".
5. **It rebuilds the master list**, `reports/HUVUDLISTA.md`
   ([`tools/master_list.py`](tools/master_list.py)).

None of this decides. A machine reading is a flag to read the report; a buy
still needs a full valuation and a person.

## What it can do

| What | Command |
|---|---|
| Value any US company from SEC filings, with four quality tests | `tools/warren.py KO` |
| A rough bear / base / bull for any listing Yahoo covers | `tools/rough_fv.py EVO.ST` |
| The nightly run: every watched name against its values | `vss run` |
| The queue: price lines, new reports read, outlook changes | `vss queue` |
| The master list of every company looked at | `tools/master_list.py` |
| List and download a Nordic issuer's reports (Nasdaq Nordic, Oslo) | `vss nordic --ticker PACT.ST --reports` |
| Read a Nordic issuer's ESEF report package | `vss esef --ticker X --draft` |
| A model's draft of a report's statement lines, gated by quote checks | `vss pdfdraft` |
| Read one report for figures and the rules' red flags | `vss earnings --ticker X --url ...` |
| A figure counts as checked only when two independent machine readings print the same digits | `tools/cross_verify.py` |
| The shadow book: every "no" priced against the index at 1, 3, 6 and 12 months | `vss shadow` |
| Every closed position against OMXS30 and the S&P 500 ("sold too early?") | `vss sales` |
| Companies that fell hard on news, with the headline | `vss newsdrop` |
| One read-only page of the whole book | `vss overview` |
| Walk one company through the review, step by step, in Claude Code | `/review` |
| An independent review of the whole method and code, in Claude Code | `/granska` |

Foreign dividend withholding in a Swedish ISK (Finland 35 %, Denmark 27 %,
Norway 25 %, US 15 %) is counted as the plain yearly cost it is.

## Four habits it enforces

1. **Figures come only from the company's own filings.** No source, no number.
2. **You write your growth view down before you see the market's.** A view
   written after seeing the price doesn't count.
3. **A rule enters or leaves only on a test registered in advance.** A rule
   that sounds right is not evidence; since November 2026 a decision rule
   changes only on a backtest written down before it runs.
4. **Every "no" is tracked.** Each refusal is priced against the index, so
   you find out whether your no's were right.

## What the backtests taught us (November 2026)

**We did not take the method on trust.** Between 29 October and 9 November
2026 every mechanical rule was put through a test on history written down
**before** it ran: 26 attempts, every one logged, the failures too. The US
from SEC filings; prices with the delisted put back, and the whole Nordic
test, from a commercial vendor under a personal licence (25,854 stocks,
18,336 of them later delisted). The vendor's data and the figures computed
from it stay private, so the results are verdicts in words; the scripts
(`tools/backtest/`) and the rule each test was held to are public.
**Attempt by attempt: [reference/backtest/WHAT-WE-TESTED.md](reference/backtest/WHAT-WE-TESTED.md).**

The bar: better in both markets **and** both halves of each period, and
from attempt #25 above what 1,000 random relabellings give.

| Rule | What the test found | Ruling |
|---|---|---|
| A price stop under the purchase price | no stop level helped; with real trading costs every one cost money | removed (E162) |
| Buy only after a 15-50 % fall from the high | did not help in either market | removed (E161) |
| The screener's ranking key | did not sort returns by decile in both markets | removed (E167) |
| Kills on falling revenue, margin and receivables | did not separate returns | removed (E163) |
| Debt limits | did not lift the mean; the loss tail is re-tested on new data (#26) | removed (E168) |
| Quality tests Q1-Q4 as a drop rule | did not separate returns | information only (E168) |
| The buy-price cushion as a binding line | did not separate returns | information only (E168) |

**What stayed:** the valuation, the growth view written before the price,
figures only from the companies' own filings, positive free cash flow, the
reading of reports, at most 6 % of the portfolio in one name, and the
shadow book.

**What it means:** survivorship flattered the first run badly; the Nordic
result held in sample but not in a check run once on later years; and
against Magic Formula, Quantitative Value, O'Shaughnessy and Piotroski ours
beat none of twelve comparisons. **No proven edge.** A broad index fund is
the base for the author's money; this method is the part that is studied,
not trusted. The next test (#26) runs only on new data, in April 2027.

## What's in the box

| Folder | What it is |
|---|---|
| `vss/` | the program (`python -m vss <command>`) |
| `tools/` | tools run by hand, the master list, the backtest scripts |
| `config/` | the watchlist, the queue, the screen's universe: **the author's own, as an example** |
| `reference/` | the rules on two pages ([FRAMEWORK.md](reference/FRAMEWORK.md)), every ruling with its date and reason ([archive/](reference/archive/)), the reviews of each company |
| `docs/` | [the book](docs/the-method/), [the manual](docs/MANUAL.md) (tasks step by step), [the command reference](docs/REFERENCE.md) (generated from the code), [why it behaves as it does](docs/EXPLANATION.md), [the changelog](docs/CHANGELOG.md) |
| `AGENTS.md` | for an AI agent: which commands change nothing, which write, which reach the phone |
| `deploy/` | the nightly jobs (user-level systemd) |
| `.claude/` | the Claude Code commands `/review` and `/granska` |
| `tests/` | about 3,000 tests |

Words like *strike*, *MBP*, *tier* or *WATCH-GATED* are explained in the
**[glossary](GLOSSARY.md)**.

## What it is not

- **Not financial advice**, and not a recommendation to buy or sell anything.
  It is one private investor's method, shared as it is.
- **Not a trading bot.** It places no orders, reads no broker account and has
  no view on next week.
- **Not a website.** It is a command-line tool and a set of rules.

## Disclosure

**As of 2026-11-09 I own shares in AcadeMedia (ACAD.ST)**, and one share of
Cognizant (CTSH) and two of Central Garden & Pet (CENTA), both being sold.
The record in this repository shows when I bought and sold others. The
values and lines in `config/` are my personal working notes. **Nothing here
is a recommendation to buy, sell or hold any security.** The watchlist's and
queue's `HELD` entries are the current record if this line is out of date.

## Data

No market data is shipped. You fetch it yourself, at run time: prices from
Yahoo Finance (yfinance), filings from SEC EDGAR, Nordic reports from the
Nasdaq Nordic feed, Euronext Oslo's NewsWeb and MFN, headlines from Google
News RSS. Reports are read by the model you choose through OpenRouter. The
universe lists in `config/universe/` hold only tickers, names and listing
facts, each with its source in its `.meta.json` (S&P lists from Wikipedia,
CC BY-SA 4.0; STOXX Europe 600 from iShares; Nordic lists from Yahoo).

## Questions?

**Shared as-is. I don't take issues or pull requests.** Open the repository
in [Claude Code](https://claude.com/claude-code) and ask it: `CLAUDE.md`
tells it how the project works, and it can explain any part for as long as
you like.

---

*Built by Veljko Radan, with Claude. MIT licence: use it, change it, share
it, just keep the credit. See [`LICENSE`](LICENSE).*
