"""Del två — maskinen. Kapitel 13 till 23.

Samma pedagogik som i del ett: först den enkla versionen, sedan det tekniska
ordet, en gång. Varje faktum om systemet är hämtat ur förvaret: enhetsfilerna
under deploy/, modulernas docstrings under vss/ och besluten.
"""

from content1_sv import Notes, fold, decision, example, wrong, right, chapter
from diagrams_sv import ALL as FIG

# ---------------------------------------------------------------------------
# 13. WHY THE METHOD NEEDED A MACHINE
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "13-why-a-machine", "Varför metoden behövde en maskin",
    "En metod på papper förfaller: du glömmer, du glider, du tar om en avgjord fråga samma dag som en kurs rör sig. Maskinens uppgift är att mäta och att minnas. Den är medvetet byggd för att inte avgöra.",
    7, True,
    f"""
<p>Allt i del ett skulle kunna göras med ett anteckningsblock. Under en tid gjordes det också. Så här går det för en metod som bor i ett anteckningsblock.</p>

<p>Du glömmer. Sex bolag på bevakningslistan, vart och ett med en köpkurs och ett stopp, och en tisdagskväll i mars minns du inte vilken rapport du senast värderade BOLAG B efter. Du glider. Säkerhetsmarginalen var 25 procent, men det här bolaget är nästan där och du förstår det väl, så 22 vore väl okej, bara den här gången. Du tar om. En kurs faller 8 procent på en dag, och en fråga du avgjorde skriftligen för tre veckor sedan står plötsligt öppen igen, för nu finns det en insats i svaret. Inget av det här är dumhet. Det är vad en människa gör med en regel när människan är trött, eller uppspelt, eller har pengar på spel. Del ett är en uppsättning vanor som är gjorda för att vara svåra att böja, och vanor är precis det en människa under press böjer först.</p>

<p>Så metoden fick en maskin: ett litet program på en hyrd server som körs varje natt, hämtar dagens kurser, jämför dem med de nivåer ägaren redan har skrivit ned, och rapporterar. Det minns vad ägaren bestämde och när. Det blir inte uppspelt.</p>

<h2>Den styrande principen</h2>
<p>Verktyget mäter. Ägaren avgör. Det är hela konstruktionen, och den är genomdriven, inte bara avsedd.</p>

{FIG["measure_decide"]()}

<p>Vad maskinen får göra är en kort lista med verb. Den får hämta kurser och rapporter. Den får räkna fram en fast uppsättning nyckeltal. Den får jämföra en kurs med en nivå. Den får skriva en rapport och en sida. Den får peka på ett bolag som behöver ägarens uppmärksamhet. Den får säga att en siffra saknas. Vad den aldrig får göra är längre, och varje punkt är nedskriven i koden som ett nej: den skriver aldrig ett utlåtande, tar aldrig in ett bolag i processen, tilldelar aldrig en nivå, sätter aldrig ett värde eller en köpkurs eller ett stopp, flyttar aldrig ett bolag från en status till en annan. Med verktygets egna ord räknar det bara fram marknadsdata, och "allt som kräver bedömning är ett MANUAL-fält som du fyller i för hand; verktyget räknar, gissar, standardsätter eller fyller aldrig i något av det i efterhand."{N.ref("README. Den schemalagda screeningen 'får SNAPSHOT, RANK och REPORT; den tar aldrig in ett bolag' (beslut E93). En uppdatering 'HÄMTAR, EXTRAHERAR och RAPPORTERAR; den avgör aldrig' (beslut E92). Kursbevakningen 'pekar en gång per korsning och skriver ingenting' (beslut E97). Sidgeneratorn: 'projektets idé är att sidan mäter och att jag avgör.'")}</p>
{N.flush()}

<h2>Varför den icke-autonoma konstruktionen är den svårare</h2>
<p>Det vore enklare att bygga ett program som avgör. Ge det reglerna och låt det markera bolag som köpta eller avvisade; det skulle aldrig bli trött. Det skulle också ärva varje svaghet hos sin upphovsperson och lägga till egna, och ingen skulle kunna avgöra vilken som var vilken, eftersom beslutet och mätningen vore en och samma sak.</p>

<p>Att hålla isär dem kostar arbete i varje lager. Varje automatiserat steg får sin lista med tillåtna verb och en mekanisk kontroll av att det inte gjorde något annat: uppdateringskommandot körs under ett påstående om att ägarens fil inte rördes; den schemalagda screeningen startas utan den enda flagga som skulle låta den ta in ett bolag, och enheten som startar den kan inte skriva i mappen där filen ligger; sidgeneratorn körs under ett test som tar en inventering av varje fil i förvaret före och efter och hävdar att inte en enda byte har flyttats.{N.ref("Påståendet assert_no_watchlist_write i uppdateringsmodulen; den saknade flaggan --write-pipeline och den skrivskyddade konfigurationsmappen i den schemalagda screeningens enhet; inventeringstestet på översiktsgeneratorn, beskrivet i projektbeskrivningen §4.7.")} Ett program som inte kan avgöra måste hindras från att avgöra på varje ställe där det vore bekvämt att avgöra.</p>
{N.flush()}

<p>Det finns en forskningslitteratur om vad som händer när människor arbetar vid sidan av automation, och dess återkommande slutsats är att människor slutar kontrollera sådant som maskinen verkar ha kontrollerat. Begreppet är automation misuse: överdrivet förtroende som leder till brister i övervakningen.{N.ref("Parasuraman och Riley, 'Humans and Automation: Use, Misuse, Disuse, Abuse', Human Factors 39 (1997).")} Ett verktyg som levererar ett utlåtande inbjuder till precis det. Ett verktyg som levererar ett avstånd och en lista över vad det inte kunde kontrollera gör motsatsen: det lämnar över ett ofärdigt arbete till läsaren, varje natt, med de ofärdiga delarna utpekade.</p>
{N.flush()}

<p>Resten av del två handlar om hur den principen byggs: hur delarna hålls isär, hur registret hålls ärligt, hur reglerna hålls över koden, vad som händer klockan halv elva varje natt, hur ägaren får veta när det inte händer, och hur resultatet når en telefon utan att öppna en dörr in i maskinen.</p>

{decision(
    "Programmet mäter och rapporterar. Varje beslut är ägarens, fattat för hand, och programmet är byggt så att det inte kan fatta något, inte ens av misstag.",
    "En metod som avgör ärver sin upphovspersons fördomar och döljer dem inuti mätningen. Genom att hålla isär de två förblir båda kontrollerbara, och ägaren fortsätter att läsa i stället för att lita.",
    "Varje tillåtet verb måste inhägnas med en kontroll av att inget annat hände, i varje lager. Ägaren gör all bedömning, på varje bolag, varje gång, och inget i maskinen gör det snabbare.",
)}
""",
    [
        ("Parasuraman och Riley (1997), Humans and Automation: Use, Misuse, Disuse, Abuse", "https://journals.sagepub.com/doi/10.1518/001872097778543886"),
        ("Vad varje automatiserat steg får och inte får göra", "repo: README.md; reference/FRAMEWORK-EDITS.md E92, E93, E97; vss/refresh.py; vss/screenwatch.py; vss/overview.py"),
    ],
)

