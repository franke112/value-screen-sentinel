"""E94: what it would take to value a ranked name.

The ranked list says which names are cheap on two vendor ratios. It says
nothing about **what it would cost to value one properly** — and a name
whose store is complete is an evening away from a fair value while a name
with no store is a week away. This module tells those apart.

Per ranked name it produces:

* **g\\***, the market-implied growth at the current price (E28's own
  figure). A g\\* above r is a NUMBER, not a refusal — the cap at the hurdle
  was removed after REVIEW-4 (report C 9.3 #1). The solver refuses only at
  its own bounds, and that is an INPUT fault, never a verdict.
* **A §5 readiness assessment** — legs present, DATA MISSING, UNVERIFIED
  and blocking under E21, whether a record forms with ZERO hand inputs, and
  whether the issuer's figures come automatically or by hand (E92).
* **An INDICATIVE fair value**, behind four fences (E94): every leg
  present; every figure the basis reads VERIFIED under E40; never from
  screener/Yahoo fundamentals — the STORE or nothing; and only on the
  owner's PRE-REGISTERED growth view.

**AN INDICATIVE VALUE IS PRINTED AND NOTHING ELSE.** It is never written to
the watchlist, never given an MBP (a tier follows a §4.4 score, which
follows the E76 reading — none of which a screen has done), and never a
strike. It is a signpost saying the strike is now cheap to make.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GROWTH_VIEWS_DIR = PROJECT_ROOT / "reference" / "growth-views"

# --- the growth view: read strictly, or not at all -------------------------

VIEW_REGISTERED = "registered"
VIEW_ABSENT = "absent"
VIEW_UNREADABLE = "unreadable"

#: A percentage, allowing the UNICODE MINUS the owner actually types --
#: NVR's bear is `−3%` (U+2212), which `float()` refuses and a naive parser
#: would read as +3%, flipping the sign of a whole case.
_PCT = re.compile(r"([-−+]?\d+(?:[.,]\d+)?)\s*%")

#: The label must OPEN its line, after nothing but list/table punctuation and
#: markdown bold, and be closed by a colon or a table pipe. Deliberately
#: strict: GDDY's file contains the prose "superseded view (fv_base 156.45,
#: bear 111.36, bull 200.58...)", and a looser pattern would read that
#: sentence's 111.36 as a growth rate.
_LABELS = {
    "base": re.compile(
        r"^\s*[-*|]*\s*\*{0,2}(?:g_base|base case fcf growth[^:|]*|base)"
        r"\*{0,2}\s*[:|]", re.I),
    "bear": re.compile(r"^\s*[-*|]*\s*\*{0,2}(?:g_bear|bear)\*{0,2}\s*[:|]", re.I),
    "bull": re.compile(r"^\s*[-*|]*\s*\*{0,2}(?:g_bull|bull)\*{0,2}\s*[:|]", re.I),
}


#: E95: the marker, and what ends its reach. A `## SUPERSEDED` heading
#: opens a block that is skipped to the next `##` heading of the same depth.
#: The heading may carry anything after the word -- GDDY's says
#: "## SUPERSEDED — the first view, 2026-08-30 (kept in the record, never
#: edited)" -- and the match is on the opening word alone.
_HEADING = re.compile(r"^\s{0,3}##(?!#)\s*")
_SUPERSEDED = re.compile(r"^\s{0,3}##(?!#)\s*SUPERSEDED\b", re.I)


@dataclass(frozen=True)
class GrowthView:
    """The owner's pre-registered g, as the file states it (E28)."""

    ticker: str
    base: float
    bear: float | None
    bull: float | None
    path: Path
    state: str = VIEW_REGISTERED
    detail: str = ""

    @property
    def registered(self) -> bool:
        return self.state == VIEW_REGISTERED

    def describe(self) -> str:
        return (f"g_base {self.base:.2%}, g_bear "
                f"{self.bear:.2%}" if self.bear is not None else
                f"g_base {self.base:.2%}") + (
            f", g_bull {self.bull:.2%}" if self.bull is not None else "")


def _percent(text: str) -> float | None:
    match = _PCT.search(text)
    if match is None:
        return None
    raw = match.group(1).replace("−", "-").replace(",", ".")
    try:
        return float(raw) / 100.0
    except ValueError:
        return None


