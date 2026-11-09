"""E140(1)'s working capital, read off the cash flow statement ITSELF and
tied to the filer's own printed operating cash flow (data rule, E164;
decided by the owner 2026-11-08).

WHY THIS EXISTS. Until 2026-11-08 `working_capital_change` was the sum of a
fixed list of us-gaap tags read from SEC's companyfacts API
(`vss/xbrl.py:e140_working_capital`). The sum was never tied to anything, so
a line the filer tagged otherwise fell out SILENTLY and the figure still
carried VERIFIED. GoDaddy FY2025: 195.1m against 103.0m on the statement.
The prepaid registry fees sit under GoDaddy's own extension element, which
companyfacts does not carry, and "Other operating assets and liabilities"
sits under `IncreaseDecreaseInOtherOperatingCapitalNet`, which the list
lacked (independent review 3, 2026-11-08, H1).

WHAT IT DOES. It reads the filing's inline XBRL (the 10-K or 10-Q in
`sources/`). For one window it walks every row of the operating section
from net income down to "net cash provided by operating activities",
whatever its prefix, extension elements included. It takes each row's
PRINTED value, signed by the parentheses the filer printed. Then:

1. The rows must sum to the printed operating cash flow EXACTLY, to the
   filer's own rounding (half a unit of its `decimals`).
2. Every row's tag must be classed in `config/manual/maps/cashflow-tags.yaml`
   as one of the CLASSES below (a per-ticker override first).
3. Working capital is the sum of the rows classed `rörelsekapital`, plus a
   loan book's provision where a receivable is stripped (E140(1)).

Any failure -- no section found, a sum that misses, a tag the map does not
know, a row whose sign or value cannot be read -- is DATA MISSING with the
reason, and nothing is returned. Nothing is guessed and nothing is
substituted.

STATUS. A derived figure inherits the WEAKEST status of its parts (owner,
2026-11-08). Every part here is a fact the filer tagged in its own filing,
so the figure is VERIFIED of kind `tagged` only because each part is. The
classification is the committed map's, and it is printed with the figure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from lxml import etree

from vss.ixbrl import NS_IX, NS_XBRLI, _number

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = PROJECT_ROOT / "config" / "manual" / "maps" / "cashflow-tags.yaml"

#: The three classes the owner named (2026-11-08). Only the first is
#: working capital. The other two stay in the flow; the difference between
#: them is documentary.
WC = "rörelsekapital"
STAYS = "kvar-i-flödet"
NONCASH = "icke-kassapost"
CLASSES = (WC, STAYS, NONCASH)
#: A CATCH-ALL tag ("Other", "Other, net") has no class of its own: it takes
#: its SECTION's (owner, 2026-11-08) -- working capital under the changes
#: heading, a non-cash adjustment above it.
FOLLOWS = "följer-sektion"

#: The two sections of the operating part of a US cash flow statement,
#: READ FROM THE FILING: the rows above the "changes in (operating) assets
#: and liabilities" heading, and the rows under it.
ADJUSTMENTS = "adjustments"
CHANGES = "changes"
SECTIONS = (ADJUSTMENTS, CHANGES)
SECTION_CLASS = {ADJUSTMENTS: NONCASH, CHANGES: WC}
CHANGES_HEADING = re.compile(
    r"^((net|other)\s+)?changes?\s+in\s+(operating\s+)?assets\s+and\s+liabilities", re.I)
#: The heading the operating section's adjustments stand under. The row
#: just above it is the statement's starting profit, WHATEVER its tag (ACN
#: tags it as income from continuing operations including minorities, BKNG
#: as net income available to common shareholders).
ADJUSTMENTS_HEADING = re.compile(r"^adjustments\s+to\s+reconcile", re.I)

#: Owner, 2026-11-08: a row under the changes heading IS working capital,
#: whatever its tag. The only rows there that stay in the flow are E140(1)'s
#: own exceptions, and a map entry claiming one must name which.
E140_EXCEPTIONS = ("tax", "lease", "long-term", "E123")

#: The rows a cash flow statement's operating section starts from.
START_TAGS = ("us-gaap:NetIncomeLoss", "us-gaap:ProfitLoss")
#: Its total.
OCF_TAGS = ("us-gaap:NetCashProvidedByUsedInOperatingActivities",)


class ReconError(Exception):
    """DATA MISSING: the working capital cannot be tied to the statement."""


@dataclass(frozen=True)
class Row:
    tag: str
    shown: float          # the printed value, signed by the printed parentheses
    klass: str
    note: str
    receivable: bool = False
    follows_receivable: bool = False
    caption: str = ""      # the row's printed caption, for the reader
    section: str = ""      # adjustments | changes, as the filing prints it


@dataclass
class Reconciliation:
    """One window's operating section, tied."""

    ticker: str
    document: str
    start: str
    end: str
    net_income: Row
    rows: list[Row]
    ocf: float
    tolerance: float
    working_capital: float
    parts: list[Row] = field(default_factory=list)
    status: str = "VERIFIED"
    verified_kind: str = "tagged"

    def page(self) -> str:
        """The store's `page` for the figure: every part, its sign, the tie."""
        legs = " + ".join(f"{p.tag} {p.shown:,.0f}" for p in self.parts) or "no line"
        return (f"E140(1) tied to the cash flow statement: {self.document}, "
                f"{self.start}..{self.end}. Working capital = {legs} = "
                f"{self.working_capital:,.0f} (printed values, cash effect). "
                f"The operating section's {len(self.rows) + 1} rows sum to the "
                f"printed operating cash flow {self.ocf:,.0f} within "
                f"{self.tolerance:,.0f}; classes from "
                f"config/manual/maps/cashflow-tags.yaml")


