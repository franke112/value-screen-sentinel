# LIAB.ST -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/LIAB.ST.yaml` on the growth DERIVED from the issuer's history (E144) 1.33% / -3.00% / 4.00%, carried from LIAB.ST-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2
- **fv_base:** 65.93 -> **66.68** (bear -5.29, bull 123.14)
- **FCF0:** 726
- **net debt:** 3,126 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 637; annual FY2024 491; annual FY2025 572 = 567; acquisitions mean 702 NOT deducted -- valued as the deal programme (E142); + interest after tax 160 at 0.206 (SE); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -197 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 3,126 on the balance sheet + deals 30 + working capital neutralised -197 = 2,959
- **growth (E144):** E144: organic 1.91%/yr over 10 years, last five 1.33% (2016-2025); owner earnings per share 17.66%/yr; cap 4%; worst 3-year -6.03%, best 5-year 6.12%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.866: the weakest E140 year 491 over the mean 567 (E143(4))
- **deal programme (E142):** repeat buyer, A = 702/yr; ROIIC base 5.73% -- adjusted operating profit 552,000,000 (2016-2018 mean) -> 1,083,000,000 (2023-2025 mean); organic x1.163; after tax 20.6%: 349,993,844 on capital added 6,108,666,667 = 5.73%; bear 0.82% -- adjusted operating profit 916,000,000 (2020) -> 1,027,000,000 (2025); organic x1.068; after tax 20.6%: 38,599,477 on capital added 4,695,000,000 = 0.82%
- **bear:** flow 726 x level 0.866 x (1 + -3.00%) = FCF0 610; programme -3,495 (-45.37/sh); deals 30 credited back 3 at ROIIC 0.82% (+0.03/sh); pension deficit after tax (E146) +58 (+0.75/sh) -> **-5.29**
- **base:** flow 726 x level 1.000 x (1 + 1.33%) = FCF0 736; programme -1,864 (-24.20/sh); deals 30 credited back 18 at ROIIC 5.73% (+0.23/sh); pension deficit after tax (E146) +58 (+0.75/sh) -> **66.68**
- **bull:** flow 726 x level 1.000 x (1 + 4.00%) = FCF0 755; programme 0 (+0.00/sh); deals 30 credited back 30 at ROIIC 9.50% (+0.39/sh); pension deficit after tax (E146) +58 (+0.75/sh) -> **123.14**
- **events ledger** `reference/events/LIAB.ST.yaml` dated 2026-10-27, cut at 2026-06-30: Connaught Ventilation Supplies (IE, sales ~EUR 2m; price NOT DISCLOSED, range estimate) 10..30; already in the balance sheet: Lindab SRL Romania divested (SEK 42m, instalments over 3 years)
- **divisor:** 77
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 452 is DEDUCTED -- principal 386 + lease interest 66; the lease liability 1,410 LEFT net debt
- **MBP (E90, tier 2):** 49.45 -> 50.01
- **close 2026-10-26:** 129.50; g* 6.52%
- **store's newest period:** 2026-06-30
- **anchors:** g* 6.52%; the base case returns ~7.4% a year at today's price against r 9.5%; tangible ROIC median 8.5% over 10 years (no goodwill row: on all invested capital) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **FAIL** -- median 8.5% over 10 years (no goodwill row: on all invested capital) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; adjusted operating profit at most 24% below its running peak
  - Q3 debt: **FAIL** -- net debt 4.0x FCF0 against 3.0x
  - Q4 capital allocation: **FAIL** -- ROIIC 5.7% against r 9.5%
  - Q5 understandable: **PASS** -- Lindab makes and distributes ventilation and indoor-climate products, sold mainly to installers in Europe.

```
LIAB.ST — strike 2026-10-27   against LIAB.ST-2026-10-27-e142.json

                                               before           after     move
fv_base                                         65.93           66.68    +1.1%
  bear                                          -6.03           -5.29   -12.4%
  bull                                         122.39          123.14    +0.6%
MBP (E90)  tier 2 -> 2                          49.45           50.01    +1.1%
g*                                                              6.52%         
  fv_base, deals at LOW end (E140(3))                           66.78         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-06-30 -> 2026-06-30
  settled close           2026-10-26 -> 2026-10-26  (129.50)
  store's newest period, today: 2026-06-30
```

Record: `reference/run-records/LIAB.ST-2026-10-27-check.json`
