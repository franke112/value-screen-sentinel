# Our fv base against the brokers' mean target, 2026-11-03

Owner asked for every name we have valued, side by side with the analysts.
Our base: the latest strike (`reference/*-STRIKE-2026-10-27-check.md`, later
strikes for CTSH 10-28 organic, BKNG 10-28 e148, DHI 10-28, ZTS 10-29, SFM
10-29, GNTX, SAP 08-30) and this week's reference notes (EVO, WAWI, HIAB,
BIOMAR, the newsdrop and cyber names). Broker mean target, analyst count and
consensus label from Yahoo `info` (`targetMeanPrice`), price 11-03.
AUTO.L and RMV.L are in pence (our base x 100). Script:
`data/scratch/vs_brokers.py`. **Information only; nothing here moves a value.**

```
SFM        px 52.78 | our 78.71 p/our  0.67 | brok 61.0 p/brok  0.87 n 14 buy
BKNG       px 151.61 | our 218.18 p/our  0.69 | brok 232.45714 p/brok  0.65 n 35 buy
EVO.ST     px 849.0 | our 1196.4 p/our  0.71 | brok 765.8581 p/brok  1.11 n 17 hold
GNTX       px 20.245 | our 27.45 p/our  0.74 | brok 25.27778 p/brok  0.80 n 9 hold
HRB        px 53.57 | our 68.38 p/our  0.78 | brok 51.66667 p/brok  1.04 n 3 hold
ACAD.ST    px 124.4 | our 158.74 p/our  0.78 | brok 128.33333 p/brok  0.97 n 3 strong_buy
DHI        px 145.57 | our 184.54 p/our  0.79 | brok 148.64285 p/brok  0.98 n 14 hold
NVR        px 6089.12 | our 7682.75 p/our  0.79 | brok 6229.6665 p/brok  0.98 n 6 hold
MEKKO.HE   px 9.25 | our 10.95 p/our  0.84 | brok 11.275 p/brok  0.82 n 4 none
CROX       px 155.95 | our 171.83 p/our  0.91 | brok 164.66667 p/brok  0.95 n 12 buy
PNDORA.CO  px 829.4 | our 903.81 p/our  0.92 | brok 858.3684 p/brok  0.97 n 19 hold
ACN        px 254.04 | our 275.51 p/our  0.92 | brok 229.73792 p/brok  1.11 n 24 buy
CTSH       px 64.1 | our 69.42 p/our  0.92 | brok 69.504 p/brok  0.92 n 25 buy
HIAB.HE    px 48.28 | our 50.6 p/our  0.95 | brok 63.4 p/brok  0.76 n 5 buy
BOUV.OL    px 53.9 | our 54.42 p/our  0.99 | brok 50.0 p/brok  1.08 n 2 none
AOS        px 63.845 | our 64.37 p/our  0.99 | brok 66.5 p/brok  0.96 n 10 hold
DECK       px 84.44 | our 85.05 p/our  0.99 | brok 96.74286 p/brok  0.87 n 21 hold
BIOMAR.CO  px 121.9 | our 122.3 p/our  1.00 | brok 144.0 p/brok  0.85 n 5 buy
CENTA      px 40.455 | our 40.19 p/our  1.01 | brok 46.25 p/brok  0.87 n 4 buy
MC.PA      px 401.5 | our 392.95 p/our  1.02 | brok 491.54074 p/brok  0.82 n 27 buy
ZTS        px 83.315 | our 79.8 p/our  1.04 | brok 88.38462 p/brok  0.94 n 13 hold
ULTA       px 630.8 | our 601.27 p/our  1.05 | brok 635.84 p/brok  0.99 n 25 buy
LOPE       px 147.725 | our 136.56 p/our  1.08 | brok 194.0 p/brok  0.76 n 3 none
AUTO.L     px 544.6 | our 499.0 p/our  1.09 | brok 560.474 p/brok  0.97 n 19 hold
LII        px 346.07 | our 309.69 p/our  1.12 | brok 371.92307 p/brok  0.93 n 13 hold
CPRT       px 31.36 | our 26.96 p/our  1.16 | brok 39.0 p/brok  0.80 n 10 buy
HPQ        px 28.165 | our 22.67 p/our  1.24 | brok 27.51765 p/brok  1.02 n 17 hold
RMV.L      px 538.4 | our 411.00000000000006 p/our  1.31 | brok 535.90497 p/brok  1.00 n 21 hold
GDDY       px 113.93 | our 79.99 p/our  1.42 | brok 117.6875 p/brok  0.97 n 16 buy
SAP.DE     px 206.65 | our 140.37 p/our  1.47 | brok 238.93295 p/brok  0.86 n 27 buy
WAWI.OL    px 168.0 | our 114 p/our  1.47 | brok 175.2329 p/brok  0.96 n 5 buy
ALV        px 119.82 | our 71.74 p/our  1.67 | brok 131.25 p/brok  0.91 n 16 buy
MUSA       px 512.485 | our 268.53 p/our  1.91 | brok 616.0 p/brok  0.83 n 10 buy
LIAB.ST    px 130.9 | our 66.68 p/our  1.96 | brok 141.66667 p/brok  0.92 n 3 buy
PEP        px 138.43 | our 65.28 p/our  2.12 | brok 141.59091 p/brok  0.98 n 22 hold
QLYS       px 210.61 | our 93.73 p/our  2.25 | brok 187.585 p/brok  1.12 n 18 hold
RBREW.CO   px 454.0 | our 195.97 p/our  2.32 | brok 489.6 p/brok  0.93 n 15 hold
NTAP       px 191.19 | our 59.81 p/our  3.20 | brok 211.6875 p/brok  0.90 n 16 buy
AMAT       px 381.37 | our 107.78 p/our  3.54 | brok 626.86487 p/brok  0.61 n 37 strong_buy
DELL       px 407.96 | our 112.59 p/our  3.62 | brok 590.0 p/brok  0.69 n 25 buy
AVGO       px 332.48 | our 57.62 p/our  5.77 | brok 526.80835 p/brok  0.63 n 48 strong_buy
CSCO       px 103.15 | our 16.53 p/our  6.24 | brok 136.16 p/brok  0.76 n 25 buy
KEYS       px 306.69 | our 48.51 p/our  6.32 | brok 419.66666 p/brok  0.73 n 12 buy
```

