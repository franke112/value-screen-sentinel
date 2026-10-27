"""Pilot of the rebuilt method. Every input is from the 2026-10-27 run records
or the filed figures named beside it; nothing here writes anything."""
from vss.valuation import equity_value_per_share as ev, implied_growth
R=0.095
def annuity(g, n=10, r=R):
    return sum((1+g)**t/(1+r)**t for t in range(1,n+1))
def value(c, case):
    g = c['g'][case]
    # 1. owner earnings, organic: 3y mean ex WC, after all capex/SBC/leases,
    #    interest after tax back, minorities out, NO acquisitions; rolled one year (F3)
    e0 = (c['mean'] + c['int'] - c['nci']) * c['level'][case] * (1+g)
    core = ev(fcf0=e0, growth=g, net_cash=-(c['nd']-c['deals_price']), shares=c['sh'])
    roiic = c['roiic'][case]
    k = min(roiic, R)/R - 1          # never credit value creation from future deals
    prog = k * c['acq'] * annuity(g) / c['sh']
    pend = sum(price * ((min(y, R)/R) - 1) for price, y in c['pending'](roiic)) / c['sh']
    return core, prog, pend, core+prog+pend, e0
C = {
 'CENTA': dict(price=39.13, mean=193.349667e6, int=24.609e6, nci=1.346e6, nd=986.187e6, deals_price=840e6,
   sh=61.947e6, acq=21.181333e6, g={'bear':-0.01,'base':0.02,'bull':0.035},
   level={'bear':173.101/193.35,'base':1.0,'bull':1.0},
   roiic={'bear':0.0,'base':0.051,'bull':R},
   # TRIXIE files no profit (PublG 9(2)); Burpee private: both at the acquirer's own record
   pending=lambda y: [(580e6, y), (260e6, y)]),
 'PEP': dict(price=135.46, mean=8323e6, int=840.75e6, nci=44e6, nd=39535e6, deals_price=0, sh=1367e6,
   acq=1320.333e6, g={'bear':0.01,'base':0.02,'bull':0.04}, level={'bear':8182/8323,'base':1.0,'bull':1.0},
   roiic={'bear':0.04,'base':0.055,'bull':R}, pending=lambda y: []),
 'LIAB.ST': dict(price=129.50, mean=567, int=160, nci=0, nd=2959, deals_price=30, sh=77.036,
   acq=702, g={'bear':0.0,'base':0.02,'bull':0.04}, level={'bear':491/567,'base':1.0,'bull':1.0},
   roiic={'bear':0.0,'base':0.05,'bull':R}, pending=lambda y: [(30, y)]),
 'RBREW.CO': dict(price=435.40, mean=1034, int=198, nci=0, nd=6385, deals_price=0, sh=48.661324,
   acq=889, g={'bear':0.0,'base':0.03,'bull':0.06}, level={'bear':954/1034,'base':1.0,'bull':1.0},
   roiic={'bear':0.04,'base':0.07,'bull':R}, pending=lambda y: []),
}
for t,c in C.items():
    print(f"== {t}  price {c['price']}")
    for case in ('bear','base','bull'):
        core,prog,pend,tot,e0=value(c,case)
        print(f"  {case:4s} core {core:8.2f}  deal programme {prog:7.2f}  pending deals {pend:7.2f}  = {tot:8.2f}   E0 {e0/(1e6 if e0>1e5 else 1):,.0f}")
    e0=(c['mean']+c['int']-c['nci'])
    gs=implied_growth(price=c['price'],fcf0=e0,net_cash=-c['nd'],shares=c['sh'])
    ey=e0/(c['price']*c['sh']+c['nd'])
    print(f"  anchors: g* on organic E0 {gs*100:.2f}%  | owner-earnings yield on EV {ey*100:.2f}% -> expected return ~{(ey+c['g']['base'])*100:.1f}%")
print("\n== base with growth DERIVED (min of 10y organic revenue CAGR and 10y owner-earnings/share CAGR, cap 4%)")
for t,g in (('LIAB.ST',0.017),('RBREW.CO',0.04),('PEP',0.01)):
    c=dict(C[t]); c['g']=dict(C[t]['g']); c['g']['base']=g
    core,prog,pend,tot,e0=value(c,'base'); print(f"  {t:9s} g {g*100:.1f}%  core {core:7.2f} prog {prog:7.2f} pend {pend:6.2f} = {tot:7.2f}")
