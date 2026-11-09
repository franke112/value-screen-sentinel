"""TEST 1 (wrez-devour, pre-registered in reference/backtest/ATTEMPTS.md #10):
stop-losses, with and without re-entry.

    .venv/bin/python -m tools.backtest.stops            # writes data/backtest/devour-stops/
    .venv/bin/python -m tools.backtest.stops --summary  # the tables

Selections per date and horizon (among `measure.usable` rows):
- fvp5: the cheapest fifth by fv/price;
- key5: the best fifth by the live E43 key;
- method: the method's buy rule (US only; it fired 5 times in 12 Nordic years);
- all: every usable name (the stop's effect with no selection).

Variants: no stop; stops 8, 12, 20, 30% below the entry close, measured on
the ADJUSTED close (the old `nordic.stop_return` used the printed close,
which a split or a large dividend also moves); each without re-entry (cash
to the horizon) and with re-entry: at each month-end after an exit the name
is bought back if it still meets its selection at that price against the
test day's cross-section (fundamentals frozen at the test day; no report is
read mid-period -- a stated limit), and the stop resets at the new entry.
Cash earns nothing, as in the old stop.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date

from . import devour as D
from . import measure as MS
from . import pilot as PL

OUT = D.BT / ("devour-stops" + D.SUFFIX)
STOPS = (None, 0.08, 0.12, 0.20, 0.30)
HORIZONS = (1, 3, 5)


def variants():
    yield ("none", None, False)
    for s in STOPS[1:]:
        yield (f"stop{int(s * 100)}", s, False)
        yield (f"stop{int(s * 100)}+re", s, True)


def requalifier(sel_name: str, sel: list[dict], universe: list[dict]):
    """name -> function(row) -> function(value) -> bool."""
    if sel_name in ("fvp5",):
        cutoff = min(MS.fv_ratio(r) for r in sel)
        return lambda r: (lambda v: MS.fv_ratio(r) / v >= cutoff)
    if sel_name == "method":
        return lambda r: (lambda v: MS.fv_ratio(r) / v >= 1 / MS.MOS)
    if sel_name == "key5":
        ranks = D.key_rank(universe)
        keyed = [r for r in universe if id(r) in ranks]
        ops = {id(r): i for i, r in enumerate(sorted(keyed, key=lambda r: -r["ebit"] / r["assets"]))}
        eys = sorted((r["ebit_ev"] for r in keyed), reverse=True)
        cutoff = max(ranks[id(r)] for r in sel)

        def make(r):
            cap = r.get("market_cap") or (r["shares"] * r["price"])
            def ok(v):
                ev = cap * v + (r.get("net_debt") or 0.0)
                if ev <= 0:
                    return False
                ey = r["ebit"] / ev
                ey_rank = sum(1 for x in eys if x > ey)   # others ahead (own old value counts once at most)
                return ops[id(r)] + ey_rank <= cutoff
            return ok
        return make
    return lambda r: (lambda v: True)


def job(args):
    market, d = args
    _, policy = D.MARKETS[market]
    rows = D.load(market)[d]
    out, mismatches, checked = [], [], 0
    for h in HORIZONS:
        u = MS.usable(rows, h)
        if not u:
            continue
        day = D.start_day(u[0])
        end = PL.years_after(day, h)
        paths = {}
        for r in u:
            p = D.path(D.symbol(r), day, end, policy)
            paths[id(r)] = p
            checked += 1
            ret = MS.excess(r, h) + (r["index_returns"].get(str(h)) if str(h) in r["index_returns"]
                                     else r["index_returns"].get(h))
            got = None if p is None else float(p.iloc[-1]) - 1
            if got is None or abs(got - ret) > 1e-9:
                mismatches.append((D.symbol(r), h, ret, got))
        bench = (r0 := u[0])["index_returns"].get(str(h), r0["index_returns"].get(h))
        sels = {"fvp5": D.fifth(u, MS.fv_ratio), "key5": D.key_best_fifth(u), "all": u}
        if market != "nordic":
            sels["method"] = MS.portfolio(u)
        if market == "nordic":
            legacy = [r.get("returns_stop8", {}).get(str(h)) for r in sels["fvp5"]]
            legacy = [x for x in legacy if x is not None]
            out.append({"market": market, "date": d, "h": h, "sel": "fvp5", "variant": "legacy-stop8",
                        "n": len(legacy), "excess": (statistics.mean(legacy) - bench) if legacy else None})
        bpath = D.index_path(day, end) if market != "nordic" else D.portfolio_path([paths[id(r)] for r in u])
        for name, sel in sels.items():
            sel = [r for r in sel if paths[id(r)] is not None]
            if not sel:
                continue
            rq = requalifier(name, sel, u)
            for vname, stop, re in variants():
                sleeves, stopped = [], 0
                for r in sel:
                    s, k = D.with_stop(paths[id(r)], stop, rq(r) if re else None,
                                       D.trade_cost(r, market))
                    sleeves.append(s)
                    stopped += k > 0
                port = D.portfolio_path(sleeves)
                finals = [float(s.iloc[-1]) - 1 for s in sleeves]
                out.append({"market": market, "date": d, "h": h, "sel": name, "variant": vname,
                            "n": len(sel), "excess": statistics.mean(finals) - bench,
                            "stopped": stopped / len(sel), "maxdd": D.max_drawdown(port),
                            "bench_maxdd": None if bpath is None else D.max_drawdown(bpath)})
    return out, mismatches, checked


def run(workers: int) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(m, d) for m in D.MARKETS for d in D.load(m)]
    results, mism, checked = [], [], 0
    with ProcessPoolExecutor(workers) as pool:
        for out, mm, c in pool.map(job, jobs):
            results += out
            mism += mm
            checked += c
    D.write_jsonl(OUT / "results.jsonl", results)
    D.write_jsonl(OUT / "path-mismatches.jsonl", [dict(zip(("sym", "h", "row", "path"), m)) for m in mism])
    print(f"{len(results)} result rows; path check: {len(mism)} of {checked} paths differ from the row's return")
    return 0


def summary() -> int:
    res = [json.loads(l) for l in (OUT / "results.jsonl").read_text().splitlines()]
    groups = {}
    for r in res:
        groups.setdefault((r["market"], r["sel"], r["variant"], r["h"]), []).append(r)
    names = [v[0] for v in variants()] + ["legacy-stop8"]
    for market in D.MARKETS:
        for sel in ("fvp5", "key5", "method", "all"):
            if not any(k[0] == market and k[1] == sel for k in groups):
                continue
            print(f"\n### {market} / {sel}\n")
            print("| Variant | 1 y | 3 y | 5 y | 3 y half 1 / half 2 | 3 y vs no stop, half 1 / half 2 | "
                  "stopped (3 y) | max DD 3 y (mean / worst) | benchmark max DD 3 y |")
            print("|---|---:|---:|---:|---|---|---:|---|---:|")
            for v in names:
                g = {h: groups.get((market, sel, v, h), []) for h in HORIZONS}
                if not any(g.values()):
                    continue
                m = {h: D.mean([x["excess"] for x in g[h]]) for h in HORIZONS}
                three = g[3]
                base = {x["date"]: x["excess"] for x in groups.get((market, sel, "none", 3), [])}
                halves, rel = [], []
                for hf in (0, 1):
                    xs = [x for x in three if D.half_of(market, x["date"]) == hf]
                    halves.append(D.mean([x["excess"] for x in xs]))
                    rel.append(D.mean([x["excess"] - base[x["date"]] for x in xs if x["excess"] is not None
                                       and x["date"] in base]))
                st = D.mean([x.get("stopped") for x in three])
                dd = [x.get("maxdd") for x in three if x.get("maxdd") is not None]
                bdd = D.mean([x.get("bench_maxdd") for x in three])
                print(f"| {v} | {D.pp(m[1])} | {D.pp(m[3])} | {D.pp(m[5])} | {D.pp(halves[0])} / {D.pp(halves[1])} | "
                      f"{D.pp(rel[0])} / {D.pp(rel[1])} | {'–' if st is None else f'{st:.0%}'} | "
                      f"{'–' if not dd else f'{100 * statistics.mean(dd):.0f} / {100 * min(dd):.0f}'} % | "
                      f"{'–' if bdd is None else f'{100 * bdd:.0f}'} % |")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--workers", type=int, default=22)
    a = ap.parse_args(argv)
    return summary() if a.summary else run(a.workers)


if __name__ == "__main__":
    sys.exit(main())
