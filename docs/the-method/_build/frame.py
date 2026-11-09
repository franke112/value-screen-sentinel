"""The frame every chapter shares (2026-11-09), in both languages.

Each chapter has the same parts in the same order: the claim in one
sentence, the story and the rule (the chapter's own text), CENTA at this
step, what the test said, one command to try, and three lines to take away.
This module holds the short parts; the chapter text stays where it was.

CENTA is Central Garden & Pet's Class A share. Every figure in those boxes
is from the company's own SEC filings (reference/CENTA-STRIKE-*.md) or the
owner's own fills (the `sales:` block of the watchlist entry). No vendor
figure appears anywhere in this file: the tests are told in words.
"""

LABELS = {
    "en": dict(claim="The claim", centa="CENTA at this step", test="What the test said",
               tryit="Try it", three="In three lines",
               try_note="From the repository's root, after the install in the manual."),
    "sv": dict(claim="Påståendet", centa="CENTA i det här steget", test="Vad testet sade",
               tryit="Prova själv", three="På tre rader",
               try_note="Från repots rot, efter installationen i manualen."),
}

FRAME = {"en": {}, "sv": {}}


def _f(lang, slug, claim, three, tryit=None, test=None, centa=None):
    FRAME[lang][slug] = dict(claim=claim, three=three, tryit=tryit, test=test, centa=centa)


# ===========================================================================
# English
# ===========================================================================
E = "en"

_f(E, "prologue",
   "A method built from good books was tested on history, most of it did not hold, and the rest of this book is what was left.",
   ["Three months of building gave about 150 rules. Ten days of testing removed most of the mechanical ones.",
    "No edge was shown. An index fund is the base, and this method is the part that is studied.",
    "What remains is a valuation, a few rules about how figures are read, and the reading a person does by hand, measured the slow way."],
   tryit=("less reference/backtest/WHAT-WE-TESTED.md", "The account of all twenty-six attempts, in words."),
   centa="CENTA is the Class A share of Central Garden &amp; Pet, an American company that sells pet supplies and lawn and garden products through shops. The owner of this project bought 148 shares between 20 and 26 October 2026 and sold 146 of them on 27 and 28 October. Every figure in these boxes comes from the company's own filings or from the owner's own trades. It is here as a worked example with its mistakes left in. It is not a recommendation, in either direction.")

_f(E, "01-the-problem",
   "One person cannot read two thousand companies, and cannot tell from the inside whether a decision was careful or lucky.",
   ["About two thousand companies, each with a report every quarter. Nobody reads them all.",
    "Buying on a story is the usual substitute, and a story is not a reason.",
    "Even careful work cannot check itself from the inside. The rest of the book is habits that can be checked from the outside."],
   tryit=("wc -l config/universe/*.csv", "Count them yourself: the lists are dated files in the repository."),
   centa="CENTA did not arrive from reading two thousand reports. On 20 October 2026 a one-off screen of small companies left three names on the table. The owner thought this one the safest of the three, and bought 30 shares the same day at 36.73 dollars. He had a reason and a price. Whether either was sound, nobody yet knew, which is the problem this chapter describes.")

_f(E, "02-value",
   "A share is a piece of a business with a value, the market quotes a different number called the price, and you buy only when the price is well below your estimate of the value.",
   ["Value is what a business's spare cash is worth. Price is what the market quotes today.",
    "Your estimate of value will be wrong, so you leave room: the margin of safety.",
    "Patience is a step in the procedure. The number written down in advance does the waiting."],
   tryit=(".venv/bin/python tools/warren.py KO", "Bear, base and bull value per share for any US company, from its own filings, beside today's price."),
   test="The cushion under the value was tested as a buy rule (attempt 25). Companies bought at or under 85 percent of the method's value did not do better than the rest in both markets and both halves of each period. The cushion is still computed and shown, and it binds nothing (ruling E168). The margin of safety stands as a principle. As a mechanical line, it was not shown to help.",
   centa="What one CENTA share buys: a claim on the spare cash of a business that sells pet food, seeds and lawn products to shops. In its 2025 financial year that spare cash was about 301 million dollars. On 20 October the method put a value of 61.83 dollars on a share that cost 36.73, so the price was 40 percent under the value. It looked like the margin of safety on this page. It was not, because 301 million was one unusually good year. [[Ch:bug-museum]] has what became of that number.")

_f(E, "03-this-project",
   "The tool measures and remembers; a person decides, and every decision is written down with its date.",
   ["Figures come only from the company's own filings, and the owner's view of growth is written before the market's number is seen.",
    "A failed test stays failed, and a rule changes only on a test registered in advance.",
    "Every refusal is tracked. The tool measures; the person decides."],
   tryit=("git log --oneline -5 -- config/watchlist.yaml", "Every decision is a dated line in the history of one file."),
   centa="Both decisions about CENTA are the owner's, and both are in the file with their dates: bought between 20 and 26 October, sold on 27 and 28 October. The check that changed his mind was run by a Claude Code session on his instruction, under a ruling (E141) made on that same 27 October. The session said the value was wrong. He decided what to do about it.")

