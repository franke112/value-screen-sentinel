"""``reports/OVERVIEW.html`` — the state of the book on one page.

**READ-ONLY, AND THAT IS THE WHOLE DESIGN.** Nothing on this page writes,
decides or accepts anything. There is no form, no button, no request and no
script: it is a file on disk that a browser opens. Every decision this
project makes is a dictated ruling in a session, and a page that could take
one would be a second place decisions come from.

**IT SHOWS THE STATE; THE DOCUMENTS CARRY THE EVIDENCE.** Per name it links
to the briefing, the reading, the strike document and the run record, and it
**never summarises one**. A summary of a sourced document is a judgement
without its sources, and the whole point of those files is that every line
carries a page.

**EVERY FIGURE IS READ AT GENERATION TIME AND NOTHING IS STORED TWICE.**
`config/`, `reference/` and `data/` are the record; this page is a view of
them and holds no state of its own. Regenerating it after a change to the
watchlist is the only way its contents change.

**A FIGURE THAT CANNOT BE READ PRINTS `DATA MISSING` AND KEEPS ITS ROW.** An
absent row reads as *nothing to see*, and that is the failure mode this page
exists to remove. Every refusal here says WHY in the cell that refused.

**NO ARITHMETIC CROSSES A UNIT SEAM.** AUTO.L's `fv_base` is written in GBP
to match its run record while its close is quoted in GBX, and the watchlist
records that seam as OPEN. A distance computed across it would read as
roughly −12,700%, which is the shape of the defect this project has already
met once. Where the two currencies are not the same code, the distance is
`DATA MISSING` with the seam named.

**WHAT IT WRITES:** `reports/OVERVIEW.html`, and nothing else, anywhere.
"""

from __future__ import annotations

import html
import json
import logging
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Sequence

from . import metrics as M
from . import readiness as R
from .config import ConfigError, WatchlistEntry, load_watchlist
from .fetch import FetchResult, SOURCE_CACHE, SOURCE_NONE, read_cache
from .manual import (TEMPLATE_PATH, ManualError,
                     gate_on_registered_view, load_manual)
from .refresh import needs_owner as e92_needs_owner
from .refresh import waits_for
from .runner import (CACHE_DIR, DB_PATH, PROJECT_ROOT, REPORTS_DIR,
                     WATCHLIST_PATH, build_row, load_run_record)
from . import heartbeat as HB
from .rules import (AT_BELOW_MBP, DEFINITION_CROSSING, NO_STOP,
                    NO_STOP_PRE_ENTRY, STALE_DATA, STOP_BREACHED)
from .runrecord import RecordError, RunRecord
from .sales import DATA_MISSING, pct, settled_closes
from .shadowbook import (BENCHMARKS, INCOMPLETE, SHADOW_BOOK_PATH,
                         load_shadow_book, shadow_rows)

log = logging.getLogger("vss.overview")

OUTPUT_PATH = REPORTS_DIR / "OVERVIEW.html"

MANUAL_DIR = PROJECT_ROOT / "config" / "manual"
REFERENCE_DIR = PROJECT_ROOT / "reference"
RUN_RECORDS_DIR = REFERENCE_DIR / "run-records"
GROWTH_VIEWS_DIR = REFERENCE_DIR / "growth-views"
FRAMEWORK_EDITS = REFERENCE_DIR / "FRAMEWORK-EDITS.md"

#: The order the live sections are printed in — held first, then the two
#: halves of E27's WATCH, then the review queue, then E111's read-not-
#: watched. Anything the watchlist grows that is not on this list sorts
#: after it rather than vanishing.
STATUS_ORDER = ("HELD", "WATCH-PRICED", "WATCH-GATED", "PIPELINE", "INTAKE")

#: The three top-level groupings of view 1. E51 and E96 names and DROPPED
#: names get their own sections rather than being interleaved: a name the
#: framework cannot value and a name it has refused are not waiting on
#: anything, and mixing them into the live list is what makes a long table
#: unreadable.
SECTION_LIVE = "live"
SECTION_OUTSIDE = "outside"
SECTION_DROPPED = "dropped"

#: Where a store exists but no watchlist entry does. Not a status the
#: schema knows — E109/E111 keep entry-making an owner's act — so it is
#: spelled differently from every real status on purpose.
STATUS_STORE_ONLY = "STORE ONLY — no watchlist entry"


# --- small value objects ---------------------------------------------------


@dataclass(frozen=True)
class Doc:
    """One existing document, linked and never summarised."""

    kind: str
    label: str
    href: str


@dataclass(frozen=True)
class Figure:
    """A money figure, its currency, and where it came from.

    ``label`` is empty for a struck `fv_base` and carries the word
    PROVISIONAL for a run-record replay the owner has not written to the
    watchlist. ``why`` is the reason a figure is absent, or the provenance
    of the one that is present — either way it is printed.
    """

    amount: float | None = None
    currency: str | None = None
    label: str = ""
    why: str = ""


@dataclass(frozen=True)
class Distance:
    """A percentage distance, or the reason there is none."""

    value: float | None = None
    why: str = ""


@dataclass
class NameRow:
    ticker: str
    name: str
    status: str
    section: str
    currency: str | None = None
    fv: Figure = field(default_factory=Figure)
    price: float | None = None
    price_date: date | None = None
    #: E122(e): set when this close is one the vendor dropped or blanked and
    #: we kept. Printed beside the price wherever it appears.
    retained: object | None = None
    price_settled: bool | None = None
    price_why: str = ""
    #: When the price cache this row was read from was last written. The
    #: footer takes the newest of these, so a reader can tell a page built
    #: on tonight's fetch from one built on a cache four days old.
    price_fetched_at: datetime | None = None
    dist_fv: Distance = field(default_factory=Distance)
    mbp: float | None = None
    mbp_superseded: bool = False
    dist_mbp: Distance = field(default_factory=Distance)
    stop_price: float | None = None
    #: The entry's own catalyst, carried so the qualifying clause is built
    #: from the record rather than restated in the renderer.
    catalyst_date: date | None = None
    catalyst_resolved: date | None = None
    catalyst_event: str | None = None
    #: The MBP move the entry's catalyst note states, or why there is none.
    rescore: "Rescore" = field(default_factory=lambda: Rescore())
    #: Where the price sits on a track anchored on the fair value, or the
    #: reason there is no track. Struck AFTER `dist_fv`, from its refusal,
    #: so the unit check happens once.
    pos: "Position" = field(default_factory=lambda: Position())
    #: The 52-week close series as a picture, or why there is none.
    spark: "Spark" = field(default_factory=lambda: Spark())
    waiting: tuple[str, ...] = ()
    #: The blocker and verdict CODES `rules.assess` struck. Read by the
    #: queue: a code is a fact, and matching on the rendered sentence is
    #: how the two drift apart.
    blockers: tuple[str, ...] = ()
    verdicts: tuple[str, ...] = ()
    docs: tuple[Doc, ...] = ()
    #: (ruling, reason) where E51 or E96 puts the name outside the circle.
    circle: tuple[str, str] | None = None
    #: True where no vendor industry string is stored, so E51/E96's
    #: industry limb could not be evaluated. The silence is a fact about
    #: the fetch and is printed as one.
    circle_blind: bool = False
    has_entry: bool = True
    has_store: bool = False

    @property
    def gate_closed(self) -> str:
        """Why this name's distance is drawn muted, or "" where it is not.

        THE WORDS ARE THE POINT. The mute is a colour and a colour cannot
        say why on its own, so the card prints this sentence beside the
        figures it drains.

        E51 AND E96 ARE HERE TOO, AND THE OWNER NAMED ONLY DROPPED AND
        WATCH-GATED. The ground he gave is that a cheap gate-closed name
        must not read as an invitation, and a name section 5 CANNOT BE RUN
        ON AT ALL is the strongest case of it -- NHY.OL is PIPELINE, sits
        inside E96, and would otherwise wear a live tone. Recorded here as
        an extension rather than assumed.
        """
        if self.section == SECTION_OUTSIDE:
            ruling = self.circle[0] if self.circle else "E51/E96"
            return (f"outside the circle of competence ({ruling}) — section "
                    f"5 cannot be run on this name at all")
        if self.status == "DROPPED":
            return ("DROPPED — refused, exited or killed at a gate")
        if self.status == "WATCH-GATED":
            return ("WATCH-GATED — re-entry is on a named information "
                    "event, never on a price level")
        return ""
    #: `manual.section5_gate` as `vss manual` strikes it, or None where the
    #: name has no store. COMPUTED ONCE and read by both view 1 and view 2,
    #: so the read-back count in the table and the read-back count in the
    #: queue cannot disagree.
    gate: object | None = None
    gate_error: str = ""


#: Queue kinds, in the order they break ties. `actions` — how many owner
#: acts would clear the item — is the primary sort, so the top of the queue
#: is literally what one action would unblock.
Q_STOP = "missing stop"
Q_VIEW = "no growth view"
Q_READBACK = "read-backs (E108 floor)"
Q_PROVISIONAL = "PROVISIONAL value"
Q_RECORD = "no run record named"
Q_NEEDS_OWNER = "NEEDS OWNER (E92)"
QUEUE_ORDER = (Q_STOP, Q_VIEW, Q_RECORD, Q_PROVISIONAL, Q_READBACK,
               Q_NEEDS_OWNER)


