# Placera "dagens aktierekommendationer" 2026-11-03 -- rough fv on the buy-rated names

Source: placera.se/nyheter/telia-kopstamplas-dagens-aktierekommendationer-2026-11-03
(owner asked). Rough Yahoo screen, same method as AVANZA-ZERO-FV-2026-11-02:
3y mean FCF (OCF - capex as Yahoo reports it), r 9.5 %, terminal 2.5 %,
growth 0 / 4 / 8 % = bear / base / bull. Prices 11-03, in the trading currency.
Scratch script: data/scratch/placera_fv.py (not in the repo). **Not a strike.**

| Ticker | Price | Bear | Base | Bull | Price/base | Note |
|---|---:|---:|---:|---:|---:|---|
| SOFF.OL  | 68.80  | 153.1 | 223.9 | 323.3 | 0.31x | offshore vessels, peak cycle; consolidates its Solstad Maritime stake -> overstated |
| WAWI.OL  | 171.20 | 363.5 | 521.8 | 744.2 | 0.33x | car shipping, peak freight rates, heavy leases (IFRS 16) |
| SOMA.OL  | 27.85  | 35.2  | 53.5  | 79.3  | 0.52x | offshore vessels, peak cycle, net debt |
| HIAB.HE  | 48.34  | 63.5  | 87.4  | 121.0 | 0.55x | ex-Cargotec; older years likely include the old group; latest year FCF 172m -> base about 50 |
| ENDUR.OL | 128.40 | 113.8 | 161.2 | 227.7 | 0.80x | FCF 92 -> 435 -> 972, latest year a jump; deal-driven |
| UPM.HE   | 21.93  | 16.9  | 25.8  | 38.3  | 0.85x | forest, cyclical |
| TEL.OL   | 133.60 | 93.4  | 154.9 | 241.3 | 0.86x | telecom; lease payments + spectrum not taken out -> about fair |
| BIOMAR.CO| 123.50 | 91.9  | 141.4 | 210.9 | 0.87x | fish feed; 2025 FCF 433 vs 1 300 before (WC); levered |
| DOFG.OL  | 129.00 | 36.8  | 69.4  | 115.2 | 1.86x | |
| OEM-B.ST | 168.80 | 66.3  | 90.5  | 124.6 | 1.87x | quality, net cash, but 1.9x |
| TELIA.ST | 49.22  | 11.9  | 23.8  | 40.6  | 2.07x | (same as the Zero file) |
| SUS.ST   | 59.35  | 36.0  | 45.9  | 59.8  | 1.29x | |
| FRAMERY.HE| 7.16  | 3.6   | 5.4   | 7.9   | 1.33x | two years of FCF only |
| METSB.HE | 3.00   | 0.6   | 1.1   | 1.7   | 2.85x | |
| IVSO.ST  | 217.80 | 43.6  | 58.1  | 78.4  | 3.75x | |
| SOBI.ST  | 480.40 | 78.8  | 121.9 | 182.4 | 3.94x | |
| BAKKA.OL | 434.20 | 6.2   | 52.4  | 117.2 | 8.3x  | FCF -39 / 1 329 / -56 |
| EMBRAC-B.ST | 91.76 | neg | neg | neg | -- | FCF negative three years |
| BEWI.OL  | 17.50  | neg   | neg   | 0.4   | -- | |

Not valued: Avanza, Danske Bank, Ringkjobing (banks); Catena (property);
Dormy, Outlet Group, Ilkka (no Yahoo data / new listings). AstraZeneca 2.8x and
Telia 2.1x in AVANZA-ZERO-FV-2026-11-02.

ACAD.ST (held): Nordea 135, DNB Carnegie 142, SEB 130 (upgraded to kop);
price 123.80; our fv 110.63 / 158.74 / 181.95 -- the brokers sit under our base.

**Verdict: nothing to take in.** The only names under 0.8x base are
shipping/offshore at peak cycle (the method reads peak FCF as normal -- the
cyclical trap, E77) and Hiab, whose cheap reading comes from pre-split years.
Hiab is the one worth a proper look if the owner wants one: Finnish IFRS
filer, needs a hand read of the 2025 AR + Q3 2026.

## Second pass, same day: the eight under 0.9x, with Warren (E145 Q1-Q5) and the news

Owner: "kolla alla dem som är för billiga ... kör warren på dem". Yahoo 2022-25
annuals (data/scratch/warren8.py), statutory tax NO/DK 22 %, FI 20 %; one
news search per name. Still a screen, not a strike: the figures marked *est*
are the session's estimates, not read from a report.

| Name | Q1 ROTIC | Q2 | Q3 | Normalised fv 0/4/8 % | Price | Verdict |
|---|---|---|---|---|---:|---|
| UPM | ~5 % FAIL | | | | 21.93 | out on Q1 |
| Telenor | ~12 % FAIL | | | | 133.60 | out on Q1 |
| Solstad Offshore | | FAIL (restructured 2020-23, equity 180m on 2.3bn debt in 2022) | | | 68.80 | out on Q2 |
| Solstad Maritime | | FAIL (same history, listed 2024) | | | 27.85 | out on Q2 |
| Hiab | ~16-18 % pass | pass (comp EBIT 197-216) | pass before the deal | 33.1 / **50.6** / -- | 48.34 | **fair, not cheap**: bought Labrie (EVS) 07-01 at EV USD 1 035m (9.2x EBITDA) on bank debt -> net debt about EUR 0.72bn, absent from Yahoo's 2025 balance sheet. FCF0 235 *est* (old Hiab 167 + EVS 68). Deal return ~7 % < r |
| BioMar | ~14-19 % pass (3 y only) | pass (3 y) | 3.3x, passes under 4.5x limb | 79.1 / **122.3** / 182.8 | 123.50 | **fair**: on the 2026 EBIT guide 1.2-1.3bn (raised 08-12), capex 400-500. Yahoo's mean leaned on a 2024-25 working-capital release (the CENTA trap) |
| Endúr | median ~16 % (tangible base tiny, 80 % goodwill) | pass | pass | 82.7 / **115.2** / 160.8 | 128.40 | **over**: 2025 OCF 1 039 on EBIT 322 = working-capital inflow; on run-rate EBIT 388 it is 1.1x. Roll-up, equity doubled 2025 (share issue) |
| Wallenius Wilhelmsen | ~16-21 % pass at peak | doubtful: 2020 loss year (not checked) | pass | guide EBITDA 1.6bn: 142.6 / **201.3** / 283.6; mid-cycle 1.1bn: 19 / 29 / 43 | 171.20 | **cyclical, no**: 0.85x only if the peak holds. FCF0 = EBITDA - leases 400 *est* - fleet renewal 600 *est* (26 newbuilds through 2032; USD 300m share issue 10-06 to fund them). 2026 EBITDA guide already cut from 1.65-1.75 to ~1.6bn. Q3 report 11-04 |

**Result: nothing passes both Warren and the price.** Two fail Q1, two fail Q2;
of the four that pass the tests, Hiab and BioMar are at fair value once the
deal debt and the working capital are taken out, Endúr is over, and Wallenius
is cheap only on peak freight. The first screen's 0.3-0.6x readings came from
three things the Yahoo shortcut cannot see: peak-cycle cash flow, a debt-funded
deal after the balance-sheet date, and working-capital releases.
