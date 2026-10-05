"""The vendor's SECTOR and INDUSTRY strings, kept where pruning cannot reach.

**WHY THIS MODULE EXISTS** (CODE-REVIEW-2026-09-01, finding D3).

E51 and E96 remove a name from the universe at step 0 on one of two limbs:
the OWNER'S TICKER LIST, or the VENDOR'S INDUSTRY STRING.
`config/screener_commodity_price.yaml` carries `tickers: []`, so **E96 rests
on the string alone** — and until this module the string lived in exactly one
place: the `fundamentals_fields` table of
`data/screener_snapshots/<date>/fundamentals.sqlite`.

Two facts collided there:

* E93's `screenwatch.prune_snapshots(keep=4)` deletes those dated
  directories, fundamentals store included;
* E49's retention (`snapshot.write_fundamentals(retain_from=…)`) carries
  **series rows** between stores and **not fields**, so the string did not
  travel.

And a name the string limb excludes is never a filter-1 survivor, so its
fundamentals are never re-fetched and its string is never re-stored. It aged
out of the tree. Measured on 2026-09-01: **61 names were excluded by the
string alone**, and for eight of them (ANTO.L, KGH.WA, LUMI.ST, MRNA,
SCA-A.ST, SCA-B.ST, SNM-SDB.ST, UPM.HE) the last surviving copy of that
string was in the `2026-08-21` store, which the 2026-09-05 run prunes.

**THE ACCIDENT THAT WAS DOING THE WORK.** The ranked list was protected, but
not by design: `screen.fetch_fundamentals` runs filter 1, fetches, and writes
the store *before* `screen.rank` runs filter 1 a second time, and that second
pass reads the store just written. So a stringless excluded name passed step
0 once, was fetched, and was caught on the second pass. That repair does not
happen for a name outside filter 1's dislocation band (never fetched, so
never repaired), it does not happen if the fetch is THROTTLED, and it does
not happen at all for the nightly `pricewatch.industry_strings`, which runs
off the stored ranking between weekly runs. **The accident must not be the
mechanism**, so it no longer is: every string this project has ever observed
is written here, and step 0 reads here first.

**WHAT THIS IS NOT.** It is not a ruling and it changes no verdict. The
vendor still classifies; E51 and E96 still decide; the owner's lists are
still checked first and are still not exemptible. All that changes is that
the evidence outlives a disk-space policy.

**WHERE IT LIVES.** `data/vss.sqlite` — the database that is never pruned and
already holds `screen_rankings` on the same promise. NOT `config/`: the
scheduled units mount `config/` read-only on purpose (E92), and an automated
write into tracked configuration is the one thing that ruling forbids.

**REPLAY.** `first_seen` is what makes a replay honest. `read(before=…)`
returns the newest classification whose `first_seen` is on or before that
date, which is exactly what scanning the dated stores used to do — E49's
"a later-dated store is never read backwards", applied to this table.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "vss.sqlite"

#: Where a string came from, for the report line that names the source.
SOURCE_TABLE = "vendor_strings"
SOURCE_STORES = "snapshot stores"


_UPSERT = """
INSERT INTO vendor_strings (ticker, sector, industry, first_seen, last_seen)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(ticker, sector, industry) DO UPDATE SET
    first_seen = MIN(vendor_strings.first_seen, excluded.first_seen),
    last_seen  = MAX(vendor_strings.last_seen,  excluded.last_seen)
