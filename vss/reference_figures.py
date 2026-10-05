"""E103: the issuer's own free cash flow and net debt, fetched automatically.

**WHY THIS MODULE MAY DO WHAT NO OTHER EXTRACTION PATH MAY.** Everything
else that reads a figure into `config/manual/` proposes it and stops; the
owner enters it by hand and reads it back (E40). This one WRITES, and enters
what it wrote UNVERIFIED — because E103 draws a line nothing before it drew:

    A BASIS FIGURE ENTERS A VALUATION.
    A REFERENCE FIGURE IS ONLY EVER COMPARED AGAINST ONE.

A wrong basis figure produces a **wrong value** that nothing downstream can
detect. A wrong reference figure produces a **false blink**: E101's detector
says the two disagree, the owner looks, and it turns out to be the
comparator. The cost is one look, and the cost of the alternative — a
comparator nobody ever enters — is the detector not existing at all, which
is exactly where E101 stood on the day it was built.

**THE FENCE THAT MAKES THAT SAFE IS NOT HERE.** It is in `manual.py`:
`REFERENCE_FIELDS`, `reference_fields_in_basis`, and `section5_gate`'s
refusal. If a reference field ever acquires a `5.*` reader, section 5 stops
running. This module writes; that fence is why writing is allowed.

**TWO ROUTES, AND THE FIRST ONE IS EMPTY ON PURPOSE.**

* **SEC XBRL** — and it supplies NEITHER FIELD, for any filer. Free cash
  flow and net debt are both non-GAAP APMs: `us-gaap` has no element for
  either, which `xbrl.OMITTED_FIELDS` has recorded for free cash flow since
  that path was built. This is not a coverage gap to be closed later; it is
  a fact about the taxonomy, and the route is asked anyway so the report can
  say so by name rather than by silence.
* **THE PDF PATH** — the issuer's own report, read by the model
  `vss/extract.py` already uses. This is where every figure will actually
  come from.

**WHAT IS EXTRACTED IS THE ISSUER'S OWN LINE, NOT A DERIVATION.** The model
is asked for a figure the report PRINTS, with the page it is printed on, and
for nothing else. It does not add, net, adjust or annualise — a derived
comparator would be this project's arithmetic wearing the issuer's name, and
the entire value of the check is that the two constructions are independent.
Where the issuer prints no such line the answer is DATA MISSING, which E101
already distinguishes from a disagreement of zero.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Callable, Sequence
from . import env

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANUAL_DIR = PROJECT_ROOT / "config" / "manual"
SOURCES_DIR = PROJECT_ROOT / "sources"

#: The two fields, and what kind of quantity each is. A FLOW is summed over
#: the basis window and needs every period in it; a STOCK is taken at the
#: window's end and needs only the newest. `manual.resolve_on_basis` does
#: the arithmetic; this is here so the report can say how many periods a
#: name still needs.
FIELDS: dict[str, str] = {
    "free_cash_flow_reported": "flow",
    "net_debt_reported": "stock",
}

#: How much of a document reaches the model, and the phrases that decide
#: WHICH part when it does not all fit.
#:
#: **WHY THIS IS NOT A HEAD TRUNCATION.** The first cut sent `text[:120_000]`
#: and CTSH's FY2025 10-K is 370,635 characters: every one of the six
#: occurrences of "free cash flow" sits between offsets 193,439 and 205,133,
#: in MD&A, so the model saw NONE of them and correctly reported that it
#: could not find the line. The document printed `Free cash flow $ 2,665`
#: with its own definition beside it. A null from a document whose relevant
#: pages were never sent is a FALSE ABSENCE, and E101 reads an absence as
#: "the issuer publishes none" -- so the truncation would have entered a
#: fact about the reader as a fact about the filer.
DOCUMENT_CHARS = 120_000
EXCERPT_MARKERS = (
    "free cash flow", "net debt", "net cash provided by operating",
    "cash flows from operating activities", "net financial debt",
)
EXCERPT_WINDOW = 6_000

ROUTE_SEC = "sec-xbrl"
ROUTE_PDF = "pdf (model-read)"
ROUTE_HAND = "hand download"

#: E103: everything this path writes enters UNVERIFIED, and says so on the
#: figure. It is never promoted by anything here -- a status is the owner's
#: to change, and E101's checks are explicitly not authoritative anyway.
STATUS_UNVERIFIED = "UNVERIFIED"

#: What the model is asked for, and the whole prompt is a refusal to derive.
PROMPT = """You are reading a company's own periodic report.

Return STRICT JSON and nothing else:

{"free_cash_flow_reported": {"value": <number or null>, "scale": "<see 4>",
                             "page": "<where>", "quote": "<verbatim line>"},
 "net_debt_reported":       {"value": <number or null>, "scale": "<see 4>",
                             "page": "<where>", "quote": "<verbatim line>"}}

RULES, and every one of them is a refusal:

1. Return ONLY a figure THE REPORT ITSELF PRINTS under that name. Free cash
   flow must be a line the company calls free cash flow. Net debt must be a
   line the company calls net debt.
2. DO NOT DERIVE, ADD, NET, ADJUST OR ANNUALISE ANYTHING. If the report does
   not print the line, the value is null. A figure you computed is worthless
   here: the entire purpose is to compare the company's own construction
   against one built separately, and a derivation destroys that.
3. Net debt is POSITIVE for a company that owes more than it holds, and
   NEGATIVE for a net-cash company. Say which the report shows.
4. UNITS AND SCALE. Put the number in "value" EXACTLY AS THE REPORT PRINTS
   IT -- do not multiply it out -- and put the scale it is printed in in
   "scale", as one of exactly these words:

       "units"      the figure is in whole currency units
       "thousands"  the table says "SEK 000s", "$ thousands"
       "millions"   the table says "SEK m", "$ millions", "EURm"
       "billions"   the table says "$ billions"

   A US 10-K's MD&A usually prints millions; a Nordic interim report
   usually prints millions; a cash flow statement sometimes prints
   thousands. READ THE COLUMN HEADING OR THE TABLE CAPTION and say what it
   says. If you cannot find a stated scale, set "scale": null -- the
   figure will be refused rather than guessed at, and that is correct.
5. If a figure is stated for several periods, take THE PERIOD THIS REPORT IS
   FOR, not a comparative and not a rolling twelve months, unless the
   requested period below says otherwise.
