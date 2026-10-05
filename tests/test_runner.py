"""Runner wiring: scoped runs must not clobber or pollute full-run artifacts."""

import sqlite3
from datetime import date, datetime, timedelta

import pandas as pd
import pytest

from vss import fetch as F
from vss import runner as RUN

WATCHLIST = """
tickers:
  - ticker: AAA.ST
    name: Aaa Co
    currency: SEK
    status: WATCH-GATED
    fv_base: 200.0
    tier: 2
    stop_price: 80.0
  - ticker: BBB.ST
    name: Bbb Co
    currency: SEK
    status: WATCH-GATED
    fv_base: 100.0
    tier: 1
    stop_price: 40.0
"""


@pytest.fixture
def project(tmp_path, monkeypatch):
    wl = tmp_path / "watchlist.yaml"
    wl.write_text(WATCHLIST)

    end = date(2026, 8, 20)
    index = pd.to_datetime([end - timedelta(days=29 - i) for i in range(30)])
    frame = pd.DataFrame({"Close": [100.0] * 30, "Volume": [1000.0] * 30}, index=index)
    monkeypatch.setattr(F, "fetch_live", lambda t, period=F.DEFAULT_PERIOD: frame.copy())

    return {
        "watchlist_path": wl,
        "cache_dir": tmp_path / "cache",
        "db_path": tmp_path / "vss.sqlite",
        "reports_dir": tmp_path / "reports",
        "now": datetime(2026, 8, 20, 22, 30).astimezone(),
    }


def test_full_run_writes_the_dated_report(project):
    assert RUN.run(**project) == 0
    assert (project["reports_dir"] / "2026-08-20.md").exists()


def test_scoped_run_does_not_overwrite_the_full_report(project):
    RUN.run(**project)
    full = (project["reports_dir"] / "2026-08-20.md").read_text()

    RUN.run(only_ticker="AAA.ST", **project)
    assert (project["reports_dir"] / "2026-08-20.md").read_text() == full
    assert (project["reports_dir"] / "2026-08-20.AAA.ST.md").exists()


def test_scoped_run_is_marked_in_the_database(project):
    RUN.run(**project)
    RUN.run(only_ticker="AAA.ST", **project)

    conn = sqlite3.connect(project["db_path"])
    rows = dict(conn.execute("SELECT ticker_filter, COUNT(*) FROM run_metrics GROUP BY 1"))
    conn.close()
    assert rows[None] == 2   # the full run covered both tickers
    assert rows["AAA.ST"] == 1  # the scoped run is identifiable as partial


def test_scoped_report_declares_itself_partial(project, capsys):
    RUN.run(only_ticker="AAA.ST", **project)
    out = capsys.readouterr().out
    assert "PARTIAL RUN" in out
    assert "1 of 2 tickers" in out
    assert "Every ticker" not in out


def test_unknown_ticker_exits_2_and_writes_nothing(project):
    assert RUN.run(only_ticker="NOSUCH", **project) == 2
    assert not project["reports_dir"].exists()


def test_dry_run_writes_no_artifacts(project):
    assert RUN.run(dry_run=True, **project) == 0
    assert not project["reports_dir"].exists()
    assert not project["db_path"].exists()
    assert not project["cache_dir"].exists()


def test_normal_run_persists_every_ticker(project):
    RUN.run(**project)
    conn = sqlite3.connect(project["db_path"])
    tickers = {r[0] for r in conn.execute("SELECT ticker FROM run_metrics")}
    conn.close()
    assert tickers == {"AAA.ST", "BBB.ST"}


def test_migration_adds_ticker_filter_to_an_older_database(project):
    """A database created before the column existed must gain it, not crash."""
    from vss.store import SCHEMA, connect

    legacy = SCHEMA.replace(",\n    -- NULL for a full run; the ticker for a --ticker run, so a partial\n    -- run is never mistaken for full coverage when reading history back.\n    ticker_filter   TEXT", "")
    conn = sqlite3.connect(project["db_path"])
    conn.executescript(legacy)
    conn.close()

    conn = connect(project["db_path"])
    columns = {r[1] for r in conn.execute("PRAGMA table_info(run_metrics)")}
    conn.close()
    assert "ticker_filter" in columns

    assert RUN.run(**project) == 0


