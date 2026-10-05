"""Snapshot storage: format, manifest, replayability."""

from __future__ import annotations

import csv
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest

from vss import snapshot as store
from vss.metrics import compute
from vss.prices import STATUS_OK, TickerFetch
from vss.universe import SCHEMA, Instrument, Merge, Rejection, SourceFile, Tally

AS_OF = date(2026, 8, 21)
CREATED = datetime(2026, 8, 22, 9, 30, 0)


def frame(days: int = 300, last: date = AS_OF) -> pd.DataFrame:
    index = pd.to_datetime([last - pd.Timedelta(days=days - 1 - i) for i in range(days)])
    return pd.DataFrame(
        {
            "Open": [10.0 + i * 0.01 for i in range(days)],
            "High": [10.5 + i * 0.01 for i in range(days)],
            "Low": [9.5 + i * 0.01 for i in range(days)],
            "Close": [10.0 + i * 0.01 for i in range(days)],
            "Volume": [1000.0 + i for i in range(days)],
        },
        index=index,
    )


def instrument(**kw) -> Instrument:
    base = dict(
        ticker_yahoo="SAP.DE", ticker_lokal="SAP", isin="DE0007164600", namn="SAP SE",
        marknad="Xetra", tier="A", listdatum=date(1998, 4, 9), valuta="EUR",
        instrumenttyp="Equity", source_file="stoxx600.csv", source_line=2,
    )
    base.update(kw)
    return Instrument(**base)


def universe_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "universe"
    directory.mkdir(exist_ok=True)
    path = directory / "stoxx600.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(SCHEMA)
        writer.writerow(["SAP.DE", "SAP", "DE0007164600", "SAP SE", "Xetra", "A",
                         "1998-04-09", "EUR", "Equity"])
    return directory


def source_file(directory: Path) -> SourceFile:
    import hashlib

    path = directory / "stoxx600.csv"
    return SourceFile(
        path=path, rows=1, tier_counts={"A": 1},
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        meta={"expected_rows": 600, "approximation": False},
        meta_sha_matches=True,
    )


def write_snapshot(tmp_path: Path, *, frames=None, as_of=AS_OF) -> tuple[Path, Path]:
    directory = universe_dir(tmp_path)
    path = store.snapshot_path(as_of, tmp_path / "snaps")
    store.write(
        path,
        as_of=as_of,
        created_at=CREATED,
        instruments=[instrument()],
        tallies=[Tally("read", count_in=1, count_out=1)],
        rejections=[Rejection("X.ST", "instrument_type", "value", "etf")],
        merges=[Merge(kept="A.ST", dropped="B.SW", on="isin", basis="highest turnover")],
        files=[source_file(directory)],
        statuses=[TickerFetch("SAP.DE", STATUS_OK, rows=300, first_date=date(2025, 10, 26),
                              last_date=as_of, attempts=1, batch=1)],
        frames={"SAP.DE": frame()} if frames is None else frames,
        extra_manifest={"tiers": "A", "period": "2y"},
    )
    return path, directory


# --- format ----------------------------------------------------------------


def test_snapshot_path_is_dated(tmp_path: Path):
    assert store.snapshot_path(AS_OF, tmp_path).parts[-2:] == ("2026-08-21", "snapshot.sqlite")


def test_every_table_is_written(tmp_path: Path):
    path, _ = write_snapshot(tmp_path)
    conn = sqlite3.connect(path)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    assert {"manifest", "universe", "rejections", "merges", "tallies",
            "fetch_status", "prices", "source_files"} <= tables
    counts = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("universe", "rejections", "merges", "tallies", "fetch_status")
    }
    conn.close()
    assert counts == {"universe": 1, "rejections": 1, "merges": 1, "tallies": 1,
                      "fetch_status": 1}


def test_manifest_records_what_a_replay_needs(tmp_path: Path):
    path, _ = write_snapshot(tmp_path)
    manifest = store.read_manifest(path)
    assert manifest["asof"] == "2026-08-21"
    assert manifest["tiers"] == "A"
    assert manifest["period"] == "2y"
    assert manifest["max_price_date"] == "2026-08-21"
    assert "stoxx600.csv" in manifest["universe_files"]
    assert manifest["schema_version"] == "3"


