"""Batched price retrieval for the whole screening universe (screener step 1).

Two-step fetching is the architecture of the screener. Bulk price history is
cheap and batchable; fundamentals are one call per ticker and do not scale to
thirteen thousand names. So step 1 prices EVERYTHING, and only the survivors
of the price filter ever cost a fundamentals call.

Every ticker leaves this module with a STATUS, and the four are kept apart on
purpose:

    OK         a usable series arrived
    THROTTLED  the request was refused for rate reasons -- retry later, the
               ticker is probably fine
    NO_DATA    the request succeeded and the ticker was not in it -- the
               symbol mapping is probably wrong
    STALE      a series arrived but its newest close is older than the gate
               allows as of the run date

THROTTLED and NO_DATA look identical in a naive implementation, and lumping
them together is how a screener quietly shrinks its own universe on a bad
network day. They have different fixes -- wait, versus repair the mapping --
so they get different names.

STALE is not a fetch outcome at all; it is decided AFTER the data arrives, by
``rules.stale_close_blocker``, which is the same staleness gate ``vss run``
uses. It is imported, never reimplemented.

No clock reads: ``as_of`` is a parameter, and both the downloader and the
sleeper are injectable so batching and backoff can be tested without a
network and without waiting.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Iterable, Mapping, Sequence

import pandas as pd

from .fetch import AUTO_ADJUST, DEFAULT_PERIOD
# ``truncate`` comes from metrics so there is ONE truncation, used both when a
# snapshot is written and whenever it is measured. yfinance always answers with
# the latest session it has, whatever date was asked about; without this,
# re-running --asof 2026-08-21 on the following Monday would quietly ingest
# Monday and the snapshot would stop being a replay of Friday.
from .metrics import index_dates, truncate
from .rules import stale_close_blocker
from .universe import ON_MISSING, ON_VALUE, Tally

log = logging.getLogger(__name__)

STATUS_OK = "OK"
STATUS_THROTTLED = "THROTTLED"
STATUS_NO_DATA = "NO_DATA"
STATUS_STALE = "STALE"
ALL_STATUSES = (STATUS_OK, STATUS_THROTTLED, STATUS_NO_DATA, STATUS_STALE)

#: yfinance is happiest with a few dozen symbols per request. Bigger batches
#: fail as a unit, which costs more on a retry than they save on a good run.
BATCH_SIZE = 50

#: Attempts per batch, first try included.
MAX_ATTEMPTS = 4
BACKOFF_BASE_SECONDS = 2.0
BACKOFF_CAP_SECONDS = 60.0
#: Politeness pause between successful batches.
INTER_BATCH_SECONDS = 0.5

#: Substrings that identify a refusal as rate limiting rather than a bad
#: symbol. Matched case-insensitively against the exception text.
THROTTLE_MARKERS = (
    "429", "too many requests", "rate limit", "rate-limit", "ratelimit",
    "throttl", "temporarily blocked", "try again later",
)


@dataclass(frozen=True)
class TickerFetch:
    ticker: str
    status: str
    rows: int = 0
    first_date: date | None = None
    last_date: date | None = None
    attempts: int = 0
    error: str | None = None
    batch: int = 0

    @property
    def ok(self) -> bool:
        return self.status == STATUS_OK


@dataclass
class FetchOutcome:
    frames: dict[str, pd.DataFrame] = field(default_factory=dict)
    statuses: list[TickerFetch] = field(default_factory=list)
    tally: Tally = field(default_factory=lambda: Tally("price_fetch"))

    def by_status(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {s: [] for s in ALL_STATUSES}
        for item in self.statuses:
            out.setdefault(item.status, []).append(item.ticker)
        return out


def batches(tickers: Sequence[str], size: int = BATCH_SIZE) -> list[list[str]]:
    """Split into fixed-size batches, order preserved, no ticker lost."""
    if size < 1:
        raise ValueError("batch size must be at least 1")
    return [list(tickers[i : i + size]) for i in range(0, len(tickers), size)]


def is_throttle(error: BaseException | str) -> bool:
    text = str(error).lower()
    return any(marker in text for marker in THROTTLE_MARKERS)


def backoff_delay(
    attempt: int,
    base: float = BACKOFF_BASE_SECONDS,
    cap: float = BACKOFF_CAP_SECONDS,
) -> float:
    """Exponential backoff, deterministic on purpose.

    No jitter: a single-process screener has nothing to de-synchronise from,
    and a deterministic delay is one a test can assert on exactly.
    """
    if attempt < 1:
        raise ValueError("attempt is 1-based")
    return min(cap, base * (2 ** (attempt - 1)))


def default_download(tickers: Sequence[str], period: str) -> pd.DataFrame:
    """The real yfinance call. Replaced wholesale in tests."""
    import yfinance as yf

    return yf.download(
        list(tickers),
        period=period,
        interval="1d",
        auto_adjust=AUTO_ADJUST,
        group_by="ticker",
        threads=False,
        progress=False,
        actions=False,
    )


def split_frame(frame: pd.DataFrame | None, tickers: Sequence[str]) -> dict[str, pd.DataFrame]:
    """Per-ticker frames out of a yfinance multi-ticker response.

    yfinance returns MultiIndex columns for several tickers and flat columns
    for one, and a ticker it could not resolve is simply ABSENT -- or present
    as an all-NaN block. Both are treated as "did not arrive"; the caller
    reconciles against what it asked for.

    Rows with no Close are dropped. Yahoo does publish a session with open,
    high, low and volume but a NULL close -- Stockholm's 2026-08-21 is one --
    and keeping such a row would date the series a day later than its newest
    usable price, which would make the staleness gate answer for a close that
    does not exist. metrics.compute drops them anyway; they never reach a
    snapshot.
    """
    out: dict[str, pd.DataFrame] = {}
    if frame is None or len(frame) == 0:
        return out
    if isinstance(frame.columns, pd.MultiIndex):
        available = set(frame.columns.get_level_values(0))
        for ticker in tickers:
            if ticker not in available:
                continue
            part = frame[ticker]
            if "Close" not in part.columns:
                continue
            part = part[part["Close"].notna()]
            if len(part):
                out[ticker] = part
        return out
    if len(tickers) == 1 and "Close" in frame.columns:
        part = frame[frame["Close"].notna()]
        if len(part):
            out[tickers[0]] = part
    return out


def fetch_batch(
    tickers: Sequence[str],
    *,
    as_of: date,
    period: str = DEFAULT_PERIOD,
    download: Callable[[Sequence[str], str], pd.DataFrame] = default_download,
    sleep: Callable[[float], None] = time.sleep,
    max_attempts: int = MAX_ATTEMPTS,
    batch_index: int = 0,
    holidays_of: Mapping[str, frozenset[date]] | None = None,
) -> tuple[dict[str, pd.DataFrame], list[TickerFetch]]:
    """One batch, with retry and backoff. Never raises; always accounts for
    every ticker it was given.

    ``holidays_of`` maps a ticker to its exchange's closed weekdays in the
    window the staleness gate counts over (E47); a ticker absent from it is
    counted Monday to Friday, as before 2026-08-26."""
    attempts, last_error, throttled = 0, None, False
    frames: dict[str, pd.DataFrame] = {}

    while attempts < max_attempts:
        attempts += 1
        try:
            raw = download(list(tickers), period)
            frames = split_frame(raw, tickers)
            last_error, throttled = None, False
            break
        except Exception as exc:  # noqa: BLE001 - classified, then retried
            last_error = f"{type(exc).__name__}: {exc}"
            throttled = is_throttle(exc)
            if attempts >= max_attempts:
                break
            delay = backoff_delay(attempts)
            log.warning(
                "batch %d attempt %d failed (%s); retrying in %.1fs",
                batch_index, attempts, last_error, delay,
            )
            sleep(delay)

    statuses: list[TickerFetch] = []
    for ticker in tickers:
        frame = frames.get(ticker)
        if frame is not None:
            frame = truncate(frame, as_of)
        if frame is None or len(frame) == 0:
            # Truncation can empty a frame that arrived non-empty. Drop it,
            # or the untruncated original would survive into the snapshot and
            # --asof would leak future closes.
            frames.pop(ticker, None)
            # Absent from a response we DID receive means the symbol is
            # wrong; absent because the response never came, and the refusal
            # looked like rate limiting, means the symbol is probably fine.
            if last_error is not None:
                status = STATUS_THROTTLED if throttled else STATUS_NO_DATA
            else:
                status = STATUS_NO_DATA
            statuses.append(
                TickerFetch(
                    ticker=ticker, status=status, attempts=attempts,
                    error=last_error
                    or ("not present in the response and no error was raised"
                        if frame is None else
                        f"every close is dated after as_of {as_of.isoformat()}"),
                    batch=batch_index,
                )
            )
            continue

        dates = index_dates(frame.index)
        last_date = max(dates)
        stale = stale_close_blocker(
            last_date, as_of,
            holidays=(holidays_of or {}).get(ticker, frozenset()))
        statuses.append(
            TickerFetch(
                ticker=ticker,
                status=STATUS_STALE if stale else STATUS_OK,
                rows=len(frame),
                first_date=min(dates),
                last_date=last_date,
                attempts=attempts,
                error=str(stale) if stale else None,
                batch=batch_index,
            )
        )
        frames[ticker] = frame

    return {t: f for t, f in frames.items() if t in tickers and len(f)}, statuses


def fetch_universe(
    tickers: Sequence[str],
    *,
    as_of: date,
    period: str = DEFAULT_PERIOD,
    batch_size: int = BATCH_SIZE,
    download: Callable[[Sequence[str], str], pd.DataFrame] = default_download,
    sleep: Callable[[float], None] = time.sleep,
    max_attempts: int = MAX_ATTEMPTS,
    inter_batch_seconds: float = INTER_BATCH_SECONDS,
    on_batch: Callable[[int, int, int], None] | None = None,
    holidays_of: Mapping[str, frozenset[date]] | None = None,
) -> FetchOutcome:
    """Price the whole universe in batches. Every ticker gets a status."""
    outcome = FetchOutcome()
    outcome.tally = Tally("price_fetch", count_in=len(tickers))
    groups = batches(tickers, batch_size)

    for index, group in enumerate(groups, start=1):
        frames, statuses = fetch_batch(
            group, as_of=as_of, period=period, download=download, sleep=sleep,
            max_attempts=max_attempts, batch_index=index, holidays_of=holidays_of,
        )
        outcome.frames.update(frames)
        outcome.statuses.extend(statuses)
        if on_batch:
            on_batch(index, len(groups), len(group))
        if index < len(groups) and inter_batch_seconds:
            sleep(inter_batch_seconds)

    for item in outcome.statuses:
        if item.status == STATUS_OK:
            continue
        if item.status == STATUS_STALE:
            # A value we HAVE, judged too old. That is a rejection on a
            # value, not on the absence of one.
            outcome.tally.reject(ON_VALUE, "newest close older than the staleness gate")
        else:
            outcome.tally.reject(ON_MISSING, f"no usable series ({item.status})")
    outcome.tally.count_out = sum(1 for s in outcome.statuses if s.status == STATUS_OK)
    return outcome


def status_counts(statuses: Iterable[TickerFetch]) -> dict[str, int]:
    counts = {status: 0 for status in ALL_STATUSES}
    for item in statuses:
        counts[item.status] = counts.get(item.status, 0) + 1
    return counts


def coverage_by_market(
    statuses: Iterable[TickerFetch], market_of: Mapping[str, str]
) -> dict[str, dict[str, int]]:
    """Fetch-status distribution per market, as ``--snapshot-only`` reports it."""
    table: dict[str, dict[str, int]] = {}
    for item in statuses:
        market = market_of.get(item.ticker, "UNKNOWN")
        row = table.setdefault(market, {status: 0 for status in ALL_STATUSES})
        row[item.status] = row.get(item.status, 0) + 1
    return table
