# PEP -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/PEP.yaml` on the pre-registered growth view 2.00% / 1.00% / 4.00%, carried from PEP-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 65.03 -> **65.28** (bear 52.55, bull 84.85)
- **FCF0:** 9,119,750,000
- **net debt:** 42,578,000,000 on the balance sheet of 2026-09-05
- **E140 FCF0:** mean of annual FY2023 8,191,000,000; annual FY2024 8,182,000,000; annual FY2025 8,596,000,000 = 8,323,000,000; acquisitions mean 1,320,333,333 NOT deducted -- valued as the deal programme (E142); + interest after tax 840,750,000 at 0.25 (US); - minority dividends 44,000,000
- **bridge rolled (E140.1(3)):** 2025-12-27 -> 2026-09-05; year-to-date working capital -3,043,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 42,578,000,000 on the balance sheet + deals 0 + working capital neutralised -3,043,000,000 = 39,535,000,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/PEP.yaml; the registered view reference/growth-views/PEP.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.983: the weakest E140 year 8,182,000,000 over the mean 8,323,000,000 (E143(4))
- **deal programme (E142):** repeat buyer, A = 1,320,333,333/yr; ROIIC base 6.53% -- operating profit 9,477,666,667 (2015-2017 mean) -> 12,123,666,667 (2023-2025 mean); organic x1.144 (6 of 8 years at the view's 2.0%); after tax 25.0%: 961,256,554 on capital added 14,724,666,667 = 6.53%; bear 1.08% -- operating profit 10,276,000,000 (2017) -> 11,512,000,000 (2022); organic x1.104 (5 of 5 years at the view's 2.0%); after tax 25.0%: 124,849,250 on acquisitions 11,519,000,000 = 1.08%
- **bear:** flow 9,119,750,000 x level 0.983 x (1 + 1.00%) = FCF0 9,054,904,775; programme -7,703,648,678 (-5.64/sh); deals 0 credited back 0 at ROIIC 1.08% (+0.00/sh); pension deficit after tax (E146) +343,000,000 (+0.25/sh) -> **52.55**
- **base:** flow 9,119,750,000 x level 1.000 x (1 + 2.00%) = FCF0 9,302,145,000; programme -2,854,188,040 (-2.09/sh); deals 0 credited back 0 at ROIIC 6.53% (+0.00/sh); pension deficit after tax (E146) +343,000,000 (+0.25/sh) -> **65.28**
- **bull:** flow 9,119,750,000 x level 1.000 x (1 + 4.00%) = FCF0 9,484,540,000; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh); pension deficit after tax (E146) +343,000,000 (+0.25/sh) -> **84.85**
- **events ledger** `reference/events/PEP.yaml` dated 2026-10-27, cut at 2026-09-05: no deal in the bridge
- **divisor:** 1,367,000,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 3,846,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 135.46; g* 8.61%
- **store's newest period:** --
- **anchors:** g* 8.61%; the base case returns ~6.6% a year at today's price against r 9.5%; tangible ROIC median 28.6% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 28.6% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 11% below its running peak
  - Q3 debt: **PASS** -- net debt 4.3x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **FAIL** -- ROIIC 6.5% against r 9.5%
  - Q5 understandable: **PASS** -- PepsiCo makes and sells snacks and beverages to retailers and consumers worldwide; strong brands and distribution drive repeat buying.

```
PEP — strike 2026-10-27   against PEP-2026-10-27-e142.json

                                  before           after     move
fv_base                            65.03           65.28    +0.4%
  bear                             52.30           52.55    +0.5%
  bull                             84.59           84.85    +0.3%
MBP (E90)  tier -- -> --              --              --         
g*                                                 8.61%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-27 -> 2025-12-27
  settled close           2026-10-26 -> 2026-10-26  (135.46)
  store's newest period, today: --
```

Record: `reference/run-records/PEP-2026-10-27-check.json`