_f(E, "04-the-screen",
   "A screen does not find good companies; it removes the ones that fail a few coarse tests, so that reading time goes to what is left.",
   ["The list of two thousand is fixed and dated, never fetched live.",
    "The screen asks only what a machine can ask of public figures: is the data fresh, is there five years of history, did the business make cash?",
    "What comes out is a reading list in a fixed random order, with no value and no opinion."],
   tryit=(".venv/bin/python -m vss screen --universe-report", "What the lists hold per market, what was excluded, and why."),
   test="Three parts of the screen were tested and removed. The 15 to 50 percent band (attempts 8 and 12): the companies inside it did no better. The ranking (attempt 24): it did not sort later returns by tenths in both markets. The debt limit and the 'lower than a year ago' test (attempt 25): neither separated returns. What is left is fresh data, five years of history and positive spare cash, in a fixed random order.",
   centa="CENTA came from a one-off screen of small companies run by hand on 20 October, not from the weekly one. It passed what a screen can ask: its spare cash was positive, and its price was 12 percent under the highest close of the last year (35.79 against 40.60). The screen said nothing about the quality of the business. The four quality tests it failed a week later are not in any screen.")

_f(E, "05-refusal",
   "Most companies that are read are refused, a company that fails on a fact about its business stays refused at any price, and 'I cannot judge this' is a real answer.",
   ["The first question is why the price fell. If you cannot say, treat the business as broken.",
    "Four warning signs end a reading on their own.",
    "A name that failed on something other than price comes back only on a named new fact, never on a lower price."],
   tryit=("head -3 config/shadow_book.csv", "The first refusals on record, each with its date, price and one line of reason."),
   test="Seven warning signs once ended a reading on their own. Three were tested and removed (attempts 17 and 24): falling sales, a squeezed margin and swelling unpaid invoices did not separate the companies that did well from the others. A fourth lost its debt leg (attempt 25). Of the signs that could be tested, only repeated earnings misses separated returns. Cuts to a company's own forecast and the loss of both top executives could not be tested, for lack of data, and stay.",
   centa="CENTA was not refused. It was bought first and tested afterwards, which is the order this chapter exists to prevent. When the quality tests were run on 27 October it failed four of five: a return of 12.6 percent on the capital in the business against a bar of 15; one year, 2022, in which the owners' earnings were negative; net debt of 4.5 times its spare cash against a limit of 3; and a return of 4.9 percent on the companies it had bought, against the 9.5 percent the method demands. Under the rule of that day, a name that fails is sold. [[Ch:tested]] says what later became of that rule.")

_f(E, "06-what-gets-read",
   "A figure counts only if you can point to the filing, the period and the page it came from; everything else is hearsay.",
   ["Every figure carries where it came from, which period it covers, and whether anyone has checked it.",
    "Nothing is scaled, annualised or borrowed from another period. A figure of the wrong length is missing.",
    "A valuation refuses to run on a figure nobody has read back."],
   tryit=(".venv/bin/python -m vss manual --ticker CTSH", "One company's figures, and whether a valuation may read them. Exit code 1 means it may not, and the reason is printed."),
   centa="The first valuation read the figures CENTA had filed with the regulator, and nothing else. Two things were not in them. On 19 October, the day before the first purchase, the company announced that it had bought the seed company Burpee. It did so by press release only: the deal was too small to require a filing. And on 22 September it had filed that the head of its garden division was retiring. The owner found both a week later, and asked how they could have been missed. The rule since then: before any valuation, the company's own press releases for the last sixty days and every filing since its last report are read.")

_f(E, "07-reverse-dcf",
   "Do not ask what a business is worth; ask what growth today's price assumes, and whether you believe it.",
   ["Run the valuation backwards: from the price, solve for the growth it needs.",
    "The answer is an assumption you can argue with, not a number you have to trust.",
    "The arithmetic is fixed (ten years, then 2.5 percent, a 9.5 percent required return), so the only thing left to disagree about is growth."],
   tryit=(".venv/bin/python -m vss strike --ticker CTSH --dry-run", "One company's valuation, with the growth today's price assumes. It may refuse, and then it says why."),
   test="The growth the method derives from a company's own history was tested against what then happened (attempt 23). It did not overestimate: the growth that followed was above the derived figure on every US date and in both Nordic halves, and a planned haircut was struck. Whether the gap between assumed and believed growth predicts returns is another question, and there the answer was no: value against price did not sort returns by tenths in both markets (attempt 24).",
   centa="On the first valuation's figures, CENTA's price seemed to assume a business shrinking by almost 5 percent a year. That looked like a gift: the market expecting decline from a company that was not declining. On the corrected figures a week later, the price of 39.13 dollars assumed growth of 1.7 percent a year. The owner's own written view was 2 percent. Price and belief were saying almost the same thing. There was no gap to buy.")

_f(E, "08-pre-registration",
   "Write down the growth you believe before you calculate the growth the price assumes, or your belief will quietly move to meet it.",
   ["Three growth rates, low, base and high, are written with their reasons and timestamped.",
    "Only then is the price's own assumption calculated.",
    "If the market's number was seen first, the view is void for that company in that round."],
   tryit=("cat reference/growth-views/CENTA.md", "A registered view: three growth rates and their reasons, dated before the value."),
   test="Pre-registration itself cannot be tested on history: there is no record of what an investor would have written. What was tested is the same discipline turned on the method. Every one of the twenty-six tests was registered before it ran, and one result that looked good in the years the method was developed on was not confirmed on two later years.",
   centa="The view on CENTA was written on 20 October, before the value: growth of 2 percent a year in the base case, minus 1 in the low case, 3.5 in the high. A week later the value fell from 61.83 to 40.19. The growth view did not move by a decimal. What moved was the cash the growth is applied to, and the cost of the companies CENTA buys. That is what writing the view first bought: it could not be bent to rescue the purchase, and it was not the part that was wrong.")

