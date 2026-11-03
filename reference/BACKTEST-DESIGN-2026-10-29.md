# Historiskt test av motorn — design, 2026-10-29

*Ägaren 2026-10-29: "lägg in alla nej besluten sedan skriv en design så gör vi
resten sen". Det här dokumentet är designen. Inget är byggt. Testet körs i
en ny session på ägarens ord, med prompten längst ned.*

## 1. Frågan

**Hade motorn, som den ser ut i dag (E140–E148, E145 Q1–Q5, §4.2), valt
bolag som sedan gick bättre än marknaden, om den hade körts vid tidpunkter
där svaret i dag är känt?**

Svaret delas upp i tre frågor, eftersom de kan falla olika:

1. **Värderingen.** Gav de bolag som motorn bedömde som billiga (låg kurs mot
   fv_base, alltså en hög kvot fv/kurs) högre avkastning än de som den bedömde som dyra?
   Det testar E140–E144, alltså FCF0, bryggan och den härledda tillväxten.
2. **Kvalitetsgrinden.** Gick bolag som klarade E145 Q1–Q4 bättre än de som
   inte klarade den, vid samma värdering? Det testar om grinden tar bort
   förlorare eller vinnare.
3. **Hela kedjan.** Om motorn bara får köpa det den faktiskt hade köpt
   (billig, klarar E145 och har inget mätbart hårt stopp under §4.2), hur gick
   den portföljen mot S&P 500 med återinvesterad utdelning?

Skuggboken (E114) mäter samma sak framåt, men den är två månader gammal.
Testet mäter bakåt, där facit redan finns.

## 2. Vad som kan göra testet falskt, och hur det stängs

Det här är testets viktigaste avsnitt. Ett test som ser framåt i tiden
visar alltid att metoden fungerar.

| Risk | Vad den gör | Hur den stängs |
|---|---|---|
| **Framtida data** | Motorn ser en siffra som inte var publicerad på testdagen | Varje fakta i SEC companyfacts har ett `filed`-datum. Storen byggs bara av fakta med `filed` ≤ testdagen. Testas med en revision: tre bolag kontrolleras för hand mot EDGAR. |
| **Omräknade siffror** | En senare 10-K räknar om ett äldre år, och motorn får den rättade siffran | För varje (tagg, period) används den **först inlämnade** siffran med `filed` ≤ testdagen, aldrig den senaste. |
| **Överlevnadsfel** | Urvalet består av dagens vinnare, och de som gick under saknas | Urvalet byggs av alla bolag som lämnade in en 10-K under året före testdagen (EDGAR:s fullständiga index), inte av dagens index. Bolag som senare avnoterats ligger kvar. |
| **Saknade kurser** | yfinance saknar ofta avnoterade bolag, och de försvinner tyst | Varje bolag utan kurs vid horisonten räknas och redovisas. Resultatet visas i tre versioner: utan dem, med dem satta till −100 % och med dem satta till index. Skillnaden mellan versionerna är osäkerheten. |
| **Aktiesplit** | Antalet aktier och kursen ligger på olika bas | Samma splitkorrigering som i c046701, men bara med splitar kända på testdagen. Kursen för fv/kurs är den ojusterade stängningen på testdagen. Avkastningen räknas på justerad kurs. |
| **Metoden är formad av facit** | E142–E148 skrevs i oktober 2026 efter att vi sett bolag som CENTA, BKNG och UBER | Det går inte att stänga helt, så det skrivs ut. Testets trovärdigaste del är därför **perioden före 2021**, långt från de bolag regelboken byggdes på. |
| **Mänskliga bedömningar** | Q5 ("begriplig"), E141-beslut och tillväxtvyer finns inte bakåt | Bara mekaniska delar körs: E144:s härledda tillväxt (ingen vy), Q1–Q4, och de hårda stoppen som går att mäta ur kvartalsdata (§4.2.1 omsättning, §4.2.2 marginal, §4.2.5 skuld, §4.2.7 lager och fordringar). §4.2.3 (prognossänkningar) och §4.2.6 (VD och finanschef) kräver pressmeddelanden och körs **inte**. Det skrivs ut. |
| **Valda testdagar** | En bra testdag kan få vilken metod som helst att se bra ut | Fem fasta testdagar bestäms nu, innan något körs: **30 april 2016, 2017, 2018, 2019 och 2020**. 2020 tas med medvetet, eftersom det var mitt i pandemin. |
| **Vinsten kommer från en sektor** | Allt beror på till exempel teknik 2016–2021 | Resultatet redovisas också per sektor (SIC-kod) och med och utan de fem största vinnarna. |

## 3. Urval och data

