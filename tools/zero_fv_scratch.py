import json, yfinance as yf, pandas as pd
from vss import valuation as VA
W={h["name"]:h["y"] for h in json.load(open("data/zero.json"))["holdingChartData"]}
T=[("Investor B","INVE-B.ST"),("Atlas Copco A","ATCO-A.ST"),("Volvo B","VOLV-B.ST"),("Sandvik","SAND.ST"),("Swedbank A","SWED-A.ST"),("SEB A","SEB-A.ST"),("ABB","ABB.ST"),("Assa Abloy B","ASSA-B.ST"),("EQT","EQT.ST"),("SAAB B","SAAB-B.ST"),("Handelsbanken A","SHB-A.ST"),("Ericsson B","ERIC-B.ST"),("Hexagon B","HEXA-B.ST"),("AstraZeneca","AZN.ST"),("Alfa Laval","ALFA.ST"),("H&M B","HM-B.ST"),("Epiroc A","EPI-A.ST"),("Telia Company","TELIA.ST"),("Essity B","ESSITY-B.ST"),("Evolution","EVO.ST"),("Boliden","BOL.ST"),("SKF B","SKF-B.ST"),("Tele2 B","TEL2-B.ST"),("Nordea","NDA-SE.ST")]
BANK={"SWED-A.ST","SEB-A.ST","SHB-A.ST","NDA-SE.ST","INVE-B.ST"}
fxc={}
def fx(c):
    if c=="SEK": return 1.0
    if c not in fxc: fxc[c]=float(yf.Ticker(f"{c}SEK=X").history(period="5d")["Close"].iloc[-1])
    return fxc[c]
def g(df,*names):
    for n in names:
        if n in df.index: return df.loc[n]
    return None
rows=[]
for name,t in T:
    tk=yf.Ticker(t); info=tk.info; price=float(tk.history(period="5d")["Close"].iloc[-1])
    if t in BANK: rows.append((name,t,W.get(name),price,None,None,None,None,"bank/holding: FCF-DCF passar inte")); continue
    cf=tk.cashflow; bs=tk.balance_sheet
    fcf=g(cf,"Free Cash Flow"); fcf=fcf.dropna().sort_index(ascending=False)[:3]
    cur=info.get("financialCurrency","SEK"); k=fx(cur)
    cash=(g(bs,"Cash Cash Equivalents And Short Term Investments","Cash And Cash Equivalents").dropna().sort_index().iloc[-1])
    debt=g(bs,"Total Debt"); debt=0 if debt is None else debt.dropna().sort_index().iloc[-1]
    sh=info.get("impliedSharesOutstanding") or info.get("sharesOutstanding")
    f0=fcf.mean()*k; nc=(cash-debt)*k
    fv=[]
    for gr in (0.0,0.04,0.08):
        try: fv.append(VA.equity_value_per_share(fcf0=f0*(1+gr),growth=gr,net_cash=nc,shares=sh))
        except Exception as e: fv.append(float("nan"))
    rows.append((name,t,W.get(name),price,*fv,f"FCF {len(fcf)}y {cur} {fcf.mean()/1e9:.1f}bn, shares {sh/1e6:.0f}m"))
for r in rows:
    n,t,w,p,b,ba,bu,_,note=(r+(None,))[:9] if len(r)==8 else (r[0],r[1],r[2],r[3],r[4],r[5],r[6],None,r[-1])
    f=lambda x:"   -  " if x is None or x!=x else f"{x:7.1f}"
    print(f"{n:16s} {w:5.2f}% {p:8.1f} | {f(b)} {f(ba)} {f(bu)} | {'' if not ba else f'{p/ba:4.1f}x'} | {note}")
