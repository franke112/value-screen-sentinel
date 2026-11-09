"""ATTEMPTS #24 (pre-registered 2026-11-08, before any run): the hard kills
4.2.1 / 4.2.2 / 4.2.7 as continuous signals, and the screener's ordering
candidates, by decile, in one run.

    DEVOUR_LB=clean .venv/bin/python -m tools.backtest.a24_deciles > reports/attempts/A24-RESULT.md

Reads the cleaned rows (nordic-m7, US *-clean) and the signals of
data/backtest/devour-fundsig-r2/ (fundsig.py, with rev_declines and
inv_growth added for this attempt). Deciles per date, mean 3-year excess per
decile, averaged over dates (a3_kills.group_means); 1 and 5 years beside.

THE DECISION RULE (owner, fixed 2026-11-08): a signal "sorts" if the rank
correlation over its decile means is >= 0.8 in the direction the rule
claims AND top minus bottom decile > 0, in BOTH markets AND BOTH halves, at
3 years. A kill that sorts STAYS (IN); one that does not is REMOVED (OUT,
E163 for it). Among the ordering candidates, the one that sorts with the
highest top decile becomes the screener's order (IN); if none sorts, E43 is
removed and the order is random (OUT). Ties go to the existing E43 key.
"""
from __future__ import annotations

import random
import statistics
import sys

from . import a3_kills as A3
from . import devour as D
from . import measure as MS
from . import measure_key as MK


def s(r, k):
    return (r.get("_s") or {}).get(k)


def ratio_over_rev(k):
    def f(r):
        g, ry = s(r, k), s(r, "rev_yoy")
        return None if g is None or ry is None or ry <= 0 else g / ry
    return f


#: (name, key, the direction the rule claims: +1 = higher key -> higher return)
KILLS = (
    ("4.2.1 consecutive YoY revenue declines", lambda r: s(r, "rev_declines"), -1),
    ("4.2.1 latest YoY revenue change", lambda r: s(r, "rev_yoy"), +1),
    ("4.2.2 YoY op-margin change, bps", lambda r: s(r, "margin_chg_bps"), +1),
    ("4.2.7 receivables growth / revenue growth", ratio_over_rev("rec_growth"), -1),
    ("4.2.7 inventory growth / revenue growth", ratio_over_rev("inv_growth"), -1),
)


def e43_rank(u, d):
    rs = MK.key_order(u)              # best first
    k = len(rs)
    if k < 50:
        return {}
    return {id(r): 9 - min(9, i * 10 // k) for i, r in enumerate(rs)}   # 9 = best


def quality_score(r):
    q = r.get("quality") or {}
    return sum(1 for v in q.values() if v is True)


ORDERS = (
    ("E43 key (EBIT/assets + EBIT/EV)", e43_rank, +1),
    ("fv / price", A3.deciles(MS.fv_ratio), +1),
    ("Q1-Q4 composite (#21)", A3.deciles(quality_score), +1),
)


def random_null(data, market, h, n=1000, seed=20261108):
    """The mean top-minus-bottom of n random decile assignments."""
    rng = random.Random(seed)
    tbs = []
    for _ in range(n):
        def grp(u, d):
            idx = list(range(len(u)))
            rng.shuffle(idx)
            k = len(u)
            return {id(u[j]): min(9, i * 10 // k) for i, j in enumerate(idx)} if k >= 50 else {}
        _, _, tbm, _, _ = A3.group_means(data, market, h, grp, 10)
        if tbm is not None:
            tbs.append(tbm)
    return statistics.mean(tbs) if tbs else None


def sorts(market_results, direction):
    """market_results: {market: (rc, halves_tb)} at 3 y -> True / False."""
    for rc, hl in market_results.values():
        if rc is None or None in hl:
            return False
        if direction * rc < 0.8 or any(direction * x <= 0 for x in hl):
            return False
    return True


def main() -> int:
    if D.LB != "clean":
        raise SystemExit("run with DEVOUR_LB=clean (the registered data)")
    print("# #24 -- the kills and the ordering candidates by decile\n")
    print("Pre-registered 2026-11-08 (ATTEMPTS #24); decision rule fixed by the owner the same day.\n")
    markets = ("nordic", "us-bust")
    data = {}
    for m in markets:
        data[m] = D.load(m)
        A3.attach(m, data[m])
    results = {}
    print("| Market | Signal | h | decile means (pp, low -> high) | rank corr. | top - bottom | half 1 / half 2 |")
    print("|---|---|---|---|---:|---:|---|")
    for name, key, direction in KILLS + tuple((n, g, dr) for n, g, dr in ORDERS):
        grouper = A3.deciles(key) if name in {k[0] for k in KILLS} else key
        per_market = {}
        for m in markets:
            for h in (1, 3, 5):
                means, rc, tbm, hl, tb = A3.group_means(data[m], m, h, grouper, 10)
                print(f"| {m} | {name} | {h} y | {' / '.join(D.pp(x, 0) for x in means)} | "
                      f"{'–' if rc is None else f'{rc:+.2f}'} | {D.pp(tbm)} | {D.pp(hl[0])} / {D.pp(hl[1])} |")
                if h == 3:
                    per_market[m] = (rc, hl, means[-1] if means else None)
        results[name] = (per_market, direction)
    print("\n## Random null (mean top - bottom of 1,000 random decile orders, 3 y)\n")
    for m in markets:
        print(f"- {m}: {D.pp(random_null(data[m], m, 3))}")
    print("\n## Decisions (3 years, both markets, both halves)\n")
    for name, key, direction in KILLS:
        pm, dr = results[name]
        ok = sorts({m: (v[0], v[1]) for m, v in pm.items()}, dr)
        print(f"- **{name}**: {'SORTS -> stays (IN)' if ok else 'does not sort -> removed (OUT, E163)'}")
    best = None
    for name, _, direction in ORDERS:
        pm, dr = results[name]
        ok = sorts({m: (v[0], v[1]) for m, v in pm.items()}, dr)
        top = statistics.mean(v[2] for v in pm.values() if v[2] is not None) if ok else None
        print(f"- order **{name}**: {'sorts' if ok else 'does not sort'}"
              + (f", mean top decile {D.pp(top)}" if top is not None else ""))
        if ok and (best is None or top > best[1] or (top == best[1] and name.startswith("E43"))):
            best = (name, top)
    print(f"\n**Screener order:** {best[0] + ' (IN)' if best else 'none sorts -> E43 removed, random order (OUT)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