- **Bara USA.** Nordiska bolag saknar inlämningsdatum per siffra. Testet
  gäller alltså motorn, inte de nordiska handläsningarna.
- **Urval per testdag:** alla 10-K-lämnare med börsvärde ≥ 300 MUSD på
  testdagen, där börsvärdet är antal aktier enligt senaste inlämning gånger
  ojusterad kurs. Banker, försäkringsbolag och fastighetsbolag (REIT) tas bort
  med SIC-kod, eftersom motorn inte värderar dem (samma gräns som i dag).
  Uppskattat 1 500–2 500 bolag per testdag.
- **Data:**
  - SEC companyfacts, en fil per bolag, 1–5 MB. Varje fil hämtas en gång och
    används för alla fem testdagarna. Det blir 3–6 GB, som läggs i
    `data/backtest/` (24 GB ledigt) och **inte** i `/tmp`, som bara har 1,9 GB.
  - Kurser hämtas via verktygets egen kursväg (`vss.fetch.get_history`).
  - Index: `^SP500TR`, samma som skuggboken använder.
- **Horisonter:** 1, 3 och 5 år från varje testdag. 5 år från 2020 slutar
  2025-04-30 och är därmed möjligt att mäta.

## 4. Vad som mäts

För varje testdag och bolag skrivs en rad: fv_base, bear, kvoten fv/kurs, Q1–Q4,
vilka mätbara hårda stopp som slog till, och avkastning efter 1, 3 och 5 år
(totalavkastning, i USD) jämfört med `^SP500TR`.

Därefter:

1. **Kvintiler på fv/kurs.** Ger den billigaste femtedelen högst avkastning,
   och stiger avkastningen jämnt från dyr till billig? Det är det enklaste
   och ärligaste testet av värderingen.
2. **E145, klarar mot klarar inte,** inom samma kvintil.
3. **Portföljen:** bolag med kurs ≤ fv_base × 0,65 (tier 3:s kudde, den
   strängaste) som klarar Q1–Q4 och inte har något mätbart hårt stopp.
   Varje bolag får lika vikt och hålls till horisonten. Snittavkastning
   jämfört med index, andel som slog index och den sämsta enskilda förlusten.
4. **Jämförelser som motorn måste slå,** annars är den bara dyr komplexitet:
   - lågt EV/EBIT eller hög FCF-avkastning, alltså billigast först utan något av
     vår maskineri;
   - Greenblatts magiska formel, som redan finns i screenern (E6);
   - hela urvalet med lika vikt.
5. **Osäkerhet:** ett bootstrap-intervall (95 %) på portföljens överavkastning.
   Med 20–50 bolag per testdag blir intervallet brett, och det redovisas som
   det är.
6. **Tillväxttaket (E144), tillagt 2026-10-29 efter ZTS.** Samma bolag och
   testdagar körs med taket 4 % (gällande), 6 % och 8 %; allt annat lika.
   Frågan är om ett högre tak ger en *bättre rangordning* (punkt 1:s
   kvintiler och punkt 3:s portfölj), inte bara högre fv. Mäts två gånger:
   på hela urvalet, och bara på bolag som klarar Q1–Q4 — om tillväxt består
   bättre någonstans är det i bolag med hög avkastning på kapitalet.
   Varför: ZTS 2026-10-29 gav fv 79,80 vid 4 %, 97,46 vid 6 % och 108,91 vid
   8 % mot kursen 78,54 — en enda parameter flyttar beslutet. Forskningen
   (Chan, Karceski & Lakonishok 2003) säger att tillväxt knappt består, så
   förväntningen är att 4 % håller; testet ska kunna visa motsatsen.
7. **De hårda stoppen mot utfallet, tillagt 2026-10-29 efter ZTS.** Bland
   bolag som klarar Q1–Q4 och ligger under fv_base: avkastning 1 och 3 år
   för dem med ett mätbart hårt stopp (4.2.1 intäkt, 4.2.2 marginal) mot dem
   utan. Frågan är om stoppen skyddar mot värdefällor eller stänger dörren
   just när pessimismen är störst och priset bäst (Burrys köp av ZTS efter
   två prognossänkningar). **§4.2.3 (sänkt prognos) går inte att mäta**:
   prognoser står i pressmeddelanden, inte i XBRL, och kan inte klippas i
   tid mekaniskt. Testet säger därför något om 4.2.1–4.2.2 och ingenting om
   4.2.3; det redovisas så och 4.2.3 dras inte in via någon ersättare.

Punkt 6 och 7 följer regeln nedan: en ändring prövas på 2016–2018 och
godtas bara om den håller på 2019–2020. Båda frågorna är skrivna innan
någon körning med de nya taken eller uppdelningen har gjorts.

