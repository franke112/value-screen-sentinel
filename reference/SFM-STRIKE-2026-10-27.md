# SFM -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/SFM.yaml` on the growth DERIVED from the issuer's history (E144) 8.00% / 4.44% / 8.00% (first strike, from the entry). Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** -- -> **78.47** (bear 38.47, bull 78.47)
- **FCF0:** 305,291,500
- **net debt:** -110,104,000 on the balance sheet of 2026-06-28
- **E140 FCF0:** mean of annual FY2023 198,891,000; annual FY2024 297,397,000; annual FY2025 425,495,000 = 307,261,000; acquisitions mean 4,344,000 NOT deducted -- valued as the deal programme (E142); + interest after tax -1,969,500 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-28 -> 2026-06-28; year-to-date working capital -33,718,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -110,104,000 on the balance sheet + deals 0 + working capital neutralised -33,718,000 = -143,822,000
- **growth (E144):** E144: organic 12.68%/yr over 8 years, last five 8.06% (2014-2025, 8 of them PROXY from deal-free years); owner earnings per share 22.17%/yr; cap 8%; worst 3-year 4.44%, best 5-year 12.48%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.647: the weakest E140 year 198,891,000 over the mean 307,261,000 (E143(4))
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 305,291,500 x level 0.647 x (1 + 4.44%) = FCF0 206,384,689; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **38.47**
- **base:** flow 305,291,500 x level 1.000 x (1 + 8.00%) = FCF0 329,714,820; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 8.18% (+0.00/sh) -> **78.47**
- **bull:** flow 305,291,500 x level 1.000 x (1 + 8.00%) = FCF0 329,714,820; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **78.47**
- **events ledger** `reference/events/SFM.yaml` dated 2026-10-27, cut at 2026-06-28: no deal in the bridge
- **divisor:** 94,410,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 1,992,469,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-27:** 64.41; g* 5.59%
- **store's newest period:** --
- **anchors:** g* 5.59%; the base case returns ~10.9% a year at today's price against r 9.5%; tangible ROIC median 38.1% over 11 years (goodwill taken out) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 38.1% over 11 years (goodwill taken out) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 15% below its running peak
  - Q3 debt: **PASS** -- net debt -0.4x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Sprouts runs specialty grocery stores selling fresh, natural and organic food to US shoppers.

```
SFM — strike 2026-10-27   (first strike: no prior record)

                                  before           after     move
fv_base                               --           78.47         
  bear                                --           38.47         
  bull                                --           78.47         
MBP (E90)  tier -- -> --              --              --         
g*                                                 5.59%         

WHICH LEG MOVED
  FCF0                                   -- -> 305,291,500                   
  net debt                               -- -> -110,104,000                  
  divisor (shares)                       -- -> 94,410,000                    
  basis                                  -- -> annual FY2025                 
  growth view                            -- -> 8.00% / 4.44% / 8.00%            E144: derived from the issuer's history
  discount rate                          -- -> 0                             
  lease treatment                        -- -> RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease paymen        

WHAT THE TWO SIDES STAND ON
  basis window end        -- -> 2025-12-28
  settled close           -- -> 2026-10-27  (64.41)
  store's newest period, today: --
```

Record: `reference/run-records/SFM-2026-10-27.json`
