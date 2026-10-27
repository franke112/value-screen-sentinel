# Uppdrag: en värderingsmaskin som tänker som Warren Buffett

*Skriven 2026-10-27 för en ny Opus-session i ~/stocks. Ägaren startar sessionen
och klistrar in: "Läs reference/METHOD-REBUILD-PROMPT-2026-10-27.md och gör det."*

## Vad ägaren vill ha

En maskin som för varje bolag själv tar fram **bear, base och bull fair value**,
var och en med sin egen motivering, utan att ägaren behöver avgöra något.
Ägaren ska inte besluta om leasing är skuld, vilken tillväxt som är rimlig
eller om ett förvärv var bra. Det avgör maskinen, som Warren Buffett hade gjort,
och visar hur den kom fram till det.

Allt som hittas ska in i värdet. Ett bekräftat fel som flyttar värdet 2 % rättas
lika väl som ett som flyttar det 40 %. Ingen tröskel, ingen lista med "småfel
vi lever med".

## Varför det här behövs

- CENTA värderades till 61.83 när rätt värde ligger runt 30–34. Ett enskilt
  bra år kapitaliserades.
- Efter E140 har felet möjligen svängt åt andra hållet: LIAB −33.97 och
  RBREW −24.08 (lönsamma bolag värderade under noll), PEP 51.60 mot kurs ~135.
  Ett negativt värde på ett lönsamt bolag är ett räknefel tills motsatsen är
  visad, inte en åsikt.
- **Det viktigaste hålet:** bear/base/bull-tillväxten ("view", t.ex. 3/1/5)
  sätts i dag för hand per namn. Det är där ägaren dras in och där värdet
  styrs mest. Den ska i stället härledas ur bolagets historik och läge.

## Vad maskinen ska väga in, per bolag

1. **Verksamheten.** Vad bolaget säljer, till vem, hur det tjänar pengar.
   Skulle Warren förstå det? Om inte: inget värde, namnet lämnar listan.
2. **Historiken, 10 år där det finns.** Omsättning, rörelsemarginal,
   ägarvinst (owner earnings: vinst + avskrivningar − underhållsinvesteringar),
   avkastning på kapitalet, hur stabilt det varit genom en lågkonjunktur.
3. **Marknaden och konkurrenterna.** Vilka de är, om bolaget vinner eller
   tappar andelar, om vallgraven blir bredare eller smalare, prissättningsmakt.
4. **Förvärven.** Vad bolaget köpt, vad det betalat, och om det som köptes
   sedan gav avkastning. En ledning som historiskt köpt dyrt och skrivit ned
   ska ge ett lägre värde, en som köpt bra ett högre.
5. **Skulden och allt som liknar skuld.** Lån, leasing, pensioner,
   tilläggsköpeskillingar, minoritetsintressen. Hur skulden använts historiskt
   och vad den skulle betyda i ett dåligt år.
6. **Ledningen och kapitalallokeringen.** Återköp på rätt eller fel nivåer,
   utdelningar, hur ärligt de redovisar.

## Hur bear, base och bull tas fram

- **Base** utgår från bolagets egen normaliserade ägarvinst och dess egen
  historiska tillväxt och avkastning på kapitalet. Avvikelse från historiken
  kräver en skriftlig orsak med källa (en konkurrent som tar andelar, ett
  förvärv som ändrar mixen).
- **Bear** är vad som händer om det svagaste rimliga utfallet inträffar:
  sämsta perioden i historiken upprepas, vallgraven krymper, förvärven
  levererar som de sämsta tidigare gjort. Den ska beskrivas i ord först,
  sedan räknas.
- **Bull** på samma sätt åt andra hållet, men aldrig bättre än bolagets
  bästa uthålliga period utan en uttalad orsak.
- Varje antagande har en källa: en sida i en årsredovisning i `sources/`,
  en siffra i storen, en namngiven konkurrent. Inget antagande utan källa.

## Bedömningsfrågorna avgörs en gång, som Warren

Skriv en **regelbok** för de frågor som återkommer, varje fråga avgjord en
gång med motivering och sedan tillämpad på alla namn:

- Är leasing skuld? Rörelseleasing vs finansiell, och hur leasingräntan räknas.
- Tilläggsköpeskillingar, pensionsunderskott, minoritetsintressen.
- Förvärv: investering för tillväxt eller underhåll? (E140/E140.1 finns, pröva dem.)
- Ett år med negativt kassaflöde, eller ett ovanligt bra år.
- Bolag som inte redovisar ett rörelseresultat (NVR).
- Cyklisk verksamhet: vilken del av cykeln normaliseras mot.
- Valuta och utländska bolag.

Frågor som redan har en regel i `reference/FRAMEWORK.md` /
`reference/FRAMEWORK-EDITS.md` prövas mot Warrens sätt att tänka. Håller
regeln, behåll den. Håller den inte, föreslå en ersättning och visa vilka
namns värden som ändras och hur mycket.

## Arbetsordning

**Fas 1 — Granska det som finns (läs, ändra inget).**
- Läs `reference/FRAMEWORK.md`, `reference/FRAMEWORK-EDITS.md` (minst E117,
  E131, E140, E140.1, E141), motorn i `vss/` (börja i `strike.py`,
  `rules.py`, `store.py`, `manual.py`) och de senaste STRIKE-filerna i
  `reference/` för de namn som nämns ovan.
- För varje steg i beräkningen: gör det här vad Warren menar med ägarvinst
  och värde? Pröva åt båda hållen, för högt och för lågt.
- Förklara LIAB, RBREW och PEP fullständigt: hela nedbrytningen från
  kassaflöde till värde per aktie, och var exakt värdet går fel om det gör det.
- Leta efter felklasser, inte bara enskilda fel: "ett enskilt år
  kapitaliseras" var en klass. Vilka fler finns?

**Fas 2 — Designa maskinen.** Beskriv hur bear/base/bull tas fram enligt
ovan: vilka indata, vilka steg, vad som är deterministisk kod och vad som
kräver läsning av rapporter och marknaden, och hur läsningens slutsatser
sparas så att de kan granskas och återanvändas.

**Fas 3 — Pilot på fyra namn med ungefärligt facit**, innan något rullas ut:
- **CENTA**: ska landa runt 30–34 (ägarens egen genomgång).
- **RBREW** och **LIAB**: ska bli positiva, och det ska gå att förklara varför.
- **PEP**: ska antingen hamna närmare kursen eller ha en skriftlig, belagd
  förklaring till varför marknaden har fel.
- Varje pilotvärde jämförs mot tre oberoende ankare: vad kursen implicerar
  (omvänd DCF), bolagets ägarvinst över 5–10 år, och avkastningen på
  kapitalet. Ett värde långt från alla tre förklaras eller rättas.

## Regler för sessionen

- **Inga ändringar i `config/`, watchlisten, FRAMEWORK-EDITS eller motorns
  beräkningar i fas 1 och 2.** Piloten i fas 3 körs i scratch eller på en
  egen gren och skriver inte till watchlisten.
- Inget pushas, inget handlas.
- Varje fynd ska visa sin nedbrytning och sin källa. En åsikt utan källa är
  inget fynd.
- Granskningen är klar när fas 1–3 är gjorda, inte när det känns färdigt.
  Hitta inte på nya krav under arbetets gång; skriv dem i ett eget avsnitt
  "Utanför uppdraget" och gå vidare.
- Det här är ett stort arbete. Commita rapporten efter varje fas så att
  inget förloras om sessionen bryts. Underagenter får hämta och läsa
  (Sonnet, högst medium), inte bedöma.
- Var rak. Om en del av ägarens önskemål inte går att göra som beskrivet,
  säg det och föreslå det som ligger närmast.

## Leverans

`reference/reviews/method/2026-10-27-REBUILD.md`, med:

1. **Svar först:** fungerar metoden i dag, ja eller nej, och de tre största
   felen i klartext.
2. Alla bekräftade fel, med påverkan per namn i procent och riktning.
3. Systematisk slagsida: drar felen åt samma håll över många namn?
4. Regelboken, varje fråga avgjord med motivering.
5. Designen av bear/base/bull-maskinen.
6. Pilotresultaten för de fyra namnen, med nedbrytning och de tre ankarna.
7. En byggplan: vilka filer som ändras, i vilken ordning, vilka tester.