**Vad som räknas som att motorn fungerar**, bestämt nu och inte efteråt:
avkastningen stiger med kvoten fv/kurs över kvintilerna i minst 4 av 5 testdagar,
och portföljen slår både index och EV/EBIT-jämförelsen på 3 års horisont med ett
intervall som inte omfattar noll. Klarar motorn det mot index men inte mot
EV/EBIT, är slutsatsen att maskineriet inte tillför något utöver billighet.

### Om resultatet leder till ändrade regler

Testet får visa att en regel är fel, men det får inte bli verktyget som
regeln trimmas mot. **Ett förslag till ändring (tillväxttaket, bear-nivån,
kudden, en E145-gräns) prövas på testdagarna 2016–2018 och godtas bara om
det håller på 2019–2020, som inte används vid justeringen.** En ändring som
bara förbättrar den första perioden är anpassning till facit, inte en
förbättring. Varje ändring går sedan den vanliga vägen: en ny post i
FRAMEWORK-EDITS och ägarens ord.

## 5. Byggplan

Ett steg per commit. Testerna ska gå igenom i varje steg. Inget steg ändrar hur
en siffra räknas i dag. Testverktyget läser motorn men skriver aldrig till
`config/manual/`, bevakningslistan eller FRAMEWORK-EDITS.

| Steg | Vad | Filer |
|---|---|---|
| 1 | **Klippning per datum:** en funktion som tar companyfacts och en testdag och ger den store och historik som motorn hade sett, med först inlämnad siffra per period. Egna tester med påhittade fakta: en omräkning efter testdagen syns inte, och en siffra inlämnad dagen efter syns inte. | `tools/backtest/pit.py`, `tests/test_backtest_pit.py` |
| 2 | **Revision av klippningen på tre riktiga bolag** (förslag: CENTA 2019, DHI 2018, NKE 2017). Klippt store jämförs för hand mot de 10-K som fanns på testdagen. Steget går inte vidare förrän alla tre stämmer. | `reference/backtest/AUDIT-PIT.md` |
| 3 | **Urvalet:** EDGAR:s fullständiga index för 10-K per år, CIK, SIC, börsvärdesgräns. Antal per testdag skrivs ut. | `tools/backtest/universe.py` |
| 4 | **Pilot:** 50 slumpvis valda bolag, en testdag (2018). Hela tabellen läses i sin helhet. Det är här sådant som pence/pund-felet och 100x-siffror syns, så CLAUDE.md:s regel om att läsa allt gäller. | `reference/backtest/PILOT-2018.md` |
| 5 | **Full körning** av fem testdagar. Hämtningen görs en gång och lagras. Körningen tål att avbrytas och kan fortsätta där den slutade. | `data/backtest/`, `tools/backtest/run.py` |
| 6 | **Mätningen** enligt avsnitt 4, med jämförelserna och osäkerheten. | `tools/backtest/measure.py` |
| 7 | **Rapport** på svenska, med svaret först: fungerar motorn, och tillför den något utöver billighet? | `reference/backtest/RESULT-<datum>.md` |

**Storlek:**
- **Steg 1–4:** ungefär en dags arbete.
- **Steg 5:** mest väntetid på hämtningar, 2 000–3 000 filer från SEC i
  högst 10 anrop per sekund. Räkna med några timmar.
- **Steg 6–7:** en halv dag.
- **Underagenter:** Sonnet medium, endast för hämtning, aldrig för bedömning
  (CLAUDE.md).

## 6. Utanför testet

- §4.2.3 och §4.2.6, alltså prognossänkningar och avgångar i ledningen. Ett senare steg kan läsa
  dem ur 8-K item 2.02 och 5.02, som har datum, men det är ett eget arbete.
- Gate 1 (fall på 15–50 % med en daterad katalysator) och Gate 2
  (klassningen A–D). De kräver bedömning av nyheter.
- Tier och de olika kuddarna. Bara tier 3:s 0,65 används, som strängaste fall.
- Nordiska och europeiska bolag.

Testet mäter alltså **motorns mekaniska kärna**, inte hela ramverket. Visar
kärnan ingen effekt hjälper inga gates. Visar den effekt är nästa fråga om
gates och bedömningar lägger till något eller drar ifrån.

## 7. Prompt till nästa session

> Läs reference/BACKTEST-DESIGN-2026-10-29.md och gör steg 1–4 i ordning,
> commit efter varje steg. Stanna efter piloten (steg 4) och visa mig hela
> pilottabellen och revisionen från steg 2 innan full körning. Ändra ingenting
> i motorn, i config/manual/, i bevakningslistan eller i FRAMEWORK-EDITS. Det
> som avgör om testet går att lita på är avsnitt 2. Om en risk där inte kan
> stängas, säg det i stället för att gå runt den.
