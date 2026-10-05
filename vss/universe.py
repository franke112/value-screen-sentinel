"""The screening universe: loading, validating and reducing the source lists.

The universe is a set of STATIC, dated CSVs under ``config/universe/``. Index
membership is never fetched at runtime -- ``tools/build_universe.py`` writes
the files, they are committed, and this module only reads them.

Three rules shape everything here.

1. A broken row is a HARD ERROR, never a silent skip. A quietly dropped
   ticker is invisible; a crash is not. This mirrors ``config.py``, where a
   malformed watchlist entry fails the whole run.

2. DATA MISSING is a THIRD STATE. A row rejected because a value said so and
   a row rejected because the value was absent are counted in different
   columns and never added together. "0 excluded" and "0 evaluated" are
   different facts and the report says which one it is.

3. Instrument type comes from the SOURCE LIST, never from the name string.
   "iShares Core MSCI Europe" is a fund and "Rio Tinto" is not, but nothing
   in this module tries to tell them apart by reading their names. If the
   source list has no type for a row, the row is UNKNOWN -- a third state
   with its own count and its own configurable policy.

This module performs no network I/O and no clock reads: ``as_of`` is passed
in wherever it is needed.
"""

from __future__ import annotations

import csv
import re
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import yaml

#: The committed CSV header, exactly, in order. A file whose header differs
#: -- extra column, missing column, reordered, renamed -- is rejected before
#: a single row is read.
SCHEMA: tuple[str, ...] = (
    "ticker_yahoo",
    "ticker_lokal",
    "isin",
    "namn",
    "marknad",
    "tier",
    "listdatum",
    "valuta",
    "instrumenttyp",
)

VALID_TIERS = ("A", "B", "C")

#: Columns that may be empty, meaning DATA MISSING. Everything else is
#: required and an empty value is a broken row.
#:
#: ``ticker_yahoo`` is optional on purpose: a constituent whose Yahoo symbol
#: could not be resolved is still a real constituent. Dropping it at build
#: time would hide a mapping bug; keeping it with an empty symbol makes the
#: gap countable, which is what ``--universe-report`` reports.
#:
#: ``namn`` is optional too, and deliberately so: nothing in this system is
#: allowed to decide anything from a name string, so a missing name costs no
#: decision. It is DATA MISSING, counted, and otherwise harmless.
OPTIONAL_COLUMNS = frozenset(
    {"ticker_yahoo", "isin", "namn", "listdatum", "valuta", "instrumenttyp"}
)

#: Rejection kinds. They are counted separately and never summed.
ON_VALUE = "value"
ON_MISSING = "missing"

#: Instrument-type classifications.
INCLUDE = "INCLUDE"
EXCLUDE = "EXCLUDE"
UNKNOWN = "UNKNOWN"


class UniverseError(Exception):
    """A universe file is malformed. Always fatal -- never caught and skipped."""


# --- value objects ---------------------------------------------------------


@dataclass(frozen=True)
class Instrument:
    ticker_yahoo: str | None
    ticker_lokal: str
    isin: str | None
    namn: str | None
    marknad: str
    tier: str
    listdatum: date | None
    valuta: str | None
    instrumenttyp: str | None
    source_file: str = ""
    source_line: int = 0

    @property
    def key(self) -> str:
        """Stable identity for reporting: the Yahoo symbol when we have one."""
        return self.ticker_yahoo or f"{self.marknad}:{self.ticker_lokal}"


@dataclass(frozen=True)
class Rejection:
    key: str
    step: str
    kind: str          # ON_VALUE or ON_MISSING
    reason: str


@dataclass(frozen=True)
class Merge:
    kept: str
    dropped: str
    on: str            # "ticker_yahoo" or "isin"
    basis: str         # how the winner was chosen
    detail: str = ""
    #: Which source file each side came from. On the ticker layer the two
    #: symbols are identical -- it is one listing named twice -- so without
    #: these the stored row would say kept == dropped and carry no way to
    #: tell which file won.
    kept_source: str = ""
    dropped_source: str = ""


