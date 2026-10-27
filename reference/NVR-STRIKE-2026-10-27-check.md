# NVR -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/NVR.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / -0.65% / 4.00%, carried from NVR-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 7,682.75 -> **7,682.75** (bear 5,138.49, bull 7,682.75)
- **FCF0:** 1,267,713,917
- **net debt:** -194,038,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 1,363,520,000; annual FY2024 1,303,391,000; annual FY2025 1,300,951,000 = 1,322,620,667; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax -54,906,750 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital 127,690,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -194,038,000 on the balance sheet + deals 0 + working capital neutralised 127,690,000 = -66,348,000
- **growth (E144):** E144: organic 7.18%/yr over 10 years, last five 6.50% (2016-2025, 10 of them PROXY from deal-free years); owner earnings per share 20.44%/yr; cap 4%; worst 3-year -0.65%, best 5-year 10.79%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.984: the weakest E140 year 1,300,951,000 over the mean 1,322,620,667 (E143(4))
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 1,267,713,917 x level 0.984 x (1 + -0.65%) = FCF0 1,238,897,070; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -- (+0.00/sh) -> **5,138.49**
- **base:** flow 1,267,713,917 x level 1.000 x (1 + 4.00%) = FCF0 1,318,422,473; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -- (+0.00/sh) -> **7,682.75**
- **bull:** flow 1,267,713,917 x level 1.000 x (1 + 4.00%) = FCF0 1,318,422,473; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **7,682.75**
- **events ledger** `reference/events/NVR.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 2,816,295
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 143,733,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 5,727.77; g* 0.47%
- **store's newest period:** 2026-06-30
- **anchors:** g* 0.47%; the base case returns ~11.8% a year at today's price against r 9.5%; tangible ROIC median 67.7% over 6 years (no goodwill row: on all invested capital) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 67.7% over 6 years (no goodwill row: on all invested capital) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 15% below its running peak
  - Q3 debt: **PASS** -- net debt -0.1x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- NVR builds and sells single-family homes, townhomes and condos to homebuyers, mostly pre-sold, with mortgage and title services.

```
NVR — strike 2026-10-27   against NVR-2026-10-27-e142.json

                                  before           after     move
fv_base                         7,682.75        7,682.75    +0.0%
  bear                          5,138.49        5,138.49    +0.0%
  bull                          7,682.75        7,682.75    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 0.47%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (5,727.77)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/NVR-2026-10-27-check.json`
