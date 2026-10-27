# Uppdrag: kontrollera metodombyggnaden (E142–E147) — kort, inte en ny jakt

*För en NY Opus-session i ~/stocks. Ägaren klistrar in: "Läs
reference/METHOD-CHECK-PROMPT-2026-10-27.md och gör det."*

Den förra sessionen granskade värderingsmetoden
(`reference/reviews/method/2026-10-27-REBUILD.md`, avsnitt 1–7) och byggde om
den (avsnitt 8, commits bb6e87c..44002e1). Du ska INTE leta nya fel i allt.
Du ska svara på fyra frågor, och sedan är du klar.

1. **Gör koden det reglerna säger?** Läs E142–E147 i
   `reference/FRAMEWORK-EDITS.md` och jämför med `vss/history.py`,
   `vss/valuation.py` (`deal_programme_value`, `roiic_fraction`,
   `growth_annuity`) och E142-delarna i `vss/runrecord.py`
   (`E142Params`, `e142_parts`, `_strike_unchecked`) och `vss/strike.py`
   (`apply_e142`). En avvikelse mellan text och kod är ett fynd.
2. **Räkna om tre namn för hand** från deras strike-dokument
   (`reference/<T>-STRIKE-2026-10-27-e142.md`) och historikfiler
   (`config/history/<T>.yaml`): CENTA, LIAB.ST och ULTA. Stämmer kedjan
   nivå → tillväxt → kärna → program → affärer → per aktie?
3. **Klarar värdena ankarna?** För varje namn i avsnitt 8:s tabell: ligger
   base långt från både g* och den förväntade avkastningen utan att
   dokumentet förklarar varför? Lista bara de som gör det.
4. **Historikfilerna:** kör `vss history --ticker X --check` på alla 25 och
   stickprova fem rader mot PDF:en med egna ögon (två svenska, en dansk, en
   brittisk, en amerikansk). Stämmer siffran och året?

**Regler.** Ändra ingenting i `config/`, watchlisten, FRAMEWORK-EDITS eller
`vss/`. Varje fynd har källa och nedbrytning. Ett bekräftat fel, hur litet
det än är, rättas av nästa session i värdet. Nya idéer som inte svarar på
frågorna 1–4 skrivs under "Utanför uppdraget" och följs inte. Underagenter
får hämta och läsa (Sonnet, högst medium), inte bedöma.

**Leverans:** `reference/reviews/method/2026-10-27-CHECK.md`, svar först
(fungerar ombyggnaden: ja/nej), sedan fynden per fråga. Commit när den är
skriven.
