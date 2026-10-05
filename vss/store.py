"""SQLite persistence of each run's metrics (SCOPE 7).

One row per ticker per run, so history can be reconstructed later. Nothing
reads this back yet -- it exists to accumulate.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS run_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_ts          TEXT    NOT NULL,
    as_of           TEXT    NOT NULL,
    ticker          TEXT    NOT NULL,
    name            TEXT,
    currency        TEXT,
    status          TEXT,
    source          TEXT,
    error           TEXT,
    last_close      REAL,
    last_close_date TEXT,
    -- 1 = the close had settled when the run read it, 0 = it had
    -- not, NULL = the run declared no settlement cutoff. A run
    -- made during the session sees a LIVE PRINT dated today and
    -- cannot tell it from a close by looking (report A 4.2).
    last_close_settled INTEGER,
    -- the newest bar DROPPED as a live print, where one was
    live_bar_date   TEXT,
    high_52w        REAL,
    drawdown        REAL,
    -- E63: the 52-week closing LOW, its session, and (close - low) / low.
    -- NULL together below the coverage bar. Reported, never applied.
    low_52w         REAL,
    low_52w_date    TEXT,
    pct_above_52w_low REAL,
    rsi14           REAL,
    sma50           REAL,
    sma200          REAL,
    pct_vs_sma50    REAL,
    pct_vs_sma200   REAL,
    avg_volume_20   REAL,
    volume_ratio    REAL,
    fv_base         REAL,
    tier            INTEGER,
    mbp             REAL,
    -- E32: mbp = fv_base * tier multiplier is SUPERSEDED as a definition.
    -- The flag travels with the number so a row read back later cannot be
    -- mistaken for a live buy price; `mbp_struck` is the entry's recorded
    -- date, or NULL where the row records none.
    mbp_superseded  INTEGER,
    mbp_struck      TEXT,
    stop_price      REAL,
    pct_to_mbp      REAL,
    pct_to_stop     REAL,
    blocked         INTEGER NOT NULL,
    blockers        TEXT,
    verdicts        TEXT,
    -- NULL for a full run; the ticker for a --ticker run, so a partial
    -- run is never mistaken for full coverage when reading history back.
    ticker_filter   TEXT,
    -- K4: series_sanity's finding for the price series, or NULL. When
    -- set, the stop/MBP/dislocation checks in `verdicts` are DATA MISSING
    -- because of it, and this column is the reason.
    series_finding  TEXT,
    -- item 9: why the entry's fv_base was NOT printed (no complete run
    -- record replays to it), or NULL. `fv_base` above is what was printed.
    fv_refused      TEXT
);
CREATE INDEX IF NOT EXISTS idx_run_metrics_ticker_ts ON run_metrics (ticker, run_ts);
CREATE INDEX IF NOT EXISTS idx_run_metrics_run_ts ON run_metrics (run_ts);

CREATE TABLE IF NOT EXISTS earnings_runs (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_ts               TEXT    NOT NULL,
    as_of                TEXT    NOT NULL,
    ticker               TEXT    NOT NULL,
    source_url           TEXT,
    model                TEXT,
    -- 1 = shadow: logged here, nothing sent. Recorded per row so history
    -- can never imply an alert went out when it did not.
    shadow               INTEGER NOT NULL,
    trips                TEXT,
    cannot_evaluate      TEXT,
    extraction_uncertain INTEGER NOT NULL,
    uncertainty_reasons  TEXT,
    error                TEXT,
    alert                TEXT,
    raw_response         TEXT
);
CREATE INDEX IF NOT EXISTS idx_earnings_ticker ON earnings_runs (ticker, run_ts);

-- E93: one row per RANKED NAME per screening run. This is the ONLY thing a
-- later run can diff against: `vss screen --rank` printed its report to
-- stdout and stored the ranked order nowhere, so before this table no
-- change could be detected at all.
--
-- It is deliberately small. The price snapshot beside it is ~235MB a run
-- and is pruned to the last four (E93); these rows are kilobytes and are
-- KEPT FOREVER, because they are what every future comparison stands on.
CREATE TABLE IF NOT EXISTS screen_rankings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_ts          TEXT    NOT NULL,
    -- the session the ranking was struck for, and the snapshot it read.
    as_of           TEXT    NOT NULL,
    snapshot_date   TEXT,
    ticker          TEXT    NOT NULL,
    -- POSITION in the ordered list, 1-based, and NULLABLE ON PURPOSE: an
    -- unrankable or stale name is stored WITHOUT one, so a later run can
    -- see that a name which HAD a position no longer has one. That is
    -- E93's data event, and it is how a feed or tag-map breakage shows up.
    -- E93 defines the top 10 on
    -- THIS and never on `combined`, which is a sum of two placings and
    -- ties freely: ranking.py breaks those ties alphabetically as a
    -- stated arbitrary rule, so position is reproducible and the top-10
    -- boundary does not move on sort instability.
    position        INTEGER,
    -- which list: `ranked` (both legs) or `earnings_yield_only` (E5(a),
    -- its own section and never interleaved).
    section         TEXT    NOT NULL,
    combined        INTEGER,
    quality_rank    INTEGER,
    ey_rank         INTEGER,
    operating_profitability REAL,
    earnings_yield  REAL,
    -- E93's data-event leg: a name ranked last week and unrankable or
    -- stale this week is reported. Those names carry a NULL position and
    -- their state here.
    quality_state   TEXT,
    -- 1 when the run's coverage was judged SHORT of the previous run's, so
    -- a row read back later says whether it belonged to a run that was
    -- allowed to send a pointer. E93: an incomplete run sends none.
    coverage_short  INTEGER,
    ranked_count    INTEGER,
    fx_source       TEXT,
    -- WHAT KIND OF RUN PRODUCED THIS ROW. `scheduled` = a real weekly run.
    -- Anything else -- `backfill`, or NULL for a row written before this
    -- column existed -- means the ranking was seeded from an artifact
    -- rather than produced by a run.
    --
    -- E93's change detection reads it: a diff is only worth notifying when
    -- BOTH sides are genuine runs. A baseline that was regenerated under
    -- code the original run never used would report the CODE CHANGE as
    -- market movement, which is the phantom E93 exists to prevent.
    provenance      TEXT,
    -- WHICH UNIVERSE THE RANKING WAS STRUCK ON: "A", "A,B", and so on.
    --
    -- THE SAME RULE AS `provenance`, GENERALISED. A run over 2,011 names
    -- and a run over 1,360 place their names against different fields, so
    -- every "entered the top 10" between them is the TIER CHANGE speaking
    -- and not the market -- the identical phantom, arriving through a third
    -- door. The 2026-09-05 widening to tier B is the case it was written
    -- for, and it is written as a rule so the next widening needs no one to
    -- remember anything.
    --
    -- NULL means the run recorded no tier set (a row written before this
    -- column existed). NULL is read as UNKNOWN and therefore NOT
    -- comparable, which is the safe direction: a baseline nobody can vouch
    -- for does not license a notification.
    tiers           TEXT
);
CREATE INDEX IF NOT EXISTS idx_screen_rankings_run ON screen_rankings (as_of, position);
CREATE INDEX IF NOT EXISTS idx_screen_rankings_ticker ON screen_rankings (ticker, as_of);

-- THE DEAD MAN'S SWITCH: one row per RUN, written by the run itself.
--
-- WHY THIS EXISTS. Before it, a nightly run that CRASHED and a nightly run
-- that had NOTHING TO SAY looked identical from the outside: no pointer
-- either way. `run_metrics` above does not close the gap -- it holds a row
-- per ticker per run, so a run that died halfway leaves rows that look like
-- a run, and a run that never started leaves nothing that says so.
--
-- This table records the RUN, not the tickers. A row is INSERTED when the
-- run starts, with `completed = 0`, and UPDATED to 1 when the run reaches
-- its end. So the three states are distinguishable and none of them is
-- inferred:
--
--   no row at all      -- the run never started (timer off, machine down,
--                         unit failed before Python)
--   completed = 0      -- it started and DIED before the end
--   completed = 1      -- it reached the end, and `covered`/`expected` say
--                         how much of the list it actually got
--
-- `scope` is NULL for a full run and the ticker for a `--ticker` run. The
-- staleness check reads only full, non-dry rows: a one-ticker run is not
-- "the nightly run happened", and must not reset the clock.
CREATE TABLE IF NOT EXISTS run_completions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    -- `nightly` (vss run) or `weekly` (vss screen --weekly).
    kind         TEXT    NOT NULL,
    started_at   TEXT    NOT NULL,
    -- NULL while the run is in flight AND for a run that died in flight.
    finished_at  TEXT,
    completed    INTEGER NOT NULL,
    as_of        TEXT    NOT NULL,
    -- NULL = full run; the ticker for a scoped one.
    scope        TEXT,
    dry_run      INTEGER NOT NULL,
    -- what the run set out to cover, and what it actually covered. For the
    -- nightly run: watchlist entries, and entries that got a price. For the
    -- weekly: names ranked last run, and names ranked this run.
    expected     INTEGER,
    covered      INTEGER,
    errors       INTEGER,
    detail       TEXT,
    -- 1 when the run REACHED ITS END but did not cover enough of what it set
    -- out to cover (CODE-REVIEW-2026-09-01 D2). A THIRD STATE, kept apart
    -- from the other two on purpose:
    --
    --   completed = 0             it started and DIED
    --   completed = 1, short = 1  it ran to the end and got almost nothing
    --   completed = 1, short = 0  it ran, and covered the list
    --
    -- Folding the middle one into either neighbour loses the distinction the
    -- switch exists to make. A short run does NOT reset the staleness clock:
    -- `last_completion` excludes it, so a week of runs that price nothing
    -- reads as a week without a run, which is what it is.
    short        INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_run_completions_kind
    ON run_completions (kind, completed, finished_at);

-- THE VENDOR'S SECTOR AND INDUSTRY STRINGS, KEPT WHERE PRUNING CANNOT REACH.
--
-- WHY THIS TABLE EXISTS (CODE-REVIEW-2026-09-01 D3). E51 and E96 remove a
-- name from the universe on one of two limbs: the owner's ticker list, or
-- the VENDOR'S INDUSTRY STRING. `config/screener_commodity_price.yaml` has
-- `tickers: []`, so E96 rests on the string alone -- and until this table
-- the string lived in exactly one place, the `fundamentals_fields` table of
-- `data/screener_snapshots/<date>/fundamentals.sqlite`.
--
-- Two facts then collided. E93's `prune_snapshots(keep=4)` deletes those
-- directories on a rolling basis, and E49's retention carries SERIES rows
-- between stores and NOT FIELDS -- so the string did not travel. An excluded
-- name is never a filter-1 survivor, so its fundamentals are never re-fetched
-- and its string is never re-stored: it simply aged out of the tree. Measured
-- on 2026-09-01: 61 names were excluded by the string alone, and for eight of
-- them the last surviving copy was in the 2026-08-21 store.
--
-- So the strings are written HERE, in the database that is never pruned and
-- already holds `screen_rankings` on the same promise. One row per DISTINCT
-- classification per ticker, not one per observation: a ticker the vendor
-- never reclassifies has exactly one row for ever.
--
-- `first_seen` is what makes a replay honest. A reader asks for the strings
-- known AT a date and gets the newest classification whose `first_seen` is on
-- or before it -- which is what scanning the dated stores used to do, and is
-- E49's "a later-dated store is never read backwards" applied to this table.
CREATE TABLE IF NOT EXISTS vendor_strings (
    ticker     TEXT NOT NULL,
    -- '' rather than NULL, so the primary key groups as one would expect:
    -- SQLite treats NULLs in a compound key as distinct from each other and
    -- would grow a fresh row on every observation.
    sector     TEXT NOT NULL DEFAULT '',
    industry   TEXT NOT NULL DEFAULT '',
    first_seen TEXT NOT NULL,
    last_seen  TEXT NOT NULL,
    PRIMARY KEY (ticker, sector, industry)
);
CREATE INDEX IF NOT EXISTS idx_vendor_strings_ticker
    ON vendor_strings (ticker, first_seen);
"""

