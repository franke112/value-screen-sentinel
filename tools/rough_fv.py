"""Rough bear / base / bull per share for ANY listing Yahoo covers -- a
SCREEN, not a strike, and never a figure for config/manual/ or the watchlist.

    .venv/bin/python tools/rough_fv.py EVO.ST ZZ-B.ST UMG.AS

The method of reference/AVANZA-ZERO-FV-2026-11-02.md, generalised from
tools/zero_fv_scratch.py: Yahoo's free cash flow (operating cash flow less
capex), mean of the last three fiscal years; net cash = cash less total
debt at the last balance sheet; implied shares across all classes; the
statement currency converted to the TRADING currency (GBX = pence).
Growth 0 / 4 / 8 % into vss.valuation's engine (r 9.5 %).

What it does NOT do, and why a name that passes still needs a hand read:
no E140 normalisation (working capital is in the mean), no E142 deal
programme, no E143 cycle level, no E144 derived growth, no IFRS 16 rent
correction (a heavy leaser's FCF is overstated), and no E145 tests beyond
the rough return-on-capital and debt lines printed beside the value.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vss import valuation as VA  # noqa: E402

GROWTHS = (0.0, 0.04, 0.08)


def _row(df, *names):
    if df is None:
        return None
    for n in names:
        if n in df.index:
            return df.loc[n].dropna().sort_index(ascending=False)
    return None


def _fx(src: str, dst: str) -> float:
    import yfinance as yf
    if src == dst:
        return 1.0
    return float(yf.Ticker(f"{src}{dst}=X").history(period="5d")["Close"].iloc[-1])


def rough(ticker: str) -> dict:
    import yfinance as yf
    tk = yf.Ticker(ticker)
    info = tk.info
    hist = tk.history(period="10d")["Close"].dropna()   # today's row is NaN until it settles
    price = float(hist.iloc[-1]) if len(hist) else None
    trade = info.get("currency") or "USD"
    fin = info.get("financialCurrency") or trade
    pence = trade in ("GBp", "GBX")
    k = _fx(fin, "GBP" if pence else trade) * (100 if pence else 1)
    cf, bs, inc = tk.cashflow, tk.balance_sheet, tk.income_stmt
    fcf = _row(cf, "Free Cash Flow")
    if fcf is None or fcf.empty:
        return {"ticker": ticker, "price": price, "error": "no free cash flow row"}
    fcf3 = fcf.iloc[:3]
    cash = _row(bs, "Cash Cash Equivalents And Short Term Investments",
                "Cash And Cash Equivalents")
    debt = _row(bs, "Total Debt")
    nc = ((cash.iloc[0] if cash is not None and len(cash) else 0)
          - (debt.iloc[0] if debt is not None and len(debt) else 0))
    shares = info.get("impliedSharesOutstanding") or info.get("sharesOutstanding")
    ebit = _row(inc, "Operating Income", "EBIT")
    out = {"ticker": ticker, "price": price, "ccy": trade, "fin": fin,
           "fcf_years": [f"{d.year}:{v / 1e6:,.0f}" for d, v in fcf3.items()],
           "fcf_mean_m": fcf3.mean() / 1e6, "net_cash_m": nc / 1e6,
           "nd_over_fcf": (-nc / fcf3.mean()) if fcf3.mean() > 0 else None,
           "fcf_negative_years": int((fcf.iloc[:4] <= 0).sum()),
           "ebit_m": [f"{d.year}:{v / 1e6:,.0f}" for d, v in ebit.iloc[:4].items()] if ebit is not None else []}
    vals = []
    for g in GROWTHS:
        try:
            vals.append(VA.equity_value_per_share(
                fcf0=fcf3.mean() * k * (1 + g), growth=g, net_cash=nc * k, shares=shares))
        except Exception:  # noqa: BLE001
            vals.append(float("nan"))
    out["bear"], out["base"], out["bull"] = vals
    return out


def main(argv=None) -> int:
    for t in (argv or sys.argv[1:]):
        try:
            r = rough(t)
        except Exception as exc:  # noqa: BLE001
            print(f"== {t}  ERROR {type(exc).__name__}: {exc}")
            continue
        if "error" in r:
            print(f"== {t}  price {r['price']}  {r['error']}")
            continue
        f = lambda x: "--" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:,.2f}"
        ratio = (r["price"] / r["base"]) if r["price"] and r["base"] and r["base"] > 0 else None
        print(f"== {t}  price {f(r['price'])} {r['ccy']}  |  bear {f(r['bear'])}  base {f(r['base'])}  "
              f"bull {f(r['bull'])}  |  price/base {f(ratio)}x")
        print(f"   FCF ({r['fin']} m) {', '.join(r['fcf_years'])}; mean {r['fcf_mean_m']:,.0f}; "
              f"net cash {r['net_cash_m']:,.0f}; net debt/FCF {f(r['nd_over_fcf'])}; "
              f"FCF<=0 in {r['fcf_negative_years']} of last 4 years; EBIT {', '.join(r['ebit_m'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
