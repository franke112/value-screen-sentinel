"""E76's BRIEFING: the research a reading stands on, assembled automatically.

**THIS IS RESEARCH AND IT IS NOT A VERDICT.** E76's reading is the owner's
and stays his: this file gathers what the reading needs and stops there.
Every line it writes is either a figure the store or the filer's own tagged
facts already hold, or a VERBATIM QUOTE with the document it came from.
**It never proposes a growth rate and never proposes a fair value**, and a
test holds that line the way `medians` holds "printed, never filtered".

**WHY VERBATIM AND NOT SUMMARISED.** A summary is a judgement wearing a
fact's clothes. The whole of this project's discipline is that a figure
carries where it came from, and a paraphrase cannot: two readers cannot
check it against the page. So the extraction here LOCATES and QUOTES --
it finds the heading, takes the lines beneath it as the filer wrote them,
and prints the accession and the URL beside them. Nothing is compressed.

**WHERE A FILING CANNOT ANSWER, THE WEB IS ASKED -- AND ANSWERS ONLY WITH A
URL.** One section genuinely cannot come out of a filing: *why the price
fell on a given day*. The price series says WHEN, to the day, and the
filings do not say why. That section calls out, and **every claim it keeps
carries the citation the route returned; a claim with no citation is
dropped.** The block is labelled so a reader never mistakes it for a
filing.

**A SECTION THAT CANNOT BE FILLED SAYS SO.** It is never filled with
something adjacent, and the closing section names every gap in one place --
which is the part of the briefing E76's reading actually consumes.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence
from . import env

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
SOURCES_DIR = PROJECT_ROOT / "sources"
RUNS_ROOT = PROJECT_ROOT / "data" / "screener_runs"

SEC_ARCHIVES = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"

#: How far back the insider section looks. E76 says "the trailing twelve
#: months", and it is the ruling's number rather than this file's.
INSIDER_MONTHS = 12

#: How many quarters of revenue and margin the "what has happened" section
#: prints. Eight, so a reader sees the year and the year before it.
QUARTERS = 8

#: A single-day fall this large or larger is a DATED EVENT the briefing
#: asks about. Not a threshold with any meaning in the framework -- it is
#: how the section picks which days to research, and it is stated so a
#: reader knows the list is not exhaustive.
SHARP_FALL = -0.07
MAX_EVENTS = 5

#: What this file may NEVER ASSERT. The check runs over the finished text
#: -- not trusted to the author, because the failure it guards against is
#: exactly the one an author does not notice himself committing, and the
#: web route can commit it on his behalf.
#:
#: **THEY ARE ASSERTIONS AND NOT WORDS.** An earlier cut banned the phrase
#: "fair value" outright and the briefing refused itself for saying *no fair
#: value stands on the watchlist* -- the disclaimer tripping the guard the
#: disclaimer exists to state. And it banned "we believe", which refused
#: CROX for quoting Crocs' own sentence *"we do not believe that we compete
#: directly with any single company"*. **QUOTING A FILER IS NOT ASSERTING**,
#: so fenced blocks are exempt and the patterns match a claim being MADE.
FORBIDDEN: tuple[tuple[str, str], ...] = (
    (r"\bwe believe\b|\bwe expect\b|\bin (my|our) view\b", "a first-person belief"),
    (r"\b(under|over)valued\b|\bintrinsic value\b", "a valuation judgement"),
    (r"\battractive|\bcompelling|\bbargain\b", "a recommendation's vocabulary"),
    (r"\b(too )?(cheap|expensive)\b|\bshould (trade|be worth)\b", "a price opinion"),
    (r"\bfair value of\b|\btarget price\b|\bworth (about |roughly )?[\d$]", "a proposed value"),
    (r"\bgrowth (view|rate|assumption) of\b|\bwe (assume|forecast|project)\b", "a proposed growth rate"),
    (r"\brecommend|\bwe rate\b|\bconviction\b", "a verdict"),
)


class BriefingError(Exception):
    """The briefing cannot be built, and says which part is absent."""


@dataclass
class Section:
    """One part of the briefing: filled from named sources, or NOT filled."""

    key: str
    title: str
    lines: list[str] = field(default_factory=list)
    #: Why it is empty. Non-empty exactly when `lines` is empty, and it is
    #: what the closing section collects.
    why_not: str = ""

    @property
    def filled(self) -> bool:
        return bool(self.lines)

    def render(self) -> list[str]:
        out = [f"## {self.title}", ""]
        if self.filled:
            out += self.lines
        else:
            out += [f"**NOT FILLED.** {self.why_not}"]
        out.append("")
        return out


# --- documents ------------------------------------------------------------


def user_agent(contact: str | None = None) -> str:
    from .xbrl import user_agent as sec_agent
    return sec_agent(contact)


def _get(url: str, contact: str | None = None, *, opener=None) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent(contact)})
    opener = opener or urllib.request.urlopen
    with opener(request, timeout=120) as response:
        return response.read()


@dataclass(frozen=True)
class Filing:
    form: str
    filed: str
    period: str
    accession: str
    document: str
    cik: int
    items: str = ""        # an 8-K's item codes, "2.02,9.01"; empty otherwise

    @property
    def url(self) -> str:
        return SEC_ARCHIVES.format(cik=self.cik,
                                   accession=self.accession.replace("-", ""),
                                   doc=self.document)

    def cite(self, where: str = "") -> str:
        """The citation this file puts beside every quote.

        AN EDGAR HTML FILING HAS NO PAGE NUMBER, so inventing one would be
        worse than not having it: the citation is the FORM, the ACCESSION,
        the heading the quote sits under, and the URL -- which between them
        take a reader to the exact place.
        """
        heading = f', "{where}"' if where else ""
        return f"{self.form} {self.accession}{heading} — {self.url}"


def submissions(cik: int, *, contact=None, opener=None) -> list[Filing]:
    """Every filing SEC lists as recent for one filer, newest first."""
    raw = _get(SEC_SUBMISSIONS.format(cik=int(cik)), contact, opener=opener)
    recent = json.loads(raw.decode("utf-8"))["filings"]["recent"]
    out: list[Filing] = []
    for i, form in enumerate(recent.get("form", [])):
        def at(key):
            values = recent.get(key) or []
            return str(values[i]) if i < len(values) else ""
        if not at("accessionNumber") or not at("primaryDocument"):
            continue
        out.append(Filing(form=str(form), filed=at("filingDate"),
                          period=at("reportDate"),
                          accession=at("accessionNumber"),
                          document=at("primaryDocument"), cik=int(cik),
                          items=at("items")))
    return out


def detag(raw: str) -> str:
    """An (i)XBRL or HTML filing as text, with table rows kept on one line.

    Rows and cells are what a financial statement IS; flattening them would
    turn a segment table into a column of loose numbers and make a verbatim
    quote unreadable. Cells are separated by a tab and rows by a newline.
    """
    import html as _html

    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    s = re.sub(r"(?i)</t[dh]>", "\t", s)
    s = re.sub(r"(?i)</tr>", "\n", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|div|li|h[1-6]|table)>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", "", s)
    s = _html.unescape(s).replace("\xa0", " ")
    out = []
    for line in s.split("\n"):
        line = re.sub(r"[ ]{2,}", " ", line).strip()
        if line and line != "​":
            out.append(line)
    return "\n".join(out)


def filing_text(filing: Filing, *, root: Path | None = None, contact=None,
                opener=None) -> str:
    """The filing as text, cached under `sources/` so it is fetched once."""
    root = Path(root or SOURCES_DIR)
    root.mkdir(parents=True, exist_ok=True)
    cached = root / f"_briefing_{filing.accession}_{filing.document}.txt"
    if cached.exists():
        return cached.read_text(encoding="utf-8")
    raw = _get(filing.url, contact, opener=opener)
    text = detag(raw.decode("utf-8", "replace"))
    cached.write_text(text, encoding="utf-8")
    return text


# --- locating and quoting -------------------------------------------------


def block_at(text: str, heading: str, *, lines: int = 14,
             stop: str | None = None, after: int = 0, last: bool = False,
             prose: bool = False) -> tuple[int, list[str]]:
    """The lines under a matching heading, verbatim.

    Returns (the index the heading was found at, the lines). Empty where
    the heading is not there -- which is a fact about the filing and is
    reported as one, never filled from a neighbouring section.

    ``last`` takes the FINAL match instead of the first, which is what a
    heading named in the table of contents needs: the contents come before
    the body, always. ``prose`` keeps only lines long enough to be prose
    and free of tabs, which is what a *discussion* needs -- without it the
    step quotes a table's column headers and calls them management's words.
    """
    body = text.split("\n")
    pattern = re.compile(heading, re.I)
    stopper = re.compile(stop, re.I) if stop else None
    starts = [i for i in range(after, len(body)) if pattern.search(body[i])]
    for i in (reversed(starts) if last else starts):
        out: list[str] = []
        for line in body[i + 1: i + 1 + lines * 6]:
            if stopper is not None and stopper.search(line) and out:
                break
            if not line.strip():
                continue
            if prose and (len(line) < 140 or "\t" in line):
                continue
            out.append(line)
            if len(out) >= lines:
                break
        if out:
            return i, out
    return -1, []


def item_body(text: str, item: str, nxt: str, *, lines: int = 8) -> list[str]:
    """The PROSE under `ITEM <n>` -- the body, never the table of contents.

    A 10-K names every item twice: once in the contents at the front and
    once where the item actually is. Taking the first match lands in the
    contents; taking a fixed offset past it lands wherever the contents
    happen to end. So this takes the LAST heading that matches -- the body
    always follows the contents -- and keeps only lines long enough to be
    prose, which drops the page numbers and the table rows an item's
    opening is full of.
    """
    body = text.split("\n")
    start = end = -1
    head = re.compile(rf"^\s*item\s*{item}\.?\b", re.I)
    stop = re.compile(rf"^\s*item\s*{nxt}\.?\b", re.I)
    for i, line in enumerate(body):
        if head.match(line.strip()) and len(line) < 90:
            start = i
    for i in range(start + 1, len(body)):
        if stop.match(body[i].strip()) and len(body[i]) < 90:
            end = i
            break
    if start < 0:
        return []
    out = []
    for line in body[start + 1: end if end > 0 else start + 400]:
        if len(line) >= 140 and "\t" not in line:
            out.append(line)
        if len(out) >= lines:
            break
    return out


def prose_matching(text: str, pattern: str, *, keep: int = 3,
                   least: int = 180) -> list[str]:
    """The first ``keep`` PROSE sentences that match, verbatim.

    **ANCHORED ON THE SENTENCE AND NOT ON A HEADING**, which is what an
    MD&A discussion needs. Crocs' 10-Q puts *"Revenues were $996.3 million
    for the third quarter of 2025, a 6.2% decrease"* under a heading called
    `Revenues`, and so does the income-statement table three lines further
    down -- a heading cannot tell them apart and a length can. A line short
    enough to be a caption, or holding a tab, is a table row.
    """
    matcher = re.compile(pattern, re.I)
    out = []
    for line in text.split("\n"):
        if len(line) >= least and "\t" not in line and matcher.search(line):
            out.append(line)
            if len(out) >= keep:
                break
    return out


def numeric_rows(lines: Sequence[str], *, cells: int = 3) -> int:
    """How many of these lines are a TABLE ROW rather than a caption."""
    count = 0
    for line in lines:
        numbers = re.findall(r"\(?\d[\d,]*\.?\d*\)?", line)
        if len(numbers) >= cells:
            count += 1
    return count


def first_table(text: str, anchors: Sequence[str], *, lines: int = 20,
                stop: str | None = None, rows: int = 3,
                ) -> tuple[str, list[str]]:
    """The first block under any anchor that actually LOOKS like a table.

    **A HEADING IS NOT ENOUGH AND THREE FILERS PROVED IT.** Crocs names
    `Summary Compensation Table` four times and only one is the table; Murphy
    USA splits `Total Number of Shares Purchased` across five lines so the
    phrase never appears whole; Grand Canyon's contents name Item 5 above a
    page number. So every anchor is tried at its FIRST and its LAST match,
    and a block is accepted only when enough of its lines carry numbers to
    be a table. Returns (the anchor that worked, the lines).
    """
    for anchor in anchors:
        for last in (True, False):
            _, block = block_at(text, anchor, lines=lines, stop=stop, last=last)
            if block and numeric_rows(block) >= rows:
                return anchor, block
    return "", []


def quote(lines: Sequence[str], cite: str, *, width: int = 300) -> list[str]:
    """A verbatim block, fenced, with its citation beneath it."""
    if not lines:
        return []
    out = ["```"]
    out += [line[:width] for line in lines]
    out += ["```", f"*{cite}*", ""]
    return out


# --- the sections ---------------------------------------------------------


def business_section(tenk: Filing, text: str) -> Section:
    """What is sold, and the segment revenue table as the filer prints it."""
    section = Section("business", "1. What the business does, and its segments")
    opening = item_body(text, "1", "1A", lines=6)
    if opening:
        section.lines += ["**How the filer describes itself**", ""]
        section.lines += quote(opening, tenk.cite("Item 1. Business"))

    found = False
    for heading in (r"Revenues? by reportable operating segment",
                    r"Revenues? (dis)?aggregated by",
                    r"The following tables? set forth information related to "
                    r"reportable operating segments",
                    r"^(\d+\.\s*)?(OPERATING |REPORTABLE )?SEGMENTS?( AND "
                    r"GEOGRAPHIC INFORMATION)?$"):
        _, table = block_at(
            text, heading, lines=30,
            stop=r"^Reconciliation of|^Table of Contents$|"
                 r"^\d+\.\s+[A-Z]{3,}|^(Contract|Refund) Liabilities$|"
                 r"^(Long-Lived Assets|Geographic)",
            after=200)
        if len(table) >= 6:
            section.lines += ["**Revenue by segment, as printed**", ""]
            section.lines += quote(table, tenk.cite("segment note"))
            found = True
            break
    if not found and not section.lines:
        section.why_not = (
            f"no Item 1 opening and no segment table could be located in "
            f"{tenk.form} {tenk.accession}. The filing was read and the "
            f"headings this step looks for are not in it.")
    elif not found:
        section.lines += [
            "**Segment revenue: NOT LOCATED.** No segment revenue table was "
            f"found in {tenk.form} {tenk.accession} under the headings this "
            "step looks for. A single-segment filer prints none, and that is "
            "the likeliest reason, but this step did not confirm it.", ""]
    return section


def competitors_section(tenk: Filing, text: str, peers: list[dict],
                        ticker: str) -> Section:
    """Who the filer says it competes with, and the measured comparison.

    **THE COMPARISON IS ON FIGURES THIS PROJECT ALREADY MEASURED** -- the
    ranking run's own operating profitability (EBIT / total assets, E43),
    earnings yield and the two five-year median columns -- and on nobody
    else's. It compares against the SECTOR as the screener holds it, which
    is not the same as the competitors the filer names, and it says so.
    """
    section = Section("competitors", "2. Competitors, and how the figures compare")
    _, competition = block_at(text, r"^Competition$", lines=6,
                              stop=r"^(Available Information|Human Capital|"
                                   r"Item 1A|Government Regulation)", after=100)
    if competition:
        section.lines += ["**Who the filer says it competes with, in its own "
                          "words**", ""]
        section.lines += quote(competition, tenk.cite("Item 1, Competition"))
    else:
        section.lines += [
            f"**The filer names no competitors under a `Competition` heading "
            f"in {tenk.form} {tenk.accession}.**", ""]

    mine = next((r for r in peers if r["ticker"] == ticker), None)
    if mine is None:
        section.lines += [
            "**The measured comparison is NOT AVAILABLE:** this ticker is not "
            "in the ranking run this briefing read, so there is nothing to "
            "compare it against on figures this project measured.", ""]
        return section
    sector = mine.get("sector") or ""
    group = [r for r in peers if (r.get("sector") or "") == sector
             and r.get("operating_profitability")]
    group.sort(key=lambda r: -float(r["operating_profitability"] or 0))
    section.lines += [
        f"**Against the {sector or 'unclassified'} names in the same ranking "
        f"run.** THESE ARE NOT THE COMPETITORS THE FILER NAMES -- they are "
        f"the sector as the screener classifies it, which is a different "
        f"list, and the two are printed apart on purpose. Operating "
        f"profitability is EBIT / total assets (E43); the median columns are "
        f"this year against the name's own five-year median (printed, never "
        f"filtered).", "",
        "| | op. profitability | earnings yield | EBIT vs 5y median | FCF vs 5y median |",
        "|---|---:|---:|---:|---:|"]
    for row in group[:12]:
        mark = "**" if row["ticker"] == ticker else ""
        def pct(key):
            value = row.get(key)
            return f"{float(value):.1%}" if value else "--"
        def ratio(key):
            value = row.get(key)
            return f"{float(value):.2f}" if value else "--"
        section.lines.append(
            f"| {mark}{row['ticker']}{mark} | {pct('operating_profitability')} "
            f"| {pct('earnings_yield')} | {ratio('ebit_vs_5y_median')} "
            f"| {ratio('fcf_vs_5y_median')} |")
    section.lines.append("")
    return section


def _quarterly(facts: dict, tags: Sequence[str]) -> dict[tuple[str, str], float]:
    """Three-month duration facts for the first tag that has any."""
    from .xbrl import _is_statement
    for namespace, elements in (facts.get("facts") or {}).items():
        del namespace
        for tag in tags:
            element = elements.get(tag)
            if not element:
                continue
            out: dict[tuple[str, str], float] = {}
            for rows in (element.get("units") or {}).values():
                for row in rows:
                    start, end = row.get("start"), row.get("end")
                    if not start or not end or not _is_statement(row):
                        continue
                    first, last = date.fromisoformat(start), date.fromisoformat(end)
                    if not 80 <= (last - first).days <= 100:
                        continue
                    out[(start, end)] = float(row["val"])
            if out:
                return out
    return {}


def quarters_section(facts: dict, quarterlies: Sequence[tuple[Filing, str]],
                     ) -> Section:
    """Revenue and margin by quarter, and what the filer said about each.

    The figures are the filer's OWN TAGGED FACTS, three-month durations
    from a statement form. **The margin is a ratio of two of them and is
    labelled as computed** -- it is printed, and nothing in this file is
    read by anything that decides.
    """
    section = Section("quarters", "3. What has happened, quarter by quarter")
    revenue = _quarterly(facts, ("RevenueFromContractWithCustomerExcludingAssessedTax",
                                 "Revenues", "RevenueFromContractWithCustomerIncludingAssessedTax"))
    operating = _quarterly(facts, ("OperatingIncomeLoss",))
    if not revenue:
        section.why_not = (
            "the filer tags no three-month revenue fact on any statement "
            "form, so there is no quarterly series to print. Its annual "
            "figures are in the store.")
        return section
    windows = sorted(revenue)[-QUARTERS:]
    section.lines += [
        "**The filer's own tagged three-month facts.** The margin is "
        "operating income over revenue, COMPUTED from the two beside it and "
        "labelled so. **A FOURTH QUARTER IS USUALLY ABSENT AND THAT IS NOT A "
        "HOLE:** US filers stopped tagging the discrete fourth quarter when "
        "the SEC dropped Selected Quarterly Financial Data in 2021, so the "
        "series below runs Q1-Q3 for most filers. The year is in the store.",
        "",
        "| quarter ends | revenue | operating income | margin (computed) |",
        "|---|---:|---:|---:|"]
    for window in windows:
        rev, op = revenue[window], operating.get(window)
        margin = f"{op / rev:.1%}" if op is not None and rev else "--"
        section.lines.append(
            f"| {window[1]} | {rev:,.0f} | "
            f"{op:,.0f} | {margin} |" if op is not None else
            f"| {window[1]} | {rev:,.0f} | DATA MISSING | -- |")
    section.lines.append("")

    said = 0
    for filing, text in quarterlies:
        body = prose_matching(
            text,
            r"^(Revenues?|Net revenues?|Net sales|Total revenues?)[\s.,]")
        if body:
            section.lines += [
                f"**{filing.form}, period ending {filing.period}, in the "
                f"filer's own words**", ""]
            section.lines += quote(body, filing.cite(
                "Management's Discussion and Analysis"), width=700)
            said += 1
    if not said:
        section.lines += [
            "**What management said about each quarter: NOT LOCATED.** The "
            "10-Q filings were read and no `Results of Operations` or "
            "`Revenues` discussion could be located under the headings this "
            "step looks for.", ""]
    return section


def price_section(ticker: str, closes: Sequence[tuple[date, float]],
                  ask: Callable[[str], tuple[str, list[str]]] | None) -> Section:
    """WHEN the price fell, from our own series, and WHY, from the web.

    **THE TWO HALVES HAVE DIFFERENT STANDING AND ARE PRINTED APART.** The
    dates and the falls are measured off the price series this project
    already holds. The reason is not in any filing -- a 10-K does not say
    why the shares fell on a Thursday -- so it is asked of the web, and
    **every claim kept carries the citation the route returned. A claim
    with no citation is dropped.**
    """
    section = Section("price", "4. Why the price fell — the dated events")
    if len(closes) < 2:
        section.why_not = (
            f"no price history for {ticker} is cached, so no dated fall can "
            f"be measured. Nothing here is guessed from a filing.")
        return section
    peak_date, peak = max(closes[-260:], key=lambda p: p[1])
    last_date, last = closes[-1]
    section.lines += [
        f"**Measured off the cached series.** 52-week closing high "
        f"{peak:,.2f} on {peak_date.isoformat()}; last close {last:,.2f} on "
        f"{last_date.isoformat()}; drawdown "
        f"{(last / peak - 1):.1%}.", ""]
    # THE WINDOW IS SLICED ONCE AND THEN WALKED IN PAIRS. Slicing twice at
    # [-260:] and [-259:] gives the same list back for any series shorter
    # than 260 and pairs every day with ITSELF, so no fall is ever found --
    # which is exactly the shape a test with two closes exposed.
    window = closes[-260:]
    falls = []
    for (_before, prior), (when, close) in zip(window, window[1:]):
        if prior and (close / prior - 1) <= SHARP_FALL:
            falls.append((when, close / prior - 1))
    falls.sort(key=lambda p: p[1])
    falls = falls[:MAX_EVENTS]
    if not falls:
        section.lines += [
            f"**No single session in the last 260 fell {abs(SHARP_FALL):.0%} "
            f"or more**, so this step has no dated event to research. The "
            f"drawdown above was not made in one day.", ""]
        return section
    section.lines += [f"**{len(falls)} session(s) fell {abs(SHARP_FALL):.0%} "
                      f"or more.** Largest first.", ""]
    for when, move in falls:
        section.lines.append(f"- **{when.isoformat()}: {move:.1%}**")
        if ask is None:
            section.lines.append(
                "  - *the web route was not available on this run, so the "
                "reason is NOT FILLED*")
            continue
        answer, citations = ask(
            f"What happened to {ticker} shares on {when.isoformat()}? "
            f"They fell {abs(move):.0%} that session. Answer in one sentence, "
            f"stating only what a cited source reports.")
        if not citations:
            section.lines.append(
                "  - *the web route returned no citation, so nothing is "
                "kept: an uncited claim is dropped rather than printed*")
            continue
        section.lines.append(f"  - {answer.strip()}")
        for url in citations:
            section.lines.append(f"    - {url}")
    section.lines += ["", "*The reasons above are WEB-SOURCED, not from a "
                      "filing, and each carries the URL the route returned.*",
                      ""]
    return section


#: Cash-flow elements the capital-allocation section reads, in the order a
#: reader wants them. Each is a us-gaap element the filer tags itself; NONE
#: is derived and nothing is netted against anything.
CAPITAL_TAGS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("share repurchases", ("PaymentsForRepurchaseOfCommonStock",)),
    ("dividends paid", ("PaymentsOfDividendsCommonStock", "PaymentsOfDividends")),
    ("acquisitions, net of cash", ("PaymentsToAcquireBusinessesNetOfCashAcquired",)),
    ("capital expenditure", ("PaymentsToAcquirePropertyPlantAndEquipment",
                             "PaymentsToAcquireProductiveAssets")),
    ("debt raised", ("ProceedsFromIssuanceOfLongTermDebt",
                     "ProceedsFromLinesOfCredit", "ProceedsFromNotesPayable")),
    ("debt repaid", ("RepaymentsOfLongTermDebt", "RepaymentsOfLinesOfCredit",
                     "RepaymentsOfNotesPayable")),
)


def _annual(facts: dict, tags: Sequence[str]) -> dict[int, float]:
    from .xbrl import _is_statement
    for namespace, elements in (facts.get("facts") or {}).items():
        del namespace
        for tag in tags:
            element = elements.get(tag)
            if not element:
                continue
            out: dict[int, float] = {}
            for rows in (element.get("units") or {}).values():
                for row in rows:
                    start, end = row.get("start"), row.get("end")
                    if not start or not end or not _is_statement(row):
                        continue
                    first, last = date.fromisoformat(start), date.fromisoformat(end)
                    if 330 <= (last - first).days <= 400:
                        out[last.year] = float(row["val"])
            if out:
                return out
    return {}


def capital_section(facts: dict, tenk: Filing, text: str,
                    fv_base: float | None) -> Section:
    """What the cash went on, and at what price the shares were bought."""
    section = Section("capital", "5. Capital allocation")
    rows = {label: _annual(facts, tags) for label, tags in CAPITAL_TAGS}
    years = sorted({y for series in rows.values() for y in series})[-3:]
    if years:
        section.lines += [
            "**From the filer's own tagged annual cash-flow facts.** An "
            "element the filer does not tag is DATA MISSING and is printed "
            "as such; nothing is derived and nothing is netted.", "",
            "| | " + " | ".join(str(y) for y in years) + " |",
            "|---|" + "---:|" * len(years)]
        for label, _tags in CAPITAL_TAGS:
            cells = []
            for year in years:
                value = rows[label].get(year)
                cells.append(f"{value:,.0f}" if value is not None else "DATA MISSING")
            section.lines.append(f"| {label} | " + " | ".join(cells) + " |")
        section.lines.append("")
    else:
        section.lines += ["**No annual cash-flow element this step reads is "
                          "tagged by the filer.**", ""]

    _, table = first_table(
        text,
        (r"^Issuer Purchases of Equity Securities\s*$",
         r"Total Number of Shares Purchased",
         r"Average Price Paid [Pp]er Share"),
        lines=16, stop=r"^(Item 6|ITEM 6|Equity Compensation Plan|"
                       r"Table of Contents)")
    if table:
        section.lines += [
            "**What was paid for the shares, as the filer prints it** "
            "(Item 5, the monthly repurchase table)", ""]
        section.lines += quote(table, tenk.cite("Item 5, issuer purchases"))
    else:
        section.lines += [
            "**The average price paid: NOT LOCATED.** No Item 5 issuer-"
            f"purchase table was found in {tenk.form} {tenk.accession}. A "
            "filer that repurchased nothing in the fourth quarter prints "
            "none, and that is the likeliest reason.", ""]

    if fv_base is None:
        section.lines += [
            "**Against `fv_base`: NOT POSSIBLE.** No fair value stands on "
            "the watchlist for this name, so there is nothing to measure the "
            "prices paid against. E76 calls this one of the few places "
            "management's judgement is directly measurable against the "
            "owner's, and it cannot be done until he strikes one.", ""]
    else:
        section.lines += [
            f"**Against `fv_base` {fv_base:,.2f}**, which is the figure on "
            f"the watchlist and not one struck here. The prices in the table "
            f"above are the comparison; this step does not compute the "
            f"difference, because the table's own average is the filer's and "
            f"the arithmetic is the reader's.", ""]
    return section


def ceo_section(proxy: Filing | None, text: str,
                ask: Callable[[str], tuple[str, list[str]]] | None,
                company: str) -> Section:
    """Who runs it, since when, what they did before, and what they are paid."""
    section = Section("ceo", "6. The CEO")
    if proxy is None:
        section.why_not = ("no DEF 14A is among the filer's recent filings, "
                           "so tenure, background and pay have no primary "
                           "source here. Nothing is taken from elsewhere.")
        return section
    found = False
    # THE HEADING APPEARS FOUR TIMES IN A PROXY and only one of them is the
    # table: the contents name it, the CD&A cross-refers to it, and the pay-
    # versus-performance note explains what it excludes. The TABLE is the
    # one whose next lines are the column headers, so that is the anchor.
    # A PROXY SPLITS ITS COLUMN HEADERS OVER AS MANY LINES AS THE TYPE
    # NEEDS. Murphy USA's `NAME AND` / `PRINCIPAL POSITION` sit on two, and
    # twenty-seven lines of header stand between the anchor and the first
    # row -- so the window is wide and the acceptance is on the ROWS.
    _, pay = first_table(
        text,
        (r"^Name and Principal Position\b", r"^NAME AND\s*$",
         r"^PRINCIPAL POSITION\s*$",
         r"^(\d{4} )?Summary Compensation Table\s*$",
         r"^SUMMARY COMPENSATION TABLE\s*$"),
        lines=44, rows=4,
        stop=r"^\(1\)Reflects|^Grants of Plan|^Pay Versus Performance|"
             r"^CEO Pay Ratio")
    if pay:
        section.lines += ["**What the CEO is paid, as the proxy prints it** "
                          "(Summary Compensation Table)", ""]
        section.lines += quote(pay, proxy.cite("Summary Compensation Table"))
        found = True
    bio = prose_matching(
        text, r"(has served as|has been) (our |the )?(President and )?"
              r"Chief Executive Officer", keep=2, least=200)
    if not bio:
        bio = prose_matching(text, r"Chief Executive Officer since", keep=2,
                             least=200)
    if bio:
        section.lines += ["**Background, as the proxy states it**", ""]
        section.lines += quote(bio, proxy.cite("director and officer biography"),
                               width=900)
        found = True
    if not found:
        section.lines += [
            f"**NOT LOCATED in {proxy.form} {proxy.accession}.** Neither a "
            f"`Summary Compensation Table` nor a chief-executive biography "
            f"could be found under the headings this step looks for.", ""]
    if ask is not None:
        answer, citations = ask(
            f"Who is the chief executive of {company}, when were they "
            f"appointed, what did they do immediately before, and what were "
            f"they publicly said to have been hired to do? Answer in at most "
            f"three sentences, stating only what a cited source reports.")
        if citations:
            section.lines += ["**Tenure and what they were hired to do "
                              "(WEB-SOURCED, not a filing)**", "",
                              answer.strip(), ""]
            section.lines += [f"- {url}" for url in citations] + [""]
        else:
            section.lines += [
                "**Tenure and what they were hired to do: NOT FILLED.** The "
                "web route returned no citation, and an uncited claim about a "
                "person is dropped rather than printed.", ""]
    else:
        section.lines += [
            "**Tenure and what they were hired to do: NOT FILLED.** The web "
            "route was not available on this run, and the proxy does not "
            "state it in the sections this step reads.", ""]
    return section


#: Form 4 transaction codes this step reports. E76 wants OPEN-MARKET
#: transactions, and the code is what says which they are: `P` is an
#: open-market or private PURCHASE and `S` an open-market or private SALE.
#: **`A` and `M` are deliberately excluded** -- a grant and an option
#: exercise are not somebody choosing to buy at the price on the screen,
#: and folding them in is how an insider "buy" gets reported that nobody
#: made. They are counted and named, never listed as transactions.
OPEN_MARKET = {"P": "PURCHASE", "S": "SALE"}


@dataclass(frozen=True)
class InsiderTrade:
    owner: str
    title: str
    when: date
    code: str
    shares: float
    price: float | None
    plan: bool          # reported under a Rule 10b5-1 trading plan
    url: str


def _tag(xml: str, name: str) -> list[str]:
    out = []
    for block in re.findall(rf"<{name}\b[^>]*>(.*?)</{name}>", xml, re.S):
        out.append(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", block)).strip())
    return out


def insider_trades(filings: Sequence[Filing], *, since: date, contact=None,
                   opener=None, root: Path | None = None,
                   ) -> tuple[list[InsiderTrade], int]:
    """Every open-market Form 4 transaction since `since`, never netted.

    Returns (the trades, how many non-open-market lines were skipped). E76
    is explicit that buys and sells are reported SEPARATELY and never
    netted, and that a scheduled sale is not the evidence an open-market
    purchase is -- so the plan flag travels with each line.
    """
    root = Path(root or SOURCES_DIR)
    root.mkdir(parents=True, exist_ok=True)
    trades: list[InsiderTrade] = []
    skipped = 0
    for filing in filings:
        if filing.form != "4" or not filing.filed:
            continue
        if date.fromisoformat(filing.filed) < since:
            continue
        document = filing.document.split("/")[-1]
        url = SEC_ARCHIVES.format(cik=filing.cik,
                                  accession=filing.accession.replace("-", ""),
                                  doc=document)
        cached = root / f"_briefing_{filing.accession}_{document}"
        if cached.exists():
            xml = cached.read_text(encoding="utf-8")
        else:
            try:
                xml = _get(url, contact, opener=opener).decode("utf-8", "replace")
            except Exception:      # noqa: BLE001 -- one form is not the run
                continue
            cached.write_text(xml, encoding="utf-8")
        owner = (_tag(xml, "rptOwnerName") or ["?"])[0]
        title = (_tag(xml, "officerTitle") or [""])[0]
        for block in re.findall(r"<nonDerivativeTransaction>(.*?)"
                                r"</nonDerivativeTransaction>", xml, re.S):
            code = (_tag(block, "transactionCode") or [""])[0]
            if code not in OPEN_MARKET:
                skipped += 1
                continue
            when = (_tag(block, "transactionDate") or [""])[0][:10]
            shares = (_tag(block, "transactionShares") or ["0"])[0]
            price = (_tag(block, "transactionPricePerShare") or [""])[0]
            plan = (_tag(block, "aff10b5One") or ["0"])[0] not in ("0", "")
            try:
                trades.append(InsiderTrade(
                    owner=owner, title=title, when=date.fromisoformat(when),
                    code=code, shares=float(shares.replace(",", "")),
                    price=float(price) if price else None, plan=plan, url=url))
            except ValueError:
                skipped += 1
    trades.sort(key=lambda t: t.when, reverse=True)
    return trades, skipped


def insiders_section(trades: Sequence[InsiderTrade], skipped: int,
                     since: date, forms: int) -> Section:
    section = Section("insiders", "7. Insider open-market transactions, "
                                  "last twelve months")
    if forms == 0:
        section.why_not = ("SEC lists no Form 4 for this filer in the "
                           "trailing twelve months.")
        return section
    if not trades:
        section.lines += [
            f"**{forms} Form 4(s) since {since.isoformat()} and NOT ONE "
            f"OPEN-MARKET TRANSACTION among them.** {skipped} line(s) were "
            f"skipped as grants, option exercises, withholding or gifts -- "
            f"codes other than `P` and `S`. That is a finding and not an "
            f"absence of data: the insiders filed, and none of them bought or "
            f"sold in the market.", ""]
        return section
    buys = [t for t in trades if t.code == "P"]
    sells = [t for t in trades if t.code == "S"]
    section.lines += [
        f"**{len(buys)} purchase(s) and {len(sells)} sale(s)** across {forms} "
        f"Form 4(s) filed since {since.isoformat()}. **NEVER NETTED** (E76), "
        f"and each carries whether it was under a Rule 10b5-1 plan -- a "
        f"scheduled sale is not the evidence an open-market purchase is. "
        f"{skipped} line(s) were skipped as grants, option exercises, "
        f"withholding or gifts (codes other than `P` and `S`).", ""]
    for label, group in (("PURCHASES", buys), ("SALES", sells)):
        section.lines += [f"**{label}**", ""]
        if not group:
            section.lines += ["*none*", ""]
            continue
        section.lines += ["| date | who | title | shares | price | 10b5-1 plan | source |",
                          "|---|---|---|---:|---:|---|---|"]
        for t in group:
            price = f"{t.price:,.2f}" if t.price is not None else "not stated"
            section.lines.append(
                f"| {t.when.isoformat()} | {t.owner} | {t.title or '--'} | "
                f"{t.shares:,.0f} | {price} | {'YES' if t.plan else 'no'} | "
                f"[Form 4]({t.url}) |")
        section.lines.append("")
    return section


# --- the web route --------------------------------------------------------


def web_asker(*, model=None, api_key=None, transport=None,
              ) -> Callable[[str], tuple[str, list[str]]] | None:
    """A callable that asks the web ONE question and returns (answer, urls).

    None where no key is set, and the sections then say NOT FILLED rather
    than quietly leaving a hole. **The urls are the route's own citations
    and the caller drops any answer that has none** -- which is the whole
    discipline: this file may print what a source says, never what a model
    recalls.
    """
    from .extract import API_URL, KEY_ENV, MODEL_ENV, DEFAULT_MODEL

    key = api_key or env.get(KEY_ENV)
    if not key:
        return None
    chosen = model or env.get(MODEL_ENV, DEFAULT_MODEL)

    def ask(question: str) -> tuple[str, list[str]]:
        payload = json.dumps({
            "model": chosen,
            "plugins": [{"id": "web", "max_results": 3}],
            "temperature": 0,
            "messages": [
                {"role": "system", "content":
                 "You are a research assistant assembling sourced facts. "
                 "State only what a cited source reports. Do not speculate, "
                 "do not value anything, do not forecast, and never say "
                 "whether a share is cheap or dear. If the sources do not "
                 "answer, say so in one sentence."},
                {"role": "user", "content": question},
            ],
        }).encode("utf-8")
        request = urllib.request.Request(
            API_URL, data=payload,
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"})
        try:
            opener = transport or urllib.request.urlopen
            with opener(request, timeout=180) as response:
                body = json.loads(response.read().decode("utf-8"))
            message = body["choices"][0]["message"]
        except Exception:      # noqa: BLE001 -- a route failure is NOT FILLED
            return "", []
        # KEEP THE SOURCE'S NAME AND DROP ONLY THE LINK. Stripping the
        # whole markdown link left sentences reading "According to , MUSA
        # closed at..." -- the citation removed along with the attribution
        # it carried. The URLs are printed beneath, from the annotations.
        text = re.sub(r"\[([^\]]*)\]\(https?://[^)]*\)", r"\1",
                      message.get("content") or "").strip()
        urls, seen = [], set()
        for note in message.get("annotations") or []:
            url = (note.get("url_citation") or {}).get("url")
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
        return re.sub(r"\s{2,}", " ", text), urls

    return ask


# --- assembly -------------------------------------------------------------


def unanswered_section(sections: Sequence[Section]) -> Section:
    """Every gap, in one place. **This is the part E76's reading consumes.**"""
    section = Section("unanswered", "8. What this could NOT answer")
    empty = [s for s in sections if not s.filled]
    partial = [s for s in sections if s.filled and any(
        "NOT FILLED" in line or "NOT LOCATED" in line or "NOT POSSIBLE" in line
        or "NOT AVAILABLE" in line for line in s.lines)]
    if not empty and not partial:
        section.lines += ["Every section above was filled from a named "
                          "source. **That is not the same as complete:** it "
                          "means nothing this step looks for was absent, and "
                          "the step looks for a fixed list.", ""]
        return section
    for s in empty:
        section.lines.append(f"- **{s.title} — NOT FILLED.** {s.why_not}")
    for s in partial:
        for line in s.lines:
            if any(k in line for k in ("NOT FILLED", "NOT LOCATED",
                                       "NOT POSSIBLE", "NOT AVAILABLE")):
                section.lines.append(
                    f"- **{s.title}** — " + re.sub(r"\*+", "", line).strip()[:400])
    section.lines.append("")
    return section


