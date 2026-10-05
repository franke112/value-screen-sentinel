"""Del ett — metoden. Kapitel 1 till 12.

Varje påstående om systemet är hämtat från arkivet (beslutsnummer och
modulnamn anges i de hopfällbara rutorna). Varje påstående om investering
eller om var en idé kommer ifrån styrs till en URL i kapitlets källor.
Facktermer förekommer en gång, efter den enkla versionen, markerade med <dfn>.
"""

from diagrams_sv import ALL as FIG


class Notes:
    """Numbered notes, Tufte-style: the note is emitted inline at the point
    of reference as a span, so it floats beside the sentence on a wide
    screen and follows the sentence on a narrow one. flush() is kept for
    the templates and returns nothing."""

    def __init__(self):
        self.n = 0

    def ref(self, txt):
        self.n += 1
        n = self.n
        return (f'<a class="noteref" href="#n{n}" id="r{n}" aria-label="note {n}">{n}</a>'
                f'<span class="note" id="n{n}" role="note"><span class="nn">{n}</span>{txt}</span>')

    def flush(self):
        return ""


def fold(title, inner):
    return f'<details class="fold"><summary>{title}</summary><div class="inner">{inner}</div></details>'


def decision(decided, why, cost):
    return (f'<dl class="decision"><dt>Beslut</dt><dd>{decided}</dd>'
            f'<dt>Varför</dt><dd>{why}</dd><dt>Kostnad</dt><dd>{cost}</dd></dl>')


def example(inner, tag="Räkneexempel: BOLAG A"):
    return f'<div class="example"><span class="tag">{tag}</span>{inner}</div>'


def wrong(inner, tag="Det naturliga sättet, som är fel"):
    return f'<div class="wrong"><span class="tag">{tag}</span>{inner}</div>'


def right(inner, tag="Regeln"):
    return f'<div class="right"><span class="tag">{tag}</span>{inner}</div>'


CHAPTERS = []


def chapter(slug, title, lede, minutes, short, body, sources):
    CHAPTERS.append(dict(slug=slug, title=title, lede=lede, minutes=minutes,
                         short=short, body=body, sources=sources))


# ---------------------------------------------------------------------------
# 1. THE PROBLEM
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "01-the-problem", "Problemet",
    "Ungefär tvåtusen bolag där du kan köpa en bit, en enda person, några kvällar i veckan och inget sätt att veta om du lurar dig själv.",
    5, True,
    f"""
<p>Börja med storleken. På de börser som en svensk privatinvesterare når via ett vanligt depåkonto finns det ungefär tvåtusen bolag som är stora nog att överväga.{N.ref("Verktygets egen lista innehåller 2 011 instrument bland de stora och medelstora bolagen i USA, Europa och på de nordiska börserna. Se kapitel 4.")} Vart och ett publicerar en rapport var tredje månad. Varje rapport är dussintals sidor lång. Ingen som har ett jobb läser tvåtusen av dem.</p>
{N.flush()}
<p>Så folk läser dem inte. De köper på en historia i stället. En vän nämner ett bolag. En tidning skriver att en bransch är het. Ett pris har stigit i ett år, vilket känns som ett belägg. Eller ett pris har halverats, vilket känns som ett fynd. Inget av detta är ett skäl. Så här hamnar man som ägare till något man inte kan beskriva, till ett pris man inte kan försvara, utan aning om vad som skulle få en att sälja.</p>

<p>Nu kommer den svårare delen. Anta att du bestämmer dig för att göra det ordentligt. Du väljer ett bolag, läser dess rapporter, räknar ut vad du tror att det är värt och köper under det. Bra. Fråga dig nu: hur vet du att din siffra inte påverkades av priset du redan hade sett? Hur vet du att du inte läste rapporten på jakt efter skäl att köpa, och hittade dem, eftersom folk alltid hittar dem? Hur vet du att de tjugo bolag du avfärdade inte var de du borde ha köpt, när du aldrig kontrollerade det?</p>

<p>Det här är inga retoriska frågor. De är de frågor som hela projektet finns till för att besvara, och det ärliga första svaret på var och en är: du vet inte. Du kan inte veta det inifrån. Den som bestämmer ensam har inget sätt att skilja ett bra beslut från ett lyckosamt, eller en noggrann läsning från en motiverad.</p>

<p>Allt som följer är en uppsättning vanor för en person som har accepterat detta, och en maskin som är byggd för att hålla vanorna på plats när personen är trött, upphetsad eller har ett intresse i svaret.</p>

<h2>Vad resten av webbplatsen är</h2>
<p>Del ett är metoden: vad det innebär att köpa en bit av ett företag för mindre än det är värt, hur tvåtusen namn blir fem, varför de flesta av de fem får ett nej, och hur ett beslut skrivs ned så att det inte i det tysta kan skrivas om. Del två är maskinen: ett litet program på en hyrd server som körs varje natt, mäter och vägrar avgöra.</p>

<p>Inget här är en genväg. När du har läst klart vet du inte vilket bolag du ska köpa. Du vet vad som krävs för att ta reda på det, och varför det inte går att hoppa över.</p>
""",
    [("Verktygets universumfiler och deras antal", "repo: config/universe/, VSS-PROJECT-BRIEF-2026-09-10.md §4.6")],
)

# ---------------------------------------------------------------------------
# 2. WHAT VALUE INVESTING IS
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "02-value", "Vad värdeinvestering är",
    "En bit av ett verkligt företag är värd något. Marknaden anger ett pris för den varje dag. Det är två olika tal, och gapet mellan dem är hela möjligheten.",
    9, True,
    f"""
{example('''
<p>BOLAG A är ett företag som tillverkar något vardagligt och säljer det varje år. Förra året, efter att ha betalat personal, leverantörer och skatt, och efter att ha lagt det som krävdes för att hålla fabrikerna igång, hade det 10 kvar per aktie. Det har gjort ungefär så i tio år. Det är knappt skyldigt någon något av betydelse.</p>
<p>De där 10 per aktie i överskottskassa, år efter år, är vad du faktiskt köper när du köper en aktie. Inte en ticker, inte ett diagram. En fordran på ett flöde av kontanter från ett företag som finns på riktigt.</p>
''')}

<p>Här är den första idén, och den som allt annat vilar på. När du köper en aktie köper du en andel av ett verkligt företag som tjänar verkliga pengar. Andelen kallas en <dfn>aktie</dfn>, och bolagets överskottskassa efter allt det måste betala kallas dess <dfn>fritt kassaflöde</dfn>. Företaget är värt något: ett belopp som en förnuftig person skulle betala för rätten till det kassaflödet så länge det varar. Det beloppet är dess <dfn>värde</dfn>.</p>

<p>Den andra idén: varje handelsdag anger marknaden ett tal som du kan köpa eller sälja aktien till. Det talet är <dfn>priset</dfn>. Priset rör sig varje minut. Företagets värde gör det inte. En fabrik blir inte värd mindre mellan tisdag och onsdag för att de som handlar med dess aktier blev nervösa.</p>

<p>Pris och värde är inte samma tal, och för det mesta vet ingen hur långt ifrån varandra de ligger. Det är möjligheten. Benjamin Graham, som undervisade om detta vid Columbia på 1930-talet, formulerade det i en mening som hans elev Warren Buffett har upprepat i femtio år: "Pris är vad du betalar; värde är vad du får."{N.ref("Buffett, brev till Berkshire Hathaways aktieägare för 2008, sidan 4, med hänvisning till Graham. Källan finns i den hopfällbara rutan nedan.")}</p>
{N.flush()}

{FIG["price_vs_value"]()}

<p>Graham hade ett sätt att göra skillnaden tydlig. Föreställ dig att du äger en andel i ett företag tillsammans med en kompanjon som är lite virrig. Varje dag nämner han ett pris som han köper din hälft till eller säljer sin till dig för. Vissa dagar är han yr av glädje och nämner ett löjligt högt pris. Vissa dagar är han förtvivlad och nämner ett löjligt lågt. Han tar inte illa upp om man ignorerar honom. Misstaget är att låta hans sinnesstämning avgöra vad företaget är värt. Möjligheten är att sälja till honom när han är yr av glädje och köpa av honom när han är förtvivlad, och i övrigt gå vidare med sitt liv.{N.ref("Graham, The Intelligent Investor, kapitel 8; återberättad av Buffett i hans brev från 1987: 'Mr. Market is there to serve you, not to guide you. It is his pocketbook, not his wisdom, that you will find useful.'")} Graham kallade kompanjonen Mr Market.</p>
{N.flush()}

<h2>Säkerhetsmarginal</h2>
<p>Du kommer aldrig att veta värdet exakt. Du kommer att uppskatta det, och din uppskattning blir fel med ett belopp som du inte kan känna till i förväg. Därför köper du inte till din uppskattning. Du köper långt under den, och avståndet mellan din uppskattning och det högsta du vill betala är ditt utrymme för att ha fel.</p>

<p>Tänk på en vägbro. Ingenjören räknar ut att den klarar en viss last och sätter sedan en skylt med en gräns långt under den. Inte för att beräkningen är slarvig, utan för att en beräkning är en beräkning, stålet är verkligt och lastbilen är tung. Gapet mellan den skyltade gränsen och den beräknade lasten är det som gör att bron överlever ingenjörens misstag. Graham kallade samma gap, tillämpat på köp av ett företag, <dfn>säkerhetsmarginalen</dfn>, och utsåg den till investeringens centrala begrepp.{N.ref("Graham, The Intelligent Investor (1949), kapitel 20, 'Margin of Safety as the Central Concept of Investment'. Brobilden här är webbplatsens egen; en liknande bild tillskrivs ofta Buffett, men den gick inte att verifiera mot någon primärtext och görs inte gällande som hans.")}</p>
{N.flush()}

{FIG["margin_of_safety"]()}

<h2>Varför tålamod är mekanismen och inte ett personlighetsdrag</h2>
<p>Här har folk det bakvänt. Tålamod låter som en dygd som man antingen har eller inte har. Här är det ingen dygd. Det är ett steg i förfarandet.</p>

<p>Om du har kommit fram till att BOLAG A är värt 100 och att du högst vill betala 85, så är den rätta åtgärden varje dag då kursen är 93 ingenting. Inte "avvakta och se". Ingenting, som ett beslut, fattat och nedskrivet. Möjligheten finns bara för att de flesta aktörer inte kan göra ingenting: de måste vara investerade, eller reagera på nyheter, eller visa aktivitet för någon. Den som kan sitta still på 93 i ett år och köpa på 84 den enda dag kursen kommer dit är inte lugnare än de andra. Hen har helt enkelt skrivit ned talet i förväg, och talet gör väntandet åt hen.</p>

<p>Graham igen, via Buffett: "På kort sikt är marknaden en röstningsmaskin, men på lång sikt är marknaden en våg."{N.ref("Buffett, brev till aktieägarna 1993, med citat från Graham. Källan finns i den hopfällbara rutan.")} Röster är billiga och snabba. Vikt tar tid att visa. Metoden är byggd för vägningen.</p>
{N.flush()}

{fold("Var det här kommer ifrån", '''
<ul>
<li>"Pris är vad du betalar; värde är vad du får." Buffett, aktieägarbrevet för 2008, sidan 4, med hänvisning till Graham. <span class="how">Webbplatsens författare hämtade meningen ur brevets PDF.</span></li>
<li>Mr Market: Graham, The Intelligent Investor, kapitel 8; Buffetts återberättelse, brevet från 1987.</li>
<li>Röstningsmaskin och våg: Buffett, brevet från 1993, med citat från Graham.</li>
<li>Säkerhetsmarginal: Graham, The Intelligent Investor, kapitel 20.</li>
</ul>
<p>Där det här projektet skiljer sig från Graham: marginalen är en fast andel som bestäms av hur väl företaget förstås (kapitel 11), och den skrivs ned innan man tittar på priset (kapitel 8). Graham beskrev principen; projektet gör den till en regel med ett tal.</p>
''')}
""",
    [
        ("Buffett, brev till aktieägarna 2008 (sidan 4: 'Price is what you pay; value is what you get')", "https://www.berkshirehathaway.com/letters/2008ltr.pdf"),
        ("Buffett, brev till aktieägarna 1987 (Mr Market)", "https://www.berkshirehathaway.com/letters/1987.html"),
        ("Buffett, brev till aktieägarna 1993 (röstningsmaskin, våg)", "https://www.berkshirehathaway.com/letters/1993.html"),
        ("Margin of safety (financial), Wikipedia", "https://en.wikipedia.org/wiki/Margin_of_safety_(financial)"),
    ],
)

