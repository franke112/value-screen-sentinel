"""Parsers for every source the playbook reads. Nothing here composes.

Every function returns what it found and a list of `problems` -- a source
that is absent on a fresh clone is a sentence on the page, never a failed
build.
"""

from __future__ import annotations

import csv
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK = ROOT / "reference" / "FRAMEWORK.md"
EDITS = ROOT / "reference" / "FRAMEWORK-EDITS.md"
WATCHLIST = ROOT / "config" / "watchlist.yaml"
SHADOW_BOOK = ROOT / "config" / "shadow_book.csv"
REPORTS = ROOT / "reports"
REFERENCE = ROOT / "reference"

ISO = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _name(path: Path) -> str:
    """A path as the page names it: relative to the repository where it
    is inside it, absolute otherwise (a test fixture)."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _as_date(text: str) -> date | None:
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def first_sentence(text: str, limit: int = 300) -> str:
    """The first sentence of a paragraph, verbatim, capped in length."""
    text = " ".join(text.split())
    if not text:
        return ""
    m = re.search(r"(?<=[.!?])\s+(?=[A-Z\"'`*(])", text)
    sentence = text[: m.start()] if m else text
    if len(sentence) > limit:
        sentence = sentence[: limit - 1].rstrip() + "…"
    return sentence


# --------------------------------------------------------------------------
# FRAMEWORK.md
# --------------------------------------------------------------------------

@dataclass
class Section:
    key: str            # "§3", "Gate 1", "4.2", "5.3", "6.4"
    title: str          # the heading text after the key
    level: int          # 2 or 3
    parent: str | None  # the §N a level-3 section sits under
    lines: list[str] = field(default_factory=list)

    @property
    def heading(self) -> str:
        return f"{self.key} — {self.title}" if self.title else self.key


_H2 = re.compile(r"^## (?P<key>§\d+)\s*[—-]+\s*(?P<title>.+?)\s*$")
_H3 = re.compile(r"^### (?P<key>Gate \d|\d+\.\d+)\s*[—-]*\s*(?P<title>.*?)\s*$")


def framework_sections(path: Path = FRAMEWORK) -> tuple[dict[str, Section], list[str]]:
    if not path.exists():
        return {}, [f"{_name(path)} is not on disk; no framework text is quoted"]
    out: dict[str, Section] = {}
    current: Section | None = None
    parent: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        m2 = _H2.match(line)
        m3 = _H3.match(line)
        if m2:
            parent = m2.group("key")
            current = Section(parent, m2.group("title"), 2, None)
            out[parent] = current
            continue
        if m3:
            current = Section(m3.group("key"), m3.group("title"), 3, parent)
            out[m3.group("key")] = current
            continue
        if current is not None:
            current.lines.append(line)
    return out, []


def framework_version(path: Path = FRAMEWORK) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines()[:6]:
        m = re.match(r"\*\*Version:\*\*\s*(\S+)", line)
        if m:
            return m.group(1)
    return None


# --------------------------------------------------------------------------
# FRAMEWORK-EDITS.md
# --------------------------------------------------------------------------

_ENTRY = re.compile(
    r"^### (?P<key>[A-F]\d+(?:\.\d+)?)"
    r"(?P<more>(?:\s*/\s*[A-F]\d+(?:\.\d+)?)*)"
    r"\s*[—–-]+\s*(?P<title>.+?)\s*$")
_ANY_H3 = re.compile(r"^### (?P<title>.+?)\s*$")
_LABEL = re.compile(r"^\*\*(?P<label>[^*]{2,80}?)[.:]?\*\*\s*(?P<rest>.*)$")
_KEYREF = re.compile(r"\b([A-F]\d+(?:\.\d+)?)\b")
SETTLED_MARKERS = ("RULED", "DECIDED", "SETTLED", "CLOSED", "APPLIED",
                   "WITHDRAWN", "REFUSED", "BUILT", "AMENDED")
OPEN_MARKERS = ("PROPOSED", "RAISED", "OPEN", "NOT DECIDED", "NOT RULED")
_WINDOW = 14


@dataclass
class Ruling:
    key: str
    title: str
    line: int
    kind: str                       # the letter
    date: date | None = None
    date_how: str = "DATA MISSING"  # stated | inferred | DATA MISSING
    status: str = ""                # the marker word found, verbatim
    settled: bool = False
    superseded_by: list[str] = field(default_factory=list)
    supersede_phrase: str = ""
    closed_by: list[str] = field(default_factory=list)
    amends: list[str] = field(default_factory=list)
    amended_by: list[str] = field(default_factory=list)
    application: bool = False       # a "second application" of an earlier key
    also_keys: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    blocks: dict[str, str] = field(default_factory=dict)
    cases: list[str] = field(default_factory=list)

    @property
    def open(self) -> bool:
        return not self.settled and not self.superseded_by

    @property
    def superseded(self) -> bool:
        return bool(self.superseded_by)


def _paragraphs(lines: Sequence[str]) -> list[str]:
    out, buf = [], []
    for line in lines:
        if line.startswith("#"):
            if buf:
                out.append(" ".join(buf))
                buf = []
            continue
        if line.strip() == "" or line.strip() == "---":
            if buf:
                out.append(" ".join(buf))
                buf = []
            continue
        buf.append(line.strip().lstrip("> ").strip())
    if buf:
        out.append(" ".join(buf))
    return [p for p in out if p]


def edits_rulings(path: Path = EDITS, tickers: Sequence[str] = ()
                  ) -> tuple[list[Ruling], list[str], list[str]]:
    """Every numbered entry, in file order; plus unnumbered `###` notes."""
    if not path.exists():
        return [], [], [f"{_name(path)} is not on disk; no ruling is placed"]
    lines = path.read_text(encoding="utf-8").splitlines()
    heads = [i for i, l in enumerate(lines) if _ANY_H3.match(l)]
    heads.append(len(lines))
    rulings: list[Ruling] = []
    notes: list[str] = []
    seen: set[str] = set()
    ticker_set = sorted(set(tickers), key=len, reverse=True)
    for start, stop in zip(heads, heads[1:]):
        m = _ENTRY.match(lines[start])
        if not m:
            notes.append(_ANY_H3.match(lines[start]).group("title"))
            continue
        key = m.group("key")
        also = _KEYREF.findall(m.group("more") or "")
        body = lines[start + 1: stop]
        r = Ruling(key=key, title=m.group("title"), line=start + 1, kind=key[0],
                   also_keys=also, paragraphs=_paragraphs(body))
        r.application = key in seen or "second application" in r.title.lower()
        seen.add(key)
        window = "\n".join(lines[start: min(start + _WINDOW, stop)])
        # date
        for pat in (r"\b(?:RULED|DECIDED|SETTLED|CLOSED|PROPOSED|RAISED|APPLIED|WITHDRAWN|BUILT|AMENDED)\b[^\n]{0,80}?(\d{4}-\d{2}-\d{2})",
                    r"\bowner[^\n]{0,60}?(\d{4}-\d{2}-\d{2})"):
            f = re.search(pat, window, re.I)
            if f:
                r.date, r.date_how = _as_date(f.group(1)), "stated"
                break
        else:
            f = ISO.search(window)
            if f:
                r.date, r.date_how = _as_date(f.group(1)), "inferred"
        # status
        upper = window.upper()
        found = [w for w in SETTLED_MARKERS + OPEN_MARKERS if re.search(rf"\b{w}\b", upper)]
        r.status = ", ".join(found) if found else "no marker in the opening lines"
        if r.kind == "E" or r.kind == "F":
            r.settled = not any(w in found for w in ("PROPOSED", "NOT DECIDED", "NOT RULED")) or any(
                w in found for w in SETTLED_MARKERS)
        else:
            r.settled = any(w in found for w in SETTLED_MARKERS) and not (
                "OPEN" in found and not any(w in found for w in ("DECIDED", "RULED", "SETTLED", "CLOSED")))
        # supersession: ONLY when the entry says so at its own head, in
        # bold, below the heading. "amends" is recorded separately and does
        # not strike an entry through: E90 amends E28's arithmetic and E28
        # is still the engine ruling.
        text = "\n".join(body)
        head_window = "\n".join(lines[start + 1: min(start + _WINDOW, stop)])
        for f in re.finditer(r"\*\*SUPERSEDED\b[^*\n]{0,80}?\b(?:by|under)\s+([A-F]\d+(?:\.\d+)?)", head_window):
            if f.group(1) != key:
                r.superseded_by.append(f.group(1))
                r.supersede_phrase = f.group(0)
        for f in re.finditer(r"\b(?:CLOSED|SETTLED|DECIDED|RULED)\b[^.\n]{0,40}?\bby\s+\**([A-F]\d+(?:\.\d+)?)", head_window):
            if f.group(1) != key:
                r.closed_by.append(f.group(1))
        # labelled blocks
        for i, p in enumerate(r.paragraphs):
            lm = _LABEL.match(p)
            if lm:
                label = lm.group("label").strip().upper().rstrip(".:")
                rest = lm.group("rest").strip()
                if not rest and i + 1 < len(r.paragraphs):
                    rest = r.paragraphs[i + 1]
                r.blocks.setdefault(label, rest or p)
        amends = next((t for l, t in r.blocks.items() if l.startswith("WHICH EARLIER RULING")), "")
        if amends:
            r.amends = [k for k in _KEYREF.findall(first_sentence(amends, 400)) if k != key]
        # case references
        for t in ticker_set:
            if re.search(rf"(?<![A-Z0-9.])({re.escape(t)})(?![A-Z0-9.])", text):
                r.cases.append(t)
        rulings.append(r)
    # the reverse links: which later entries amend this one
    by_key = {r.key: r for r in rulings if not r.application}
    for r in rulings:
        for k in dict.fromkeys(r.amends):
            if k in by_key and k != r.key and r.key not in by_key[k].amended_by:
                by_key[k].amended_by.append(r.key)
    return rulings, notes, []


def _plain(text: str) -> str:
    """Drop bold and italic markers: a sentence cut mid-bold must not leak `**`."""
    return re.sub(r"\*{1,2}", "", text).strip()


_STATUS_LABEL = re.compile(r"^(RULED|DECIDED|SETTLED|CLOSED|PROPOSED|RAISED|APPLIED|BUILT|AMENDED|WITHDRAWN|SUPERSEDED)\b")
_ACCEPT_WORDS = re.compile(r"\b(accept\w*|costs?\b|the price of|trade-?off|gives up|forgo\w*|knowingly)", re.I)


def y_statement(r: Ruling, context: str) -> dict[str, str]:
    """Four quoted parts. The wording is the file's; the frame is fixed.

    `facing` is the first labelled PROBLEM/WHY/QUESTION paragraph, else the
    first paragraph that is not the status line. `decided` is the heading --
    the owner's own one-line ruling -- plus the THE RULE paragraph where one
    exists. `accepting` is a WHAT THIS COSTS paragraph where one exists, else
    the first sentence in the entry that uses a cost word, marked as such,
    else a statement that none is recorded.
    """
    def pick(patterns: Sequence[str]) -> str:
        for pat in patterns:
            for label, text in r.blocks.items():
                if _STATUS_LABEL.match(label):
                    continue
                if re.search(pat, label):
                    return _plain(first_sentence(text))
        return ""
    facing = pick((r"^(THE )?PROBLEM", r"DEADLOCK", r"QUESTION", r"^WHY\b", r"^THE CASE", r"WHAT WAS FOUND", r"THE DEFECT", r"THE FACT", r"^THE GAP", r"^RATIONALE"))
    if not facing:
        status_rest = ""
        for p in r.paragraphs:
            lm = _LABEL.match(p)
            if _STATUS_LABEL.match(_plain(p)[:40]):
                if lm and lm.group("rest").strip() and not status_rest:
                    status_rest = lm.group("rest").strip()
                continue
            if lm and re.search(r"^(THE RULE|RULE|RULING|DECISION)", lm.group("label").upper()):
                continue
            facing = _plain(first_sentence(lm.group("rest") if lm and lm.group("rest") else p))
            if facing:
                break
        if not facing and status_rest:
            # the status line carried the problem after its bold marker
            facing = _plain(first_sentence(status_rest))
    decided = pick((r"^THE RULE", r"^RULE\b", r"^RULING", r"^DECISION", r"^RESOLUTION", r"^THE ANSWER"))
    accepting = pick((r"COST",))
    how = "labelled"
    if not accepting:
        for p in r.paragraphs:
            if _STATUS_LABEL.match(_plain(p)[:40]):
                continue
            for sent in re.split(r"(?<=[.!?])\s+", _plain(p)):
                if _ACCEPT_WORDS.search(sent) and 20 < len(sent) < 400:
                    accepting, how = sent.strip(), "keyword"
                    break
            if accepting:
                break
    if not accepting:
        accepting, how = "no cost is recorded in the entry", "none"
    return {"context": context, "facing": facing or "the entry's opening paragraph is empty",
            "decided": _plain(r.title) if not decided else f"{_plain(r.title)}. {decided}",
            "accepting": accepting, "accepting_how": how}


# --------------------------------------------------------------------------
# config/watchlist.yaml
# --------------------------------------------------------------------------

@dataclass
class Name:
    ticker: str
    name: str
    status: str
    currency: str
    notes: str
    fv_base: float | None
    tier: int | None
    view_registered: date | None
    catalyst_date: date | None
    catalyst_event: str | None
    run_record: str | None
    stop_price: float | None

    @property
    def view_registered_ok(self) -> bool:
        return self.view_registered is not None


def watchlist_names(path: Path = WATCHLIST) -> tuple[list[Name], list[str]]:
    if not path.exists():
        return [], [f"{_name(path)} is not on disk; no name is placed on any step"]
    try:
        from vss.config import load_watchlist
        entries = load_watchlist(path)
    except Exception as exc:  # pragma: no cover - a broken file is a sentence
        return [], [f"{path.name} would not load: {exc}"]
    out = []
    for e in entries:
        g = getattr(e, "growth", None)
        out.append(Name(
            ticker=e.ticker, name=e.name or e.ticker, status=e.status,
            currency=e.currency or "", notes=(e.notes or "").strip(),
            fv_base=e.fv_base, tier=e.tier,
            view_registered=getattr(g, "registered", None) if g else None,
            catalyst_date=e.catalyst_date, catalyst_event=e.catalyst_event,
            run_record=getattr(e, "run_record", None), stop_price=e.stop_price))
    return out, []


# --------------------------------------------------------------------------
# precedents
# --------------------------------------------------------------------------

@dataclass
class Precedent:
    step: str
    ticker: str
    when: date | None
    verdict: str        # a status or a document kind, never composed
    line: str           # verbatim from the source
    href: str           # relative to docs/playbook/
    source: str         # where it came from


def rel(path: Path) -> str:
    """A link from docs/playbook/ to a repository file. A path outside the
    repository (a test fixture) links by its absolute form."""
    try:
        return "../../" + path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_uri()


STATUS_STEP = {"HELD": "held", "WATCH-PRICED": "watch-priced",
               "WATCH-GATED": "watch-gated", "PIPELINE": "pipeline",
               "INTAKE": "intake", "DROPPED": "dropped"}

_DOC_KIND_STEP = {"STRIKE": "strike", "DROP": "dropped", "GATED": "watch-gated",
                  "CHAIN": "verdict", "BRIEFING": "intake", "INTAKE": "intake",
                  "reading": "hard-kills", "PREBUY": "entry", "REVIEW": "hard-kills",
                  "METHOD-C": "strike", "BRAND-EVIDENCE": "hard-kills",
                  "REFRESH": "refresh"}

_PATH_IN_TEXT = re.compile(r"(?:reference|reports|config)/[A-Za-z0-9._/-]+\.(?:md|json|yaml|csv|txt)")


def _first_heading(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:8]:
            if line.startswith("#"):
                return line.lstrip("#").strip()
    except OSError:
        pass
    return path.stem


def precedents_from_names(names: Sequence[Name]) -> list[Precedent]:
    out = []
    for n in names:
        step = STATUS_STEP.get(n.status)
        if not step:
            continue
        f = ISO.search(n.notes)
        href = rel(WATCHLIST) if WATCHLIST.exists() else "index.html"
        for p in _PATH_IN_TEXT.findall(n.notes):
            if (ROOT / p).exists():
                href = rel(ROOT / p)
                break
        out.append(Precedent(step, n.ticker, _as_date(f.group(1)) if f else None,
                             n.status, first_sentence(n.notes) or "(the notes field is empty)",
                             href, "watchlist notes"))
    return out


def precedents_from_shadow_book(path: Path = SHADOW_BOOK) -> tuple[list[Precedent], list[str]]:
    if not path.exists():
        return [], [f"{_name(path)} is not on disk; the shadow book lists nothing"]
    out = []
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            verdict = (row.get("verdict") or "").strip()
            step = STATUS_STEP.get(verdict, "verdict")
            href = rel(path)
            src = row.get("source") or ""
            for p in _PATH_IN_TEXT.findall(src):
                if (ROOT / p).exists():
                    href = rel(ROOT / p)
                    break
            out.append(Precedent(step, row.get("ticker", "").strip(),
                                 _as_date(row.get("verdict_date", "")), verdict,
                                 first_sentence(row.get("decided_by") or ""), href,
                                 "shadow book"))
    return out, []


_TICKER = re.compile(r"^[A-Z0-9]{1,6}(?:-[A-Z0-9]{1,2})?(?:\.[A-Z]{1,2})?$")

#: Multi-name record files, by the prefix before their date, and the step
#: they belong to. Their first heading is scanned for the names.
_PREFIX_STEP = {"RESTRIKE": "strike", "SALES-RECORD": "exit", "SHADOW-BOOK": "shadow-book",
                "READINESS-TOP20": "strike", "SESSION": "hard-kills", "TRIAGE": "verdict",
                "SOURCES-SIX-NAMES": "basis", "INTAKE": "intake"}


def tickers_from_files() -> set[str]:
    """Names the record knows from file names alone: BRIEFING-<T>-, INTAKE-<T>-,
    <T>-STRIKE-, growth-views/<T>.md. A name read but never entered."""
    out: set[str] = set()
    for d in (REPORTS, REFERENCE):
        if d.exists():
            for p in d.iterdir():
                m = re.match(r"(?:BRIEFING|INTAKE)-([A-Z0-9.-]+?)-\d{4}-\d{2}-\d{2}", p.stem)
                if m and _TICKER.match(m.group(1)):
                    out.add(m.group(1))
                m = re.match(r"([A-Z0-9.-]+?)-(?:STRIKE|DROP|GATED|CHAIN)-\d{4}-\d{2}-\d{2}", p.stem)
                if m and _TICKER.match(m.group(1)):
                    out.add(m.group(1))
    gv = REFERENCE / "growth-views"
    if gv.exists():
        out |= {p.stem for p in gv.iterdir() if p.suffix == ".md"}
    rv = REFERENCE / "reviews"
    if rv.exists():
        out |= {p.name for p in rv.iterdir() if p.is_dir() and _TICKER.match(p.name)}
    return out


def precedents_from_reviews(directory: Path | None = None) -> tuple[list[Precedent], list[str]]:
    """`reference/reviews/<TICKER>/<date>.yaml`, the review session's record
    (`vss review`). Every ANSWERED step lands on its own step page with the
    owner's text, verbatim; a skipped step lands nowhere. The growth view's
    words land on the growth-view step. Nothing is composed: the outcome is
    the owner's word from the step's own vocabulary."""
    directory = directory or (REFERENCE / "reviews")
    if not directory.exists():
        return [], [f"{_name(directory)} is not on disk; no review session is on record"]
    import yaml
    out, problems = [], []
    for path in sorted(directory.glob("*/*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            problems.append(f"{rel(path)}: not readable ({exc})")
            continue
        if not isinstance(raw, dict):
            continue
        ticker = str(raw.get("ticker") or path.parent.name)
        when = _as_date(str(raw.get("date") or path.stem))
        for s in raw.get("steps") or []:
            if not isinstance(s, dict) or s.get("skipped") or not s.get("outcome"):
                continue
            step = str(s.get("step"))
            text = str(s.get("text") or "")
            out.append(Precedent(step, ticker, when, str(s["outcome"]),
                                 first_sentence(text) or "(no words recorded)",
                                 rel(path) + f"#{step}", "review session"))
        g = raw.get("growth_view")
        if isinstance(g, dict) and str(g.get("reasons") or "").strip():
            out.append(Precedent("growth-view", ticker, when, "growth view",
                                 first_sentence(str(g["reasons"])), rel(path) + "#growth_view",
                                 "review session"))
    return out, problems


def precedents_from_files(tickers: Sequence[str]) -> tuple[list[Precedent], list[Path]]:
    """Dated files named for a ticker. Returns what was placed and what was not."""
    known = set(tickers)
    placed, unplaced = [], []
    candidates: list[Path] = []
    for d in (REPORTS, REFERENCE):
        if d.exists():
            candidates += [p for p in d.iterdir() if p.suffix == ".md" and p.is_file()]
    rr = REFERENCE / "run-records"
    if rr.exists():
        candidates += [p for p in rr.iterdir() if p.suffix == ".json"]
    gv = REFERENCE / "growth-views"
    if gv.exists():
        candidates += [p for p in gv.iterdir() if p.suffix == ".md"]
    for p in sorted(candidates):
        stem = p.stem
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", stem):
            continue  # a daily report holds no verdict
        d = ISO.search(stem)
        when = _as_date(d.group(1)) if d else None
        if p.parent == gv:
            placed.append(Precedent("growth-view", stem, _view_date(p), "growth view",
                                    "view registered (the rates are not shown here)", rel(p), "growth view file"))
            continue
        if p.parent == rr:
            t = re.match(r"(.+?)-\d{4}-\d{2}-\d{2}", stem)
            placed.append(Precedent("strike", t.group(1) if t else stem, when, "run record",
                                    stem, rel(p), "run record"))
            continue
        m = re.match(r"(?P<kind>[A-Z]+)-(?P<t>[A-Z0-9.-]+?)-(?P<date>\d{4}-\d{2}-\d{2})", stem)
        if m and m.group("t") in known and m.group("kind") in _DOC_KIND_STEP:
            placed.append(Precedent(_DOC_KIND_STEP[m.group("kind")], m.group("t"), when,
                                    m.group("kind"), _first_heading(p), rel(p), p.parent.name))
            continue
        m = re.match(r"(?P<t>[A-Z0-9.-]+?)-(?P<kind>[A-Za-z0-9-]+?)-(?P<date>\d{4}-\d{2}-\d{2})", stem)
        if m and m.group("t") in known:
            kind = m.group("kind")
            step = next((s for k, s in _DOC_KIND_STEP.items() if kind.startswith(k)), None)
            if step:
                placed.append(Precedent(step, m.group("t"), when, kind, _first_heading(p), rel(p), p.parent.name))
                continue
        prefix = next((k for k in _PREFIX_STEP if stem.startswith(k + "-")), None)
        if prefix and when:
            heading = _first_heading(p)
            found = [t for t in known if re.search(rf"(?<![A-Z0-9.]){re.escape(t)}(?![A-Z0-9.])", heading + " " + stem)]
            for t in found:
                placed.append(Precedent(_PREFIX_STEP[prefix], t, when, prefix, heading, rel(p), p.parent.name))
            if found:
                continue
        unplaced.append(p)
    return placed, unplaced


def _view_date(path: Path) -> date | None:
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:600]
    except OSError:
        return None
    m = ISO.search(head)
    return _as_date(m.group(1)) if m else None


@dataclass
class Commit:
    sha: str
    when: date | None
    subject: str


def git_log(root: Path = ROOT) -> tuple[list[Commit], list[str]]:
    try:
        raw = subprocess.run(["git", "log", "--format=%h%x09%ad%x09%s", "--date=short"],
                             cwd=root, capture_output=True, text=True, timeout=30, check=True).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        return [], [f"git log is unavailable: {exc}"]
    out = []
    for line in raw.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            out.append(Commit(parts[0], _as_date(parts[1]), parts[2]))
    return out, []


_SUBJECT_STEP = (
    (re.compile(r"re-?str(ike|uck)|\bstrike|\bstruck", re.I), "strike"),
    (re.compile(r"briefing", re.I), "intake"),
    (re.compile(r"\bintake", re.I), "intake"),
    (re.compile(r"WATCH-GATED|\bgated\b", re.I), "watch-gated"),
    (re.compile(r"WATCH-PRICED", re.I), "watch-priced"),
    (re.compile(r"\bDROPPED\b|\bdropped\b", re.I), "dropped"),
    (re.compile(r"\bsold\b|\bexit", re.I), "exit"),
    (re.compile(r"growth view|pre-registered", re.I), "growth-view"),
    (re.compile(r"\bstop\b", re.I), "held"),
    (re.compile(r"hard kill|4\.2", re.I), "hard-kills"),
)


def precedents_from_git(commits: Sequence[Commit], names: Sequence[Name],
                        extra: Sequence[str] = ()) -> list[Precedent]:
    current = {n.ticker: STATUS_STEP.get(n.status, "verdict") for n in names}
    for t in extra:
        current.setdefault(t, "intake")
    tickers = sorted(current, key=len, reverse=True)
    out = []
    for c in commits:
        hit = [t for t in tickers if re.search(rf"(?<![A-Z0-9.]){re.escape(t)}(?![A-Z0-9.])", c.subject)]
        if not hit:
            continue
        step = next((s for pat, s in _SUBJECT_STEP if pat.search(c.subject)), None)
        # A commit whose subject names no step is kept on the name's own
        # history (step "commit") and shown on no step's fold.
        for t in hit:
            out.append(Precedent(step or "commit", t, c.when, "commit", c.subject,
                                 f"git-log.html#{c.sha}", "git log"))
    return out


# --------------------------------------------------------------------------
# the CLI's own help
# --------------------------------------------------------------------------

@dataclass
class Command:
    name: str
    usage: str
    help: str          # the one-line help from the top-level parser
    description: str
    options: dict[str, str]   # option string -> help text


def cli_commands() -> tuple[dict[str, Command], list[str]]:
    try:
        from vss.__main__ import build_parser
    except Exception as exc:  # pragma: no cover
        return {}, [f"the CLI parser would not import: {exc}"]
    parser = build_parser()
    out: dict[str, Command] = {}
    for action in parser._actions:
        if not hasattr(action, "choices") or not isinstance(action.choices, dict):
            continue
        helps = {a.dest: a.help for a in action._choices_actions}
        for name, sub in action.choices.items():
            options = {}
            for a in sub._actions:
                if a.option_strings and "-h" not in a.option_strings:
                    options[", ".join(a.option_strings)] = (a.help or "").replace("%(default)s", str(a.default))
            out[name] = Command(name, sub.format_usage().strip(), helps.get(name, "") or "",
                                sub.description or "", options)
    return out, []


def option_known(cmd: Command, flag: str) -> bool:
    return any(flag in key.split(", ") for key in cmd.options)


# --------------------------------------------------------------------------
# the ranked list tonight, from the newest daily report
# --------------------------------------------------------------------------

def ranked_tonight(reports: Path = REPORTS) -> tuple[list[str], str]:
    if not reports.exists():
        return [], "reports/ is not on disk"
    dailies = sorted(p for p in reports.glob("????-??-??.md"))
    if not dailies:
        return [], "no daily report under reports/"
    latest = dailies[-1]
    names, inside = [], False
    for line in latest.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## RANKED WATCH"):
            inside = True
            continue
        if inside and line.startswith("## "):
            break
        if inside:
            m = re.match(r"\|\s*\d+\s*\|\s*`([^`]+)`", line)
            if m:
                names.append(m.group(1))
    return names, f"from {latest.name}"


# --------------------------------------------------------------------------
# the code's own constants, for the disagreement panel
# --------------------------------------------------------------------------

def code_constants() -> dict[str, object]:
    out: dict[str, object] = {}
    try:
        from vss import rules as R
        out["mbp_live"] = dict(R.MBP_TIER_CUSHION_E90)
        out["mbp_kept"] = dict(R.MBP_TIER_MULTIPLIER)
        out["band"] = (R.DISLOCATION_MIN, R.DISLOCATION_MAX)
        out["stale_days"] = R.MAX_CLOSE_AGE_TRADING_DAYS
        out["statuses"] = tuple(R.VALID_STATUSES)
    except Exception as exc:  # pragma: no cover
        out["error"] = str(exc)
    return out


def module_doc(name: str) -> str:
    """The first paragraph of a vss module's docstring, verbatim."""
    try:
        import importlib
        mod = importlib.import_module(f"vss.{name}")
    except Exception:
        return ""
    doc = (mod.__doc__ or "").strip()
    return doc.split("\n\n")[0] if doc else ""


def deploy_units(root: Path = ROOT) -> list[tuple[str, str, str]]:
    """(unit, OnCalendar or ExecStart, Description) for each deploy unit."""
    d = root / "deploy"
    out = []
    if not d.exists():
        return out
    for p in sorted(d.iterdir()):
        if p.suffix not in (".timer", ".service"):
            continue
        desc = when = ""
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("Description="):
                desc = line.split("=", 1)[1]
            if line.startswith(("OnCalendar=", "ExecStart=")):
                when = line.split("=", 1)[1]
        out.append((p.name, when, desc))
    return out