def test_config_flag_points_at_an_alternate_watchlist(project, capsys, monkeypatch):
    """--config must not require touching config/watchlist.yaml."""
    from vss.__main__ import main
    # The fixture's series end 2026-08-20; the dry-run staleness refusal
    # (tests/test_dry_run_stale.py) is not what this test is about.
    monkeypatch.setattr("vss.rules.MAX_CLOSE_AGE_TRADING_DAYS_LEVEL", 10_000)

    rc = main(["run", "--dry-run", "--config", str(project["watchlist_path"])])
    assert rc == 0
    out = capsys.readouterr().out
    assert "AAA.ST" in out and "BBB.ST" in out


def test_config_flag_with_missing_file_exits_2(capsys, tmp_path):
    from vss.__main__ import main

    assert main(["run", "--dry-run", "--config", str(tmp_path / "nope.yaml")]) == 2


def test_the_run_declares_a_settlement_cutoff_and_the_row_carries_it():
    """REVIEW-4 report A 4.2: `vss run` read a live partial bar as a close.

    `runner.run` computes `metrics.settled_through(run_ts)` once and hands it
    to every row, so a hand run during the session prices on the last settled
    close and the store row records which it was.
    """
    import inspect
    from vss import runner as R
    source = inspect.getsource(R.run)
    assert "settled = M.settled_through(run_ts)" in source
    # The CUTOFF reaching every row is the claim; the exact argument list is
    # not. Matching the whole call broke on E100 adding `previous_mbp=`,
    # which is a true change that this test has no view about.
    assert "build_row(entry, fetched, as_of, settled" in source
    assert "last_close_settled" in inspect.getsource(R.to_record)
    assert "live_bar_date" in inspect.getsource(R.to_record)


# --- K4 in `vss run` (Build 2 item 0) -------------------------------------


def _held_entry():
    from vss.config import WatchlistEntry
    return WatchlistEntry(ticker="HLD", name="Held Co", currency="SEK",
                          status="HELD", stop_price=80.0)


def _series(last_close: float, last_volume: float, sessions: int = 60):
    end = date(2026, 8, 20)
    index = pd.to_datetime([end - timedelta(days=sessions - 1 - i)
                            for i in range(sessions)])
    closes = [100.0] * (sessions - 1) + [last_close]
    volumes = [1000.0] * (sessions - 1) + [last_volume]
    return pd.DataFrame({"Close": closes, "Volume": volumes}, index=index)


def test_a_phantom_halving_prints_DATA_MISSING_for_the_stop_check_not_a_breach():
    """The one-call fix report B #7 named: `series_sanity.check` now runs
    in `build_row`, before any level is compared. A 0.5x last bar on
    ordinary volume is an uncorroborated discontinuity, and the close it
    puts against the 80 stop is not a measurement."""
    frame = _series(last_close=50.0, last_volume=1000.0)
    fetched = F.FetchResult("HLD", frame, F.SOURCE_LIVE)
    row = RUN.build_row(_held_entry(), fetched, date(2026, 8, 20), date(2026, 8, 20))
    assert row.series_finding is not None
    codes = [v.code for v in row.assessment.verdicts]
    assert "STOP_BREACHED" not in codes
    stop = next(v for v in row.assessment.verdicts if "stop check" in v.detail)
    assert stop.code == "DATA_MISSING" and "K4" in stop.detail
    assert RUN.to_record(row, datetime(2026, 8, 20, 22, 30), date(2026, 8, 20))[
        "series_finding"] == row.series_finding


def test_a_real_repricing_the_tape_corroborates_still_breaches():
    """The control: the same halving on 20x the median volume is a repricing
    that traded, carries no finding, and the stop check fires as before."""
    frame = _series(last_close=50.0, last_volume=20_000.0)
    fetched = F.FetchResult("HLD", frame, F.SOURCE_LIVE)
    row = RUN.build_row(_held_entry(), fetched, date(2026, 8, 20), date(2026, 8, 20))
    assert row.series_finding is None
    assert "STOP_BREACHED" in [v.code for v in row.assessment.verdicts]


def test_the_report_names_the_flagged_series_and_the_store_keeps_the_reason(project):
    from vss.report import render
    frame = _series(last_close=50.0, last_volume=1000.0)
    row = RUN.build_row(_held_entry(), F.FetchResult("HLD", frame, F.SOURCE_LIVE),
                        date(2026, 8, 20), date(2026, 8, 20))
    out = render([row], run_ts=datetime(2026, 8, 20, 22, 30), as_of=date(2026, 8, 20))
    assert "Series sanity (K4)" in out and "`HLD`" in out
    assert "STOP BREACHED" not in out
    from vss.store import COLUMNS, persist
    assert "series_finding" in COLUMNS
    persist(project["db_path"], [RUN.to_record(row, datetime(2026, 8, 20, 22, 30),
                                                date(2026, 8, 20))])
    conn = sqlite3.connect(project["db_path"])
    stored = conn.execute("SELECT series_finding FROM run_metrics").fetchone()[0]
    conn.close()
    assert stored == row.series_finding