# ---------------------------------------------------------------------------
# 14. HOW THE PROGRAM IS PUT TOGETHER
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "14-the-pieces", "Hur programmet är uppbyggt",
    "Sju sorters delar och väggarna mellan dem. Det intressanta är inte vad varje del gör utan vad den är förbjuden att göra.",
    9, False,
    f"""
<p>Programmet är en uppsättning små delar, var och en med ett enda jobb, och konstruktionsfrågan var aldrig "vad ska varje del göra" utan "vad måste varje del vara oförmögen att göra". Det här kapitlet går igenom delarna som en bild och namnger sedan väggarna. Det finns ingen kod i det.</p>

{FIG["pieces_walls"]()}

<h2>De sju sorternas delar</h2>

<h3>Hämtning: att föra in siffror utifrån</h3>
<p>En del hämtar dagliga kurser och sparar en kopia på disk, så att körningen, när kurstjänsten ligger nere, har gårdagens siffror markerade som gamla i stället för ingenting alls. En annan läser den strukturerade data som amerikanska bolag måste lämna till sin tillsynsmyndighet. Ytterligare två läser de nordiska börsernas egna flöden för offentliggöranden, där ett svenskt eller norskt bolags rapporter faktiskt dyker upp. En läser ett bolags kalkylbladsbilaga via en karta, incheckad tillsammans med koden, som säger vilken cell som är vilken siffra. En hämtar ett bolags egen rapportsida och inget annat: den söker inte, gissar inte och följer inga länkar. Och en lämnar ett hämtat dokument till en språkmodell med en snäv instruktion: plocka ut de uppgivna siffrorna och citera meningen var och en kom från; härled, uppskatta eller stäm aldrig av en siffra, avgör aldrig om något är väsentligt, skriv aldrig någon löptext.{N.ref("Modulbeskrivningar i vss/fetch.py, vss/xbrl.py, vss/nordic.py, vss/oslo.py, vss/appendix.py, vss/source.py och vss/extract.py; README om extraktorn: den 'härleder, uppskattar eller stämmer aldrig av en siffra, avgör aldrig väsentlighet och skriver aldrig löptext.'")}</p>
{N.flush()}
<p>Det förbjudna, för varje hämtare: den får inte döma det den hämtat. Den för in en siffra med dess ursprung fastsatt, och stannar där.</p>

<h3>Registret: att spara varje siffra</h3>
<p>En del skriver en rad per bolag och körning i en liten databas, så att historiken kan byggas upp igen senare. En för körningsprotokollet för varje värdering, de åtta saker som måste vara deklarerade innan ett värde får skrivas ut (kapitel 15). En sparar en ögonblicksbild av varje screeningkörning, de råa kurserna och listan över bolag, så att körningen kan spelas upp igen exakt. En håller handinmatade siffror för bolag som ingen datakälla täcker, var och en markerad som kontrollerad eller inte. En testar om en kursserie är en verklig mätning eller en artefakt från datakällan.{N.ref("vss/store.py, vss/runrecord.py, vss/snapshot.py, vss/manual.py, vss/series_sanity.py.")}</p>
{N.flush()}
<p>Det förbjudna: registret fyller aldrig ett hål. En siffra som inte hämtades saknas, och fortsätter att saknas.</p>

<h3>Beräkning: aritmetiken, hållen ren</h3>
<p>De delar som räknar fram nyckeltal, tillämpar reglerna och löser värderingen gör ingen inmatning och ingen utmatning. De läser inga filer, rör inte nätverket och vet inte vad klockan är; datumet lämnas alltid till dem. Det här är en vägg, inte en konvention: det betyder att en uträknad siffra kan återskapas senare från samma indata och bli densamma, eftersom ingenting i beräkningen kunde ha berott på världen utanför.{N.ref("Regelmodulen: 'Den här modulen gör NOLL I/O. Ingen filåtkomst, inget nätverk, ingen loggning och avsiktligt ingen datetime.now().' Nyckeltalsmodulen är likadan, med as-of-datumet alltid överlämnat.")}</p>
{N.flush()}

<h3>Rapportering: rapporten och sidan</h3>
<p>En del skriver nattrapporten i en fast ordning: när körningen skedde och hur färsk datan var; sedan blockeringar, det som stoppade en bedömning; sedan åtgärder, det som kräver ägaren; sedan hela tabellen över varje bolag. En annan genererar översiktssidan på en sida som når telefonen (kapitel 21). En tredje sätter ihop ett underlag för ett bolag som läses, en samling av siffrorna och deras källor, inte en uppfattning.{N.ref("vss/report.py, vss/overview.py, vss/briefing.py.")}</p>
{N.flush()}
<p>Det förbjudna: ingen rapport säger köp, sälj eller bra. Den säger hur långt, hur färskt och vad som saknas.</p>

<h3>Screeningen</h3>
<p>Delarna från kapitel 4: den fasta listan över bolag, de två filtren, rangordningen och ett skal som kör dem en lördagsmorgon. Plus en liten del, och den är den enda delen i screenern som får skriva i ägarens fil: den som tar in ett föreslaget bolag. Den körs bara när ägaren startar den för hand.{N.ref("vss/screen.py, vss/filters.py, vss/universe.py, vss/ranking.py, vss/screenwatch.py; vss/pipeline.py är 'den enda modulen i screenern som skriver till filen med ägarens levande positioner', och den schemalagda enheten startas utan den flagga som skulle anropa den.")}</p>
{N.flush()}

<h3>Bevakning</h3>
<p>Två delar. Den ena bevakar flödena för offentliggöranden för bolagen på väntelistorna och rapporterar bara tre sorters dokument: en periodisk rapport, en ändring av bolagets egen prognos, en vinstvarning. Allt annat börsen publicerar avvisas och avvisningen skrivs ut. Den andra bevakar kurserna för screenerns tjugo främsta mot en vägledande nivå och pekar, en gång, när en kurs korsar den. Nivån är ett avstånd från ett grovt värde, inte en köplinje, och beslutet säger det.{N.ref("vss/watch.py; vss/pricewatch.py, beslut E97: 'ett avstånd, inte en köplinje'.")}</p>
{N.flush()}

<h3>Hjärtslaget</h3>
<p>En del vars enda uppgift är att få en körning som uteblev att se annorlunda ut än en körning som inte hade något att säga. Kapitel 18.</p>

<h3>Körningsledaren</h3>
<p>En del knyter ihop nattkörningen: läs in ägarens fil, hämta, räkna, bedöm, rapportera. All läsning och skrivning i körningen bor här och i delarna för hämtning, lagring och rapport, så att allt annat kan förbli rent.{N.ref("vss/runner.py: 'All I/O bor här och i fetch/store/report. rules.py och metrics.py förblir rena.'")}</p>
{N.flush()}

<h2>De två väggarna</h2>
<p>Den första väggen går runt ägarens fil. Den rymmer varje status, varje nivå, varje värde, varje stopp: besluten. Ingen del som körs enligt schema får skriva i den. Uppdateringskommandot hävdar att det inte gjorde det. Den schemalagda screeningens enhet kan inte skriva i mappen. En handskriven köpkurs i filen får körningen att misslyckas rakt av, eftersom en köpkurs måste komma från ett värde och en nivå, annars har den inget ursprung.{N.ref("Besluten E92 och E93; README om proveniensmotsägelsen; den skrivskyddade konfigurationsmappen i deploy/vss-screen.service.")}</p>
{N.flush()}
<p>Den andra väggen går runt aritmetiken. Inget som räknar får hämta, och inget som hämtar får räkna. En siffra tar sig från den ena sidan till den andra bara genom registret, med sitt ursprung fastsatt. Det är det som gör ett tal reproducerbart, och som gör att ett felaktigt tal kan spåras till hämtningen som förde in det i stället för att försvinna inuti en beräkning.</p>

{fold("Kommandona, för den nyfikne", '''
<p>Programmet körs från kommandoraden som <code>python -m vss</code> följt av ett av sexton underkommandon. De som en läsare av den här webbplatsen har mött: <code>run</code> (nattkörningen), <code>screen</code> (veckoscreeningen), <code>watch</code> (offentliggöranden), <code>refresh</code> (läs om ett bolags siffror på rapportdagen), <code>earnings</code>, <code>xbrl</code>, <code>nordic</code>, <code>manual</code>, <code>appendix</code> (sätten som siffror kommer in), <code>briefing</code> (sätt ihop ett underlag), <code>overview</code> (sidan), <code>checkin</code> (hjärtslagets egen timer), <code>sales</code> (stängda positioner mätta mot index), <code>shadow</code> (skuggboken). Varje en av dem skriver en rapport till standard output och loggar till standard error, och ingen av dem skriver ett beslut.</p>
''')}
""",
    [("Modulernas uppbyggnad och vars och ens angivna omfång", "repo: vss/*.py module docstrings; vss/__main__.py; README.md")],
)

