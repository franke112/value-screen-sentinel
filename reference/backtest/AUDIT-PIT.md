# Revision av klippningen per datum (backtest, steg 2), 2026-10-29

*Design: `reference/BACKTEST-DESIGN-2026-10-29.md`, steg 2. Verktyg:
`tools/backtest/pit.py` (klippningen), `tools/backtest/value.py` (kedjan
genom motorn). Källdokumenten ligger i `data/backtest/audit/`.*

## Svaret först

**Klippningen stämmer för alla tre bolagen.** Varje siffra i basåret och i
roll-forward-balansen finns under rätt rad i det 10-K eller 10-Q som fanns
på EDGAR före testdagen. Ingen siffra kommer från en senare inlämning, och
nästa inlämning efter testdagen hålls ute i alla tre fallen.

**Men motorn ger inte ett värde ur den klippta storen för två av tre bolag,
och det tredje värdet är fel på grund av ett fel i motorn.** Det beror inte
på klippningen. Det beror på att motorns XBRL-väg i dag förutsätter
handarbete per bolag, som en session gör live. Det påverkar avsnitt 2:s risk
"Mänskliga bedömningar", som **inte går att stänga så som designen skrev.**
Se avsnitt 4.

## 1. Gränsen: vad som syns och vad som inte syns

| Bolag | Testdag | Senaste siffra som används | Första inlämning som hålls ute |
|---|---|---|---|
| CENTA | 2019-04-30 | 10-Q 0000887733-19-000004, 2019-02-07 (Q1 FY2019) | 10-Q 2019-05-07 (Q2) |
| DHI | 2018-04-30 | 10-Q 0000882184-18-000019, 2018-02-08 (Q1 FY2018) | 10-Q **2018-04-30**, samma dag (Q2) |
| NKE | 2017-04-30 | 10-Q 0000320187-17-000031, 2017-04-04 (Q3 FY2017) | 10-K 2017-07-20 (FY2017) |

Storarna citerar 101, 68 och 109 inlämningar. Ingen av dem har ett
`filed`-datum på eller efter testdagen (maskinkontroll av varje `filed` i
storens text).

DHI visar varför **samma dag hålls ute**. Det är strängare än designen, som
skrev "filed ≤ testdagen". DHI lämnade in sin Q2-10-Q den 30 april 2018.
EDGAR tar emot inlämningar till 17:30 ET, men kursen är stängningen klockan
16:00, så en inlämning samma dag kan ha kommit efter kursen. Regeln är
"filed < testdagen".

## 2. Siffrorna mot dokumenten

Siffrorna i storen jämfördes mot dokumenttexten, med radetiketten avläst för
varje siffra. CENTA redovisar i tusental, DHI i miljoner med en decimal och
NKE i miljoner.

**CENTA, FY2018 (10-K 2018-11-28) och Q1 FY2019 (10-Q 2019-02-07)**

| Fält | Storen | Dokumentets rad |
|---|---:|---|
| revenue | 2,215,362 | Net sales $2,215,362 |
| operating_cash_flow | 114,112 | Net cash provided by operating activities 114,112 114,309 151,426 |
| capex | −37,845 | Capital expenditures $37,845 |
| acquisitions_paid | −91,244 | Businesses acquired, net of cash acquired (91,244) |
| sbc | 11,602 | Stock-based compensation 11,602 |
| finance_costs_paid | 36,664 | Cash paid for interest $36,664 |
| finance_income_period | 3,145 | Interest income 3,145 |
| nci_dividends_paid | −1,597 | Distribution to noncontrolling interest (1,597) |
| cash (FY / roll) | 482,106 / 478,737 | Cash and cash equivalents |
| long-term debt (FY / roll) | 692,031 / 692,332 | Long-term debt |
| current debt (FY / roll) | 122 / 117 | Current portion of long-term debt |
| diluted shares (FY / roll) | 53,341 / 58,001 | Diluted 53,341 / Diluted 58,001 |

**DHI, FY2017 (10-K 2017-11-15) och Q1 FY2018 (10-Q 2018-02-08)**

