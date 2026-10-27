# TPR -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/TPR.yaml` on the growth DERIVED from the issuer's history (E144) 3.60% / -1.60% / 4.00% (first strike, from the entry). Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2026
- **fv_base:** -- -> **64.37** (bear 8.33, bull 102.71)
- **FCF0:** 1,352,400,000
- **net debt:** 1,421,900,000 on the balance sheet of 2026-06-27
- **E140 FCF0:** mean of annual FY2024 888,600,000; annual FY2025 1,042,300,000; annual FY2026 1,582,700,000 = 1,171,200,000; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 181,200,000 at 0.25 (US); - minority dividends 0
- **bridge (E140(3), deals at the HIGH end):** net debt 1,421,900,000 on the balance sheet + deals 0 + working capital neutralised 0 = 1,421,900,000
- **growth (E144):** E144: organic 3.60%/yr over 8 years, last five 6.85% (2017-2026, 8 of them PROXY from deal-free years); owner earnings per share 15.46%/yr; cap 4%; worst 3-year -1.60%, best 5-year 7.16%
- **cycle and level (E143):** CYCLICAL (revenue fell -18% in a year; operating margin fell from 17.5% to -11.1%): owner-earnings margin median 12.4%, last three 18.5%, lowest 4.1% -> base level x0.672, bear x0.220
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 1,352,400,000 x level 0.220 x (1 + -1.60%) = FCF0 292,615,701; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 7.39% (+0.00/sh) -> **8.33**
- **base:** flow 1,352,400,000 x level 0.672 x (1 + 3.60%) = FCF0 941,444,629; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 8.59% (+0.00/sh) -> **64.37**
- **bull:** flow 1,352,400,000 x level 1.000 x (1 + 4.00%) = FCF0 1,406,496,000; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **102.71**
- **events ledger** `reference/events/TPR.yaml` dated 2026-10-27, cut at 2026-06-27: no deal in the bridge
- **divisor:** 210,200,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 1,574,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-27:** 111.39; g* 9.65%
- **store's newest period:** --
- **anchors:** g* 9.65%; the base case returns ~6.8% a year at today's price against r 9.5%; tangible ROIC median 34.4% over 11 years (goodwill taken out) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 34.4% over 11 years (goodwill taken out) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 167% below its running peak, regained within three years
  - Q3 debt: **PASS** -- net debt 1.5x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Tapestry sells Coach and kate spade handbags, accessories and clothing to consumers through its own stores, online and wholesale.

```
TPR — strike 2026-10-27   (first strike: no prior record)

                                  before           after     move
fv_base                               --           64.37         
  bear                                --            8.33         
  bull                                --          102.71         
MBP (E90)  tier -- -> --              --              --         
g*                                                 9.65%         

WHICH LEG MOVED
  FCF0                                   -- -> 1,352,400,000                 
  net debt                               -- -> 1,421,900,000                 
  divisor (shares)                       -- -> 210,200,000                   
  basis                                  -- -> annual FY2026                 
  growth view                            -- -> 3.60% / -1.60% / 4.00%           E144: derived from the issuer's history
  discount rate                          -- -> 0                             
  lease treatment                        -- -> RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease paymen        

WHAT THE TWO SIDES STAND ON
  basis window end        -- -> 2026-06-27
  settled close           -- -> 2026-10-27  (111.39)
  store's newest period, today: --
```

Record: `reference/run-records/TPR-2026-10-27.json`