@dataclass(frozen=True)
class QueueItem:
    kind: str
    ticker: str
    #: How many owner actions would clear it, or None for DATA MISSING.
    actions: int | None
    #: What one action would unblock. Never a judgement — a consequence.
    unblocks: str
    detail: str
    docs: tuple[Doc, ...] = ()

    @property
    def sort_key(self) -> tuple:
        rank = (QUEUE_ORDER.index(self.kind)
                if self.kind in QUEUE_ORDER else len(QUEUE_ORDER))
        # An unknown count sorts LAST rather than first: a queue that put
        # DATA MISSING at the top would read as the most urgent work.
        return (self.actions if self.actions is not None else 10**6,
                rank, self.ticker)


#: How far ahead the top line looks. A week: the horizon on which the owner
#: could actually do something about a report, and short enough that a line
#: saying "nothing needs you" still means it. Longer, and the top of the
#: page fills with dates nobody can act on and stops being read.
ATTENTION_HORIZON_DAYS = 7

#: The kinds of thing that may reach the top line, MOST URGENT FIRST. The
#: list is CLOSED on purpose: a top line that grew a fourth and a fifth
#: category would be a second report, and the page already has one below.
A_STOP_BREACHED = "stop breached"
A_HELD_NO_STOP = "no stop on a holding"
A_AT_BELOW_MBP = "maximum buy price crossed"
A_DEFINITION = "the buy price moved, not the price"
A_CATALYST = "a dated event this week"
A_UNCHECKABLE = "a check could not run"
ATTENTION_ORDER = (A_STOP_BREACHED, A_HELD_NO_STOP, A_AT_BELOW_MBP,
                   A_DEFINITION, A_CATALYST, A_UNCHECKABLE)


@dataclass(frozen=True)
class Attention:
    """One thing that needs the owner today, in plain words.

    `sentence` is the whole item: the page prints it and adds nothing. A
    top line assembled out of fragments and a template is a top line that
    reads like a machine, and this one has to be read in a second.
    """

    kind: str
    ticker: str
    sentence: str
    #: Order WITHIN a kind, lowest first (owner, 2026-09-20). A HELD name
    #: whose STOP could not be checked heads its group: an unchecked stop
    #: is the one blocker that can suppress an exit.
    within: int = 0

    @property
    def sort_key(self) -> tuple:
        rank = (ATTENTION_ORDER.index(self.kind)
                if self.kind in ATTENTION_ORDER else len(ATTENTION_ORDER))
        return (rank, self.within, self.ticker)


#: The track runs from HALF the fair value to HALF AGAIN, with the fair
#: value dead centre. Chosen so both decision points are ON it and away
#: from the ends: E90's cushions put an MBP at 0.85 / 0.75 / 0.65 of the
#: base value, which lands between a fifth and a third of the way across,
#: and a price up to 50% over fair value still has somewhere to sit.
#: A price outside the range is CLIPPED TO THE EDGE AND SAID IN WORDS --
#: never silently pinned, and never allowed to rescale the track, because
#: a scale that moves per name is a scale nobody can compare across names.
SCALE_LOW = 0.5
SCALE_HIGH = 1.5

#: What the position MEANS, in words, because colour never carries a
#: meaning on its own here. Read in order; the first that matches wins.
BAND_BELOW_MBP = "at or below the maximum buy price"
BAND_NEAR_MBP = "within 5% of the maximum buy price"
BAND_UNDER_FV = "below fair value, above the buy price"
BAND_OVER_FV = "above fair value"
#: THE SAME TWO PLACES WITH NO BUY PRICE TO NAME. A name with no tier has
#: no MBP (E90's cushion needs one), and saying "above the buy price" of a
#: price that does not exist is a sentence about a level nobody struck.
BAND_UNDER_FV_NO_MBP = "below fair value; no buy price is struck"
BAND_OVER_FV_NO_MBP = "above fair value; no buy price is struck"


@dataclass(frozen=True)
class Position:
    """Where the price sits on a track anchored on the fair value.

    Every figure here is a FRACTION OF THE FAIR VALUE, so the track means
    the same thing on every row. `why` is the whole answer where no
    position can be struck -- a unit seam, no fair value, no close -- and
    the row prints it in place of the track rather than showing an empty
    one, which would read as a price at zero.
    """

    price_at: float | None = None
    mbp_at: float | None = None
    clipped: str = ""
    band: str = ""
    why: str = ""

    @property
    def ok(self) -> bool:
        return self.price_at is not None

    @staticmethod
    def _place(fraction: float) -> tuple[float, str]:
        """A fraction of fair value as a percentage across the track."""
        if fraction < SCALE_LOW:
            return 0.0, "below the left end of the scale"
        if fraction > SCALE_HIGH:
            return 100.0, "past the right end of the scale"
        span = SCALE_HIGH - SCALE_LOW
        return (fraction - SCALE_LOW) / span * 100.0, ""



def _watchlist_calendars():
    """The exchange calendars, or None (every name counted Monday to Friday,
    and the block says so) when they cannot be loaded."""
    try:
        from .calendars import load_market_calendars
        return load_market_calendars(PROJECT_ROOT / "config" / "exchange_calendars.yaml")
    except Exception:  # noqa: BLE001 -- the page must still render
        return None

def position(price: float | None, fv: float | None, mbp: float | None,
             *, why: str = "") -> Position:
    """The row's position, or the reason there is none.

    THE UNIT CHECK HAS ALREADY HAPPENED. `distance` refuses across a seam
    and hands its reason here as `why`; this function never compares
    currencies itself, so there is exactly one place in the module that
    decides whether two figures may be divided.
    """
    if why:
        return Position(why=why)
    if price is None or fv is None or fv <= 0:
        return Position(why=f"{DATA_MISSING}: no fair value to measure against")
    at, clipped = Position._place(price / fv)
    mbp_at = None
    if mbp is not None and mbp > 0:
        mbp_at, _ = Position._place(mbp / fv)
    if mbp is not None and mbp > 0:
        if price <= mbp:
            band = BAND_BELOW_MBP
        elif price <= mbp * 1.05:
            band = BAND_NEAR_MBP
        elif price <= fv:
            band = BAND_UNDER_FV
        else:
            band = BAND_OVER_FV
    else:
        band = (BAND_UNDER_FV_NO_MBP if price <= fv
                else BAND_OVER_FV_NO_MBP)
    return Position(at, mbp_at, clipped, band)


#: THE DISTANCE SCALE. Green at or below a level, red far above it,
#: neutral between -- and it is a MEASUREMENT, never a verdict. It says
#: HOW FAR, and nothing about whether to act: a name can be green and
#: need nothing, and the thing that needs the owner can be red.
#:
#: The ladder is not chosen by eye. **0% is the level itself** and **5% is
#: `rules.APPROACHING_MBP_FACTOR`**, the band the framework already calls
#: approaching; 25% and 75% are the two steps beyond it, spaced so a name
#: a quarter above its buy price and a name three-quarters above it do not
#: read the same. The bound is INCLUSIVE and the first match wins.
#:
#: EVERY TONE CARRIES ITS WORDS. They are printed as the figure's title
#: and in the page's own key, because a scale whose only carrier is hue
#: says nothing to a red-green colourblind reader -- and the figure keeps
#: its sign and its number either way.
DISTANCE_TONES: tuple[tuple[float | None, str, str], ...] = (
    (0.0, "d-at", "at or below the level"),
    (0.05, "d-near", "within 5% above it — the APPROACHING band"),
    (0.25, "d-mid", "between 5% and 25% above it"),
    (0.75, "d-far", "between 25% and 75% above it"),
    (None, "d-remote", "more than 75% above it"),
)

#: What a muted figure is drawn in, and it overrides every tone above.
TONE_MUTED = "d-muted"
TONE_NONE = "d-none"

#: A name whose gate is CLOSED is drawn muted whatever its distance says.
#: **A NAME THAT IS CHEAP AND GATE-CLOSED MUST NOT READ AS AN
#: INVITATION.** DECK is 35% below its fair value and its Gate 1 catalyst
#: limb failed; a green figure on that card is the page arguing for a
#: trade the framework has already refused.
GATE_CLOSED_STATUSES = ("DROPPED", "WATCH-GATED")


def tone(value: float | None, *, muted: bool = False) -> tuple[str, str]:
    """(class, words) for a distance. The words are never optional."""
    if muted:
        return TONE_MUTED, "the gate is closed — a measurement, not an invitation"
    if value is None:
        return TONE_NONE, ""
    for bound, name, meaning in DISTANCE_TONES:
        if bound is None or value <= bound:
            return name, meaning
    return TONE_NONE, ""


#: How many points the sparkline draws. A 52-week window holds about 255
#: settled bars and the picture is 120px wide, so every bar would be two
#: points to the pixel and four kilobytes of path per card. Sampled EVERY
#: Nth, which preserves the shape the picture exists to show -- did it
#: fall and stay down, or fall and recover -- and is stated rather than
#: hidden: a bucketed min/max would draw a line the prices never traced.
SPARK_POINTS = 60

#: Below this many settled bars in the window there is no shape to see,
#: and a two-point line drawn across a card reads as a year of history.
SPARK_MIN_BARS = 20


