# AOS -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/AOS.yaml` on the pre-registered growth view 4.00% / 0.00% / 7.00%, carried from AOS-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 64.35 -> **64.37** (bear 38.29, bull 85.58)
- **FCF0:** 555,858,333
- **net debt:** 463,600,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 570,300,000; annual FY2024 482,100,000; annual FY2025 584,800,000 = 545,733,333; acquisitions mean 54,233,333 NOT deducted -- valued as the deal programme (E142); + interest after tax 10,125,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -97,100,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 463,600,000 on the balance sheet + deals 0 + working capital neutralised -97,100,000 = 366,500,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/AOS.yaml; the registered view reference/growth-views/AOS.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.883: the weakest E140 year 482,100,000 over the mean 545,733,333 (E143(4))
- **deal programme (E142):** repeat buyer, A = 54,233,333/yr; ROIIC base 4.45% -- operating profit 515,266,667 (2015-2017 mean) -> 727,266,667 (2023-2025 mean); organic x1.351 (7 of 8 years at the view's 4.0%); after tax 25.0%: 23,510,154 on acquisitions 528,400,000 = 4.45%; bear 0.00% -- operating profit 577,900,000 (2017) -> 362,000,000 (2022); organic x1.217 (5 of 5 years at the view's 4.0%); after tax 25.0%: -255,827,784 on acquisitions 322,600,000 = -79.30%
- **bear:** flow 555,858,333 x level 0.883 x (1 + 0.00%) = FCF0 491,044,410; programme -340,520,147 (-2.47/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh); pension deficit after tax (E146) +1,850,000 (+0.01/sh) -> **38.29**
- **base:** flow 555,858,333 x level 1.000 x (1 + 4.00%) = FCF0 578,092,667; programme -219,556,421 (-1.59/sh); deals 0 credited back 0 at ROIIC 4.45% (+0.00/sh); pension deficit after tax (E146) +1,850,000 (+0.01/sh) -> **64.37**
- **bull:** flow 555,858,333 x level 1.000 x (1 + 7.00%) = FCF0 594,768,417; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh); pension deficit after tax (E146) +1,850,000 (+0.01/sh) -> **85.58**
- **events ledger** `reference/events/AOS.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge; already in the balance sheet: Leonard Valve
- **divisor:** 137,862,584
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 47,900,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 61.91; g* 3.56%
- **store's newest period:** --
- **anchors:** g* 3.56%; the base case returns ~9.8% a year at today's price against r 9.5%; tangible ROIC median 39.5% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 39.5% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 47% below its running peak
  - Q3 debt: **PASS** -- net debt 0.6x FCF0 against 3.0x
  - Q4 capital allocation: **FAIL** -- ROIIC 4.4% against r 9.5%
  - Q5 understandable: **PASS** -- A. O. Smith makes water heaters, boilers and water treatment products for homes and businesses; replacement need and installer loyalty bring repeat sales.

```
AOS — strike 2026-10-27   against AOS-2026-10-27-e142.json

                                  before           after     move
fv_base                            64.35           64.37    +0.0%
  bear                             38.28           38.29    +0.0%
  bull                             85.57           85.58    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 3.56%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (61.91)
  store's newest period, today: --
```

Record: `reference/run-records/AOS-2026-10-27-check.json`