COLUMNS = (
    "run_ts", "as_of", "ticker", "name", "currency", "status", "source", "error",
    "last_close", "last_close_date", "last_close_settled", "live_bar_date",
    "high_52w", "drawdown", "low_52w", "low_52w_date", "pct_above_52w_low",
    "rsi14", "sma50", "sma200", "pct_vs_sma50", "pct_vs_sma200",
    "avg_volume_20", "volume_ratio",
    "fv_base", "tier", "mbp", "mbp_superseded", "mbp_struck",
    "stop_price", "pct_to_mbp", "pct_to_stop",
    "blocked", "blockers", "verdicts", "ticker_filter", "series_finding",
    "fv_refused",
)


RANKING_COLUMNS = (
    "run_ts", "as_of", "snapshot_date", "ticker", "position", "section",
    "combined", "quality_rank", "ey_rank", "operating_profitability",
    "earnings_yield", "quality_state", "coverage_short", "ranked_count",
    "fx_source", "provenance", "tiers",
)


EARNINGS_COLUMNS = (
    "run_ts", "as_of", "ticker", "source_url", "model", "shadow", "trips",
    "cannot_evaluate", "extraction_uncertain", "uncertainty_reasons", "error",
    "alert", "raw_response",
)


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after a database was first created."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(run_metrics)")}
    for column, ddl in (("ticker_filter", "TEXT"),
                        ("mbp_superseded", "INTEGER"),
                        ("mbp_struck", "TEXT"),
                        ("last_close_settled", "INTEGER"),
                        ("live_bar_date", "TEXT"),
                        ("series_finding", "TEXT"),
                        ("fv_refused", "TEXT"),
                        ("low_52w", "REAL"),
                        ("low_52w_date", "TEXT"),
                        ("pct_above_52w_low", "REAL")):
        if column not in existing:
            conn.execute(f"ALTER TABLE run_metrics ADD COLUMN {column} {ddl}")
            log.info("migrated run_metrics: added %s", column)
    _migrate_completions(conn)
    _migrate_rankings(conn)
    conn.commit()


