# Coverage prune, 2026-11-09 (sweep D15)

## How it was measured

Every timer's command was run once under coverage, with no messages sent:

- `vss doctor`
- `vss run --dry-run`
- `vss queue --dry-run --no-notify`
- `vss checkin --no-send`
- `vss watch --read --no-send`
- `vss newsdrop --no-notify`
- `vss overview`
- `vss sales --dry-run`
- `vss shadow --dry-run`
- `tools/fetch_mfn.py --queue --days 45 --dry-run`
- `tools/cross_verify.py --all`
- `tools/nordic_screen.py --no-refresh`
- `vss screen --weekly --tier A --tier B --dry-run --no-notify`

The full test suite ran under coverage too (3,060 passed). Every run
exited 0. `tools/backtest/` was left out, because round 3 is running
from it.

## What was removed

**`vss/` modules at 0 %: none.**

**Functions with zero hits and no reference anywhere** (8):

| File | Function |
|---|---|
| `vss/heartbeat.py` | `find_failure` |
| `vss/manual.py` | `section5_period`, `registered_view_tolerance`, `newest_annual`, `net_shares_for` |
| `vss/prices.py` | `by_status` |
| `vss/reference_figures.py` | `_figure_provenance` |
| `vss/runner.py` | `previous_push_failure` |

**`tools/` scripts at 0 %, run neither from the CLI nor from a test**
(26). They were dated one-offs whose results are already recorded in run
records, strike documents and rulings; the code stays in git history:

- the backfills: `backfill_ranking_2026_08_29`, `backfill_shadow_book_2026_09_08`;
- `e34_lease_options_2026_09_19`;
- `normalize_e140`, now native in the engine;
- the probes: `probe_cash_bias`, `probe_rank_distances`, `probe_ranking_fields`;
- the dated re-strikes: `restrike_*`;
- `seed_cache_from_db`;
- the dated strikes: `strike_*_2026_*`;
- `threshold_reachability`;
- `zero_fv_scratch`.

## Kept, although at 0 %

Each of these is in operational use:

- `build_universe`: rebuilds the universe;
- `fetch_eodhd`: the yearly April purchase;
- `rough_fv`: the queue's rough rows;
- `quotecheck`: E131's wrapper;
- `newsdrop/backtest`;
- `freeze_ranking_acceptance`: regenerates the test fixtures;
- `replay_e166`: the E166 records cite it.

There are 84 zero-hit functions in `vss/` in all. The 76 not removed are
referenced elsewhere: called on paths these runs did not take (errors,
rare data), or named in a test or a doc.
