# Nyhetsfall — design för ett tredje spår, 2026-10-29

Ägaren, 2026-10-29: köp stora, stabila bolag som fallit kraftigt den senaste
veckan på en nyhet som inte rör vad bolaget faktiskt gör ("skandaler" som folk
överreagerar på), när motorn säger att de är undervärderade bara på grund av
nyheten; sälj när kursen nått fair value. Ett parallellt spår, inte en ändring
av metoden. "Det viktigaste är vilken nyhet som är värdig, hur den ska tolkas,
och för vilken typ av bolag."

Ingenting här är byggt. Designen ska läsas och godkännas först, som
BACKTEST-DESIGN.

## 1. Kort svar från forskningen

**Ägarens intuition har stöd, men bara för hälften av fallen — och hälften
som ser ut som den rätta är den farliga.**

- **Kursfall med nyheter som rör bolagets affär fortsätter falla; kursfall
  utan sådan nyhet studsar tillbaka.** Chan (2003, JFE 70) fann stark
  fortsatt nedgång ("drift") efter dåliga nyheter och återhämtning efter
  extrema rörelser utan offentlig nyhet. Savor (2012, JFE 106) fann samma sak
  med analytikerrapporter som mått på information: stora rörelser som bär
  information fortsätter, de som inte gör det vänder. Han tolkar det som att
  marknaden *under*reagerar på verklig information och *över*reagerar på
  annat.
- **Effekten är starkast i små och illikvida bolag** (Chan). I stora bolag är
  den mindre, så vi kan inte räkna med att "stort fall = köp" ger något av sig
  självt. Kanten måste komma från klassningen och från värderingen.
- **Bokföringsfusk är aldrig en överreaktion.** Karpoff, Lee & Martin (2008,
  JFQA 43, 585 bolag): för varje dollar ett bolag blåst upp sitt värde förlorar
  det den dollarn plus 3,08 dollar till när det avslöjas, varav 2,71 är förlorat
  rykte (lägre försäljning, dyrare avtal). Marknaden straffar inte för hårt —
  den straffar rätt eller för lite.
- **Resultat- och prognosbesked ger fortsatt drift** (post-earnings
  announcement drift, Bernard & Thomas 1989 — citerat ur minnet). ZTS 2026 är
  precis det fallet: två prognossänkningar, kursen fortsatte ned från 111 till
  69.
- **Tvångsförsäljning vänder.** Coval & Stafford (2007; arbetspapper NBER
  11357): när fonder måste sälja på grund av utflöden pressas priset och
  återhämtar sig sedan — priset rörde sig utan att något om bolaget ändrats.
- **Smitta till andra bolag vänder ofta, men inte alltid.** Studier av
  kinesiska aktier (Pacific Accounting Review, 2023-ish, bara abstrakt läst)
  fann att konkurrenters kurser rör sig på ett branschledande bolags nyheter och
  sedan vänder inom ett kvartal. Men smitta efter bokföringsomräkningar
  (Gleason, Rahman & Stice 2008) drabbar konkurrenter med *liknande* bokföring
  hårdare — där är smittan information, inte brus.

**Slutsatsen som styr designen:** frågan är inte "är nyheten en skandal?"
utan **"ändrar nyheten bolagets framtida kassaflöde, och i så fall med hur
mycket jämfört med vad kursen tappade?"** En skandal som ändrar kassaflödet
(fusk, förlorad kund, säkerhetsproblem i kärnprodukten) är information. En
som inte gör det, eller vars kostnad kan sättas ett tak på långt under
kursfallet, är brus.

## 2. Nyhetsklassning — kärnan

Varje kandidat får EN klass, skriven i en fil med källan citerad (8-K,
pressmeddelande, domstolshandling), innan något pris eller fv visas för
klassningen. Samma ordning som E28 för tillväxtsynen: klassen får inte
formas av hur billig aktien ser ut.

### Klass A — brus: får köpas (efter steg 3–4)

