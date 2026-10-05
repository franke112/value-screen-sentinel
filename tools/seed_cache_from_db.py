"""E122: put back the closes the blind cache overwrite destroyed.

The database kept one close per ticker per night, so every close that was
ever the newest on a run survives there even where the cache no longer
carries it. This reads those, fills a blank close in place, adds a row the
cache has lost entirely, and MARKS both retained with the run date the
close was first recorded on (E122 e).

It writes through `fetch.write_cache`, which is a union -- nothing here can
remove a row. Run with --dry-run to see what it would do.
"""
from __future__ import annotations

import argparse
import math
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vss.fetch import Retained, read_cache, read_retained, write_cache, write_retained
from vss.runner import CACHE_DIR, DB_PATH


def held_from_db(db_path: Path) -> dict[str, dict[str, tuple[float, str]]]:
    c = sqlite3.connect(db_path)
    out: dict[str, dict[str, tuple[float, str]]] = {}
    for ticker, when, close, first in c.execute(
            """select ticker, last_close_date, last_close, min(as_of)
               from run_metrics
               where last_close_date is not null and last_close is not null
               group by ticker, last_close_date, last_close"""):
        out.setdefault(ticker, {})[when] = (float(close), first)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    ap.add_argument("--db", type=Path, default=DB_PATH)
    args = ap.parse_args()

    total = 0
    for ticker, rows in sorted(held_from_db(args.db).items()):
        frame, _ = read_cache(args.cache_dir, ticker)
        if frame is None:
            print(f"{ticker}: no cache file; skipped")
            continue
        have = {str(i.date()): n for n, i in enumerate(frame.index)}
        seed = frame.copy()
        marks = dict(read_retained(args.cache_dir, ticker))
        restored = []
        for when, (close, first) in sorted(rows.items()):
            if when in have:
                current = seed["Close"].iloc[have[when]]
                if current is None or (isinstance(current, float) and math.isnan(current)):
                    seed.iloc[have[when], seed.columns.get_loc("Close")] = close
                    restored.append((when, close, "blank close filled", first))
                continue
            row = {col: float("nan") for col in seed.columns}
            row["Close"] = close
            seed.loc[pd.Timestamp(when)] = row
            restored.append((when, close, "row restored", first))
        if not restored:
            continue
        seed = seed.sort_index()
        total += len(restored)
        print(f"\n{ticker}: {len(restored)} restored")
        for when, close, what, first in restored:
            print(f"    {when}  {close:>12,.4f}  {what} (first recorded {first})")
            marks[date.fromisoformat(when)] = Retained(
                date.fromisoformat(when), date.fromisoformat(first),
                date.today(), "db-seed")
        if not args.dry_run:
            write_cache(args.cache_dir, ticker, seed, datetime.now().astimezone())
            write_retained(args.cache_dir, ticker, marks)
    print(f"\n{'would restore' if args.dry_run else 'restored'}: {total} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