6. "quote" is the line copied verbatim. If you cannot quote it, the value is
   null."""

#: The scale words the model may return, mapped onto `manual.UNIT_SCALE`.
#: "units" is the plain-English spelling of that module's "whole".
SCALE_WORDS: dict[str, str] = {
    "units": "whole", "unit": "whole", "whole": "whole", "ones": "whole",
    "thousands": "thousands", "thousand": "thousands",
    "millions": "millions", "million": "millions",
    "billions": "billions", "billion": "billions",
}


class ReferenceError(RuntimeError):
    """This path could not run. Never raised for an absent FIGURE."""


@dataclass
class Proposal:
    """One reference figure, or the named reason there is none."""

    ticker: str
    field: str
    period: str
    value: float | None = None
    #: The scale the REPORT printed it in -- one of `manual.UNIT_SCALE`'s
    #: keys. The value is stored AS PRINTED and converted to the store's own
    #: `money_unit` at the write, so both numbers are on the page they came
    #: from until the one moment they have to agree.
    scale: str | None = None
    page: str = ""
    quote: str = ""
    route: str = ""
    detail: str = ""

    @property
    def obtained(self) -> bool:
        return self.value is not None

    def line(self) -> str:
        if self.obtained:
            return (f"{self.ticker} {self.period} {self.field} = "
                    f"{self.value:,.0f} [{self.route}] {self.page}")
        return f"{self.ticker} {self.period} {self.field}: {self.detail}"


@dataclass
class TickerPlan:
    """What one name needs, and by which route it can be got."""

    ticker: str
    route: str
    why: str
    basis: str = ""
    #: (field, [periods still without it])
    wanted: dict[str, list[str]] = field(default_factory=dict)
    documents: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not any(self.wanted.values())


# --- route 1: SEC XBRL, which supplies neither and says so ----------------


def sec_reference_figures(cik: int | None) -> tuple[dict, str]:
    """({}, why) — always empty, and the reason is a fact about the taxonomy.

    **NEITHER FIELD IS TAGGED BY ANYBODY.** `us-gaap` has no element for
    free cash flow and none for net debt: both are non-GAAP alternative
    performance measures a company constructs in its own words.
    `xbrl.OMITTED_FIELDS` has said so about free cash flow since that path
    was written — *"a non-GAAP memo with no us-gaap element. Absent, not
    zero."* — and net debt is the same kind of number.

    This is asked anyway, and returns its reason rather than nothing,
    because a route that is EMPTY BY CONSTRUCTION and a route that merely
    found nothing today are different facts and the report must not print
    them the same way. Deriving either from tagged components is the exact
    substitution `vss/xbrl.py` exists not to make — and here it would be
    worse than elsewhere, because a comparator derived from this project's
    own inputs cannot disagree with them.
    """
    if cik is None:
        return {}, ("no CIK on the entry, and the SEC route needs one -- "
                    "though it would supply neither field even with one")
    return {}, ("SEC XBRL supplies NEITHER field for any filer: free cash "
                "flow and net debt are both non-GAAP APMs with no us-gaap "
                "element (xbrl.OMITTED_FIELDS). Deriving them from tagged "
                "components would make the comparator a function of this "
                "project's own inputs, which cannot disagree with them")


# --- route 2: the issuer's own report, read by the model ------------------


def _number(raw) -> float | None:
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip().replace(" ", "").replace(",", "")
    text = text.replace("−", "-").replace("(", "-").replace(")", "")
    try:
        return float(text)
    except ValueError:
        return None


def parse_model_reply(body: str) -> dict[str, dict]:
    """The model's JSON, or ReferenceError. Ambiguity is NEVER a figure."""
    text = (body or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text).strip()
    try:
        document = json.loads(text)
    except ValueError as exc:
        raise ReferenceError(f"the model's reply is not JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise ReferenceError("the model's reply is not an object")
    out: dict[str, dict] = {}
    for name in FIELDS:
        entry = document.get(name)
        if not isinstance(entry, dict):
            out[name] = {"value": None, "page": "", "quote": "",
                         "detail": "the model returned no entry for it"}
            continue
        value = _number(entry.get("value"))
        quote = str(entry.get("quote") or "").strip()
        # A FIGURE WITHOUT ITS LINE IS NOT A FIGURE. The prompt's rule 6,
        # enforced here rather than trusted: a value the model could not
        # quote is one it constructed, and a constructed comparator is
        # worse than none.
        if value is not None and not quote:
            out[name] = {"value": None, "page": "", "quote": "",
                         "detail": "a value with no verbatim line -- refused, "
                                   "because a figure the model cannot quote "
                                   "is one it derived"}
            continue
        scale = SCALE_WORDS.get(
            str(entry.get("scale") or "").strip().lower())
        # A FIGURE WITHOUT ITS SCALE IS NOT A FIGURE EITHER. CTSH's 10-K
        # prints "Free cash flow $ 2,665" in MILLIONS while its store is in
        # WHOLE units; entered raw that is a millionfold error, and E101
        # printed it as a +99,174,384% disagreement -- a false blink big
        # enough to discredit the detector on its first real use.
        if value is not None and scale is None:
            out[name] = {"value": None, "scale": None, "page": "", "quote": "",
                         "detail": "a value with no stated SCALE -- refused. "
                                   "A figure printed in millions entered into "
                                   "a whole-unit store is out by 1e6, and "
                                   "guessing the scale is how that happens"}
            continue
        out[name] = {"value": value, "scale": scale,
                     "page": str(entry.get("page") or "").strip(),
                     "quote": quote,
                     "detail": ("" if value is not None else
                                "the report prints no such line")}
    return out


def document_excerpt(text: str,
                     limit: int = DOCUMENT_CHARS) -> tuple[str, bool]:
    """The whole document, or the parts of it that could carry the figures.

    Returns (text, was_excerpted). Under ``limit`` nothing is cut. Over it,
    the HEAD is kept -- it carries the period, the currency and the scale --
    and a window is taken around every occurrence of a marker phrase, in
    document order, with the gaps marked. Nothing is silently dropped: the
    caller records that the document was excerpted, so a null out of an
    excerpt is never read as "the issuer publishes none".
    """
    if len(text) <= limit:
        return text, False

    head = limit // 4
    spans: list[tuple[int, int]] = [(0, head)]
    lowered = text.lower()
    for marker in EXCERPT_MARKERS:
        start = 0
        while True:
            found = lowered.find(marker, start)
            if found < 0:
                break
            spans.append((max(0, found - EXCERPT_WINDOW // 2),
                          found + EXCERPT_WINDOW // 2))
            start = found + len(marker)

    spans.sort()
    merged: list[list[int]] = []
    for lo, hi in spans:
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])

    out, used = [], 0
    for lo, hi in merged:
        piece = text[lo:hi]
        if used + len(piece) > limit:
            piece = piece[:max(0, limit - used)]
        if not piece:
            break
        out.append(f"\n[...document excerpt from character {lo:,}...]\n"
                   if lo else "")
        out.append(piece)
        used += len(piece)
        if used >= limit:
            break
    return "".join(out), True


def read_document(path: Path, *, period: str, ticker: str,
                  transport=None, model=None, api_key=None) -> dict[str, dict]:
    """Ask the model for both figures out of one report.

    Raises `ReferenceError` where the path CANNOT RUN -- no key, an
    unreadable document, a refused request. That is never confused with the
    report simply not printing a line, which is a value of None.
    """
    from . import source as source_step
    from .extract import API_URL, KEY_ENV, MODEL_ENV, DEFAULT_MODEL

    key = api_key or env.get(KEY_ENV)
    if not key:
        raise ReferenceError(
            f"no API key: set {KEY_ENV} in the environment. vss never embeds "
            f"keys, and E103's automatic route is the model path -- without "
            f"it these figures need a hand download")
    raw = Path(path).read_bytes()
    try:
        text = (source_step.pdf_to_text(raw, where=str(path))
                if source_step.looks_like_pdf(str(path), raw=raw)
                else raw.decode("utf-8", errors="replace"))
    except Exception as exc:  # noqa: BLE001 -- reported as a route failure
        raise ReferenceError(f"{path.name}: not readable ({exc})") from exc
    if not text.strip():
        raise ReferenceError(f"{path.name}: no text could be extracted")

    import urllib.request

    body_text, excerpted = document_excerpt(text)
    note = ("\n\nNOTE: this document was too long to send whole. What follows "
            "is its opening plus every passage mentioning free cash flow, net "
            "debt or operating cash flow, in document order, with gaps "
            "marked. If a figure is not in these passages, say null -- do not "
            "guess at what the omitted pages might have said.\n"
            if excerpted else "")
    payload = json.dumps({
        "model": model or env.get(MODEL_ENV, DEFAULT_MODEL),
        "temperature": 0,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user",
             "content": f"Company: {ticker}. Period wanted: {period}.{note}\n\n"
                        f"{body_text}"},
        ],
    }).encode("utf-8")
    request = urllib.request.Request(
        API_URL, data=payload,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    try:
        opener = transport or urllib.request.urlopen
        with opener(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
        reply = body["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001 -- a route failure, not an absence
        raise ReferenceError(f"the model call failed: "
                             f"{type(exc).__name__}: {exc}") from exc
    return parse_model_reply(reply)


# --- what each name needs -------------------------------------------------


def _label(entry) -> str:
    """A basis holder's period label -- `2026-Q2` or `FY2025`."""
    period = getattr(entry, "period", None)
    if period:
        return str(period)
    year = getattr(entry, "fiscal_year", None)
    return f"FY{year}" if year is not None else str(entry)


def documents_for(ticker: str, root: Path | None = None) -> list[Path]:
    """The issuer's own reports already on disk for this ticker."""
    root = Path(root or SOURCES_DIR)
    if not root.is_dir():
        return []
    return sorted(p for p in root.glob(f"{ticker}_*")
                  if p.suffix.lower() in (".pdf", ".html", ".htm"))


def plan(ticker: str, *, manual_dir: Path | None = None,
         sources_root: Path | None = None, cik: int | None = None) -> TickerPlan:
    """Which reference figures this name still lacks, and how to get them.

    Reads the store; writes nothing. A field is WANTED for a period when the
    basis needs it there and no figure supplies it -- a flow in every period
    of the window, a stock at the window's end (`resolve_on_basis`'s own
    rule, so the plan cannot disagree with what the check will read).
    """
    from .config import ConfigError
    from .manual import load_manual, section5_basis

    try:
        parsed = load_manual(ticker, directory=manual_dir or MANUAL_DIR)
    except (ConfigError, OSError) as exc:
        return TickerPlan(ticker, ROUTE_HAND,
                          f"no store loads for it ({type(exc).__name__})")

    basis = section5_basis(parsed)
    if basis is None:
        return TickerPlan(ticker, ROUTE_HAND,
                          "no twelve-month basis (E19), so there is no window "
                          "to compare anything on")

    # THE BASIS'S OWN HOLDERS, not the file's periods: `basis.holders` is
    # the exact set `resolve_on_basis` reads, so the plan cannot disagree
    # with what the check will look for. A quarterly basis holds four
    # period entries; an "as filed" basis holds one annual entry.
    holders = list(getattr(basis, "holders", ()) or ())
    labels = [_label(h) for h in holders] or [basis.label]
    held: dict[tuple[str, str], bool] = {}
    for entry in holders:
        for name in FIELDS:
            figure = entry.figures.get(name)
            held[(_label(entry), name)] = figure is not None and figure.present

    wanted: dict[str, list[str]] = {}
    for name, kind in FIELDS.items():
        # A FLOW is summed over the window and needs EVERY period in it;
        # a STOCK is taken at the window's end. `resolve_on_basis`'s rule.
        needed = labels if kind == "flow" else labels[-1:]
        wanted[name] = [p for p in needed if not held.get((p, name))]

    documents = documents_for(ticker, sources_root)
    _, sec_why = sec_reference_figures(cik)
    if documents:
        route, why = ROUTE_PDF, (f"{len(documents)} of the issuer's own "
                                 f"report(s) are on disk; {sec_why}")
    elif cik is not None:
        # E103's third route: fetch the DOCUMENT from EDGAR. Not the
        # companyfacts endpoint -- that is empty by construction for both
        # fields -- but the 10-K/10-Q the filer actually wrote.
        route, why = ROUTE_EDGAR, (
            f"no report on disk, but CIK {int(cik)} is on the entry, so the "
            f"10-K/10-Q can be fetched from EDGAR's archive. NOTE: the "
            f"companyfacts endpoint supplies neither field -- {sec_why}")
    else:
        route, why = ROUTE_HAND, (f"no report for this ticker under "
                                  f"`sources/` and no CIK on the entry; "
                                  f"{sec_why}")
    return TickerPlan(ticker, route, why, basis=basis.label, wanted=wanted,
                      documents=[p.name for p in documents])


def _fetch_from_edgar(plan_: "TickerPlan", ticker: str, cik: int | None, *,
                      sources_root=None, manual_dir=None,
                      opener=None) -> tuple["TickerPlan", list["Proposal"]]:
    """Pull each wanted period's 10-K/10-Q into `sources/`, then re-plan.

    Fetching and extracting are kept apart on purpose: the download is a
    fact about EDGAR and the extraction is a fact about the document, and a
    failure in one must not be reported as the other.
    """
    problems: list[Proposal] = []
    periods = sorted({p for names in plan_.wanted.values() for p in names})
    try:
        filings = list_filings(int(cik), opener=opener)
    except ReferenceError as exc:
        for period in periods:
            for name, names in plan_.wanted.items():
                if period in names:
                    problems.append(Proposal(ticker, name, period,
                                             route=ROUTE_EDGAR,
                                             detail=f"EDGAR: {exc}"))
        return plan_, problems

    for period in periods:
        filing = filing_for_period(filings, period)
        if filing is None:
            for name, names in plan_.wanted.items():
                if period in names:
                    problems.append(Proposal(
                        ticker, name, period, route=ROUTE_EDGAR,
                        detail=f"no 10-K/10-Q on EDGAR reports on {period} "
                               f"({len(filings)} filing(s) listed)"))
            continue
        try:
            download_filing(filing, ticker, period, root=sources_root,
                            opener=opener)
        except ReferenceError as exc:
            for name, names in plan_.wanted.items():
                if period in names:
                    problems.append(Proposal(ticker, name, period,
                                             route=ROUTE_EDGAR,
                                             detail=f"EDGAR: {exc}"))
    return (plan(ticker, manual_dir=manual_dir, sources_root=sources_root,
                 cik=cik),
            problems)


def obtain(ticker: str, *, manual_dir: Path | None = None,
           sources_root: Path | None = None, cik: int | None = None,
           reader: Callable | None = None,
           opener: Callable | None = None) -> tuple[TickerPlan, list[Proposal]]:
    """Run both routes for one name. Writes nothing; proposes.

    `reader` is `read_document`'s signature, replaced wholesale in tests.
    """
    plan_ = plan(ticker, manual_dir=manual_dir, sources_root=sources_root,
                 cik=cik)
    proposals: list[Proposal] = []
    if plan_.complete or plan_.route not in (ROUTE_PDF, ROUTE_EDGAR):
        return plan_, proposals

    if plan_.route == ROUTE_EDGAR:
        plan_, fetched = _fetch_from_edgar(plan_, ticker, cik,
                                           sources_root=sources_root,
                                           manual_dir=manual_dir,
                                           opener=opener)
        proposals.extend(fetched)
        if plan_.route != ROUTE_PDF:
            return plan_, proposals

    reader = reader or read_document
    root = Path(sources_root or SOURCES_DIR)
    periods = sorted({p for names in plan_.wanted.values() for p in names})
    for period in periods:
        document = _document_for_period(root, plan_.documents, period)
        if document is None:
            for name, names in plan_.wanted.items():
                if period in names:
                    proposals.append(Proposal(
                        ticker, name, period, route=ROUTE_HAND,
                        detail=f"no report for {period} under `sources/` -- "
                               f"hand download"))
            continue
        try:
            found = reader(root / document, period=period, ticker=ticker)
        except ReferenceError as exc:
            for name, names in plan_.wanted.items():
                if period in names:
                    proposals.append(Proposal(
                        ticker, name, period, route=ROUTE_PDF,
                        detail=f"the model route could not run: {exc}"))
            continue
        for name, names in plan_.wanted.items():
            if period not in names:
                continue
            entry = found.get(name) or {}
            proposals.append(Proposal(
                ticker, name, period, value=entry.get("value"),
                scale=entry.get("scale"),
                page=entry.get("page", ""), quote=entry.get("quote", ""),
                route=ROUTE_PDF,
                detail=entry.get("detail", "") or f"read from {document}"))
    return plan_, proposals


def _document_for_period(root: Path, documents: Sequence[str],
                         period: str) -> str | None:
    """The report that covers ``period``, by the filename convention.

    `sources/` names files `TICKER_PERIOD_kind_date_lang_rev.ext`, so the
    period is matched on the filename and never guessed from the content.
    """
    for name in documents:
        parts = name.split("_")
        if len(parts) > 1 and parts[1] == period:
            return name
    return None


# --- writing what was obtained, UNVERIFIED --------------------------------


def rescale(value: float, stated: str | None,
            store_unit: str | None) -> tuple[float | None, str]:
    """``value``, printed on the ``stated`` scale, in the STORE's units.

    Returns (converted, why-refused). **REFUSES rather than guessing** where
    either scale is unknown: a figure printed in millions entered into a
    whole-unit store is out by a factor of a million, and that is precisely
    how a detector built to catch construction errors comes to print one.

    Nothing is rounded. The store keeps ONE unit per file (`money_unit`) and
    E103's comparators must be on it, or the comparison compares scales.
    """
    from .manual import UNIT_SCALE

    if stated is None:
        return None, ("the report's scale was not stated, so the figure "
                      "cannot be put on the store's unit")
    if store_unit is None:
        return None, ("the store declares no `money_unit`, so there is no "
                      "unit to convert onto (E103 never guesses one)")
    if stated not in UNIT_SCALE or store_unit not in UNIT_SCALE:
        return None, f"unknown scale {stated!r} or store unit {store_unit!r}"
    factor = UNIT_SCALE[stated] / UNIT_SCALE[store_unit]
    return value * factor, ""


def figure_block(name: str, proposal: "Proposal") -> str:
    """One figure entry, as text, with E103's provenance on it.

    UNVERIFIED, and it SAYS WHY it may be: the status is not a shortcut
    anybody took, it is the ruling. A reader months from now must be able to
    see that this figure was written by a machine and that nothing depends
    on it being right.
    """
    quote = (proposal.quote or "").replace('"', "'")[:300]
    page = (proposal.page or "no page stated").replace('"', "'")[:200]
    if proposal.scale:
        page = f"{page} [printed in {proposal.scale}]"
    return (f"      {name}:\n"
            f"        value: {proposal.value:g}\n"
            f'        source: "E103 automatic reference extraction '
            f'({proposal.route})"\n'
            f'        page: "{page} -- verbatim: {quote}"\n'
            f"        status: {STATUS_UNVERIFIED}\n")


def insert_figure(text: str, period: str, block: str) -> str:
    """Put one figure into an existing period's `figures:` block.

    TEXTUAL, deliberately, for the reason `refresh._insert_periods` gives:
    these files carry the rulings in their comments and a round trip
    through a YAML dumper would throw every one away.

    Raises where the period or its `figures:` key cannot be found -- this
    NEVER creates a period, and it never appends to the wrong one.
    """
    lines = text.split("\n")
    head = f"  - period: {period}"
    annual_head = f"  - fiscal_year: {period[2:]}" if period.startswith("FY") else None
    start = None
    for index, line in enumerate(lines):
        if line.rstrip() == head or (annual_head and line.rstrip() == annual_head):
            start = index
            break
    if start is None:
        raise ReferenceError(f"no `{period}` entry in the file to write into")
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        # the next entry begins: stop rather than write into it
        if lines[index].startswith("  - "):
            raise ReferenceError(f"`{period}` has no `figures:` block")
        if stripped == "figures:":
            name = block.strip().split(":", 1)[0].strip()
            for later in range(index + 1, len(lines)):
                if lines[later].startswith("  - ") or (
                        lines[later] and not lines[later][0].isspace()):
                    break
                if (lines[later].startswith("      ")
                        and lines[later].strip().rstrip(":") == name):
                    raise ReferenceError(
                        f"`{period}` already carries `{name}` -- refused. A "
                        f"second key under one `figures:` block is valid YAML "
                        f"that resolves LAST-WINS, so a duplicate would "
                        f"silently decide which figure counts")
            return "\n".join(lines[:index + 1] + block.rstrip("\n").split("\n")
                             + lines[index + 1:])
    raise ReferenceError(f"`{period}` has no `figures:` block")


def write_proposals(ticker: str, proposals: "Sequence[Proposal]", *,
                    manual_dir: Path | None = None) -> tuple[int, list[str]]:
    """Write every obtained figure into the store. Returns (written, notes).

    THREE THINGS THIS DOES THAT `refresh` DID NOT, and the third is the one
    that matters:

    * it NEVER OVERWRITES. A figure the store already holds stands, whatever
      its status -- the owner may have verified it, and a machine must not
      quietly replace a figure a person read back.
    * it writes ATOMICALLY, through a temporary file and `os.replace`, so an
      interrupt cannot leave a half-written store (CODE-REVIEW-2026-09-01
      B2 found the truncating version of this in `refresh`).
    * **IT RE-READS THE FILE AFTERWARDS AND ROLLS BACK IF IT NO LONGER
      LOADS.** A store that stops parsing takes section 5 with it, and the
      failure would surface days later as "the store does not load".
    """
    import os
    import tempfile

    from .config import ConfigError
    from .manual import load_manual

    directory = Path(manual_dir or MANUAL_DIR)
    path = directory / f"{ticker.upper()}.yaml"
    if not path.exists():
        return 0, [f"no store at {path}"]
    original = path.read_text(encoding="utf-8")
    text, written, notes = original, 0, []

    parsed = load_manual(ticker, directory=directory)
    held = {(_label(e), n)
            for e in list(parsed.periods) + list(parsed.annual)
            for n, f in e.figures.items() if f is not None and f.present}

    for proposal in proposals:
        if not proposal.obtained:
            continue
        if (proposal.period, proposal.field) in held:
            notes.append(f"{proposal.period} {proposal.field}: already held, "
                         f"NOT overwritten")
            continue
        # ONTO THE STORE'S OWN UNIT, or not at all.
        converted, refused = rescale(proposal.value, proposal.scale,
                                     parsed.money_unit)
        if converted is None:
            notes.append(f"{proposal.period} {proposal.field}: REFUSED -- "
                         f"{refused}")
            continue
        proposal = replace(proposal, value=converted)
        try:
            text = insert_figure(text, proposal.period,
                                 figure_block(proposal.field, proposal))
        except ReferenceError as exc:
            notes.append(f"{proposal.period} {proposal.field}: {exc}")
            continue
        written += 1

    if not written:
        return 0, notes

    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(directory), delete=False,
        prefix=f".{path.name}.", suffix=".tmp")
    try:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    os.replace(handle.name, path)

    try:
        load_manual(ticker, directory=directory)
    except (ConfigError, OSError) as exc:
        path.write_text(original, encoding="utf-8")
        return 0, notes + [f"ROLLED BACK -- the store stopped loading after "
                           f"the write ({type(exc).__name__}: {exc}). "
                           f"Nothing was changed."]
    return written, notes


# --- the command ----------------------------------------------------------


def report_reference_figures(*, ticker: str | None = None,
                             write: bool = False,
                             manual_dir: Path | None = None,
                             sources_root: Path | None = None,
                             reader: Callable | None = None) -> tuple[int, str]:
    """`vss reference-figures`. Returns (exit code, markdown).

    Says three things per name and never conflates them: what was OBTAINED,
    what needs a HAND DOWNLOAD, and -- for a route that could not run at all
    -- WHY, by name. A route that is empty by construction (SEC XBRL, which
    tags neither field for anybody) and a route that merely found nothing
    are different facts.
    """
    directory = Path(manual_dir or MANUAL_DIR)
    names = ([ticker.upper()] if ticker else
             sorted(p.stem for p in directory.glob("*.yaml")
                    if p.stem != "TEMPLATE"))
    # The CIK the entry carries, so the SEC line says the RIGHT reason. It
    # supplies neither field with a CIK or without one, and a report that
    # blames a missing CIK for that sends the owner to look up a number
    # which would change nothing.
    # THE STORE FIRST, then the watchlist. Ruled by the owner 2026-09-04:
    # a CIK identifies the COMPANY, not the watching of it. Five of these
    # names carry no watchlist entry at all, so the entry could not hold one
    # even where it existed -- and a ticker lookup at runtime can match the
    # wrong company on a re-used or dual-listed symbol and fetch another
    # filer's document with nothing to catch it.
    ciks: dict[str, int | None] = {}
    for name in names:
        try:
            from .manual import load_manual
            ciks[name] = load_manual(name, directory=directory).cik
        except Exception:  # noqa: BLE001 -- the watchlist may still have it
            pass
    try:
        from .config import load_watchlist
        from .runner import WATCHLIST_PATH

        ciks.update({e.ticker.upper(): getattr(e, "cik", None)
                     for e in load_watchlist(WATCHLIST_PATH)
                     if getattr(e, "cik", None) is not None
                     or e.ticker.upper() not in ciks})
    except Exception as exc:  # noqa: BLE001 -- the route is empty either way
        log.warning("E103: watchlist CIKs unavailable (%s); the SEC line "
                    "will read as though none is on file", exc)

    out = [f"# reference figures (E103) — {date.today().isoformat()}", "",
           "*A REFERENCE figure is compared against a valuation and never "
           "used to build one, so it may be fetched automatically and "
           "entered UNVERIFIED. `section5_gate` refuses if one is ever wired "
           "into a basis.*", ""]
    obtained_total = wanted_total = 0
    hand: list[str] = []
    rows: list[str] = []

    for name in names:
        try:
            plan_, proposals = obtain(name, manual_dir=directory,
                                      sources_root=sources_root,
                                      cik=ciks.get(name), reader=reader)
        except Exception as exc:  # noqa: BLE001 -- one name never stops it
            rows.append(f"| `{name}` | — | — | ERROR: "
                        f"{type(exc).__name__}: {exc} |")
            continue
        outstanding = sum(len(v) for v in plan_.wanted.values())
        wanted_total += outstanding
        got = [p for p in proposals if p.obtained]
        obtained_total += len(got)

        if write and got:
            written, notes = write_proposals(name, got, manual_dir=directory)
            for note in notes:
                rows.append(f"| `{name}` | — | — | {note} |")
            detail = f"{written} written UNVERIFIED"
        elif got:
            detail = f"{len(got)} obtained, NOT written (pass `--write`)"
        elif outstanding:
            reasons = {p.detail for p in proposals} or {plan_.why}
            detail = "; ".join(sorted(reasons))[:240] or plan_.why[:240]
            if plan_.route == ROUTE_HAND:
                hand.append(name)
        else:
            detail = "complete — every reference figure is on file"
        rows.append(f"| `{name}` | {plan_.route} | {outstanding} | {detail} |")

    out += [f"- **obtained automatically:** {obtained_total}",
            f"- **still wanted:** {wanted_total}",
            f"- **needing a hand download:** {len(hand)}"
            + (f" — {', '.join(f'`{t}`' for t in hand)}" if hand else ""), ""]
    out += ["| ticker | route | outstanding | what happened |",
            "|---|---|---:|---|"] + rows + [""]
    return 0, "\n".join(out)


# --- route 3: the issuer's own 10-K / 10-Q from EDGAR ---------------------
#
# **THIS IS NOT THE COMPANYFACTS ROUTE, AND THE DISTINCTION IS LOAD-BEARING.**
# `refresh.extract_edgar` and `xbrl.fetch_company_facts` call
# `data.sec.gov/api/xbrl/companyfacts/CIK…json`, which returns TAGGED FACTS.
# Neither reference figure is tagged by anybody -- that is exactly why
# `sec_reference_figures` is empty by construction -- so no amount of
# companyfacts will ever supply them.
#
# What supplies them is the DOCUMENT: the 10-K or 10-Q the filer actually
# wrote, where "free cash flow" and "net debt" appear as prose or as an MD&A
# table if they appear at all. That needs two other endpoints:
#
#     data.sec.gov/submissions/CIK##########.json   -- what was filed, when
#     www.sec.gov/Archives/edgar/data/…             -- the document itself
#
# E103 governs this, not E92. E92 rules what a REFRESH may do and turns on
# its writing into `config/manual/`, a git-tracked configuration directory;
# this route writes a DOCUMENT into `sources/` and then enters REFERENCE
# figures, which is the licence E103 grants and fences.
#
# SEC's access policy is followed rather than worked around: every request
# declares `VSS_SEC_CONTACT`, and a 401/403 is reported as a refusal with the
# variable named -- never retried behind a browser's user-agent.

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
ARCHIVE_URL = ("https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/"
               "{document}")
ROUTE_EDGAR = "edgar 10-K/10-Q"

#: The forms that carry a period's own numbers. 10-K for a fiscal year,
#: 10-Q for a quarter; the amended forms are taken where they are the
#: newest for that period, because an amendment supersedes.
#:
#: **20-F ADDED 2026-09-04, RULED BY THE OWNER.** It is the annual report of
#: a FOREIGN PRIVATE ISSUER and is the same class of document as a 10-K for
#: this purpose. It was left to him rather than assumed because it changes
#: which documents an automated route will fetch. His ground, recorded:
#: SAP.DE's own site refuses automated requests (HTTP 403, measured
#: 2026-08-24, E92's REFUSING_ISSUERS), so **EDGAR is the only route to a
#: document this project may hold for it** -- and without a document E107
#: can record no search, so E106 clause 5 can never bound its leg.
EDGAR_FORMS = ("10-K", "10-K/A", "20-F", "20-F/A", "10-Q", "10-Q/A")

#: How large a filing this route will take. A 10-K with exhibits runs to
#: tens of megabytes; the primary document alone is a few.
MAX_DOCUMENT_BYTES = 25_000_000


@dataclass(frozen=True)
class Filing:
    """One filing EDGAR lists, reduced to what this route needs."""

    form: str
    accession: str
    document: str
    filed: str
    period_end: str
    #: The 8-K item numbers EDGAR lists for this filing, e.g. "2.02,9.01".
    #: Empty for a 10-K or 10-Q, which carry none. Read by `secwatch`:
    #: an earnings RELEASE is an 8-K Item 2.02 and arrives days before the
    #: 10-Q, so a detector that waits for the 10-Q learns late.
    items: str = ""

    @property
    def url(self) -> str:
        return ARCHIVE_URL.format(cik=self.cik, accession=self.accession,
                                  document=self.document)

    cik: int = 0


def list_filings(cik: int, *, contact=None, opener=None,
                 forms: "Sequence[str]" = EDGAR_FORMS) -> list[Filing]:
    """The filer's recent filings of ``forms``, newest first.

    Raises `ReferenceError` where the route cannot run. An empty LIST is a
    filer with no such filing on record, which is a different fact.

    ``forms`` defaults to the annual and quarterly reports this route
    reads. `secwatch` passes 8-K as well: an earnings RELEASE is an 8-K
    Item 2.02 and arrives days before the 10-Q it precedes.
    """
    import urllib.request

    from .xbrl import CONTACT_ENV, XbrlError, user_agent

    try:
        agent = user_agent(contact)
    except XbrlError as exc:
        raise ReferenceError(str(exc)) from exc
    url = SUBMISSIONS_URL.format(cik=int(cik))
    request = urllib.request.Request(
        url, headers={"User-Agent": agent, "Accept-Encoding": "gzip, deflate"})
    try:
        opener = opener or urllib.request.urlopen
        with opener(request, timeout=60) as response:
            raw = response.read(MAX_DOCUMENT_BYTES)
            encoding = ((getattr(response, "headers", None) or {})
                        .get("Content-Encoding") or "").lower()
        if "gzip" in encoding:
            import gzip
            raw = gzip.decompress(raw)
        document = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 -- a route failure, named
        hint = (f" -- SEC refuses callers that do not declare a contact; "
                f"check {CONTACT_ENV}"
                if "403" in str(exc) or "401" in str(exc) else "")
        raise ReferenceError(f"{type(exc).__name__} fetching {url}{hint}: "
                             f"{exc}") from exc

    recent = ((document.get("filings") or {}).get("recent") or {})
    out: list[Filing] = []
    # NOT named `forms`: that is the parameter, and shadowing it made the
    # filter compare every form against the list of all forms, which is
    # always true (caught 2026-09-20 by a run that returned Form 4s).
    filed_forms = recent.get("form") or []
    for index, form in enumerate(filed_forms):
        if form not in forms:
            continue
        def at(key):
            values = recent.get(key) or []
            return values[index] if index < len(values) else ""
        accession = str(at("accessionNumber")).replace("-", "")
        primary = str(at("primaryDocument"))
        if not accession or not primary:
            continue
        out.append(Filing(form=form, accession=accession, document=primary,
                          filed=str(at("filingDate")),
                          period_end=str(at("reportDate")), cik=int(cik),
                          items=str(at("items"))))
    return out


def filing_for_period(filings: Sequence[Filing], period: str) -> Filing | None:
    """The filing whose OWN period is ``period`` — FY2025 or 2026-Q2.

    Matched on the filing's `reportDate`, never on its filing date: a 10-K
    filed in February 2026 reports on 2025, and taking the newest filing
    would put the wrong year's figures under the right label.
    """
    wanted_year = None
    if period.startswith("FY") and period[2:].isdigit():
        wanted_year = int(period[2:])
    for filing in filings:
        end = filing.period_end
        if not end or len(end) < 7:
            continue
        year, month = int(end[:4]), int(end[5:7])
        if wanted_year is not None:
            if (filing.form.startswith(("10-K", "20-F"))
                    and year == wanted_year):
                return filing
            continue
        # a quarter label, e.g. 2026-Q2
        if "-Q" in period and filing.form.startswith("10-Q"):
            q_year, quarter = period.split("-Q")
            if int(q_year) == year and (month - 1) // 3 + 1 == int(quarter):
                return filing
    return None


def download_filing(filing: Filing, ticker: str, period: str, *,
                    root: Path | None = None, contact=None,
                    opener=None) -> Path:
    """Fetch one filing into `sources/`, under the directory's own naming.

    Records the download in `sources/manifest.json` in the shape the Nordic
    route already uses -- the URL, the moment, the byte count and the SHA-256
    -- because that manifest is the provenance record and a file beside it
    with no entry is a file nobody can vouch for.
    """
    import hashlib
    import urllib.request
    from datetime import datetime, timezone

    from .xbrl import XbrlError, user_agent

    root = Path(root or SOURCES_DIR)
    try:
        agent = user_agent(contact)
    except XbrlError as exc:
        raise ReferenceError(str(exc)) from exc

    suffix = Path(filing.document).suffix.lower() or ".htm"
    kind = ("annual-report-10k" if filing.form.startswith("10-K")
            else "annual-report-20f" if filing.form.startswith("20-F")
            else "quarterly-report-10q")
    name = f"{ticker}_{period}_{kind}_{filing.filed}_en_a0{suffix}"
    path = root / name
    if path.exists():
        return path

    request = urllib.request.Request(
        filing.url, headers={"User-Agent": agent})
    try:
        opener = opener or urllib.request.urlopen
        with opener(request, timeout=120) as response:
            raw = response.read(MAX_DOCUMENT_BYTES)
    except Exception as exc:  # noqa: BLE001 -- a route failure, named
        raise ReferenceError(f"{type(exc).__name__} fetching "
                             f"{filing.url}: {exc}") from exc
    if not raw:
        raise ReferenceError(f"{filing.url}: empty response")

    root.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    _record_download(root, {
        "file": name, "ticker": ticker, "period": period, "origin": "sec-edgar",
        "primary_source": True,
        "primary_source_basis": ("the document the filer filed with the SEC, "
                                 "taken from EDGAR's own archive"),
        "form": filing.form, "accession": filing.accession,
        "period_end": filing.period_end, "filed": filing.filed,
        "url": filing.url,
        "retrieved": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
    })
    return path


def _record_download(root: Path, entry: dict) -> None:
    """Append one download to the manifest. Never rewrites an entry."""
    path = Path(root) / "manifest.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        document = {"schema": "vss/nordic manifest v1", "note": "", "downloads": []}
    downloads = document.setdefault("downloads", [])
    if any(d.get("file") == entry["file"] for d in downloads):
        return
    downloads.append(entry)
    # ensure_ascii=False, as nordic.py writes the same file: otherwise every
    # Nordic headline is rewritten as \u escapes on each E103 download.
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# --- E104: the second reading ---------------------------------------------
#
# **A DISAGREEING CHECK IS RE-EXTRACTED BEFORE IT IS ESCALATED.** E103 moved
# the read-back from every figure in advance to the figure that blinked; it
# never asked whether the machine could answer that one itself. It can, and
# separating the two failure modes needs nothing more than a second look:
#
#     the line was misread   ->  two readings differ  ->  WITHDRAW
#     the line was read right->  two readings agree   ->  the owner's
#
# A misread comes from choosing the wrong column of a multi-column row, the
# wrong period, or the wrong one of two similarly-named lines. Every one of
# those is a choice made across a WIDE excerpt, and a NARROW one removes it.

#: How much of the document the second pass sees around the quoted line.
#: Wide enough to carry the column headings and the table caption the figure
#: is read against; narrow enough that the choice the first pass got wrong
#: is no longer available to make.
CONFIRM_WINDOW = 2_500

CONFIRM_PROMPT = """You are reading ONE passage from a company's own report.

Return STRICT JSON and nothing else:

{"value": <number or null>, "scale": "units|thousands|millions|billions",
 "quote": "<the verbatim line>"}

You are being asked for exactly one figure: __FIELD__.

RULES:

1. Return ONLY the figure THIS PASSAGE PRINTS under that name, for the
   period named below. If the passage does not print it, the value is null.
2. DO NOT DERIVE, ADD, NET OR ADJUST ANYTHING.
3. The passage may be a table row with SEVERAL COLUMNS. Read the column
   headings and take the column for the period asked about. If you cannot
   tell which column belongs to that period, the value is null -- say so
   rather than picking one.
4. "scale" is the scale the passage prints, from its caption or column
   heading. If it is not stated, null.
5. "quote" is the line copied verbatim."""


@dataclass(frozen=True)
class Confirmation:
    """What a second, independent reading of one figure found."""

    field: str
    period: str
    first: float | None
    second: float | None
    second_quote: str = ""
    detail: str = ""
    #: True only where both readings produced a number AND they agree.
    agreed: bool = False

    @property
    def conclusive(self) -> bool:
        """Did the second pass produce a number to compare at all?"""
        return self.second is not None

    def line(self) -> str:
        # `:g`, NOT `:,.0f`. Rounding to whole units printed KAR.ST's
        # 2025-Q4 withdrawal as "the first pass read 239 and the second 239"
        # -- a contradiction that read as an identity. The readings were
        # 238.6 and 239, which is exactly the difference E104 exists to
        # catch, and a summary that hides it discredits the report rather
        # than the extraction.
        if self.agreed:
            return (f"{self.period} {self.field}: CONFIRMED — two independent "
                    f"readings both give {self.first:g}. The transcription "
                    f"is settled, so the disagreement is CONSTRUCTION.")
        if self.second is None:
            return (f"{self.period} {self.field}: NOT CONFIRMED — the second "
                    f"pass could not read the figure from its own line "
                    f"({self.detail}). The first reading stands unconfirmed "
                    f"and is WITHDRAWN.")
        return (f"{self.period} {self.field}: CONTRADICTED — the first pass "
                f"read {self.first:g} and the second {self.second:g} "
                f"from the same line. Neither can be trusted; the figure is "
                f"WITHDRAWN.")


def narrow_excerpt(text: str, quote: str,
                   window: int = CONFIRM_WINDOW) -> str | None:
    """The passage around ``quote``, or None where the line is not found.

    The quote LOCATES the passage and never supplies the number -- that is
    the whole of the second reading's independence (E104 clause 2).
    """
    if not quote:
        return None
    lowered, needle = text.lower(), quote.strip().lower()
    found = lowered.find(needle)
    if found < 0:
        # The quote may have been normalised by the first pass. Fall back to
        # its longest distinctive run of words, never to a single number.
        words = [w for w in needle.split() if len(w) > 3]
        for length in (6, 5, 4, 3):
            for start in range(0, max(1, len(words) - length + 1)):
                probe = " ".join(words[start:start + length])
                found = lowered.find(probe)
                if found >= 0:
                    break
            if found >= 0:
                break
    if found < 0:
        return None
    return text[max(0, found - window // 2): found + window // 2]


def confirm_figure(proposal: "Proposal", document: Path, *,
                   transport=None, model=None, api_key=None) -> Confirmation:
    """Read one figure a SECOND time, from its own line alone (E104).

    The second pass is given the passage and the question and NEVER the
    first answer. Comparison is on the value AFTER both are put on the same
    scale, because two readings that differ only in stated scale have not
    disagreed about the line.
    """
    from . import source as source_step
    from .extract import API_URL, DEFAULT_MODEL, KEY_ENV, MODEL_ENV
    from .manual import UNIT_SCALE

    key = api_key or env.get(KEY_ENV)
    if not key:
        return Confirmation(proposal.field, proposal.period, proposal.value,
                            None, detail=f"{KEY_ENV} is not set")
    try:
        raw = Path(document).read_bytes()
        text = (source_step.pdf_to_text(raw, where=str(document))
                if source_step.looks_like_pdf(str(document), raw=raw)
                else raw.decode("utf-8", errors="replace"))
    except Exception as exc:  # noqa: BLE001 -- reported, never raised
        return Confirmation(proposal.field, proposal.period, proposal.value,
                            None, detail=f"{document.name} unreadable: {exc}")

    passage = narrow_excerpt(text, proposal.quote)
    if passage is None:
        return Confirmation(
            proposal.field, proposal.period, proposal.value, None,
            detail="the first pass's quoted line could not be found in the "
                   "document, which is itself a reason to distrust it")

    import urllib.request

    payload = json.dumps({
        "model": model or env.get(MODEL_ENV, DEFAULT_MODEL),
        "temperature": 0,
        "messages": [
            {"role": "system",
             "content": CONFIRM_PROMPT.replace("__FIELD__", proposal.field)},
            {"role": "user",
             "content": f"Company: {proposal.ticker}. "
                        f"Period asked about: {proposal.period}.\n\n"
                        f"{passage}"},
        ],
    }).encode("utf-8")
    request = urllib.request.Request(
        API_URL, data=payload,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    try:
        opener = transport or urllib.request.urlopen
        with opener(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
        reply = body["choices"][0]["message"]["content"].strip()
        if reply.startswith("```"):
            reply = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", reply).strip()
        answer = json.loads(reply)
    except Exception as exc:  # noqa: BLE001 -- reported, never raised
        return Confirmation(proposal.field, proposal.period, proposal.value,
                            None, detail=f"the second call failed: {exc}")

    second = _number(answer.get("value"))
    scale = SCALE_WORDS.get(str(answer.get("scale") or "").strip().lower())
    quote = str(answer.get("quote") or "").strip()
    if second is None:
        return Confirmation(proposal.field, proposal.period, proposal.value,
                            None, second_quote=quote,
                            detail="the second pass returned no figure for "
                                   "that period from that line")

    # Both onto ONE scale before comparing: two readings that differ only in
    # the scale they named have not disagreed about the line.
    first_scaled, second_scaled = proposal.value, second
    if proposal.scale and scale and proposal.scale != scale:
        second_scaled = second * UNIT_SCALE[scale] / UNIT_SCALE[proposal.scale]
    agreed = (first_scaled is not None
              and abs(second_scaled - first_scaled)
              <= max(abs(first_scaled), 1.0) * 1e-6)
    return Confirmation(proposal.field, proposal.period, first_scaled,
                        second_scaled, second_quote=quote, agreed=agreed,
                        detail="" if agreed else "the two readings differ")


def withdraw_figure(text: str, period: str, name: str,
                    confirmation: Confirmation) -> str:
    """Replace an unconfirmed figure with a NAMED ABSENCE (E104 clause 4).

    Not a deletion: the block stays, `value` becomes null, and the page
    carries BOTH readings. A reader must be able to see that the figure was
    tried and withdrawn rather than never attempted, and the next run may
    try again because a null figure is not `present`.
    """
    lines = text.split("\n")
    head = f"  - period: {period}"
    annual = f"  - fiscal_year: {period[2:]}" if period.startswith("FY") else None
    start = next((i for i, l in enumerate(lines)
                  if l.rstrip() == head or (annual and l.rstrip() == annual)),
                 None)
    if start is None:
        raise ReferenceError(f"no `{period}` entry to withdraw from")
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("  - "):
            break
        if (lines[index].startswith("      ")
                and lines[index].strip().rstrip(":") == name):
            end = index + 1
            while end < len(lines) and lines[end].startswith("        "):
                end += 1
            second = ("no figure" if confirmation.second is None
                      else f"{confirmation.second:g}")
            block = [
                f"      {name}:",
                f"        value: null",
                f'        source: "E104 WITHDRAWN -- two independent '
                f'extractions did not agree"',
                f'        page: "first pass read '
                f'{confirmation.first:g}, second pass read {second} from the '
                f'same line; {confirmation.detail}. A named absence, not a '
                f'figure: two transcriptions of one printed line that differ '
                f'mean the line was not read (E104, E25)"',
                f"        status: {STATUS_UNVERIFIED}",
            ]
            return "\n".join(lines[:index] + block + lines[end:])
    raise ReferenceError(f"`{period}` carries no `{name}` to withdraw")


def _figure_provenance(parsed, period: str, name: str):
    """(figure, entry) for one field on one period, or (None, None)."""
    for entry in list(parsed.periods) + list(parsed.annual):
        if _label(entry) != period:
            continue
        figure = entry.figures.get(name)
        if figure is not None and figure.present:
            return figure, entry
    return None, None


def confirm_disagreements(ticker: str, *, manual_dir: Path | None = None,
                          sources_root: Path | None = None,
                          confirmer: Callable | None = None,
                          write: bool = False) -> tuple[list, list[str]]:
    """E104: re-read every disagreeing check this project entered itself.

    Returns (confirmations, notes). Only checks that are FLAGGED, whose
    comparator is UNVERIFIED, and whose comparator this project wrote are
    touched -- a figure the owner VERIFIED is already settled and a second
    machine reading adds nothing to it.
    """
    from datetime import datetime

    from .manual import load_manual, section5_basis
    from .runrecord import Growth, from_store

    directory = Path(manual_dir or MANUAL_DIR)
    confirmations, notes = [], []
    parsed = load_manual(ticker, directory=directory)
    basis = section5_basis(parsed)
    if basis is None:
        return confirmations, [f"{ticker}: no twelve-month basis"]
    record = from_store(parsed, basis,
                        growth=Growth(base=0.0, view_file="E104 probe"),
                        run_ts=datetime.now().astimezone(),
                        notes="E104 confirmation probe")

    documents = documents_for(ticker, sources_root)
    root = Path(sources_root or SOURCES_DIR)
    confirmer = confirmer or confirm_figure

    for check in record.construction_checks():
        if not check.flagged or not check.comparator_field:
            continue
        if check.comparator_verified:
            notes.append(f"{check.comparator_field}: the owner has VERIFIED "
                         f"it, so the disagreement is his to judge (E104 "
                         f"does not re-read a settled figure)")
            continue
        name = check.comparator_field
        # The comparator may be summed over several periods; each one this
        # project wrote is re-read on its own line.
        for entry in list(parsed.periods) + list(parsed.annual):
            figure = entry.figures.get(name)
            if figure is None or not figure.present or figure.verified:
                continue
            if "E103" not in (figure.source or ""):
                notes.append(f"{_label(entry)} {name}: entered by hand, not "
                             f"by E103 -- not re-read")
                continue
            period = _label(entry)
            quote = ""
            page = figure.page or ""
            if "verbatim: " in page:
                quote = page.split("verbatim: ", 1)[1].strip()
            document = _document_for_period(root, [d.name for d in documents],
                                            period)
            if document is None:
                confirmations.append(Confirmation(
                    name, period, figure.value, None,
                    detail="the document it was read from is no longer "
                           "under `sources/`"))
                continue
            proposal = Proposal(ticker, name, period, value=figure.value,
                                scale=None, page=page, quote=quote,
                                route=ROUTE_PDF)
            confirmations.append(confirmer(proposal, root / document))

    if write:
        notes.extend(_apply_confirmations(ticker, confirmations,
                                          manual_dir=directory))
    return confirmations, notes


def _apply_confirmations(ticker: str, confirmations, *,
                         manual_dir: Path) -> list[str]:
    """Withdraw every figure a second reading did not confirm. Atomic."""
    import os
    import tempfile

    from .config import ConfigError
    from .manual import load_manual

    directory = Path(manual_dir)
    path = directory / f"{ticker.upper()}.yaml"
    original = path.read_text(encoding="utf-8")
    text, notes, withdrawn = original, [], 0
    for confirmation in confirmations:
        if confirmation.agreed:
            continue
        try:
            text = withdraw_figure(text, confirmation.period,
                                   confirmation.field, confirmation)
            withdrawn += 1
        except ReferenceError as exc:
            notes.append(f"{confirmation.period} {confirmation.field}: {exc}")
    if not withdrawn:
        return notes

    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(directory), delete=False,
        prefix=f".{path.name}.", suffix=".tmp")
    try:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    os.replace(handle.name, path)
    try:
        load_manual(ticker, directory=directory)
    except (ConfigError, OSError) as exc:
        path.write_text(original, encoding="utf-8")
        return notes + [f"ROLLED BACK -- the store stopped loading ({exc})"]
    return notes + [f"{withdrawn} figure(s) withdrawn to a named absence"]


def report_confirmations(*, ticker: str | None = None, write: bool = False,
                         manual_dir: Path | None = None,
                         sources_root: Path | None = None,
                         confirmer: Callable | None = None) -> tuple[int, str]:
    """`vss reference-figures --confirm`. E104's second reading, reported."""
    directory = Path(manual_dir or MANUAL_DIR)
    names = ([ticker.upper()] if ticker else
             sorted(p.stem for p in directory.glob("*.yaml")
                    if p.stem != "TEMPLATE"))
    out = [f"# second readings (E104) — {date.today().isoformat()}", "",
           "*A disagreeing check is RE-EXTRACTED before it is escalated. Two "
           "independent readings agreeing settle the TRANSCRIPTION, so the "
           "disagreement is CONSTRUCTION and yours to judge; two disagreeing "
           "convict the extraction and the figure withdraws itself. A figure "
           "you have VERIFIED is never re-read.*", ""]
    confirmed, withdrawn, skipped = [], [], []
    for name in names:
        try:
            results, notes = confirm_disagreements(
                name, manual_dir=directory, sources_root=sources_root,
                confirmer=confirmer, write=write)
        except Exception as exc:  # noqa: BLE001 -- one name never stops it
            out.append(f"- `{name}` ERROR: {type(exc).__name__}: {exc}")
            continue
        for note in notes:
            if "VERIFIED" in note:
                skipped.append(f"`{name}` {note}")
        for result in results:
            (confirmed if result.agreed else withdrawn).append(
                f"`{name}` {result.line()}")

    out += [f"- **confirmed — CONSTRUCTION, and yours to judge:** "
            f"{len(confirmed)}",
            f"- **withdrawn — the extraction was the problem:** "
            f"{len(withdrawn)}",
            f"- **not re-read because you verified them:** {len(skipped)}", ""]
    for heading, rows in (("CONFIRMED — two readings agree", confirmed),
                          ("WITHDRAWN — two readings differ", withdrawn),
                          ("YOURS ALREADY", skipped)):
        if not rows:
            continue
        out += [f"## {heading}", ""] + [f"- {r}" for r in rows] + [""]
    return 0, "\n".join(out)