| Kod | Vad | Exempel på bevis | Varför det vänder |
|---|---|---|---|
| A1 | **Smitta:** bolaget faller på ett *annat* bolags nyhet eller en branschrörelse, och inget eget 8-K eller pressmeddelande finns i fönstret | konkurrentens rapport; ett branschindex föll | ingen information om bolaget självt (Chan, Savor); peer-studier |
| A2 | **Tvingad eller teknisk försäljning:** borttagning ur index, en storägare säljer ett block, spin-off som säljs av fonder som inte får äga den, fondlikvidation | indexleverantörens besked; 13D/Form 4/144; prospekt för blockförsäljning | Coval & Stafford |
| A3 | **Rubrik med kostnadstak:** stämning, böter, politiskt utspel, personlig skandal hos en chef som inte är VD/CFO, kortsäljarrapport *utan* bokföringsanklagelser, cyberincident | bolagets egen uppgift om belopp; domstolens yrkande; 8-K item 1.05 med kostnad | kostnaden kan sättas ett tak på (steg 3) |

### Klass B — information: köps aldrig i detta spår

| Kod | Vad | Varför |
|---|---|---|
| B1 | Resultat, prognos, vinstvarning (8-K 2.02, eller nyheten är bolagets egen siffra) | drift (PEAD); ZTS |
| B2 | Bokföring: omräkning, 8-K 4.02 (non-reliance), revisorsbyte 4.01, väsentlig brist i intern kontroll, SEC-utredning om räkenskaperna, kortsäljare med bokföringsanklagelser som bolaget inte vederlägger med siffror | Karpoff m.fl.: rykteskostnaden är 3× |
| B3 | Förlorad kund, kontrakt, licens, patent eller produkt som står för mer än 10 % av intäkterna | kassaflödet ändras på riktigt |
| B4 | Säkerhets- eller kvalitetsproblem i en produkt som står för mer än 10 % av intäkterna (återkallelse, varningstext, förbud) | efterfrågan på kärnprodukten |
| B5 | Regeländring som ändrar affärsmodellen (prisreglering, förbud, skatt riktad mot branschen) | varaktig |
| B6 | VD **och** CFO lämnar, utdelning sänks, kovenantbrott, going concern | ramverkets egna stoppregler (§4.2) |

### Klass C — gråzon: köps bara om kostnadstaket håller

Stämningar och utredningar vars utfall kan bli stort (massprocesser,
miljöskador, konkurrensmål). De behandlas som A3 **bara** om ett tak kan
läsas ur primärkällor. Annars är de B. Exempel från minnet, inte
kontrollerade: Bayer/Roundup, 3M/hörselskydd — där överskred kostnaden vad
många trodde vid första fallet.

### Regler som gäller alla klasser

1. **Ett eget 8-K i fönstret läses alltid, oavsett klass.** Item 2.02, 4.01,
   4.02 och 5.02 (VD/CFO) ger klass B direkt, utan att en session behöver
   tolka något.
2. **Är fönstret en rapportvecka** (10-Q/10-K eller 2.02 inom ±5 handelsdagar)
   **är fallet B1** om inte bolaget bevisligen höll prognosen och fallet kom
   från något annat.
3. **Osäker → B.** Klass A kräver ett citerat bevis; avsaknad av bevis för B
   räcker inte.
4. **Ett beslut per händelse**, daterat, med källan, och aldrig ändrat i
   efterhand. Ändras bilden kommer en ny post.

## 3. Kostnadstaket — det kvantitativa testet

För klass A3 och C: **kursfallet i dollar jämfört med det värsta rimliga
kostnadsutfallet.**

    fall i börsvärde  = (kurs före − kurs nu) × aktier
    kostnadstak      = högsta belopp primärkällorna stöder (yrkat belopp,
                       lagstadgat maxbötesbelopp, bolagets egen avsättning
                       × 3 om bara avsättningen finns)
    marginal         = fall i börsvärde / kostnadstak

Köp kräver **marginal ≥ 3**: marknaden har dragit av minst tre gånger det
värsta rimliga utfallet. Siffran 3 är vald efter Karpoff-multipeln (rykte ≈ 3×
direkt kostnad) så att även ett rykteslyft av den storleken ryms. Ett tak som
inte går att läsa ur en primärkälla gör händelsen till B.

## 4. Vilka bolag

Bolaget ska ha varit köpvärt *före* nyheten, bortsett från priset:

- **Stort:** börsvärde ≥ 10 mdr USD före fallet (ägarens "stora"; och där
  läckage av verklig information är minst och likviditeten störst).
- **E145 Q1–Q4 klarar** på senaste rapport före händelsen.
- **Inget hårt stopp (§4.2) fanns före händelsen.**
- **Inte cykliskt eller råvarubolag** (E143(3)) — där är ett kursfall ofta
  cykeln, inte brus.
