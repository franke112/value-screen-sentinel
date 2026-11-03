# Cybersecurity fund holdings (Placera 2026-11-02) -- machine fv, 2026-11-03

Source: placera.se/nyheter/hackarna-slar-till-har-ar-fonderna-som-ska-ge-skydd-2026-11-02
(owner asked). The names the article gives as the funds' large holdings, run
through `tools/backtest/method.py` (scratch `data/scratch/cyber_fv.py`), prices
11-03. Yahoo FCF and SBC (stock-based pay) as a check. **Not a strike.**

| Ticker | Price | Bear | Base | Bull | Price/base | Q1-Q4 | FCF - SBC yield |
|---|---:|---:|---:|---:|---:|---|---:|
| CRWD | 241.81 | -- | -- | -- | -- | no fv (M6: under three revenue years in the tags) | 0.1 % |
| S    | 23.16  | -- | neg | neg | -- | FCF mean negative | -3.1 % |
| RBRK | 114.67 | -- | neg | neg | -- | FCF mean negative | -0.4 % |
| VRNS | 48.75  | -- | neg | neg | -- | Q1, Q2, Q3 fail | 0.0 % |
| QLYS | 207.60 | 69.23 | 93.73 | 93.73 | 2.2x | all pass | 3.1 % |
| RPD  | 14.85  | 9.71 | 12.12 | 12.83 | 1.2x | Q2, Q4 fail | 2.6 % |
| AVGO | 322.23 | 33.32 | 57.62 | 57.62 | 5.6x | all pass | 1.3 % |
| CSCO | 101.61 | 1.65 | 16.53 | 38.08 | 6.1x | Q4 fails (Splunk at low ROIIC) | 2.2 % |

The pure cyber names earn little or nothing once stock-based pay is counted
as the cost it is: CrowdStrike's 1.24bn FCF is 1.1bn of SBC. Qualys is the
one real business at 2.2x base; Rapid7 is the cheapest and fails Q2/Q4.
Nothing to take in; a theme fund after +76-139 % is a bet on the theme, not
on value.
