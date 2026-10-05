"""SEC XBRL companyfacts as a primary source.

``data.sec.gov`` returns every tagged financial fact for a US filer as
JSON. There is no HTML to flatten, no PDF to reconstruct and no model in
the loop: a figure arrives already attached to its tag, its context
period and the accession number of the filing that reported it. That is
stronger provenance than a quoted sentence, and it is why this module
exists alongside the extractor rather than replacing it -- most of the
world does not file with the SEC.

What does NOT change: DATA MISSING is still DATA MISSING. A tag the
filer does not use is absent, not substituted. NIKE reports no
OperatingIncomeLoss because it publishes no operating income line, and
this module will not hand back Income-before-taxes or Gross profit in
its place -- the same substitution the extraction prompt forbids.
"""

from __future__ import annotations

import gzip
import json
import logging
import os
import zlib
import urllib.error
import urllib.request
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from . import env
from .env import ENV_FILE

log = logging.getLogger(__name__)

API_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

#: THE TWO TAXONOMIES A FILER ON data.sec.gov REPORTS IN. A US domestic
#: filer tags `us-gaap`; a foreign private issuer filing a 20-F under IFRS
#: tags `ifrs-full`. They are not dialects of one vocabulary -- the element
#: names, the sign conventions and the statement structure all differ -- so
#: each has its own map and its own year-end tags, and nothing falls back
#: from one to the other.
US_GAAP = "us-gaap"
IFRS_FULL = "ifrs-full"

#: A unit resolved PER FILER rather than named in the map. `us-gaap` is
#: effectively always USD; `ifrs-full` is whatever the issuer reports in,
#: and SAP's facts carry BOTH EUR and USD on most tags (the USD entries are
#: convenience translations from a 2018 20-F). Naming "the first money unit"
#: would pick whichever the JSON happened to list first, so the reporting
#: currency is MEASURED from the facts and then named exactly.
MONEY = "*money*"
MONEY_PER_SHARE = "*money/shares*"
CONTACT_ENV = "VSS_SEC_CONTACT"
TIMEOUT_SECONDS = 60
MAX_BYTES = 50_000_000

#: SEC asks every automated caller to declare itself with a real contact
#: address. That is their published access policy, so vss follows it --
#: and refuses to call rather than sending a fake one or pretending to be
#: a browser. The contact is the owner's to supply; it is never embedded.
CONTACT_MISSING = (
    f"{CONTACT_ENV} is not set, in the environment or in {ENV_FILE}. "
    f"data.sec.gov requires every automated request to declare a real "
    f"contact address -- that is SEC's stated access policy. Set it to "
    f"something they can reach you at, either as "
    f"{CONTACT_ENV}='vss/1.0 (you@example.com)' in the environment or as a "
    f"line in that file, and re-run. vss will not invent one."
)

#: Schema field -> the tags that may supply it, in order of preference.
#: A field whose tags are all absent is DATA MISSING and stays that way.
#:
#: op_income maps to OperatingIncomeLoss ALONE, deliberately. An issuer
#: with no operating income line has none to give, and the near neighbours
#: are different quantities: IncomeLossFromContinuingOperations...
#: is struck after interest, GrossProfit is struck before overhead.
TAGS: dict[str, tuple[str, ...]] = {
    "revenue": (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ),
    "op_income": ("OperatingIncomeLoss",),
    "eps": ("EarningsPerShareDiluted",),
    "receivables": ("AccountsReceivableNetCurrent",),
    # NIKE tagged InventoryNet until 2011 and has used the finished-goods
    # element since. Its balance sheet line "Inventories" IS that element
    # -- 7,487 in Q3 FY26, matching the release to the dollar -- and the
    # provenance records which tag supplied the figure, so a reader can
    # see that it was finished goods rather than a total.
    "inventory": ("InventoryNet", "InventoryFinishedGoodsNetOfReserves"),
}

#: Fields measured over a period rather than at an instant.
DURATION_FIELDS = ("revenue", "op_income", "eps")

#: A quarterly duration, in days. 13 weeks is 91; filers vary by a few.
QUARTER_MIN_DAYS = 80
QUARTER_MAX_DAYS = 100


class XbrlError(Exception):
    """Raised when the API cannot be called or its answer cannot be used."""


@dataclass
class Figure:
    """One fact, with the provenance the filing itself carries."""

    value: float
    tag: str
    start: str | None
    end: str
    accession: str
    form: str
    filed: str
    #: An earlier filing reported a different value for the same period.
    restated_from: float | None = None
    #: WHICH VOCABULARY the tag belongs to. On the page reference, because
    #: `Revenue` means one thing in `ifrs-full` and nothing in `us-gaap`.
    taxonomy: str = US_GAAP
    #: Set where a SHARE SPLIT was declared AFTER this figure was filed and
    #: TRUE where `restated_from` is not a restatement at all but the SAME
    #: FIGURE IN ANOTHER UNIT -- the two differ by a round power of a
    #: thousand and by nothing else. A 1,000x "restatement" is news that
    #: did not happen, and saying so is the difference between a reader
    #: chasing a filing and a reader chasing a scale.
    unit_slip: bool = False
    #: no later filing has restated it, so the figure is on the pre-split
    #: basis while its neighbours are not. Carried on the page reference
    #: because a figure key cannot hold it: `ALLOWED_FIGURE_KEYS` is
    #: {value, source, page, status, zero_basis} and refuses a sixth.
    split_note: str = ""
    #: Set where the tag that supplied this figure answers the field with a
    #: DIFFERENT CONCEPT from the field's first tag (`CONCEPT_NOTES`): the
    #: income-statement SBC charge standing in for the cash-flow add-back,
    #: commercial paper standing in for current maturities. On the page
    #: line, so a reader of the file sees which concept was taken without
    #: opening this map.
    concept_note: str = ""
    #: E65 / E66 / E68 (2026-08-29): set where the figure is the SUM of two
    #: or more STATED captions. Holds the whole provenance -- every
    #: component with its own tag, accession and amount, and the
    #: arithmetic -- and `components` carries the Figures it was built from.
    composite: str = ""
    components: tuple = ()

    @property
    def provenance(self) -> str:
        if self.composite:
            return f"{self.composite}{self.split_note}"
        window = f"{self.start}..{self.end}" if self.start else f"as of {self.end}"
        base = (f"{self.taxonomy}:{self.tag} [{window}] {self.form} "
                f"{self.accession} filed {self.filed}")
        return f"{base}{self.concept_note}{self.split_note}"


@dataclass
class XbrlQuarter:
    period: str
    period_basis: str
    figures: dict = field(default_factory=dict)      # field -> Figure
    missing: list = field(default_factory=list)      # fields no tag supplied
    #: True when the filer tagged a balance sheet at this quarter end but
    #: no income statement for the quarter itself.
    balance_sheet_only: bool = False

    def value(self, name):
        figure = self.figures.get(name)
        return figure.value if figure else None


def user_agent(contact: str | None = None) -> str:
    """The contact SEC's access policy requires, or a loud refusal.

    An explicit argument wins, then the environment, then the env file
    systemd already reads (`vss.env.get`). Nothing here invents one.
    """
    contact = contact or env.get(CONTACT_ENV)
    if not contact or not contact.strip():
        raise XbrlError(CONTACT_MISSING)
    return contact.strip()


def fetch_company_facts(cik: int, *, contact=None, opener=None) -> dict:
    """GET companyfacts for one filer. Fails loudly, never silently."""
    agent = user_agent(contact)
    url = API_URL.format(cik=int(cik))
    request = urllib.request.Request(
        url, headers={"User-Agent": agent, "Accept-Encoding": "gzip, deflate"}
    )
    try:
        opener = opener or urllib.request.urlopen
        with opener(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_BYTES + 1)
            headers = getattr(response, "headers", None) or {}
            encoding = (headers.get("Content-Encoding") or "").lower()
    except urllib.error.HTTPError as exc:
        hint = ""
        if exc.code in (401, 403):
            hint = (f" -- SEC refuses callers that do not declare a contact. "
                    f"Check {CONTACT_ENV}.")
        raise XbrlError(f"HTTP {exc.code} fetching {url}{hint}") from exc
    except Exception as exc:
        raise XbrlError(f"{type(exc).__name__} fetching {url}: {exc}") from exc

    if len(raw) > MAX_BYTES:
        raise XbrlError(f"{url}: response exceeds {MAX_BYTES} bytes")

    # The companyfacts payload is megabytes of JSON, so it is requested
    # compressed. urllib does not unwrap it, and a gzip stream decoded as
    # UTF-8 fails on byte 2 -- loudly, but with the wrong explanation.
    try:
        if "gzip" in encoding:
            raw = gzip.decompress(raw)
        elif "deflate" in encoding:
            raw = zlib.decompress(raw)
    except Exception as exc:
        raise XbrlError(f"{url}: cannot decompress a {encoding!r} response ({exc})") from exc
    if len(raw) > MAX_BYTES:
        raise XbrlError(f"{url}: decompressed response exceeds {MAX_BYTES} bytes")

    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise XbrlError(f"{url}: response is not JSON ({exc})") from exc


def _entries(facts: dict, tag: str, unit: str | None = None,
             taxonomy: str = US_GAAP) -> list[dict]:
    """Every fact filed under one tag, in one taxonomy, in one unit.

    ``unit`` names the unit EXACTLY -- ``USD``, ``EUR``, ``shares``,
    ``USD/shares``. Without it the historical behaviour stands: the first
    money unit found, which is what the quarter shape has always read. A
    share count is not a money unit and would come back empty under that
    rule, which is why the annual path names its unit on every field rather
    than inheriting one.

    ``taxonomy`` IS NOT OPTIONAL IN SPIRIT. It defaulted to `us-gaap` for
    the whole life of this module and that default made both held names
    unreachable: SAP.DE and UNA.AS file 20-Fs whose facts are entirely
    `ifrs-full`, so every lookup returned an empty list and
    `fiscal_year_end_month` raised "no annual periods in the facts"
    (REVIEW-4 report B 5.1, RUN twice). The default is kept so the quarter
    shape's call sites read as they did; every annual call site names it.
    """
    node = (facts.get("facts", {}).get(taxonomy, {}) or {}).get(tag)
    if not node:
        return []
    units = node.get("units", {})
    if unit is not None:
        return units.get(unit, [])
    for name, entries in units.items():
        if name == "USD" or name.startswith("USD/"):
            return entries
    return []


def fiscal_year_end_month(facts: dict, taxonomy: str = US_GAAP,
                          currency: str | None = None) -> int:
    """The month the filer's financial year ends, read from its own facts.

    Taken from annual-length durations rather than assumed: NIKE's year
    ends 31 May, and calling its Sep-Nov quarter "Q4" because a calendar
    year ends in December would misdate every figure in the history.

    THE TAGS IT SCANS ARE THE TAXONOMY'S. Opening `ifrs-full` in `_entries`
    is not enough on its own: this scanned `TAGS["revenue"]` --
    `RevenueFromContractWithCustomer...`, a us-gaap spelling -- so an IFRS
    filer still raised "no annual periods in the facts", which is exactly
    what reports A and B measured on `--cik 1000184`.
    """
    year_end_tags = TAXONOMY_BY_NAME[taxonomy].year_end_tags
    months: dict[int, int] = {}
    ends: set[date] = set()
    for tag in year_end_tags:
        # NAME THE CURRENCY. Without it `_entries` falls back to "the first
        # money unit", which means the first unit called USD -- so Unilever,
        # whose facts are EUR alone, answered with an empty list and raised
        # "no annual periods in the facts", and SAP placed its year end off a
        # single 2017 USD convenience translation. Both were the same defect
        # and only one of them looked like one.
        for entry in _entries(facts, tag, currency, taxonomy=taxonomy):
            if not entry.get("start"):
                continue
            span = (date.fromisoformat(entry["end"])
                    - date.fromisoformat(entry["start"])).days
            if 350 <= span <= 380:
                end = date.fromisoformat(entry["end"])
                months[end.month] = months.get(end.month, 0) + 1
                ends.add(end)
    if not months:
        raise XbrlError("no annual periods in the facts; cannot place quarters")
    return changed_year_end_month(sorted(ends), max(months, key=months.get))


def changed_year_end_month(ends: list[date], modal: int) -> int:
    """The modal month, unless the filer has since MOVED its year end.

    HRB moved from 30 April to 30 June in 2021: fourteen April years
    against five June ones, so the modal month was April and every year
    since the move was passed over -- the basis read FY2021, 1,966 days
    old. A count over the whole history is a vote the past always wins.

    The move is read off the TAIL: the year ends after the last one within
    tolerance of the modal month. It counts only if there are at least TWO
    of them and they all sit within tolerance of ONE month -- so a lone
    trailing-twelve-months window, or two stubs on different months, leave
    the modal month standing. A 52/53-week year drifting across a month
    boundary (LULU) is within tolerance of the modal month and has no tail.
    The years before the move are then passed over and named, as any
    window off the anchor is.
    """
    anchored = [i for i, end in enumerate(ends) if _anchor(end, modal) is not None]
    tail = ends[anchored[-1] + 1:] if anchored else ends
    if len(tail) < 2:
        return modal
    counts: dict[int, int] = {}
    for end in tail:
        counts[end.month] = counts.get(end.month, 0) + 1
    moved = max(counts, key=counts.get)
    if all(_anchor(end, moved) is not None for end in tail):
        return moved
    return modal


def fiscal_period(end: date, fy_end_month: int) -> tuple[str, str]:
    """(period label, period_basis) for a quarter ending on ``end``."""
    quarter = ((end.month - fy_end_month - 1) % 12) // 3 + 1
    year = end.year if end.month <= fy_end_month else end.year + 1
    basis = "calendar" if fy_end_month == 12 else "fiscal"
    return f"{year}-Q{quarter}", basis


#: The forms that tag the FINANCIAL STATEMENTS themselves. Everything else
#: that carries the same element -- a DEF 14A above all -- is tagging a
#: SUMMARY of them, and a summary is written in whatever scale its table is
#: printed in.
STATEMENT_FORMS = ("10-K", "10-Q", "20-F", "40-F")


def _is_statement(entry: dict) -> bool:
    return str(entry.get("form", "")).startswith(STATEMENT_FORMS)


def _is_unit_slip(one: float | None, other: float | None) -> bool:
    """Are these the same figure in two units?

    The exact question, not "are these very different": a statement printed
    in thousands against one printed in units differs by a round power of a
    thousand AND BY NOTHING ELSE. `ranking.is_unit_slip` asks it of two
    vendor labels; this asks it of two filings.
    """
    if not one or not other:
        return False
    big, small = (abs(one), abs(other)) if abs(one) > abs(other) else (abs(other), abs(one))
    ratio = big / small
    for power in (1e3, 1e6, 1e9):
        if abs(ratio - power) < power * 1e-9:
            return True
    return False


def _slip_in(entries: list[dict]) -> str:
    """A UNIT SLIP inside one (element, period, unit) pool, described.

    Asked over the WHOLE pool and not only against the chosen entry: a
    filer that tagged three values, two of them a thousand apart, has a
    slip whether or not the latest filing is one of the two.

    Empty string where there is none, which is the overwhelmingly common
    case -- measured 2026-09-04 over fifteen filers' complete companyfacts:
    6,924 (element, period) groups held more than one value and 43 were a
    round power of a thousand apart.
    """
    pool = [e for e in entries if _is_statement(e)] or entries
    values = sorted({float(e["val"]) for e in pool if e.get("val")})
    for i, one in enumerate(values):
        for other in values[i + 1:]:
            if _is_unit_slip(one, other):
                where = {}
                for e in pool:
                    where.setdefault(float(e["val"]), set()).add(
                        f"{e.get('form', '?')} {e.get('accn', '?')}")
                return " against ".join(
                    f"{v:,.0f} ({', '.join(sorted(where.get(v, ())))})"
                    for v in (one, other))
    return ""


def _pick(entries: list[dict]) -> tuple[dict, float | None]:
    """The authoritative entry for one period, and any value it restates.

    Several filings report the same period: the original 10-Q, then the
    next year's comparative. The latest filing is the current official
    figure. When an earlier one said something DIFFERENT, that is a
    restatement, and this says so rather than quietly preferring one.

    **A FINANCIAL STATEMENT OUTRANKS A PROXY, AND A LIVE FILER SHOWED WHY
    (2026-09-04, found on LOPE's intake).** Grand Canyon Education tags
    `us-gaap:NetIncomeLoss` for FY2025 twice: **216,170,000** in the 10-K
    (0001104659-26-017047, filed 2026-02-18) and **216,170** in the DEF 14A
    (0001104659-26-047719, filed 2026-04-23). The proxy tagged the number
    as its own table PRINTS it -- the statement says *(In thousands, except
    per share data)* -- and did not scale it. Taking the latest filing put
    a figure **1,000x too small** into the store, beside a revenue in whole
    units, and nothing downstream could tell: `net_income` is read by 5.1C
    and the FCF conversion would have been out by three orders.

    So the pool is narrowed to `STATEMENT_FORMS` where any exist. This is
    NOT a judgement about which value is right -- it is a fact about which
    document states the accounts.

    **AND A SLIP THAT SURVIVES THAT IS NOT A RESTATEMENT.** Two statement
    filings whose values differ by a round power of a thousand are one
    figure in two units, and calling the later one a restatement of the
    earlier would record a 1,000x move as news. It is reported as a slip
    instead -- the caller names both and writes neither.
    """
    statements = [e for e in entries if _is_statement(e)]
    pool = statements or entries
    ordered = sorted(pool, key=lambda e: (e.get("filed", ""), e.get("accn", "")))
    latest = ordered[-1]
    earlier = {e["val"] for e in ordered[:-1] if e["val"] != latest["val"]}
    return latest, (sorted(earlier)[-1] if earlier else None)


def _duration_groups(facts: dict, tag: str) -> dict:
    """Quarter-length entries for one tag, grouped by their exact window."""
    groups: dict[tuple, list] = {}
    for entry in _entries(facts, tag):
        if not entry.get("start"):
            continue
        start = date.fromisoformat(entry["start"])
        end = date.fromisoformat(entry["end"])
        if QUARTER_MIN_DAYS <= (end - start).days <= QUARTER_MAX_DAYS:
            groups.setdefault((entry["start"], entry["end"]), []).append(entry)
    return groups


def _instant_groups(facts: dict, tag: str, unit: str | None = None,
                    taxonomy: str = US_GAAP) -> dict:
    """Point-in-time entries for one tag, grouped by date."""
    groups: dict[str, list] = {}
    for entry in _entries(facts, tag, unit, taxonomy=taxonomy):
        if not entry.get("start"):
            groups.setdefault(entry["end"], []).append(entry)
    return groups


def _record(slot: dict, name: str, tag: str, entries: list) -> None:
    """Fill a field from the authoritative entry, if it is still empty.

    Tags are tried in preference order and a later one only fills a gap,
    never overwrites. The preference is per PERIOD, not per company:
    NIKE tagged InventoryNet until 2011 and the finished-goods element
    after, so a tag that is dead today may still be the right one for an
    old quarter -- and a tag with data SOMEWHERE must not shadow a tag
    with data HERE.
    """
    if name in slot["figures"]:
        return
    entry, restated = _pick(entries)
    slot["figures"][name] = Figure(
        value=float(entry["val"]), tag=tag, start=entry.get("start"),
        end=entry["end"], accession=entry["accn"], form=entry.get("form", ""),
        filed=entry.get("filed", ""), restated_from=restated,
        unit_slip=_is_unit_slip(float(entry["val"]), restated),
    )