# --- the map ----------------------------------------------------------------

def load_map(path: Path = MAP_PATH) -> dict[str, Any]:
    """The committed map. Refuses an entry without a class, a section or a
    note, and a changes-section entry outside working capital that does not
    name its E140(1) exception. `pending:` is the owner's list: tags seen,
    a classification PROPOSED, none applied."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tags = raw.get("tags") or {}
    overrides = raw.get("overrides") or {}
    pending = raw.get("pending") or {}
    for where, table in [("tags", tags)] + [(f"overrides.{t}", v)
                                            for t, v in overrides.items()]:
        for tag, entry in (table or {}).items():
            name = f"{path.name}: {where}.{tag}"
            if not isinstance(entry, dict) or entry.get("class") not in CLASSES + (FOLLOWS,):
                raise ReconError(f"{name} has no class in {CLASSES + (FOLLOWS,)}")
            if entry.get("section") not in SECTIONS:
                raise ReconError(f"{name} has no section in {SECTIONS} -- the "
                                 f"section is read from the filing")
            if not str(entry.get("note") or "").strip():
                raise ReconError(f"{name} has no note -- every classification "
                                 f"states its reason")
            if (entry["section"] == CHANGES and entry["class"] not in (WC, FOLLOWS)
                    and entry.get("e140_exception") not in E140_EXCEPTIONS):
                raise ReconError(
                    f"{name}: a row under the changes heading is working capital "
                    f"unless it is one of E140(1)'s exceptions -- name it "
                    f"(e140_exception: one of {E140_EXCEPTIONS})")
    for tag, entry in pending.items():
        if not isinstance(entry, dict) or not str(entry.get("note") or "").strip():
            raise ReconError(f"{path.name}: pending.{tag} has no note")
    return {"tags": tags, "overrides": overrides, "pending": pending}


def classify(tag: str, ticker: str, cmap: dict[str, Any]) -> dict | None:
    own = (cmap["overrides"].get(ticker) or {}).get(tag)
    return own if own is not None else cmap["tags"].get(tag)


def _row_of(el):
    return next((a for a in el.iterancestors() if etree.QName(a).localname == "tr"), None)


def _sections(root, section) -> list[str]:
    """Each fact's section (adjustments | changes), read from the filing:
    the rows under the one "changes in ... assets and liabilities" heading
    between the net income row and the total are changes. No heading, or
    more than one, refuses -- the section is never guessed."""
    first, last = _row_of(section[0][0]), _row_of(section[-1][0])
    if first is None or last is None:
        raise ReconError("the statement is not laid out in table rows")
    order, headings, on = {}, [], False
    for i, tr in enumerate(r for r in root.iter() if isinstance(r.tag, str)
                           and etree.QName(r).localname == "tr"):
        if tr is first:
            on = True
        if on:
            order[tr] = i
            text = " ".join("".join(tr.itertext()).split())
            if CHANGES_HEADING.match(text) and not any(
                    True for _ in tr.iter(f"{{{NS_IX}}}nonFraction")):
                headings.append(i)
        if tr is last:
            break
    if len(headings) > 1:
        raise ReconError(f"{len(headings)} 'changes in assets and liabilities' "
                         f"headings in the section; the rows cannot be sectioned")
    # NO changes heading (MUSA): the filing prints every row under the
    # adjustments heading, and that is the section each row is read in.
    cut = headings[0] if headings else None
    out = []
    for el, _, _ in section:
        tr = _row_of(el)
        if tr not in order:
            raise ReconError("a row stands outside the statement's table rows")
        out.append(CHANGES if cut is not None and order[tr] > cut else ADJUSTMENTS)
    return out


def _start_index(root, facts, t) -> int | None:
    """The statement's starting row for the total at ``t``: the last fact
    above the nearest "Adjustments to reconcile" heading. Where the filing
    prints no such heading, the nearest net income tag (START_TAGS). None
    where neither is found, or another total stands in between."""
    trs = [r for r in root.iter() if isinstance(r.tag, str)
           and etree.QName(r).localname == "tr"]
    order = {tr: i for i, tr in enumerate(trs)}
    total_tr = _row_of(facts[t][0])
    if total_tr in order:
        heads = [order[tr] for tr in trs[:order[total_tr]]
                 if ADJUSTMENTS_HEADING.match(" ".join("".join(tr.itertext()).split()))
                 and not any(True for _ in tr.iter(f"{{{NS_IX}}}nonFraction"))]
        if heads:
            h = heads[-1]
            above = [i for i in range(t) if order.get(_row_of(facts[i][0]), -1) < h
                     and order.get(_row_of(facts[i][0]), -1) >= 0]
            if above:
                s = above[-1]
                if not any(facts[i][1] in OCF_TAGS for i in range(s, t)):
                    return s
    s = next((i for i in range(t - 1, -1, -1) if facts[i][1] in START_TAGS
              or facts[i][1] in OCF_TAGS), None)
    if s is None or facts[s][1] in OCF_TAGS:
        return None
    return s


# --- the document -------------------------------------------------------------

def _contexts(root) -> dict[str, tuple[str, str]]:
    """Non-dimensional DURATION contexts: id -> (start, end)."""
    out = {}
    for ctx in root.iter(f"{{{NS_XBRLI}}}context"):
        if ctx.find(f".//{{{NS_XBRLI}}}segment") is not None or \
                ctx.find(f".//{{{NS_XBRLI}}}scenario") is not None:
            continue
        period = ctx.find(f"{{{NS_XBRLI}}}period")
        if period is None:
            continue
        start = period.find(f"{{{NS_XBRLI}}}startDate")
        end = period.find(f"{{{NS_XBRLI}}}endDate")
        if start is not None and end is not None:
            out[ctx.get("id")] = (start.text.strip(), end.text.strip())
    return out


def _in_header(el) -> bool:
    return any(a.tag == f"{{{NS_IX}}}header" for a in el.iterancestors())


_MARK = "⁣⁣"          # invisible separator, never in a filing's text


def _shown_sign(el) -> int | None:
    """-1 where the printed number stands in parentheses, +1 where it does
    not, None where the text around it is unreadable. Read in the table row
    (or the parent block) so a parenthesis in a neighbouring cell counts."""
    row = next((a for a in el.iterancestors() if etree.QName(a).localname == "tr"),
               el.getparent())
    original = el.text
    el.text = _MARK + (original or "")
    try:
        text = "".join(row.itertext())
    finally:
        el.text = original
    i = text.find(_MARK)
    if i < 0:
        return None
    shown = "".join(el.itertext())
    before = text[:i].rstrip("  \t\n$€£")
    after = text[i + len(_MARK) + len(shown):].lstrip("  \t\n")
    opened = before.endswith("(")
    closed = after.startswith(")")
    if opened and closed:
        return -1
    if opened or closed:
        return None             # half a parenthesis: not guessed
    return 1


def _caption(el) -> str:
    """The printed caption of the fact's row: the row's first cell."""
    row = next((a for a in el.iterancestors() if etree.QName(a).localname == "tr"), None)
    if row is None:
        return ""
    for cell in row:
        text = " ".join("".join(cell.itertext()).split())
        if text:
            return text[:90]
    return ""


def _facts(root, contexts):
    """Body facts in document order: (element, tag, window, magnitude, sign)."""
    out = []
    for el in root.iter(f"{{{NS_IX}}}nonFraction"):
        window = contexts.get(el.get("contextRef"))
        if window is None or _in_header(el):
            continue
        out.append((el, el.get("name") or "", window))
    return out


def _magnitude(el) -> float | None:
    """The printed magnitude: the element's number WITHOUT its `sign`."""
    value = _number(el)
    if value is None:
        return None
    d = el.get("decimals")
    if d not in (None, "", "INF"):
        # to the filer's own precision: 1,047.6 x 10^6 is 1,047,600,000, not
        # the float 1,047,599,999.9999999
        return abs(round(value, int(d)))
    return abs(value)


