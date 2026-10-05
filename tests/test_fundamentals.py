"""Fundamentals fetching: per-ticker and per-field status, storage, replay."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest

from vss import snapshot as store
from vss.fundamentals import (
    ALL_FIELDS,
    FIELD_NO_DATA,
    FIELD_OK,
    FIELD_THROTTLED,
    REQUESTS_PER_TICKER,
    extract_fields,
    extract_series,
    fetch_many,
    fetch_one,
    field_coverage,
    series_coverage,
    status_counts,
)
from vss.prices import STATUS_NO_DATA, STATUS_OK, STATUS_STALE, STATUS_THROTTLED

AS_OF = date(2026, 8, 21)

INFO = {
    "sector": "Technology", "industry": "Software", "financialCurrency": "EUR",
    "currency": "EUR", "quoteType": "EQUITY",
    "freeCashflow": 9_090_624_512, "operatingCashflow": 9_464_999_936,
    "totalRevenue": 38_192_001_024, "revenueGrowth": 0.094,
    "ebitda": 11_760_000_000, "totalDebt": 9_939_000_320,
    "totalCash": 11_624_999_936, "enterpriseValue": 215_947_100_160,
    "marketCap": 217_128_910_848, "regularMarketPrice": 186.16,
}


def statement(years=(2025, 2024, 2023, 2022), revenue=(38.2, 34.2, 31.2, 30.9)) -> pd.DataFrame:
    columns = [pd.Timestamp(f"{y}-12-31") for y in years]
    return pd.DataFrame(
        {c: [r * 1e9, 11.7e9, 9.0e9, 8.0e9] for c, r in zip(columns, revenue)},
        index=["Total Revenue", "EBITDA", "EBIT", "Net Income"],
    )


def reader_for(info=None, frame=None, error=None):
    def reader(ticker):
        if error is not None:
            raise error
        return (INFO if info is None else info), (statement() if frame is None else frame), \
            REQUESTS_PER_TICKER
    return reader


# --- extraction ------------------------------------------------------------


def test_every_requested_field_gets_a_status():
    fields = extract_fields("SAP.DE", INFO)
    assert {f.name for f in fields} == set(ALL_FIELDS)
    assert all(f.status == FIELD_OK for f in fields)


def test_a_missing_field_is_no_data_not_zero():
    info = dict(INFO)
    info.pop("ebitda")
    by_name = {f.name: f for f in extract_fields("X", info)}
    assert by_name["ebitda"].status == FIELD_NO_DATA
    assert by_name["ebitda"].number is None


def test_a_none_field_is_no_data():
    by_name = {f.name: f for f in extract_fields("X", dict(INFO, ebitda=None))}
    assert by_name["ebitda"].status == FIELD_NO_DATA


def test_a_non_numeric_value_does_not_become_a_number():
    by_name = {f.name: f for f in extract_fields("X", dict(INFO, ebitda="n/a"))}
    assert by_name["ebitda"].status == FIELD_NO_DATA


def test_a_nan_is_no_data():
    by_name = {f.name: f for f in extract_fields("X", dict(INFO, ebitda=float("nan")))}
    assert by_name["ebitda"].status == FIELD_NO_DATA


def test_series_extraction_keeps_period_ends():
    points = extract_series("X", statement())
    revenue = sorted((p for p in points if p.line == "Total Revenue"),
                     key=lambda p: p.period_end)
    assert [p.period_end.year for p in revenue] == [2022, 2023, 2024, 2025]


def test_an_empty_statement_yields_no_series():
    assert extract_series("X", None) == []
    assert extract_series("X", pd.DataFrame()) == []


# --- per-ticker fetching ---------------------------------------------------


def test_a_good_ticker_comes_back_ok_with_both_layers():
    record = fetch_one("SAP.DE", as_of=AS_OF, reader=reader_for(), sleep=lambda _: None)
    assert record.status == STATUS_OK
    assert record.requests == REQUESTS_PER_TICKER
    assert record.value("ebitda") == 11_760_000_000
    assert record.text("sector") == "Technology"
    assert len(record.revenue_series()) == 4


def test_a_bank_is_ok_at_ticker_level_and_missing_at_field_level():
    """The reason the two layers exist."""
    info = {k: v for k, v in INFO.items() if k not in ("ebitda", "freeCashflow")}
    info["sector"] = "Financial Services"
    record = fetch_one("HSBA.L", as_of=AS_OF, reader=reader_for(info),
                       sleep=lambda _: None)
    assert record.status == STATUS_OK
    assert record.value("ebitda") is None
    assert record.value("totalDebt") is not None
    by_name = {f.name: f.status for f in record.fields}
    assert by_name["ebitda"] == FIELD_NO_DATA
    assert by_name["totalDebt"] == FIELD_OK


def test_throttling_is_distinguished_from_absence():
    throttled = fetch_one("A", as_of=AS_OF, sleep=lambda _: None, max_attempts=1,
                          reader=reader_for(error=RuntimeError("HTTP 429 Too Many Requests")))
    absent = fetch_one("B", as_of=AS_OF, sleep=lambda _: None, max_attempts=1,
                       reader=reader_for(error=RuntimeError("no such ticker")))
    assert throttled.status == STATUS_THROTTLED
    assert absent.status == STATUS_NO_DATA
    assert all(f.status == FIELD_THROTTLED for f in throttled.fields)
    assert all(f.status == FIELD_NO_DATA for f in absent.fields)


def test_a_failed_ticker_still_reports_every_field():
    record = fetch_one("A", as_of=AS_OF, sleep=lambda _: None, max_attempts=1,
                       reader=reader_for(error=RuntimeError("boom")))
    assert {f.name for f in record.fields} == set(ALL_FIELDS)


def test_retry_and_backoff_fire_with_growing_delays():
    slept, attempts = [], {"n": 0}

    def reader(ticker):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("HTTP 429 Too Many Requests")
        return INFO, statement(), REQUESTS_PER_TICKER

    record = fetch_one("A", as_of=AS_OF, reader=reader, sleep=slept.append,
                       max_attempts=4)
    assert slept == [2.0, 4.0]
    assert record.status == STATUS_OK and record.attempts == 3


def test_an_empty_response_is_no_data():
    record = fetch_one("A", as_of=AS_OF, sleep=lambda _: None,
                       reader=lambda t: ({}, None, 2))
    assert record.status == STATUS_NO_DATA


def test_an_old_newest_period_is_stale_and_counted_on_value():
    old = statement(years=(2023, 2022), revenue=(30.0, 29.0))
    outcome = fetch_many(["A"], as_of=AS_OF, sleep=lambda _: None,
                         reader=reader_for(frame=old))
    assert outcome.records[0].status == STATUS_STALE
    assert outcome.tally.rejected_on_value == 1
    assert outcome.tally.rejected_on_missing == 0


def test_no_fundamentals_is_counted_on_missing():
    outcome = fetch_many(["A"], as_of=AS_OF, sleep=lambda _: None,
                         reader=reader_for(error=RuntimeError("gone")))
    assert outcome.tally.rejected_on_missing == 1
    assert outcome.tally.rejected_on_value == 0


def test_fetch_many_visits_every_ticker_once_and_counts_requests():
    seen = []

    def reader(ticker):
        seen.append(ticker)
        return INFO, statement(), REQUESTS_PER_TICKER

    outcome = fetch_many(["A", "B", "C"], as_of=AS_OF, reader=reader,
                         sleep=lambda _: None)
    assert seen == ["A", "B", "C"]
    assert outcome.requests == 3 * REQUESTS_PER_TICKER
    assert len(outcome.records) == 3


def test_fetch_many_pauses_between_tickers_but_not_after_the_last():
    slept = []
    fetch_many(["A", "B", "C"], as_of=AS_OF, reader=reader_for(),
               sleep=slept.append, inter_ticker_seconds=0.25)
    assert slept == [0.25, 0.25]


# --- coverage tables -------------------------------------------------------


def test_field_coverage_counts_per_field_not_per_ticker():
    thin = {k: v for k, v in INFO.items() if k != "ebitda"}
    records = [
        fetch_one("A", as_of=AS_OF, reader=reader_for(), sleep=lambda _: None),
        fetch_one("B", as_of=AS_OF, reader=reader_for(thin), sleep=lambda _: None),
    ]
    table = field_coverage(records)
    assert table["ebitda"] == {FIELD_OK: 1, FIELD_NO_DATA: 1, FIELD_THROTTLED: 0}
    assert table["totalDebt"][FIELD_OK] == 2


def test_status_counts_covers_all_four():
    assert set(status_counts([])) == {STATUS_OK, STATUS_THROTTLED, STATUS_NO_DATA,
                                      STATUS_STALE}


def test_series_coverage_is_a_histogram():
    records = [fetch_one("A", as_of=AS_OF, reader=reader_for(), sleep=lambda _: None)]
    assert series_coverage(records) == {4: 1}


# --- storage ---------------------------------------------------------------


def write(tmp_path: Path, records, requests=4):
    path = store.fundamentals_path(AS_OF, tmp_path / "snaps")
    store.write_fundamentals(
        path, as_of=AS_OF, fetched_at=datetime(2026, 8, 22, 16, 0),
        records=records, requests=requests,
    )
    return path


def test_the_store_lives_beside_the_price_snapshot_not_inside_it(tmp_path: Path):
    path = write(tmp_path, [fetch_one("A", as_of=AS_OF, reader=reader_for(),
                                      sleep=lambda _: None)])
    assert path.name == "fundamentals.sqlite"
    assert path.parent.name == AS_OF.isoformat()
    assert not (path.parent / "snapshot.sqlite").exists()


def test_records_round_trip(tmp_path: Path):
    original = fetch_one("SAP.DE", as_of=AS_OF, reader=reader_for(), sleep=lambda _: None)
    path = write(tmp_path, [original])
    (restored,) = store.read_fundamentals(path)
    assert restored.ticker == original.ticker
    assert restored.status == original.status
    assert restored.value("ebitda") == original.value("ebitda")
    assert restored.text("sector") == original.text("sector")
    assert restored.revenue_series() == original.revenue_series()
    assert restored.newest_period == original.newest_period


def test_field_statuses_survive_the_round_trip(tmp_path: Path):
    thin = {k: v for k, v in INFO.items() if k != "ebitda"}
    path = write(tmp_path, [fetch_one("B", as_of=AS_OF, reader=reader_for(thin),
                                      sleep=lambda _: None)])
    (restored,) = store.read_fundamentals(path)
    by_name = {f.name: f.status for f in restored.fields}
    assert by_name["ebitda"] == FIELD_NO_DATA
    assert by_name["totalDebt"] == FIELD_OK


def test_the_manifest_records_both_dates(tmp_path: Path):
    """The look-ahead warning is written from these two."""
    path = write(tmp_path, [fetch_one("A", as_of=AS_OF, reader=reader_for(),
                                      sleep=lambda _: None)])
    manifest = store.read_fundamentals_manifest(path)
    assert manifest["price_asof"] == "2026-08-21"
    assert manifest["fundamentals_asof"] == "2026-08-22"
    assert manifest["fundamentals_asof"] != manifest["price_asof"]


def test_rewriting_replaces_rather_than_appends(tmp_path: Path):
    record = fetch_one("A", as_of=AS_OF, reader=reader_for(), sleep=lambda _: None)
    write(tmp_path, [record])
    path = write(tmp_path, [record])
    conn = sqlite3.connect(path)
    rows = conn.execute("SELECT COUNT(*) FROM fundamentals_status").fetchone()[0]
    conn.close()
    assert rows == 1


def test_reading_a_store_that_is_not_there(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        store.read_fundamentals(tmp_path / "nope.sqlite")


# --- item 8: the quarterly statements ---------------------------------------


def _quarterly_frames():
    quarterly = pd.DataFrame(
        {pd.Timestamp("2026-06-30"): [1.0e9, 2.0e8],
         pd.Timestamp("2026-03-31"): [float("nan"), 1.9e8]},
        index=["Total Revenue", "EBIT"],
    )
    balance_q = pd.DataFrame({pd.Timestamp("2026-06-30"): [5.0e9]}, index=["Total Assets"])
    return {"income": statement(), "income_quarterly": quarterly,
            "balance_quarterly": balance_q}


def test_quarterly_statements_carry_their_length_under_their_own_name():
    points = extract_series("X", _quarterly_frames())
    quarterly = [p for p in points if p.statement == "income_quarterly"]
    assert {p.period_months for p in quarterly} == {3}
    assert {p.period_months for p in points if p.statement == "income"} == {12}
    assert [p.period_months for p in points if p.statement == "balance_quarterly"] == [None]
    hole = next(p for p in quarterly
                if p.line == "Total Revenue" and p.period_end == date(2026, 3, 31))
    assert hole.value is None, "a NaN quarter is a hole, never a zero"


def test_the_annual_and_quarterly_views_never_mix(tmp_path: Path):
    record = fetch_one("X", as_of=AS_OF, sleep=lambda _: None,
                       reader=lambda t: (INFO, _quarterly_frames(), REQUESTS_PER_TICKER))
    assert record.status == STATUS_OK
    assert len(record.revenue_series()) == 4, "the annual trend must not gain a quarter"
    assert record.quarterly_series("Total Revenue") == [(date(2026, 6, 30), 1.0e9)]
    assert record.quarterly_series("EBIT") == [(date(2026, 3, 31), 1.9e8), (date(2026, 6, 30), 2.0e8)]
    assert record.latest("Total Assets") == (date(2026, 6, 30), 5.0e9)
    assert record.at(date(2026, 6, 30), "Total Assets") == (date(2026, 6, 30), 5.0e9)
    assert record.at(date(2025, 12, 31), "Total Assets") is None
    from vss.fundamentals import quarterly_coverage

    assert quarterly_coverage([record]) == {1: 1}
    assert series_coverage([record]) == {4: 1}
    # And the round trip through the store keeps every length.
    path = write(tmp_path, [record])
    (restored,) = store.read_fundamentals(path)
    assert restored.quarterly_series("EBIT") == record.quarterly_series("EBIT")
    assert len(restored.revenue_series()) == 4


def test_an_absent_quarterly_frame_is_data_missing_for_the_quarters_only():
    frames = {"income": statement(), "income_quarterly": None, "balance_quarterly": None}
    record = fetch_one("X", as_of=AS_OF, sleep=lambda _: None,
                       reader=lambda t: (INFO, frames, REQUESTS_PER_TICKER))
    assert record.status == STATUS_OK
    assert record.quarterly_series("Total Revenue") == []
    assert len(record.revenue_series()) == 4


def test_a_point_of_unrecorded_length_counts_as_annual():
    from vss.fundamentals import SeriesPoint, TickerFundamentals

    legacy = TickerFundamentals("X", STATUS_OK, 1, 3, (), (
        SeriesPoint("X", "Total Revenue", date(2025, 12, 31), 1.0, "income", None),
        SeriesPoint("X", "Total Revenue", date(2026, 3, 31), 2.0, "income_quarterly", 3),
    ))
    assert legacy.revenue_series() == [(date(2025, 12, 31), 1.0)]
    assert legacy.quarterly_series("Total Revenue") == [(date(2026, 3, 31), 2.0)]


# --- E49: the store retains every period it has ever fetched ---------------


def _quarters(ticker: str, quarters: dict) -> "TickerFundamentals":
    """A fetched record whose quarterly revenue is exactly ``quarters``
    (ISO date -> value; NaN is a hole), on top of the annual fixture."""
    frame = pd.DataFrame(
        {pd.Timestamp(day): [value] for day, value in quarters.items()},
        index=["Total Revenue"],
    )
    frames = {"income": statement(), "income_quarterly": frame}
    return fetch_one(ticker, as_of=AS_OF, sleep=lambda _: None,
                     reader=lambda t: (INFO, frames, REQUESTS_PER_TICKER))


def _write_at(path: Path, records, fetched_at: datetime, retain_from=()):
    return store.write_fundamentals(
        path, as_of=AS_OF, fetched_at=fetched_at, records=records, requests=5,
        retain_from=retain_from,
    )


def _stamps(path: Path, ticker: str, line: str = "Total Revenue") -> dict:
    conn = sqlite3.connect(path)
    try:
        return {
            date.fromisoformat(period): (value, fetched)
            for period, value, fetched in conn.execute(
                "SELECT period_end, value, fetched_at FROM fundamentals_series "
                "WHERE ticker = ? AND statement = 'income_quarterly' AND line = ?",
                (ticker, line),
            )
        }
    finally:
        conn.close()


FETCH_1 = datetime(2026, 5, 1, 16, 0)
FETCH_2 = datetime(2026, 8, 22, 16, 0)


def test_e49_two_fetches_with_overlapping_quarters_yield_the_union(tmp_path: Path):
    """The vendor serves five quarters; E45 wants eight. Two fetches four
    months apart leave SIX in the store, and the overlap carries the newer
    fetch's figures."""
    path = store.fundamentals_path(AS_OF, tmp_path / "snaps")
    _write_at(path, [_quarters("A", {"2025-03-31": 1.0, "2025-06-30": 2.0,
                                     "2025-09-30": 3.0, "2025-12-31": 4.0})], FETCH_1)
    _write_at(path, [_quarters("A", {"2025-09-30": 3.5, "2025-12-31": 4.5,
                                     "2026-03-31": 5.0, "2026-06-30": 6.0})], FETCH_2)
    (restored,) = store.read_fundamentals(path)
    assert restored.quarterly_series("Total Revenue") == [
        (date(2025, 3, 31), 1.0), (date(2025, 6, 30), 2.0),
        (date(2025, 9, 30), 3.5), (date(2025, 12, 31), 4.5),
        (date(2026, 3, 31), 5.0), (date(2026, 6, 30), 6.0),
    ]
    stamps = _stamps(path, "A")
    assert stamps[date(2025, 3, 31)] == (1.0, "2026-05-01T16:00:00")
    assert stamps[date(2025, 9, 30)] == (3.5, "2026-08-22T16:00:00")
    assert restored.fetched_at == FETCH_2, "the status row is the latest fetch's"
    # And the annual rows, present in both fetches, are one row per period.
    assert len(restored.revenue_series()) == 4


