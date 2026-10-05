"""E97: price-watching the ranked list, once per crossing.

E94 says what it would take to VALUE a ranked name. This says **when to look
again** — and it exists because the nightly run watches only the names
already on the watchlist, so a ranked name that halved would go unnoticed
until the next weekly screen.

**IT WRITES NOTHING.** No watchlist field, no `fv_base`, no `tier`, no
`mbp`, no PIPELINE entry, no gate score. An INDICATIVE value stays
INDICATIVE however far the price falls — E94's fences are carried here
unchanged and a price move loosens none of them.

Two things are watched, because they are different facts:

* a name with an **indicative value and a registered growth view** — its
  **REFERENCE DISTANCE**, the MBP that value would imply at the **tier-1
  cushion** (E90: base × 0.85). **A reference, not a tier and not a buy
  line**: tier 1 is the LOOSEST cushion and therefore the EARLIEST warning,
  and any real tier would sit lower.
* a name with **no value** — its **drawdown from the 52-week high**, against
  Gate 1's 15–50% band. It is the only thing the framework can say about a
  name it cannot value.

**A name outside the circle of competence (E51/E96) is never watched at
all**: §5 cannot be run on it, so no level it crosses would mean anything.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = PROJECT_ROOT / "data" / "pricewatch_state.json"
STATE_VERSION = 1

#: How many ranked names are watched. E97 makes it configurable; 20 is the
#: default because it is the depth E94's readiness table already covers.
DEFAULT_TOP_N = 20

#: E90's tier-1 cushion, used as a REFERENCE and never as a tier. The
#: loosest of the three, so the reference is the earliest warning any real
#: tier could give. E77's one-tier-stricter shift is NOT applied: it adjusts
#: a tier that has been scored, and a ranked name has none.
REFERENCE_CUSHION = 0.85
REFERENCE_TIER = 1

#: The approach rung: price within 25% above the reference.
APPROACH_MULTIPLE = 1.25

#: Gate 1's band (FRAMEWORK §3). A name with no value is watched on entering
#: it; the upper edge is carried so the table can say "through it".
BAND_LOW = 0.15
BAND_HIGH = 0.50

#: How far above a level the price must rise before that level may fire
#: again.
#:
#: **A CHOSEN NUMBER, NOT A DERIVED ONE, AND THE OWNER'S TO MOVE.** E97
#: requires a margin and does not put a figure on it. Without one a level
#: re-arms the instant the price ticks back over it and fires again on the
#: next tick down — the oscillation the once-per-crossing rule exists to
#: prevent, arriving a day later. 3% is wide enough to sit outside ordinary
#: daily noise on these names and narrow enough that a real recovery re-arms
#: within a week. Nothing stronger is claimed for it.
REARM_MARGIN = 0.03

EVENT_APPROACH = "WITHIN 25% OF REFERENCE"
EVENT_REFERENCE = "AT REFERENCE"

#: E97.1: the Gate 1 band event is DROPPED. Filter 1 already rejects any
#: name outside 15-50%, so every ranked name is in the band by construction
#: and the event announced what the ranking had already said -- fourteen of
#: eighteen on the first night. A deeper line was offered and refused: a
#: deeper fall is still just a PRICE, and this framework does not act on
#: price without a named event (E27, and CTSH's own 2026-08-31 verdict).
#:
#: THE FIGURE STAYS AND THE POINTER GOES. The drawdown is still computed and
#: still printed, as information; it simply never fires.

KIND_REFERENCE = "reference"
KIND_DRAWDOWN = "drawdown"
KIND_SKIPPED = "not watched"


@dataclass
class Watched:
    """One ranked name's state tonight. Computed; never stored as a verdict."""

    ticker: str
    rank: int
    kind: str
    close: float | None = None
    currency: str | None = None
    #: KIND_REFERENCE: the indicative value and the level it implies.
    indicative: float | None = None
    reference: float | None = None
    approach: float | None = None
    #: (close - reference) / reference, as a fraction. Negative = below it.
    distance: float | None = None
    #: KIND_DRAWDOWN: the fall from the 52-week high, as a positive fraction.
    drawdown: float | None = None
    in_band: bool = False
    #: E98: how the value was brought into the price's denomination, with
    #: the rate and date where one was used, so the arithmetic is checkable.
    conversion: str = ""
    #: Why this name is not watched, where it is not.
    detail: str = ""
    events: list[str] = field(default_factory=list)

    @property
    def watched(self) -> bool:
        return self.kind != KIND_SKIPPED