# ---------------------------------------------------------------------------
# 15. WHERE THE DATA LIVES AND HOW IT IS KEPT HONEST
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "15-the-record", "Var datan bor och hur den hålls ärlig",
    "Varje siffra med sitt ursprung, varje värdering med sina åtta deklarationer, varje körning med sin egen rad. Varför en värdering som inte kan slutföra sitt protokoll skriver ut ingenting i stället för ett tal med en varning.",
    8, False,
    f"""
<p>Del ett sa att varje siffra bär med sig var den kom ifrån. Det här kapitlet handlar om vart det tar vägen, och om den enda regel som håller hela registret pålitligt: ett tal med ett hål i sitt ursprung skrivs inte ut med ett förbehåll. Det skrivs inte ut alls.</p>

{FIG["figure_journey"]()}

<h2>Fyra ställen där en siffra kan bo</h2>
<ul>
<li><strong>Körningsdatabasen.</strong> En rad per bolag och nattkörning: kursen, de uträknade siffrorna, utlåtandekoderna, blockeringarna. Ingenting läser tillbaka den ännu; den finns för att samla på sig, så att historiken kan rekonstrueras senare.{N.ref("vss/store.py.")}</li>
<li><strong>Grunddatalagret.</strong> Varje redovisningsperiod som någonsin hämtats för ett bolag, sparad för gott. Ett kvartal ersätter aldrig ett år. Ett lager som rensade gamla perioder skulle göra det omöjligt att återskapa en gammal värdering.{N.ref("Beslut E49: lagret behåller varje period det någonsin har hämtat. Beslut E17: ett kvartal ersätter aldrig ett år.")}</li>
<li><strong>Screenerns ögonblicksbilder.</strong> En liten databas per screeningkörning, med råa dagliga kurser, aldrig uträknade siffror, plus listan över bolag, avvisningarna och en hämtningsstatus per bolag. De fyra senaste kursbilderna sparas; varje rangordning sparas för alltid, eftersom varje framtida jämförelse vilar på den.{N.ref("vss/snapshot.py; lagringstiden beskrivs i projektbeskrivningen §6.5.")}</li>
<li><strong>Ägarens fil.</strong> Statusar, nivåer, värden, stopp, anteckningar och handinmatade siffror. Spårad under versionshantering, på ägarens beslut, så att beslutens historik finns i filens historik.{N.ref("README om config/watchlist.yaml, spårad sedan 2026-08-25.")}</li>
</ul>
{N.flush()}

<h2>Körningsprotokollet: åtta deklarationer eller ingenting</h2>
<p>En värdering är inte ett tal. Den är ett tal plus allt som avgjordes för att få fram det. Så innan ett värde får skrivas ut måste körningsprotokollet för den värderingen deklarera åtta saker: vilket antal aktier som användes och per vilket datum; hur aktiebaserad ersättning behandlades; var bolaget bokför sin ränta, och därmed vad "fritt kassaflöde" betyder för det; varje post i bryggan från värdet på hela verksamheten till värdet på dess aktier; aritmetikens konventioner; diskonteringsräntan med sitt ankare och tillväxttakten med den bedömning den kom från; de tre as-of-datumen och kursdatumet; och ursprunget för varje indata.{N.ref("vss/runrecord.py: 'EN KÖRNING UTAN KOMPLETT PROTOKOLL SKRIVER INTE UT ETT VERKLIGT VÄRDE. Inte \\'skriver ut ett med en varning\\'.'")}</p>
{N.flush()}

<h2>Varför att vägra slår att fortsätta</h2>
{wrong('''
<p>Sju av de åtta deklarationerna är på plats. Aktieantalet finns men datumet det angavs saknas. Skriv ändå ut värdet, med en anmärkning: "aktieantalets datum okänt". Ägaren kommer att se anmärkningen.</p>
''', "Det rimligt klingande sättet, som är fel")}
{right('''
<p>Värderingen kastar ett fel och skriver inte ut något värde för det bolaget. Rapporten säger vilken deklaration som saknas. De andra bolagen i samma körning påverkas inte: ett bolags saknade deklaration är det bolagets DATA SAKNAS, aldrig en orsak att stoppa körningen för de övriga.</p>
''', "Vad koden gör")}
<p>Anmärkningen skulle läsas första gången och inte den tionde. Ett tal på en sida är ett tal; förbehållet bredvid är dekoration, och dekoration ignoreras. Det enda förbehåll som inte går att ignorera är att talet saknas. Därför vägrar registret, och vägran är en rad i rapporten som säger vad du ska gå och leta efter.</p>

<p>Det finns två nivåer av vägran, och det är värt att vara exakt. En felaktig eller saknad siffra för ett bolag försämrar det bolagets rad och inget annat; nattkörningen är byggd så att ett enskilt bolag aldrig kan bryta den. En korrupt ägarfil, en felformad post eller en handskriven köpkurs, stoppar hela körningen innan den börjar, högljutt, eftersom en körning på en korrupt fil skulle skriva korrupta rader i registret för varje bolag.{N.ref("Körningsledaren fångar fel per bolag och fortsätter ('ett bolag bryter aldrig körningen'); konfigurationsläsaren låter hela körningen misslyckas vid en felformad post eller en proveniensmotsägelse.")}</p>
{N.flush()}

<h2>Kontrollerad, okontrollerad, saknad, inte där</h2>
<p>En siffras verifieringsstatus följer med den. Den kommer in okontrollerad. En människa läser tillbaka den mot sidan som anges bredvid och markerar den som kontrollerad, och markeringen anger vilken sorts kontroll: mot tillsynsmyndighetens strukturerade data, över två skilda dokument, eller mot samma sida den kom från. Där en siffra eftersöktes i en fullständig rapport och inte finns, säger registret det, vilket är något annat än en nolla och något annat än saknad.{N.ref("Verifieringssorter: beslut E40 och vss/manual.py. Ej redovisad: beslut E85. En nolla kräver ett underlag: beslut E25.")}</p>
{N.flush()}
<p>Att två oberoende avläsningar stämmer överens är det som gör en siffra till ägarens. Där två avläsningar skiljer sig åt extraheras siffran på nytt innan någon eskalerar den, eftersom den första frågan om en avvikelse är om den ena avläsningen helt enkelt var fel.{N.ref("Beslut E104.")}</p>
{N.flush()}

<h2>Att avbryta en screening på grund av ett hål</h2>
<p>Screenern har ett ställe där den stannar i stället för att fortsätta: när en kvartalsjämförelse den behöver inte kan bildas för att ett kvartal saknas, bryter den körningen i stället för att slå ut ett bolag på ett hål. Ett test av fallande omsättning som underkänner ett bolag för ett kvartal som leverantören inte levererade vore precis det tvåsidiga felet från kapitel 9, i stor skala.{N.ref("vss/filters.py, omsättningsledet: en jämförelse som kvartalen inte kan bilda 'bryter körningen i stället för att slå ut på ett hål'.")}</p>
{N.flush()}

{decision(
    "En värdering skriver ut ett värde bara med ett komplett protokoll om åtta deklarationer; annars skriver den ut ingenting för det bolaget och säger vad som saknas. Ett enskilt bolags fel stoppar aldrig körningen; en korrupt ägarfil stoppar den innan den börjar.",
    "Ett förbehåll bredvid ett tal läses en gång. Ett saknat tal läses varje gång.",
    "Bolag står värderade till ingenting så länge en deklaration saknas, och rapporten blir längre av att förklara varför. Ägaren lägger kvällar på att leta aktieantalsdatum.",
)}
""",
    [("Registret, körningsprotokollet och lagret", "repo: vss/store.py; vss/runrecord.py; vss/snapshot.py; vss/manual.py; vss/runner.py; reference/FRAMEWORK-EDITS.md E17, E25, E40, E49, E85, E104")],
)

# ---------------------------------------------------------------------------
# 16. THE RULES FILE
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "16-the-rules-file", "Regelfilen",
    "Ett nedskrivet ramverk, ändrat bara genom daterade, numrerade beslut. En regelfråga och ett fel hör hemma i olika filer. Att skriva regeln innan situationen uppstår är det som hindrar dig från att böja den när du väl har en insats i svaret.",
    8, True,
    f"""
<p>Metoden finns som ett dokument innan den finns som kod. Det är ingen bild. Det finns en fil, ramverket, med numrerade avsnitt från 0 till 11, och det finns en andra, mycket längre fil med beslut som ändrar det, vart och ett med en bokstav eller ett nummer, ett datum och påståendet att ägaren har avgjort det. Koden genomför besluten. Den fattar dem inte.</p>

<h2>Tre filer, tre uppgifter</h2>
<ul>
<li><strong>Ramverket.</strong> Själva metoden: spärrarna, de hårda diskvalificeringarna, värderingen, disciplinen vid köp och avyttring, positionsstorleken. Det innehåller inga daterade innehav och ingen marknadsdata, så det blir aldrig inaktuellt. Det är i version 2.3.</li>
<li><strong>Besluten.</strong> Varje oklarhet, avvikelse och ändring, i serier med bokstäver. A för strukturella rättelser. B för verkliga oklarheter i spärrarna, var och en väckt med ett datum och antingen avgjord eller lämnad öppen, och en öppen är en fråga som ägaren är skyldig ett svar. C för oklarheter som påverkar pengar. D för konsekvensrättelser. E för beslut om verktygen och, senare, de materiella reglerna, E1 till E114 när detta skrivs. F, den nyaste serien, för översiktssidan. Filen byggs på och skrivs aldrig om.{N.ref("reference/FRAMEWORK.md och reference/FRAMEWORK-EDITS.md. Beslutsfilen inleds: 'Varje punkt är ett ställe där en människa som läser det vet vad du menar och en maskin inte gör det. Jag har inte tillämpat något av detta — varje punkt ändrar en regel, och det är dina regler.'")}</li>
<li><strong>Backloggen.</strong> Sådant som är fel i koden. Dess första rader drar gränsen: "En regelfråga går till beslutsfilen och får en bokstav; ett fel går hit och blir åtgärdat. Ingenting i den här filen är ett beslut som ägaren är skyldig ett svar."{N.ref("reference/BACKLOG.md, inledningen.")}</li>
</ul>
{N.flush()}

<p>Åtskillnaden mellan den andra och den tredje filen är den viktiga. Ett tröskelvärde som är fel för att regeln var fel är ett beslut. Ett tröskelvärde som är fel för att koden missförstod regeln är ett fel. Blandas de kan en felrättelse i tysthet ändra en regel, eller en regeländring gömma sig i en felrättelse. Varje tröskelvärde i koden hänvisar till det beslut som satte det, och screenerns tröskelvärden bor i en konfigurationsfil där vart och ett anger sitt avsnitt i ramverket, inte alls i koden.{N.ref("config/screener_filter2.yaml, varje led med hänvisning till sitt avsnitt eller beslut; modulernas docstrings genom hela vss/ hänvisar till E-nummer som auktoritet för ett tröskelvärde eller ett fält.")}</p>
{N.flush()}

<h2>Varför regeln skrivs först</h2>
{wrong('''
<p>BOLAG A står i 91, köplinjen är 85, och ägaren har just läst om rapporterna och känner sig tryggare än nivån tillåter. Det förnuftiga vore att flytta det till nivå 1, vilket sätter linjen vid 89. Sedan vänta på 89.</p>
''', "Vad som händer utan en nedskriven regel")}
{right('''
<p>En ändring av en säkerhetsmarginal är ett daterat beslut, och den träder i kraft vid varje bolags nästa schemalagda omvärdering, aldrig omedelbart. En köplinje som korsas för att säkerhetsmarginalen flyttats beväpnar ingenting.</p>
''', "Regeln, E100")}
<p>Hela poängen med att skriva en regel innan situationen uppstår är att du i det ögonblicket inte har någon insats i svaret. När situationen väl kommer har du det, och regeln du skrev tidigare är den enda version av dig som tänkte klart. Besluten säger "skrivet före koden" öppet på sin framsida, och versionshanteringens historik behandlas som bevis för ordningen.{N.ref("Beslut E100 om ändringar av säkerhetsmarginalen. Projektbeskrivningen §1.2: 'Ett beslut skrivs FÖRE koden som genomför det, och många säger det öppet på sin framsida.'")} En session som ändrar vad koden gör utan ett beslut bakom sig gör, med projektets egna ord, fel sak.{N.ref("Projektbeskrivningen, §0.")}</p>
{N.flush()}

<h2>Varje beslut anger sitt pris</h2>
<p>Besluten är skrivna i ett ovanligt tonläge: deklarativt, absolut där en regel är absolut, och uttryckligt om vad ett beslut kostar. En borttagning anger vad som gick förlorat genom att ta bort. Ett nytt krav anger vad det kommer att göra långsammare. Den här webbplatsens beslutsrutor har lånat formen från besluten.</p>

<h2>Regler som drogs tillbaka</h2>
<p>En regelfil som bara någonsin växer är misstänkt. Den här dokumenterar sina egna omsvängningar, och de är det bästa beviset för att processen fungerar, eftersom var och en visar en regel som rättas genom ett daterat beslut i stället för att i tysthet böjas.</p>
<ul>
<li><strong>En spärr med två led som inte mätte någonting.</strong> Två test av stabilitet i rapporterade siffror visade sig mäta valuta och säsong, inte verksamheten, och hade inte ändrat något utlåtande över fem bolag. Raderades, med meningen "inte vidgat, inte mjukat upp, borttaget".{N.ref("Beslut E30, 2026-08-25.")}</li>
<li><strong>Ett skuldtak som lättades av fel skäl.</strong> Screenerns första tak sattes löst, på principen att ett grovt filter inte får förlora ett bolag som den noggranna läsningen skulle behålla. Fyra dagar senare visade en provkörning 72 bolag som passerade det lösa taket och föll på metodens egna strängare test. Skärptes, med antalet i beslutet.{N.ref("Beslut E2 ersatt av E44, 2026-08-26.")}</li>
<li><strong>En köpkursformel ersatt, med de gamla siffrorna kvar.</strong> När säkerhetsmarginalen flyttades från värdet i sämre fall till värdet i basfall räknades inte tre köpkurser som redan värderats enligt den gamla formeln om i tysthet. De behölls, markerade som ersatta överallt där de skrivs ut, och de gamla multiplikatorerna ligger kvar i koden med en kommentar som säger varför.{N.ref("Besluten E28, E32 och E90. Koden behåller båda multiplikatortabellerna: 'MBP_TIER_MULTIPLIER ovan BEHÅLLS för de ersatta vägarnas historik.'")}</li>
<li><strong>En hänvisning som inte fanns.</strong> Commiten som byggde telefontunneln hänvisade till ett avsnitt i ramverket som förbjöd en server. Avsnittet finns inte. Beslutet som följde säger: "Hänvisningen gjordes utan att filen lästes och dras tillbaka här." Commitmeddelandet är oföränderligt; beslutet är den gällande rättelsen.{N.ref("Beslut F1, 2026-09-13.")}</li>
<li><strong>Ett krav som drogs tillbaka samma dag det beslutades.</strong> Beslut F1 krävde att telefonsidan skulle markera sig själv som gammal efter 26 timmar. Beslut F2, samma dag, drog tillbaka kravet som omöjligt att bygga: en statisk fil kan inte jämföra sin egen ålder med tiden då den läses utan ett skript, och samma beslut förbjuder skript. De två leden motsade varandra; det ena föll. Det som återstod, att sidan anger sin egen ålder två gånger, genomfördes samma dag.{N.ref("Beslut F2, 2026-09-13.")}</li>
</ul>
{N.flush()}

<p>Inget av detta är pinsamt. Var och en är en regel som möter verkligheten och rättas i registret, med kostnaden angiven, av den som har rätt att ändra den. En metod som inte kan visa något tillbakadragande har antingen aldrig prövats eller döljer något.</p>

{decision(
    "Ramverket ändras bara genom daterade, numrerade beslut som ägaren fattar. Koden hänvisar till det beslut den genomför. En regelfråga och ett fel hör hemma i olika filer.",
    "En regel som skrivs innan situationen uppstår skrivs av någon utan insats i svaret. En regel som bara bor i koden kan ändras av en felrättelse.",
    "Förändring går långsamt. Ett tröskelvärde som ägaren vet är fel förblir fel tills ett beslut skrivs, och vissa öppna frågor har stått öppna i veckor. Beslutsfilen är över elvatusen rader lång.",
)}
""",
    [("Ramverket, besluten och backloggen", "repo: reference/FRAMEWORK.md; reference/FRAMEWORK-EDITS.md (A1–A3, B1–B48, C1–C4, D1–D2, E1–E114, F1–F2); reference/BACKLOG.md; config/screener_filter2.yaml")],
)