def untagged_tail(facts: dict, quarters: list) -> dict | None:
    """A reporting period the filer covered but did not tag as a quarter.

    A 10-K states the full year, and the Q3 10-Q states nine months. The
    fourth quarter is the difference between them and is tagged by
    nobody: filers stopped reporting discrete Q4 figures when the SEC
    dropped the Selected Quarterly Financial Data requirement in 2021 --
    MICROSOFT last tagged one for the year ended 30 June 2020.

    So the newest quarter here can lag the newest FILING by a quarter,
    for a reason that is neither a bug nor a delay, and waiting does not
    fix it. Subtracting one from the other would produce a figure no
    filing states, which is the one thing this module will not do. It
    reports the gap instead.
    """
    if not quarters:
        return None
    newest_quarter_end = max(q.figures[n].end for q in quarters
                             for n in q.figures if q.figures[n].start)
    annual = None
    for tag in TAGS["revenue"] + TAGS["op_income"]:
        for entry in _entries(facts, tag):
            if not entry.get("start"):
                continue
            span = (date.fromisoformat(entry["end"])
                    - date.fromisoformat(entry["start"])).days
            if 350 <= span <= 380 and entry["end"] > newest_quarter_end:
                if annual is None or entry["end"] > annual["end"]:
                    annual = entry
    if annual is None:
        return None
    return {"covers_to": annual["end"], "form": annual.get("form", ""),
            "accession": annual["accn"], "newest_quarter_end": newest_quarter_end}


def build_quarters(facts: dict, *, limit: int = 8) -> list[XbrlQuarter]:
    """The most recent ``limit`` quarters, oldest first."""
    fy_end_month = fiscal_year_end_month(facts)
    by_period: dict[str, dict] = {}

    # Duration facts define which quarters exist at all.
    for name in DURATION_FIELDS:
        for tag in TAGS[name]:
            for (_, end_s), entries in _duration_groups(facts, tag).items():
                end = date.fromisoformat(end_s)
                period, basis = fiscal_period(end, fy_end_month)
                slot = by_period.setdefault(
                    period, {"basis": basis, "end": end, "figures": {}})
                _record(slot, name, tag, entries)

    # A year end reports a balance sheet without a fourth-quarter income
    # statement. The instants are real, tagged facts about a quarter that
    # otherwise would not appear at all, so the quarter is opened for them
    # and its income-statement fields stay blank -- DATA MISSING, which is
    # what they are. Nothing is derived to fill them.
    newest_duration_end = max((slot["end"] for slot in by_period.values()),
                              default=None)
    if newest_duration_end is not None:
        for name in (n for n in TAGS if n not in DURATION_FIELDS):
            for tag in TAGS[name]:
                for end_s in _instant_groups(facts, tag):
                    end = date.fromisoformat(end_s)
                    if end <= newest_duration_end:
                        continue
                    # Only a real quarter boundary for THIS filer, so a
                    # subsequent-event date cannot invent a quarter.
                    if (end.month - fy_end_month) % 3 != 0:
                        continue
                    period, basis = fiscal_period(end, fy_end_month)
                    by_period.setdefault(period, {"basis": basis, "end": end,
                                                  "figures": {}})

    # A balance-sheet instant belongs to the quarter it closes.
    for name in (n for n in TAGS if n not in DURATION_FIELDS):
        for tag in TAGS[name]:
            groups = _instant_groups(facts, tag)
            for slot in by_period.values():
                entries = groups.get(slot["end"].isoformat())
                if entries:
                    _record(slot, name, tag, entries)

    quarters = []
    for period in sorted(by_period)[-limit:]:
        slot = by_period[period]
        quarters.append(XbrlQuarter(
            period=period, period_basis=slot["basis"], figures=slot["figures"],
            missing=[n for n in TAGS if n not in slot["figures"]],
            balance_sheet_only=not any(n in slot["figures"] for n in DURATION_FIELDS),
        ))
    return quarters


def as_quarter(q: XbrlQuarter):
    """An XbrlQuarter in the shape rules.py and the loader already know."""
    from . import rules as R

    return R.Quarter(
        period=q.period,
        revenue=q.value("revenue"),
        op_income=q.value("op_income"),
        eps=q.value("eps"),
        receivables=q.value("receivables"),
        inventory=q.value("inventory"),
        # Everything below is absent BY CONSTRUCTION, not by omission.
        # op_margin has no tag -- it would have to be computed from
        # op_income and revenue, which is the one thing this project
        # never does. revenue_yoy likewise. eps_consensus is MANUAL ONLY.
        op_margin=None, revenue_yoy=None, eps_consensus=None,
        net_debt_ebitda=None, guidance_action=None, class_c_impact=None,
        covenant_headroom=None,
        basis="reported", accounting="gaap", period_basis=q.period_basis,
        # The tag is the provenance. It exempts the entry from the
        # op_margin reconciliation -- which existed to establish which
        # line op_income came from, a question us-gaap:OperatingIncomeLoss
        # answers outright -- and it makes the row's origin visible in
        # the file, where a mixed-unit history is otherwise invisible.
        source="xbrl",
    )


UNITS_WARNING = (
    "XBRL states values in whole units -- 11,279,000,000, where the press "
    "release for the same quarter says 11,279 million. Both are the figure "
    "the source states, and vss does not rescale either. Do NOT mix the two "
    "sources within one ticker's history: a sequential comparison across a "
    "1,000,000x step is meaningless."
)


def render_report(*, ticker: str, name: str, cik: int, quarters: list,
                  as_of: date, gap: dict | None = None) -> str:
    from .config import unit_problem
    from .earnings import _yaml_block

    url = API_URL.format(cik=int(cik))
    out = [f"# vss xbrl -- {ticker} ({name}) -- {as_of.isoformat()}", ""]
    out.append(f"**PRIMARY SOURCE:** {url}")
    out.append("")
    out.append("*Every figure below carries the tag it was filed under, the "
               "context period it covers and the accession number of the filing "
               "that reported it. No model read this; nothing was quoted, "
               "summarised or inferred. Verify against the filing before any "
               "action -- this tool flags; it does not advise.*")
    out.append("")
    out.append(f"**UNITS:** {UNITS_WARNING}")
    out.append("")

    missing = sorted({f for q in quarters for f in q.missing})
    if missing:
        out.append("## DATA MISSING")
        out.append("")
        out.append("No tag in the filer's own facts supplies these. They are "
                   "left blank -- a near neighbour is a different quantity, and "
                   "substituting one is how a wrong figure enters a record:")
        out.append("")
        for name_ in missing:
            tags = ", ".join(f"`{t}`" for t in TAGS[name_])
            periods = [q.period for q in quarters if name_ in q.missing]
            out.append(f"- `{name_}` -- not tagged in {len(periods)} of "
                       f"{len(quarters)} quarters (tried {tags})")
        out.append("")

    restated = [(q, f) for q in quarters for f in q.figures.values()
                if f.restated_from is not None]
    if restated:
        out.append("## RESTATED SINCE FIRST FILED")
        out.append("")
        out.append("A later filing reported a different value for a period an "
                   "earlier one had already reported. The later filing is used; "
                   "the earlier value is named so the change is visible:")
        out.append("")
        for q, f in restated:
            if f.unit_slip:
                out.append(
                    f"- `{q.period}` {f.tag}: **UNIT SLIP, NOT A "
                    f"RESTATEMENT** -- {f.restated_from:,.2f} against "
                    f"{f.value:,.2f} is a round power of a thousand and "
                    f"nothing else, so the two filings state ONE figure in "
                    f"TWO SCALES. The statement form is preferred "
                    f"({f.form} {f.accession}); check it before using this.")
                continue
            out.append(f"- `{q.period}` {f.tag}: {f.restated_from:,.2f} -> "
                       f"{f.value:,.2f} ({f.form} {f.accession})")
        out.append("")

    if gap:
        out.append("## A PERIOD THE FILER DID NOT TAG AS A QUARTER")
        out.append("")
        out.append(f"The newest quarter above ends {gap['newest_quarter_end']}, but "
                   f"the filer has since reported a full year ending "
                   f"{gap['covers_to']} ({gap['form']} {gap['accession']}). Its "
                   f"FOURTH QUARTER is not tagged as a discrete period, by this "
                   f"filer or generally: the SEC dropped the quarterly-data "
                   f"requirement in 2021 and filers stopped.")
        out.append("")
        partial = [q.period for q in quarters if q.balance_sheet_only]
        if partial:
            out.append(f"Its BALANCE SHEET is tagged, so `{partial[0]}` appears "
                       f"below carrying receivables and inventory and nothing "
                       f"else. Those are real facts about that quarter; the "
                       f"blanks beside them are DATA MISSING, not zeroes.")
            out.append("")
        out.append("That quarter is the difference between the annual figure and "
                   "the nine-month figure. vss does not compute it: the result "
                   "would be a number no filing states, and this source exists "
                   "precisely because every figure in it does. Waiting will not "
                   "produce it either -- read that quarter from the release if "
                   "you need it, in the units the rest of the history uses.")
        out.append("")

    out.append("## PROPOSED quarters: ENTRIES -- NOT WRITTEN")
    out.append("")
    out.append("vss will never write these. Copy them into "
               "`config/watchlist.yaml` yourself after verifying every figure "
               "against the filing named beside it.")
    out.append("")
    out.append("```yaml")
    for q in quarters:
        out.extend(_yaml_block(as_quarter(q)))
    out.append("```")
    out.append("")

    problems = [(q.period, unit_problem(as_quarter(q))) for q in quarters]
    problems = [(p, m) for p, m in problems if m]
    if problems:
        out.append("## THESE ENTRIES WILL NOT LOAD")
        out.append("")
        for period, message in problems:
            out.append(f"- `{period}`: {message}")
        out.append("")

    out.append("## PROVENANCE")
    out.append("")
    out.append("| Period | Field | Value | Tag | Context | Filing |")
    out.append("|---|---|---|---|---|---|")
    for q in quarters:
        for field_name, f in sorted(q.figures.items()):
            window = f"{f.start}..{f.end}" if f.start else f"as of {f.end}"
            out.append(f"| `{q.period}` | `{field_name}` | {f.value:,.2f} | "
                       f"`us-gaap:{f.tag}` | {window} | {f.form} {f.accession} "
                       f"filed {f.filed} |")
    out.append("")
    return "\n".join(out)


def run_xbrl(*, ticker: str, cik: int | None = None, limit: int = 8,
             watchlist_path, db_path, now=None, fetcher=None) -> tuple[int, str]:
    """Returns (exit_code, report_markdown)."""
    from datetime import datetime

    from .config import ConfigError, load_watchlist
    from .store import persist_earnings

    run_ts = now or datetime.now().astimezone()
    as_of = run_ts.date()

    entries = {e.ticker.upper(): e for e in load_watchlist(watchlist_path)}
    entry = entries.get(ticker.strip().upper())
    if entry is None:
        raise ConfigError(f"ticker {ticker} is not in {watchlist_path}")
    cik = cik if cik is not None else entry.cik
    if cik is None:
        raise ConfigError(
            f"{entry.ticker} has no cik. SEC identifies filers by CIK, not by "
            f"ticker, and NO CIK RESOLUTION STEP IS BUILT. That is a gap in "
            f"this project, NOT a closed door: "
            f"https://www.sec.gov/files/company_tickers.json answers HTTP 200 "
            f"to a caller that declares a real contact, and every CIK in this "
            f"project was typed by hand anyway. Add `cik: NNNNNN` to the "
            f"watchlist entry or pass --cik."
        )

    error, quarters, report = None, [], ""
    try:
        facts = (fetcher or fetch_company_facts)(int(cik))
        quarters = build_quarters(facts, limit=limit)
        if not quarters:
            raise XbrlError(f"no quarterly facts found for CIK {cik}")
        report = render_report(ticker=entry.ticker, name=entry.name, cik=int(cik),
                               quarters=quarters, as_of=as_of,
                               gap=untagged_tail(facts, quarters))
    except XbrlError as exc:
        error = str(exc)
        log.error("%s: %s", entry.ticker, error)
        report = (f"# vss xbrl -- {entry.ticker} ({entry.name}) -- "
                  f"{as_of.isoformat()}\n\n## SOURCE UNAVAILABLE\n\n- {error}\n")

    missing = sorted({f for q in quarters for f in q.missing})
    persist_earnings(db_path, {
        "run_ts": run_ts.isoformat(timespec="seconds"),
        "as_of": as_of.isoformat(),
        "ticker": entry.ticker,
        "source_url": API_URL.format(cik=int(cik)),
        "model": None,                      # no model reads XBRL
        "shadow": 1,
        "trips": None,
        "cannot_evaluate": None,
        "extraction_uncertain": 1 if (error or missing) else 0,
        "uncertainty_reasons": ("not tagged by the filer: " + ", ".join(missing))
                               if missing else error,
        "error": error,
        "alert": report,
        "raw_response": None,               # 3MB of facts; the URL is the record
    })
    return (0 if error is None else 1), report


# --- SECTION 5's OWN FACTS: THE ANNUAL PATH -------------------------------
#
# The quarter shape above answers section 4.2. It carries no cash-flow line
# at all, so Method C -- which E28 made the engine -- had nothing to read
# and every US filer's fair value was reached by hand out of a 10-K.
#
# What follows closes that gap, and it closes it by WRITING A MANUAL FILE
# rather than by growing a second section 5. Six rules govern it and each
# one is answered in code below:
#
#   1. IT WRITES config/manual/<TICKER>.yaml, in the existing schema, so
#      section 5 reads it through `vss manual` -- the same validation, the
#      same E21 verification gate, the same basis machinery. The origin is
#      `sec-xbrl` and every figure's page reference is the us-gaap tag, the
#      context period and the accession number. That IS its page.
#   2. IT DERIVES NOTHING. A tag the filer does not use is DATA MISSING and
#      is named. Nothing is summed, netted, annualised or substituted, and
#      a near neighbour is listed under NOT_WRITTEN with the reason rather
#      than quietly filling a field. The ONE transformation applied is a
#      SIGN FLIP on the `Payments...` elements, which state a positive
#      outflow where this schema states a negative one -- the same
#      convention shift the schema already makes for finance costs, and
#      recorded on the field itself rather than assumed.
#   3. IT NEVER MIXES SOURCES within one ticker's history. XBRL states
#      whole units where a press release states millions, and a file
#      holding both is a file whose every sequential comparison is
#      meaningless. `write_manual_file` refuses an existing file whose
#      origin is not `sec-xbrl` rather than writing beside it.
#   4. ANNUAL, NOT QUARTERLY. The SEC dropped the Selected Quarterly
#      Financial Data requirement in 2021 and filers stopped tagging
#      discrete fourth quarters, so the newest COMPLETE tagged quarter can
#      lag the newest filing by months -- `untagged_tail` above is that
#      finding. Annual periods do not have the gap. They land in the
#      schema's `annual:` block (E15), which is keyed on the fiscal year
#      rather than on a period label, and E19's "as filed" branch carries
#      them.
#   5. A BACKUP CARRIES A TIME, not only a date. Three writers in this
#      project stamp `.bak-<date>` and lose the earlier of two runs made on
#      one day; this one stamps the hour, minute and second and a purpose.
#   6. NO AI ANYWHERE IN IT. Deterministic tag reads. Nothing here quotes,
#      summarises, infers or asks a model anything.

#: An annual duration, in days. A 52/53-week filer's year is 364 or 371.
ANNUAL_MIN_DAYS = 350
ANNUAL_MAX_DAYS = 380

#: How many fiscal years to write. Section 5 stands on ONE twelve-month
#: basis (E19) and reads the newest; the rest are history a reader can see
#: the trend in, and they cost nothing because the basis never touches them.
ANNUAL_LIMIT = 5


@dataclass(frozen=True)
class AnnualField:
    """One manual-schema field and the tags that may answer it.

    ``unit`` is named EXACTLY rather than inferred: a share count is filed
    in ``shares`` and an EPS in ``USD/shares``, and a reader that looked for
    the first money unit would find neither.

    ``negate`` is the sign convention and NOT a derivation. us-gaap's
    ``Payments...`` elements state an outflow as a POSITIVE number; this
    schema's capex and lease fields state an outflow as a NEGATIVE one, and
    section 5 SUMS the capex legs into operating cash flow. Flipping the
    sign is the same convention shift the schema already documents for
    finance costs ("enter a POSITIVE MAGNITUDE... statements print finance
    costs NEGATIVE"). It changes no magnitude and invents no figure.
    """

    field: str
    tags: tuple[str, ...]
    unit: str
    kind: str                    # "duration" | "instant"
    negate: bool = False
    note: str = ""


