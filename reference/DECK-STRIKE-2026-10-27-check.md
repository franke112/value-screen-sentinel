# DECK -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/DECK.yaml` on the growth DERIVED from the issuer's history (E144) 2.94% / 2.52% / 8.00%, carried from DECK-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2026
- **fv_base:** 85.05 -> **85.05** (bear 26.83, bull 160.03)
- **FCF0:** 860,201,083
- **net debt:** -1,565,799,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2024 728,388,000; annual FY2025 895,690,000; annual FY2026 1,093,962,000 = 906,013,333; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax -45,812,250 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2026-03-31 -> 2026-06-30; year-to-date working capital -138,667,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -1,565,799,000 on the balance sheet + deals 0 + working capital neutralised -138,667,000 = -1,704,466,000
- **growth (E144):** E144: organic 11.30%/yr over 10 years, last five 16.54% (2017-2026, 10 of them PROXY from deal-free years); owner earnings per share 2.94%/yr; cap 8%; worst 3-year 2.52%, best 5-year 18.51%
- **cycle and level (E143):** CYCLICAL (operating margin fell from 8.6% to -0.1%): owner-earnings margin median 15.4%, last three 20.4%, lowest 3.2% -> base level x0.752, bear x0.156
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 860,201,083 x level 0.156 x (1 + 2.52%) = FCF0 137,261,905; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 56.53% (+0.00/sh) -> **26.83**
- **base:** flow 860,201,083 x level 0.752 x (1 + 2.94%) = FCF0 666,229,199; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC -- (+0.00/sh) -> **85.05**
- **bull:** flow 860,201,083 x level 1.000 x (1 + 8.00%) = FCF0 929,017,170; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **160.03**
- **events ledger** `reference/events/DECK.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 138,559,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 472,334,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 80.37; g* 2.15%
- **store's newest period:** 2026-06-30
- **anchors:** g* 2.15%; the base case returns ~10.0% a year at today's price against r 9.5%; tangible ROIC median 62.2% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 62.2% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 101% below its running peak, regained within three years
  - Q3 debt: **PASS** -- net debt -2.6x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Deckers sells HOKA, UGG and Teva footwear and apparel through retailers and directly to consumers; brand strength brings repeat purchases.

```
DECK — strike 2026-10-27   against DECK-2026-10-27-e142.json

                                  before           after     move
fv_base                            85.05           85.05    +0.0%
  bear                             26.83           26.83    +0.0%
  bull                            160.03          160.03    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 2.15%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-03-31 -> 2026-03-31
  settled close           2026-10-26 -> 2026-10-26  (80.37)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/DECK-2026-10-27-check.json`
