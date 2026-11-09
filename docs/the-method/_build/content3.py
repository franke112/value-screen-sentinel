"""The chapters added or assembled in the redesign of 2026-11-09.

* the prologue: the story of the tests, told first;
* the three machine chapters, ASSEMBLED from sections of the nine old ones
  (content2*.py keeps them as a library, so both languages keep their own
  prose and nothing is retyped);
* the bug museum.

One module for both languages: the structure is shared, the words are in T.
Every claim about the system is read from the repository; the tests are
told in words, never in a licensed vendor's figures.
"""

import re

# ---------------------------------------------------------------------------
# cutting the old chapters into sections


def _parts(body):
    return re.split(r"(?=<h2)", body)


def _inner(part):
    m = re.match(r"<h2[^>]*>.*?</h2>", part, re.S)
    return part[m.end():] if m else part


def _title(part):
    m = re.match(r"<h2[^>]*>(.*?)</h2>", part, re.S)
    return m.group(1) if m else ""


_NOTE = re.compile(
    r'<a class="noteref" href="#n(\d+)" id="r\1" aria-label="([^"]*?)\1">\1</a>'
    r'<span class="note" id="n\1" role="note"><span class="nn">\1</span>')


def renumber_notes(html):
    """Notes are numbered per old chapter; an assembled chapter needs one run."""
    count = [0]

    def sub(m):
        count[0] += 1
        n, label = count[0], m.group(2)
        return (f'<a class="noteref" href="#n{n}" id="r{n}" aria-label="{label}{n}">{n}</a>'
                f'<span class="note" id="n{n}" role="note"><span class="nn">{n}</span>')

    return _NOTE.sub(sub, html)


class Library:
    """The old chapters, addressed as (slug, section number)."""

    def __init__(self, lib):
        self.lib = lib

    def part(self, slug, k):
        return _parts(self.lib[slug]["body"])[k]

    def sec(self, slug, k):
        """A whole section, its own heading included."""
        return self.part(slug, k)

    def inner(self, slug, k):
        """A section without its heading."""
        return _inner(self.part(slug, k))

    def title(self, slug, k):
        return _title(self.part(slug, k))

    def sources(self, *slugs):
        seen, out = set(), []
        for slug in slugs:
            for item in self.lib[slug]["sources"]:
                if item not in seen:
                    seen.add(item)
                    out.append(item)
        return out


def _minutes(html):
    """Reading time of what is on the page: a fold is opened on demand."""
    visible = re.sub(r'<details class="fold">.*?</details>', " ", html, flags=re.S)
    words = len(re.sub(r"<[^>]+>", " ", visible).split())
    return max(3, round(words / 190))


# ---------------------------------------------------------------------------
# the words

T = {}