#: WHICH TAG ANSWERS WHICH FIELD -- the one judgement in this path, kept in
#: a table so it can be diffed and argued with, the way the appendix path's
#: judgement lives in `config/manual/maps/`.
#:
#: EVERY LIST IS SHORT ON PURPOSE. A long preference chain is substitution
#: wearing a schedule: the second tag gets used on the day the first is
#: absent, and nobody is told. Where two tags are genuinely one line under
#: two spellings the list holds both and the page reference names which was
#: taken. Where they are DIFFERENT QUANTITIES the list holds one and the
#: other is in NOT_WRITTEN below.
ANNUAL_FIELDS: tuple[AnnualField, ...] = (
    AnnualField(
        "revenue", TAGS["revenue"], MONEY, "duration",
        note="Total revenue. `operating_income` is deliberately NOT written "
             "beside it -- see OMITTED_FIELDS."),
    AnnualField(
        "net_income", ("NetIncomeLoss",), MONEY, "duration",
        note="Profit for the year attributable to the parent."),
    AnnualField(
        "diluted_eps", ("EarningsPerShareDiluted",), MONEY_PER_SHARE, "duration"),
    # --- the cash flow Method C discounts ---------------------------------
    AnnualField(
        "operating_cash_flow",
        ("NetCashProvidedByUsedInOperatingActivities",), MONEY, "duration",
        note="Net cash from operating activities, AFTER tax -- a US cash "
             "flow statement is laid out that way, so "
             "`operating_cash_flow_pretax` and `income_tax_paid` stay "
             "DATA MISSING and the pre-tax pair is never used."),
    AnnualField(
        "capex_ppe", ("PaymentsToAcquirePropertyPlantAndEquipment",),
        MONEY, "duration", negate=True,
        note="Additions to property, plant and equipment. The element "
             "states a POSITIVE payment; the sign is flipped to the "
             "schema's outflow convention and nothing else is done to it."),
    AnnualField(
        "capex_intangibles", ("PaymentsToAcquireIntangibleAssets",),
        MONEY, "duration", negate=True,
        note="Rarely tagged by a US filer. Where it IS tagged beside the "
             "PP&E line, the two are E23's split pair. Where it is not, the "
             "PP&E line is the ONE line the issuer prints and moves to "
             "`capex_combined` -- see `place_capex`. The element states a "
             "POSITIVE payment and the sign is flipped to the schema's "
             "outflow convention, as on `capex_ppe`."),
    AnnualField(
        "capex_combined", ("PaymentsToAcquireProductiveAssets",),
        MONEY, "duration", negate=True,
        note="E23's ONE LINE, and this field is NEVER a sum. It is filled "
             "by `place_capex` with the single capex line a filer tags, and "
             "is empty whenever the filer tags the split. ONE TAG OF ITS "
             "OWN (added 2026-08-29, a tag-map gap found on AOS): "
             "`PaymentsToAcquireProductiveAssets`, the broader element a "
             "filer uses when its one capex line is captioned 'capital "
             "expenditures' rather than PP&E -- A. O. Smith tags it (70.8m "
             "FY2025) and tags NO PropertyPlantAndEquipment element at all, "
             "so E23's one line was DATA MISSING for a filer that prints "
             "exactly one. Where a filer tags the PP&E element as well, "
             "`place_capex` keeps that and drops this: the PP&E line is "
             "the narrower concept. The element states a POSITIVE payment "
             "and the sign is flipped, as on `capex_ppe`."),
    AnnualField(
        "nci_dividends_paid", ("PaymentsOfDividendsMinorityInterest",
                               "PaymentsToMinorityShareholders",
                               "MinorityInterestDecreaseFromDistributions"
                               "ToNoncontrollingInterestHolders"),
        MONEY, "duration", negate=True,
        note="E105 (2026-09-04): THE CASH PAID TO NON-CONTROLLING "
             "INTERESTS over the window, a LEG of FCF0. THREE ELEMENTS AND "
             "NOT ONE, because US filers do not agree which to use for the "
             "same line: Accenture tags "
             "`PaymentsOfDividendsMinorityInterest` (3,492,000 FY2025, "
             "0001467373-25-000217), Lennox and NVR tag "
             "`PaymentsToMinorityShareholders`, GoDaddy tags "
             "`MinorityInterestDecreaseFromDistributionsTo"
             "NoncontrollingInterestHolders`. They are read in that order "
             "and the FIRST one present answers; a filer that tags two is "
             "tagging one line twice, and the narrower dividend element "
             "comes first. NOT `PaymentsForRepurchaseOfRedeemable"
             "NoncontrollingInterest`, which BUYS THE STAKE and is a "
             "transaction with the minority rather than a distribution to "
             "it -- Expand Energy tags 1,254,000,000 of it in FY2014 "
             "against 173,000,000 of dividends the same year, and reading "
             "the two as one field would put a stake purchase in the flow. "
             "The elements state a POSITIVE payment; the sign is flipped to "
             "the schema's outflow convention, as on `capex_ppe`. AN "
             "UNTAGGED YEAR IS DATA MISSING, never a zero: E105 refuses a "
             "coerced zero because it would report the record complete "
             "while overstating the flow by the whole of a group's "
             "distributions."),
    AnnualField(
        "sbc", ("ShareBasedCompensation",
                "AllocatedShareBasedCompensationExpense"), MONEY, "duration",
        note="E36: SHARE-BASED COMPENSATION IS A COST and FCF0 subtracts "
             "it. `us-gaap:ShareBasedCompensation` is the cash-flow "
             "statement's own non-cash add-back line, which is exactly the "
             "charge that made it free -- DECK 44,835,000 FY2026, NKE "
             "715,000,000 FY2026. A US filer settles in stock, so the "
             "equity/cash split E36 makes for an IFRS filer does not arise. "
             "`AllocatedShareBasedCompensationExpense` (added 2026-08-29, a "
             "tag-map gap found on AOS) is the INCOME STATEMENT'S charge, "
             "read only where the add-back element is absent -- A. O. "
             "Smith tags the charge (13.8m FY2025) and never the add-back. "
             "The page line says which concept was taken (CONCEPT_NOTES)."),
    AnnualField(
        "finance_costs_paid", ("InterestPaidNet",), MONEY, "duration",
        note="INTEREST PAID IN CASH, from the supplemental cash-flow "
             "disclosure. A POSITIVE MAGNITUDE, which is the sign this "
             "schema states finance costs in.\n"
             "THE OTHER HALF IS NOT TAGGED BY A US FILER. E18 forms "
             "`net_interest_paid` as paid MINUS received, both from the cash "
             "flow statement, and a US filer states interest RECEIVED only on "
             "the income statement (`InvestmentIncomeInterest`) -- a "
             "different quantity, what was EARNED rather than what arrived. "
             "So `finance_income_received` is DATA MISSING and the cash net "
             "does not form. E34.1 RULED the sub-case: the add-back is the "
             "INCOME STATEMENT'S net -- the three fields below -- stored "
             "with `interest_source: income_statement_net` and printed as "
             "an accrual proxy. THIS FIGURE IS NEVER THE NET ON ITS OWN: on "
             "Nike FY2026 that would add back 323m against a true net of "
             "-50m, an income."),
    AnnualField(
        "finance_costs_period", ("InterestExpenseNonoperating",
                                 "InterestExpenseOther"),
        MONEY, "duration",
        note="E34.1 / E18: the income statement's interest EXPENSE, one "
             "half of the pair the store subtracts into `net_finance_costs` "
             "where the net itself is not tagged (Deckers: 2,530,000 FY2026 "
             "beside interest income of 63,613,000, a net INCOME). A "
             "POSITIVE MAGNITUDE. `InterestExpenseOther` (added 2026-08-29, "
             "a tag-map gap found on LII) is the residual 'other' element "
             "Lennox uses for its gross expense: 46.4m FY2025 beside "
             "`InvestmentIncomeInterest` 5.5m, and its own `InterestExpense` "
             "40.9m is exactly the difference -- E18's subtraction of two "
             "stated figures, which the store already performs, not a "
             "reconstruction (E22 forbids inferring a figure the accounts "
             "do not state; both operands here are stated). It serves ONLY "
             "as the pair operand: E61's gross-only proxy names "
             "`InterestExpenseNonoperating` and fires on that tag alone "
             "(E61_GROSS_INTEREST_TAG). `InterestExpense` itself is NOT an "
             "alias -- see NOT_WRITTEN."),
    AnnualField(
        "finance_income_period", ("InvestmentIncomeInterest",),
        MONEY, "duration",
        note="E34.1 / E18: the income statement's interest INCOME -- what "
             "was EARNED, which is why it cannot stand in for interest "
             "received in cash. The other half of the pair above."),
    AnnualField(
        "net_finance_costs", ("InterestIncomeExpenseNonoperatingNet",),
        MONEY, "duration", negate=True,
        note="E34.1: THE NET THE INCOME STATEMENT PRINTS -- Nike's "
             "'Interest expense (income), net'. The element is POSITIVE for "
             "a net INCOME (Nike FY2022 -205,000,000 in the year it printed "
             "a net expense of 205; FY2024 +161,000,000 in the year it "
             "printed (161)), and this schema holds a net COST as a positive "
             "magnitude, so the sign is flipped: Nike FY2026 +50,000,000 "
             "lands here as -50,000,000, a net interest income that FCF0 "
             "REMOVES rather than adds back. Where the filer tags the pair "
             "and not the net, E18 forms it from the two fields above."),
    AnnualField(
        "lease_payments_capital", ("FinanceLeasePrincipalPayments",),
        MONEY, "duration", negate=True,
        note="The CAPITAL element of a FINANCE lease rental, which under "
             "ASC 842 sits in FINANCING and is therefore outside operating "
             "cash flow. A MEMO since E70 (2026-08-30): FCF0 deducts no "
             "lease principal -- the lease is charged once, in net debt. "
             "`OperatingLeasePayments` is NOT this figure; it is the field "
             "below."),
    AnnualField(
        "operating_lease_payments", ("OperatingLeasePayments",), MONEY, "duration",
        note="E70 (2026-08-30): the cash paid for OPERATING leases, which "
             "under ASC 842-20-45-5(a) is INSIDE operating cash flow. It was "
             "NOT_WRITTEN until E70 (B33), because writing it looked like "
             "basis 2 deducting it twice; E70 turned it round: the lease is "
             "charged once, in net debt (E35, E65), so the payment the flow "
             "bore is ADDED BACK to FCF0, principal under E70 and the "
             "interest inside the single lease payment under E34. A POSITIVE "
             "MAGNITUDE. Absent is DATA MISSING for FCF0 on a `yes` filer "
             "(A. O. Smith states the expense and not the cash paid)."),
    # --- net debt: the bridge from enterprise value to equity -------------
    AnnualField(
        "pension_deficit",
        ("PensionAndOtherPostretirementDefinedBenefitPlansLiabilitiesNoncurrent",
         "DefinedBenefitPensionPlanLiabilitiesNoncurrent"),
        MONEY, "instant",
        note="E35.1: the recognised defined-benefit LIABILITY, a leg of net "
             "debt. `PensionAndOtherPostretirement...` is the CONSOLIDATED "
             "concept covering both pension and other post-retirement "
             "plans together; `DefinedBenefitPensionPlanLiabilitiesNoncurrent` "
             "(added after a tag-map bug on CTSH, 2026-08-28) is the "
             "pension-plan-only concept a filer with no OTHER "
             "post-retirement obligation may use instead -- CTSH tags the "
             "second and not the first. Neither Nike nor Deckers tags "
             "either -- absence of a tag is DATA MISSING, not zero; a "
             "filer with no plan says so in its benefit-plan note and the "
             "sentence is entered by hand on E25's `note` form. "
             "`DefinedBenefitPlanFundedStatusOfPlan` is a SIGNED net of "
             "assets and obligations and is not this field. NEITHER TAG "
             "REACHES A SECOND DEFINED-BENEFIT PLAN A FILER PRESENTS UNDER "
             "A DIFFERENT NAME (E62: CTSH's India gratuity plan is such a "
             "plan and is not tagged under any concept at all -- E62's sum "
             "is entered by hand, this field's tags supply only the "
             "pension-captioned leg)."),
    AnnualField(
        "asset_retirement_obligation", ("AssetRetirementObligation",),
        MONEY, "instant",
        note="E68 (2026-08-29): a legally required, discounted, cash-settled "
             "decommissioning obligation is DEBT IN SUBSTANCE and a leg of "
             "net debt. THE STATED TOTAL. Where the filer tags no total but "
             "both `AssetRetirementObligationsNoncurrent` and "
             "`AssetRetirementObligationCurrent`, `apply_debt_rulings` adds "
             "the two stated parts on E66's precedence and names both; a "
             "lone non-current element is NOT the obligation (DECK 36.8m at "
             "2026-03-31, no total, no current) and leaves the leg DATA "
             "MISSING with the part named. Absent is DATA MISSING, never "
             "zero (E25 `note` form for a filer that has none). Expand "
             "Energy 724m at 2025-12-31, 14.5% of its borrowings."),
    AnnualField(
        "cash_and_equivalents", ("CashAndCashEquivalentsAtCarryingValue",),
        MONEY, "instant",
        note="Cash and equivalents at the balance sheet date. SHORT-TERM "
             "INVESTMENTS ARE NOT INCLUDED -- whether they count as cash is "
             "assumption A1, which is the owner's to throw, and folding "
             "them in here would decide it invisibly."),
    AnnualField(
        "financial_liabilities_current", ("LongTermDebtCurrent",
                                          "ShortTermBorrowings",
                                          "CommercialPaper"),
        MONEY, "instant",
        note="BORROWINGS ALONE (E14). Under ASC 842 operating leases are "
             "presented separately and are not inside this element, which "
             "is what makes the E14 split hold on a US filer without any "
             "note being read. `ShortTermBorrowings` (added after a "
             "tag-map bug on CTSH, 2026-08-28) is the tag a filer uses "
             "when it captions the line 'Short-term debt' rather than "
             "presenting a 'current portion of long-term debt' line -- "
             "CTSH's $33m current maturity of its Term Loan is tagged "
             "under this element and NOT under `LongTermDebtCurrent`, "
             "which this filer does not use at all. Before this fix the "
             "map read that absence as the filer stating no current debt; "
             "it was this map's own gap, not a fact about the filer. "
             "`CommercialPaper` (added 2026-08-29, found on LII) is the "
             "element for paper outstanding. E66 (ruled the same day): TWO "
             "STATED CURRENT-BORROWING CAPTIONS ARE ADDED, NOT CHOSEN "
             "BETWEEN -- `apply_debt_rulings` overrides this field after the "
             "map: `DebtCurrent`, the taxonomy's subtotal, wins where tagged; "
             "otherwise `LongTermDebtCurrent` plus ONE of `ShortTermBorrowings` "
             "or `CommercialPaper` (short-term borrowings is by definition a "
             "subtotal that includes paper), every component on the page "
             "line. Lennox 2025-12-31: 18.3m + 226.0m = 244.3m."),
    AnnualField(
        "financial_liabilities_noncurrent", ("LongTermDebtNoncurrent",
                                            "NotesPayable"),
        MONEY, "instant",
        note="Borrowings alone, on the same terms, and additive with the "
             "current leg and with `lease_liabilities`.\n"
             "E124 (2026-09-20): `NotesPayable` is HERE and not in the "
             "current leg because a filer that presents an UNCLASSIFIED "
             "balance sheet states ONE debt caption and no current / "
             "non-current split. PulteGroup 2025-12-31: 'Notes payable "
             "1,631,098', a stated subtotal that note 5 reconciles exactly "
             "(total senior notes 1,583,913 + other notes payable 47,185), "
             "so E26's two-captions-no-total problem does not arise and "
             "E71's summing is not needed. THE WHOLE CAPTION ENTERS THIS "
             "LEG and the current leg stays absent: inventing a split "
             "would be fabrication, and nothing in section 5 or Gate 3 "
             "reads the split -- net debt ADDS the two legs.\n"
             "AND `us-gaap:LongTermDebt` IS EXCLUDED BY NAME for this "
             "shape. PulteGroup tags 43,900,000 under it, and the filing "
             "says what it is: 'aggregate outstanding debt of "
             "unconsolidated joint ventures', OFF BALANCE SHEET and "
             "generally non-recourse. It is not the filer's borrowing and "
             "a generic reach for that element would import someone "
             "else's liability.\n"
             "WHAT THIS LEG CANNOT SEE, AND IT IS SAID HERE: a CAPTIVE "
             "FINANCE SUBSIDIARY's debt. PulteGroup presents 'Financial "
             "Services debt 532,338' as its own caption beside Notes "
             "payable, and that line is ABSENT FROM THE companyfacts API "
             "UNDER EVERY NAMESPACE (searched 2026-09-20 by exact value "
             "across us-gaap, dei and srt): the filer tags it with a "
             "custom element the API does not expose. A tag-built store "
             "CANNOT reach it. It is carried in `captive_finance_debt`, "
             "read from the filing, and where no document supplies it "
             "E123's second capitalisation line reads DATA MISSING -- "
             "never omitted, because an omitted line and a zero look "
             "identical in a packet.\n"
             "E67 (2026-08-29): "
             "where this element is untagged and the filer presents "
             "borrowings and finance leases as ONE line "
             "(`LongTermDebtAndCapitalLeaseObligations`), `apply_debt_rulings` "
             "reads that line whole, names the finance lease inside it "
             "(`FinanceLeaseLiabilityNoncurrent`, which must be tagged -- "
             "otherwise REFUSED rather than guessed), and E65 does not add "
             "that lease again. Lennox 2025-12-31: 1,144.1m incl. 50.6m."),
    AnnualField(
        "operating_lease_liabilities", ("OperatingLeaseLiability",), MONEY,
        "instant",
        note="E117 (2026-09-19): the OPERATING lease liability, which LEAVES "
             "net debt because its rent is in the flow. The same stated total "
             "`lease_liabilities` starts from, before E65 adds finance leases; "
             "where only E71's two parts are tagged, their sum, captured "
             "under this name too."),
    AnnualField(
        "lease_liabilities", ("OperatingLeaseLiability",), MONEY, "instant",
        note="THE STATED OPERATING TOTAL (E26). Where a filer tags only "
             "`OperatingLeaseLiabilityCurrent` and "
             "`OperatingLeaseLiabilityNoncurrent` and never their total, "
             "this field is DATA MISSING and both components are named in "
             "the report -- adding them here would be a sum no rule "
             "authorises. E65 (2026-08-29): FINANCE LEASES ARE IN NET DEBT "
             "TOO -- `apply_debt_rulings` adds `FinanceLeaseLiability` (or "
             "its two stated parts) LESS whatever finance lease a borrowing "
             "leg already holds (E67), and the page line states every "
             "component. Lennox 2025-12-31: 382.3m + (68.9 - 18.3 - 50.6 = "
             "0.0) = 382.3m."),
    # --- the divisor ------------------------------------------------------
    AnnualField(
        "shares_point_in_time",
        ("CommonStockSharesOutstanding",), "shares", "instant",
        note="E38's MEMO, at the year end. A tagged fact -- DECK 139,978,000 "
             "at 2026-03-31 -- and NEVER the divisor: it is a stock and the "
             "flow it would divide is a window. B36 said neither this "
             "element nor the cover-page count was tagged; both are, and the "
             "path simply never asked. See also `dei:EntityCommonStock"
             "SharesOutstanding` in DEI_SHARES_TAG, the cover count, which "
             "is written only where its own date falls inside the year's "
             "filing window."),
    AnnualField(
        "diluted_weighted_average_shares",
        ("WeightedAverageNumberOfDilutedSharesOutstanding",),
        "shares", "duration",
        note="The WEIGHTED AVERAGE over the year. It is NOT the period-end "
             "count and NOT the cover page's outstanding count, and those "
             "are DIFFERENT CONCEPTS -- a flow against a stock.\n"
             "CORRECTED 2026-08-26: this note said *neither of those is a "
             "tagged fact*, and both are. "
             "`us-gaap:CommonStockSharesOutstanding` is tagged at every "
             "quarter end (DECK 139,978,000 at 2026-03-31; 136,725,000 at "
             "2026-06-30) and `dei:EntityCommonStockSharesOutstanding` on "
             "every cover page (136,414,227 as of 2026-07-09 -- the figure "
             "the hand run used). This path could not reach them because it "
             "never asked: `_entries` opened `us-gaap` alone and this map "
             "listed one count. A reader's choice, not a source's limit "
             "(B36, corrected)."),
)

#: E61 names ONE element for its gross-only proxy, and the writer fires the
#: proxy on that tag alone. A gross expense reached through another alias
#: (`InterestExpenseOther`) is E18's pair operand and nothing more: with no
#: income leg beside it, FCF0 is DATA MISSING rather than a gross add-back on
#: an element no ruling covers.
E61_GROSS_INTEREST_TAG = "InterestExpenseNonoperating"

#: WHICH CONCEPT WAS TAKEN, written on the figure's own page line (E40)
#: whenever an alias answers a field with a DIFFERENT CONCEPT from the
#: field's first tag. A later reader of the file must be able to see that
#: without opening this map.
CONCEPT_NOTES: dict[str, str] = {
    "AllocatedShareBasedCompensationExpense": (
        " -- CONCEPT: the INCOME-STATEMENT share-based compensation CHARGE, "
        "taken because this filer tags no `ShareBasedCompensation` (the "
        "cash-flow statement's non-cash add-back). E36 subtracts the cost "
        "either way; the two elements state one charge from two statements "
        "and can differ by any capitalised or discontinued portion"),
    "PaymentsToAcquireProductiveAssets": (
        " -- CONCEPT: the filer's ONE capital-expenditure line, tagged under "
        "the broader 'productive assets' element and not the PP&E one; E23's "
        "combined line, a record of the issuer's presentation and not a claim "
        "about what is inside it"),
    "CommercialPaper": (
        " -- CONCEPT: commercial paper outstanding, read as the current "
        "borrowing because this filer tags neither a current-maturities nor "
        "a short-term-borrowings element at this year end"),
    "InterestExpenseOther": (
        " -- CONCEPT: the residual 'other' interest-expense element, read as "
        "the income statement's GROSS interest expense and only as E18's pair "
        "operand beside `InvestmentIncomeInterest`; never the add-back on its "
        "own (E61 names `InterestExpenseNonoperating`)"),
}