- **Spridd intäkt:** ingen enskild produkt eller kund > 25 % (så att en
  A3-händelse inte kan vara en dold B3/B4).

## 5. Trigger — den dagliga screenern

Körs efter stängning, samma timer-mönster som `vss watch`.

- **Fall:** ≥ 10 % på högst 5 handelsdagar, **efter att indexets och
  branschens rörelse dragits bort** (bolaget mot `^SP500TR` och mot sin
  sektor-ETF). Ett marknadsras är inte en nyhet om bolaget och hör till ett
  eget beslut.
- **Universum:** S&P 500 till att börja med (stora, likvida, tickers som
  vendorn håller). Stockholmsbörsens storbolag senare om spåret fungerar.
- **Ut:** en rad per kandidat med fallets storlek, egna 8-K i fönstret med
  item-nummer, om fönstret är en rapportvecka, och börsvärde före.
- **Mekanisk förklassning:** 2.02/4.01/4.02/5.02 eller rapportvecka → B direkt;
  resten till sessionen.

### Tre regler från första körningen (2026-10-29)

- **Rapport på väg = B (`B-pre-report`):** leverantörens nästa rapportdatum
  ligger inom 10 dagar från stängningen, och stängningsdagen själv räknas
  med. Ett fall strax före en rapport är marknaden som gissar på rapporten
  (FICO, RDDT, CTVA).
- **Avknoppning eller split (`series`):** ett 8-K item 2.01, en split i
  leverantörens serie eller en endagsrörelse ≤ −40 % i fönstret. Läs serien
  innan något annat (CTVA:s "−84 %" 2026-10-01).
- **Stockholm utan post i `config/nordic_issuers.yaml`:** börsflödets bolag
  används när namnet är exakt lika utan "(publ)", skiljetecken och bolagsform
  ("Intrum AB (publ)" = "Intrum"), och då bara en kandidat. Matchningen står
  på raden. Ingenting skrivs till config.

## 6. Från kandidat till köp

1. **Screenern** flaggar (§5).
2. **Sessionen klassar** (§2) från primärkällor och skriver
   `reference/news-drops/<TICKER>-<datum>.md`: klass, bevis, och för A3/C
   kostnadstaket (§3). Ingen fv har visats än.
3. **Motorn värderar** som vanligt (store, E140, E144, E145) på bokslutet före
   händelsen. Klass A3/C: kostnadstaket dras från fv per aktie.
4. **Köpgräns:** kurs ≤ 0,80 × justerat fv (minst 25 % upp till fv, eftersom
   försäljning sker vid fv — kudden är hela vinsten).
5. **Ägaren lägger ordern.** Spåret skriver aldrig watchlistan och lägger
   aldrig order.

## 7. Försäljning

- **Vid fv:** säljgräns på justerat fv när köpet görs.
- **Tidsstopp:** 12 månader. Har kursen inte nått fv på ett år var nyheten
  troligen information, och pengarna behövs bättre någon annanstans.
- **Ny B-händelse** under innehavet → sälj.
- **Storlek:** högst 3 % av portföljen per innehav, högst ~10 % i spåret
  totalt (av ägarens ~30 % utanför Avanza Zero). Förslag; ägarens beslut.

## 8. Hur det testas innan riktiga pengar

**a) Bakåt (det som går).** Kurser och SEC:s inlämningar finns redan för
2016–2025 (`data/backtest/`):

- händelser: alla S&P 500-liknande bolag (float ≥ 10 mdr) med ett fall ≥ 10 %
  på 5 dagar utöver index;
- mekanisk klass: rapportvecka eller eget 8-K 2.02/4.01/4.02/5.02 i fönstret
  = B; inget eget 8-K i fönstret = "A-kandidat";
- mät: överavkastning efter 1, 3, 6 och 12 månader, och andel som nått fv
  (metodens fv från `method.py`) inom 12 månader, för A-kandidater mot B.

Förväntan enligt litteraturen: B fortsätter falla, A återhämtar sig något —
men i stora bolag kanske lite. **Den fina klassningen (A3, kostnadstak) går
inte att göra bakåt**: nyhetstexter finns inte klippta i tid. Bakåttestet
prövar bara grovsorteringen.

**b) Framåt i skuggläge.** Screenern och klassningen körs dagligen i 6
månader utan pengar. Varje beslut loggas med datum och utfall, som
skuggboken (E114). Spåret får riktiga pengar först om A-klassens utfall slår
index och B-klassens efter de 6 månaderna, och ägaren säger ja.