T["en"] = dict(
    # --- prologue ----------------------------------------------------------
    prologue_title="Twenty-six tests, and what was left",
    prologue_lede="This method was built from good books for three months and then tested for ten days. Most of it did not survive, and no edge was found. This is the story of that, told first, because everything after it is what remained.",
    prologue_body="""
<p>This book describes a slow way of buying shares, and the small program that keeps the person doing it honest. It was written twice. The first time it described a method. A few weeks later it had to describe what was left of one.</p>

<p>The method took three months to build. It came from the books anyone would start with: Benjamin Graham, Warren Buffett's letters, Joel Greenblatt, the academic papers on value and quality. Every rule had a reason and most had a citation. By late October 2026 there were about 150 written rulings. A company had to have fallen 15 to 50 percent from its high. The survivors were ranked so the best came first. Seven warning signs ended a reading on the spot. Every holding had a price at which it would be sold without argument. Every value had a cushion under it. Four quality tests were borrowed from the way Buffett describes a good business. It read well. It felt careful.</p>

<p>Reading well is not evidence. So between 29 October and 9 November the whole method was put on trial against history: the United States from 2016 to 2020 and the Nordic markets from 2010 to 2021. The companies that later went bankrupt or were bought were put back in, and every figure was allowed in only on the day it became public. Each test was written down before it ran: what is claimed, what is measured, where the bar is, and what happens to the rule if it fails. There were twenty-six attempts.</p>

<h2>What happened</h2>
<p>Most of the rules died.</p>
<ul>
<li><strong>The price stop.</strong> No level helped, and with trading costs every one of them cost money.</li>
<li><strong>The 15 to 50 percent band.</strong> The companies inside it did no better than the ones outside.</li>
<li><strong>The ranking.</strong> It did not put the better companies first. The list is now in a fixed random order, and says so.</li>
<li><strong>Three of the seven warning signs.</strong> Falling sales, a squeezed margin and swelling unpaid invoices did not separate the companies that did well from those that did not.</li>
<li><strong>The debt limits, the quality tests as a reason to drop a company, and the cushion as a binding buy line.</strong> None separated returns. The tests and the cushion are still printed, as information.</li>
</ul>
<p>What survived is short: the valuation itself, the rule that figures come only from the company's own reports, the belief about growth written down before the price is looked at, positive spare cash, at most six percent of the money in one company, and the reading a person does by hand.</p>

<p>And the trial did not find what every investor hopes a trial will find. <strong>No edge has been shown.</strong> In the Nordic markets the cheaper companies by the method's own value beat the dearer ones in most of the years it was developed on. A check on two later years, written down in advance and run once, did not confirm it. Against four well-known published value methods, this one won none of twelve comparisons.</p>

<h2>Why go on, then</h2>
<p>Three reasons, none of them hopeful in the usual way.</p>
<p><strong>The money is somewhere else.</strong> A broad index fund is the base of the owner's savings. This method is the smaller part: the part that is studied, not trusted. Nothing in this book asks you to trust it with more.</p>
<p><strong>What is left is the part no history can test.</strong> Reading a company's own reports. Saying in one sentence what it sells and why its customers come back. Writing down what you believe before the market tells you what to believe. These are tested the slow way: every company the method says no to is written down with its price that day and measured against the index for years ([[ch:12-shadow-book]]). The verdict on the hand-made parts arrives around 2030.</p>
<p><strong>The taking apart is the useful thing.</strong> A person with a method and no test has a belief. This is a record of what it costs to find out: the rule that every test is written down first, the faults found in our own data, and the day a value fell by a third because a rule was finally applied to a company that had already been bought.</p>

<h2>How to read it</h2>
<p>Part One is the method as it stands now. Each chapter states its claim in one sentence, tells the rule, and says what the test found where there was one. The tests have their own chapter in the middle. Part Two is the machine, and the faults it has caught in itself.</p>
<p>One real company runs through the whole book in a box marked <strong>CENTA</strong>. The owner bought it, valued it wrongly, valued it again and sold it, all within eight days in October 2026. It shows each rule doing its work, or arriving too late.</p>
""",
    # --- the three machine chapters ---------------------------------------
    reads_title="How the machine reads",
    reads_lede="A program that measures and remembers, with walls around what it may write. Where a figure lives, what must be declared before a value is printed, and why the rules are a document before they are code.",
    reads_fold_pieces="The seven kinds of piece, one by one",
    reads_h_rules="The rules are a document first",
    reads_fold_withdrawn="Rules that were withdrawn before the tests",
    watches_title="How it watches",
    watches_lede="Every night a clock fires, prices are held against decisions already made, each new report is read, and the phone hears only what changed. Silence has to mean healthy, so two observers watch the watcher.",
    watches_h_switch="The dead man's switch",
    watches_fold_name="The name, and where it comes from",
    watches_h_page="The page on the phone",
    watches_fold_tunnel="How the page reaches the phone, and what that costs",
    watches_fold_rules="The rules on what the page may say",
    limits_h_boundary="The boundary: one file served, every other path refused",
    # --- the bug museum ----------------------------------------------------
    museum_title="The bug museum",
    museum_lede="Six wrong numbers and one false sentence from this project's own records: what each looked like, how it was caught, and what changed. None was found by searching for it.",
    museum_intro="""
<p>Every project that computes with money produces wrong numbers. The honest question is not whether, but how they are caught, and what is left behind afterwards. This chapter is a museum. Each exhibit is a real fault from this project's records, kept because of what it taught.</p>
<p>One thing is common to all of them, and it is the reason the chapter exists. <strong>None was found by a search for it.</strong> A search finds what you already suspect. Each of these was caught because somebody read a whole table and one number was absurd on sight, or because two things that should have agreed did not.</p>
""",
    exhibits=[
        ("A share 12,791 percent above its line",
         "In a twenty-row table printed by a trial run in August 2026, one London company stood 12,791 percent above its buy line. Nobody was looking for it. The number was simply impossible.",
         "London shares are quoted in pence. The value had been worked out in pounds. The table divided one by the other.",
         "By eye, in a full table. A filter for \"names near their line\" would have hidden it, because it was nowhere near.",
         "Pence and pounds are now two different currencies to the program, and <em>no arithmetic crosses a unit seam</em>: where the two codes differ, no distance is printed at all, and the page says which seam it met. The first draft of the phone page made the same mistake before the rule was written: it showed 10,543 percent."),
        ("Coach, many times over",
         "In the history test, with bankrupt and bought companies put back in, one American company's five-year return came out at several thousand percent, and carried a whole portfolio with it.",
         "The handbag maker Coach renamed itself Tapestry in 2017 and changed its ticker from COH to TPR. The letters COH were later used for a different security. The price file under those letters began with one company and ended with another.",
         "An independent review read the list of the largest winners instead of the average, and one name was carrying the result.",
         "A guard: a price series that breaks level across a gap is not a return. Then the lesson's second half. The guard itself was tested as an attempt of its own, and it turned out to be removing real winners on single bad days. It was fixed, and the results it had touched were run again and logged. A fix made after seeing a result is not free: it is one more look, and it is counted."),
        ("The companies with no debt",
         "The Nordic screen listed a large part of its universe as free of debt, which made those companies look cheap.",
         "The data vendor's field for total debt was empty for them. The program read empty as zero. The borrowings were there all along, in the separate lines for short and long loans. Orkla, whose own annual report shows a net debt of about fourteen billion kronor, was being valued as a company that owed nothing.",
         "In November 2026 the screen's top names were read one by one against each company's own report. The first balance sheets opened showed loans the screen said did not exist.",
         "An empty total is rebuilt from its parts. The earlier history tests had run with the fault; they were not quietly re-run, and the fault is written into the log beside them. Empty is not zero: the third outcome of [[ch:09-three-outcomes]], learned again."),
        ("Seven messages, all false", None, None, None, None),   # the old chapter's own text
        ("The night the queue stopped",
         "On 2026-11-09 the nightly queue stopped with an error the first time it met a newly added company.",
         "A line written that day, for the weekly reminder about a sale decided but not yet carried out, used the name <code>since</code>. The run already used that name for something else: the date it looks back to. After the first held company with a sale pending, the run's window was no longer a date but a piece of text.",
         "It crashed. That is the good kind of failure: a run that stops with an error is reported as failed, and nothing wrong is sent to the phone.",
         "One variable renamed, and a comment on that line saying why. The exhibit is here for the contrast with the others: the faults that hurt are the ones that do not crash."),
        ("A sentence that outlived its rule",
         "Three days after the price stop was removed, the nightly report still said of one group of holdings that \"the stop is LIVE and is checked below\", and the phone page still said it had checked \"every stop against its close\". Nothing was checked. There was nothing to check.",
         "The rule was removed from the code that decides. The sentences lived in the code that describes, and nobody had a list of them.",
         "An audit of the manual against the code, line by line, on 2026-11-09. The manual had the same disease: it named a message the program no longer sent and listed four of ten scheduled jobs.",
         "The sentences are gone, and the page that lists every command is now generated from the code, with a test that fails when the two differ. A report that says it checked something it did not check is worse than a report that says nothing."),
        ("The value that fell by a third",
         "On 2026-10-27 the method's value for a company the owner already held went from 61.83 dollars a share to 28.60, and then to 40.19, in one day. The owner read the middle number as a joke or a lie.",
         "Not a fault in the code. A fault in the method, found by the method. The first value stood on one year's spare cash, and that year the company had been selling down its stock, which is cash that comes once. And the company buys other companies most years, which the first value neither charged nor checked. Two rules written that week fixed both: spare cash is the average of three years with the stock changes taken out, and a buyer of companies is valued on what its past purchases have actually earned.",
         "An outside review, asked for by the owner, said on the very first day that the cash figure was flattered. It was half accepted. A week later a second review went to the cash flow statement in the annual report itself, and three years of stock being sold down were there in print.",
         "The value now in force is 40.19. Most of the shares were sold over the next two days. And a habit: when a value moves a lot, it is shown step by step, never as a bare number. The CENTA boxes through this book are that waterfall, a chapter at a time."),
    ],
    labels=("What it looked like", "The cause", "How it was caught", "What changed"),
    museum_outro="""
<h2>What the museum teaches</h2>
<ul>
<li><strong>Read the whole table when you are hunting.</strong> A filter is for a known question. A wrong figure is by definition not where you expect it.</li>
<li><strong>Empty is not zero, and silence is not health.</strong> Three of the seven exhibits are a missing thing read as a harmless one.</li>
<li><strong>A fix made after seeing a result is itself a result.</strong> It is logged, and where it could change a conclusion it is tested.</li>
<li><strong>The loud failures are the cheap ones.</strong> A crash costs an evening. A plausible wrong number costs until somebody reads a full table.</li>
</ul>
""",
    museum_sources=[
        ("The habit of full reading, with the first five finds", "repo: CLAUDE.md, 'Bounded output, and when to ignore it'"),
        ("The reused ticker and the guard that was tested", "repo: reference/backtest/WHAT-WE-TESTED.md, attempts #2 and #15; tools/backtest/eodhd_reprice.py"),
        ("The empty debt total", "repo: tools/backtest/nordic.py, 'EMPTY DEBT TOTAL'"),
        ("The seven notifications", "repo: deploy/README.md; the failure notifier"),
        ("The run's window", "repo: vss/queue.py, the comment beside the exit reminder"),
        ("The sentences that outlived the stop", "repo: docs/CHANGELOG.md, 2026-11-09"),
        ("The three values of one day", "repo: reference/CENTA-STRIKE-2026-10-20.md, -2026-10-27.md, -2026-10-27-e142.md, -2026-10-27-check.md"),
    ],
)

