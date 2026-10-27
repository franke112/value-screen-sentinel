# ALV -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/ALV.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / -1.70% / 4.00%, carried from ALV-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 68.15 -> **71.74** (bear -18.41, bull 99.72)
- **FCF0:** 529,083,333
- **net debt:** 1,912,000,000 on the balance sheet of 2026-09-30
- **E140 FCF0:** mean of annual FY2023 209,000,000; annual FY2024 422,000,000; annual FY2025 750,000,000 = 460,333,333; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 69,750,000 at 0.25 (US); - minority dividends 1,000,000
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-09-30; year-to-date working capital -135,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 1,912,000,000 on the balance sheet + deals 0 + working capital neutralised -135,000,000 = 1,777,000,000
- **growth (E144):** E144: organic 4.58%/yr over 8 years, last five 8.55% (2018-2025, 1 of them PROXY from deal-free years); owner earnings per share 7.37%/yr; cap 4%; worst 3-year -1.70%, best 5-year 8.55%
- **cycle and level (E143):** CYCLICAL (revenue fell -14% in a year; operating margin fell from 10.6% to 5.1%): owner-earnings margin median 3.9%, last three 5.0%, lowest 0.4% -> base level x0.773, bear x0.070
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 529,083,333 x level 0.070 x (1 + -1.70%) = FCF0 36,326,209; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh); pension deficit after tax (E146) +43,750,000 (+0.60/sh) -> **-18.41**
- **base:** flow 529,083,333 x level 0.773 x (1 + 4.00%) = FCF0 425,583,249; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -64.52% (+0.00/sh); pension deficit after tax (E146) +43,750,000 (+0.60/sh) -> **71.74**
- **bull:** flow 529,083,333 x level 1.000 x (1 + 4.00%) = FCF0 550,246,667; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh); pension deficit after tax (E146) +43,750,000 (+0.60/sh) -> **99.72**
- **events ledger** `reference/events/ALV.yaml` dated 2026-10-27, cut at 2026-09-30: no deal in the bridge
- **divisor:** 72,900,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 154,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 115.32; g* 8.48%
- **store's newest period:** --
- **anchors:** g* 8.48%; the base case returns ~7.4% a year at today's price against r 9.5%; tangible ROIC median 22.2% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 22.2% over 11 years against 15%
  - Q2 stability: **FAIL** -- owner earnings negative in no year; operating profit at most 56% below its running peak, not regained within three years after [2020]
  - Q3 debt: **FAIL** -- net debt 4.2x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Autoliv makes airbags, steering wheels and seatbelts for car makers, who keep buying because safety systems are designed in for each vehicle platform.

```
ALV — strike 2026-10-27   against ALV-2026-10-27-e142.json

                                  before           after     move
fv_base                            68.15           71.74    +5.3%
  bear                            -19.01          -18.41    -3.2%
  bull                             99.12           99.72    +0.6%
MBP (E90)  tier -- -> --              --              --         
g*                                                 8.48%         

WHICH LEG MOVED
  growth view        3.62% / -2.91% / 4.00% -> 4.00% / -1.70% / 4.00%           E144: derived from the issuer's history
  unchanged: FCF0, net debt, divisor (shares), basis, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-26  (115.32)
  store's newest period, today: --
```

Record: `reference/run-records/ALV-2026-10-27-check.json`
