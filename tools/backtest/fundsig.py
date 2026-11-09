"""Round 2 signals (ATTEMPTS #17, #19, #21): per valued row, from the facts
visible on the test day.

    .venv/bin/python -m tools.backtest.fundsig        # data/backtest/devour-fundsig-r2/<market>.jsonl

- the quarter signals the hard kills read (`xbrl.build_quarters` +
  `value.with_ratios`), and the kills themselves recomputed by the engine's
  own `value.kills` -- on Nordic rows with receivables and inventory added
  to the translation IN THIS PROCESS ONLY (the stored Nordic 4.2.7 is never
  evaluable);
- EPS misses: EODHD Earnings History, reports dated before the test day,
  `epsActual` < `epsEstimate`, over the last eight with both;
- annual lines for asset growth and the competitors (Magic Formula,
  Quantitative Value, O'Shaughnessy VC2, Piotroski's book-to-market), at the
  newest fiscal year with net income, operating cash flow and assets, and
  the year before.
Nothing is valued; no return is read.
"""
from __future__ import annotations

import gzip
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date

from vss import history as HI
from vss import xbrl as X

from . import devour as D
from . import fscore_accruals as FA
from . import method as M
from . import pilot as PL
from . import pit as P
from . import value as V

OUT = D.BT / "devour-fundsig-r2"
FUND = D.ROOT / "data" / "eodhd" / "fundamentals"

