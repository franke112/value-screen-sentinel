"""TEST A7 (ATTEMPTS #21): ablation of the method's chain, and competitors.

    DEVOUR_LB=clean .venv/bin/python -m tools.backtest.a7_ablation > data/backtest/devour-a7-r2/MEASURE.md

(a) the chain as FILTERS: band (15-50 % under the 52-week high, cleaned
    series) -> E145 Q1-Q4 -> no measurable hard kill -> MBP at 0.65 x fv;
    full, each brick removed, each brick alone.
(a') the same bricks as a COMPOSITE RANK (mean percentile): band = closeness
    to the band's centre, quality = Q1-Q4 passed, kills = fewer tripped,
    value = fv/price; the best fifth, and with each brick left out.
(b) Magic Formula, Quantitative Value (approximated: Beneish M and Altman Z
    filters, cheapest fifth by EBIT/EV, better half by F-score),
    O'Shaughnessy VC2, Piotroski (F >= 8 in the cheapest book-to-market
    fifth), on the same rows; lines from data/backtest/devour-fundsig-r2/.
"""
from __future__ import annotations

import json
import statistics
import sys

from . import devour as D
from . import fscore_accruals as FA
from . import measure as MS
from . import measure_key as MK

BAND = (0.15, 0.50)
BRICKS = ("band", "quality", "kills", "mbp")


def prep(market, data):
    FA.attach(market, data)
    sig = {}
    for l in (D.BT / "devour-fundsig-r2" / f"{'nordic' if market == 'nordic' else 'us-bust'}.jsonl").read_text().splitlines():
        x = json.loads(l)
        sig[(x["date"], x["id"])] = x
    for d, rows in data.items():
        for r in rows:
            if r.get("status") != "ok":
                continue
            r["_l"] = sig.get((d, str(r.get("cik"))), {})
            r["_dd"] = MK.drawdown(D.symbol(r), D.start_day(r)) if r.get("price") else None


def passes(r, brick):
    if brick == "band":
        return r["_dd"] is not None and BAND[0] <= r["_dd"] <= BAND[1]
    if brick == "quality":
        return r.get("passes_quality") is True
    if brick == "kills":
        return not r.get("measured_kill")
    if brick == "mbp":
        v = MS.fv_ratio(r)
        return v is not None and v >= 1 / MS.MOS
    raise ValueError(brick)


def pct_ranks(rows, val):
    """percentile (0..1, higher = better) of val(r); None -> 0.5"""
    xs = [(val(r), i) for i, r in enumerate(rows)]
    have = sorted((v, i) for v, i in xs if v is not None)
    out = [0.5] * len(rows)
    n = len(have)
    for k, (_, i) in enumerate(have):
        out[i] = (k + 0.5) / n if n else 0.5
    return out


