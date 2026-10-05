"""E34 lease prep, 2026-09-19: fair value per name under option A (E70 as
struck) and option B (rent an operating cost, the lease liability out of net
debt), off each latest run record. Reads only; writes nothing.

    PYTHONPATH=. .venv/bin/python tools/e34_lease_options_2026_09_19.py
"""
import json, re, yaml
from pathlib import Path
from vss.runrecord import RunRecord
from vss.valuation import equity_value_per_share
wl = yaml.safe_load(open('config/watchlist.yaml'))
items = wl if isinstance(wl, list) else next(v for v in wl.values() if isinstance(v, list))
status = {e['ticker']: e.get('status') for e in items}
wl_fv = {e['ticker']: e.get('fv_base') for e in items}
wl_mbp = {e['ticker']: e.get('mbp') for e in items}
# IFRS lease principal paid on each record's basis, from the stores (sign dropped)
IFRS_L = {'BOUV.OL': (15058+15613+17231+17187, 'TTM 2025-Q3..2026-Q2, four stated quarters'),
          'PNDORA.CO': (324+300+364+345, 'TTM 2025-Q3..2026-Q2, four stated quarters'),
          'AUTO.L': (1.8, 'FY2026 as stated, VERIFIED cross-document (one long property lease)'),
          'RMV.L': (3146, 'FY2025 as stated'),
          'MEKKO.HE': (8.7, 'FY2025 as stated'),
          'SAP.DE': (299e6, 'FY2025 annual, used for a TTM basis -- PROXY')}
recs = {}
for p in sorted(Path('reference/run-records').glob('*.json')):
    t = re.match(r'(.+?)-2026', p.name).group(1)
    d = json.loads(p.read_text())
    if t not in recs or d['run_ts'] > recs[t][1]['run_ts']:
        recs[t] = (p, d)
rows = []
for t, (p, d) in sorted(recs.items()):
    r = RunRecord.from_dict(d)
    try:
        F = r.fcf0(); A = r.strike()
    except Exception as e:
        rows.append((t, status.get(t), 'REFUSES', str(e)[:70])); continue
    g, rate = d['growth']['base'], d['rate']['rate']
    c = d['conventions']
    M = equity_value_per_share(fcf0=1, growth=g, net_cash=0, shares=1, rate=rate,
                               terminal=c['terminal_growth'], years=c['horizon_years'])
    NC = -d['bridge']['net_debt']
    S = (M*F + NC)/A
    LL = d['bridge']['items'].get('leases') or 0
    lease = d.get('lease') or {}
    if lease.get('in_operating_cash_flow'):
        L, src = lease['principal_added_back'], 'US: E70 add-back (whole payment)'
    elif t in IFRS_L:
        L, src = IFRS_L[t]
    else:
        rows.append((t, status.get(t), f'A={A:.2f}', 'IFRS: lease principal NOT ON FILE')); continue
    B = (M*(F-L) + NC + LL)/S
    rows.append((t, status.get(t), A, B, LL/L if L else None, M, L*M/S, LL/S, src))
for row in rows:
    if isinstance(row[2], float):
        t, st, A, B, yrs, M, add, liab, src = row
        print(f"{t:10} {st or '-':12} A={A:9.2f} B={B:9.2f} ({(B/A-1)*100:+6.1f}%)  liab={yrs:5.1f}y  M={M:5.2f}  addback={add:7.2f}/sh liab={liab:6.2f}/sh  [{src}]")
    else:
        print(f"{row[0]:10} {row[1] or '-':12} {row[2]} {row[3]}")
