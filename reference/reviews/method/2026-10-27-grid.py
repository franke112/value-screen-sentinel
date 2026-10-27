from vss.valuation import equity_value_per_share as ev
# name: mean, acq, interest_after_tax, nci, bridge_net_debt, deals_in_bridge, shares, g_base, price
N={
 'LIAB.ST':(567,702,160,0,2959,30,77,0.02,129.50),
 'RBREW.CO':(1034,889,198,0,6385,0,48.661324,0.03,435.40),
 'PEP':(8323e6,1320.333e6,840.75e6,44e6,39535e6,0,1367e6,0.02,135.46),
 'CENTA':(193.349667e6,21.181333e6,24.609e6,1.346e6,986.187e6,840e6,61.947e6,0.02,39.13),
 'ACN':(9549.431e6,4331.614e6,-44.856e6,3.779e6,-667.236e6,500e6,617.498483e6,0.045,247.23),
 'ACAD.ST':(931,643,0,0,2350,640,98.237,0.045,113.0),
}
for t,(m,a,i,n,nd,deals,sh,g,p) in N.items():
    def v(f,d=nd,gg=g,r=0.095): return ev(fcf0=f,growth=gg,net_cash=-d,shares=sh,rate=r)
    cur=v(m-a+i-n); org=v(m+i-n); org_nodeal=v(m+i-n,d=nd-deals)
    print(f"{t:9s} price {p:8.2f} | now {cur:8.2f} | acq not deducted {org:8.2f} | + pending deals out {org_nodeal:8.2f} | FCF0 now {(m-a+i-n)/ (1e6 if m>1e5 else 1):,.0f} vs {(m+i-n)/(1e6 if m>1e5 else 1):,.0f}")