def test_e49_a_re_fetch_replaces_only_the_periods_it_returns(tmp_path: Path):
    path = store.fundamentals_path(AS_OF, tmp_path / "snaps")
    _write_at(path, [_quarters("A", {"2025-09-30": 3.0, "2025-12-31": 4.0})], FETCH_1)
    _write_at(path, [_quarters("A", {"2025-12-31": 4.4})], FETCH_2)
    stamps = _stamps(path, "A")
    assert stamps[date(2025, 12, 31)] == (4.4, "2026-08-22T16:00:00"), "restated: replaced"
    assert stamps[date(2025, 9, 30)] == (3.0, "2026-05-01T16:00:00"), "not returned: kept"


def test_e49_a_hole_never_overwrites_a_stored_figure(tmp_path: Path):
    """yfinance #1345: a quarter present in May and NaN in August is the
    vendor's instability, not a restatement. The May figure stays, with
    its own stamp. A hole with no figure behind it is stored as a hole,
    and a later figure fills it."""
    path = store.fundamentals_path(AS_OF, tmp_path / "snaps")
    _write_at(path, [_quarters("A", {"2025-12-31": 4.0, "2026-03-31": float("nan")})], FETCH_1)
    _write_at(path, [_quarters("A", {"2025-12-31": float("nan"), "2026-03-31": 5.0})], FETCH_2)
    stamps = _stamps(path, "A")
    assert stamps[date(2025, 12, 31)] == (4.0, "2026-05-01T16:00:00")
    assert stamps[date(2026, 3, 31)] == (5.0, "2026-08-22T16:00:00")
    (restored,) = store.read_fundamentals(path)
    assert restored.quarterly_series("Total Revenue") == [
        (date(2025, 12, 31), 4.0), (date(2026, 3, 31), 5.0)]