@dataclass
class Tally:
    """One step of the yield report.

    ``rejected_on_value`` and ``rejected_on_missing`` are deliberately two
    fields. Collapsing them into one "rejected" number is the exact mistake
    this structure exists to prevent.
    """

    step: str
    count_in: int = 0
    count_out: int = 0
    rejected_on_value: int = 0
    rejected_on_missing: int = 0
    reasons: Counter = field(default_factory=Counter)

    @property
    def rejected(self) -> int:
        return self.rejected_on_value + self.rejected_on_missing

    def reject(self, kind: str, reason: str) -> None:
        if kind == ON_VALUE:
            self.rejected_on_value += 1
        elif kind == ON_MISSING:
            self.rejected_on_missing += 1
        else:  # pragma: no cover - programming error
            raise ValueError(f"unknown rejection kind: {kind}")
        self.reasons[f"{kind}:{reason}"] += 1


@dataclass(frozen=True)
class TypeRules:
    """Instrument-type policy, loaded from config -- never hardcoded."""

    include: Mapping[str, str]          # normalised type -> canonical label
    exclude: Mapping[str, str]          # normalised type -> exclusion reason
    unknown_action: str                 # "keep" or "exclude"
    #: TICKER rules (item 4, SCREENER-REVIEW-3 Part 14.3): a listing the
    #: source types as an equity but whose TICKER the owner has classified
    #: -- the six German preference lines the STOXX file types `Equity`, and
    #: the Stockholm `-PREF` and `-D` lines Yahoo types `EQUITY`. Exact
    #: tickers and compiled patterns, each with the exclusion reason. The
    #: NAME string is still never read: a ticker is the source list's own
    #: identifier for the line, not prose about it.
    exclude_tickers: Mapping[str, str] = field(default_factory=dict)
    exclude_ticker_patterns: tuple[tuple[re.Pattern, str], ...] = ()

    def classify(self, instrumenttyp: str | None,
                 ticker_yahoo: str | None = None) -> tuple[str, str]:
        """(state, reason). State is INCLUDE, EXCLUDE or UNKNOWN.

        Matching is on the source list's own type string, case- and
        whitespace-insensitive, then on the TICKER against the owner's list
        and patterns. Nothing is inferred from ``namn``. A type exclusion
        wins over a ticker rule; a ticker rule wins over an included or
        unknown type.
        """
        if instrumenttyp is None or not instrumenttyp.strip():
            state, reason = UNKNOWN, "no instrument type in the source list"
        else:
            norm = normalise_type(instrumenttyp)
            if norm in self.exclude:
                return EXCLUDE, self.exclude[norm]
            if norm in self.include:
                state, reason = INCLUDE, self.include[norm]
            else:
                state, reason = UNKNOWN, f"instrument type {instrumenttyp!r} is not in the config"
        ticker = (ticker_yahoo or "").strip()
        if ticker:
            if ticker in self.exclude_tickers:
                return EXCLUDE, self.exclude_tickers[ticker]
            for pattern, why in self.exclude_ticker_patterns:
                if pattern.search(ticker):
                    return EXCLUDE, why
        return state, reason


@dataclass(frozen=True)
class Floors:
    """Per-tier floors. Every threshold carries its own currency.

    The currency is part of the threshold because the universe spans some
    fifteen quoting currencies: "market cap > 300 000 000" is not a rule
    until it says 300 million of WHAT. Phase 3 will need an FX source to
    apply these; phase 1 only loads and reports them.
    """

    raw: Mapping[str, Mapping]

    def for_tier(self, tier: str) -> Mapping:
        return dict(self.raw.get(tier, {}) or {})


@dataclass(frozen=True)
class SourceFile:
    path: Path
    rows: int
    tier_counts: Mapping[str, int]
    sha256: str
    meta: Mapping | None
    meta_sha_matches: bool | None


@dataclass
class UniverseLoad:
    instruments: list[Instrument]
    tallies: list[Tally]
    rejections: list[Rejection]
    merges: list[Merge]
    files: list[SourceFile]
    unknown_type_kept: list[str] = field(default_factory=list)
    dual_listing_candidates: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)

    @property
    def by_market(self) -> Counter:
        return Counter(inst.marknad for inst in self.instruments)


# --- parsing ---------------------------------------------------------------


def normalise_type(value: str) -> str:
    return " ".join(value.strip().lower().split())


ISIN_LENGTH = 12


def isin_check_digit_ok(isin: str) -> bool:
    """Luhn check over the letter-expanded ISIN body."""
    digits = ""
    for char in isin[:-1]:
        digits += str(ord(char) - 55) if char.isalpha() else char
    total, double = 0, True
    for char in reversed(digits):
        value = int(char)
        if double:
            value *= 2
            if value > 9:
                value -= 9
        total += value
        double = not double
    return (10 - total % 10) % 10 == int(isin[-1])