def read_growth_view(ticker: str, *,
                     directory: Path | None = None) -> GrowthView | None:
    """The owner's registered view, or None with the reason.

    **NEVER INFERRED, DEFAULTED OR BORROWED** (E94). Three outcomes, and the
    difference between the last two matters to the owner:

    * ABSENT   — no file. He has not written one.
    * UNREADABLE — a file exists and this parser could not get three rates
      out of it. That is reported AS SUCH, so it is never mistaken for "you
      have not written one".
    * REGISTERED — base, bear and bull all read, unambiguously.

    Ambiguity refuses. Where a label appears twice with DIFFERENT values the
    view is unreadable, because picking one would be choosing the owner's
    judgement for him.
    """
    directory = directory or GROWTH_VIEWS_DIR
    path = Path(directory) / f"{ticker.upper()}.md"
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return GrowthView(ticker, 0.0, None, None, path, VIEW_UNREADABLE,
                          f"the file could not be read: {exc}")

    found: dict[str, list[float]] = {"base": [], "bear": [], "bull": []}
    skipping = False
    for line in text.splitlines():
        # E95: a `## SUPERSEDED` heading opens a block the reader SKIPS,
        # until the next `##` heading. The old view stays in the file --
        # E76 requires it -- and simply stops being read.
        if _HEADING.match(line):
            skipping = bool(_SUPERSEDED.match(line))
        if skipping:
            continue
        for name, pattern in _LABELS.items():
            match = pattern.match(line)
            if match is None:
                continue
            value = _percent(line[match.end():])
            if value is not None:
                found[name].append(value)

    ambiguous = [n for n, values in found.items() if len(set(values)) > 1]
    if ambiguous:
        return GrowthView(
            ticker, 0.0, None, None, path, VIEW_UNREADABLE,
            f"{', '.join(sorted(ambiguous))} stated more than once with "
            f"different values; choosing one would be choosing the owner's "
            f"judgement for him")
    missing = [n for n, values in found.items() if not values]
    if missing:
        return GrowthView(
            ticker, 0.0, None, None, path, VIEW_UNREADABLE,
            f"no {', '.join(sorted(missing))} rate could be read from the file")
    return GrowthView(ticker, found["base"][0], found["bear"][0],
                      found["bull"][0], path)


# --- currency units: pence is not pounds ----------------------------------

#: Minor-unit quote labels. Yahoo writes London prices as `GBp` -- PENCE --
#: and the store writes the same thing as `GBX`, while the ACCOUNTS are in
#: `GBP`. The distinction is carried by CASE ALONE in the vendor's label, so
#: `quote.upper() == reporting.upper()` silently equates a pence price with
#: a pound per-share value and reports a g* off by a factor of a hundred.
#: That is exactly what happened to AUTO.L, RMV.L, RKT.L and IMB.L before
#: this existed, and their g* read +72% to +75%.
_MINOR_UNITS = {"GBP": ("GBX", "GBP")}          # major -> minor spellings


def currency_unit(label: str | None) -> tuple[str | None, bool]:
    """(major currency code, is the label a MINOR unit?).

    `GBp` and `GBX` are pence; `GBP` is pounds. The test is not a case-
    insensitive compare -- case is the whole of the signal.
    """
    if not label:
        return None, False
    raw = label.strip()
    if not raw:
        return None, False
    upper = raw.upper()
    if upper in ("GBX", "GBP"):
        # `GBp` (mixed case) and `GBX` are pence; `GBP` is pounds.
        minor = raw == "GBX" or (upper == "GBP" and raw != "GBP")
        return "GBP", minor
    # The general vendor convention: a trailing lowercase letter on an
    # otherwise uppercase code marks the minor unit (ZAc, ILa).
    if len(raw) == 3 and raw[:2].isupper() and raw[2].islower():
        return upper, True
    return upper, False


def comparable_currencies(quote: str | None, reporting: str | None) -> bool:
    """May a price in ``quote`` be divided into a value stated in
    ``reporting``? Same code AND the same major/minor unit, or no."""
    q_code, q_minor = currency_unit(quote)
    r_code, r_minor = currency_unit(reporting)
    if q_code is None or r_code is None:
        return True                 # nothing to contradict; the caller says so
    return q_code == r_code and q_minor == r_minor


# --- the route ------------------------------------------------------------

ROUTE_AUTOMATIC = "automatic"
ROUTE_HAND = "hand download"
ROUTE_NEEDS_CIK = "automatic once a CIK is on file"

#: Suffixes the Nasdaq Nordic feed can be asked about (E92's fetcher), even
#: where this ticker has no issuer row yet -- `vss nordic --resolve` exists.
_NORDIC_SUFFIXES = (".ST", ".CO", ".HE", ".IC")


