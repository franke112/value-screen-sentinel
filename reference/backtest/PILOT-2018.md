# Pilot 2018-04-30 (backtest, steg 4), 2026-10-29

*Design: `reference/BACKTEST-DESIGN-2026-10-29.md`, steg 4. Körning:
`.venv/bin/python -m tools.backtest.pilot --date 2018-04-30` (seed
20261029). Raderna finns i `data/backtest/pilot/PILOT-2018-04-30.json`.*

## Svaret först

**Testet går inte att köra som designen är skriven. Full körning ska inte
göras.**

- **Motorn värderade 1 bolag av 50.**
  - 22 stoppades av grinden på FCF0 (ränteposten eller capex är inte taggad
    så som motorn läser den).
  - 12 stoppades på "PERIODS DO NOT MATCH" (bland dem Microsoft).
  - 11 saknar fem organiska år (E144).
  - 4 vägrades eller saknade store.

  Utfallet är detsamma oavsett om klippningen tar den först eller den senast
  inlämnade siffran. Felet sitter alltså inte i klippningen. Det sitter i att
  motorns XBRL-väg live kompletteras för hand av en session.
- **Det enda värdet ser orimligt ut:** Winnebago, fv 4,01 mot kursen 37,90.
  Bear-värdet är −0,07. Det är inte utrett, och därför kan inget dras av det.
- **16 av 50 har ingen ticker i dag och 17 saknar kurs på testdagen.**
  Designens tre versioner (utan dem, −100 %, index) gäller bolag som saknar
  kurs *vid horisonten*. Här saknas kursen redan *vid start*, så bolagen kan
  inte ens sorteras på fv/kurs. För hela urvalet 2018 gäller det 773 av 2 131
  bolag.

## Avsnitt 2: vilka risker som inte går att stänga

| Risk | Status |
|---|---|
| Framtida data | **Stängd.** Revision i steg 2: tre bolag stämmer mot EDGAR, och samma dag hålls ute |
| Omräknade siffror | **Stängd** för omräkningar efter testdagen. "Först inlämnad" gäller per tagg, se AUDIT-PIT avsnitt 3 |
| Överlevnadsfel i urvalet | **Stängd.** Urvalet byggs ur EDGAR:s fullständiga index, och storleken mäts på bolagets egen float (steg 3) |
| **Saknade kurser** | **Inte stängd.** yfinance har ingen kurs för ungefär en tredjedel av urvalet, ofta just de som försvann. Utan en kurskälla som har avnoterade bolag (CRSP, Norgate; båda kostar pengar) blir urvalet för mätningen ett överlevarurval |
| Aktiesplit | **Stängd** i klippningen. **Motorfel:** två splitar med samma kvot slås ihop (NKE, AUDIT-PIT 5.1) |
| **Mänskliga bedömningar** | **Inte stängd.** Motorns mekaniska kärna står på en store som en session gör komplett för hand. Ersättningsreglerna (räntans form, sökta nollor) räcker inte: 49 av 50 vägras ändå |
| Metoden formad av facit, testdagar, sektor | Oförändrat från designen. De kan inte prövas förrän något värderas |

## Annat som syntes vid en läsning av hela tabellen

