# ALV -- struck 2026-10-20

*Struck by `vss strike` off `config/manual/ALV.yaml` on the pre-registered growth view 3.00% / 1.00% / 5.00% (first strike, from the entry). Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** -- -> **134.34** (bear 112.88, bull 159.37)
- **FCF0:** 793,000,000
- **net debt:** 1,718,000,000
- **divisor:** 76,900,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 165,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-19:** 116.49; g* 1.36%
- **store's newest period:** --

```
ALV — strike 2026-10-20   (first strike: no prior record)

                                  before           after     move
fv_base                               --          134.34         
  bear                                --          112.88         
  bull                                --          159.37         
MBP (E90)  tier -- -> --              --              --         
g*                                                 1.36%         

WHICH LEG MOVED
  FCF0                                   -- -> 793,000,000                   
  net debt                               -- -> 1,718,000,000                 
  divisor (shares)                       -- -> 76,900,000                    
  basis                                  -- -> annual FY2025                 
  growth view                            -- -> 3.00% / 1.00% / 5.00%            E28: the view is the prior record's, unchanged by a strike
  discount rate                          -- -> 0                             
  lease treatment                        -- -> RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease paymen        

WHAT THE TWO SIDES STAND ON
  basis window end        -- -> 2025-12-31
  settled close           -- -> 2026-10-19  (116.49)
  store's newest period, today: --
```

Record: `reference/run-records/ALV-2026-10-20.json`
