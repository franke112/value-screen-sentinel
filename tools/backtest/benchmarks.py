"""TEST A2 (ATTEMPTS #16): the best and worst fifths against several
benchmarks, and Ken French's value portfolios over the same windows.

    DEVOUR_LB=clean .venv/bin/python -m tools.backtest.benchmarks > data/backtest/devour-bench-r2/MEASURE.md

For the best and worst fifth on fv/price and on the E43 key, per market,
the mean over test dates of: best - equal-weighted universe, best -
cap-weighted universe, best - index (the stored benchmark), and universe -
worst (EW and CW). French (data/french/, downloaded 2026-11-08):
Nordic -- each country's value-weighted BE/ME High (top 30 %), Low (bottom
30 %) and market in LOCAL currency, mean of the four countries; US -- the
value-weighted BE/ME Hi 20 and Lo 20 quintiles and the market (Mkt-RF +
RF). Windows: 36 or 60 months from the month after the test date; a
window the data does not fully cover is left out and counted.
"""
from __future__ import annotations

import io
import re
import statistics
import sys
import zipfile
from pathlib import Path

from . import devour as D
from . import measure as MS
from . import measure_key as MK

FRENCH = D.ROOT / "data" / "french"
COUNTRIES = ("Sweden", "Norway", "Denmark", "Finland")


def _blocks(lines):
    """Consecutive runs of 'yyyymm values' lines, in file order."""
    out, cur = [], None
    for l in lines:
        m = re.match(r"^\s*(\d{6})\s*,?\s*(.*)$", l)
        if m and len(m.group(1)) == 6:
            if cur is None:
                cur = {}
                out.append(cur)
            vals = [float(v) for v in re.split(r"[,\s]+", m.group(2).strip()) if v]
            cur[(int(m.group(1)[:4]), int(m.group(1)[4:]))] = vals
        elif l.strip():
            cur = None
    return out


def french_nordic():
    z = zipfile.ZipFile(FRENCH / "F-F_International_Countries.zip")
    out = {}
    for c in COUNTRIES:
        bl = _blocks(z.read(f"{c}.Dat").decode("latin-1").splitlines())
        local = bl[1]          # the second block: value-weight LOCAL returns, all firms
        out[c] = {k: {"mkt": v[0], "high": v[1], "low": v[2]} for k, v in local.items()}
    return out


def french_us():
    z = zipfile.ZipFile(FRENCH / "Portfolios_Formed_on_BE-ME_CSV.zip")
    text = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    head = next(l for l in text if "Lo 20" in l).split(",")
    vw = _blocks(text)[0]                       # value-weight monthly
    lo, hi = head.index("Lo 20") - 1, head.index("Hi 20") - 1
    f = zipfile.ZipFile(FRENCH / "F-F_Research_Data_Factors_CSV.zip")
    fac = _blocks(f.read(f.namelist()[0]).decode("latin-1").splitlines())[0]
    out = {}
    for k, v in vw.items():
        if k in fac:
            out[k] = {"high": v[hi], "low": v[lo], "mkt": fac[k][0] + fac[k][3]}
    return {"US": out}


def window(series, start_ym, months):
    """compounded return of each column over `months` from start_ym, or None."""
    y, m = start_ym
    acc = {"high": 1.0, "low": 1.0, "mkt": 1.0}
    for i in range(months):
        k = (y + (m - 1 + i) // 12, (m - 1 + i) % 12 + 1)
        if k not in series:
            return None
        for c in acc:
            v = series[k][c]
            if v <= -99:
                return None
            acc[c] *= 1 + v / 100
    return {c: v - 1 for c, v in acc.items()}


def ranked(rows, how):
    if how == "E43 key":
        return MK.key_order(rows)                                 # best first
    return sorted((r for r in rows if MS.fv_ratio(r) is not None), key=MS.fv_ratio, reverse=True)


def cap(r):
    return r.get("market_cap_usd") or r.get("market_cap")


def ret(r, h):
    x = r["returns"]
    return x.get(str(h), x.get(h))


def main() -> int:
    print("# A2: benchmarks (attempt #16), cleaned data\n")
    print("Mean over test dates, pp. top = best fifth minus the universe; bottom = the universe minus the "
          "worst fifth. EW / CW = equal- / cap-weighted universe of the same valued names.\n")
    print("| Market | Key | h | best - EW | best - CW | best - index | EW - worst | CW - worst | "
          "best - EW, half 1 / half 2 | EW - worst, half 1 / half 2 | dates |")
    print("|---|---|---|---:|---:|---:|---:|---:|---|---|---:|")
    for market in ("nordic", "us-bust", "us-last"):
        data = D.load(market)
        for how in ("fv/price", "E43 key"):
            for h in (3, 5):
                per = []
                for d, rows in sorted(data.items()):
                    u = MS.usable(rows, h)
                    rs = ranked(u, how)
                    if len(rs) < 25:
                        continue
                    k = len(rs)
                    best, worst = rs[:k // 5], rs[-(k // 5):]
                    ew = statistics.mean(ret(r, h) for r in u)
                    w = [(cap(r), ret(r, h)) for r in u if cap(r)]
                    cw = sum(a * b for a, b in w) / sum(a for a, _ in w)
                    bm = statistics.mean(ret(r, h) for r in best)
                    wm = statistics.mean(ret(r, h) for r in worst)
                    idx = u[0]["index_returns"].get(str(h), u[0]["index_returns"].get(h))
                    per.append({"d": d, "bew": bm - ew, "bcw": bm - cw, "bix": bm - idx,
                                "eww": ew - wm, "cww": cw - wm})
                m = lambda k: D.pp(D.mean([p[k] for p in per]))
                hl = lambda k, hf: D.pp(D.mean([p[k] for p in per if D.half_of(market, p["d"]) == hf]))
                print(f"| {market} | {how} | {h} y | {m('bew')} | {m('bcw')} | {m('bix')} | {m('eww')} | "
                      f"{m('cww')} | {hl('bew', 0)} / {hl('bew', 1)} | {hl('eww', 0)} / {hl('eww', 1)} | {len(per)} |")
    print("\n## Ken French over the same windows (value-weighted; Nordic in local currency)\n")
    print("| Market | h | High - market | market - Low | High - Low | High - market, half 1 / half 2 | "
          "market - Low, half 1 / half 2 | windows covered |")
    print("|---|---|---:|---:|---:|---|---|---|")
    fn, fu = french_nordic(), french_us()
    for market, src, dates in (("nordic", fn, sorted(D.load("nordic"))),
                               ("us", fu, sorted(D.load("us-bust")))):
        for h in (3, 5):
            per, missing = [], 0
            for d in dates:
                y = int(d[:4])
                ws = [window(s, (y, 5), 12 * h) for s in src.values()]
                ws = [w for w in ws if w]
                if len(ws) < len(src):
                    missing += 1
                    continue
                per.append({"d": d, "top": statistics.mean(w["high"] - w["mkt"] for w in ws),
                            "bot": statistics.mean(w["mkt"] - w["low"] for w in ws),
                            "hl": statistics.mean(w["high"] - w["low"] for w in ws)})
            mk = "nordic" if market == "nordic" else "us-bust"
            m = lambda k: D.pp(D.mean([p[k] for p in per]))
            hl = lambda k, hf: D.pp(D.mean([p[k] for p in per if D.half_of(mk, p["d"]) == hf]))
            print(f"| {market} | {h} y | {m('top')} | {m('bot')} | {m('hl')} | {hl('top', 0)} / {hl('top', 1)} | "
                  f"{hl('bot', 0)} / {hl('bot', 1)} | {len(per)} of {len(dates)} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
