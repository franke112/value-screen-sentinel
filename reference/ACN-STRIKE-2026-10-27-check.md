# ACN -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/ACN.yaml` on the pre-registered growth view 4.50% / 0.00% / 7.50%, carried from ACN-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** TTM 2026-Q1+2026-Q2+2026-Q3+2026-Q4
- **fv_base:** 274.88 -> **275.51** (bear 167.04, bull 353.60)
- **FCF0:** 9,500,796,333
- **net debt:** -1,167,236,000 on the balance sheet of 2026-08-31
- **E140 FCF0:** mean of annual FY2024 8,945,894,000; annual FY2025 9,530,579,000; annual FY2026 10,171,821,000 = 9,549,431,333; acquisitions mean 4,331,613,667 NOT deducted -- valued as the deal programme (E142); + interest after tax -44,856,000 at 0.25 (US); - minority dividends 3,779,000
- **bridge (E140(3), deals at the HIGH end):** net debt -1,167,236,000 on the balance sheet + deals 500,000,000 + working capital neutralised 0 = -667,236,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/ACN.yaml; the registered view reference/growth-views/ACN.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.937: the weakest E140 year 8,945,894,000 over the mean 9,549,431,333 (E143(4))
- **deal programme (E142):** repeat buyer, A = 4,331,613,667/yr; ROIIC base 9.98% -- operating profit 5,300,208,667 (2016-2018 mean) -> 10,409,157,000 (2024-2026 mean); organic x1.422 (8 of 8 years at the view's 4.5%); after tax 25.0%: 2,153,795,255 on acquisitions 21,585,711,000 = 9.98%; bear 7.14% -- operating profit 6,305,074,000 (2019) -> 9,595,847,000 (2024); organic x1.246 (5 of 5 years at the view's 4.5%); after tax 25.0%: 1,303,933,249 on acquisitions 18,263,839,000 = 7.14%
- **bear:** flow 9,500,796,333 x level 0.937 x (1 + 0.00%) = FCF0 8,900,332,800; programme -6,758,032,315 (-10.94/sh); deals 500,000,000 credited back 375,759,257 at ROIIC 7.14% (+0.61/sh); pension deficit after tax (E146) +389,693,750 (+0.63/sh) -> **167.04**
- **base:** flow 9,500,796,333 x level 1.000 x (1 + 4.50%) = FCF0 9,928,332,168; programme 0 (+0.00/sh); deals 500,000,000 credited back 500,000,000 at ROIIC 9.98% (+0.81/sh); pension deficit after tax (E146) +389,693,750 (+0.63/sh) -> **275.51**
- **bull:** flow 9,500,796,333 x level 1.000 x (1 + 7.50%) = FCF0 10,213,356,058; programme 0 (+0.00/sh); deals 500,000,000 credited back 500,000,000 at ROIIC 9.50% (+0.81/sh); pension deficit after tax (E146) +389,693,750 (+0.63/sh) -> **353.60**
- **events ledger** `reference/events/ACN.yaml` dated 2026-10-27, cut at 2026-08-31: Mjolner Informatics, Sagacity, McCoy (pending), NetRise/IndX (status unconfirmed) -- prices NOT DISCLOSED; range is the session estimate 50,000,000..500,000,000
- **divisor:** 617,498,483
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 3,285,232,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-26:** 247.23; g* 3.19%
- **store's newest period:** 2026-08-31
- **anchors:** g* 3.19%; the base case returns ~10.2% a year at today's price against r 9.5%; tangible ROIC median 2309.6% over 11 years against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 2309.6% over 11 years against 15%
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 6% below its running peak
  - Q3 debt: **PASS** -- net debt -0.1x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **PASS** -- ROIIC 10.0% against r 9.5%
  - Q5 understandable: **PASS** -- Accenture sells consulting, managed services, proprietary platforms and software to large companies and governments, who return because it embeds in their technology and operations.

```
ACN — strike 2026-10-27   against ACN-2026-10-27-e142.json

                                               before           after     move
fv_base                                        274.88          275.51    +0.2%
  bear                                         166.41          167.04    +0.4%
  bull                                         352.97          353.60    +0.2%
MBP (E90)  tier -- -> --                           --              --         
g*                                                              3.19%         
  fv_base, deals at LOW end (E140(3))                          275.51         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-08-31 -> 2026-08-31
  settled close           2026-10-26 -> 2026-10-26  (247.23)
  store's newest period, today: 2026-08-31
```

Record: `reference/run-records/ACN-2026-10-27-check.json`
