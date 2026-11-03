"""The measure (backtest design, step 6), on the rows `run` wrote.

    .venv/bin/python -m tools.backtest.measure [--horizon 3] > data/backtest/run/MEASURE.md

Every number is an EXCESS return: the name's total return over the horizon
less ^SP500TR's over the same days. A row counts when it was valued
(`status` ok), has a price on the test day, a return at the horizon, and
passes the float check (`cap_check`: the filer's own public float within
0.15-1.6 of cover shares x price; outside it the ticker most likely belongs
to another security today, the pilot's SPB-for-HRG case).

DECIDED BEFORE THE FIRST RESULT (2026-10-29), as the design asks:

- "Returns rise with fv/price over the quintiles" is read as: the rank
  correlation between quintile order (dearest to cheapest) and the
  quintile's mean excess return is at least 0.8 -- at most one swap of
  neighbours. The design's bar is 4 of 5 test dates.
- The comparators' portfolios have the SAME number of names as the
  method's portfolio on each date (the top N by EBIT/EV, by FCF yield, by
  Greenblatt's rank sum), so size does not decide the comparison.
- The bootstrap resamples names within each date (10,000 draws) and pools
  the dates by equal weight.
- Points 6 and 7 are reported on 2016-2018 (where a change may be tuned)
  and 2019-2020 (where it must hold) separately.

Survivors only: a name with no ticker or no price is counted, never valued.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from collections import defaultdict

from . import pilot as PL
from . import run as R
from . import universe as U

MOS = 0.65            # tier 3's cushion, the strictest
TUNE = ("2016", "2017", "2018")
HOLD = ("2019", "2020")
DRAWS = 10_000


def load() -> dict[str, list[dict]]:
    out = {}
    for d in U.TEST_DATES:
        p = R.OUT / f"{d.isoformat()}.jsonl"
        if p.exists():
            out[d.isoformat()] = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    return out


def excess(row: dict, h: int):
    a, b = row.get("returns", {}).get(str(h)), row.get("index_returns", {}).get(str(h))
    if a is None:
        a, b = row.get("returns", {}).get(h), row.get("index_returns", {}).get(h)
    return None if a is None or b is None else a - b


def usable(rows, h):
    return [r for r in rows if r.get("status") == "ok" and r.get("price")
            and r.get("cap_check", True) and excess(r, h) is not None]


def fv_ratio(r, cap=None):
    if cap is None:
        return r.get("fv_over_price")
    c = r.get("caps", {}).get(cap)
    return c.get("fv_over_price") if c else r.get("fv_over_price")


def fv_base(r, cap=None):
    c = r.get("caps", {}).get(cap) if cap else None
    return c.get("fv_base") if c else r.get("fv_base")


def mean(xs):
    return statistics.mean(xs) if xs else None


def rank_corr(xs):
    """Spearman of position against value, for a short list without ties."""
    n = len(xs)
    order = sorted(range(n), key=lambda i: xs[i])
    rank = [0] * n
    for k, i in enumerate(order):
        rank[i] = k
    d = sum((i - rank[i]) ** 2 for i in range(n))
    return 1 - 6 * d / (n * (n * n - 1))


def quintiles(rows, h, key):
    rs = sorted((r for r in rows if key(r) is not None), key=key)
    if len(rs) < 25:
        return None
    k = len(rs)
    return [[excess(r, h) for r in rs[i * k // 5:(i + 1) * k // 5]] for i in range(5)]


def portfolio(rows, cap=None):
    return [r for r in rows if fv_base(r, cap) is not None and r["price"] <= MOS * fv_base(r, cap)
            and r.get("passes_quality") is True and not r.get("measured_kill")]


def top(rows, n, key):
    rs = [r for r in rows if key(r) is not None]
    return sorted(rs, key=key, reverse=True)[:n]


def greenblatt(rows):
    rs = [r for r in rows if r.get("ebit_ev") is not None and r.get("roc") is not None]
    a = {id(r): i for i, r in enumerate(sorted(rs, key=lambda r: -r["ebit_ev"]))}
    b = {id(r): i for i, r in enumerate(sorted(rs, key=lambda r: -r["roc"]))}
    return sorted(rs, key=lambda r: a[id(r)] + b[id(r)])


def bootstrap(groups, h, seed=20261029):
    """95% interval on the equal-weight mean over dates of each date's mean."""
    rng = random.Random(seed)
    groups = [[excess(r, h) for r in g] for g in groups if g]
    if not groups:
        return None
    stats = []
    for _ in range(DRAWS):
        stats.append(statistics.mean(statistics.mean(rng.choices(g, k=len(g))) for g in groups))
    stats.sort()
    return stats[int(0.025 * DRAWS)], stats[int(0.975 * DRAWS)]


