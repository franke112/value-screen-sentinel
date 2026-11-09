# Shadow-book moves

`config/shadow_book.csv` measures what was NEVER bought (E114). Since
2026-11-08 (owner) the rule is per row: a row is valid only if its name was
not HELD on its `verdict_date` -- the date is after the last sale in the
entry's `sales:`, or before the first buy (`sales[].bought`). A row that
fails is moved out, never deleted. The rows themselves are kept verbatim in
`arkiv/2026-11-08-shadow-book-ogiltiga/rows.csv` (private, like all of
`arkiv/`); this file is the tracked record of why. The test
`tests/test_shadowbook.py::test_no_committed_row_falls_inside_a_holding_period`
holds the rule on every commit.

Source for every date below: Avanza transaktioner 2026-11-08
(konto/, private) and the entries' `sales:` blocks in config/watchlist.yaml.

## Moved

| Moved | Row (ticker, verdict_date, verdict) | Collision | Commit |
|---|---|---|---|
| 2026-11-08 | ACAD.ST, 2026-11-06, OVERRIDE | An owned name: HELD, 486 shares, on the verdict date and today. What it meant to measure -- what E157 would have given -- is a sale; it is now a counterfactual fill in ACAD.ST's `sales:` (`counterfactual: true`, overrides E157, 367 at 124.80 to Avanza Zero, commit 28cb285), which `vss sales` reports apart and never totals. The OVERRIDE verdict kind added for it was removed. | e57c648 |
| 2026-11-08 | HNSA.ST, 2026-08-21, DROPPED | HELD on its verdict date: first buy 2020-07-07, last sale 2026-08-21 -- the same day (9 + 31 at 40.64). The row itself said "EXIT -- B45 territory, and never a refusal". The exit is in `vss sales`. | 483bfa6 |
| 2026-11-08 | MSFT, 2026-08-21, DROPPED | HELD on its verdict date: first buy 2020-07-21, last fills 2026-08-21 -- the same day (4 + 1 at 482.43, C4). The exit is in `vss sales`. | 483bfa6 |
| 2026-11-08 | LIAB.ST, 2026-09-21, DROPPED | HELD on its verdict date: first buy 2026-07-17, the whole holding (121 at 120.70, C4) sold 2026-09-21 -- the same day. The exit is in `vss sales`. | 483bfa6 |

## Checked and kept

The other rows whose names have `sales:`, checked the same day (483bfa6):

| Row | Why it stands |
|---|---|
| NKE, 2026-08-25, DROPPED | After the last sale (2026-07-14). |
| UNA.AS, 2026-08-28, DROPPED | After the last sale (2026-08-24). |
| CRUS, 2026-09-08, DROPPED | Before the first buy (2026-09-10, recorded as `bought` on its fills). |
| SAP.DE, 2026-09-18, WATCH-GATED | After the last sale (2026-08-26). |
