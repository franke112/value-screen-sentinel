# CROX — section 5 strike, 2026-09-04

**Growth view registered 2026-09-04 by the owner, in his own words, BEFORE this ran (E28).** bear -1% / base 1% / bull 3%, from `reference/growth-views/CROX.md` and read off the watchlist entry (E109).

Basis `annual FY2025`, ending 2025-12-31. Rate 9.5% (7.0% core + 2.5% premium). Settled close 116.01 USD on 2026-09-03.

## The value

| | USD |
|---|---:|
| **fv_base** (g 1%) | **169.79** |
| E29 band, low (g 1% − 0.5pp) | 184.52 |
| E29 band, high (g 1% + 0.5pp) | 157.02 |
| FV_bear (g -1%) | 143.01 |
| FV_bull (g 3%) | 201.08 |

## What the price implies

- settled close **116.01 USD** on 2026-09-03
- **g\*, the growth the price implies at r 9.5%: -3.39%** — against the owner's registered base of 1%
- price vs fv_base: **-31.7%**
- price vs FV_bear: **-18.9%**
- price vs FV_bull: **-42.3%**

## The legs

- FCF0 **815,061,000 USD**
- net debt **1,483,495,000 USD**
- divisor **54,208,000** shares — weighted-average DILUTED count for annual FY2025, the same window as the flows (E38); `shares_point_in_time` 50,200,000 is on the file as a MEMO and is NOT the divisor (E38)

## NO MBP, and that is E111 and B22 rather than an omission

This name is **INTAKE**: read, not watched. It carries no tier, and `compute_mbp` is `fv_base` × the tier multiplier — so **no maximum buy price exists and none is written here.** What the MBP *would* be at each tier (E90's cushion on the BASE case) is printed so the owner sees the range before scoring; **none of them is the MBP.**

| tier | MBP would be |
|---|---:|
| 1 | 144.33 USD |
| 2 | 127.35 USD |
| 3 | 110.37 USD |

## The run record

`reference/run-records/CROX-2026-09-04.json` — every leg, every page, zero hand inputs.

