"""Per-run snapshot storage, so any candidate list can be replayed exactly.

One sqlite file per run, under::

    data/screener_snapshots/<ASOF>/snapshot.sqlite

sqlite rather than parquet: it is in the standard library, it needs no new
dependency, and it holds the universe, the exclusions, the fetch statuses and
the raw prices in one file that can be opened with any client months later.

What is stored is RAW daily OHLCV, never computed metrics. A snapshot exists
so that a filter can be re-run against a past date and produce the same
answer -- which means the 52-week high, the moving averages and the RSI must
be recomputable AS OF an arbitrary date inside the window. Storing yesterday's
SMA200 would make the replay a lookup instead of a computation, and the first
time a metric definition changed the old snapshots would silently disagree
with the new code.

Reproducibility rests on three things recorded in the manifest:

  * ``asof`` and the truncation it implies -- no row in ``prices`` is dated
    after it;
  * the sha256 of every universe CSV that fed the run, so a later replay can
    prove it is reading the same lists;
  * the fetch parameters (period, auto_adjust, batch size), because a series
    fetched with dividend adjustment is a different series.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import pandas as pd

from . import __version__
from .metrics import index_dates
from .prices import TickerFetch
from .universe import Instrument, Merge, Rejection, SourceFile, Tally

#: Bumped whenever the table layout changes in a way a reader must notice.
SCHEMA_VERSION = 3

SNAPSHOT_ROOT = Path("data/screener_snapshots")
SNAPSHOT_FILENAME = "snapshot.sqlite"

DDL = """
CREATE TABLE IF NOT EXISTS manifest (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS source_files (
    file              TEXT PRIMARY KEY,
    sha256            TEXT NOT NULL,
    rows              INTEGER NOT NULL,
    tier_counts       TEXT,
    meta_sha_matches  INTEGER,
    approximation     INTEGER,
    meta              TEXT
);
CREATE TABLE IF NOT EXISTS universe (
    ticker_yahoo  TEXT,
    ticker_lokal  TEXT NOT NULL,
    isin          TEXT,
    namn          TEXT,
    marknad       TEXT NOT NULL,
    tier          TEXT NOT NULL,
    listdatum     TEXT,
    valuta        TEXT,
    instrumenttyp TEXT,
    source_file   TEXT,
    source_line   INTEGER
);
CREATE TABLE IF NOT EXISTS rejections (
    key    TEXT NOT NULL,
    step   TEXT NOT NULL,
    kind   TEXT NOT NULL,
    reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS merges (
    kept           TEXT NOT NULL,
    dropped        TEXT NOT NULL,
    on_field       TEXT NOT NULL,
    basis          TEXT NOT NULL,
    detail         TEXT,
    kept_source    TEXT,
    dropped_source TEXT
);
CREATE TABLE IF NOT EXISTS tallies (
    step                 TEXT PRIMARY KEY,
    count_in             INTEGER NOT NULL,
    count_out            INTEGER NOT NULL,
    rejected_on_value    INTEGER NOT NULL,
    rejected_on_missing  INTEGER NOT NULL,
    reasons              TEXT
);
CREATE TABLE IF NOT EXISTS fetch_status (
    ticker     TEXT PRIMARY KEY,
    status     TEXT NOT NULL,
    rows       INTEGER NOT NULL,
    first_date TEXT,
    last_date  TEXT,
    attempts   INTEGER NOT NULL,
    error      TEXT,
    batch      INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS prices (
    ticker TEXT NOT NULL,
    date   TEXT NOT NULL,
    open   REAL,
    high   REAL,
    low    REAL,
    close  REAL,
    volume REAL,
    PRIMARY KEY (ticker, date)
);
CREATE INDEX IF NOT EXISTS prices_by_date ON prices (date);
"""


def snapshot_path(as_of: date, root: Path = SNAPSHOT_ROOT) -> Path:
    return root / as_of.isoformat() / SNAPSHOT_FILENAME


def connect(path: Path, *, create: bool = True) -> sqlite3.Connection:
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    elif not path.exists():
        raise FileNotFoundError(f"{path}: no snapshot there")
    conn = sqlite3.connect(path)
    conn.executescript(DDL)
    return conn


def _rows_from_frame(ticker: str, frame: pd.DataFrame) -> list[tuple]:
    dates = index_dates(frame.index)
    columns = {name.lower(): name for name in frame.columns}

    def column(name: str):
        real = columns.get(name)
        return frame[real].to_numpy() if real is not None else [None] * len(frame)

    opens, highs, lows, closes, volumes = (
        column("open"), column("high"), column("low"), column("close"), column("volume")
    )

    def clean(value):
        if value is None or pd.isna(value):
            return None
        return float(value)

    return [
        (ticker, dates[i].isoformat(), clean(opens[i]), clean(highs[i]),
         clean(lows[i]), clean(closes[i]), clean(volumes[i]))
        for i in range(len(frame))
    ]


def write(
    path: Path,
    *,
    as_of: date,
    created_at: datetime,
    instruments: Sequence[Instrument],
    tallies: Sequence[Tally],
    rejections: Sequence[Rejection],
    merges: Sequence[Merge],
    files: Sequence[SourceFile],
    statuses: Sequence[TickerFetch],
    frames: Mapping[str, pd.DataFrame],
    extra_manifest: Mapping[str, object] | None = None,
) -> Path:
    """Write one complete snapshot. Overwrites an existing file for the date."""
    if path.exists():
        path.unlink()
    conn = connect(path)
    try:
        with conn:
            conn.executemany(
                "INSERT INTO universe VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        i.ticker_yahoo, i.ticker_lokal, i.isin, i.namn, i.marknad,
                        i.tier, i.listdatum.isoformat() if i.listdatum else None,
                        i.valuta, i.instrumenttyp, i.source_file, i.source_line,
                    )
                    for i in instruments
                ],
            )
            conn.executemany(
                "INSERT INTO rejections VALUES (?,?,?,?)",
                [(r.key, r.step, r.kind, r.reason) for r in rejections],
            )
            conn.executemany(
                "INSERT INTO merges VALUES (?,?,?,?,?,?,?)",
                [(m.kept, m.dropped, m.on, m.basis, m.detail,
                  m.kept_source, m.dropped_source) for m in merges],
            )
            conn.executemany(
                "INSERT INTO tallies VALUES (?,?,?,?,?,?)",
                [
                    (t.step, t.count_in, t.count_out, t.rejected_on_value,
                     t.rejected_on_missing, json.dumps(dict(t.reasons)))
                    for t in tallies
                ],
            )
            conn.executemany(
                "INSERT INTO source_files VALUES (?,?,?,?,?,?,?)",
                [
                    (
                        f.path.name, f.sha256, f.rows, json.dumps(dict(f.tier_counts)),
                        None if f.meta_sha_matches is None else int(f.meta_sha_matches),
                        int(bool((f.meta or {}).get("approximation"))),
                        json.dumps(f.meta, ensure_ascii=False) if f.meta else None,
                    )
                    for f in files
                ],
            )
            conn.executemany(
                "INSERT INTO fetch_status VALUES (?,?,?,?,?,?,?,?)",
                [
                    (
                        s.ticker, s.status, s.rows,
                        s.first_date.isoformat() if s.first_date else None,
                        s.last_date.isoformat() if s.last_date else None,
                        s.attempts, s.error, s.batch,
                    )
                    for s in statuses
                ],
            )
            price_rows: list[tuple] = []
            for ticker, frame in frames.items():
                price_rows.extend(_rows_from_frame(ticker, frame))
            conn.executemany(
                "INSERT OR REPLACE INTO prices VALUES (?,?,?,?,?,?,?)", price_rows
            )

            manifest = {
                "schema_version": SCHEMA_VERSION,
                "vss_version": __version__,
                "asof": as_of.isoformat(),
                "created_at": created_at.isoformat(timespec="seconds"),
                "instruments": len(instruments),
                "price_rows": len(price_rows),
                "tickers_with_prices": len(frames),
                "universe_files": json.dumps(
                    {f.path.name: f.sha256 for f in files}, sort_keys=True
                ),
                "max_price_date": max(
                    (row[1] for row in price_rows), default=""
                ),
            }
            manifest.update(dict(extra_manifest or {}))
            conn.executemany(
                "INSERT OR REPLACE INTO manifest VALUES (?,?)",
                [(k, json.dumps(v) if not isinstance(v, str) else v)
                 for k, v in manifest.items()],
            )
    finally:
        conn.close()
    return path


def read_manifest(path: Path) -> dict[str, str]:
    conn = connect(path, create=False)
    try:
        return dict(conn.execute("SELECT key, value FROM manifest").fetchall())
    finally:
        conn.close()


def read_prices(path: Path, ticker: str) -> pd.DataFrame:
    """Rebuild one ticker's OHLCV frame, indexed by date, ready for
    ``metrics.compute``."""
    conn = connect(path, create=False)
    try:
        rows = conn.execute(
            "SELECT date, open, high, low, close, volume FROM prices "
            "WHERE ticker = ? ORDER BY date",
            (ticker,),
        ).fetchall()
    finally:
        conn.close()
    frame = pd.DataFrame(
        rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"]
    )
    frame["Date"] = pd.to_datetime(frame["Date"])
    return frame.set_index("Date")


def read_all_prices(path: Path, tickers: Sequence[str] | None = None) -> dict[str, pd.DataFrame]:
    """Every stored series at once, as frames ready for ``metrics.compute``.

    One query and one group-by rather than a query per ticker: filter 1 reads
    the whole universe, and 1,370 round trips to sqlite to rebuild frames one
    at a time is time spent for nothing.
    """
    conn = connect(path, create=False)
    try:
        rows = conn.execute(
            "SELECT ticker, date, open, high, low, close, volume FROM prices "
            "ORDER BY ticker, date"
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return {}
    frame = pd.DataFrame(
        rows, columns=["Ticker", "Date", "Open", "High", "Low", "Close", "Volume"]
    )
    if tickers is not None:
        frame = frame[frame["Ticker"].isin(set(tickers))]
    frame["Date"] = pd.to_datetime(frame["Date"])
    out: dict[str, pd.DataFrame] = {}
    for ticker, part in frame.groupby("Ticker", sort=False):
        out[str(ticker)] = part.drop(columns=["Ticker"]).set_index("Date")
    return out


def available_snapshots(root: Path = SNAPSHOT_ROOT) -> list[date]:
    """Snapshot dates present on disk, oldest first."""
    if not root.is_dir():
        return []
    found = []
    for child in root.iterdir():
        if not (child / SNAPSHOT_FILENAME).exists():
            continue
        try:
            found.append(date.fromisoformat(child.name))
        except ValueError:
            continue
    return sorted(found)


def read_fetch_status(path: Path) -> list[TickerFetch]:
    conn = connect(path, create=False)
    try:
        rows = conn.execute(
            "SELECT ticker, status, rows, first_date, last_date, attempts, error, "
            "batch FROM fetch_status ORDER BY ticker"
        ).fetchall()
    finally:
        conn.close()
    return [
        TickerFetch(
            ticker=r[0], status=r[1], rows=r[2],
            first_date=date.fromisoformat(r[3]) if r[3] else None,
            last_date=date.fromisoformat(r[4]) if r[4] else None,
            attempts=r[5], error=r[6], batch=r[7],
        )
        for r in rows
    ]


def verify(path: Path, universe_dir: Path) -> list[str]:
    """Problems that would make this snapshot a dishonest replay.

    An empty list means: the universe files on disk still hash to what the
    run recorded, and no stored close is dated after the snapshot's asof.
    """
    problems: list[str] = []
    manifest = read_manifest(path)
    as_of = manifest.get("asof", "")
    recorded = json.loads(manifest.get("universe_files", "{}"))

    import hashlib

    for name, digest in sorted(recorded.items()):
        candidate = universe_dir / name
        if not candidate.exists():
            problems.append(f"{name}: recorded in the snapshot but missing from disk")
            continue
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != digest:
            problems.append(
                f"{name}: sha256 on disk {actual[:12]} != recorded {digest[:12]}"
            )

    conn = connect(path, create=False)
    try:
        newest = conn.execute("SELECT MAX(date) FROM prices").fetchone()[0]
    finally:
        conn.close()
    if newest and as_of and newest > as_of:
        problems.append(f"prices hold {newest}, which is after asof {as_of}")
    return problems


def snapshot_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


# --- fundamentals ----------------------------------------------------------

FUNDAMENTALS_FILENAME = "fundamentals.sqlite"

#: Fundamentals live in their OWN file beside the price snapshot, not inside
#: it. The price snapshot is the reproducibility artefact -- ``verify``
#: hashes against it and every stored close is dated at or before its asof --
#: and appending a second, later-dated fetch into that file would make it
#: describe two moments at once. The directory is shared; the guarantee is
#: not.
#:
#: THE STORE RETAINS (FRAMEWORK-EDITS E49, 2026-08-27). A write never unlinks
#: the file. ``fundamentals_status`` and ``fundamentals_fields`` are one row
#: per ticker and describe THE FETCH THAT WROTE THEM. ``fundamentals_series``
#: is the UNION of every period ever fetched for the ticker, each row stamped
#: with the fetch that supplied it: a re-fetch replaces the periods it
#: returns and leaves the rest; a returned hole (NULL) never overwrites a
#: figure; and between two figures for one key the NEWER fetch wins, in
#: whatever order the two were written. A new date's store is seeded from
#: every earlier-dated store under the root, so E45's eight-quarter window
#: fills over time from a vendor that serves five. A ticker whose periods
#: were carried in but which THIS store's fetch never visited has series
#: rows and no status row; ``read_fundamentals`` returns status rows only,
#: so such a ticker is invisible to the chain until a fetch visits it, and
#: ``fundamentals_store_summary`` counts it so the report can say so.
FUNDAMENTALS_DDL = """
CREATE TABLE IF NOT EXISTS manifest (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS fundamentals_status (
    ticker        TEXT PRIMARY KEY,
    status        TEXT NOT NULL,
    attempts      INTEGER NOT NULL,
    requests      INTEGER NOT NULL,
    error         TEXT,
    newest_period TEXT,
    -- E49: the fetch that wrote this row. A ticker fetched on two dates
    -- carries the later one here; its earlier periods stay in the series.
    fetched_at    TEXT
);
CREATE TABLE IF NOT EXISTS fundamentals_fields (
    ticker TEXT NOT NULL,
    name   TEXT NOT NULL,
    status TEXT NOT NULL,
    number REAL,
    text   TEXT,
    PRIMARY KEY (ticker, name)
);
CREATE TABLE IF NOT EXISTS fundamentals_series (
    ticker     TEXT NOT NULL,
    statement  TEXT NOT NULL,
    line       TEXT NOT NULL,
    period_end TEXT NOT NULL,
    value      REAL,
    -- How long a period a FLOW line covers, in months. NULL on a stock
    -- line, where it does not apply. A file written before this column
    -- existed has NULL on its income rows, which the first write into it
    -- backfills to the vendor's twelve: the vendor path was the only thing
    -- that wrote them and its income statement IS the annual one.
    period_months INTEGER,
    -- E49: the fetch that supplied THIS row. NULL only in a file written
    -- before the column existed, and backfilled from that file's manifest
    -- on the first write into it -- that one fetch is the provenance of
    -- every row such a file holds.
    fetched_at TEXT,
    PRIMARY KEY (ticker, statement, line, period_end)
);
"""

#: The series upsert (E49). A period this fetch returns replaces the stored
#: one and a period it does not return stays; a hole never overwrites a
#: figure; between two figures the newer fetch wins whatever the write
#: order. ISO-8601 stamps compare as text.
SERIES_UPSERT = """
INSERT INTO fundamentals_series
    (ticker, statement, line, period_end, value, period_months, fetched_at)
VALUES (?,?,?,?,?,?,?)
ON CONFLICT(ticker, statement, line, period_end) DO UPDATE SET
    value = excluded.value,
    period_months = excluded.period_months,
    fetched_at = excluded.fetched_at
WHERE excluded.value IS NOT NULL
  AND (fundamentals_series.value IS NULL
       OR fundamentals_series.fetched_at IS NULL
       OR excluded.fetched_at >= fundamentals_series.fetched_at)
"""


def fundamentals_path(as_of: date, root: Path = SNAPSHOT_ROOT) -> Path:
    return root / as_of.isoformat() / FUNDAMENTALS_FILENAME


def earlier_fundamentals_stores(root: Path = SNAPSHOT_ROOT, *, before: date) -> list[Path]:
    """The canonical stores under ``root`` dated strictly BEFORE ``before``,
    oldest first -- what a new date's store is seeded from (E49).

    A later-dated store is never read backwards: a period it holds may
    have been reported after the run date, and a replay of an old date
    must not see it. Only ``fundamentals.sqlite`` counts; a copy saved
    beside it under another name is a record, not a store.
    """
    if not root.is_dir():
        return []
    found: list[tuple[date, Path]] = []
    for child in root.iterdir():
        path = child / FUNDAMENTALS_FILENAME
        if not path.exists():
            continue
        try:
            day = date.fromisoformat(child.name)
        except ValueError:
            continue
        if day < before:
            found.append((day, path))
    return [path for _, path in sorted(found)]


def connect_fundamentals(path: Path, *, create: bool = True) -> sqlite3.Connection:
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    elif not path.exists():
        raise FileNotFoundError(f"{path}: no fundamentals store there")
    conn = sqlite3.connect(path)
    conn.executescript(FUNDAMENTALS_DDL)
    return conn


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _manifest_of(conn: sqlite3.Connection) -> dict[str, str]:
    return dict(conn.execute("SELECT key, value FROM manifest").fetchall())


def _migrate_fundamentals(conn: sqlite3.Connection) -> None:
    """Bring a store written before E49 (or before ``period_months``) up to
    the current layout, in place, on the first WRITE into it. Reads never
    alter a file. A row without a fetch stamp gets the file's manifest
    fetch -- every row a pre-E49 file holds came from that one fetch -- and
    an income row without a length gets the vendor's twelve, for the reason
    ``read_fundamentals`` already applied to it."""
    from .fundamentals import ANNUAL_MONTHS

    stamp = _manifest_of(conn).get("fetched_at")
    if "period_months" not in _columns(conn, "fundamentals_series"):
        conn.execute("ALTER TABLE fundamentals_series ADD COLUMN period_months INTEGER")
    for table in ("fundamentals_status", "fundamentals_series"):
        if "fetched_at" not in _columns(conn, table):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN fetched_at TEXT")
    conn.execute(
        "UPDATE fundamentals_series SET period_months = ? "
        "WHERE period_months IS NULL AND statement = 'income'",
        (ANNUAL_MONTHS,),
    )
    if stamp:
        for table in ("fundamentals_status", "fundamentals_series"):
            conn.execute(f"UPDATE {table} SET fetched_at = ? WHERE fetched_at IS NULL",
                         (stamp,))


def read_series_rows(path: Path) -> list[tuple]:
    """Every series row of a store, as the tuple ``SERIES_UPSERT`` takes,
    with the file's manifest fetch standing in where a row carries no stamp
    and twelve months standing in on an unlengthed income row. What one
    store carries into another (E49). Does not alter the file."""
    from .fundamentals import ANNUAL_MONTHS

    conn = connect_fundamentals(path, create=False)
    try:
        columns = _columns(conn, "fundamentals_series")
        stamp = _manifest_of(conn).get("fetched_at")
        rows = conn.execute(
            "SELECT ticker, statement, line, period_end, value, "
            + ("period_months" if "period_months" in columns else "NULL")
            + ", " + ("fetched_at" if "fetched_at" in columns else "NULL")
            + " FROM fundamentals_series"
        ).fetchall()
    finally:
        conn.close()
    out = []
    for ticker, statement, line, period_end, value, months, fetched in rows:
        if months is None and statement == "income":
            months = ANNUAL_MONTHS
        out.append((ticker, statement, line, period_end, value, months, fetched or stamp))
    return out


def write_fundamentals(
    path: Path,
    *,
    as_of: date,
    fetched_at: datetime,
    records: Sequence,
    requests: int,
    extra_manifest: Mapping[str, object] | None = None,
    retain_from: Sequence[Path] = (),
) -> Path:
    """Write one fetch INTO the store at ``path``. Never unlinks it (E49).

    Status and fields are replaced per ticker -- they describe this fetch.
    Series rows are upserted under ``SERIES_UPSERT``'s rule, stamped with
    ``fetched_at``. ``retain_from`` names earlier stores whose series are
    carried in FIRST, under the same rule, so the newest figure wins per
    key regardless of order. The manifest records this fetch as the latest,
    keeps the first, and appends to a ``fetches`` history.
    """
    stamp = fetched_at.isoformat(timespec="seconds")
    carried: list[tuple] = []
    for earlier in retain_from:
        earlier = Path(earlier)
        if earlier.resolve() == path.resolve():
            continue
        carried.extend(read_series_rows(earlier))

    conn = connect_fundamentals(path)
    try:
        with conn:
            _migrate_fundamentals(conn)
            if carried:
                conn.executemany(SERIES_UPSERT, carried)
            conn.executemany(
                "INSERT OR REPLACE INTO fundamentals_status VALUES (?,?,?,?,?,?,?)",
                [
                    (r.ticker, r.status, r.attempts, r.requests, r.error,
                     r.newest_period.isoformat() if r.newest_period else None,
                     stamp)
                    for r in records
                ],
            )
            conn.executemany(
                "INSERT OR REPLACE INTO fundamentals_fields VALUES (?,?,?,?,?)",
                [(f.ticker, f.name, f.status, f.number, f.text)
                 for r in records for f in r.fields],
            )
            conn.executemany(
                SERIES_UPSERT,
                [(p.ticker, p.statement, p.line, p.period_end.isoformat(),
                  p.value, p.period_months, stamp)
                 for r in records for p in r.series],
            )
            previous = _manifest_of(conn)
            try:
                fetches = json.loads(previous.get("fetches") or "[]")
            except ValueError:
                fetches = []
            if not fetches and previous.get("fetched_at"):
                # A pre-E49 file: its one fetch is the history so far.
                fetches.append({
                    "fetched_at": previous["fetched_at"],
                    "tickers": int(previous.get("tickers") or 0),
                    "requests": int(previous.get("requests") or 0),
                    "retained_from": [],
                })
            fetches.append({
                "fetched_at": stamp,
                "tickers": len(records),
                "requests": requests,
                "retained_from": [str(p) for p in retain_from],
            })
            first = previous.get("first_fetched_at") or previous.get("fetched_at") or stamp
            tickers_total = conn.execute(
                "SELECT COUNT(*) FROM fundamentals_status"
            ).fetchone()[0]
            manifest = {
                "schema_version": SCHEMA_VERSION,
                "vss_version": __version__,
                "price_asof": as_of.isoformat(),
                # The fundamentals are as-of the FETCH, not as-of price_asof.
                # Keeping both in the manifest is what lets a report state the
                # look-ahead exactly rather than in general terms. Under E49
                # the store may hold several fetches: `fetched_at` is the
                # LATEST, `first_fetched_at` the earliest, `fetches` all of
                # them, and every status and series row carries its own.
                "fundamentals_asof": fetched_at.date().isoformat(),
                "fetched_at": stamp,
                "first_fetched_at": min(first, stamp),
                "fetches": fetches,
                # The store's tickers, not this fetch's: a re-fetch of a
                # subset leaves the rest in place.
                "tickers": tickers_total,
                "requests": requests,
            }
            manifest.update(dict(extra_manifest or {}))
            conn.executemany(
                "INSERT OR REPLACE INTO manifest VALUES (?,?)",
                [(k, json.dumps(v) if not isinstance(v, str) else v)
                 for k, v in manifest.items()],
            )
    finally:
        conn.close()
    return path


def _stamp_to_datetime(stamp: str | None) -> datetime | None:
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp)
    except ValueError:
        return None


def read_fundamentals(path: Path):
    """Rebuild the stored records, ready for filter 2.

    A record's ``fetched_at`` is the fetch that wrote its status row (E49);
    in a file written before the column existed it is the manifest's, which
    was that file's only fetch.
    """
    from .fundamentals import FieldValue, SeriesPoint, TickerFundamentals

    conn = connect_fundamentals(path, create=False)
    try:
        manifest_stamp = _manifest_of(conn).get("fetched_at")
        has_stamp = "fetched_at" in _columns(conn, "fundamentals_status")
        status_rows = conn.execute(
            "SELECT ticker, status, attempts, requests, error, newest_period"
            + (", fetched_at" if has_stamp else ", NULL")
            + " FROM fundamentals_status ORDER BY ticker"
        ).fetchall()
        field_rows = conn.execute(
            "SELECT ticker, name, status, number, text FROM fundamentals_fields"
        ).fetchall()
        # `period_months` was added after the 2026-08-21 snapshot was
        # written, so a stored file may not have the column. Asking for it
        # unconditionally would make every earlier snapshot unreadable.
        has_months = "period_months" in _columns(conn, "fundamentals_series")
        series_rows = conn.execute(
            "SELECT ticker, statement, line, period_end, value"
            + (", period_months" if has_months else ", NULL")
            + " FROM fundamentals_series"
        ).fetchall()
    finally:
        conn.close()

    fields: dict[str, list] = {}
    for ticker, name, status, number, text in field_rows:
        fields.setdefault(ticker, []).append(FieldValue(ticker, name, status, number, text))
    series: dict[str, list] = {}
    for ticker, statement, line, period_end, value, months in series_rows:
        if months is None and statement == "income":
            # A NULL is a row written before the column existed, and every
            # one of those came from the vendor path, whose statements ARE
            # the annual ones. Twelve months is what that endpoint returned,
            # not an assumption about the figure. A row written from now on
            # carries its own length, so a quarterly record stored here
            # later cannot be read as annual.
            months = 12
        series.setdefault(ticker, []).append(
            SeriesPoint(ticker, line, date.fromisoformat(period_end), value,
                        statement, months)
        )

    return [
        TickerFundamentals(
            ticker=row[0], status=row[1], attempts=row[2], requests=row[3],
            fields=tuple(fields.get(row[0], ())), series=tuple(series.get(row[0], ())),
            error=row[4],
            newest_period=date.fromisoformat(row[5]) if row[5] else None,
            fetched_at=_stamp_to_datetime(row[6] or manifest_stamp),
        )
        for row in status_rows
    ]


def read_sector_strings(path: Path) -> dict[str, tuple[str | None, str | None]]:
    """``{ticker: (sector, industry)}`` out of a fundamentals store.

    The cheap read E51's step-0 string limb needs: the two text fields, and
    nothing else. `read_fundamentals` rebuilds every series row in the file
    and step 0 has no use for them.

    A ticker absent from the result carries NO stored string -- which the
    string limb must treat as DATA MISSING about the fetch (fundamentals are
    fetched for the survivors of filter 1 alone), never as a statement that
    the company is in the circle.
    """
    if not path.exists():
        return {}
    conn = connect_fundamentals(path, create=False)
    try:
        rows = conn.execute(
            "SELECT ticker, name, text FROM fundamentals_fields "
            "WHERE name IN ('sector', 'industry')"
        ).fetchall()
    finally:
        conn.close()
    out: dict[str, list[str | None]] = {}
    for ticker, name, text in rows:
        entry = out.setdefault(ticker, [None, None])
        entry[0 if name == "sector" else 1] = (text or None)
    return {t: (v[0], v[1]) for t, v in out.items()}


def read_fundamentals_manifest(path: Path) -> dict[str, str]:
    conn = connect_fundamentals(path, create=False)
    try:
        return _manifest_of(conn)
    finally:
        conn.close()


def fundamentals_store_summary(path: Path) -> dict:
    """What the store holds after retention (E49), for the report: how many
    tickers have a status row, how many series rows there are and from
    which fetches, and which tickers carry series only -- periods carried
    in from an earlier store for a name this store's fetch never visited."""
    conn = connect_fundamentals(path, create=False)
    try:
        manifest = _manifest_of(conn)
        tickers = conn.execute("SELECT COUNT(*) FROM fundamentals_status").fetchone()[0]
        series_rows = conn.execute("SELECT COUNT(*) FROM fundamentals_series").fetchone()[0]
        has_stamp = "fetched_at" in _columns(conn, "fundamentals_series")
        by_fetch = dict(conn.execute(
            "SELECT COALESCE(fetched_at, ''), COUNT(*) FROM fundamentals_series "
            "GROUP BY fetched_at ORDER BY fetched_at"
        ).fetchall()) if has_stamp else {manifest.get("fetched_at", ""): series_rows}
        series_only = [row[0] for row in conn.execute(
            "SELECT DISTINCT ticker FROM fundamentals_series WHERE ticker NOT IN "
            "(SELECT ticker FROM fundamentals_status) ORDER BY ticker"
        ).fetchall()]
    finally:
        conn.close()
    try:
        fetches = json.loads(manifest.get("fetches") or "[]")
    except ValueError:
        fetches = []
    return {
        "tickers": tickers,
        "series_rows": series_rows,
        "rows_by_fetch": by_fetch,
        "fetches": fetches,
        "first_fetched_at": manifest.get("first_fetched_at") or manifest.get("fetched_at"),
        "fetched_at": manifest.get("fetched_at"),
        "series_only_tickers": series_only,
    }