@dataclass(frozen=True)
class Spark:
    """The 52-week close series as a picture, or the reason there is none.

    **THE RANGE IS THE PRICE SERIES' OWN.** A fair value or an MBP inside
    it is drawn as a line; one OUTSIDE it is NOT drawn and the card says
    which way it lies. Stretching the range to reach a level would squash
    the price line -- MUSA's fair value is a third of its 52-week low, and
    a chart including it would show a year of trading as a flat smear at
    the top. The picture is about the prices; the levels are figures
    beside it either way.

    `points` are (x, y) in 0..1 with **y running LOW TO HIGH**. The
    renderer flips it for SVG's downward axis, which keeps the flip in one
    place instead of in the arithmetic here.
    """

    points: tuple[tuple[float, float], ...] = ()
    first: date | None = None
    last: date | None = None
    low: float | None = None
    high: float | None = None
    bars: int = 0
    fv_y: float | None = None
    mbp_y: float | None = None
    #: The y under which the drawn line is BELOW FAIR VALUE, or None where
    #: no part of it is. 1.0 means the whole year traded below it, which
    #: is what a fair value above the window's high means -- CTSH is the
    #: case. Distinct from `fv_y`, which is None in exactly that case
    #: because there is no line to draw INSIDE the box.
    below_fv_y: float | None = None
    #: Where a level lies when it is not drawn, in words.
    fv_off: str = ""
    mbp_off: str = ""
    why: str = ""

    @property
    def ok(self) -> bool:
        return len(self.points) >= 2


def _place_level(value: float | None, low: float, high: float,
                 what: str) -> tuple[float | None, str]:
    if value is None or high <= low:
        return None, ""
    if value < low:
        return None, (f"the {what} {value:,.2f} is below everything this "
                      f"window holds")
    if value > high:
        return None, (f"the {what} {value:,.2f} is above everything this "
                      f"window holds")
    return (value - low) / (high - low), ""


