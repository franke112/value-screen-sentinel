"""Cache behaviour (SCOPE 2): an outage must degrade to stale data, not no data."""

from datetime import date, datetime, timedelta

import pandas as pd
import pytest

from vss import fetch as F
from vss import metrics as M


def sample_frame(rows: int = 30, end: date = date(2026, 8, 20), tz: str | None = "Europe/Stockholm"):
    index = pd.to_datetime([end - timedelta(days=rows - 1 - i) for i in range(rows)])
    if tz:
        index = index.tz_localize(tz)
    return pd.DataFrame(
        {"Open": [100.0] * rows, "Close": [100.0] * rows, "Volume": [1000.0] * rows},
        index=index,
    )


# --- the DST regression ---------------------------------------------------


def test_index_dates_handles_mixed_utc_offsets():
    """A cached series spanning a DST change has mixed offsets; it must parse.

    pd.to_datetime raises ValueError on this input, and converting to UTC
    would shift a midnight close onto the previous calendar day.
    """
    mixed = ["2026-03-28 00:00:00+01:00", "2026-03-30 00:00:00+02:00"]
    assert M.index_dates(mixed) == [date(2026, 3, 28), date(2026, 3, 30)]


def test_high_52w_survives_a_mixed_offset_index():
    closes = pd.Series(
        [100.0, 120.0],
        index=["2026-03-28 00:00:00+01:00", "2026-03-30 00:00:00+02:00"],
    )
    assert M.high_52w(closes, date(2026, 8, 20)) == pytest.approx(120.0)


def test_cache_round_trip_across_a_dst_change(tmp_path):
    """Write a live frame that spans a DST boundary, read it back, compute."""
    end = date(2026, 4, 15)
    frame = sample_frame(rows=40, end=end)  # spans the late-March change
    F.write_cache(tmp_path, "DST.ST", frame, datetime(2026, 4, 15, 22, 30))

    restored, fetched_at = F.read_cache(tmp_path, "DST.ST")
    assert restored is not None
    assert fetched_at == datetime(2026, 4, 15, 22, 30)

    computed = M.compute(restored, end)
    assert computed.last_close == pytest.approx(100.0)
    assert computed.last_close_date == end


# --- cache mechanics ------------------------------------------------------


def test_write_then_read_preserves_closes(tmp_path):
    F.write_cache(tmp_path, "AAA", sample_frame(), datetime(2026, 8, 20, 22, 30))
    restored, _ = F.read_cache(tmp_path, "AAA")
    assert list(restored["Close"]) == [100.0] * 30


def test_read_cache_missing_is_none(tmp_path):
    assert F.read_cache(tmp_path, "NOPE") == (None, None)


def test_corrupt_cache_is_not_silently_reused(tmp_path):
    csv_path, _ = F.cache_paths(tmp_path, "BAD")
    tmp_path.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("this is not a csv index\x00\x01")
    frame, _ = F.read_cache(tmp_path, "BAD")
    assert frame is None


def test_safe_name_keeps_real_tickers_readable():
    assert F.safe_name("VOLV-B.ST") == "VOLV-B.ST"
    assert F.safe_name("BRK-B") == "BRK-B"
    assert F.safe_name("A/B") == "A_B"


# --- fallback behaviour ---------------------------------------------------


def test_outage_falls_back_to_cache(tmp_path, monkeypatch):
    F.write_cache(tmp_path, "AAA", sample_frame(), datetime(2026, 8, 20, 22, 30))

    def boom(ticker, period=F.DEFAULT_PERIOD):
        raise RuntimeError("simulated yfinance outage")

    monkeypatch.setattr(F, "fetch_live", boom)
    result = F.get_history("AAA", tmp_path, now=datetime(2026, 8, 21, 22, 30))

    assert result.ok
    assert result.source == F.SOURCE_CACHE
    assert result.degraded
    assert "simulated yfinance outage" in result.error


def test_outage_without_cache_is_an_error_not_a_silent_drop(tmp_path, monkeypatch):
    def boom(ticker, period=F.DEFAULT_PERIOD):
        raise RuntimeError("simulated yfinance outage")

    monkeypatch.setattr(F, "fetch_live", boom)
    result = F.get_history("AAA", tmp_path, now=datetime(2026, 8, 21, 22, 30))

    assert not result.ok
    assert result.source == F.SOURCE_NONE
    assert result.error is not None


def test_dry_run_does_not_write_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "fetch_live", lambda t, period=F.DEFAULT_PERIOD: sample_frame())
    F.get_history("AAA", tmp_path, now=datetime(2026, 8, 20, 22, 30), write=False)
    csv_path, _ = F.cache_paths(tmp_path, "AAA")
    assert not csv_path.exists()


def test_normal_run_does_write_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "fetch_live", lambda t, period=F.DEFAULT_PERIOD: sample_frame())
    F.get_history("AAA", tmp_path, now=datetime(2026, 8, 20, 22, 30), write=True)
    csv_path, meta_path = F.cache_paths(tmp_path, "AAA")
    assert csv_path.exists() and meta_path.exists()


def test_stale_cache_still_trips_the_staleness_gate(tmp_path, monkeypatch):
    """Serving from cache must never make old data look fresh.

    The gate reads the newest close DATE out of the series, not the cache
    file's fetch timestamp.
    """
    from vss.rules import STALE_DATA, assess

    old_end = date(2026, 8, 1)
    F.write_cache(tmp_path, "AAA", sample_frame(end=old_end), datetime(2026, 8, 20, 22, 30))

    def boom(ticker, period=F.DEFAULT_PERIOD):
        raise RuntimeError("outage")

    monkeypatch.setattr(F, "fetch_live", boom)
    result = F.get_history("AAA", tmp_path, now=datetime(2026, 8, 20, 22, 30))
    computed = M.compute(result.frame, date(2026, 8, 20))

    verdict = assess(
        ticker="AAA", status="WATCH-GATED", last_close=computed.last_close,
        last_close_date=computed.last_close_date, drawdown=computed.drawdown,
        fv_base=100.0, tier=2, stop_price=50.0, catalyst_date=None,
        catalyst_resolved=None, catalyst_event=None, as_of=date(2026, 8, 20),
    )
    assert verdict.blocked
    assert STALE_DATA in {b.code for b in verdict.blockers}
    assert verdict.verdicts == ()