_f(E, "09-three-outcomes",
   "Every test ends in pass, fail or data missing, and the third is never quietly turned into the second.",
   ["PASS and FAIL mean the test ran. DATA MISSING means it could not.",
    "A missing figure is a fact about the data, not about the company.",
    "DATA MISSING is information: it says what to go and find, and how much of the method is actually running."],
   tryit=('.venv/bin/python -m vss run --dry-run | grep -c "DATA MISSING"', "How many times tonight's report says it could not check something."),
   test="The history tests found this very fault in their own data. A vendor's empty field for total debt had been read as zero for a large part of the Nordic list, so those companies looked free of debt ([[ch:bug-museum]]). Empty was not zero there either.",
   centa="What CENTA paid for Burpee was not disclosed. The valuation does not call that zero, and it does not invent a single number. It carries a range, 90 to 260 million dollars, worked out from Burpee's published retail sales and labelled as an estimate, and it values at the dear end. A later ruling took the estimate out because it was not a filed figure. A review put it back the next day: a company that was bought was paid for, and 'not disclosed' does not mean 'free'.")

_f(E, "10-the-funnel",
   "Every company the method has touched is in exactly one of six states, and only a person moves it from one to another.",
   ["Six statuses: in the pipeline, read but not watched, watched for price, watched behind a gate, held, dropped.",
    "The tool reports where a name stands and points when something crosses a line. It never moves a name.",
    "The master list puts all of them on one page, rebuilt every night."],
   tryit=(".venv/bin/python tools/master_list.py --short", "Every company looked at, in five groups, with the cheapest to review first."),
   centa="CENTA entered as PIPELINE on 20 October and became HELD the same day. It is still HELD: two shares are left. In the master list of 9 November it stood under 'owned', at 41.84 dollars against a base value of 40.19. A status says where a company stands in the process. It does not say the process was followed.")

_f(E, "11-the-decision",
   "A decision is never 'buy': it is a price, the conditions and the exit, written down before any money moves.",
   ["X is the most you will pay: the value times a cushion set by how well you understand the business. It is shown as information.",
    "Y is the conditions that must still hold. Z is the exit, written while you have no stake in the answer.",
    "At most six percent of the portfolio goes into one company."],
   tryit=(".venv/bin/python -m vss queue --dry-run", "Every valued company against its lines tonight."),
   test="Two parts were tested and removed. The price stop (attempts 10 and 18): no level helped in any selection, and with real trading costs each one lost money. The exit is still written first, and for this owner it reads 'no price stop'. The cushion as a binding buy line (attempt 25): not shown to help, and now information. A third part was tested and kept: holding fewer names did not raise the typical outcome and only widened the spread (attempt 11), so one name is at most six percent.",
   centa="None of the three was written before the money moved. The owner bought over six days, at prices from 36.73 to 39.33 dollars, 148 shares in all. The exit was written afterwards, by the check: the name fails the quality tests, so sell at the base value of 40.19. The price that day was under 40.19, and he sold at the market instead: 75 shares at 38.80 on 27 October and 71 at 38.34 on the 28th. That is roughly what he had paid. Two shares were kept.")

_f(E, "12-shadow-book",
   "A method that only measures what it bought cannot learn, so every refusal and every sale is priced against the index afterwards.",
   ["Each refusal is one row: the company, the date, the verdict, the price that day and one line of reason.",
    "It is set against an index over the same period, in the same currency and the same kind of return.",
    "It is not a signal and nothing reads it. It is looked at once a year, so that it cannot bend the rules."],
   tryit=(".venv/bin/python -m vss shadow --dry-run", "Every refusal against the indices since the day of its verdict. Add `vss sales --dry-run` for the positions that were sold."),
   test="This chapter is the test, for everything no history could test: the reading, the judgement that a business is understood, the view on growth. It runs forward in real time, it is read once a year, and its first useful verdict needs several years of rows.",
   centa="CENTA is not in the shadow book, because it was bought. But its sale is measured the same way, in the sales record. The owner sold at 38.80 and 38.34 dollars. On 9 November the share stood at 41.84. So far the sale looks early. The record exists to say exactly that, about the owner's own decision, and to say it again at 30, 90 and 365 days.")

_f(E, "tested",
   "A rule that sounds right is not evidence: every mechanical rule was tested on history under a bar set in advance, and most were removed.",
   ["Each test was written down before it ran, and a rule held only if it helped in both markets and in both halves of each period.",
    "The stop, the band, the ranking, three warning signs, the debt limits and the cushion as a buy line were removed.",
    "No edge was found. The history is closed, and the next test runs on new data in April 2027."],
   tryit=("ls tools/backtest/", "The test scripts. With a data licence of your own they reproduce the results, or show where they are wrong."),
   centa="The rule that sold CENTA was itself tested two weeks later. 'It fails the quality tests, so sell at the base value' was part of attempt 25, and the quality tests did not separate the companies that did well from those that did not. The rule was removed on 9 November. The sale was not undone, and could not be. It stands in the record as the owner's decision of 27 October, with no price attached to the two shares that are left.")

_f(E, "machine-reads",
   "The machine may measure and remember but not decide, and it refuses to print a value whose origin has a gap.",
   ["The tool measures; the owner decides. No part that runs on a schedule may write a decision.",
    "A value is printed only from a complete run record: every input and every choice, or nothing.",
    "The rules are a dated document first, and the code implements them."],
   tryit=("ls reference/run-records/ | grep CENTA", "One company's run records. Every valuation ever made of it can be replayed."),
   centa="CENTA has six run records, one for every time it was valued: 20 October (61.83), three on 27 October as the rules were corrected (28.60, then 40.19, then the check that confirmed 40.19), and two on 8 November. Each can be replayed to the cent, and the owner's file names the one in force. Without that, 'the value of CENTA' would be whichever number somebody remembered.")