**c) Ägarens egna affärer.** En lista (bolag, datum, köp, sälj, vad nyheten
var) läses som belägg — men med vetskap om att man minns sina vinnare bättre
än sina förlorare.

## 9. Ägarens beslut innan något byggs

1. Fallgräns och fönster: 10 % på 5 dagar?
2. Universum: bara S&P 500 först, eller Stockholm med från början?
3. Storlek: 3 % per innehav, 10 % totalt?
4. Kudde: 0,80 × fv?
5. Ägarens tidigare affärer i spåret — kan de listas?

### Besluten, 2026-10-29

Ägaren svarade på 1, 2 och 5; 3 och 4 beslutade av sessionen (E141), ändras
på ägarens ord.

1. **Trigger:** fall ≥ 10 % utöver index på högst 5 handelsdagar. Ett fall
   ≥ 5 % utöver index på EN dag ger en **tidig flagga** (bevakas, klassas
   direkt, men köpregeln kräver fortfarande 10 % på 5 dagar eller köpgränsen
   i §6).
2. **Universum:** S&P 500 och Stockholmsbörsens Large Cap från början. Svenska
   bolag lämnar inga 8-K: deras nyheter läses ur börsens eget flöde (`vss
   nordic`), och de mekaniska B-reglerna i §2 översätts till deras
   motsvarigheter (delårsrapport, vinstvarning, insiderinformation enligt
   MAR art. 17).
3. **Storlek:** högst 3 % av portföljen per innehav, högst 10 % i spåret.
4. **Köpgräns:** 0,80 × justerat fv.
5. **Ägarens egna affärer:** Unilever, UnitedHealth (efter mordet på
   UnitedHealthcares VD i december 2024 och kritiken av hur bolaget tjänar
   pengar), Micron (september 2025 — köpt på *nyhetens* momentum, inte på ett
   fall).

**UnitedHealth är ett prov för klassningen.** Mordet och kritiken (december
2024) ser ut som A3. Men under 2025 kom information: prognosen drogs in, VD
byttes och en utredning om Medicare-debitering blev känd (ur minnet, ej
kontrollerat), och kursen föll långt under nivån efter mordet. Under
designens regler hade det första köpet varit tillåtet och den nya
B-händelsen hade tvingat fram en försäljning (§7). Köp- och säljdatum behövs
för att se hur det faktiskt gick.

**Micron är den andra halvan av samma forskning.** Savor (2012) och Chan
(2003) fann att kursrörelser som *bär* information fortsätter i samma
riktning — också uppåt. Att köpa tidigt på en verklig, positiv nyhet
(efterfrågan på AI-minne) är det beteendet, inte motsatsen till spåret. Det
läggs till som **ett andra ben att testa, inte att bygga**: uppgångar ≥ 10 %
på 5 dagar med eget informationsbärande besked (2.02 med höjd prognos, stor
order) mot uppgångar utan. Bakåttestet mäter båda benen; byggs bara det som
håller.

## 10. Byggplan

1. Bakåttestet (§8a) på befintlig data → `reference/news-drops/BACKTEST.md`,
   med båda benen: fall utan eget besked (vändning) och uppgångar med eget
   besked (fortsättning). Bara USA bakåt — Stockholms nyhetsflöde finns inte
   klippt i tid här.
2. Screenern (§5) som `vss newsdrop`, skuggläge, ntfy bara till ägaren.
3. Klassningsmallen (§2–3) som fil per händelse, med tester för de mekaniska
   B-reglerna.
4. Sex månaders skugglogg, sedan beslut.

Källor (länkar):
[Chan 2003](https://academicnewsletter.sufe.edu.cn/info/357702),
[Savor 2012](https://repository.upenn.edu/fnce_papers/387),
[Karpoff, Lee & Martin 2008](https://ideas.repec.org/a/cup/jfinqa/v43y2008i03p581-611_00.html),
[Coval & Stafford (NBER 11357)](https://www.nber.org/papers/w11357.pdf),
[peer-nyheter, Pacific Accounting Review](https://doi.org/10.1108/PAR-08-2022-0110),
[Gleason, Rahman & Stice 2008](https://iro.uiowa.edu/esploro/outputs/journalArticle/The-Contagion-Effects-of-Accounting-Restatements/9984380451102771).
Bernard & Thomas, Bayer- och 3M-exemplen är ur minnet och inte kontrollerade.
