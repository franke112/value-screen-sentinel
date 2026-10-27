# BKNG -- struck 2026-10-27

*Struck by `vss strike` off `config/manual/BKNG.yaml` on the pre-registered growth view 5.00% / 0.00% / 8.00% (first strike, from the entry). Nothing here writes the watchlist: fv_base, tier, mbp and stop_price are the owner's.*

- **basis:** annual FY2025
- **fv_base:** -- -> **218.18** (bear -2.96, bull 281.48)
- **FCF0:** 9,204,416,667
- **net debt:** 2,972,000,000 on the balance sheet of 2026-06-30
- **E140 FCF0:** mean of annual FY2023 7,475,000,000; annual FY2024 7,591,000,000; annual FY2025 8,909,000,000 = 7,991,666,667; acquisitions mean 0 NOT deducted -- valued as the deal programme (E142); + interest after tax 1,212,750,000 at 0.25 (US); - minority dividends 0
- **bridge rolled (E140.1(3)):** 2025-12-31 -> 2026-06-30; year-to-date working capital -690,000,000 neutralised (added to net debt)
- **bridge (E140(3), deals at the HIGH end):** net debt 2,972,000,000 on the balance sheet + deals 0 + working capital neutralised -690,000,000 = 2,282,000,000
- **growth (E144):** VIEW, NOT DERIVED (E144(4)): fewer than five organic years in config/history/BKNG.yaml; the registered view reference/growth-views/BKNG.md
- **cycle and level (E143):** CYCLICAL (revenue fell -55% in a year; operating margin fell from 36.8% to -9.3%): owner-earnings margin median 33.3%, last three 33.3%, lowest -3.0% -> base level x1.000, bear x0.000
- **deal programme (E142):** not a repeat buyer: no programme
- **bear:** flow 9,204,416,667 x level 0.000 x (1 + 0.00%) = FCF0 0; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 0.00% (+0.00/sh) -> **-2.96**
- **base:** flow 9,204,416,667 x level 1.000 x (1 + 5.00%) = FCF0 9,663,482,133; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 169.01% (+0.00/sh) -> **218.18**
- **bull:** flow 9,204,416,667 x level 1.000 x (1 + 8.00%) = FCF0 9,940,770,000; programme 0 (+0.00/sh); deals 0 credited back 0 at ROIIC 9.50% (+0.00/sh) -> **281.48**
- **events ledger** `reference/events/BKNG.yaml` dated 2026-10-27, cut at 2026-06-30: no deal in the bridge
- **divisor:** 770,000,000
- **lease:** RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease payments (ASC 842-20-45-5(a)) and NOTHING is added back; the lease liability 672,000,000 LEFT net debt; finance leases stay in net debt
- **close 2026-10-27:** 150.14; g* 0.60%
- **store's newest period:** --
- **anchors:** g* 0.60%; the base case returns ~12.4% a year at today's price against r 9.5%; tangible ROIC median 60.6% over 11 years (goodwill taken out) against 15%
- **would Warren own it (E145):**
  - Q1 tangible ROIC: **PASS** -- median 60.6% over 11 years (goodwill taken out) against 15%
  - Q2 stability: **FAIL** -- owner earnings negative in [2020]; operating profit at most 112% below its running peak, regained within three years
  - Q3 debt: **PASS** -- net debt 0.2x FCF0 against 3.0x
  - Q4 capital allocation: **PASS** -- not a repeat buyer
  - Q5 understandable: **PASS** -- Booking sells hotel rooms, flights, car rentals and restaurant bookings online to travellers through Booking.com, Priceline, Agoda, KAYAK and OpenTable, earning a commission from the providers.

```
BKNG — strike 2026-10-27   (first strike: no prior record)

                                  before           after     move
fv_base                               --          218.18         
  bear                                --           -2.96         
  bull                                --          281.48         
MBP (E90)  tier -- -> --              --              --         
g*                                                 0.60%         

WHICH LEG MOVED
  FCF0                                   -- -> 9,204,416,667                 
  net debt                               -- -> 2,972,000,000                 
  divisor (shares)                       -- -> 770,000,000                   
  basis                                  -- -> annual FY2025                 
  growth view                            -- -> 5.00% / 0.00% / 8.00%            E28: the view is the prior record's, unchanged by a strike
  discount rate                          -- -> 0                             
  lease treatment                        -- -> RENT IS AN OPERATING COST (E117): the operating cash flow bears the operating lease paymen        

WHAT THE TWO SIDES STAND ON
  basis window end        -- -> 2025-12-31
  settled close           -- -> 2026-10-27  (150.14)
  store's newest period, today: --
```

Record: `reference/run-records/BKNG-2026-10-27.json`
