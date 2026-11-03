# DHI -- struck 2026-10-28

*Struck by `vss strike` off `config/manual/DHI.yaml` on the growth DERIVED from the issuer's history (E144) 4.00% / 0.76% / 4.00% (first strike, from the entry). Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** -- -> **184.54** (bear 85.96, bull 184.54)
- **FCF0:** 3,375,016,667
- **net debt:** 5,033,900,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 4,122,300,000; annual FY2024 2,218,200,000; annual FY2025 3,317,000,000 = 3,219,166,667; acquisitions mean 102,133,333 NOT deducted -- valued as the deal programme (E142); + interest after tax 155,850,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-09-30 -> 2026-06-30; year-to-date working capital 169,100,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 5,033,900,000 on the balance sheet + deals 0 + working capital neutralised 169,100,000 = 5,203,000,000
- **growth (E144):** E144: organic 12.15%/yr over 8 years, last five 11.02% (2016-2025, 8 of them PROXY from deal-free years); owner earnings per share 27.64%/yr; cap 4%; worst 3-year 0.76%, best 5-year 19.60%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.689: the weakest E140 year 2,218,200,000 over the mean 3,219,166,667 (E143(4))
- **deal programme (E142):** repeat buyer, A = 102,133,333/yr; ROIIC base 11.52% -- operating profit 1,359,666,667 (2015-2017 mean) -> 5,779,766,667 (2023-2025 mean); organic x2.590 (2 of 8 years at the view's 4.0%); after tax 25.0%: 1,693,557,389 on capital added 14,694,966,667 = 11.52%; bear 0.00% -- operating profit 2,983,000,000 (2020) -> 4,739,900,000 (2025); organic x1.686; after tax 25.0%: -217,726,772 on capital added 12,383,500,000 = -1.76%
- **bear:** flow 3,375,016,667 x level 0.689 x (1 + 0.76%) = FCF0 2,343,292,811; programme -665,004,363 (-2.35/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **85.96**
- **base:** flow 3,375,016,667 x level 1.000 x (1 + 4.00%) = FCF0 3,510,017,333; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 11.52% (+0.00/sh) -> **184.54**
- **bull:** flow 3,375,016,667 x level 1.000 x (1 + 4.00%) = FCF0 3,510,017,333; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **184.54**
- **events ledger** `reference/events/DHI.yaml` dated 2026-10-28, cut at 2026-06-30: no deal in the bridge; already in the balance sheet: SK Builders (homebuilding operations, Greenville SC)
- **divisor:** 283,000,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 71,300,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-27:** 147.02; g* 1.55%
- **store's newest period:** --
- **anchors:** g* 1.55%; the base case returns ~11.0% a year at today's price against r 9.5%; tangible ROIC median 22.8% over 9 years (goodwill taken out) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 22.8% over 9 years (goodwill taken out) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 38% below its running peak
  - Q3 debt: **PASS** -- net debt 1.5x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- ROIIC 11.5% against r 9.5%
  - Q5 understandable: **PASS** -- D.R. Horton builds and sells homes across the US, mostly entry-level, and develops lots (Forestar, 62% owned), with mortgage, title and rental operations.

```
DHI — strike 2026-10-28   (first strike: no prior record)

                                  before           after     move
fv_base                               --          184.54         
  bear                                --           85.96         
  bull                                --          184.54         
MBP (E90)  tier -- -> --              --              --         
g*                                                 1.55%         

WHICH LEG MOVED
  FCF0                                   -- -> 3,375,016,667                 
  net debt                               -- -> 5,033,900,000                 
  divisor (shares)                       -- -> 283,000,000                   
  basis                                  -- -> annual FY2025                 
  growth view                            -- -> 4.00% / 0.76% / 4.00%            E144: derived from the issuer's history
  discount rate                          -- -> 0                             
  lease treatment                        -- -> RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease paymen        

WHAT THE TWO SIDES STAND ON
  basis window end        -- -> 2025-09-30
  settled close           -- -> 2026-10-27  (147.02)
  store's newest period, today: --
```

Record: `reference/run-records/DHI-2026-10-28.json`
