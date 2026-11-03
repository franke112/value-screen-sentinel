# Metodpiloten 2018-04-30 (väg 1), 2026-10-29

*Körning: `.venv/bin/python -m tools.backtest.method_pilot --date 2018-04-30`
(samma 50 bolag och seed som `PILOT-2018.md`). Raderna finns i
`data/backtest/pilot/METHOD-2018-04-30.json`. Reglerna M1–M8 står i
`tools/backtest/method.py`. Resultatet gäller bara överlevare (ägaren
2026-10-29).*

## Svaret först

- **Metoden värderar 32 av 50 bolag**, mot motorns 1. 24 av dem har kurs på
  testdagen.
- **Metoden är mycket försiktig. Bara 1 av 24 bolag ligger under fv:**
  Altisource (ASPS), fv/kurs 3,45. Det klarar inte Q2 och Q4 och föll 77 %
  på tre år, alltså en värdefälla som grinden sorterade bort. Inget bolag
  ligger under tier 3:s köpgräns och klarar Q1–Q4. Portföljen i
  designens fråga 3 blir alltså liten per testdag, även med 2 000 bolag.
  Kvintiltestet påverkas inte, eftersom det rangordnar bolagen.
- **E142:s avdrag för framtida förvärv avgör mycket.** 16 av 32 är
  återkommande köpare, och 8 får negativt fv, de flesta av avdraget: POST,
  OLN, Snyder's-Lance, SPB/HRG, ASH, Playa. LUMN och ALGT är negativa redan
  på grund av skulden. RBC Bearings får 8,21 med avdraget och 43,52 utan.
  Kolumnen "utan E142" finns för att testet ska kunna visa om regeln är för
  hård.
- **E144 räcker sällan för amerikanska bolag:** 21 av 32 använder
  reservregeln M6 (`*` i tabellen), eftersom de saknar fem år utan förvärv.

## Fel som hittades vid läsningen och rättades före den här tabellen

1. **MSFT fick FCF0 −33 mdr.** Microsoft taggar förutbetalda intäkter
   brutto: 52 mdr tillskott och de 48 mdr som intäktsförts på en egen rad.
   Regeln M2 lägger nu inte in en rörelsekapitalpost som är större än 25 % av
   årets intäkter, och antalet sådana poster står på raden. MSFT får nu FCF0
   25,7 mdr.
2. **MSFT fick nettoskuld 68 mdr i stället för nettokassa 55 mdr.** Den
   kombinerade taggen för kassa och kortfristiga placeringar läses nu
   först (M4).

## Kvar, inte rättat

- **6 stoppas på "no growth"** (NJR, PRIM, MELI, AMEDISYS, YRC, 2U).
  Historiken saknar intäkter, eftersom deras intäktstagg inte finns i
  motorns lista. Det gäller också live.
- **4 stoppas på "no FCF0"**, bland dem VFC (inga år med både OCF och capex).
  Det är inte utrett.
- **Kontrollen av börsvärde mot float fångar AMEDICA** (float 3 850 × börsvärdet),
  men inte IAC/MTCH eller HRG/SPB, vars tickers i dag hör till ett annat
  värdepapper. De måste tas bort för hand eller via en lista.
- **Cyklisk (C) på 28 av 50.** E143(3) räknar varje år över tio år, alltså
  även 2008–09. Det är motorns regel och den är inte ändrad.

## Hela tabellen

`*` = tillväxt enligt M6 (reserv). Q1–4: + klarar, x klarar inte, ? kan inte avgöras.
Belopp i miljoner USD.