def _tolerance(el) -> float:
    d = el.get("decimals")
    if d in (None, "", "INF"):
        return 0.5
    return 0.5 * 10 ** (-int(d))


def windows(html: bytes) -> list[tuple[str, str]]:
    """Every window the document prints an operating cash flow for."""
    root = _parse(html)
    ctx = _contexts(root)
    seen = []
    for el, tag, w in _facts(root, ctx):
        if tag in OCF_TAGS and w not in seen:
            seen.append(w)
    return seen


def _parse(html: bytes):
    root = etree.fromstring(html, parser=etree.XMLParser(recover=True, huge_tree=True))
    if root is None:
        raise ReconError("the document is not parseable as inline XBRL")
    return root


def reconcile(html: bytes, *, ticker: str, document: str, start: str, end: str,
              cmap: dict[str, Any] | None = None) -> Reconciliation:
    """The operating section for the window start..end, tied and classed.
    Raises ReconError (DATA MISSING) on anything that does not hold."""
    cmap = load_map() if cmap is None else cmap
    root = _parse(html)
    facts = [f for f in _facts(root, _contexts(root)) if f[2] == (start, end)]
    totals = [i for i, f in enumerate(facts) if f[1] in OCF_TAGS]
    if not totals:
        raise ReconError(f"{document}: no operating cash flow is tagged for "
                         f"{start}..{end}")
    failures = []
    for t in totals:
        s = _start_index(root, facts, t)
        if s is None:
            failures.append("no net income row above the total")
            continue
        try:
            return _tie(facts[s:t + 1], _sections(root, facts[s:t + 1]),
                        ticker=ticker, document=document,
                        start=start, end=end, cmap=cmap)
        except ReconError as exc:
            failures.append(str(exc))
    raise ReconError(f"{document} {start}..{end}: no operating section ties -- "
                     + " | ".join(failures))