def spark(frame, *, as_of: date, settled: date,
          fv: float | None = None, mbp: float | None = None) -> Spark:
    """The 52-week settled closes, sampled, or why there is no picture.

    **NOTHING IS FETCHED.** The frame is the cache the nightly run wrote,
    and a window that is short says so rather than drawing a shorter year
    and calling it one.

    `fv` and `mbp` reach here ONLY where the caller has already found them
    comparable with the quote currency. The unit check lives in
    `distance` and is not repeated -- a fair value in pounds drawn across
    a chart of pence would be a line at one hundredth of its height.
    """
    if frame is None or len(frame) == 0:
        return Spark(why=f"{DATA_MISSING}: no cached price series")
    closes = settled_closes(frame, settled)
    if len(closes) == 0:
        return Spark(why=f"{DATA_MISSING}: the cache holds no settled bar")
    start = M.coverage_start(as_of)
    window = [(d, float(v)) for d, v in closes.items() if d >= start]
    if len(window) < SPARK_MIN_BARS:
        held = f"{len(window)} settled bar(s)" if window else "none"
        return Spark(why=(f"{DATA_MISSING}: the cached series holds {held} "
                          f"inside the 52 weeks from {start.isoformat()}, "
                          f"below the {SPARK_MIN_BARS} a shape needs"),
                     bars=len(window))
    first_bar = closes.index[0]
    if not M.covers_52_weeks(first_bar, as_of):
        return Spark(why=(f"{DATA_MISSING}: the cached series begins "
                          f"{first_bar.isoformat()} and does not cover 52 "
                          f"weeks, so no year can be drawn"),
                     bars=len(window), first=first_bar)
    values = [v for _, v in window]
    low, high = min(values), max(values)
    step = max(1, len(window) // SPARK_POINTS)
    # ALWAYS THE LAST BAR. Sampling every Nth can drop the newest close,
    # and a sparkline whose right-hand end is not today's price is a
    # picture that disagrees with the figure printed beside it.
    kept = window[::step]
    if kept[-1] is not window[-1]:
        kept.append(window[-1])
    span = (high - low) or 1.0
    points = tuple(
        ((i / (len(kept) - 1)) if len(kept) > 1 else 0.0, (v - low) / span)
        for i, (_, v) in enumerate(kept))
    fv_y, fv_off = _place_level(fv, low, high, "fair value")
    mbp_y, mbp_off = _place_level(mbp, low, high, "maximum buy price")
    # WHERE THE YEAR TRADED BELOW FAIR VALUE. Three cases and they are not
    # the same: the level sits inside the window (green under the line),
    # it sits above everything the window holds (the whole year was below
    # it), or it sits below everything (no part of the year was).
    if fv_y is not None:
        below = fv_y
    elif fv is not None and fv > high:
        below = 1.0
    else:
        below = None
    return Spark(points, window[0][0], window[-1][0], low, high,
                 len(window), fv_y, mbp_y, below, fv_off, mbp_off)


@dataclass(frozen=True)
class RunStamp:
    """WHICH RUN this page stands on, so a stale page cannot read as current.

    Three separate facts and none of them stands in for another: the
    newest COMPLETED nightly run on record, whether that run is stale by
    the dead man's switch's own bar, and when the price cache the page
    actually read was last written. A page generated by hand at noon on a
    machine whose timer died on Tuesday must say Tuesday.
    """

    completion: "HB.Completion | None"
    stale: str
    cache_written: datetime | None
    why: str = ""


def run_stamp(*, now: datetime, db_path: Path = DB_PATH,
              rows: Sequence[NameRow] = ()) -> RunStamp:
    stamps = [r.price_fetched_at for r in rows if r.price_fetched_at]
    cache_written = max(stamps) if stamps else None
    try:
        last = HB.last_completion(db_path, kind=HB.KIND_NIGHTLY)
    except Exception as exc:      # noqa: BLE001 -- a footer must not crash
        return RunStamp(None, "", cache_written,
                        f"the run record would not read: {exc}")
    stale = HB.staleness_line(last, now=now) or ""
    why = ("" if last is not None else
           "no completed nightly run is on record, so this page cannot say "
           "which run its prices came from")
    return RunStamp(last, stale, cache_written, why)


def attention(rows: Sequence[NameRow], calendar: Sequence[CalendarItem], *,
              as_of: date) -> list[Attention]:
    """What needs the owner TODAY, and nothing else.

    THREE QUESTIONS, and the list is closed to them: has a level been
    crossed, is a holding unguarded, and does something land this week.
    Everything else on this page is work that can wait, which is why it
    is below the fold or behind a disclosure.

    A FOURTH ITEM EXISTS AND IS NOT A FINDING ABOUT A NAME: where one of
    those checks COULD NOT RUN, it says so. "Nothing needs you today" is
    a claim, and a page that cannot support it must not make it.
    """
    out: list[Attention] = []
    for row in rows:
        if row.status == "DROPPED" or row.section == SECTION_OUTSIDE:
            continue
        where = f"{row.ticker} ({row.name})" if row.name else row.ticker
        close = (f"{row.price:,.2f} {row.currency}" if row.price is not None
                 else DATA_MISSING)
        if STOP_BREACHED in row.verdicts:
            out.append(Attention(
                A_STOP_BREACHED, row.ticker,
                f"{where} has broken its stop — the close is {close} against "
                f"a stop of {row.stop_price:,.2f}."
                if row.stop_price is not None else
                f"{where} has broken its stop, and the level is {DATA_MISSING}."))
        if NO_STOP in row.blockers:
            out.append(Attention(
                A_HELD_NO_STOP, row.ticker,
                f"{where} is held and has no stop set. It collects no "
                f"verdict at all until one exists."))
        # A BUY-SIDE CONDITION NEVER STANDS ALONE. The qualifying clause
        # goes in the SAME SENTENCE, not a line below it: the reader who
        # stops after the first half is the reader this page is for.
        if DEFINITION_CROSSING in row.verdicts:
            out.append(Attention(
                A_DEFINITION, row.ticker,
                f"{where} is at or below its maximum buy price because the "
                f"MBP MOVED, not the price — E100 arms nothing on that. "
                f"What else qualifies it: {qualifying_clause(row)}."))
        elif AT_BELOW_MBP in row.verdicts:
            tail = ("" if NO_STOP_PRE_ENTRY not in row.verdicts else
                    " It has no stop set, so the buy is not actionable "
                    "either way.")
            out.append(Attention(
                A_AT_BELOW_MBP, row.ticker,
                f"{where} is at or below its maximum buy price — {close} "
                f"against an MBP of {row.mbp:,.2f}. What qualifies that: "
                f"{qualifying_clause(row)}.{tail}"))
        # A LEVEL THAT COULD NOT BE CHECKED IS NOT A LEVEL THAT HELD.
        # A STALE CLOSE ON A NAME CARRYING A LEVEL (owner, 2026-09-19): the
        # nightly blocked it, so its stop and MBP were NOT checked -- the
        # page says so, with where the name last stood.
        if STALE_DATA in row.blockers and (row.status == "HELD"
                                           or row.mbp is not None
                                           or row.stop_price is not None):
            levels = " and ".join(
                f"{label} {value:,.2f}" for label, value in
                (("stop", row.stop_price), ("MBP", row.mbp)) if value is not None
            ) or "its HELD checks"
            last = (f"{close} on {row.price_date.isoformat()}"
                    if row.price is not None and row.price_date else DATA_MISSING)
            if row.retained is not None:
                last += (f" (RETAINED, first seen "
                         f"{row.retained.first_seen.isoformat()})")
            out.append(Attention(
                A_UNCHECKABLE, row.ticker,
                f"{where} is BLOCKED on a stale close — the newest is {last} "
                f"— so {levels} {'were' if ' and ' in levels else 'was'} "
                f"NOT CHECKED tonight.",
                within=(0 if row.status == "HELD" and row.stop_price is not None
                        else 1 if row.status == "HELD" else 2)))
        elif row.mbp is not None and row.price is None:
            out.append(Attention(
                A_UNCHECKABLE, row.ticker,   # after every stale block

                f"{where} carries a maximum buy price of {row.mbp:,.2f} and "
                f"the page found no settled close for it, so the crossing "
                f"could not be checked either way.", within=3))

    horizon = as_of + timedelta(days=ATTENTION_HORIZON_DAYS)
    for item in calendar:
        if item.resolved is not None or item.status == "DROPPED":
            continue
        if not as_of <= item.when <= horizon:
            continue
        days = (item.when - as_of).days
        when = ("today" if days == 0 else
                "tomorrow" if days == 1 else f"in {days} days")
        out.append(Attention(
            A_CATALYST, item.ticker,
            f"{item.ticker} has a dated event {when}, on "
            f"{item.when.isoformat()}: {item.event}"))
    out.sort(key=lambda item: item.sort_key)
    return out


#: THE KINDS THAT STATE A BUY-SIDE CONDITION. **The page may never state
#: one without the conditions that qualify it.** A price condition met on
#: a name whose gate is shut, or whose buy line is scheduled to move, is
#: INFORMATION AND NOT AN ACTION, and saying the first half without the
#: second is the failure this page exists to remove.
BUY_SIDE_KINDS = (A_AT_BELOW_MBP, A_DEFINITION)

#: What each status means for RE-ENTRY, in the framework's own terms. Read
#: off the status and never inferred from anything else: E27 split WATCH
#: into two precisely because the two carry opposite re-entry rules, and a
#: page that printed "at or below the buy price" without saying which one
#: it was looking at would have thrown that ruling away.
STATUS_MEANING = {
    "HELD": "it is HELD — this is a position, not a purchase",
    "WATCH-PRICED": ("it is WATCH-PRICED — it passed section 5 and was only "
                     "too expensive, so a price condition is the whole of "
                     "what it was waiting for (E27)"),
    "WATCH-GATED": ("it is WATCH-GATED — re-entry is on a NAMED INFORMATION "
                    "EVENT and never on a price level, so a price condition "
                    "changes nothing (E27)"),
    "PIPELINE": ("it is PIPELINE — review work with a frozen Gate 1 (E12), "
                 "and no section 5 run has been made"),
    "INTAKE": ("it is INTAKE — read, not watched, and nothing has been "
               "decided (E111)"),
    "DROPPED": "it is DROPPED — refused, exited or killed at a gate",
}

#: An arrow between two figures, in either of the two forms a note may use.
_RESCORE = re.compile(
    r"([\d][\d,]*\.?\d*)\s*(?:->|→|-->)\s*([\d][\d,]*\.?\d*)")


@dataclass(frozen=True)
class Rescore:
    """A scheduled move of the MBP, AS THE ENTRY'S OWN NOTE STATES IT.

    **NOTHING HERE IS DERIVED.** The figure is read out of the entry's
    `catalyst_event` and reconciled against the MBP the tool computed; a
    note that states no move gives `stated = False`, and a note whose
    stated `from` does not match the live MBP gives DATA MISSING with the
    reason. Recomputing E77's one-tier-stricter cushion here would be the
    page striking a buy price, which is the owner's act and E90's
    arithmetic, not a render-time convenience.

    THE RECONCILIATION IS WHAT MAKES THE PARSE SAFE. CTSH's note carries
    TWO arrows -- the live `67.04 -> 58.10` and, in a trailing
    parenthesis, the superseded E28-era `46.78 -> 40.10`. Requiring the
    left-hand figure to equal the computed MBP is what tells them apart,
    and it is a check rather than a guess.
    """

    when: date | None = None
    frm: float | None = None
    to: float | None = None
    stated: bool = False
    why: str = ""

    @property
    def ok(self) -> bool:
        return self.stated and self.to is not None


#: How close a stated `from` must sit to the computed MBP to be accepted
#: as the same figure. The watchlist states two decimals and `compute_mbp`
#: rounds to two.
RESCORE_TOLERANCE = 0.005


def rescore(entry: WatchlistEntry, mbp: float | None) -> Rescore:
    """The MBP move the entry's catalyst note states, or why there is none."""
    note = entry.catalyst_event or ""
    if "MBP" not in note.upper():
        return Rescore(entry.catalyst_date)
    after = note[note.upper().index("MBP"):]
    found = _RESCORE.search(after)
    if found is None:
        return Rescore(entry.catalyst_date, why=(
            f"{DATA_MISSING}: the entry's catalyst note mentions the MBP and "
            f"states no move of it"))
    try:
        frm = float(found.group(1).replace(",", ""))
        to = float(found.group(2).replace(",", ""))
    except ValueError:
        return Rescore(entry.catalyst_date, why=(
            f"{DATA_MISSING}: the entry's catalyst note states a move this "
            f"page could not read"))
    if mbp is None:
        return Rescore(entry.catalyst_date, frm, to, why=(
            f"{DATA_MISSING}: the entry states a move from {frm:,.2f} and "
            f"this name has no live MBP to check it against"))
    if abs(frm - mbp) > RESCORE_TOLERANCE:
        return Rescore(entry.catalyst_date, frm, to, why=(
            f"{DATA_MISSING}: the entry states a move from {frm:,.2f} and "
            f"the live MBP is {mbp:,.2f}; the two do not reconcile, so "
            f"nothing here reads the move as this name's"))
    return Rescore(entry.catalyst_date, frm, to, stated=True)


#: How much of a catalyst note the qualifying clause carries. CTSH's runs
#: to four hundred characters of tier arithmetic; the FIRST SENTENCE names
#: the event, and the operative figure inside the rest is read out
#: separately by `rescore` and stated as its own clause. The whole note is
#: on the name's card, uncut.
def lead_sentence(text: str | None) -> str:
    if not text:
        return ""
    body = str(text).strip()
    cut = body.find(". ")
    lead = body[:cut] if cut > 0 else body
    # No trailing stop: the clause this joins into supplies its own
    # punctuation, and "reassessment.;" is what happens otherwise.
    return lead.rstrip(". ")


def qualifying_clause(row: "NameRow") -> str:
    """The conditions that qualify a buy-side reading of this name.

    **THE WHOLE POINT IS THAT IT RIDES IN THE SAME BREATH.** CTSH's close
    sat below its maximum buy price and the entry said, in its own note,
    that the same buy price is scheduled to fall to a level the close is
    ABOVE -- so the crossing the top line announced would not exist after
    the event it was waiting for. A page that states the first half and
    withholds the second is worse than one that states neither.
    """
    parts: list[str] = []
    meaning = STATUS_MEANING.get(row.status)
    parts.append(meaning if meaning else f"its status is {row.status}")
    if row.catalyst_date is not None and row.catalyst_resolved is None:
        when = row.catalyst_date.isoformat()
        lead = lead_sentence(row.catalyst_event) or DATA_MISSING
        # The date is not repeated where the owner's own sentence already
        # carries it.
        parts.append(f"it is waiting on {lead}"
                     if when in lead else
                     f"it is waiting on {lead} ({when})")
    elif row.catalyst_date is None:
        parts.append(f"the entry records no catalyst date, so what would "
                     f"change this is {DATA_MISSING}")
    move = row.rescore
    if move.ok:
        tail = ""
        if row.price is not None and move.to is not None:
            tail = (f", and the close {row.price:,.2f} is ABOVE that — this "
                    f"crossing would not exist after the re-score"
                    if row.price > move.to else
                    f", and the close {row.price:,.2f} is below that too")
        parts.append(f"the entry states a scheduled re-score on "
                     f"{move.when.isoformat() if move.when else DATA_MISSING} "
                     f"moving the maximum buy price from {move.frm:,.2f} to "
                     f"{move.to:,.2f}{tail}")
    elif move.why:
        parts.append(move.why)
    return "; ".join(parts)


#: What the top line looked at, printed BESIDE it whether or not it found
#: anything. Silence has to be distinguishable from not having looked --
#: the dead man's switch's own argument, applied to a sentence.
ATTENTION_CHECKS = (
    "every stop against its close",
    "every maximum buy price against its close",
    f"the next {ATTENTION_HORIZON_DAYS} days of the calendar",
)


@dataclass(frozen=True)
class CalendarItem:
    when: date
    ticker: str
    status: str
    event: str
    decides: str
    resolved: date | None
    docs: tuple[Doc, ...] = ()


@dataclass(frozen=True)
class Event:
    """One dated thing that has happened: a ruling, a strike, a verdict."""

    when: date | None
    kind: str
    title: str
    detail: str
    href: str | None = None
    #: "stated", "inferred from the text", or DATA MISSING. A ruling whose
    #: date had to be inferred says so rather than passing as recorded.
    dated_by: str = "stated"


@dataclass
class Overview:
    generated: datetime
    as_of: date
    settled: date
    #: What needs the owner today. Empty is an ANSWER, not an absence.
    attention: list["Attention"]
    #: Which run this page stands on. Printed in the footer, always.
    stamp: "RunStamp"
    rows: list[NameRow]
    queue: list[QueueItem]
    calendar: list[CalendarItem]
    events: list[Event]
    shadow: list
    shadow_note: str
    #: Anything that failed to load. Printed at the top of the page: a
    #: source that could not be read is the one thing a state page must
    #: never be silent about.
    problems: list[str]
    sources: list[tuple[str, str]]


# --- reading the record ----------------------------------------------------


def store_tickers(manual_dir: Path = MANUAL_DIR) -> list[str]:
    """Every ticker with a figure store. Backups and the schema are not stores.

    `config/manual/` holds `.yaml.bak-<date>-...` copies beside the live
    files; `*.yaml` does not match them, and that is deliberate rather than
    lucky — a backup read as a store would double every name. `TEMPLATE.yaml`
    is the committed EMPTY schema and is excluded here for the reason
    `screen` and `reference_figures` both exclude it: it is a file that
    loads and names no company.
    """
    if not manual_dir.exists():
        return []
    return sorted(p.name[: -len(".yaml")] for p in manual_dir.glob("*.yaml")
                  if p.name != TEMPLATE_PATH.name)


def vendor_industries(db_path: Path = DB_PATH) -> tuple[dict[str, str], str]:
    """The stored vendor industry strings, and why there are none.

    E51's and E96's INDUSTRY limbs decide on these. Fundamentals reach the
    survivors of filter 1 alone, so a name with no string is one the limb is
    BLIND to — a fact about the fetch, printed on the row rather than read
    as a pass.
    """
    if not db_path.exists():
        return {}, f"{db_path} is not on disk"
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        return {}, f"{db_path} would not open: {exc}"
    try:
        rows = conn.execute(
            "SELECT ticker, industry FROM vendor_strings").fetchall()
    except sqlite3.Error as exc:
        return {}, f"vendor_strings is not readable: {exc}"
    finally:
        conn.close()
    return {t: i for t, i in rows if i}, ""


def cache_fetcher(cache_dir: Path = CACHE_DIR):
    """A `Fetcher` that reads the price cache and NEVER the vendor.

    The page is generated from the repository. A generation that fetched
    would make the page's contents depend on the network being up and on
    the hour it ran, and a nightly run that already fetched has written the
    cache this reads.
    """

    seen: dict[str, FetchResult] = {}

    def fetch(ticker: str) -> FetchResult:
        # ONE READ PER SERIES. A name on the watchlist that is also in the
        # shadow book is asked for twice, and parsing a six-year CSV costs
        # more than everything else the page does with it. Nothing here
        # mutates a frame -- `metrics` and `sales` both return new ones --
        # so the same object is safe to hand to both readers.
        if ticker in seen:
            return seen[ticker]
        frame, fetched_at = read_cache(cache_dir, ticker)
        if frame is None:
            result = FetchResult(
                ticker, None, SOURCE_NONE, None,
                f"no cached bars for {ticker} in {cache_dir}")
        else:
            result = FetchResult(ticker, frame, SOURCE_CACHE, fetched_at, None)
        seen[ticker] = result
        return result

    return fetch


# --- the documents ---------------------------------------------------------

#: Filename shapes that name a ticker. Each is anchored on the ticker so a
#: one-letter ticker (`G` is in the universe) cannot match every file in the
#: directory — the reason these are patterns and not substring searches.
_STRIKE_KINDS = ("STRIKE", "DROP", "GATED", "CHAIN")


def _rel(path: Path, base: Path = REPORTS_DIR) -> str:
    """A link from the page's own directory. The page opens from disk.

    A path outside the project falls back to its absolute form rather than
    raising: this function is also how a path is NAMED in a refusal, and a
    refusal that crashes while explaining itself is worse than a long link.
    """
    path = Path(path)
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        pass
    try:
        return Path("..").joinpath(path.relative_to(PROJECT_ROOT)).as_posix()
    except ValueError:
        return path.as_posix()


def documents(ticker: str, *, root: Path = PROJECT_ROOT) -> tuple[Doc, ...]:
    """Every existing document for one name, linked, newest first.

    NOTHING IS SUMMARISED. This function finds files and nothing else — it
    never opens one, so it cannot accidentally lift a sentence out of a
    sourced document and print it without its page.
    """
    out: list[Doc] = []
    quoted = re.escape(ticker)
    reports = root / "reports"
    reference = root / "reference"

    def add(paths, kind: str, label) -> None:
        for path in sorted(paths, reverse=True):
            out.append(Doc(kind, label(path), _rel(path)))

    if reports.exists():
        add([p for p in reports.glob(f"BRIEFING-{ticker}-*.md")],
            "briefing", lambda p: p.stem)
        add([p for p in reports.iterdir()
             if re.fullmatch(rf"{quoted}-(reading|PREBUY|REVIEW)-.+\.md",
                             p.name)],
            "reading", lambda p: p.stem)
    if reference.exists():
        add([p for p in reference.iterdir()
             if re.fullmatch(rf"{quoted}-({'|'.join(_STRIKE_KINDS)})-.+\.md",
                             p.name)],
            "strike", lambda p: p.stem)
        add([p for p in reference.glob(f"INTAKE-{ticker}-*.md")],
            "intake", lambda p: p.stem)
    records = root / "reference" / "run-records"
    if records.exists():
        add([p for p in records.iterdir()
             if re.fullmatch(rf"{quoted}-\d{{4}}-\d{{2}}-\d{{2}}.*\.json",
                             p.name)],
            "run record", lambda p: p.stem)
    view = root / "reference" / "growth-views" / f"{ticker}.md"
    if view.exists():
        out.append(Doc("growth view", view.name, _rel(view)))
    store = root / "config" / "manual" / f"{ticker}.yaml"
    if store.exists():
        out.append(Doc("store", store.name, _rel(store)))
    return tuple(out)


def run_records_for(ticker: str, *,
                    directory: Path = RUN_RECORDS_DIR) -> list[Path]:
    """Every run record on disk for a name, by filename.

    Used ONLY to print a PROVISIONAL value for a name whose entry carries
    no `fv_base`. A written `fv_base` is never taken from here: it comes
    off the entry, through `runner.load_run_record`, which replays the
    LINKED record and refuses anything that does not reconcile.
    """
    if not directory.exists():
        return []
    quoted = re.escape(ticker)
    return sorted(p for p in directory.iterdir()
                  if re.fullmatch(rf"{quoted}-\d{{4}}-\d{{2}}-\d{{2}}.*\.json",
                                  p.name))


def provisional_value(ticker: str, *,
                      directory: Path = RUN_RECORDS_DIR) -> Figure:
    """A run record's replay, marked PROVISIONAL, or why there is none.

    **THIS IS NOT A FAIR VALUE AND THE LABEL IS THE POINT.** A struck
    `fv_base` is written on the watchlist entry with its tier and its
    linked record; a record sitting in `reference/run-records/` that no
    entry names is arithmetic the owner has not adopted. E94's INDICATIVE
    value has the same standing and the same rule: printed, never written,
    never an MBP, never a strike.
    """
    found = run_records_for(ticker, directory=directory)
    if not found:
        return Figure(why="no run record on disk")
    if len(found) > 1:
        # WHICH RECORD GOVERNS IS THE OWNER'S WRITE, NOT A FILENAME.
        # LII has a 2026-08-30 record and a 2026-08-30-e70 restrike of it,
        # and picking one by sort order would be this page deciding which
        # method stands -- E39's question, answered by a character class.
        # An entry that names one settles it; where none does, the page
        # says so and links both.
        return Figure(why=(
            f"{len(found)} run records exist for this name — "
            + ", ".join(f"`{p.name}`" for p in found)
            + " — and no entry names one, so which of them governs is not "
              "recorded. Nothing here chooses."))
    path = found[0]
    try:
        record = RunRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError, RecordError) as exc:
        return Figure(why=f"`{path.name}` does not load: {exc}")
    gaps = record.missing()
    if gaps:
        return Figure(why=(f"`{path.name}` is INCOMPLETE — absent: "
                           f"{'; '.join(gaps)}"))
    try:
        value = record.strike()
    except (RecordError, ValueError) as exc:
        return Figure(why=f"`{path.name}` does not replay: {exc}")
    return Figure(value, record.currency, "PROVISIONAL",
                  f"replay of `{path.name}`; no fv_base is written on the "
                  f"entry, so nothing has been adopted")


