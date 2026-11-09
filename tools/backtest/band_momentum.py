"""TEST 3 (wrez-devour, pre-registered in reference/backtest/ATTEMPTS.md #12):
Gate 1's 15-50% band in the NORDICS, and a 12-1 momentum filter in both.

    .venv/bin/python -m tools.backtest.band_momentum > data/backtest/devour-band/MEASURE.md

(a) The band (`measure_key.drawdown`, the fall from the 52-week adjusted
    closing high) in the Nordics, on the E43 key and on fv/price: fifths
    over all valued names and inside the band only, and the band against
    the names outside it. The US band was measured in #8 and is not redone.
(b) Instead of the band: drop the bottom DECILE of 12-1 month momentum (the
    adjusted close a month before the test day over the close a year
    before; names with under a year of prices are kept and counted), then
    the same fifths -- in the Nordics and the US (bust; last beside).
"""
from __future__ import annotations

import statistics
import sys
from datetime import date, timedelta

from . import devour as D
from . import eodhd_reprice as EP
from . import measure as MS
from . import measure_key as MK

H = (3, 5)


def momentum(sym, day: date):
    if not sym:
        return None
    f = EP.frame(sym)
    if f is None:
        return None
    a = EP.on(f, day - timedelta(days=365), "adjusted_close")
    b = EP.on(f, day - timedelta(days=30), "adjusted_close")
    if a is None or b is None or a[1] <= 0:
        return None
    if EP.level_breaks(f, day - timedelta(days=365), day):
        return None
    return b[1] / a[1] - 1


def key_score(rows):
    """higher = better: minus the E43 rank sum."""
    ranks = D.key_rank(rows)
    return lambda r: None if id(r) not in ranks else -ranks[id(r)]


def fifths_means(rows, h, score):
    rs = sorted((r for r in rows if score(r) is not None), key=score)
    if len(rs) < 25:
        return None
    k = len(rs)
    return [statistics.mean(MS.excess(r, h) for r in rs[i * k // 5:(i + 1) * k // 5]) for i in range(5)]


def table(market, data, label, keep, h):
    per = []
    for d, rows in sorted(data.items()):
        u = [r for r in MS.usable(rows, h) if keep(r)]
        for name, score in (("E43 key", key_score(u)), ("fv/price", MS.fv_ratio)):
            q = fifths_means(u, h, score)
            if q:
                per.append({"date": d, "key": name, "q": q})
    out = []
    for name in ("E43 key", "fv/price"):
        xs = [p for p in per if p["key"] == name]
        if not xs:
            out.append(f"| {market} | {label} | {name} | {h} y | too few | | | |")
            continue
        means = [statistics.mean(p["q"][i] for p in xs) for i in range(5)]
        halves = [D.mean([p["q"][4] for p in xs if D.half_of(market, p["date"]) == hf]) for hf in (0, 1)]
        wins = sum(p["q"][4] > p["q"][0] for p in xs)
        out.append(f"| {market} | {label} | {name} | {h} y | {' / '.join(D.pp(m) for m in means)} | "
                   f"{D.pp(means[4] - means[0])} | {wins}/{len(xs)} | {D.pp(halves[0])} / {D.pp(halves[1])} |")
    return out, per


def main() -> int:
    print("# Test 3: the band in the Nordics, and the 12-1 momentum filter (attempt #12)\n")
    print("Fifths worst -> best, mean excess over the index (pp); best half 1 / half 2 = the best "
          "fifth's mean excess in each half.\n")
    print("| Market | Set | Key | Horizon | fifths worst -> best | best - worst | best > worst | "
          "best fifth, half 1 / half 2 |")
    print("|---|---|---|---|---|---|---|---|")
    extra = []
    for market in ("nordic", "us-bust", "us-last"):
        data = D.load(market)
        for rows in data.values():
            for r in rows:
                day = D.start_day(r)
                r["_mom"] = momentum(D.symbol(r), day)
                if market == "nordic":
                    r["_dd"] = MK.drawdown(D.symbol(r), day)
        for h in H:
            # the decile cut, per date, among usable names with a momentum
            cut = {}
            for d, rows in data.items():
                ms = sorted(r["_mom"] for r in MS.usable(rows, h) if r["_mom"] is not None)
                cut[d] = ms[len(ms) // 10] if len(ms) >= 10 else None
            not_bottom = lambda r: r["_mom"] is None or cut[r["as_of"]] is None or r["_mom"] >= cut[r["as_of"]]
            sets = [("all valued", lambda r: True), ("bottom momentum decile out", not_bottom)]
            if market == "nordic":
                sets.append(("inside 15-50% band",
                             lambda r: r["_dd"] is not None and MK.BAND[0] <= r["_dd"] <= MK.BAND[1]))
            for label, keep in sets:
                lines, _ = table(market, data, label, keep, h)
                print("\n".join(lines))
            # the excluded decile itself, and (Nordic) the band itself
            dec, rest, band_in, band_out, nomom = [], [], [], [], 0
            for d, rows in sorted(data.items()):
                u = MS.usable(rows, h)
                nomom += sum(r["_mom"] is None for r in u)
                a = [MS.excess(r, h) for r in u if r["_mom"] is not None and cut[d] is not None and r["_mom"] < cut[d]]
                b = [MS.excess(r, h) for r in u if r["_mom"] is not None and cut[d] is not None and r["_mom"] >= cut[d]]
                if a and b:
                    dec.append((d, statistics.mean(a))); rest.append((d, statistics.mean(b)))
                if market == "nordic":
                    ins = [MS.excess(r, h) for r in u if r["_dd"] is not None and MK.BAND[0] <= r["_dd"] <= MK.BAND[1]]
                    outs = [MS.excess(r, h) for r in u if r["_dd"] is not None and not (MK.BAND[0] <= r["_dd"] <= MK.BAND[1])]
                    if ins and outs:
                        band_in.append((d, statistics.mean(ins))); band_out.append((d, statistics.mean(outs)))
            hl = lambda xs, hf: D.mean([x for d, x in xs if D.half_of(market, d) == hf])
            extra.append(f"| {market} | {h} y | bottom momentum decile vs the rest | "
                         f"{D.pp(D.mean([x for _, x in dec]))} vs {D.pp(D.mean([x for _, x in rest]))} | "
                         f"{D.pp(hl(dec, 0))} vs {D.pp(hl(rest, 0))} | {D.pp(hl(dec, 1))} vs {D.pp(hl(rest, 1))} | "
                         f"{len(dec)} dates, {nomom} name-dates without momentum (kept) |")
            if band_in:
                extra.append(f"| {market} | {h} y | inside 15-50% band vs outside | "
                             f"{D.pp(D.mean([x for _, x in band_in]))} vs {D.pp(D.mean([x for _, x in band_out]))} | "
                             f"{D.pp(hl(band_in, 0))} vs {D.pp(hl(band_out, 0))} | "
                             f"{D.pp(hl(band_in, 1))} vs {D.pp(hl(band_out, 1))} | {len(band_in)} dates |")
    print("\n| Market | Horizon | Comparison | all dates | half 1 | half 2 | note |")
    print("|---|---|---|---|---|---|---|")
    print("\n".join(extra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
