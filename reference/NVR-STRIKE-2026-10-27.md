# NVR -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/NVR.yaml` on the pre-registered growth view 2.50% / -3.00% / 6.50%, carried from NVR-2026-09-19-e117.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 4,867.82 -> **6,614.83** (bear 4,438.52, bull 8,892.00)
- **FCF0:** 1,267,713,917
- **net debt:** -194,038,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 1,363,520,000; annual FY2024 1,303,391,000; annual FY2025 1,300,951,000 = 1,322,620,667; acquisitions mean 0 NOT deducted (paid in fewer than two of three years); + interest after tax -54,906,750 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital 127,690,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -194,038,000 on the balance sheet + deals 0 + working capital neutralised 127,690,000 = -66,348,000
- **events ledger** `reference/events/NVR.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 2,816,295
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 143,733,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 5,727.77; g* 0.53%
- **store's newest period:** 2026-06-30

```
NVR — strike 2026-10-27   against NVR-2026-09-19-e117.json

                                  before           after     move
fv_base                         4,867.82        6,614.83   +35.9%
  bear                          3,364.36        4,438.52   +31.9%
  bull                          6,440.96        8,892.00   +38.1%
MBP (E90)  tier -- -> --              --              --         
g*                                                 0.53%         

WHICH LEG MOVED
  FCF0                          954,390,000 -> 1,267,713,917           +32.8%
  net debt                     -964,852,000 -> -194,038,000            -79.9%
  divisor (shares)                3,069,103 -> 2,816,295                -8.2%
  unchanged: basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-09-18 -> 2026-10-26  (5,727.77)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/NVR-2026-10-27.json`
