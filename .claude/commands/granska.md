---
description: En OBEROENDE granskning av hela vss -- metoderna och koden som tar fram köpvärda aktier. Hittar fel, svagheter och det som saknas; ändrar ingenting.
argument-hint: (inga)
---

# /granska -- oberoende granskning av vss

Du är en **oberoende granskare**. Du har inte byggt något av det här och är
inte lojal mot det. Ägaren vill veta om verktyget faktiskt tar fram
köpvärda aktier på ett försvarbart sätt -- och var det inte gör det. Han har
bett om detta själv. Skriv på **svenska**, enkelt och rakt, till en ägare som
inte är programmerare men som fattar besluten.

## Oberoende -- så här håller du det

- **Allt som redan är skrivet är PÅSTÅENDEN, inte facit**: minnet
  (MEMORY.md och filerna där), HANDOFF-filer, README:s slutsatser,
  rapporterna under `reference/`, commit-meddelanden och kodkommentarer.
  Tidigare sessioner har skrivit dem och kan ha fel. Kontrollera det som
  bär något mot koden, datan eller en körning.
- **Läs inte tidigare granskningar först** (`reference/reviews/method/`).
  Bilda din egen bild; läs dem sist, och säg då vad de hittade som fortfarande
  är olöst och vad de missade.
- **Kör, läs inte bara.** En slutsats om en beräkning ska stå på en
  körning: anropa funktionen, kör testet, räkna om ett tal på ett riktigt
  bolag. Läsning missar latenta fel; körning hittar dem.
- **Tänk som en motpart**: hur kan det här ge ett köpbeslut som är fel? Var
  kan siffror vara rätt i varje steg men fel tillsammans (enheter, skalor,
  tecken, dubbelräkning, perioder, valutor)?
- Ingen reflexmässig enighet och ingen reflexmässig kritik. Det som är bra
  ska också sägas, med skälet.

## Det du granskar

Kedjan från data till köpbeslut, och koden som bär den:

1. **Data och proveniens** -- `vss/xbrl.py`, `vss/ixbrl.py`, `vss/esef.py`,
   `vss/pdfdraft.py`, `vss/manual.py`, `vss/history.py`, `vss/nordic.py`,
   `tools/fetch_mfn.py`, `vss/quotecheck.py`, `tools/cross_verify.py`,
   `sources/manifest.json`. Skalor (tusental/miljoner), tecken,
   perioder, valutor, IFRS mot US GAAP (leasing!), vad som räknas som
   "verifierat" (E21, E40, E131, E149, E151) -- kan något overifierat glida in
   i en värdering eller ranking?
2. **Värderingen** -- `vss/valuation.py`, `vss/rules.py`, `vss/strike.py`,
   `vss/prepare.py`, `vss/runrecord.py`. Kassaflödet (E140/E140.1),
   tillväxten (E144, taket), förvärv (E142), cykler (E143), nettoskuld
   (E14, E117, E146), aktieantal, diskonteringsränta och slutvärde.
   Dubbelräkning? Saknas något (t.ex. hyra under IFRS 16, minoriteter,
   utspädning, källskatt)? Räkna om fv för minst tre riktiga namn i
   `config/manual/` för hand och jämför med verktyget.
3. **Reglerna** -- `reference/FRAMEWORK.md` och de 150+ besluten i
   `reference/FRAMEWORK-EDITS.md`. Motsäger de varandra? Har de blivit så
   många att metoden anpassats i efterhand till enskilda bolag? Vilka beslut
   flyttade ett utfall åt rätt håll för ett bolag som redan ägdes eller
   övervägdes? Är "E141 -- sessionen beslutar" en risk?
4. **Grindar, köpregel, stopp och storlek** -- `docs/manual/`,
   `tools/playbook/`, `config/watchlist.yaml`, `vss/queue.py`,
   `vss/watch.py`. MBP, nivåer, stopp, positionsstorlek. Stämmer reglerna
   med vad backtesten säger om stopp och köpregeln?
5. **Screenern** -- `vss/screen.py`, `vss/ranking.py`, `vss/filters.py`,
   `vss/sec_pit.py`, `tools/nordic_screen.py`. Framåtblick, överlevnadsfel,
   valuta, rankingnyckeln (E6/E43): är den testad?
6. **Backtesten** -- `tools/backtest/` (pit, method, run, measure,
   eodhd_reprice, nordic, confirm_nordic) och `reference/backtest/`.
   Point-in-time på riktigt? Avnoterade med? Felkurser och återanvända
   tickers (ett känt fall i den privata datan: ett bolag som bytte ticker
   gav en orimlig avkastning och klarade ändå floatkontrollen)? Jämförelseindex
   rätt (totalavkastning)? Försöksloggen, förregistreringen och resultaten
   från de EODHD-baserade testen är PRIVATA (licensen) och finns inte här --
   granska koden och de slutsatser README beskriver i ord, och säg vad som
   inte går att pröva utan datan.
7. **Kodkvalitet** -- tester som bara låser in dagens tal i stället för att
   pröva logiken; tysta `except`; fail-closed eller inte; timers och vad som
   händer när en körning misslyckas; säkerhet (nycklar, `~/.config`).
8. **Det som saknas helt** -- kostnader, skatt i ISK (källskatt), valuta,
   likviditet, koncentration, beteenderisker, hur ett köp faktiskt följs upp.

Ta en del i taget och skriv in fynden allteftersom, så att inget går
förlorat om sessionen blir lång.

## Regler för arbetet

- **Ändra ingenting** i kod, konfiguration, watchlist, regler eller data.
  Du får skapa filer i scratchpad och din rapport, inget annat. Inga commits
  utom rapporten (fråga ägaren först).
- **Följ CLAUDE.md** (läs filer med offset/limit, begränsa utdata vid kända
  uppslag men läs HELA utdata när du jagar fel). Underagenter: högst 2-3,
  Sonnet på medium eller lägre, bara för att hämta och läsa -- bedömningen
  gör du själv.
- **EODHD-data finns inte i den här publika kopian** (privat licens). De
  verktyg som behöver den (`tools/fetch_eodhd.py`, `tools/backtest/nordic.py`,
  `tools/nordic_screen.py`) granskas som kod; hämta inte EODHD-data med någon
  annans nyckel.
- Testsviten: `.venv/bin/python -m pytest -q` (cirka 4 minuter). `vss
  doctor` för miljön.
- Om något är oklart enligt reglerna eller kräver ägarens omdöme: skriv det
  som en fråga i rapporten, gissa inte.

## Leverans

Skriv `reference/reviews/method/<dagens datum>-OBEROENDE-GRANSKNING.md`
(den publika kopian -- inga personuppgifter, inga kontonummer):

1. **Sammanfattning** (högst 15 rader): går det att lita på att verktyget
   tar fram köpvärda aktier? De tre allvarligaste fynden.
2. **Fynd**, sorterade efter allvar (KRITISK / HÖG / MEDEL / LÅG). För varje
   fynd: vad, var (`fil:rad`), bevis (körning, uträkning eller citat), vad
   det kan leda till i ett köpbeslut, och förslag på åtgärd.
3. **Det som är bra**, och varför.
4. **Det som inte gick att avgöra**, och vad som skulle behövas.
5. **Tidigare granskningar** (läses sist): vad som är löst, olöst, missat.

Visa ägaren sammanfattningen och de tre allvarligaste fynden i chatten när
du är klar. Föreslå inga ändringar som redan genomförda -- ägaren väljer
vad som görs.
