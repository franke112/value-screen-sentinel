# Vad andra redan har testat — litteraturgenomgång, 2026-10-29

Skriven efter piloten (`PILOT-2018.md`) och före räkneverktyget (väg 1).
Ägaren 2026-10-29: "vi tar bara överlevare så länge".

**Hur säker varje rad är.** Tre hämtare (Sonnet) läste källorna. Bara
Piotroski, Novy-Marx, QMJ och McLean & Pontiff lästes i originaltext.
Övriga bygger på sammanfattningar eller citat, och de siffrorna är märkta
*ej bekräftad*. Ingen siffra här får användas som facit i en rapport förrän
den lästs i originalet.

## 1. Kort svar

1. **Att fv/kurs fungerar har stöd.** Frankel & Lee fann att ett eget
   värde delat med kursen förutsäger avkastning på 2–3 års sikt, bättre
   än B/M. Deras värde bygger dock på analytikernas prognoser, inte på
   bokslut. Ett FCF-värde byggt bara på bokslut, som vårt, hittade vi
   inget direkt test av.
2. **EBIT/EV är svårt att slå.** I Gray & Vogel (NYSE 1964–2011) vann
   EBIT/TEV bland de enkla nyckeltalen. Enligt Alpha Architect var det
   EBIT/TEV-delen som stod för nästan allt i Greenblatts formel. Ingen av
   källorna visar att en avancerad modell slår enkla nyckeltal utanför
   den period den byggdes på. *Siffrorna ej bekräftade; källorna motsäger
   delvis varandra.*
3. **Kvalitet bland billiga bolag har stöd, men effekten sitter i småbolag
   och på förlorarsidan.** Piotroski fann en skillnad på 23 procentenheter
   per år mellan de starka och de svaga bolagen i den billigaste femtedelen,
   men effekten var svag bland stora bolag. I QMJ ligger det mesta av
   effekten i att undvika skräp, inte i att hitta vinnare.
4. **Det mesta krymper efter publicering.** Hos McLean & Pontiff föll
   avkastningen med 26 % utanför provet och 58 % efter publicering. Vår
   regel att justera på 2016–2018 och pröva på 2019–2020 är alltså rätt
   och behövs.

## 2. Per studie

| Studie | Urval | Signal | Datum hålls ute | Avnoterade | Resultat | Status |
|---|---|---|---|---|---|---|
| Frankel & Lee 1998, JAE 25(3) | USA, troligen 1975–1993 | V/P, residualvinst + analytikerprognoser | ej bekräftad | ej bekräftad | V/P förutsäger avkastning, inte förklarat av beta, B/P eller storlek; köp-och-behåll 2–3 år "mer än dubbelt" B/M | abstract bekräftat, siffra via citat |
| Gray & Vogel 2012, JPM 39(1) | NYSE 1964–2011 | EBIT/TEV, EBITDA/TEV, E/P, B/M, FCF/TEV, snitt över flera år | ej bekräftad | ej bekräftad | EBIT/TEV bäst (14,55 % CAGR i sammanfattning); snitt av vinst över 2–8 år tillför lite | ej bekräftad, källorna motsäger varandra |
| Gray & Carlisle 2012, *Quantitative Value* | USA 1974–2011 | EBIT/TEV + kvalitet + undvika bedrägerier/kris | ej bekräftad | ej bekräftad | slog Greenblatt med 3,74 pe/år; enbart EBIT/TEV ~15,95 %/år | via bokrecension |
| Piotroski 2000, JAR 38 suppl. | USA 1976–1996, billigaste B/M-femtedelen, 14 043 bolagsår | F-score, nio binära test | avkastning från 5:e månaden efter bokslut | **avnoterade räknas som 0 %** | högsta minus lägsta 0,230 första året; 23 %/år lång–kort; koncentrerat i små, lite handlade bolag utan analytiker | **originaltext** |
| Novy-Marx 2013, JFE 108(1) | USA 1963–2009, utan finans | (intäkter − KSV) / tillgångar | redovisning släpas till juni året efter | ej i texten | 0,33 %/mån; tillsammans med värde 0,75 %/mån; **värde fungerar mycket bättre när man kontrollerar för lönsamhet, särskilt bland stora bolag** | **originaltext** (NBER-versionen) |
| Asness, Frazzini & Pedersen 2019, RAST 24(1), "Quality minus junk" | USA 1957–2016 | lönsamhet, tillväxt, säkerhet | ≥ 6 månader | avnoterade av dåliga skäl utan kurs = −30 % | QMJ 0,29 %/mån, 4-faktor-alfa 0,60 %; **alfa −0,44 % i sämsta decilen mot +0,20 % i bästa** (CAPM) | **originaltext** |
| Mohanram 2005, RAST 10(2) | dyra (låg B/M) bolag | G-score, åtta test | – | – | bättre på att hitta stora förlorare än vinnare | ej bekräftad |
| McLean & Pontiff 2016, JF 71(1) | 97 signaler | – | – | – | −26 % utanför provet, −58 % efter publicering; större fall för signaler som var starkast i provet | **originaltext** |
| Fama & French 2021, RAPS 11(1); Israel m.fl. 2021, JPM | – | värde | – | – | värdepremien mindre 1991–2019 än 1963–1991; djup nedgång 2017–2020 | storleken ej bekräftad |
| Jegadeesh & Titman 1993, JF 48(1) | USA 1965–1989 | 3–12 mån vinnare minus förlorare | – | – | fortsätter i 3–12 månader | siffror ej bekräftade |
| Asness, Moskowitz & Pedersen 2013, JF 68(3) | många marknader | värde och momentum | – | – | negativt korrelerade (~−0,6 för aktier); kombinationen bättre än var för sig | korrelation ej bekräftad |
| Bernard & Thomas 1989, JAR 27; Martineau 2022 | USA 1974–1985 | överraskning i vinst (SUE) | – | – | drift ~4,2 % på 60 dagar; **nära noll för stora bolag efter 2006** (Martineau) | ej bekräftad |
| Kothari, Shu & Wysocki 2009, JAR 47(1) | USA | dåliga nyheter vs goda | – | – | dåliga nyheter ger större kursfall, i linje med att ledningar håller inne dem | resultat ej kvantifierat |
| Shumway 1997, JF 52(1); Shumway & Warther 1999, JF 54(6) | CRSP | avnoterade utan kurs | – | −30 % NYSE/Amex, **−55 % Nasdaq** | Nasdaq 1977–1994: 5,6 %/år avnoteras; rättning sänker likaviktad avkastning ~3 pe/år och tar bort småbolagseffekten | abstract bekräftat |

