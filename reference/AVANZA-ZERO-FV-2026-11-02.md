# Avanza Zero holdings -- rough bear / base / bull, 2026-11-02

Owner asked for fair value on every Avanza Zero holding (top 25 per Avanza's
fund API, `holdingChartData`, ~96 % of the fund). **ROUGH FILTER, NOT A STRIKE**:
figures are Yahoo's (OCF - capex, last 3 fiscal years mean; cash - total debt;
implied shares across all classes; statement currency converted to SEK at
11-02 FX). Growth 0 / 4 / 8 %, r 9.5 %, terminal 2.5 %. Script:
`tools/zero_fv_scratch.py`.

**IFRS 16 trap**: lease payments sit in financing, so OCF - capex overstates
FCF for heavy leasers. H&M and Ericsson corrected by hand below; Telia, Tele2,
Essity carry it too, and correcting only makes them dearer.

| Name | Weight | Price | Bear 0 % | Base 4 % | Bull 8 % | Price / base |
|---|---:|---:|---:|---:|---:|---:|
| Evolution | 1.91 % | 840.2 | 869.4 | **1196.4** | 1655.6 | **0.70x** |
| Ericsson B (lease-adj ~3bn/yr) | 3.51 % | 108.8 | 85.6 | **117.6** | 162.5 | 0.93x |
| Essity B | 1.99 % | 279.4 | 154.6 | 232.3 | 341.3 | 1.2x |
| SKF B | 1.42 % | 274.9 | 150.0 | 214.7 | 305.4 | 1.3x |
| Tele2 B | 1.37 % | 159.2 | 72.3 | 117.3 | 180.4 | 1.4x |
| Assa Abloy B | 4.60 % | 390.2 | 147.7 | 229.0 | 343.2 | 1.7x |
| Alfa Laval | 2.84 % | 538.8 | 191.0 | 279.3 | 403.3 | 1.9x |
| Sandvik | 5.78 % | 360.6 | 118.8 | 176.0 | 256.3 | 2.0x |
| Atlas Copco A (+B 3.41 %) | 8.50 % | 185.4 | 62.6 | 89.0 | 126.0 | 2.1x |
| Telia | 2.12 % | 49.0 | 11.9 | 23.8 | 40.6 | 2.1x |
| ABB | 5.12 % | 845.4 | 246.8 | 349.9 | 494.7 | 2.4x |
| Hexagon B | 3.14 % | 109.8 | 28.5 | 45.3 | 68.7 | 2.4x |
| Epiroc A | 2.66 % | 242.6 | 67.6 | 97.8 | 140.3 | 2.5x |
| EQT | 4.33 % | 313.5 | 92.2 | 116.5 | 150.7 | 2.7x |
| AstraZeneca | 3.05 % | 1817.5 | 427.6 | 655.4 | 975.3 | 2.8x |
| H&M B (lease-adj ~16.5bn/yr) | 2.75 % | 177.1 | 38.1 | 54.4 | 77.4 | 3.3x |
| Volvo B | 6.30 % | 305.1 | 11.4 | 51.4 | 107.5 | 5.9x |
| SAAB B | 4.05 % | 672.5 | 74.3 | 103.3 | 143.9 | 6.5x |
| Boliden | 1.79 % | 502.4 | 13.3 | 38.9 | 74.8 | 12.9x |
| Investor B, Swedbank, SEB, Handelsbanken, Nordea | 25.4 % | | -- | -- | -- | banks / holding co: FCF-DCF does not apply (book value, NAV) |

Notes:
- Volvo's FCF runs through its financial-services arm (customer financing
  in OCF), so the figure is meaningless low, not a verdict. Boliden and SAAB
  are in capex-heavy phases (mines; defence ramp) -- same caveat.
- **Evolution is the one under even the bear case.** The discount is the
  market's price for its risks: regulation (UK and others), revenue from
  unregulated Asian markets, slowing growth. Candidate for a proper screen
  (§4.2 kills, Q1-Q4, circle of competence) if the owner wants it.
- Ericsson is about fair after leases; its 3y mean straddles a weak 2023 and a
  working-capital release in 2024.