**What it shows.** The brokers' target sits 0.6-1.1x the price on every
name; ours runs 0.67x to 6.3x. On our ten cheapest the brokers see a median
of about 4 % upside and mostly say *hold*; on our ten dearest (AVGO, AMAT,
CSCO, KEYS, DELL, NTAP...) they see about 19 % and say *buy / strong buy*. The
two lists point in opposite directions: a 12-month target follows the price
and the story, a value follows the cash. Several of our cheapest names
(SFM, BKNG, NVR, DHI, GNTX, HRB) are gated by kill rules, not bought, so
"cheap on our number" is not "a buy" either.

## Where the broker mean lands in our bear / base / bull range

Bear/bull from the same strikes (AUTO.L/RMV.L in pence; HIAB, BIOMAR, WAWI,
EVO from this week's rough notes). Count of 43: **below our bear 1** (EVO);
**bear-base 10** (SFM, GNTX, HRB, ACAD, DHI, NVR, CROX, PNDORA, ACN, BOUV);
**about base 1** (CTSH); **base-bull 8** (BKNG, MEKKO, AOS, DECK, BIOMAR,
CENTA, AUTO.L, GDDY); **about our bull 1** (WAWI); **above base, no bull
struck 2** (HIAB, SAP); **above our bull 20** (MC.PA, ZTS, ULTA, LOPE, LII,
CPRT, HPQ, RMV.L, ALV, MUSA, LIAB, PEP, QLYS, RBREW, NTAP, AMAT, DELL, AVGO,
CSCO, KEYS).