_f(E, "machine-watches",
   "The machine watches every night and speaks only when something changed, so its silence has to be made trustworthy.",
   ["Every night prices are held against decisions already made, and each new report is read and the company valued again.",
    "The phone hears only a change.",
    "Two observers make silence mean something: one on the machine says what broke, one outside notices when nothing arrives."],
   tryit=("systemctl --user list-timers 'vss*'", "What runs next, if you installed the timers."),
   centa="CENTA is in the nightly queue with its two shares: a base value of 40.19, a bull value of 54.70 at which the queue would say SÄLJ, and a reminder once a week that a sale was decided and two shares are still held. Its annual report is expected at the end of November. When it is filed, the queue will fetch it, read it twice, value the company again on its last four quarters, and send a message only if the outcome changed.")

_f(E, "bug-museum",
   "Every wrong number this project caught was caught by reading a whole table or by two things failing to agree, never by searching for it.",
   ["Units, tickers, empty fields and sentences all go wrong quietly.",
    "A filter finds what you already suspect. Reading everything finds the rest.",
    "Each fault left a rule behind: no arithmetic across units, empty is not zero, and a fix made after a result is counted as one more look."],
   tryit=(".venv/bin/python -m vss run --dry-run | less", "Read the whole table once. That is how most of these were found."),
   centa="The last exhibit is CENTA: 61.83, 28.60 and 40.19 in one day. The CENTA boxes in the other chapters are that fall, told one step at a time.")

_f(E, "limits",
   "The tool cannot tell you a business is good, cannot make you patient and cannot stop you overriding it, and the last of those is on purpose.",
   ["The limits on security and monitoring are written down, not hidden.",
    "The method cannot judge a business for you, and cannot supply patience.",
    "The scheduled machine decides nothing, on purpose: a tool that decided would be trusted, and a trusted tool stops being checked."],
   tryit=(".venv/bin/python -m vss doctor", "What this machine can and cannot do right now, one line per check."),
   centa="Nothing in the tool stopped the owner buying CENTA before the checks were done. Nothing could. The valuation existed; the quality tests were written a week later. The tool can refuse to print a value with a gap in its origin. It cannot refuse to let a person act on a value that is complete and wrong.")

_f(E, "close",
   "There is no easy way: the method is slow on purpose, and the machine exists to keep the slowness honest.",
   ["The method was written before the code, and the code cannot overrule it.",
    "Every refusal is measured, and every rule was tested where it could be.",
    "No edge was found. What is left is reading, writing things down first, and checking afterwards."],
   tryit=("git clone https://github.com/franke112/value-screen-sentinel.git", "Everything in this book is in the repository, with the tests."),
   centa="CENTA in one paragraph. Bought at 36.73 to 39.33 dollars on a value of 61.83. A week later the method, applied properly, said 40.19. Sold at 38.80 and 38.34, about what was paid. The method did not make money on CENTA. It found its own mistake within a week, said so in writing, and changed two rules. That is what it is for.")


# ===========================================================================
# Svenska
# ===========================================================================
S = "sv"

_f(S, "prologue",
   "En metod byggd ur bra böcker prövades mot historien, det mesta höll inte, och resten av boken är det som blev kvar.",
   ["Tre månaders byggande gav omkring 150 regler. Tio dagars testande tog bort de flesta av de mekaniska.",
    "Ingen fördel visades. En indexfond är grunden, och den här metoden är den del som studeras.",
    "Kvar finns en värdering, några regler om hur siffror läses, och läsningen som en människa gör för hand, mätt den långsamma vägen."],
   tryit=("less reference/backtest/WHAT-WE-TESTED.md", "Redogörelsen för alla tjugosex försök, i ord (på engelska)."),
   centa="CENTA är A-aktien i Central Garden &amp; Pet, ett amerikanskt bolag som säljer djurtillbehör och trädgårdsprodukter genom butiker. Projektets ägare köpte 148 aktier mellan den 20 och 26 oktober 2026 och sålde 146 av dem den 27 och 28 oktober. Varje siffra i de här rutorna kommer ur bolagets egna rapporter eller ur ägarens egna affärer. Det står här som ett räkneexempel med misstagen kvar. Det är ingen rekommendation, åt något håll.")

_f(S, "01-the-problem",
   "En människa kan inte läsa tvåtusen bolag, och kan inte inifrån avgöra om ett beslut var noggrant eller bara tur.",
   ["Omkring tvåtusen bolag, vart och ett med en rapport varje kvartal. Ingen läser alla.",
    "Att köpa på en berättelse är den vanliga ersättningen, och en berättelse är inget skäl.",
    "Inte ens noggrant arbete kan kontrollera sig självt inifrån. Resten av boken är vanor som kan kontrolleras utifrån."],
   tryit=("wc -l config/universe/*.csv", "Räkna dem själv: listorna är daterade filer i repot."),
   centa="CENTA kom inte ur läsningen av tvåtusen rapporter. Den 20 oktober 2026 lämnade en engångsscreening av småbolag tre namn på bordet. Ägaren tyckte att det här var det säkraste av de tre, och köpte 30 aktier samma dag för 36,73 dollar. Han hade ett skäl och en kurs. Om något av dem höll visste ingen ännu, och det är just problemet som kapitlet beskriver.")