# --- the distances ---------------------------------------------------------


def distance(price: float | None, level: float | None,
             price_currency: str | None, level_currency: str | None,
             *, what: str) -> Distance:
    """``price / level - 1``, or the reason it must not be computed.

    **THE UNIT CHECK IS NOT OPTIONAL.** GBX and GBP are different codes
    meaning different units and a hundred apart; a distance struck across
    them is not a slightly wrong number, it is a wrong number of a size
    that reads as a screaming opportunity. Nothing here converts — a
    conversion needs a rate, a rate needs a date, and E24 freezes both onto
    the verdict rather than inventing them at render time.
    """
    if price is None:
        return Distance(why=f"{DATA_MISSING}: no settled close")
    if level is None:
        return Distance(why=f"{DATA_MISSING}: no {what}")
    if level == 0:
        return Distance(why=f"{DATA_MISSING}: {what} is zero")
    if not price_currency or not level_currency:
        # TWO UNKNOWNS ARE NOT A MATCH. Comparing an unstated currency with
        # another unstated currency and finding them equal is how a seam
        # gets crossed by a `!=` that happened to be False.
        return Distance(why=(
            f"{DATA_MISSING}: the "
            + ("close" if not price_currency else what)
            + " states no currency, so nothing can be compared with it"))
    if price_currency != level_currency:
        return Distance(why=(
            f"{DATA_MISSING}: UNIT SEAM — the close is quoted in "
            f"{price_currency or 'an unstated currency'} and the {what} is "
            f"in {level_currency or 'an unstated currency'}. No rate is "
            f"frozen onto this entry (E24), so no distance is struck."))
    return Distance(price / level - 1.0)