#: E26's components: named when the total above is absent, never added.
LEASE_LIABILITY_PARTS = ("OperatingLeaseLiabilityCurrent",
                         "OperatingLeaseLiabilityNoncurrent")

#: TAGS READ AND DELIBERATELY NOT WRITTEN. Each one looks like it answers a
#: field and answers a DIFFERENT QUESTION. This table is printed in the
#: report so a reader can see what was passed over and why, rather than
#: discovering later that a near neighbour had been quietly accepted.
NOT_WRITTEN: tuple[tuple[str, str, str], ...] = (
    ("NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
     "operating_cash_flow",
     "CONTINUING OPERATIONS ONLY. It is a different quantity from the total, "
     "and a filer that tags both is stating two figures, not one figure "
     "twice."),
    (" + ".join(LEASE_LIABILITY_PARTS), "lease_liabilities",
     "Two captions the filer states and never totals. E26: the total is DATA "
     "MISSING and both components are named. They are printed in the report "
     "below when the stated total is absent."),
    ("ShortTermInvestments", "cash_and_equivalents",
     "Whether short-term investments count as cash is assumption A1. It is "
     "the owner's to throw and is not decided by a fetch."),
    ("InterestExpense", "finance_costs_period / net_finance_costs",
     "The element carries a DIFFERENT LINE for different filers. Lennox "
     "tags it for its NET line ('Interest expense, net' 40.9m FY2025 = "
     "`InterestExpenseOther` 46.4m - `InvestmentIncomeInterest` 5.5m) and "
     "A. O. Smith for its GROSS line (13.5m, equal to `InterestPaidNet`). "
     "Read blind it would be netted twice for one filer and never for the "
     "other, so it answers neither field. Found 2026-08-29; the LII pair "
     "is read through `InterestExpenseOther` instead."),
)

#: THE SAME JUDGEMENT, FOR AN IFRS FILER. A separate table and not a
#: fallback chain: `ifrs-full` is a different vocabulary, not a set of
#: aliases for the one above, and a reader that tried us-gaap first and
#: IFRS second would silently answer an IFRS field with a US element the
#: day both happened to exist.
#:
#: Read from the facts of SAP SE (CIK 1000184) and Unilever PLC (217410) on
#: 2026-08-26. The two filers between them exercise both capex shapes E23
#: names: SAP tags ONE combined line and no split, Unilever tags the split
#: pair and no combined line.
IFRS_ANNUAL_FIELDS: tuple[AnnualField, ...] = (
    AnnualField(
        "revenue", ("Revenue",), MONEY, "duration",
        note="Total revenue. `operating_income` is deliberately NOT written "
             "beside it -- see OMITTED_FIELDS, which holds for both "
             "taxonomies and for the same reason."),
    AnnualField(
        "net_income", ("ProfitLossAttributableToOwnersOfParent",),
        MONEY, "duration",
        note="Profit for the year ATTRIBUTABLE TO THE PARENT. `ProfitLoss` "
             "is the group total INCLUDING the minorities' share and is a "
             "different quantity -- SAP FY2025: 7,161 against 7,326, the "
             "165 being the non-controlling interests. See NOT_WRITTEN."),
    AnnualField(
        "diluted_eps", ("DilutedEarningsLossPerShare",),
        MONEY_PER_SHARE, "duration"),
    # --- the cash flow Method C discounts ---------------------------------
    AnnualField(
        "operating_cash_flow", ("CashFlowsFromUsedInOperatingActivities",),
        MONEY, "duration",
        note="Net cash from operating activities. UNLIKE ASC 230, IAS 7.31-34 "
             "lets the filer put interest paid in operating OR in financing, "
             "so this field's relation to interest is NOT fixed by the "
             "taxonomy -- see `InterestPaidClassifiedAs...` in NOT_WRITTEN."),
    AnnualField(
        "capex_ppe",
        ("PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",),
        MONEY, "duration", negate=True,
        note="Additions to property, plant and equipment. The element states "
             "a POSITIVE payment; the sign is flipped to the schema's "
             "outflow convention and nothing else is done to it."),
    AnnualField(
        "capex_intangibles",
        ("PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities",),
        MONEY, "duration", negate=True,
        note="Where it is tagged beside the PP&E line -- Unilever tags both "
             "-- the two are E23's split pair."),
    AnnualField(
        "capex_combined",
        ("PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwill"
         "InvestmentPropertyAndOtherNoncurrentAssets",),
        MONEY, "duration", negate=True,
        note="E23's ONE LINE, and UNLIKE the us-gaap map this one HAS a tag: "
             "IFRS gives a filer that prints a single capital-expenditure "
             "line an element for exactly that, and SAP uses it (FY2025 739). "
             "It is still never a sum, and `place_capex` still refuses a mix "
             "-- a filer tagging this AND the split pair gets the split."),
    AnnualField(
        "sbc",
        ("ExpenseFromEquitysettledSharebasedPaymentTransactionsInWhichGoods"
         "OrServicesReceivedDidNotQualifyForRecognitionAsAssets",),
        MONEY, "duration",
        note="E36, EQUITY-SETTLED ONLY. SAP FY2025: 1,331 equity-settled "
             "inside a 1,695 total, the other 364 being CASH-settled, which "
             "flowed through operating cash flow as cash when it was paid "
             "and is therefore already borne by FCF0. Deducting the total "
             "would charge it twice -- 134.82 against 141.74 on SAP's "
             "Method C. A filer that tags only a total is DATA MISSING here; "
             "see NOT_WRITTEN."),
    AnnualField(
        "finance_costs_paid",
        ("InterestPaidClassifiedAsOperatingActivities",),
        MONEY, "duration",
        note="INTEREST PAID IN CASH, and only the OPERATING spelling. Where "
             "the filer books it in financing its operating cash flow never "
             "bore it, there is nothing to add back (E34), and entering it "
             "here would invite exactly that. A POSITIVE MAGNITUDE."),
    AnnualField(
        "finance_income_received",
        ("InterestReceivedClassifiedAsOperatingActivities",),
        MONEY, "duration",
        note="INTEREST RECEIVED IN CASH, the operating spelling. The other "
             "half of E18's pair; where only one of the two is stated, both "
             "and their net are DATA MISSING."),
    AnnualField(
        "lease_payments_capital",
        ("PaymentsOfLeaseLiabilitiesClassifiedAsFinancingActivities",),
        MONEY, "duration", negate=True,
        note="The CAPITAL element of a lease rental. Under IFRS 16.50 it "
             "sits in FINANCING and is therefore outside operating cash "
             "flow, so FCF basis 2 may deduct it without double counting."),
    # --- net debt: the bridge from enterprise value to equity -------------
    AnnualField(
        "pension_deficit", ("RecognisedLiabilitiesDefinedBenefitPlan",),
        MONEY, "instant",
        note="E35.1: the recognised defined-benefit LIABILITY -- SAP 249 at "
             "2025-12-31 -- a leg of net debt. The separately tagged "
             "`RecognisedAssetsDefinedBenefitPlan` (SAP 19) is NOT netted: "
             "no field holds a pension asset and omitting an asset is the "
             "conservative direction. `DefinedBenefitObligationAtPresentValue` "
             "(SAP 2,358) is the GROSS obligation before plan assets and is "
             "not this field."),
    AnnualField(
        "asset_retirement_obligation",
        ("ProvisionForDecommissioningRestorationAndRehabilitationCosts",),
        MONEY, "instant",
        note="E68: the decommissioning provision, the IFRS equivalent of "
             "`AssetRetirementObligation`. Element name per the ifrs-full "
             "taxonomy; no filer on file tags it, so it has never supplied a "
             "figure -- absent is DATA MISSING, never zero."),
    AnnualField(
        "cash_and_equivalents", ("CashAndCashEquivalents",), MONEY, "instant",
        note="SHORT-TERM INVESTMENTS ARE NOT INCLUDED -- whether they count "
             "as cash is assumption A1, and `OtherFinancialAssets` is left "
             "in NOT_WRITTEN for that reason."),
    AnnualField(
        "financial_liabilities_current",
        ("CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings",
         "ShorttermBorrowings"),
        MONEY, "instant",
        note="BORROWINGS ALONE (E14). The consolidated `Borrowings` element "
             "is NOT read into this field: under IFRS 16 the face-of-balance "
             "-sheet line may contain the leases, and E14's split has to come "
             "from the tags that state it. SAP tags this split (FY2025: 1,600 "
             "current + 4,550 non-current = the 6,150 of `Borrowings`); "
             "Unilever tags only the consolidated line, so BOTH borrowing "
             "fields are DATA MISSING for it and net debt does not form."),
    AnnualField(
        "financial_liabilities_noncurrent",
        ("LongtermBorrowings", "NoncurrentBorrowings"), MONEY, "instant",
        note="Borrowings alone, on the same terms, and additive with the "
             "current leg and with `lease_liabilities`."),
    AnnualField(
        "lease_liabilities", ("LeaseLiabilities",), MONEY, "instant",
        note="THE STATED TOTAL ONLY (E26). Where a filer tags only "
             "`CurrentLeaseLiabilities` and `NoncurrentLeaseLiabilities` and "
             "never their total, this field is DATA MISSING and both "
             "components are named in the report."),
    AnnualField(
        "nci_dividends_paid",
        ("DividendsPaidToNoncontrollingInterestsClassifiedAsFinancing"
         "Activities", "DividendsPaidToNoncontrollingInterests"),
        MONEY, "duration", negate=True,
        note="E105 (2026-09-04): the IFRS half of the same leg. SAP tags "
             "the CLASSIFIED-AS-FINANCING element from FY2018 on (FY2025 "
             "2,000,000; FY2024 1,000,000; FY2023 13,000,000 -- "
             "0001104659-26-020058) and the bare element on the older "
             "20-Fs, so both are read, the classified one first. The "
             "element states a POSITIVE payment and the sign is flipped. "
             "IT DOES NOT REACH A TTM BASIS: SAP tags this annually only, "
             "and a window spanning two fiscal years is built from the "
             "quarterly statements under E86 -- which is how SAP.DE's own "
             "-30,000,000 was formed, and why the FY2025 tag of -2,000,000 "
             "is a check on it rather than the figure."),
    # --- the divisor ------------------------------------------------------
    AnnualField(
        "shares_point_in_time", ("NumberOfSharesOutstanding",),
        "shares", "instant",
        note="E38's MEMO, at the year end, where the filer tags one. NOT "
             "`dei:EntityCommonStockSharesOutstanding`, which on a 20-F is "
             "the ISSUED count including treasury -- SAP states 1,228,504,232 "
             "for every year 2021-2025, which is `NumberOfSharesIssued` and "
             "not an outstanding count."),
    AnnualField(
        "diluted_weighted_average_shares", ("AdjustedWeightedAverageShares",),
        "shares", "duration",
        note="IFRS calls the DILUTED weighted average `Adjusted...`; the "
             "undiluted one is `WeightedAverageShares`, which is a different "
             "quantity and is not written. Assumption A6 is the owner's to "
             "throw between an average and a period-end count."),
)

#: E26's two captions for an IFRS filer.
IFRS_LEASE_LIABILITY_PARTS = ("CurrentLeaseLiabilities",
                              "NoncurrentLeaseLiabilities")

IFRS_NOT_WRITTEN: tuple[tuple[str, str, str], ...] = (
    ("ProfitLoss", "net_income",
     "THE GROUP TOTAL, including the share belonging to non-controlling "
     "interests. `net_income` is the parent's share and the two differ by "
     "exactly the minorities -- SAP FY2025 7,326 against 7,161. A filer "
     "tagging both is stating two figures, not one figure twice."),
    ("CashFlowsFromUsedInOperatingActivitiesContinuingOperations",
     "operating_cash_flow",
     "CONTINUING OPERATIONS ONLY, as its us-gaap twin. A different quantity "
     "from the total."),
    ("Borrowings", "financial_liabilities_current / _noncurrent",
     "THE CONSOLIDATED LINE. E14: where an issuer states only the "
     "consolidated borrowings figure and does not split it, both fields are "
     "DATA MISSING -- never the consolidated figure in one of them. Unilever "
     "is that case (26,038 at 2025-12-31 and no split tagged); SAP is not."),
    (" + ".join(IFRS_LEASE_LIABILITY_PARTS), "lease_liabilities",
     "Two captions the filer states and never totals. E26: the total is DATA "
     "MISSING and both components are named. They are printed in the report "
     "below when the stated total is absent."),
    ("OtherFinancialAssets", "other_current_financial_assets",
     "Whether financial assets count as cash is assumption A1, the owner's to "
     "throw. The element is also a TOTAL across current and non-current -- "
     "SAP's 8,821 at 2025-12-31 is mostly the 7,269 of non-current venture "
     "and debt investments -- and A1 as thrown on SAP asked only about the "
     "current line, so writing the total here would answer a question nobody "
     "put."),
    ("InterestPaidClassifiedAsFinancingActivities / "
     "InterestPaidClassifiedAsOperatingActivities / "
     "InterestReceivedClassifiedAsInvestingActivities / "
     "InterestReceivedClassifiedAsOperatingActivities",
     "net_interest_paid + where the filer books it",
     "THE FIELD THAT WOULD HOLD THE ANSWER DOES NOT EXIST YET. IAS 7.31-34 "
     "lets a filer put interest in operating or in financing, and which it "
     "chose decides whether FCF0 is a flow to the firm or to equity -- the "
     "largest single ERROR REVIEW-4 found. SAP tags BOTH spellings, for "
     "different years, because it reclassified in January 2025. Left unread "
     "until the schema carries the classification."),
    ("AdjustmentsForSharebasedPayments / "
     "ExpenseFromSharebasedPaymentTransactionsInWhichGoodsOrServicesReceived"
     "DidNotQualifyForRecognitionAsAssets / "
     "ExpenseFromSharebasedPaymentTransactionsWithEmployees", "sbc",
     "TOTALS THAT INCLUDE CASH-SETTLED AWARDS. E36 deducts the "
     "EQUITY-SETTLED charge only: a cash-settled award flows through "
     "operating cash flow as cash when it is paid, so FCF0 already bears it "
     "and deducting it here would charge it twice. SAP FY2025: 1,695 total, "
     "1,331 equity-settled, 364 cash-settled. A filer that tags only a "
     "total states a DIFFERENT QUANTITY, and `sbc` stays DATA MISSING for "
     "it -- Unilever is that case."),
    ("NoncontrollingInterests", "the enterprise-to-equity bridge",
     "The minorities' share of equity. `manual.FIELDS` carries no field for "
     "it -- nor for pensions, associates, preferred or convertibles -- so the "
     "bridge this schema can express is net financial debt plus or minus "
     "leases, and nothing else."),
)

#: FIELDS THIS PATH DOES NOT WRITE AT ALL, and why. Not a coverage gap: each
#: is a decision, and a decision is worth more written down than implied by
#: a missing row.
OMITTED_FIELDS: tuple[tuple[str, str], ...] = (
    ("operating_income",
     "us-gaap:OperatingIncomeLoss is tagged by many filers and NOT by all "
     "-- NIKE publishes no operating income line and tags none. Until E79 "
     "(2026-08-30) writing it where tagged would have tripped the loader's "
     "UNRECONCILED check, which demanded an `op_margin` beside it; E79 "
     "withdrew that check (a stated EBIT with no stated margin enters), so "
     "the obstacle is gone. WRITING the field from this path is a separate "
     "decision the ruling did not take, and it is still left out here. No "
     "method of section 5's engine reads it: its readers are the ranking "
     "key, Method B and the margin check."),
    ("ebitda / net_debt_ebitda",
     "Not tagged by anybody. EBITDA is a non-GAAP measure and us-gaap has no "
     "element for it; deriving one from operating income and depreciation is "
     "the substitution this module exists not to make. Gate 3's leverage limb "
     "reads DATA MISSING in consequence."),
    ("free_cash_flow_reported",
     "A non-GAAP memo with no us-gaap element. Absent, not zero."),
    ("gross_profit / total_assets / net_ppe",
     "Ranking-key fields. `as_record` builds the store's series from "
     "`periods:` only, so an annual-only file supplies the ranking key "
     "nothing whatever they held. Out of scope rather than absent."),
    ("market: enterprise_value / market_cap",
     "Priced facts. They belong to a date, not to a fiscal year, and no "
     "price is fetched here."),
)


#: THE FIELDS A SHARE SPLIT CHANGES THE MAGNITUDE OF.
#:
#: A split is not a restatement and not a business event: the company is the
#: same, the count and every per-share figure are on a different basis, and
#: `_pick` -- which takes the newest filing -- reports it as *"RESTATED 29.16
#: -> 4.86"* (REVIEW-4 report B 7.1). Where the newest filing is OLDER than
#: the split, nothing restates the year at all and the figure simply stays on
#: the old basis beside neighbours on the new one. `config/manual/DECK.yaml`
#: holds exactly that: FY2022 `diluted_eps` 16.26 and 27,789,000 shares --
#: filed 2024-05-24, before the 6-for-1 split of 2024-09-13 -- beside FY2023's
#: 3.23 and 160,111,000. A 5.8x step in a count inside one file.
#:
#: NOTHING IS RESCALED. The figure as filed is the figure as filed; what
#: changes is that the page reference now says which basis it is on.
SPLIT_SENSITIVE_FIELDS = ("diluted_eps", "diluted_weighted_average_shares",
                          "shares_outstanding_period_end",
                          "shares_issued_period_end",
                          "treasury_shares_period_end",
                          # E38's memo. A count stated on one day is as
                          # split-sensitive as an average over a year, and
                          # DECK's FY2022 and FY2023 memos are both filed
                          # before the 2024 split.
                          "shares_point_in_time")


@dataclass(frozen=True)
class Split:
    """One share split the filer tagged: when it took effect and by how much."""

    effective: date
    ratio: float
    first_filed: str
    tag: str

    def __str__(self) -> str:
        return (f"{self.ratio:g}-for-1 split effective "
                f"{self.effective.isoformat()} (`{self.tag}`, first filed "
                f"{self.first_filed})")


def stock_splits(facts: dict,
                 taxonomy: "Taxonomy | None" = None) -> list["Split"]:
    """Every share split this filer tagged, oldest first.

    One split is tagged by several filings in a row; they are collapsed on
    (effective date, ratio) and the EARLIEST filing date is kept, because
    what the note has to answer is "was this figure filed before the split
    was declared".
    """
    taxonomy = taxonomy or US_GAAP_TAXONOMY
    seen: dict[tuple[str, float], tuple[str, str]] = {}
    for tag in taxonomy.split_tags:
        for entry in _entries(facts, tag, "pure", taxonomy=taxonomy.name):
            if not entry.get("end"):
                continue
            key = (entry["end"], float(entry["val"]))
            filed = entry.get("filed", "")
            if key not in seen or filed < seen[key][0]:
                seen[key] = (filed, tag)
    return sorted(
        (Split(effective=date.fromisoformat(end), ratio=ratio,
               first_filed=filed, tag=tag)
         for (end, ratio), (filed, tag) in seen.items()),
        key=lambda split: split.effective)


#: ASC 230-10-45-17(d): interest paid is an OPERATING cash outflow for
#: every US filer, without exception and without a tag to read. The
#: citation is what goes on the emitted file's `page:`, because E34 asks
#: for a page and a standard IS the page here.
ASC_230_CITATION = ("ASC 230-10-45-17(d): under US GAAP interest paid is an "
                    "OPERATING cash outflow for every filer, so this filer's "
                    "`operating_cash_flow` already bears its interest. No tag "
                    "states it because the standard leaves no choice to state")


