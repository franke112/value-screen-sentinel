# LIAB.ST -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/LIAB.ST.yaml` on the pre-registered growth view 2.00% / 0.00% / 4.00%, carried from LIAB.ST-2026-09-19-e117.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2
- **fv_base:** 68.97 -> **-33.97** (bear -34.57, bull -33.26)
- **FCF0:** 24
- **net debt:** 3,126 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 637; annual FY2024 491; annual FY2025 572 = 567; LESS acquisitions mean 702 (E140.1(1): a repeat buyer); + interest after tax 160 at 0.206 (SE); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -197 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 3,126 on the balance sheet + deals 30 + working capital neutralised -197 = 2,959
- **events ledger** `reference/events/LIAB.ST.yaml` dated 2026-10-27, cut at 2026-06-30: Connaught Ventilation Supplies (IE, sales ~EUR 2m; price NOT DISCLOSED, range estimate) 10..30; already in the balance sheet: Lindab SRL Romania divested (SEK 42m, instalments over 3 years)
- **divisor:** 77
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 452 is DEDUCTED -- principal 386 + lease interest 66; the lease liability 1,410 LEFT net debt
- **MBP (E90, tier 2):** 51.73 -> -25.47
- **close 2026-10-26:** 129.50; g* 53.66%
- **store's newest period:** 2026-06-30

```
LIAB.ST — strike 2026-10-27   against LIAB.ST-2026-09-19-e117.json

                                               before           after     move
fv_base                                         68.97          -33.97  -149.2%
  bear                                          54.03          -34.57  -164.0%
  bull                                          86.42          -33.26  -138.5%
MBP (E90)  tier 2 -> 2                          51.73          -25.47  -149.2%
g*                                                             53.66%         
  fv_base, deals at LOW end (E140(3))                          -33.71         

WHICH LEG MOVED
  FCF0                          598,000,000 -> 24,260,667              -95.9%
  unchanged: net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-06-30 -> 2026-06-30
  settled close           2026-09-16 -> 2026-10-26  (129.50)
  store's newest period, today: 2026-06-30
```

Record: `reference/run-records/LIAB.ST-2026-10-27.json`
