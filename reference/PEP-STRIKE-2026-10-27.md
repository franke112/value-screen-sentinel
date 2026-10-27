# PEP -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/PEP.yaml` on the pre-registered growth view 2.00% / 1.00% / 4.00%, carried from PEP-2026-10-19.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 56.82 -> **51.60** (bear 45.89, bull 64.43)
- **FCF0:** 7,799,416,667
- **net debt:** 42,578,000,000 on the balance sheet of 2026-09-05
- **E140 FCF0:** mean of annual FY2023 8,191,000,000; annual FY2024 8,182,000,000; annual FY2025 8,596,000,000 = 8,323,000,000; LESS acquisitions mean 1,320,333,333 (E140.1(1): a repeat buyer); + interest after tax 840,750,000 at 0.25 (US); - minority dividends 44,000,000
- **bridge rolled (E140.1(3)):** 2025-12-27 -> 2026-09-05; year-to-date working capital -3,043,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 42,578,000,000 on the balance sheet + deals 0 + working capital neutralised -3,043,000,000 = 39,535,000,000
- **events ledger** `reference/events/PEP.yaml` dated 2026-10-27, cut at 2026-09-05: no deal in the bridge
- **divisor:** 1,367,000,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 3,846,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 135.46; g* 11.59%
- **store's newest period:** --

```
PEP — strike 2026-10-27   against PEP-2026-10-19.json

                                  before           after     move
fv_base                            56.82           51.60    -9.2%
  bear                             50.66           45.89    -9.4%
  bull                             70.67           64.43    -8.8%
MBP (E90)  tier -- -> --              --              --         
g*                                                11.59%         

WHICH LEG MOVED
  FCF0                        8,461,000,000 -> 7,799,416,667            -7.8%
  net debt                   41,395,000,000 -> 42,578,000,000           +2.9%
  divisor (shares)            1,373,000,000 -> 1,367,000,000            -0.4%
  unchanged: basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-27 -> 2025-12-27
  settled close           2026-10-16 -> 2026-10-26  (135.46)
  store's newest period, today: --
```

Record: `reference/run-records/PEP-2026-10-27.json`
