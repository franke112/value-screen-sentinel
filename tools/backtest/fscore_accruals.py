"""TEST 4 (wrez-devour, pre-registered in reference/backtest/ATTEMPTS.md #13):
Piotroski's F-score and Sloan's accruals from point-in-time fundamentals.

    .venv/bin/python -m tools.backtest.fscore_accruals --signals   # data/backtest/devour-fscore/signals-*.jsonl
    .venv/bin/python -m tools.backtest.fscore_accruals             # the tables

THE SIGNALS, per valued row, from the facts visible on the test day
(`sec_pit.clip`; Nordic: EODHD statements entered on the day they became
known, `nordic.facts_from_eodhd`, with current assets and current
liabilities added to the translation IN THIS PROCESS ONLY -- the engine's
own mapping lacks them, so its stored Nordic F-score is always empty):
- F-score: `method.fscore`'s nine signals on the newest fiscal year y with
  net income, operating cash flow and assets, against y-1, read straight
  from the clipped facts (`fscore_cut`); None where a signal is missing. On
  US rows the engine's stored F-score is used, and `fscore_cut` is checked
  against it.
- Accruals (cash-flow form, as Sloan's balance-sheet form needs lines EODHD
  lacks): (net income - operating cash flow) / mean total assets of y, y-1.
"""
from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date

from vss import history as HI

from . import devour as D
from . import measure as MS
from . import method as M
from . import pilot as PL
from . import pit as P

OUT = D.BT / ("devour-fscore" + D.SUFFIX)
OCF = "NetCashProvidedByUsedInOperatingActivities"
GROUPS = ((0, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 9))


def dei_shares(cut) -> dict[int, float]:
    rows = (cut.get("facts", {}).get("dei", {}).get("EntityCommonStockSharesOutstanding", {})
            .get("units", {}).get("shares", []))
    out = {}
    for e in sorted(rows, key=lambda e: (e["end"], e["filed"])):
        if e.get("form") in ("10-K", "10-K/A"):
            out[int(e["end"][:4])] = float(e["val"])
    return out


def first_annual(cut, tags):
    for t in tags:
        a = M.annual(cut, t)
        if a:
            return a
    return {}


def fy_ends(cut, tag) -> dict[int, str]:
    """Fiscal-year label -> its end date, from the tag's annual entries."""
    out = {}
    for e in M._gaap(cut).get(tag, {}).get("units", {}).get("USD", []):
        if e.get("form") in ("10-K", "10-K/A") and "start" in e:
            out[int(e["end"][:4])] = e["end"]
    return out


def at_ends(cut, tag, ends: dict[int, str]) -> dict[int, float]:
    """The balance-sheet value AT each fiscal-year end, from a 10-K or a
    10-Q of that end (`method.instants`): EODHD's yearly balance sheet often
    has no known date while the Q4 one for the same day does."""
    inst = M.instants(cut, tag)
    return {y: inst[e] for y, e in ends.items() if e in inst}


def signals_cut(cut):
    """(F-score, accruals, year, assets at the EBIT year's end)."""
    ni = M.annual(cut, "NetIncomeLoss")
    ocf = M.annual(cut, OCF)
    ends = fy_ends(cut, "NetIncomeLoss")
    op_ends = fy_ends(cut, "OperatingIncomeLoss")
    assets_fy = None
    if op_ends:
        ye = max(op_ends)
        assets_fy = at_ends(cut, "Assets", {ye: op_ends[ye]}).get(ye)
    years = [y for y in ni if y in ocf]
    if not years:
        return None, None, None, assets_fy
    y = max(years)
    a = at_ends(cut, "Assets", ends)
    if y not in a:
        return None, None, y, assets_fy
    acc = None
    if (y - 1) in a and a[y] + a[y - 1] > 0:
        acc = (ni[y] - ocf[y]) / ((a[y] + a[y - 1]) / 2)
    rev = first_annual(cut, HI.XBRL_TAGS["revenue"])
    sh = dei_shares(cut)
    gp = {}
    for z in (y, y - 1):
        g, _ = M.first_of(cut, ("GrossProfit",), z)
        if g is None:
            cogs, _ = M.first_of(cut, ("CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"), z)
            g = None if cogs is None or z not in rev else rev[z] - cogs
        gp[z] = g
    inst = {t: at_ends(cut, t, ends) for t in ("AssetsCurrent", "LiabilitiesCurrent",
                                               "LongTermDebtNoncurrent", "LongTermDebt")}
    ltd = inst["LongTermDebtNoncurrent"] or inst["LongTermDebt"]
    ca, cl = inst["AssetsCurrent"], inst["LiabilitiesCurrent"]
    need = [a.get(y), a.get(y - 1), a.get(y - 2), ni.get(y), ni.get(y - 1), ocf.get(y),
            rev.get(y), rev.get(y - 1), sh.get(y), sh.get(y - 1), gp[y], gp[y - 1],
            ca.get(y), ca.get(y - 1), cl.get(y), cl.get(y - 1)]
    if any(v is None for v in need) or not cl[y] or not cl[y - 1] or not rev[y] or not rev[y - 1] \
            or not a[y - 1] or not a[y - 2]:
        return None, acc, y, assets_fy
    roa, roa0 = ni[y] / a[y - 1], ni[y - 1] / a[y - 2]
    lev = ltd.get(y, 0.0) / ((a[y] + a[y - 1]) / 2)
    lev0 = ltd.get(y - 1, 0.0) / ((a[y - 1] + a[y - 2]) / 2)
    f = sum((roa > 0, ocf[y] > 0, roa > roa0, ocf[y] / a[y - 1] > roa,
             gp[y] / rev[y] > gp[y - 1] / rev[y - 1],
             rev[y] / a[y - 1] > rev[y - 1] / a[y - 2],
             lev < lev0 or (lev == 0 and lev0 == 0),
             ca[y] / cl[y] > ca[y - 1] / cl[y - 1],
             sh[y] <= sh[y - 1]))
    return f, acc, y, assets_fy