| Fält | Storen | Dokumentets rad |
|---|---:|---|
| revenue | 14,091.0 | Total revenues $14,091.0 |
| operating_cash_flow | 435.1 | Net cash provided by operating activities 435.1 618.0 700.4 |
| capex | −157.3 | Expenditures for property and equipment (157.3) |
| acquisitions_paid | −4.1 | Payments related to acquisition of a business (4.1) |
| sbc | 59.2 | Stock-based compensation expense 59.2 |
| cash (FY / roll) | 1,007.8 / 920.3 | Cash and cash equivalents |
| notes payable (FY / roll) | 2,871.6 / 3,258.1 | Notes payable |
| diluted shares (FY / roll) | 378.9 / 383.8 | adjusted weighted average common shares 378.9 / 383.8 |
| shares outstanding | 374,986,079 | 374,986,079 … shares outstanding at December 31, 2017 |

**NKE, FY2016 (10-K 2016-07-21) och Q3 FY2017 (10-Q 2017-04-04)**

| Fält | Storen | Dokumentets rad |
|---|---:|---|
| revenue | 32,376 | Revenues $32,376 |
| operating_cash_flow | 3,096 | Cash provided by operations 3,096 4,680 3,013 |
| capex | −1,143 | Additions to property, plant and equipment (1,143) (963) (880) |
| sbc | 236 | Stock-based compensation 236 191 177 |
| finance_costs_paid | 70 | Cash paid … Interest, net of capitalized interest $70 |
| net_finance_costs | 19 | Interest expense (income), net 19 |
| cash (FY / roll) | 3,138 / 4,021 | Cash and equivalents |
| long-term debt (FY / roll) | 2,010 / 3,472 | Long-term debt |
| current debt (FY / roll) | 45 / 29 | E66: current portion 44 + notes payable 1 / 6 + 23 |
| diluted shares (FY / roll) | 1,742.5 / 1,686.3 | Diluted weighted average common shares outstanding |

Även de två tidigare åren i E140:s treårssnitt (kassaflöde och capex) står
som komparativ i samma 10-K och stämmer: CENTA 114,309 / 151,426, DHI 618.0 /
700.4, NKE 4,680 / 3,013.

## 3. Tre regler i klippningen som avviker från designens ordalydelse

1. **Samma dag hålls ute** (avsnitt 1). Strängare, aldrig lösare.
2. **Antal aktier behåller alla synliga inlämningar.** En split når äldre år
   bara genom att de lämnas in igen med det nya antalet. Om bara den först
   inlämnade siffran behölls skulle alla år före en split ha det gamla
   antalet mot en kurs efter splitten. Bara splitar som var inlämnade före
   testdagen syns, vilket är designens "bara splitar kända på testdagen".
3. **"Först inlämnad" gäller per tagg och period, inte per begrepp.** Ett
   omräknat värde under en ny tagg kommer därför igenom. CENTA:s omsättning
   för FY2016 och FY2017 läses ur 10-K 2018 under `Revenues`, eftersom
   motorn föredrar den taggen. Det är inget läckage, eftersom inlämningen
   ligger före testdagen. Men det visar att "först inlämnad" och "senast
   inlämnad före testdagen" inte skiljer sig så rent som designen antog.
   Skillnaden mellan de två är 146 värden för CENTA, 76 för DHI och 572 för
   NKE (de flesta är omräknade per aktie-tal efter splitar). Piloten
   redovisar hur mycket det flyttar fv.

## 4. Det klippningen inte kan rätta: motorn behöver handarbete

En live-store för ett amerikanskt bolag är `vss xbrl --annual` **plus** det
en session skriver för hand efter att ha läst 10-K. Utan det handarbetet ger
motorn inget värde. Revisionen fann följande, och varje punkt är nu en kolumn
eller en vägran i backtestens rad, aldrig en tyst standard.

