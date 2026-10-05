"""E122 (owner, 2026-09-20): a price we have held is not retractable by the
vendor's silence.

The case: on 2026-09-19 yfinance returned no 09-17 row and a NaN close on
09-18 for twelve continental-European names, and `write_cache`'s blind
`frame.to_csv(path)` destroyed closes the 09-18 nightly had already seen,
stored and printed -- LIAB.ST 119.70, SAP.DE 183.12.
"""
from datetime import date, datetime

import pandas as pd
import pytest

from vss import fetch as F

NAN = float("nan")


def _frame(rows: dict[str, float | None], *, open_=100.0) -> pd.DataFrame:
    idx = pd.DatetimeIndex([pd.Timestamp(d) for d in rows])
    f = pd.DataFrame({"Open": open_, "High": 0.0, "Low": 0.0,
                      "Close": [NAN if v is None else v for v in rows.values()],
                      "Volume": 1}, index=idx)
    f.index.name = "Date"
    return f


def _closes(frame) -> dict[str, float]:
    return {str(i.date()): v for i, v in zip(frame.index, frame["Close"])}


# --- (a) a date once held is never removed ---------------------------------

def test_a_date_the_vendor_drops_is_kept():
    held = _frame({"2026-09-16": 123.4, "2026-09-17": 123.8, "2026-09-18": 119.7})
    merged, retained, corrections = F.merge_series(
        held, _frame({"2026-09-16": 123.4}), as_of=date(2026, 9, 19))
    assert _closes(merged) == {"2026-09-16": 123.4, "2026-09-17": 123.8,
                               "2026-09-18": 119.7}
    assert sorted(str(d) for d in retained) == ["2026-09-17", "2026-09-18"]
    assert corrections == ()


# --- (b) a blank never overwrites a held close -----------------------------

def test_a_nan_close_never_overwrites_a_held_one():
    """The exact 2026-09-18 LIAB.ST row: OHLV present, close blank."""
    held = _frame({"2026-09-18": 119.7})
    merged, retained, _ = F.merge_series(held, _frame({"2026-09-18": None}),
                                         as_of=date(2026, 9, 19))
    assert _closes(merged) == {"2026-09-18": 119.7}
    assert retained[date(2026, 9, 18)].first_seen == date(2026, 9, 18)


def test_a_held_blank_is_filled_by_a_real_close():
    merged, retained, corrections = F.merge_series(
        _frame({"2026-09-18": None}), _frame({"2026-09-18": 119.7}),
        as_of=date(2026, 9, 19))
    assert _closes(merged) == {"2026-09-18": 119.7}
    assert not retained and corrections == ()


# --- (c) a differing close IS a correction and applies ---------------------

def test_a_correction_that_crosses_no_level_applies_and_is_reported():
    merged, _, corrections = F.merge_series(
        _frame({"2026-09-18": 119.7}), _frame({"2026-09-18": 119.9}),
        levels={"stop": 112.0, "MBP": 51.73}, as_of=date(2026, 9, 19))
    assert _closes(merged) == {"2026-09-18": 119.9}
    assert len(corrections) == 1 and corrections[0].applied
    line = corrections[0].line()
    assert "119.7000" in line and "119.9000" in line and "2026-09-18" in line


# --- (d) one that crosses a level does not apply silently ------------------

@pytest.mark.parametrize("incoming", [110.0, 112.0])
def test_a_correction_across_a_stop_is_refused_and_the_held_close_stands(incoming):
    merged, _, corrections = F.merge_series(
        _frame({"2026-09-18": 119.7}), _frame({"2026-09-18": incoming}),
        levels={"stop": 112.0}, as_of=date(2026, 9, 19))
    assert _closes(merged) == {"2026-09-18": 119.7}      # held stands
    assert corrections[0].applied is False
    assert corrections[0].crossed == ("stop", 112.0)


def test_a_correction_that_un_crosses_an_mbp_is_refused_too():
    """The direction that matters most: a revision that quietly lifts a close
    back ABOVE the buy line."""
    _, _, corrections = F.merge_series(
        _frame({"2026-09-18": 82.0}), _frame({"2026-09-18": 85.0}),
        levels={"MBP": 83.87}, as_of=date(2026, 9, 19))
    assert corrections[0].applied is False
    assert corrections[0].crossed == ("MBP", 83.87)


# --- (e) the mark, and it survives the round trip --------------------------