# --- Item 9: vss run prints a fair value ONLY from a complete run record ---


def _entry_with(fv_base, run_record=None, ticker="DECK"):
    """120.03 is DECK's replay under E117 (127.49 under E68, 127.75 under E70, 117.71 before it); 131.74 is B36's."""
    from vss.config import WatchlistEntry
    return WatchlistEntry(ticker=ticker, name="Deckers", currency="USD",
                          status="WATCH-GATED", fv_base=fv_base, tier=1,
                          stop_price=80.0, run_record=run_record)


def _fetched():
    return F.FetchResult("DECK", _series(last_close=100.0, last_volume=1000.0),
                         F.SOURCE_LIVE)


def test_item_9_an_fv_base_with_no_run_record_prints_DATA_MISSING_not_a_number():
    row = RUN.build_row(_entry_with(127.75), _fetched(), date(2026, 8, 20),
                        date(2026, 8, 20))
    assert row.fv_base is None
    assert "names no run record" in row.fv_refused
    assert row.assessment.mbp is None                     # nothing hangs off it
    assert "DATA MISSING" in [v.label for v in row.assessment.verdicts]
    from vss.report import render
    out = render([row], run_ts=datetime(2026, 8, 20, 22, 30), as_of=date(2026, 8, 20))
    assert "**DATA MISSING** (no complete run record)" in out
    assert "127.75" not in out.split("## ALL TICKERS")[1].split("*Run record")[0]
    assert "NOT PRINTED: `DECK`" in out
    assert RUN.to_record(row, datetime(2026, 8, 20, 22, 30), date(2026, 8, 20))[
        "fv_base"] is None


def test_item_9_a_record_missing_a_declaration_prints_DATA_MISSING_for_fv(tmp_path):
    """The test the item asks for: a run with a missing declaration prints
    DATA MISSING for fv, not a number."""
    import json
    from tests.test_runrecord import deck_record
    data = deck_record().to_dict()
    data["growth"]["view_file"] = ""                      # declaration 6 gone
    path = tmp_path / "DECK.json"
    path.write_text(json.dumps(data))
    row = RUN.build_row(_entry_with(120.03, str(path)), _fetched(),
                        date(2026, 8, 20), date(2026, 8, 20))
    assert row.fv_base is None
    assert "INCOMPLETE" in row.fv_refused and "growth view" in row.fv_refused
    assert row.assessment.mbp is None


def test_item_9_a_complete_record_that_replays_to_fv_base_prints_it(tmp_path):
    import json
    from tests.test_runrecord import deck_record
    path = tmp_path / "DECK.json"
    path.write_text(json.dumps(deck_record().to_dict()))
    row = RUN.build_row(_entry_with(120.03, str(path)), _fetched(),
                        date(2026, 8, 20), date(2026, 8, 20))
    assert row.fv_base == 120.03 and row.fv_refused is None
    assert row.assessment.mbp is not None
    from vss.report import render
    out = render([row], run_ts=datetime(2026, 8, 20, 22, 30), as_of=date(2026, 8, 20))
    assert "| 120.03 |" in out and "NOT PRINTED" not in out


def test_item_9_a_record_that_replays_to_another_number_is_refused(tmp_path):
    import json
    from tests.test_runrecord import deck_record
    path = tmp_path / "DECK.json"
    path.write_text(json.dumps(deck_record().to_dict()))
    row = RUN.build_row(_entry_with(131.74, str(path)), _fetched(),
                        date(2026, 8, 20), date(2026, 8, 20))
    assert row.fv_base is None
    assert "replays to 120.03 and the entry says 131.74" in row.fv_refused
    # and a record for another name is not this name's
    row = RUN.build_row(_entry_with(120.03, str(path), ticker="NKE"), _fetched(),
                        date(2026, 8, 20), date(2026, 8, 20))
    assert row.fv_base is None and "is DECK's, not NKE's" in row.fv_refused
    # a path that is not there
    row = RUN.build_row(_entry_with(120.03, str(tmp_path / "nope.json")), _fetched(),
                        date(2026, 8, 20), date(2026, 8, 20))
    assert row.fv_base is None and "not on disk" in row.fv_refused