DUR = {
    "ni": ("NetIncomeLoss",),
    "ocf": ("NetCashProvidedByUsedInOperatingActivities",),
    "rev": HI.XBRL_TAGS["revenue"],
    "cogs": ("CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"),
    "gp": ("GrossProfit",),
    "sga": ("SellingGeneralAndAdministrativeExpense",),
    "da": ("DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
           "DepreciationAmortizationAndAccretionNet", "Depreciation"),
    "div": ("PaymentsOfDividends", "PaymentsOfDividendsCommonStock"),
    "buyback": ("PaymentsForRepurchaseOfCommonStock",),
    "ebit": ("OperatingIncomeLoss",),
}
INST = {
    "assets": ("Assets",), "equity": ("StockholdersEquity",
                                      "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    "liab": ("Liabilities",), "ca": ("AssetsCurrent",), "cl": ("LiabilitiesCurrent",),
    "cash": ("CashAndCashEquivalentsAtCarryingValue",), "ppe": ("PropertyPlantAndEquipmentNet",),
    "rec": ("AccountsReceivableNetCurrent",), "inv": ("InventoryNet",),
    "re": ("RetainedEarningsAccumulatedDeficit",),
    "ltd": ("LongTermDebtNoncurrent", "LongTermDebt"),
}


def _nordic_extend():
    from . import nordic as N
    if "netReceivables" in N.BALANCE:
        return N
    N.BALANCE.update({"totalCurrentAssets": "AssetsCurrent", "totalCurrentLiabilities": "LiabilitiesCurrent",
                      "netReceivables": "AccountsReceivableNetCurrent", "inventory": "InventoryNet",
                      "totalLiab": "Liabilities", "retainedEarnings": "RetainedEarningsAccumulatedDeficit"})
    N.INCOME.update({"costOfRevenue": "CostOfRevenue",
                     "sellingGeneralAdministrative": "SellingGeneralAndAdministrativeExpense",
                     "depreciationAndAmortization": "DepreciationDepletionAndAmortization"})
    N.CASH.update({"dividendsPaid": "PaymentsOfDividends"})
    N.POSITIVE = N.POSITIVE + ("PaymentsOfDividends", "DepreciationDepletionAndAmortization")
    return N


def _nordic_facts(sym):
    N = _nordic_extend()
    d = json.loads(gzip.decompress((FUND / f"{sym}.json.gz").read_bytes()))
    facts = FA._nordic_facts(sym)            # assets guard of round 1 included
    return facts, d


def _eodhd_file(sym):
    p = FUND / f"{sym}.json.gz"
    return json.loads(gzip.decompress(p.read_bytes())) if p.exists() else None


def eps_misses(d, day: date):
    if not d:
        return None, 0
    hist = (d.get("Earnings") or {}).get("History") or {}
    rows = []
    for v in hist.values():
        if not isinstance(v, dict):
            continue
        rd, a, e = v.get("reportDate"), v.get("epsActual"), v.get("epsEstimate")
        if rd and rd < day.isoformat() and a is not None and e is not None:
            rows.append((rd, float(a), float(e)))
    rows = sorted(rows)[-8:]
    if len(rows) < 8:
        return None, len(rows)
    return sum(a < e for _, a, e in rows), len(rows)


def buybacks_nordic(d, y_end):
    cf = (((d or {}).get("Financials") or {}).get("Cash_Flow") or {}).get("yearly") or {}
    e = cf.get(y_end) or {}
    try:
        v = float(e.get("salePurchaseOfStock"))
    except (TypeError, ValueError):
        return None
    return max(0.0, -v)


def annual_lines(cut):
    ends = FA.fy_ends(cut, "NetIncomeLoss")
    ni, ocf = M.annual(cut, "NetIncomeLoss"), M.annual(cut, DUR["ocf"][0])
    a = FA.at_ends(cut, "Assets", ends)
    years = [y for y in ni if y in ocf and y in a]
    if not years:
        return None, None
    y = max(years)
    out = {"year": y, "end": ends.get(y)}
    for z, tag in ((y, ""), (y - 1, "_1")):
        for k, tags in DUR.items():
            v = None
            for t in tags:
                v = M.annual(cut, t).get(z)
                if v is not None:
                    break
            out[k + tag] = v
        for k, tags in INST.items():
            v = None
            for t in tags:
                v = FA.at_ends(cut, t, ends).get(z)
                if v is not None:
                    break
            out[k + tag] = v
    return out, ends


def quarter_signals(cut):
    try:
        qs = V.with_ratios([X.as_quarter(q) for q in X.build_quarters(cut, limit=12)])
    except Exception as exc:  # noqa: BLE001
        return {"q_error": f"{type(exc).__name__}"[:60]}
    if len(qs) < 5:
        return {"q_n": len(qs)}
    by = {q.period: q for q in qs}
    last = qs[-1]
    from vss import rules as RU
    parts = RU.period_parts(last.period)
    prior = by.get(f"{parts[0] - 1}-{parts[1]}") if parts else None
    out = {"q_n": len(qs), "rev_yoy": last.revenue_yoy}
    if prior and last.op_margin is not None and prior.op_margin is not None:
        out["margin_chg_bps"] = (last.op_margin - prior.op_margin) * 10_000
    if prior and last.receivables and prior.receivables and prior.receivables > 0:
        out["rec_growth"] = last.receivables / prior.receivables - 1
    # ATTEMPTS #24 (registered 2026-11-08): 4.2.1 as a continuous score --
    # consecutive YoY revenue declines counted back from the newest quarter
    # -- and 4.2.7's inventory leg
    n = 0
    for q in reversed(qs):
        if q.revenue_yoy is None or q.revenue_yoy >= 0:
            break
        n += 1
    out["rev_declines"] = n
    li, pi = getattr(last, "inventory", None), getattr(prior, "inventory", None) if prior else None
    if li and pi and pi > 0:
        out["inv_growth"] = li / pi - 1
    return out


def job(args):
    market, d = args
    rows = D.load(market, fill=False)[d]
    out = []
    for r in rows:
        if r.get("status") != "ok":
            continue
        day = D.start_day(r)
        rec = {"id": str(r.get("cik"))}
        try:
            if market == "nordic":
                facts, raw = _nordic_facts(r["symbol"])
            else:
                facts = PL.company_facts(int(r["cik"]))
                raw = _eodhd_file(r.get("eodhd_symbol")) if r.get("eodhd_symbol") else None
            rec["eps_misses"], rec["eps_n"] = eps_misses(raw, day)
            if facts is None:
                rec["why"] = "no facts"
                out.append(rec)
                continue
            cut = P.clip(facts, day)
            lines, _ = annual_lines(cut)
            if lines:
                rec.update(lines)
                if market == "nordic":
                    rec["buyback"] = buybacks_nordic(raw, lines["end"]) if lines.get("end") else None
            rec.update(quarter_signals(cut))
            rec["kills"] = {k["rule"]: k["state"] for k in V.kills(cut, None, day)}
        except Exception as exc:  # noqa: BLE001
            rec["why"] = f"{type(exc).__name__}: {exc}"[:200]
        out.append(rec)
    return market, d, out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(m, d) for m in ("nordic", "us-bust") for d in D.load(m, fill=False)]
    got = {}
    with ProcessPoolExecutor(int(__import__("os").environ.get("BT_WORKERS", "17"))) as pool:
        for market, d, out in pool.map(job, jobs):
            got.setdefault(market, {})[d] = out
    for market, by in got.items():
        D.write_jsonl(OUT / f"{market}.jsonl", [{"date": d, **x} for d, xs in sorted(by.items()) for x in xs])
        xs = [x for v in by.values() for x in v]
        cov = {k: sum(x.get(k) is not None for x in xs) for k in
               ("margin_chg_bps", "rec_growth", "eps_misses", "equity", "rev", "da", "div", "buyback",
                "ca", "cl", "ppe", "rec", "re", "liab", "assets_1", "sga", "cogs")}
        kills = {}
        for x in xs:
            for k, s in (x.get("kills") or {}).items():
                kills.setdefault(k, {}).setdefault(s, 0)
                kills[k][s] += 1
        errs = sum(1 for x in xs if x.get("why"))
        print(f"{market}: {len(xs)} rows, errors {errs}; coverage {cov}")
        print(f"   kills: { {k: v for k, v in sorted(kills.items()) if k in ('4.2.2', '4.2.7', '4.2.1')} }")
    return 0


if __name__ == "__main__":
    sys.exit(main())
