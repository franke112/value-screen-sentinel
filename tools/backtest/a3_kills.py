"""TEST A3 (ATTEMPTS #17): the hard-kill thresholds.

    DEVOUR_LB=clean .venv/bin/python -m tools.backtest.a3_kills > data/backtest/devour-kills-r2/MEASURE.md

Reads data/backtest/devour-fundsig-r2/ (fundsig.py) and the cleaned rows
(nordic-m7, US *-clean). Per date, the valued usable names; a group's mean
counts on a date only with >= 3 names; means are averaged over dates.
"""
from __future__ import annotations

import json
import statistics
import sys

from . import devour as D
from . import measure as MS

SIG = D.BT / "devour-fundsig-r2"


def attach(market, data):
    src = "us-bust" if market.startswith("us") else "nordic"
    sig = {}
    for l in (SIG / f"{src}.jsonl").read_text().splitlines():
        x = json.loads(l)
        sig[(x["date"], x["id"])] = x
    for d, rows in data.items():
        for r in rows:
            r["_s"] = sig.get((d, str(r.get("cik"))), {})


def group_means(data, market, h, groupof, n_groups):
    per = {g: [] for g in range(n_groups)}
    tb = []
    for d, rows in sorted(data.items()):
        u = MS.usable(rows, h)
        g = {i: [] for i in range(n_groups)}
        gid = groupof(u, d)
        for r in u:
            i = gid.get(id(r))
            if i is not None:
                g[i].append(MS.excess(r, h))
        for i, xs in g.items():
            if len(xs) >= 3:
                per[i].append((d, statistics.mean(xs)))
        if len(g[0]) >= 3 and len(g[n_groups - 1]) >= 3:
            tb.append((d, statistics.mean(g[n_groups - 1]) - statistics.mean(g[0])))
    means = [D.mean([x for _, x in per[i]]) for i in range(n_groups)]
    rc = MS.rank_corr(means) if None not in means else None
    hl = [D.mean([x for d, x in tb if D.half_of(market, d) == hf]) for hf in (0, 1)]
    return means, rc, D.mean([x for _, x in tb]), hl, tb