def interest_classification(facts: dict, year: "AnnualYear",
                            taxonomy: "Taxonomy | None" = None,
                            currency: str = "USD") -> tuple[bool, str] | None:
    """E34's `interest_in_ocf` for one fiscal year, or None if unanswerable.

    us-gaap: ALWAYS `yes`, from the standard rather than from a tag.

    ifrs-full: from the two `InterestPaidClassifiedAs...` elements AT THIS
    YEAR END. A filer that tags NEITHER is unanswerable and gets None --
    never a default. A filer that tags BOTH for one year is also None: SAP
    tags financing for FY2025 and its FY2024 20-F tagged the identical
    amounts as operating, because it reclassified in January 2025, so
    "both" is a real state and a reader has to settle it.
    """
    taxonomy = taxonomy or US_GAAP_TAXONOMY
    if not taxonomy.interest_operating_tags and not taxonomy.interest_financing_tags:
        return True, ASC_230_CITATION
    end_s = year.end.isoformat()

    def tagged(tags):
        for tag in tags:
            for entry in _entries(facts, tag, currency, taxonomy=taxonomy.name):
                if entry.get("end") == end_s and entry.get("start"):
                    return f"{taxonomy.name}:{tag} [{entry['start']}..{end_s}] " \
                           f"{entry.get('form', '')} {entry.get('accn', '')}"
        return None

    operating, financing = tagged(taxonomy.interest_operating_tags), \
        tagged(taxonomy.interest_financing_tags)
    if operating and not financing:
        return True, operating
    if financing and not operating:
        return False, financing
    return None


def split_note(figure: "Figure", field: str, splits: list["Split"]) -> str:
    """The sentence a pre-split figure carries on its page reference."""
    if field not in SPLIT_SENSITIVE_FIELDS or not figure.filed:
        return ""
    later = [s for s in splits
             if s.effective > date.fromisoformat(figure.filed)]
    if not later:
        return ""
    which = "; ".join(str(s) for s in later)
    return (f" -- PRE-SPLIT BASIS: {which}. This figure was filed BEFORE "
            f"that and no later filing restates the period, so it is stated "
            f"on the OLD share basis while neighbouring years are on the "
            f"new one. NOT RESCALED HERE.")


#: E23's two shapes per taxonomy, and which tag pair distinguishes them.
CAPEX_PPE_TAG = "PaymentsToAcquirePropertyPlantAndEquipment"
CAPEX_INTANGIBLES_TAG = "PaymentsToAcquireIntangibleAssets"


@dataclass(frozen=True)
class Taxonomy:
    """One reporting vocabulary, and everything the annual path reads by it.

    Bundled rather than passed as five arguments so a third taxonomy is one
    record and not five edits, and so no call site can take the field map of
    one and the year-end tags of another.
    """

    name: str
    fields: tuple[AnnualField, ...]
    #: The tags whose annual-length durations place the fiscal year end.
    year_end_tags: tuple[str, ...]
    lease_parts: tuple[str, ...]
    not_written: tuple[tuple[str, str, str], ...]
    capex_ppe_tag: str
    capex_intangibles_tag: str
    #: The tags that state a share split's conversion ratio. EMPTY for
    #: `ifrs-full`: IFRS has no widely used element for it, so a pre-split
    #: figure in an IFRS file cannot be marked from the tags and the
    #: >= 2x step flag in `manual.section5_gate` is the only guard.
    split_tags: tuple[str, ...] = ()
    #: E34. (tags saying interest paid is in OPERATING, tags saying it is
    #: in FINANCING). Empty means the taxonomy settles it without a tag --
    #: which ASC 230 does, always.
    interest_operating_tags: tuple[str, ...] = ()
    interest_financing_tags: tuple[str, ...] = ()
    #: E34.1: which statement supplies the net a `yes` filer adds back. A
    #: US filer states interest paid and never interest received as cash,
    #: so its net is the income statement's, printed as an accrual proxy.
    interest_source: str = "cash_flow_statement"
    #: E65-E68 (2026-08-29): the elements `apply_debt_rulings` reads beside
    #: the field map. Empty where the taxonomy has no such caption.
    debt_current_subtotal_tag: str = ""        # E66 rule 1: the subtotal
    debt_current_ltd_tag: str = ""             # E66: current maturities
    debt_current_stb_tag: str = ""             # E66: short-term borrowings (a subtotal over paper)
    debt_current_cp_tag: str = ""              # E66: commercial paper
    combined_current_tag: str = ""             # E67: borrowings + finance leases, current
    combined_noncurrent_tag: str = ""          # E67: borrowings + finance leases, non-current
    borrowings_noncurrent_tag: str = ""        # the borrowings-only element E67 defers to
    finance_lease_tags: tuple[str, ...] = ()   # E65: (total, current, non-current)
    aro_part_tags: tuple[str, ...] = ()        # E68: (non-current, current)


US_GAAP_TAXONOMY = Taxonomy(
    name=US_GAAP, fields=ANNUAL_FIELDS,
    year_end_tags=TAGS["revenue"] + TAGS["op_income"],
    lease_parts=LEASE_LIABILITY_PARTS, not_written=NOT_WRITTEN,
    capex_ppe_tag=CAPEX_PPE_TAG,
    capex_intangibles_tag=CAPEX_INTANGIBLES_TAG,
    split_tags=("StockholdersEquityNoteStockSplitConversionRatio1",
                "StockholdersEquityNoteStockSplitConversionRatio"),
    interest_source="income_statement_net",
    debt_current_subtotal_tag="DebtCurrent",
    debt_current_ltd_tag="LongTermDebtCurrent",
    debt_current_stb_tag="ShortTermBorrowings",
    debt_current_cp_tag="CommercialPaper",
    combined_current_tag="LongTermDebtAndCapitalLeaseObligationsCurrent",
    combined_noncurrent_tag="LongTermDebtAndCapitalLeaseObligations",
    borrowings_noncurrent_tag="LongTermDebtNoncurrent",
    finance_lease_tags=("FinanceLeaseLiability", "FinanceLeaseLiabilityCurrent",
                        "FinanceLeaseLiabilityNoncurrent"),
    aro_part_tags=("AssetRetirementObligationsNoncurrent",
                   "AssetRetirementObligationCurrent"))

IFRS_TAXONOMY = Taxonomy(
    name=IFRS_FULL, fields=IFRS_ANNUAL_FIELDS,
    year_end_tags=("Revenue", "ProfitLossFromOperatingActivities"),
    lease_parts=IFRS_LEASE_LIABILITY_PARTS, not_written=IFRS_NOT_WRITTEN,
    capex_ppe_tag=(
        "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"),
    capex_intangibles_tag=(
        "PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities"),
    interest_operating_tags=("InterestPaidClassifiedAsOperatingActivities",),
    interest_financing_tags=("InterestPaidClassifiedAsFinancingActivities",),
    # IFRS 16 has ONE lessee model: `LeaseLiabilities` is every lease and
    # E65 has nothing to add; the current-borrowings alias is already a
    # stated subtotal, so E66 has nothing to add either. E68's parts:
    aro_part_tags=("NoncurrentProvisionsForDecommissioningRestorationAndRehabilitationCosts",
                   "CurrentProvisionsForDecommissioningRestorationAndRehabilitationCosts"))

TAXONOMIES = (US_GAAP_TAXONOMY, IFRS_TAXONOMY)
TAXONOMY_BY_NAME = {t.name: t for t in TAXONOMIES}


def pick_taxonomy(facts: dict) -> Taxonomy:
    """Which vocabulary this filer reports in, from the facts themselves.

    NOT from the form type and not from the ticker suffix: a 20-F filer may
    report under us-gaap, and `facts` says which blocks it actually filled.
    Where both are present the LARGER one wins and the choice is reported.
    """
    blocks = facts.get("facts", {}) or {}
    sizes = [(len(blocks.get(t.name) or {}), t) for t in TAXONOMIES]
    best = max(sizes, key=lambda pair: pair[0])
    if best[0] == 0:
        raise XbrlError(
            f"this filer's facts carry neither `{US_GAAP}` nor `{IFRS_FULL}`; "
            f"the blocks present are {sorted(blocks)}. Section 5 reads one of "
            f"those two vocabularies and nothing is guessed from the others.")
    return best[1]


def reporting_currency(facts: dict, taxonomy: Taxonomy) -> str:
    """The currency the filer reports in, MEASURED from its own facts.

    Not assumed. `manual_yaml` wrote `reporting_currency: USD` as a literal,
    which is right for a us-gaap filer and wrong for every 20-F under IFRS.
    And SAP's facts carry BOTH EUR and USD on most tags -- the USD entries
    are convenience translations from a 2018 20-F -- so "the first money
    unit found" would pick whichever the JSON listed first.

    The census counts FACTS, not tags, and only three-letter currency codes.
    SAP: EUR by a wide margin. NIKE: USD.
    """
    census: dict[str, int] = {}
    for node in (facts.get("facts", {}).get(taxonomy.name) or {}).values():
        for unit, entries in (node.get("units") or {}).items():
            if len(unit) == 3 and unit.isalpha() and unit.isupper():
                census[unit] = census.get(unit, 0) + len(entries)
    if not census:
        raise XbrlError(
            f"no currency unit anywhere in this filer's `{taxonomy.name}` "
            f"facts; nothing can say what its figures are denominated in.")
    return max(census, key=lambda code: (census[code], code))


def resolve_unit(spec: "AnnualField", currency: str) -> str:
    """The sentinel units of a map, named exactly for one filer."""
    if spec.unit == MONEY:
        return currency
    if spec.unit == MONEY_PER_SHARE:
        return f"{currency}/shares"
    return spec.unit


@dataclass
class AnnualYear:
    """One fiscal year, and every mapped field it does or does not supply."""

    fiscal_year: int
    end: date
    figures: dict = field(default_factory=dict)   # field name -> Figure
    missing: list = field(default_factory=list)   # fields no tag supplied
    #: E23: which capex shape this filer tags, in one sentence.
    capex_shape: str = ""
    #: E34: (interest_in_ocf, the page it is read from), or None where the
    #: filer's own facts do not settle it.
    interest: tuple[bool, str] | None = None
    #: E65-E68: one sentence per debt leg, saying what was read, what was
    #: summed, what sits inside what, and what was REFUSED.
    debt_notes: list = field(default_factory=list)
    #: field name -> the sentence naming a UNIT SLIP that REFUSED it. The
    #: filer tagged one element, one period and one unit at two scales a
    #: round power of a thousand apart, and NOTHING HERE CHOOSES BETWEEN
    #: THEM: the figure is DATA MISSING, with both filings named.
    unit_slips: dict = field(default_factory=dict)

    def value(self, name):
        figure = self.figures.get(name)
        return figure.value if figure else None


def _annual_groups(facts: dict, tag: str, unit: str,
                   taxonomy: str = US_GAAP) -> dict:
    """Annual-length duration entries for one tag, grouped by their window."""
    groups: dict[str, list] = {}
    for entry in _entries(facts, tag, unit, taxonomy=taxonomy):
        if not entry.get("start"):
            continue
        start = date.fromisoformat(entry["start"])
        end = date.fromisoformat(entry["end"])
        if ANNUAL_MIN_DAYS <= (end - start).days <= ANNUAL_MAX_DAYS:
            groups.setdefault(entry["end"], []).append(entry)
    return groups


#: HOW FAR A 52/53-WEEK YEAR MAY DRIFT AND STILL BE THE YEAR AS FILED.
#:
#: A 52/53-week filer closes on a WEEKDAY near a fixed month end, so its
#: year end walks a few days each year and crosses the month boundary every
#: few years. Under a bare "same month" rule those years are passed over.
#: REVIEW-4 report B 5.1, RUN and live on the watchlist: LULU's FY2025
#: (2025-02-02) and FY2026 (2026-02-01) are both passed over because the
#: modal month is January, FY2024 (2024-01-28) is chosen instead, and the
#: basis reads **940 days old -> STALE**. `xbrl.py`'s own docstring called
#: this "exactly the case where this rule is wrong" and the test suite
#: pinned only the half where it is right (report C 9.3 #6).
#:
#: Seven days is a week, which is the unit a 52/53-week year moves in.
FISCAL_YEAR_END_TOLERANCE_DAYS = 7


def _month_end(year: int, month: int) -> date:
    """The last day of one month."""
    return (date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1))


def _anchor(end: date, fy_end_month: int) -> tuple[int, int] | None:
    """(anchor year, days from the anchor) for a window ending ``end``.

    The anchor is the END of the filer's fiscal-year-end month, in whichever
    adjacent year is nearest. Returns None beyond the tolerance.
    """
    best: tuple[int, int] | None = None
    for year in (end.year - 1, end.year, end.year + 1):
        anchor = _month_end(year, fy_end_month)
        distance = abs((end - anchor).days)
        if best is None or distance < best[1]:
            best = (year, distance)
    if best is None or best[1] > FISCAL_YEAR_END_TOLERANCE_DAYS:
        return None
    return best


def fiscal_year_ends(facts: dict, fy_end_month: int, *,
                     taxonomy: Taxonomy = US_GAAP_TAXONOMY,
                     currency: str = "USD") -> tuple[list, list]:
    """(the year ends this filer tagged, the annual windows passed over).

    A fiscal year ends AT OR WITHIN A WEEK OF the end of the month the
    filer's year ends in. An annual-length window that closes further away
    than that is a trailing twelve months or a stub, and neither is the year
    as filed. They are RETURNED rather than dropped in silence.

    ONE WINDOW PER ANCHOR. With a tolerance, two windows can sit within a
    week of the same month end -- a TTM stub ending 2025-01-31 beside a
    fiscal year ending 2025-02-02 -- and both would become an `annual:`
    entry keyed on the same year. The one CLOSEST to the anchor wins, a tie
    goes to the later window, and the loser is named in `passed_over`.
    """
    candidates: set[str] = set()
    passed_over: set[str] = set()
    for spec in taxonomy.fields:
        if spec.kind != "duration":
            continue
        for tag in spec.tags:
            for end_s in _annual_groups(facts, tag,
                                        resolve_unit(spec, currency),
                                        taxonomy=taxonomy.name):
                if _anchor(date.fromisoformat(end_s), fy_end_month) is None:
                    passed_over.add(end_s)
                else:
                    candidates.add(end_s)

    by_anchor: dict[int, tuple[int, str]] = {}
    for end_s in candidates:
        anchor_year, distance = _anchor(date.fromisoformat(end_s), fy_end_month)
        held = by_anchor.get(anchor_year)
        if held is None or (distance, end_s) < (held[0], held[1]):
            if held is not None:
                passed_over.add(held[1])
            by_anchor[anchor_year] = (distance, end_s)
        else:
            passed_over.add(end_s)

    ends = {end_s for _distance, end_s in by_anchor.values()}
    return sorted(ends), sorted(passed_over - ends)


def build_annual(facts: dict, *, limit: int = ANNUAL_LIMIT,
                 taxonomy: Taxonomy | None = None,
                 currency: str | None = None) -> tuple[list, list]:
    """(the most recent ``limit`` fiscal years, the windows passed over).

    Oldest first. A year appears when at least one mapped field answers at
    its end; a field no tag supplies is listed in ``missing`` and written
    nowhere. Nothing is carried across from a neighbouring year, and no
    figure is built out of two others.

    ``taxonomy`` and ``currency`` default to what the FACTS say: which
    vocabulary the filer filled, and which currency it states its figures
    in. Both are passable so a caller can pin them in a test.
    """
    from .manual import ZERO_REFUSED

    taxonomy = taxonomy or pick_taxonomy(facts)
    currency = currency or reporting_currency(facts, taxonomy)
    splits = stock_splits(facts, taxonomy)
    fy_end_month = fiscal_year_end_month(facts, taxonomy.name, currency)
    ends, passed_over = fiscal_year_ends(facts, fy_end_month,
                                         taxonomy=taxonomy, currency=currency)

    years: list[AnnualYear] = []
    for end_s in ends[-limit:]:
        end = date.fromisoformat(end_s)
        year = AnnualYear(fiscal_year=end.year, end=end)
        for spec in taxonomy.fields:
            unit = resolve_unit(spec, currency)
            for tag in spec.tags:
                if spec.field in year.figures:
                    break
                if spec.kind == "duration":
                    entries = _annual_groups(
                        facts, tag, unit, taxonomy=taxonomy.name).get(end_s)
                else:
                    entries = [e for e in _entries(facts, tag, unit,
                                                   taxonomy=taxonomy.name)
                               if not e.get("start") and e["end"] == end_s]
                if not entries:
                    continue
                entry, restated = _pick(entries)
                # A UNIT SLIP IS NOT SOMETHING TO CHOOSE BETWEEN. Where the
                # pool holds one element, one period and one unit at two
                # scales a round power of a thousand apart, the filer has
                # stated ONE figure in TWO units and there is nothing here
                # that can tell which is meant. Taking either is a coin
                # toss on a factor of a thousand, so the field is DATA
                # MISSING and both filings are named -- the same answer
                # `ranking` rule 1 gives for two vendor labels a round power
                # apart, and E22's rule that nothing is derived or guessed.
                slip = _slip_in(entries)
                if slip:
                    year.unit_slips[spec.field] = (
                        f"`{taxonomy.name}:{tag}` is tagged at TWO SCALES "
                        f"for this period, a round power of a thousand "
                        f"apart: {slip}. One figure in two units, and "
                        f"nothing here chooses between them -- the field is "
                        f"DATA MISSING until the filer or the owner settles "
                        f"which is meant.")
                    continue
                value = float(entry["val"])
                # E25 refuses a zero on some fields OUTRIGHT -- a count, a
                # non-GAAP memo, a concept the issuer does not present. A
                # tagged zero on one of those would not load, so it is not
                # written and is named instead.
                if value == 0 and spec.field in ZERO_REFUSED:
                    continue
                year.figures[spec.field] = Figure(
                    value=-value if spec.negate else value, tag=tag,
                    start=entry.get("start"), end=entry["end"],
                    accession=entry["accn"], form=entry.get("form", ""),
                    filed=entry.get("filed", ""),
                    restated_from=(-restated if spec.negate and restated is not None
                                   else restated),
                    unit_slip=_is_unit_slip(float(entry["val"]), restated),
                    taxonomy=taxonomy.name,
                    concept_note=CONCEPT_NOTES.get(tag, ""))
        for field_name, figure in year.figures.items():
            note = split_note(figure, field_name, splits)
            if note:
                year.figures[field_name] = replace(figure, split_note=note)
        year.capex_shape = place_capex(year, taxonomy)
        apply_debt_rulings(facts, year, taxonomy, currency)
        year.interest = interest_classification(facts, year, taxonomy, currency)
        # `capex_combined` is "missing" only when NO capex leg resolved: a
        # filer that tags the split pair has no combined line to lack, and
        # which capex shape a filer tags is reported as a sentence anyway.
        capex_seen = any(name in year.figures for name in
                         ("capex_ppe", "capex_intangibles", "capex_combined"))
        year.missing = [s.field for s in taxonomy.fields
                        if s.tags and s.field not in year.figures
                        and not (s.field == "capex_combined" and capex_seen)]
        if year.figures:
            years.append(year)
    return years, passed_over