def test_e49_the_newest_fetch_wins_whatever_the_write_order(tmp_path: Path):
    """Carry-in and re-runs can write an older fetch AFTER a newer one. The
    stamp decides, not the order."""
    path = store.fundamentals_path(AS_OF, tmp_path / "snaps")
    _write_at(path, [_quarters("A", {"2025-12-31": 4.4})], FETCH_2)
    _write_at(path, [_quarters("A", {"2025-12-31": 4.0, "2025-09-30": 3.0})], FETCH_1)
    stamps = _stamps(path, "A")
    assert stamps[date(2025, 12, 31)] == (4.4, "2026-08-22T16:00:00")
    assert stamps[date(2025, 9, 30)] == (3.0, "2026-05-01T16:00:00")


def test_e49_an_earlier_dated_store_seeds_a_new_one(tmp_path: Path):
    root = tmp_path / "snaps"
    earlier = store.fundamentals_path(date(2026, 8, 14), root)
    later_dated = store.fundamentals_path(date(2026, 9, 4), root)
    _write_at(earlier, [_quarters("A", {"2025-03-31": 1.0, "2025-06-30": 2.0}),
                        _quarters("ONLY-EARLIER", {"2025-06-30": 9.0})], FETCH_1)
    _write_at(later_dated, [_quarters("A", {"2026-09-30": 99.0})], datetime(2026, 9, 4, 16, 0))

    assert store.earlier_fundamentals_stores(root, before=AS_OF) == [earlier], \
        "strictly earlier dates only -- a later store could carry look-ahead"

    path = store.fundamentals_path(AS_OF, root)
    _write_at(path, [_quarters("A", {"2025-06-30": 2.2, "2025-09-30": 3.0})], FETCH_2,
              retain_from=store.earlier_fundamentals_stores(root, before=AS_OF))
    records = {r.ticker: r for r in store.read_fundamentals(path)}
    assert records["A"].quarterly_series("Total Revenue") == [
        (date(2025, 3, 31), 1.0), (date(2025, 6, 30), 2.2), (date(2025, 9, 30), 3.0)]
    assert "ONLY-EARLIER" not in records, "no status row: invisible to the chain"
    summary = store.fundamentals_store_summary(path)
    assert summary["series_only_tickers"] == ["ONLY-EARLIER"]
    assert summary["tickers"] == 1
    assert [f["fetched_at"] for f in summary["fetches"]] == ["2026-08-22T16:00:00"]
    assert summary["fetches"][0]["retained_from"] == [str(earlier)]
    # The earlier store itself is untouched by being read.
    assert _stamps(earlier, "A")[date(2025, 6, 30)] == (2.0, "2026-05-01T16:00:00")