def test_the_retention_mark_is_written_read_and_kept_across_runs(tmp_path):
    held = _frame({"2026-09-17": 123.8, "2026-09-18": 119.7})
    F.write_cache(tmp_path, "LIAB.ST", held, datetime(2026, 9, 18, 22, 30))
    # the vendor now omits both rows, two nights running
    for day in (19, 20):
        merged, retained, _ = F.write_cache(
            tmp_path, "LIAB.ST", _frame({"2026-09-16": 123.4}),
            datetime(2026, 9, day, 22, 30))
    assert _closes(merged)["2026-09-18"] == 119.7
    marks = F.read_retained(tmp_path, "LIAB.ST")      # keyed by DATE, as the merge is
    assert marks[date(2026, 9, 18)].first_seen == date(2026, 9, 18)
    assert marks[date(2026, 9, 18)].since == date(2026, 9, 19)   # not moved by night 2
    assert "RETAINED" in marks[date(2026, 9, 18)].line().upper()


# --- (g) no write path replaces a file of dated rows wholesale -------------

def test_only_one_writer_of_a_cached_series_exists():
    import inspect
    from pathlib import Path
    src = Path(inspect.getfile(F)).read_text()
    code = [l for l in src.splitlines()
            if ".to_csv(" in l and not l.strip().startswith("#")]
    assert code == ["    merged.to_csv(csv_path)"], code
    assert "merged" in inspect.getsource(F.write_cache)


# --- the exit test a holding must have (owner, 2026-09-20) -----------------

def test_a_held_entry_with_no_bull_is_REFUSED_where_the_name_becomes_held():
    """C4 / E42 run the exit against FV_bull -- that is how LIAB.ST's exit
    was decided on 2026-09-19. The gate sits in the LOADER, not in the
    assessment: a blocker suppresses every verdict, and silencing a
    holding's STOP to enforce a bull would be the failure it prevents."""
    from vss.config import ConfigError, parse_watchlist
    held = {"ticker": "SAP.DE", "name": "SAP SE", "currency": "EUR",
            "status": "HELD", "fv_base": 140.3746, "tier": 1}
    with pytest.raises(ConfigError) as exc:
        parse_watchlist({"tickers": [dict(held)]})
    assert "fv_bull" in str(exc.value) and "C4 / E42" in str(exc.value)
    (entry,) = parse_watchlist({"tickers": [dict(held, fv_bull=175.42)]})
    assert entry.fv_bull == 175.42


def test_the_bull_is_only_required_of_a_holding():
    from vss.config import parse_watchlist
    (entry,) = parse_watchlist({"tickers": [
        {"ticker": "GDDY", "name": "GoDaddy", "currency": "USD",
         "status": "WATCH-PRICED", "fv_base": 129.03, "tier": 3}]})
    assert entry.fv_bull is None


def test_every_holding_on_the_shipped_watchlist_carries_its_bull():
    """LIAB.ST was sold on 2026-09-21 and the watchlist now carries NO held
    name, so this is vacuous today -- and it is the loader, not this test,
    that enforces the gate: `config.load_watchlist` refuses status HELD
    without `fv_bull`."""
    from pathlib import Path
    from vss.config import load_watchlist
    held = [e for e in load_watchlist(Path("config/watchlist.yaml"))
            if e.status == "HELD"]
    assert all(e.fv_bull is not None for e in held)


def test_the_retained_mark_survives_a_CACHE_SERVED_run(tmp_path):
    """E122(e) says the mark prints wherever the close appears. The marks
    were keyed by STRING when read back and by DATE when merged, and
    `build_row` looks them up by date -- so on a cache-served run (offline,
    or after a failed live fetch) the mark silently vanished. Found
    2026-09-20 while printing an inventory."""
    from datetime import datetime as dt
    held = _frame({"2026-09-17": 123.8, "2026-09-18": 119.7})
    F.write_cache(tmp_path, "LIAB.ST", held, dt(2026, 9, 18, 22, 30))
    F.write_cache(tmp_path, "LIAB.ST", _frame({"2026-09-16": 123.4}),
                  dt(2026, 9, 19, 22, 30))
    offline = F.get_history("LIAB.ST", tmp_path, now=dt(2026, 9, 20, 22, 30),
                            allow_network=False, write=False)
    assert set(offline.retained) == {date(2026, 9, 17), date(2026, 9, 18)}
    assert offline.retained[date(2026, 9, 18)].first_seen == date(2026, 9, 18)