| # | Bolag | Status | FCF0 m | g | Cyk | ND m | fv | bear | Kurs | fv/kurs | utan E142 | Q1-4 | Stopp | EBIT/EV | F | Float/cap | 1 år | 3 år | Index 3 år | Nollor |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | LEMAITRE VASCULAR INC (LMAT) | ok | 13 | 4.0%* |  | -19 | 12.41 | 9.24 | 31.45 | 0.39 | 12.41 | x+++ |  | 3.6% | 7 | 0.67 | -7% | 72% | 67% | 1 |
| 2 | WINNEBAGO INDUSTRIES INC (WGO) | ok | 38 | 4.0% |  | 244 | 12.03 | 4.21 | 37.90 | 0.32 | 12.03 | +xx+ |  | 8.7% | 6 | 0.85 | -5% | 118% | 67% | 0 |
| 3 | MARINEMAX INC (HZO) | ok | 37 | 4.0% | C | 272 | 12.38 | -10.24 | 21.60 | 0.57 | 12.38 | xxx+ | JA | 5.4% | 5 | 0.87 | -20% | 163% | 67% | 0 |
| 4 | Legacy Education Alliance, I (CIK1561880) | ok | 1 | 3.5%* | C | -6 | 1.22 | 0.26 | – | – | 1.22 | +x++ |  | – | 9 | – | – | – | – | 0 |
| 5 | NEW JERSEY RESOURCES CORP (NJR) | no growth: fewer than three revenue years (M6) | – | – | ? | – | – | – | 41.35 | – | – | – |  | – | – | – | 24% | 11% | 67% | 0 |
| 6 | 2U, Inc. (CIK1459417) | no growth: fewer than three revenue years (M6) | – | – | ? | – | – | – | – | – | – | – |  | – | – | – | – | – | – | 0 |
| 7 | Park Hotels & Resorts Inc. (PK) | ok | 419 | 1.9%* |  | 2,560 | 15.37 | 4.21 | 28.78 | 0.53 | 15.37 | x+x+ |  | 4.2% | – | 0.62 | 23% | -5% | 67% | 2 |
| 8 | HALLIBURTON CO (HAL) | FCF0 not positive | -445 | 3.1%* | C | 8,588 | – | – | 52.99 | – | – | xxxx |  | 2.5% | 5 | 0.80 | -45% | -60% | 67% | 3 |
| 9 | Bristow Group Inc (CIK73887) | FCF0 not positive | -254 | 2.7%* | C | 1,084 | – | – | – | – | – | ??x+ |  | – | – | – | – | – | – | 0 |
| 10 | GUIDED THERAPEUTICS INC (GTHP) | no FCF0: OCF and capex in [2016] (M1 needs three consecutive | – | – | ? | – | – | – | – | – | – | – |  | – | – | – | – | – | – | 0 |
| 11 | AMEDISYS INC (CIK896262) | no growth: fewer than three revenue years (M6) | – | – | ? | – | – | – | – | – | – | – |  | – | – | – | – | – | – | 0 |
| 12 | OCLARO, INC. (CIK1110647) | ok | 7 | 4.0% | C | -290 | 2.38 | 1.71 | – | – | 2.38 | xx++ | JA | – | 7 | – | – | – | – | 0 |
| 13 | Altisource Portfolio Solutio (ASPS) | ok | 125 | 4.0%* | C | 324 | 94.34 | 32.15 | 27.38 | 3.45 | 99.96 | +x+x | JA | 6.3% | – | 0.82 | -14% | -77% | 67% | 0 |
| 14 | TransMontaigne Partners L.P. (CIK1319229) | ok | 46 | 3.2%* |  | -1 | 0.56 | -14.14 | – | – | 44.05 | ?++? |  | – | – | – | – | – | – | 0 |
| 15 | IAC/INTERACTIVECORP (MTCH) | ok | 240 | 4.0%* | C | 988 | 10.45 | -17.17 | 165.01 | 0.06 | 32.61 | +xxx |  | 1.2% | – | 0.51 | 35% | 247% | 67% | 0 |
| 16 | Post Holdings, Inc. (POST) | ok | 495 | 4.0%* | C | 5,642 | -4.92 | -81.46 | 79.57 | -0.06 | 37.42 | xxxx |  | 4.8% | 6 | 1.06 | 42% | 43% | 67% | 0 |
| 17 | MICROSOFT CORP (MSFT) | ok | 25,684 | 4.0% | C | -54,909 | 61.84 | 43.21 | 93.52 | 0.66 | 61.84 | ++++ |  | 3.4% | 7 | 0.65 | 42% | 181% | 67% | 0 (-3 brutto) |
| 18 | Primoris Services Corp (PRIM) | no growth: fewer than three revenue years (M6) | – | – | ? | – | – | – | 25.59 | – | – | – |  | – | – | – | -13% | 32% | 67% | 0 |
| 19 | OLIN CORP (OLN) | ok | 223 | 4.0%* | C | 3,394 | -5.65 | -27.52 | 30.19 | -0.19 | 1.57 | +xxx |  | 3.9% | 7 | 0.99 | -26% | 62% | 67% | 0 |
| 20 | SNYDER'S-LANCE, INC. (CIK57528) | ok | 79 | 2.2%* | C | 1,076 | -30.29 | -41.80 | – | – | 0.56 | xxxx |  | – | 5 | – | – | – | – | 0 |
| 21 | El Pollo Loco Holdings, Inc. (LOCO) | ok | 9 | 4.0% | C | 85 | 1.77 | -2.19 | 10.00 | 0.18 | 1.77 | +xx+ |  | 1.4% | – | 0.80 | 28% | 69% | 67% | 0 |
| 22 | YRC Worldwide Inc. (CIK716006) | no growth: fewer than three revenue years (M6) | – | – | ? | – | – | – | – | – | – | – |  | – | – | – | – | – | – | 0 |
| 23 | V F CORP (VFC) | no FCF0: OCF and capex in [] (M1 needs three consecutive yea | – | – | ? | – | – | – | 80.87 | – | – | – |  | – | – | – | 19% | 24% | 67% | 0 |
| 24 | CENTURYLINK, INC (LUMN) | ok | 2,409 | -3.0% | C | 37,175 | -12.66 | -23.78 | 18.58 | -0.68 | -12.66 | ++x+ |  | 3.5% | 6 | 0.59 | -32% | -9% | 67% | 0 |
| 25 | EBAY INC (EBAY) | ok | 2,136 | 1.3%* | C | 4,422 | 24.29 | 13.73 | 37.88 | 0.64 | 24.29 | ++++ |  | 5.4% | 4 | 0.93 | 3% | 52% | 67% | 0 |
| 26 | HRG GROUP, INC. (SPB) | ok | 548 | 4.0%* | C | 6,009 | -5.84 | -48.53 | 11.24 | -0.52 | 14.72 | xxxx | JA | 6.2% | – | 1.01 | -9% | 38% | 67% | 0 |
| 27 | FUTURELAND CORP. (CIK1424549) | no FCF0: OCF and capex in [] (M1 needs three consecutive yea | – | – | ? | – | – | – | – | – | – | – |  | – | – | – | – | – | – | 0 |
| 28 | LANCASTER COLONY CORP (MZTI) | ok | 115 | -0.2% | C | -179 | 56.79 | 46.06 | 125.59 | 0.45 | 56.79 | ++++ |  | 5.3% | 8 | 0.77 | 20% | 55% | 67% | 0 |
| 29 | AMEDICA Corp (SINT) | FCF0 not positive | -8 | -3.0%* | C | 2 | – | – | 1.18 | – | – | xxx+ |  | -148.0% | – | 3849.79 ! | -81% | -96% | 67% | 0 |
| 30 | Enviva Partners, LP (CIK1592057) | ok | 51 | 4.0%* |  | 400 | 36.29 | -14.29 | – | – | 36.29 | ?+x+ |  | – | – | – | – | – | – | 0 |
| 31 | National CineMedia, Inc. (NCMI) | ok | 141 | -3.0%* |  | 1,181 | 2.54 | 1.27 | 5.72 | 0.44 | 2.54 | ++x+ |  | 9.4% | – | 1.02 | 33% | -3% | 67% | 0 |
| 32 | PARK ELECTROCHEMICAL CORP (PKE) | ok | 15 | -3.0% | C | -163 | 15.39 | 13.40 | 17.03 | 0.90 | 15.39 | xx++ | JA | 5.5% | 5 | 0.95 | 21% | 12% | 67% | 0 |
| 33 | RBC Bearings INC (RBC) | ok | 74 | 4.0%* | C | 154 | 8.21 | -23.31 | 116.38 | 0.07 | 43.52 | +++x |  | 3.8% | 5 | 0.64 | 18% | 75% | 67% | 0 |
| 34 | C H ROBINSON WORLDWIDE INC (CHRW) | ok | 576 | 4.0% | C | 416 | 52.82 | 28.31 | 92.03 | 0.57 | 64.43 | +++x |  | 5.8% | 5 | 0.75 | -10% | 13% | 67% | 0 |
| 35 | NEKTAR THERAPEUTICS (NKTR) | FCF0 not positive | -99 | 4.0% | C | 245 | – | – | 83.66 | – | – | xxx+ |  | -0.4% | – | 0.22 | -62% | -77% | 67% | 0 |
| 36 | RAYTHEON CO/ (CIK1047122) | ok | 2,062 | 1.8%* |  | 2,303 | 76.50 | 58.51 | – | – | 91.50 | +++x |  | – | 6 | – | – | – | – | 0 |
| 37 | MERCADOLIBRE INC (MELI) | no growth: fewer than three revenue years (M6) | – | – | ? | – | – | – | 339.61 | – | – | – |  | – | – | – | 43% | 363% | 67% | 0 |
| 38 | NGL Energy Partners LP (NGL) | FCF0 not positive | -562 | 4.0%* | C | 2,920 | – | – | 12.65 | – | – | ?xx? |  | 5.7% | – | 1.08 | 29% | -75% | 67% | 0 |
| 39 | Premier, Inc. (CIK1577916) | no shares: no cover-page count (M5) | 270 | -3.0% |  | 45 | – | – | – | – | – | – |  | – | – | – | – | – | – | 0 |
| 40 | MATTEL INC /DE/ (MAT) | ok | 276 | -3.0% | C | 2,345 | 1.04 | -6.82 | 14.80 | 0.07 | 1.04 | +xx+ | JA | -4.6% | 2 | 1.45 | -18% | 45% | 67% | 0 |
| 41 | LogMeIn, Inc. (CIK1420302) | ok | 57 | 4.0%* | C | -365 | 18.32 | 7.09 | – | – | 24.93 | +x+x |  | – | 6 | – | – | – | – | 0 |
| 42 | ICF International, Inc. (ICFI) | ok | 82 | 4.0%* |  | 194 | 61.52 | 40.81 | 67.10 | 0.92 | 61.52 | ++++ |  | 5.7% | 8 | 0.68 | 17% | 39% | 67% | 0 |
| 43 | TIMKEN CO (TKR) | ok | 218 | -3.0%* | C | 856 | 1.71 | -10.38 | 42.75 | 0.04 | 16.47 | xxxx |  | 6.8% | 7 | 0.93 | 15% | 110% | 67% | 0 |
| 44 | Allegiant Travel CO (ALGT) | ok | 36 | -3.0% |  | 1,105 | -47.05 | -68.80 | 160.25 | -0.29 | -47.05 | +xx+ |  | 6.2% | – | 0.66 | -6% | 53% | 67% | 0 |
| 45 | CICERO INC (CIK945384) | no FCF0: OCF and capex in [] (M1 needs three consecutive yea | – | – | ? | – | – | – | – | – | – | – |  | – | – | – | – | – | – | 0 |
| 46 | ASHLAND GLOBAL HOLDINGS INC (ASH) | ok | 225 | -3.0%* | C | 2,368 | -20.00 | -37.30 | 66.18 | -0.30 | -2.65 | xxxx | JA | 2.2% | 6 | 1.08 | 23% | 36% | 67% | 0 |
| 47 | HEALTHEQUITY INC (HQY) | ok | 40 | -3.0%* |  | -241 | 10.37 | 7.52 | 65.67 | 0.16 | 10.37 | ++++ |  | 1.4% | 7 | 0.57 | 3% | 16% | 67% | 0 |
| 48 | AXON ENTERPRISE, INC. (AXON) | FCF0 not positive | -4 | 4.0% | C | -82 | – | – | 41.98 | – | – | +xx+ |  | 0.6% | 5 | 0.59 | 51% | 261% | 67% | 3 |
| 49 | U.S. SILICA HOLDINGS, INC. (CIK1524741) | FCF0 not positive | -52 | 4.0%* | C | 181 | – | – | – | – | – | +xxx |  | – | 7 | – | – | – | – | 0 |
| 50 | Playa Hotels & Resorts N.V. (CIK1692412) | ok | 14 | 4.0%* |  | 781 | -5.06 | -7.08 | – | – | -5.06 | xxx+ |  | – | – | – | – | – | – | 0 |