def _tie(section, sections, *, ticker, document, start, end, cmap) -> Reconciliation:
    rows: list[Row] = []
    unknown, unreadable, pending, misplaced = [], [], [], []
    for (el, tag, _), where in zip(section, sections):
        mag, sign = _magnitude(el), _shown_sign(el)
        if mag is None or sign is None:
            unreadable.append(tag)
            continue
        if not rows:            # the statement's starting profit, whatever its tag
            rows.append(Row(tag, sign * mag, "start", "net income", caption=_caption(el)))
            continue
        if tag in OCF_TAGS:
            rows.append(Row(tag, sign * mag, "total", "operating cash flow",
                            caption=_caption(el)))
            continue
        entry = classify(tag, ticker, cmap)
        if entry is None:
            if tag in (cmap.get("pending") or {}):
                p = cmap["pending"][tag]
                pending.append(f"{tag} (proposed: {p.get('proposal', '?')})")
            else:
                unknown.append(f"{tag} [{where}] '{_caption(el)}'")
            continue
        if entry["section"] != where and entry["class"] != FOLLOWS:
            # a catch-all follows the section it stands in (owner,
            # 2026-11-08); any other entry must stand where it was classed
            misplaced.append(f"{tag} is classed for {entry['section']} and stands "
                             f"under {where} ('{_caption(el)}')")
            continue
        klass = SECTION_CLASS[where] if entry["class"] == FOLLOWS else entry["class"]
        rows.append(Row(tag, sign * mag, klass, str(entry["note"]), section=where,
                        receivable=bool(entry.get("fordran")),
                        follows_receivable=bool(entry.get("följer_fordran")),
                        caption=_caption(el)))
    if unreadable:
        raise ReconError(f"a printed value or sign cannot be read: {unreadable}")
    if unknown:
        raise ReconError(f"not in the map (config/manual/maps/cashflow-tags.yaml) "
                         f"-- ASK THE OWNER, the session never adds one: "
                         f"{sorted(set(unknown))}")
    if pending:
        raise ReconError(f"waiting for the owner's classification: "
                         f"{sorted(set(pending))}")
    if misplaced:
        raise ReconError(f"section differs from the map -- ask the owner: {misplaced}")
    ni, total, body = rows[0], rows[-1], rows[1:-1]
    # E166 (owner, 2026-11-08): the filer's own rounding, half a unit of its
    # `decimals` FOR EACH PRINTED ROW summed -- a statement in millions whose
    # lines are rounded one by one need not foot to the million (ALV FY2025:
    # rows 1,155m, printed 1,157m). Never more than half a unit per row.
    tol = _tolerance(section[-1][0]) * len(section)
    summed = ni.shown + sum(r.shown for r in body)
    if abs(summed - total.shown) > tol:
        raise ReconError(f"the rows sum to {summed:,.0f} and the statement prints "
                         f"{total.shown:,.0f} (difference {summed - total.shown:,.0f}, "
                         f"tolerance {tol:,.0f})")
    parts = [r for r in body if r.klass == WC]
    if any(r.receivable for r in parts):
        parts += [r for r in body if r.follows_receivable and r.klass != WC]
    return Reconciliation(ticker=ticker, document=document, start=start, end=end,
                          net_income=ni, rows=body, ocf=total.shown, tolerance=tol,
                          working_capital=sum(p.shown for p in parts), parts=parts)


