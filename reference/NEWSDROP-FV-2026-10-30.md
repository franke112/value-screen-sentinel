# Newsdrop 2026-10-30 -- bear / base / bull for the names that fell

Owner asked on 2026-11-02 for fair value on every name in
`reports/NEWSDROP-2026-10-30.md`, so it need not be run again. Prices are the
10-30 close (Nokia: 11-02). **None is a buy; all trade over even the bull case.**

## The machine names (SEC us-gaap, tools/backtest/method.py)

Bear / base / bull = the method's growth cases (E144 derived growth or the M6
fallback, cap 4 %); bull is `derived_growth().bull` or base + 1pp. The scratch
script was `fv3.py` off `data/newsdrop/2026-10-30.json`.

| Ticker | Price | Bear | Base | Bull | Price / base | Q1-Q4 |
|---|---:|---:|---:|---:|---:|---|
| HPQ  | 28.78  | 8.82   | 22.67  | 25.09  | 1.27x | all pass |
| NTAP | 199.18 | 38.54  | 59.81  | 64.53  | 3.3x  | all pass |
| AMAT | 390.09 | 53.63  | 107.78 | 107.78 | 3.6x  | all pass |
| DELL | 424.30 | --     | 112.59 | 128.46 | 3.8x  | -- (shares from Yahoo, 315m; no dei cover shares) |
| KEYS | 307.20 | 16.48  | 48.51  | 48.51  | 6.3x  | all pass |
| MRVL | 196.40 | 9.64   | 21.50  | 21.50  | 9x    | Q1 fails |
| CIEN | 320.72 | -11.21 | 23.96  | 30.94  | 13x   | Q1, Q2, Q4 fail |
| PSKY | 6.91   | --     | --     | --     | --    | no fv: two years of OCF/capex since the merger (CIK 2041610, listed SKYD) |

- HPQ and DELL run on -3 % growth because their histories span a spin-off
  (HPE 2015, VMware 2021); at 0 % HPQ's base is about 27-28, still no discount.
- AI/semis: even at 8 % (the most the method ever lets through) AMAT is about
  150-160 against 390.
- SIVE.ST: no stable profit, fails the quality bar; not valued.

## NOKIA-SEK.ST -- by hand (IFRS 20-F filer, so the us-gaap machine cannot read it)

Sources: `sources/NOKIA-SEK.ST_2025-FY_annual-report-2025_*` (cash flow
statement p.201, FCF composition p.196) and
`sources/NOKIA-SEK.ST_2026-Q3_interim-report-q3-2026_2026-10-22_en_a0.pdf`.

| EURm | 2023 | 2024 | 2025 | Q1-Q3 2026 |
|---|---:|---:|---:|---:|
| Net cash from operations | 1 317 | 2 493 | 2 071 | 254 |
| Capex | (652) | (472) | (606) | (459) |
| **FCF** | **665** | **2 021** | **1 465** | **(205)** |
| Change in net working capital | (1 282) | (569) | (209) | |
| Share-based payments | 202 | 241 | 337 | |

- Net cash 2 584 (excl. leases), shares 5 658.9m (Q3, excl. treasury),
  EUR/SEK 10.933, price EUR 7.838 / SEK 85.68 (11-02).
- TTM FCF is about 0 (Q4'25 227 + Q1-Q3'26 -205). Nokia is investing
  an extra EUR 400m in working capital in 2026 and cutting restructuring cash
  of 800-900m; 2026 FCF guide = 35-55 % of comparable EBIT 2.1-2.6bn, i.e.
  about 0.7-1.4bn.
- Nokia's "change in NWC" carries the restructuring cash (charges are added
  back in adjustments), and restructuring recurs every year, so the ex-WC
  figure is generous.

fv per share (r 9.5 %, terminal 2.5 %), growth 0 / 4 / 8 %:

| FCF basis | FCF0 | 0 % | 4 % | 8 % |
|---|---:|---:|---:|---:|
| Cash FCF, mean 2023-25 | 1 384 | EUR 3.44 / SEK 37.6 | **EUR 4.62 / SEK 50.5** | EUR 6.27 / SEK 68.6 |
| Same minus SBC (~260) | 1 124 | SEK 31.5 | SEK 41.9 | SEK 56.7 |
| Ex-WC mean (generous) | 2 070 | SEK 53.7 | SEK 73.1 | SEK 100.2 |

**Bear 37.6 / base 50.5 / bull ~100 SEK against 85.68.** At 4 % growth the
price needs about EUR 2.45bn FCF every year; Nokia's best year was 2.0bn
(2024), and 2026 will be about half that. The market is paying for the AI/optical
story (Optical + IP guided +25-30 % in 2027, AI & Cloud sales +123 % in Q3).
Not a value buy; revisit only under about SEK 40 (0.80 x base) or if FCF
actually steps up to 2bn+ for consecutive years.