def place_capex(year: "AnnualYear",
                taxonomy: "Taxonomy | None" = None) -> str:
    """E23, applied to what the filer actually tagged. Nothing is summed.

    E23: "`capex_combined` for the single line an issuer prints; section 5
    reads the split pair when both resolve and the combined line when they
    do not, never a mix."

    THE TAGS SAY WHICH SHAPE IT IS. A filer that tags both
    ``PaymentsToAcquirePropertyPlantAndEquipment`` and
    ``PaymentsToAcquireIntangibleAssets`` is printing the SPLIT, and the two
    go to the split pair. A filer that tags only the first is printing ONE
    CAPEX LINE -- NIKE's cash flow statement has exactly one, "Additions to
    property, plant and equipment" -- and under E23 the one line an issuer
    prints is ``capex_combined``.

    THE CAVEAT, AND IT IS REAL. ``capex_combined``'s own example is
    Betsson's "Investments in intangibles/tangibles", a line that genuinely
    holds both. NIKE's holds property, plant and equipment and nothing
    else, because NIKE states no separate intangible capital spend. **The
    field records the ISSUER'S CAPEX PRESENTATION, not a claim about what
    is inside the line**, and the page reference names the exact tag so a
    reader sees which line it was. Where a filer capitalises software under
    some third element this path does not read, that spend is outside this
    figure -- which is why the tag, not the field name, is the record.

    Left alone: a year that tagged ONLY the intangibles line. That is not
    an issuer's whole capital spending and must not be presented as one, so
    it stays in ``capex_intangibles``, where E23's own rule -- a lone split
    leg is never used -- makes free cash flow DATA MISSING rather than
    understated. Returns one sentence naming which shape was found.
    """
    taxonomy = taxonomy or US_GAAP_TAXONOMY
    ppe_tag = taxonomy.capex_ppe_tag
    intangibles_tag = taxonomy.capex_intangibles_tag
    ppe = year.figures.get("capex_ppe")
    intangibles = year.figures.get("capex_intangibles")
    combined = year.figures.get("capex_combined")
    if ppe is not None and intangibles is not None:
        # NEVER A MIX (E23). An IFRS filer that tagged the split AND the
        # single line is stating two presentations; the split is the finer
        # one and the combined element is dropped rather than added to it.
        note = ""
        if combined is not None:
            del year.figures["capex_combined"]
            note = (f". `{combined.tag}` is tagged as well and is NOT used: "
                    f"E23 reads the split pair or the one line, never a mix")
        return (f"split: `capex_ppe` + `capex_intangibles`, as the filer tags "
                f"them (`{ppe_tag}`, `{intangibles_tag}`){note}")
    if combined is not None and ppe is None and intangibles is None:
        return (f"combined: `capex_combined` holds `{combined.tag}`, the "
                f"issuer's OWN single capital-expenditure element. Neither "
                f"split leg is tagged at this year end, so there is no split "
                f"to read and nothing is added (E23)")
    if ppe is not None:
        if combined is not None:
            del year.figures["capex_combined"]
        year.figures["capex_combined"] = ppe
        del year.figures["capex_ppe"]
        return (f"combined: `capex_combined` holds `{ppe_tag}`, the ONE "
                f"capex line this filer tags. `{intangibles_tag}` is "
                f"not tagged at this year end, so there is no split to read "
                f"and no second line to add (E23)")
    if intangibles is not None:
        return (f"NEITHER: only `{intangibles_tag}` is tagged. An "
                f"intangibles line alone is not an issuer's capital "
                f"spending, so it is NOT moved to `capex_combined` -- it "
                f"stays a lone split leg, which E23 refuses to use, and free "
                f"cash flow is DATA MISSING rather than understated")
    return "NEITHER: no capex line is tagged at this year end"


def _instant_figure(facts: dict, tag: str, unit: str, end_s: str,
                    taxonomy: "Taxonomy") -> "Figure | None":
    """One instant fact at a year end, as a Figure, or None."""
    if not tag:
        return None
    entries = [e for e in _entries(facts, tag, unit, taxonomy=taxonomy.name)
               if not e.get("start") and e["end"] == end_s]
    if not entries:
        return None
    entry, restated = _pick(entries)
    return Figure(value=float(entry["val"]), tag=tag, start=None,
                  end=entry["end"], accession=entry["accn"],
                  form=entry.get("form", ""), filed=entry.get("filed", ""),
                  restated_from=restated,
                  unit_slip=_is_unit_slip(float(entry["val"]), restated),
                  taxonomy=taxonomy.name,
                  concept_note=CONCEPT_NOTES.get(tag, ""))


def _summed(rule: str, parts: list, extra: str = "") -> "Figure":
    """One Figure out of two or more STATED captions (E65/E66/E68).

    The whole provenance -- every component's own page line and amount, and
    the arithmetic -- is the figure's page. Nothing here is a derivation of
    the kind E22 forbids: every operand is a figure the filer tagged.
    """
    total = float(sum(p.value for p in parts))
    first = parts[0]
    text = (f"{rule}: "
            + " + ".join(f"{p.provenance} = {p.value:,.0f}" for p in parts)
            + f" = {total:,.0f}{extra}")
    return Figure(value=total, tag=" + ".join(p.tag for p in parts), start=None,
                  end=first.end, accession=first.accession, form=first.form,
                  filed=first.filed, taxonomy=first.taxonomy, composite=text,
                  components=tuple(parts))


def apply_debt_rulings(facts: dict, year: "AnnualYear", taxonomy: "Taxonomy",
                       currency: str) -> None:
    """FRAMEWORK-EDITS E65, E66, E67 and E68 on one fiscal year, AFTER the
    per-field map has run. Overrides the borrowing and lease legs where a
    ruling says so, adds the asset-retirement leg's two-part shape, and
    writes one sentence per leg to ``year.debt_notes``.

    E66: two stated current-borrowing captions are ADDED; a stated subtotal
    (`DebtCurrent`) wins and the captions beside it are memo; short-term
    borrowings is itself a subtotal over commercial paper.
    E67: a combined borrowings-and-finance-leases caption is read whole
    where no borrowings-only element is tagged, the finance lease inside
    it named (and REFUSED where the filer does not state it). An ex-lease
    current element tagged EQUAL to its inclusive twin was tagged
    inclusive, and is treated the same way.
    E65: `lease_liabilities` = operating total + the finance lease liability
    LESS whatever a borrowing leg already holds (E67) -- never twice, never
    dropped; a residual below zero refuses the field.
    E68: `asset_retirement_obligation` is the stated total, or its two
    stated parts added; a lone part is not the obligation.
    """
    t = taxonomy
    end_s = year.end.isoformat()
    notes = year.debt_notes

    def get(tag):
        return _instant_figure(facts, tag, currency, end_s, t)

    fl_total = get(t.finance_lease_tags[0]) if len(t.finance_lease_tags) > 0 else None
    fl_cur = get(t.finance_lease_tags[1]) if len(t.finance_lease_tags) > 1 else None
    fl_non = get(t.finance_lease_tags[2]) if len(t.finance_lease_tags) > 2 else None
    lease_in_current = 0.0
    lease_in_noncurrent = 0.0

    # --- E66 + E67, the current leg ---------------------------------------
    if t.debt_current_ltd_tag or t.debt_current_subtotal_tag:
        subtotal = get(t.debt_current_subtotal_tag)
        ltd = get(t.debt_current_ltd_tag)
        stb = get(t.debt_current_stb_tag)
        cp = get(t.debt_current_cp_tag)
        comb_cur = get(t.combined_current_tag)
        if subtotal is not None:
            memo = [p for p in (ltd, stb, cp) if p is not None]
            named = ", ".join(f"`{p.tag}` {p.value:,.0f}" for p in memo)
            note = (" -- E66: the taxonomy's SUBTOTAL of current borrowings, "
                    "read whole" + (f"; tagged beside it as memo and never "
                                    f"added: {named}" if memo else ""))
            year.figures["financial_liabilities_current"] = replace(
                subtotal, concept_note=subtotal.concept_note + note)
            notes.append(f"current borrowings: `{subtotal.tag}` "
                         f"{subtotal.value:,.0f}, the stated subtotal (E66)"
                         + (f"; memo inside it: {named}" if memo else ""))
        else:
            parts: list = []
            if ltd is not None:
                first = ltd
                if (comb_cur is not None and fl_cur is not None
                        and comb_cur.value == ltd.value):
                    lease_in_current = fl_cur.value
                    first = replace(ltd, concept_note=ltd.concept_note + (
                        f" -- E67: tagged EQUAL to `{comb_cur.tag}` "
                        f"{comb_cur.value:,.0f}, the inclusive caption, so this "
                        f"ex-lease element was tagged INCLUSIVE of its finance "
                        f"lease: {fl_cur.value:,.0f} of it is `{fl_cur.tag}` and "
                        f"E65 does not add that again"))
                parts.append(first)
            elif comb_cur is not None:
                if fl_cur is not None:
                    lease_in_current = fl_cur.value
                    parts.append(replace(comb_cur, concept_note=comb_cur.concept_note + (
                        f" -- E67: borrowings AND finance leases as one current "
                        f"caption, read whole because the filer tags no "
                        f"borrowings-only current element; {fl_cur.value:,.0f} of "
                        f"it is `{fl_cur.tag}` and E65 does not add that again")))
                elif fl_total is None and fl_non is None:
                    parts.append(replace(comb_cur, concept_note=comb_cur.concept_note + (
                        f" -- E72: borrowings AND finance leases as one current "
                        f"caption, read WHOLE: the filer tags no finance-lease "
                        f"element at all, so the lease inside is stated only in "
                        f"the filing's words, which must be quoted on this figure "
                        f"by hand (E72); E65 adds nothing")))
                else:
                    notes.append(
                        f"current borrowings: `{comb_cur.tag}` {comb_cur.value:,.0f} "
                        f"is tagged and the finance lease inside it is sized "
                        f"elsewhere but NOT stated for this caption "
                        f"(`{t.finance_lease_tags[1]}` untagged while another "
                        f"finance-lease element is) -- E67 REFUSES the caption "
                        f"rather than guess; the leg is DATA MISSING on it")
            short = stb if stb is not None else cp
            if short is not None:
                if stb is not None and cp is not None:
                    short = replace(stb, concept_note=stb.concept_note + (
                        f" -- E66: `{cp.tag}` {cp.value:,.0f} is tagged beside it "
                        f"and is memo: short-term borrowings is by the element's "
                        f"definition a subtotal that includes commercial paper"))
                parts.append(short)
            if len(parts) >= 2:
                year.figures["financial_liabilities_current"] = _summed(
                    "E66 -- two stated current-borrowing captions, added", parts)
                notes.append("current borrowings: "
                             + " + ".join(f"`{p.tag}` {p.value:,.0f}" for p in parts)
                             + f" = {sum(p.value for p in parts):,.0f} (E66: two "
                             f"stated captions, neither a subtotal of the other)")
            elif len(parts) == 1:
                year.figures["financial_liabilities_current"] = parts[0]
                if "financial_liabilities_current" in year.missing:
                    year.missing.remove("financial_liabilities_current")
                notes.append(f"current borrowings: `{parts[0].tag}` "
                             f"{parts[0].value:,.0f}, the one caption tagged"
                             + (f"; {lease_in_current:,.0f} of it is finance lease "
                                f"(E67)" if lease_in_current else "")
                             + (" -- read whole under E72" if "E72" in
                                parts[0].concept_note else ""))
            elif "financial_liabilities_current" not in year.figures:
                notes.append("current borrowings: no current-borrowing element "
                             "tagged at this year end -- DATA MISSING")

    # --- E67, the non-current leg -----------------------------------------
    if t.borrowings_noncurrent_tag:
        ltdn = get(t.borrowings_noncurrent_tag)
        comb = get(t.combined_noncurrent_tag)
        if ltdn is not None:
            notes.append(f"non-current borrowings: `{ltdn.tag}` {ltdn.value:,.0f}, "
                         f"the borrowings-only element; no lease inside it (E14)")
        elif comb is not None:
            if fl_non is not None:
                lease_in_noncurrent = fl_non.value
                year.figures["financial_liabilities_noncurrent"] = replace(
                    comb, concept_note=comb.concept_note + (
                        f" -- E67: borrowings AND finance leases as one non-current "
                        f"caption, read whole because the filer tags no "
                        f"borrowings-only element; {fl_non.value:,.0f} of it is "
                        f"`{fl_non.tag}` and E65 does not add that again"))
                notes.append(f"non-current borrowings: `{comb.tag}` {comb.value:,.0f} "
                             f"read whole (E67), of which {fl_non.value:,.0f} is "
                             f"`{fl_non.tag}`")
            elif fl_total is None and fl_cur is None:
                # E72 (2026-08-30): no finance-lease element of ANY kind is
                # tagged, so the lease inside the caption is stated only in
                # words. The caption is the leg, read whole; the wording is
                # quoted on the figure by hand. E65 adds nothing, so nothing
                # is counted twice.
                year.figures["financial_liabilities_noncurrent"] = replace(
                    comb, concept_note=comb.concept_note + (
                        f" -- E72: borrowings AND finance leases as one "
                        f"non-current caption, read WHOLE: the filer tags no "
                        f"finance-lease element at all, so the lease inside is "
                        f"stated only in the filing's words, which must be "
                        f"quoted on this figure by hand (E72); E65 adds nothing"))
                if "financial_liabilities_noncurrent" in year.missing:
                    year.missing.remove("financial_liabilities_noncurrent")
                notes.append(f"non-current borrowings: `{comb.tag}` {comb.value:,.0f} "
                             f"read whole (E72): no finance-lease element is "
                             f"tagged, so the lease inside it is stated only in "
                             f"words -- quote them on the figure by hand")
            else:
                notes.append(
                    f"non-current borrowings: `{comb.tag}` {comb.value:,.0f} is "
                    f"tagged and the finance lease inside it is sized elsewhere "
                    f"but NOT stated for this caption (`{t.finance_lease_tags[2]}` "
                    f"untagged while another finance-lease element is) -- E67 "
                    f"REFUSES the caption rather than guess, because E65 would "
                    f"add the sized lease again; the leg stays DATA MISSING")
        else:
            notes.append("non-current borrowings: neither the borrowings-only "
                         "element nor a combined caption is tagged -- DATA MISSING")

    # --- E71, the operating total from two stated parts -------------------
    # E71 (2026-08-30): where the filer tags no operating-lease total but
    # BOTH its current and non-current portions, the field is their sum
    # with both named. The issuer's evidence that they are one quantity is
    # its choice of two elements the taxonomy defines as the portions of
    # that one liability -- the same shape E65 and E68 already add for
    # finance leases and asset retirement obligations. One part alone is
    # E26's DATA MISSING, named and never added.
    if year.figures.get("lease_liabilities") is None and len(t.lease_parts) == 2:
        part_cur, part_non = (get(t.lease_parts[0]), get(t.lease_parts[1]))
        if part_cur is not None and part_non is not None:
            year.figures["lease_liabilities"] = _summed(
                "E71 -- the lease liability from two stated parts the filer "
                "never totals, current and non-current portions of one "
                "liability by the taxonomy's own definition", [part_cur, part_non])
            if "lease_liabilities" in year.missing:
                year.missing.remove("lease_liabilities")
            notes.append(f"leases: no stated total; `{part_cur.tag}` "
                         f"{part_cur.value:,.0f} + `{part_non.tag}` "
                         f"{part_non.value:,.0f} = {part_cur.value + part_non.value:,.0f} "
                         f"(E71: two stated parts of one liability, added)")

    # --- E117, the operating part that LEAVES net debt ---------------------
    # Captured HERE, while `lease_liabilities` is still the operating total
    # alone (the stated element, or E71's two parts) and before E65 adds
    # the finance leases to it. It is the same figure under a second name:
    # `lease_liabilities` less this is what stays in net debt (E117).
    if (t.name == US_GAAP and year.figures.get("lease_liabilities") is not None
            and "operating_lease_liabilities" not in year.figures):
        year.figures["operating_lease_liabilities"] = year.figures["lease_liabilities"]
        if "operating_lease_liabilities" in year.missing:
            year.missing.remove("operating_lease_liabilities")

    # --- E65, the lease leg -----------------------------------------------
    if t.finance_lease_tags:
        op = year.figures.get("lease_liabilities")
        finance = None
        if fl_total is not None:
            finance = fl_total
        elif fl_cur is not None and fl_non is not None:
            finance = _summed("E65 -- finance lease liability from two stated "
                              "parts (E66's precedence)", [fl_cur, fl_non])
        elif fl_cur is not None or fl_non is not None:
            lone = fl_cur if fl_cur is not None else fl_non
            year.figures.pop("lease_liabilities", None)
            notes.append(f"leases: only `{lone.tag}` {lone.value:,.0f} of the finance "
                         f"lease liability is tagged -- one part alone is not the "
                         f"liability (E65, E26); `lease_liabilities` is REFUSED "
                         f"rather than understated")
        if finance is not None:
            added = finance.value - lease_in_current - lease_in_noncurrent
            if added < -0.5:
                year.figures.pop("lease_liabilities", None)
                notes.append(f"leases: finance lease liability {finance.value:,.0f} is "
                             f"LESS than the lease the borrowing legs already hold "
                             f"({lease_in_current:,.0f} + {lease_in_noncurrent:,.0f}) "
                             f"-- the filer's captions disagree; `lease_liabilities` "
                             f"is REFUSED rather than clamped (E65)")
            elif op is not None:
                inside = []
                if lease_in_current:
                    inside.append(f"{lease_in_current:,.0f} already inside "
                                  f"`financial_liabilities_current` (E67)")
                if lease_in_noncurrent:
                    inside.append(f"{lease_in_noncurrent:,.0f} already inside "
                                  f"`financial_liabilities_noncurrent` (E67)")
                text = (f"E65 -- operating and finance lease liabilities: "
                        f"{op.provenance} = {op.value:,.0f} + {finance.provenance} "
                        f"= {finance.value:,.0f}"
                        + (f", of which {' and '.join(inside)}, so {added:,.0f} "
                           f"is added" if inside else ", added in full")
                        + f" = {op.value + added:,.0f}")
                year.figures["lease_liabilities"] = Figure(
                    value=op.value + added, tag=f"{op.tag} + {finance.tag}",
                    start=None, end=op.end, accession=op.accession, form=op.form,
                    filed=op.filed, taxonomy=op.taxonomy, composite=text,
                    components=(op, finance))
                notes.append(f"leases: `{op.tag}` {op.value:,.0f} + finance lease "
                             f"{finance.value:,.0f} (`{finance.tag}`)"
                             + (f", of which {' and '.join(inside)}" if inside else "")
                             + f" -> {added:,.0f} added; `lease_liabilities` = "
                             f"{op.value + added:,.0f} (E65)")
            else:
                notes.append(f"leases: finance lease liability {finance.value:,.0f} "
                             f"(`{finance.tag}`) is tagged but the operating total "
                             f"is not (E26) -- `lease_liabilities` stays DATA "
                             f"MISSING; E65 sums where BOTH are stated")
        elif fl_cur is None and fl_non is None:
            notes.append("leases: no finance-lease element is tagged at this year "
                         "end; `lease_liabilities` is the operating total alone. "
                         "A finance lease the filing DISCLOSES but never sizes is "
                         "a NAMED ZERO for the component, entered by hand with "
                         "the sentence quoted (E73)"
                         if op is not None else
                         "leases: neither an operating total nor a finance-lease "
                         "element is tagged at this year end -- DATA MISSING")
    else:
        notes.append("leases: one lessee model in this taxonomy (IFRS 16) -- "
                     "`lease_liabilities` is every lease and E65 adds nothing")

    # --- E68, the asset-retirement leg ------------------------------------
    aro = year.figures.get("asset_retirement_obligation")
    non = get(t.aro_part_tags[0]) if len(t.aro_part_tags) > 0 else None
    cur = get(t.aro_part_tags[1]) if len(t.aro_part_tags) > 1 else None
    if aro is not None:
        memo = [p for p in (non, cur) if p is not None]
        named = ", ".join(f"`{p.tag}` {p.value:,.0f}" for p in memo)
        if memo:
            year.figures["asset_retirement_obligation"] = replace(
                aro, concept_note=aro.concept_note + (
                    f" -- E68: the stated TOTAL; tagged beside it as memo and "
                    f"never added: {named}"))
        notes.append(f"asset retirement obligations: `{aro.tag}` {aro.value:,.0f}, "
                     f"the stated total (E68)" + (f"; memo: {named}" if memo else ""))
    elif non is not None and cur is not None:
        year.figures["asset_retirement_obligation"] = _summed(
            "E68 -- asset retirement obligation from two stated parts (E66's "
            "precedence)", [non, cur])
        notes.append(f"asset retirement obligations: `{non.tag}` {non.value:,.0f} + "
                     f"`{cur.tag}` {cur.value:,.0f} = {non.value + cur.value:,.0f} "
                     f"(E68, two stated parts)")
    elif non is not None or cur is not None:
        lone = non if non is not None else cur
        notes.append(f"asset retirement obligations: only `{lone.tag}` "
                     f"{lone.value:,.0f} is tagged -- a lone part is not the "
                     f"obligation (E68); the leg is DATA MISSING with the part named")
    else:
        notes.append("asset retirement obligations: no element tagged at this year "
                     "end -- DATA MISSING, never zero (E68). A caption-based zero "
                     "may be ENTERED BY HAND where the balance sheet presents no "
                     "such provision and the business owns nothing requiring "
                     "decommissioning (E68.1); extractive, utility, mining, "
                     "shipping, chemical and heavy-industrial filers stay DATA "
                     "MISSING until read from the filing (E69)")