# ---------------------------------------------------------------------------
# 3. THIS PROJECT'S FLAVOUR
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "03-this-project", "Det här projektets särdrag",
    "En persons version av metoden, med fyra vanor som gör den ovanlig, och ett verktyg byggt kring de vanorna snarare än kring en marknad.",
    6, False,
    f"""
<p>Värdeinvestering är en bred kyrka. Det här är en persons version av den, och den beskrevs av ägaren, med ägarens egna ord, innan något av den var byggt:</p>

<blockquote><p>"a tool that we can read reports and follow the stocks we have catched with the screener and then evaluated and make a tool that gives me the ability to follow the companies and then make an educated 'guess' and buy it when i think it is undervalued and we can make some cash"</p><cite>The owner, describing the project.</cite></blockquote>

<p>Läs det noga, för varje del av det blev en regel. <em>Läsa rapporter</em>: siffrorna kommer från bolagets egna rapporter, inte från en dataleverantörs sammanfattning. <em>Fångat med screenern</em>: ett grovt mekaniskt pass över tvåtusen namn hittar de få som är värda att läsa. <em>Följa bolagen</em>: en bevakningslista, kontrollerad varje natt. <em>En kvalificerad gissning</em>: ägarens egen bedömning av hur företaget kommer att växa, nedskriven som en bedömning och inte förklädd till en prognos. <em>Köpa det när jag tycker att det är undervärderat</em>: ägaren bestämmer. Inte verktyget.</p>

<h2>Fyra vanor som gör den här versionen särpräglad</h2>

<h3>1. Siffror kommer bara från bolagets egna rapporter</h3>
<p>Ett tal i det här systemet måste komma från den rapport som bolaget självt har publicerat: dess kvartals- eller årsbokslut, eller en myndighetsanmälan. Inte en nyhetsartikel om rapporten. Inte en dataleverantörs tillrättalagda version. Varje siffra bär med sig var den kommer ifrån, vilken period den avser och vilken sida den lästes på. En siffra utan det är ingen siffra; det är ett rykte med decimaler. Kapitel 6 visar vad detta kostar och varför det är värt det.</p>

<h3>2. Ägarens bedömning skrivs före det att marknadens tal har setts</h3>
<p>Metoden räknar ut vilken tillväxt det nuvarande priset förutsätter (kapitel 7). Innan det talet beräknas skriver ägaren ned vilken tillväxt han faktiskt tror på, med skäl, och filen tidsstämplas. Om marknadens tal sågs först är ägarens bedömning ogiltig för det bolaget i den omgången. Kapitel 8 förklarar varför regeln finns och vad den lånar från kliniska prövningar.</p>

<h3>3. Ett underkänt test är slutgiltigt och vidgas aldrig för att släppa igenom ett namn</h3>
<p>När ett bolag faller på ett test som gäller något annat än pris, för inte ett lägre pris tillbaka det. Bara ett namngivet nytt faktum kan göra det: en ny rapport, en ändrad prognos från bolaget, en vinstvarning. Och när en regel visar sig vara dåligt utformad tas den bort eller ersätts av ett daterat beslut som anger vad ändringen kostade. Den mjukas inte upp i det tysta för att ett visst namn nästan klarade sig. Kapitel 5 och 16.</p>

<h3>4. Varje nej spåras</h3>
<p>Det mesta som metoden tittar på ger den nej. Ett system som bara mäter vad det köpte kan inte avgöra om dess nej var rätt. Därför registreras varje nej med dagens pris och en rad som anger skälet, och mäts mot marknaden i efterhand. Kapitel 12.</p>

<h2>Vad det här inte är</h2>
<p>Det är inte ett handelssystem. Det förutsäger inte priser, det har ingen uppfattning om nästa vecka och det kommer aldrig att säga åt dig att köpa något. Det är ett sätt att läsa, besluta och registrera, för en person som har accepterat att det rätta svaret för det mesta är nej, och som vill kunna kontrollera i efterhand om nejet var rätt.</p>

{decision(
    "Verktyget mäter; ägaren bestämmer. Inget automatiserat steg får skriva en dom, föra in ett bolag i processen, tilldela en säkerhetsnivå eller sätta en köpkurs.",
    "Den som bestämmer ensam kan inte skilja en noggrann läsning från en motiverad. En maskin som också bestämde skulle ärva personens motiv och lägga till egna fel. Genom att låta beslutet ligga hos personen och mätningen hos maskinen går vart och ett att granska.",
    "Ägaren gör allt bedömande, för hand, varje gång. Ingenting går snabbare för det. Maskinen kan inte rädda ett dåligt beslut; den kan bara se till att beslutet skrevs ned innan utfallet var känt.",
)}
""",
    [("Ägarens beskrivning av projektet, ordagrant", "repo: the brief for this site"),
     ("Vad automatiserade steg får och inte får göra", "repo: reference/FRAMEWORK-EDITS.md rulings E92, E93, E97; README.md")],
)

# ---------------------------------------------------------------------------
# 4. THE SCREENER
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "04-the-screen", "Screenern: från tvåtusen till en handfull",
    "Ett grovt mekaniskt pass som tar bort det som går att anmärka på med offentliga siffror, så att en människas lästid går till det som återstår. Det hittar ingenting. Det tar bara bort.",
    10, False,
    f"""
<p>Tvåtusen namn, en läsare. Det enda sättet igenom är att ta bort de flesta utan att läsa dem, med frågor som är så grova att en maskin kan ställa dem till offentliga siffror. Det passet är <dfn>screenern</dfn>, och det viktigaste att förstå om den är vad den inte gör: den hittar inga bra bolag. Den tar bort bolag som faller på ett litet antal grova test, och lämnar det som blir kvar till en människa.</p>

{FIG["screen_filter"]()}

<h2>Var de två tusen kommer ifrån</h2>
<p>Listan är fast och daterad: medlemmarna i de stora amerikanska, europeiska och nordiska indexen för stora och medelstora bolag, skrivna till filer en angiven dag och förvarade under versionshantering. Listan hämtas aldrig live, så en körning vilken dag som helst kan upprepas senare på exakt samma namn.{N.ref("Universumfilerna under config/universe/ har sitt datum i filnamnet; indexmedlemskap hämtas aldrig vid körning (vss/universe.py). 2 011 instrument den 2026-09-10.")} Fonder, trusts, blankocheckbolag och omslag för utländska noteringar tas bort utifrån källlistans eget typfält, aldrig genom att gissa efter namnet.</p>
{N.flush()}

<h2>Stegen, i ordning, och varför varje fråga ställs</h2>

<h3>Steg 0: namn som redan ägs eller redan avgjorts</h3>
<p>En kort undantagslista med bolag som ägaren redan innehar eller redan har tagit ställning till. Det är meningslöst att screena ett namn vars svar redan är känt. En post på den listan som inte matchar något rapporteras som overksam, så att listan inte i det tysta kan ruttna.</p>

<h3>Filter 1: har kursen fallit tillräckligt, men inte för mycket?</h3>
<p>Metoden letar efter företag som marknaden tillfälligt har tappat intresset för. Den första frågan är därför om kursen ligger mellan 15 och 50 procent under sin högsta nivå det senaste året. Mindre än 15 och ingenting har hänt. Mer än 50 och arbetsantagandet är att något faktiskt är trasigt, vilket är en annan sorts bolag och ligger utanför ramen.{N.ref("Ramverket §3 spärr 1; bandet är implementerat en enda gång i vss/rules.py och återanvänds av både screenern och nattkörningen.")}</p>
{N.flush()}
<p>Två frågor till följer med den här. Har bolaget varit börsnoterat i minst fem år? En yngre notering har inte tillräckligt med redovisad historik att testa, och ett bolag som knoppats av från ett annat räknas som nytt.{N.ref("Beslut E52 och E52.1: en notering yngre än fem år avvisas på saknade data, och en avknoppning är en ny notering.")} Och är företaget ett som metoden över huvud taget kan bedöma? Kapitel 5 behandlar den gränsen.</p>
{N.flush()}

<h3>Filter 2: går det att anmärka på företaget utifrån tre grova siffror?</h3>
<p>För de som klarat sig, och bara för dem, hämtar verktyget bokslut och ställer tre frågor. Genererade företaget överskottskassa under de senaste tolv månaderna? Är dess skuld, efter avdrag för kassan, högst två och en halv gång dess årliga rörelseresultat före ränta, skatt, avskrivningar och nedskrivningar, en siffra som förkortas <dfn>EBITDA</dfn>? Och har omsättningen undvikit att falla, jämfört med samma kvartal ett år tidigare, två kvartal i rad?{N.ref("Tröskelvärdena finns i config/screener_filter2.yaml, var och en med hänvisning till sitt avsnitt i ramverket: positivt fritt kassaflöde (en förgrovning av spärr 3:s sex av åtta kvartal, eftersom kvartalsvis kassaflödeshistorik saknas för en stor del av listan); nettoskuld i förhållande till EBITDA högst 2,5×, beslut E44; två på varandra följande kvartalsvisa omsättningsminskningar jämfört med föregående år diskvalificerar, beslut E45.")}</p>
{N.flush()}
<p>Skuldtaket har sin egen historia. Den första versionen använde en generösare gräns, tre och en halv gång, med argumentet att ett grovt filter inte får förlora ett namn som den noggranna läsningen skulle behålla. Fyra dagar senare visade en testkörning att 72 namn klarade den generösa gränsen och sedan föll på metodens egna strängare test längre fram. Att släppa igenom dem gav inget annat än mer läsning. Taket skärptes genom ett daterat beslut som anger antalet.{N.ref("Besluten E2 (2026-08-22, 3,5×) och E44 (2026-08-26, 2,5×), med mätningen av 72 namn i beslutstexten.")}</p>
{N.flush()}

<h3>Rangordning: vilka som klarat sig läses först</h3>
<p>Det som återstår ordnas efter två siffror. Hur lönsamt är företaget i förhållande till allt det äger, mätt som rörelseresultat genom totala tillgångar. Och hur billigt är det i förhållande till vad hela företaget skulle kosta att köpa, mätt som rörelseresultat genom den kostnaden. Varje överlevare rangordnas på båda, de två rangplatserna adderas och listan sorteras. Inga vikter, ingen poäng, ingen tröskel.{N.ref("Beslut E6 enligt ändring i E43. En tidigare version använde ett lönsamhetsmått vars nämnare gick mot noll för företag som äger lite, så de tretton främsta placeringarna gick till de tretton namn som låg närmast den polen; det ersattes.")} Banker, försäkringsbolag och fastighetsbolag kan inte rangordnas på den första siffran och listas separat på enbart den andra, aldrig blandade med de övriga.</p>
{N.flush()}

<h3>Vad som kommer ut</h3>
<p>De tjugo främsta bevakas för kursrörelser. Tre till fem föreslås för läsning. Inget av dem bär ett värde, en köpkurs eller en säkerhetsnivå. Screenerns resultat är en läslista, och en människa läser den.</p>

<h2>Vad en screening inte kan se</h2>
<ul>
<li><strong>Varför kursen föll.</strong> Ett fall på 30 procent på grund av ett rykte och ett fall på 30 procent på grund av bedrägeri ser likadana ut för filter 1. Orsaken är det första läsaren måste ta reda på, och den är ämnet för nästa kapitel.</li>
<li><strong>Allt som leverantörens siffror får fel.</strong> Bokslutet kommer i det här skedet från en dataleverantör, inte från rapporterna. En felaktigt märkt rad passerar obemärkt. En sådan rad hittades bara därför att den inte stämde med någon inlämnad siffra för något av de fem bolag som kontrollerades för hand.{N.ref("Beslut E43: leverantörens rad för 'bruttovinst' gick inte att stämma av mot någon inlämnad rad för något av fem testnamn, och ersattes av rörelseresultat i rangordningen.")}</li>
<li><strong>Ett namn som den aldrig hämtade bokslut för.</strong> Bokslut hämtas bara för filter 1:s överlevare. Ett test som läser en branschetikett kan inte se ett bolag som aldrig kom så långt. Den tystnaden är ett faktum om hämtningen, inte om bolaget, och verktyget säger det.{N.ref("Beslut E96: 'The string limb is blind where the fetch has not reached.'")}</li>
<li><strong>Om ett bolag är bra.</strong> Inget i det här kapitlet är en bedömning. Det är en lista över sådant som inte kunde anmärkas på i ett grovt test.</li>
</ul>
{N.flush()}

<p>Ytterligare en ärlighetsförklaring. Screenern spelar upp tidigare datum igen med hjälp av dagens bokslut mot den dagens kurser, eftersom leverantören bara levererar det senaste bokslutet. En sådan uppspelning är därför inget belägg för vad screeningen skulle ha hittat den dagen, och varje uppspelningsrapport säger det i en banderoll överst.</p>

{fold("De exakta reglerna", '''
<p>Ramverket §3 (spärrarna 1 till 5) och screenerbesluten E2, E6, E43, E44, E45, E46, E48, E52, E93, E96, E97 i <code>reference/FRAMEWORK-EDITS.md</code>. Tröskelvärden: <code>config/screener_filter2.yaml</code>. Kod: <code>vss/screen.py</code>, <code>vss/filters.py</code>, <code>vss/universe.py</code>, <code>vss/ranking.py</code>. Två tekniska mått, en momentumindikator och ett glidande medelvärde, beräknas och skrivs ut men används aldrig som filter, eftersom ett sådant filter, oavsett riktning, vid ett verkligt köp i det förflutna hade förkastat en av de två relevanta dagarna.</p>
''')}
""",
    [("Screenerns utformning och beslut", "repo: reference/FRAMEWORK-EDITS.md E2, E6, E43, E44, E45, E52, E93, E96, E97; config/screener_filter2.yaml; vss/screen.py; vss/filters.py")],
)