# ---------------------------------------------------------------------------
# 17. THE NIGHTLY RUN
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "17-the-nightly-run", "Nattkörningen",
    "Klockan halv elva går en klocka igång. Kurser kontrolleras på nytt mot beslut som redan fattats, filer skrivs, och körningen lämnar via en av två utgångar: en tyst signal till en yttre observatör, eller ett rop till ägarens telefon.",
    7, False,
    f"""
<p>Servrar har ingen människa som sitter vid dem. För att få något att hända vid samma tid varje dag skriver du två små filer åt operativsystemets schemaläggare. Den ena är en <dfn>timer</dfn>: den säger när. Den andra är en <dfn>tjänst</dfn> (service): den säger vad. Schemaläggaren här är den som är inbyggd i modern Linux, kallad systemd, och filerna kallas enheter (units).{N.ref("deploy/vss.timer och deploy/vss.service.")}</p>
{N.flush()}

{FIG["nightly_cycle"]()}

<h2>När</h2>
<p>Varje dag klockan 22:30, sedan de sista europeiska och amerikanska börserna har stängt och kurserna har lagt sig. Om maskinen var avstängd klockan 22:30 kör timern jobbet så snart maskinen är tillbaka, i stället för att hoppa över dagen.{N.ref("OnCalendar=*-*-* 22:30:00; Persistent=true.")}</p>
{N.flush()}

<h2>Vad</h2>
<p>Nattkörningen läser in ägarens fil, hämtar dagens kurser, räknar fram den fasta uppsättningen nyckeltal, jämför varje kurs med de nivåer som redan är skrivna för det bolaget, skriver rapporten, skriver en rad per bolag i körningsdatabasen och genererar sedan översiktssidan. Sidgenereringen körs sist och är ordnad så att körningen ändå är en framgång om den misslyckas: rapporten och databasraden kommer först, och ett misslyckande att rita sidan loggas som en varning, inte som ett misslyckande för natten.{N.ref("Översiktssidan 'åker med i samma enhet efter att rapporten och databasraden skrivits och kan inte bryta körningen'.")}</p>
{N.flush()}

<h2>Vad den inte kan röra</h2>
<p>Körningen är inhägnad av operativsystemet, inte bara av sin egen kod. Den ser hela systemet som skrivskyddat. Den ser ägarens hemkatalog som skrivskyddad. De enda två mappar den får skriva i är datamappen och rapportmappen. Den kan inte få några nya behörigheter när den väl startat, och den avbryts om den körs längre än femton minuter.{N.ref("ProtectSystem=strict; ProtectHome=read-only; ReadWritePaths= bara data- och rapportmapparna; NoNewPrivileges=true; TimeoutStartSec=15min.")} Det här är den första väggen från kapitel 14, dragen av en annan hand: även om koden hade ett fel som försökte skriva ett beslut i ägarens fil skulle operativsystemet vägra.</p>
{N.flush()}

<h2>De två utgångarna</h2>
<p>En körning slutar på ett av två sätt, och varje sätt ger ett olika ljud.</p>
<ul>
<li><strong>Framgång.</strong> Direkt efter att körningen slutförts skickar ett separat enradsskript en enda, tom förfrågan till en yttre övervakningstjänst. Den bär inget bolagsnamn, ingen kurs, ingen rapport, inget maskinnamn: en förfrågan till en ogenomskinlig adress, som betyder "körningen skedde". Om själva den förfrågan misslyckas räknas körningen ändå som en framgång; en misslyckad signal får inte förvandla en bra natt till en dålig.{N.ref("ExecStartPost=- pingskriptet; bindestrecket i början betyder att dess misslyckande inte får enheten att misslyckas. Skriptets egen kommentar: 'VAD SOM LÄMNAR MASKINEN: en HTTP GET till ett ogenomskinligt UUID. Ingen ticker, ingen kurs, ingen rapport, inget värdnamn, ingen kropp.'")}</li>
<li><strong>Misslyckande.</strong> Om körningen avslutas med ett fel eller avbryts för att den körts för länge startar schemaläggaren en andra enhet vars enda uppgift är att meddela. Den enheten kör ett vanligt skalskript, avsiktligt inte programmets eget språk, eftersom det som gick sönder kan vara programmets egen miljö. Skriptet skickar ett meddelande till ägarens telefon som säger vilken enhet som stannade och vad det betyder, med de sista åtta raderna ur loggen.{N.ref("OnFailure=vss-failure@%n.service; deploy/vss-notify-failure.sh. Hjärtslagsmodulen: 'Det är avsiktligt en vanlig curl i ett skalskript och INTE det här paketet: felet som rapporteras kan mycket väl VARA det här paketet.'")}</li>
</ul>
{N.flush()}

<p>Lägg märke till asymmetrin. Framgång är tyst på telefonen. Ägaren vill inte ha ett meddelande varje natt som säger att ingenting hände; ett meddelande som alltid kommer är ett meddelande som slutar läsas. Framgång ger sitt ljud någon annanstans, till en observatör vars uppgift är att märka om ljudet uteblir. Det är kapitel 18.</p>

<h2>Veckokörningen</h2>
<p>Screenern körs enligt samma mönster, på lördagsmorgnar klockan 08:00, på fredagens avstämda kurser, med en fyratimmarsgräns och ett strängare stängsel: mappen med ägarens fil är över huvud taget inte skrivbar för den. Den enda raden är beslutet "den schemalagda screeningen tar aldrig in ett bolag" skrivet på schemaläggarens språk.{N.ref("deploy/vss-screen.timer: Sat 08:00; tjänstens skrivskyddade konfigurationsmapp, i projektbeskrivningen kallad 'E93 på en rad'. Uppmätt 2026-08-31: omkring 38 minuter, 3 495 förfrågningar om grunddata, noll strypningar.")} En tredje timer, klockan 09:30 varje dag, tillhör dödmansgreppet.</p>
{N.flush()}

{fold("Enheterna, med ord", '''
<p><code>vss.timer</code> startar <code>vss.service</code> klockan 22:30 varje dag och tar igen om den missats. Tjänsten är engångs (one-shot), kör nattkommandot i en sandlåda som bara är skrivbar i data- och rapportmapparna, pingar den yttre observatören vid framgång och startar <code>vss-failure@vss.service</code> vid misslyckande. <code>vss-screen.timer</code> startar <code>vss-screen.service</code> på lördagar klockan 08:00 med konfigurationsmappen skrivskyddad. <code>vss-checkin.timer</code> startar <code>vss-checkin.service</code> klockan 09:30 varje dag. <code>vss-failure@.service</code> är en mall: namnet på den misslyckade enheten fylls i och skickas till notifieringsskriptet, som alltid avslutas med framgång, eftersom "en felnotifierare som kan misslyckas är en andra sak att övervaka".</p>
''')}
""",
    [("Schemaläggarens enheter och skript", "repo: deploy/vss.timer, deploy/vss.service, deploy/vss-screen.timer, deploy/vss-checkin.timer, deploy/vss-failure@.service, deploy/vss-ping-healthcheck.sh, deploy/vss-notify-failure.sh, deploy/README.md")],
)

