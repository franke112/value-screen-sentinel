# ZTS -- struck 2026-10-29

*Struck by `vss strike` off `config/manual/ZTS.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / 4.00% / 4.00% (first strike, from the entry). Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** -- -> **79.80** (bear 69.62, bull 79.80)
- **FCF0:** 2,375,416,667
- **net debt:** 7,646,000,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 2,039,000,000; annual FY2024 2,128,000,000; annual FY2025 2,669,000,000 = 2,278,666,667; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 96,750,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -550,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 7,646,000,000 on the balance sheet + deals 460,000,000 + working capital neutralised -550,000,000 = 7,556,000,000
- **growth (E144):** E144: organic 7.14%/yr over 6 years, last five 7.24% (2020-2025, 6 of them PROXY from deal-free years); owner earnings per share 16.11%/yr; cap 4%; worst 3-year 5.42%, best 5-year 8.14%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.895: the weakest E140 year 2,039,000,000 over the mean 2,278,666,667 (E143(4))
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 2,375,416,667 x level 0.895 x (1 + 4.00%) = FCF0 2,210,596,943; programme 0 (+0.00/sh); deals 460,000,000 credited back 460,000,000 at ROIIC 191.70% (+1.10/sh); pension deficit after tax (E146) +10,500,000 (+0.03/sh) -> **69.62**
- **base:** flow 2,375,416,667 x level 1.000 x (1 + 4.00%) = FCF0 2,470,433,333; programme 0 (+0.00/sh); deals 460,000,000 credited back 460,000,000 at ROIIC 191.70% (+1.10/sh); pension deficit after tax (E146) +10,500,000 (+0.03/sh) -> **79.80**
- **bull:** flow 2,375,416,667 x level 1.000 x (1 + 4.00%) = FCF0 2,470,433,333; programme 0 (+0.00/sh); deals 460,000,000 credited back 460,000,000 at ROIIC 9.50% (+1.10/sh); pension deficit after tax (E146) +10,500,000 (+0.03/sh) -> **79.80**
- **events ledger** `reference/events/ZTS.yaml` dated 2026-10-29, cut at 2026-06-30: Neogen animal genomics business (GeneSeek) 160,000,000..160,000,000; VitalRADS (veterinary teleradiology, from Thrive Pet Healthcare) 50,000,000..300,000,000
- **divisor:** 417,700,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 248,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-29:** 78.80; g* 3.88%
- **store's newest period:** --
- **anchors:** g* 3.88%; the base case returns ~9.6% a year at today's price against r 9.5%; tangible ROIC median 27.9% over 3 years (goodwill taken out) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 27.9% over 3 years (goodwill taken out) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 0% below its running peak
  - Q3 debt: **PASS** -- net debt 3.1x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Zoetis makes and sells medicines, vaccines and diagnostics for pets and livestock worldwide; companion animal is about 70% of revenue (6,587 of 9,467 $m in 2025).

```
ZTS — strike 2026-10-29   (first strike: no prior record)

                                               before           after     move
fv_base                                            --           79.80         
  bear                                             --           69.62         
  bull                                             --           79.80         
MBP (E90)  tier -- -> --                           --              --         
g*                                                              3.88%         
  fv_base, deals at LOW end (E140(3))                           79.80         

WHICH LEG MOVED
  FCF0                                   -- -> 2,375,416,667                 
  net debt                               -- -> 7,646,000,000                 
  divisor (shares)                       -- -> 417,700,000                   
  basis                                  -- -> annual FY2025                 
  growth view                            -- -> 4.00% / 4.00% / 4.00%            E144: derived from the issuer's history
  discount rate                          -- -> 0                             
  lease treatment                        -- -> RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease paymen        

WHAT THE TWO SIDES STAND ON
  basis window end        -- -> 2025-12-31
  settled close           -- -> 2026-10-29  (78.80)
  store's newest period, today: --
```

Record: `reference/run-records/ZTS-2026-10-29.json`