def _nordic_facts(sym):
    from . import nordic as N
    if "totalCurrentAssets" not in N.BALANCE:
        N.BALANCE.update({"totalCurrentAssets": "AssetsCurrent",
                          "totalCurrentLiabilities": "LiabilitiesCurrent"})
    d = json.loads(gzip.decompress((N.FUND / f"{sym}.json.gz").read_bytes()))
    facts = N.facts_from_eodhd(sym, d)
    # GUARD (2026-11-08): where the vendor's yearly and quarterly balance
    # sheets for the SAME day disagree on total assets by over 10% (33 of
    # 3,928 Nordic year-ends: DEMANT 2009 a quarter of the yearly, ERIC 2009
    # eight times it), the quarterly balance of that day is not used: the
    # figures it would feed are left empty, never guessed.
    bs = (d.get("Financials") or {}).get("Balance_Sheet") or {}
    yearly, quarterly = bs.get("yearly") or {}, bs.get("quarterly") or {}
    bad = set()
    for end, e in yearly.items():
        a, b = N._num((e or {}).get("totalAssets")), N._num((quarterly.get(end) or {}).get("totalAssets"))
        if a and b and abs(b / a - 1) > 0.10:
            bad.add(end)
    if bad:
        for node in facts["facts"]["us-gaap"].values():
            for unit, entries in node["units"].items():
                node["units"][unit] = [e for e in entries
                                       if not (e.get("form") == "10-Q" and "start" not in e and e["end"] in bad)]
    return facts


def job(args):
    market, d = args
    rows = D.load(market, fill=False)[d]
    out = []
    for r in rows:
        if r.get("status") != "ok":
            continue
        day = D.start_day(r)
        try:
            if market == "nordic":
                sym = r["symbol"]
                facts = _nordic_facts(sym)
            else:
                facts = PL.company_facts(int(r["cik"]))
            if facts is None:
                out.append({"id": r["cik"], "fscore": None, "accruals": None, "why": "no facts"})
                continue
            f, acc, y, assets_fy = signals_cut(P.clip(facts, day))
            out.append({"id": r["cik"], "fscore_cut": f, "accruals": acc, "year": y, "assets_fy": assets_fy,
                        "fscore": f if market == "nordic" else r.get("fscore")})
        except Exception as exc:  # noqa: BLE001 -- one name never stops the run
            out.append({"id": r["cik"], "fscore": None, "accruals": None, "why": f"{type(exc).__name__}: {exc}"[:200]})
    return market, d, out


def make_signals(workers):
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(m, d) for m in ("nordic", "us-bust") for d in D.load(m, fill=False)]
    got = {}
    with ProcessPoolExecutor(workers) as pool:
        for market, d, out in pool.map(job, jobs):
            got.setdefault(market, {})[d] = out
    for market, by in got.items():
        D.write_jsonl(OUT / f"signals-{market}.jsonl", [{"date": d, **x} for d, xs in sorted(by.items()) for x in xs])
    us = [x for xs in got["us-bust"].values() for x in xs if x.get("fscore") is not None and x.get("fscore_cut") is not None]
    agree = sum(x["fscore"] == x["fscore_cut"] for x in us)
    print(f"US check: fscore_cut equals the engine's stored F-score on {agree} of {len(us)} rows")
    for market, by in got.items():
        xs = [x for v in by.values() for x in v]
        print(f"{market}: {len(xs)} valued rows, F-score on {sum(x.get('fscore') is not None for x in xs)}, "
              f"accruals on {sum(x.get('accruals') is not None for x in xs)}, "
              f"assets at the EBIT year's end on {sum(x.get('assets_fy') is not None for x in xs)}")


def attach(market, data):
    src = "us-bust" if market.startswith("us") else "nordic"
    sig = {}
    for l in (D.SIGNALS / f"signals-{src}.jsonl").read_text().splitlines():
        x = json.loads(l)
        sig[(x["date"], str(x["id"]))] = x
    for d, rows in data.items():
        for r in rows:
            x = sig.get((d, str(r.get("cik"))), {})
            r["_f"], r["_acc"] = x.get("fscore"), x.get("accruals")