def test_e49_a_pre_e49_store_is_migrated_on_the_first_write(tmp_path: Path):
    """The 2026-08-21 and 2026-08-26 stores predate the stamp column (and
    08-21 the length column). The first write into one backfills every
    row with the file's manifest fetch and every income row with twelve
    months, then upserts on top."""
    path = tmp_path / "snaps" / "2026-08-21" / "fundamentals.sqlite"
    path.parent.mkdir(parents=True)
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE manifest (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE fundamentals_status (ticker TEXT PRIMARY KEY, status TEXT NOT NULL,
            attempts INTEGER NOT NULL, requests INTEGER NOT NULL, error TEXT, newest_period TEXT);
        CREATE TABLE fundamentals_fields (ticker TEXT NOT NULL, name TEXT NOT NULL,
            status TEXT NOT NULL, number REAL, text TEXT, PRIMARY KEY (ticker, name));
        CREATE TABLE fundamentals_series (ticker TEXT NOT NULL, statement TEXT NOT NULL,
            line TEXT NOT NULL, period_end TEXT NOT NULL, value REAL,
            PRIMARY KEY (ticker, statement, line, period_end));
        INSERT INTO manifest VALUES ('fetched_at', '2026-08-22T16:00:00');
        INSERT INTO manifest VALUES ('fundamentals_asof', '2026-08-22');
        INSERT INTO fundamentals_status VALUES ('A', 'OK', 1, 3, NULL, '2025-12-31');
        INSERT INTO fundamentals_series VALUES ('A', 'income', 'Total Revenue', '2025-12-31', 38.2e9);
        INSERT INTO fundamentals_series VALUES ('A', 'income', 'Total Revenue', '2021-12-31', 28.0e9);
    """)
    conn.commit()
    conn.close()
    # Reading does not alter the file ...
    (legacy,) = store.read_fundamentals(path)
    assert legacy.fetched_at == datetime(2026, 8, 22, 16, 0)
    assert legacy.revenue_series() == [(date(2021, 12, 31), 28.0e9), (date(2025, 12, 31), 38.2e9)]
    conn = sqlite3.connect(path)
    assert "fetched_at" not in {r[1] for r in conn.execute("PRAGMA table_info(fundamentals_series)")}
    conn.close()
    # ... the first write does, in place, and the union holds.
    _write_at(path, [_quarters("A", {"2026-03-31": 5.0})], datetime(2026, 8, 27, 1, 0))
    conn = sqlite3.connect(path)
    rows = conn.execute(
        "SELECT statement, period_end, period_months, fetched_at FROM fundamentals_series "
        "WHERE ticker = 'A' AND line = 'Total Revenue' ORDER BY statement, period_end"
    ).fetchall()
    conn.close()
    assert ("income", "2021-12-31", 12, "2026-08-22T16:00:00") in rows, \
        "not returned again: kept, backfilled with the file's one fetch and twelve months"
    assert ("income", "2025-12-31", 12, "2026-08-27T01:00:00") in rows, "returned again: re-stamped"
    assert ("income_quarterly", "2026-03-31", 3, "2026-08-27T01:00:00") in rows
    manifest = store.read_fundamentals_manifest(path)
    assert manifest["first_fetched_at"] == "2026-08-22T16:00:00"
    assert manifest["fetched_at"] == "2026-08-27T01:00:00"
    assert manifest["fundamentals_asof"] == "2026-08-27"
    import json

    assert [f["fetched_at"] for f in json.loads(manifest["fetches"])] == [
        "2026-08-22T16:00:00", "2026-08-27T01:00:00"], "the file's own fetch heads the history"


def test_e49_the_manifest_records_every_fetch_and_the_stores_tickers(tmp_path: Path):
    path = store.fundamentals_path(AS_OF, tmp_path / "snaps")
    _write_at(path, [_quarters("A", {"2025-12-31": 4.0}), _quarters("B", {"2025-12-31": 1.0})], FETCH_1)
    _write_at(path, [_quarters("B", {"2026-03-31": 1.1})], FETCH_2)
    manifest = store.read_fundamentals_manifest(path)
    assert manifest["first_fetched_at"] == "2026-05-01T16:00:00"
    assert manifest["fetched_at"] == "2026-08-22T16:00:00"
    assert manifest["tickers"] == "2", "the store's tickers, not the subset re-fetched"
    import json

    fetches = json.loads(manifest["fetches"])
    assert [(f["fetched_at"], f["tickers"]) for f in fetches] == [
        ("2026-05-01T16:00:00", 2), ("2026-08-22T16:00:00", 1)]
    records = {r.ticker: r for r in store.read_fundamentals(path)}
    assert records["A"].fetched_at == FETCH_1, "A was not re-fetched: its own stamp"
    assert records["B"].fetched_at == FETCH_2
    conn = sqlite3.connect(path)
    assert conn.execute("SELECT COUNT(*) FROM fundamentals_status").fetchone()[0] == 2
    conn.close()