# ---------------------------------------------------------------------------
# 5. WHY A NAME IS REFUSED
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "05-refusal", "Varför ett namn får nej, och varför det är det normala utfallet",
    "De flesta bolag som når läsaren skickas bort. Spärrarna är utformade för att säga nej, en underkänd spärr förblir underkänd, och att vägra bedöma ett företag du inte kan bedöma är ett riktigt svar.",
    9, False,
    f"""
<p>När ett namn når en människa har det klarat en grov screening. Det är hyfsat billigt, det tjänar pengar, det har inte uppenbart gått sönder. Frestelsen är att tro att den svåra delen är avklarad. Det är den inte. Det är under läsningen som de flesta namn får nej, och nej är det väntade resultatet, inte en besvikelse.</p>

<h2>Spärren som står för det mesta av nejen: varför föll kursen?</h2>
<p>Screeningen hittade bolag vars kurs föll. Läsarens första uppgift är att ange orsaken och lägga den i en av fyra lådor.</p>
<ul>
<li><strong>A: stämningen ändrades.</strong> Ingenting i företaget förändrades; berättelsen som folk berättar om det gjorde det.</li>
<li><strong>B: hela branschen såldes ut.</strong> Pengar lämnade en bransch och tog det här bolaget med sig.</li>
<li><strong>C: en engångskostnad med ett belopp på.</strong> Ett vite, en nedskrivning, en fabriksbrand. Det hände en gång och dess storlek är känd.</li>
<li><strong>D: något är faktiskt trasigt.</strong> En produkt som inte längre säljer, en kund som lämnade, en tillsynsmyndighet som för gott har ändrat reglerna.</li>
</ul>
<p>A, B och C klarar sig. D faller, och regeln är strängare än den ser ut: om läsaren inte med säkerhet kan säga vilken låda det är, så är det D.{N.ref("Ramverket §3 spärr 2: fyra klasser av bortkoppling; 'if you cannot classify confidently, it is D.' Ett verkligt namn föll ut på klass D den 2026-09-08.")} Att inte veta varför en kurs föll är inte neutralt. Det är det vanligaste sättet att köpa ett trasigt företag.</p>
{N.flush()}

{example('''
<p>BOLAG A:s kurs ligger 35 procent under fjolårets topp, så det klarade filter 1. Läsaren öppnar de fyra senaste rapporterna. Omsättningen är oförändrad. Fallet började veckan då bolagets största kund, en femtedel av dess försäljning, meddelade att den skulle tillverka produkten själv från nästa år. Det är en förlorad kund som inte kommer tillbaka: låda D. BOLAG A faller på spärr 2 och lämnar processen. Dess billighet var aldrig frågan.</p>
''')}

{FIG["name_fails_gate"]()}

<h2>De andra spärrarna</h2>
<p>Ett namn som klarar "varför"-spärren prövas sedan mot sitt bokslut för de senaste två åren: skulden inom en angiven multipel av resultatet, räntorna täckta minst fem gånger av rörelseresultatet, överskottskassa genererad under minst sex av de senaste åtta kvartalen, ingen revisorsanmärkning om bolagets fortsatta drift, inget byte av revisor, inga omräknade bokslut. Sedan behöver det en daterad händelse inom nittio dagar som kan få marknaden att titta igen: ett resultatdatum, ett produktbeslut, ett avgörande. "Så småningom inser marknaden" är ingen händelse.{N.ref("Ramverket §3 spärr 3 och 5. Spärr 4, en värderingsrabatt mot jämförbara bolag, registreras som DATA SAKNAS för varje namn eftersom de jämförelsesiffror den behöver aldrig har sammanställts; den är inte borttagen, och återkommer när de finns (beslut E99).")}</p>
{N.flush()}

<p>Sedan finns det sju <dfn>hårda diskvalificeringar</dfn>: sådant som ensamt avslutar läsningen, hur bra allt annat än ser ut. Omsättningen faller två kvartal i rad. Marginalerna krymper medan omsättningen är oförändrad. Två nedskärningar av bolagets egen prognos på ett år. Tre missade resultat på två år. Skuld över en angiven multipel eller nära att bryta mot ett låneavtal. Både vd:n och finanschefen lämnar inom ett år. Lager eller obetalda fakturor som hopar sig snabbare än försäljningen.{N.ref("Ramverket §4.2. 'Any one invalidates.'")}</p>
{N.flush()}

<h2>Varför en underkänd spärr är slutgiltig</h2>
{wrong('''
<p>BOLAG A föll på en förlorad kund vid kursen 60. Sex månader senare är kursen 40. Vid 40 är det väl värt en ny titt? Kursen har gjort halva jobbet.</p>
''')}
{right('''
<p>Kursen var aldrig problemet. BOLAG A föll på ett faktum om sin verksamhet, och vid 40 är det faktumet fortfarande sant. Ett namn som föll på något annat än pris parkeras som <dfn>WATCH-GATED</dfn>, och det enda som kan få tillbaka det är ett namngivet nytt faktum: en ny rapport, en ändrad prognos, en varning. En kursnivå kan inte öppna det på nytt, eftersom ett kurslarm skulle väcka det in i samma spärr som det redan är känt för att falla på.</p>
''', "Regeln, och varför")}
<p>Detta är inskrivet i metoden som ett beslut med ett nummer, och det är skälet till att verktyget håller två sorters väntelistor isär. Ett namn som bara är för dyrt väntar på ett pris. Ett namn som föll på en spärr väntar på ett faktum.{N.ref("Beslut E27 delar den gamla enskilda statusen 'watch' i WATCH-PRICED och WATCH-GATED; den utfasade stavningen vägras av koden med ett meddelande som pekar på beslutet.")}</p>
{N.flush()}

<p>Samma slutgiltighet gäller reglerna själva. När två led i en spärr visade sig inte mäta något användbart togs de bort, och beslutet som tog bort dem säger "not widened, not softened, removed". En regel gäller antingen, eller har den avvecklats genom ett daterat beslut. Det finns inget tredje tillstånd där den böjs för ett namn som nästan klarade sig.{N.ref("Beslut E30, 2026-08-25, som tog bort två led i spärr 3 vilka mätte volatiliteten i redovisade siffror i stället för företagets kvalitet, efter att inte ha ändrat något utlåtande för fem namn.")}</p>
{N.flush()}

<h2>Cirkeln: att vägra det du inte kan bedöma</h2>
<p>Vissa företag får nej före varje spärr, inte för att de är dåliga utan för att metoden inte ärligt kan köras på dem. Metoden kräver att ägaren skriver ned ett trovärdigt spann för hur företaget kommer att växa (kapitel 8). För vissa företag är det inte en bedömning som någon kan göra.</p>
<ul>
<li>Ett bolag vars intäkt är ett världspris det inte sätter själv, multiplicerat med en volym: ett gruvbolag, en oljeproducent, ett bulkrederi. Dess sämre fall är inte långsammare tillväxt utan ett halverat pris, vilket är ett annat företag och inte ett lägre tal i samma räkneexempel.{N.ref("Beslut E96, 2026-08-31: 'This is a limit of the METHOD, and it is not a judgement about the industry.' Sexton branschmönster; reglerade elbolag, avtalad produktion och halvledare är uttryckligen undantagna från regeln.")}</li>
<li>Ett läkemedelsutvecklingsbolag, vars tillväxt är en gissning om godkännanden som ägaren inte har något sätt att bedöma.{N.ref("Beslut E51.")}</li>
</ul>
{N.flush()}
<p>Buffetts uttryck för detta är <dfn>kompetenscirkeln</dfn>: "The size of that circle is not very important; knowing its boundaries, however, is vital."{N.ref("Buffett, brev till aktieägarna 1996.")} Vad det här projektet tillför är att gränsen skrivs ned som en regel och upprätthålls av screeningen, så att ett osannolikt billigt gruvbolag inte kan locka någon att låtsas att metoden är tillämplig. Ett sådant namn bevakas aldrig alls, inte ens på sin kurs, eftersom det inte finns någon nivå det skulle kunna nå som betydde något.{N.ref("Beslut E97: ett namn utanför cirkeln 'is NEVER WATCHED AT ALL, not even on its drawdown'.")}</p>
{N.flush()}

<p>Att vägra ett företag man inte kan bedöma är ingen kapitulation. Det är det enda svaret som inte kräver att man låtsas.</p>

{fold("De exakta reglerna", '''
<p>Ramverket §3 (spärrarna), §4.2 (hårda diskvalificeringar), §4.4 (övertygelsepoäng). Besluten E27 (de två väntelistorna), E30 (borttagning av två led), E51 och E96 (cirkeln), E97 (bevakas aldrig), E99 (spärr 4 som DATA SAKNAS). Kod: statuslistan i <code>vss/rules.py</code>, cirkellistorna under <code>config/</code>.</p>
''')}
""",
    [
        ("Buffett, brev till aktieägarna 1996 (kompetenscirkeln)", "https://www.berkshirehathaway.com/letters/1996.html"),
        ("Circle of competence, Wikipedia", "https://en.wikipedia.org/wiki/Circle_of_competence"),
        ("Spärrar, hårda diskvalificeringar och cirkelbesluten", "repo: reference/FRAMEWORK.md §3–§4; reference/FRAMEWORK-EDITS.md E27, E30, E51, E96, E97, E99"),
    ],
)