def reconcile_file(path: Path, *, ticker: str, cmap=None) -> list[Reconciliation | ReconError]:
    """Every window in one document, each tied or its DATA MISSING."""
    html = Path(path).read_bytes()
    out: list[Reconciliation | ReconError] = []
    for start, end in windows(html):
        try:
            out.append(reconcile(html, ticker=ticker, document=Path(path).name,
                                 start=start, end=end, cmap=cmap))
        except ReconError as exc:
            out.append(exc)
    return out


# --- the store (E166): the figure the record reads ----------------------------

#: The page every tied figure starts with; `vss/runrecord.py` refuses a US
#: GAAP store's working capital that does not carry it.
TIED_PREFIX = "E140(1) tied to the cash flow statement"
#: E166: the figure is DERIVED -- a sum of tagged facts, tied to the printed
#: total and classed by the committed map. It is never VERIFIED in its own
#: right: its status is the weakest of its parts', and every part is a fact
#: the filer tagged in its own filing (`tagged`).
KIND_TIED = "tied_statement"
SOURCES = PROJECT_ROOT / "sources"


def _store_documents(ticker: str, ends: list[str], rf_end: str | None,
                     sources: Path = SOURCES) -> list[Path]:
    """The 10-K whose columns hold ``ends`` and the 10-Q at ``rf_end``."""
    names = sorted(p.name for p in sources.glob(f"{ticker}_*"))
    out = []
    tenk = [n for n in names if n.startswith(f"{ticker}_FY") and "10k" in n]
    if tenk:
        out.append(sources / tenk[-1])
    if rf_end:
        q = [n for n in names if n.startswith(f"{ticker}_{rf_end}_") and "10q" in n]
        if q:
            out.append(sources / q[-1])
    return out


