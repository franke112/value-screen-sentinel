"""A figures appendix, read through a committed cell-to-field map.

SOME NORDIC ISSUERS PUBLISH THE NUMBERS AS A SPREADSHEET. Pandora attaches
one to every interim release: `Pandora Appendix Company Announcement
Q2 2026.xlsx`, ten sheets, the consolidated statements quarter by quarter
back to Q1 2023. **A cell is a number.** There is no glyph at a
coordinate to be reassembled into a row, no model in the loop and nothing
to quote -- so this path is not PDF extraction and must not be confused
with it.

WHAT IS STILL A DECISION, AND WHERE IT LIVES. Which cell answers which
field is a judgement, and frequently a close one. Pandora's balance sheet
says `Cash`; its cash-flow statement says `Cash and cash equivalents, end
of period`, and the two are different numbers -- the second is net of
overdrafts. Its `Loans and borrowings` is the financial-liabilities line
AND contains the lease liabilities, which are not separable from it. A
reader that inferred those mappings at runtime would be making that
judgement invisibly, every run, with nothing to review.

So the mapping is a FILE: `config/manual/maps/<TICKER>.yaml`, one entry
per schema field, naming the sheet and the ROW LABEL -- and carrying a
`note:` wherever the choice is not obvious. It is committed, diffed and
read like any other rule in this project.

THE LABEL, NEVER THE INDEX. A row inserted next year must break the run
loudly rather than shift every figure by one, so nothing here counts
rows. Labels are compared EXACTLY, after stripping surrounding whitespace
and nothing else: this workbook appends footnote markers to some labels
(`Change in payables and other liabilities1`), and a marker appearing on a
mapped label next year is exactly the change that should stop the run
rather than be papered over.

FIVE RULES THE READER MUST NOT SOFTEN:

1. NOTHING IS DERIVED. No row is summed with another, no missing line is
   inferred from its neighbours, no figure is rescaled. `net_interest_paid`
   is absent from Pandora's appendix -- `Finance income received` and
   `Finance costs paid` are stated separately -- and absent is what it
   stays. Adding them would produce a figure the sheet does not state,
   which is the one thing this path exists not to do.
2. AN AMBIGUOUS LABEL IS A HARD ERROR. `Operating profit` appears in
   Pandora's income statement AND in its cash-flow statement; `Loans and
   borrowings` appears under both non-current and current liabilities.
   The map disambiguates with `section:` and `after:`, and a label that
   still matches twice stops the run naming every row it matched.
3. A BLANK OR A DASH IS DATA MISSING, NEVER ZERO. The appendix prints `-`
   where a line does not apply.
4. PERIODS ARE MATCHED BY LABEL ACROSS SHEETS, NOT BY COLUMN POSITION.
   `op_margin` comes from a different sheet than `revenue` and
   `operating_income`, so a column misaligned between two sheets would
   pair figures from different quarters. Matching on the header text makes
   that impossible -- and `config.unit_problem`'s margin reconciliation
   then checks the result for free, across sheets, every period.
5. EVERY FIGURE LANDS UNVERIFIED. The map says which cell; only a person
   says the cell was right. Section 5 refuses until they have.
"""

from __future__ import annotations

import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

from . import manual as M
from .config import ConfigError

log = logging.getLogger(__name__)

#: Where the cell-to-field maps live, one per ticker.
MAPS_DIR = Path("config/manual/maps")

#: Column headers this reader understands, as the appendices write them.
#: `Q2 2026` -> `2026-Q2`; `H1 2026` -> `2026-H1`; `FY 2026` -> `2026-FY`.
#: Anything else STOPS THE RUN rather than being skipped: a header that
#: does not parse is a column whose period nobody knows, and a column
#: silently dropped is a quarter silently missing.
HEADER_PATTERN = re.compile(r"^(Q[1-4]|H[12]|FY)\s+(\d{4})$", re.IGNORECASE)