def groups_line(market, data, h, label, keyfun, cuts):
    """Mean excess per group (date-averaged over dates where the group has
    >= 3 names), rank correlation over the group means, top - bottom by half."""
    per = {i: [] for i in range(len(cuts))}
    tb = []
    for d, rows in sorted(data.items()):
        u = [r for r in MS.usable(rows, h) if keyfun(r, d) is not None]
        g = {i: [MS.excess(r, h) for r in u if keyfun(r, d) == i] for i in range(len(cuts))}
        for i, xs in g.items():
            if len(xs) >= 3:
                per[i].append(statistics.mean(xs))
        if len(g[0]) >= 3 and len(g[len(cuts) - 1]) >= 3:
            tb.append((d, statistics.mean(g[len(cuts) - 1]) - statistics.mean(g[0])))
    means = [D.mean(per[i]) for i in range(len(cuts))]
    rc = MS.rank_corr(means) if None not in means else None
    hl = [D.mean([x for d, x in tb if D.half_of(market, d) == hf]) for hf in (0, 1)]
    return (f"| {market} | {label} | {h} y | {' / '.join(D.pp(m) for m in means)} | "
            f"{'–' if rc is None else f'{rc:+.2f}'} | {D.pp(D.mean([x for _, x in tb]))} | "
            f"{D.pp(hl[0])} / {D.pp(hl[1])} | {sum(x > 0 for _, x in tb)}/{len(tb)} |")


def report():
    print("# Test 4: F-score and accruals (attempt #13)\n")
    print("| Market | Sort | Horizon | group means, low -> high (pp) | rank corr. | top - bottom | "
          "half 1 / half 2 | top > bottom |")
    print("|---|---|---|---|---|---|---|---|")
    filt_lines = []
    for market in ("nordic", "us-bust", "us-last"):
        data = D.load(market)
        attach(market, data)
        fgroup = lambda r, d: (None if r["_f"] is None else
                               next(i for i, (lo, hi) in enumerate(GROUPS) if lo <= r["_f"] <= hi))
        for h in (1, 3, 5):
            print(groups_line(market, data, h, "F-score 0-3/4/5/6/7/8-9", fgroup, GROUPS))
            # accrual fifths, HIGH accruals first so 'top' = the lowest accruals
            qcut = {}
            for d, rows in data.items():
                xs = sorted(r["_acc"] for r in MS.usable(rows, h) if r["_acc"] is not None)
                qcut[d] = [xs[i * len(xs) // 5] for i in range(1, 5)] if len(xs) >= 25 else None
            def agroup(r, d):
                if r["_acc"] is None or qcut[d] is None:
                    return None
                return 4 - sum(r["_acc"] >= c for c in qcut[d])
            print(groups_line(market, data, h, "accrual fifths, highest -> lowest", agroup, range(5)))
        for h in (3, 5):
            for selname in ("fvp5", "key5", "method"):
                if selname == "method" and market == "nordic":
                    continue
                res = {"none": [], "F>=7": [], "top accrual decile out": []}
                counts = {k: 0 for k in res}
                for d, rows in sorted(data.items()):
                    u = MS.usable(rows, h)
                    sel = {"fvp5": lambda: D.fifth(u, MS.fv_ratio), "key5": lambda: D.key_best_fifth(u),
                           "method": lambda: MS.portfolio(u)}[selname]()
                    if not sel:
                        continue
                    accs = sorted(r["_acc"] for r in u if r["_acc"] is not None)
                    dec = accs[9 * len(accs) // 10] if len(accs) >= 10 else None
                    variants = {"none": sel,
                                "F>=7": [r for r in sel if r["_f"] is not None and r["_f"] >= 7],
                                "top accrual decile out": [r for r in sel if r["_acc"] is None or dec is None
                                                           or r["_acc"] < dec]}
                    for k, v in variants.items():
                        counts[k] += len(v)
                        if v:
                            res[k].append((d, statistics.mean(MS.excess(r, h) for r in v)))
                base = dict(res["none"])
                for k, xs in res.items():
                    rel = [(d, x - base[d]) for d, x in xs]
                    hl = [D.mean([x for d, x in rel if D.half_of(market, d) == hf]) for hf in (0, 1)]
                    filt_lines.append(f"| {market} | {selname} | {h} y | {k} | {D.pp(D.mean([x for _, x in xs]))} | "
                                      f"{D.pp(D.mean([x for _, x in rel]))} | {D.pp(hl[0])} / {D.pp(hl[1])} | "
                                      f"{counts[k]} names, {len(xs)} dates |")
    print("\n## As filters on the method's rankings\n")
    print("| Market | Selection | Horizon | Filter | mean excess | vs unfiltered | vs unfiltered, half 1 / half 2 | N |")
    print("|---|---|---|---|---|---|---|---|")
    print("\n".join(filt_lines))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--signals", action="store_true")
    ap.add_argument("--workers", type=int, default=17)
    a = ap.parse_args(argv)
    if a.signals:
        make_signals(a.workers)
    else:
        report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