def test_item_9_the_store_keeps_the_refusal_beside_the_null(project):
    row = RUN.build_row(_entry_with(127.75), _fetched(), date(2026, 8, 20),
                        date(2026, 8, 20))
    from vss.store import persist
    persist(project["db_path"], [RUN.to_record(row, datetime(2026, 8, 20, 22, 30),
                                                date(2026, 8, 20))])
    conn = sqlite3.connect(project["db_path"])
    fv, why = conn.execute("SELECT fv_base, fv_refused FROM run_metrics").fetchone()
    conn.close()
    assert fv is None and "names no run record" in why


def test_item_9_the_watchlist_key_loads():
    from vss.config import parse_entry
    e = parse_entry({"ticker": "X", "name": "X", "currency": "USD",
                     "status": "WATCH-GATED", "fv_base": 10.0,
                     "run_record": "reference/run-records/X-2026-08-26.json"}, 0)
    assert e.run_record == "reference/run-records/X-2026-08-26.json"


# --- E28 wired: the MBP is the linked record's bear case x the tier cushion --


def test_e90_SAP_DE_prints_118_56_from_its_run_record():
    """E90's MBP is the BASE-case value the record replays to (139.48) x
    the tier-1 cushion 0.85 = 118.56 -- computed, unmarked; the bear value
    120.27 stays on the row as information and no longer sets the line
    (the E28-era 96.21 must be gone from the output). Exercised on a COPY
    of the SAP.DE entry, then on the shipped entry itself."""
    from pathlib import Path
    from vss import rules as R
    from vss.config import WatchlistEntry, load_watchlist
    from vss.report import render
    shipped = {e.ticker: e for e in load_watchlist(Path("config/watchlist.yaml"))}["SAP.DE"]
    assert shipped.fv_base == 140.37 and shipped.tier == 1   # the E90/E91 re-strike of 2026-08-30 evening
    assert shipped.run_record == "reference/run-records/SAP.DE-2026-08-30-e91.json"
    fetched = F.FetchResult("SAP.DE", _series(last_close=187.20, last_volume=1000.0),
                            F.SOURCE_LIVE)
    entry = WatchlistEntry(ticker="SAP.DE", name="SAP SE", currency="EUR",
                           status="WATCH-PRICED", fv_base=139.48, tier=1,
                           # the COPY half exercises the E88-divisor record
                           # of 2026-08-30, which replays to 139.48; the
                           # shipped entry now links the -e91 record (140.37)
                           run_record="reference/run-records/SAP.DE-2026-08-30.json")
    row = RUN.build_row(entry, fetched, date(2026, 8, 20), date(2026, 8, 20))
    assert row.fv_base == 139.48 and row.fv_refused is None
    assert row.fv_bear == pytest.approx(120.27, abs=0.005)   # information, not the line
    assert row.assessment.mbp == 118.56
    assert row.assessment.mbp_superseded is False
    out = render([row], run_ts=datetime(2026, 8, 26, 9, 0), as_of=date(2026, 8, 20))
    assert "| 118.56 |" in out and "96.21" not in out
    assert R.MBP_SUPERSEDED_MARK not in out
    assert "`SAP.DE` 118.56 = base-case value 139.48 x tier 1 cushion 0.85" in out
    # the shipped entry, on the E91 record: 140.3746... x 0.85 = 119.32,
    # computed from the UNROUNDED replay, unmarked
    row = RUN.build_row(shipped, fetched, date(2026, 8, 20), date(2026, 8, 20))
    assert row.fv_base == 140.37 and row.assessment.mbp == 119.32
    assert row.assessment.mbp_superseded is False


def test_e90_LIAB_ST_prints_51_73_from_its_run_record():
    """The shipped watchlist: LIAB.ST links its E117 record (E120's stand-in,
    2026-09-19) with fv_base 68.97 and tier 2. E90's MBP = 68.97 x 0.75 =
    51.73 -- computed, unmarked; the bear value 54.03 prints as information.
    (Before E117: 133.48, MBP 100.11, bear 107.23.)

    THE POSITION WAS SOLD 2026-09-21 at 120.70 for 121 shares (C4 / E42,
    decided 2026-09-19), so the name is DROPPED, its stop is cleared and its
    catalyst is cleared. What this test pins is E90's ARITHMETIC off the
    record, which the exit does not touch -- the fair value and the tier
    stay on the entry as the record of what was struck."""
    from pathlib import Path
    from vss.config import load_watchlist
    entry = {e.ticker: e for e in load_watchlist(Path("config/watchlist.yaml"))}["LIAB.ST"]
    assert entry.status == "DROPPED" and entry.stop_price is None   # sold 2026-09-21
    assert entry.tier == 2
    assert [f.shares for f in entry.sales] == [121] and entry.sales[0].price == 120.70
    assert entry.fv_base == 68.97
    assert entry.run_record == "reference/run-records/LIAB.ST-2026-09-19-e117.json"
    fetched = F.FetchResult("LIAB.ST", _series(last_close=123.60, last_volume=1000.0),
                            F.SOURCE_LIVE)
    row = RUN.build_row(entry, fetched, date(2026, 8, 20), date(2026, 8, 20))
    assert row.fv_base == 68.97 and row.fv_refused is None
    assert row.fv_bear == pytest.approx(54.03, abs=0.005)   # information
    assert row.assessment.mbp == 51.73 and row.assessment.mbp_superseded is False