| # | Vad live-storen får för hand | Vad backtesten gör | Riktning om det blir fel |
|---|---|---|---|
| a | **Räntans form** (E34.1 / E61 / E115), vald av en session | Väljs ur taggarna i reglernas egen ordning (`pit.interest_shape`). CENTA → E115, NKE → E34.1. **DHI aktiverar sin ränta och taggar ingen: vägras (FCF0 DATA MISSING).** | E115 och E61 är ensidiga och kan bara överskatta FCF0 |
| b | **Sökta nollor** för otaggade poster: NCI-utdelning (E105), pension (E35.1), ARO (E68), leasing (E35), förskottsleverans (E81) | Skrivs som E107-sökta nollor på basåret när ingen tagg i kartan svarar (`pit._searched_zeros`) | En nolla där bolaget hade en skuld **höjer** värdet. E81 har ingen tagg alls, så ett strömningsavtal (gruvbolag) syns aldrig |
| c | **Tillväxtvy** när E144 har färre än fem organiska år | **Ingen ersättning.** Bolaget får inget värde | Bolag som köper upp andra bolag (CENTA, DHI) faller ur. **Urvalet motorn kan värdera blir inte slumpmässigt.** Det är en ny risk som avsnitt 2 inte har |
| d | **Ingen händelselogg** för affärer efter basen | Tom logg | Affärer efter basen saknas i bryggan |
| e | **§4.2-stoppen** läses live ur pressmeddelanden (omsättning mot året före, marginal) | Verktyget delar själv taggad omsättning med året före och rörelseresultat med omsättning (`value.with_ratios`). Motorn gör aldrig den divisionen | §4.2.5 kräver EBITDA, och avskrivningar finns inte i storen: **CANNOT EVALUATE för alla** |

**Avsnitt 2 sa** att bara mekaniska delar körs, alltså E144:s härledda
tillväxt, Q1–Q4 och de mätbara stoppen. **Det håller inte fullt ut.** Motorns
mekaniska delar står på en store som live blir komplett först genom en
session. Punkterna a, b och e ovan ersätter det handarbetet med regler.
Punkterna c och d går inte att ersätta mekaniskt. **Backtesten mäter därför
"motorn plus backtestens ersättningar, på de bolag där E144 kan härleda
tillväxt"**, inte motorn som den körs live. Piloten visar hur stor den
skillnaden är.

## 5. Fel som revisionen hittade i motorn och i bolagens data (inte rättade, motorn är orörd)

1. **Två splitar med samma kvot slås ihop** (`vss/history.py`,
   `_annual_facts`, c046701). Splitar nycklas på `round(b/a, 1)`. NKE har två
   2:1-splitar, i december 2012 och december 2015, och bara den första
   tillämpas. År 2009–2013 står därför på halva antalet aktier.
   - Följd: vinsttillväxten per aktie blir −4,70 % per år, E144 golvar
     tillväxten till −3 % och fv blir **17,84**, mot en kurs kring 55.
   - Live påverkas inget av dagens bolag, eftersom elvaårsfönstret
     2016–2026 inte har två lika splitar. I backtesten påverkas varje bolag
     som har det.
   - Det är en kodändring i motorn och väntar på ditt ord.
2. **CENTA:s eget 10-K för FY2018 daterar kvartalen för FY2017 ett år
   fel.** Värdena för Q1–Q3 FY2018 är taggade med datumen för FY2017
   (442,011 under 2016-09-25..2016-12-24, där rätt värde är 419,498). Motorn
   föredrar taggen `Revenues` och tar det felaktiga värdet, både live och i
   backtesten. I backtesten får ett kvartal vars omsättning är exakt lika med
   året före ingen kvot, så stoppet blir CANNOT EVALUATE i stället för ett
   falskt "oförändrat".
3. **2019, ASC 842:** en kalenderårsfilare har vid testdagen 2019-04-30 ett
   10-K för 2018 (före ASC 842) och en Q1-10-Q (efter). Bryggan läser
   leasingskulden på 10-Q medan kassaflödet redan har betalat hyran. Leasing
   räknas då två gånger. Raden flaggas (`lease_transition`), och testdagen
   2019 bör redovisas med och utan de flaggade bolagen.

## 6. Status för steg 2

- **Klippningen:** godkänd för CENTA, DHI och NKE.
- **Kedjan genom motorn:**
  - CENTA: inget värde (punkt 4c);
  - DHI: inget värde (punkt 4a);
  - NKE: ett värde som är fel (punkt 5.1).
- Steg 3 och 4 genomförs enligt uppdraget, och piloten mäter täckningen.
  **Full körning bör inte göras förrän du har tagit ställning till punkt 4
  och 5.1.**