#: The last calendar day of each period kind. Used ONLY on a declared
#: `period_basis: calendar`, and only to fill `period_end`, which the
#: manual schema requires and the sheet does not state. It is arithmetic
#: on the COLUMN LABEL, not on any figure, and the emitted file says so
#: on every period. A fiscal-basis issuer gets no derivation at all: the
#: map must then state the dates, because where a fiscal year ends is a
#: fact about the company and not about the calendar (backlog B-3).
CALENDAR_ENDS: dict[str, tuple[int, int]] = {
    "Q1": (3, 31), "Q2": (6, 30), "Q3": (9, 30), "Q4": (12, 31),
    "H1": (6, 30), "H2": (12, 31), "FY": (12, 31),
}

ALLOWED_MAP_KEYS = frozenset({
    "ticker", "name", "reporting_currency", "quote_currency", "sector",
    "reporting_frequency", "period_basis", "document", "url", "note",
    "period_ends", "fields", "money_unit", "share_unit",
})
REQUIRED_MAP_KEYS = frozenset({"ticker", "name", "reporting_currency",
                               "quote_currency", "sector", "fields"})
ALLOWED_FIELD_KEYS = frozenset({"sheet", "label", "section", "after", "note"})


class AppendixError(ConfigError):
    """Any problem with a map, a workbook or the match between them."""


# --- the map --------------------------------------------------------------


@dataclass(frozen=True)
class FieldMap:
    name: str
    sheet: str
    label: str
    #: The heading of the period block the row sits in, when the same label
    #: appears in more than one block of one sheet.
    section: str | None = None
    #: A label that must occur ABOVE the wanted row, when the same label
    #: appears twice inside one block. Must itself be unique in the sheet.
    after: str | None = None
    #: Why THIS row and not the one that looks like it. The map is only a
    #: reviewable artefact if the close calls are written down.
    note: str | None = None


@dataclass(frozen=True)
class CellMap:
    ticker: str
    name: str
    reporting_currency: str
    quote_currency: str
    sector: str
    reporting_frequency: str
    period_basis: str
    path: Path
    fields: tuple[FieldMap, ...] = ()
    document: str | None = None
    url: str | None = None
    note: str | None = None
    period_ends: dict[str, date] = field(default_factory=dict)
    #: The scale the appendix states money and counts in -- carried onto
    #: the written file as `money_unit` / `share_unit`, so a regenerated
    #: file keeps the declarations the run record divides on. Optional:
    #: a map that does not say writes a file that does not say, and that
    #: file's record is DATA MISSING per share until the owner declares.
    money_unit: str | None = None
    share_unit: str | None = None

    @property
    def by_name(self) -> dict[str, FieldMap]:
        return {f.name: f for f in self.fields}

    @property
    def unmapped(self) -> tuple[str, ...]:
        """Schema fields the map does not name. Reported, never guessed at."""
        named = self.by_name
        return tuple(n for n in M.FIELDS_BY_NAME if n not in named)


def map_path(ticker: str, directory: Path = MAPS_DIR) -> Path:
    return Path(directory) / f"{ticker.strip().upper()}.yaml"