# ---------------------------------------------------------------------------
# 6. WHAT GETS READ
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "06-what-gets-read", "Vad som läses",
    "Bara bolagets egna rapporter. Varje siffra med sitt ursprung, sin period och sin sida. Ingenting sträcks, skalas eller räknas om till helår för att fylla ett hål. Ett konkret exempel på fel sorts tal och vad det hade kostat att tro på det.",
    8, False,
    f"""
<p>När ett namn har klarat spärrarna ändrar läsningen karaktär. Screeningen använde en leverantörs sammanfattning av bokslutet eftersom det är det enda som skalar till tvåtusen namn. Härifrån kommer varje siffra som kan påverka ett beslut från det dokument som bolaget självt har publicerat.</p>

<h2>Regeln, i en mening</h2>
<p>En siffra är tillåten om det går att peka på den: den här rapporten, den här perioden, den här sidan. Allt annat är hörsägen.</p>

<p>Det låter självklart och bryts ständigt. En dataleverantörs "omsättning" kan vara bolagets omsättning, eller omsättning där ett segment har omklassificerats, eller förra årets tal som leverantören inte har uppdaterat. En nyhetsartikels "vinsten steg med 12 procent" kan vara rörelseresultat, nettoresultat eller justerat resultat enligt bolagets egen definition. Inget av detta är lögner. De är bara inte siffran, och den som bygger en värdering på dem har byggt den på något hen inte kan kontrollera.</p>

<p>Därför hämtar verktygets läskod bara bolagsrapporter och myndighetsdokument, och vägrar följa länkar eller söka.{N.ref("Källmodulens egen beskrivning: 'Primary source ONLY: a company IR release or a regulatory filing. Never a news article about one. This module does not search, guess or follow links.'")} För amerikanska bolag läser den den strukturerade data som bolagen måste lämna in till tillsynsmyndigheten. För nordiska bolag läser den börsens eget flöde av offentliggöranden. För allt annat läser en människa PDF:en och skriver in siffran, med sidnumret bredvid.</p>
{N.flush()}

<h2>Varje siffra bär med sig tre saker</h2>
<ol>
<li><strong>Var den kommer ifrån.</strong> Dokumentet, och sidan eller taggen i det.</li>
<li><strong>Vilken period den avser.</strong> Ett kvartal, ett halvår, ett år, och vilket.</li>
<li><strong>Om en människa har kontrollerat den.</strong> En siffra kommer in som okontrollerad. Den blir kontrollerad först när ägaren har läst tillbaka den mot sidan som anges bredvid, och registret anger vilken sorts kontroll den klarade: avstämd mot tillsynsmyndighetens strukturerade data, avstämd över två separata dokument, eller tillbakaläst mot samma sida den kom från, vilket är den svagaste sorten och säger det.{N.ref("Beslut E40 och kontrollsorterna i vss/manual.py: taggad, över dokument, samma sida. Okontrollerad är inte samma tillstånd som frånvarande: 'UNVERIFIED is the state a figure is entered in, and it is what section 5 refuses on. It is NOT the same state as absent.'")}</li>
</ol>
{N.flush()}
<p>Värderingen vägrar köra på en okontrollerad siffra. Inte varnar: vägrar, och kommandot avslutas med ett fel. En siffra som ingen har läst tillbaka är en siffra som ingen har läst.</p>

<h2>Ingenting sträcks för att passa</h2>
<p>Värderingen arbetar med tolv månaders kassaflöde. Anta att bolaget har redovisat tre kvartal av det här året och du vill ha ett helår. Det frestande draget är att ta de nio månaderna och multiplicera med fyra tredjedelar. Metoden förbjuder det. En siffra av fel längd saknas; den är inte en siffra som justerats för att passa.{N.ref("Ramverket §5 basregel (besluten E19, E20): 'Nothing here is annualised and nothing is scaled — a figure of the wrong length is DATA MISSING, never a figure adjusted to fit.'")} Tolv månader sätts samman av fyra faktiska kvartal, alla fyra kontrollerade, och rapporten anger alla fyra bredvid siffran. En tolvmånaderssiffra som slutar på ett annat datum än de andra siffrorna i samma beräkning vägras också, med båda datumen utskrivna, eftersom två fönster inte är en kvot.</p>
{N.flush()}
<p>Samma stränghet gäller sådant som ser trivialt ut. Ett antal aktier måste anges av bolaget, inte härledas. En nolla är ett påstående om bolaget och behöver ett underlag: raden finns och visar noll, eller bolaget anger att posten är noll, eller hela rapporten har genomsökts och registret anger det. En siffra som räknats om från en valuta till en annan anger kursen och datumet, och ett byte av enhet är ingen kurs.{N.ref("Besluten E22 och följande (antalet aktier), E25 (en nolla är ett påstående), E98 (en kurs och ett datum; en enhet är ingen kurs).")}</p>
{N.flush()}

<h2>Fel sorts tal, och vad det hade kostat</h2>
{example('''
<p>BOLAG A är noterat i London. Dess aktier kvoteras i pence. Dess bokslut, och därmed ägarens uppskattning av dess värde, är i pund. Det första utkastet till verktygets översiktssida tog värdet i pund, kursen i pence och räknade ut hur långt ifrån varandra de låg. Svaret som skrevs ut var att kursen låg ungefär 12 700 procent från värdet.</p>
<p>Ingen hade köpt på det talet; det var absurt vid första anblick. Men samma fel, på ett namn där enheterna skilde sig med en faktor tio i stället för hundra, hade skrivit ut ett avstånd som bara såg överraskande ut. Lösningen var inte att räkna om. Den var att vägra: där de två valutorna inte har samma kod saknas avståndet och sömmen namnges.</p>
''', "Ett verkligt fel, med namnet borttaget")}
<p>Felet och regeln som ersatte det är inskrivna i sidgeneratorns egna kommentarer, så att nästa person som rör den koden möter talet före räkningen.{N.ref("Sidgeneratorns egen regel: 'NO ARITHMETIC CROSSES A UNIT SEAM ... A distance computed across it would read as roughly −12,700%, which is the shape of the defect this project has already met once.' Det första utkastet skrev ut +10 543 % på ett namn och +12 791 % i en provkörningstabell.")}</p>
{N.flush()}

<p>Ett andra exempel ur samma familj. En dataleverantörs kurshistorik för ett stort bolag växlade, under fyra veckor, mellan två skalor: en justerad för en aktiesplit och en som inte var det. Det beräknade fallet från årets topp var 52 procent. Det sanna talet var ungefär 4. En kontroll byggdes som behandlar ett hopp åt ena hållet följt av ett motsvarande hopp tillbaka som bevis för två skalor i samma kolumn, eftersom verkliga bolagshändelser inte vänder om, och som behandlar ett ensamt hopp som misstänkt om inte dagen omsattes i många multipler av normal volym, vilket verkliga omvärderingar gör och matningsfel inte gör.{N.ref("vss/series_sanity.py, beslut K4. Uppmätt: två verkliga stora endagsrörelser omsattes i ungefär 24× och 14× sin medianvolym; de korrumperade halveringarna omsattes i 0,7× till 2,6×.")}</p>
{N.flush()}

<p>Att tro på något av talen hade inte direkt kostat ett felaktigt köp. Det hade kostat något värre: ett system vars siffror ingen kunde lita på, och därmed ett system som ingen skulle använda den natt det gällde.</p>

{decision(
    "Siffror kommer bara från utgivarens egna dokument, bär ursprung, period och sida, och skalas, räknas om till helår eller lånas över fönster aldrig. Värderingen vägrar köra på en siffra som ingen har läst tillbaka.",
    "En siffra som inte går att peka på går inte att kontrollera, och en siffra som inte går att kontrollera blir förr eller senare fel den natt det gäller.",
    "Läsningen går långsamt. Vissa bolag går inte att värdera alls på månader eftersom en siffra de aldrig anger saknas. Verktyget säger vilken siffra, och väntar.",
)}
""",
    [("Beslut om primärkällor och ursprung", "repo: vss/source.py; reference/FRAMEWORK.md §5 basis rule; reference/FRAMEWORK-EDITS.md E19, E20, E22, E25, E40, E98; vss/overview.py (the unit seam); vss/series_sanity.py (ruling K4)")],
)

# ---------------------------------------------------------------------------
# 7. THE REVERSE DCF
# ---------------------------------------------------------------------------
# Static table for the explorable (same arithmetic as site.js)
def _value_at(g, fcf0=10.0, rate=0.095, term=0.025, years=10):
    v, cf = 0.0, fcf0
    for t in range(1, years + 1):
        cf *= (1 + g)
        v += cf / (1 + rate) ** t
    v += cf * (1 + term) / (rate - term) / (1 + rate) ** years
    return v


def _implied(price):
    lo, hi = -0.9, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if _value_at(mid) < price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


_rows = "".join(f'<tr><td class="num">{p}</td><td class="num">{_implied(p)*100:.1f}%</td></tr>' for p in (100, 130, 160, 200, 250, 320))