# --- view 1 ----------------------------------------------------------------


def collect_rows(entries: Sequence[WatchlistEntry], *, as_of: date,
                 settled: date, cache_dir: Path = CACHE_DIR,
                 manual_dir: Path = MANUAL_DIR,
                 records_dir: Path = RUN_RECORDS_DIR,
                 db_path: Path = DB_PATH,
                 root: Path = PROJECT_ROOT,
                 fetch=None,
                 problems: list[str] | None = None) -> list[NameRow]:
    """Every name with an entry or a store, one row each."""
    problems = problems if problems is not None else []
    industries, industry_why = vendor_industries(db_path)
    if industry_why:
        problems.append(f"the E51/E96 industry limb is blind everywhere: "
                        f"{industry_why}")
    # ONE fetcher for the whole page, so the shadow book and the name table
    # read a shared series once between them.
    fetch = fetch if fetch is not None else cache_fetcher(cache_dir)
    stores = set(store_tickers(manual_dir))
    by_ticker = {e.ticker: e for e in entries}

    rows: list[NameRow] = []
    for ticker in sorted(set(by_ticker) | stores):
        entry = by_ticker.get(ticker)
        fetched = fetch(ticker)
        # ONE LOAD PER STORE, and the loaded watchlist handed down. Both
        # the gate and a store-only row read this file, and
        # `registered_view_record` reads the watchlist for every name it is
        # asked about -- thirty-three parses of a 2,400-line YAML file for
        # a page that had already parsed it once.
        parsed, gate, gate_error = None, None, ""
        if ticker in stores:
            try:
                parsed = load_manual(ticker, directory=manual_dir)
                gate = gate_on_registered_view(parsed, as_of=as_of,
                                               entries=entries)
            except (ManualError, ConfigError, OSError) as exc:
                gate_error = str(exc)
                problems.append(f"{ticker}: the section 5 gate did not run: "
                                f"{exc}")
        industry = industries.get(ticker)
        circle = R.circle_of_competence(ticker, industry)
        docs = documents(ticker, root=root)

        if entry is not None:
            row = _row_from_entry(entry, fetched, as_of=as_of, settled=settled,
                                  records_dir=records_dir, manual_dir=manual_dir,
                                  root=root, problems=problems)
        else:
            row = _row_from_store(ticker, fetched, parsed=parsed,
                                  parse_error=gate_error, as_of=as_of,
                                  settled=settled, records_dir=records_dir,
                                  root=root)
        row.gate, row.gate_error = gate, gate_error
        if gate is not None or gate_error:
            # `refresh.waits_for` writes "read-back (N UNVERIFIED)". The
            # floor line carries the SAME N and the narrower count beside
            # it, so the shorter form is dropped rather than printed above
            # its own restatement. Nothing is lost: both counts survive,
            # each with its definition attached.
            row.waiting = tuple(
                w for w in row.waiting if not w.startswith("read-back (")
            ) + (_floor_line(gate, gate_error),)
        row.docs = docs
        row.circle = circle
        row.circle_blind = industry is None
        row.has_store = ticker in stores
        if circle is not None:
            row.section = SECTION_OUTSIDE
        elif row.status == "DROPPED":
            row.section = SECTION_DROPPED
        else:
            row.section = SECTION_LIVE
        rows.append(row)
    return rows


def _floor_line(gate, gate_error: str) -> str:
    """Read-backs ABOVE E108's floor, said in a way the other count cannot
    be mistaken for.

    `refresh.waits_for` counts every UNVERIFIED figure in the store, which
    is what the nightly E92 pointer says and what the phone shows. THE GATE
    COUNTS SOMETHING NARROWER: the figures the CURRENT BASIS reads, after
    E108's sensitivity floor has waived the ones that cannot move `fv_base`
    by 1%. MEKKO.HE stands at 25 by the first count and 2 by the second,
    and neither is wrong. A page that printed one of them alone would be
    read as contradicting the other, so it prints both with their
    definitions attached.
    """
    if gate is None:
        return (f"read-backs above E108's floor: {DATA_MISSING} — the store "
                f"did not load: {gate_error}")
    if gate.basis is None:
        return ("read-backs above E108's floor: none can be counted — the "
                "store supplies no twelve-month basis (E19), so section 5 "
                "reads nothing and no figure is above or below the floor")
    waived = sum(1 for f in gate.flags if "VERIFIED-EXEMPT" in f.detail)
    return (f"read-backs: {len(gate.blocking)} ABOVE E108's floor, of "
            f"{len(gate.unverified)} UNVERIFIED in the store — basis "
            f"{gate.basis.label}; {waived} waived by the floor as unable to "
            f"move fv_base by 1%, the rest not read at this basis")


def _price_fields(row: NameRow, computed: M.Metrics, fetched: FetchResult) -> None:
    row.price_fetched_at = fetched.fetched_at
    row.price = computed.last_close
    row.price_date = computed.last_close_date
    row.price_settled = computed.last_close_settled
    if computed.last_close is None:
        row.price_why = (f"{DATA_MISSING}: "
                         f"{fetched.error or 'the price cache holds no settled bar'}")


def _row_from_entry(entry: WatchlistEntry, fetched: FetchResult, *,
                    as_of: date, settled: date, records_dir: Path,
                    manual_dir: Path, root: Path,
                    problems: list[str]) -> NameRow:
    """One watchlist name, assessed by the SAME code the nightly run uses.

    `runner.build_row` is what strikes the MBP, replays the linked record
    and collects the blockers. Calling it here rather than recomputing is
    the difference between a page that shows the state and a page that
    shows a second opinion about it.
    """
    # The nightly's own judgement, calendar included, so the page and the
    # report never disagree about a block (owner, 2026-09-19).
    built = build_row(entry, fetched, as_of, settled,
                      calendars=_watchlist_calendars(), use_calendar=True)
    row = NameRow(ticker=entry.ticker, name=entry.name, status=entry.status,
                  section=SECTION_LIVE, currency=entry.currency)
    _price_fields(row, built.metrics, fetched)

    if built.fv_base is not None:
        # THE FAIR VALUE'S CURRENCY IS THE RECORD'S, NOT THE ENTRY'S, and
        # AUTO.L is why. Its entry says GBX because the price series is in
        # pence; its `fv_base` 4.82 is written in GBP to match the linked
        # record, and the entry records that seam as OPEN. Taking the
        # currency off the entry would make the two agree by assumption and
        # print a distance of about +10,500%.
        record, _ = load_run_record(entry)
        row.fv = Figure(built.fv_base,
                        record.currency if record is not None else None, "",
                        f"struck; `{entry.run_record}` replays to it"
                        + ("" if record is not None else
                           f" — but its currency is {DATA_MISSING}"))
    elif built.fv_refused:
        row.fv = Figure(why=f"{DATA_MISSING}: {built.fv_refused}")
    else:
        row.fv = provisional_value(entry.ticker, directory=records_dir)

    # E24 / the AUTO.L seam: `fv_base` is stated in the RECORD's currency,
    # which is NOT always the quote currency the close is in. The entry
    # names the quote currency; the record names its own. NO FALLBACK to
    # the entry's code -- defaulting an unstated currency to the quote
    # currency is how the two are made to agree by assumption.
    row.dist_fv = distance(row.price, row.fv.amount, entry.currency,
                           row.fv.currency, what="fair value")
    row.mbp = built.assessment.mbp
    row.mbp_superseded = built.assessment.mbp_superseded
    row.stop_price = entry.stop_price
    row.catalyst_date = entry.catalyst_date
    row.catalyst_resolved = entry.catalyst_resolved
    row.catalyst_event = entry.catalyst_event
    row.rescore = rescore(entry, built.assessment.mbp)
    row.dist_mbp = distance(row.price, row.mbp, entry.currency,
                            entry.currency, what="MBP")
    row.pos = position(row.price, row.fv.amount, row.mbp,
                       why=row.dist_fv.why)
    # A LEVEL REACHES THE PICTURE ONLY WHERE THE DISTANCE WAS STRUCK. That
    # is the one place the currencies were compared, and passing the
    # figure through its own refusal is what stops a GBP fair value being
    # drawn across a chart of pence.
    row.spark = spark(
        fetched.frame, as_of=as_of, settled=settled,
        fv=row.fv.amount if row.dist_fv.value is not None else None,
        mbp=row.mbp if row.dist_mbp.value is not None else None)

    waits: list[str] = []
    row.retained = built.retained
    row.blockers = tuple(b.code for b in built.assessment.blockers)
    row.verdicts = tuple(v.code for v in built.assessment.verdicts)
    for blocker in built.assessment.blockers:
        waits.append(f"BLOCKED — {blocker.code}: {blocker.reason}"
                     if blocker.reason else f"BLOCKED — {blocker.code}")
    for verdict in built.assessment.verdicts:
        waits.append(str(verdict))
    try:
        waits.extend(waits_for(entry, manual_dir=manual_dir, root=root))
    except Exception as exc:      # noqa: BLE001 — a page must not die on one name
        problems.append(f"{entry.ticker}: waits_for failed: "
                        f"{type(exc).__name__}: {exc}")
        waits.append(f"{DATA_MISSING}: what this name waits on could not be "
                     f"computed")
    row.waiting = tuple(waits)
    return row


