# LOPE -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/LOPE.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / -2.14% / 4.00%, carried from LOPE-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 136.56 -> **136.56** (bear 4.96, bull 146.29)
- **FCF0:** 217,789,000
- **net debt:** -171,060,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 194,041,000; annual FY2024 227,536,000; annual FY2025 231,790,000 = 217,789,000; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 0 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital 40,997,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -171,060,000 on the balance sheet + deals 0 + working capital neutralised 40,997,000 = -130,063,000
- **growth (E144):** E144: organic 4.51%/yr over 8 years, last five 5.55% (2016-2025, 8 of them PROXY from deal-free years); owner earnings per share 22.09%/yr; cap 4%; worst 3-year -2.14%, best 5-year 5.55%
- **cycle and level (E143):** CYCLICAL (revenue fell -13% in a year): owner-earnings margin median 20.7%, last three 22.3%, lowest -2.5% -> base level x0.931, bear x0.000
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 217,789,000 x level 0.000 x (1 + -2.14%) = FCF0 0; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **4.96**
- **base:** flow 217,789,000 x level 0.931 x (1 + 4.00%) = FCF0 210,913,830; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -10.06% (+0.00/sh) -> **136.56**
- **bull:** flow 217,789,000 x level 1.000 x (1 + 4.00%) = FCF0 226,500,560; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **146.29**
- **events ledger** `reference/events/LOPE.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 26,221,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 104,212,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 160.71; g* 6.01%
- **store's newest period:** --
- **anchors:** g* 6.01%; the base case returns ~8.4% a year at today's price against r 9.5%; tangible ROIC median 27.0% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 27.0% over 11 years against 15%
  - Q2 stability: **FAIL** -- owner earnings negative in [2015]; operating profit at most 16% below its running peak
  - Q3 debt: **PASS** -- net debt -0.6x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Grand Canyon Education provides services to universities, chiefly Grand Canyon University, for a share of revenue; long-term contracts keep the partnership.

```
LOPE — strike 2026-10-27   against LOPE-2026-10-27-e142.json

                                  before           after     move
fv_base                           136.56          136.56    +0.0%
  bear                              4.96            4.96    +0.0%
  bull                            146.29          146.29    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 6.01%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (160.71)
  store's newest period, today: --
```

Record: `reference/run-records/LOPE-2026-10-27-check.json`