def load_map(ticker: str, *, directory: Path = MAPS_DIR) -> CellMap:
    path = map_path(ticker, directory)
    if not path.exists():
        raise AppendixError(
            f"no cell map at {path}. Which cell answers which field is a "
            f"judgement -- Pandora's balance sheet `Cash` and its cash-flow "
            f"`Cash and cash equivalents, end of period` are different "
            f"numbers -- so it is written down and reviewed, not inferred at "
            f"runtime. Write the map before reading the workbook."
        )
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise AppendixError(f"{path} is not valid YAML: {exc}")
    return parse_map(document, path=path)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_map(document: Any, *, path: Path) -> CellMap:
    if not isinstance(document, Mapping):
        raise AppendixError(f"{path}: the map must be a mapping")
    unknown = set(document) - ALLOWED_MAP_KEYS
    if unknown:
        raise AppendixError(f"{path}: unknown key(s) {', '.join(sorted(unknown))}. "
                            f"Allowed: {', '.join(sorted(ALLOWED_MAP_KEYS))}")
    missing = REQUIRED_MAP_KEYS - set(document)
    if missing:
        raise AppendixError(f"{path}: missing required key(s) "
                            f"{', '.join(sorted(missing))}")

    frequency = (_text(document.get("reporting_frequency"))
                 or M.DEFAULT_REPORTING_FREQUENCY).lower()
    if frequency not in M.VALID_REPORTING_FREQUENCIES:
        raise AppendixError(f"{path}: reporting_frequency must be one of "
                            f"{'|'.join(M.VALID_REPORTING_FREQUENCIES)}")
    basis = (_text(document.get("period_basis")) or "calendar").lower()
    if basis not in M.VALID_PERIOD_BASIS:
        raise AppendixError(f"{path}: period_basis must be one of "
                            f"{'|'.join(M.VALID_PERIOD_BASIS)}")

    raw_ends = document.get("period_ends") or {}
    if not isinstance(raw_ends, Mapping):
        raise AppendixError(f"{path}: period_ends must be a mapping of period "
                            f"label to YYYY-MM-DD")
    period_ends: dict[str, date] = {}
    for label, value in raw_ends.items():
        try:
            period_ends[str(label).strip()] = (
                value if isinstance(value, date)
                else date.fromisoformat(str(value).strip()))
        except ValueError:
            raise AppendixError(f"{path}: period_ends[{label}] must be a "
                                f"YYYY-MM-DD date, got {value!r}")

    raw_fields = document.get("fields") or {}
    if not isinstance(raw_fields, Mapping) or not raw_fields:
        raise AppendixError(f"{path}: 'fields:' must be a non-empty mapping of "
                            f"schema field to its sheet and row label")

    fields: list[FieldMap] = []
    for name, entry in raw_fields.items():
        name = str(name).strip()
        where = f"{path}: field {name}"
        # A map naming a field the schema does not have fails HERE, not at
        # emit: the schema is the contract, and a typo that reaches the
        # emitted file becomes an unknown key in a different error message.
        if name not in M.FIELDS_BY_NAME:
            raise AppendixError(
                f"{where}: the manual schema has no such field. It carries "
                f"only what the ranking key and the section 5 chain read; "
                f"allowed: {', '.join(sorted(M.FIGURE_KEYS))}")
        if not isinstance(entry, Mapping):
            raise AppendixError(f"{where}: expected a mapping with sheet: and "
                                f"label:")
        unknown = set(entry) - ALLOWED_FIELD_KEYS
        if unknown:
            raise AppendixError(f"{where}: unknown key(s) "
                                f"{', '.join(sorted(unknown))}. Allowed: "
                                f"{', '.join(sorted(ALLOWED_FIELD_KEYS))}")
        for required in ("sheet", "label"):
            if not _text(entry.get(required)):
                raise AppendixError(f"{where}: {required} is required")
        fields.append(FieldMap(
            name=name, sheet=str(entry["sheet"]).strip(),
            label=str(entry["label"]).strip(),
            section=_text(entry.get("section")),
            after=_text(entry.get("after")),
            note=_text(entry.get("note")),
        ))

    return CellMap(
        ticker=str(document["ticker"]).strip().upper(),
        name=str(document["name"]).strip(),
        reporting_currency=str(document["reporting_currency"]).strip().upper(),
        quote_currency=str(document["quote_currency"]).strip().upper(),
        sector=str(document["sector"]).strip(),
        reporting_frequency=frequency,
        period_basis=basis,
        path=path,
        fields=tuple(sorted(fields, key=lambda f: list(M.FIELDS_BY_NAME).index(f.name))),
        document=_text(document.get("document")),
        url=_text(document.get("url")),
        note=_text(document.get("note")),
        period_ends=period_ends,
        money_unit=_map_unit(document.get("money_unit"), "money_unit", path),
        share_unit=_map_unit(document.get("share_unit"), "share_unit", path),
    )


def _map_unit(raw, key: str, path: Path) -> str | None:
    """One of `manual.UNIT_SCALE`, or None. Same rule as the store's own."""
    text = _text(raw)
    if text is None:
        return None
    unit = text.strip().lower()
    if unit not in M.UNIT_SCALE:
        raise AppendixError(
            f"{path}: {key} must be one of {'|'.join(M.VALID_UNITS)}, got "
            f"{raw!r}. The declaration is what a divisor reads; a misspelt "
            f"one is refused rather than guessed at")
    return unit