def _bad(path: Path, line: int, message: str) -> UniverseError:
    return UniverseError(f"{path.name}:{line}: {message}")


def parse_row(raw: Mapping[str, str], path: Path, line: int) -> Instrument:
    """One CSV row to an Instrument. Anything malformed raises."""
    values = {}
    for column in SCHEMA:
        value = raw.get(column)
        if value is None:
            raise _bad(path, line, f"column {column!r} is missing from the row")
        value = value.strip()
        if not value and column not in OPTIONAL_COLUMNS:
            raise _bad(path, line, f"column {column!r} is empty and is required")
        values[column] = value

    tier = values["tier"].upper()
    if tier not in VALID_TIERS:
        raise _bad(path, line, f"tier {values['tier']!r} is not one of {VALID_TIERS}")

    isin = values["isin"].upper() or None
    if isin is not None:
        if len(isin) != ISIN_LENGTH or not isin[:2].isalpha() or not isin.isalnum():
            raise _bad(path, line, f"isin {isin!r} is not a 12-character ISIN")
        if not isin[-1].isdigit() or not isin_check_digit_ok(isin):
            raise _bad(path, line, f"isin {isin!r} fails its check digit")

    listdatum: date | None = None
    if values["listdatum"]:
        try:
            listdatum = date.fromisoformat(values["listdatum"])
        except ValueError as exc:
            raise _bad(path, line, f"listdatum {values['listdatum']!r}: {exc}") from exc

    valuta = values["valuta"].upper() or None
    if valuta is not None and not (len(valuta) == 3 and valuta.isalpha()):
        raise _bad(path, line, f"valuta {values['valuta']!r} is not a 3-letter code")

    ticker_yahoo = values["ticker_yahoo"] or None
    if ticker_yahoo is not None and any(c.isspace() for c in ticker_yahoo):
        raise _bad(path, line, f"ticker_yahoo {ticker_yahoo!r} contains whitespace")

    return Instrument(
        ticker_yahoo=ticker_yahoo,
        ticker_lokal=values["ticker_lokal"],
        isin=isin,
        namn=values["namn"] or None,
        marknad=values["marknad"],
        tier=tier,
        listdatum=listdatum,
        valuta=valuta,
        instrumenttyp=values["instrumenttyp"] or None,
        source_file=path.name,
        source_line=line,
    )


def read_list(path: Path) -> list[Instrument]:
    """Read one universe CSV. A malformed header or row aborts the run."""
    if not path.exists():
        raise UniverseError(f"{path}: no such universe file")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise UniverseError(f"{path.name}: file is empty, not even a header") from exc
        header = [h.strip().lstrip("﻿") for h in header]
        if tuple(header) != SCHEMA:
            raise UniverseError(
                f"{path.name}: header is {header}, expected {list(SCHEMA)}"
            )
        instruments = []
        for line, row in enumerate(reader, start=2):
            if not row or all(not cell.strip() for cell in row):
                raise _bad(path, line, "blank row (a blank row is a broken row)")
            if len(row) != len(SCHEMA):
                raise _bad(
                    path, line,
                    f"has {len(row)} fields, expected {len(SCHEMA)}",
                )
            instruments.append(parse_row(dict(zip(SCHEMA, row)), path, line))
    return instruments


def read_meta(csv_path: Path) -> Mapping | None:
    meta_path = csv_path.with_suffix("").with_suffix(".meta.json")
    if meta_path.name == csv_path.name:  # pragma: no cover - defensive
        return None
    meta_path = csv_path.parent / (csv_path.stem + ".meta.json")
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise UniverseError(f"{meta_path.name}: unreadable metadata ({exc})") from exc


# --- config ----------------------------------------------------------------


