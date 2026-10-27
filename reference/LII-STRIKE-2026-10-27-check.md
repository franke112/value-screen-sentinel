# LII -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/LII.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / -1.82% / 4.00%, carried from LII-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 309.55 -> **309.69** (bear 92.28, bull 309.69)
- **FCF0:** 708,375,000
- **net debt:** 1,549,900,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 426,200,000; annual FY2024 704,500,000; annual FY2025 902,400,000 = 677,700,000; acquisitions mean 213,300,000 NOT deducted -- valued as the deal programme (E142); + interest after tax 30,675,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -269,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 1,549,900,000 on the balance sheet + deals 205,000,000 + working capital neutralised -269,000,000 = 1,485,900,000
- **growth (E144):** E144: organic 4.50%/yr over 7 years, last five 4.21% (2016-2022, 7 of them PROXY from deal-free years); owner earnings per share 14.51%/yr; cap 4%; worst 3-year -1.82%, best 5-year 4.21%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.629: the weakest E140 year 426,200,000 over the mean 677,700,000 (E143(4))
- **deal programme (E142):** repeat buyer, A = 213,300,000/yr; ROIIC base 39.67% -- operating profit 409,766,667 (2015-2017 mean) -> 957,800,000 (2023-2025 mean); organic x1.401 (2 of 8 years at the view's 4.0%); after tax 25.0%: 287,657,724 on capital added 725,200,000 = 39.67%; bear 8.28% -- operating profit 494,500,000 (2017) -> 656,200,000 (2022); organic x1.229; after tax 25.0%: 36,389,869 on capital added 439,500,000 = 8.28%
- **bear:** flow 708,375,000 x level 0.629 x (1 + -1.82%) = FCF0 437,397,351; programme -157,841,748 (-4.54/sh); deals 205,000,000 credited back 178,670,094 at ROIIC 8.28% (+5.13/sh); pension deficit after tax (E146) +5,025,000 (+0.14/sh) -> **92.28**
- **base:** flow 708,375,000 x level 1.000 x (1 + 4.00%) = FCF0 736,710,000; programme 0 (+0.00/sh); deals 205,000,000 credited back 205,000,000 at ROIIC 39.67% (+5.89/sh); pension deficit after tax (E146) +5,025,000 (+0.14/sh) -> **309.69**
- **bull:** flow 708,375,000 x level 1.000 x (1 + 4.00%) = FCF0 736,710,000; programme 0 (+0.00/sh); deals 205,000,000 credited back 205,000,000 at ROIIC 9.50% (+5.89/sh); pension deficit after tax (E146) +5,025,000 (+0.14/sh) -> **309.69**
- **events ledger** `reference/events/LII.yaml` dated 2026-10-27, cut at 2026-06-30: Heat Controller 205,000,000..205,000,000
- **divisor:** 34,800,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 443,400,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 365.64; g* 5.79%
- **store's newest period:** --
- **anchors:** g* 5.79%; the base case returns ~8.5% a year at today's price against r 9.5%; tangible ROIC median 712.5% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 712.5% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 27% below its running peak
  - Q3 debt: **PASS** -- net debt 2.0x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- ROIIC 39.7% against r 9.5%
  - Q5 understandable: **PASS** -- Lennox makes heating, cooling and refrigeration equipment sold through dealers and distributors to homes and buildings; installer relationships and replacement demand recur.

```
LII — strike 2026-10-27   against LII-2026-10-27-e142.json

                                               before           after     move
fv_base                                        309.55          309.69    +0.0%
  bear                                          92.14           92.28    +0.2%
  bull                                         309.55          309.69    +0.0%
MBP (E90)  tier -- -> --                           --              --         
g*                                                              5.79%         
  fv_base, deals at LOW end (E140(3))                          309.69         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (365.64)
  store's newest period, today: --
```

Record: `reference/run-records/LII-2026-10-27-check.json`