def judgement_in(text: str) -> list[str]:
    """Every judgement this file may never make, found in the finished text.

    **VERBATIM QUOTES ARE EXEMPT AND NOTHING ELSE IS.** A fenced block is
    the filer speaking, and a filer is entitled to say "we believe" about
    its own competition; reproducing that sentence is reporting, not
    asserting. Every line OUTSIDE a fence is this file speaking, including
    anything the web route handed it, and every one of them is checked.
    """
    problems: list[str] = []
    fenced = False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        for pattern, what in FORBIDDEN:
            match = re.search(pattern, line, re.I)
            if match:
                problems.append(f"{what}: {match.group(0)!r} in "
                                f"{line.strip()[:110]!r}")
    return problems


def ranking_rows(runs_root: Path | None = None) -> list[dict]:
    """The newest ranking run's rows, or an empty list."""
    import csv

    root = Path(runs_root or RUNS_ROOT)
    runs = sorted(p for p in root.glob("*/ranking.csv")) if root.exists() else []
    if not runs:
        return []
    with runs[-1].open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def cached_closes(ticker: str) -> list[tuple[date, float]]:
    """The settled closes this project already holds, oldest first."""
    try:
        from .fetch import get_history
        from .runner import CACHE_DIR
        fetched = get_history(ticker, CACHE_DIR,
                              now=datetime.now(timezone.utc), write=False)
        frame = fetched.frame
    except Exception:      # noqa: BLE001 -- no cache is NOT FILLED, not a crash
        return []
    out: list[tuple[date, float]] = []
    for stamp, close in zip(frame.index, frame["Close"]):
        try:
            out.append((stamp.date(), float(close)))
        except Exception:      # noqa: BLE001
            continue
    return [row for row in out if row[1] == row[1]]


