"""Watchlist loading and validation.

A malformed entry fails the WHOLE run loudly (reference/SPEC.md 5). We never
skip a bad entry and carry on -- a silently dropped ticker is a worse failure
than a crash.

``mbp`` is COMPUTED (rules.compute_mbp) and must never appear in the
watchlist. If it does, that is a provenance conflict and the run fails.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from . import valuation
#: E24 / fx.UPPER_SAFE_MINOR: the ONE place that knows which currency codes
#: survive `.upper()`. Imported rather than restated -- a second mapping is
#: how the two drift apart, and the direction they drift in is a factor of
#: a hundred on every price leg of a London row.
from .fx import upper_safe_code
from .rules import (
    DEFAULT_REPORTING_FREQUENCY,
    FRACTION_BANDS,
    MARGIN_PRECISION_DECIMALS,
    MARGIN_TOLERANCE_FLOOR,
    PERIOD_KINDS_BY_FREQUENCY,
    SCALE_JUMP_FACTOR,
    SCALE_STABLE_FIELDS,
    VALID_ACCOUNTING,
    VALID_BASIS,
    VALID_PERIOD_BASIS,
    VALID_GUIDANCE_ACTIONS,
    VALID_REPORTING_FREQUENCIES,
    INTAKE_REFUSED_KEYS,
    RETIRED_STATUSES,
    VALID_SOURCES,
    VALID_STATUSES,
    VALID_TIERS,
    ExecChange,
    Quarter,
    overlap_problem,
    period_kind_allowed,
    period_months,
    period_sort_key,
    # E32's enum. Spelled once, in the lower layer: `rules` does not import
    # this module, so the definition lives there and is read here.
    MBP_DEF_E28,
    MBP_DEF_E90,
    VALID_MBP_DEFINITIONS,
)

#: Keys accepted on a watchlist entry. Every one is MANUAL.
ALLOWED_KEYS = {
    "ticker",
    "cik",
    "name",
    "currency",
    "status",
    "reporting_frequency",
    "fv_base",
    # The record replayed at its PRE-REGISTERED BULL case. Recorded on the
    # entry because the C4 / E42 exit test runs against it, and a HELD name
    # without one has no exit test at all (owner, 2026-09-20).
    "fv_bull",
    "tier",
    "dd_at_entry",
    "peak_date",
    "stop_price",
    "catalyst_date",
    "catalyst_resolved",
    "catalyst_event",
    "notes",
    "quarters",
    "exec_changes",
    "fx",
    "hurdle",
    "mbp_basis",
    "run_record",
    "sales",
    # E28's pre-registered growth view, MACHINE-READABLE (2026-09-04).
    # The words stay in `reference/growth-views/<TICKER>.md`; the numbers
    # live here, on the name being watched rather than in the store of
    # figures -- and here rather than in `tools/`, where until today every
    # strike hard-coded its own copy.
    "growth",
}

REQUIRED_KEYS = {"ticker", "name", "currency", "status"}

#: Keys that are computed by the tool and must never be supplied by hand.
COMPUTED_KEYS = {"mbp"}

#: Per-quarter keys. All MANUAL. eps_consensus is MANUAL ONLY -- consensus
#: is not in the primary source and must never be extracted or proposed.
ALLOWED_QUARTER_KEYS = {
    "period", "revenue", "revenue_yoy", "revenue_yoy_organic",
    "op_income", "op_margin", "eps",
    "eps_consensus", "net_debt_ebitda", "guidance_action", "receivables",
    "inventory", "class_c_impact", "covenant_headroom", "basis", "accounting",
    "period_basis", "source",
}
QUARTER_NUMERIC_KEYS = (
    "revenue", "revenue_yoy", "revenue_yoy_organic",
    "op_income", "op_margin", "eps", "eps_consensus",
    "net_debt_ebitda", "receivables", "inventory", "class_c_impact",
    "covenant_headroom",
)
#: YYYY-Qn for a quarter; YYYY-H1, YYYY-H2 or YYYY-FY for a half-yearly
#: reporter. Which kinds a ticker may hold is decided by its
#: reporting_frequency (rules.PERIOD_KINDS_BY_FREQUENCY), and no two of its
#: periods may overlap (rules.overlap_problem).
PERIOD_PATTERN = re.compile(r"^\d{4}-(Q[1-4]|H[12]|FY)$")
ALLOWED_EXEC_KEYS = {"role", "departed"}

#: E28's growth view, as the watchlist states it. `base`, `view` and
#: `registered` are REQUIRED and `bear`/`bull` come as a PAIR or not at all:
#: E90's cushion and E29's band are struck against the bear case, and a bull
#: with no bear is half of a range nobody can read.
GROWTH_KEYS = ("base", "bear", "bull", "view", "registered")
GROWTH_REQUIRED = ("base", "view", "registered")


class ConfigError(Exception):
    """Raised for any watchlist problem. Always fatal to the run."""


#: E24: the six things a converted price leg must carry to be reproducible.
#: `fx.Rate` already holds four of them -- value, pair, as_of, source -- and
#: nothing wrote them down outside a screener run manifest, so the verdict
#: gets somewhere to hold all six.
FX_KEYS = ("pair", "rate", "rate_as_of", "source", "converted", "price_date")

#: E29's frozen hurdle rate: all four or none, for E24's reason. A rate
#: without its anchor cannot be audited later, and a rate without its own
#: as-of date cannot be told from today's.
HURDLE_KEYS = ("rate", "core_expected_return", "premium", "rate_as_of")

#: E32: which definition an `mbp` was struck under, and when. Both or
#: neither, for E24's and E29's reason -- a definition with no date cannot
#: be told from a later one, and a date with no definition says nothing.
MBP_BASIS_KEYS = ("definition", "struck")

#: The two forms `struck` may take, and there are exactly two on purpose.
#: LIAB.ST's date is not recoverable -- the figure predates the oldest
#: backup on disk and the watchlist was untracked then -- and recording
#: the imprecision is better than inventing a day. A third form would let
#: the next person write prose where a date belongs.
MBP_STRUCK_EXACT = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MBP_STRUCK_BOUND = re.compile(r"^on or before \d{4}-\d{2}-\d{2}$")

#: Which side the rate was applied to. "price" = the quote was brought into
#: the reporting currency; "accounts" = a per-share value built from the
#: accounts was brought into the quote currency. The two round differently
#: and leave different audit trails, so the record says which.
FX_SIDES = ("price", "accounts")

FX_PAIR_PATTERN = re.compile(r"^[A-Z]{3}->[A-Z]{3}$")


@dataclass(frozen=True)
class FxRecord:
    """The rate a verdict was struck at, FROZEN WITH IT (E24).

    Not re-struck each run, for the reason E12 froze Gate 1: a stop that
    moves 5% because the exchange rate moved, with nothing changed in the
    business, is the currency selling for you rather than the analysis.

    THE COST, STATED: a frozen rate AGES, and nothing here says when it has
    aged enough to re-strike the verdict. That question is open and is
    recorded as open in FRAMEWORK-EDITS E24, rather than answered by a
    default nobody chose. `age_days` exists so a report can show the age
    without anything acting on it.
    """

    #: "EUR->SEK". The DIRECTION is part of the fact: the reciprocal is a
    #: different number, and the wrong one.
    pair: str
    rate: float
    #: The date of the close the rate came from -- NOT the day the
    #: calculation was done.
    rate_as_of: date
    source: str
    #: One of FX_SIDES.
    converted: str
    #: The quote date the converted figure is meant to be compared against.
    price_date: date

    @property
    def base(self) -> str:
        return self.pair.split("->")[0]

    @property
    def quote(self) -> str:
        return self.pair.split("->")[1]

    def age_days(self, as_of: date) -> int:
        return (as_of - self.rate_as_of).days


@dataclass(frozen=True)
class WatchlistEntry:
    ticker: str
    name: str
    currency: str
    status: str
    #: quarterly | half_yearly. Absent means quarterly, the FRAMEWORK's own
    #: unit. A half_yearly ticker stores YYYY-H1/H2/FY periods and has its
    #: 4.2 windows counted in half-years (rules.PERIODS_PER_YEAR).
    reporting_frequency: str = DEFAULT_REPORTING_FREQUENCY
    #: SEC Central Index Key, for `vss xbrl`. MANUAL, and manual because NO
    #: RESOLUTION STEP IS BUILT -- not because the mapping is unreachable.
    #: www.sec.gov/files/company_tickers.json answers HTTP 200 to a caller
    #: that declares a real contact (794,966 bytes, 10,388 rows, measured
    #: 2026-08-25). Nothing here guesses a CIK; nothing here looks one up
    #: either, and the second half of that is a gap rather than a rule.
    cik: int | None = None
    fv_base: float | None = None
    #: The struck bull case, in the QUOTE currency. Required of a HELD name:
    #: the exit test is the bull case (C4 / E42, and LIAB.ST's exit of
    #: 2026-09-19 is the worked example).
    fv_bull: float | None = None
    tier: int | None = None
    #: FRAMEWORK-EDITS E12: Gate 1 is evaluated ONCE, when a name enters
    #: PIPELINE, and is then frozen. This is the drawdown as measured at
    #: that moment, as a FRACTION, with the date of the 52-week closing
    #: high it was struck against. They are a PAIR -- a frozen drawdown
    #: whose reference peak is not named cannot be checked against
    #: anything, and E11 is the case: half of PNDORA.CO's move out of the
    #: band was the peak ageing out of the rolling window, which is
    #: invisible without the date.
    dd_at_entry: float | None = None
    peak_date: date | None = None
    stop_price: float | None = None
    catalyst_date: date | None = None
    catalyst_resolved: date | None = None
    catalyst_event: str | None = None
    notes: str | None = None
    quarters: tuple[Quarter, ...] = ()
    #: None means "not recorded" (cannot evaluate). An empty tuple means
    #: "checked, no departures". The distinction is load-bearing for 4.2.6.
    exec_changes: tuple[ExecChange, ...] | None = None
    #: E24: present only where the accounts and the quote are in different
    #: currencies and a price leg was converted. fv_base, mbp and
    #: stop_price are ALWAYS in the QUOTE currency -- `rules.compute_mbp`
    #: and `rules.mbp_verdict` compare them against last_close and nothing
    #: in the code converts -- so this records how they got there.
    fx: "FxRecord | None" = None
    #: E29's frozen hurdle rate, present only where a PURCHASE verdict was
    #: struck. Absent everywhere else -- an exit re-strikes at today's rate.
    hurdle: "HurdleRecord | None" = None
    #: E32: which definition this name's `mbp` was struck under, and when.
    #: ABSENT DOES NOT MEAN LIVE -- see MbpBasisRecord. Every `mbp` the
    #: chain computes today is struck under the superseded definition,
    #: because `rules.compute_mbp` is that definition.
    mbp_basis: "MbpBasisRecord | None" = None
    #: Build 2 item 9: the section 5 RUN RECORD `fv_base` was struck from,
    #: as a path (relative to the project root) to the JSON `vss.runrecord`
    #: writes. `vss run` prints a fair value ONLY when this record exists,
    #: is complete, and replays to `fv_base`; otherwise the row reads DATA
    #: MISSING for it, with the reason. An `fv_base` with no record is a
    #: number nobody can regenerate, and Phase 3's rule is that such a
    #: number is not printed.
    run_record: str | None = None
    #: B45: the fills that closed (or trimmed) the position, oldest first.
    #: Empty means no sale is recorded, which is the normal state.
    sales: tuple["SaleRecord", ...] = ()
    #: E28's pre-registered growth view (2026-09-04), machine-readable at
    #: last. None means the entry does not carry one, which under E28 means
    #: NO FAIR VALUE MAY BE STRUCK -- never that growth is zero.
    growth: "GrowthView | None" = None


def _where(index: int, ticker: Any = None) -> str:
    label = f" (ticker: {ticker})" if ticker else ""
    return f"watchlist entry #{index + 1}{label}"


def _as_float(value: Any, key: str, index: int, ticker: Any) -> float | None:
    """A number, or None for DATA MISSING. A BOOLEAN is neither.

    YAML 1.1 resolves an unquoted ``no``, ``yes``, ``on`` or ``off`` to a
    bool before any code here sees the file, and ``float(False)`` is 0.0 --
    so a word written where a number belongs becomes a figure nobody
    entered, on a field where zero is a claim. ``manual._as_float`` has
    always refused this and this loader had not; one rule, both loaders.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise ConfigError(
            f"{_where(index, ticker)}: {key} must be a number, got {value!r}. "
            f"YAML reads an unquoted yes/no/on/off as a BOOLEAN and "
            f"float({value!r}) is {float(value):g} -- a figure nobody typed. "
            f"Leave the field blank to say DATA MISSING."
        )
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ConfigError(f"{_where(index, ticker)}: {key} must be a number, got {value!r}")


