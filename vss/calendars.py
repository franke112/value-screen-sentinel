"""Exchange calendars for the staleness gate (FRAMEWORK-EDITS E47 / C3).

`rules.trading_days_between` counts weekdays and takes the exchange's closed
days from the caller -- rules.py does no I/O and knows no calendar. This
module is the caller's supply: the universe row's `marknad` string is
mapped to an ISO 10383 MIC in `config/exchange_calendars.yaml`, and the
`exchange_calendars` package builds the session calendar for that MIC from
the exchange's own holiday rules, offline, for past and future dates alike.

Measured cost of NOT having this (SCREENER-REVIEW-3 Part 10): Christmas Eve
to Boxing Day is three closed weekdays on seven of the eleven markets, so a
3-session gate counted on Monday-to-Friday blocked after ONE real session and
removed a whole market on value on the first morning after; Easter and New
Year collapsed it to two on every European exchange.

THE FALLBACK IS NAMED, NEVER SILENT. A market the config does not map is
measured on the naive count, and `closed_weekdays` returns None so the
caller can say so in its report. A date outside the calendar's built range
is treated the same way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Mapping

from .universe import UniverseError

CALENDARS_PATH = Path("config/exchange_calendars.yaml")


@dataclass(frozen=True)
class MarketCalendars:
    """`marknad` -> MIC, and the closed weekdays each market had in a window."""

    mics: Mapping[str, str]
    source: str = ""
    #: ticker suffix -> market, for `vss run` (a watchlist entry has no market)
    suffixes: Mapping[str, str] = field(default_factory=dict)

    def mic(self, market: str | None) -> str | None:
        return self.mics.get(market or "")

    def market_of_ticker(self, ticker: str) -> str | None:
        """The market a watchlist ticker's suffix names, or None if unmapped.

        'LIAB.ST' -> 'Stockholm'; 'GDDY' (no suffix) -> the empty key's market.
        """
        suffix = ticker.rsplit(".", 1)[1].upper() if "." in ticker else ""
        return self.suffixes.get(suffix)

    def closed_weekdays(self, market: str | None, start: date, end: date
                        ) -> frozenset[date] | None:
        """Weekdays in (``start``, ``end``] on which ``market`` held NO session.

        The window is the one `rules.trading_days_between` counts over --
        the day after ``start`` through ``end`` inclusive -- so the result
        can be handed to it as ``holidays`` unchanged. None when the market
        is not mapped, or when the calendar cannot answer for the window:
        DATA MISSING about the calendar, and the caller says so.
        """
        mic = self.mic(market)
        if mic is None or end <= start:
            return frozenset() if mic is not None else None
        sessions = _sessions(mic, start, end)
        if sessions is None:
            return None
        closed = []
        day = start + timedelta(days=1)
        while day <= end:
            if day.weekday() < 5 and day not in sessions:
                closed.append(day)
            day += timedelta(days=1)
        return frozenset(closed)


@lru_cache(maxsize=None)
def _calendar(mic: str):
    import exchange_calendars

    return exchange_calendars.get_calendar(mic)


def _sessions(mic: str, start: date, end: date) -> frozenset[date] | None:
    """Session dates in [start, end] for ``mic``, or None if out of range."""
    import pandas as pd

    try:
        calendar = _calendar(mic)
        index = calendar.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end))
    except Exception:  # noqa: BLE001 - an unknown MIC or a date past the built range
        return None
    return frozenset(stamp.date() for stamp in index)


def load_market_calendars(path: Path = CALENDARS_PATH) -> MarketCalendars:
    """Read the market -> MIC map. A missing file is an error, not silence."""
    import yaml

    if not path.exists():
        raise UniverseError(f"{path}: no exchange calendar config")
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    markets = document.get("markets") or {}
    if not isinstance(markets, Mapping):
        raise UniverseError(f"{path.name}: 'markets' must be a mapping of marknad -> MIC")
    mics: dict[str, str] = {}
    for market, mic in markets.items():
        if not market or not mic:
            raise UniverseError(f"{path.name}: empty market or MIC in {market!r}: {mic!r}")
        mics[str(market)] = str(mic)
    suffixes_doc = document.get("suffixes") or {}
    if not isinstance(suffixes_doc, Mapping):
        raise UniverseError(f"{path.name}: 'suffixes' must be a mapping of suffix -> market")
    suffixes = {str(k).upper(): str(v) for k, v in suffixes_doc.items()}
    for suffix, market in suffixes.items():
        if market not in mics:
            raise UniverseError(f"{path.name}: suffix {suffix!r} names {market!r}, "
                                f"which is not under 'markets'")
    return MarketCalendars(mics=mics, source=str(path), suffixes=suffixes)