# --- the workbook ---------------------------------------------------------


@dataclass(frozen=True)
class SheetRow:
    number: int          # for error messages ONLY; nothing matches on it
    label: str
    section: str
    values: dict[str, Any]      # period label -> raw cell value


@dataclass(frozen=True)
class Sheet:
    name: str
    rows: tuple[SheetRow, ...]
    periods: tuple[str, ...]


def parse_header(value: Any) -> str | None:
    """`Q2 2026` -> `2026-Q2`. None when the cell is not a period at all."""
    text = str(value).strip() if value is not None else ""
    match = HEADER_PATTERN.match(text)
    if not match:
        return None
    return f"{match.group(2)}-{match.group(1).upper()}"


def read_sheet(worksheet, name: str) -> Sheet:
    """One sheet as labelled rows, each carrying its own period columns.

    A PERIOD-HEADER ROW is any row whose first cell has text and whose
    remaining cells parse as period labels. Every row below one belongs to
    it, until the next; that row's first cell is the SECTION, and its
    period labels are the columns for everything under it. Pandora's
    financial-statements sheet has four such rows -- income statement,
    comprehensive income, balance sheet, cash flow -- and that is what
    lets `Operating profit` be told from `Operating profit`.

    Nothing here counts rows. The row number is carried for error
    messages, so a failure can be looked at, and is never matched on.
    """
    rows: list[SheetRow] = []
    section = ""
    columns: dict[int, str] = {}
    all_periods: list[str] = []

    for number, raw in enumerate(worksheet.iter_rows(values_only=True), start=1):
        if not raw:
            continue
        label = str(raw[0]).strip() if raw[0] is not None else ""
        parsed = {i: parse_header(v) for i, v in enumerate(raw[1:], start=1)}
        headers = {i: p for i, p in parsed.items() if p}
        if label and headers and len(headers) == len([v for v in raw[1:] if v is not None]):
            # A period-header row: every populated cell beside the label is
            # a period. A row with SOME period-looking cells is not one --
            # that would be a data row that happens to hold a year.
            section, columns = label, headers
            for period in headers.values():
                if period not in all_periods:
                    all_periods.append(period)
            continue
        if not label:
            continue
        rows.append(SheetRow(number=number, label=label, section=section,
                             values={p: raw[i] for i, p in columns.items()
                                     if i < len(raw)}))
    return Sheet(name=name, rows=tuple(rows), periods=tuple(all_periods))


def load_workbook(path: Path) -> dict[str, Sheet]:
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover - openpyxl is a requirement
        raise AppendixError(
            f"reading {path} needs openpyxl: pip install openpyxl") from exc
    if not Path(path).exists():
        raise AppendixError(f"no such workbook: {path}")
    try:
        book = openpyxl.load_workbook(path, data_only=True, read_only=True)
    except Exception as exc:
        raise AppendixError(f"{path}: cannot read as xlsx "
                            f"({type(exc).__name__}: {exc})") from exc
    return {name: read_sheet(book[name], name) for name in book.sheetnames}


# --- matching -------------------------------------------------------------