_f(S, "02-value",
   "En aktie är en bit av ett företag som har ett värde, marknaden noterar ett annat tal som kallas pris, och du köper bara när priset ligger klart under din uppskattning av värdet.",
   ["Värde är vad ett företags fria kassaflöde är värt. Pris är vad marknaden noterar i dag.",
    "Din uppskattning av värdet kommer att vara fel, så du lämnar utrymme: säkerhetsmarginalen.",
    "Tålamod är ett steg i proceduren. Talet som skrevs ned i förväg sköter väntandet."],
   tryit=(".venv/bin/python tools/warren.py KO", "Sämre fall, basfall och bättre fall per aktie för vilket amerikanskt bolag som helst, ur dess egna rapporter, bredvid dagens kurs."),
   test="Kudden under värdet testades som köpregel (försök 25). Bolag köpta vid eller under 85 procent av metodens värde gick inte bättre än resten på båda marknaderna och i båda halvorna av varje period. Kudden räknas fortfarande ut och visas, och den binder ingenting (beslut E168). Säkerhetsmarginalen står kvar som princip. Som mekanisk linje visades den inte hjälpa.",
   centa="Vad en CENTA-aktie köper: ett anspråk på det fria kassaflödet i ett företag som säljer djurmat, fröer och gräsmatteprodukter till butiker. Räkenskapsåret 2025 var det kassaflödet omkring 301 miljoner dollar. Den 20 oktober satte metoden ett värde på 61,83 dollar på en aktie som kostade 36,73, så priset låg 40 procent under värdet. Det såg ut som säkerhetsmarginalen på den här sidan. Det var det inte, för 301 miljoner var ett ovanligt bra år. [[Ch:bug-museum]] berättar vad som hände med det talet.")

_f(S, "03-this-project",
   "Verktyget mäter och minns; en människa bestämmer, och varje beslut skrivs ned med sitt datum.",
   ["Siffror kommer bara ur bolagets egna rapporter, och ägarens tillväxtbedömning skrivs innan marknadens tal syns.",
    "Ett underkänt test förblir underkänt, och en regel ändras bara genom ett test som registrerats i förväg.",
    "Varje nej följs upp. Verktyget mäter; människan bestämmer."],
   tryit=("git log --oneline -5 -- config/watchlist.yaml", "Varje beslut är en daterad rad i en enda fils historik."),
   centa="Båda besluten om CENTA är ägarens, och båda står i filen med sina datum: köpt mellan den 20 och 26 oktober, sålt den 27 och 28 oktober. Kontrollen som fick honom att ändra sig kördes av en Claude Code-session på hans uppdrag, enligt ett beslut (E141) som fattades samma 27 oktober. Sessionen sade att värdet var fel. Han bestämde vad som skulle göras åt det.")

_f(S, "04-the-screen",
   "En screening hittar inte bra bolag; den tar bort dem som faller på några grova test, så att lästiden går till det som blir kvar.",
   ["Listan på tvåtusen är fast och daterad, den hämtas aldrig direkt.",
    "Screeningen frågar bara det en maskin kan fråga offentliga siffror: är datan färsk, finns fem års historik, gav verksamheten pengar?",
    "Ut kommer en läslista i fast slumpordning, utan värde och utan åsikt."],
   tryit=(".venv/bin/python -m vss screen --universe-report", "Vad listorna innehåller per marknad, vad som uteslöts och varför."),
   test="Tre delar av screeningen testades och togs bort. Bandet på 15 till 50 procent (försök 8 och 12): bolagen inom det gick inte bättre. Rangordningen (försök 24): den sorterade inte senare avkastning i tiondelar på båda marknaderna. Skuldgränsen och testet 'lägre än för ett år sedan' (försök 25): inget av dem skilde avkastningen åt. Kvar finns färsk data, fem års historik och positivt fritt kassaflöde, i fast slumpordning.",
   centa="CENTA kom ur en engångsscreening av småbolag som kördes för hand den 20 oktober, inte ur den veckovisa. Det klarade det en screening kan fråga: det fria kassaflödet var positivt, och kursen låg 12 procent under årets högsta stängning (35,79 mot 40,60). Screeningen sade ingenting om verksamhetens kvalitet. De fyra kvalitetstest som det föll på en vecka senare finns inte i någon screening.")

_f(S, "05-refusal",
   "De flesta bolag som läses får nej, ett bolag som faller på ett faktum om verksamheten förblir underkänt oavsett pris, och 'det här kan jag inte bedöma' är ett riktigt svar.",
   ["Första frågan är varför kursen föll. Kan du inte säga det, behandla verksamheten som trasig.",
    "Fyra varningstecken avslutar en läsning på egen hand.",
    "Ett namn som föll på något annat än priset kommer tillbaka bara på ett namngivet nytt faktum, aldrig på en lägre kurs."],
   tryit=("head -3 config/shadow_book.csv", "De första nejen i registret, vart och ett med datum, kurs och en rad med skälet."),
   test="En gång avslutade sju varningstecken en läsning på egen hand. Tre testades och togs bort (försök 17 och 24): fallande försäljning, pressad marginal och svällande obetalda fakturor skilde inte bolagen som gick bra från de andra. Ett fjärde förlorade sitt skuldben (försök 25). Av de tecken som gick att testa var det bara upprepade vinstmissar som skilde avkastningen åt. Sänkta egna prognoser och att både vd och finanschef lämnar gick inte att testa, i brist på data, och står kvar.",
   centa="CENTA fick inget nej. Det köptes först och testades efteråt, vilket är den ordning kapitlet finns till för att förhindra. När kvalitetstesten kördes den 27 oktober föll det på fyra av fem: en avkastning på 12,6 procent på kapitalet i verksamheten mot en ribba på 15; ett år, 2022, då ägarnas intjäning var negativ; en nettoskuld på 4,5 gånger det fria kassaflödet mot en gräns på 3; och en avkastning på 4,9 procent på bolagen det hade köpt, mot de 9,5 procent metoden kräver. Enligt regeln den dagen säljs ett namn som faller. [[Ch:tested]] berättar vad som senare hände med den regeln.")