T["sv"] = dict(
    prologue_title="Tjugosex tester, och vad som blev kvar",
    prologue_lede="Metoden byggdes ur bra böcker under tre månader och testades sedan i tio dagar. Det mesta höll inte, och ingen fördel hittades. Det här är berättelsen om det, och den kommer först, för allt som följer är det som blev kvar.",
    prologue_body="""
<p>Den här boken beskriver ett långsamt sätt att köpa aktier, och det lilla programmet som håller den som gör det ärlig. Den skrevs två gånger. Första gången beskrev den en metod. Några veckor senare fick den beskriva vad som fanns kvar av en.</p>

<p>Metoden tog tre månader att bygga. Den kom ur böckerna vem som helst skulle börja med: Benjamin Graham, Warren Buffetts brev, Joel Greenblatt, forskningen om värde och kvalitet. Varje regel hade ett skäl och de flesta en källa. I slutet av oktober 2026 fanns omkring 150 nedskrivna beslut. Ett bolag skulle ha fallit 15 till 50 procent från sin topp. De som klarade sig rangordnades så att de bästa kom först. Sju varningstecken avslutade en läsning på stället. Varje innehav hade en kurs där det skulle säljas utan diskussion. Varje värde hade en kudde under sig. Fyra kvalitetstest var lånade från hur Buffett beskriver ett bra företag. Det lät bra. Det kändes noggrant.</p>

<p>Att något låter bra är inget belägg. Så mellan den 29 oktober och den 9 november ställdes hela metoden inför historien: USA 2016 till 2020 och Norden 2010 till 2021. Bolagen som senare gick i konkurs eller köptes upp lades tillbaka, och varje siffra fick komma in först den dag den blev offentlig. Varje test skrevs ned innan det kördes: vad som påstås, vad som mäts, var ribban ligger och vad som händer med regeln om den faller. Det blev tjugosex försök.</p>

<h2>Vad som hände</h2>
<p>De flesta reglerna dog.</p>
<ul>
<li><strong>Kursstoppet.</strong> Ingen nivå hjälpte, och med handelskostnader kostade varenda en pengar.</li>
<li><strong>Bandet på 15 till 50 procent.</strong> Bolagen inom det gick inte bättre än de utanför.</li>
<li><strong>Rangordningen.</strong> Den satte inte de bättre bolagen först. Listan står nu i en fast slumpordning, och säger det.</li>
<li><strong>Tre av de sju varningstecknen.</strong> Fallande försäljning, pressad marginal och svällande obetalda fakturor skilde inte bolagen som gick bra från dem som inte gjorde det.</li>
<li><strong>Skuldgränserna, kvalitetstesten som skäl att stryka ett bolag, och kudden som bindande köplinje.</strong> Ingen skilde avkastningen åt. Testen och kudden skrivs fortfarande ut, som information.</li>
</ul>
<p>Det som överlevde är kort: själva värderingen, regeln att siffror bara kommer ur bolagets egna rapporter, tron om tillväxten nedskriven innan man tittar på kursen, positivt fritt kassaflöde, högst sex procent av pengarna i ett bolag, och läsningen som en människa gör för hand.</p>

<p>Och prövningen hittade inte det varje investerare hoppas att en prövning ska hitta. <strong>Ingen fördel har visats.</strong> I Norden gick de billigare bolagen enligt metodens eget värde bättre än de dyrare under de flesta år metoden utvecklades på. En kontroll på två senare år, nedskriven i förväg och körd en gång, bekräftade det inte. Mot fyra välkända publicerade värdemetoder vann den här ingen av tolv jämförelser.</p>

<h2>Varför fortsätta, då</h2>
<p>Tre skäl, inget av dem hoppfullt på det vanliga sättet.</p>
<p><strong>Pengarna ligger någon annanstans.</strong> En bred indexfond är grunden i ägarens sparande. Den här metoden är den mindre delen: den som studeras, inte den man litar på. Inget i boken ber dig lita på den med mer.</p>
<p><strong>Det som är kvar är den del ingen historia kan pröva.</strong> Att läsa bolagets egna rapporter. Att i en mening säga vad det säljer och varför kunderna kommer tillbaka. Att skriva ned vad du tror innan marknaden talar om för dig vad du ska tro. De prövas den långsamma vägen: varje bolag metoden säger nej till skrivs ned med kursen den dagen och mäts mot index i åratal ([[ch:12-shadow-book]]). Domen över de handgjorda delarna kommer kring 2030.</p>
<p><strong>Det nyttiga är isärtagningen.</strong> Den som har en metod men inget test har en tro. Det här är ett protokoll över vad det kostar att ta reda på: regeln att varje test skrivs ned först, felen vi hittade i vår egen data, och dagen då ett värde föll med en tredjedel för att en regel till slut tillämpades på ett bolag som redan var köpt.</p>

<h2>Hur boken ska läsas</h2>
<p>Del ett är metoden som den ser ut nu. Varje kapitel säger sitt påstående i en mening, berättar regeln och säger vad testet fann där det fanns ett. Testerna har ett eget kapitel i mitten. Del två är maskinen, och felen den har hittat hos sig själv.</p>
<p>Ett verkligt bolag går genom hela boken i en ruta märkt <strong>CENTA</strong>. Ägaren köpte det, värderade det fel, värderade det igen och sålde det, allt inom åtta dagar i oktober 2026. Det visar varje regel göra sitt jobb, eller komma för sent.</p>
""",
    reads_title="Hur maskinen läser",
    reads_lede="Ett program som mäter och minns, med väggar kring vad det får skriva. Var en siffra bor, vad som måste deklareras innan ett värde skrivs ut, och varför reglerna är ett dokument innan de är kod.",
    reads_fold_pieces="De sju sorternas delar, en i taget",
    reads_h_rules="Reglerna är ett dokument först",
    reads_fold_withdrawn="Regler som drogs tillbaka före testerna",
    watches_title="Hur den vakar",
    watches_lede="Varje natt slår en klocka, kurserna hålls mot beslut som redan är fattade, varje ny rapport läses, och telefonen får bara höra det som har ändrats. Tystnad måste betyda att allt är friskt, så två observatörer vakar över vakten.",
    watches_h_switch="Dödmansgreppet",
    watches_fold_name="Namnet, och var det kommer ifrån",
    watches_h_page="Sidan i telefonen",
    watches_fold_tunnel="Hur sidan når telefonen, och vad det kostar",
    watches_fold_rules="Reglerna för vad sidan får säga",
    limits_h_boundary="Gränsen: en fil lämnas ut, varje annan sökväg nekas",
    museum_title="Buggmuseet",
    museum_lede="Sex felaktiga tal och en falsk mening ur projektets egna protokoll: hur vart och ett såg ut, hur det upptäcktes och vad som ändrades. Inget hittades genom att någon letade efter det.",
    museum_intro="""
<p>Varje projekt som räknar med pengar producerar felaktiga tal. Den ärliga frågan är inte om, utan hur de upptäcks och vad som lämnas kvar efteråt. Det här kapitlet är ett museum. Varje föremål är ett verkligt fel ur projektets protokoll, sparat för vad det lärde.</p>
<p>En sak har de gemensamt, och den är skälet till att kapitlet finns. <strong>Inget hittades genom en sökning efter det.</strong> En sökning hittar det du redan misstänker. Vart och ett av de här upptäcktes för att någon läste en hel tabell och ett tal var orimligt vid första anblick, eller för att två saker som borde ha stämt överens inte gjorde det.</p>
""",
    exhibits=[
        ("En aktie 12 791 procent över sin linje",
         "I en tabell på tjugo rader från en provkörning i augusti 2026 stod ett Londonbolag 12 791 procent över sin köplinje. Ingen letade efter det. Talet var helt enkelt omöjligt.",
         "Londonaktier noteras i pence. Värdet hade räknats fram i pund. Tabellen delade det ena med det andra.",
         "Med blotta ögat, i en hel tabell. Ett filter för \"namn nära sin linje\" hade gömt det, för det var inte i närheten.",
         "Pence och pund är nu två olika valutor för programmet, och <em>ingen räkning korsar en enhetsgräns</em>: där de två koderna skiljer sig skrivs inget avstånd ut alls, och sidan säger vilken gräns den mötte. Första utkastet till telefonsidan gjorde samma misstag innan regeln var skriven: den visade 10 543 procent."),
        ("Coach, många gånger om",
         "I historietestet, med konkursade och uppköpta bolag tillbakalagda, blev ett amerikanskt bolags avkastning på fem år flera tusen procent, och bar en hel portfölj med sig.",
         "Väsktillverkaren Coach bytte namn till Tapestry 2017 och ticker från COH till TPR. Bokstäverna COH användes senare för ett annat värdepapper. Kursfilen under de bokstäverna började med ett bolag och slutade med ett annat.",
         "En oberoende granskning läste listan över de största vinnarna i stället för genomsnittet, och ett enda namn bar resultatet.",
         "Ett skydd: en kursserie som byter nivå över ett glapp är ingen avkastning. Sedan lärdomens andra halva. Skyddet testades som ett eget försök, och visade sig plocka bort verkliga vinnare på enstaka dåliga dagar. Det rättades, och resultaten det hade rört kördes om och loggades. En rättning som görs efter att man sett ett resultat är inte gratis: den är en titt till, och den räknas."),
        ("Bolagen utan skulder",
         "Den nordiska screeningen listade en stor del av sitt urval som skuldfritt, vilket fick de bolagen att se billiga ut.",
         "Dataleverantörens fält för total skuld var tomt för dem. Programmet läste tomt som noll. Lånen fanns där hela tiden, på de separata raderna för korta och långa lån. Orkla, vars egen årsredovisning visar en nettoskuld på omkring fjorton miljarder kronor, värderades som ett bolag som inte var skyldigt någonting.",
         "I november 2026 lästes screeningens toppnamn ett i taget mot varje bolags egen rapport. De första balansräkningarna som öppnades visade lån som screeningen sade inte fanns.",
         "En tom summa byggs upp ur sina delar. De tidigare historietesterna hade körts med felet; de kördes inte om i tysthet, och felet står inskrivet i loggen bredvid dem. Tomt är inte noll: det tredje utfallet i [[ch:09-three-outcomes]], lärt en gång till."),
        ("Sju meddelanden, alla falska", None, None, None, None),
        ("Natten då kön stannade",
         "Den 9 november 2026 stannade den nattliga kön med ett fel första gången den mötte ett nytillagt bolag.",
         "En rad som skrevs den dagen, för den veckovisa påminnelsen om en försäljning som är beslutad men inte utförd, använde namnet <code>since</code>. Körningen använde redan det namnet till något annat: datumet den tittar tillbaka till. Efter det första ägda bolaget med en väntande försäljning var körningens fönster inte längre ett datum utan en textbit.",
         "Den kraschade. Det är den goda sortens fel: en körning som stannar med ett fel rapporteras som misslyckad, och inget felaktigt skickas till telefonen.",
         "En variabel fick nytt namn, och en kommentar på den raden säger varför. Föremålet är här för kontrasten mot de andra: felen som gör ont är de som inte kraschar."),
        ("En mening som överlevde sin regel",
         "Tre dagar efter att kursstoppet togs bort sade nattrapporten fortfarande om en grupp innehav att \"stoppet är LIVE och kontrolleras nedan\", och telefonsidan sade fortfarande att den hade kontrollerat \"varje stopp mot sin stängningskurs\". Ingenting kontrollerades. Det fanns inget att kontrollera.",
         "Regeln togs bort ur koden som bestämmer. Meningarna bodde i koden som beskriver, och ingen hade en lista över dem.",
         "En granskning av manualen mot koden, rad för rad, den 9 november 2026. Manualen hade samma sjukdom: den nämnde ett meddelande programmet inte längre skickade och listade fyra av tio schemalagda jobb.",
         "Meningarna är borta, och sidan som listar varje kommando genereras nu ur koden, med ett test som faller när de två skiljer sig. En rapport som säger att den har kontrollerat något den inte har kontrollerat är värre än en rapport som inte säger något."),
        ("Värdet som föll med en tredjedel",
         "Den 27 oktober 2026 gick metodens värde för ett bolag ägaren redan ägde från 61,83 dollar per aktie till 28,60, och sedan till 40,19, på en dag. Ägaren läste det mellersta talet som ett skämt eller en lögn.",
         "Inget fel i koden. Ett fel i metoden, hittat av metoden. Det första värdet stod på ett enda års fria kassaflöde, och det året hade bolaget sålt ned sitt lager, vilket är pengar som kommer en gång. Och bolaget köper andra bolag de flesta år, vilket det första värdet varken belastade eller kontrollerade. Två regler skrivna den veckan rättade båda: det fria kassaflödet är snittet av tre år med lagerförändringarna borttagna, och en uppköpare värderas på vad dess tidigare köp faktiskt har tjänat.",
         "En utomstående granskning, som ägaren bad om, sade redan första dagen att kassaflödet var smickrat. Det godtogs till hälften. En vecka senare gick en andra granskning till kassaflödesanalysen i själva årsredovisningen, och där stod tre år av lagerminskning i tryck.",
         "Värdet som gäller nu är 40,19. De flesta aktierna såldes de två följande dagarna. Och en vana: när ett värde rör sig mycket visas det steg för steg, aldrig som ett naket tal. CENTA-rutorna genom boken är det vattenfallet, ett kapitel i taget."),
    ],
    labels=("Hur det såg ut", "Orsaken", "Hur det upptäcktes", "Vad som ändrades"),
    museum_outro="""
<h2>Vad museet lär</h2>
<ul>
<li><strong>Läs hela tabellen när du jagar.</strong> Ett filter är till för en känd fråga. Ett felaktigt tal finns per definition inte där du väntar dig det.</li>
<li><strong>Tomt är inte noll, och tystnad är inte hälsa.</strong> Tre av de sju föremålen är något som saknas, läst som något ofarligt.</li>
<li><strong>En rättning som görs efter att man sett ett resultat är själv ett resultat.</strong> Den loggas, och där den kan ändra en slutsats testas den.</li>
<li><strong>De högljudda felen är de billiga.</strong> En krasch kostar en kväll. Ett rimligt felaktigt tal kostar tills någon läser en hel tabell.</li>
</ul>
""",
    museum_sources=[
        ("Vanan att läsa allt, med de fem första fynden", "repo: CLAUDE.md, 'Bounded output, and when to ignore it'"),
        ("Den återanvända tickern och skyddet som testades", "repo: reference/backtest/WHAT-WE-TESTED.md, försök #2 och #15; tools/backtest/eodhd_reprice.py"),
        ("Den tomma skuldsumman", "repo: tools/backtest/nordic.py, 'EMPTY DEBT TOTAL'"),
        ("De sju notiserna", "repo: deploy/README.md; felnotifieraren"),
        ("Körningens fönster", "repo: vss/queue.py, kommentaren vid exit-påminnelsen"),
        ("Meningarna som överlevde stoppet", "repo: docs/CHANGELOG.md, 2026-11-09"),
        ("En dags tre värden", "repo: reference/CENTA-STRIKE-2026-10-20.md, -2026-10-27.md, -2026-10-27-e142.md, -2026-10-27-check.md"),
    ],
)