def test_e90_a_record_without_a_bear_case_prints_the_same_unmarked_figure(tmp_path):
    """E90: the bear case no longer enters the buy line, so a record with
    no bear case prints the SAME base x cushion figure, unmarked -- the
    E28-era marked fallback is retired."""
    import json
    from tests.test_runrecord import deck_record
    data = deck_record().to_dict()
    data["growth"]["bear"] = None
    path = tmp_path / "DECK.json"
    path.write_text(json.dumps(data))
    row = RUN.build_row(_entry_with(120.03, str(path)), _fetched(),
                        date(2026, 8, 20), date(2026, 8, 20))
    assert row.fv_base == 120.03 and row.fv_bear is None
    assert row.assessment.mbp == 102.03 and row.assessment.mbp_superseded is False   # 120.03 x 0.85
    # with the bear case the figure is IDENTICAL -- the bear is information
    path.write_text(json.dumps(deck_record().to_dict()))
    live = RUN.build_row(_entry_with(120.03, str(path)), _fetched(),
                         date(2026, 8, 20), date(2026, 8, 20))
    assert live.fv_bear == pytest.approx(deck_record().strike(0.0))
    assert live.assessment.mbp == 102.03
    assert live.assessment.mbp_superseded is False


# --- E63: the store keeps the 52-week low beside the drawdown ---------------


def test_e63_the_store_keeps_the_low_its_date_and_the_distance_and_migrates_an_older_database(project):
    """The three E63 columns travel to run_metrics beside the drawdown, and a
    database created before them gains them rather than crashing. NULL
    together below the coverage bar, never a partial reading."""
    from vss.store import COLUMNS, SCHEMA, connect, persist

    legacy = SCHEMA
    for column in ("    low_52w         REAL,\n", "    low_52w_date    TEXT,\n",
                   "    pct_above_52w_low REAL,\n"):
        assert column in legacy
        legacy = legacy.replace(column, "")
    conn = sqlite3.connect(project["db_path"])
    conn.executescript(legacy)
    conn.close()
    conn = connect(project["db_path"])
    columns = {r[1] for r in conn.execute("PRAGMA table_info(run_metrics)")}
    conn.close()
    assert {"low_52w", "low_52w_date", "pct_above_52w_low"} <= columns
    assert {"low_52w", "low_52w_date", "pct_above_52w_low"} <= set(COLUMNS)

    covered = RUN.build_row(
        _held_entry(), F.FetchResult("HLD", _series(90.0, 1000.0, sessions=400), F.SOURCE_LIVE),
        date(2026, 8, 20), date(2026, 8, 20))
    persist(project["db_path"], [RUN.to_record(covered, datetime(2026, 8, 20, 22, 30),
                                                date(2026, 8, 20))])
    conn = sqlite3.connect(project["db_path"])
    low, when, above, dd = conn.execute(
        "SELECT low_52w, low_52w_date, pct_above_52w_low, drawdown FROM run_metrics"
    ).fetchone()
    conn.close()
    assert low == pytest.approx(90.0) and when == "2026-08-20"
    assert above == pytest.approx(0.0) and dd == pytest.approx(0.10)

    short = RUN.build_row(
        _held_entry(), F.FetchResult("HLD", _series(90.0, 1000.0), F.SOURCE_LIVE),
        date(2026, 8, 20), date(2026, 8, 20))
    record = RUN.to_record(short, datetime(2026, 8, 20, 22, 30), date(2026, 8, 20))
    assert record["drawdown"] is None
    assert (record["low_52w"], record["low_52w_date"], record["pct_above_52w_low"]) \
        == (None, None, None)