def reference_level(indicative: float) -> float:
    """E90's arithmetic at the tier-1 cushion. A DISTANCE, not a buy line."""
    return indicative * REFERENCE_CUSHION


@dataclass(frozen=True)
class Conversion:
    """E98: how a value in one denomination reached another, checkably.

    ``factor`` multiplies the VALUE to reach the price's denomination.
    ``kind`` is "unit" for a minor-unit divisor -- exact, dateless,
    sourceless -- or "rate" for a real exchange rate, which carries the
    rate's own as-of date and its source.
    """

    factor: float
    kind: str                       # "unit" | "rate" | "identity"
    detail: str
    rate: float | None = None
    as_of: date | None = None
    source: str = ""

    def describe(self) -> str:
        if self.kind == "identity":
            return ""
        if self.kind == "unit":
            return f"× {self.factor:g} ({self.detail})"
        return (f"× {self.factor:.6f} ({self.detail}, "
                f"{self.as_of.isoformat() if self.as_of else 'NO DATE'}, "
                f"{self.source})")


def convert_value(value: float, *, reporting: str | None, quote: str | None,
                  price_date: date | None = None,
                  rate_lookup=None) -> tuple[float | None, Conversion | None, str]:
    """E98: bring ``value`` (in ``reporting``) into ``quote``'s denomination.

    Returns (converted, how, why-refused). THE TWO CASES ARE DIFFERENT
    THINGS and the first half of E98 is that they must not be conflated:

    * **A MINOR UNIT IS NOT A CURRENCY.** GBX/GBp and GBP are the same
      currency, exactly one hundred to one, for ever. That is a DIVISOR --
      exact, dateless, sourceless -- and it is NEVER refused for want of a
      rate. All four names E97 could not watch are in this case.
    * **A different currency needs a REAL RATE, dated to THE PRICE'S OWN
      DATE.** Where none exists for that date the conversion is REFUSED --
      never interpolated, never carried forward from the previous session.
      A rate invented for a date is the same class of error as a zero
      invented for an absent tag (E25).
    """
    from .fx import MINOR_UNITS_PER_MAJOR, major_unit

    if not reporting or not quote:
        return None, None, "the store does not state both currencies"

    r_major, q_major = major_unit(reporting), major_unit(quote)
    if r_major != q_major:
        # CASE 2: a real rate, and it must be the price's own date.
        if rate_lookup is None:
            return None, None, (
                f"{r_major}->{q_major} needs an exchange rate for "
                f"{price_date.isoformat() if price_date else 'the price date'}"
                f" and no dated lookup was supplied (E98: never a stale rate)")
        try:
            rate = rate_lookup(r_major, q_major, price_date)
        except Exception as exc:  # noqa: BLE001 -- reported, never raised
            return None, None, f"{r_major}->{q_major}: {exc}"
        if rate is None:
            return None, None, (
                f"no {r_major}->{q_major} rate for "
                f"{price_date.isoformat() if price_date else 'the price date'}"
                f" -- REFUSED, not interpolated (E98)")
        value = value * rate.value
        how = Conversion(rate.value, "rate", f"{r_major}->{q_major}",
                         rate=rate.value, as_of=rate.as_of,
                         source=rate.source or "unstated")
    else:
        how = None

    # CASE 1: the minor unit, which is arithmetic and not a rate.
    divisor = MINOR_UNITS_PER_MAJOR.get((quote or "").strip(), 1.0)
    if divisor != 1.0:
        value = value * divisor
        unit = Conversion(divisor, "unit",
                          f"{q_major} -> {quote.strip()}, "
                          f"{divisor:g} minor units per major")
        how = unit if how is None else Conversion(
            how.factor * divisor, "rate",
            f"{how.detail} then {unit.detail}", rate=how.rate,
            as_of=how.as_of, source=how.source)
    if how is None:
        how = Conversion(1.0, "identity", "same currency and unit")
    return value, how, ""