# ---------------------------------------------------------------------------
# 18. THE DEAD MAN'S SWITCH
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "18-dead-mans-switch", "Dödmansgreppet",
    "En kraschad körning och en körning utan något att säga såg förr likadana ut: båda var tystnad. Nu ropar en observatör när något går sönder på maskinen, och en annan slår larm när en signal uteblir, vilket är det enda larm en död maskin fortfarande kan ge.",
    9, True,
    f"""
<p>Här är felet som hela det här kapitlet finns för att undanröja. Nattkörningen skickar ett meddelande till ägarens telefon bara när ett bolag behöver uppmärksamhet. De flesta nätter gör inget bolag det, och telefonen är tyst. Anta nu att körningen kraschade klockan 22:30 en tisdag och har varit död sedan dess. Telefonen är tyst. De två situationerna, "ingenting behöver dig" och "ingenting har körts på en vecka", ger exakt samma upplevelse: tystnad. Med verktygets egna ord: "en bevakning vars felläge är tystnad är en bevakning som slutar bli trodd första gången du får veta det den hårda vägen."{N.ref("vss/heartbeat.py, inledningen.")}</p>
{N.flush()}

<h2>Namnet, och var det kommer ifrån</h2>
<p>Tåg har ett handtag som föraren måste hålla eller trycka ned med jämna mellanrum. Om föraren segnar ned släpps handtaget och bromsarna går på. Det kallas dödmansgrepp, och konstruktionsidén är att säkerheten inte får bero på att en signal skickas, eftersom en människa som inte kan skicka den är precis det fall som den finns för. Den måste bero på en signal som fortsätter komma, med larmet på dess uteblivande.{N.ref("Wikipedia, Dead man's switch: 'Vigilance control was developed to detect this condition by requiring that the dead man's device be released momentarily and re-applied at timed intervals.'")} Programvaruversionen kallas <dfn>dödmansgrepp</dfn> (dead man's switch), och den fungerar på samma sätt: något väntar sig en regelbunden signal och slår larm när signalen inte kommer.</p>
{N.flush()}

{FIG["two_observers"]()}

<h2>Två observatörer, för det finns två sorters döda</h2>
<p>En maskin kan vara levande och trasig, eller så kan den vara död. De kräver olika observatörer, eftersom en observatör som bor på maskinen dör med den.</p>

<h3>Observatör ett bor på maskinen</h3>
<p>När körningen misslyckas startar schemaläggaren notifieraren från kapitel 17, som skickar till telefonen vad som stannade och de sista raderna ur loggen. Det här är den snabba observatören: den utlöses medan felet pågår, och den kan beskriva det. Dess svaghet är att den behöver att maskinen är uppe, att schemaläggaren går och att timern har utlösts. En timer som stängdes av efter en omstart startar ingenting, så ingenting misslyckas, så ingenting ropar, och det är precis det fel som mest liknar en tyst vecka.</p>
<p>Därför har observatör ett ett andra ben på sin egen timer: varje morgon klockan 09:30 kontrollerar ett separat jobb om en slutförd körning finns i registret och om nattimern fortfarande är aktiverad. Det körs avsiktligt på sin egen timer: "om kontrollen av körningen delade timer med körningen skulle felet som stoppade körningen stoppa kontrollen, och dödmansgreppet vore kopplat till sin egen strömförsörjning."{N.ref("deploy/vss-checkin.timer, kommentar. Körningen registrerar också sin egen slutförning i en tabell, med en gräns på 72 timmar för nattkörningen och 10 dagar för veckokörningen, och en provkörning eller en körning på ett enda bolag nollställer inte klockan.")}</p>
{N.flush()}

<h3>Observatör två bor utanför</h3>
<p>Inget av det hjälper om maskinen är avstängd, nätverket ligger nere eller hela schemaläggaren har stannat. En död maskin kan inte larma om sig själv. Det enda som kan upptäcka en död maskin är något som inte finns på den: en yttre tjänst som väntar sig en signal om dagen och slår larm när signalen inte kommit före en tidsgräns.{N.ref("vss/heartbeat.py: 'a dead VPS cannot page itself... Closing that needs an OUTSIDE observer — a service that expects a ping and alerts on its ABSENCE.'")} Det är den tomma förfrågan från framgångsutgången i kapitel 17. Den yttre tjänsten "är tyst så länge pingarna kommer i tid" och "slår larm så fort en ping inte kommer i tid", med en respitperiod efter den förväntade tiden.{N.ref("Övervakningstjänstens egen dokumentation; de föreslagna inställningarna i exempelmiljöfilen är en period på en dag och sex timmars respit.")}</p>
{N.flush()}

<h2>Varför frånvaro slår fel</h2>
<p>Ett felmeddelande behöver en avsändare. Varje avsändare kan fela på ett sätt som hindrar sändningen: processen kraschade innan den nådde den raden, nätverket låg nere, maskinen var avstängd. Ett larm på frånvaro behöver ingenting från den felande sidan. Det är den enda sortens larm vars täckning omfattar fallet att det som bevakas inte längre finns. Därför ger den lyckade körningen ett ljud till den yttre observatören och inget ljud till telefonen: ljudet är inte till för ägaren, det är till för det som kommer att märka när ljudet uteblir.</p>

<p>Ägarens ord när det här benet lades till: "en död VPS är exakt det fall jag vill ha täckt och ingen ping lämnar data."{N.ref("deploy/vss-ping-healthcheck.sh, med citat av ägaren, 2026-09-01.")}</p>
{N.flush()}

<h2>Varför notifieringsadressen hålls utanför förvaret</h2>
<p>Telefonnotiserna går via en offentlig pushtjänst där vem som helst som känner till ett ämnes namn kan posta till det. Ämnesnamnet är därför den enda hemlighet tjänsten har, och det ligger i en fil i ägarens hemkatalog som aldrig checkas in. Programmet läser det först från miljön, sedan från den filen, och skriver, loggar eller skriver aldrig ut det. Samma fil rymmer den yttre observatörens adress. Förvaret innehåller en exempelfil där båda lämnats tomma.{N.ref("deploy/vss.env.example: 'THE REAL FILE IS NEVER COMMITTED: the topic is the only secret ntfy has.' vss/env.py läser miljön först, sedan filen.")} Ämnet är bara utgående: ingenting i projektet läser någonsin från det, så även ett läckt namn låter en utomstående bara posta brus till ägarens telefon, inte läsa något.</p>
{N.flush()}

<h2>Vad som inte täcks, sagt i stället för antytt</h2>
<ul>
<li>Veckoscreeningen har ingen egen yttre signal. En död veckoscreening fångas bara av morgonkontrollen.</li>
<li>En maskin som är uppe, pingar och har fel. Den yttre observatören bevisar att körningen blev klar, inte att den var rätt.</li>
<li>Att själva den yttre observatören ligger nere.</li>
<li>Telefontunneln (kapitel 19) har ingen felnotis, av ett skäl som det kapitlet förklarar.</li>
</ul>

<h2>Ett fel som konstruktionen hittade hos sig själv</h2>
<p>Den 2026-09-13 startade sidservern om sju gånger i rad på grund av en saknad mapp, och notifieraren skickade sju meddelanden. Vart och ett sa att ingen rapport hade skrivits för dagen, eftersom den meningen hade skrivits för nattkörningen och återanvänts för varje enhet. För en sidserver som aldrig skriver en rapport var meningen falsk. Rättelsen, registrerad som en punkt i backloggen och incheckad samma dag, ger varje enhet sin egen korrekta mening om vad dess stannande betyder.{N.ref("Backlogpunkt B-13; commit 'the failure notifier says what stopped, not \"no report was written\" for every unit'.")} En notifierare som ljuger, även lite, är på väg att bli ignorerad.</p>
{N.flush()}

{decision(
    "Två observatörer. En på maskinen som beskriver vad som gick sönder; en utanför som slår larm när en daglig signal uteblir. Framgångsutgången signalerar till den yttre observatören och säger ingenting till telefonen.",
    "Tystnad måste betyda en sak. Det enda larm som täcker en död maskin är ett som ges av något som inte finns på den.",
    "En andra extern tjänst, vars egna avbrott är obevakat. En signal som lämnar maskinen varje natt, hållen till en enda tom förfrågan så att ingenting om boken lämnar den med.",
)}
""",
    [
        ("Dead man's switch, Wikipedia", "https://en.wikipedia.org/wiki/Dead_man%27s_switch"),
        ("Healthchecks.io-dokumentationen (larm vid saknad ping)", "https://healthchecks.io/docs/"),
        ("Hjärtslagsmodulen och enheterna", "repo: vss/heartbeat.py; deploy/vss-checkin.timer; deploy/vss-ping-healthcheck.sh; deploy/vss-notify-failure.sh; deploy/vss.env.example; reference/BACKLOG.md B-13"),
    ],
)