def _numeric(value: Any) -> float | None:
    """A cell's number, or None. A dash and a blank are DATA MISSING.

    The appendix prints `-` where a line does not apply, and an absent line
    is never a zero -- ASM.AS has no long-term debt line because it has no
    long-term debt, and that is a different fact from zero.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text in ("", "-", "–", "—", "n/a", "N/A"):
        return None
    raise AppendixError(
        f"cell value {value!r} is neither a number nor one of the blanks this "
        f"reader knows. It is NOT guessed at: a cell that has to be "
        f"interpreted is a cell somebody has to look at."
    )


def find_row(sheet: Sheet, spec: FieldMap) -> SheetRow:
    """The one row a field maps to, or a loud failure saying why not."""
    where = f"{spec.name} -> {sheet.name!r} / {spec.label!r}"
    exact = [r for r in sheet.rows if r.label == spec.label]
    if not exact:
        near = sorted({r.label for r in sheet.rows
                       if spec.label.lower() in r.label.lower()
                       or r.label.lower() in spec.label.lower()})
        hint = (f" The sheet has {', '.join(repr(n) for n in near[:4])}, which "
                f"is NOT the same label." if near else "")
        raise AppendixError(
            f"{where}: no row carries that label. Labels are compared exactly, "
            f"after stripping surrounding whitespace and nothing else -- a "
            f"footnote marker or a restated wording is a change the run must "
            f"stop on rather than paper over.{hint}"
        )

    # Only rows that carry a figure SOMEWHERE. A label row blank across
    # every period is a heading, not a line -- Pandora's margin sheet has
    # `EBITDA` as a block heading directly above `EBITDA` the line -- and a
    # row that supplies nothing cannot be the row that was meant.
    candidates = [r for r in exact
                  if any(_numeric(v) is not None for v in r.values.values())]
    if not candidates:
        raise AppendixError(
            f"{where}: the label is present but carries no figure in any "
            f"period column. Nothing is read from it."
        )

    if spec.section is not None:
        candidates = [r for r in candidates if r.section == spec.section]
        if not candidates:
            sections = sorted({r.section for r in exact})
            raise AppendixError(
                f"{where}: no row with that label sits under section "
                f"{spec.section!r}. It appears under "
                f"{', '.join(repr(s) for s in sections)}."
            )

    if spec.after is not None:
        anchors = [r for r in sheet.rows if r.label == spec.after]
        if len(anchors) != 1:
            raise AppendixError(
                f"{where}: the `after:` anchor {spec.after!r} occurs "
                f"{len(anchors)} times in this sheet and must occur exactly "
                f"once. An ambiguous anchor moves the ambiguity rather than "
                f"resolving it."
            )
        after = [r for r in candidates if r.number > anchors[0].number]
        if not after:
            raise AppendixError(
                f"{where}: no row with that label follows {spec.after!r}."
            )
        candidates = [after[0]]

    if len(candidates) > 1:
        listing = "\n".join(
            f"    row {r.number} under section {r.section!r}" for r in candidates)
        raise AppendixError(
            f"{where}: the label matches {len(candidates)} rows and the map "
            f"does not say which. Add `section:` (the heading of the period "
            f"block) or `after:` (a label that occurs once, above the row "
            f"you mean). It is NOT resolved by taking the first:\n{listing}"
        )
    return candidates[0]


# --- extraction -----------------------------------------------------------


@dataclass(frozen=True)
class Filled:
    name: str
    spec: FieldMap
    row: SheetRow
    values: dict[str, float]     # period label -> figure, absent periods omitted


@dataclass(frozen=True)
class Extraction:
    cell_map: CellMap
    workbook: Path
    periods: tuple[str, ...]
    filled: tuple[Filled, ...]
    #: Schema fields the map does not name at all, in schema order. Every
    #: one is a figure this appendix does not state; none is guessed at.
    unmapped: tuple[str, ...] = ()

    @property
    def by_field(self) -> dict[str, Filled]:
        return {f.name: f for f in self.filled}


def period_end_for(label: str, cell_map: CellMap) -> date:
    """The date the period closed. Stated, or derived from the LABEL.

    The manual schema requires it -- STALE is measured on it -- and the
    appendix does not carry it. On a declared CALENDAR basis the label
    determines it: 2026-Q2 ends 30 June, by what the label means. That is
    arithmetic on the column heading, not on any figure, and the emitted
    file says so beside every period.

    On a FISCAL basis nothing is derived. Where a company's year ends is a
    fact about the company -- LULU's fiscal Q1 2026 ended 2026-05-03 --
    and guessing it is backlog B-3 happening again. The map must state the
    dates in `period_ends:`, or the run stops.
    """
    if label in cell_map.period_ends:
        return cell_map.period_ends[label]
    if cell_map.period_basis != "calendar":
        raise AppendixError(
            f"{cell_map.path}: period_ends is missing {label}. This map "
            f"declares `period_basis: fiscal`, and where a fiscal period ends "
            f"is a fact about the company, not about the calendar -- it is "
            f"stated, never derived. Add the closing date for every column, "
            f"or declare the basis calendar if it is one."
        )
    year, kind = int(label[:4]), label[5:]
    month, day = CALENDAR_ENDS[kind]
    return date(year, month, day)


def extract(cell_map: CellMap, sheets: Mapping[str, Sheet]) -> Extraction:
    """Every mapped field, from the sheet and row the map names."""
    filled: list[Filled] = []
    periods: list[str] = []
    for spec in cell_map.fields:
        if spec.sheet not in sheets:
            raise AppendixError(
                f"{cell_map.path}: field {spec.name} names sheet "
                f"{spec.sheet!r}, which this workbook does not contain. It "
                f"has: {', '.join(repr(n) for n in sheets)}."
            )
        sheet = sheets[spec.sheet]
        row = find_row(sheet, spec)
        values = {p: v for p, v in
                  ((p, _numeric(raw)) for p, raw in row.values.items())
                  if v is not None}
        filled.append(Filled(name=spec.name, spec=spec, row=row, values=values))
        for period in sheet.periods:
            if period not in periods:
                periods.append(period)

    ordered = tuple(sorted(periods, key=M.period_sort_key))
    for label in ordered:
        if not M.period_kind_allowed(label, cell_map.reporting_frequency):
            kinds = "/".join(M.PERIOD_KINDS_BY_FREQUENCY[cell_map.reporting_frequency])
            raise AppendixError(
                f"{cell_map.path}: the workbook has a {label} column but this "
                f"ticker is mapped as {cell_map.reporting_frequency}, which "
                f"stores {kinds} periods only."
            )
    return Extraction(cell_map=cell_map, workbook=Path(""), periods=ordered,
                      filled=tuple(filled), unmapped=cell_map.unmapped)


# --- emitting the manual file ---------------------------------------------


def _yaml_scalar(text: str) -> str:
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _number(value: float) -> str:
    """As stated. Never rounded, never rescaled, and never 1.0 for 1."""
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return repr(value)


def render_manual_yaml(extraction: Extraction, *, workbook: Path,
                       as_of: date) -> str:
    """The filled `config/manual/<TICKER>.yaml`, deterministic byte for byte.

    Stable field order (the schema's own) and stable period order (oldest
    first), so re-running against a later appendix produces a diff a person
    can read rather than a reshuffle.
    """
    m = extraction.cell_map
    by_field = extraction.by_field
    document = m.document or workbook.name

    out = [
        f"# {m.ticker} -- fundamentals lifted from the issuer's figures appendix.",
        f"#",
        f"# GENERATED by `vss appendix` on {as_of.isoformat()} from",
        f"#     {workbook}",
        f"# through the cell map",
        f"#     {m.path}",
        f"#",
        f"# EVERY FIGURE IS UNVERIFIED. A cell is a number and the map says",
        f"# which cell -- neither says the cell was the right one. Section 5",
        f"# refuses to run until every figure THE BASIS READS has been read",
        f"# back against the appendix and its status set to VERIFIED (E21).",
        f"# The rest are named in the report and do not block: a quarter",
        f"# outside the twelve-month window cannot move a number section 5",
        f"# produces. The flag is still theirs to clear, and a window that",
        f"# moves may start reading them.",
        f"#",
        f"# Nothing here was summed, inferred, rescaled or filled in by hand.",
        f"# A field the appendix does not state is absent, not zero.",
        "",
        f"ticker: {m.ticker}",
        f"name: {_yaml_scalar(m.name)}",
        f"reporting_currency: {m.reporting_currency}",
        f"quote_currency: {m.quote_currency}",
        f"sector: {_yaml_scalar(m.sector)}",
        f"reporting_frequency: {m.reporting_frequency}",
        f"origin: {M.ORIGIN_XLSX}",
    ]
    # THE DECLARATIONS THE RUN RECORD DIVIDES ON, from the map. Absent
    # there, absent here -- and the record says DATA MISSING per share
    # rather than assuming a scale.
    if m.money_unit is not None:
        out.append(f"money_unit: {m.money_unit}   # from the cell map: the "
                   f"scale the appendix states money in")
    if m.share_unit is not None:
        out.append(f"share_unit: {m.share_unit}   # from the cell map: the "
                   f"scale the appendix states counts in")
    out += ["", "periods:"]

    derived_note = ("derived from the column heading on a calendar basis"
                    if m.period_basis == "calendar" else "as stated in the map")
    for label in extraction.periods:
        end = period_end_for(label, m)
        out.append(f"  - period: {label}")
        out.append(f"    period_end: {end.isoformat()}   # {derived_note};"
                   f" the appendix states no closing date")
        out.append(f"    period_basis: {m.period_basis}")
        out.append(f"    document: {_yaml_scalar(document)}")
        if m.url:
            out.append(f"    url: {_yaml_scalar(m.url)}")
        out.append("    figures:")
        wrote = False
        for name in M.FIELDS_BY_NAME:
            hit = by_field.get(name)
            if hit is None or label not in hit.values:
                continue
            wrote = True
            page = f"{hit.spec.sheet} · {hit.row.label}"
            out.append(f"      {name}:")
            out.append(f"        value: {_number(hit.values[label])}")
            out.append(f"        page: {_yaml_scalar(page)}")
            out.append(f"        status: {M.STATUS_UNVERIFIED}")
        if not wrote:
            out.append("      {}")
    out.append("")
    return "\n".join(out)


def verified_count(path: Path) -> int:
    """How many figures in an existing file a person has already checked."""
    if not path.exists():
        return 0
    try:
        existing = M.parse_manual(
            yaml.safe_load(path.read_text(encoding="utf-8")), path=path)
    except ConfigError:
        return -1
    return sum(1 for f in existing.all_figures() if f.present and f.verified)


def write_manual(text: str, target: Path, *, as_of: date,
                 force: bool = False) -> Path:
    """Write the filled file, and REFUSE to flatten a verified one.

    The status flag records work only a person can do. A writer that
    replaces a file in which figures have been checked resets every one of
    them to UNVERIFIED and throws that evening away -- the single
    irrecoverable action in this module. So an existing file stops the run,
    and says what it is holding.
    """
    target = Path(target)
    if target.exists() and not force:
        checked = verified_count(target)
        held = ("it does not currently load, so nothing can say what it holds"
                if checked < 0 else
                f"it holds {checked} figure(s) already marked "
                f"{M.STATUS_VERIFIED}")
        raise AppendixError(
            f"{target} already exists and {held}. It is NOT overwritten: the "
            f"status flag records a reading a person did against the report, "
            f"and nothing here can redo it.\n"
            f"  * To keep that work, merge the new periods in by hand.\n"
            f"  * To see what would be written, run without --write.\n"
            f"  * To replace it anyway -- an untouched copy of the template, "
            f"say -- pass --force. The file is backed up first, and the "
            f"{M.STATUS_VERIFIED} figures above are what you are discarding.\n"
            f"  * Whether a re-run should MERGE -- keep a VERIFIED figure "
            f"whose value has not changed and refresh the rest -- is a rule "
            f"question and the owner's; it is not decided here."
        )
    backup = None
    if target.exists():
        backup = target.with_suffix(target.suffix + f".bak-{as_of.isoformat()}")
        shutil.copy2(target, backup)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    log.info("wrote %s%s", target, f" (backup {backup})" if backup else "")
    return target


# --- the report -----------------------------------------------------------


def render_report(extraction: Extraction, *, workbook: Path, target: Path,
                  written: Path | None, validated: str | None,
                  as_of: date) -> str:
    m = extraction.cell_map
    by_field = extraction.by_field
    out = [f"# vss appendix -- {m.ticker} ({m.name}) -- {as_of.isoformat()}", ""]
    out.append(f"**SOURCE:** `{workbook}` — the issuer's own figures "
               f"appendix, downloaded by `vss nordic` and recorded in "
               f"`sources/manifest.json`.")
    out.append(f"**MAP:** `{m.path}` — which cell answers which field, "
               f"committed and reviewable. Rows are matched on their LABEL; "
               f"nothing here counts rows.")
    out.append("")
    out.append(f"**ORIGIN `{M.ORIGIN_XLSX}`.** A cell is a number, so this is "
               f"not PDF extraction — but WHICH cell was a decision, and the "
               f"map is where that decision is written down. **Every figure "
               f"lands UNVERIFIED**; section 5 refuses until every figure ITS "
               f"BASIS READS has been read back against the appendix (E21), "
               f"and names the others rather than blocking on them.")
    out.append("")
    out.append(f"- periods found: **{len(extraction.periods)}** — "
               f"`{extraction.periods[0]}` to `{extraction.periods[-1]}`"
               if extraction.periods else "- periods found: none")
    out.append(f"- schema fields filled: **{len(extraction.filled)}** of "
               f"{len(M.FIELDS_BY_NAME)}")
    out.append("")

    out.append("## FILLED")
    out.append("")
    out.append("| Field | Sheet | Row label | Periods | Note |")
    out.append("|---|---|---|---|---|")
    for hit in extraction.filled:
        out.append(f"| `{hit.name}` | {hit.spec.sheet} | {hit.row.label} | "
                   f"{len(hit.values)} | {hit.spec.note or ''} |")
    out.append("")

    if extraction.unmapped:
        out.append("## NOT FILLED — the appendix does not state them")
        out.append("")
        out.append("Absent, not zero, and **nothing is derived to close a "
                   "gap**: a figure summed out of two neighbouring rows is a "
                   "figure the sheet does not state, which is the one thing "
                   "this path exists not to do.")
        out.append("")
        out.append("| Field | Read by |")
        out.append("|---|---|")
        for name in extraction.unmapped:
            spec = M.FIELDS_BY_NAME[name]
            out.append(f"| `{name}` | {', '.join(spec.reads)} |")
        out.append("")

    out.append("## VALIDATION")
    out.append("")
    if validated is None:
        out.append("The emitted file was parsed back through the manual "
                   "loader and **passed**: the unit contract, the "
                   "one-scale-per-file check, the period labels and the "
                   "overlap guard all hold. `op_margin` comes from a "
                   "different sheet than `revenue` and `operating_income`, so "
                   "the margin reconciliation is also a live check that the "
                   "two sheets' columns were matched to the same quarter.")
    else:
        out.append("**The emitted file DOES NOT LOAD.** Nothing was written.")
        out.append("")
        out.append(f"```\n{validated}\n```")
    out.append("")

    out.append("## OUTPUT")
    out.append("")
    if written:
        out.append(f"Written to `{written}`.")
    else:
        out.append(f"**NOT WRITTEN.** Re-run with `--write` to put this in "
                   f"`{target}`.")
    out.append("")
    return "\n".join(out)


def run_appendix(*, ticker: str, workbook: Path, write: bool = False,
                 force: bool = False, maps_dir: Path = MAPS_DIR,
                 manual_dir: Path = M.MANUAL_DIR,
                 as_of: date | None = None) -> tuple[int, str]:
    """Returns (exit_code, report_markdown)."""
    as_of = as_of or date.today()
    key = ticker.strip().upper()
    cell_map = load_map(key, directory=maps_dir)
    if cell_map.ticker != key:
        raise AppendixError(
            f"{cell_map.path} names ticker {cell_map.ticker!r} but was loaded "
            f"for {key!r}. The file name is the key.")

    workbook = Path(workbook)
    sheets = load_workbook(workbook)
    extraction = extract(cell_map, sheets)
    text = render_manual_yaml(extraction, workbook=workbook, as_of=as_of)
    target = Path(manual_dir) / f"{key}.yaml"

    # Parsed back through the loader BEFORE anything is written. The unit
    # contract, the scale check and the period rules are the manual path's,
    # imported rather than repeated, so this path cannot pass something
    # `vss manual` would reject.
    validated: str | None = None
    try:
        M.parse_manual(yaml.safe_load(text), path=target)
    except ConfigError as exc:
        validated = str(exc)

    written = None
    if write and validated is None:
        written = write_manual(text, target, as_of=as_of, force=force)
    report = render_report(extraction, workbook=workbook, target=target,
                           written=written, validated=validated, as_of=as_of)
    if validated is None and not write:
        report += "\n```yaml\n" + text + "```\n"
    return (1 if validated else 0), report