def _as_cik(value: Any, index: int, ticker: Any) -> int | None:
    """A CIK is a positive integer. Leading zeros are formatting, not data."""
    if value is None:
        return None
    try:
        cik = int(str(value).strip())
    except (TypeError, ValueError):
        raise ConfigError(
            f"{_where(index, ticker)}: cik must be a number, got {value!r}"
        )
    if not 0 < cik <= 9_999_999_999:
        raise ConfigError(
            f"{_where(index, ticker)}: cik {cik} is out of range (1..9999999999)"
        )
    return cik


def _as_date(value: Any, key: str, index: int, ticker: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            pass
    raise ConfigError(
        f"{_where(index, ticker)}: {key} must be a YYYY-MM-DD date, got {value!r}"
    )


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text.strip() else None


def _check_entry_drawdown(dd_at_entry, peak_date, index: int, ticker) -> None:
    """E12's frozen Gate 1 reading: a FRACTION, and never alone.

    Two checks, and both are the ruling rather than a threshold invented
    here. E12 says to store the drawdown at entry *and the date of the
    reference peak alongside it*, so one without the other is a
    half-recorded fact: a frozen drawdown whose peak is not named cannot
    be told from one whose peak aged out, which is the whole of E11. And
    the drawdown obeys the same unit contract every other ratio in this
    file obeys -- 15.64 per cent is 0.1564, and a hand-entered 15.64
    would read as a 1,564% fall.
    """
    if (dd_at_entry is None) != (peak_date is None):
        present, absent = (("dd_at_entry", "peak_date") if peak_date is None
                           else ("peak_date", "dd_at_entry"))
        raise ConfigError(
            f"{_where(index, ticker)}: {present} is set but {absent} is not. "
            f"FRAMEWORK-EDITS E12 stores them as a pair -- a frozen Gate 1 "
            f"reading whose reference peak is not named cannot be told from "
            f"one whose peak has since aged out of the rolling window, which "
            f"is exactly what E11 found."
        )
    if dd_at_entry is None:
        return
    if not 0.0 <= dd_at_entry <= 1.0:
        raise ConfigError(
            f"{_where(index, ticker)}: dd_at_entry is {dd_at_entry:g}, outside "
            f"[0, 1]. A drawdown is a FRACTION, not a percentage -- "
            f"{dd_at_entry:g} per cent is written {dd_at_entry / 100:g}. It "
            f"cannot be negative (the trailing high includes today's close) "
            f"and cannot exceed 1 (the price cannot fall below zero). See "
            f"SPEC.md section 2."
        )


def _check_price_leg(value: float | None, key: str, index: int, ticker) -> None:
    """A price leg is a PRICE: strictly positive, or blank.

    `fv_base` and `stop_price` are the only two entry fields that name a
    LEVEL a quote is compared against -- E24: both are in the QUOTE
    currency and nothing in the code converts -- so a zero or a negative on
    either is not a low figure, it is a figure that cannot be what the
    field says it is. Each refuses zero for a reason of its own:

      stop_price 0  is a stop no close can ever reach. `rules.stop_verdict`
                    tests `last_close <= stop_price`, so STOP BREACHED
                    becomes unreachable for that name for good -- and
                    `rules.missing_stop_blocker` tests `is None`, so the
                    blocker written to catch exactly a HELD name with no
                    exit reports nothing and the row is actioned.
      fv_base 0     makes `rules.compute_mbp` return 0.0 rather than None,
                    and 0.0 is not DATA MISSING: `rules.mbp_verdict` then
                    returns NO VERDICT AT ALL instead of the DATA MISSING
                    it is written to report. MSFT's own entry comment
                    depends on that DATA MISSING path.

    A negative is refused on the same ground and needs no separate one.

    BLANK IS STILL HOW YOU SAY NOTHING. This does not make either field
    required; it says that where one carries a value, the value is a price.

    ZERO IS KEPT EVERYWHERE ELSE ON THIS LOADER, and deliberately -- it is
    a real reading of every other numeric field: a flat `revenue_yoy` or
    `revenue_yoy_organic`, a breakeven `op_income` or `op_margin`, a
    `covenant_headroom` of nil which SHOULD trip 4.2.5, a
    `net_debt_ebitda` of nil on a debt-free balance sheet, a
    `class_c_impact` of nil, an `eps` or `eps_consensus` of nil, a
    `dd_at_entry` of nil for a name sitting at its own 52-week high.
    Refusing zero there would convert a reading into an error.
    """
    if value is None:
        return
    if value <= 0:
        raise ConfigError(
            f"{_where(index, ticker)}: {key} is {value:g}, and a price leg "
            f"must be strictly positive. `fv_base` and `stop_price` are "
            f"LEVELS compared against last_close with no conversion "
            f"anywhere (E24), so a zero is not a low price -- a stop of 0 "
            f"can never breach and an fv_base of 0 makes the computed mbp "
            f"0.00 instead of DATA MISSING. Leave the field BLANK to say "
            f"DATA MISSING, which is a legitimate state; do not enter a "
            f"placeholder."
        )


def unit_problem(fields) -> str | None:
    """The unit contract, as a question rather than an exception.

    Pure and importable, so the one place that decides whether a quarter
    obeys SPEC.md section 2 is also the place `vss earnings` asks before
    proposing a row. A tool that proposes an entry its own loader would
    reject has two definitions of valid.

    ``fields`` is a mapping or any object with the quarter's attributes.
    """
    get = fields.get if hasattr(fields, "get") else lambda k: getattr(fields, k, None)

    for key, (low, high) in FRACTION_BANDS.items():
        value = get(key)
        if value is None or low <= value <= high:
            continue
        if key == "op_margin" and get("op_margin_cause"):
            # E83: a STATED margin outside the band, which the accounts
            # explain (a gain inside operating profit), is accepted with
            # the cause on the field. An unexplained one is refused below.
            continue
        return (
            f"{key} is {value:g}, outside the plausible band [{low:g}, {high:g}]. "
            f"Ratio fields are FRACTIONS, not percentages -- {value:g} per cent "
            f"is written {value / 100:g}. Fix the source of the figure; do not "
            f"scale it by hand. See SPEC.md section 2, 'Quarter figure units'."
        )

    revenue, op_income, op_margin = get("revenue"), get("op_income"), get("op_margin")
    if not revenue or op_income is None:
        return None

    # E79 (2026-08-30): where the issuer states NO margin, the check has
    # nothing to compare and does not fire. The older UNRECONCILED refusal
    # -- an op_income with a blank op_margin refused on every path but
    # `source: xbrl`, the NIKE income-before-taxes safeguard -- is
    # withdrawn by that ruling; what guards the line an operating income
    # came from is now its page reference, which on the manual path must
    # quote the caption.
    if op_margin is None:
        return None

    decimals = margin_precision(op_margin, get("op_margin_precision"))
    band = margin_band(op_margin, get("op_margin_precision"))
    implied = op_income / revenue
    gap = abs(implied - op_margin)
    if gap > band + 1e-12:
        unit = "a whole percent" if decimals == 2 else "a tenth of a percent"
        return (
            f"op_income / revenue is {implied:.4f} but op_margin is {op_margin:.4f} "
            f"-- a gap of {gap * 100:.2f}pp, over the ±{band * 100:.2g}pp band for "
            f"a margin stated to {unit} (E79): rounded the same way they are "
            f"{round(implied, decimals):.{decimals}f} and "
            f"{round(op_margin, decimals):.{decimals}f} and do not agree. The three "
            f"figures do not describe one measure of one period: an adjusted "
            f"margin beside a reported operating income reads exactly like this."
        )
    return None


def margin_band(op_margin: float, stated: float | None = None) -> float:
    """E79: half a unit of the stated precision, never below the floor.

    0.68 (a whole percent) may sit 0.5pp either side of the computed
    margin and still be its rounding; 0.297 (a tenth) gets the floor,
    `rules.MARGIN_TOLERANCE_FLOOR` -- one unit, 0.1pp, because the
    components it was struck from are printed rounded too.
    """
    return max(0.5 * 10 ** -margin_precision(op_margin, stated), MARGIN_TOLERANCE_FLOOR)


def margin_precision(op_margin: float, stated: float | None = None) -> int:
    """E79: the decimals a stated margin is compared at, read from the entry.

    `0.68` is a whole percent (two decimals of a fraction), `0.297` a
    tenth of a percent (three). Floored and capped by
    `rules.MARGIN_PRECISION_DECIMALS`: a margin typed `0.7` for a printed
    70% is still a whole percent, and one printed to a hundredth of a
    percent is compared at a tenth -- looser by at most 0.05pp, never
    tighter. The decimals are read from the shortest decimal form that
    reproduces the float, which is what a reader typed.
    """
    low, high = MARGIN_PRECISION_DECIMALS
    if stated is not None:
        # E79.1: the printed precision in percentage points -- 1 is a
        # whole percent (two decimals of a fraction), 0.1 a tenth (three)
        # -- so a printed 19.0% typed `0.19` keeps its tenth.
        import math
        return max(low, min(high, 2 + round(-math.log10(stated))))
    text = repr(float(op_margin))
    if "e" in text or "E" in text:
        return high
    decimals = len(text.split(".")[1]) if "." in text else 0
    return max(low, min(high, decimals))


def _check_units(fields: dict, where: str) -> None:
    """Enforce the unit contract at load time. See SPEC.md section 2.

    A ratio outside its band is a UNIT ERROR, not a value to evaluate:
    an op_margin of 6.6 is six hundred and sixty per cent, and no verdict
    computed from it would be about anything the owner entered. The run
    fails rather than reporting on a number nobody meant.
    """
    problem = unit_problem(fields)
    if problem:
        raise ConfigError(f"{where}: {problem}")


def _check_one_scale(quarters: list, index: int, ticker: Any) -> None:
    """One ticker's history must be in ONE unit.

    `vss xbrl` reports whole units, a press release reports millions, and
    a row from each is internally consistent -- so the band check, the
    reconciliation check and every rule pass while the history is out by
    a factor of a million. Only a comparison ACROSS rows can see it, so
    only this check can.

    Sequential revenue would read as a 100,000% collapse and a YoY
    comparison would be arithmetic about nothing.
    """
    for key in SCALE_STABLE_FIELDS:
        seen = [(q.period, abs(getattr(q, key)))
                for q in quarters if getattr(q, key)]
        if len(seen) < 2:
            continue
        low_period, low = min(seen, key=lambda pair: pair[1])
        high_period, high = max(seen, key=lambda pair: pair[1])
        if high / low < SCALE_JUMP_FACTOR:
            continue
        raise ConfigError(
            f"{_where(index, ticker)}: {key} jumps by {high / low:,.0f}x between "
            f"{low_period} ({low:,.0f}) and {high_period} ({high:,.0f}). That is "
            f"a UNIT MIX, not a business event: XBRL states whole units where a "
            f"press release states millions. Put the whole history in one unit "
            f"by re-reading the odd quarters from one source -- do not rescale "
            f"a figure by hand."
        )


def _parse_quarters(
    raw: Any, index: int, ticker: Any,
    frequency: str = DEFAULT_REPORTING_FREQUENCY,
) -> tuple[Quarter, ...]:
    """Validate the quarters: block. Oldest first, unique, well-formed.

    Two checks belong to the ticker's reporting frequency. The label KIND
    must match it -- a quarterly ticker stores YYYY-Qn, a half_yearly one
    stores YYYY-H1/H2/FY -- so the rules' windows are counted in one unit.
    And the OVERLAP GUARD: no two periods of one ticker may cover the same
    month (FY contains H1 and H2, H1 contains Q1 and Q2, ...). A history
    holding both 2025-H1 and 2025-FY would count the same six months twice
    in every trailing window. The guard keeps the finest resolution; the
    error says which label to remove.
    """
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ConfigError(f"{_where(index, ticker)}: quarters must be a list")

    parsed, seen = [], []
    for n, item in enumerate(raw):
        where = f"{_where(index, ticker)} quarter #{n + 1}"
        if not isinstance(item, dict):
            raise ConfigError(f"{where}: expected a mapping")
        unknown = set(item) - ALLOWED_QUARTER_KEYS
        if unknown:
            raise ConfigError(
                f"{where}: unknown key(s) {', '.join(sorted(unknown))}. "
                f"Allowed: {', '.join(sorted(ALLOWED_QUARTER_KEYS))}"
            )
        period = item.get("period")
        if not period or not PERIOD_PATTERN.match(str(period).strip()):
            raise ConfigError(
                f"{where}: period must look like 2026-Q2 (quarterly) or "
                f"2026-H1 / 2026-H2 / 2026-FY (half_yearly), got {period!r}"
            )
        period = str(period).strip()
        if not period_kind_allowed(period, frequency):
            kinds = "/".join(PERIOD_KINDS_BY_FREQUENCY[frequency])
            raise ConfigError(
                f"{where}: period {period} is a {period_months(period)}-month "
                f"period but the ticker reports {frequency}, which stores "
                f"{kinds} periods only. Set reporting_frequency on the ticker "
                f"or relabel the period -- the 4.2 windows are counted in one unit."
            )
        if period in seen:
            raise ConfigError(f"{where}: duplicate period {period}")
        if seen and period_sort_key(period) < period_sort_key(seen[-1]):
            raise ConfigError(
                f"{where}: quarters must be listed oldest first -- {period} "
                f"follows {seen[-1]}"
            )
        seen.append(period)

        fields = {"period": period}
        for key in QUARTER_NUMERIC_KEYS:
            fields[key] = _as_float(item.get(key), key, index, ticker)
        for key, allowed in (("guidance_action", VALID_GUIDANCE_ACTIONS),
                             ("basis", VALID_BASIS),
                             ("accounting", VALID_ACCOUNTING),
                             ("period_basis", VALID_PERIOD_BASIS),
                             ("source", VALID_SOURCES)):
            value = _as_text(item.get(key))
            if value is not None:
                value = value.strip().lower()
                if value not in allowed:
                    raise ConfigError(
                        f"{where}: {key} must be one of {'|'.join(allowed)}, "
                        f"got {item.get(key)!r}"
                    )
            fields[key] = value

        _check_units(fields, where)
        parsed.append(Quarter(**fields))

    _check_one_scale(parsed, index, ticker)

    # The OVERLAP GUARD. Never two labels covering the same month.
    problem = overlap_problem(seen)
    if problem:
        raise ConfigError(f"{_where(index, ticker)}: {problem}")

    # A fiscal Q4 and a calendar Q4 are different three-month windows, so
    # a history mixing the two cannot be ordered or compared year over year.
    bases = {q.period_basis for q in parsed if q.period_basis is not None}
    if len(bases) > 1:
        raise ConfigError(
            f"{_where(index, ticker)}: quarters mix period_basis "
            f"{sorted(bases)}. A fiscal Q4 and a calendar Q4 are different "
            f"periods -- pick one basis per ticker or ordering breaks."
        )
    return tuple(parsed)


@dataclass(frozen=True)
class HurdleRecord:
    """The hurdle rate a PURCHASE verdict was struck at, FROZEN WITH IT (E29).

    r is the OWNER'S HURDLE RATE, not an estimate of what the market demands
    (E29). It is flat across every name -- it says what the owner requires to
    move capital out of the index core, which is a fact about him and not
    about a company or a currency.

    FROZEN FOR ENTRY, RE-STRUCK FOR EXIT, and the asymmetry is the ruling.
    This record is the ENTRY half: the rate that struck a purchase, kept so
    the verdict stays re-derivable. The EXIT half is deliberately absent --
    C4 is re-struck at today's rate, because C4's own reasoning is that a
    level set months earlier states where the thesis was rather than what the
    capital can earn next.

    So, unlike `FxRecord`, this one does NOT age: it is a record of a
    commitment, not a live input. Nothing should compute its staleness.

    The anchor is stored beside the rate because it is the only thing that
    makes r changeable on a rule rather than on a whim: r = the index core's
    long-run expected return + 2-3 points, and if the core's expected return
    moves materially, r moves with it.
    """

    #: The frozen rate, e.g. 0.095.
    rate: float
    #: What the index core was expected to return, long run, when it was set.
    core_expected_return: float
    #: The single-company premium over the core. E29 sets it at 2-3 points.
    premium: float
    #: When it was struck. NOT for ageing -- for telling one verdict's rate
    #: from another's.
    rate_as_of: date | None


def _parse_hurdle(raw: Any, index: int, ticker: Any) -> "HurdleRecord | None":
    """E29's four facts, all four or none.

    Partial is refused for E24's reason: a rate with no anchor cannot be
    audited, and an anchor that does not reconcile to the rate is two claims
    where there should be one.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ConfigError(f"{_where(index, ticker)}: hurdle must be a mapping "
                          f"with {', '.join(HURDLE_KEYS)}")
    unknown = sorted(set(raw) - set(HURDLE_KEYS))
    if unknown:
        raise ConfigError(f"{_where(index, ticker)}: hurdle has unknown key(s) "
                          f"{', '.join(unknown)}")
    missing = [k for k in HURDLE_KEYS if raw.get(k) in (None, "")]
    if missing:
        raise ConfigError(
            f"{_where(index, ticker)}: hurdle is missing {', '.join(missing)}. "
            f"E29 records four things or none: a rate without its anchor "
            f"cannot be audited later, and without its own as-of date it "
            f"cannot be told from today's rate.")
    rate = _as_float(raw.get("rate"), "hurdle.rate", index, ticker)
    core = _as_float(raw.get("core_expected_return"),
                     "hurdle.core_expected_return", index, ticker)
    premium = _as_float(raw.get("premium"), "hurdle.premium", index, ticker)
    if rate is None or rate <= 0:
        raise ConfigError(f"{_where(index, ticker)}: hurdle rate must be "
                          f"positive, got {raw['rate']!r}")
    try:
        anchored = valuation.anchored_rate(core, premium)
    except valuation.ValuationError as exc:
        raise ConfigError(f"{_where(index, ticker)}: {exc}") from exc
    if abs(anchored - rate) > 1e-9:
        raise ConfigError(
            f"{_where(index, ticker)}: hurdle rate {rate} does not equal "
            f"core_expected_return {core} + premium {premium} = {anchored}. "
            f"E29 anchors r to the core; a rate that does not reconcile to "
            f"its own anchor is not anchored.")
    return HurdleRecord(
        rate=rate, core_expected_return=core, premium=premium,
        rate_as_of=_as_date(raw.get("rate_as_of"), "hurdle.rate_as_of",
                            index, ticker),
    )


@dataclass(frozen=True)
class MbpBasisRecord:
    """Which definition an `mbp` was struck under, and when (E32).

    E32 rules that there were never two competing definitions: E28 states
    one and the code implements the other, and only the code computes
    anything. **E28's governs from here** -- MBP is the price at which
    implied growth equals the PRE-REGISTERED bear case, with the tier
    cushion on that -- and `fv_base x tier multiplier` is SUPERSEDED AS A
    DEFINITION.

    The figures already struck under it are kept, not recomputed and not
    deleted, because they cannot be restruck: E28 needs the bear case
    pre-registered BEFORE implied growth is solved, and for all three held
    names the bear rate was decided after. **That is a missing proof of
    ORDERING, not a missing figure**, and no amount of reading reports
    supplies it. So each keeps its number and carries this record beside
    it.

    ABSENCE DOES NOT MEAN LIVE. `rules.compute_mbp` IS the superseded
    definition and `valuation.maximum_buy_price` is wired to nothing, so
    every `mbp` the chain can produce today is struck under the superseded
    one whether or not a row says so. This record makes the fact explicit
    and dates it; it does not create it. Over-marking is the deliberate
    direction, the same way E31 over-names.
    """

    #: One of VALID_MBP_DEFINITIONS.
    definition: str
    #: `YYYY-MM-DD`, or `on or before YYYY-MM-DD` where the day is not
    #: recoverable. Kept as the STRING it was written as: the second form
    #: is a claim about what is known, and parsing it to a date would
    #: throw that away.
    struck: str

    @property
    def superseded(self) -> bool:
        # E90 (2026-08-30) is the live definition; no E28-basis row remains
        # on the watchlist, and the flag keeps marking E32's retained
        # fv_base_x_tier history.
        return self.definition not in (MBP_DEF_E28, MBP_DEF_E90)


@dataclass(frozen=True)
class GrowthView:
    """E28's pre-registered growth view, read off the watchlist entry.

    **THE NUMBERS ARE THE OWNER'S AND NOTHING HERE FORMS ONE.** This is a
    reader, not a source: it moves the three rates from prose the code
    could not see -- `reference/growth-views/<TICKER>.md`, and a hard-coded
    copy inside whichever `tools/` script last struck the name -- to the
    entry for the name being watched. E28's ORDERING IS UNTOUCHED: `view`
    names the file the words were written in and `registered` the day they
    were written, and both are required, so a view can still be shown to
    predate the fair value it was used for.

    WHY THE WATCHLIST AND NOT THE STORE. `config/manual/<TICKER>.yaml` is
    the store of FIGURES THE ACCOUNTS STATE; a growth view is a judgement
    about the future that no filing contains, and putting it there would
    make it look like one more thing read off a page.
    """

    base: float
    view: str
    registered: date
    bear: float | None = None
    bull: float | None = None

    @property
    def has_band(self) -> bool:
        return self.bear is not None and self.bull is not None


def _parse_growth(raw: Any, index: int, ticker: Any) -> "GrowthView | None":
    """E28's view, or None where the entry does not carry one.

    ABSENT IS NOT ZERO GROWTH AND NEVER READ AS ONE: a name with no view
    has no fair value at all, which is E28's rule and not this parser's.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ConfigError(f"{_where(index, ticker)}: growth must be a mapping "
                          f"with {', '.join(GROWTH_KEYS)}")
    unknown = sorted(set(raw) - set(GROWTH_KEYS))
    if unknown:
        raise ConfigError(f"{_where(index, ticker)}: growth has unknown "
                          f"key(s) {', '.join(unknown)}")
    missing = [k for k in GROWTH_REQUIRED if raw.get(k) in (None, "")]
    if missing:
        raise ConfigError(
            f"{_where(index, ticker)}: growth is missing {', '.join(missing)}. "
            f"E28 pre-registers a view BEFORE any fair value is solved, and a "
            f"rate with no file and no date cannot be shown to have been "
            f"written first -- which is the whole of what pre-registration "
            f"means.")
    rates: dict[str, float | None] = {}
    for key in ("base", "bear", "bull"):
        value = _as_float(raw.get(key), f"growth.{key}", index, ticker)
        if value is not None and not -0.50 <= value <= 0.50:
            raise ConfigError(
                f"{_where(index, ticker)}: growth.{key} is {value}, outside "
                f"-50%..+50%. A view is a FRACTION -- 0.08 for 8% -- and 8 "
                f"entered for 8% would be read as 800% and pass every other "
                f"check in this file.")
        rates[key] = value
    if (rates["bear"] is None) != (rates["bull"] is None):
        raise ConfigError(
            f"{_where(index, ticker)}: growth.bear and growth.bull come "
            f"TOGETHER or not at all. E90's cushion and E29's band are struck "
            f"against the bear case; a bull with no bear is half a range "
            f"nobody can read.")
    if rates["bear"] is not None and not rates["bear"] <= rates["base"] <= rates["bull"]:
        raise ConfigError(
            f"{_where(index, ticker)}: growth wants bear <= base <= bull and "
            f"has {rates['bear']}, {rates['base']}, {rates['bull']}. A base "
            f"outside its own range is a typo, not a view.")
    view = str(raw["view"]).strip()
    if not view.startswith("reference/growth-views/"):
        raise ConfigError(
            f"{_where(index, ticker)}: growth.view must name the file the "
            f"view was WRITTEN in, under reference/growth-views/; got "
            f"{view!r}. A rate whose reasoning is nowhere is a number, not a "
            f"view.")
    registered = _as_date(raw.get("registered"), "growth.registered",
                          index, ticker)
    return GrowthView(base=rates["base"], bear=rates["bear"],
                      bull=rates["bull"], view=view, registered=registered)


def _parse_mbp_basis(raw: Any, index: int,
                     ticker: Any) -> "MbpBasisRecord | None":
    """E32's two facts, both or neither.

    The date grammar has exactly two forms and the second one exists for
    a reason worth stating: LIAB.ST's `mbp` predates the oldest backup on
    disk and the watchlist was not tracked in git then, so the day it was
    struck is not recoverable. `on or before 2026-08-21` records what is
    known. Inventing a day would be worse than the imprecision, and a
    third form would invite prose where a date belongs.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ConfigError(f"{_where(index, ticker)}: mbp_basis must be a "
                          f"mapping with {', '.join(MBP_BASIS_KEYS)}")
    unknown = sorted(set(raw) - set(MBP_BASIS_KEYS))
    if unknown:
        raise ConfigError(f"{_where(index, ticker)}: mbp_basis has unknown "
                          f"key(s) {', '.join(unknown)}")
    missing = [k for k in MBP_BASIS_KEYS if raw.get(k) in (None, "")]
    if missing:
        raise ConfigError(
            f"{_where(index, ticker)}: mbp_basis is missing "
            f"{', '.join(missing)}. E32 records both or neither: a "
            f"definition with no date cannot be told from a later one, and "
            f"a date with no definition says nothing.")
    definition = str(raw["definition"]).strip()
    if definition not in VALID_MBP_DEFINITIONS:
        raise ConfigError(
            f"{_where(index, ticker)}: mbp_basis.definition must be one of "
            f"{'|'.join(VALID_MBP_DEFINITIONS)}, got {raw['definition']!r}")
    struck = str(raw["struck"]).strip()
    if not (MBP_STRUCK_EXACT.match(struck) or MBP_STRUCK_BOUND.match(struck)):
        raise ConfigError(
            f"{_where(index, ticker)}: mbp_basis.struck must be "
            f"`YYYY-MM-DD` or `on or before YYYY-MM-DD`, got {struck!r}. "
            f"The second form is for a date that is not recoverable; there "
            f"is no third form, and a day must never be invented to fill "
            f"this in.")
    return MbpBasisRecord(definition=definition, struck=struck)


#: B45 (implemented 2026-08-30): one item per FILL, as the broker executed
#: it. `date`, `shares` and `rule` are required -- a sale with no date is
#: not a sale, a sale with no size is not a fill, and a sale with no rule
#: is a trade the framework cannot learn from. `price` is OPTIONAL and its
#: absence is DATA MISSING: `vss sales` prints the fill as unpriced and
#: NEVER reads a price off a bar to fill it in. `proceeds_sek` is what
#: actually landed in the account, net of the broker's charges and FX --
#: a different quantity from price x shares, kept apart from it.
SALE_KEYS = ("date", "price", "currency", "shares", "account", "rule",
             "run_record", "proceeds_sek", "note")
#: The rule that fired. C1-C4 are FRAMEWORK section 6.4's exit rules as
#: FRAMEWORK-EDITS numbers them (C4 = the fair-value-gap exit, E42 its
#: horizon); `owner` is a discretionary sale outside any rule, which is
#: allowed and is named as such so the record can tell the two apart.
VALID_SALE_RULES = ("C1", "C2", "C3", "C4", "owner")


@dataclass(frozen=True)
class SaleRecord:
    """One executed fill of a position (B45)."""

    date: date
    shares: float
    rule: str
    #: In `currency` (the entry's quote currency when not stated). None is
    #: DATA MISSING -- the owner has not entered the fill -- and stays so.
    price: float | None = None
    currency: str | None = None
    account: str | None = None
    #: The section 5 run record the rule was struck against, as a path,
    #: where one exists. Older sales were struck in workbooks and carry
    #: none; the note says where.
    run_record: str | None = None
    proceeds_sek: float | None = None
    note: str | None = None

    @property
    def price_missing(self) -> bool:
        return self.price is None


def _parse_sales(raw: Any, index: int, ticker: Any,
                 currency: str) -> tuple[SaleRecord, ...]:
    """B45's `sales:` block: a list of fills, validated, oldest first."""
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ConfigError(f"{_where(index, ticker)}: sales must be a list of "
                          f"fills, one mapping per executed transaction")
    fills: list[SaleRecord] = []
    for n, item in enumerate(raw, start=1):
        where = f"{_where(index, ticker)}: sales[{n}]"
        if not isinstance(item, dict):
            raise ConfigError(f"{where}: each fill must be a mapping with "
                              f"{', '.join(SALE_KEYS)}")
        unknown = sorted(set(item) - set(SALE_KEYS))
        if unknown:
            raise ConfigError(f"{where}: unknown key(s) {', '.join(unknown)}. "
                              f"Allowed: {', '.join(SALE_KEYS)}")
        missing = [k for k in ("date", "shares", "rule")
                   if item.get(k) in (None, "")]
        if missing:
            raise ConfigError(
                f"{where}: missing {', '.join(missing)}. A fill needs its "
                f"date, its size and the rule that fired; only the price "
                f"may be absent, and then it is DATA MISSING -- never "
                f"inferred from a bar.")
        sale_date = _as_date(item.get("date"), "date", index, ticker)
        shares = _as_float(item.get("shares"), "shares", index, ticker)
        if shares is None or shares <= 0:
            raise ConfigError(f"{where}: shares must be a positive number, "
                              f"got {item.get('shares')!r}")
        rule = str(item["rule"]).strip()
        rule = "owner" if rule.lower() == "owner" else rule.upper()
        if rule not in VALID_SALE_RULES:
            raise ConfigError(f"{where}: rule must be one of "
                              f"{'|'.join(VALID_SALE_RULES)}, got "
                              f"{item.get('rule')!r}")
        price = _as_float(item.get("price"), "price", index, ticker)
        if price is not None and price <= 0:
            raise ConfigError(f"{where}: price must be positive, got "
                              f"{item.get('price')!r}; leave it blank where "
                              f"the fill is not known")
        proceeds = _as_float(item.get("proceeds_sek"), "proceeds_sek",
                             index, ticker)
        if proceeds is not None and proceeds < 0:
            raise ConfigError(f"{where}: proceeds_sek must not be negative, "
                              f"got {item.get('proceeds_sek')!r}")
        fill_currency = _as_text(item.get("currency"))
        fill_currency = (upper_safe_code(fill_currency.strip())
                         if fill_currency else currency)
        fills.append(SaleRecord(
            date=sale_date, shares=shares, rule=rule, price=price,
            currency=fill_currency, account=_as_text(item.get("account")),
            run_record=_as_text(item.get("run_record")),
            proceeds_sek=proceeds, note=_as_text(item.get("note")),
        ))
    fills.sort(key=lambda f: f.date)
    return tuple(fills)


def _parse_fx(raw: Any, index: int, ticker: Any) -> "FxRecord | None":
    """E24's six facts, all six or none.

    Five of six is not a record: a rate without its own as-of date cannot
    be re-struck, and a rate without a direction is as likely to be its
    reciprocal. So a partial block is an error rather than a best effort.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ConfigError(f"{_where(index, ticker)}: fx must be a mapping with "
                          f"{', '.join(FX_KEYS)}")
    unknown = sorted(set(raw) - set(FX_KEYS))
    if unknown:
        raise ConfigError(f"{_where(index, ticker)}: fx has unknown key(s) "
                          f"{', '.join(unknown)}")
    missing = [k for k in FX_KEYS if raw.get(k) in (None, "")]
    if missing:
        raise ConfigError(
            f"{_where(index, ticker)}: fx is missing {', '.join(missing)}. "
            f"E24 records six things or none: a rate without its own as-of "
            f"date cannot be re-struck, and a rate without a direction is as "
            f"likely to be its reciprocal.")
    pair = str(raw["pair"]).strip().upper()
    if not FX_PAIR_PATTERN.match(pair):
        raise ConfigError(f"{_where(index, ticker)}: fx pair must read "
                          f"BASE->QUOTE, e.g. EUR->SEK, got {raw['pair']!r}")
    rate = _as_float(raw.get("rate"), "fx.rate", index, ticker)
    if rate is None or rate <= 0:
        raise ConfigError(f"{_where(index, ticker)}: fx rate must be positive, "
                          f"got {raw['rate']!r}")
    converted = str(raw["converted"]).strip().lower()
    if converted not in FX_SIDES:
        raise ConfigError(f"{_where(index, ticker)}: fx converted must be one "
                          f"of {'|'.join(FX_SIDES)} -- which side the rate was "
                          f"applied to -- got {raw['converted']!r}")
    return FxRecord(
        pair=pair, rate=rate,
        rate_as_of=_as_date(raw.get("rate_as_of"), "fx.rate_as_of", index, ticker),
        source=str(raw["source"]).strip(), converted=converted,
        price_date=_as_date(raw.get("price_date"), "fx.price_date", index, ticker),
    )


def _parse_exec_changes(raw: Any, index: int, ticker: Any):
    """None = not recorded (cannot evaluate). [] = checked, no departures."""
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ConfigError(f"{_where(index, ticker)}: exec_changes must be a list")

    parsed = []
    for n, item in enumerate(raw):
        where = f"{_where(index, ticker)} exec_change #{n + 1}"
        if not isinstance(item, dict):
            raise ConfigError(f"{where}: expected a mapping")
        unknown = set(item) - ALLOWED_EXEC_KEYS
        if unknown:
            raise ConfigError(f"{where}: unknown key(s) {', '.join(sorted(unknown))}")
        role = _as_text(item.get("role"))
        if role is None:
            raise ConfigError(f"{where}: role is required (CEO | CFO | other)")
        departed = _as_date(item.get("departed"), "departed", index, ticker)
        if departed is None:
            raise ConfigError(f"{where}: departed is required (YYYY-MM-DD)")
        parsed.append(ExecChange(role=role.strip(), departed=departed))
    return tuple(parsed)


def parse_entry(raw: Any, index: int) -> WatchlistEntry:
    """Validate one raw mapping into a WatchlistEntry, or raise ConfigError."""
    if not isinstance(raw, dict):
        raise ConfigError(f"{_where(index)}: expected a mapping, got {type(raw).__name__}")

    ticker = raw.get("ticker")

    conflicts = COMPUTED_KEYS & set(raw)
    if conflicts:
        raise ConfigError(
            f"{_where(index, ticker)}: {', '.join(sorted(conflicts))} is COMPUTED by vss "
            f"and must not be set by hand. Under E28, as E32 rules it "
            f"governs, MBP is the price at which implied growth equals the "
            f"PRE-REGISTERED bear case, with the tier cushion on that. "
            f"`fv_base * tier multiplier` is SUPERSEDED AS A DEFINITION and "
            f"is what `rules.compute_mbp` still computes -- so a figure it "
            f"produces carries `mbp_basis` saying so. Set fv_base and tier; "
            f"the field is never entered by hand either way."
        )

    unknown = set(raw) - ALLOWED_KEYS
    if unknown:
        raise ConfigError(
            f"{_where(index, ticker)}: unknown key(s) {', '.join(sorted(unknown))}. "
            f"Allowed: {', '.join(sorted(ALLOWED_KEYS))}"
        )

    missing = REQUIRED_KEYS - set(raw)
    if missing:
        raise ConfigError(
            f"{_where(index, ticker)}: missing required key(s) {', '.join(sorted(missing))}"
        )

    for key in sorted(REQUIRED_KEYS):
        if _as_text(raw.get(key)) is None:
            raise ConfigError(f"{_where(index, ticker)}: {key} must not be empty")

    status = str(raw["status"]).strip().upper()
    if status in RETIRED_STATUSES:
        # A retired spelling is a different error from a typo: the file is
        # not wrong, it is out of date, and the fix is a decision rather
        # than a correction. Say which decision.
        raise ConfigError(
            f"{_where(index, ticker)}: status {raw['status']!r} is retired. "
            f"{RETIRED_STATUSES[status]}"
        )
    if status not in VALID_STATUSES:
        raise ConfigError(
            f"{_where(index, ticker)}: status must be one of "
            f"{'|'.join(VALID_STATUSES)}, got {raw['status']!r}"
        )
    # E111 (2026-09-04): an INTAKE name is READ, NOT WATCHED, and carries no
    # entry stamp. The refusal is here rather than left to a convention
    # because the whole point of the status is that reading a company must
    # not start E12's clock by accident -- and a stamp written by mistake is
    # exactly an accident.
    if status == "INTAKE":
        present = [k for k in INTAKE_REFUSED_KEYS if raw.get(k) is not None]
        if present:
            raise ConfigError(
                f"{_where(index, ticker)}: status INTAKE carries "
                f"{', '.join(present)}, and each is an ENTRY FACT. An intake "
                f"is READ, NOT WATCHED: no `dd_at_entry` and no `peak_date` "
                f"(E12 freezes Gate 1 at ENTRY, and an intake has no dated "
                f"starting point to freeze), no `stop_price`, no `tier` -- "
                f"and no tier is what removes the MBP, since `compute_mbp` is "
                f"fv_base x the tier multiplier. PROMOTION TO PIPELINE is "
                f"what stamps the entry, and that promotion is the owner's "
                f"act, not a side effect of writing a growth view down.")

    tier = raw.get("tier")
    if tier is not None:
        # int(2.5) silently truncates to 2, which would change the computed
        # MBP. Require an exactly integral value.
        raw_tier = tier
        try:
            tier = int(raw_tier)
            integral = not isinstance(raw_tier, bool) and float(raw_tier) == tier
        except (TypeError, ValueError):
            integral = False
        if not integral or tier not in VALID_TIERS:
            raise ConfigError(
                f"{_where(index, ticker)}: tier must be 1, 2 or 3, got {raw_tier!r}"
            )

    dd_at_entry = _as_float(raw.get("dd_at_entry"), "dd_at_entry", index, ticker)
    peak_date = _as_date(raw.get("peak_date"), "peak_date", index, ticker)
    _check_entry_drawdown(dd_at_entry, peak_date, index, ticker)

    catalyst_date = _as_date(raw.get("catalyst_date"), "catalyst_date", index, ticker)
    catalyst_resolved = _as_date(
        raw.get("catalyst_resolved"), "catalyst_resolved", index, ticker
    )
    # Resolving a catalyst before it happened is a data error, not a
    # resolution. Fail the run rather than let it silently unblock.
    if catalyst_date is not None and catalyst_resolved is not None:
        if catalyst_resolved < catalyst_date:
            raise ConfigError(
                f"{_where(index, ticker)}: catalyst_resolved "
                f"{catalyst_resolved.isoformat()} is earlier than catalyst_date "
                f"{catalyst_date.isoformat()} -- an outcome cannot be ingested "
                f"before the event occurs"
            )

    frequency = _as_text(raw.get("reporting_frequency"))
    if frequency is None:
        frequency = DEFAULT_REPORTING_FREQUENCY
    else:
        frequency = frequency.strip().lower()
        if frequency not in VALID_REPORTING_FREQUENCIES:
            raise ConfigError(
                f"{_where(index, ticker)}: reporting_frequency must be one of "
                f"{'|'.join(VALID_REPORTING_FREQUENCIES)}, got "
                f"{raw.get('reporting_frequency')!r}"
            )

    # `.upper()` is not safe on a currency code. `GBp` upper-cases to
    # `GBP`, which is a DIFFERENT UNIT -- pounds where the quote is pence --
    # and `fv_base`, `stop_price` and the mbp derived from them are compared
    # against `last_close` with no conversion anywhere (E24), so the error is
    # a factor of a hundred and shows as nothing: a 4,161p close against an
    # 84.00 mbp simply produces no verdict, and a stop never breaches.
    # `fx.upper_safe_code` maps it to `GBX`, which means the same thing and
    # survives the round trip. The required-key check above guarantees the
    # value is non-blank, so this cannot come back None.
    currency = upper_safe_code(str(raw["currency"]).strip())

    # E121(c), 2026-09-20. A ticker with NO exchange suffix is treated as a
    # US listing on the NYSE calendar, and that is the ruling's one weak
    # leg: it rests on the vendor's convention that only non-US listings
    # carry a suffix. So the convention is CHECKED HERE rather than
    # assumed -- a US listing quotes in USD, and a name that does not is
    # refused by name with the check that failed. A suffixed ticker is not
    # touched: its market comes from the mapping table, which is data.
    if "." not in ticker and currency != "USD":
        raise ConfigError(
            f"{_where(index, ticker)}: the ticker carries NO exchange suffix, "
            f"so E121(c) reads it as a US listing on the NYSE calendar for "
            f"session counting -- but it is quoted in {currency}, not USD. "
            f"Either the ticker is missing its suffix (write it: 'XYZ.ST') "
            f"or the currency is wrong. FAILED CHECK: E121(c), unsuffixed "
            f"ticker must be a US listing.")

    # The two price legs are checked before the entry is built: a level
    # that cannot be a price is a provenance problem, not a low number.
    fv_base = _as_float(raw.get("fv_base"), "fv_base", index, ticker)
    fv_bull = _as_float(raw.get("fv_bull"), "fv_bull", index, ticker)
    stop_price = _as_float(raw.get("stop_price"), "stop_price", index, ticker)
    _check_price_leg(fv_base, "fv_base", index, ticker)
    _check_price_leg(fv_bull, "fv_bull", index, ticker)
    _check_price_leg(stop_price, "stop_price", index, ticker)


    fx = _parse_fx(raw.get("fx"), index, ticker)
    hurdle = _parse_hurdle(raw.get("hurdle"), index, ticker)
    mbp_basis = _parse_mbp_basis(raw.get("mbp_basis"), index, ticker)
    quarters = _parse_quarters(raw.get("quarters"), index, ticker, frequency)
    exec_changes = _parse_exec_changes(raw.get("exec_changes"), index, ticker)
    sales = _parse_sales(raw.get("sales"), index, ticker, currency)

    # THE EXIT TEST A HOLDING MUST HAVE (owner, 2026-09-20). C4 and E42 run
    # the exit against FV_bull -- LIAB.ST's full exit of 2026-09-19 was
    # decided on the close standing above it -- so a HELD name with no
    # struck bull has no exit test. It is refused HERE, where a name
    # BECOMES held, and never as a runtime blocker: a blocker suppresses
    # EVERY verdict, and silencing a holding's STOP to enforce a bull would
    # be the very failure this is meant to prevent.
    if status == "HELD" and fv_bull is None:
        raise ConfigError(
            f"{_where(index, ticker)}: status HELD with no `fv_bull`. The "
            f"exit test is the bull case (C4 / E42), so a holding without "
            f"one cannot be exited by the framework that holds it. Strike "
            f"the bull -- the record replayed at the growth view's g_bull -- "
            f"and record it here before the name is held.")

    return WatchlistEntry(
        ticker=str(raw["ticker"]).strip(),
        name=str(raw["name"]).strip(),
        currency=currency,
        status=status,
        reporting_frequency=frequency,
        cik=_as_cik(raw.get("cik"), index, ticker),
        fv_base=fv_base,
        fv_bull=fv_bull,
        tier=tier,
        dd_at_entry=dd_at_entry,
        peak_date=peak_date,
        stop_price=stop_price,
        catalyst_date=catalyst_date,
        catalyst_resolved=catalyst_resolved,
        catalyst_event=_as_text(raw.get("catalyst_event")),
        notes=_as_text(raw.get("notes")),
        quarters=quarters,
        exec_changes=exec_changes,
        fx=fx,
        hurdle=hurdle,
        mbp_basis=mbp_basis,
        run_record=_as_text(raw.get("run_record")),
        sales=sales,
        growth=_parse_growth(raw.get("growth"), index, ticker),
    )


def parse_watchlist(document: Any) -> list[WatchlistEntry]:
    """Validate a parsed YAML document into entries. Raises ConfigError."""
    if document is None:
        raise ConfigError("watchlist is empty")
    if not isinstance(document, dict) or "tickers" not in document:
        raise ConfigError("watchlist must be a mapping with a top-level 'tickers:' list")

    raw_entries = document["tickers"]
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ConfigError("'tickers:' must be a non-empty list")

    entries = [parse_entry(raw, i) for i, raw in enumerate(raw_entries)]

    seen: dict[str, int] = {}
    for i, entry in enumerate(entries):
        if entry.ticker in seen:
            raise ConfigError(
                f"duplicate ticker {entry.ticker!r} "
                f"(entries #{seen[entry.ticker] + 1} and #{i + 1})"
            )
        seen[entry.ticker] = i
    return entries


def load_watchlist(path: Path) -> list[WatchlistEntry]:
    """Read and validate the watchlist file."""
    if not path.exists():
        raise ConfigError(
            f"watchlist not found at {path}. "
            f"Copy config/watchlist.example.yaml to {path} and fill it in."
        )
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}")
    return parse_watchlist(document)
