"""One-off: seed `screen_rankings` from the stored 2026-08-29 ranking CSV.

E93's change detection needs a PREVIOUS run to diff against, and the table
was introduced after that run was made. Without this the first scheduled
Saturday reports "first stored run, nothing to compare" and tells the owner
nothing -- so the run that already exists on disk is entered as the baseline.

WHAT THIS FILE ACTUALLY IS, stated because it is not what it looks like.
`data/screener_runs/2026-08-29/ranking.csv` is NOT the artifact the 2026-08-29
session wrote. That file was DESTROYED on 2026-08-31 by a smoke run of
`run_weekly` that isolated its snapshot root but not `runs_root`, so `rank()`
overwrote it with a six-ticker result (the bug is fixed, and
`test_the_weekly_run_isolates_runs_root` pins the fix). `data/` is gitignored,
so there was no copy to restore.

The price snapshot and the fundamentals store for that date SURVIVED intact,
so the ranking was REGENERATED from them -- and the regeneration is NOT the
original: it ranks 216 names where the original ranked 202, because commit
`d171724` changed filter 2's leverage limb AFTER that run (E63's columns in
the header are the other visible difference). The original's own top 20 is
quoted in the session record of 2026-08-31.

**And the regenerated ranking is nonetheless the RIGHT baseline**, which is
why it is seeded rather than abandoned: a diff is only meaningful when both
sides are computed the same way, and Saturday's run will use today's code.
Diffing today's code against a ranking made by older code would report the
CODE CHANGE as market movement -- exactly the phantom E93 exists to prevent.
Position is recomputed the way `ranking.py` orders -- ascending on the
combined rank, ties broken alphabetically -- because the CSV stores the rank
value and not the position, and E93 draws the top 10 on position.

Idempotent: refuses if 2026-08-29 is already in the table.
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vss.screenwatch import PROVENANCE_BACKFILL  # noqa: E402
from vss.store import persist_ranking, ranking_run_dates  # noqa: E402

AS_OF = "2026-08-29"
CSV_PATH = ROOT / "data" / "screener_runs" / AS_OF / "ranking.csv"
DB_PATH = ROOT / "data" / "vss.sqlite"


def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def main() -> int:
    if AS_OF in ranking_run_dates(DB_PATH):
        print(f"{AS_OF} is already in screen_rankings; nothing done.")
        return 0
    if not CSV_PATH.exists():
        print(f"missing {CSV_PATH}")
        return 1

    rows = list(csv.DictReader(CSV_PATH.open()))
    run_ts = datetime.fromtimestamp(CSV_PATH.stat().st_mtime).astimezone()
    common = {
        "run_ts": run_ts.isoformat(timespec="seconds"),
        "as_of": AS_OF,
        "snapshot_date": AS_OF,
        "coverage_short": 0,
        "fx_source": ("regenerated 2026-08-31 from the 2026-08-29 snapshot "
                      "under current code; NOT the original 08-29 artifact"),
        # Marks this ranking as seeded rather than run, which is what stops
        # the next scheduled run notifying on a diff against it.
        "provenance": PROVENANCE_BACKFILL,
    }

    out = []
    for section, key in (("ranked", "combined_rank"),
                         ("earnings_yield_only", "ey_rank")):
        members = [r for r in rows if r["section"] == section
                   and _int(r[key]) is not None]
        # ranking.py: ascending on the key, an equal key breaks alphabetically.
        members.sort(key=lambda r: (_int(r[key]), r["ticker"]))
        for position, row in enumerate(members, start=1):
            out.append({**common, "ticker": row["ticker"], "position": position,
                        "section": section,
                        "combined": _int(row["combined_rank"]),
                        "quality_rank": _int(row["quality_rank"]),
                        "ey_rank": _int(row["ey_rank"]),
                        "operating_profitability": _float(row["operating_profitability"]),
                        "earnings_yield": _float(row["earnings_yield"]),
                        "quality_state": row.get("quality_state")})

    ranked_count = sum(1 for r in out if r["section"] == "ranked")
    for row in out:
        row["ranked_count"] = ranked_count

    for section in ("unrankable", "stale"):
        for row in (r for r in rows if r["section"] == section):
            out.append({**common, "ticker": row["ticker"], "position": None,
                        "section": section, "combined": None,
                        "quality_rank": None, "ey_rank": None,
                        "operating_profitability": _float(row["operating_profitability"]),
                        "earnings_yield": _float(row["earnings_yield"]),
                        "quality_state": row.get("quality_state"),
                        "ranked_count": ranked_count})

    persist_ranking(DB_PATH, out)
    print(f"seeded {len(out)} rows for {AS_OF} ({ranked_count} ranked).")
    top = [r for r in out if r["section"] == "ranked" and r["position"] <= 10]
    print("top 10:", ", ".join(f"{r['position']}.{r['ticker']}" for r in top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