Inget hittades om att köpa efter kraftiga fall i värdebolag ("falling
knives") eller om drift efter att ledningen sänkt sin egen prognos. Det är
de två mest direkta frågorna för Gate 1 och §4.2.3, och de är fortfarande öppna.

## 3. Vad det betyder för räkneverktyget

1. **Datum.** Vi tar inlämningsdatum per siffra och håller ute
   inlämningar samma dag. Det är strängare än litteraturens "4–6
   månader efter bokslut". Det behöver inte ändras.
2. **Bara överlevare snedvrider åt två håll, och kvalitetstestet drabbas
   mest.** De avnoterade av dåliga skäl (−30 till −55 %) är oftast billiga
   och av låg kvalitet. När de saknas:
   - ser den **billiga kvintilen bättre ut** än den var, och då
     överskattas fv/kurs-effekten;
   - ser **bolagen som underkänns av Q1–Q4 bättre ut** än de var. Det är
     just där QMJ och Mohanram hittar effekten. Då *underskattas* nyttan
     med E145.

   Därför måste ett svagt resultat för E145 bland överlevarna läsas som
   "inte bevisat", inte som "grinden tar bort vinnare". Ett starkt resultat
   för fv/kurs bland överlevarna kräver avnoterade data innan vi tror på det.
3. **Urvalet ≥ 300 MUSD ligger där Piotroski är svagast.** Räkna med en
   mindre kvalitetseffekt än hans 23 %.
4. **Lägg till två enkla jämförelser** till designens tre (EV/EBIT,
   Greenblatt, hela urvalet med lika vikt):
   - **bruttolönsamhet** (Novy-Marx), som är den enklaste kvalitetssignalen;
   - **F-score bland de billiga** (Piotroski), som är vad E145 ska slå.

   Båda går att räkna ur samma klippta companyfacts. Om E145 inte slår
   F-score är grinden bara en dyrare F-score.
5. **Förvänta dig mindre än du ser.** Det som förbättras på 2016–2018
   tappar enligt McLean & Pontiff en fjärdedel till hälften. Testdagarna
   ligger dessutom mitt i värdets sämsta period, så ett svagt resultat mot
   index säger mer om perioden än om motorn. Jämförelsen mot EV/EBIT är den
   som avgör.
6. **Gate 1 och §4.2.3 förblir utanför.** Forskningen om momentum går
   *mot* att köpa efter fall. Forskningen om drift *stöder* att undvika dåliga
   nyheter men visar en svag effekt för stora bolag efter 2006, vilket inte
   är bekräftat. Ingen av dem besvarar våra regler direkt. Ett senare test
   via 8-K item 2.02 behövs.

## 4. Att läsa i original innan resultatrapporten

- Gray & Vogel 2012: datumregel, avnoterade, CAGR för FCF/TEV och
  E/P. Hämtaren fick 403 från alphaarchitect.com.
- Frankel & Lee 1998: urval, år, avnoterade, kvintilspridning.
- Fama & French 2021: hur djup nedgången 2017–2020 var.
- Studier av avkastning efter att ledningen sänkt prognosen, till exempel
  Hutton, Rogers & Stocken eller Penman 1980.