_f(S, "06-what-gets-read",
   "En siffra räknas bara om du kan peka på rapporten, perioden och sidan den kom ifrån; allt annat är hörsägen.",
   ["Varje siffra bär med sig var den kom ifrån, vilken period den gäller och om någon har kontrollerat den.",
    "Ingenting skalas, räknas om till helår eller lånas från en annan period. En siffra av fel längd saknas.",
    "En värdering vägrar köra på en siffra som ingen har läst tillbaka."],
   tryit=(".venv/bin/python -m vss manual --ticker CTSH", "Ett bolags siffror, och om en värdering får läsa dem. Felkod 1 betyder att den inte får, och skälet skrivs ut."),
   centa="Den första värderingen läste siffrorna CENTA hade lämnat till tillsynsmyndigheten, och inget annat. Två saker fanns inte i dem. Den 19 oktober, dagen före första köpet, meddelade bolaget att det hade köpt fröföretaget Burpee. Det skedde bara i ett pressmeddelande: affären var för liten för att kräva en anmälan. Och den 22 september hade det anmält att chefen för trädgårdsdivisionen skulle gå i pension. Ägaren hittade båda en vecka senare, och frågade hur de hade kunnat missas. Regeln sedan dess: före varje värdering läses bolagets egna pressmeddelanden de senaste sextio dagarna och varje anmälan sedan senaste rapporten.")

_f(S, "07-reverse-dcf",
   "Fråga inte vad ett företag är värt; fråga vilken tillväxt dagens pris förutsätter, och om du tror på den.",
   ["Kör värderingen baklänges: lös ut den tillväxt som priset kräver.",
    "Svaret är ett antagande du kan argumentera mot, inte ett tal du måste lita på.",
    "Räkningen är fast (tio år, sedan 2,5 procent, 9,5 procents avkastningskrav), så det enda kvar att vara oense om är tillväxten."],
   tryit=(".venv/bin/python -m vss strike --ticker CTSH --dry-run", "Ett bolags värdering, med den tillväxt dagens pris förutsätter. Den kan vägra, och säger då varför."),
   test="Tillväxten som metoden härleder ur ett bolags egen historia testades mot vad som sedan hände (försök 23). Den överskattade inte: tillväxten som följde låg över den härledda siffran vid varje amerikanskt datum och i båda nordiska halvorna, och ett planerat avdrag ströks. Om glappet mellan förutsatt och trodd tillväxt förutsäger avkastning är en annan fråga, och där blev svaret nej: värde mot pris sorterade inte avkastningen i tiondelar på båda marknaderna (försök 24).",
   centa="Med den första värderingens siffror såg CENTA:s pris ut att förutsätta en verksamhet som krympte med nästan 5 procent om året. Det såg ut som en gåva: marknaden väntade sig nedgång av ett bolag som inte gick nedåt. Med de rättade siffrorna en vecka senare förutsatte kursen 39,13 dollar en tillväxt på 1,7 procent om året. Ägarens egen nedskrivna bedömning var 2 procent. Pris och tro sade nästan samma sak. Det fanns inget glapp att köpa.")

_f(S, "08-pre-registration",
   "Skriv ned den tillväxt du tror på innan du räknar ut den tillväxt priset förutsätter, annars flyttar sig din tro tyst för att möta den.",
   ["Tre tillväxttal, lågt, bas och högt, skrivs med sina skäl och tidsstämplas.",
    "Först därefter räknas prisets eget antagande ut.",
    "Om marknadens tal sågs först är bedömningen ogiltig för det bolaget i den omgången."],
   tryit=("cat reference/growth-views/CENTA.md", "En registrerad bedömning: tre tillväxttal och skälen, daterade före värdet (på engelska)."),
   test="Själva förregistreringen går inte att testa mot historien: det finns inget register över vad en investerare skulle ha skrivit. Det som testades är samma disciplin vänd mot metoden. Vart och ett av de tjugosex testerna registrerades innan det kördes, och ett resultat som såg bra ut under åren metoden utvecklades på bekräftades inte på två senare år.",
   centa="Bedömningen av CENTA skrevs den 20 oktober, före värdet: 2 procents tillväxt om året i basfallet, minus 1 i det sämre fallet, 3,5 i det bättre. En vecka senare föll värdet från 61,83 till 40,19. Tillväxtbedömningen rörde sig inte en decimal. Det som rörde sig var kassaflödet som tillväxten läggs på, och kostnaden för bolagen CENTA köper. Det var vad det gav att skriva bedömningen först: den gick inte att böja för att rädda köpet, och det var inte den som var fel.")