def route_for_ticker(ticker: str, *, cik: int | None = None,
                     store_origin: str | None = None) -> tuple[str, str]:
    """(route, why) for a name that may not be on the watchlist at all.

    `refresh.route_for` answers for a watchlist ENTRY; a ranked name usually
    has none, so this answers from the ticker, the store and the registries.
    """
    from .refresh import (NO_ADAPTER_ISSUERS, REFUSING_ISSUERS,
                          _on_nordic_feed)

    key = ticker.upper()
    if store_origin == "sec-xbrl":
        return ROUTE_AUTOMATIC, "already on the SEC XBRL path (the store says so)"
    refused = REFUSING_ISSUERS.get(key)
    gap = NO_ADAPTER_ISSUERS.get(key)
    if cik is not None:
        return ROUTE_AUTOMATIC, f"SEC XBRL companyfacts, CIK {int(cik)}"
    if _on_nordic_feed(key):
        return ROUTE_AUTOMATIC, "on the Nasdaq Nordic feed"
    if refused is not None:
        return ROUTE_HAND, refused.reason
    if gap is not None:
        return ROUTE_HAND, gap.reason
    if "." not in key:
        # A US listing. The facts are reachable; the CIK is not looked up.
        return ROUTE_NEEDS_CIK, ("a US listing: data.sec.gov answers, but no "
                                 "CIK resolution step is built (a gap, not a "
                                 "closed door -- company_tickers.json answers "
                                 "200 to a caller with a contact)")
    if key.endswith(_NORDIC_SUFFIXES):
        return ROUTE_NEEDS_CIK, ("a Nordic listing with no issuer row yet: "
                                 f"`vss nordic --resolve --ticker {key}` "
                                 f"would establish one")
    return ROUTE_HAND, ("no adapter is built for this market's archive "
                        "(FETCHER-SURVEY section 6)")


# --- readiness -------------------------------------------------------------

#: E51 / E96: the name is outside the circle of competence and section 5
#: cannot be run on it AT ALL. This outranks every other state -- a
#: complete, fully verified store does not make a name valuable if the
#: method cannot value it, and printing READY beside one would invite
#: exactly the growth view the ruling says nobody can write.
STATE_OUT_OF_CIRCLE = "OUTSIDE THE CIRCLE OF COMPETENCE"
STATE_NO_STORE = "NO STORE"
STATE_NO_BASIS = "NO BASIS"
STATE_INCOMPLETE = "INCOMPLETE"
STATE_UNVERIFIED = "UNVERIFIED"
STATE_NEEDS_VIEW = "READY — NEEDS GROWTH VIEW"
STATE_READY = "READY"


@dataclass
class Readiness:
    """What it would take to value this name, and what can be said today."""

    ticker: str
    state: str
    route: str = ""
    route_why: str = ""
    basis: str | None = None
    missing: tuple[str, ...] = ()
    blocking: tuple[str, ...] = ()
    zero_hand_inputs: bool = False
    g_star: float | None = None
    g_star_refused: str = ""
    #: E94: printed, never written, never given an MBP, never a strike.
    indicative: float | None = None
    indicative_on: str = ""
    view: GrowthView | None = None
    detail: str = ""
    currency: str | None = None
    #: The store's QUOTE currency, beside the reporting one above.
    #: Both are needed to tell a pence price from a pound value --
    #: E24's conversion is never made here, so a caller that cannot
    #: compare them must refuse rather than divide.
    quote_currency: str | None = None

    @property
    def ready(self) -> bool:
        return self.state in (STATE_READY, STATE_NEEDS_VIEW)

    def line(self) -> str:
        bits = [self.state]
        if self.g_star is not None:
            bits.append(f"g* {self.g_star:+.2%}")
        elif self.g_star_refused:
            bits.append(f"g* {self.g_star_refused}")
        if self.indicative is not None:
            bits.append(f"INDICATIVE {self.indicative:,.2f} "
                        f"{self.currency or ''}".strip())
        if self.missing:
            bits.append(f"missing: {', '.join(self.missing[:4])}"
                        + ("…" if len(self.missing) > 4 else ""))
        if self.blocking:
            bits.append(f"{len(self.blocking)} UNVERIFIED blocking")
        bits.append(self.route)
        return " | ".join(bits)