def build(ticker: str, *, cik: int, company: str, as_of: date | None = None,
          contact=None, ask=None, sources_root: Path | None = None,
          runs_root: Path | None = None, fv_base: float | None = None,
          opener=None) -> str:
    """The whole briefing, as markdown. **Research, never a verdict.**"""
    as_of = as_of or date.today()
    filings = submissions(int(cik), contact=contact, opener=opener)
    if not filings:
        raise BriefingError(f"SEC lists no recent filing for CIK {cik}")

    def newest(form: str) -> Filing | None:
        return next((f for f in filings if f.form == form), None)

    tenk = newest("10-K") or newest("20-F")
    if tenk is None:
        raise BriefingError(
            f"no 10-K or 20-F among CIK {cik}'s recent filings, and the "
            f"business, competitor and capital-allocation sections all read "
            f"one. A briefing without them would be three eighths of a "
            f"briefing wearing the name of a whole one.")
    tenk_text = filing_text(tenk, root=sources_root, contact=contact,
                            opener=opener)
    quarterlies = []
    for filing in [f for f in filings if f.form == "10-Q"][:3]:
        try:
            quarterlies.append((filing, filing_text(
                filing, root=sources_root, contact=contact, opener=opener)))
        except Exception:      # noqa: BLE001 -- one filing is not the run
            continue
    proxy = newest("DEF 14A")
    proxy_text = ""
    if proxy is not None:
        try:
            proxy_text = filing_text(proxy, root=sources_root, contact=contact,
                                     opener=opener)
        except Exception:      # noqa: BLE001
            proxy = None

    from .xbrl import fetch_company_facts
    try:
        facts = fetch_company_facts(int(cik), contact=contact)
    except Exception:      # noqa: BLE001
        facts = {}

    since = as_of - timedelta(days=INSIDER_MONTHS * 31)
    form4s = [f for f in filings if f.form == "4" and f.filed
              and date.fromisoformat(f.filed) >= since]
    trades, skipped = insider_trades(form4s, since=since, contact=contact,
                                     opener=opener, root=sources_root)

    sections = [
        business_section(tenk, tenk_text),
        competitors_section(tenk, tenk_text, ranking_rows(runs_root), ticker),
        quarters_section(facts, quarterlies),
        price_section(ticker, cached_closes(ticker), ask),
        capital_section(facts, tenk, tenk_text, fv_base),
        ceo_section(proxy, proxy_text, ask, company),
        insiders_section(trades, skipped, since, len(form4s)),
    ]
    sections.append(unanswered_section(sections))

    head = [
        f"# Briefing — {company} ({ticker}) — {as_of.isoformat()}",
        "",
        "**RESEARCHED, NOT DICTATED.** This is the material E76's reading "
        "stands on and it is not the reading. It contains no judgement, no "
        "thesis, no growth rate and no fair value, and a check over the "
        "finished text refuses it if it does. **The E76 verdict is the "
        "owner's to dictate after reading this.**",
        "",
        "**Everything below is either a figure the filer tagged itself or a "
        "VERBATIM QUOTE with the filing it came from.** Nothing is "
        "summarised. Where the web was asked -- which is where a filing "
        "cannot answer -- the block says so and every claim carries the URL "
        "the route returned; an uncited claim is dropped rather than "
        "printed.",
        "",
        f"Sources read: `{tenk.form} {tenk.accession}`"
        + (f", {len(quarterlies)} 10-Q(s)" if quarterlies else "")
        + (f", `{proxy.form} {proxy.accession}`" if proxy else "")
        + (f", {len(form4s)} Form 4(s)" if form4s else "")
        + (", SEC companyfacts" if facts else "")
        + ".",
        "",
    ]
    body: list[str] = []
    for section in sections:
        body += section.render()
    text = "\n".join(head + body)
    found = judgement_in(text)
    if found:
        raise BriefingError(
            f"the finished briefing for {ticker} MAKES A JUDGEMENT, and this "
            f"file may make none -- no thesis, no growth rate, no valuation. "
            f"E76's verdict is the owner's to dictate and the briefing is "
            f"only the research it stands on. Nothing was written. Found: "
            + "; ".join(found[:6]))
    return text


