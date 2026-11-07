# vss -- value-screen sentinel

**A value-investing method one person can actually keep to, and the machine
that keeps it honest.** It runs together with [Claude Code](https://claude.com/claude-code).

There are about two thousand companies you could buy a piece of, and one
person with a few evenings a week. vss screens them, reads the companies' own
reports, works out what a business is worth and what today's price already
assumes, and watches every name you have valued, every night.
**It never tells you to buy anything.** It measures, you decide, and it keeps
the record of what you decided and why.

> **How it works and why, in 23 short chapters (or a ten-minute route):**
> **[franke112.github.io/value-screen-sentinel/the-method](https://franke112.github.io/value-screen-sentinel/the-method/)**
> *(på svenska: [the-method/sv](https://franke112.github.io/value-screen-sentinel/the-method/sv/))*

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

Every company you have valued sits in a queue. One message reaches your
phone, and only when something changes (the messages are in Swedish: *titta*
is "look", *rapport* is "report"):

```
TITTA DHI 152.28 <= 156.86 (0.83x base 184.54, strike) -- value it properly now
RAPPORT GNTX: 2026-11-06 10-Q
```

## Try it in five minutes

Linux, Python 3.11+. Tested from a fresh clone: 29 seconds to install, 14
seconds for the first run.

```bash
git clone https://github.com/franke112/value-screen-sentinel.git ~/vss && cd ~/vss
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m vss run --dry-run        # the nightly report, writes nothing
export VSS_SEC_CONTACT='mytool/1.0 (you@example.com)'   # SEC asks every caller for a contact
.venv/bin/python tools/warren.py KO AAPL     # would Warren own it?
```

Then **[`SETUP.md`](SETUP.md)** covers the settings, starting your own
watchlist and queue, phone alerts and the nightly timers.

## How it works

```
 screen  ──>  read  ──>  value  ──>  queue  ──>  you decide
 weekly       the        bear /      nightly,    in a Claude Code
 ranking      company's  base /      one         session, every
 of ~2,000    own        bull per    message     reason written
 companies    reports    share       on change   down
```

1. **Screen.** Every Saturday it ranks the market on quality and cheapness,
   among companies that have fallen 15-50% from their high.
2. **Read.** Figures come only from the company's own filings: SEC for the
   US, the issuers' own report PDFs for the Nordics. Every number carries
   its source.
3. **Value.** Four quality tests come first: a business that fails them is
   not worth a price. Then a bear, base and bull value per share, from ten
   years of cash flow at a 9.5% required return.
4. **Queue.** Every valued company is held against its lines every night.
   You get one message when one crosses a line, a ban lifts or a report
   comes in.
5. **You decide.** The machine writes no verdict, no fair value and no buy
   price on its own. A person does that, in a session, with the reasons
   written down.

## Four habits it enforces

1. **Figures come only from the company's own filings.** No source, no number.
2. **You write your growth view down before you see the market's.** A view
   written after seeing the price doesn't count.
3. **A failed test is final.** A company that fails on something other than
   price does not come back because the price fell. Only a new fact brings it
   back: a new report, a changed forecast.
4. **Every "no" is tracked.** Each refusal is measured against the index at
   1, 3, 6 and 12 months, so you find out whether your no's were right.

## What's in the box

| Folder | What it is |
|---|---|
| `vss/` | the program (`python -m vss <command>`) |
| `tools/` | tools run by hand: `warren.py`, `rough_fv.py`, `fetch_mfn.py`, ... |
| `config/` | the watchlist, the queue, the screen's universe: **the author's own, as an example** |
| `reference/` | the rules and every ruling since, with dates and reasons: [start here](reference/README.md) |
| `docs/` | [the book](docs/the-method/) and [the technical manual](docs/MANUAL.md) |
| `deploy/` | the nightly jobs (user-level systemd) |
| `tests/` | about 3,000 tests |
| `reports/`, `data/`, `sources/` | what the runs write; your own fetched data lands here |

Words like *strike*, *MBP*, *tier* or *WATCH-GATED* are explained in the
**[glossary](GLOSSARY.md)**.

## An honest result

Back-tested on US large caps 2016-2021 (survivors only), ranking by value
against price did **not** sort later returns
([`reference/backtest/`](reference/backtest/)). What did hold up: the dearest
fifth did worst, and the quality tests helped. That is why the tool says
"wait" far more often than anything else.

## What it is not

- **Not financial advice**, and not a recommendation to buy or sell anything.
  It is one private investor's method, shared as it is.
- **Not a trading bot.** It places no orders, reads no broker account and has
  no view on next week.
- **Not a website.** It is a command-line tool and a set of rules.

## Disclosure

**I own shares in AcadeMedia (ACAD.ST), Cognizant (CTSH) and Central Garden
& Pet (CENTA)** as of 2026-11-07 (the CTSH and CENTA positions are being
exited, two CENTA shares left; Cirrus Logic, CRUS, was sold in full on
2026-10-23). The record in this repository shows when I bought and sold
others. The fair values, buy limits and stops in `config/watchlist.yaml` are
my personal working notes. **Nothing here is a recommendation to buy, sell or
hold any security.** If my holdings change, this line may be out of date: the
watchlist's `status: HELD` entries are the current record.

## Data

No market data is shipped. Prices come from Yahoo Finance (via yfinance),
filings from SEC EDGAR, the Nasdaq Nordic feed and MFN's public news feed,
and headlines from Google News RSS. You fetch them yourself, at run time.
The universe lists in `config/universe/` hold only tickers, names and
listing facts, each with its source in its `.meta.json` (S&P lists from
Wikipedia, CC BY-SA 4.0; STOXX Europe 600 from iShares; Nordic lists from
Yahoo).

## Questions?

**Shared as-is. I don't take issues or pull requests.** Open the repository
in [Claude Code](https://claude.com/claude-code) and ask it: `CLAUDE.md`
tells it how the project works, and it can explain any part for as long as
you like.

---

*Built by Veljko Radan, with Claude. MIT licence: use it, change it, share
it, just keep the credit. See [`LICENSE`](LICENSE).*
