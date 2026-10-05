# LOPE — section 5 strike, 2026-09-04

**Growth view registered 2026-09-04 by the owner, in his own words, BEFORE this ran (E28).** bear 2% / base 3% / bull 5%, from `reference/growth-views/LOPE.md` and read off the watchlist entry (E109).

Basis `annual FY2025`, ending 2025-12-31. Rate 9.5% (7.0% core + 2.5% premium). Settled close 152.45 USD on 2026-09-03.

## The value

| | USD |
|---|---:|
| **fv_base** (g 3%) | **131.43** |
| E29 band, low (g 3% − 0.5pp) | 141.62 |
| E29 band, high (g 3% + 0.5pp) | 122.60 |
| FV_bear (g 2%) | 122.09 |
| FV_bull (g 5%) | 152.40 |

## What the price implies

- settled close **152.45 USD** on 2026-09-03
- **g\*, the growth the price implies at r 9.5%: 5.00%** — against the owner's registered base of 3%
- price vs fv_base: **+16.0%**
- price vs FV_bear: **+24.9%**
- price vs FV_bull: **+0.0%**

## The legs

- FCF0 **242,120,000 USD**
- net cash **4,439,000 USD**
- divisor **28,024,000** shares — weighted-average DILUTED count for annual FY2025, the same window as the flows (E38); `shares_point_in_time` 27,393,000 is on the file as a MEMO and is NOT the divisor (E38)

## NO MBP, and that is E111 and B22 rather than an omission

This name is **INTAKE**: read, not watched. It carries no tier, and `compute_mbp` is `fv_base` × the tier multiplier — so **no maximum buy price exists and none is written here.** What the MBP *would* be at each tier (E90's cushion on the BASE case) is printed so the owner sees the range before scoring; **none of them is the MBP.**

| tier | MBP would be |
|---|---:|
| 1 | 111.71 USD |
| 2 | 98.57 USD |
| 3 | 85.43 USD |

## The run record

`reference/run-records/LOPE-2026-09-04.json` — every leg, every page, zero hand inputs.

