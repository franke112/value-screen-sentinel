"""TEST A5 (ATTEMPTS #19): our best-minus-worst spreads against the JKP
factors (Jensen, Kelly and Pedersen 2023, jkpfactors.com, CC BY-NC 4.0).

    DEVOUR_LB=clean .venv/bin/python -m tools.backtest.a5_jkp > data/backtest/devour-jkp-r2/MEASURE.md

JKP: monthly long-short (top minus bottom tercile, signed by the factor's
direction, USD), compounded over the 36 months May..April after each test
date; Nordic = the mean of Sweden, Norway, Denmark and Finland. Ours: the
3-year mean excess of the best fifth minus the worst fifth (F-score: F >= 7
minus F <= 3, the integer score has no clean fifths -- the deviation),
cleaned data, Nordic nordic-m7. Raw JKP files stay in data/jkp/ (gitignored).
"""
from __future__ import annotations

import csv
import io
import json
import statistics
import sys
import zipfile
from datetime import timedelta

from . import band_momentum as BM
from . import devour as D
from . import fscore_accruals as FA
from . import measure as MS

JKP = D.ROOT / "data" / "jkp" / "raw"
NORDIC = ("swe", "nor", "dnk", "fin")
H = 3


def jkp(country, weight):
    z = zipfile.ZipFile(JKP / f"{country}_all_factors_monthly_{weight}.zip")
    out = {}
    for row in csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode())):
        out.setdefault(row["name"], {})[row["date"][:7]] = float(row["ret"])
    return out


def compound(series, year, months=36):
    acc = 1.0
    for i in range(months):
        y, m = year + (4 + i) // 12, (4 + i) % 12 + 1
        k = f"{y:04d}-{m:02d}"
        if k not in series:
            return None
        acc *= 1 + series[k]
    return acc - 1


def spread(rows, key, best_high=True):
    rs = sorted((r for r in rows if key(r) is not None), key=key, reverse=best_high)
    k = len(rs)
    if k < 25:
        return None
    b, w = rs[:k // 5], rs[-(k // 5):]
    return statistics.mean(MS.excess(r, H) for r in b) - statistics.mean(MS.excess(r, H) for r in w)


def group_spread(rows, key):
    hi = [MS.excess(r, H) for r in rows if key(r) is not None and key(r) >= 7]
    lo = [MS.excess(r, H) for r in rows if key(r) is not None and key(r) <= 3]
    if len(hi) < 3 or len(lo) < 3:
        return None
    return statistics.mean(hi) - statistics.mean(lo)


def main() -> int:
    sig = D.BT / "devour-fundsig-r2"
    print("# A5: our spreads against the JKP factors (attempt #19), 3 years\n")
    print("Source: Jensen, Kelly and Pedersen (2023), \"Is There a Replication Crisis in Finance?\", "
          "Journal of Finance 78(5); jkpfactors.com, CC BY-NC 4.0.\n")
    print("| Market | Ours | JKP | weight | ours mean | JKP mean | signs agree | corr. | ours half 1 / 2 | "
          "JKP half 1 / 2 | agree? | largest disagreements (date: ours / JKP) |")
    print("|---|---|---|---|---:|---:|---|---:|---|---|---|---|")
    for market, countries in (("nordic", NORDIC), ("us-bust", ("usa",))):
        data = D.load(market)
        FA.attach(market, data)
        fs = {}
        for l in (sig / f"{'nordic' if market == 'nordic' else 'us-bust'}.jsonl").read_text().splitlines():
            x = json.loads(l)
            fs[(x["date"], x["id"])] = x
        for d, rows in data.items():
            for r in rows:
                x = fs.get((d, str(r.get("cik"))), {})
                a, a1 = x.get("assets"), x.get("assets_1")
                r["_ag"] = None if not a or not a1 or a1 <= 0 else a / a1 - 1
                r["_mom"] = BM.momentum(D.symbol(r), D.start_day(r)) if r.get("status") == "ok" else None
        ours = {}
        for d, rows in sorted(data.items()):
            u = MS.usable(rows, H)
            ks = BM.key_score(u)
            ours.setdefault("fv/price", {})[d] = spread(u, MS.fv_ratio)
            ours.setdefault("E43 key", {})[d] = spread(u, ks)
            ours.setdefault("F-score (>=7 minus <=3)", {})[d] = group_spread(u, lambda r: r["_f"])
            ours.setdefault("accruals (low minus high)", {})[d] = spread(u, lambda r: r["_acc"], best_high=False)
            ours.setdefault("12-1 momentum", {})[d] = spread(u, lambda r: r["_mom"])
            ours.setdefault("asset growth (low minus high)", {})[d] = spread(u, lambda r: r["_ag"], best_high=False)
        pairs = (("fv/price", "be_me"), ("fv/price", "ebitda_mev"), ("E43 key", "op_at"),
                 ("E43 key", "ebitda_mev"), ("F-score (>=7 minus <=3)", "f_score"),
                 ("accruals (low minus high)", "oaccruals_at"), ("12-1 momentum", "ret_12_1"),
                 ("asset growth (low minus high)", "at_gr1"))
        for weight in ("vw_cap", "ew"):
            fac = [jkp(c, weight) for c in countries]
            for mine, theirs in pairs:
                xs = []
                for d, v in sorted(ours[mine].items()):
                    js = [compound(f.get(theirs, {}), int(d[:4])) for f in fac]
                    js = [j for j in js if j is not None]
                    if v is None or len(js) < len(fac):
                        continue
                    xs.append((d, v, statistics.mean(js)))
                if len(xs) < 3:
                    print(f"| {market} | {mine} | {theirs} | {weight} | too few dates | | | | | | | |")
                    continue
                o, j = [x[1] for x in xs], [x[2] for x in xs]
                agree = sum((a > 0) == (b > 0) for a, b in zip(o, j))
                corr = statistics.correlation(o, j) if len(xs) > 2 else None
                hl = lambda i, hf: D.pp(D.mean([x[i] for x in xs if D.half_of(market, x[0]) == hf]))
                ok = ((statistics.mean(o) > 0) == (statistics.mean(j) > 0)) and agree >= 2 * len(xs) / 3
                worst = sorted(xs, key=lambda x: -abs(x[1] - x[2]))[:3]
                print(f"| {market} | {mine} | {theirs} | {weight} | {D.pp(statistics.mean(o))} | "
                      f"{D.pp(statistics.mean(j))} | {agree}/{len(xs)} | {corr:+.2f} | {hl(1, 0)} / {hl(1, 1)} | "
                      f"{hl(2, 0)} / {hl(2, 1)} | {'yes' if ok else 'NO'} | "
                      f"{'; '.join(f'{d[:4]}: {D.pp(a, 0)} / {D.pp(b, 0)}' for d, a, b in worst)} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
