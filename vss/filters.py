"""Screener filter steps (phase 2).

Two steps run here, and they are kept separable on purpose:

    step 0  the exclusion list -- names already owned or already decided
    filter 1  price coverage, listing age, a measurable 52-week high, E127

Separable, because the acceptance test for filter 1 uses SAP.DE, and SAP.DE
is on the exclusion list. A test that ran the whole chain would report an
empty result and could not tell "the filter is wrong" from "step 0 removed
it first". ``run_filter1`` therefore takes instruments and knows nothing
about exclusions; ``apply_exclusions`` is called by the chain, never by the
filter.

E161 (2026-11-08): the dislocation band is no longer a filter; the
drawdown from the 52-week high travels as a field.

RSI, SMA50 and SMA200 are computed for every candidate and travel as FIELDS.
Nothing in this module reads them to keep or drop a name -- see the standing
rule in ``screen.py``.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd

from .metrics import (
    LISTING_AGE_YEARS,
    Metrics,
    compute,
    covers_listing_age,
    index_dates,
    listing_age_start,
)
from .series_sanity import STEP_SERIES_SANITY
from .series_sanity import check as series_check
from .rules import (
    stale_close_blocker,
)
from .universe import ON_MISSING, ON_VALUE, Instrument, Rejection, Tally, UniverseError

EXCLUSIONS_PATH = Path("config/screener_exclusions.csv")

#: E51: pharmaceuticals and biotech are outside the circle of competence.
#: Two limbs -- the vendor's industry string and the owner's ticker list --
#: plus the owner's `exempt:` block, all in one file the owner maintains.
PHARMA_BIOTECH_PATH = Path("config/screener_pharma_biotech.yaml")

#: E96's file, the SECOND circle-of-competence limb: a company whose revenue
#: is a world price it does not set. Same shape, same two limbs, its own
#: file -- the two rules are separate grounds and their lists must not mix.
COMMODITY_PRICE_PATH = Path("config/screener_commodity_price.yaml")

#: The exclusion file's header, exactly and in order.
EXCLUSION_SCHEMA: tuple[str, ...] = ("ticker_yahoo", "skal", "datum", "kalla")

STEP_EXCLUSION_LIST = "exclusion_list"
#: E51. Sits INSIDE step 0, after the exclusion list: both remove a name
#: for a reason recorded outside the run, and neither measures anything.
STEP_CIRCLE_OF_COMPETENCE = "circle_of_competence"
#: E96, the SECOND circle-of-competence limb. Its own step name, and not
#: a second tally under E51's: two tallies sharing a name are
#: indistinguishable in the funnel, and a reader must be able to see
#: WHICH ground removed a name without opening the report.
STEP_COMMODITY_PRICE = "commodity_price"
#: E52. Sits at the head of filter 1, on `metrics.first_bar_date`.
STEP_LISTING_AGE = "listing_age"
STEP_PRICE_COVERAGE = "price_coverage"
#: STEP_SERIES_SANITY sits between the two on purpose: it asks whether the
#: series can be measured at all, which is upstream of what it measures to.
#: E161: Gate 1's 15-50% band is gone (attempts #12, #21: it cost in both
#: markets). What stays is that the drawdown must be MEASURABLE -- every
#: candidate carries it as a field -- so a name without a 52-week high is
#: rejected ON MISSING here, never on value.
STEP_HIGH_52W = "high_52w"
#: E127's step, kept in the tally only: E168 removed the rejection.
STEP_TRAILING_YEAR = "trailing_year"

#: B1's window: the "bulk of the decline in the trailing 3-6 months" clause.
B1_WINDOW_DAYS = 180


class ExclusionError(UniverseError):
    """The exclusion list is malformed. Fatal, like a broken universe row."""


# --- the exclusion list ----------------------------------------------------


@dataclass(frozen=True)
class Exclusion:
    ticker_yahoo: str
    skal: str
    datum: date
    kalla: str
    source_line: int = 0


def load_exclusions(path: Path = EXCLUSIONS_PATH) -> list[Exclusion]:
    """Read the committed exclusion list.

    ``skal`` is free text and is NOT validated against a vocabulary: the
    reasons are the owner's and a new one must not need a code change. It
    must merely be present -- an exclusion without a stated reason is the
    thing this file exists to prevent.

    A ticker listed twice is a hard error. Two rows for one name mean the
    file disagrees with itself about why, and picking one silently would
    discard the other reason.
    """
    if not path.exists():
        raise ExclusionError(f"{path}: no such exclusion list")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ExclusionError(f"{path.name}: file is empty, not even a header") from exc
        header = [column.strip().lstrip("﻿") for column in header]
        if tuple(header) != EXCLUSION_SCHEMA:
            raise ExclusionError(
                f"{path.name}: header is {header}, expected {list(EXCLUSION_SCHEMA)}"
            )
        seen: dict[str, int] = {}
        out: list[Exclusion] = []
        for line, row in enumerate(reader, start=2):
            if not row or all(not cell.strip() for cell in row):
                raise ExclusionError(f"{path.name}:{line}: blank row")
            if len(row) != len(EXCLUSION_SCHEMA):
                raise ExclusionError(
                    f"{path.name}:{line}: has {len(row)} fields, "
                    f"expected {len(EXCLUSION_SCHEMA)}"
                )
            values = dict(zip(EXCLUSION_SCHEMA, (cell.strip() for cell in row)))
            for column in EXCLUSION_SCHEMA:
                if not values[column]:
                    raise ExclusionError(
                        f"{path.name}:{line}: column {column!r} is empty and is required"
                    )
            ticker = values["ticker_yahoo"]
            if ticker in seen:
                raise ExclusionError(
                    f"{path.name}:{line}: {ticker} is already excluded on line "
                    f"{seen[ticker]}; one name, one reason"
                )
            try:
                stamp = date.fromisoformat(values["datum"])
            except ValueError as exc:
                raise ExclusionError(
                    f"{path.name}:{line}: datum {values['datum']!r}: {exc}"
                ) from exc
            seen[ticker] = line
            out.append(
                Exclusion(ticker, values["skal"], stamp, values["kalla"], line)
            )
    return out


def apply_exclusions(
    instruments: Sequence[Instrument], exclusions: Sequence[Exclusion]
) -> tuple[list[Instrument], list[Rejection], Tally, list[Exclusion]]:
    """Step 0. Drop names already owned or already decided.

    Matched on ``ticker_yahoo``, exactly. Never on name, never on ISIN --
    there is no ISIN to match on, and a name match is not evidence.

    Returns the survivors, the rejections, the tally, and the exclusions that
    matched NOTHING. That last list matters: an entry for a name outside the
    universe is inert, and an inert entry that looks active is how a name
    quietly comes back.
    """
    tally = Tally(STEP_EXCLUSION_LIST, count_in=len(instruments))
    by_ticker = {e.ticker_yahoo: e for e in exclusions}
    matched: set[str] = set()
    kept, rejections = [], []

    for instrument in instruments:
        exclusion = by_ticker.get(instrument.ticker_yahoo or "")
        if exclusion is None:
            kept.append(instrument)
            continue
        matched.add(exclusion.ticker_yahoo)
        reason = f"{exclusion.skal} since {exclusion.datum.isoformat()}"
        # Rejected on a VALUE -- the owner's decision, recorded and dated.
        tally.reject(ON_VALUE, exclusion.skal)
        rejections.append(
            Rejection(instrument.key, STEP_EXCLUSION_LIST, ON_VALUE, reason)
        )

    tally.count_out = len(kept)
    unmatched = [e for e in exclusions if e.ticker_yahoo not in matched]
    return kept, rejections, tally, unmatched


# --- step 0, second limb: the circle of competence (E51) -------------------


class CircleError(UniverseError):
    """The E51 list is malformed. Fatal, like a broken exclusion list."""


@dataclass(frozen=True)
class CircleConfig:
    """FRAMEWORK-EDITS E51, as the owner's file states it.

    ``industries`` and ``sectors`` are the VENDOR's strings and reach a name
    only where one has been STORED for it; ``tickers`` is the owner's own
    list and does not depend on the vendor having classified anything;
    ``exempt`` is a ticker the string limb catches and the owner has ruled
    back IN. A session never writes to ``exempt`` -- it flags the name.
    """

    industries: frozenset[str] = frozenset()
    sectors: frozenset[str] = frozenset()
    tickers: frozenset[str] = frozenset()
    exempt: frozenset[str] = frozenset()
    #: WHICH RULING this config carries -- "E51" or "E96". The two limbs are
    #: the same mechanism on different grounds, and a rejection must name
    #: the one it stands on: "pharma/biotech" and "commodity price" are not
    #: interchangeable reasons and a reader months later needs the right one.
    ruling: str = "E51"
    label: str = "pharma/biotech"
    #: The tally's step name, so the funnel names the ground.
    step: str = STEP_CIRCLE_OF_COMPETENCE
    #: Why each exempt ticker is exempt, for the report. E51 requires a
    #: reason beside the decision, and an unexplained exemption is the thing
    #: the block exists to prevent.
    exempt_reasons: Mapping[str, str] = field(default_factory=dict)


def load_circle_of_competence(path: Path = PHARMA_BIOTECH_PATH, *,
                              ruling: str = "E51",
                              label: str = "pharma/biotech",
                              step: str = STEP_CIRCLE_OF_COMPETENCE) -> CircleConfig:
    """Read the E51 file.

    A missing file is an ERROR, never an empty config. A run that silently
    ranked a biotech because the file was not there is exactly the failure
    E46 diagnosed for the sector-string exemption, and E51 says section 5
    cannot be run on these names at all.
    """
    import yaml

    if not path.exists():
        raise CircleError(f"{path}: no circle-of-competence list ({ruling})")
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def strings(key: str) -> frozenset[str]:
        rows = document.get(key, [])
        if rows is None:
            rows = []
        if not isinstance(rows, list):
            raise CircleError(f"{path.name}: {key!r} must be a list")
        out: set[str] = set()
        for row in rows:
            value = str(row).strip()
            if not value:
                raise CircleError(f"{path.name}: {key!r} holds an empty entry")
            if value in out:
                raise CircleError(f"{path.name}: {key!r} lists {value!r} twice")
            out.add(value)
        return frozenset(out)

    def ticker_rows(key: str, *, need_reason: bool) -> tuple[frozenset[str], dict[str, str]]:
        rows = document.get(key, [])
        if rows is None:
            rows = []
        if not isinstance(rows, list):
            raise CircleError(f"{path.name}: {key!r} must be a list of rows")
        tickers: set[str] = set()
        reasons: dict[str, str] = {}
        for row in rows:
            if not isinstance(row, Mapping) or not str(row.get("ticker", "")).strip():
                raise CircleError(f"{path.name}: every {key!r} row needs a ticker: {row!r}")
            ticker = str(row["ticker"]).strip()
            if ticker in tickers:
                raise CircleError(f"{path.name}: {key!r} lists {ticker} twice")
            reason = str(row.get("reason", "")).strip()
            if need_reason and not reason:
                # E51: the block exists so the decision is written down.
                raise CircleError(
                    f"{path.name}: {ticker} is exempt with no reason; an "
                    f"exemption without one is what this block exists to prevent"
                )
            tickers.add(ticker)
            reasons[ticker] = reason
        return frozenset(tickers), reasons

    listed, _ = ticker_rows("tickers", need_reason=False)
    exempt, exempt_reasons = ticker_rows("exempt", need_reason=True)
    overlap = listed & exempt
    if overlap:
        raise CircleError(
            f"{path.name}: {', '.join(sorted(overlap))} is on the owner's list "
            f"AND exempt; the file disagrees with itself"
        )
    return CircleConfig(
        industries=strings("industries"),
        sectors=strings("sectors"),
        tickers=listed,
        exempt=exempt,
        exempt_reasons=exempt_reasons,
        ruling=ruling,
        label=label,
        step=step,
    )


@dataclass(frozen=True)
class CircleHit:
    """One name E51 removed, and WHICH limb removed it."""

    ticker: str
    namn: str | None
    limb: str          # "industry", "sector" or "owner list"
    detail: str        # the string that matched, or the owner's note


@dataclass(frozen=True)
class CircleOutcome:
    kept: list[Instrument]
    rejections: list[Rejection]
    tally: Tally
    hits: list[CircleHit]
    #: Tickers on the owner's list that matched NOTHING in this universe --
    #: inert, and an inert entry that looks active is how a name comes back.
    unmatched: list[str]
    #: Names the string limb caught that the owner's `exempt:` block let
    #: through, with the reason. Printed: an exemption nobody sees is the
    #: string exemption's failure again.
    exempted: list[CircleHit]
    #: How many of the instruments offered carried NO vendor string at all.
    #: The string limb is blind to these, and the report must say so.
    without_string: int = 0


def apply_circle_of_competence(
    instruments: Sequence[Instrument],
    config: CircleConfig,
    sector_of: Mapping[str, str | None] | None = None,
    industry_of: Mapping[str, str | None] | None = None,
) -> CircleOutcome:
    """Step 0, second limb. FRAMEWORK-EDITS E51.

    ``sector_of`` and ``industry_of`` are the VENDOR's stored strings, keyed
    on ticker_yahoo. A ticker absent from both is not matched by the string
    limb and is COUNTED -- the limb's silence about it is a fact about the
    fundamentals fetch, which visits the survivors of filter 1 only, and
    never a statement that the company is in the circle.

    The owner's ticker list is checked FIRST and is not exemptible: a name
    the owner has named is out, whatever the vendor calls it.
    """
    sector_of = sector_of or {}
    industry_of = industry_of or {}
    tally = Tally(config.step, count_in=len(instruments))
    kept: list[Instrument] = []
    rejections: list[Rejection] = []
    hits: list[CircleHit] = []
    exempted: list[CircleHit] = []
    matched: set[str] = set()
    without_string = 0

    for instrument in instruments:
        ticker = instrument.ticker_yahoo or ""
        industry = (industry_of.get(ticker) or "").strip()
        sector = (sector_of.get(ticker) or "").strip()
        if not industry and not sector:
            without_string += 1

        hit: CircleHit | None = None
        if ticker in config.tickers:
            matched.add(ticker)
            hit = CircleHit(ticker, instrument.namn, "owner list",
                            f"named by the owner ({config.ruling})")
        elif industry and industry in config.industries:
            hit = CircleHit(ticker, instrument.namn, "industry", industry)
        elif sector and sector in config.sectors:
            hit = CircleHit(ticker, instrument.namn, "sector", sector)

        if hit is None:
            kept.append(instrument)
            continue

        # The owner's own list is a decision and is never exempted by the
        # same file's escape hatch; only the STRING limbs are.
        if hit.limb != "owner list" and ticker in config.exempt:
            exempted.append(
                CircleHit(ticker, instrument.namn, hit.limb,
                          config.exempt_reasons.get(ticker, ""))
            )
            kept.append(instrument)
            continue

        hits.append(hit)
        reason = (f"outside the circle of competence ({config.ruling}): "
                  f"{hit.limb} {hit.detail!r}" if hit.limb != "owner list"
                  else f"outside the circle of competence ({config.ruling}): "
                       f"named by the owner")
        # Rejected ON A VALUE -- a ruling about what the company is, dated
        # and recorded, exactly as the exclusion list's rows are.
        tally.reject(ON_VALUE, f"{config.label} ({hit.limb})")
        rejections.append(
            Rejection(instrument.key, config.step, ON_VALUE, reason)
        )

    tally.count_out = len(kept)
    hits.sort(key=lambda h: h.ticker)
    exempted.sort(key=lambda h: h.ticker)
    return CircleOutcome(
        kept=kept, rejections=rejections, tally=tally, hits=hits,
        unmatched=sorted(config.tickers - matched), exempted=exempted,
        without_string=without_string,
    )


# --- filter 1: prices (the band went in E161) -----------------------------


@dataclass(frozen=True)
class Candidate:
    """One survivor of filter 1, with its measurements as of the run date.

    ``rsi14``, ``sma50``, ``sma200`` and the two distances are FIELDS. They
    are carried so the owner can see them; nothing decided whether this row
    exists.
    """

    ticker: str
    marknad: str
    namn: str | None
    last_close: float
    last_close_date: date
    high_52w: float
    drawdown: float
    b1: float | None
    rsi14: float | None
    sma50: float | None
    sma200: float | None
    pct_vs_sma50: float | None
    pct_vs_sma200: float | None
    volume_ratio: float | None
    #: The session the 52-week closing high was set on (E11/E12): the
    #: reference peak a written PIPELINE entry freezes beside its drawdown.
    high_52w_date: date | None = None
    #: E63: the 52-week closing LOW, its session, and how far the close sits
    #: above it -- (close - low) / low. The drawdown cannot tell a name that
    #: fell and stayed down from one that has since recovered; this can.
    #: FIELDS, under the same standing rule as RSI and the SMAs: carried,
    #: printed, and read by no filter and by nothing in the ranking key.
    #: DATA MISSING together below the coverage bar, never a partial reading.
    low_52w: float | None = None
    low_52w_date: date | None = None
    pct_above_52w_low: float | None = None
    #: E127: the close a year ago, its session, and the return since. Every
    #: candidate carries a NEGATIVE return -- filter 1 removed the rest.
    close_year_ago: float | None = None
    close_year_ago_date: date | None = None
    return_12m: float | None = None


@dataclass
class Filter1Result:
    candidates: list[Candidate]
    rejections: list[Rejection]
    tallies: list[Tally]
    #: Every series the sanity check refused, with the finding that refused
    #: it. Reported by name: a count alone would let a growing data problem
    #: hide inside a column (K4).
    unmeasurable: list[tuple[str, object]] = field(default_factory=list)
    #: Markets whose staleness gate was counted on the NAIVE Monday-to-Friday
    #: calendar because no exchange calendar answered for them, with the
    #: number of names each. Named in the report, never silent (E47).
    naive_calendar: dict[str, int] = field(default_factory=dict)


def b1_metric(frame: pd.DataFrame, metrics: Metrics, as_of: date) -> float | None:
    """FRAMEWORK-EDITS B1, reported as CONTEXT and never as a pass/fail limb.

    ``(close_180d_ago - last_close) / (high_52w - last_close)`` -- how much of
    the peak-to-current decline happened in the trailing 180 days. Per B1 as
    decided 2026-08-22, Gate 1 measures today's position and this number does
    not by itself fail it.

    ``None`` when there is no close old enough to compare against, or when the
    close IS the 52-week high and there is no decline to attribute.
    """
    if metrics.last_close is None or metrics.high_52w is None:
        return None
    decline = metrics.high_52w - metrics.last_close
    if decline <= 0:
        return None
    cutoff = as_of - timedelta(days=B1_WINDOW_DAYS)
    prior = [
        float(close)
        for close, day in zip(frame["Close"].to_numpy(), index_dates(frame.index))
        if day <= cutoff and pd.notna(close)
    ]
    if not prior:
        return None
    return (prior[-1] - metrics.last_close) / decline


def run_filter1(
    instruments: Sequence[Instrument],
    frames: Mapping[str, pd.DataFrame],
    as_of: date,
    settled: date | None = None,
    holidays_for=None,
) -> Filter1Result:
    """Filter 1, against price frames read back from a snapshot.

    ``holidays_for(market, start, end)`` supplies the exchange's closed
    weekdays in ``(start, end]`` for the staleness gate (E47: three trading
    days ON THE EXCHANGE CALENDAR), or None where it cannot -- then the
    gate counts Monday to Friday for that name and the market is named in
    ``naive_calendar``. `vss/calendars.py` is the supply; this function
    does no I/O of its own.

    Takes instruments and frames and NOTHING else -- in particular it does
    not know the exclusion list exists, so it can be tested on a name that
    step 0 would have removed.

    ``compute`` truncates to ``as_of``, so a replay of an old date is priced
    at that date rather than at the snapshot's edge.

    ``settled`` is the newest date whose bar may be read as a SETTLED close
    (`metrics.settled_through`, struck from the clock the snapshot was
    taken by). A bar after it is a live print and is demoted, exactly as
    `vss run` demotes it for the watchlist. Until 2026-08-26 the screener
    passed nothing here: a `--snapshot-only` made at 11:19 CEST stored a
    live print as the close of the run date for 864 of 1,370 names, and the
    15% edge of the band -- the one threshold that removes names -- was
    decided on it (SCREENER-REVIEW-3 Part 1.2: 26 verdicts flipped between
    that snapshot and the settled one, 23 across the 15% edge; 57 names sat
    within a point of the edge). None means no cutoff was declared and the
    result says so on every metric (`last_close_settled` is None).
    """
    coverage = Tally(STEP_PRICE_COVERAGE, count_in=len(instruments))
    listing_age = Tally(STEP_LISTING_AGE)
    sanity = Tally(STEP_SERIES_SANITY)
    high = Tally(STEP_HIGH_52W)
    year = Tally(STEP_TRAILING_YEAR)
    rejections: list[Rejection] = []
    candidates: list[Candidate] = []
    measured: list[tuple[Instrument, pd.DataFrame, Metrics]] = []
    unmeasurable: list[tuple[str, object]] = []
    naive_calendar: dict[str, int] = {}

    for instrument in instruments:
        ticker = instrument.ticker_yahoo or ""
        frame = frames.get(ticker)
        if frame is None or len(frame) == 0:
            coverage.reject(ON_MISSING, "no price series in the snapshot")
            rejections.append(
                Rejection(instrument.key, STEP_PRICE_COVERAGE, ON_MISSING,
                          "no price series in the snapshot")
            )
            continue
        metrics = compute(frame, as_of, settled)
        if metrics.last_close is None or metrics.last_close_date is None:
            coverage.reject(ON_MISSING, f"no close at or before {as_of.isoformat()}")
            rejections.append(
                Rejection(instrument.key, STEP_PRICE_COVERAGE, ON_MISSING,
                          f"no close at or before {as_of.isoformat()}")
            )
            continue
        holidays = None
        if holidays_for is not None:
            holidays = holidays_for(instrument.marknad, metrics.last_close_date, as_of)
        if holidays is None:
            # No calendar answered: the naive count, and the market is NAMED.
            naive_calendar[instrument.marknad] = naive_calendar.get(instrument.marknad, 0) + 1
            holidays = frozenset()
        stale = stale_close_blocker(metrics.last_close_date, as_of, holidays=holidays)
        if stale is not None:
            # A close we HAVE, judged too old: a value rejection, not a
            # missing one. Same gate `vss run` applies to the watchlist.
            coverage.reject(ON_VALUE, "newest close older than the staleness gate")
            rejections.append(
                Rejection(instrument.key, STEP_PRICE_COVERAGE, ON_VALUE, str(stale))
            )
            continue
        measured.append((instrument, frame, metrics))

    coverage.count_out = len(measured)

    # --- E52: has this listing existed long enough to be judged?
    #
    # Ruled by the owner 2026-08-27. Five years, measured on the oldest bar
    # the STORED SERIES carries -- never on the universe CSV's `listdatum`,
    # which is empty on most rows and would reject the whole universe on a
    # field the vendor does not fill. The rejection is ON MISSING DATA: the
    # name did not fail a limb, there was not enough history to evaluate one.
    #
    # THIS RUNS BEFORE THE SANITY CHECK AND BEFORE THE BAND, and the order
    # is the point. Five years is strictly longer than the 52-weeks-plus-
    # five-trading-days coverage bar (`metrics.coverage_start`), so every
    # name that would have failed the band's `covers_52_weeks` branch below
    # is removed here first, at its own step, with its own count. That
    # branch is now unreachable from the screener and is KEPT anyway --
    # reachability is a property of E52's constant, not of the code.
    listing_age.count_in = len(measured)
    old_enough: list[tuple[Instrument, pd.DataFrame, Metrics]] = []
    age_floor = listing_age_start(as_of)
    for instrument, frame, metrics in measured:
        if covers_listing_age(metrics.first_bar_date, as_of):
            old_enough.append((instrument, frame, metrics))
            continue
        first = (metrics.first_bar_date.isoformat()
                 if metrics.first_bar_date else "no bars")
        why = (f"price history reaches back only to {first}, short of the "
               f"{LISTING_AGE_YEARS}-year floor at {age_floor.isoformat()} (E52)")
        listing_age.reject(ON_MISSING, f"listing younger than {LISTING_AGE_YEARS} years")
        rejections.append(
            Rejection(instrument.key, STEP_LISTING_AGE, ON_MISSING, why)
        )
    listing_age.count_out = len(old_enough)
    measured = old_enough

    # --- K4: can this series be measured at all?
    #
    # A series that alternates between two scales, or that carries a break the
    # tape does not corroborate, yields a NUMBER where the answer is "we do not
    # know". MNST's stored series produced a 52.2% drawdown against a true
    # figure near -4%. The rejection is ON MISSING DATA, never on value: the
    # name did not fail the band, the band could not be evaluated for it.
    sanity.count_in = len(measured)
    usable: list[tuple[Instrument, pd.DataFrame, Metrics]] = []
    for instrument, frame, metrics in measured:
        finding = series_check(frame, as_of)
        if finding is not None:
            unmeasurable.append((instrument.ticker_yahoo or "", finding))
            sanity.reject(ON_MISSING, f"price series not measurable ({finding.kind})")
            rejections.append(
                Rejection(instrument.key, STEP_SERIES_SANITY, ON_MISSING,
                          f"{finding.kind}: {finding.detail}")
            )
            continue
        usable.append((instrument, frame, metrics))
    sanity.count_out = len(usable)

    high.count_in = len(usable)
    measurable: list[tuple[Instrument, pd.DataFrame, Metrics]] = []

    for instrument, frame, metrics in usable:
        if metrics.drawdown is None:
            # A short series or a non-positive high: MISSING DATA, never a
            # value rejection (REVIEW-4 report B 7.2).
            why = ("series does not cover 52 weeks"
                   if metrics.covers_52_weeks is False
                   else "no 52-week high")
            high.reject(ON_MISSING, f"drawdown not computable ({why})")
            rejections.append(
                Rejection(instrument.key, STEP_HIGH_52W, ON_MISSING,
                          f"drawdown not computable ({why})")
            )
            continue
        measurable.append((instrument, frame, metrics))
    high.count_out = len(measurable)

    # --- E127 REMOVED by E168 (attempt #25, 2026-11-09): "below its close of a
    # year ago" did not separate returns (Nordic -14.1 pp at 3 years). The
    # 12-month return is still carried as a field; it rejects nothing. The
    # step stays in the tally so the yield table keeps its shape.
    year.count_in = len(measurable)
    for instrument, frame, metrics in measurable:
        candidates.append(
            Candidate(
                ticker=instrument.ticker_yahoo or "",
                marknad=instrument.marknad,
                namn=instrument.namn,
                last_close=metrics.last_close,
                last_close_date=metrics.last_close_date,
                high_52w=metrics.high_52w,       # type: ignore[arg-type]
                drawdown=metrics.drawdown,       # type: ignore[arg-type]
                b1=b1_metric(frame, metrics, as_of),
                rsi14=metrics.rsi14,
                sma50=metrics.sma50,
                sma200=metrics.sma200,
                pct_vs_sma50=metrics.pct_vs_sma50,
                pct_vs_sma200=metrics.pct_vs_sma200,
                volume_ratio=metrics.volume_ratio,
                high_52w_date=metrics.high_52w_date,
                low_52w=metrics.low_52w,
                low_52w_date=metrics.low_52w_date,
                pct_above_52w_low=metrics.pct_above_52w_low,
                close_year_ago=metrics.close_year_ago,
                close_year_ago_date=metrics.close_year_ago_date,
                return_12m=metrics.return_12m,
            )
        )

    year.count_out = len(candidates)
    # Ordered by ticker. This is an ORDER, not a ranking: the ranking key is
    # phase 5, it is proposed as text and approved before it is coded, and
    # nothing here may stand in for it.
    candidates.sort(key=lambda c: c.ticker)
    return Filter1Result(candidates=candidates, rejections=rejections,
                         tallies=[coverage, listing_age, sanity, high, year],
                         unmeasurable=unmeasurable, naive_calendar=naive_calendar)


# --- filter 2: coarse quality ---------------------------------------------
#
# The MECHANISM is here. The VALUES are in config/screener_filter2.yaml,
# marked PROPOSED until the owner decides them, each carrying the FRAMEWORK
# section it came from. Nothing in this module hardcodes a threshold, and a
# test asserts it: change 2.5 to 3.5 in the config and no code recompiles.

FILTER2_CONFIG_PATH = Path("config/screener_filter2.yaml")
#: E46: the owner-maintained list of investment companies, exempt on the
#: leverage limb here and on the quality leg in the ranking. The LIST
#: decides, never the vendor's sector string.
INVESTMENT_COMPANIES_PATH = Path("config/screener_investment_companies.yaml")

STEP_FILTER2 = "filter2"

PASS = "PASS"
FAIL = "FAIL"
DATA_MISSING = "DATA MISSING"
NOT_APPLICABLE = "NOT APPLICABLE"
FLAG = "FLAG"

LIMB_FCF = "free_cash_flow"


class Filter2Error(UniverseError):
    """The filter 2 config is malformed or has not been decided."""


@dataclass(frozen=True)
class Filter2Config:
    status: str
    proposed: str | None
    fcf_min: float
    on_missing_action: str
    raw: Mapping
    #: E46: the owner's investment companies (read by the ranking's quality
    #: leg since E168 removed the leverage limb). From INVESTMENT_COMPANIES_PATH.
    investment_companies: frozenset[str] = frozenset()

    @property
    def decided(self) -> bool:
        return str(self.status).upper() == "DECIDED"


def load_investment_companies(path: Path = INVESTMENT_COMPANIES_PATH) -> frozenset[str]:
    """The owner's list of investment companies (E46), by ticker_yahoo.

    A missing file is an error, not an empty list: the exemption is a
    decision, and a run that silently ranked Latour because the file was
    not there would be the string exemption's failure all over again.
    """
    import yaml

    if not path.exists():
        raise Filter2Error(f"{path}: no investment-company list (E46)")
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = document.get("investment_companies")
    if not isinstance(rows, list):
        raise Filter2Error(f"{path.name}: 'investment_companies' must be a list of rows")
    tickers: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping) or not str(row.get("ticker", "")).strip():
            raise Filter2Error(f"{path.name}: every row needs a ticker: {row!r}")
        if not str(row.get("company", "")).strip():
            raise Filter2Error(f"{path.name}: {row['ticker']}: every row names its company")
        ticker = str(row["ticker"]).strip()
        if ticker in tickers:
            raise Filter2Error(f"{path.name}: {ticker} is listed twice")
        tickers.add(ticker)
    return frozenset(tickers)


def load_filter2_config(path: Path = FILTER2_CONFIG_PATH,
                        investment_companies_path: Path | None = INVESTMENT_COMPANIES_PATH,
                        ) -> Filter2Config:
    import yaml

    if not path.exists():
        raise Filter2Error(f"{path}: no filter 2 config")
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    limbs = document.get("limbs") or {}
    if LIMB_FCF not in limbs:
        raise Filter2Error(f"{path.name}: limb {LIMB_FCF!r} is missing")
    action = str(document.get("on_missing_action", "pass_through")).lower()
    if action not in ("pass_through", "reject"):
        raise Filter2Error(
            f"{path.name}: on_missing_action must be 'pass_through' or 'reject'"
        )

    return Filter2Config(
        status=str(document.get("status", "PROPOSED")),
        proposed=str(document.get("proposed")) if document.get("proposed") else None,
        fcf_min=float(limbs[LIMB_FCF].get("min", 0.0)),
        on_missing_action=action,
        raw=document,
        investment_companies=(load_investment_companies(investment_companies_path)
                              if investment_companies_path is not None else frozenset()),
    )


@dataclass(frozen=True)
class Limb:
    name: str
    state: str
    detail: str


@dataclass(frozen=True)
class Assessed:
    ticker: str
    limbs: tuple[Limb, ...]

    def state(self, name: str) -> str:
        for limb in self.limbs:
            if limb.name == name:
                return limb.state
        return DATA_MISSING

    @property
    def failed(self) -> tuple[Limb, ...]:
        return tuple(limb for limb in self.limbs if limb.state == FAIL)

    @property
    def untested(self) -> tuple[Limb, ...]:
        return tuple(limb for limb in self.limbs if limb.state == DATA_MISSING)


@dataclass
class Filter2Result:
    survivors: list
    assessed: dict[str, Assessed]
    rejections: list[Rejection]
    tally: Tally
    config: Filter2Config
    #: Candidates with no record in the fundamentals store. Zero when the
    #: store was built from this same survivor set; non-zero the moment the
    #: universe or the exclusion list changed after the fetch, which is
    #: precisely when it must not pass unnoticed.
    not_fetched: list[str] = field(default_factory=list)
    #: How many tickers the store holds, whether or not filter 1 kept them.
    store_size: int = 0


#: Said when a ticker has no record in the store at all. Distinct from "the
#: company reported no such figure", which is a fact about the company. This
#: one is a fact about the FETCH, and collapsing the two would hide a
#: survivor set that has drifted out of step with the store -- the same
#: distinction prices.py keeps between NO_DATA and THROTTLED.
NOT_FETCHED = "no fundamentals record for this ticker: it was not in the fetch"


def fcf_limb(record, config: Filter2Config) -> Limb:
    if record is None:
        return Limb(LIMB_FCF, DATA_MISSING, NOT_FETCHED)
    value = record.value("freeCashflow")
    if value is None:
        return Limb(LIMB_FCF, DATA_MISSING, "no trailing free cash flow reported")
    if value > config.fcf_min:
        return Limb(LIMB_FCF, PASS, f"TTM free cash flow {value:,.0f}")
    return Limb(LIMB_FCF, FAIL, f"TTM free cash flow {value:,.0f}")


#: E168 (attempt #25, 2026-11-09): the leverage limb (net debt / EBITDA <=
#: 2.5x) is removed -- it did not separate returns in both markets and both
#: halves. The FCF limb stays (not testable: every valued name has a
#: positive flow).


def run_filter2(
    candidates: Sequence,
    fundamentals: Mapping,
    config: Filter2Config,
) -> Filter2Result:
    """Filter 2 over the survivors of filter 1.

    Rejections stay split. A limb that FAILED is a value rejection. A limb
    with no data is DATA MISSING -- a name that could not be tested has not
    failed, so by default it passes through marked, and the count is
    reported separately either way.
    """
    tally = Tally(STEP_FILTER2, count_in=len(candidates))
    survivors, rejections = [], []
    assessed: dict[str, Assessed] = {}

    for candidate in candidates:
        record = fundamentals.get(candidate.ticker)
        limbs = (fcf_limb(record, config),)
        verdict = Assessed(candidate.ticker, limbs)
        assessed[candidate.ticker] = verdict

        failed = verdict.failed
        if failed:
            reason = "; ".join(f"{limb.name} {limb.detail}" for limb in failed)
            tally.reject(ON_VALUE, ", ".join(limb.name for limb in failed))
            rejections.append(Rejection(candidate.ticker, STEP_FILTER2, ON_VALUE, reason))
            continue
        untested = verdict.untested
        if untested and config.on_missing_action == "reject":
            tally.reject(ON_MISSING, ", ".join(limb.name for limb in untested))
            rejections.append(
                Rejection(candidate.ticker, STEP_FILTER2, ON_MISSING,
                          "; ".join(f"{l.name}: {l.detail}" for l in untested))
            )
            continue
        survivors.append(candidate)

    tally.count_out = len(survivors)
    return Filter2Result(
        survivors=survivors, assessed=assessed, rejections=rejections,
        tally=tally, config=config,
        not_fetched=[c.ticker for c in candidates if c.ticker not in fundamentals],
        store_size=len(fundamentals),
    )


def limb_matrix(assessed: Mapping[str, Assessed]) -> dict[str, dict[str, int]]:
    """Per limb: how many PASS, FAIL, DATA MISSING, NOT APPLICABLE, FLAG."""
    states = (PASS, FAIL, DATA_MISSING, NOT_APPLICABLE, FLAG)
    table = {name: {state: 0 for state in states}
             for name in (LIMB_FCF,)}
    for verdict in assessed.values():
        for limb in verdict.limbs:
            table[limb.name][limb.state] = table[limb.name].get(limb.state, 0) + 1
    return table