def circle_of_competence(ticker: str,
                         industry: str | None = None) -> tuple[str, str] | None:
    """(ruling, reason) where E51 or E96 removes this name, else None.

    Checks the OWNER LIST limb always -- it needs no vendor string -- and the
    INDUSTRY limb only where an industry is supplied. That blindness is the
    same one E51 and E96 both record: fundamentals reach the survivors of
    filter 1 alone, and silence here is a fact about the fetch.
    """
    from .filters import (COMMODITY_PRICE_PATH, PHARMA_BIOTECH_PATH,
                          CircleError, load_circle_of_competence)

    key = ticker.upper()
    industry = (industry or "").strip()
    for path, ruling, subject in (
            (PHARMA_BIOTECH_PATH, "E51",
             "cash flow beyond the next patent expiry turns on clinical trial "
             "outcomes and regulatory approval"),
            (COMMODITY_PRICE_PATH, "E96",
             "revenue is a world price the company does not set, times a "
             "volume -- the bear case is a halved price, not slower growth")):
        try:
            config = load_circle_of_competence(path, ruling=ruling)
        except (CircleError, OSError):
            continue
        if key in config.exempt:
            continue
        if key in config.tickers:
            return ruling, f"{ruling}: named on the owner's list -- {subject}"
        if industry and industry in config.industries:
            return ruling, (f"{ruling}: industry {industry!r} -- {subject}")
    return None


def assess(ticker: str, *, price: float | None = None,
           quote_currency: str | None = None,
           industry: str | None = None,
           as_of: date | None = None,
           manual_dir: Path | None = None,
           views_dir: Path | None = None,
           cik: int | None = None,
           run_ts: datetime | None = None) -> Readiness:
    """E94's per-name assessment. Reads; writes nothing, anywhere."""
    from .config import ConfigError
    from .manual import MANUAL_DIR, load_manual, section5_basis, section5_gate
    from .runrecord import Growth, from_store
    from .valuation import ValuationError, implied_growth

    as_of = as_of or date.today()
    run_ts = run_ts or datetime.now().astimezone()
    manual_dir = manual_dir or MANUAL_DIR
    view = read_growth_view(ticker, directory=views_dir)

    # E51 / E96 FIRST, before any store is opened. Section 5 cannot be run on
    # such a name at all, so its readiness is not a question of legs: no g*,
    # no indicative value, and above all NO "NEEDS GROWTH VIEW" -- that line
    # would ask the owner for the one thing the ruling says cannot be written.
    outside = circle_of_competence(ticker, industry)
    if outside is not None:
        ruling, why = outside
        route, route_why = route_for_ticker(ticker, cik=cik)
        return Readiness(ticker, STATE_OUT_OF_CIRCLE, route, route_why,
                         view=view, detail=why)

    try:
        parsed = load_manual(ticker, directory=manual_dir)
    except (ConfigError, OSError) as exc:
        route, why = route_for_ticker(ticker, cik=cik)
        return Readiness(ticker, STATE_NO_STORE, route, why, view=view,
                         detail=(f"no `config/manual/{ticker.upper()}.yaml` "
                                 f"({type(exc).__name__})"))

    route, why = route_for_ticker(ticker, cik=cik, store_origin=parsed.origin)
    basis = section5_basis(parsed)
    if basis is None:
        return Readiness(ticker, STATE_NO_BASIS, route, why, view=view,
                         currency=parsed.reporting_currency,
                         quote_currency=parsed.quote_currency,
                         detail=("no twelve-month window: fewer than four "
                                 "consecutive quarters and no annual entry "
                                 "(E19)"))

    gate = section5_gate(parsed, as_of=as_of)
    blocking = tuple(f.name for f in gate.blocking)

    # The record is built with the OWNER'S view where one is registered, so
    # that what is printed is the record the value would actually rest on.
    # Where none is, a placeholder base is used ONLY to reach `missing()` and
    # the legs -- and no value is struck off it (E94's fourth fence).
    growth = (Growth(base=view.base, view_file=str(view.path),
                     bear=view.bear, bull=view.bull)
              if view is not None and view.registered
              else Growth(base=0.0, view_file="(readiness probe — NOT a view)"))
    try:
        record = from_store(parsed, basis, growth=growth, run_ts=run_ts,
                            notes="E94 readiness probe — nothing is written")
    except Exception as exc:  # noqa: BLE001 -- a probe never raises upward
        return Readiness(ticker, STATE_INCOMPLETE, route, why,
                         basis=basis.label, view=view,
                         currency=parsed.reporting_currency,
                         quote_currency=parsed.quote_currency,
                         detail=f"the record does not form: "
                                f"{type(exc).__name__}: {exc}")

    gaps = record.missing()
    result = Readiness(
        ticker=ticker, state=STATE_INCOMPLETE, route=route, route_why=why,
        basis=basis.label, missing=tuple(gaps), blocking=blocking,
        zero_hand_inputs=not gaps, view=view,
        currency=parsed.reporting_currency,
        quote_currency=parsed.quote_currency)

    if gaps:
        result.detail = "legs the basis cannot supply"
        return result

    # --- g*, which needs the legs PRESENT but not verified ----------------
    # THE CURRENCY FENCE. `implied_growth` divides a price into a per-share
    # value struck in the REPORTING currency. Where the quote currency
    # differs (RMV.L quotes GBX and reports GBP) the two are not comparable
    # and E24's conversion is not attempted here: a g* off by a factor of a
    # hundred is worse than no g* at all.
    legs = record.legs()
    if price is not None and price > 0:
        if not comparable_currencies(quote_currency, parsed.reporting_currency):
            result.g_star_refused = (
                f"NOT ATTEMPTED: price is {quote_currency}, the accounts are "
                f"{parsed.reporting_currency} (E24's conversion is not made "
                f"here)")
        else:
            try:
                result.g_star = implied_growth(
                    price=price, fcf0=legs.fcf0, net_cash=legs.net_cash,
                    shares=legs.shares, rate=record.rate.rate,
                    terminal=record.conventions.terminal_growth,
                    years=record.conventions.horizon_years)
            except ValuationError as exc:
                # An INPUT fault, reported as one -- never a verdict.
                result.g_star_refused = f"NOT SOLVED (input fault): {exc}"
    elif price is None:
        result.g_star_refused = "no price supplied"

    # --- the four fences on an INDICATIVE value ---------------------------
    if gate.refused:
        result.state = STATE_UNVERIFIED
        reasons = "; ".join(r.detail if hasattr(r, "detail") else str(r)
                            for r in gate.refusals[:3])
        result.detail = (f"the §5 gate refuses: {reasons}"
                         + (f" ({len(blocking)} UNVERIFIED figures the basis "
                            f"reads)" if blocking else ""))
        return result

    if view is None or not view.registered:
        result.state = STATE_NEEDS_VIEW
        result.detail = (
            f"every leg present and VERIFIED, a record forms with zero hand "
            f"inputs — {'no growth view is registered' if view is None else view.detail}")
        return result

    result.state = STATE_READY
    result.indicative = record.strike()
    result.indicative_on = (
        f"{basis.label}; FCF0 {legs.fcf0:,.0f}, net cash {legs.net_cash:,.0f}, "
        f"{legs.shares:,.0f} shares; r {record.rate.rate:.2%}; "
        f"g_base {view.base:.2%} from {view.path.name}")
    result.detail = "indicative only — never written, no MBP, not a strike (E94)"
    return result