def load_type_rules(path: Path) -> TypeRules:
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    include_raw = document.get("include") or {}
    exclude_raw = document.get("exclude") or {}
    if not isinstance(include_raw, Mapping) or not isinstance(exclude_raw, Mapping):
        raise UniverseError(f"{path.name}: include and exclude must be mappings")

    include: dict[str, str] = {}
    for label, values in include_raw.items():
        for value in values or []:
            include[normalise_type(str(value))] = str(label)
    exclude: dict[str, str] = {}
    for reason, values in exclude_raw.items():
        for value in values or []:
            key = normalise_type(str(value))
            if key in include:
                raise UniverseError(
                    f"{path.name}: instrument type {value!r} is both included and excluded"
                )
            exclude[key] = str(reason)

    action = str(document.get("unknown_action", "keep")).lower()
    if action not in ("keep", "exclude"):
        raise UniverseError(f"{path.name}: unknown_action must be 'keep' or 'exclude'")

    # Ticker rules (item 4). Each reason names the tickers and the patterns
    # it covers; a pattern that does not compile is a config error.
    ticker_raw = document.get("exclude_tickers") or {}
    if not isinstance(ticker_raw, Mapping):
        raise UniverseError(f"{path.name}: exclude_tickers must be a mapping of reason -> rules")
    exclude_tickers: dict[str, str] = {}
    patterns: list[tuple[re.Pattern, str]] = []
    for reason, spec in ticker_raw.items():
        spec = spec or {}
        if not isinstance(spec, Mapping):
            raise UniverseError(
                f"{path.name}: exclude_tickers.{reason} must carry 'tickers' and/or 'patterns'"
            )
        for ticker in spec.get("tickers") or []:
            key = str(ticker).strip()
            if key in exclude_tickers and exclude_tickers[key] != str(reason):
                raise UniverseError(
                    f"{path.name}: ticker {key} is excluded under two reasons"
                )
            exclude_tickers[key] = str(reason)
        for pattern in spec.get("patterns") or []:
            try:
                patterns.append((re.compile(str(pattern)), str(reason)))
            except re.error as exc:
                raise UniverseError(
                    f"{path.name}: exclude_tickers.{reason} pattern {pattern!r}: {exc}"
                ) from exc
    return TypeRules(include=include, exclude=exclude, unknown_action=action,
                     exclude_tickers=exclude_tickers,
                     exclude_ticker_patterns=tuple(patterns))


def load_floors(path: Path) -> Floors:
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tiers = document.get("tiers") or {}
    if not isinstance(tiers, Mapping):
        raise UniverseError(f"{path.name}: 'tiers' must be a mapping")
    for tier, floors in tiers.items():
        if tier not in VALID_TIERS:
            raise UniverseError(f"{path.name}: unknown tier {tier!r}")
        for name, spec in (floors or {}).items():
            if not isinstance(spec, Mapping):
                continue
            if "min" in spec and "currency" not in spec and spec.get("unit") != "years":
                raise UniverseError(
                    f"{path.name}: floor {tier}.{name} has a threshold but no currency. "
                    "Across fifteen quoting currencies an unqualified amount is not a rule."
                )
    return Floors(raw=tiers)


# --- reduction -------------------------------------------------------------


def apply_type_exclusions(
    instruments: Sequence[Instrument], rules: TypeRules
) -> tuple[list[Instrument], list[Rejection], list[str], Tally]:
    """Drop instruments the SOURCE LIST types as something we do not screen."""
    tally = Tally("instrument_type", count_in=len(instruments))
    kept: list[Instrument] = []
    rejections: list[Rejection] = []
    unknown_kept: list[str] = []

    for inst in instruments:
        state, reason = rules.classify(inst.instrumenttyp, inst.ticker_yahoo)
        if state == EXCLUDE:
            tally.reject(ON_VALUE, reason)
            rejections.append(Rejection(inst.key, tally.step, ON_VALUE, reason))
            continue
        if state == UNKNOWN:
            if rules.unknown_action == "exclude":
                tally.reject(ON_MISSING, reason)
                rejections.append(Rejection(inst.key, tally.step, ON_MISSING, reason))
                continue
            # Kept, but never silently: an unknown type is DATA MISSING and
            # gets its own line in the report. Excluding it by default would
            # be guessing that it is a fund.
            unknown_kept.append(inst.key)
        kept.append(inst)

    tally.count_out = len(kept)
    return kept, rejections, unknown_kept, tally


def require_yahoo_mapping(
    instruments: Sequence[Instrument],
) -> tuple[list[Instrument], list[Rejection], Tally]:
    """Split off constituents we cannot price because we have no symbol."""
    tally = Tally("yahoo_mapping", count_in=len(instruments))
    kept, rejections = [], []
    for inst in instruments:
        if inst.ticker_yahoo:
            kept.append(inst)
            continue
        # Rejected for ABSENCE of a value, not on a value. The distinction is
        # the whole point of the split counters.
        tally.reject(ON_MISSING, "no yahoo symbol resolved for this constituent")
        rejections.append(
            Rejection(inst.key, tally.step, ON_MISSING, "no yahoo symbol")
        )
    tally.count_out = len(kept)
    return kept, rejections, tally


