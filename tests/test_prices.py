"""Batched price retrieval: batching, backoff, retry, and the four statuses."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from vss.prices import (
    ALL_STATUSES,
    BACKOFF_BASE_SECONDS,
    STATUS_NO_DATA,
    STATUS_OK,
    STATUS_STALE,
    STATUS_THROTTLED,
    backoff_delay,
    batches,
    coverage_by_market,
    fetch_batch,
    fetch_universe,
    is_throttle,
    split_frame,
    status_counts,
    truncate,
)

AS_OF = date(2026, 8, 21)


def frame_for(ticker: str, days: int = 5, last: date = AS_OF, close=100.0) -> pd.DataFrame:
    index = pd.to_datetime([last - pd.Timedelta(days=days - 1 - i) for i in range(days)])
    return pd.DataFrame(
        {
            "Open": [close] * days,
            "High": [close] * days,
            "Low": [close] * days,
            "Close": [close] * days,
            "Volume": [1000.0] * days,
        },
        index=index,
    )


def multi(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(frames, axis=1, sort=False)


def fake_download(available: dict[str, pd.DataFrame], calls: list | None = None):
    def download(tickers, period):
        if calls is not None:
            calls.append(list(tickers))
        present = {t: available[t] for t in tickers if t in available}
        if not present:
            return pd.DataFrame()
        return multi(present)

    return download


# --- batching --------------------------------------------------------------


def test_batches_preserve_order_and_lose_nothing():
    tickers = [f"T{i}" for i in range(125)]
    groups = batches(tickers, 50)
    assert [len(g) for g in groups] == [50, 50, 25]
    assert [t for g in groups for t in g] == tickers


def test_batch_size_must_be_positive():
    with pytest.raises(ValueError):
        batches(["A"], 0)


def test_fetch_universe_batches_the_request(monkeypatch):
    tickers = [f"T{i}" for i in range(7)]
    available = {t: frame_for(t) for t in tickers}
    calls: list[list[str]] = []
    outcome = fetch_universe(
        tickers, as_of=AS_OF, batch_size=3,
        download=fake_download(available, calls), sleep=lambda _: None,
    )
    assert [len(c) for c in calls] == [3, 3, 1]
    assert len(outcome.frames) == 7
    assert outcome.tally.count_in == 7
    assert outcome.tally.count_out == 7


# --- backoff ---------------------------------------------------------------


def test_backoff_is_exponential_and_capped():
    assert backoff_delay(1) == BACKOFF_BASE_SECONDS
    assert backoff_delay(2) == BACKOFF_BASE_SECONDS * 2
    assert backoff_delay(3) == BACKOFF_BASE_SECONDS * 4
    assert backoff_delay(20) == 60.0


def test_backoff_rejects_a_zero_attempt():
    with pytest.raises(ValueError):
        backoff_delay(0)


def test_a_failing_batch_is_retried_with_growing_delays():
    slept: list[float] = []
    attempts = {"n": 0}

    def download(tickers, period):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("HTTP 429 Too Many Requests")
        return multi({t: frame_for(t) for t in tickers})

    frames, statuses = fetch_batch(
        ["A"], as_of=AS_OF, download=download, sleep=slept.append, max_attempts=4
    )
    assert slept == [2.0, 4.0]
    assert statuses[0].status == STATUS_OK
    assert statuses[0].attempts == 3


def test_retries_stop_at_max_attempts():
    slept: list[float] = []

    def download(tickers, period):
        raise RuntimeError("HTTP 429 Too Many Requests")

    frames, statuses = fetch_batch(
        ["A"], as_of=AS_OF, download=download, sleep=slept.append, max_attempts=3
    )
    assert len(slept) == 2
    assert statuses[0].attempts == 3
    assert statuses[0].status == STATUS_THROTTLED


# --- status classification -------------------------------------------------


@pytest.mark.parametrize(
    "text",
    ["HTTP 429", "Too Many Requests", "rate limit exceeded", "YFRateLimitError: throttled"],
)
def test_throttling_is_recognised(text):
    assert is_throttle(RuntimeError(text))


def test_a_plain_failure_is_not_throttling():
    assert not is_throttle(RuntimeError("possibly delisted; no price data found"))


def test_throttled_and_no_data_are_never_merged():
    def throttling(tickers, period):
        raise RuntimeError("HTTP 429 Too Many Requests")

    _, throttled = fetch_batch(["A"], as_of=AS_OF, download=throttling,
                               sleep=lambda _: None, max_attempts=1)
    _, absent = fetch_batch(["A"], as_of=AS_OF,
                            download=fake_download({}), sleep=lambda _: None)
    assert throttled[0].status == STATUS_THROTTLED
    assert absent[0].status == STATUS_NO_DATA


def test_a_ticker_missing_from_a_good_response_is_no_data_not_dropped():
    available = {"A": frame_for("A")}
    frames, statuses = fetch_batch(["A", "B"], as_of=AS_OF,
                                   download=fake_download(available), sleep=lambda _: None)
    assert set(frames) == {"A"}
    assert {s.ticker: s.status for s in statuses} == {"A": STATUS_OK, "B": STATUS_NO_DATA}


def test_every_requested_ticker_gets_exactly_one_status():
    tickers = [f"T{i}" for i in range(11)]
    available = {t: frame_for(t) for t in tickers[:5]}
    outcome = fetch_universe(tickers, as_of=AS_OF, batch_size=4,
                             download=fake_download(available), sleep=lambda _: None)
    assert [s.ticker for s in outcome.statuses] == tickers


def test_an_old_series_is_stale_and_that_is_a_value_rejection():
    available = {"A": frame_for("A", last=date(2026, 8, 10))}
    outcome = fetch_universe(["A"], as_of=AS_OF, download=fake_download(available),
                             sleep=lambda _: None)
    (status,) = outcome.statuses
    assert status.status == STATUS_STALE
    assert status.last_date == date(2026, 8, 10)
    assert outcome.tally.rejected_on_value == 1
    assert outcome.tally.rejected_on_missing == 0


def test_a_weekend_run_on_fridays_close_is_not_stale():
    available = {"A": frame_for("A", last=date(2026, 8, 21))}
    outcome = fetch_universe(["A"], as_of=date(2026, 8, 23),
                             download=fake_download(available), sleep=lambda _: None)
    assert outcome.statuses[0].status == STATUS_OK


def test_missing_data_statuses_are_counted_apart_from_stale():
    available = {"A": frame_for("A"), "B": frame_for("B", last=date(2026, 7, 1))}
    outcome = fetch_universe(["A", "B", "C"], as_of=AS_OF,
                             download=fake_download(available), sleep=lambda _: None)
    assert outcome.tally.rejected_on_value == 1     # B, stale
    assert outcome.tally.rejected_on_missing == 1   # C, absent
    assert outcome.tally.count_out == 1


def test_status_counts_covers_all_four():
    counts = status_counts([])
    assert set(counts) == set(ALL_STATUSES)
    assert sum(counts.values()) == 0


def test_coverage_by_market_splits_by_market():
    available = {"A.ST": frame_for("A.ST")}
    outcome = fetch_universe(["A.ST", "B.L"], as_of=AS_OF,
                             download=fake_download(available), sleep=lambda _: None)
    table = coverage_by_market(outcome.statuses, {"A.ST": "Stockholm", "B.L": "London"})
    assert table["Stockholm"][STATUS_OK] == 1
    assert table["London"][STATUS_NO_DATA] == 1


# --- asof truncation -------------------------------------------------------


def test_truncate_drops_rows_after_asof():
    frame = frame_for("A", days=5, last=date(2026, 8, 25))
    cut = truncate(frame, AS_OF)
    assert len(cut) == 1
    assert cut.index[-1].date() == date(2026, 8, 21)


def test_a_series_entirely_after_asof_is_no_data_and_leaves_no_frame():
    available = {"A": frame_for("A", days=2, last=date(2026, 9, 1))}
    frames, statuses = fetch_batch(["A"], as_of=AS_OF,
                                   download=fake_download(available), sleep=lambda _: None)
    assert frames == {}
    assert statuses[0].status == STATUS_NO_DATA


def test_asof_truncation_reaches_the_stored_frame():
    available = {"A": frame_for("A", days=10, last=date(2026, 8, 28))}
    outcome = fetch_universe(["A"], as_of=AS_OF, download=fake_download(available),
                             sleep=lambda _: None)
    assert max(d.date() for d in outcome.frames["A"].index) == AS_OF


# --- response shapes -------------------------------------------------------


def test_split_frame_handles_a_single_ticker_flat_frame():
    out = split_frame(frame_for("A"), ["A"])
    assert list(out) == ["A"]


def test_split_frame_ignores_an_empty_response():
    assert split_frame(pd.DataFrame(), ["A"]) == {}
    assert split_frame(None, ["A"]) == {}


def test_split_frame_drops_a_session_with_no_close():
    frame = frame_for("A", days=3)
    frame.iloc[-1, frame.columns.get_loc("Close")] = None
    out = split_frame(multi({"A": frame}), ["A"])
    assert len(out["A"]) == 2
    assert out["A"]["Close"].notna().all()


def test_an_all_nan_block_counts_as_absent():
    frame = frame_for("A", days=3)
    frame["Close"] = None
    assert split_frame(multi({"A": frame}), ["A"]) == {}


def test_the_fetch_time_stale_status_counts_on_the_exchange_calendar():
    """E47 / item 3: a close of 2026-12-23 read on the 30th is five weekdays
    old and three Stockholm sessions old (24th and 25th shut). The status
    a snapshot records must agree with the gate filter 1 applies later."""
    available = {"A": frame_for("A", last=date(2026, 12, 23))}
    shut = frozenset({date(2026, 12, 24), date(2026, 12, 25)})
    on_calendar = fetch_universe(["A"], as_of=date(2026, 12, 30),
                                 download=fake_download(available), sleep=lambda _: None,
                                 holidays_of={"A": shut})
    assert on_calendar.statuses[0].status == STATUS_OK
    naive = fetch_universe(["A"], as_of=date(2026, 12, 30),
                           download=fake_download(available), sleep=lambda _: None)
    assert naive.statuses[0].status == STATUS_STALE