def lease_parts(facts: dict, year: "AnnualYear",
                taxonomy: "Taxonomy | None" = None,
                currency: str | None = None) -> dict:
    """E26's two captions at a year end, for the report. NEVER added."""
    taxonomy = taxonomy or US_GAAP_TAXONOMY
    currency = currency or "USD"
    out: dict[str, float] = {}
    for tag in taxonomy.lease_parts:
        entries = _instant_groups(facts, tag, currency,
                                  taxonomy=taxonomy.name).get(
                                      year.end.isoformat())
        if entries:
            out[tag] = float(_pick(entries)[0]["val"])
    return out


def tag_coverage(facts: dict, years: list,
                 taxonomy: "Taxonomy | None" = None,
                 currency: str | None = None) -> list:
    """Per TAG, in how many of the chosen years it supplied the figure.

    Per tag and not per field, because "the field is filled" hides which of
    two spellings filled it, and a tag that is dead for the newest year and
    alive for the oldest is exactly what a reader needs to see.
    """
    taxonomy = taxonomy or US_GAAP_TAXONOMY
    currency = currency or "USD"
    rows = []
    for spec in taxonomy.fields:
        unit = resolve_unit(spec, currency)
        for tag in spec.tags:
            used = [y.fiscal_year for y in years
                    if y.figures.get(spec.field)
                    and tag in y.figures[spec.field].tag.split(" + ")]
            present = bool(_entries(facts, tag, unit, taxonomy=taxonomy.name))
            rows.append({"field": spec.field, "tag": tag, "unit": unit,
                         "present": present, "years": used})
    return rows


# --- writing config/manual/<TICKER>.yaml ----------------------------------


def _yaml_scalar(text: str) -> str:
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _number(value: float) -> str:
    """As filed. Never rounded, never rescaled, and never 1.0 for 1."""
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return repr(value)


def manual_yaml(*, ticker: str, name: str, cik: int, quote_currency: str | None,
                years: list, run_ts, facts: dict | None = None,
                taxonomy: "Taxonomy | None" = None,
                currency: str | None = None) -> str:
    """The filled `config/manual/<TICKER>.yaml`, deterministic byte for byte.

    Stable field order (the schema's own, through ANNUAL_FIELDS) and stable
    year order (oldest first), so re-running against a later 10-K produces a
    diff a person can read rather than a reshuffle.
    """
    from .manual import (KIND_TAGGED, ORIGIN_XBRL, STATUS_VERIFIED,
                         ZERO_CAPTION, ZERO_NEEDS_BASIS)

    taxonomy = taxonomy or US_GAAP_TAXONOMY
    currency = currency or "USD"
    url = API_URL.format(cik=int(cik))
    document = (f"SEC XBRL companyfacts for CIK {int(cik):010d} ({name}) -- "
                f"{url}. The filing each figure came out of is named on the "
                f"figure itself, with its tag and context period.")

    out = [
        f"# {ticker} -- fundamentals from the filer's own tagged facts.",
        "#",
        f"# GENERATED by `vss xbrl --annual --write` on "
        f"{run_ts.isoformat(timespec='seconds')} from",
        f"#     {url}",
        f"# through the `{taxonomy.name}` tag map in `vss/xbrl.py`. No model read",
        "# this. Nothing was quoted, summarised, inferred, summed, netted or",
        "# rescaled. A tag the filer does not use is DATA MISSING and is named",
        "# in the run's report, never filled from a near neighbour.",
        "#",
        "# ANNUAL, NOT QUARTERLY, and that is the point of this file. Filers",
        "# stopped tagging discrete fourth quarters when the SEC dropped the",
        "# Selected Quarterly Financial Data requirement in 2021, so the newest",
        "# COMPLETE tagged quarter can lag the newest filing by months. These",
        "# are `annual:` entries (E15), keyed on the fiscal year, and E19's",
        "# `as filed` branch is what puts section 5 on the newest of them.",
        "#",
        f"# CURRENCY: {currency}, MEASURED from the filer's own facts rather",
        f"# than assumed -- the census counts every tagged fact carrying a",
        f"# three-letter currency code and takes the commonest. It is not the",
        f"# only one present for every filer: SAP's facts carry USD",
        f"# convenience translations from a 2018 20-F beside its EUR.",
        "#",
        "# UNITS: WHOLE UNITS, as XBRL states them -- 46,309,000,000 where a",
        "# press release for the same year says 46,309 million. Both are the",
        "# figure the source states and neither is rescaled here. DO NOT ADD A",
        "# PERIOD FROM A RELEASE TO THIS FILE: a history holding both units is",
        "# a history in which no comparison means anything, and the writer",
        "# refuses to overwrite a file of any other origin for that reason.",
        "#",
        "# SIGN: the `Payments...` elements state an OUTFLOW AS A POSITIVE",
        "# NUMBER and this schema states an outflow as a negative one, because",
        "# section 5 SUMS the capex legs into operating cash flow. The sign is",
        "# flipped on those fields and nothing else is done to the magnitude.",
        "#",
        f"# EVERY FIGURE IS {STATUS_VERIFIED} / {KIND_TAGGED} (E40): a tagged fact is",
        "# verified BY PROVENANCE -- tag + accession + filing date, on every",
        "# figure's own page line. There is no transcription to have got",
        "# wrong; WHICH TAG answers which field is the committed map in",
        "# `vss/xbrl.py`, diffable and argued with there. The gate accepts",
        "# the kind (E21 as narrowed by E40) and prints it beside the figure.",
        "",
        f"ticker: {ticker}",
        f"name: {_yaml_scalar(name)}",
        f"reporting_currency: {currency}",
        # THE DECLARATIONS THE RUN RECORD DIVIDES ON. XBRL states whole
        # units (see UNITS above) and tags a count as whole shares.
        f"money_unit: whole     # as XBRL states them; the run record "
        f"normalises on this declaration",
        f"share_unit: whole     # counts are tagged as whole shares",
    ]
    if quote_currency:
        out.append(f"quote_currency: {quote_currency}   # from the watchlist "
                   f"entry, not from the facts: a listing currency is not a "
                   f"tagged fact")
    # E34, FOR THE BASIS YEAR. The attribute describes the newest year --
    # section 5 reads that one and nothing else -- and where an older year
    # in the same file is on the other side, the note says so.
    newest = years[-1] if years else None
    if newest is not None and newest.interest is not None:
        value, page = newest.interest
        others = sorted({y.interest[0] for y in years
                         if y.interest is not None} - {value})
        out += [
            "",
            f"# E34: where this filer books its interest, for the BASIS YEAR",
            f"# (FY{newest.fiscal_year}). Section 5 reads that year and no",
            f"# other; a five-year per-share proxy reading this file is not",
            f"# covered by one attribute.",
        ]
        if others:
            out.append("# THIS FILER IS ON BOTH SIDES INSIDE THIS FILE -- at "
                       "least one older")
            out.append("# year is classified the other way. A reclassification, "
                       "not an error.")
        out += [
            "interest_in_ocf:",
            f"  value: {'yes' if value else 'no'}",
            f"  source: {_yaml_scalar(document)}",
            f"  page: {_yaml_scalar(page)}",
        ]
        # E34.1 / E61: `taxonomy.interest_source` names the SHAPE a filer in
        # this taxonomy is left with when it books interest inside operating
        # cash flow at all -- but WHICH figure that shape actually reads
        # depends on what THIS YEAR's facts tagged, not on the taxonomy
        # alone. A filer can tag the net (E34.1) some years and neither the
        # net nor the gross other years; only the BASIS year's own tags
        # decide what this file writes.
        if value and taxonomy.interest_source != "cash_flow_statement":
            if "net_finance_costs" in newest.figures:
                out += [
                    "  # E34.1: this filer states interest PAID as a cash figure and",
                    "  # never interest RECEIVED, so E18's cash pair cannot form. The",
                    "  # add-back is the INCOME STATEMENT'S net (`net_finance_costs`),",
                    "  # an ACCRUAL PROXY, and FCF0 prints it as one. Interest paid",
                    "  # alone is never the net.",
                    f"  interest_source: {taxonomy.interest_source}",
                ]
            elif ("finance_costs_period" in newest.figures
                  and "finance_income_period" in newest.figures):
                costs = newest.figures["finance_costs_period"]
                income = newest.figures["finance_income_period"]
                out += [
                    "  # E34.1 via E18: this filer tags the income statement's PAIR",
                    f"  # -- `finance_costs_period` (`{costs.tag}`) and",
                    f"  # `finance_income_period` (`{income.tag}`) -- and not the net",
                    "  # element. THE STORE SUBTRACTS the two stated figures on the",
                    "  # basis (E18, the same permission E16 gives the share count);",
                    "  # nothing here nets them and no net is written. The add-back",
                    "  # is that net, an ACCRUAL PROXY, and FCF0 prints it as one.",
                    f"  interest_source: {taxonomy.interest_source}",
                ]
            elif ("finance_costs_period" in newest.figures
                  and newest.figures["finance_costs_period"].tag
                  == E61_GROSS_INTEREST_TAG):
                out += [
                    "  # E61: this filer tags GROSS interest expense",
                    "  # (`finance_costs_period`) but never the net and never an",
                    "  # interest-received figure, so neither E34's cash pair nor",
                    "  # E34.1's accrual net can form. The add-back is the gross",
                    "  # expense alone -- a BOUNDED, ONE-SIDED PROXY: interest income",
                    "  # is never negative, so this can only OVERSTATE FCF0, never",
                    "  # understate it, and FCF0 prints the bound as a percentage.",
                    "  interest_source: interest_expense_only",
                ]
            elif "finance_costs_period" in newest.figures:
                out += [
                    "  # NO PROXY: `finance_costs_period` here is",
                    f"  # `{newest.figures['finance_costs_period'].tag}`, which E61 does",
                    "  # not name, and no interest-income element is tagged to pair it",
                    "  # with (E18). FCF0 is DATA MISSING rather than a gross add-back",
                    "  # on an element no ruling covers.",
                ]
            # Neither tag resolved this year: no interest_source override is
            # written. The loader's own default (`cash_flow_statement`) then
            # asks for `net_interest_paid`, which is also untagged for a US
            # filer in this shape -- FCF0 is correctly DATA MISSING rather
            # than silently taking a shape no tag supports.
    # E70: what the operating cash flow bears of the LEASE, by the standard
    # the filer reports under -- a fact the taxonomy settles, as ASC 230
    # settles E34 for a US filer.
    if taxonomy.name == US_GAAP:
        out += [
            "",
            "# E70: whether this filer's operating cash flow bears its operating",
            "# lease payments. Under ASC 842 it does, so FCF0 ADDS the stated cash",
            "# paid (`operating_lease_payments`) back: the lease liability in net",
            "# debt already charges the obligation, and the lease is counted once.",
            "operating_leases_in_ocf:",
            "  value: yes",
            f"  source: {_yaml_scalar(document)}",
            "  page: \"ASC 842-20-45-5(a): a lessee classifies payments for operating "
            "leases within OPERATING activities, so this filer's "
            "`operating_cash_flow` already bears them; the stated cash paid is "
            "`us-gaap:OperatingLeasePayments`, written as "
            "`operating_lease_payments` where tagged. No filer-specific tag "
            "states the classification because the standard leaves no choice\"",
        ]
    else:
        out += [
            "",
            "# E70: whether this filer's operating cash flow bears its lease",
            "# principal. Under IFRS 16 it does not, so nothing is added back: the",
            "# lease is counted once, in net debt (E35, E65).",
            "operating_leases_in_ocf:",
            "  value: no",
            f"  source: {_yaml_scalar(document)}",
            "  page: \"IFRS 16.50(b): a lessee classifies cash payments for the "
            "principal portion of the lease liability within FINANCING "
            "activities, so this filer's `operating_cash_flow` never bore the "
            "principal; the interest portion follows the filer's IAS 7 policy, "
            "which `interest_in_ocf` records. The standard leaves no choice on "
            "the principal\"",
        ]
    out += [
        f"origin: {ORIGIN_XBRL}",
        "",
        "annual:",
    ]

    for year in years:
        out.append(f"  - fiscal_year: {year.fiscal_year}")
        out.append(f"    period_end: {year.end.isoformat()}")
        out.append(f"    document: {_yaml_scalar(document)}")
        out.append(f"    url: {_yaml_scalar(url)}")
        out.append("    figures:")
        wrote = False
        for spec in taxonomy.fields:
            figure = year.figures.get(spec.field)
            if figure is None:
                continue
            wrote = True
            out.append(f"      {spec.field}:")
            out.append(f"        value: {_number(figure.value)}")
            out.append(f"        page: {_yaml_scalar(figure.provenance)}")
            out.append(f"        status: {STATUS_VERIFIED}")
            out.append(f"        verified_kind: {KIND_TAGGED}")
            # E25: a zero is a claim about the company. A TAGGED zero is the
            # filer listing the line and stating nil, which is exactly the
            # `caption` form -- and it is evidence the filer supplied, not a
            # reader's failure to find the line.
            if figure.value == 0 and spec.field in ZERO_NEEDS_BASIS:
                out.append(f"        zero_basis: {ZERO_CAPTION}")
        if not wrote:
            out.append("      {}")
    out.append("")
    return "\n".join(out)


#: Rule 5. A date-only backup loses the earlier of two runs made on one day,
#: which is a known defect on three writers in this project. The purpose
#: suffix says what the run was about, so a directory of them reads.
BACKUP_SUFFIX = "pre-xbrl"


def backup_name(target, run_ts) -> "Path":
    from pathlib import Path

    target = Path(target)
    stamp = run_ts.strftime("%Y-%m-%d-%H%M%S")
    return target.with_suffix(f"{target.suffix}.bak-{stamp}-{BACKUP_SUFFIX}")


def write_manual_file(text: str, target, *, run_ts, force: bool = False):
    """Write the filled file, and REFUSE on the two things it cannot undo.

    ONE: A MIXED HISTORY (rule 3). XBRL states whole units and a press
    release states millions. A file holding both would pass every check in
    the loader -- each period is internally consistent -- and every
    comparison across them would be meaningless. So an existing file whose
    origin is not `sec-xbrl` STOPS THE RUN. It is not overwritten either:
    replacing a hand-read history with a fetched one is not this command's
    decision to make.

    TWO: A VERIFIED READING. The status flag records work only a person can
    do, and a writer that replaces a file in which figures have been checked
    throws that reading away.
    """
    import shutil
    from pathlib import Path

    import yaml

    from .config import ConfigError
    from .manual import KIND_TAGGED, ORIGIN_XBRL, STATUS_VERIFIED, parse_manual

    target = Path(target)
    if target.exists():
        try:
            existing = parse_manual(
                yaml.safe_load(target.read_text(encoding="utf-8")), path=target)
        except ConfigError as exc:
            raise XbrlError(
                f"{target} already exists and does not load, so nothing can "
                f"say what it holds or where it came from. It is NOT "
                f"overwritten. Fix or move it by hand first.\n  ({exc})")
        if existing.origin != ORIGIN_XBRL:
            raise XbrlError(
                f"{target} already exists with origin `{existing.origin}` and "
                f"this path writes `{ORIGIN_XBRL}`. IT IS NOT OVERWRITTEN AND "
                f"NOTHING IS WRITTEN BESIDE IT.\n"
                f"  XBRL states WHOLE UNITS -- 46,309,000,000 -- where a press "
                f"release or a hand-read report states MILLIONS. A history "
                f"holding both passes every check in the loader, because each "
                f"period is internally consistent, and every comparison across "
                f"them is meaningless.\n"
                f"  `--force` does NOT open this: replacing a hand-read "
                f"history with a fetched one is a decision about which source "
                f"a name is kept on, and it is the owner's, not a writer's. "
                f"Move the existing file aside by hand if that is the "
                f"decision.")
        # E40: a `tagged` flag is provenance this same path writes again;
        # only a cross_document, same_page or (E78) caption_statement flag
        # records a reading a person did, and only those stop the write.
        checked = sum(1 for f in existing.all_figures()
                      if f.present and f.verified
                      and f.verified_kind != KIND_TAGGED)
        if checked and not force:
            raise XbrlError(
                f"{target} already exists and holds {checked} figure(s) marked "
                f"{STATUS_VERIFIED} by a READING (cross_document, same_page "
                f"or caption_statement -- E40, E78). It is NOT overwritten: the status flag "
                f"records a reading a person did, and nothing here can redo "
                f"it.\n"
                f"  * To see what would be written, run without --write.\n"
                f"  * To replace it anyway, pass --force. The file is backed "
                f"up first, and those {checked} figure(s) are what you are "
                f"discarding.\n"
                f"  * Whether a re-run should MERGE -- keep a VERIFIED figure "
                f"whose value has not changed and refresh the rest -- is a "
                f"rule question and the owner's; it is not decided here.")

    backup = None
    if target.exists():
        backup = backup_name(target, run_ts)
        shutil.copy2(target, backup)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    log.info("wrote %s%s", target, f" (backup {backup})" if backup else "")
    return target, backup


# --- the report -----------------------------------------------------------


