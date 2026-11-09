"""The LIVE screener's ranking key and drawdown band, measured on the US run.

    .venv/bin/python -m tools.backtest.measure_key [run-dir-name]

Review 2026-11-08 M3: `vss/ranking.py` ranks on operating profitability
(EBIT / total assets, E43) plus earnings yield (EBIT / EV), rank-summed, and
the weekly screen takes only names 15-50% below their 52-week closing high.
Neither had been measured; the backtests measured the method's fv/price and
a plain EBIT/EV. This prints, per horizon:

- the key's fifths (worst rank sum -> best), mean excess return over the
  S&P 500 total return, averaged over dates, and the share of dates on
  which the best fifth beat the worst;
- the same inside the 15-50% band only, and the band against the rest.

The figures come from private EODHD prices and stay in this private repo.
Every run of this is an attempt in reference/backtest/ATTEMPTS.md.
"""
from __future__ import annotations

import statistics
import sys
from datetime import date, timedelta
from pathlib import Path

from . import eodhd_reprice as EP
from . import measure as M

BAND = (0.15, 0.50)


def drawdown(sym: str | None, day: date) -> float | None:
    """Fall from the 52-week closing high to the day's close, as the screen
    reads it (unadjusted close is what the screen sees; adjusted for splits
    so a split is not a fall)."""
    if not sym:
        return None
    f = EP.frame(sym)
    if f is None:
        return None
    w = f[(f.index > (day - timedelta(days=365)).isoformat()) & (f.index <= day.isoformat())]
    if len(w) < 200:
        return None
    hi, now = float(w["adjusted_close"].max()), float(w["adjusted_close"].iloc[-1])
    return None if hi <= 0 else 1 - now / hi


def key_order(rows):
    rs = [r for r in rows if r.get("ebit") is not None and r.get("assets") and r.get("ebit_ev") is not None]
    op = {id(r): i for i, r in enumerate(sorted(rs, key=lambda r: -r["ebit"] / r["assets"]))}
    ey = {id(r): i for i, r in enumerate(sorted(rs, key=lambda r: -r["ebit_ev"]))}
    return sorted(rs, key=lambda r: op[id(r)] + ey[id(r)])   # best first


def fifths(rows, h):
    rs = key_order(rows)
    if len(rs) < 25:
        return None
    k = len(rs)
    best_first = [[M.excess(r, h) for r in rs[i * k // 5:(i + 1) * k // 5]] for i in range(5)]
    return best_first[::-1]                                    # worst -> best


def report(data, h, label, keep=lambda r: True):
    per, wins, n = [[] for _ in range(5)], 0, 0
    for _, rows in sorted(data.items()):
        q = fifths([r for r in M.usable(rows, h) if keep(r)], h)
        if not q:
            continue
        n += 1
        for i in range(5):
            per[i].append(statistics.mean(q[i]))
        wins += statistics.mean(q[4]) > statistics.mean(q[0])
    if not n:
        return f"| {label} | {h} y | too few names | | |"
    cells = " / ".join(f"{100 * statistics.mean(x):+.1f}" for x in per)
    spread = statistics.mean(per[4]) - statistics.mean(per[0])
    return f"| {label} | {h} y | {cells} | {100 * spread:+.1f} pp | {wins}/{n} |"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    run = Path("data/backtest") / (argv[0] if argv else "run-eodhd-m5")
    data = M.load(run)
    for rows in data.values():
        for r in rows:
            r["_dd"] = drawdown(r.get("eodhd_symbol"), date.fromisoformat(r.get("trading_day") or r["as_of"]))
    in_band = lambda r: r["_dd"] is not None and BAND[0] <= r["_dd"] <= BAND[1]
    print(f"# Live ranking key (E43) and drawdown band, {run.name}\n")
    print("| Set | Horizon | fifths worst -> best key, mean excess (pp) | best - worst | best > worst |")
    print("|---|---|---|---|---|")
    for h in (3, 5):
        print(report(data, h, "all valued"))
        print(report(data, h, "inside 15-50% band", in_band))
    print("\n| Horizon | inside band | outside band | dates |\n|---|---|---|---|")
    for h in (3, 5):
        ins, outs = [], []
        for _, rows in sorted(data.items()):
            u = M.usable(rows, h)
            a = [M.excess(r, h) for r in u if in_band(r)]
            b = [M.excess(r, h) for r in u if r["_dd"] is not None and not in_band(r)]
            if a and b:
                ins.append(statistics.mean(a)); outs.append(statistics.mean(b))
        print(f"| {h} y | {100 * statistics.mean(ins):+.1f} | {100 * statistics.mean(outs):+.1f} | {len(ins)} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