# ---------------------------------------------------------------------------
# 19. THE PHONE PROBLEM
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "19-the-phone", "Telefonproblemet",
    "Ett beslut är värdelöst på en server i ett annat land när kursen rör sig. Investeringsproblemets sista sträcka, och formen som byggdes för att täcka den: maskinen ringer ut, ingenting ringer in, och ytterdörren frågar vem du är innan något bakom den går att nå.",
    9, False,
    f"""
<p>Allt hittills producerar en sida på en hyrd server i ett datacenter. Ägaren sitter på ett tåg i Sverige med en telefon. Kursen på ett bolag på väntelistan har just korsat sin linje. Sidan vet det. Ägaren vet det inte. Det här är inte ett infrastrukturproblem; det är det sista steget i investeringsproblemet, och om det inte löses var resten dekoration.</p>

<h2>Begränsningen som gör det svårt</h2>
<p>Sidan rymmer hela boken: varje innehavt bolag, varje stopp, varje köplinje, varje värde. Att få den till en telefon betyder att få den av maskinen, och varje sätt att göra det öppnar något. Frågan är vad som ska öppnas, och reglerna som styr svaret skrevs ned som ett beslut innan det byggdes. Dess form: sidan får lämna maskinen bara genom en spärr som kontrollerar identitet; servern som lämnar över den får lyssna bara på maskinen själv; ingen inkommande port får öppnas; brandväggen förblir som den var.{N.ref("Beslut F1, leden (a) och (b), 2026-09-13.")}</p>
{N.flush()}

<h2>De former som ratades</h2>
<p>Registret listar inte alternativ som övervägdes och förkastades; det listar vad som är förbjudet, och varje förbud är formen på ett frestande svar.</p>
<ul>
<li><strong>Öppna en dörr i väggen.</strong> Kör en webbserver, öppna dess port i brandväggen, peka en telefon mot den. Snabbt, och det förvandlar en maskin som inte tar emot något från internet till en som tar emot anslutningar från vem som helst som hittar adressen. Driftsättningsanteckningarna: "Varje ändring som öppnar en port, binder [varje gränssnitt] eller lägger till en Access Bypass-policy upphäver syftet med den här driftsättningen och måste avgöras genom ett beslut, inte slås ihop."{N.ref("deploy/TUNNEL-NOTES.md, första stycket.")} Under bygget band servern sig faktiskt till varje gränssnitt i tre minuter, eftersom en konfigurationsrad som såg ut som en adress var en port. Det upptäcktes och rättades samma morgon, och det är det första av tre fel som anteckningarna registrerar.</li>
<li><strong>Lägg adressen i vanlig offentlig DNS utan spärren.</strong> Nåbar var som helst, och den skulle gå runt identitetskontrollen helt. Anteckningarna: "En DNS-only-post skulle kringgå Access helt."</li>
<li><strong>Lägg till en regel som låter viss trafik hoppa över identitetskontrollen.</strong> Spärrleverantören utvärderar sådana regler först. En sådan skulle göra boken offentlig "omedelbart och i tysthet". Det är förbjudet i beslutet, med fetstil.</li>
</ul>
{N.flush()}

<h2>Formen som byggdes</h2>
{FIG["tunnel"]()}

<p>Följ pilarna. På maskinen håller en liten webbserver sidan och lyssnar bara på maskinen själv: den är bunden till adressen som betyder "den här datorn och ingenting annat", så ingenting utifrån kan nå den direkt, någonsin.{N.ref("Servern binder bara loopback-adressen. Anteckningarna kallar den raden bärande: utan den skulle servern binda varje gränssnitt, offentligt.")} Bredvid den går ett andra litet program, en tunnelklient, som gör en enda sak: den ringer ut till en relässtjänst på internet och håller anslutningen öppen. Riktningen spelar roll och är hela konstruktionen. Maskinen gör en utgående anslutning, av samma slag som en webbläsare gör när den laddar en webbsida. Brandväggen rördes inte. Det enda internet kan nå på den här maskinen är porten för fjärrinloggning som redan fanns.{N.ref("deploy/TUNNEL-NOTES.md: tunnelklienten 'gör en utgående anslutning... brandväggen är oförändrad', och den enda offentliga lyssnaren är porten för fjärrinloggning som redan fanns.")}</p>
{N.flush()}

<p>Nu öppnar ägaren sidans adress på en telefon. Förfrågan går till reläet, inte till maskinen. Innan reläet gör något frågar en ytterdörr vem som frågar. Ytterdörren släpper in exakt en e-postadress. Den skickar en engångskod till den adressen och till ingen annan; en annan adress får inte ens någon kod, eftersom policyn vägrar innan en kod utfärdas. När koden är angiven öppnas dörren i 24 timmar. Först då för reläet förfrågan vidare nedför anslutningen som maskinen öppnade tidigare, maskinens egen server svarar med sidan, och sidan färdas tillbaka uppför samma linje till telefonen.{N.ref("Cloudflare Access: en applikation, en policy som tillåter en e-postadress, engångs-PIN som enda identitetsleverantör, 24 timmars session. Verifierat 2026-09-13: två andra adresser fick ingen PIN alls.")}</p>
{N.flush()}

<p>Tanken att åtkomst ska bero på vem du är och inte på vilket nätverk du sitter på har ett namn i säkerhetslitteraturen och en historia: det är principen Google beskrev 2014 när det flyttade sina interna verktyg ut på det publika internet bakom identitetskontroller, och den hade fått beteckningen zero trust tidigare av en branschanalytiker. Det här projektet uppfann inte formen; det lånade den minsta möjliga versionen av den.{N.ref("Ward och Beyer, 'BeyondCorp: A New Approach to Enterprise Security', ;login: 39(6), 2014; Kindervag, Forrester Research, 2010. Ingen av texterna citeras här; hänvisningen är en pekare, inte ett påstående om deras ordalydelse.")}</p>
{N.flush()}

<h2>Vad det kostar, enligt beslutet</h2>
<p>Sidan passerar ett företags infrastruktur som ägaren inte kontrollerar, och det företaget dekrypterar den i sin kant. Med beslutets ord: "Sidan är klartext i deras kant: innehav, statusar, spärrresultat, MBP och stopp, läsbara för Cloudflare och för vem som helst som tvingar eller bryter sig in hos Cloudflare. Det här går inte att mildra inom den här arkitekturen. Det är priset för att läsa boken på en telefon från ett godtyckligt nätverk, och jag betalar det medvetet." Ytterdörren har en enda faktor: den som kontrollerar postlådan kontrollerar sidan. Och tunnelklienten måste köras som en systemtjänst med en inloggningsuppgift som ägarens eget konto inte kan läsa, vilket betyder att den inte kan använda felnotifieraren från kapitel 17. Om tunneln dör slutar sidan laddas och telefonen förblir tyst. Nattkörningen och dess egen larmning är inte beroende av den.{N.ref("Beslut F1: 'WHAT THIS COSTS' under leden (a) och (b); deploy/TUNNEL-NOTES.md, 'Units — Option C'.")}</p>
{N.flush()}

{decision(
    "Sidan når telefonen genom en utgående tunnel till ett relä, bakom en ytterdörr som släpper in en adress med engångskod. Servern lyssnar bara på maskinen själv. Ingen port öppnas.",
    "Ett beslut som inte kan nå ägaren när kursen rör sig var inte värt att fatta. Varje inkommande form öppnar maskinen; den utgående formen öppnar bara en sida, och bara för en person.",
    "Sidan är läsbar för reläoperatören. Dörren har en enda faktor. Tunneln kan inte larma telefonen när den dör. Var och en är nedskriven i beslutet som priset.",
)}
""",
    [
        ("Ward och Beyer (2014), BeyondCorp: A New Approach to Enterprise Security, ;login:", "https://www.usenix.org/publications/login/dec14/ward"),
        ("Beslut F1 och tunnelanteckningarna", "repo: reference/FRAMEWORK-EDITS.md F1; deploy/TUNNEL-NOTES.md; deploy/vss-tunnel.service; deploy/vss-overview.service"),
    ],
)