def deciles(key):
    def f(u, d):
        rs = sorted((r for r in u if key(r) is not None), key=key)
        k = len(rs)
        if k < 50:
            return {}
        return {id(r): min(9, i * 10 // k) for i, r in enumerate(rs)}
    return f


def bins(key, edges):
    """group i = edges[i] <= key < edges[i+1]"""
    def f(u, d):
        out = {}
        for r in u:
            v = key(r)
            if v is None:
                continue
            for i in range(len(edges) - 1):
                if edges[i] <= v < edges[i + 1]:
                    out[id(r)] = i
        return out
    return f


def margin(r):
    return r["_s"].get("margin_chg_bps")


def ratio(r):
    s = r["_s"]
    g, ry = s.get("rec_growth"), s.get("rev_yoy")
    return None if g is None or ry is None or ry <= 0 else g / ry


def flat_or_falling(r):
    ry = r["_s"].get("rev_yoy")
    return ry is not None and ry <= 0


def kill_state(rule):
    def f(r):
        if rule == "4.2.4":
            m = r["_s"].get("eps_misses")
            return None if m is None else ("TRIP" if m >= 3 else "NO_TRIP")
        if rule == "any":
            ks = r["_s"].get("kills") or {}
            states = [ks.get(k) for k in ("4.2.1", "4.2.2", "4.2.7")] + [kill_state("4.2.4")(r)]
            if "TRIP" in states:
                return "TRIP"
            return "NO_TRIP" if all(s == "NO_TRIP" for s in states) else None
        s = (r["_s"].get("kills") or {}).get(rule)
        return s if s in ("TRIP", "NO_TRIP") else None
    return f


def main() -> int:
    print("# A3: the hard-kill thresholds (attempt #17), cleaned data, Nordic nordic-m7\n")
    lines_d, lines_s, lines_k = [], [], []
    for market in ("nordic", "us-bust", "us-last"):
        data = D.load(market)
        attach(market, data)
        for h in (1, 3, 5):
            for label, key in (("op margin change YoY, bps (low -> high)", margin),
                               ("receivables growth / revenue growth (low -> high)", ratio)):
                means, rc, tbm, hl, tb = group_means(data, market, h, deciles(key), 10)
                lines_d.append(f"| {market} | {label} | {h} y | {' / '.join(D.pp(m, 0) for m in means)} | "
                               f"{'–' if rc is None else f'{rc:+.2f}'} | {D.pp(tbm)} | {D.pp(hl[0])} / {D.pp(hl[1])} | "
                               f"{sum(x > 0 for _, x in tb)}/{len(tb)} |")
            means, rc, tbm, hl, tb = group_means(
                data, market, h, bins(lambda r: r["_s"].get("eps_misses"), (0, 1, 2, 3, 9)), 4)
            lines_d.append(f"| {market} | EPS misses in the last 8: 0 / 1 / 2 / 3+ | {h} y | "
                           f"{' / '.join(D.pp(m, 0) for m in means)} | {'–' if rc is None else f'{rc:+.2f}'} | "
                           f"{D.pp(tbm)} | {D.pp(hl[0])} / {D.pp(hl[1])} | {sum(x > 0 for _, x in tb)}/{len(tb)} |")
            # steps at the thresholds: group 0 = beyond the threshold, 1 = just inside
            for label, key, edges in (
                    ("margin: [-300,-150) vs [-150,0)", margin, (-300, -150, 0)),
                    ("margin, revenue flat/falling: [-300,-150) vs [-150,0)",
                     lambda r: margin(r) if flat_or_falling(r) else None, (-300, -150, 0)),
                    ("receivables/revenue: (1.5,2.25] vs (1.0,1.5]", lambda r: (None if ratio(r) is None else -ratio(r)),
                     (-2.25, -1.5, -1.0))):
                means, _, tbm, hl, tb = group_means(data, market, h, bins(key, edges), 2)
                lines_s.append(f"| {market} | {label} | {h} y | {D.pp(means[0])} | {D.pp(means[1])} | "
                               f"{D.pp(tbm)} | {D.pp(hl[0])} / {D.pp(hl[1])} | {len(tb)} |")
            for rule in ("4.2.1", "4.2.2", "4.2.4", "4.2.7", "any"):
                st = kill_state(rule)
                means, _, tbm, hl, tb = group_means(
                    data, market, h, lambda u, d, st=st: {id(r): (0 if st(r) == "TRIP" else 1)
                                                         for r in u if st(r) is not None}, 2)
                n_trip = sum(1 for rows in data.values() for r in MS.usable(rows, h) if st(r) == "TRIP")
                n_no = sum(1 for rows in data.values() for r in MS.usable(rows, h) if st(r) == "NO_TRIP")
                lines_k.append(f"| {market} | {rule} | {h} y | {D.pp(means[0])} ({n_trip}) | {D.pp(means[1])} ({n_no}) | "
                               f"{D.pp(tbm)} | {D.pp(hl[0])} / {D.pp(hl[1])} | {len(tb)} |")
    print("## Deciles / groups, mean excess (pp), low -> high\n")
    print("| Market | Signal | h | groups | rank corr. | high - low | half 1 / half 2 | high > low |")
    print("|---|---|---|---|---|---|---|---|")
    print("\n".join(lines_d))
    print("\n## Steps at the thresholds\n")
    print("| Market | Comparison | h | beyond the threshold | just inside | inside - beyond | half 1 / half 2 | dates |")
    print("|---|---|---|---:|---:|---:|---|---:|")
    print("\n".join(lines_s))
    print("\n## The kill rules: names that TRIP against names that do not (CANNOT EVALUATE out)\n")
    print("| Market | Kill | h | TRIP (name-dates) | NO TRIP (name-dates) | no trip - trip | half 1 / half 2 | dates |")
    print("|---|---|---|---:|---:|---:|---|---:|")
    print("\n".join(lines_k))
    return 0


if __name__ == "__main__":
    sys.exit(main())
