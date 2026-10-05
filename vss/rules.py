"""Pure rule logic for vss.

This module performs ZERO I/O. No file access, no network, no logging, and
deliberately no ``datetime.now()`` -- every rule that needs "today" takes an
``as_of`` date as a parameter so it can be tested at any point in time.

Inputs are plain scalars; outputs are Verdict / Blocker / TickerAssessment
objects. Nothing here touches pandas or yfinance.

Authority for these rules, in order of precedence:
  1. The SCOPE given by the user, plus their explicit answers on
     verdict combination, RSI's role, DATA MISSING reach and --dry-run.
  2. reference/SPEC.md, for the items that do not conflict with (1):
     inclusive dislocation band, 52w high semantics, DATA MISSING never
     meaning FAIL, and blockers being emitted instead of verdicts.

The catalyst gate reads the structured ``catalyst_resolved`` date only.
It never parses ``notes``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence

# --- Constants -------------------------------------------------------------

#: MBP is COMPUTED, never entered by hand. E28's engine, wired 2026-08-26
#: after E42: mbp = the linked run record's BEAR-CASE value * multiplier[tier]
#: (`compute_mbp_e28`). Where no record supplies a bear case the superseded
#: `fv_base * multiplier[tier]` (`compute_mbp`) still computes, and is MARKED.
#:
#: E32: THIS ARITHMETIC IS THE SUPERSEDED DEFINITION. E28's MBP is the
#: price at which implied growth equals the pre-registered bear case, with
#: the same cushion applied to THAT. `compute_mbp` is kept working -- three
#: stored figures were struck under it and E32 retains them -- and every
#: number it produces is marked wherever it prints.
MBP_TIER_MULTIPLIER: dict[int, float] = {1: 0.80, 2: 0.70, 3: 0.60}

#: E90 (2026-08-30): THE LIVE DEFINITION. MBP = the BASE-case value x this
#: cushion -- tier 1 0.85 / tier 2 0.75 / tier 3 0.65 (the 0.10 step
#: continued, decided at the ruling's read-back). The cushion covers MODEL
#: AND INPUT ERROR -- REVIEW-4's actual fault class, typically 5-15% of
#: value -- and NOT scenario risk, which the pre-registered growth views
#: carry. E28's bear-value arithmetic is superseded; bear and bull values
#: stay printed as information. MBP_TIER_MULTIPLIER above is KEPT for the
#: superseded paths' history (E32's three retained figures).
MBP_TIER_CUSHION_E90: dict[int, float] = {1: 0.85, 2: 0.75, 3: 0.65}

#: E32's marker. Appended rather than substituted, so a reader who knows
#: the old sentence still finds it and cannot miss what is now beside it.
MBP_SUPERSEDED_MARK = "[SUPERSEDED DEFINITION, E32]"

#: Which definition an mbp was struck under. E32 supersedes the first AS A
#: DEFINITION and keeps it as a VALUE, because three stored figures carry
#: it. Defined here rather than in `config` because `config` imports this
#: module and not the other way round; one spelling, one place.
MBP_DEF_SUPERSEDED = "fv_base_x_tier"
MBP_DEF_E28 = "e28_bear_case"
#: E90 (2026-08-30): the live definition -- base-case value x tier cushion.
MBP_DEF_E90 = "e90_base_cushion"
VALID_MBP_DEFINITIONS = (MBP_DEF_SUPERSEDED, MBP_DEF_E28, MBP_DEF_E90)

#: Dislocation band, both bounds INCLUSIVE. Exactly 0.15 and exactly 0.50
#: are inside the band and therefore do NOT raise OUTSIDE DISLOCATION BAND.
DISLOCATION_MIN = 0.15
DISLOCATION_MAX = 0.50

#: price <= mbp * this factor (and above mbp) => APPROACHING MBP.
APPROACHING_MBP_FACTOR = 1.05

#: A close strictly older than this many TRADING days blocks the ticker.
#:
#: FRAMEWORK-EDITS C3, DECIDED 2026-08-26 -- ruled by the owner after
#: REVIEW-4; the trading days are sessions on the EXCHANGE CALENDAR where
#: the caller supplies one (E47; the screener does, `vss/calendars.py`). This
#: was three CALENDAR days and the comment here defended the choice. The
#: defence was wrong in the one direction that costs money: measured in
#: calendar days, EVERY held name is blocked -- no stop check, no verdict --
#: on the first trading day after any holiday of two days or more. Measured
#: by REVIEW-4 report A 4.2: the Tuesday after US Memorial Day 4 days, the
#: Tuesday after Easter 5, the Monday after Midsommar 4. The day after a
#: long weekend is precisely the day the stop check should run.
#:
#: THE LIMIT IS UNCHANGED AT 3. On an ordinary week a trading day and a
#: calendar day coincide from Monday to Thursday, so this is the same
#: tightness the gate has always had -- what changed is that a market
#: holiday no longer counts against the feed.
MAX_CLOSE_AGE_TRADING_DAYS = 3


#: THE LIMIT FOR A NAME CARRYING A LEVEL (owner, 2026-09-19): a HELD name,
#: or one with an MBP or a stop, is BLOCKED when its newest close is more
#: than ONE trading day old; every other name keeps
#: MAX_CLOSE_AGE_TRADING_DAYS. A block is visible, a stale close is not.
#: The block names the last known close, its date and age, and says in
#: words that the level was NOT CHECKED. The exchange's closed days are not
#: counted (vss/calendars.py).
#:
#: A DRY RUN REFUSES on the same judgement -- exits with an error and prints
#: no report when any name carrying a level is blocked by it. Why, and the
#: case that found it:
#: THE DRY-RUN LIMIT (owner, 2026-09-19): a dry run REFUSES -- exits with an
#: error and prints no report -- when any name's newest settled close is
#: more than this many trading days old. A dry run is how a trigger is
#: checked by hand, and a trigger check on a stale close is the one failure
#: that loses money silently: a name crosses its MBP or stop and nothing
#: fires. Found on 2026-09-19: yfinance had no 2026-09-17 row and a NaN
#: close on 2026-09-18 for SAP.DE and LIAB.ST (a HELD name), so both were
#: served their 2026-09-16 close as "live" and passed the 3-session gate.
#: The nightly run keeps MAX_CLOSE_AGE_TRADING_DAYS and blocks per name.
MAX_CLOSE_AGE_TRADING_DAYS_LEVEL = 1


def carries_level(status: str | None, mbp: float | None,
                  stop_price: float | None) -> bool:
    """HELD, or an MBP or a stop to compare a close with."""
    return status == "HELD" or mbp is not None or stop_price is not None


def unchecked_levels(status: str | None, mbp: float | None,
                     stop_price: float | None) -> str:
    """The words a stale block carries for a name with a level."""
    parts = []
    if stop_price is not None:
        parts.append(f"stop {stop_price:,.2f}")
    if mbp is not None:
        parts.append(f"MBP {mbp:,.2f}")
    if not parts:
        parts.append("the HELD checks")
    return ("LEVEL NOT CHECKED: " + " and ".join(parts)
            + " -- tonight's close was not compared with it")

#: The CALENDAR-day limit on a PRICED FIGURE in a manual file (a market
#: capitalisation or enterprise value, which is struck on a date rather than
#: filed for a window). Left in calendar days deliberately: a priced figure
#: is not a feed, and nothing about it improves for being counted in
#: sessions. `manual.section5_gate` is its only consumer.
MAX_CLOSE_AGE_DAYS = 3

#: DROPPED is a RECORD, not a stage: a name rejected at some phase and
#: kept so it is not screened again from scratch, and so the reason
#: survives in notes. It collects no verdicts -- there is no position to
#: exit and no entry to prepare for, so the pre-entry stop flag and the
#: MBP checks would both be answering questions nobody is asking.
#: WATCH was split into two by FRAMEWORK-EDITS E27 (2026-08-25), because
#: the one word carried two states whose RE-ENTRY RULES ARE OPPOSITE:
#:
#:   WATCH-PRICED  the name passed section 5 and is merely too expensive.
#:                 Section 5.3 applies as written -- a limit-alert price,
#:                 armed, computed from MBP. Price is the correct trigger
#:                 because price is the only thing standing between the
#:                 analysis and the purchase.
#:   WATCH-GATED   the name failed a gate in section 3 and the failure was
#:                 NOT about price. Re-entry requires a named information
#:                 event, NEVER a price level, because the price was not
#:                 what disqualified it.
#:
#: The bare "WATCH" is GONE rather than aliased. A file that still carries
#: it has not yet said which state the name is in, and that is a question
#: only a person can answer -- so the validator refuses it and says so.
#: INTAKE (E111, 2026-09-04): READ, NOT WATCHED. A name whose figures have
#: been built into a store and whose growth view may be registered, so
#: E108's floor and E106 clause 4 can run for it -- and which carries NO
#: entry stamp of any kind.
#:
#: **THE GROUND IS E12's OWN.** E12 freezes Gate 1 because a PIPELINE name
#: is review work with a DATED STARTING POINT. A name somebody has only read
#: the figures of has no such starting point and must not acquire one by
#: accident -- but its growth view has to live where a machine can read it
#: (E109 put that on the watchlist entry), and before this the only way to
#: get an entry was to start the clock. PROMOTION TO PIPELINE IS WHAT STAMPS
#: E12's ENTRY, and that promotion is the owner's act.
VALID_STATUSES = ("HELD", "WATCH-PRICED", "WATCH-GATED", "PIPELINE",
                  "INTAKE", "DROPPED")

#: What an INTAKE entry may NOT carry, because each is an ENTRY FACT and an
#: intake is not an entry. `tier` is on the list and that is what removes
#: the MBP: `compute_mbp` is fv_base x the tier multiplier, so a name with
#: no tier has no maximum buy price to be measured against.
INTAKE_REFUSED_KEYS = ("dd_at_entry", "peak_date", "stop_price", "tier",
                       "mbp_basis")

#: The two halves of the old WATCH, for code that means "waiting, not held".
#: Derived nowhere else: anything testing for a waiting name uses this.
WATCH_STATUSES = ("WATCH-PRICED", "WATCH-GATED")

#: What the validator says when it meets the retired spelling. Not an
#: auto-migration: E27 requires the reason to be stated on the row.
RETIRED_STATUSES = {
    "WATCH": (
        "WATCH was split by FRAMEWORK-EDITS E27 (2026-08-25). Use "
        "WATCH-PRICED if the name passed section 5 and is only too "
        "expensive (section 5.3 applies: a limit alert computed from MBP), "
        "or WATCH-GATED if it failed a section 3 gate on something other "
        "than price (re-entry on a named information event, never a price "
        "level). State the reason on the row."
    ),
}
VALID_TIERS = (1, 2, 3)


# --- Value objects ---------------------------------------------------------


@dataclass(frozen=True)
class Verdict:
    """One evaluated check. ``code`` is stable, ``label`` is for humans."""

    code: str
    label: str
    detail: str = ""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.label} ({self.detail})" if self.detail else self.label


@dataclass(frozen=True)
class Blocker:
    """A reason a ticker may not receive any verdict at all."""

    code: str
    reason: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.reason


@dataclass(frozen=True)
class TickerAssessment:
    ticker: str
    blockers: tuple[Blocker, ...] = ()
    verdicts: tuple[Verdict, ...] = ()
    mbp: float | None = None
    #: E32: this `mbp` was struck under the superseded `fv_base x tier`
    #: definition. True whenever an mbp exists and nothing says it came
    #: from E28's engine -- absence of a record is not evidence of one.
    mbp_superseded: bool = False

    @property
    def blocked(self) -> bool:
        return bool(self.blockers)

    @property
    def actionable(self) -> bool:
        """True when this ticker belongs in the ACTIONS section."""
        if self.blocked:
            return False
        return any(v.code not in (NO_ACTION, DROPPED, INTAKE)
                   for v in self.verdicts)


# Verdict codes
STOP_BREACHED = "STOP_BREACHED"
AT_BELOW_MBP = "AT_BELOW_MBP"
APPROACHING_MBP = "APPROACHING_MBP"
OUTSIDE_BAND = "OUTSIDE_BAND"
NO_STOP_PRE_ENTRY = "NO_STOP_PRE_ENTRY"
DROPPED = "DROPPED"
#: E111: the verdict an INTAKE name collects, which is none of the others.
INTAKE = "INTAKE"
DATA_MISSING = "DATA_MISSING"
NO_ACTION = "NO_ACTION"

# Blocker codes
NO_DATA = "NO_DATA"
STALE_DATA = "STALE_DATA"
#: E122(d): the vendor restated a close ACROSS a level this name carries.
#: The held close stands, the name collects no verdict, and the owner rules.
PRICE_CORRECTION = "PRICE_CORRECTION"
#: E121(e), amended 2026-09-20: the vendor printed a close on a day this
#: name's DERIVED calendar calls closed, so the suffix is mapped to the
#: wrong exchange and the session count may UNDER-state staleness.
CALENDAR_MISMATCH = "CALENDAR_MISMATCH"
#: The bull case a holding must carry is enforced where a name BECOMES
#: held -- `config.load_watchlist` refuses status HELD without `fv_bull`
#: (owner, 2026-09-20). NOT a blocker: a blocker suppresses every verdict,
#: and silencing a holding's STOP to enforce a bull would be the failure
#: the gate exists to prevent.
CATALYST_UNRESOLVED = "CATALYST_UNRESOLVED"
NO_STOP = "NO_STOP"


# --- MBP ------------------------------------------------------------------


def compute_mbp(fv_base: float | None, tier: int | None) -> float | None:
    """MBP = fv_base * tier multiplier, rounded to 2dp. THE SUPERSEDED PATH.

    Returns None -- meaning DATA MISSING -- when either input is absent.
    Never guesses a multiplier and never defaults a missing fv_base. Kept
    for names without a bear case (E32 retains three figures struck under
    it); every figure it produces is marked wherever it prints.
    """
    if fv_base is None or tier is None:
        return None
    multiplier = MBP_TIER_MULTIPLIER.get(tier)
    if multiplier is None:
        return None
    return round(float(fv_base) * multiplier, 2)


def compute_mbp_e90(base_value: float | None, tier: int | None) -> float | None:
    """E90's MBP: the BASE-case value x the tier cushion, rounded to 2dp.

    ``base_value`` is the fair value the linked run record replays to --
    the record struck at its pre-registered g_base -- and the cushion is
    E90's (0.85 / 0.75 / 0.65) applied to THAT. The cushion covers model
    and input error, not scenario risk; bear and bull stay printed as
    information, not the buy line. None when either input is absent --
    never a guessed cushion, never a defaulted value.
    """
    if base_value is None or tier is None:
        return None
    cushion = MBP_TIER_CUSHION_E90.get(tier)
    if cushion is None:
        return None
    return round(float(base_value) * cushion, 2)


def compute_mbp_e28(bear_value: float | None, tier: int | None) -> float | None:
    """SUPERSEDED BY E90 (2026-08-30) -- kept as the record of E28's
    arithmetic; nothing live calls it.

    E28's MBP: the PRE-REGISTERED bear case's fair value x the tier cushion.

    ``bear_value`` is the linked run record struck at its own `growth.bear`
    -- the price at which implied growth equals the bear case -- and the
    cushion is E32's multiplier applied to THAT, not to fv_base. Rounded to
    2dp from the unrounded bear value, as the Build 2 printout was (SAP.DE
    120.27 x 0.80 prints 96.21, not 96.22).

    None when either input is absent: a record that carries no bear case,
    or a name with no tier, has no E28 MBP, and `assess` falls back to the
    superseded arithmetic WITH its mark. The band across E29's +/-0.5% is
    on the record and the printout (`valuation.maximum_buy_price`); this
    is its mid.
    """
    if bear_value is None or tier is None:
        return None
    multiplier = MBP_TIER_MULTIPLIER.get(tier)
    if multiplier is None:
        return None
    return round(float(bear_value) * multiplier, 2)


# --- Blockers (SCOPE 4 -- the staleness gate) ------------------------------


def no_data_blocker(last_close: float | None, fetch_error: str | None) -> Blocker | None:
    """A ticker with no usable price data can never be evaluated."""
    if fetch_error and last_close is None:
        return Blocker(NO_DATA, f"fetch failed and no cached data: {fetch_error}")
    if last_close is None:
        return Blocker(NO_DATA, "no price data available")
    return None


def trading_days_between(
    start: date,
    end: date,
    *,
    holidays: frozenset[date] | set[date] = frozenset(),
) -> int:
    """Sessions from the day AFTER ``start`` through ``end`` inclusive.

    A TRADING day here is a weekday that is not in ``holidays``. NO CALENDAR
    IS BUILT IN, and that is deliberate: this module does no I/O and the
    universe spans seventeen exchanges whose holidays do not coincide. The
    exchange's closed days are the CALLER'S to supply, and with the default
    empty set this is Monday-to-Friday counting.

    WHO SUPPLIES THEM (E47, 2026-08-26): the screener does, from
    `vss/calendars.py` -- the universe row's market mapped to an exchange
    calendar -- for both the fetch-time STALE status and filter 1's gate.
    `vss run` still passes nothing: a watchlist entry carries no market, and
    a calendar guessed from a ticker suffix would be a guess.

    What the default costs, measured (SCREENER-REVIEW-3 Part 10): a weekday
    the exchange was shut still counts against the feed, so Christmas Eve to
    Boxing Day -- three closed weekdays on seven of eleven markets --
    collapsed a 3-session gate to ONE real session and removed a whole
    market on value the first morning after; Easter and New Year collapsed
    it to two on every European exchange. Still a smaller error, and in the
    safer direction, than the calendar-day rule this replaced -- which
    blocked on every ordinary two-day holiday (C3).

    Returns 0 when ``end`` is not after ``start``.
    """
    if end <= start:
        return 0
    sessions = 0
    day = start + timedelta(days=1)
    while day <= end:
        if day.weekday() < 5 and day not in holidays:
            sessions += 1
        day += timedelta(days=1)
    return sessions


def stale_close_blocker(
    last_close_date: date | None,
    as_of: date,
    max_age_trading_days: int = MAX_CLOSE_AGE_TRADING_DAYS,
    holidays: frozenset[date] | set[date] = frozenset(),
    *,
    last_close: float | None = None,
    level_note: str | None = None,
) -> Blocker | None:
    """BLOCK when the newest close is older than ``max_age_trading_days``.

    ``last_close`` and ``level_note``, when given, go into the reason, so a
    blocked night still says where the name stood and what went unchecked.

    TRADING days, not calendar days (C3) -- see MAX_CLOSE_AGE_TRADING_DAYS.

    A CACHED row is measured the same way and that is right: when the fetch
    failed and the report fell back to the cache, the age of the cache IS
    the age of the newest close the tool has, and a cache that has stopped
    moving should block.
    """
    if last_close_date is None:
        return Blocker(STALE_DATA, "no close date available")
    age = trading_days_between(last_close_date, as_of, holidays=holidays)
    if age > max_age_trading_days:
        close = f" at {last_close:,.2f}" if last_close is not None else ""
        reason = (f"newest close{close} {last_close_date.isoformat()} is {age} "
                  f"trading days old (limit {max_age_trading_days})")
        if level_note:
            reason += f". {level_note}"
        return Blocker(STALE_DATA, reason)
    return None


def catalyst_blocker(
    catalyst_date: date | None,
    catalyst_resolved: date | None,
    as_of: date,
    catalyst_event: str | None = None,
) -> Blocker | None:
    """BLOCK when a catalyst date has passed and it has not been resolved.

    Resolution is the structured ``catalyst_resolved`` date -- the day the
    outcome was actually ingested. This rule NEVER reads ``notes``: a prose
    prefix match let any free text satisfy the gate, including text saying
    the outcome was *not* ingested. Notes keep their prose "outcome:" lines
    as a human record, but they carry no machine meaning.

    A ticker with no catalyst_date is never blocked by this rule.
    A catalyst dated today has not yet passed.
    """
    if catalyst_date is None:
        return None
    if catalyst_date >= as_of:
        return None
    if catalyst_resolved is not None:
        return None
    event = f" ({catalyst_event})" if catalyst_event else ""
    return Blocker(
        CATALYST_UNRESOLVED,
        f"catalyst {catalyst_date.isoformat()}{event} has passed and "
        f"catalyst_resolved is not set",
    )


def missing_stop_blocker(status: str | None, stop_price: float | None) -> Blocker | None:
    """A HELD position with no stop is blocked, never actioned.

    Only HELD. A waiting name -- WATCH-PRICED, WATCH-GATED or PIPELINE --
    has no position to exit, so a missing stop is not an emergency; it is
    a prerequisite for entry, reported as the NO STOP DEFINED flag in
    ``pre_entry_stop_flag``.
    """
    if status != "HELD":
        return None
    if stop_price is None:
        return Blocker(NO_STOP, "no stop defined (FRAMEWORK 0.4 / 6.4)")
    return None


def collect_blockers(
    *,
    status: str | None,
    last_close: float | None,
    last_close_date: date | None,
    stop_price: float | None,
    catalyst_date: date | None,
    catalyst_resolved: date | None,
    catalyst_event: str | None,
    as_of: date,
    fetch_error: str | None = None,
    mbp: float | None = None,
    holidays: frozenset[date] | None = frozenset(),
    pending_correction: str | None = None,
    calendar_mismatch: str | None = None,
) -> tuple[Blocker, ...]:
    """Every blocker that applies. Blockers always fire, independently."""
    no_data = no_data_blocker(last_close, fetch_error)
    # With no price series at all there is nothing to be stale about; the
    # no-data blocker already says so. Every other blocker still fires.
    # A name carrying a level is held to ONE session (owner, 2026-09-19).
    # ``holidays`` is the exchange's closed weekdays over the window (owner,
    # 2026-09-19: no block when the exchange had no session); None means no
    # calendar could answer, and the naive count is used AND NAMED.
    level = carries_level(status, mbp, stop_price)
    notes = []
    if holidays is None:
        notes.append("no exchange calendar for this name: counted Monday to Friday")
    if level:
        notes.append(unchecked_levels(status, mbp, stop_price))
    stale = None if no_data else stale_close_blocker(
        last_close_date, as_of,
        MAX_CLOSE_AGE_TRADING_DAYS_LEVEL if level else MAX_CLOSE_AGE_TRADING_DAYS,
        holidays=holidays or frozenset(),
        last_close=last_close,
        level_note=". ".join(notes) or None)
    found = [
        no_data,
        stale,
        # E122(d): a correction that moves a close across a level does not
        # apply silently -- it blocks and asks.
        Blocker(PRICE_CORRECTION, pending_correction) if pending_correction else None,
        # E121(e): compliance BY DETECTION. A wrong mapping is loud within
        # one trading day of the name being live.
        Blocker(CALENDAR_MISMATCH, calendar_mismatch) if calendar_mismatch else None,
        catalyst_blocker(catalyst_date, catalyst_resolved, as_of, catalyst_event),
        missing_stop_blocker(status, stop_price),
    ]
    return tuple(b for b in found if b is not None)


# --- Verdicts (SCOPE 5) ----------------------------------------------------


def stop_verdict(
    status: str | None, last_close: float | None, stop_price: float | None,
    series_finding: str | None = None,
) -> Verdict | None:
    """STOP BREACHED for a HELD name at or below its stop.

    A risk check: it evaluates regardless of whether other manual fields
    are absent. Boundary is inclusive -- exactly at the stop is breached.

    ``series_finding`` is K4's verdict on the SERIES (`series_sanity.check`):
    a scale switch or an uncorroborated discontinuity inside the window.
    When it is set the close is not a measurement, so the check is DATA
    MISSING and never STOP BREACHED -- MNST's feed halved its price for
    four weeks in 2026, and a HELD name on such a feed would have printed
    a breach against a stop the market never touched. A REAL repricing
    that the tape corroborates carries no finding and still breaches.
    """
    if last_close is None:
        return None
    if status != "HELD":
        return None  # no position to exit; see pre_entry_stop_flag
    if stop_price is None:
        return Verdict(DATA_MISSING, "DATA MISSING", "stop check: stop_price not set")
    if series_finding:
        return Verdict(
            DATA_MISSING, "DATA MISSING",
            f"stop check: the price series cannot be measured (K4) -- "
            f"{series_finding}",
        )
    if last_close <= stop_price:
        return Verdict(
            STOP_BREACHED,
            "STOP BREACHED",
            f"close {last_close:.2f} <= stop {stop_price:.2f}",
        )
    return None


def pre_entry_stop_flag(status: str | None, stop_price: float | None) -> Verdict | None:
    """Flag a non-HELD name that has no stop defined.

    Not a blocker: there is no position to exit, so the MBP checks still
    run normally. But FRAMEWORK 0.4 rule 4 says a name is a buy below
    price X, under conditions Y, *with stop Z* -- so a buy verdict on a
    name with no stop is not yet actionable. The flag rides alongside the
    verdicts to say so.
    """
    if status == "HELD":
        return None
    if stop_price is not None:
        return None
    return Verdict(
        NO_STOP_PRE_ENTRY,
        "NO STOP DEFINED",
        "required before entry (FRAMEWORK 0.4 / 6.4)",
    )


#: E100 (2026-09-01): the mark on a crossing the DEFINITION caused.
#:
#: A name is at or below its MBP tonight and was NOT at last night's MBP --
#: and tonight's close is still strictly ABOVE the MBP the previous run
#: recorded. The price did not reach the old line; THE LINE CAME TO THE
#: PRICE. E100 marks it and arms nothing on it.
#:
#: THE SEQUENCE THAT PROMPTED THE RULING. On 2026-08-30 CTSH's MBP rose 43%
#: on two same-day rule changes while the price did not move, four days
#: after a measurement expressly recommended no change -- and that produced
#: this framework's only BUY signal. E28 makes `g` pre-registered before the
#: solve for exactly this reason; the cushion is the same lever and had none
#: of the discipline.
MBP_DEFINITION_MARK = ("[DEFINITION-CAUSED CROSSING, E100 -- the MBP moved, "
                       "not the price; no alert is armed]")

DEFINITION_CROSSING = "MBP_DEFINITION_CROSSING"


def crossing_is_definition_caused(last_close: float | None,
                                  mbp: float | None,
                                  previous_mbp: float | None) -> bool:
    """E100 clause 3, as a TEST rather than a judgement.

    True when the name is at or below its MBP tonight and would NOT have
    been at the MBP the previous run recorded. Both figures are already in
    `run_metrics`, so this needs no new input and nobody has to remember
    anything.

    False where there is no previous MBP to compare against: a first run
    cannot tell a definition change from a price move, and asserting one
    would be inventing the answer. False also where the MBP did not move --
    then the price did it, which is a real crossing.
    """
    if last_close is None or mbp is None or previous_mbp is None:
        return False
    if last_close > mbp:
        return False                 # not a crossing at all tonight
    return last_close > previous_mbp


def mbp_verdict(last_close: float | None, mbp: float | None,
                superseded: bool = False,
                series_finding: str | None = None,
                previous_mbp: float | None = None) -> Verdict | None:
    """AT/BELOW MBP or APPROACHING MBP -- mutually exclusive.

    AT/BELOW wins at and under the MBP; APPROACHING covers the band
    strictly above MBP up to mbp * 1.05 inclusive. Both boundaries are
    inclusive: exactly at MBP is AT/BELOW, exactly at mbp*1.05 is
    APPROACHING.

    E32: where the mbp was struck under the SUPERSEDED definition, every
    sentence that names the number says so. The mark is APPENDED, not
    substituted -- the arithmetic is unchanged and the old sentence is
    still the true description of it; what is added is that the
    definition behind it no longer governs.
    """
    if last_close is None:
        return None
    if mbp is None:
        return Verdict(
            DATA_MISSING, "DATA MISSING", "MBP checks: mbp requires fv_base and tier"
        )
    if series_finding:
        # K4: the close being compared may be the phantom bar itself.
        return Verdict(
            DATA_MISSING, "DATA MISSING",
            f"MBP checks: the price series cannot be measured (K4) -- "
            f"{series_finding}",
        )
    mark = f" {MBP_SUPERSEDED_MARK}" if superseded else ""
    if last_close <= mbp:
        # E100: is this the price reaching the line, or the line reaching
        # the price? The report already knew the MBP's derivation and had
        # never asked.
        if crossing_is_definition_caused(last_close, mbp, previous_mbp):
            return Verdict(
                DEFINITION_CROSSING, "AT/BELOW MBP — DEFINITION-CAUSED",
                f"close {last_close:.2f} <= mbp {mbp:.2f}{mark}, but the "
                f"previous run's mbp was {previous_mbp:.2f} and this close "
                f"is ABOVE it: the crossing is the DENOMINATOR moving. "
                f"{MBP_DEFINITION_MARK}"
            )
        return Verdict(
            AT_BELOW_MBP, "AT/BELOW MBP",
            f"close {last_close:.2f} <= mbp {mbp:.2f}{mark}"
        )
    if last_close <= mbp * APPROACHING_MBP_FACTOR:
        return Verdict(
            APPROACHING_MBP,
            "APPROACHING MBP",
            f"close {last_close:.2f} within 5% of mbp {mbp:.2f}{mark}",
        )
    return None


def in_dislocation_band(drawdown: float | None) -> bool | None:
    """FRAMEWORK Gate 1's level limb, as a PREDICATE.

    True inside [0.15, 0.50], False outside, and ``None`` -- DATA MISSING --
    when the drawdown could not be computed at all. The third value is not a
    convenience: a name whose 52-week high is unknown has not failed Gate 1,
    it has not been tested, and a caller that collapses ``None`` to False
    would silently convert an ungathered fact into a rejection.

    Both bounds are INCLUSIVE per FRAMEWORK-EDITS B2: exactly 0.15 and
    exactly 0.50 are inside the band.

    This exists separately from ``dislocation_verdict`` because a verdict is
    a reporting shape -- ``Verdict`` or ``None``, where ``None`` means "no
    finding" -- and reading it as a filter inverts that meaning. Callers
    that need to decide keep or drop call THIS. Callers that need to report
    call the verdict. Neither reimplements the band.
    """
    if drawdown is None:
        return None
    return DISLOCATION_MIN <= drawdown <= DISLOCATION_MAX


def fell_over_year(return_12m: float | None) -> bool | None:
    """FRAMEWORK-EDITS E127: has the price FALLEN over the trailing year?

    True when the close is BELOW the close of a year ago, False at or above
    it, ``None`` -- DATA MISSING -- when there is no close a year back. The
    band asks how far a name sits below its PEAK and cannot tell a fall
    from a pullback after a run-up: HUNT.OL and CF entered the 2026-09-26
    top 10 at 15.5% and 17.7% below highs set five and twenty-four days
    earlier, +1150% and +24.5% on the year.

    SCREENER ONLY. Filter 1 reads it after the band; `vss run` does not, and
    Gate 1 on the watchlist is unchanged by E127. Zero is not a fall.
    """
    if return_12m is None:
        return None
    return return_12m < 0


def dislocation_verdict(drawdown: float | None,
                        series_finding: str | None = None) -> Verdict | None:
    """OUTSIDE DISLOCATION BAND when drawdown leaves [0.15, 0.50].

    K4: with a ``series_finding`` the 52-week high on the far side of the
    break is not comparable with today's close, so the drawdown across it
    is not a measurement -- DATA MISSING, whatever number it came to.

    Both bounds inclusive: exactly 0.15 and exactly 0.50 are inside.
    """
    if series_finding:
        return Verdict(
            DATA_MISSING, "DATA MISSING",
            f"dislocation check: a drawdown measured across a break is not "
            f"a measurement (K4) -- {series_finding}",
        )
    inside = in_dislocation_band(drawdown)
    if inside is None:
        return Verdict(
            DATA_MISSING, "DATA MISSING", "dislocation check: drawdown not computable"
        )
    if inside:
        return None
    return Verdict(
        OUTSIDE_BAND,
        "OUTSIDE DISLOCATION BAND",
        f"drawdown {drawdown:.1%} outside "
        f"{DISLOCATION_MIN:.0%}-{DISLOCATION_MAX:.0%}",
    )


def frozen_gate_1(status: str | None, dd_at_entry: float | None,
                  peak_date: date | None) -> bool:
    """Is Gate 1 FROZEN for this name (FRAMEWORK-EDITS E12)?

    Only a PIPELINE name whose entry carries the pair. A holding reads
    today's level (B1); a WATCH-* name has its own re-entry rule (E27); a
    PIPELINE entry written before the pair existed has nothing frozen and
    is read on today's level, which the report says.
    """
    return status == "PIPELINE" and dd_at_entry is not None and peak_date is not None


def collect_verdicts(
    *,
    status: str | None,
    last_close: float | None,
    drawdown: float | None,
    mbp: float | None,
    stop_price: float | None,
    mbp_superseded: bool = False,
    previous_mbp: float | None = None,
    series_finding: str | None = None,
    dd_at_entry: float | None = None,
    peak_date: date | None = None,
) -> tuple[Verdict, ...]:
    """Every verdict that applies, in stable reporting order.

    Verdicts are COLLECTED, not first-match-wins: a HELD name below both
    its stop and its MBP reports both, so a stop breach can never be
    masked by another rule firing first.

    E12: for a PIPELINE name carrying `dd_at_entry` and `peak_date`, the
    dislocation verdict is struck on the FROZEN reading, never on today's
    drawdown -- leaving PIPELINE takes an information event, not a
    re-reading of the band. Today's figure stays on the row as context.
    The frozen reading is a stored number, not a measurement across
    today's series, so K4's finding does not reach it.
    """
    # A dropped name is out of the funnel. Running the entry checks over
    # it would report a missing stop "required before entry" for a name
    # nobody will enter, and a distance to an MBP that was never
    # computed. It keeps its row and its reason; it collects no verdicts.
    if status == "DROPPED":
        return (Verdict(DROPPED, "DROPPED",
                        "rejected and kept as a record -- no checks run"),)

    # E111: an INTAKE name has been READ and is not WATCHED. There is no
    # position to exit, no entry to prepare for and no MBP to be measured
    # against, so every check below would be answering a question nobody is
    # asking -- exactly the argument DROPPED rests on, for the opposite
    # reason. What it DOES carry is a store, and where the owner has
    # registered one, a growth view: enough for E108's floor and E106
    # clause 4 to run without the name acquiring a dated starting point.
    if status == "INTAKE":
        return (Verdict(INTAKE, "INTAKE",
                        "read, not watched -- no entry stamp, no MBP and no "
                        "stop, and no checks run. Promotion to PIPELINE is "
                        "what starts E12's clock, and it is the owner's act"),)

    if frozen_gate_1(status, dd_at_entry, peak_date):
        band = dislocation_verdict(dd_at_entry, None)
        if band is not None:
            today = "DATA MISSING" if drawdown is None else f"{drawdown:.1%}"
            band = Verdict(
                band.code, band.label,
                f"{band.detail} -- FROZEN AT ENTRY per E12, against the 52-week "
                f"closing high of {peak_date.isoformat()}; today's reading "
                f"{today} is context",
            )
    else:
        band = dislocation_verdict(drawdown, series_finding)

    found = [
        stop_verdict(status, last_close, stop_price, series_finding),
        pre_entry_stop_flag(status, stop_price),
        mbp_verdict(last_close, mbp, mbp_superseded, series_finding,
                    previous_mbp=previous_mbp),
        band,
    ]
    verdicts = [v for v in found if v is not None]
    if not verdicts:
        return (Verdict(NO_ACTION, "NO ACTION"),)
    return tuple(verdicts)


# --- Composition -----------------------------------------------------------


def assess(
    *,
    ticker: str,
    status: str | None,
    last_close: float | None,
    last_close_date: date | None,
    drawdown: float | None,
    fv_base: float | None,
    tier: int | None,
    stop_price: float | None,
    catalyst_date: date | None,
    catalyst_resolved: date | None,
    catalyst_event: str | None,
    as_of: date,
    fetch_error: str | None = None,
    bear_value: float | None = None,
    series_finding: str | None = None,
    dd_at_entry: float | None = None,
    peak_date: date | None = None,
    #: E100: the MBP the previous FULL run recorded for this name. Where a
    #: close sits at or below tonight's MBP and ABOVE that one, the crossing
    #: is the definition moving and not the price, and it arms nothing.
    previous_mbp: float | None = None,
    #: The exchange's closed weekdays between the newest close and ``as_of``
    #: (vss/calendars.py), or None when no calendar could answer.
    holidays: frozenset[date] | None = frozenset(),
    #: E122(d): a refused price correction waiting on the owner, in words.
    pending_correction: str | None = None,
    #: E121(e): a session the derived calendar denies, in words.
    calendar_mismatch: str | None = None,
) -> TickerAssessment:
    """Full assessment for one ticker.

    A blocked ticker carries its blocker reasons and NO verdicts, ever.

    K4: `series_finding` is `series_sanity.check`'s detail for the price
    series, or None. It is NOT a blocker -- the run still prices the name
    and still reports it -- but every check that compares the close with
    a level (stop, MBP, dislocation band) returns DATA MISSING with the
    finding in it, so a phantom halving can never print STOP BREACHED.

    E28, WIRED (2026-08-26, after E42). ``bear_value`` is the entry's linked
    run record struck at its pre-registered bear case, or None. With it the
    MBP is E28's -- bear-case value x tier cushion -- and carries no mark.
    Without it `compute_mbp` below IS the superseded definition and the
    figure is marked, WHATEVER the row's `mbp_basis` says: a row's claim is
    a record of what was struck, not an engine, and **absence of a bear
    case does NOT mean live.** Over-marking is the deliberate direction, as
    it is in E31 and E32.
    """
    # E90 (2026-08-30): MBP = the record-backed BASE-case value x the tier
    # cushion. ``bear_value`` no longer enters the buy line -- it stays on
    # the row as information. ``fv_base`` here is None unless a complete
    # record replays to it (item 9), so an E90 figure is record-backed by
    # construction and carries no mark; E28's bear arithmetic and the
    # marked `fv_base x old multiplier` fallback are retired together
    # (E32's mark remains on the stored-basis rows it always marked).
    del bear_value          # E90: information on the row, not an input here
    mbp = compute_mbp_e90(fv_base, tier)
    superseded = False
    blockers = collect_blockers(
        status=status,
        last_close=last_close,
        last_close_date=last_close_date,
        stop_price=stop_price,
        catalyst_date=catalyst_date,
        catalyst_resolved=catalyst_resolved,
        catalyst_event=catalyst_event,
        as_of=as_of,
        fetch_error=fetch_error,
        mbp=mbp,
        holidays=holidays,
        pending_correction=pending_correction,
        calendar_mismatch=calendar_mismatch,
    )
    if blockers:
        return TickerAssessment(ticker=ticker, blockers=blockers, verdicts=(),
                                mbp=mbp, mbp_superseded=superseded)
    verdicts = collect_verdicts(
        status=status,
        last_close=last_close,
        drawdown=drawdown,
        mbp=mbp,
        stop_price=stop_price,
        mbp_superseded=superseded,
        previous_mbp=previous_mbp,
        series_finding=series_finding,
        dd_at_entry=dd_at_entry,
        peak_date=peak_date,
    )
    return TickerAssessment(ticker=ticker, blockers=(), verdicts=verdicts,
                            mbp=mbp, mbp_superseded=superseded)


# =========================================================================
# FRAMEWORK 4.2 -- HARD KILLS (any one invalidates)
#
# Pure functions over an ordered sequence of Quarter records, OLDEST FIRST.
# Each returns a KillResult with one of three states. There is no fourth
# state and no silent skip: a rule that lacks its inputs says so and names
# the field it needs.
#
# These evaluate; they never decide materiality and never recommend an
# action. A trip means "verify against the source", nothing more.
# =========================================================================

TRIP = "TRIP"
NO_TRIP = "NO_TRIP"
CANNOT_EVALUATE = "CANNOT_EVALUATE"

#: Revenue must decline year-over-year this many quarters running (4.2.1).
#: YoY, not sequential: sequential would fire every Q1 on a seasonal name.
REVENUE_DECLINE_QUARTERS = 2

#: Sequential declines needed for the 4.3 SOFT flag. Catches the case YoY
#: misses -- a name eroding quarter on quarter while lapping a weak base.
SEQUENTIAL_DECLINE_QUARTERS = 3

#: Operating margin compression threshold, in BASIS POINTS.
#: Compared in bps with rounding rather than as a fraction: subtracting
#: two margins in binary float leaves ~1e-17 of noise, which made an
#: exactly-150bps compression read as 150.00000000000014 and trip a rule
#: documented as "> 150bps".
MARGIN_COMPRESSION_BPS = 150.0

#: Decimal places used to damp float noise before a threshold comparison.
COMPARISON_PRECISION = 6

#: THE UNIT CONTRACT. A ratio is stored as a FRACTION, never a percentage:
#: an operating margin of 6.6 per cent is 0.066. Every layer obeys it --
#: the extractor converts a quoted percentage, the watchlist loader
#: rejects anything outside these bands, and the rules below assume it
#: (4.2.2 multiplies by 10,000 for basis points). See SPEC.md section 2,
#: "Quarter figure units".
#:
#: The bands are arithmetic, not taste. Operating income above revenue is
#: not a thing, so a margin cannot exceed 1.0 -- but a pre-revenue name
#: can lose many times its revenue, so the floor is generous. Revenue
#: cannot fall by more than 100%; growth above 100% is possible but rare
#: enough that saying so in a fraction is worth the one-line error.
FRACTION_BANDS: dict[str, tuple[float, float]] = {
    "op_margin": (-10.0, 1.0),
    "revenue_yoy": (-1.0, 1.0),
    "revenue_yoy_organic": (-1.0, 1.0),
    "covenant_headroom": (-1.0, 1.0),
}

#: Money fields whose magnitude is stable quarter to quarter, and the
#: factor between two of them that can only be a UNIT MIX rather than a
#: business event. XBRL states whole units (11,279,000,000) where a press
#: release states millions (11,279); a history holding both is out by
#: 1,000,000 and every other check passes, because each row is internally
#: consistent.
#:
#: Only these three fields. op_income and class_c_impact are excluded on
#: purpose: they cross zero and can genuinely swing by orders of
#: magnitude, so a jump there is not evidence of anything.
SCALE_STABLE_FIELDS = ("revenue", "receivables", "inventory")
SCALE_JUMP_FACTOR = 1_000.0

#: E79 (2026-08-30): op_income / revenue must agree with op_margin AT THE
#: PRECISION THE ISSUER PRINTED, read from the entered margin's decimals --
#: 0.68 is a whole percent, 0.297 a tenth -- floored at the first value
#: (a margin typed 0.7 for a printed 70% is still a whole percent) and
#: capped at the second (a margin printed to a hundredth of a percent is
#: compared at a tenth: looser by at most 0.05pp, never tighter). Both
#: figures are rounded to that many decimals and must be equal. This
#: still catches a quarter assembled from two measures -- an adjusted
#: margin beside a reported operating income -- and no longer fires on
#: the issuer's own rounding (RMV.L: 67.71% printed as 68%).
MARGIN_PRECISION_DECIMALS = (2, 3)

#: E79's floor: the band is never TIGHTER than the 0.1pp the check applied
#: before the ruling. Half a unit of a margin printed to a tenth would be
#: 0.05pp, and the components that margin was struck from are printed
#: rounded too (SYNSAM.ST 2026-Q1: 10.33% against a printed 10.4%), so a
#: band that narrow fires on the issuer's rounding again -- the thing E79
#: exists to stop. Whole-percent margins get half a unit, 0.5pp.
MARGIN_TOLERANCE_FLOOR = 0.001

GUIDANCE_CUT_LIMIT = 2
GUIDANCE_CUT_WINDOW = 4

EPS_MISS_LIMIT = 3
EPS_MISS_WINDOW = 8

NET_DEBT_EBITDA_MAX = 3.5

#: NOT from FRAMEWORK 4.2, which says only "covenant proximity" without a
#: number. This is a chosen default; change it deliberately.
COVENANT_HEADROOM_MIN = 0.10

WORKING_CAPITAL_MULTIPLE = 1.5
WORKING_CAPITAL_QUARTERS = 2

EXEC_DEPARTURE_WINDOW_DAYS = 365

#: A YoY comparison needs the same quarter one year earlier.
QUARTERS_PER_YEAR = 4

#: How often a ticker reports. FRAMEWORK 4.2 states its windows in quarters
#: ("trailing 8 quarters", "2+ consecutive quarters") because US names
#: report quarterly. A half-yearly reporter (Unilever, most of Europe)
#: publishes half as many observations over the same span, so every window
#: is converted by TIME, not by count: a trailing 8 quarters is a trailing
#: 4 half-years, a YoY comparison looks back 2 periods instead of 4, and
#: "2+ consecutive quarters" is the same six months, which is ONE half-year.
#: That last conversion makes the run-length rules fire on a single
#: half-year observation; it is the literal span, stated here so it can be
#: overruled deliberately rather than discovered. See periods_for().
VALID_REPORTING_FREQUENCIES = ("quarterly", "half_yearly")
DEFAULT_REPORTING_FREQUENCY = "quarterly"
PERIODS_PER_YEAR: dict[str, int] = {"quarterly": 4, "half_yearly": 2}

#: Period labels and the months each covers. A quarterly ticker stores
#: YYYY-Qn; a half_yearly ticker stores YYYY-H1, YYYY-H2 or YYYY-FY. The
#: spans are what the OVERLAP GUARD compares: no two loaded periods of one
#: ticker may cover the same month. FY contains both halves and all four
#: quarters; H1 contains Q1 and Q2; H2 contains Q3 and Q4.
PERIOD_SPANS: dict[str, tuple[int, int]] = {
    "Q1": (1, 3), "Q2": (4, 6), "Q3": (7, 9), "Q4": (10, 12),
    "H1": (1, 6), "H2": (7, 12), "FY": (1, 12),
}
#: Which label kinds each reporting frequency stores.
PERIOD_KINDS_BY_FREQUENCY: dict[str, tuple[str, ...]] = {
    "quarterly": ("Q1", "Q2", "Q3", "Q4"),
    "half_yearly": ("H1", "H2", "FY"),
}


def periods_for(quarters: int, ppy: int) -> int:
    """A window stated in quarters, expressed in this frequency's periods.

    Converted by time and rounded UP, never below one: 8 quarters are 4
    half-years, 4 quarters are 2, 3 quarters are 2 (18 months does not fit
    in one half-year), 2 quarters are 1. Identity for a quarterly name.
    """
    return max(1, -(-quarters * ppy // QUARTERS_PER_YEAR))


def period_unit(ppy: int) -> str:
    """The word for one period at this frequency, for rule names and details."""
    return "quarters" if ppy == QUARTERS_PER_YEAR else "half-years"


def period_parts(label: str | None) -> tuple[int, str] | None:
    """(year, kind) for a well-formed label, else None. Pure string work."""
    if not label or not isinstance(label, str):
        return None
    text = label.strip()
    if len(text) != 7 or text[4] != "-" or not text[:4].isdigit():
        return None
    kind = text[5:]
    if kind not in PERIOD_SPANS:
        return None
    return int(text[:4]), kind


def period_span(label: str) -> tuple[int, int, int]:
    """(year, first_month, last_month) covered by a label. Raises on junk."""
    parts = period_parts(label)
    if parts is None:
        raise ValueError(f"malformed period label {label!r}")
    year, kind = parts
    start, end = PERIOD_SPANS[kind]
    return year, start, end


def period_months(label: str) -> int:
    """Resolution: 3 for a quarter, 6 for a half-year, 12 for a full year."""
    _, start, end = period_span(label)
    return end - start + 1


def period_sort_key(label: str) -> tuple[int, int, int]:
    """Chronological order: by year, then first month, then length."""
    return period_span(label)


def periods_overlap(a: str, b: str) -> bool:
    """True when the two labels cover at least one common month."""
    ya, sa, ea = period_span(a)
    yb, sb, eb = period_span(b)
    return ya == yb and sa <= eb and sb <= ea


def period_kind_allowed(label: str, frequency: str) -> bool:
    parts = period_parts(label)
    return parts is not None and parts[1] in PERIOD_KINDS_BY_FREQUENCY.get(frequency, ())


def overlap_problem(labels: Sequence[str]) -> str | None:
    """The first overlapping pair in a history, described, or None.

    The guard's rule: two periods of one ticker never share a month. Where
    they do, the FINEST resolution stays and the coarser goes -- the
    message says which to remove. Equal resolution overlapping is only
    possible for identical labels, which the duplicate check already
    catches, so the message always has a coarse side to name.
    """
    for i, a in enumerate(labels):
        for b in labels[i + 1:]:
            if not periods_overlap(a, b):
                continue
            fine, coarse = sorted((a, b), key=period_months)
            return (
                f"periods {a} and {b} overlap ({coarse} contains {fine}). The "
                f"overlap guard keeps the finest resolution and never holds both: "
                f"remove {coarse}, or remove {fine} if only the coarse figures exist."
            )
    return None


@dataclass(frozen=True)
class Admission:
    """The overlap guard's answer for ONE period offered against a history.

    ``admitted`` False means the period is not proposed and not evaluated.
    ``displaced`` lists loaded periods the new one supersedes for the
    EVALUATION only -- a re-read of a loaded period, or a finer period
    replacing a coarser one. The watchlist is never written; ``reason``
    tells the owner what to remove before pasting.
    """

    period: str
    admitted: bool
    reason: str
    displaced: tuple[str, ...] = ()


def admit_period(stored: Sequence[str], new: str | None, frequency: str) -> Admission:
    """Decide whether an extracted period may join a ticker's history.

    Rules, in order:
      1. A malformed or missing label is not admitted.
      2. A label of the wrong kind for the ticker's reporting frequency
         (a quarter on a half_yearly name, a half-year on a quarterly
         name) is not admitted.
      3. The same label already loaded: admitted, and it DISPLACES the
         stored entry for the evaluation -- a re-read is evaluated in
         place of the stored row, never beside it, or a single guidance
         cut would be counted twice.
      4. Overlapping a loaded FINER period: not admitted -- the guard keeps
         the finest resolution.
      5. Overlapping loaded COARSER period(s): admitted, displacing them;
         the reason names what must be removed before pasting.
      6. No overlap: admitted.
    """
    label = (new or "").strip()
    if period_parts(label) is None:
        return Admission(label or "PROVISIONAL", False,
                         f"period {label or 'not stated'} is not a label the schema "
                         f"knows (YYYY-Qn, YYYY-H1, YYYY-H2 or YYYY-FY)")
    if not period_kind_allowed(label, frequency):
        kinds = "/".join(PERIOD_KINDS_BY_FREQUENCY.get(frequency, ()))
        return Admission(label, False,
                         f"{label} is a {period_months(label)}-month period; this ticker "
                         f"reports {frequency}, which stores {kinds} periods only")
    if label in stored:
        return Admission(label, True,
                         f"{label} is already loaded: this re-read is evaluated in "
                         f"place of the stored entry, not beside it", (label,))
    finer = [s for s in stored if periods_overlap(s, label)
             and period_months(s) < period_months(label)]
    if finer:
        return Admission(label, False,
                         f"{label} overlaps loaded {', '.join(finer)}, which is finer; "
                         f"the overlap guard keeps the finest resolution and never "
                         f"holds both -- {label} is not proposed")
    coarser = [s for s in stored if periods_overlap(s, label)]
    if coarser:
        return Admission(label, True,
                         f"{label} is finer than loaded {', '.join(coarser)}; it is "
                         f"evaluated in their place, and they must be REMOVED from the "
                         f"watchlist before this entry is pasted -- the guard never "
                         f"holds both", tuple(coarser))
    return Admission(label, True, f"{label} overlaps nothing loaded")

VALID_GUIDANCE_ACTIONS = ("raised", "maintained", "cut", "none")
VALID_BASIS = ("reported", "constant_currency")
VALID_ACCOUNTING = ("gaap", "non_gaap")
#: A fiscal Q4 and a calendar Q4 are different three-month windows.
#: Microsoft's fiscal Q4 2026 ended 30 June 2026; calendar Q4 2026
#: is October-December. Mixing them inside one ticker breaks ordering.
VALID_PERIOD_BASIS = ("fiscal", "calendar")

#: Where a quarter's figures came from. Blank means the same as
#: "release": read from a published report, by a model, and cross-checked
#: by the margin reconciliation. "xbrl" means the figures came from the
#: filer's own tagged facts, where us-gaap:OperatingIncomeLoss already
#: says which line op_income is -- provenance the reconciliation was
#: standing in for.
#: "manual" means the owner read the figures out of the report themselves.
#: It is NOT given xbrl's exemption from the margin reconciliation: a tag
#: says which line an operating income is, and a pair of human eyes on a
#: PDF does not, so the check that exists to catch exactly that ambiguity
#: stays on. See config.unit_problem.
VALID_SOURCES = ("release", "xbrl", "manual")


@dataclass(frozen=True)
class Quarter:
    """One reported quarter. Every field is MANUAL -- entered by the owner.

    ``basis`` and ``accounting`` exist so a comparison can refuse to mix
    constant-currency with reported, or GAAP with non-GAAP, rather than
    quietly producing a number that means nothing.
    """

    period: str
    revenue: float | None = None
    revenue_yoy: float | None = None
    #: The issuer's own ORGANIC (or constant-currency) growth rate, as
    #: disclosed. E30 makes this the basis 4.2.1 reads: reported currency
    #: movement is not demand loss, and demand is what 4.2.1 measures.
    #: NOT like-for-like -- PNDORA disclosed organic +2% and LFL 0% in the
    #: same quarter, and E30 names organic. Where an issuer publishes only
    #: an LFL figure this stays empty and 4.2.1 falls back to reported,
    #: saying so.
    revenue_yoy_organic: float | None = None
    op_income: float | None = None
    op_margin: float | None = None
    eps: float | None = None
    eps_consensus: float | None = None       # MANUAL ONLY -- never extracted
    net_debt_ebitda: float | None = None
    guidance_action: str | None = None
    receivables: float | None = None
    inventory: float | None = None
    class_c_impact: float | None = None
    covenant_headroom: float | None = None
    basis: str | None = None
    accounting: str | None = None
    period_basis: str | None = None
    #: release | xbrl | None. See VALID_SOURCES.
    source: str | None = None


@dataclass(frozen=True)
class ExecChange:
    role: str          # CEO | CFO | other
    departed: date


@dataclass(frozen=True)
class KillResult:
    rule: str
    name: str
    state: str
    detail: str
    figures: tuple[str, ...] = ()

    @property
    def tripped(self) -> bool:
        return self.state == TRIP

    @property
    def uncertain(self) -> bool:
        return self.state == CANNOT_EVALUATE


def _result(rule, name, state, detail, figures=()):
    return KillResult(rule, name, state, detail, tuple(figures))


def _cannot(rule, name, why):
    return _result(rule, name, CANNOT_EVALUATE, why)


def basis_mismatch(a: Quarter, b: Quarter) -> str | None:
    """Describe why two quarters cannot be compared, or None if they can.

    Comparing a constant-currency figure against a reported one produces a
    number that is neither. Refuse rather than compute it.
    """
    if a.basis is None or b.basis is None:
        return f"basis not recorded for {a.period} or {b.period}"
    if a.basis != b.basis:
        return f"BASIS MISMATCH: {b.period} is {b.basis}, {a.period} is {a.basis}"
    if a.accounting is not None and b.accounting is not None:
        if a.accounting != b.accounting:
            return (
                f"BASIS MISMATCH: {b.period} is {b.accounting}, "
                f"{a.period} is {a.accounting}"
            )
    return None


def _year_ago(quarters, index, ppy: int = QUARTERS_PER_YEAR):
    """The same period one year earlier, or None if there is none.

    Matched by LABEL, not by position: 2026-Q2's year-ago is the entry
    labelled 2025-Q2, 2026-H1's is 2025-H1. Positional look-back (index
    minus ``ppy``) is right only when the history is contiguous and every
    period has the same length; a gap, or a half_yearly history that holds
    a YYYY-FY beside YYYY-H1 rows (which the overlap guard allows, since
    they do not overlap), would pair unlike periods and call it YoY. With
    label matching a missing comparator is None -> CANNOT EVALUATE, which
    is the honest answer. Positional look-back remains the fallback for
    labels the schema cannot parse (tests build ad-hoc ones).
    """
    parts = period_parts(getattr(quarters[index], "period", None))
    if parts is not None:
        year, kind = parts
        wanted = f"{year - 1}-{kind}"
        for i in range(index - 1, -1, -1):
            if quarters[i].period == wanted:
                return quarters[i]
        return None
    prior = index - ppy
    return quarters[prior] if prior >= 0 else None


# --- 4.2.1 Revenue declining 2+ consecutive quarters ----------------------


def revenue_decline_kill(quarters: Sequence[Quarter], ppy: int = QUARTERS_PER_YEAR) -> KillResult:
    """4.2.1, read on an ORGANIC basis where the issuer discloses one (E30).

    B9 ruled one direction: reported down, organic up, NOT a kill -- UNA.AS,
    where reported turnover fell four quarters on currency and disposals
    while underlying growth was positive throughout. E30 rules the mirror
    JD.L exposed: reported UP and organic DOWN IS a kill, and the reported
    figure does not rescue it. Reported +10.5%, organic -0.1% then -1.3%.

    One rule, both directions: 4.2.1 measures DEMAND, and organic is the
    measure of demand.

    THE BASIS IS NAMED IN THE RESULT, which is what B20 actually asked for.
    A window that mixes the two is CANNOT EVALUATE rather than a number: a
    run of declines counted partly on one measure and partly on another is
    not a run.
    """
    run, unit = periods_for(REVENUE_DECLINE_QUARTERS, ppy), period_unit(ppy)
    rule = "4.2.1"
    if len(quarters) < run:
        return _cannot(rule, f"Revenue declining {run}+ consecutive {unit} (YoY)",
                       f"needs {run} {unit} of history")

    recent = quarters[-run:]
    organic = [q.revenue_yoy_organic is not None for q in recent]
    if any(organic) and not all(organic):
        without = ", ".join(q.period for q in recent
                            if q.revenue_yoy_organic is None)
        return _cannot(
            rule, f"Revenue declining {run}+ consecutive {unit} (YoY, organic)",
            f"organic growth is disclosed for some of the window and not for "
            f"{without}; a run counted partly on organic and partly on "
            f"reported is not a run (E30)")

    on_organic = all(organic)
    basis_label = "organic" if on_organic else "reported"
    name = f"Revenue declining {run}+ consecutive {unit} (YoY, {basis_label})"

    # B9/E30, SAID RATHER THAN IMPLIED. A kill struck on REPORTED revenue is
    # a kill the carve-out did not reach, and until 2026-09-01 the only sign
    # of that was the word "reported" in the name. B9 exists because a
    # reported decline can be a disposal or a currency move rather than a
    # loss of demand -- UNA.AS fell 4.6/3.5/2.7/3.3% on four consecutive
    # reported quarters while underlying growth ran 3.0-5.8% throughout --
    # so a reader must be able to tell "no organic figure was disclosed"
    # from "the organic series was checked and declined too".
    #
    # THE XBRL ROUTE CAN NEVER SUPPLY ONE: us-gaap tags no organic measure,
    # `xbrl.as_quarter` records that absence as by-construction, and this
    # is where that absence becomes visible instead of inferred.
    carve_out = "" if on_organic else (
        f" No organic figure is on file for {'any of' if not any(organic) else 'all of'} "
        f"the window, so B9's carve-out could not be applied and this run is "
        f"counted on REPORTED revenue -- which a disposal, a demerger or a "
        f"currency move can produce without any loss of demand. Where the "
        f"release states an underlying figure, enter `revenue_yoy_organic`; "
        f"the XBRL route cannot supply one (no us-gaap tag exists).")

    def read(q: Quarter) -> float | None:
        return q.revenue_yoy_organic if on_organic else q.revenue_yoy

    field = "revenue_yoy_organic" if on_organic else "revenue_yoy"
    if any(read(q) is None for q in recent):
        missing = ", ".join(q.period for q in recent if read(q) is None)
        return _cannot(rule, name, f"{field} not set for {missing}{carve_out}")

    # A YoY figure that mixes bases is not a YoY figure. The reported
    # series carries the basis marker, so this check runs whichever
    # measure is read: a constant-currency quarter against a reported one
    # is a mismatch even where an organic rate exists for both.
    for i in range(len(quarters) - run, len(quarters)):
        prior = _year_ago(quarters, i, ppy)
        if prior is not None:
            problem = basis_mismatch(quarters[i], prior)
            if problem:
                return _cannot(rule, name, problem)

    figures = tuple(
        f"{q.period} revenue YoY {read(q):+.1%} ({basis_label})"
        + (f", reported {q.revenue_yoy:+.1%}"
           if on_organic and q.revenue_yoy is not None else "")
        for q in recent)

    if all(read(q) < 0 for q in recent):
        # THE KILL ITSELF CARRIES THE CARVE-OUT'S ABSENCE. This is the one
        # place it matters most: a hard kill struck on reported revenue,
        # with no organic series to test it against, is exactly the verdict
        # B9 was ruled to prevent -- and B9's own case (UNA.AS) TRIPS here
        # if the organic figures are not on file.
        detail = (f"{run} consecutive YoY declines on {basis_label} revenue"
                  + carve_out)
        if on_organic and all(q.revenue_yoy is not None and q.revenue_yoy > 0
                              for q in recent):
            # JD.L's shape, named where it occurs so the verdict cannot
            # read as an arithmetic slip.
            detail += (" -- reported revenue GREW throughout and does not "
                       "rescue it (E30)")
        return _result(rule, name, TRIP, detail, figures)
    return _result(rule, name, NO_TRIP,
                   f"no consecutive YoY decline run on {basis_label} revenue",
                   figures)


# --- 4.3 SOFT flag: sequential erosion YoY would miss ---------------------


def sequential_decline_soft_flag(quarters: Sequence[Quarter], ppy: int = QUARTERS_PER_YEAR) -> KillResult:
    """NOT a hard kill. FRAMEWORK 4.3 territory, worth -1.

    Catches the name that erodes quarter on quarter while lapping a weak
    base, so 4.2.1 never fires and the deterioration surfaces four
    quarters late.
    """
    run, unit = periods_for(SEQUENTIAL_DECLINE_QUARTERS, ppy), period_unit(ppy)
    rule = "4.3.soft"
    name = f"Revenue declining {run}+ consecutive {unit} (sequential)"
    need = run + 1
    if len(quarters) < need:
        return _cannot(rule, name, f"needs {need} {unit} of history")

    recent = quarters[-need:]
    if any(q.revenue is None for q in recent):
        missing = ", ".join(q.period for q in recent if q.revenue is None)
        return _cannot(rule, name, f"revenue not set for {missing}")
    for earlier, later in zip(recent, recent[1:]):
        problem = basis_mismatch(later, earlier)
        if problem:
            return _cannot(rule, name, problem)

    steps = [(b.period, b.revenue - a.revenue) for a, b in zip(recent, recent[1:])]
    figures = tuple(f"{p} sequential change {d:+,.1f}" for p, d in steps)
    if all(d < 0 for _, d in steps):
        return _result(rule, name, TRIP,
                       f"{run} consecutive sequential declines "
                       f"-- SOFT FLAG (-1), not a 4.2 hard kill", figures)
    return _result(rule, name, NO_TRIP, "no sequential decline run", figures)


# --- 4.2.2 Op margin compression > 150bps YoY with flat/declining revenue --


def _margin_excluding_one_off(quarter: Quarter) -> tuple[float | None, str | None]:
    """The margin with the quantified one-off taken out, or why it cannot be.

    ``class_c_impact`` is the one-off's effect on REPORTED operating
    profit, so removing it is a subtraction in margin terms:
    ``op_margin - class_c_impact / revenue``. Lindab's 2025-Q4 reports a
    3.1% margin with a -106 MSEK one-off on 3,134 MSEK of revenue, which
    is 6.5% ex one-off -- the adjusted margin the report itself states.

    A quarter with no recorded one-off has nothing to exclude and keeps
    its reported margin. A quarter with a one-off but no revenue cannot
    express it as a margin at all; that is CANNOT EVALUATE, not an
    exemption granted on the strength of an unquantifiable number.
    """
    if quarter.class_c_impact is None:
        return quarter.op_margin, None
    if not quarter.revenue:
        return None, (
            f"{quarter.period} records a class_c_impact of "
            f"{quarter.class_c_impact:,.1f} but no revenue, so the one-off "
            f"cannot be expressed as a margin and its effect on the "
            f"compression cannot be measured"
        )
    return quarter.op_margin - quarter.class_c_impact / quarter.revenue, None


def margin_compression_kill(quarters: Sequence[Quarter], ppy: int = QUARTERS_PER_YEAR) -> KillResult:
    """4.2.2, evaluated on the margin EXCLUDING quantified one-offs.

    FRAMEWORK 4.2 exempts compression "explained by a quantified Class C
    event", and explaining is a matter of size: a 2 MSEK one-off does not
    explain a 400bps collapse. The rule therefore recomputes both
    margins with their one-offs removed and applies the 150bps threshold
    to what is left. A one-off large enough to account for the
    compression exempts it; one that is not, does not.

    Both quarters are adjusted, not just the latest. A one-off that
    flattered the year-ago base manufactures compression that never
    happened, and a one-off that flatters the LATEST quarter hides
    compression that did -- so the ex-one-off figure is the one the
    threshold reads, in both directions.
    """
    rule = "4.2.2"
    name = "Op margin compression > 150bps YoY with flat/declining revenue"
    if len(quarters) < ppy + 1:
        return _cannot(rule, name, f"needs {ppy + 1} {period_unit(ppy)} for a YoY margin comparison")

    latest = quarters[-1]
    prior = _year_ago(quarters, len(quarters) - 1, ppy)
    if prior is None:
        return _cannot(rule, name, "no year-ago period")
    if latest.op_margin is None or prior.op_margin is None:
        return _cannot(rule, name, f"op_margin not set for {latest.period} or {prior.period}")
    if latest.revenue_yoy is None:
        return _cannot(rule, name, f"revenue_yoy not set for {latest.period}")
    problem = basis_mismatch(latest, prior)
    if problem:
        return _cannot(rule, name, problem)

    latest_ex, problem = _margin_excluding_one_off(latest)
    if problem:
        return _cannot(rule, name, problem)
    prior_ex, problem = _margin_excluding_one_off(prior)
    if problem:
        return _cannot(rule, name, problem)

    compression_bps = round(
        (prior.op_margin - latest.op_margin) * 10_000, COMPARISON_PRECISION
    )
    compression_ex_bps = round(
        (prior_ex - latest_ex) * 10_000, COMPARISON_PRECISION
    )
    one_offs = tuple(q for q in (latest, prior) if q.class_c_impact is not None)

    if one_offs:
        figures = (
            f"{latest.period} op margin {latest.op_margin:.2%} reported, "
            f"{latest_ex:.2%} ex one-off",
            f"{prior.period} op margin {prior.op_margin:.2%} reported, "
            f"{prior_ex:.2%} ex one-off",
            f"compression {compression_bps:+.0f}bps reported, "
            f"{compression_ex_bps:+.0f}bps ex one-off",
        ) + tuple(
            f"{q.period} class_c_impact {q.class_c_impact:,.1f} excluded"
            for q in one_offs
        ) + (f"{latest.period} revenue YoY {latest.revenue_yoy:+.1%}",)
    else:
        figures = (
            f"{latest.period} op margin {latest.op_margin:.2%}",
            f"{prior.period} op margin {prior.op_margin:.2%}",
            f"compression {compression_bps:+.0f}bps",
            f"{latest.period} revenue YoY {latest.revenue_yoy:+.1%}",
        )

    # The threshold reads the ex-one-off figure. Where they differ, the
    # reported number is still shown: a reader must be able to see what
    # the one-off did, not just be told it was handled.
    if compression_ex_bps <= MARGIN_COMPRESSION_BPS:
        if one_offs and compression_bps > MARGIN_COMPRESSION_BPS:
            detail = (
                f"compression of {compression_bps:+.0f}bps IS explained by the "
                f"quantified Class C event(s): {compression_ex_bps:+.0f}bps remains "
                f"once they are excluded, within {MARGIN_COMPRESSION_BPS:.0f}bps"
            )
        else:
            detail = f"compression within {MARGIN_COMPRESSION_BPS:.0f}bps"
        return _result(rule, name, NO_TRIP, detail, figures)
    if latest.revenue_yoy > 0:
        return _result(rule, name, NO_TRIP, "revenue growing, not flat/declining", figures)
    if one_offs:
        detail = (
            f"compression > {MARGIN_COMPRESSION_BPS:.0f}bps with flat/declining "
            f"revenue: {compression_ex_bps:+.0f}bps remains after excluding the "
            f"quantified Class C event(s), which therefore do NOT explain it"
        )
    else:
        detail = (
            f"compression > {MARGIN_COMPRESSION_BPS:.0f}bps with flat/declining "
            f"revenue and no quantified Class C event"
        )
    return _result(rule, name, TRIP, detail, figures)


# --- 4.2.3 2+ guidance cuts within trailing 4 quarters --------------------


def guidance_cuts_kill(quarters: Sequence[Quarter], ppy: int = QUARTERS_PER_YEAR) -> KillResult:
    span, unit = periods_for(GUIDANCE_CUT_WINDOW, ppy), period_unit(ppy)
    rule, name = "4.2.3", f"{GUIDANCE_CUT_LIMIT}+ guidance cuts within trailing {span} {unit}"
    if len(quarters) < span:
        return _cannot(rule, name, f"needs {span} {unit} of history")

    window = quarters[-span:]
    cuts = [q for q in window if q.guidance_action == "cut"]
    unknown = [q for q in window if q.guidance_action is None]
    figures = tuple(f"{q.period} guidance {q.guidance_action or 'not set'}" for q in window)

    if len(cuts) >= GUIDANCE_CUT_LIMIT:
        return _result(rule, name, TRIP,
                       f"{len(cuts)} guidance cuts in trailing {span} {unit}",
                       figures)
    if unknown:
        missing = ", ".join(q.period for q in unknown)
        return _cannot(rule, name, f"guidance_action not set for {missing}")
    return _result(rule, name, NO_TRIP, f"{len(cuts)} guidance cut(s)", figures)


# --- 4.2.4 3+ EPS misses within trailing 8 quarters -----------------------


def eps_misses_kill(quarters: Sequence[Quarter], ppy: int = QUARTERS_PER_YEAR) -> KillResult:
    """Needs consensus, which is MANUAL ONLY and never extracted.

    Consensus estimates are not in the primary source and are not free --
    the same class of number as fv_base. Absent consensus reports
    CANNOT EVALUATE rather than being skipped.
    """
    span, unit = periods_for(EPS_MISS_WINDOW, ppy), period_unit(ppy)
    rule, name = "4.2.4", f"{EPS_MISS_LIMIT}+ EPS misses within trailing {span} {unit}"
    if not quarters:
        return _cannot(rule, name, "no quarterly history")

    window = quarters[-span:]
    misses, unknown = [], []
    for q in window:
        if q.eps is None or q.eps_consensus is None:
            unknown.append(q)
        elif q.eps < q.eps_consensus:
            misses.append(q)
    figures = tuple(
        f"{q.period} EPS {q.eps if q.eps is not None else 'not set'} vs consensus "
        f"{q.eps_consensus if q.eps_consensus is not None else 'NOT SET (manual)'}"
        for q in window
    )

    # A confirmed trip stands even with gaps: more data cannot un-miss these.
    if len(misses) >= EPS_MISS_LIMIT:
        return _result(rule, name, TRIP, f"{len(misses)} EPS misses", figures)
    if unknown:
        missing = ", ".join(q.period for q in unknown)
        return _cannot(rule, name,
                       f"missing consensus -- eps_consensus is MANUAL ONLY and was not "
                       f"entered for {missing}")
    if len(window) < span:
        return _cannot(rule, name, f"needs {span} {unit}, have {len(window)}")
    return _result(rule, name, NO_TRIP, f"{len(misses)} EPS miss(es)", figures)


# --- 4.2.5 Net debt/EBITDA > 3.5x or covenant proximity -------------------


def leverage_kill(quarters: Sequence[Quarter],
                  derived: tuple[str, str] | None = None) -> KillResult:
    """``derived`` is E119's reading off the store, ``(state, line)`` with
    state PASS / REVIEW / FAIL / DATA MISSING (`manual.gate3_leverage` at
    3.5x). It is read ONLY where no stated quarterly figure exists: a
    stated `net_debt_ebitda` or `covenant_headroom` takes precedence."""
    rule, name = "4.2.5", "Net debt/EBITDA > 3.5x or covenant proximity"
    stated = bool(quarters) and (quarters[-1].net_debt_ebitda is not None
                                 or quarters[-1].covenant_headroom is not None)
    if not stated and derived is not None:
        state, line = derived
        if state == "FAIL":
            return _result(rule, name, TRIP, f"E119 DERIVED -- {line}", (line,))
        if state in ("PASS", "REVIEW"):
            return _result(rule, name, NO_TRIP, f"E119 DERIVED -- {line}", (line,))
        return _cannot(rule, name, f"E119: {line}")
    if not quarters:
        return _cannot(rule, name, "no quarterly history")

    latest = quarters[-1]
    if latest.net_debt_ebitda is None and latest.covenant_headroom is None:
        return _cannot(rule, name,
                       f"net_debt_ebitda and covenant_headroom both not set for {latest.period}")

    figures = []
    if latest.net_debt_ebitda is not None:
        # E117 clause 5 (owner, 2026-09-19): until a rent-bearing ratio forms
        # from the store, the kill reads the ISSUER'S STATED ratio -- lease-
        # inclusive for an IFRS 16 filer -- and says so, rather than going blind.
        figures.append(f"{latest.period} net debt/EBITDA {latest.net_debt_ebitda:.2f}x "
                       f"(issuer-stated; lease-inclusive under IFRS 16 -- E117 "
                       f"clause 5 pending)")
    if latest.covenant_headroom is not None:
        figures.append(f"{latest.period} covenant headroom {latest.covenant_headroom:.1%}")
    figures = tuple(figures)

    if latest.net_debt_ebitda is not None and latest.net_debt_ebitda > NET_DEBT_EBITDA_MAX:
        return _result(rule, name, TRIP,
                       f"net debt/EBITDA {latest.net_debt_ebitda:.2f}x exceeds "
                       f"{NET_DEBT_EBITDA_MAX}x", figures)
    if latest.covenant_headroom is not None and latest.covenant_headroom <= COVENANT_HEADROOM_MIN:
        return _result(rule, name, TRIP,
                       f"covenant headroom {latest.covenant_headroom:.1%} at or below the "
                       f"{COVENANT_HEADROOM_MIN:.0%} proximity threshold", figures)
    if latest.net_debt_ebitda is None:
        return _cannot(rule, name, f"net_debt_ebitda not set for {latest.period}")
    return _result(rule, name, NO_TRIP, "leverage within limit", figures)


# --- 4.2.6 CEO and CFO departure within trailing 12 months ----------------


def exec_departure_kill(
    exec_changes: Sequence[ExecChange] | None, as_of: date
) -> KillResult:
    """Both chairs vacated inside a year. Requires BOTH CEO and CFO.

    ``exec_changes`` absent means unknown -> CANNOT EVALUATE. An empty
    list means "checked, none" -> NO_TRIP. The distinction matters.
    """
    rule, name = "4.2.6", "CEO and CFO departure within trailing 12 months"
    if exec_changes is None:
        return _cannot(rule, name, "exec_changes not recorded (MANUAL)")

    cutoff_days = EXEC_DEPARTURE_WINDOW_DAYS
    recent = [c for c in exec_changes if 0 <= (as_of - c.departed).days <= cutoff_days]
    roles = {c.role.upper() for c in recent}
    figures = tuple(
        f"{c.role.upper()} departed {c.departed.isoformat()} "
        f"({(as_of - c.departed).days}d ago)" for c in recent
    )
    if "CEO" in roles and "CFO" in roles:
        return _result(rule, name, TRIP,
                       "both CEO and CFO departed within 12 months", figures)
    return _result(rule, name, NO_TRIP,
                   f"{sorted(roles) or 'no'} departure(s) in window", figures)


# --- 4.2.7 Receivables/inventory outgrowing revenue 1.5x for 2+ quarters ---


def working_capital_kill(quarters: Sequence[Quarter], ppy: int = QUARTERS_PER_YEAR) -> KillResult:
    """Channel stuffing / demand fade signal."""
    run, unit = periods_for(WORKING_CAPITAL_QUARTERS, ppy), period_unit(ppy)
    rule = "4.2.7"
    name = f"Receivables or inventory growing > 1.5x revenue growth for {run}+ {unit}"
    need = ppy + run
    if len(quarters) < need:
        return _cannot(rule, name, f"needs {need} {unit} for YoY working-capital growth")

    figures, flagged, missing = [], [], []
    for i in range(len(quarters) - run, len(quarters)):
        q, prior = quarters[i], _year_ago(quarters, i, ppy)
        if prior is None:
            missing.append(q.period)
            continue
        if q.revenue_yoy is None:
            missing.append(f"{q.period} revenue_yoy")
            continue
        problem = basis_mismatch(q, prior)
        if problem:
            return _cannot(rule, name, problem)

        hit = False
        for label, now_v, then_v in (
            ("receivables", q.receivables, prior.receivables),
            ("inventory", q.inventory, prior.inventory),
        ):
            if now_v is None or then_v is None:
                missing.append(f"{q.period} {label}")
                continue
            if then_v == 0:
                missing.append(f"{q.period} {label} (zero base)")
                continue
            growth = round((now_v - then_v) / then_v, COMPARISON_PRECISION)
            figures.append(f"{q.period} {label} YoY {growth:+.1%} vs revenue "
                           f"{q.revenue_yoy:+.1%}")
            # 1.5x a negative growth rate is meaningless: if revenue is
            # flat or shrinking, any working-capital growth is the signal.
            if q.revenue_yoy <= 0:
                hit = hit or growth > 0
            else:
                threshold = round(
                    WORKING_CAPITAL_MULTIPLE * q.revenue_yoy, COMPARISON_PRECISION
                )
                hit = hit or growth > threshold
        flagged.append(hit)

    if missing:
        return _cannot(rule, name, f"not set: {', '.join(missing)}")
    if flagged and all(flagged):
        return _result(rule, name, TRIP,
                       f"working capital outgrew revenue {run} "
                       f"{unit} running", tuple(figures))
    return _result(rule, name, NO_TRIP, "working capital in line", tuple(figures))


def evaluate_hard_kills(
    quarters: Sequence[Quarter] | None,
    exec_changes: Sequence[ExecChange] | None,
    as_of: date,
    reporting_frequency: str = DEFAULT_REPORTING_FREQUENCY,
    derived_leverage: tuple[str, str] | None = None,
) -> tuple[KillResult, ...]:
    """Every FRAMEWORK 4.2 rule, plus the 4.3 sequential soft flag last.

    ``derived_leverage`` is E119's store reading for 4.2.5, used only where
    the quarters state neither leverage input (see `leverage_kill`).

    Absent history is not silence: every rule still reports, saying which
    input it lacked.

    ``reporting_frequency`` sets the unit the windows are counted in:
    "quarterly" (the FRAMEWORK's own unit) or "half_yearly", where every
    quarter-denominated window is converted by time -- see
    PERIODS_PER_YEAR and periods_for(). 4.2.5 and 4.2.6 read a single
    period or a date window and are unaffected.
    """
    ppy = PERIODS_PER_YEAR.get(reporting_frequency)
    if ppy is None:
        raise ValueError(
            f"reporting_frequency must be one of {VALID_REPORTING_FREQUENCIES}, "
            f"got {reporting_frequency!r}"
        )
    qs = list(quarters or ())
    return (
        revenue_decline_kill(qs, ppy),
        margin_compression_kill(qs, ppy),
        guidance_cuts_kill(qs, ppy),
        eps_misses_kill(qs, ppy),
        leverage_kill(qs, derived_leverage),
        exec_departure_kill(exec_changes, as_of),
        working_capital_kill(qs, ppy),
        sequential_decline_soft_flag(qs, ppy),
    )