def dedupe(
    instruments: Sequence[Instrument],
    turnover: Mapping[str, float] | None = None,
) -> tuple[list[Instrument], list[Merge], Tally]:
    """Collapse dual listings.

    Two layers, because they answer different questions:

    * layer 1, ``ticker_yahoo``: the SAME listing appearing in two source
      lists (a Swedish STOXX 600 member is also an OMXS Large Cap member).
      There is nothing to choose between them -- they are one row.
    * layer 2, ``isin``: DIFFERENT listings of the same security (ABB.ST and
      ABBN.SW). Here a choice is required, and the rule is highest turnover
      wins. When turnover is unknown the winner is picked deterministically
      and the merge records that it was decided WITHOUT turnover data, so a
      report can never imply a liquidity judgement that was not made.
    """
    tally = Tally("dedup", count_in=len(instruments))
    merges: list[Merge] = []

    by_ticker: dict[str, Instrument] = {}
    ordered: list[str] = []
    for inst in instruments:
        assert inst.ticker_yahoo  # guaranteed by require_yahoo_mapping
        symbol = inst.ticker_yahoo
        if symbol in by_ticker:
            first = by_ticker[symbol]
            merges.append(
                Merge(
                    kept=symbol, dropped=symbol, on="ticker_yahoo",
                    basis="same listing in two source lists",
                    detail=f"{first.source_file} kept, {inst.source_file} folded in",
                    kept_source=first.source_file,
                    dropped_source=inst.source_file,
                )
            )
            tally.reject(ON_VALUE, "duplicate ticker_yahoo across source lists")
            continue
        by_ticker[symbol] = inst
        ordered.append(symbol)

    by_isin: dict[str, str] = {}
    dropped: set[str] = set()
    for symbol in ordered:
        inst = by_ticker[symbol]
        if not inst.isin:
            continue
        incumbent_symbol = by_isin.get(inst.isin)
        if incumbent_symbol is None:
            by_isin[inst.isin] = symbol
            continue
        winner, loser, basis, detail = _pick_listing(
            by_ticker[incumbent_symbol], inst, turnover
        )
        by_isin[inst.isin] = winner.ticker_yahoo  # type: ignore[assignment]
        dropped.add(loser.ticker_yahoo)  # type: ignore[arg-type]
        merges.append(
            Merge(kept=winner.ticker_yahoo, dropped=loser.ticker_yahoo,  # type: ignore[arg-type]
                  on="isin", basis=basis, detail=f"isin {inst.isin}: {detail}",
                  kept_source=winner.source_file, dropped_source=loser.source_file)
        )
        kind = ON_VALUE if turnover else ON_MISSING
        tally.reject(kind, f"dual listing of {inst.isin} ({basis})")

    kept = [by_ticker[s] for s in ordered if s not in dropped]
    tally.count_out = len(kept)
    return kept, merges, tally


def _pick_listing(
    a: Instrument, b: Instrument, turnover: Mapping[str, float] | None
) -> tuple[Instrument, Instrument, str, str]:
    left = (turnover or {}).get(a.ticker_yahoo or "")
    right = (turnover or {}).get(b.ticker_yahoo or "")
    if left is not None and right is not None:
        if right > left:
            return b, a, "highest turnover", f"{right:,.0f} beats {left:,.0f}"
        return a, b, "highest turnover", f"{left:,.0f} beats {right:,.0f}"
    # No turnover for at least one side. Pick deterministically and SAY that
    # liquidity was not what decided it.
    ordered = sorted((a, b), key=lambda i: (i.marknad, i.ticker_yahoo or ""))
    return (
        ordered[0], ordered[1],
        "no turnover data -- first by (marknad, ticker)",
        f"{ordered[0].ticker_yahoo} kept over {ordered[1].ticker_yahoo}",
    )


def dual_listing_candidates(
    instruments: Sequence[Instrument],
) -> list[tuple[str, tuple[str, ...]]]:
    """Same company name on two markets, with no ISIN to prove or disprove it.

    Reported, never merged. Merging on a name match would be exactly the
    name-string guessing the exclusion rule forbids; the point of this list
    is to show the user what ISIN coverage would resolve.
    """
    groups: dict[str, list[Instrument]] = defaultdict(list)
    for inst in instruments:
        if inst.isin or not inst.namn:
            continue
        groups[_name_key(inst.namn)].append(inst)
    out = []
    for name, rows in sorted(groups.items()):
        markets = {r.marknad for r in rows}
        if len(rows) > 1 and len(markets) > 1:
            out.append((name, tuple(sorted(r.ticker_yahoo or r.ticker_lokal for r in rows))))
    return out