N = Notes()
chapter(
    "07-reverse-dcf", "Den omvända DCF:en",
    "Fråga inte vad ett företag är värt. Fråga vad priset förutsätter, och om du tror på det. Samma räkning, körd baklänges, och en annan sorts fråga kommer ut.",
    10, True,
    f"""
<p>Så här brukar man värdera ett företag. Du gissar hur snabbt dess kassaflöde kommer att växa. Du lägger ihop kassan du räknar med att det ger ifrån sig de kommande tio åren, diskonterad eftersom pengar senare är värda mindre än pengar nu, och lägger till något för åren därefter. Ut kommer ett tal. Du jämför talet med priset. Det förfarandet har ett namn, <dfn>diskonterat kassaflöde</dfn>, vanligen förkortat DCF.</p>

<p>Det har ett välkänt problem. Talet som kommer ut beror nästan helt på den tillväxt du gissade, och den tillväxt du gissade beror, om du är ärlig, på vad du redan ville att svaret skulle bli. "Vad är det värt?" är en fråga som bjuder in dig att lura dig själv, eftersom vilket svar som helst kan nås genom valet av gissning.</p>

<h2>Omvändningen</h2>
<p>Kör nu samma räkning baklänges. Utgå från den kurs marknaden anger i dag. Fråga: vilken tillväxttakt skulle företaget behöva under de kommande tio åren för att kursen ska vara precis rättvis? Räkningen är identisk; du löser bara ut en annan okänd. Ut kommer inte ett värde utan ett antagande: den tillväxt som marknaden för närvarande satsar på.</p>

<p>Det talet går att bedöma. "Kommer det här företaget att växa sitt kassaflöde med 14 procent om året i ett decennium?" är en fråga som den som har läst rapporterna kan ha en åsikt om. Den har en form. Du kan titta på vad bolaget har gjort de senaste tio åren, vad dess marknad gör, vad det skulle behöva sälja för att komma dit, och säga: det tror jag inte på. Eller: jag tror på mer än så. "Vad är det värt?" går inte att besvara. "Tror jag på det?" är en bedömning, och bedömningar är vad människor finns till för.</p>

{FIG["dcf_vs_reverse"]()}

<h2>En analogi</h2>
<p>En begagnad bil annonseras till ett pris. Du kan försöka räkna ut vad bilen är "värd", och du skulle upptäcka att svaret beror på hur många år av problemfri körning du antar. Eller så kan du ställa den andra frågan: till det här priset, hur många år av problemfri körning ber säljaren mig tro på? Om priset bara är rimligt om bilen går tolv år till utan reparation, och den har 200 000 kilometer på mätaren, då har du ditt svar, och du fick det utan att någonsin behöva veta vad bilen är "värd".</p>

<h2>Prova själv</h2>
<p>BOLAG A producerar 10 per aktie i överskottskassa om året. Fastställ räkningen så som det här projektet fastställer den: tio års tillväxt, därefter en slutlig tillväxt på 2,5 procent om året, allt diskonterat med 9,5 procent. Det enda fria talet är tillväxttakten. Så här ser det ut för olika priser och vad de förutsätter.</p>

<div class="tbl"><table>
<thead><tr><th class="num">Kurs per aktie</th><th class="num">Tillväxt som kursen förutsätter, per år i tio år</th></tr></thead>
<tbody>{_rows}</tbody>
</table></div>

<div class="explore js-only" id="rdcf-explore" hidden>
<label for="rdcf-price">Flytta kursen och se hur antagandet flyttar sig</label>
<input type="range" id="rdcf-price" min="80" max="400" step="5" value="160">
<output id="rdcf-price-out" for="rdcf-price"></output>
<output id="rdcf-out" aria-live="polite"></output>
<p class="hint">Samma räkning som i tabellen. Utan skript är tabellen siffran.</p>
</div>

<p>Läs tabellen från höger. Vid 100 förutsätter kursen att kassan knappt växer. Vid 250 förutsätter den en tillväxt som mycket få företag klarar i ett decennium. Metoden talar inte om vilket som stämmer. Den talar om vad du skulle behöva tro, och lämnar tillbaka trodden till dig.</p>

<h2>Hur det här projektet fastställer räkningen, och vad det medger</h2>
<p>Indata är tolvmånaders överskottskassa från rapporterna, bolagets nettoskuld och ett antal aktier som bolaget har angett. Horisonten är tio år, tillväxten därefter 2,5 procent. Diskonteringsräntan är 9,5 procent, och metoden är ovanligt öppen med vad det talet är: inte en uppskattning av vad marknaden kräver, utan ägarens eget avkastningskrav, satt till vad en indexfond förväntas ge på lång sikt plus två till tre punkter för risken att äga ett enda bolag. Den är densamma för alla bolag, vilket medvetet kräver lite mer av ett svenskt företag än av ett amerikanskt, och rapporten skriver ut skevheten i stället för att dölja den. Med beslutets egna ord "kommer räntan aldrig att verifieras mot något. Den är en preferens och säger det."{N.ref("Beslut E29. Motorn: vss/valuation.py. Varje köpkurs skrivs ut tillsammans med sitt värde vid en ränta en halv punkt lägre och en halv punkt högre, så att läsaren ser hur mycket talet lutar sig mot preferensen.")}</p>
{N.flush()}

<h2>Var idén kommer ifrån</h2>
<p>Att läsa den tillväxt som ligger inbäddad i ett pris, i stället för att prognostisera tillväxt för att hitta ett pris, utarbetades och populariserades av Alfred Rappaport och Michael Mauboussin i <em>Expectations Investing</em>, först utgiven 2001. Deras sammanfattning av metoden är två steg: läs priset, förutse sedan revideringen.{N.ref("Rappaport och Mauboussin, Expectations Investing (Harvard Business School Press 2001; reviderad upplaga Columbia 2021). Deras webbplats anger metoden som 'Read the price. Then anticipate the revision.'")} Aswath Damodaran lär ut samma omvändning under namnet implicit tillväxt. Det här projektet lånar omvändningen i sin helhet. Där det avviker är i vad som händer härnäst: Rappaport och Mauboussin jämför marknadens antagande med analytikerns; det här projektet kräver att analytikerns bedömning ligger i registret innan marknadens tal ens har beräknats. Det är nästa kapitel.</p>
{N.flush()}

{fold("Den exakta regeln", '''
<p>Ramverket §5 såsom ombyggt genom besluten E28 och E29: den omvända DCF:en är den enda motorn; två äldre metoder, jämförelse med tidigare multiplar och med jämförbara bolag, visas bredvid som sammanhang och vägs aldrig in i medelvärdet. Indata: rapporterat fritt kassaflöde för tolv månader, nettoskuld, ett angivet antal aktier. Horisont tio år, slutlig tillväxt 2,5 procent, avkastningskrav 9,5 procent, löst genom bisektion för den tillväxt som gör att eget kapital per aktie är lika med kursen. Kod: <code>vss/valuation.py</code>, funktionen <code>implied_growth</code>.</p>
''')}
""",
    [
        ("Rappaport och Mauboussin, Expectations Investing (bokens webbplats)", "https://www.expectationsinvesting.com/"),
        ("Den omvända DCF-motorn och avkastningskravet", "repo: vss/valuation.py; reference/FRAMEWORK-EDITS.md E28, E29"),
    ],
)

