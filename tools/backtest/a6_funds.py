"""TEST A6 re-run (ATTEMPTS #20b): our best fifths against real value funds,
in SEK, before and after costs.

    DEVOUR_LB=clean .venv/bin/python -m tools.backtest.a6_funds > data/backtest/devour-funds-r2/MEASURE.md

Funds (yfinance through `pilot.prices`, checked against Avanza's 5-year
series before the pre-registration): adjusted close, converted to SEK at
the day's rate. Ours: each best-fifth name's local return converted at the
start and end days' rates; NET = one round trip at #18's Mini costs.
"""
from __future__ import annotations

import statistics
import sys

from . import devour as D
from . import measure as MS
from . import measure_key as MK
from . import pilot as PL

FUNDS = {"IS3S.DE": ("EUR", 0.0030), "XDEV.DE": ("EUR", 0.0025), "PSWD.DE": ("EUR", 0.0039),
         "AVUV": ("USD", 0.0025), "AVDV": ("USD", 0.0036)}
PAIRS = {"nordic": ("AVDV", "IS3S.DE", "XDEV.DE", "PSWD.DE"),
         "us-bust": ("AVUV", "IS3S.DE", "XDEV.DE", "PSWD.DE")}
_FX = {}


def fx_sek(cur, day):
    if cur == "SEK":
        return 1.0
    t = f"{cur}SEK=X"
    if t not in _FX:
        _FX[t] = PL.prices(t)
    got = PL.close_on(_FX[t], day, "Close") if _FX[t] is not None else None
    return got[1] if got else None


def sek_return(ret, cur, start, end):
    if ret is None:
        return None
    if ret <= -1:
        return -1.0
    a, b = fx_sek(cur, start), fx_sek(cur, end)
    return None if not a or not b else (1 + ret) * b / a - 1


def fund_return(t, start, end):
    f = PL.prices(t)
    a, b = PL.close_on(f, start, "Adj Close"), PL.close_on(f, end, "Adj Close")
    if a is None or b is None:
        return None
    cur = FUNDS[t][0]
    return sek_return(b[1] / a[1] - 1, cur, start, end)


def best_fifth(u, how):
    rs = MK.key_order(u) if how == "E43 key" else sorted(
        (r for r in u if MS.fv_ratio(r) is not None), key=MS.fv_ratio, reverse=True)
    return rs[:len(rs) // 5] if len(rs) >= 25 else []


def main() -> int:
    print("# A6 re-run: our best fifths against value funds, in SEK (attempt #20b)\n")
    print("Fund = adjusted close in SEK, after its TER (+TER = before fees). Ours gross / net of one "
          "Mini round trip (#18). Mean over the overlapping test dates, %.\n")
    print("| Market | Ours | Fund | h | dates | ours gross | ours net | fund | fund +TER | "
          "ours net - fund | dates ours net > fund |")
    print("|---|---|---|---|---:|---:|---:|---:|---:|---:|---|")
    for market, funds in PAIRS.items():
        data = D.load(market)
        for how in ("fv/price", "E43 key"):
            for fund in funds:
                for h in (1, 3, 5):
                    xs = []
                    for d, rows in sorted(data.items()):
                        u = MS.usable(rows, h)
                        sel = best_fifth(u, how)
                        if not sel:
                            continue
                        start = D.start_day(sel[0])
                        end = PL.years_after(start, h)
                        fr = fund_return(fund, start, end)
                        if fr is None:
                            continue
                        g, n = [], []
                        for r in sel:
                            cur = "USD" if market != "nordic" else (r.get("currency") or "SEK")
                            ret = r["returns"].get(str(h), r["returns"].get(h))
                            s = sek_return(ret, cur, start, end)
                            if s is None:
                                continue
                            c = D.trade_cost(r, market, "mini")
                            g.append(s)
                            n.append(-1.0 if s <= -1 else (1 - c) * (1 + s) * (1 - c) - 1)
                        if not g:
                            continue
                        ter = FUNDS[fund][1]
                        xs.append((d, statistics.mean(g), statistics.mean(n), fr, (1 + fr) * (1 + ter) ** h - 1))
                    if not xs:
                        print(f"| {market} | {how} | {fund} | {h} y | 0 | | | | | | |")
                        continue
                    m = lambda i: 100 * statistics.mean(x[i] for x in xs)
                    diff = [x[2] - x[3] for x in xs]
                    print(f"| {market} | {how} | {fund} | {h} y | {len(xs)} ({xs[0][0][:4]}-{xs[-1][0][:4]}) | "
                          f"{m(1):+.1f} | {m(2):+.1f} | {m(3):+.1f} | {m(4):+.1f} | "
                          f"{100 * statistics.mean(diff):+.1f} | {sum(x > 0 for x in diff)}/{len(diff)} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