def _migrate_completions(conn: sqlite3.Connection) -> None:
    """Add `short` to a `run_completions` written before D2's fix.

    DEFAULT 0, which reads every row already on file as "covered the list".
    That is the honest default: those runs were never judged on coverage,
    and calling them short after the fact would invent a finding.
    """
    info = list(conn.execute("PRAGMA table_info(run_completions)"))
    if info and "short" not in {row[1] for row in info}:
        conn.execute("ALTER TABLE run_completions "
                     "ADD COLUMN short INTEGER NOT NULL DEFAULT 0")
        log.info("migrated run_completions: added short")


def _migrate_rankings(conn: sqlite3.Connection) -> None:
    """Drop the NOT NULL that the first cut of `screen_rankings` put on
    `position`.

    An unrankable or stale name is stored WITHOUT a position -- that is how
    E93's data event is detected -- and the original DDL forbade it, so the
    first backfill failed on an IntegrityError. SQLite cannot alter a
    constraint in place, so the table is rebuilt and its rows copied.
    """
    info = list(conn.execute("PRAGMA table_info(screen_rankings)"))
    if not info:
        return
    if "tiers" not in {row[1] for row in info}:
        # Rows written before this column existed stay NULL, and NULL is
        # read as "the tier set is unknown" -- not comparable, the same
        # safe direction NULL provenance already takes.
        conn.execute("ALTER TABLE screen_rankings ADD COLUMN tiers TEXT")
        log.info("migrated screen_rankings: added tiers")
        info = list(conn.execute("PRAGMA table_info(screen_rankings)"))
    if "provenance" not in {row[1] for row in info}:
        # Rows written before this column existed stay NULL, and NULL is
        # read as "not a scheduled run" -- the safe direction: a baseline
        # nobody can vouch for does not license a notification.
        conn.execute("ALTER TABLE screen_rankings ADD COLUMN provenance TEXT")
        log.info("migrated screen_rankings: added provenance")
        info = list(conn.execute("PRAGMA table_info(screen_rankings)"))
    position = next((row for row in info if row[1] == "position"), None)
    if position is None or not position[3]:      # row[3] = notnull flag
        return
    log.info("migrating screen_rankings: position becomes nullable")
    columns = ", ".join(row[1] for row in info if row[1] != "id")
    conn.executescript(
        "ALTER TABLE screen_rankings RENAME TO screen_rankings_old;")
    conn.executescript(SCHEMA)
    conn.execute(f"INSERT INTO screen_rankings ({columns}) "
                 f"SELECT {columns} FROM screen_rankings_old")
    conn.executescript("DROP TABLE screen_rankings_old;")


