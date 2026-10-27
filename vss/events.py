"""E140(3)-(4) and E140.1(3): the EVENTS LEDGER a strike stands on.

`reference/events/<TICKER>.yaml` lists every acquisition, divestiture and
partnership contribution after the basis balance sheet, or states that none
was found, and records what was searched and when. **No value is struck
without one** (E140(4)): CENTA's strike of 2026-10-20 missed four deals,
one of them announced the day before.

THE CUT (E140.1(3)). The bridge rolls to the latest filed balance sheet. A
deal CLOSED on or before that date is already in it -- its cash paid is out
of cash, its debt is in borrowings -- and is not added again. A deal closed
after it, or not yet closed, enters the bridge at its price.

THE PRICE. `low` and `high` are what the deal ADDS TO NET DEBT, in the
store's money unit: cash paid, an earn-out at its maximum, a put on a
retained stake pro rata, LESS cash received. A divestiture is negative. An
undisclosed price is a range and is never left out. The value is struck at
the HIGH end -- the most debt, the lower value -- and printed at both.

THE AGE. A ledger older than `LEDGER_MAX_AGE_DAYS` at strike time refuses:
a ledger states what was searched on its date, and a deal announced after
it is exactly what E140 was ruled to stop missing.

Nothing here fetches or searches. It reads a file a session wrote after
searching, and refuses one that does not say enough.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVENTS_DIR = PROJECT_ROOT / "reference" / "events"

#: E140(4): how old a ledger may be on the day of a strike. A week: the
#: CENTA strike of 2026-10-20 missed Burpee, announced on 2026-10-19.
LEDGER_MAX_AGE_DAYS = 7

#: The money units a ledger may state, the store's own vocabulary.
LEDGER_UNITS = ("whole", "thousands", "millions", "billions")


class EventsError(Exception):
    """The ledger is absent, stale, or does not say enough to strike on."""


@dataclass(frozen=True)
class Deal:
    """One deal after the basis, as the ledger states it."""

    name: str
    status: str
    #: The day it CLOSED, or None where it has not (pending, agreed, or a
    #: group whose closings are not all confirmed). None is ALWAYS in the
    #: bridge: counting a closed deal twice errs toward more debt, leaving
    #: an open one out errs the other way.
    closed: date | None
    low: float
    high: float
    #: The acquired business's FCF entering FCF0 -- only where the issuer
    #: has filed figures for it (E140(3)); zero otherwise, and the zero is
    #: named by the ledger's source line.
    fcf: float
    date_text: str
    source: str

    def in_bridge(self, cut: date) -> bool:
        """Whether the deal is NOT already in the balance sheet of `cut`."""
        return self.closed is None or self.closed > cut


@dataclass(frozen=True)
class Ledger:
    ticker: str
    path: str
    dated: date
    money_unit: str
    deals: tuple[Deal, ...]
    none_found: bool
    searched: tuple[str, ...]
    notes: str = ""

    def in_bridge(self, cut: date) -> tuple[Deal, ...]:
        return tuple(d for d in self.deals if d.in_bridge(cut))


def _date(value: Any, where: str) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise EventsError(f"{where} must be a YYYY-MM-DD date or null, got "
                          f"{value!r}") from exc


def load_ledger(ticker: str, *, directory: Path = EVENTS_DIR) -> Ledger:
    """Read and validate one ledger. Raises EventsError, never defaults."""
    path = Path(directory) / f"{ticker}.yaml"
    if not path.exists():
        raise EventsError(
            f"{ticker}: NO EVENTS LEDGER at {path} -- E140(4) refuses to "
            f"strike a name whose post-basis deals have not been listed. "
            f"Search the issuer's press releases, every 8-K/10-Q/10-K (or "
            f"the local equivalent) since the basis, and the news, and "
            f"write the ledger with what was found or `none_found: true`")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    where = str(path)
    dated = _date(raw.get("dated"), f"{where}: dated")
    if dated is None:
        raise EventsError(f"{where}: `dated` is required -- a ledger states "
                          f"what was searched ON A DATE")
    unit = raw.get("money_unit")
    if unit not in LEDGER_UNITS:
        raise EventsError(f"{where}: money_unit must be one of "
                          f"{'|'.join(LEDGER_UNITS)}, got {unit!r}")
    searched = tuple(raw.get("searched") or ())
    if not searched:
        raise EventsError(f"{where}: `searched` is empty -- E140(4) records "
                          f"WHAT was searched, so a reader can repeat it")
    deals = []
    for i, d in enumerate(raw.get("deals") or ()):
        w = f"{where}: deal #{i + 1}"
        for key in ("name", "status", "low", "high", "source"):
            if d.get(key) in (None, ""):
                raise EventsError(f"{w}: `{key}` is required")
        if "closed" not in d:
            raise EventsError(
                f"{w}: `closed` is required -- the day it closed, or null "
                f"where it has not. The cut at the balance-sheet date turns "
                f"on it (E140.1(3))")
        closed = _date(d.get("closed"), f"{w}: closed")
        status = str(d["status"]).strip().lower()
        if status == "closed" and closed is None:
            raise EventsError(f"{w}: status `closed` with no `closed` date")
        low, high = float(d["low"]), float(d["high"])
        if low > high:
            raise EventsError(f"{w}: low {low} is above high {high} -- both "
                              f"are what the deal ADDS to net debt")
        deals.append(Deal(name=str(d["name"]), status=status, closed=closed,
                          low=low, high=high, fcf=float(d.get("fcf") or 0.0),
                          date_text=str(d.get("date", "")),
                          source=str(d["source"])))
    none_found = bool(raw.get("none_found"))
    if not deals and not none_found:
        raise EventsError(f"{where}: no deals and `none_found` is not true -- "
                          f"a ledger states one or the other")
    if deals and none_found:
        raise EventsError(f"{where}: deals listed AND `none_found: true`")
    try:
        shown = str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        shown = str(path)
    return Ledger(ticker=str(raw.get("ticker") or ticker), path=shown,
                  dated=dated, money_unit=unit, deals=tuple(deals),
                  none_found=none_found, searched=searched,
                  notes=str(raw.get("notes") or ""))


def check_fresh(ledger: Ledger, as_of: date,
                max_age_days: int = LEDGER_MAX_AGE_DAYS) -> None:
    """Refuse a ledger older than the limit on the strike's day."""
    age = (as_of - ledger.dated).days
    if age > max_age_days:
        raise EventsError(
            f"{ledger.ticker}: the events ledger is dated "
            f"{ledger.dated.isoformat()}, {age} days before {as_of.isoformat()} "
            f"-- past E140(4)'s {max_age_days}. Search again (press releases, "
            f"every filing since the last sweep, the news), update the "
            f"ledger and its `dated`, then strike")
    if age < 0:
        raise EventsError(f"{ledger.ticker}: the ledger is dated after the "
                          f"strike ({ledger.dated} > {as_of})")
