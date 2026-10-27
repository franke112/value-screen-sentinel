"""The mechanical half of a read-back: does what a hand-read figure QUOTES
stand in the document it cites, and does the figure's VALUE stand in what
it quotes?

A read-back asked the owner two kinds of question. One was a judgment --
is a 5.3bn customer prepayment debt? -- and stays the owner's. The other
was a lookup -- is this sentence on the page, is this word absent from the
filing? -- and a script answers a lookup exactly, every time, without
skimming. This module answers the lookups and nothing else.

SHADOW: it reports and writes nothing. No figure's status is changed here.

Per figure, every quoted string in its `page` is looked for in the cited
document's extracted text, with whitespace, dashes and quote marks
normalised away (an EDGAR table prints "$ 9,144,314" where the quote says
"$9,144,314"; a PDF puts line breaks inside a caption). A quote is:

  EXACT     found as written;
  NEAR      every word and number found, in order, within a short window
            -- a PDF table row that extracted with other columns between;
  MISSING   not found. On a figure that says it was copied from this
            document, that is the defect the read-back exists to catch.

Search claims are checked the other way: "searched ... for 'x', 'y' --
ZERO occurrences" and "'x' occurs NOWHERE" must count zero, and a stated
count ("44 occurrences") must count what it says.

The VALUE check: a non-zero figure is matched against the numbers inside
its own found quotes, at the printed precision, on scales of 1, thousand,
million, billion and percent. A value no found quote contains is not
shown to have been copied, however real the quotes are.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from vss import source as S

TEXT_SUFFIXES = (".htm", ".html", ".pdf", ".txt")

EXACT, NEAR, MISSING = "EXACT", "NEAR", "MISSING"
#: found, but in another of the issuer's filings than the one cited
ELSEWHERE = "ELSEWHERE"
#: a short term on a page that records a search, not found: the absence
#: the search reports, not a misquote
TERM_ABSENT = "TERM ABSENT"

# A quote opens after a boundary and closes before one, so the apostrophe in
# "Gentex's" is neither.
_QUOTE_RE = re.compile(
    r"(?:(?<=^)|(?<=[\s(\[:;,=]))['‘“\"](.+?)['’”\"]"
    r"(?=$|[\s).,;:\]—-])")
#: Where a reader joined pieces of a table row or a sentence: an ellipsis,
#: or a column bar, slash or semicolon written between them.
_ELLIPSIS_RE = re.compile(r"\s*(?:\.\.\.|…)\s*|\s+[|/]\s+|;\s+")
#: A search TERM, not a quote: short, no digit.
_TERM_RE = re.compile(r"^[^\d]{2,40}$")
_SEARCH_RE = re.compile(r"\bsearch(?:ed)?\b(.*?)\b(ZERO|\d[\d,]*)\s+occurrences?",
                        re.I | re.S)
_CHARS_RE = re.compile(r"\(?([\d,]{5,}) characters")
_NOWHERE_RE = re.compile(
    r"['‘\"]([^'’\"]{2,60})['’\"]\s+(?:occurs\s+)?"
    r"(?:occurs NOWHERE|appears NOWHERE|ZERO occurrences|nowhere in)", re.I)
_NUM_RE = re.compile(r"\(?-?\d[\d,.   ]*\d\)?|\(?-?\d\)?")


def _flat(text: str) -> str:
    """Lowercase, one dash, one quote mark, and no whitespace at all."""
    text = text.lower()
    text = re.sub(r"[‐-―−]", "-", text)
    text = re.sub(r"[‘’“”`´\"]", "'", text)
    text = text.replace("$", "")
    text = re.sub(r"\s+", "", text)
    return re.sub(r"-{2,}", "-", text)


def _spaced(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[‐-―−]", "-", text)
    return re.sub(r"\s+", " ", text)


@dataclass
class Doc:
    path: str
    text: str
    flat: str
    spaced: str
    #: the same, with a PDF's end-of-line hyphenation ("struc-\nture") joined
    joined: str = ""


_CACHE: dict[str, Doc | None] = {}


def load_doc(path: str) -> Doc | None:
    if path in _CACHE:
        return _CACHE[path]
    p = Path(path)
    doc = None
    if p.exists() and p.suffix.lower() in TEXT_SUFFIXES:
        raw = p.read_bytes()
        try:
            if S.looks_like_pdf(p.name, raw=raw):
                text = S.pdf_to_text(raw, where=str(p))
            else:
                text, _ = S.to_text(raw.decode("utf-8", errors="ignore"))
            doc = Doc(path, text, _flat(text), _spaced(text),
                      _flat(re.sub(r"-[ \t]*\n\s*", "", text)))
        except S.SourceError:
            doc = None
    _CACHE[path] = doc
    return doc


#: the reference-figures form: `... -- verbatim: <the printed line>`
_VERBATIM_RE = re.compile(r"\bverbatim:\s*(.+?)\s*$", re.S)


def quotes_in(page: str) -> list[str]:
    out = [q.strip() for q in _QUOTE_RE.findall(page or "")
           if len(q.strip()) >= 3]
    m = _VERBATIM_RE.search(page or "")
    if m and not out:
        out.append(m.group(1))
    return out


def _near(fragment: str, doc: Doc, window: int = 400, gap: int = 40) -> bool:
    """Every token of the fragment, in order, inside one short window."""
    tokens = [_flat(t).strip(":;,.()'") for t in re.split(r"\s+", fragment)]
    tokens = [t for t in tokens if t]
    if not tokens:
        return False
    start = 0
    while True:
        i = doc.flat.find(tokens[0], start)
        if i < 0:
            return False
        pos, ok = i + len(tokens[0]), True
        for t in tokens[1:]:
            # a GAP between two words of a quote is a table's other
            # columns, never a clause: wider than that is a paraphrase
            j = doc.flat.find(t, pos, min(i + window, pos + gap + len(t)))
            if j < 0:
                ok = False
                break
            pos = j + len(t)
        if ok:
            return True
        start = i + 1


def find_quote(quote: str, doc: Doc) -> str:
    fragments = [f for f in _ELLIPSIS_RE.split(quote) if _flat(f)]
    if fragments and all(_flat(f) in doc.flat or _flat(f) in doc.joined
                         for f in fragments):
        return EXACT
    if fragments and all(_flat(f) in doc.flat or _near(f, doc)
                         for f in fragments):
        return NEAR
    return MISSING


def _reading(token: str) -> tuple[float, int] | None:
    """One printed number: English (1,234.5) or Nordic (1 234,5 -- the
    space already joined away by the caller)."""
    t = token.rstrip(",.;:").strip("()%").lstrip("-−")
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?|\d+(\.\d+)?", t):
        e = t.replace(",", "")
        return float(e), len(e.split(".")[1]) if "." in e else 0
    if re.fullmatch(r"\d+,\d+", t):
        return float(t.replace(",", ".")), len(t.split(",")[1])
    return None


def numbers_in(text: str) -> list[tuple[float, int]]:
    """Every number a quote can be read as printing, with its decimals.

    A space is a thousands separator in a Nordic report ("672 304") and a
    column break in every table ("624.3 601.1"), and the text cannot say
    which. So both are read: each token alone, and each token joined to
    the three-digit groups after it. Over-reading is safe here -- the
    value must still be one of the readings -- where under-reading made
    every Nordic figure unmatched.
    """
    tokens = re.findall(r"\(?[-−]?[\d][\d,.]*%?\)?", text.replace(
        " ", " ").replace(" ", " "))
    out = []
    for i, tok in enumerate(tokens):
        r = _reading(tok)
        if r:
            out.append(r)
        joined = tok.strip("()").lstrip("-−")
        for nxt in tokens[i + 1:i + 4]:
            n = nxt.strip("()%")
            if not re.fullmatch(r"\d{3}(,\d+)?", n):
                break
            joined += n
            r = _reading(joined)
            if r:
                out.append(r)
    return out


SCALES = (1, 1e3, 1e6, 1e9, 1e-2, 1e-3, 1e-6)


def _matches(v: float, n: float, decimals: int) -> bool:
    tol = 0.5 * 10 ** -decimals + 1e-9
    return any(abs(v / scale - n) <= tol for scale in SCALES)


def value_in(value: float, quotes: list[str]) -> bool:
    """The value is one number a found quote prints -- or, where the page
    adds stated parts ('A' + 'B' = total), the sum of one number from each
    of two or three found quotes."""
    v = abs(float(value))
    per_quote = [numbers_in(q) for q in quotes]
    for nums in per_quote:
        if any(_matches(v, n, d) for n, d in nums):
            return True
    from itertools import combinations, product
    for k in (2, 3):
        for group in combinations([q for q in per_quote if q][:6], k):
            for picks in product(*group):
                total = sum(n for n, _ in picks)
                d = max(d for _, d in picks)
                if _matches(v, total, d):
                    return True
    return False


@dataclass
class FigureCheck:
    ticker: str
    where: str
    name: str
    value: object
    status: str
    doc: str | None
    quotes: dict[str, str] = field(default_factory=dict)
    searches: list[str] = field(default_factory=list)   # failures only
    search_ok: int = 0
    value_matched: bool | None = None
    note: str = ""

    @property
    def verdict(self) -> str:
        if self.doc is None:
            return "NO DOCUMENT"
        if any(v == MISSING for v in self.quotes.values()) or self.searches:
            return "FAILED"
        if not self.quotes and not self.search_ok:
            return "NOTHING TO CHECK"
        if self.value_matched is False:
            return "VALUE NOT IN QUOTES"
        if any(v in (NEAR, ELSEWHERE) for v in self.quotes.values()):
            return "PASS (near)"
        return "PASS"


def _docs_named(text: str) -> list[str]:
    """The filings a page names: a path under sources/, a bare file name
    that is one, or an EDGAR accession number whose saved text is there."""
    text = text or ""
    out = re.findall(r"sources/[^\s'\",;)]+?\.(?:html?|pdf|txt)\b", text)
    for name in re.findall(r"(?<![/\w])([A-Z][\w.-]*_[\w.-]+?\.(?:html?|pdf|txt))\b",
                           text):
        if Path("sources", name).exists():
            out.append(f"sources/{name}")
    for acc in re.findall(r"\b(\d{10}-\d{2}-\d{6})\b", text):
        out += sorted(str(p) for p in Path("sources").glob(f"_briefing_{acc}_*"))
    return out


def _search_claims(page: str) -> tuple[list[tuple[str, int]], set[str]]:
    """(term, expected count) for every recorded search, and the set of
    quoted strings that are search TERMS, not quotes from the page."""
    claims, terms = [], set()
    for m in _SEARCH_RE.finditer(page or ""):
        count = 0 if m.group(2).upper() == "ZERO" else int(
            m.group(2).replace(",", ""))
        found = re.findall(r"['‘\"]([^'’\"]+)['’\"]", m.group(1))
        if not found:
            continue
        # a stated count is the TOTAL over the terms searched
        claims.append(("\x00".join(found), count))
        terms.update(found)
    for t in _NOWHERE_RE.findall(page or ""):
        claims.append((t, 0))
        terms.add(t)
    return claims, terms


def _count(term: str, doc: Doc) -> int:
    return len(re.findall(re.escape(_spaced(term).strip()), doc.spaced))


_RULES: str | None = None


def _is_rule_quote(q: str) -> bool:
    """A page may quote the RULEBOOK ("NOT this leg: ..."), not the filing."""
    global _RULES
    if _RULES is None:
        _RULES = "".join(_flat(Path(p).read_text()) for p in
                         ("reference/FRAMEWORK-EDITS.md",
                          "reference/FRAMEWORK.md") if Path(p).exists())
    return len(q) > 25 and _flat(q)[:60] in _RULES


def issuer_docs(ticker: str) -> list[str]:
    return sorted(str(p) for p in Path("sources").glob(f"{ticker}_*")
                  if p.suffix.lower() in TEXT_SUFFIXES)


def _search_doc(clause: str, cited: Doc, ticker: str) -> Doc:
    """The document a recorded search ran on: the one whose extracted
    length the page states, where it states one; else the cited one."""
    m = _CHARS_RE.search(clause)
    if not m:
        return cited
    n = int(m.group(1).replace(",", ""))
    for path in [cited.path] + issuer_docs(ticker):
        d = load_doc(path)
        if d and abs(len(d.text) - n) <= 0.02 * n:
            return d
    return cited


_XLSX: dict[str, object] = {}
_CELL_RE = re.compile(r"^\s*([^·]+?)\s*·\s*(.+?)\s*$")


def _xlsx_rows(path: str, sheet: str) -> dict[str, dict[str, object]] | None:
    """{row label: {column heading: value}} for one sheet, labels and
    headings stripped and lowercased."""
    key = f"{path}::{sheet}"
    if key not in _XLSX:
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        rows = None
        if sheet in wb.sheetnames:
            heads, rows = None, {}
            for r in wb[sheet].iter_rows(values_only=True):
                if heads is None and any(isinstance(c, str) and
                                         re.fullmatch(r"\s*Q\d \d{4}\s*", c)
                                         for c in r):
                    heads = [str(c).strip().lower() if c is not None else ""
                             for c in r]
                    continue
                # a label repeats -- a section heading with no values, then
                # the amounts, then the ratios: the first row with values
                if (heads and r and isinstance(r[0], str)
                        and any(isinstance(c, (int, float)) for c in r[1:])):
                    rows.setdefault(r[0].strip().lower(), dict(zip(heads, r)))
        _XLSX[key] = rows
    return _XLSX[key]


def check_cell(ticker, where, name, raw, period: str) -> FigureCheck | None:
    """A figure whose page is `<sheet> · <row label>` in an issuer's xlsx
    appendix: the cell at that row and the period's column must hold the
    value (either sign -- the appendix prints costs negative)."""
    m = _CELL_RE.match(str(raw.get("page") or ""))
    books = sorted(Path("sources").glob(f"{ticker}_*.xlsx"))
    pm = re.fullmatch(r"(\d{4})-Q(\d)", period or "")
    if not (m and books and pm):
        return None
    fc = FigureCheck(ticker, where, name, raw.get("value"),
                     str(raw.get("status")), str(books[-1]))
    rows = _xlsx_rows(str(books[-1]), m.group(1))
    col = f"q{pm.group(2)} {pm.group(1)}"
    cell = (rows or {}).get(m.group(2).lower(), {}).get(col)
    label = f"{m.group(1)} / {m.group(2)} / {col.upper()}"
    if cell is None:
        fc.quotes[label] = MISSING
        return fc
    fc.quotes[label] = EXACT
    try:
        fc.value_matched = abs(abs(float(cell)) - abs(float(fc.value))) < 1e-6
    except (TypeError, ValueError):
        fc.value_matched = False
    if not fc.value_matched:
        fc.note += f"cell holds {cell!r}; "
    return fc


def check_figure(ticker, where, name, raw, period_doc) -> FigureCheck:
    page = str(raw.get("page") or "")
    cited = _docs_named(page) or _docs_named(str(raw.get("source") or ""))
    path = cited[0] if cited else period_doc
    fc = FigureCheck(ticker, where, name, raw.get("value"),
                     str(raw.get("status")), path)
    doc = load_doc(path) if path else None
    if doc is None and quotes_in(page) and not _search_claims(page)[0]:
        # no readable filing cited (an xlsx, a zip, a description in
        # words): the issuer's own filing that holds every quote. Never for
        # a search, which is about ONE document.
        for other in issuer_docs(ticker):
            d = load_doc(other)
            if d and all(find_quote(q, d) != MISSING for q in quotes_in(page)):
                doc, fc.doc = d, other
                break
    if doc is None:
        fc.doc = None
        return fc
    claims, terms = _search_claims(page)
    for joined, expected in claims:
        target = _search_doc(page, doc, ticker)
        got = sum(_count(t, target) for t in joined.split("\x00"))
        if got == expected:
            fc.search_ok += 1
        elif expected:
            # a stated count over overlapping terms ("minority interest"
            # inside "minority interests") is not reproducible; what the
            # hits WERE is a reading. Named, not failed.
            fc.note += (f"stated {expected} hits, counted {got}; ")
        else:
            fc.searches.append(f"{joined.replace(chr(0), ' / ')!r}: "
                               f"page says {expected}, document has {got}")
    for q in quotes_in(page):
        if q in terms or q.startswith("sources/"):
            continue
        fc.quotes[q] = find_quote(q, doc)
        if (fc.quotes[q] == MISSING and _TERM_RE.match(q)
                and len(q.split()) <= 5 and re.search(r"search", page, re.I)):
            fc.quotes[q] = TERM_ABSENT
            continue
        if fc.quotes[q] == MISSING:
            for other in issuer_docs(ticker) + _docs_named(page):
                d = load_doc(other)
                if d and d is not doc and find_quote(q, d) != MISSING:
                    fc.quotes[q] = ELSEWHERE
                    break
            else:
                # a page may quote the RULEBOOK; only once no filing has it
                if _is_rule_quote(q):
                    del fc.quotes[q]
    value = raw.get("value")
    if isinstance(value, (int, float)) and value != 0:
        found = [q for q, v in fc.quotes.items() if v != MISSING]
        fc.value_matched = (value_in(value, found)
                            or stated_arithmetic(value, page, found))
    return fc


_OPERAND_RE = re.compile(r"(?:^|\s)([+\-−])\s|(\d[\d,]*(?:\.\d+)?)")


def stated_arithmetic(value: float, page: str, quotes: list[str]) -> bool:
    """E132: a WORKED-OUT figure. The page writes its arithmetic out
    ('opening 300 + new 71 - closing 274 = 97'), every operand is a number
    one of the found quotes prints, and the sum comes to the value. The
    script checks the sum and the operands; whether the working is the
    right one is the owner's ruling, named on the page."""
    v = abs(float(value))
    printed = {abs(n) for q in quotes for n, _ in numbers_in(q)}
    for m in re.finditer(r"=\s*(\d[\d,]*(?:\.\d+)?)", page):
        r = _reading(m.group(1))
        if not r or not _matches(v, r[0], r[1]):
            continue
        segment = re.split(r"[=:;]|\.\s", page[:m.start()])[-1]
        sign, total, operands = 1, 0.0, 0
        for op, num in _OPERAND_RE.findall(segment):
            if op:
                sign = -1 if op in "-−" else 1
                continue
            n = float(num.replace(",", ""))
            if n not in printed:
                break
            total += sign * n
            sign, operands = 1, operands + 1
        else:
            if operands >= 2 and _matches(v, abs(total), r[1]):
                return True
    return False


def check_store(path: Path, *, include_verified: bool = False
                ) -> list[FigureCheck]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        return []
    ticker = str(data.get("ticker") or path.stem)
    out = []
    # E140.1(3): the roll-forward is one mapping, read like a period.
    rf = data.get("roll_forward")
    blocks = [("periods", data.get("periods") or []),
              ("annual", data.get("annual") or []),
              ("roll_forward", [rf] if isinstance(rf, dict) else [])]
    for block, entries in blocks:
        for period in entries:
            label = str(period.get("period") or period.get("fiscal_year")
                        or period.get("period_end"))
            url = str(period.get("url") or "")
            period_doc = url if url.startswith("sources/") else (
                (_docs_named(str(period.get("document") or "")) or [None])[0])
            for name, raw in (period.get("figures") or {}).items():
                if not isinstance(raw, dict):
                    continue
                status = str(raw.get("status"))
                if raw.get("verified_kind") == "tagged":
                    continue
                if status != "UNVERIFIED" and not include_verified:
                    continue
                if raw.get("value") is None:
                    continue
                cell = check_cell(ticker, f"{block} {label}", name, raw,
                                  label)
                out.append(cell or check_figure(ticker, f"{block} {label}",
                                                name, raw, period_doc))
    return out