# --- rendering -------------------------------------------------------------


def render_readiness_table(items: Sequence[Readiness]) -> list[str]:
    """The block the weekly report carries. A table, then the caveat."""
    out = ["| # | Ticker | Readiness | g* | Indicative | Route | Missing / blocking |",
           "|---:|---|---|---:|---:|---|---|"]
    for index, item in enumerate(items, start=1):
        g = (f"{item.g_star:+.2%}" if item.g_star is not None
             else (item.g_star_refused.split(":")[0] if item.g_star_refused else "--"))
        indicative = (f"{item.indicative:,.2f}" if item.indicative is not None
                      else "--")
        gap = ""
        if item.missing:
            gap = ", ".join(item.missing[:3]) + ("…" if len(item.missing) > 3 else "")
        elif item.blocking:
            gap = f"{len(item.blocking)} UNVERIFIED: " + ", ".join(item.blocking[:3])
        elif item.state == STATE_NEEDS_VIEW:
            gap = "a growth view"
        out.append(f"| {index} | `{item.ticker}` | {item.state} | {g} | "
                   f"{indicative} | {item.route} | {gap} |")
    out.append("")
    out.append("*E94: `g*` is the growth the current price implies — a value "
               "above r is a number, not a refusal. An INDICATIVE value is "
               "printed only where every leg is present AND every figure the "
               "basis reads is VERIFIED (E40) AND the owner's growth view is "
               "registered. **It is never written to the watchlist, never "
               "gets an MBP, and is not a strike** — a real fair value still "
               "needs the owner's write. No indicative value is ever formed "
               "from screener or Yahoo fundamentals.*")
    return out