# ---------------------------------------------------------------------------
# 8. PRE-REGISTRATION
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "08-pre-registration", "Förregistrering: skriv ned tron innan du ser talet",
    "Räkna först ut vad kursen förutsätter, så hamnar det du skriver därefter misstänkt nära. Alla människor gör så. Därför skrivs tron först, tidsstämplas, och en bedömning som skrivits efter att talet setts är ogiltig.",
    10, True,
    f"""
<p>Förra kapitlet slutade med en fråga: tror jag på den tillväxt som kursen förutsätter? Här är problemet med att besvara den.</p>

{wrong('''
<p>Du räknar ut att BOLAG A:s kurs förutsätter 11 procents tillväxt om året. Nu sätter du dig ned för att skriva vad du tror att BOLAG A faktiskt kommer att växa med. Du har läst rapporterna. Du tänker noga efter. Du skriver ned 10 procent, med skäl.</p>
<p>Skälen är verkliga. Talet är det inte. Det är 11 med en liten rabatt för blygsamhet. Om kursen hade förutsatt 6 procent hade du skrivit 5 eller 7, med lika verkliga skäl. Talet du såg först blev mitten av det spann du trodde att du valde fritt.</p>
''', "Den naturliga ordningen, som är fel")}

<p>Det här är ingen karaktärsbrist. Det är ett av de mest pålitligt reproducerade fynden i forskningen om bedömning. I ett experiment 1974 fick människor se ett lyckohjul stanna på ett tal och sedan uppskatta hur stor andel av Afrikas länder som var medlemmar i FN. Hjulet var riggat att stanna på 10 eller på 65. De som såg 10 gissade ungefär 25 procent; de som såg 65 gissade ungefär 45. De visste att hjulet var slumpmässigt. Det hjälpte inte.{N.ref("Tversky och Kahneman, 'Judgment under Uncertainty: Heuristics and Biases', Science 185 (1974). Effekten kallas förankring.")} En senare studie lät fastighetsmäklare besöka ett hus och gav dem ett utropspris; mäklarnas värderingar följde det utropspris de hade visats, och de förnekade att de påverkats av det.{N.ref("Northcraft och Neale, 'Experts, Amateurs, and Real Estate', Organizational Behavior and Human Decision Processes 39 (1987).")}</p>
{N.flush()}
<p>Lägg till detta benägenheten att tolka belägg till förmån för den tro man redan har, dokumenterad i hundratals studier under namnet <dfn>bekräftelsebias</dfn>,{N.ref("Nickerson, 'Confirmation Bias: A Ubiquitous Phenomenon in Many Guises', Review of General Psychology 2 (1998).")} och bilden är tydlig. Den som har sett marknadens tal och sedan skriver sitt eget skriver inte sitt eget.</p>
{N.flush()}

<h2>Regeln</h2>
{right('''
<p>Innan den tillväxt som kursen implicerar beräknas skriver ägaren ned tre tillväxttakter, ett sämre fall, ett basfall och ett bättre fall, var och en med sina skäl, i en fil som tidsstämplas och förvaras under versionshantering. Först därefter löses det implicita talet ut. Om det implicita talet sågs först är bedömningen ogiltig för det bolaget i den omgången och kan inte användas.</p>
''', "Regeln, i kraft sedan 2026-08-25")}

{FIG["two_orderings"]()}

<p>Ordningen är hela mekanismen. Ingenting i räkningen ändras. Det som ändras är att ägarens tro finns som en daterad post före talet som kunde ha böjt den. När de två jämförs betyder jämförelsen något: antingen kräver marknaden mer tillväxt än ägaren tror på, eller mindre, och ägarens sida av jämförelsen tillverkades inte för att passa.</p>

<p>Registret upprätthålls av versionshanteringens historik, som inte kan redigeras utan att lämna spår. En ersatt bedömning raderas inte; den markeras som ersatt och lämnas kvar i filen, så att följden av vad ägaren trodde, och när, bevaras.{N.ref("Beslut E28: 'A view written after the implied growth has been seen is VOID and may not be used for that name in that cycle.' Beslut E95: en ersatt bedömning markeras, behålls och vägras av koden. Bedömningsfilerna registrerar vilka siffror som redan hade skrivits ut innan bedömningen skrevs, vilket är det som gör en sen bedömning möjlig att upptäcka.")}</p>
{N.flush()}

<h2>Var det här kommer ifrån: den kliniska prövningen</h2>
<p>Vetenskapen hade exakt det här problemet och löste det på samma sätt. En forskare som först samlar in data och sedan bestämmer vilken hypotes som ska testas kan alltid hitta något som ser signifikant ut, genom att i efterhand välja vilket utfall som redovisas. Metoderna har namn: <dfn>p-hacking</dfn>, att prova analyser tills en fungerar; <dfn>HARKing</dfn>, att ställa upp hypoteser efter att resultaten är kända; <dfn>byte av utfallsmått</dfn>, att i det tysta redovisa ett annat utfall än det prövningen utformades för att mäta.{N.ref("Simmons, Nelson och Simonsohn, 'False-Positive Psychology', Psychological Science 22 (2011); Kerr, 'HARKing', Personality and Social Psychology Review 2 (1998); Chan m.fl., JAMA 291 (2004), som fann att 62 procent av prövningarna hade minst ett primärt utfallsmått ändrat, tillagt eller utelämnat jämfört med protokollet.")}</p>
{N.flush()}
<p>Lösningen var <dfn>förregistrering</dfn>: skriv ned hypotesen och det utfall du ska mäta, i ett offentligt register, innan du samlar in data. Belägget för att det spelar roll är slående. En studie av stora, dyra hjärtsjukdomsprövningar som finansierats av en amerikansk myndighet fann att 57 procent av prövningarna som publicerades före 2000 redovisade en signifikant nytta. Efter 2000, när förhandsregistrering blev ett krav, föll det till 8 procent. Samma sorts prövning, samma sorts finansiering. Skillnaden var att svaret inte längre kunde väljas i efterhand.{N.ref("Kaplan och Irvin, 'Likelihood of Null Effects of Large NHLBI Clinical Trials Has Increased over Time', PLOS ONE 10 (2015): '17 of 30 studies (57%) published prior to 2000 showed a significant benefit' mot '2 among the 25 (8%) trials published after 2000'; 'Pre-registration in clinical trials.gov was strongly associated with the trend toward null findings.'")}</p>
{N.flush()}

<p>Det här projektet lånar mekanismen i sin helhet. Hypotesen är tillväxtbedömningen. Datan är ett enda tal, den tillväxt som kursen implicerar. Registret är en fil under versionshantering. Straffet för att titta först är att bedömningen inte räknas.</p>

<h2>Vad det kostar, rakt sagt</h2>
<p>Metodens uppskattning av värde vilar nu på ett tillväxtantagande som är en uttalad åsikt och aldrig kommer att verifieras. Beslutet som införde det säger så med de orden. Tidigare beslut hade höjt beviskravet för siffror som flyttar svaret med mindre än en procent; det här flyttar det med trettio. Projektets svar är att verifieringsinsatsen ska följa hur mycket ett tal betyder, inte hur lätt det är att kontrollera, och att det tal som betyder mest är det som bara kan skyddas genom ordning, eftersom det inte alls går att kontrollera.{N.ref("Ur ramverkets §5 enligt ändring i E28: 'Verification effort follows sensitivity, not availability.'")}</p>
{N.flush()}

{fold("Var det här kommer ifrån", '''
<ul>
<li>Förankring: Tversky och Kahneman, Science 185 (1974), lyckohjulsexperimentet. Northcraft och Neale (1987) om fastighetsmäklare.</li>
<li>Bekräftelsebias: Nickerson (1998); den ursprungliga demonstrationen är Wason (1960).</li>
<li>Förregistrering inom vetenskapen: Simmons, Nelson och Simonsohn (2011); Kerr (1998); Chan m.fl. (2004); Kaplan och Irvin (2015); Nosek m.fl., 'The preregistration revolution', PNAS 115 (2018).</li>
<li>Det här projektets regel: beslut E28 (2026-08-25) och E95 (ersatta bedömningar), <code>reference/growth-views/</code>.</li>
</ul>
<p>Där det här skiljer sig från sin förebild: en vetenskaplig förregistrering är offentlig och hypotesen testas mot många datapunkter. Här är registret privat, "datan" är ett enda tal, och straffet är att bedömningen blir ogiltig snarare än att en artikel refuseras. Mekanismen är densamma: tron måste finnas, daterad, före det som kunde böja den.</p>
''')}
""",
    [
        ("Tversky och Kahneman (1974), Judgment under Uncertainty, Science", "https://www.science.org/doi/10.1126/science.185.4157.1124"),
        ("Förankringseffekten (lyckohjulsexperimentet beskrivs), Wikipedia", "https://en.wikipedia.org/wiki/Anchoring_effect"),
        ("Northcraft och Neale (1987), Experts, Amateurs, and Real Estate", "https://www.sciencedirect.com/science/article/abs/pii/074959788790046X"),
        ("Nickerson (1998), Confirmation Bias", "https://journals.sagepub.com/doi/abs/10.1037/1089-2680.2.2.175"),
        ("Simmons, Nelson och Simonsohn (2011), False-Positive Psychology", "https://journals.sagepub.com/doi/10.1177/0956797611417632"),
        ("Kerr (1998), HARKing", "https://journals.sagepub.com/doi/10.1207/s15327957pspr0203_4"),
        ("Chan m.fl. (2004), Selective reporting of outcomes in randomized trials, JAMA", "https://jamanetwork.com/journals/jama/fullarticle/198809"),
        ("Kaplan och Irvin (2015), Likelihood of Null Effects of Large NHLBI Clinical Trials Has Increased over Time, PLOS ONE", "https://doi.org/10.1371/journal.pone.0132382"),
        ("Nosek m.fl. (2018), The preregistration revolution, PNAS", "https://www.pnas.org/doi/abs/10.1073/pnas.1708274114"),
        ("Förregistreringsregeln", "repo: reference/FRAMEWORK-EDITS.md E28, E95; reference/growth-views/"),
    ],
)

# ---------------------------------------------------------------------------
# 9. THE THREE OUTCOMES
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "09-three-outcomes", "De tre utfallen",
    "Varje test slutar i GODKÄND, UNDERKÄND eller DATA SAKNAS. Det tredje är ingen svagare version av det andra, och ett system som i det tysta registrerar 'kunde inte kontrollera' som 'underkänd' kommer att ljuga för dig åt båda hållen.",
    6, False,
    f"""
<p>De flesta checklistor har två utfall. En ruta är kryssad eller inte. Metoden har tre, och det tredje är det som gör de två andra pålitliga.</p>

{FIG["three_doors"]()}

<h2>Varför två inte räcker</h2>
{wrong('''
<p>Testet frågar om BOLAG A:s skuld ligger inom gränsen. Leverantören har ingen skuldsiffra för BOLAG A det här kvartalet. Testet går inte att köra. Så rutan lämnas okryssad, och okryssad betyder underkänd, och BOLAG A tas bort.</p>
<p>Senare, BOLAG B: samma test, samma saknade siffra. Men BOLAG B är ett namn som läsaren gillar, så den saknade siffran uppmärksammas, jagas, hittas i rapporten, och bolaget klarar sig.</p>
''', "Tvåutfallsversionen, som är fel två gånger")}
<p>Det första felet är att BOLAG A togs bort på grund av ett faktum om dataleverantören, inte ett faktum om BOLAG A. Det andra felet är värre: huruvida en saknad siffra räknas som underkänd beror nu på om någon brydde sig tillräckligt för att jaga den, vilket betyder att det beror på vad läsaren redan ville. Tvåutfallschecklistan har i det tysta blivit ett sätt att tvätta preferenser.</p>

{right('''
<p>Varje test slutar i exakt ett av tre tillstånd. GODKÄND: testet kördes och siffran klarade det. UNDERKÄND: testet kördes och siffran klarade det inte. DATA SAKNAS: testet kunde inte köras, eftersom siffran saknas, är gammal, har fel längd eller ännu inte har kontrollerats av en människa. Inget test får hoppas över i det tysta, och DATA SAKNAS räknas aldrig som UNDERKÄND.</p>
''', "Regeln")}

<p>Det här är den andra av de fem driftreglerna som hela metoden är skriven under, och den återkommer i varje lager av verktyget. Screenern räknar ett namn som förkastats för att en siffra sa så och ett namn som förkastats för att en siffra saknades i olika kolumner, och adderar dem aldrig.{N.ref("Ramverket §0 regel 2: 'Every screening criterion gets an explicit PASS / FAIL / DATA MISSING verdict. No criterion may be silently skipped.' I screenerns universumkod: 'DATA MISSING is a THIRD STATE ... counted in different columns and never added together.' Filterkonfigurationens policy för saknade data är att släppa igenom, vald så att luckor i leverantörens täckning inte ska utge sig för att vara kvalitetsbrister.")} Nattkörningen skiljer en dom om ett bolag från en blockering om datan: gamla kurser, ett olöst händelsedatum, ett saknat stopp. I verktygets grundmening: "gammal eller olöst data ger en blockering, aldrig en dom. Verktyget talar hellre om att det inte kan bedöma än att bedöma på dålig data."{N.ref("README, inledningen. Blockeringskoderna och domkoderna är separata listor i vss/rules.py.")}</p>
{N.flush()}

<h2>Det tredje utfallet är information</h2>
<p>DATA SAKNAS är inte frånvaro av resultat. Det är ett resultat, och det säger läsaren två saker: att det här testet inte säger något om bolaget, och att det finns en siffra att gå och hitta. Det är också, ärligt registrerat, en beskrivning av hur mycket av metoden som faktiskt körs. En av metodens fem spärrar, en jämförelse av värdering mot jämförbara bolag, har varit DATA SAKNAS för varje bolag som någonsin granskats, eftersom de jämförelsesiffror den behöver aldrig har sammanställts. Spärren togs inte bort för att få räkningen att se bättre ut. Den ligger kvar, markerad, tills siffrorna finns.{N.ref("Beslut E99: 'A criterion nobody can evaluate is not a criterion a company has failed.'")}</p>
{N.flush()}

<p>Ett närliggande tillstånd förtjänar att nämnas. En siffra som en människa har skrivit in men ännu inte läst tillbaka mot sin sida är UNVERIFIED, vilket inte är samma sak som saknad: den finns, har ett namn och vägras av värderingen tills den är kontrollerad. Och en siffra som har eftersökts i en fullständig rapport och verkligen inte finns där är NOT PRESENTED, vilket inte är samma sak som noll. Vart och ett är ett eget tillstånd eftersom ett hopslagande skulle låta en sorts okunnighet utge sig för en annan.{N.ref("Kontrolltillstånden i vss/manual.py och beslut E85.")}</p>
{N.flush()}

{decision(
    "Tre utfall för varje test, i varje lager, och det tredje slås aldrig ihop med det andra.",
    "En saknad siffra är ett faktum om datan. Att registrera den som ett faktum om bolaget för in ett fel vars riktning beror på vem som var uppmärksam.",
    "Rapporterna är fulla av DATA SAKNAS. Vissa namn står ovärderade i veckor i väntan på en enda siffra. Läsaren ser exakt hur litet metoden för tillfället kan säga, vilket är obehagligt och är poängen.",
)}
""",
    [("Tre-utfallsregeln i varje lager", "repo: reference/FRAMEWORK.md §0 rule 2; vss/rules.py (verdict and blocker codes); vss/universe.py; config/screener_filter2.yaml; reference/FRAMEWORK-EDITS.md E85, E99")],
)

