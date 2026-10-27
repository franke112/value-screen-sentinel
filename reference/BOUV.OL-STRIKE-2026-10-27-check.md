# BOUV.OL -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/BOUV.OL.yaml` on the pre-registered growth view 3.00% / 2.00% / 6.00%, carried from BOUV.OL-2026-10-27-e142.json. Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2
- **fv_base:** 54.42 -> **54.42** (bear 46.07, bull 69.34)
- **FCF0:** 335,307
- **net debt:** -159,733 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 304,182; annual FY2024 378,272; annual FY2025 323,468 = 335,307; acquisitions mean 6,571 NOT deducted -- valued as the deal programme (E142); + interest after tax 0 at 0.22 (NO); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -284,001 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt -159,733 on the balance sheet + deals 0 + working capital neutralised -284,001 = -443,734
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/BOUV.OL.yaml; the registered view reference/growth-views/BOUV.OL.md
- **cycle and level (E143):** not cyclical (E143(3)); bear level x0.907: the weakest E140 year 304,182 over the mean 335,307 (E143(4))
- **deal programme (E142):** repeat buyer, A = 6,571/yr; ROIIC base 0.00% -- ROIIC NOT DERIVABLE (the history has no profit and capital pair); struck at ZERO, the conservative end: the programme at zero moves the value 0.8%, inside E106's 3.5% (E142(6)); bear 0.00% -- ROIIC NOT DERIVABLE (the history has no profit and capital pair); struck at ZERO, the conservative end: the programme at zero moves the value 0.8%, inside E106's 3.5% (E142(6))
- **bear:** flow 335,307 x level 0.907 x (1 + 2.00%) = FCF0 310,266; programme -45,408 (-0.44/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **46.07**
- **base:** flow 335,307 x level 1.000 x (1 + 3.00%) = FCF0 345,367; programme -47,659 (-0.46/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **54.42**
- **bull:** flow 335,307 x level 1.000 x (1 + 6.00%) = FCF0 355,426; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **69.34**
- **events ledger** `reference/events/BOUV.OL.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 103,695,316
- **lease:** RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash outflow 89,629 is DEDUCTED -- principal 65,089 + lease interest 24,540; the lease liability 321,855 LEFT net debt
- **close 2026-10-26:** 51.70; g* 2.33%
- **store's newest period:** 2026-06-30
- **anchors:** g* 2.33%; the base case returns ~9.9% a year at today's price against r 9.5%; tangible ROIC no profit and capital years
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **n/a** -- no profit and capital years
  - Q2 stability: **PASS** -- owner earnings negative in no year; operating profit at most 3% below its running peak
  - Q3 debt: **PASS** -- net debt -1.3x FCF0 against 4.5x (stable class)
  - Q4 capital allocation: **FAIL** -- ROIIC 0.0% against r 9.5%
  - Q5 understandable: **PASS** -- Bouvet is a Scandinavian IT and digital communication consultancy serving private and public clients.

```
BOUV.OL — strike 2026-10-27   against BOUV.OL-2026-10-27-e142.json

                                  before           after     move
fv_base                            54.42           54.42    +0.0%
  bear                             46.07           46.07    +0.0%
  bull                             69.34           69.34    +0.0%
MBP (E90)  tier -- -> --              --              --         
g*                                                 2.33%         

WHICH LEG MOVED
  unchanged: FCF0, net debt, divisor (shares), basis, growth view, discount rate, lease treatment

WHAT THE TWO SIDES STAND ON
  basis window end        2026-06-30 -> 2026-06-30
  settled close           2026-10-26 -> 2026-10-26  (51.70)
  store's newest period, today: 2026-06-30
```

Record: `reference/run-records/BOUV.OL-2026-10-27-check.json`