def composite_fifth(u, bricks):
    comps = {
        "band": lambda r: None if r["_dd"] is None else -abs(r["_dd"] - sum(BAND) / 2),
        "quality": lambda r: sum(1 for v in (r.get("quality") or {}).values() if v is True),
        "kills": lambda r: -sum(1 for k in (r.get("kills") or []) if k.get("state") == "TRIP"
                                and k.get("rule") in ("4.2.1", "4.2.2", "4.2.5", "4.2.7")),
        "mbp": MS.fv_ratio,
    }
    ranks = [pct_ranks(u, comps[b]) for b in bricks]
    score = [statistics.mean(rk[i] for rk in ranks) for i in range(len(u))]
    order = sorted(range(len(u)), key=lambda i: -score[i])
    return [u[i] for i in order[:len(u) // 5]] if len(u) >= 25 else []


# --- competitors -------------------------------------------------------------

def _div(a, b):
    return None if a is None or b in (None, 0) else a / b


def beneish(l):
    try:
        rev, rev1 = l["rev"], l["rev_1"]
        gm = (rev - l["cogs"]) / rev if l.get("cogs") is not None else l["gp"] / rev
        gm1 = (rev1 - l["cogs_1"]) / rev1 if l.get("cogs_1") is not None else l["gp_1"] / rev1
        dsri = (l["rec"] / rev) / (l["rec_1"] / rev1)
        gmi = gm1 / gm
        aqi = (1 - (l["ca"] + l["ppe"]) / l["assets"]) / (1 - (l["ca_1"] + l["ppe_1"]) / l["assets_1"])
        sgi = rev / rev1
        depi = (l["da_1"] / (l["da_1"] + l["ppe_1"])) / (l["da"] / (l["da"] + l["ppe"]))
        sgai = (l["sga"] / rev) / (l["sga_1"] / rev1)
        lvgi = ((l["cl"] + (l["ltd"] or 0)) / l["assets"]) / ((l["cl_1"] + (l["ltd_1"] or 0)) / l["assets_1"])
        tata = (l["ni"] - l["ocf"]) / l["assets"]
    except (KeyError, TypeError, ZeroDivisionError):
        return None
    return (-4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi + 0.115 * depi
            - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi)


def altman(l, mcap):
    try:
        ta = l["assets"]
        tl = l.get("liab") if l.get("liab") is not None else ta - l["equity"]
        return (1.2 * (l["ca"] - l["cl"]) / ta + 1.4 * l["re"] / ta + 3.3 * l["ebit"] / ta
                + 0.6 * mcap / tl + 1.0 * l["rev"] / ta)
    except (KeyError, TypeError, ZeroDivisionError):
        return None


def mcap(r):
    return r.get("market_cap") or ((r.get("shares") or 0) * (r.get("price") or 0)) or None


def magic(u):
    def roc(r):
        l = r["_l"]
        try:
            cap = max(0.0, l["ca"] - (l.get("cash") or 0) - l["cl"]) + l["ppe"]
            return r["ebit"] / cap if cap > 0 and r.get("ebit") is not None else None
        except (KeyError, TypeError):
            return None
    rs = [r for r in u if r.get("ebit_ev") is not None and roc(r) is not None]
    a = {id(r): i for i, r in enumerate(sorted(rs, key=lambda r: -r["ebit_ev"]))}
    b = {id(r): i for i, r in enumerate(sorted(rs, key=lambda r: -roc(r)))}
    rs = sorted(rs, key=lambda r: a[id(r)] + b[id(r)])
    return rs[:len(rs) // 5] if len(rs) >= 25 else []


def qv(u):
    keep = []
    for r in u:
        m = beneish(r["_l"])
        z = altman(r["_l"], mcap(r))
        if (m is not None and m > -1.78) or (z is not None and z < 1.81):
            continue
        if r.get("ebit_ev") is not None:
            keep.append(r)
    if len(keep) < 25:
        return []
    cheap = sorted(keep, key=lambda r: -r["ebit_ev"])[:len(keep) // 5]
    cheap = sorted(cheap, key=lambda r: -(r["_f"] if r["_f"] is not None else -1))
    return cheap[:max(1, len(cheap) // 2)]


def vc2(u):
    def ratio(f):
        return lambda r: f(r["_l"], mcap(r), r)
    comps = [
        ratio(lambda l, m, r: _div(l.get("equity"), m)),
        ratio(lambda l, m, r: _div(l.get("ni"), m)),
        ratio(lambda l, m, r: _div(l.get("rev"), m)),
        ratio(lambda l, m, r: None if r.get("ebit") is None or l.get("da") is None or not r.get("ev")
              or r["ev"] <= 0 else (r["ebit"] + l["da"]) / r["ev"]),
        ratio(lambda l, m, r: _div(l.get("ocf"), m)),
        ratio(lambda l, m, r: None if l.get("div") is None and l.get("buyback") is None
              else _div((l.get("div") or 0) + (l.get("buyback") or 0), m)),
    ]
    ranks = [pct_ranks(u, c) for c in comps]
    score = [statistics.mean(rk[i] for rk in ranks) for i in range(len(u))]
    order = sorted(range(len(u)), key=lambda i: -score[i])
    return [u[i] for i in order[:len(u) // 5]] if len(u) >= 25 else []


def piotroski(u):
    rs = [r for r in u if r["_l"].get("equity") and r["_l"]["equity"] > 0 and mcap(r)]
    if len(rs) < 25:
        return []
    cheap = sorted(rs, key=lambda r: -r["_l"]["equity"] / mcap(r))[:len(rs) // 5]
    return [r for r in cheap if r["_f"] is not None and r["_f"] >= 8]


def measure(data, market, h, select):
    per, buys, empty = [], 0, 0
    for d, rows in sorted(data.items()):
        u = MS.usable(rows, h)
        sel = select(u)
        buys += len(sel)
        if not sel:
            empty += 1
            continue
        per.append((d, statistics.mean(MS.excess(r, h) for r in sel)))
    xs = [x for _, x in per]
    hl = [D.mean([x for d, x in per if D.half_of(market, d) == hf]) for hf in (0, 1)]
    return {"mean": D.mean(xs), "sd": statistics.pstdev(xs) if len(xs) > 1 else None, "buys": buys,
            "empty": empty, "h1": hl[0], "h2": hl[1], "n": len(xs), "per": per}


def line(market, label, h, m):
    return (f"| {market} | {label} | {h} y | {D.pp(m['mean'])} | {D.pp(m['sd'])} | {D.pp(m['h1'])} / {D.pp(m['h2'])} | "
            f"{m['buys']} | {m['empty']} |")


def main() -> int:
    print("# A7: ablation and competitors (attempt #21), cleaned data, Nordic nordic-m7\n")
    head = "| Market | Variant | h | mean excess | sd over dates | half 1 / half 2 | buys | dates with no buy |\n|---|---|---|---:|---:|---|---:|---:|"
    out_a, out_b, out_c = [head], [head], [head]
    results = {}
    for market in ("nordic", "us-bust", "us-last"):
        data = D.load(market)
        prep(market, data)
        for h in (3, 5):
            variants = [("FULL chain (all four)", BRICKS)]
            variants += [(f"without {b}", tuple(x for x in BRICKS if x != b)) for b in BRICKS]
            variants += [(f"{b} alone", (b,)) for b in BRICKS]
            variants += [("no filter (all valued)", ())]
            for label, bricks in variants:
                m = measure(data, market, h, lambda u, bricks=bricks: [r for r in u if all(passes(r, b) for b in bricks)])
                out_a.append(line(market, label, h, m))
                results[(market, h, "chain:" + label)] = m
            for label, bricks in [("COMPOSITE, all four", BRICKS)] + [
                    (f"composite without {b}", tuple(x for x in BRICKS if x != b)) for b in BRICKS]:
                m = measure(data, market, h, lambda u, bricks=bricks: composite_fifth(u, bricks))
                out_b.append(line(market, label, h, m))
                results[(market, h, label)] = m
            comps = [("ours: cheapest fv/price fifth", lambda u: D.fifth(u, MS.fv_ratio)),
                     ("ours: E43 best fifth", D.key_best_fifth),
                     ("Magic Formula", magic), ("Quantitative Value (approx.)", qv),
                     ("O'Shaughnessy VC2", vc2), ("Piotroski F>=8, cheapest B/M fifth", piotroski)]
            for label, sel in comps:
                m = measure(data, market, h, sel)
                out_c.append(line(market, label, h, m))
                results[(market, h, label)] = m
    print("## (a) The chain as filters\n")
    print("\n".join(out_a))
    print("\n## (a') The bricks as one composite rank (best fifth)\n")
    print("\n".join(out_b))
    print("\n## (b) Competitors on the same rows\n")
    print("\n".join(out_c))
    print("\n## Ours against each competitor, 3 years: ours - theirs by half (beats = > 0 in both halves of both markets)\n")
    print("| Ours | Competitor | Nordic half 1 / half 2 | US half 1 / half 2 | beats? |")
    print("|---|---|---|---|---|")
    for ours in ("ours: cheapest fv/price fifth", "ours: E43 best fifth", "chain:FULL chain (all four)"):
        for comp in ("Magic Formula", "Quantitative Value (approx.)", "O'Shaughnessy VC2", "Piotroski F>=8, cheapest B/M fifth"):
            cells, ok = [], True
            for market in ("nordic", "us-bust"):
                a, b = results[(market, 3, ours)], results[(market, 3, comp)]
                pa, pb = dict(a["per"]), dict(b["per"])
                ds = sorted(pa.keys() & pb.keys())
                hs = [D.mean([pa[d] - pb[d] for d in ds if D.half_of(market, d) == hf]) for hf in (0, 1)]
                ok = ok and all(x is not None and x > 0 for x in hs)
                cells.append(f"{D.pp(hs[0])} / {D.pp(hs[1])}")
            print(f"| {ours.replace('chain:', '')} | {comp} | {cells[0]} | {cells[1]} | {'yes' if ok else 'no'} |")
    json.dump({f"{k[0]}|{k[1]}|{k[2]}": {"mean": v["mean"], "per": v["per"]} for k, v in results.items()},
              open(D.BT / "devour-a7-r2" / "results.json", "w"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