def render_annual_report(*, ticker: str, name: str, cik: int, years: list,
                         facts: dict, passed_over: list, as_of: date,
                         target, written=None, backup=None,
                         validated: str | None = None, gate=None,
                         text: str | None = None,
                         taxonomy: "Taxonomy | None" = None,
                         currency: str | None = None) -> str:
    taxonomy = taxonomy or US_GAAP_TAXONOMY
    currency = currency or "USD"
    from .manual import ORIGIN_XBRL, STATUS_UNVERIFIED

    url = API_URL.format(cik=int(cik))
    out = [f"# vss xbrl --annual -- {ticker} ({name}) -- {as_of.isoformat()}", ""]
    out.append(f"**PRIMARY SOURCE:** {url}")
    out.append("")
    out.append(f"**ORIGIN `{ORIGIN_XBRL}`.** Every figure below carries the "
               f"us-gaap tag it was filed under, the context period it covers "
               f"and the accession number of the filing that reported it. "
               f"**That is its page reference.** No model read this; nothing "
               f"was quoted, summarised or inferred, and **nothing was "
               f"derived** -- a tag the filer does not use is DATA MISSING and "
               f"is named below.")
    out.append("")
    out.append(f"**UNITS:** {UNITS_WARNING}")
    out.append("")

    # --- rule 4: which years came back, and where each ends ---------------
    out.append("## FISCAL YEARS RETURNED")
    out.append("")
    if not years:
        out.append("**None.** The filer tagged no annual-length period ending "
                   "in its own fiscal year-end month.")
        out.append("")
    else:
        out.append("Section 5 stands on ONE twelve-month basis (E19) and will "
                   "take the NEWEST of these. The rest are history: they cost "
                   "nothing, because the basis never reads them.")
        out.append("")
        out.append("| Fiscal year | Ends | Fields filled | DATA MISSING |")
        out.append("|---|---|---:|---:|")
        for year in years:
            out.append(f"| **FY{year.fiscal_year}** | "
                       f"**{year.end.isoformat()}** | {len(year.figures)} | "
                       f"{len(year.missing)} |")
        out.append("")
        newest = years[-1]
        out.append(f"**The basis will be `annual FY{newest.fiscal_year}`, "
                   f"ending {newest.end.isoformat()}** -- "
                   f"{(as_of - newest.end).days} days before "
                   f"{as_of.isoformat()}.")
        out.append("")

    if passed_over:
        out.append("### Annual-length windows PASSED OVER")
        out.append("")
        out.append("Twelve-month windows the filer tagged that do NOT close in "
                   "its fiscal year-end month. A trailing twelve months, a "
                   "stub, or a 52/53-week year drifted across a month "
                   "boundary -- and none of the three is the year as filed. "
                   "**Named rather than dropped in silence:** the drifting "
                   "52/53-week case is exactly where this rule is wrong.")
        out.append("")
        for end_s in passed_over:
            out.append(f"- `{end_s}`")
        out.append("")

    # --- a UNIT SLIP, refused and named -----------------------------------
    slipped = [(y, f, why) for y in years for f, why in y.unit_slips.items()]
    if slipped:
        out.append("## REFUSED -- ONE FIGURE IN TWO UNITS")
        out.append("")
        out.append("The filer tagged the same element, for the same period, "
                   "in the same unit, at **two scales a round power of a "
                   "thousand apart**. **Nothing here chooses between them:** "
                   "taking either would be a coin toss on a factor of a "
                   "thousand, and a wrong one is invisible downstream. The "
                   "field is DATA MISSING and both filings are named.")
        out.append("")
        for y, name_, why in slipped:
            out.append(f"- **FY{y.fiscal_year}** `{name_}` -- {why}")
        out.append("")

    # --- rule 2: what is missing, per field and per tag -------------------
    missing = sorted({f for y in years for f in y.missing})
    if missing:
        out.append("## DATA MISSING")
        out.append("")
        out.append("No tag in the filer's own facts supplies these at these "
                   "year ends. They are written nowhere -- **a near neighbour "
                   "is a different quantity, and substituting one is how a "
                   "wrong figure enters a record:**")
        out.append("")
        out.append("| Field | Tags tried | Absent in |")
        out.append("|---|---|---|")
        by_field = {s.field: s for s in taxonomy.fields}
        for name_ in missing:
            tags = ", ".join(f"`{t}`" for t in by_field[name_].tags)
            where = ", ".join(f"FY{y.fiscal_year}" for y in years
                              if name_ in y.missing)
            out.append(f"| `{name_}` | {tags} | {where} |")
        out.append("")

    if years:
        out.append("## CAPEX ON THE BASIS (E23)")
        out.append("")
        out.append("E23: *the split pair when both resolve and the combined "
                   "line when they do not, never a mix.* **The tags say which "
                   "shape the filer prints**, and the field records the "
                   "issuer's capex PRESENTATION rather than a claim about "
                   "what is inside the line — which is why the page reference "
                   "names the exact tag.")
        out.append("")
        for year in years:
            out.append(f"- **FY{year.fiscal_year}** — {year.capex_shape}")
        out.append("")

    out.append("## DEBT LEGS ON THE BASIS (E65-E68)")
    out.append("")
    out.append("E65: finance leases in `lease_liabilities` beside operating leases, "
               "only the part no borrowing leg already holds. E66: two stated "
               "current-borrowing captions are ADDED; a stated subtotal wins and "
               "the captions beside it are memo. E67: a combined "
               "borrowings-and-finance-leases caption is read whole where no "
               "borrowings-only element is tagged, the lease inside it named and "
               "not added again -- REFUSED where the filer does not state it. "
               "E68: asset retirement obligations are a leg, DATA MISSING where "
               "untagged. **Every summed figure names each component on its own "
               "page line.**")
    out.append("")
    for year in years:
        out.append(f"- **FY{year.fiscal_year}** ({year.end.isoformat()})")
        for sentence in year.debt_notes:
            out.append(f"  - {sentence}")
    out.append("")
    out.append("## TAG COVERAGE")
    out.append("")
    out.append("**Per TAG, not per field.** No tag is assumed universal: "
               "`OperatingIncomeLoss` is absent for NIKE and present for "
               "DECKERS, and a tag that is dead for the newest year may still "
               "be the right one for an older one.")
    out.append("")
    out.append(f"| Field | {taxonomy.name} tag | Unit | In the facts "
               f"| Supplied |")
    out.append("|---|---|---|---|---|")
    for row in tag_coverage(facts, years, taxonomy, currency):
        supplied = (", ".join(f"FY{y}" for y in row["years"])
                    if row["years"] else "—")
        out.append(f"| `{row['field']}` | `{row['tag']}` | {row['unit']} | "
                   f"{'yes' if row['present'] else '**ABSENT**'} | {supplied} |")
    out.append("")

    # --- E71 / E26: the lease pair, where the stated total is absent ------
    added = [y for y in years
             if (f := y.figures.get("lease_liabilities")) is not None
             and f.composite and "E71" in f.composite]
    if added:
        out.append("## E71 -- TWO STATED PARTS THE FILER NEVER TOTALS, ADDED")
        out.append("")
        out.append("`OperatingLeaseLiability` is untagged at these year ends "
                   "and BOTH its portions are tagged: the field is their sum, "
                   "both named (E71, 2026-08-30) -- the filer chose two "
                   "elements the taxonomy defines as the current and "
                   "non-current portions of one liability, which is its own "
                   "statement that they are one quantity.")
        out.append("")
        for year in added:
            out.append(f"- **FY{year.fiscal_year}** ({year.end.isoformat()}): "
                       f"{year.figures['lease_liabilities'].composite}")
        out.append("")
    pairs = [(y, lease_parts(facts, y, taxonomy, currency)) for y in years
             if "lease_liabilities" in y.missing]
    pairs = [(y, p) for y, p in pairs if p]
    if pairs:
        out.append("## E26 -- ONE PART ALONE IS NOT THE TOTAL")
        out.append("")
        out.append("`lease_liabilities` is DATA MISSING above, and the one "
                   "caption the filer DOES state is named here. **It is not "
                   "the total:** E71 adds two stated parts of one quantity; a "
                   "lone part is E26's DATA MISSING, named and never added.")
        out.append("")
        for year, parts in pairs:
            legs = "; ".join(f"`{t}` {v:,.0f}" for t, v in sorted(parts.items()))
            out.append(f"- **FY{year.fiscal_year}** ({year.end.isoformat()}): "
                       f"{legs}")
        out.append("")

    out.append("## TAGS READ AND DELIBERATELY NOT WRITTEN")
    out.append("")
    out.append("Each one looks like it answers a field and answers a different "
               "question. **Listed so a reader can see what was passed over "
               "and why**, rather than discovering later that a near neighbour "
               "had been quietly accepted.")
    out.append("")
    out.append("| Tag | Looks like | Why not |")
    out.append("|---|---|---|")
    for tag, looks_like, why in taxonomy.not_written:
        out.append(f"| `{tag}` | `{looks_like}` | {why} |")
    out.append("")

    out.append("## SCHEMA FIELDS THIS PATH DOES NOT WRITE")
    out.append("")
    out.append("| Field | Why |")
    out.append("|---|---|")
    for field_name, why in OMITTED_FIELDS:
        out.append(f"| `{field_name}` | {why} |")
    out.append("")

    splits = stock_splits(facts, taxonomy)
    if splits:
        out.append("## SHARE SPLITS THE FILER TAGGED")
        out.append("")
        out.append("A split changes every count and every per-share figure at "
                   "once and changes NOTHING about the company. `_pick` takes "
                   "the newest filing, so where a later filing restates the "
                   "year the change shows up below as a RESTATEMENT — and "
                   "where no later filing carries the year at all, it does "
                   "not show up as anything: the old basis simply stays in "
                   "the file beside the new one. **Nothing here is "
                   "rescaled**; the page reference of an affected figure says "
                   "which basis it is on.")
        out.append("")
        for split in splits:
            out.append(f"- {split}")
        marked = [(y, name) for y in years for name, f in y.figures.items()
                  if f.split_note]
        if marked:
            out.append("")
            out.append("On the PRE-SPLIT basis, and marked on the page "
                       "reference:")
            out.append("")
            for year, name in marked:
                out.append(f"- `FY{year.fiscal_year}` `{name}` = "
                           f"{year.figures[name].value:,.6g}")
        out.append("")

    restated = [(y, f) for y in years for f in y.figures.values()
                if f.restated_from is not None]
    if restated:
        out.append("## RESTATED SINCE FIRST FILED")
        out.append("")
        out.append("A later filing reported a different value for a year an "
                   "earlier one had already reported. The later filing is "
                   "used; the earlier value is named so the change is visible:")
        out.append("")
        for year, f in restated:
            out.append(f"- `FY{year.fiscal_year}` `{f.tag}`: "
                       f"{f.restated_from:,.2f} -> {f.value:,.2f} "
                       f"({f.form} {f.accession})")
        out.append("")

    out.append("## VALIDATION")
    out.append("")
    if validated is None:
        out.append("The emitted file was parsed back through the **manual "
                   "loader** before anything was written, and **passed**: the "
                   "unit contract, the one-scale-per-file check, the annual "
                   "block's own rules and E25's zero rules all hold. Those "
                   "checks are imported from `vss/manual.py`, not repeated "
                   "here, so this path cannot emit something `vss manual` "
                   "would reject.")
    else:
        out.append("**The emitted file DOES NOT LOAD. Nothing was written.**")
        out.append("")
        out.append(f"```\n{validated}\n```")
    out.append("")

    if gate is not None:
        out.append("## WHAT `vss manual` WILL SAY")
        out.append("")
        out.append(f"- basis: **{gate.period or 'none'}**")
        out.append(f"- refusals: **{len(gate.refusals)}**")
        for refusal in gate.refusals[:6]:
            out.append(f"  - `{refusal.kind}` — {refusal.subject}")
        if len(gate.refusals) > 6:
            out.append(f"  - … and {len(gate.refusals) - 6} more")
        for ratio in gate.ratios:
            out.append(f"- {ratio.name}: **{ratio.state}** — {ratio.detail}")
        out.append("")
        out.append("**Every figure lands VERIFIED / tagged (E40): a tagged "
                   "fact is verified by its provenance** -- tag, accession "
                   "and filing date, on the figure's own page line. E21's "
                   "gate accepts the kind; what it still refuses on is named "
                   "above, if anything is.")
        out.append("")

    out.append("## OUTPUT")
    out.append("")
    if written:
        out.append(f"Written to `{written}`.")
        if backup:
            out.append("")
            out.append(f"Previous file backed up to `{backup}` — **the stamp "
                       f"carries the TIME, not only the date**, so two runs on "
                       f"one day do not overwrite each other's backup.")
    else:
        out.append(f"**NOT WRITTEN.** Re-run with `--write` to put this in "
                   f"`{target}`.")
    out.append("")
    if text is not None:
        out.append("```yaml")
        out.append(text)
        out.append("```")
        out.append("")
    return "\n".join(out)


@dataclass(frozen=True)
class _IntakeEntry:
    """What `run_xbrl_annual` needed a watchlist entry FOR, and no more.

    A stand-in built for a name being INTAKEN -- looked at before anyone
    has decided to watch it. It carries no status, no drawdown, no peak
    date and no fair value, because an intake makes none of those claims.
    """

    ticker: str
    name: str
    currency: str
    cik: int


def run_xbrl_annual(*, ticker: str, cik: int | None = None,
                    limit: int = ANNUAL_LIMIT, watchlist_path, db_path,
                    manual_dir=None, write: bool = False, force: bool = False,
                    name: str | None = None,
                    quote_currency: str | None = None,
                    now=None, fetcher=None) -> tuple[int, str]:
    """`vss xbrl --annual`. Returns (exit_code, report_markdown)."""
    from datetime import datetime
    from pathlib import Path

    import yaml

    from .config import ConfigError, load_watchlist
    from .manual import MANUAL_DIR, parse_manual, section5_gate
    from .store import persist_earnings

    run_ts = now or datetime.now().astimezone()
    as_of = run_ts.date()

    entries = {e.ticker.upper(): e for e in load_watchlist(watchlist_path)}
    entry = entries.get(ticker.strip().upper())
    intake = False
    if entry is None:
        # INTAKE (2026-09-04): a name that is NOT on the watchlist yet.
        #
        # **THE ORDER WAS BACKWARDS.** Until today this path refused any
        # ticker without an entry, so the only way to look at a candidate's
        # filed figures was to put it on the watchlist FIRST -- and entering
        # a name stamps `dd_at_entry` and FREEZES GATE 1 under E12. Reading
        # a filer's own facts is not a decision to watch it, and it must not
        # cost a frozen catalyst window.
        #
        # NOTHING IS GUESSED IN EXCHANGE. The entry supplied four things and
        # each is accounted for: the TICKER (the caller's), the CIK (--cik,
        # and no resolution step exists either way), the filer's NAME (SEC's
        # own `entityName` where the facts carry one), and the QUOTE
        # CURRENCY -- a fact about a LISTING and not a tagged fact, which
        # differs from the reporting currency for any name traded away from
        # home, so the caller states it or this refuses.
        if cik is None:
            raise ConfigError(
                f"ticker {ticker} is not in {watchlist_path} and no --cik "
                f"was given. A name may be INTAKEN with no watchlist entry "
                f"(entering one freezes Gate 1 under E12), but SEC "
                f"identifies filers by CIK and nothing here resolves one: "
                f"pass --cik.")
        if not quote_currency:
            raise ConfigError(
                f"ticker {ticker} is not in {watchlist_path}, so its QUOTE "
                f"CURRENCY is not on file. It is a fact about a LISTING and "
                f"not a tagged fact -- the filer's facts give the REPORTING "
                f"currency, and the two differ for any name traded away "
                f"from home -- so it is stated by the caller or not at all: "
                f"pass --quote-currency.")
        entry = _IntakeEntry(ticker=ticker.strip().upper(),
                             name=(name or ticker.strip().upper()),
                             currency=quote_currency.strip().upper(),
                             cik=int(cik))
        intake = True
    cik = cik if cik is not None else entry.cik
    if cik is None:
        raise ConfigError(
            f"{entry.ticker} has no cik. SEC identifies filers by CIK, not by "
            f"ticker, and NO CIK RESOLUTION STEP IS BUILT. That is a gap in "
            f"this project, NOT a closed door: "
            f"https://www.sec.gov/files/company_tickers.json answers HTTP 200 "
            f"to a caller that declares a real contact, and every CIK in this "
            f"project was typed by hand anyway. Add `cik: NNNNNN` to the "
            f"watchlist entry or pass --cik."
        )

    target = Path(manual_dir or MANUAL_DIR) / f"{entry.ticker.upper()}.yaml"
    error, years, report = None, [], ""
    try:
        facts = (fetcher or fetch_company_facts)(int(cik))
        # WHICH VOCABULARY AND WHICH CURRENCY, from the facts. Both were
        # assumed before: `us-gaap` and USD, which made every 20-F filer
        # under IFRS unreachable (REVIEW-4 report B #10).
        taxonomy = pick_taxonomy(facts)
        currency = reporting_currency(facts, taxonomy)
        if intake and not name:
            # THE FILER'S OWN NAME, off its own facts. `entityName` is what
            # the filer files under, not a label anyone here chose, and an
            # intake that invented one would put a guess in the header of
            # every figure's provenance line.
            filed = str(facts.get("entityName") or "").strip()
            if filed:
                entry = replace(entry, name=filed)
        years, passed_over = build_annual(facts, limit=limit,
                                          taxonomy=taxonomy, currency=currency)
        if not years:
            raise XbrlError(
                f"no annual facts found for CIK {cik} in the `{taxonomy.name}` "
                f"taxonomy. Section 5 needs a twelve-month window and this "
                f"filer tagged none ending in its own fiscal year-end month.")
        text = manual_yaml(ticker=entry.ticker.upper(), name=entry.name,
                           cik=int(cik), quote_currency=entry.currency,
                           years=years, run_ts=run_ts, facts=facts,
                           taxonomy=taxonomy, currency=currency)

        # Parsed back through the MANUAL loader before anything is written.
        # The checks are imported rather than repeated, so this path cannot
        # emit a file `vss manual` would reject.
        validated, gate = None, None
        try:
            parsed = parse_manual(yaml.safe_load(text), path=target)
            gate = section5_gate(parsed, as_of=as_of)
        except ConfigError as exc:
            validated = str(exc)

        written = backup = None
        if write and validated is None:
            written, backup = write_manual_file(text, target, run_ts=run_ts,
                                                force=force)
        report = render_annual_report(
            ticker=entry.ticker.upper(), name=entry.name, cik=int(cik),
            years=years, facts=facts, passed_over=passed_over, as_of=as_of,
            target=target, written=written, backup=backup, validated=validated,
            gate=gate, text=None if written else text,
            taxonomy=taxonomy, currency=currency)
        if validated is not None:
            error = validated
    except XbrlError as exc:
        error = str(exc)
        log.error("%s: %s", entry.ticker, error)
        report = (f"# vss xbrl --annual -- {entry.ticker} ({entry.name}) -- "
                  f"{as_of.isoformat()}\n\n## REFUSED\n\n{error}\n")

    missing = sorted({f for y in years for f in y.missing})
    persist_earnings(db_path, {
        "run_ts": run_ts.isoformat(timespec="seconds"),
        "as_of": as_of.isoformat(),
        "ticker": entry.ticker,
        "source_url": API_URL.format(cik=int(cik)),
        "model": None,                      # no model reads XBRL
        "shadow": 1,
        "trips": None,
        "cannot_evaluate": None,
        "extraction_uncertain": 1 if (error or missing) else 0,
        "uncertainty_reasons": ("not tagged by the filer: " + ", ".join(missing))
                               if missing else error,
        "error": error,
        "alert": report,
        "raw_response": None,               # 3MB of facts; the URL is the record
    })
    return (0 if error is None else 1), report