def persist(db_path: Path, records: list[dict]) -> int:
    """Insert one row per ticker. Returns the number of rows written."""
    if not records:
        return 0
    placeholders = ", ".join("?" for _ in COLUMNS)
    sql = f"INSERT INTO run_metrics ({', '.join(COLUMNS)}) VALUES ({placeholders})"
    conn = connect(db_path)
    try:
        with conn:
            conn.executemany(sql, [tuple(r.get(c) for c in COLUMNS) for r in records])
    finally:
        conn.close()
    log.info("persisted %d rows to %s", len(records), db_path)
    return len(records)


def persist_ranking(db_path: Path, records: list[dict]) -> int:
    """Store one screening run's ranked order (E93). Returns rows written.

    APPEND ONLY. A run is never updated in place and an earlier run is never
    deleted: the whole point of the table is that a later run can ask what
    the order was, and a history that can be rewritten answers nothing.
    """
    if not records:
        return 0
    placeholders = ", ".join("?" for _ in RANKING_COLUMNS)
    sql = (f"INSERT INTO screen_rankings ({', '.join(RANKING_COLUMNS)}) "
           f"VALUES ({placeholders})")
    conn = connect(db_path)
    try:
        with conn:
            conn.executemany(
                sql, [tuple(r.get(c) for c in RANKING_COLUMNS) for r in records])
    finally:
        conn.close()
    log.info("persisted %d ranking rows to %s", len(records), db_path)
    return len(records)


