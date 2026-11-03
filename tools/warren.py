"""Would Warren own it? E145's quality tests and the method's fair value on any
SEC filer, straight from EDGAR's companyfacts -- no store, no growth view.

    .venv/bin/python tools/warren.py KO PEP CTSH

For each ticker: the price, bear / base / bull per share, Q1-Q4 with their
figures, and the section 4.2 hard kills the tagged quarters can show. It is
`tools/backtest/method.py` on today's date (the rules M1-M8 in its docstring
replace a session's hand-read store), so it is a SCREEN, not a strike: a name
that passes is one worth a hand read, never a buy. Q5 (what it sells, to whom,
why the customer returns) is a sentence a person writes and is not here.
US filers only (us-gaap tags); IFRS filers (20-F) and non-US listings are
refused, not guessed.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.backtest import method as ME  # noqa: E402
from tools.backtest import pit as P  # noqa: E402
from vss import history as HI  # noqa: E402
from vss import newsdrop as N  # noqa: E402
from vss import valuation as VA  # noqa: E402

TESTS = {"Q1": "return on tangible capital >= 15%",
         "Q2": "owner earnings positive, operating profit never below half its peak",
         "Q3": "net debt <= 3x FCF0 (4.5x if profit never fell >15%)",
         "Q4": "acquisitions return >= 9.5% (repeat buyers only)"}


def price(ticker: str) -> float | None:
    try:
        import yfinance as yf
        h = yf.Ticker(ticker).history(period="5d")["Close"]
        return float(h.iloc[-1]) if len(h) else None
    except Exception:  # noqa: BLE001
        return None


def fmt(x) -> str:
    return "--" if x is None or x != x else f"{x:,.2f}"


def bull(row: dict, facts: dict, as_of: date, ticker: str) -> float | None:
    """The bull case: E144's derived bull growth (or base + 1pp under the
    cap) on the base flow, without the deal programme's charge."""
    if None in (row.get("fcf_mean"), row.get("shares"), row.get("net_debt"), row.get("g_base")):
        return None
    d = HI.derived_growth(P.history_at(facts, as_of, ticker=ticker))
    g = d.bull if d else min(HI.GROWTH_CAP, row["g_base"] + 0.01)
    f = row["fcf_mean"] * (row.get("level_base") or 1.0)
    try:
        return VA.equity_value_per_share(fcf0=f * (1 + g), growth=g,
                                         net_cash=-row["net_debt"], shares=row["shares"])
    except Exception:  # noqa: BLE001
        return None


def one(ticker: str, ciks: dict[str, int], as_of: date) -> None:
    cik = ciks.get(ticker.upper())
    if cik is None:
        print(f"{ticker}: not an SEC filer (no CIK) -- refused\n")
        return
    facts, sic = N.company_facts(cik)
    row = ME.evaluate(facts, as_of, ticker=ticker, cik=cik, sic=sic)
    px = price(ticker)
    base = row.get("fv_base")
    print(f"== {ticker}  price {fmt(px)}  |  bear {fmt(row.get('fv_bear'))}  "
          f"base {fmt(base)}  bull {fmt(bull(row, facts, as_of, ticker))}"
          + (f"  |  price/base {px / base:.2f}x" if px and base and base > 0 else ""))
    if row["status"] != "ok":
        print(f"   value: {row['status']}")
    for q, label in TESTS.items():
        passed = row["quality"].get(q)
        mark = {True: "PASS", False: "FAIL", None: "n/a "}[passed]
        print(f"   {q} {mark}  {label}: {row['quality_figures'].get(q, '')}")
    fails = [k["rule"] for k in row.get("kills", []) if k.get("state") == "FAIL"]
    print(f"   hard kills (section 4.2, from the tagged quarters): "
          f"{', '.join(fails) if fails else 'none fired'}"
          "  [an outlook cut, 4.2.3, needs the press releases read]")
    quality = row["status"] == "ok" and not fails and all(
        row["quality"].get(q) is not False for q in ("Q1", "Q2", "Q3"))
    if not quality:
        verdict = "no -- fails the quality bar (or no value)"
    elif px and base and px > base:
        verdict = f"the business passes, the price does not ({px / base:.2f}x base) -- wait"
    else:
        verdict = "passes and trades under base -- worth a hand read (Q5, the releases, the deals)"
    if quality and row["quality"].get("Q4") is False:
        verdict += "; Q4 fails, so the deals destroy value -- one tier lower"
    print(f"   -> {verdict}\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--asof", type=date.fromisoformat, default=date.today())
    a = ap.parse_args(argv)
    ciks = N.sec_ciks()
    for t in a.tickers:
        one(t.upper(), ciks, a.asof)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
