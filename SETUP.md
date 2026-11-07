# Setting up vss

vss is a command-line tool and a set of rules, designed to be worked through
in [Claude Code](https://claude.com/claude-code) sessions. This gets it
running on a Linux machine. It was built and runs on Debian, Python 3.13.
From a fresh clone it takes about five minutes: clone and install took 29
seconds on 2026-11-07, the first full run 14 seconds; the rest is filling in
the settings file.

## 1. Install

```bash
git clone https://github.com/franke112/value-screen-sentinel.git ~/vss
cd ~/vss
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The systemd units in `deploy/` assume the checkout is at `~/vss` (`%h/vss`).

## 2. Settings

```bash
mkdir -p ~/.config/vss
cp deploy/vss.env.example ~/.config/vss/vss.env
chmod 600 ~/.config/vss/vss.env
```

Fill in what you use. Only **`VSS_SEC_CONTACT`** is needed for the US
routes; the rest is optional:

| Variable | What for |
|---|---|
| `VSS_SEC_CONTACT` | Your name and e-mail. SEC EDGAR requires it to fetch filings. |
| `VSS_OPENROUTER_KEY` | The report reader. Any OpenRouter model, set by `VSS_OPENROUTER_MODEL` (default `deepseek/deepseek-v4-flash`). |
| `NTFY_TOPIC` / `VSS_NTFY_URL` | Phone alerts via [ntfy](https://ntfy.sh): the nightly run, the queue and the filing watcher. Pick a long random topic name: anyone who knows it can read it. |
| `HEALTHCHECK_URL` | Optional dead man's switch via healthchecks.io. |

Never commit this file.

## 3. Your data, fetched by you

**No market data is shipped in this repository.** Prices come from Yahoo
Finance (via yfinance), whose terms allow personal use and not
redistribution. Filings come from SEC EDGAR (public) and the Nasdaq Nordic
disclosure feed, Nordic report PDFs from MFN's public feed. No broker
account is ever read. You fetch your own:

```bash
.venv/bin/python -m vss run --dry-run      # fetches prices for the watchlist, writes nothing
.venv/bin/python -m vss xbrl --ticker CPRT --annual   # a US filer's figures from SEC
.venv/bin/python -m vss screen --weekly --no-notify   # the screener over the universe lists
.venv/bin/python tools/warren.py KO AAPL             # would Warren own it? any US filer
.venv/bin/python -m vss queue --no-notify            # every valued name against its lines
.venv/bin/python tools/fetch_mfn.py EVO.ST --kinds annual   # a Nordic issuer's annual reports as PDF
```

The tests read a few price files too. Fetch your own copies once:

```bash
.venv/bin/python tools/fetch_test_fixtures.py
.venv/bin/python -m pytest -q
```

Without them, the tests that need them **skip and say so**. With them,
two tests about Monster Beverage still skip: they were built on a glitch in
Yahoo's data that Yahoo has since corrected. `tests/fixtures/VENDOR-DATA.json`
records exactly what each file held. The screener acceptance snapshot of
2026-08-21 cannot be rebuilt at all, so its tests stay skipped.

## 4. The watchlist is mine -- start your own

`config/watchlist.yaml` is the owner's real record: the names, verdicts,
growth views and trades, kept as an example of the method in use. To use
the tool for yourself, start your own watchlist and register your own growth
views **before** you run a valuation (`reference/FRAMEWORK.md`, E28).
`config/queue.yaml` is mine as well: my valued names and my sell lines. Clear
it, value your own names, and `tools/build_queue.py --write` harvests the
strikes back into it. The
rulings in `reference/FRAMEWORK-EDITS.md` are mine too -- read them as the
reasoning behind the current rules, and make your own.

## 5. Scheduling (optional)

`deploy/README.md` describes every unit: the nightly run, the weekly screen,
the filing watcher, the dead man's switch, the queue and the PDF fetcher.
Install them as user units:

```bash
mkdir -p ~/.config/systemd/user
cp deploy/*.service deploy/*.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now vss.timer vss-screen.timer vss-checkin.timer \
    vss-watch.timer vss-queue.timer vss-mfn.timer
sudo loginctl enable-linger $USER     # so they fire when you are logged out
```

| Timer | When | What |
|---|---|---|
| `vss.timer` | daily 22:30 | the nightly run over the watchlist |
| `vss-mfn.timer` | daily 22:40 | new Nordic report PDFs for the queue's names |
| `vss-queue.timer` | weekdays 22:50 | the queue: buy / look / sell lines, gates, reports |
| `vss-screen.timer` | Saturdays 08:00 | the weekly screen |
| `vss-checkin.timer` | daily 09:30 | the check that everything above ran |
| `vss-watch.timer` | see `deploy/README.md` | new filings for watched names |

## 6. Working with Claude Code

Open the folder in Claude Code. `CLAUDE.md` tells every session how to
work here: what costs effort, what a session may and may not write, and
when to stop and ask. The `/review` command walks one name through the
playbook. **The tool measures; you decide** -- no session writes a verdict,
a fair value or a buy price on its own.

*Not financial advice. See [LICENSE](LICENSE) (MIT).*
