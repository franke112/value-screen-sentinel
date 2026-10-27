# RMV.L -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/RMV.L.yaml` on the pre-registered growth view 3.00% / 0.00% / 6.00%, carried from RMV.L-2026-09-19-e117.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** 2025-FY
- **fv_base:** 4.22 -> **3.99** (bear 3.21, bull 4.98)
- **FCF0:** 196,712
- **net debt:** -32,628 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 195,496; annual FY2024 186,982; 2025-FY 211,933 = 198,137; acquisitions mean 2,517 NOT deducted (paid in fewer than two of three years); + interest after tax -1,425 at 0.25 (GB); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital 2,373 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -32,628 on the balance sheet + deals 0 + working capital neutralised 2,373 = -30,255
- **events ledger** `reference/events/RMV.L.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 756,031,940
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 3,226 is DEDUCTED -- principal 3,146 + lease interest 80; the lease liability 5,361 LEFT net debt
- **close 2026-10-26:** 5.31; g* 6.87%
- **store's newest period:** 2026-06-30

```
RMV.L — strike 2026-10-27   against RMV.L-2026-09-19-e117.json

                                  before           after     move
fv_base                             4.22            3.99    -5.3%
  bear                              3.39            3.21    -5.4%
  bull                              5.25            4.98    -5.2%
MBP (E90)  tier -- -> --              --              --         
g*                                                 6.87%         

WHICH LEG MOVED
  FCF0                          212,455,000 -> 196,712,000              -7.4%
  net debt                          -41,189 -> -32,628                 -20.8%
  divisor (shares)              775,356,560 -> 756,031,940              -2.5%
  unchanged: basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-09-18 -> 2026-10-26  (5.31)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/RMV.L-2026-10-27.json`