def test_raw_ohlcv_is_stored_not_computed_metrics(tmp_path: Path):
    path, _ = write_snapshot(tmp_path)
    conn = sqlite3.connect(path)
    columns = {r[1] for r in conn.execute("PRAGMA table_info(prices)")}
    conn.close()
    assert columns == {"ticker", "date", "open", "high", "low", "close", "volume"}
    assert "rsi" not in columns and "sma50" not in columns


def test_a_stored_series_can_be_read_back_and_measured(tmp_path: Path):
    path, _ = write_snapshot(tmp_path)
    restored = store.read_prices(path, "SAP.DE")
    metrics = compute(restored, AS_OF)
    assert metrics.last_close is not None
    assert metrics.sma200 is not None
    assert metrics.rsi14 is not None
    assert metrics.last_close_date == AS_OF


def test_metrics_match_between_the_live_frame_and_the_snapshot(tmp_path: Path):
    live = frame()
    path, _ = write_snapshot(tmp_path, frames={"SAP.DE": live})
    before = compute(live, AS_OF)
    after = compute(store.read_prices(path, "SAP.DE"), AS_OF)
    assert after.last_close == pytest.approx(before.last_close)
    assert after.high_52w == pytest.approx(before.high_52w)
    assert after.drawdown == pytest.approx(before.drawdown)
    assert after.sma200 == pytest.approx(before.sma200)
    assert after.rsi14 == pytest.approx(before.rsi14)


def test_fetch_status_round_trips(tmp_path: Path):
    path, _ = write_snapshot(tmp_path)
    (status,) = store.read_fetch_status(path)
    assert status.ticker == "SAP.DE"
    assert status.status == STATUS_OK
    assert status.last_date == AS_OF


def test_rewriting_a_date_replaces_rather_than_appends(tmp_path: Path):
    path, _ = write_snapshot(tmp_path)
    write_snapshot(tmp_path)
    conn = sqlite3.connect(path)
    rows = conn.execute("SELECT COUNT(*) FROM universe").fetchone()[0]
    conn.close()
    assert rows == 1


# --- reproducibility -------------------------------------------------------


def test_a_fresh_snapshot_verifies_clean(tmp_path: Path):
    path, directory = write_snapshot(tmp_path)
    assert store.verify(path, directory) == []


def test_an_edited_universe_file_is_caught(tmp_path: Path):
    path, directory = write_snapshot(tmp_path)
    with (directory / "stoxx600.csv").open("a", encoding="utf-8") as handle:
        handle.write("EXTRA,EXTRA,,Extra,Xetra,A,,EUR,Equity\n")
    problems = store.verify(path, directory)
    assert len(problems) == 1 and "sha256" in problems[0]


def test_a_deleted_universe_file_is_caught(tmp_path: Path):
    path, directory = write_snapshot(tmp_path)
    (directory / "stoxx600.csv").unlink()
    assert "missing from disk" in store.verify(path, directory)[0]


def test_a_close_after_asof_is_caught(tmp_path: Path):
    path, directory = write_snapshot(tmp_path)
    conn = sqlite3.connect(path)
    with conn:
        conn.execute("INSERT INTO prices VALUES ('SAP.DE','2026-08-24',1,1,1,1,1)")
    conn.close()
    problems = store.verify(path, directory)
    assert any("after asof" in p for p in problems)


def test_reading_a_snapshot_that_is_not_there(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        store.read_manifest(tmp_path / "nope.sqlite")


def test_nan_prices_are_stored_as_null_not_as_a_number(tmp_path: Path):
    series = frame(days=5)
    series.iloc[2, series.columns.get_loc("Volume")] = float("nan")
    path, _ = write_snapshot(tmp_path, frames={"SAP.DE": series})
    conn = sqlite3.connect(path)
    nulls = conn.execute("SELECT COUNT(*) FROM prices WHERE volume IS NULL").fetchone()[0]
    conn.close()
    assert nulls == 1
