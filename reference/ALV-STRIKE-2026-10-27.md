# ALV -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/ALV.yaml` on the pre-registered growth view 3.00% / 1.00% / 5.00%, carried from ALV-2026-10-20.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 134.34 -> **85.89** (bear 70.79, bull 103.51)
- **FCF0:** 529,083,333
- **net debt:** 1,912,000,000 on the balance sheet of 2026-09-30
- **E140 FCF0:** mean of annual FY2023 209,000,000; annual FY2024 422,000,000; annual FY2025 750,000,000 = 460,333,333; acquisitions mean 0 NOT deducted (paid in fewer than two of three years); + interest after tax 69,750,000 at 0.25 (US); - minority dividends 1,000,000
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-09-30; year-to-date working capital -135,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 1,912,000,000 on the balance sheet + deals 0 + working capital neutralised -135,000,000 = 1,777,000,000
- **events ledger** `reference/events/ALV.yaml` dated 2026-10-27, cut at 2026-09-30: no deal in the bridge
- **divisor:** 72,900,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 154,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 115.32; g* 6.19%
- **store's newest period:** --

```
ALV — strike 2026-10-27   against ALV-2026-10-20.json

                                  before           after     move
fv_base                           134.34           85.89   -36.1%
  bear                            112.88           70.79   -37.3%
  bull                            159.37          103.51   -35.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 6.19%         

WHICH LEG MOVED
  FCF0                          793,000,000 -> 529,083,333             -33.3%
  net debt                    1,718,000,000 -> 1,912,000,000           +11.3%
  divisor (shares)               76,900,000 -> 72,900,000               -5.2%
  unchanged: basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-19 -> 2026-10-26  (115.32)
  store's newest period, today: --
```

Record: `reference/run-records/ALV-2026-10-27.json`
