# CTSH -- struck 2026-10-28

*Struck by `vss strike` off `config/manual/CTSH.yaml` on the growth DERIVED from the issuer's history (E144) 3.18% / 0.74% / 3.18%, carried from CTSH-2026-10-27-check.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** 73.96 -> **69.42** (bear 47.21, bull 79.99)
- **FCF0:** 2,329,416,667
- **net debt:** 782,000,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 2,014,000,000; annual FY2024 2,150,000,000; annual FY2025 2,741,000,000 = 2,301,666,667; acquisitions mean 674,666,667 NOT deducted -- valued as the deal programme (E142); + interest after tax 27,750,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -984,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 782,000,000 on the balance sheet + deals 300,000,000 + working capital neutralised -984,000,000 = 98,000,000
- **growth (E144):** E144: organic 3.18%/yr over 5 years, last five 3.18% (2021-2025); owner earnings per share 4.83%/yr; cap 4%; worst 3-year 0.74%, best 5-year 3.18%
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.875: the weakest E140 year 2,014,000,000 over the mean 2,301,666,667 (E143(4))
- **deal programme (E142):** repeat buyer, A = 674,666,667/yr; ROIIC base 0.56% -- operating profit 2,304,000,000 (2015-2017 mean) -> 2,990,000,000 (2023-2025 mean); organic x1.277 (4 of 8 years at the view's 3.2%); after tax 25.0%: 35,779,909 on acquisitions 6,428,000,000 = 0.56%; bear 0.00% -- operating profit 2,801,000,000 (2018) -> 2,689,000,000 (2023); organic x1.201 (2 of 5 years at the view's 3.2%); after tax 25.0%: -505,639,807 on acquisitions 3,486,000,000 = -14.50%
- **bear:** flow 2,329,416,667 x level 0.875 x (1 + 0.74%) = FCF0 2,053,418,492; programme -4,388,942,133 (-9.42/sh); deals 300,000,000 credited back 0 at ROIIC 0.00% (+0.00/sh); pension deficit after tax (E146) +65,000,000 (+0.14/sh) -> **47.21**
- **base:** flow 2,329,416,667 x level 1.000 x (1 + 3.18%) = FCF0 2,403,517,422; programme -4,647,297,101 (-9.97/sh); deals 300,000,000 credited back 17,577,658 at ROIIC 0.56% (+0.04/sh); pension deficit after tax (E146) +65,000,000 (+0.14/sh) -> **69.42**
- **bull:** flow 2,329,416,667 x level 1.000 x (1 + 3.18%) = FCF0 2,403,517,422; programme 0 (+0.00/sh); deals 300,000,000 credited back 300,000,000 at ROIIC 9.50% (+0.64/sh); pension deficit after tax (E146) +65,000,000 (+0.14/sh) -> **79.99**
- **events ledger** `reference/events/CTSH.yaml` dated 2026-10-27, cut at 2026-06-30: DyFlex Solutions (Australia; price NOT DISCLOSED; range is the session estimate) 50,000,000..300,000,000; already in the balance sheet: 3Cloud; Astreya Partners (incl. contingent 25m)
- **divisor:** 466,000,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 534,000,000 LEFT net debt; finance leases stay in net debt
- **MBP (E90, tier 3):** 48.07 -> 45.12
- **close 2026-10-27:** 66.22; g* 2.65%
- **store's newest period:** 2026-06-30
- **anchors:** g* 2.65%; the base case returns ~9.8% a year at today's price against r 9.5%; tangible ROIC median 35.6% over 11 years (goodwill taken out) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 35.6% over 11 years (goodwill taken out) against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 25% below its running peak
  - Q3 debt: **PASS** -- net debt 0.0x FCF0 against 3.0x
  - Q4 capital allocation: **FAIL** -- ROIIC 0.6% against r 9.5%
  - Q5 understandable: **PASS** -- Cognizant sells IT consulting, systems integration and outsourcing services to large enterprises; embedded delivery teams keep clients renewing.

```
CTSH — strike 2026-10-28   against CTSH-2026-10-27-check.json

                                               before           after     move
fv_base                                         73.96           69.42    -6.1%
  bear                                          47.21           47.21    +0.0%
  bull                                          79.99           79.99    +0.0%
MBP (E90)  tier 3 -> 3                          48.07           45.12    -6.1%
g*                                                              2.65%         
  fv_base, deals at LOW end (E140(3))                           69.92         

WHICH LEG MOVED
  growth view         4.00% / 0.00% / 7.00% -> 3.18% / 0.74% / 3.18%            E144: derived from the issuer's history
  unchanged: FCF0, net debt, divisor (shares), basis, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2025-12-31 -> 2025-12-31
  settled close           2026-10-26 -> 2026-10-27  (66.22)
  store's newest period, today: 2026-06-30   <- NEWER THAN THE BASIS: a quarter has landed that this strike did not read (E19 chooses ONE window)
```

Record: `reference/run-records/CTSH-2026-10-28-organic.json`
