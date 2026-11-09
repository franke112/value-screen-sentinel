"""TEST 2 (wrez-devour, pre-registered in reference/backtest/ATTEMPTS.md #11):
concentration -- equal-weight portfolios of 3, 5, 10, 20 names.

    .venv/bin/python -m tools.backtest.concentration > data/backtest/devour-conc/MEASURE.md

Rankings: fv/price (Nordic), the E43 key (Nordic and US). For each N:
1. ANNUAL REBALANCE: the top N on each test date held one year, chained
   (Nordic 2010-2022, US 2016-2021): mean and spread of the yearly excess,
   worst year, and the compounded strategy against the compounded benchmark.
2. BUY AND HOLD 3 and 5 years from each test date: mean, standard deviation,
   worst and best over start dates, and per half.
3. BOOTSTRAP: N names drawn at random from the ranking's best fifth on each
   date (10,000 draws a date, seed 20261108), 3-year excess: the spread a
   holder of N qualifying names faces (5th / 50th / 95th percentile, pooled
   over dates with equal weight), and the spread of the strategy's mean over
   all dates (one draw a date, averaged).
The whole best fifth is the reference line ("fifth").
"""
from __future__ import annotations

import random
import statistics
import sys

from . import devour as D
from . import measure as MS
from . import measure_key as MK

NS = (3, 5, 10, 20)
DRAWS = 10_000
SEED = 20261108


def ranked(rows, how):
    if how == "E43 key":
        return MK.key_order(rows)
    return sorted((r for r in rows if MS.fv_ratio(r) is not None), key=MS.fv_ratio, reverse=True)


def pick(rows, how, n):
    rs = ranked(rows, how)
    if len(rs) < 25:
        return None
    return rs[:len(rs) // 5] if n == "fifth" else rs[:n]


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def main() -> int:
    print("# Test 2: concentration (attempt #11)\n")
    rng = random.Random(SEED)
    for market, how in (("nordic", "fv/price"), ("nordic", "E43 key"), ("us-bust", "E43 key"),
                        ("us-last", "E43 key")):
        data = D.load(market)
        print(f"\n## {market}, ranked by {how}\n")
        print("| N | annual rebalance: mean yearly excess | sd | worst year | compounded strategy vs benchmark "
              "(per year) | 3 y hold: mean | sd | worst / best | half 1 / half 2 | 5 y hold: mean | sd | worst / best |")
        print("|---|---:|---:|---:|---|---:|---:|---|---|---:|---:|---|")
        for n in NS + ("fifth",):
            yearly, s_cum, b_cum = [], 1.0, 1.0
            for d, rows in sorted(data.items()):
                sel = pick(MS.usable(rows, 1), how, n)
                if not sel:
                    continue
                ret = statistics.mean(MS.excess(r, 1) + _idx(r, 1) for r in sel)
                b = _idx(sel[0], 1)
                yearly.append(ret - b)
                s_cum *= 1 + ret
                b_cum *= 1 + b
            yrs = len(yearly)
            hold = {}
            for h in (3, 5):
                xs = []
                for d, rows in sorted(data.items()):
                    sel = pick(MS.usable(rows, h), how, n)
                    if sel:
                        xs.append((d, statistics.mean(MS.excess(r, h) for r in sel)))
                hold[h] = xs
            def stats(xs):
                v = [x for _, x in xs]
                if not v:
                    return "–", "–", "–"
                return (D.pp(statistics.mean(v)), D.pp(statistics.pstdev(v)),
                        f"{D.pp(min(v))} / {D.pp(max(v))}")
            h3, h5 = stats(hold[3]), stats(hold[5])
            halves = " / ".join(D.pp(D.mean([x for d, x in hold[3] if D.half_of(market, d) == hf])) for hf in (0, 1))
            cagr = (s_cum ** (1 / yrs) - 1, b_cum ** (1 / yrs) - 1) if yrs else (None, None)
            print(f"| {n} | {D.pp(D.mean(yearly))} | {D.pp(statistics.pstdev(yearly)) if yearly else '–'} | "
                  f"{D.pp(min(yearly)) if yearly else '–'} | {D.pp(cagr[0])} vs {D.pp(cagr[1])} ({yrs} y) | "
                  f"{h3[0]} | {h3[1]} | {h3[2]} | {halves} | {h5[0]} | {h5[1]} | {h5[2]} |")
        print("\nBootstrap, 3 years: N names drawn from the best fifth (excess, pp)\n")
        print("| N | single date-portfolio 5% / 50% / 95% | sd | strategy mean over dates 5% / 50% / 95% | sd |")
        print("|---|---|---:|---|---:|")
        fifths = {d: pick(MS.usable(rows, 3), how, "fifth") for d, rows in sorted(data.items())}
        fifths = {d: [MS.excess(r, 3) for r in f] for d, f in fifths.items() if f}
        for n in NS:
            single, strat = [], []
            for _ in range(DRAWS):
                per = []
                for d, xs in fifths.items():
                    m = statistics.mean(rng.sample(xs, min(n, len(xs))))
                    per.append(m)
                single.extend(per)
                strat.append(statistics.mean(per))
            print(f"| {n} | {D.pp(pct(single, .05))} / {D.pp(pct(single, .5))} / {D.pp(pct(single, .95))} | "
                  f"{D.pp(statistics.pstdev(single))} | {D.pp(pct(strat, .05))} / {D.pp(pct(strat, .5))} / "
                  f"{D.pp(pct(strat, .95))} | {D.pp(statistics.pstdev(strat))} |")
    return 0


def _idx(r, h):
    ir = r["index_returns"]
    return ir.get(str(h), ir.get(h))


if __name__ == "__main__":
    sys.exit(main())