def _row_from_store(ticker: str, fetched: FetchResult, *, parsed,
                    parse_error: str, as_of: date, settled: date,
                    records_dir: Path, root: Path) -> NameRow:
    """A name with figures and no entry. It is on the page BECAUSE of that.

    E109 and E111 both turn on this case: entering a name stamps
    `dd_at_entry` and freezes Gate 1 (E12), so a store built before the
    owner has decided to watch anything is exactly right and must not be
    invisible. There is no status, no tier and no MBP, and each of those is
    a legitimate state rather than a gap.
    """
    computed = (M.compute(fetched.frame, as_of, settled)
                if fetched.frame is not None else M.Metrics())
    row = NameRow(ticker=ticker, name="", status=STATUS_STORE_ONLY,
                  section=SECTION_LIVE, has_entry=False)
    _price_fields(row, computed, fetched)
    if parsed is not None:
        row.name = parsed.name
        row.currency = parsed.quote_currency
    else:
        row.name = f"{DATA_MISSING}: the store would not load — {parse_error}"
        row.currency = None

    row.fv = provisional_value(ticker, directory=records_dir)
    row.dist_fv = distance(row.price, row.fv.amount, row.currency,
                           row.fv.currency, what="fair value")
    row.dist_mbp = Distance(why=(
        "no MBP: the MBP is the base-case value x the tier cushion (E90) "
        "and a tier follows a §4.4 score, which follows the E76 reading. "
        "A name with no entry has none of them, and that is a state, not a "
        "gap."))
    row.pos = position(row.price, row.fv.amount, None, why=row.dist_fv.why)
    row.spark = spark(fetched.frame, as_of=as_of, settled=settled,
                      fv=row.fv.amount if row.dist_fv.value is not None else None)
    row.waiting = ("no watchlist entry — nothing is watched, and entering "
                   "the name stamps E12's frozen Gate 1, which is the "
                   "owner's act",)
    return row


# --- view 2 ----------------------------------------------------------------


def collect_queue(rows: Sequence[NameRow], entries: Sequence[WatchlistEntry],
                  *, manual_dir: Path = MANUAL_DIR,
                  views_dir: Path = GROWTH_VIEWS_DIR,
                  root: Path = PROJECT_ROOT,
                  problems: list[str] | None = None) -> list[QueueItem]:
    """The queue, READ FROM THE RECORD rather than written by hand.

    Every item here is computed from a file that already exists, so an
    owner who does the work sees the item disappear on the next generation
    without touching this page. That is `refresh.waits_for`'s rule applied
    to the whole list.
    """
    problems = problems if problems is not None else []
    by_ticker = {e.ticker: e for e in entries}
    out: list[QueueItem] = []

    for row in rows:
        if row.section == SECTION_DROPPED:
            continue
        entry = by_ticker.get(row.ticker)

        # A missing stop on a HELD name. `rules.stop_blocker` is what
        # decides this and `build_row` has already run it; the queue reads
        # the blocker rather than re-deciding when a stop is required.
        if NO_STOP in row.blockers:
            out.append(QueueItem(
                Q_STOP, row.ticker, 1,
                "the name is BLOCKED and collects no verdict at all until a "
                "stop exists (FRAMEWORK 0.4 / 6.4)",
                "one `stop_price:` on the entry, at a level the owner "
                "strikes. The tool never derives one, and a guessed stop is "
                "worse than none.",
                row.docs))
        elif NO_STOP_PRE_ENTRY in row.verdicts and row.status == "WATCH-PRICED":
            # ONLY WATCH-PRICED. `pre_entry_stop_flag` fires on every
            # non-HELD name with no stop, DROPPED and INTAKE included, and
            # a queue that asked for a stop on a dropped name would be
            # asking for work nobody wants done. A WATCH-PRICED name is one
            # that passed section 5 and is only too expensive -- it is the
            # one that can become a buy, and FRAMEWORK 0.4 rule 4 says a
            # buy is a price, a condition AND a stop.
            out.append(QueueItem(
                Q_STOP, row.ticker, 1,
                "a buy verdict on this name becomes actionable; today it "
                "carries the NO STOP DEFINED flag (FRAMEWORK 0.4 rule 4)",
                "one `stop_price:`. The watchlist records the alternative "
                "as an OPEN E-candidate -- a `stop_price` FORM carrying a "
                "pre-registered derivation resolved at the actual blended "
                "entry -- and until that is ruled, a WATCH name's stop "
                "stays null and the level is written at entry.",
                row.docs))

        if row.section == SECTION_OUTSIDE:
            # E51/E96 remove the name from section 5 entirely. There is no
            # read-back to do and no view to register: the queue would be
            # asking for work the ruling forbids.
            continue

        gate = row.gate
        if row.gate_error:
            out.append(QueueItem(
                Q_READBACK, row.ticker, None,
                "nothing can be said about this store until it loads",
                f"{DATA_MISSING}: {row.gate_error}", row.docs))

        view = _registered_view(row.ticker, entry, views_dir=views_dir)
        if row.has_store and view is None:
            out.append(QueueItem(
                Q_VIEW, row.ticker, 1,
                "no fair value may be struck at all (E28), and E108's "
                "MEASURED limb cannot run, so the read-back gate stands at "
                "its strictest",
                "one pre-registered growth view — bear, base and bull, in "
                "the owner's own words. NEVER inferred, defaulted or "
                "borrowed from a peer (E94).",
                row.docs))

        if gate is not None and gate.blocking:
            out.append(QueueItem(
                Q_READBACK, row.ticker, len(gate.blocking),
                f"section 5 is REFUSED on {len(gate.blocking)} UNVERIFIED "
                f"figure(s) the basis reads (E21)",
                _readback_detail(gate),
                row.docs))

        if (row.fv.amount is None
                and "run records exist for this name" in row.fv.why):
            out.append(QueueItem(
                Q_RECORD, row.ticker, 1,
                "a value can be printed for this name at all; today the "
                "page refuses to choose which of its records governs",
                row.fv.why + " One `run_record:` on the entry settles it "
                             "(E39: a fair value struck on a superseded "
                             "method is NULLED, not left standing).",
                row.docs))

        if row.fv.label == "PROVISIONAL" and row.fv.amount is not None:
            blocking = len(gate.blocking) if gate is not None else None
            actions = None if blocking is None else blocking + 1
            out.append(QueueItem(
                Q_PROVISIONAL, row.ticker, actions,
                "the value becomes a struck fv_base with an MBP behind it",
                _provisional_detail(row, blocking),
                row.docs))

    out.extend(_needs_owner_items(entries, root=root, manual_dir=manual_dir,
                                 problems=problems))
    out.sort(key=lambda item: item.sort_key)
    return out


def _registered_view(ticker: str, entry: WatchlistEntry | None, *,
                     views_dir: Path):
    """The registered growth view, from EITHER place E109 allows.

    E109 put the machine-readable numbers on the watchlist entry and left
    the words in `reference/growth-views/`. A name with no entry can only
    have the file (BOUV.OL is the case E109 names), so both are consulted
    and either one counts as registered.
    """
    if entry is not None and entry.growth is not None:
        return entry.growth
    view = R.read_growth_view(ticker, directory=views_dir)
    if view is not None and view.registered:
        return view
    return None


def _readback_detail(gate) -> str:
    fields = sorted({f"{f.period or 'market'} {f.name}" for f in gate.blocking})
    shown = ", ".join(fields[:6]) + ("…" if len(fields) > 6 else "")
    waived = sum(1 for f in gate.flags if "VERIFIED-EXEMPT" in f.detail)
    return (f"basis {gate.basis.label if gate.basis else DATA_MISSING}. "
            f"Each is read back against the page the store already names "
            f"and set to `status: verified`. {shown}. "
            f"E108's floor has already waived {waived} other figure(s) on "
            f"this store — these are the ones above it.")


def _provisional_detail(row: NameRow, blocking: int | None) -> str:
    steps = []
    if blocking:
        steps.append(f"{blocking} read-back(s) first")
    elif blocking == 0:
        steps.append("no read-back is outstanding")
    else:
        steps.append(f"the read-back count is {DATA_MISSING} — no store loads")
    steps.append("then the owner's write of `fv_base`, `tier` and "
                 "`run_record` on the entry")
    return (f"{row.fv.why}. To convert it: " + ", ".join(steps) +
            ". Nothing here writes any of them.")


def _needs_owner_items(entries: Sequence[WatchlistEntry], *, root: Path,
                       manual_dir: Path,
                       problems: list[str]) -> list[QueueItem]:
    """E92's open pointers, from `data/refresh_state.json`.

    An ABSENT state file means no report-date refresh has ever run, which
    is a different fact from *nothing is waiting* — so it is reported as
    itself rather than as an empty list.
    """
    from .refresh import STATE_PATH

    if not STATE_PATH.exists():
        problems.append(
            f"NEEDS OWNER (E92): `{_rel(STATE_PATH)}` is not on disk, so no "
            f"report-date refresh has recorded anything. That is not the "
            f"same as nothing waiting.")
        return []
    try:
        pending = e92_needs_owner(entries, manual_dir=manual_dir, root=root)
    except Exception as exc:      # noqa: BLE001
        problems.append(f"NEEDS OWNER (E92) could not be computed: "
                        f"{type(exc).__name__}: {exc}")
        return []
    return [QueueItem(Q_NEEDS_OWNER, item.ticker, len(item.waits),
                      "the refresh has already fetched, extracted and "
                      "reported; nothing downstream moves until the owner "
                      "acts (E92)",
                      "; ".join(item.waits) +
                      (f". Report: {item.report}" if item.report else ""),
                      (Doc("refresh report", item.report,
                           _rel(root / item.report)),) if item.report else ())
            for item in pending]