# ---------------------------------------------------------------------------
# assembling


def _exhibit(n, title, rows, labels, body_html=None):
    head = f'<h2><span class="exno">{n}</span> {title}</h2>'
    if body_html is not None:
        return f'<section class="exhibit">{head}{body_html}</section>'
    dl = "".join(f"<dt>{lab}</dt><dd>{txt}</dd>" for lab, txt in zip(labels, rows))
    return f'<section class="exhibit">{head}<dl class="exhibit-dl">{dl}</dl></section>'


def register(lang, lib, H, figures):
    """Add the new chapters to ``lib`` (slug -> chapter) for one language.

    ``H`` is that language's helper module (fold, ...); ``figures`` its
    interactive figures (figures.py), called with the language.
    """
    t, L = T[lang], Library(lib)

    def chapter(slug, title, lede, body, sources):
        body = renumber_notes(body)
        lib[slug] = dict(slug=slug, title=title, lede=lede, minutes=_minutes(body),
                         short=False, body=body, sources=sources)

    # -- prologue ----------------------------------------------------------
    chapter("prologue", t["prologue_title"], t["prologue_lede"], t["prologue_body"],
            lib["tested"]["sources"])

    # -- how the machine reads: old 13, 14, 15, 16 ---------------------------
    body = "".join([
        L.sec("13-why-a-machine", 0),
        L.sec("13-why-a-machine", 1),
        L.sec("14-the-pieces", 2),
        H.fold(t["reads_fold_pieces"], L.inner("14-the-pieces", 1)),
        L.sec("15-the-record", 1),
        L.sec("15-the-record", 2),
        L.sec("15-the-record", 3),
        L.sec("15-the-record", 4),
        f'<h2>{t["reads_h_rules"]}</h2>',
        L.inner("16-the-rules-file", 0),
        L.sec("16-the-rules-file", 1),
        L.sec("16-the-rules-file", 2),
        L.sec("16-the-rules-file", 3),
        H.fold(t["reads_fold_withdrawn"], L.inner("16-the-rules-file", 4)),
    ])
    chapter("machine-reads", t["reads_title"], t["reads_lede"], body,
            L.sources("13-why-a-machine", "14-the-pieces", "15-the-record", "16-the-rules-file"))

    # -- how it watches: old 17, 18, 19, 21 ---------------------------------
    defect = L.inner("18-dead-mans-switch", 6)
    cut = defect.find('<dl class="decision"')
    defect_story, switch_decision = defect[:cut], defect[cut:]
    body = "".join([
        L.sec("17-the-nightly-run", 0),
        L.sec("17-the-nightly-run", 1),
        L.sec("17-the-nightly-run", 2),
        L.sec("17-the-nightly-run", 3),
        L.sec("17-the-nightly-run", 4),
        L.sec("17-the-nightly-run", 5),
        L.sec("17-the-nightly-run", 6),
        f'<h2>{t["watches_h_switch"]}</h2>',
        L.inner("18-dead-mans-switch", 0),
        H.fold(t["watches_fold_name"], L.inner("18-dead-mans-switch", 1)),
        L.sec("18-dead-mans-switch", 2),
        L.sec("18-dead-mans-switch", 3),
        switch_decision,
        f'<h2>{t["watches_h_page"]}</h2>',
        L.inner("19-the-phone", 0),
        H.fold(t["watches_fold_tunnel"], L.inner("19-the-phone", 3) + L.inner("19-the-phone", 4)),
        L.sec("21-the-page", 1),
        H.fold(t["watches_fold_rules"], L.inner("21-the-page", 2)),
        L.sec("21-the-page", 3),
    ])
    chapter("machine-watches", t["watches_title"], t["watches_lede"], body,
            L.sources("17-the-nightly-run", "18-dead-mans-switch", "19-the-phone", "21-the-page"))

    # -- the bug museum ------------------------------------------------------
    blocks = [t["museum_intro"]]
    for n, (title, *rows) in enumerate(t["exhibits"], 1):
        if rows[0] is None:      # the seven notifications: the old chapter's own words
            blocks.append(_exhibit(n, title, None, t["labels"], body_html=defect_story))
        else:
            blocks.append(_exhibit(n, title, rows, t["labels"]))
    blocks.append(t["museum_outro"])
    chapter("bug-museum", t["museum_title"], t["museum_lede"], "".join(blocks), t["museum_sources"])

    # -- the limits: the old chapter, with the boundary's core put first ------
    old = lib["limits"]
    parts = _parts(old["body"])
    boundary = (f'<h2>{t["limits_h_boundary"]}</h2>' + L.inner("20-the-boundary", 0)
                + L.inner("20-the-boundary", 2))
    body = renumber_notes(parts[0] + boundary + "".join(parts[1:]))
    old.update(body=body, minutes=_minutes(body),
               sources=L.sources("20-the-boundary") + old["sources"])