#: Suffixes stripped before two names are compared. Dots are removed first,
#: so "N.V." arrives here as "nv" and "S.p.A." as "spa".
_NAME_NOISE = (
    " plc", " ag", " nv", " sa", " ab", " asa", " a/s", " oyj", " se", " spa",
    " inc", " corp", " corporation", " ltd", " limited", " group", " holding",
    " holdings", " company", " co", " publ", " class a", " class b", " reg",
)


def _name_key(name: str) -> str:
    key = " " + " ".join(
        name.lower().replace(",", " ").replace(".", "").replace("(", " ")
        .replace(")", " ").split()
    )
    changed = True
    while changed:
        changed = False
        for noise in _NAME_NOISE:
            if key.endswith(noise):
                key = key[: -len(noise)]
                changed = True
    return key.strip()


# --- composition -----------------------------------------------------------


def discover_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        raise UniverseError(f"{directory}: no such universe directory")
    return sorted(p for p in directory.glob("*.csv"))


def load_universe(
    directory: Path,
    *,
    tiers: Sequence[str] = ("A",),
    type_rules: TypeRules,
    turnover: Mapping[str, float] | None = None,
) -> UniverseLoad:
    """Read every CSV, keep the requested tiers, exclude, map, dedupe."""
    wanted = tuple(t.upper() for t in tiers)
    for tier in wanted:
        if tier not in VALID_TIERS:
            raise UniverseError(f"unknown tier {tier!r}; expected one of {VALID_TIERS}")

    files: list[SourceFile] = []
    everything: list[Instrument] = []
    for path in discover_files(directory):
        rows = read_list(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        meta = read_meta(path)
        recorded = (meta or {}).get("sha256")
        files.append(
            SourceFile(
                path=path,
                rows=len(rows),
                tier_counts=Counter(r.tier for r in rows),
                sha256=digest,
                meta=meta,
                meta_sha_matches=None if recorded is None else recorded == digest,
            )
        )
        everything.extend(rows)

    read_tally = Tally("read", count_in=len(everything), count_out=len(everything))

    tier_tally = Tally("tier_select", count_in=len(everything))
    selected, rejections = [], []
    for inst in everything:
        if inst.tier in wanted:
            selected.append(inst)
        else:
            tier_tally.reject(ON_VALUE, f"tier {inst.tier} not requested")
    tier_tally.count_out = len(selected)

    kept, type_rejections, unknown_kept, type_tally = apply_type_exclusions(
        selected, type_rules
    )
    rejections.extend(type_rejections)

    mapped, map_rejections, map_tally = require_yahoo_mapping(kept)
    rejections.extend(map_rejections)

    deduped, merges, dedup_tally = dedupe(mapped, turnover)

    return UniverseLoad(
        instruments=deduped,
        tallies=[read_tally, tier_tally, type_tally, map_tally, dedup_tally],
        rejections=rejections,
        merges=merges,
        files=files,
        unknown_type_kept=unknown_kept,
        dual_listing_candidates=dual_listing_candidates(deduped),
    )


# --- reporting -------------------------------------------------------------


def yield_table(tallies: Iterable[Tally]) -> str:
    """The exchange report. Mandatory in every screener output.

    Rejections are shown split, never summed into one column: a name lost
    because a value said no and a name lost because there was no value are
    different failures with different fixes.
    """
    header = (
        f"{'step':<18}{'in':>8}{'out':>8}{'rej(value)':>12}{'rej(missing)':>14}"
    )
    lines = [header, "-" * len(header)]
    for tally in tallies:
        lines.append(
            f"{tally.step:<18}{tally.count_in:>8}{tally.count_out:>8}"
            f"{tally.rejected_on_value:>12}{tally.rejected_on_missing:>14}"
        )
    return "\n".join(lines)


def reason_breakdown(tallies: Iterable[Tally]) -> str:
    lines = []
    for tally in tallies:
        if not tally.reasons:
            continue
        lines.append(f"  {tally.step}:")
        for reason, count in sorted(tally.reasons.items(), key=lambda kv: (-kv[1], kv[0])):
            kind, _, text = reason.partition(":")
            lines.append(f"    {count:>6}  [{kind:<7}] {text}")
    return "\n".join(lines) if lines else "  (nothing rejected)"