# ---------------------------------------------------------------------------
# 20. THE BOUNDARY
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "20-the-boundary", "Gränsen",
    "En fil serveras, varje annan sökväg nekas. Mappen bakom servern rymmer dussintals privata filer. Skillnaden mellan en exponerad fil och alla av dem är ett enda block konfiguration, och att ta bort det skulle exponera allt i tysthet.",
    5, False,
    f"""
<p>Kapitel 19 fick en sida till telefonen. Det här kapitlet handlar om de två orden "en sida", eftersom servern som lämnar över den sitter i en mapp full av sådant som inte får färdas.</p>

{FIG["boundary"]()}

<h2>Vad som finns i mappen</h2>
<p>Sidan skrivs in i rapportmappen, bredvid varje nattrapport, skuggboken, registret över försäljningar, förköpsanteckningarna för bolag som övervägs och underlagen för research. Den dag tunneln byggdes rymde mappen 93 filer. Alla utom en är ägarens privata research, och flera av dem är precis de dokument vars innehåll hela metoden är byggd för att skydda från att ses för tidigt: ägarens tillväxtbedömningar och resonemang.{N.ref("deploy/TUNNEL-NOTES.md, THE BOUNDARY: 'reports/ held 93 files on 2026-09-13'.")}</p>
{N.flush()}

<h2>Regeln</h2>
<p>Servern har en regel med två halvor. En förfrågan om rotadressen besvaras med översiktssidan. En förfrågan om vilken annan sökväg som helst, vad som helst, besvaras med "hittades inte" och noll byte. Det är hela den publicerade ytan: en adress.{N.ref("Verifierat 2026-09-13 efter den sista rättelsen: en förfrågan om roten gav sidan; en förfrågan om någon av de andra filerna i mappen gav 404 med 0 byte; den enda lyssnande adressen på maskinen var loopback-adressen; en förfrågan till det publika namnet utan inloggning omdirigerades till ytterdörren.")}</p>
{N.flush()}

<h2>Varför ett block konfiguration spelar roll</h2>
<p>Regeln är några rader i serverns konfigurationsfil. Ta bort halvan som säger "allt annat: hittades inte", och serverns standardbeteende tar över, vilket är att servera vilken fil förfrågan än nämner. Varje fil i mappen skulle då ligga en adress bort, bakom samma ytterdörr men inte längre bakom något annat. Ingenting skulle misslyckas. Inget skulle larma. Sidan skulle fortsätta laddas precis som förut. Beslutet säger det: "Det blocket är gränsen; driftsättningsanteckningarna säger det, och varje ändring av det är ett beslut, inte en sammanslagning."{N.ref("Beslut F1, led (b), WHAT THIS COSTS.")}</p>
{N.flush()}

<p>Det här är den allmänna formen på en gräns som är värd att oroa sig för: en begränsning vars borttagande inte ändrar något synligt. De tre felen som hittades under bygget var alla av det slaget. Servern band sig till varje nätverksgränssnitt i tre minuter, och ingenting klagade. En saknad mapp fick servern att starta om sju gånger, och bara notifierarens upprepning avslöjade det. En konfigurationsrad i fel form fick servern att svara på varje förfrågan från reläet med en tom sida på noll byte och en lyckokod, eftersom raden också fungerade som ett filter för vilka förfrågningar den över huvud taget skulle svara på.{N.ref("deploy/TUNNEL-NOTES.md, 'Three bugs found during the build — all fixed'.")} Vart och ett hittades genom att testa saken direkt, inte genom att vänta på ett larm, eftersom inget av dem skulle ha utlöst ett.</p>
{N.flush()}

<p>Säkerhetslitteraturen har ett namn på principen som blocket genomdriver, och den är femtio år gammal: varje program ska arbeta med den minsta uppsättning behörigheter som behövs för att utföra jobbet.{N.ref("Saltzer och Schroeder, 'The Protection of Information in Computer Systems', 1975.")} Serverns jobb är en fil. Dess behörighet är en adress.</p>
{N.flush()}

{decision(
    "Servern svarar på en adress med en fil och på allt annat med hittades inte. Blocket som genomdriver detta är utpekat som gränsen, och att ändra det kräver ett beslut.",
    "Mappen rymmer ägarens privata research. En förvald filserver skulle exponera allt av det utan någon synlig förändring.",
    "En konfiguration vars återfall är tyst. Det enda försvaret är en nedskriven regel om att ändringar av den är beslut, och ett test som ber servern om något den måste neka.",
)}
""",
    [
        ("Saltzer och Schroeder (1975), The Protection of Information in Computer Systems", "https://www.cs.virginia.edu/~evans/cs551/saltzer/"),
        ("Gränsen, som den är registrerad", "repo: deploy/TUNNEL-NOTES.md; deploy/vss-overview.service; reference/FRAMEWORK-EDITS.md F1 limb (b)"),
    ],
)

# ---------------------------------------------------------------------------
# 21. THE PAGE THAT ARRIVES
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "21-the-page", "Sidan som kommer fram",
    "Vad ägaren ser på telefonen, och reglerna för vad den får säga: ett avstånd från en kurs, aldrig ett utlåtande; inget villkor på köpsidan utan de villkor som kvalificerar det; dess egen ålder angiven två gånger så att en gammal sida inte kan passera som färsk.",
    8, False,
    f"""
<p>Sidan är en enda fil: ingen serverlogik, inget ramverk, inget skript. Den öppnas från en lokal fil på ägarens egen maskin precis som genom tunneln, och den är byggd för att läsas på en telefon i den ordning en människa faktiskt skulle ställa frågorna.{N.ref("vss/overview.py; konstruktionsreglerna stöds var och en av ett test, beskrivet i projektbeskrivningen §4.7.")}</p>
{N.flush()}

<h2>Tre frågor, i ordning</h2>
<ol>
<li><strong>Behöver något mig i dag?</strong> Ett block överst, i vanliga meningar. Antingen "ingenting", eller de två–tre saker som gör det: en köplinje korsad, ett stopp brutet, ett innehavt bolag utan stopp, en daterad händelse inom sju dagar. Listan över sorter är sluten, så blocket kan inte växa till ett flöde. Bredvid står alltid vad som kontrollerades, eftersom "ingenting behöver dig" och "ingen tittade" annars är samma tystnad.</li>
<li><strong>Var står allt mot sitt värde?</strong> Ett kort per bolag. Ett kort, inte en tabell, eftersom en tabell är till för att jämföra fyrtio saker och ett kort är till för att känna igen en. Kursen stor; värdet och köplinjen bredvid; ett år av avstämda slutkurser ritat som en liten linje; och ett spår som visar var kursen ligger mellan halva värdet och hälften till, på en skala som aldrig skalas om per bolag. En bild ersätter aldrig en siffra.</li>
<li><strong>Vad är på väg?</strong> De olösta daterade händelserna, de närmaste först. En lång anteckning viks ihop, kapas aldrig, eftersom "ett utelämningstecken på en post är en post som ingen kan läsa."</li>
</ol>

<h2>Reglerna för vad den får säga</h2>

<h3>Ett avstånd, aldrig ett utlåtande</h3>
<p>Sidan använder grönt och rött. Den använder dem för att säga hur långt en kurs är från en linje, i fem band vars gränser är metodens egna tal, och för ingenting annat. Ett bolag kan vara grönt och inte behöva något; bolaget som behöver ägaren kan vara rött. Färg läggs aldrig på ett helt kort, eftersom ett grönt kort läses som ett godkännande. Ett bolag som är billigt men har fallit på en spärr ritas nedtonat, med skälet angivet i ord, så att en billig stängd dörr inte läses som en inbjudan. Ingen färg någonstans bär betydelse på egen hand.{N.ref("vss/overview.py: 'THE DISTANCE SCALE... it is a MEASUREMENT, never a verdict. It says HOW FAR, and nothing about whether to act.' Band vid 0, 5, 25 och 75 procent.")}</p>
{N.flush()}

<h3>Inget villkor på köpsidan utan de villkor som kvalificerar det</h3>
<p>Om sidan säger att en kurs ligger under sin köplinje säger samma mening vad mer som måste gälla: att avläsningen är aktuell, att villkoren från kapitel 11 håller. Inte en rad längre ned. Samma mening, eftersom "den läsare som slutar efter första halvan är den läsare den här sidan är till för."{N.ref("vss/overview.py: 'A BUY-SIDE CONDITION NEVER STANDS ALONE. The qualifying clause goes in the SAME SENTENCE, not a line below it.'")}</p>
{N.flush()}

<h3>Den anger sin egen ålder, två gånger</h3>
<p>En körning som misslyckas skriver ingenting. Servern fortsätter servera den senaste goda sidan. Sidan ser identisk ut med en färsk, och ägaren läser förra torsdagens statusar i tron att de är kvällens. Det felet är osynligt för varje larm i kapitel 18, eftersom körningen antingen skedde eller inte, och sidans ålder är en annan fråga. Så sidan skriver ut den exakta tiden den genererades, med tidszon, i sidhuvudet, synlig på en telefon utan att rulla, och igen i första meningen i sidfoten. Sidan kan inte markera sig själv som gammal, eftersom det skulle kräva ett skript och skript är förbjudna; den kan bara göra sin ålder omöjlig att missa, och subtraktionen är ägarens.{N.ref("Beslut F1 led (c) krav 1, och beslut F2 som drar tillbaka krav 2. Genomfört 2026-09-13.")}</p>
{N.flush()}

<h3>Den väljer aldrig</h3>
<p>Där registret rymmer två värderingar för ett bolag och inget säger vilken som är den aktuella skriver sidan ut DATA SAKNAS och länkar båda. Den tar inte den nyare. En sorteringsordning är inte ett beslut, och sidan får inte besvara en fråga som ägaren inte har besvarat.{N.ref("vss/overview.py: 'it never chooses (two run records and no entry naming one ⇒ DATA MISSING and both linked — a filename sort must not answer E39's question)'.")}</p>
{N.flush()}

<h2>Varför en sida som inte uttrycker någon åsikt är mer användbar</h2>
<p>En sida som sa "köp BOLAG A" skulle läsas för sitt utlåtande, och utlåtandet skulle vara rätt eller fel, och ägaren skulle inte lära sig något åt något håll om huruvida avläsningen bakom det var sund. En sida som säger "BOLAG A ligger 3 procent över sin linje, linjen värderades på junirapporten, nästa rapport kommer om nio dagar och en siffra är overifierad" ger ägaren varje fakta som behövs för att avgöra och undanhåller det enda som skulle låta ägaren sluta tänka. Den är mer arbete att läsa. Det är det den är till för.</p>

{decision(
    "Sidan visar läge, avstånd och ålder. Den uttrycker inget utlåtande om något bolag, färgar inget som godkännande, kvalificerar varje mening på köpsidan i samma mening och skriver ut sin egen genereringstid två gånger.",
    "Sidan är det ägaren handlar på. Allt den avgjorde skulle avgöras utan läsningen, och allt den dolde om sin egen ålder skulle bli trott.",
    "Den kan inte varna för att den är gammal; ägaren måste läsa tiden och subtrahera. Den ger aldrig svaret, så varje natt gör ägaren tänkandet på nytt.",
)}
""",
    [("Översiktssidans generator och dess beslut", "repo: vss/overview.py; vss/render.py; reference/FRAMEWORK-EDITS.md F1, F2")],
)