def run_briefing(*, ticker: str, cik: int | None = None, as_of: date | None = None,
                 write: bool = False, watchlist_path=None, contact=None,
                 web: bool = True) -> tuple[int, str]:
    """`vss briefing`. Returns (exit code, the briefing or the reason)."""
    from pathlib import Path as _Path

    from .config import load_watchlist
    from .manual import MANUAL_DIR, load_manual, section5_basis
    from .runner import WATCHLIST_PATH

    as_of = as_of or date.today()
    entry = next((e for e in load_watchlist(_Path(watchlist_path or WATCHLIST_PATH))
                  if e.ticker.upper() == ticker.upper()), None)
    parsed = load_manual(ticker, directory=MANUAL_DIR)
    if section5_basis(parsed) is None:
        return 2, (f"{ticker}: the store supplies no twelve-month basis, so "
                   f"the store is not complete and E76's briefing is not the "
                   f"next step. Build the store first.")
    cik = cik or (entry.cik if entry else None) or parsed.cik
    if cik is None:
        return 2, (f"{ticker}: no CIK on the watchlist entry or in the store, "
                   f"and every source this step reads is addressed by CIK. "
                   f"Nothing here looks one up.")
    company = (entry.name if entry else None) or parsed.name or ticker
    text = build(ticker, cik=int(cik), company=" ".join(str(company).split()),
                 as_of=as_of, contact=contact,
                 ask=web_asker() if web else None,
                 fv_base=(entry.fv_base if entry else None))
    if write:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORTS_DIR / f"BRIEFING-{ticker}-{as_of.isoformat()}.md"
        path.write_text(text + "\n", encoding="utf-8")
        return 0, f"{text}\n\n*Written to `{path}`.*"
    return 0, text