def pct(x):
    return "–" if x is None else f"{x * 100:+.1f}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--horizon", type=int, default=3)
    h = ap.parse_args(argv).horizon
    data = load()
    L = [f"# Mätning, horisont {h} år (överavkastning mot ^SP500TR, procentenheter)", ""]

    L += ["## Urvalet", "", "| Testdag | Kandidater | Under floatgräns | Inga fakta | Fel | "
          "Värderade | Med kurs | Floatkontroll fel | Användbara |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for d, rows in data.items():
        skip = defaultdict(int)
        for r in rows:
            if "skip" in r:
                skip["error" if r["skip"].startswith("error") else r["skip"]] += 1
        ok = [r for r in rows if r.get("status") == "ok"]
        priced = [r for r in ok if r.get("price")]
        L.append(f"| {d} | {len(rows)} | {skip['below float line']} | {skip['no facts']} | "
                 f"{skip['error']} | {len(ok)} | {len(priced)} | "
                 f"{sum(1 for r in priced if r.get('cap_check') is False)} | {len(usable(rows, h))} |")

    L += ["", "## 1. Kvintiler på fv/kurs (1 = dyrast, 5 = billigast), medel", "",
          "| Testdag | 1 | 2 | 3 | 4 | 5 | Rangkorr. | Klarar (≥ 0,8) |", "|---|---:|---:|---:|---:|---:|---:|---|"]
    passes = 0
    for d, rows in data.items():
        q = quintiles(usable(rows, h), h, fv_ratio)
        if q is None:
            L.append(f"| {d} | för få | | | | | | |")
            continue
        means = [mean(x) for x in q]
        rc = rank_corr(means)
        passes += rc >= 0.8
        L.append(f"| {d} | " + " | ".join(pct(m) for m in means) + f" | {rc:.2f} | {'ja' if rc >= 0.8 else 'nej'} |")
    L += ["", f"**{passes} av {len(data)} testdagar klarar kriteriet (designen kräver 4 av 5).**"]

    L += ["", "## 2. E145 inom kvintil (medel: klarar Q1–Q4 / klarar inte, antal)", "",
          "| Testdag | " + " | ".join(f"Q{i}" for i in range(1, 6)) + " |", "|---|" + "---|" * 5]
    for d, rows in data.items():
        rs = sorted((r for r in usable(rows, h) if fv_ratio(r) is not None), key=fv_ratio)
        k = len(rs)
        cells = []
        for i in range(5):
            part = rs[i * k // 5:(i + 1) * k // 5]
            a = [excess(r, h) for r in part if r.get("passes_quality") is True]
            b = [excess(r, h) for r in part if r.get("passes_quality") is False]
            cells.append(f"{pct(mean(a))} ({len(a)}) / {pct(mean(b))} ({len(b)})")
        L.append(f"| {d} | " + " | ".join(cells) + " |")

    L += ["", f"## 3–5. Portföljen (kurs ≤ {MOS} × fv_base, Q1–Q4, inget mätbart stopp) mot jämförelser", "",
          "| Testdag | N | Portfölj | Andel > index | Sämsta | EBIT/EV topp N | FCF-avk. topp N | "
          "Greenblatt topp N | Hela urvalet |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    groups, comp = [], defaultdict(list)
    for d, rows in data.items():
        u = usable(rows, h)
        p = portfolio(u)
        n = len(p)
        groups.append(p)
        ex = [excess(r, h) for r in p]
        e1 = [excess(r, h) for r in top(u, n, lambda r: r.get("ebit_ev"))]
        e2 = [excess(r, h) for r in top(u, n, lambda r: r.get("fcf_yield"))]
        e3 = [excess(r, h) for r in greenblatt(u)[:n]]
        comp["ebit_ev"].append(e1)
        L.append(f"| {d} | {n} | {pct(mean(ex))} | "
                 f"{'–' if not ex else f'{sum(x > 0 for x in ex) / n:.0%}'} | {pct(min(ex) if ex else None)} | "
                 f"{pct(mean(e1))} | {pct(mean(e2))} | {pct(mean(e3))} | {pct(mean([excess(r, h) for r in u]))} |")
    ci = bootstrap(groups, h)
    L += ["", f"Bootstrap 95 % på portföljens överavkastning (dagarna lika vikt): "
          f"{'–' if ci is None else f'{pct(ci[0])} till {pct(ci[1])}'}"]
    diff = [[excess(r, h) for r in g] for g in groups]
    pm = [mean(x) for x in diff if x]
    em = [mean(x) for x in comp["ebit_ev"] if x]
    L += [f"Portföljen i snitt {pct(mean(pm))}, EBIT/EV-jämförelsen {pct(mean(em))}."]

    L += ["", "## 6. Tillväxttaket 4 / 6 / 8 % (rangkorrelation över kvintiler; portföljens medel och N)", "",
          "| Period | Urval | Tak | Kvintil 1–5 | Rangkorr. | Portfölj (N) |", "|---|---|---|---|---:|---|"]
    for label, years in (("2016–18 (justering)", TUNE), ("2019–20 (prov)", HOLD)):
        for sub, filt in (("alla", lambda r: True), ("Q1–Q4", lambda r: r.get("passes_quality") is True)):
            for cap in (None, "0.06", "0.08"):
                rows = [r for d, rs in data.items() if d[:4] in years for r in usable(rs, h) if filt(r)]
                q = quintiles(rows, h, lambda r: fv_ratio(r, cap))
                p = portfolio(rows, cap) if sub == "alla" else [r for r in portfolio(rows, cap)]
                means = [mean(x) for x in q] if q else None
                L.append(f"| {label} | {sub} | {'4 %' if cap is None else f'{float(cap) * 100:.0f} %'} | "
                         f"{'–' if not means else ' / '.join(pct(m) for m in means)} | "
                         f"{'–' if not means else f'{rank_corr(means):.2f}'} | "
                         f"{pct(mean([excess(r, h) for r in p]))} ({len(p)}) |")
    capped = sum(1 for rs in data.values() for r in rs if r.get("caps"))
    L += ["", f"Rader där taket slog till och 6/8 % räknades: {capped}."]

    L += ["", "## 7. Mätbara hårda stopp (4.2.1, 4.2.2, 4.2.5, 4.2.7) bland Q1–Q4 och fv/kurs > 1", "",
          "| Period | Med stopp: medel (N) | Utan stopp: medel (N) |", "|---|---|---|"]
    for label, years in (("2016–18", TUNE), ("2019–20", HOLD)):
        rows = [r for d, rs in data.items() if d[:4] in years for r in usable(rs, h)
                if r.get("passes_quality") is True and (fv_ratio(r) or 0) > 1]
        a = [excess(r, h) for r in rows if r.get("measured_kill")]
        b = [excess(r, h) for r in rows if not r.get("measured_kill")]
        L.append(f"| {label} | {pct(mean(a))} ({len(a)}) | {pct(mean(b))} ({len(b)}) |")
    L += ["", "§4.2.3 (sänkt prognos) och §4.2.6 är inte mätta: de står inte i XBRL."]
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