- **Felaktig float i bolagens egen taggning.**
  - AMEDICA (#29) anger 19,4 miljarder USD vid kursen 1,18.
  - FUTURELAND (#27) anger 3,6 miljarder och CICERO (#45) 1,85 miljarder.
  - De är småbolag som kommer över gränsen på 300 MUSD på ett felaktigt
    taggat tal. En rimlighetskontroll mot antal aktier × kurs behövs, men den
    kräver kursen, som saknas för de avnoterade.
- **Ticker i dag hör inte alltid till samma aktie som då.**
  - SPB för HRG Group (#26), sammanslaget med Spectrum Brands 2018.
  - MTCH för IAC (#15), vars CIK blev Match Group 2020.
  - Kursserien kan då höra till ett annat värdepapper. Det måste kontrolleras
    per bolag och kan inte göras mekaniskt.
- **Sökta nollor används på nästan varje rad** (4–6 poster). Även om
  grinden släppte igenom fler bolag skulle bryggan för de flesta stå på
  nollor som en session aldrig har kontrollerat.

## Vad som skulle krävas: ett val för dig

1. **Testa metodens kärna i stället för motorn.** Ett eget, litet
   räkneverktyg räknar ut E140:s treårs-FCF utan rörelsekapital, E144:s
   tillväxt och Q1–Q4 direkt ur den klippta datan, med få och uttalade
   regler.
   - Det mäter idén, inte koden.
   - Koden har redan visat sig behöva handarbete per bolag.
   - **Det är min rekommendation.** Testet blir då ärligt om vad det mäter.
2. **Bygga ut den mekaniska kompletteringen** tills motorn värderar flertalet
   bolag. Det betyder i praktiken en andra, automatisk version av det en
   session gör. Det är stort, och varje ny regel är en ny källa till fel.
3. Oavsett 1 eller 2 behövs **en kurskälla med avnoterade bolag** för att
   stänga risken med saknade kurser. Annars ska resultatet redovisas som
   gällande överlevare, med den begränsningen först.

## Hela pilottabellen

Kolumner:
- **Stopp**: utlösta mätbara stopp (§4.2.1/2/5/7). Antalet som inte kunde
  bedömas står inom parentes.
- **Ränta**: räntans form. "E34" betyder att paret bildades *eller* att
  ingenting fanns.
- **Nollor**: antal sökta nollor.
- **842**: ASC 842-övergången.
- **fv senast %**: hur fv flyttar under regeln "senast inlämnad".
- **1/3/5 år**: totalavkastning i procent, med skillnaden mot `^SP500TR`
  inom parentes.

Under 300 MUSD vid den exakta float-kontrollen, och därför ersatta:
- AVID 222 M;
- Superior Uniform 228 M;
- MCBC 271 M;
- Natural Health Trends 202 M.

| # | Ticker | Bolag | SIC | Float M | Status | Kurs | fv_base | fv_bear | fv/kurs | g_base | Q1 Q2 Q3 Q4 | Stopp | Ränta | Nollor | 842 | fv senast % | 1 år | 3 år | 5 år |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | LMAT | LEMAITRE VASCULAR INC | 3841 | 405 | grind | 31.45 |  |  |  |  |  | – (2?) | E34 | 6 |  |  | -7 (-21) | +72 (+5) | +81 (+9) |
| 2 | WGO | WINNEBAGO INDUSTRIES INC | 3716 | 1,026 | ok | 37.90 | 4.01 | -0.07 | 0.11 | +4.0 | ✓ ✗ ✗ ✓ | – (1?) | E34.1 | 6 |  | +0.0 | -5 (-19) | +118 (+51) | +63 (-9) |
| 3 | HZO | MARINEMAX INC | 5531 | 500 | grind | 21.60 |  |  |  |  |  | 4.2.7 (1?) | E34 | 6 |  |  | -20 (-33) | +163 (+96) | +35 (-37) |
| 4 | – | Legacy Education Alliance, I | 8200 | 729 | ingen tillväxt (E144) |  |  |  |  |  |  | – (4?) | E115 | 6 |  |  |  |  |  |
| 5 | NJR | NEW JERSEY RESOURCES CORP | 4924 | 3,357 | grind | 41.35 |  |  |  |  |  | – (4?) | E115 | 5 |  |  | +24 (+11) | +11 (-56) | +47 (-25) |
| 6 | – | 2U, Inc. | 7372 | 2,219 | grind: FCF0 |  |  |  |  |  |  | – (4?) | E34 | 6 |  |  |  |  |  |
| 7 | PK | Park Hotels & Resorts Inc. | 7011 | 3,863 | ingen tillväxt (E144) | 28.78 |  |  |  |  |  | – (2?) | E34 | 5 |  |  | +23 (+9) | -5 (-72) | -47 (-119) |
| 8 | HAL | HALLIBURTON CO | 1389 | 37,084 | grind: FCF0 | 52.99 |  |  |  |  |  | – (2?) | E34.1 | 5 |  |  | -45 (-59) | -60 (-128) | -32 (-104) |
| 9 | – | Bristow Group Inc | 4522 | 450 | grind: FCF0 |  |  |  |  |  |  | – (2?) | E34 | 4 |  |  |  |  |  |
| 10 | GTHP | GUIDED THERAPEUTICS INC | 3845 | 300 | grind: FCF0 |  |  |  |  |  |  | – (4?) | E115 | 6 |  |  |  |  |  |
| 11 | – | AMEDISYS INC | 8082 | 1,500 | grind: FCF0 |  |  |  |  |  |  | – (4?) | E34 | 5 |  |  |  |  |  |
| 12 | – | OCLARO, INC. | 3674 | 1,464 | ingen store |  |  |  |  |  |  | – | E34 | 0 |  |  |  |  |  |
| 13 | ASPS | Altisource Portfolio Solutio | 7380 | 385 | grind: FCF0 | 27.38 |  |  |  |  |  | 4.2.1,4.2.2 (2?) | E34 | 5 |  |  | -14 (-27) | -77 (-144) | -86 (-158) |
| 14 | – | TransMontaigne Partners L.P. | 4610 | 543 | ingen tillväxt (E144) |  |  |  |  |  |  | – (2?) | E115 | 6 |  |  |  |  |  |
| 15 | MTCH | IAC/INTERACTIVECORP | 7370 | 7,529 | ingen tillväxt (E144) | 165.01 |  |  |  |  |  | – (2?) | E115 | 5 |  |  | +35 (+21) | +247 (+180) | -18 (-90) |
| 16 | POST | Post Holdings, Inc. | 2040 | 5,522 | grind: FCF0 | 79.57 |  |  |  |  |  | – (4?) | E34 | 5 |  |  | +42 (+28) | +43 (-24) | +74 (+2) |
| 17 | MSFT | MICROSOFT CORP | 7372 | 466,500 | grind | 93.52 |  |  |  |  |  | – (1?) | E34 | 4 |  |  | +42 (+29) | +181 (+114) | +248 (+176) |
| 18 | PRIM | Primoris Services Corp | 1623 | 1,020 | ingen tillväxt (E144) | 25.59 |  |  |  |  |  | – (4?) | E115 | 6 |  |  | -13 (-27) | +32 (-35) | +4 (-67) |
| 19 | OLN | OLIN CORP | 2800 | 5,009 | ingen tillväxt (E144) | 30.19 |  |  |  |  |  | – (3?) | E115 | 4 |  |  | -26 (-39) | +62 (-6) | +114 (+42) |
| 20 | – | SNYDER'S-LANCE, INC. | 2052 | 2,604 | grind: FCF0 |  |  |  |  |  |  | – (4?) | E34 | 6 |  |  |  |  |  |
| 21 | LOCO | El Pollo Loco Holdings, Inc. | 5812 | 308 | inget värde | 10.00 |  |  |  | +4.0 |  | – (2?) | E34 | 6 |  |  | +28 (+14) | +69 (+2) | +8 (-64) |
| 22 | – | YRC Worldwide Inc. | 4213 | 364 | grind: FCF0 |  |  |  |  |  |  | – (4?) | E34 | 5 |  |  |  |  |  |
| 23 | VFC | V F CORP | 2320 | 18,323 | grind: FCF0 | 80.87 |  |  |  |  |  | – (1?) | E34 | 5 |  |  | +19 (+6) | +24 (-43) | -64 (-136) |
| 24 | LUMN | CENTURYLINK, INC | 4813 | 11,700 | inget värde | 18.58 |  |  |  | -3.0 |  | – (2?) | E115 | 4 |  |  | -32 (-45) | -9 (-76) | -81 (-153) |
| 25 | EBAY | EBAY INC | 7389 | 34,909 | grind: FCF0 | 37.88 |  |  |  |  |  | – (2?) | E34 | 6 |  |  | +3 (-11) | +52 (-15) | +31 (-41) |
| 26 | SPB | HRG GROUP, INC. | 3690 | 2,287 | grind: FCF0 | 11.24 |  |  |  |  |  | 4.2.2 (2?) | E34 | 5 |  |  | -9 (-23) | +38 (-30) | +9 (-63) |
| 27 | – | FUTURELAND CORP. | 5900 | 3,620 | grind: FCF0 |  |  |  |  |  |  | – (4?) | E115 | 6 |  |  |  |  |  |
| 28 | MZTI | LANCASTER COLONY CORP | 2030 | 2,638 | grind: FCF0 | 125.59 |  |  |  |  |  | – (4?) | E34 | 6 |  |  | +20 (+7) | +55 (-12) | +82 (+10) |
| 29 | SINT | AMEDICA Corp | 3841 | 19,429 | grind | 1.18 |  |  |  |  |  | – (4?) | E115 | 6 |  |  | -81 (-94) | -96 (-163) | -100 (-172) |
| 30 | – | Enviva Partners, LP | 2400 | 359 | ingen tillväxt (E144) |  |  |  |  |  |  | – (2?) | E115 | 6 |  |  |  |  |  |
| 31 | NCMI | National CineMedia, Inc. | 7310 | 460 | grind | 5.72 |  |  |  |  |  | – (2?) | E34 | 5 |  |  | +33 (+20) | -3 (-70) | -92 (-164) |
| 32 | PKE | PARK ELECTROCHEMICAL CORP | 3728 | 326 | grind | 17.03 |  |  |  |  |  | 4.2.2,4.2.7 (1?) | E34 | 6 |  |  | +21 (+8) | +12 (-55) | +24 (-48) |
| 33 | RBC | RBC Bearings INC | 3562 | 1,817 | grind | 116.38 |  |  |  |  |  | – (2?) | E34 | 5 |  |  | +18 (+5) | +75 (+7) | +107 (+35) |
| 34 | CHRW | C H ROBINSON WORLDWIDE INC | 4731 | 9,616 | grind: FCF0 | 92.03 |  |  |  |  |  | – (2?) | E34 | 6 |  |  | -10 (-24) | +13 (-54) | +23 (-49) |
| 35 | NKTR | NEKTAR THERAPEUTICS | 2834 | 3,029 | grind | 83.66 |  |  |  |  |  | – (1?) | E34 | 6 |  |  | -62 (-75) | -77 (-144) | -99 (-171) |
| 36 | – | RAYTHEON CO/ | 3812 | 46,800 | grind: FCF0 |  |  |  |  |  |  | – (2?) | E34 | 4 |  |  |  |  |  |
| 37 | MELI | MERCADOLIBRE INC | 7389 | 8,522 | ingen tillväxt (E144) | 339.61 |  |  |  |  |  | – (4?) | E115 | 6 |  |  | +43 (+29) | +363 (+295) | +276 (+204) |
| 38 | NGL | NGL Energy Partners LP | 4922 | 1,654 | ingen tillväxt (E144) | 12.65 |  |  |  |  |  | – (1?) | E115 | 4 |  |  | +29 (+16) | -75 (-142) | -66 (-138) |
| 39 | – | Premier, Inc. | 8741 | 1,501 | store vägrad |  |  |  |  |  |  | – | E34 | 5 |  |  |  |  |  |
| 40 | MAT | MATTEL INC /DE/ | 3942 | 7,402 | grind: FCF0 | 14.80 |  |  |  |  |  | 4.2.1,4.2.2 (1?) | E34 | 5 |  |  | -18 (-31) | +45 (-22) | +22 (-50) |
| 41 | – | LogMeIn, Inc. | 7372 | 4,855 | grind |  |  |  |  |  |  | – (2?) | E34 | 6 |  |  |  |  |  |
| 42 | ICFI | ICF International, Inc. | 8742 | 855 | grind | 67.10 |  |  |  |  |  | – (2?) | E34 | 6 |  |  | +17 (+3) | +39 (-28) | +76 (+4) |
| 43 | TKR | TIMKEN CO | 3562 | 3,097 | grind: FCF0 | 42.75 |  |  |  |  |  | – (4?) | E34 | 4 |  |  | +15 (+2) | +110 (+43) | +99 (+27) |
| 44 | ALGT | Allegiant Travel CO | 4512 | 1,699 | grind: FCF0 | 160.25 |  |  |  |  |  | – (2?) | E34 | 6 |  |  | -6 (-20) | +53 (-14) | -33 (-104) |
| 45 | – | CICERO INC | 7371 | 1,850 | grind: FCF0 |  |  |  |  |  |  | – (4?) | E115 | 6 |  |  |  |  |  |
| 46 | ASH | ASHLAND GLOBAL HOLDINGS INC | 5160 | 4,431 | ingen tillväxt (E144) | 66.18 |  |  |  |  |  | 4.2.2 (2?) | E34 | 4 |  |  | +23 (+10) | +36 (-31) | +64 (-8) |
| 47 | HQY | HEALTHEQUITY INC | 7389 | 2,300 | grind: FCF0 | 65.67 |  |  |  |  |  | – (2?) | E34 | 6 |  |  | +3 (-10) | +16 (-51) | -19 (-91) |
| 48 | AXON | AXON ENTERPRISE, INC. | 3480 | 1,303 | grind | 41.98 |  |  |  |  |  | – (3?) | E34.1 | 6 |  |  | +51 (+38) | +261 (+194) | +402 (+330) |
| 49 | – | U.S. SILICA HOLDINGS, INC. | 1400 | 2,871 | grind: FCF0 |  |  |  |  |  |  | – (3?) | E34 | 4 |  |  |  |  |  |
| 50 | – | Playa Hotels & Resorts N.V. | 7011 | 639 | ingen tillväxt (E144) |  |  |  |  |  |  | – (2?) | E115 | 6 |  |  |  |  |  |

## Varför inget värde

- **1 LMAT**: gate refused: PERIODS DO NOT MATCH: operating_cash_flow covers another twelve months, and the basis ends 2017-12-31
- **3 HZO**: gate refused: PERIODS DO NOT MATCH: operating_cash_flow covers another twelve months, and the basis ends 2017-09-30
- **4 Legacy Education Alliance, Inc.**: no growth: fewer than five organic years (E144(4) needs a view)
- **5 NJR**: gate refused: PERIODS DO NOT MATCH: operating_cash_flow covers another twelve months, and the basis ends 2017-09-30; PERIODS DO NOT MATCH: operating_cash_flow covers another twelve months, and the basis ends 2017-09-30
- **6 2U, Inc.**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **7 PK**: no growth: fewer than five organic years (E144(4) needs a view)
- **8 HAL**: gate refused: FCF0 DATA MISSING: sbc covers another twelve months, and the basis ends 2017-12-31. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.; PERIODS DO NOT MATCH: sbc covers another twelve months, and the basis ends 2017-12-31
- **9 Bristow Group Inc**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **10 GTHP**: gate refused: FCF0 DATA MISSING: capex_ppe, capex_intangibles is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.; PERIODS DO NOT MATCH: financial_liabilities_noncurrent is stated at 2016-12-31, and the basi
- **11 AMEDISYS INC**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **12 OCLARO, INC.**: no store: XbrlError: CIK1110647: no annual facts visible on 2018-04-30
- **13 ASPS**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **14 TransMontaigne Partners L.P.**: no growth: fewer than five organic years (E144(4) needs a view)
- **15 MTCH**: no growth: fewer than five organic years (E144(4) needs a view)
- **16 POST**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **17 MSFT**: gate refused: PERIODS DO NOT MATCH: operating_cash_flow covers another twelve months, and the basis ends 2017-06-30
- **18 PRIM**: no growth: fewer than five organic years (E144(4) needs a view)
- **19 OLN**: no growth: fewer than five organic years (E144(4) needs a view)
- **20 SNYDER'S-LANCE, INC.**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **21 LOCO**: no value: RecordError: LOCO: the run record is INCOMPLETE and section 5 does not print a fair value from it. Absent: operating cash flow (declaration 8); net interest paid (declaration 3); E140 FCF0 -- E140: operating cash flow for annual FY2015 is DATA MISSING -- every leg of every year of the mean
- **22 YRC Worldwide Inc.**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **23 VFC**: gate refused: FCF0 DATA MISSING: capex_ppe, capex_intangibles, net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **24 LUMN**: no value: RecordError: LUMN: the run record is INCOMPLETE and section 5 does not print a fair value from it. Absent: operating cash flow (declaration 8); E140 FCF0 -- E140: operating cash flow for annual FY2015 is DATA MISSING -- every leg of every year of the mean is stated, and a year with no acqu
- **25 EBAY**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **26 SPB**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **27 FUTURELAND CORP.**: gate refused: FCF0 DATA MISSING: capex_ppe, capex_intangibles, sbc is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **28 MZTI**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **29 SINT**: gate refused: PERIODS DO NOT MATCH: financial_liabilities_noncurrent is stated at 2016-12-31, and the basis ends 2017-12-31
- **30 Enviva Partners, LP**: no growth: fewer than five organic years (E144(4) needs a view)
- **31 NCMI**: gate refused: PERIODS DO NOT MATCH: financial_liabilities_current is stated at 2013-12-26, and the basis ends 2017-12-28
- **32 PKE**: gate refused: PERIODS DO NOT MATCH: operating_cash_flow covers another twelve months, and the basis ends 2017-02-26
- **33 RBC**: gate refused: PERIODS DO NOT MATCH: operating_cash_flow covers another twelve months, and the basis ends 2017-04-01
- **34 CHRW**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **35 NKTR**: gate refused: PERIODS DO NOT MATCH: operating_cash_flow covers another twelve months, and the basis ends 2017-12-31
- **36 RAYTHEON CO/**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **37 MELI**: no growth: fewer than five organic years (E144(4) needs a view)
- **38 NGL**: no growth: fewer than five organic years (E144(4) needs a view)
- **39 Premier, Inc.**: store refused: ManualError: <pit CIK1577916 2018-04-30>: file: cash_and_equivalents jumps by 248,817,000x between FY2013 (1) and FY2016 (248,817,000). That is a UNIT MIX, not a business event: one report states millions where another states whole units. Re-read the odd periods from one document in o
- **40 MAT**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **41 LogMeIn, Inc.**: gate refused: PERIODS DO NOT MATCH: operating_cash_flow covers another twelve months, and the basis ends 2017-12-31
- **42 ICFI**: gate refused: PERIODS DO NOT MATCH: operating_cash_flow covers another twelve months, and the basis ends 2017-12-31
- **43 TKR**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **44 ALGT**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **45 CICERO INC**: gate refused: FCF0 DATA MISSING: capex_ppe, capex_intangibles is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.; PERIODS DO NOT MATCH: financial_liabilities_noncurrent is stated at 2013-12-31, and the basi
- **46 ASH**: no growth: fewer than five organic years (E144(4) needs a view)
- **47 HQY**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2018. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **48 AXON**: gate refused: PERIODS DO NOT MATCH: financial_liabilities_current is stated at 2015-12-31, financial_liabilities_noncurrent is stated at 2015-12-31, and the basis ends 2017-12-31
- **49 U.S. SILICA HOLDINGS, INC.**: gate refused: FCF0 DATA MISSING: net_interest_paid is not on the basis annual FY2017. FCF0 is the ONE flow section 5 discounts (E34); without it there is no fair value to strike and nothing here estimates one.
- **50 Playa Hotels & Resorts N.V.**: no growth: fewer than five organic years (E144(4) needs a view)