# ---------------------------------------------------------------------------
# 22. WHAT IT DOES NOT DO
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "22-limits", "Vad den inte gör",
    "Säkerhetsgränserna, angivna så som driftsättningsanteckningarna anger dem. Sedan metodens gränser: den kan inte säga att ett bolag är bra, den kan inte göra dig tålmodig, den kan inte hindra dig från att åsidosätta den, och den vägrar avgöra något åt dig. Det sista är avsiktligt.",
    7, False,
    f"""
<p>Det här kapitlet är en lista, och listan är inte mjukad. Varje punkt nedan står i projektets egna anteckningar, de flesta under en rubrik som lyder "What this does NOT protect against".</p>

<h2>Säkerhet</h2>
<ul class="limits">
<li><span class="what">Reläoperatören kan läsa sidan.</span><span class="does">Ingenting. Beslutet kallar det omöjligt att mildra inom den här arkitekturen och godtar det som priset för att läsa boken på en telefon från ett godtyckligt nätverk.</span></li>
<li><span class="what">Ytterdörren har en enda faktor. Den som kontrollerar postlådan kontrollerar sidan.</span><span class="does">Ingenting utöver postlådans egen säkerhet. Angivet i beslutet.</span></li>
<li><span class="what">En 24-timmarssession på en olåst telefon förblir öppen tills den löper ut.</span><span class="does">Ingenting. Telefonens lås är kontrollen.</span></li>
<li><span class="what">En enda bypass-regel hos spärrleverantören gör sidan offentlig omedelbart och i tysthet.</span><span class="does">Förbjudet genom beslut, i fetstil. Ingen mekanism förhindrar det.</span></li>
<li><span class="what">Sidans offentliga namn syns i certifikatloggar, så den går att upptäcka.</span><span class="does">Ingenting. "Att vara obskyr är inte kontrollen; Access är det."</span></li>
<li><span class="what">Kontot som styr domänen, tunneln och spärren skyddas av samma postlåda som ytterdörren.</span><span class="does">Ingenting ännu. Noterat.</span></li>
<li><span class="what">Om tunneln dör får telefonen inte veta det.</span><span class="does">Ingenting. Tunneln körs som en systemtjänst som inte kan använda felnotifieraren. Nattkörningen och dess larmning är inte beroende av den.</span></li>
<li><span class="what">Sidan kan inte markera sig själv som gammal.</span><span class="does">Den skriver ut sin genereringstid två gånger. Kravet på att markera sig själv drogs tillbaka som omöjligt att bygga.</span></li>
<li><span class="what">Gränsen är ett konfigurationsblock vars borttagande är tyst.</span><span class="does">Utpekat som gränsen; varje ändring är ett beslut. Ett test ber servern om en fil den måste neka.</span></li>
</ul>
<p>Varje rad ovan är hämtad från driftsättningsanteckningarna och de två besluten på sidan.{N.ref("deploy/TUNNEL-NOTES.md, 'What this does NOT protect against'; beslut F1; beslut F2.")}</p>
{N.flush()}

<h2>Övervakning</h2>
<ul class="limits">
<li><span class="what">Veckoscreeningen har ingen yttre signal.</span><span class="does">Morgonkontrollen är det enda skyddet.</span></li>
<li><span class="what">En maskin som är uppe och har fel pingar som om den hade rätt.</span><span class="does">Ingenting. Observatören bevisar att en körning blev klar, inte att den var korrekt.</span></li>
<li><span class="what">Den yttre observatören kan själv ligga nere.</span><span class="does">Ingenting.</span></li>
</ul>

<h2>Metoden</h2>
<ul class="limits">
<li><span class="what">Den kan inte säga att ett bolag är bra.</span><span class="does">Den kan säga att ett bolag inte kunde anmärkas på i en fast uppsättning grova test, och vilken tillväxt dess kurs förutsätter. Huruvida bolaget är bra är en avläsning, och avläsningen är ägarens.</span></li>
<li><span class="what">En av dess fem spärrar har aldrig körts.</span><span class="does">Registrerad som DATA SAKNAS för varje bolag, behållen, och väntar på de jämförelsesiffror den behöver.</span></li>
<li><span class="what">Dess värdeuppskattning vilar på en tillväxtbedömning som aldrig kommer att verifieras, och en diskonteringsränta som är en preferens.</span><span class="does">Båda skrivs ned innan kursen ses, och känsligheten för räntan skrivs ut bredvid varje köpkurs. Beslutet säger båda sakerna med de orden.</span></li>
<li><span class="what">Den kan inte göra dig tålmodig.</span><span class="does">Den kan göra väntandet till ett nedskrivet tal i stället för ett humör, och rapportera avståndet varje natt. Huruvida ägaren köper i 93 ändå är inte verktygets sak att förhindra.</span></li>
<li><span class="what">Den kan inte hindra dig från att åsidosätta den.</span><span class="does">Ägarens fil är ägarens. Varje status, nivå och värde i den kan redigeras för hand, och verktyget rapporterar troget vad det än hittar där. Vad det inte kommer att göra är att räkna fram en köpkurs från ett värde som saknar protokoll, eller acceptera en som skrivits in.</span></li>
<li><span class="what">Den vägrar avgöra något åt dig.</span><span class="does">Den här är avsiktlig, och den är konstruktionen. Se nedan.</span></li>
</ul>

<h2>Varför den sista är med flit</h2>
<p>Allt i den här listan utom den sista punkten är en gräns som projektet skulle ta bort om det kunde. Den sista är skälet till att projektet finns. Ett verktyg som avgjorde skulle bli litat på, och ett verktyg som litas på slutar kontrolleras, och ett verktyg som inte kontrolleras har fel på sätt som ingen märker förrän pengarna är borta. Verktygets vägran att avgöra är det som tvingar ägaren att fortsätta läsa, varje natt, med de ofärdiga delarna av jobbet utpekade på sidan. Det går långsammare än att bli tillsagd. Det är den enda version av det här som kan granskas i efterhand, av ägaren, mot ett register som ägaren skrev innan utfallet var känt.</p>
""",
    [("De registrerade gränserna", "repo: deploy/TUNNEL-NOTES.md; vss/heartbeat.py (what is not covered); reference/FRAMEWORK-EDITS.md E28, E29, E99, F1, F2")],
)

# ---------------------------------------------------------------------------
# 23. CLOSE
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "23-close", "Den långsamma vägen, gjord uthärdlig",
    "Metoden skrevs före koden, och koden kan inte överrösta den. Varje nej mäts. Varje regel anger sitt pris, även de som var fel och drogs tillbaka. Det här är ingen genväg.",
    4, True,
    f"""
<p>Börja där webbplatsen började. Tvåtusen bolag, en person, inget sätt att inifrån veta om ett beslut var omsorgsfullt eller bara tur. Här är vad som byggdes som svar, i ett stycke.</p>

<p>En nedskriven metod, ändrad bara genom daterade beslut som ägaren fattar. En grov screening som tar bort det som kan anmärkas på i offentliga siffror och inte hittar något. En läsning som använder enbart bolagets egna dokument, där varje siffra bär sitt ursprung och sin period, och en värdering som skriver ut ingenting hellre än ett tal med ett hål. En omvändning som frågar vad kursen förutsätter i stället för vad verksamheten är värd, och en regel att ägarens tro måste vara registrerad, daterad, innan det talet finns. Tre utfall för varje test, så att att inte veta aldrig registreras som att falla. Ett beslut som är tre nedskrivna tal, framtagna i ordning, innan pengarna rör sig. En bok över varje nej, mätt mot marknaden i efterhand och läst en gång om året. Och en maskin som körs varje natt, mäter, minns och är byggd så att den inte kan avgöra.</p>

<h2>Tre saker att ta med dig</h2>
<p><strong>Metoden skrevs före koden, och koden kan inte överrösta den.</strong> Varje tröskelvärde i programmet hänvisar till det beslut som satte det. En ändring av vad programmet gör utan ett beslut bakom sig är, enligt projektets egen måttstock, fel sak. Reglerna står över koden eftersom regler skrivna utan insats i svaret är de enda regler som är värda att ha när det finns en.</p>

<p><strong>Varje nej mäts.</strong> Metoden har sagt nej till varje bolag den har läst på nära håll. Det registret bevisar ingenting på egen hand. Skuggboken finns för att ägaren om ett år ska kunna ta reda på om nejen var dyra, och beslutet som skapade den säger att dess syfte är "att kunna säga att metoden inte fungerar".</p>

<p><strong>Varje regel anger sitt pris, även de som drogs tillbaka.</strong> En spärr med två led som inte mätte något togs bort med orden "inte vidgat, inte mjukat upp, borttaget". Ett krav på telefonsidan beslutades på morgonen och drogs tillbaka samma eftermiddag som omöjligt att bygga, med skälet nedskrivet. En hänvisning i ett commitmeddelande visade sig peka på ett avsnitt som inte finns, och rättelsen finns i registret. Det här är inga pinsamheter. De är beviset för att processen rättar sig själv skriftligen, genom den som har rätt att rätta, i stället för genom glidning.</p>

<h2>Vad det här är</h2>
<p>Ägarens egen sammanfattning av tesen är den som den här webbplatsen byggdes för att bära: det finns inga lätta sätt att tjäna pengar på det här; det tar tid, och kunskap förvärvas med tiden, och verktyget är den tiden, bevarad.</p>

<p>Ingenting här kommer att tala om för dig vad du ska köpa. Om du har följt med vet du vad som krävs för att ta reda på det: en gräns du har skrivit ned, en screening som bara tar bort, en läsning från källan, en tro i registret före talet, tre utfall, tre tal och en bok över det du vände ryggen åt. Det här är ingen genväg. Det är den långsamma vägen, gjord uthärdlig.</p>
""",
    [("Besluten som citeras i det här kapitlet", "repo: reference/FRAMEWORK-EDITS.md E30, E114, F1, F2; VSS-PROJECT-BRIEF-2026-09-10.md §0–§1")],
)
