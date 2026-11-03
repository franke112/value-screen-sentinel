# Verktygslådan — strategierna, 2026-10-29

Ägaren, 2026-10-29: verktyget ska hitta affärer på flera teorier, inte bara en.
Varje strategi är ett eget ben med samma fem delar, så att de kan jämföras och
så att ingen får pengar innan den har ett facit.

| Del | Fråga |
|---|---|
| **Trigger** | Vad gör att ett bolag tittas på? |
| **Sortering** | Vilka av dem är fel sort (hårda nej)? |
| **Värdering** | Vad är det värt, och var går köpgränsen? |
| **Ut** | När säljs det? |
| **Facit** | Vad säger bakåttestet, och vad säger skuggloggen? |

Status: `test` (bara bakåt) → `skugga` (körs dagligen, inga pengar) → `skarp`
(ägarens ord, en post i FRAMEWORK-EDITS).

## 1. Värde — skarp

- **Trigger:** screenern (`vss screen`), bandet 15–50 % från toppen.
- **Sortering:** ramverket (FRAMEWORK §3–4), dvs. grindar och hårda stopp.
- **Värdering:** motorn — E140 FCF0, E144 tillväxt, E145 Q1–Q5, MBP per nivå.
- **Ut:** C4 (över FV_bull), stopp, omprövning.
- **Facit:** `reference/backtest/RESULT-2026-10-29.md` — fv/kurs sorterade inte
  avkastningen 2016–2020 (bara överlevare); E145 och att undvika den dyraste
  femtedelen hjälpte.

## 2. Nyhetsfall — skugga från 2026-10-29

- **Trigger:** `vss newsdrop` varje vardag. Det fångar fall på minst 10 % på 5
  dagar mot index (S&P 500 och Stockholm). En tidig flagga sätts vid 5 % på en
  dag. Bolaget måste omsätta minst 50 m om dagen.
- **Sortering:** klass B är ett hårt nej (eget rapportbesked, bokföring,
  VD/CFO …). Den fina klassen A1–A3/C görs av en session, med kostnadstak
  ≥ 3×.
- **Värdering:** motorn. Q1–Q4 krävs. Köpgränsen är 0,80 × fv efter
  kostnadstaket.
- **Ut:** vid fv, efter 12 månader eller vid en ny B-händelse.
- **Storlek:** 3 % per innehav, 10 % totalt.
- **Facit:** `reference/news-drops/BACKTEST.md`.
  - Fall på rapportbesked fortsätter nedåt, så klass B har stöd.
  - Fall utan besked ger ingen kant i sig.
  - Hos Q1–Q4-bolag gav fall utan besked +7,5 i median på 12 månader (N 31).
- **Skuggloggen:** `data/newsdrop/log.jsonl`. Beslut efter sex månader
  (~2027-04-29).
- **Design:** `reference/NEWS-DROP-DESIGN-2026-10-29.md`.

## 3. Nyhetsmomentum (Micron-typen) — test, underkänt

- **Idé:** köp efter en uppgång på minst 10 % som bär eget besked.
- **Facit:** samma bakåttest. Inget stöd hos stora bolag (median −2,8 på 12
  månader), och uppgångar utan besked vänder.
- **Status:** uppgångarna loggas av `vss newsdrop`, men benet byggs inte.

## Nästa ben

Ett nytt ben skrivs först som en design med de fem delarna. Sedan
bakåttestas det om datan finns, och därefter körs det i skuggläge. Idéer som
ägaren har nämnt men som inte är prövade:

- lågkonjunkturskydd: vad föll minst 2020 och 2022?
- kvalitet utan priskrav.