"""


def _clean(value: str | None) -> str:
    return (value or "").strip()


def record(db_path: Path, strings: Mapping[str, tuple[str | None, str | None]],
           *, observed: date) -> int:
    """Write one fetch's strings. Returns how many rows were offered.

    ``strings`` is `{ticker: (sector, industry)}` as
    `snapshot.read_sector_strings` returns it. A ticker with neither string
    is skipped: an absent classification is a fact about the fetch and there
    is nothing to remember about it.

    Idempotent. Re-recording a classification already held only widens its
    ``last_seen``; it never moves ``first_seen`` forward, because the whole
    value of that column is that it says when the string was FIRST true.
    """
    from .store import connect

    stamp = observed.isoformat()
    rows = []
    for ticker, pair in strings.items():
        sector, industry = (pair if isinstance(pair, (tuple, list))
                            else (None, pair))
        sector, industry = _clean(sector), _clean(industry)
        if not sector and not industry:
            continue
        rows.append((ticker, sector, industry, stamp, stamp))
    if not rows:
        return 0
    conn = connect(Path(db_path))
    try:
        with conn:
            conn.executemany(_UPSERT, rows)
    finally:
        conn.close()
    return len(rows)


def read(db_path: Path, *,
         before: date | None = None) -> dict[str, tuple[str | None, str | None]]:
    """`{ticker: (sector, industry)}` as known on or before ``before``.

    NEWEST WINS. Where the vendor has reclassified a company this returns the
    latest classification whose ``first_seen`` is within the window, which is
    the precedence `screen.filter1` has always applied (it built its map with
    `dict.update` over the stores in oldest-first order). ``before`` None
    takes everything, which is what a live nightly run wants.

    Returns {} when the table is empty or the database is not there. **That
    emptiness is a finding, not a fact about the companies** — every caller
    is expected to say so rather than to read it as "nothing is excluded";
    `summary` is what a caller reports it with.
    """
    path = Path(db_path)
    if not path.exists():
        return {}
    sql = ("SELECT ticker, sector, industry FROM vendor_strings "
           + ("WHERE first_seen <= ? " if before is not None else "")
           + "ORDER BY ticker, first_seen")
    params = [before.isoformat()] if before is not None else []
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error:
        return {}
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.Error:
        # A database written before this table existed. Not an error: the
        # caller's report says the table is empty and names the backfill.
        return {}
    finally:
        conn.close()
    out: dict[str, tuple[str | None, str | None]] = {}
    for ticker, sector, industry in rows:      # ordered, so the last one wins
        out[ticker] = (sector or None, industry or None)
    return out


def summary(db_path: Path) -> dict:
    """What the table holds, for the line a report prints about its source."""
    path = Path(db_path)
    empty = {"tickers": 0, "rows": 0, "first_seen": None, "last_seen": None}
    if not path.exists():
        return empty
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error:
        return empty
    try:
        row = conn.execute(
            "SELECT COUNT(DISTINCT ticker), COUNT(*), MIN(first_seen), "
            "MAX(last_seen) FROM vendor_strings").fetchone()
    except sqlite3.Error:
        return empty
    finally:
        conn.close()
    return {"tickers": row[0] or 0, "rows": row[1] or 0,
            "first_seen": row[2], "last_seen": row[3]}


def backfill_from_stores(db_path: Path, root: Path) -> dict:
    """Seed the table from every fundamentals store still on disk.

    OLDEST FIRST, each store recorded under ITS OWN DATE, so ``first_seen``
    comes out right rather than stamped with the day the backfill ran. Run
    once per machine; it is idempotent and re-running it changes nothing.

    Returns a small report: which stores were read, and what the table held
    before and after.
    """
    from . import snapshot as snapshot_store

    root = Path(root)
    before = summary(db_path)
    stores = snapshot_store.earlier_fundamentals_stores(
        root, before=date(9999, 12, 31))
    read_from: list[tuple[str, int]] = []
    for store in stores:
        try:
            day = date.fromisoformat(store.parent.name)
        except ValueError:                     # not a dated directory
            continue
        try:
            strings = snapshot_store.read_sector_strings(store)
        except Exception as exc:               # noqa: BLE001 -- one store never stops it
            log.warning("vendor strings: %s unreadable (%s)", store, exc)
            continue
        written = record(db_path, strings, observed=day)
        read_from.append((store.parent.name, written))
    return {"stores": read_from, "before": before, "after": summary(db_path)}


def describe(db_path: Path, *, backfill_hint: bool = True) -> list[str]:
    """The lines a report prints about where the string limb's input came from.

    THE DEPENDENCY, STATED RATHER THAN ASSUMED. E51's and E96's string limbs
    are only as good as this table, so a run says how big it is and how old.
    An EMPTY table is printed as a FINDING and names the command that fixes
    it -- because an empty one silently readmits every name the string limb
    is the only thing excluding.
    """
    counts = summary(db_path)
    if not counts["tickers"]:
        lines = ["  VENDOR STRINGS: the durable table is EMPTY. E51's and "
                 "E96's INDUSTRY limbs have no input, so only the owners'"]
        lines.append("                  ticker lists reach a name -- and E96's "
                     "is empty, so E96 is not being applied at all.")
        if backfill_hint:
            lines.append("                  Seed it: "
                         "`python -m vss backfill-vendor-strings`.")
        return lines
    return [f"  VENDOR STRINGS: {counts['tickers']} ticker(s), "
            f"{counts['rows']} classification(s), first seen "
            f"{counts['first_seen']}, last seen {counts['last_seen']}",
            "                  (data/vss.sqlite, which pruning never touches "
            "-- CODE-REVIEW-2026-09-01 D3)"]


def merge_with_stores(
    table: Mapping[str, tuple[str | None, str | None]],
    stores: Iterable[tuple[date, Mapping[str, tuple[str | None, str | None]]]],
) -> dict[str, tuple[str | None, str | None]]:
    """The durable table, with any store still on disk laid over it.

    Belt and braces, and deliberately kept: a machine whose `data/vss.sqlite`
    was replaced still gets whatever the surviving stores carry, and a fresh
    fetch's strings reach step 0 in the same run rather than the next one.
    Store order is oldest-first and NEWEST WINS, which is the precedence
    `filter1` has always used.
    """
    out = dict(table)
    for _day, strings in stores:
        for ticker, pair in strings.items():
            sector, industry = pair
            if sector or industry:
                out[ticker] = (sector, industry)
    return out