# ---------------------------------------------------------------------------
# 10. THE FUNNEL
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "10-the-funnel", "Tratten: sex statusar",
    "Varje bolag som metoden har rört vid befinner sig i exakt ett av sex tillstånd. För varje: vad som händer där, vad verktyget gör, vad ägaren gör och vad som gör att ett namn faller ur.",
    9, False,
    f"""
<p>Ett bolag som metoden har lagt märke till befinner sig alltid i exakt ett tillstånd, och tillståndet står i ägarens bevakningslista. De sex tillstånden, med verktygets egna stavningar, är INTAKE, PIPELINE, WATCH-GATED, WATCH-PRICED, HELD och DROPPED.{N.ref("Statuslistan i vss/rules.py. En utfasad sjunde stavning, enbart WATCH, vägras av koden med ett meddelande som pekar på beslutet som delade den.")} Ordningen nedan är den ordning ett namn skulle färdas i om allt gick bra, vilket det nästan aldrig gör.</p>
{N.flush()}

{FIG["funnel"]()}

<div class="stage"><h3>INTAKE: läses, bevakas inte</h3><dl>
<dt>Vad som händer</dt><dd>Ett namn studeras. Dess rapporter läses, siffror förs in och kontrolleras, en tillväxtbedömning kan skrivas. Ingenting om det bevakas ännu.</dd>
<dt>Verktyget gör</dt><dd>Hämtar dess rapporter på begäran, lagrar dess siffror med ursprung, rapporterar vad som är verifierat och vad som saknas. Det bevakar inte kursen.</dd>
<dt>Ägaren gör</dt><dd>Läser. Avgör om namnet över huvud taget ska föras in i processen.</dd>
<dt>Faller ur när</dt><dd>Ägaren avgör att det inte är värt att föra in. Ingenting automatiskt händer här.</dd>
</dl></div>
<p>Det här tillståndet finns på grund av ett baklås som metoden skapade åt sig själv: tillväxtbedömningen måste skrivas innan värdet löses ut, men att föra in ett namn brukade stämpla datumet och frysa en spärr, så ett namn kunde inte studeras utan att man band sig vid det. INTAKE är "läses, bevakas inte", och bär ingen inträdesstämpel.{N.ref("Beslut E111, 2026-09-04, som löste det baklås som beslut E109 hade skapat. Koden vägrar en INTAKE-post som bär något av de fält som bara ett infört namn får ha.")}</p>
{N.flush()}

<div class="stage"><h3>PIPELINE: infört</h3><dl>
<dt>Vad som händer</dt><dd>Ägaren har fört in namnet. Inträdesdatumet och kursens toppunkt stämplas och fryses, så att spärren "hur långt har den fallit" bedöms per den dagen och inte driver iväg när kursen rör sig.</dd>
<dt>Verktyget gör</dt><dd>Bevakar bolagets egna offentliggöranden: periodiska rapporter, ändringar av dess prognos, vinstvarningar. Inget annat. Ledningsbyten, återköp, affärer och aktieägarmeddelanden sorteras bort, enligt ägarens test: skulle det här få mig att göra om värderingen?</dd>
<dt>Ägaren gör</dt><dd>Arbetar sig igenom spärrarna, de hårda diskvalificeringarna, läsningen, tillväxtbedömningen, värderingen.</dd>
<dt>Faller ur när</dt><dd>En spärr faller på något annat än pris (till WATCH-GATED), en hård diskvalificering eller ett klass D-skäl hittas (till DROPPED), eller företaget visar sig ligga utanför cirkeln (till DROPPED).</dd>
</dl></div>
<p>Eftersom inträdet fryser en spärr och den frysningen inte kan ångras genom att köra om något, är det schemalagda screeningjobbet förbjudet att föra in ett namn. Det får föreslå. Bara ägaren för in, för hand.{N.ref("Beslut E93: 'entering a PIPELINE name stamps dd_at_entry and peak_date and E12 freezes Gate 1 at that moment — and unlike a fair value, that is not undone by re-striking.' Flaggan som skulle tillåta det saknas i den schemalagda enheten och måste fortsätta saknas.")}</p>
{N.flush()}

<div class="stage"><h3>WATCH-GATED: väntar på ett faktum</h3><dl>
<dt>Vad som händer</dt><dd>Namnet föll på en spärr på något som inte var dess kurs. Det väntar.</dd>
<dt>Verktyget gör</dt><dd>Bevakar dess offentliggöranden, som för PIPELINE. Bevakar inte dess kurs, eftersom ingen kurs skulle ändra svaret.</dd>
<dt>Ägaren gör</dt><dd>Ingenting, tills ett namngivet nytt faktum kommer. Läser då om.</dd>
<dt>Faller ur när</dt><dd>Ägaren avgör att faktumet aldrig kommer (till DROPPED), eller ett nytt faktum öppnar spärren på nytt (tillbaka till PIPELINE).</dd>
</dl></div>

<div class="stage"><h3>WATCH-PRICED: väntar på en kurs</h3><dl>
<dt>Vad som händer</dt><dd>Läsningen är klar, värdet är värderat, det mesta ägaren vill betala är beräknat. Kursen ligger över det. Namnet väntar på kursen och ingenting annat.</dd>
<dt>Verktyget gör</dt><dd>Jämför varje natt den avslutade slutkursen med köplinjen och rapporterar avståndet. Pekar när kursen korsar den. Linjen är en beräknad köpkurs eller så finns ingen linje: en nivå som skrivits in för hand för ett namn som aldrig värderats är en påminnelse, och namnet går inte att köpa vid den.</dd>
<dt>Ägaren gör</dt><dd>Väntar. Värderar om vid bolagets nästa rapport.</dd>
<dt>Faller ur när</dt><dd>Kursen korsar linjen och ägaren köper (till HELD), eller en ny rapport ändrar läsningen (tillbaka till PIPELINE, eller till DROPPED).</dd>
</dl></div>

<div class="stage"><h3>HELD: ägt</h3><dl>
<dt>Vad som händer</dt><dd>Ägaren har köpt. Ett stopp, en kurs där positionen säljs oavsett, sattes före köpet och är registrerat.</dd>
<dt>Verktyget gör</dt><dd>Kontrollerar varje natt kursen mot stoppet och rapporterar ett brott som det första på sidan. Ett ägt namn utan stopp är en blockering, som rapporteras före allt annat.</dd>
<dt>Ägaren gör</dt><dd>Värderar om vid varje rapport. Säljer vid stoppet eller när skälet till köpet är borta.</dd>
<dt>Faller ur när</dt><dd>Ägaren säljer. Försäljningen registreras och mäts mot marknaden från sitt eget datum.</dd>
</dl></div>

<div class="stage"><h3>DROPPED: fått nej</h3><dl>
<dt>Vad som händer</dt><dd>Namnet har fått nej: en hård diskvalificering, ett klass D-skäl, utanför cirkeln eller ägarens bedömning.</dd>
<dt>Verktyget gör</dt><dd>Bevakar det inte alls. Registrerar nejet i skuggboken med dagens kurs och en rad med skäl (kapitel 12).</dd>
<dt>Ägaren gör</dt><dd>Ingenting. Läser skuggboken en gång om året.</dd>
<dt>Faller ur när</dt><dd>Det gör det inte. Ett avfört namn kan föras in igen vid INTAKE av ägaren, som ett nytt beslut, med ett nytt register.</dd>
</dl></div>

<h2>Det som är värt att lägga märke till</h2>
<p>Varje pil mellan rutorna är ägarens handling. Verktyget mäter var ett namn står, rapporterar det och pekar när något korsar en linje. Det flyttar aldrig ett namn. Om ägaren inte gör något flyttas ingenting. Det är ett designbeslut, och kapitel 13 förklarar varför.</p>

{fold("De exakta reglerna", '''
<p>Statusar: <code>vss/rules.py</code>. INTAKE: beslut E111. Stämplar vid inträde i PIPELINE och den frusna spärren: besluten E12 och E93. De två väntelistorna: beslut E27. Filtret för offentliggöranden: <code>vss/watch.py</code>. Den nattliga kursjämförelsen: <code>vss/runner.py</code>, <code>vss/rules.py</code>. Försäljningar: beslut B45, <code>vss/sales.py</code>. Nej: beslut E114, <code>vss/shadowbook.py</code>.</p>
''')}
""",
    [("Statusar och de beslut som styr flyttar mellan dem", "repo: vss/rules.py; vss/watch.py; reference/FRAMEWORK-EDITS.md E12, E27, E93, E111, E114")],
)