_f(S, "09-three-outcomes",
   "Varje test slutar i godkänt, underkänt eller data saknas, och det tredje görs aldrig tyst om till det andra.",
   ["GODKÄNT och UNDERKÄNT betyder att testet kördes. DATA SAKNAS betyder att det inte gick.",
    "En siffra som saknas är ett faktum om datan, inte om bolaget.",
    "DATA SAKNAS är information: det säger vad som ska letas upp, och hur mycket av metoden som faktiskt körs."],
   tryit=('.venv/bin/python -m vss run --dry-run | grep -c "DATA MISSING"', "Hur många gånger kvällens rapport säger att den inte kunde kontrollera något."),
   test="Historietesterna hittade just det här felet i sin egen data. En leverantörs tomma fält för total skuld hade lästs som noll för en stor del av den nordiska listan, så de bolagen såg skuldfria ut ([[ch:bug-museum]]). Tomt var inte noll där heller.",
   centa="Vad CENTA betalade för Burpee offentliggjordes inte. Värderingen kallar inte det noll, och hittar inte på ett enda tal. Den bär ett intervall, 90 till 260 miljoner dollar, framräknat ur Burpees publicerade butiksförsäljning och märkt som en uppskattning, och den värderar i den dyra änden. Ett senare beslut tog bort uppskattningen eftersom den inte var en rapporterad siffra. En granskning lade tillbaka den dagen efter: ett bolag som köptes blev betalt, och 'inte offentliggjort' betyder inte 'gratis'.")

_f(S, "10-the-funnel",
   "Varje bolag metoden har rört vid befinner sig i exakt ett av sex tillstånd, och bara en människa flyttar det från ett till ett annat.",
   ["Sex statusar: på väg in, läst men inte bevakat, bevakat för pris, bevakat bakom en spärr, ägt, struket.",
    "Verktyget rapporterar var ett namn står och pekar när något korsar en linje. Det flyttar aldrig ett namn.",
    "Huvudlistan lägger alla på en sida, ombyggd varje natt."],
   tryit=(".venv/bin/python tools/master_list.py --short", "Varje bolag vi har tittat på, i fem grupper, med de billigaste att granska först."),
   centa="CENTA kom in som PIPELINE den 20 oktober och blev HELD samma dag. Det är fortfarande HELD: två aktier finns kvar. I huvudlistan den 9 november stod det under 'ägda', på 41,84 dollar mot ett basvärde på 40,19. En status säger var ett bolag står i processen. Den säger inte att processen följdes.")

_f(S, "11-the-decision",
   "Ett beslut är aldrig 'köp': det är ett pris, villkoren och utgången, nedskrivna innan några pengar rör sig.",
   ["X är det mesta du betalar: värdet gånger en kudde som bestäms av hur väl du förstår verksamheten. Det visas som information.",
    "Y är villkoren som fortfarande måste gälla. Z är utgången, skriven medan du inte har något att förlora på svaret.",
    "Högst sex procent av portföljen går in i ett bolag."],
   tryit=(".venv/bin/python -m vss queue --dry-run", "Varje värderat bolag mot sina linjer i kväll."),
   test="Två delar testades och togs bort. Kursstoppet (försök 10 och 18): ingen nivå hjälpte i något urval, och med verkliga handelskostnader förlorade var och en pengar. Utgången skrivs fortfarande först, och för den här ägaren lyder den 'inget kursstopp'. Kudden som bindande köplinje (försök 25): visades inte hjälpa, och är nu information. En tredje del testades och behölls: färre namn höjde inte det typiska utfallet utan vidgade bara spridningen (försök 11), så ett namn är högst sex procent.",
   centa="Ingen av de tre skrevs innan pengarna rörde sig. Ägaren köpte under sex dagar, till kurser från 36,73 till 39,33 dollar, 148 aktier sammanlagt. Utgången skrevs efteråt, av kontrollen: namnet faller på kvalitetstesten, så sälj vid basvärdet 40,19. Kursen den dagen låg under 40,19, och han sålde till marknadspris i stället: 75 aktier för 38,80 den 27 oktober och 71 för 38,34 den 28. Det är ungefär vad han hade betalat. Två aktier behölls.")

_f(S, "12-shadow-book",
   "En metod som bara mäter det den köpte kan inte lära sig, så varje nej och varje försäljning prissätts mot index efteråt.",
   ["Varje nej är en rad: bolaget, datumet, utslaget, kursen den dagen och en rad med skälet.",
    "Det ställs mot ett index över samma period, i samma valuta och med samma sorts avkastning.",
    "Det är ingen signal och ingenting läser det. Det tittas på en gång om året, så att det inte kan böja reglerna."],
   tryit=(".venv/bin/python -m vss shadow --dry-run", "Varje nej mot indexen sedan dagen för utslaget. Lägg till `vss sales --dry-run` för positionerna som såldes."),
   test="Det här kapitlet är testet, för allt som ingen historia kunde pröva: läsningen, bedömningen att en verksamhet är förstådd, tillväxtbedömningen. Det löper framåt i verklig tid, det läses en gång om året, och dess första användbara dom kräver flera års rader.",
   centa="CENTA står inte i skuggboken, för det köptes. Men försäljningen mäts på samma sätt, i försäljningsregistret. Ägaren sålde för 38,80 och 38,34 dollar. Den 9 november stod aktien i 41,84. Än så länge ser försäljningen tidig ut. Registret finns för att säga just det, om ägarens eget beslut, och säga det igen efter 30, 90 och 365 dagar.")

_f(S, "tested",
   "En regel som låter rätt är inget belägg: varje mekanisk regel prövades mot historien under en ribba som sattes i förväg, och de flesta togs bort.",
   ["Varje test skrevs ned innan det kördes, och en regel höll bara om den hjälpte på båda marknaderna och i båda halvorna av varje period.",
    "Stoppet, bandet, rangordningen, tre varningstecken, skuldgränserna och kudden som köplinje togs bort.",
    "Ingen fördel hittades. Historien är stängd, och nästa test körs på ny data i april 2027."],
   tryit=("ls tools/backtest/", "Testskripten. Med en egen datalicens återskapar de resultaten, eller visar var de är fel."),
   centa="Regeln som sålde CENTA testades själv två veckor senare. 'Det faller på kvalitetstesten, så sälj vid basvärdet' ingick i försök 25, och kvalitetstesten skilde inte bolagen som gick bra från dem som inte gjorde det. Regeln togs bort den 9 november. Försäljningen gjordes inte ogjord, och kunde inte göras det. Den står i registret som ägarens beslut den 27 oktober, utan något pris knutet till de två aktier som är kvar.")