def ranking_run_dates(db_path: Path) -> list[str]:
    """Every `as_of` that has a stored ranking, newest first."""
    if not Path(db_path).exists():
        return []
    conn = connect(db_path)
    try:
        return [row[0] for row in conn.execute(
            "SELECT DISTINCT as_of FROM screen_rankings ORDER BY as_of DESC")]
    finally:
        conn.close()


def read_ranking(db_path: Path, as_of: str | None = None) -> list[dict]:
    """One run's stored ranking, in position order.

    ``as_of`` None reads the NEWEST stored run. Returns [] where nothing is
    stored -- which is what the first run ever sees, and it is not an error:
    a first run has nothing to diff against and E93 says so.
    """
    dates = ranking_run_dates(db_path)
    if not dates:
        return []
    wanted = as_of or dates[0]
    conn = connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM screen_rankings WHERE as_of = ? "
            "ORDER BY CASE WHEN position IS NULL THEN 1 ELSE 0 END, position",
            (wanted,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def previous_ranking(db_path: Path, before: str) -> list[dict]:
    """The newest stored ranking struck STRICTLY BEFORE ``before``.

    Strictly, so that re-running a date does not diff a run against itself
    and report no change when the comparison never happened.
    """
    for candidate in ranking_run_dates(db_path):
        if candidate < before:
            return read_ranking(db_path, candidate)
    return []


def previous_mbps(db_path: Path, *, before: str | None = None) -> dict[str, float]:
    """The MBP each ticker carried on the newest FULL run before ``before``.

    E100 (2026-09-01) reads this to tell a crossing the PRICE caused from a
    crossing the DEFINITION caused: a close at or below tonight's MBP that
    is still ABOVE the MBP the previous run recorded means the line came to
    the price, not the price to the line.

    SCOPED RUNS ARE EXCLUDED (`ticker_filter IS NULL`). A `--ticker` run
    examined one name, and letting it stand as "the previous run" for the
    others would compare tonight against a night that never looked at them.

    Returns {} where nothing is stored -- which is what a first run sees,
    and E100 treats an absent comparator as "cannot tell", never as "the
    price did it".
    """
    if not Path(db_path).exists():
        return {}
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT MAX(run_ts) FROM run_metrics WHERE ticker_filter IS NULL"
            + (" AND run_ts < ?" if before else ""),
            (before,) if before else ()).fetchone()
        if row is None or row[0] is None:
            return {}
        rows = conn.execute(
            "SELECT ticker, mbp FROM run_metrics "
            "WHERE run_ts = ? AND mbp IS NOT NULL", (row[0],)).fetchall()
        return {ticker: float(mbp) for ticker, mbp in rows}
    finally:
        conn.close()


def persist_earnings(db_path: Path, record: dict) -> int:
    """Log one earnings run. Every decision is recorded, shadow or not."""
    placeholders = ", ".join("?" for _ in EARNINGS_COLUMNS)
    sql = (f"INSERT INTO earnings_runs ({', '.join(EARNINGS_COLUMNS)}) "
           f"VALUES ({placeholders})")
    conn = connect(db_path)
    try:
        with conn:
            conn.execute(sql, tuple(record.get(c) for c in EARNINGS_COLUMNS))
    finally:
        conn.close()
    log.info("logged earnings run for %s (shadow=%s)",
             record.get("ticker"), record.get("shadow"))
    return 1