def collect_calendar(entries: Sequence[WatchlistEntry], *,
                     root: Path = PROJECT_ROOT) -> list[CalendarItem]:
    """Every `catalyst_date` on the watchlist, with what it decides.

    `catalyst_event` is the owner's own sentence about what the date
    settles. Where an entry carries a date and no event, the cell says
    DATA MISSING: a date with nothing attached decides nothing that can be
    checked afterwards.
    """
    out: list[CalendarItem] = []
    for entry in entries:
        if entry.catalyst_date is None:
            continue
        out.append(CalendarItem(
            entry.catalyst_date, entry.ticker, entry.status,
            entry.catalyst_event or DATA_MISSING,
            entry.catalyst_event or
            f"{DATA_MISSING}: the entry names a date and no event, so what "
            f"this date decides is not recorded",
            entry.catalyst_resolved,
            documents(entry.ticker, root=root)))
    out.sort(key=lambda item: (item.when, item.ticker))
    return out


# --- view 3 ----------------------------------------------------------------

_RULING = re.compile(r"^###\s+(?P<title>.+?)\s*$")
#: How a ruling states its own date. Checked in order, and the first that
#: matches wins; a section that matches none takes the first date in its
#: opening lines and is LABELLED as inferred, so a reader can tell a
#: recorded date from a read one.
_DATE_MARKERS = (
    re.compile(r"\bRULED\b[^\n]{0,90}?(\d{4}-\d{2}-\d{2})", re.I),
    re.compile(r"\bDECIDED\b[^\n]{0,90}?(\d{4}-\d{2}-\d{2})", re.I),
    re.compile(r"\bowner[^\n]{0,60}?(\d{4}-\d{2}-\d{2})", re.I),
)
_ANY_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
#: How far into a section to look. A ruling states its date at the top; a
#: date forty lines down is a date in an argument, not the ruling's own.
_DATE_WINDOW = 15


def rulings(path: Path = FRAMEWORK_EDITS) -> tuple[list[Event], list[str]]:
    """Every ruling in FRAMEWORK-EDITS, with its date and how it was got."""
    problems: list[str] = []
    if not path.exists():
        return [], [f"{_rel(path)} is not on disk, so no ruling is listed"]
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"{_rel(path)} would not read: {exc}"]

    heads = [i for i, line in enumerate(lines) if _RULING.match(line)]
    heads.append(len(lines))
    out: list[Event] = []
    for start, stop in zip(heads, heads[1:]):
        title = _RULING.match(lines[start]).group("title")
        window = "\n".join(lines[start:min(start + _DATE_WINDOW, stop)])
        when, how = None, DATA_MISSING
        for marker in _DATE_MARKERS:
            found = marker.search(window)
            if found:
                when, how = _as_date(found.group(1)), "stated"
                break
        else:
            found = _ANY_DATE.search(window)
            if found:
                when, how = _as_date(found.group(1)), "inferred from the text"
        if when is None and how != DATA_MISSING:
            how = DATA_MISSING
        # NO PER-ROW DETAIL. The `###` heading IS the ruling stated in one
        # line, in the owner's own words, and a generic sentence repeated
        # under every one of them is noise that hides the verdict rows'
        # detail, which is not generic at all.
        out.append(Event(when, "ruling", title, "", f"{_rel(path)}", how))
    undated = sum(1 for e in out if e.when is None)
    if undated:
        problems.append(
            f"{undated} of {len(out)} rulings state no date in their opening "
            f"{_DATE_WINDOW} lines. They are listed UNDATED rather than "
            f"dropped.")
    return out, problems


def _as_date(text: str) -> date | None:
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


_DOC_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def strike_events(root: Path = PROJECT_ROOT) -> list[Event]:
    """Every strike, drop, gating and intake document, by its own date."""
    out: list[Event] = []
    reference = root / "reference"
    if not reference.exists():
        return out
    pattern = re.compile(
        rf"^(?P<ticker>[A-Z0-9][A-Z0-9.\-]*)-(?P<kind>{'|'.join(_STRIKE_KINDS)})"
        rf"-(?P<date>\d{{4}}-\d{{2}}-\d{{2}})(?P<tail>.*)\.md$")
    for path in sorted(reference.iterdir()):
        found = pattern.match(path.name)
        if found:
            out.append(Event(
                _as_date(found.group("date")), found.group("kind").lower(),
                f"{found.group('ticker')} — {found.group('kind')}"
                f"{found.group('tail')}",
                "", _rel(path)))
            continue
        intake = re.fullmatch(
            r"INTAKE-(?P<ticker>[A-Z0-9][A-Z0-9.\-]*)-"
            r"(?P<date>\d{4}-\d{2}-\d{2})\.md", path.name)
        if intake:
            out.append(Event(_as_date(intake.group("date")), "intake",
                             f"{intake.group('ticker')} — INTAKE",
                             "read, not watched (E111)", _rel(path)))

    return out


def verdict_events(book) -> list[Event]:
    """The shadow book's verdicts. `decided_by` is the owner's own words."""
    return [Event(v.verdict_date, "verdict",
                  f"{v.ticker} — {v.verdict} ({v.standing})",
                  v.decided_by, _rel(SHADOW_BOOK_PATH))
            for v in book]


# --- assembly --------------------------------------------------------------


def collect(*, now: datetime | None = None,
            watchlist_path: Path = WATCHLIST_PATH,
            cache_dir: Path = CACHE_DIR,
            manual_dir: Path = MANUAL_DIR,
            records_dir: Path = RUN_RECORDS_DIR,
            views_dir: Path = GROWTH_VIEWS_DIR,
            edits_path: Path = FRAMEWORK_EDITS,
            book_path: Path = SHADOW_BOOK_PATH,
            db_path: Path = DB_PATH,
            root: Path = PROJECT_ROOT) -> Overview:
    """Read every source and build the whole page's contents. Writes nothing."""
    run_ts = now or datetime.now().astimezone()
    as_of = run_ts.date()
    settled = M.settled_through(run_ts)
    problems: list[str] = []

    # A malformed watchlist fails the WHOLE generation loudly (SPEC.md 5).
    # A page that quietly showed an empty book would be the exact failure
    # this page exists to remove, so nothing here catches it.
    entries = load_watchlist(watchlist_path)

    fetch = cache_fetcher(cache_dir)
    rows = collect_rows(entries, as_of=as_of, settled=settled,
                        cache_dir=cache_dir, manual_dir=manual_dir,
                        records_dir=records_dir, db_path=db_path, root=root,
                        fetch=fetch, problems=problems)
    queue = collect_queue(rows, entries, manual_dir=manual_dir,
                          views_dir=views_dir, root=root, problems=problems)
    calendar = collect_calendar(entries, root=root)

    events, ruling_problems = rulings(edits_path)
    problems.extend(ruling_problems)
    events.extend(strike_events(root))

    shadow: list = []
    shadow_note = ""
    try:
        book = load_shadow_book(book_path)
        events.extend(verdict_events(book))
        shadow = shadow_rows(book, settled=settled, fetch=fetch)
        shadow_note = (f"{len(book)} verdict(s) in `{_rel(book_path)}`, "
                       f"measured off the price cache in `{_rel(cache_dir)}` "
                       f"— settled bars only, no fetch.")
    except (ConfigError, OSError) as exc:
        problems.append(f"the shadow book did not load: {exc}")
        shadow_note = f"{DATA_MISSING}: {exc}"

    events.sort(key=lambda e: (e.when is not None, e.when or date.min,
                               e.kind, e.title), reverse=True)

    sources = [
        ("the watchlist", _rel(watchlist_path)),
        ("the figure stores", _rel(manual_dir)),
        ("the growth views", _rel(views_dir)),
        ("the run records", _rel(records_dir)),
        ("the rulings", _rel(edits_path)),
        ("the shadow book", _rel(book_path)),
        ("the price cache", _rel(cache_dir)),
    ]
    needed = attention(rows, calendar, as_of=as_of)
    stamp = run_stamp(now=run_ts, db_path=db_path, rows=rows)
    return Overview(run_ts, as_of, settled, needed, stamp, rows, queue,
                    calendar, events, shadow, shadow_note, problems, sources)


# --- writing ---------------------------------------------------------------


def write_overview(*, output: Path = OUTPUT_PATH, **kwargs) -> Path:
    """Generate the page and write it. THE ONLY WRITE IN THIS PACKAGE PAIR.

    `output` is under `reports/` and the nightly unit's `ReadWritePaths=`
    reaches `data/` and `reports/` alone -- so a generation that tried to
    write anywhere else would be refused by systemd as well as by this
    function.

    The HTML lives in `vss.render`, imported HERE rather than at module
    scope: `collect` is the half that reads the record, and a caller that
    only wants the figures should not have to load a stylesheet to get
    them.
    """
    from .render import render

    output = Path(output)
    if output.suffix.lower() != ".html":
        raise ValueError(f"the overview is an HTML file, not {output.name}")
    overview = collect(**kwargs)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(overview), encoding="utf-8")
    log.info("wrote %s: %d name(s), %d needing you today, %d queue item(s), "
             "%d event(s), %d problem(s)", output, len(overview.rows),
             len(overview.attention), len(overview.queue),
             len(overview.events), len(overview.problems))
    return output