_f(S, "machine-reads",
   "Maskinen får mäta och minnas men inte bestämma, och den vägrar skriva ut ett värde vars ursprung har en lucka.",
   ["Verktyget mäter; ägaren bestämmer. Ingen del som körs på schema får skriva ett beslut.",
    "Ett värde skrivs bara ut ur ett fullständigt körningsprotokoll: varje indata och varje val, eller ingenting.",
    "Reglerna är ett daterat dokument först, och koden genomför dem."],
   tryit=("ls reference/run-records/ | grep CENTA", "Ett bolags körningsprotokoll. Varje värdering som någonsin gjorts av det kan spelas upp igen."),
   centa="CENTA har sex körningsprotokoll, ett för varje gång det värderades: den 20 oktober (61,83), tre den 27 oktober medan reglerna rättades (28,60, sedan 40,19, sedan kontrollen som bekräftade 40,19), och två den 8 november. Vart och ett kan spelas upp på centen, och ägarens fil säger vilket som gäller. Utan det vore 'värdet på CENTA' det tal någon råkade minnas.")

_f(S, "machine-watches",
   "Maskinen vakar varje natt och säger bara till när något har ändrats, så dess tystnad måste göras pålitlig.",
   ["Varje natt hålls kurserna mot beslut som redan är fattade, och varje ny rapport läses och bolaget värderas igen.",
    "Telefonen får bara höra en förändring.",
    "Två observatörer gör att tystnaden betyder något: en på maskinen säger vad som gick sönder, en utanför märker när ingenting kommer."],
   tryit=("systemctl --user list-timers 'vss*'", "Vad som körs härnäst, om du har installerat timrarna."),
   centa="CENTA står i den nattliga kön med sina två aktier: ett basvärde på 40,19, ett värde i det bättre fallet på 54,70 där kön skulle säga SÄLJ, och en påminnelse en gång i veckan om att en försäljning är beslutad och två aktier fortfarande ägs. Årsredovisningen väntas i slutet av november. När den lämnas in hämtar kön den, läser den två gånger, värderar bolaget igen på dess fyra senaste kvartal, och skickar ett meddelande bara om utfallet har ändrats.")

_f(S, "bug-museum",
   "Varje felaktigt tal som projektet har fångat fångades genom att någon läste en hel tabell eller genom att två saker inte stämde överens, aldrig genom en sökning.",
   ["Enheter, tickrar, tomma fält och meningar går alla fel i tysthet.",
    "Ett filter hittar det du redan misstänker. Att läsa allt hittar resten.",
    "Varje fel lämnade en regel efter sig: ingen räkning över enhetsgränser, tomt är inte noll, och en rättning efter ett resultat räknas som en titt till."],
   tryit=(".venv/bin/python -m vss run --dry-run | less", "Läs hela tabellen en gång. Så hittades de flesta av de här."),
   centa="Det sista föremålet är CENTA: 61,83, 28,60 och 40,19 på en dag. CENTA-rutorna i de andra kapitlen är det fallet, berättat ett steg i taget.")

_f(S, "limits",
   "Verktyget kan inte säga dig att ett företag är bra, kan inte göra dig tålmodig och kan inte hindra dig från att köra över det, och det sista är med flit.",
   ["Gränserna för säkerhet och övervakning är nedskrivna, inte gömda.",
    "Metoden kan inte bedöma en verksamhet åt dig, och kan inte förse dig med tålamod.",
    "Den schemalagda maskinen bestämmer ingenting, med flit: ett verktyg som bestämde skulle man lita på, och ett verktyg man litar på slutar man kontrollera."],
   tryit=(".venv/bin/python -m vss doctor", "Vad den här maskinen kan och inte kan just nu, en rad per kontroll."),
   centa="Ingenting i verktyget hindrade ägaren från att köpa CENTA innan kontrollerna var gjorda. Ingenting kunde. Värderingen fanns; kvalitetstesten skrevs en vecka senare. Verktyget kan vägra skriva ut ett värde med en lucka i sitt ursprung. Det kan inte vägra låta en människa handla på ett värde som är fullständigt och fel.")

_f(S, "close",
   "Det finns ingen lätt väg: metoden är långsam med flit, och maskinen finns för att hålla långsamheten ärlig.",
   ["Metoden skrevs före koden, och koden kan inte köra över den.",
    "Varje nej mäts, och varje regel prövades där det gick.",
    "Ingen fördel hittades. Kvar finns att läsa, att skriva ned saker först och att kontrollera efteråt."],
   tryit=("git clone https://github.com/franke112/value-screen-sentinel.git", "Allt i boken finns i repot, med testerna."),
   centa="CENTA i ett stycke. Köpt för 36,73 till 39,33 dollar på ett värde av 61,83. En vecka senare sade metoden, rätt tillämpad, 40,19. Sålt för 38,80 och 38,34, ungefär vad som betalades. Metoden tjänade inga pengar på CENTA. Den hittade sitt eget misstag inom en vecka, sade det skriftligt och ändrade två regler. Det är vad den är till för.")