def _figure_block(r: Reconciliation, indent: int) -> list[str]:
    pad = " " * indent
    page = r.page().replace('"', "'")
    return [f"{pad}working_capital_change:",
            f"{pad}  value: {r.working_capital:.0f}",
            f'{pad}  page: "{page}"',
            f"{pad}  status: VERIFIED",
            f"{pad}  verified_kind: {KIND_TIED}"]


def fill_store_text(text: str, tied: dict[str, Reconciliation],
                    rf_window: tuple[str, str] | None) -> tuple[str, list[str]]:
    """The store's text with each `working_capital_change` whose window the
    reconciliation answers replaced by the tied figure. ``tied`` is keyed by
    the window END for fiscal years; the roll-forward is answered only for
    its exact year-to-date window. Every other line is kept. Returns the
    text and what was replaced."""
    lines = text.split("\n")
    out, done = [], []
    year_end = None
    in_rf = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line and line[0] not in " #":
            in_rf = line.startswith("roll_forward:")
            year_end = None
        m = re.match(r"^    period_end:\s*(\S+)", line)
        if m and not in_rf:
            year_end = m.group(1)
        stripped = line.strip()
        if stripped == "working_capital_change:":
            indent = len(line) - len(line.lstrip())
            j = i + 1
            while j < len(lines) and (not lines[j].strip()
                                      or len(lines[j]) - len(lines[j].lstrip()) > indent):
                j += 1
            r = None
            if in_rf and rf_window is not None:
                r = tied.get(f"{rf_window[0]}..{rf_window[1]}")
            elif not in_rf and year_end is not None:
                r = tied.get(year_end)
            if r is not None:
                out.extend(_figure_block(r, indent))
                trailing = [l for l in lines[i + 1:j] if not l.strip()]
                out.extend(trailing)
                done.append(f"{'roll_forward' if in_rf else year_end}: "
                            f"{r.working_capital:,.0f}")
                i = j
                continue
        out.append(line)
        i += 1
    return "\n".join(out), done


def fill(ticker: str, *, manual_dir: Path | None = None,
         sources: Path = SOURCES, write: bool = False, cmap=None) -> tuple[str, list[str]]:
    """E166: put the tied working capital into an existing sec-xbrl store --
    every fiscal year the latest 10-K's statement covers, and the
    roll-forward's year to date where the 10-Q it stands on is in sources/.
    The roll-forward's DATE IS NOT MOVED. A window the reconciliation cannot
    answer keeps its old figure, which the record then refuses (it does not
    carry `tied_statement`). The text is parsed back through the manual
    loader before it is written; git is the backup."""
    from datetime import date, timedelta

    from .manual import MANUAL_DIR, parse_manual

    target = Path(manual_dir or MANUAL_DIR) / f"{ticker}.yaml"
    text = target.read_text(encoding="utf-8")
    raw = yaml.safe_load(text)
    rf = raw.get("roll_forward") or {}
    rf_end = str(rf.get("period_end")) if rf.get("period_end") else None
    rf_from = str(rf.get("from_year_end")) if rf.get("from_year_end") else None
    rf_window = None
    if rf_end and rf_from:
        rf_window = ((date.fromisoformat(rf_from) + timedelta(days=1)).isoformat(), rf_end)
    tied: dict[str, Reconciliation] = {}
    report: list[str] = []
    for doc in _store_documents(ticker, [], rf_end, sources):
        for r in reconcile_file(doc, ticker=ticker, cmap=cmap):
            if isinstance(r, ReconError):
                report.append(f"DATA MISSING {doc.name}: {r}")
                continue
            if "10q" in doc.name:
                tied[f"{r.start}..{r.end}"] = r
            else:
                tied[r.end] = r
    new, done = fill_store_text(text, tied, rf_window)
    parse_manual(yaml.safe_load(new), path=target)          # refuses before writing
    report = [f"{ticker}: {len(done)} figure(s) tied -- " + "; ".join(done)] + report
    if write and new != text:
        target.write_text(new, encoding="utf-8")
        report.append(f"wrote {target}")
    return new, report


if __name__ == "__main__":                       # pragma: no cover
    import argparse

    ap = argparse.ArgumentParser(description="E166: tie a store's working capital")
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    for t in a.tickers:
        print("\n".join(fill(t, write=a.write)[1]))