# --- the cursor: what has already fired -----------------------------------


def load_state(path: Path = STATE_PATH) -> dict:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"version": STATE_VERSION, "fired": {}}
    if not isinstance(document, dict):
        return {"version": STATE_VERSION, "fired": {}}
    document.setdefault("fired", {})
    return document


def save_state(document: dict, path: Path = STATE_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return path


def _armed(state: dict, ticker: str, event: str) -> bool:
    """Has this level NOT already fired? A cursor, never a decision."""
    return not state.get("fired", {}).get(ticker, {}).get(event)


def _fire(state: dict, ticker: str, event: str, as_of: date, level: float | None):
    state.setdefault("fired", {}).setdefault(ticker, {})[event] = {
        "date": as_of.isoformat(),
        "level": level,
    }


def _rearm(state: dict, ticker: str, event: str) -> None:
    fired = state.get("fired", {}).get(ticker, {})
    fired.pop(event, None)
    if not fired:
        state.get("fired", {}).pop(ticker, None)


def crossings(item: Watched, state: dict, *, as_of: date,
              rearm_margin: float = REARM_MARGIN) -> list[str]:
    """Which levels fired TONIGHT, mutating the cursor.

    ONCE PER CROSSING (E97). A level that has fired stays fired until the
    price rises ``rearm_margin`` above it; only then may it fire again. A
    level that re-armed the instant the price ticked back over would fire
    again on the next tick down, which is the oscillation the rule exists to
    prevent arriving one day later.
    """
    if item.close is None or not item.watched:
        return []
    events: list[str] = []

    if item.kind == KIND_REFERENCE and item.reference is not None:
        for event, level in ((EVENT_REFERENCE, item.reference),
                             (EVENT_APPROACH, item.approach)):
            if level is None:
                continue
            if item.close <= level:
                if _armed(state, item.ticker, event):
                    events.append(event)
                    _fire(state, item.ticker, event, as_of, level)
            elif item.close > level * (1 + rearm_margin):
                _rearm(state, item.ticker, event)

    # E97.1: KIND_DRAWDOWN fires NOTHING. Its figure is information in the
    # nightly table and never a pointer.

    item.events = events
    return events


# --- the vendor's industry strings, for E51/E96 ---------------------------


class IndustryStringsUnavailable(RuntimeError):
    """The circle-of-competence STRING limb has no input at all.

    RAISED, NOT SWALLOWED (CODE-REVIEW-2026-09-01 D3/D4). With an empty map
    `readiness.assess` applies only the OWNER TICKER LISTS -- and E96's is
    empty -- so every E96 name in the ranked top twenty would be watched and
    could fire. Returning `{}` made that indistinguishable from a universe
    that happens to contain no such name. It is not a fact about the
    companies; it is a fact about this machine, and the run says so.
    """


def industry_strings(snapshot_root: Path | None = None,
                     db_path: Path | None = None) -> dict[str, str]:
    """ticker -> the vendor's industry string. NEWEST classification wins.

    THE WATCHER NEEDS THIS OR IT CANNOT OBEY E97. `readiness.assess` applies
    the circle-of-competence STRING limb only where an industry is supplied;
    without one only the owner ticker lists reach a name, and NHY.OL and EXE
    -- both caught by E96's `Aluminum` and `Oil & Gas E&P` strings -- were
    watched and fired on the first run of this watcher.

    **THE DURABLE TABLE FIRST** (`vss/vendorstrings.py`), then any snapshot
    store still on disk laid over it. Until 2026-09-01 this read the stores
    alone, which E93 prunes; and it took the OLDEST string per ticker where
    `screen.filter1` took the newest, so one ruling had two implementations
    with opposite precedence. One source, one precedence, both here.

    Raises `IndustryStringsUnavailable` when nothing at all can be read. A
    ticker merely ABSENT from a populated map still carries no string, and
    that silence is a fact about the fetch (E51/E96 both record it).
    """
    from . import snapshot as snapshot_store
    from . import vendorstrings

    root = snapshot_root or snapshot_store.SNAPSHOT_ROOT
    table = vendorstrings.read(db_path or vendorstrings.DB_PATH)
    on_disk: list[tuple[date, dict]] = []
    try:
        stores = snapshot_store.earlier_fundamentals_stores(
            root, before=date(9999, 12, 31))
    except (OSError, ValueError) as exc:
        log.warning("E97: no fundamentals store on disk (%s); the durable "
                    "table is the only source", exc)
        stores = []
    for store in stores:
        try:
            day = date.fromisoformat(store.parent.name)
        except ValueError:                     # not a dated directory
            continue
        try:
            on_disk.append((day, snapshot_store.read_sector_strings(store)))
        except Exception as exc:  # noqa: BLE001 -- one store never breaks it
            log.warning("E97: industry strings unreadable in %s: %s", store, exc)
    merged = vendorstrings.merge_with_stores(table, on_disk)
    out = {t: industry for t, (_sector, industry) in merged.items() if industry}
    if not out:
        raise IndustryStringsUnavailable(
            "no vendor industry string is available from data/vss.sqlite or "
            "any snapshot store, so E51's and E96's INDUSTRY limbs have no "
            "input -- and E96's owner ticker list is empty, so E96 is not "
            "being applied at all. Seed the table with "
            "`python -m vss backfill-vendor-strings`.")
    return out


# --- building the watch list ----------------------------------------------


def watch_ranked(rows: Sequence[dict], *, prices: dict,
                 readiness: dict | None = None,
                 top_n: int = DEFAULT_TOP_N,
                 as_of: date | None = None,
                 run_ts: datetime | None = None,
                 rate_lookup=None) -> list[Watched]:
    """One `Watched` per ranked name, in rank order.

    ``rows`` are stored ranking rows (`store.read_ranking`); ``prices`` maps
    ticker -> an object with `last_close`, `drawdown` and `high_52w`;
    ``readiness`` maps ticker -> a `readiness.Readiness`, computed by the
    caller so this module opens no stores of its own.
    """
    from .readiness import STATE_OUT_OF_CIRCLE

    as_of = as_of or date.today()
    readiness = readiness or {}
    ranked = [r for r in rows
              if r.get("section") == "ranked" and r.get("position")]
    ranked.sort(key=lambda r: r["position"])

    out: list[Watched] = []
    for row in ranked[:top_n]:
        ticker = row["ticker"]
        assessed = readiness.get(ticker)
        metrics = prices.get(ticker)
        close = getattr(metrics, "last_close", None)

        # E97: a name outside the circle is NEVER WATCHED. No level it
        # crosses would mean anything, and pointing at one would invite
        # exactly the work E51/E96 forbid.
        if assessed is not None and assessed.state == STATE_OUT_OF_CIRCLE:
            out.append(Watched(ticker, row["position"], KIND_SKIPPED,
                               close=close,
                               detail=f"outside the circle of competence — "
                                      f"{assessed.detail}"))
            continue

        indicative = getattr(assessed, "indicative", None) if assessed else None
        currency = getattr(assessed, "currency", None) if assessed else None
        quote = getattr(assessed, "quote_currency", None) if assessed else None

        # E98: bring the VALUE into the PRICE's denomination before either is
        # compared. AUTO.L, RMV.L, RKT.L and IMB.L quote GBX and report GBP,
        # and comparing them raw read +12,791% to +18,653% on this watcher's
        # first run. A minor unit is arithmetic (x100, exact, dateless); a
        # different currency needs a dated rate and is REFUSED without one.
        conversion = refusal = None
        if indicative is not None:
            converted, conversion, refusal = convert_value(
                indicative, reporting=currency, quote=quote,
                price_date=getattr(metrics, "last_close_date", None),
                rate_lookup=rate_lookup)
            indicative = converted

        if indicative is not None:
            reference = reference_level(indicative)
            item = Watched(
                ticker, row["position"], KIND_REFERENCE, close=close,
                currency=currency, indicative=indicative, reference=reference,
                approach=reference * APPROACH_MULTIPLE,
                distance=((close - reference) / reference
                          if close is not None and reference else None),
                conversion=(conversion.describe()
                            if conversion is not None else ""),
                detail=(f"indicative {indicative:,.2f} × {REFERENCE_CUSHION} "
                        f"(tier-{REFERENCE_TIER} cushion, E90) — A REFERENCE "
                        f"DISTANCE, NOT A BUY LINE"
                        + (f"; converted {conversion.describe()} (E98)"
                           if conversion is not None and conversion.kind != "identity"
                           else "")))
        else:
            drawdown = getattr(metrics, "drawdown", None)
            why = ("no indicative value" if not refusal else
                   f"an indicative value exists but could not be converted: "
                   f"{refusal}")
            item = Watched(
                ticker, row["position"], KIND_DRAWDOWN, close=close,
                currency=currency, drawdown=drawdown,
                in_band=(drawdown is not None
                         and BAND_LOW <= drawdown <= BAND_HIGH),
                detail=(f"{why}: watched on the drawdown against Gate 1's "
                        f"15–50% band"
                        + (f" ({assessed.state})" if assessed else "")))
        out.append(item)
    return out


# --- rendering -------------------------------------------------------------


def render_table(items: Sequence[Watched]) -> list[str]:
    """The block the nightly report carries, fired or not (E97)."""
    out = ["| # | Ticker | Watched on | Close | Reference / band | Distance "
           "| Converted (E98) | Fired |",
           "|---:|---|---|---:|---:|---:|---|---|"]
    for item in items:
        close = f"{item.close:,.2f}" if item.close is not None else "--"
        if item.kind == KIND_SKIPPED:
            out.append(f"| {item.rank} | `{item.ticker}` | **not watched** | "
                       f"{close} | -- | -- | -- | E51/E96 |")
            continue
        if item.kind == KIND_REFERENCE:
            level = f"{item.reference:,.2f}" if item.reference else "--"
            dist = f"{item.distance:+.1%}" if item.distance is not None else "--"
            watched_on = "reference distance"
        else:
            level = f"{BAND_LOW:.0%}–{BAND_HIGH:.0%}"
            dist = (f"{item.drawdown:.1%} dd" if item.drawdown is not None
                    else "--")
            watched_on = "drawdown vs 52w high"
        fired = ", ".join(item.events) if item.events else ""
        out.append(f"| {item.rank} | `{item.ticker}` | {watched_on} | {close} "
                   f"| {level} | {dist} | {item.conversion or '--'} | {fired} |")
    out.append("")
    out.append(f"*E97: the REFERENCE is the indicative value × "
               f"{REFERENCE_CUSHION} (E90's tier-{REFERENCE_TIER} cushion) — "
               f"**a distance, not a buy line**. Almost no ranked name has a "
               f"§4.4 score, and tier 1 is the LOOSEST cushion, so a name "
               f"that has not reached it has not reached any MBP it could "
               f"ever be given. Nothing here is written, no name is entered, "
               f"and an indicative value stays indicative.*")
    return out


def notification_lines(items: Sequence[Watched], limit: int = 6) -> list[str]:
    """A pointer, not a valuation (E92's shape)."""
    fired = [i for i in items if i.events]
    lines: list[str] = []
    for item in fired[:limit]:
        for event in item.events:
            if item.kind == KIND_REFERENCE:
                lines.append(f"{item.ticker} {event} — {item.close:,.2f} vs "
                             f"{item.reference:,.2f} (reference, not a buy line)")
            else:
                lines.append(f"{item.ticker} {event} — drawdown "
                             f"{item.drawdown:.1%}")
    if len(fired) > limit:
        lines.append(f"...and {len(fired) - limit} more — see tonight's report")
    return lines