# ---------------------------------------------------------------------------
# 11. THE DECISION
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "11-the-decision", "Beslutet",
    "Aldrig 'ett köp'. Ett köp under kurs X, på villkor Y, med stopp Z, allt skrivet innan pengarna rör sig. Den rabatt som krävs växer med hur väl ägaren tror att han förstår företaget.",
    8, False,
    f"""
<p>Metodens fjärde driftregel lyder: en aktie är inte "ett köp". En aktie är ett köp under kurs X, på villkor Y, med stopp Z, och om du inte kan ange alla tre är arbetet inte klart.{N.ref("Ramverket §0 regel 4.")} Det här kapitlet handlar om de tre bokstäverna.</p>
{N.flush()}

{FIG["buy_price"]()}

<h2>X: det mesta ägaren vill betala</h2>
<p>Kapitel 8 gav ägarens tillväxtbedömning för basfallet. Kapitel 7:s räkning, körd framlänges med den bedömningen, ger ett värde per aktie. Det är ägarens uppskattning av vad BOLAG A är värt, och den är fel med ett belopp som ingen känner till. Därför är det inte köpkursen.</p>

<p>Köpkursen är värdet multiplicerat med en marginal, och marginalen beror på hur säker ägaren är. Metoden kallar säkerhetsnivåerna <dfn>nivåer</dfn>, och det finns tre. Ett namn på nivå 1, ett som ägaren förstår väl och som har en stark balansräkning och något varaktigt som driver det framåt, får en köpkurs på 85 procent av värdet. Ett namn på nivå 2, mindre säkert eller i en konjunkturkänslig bransch, får 75. Ett namn på nivå 3, där skälet till att äga det har fått beskrivas om på vägen, får 65.{N.ref("Beslut E90, 2026-08-30. Nivå är ingen känsla: den kommer från en övertygelsepoäng byggd av klarade spärrar, varningstecken och goda tecken, och nivå 1 kräver dessutom en balansräkning som en fästning och en långsiktig medvind. 'A score alone does not make a tier 1.'")} Marginalen finns för att ta upp fel i modellen och i indata, vilka i det här projektets egna granskningar vanligtvis har uppgått till fem till femton procent av värdet. Den finns inte för att ta upp att företaget går dåligt; det bär tillväxtbedömningen för det sämre fallet, och den skrivs ut bredvid köpkursen som information, inte inräknad i den.</p>
{N.flush()}

<p>Köpkursen skrivs ut med två följeslagare: samma kurs omräknad med diskonteringsräntan en halv punkt lägre och en halv punkt högre. Ägaren ser hur mycket talet lutar sig mot en ränta som, enligt metodens egen medgivande, är en preferens. Ett förslag om att verktyget skulle lägga in veto mot varje beslut som vänder inom det bandet avvisades, med ett skäl värt att citera: en sådan regel kunde bara någonsin ta bort en slutsats, aldrig skapa en, "och det här ramverkets diagnostiserade fel är att det inte kan säga ja."{N.ref("Beslut E29. 'Fragility is DISPLAYED, never ADJUDICATED.'")}</p>
{N.flush()}

<h2>Y: villkoren</h2>
<p>En kurs ensam räcker inte. Namnet måste fortfarande ligga inom den läsning som gav värdet: den daterade händelse som skulle få marknaden att titta igen måste fortfarande finnas i kalendern, den senaste rapporten får inte innehålla någon hård diskvalificering, och tillväxtbedömningen måste vara den som ligger i registret, inte en reviderad. Om bolaget rapporterar mellan värderingen och köpet görs värderingen om. En köpkurs fastställd på siffror som sedan har ändrats är ingen köpkurs; verktyget markerar ett värde som fastställts med en ersatt metod eller på siffror det inte längre kan återbygga som annullerat, inte som något gammalt.{N.ref("Besluten E39 och E87.")}</p>
{N.flush()}

<h2>Z: utgången, bestämd först</h2>
<p>Före varje köp skriver ägaren ett stopp: en kurs där positionen säljs, vad berättelsen än är just då. Det sätts när ägaren inte har något intresse i svaret. När aktierna väl är ägda kommer varje skäl att inte sälja att verka övertygande, vilket är precis därför talet skrevs tidigare. Verktyget vägrar behandla ett ägt namn som komplett utan ett, och rapporterar ett saknat stopp före allt annat på sidan.{N.ref("Ett ägt namn utan stopp är en blockering, som rapporteras före varje dom. Ramverket §6.4 nämner också tesstopp: sälj när skälet till att äga är borta, till exempel en andra nedskärning av bolagets egen prognos.")}</p>
{N.flush()}

<h2>Vad verktyget gör med allt detta</h2>
<p>Det beräknar X utifrån värdet och nivån, eftersom båda är ägarens indata och multiplikationen inte är en bedömning. Det vägrar ta emot ett X som skrivits in för hand; att göra det får körningen att misslyckas med en konflikt, eftersom en köpkurs som inte kom från ett värde och en nivå är ett tal utan ursprung.{N.ref("README: 'Writing an mbp: key by hand fails the run with a provenance conflict.' Marginalerna som gäller är 0,85, 0,75 och 0,65; en tidigare uppsättning, 0,80, 0,70 och 0,60, finns kvar i koden bara för tre siffror som fastställts under den och markeras som ersatta överallt där de skrivs ut.")} Varje natt rapporterar det avståndet från den avslutade kursen till X, och om Z har brutits. Det säger aldrig köp. Det säger: 4 procent över linjen, eller 2 procent under den, och resten är ägarens.</p>
{N.flush()}

<h2>Marginalen på vanlig svenska</h2>
<p>Hur stor rabatt du kräver bör bero på hur sannolikt det är att du har fel, och hur sannolikt det är att du har fel beror på hur väl du förstår det du köper. Ett företag du har följt i åratal, utan skuld och med medvind, kan du köpa till en måttlig rabatt mot din uppskattning, eftersom din uppskattning är värd något. Ett företag du bara halvt kan förklara bör du köpa först med en rejäl rabatt, eftersom din uppskattning mest är gissning och rabatten gör jobbet. Nivåerna sätter siffror på det, och siffrorna är desamma för varje bolag på samma nivå, så ägaren kan inte i det tysta ge en favorit en mindre marginal.</p>

{decision(
    "Ett beslut är tre nedskrivna tal, X, Y och Z, framtagna i den ordningen, före köpet. X beräknas utifrån ägarens värde och nivå och får inte skrivas in.",
    "Ett beslut som bara finns som en känsla av säkerhet går inte att kontrollera i efterhand. Tre tal med datum går.",
    "Ingenting köps snabbt. Mellan att ett bolag rapporterar och att ägaren får agera läses varje siffra om och värdet värderas om. Möjligheter som kräver snabbhet är inga möjligheter för den här metoden.",
)}
""",
    [("Regler för köpkursen, nivåerna och stoppet", "repo: reference/FRAMEWORK.md §0 rule 4, §4.4, §5.3, §6.4; reference/FRAMEWORK-EDITS.md E29, E39, E87, E90; vss/rules.py; vss/valuation.py")],
)

# ---------------------------------------------------------------------------
# 12. THE SHADOW BOOK
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "12-shadow-book", "Skuggboken",
    "Varje nej mäts mot marknaden i efterhand. Ett system som bara mäter det det köpte kan inte lära sig, och en process som bara säger nej, och aldrig betygsätter sina nej, kan inte visas ha fel.",
    7, False,
    f"""
<p>Nu bör metodens form vara tydlig: den säger för det mesta nej. Av de namn den har läst noga har den, i skrivande stund, sagt nej till vart och ett. Det väcker en obekväm fråga. Hur skulle någon veta om metoden helt enkelt var för sträng? En process som aldrig köper har aldrig ett dåligt köp att peka på. Den har inte heller ett bra. Dess meritlista är fläckfri och säger ingenting.</p>

<p>Ägarens beslut formulerade det så här: "Det här ramverket har utvärderat namn och sagt nej till alla, och ingenting i det mäter vad ett nej kostade eller sparade. En process som bara säger nej, och aldrig betygsätter sina nej, kan inte falsifieras."{N.ref("Beslut E114, 2026-09-08.")}</p>
{N.flush()}

<h2>Vad som registreras</h2>
<p><dfn>Skuggboken</dfn> är en tabell med en rad per nej. Varje rad registrerar sex fakta och inget annat: bolaget, datumet för domen, vad domen var och om den står sig, den avslutade slutkursen det datumet i bolagets egen valuta, värdet om något hade fastställts, och en rad som anger vad som avgjorde.</p>

{FIG["refusal_tracked"]()}

<p>Det som medvetet inte registreras betyder lika mycket. Ingen tes. Ingen förväntan om vad kursen kommer att göra. Inget mål. Med beslutets ord: "en rad som argumenterar är en rad som kommer att argumenteras om." Boken är ett register över beslut och kurser, inte ett register över åsikter om dem.</p>

<h2>Vad som mäts</h2>
<p>Från domdatumet och framåt ställs det avvisade namnets avkastning bredvid ett indexs avkastning under samma period, i samma valuta, och, det här är delen som krävde en ändring, samma sorts avkastning. En akties avkastning inkluderar dess utdelningar; ett index kan göra det eller inte. Regelns första version lät ett namn vars utdelningar leverantören inte registrerade jämföras som enbart kurs mot ett index som inkluderade utdelningar, vilket hade fått varje nej att se lite klokare ut än det var. Regeln ändrades en dag efter att den skrevs: där utdelningar inte går att fastställa är raden DATA SAKNAS i stället för en smickrande jämförelse. Ägarens skäl: "en skuggbok finns för att kunna säga att metoden inte fungerar, och en som systematiskt smickrar nejen kan inte göra det."{N.ref("Beslut E114 enligt ändring 2026-09-09. Boken lagrar den ojusterade slutkursen, ett faktum som aldrig ändras, och härleder totalavkastningen bredvid den vid läsning, och säger så.")}</p>
{N.flush()}

<h2>Fyra begränsningar, angivna av beslutet självt</h2>
<ol>
<li><strong>Den mäter vad som hände, aldrig om domen var rätt.</strong> Ett avvisat namn som steg kan ha stigit av precis de skäl som domen avstod från att satsa på. Boken kan inte se skillnaden, och låtsas inte om det.</li>
<li><strong>Den är ingen signal.</strong> Ingenting i den utlöser ett larm, för in ett namn eller matar en värdering. Ingen annan del av programmet läser den. Den läses en gång om året, med flit, eftersom en resultattavla man kikar på varje vecka är ett skäl att ändra en regel av fel anledning.</li>
<li><strong>Båda sidor är samma sorts avkastning</strong>, som ovan, annars saknas raden.</li>
<li><strong>En dom skriven på en helg flyttas</strong> till den sista vardagen före den, och raden säger det. Tillbakagången korsar helger och inget annat, eftersom en vardag utan kurs kan vara en helgdag eller ett datafel, och verktyget kan inte skilja dem åt.</li>
</ol>

<h2>Var det här kommer ifrån, och var det inte gör det</h2>
<p>Ingen inom finansvärlden har ett vedertaget namn på det här. De närmaste släktingarna är beslutsjournalen, en vana som rekommenderats av Daniel Kahneman och populariserats av skribenter om beslutsfattande: skriv ned vad du beslutade, varför och vad du förväntar dig, före utfallet; och skillnaden, gjord i pokerlitteraturen av Annie Duke och inom investering av Michael Mauboussin, mellan att bedöma ett beslut efter dess process och att bedöma det efter dess utfall, där det andra är ett misstag med ett namn, "resulting".{N.ref("Duke, Thinking in Bets (2018); Mauboussin, More Than You Know, som populariserar en matris för process mot utfall som ursprungligen kommer från Russo och Schoemaker. Rådet om beslutsjournal tillskrivs allmänt Kahneman; en primär intervju gick inte att hitta och åberopas inte.")} Den underliggande psykologin är efterklokhet: när ett utfall väl är känt tror människor att de förväntade sig det.{N.ref("Fischhoff, 'Hindsight ≠ Foresight', Journal of Experimental Psychology: Human Perception and Performance 1 (1975); Fischhoff och Beyth, 'I knew it would happen', Organizational Behavior and Human Performance 13 (1975).")}</p>
{N.flush()}
<p>Skuggboken avviker från idén om beslutsjournalen på ett sätt, med flit. En journal registrerar förväntan. Den här boken vägrar, eftersom en förväntan i registret är ett argument som väntar på att tas upp igen. Den registrerar bara vad som beslutades, när och till vilken kurs, och låter marknaden leverera resten ett år senare.</p>

{decision(
    "Varje nej registreras med sitt datum, sin kurs och sitt skäl på en rad, och mäts mot ett index i efterhand. Inget annat om det skrivs ned, ingenting i programmet läser boken, och den läses en gång om året.",
    "En metod som aldrig köper har en perfekt meritlista som inte bevisar något. Det enda sättet att ta reda på om nejen var rätt är att mäta dem, och det enda sättet att hindra mätningen från att böja reglerna är att sällan titta på den.",
    "Boken kan inte säga om en dom var rätt, bara vad kursen gjorde. Det är ett svagare påstående än det låter, och beslutet säger det i sin första begränsning.",
)}
""",
    [
        ("Hindsight bias, Wikipedia (Fischhoff 1975; Fischhoff och Beyth 1975)", "https://en.wikipedia.org/wiki/Hindsight_bias"),
        ("Skuggboksbeslutet och koden", "repo: reference/FRAMEWORK-EDITS.md E114 (2026-09-08, amended 2026-09-09); vss/shadowbook.py"),
    ],
)
