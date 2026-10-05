"""E92: the report-date refresh. It fetches, it extracts, it reports.

**IT NEVER DECIDES.** Nothing here writes `fv_base`, `tier`, `mbp`,
`stop_price` or `status` to `config/watchlist.yaml`, and nothing here scores
a gate. `assert_no_watchlist_write` is the mechanical guarantee and
`tests/test_refresh.py` holds it to it.

The three acts E92 allows, in order:

1. **FETCH** the filing by whatever route the issuer allows -- SEC XBRL for a
   US filer, the Nasdaq Nordic feed where it reaches, and NOTHING AT ALL for
   an issuer whose site refuses automated requests. A refusal is a finding
   (`reference/FETCHER-SURVEY.md` section 5): the report names the document
   and its expected URL so the owner can fetch it by hand.
2. **EXTRACT** into the store, under the ordinary provenance rules. A tagged
   SEC fact enters VERIFIED / `tagged` (E40 rule 1). Anything read off a PDF
   enters UNVERIFIED and waits for the owner's read-back. An absent concept
   is DATA MISSING -- **never** E85's NOT PRESENTED, which stands on a
   searched report and not on a missed tag.
3. **REPORT** to `reports/REFRESH-<TICKER>-<date>.md`, and surface a pointer
   as NEEDS OWNER in the nightly run.

A refresh never overwrites a VERIFIED figure of any kind. New periods are
ADDED; a differing value for a figure already held is REPORTED as a conflict
and the store keeps what it has.

**THIS COMMAND IS NOT SCHEDULED, AND THAT IS A DECISION** (the owner,
2026-08-31, recorded beneath E92 and in `deploy/README.md`). It writes into
`config/manual/`, a git-tracked configuration directory, and unattended
writes into tracked config do not run overnight. The owner runs
`vss refresh --due` BY HAND on report weeks. **Do not add a timer, a cron
line, or a call to this from the nightly run** -- scheduling it would need
`deploy/vss.service`'s `ReadWritePaths` widened to `config/manual`, and that
widening is the decision, not the plumbing. Re-deciding it is the owner's
act. What IS scheduled is the nightly run's NEEDS OWNER section, which
reports what a hand-run refresh left behind and decides nothing.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Sequence
from . import env

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WATCHLIST_PATH = PROJECT_ROOT / "config" / "watchlist.yaml"
MANUAL_DIR = PROJECT_ROOT / "config" / "manual"
REPORTS_DIR = PROJECT_ROOT / "reports"
STATE_PATH = PROJECT_ROOT / "data" / "refresh_state.json"
STATE_VERSION = 1

#: The topic to POST the NEEDS OWNER pointer to. Read from the environment,
#: never committed: a topic anyone knows is a topic anyone can publish to.
#:
#: OUTBOUND ONLY, and that is a rule and not an implementation detail (E92).
#: Nothing in this module reads from the topic -- there is no GET, no poll,
#: no subscribe. A tool that took instruction from a public channel would be
#: a tool that decides on a stranger's word.
#:
#: `vss watch` has its own, older `VSS_NTFY_URL`. The two are deliberately
#: separate variables: one may be set without the other, and a refresh
#: pointer is not a disclosure alert.
NTFY_ENV = "NTFY_TOPIC"
NTFY_TIMEOUT_SECONDS = 5
NTFY_DEFAULT_HOST = "https://ntfy.sh"

ROUTE_EDGAR = "sec-xbrl"
ROUTE_NORDIC = "nasdaq-nordic"
ROUTE_MANUAL = "manual download"

#: Why a route is closed, and what the owner has to fetch instead.
#:
#: REFUSED means the issuer's own host turns this tool away -- measured, on
#: record, and not to be worked around: `source.py` answers a 401/403/429 by
#: naming the door that is still open rather than by dressing up as a
#: browser, and E92 keeps that posture for the refresh.
#:
#: NO ADAPTER means nothing about the issuer refuses us; the archive its
#: market files into simply has no adapter in this project yet. The
#: distinction matters to the owner: one is a wall, the other is a gap, and
#: only the second is worth building.
REFUSED = "REFUSED"
NO_ADAPTER = "NO ADAPTER"


@dataclass(frozen=True)
class ManualRoute:
    """A route that is closed, with the door that is still open beside it."""

    kind: str                      # REFUSED | NO_ADAPTER
    reason: str
    document: str = ""
    url: str = ""


#: Issuers whose sites REFUSE this tool, measured and on record. Keep this
#: list evidence-backed: an entry here stops an attempt being made at all,
#: so a guess would silently strand a name that could be fetched.
REFUSING_ISSUERS: dict[str, ManualRoute] = {
    "SAP.DE": ManualRoute(
        kind=REFUSED,
        reason=("sap.com returns HTTP 403 to this tool -- measured 2026-08-24, "
                "reference/FETCHER-SURVEY.md section 5. Nothing is attempted "
                "and no request pretends to be a browser."),
        document="SAP Quarterly Statement Q3 2026 (PDF)",
        url="https://www.sap.com/investors/en/reports.html",
    ),
}

#: Where a market's archive has no adapter here. The document string is what
#: the owner is looking for; the URL is where it is published.
#:
#: **THE TWO ENTRIES BELOW ARE UNMEASURED.** Unlike SAP's 403 -- which was
#: measured from this host on 2026-08-24 and is on record in
#: FETCHER-SURVEY -- the reasons and URLs here are the author's judgement
#: and NO REQUEST WAS EVER MADE to either host to check them. The owner
#: accepted them as they stand on 2026-08-31 rather than spend a fetch on a
#: name neither due nor near: **they resolve the first time either name is
#: actually refreshed**, and until then a reader should treat the URL as a
#: starting point and not as a verified fact. An unknown URL is left empty
#: and says so; a REPORTED one that turns out wrong costs one browser tab.
NO_ADAPTER_ISSUERS: dict[str, ManualRoute] = {
    "MC.PA": ManualRoute(
        kind=NO_ADAPTER,
        reason=("Euronext Paris. No EU OAM adapter is built (FETCHER-SURVEY "
                "section 6: twenty-seven archives, no common API)."),
        document="LVMH interim/annual report (PDF)",
        url="https://www.lvmh.com/en/publications",
    ),
    "NHY.OL": ManualRoute(
        kind=NO_ADAPTER,
        reason=("Oslo Bors is not on the Nasdaq Nordic feed this project "
                "reaches; no Euronext adapter is built."),
        document="Norsk Hydro quarterly report (PDF)",
        url="https://www.hydro.com/en/investors/reports-and-presentations/",
    ),
}


@dataclass(frozen=True)
class Route:
    """Which door this name's filing comes through, and what it costs."""

    kind: str
    detail: str = ""
    manual: ManualRoute | None = None

    @property
    def automatic(self) -> bool:
        return self.kind in (ROUTE_EDGAR, ROUTE_NORDIC)


def route_for(entry, *, issuers_path: Path | None = None) -> Route:
    """The route for one watchlist entry.

    A REFUSAL IS ABOUT A HOST, NOT ABOUT A NAME, and the two must not be
    confused. `sap.com` turns this tool away; `data.sec.gov` does not, and
    SAP is a 20-F filer whose tagged facts E41 already reads from it. So a
    refusal on record does NOT suppress an automatic route that runs at a
    different host: it is carried BESIDE the route as work the owner still
    has to do by hand, because the thing the refusing host publishes -- a
    quarterly statement a 20-F filer never files with the SEC -- is not in
    the tagged facts at all.

    Where there is no automatic route, the refusal is the whole story and
    the route is the hand download.
    """
    ticker = entry.ticker.upper()
    refused = REFUSING_ISSUERS.get(ticker)
    if entry.cik is not None:
        return Route(ROUTE_EDGAR,
                     f"SEC XBRL companyfacts, CIK {int(entry.cik)}",
                     refused)
    if refused is not None:
        return Route(ROUTE_MANUAL, refused.reason, refused)
    if _on_nordic_feed(ticker, issuers_path):
        return Route(ROUTE_NORDIC,
                     "Nasdaq Nordic disclosure feed (config/nordic_issuers.yaml)",
                     refused)
    gap = NO_ADAPTER_ISSUERS.get(ticker)
    if gap is not None:
        return Route(ROUTE_MANUAL, gap.reason, gap)
    return Route(ROUTE_MANUAL, "no route is built for this ticker",
                 ManualRoute(kind=NO_ADAPTER,
                             reason=("no CIK on the entry, not on the Nasdaq "
                                     "Nordic feed, and no adapter for its "
                                     "market"),
                             document="the issuer's own report for the period"))


def _on_nordic_feed(ticker: str, issuers_path: Path | None = None) -> bool:
    from .nordic import ISSUERS_PATH, NordicError, issuer_for

    try:
        issuer_for(ticker, path=issuers_path or ISSUERS_PATH)
    except (NordicError, OSError):
        return False
    return True


# --- what is due ----------------------------------------------------------


#: A quarter of the calendar year, as month-end dates. A catalyst dated D
#: reports a period that ENDED BEFORE D, and for a quarterly reporter the
#: newest such end is one of these.
_QUARTER_ENDS = ((3, 31), (6, 30), (9, 30), (12, 31))
_HALF_ENDS = ((6, 30), (12, 31))


def expected_period_end(catalyst: date, frequency: str = "quarterly") -> date:
    """The period a catalyst dated ``catalyst`` reports on.

    THE CALENDAR GRID IS AN APPROXIMATION AND IS SAID SO OUT LOUD. An issuer
    whose fiscal quarters do not end on calendar quarters (DECK's March year
    end) will be placed on the wrong grid by a few weeks. That is tolerable
    HERE and nowhere else: this function only SELECTS WHAT TO GO AND LOOK AT.
    It decides nothing, and a fetch that finds no new period reports exactly
    that. Nothing downstream reads it.
    """
    ends = _HALF_ENDS if frequency == "half_yearly" else _QUARTER_ENDS
    candidates = [date(year, m, d)
                  for year in (catalyst.year - 1, catalyst.year)
                  for m, d in ends]
    earlier = [d for d in candidates if d < catalyst]
    return max(earlier)


def store_covers(ticker: str, period_end: date, *,
                 manual_dir: Path | None = None) -> tuple[bool, date | None]:
    """Does the store already hold data reaching ``period_end``?

    Returns (covered, newest end on file). A store that does not exist, or
    does not load, is NOT covered -- and the refresh reports why rather than
    crashing on it.
    """
    from .config import ConfigError
    from .manual import load_manual

    try:
        parsed = load_manual(ticker, directory=manual_dir or MANUAL_DIR)
    except (ConfigError, OSError):
        return False, None
    ends = [p.period_end for p in parsed.periods]
    ends += [a.period_end for a in parsed.annual]
    newest = max(ends) if ends else None
    return (newest is not None and newest >= period_end), newest


@dataclass(frozen=True)
class Due:
    entry: object
    catalyst: date
    expects: date
    newest_on_file: date | None
    route: Route


def due_names(entries: Sequence, *, as_of: date,
              manual_dir: Path | None = None,
              issuers_path: Path | None = None) -> list[Due]:
    """Watchlist names whose catalyst has passed and whose store lacks it.

    Two conditions, both required (E92's `--due`):
      * the entry names a `catalyst_date` and it is on or before ``as_of``;
      * the store holds no period reaching the end that catalyst reports on.
    """
    out: list[Due] = []
    for entry in entries:
        # A DROPPED name is a RECORD, not a stage (rules.py). It is out of
        # the process, so its filings are not fetched -- MSFT's 2026-07-29
        # catalyst is on file and stays on file. Naming it explicitly with
        # `--ticker` still works: that is the owner asking.
        if getattr(entry, "status", None) == "DROPPED":
            continue
        catalyst = getattr(entry, "catalyst_date", None)
        if catalyst is None or catalyst > as_of:
            continue
        frequency = getattr(entry, "reporting_frequency", "quarterly")
        expects = expected_period_end(catalyst, frequency)
        covered, newest = store_covers(entry.ticker, expects,
                                       manual_dir=manual_dir)
        if covered:
            continue
        out.append(Due(entry=entry, catalyst=catalyst, expects=expects,
                       newest_on_file=newest,
                       route=route_for(entry, issuers_path=issuers_path)))
    return out


# --- the store merge ------------------------------------------------------


@dataclass
class Conflict:
    """A fetched value that disagrees with one the store already holds."""

    period: str
    field: str
    held: float | None
    held_status: str
    fetched: float | None

    def line(self) -> str:
        return (f"`{self.period}` / `{self.field}`: store holds "
                f"{self.held:,.10g} ({self.held_status}), the filing states "
                f"{self.fetched:,.10g} -- **the store keeps what it has**"
                if self.held is not None and self.fetched is not None else
                f"`{self.period}` / `{self.field}`: values differ and the "
                f"store keeps what it has")


@dataclass
class Extraction:
    """What a fetch found, before anything is written."""

    periods_added: list[str] = field(default_factory=list)
    fields_added: int = 0
    conflicts: list[Conflict] = field(default_factory=list)
    missing_concepts: list[str] = field(default_factory=list)
    text: str = ""                        # the YAML block to append
    note: str = ""


#: What the figures came off. E92 turns on this distinction and nothing else:
#: a TAGGED FACT carries its own provenance and needs no second reader; a
#: RENDERED DOCUMENT was transcribed, and a transcription is exactly what a
#: read-back exists to check.
SOURCE_TAGGED = "tagged-fact"
SOURCE_DOCUMENT = "rendered-document"


def figure_status(source_kind: str) -> tuple[str, str | None]:
    """E92's provenance rule, in ONE place so it can be pinned.

    A tagged SEC fact enters **VERIFIED / `tagged`** -- E40 rule 1: verified
    BY PROVENANCE, because there is no transcription to have got wrong and
    the tag map is itself the committed record of which tag answers which
    field.

    **Everything else enters UNVERIFIED**, with no kind, and waits for the
    owner's read-back. A figure read off a rendered PDF is a transcription;
    E40's three kinds each record a reading a person or a second document
    did, and an automatic fetch is neither of those things.
    """
    from .manual import KIND_TAGGED, STATUS_UNVERIFIED, STATUS_VERIFIED

    if source_kind == SOURCE_TAGGED:
        return STATUS_VERIFIED, KIND_TAGGED
    return STATUS_UNVERIFIED, None


def _period_block(period: str, period_end: date, period_basis: str,
                  document: str, url: str,
                  figures: dict,
                  source_kind: str = SOURCE_TAGGED) -> tuple[str, int]:
    """One `periods:` entry as text, with its own provenance on every figure.

    Written as TEXT and appended, never dumped from a parsed document: these
    files carry the rulings in their comments, and a round-trip through a
    YAML dumper would throw every one of them away.
    """
    from .xbrl import _number, _yaml_scalar

    lines = [f"  - period: {period}",
             f"    period_end: {period_end.isoformat()}",
             f"    period_basis: {period_basis}",
             f"    document: {_yaml_scalar(document)}"]
    if url:
        lines.append(f"    url: {_yaml_scalar(url)}")
    lines.append("    figures:")
    status, kind = figure_status(source_kind)
    written = 0
    for name in sorted(figures):
        figure = figures[name]
        lines.append(f"      {name}:")
        lines.append(f"        value: {_number(figure.value)}")
        lines.append(f"        page: {_yaml_scalar(figure.provenance)}")
        lines.append(f"        status: {status}")
        if kind:
            lines.append(f"        verified_kind: {kind}")
        written += 1
    return "\n".join(lines), written


def _insert_periods(text: str, block: str) -> str:
    """Append period entries to the file's `periods:` block, or open one.

    Textual, deliberately. The alternative -- parse, mutate, dump -- would
    strip every comment in the file, and in these files the comments carry
    the rulings the figures stand on.
    """
    lines = text.rstrip("\n").split("\n")
    try:
        start = next(i for i, line in enumerate(lines)
                     if line.rstrip() == "periods:")
    except StopIteration:
        # No `periods:` block yet. Open one at the end of the document --
        # top-level key order does not matter to the loader.
        return (text.rstrip("\n") + "\n\nperiods:\n" + block + "\n")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line and not line[0].isspace() and not line.lstrip().startswith("#"):
            end = i
            break
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    merged = lines[:end] + block.split("\n") + lines[end:]
    return "\n".join(merged) + "\n"


#: The quarter path speaks FRAMEWORK 4.2's vocabulary (`xbrl.build_quarters`:
#: revenue, op_income, eps) and the store speaks its own schema. A block
#: written in the wrong vocabulary does not load -- `eps` landed in
#: config/manual/NVR.yaml on 2026-09-13 and the file refused to open --
#: so the names are translated here, at the writer, and a name the schema
#: does not carry is dropped and NAMED rather than written.
STORE_NAME_FOR = {"eps": "diluted_eps", "op_income": "operating_income"}


def store_figures(figures: dict) -> tuple[dict, list[str]]:
    """(figures keyed by the store's own names, names dropped)."""
    from .manual import FIELDS

    allowed = {spec.name for spec in FIELDS}
    out, dropped = {}, []
    for name, figure in figures.items():
        store_name = STORE_NAME_FOR.get(name, name)
        if store_name in allowed:
            out[store_name] = figure
        else:
            dropped.append(name)
    return out, dropped


def validated_insert(original: str, block: str, path: Path) -> str:
    """`_insert_periods`, refused unless the result loads through the store's
    own parser. Raises RefreshError with the loader's message; nothing is
    written by this function either way."""
    import yaml

    from .config import ConfigError
    from .manual import parse_manual

    text = _insert_periods(original, block)
    try:
        parse_manual(yaml.safe_load(text), path=Path(path))
    except (ConfigError, yaml.YAMLError) as exc:
        raise RefreshError(
            f"the appended periods would leave {Path(path).name} unable to "
            f"load, so NOTHING IS WRITTEN: {exc}") from exc
    return text


def extract_edgar(entry, *, expects: date, manual_dir: Path | None = None,
                  fetcher: Callable | None = None,
                  limit: int = 8) -> Extraction:
    """Fetch the filer's tagged facts and prepare the NEW quarters only.

    Nothing is written here -- the caller writes, so that a dry run and a
    real run walk the same code and differ in one branch.
    """
    from .config import ConfigError
    from .manual import ORIGIN_XBRL, load_manual
    from .xbrl import (build_quarters, fetch_company_facts,
                       fiscal_year_end_month)

    out = Extraction()
    facts = (fetcher or fetch_company_facts)(int(entry.cik))
    quarters = build_quarters(facts, limit=limit)
    if not quarters:
        out.note = ("the filer tagged no quarters this path can read. "
                    "DATA MISSING -- not NOT PRESENTED (E92): a missed tag "
                    "is not a searched report.")
        return out

    try:
        parsed = load_manual(entry.ticker, directory=manual_dir or MANUAL_DIR)
        held = {p.period: p for p in parsed.periods}
        newest = max([p.period_end for p in parsed.periods]
                     + [a.period_end for a in parsed.annual], default=None)
    except (ConfigError, OSError) as exc:
        out.note = f"the store does not load ({exc}); nothing is written."
        return out

    # THE UNIT TRAP, which `write_manual_file` already refuses on the whole-file
    # path and which an APPEND could otherwise walk straight into. XBRL states
    # whole units -- 21,108,000,000 -- where a hand-read report states millions.
    # A file holding both passes every check in the loader, because each period
    # is internally consistent, and every comparison across them is meaningless.
    # So a tagged extraction only ever lands in a `sec-xbrl` store.
    if parsed.origin != ORIGIN_XBRL:
        out.note = (f"the store's origin is `{parsed.origin}` and this route "
                    f"writes `{ORIGIN_XBRL}`. NOTHING IS WRITTEN: XBRL states "
                    f"whole units where a hand-read report states millions, "
                    f"and a history holding both is a history in which no "
                    f"comparison means anything. The figures are reported "
                    f"below and entered by the path that owns this file.")
        return out

    fy_end_month = fiscal_year_end_month(facts)
    blocks: list[str] = []
    for quarter in quarters:
        if not quarter.figures or quarter.balance_sheet_only:
            continue
        end = _quarter_end(quarter, fy_end_month)
        if end is None:
            continue
        existing = held.get(quarter.period)
        if existing is not None:
            # NEVER OVERWRITE. A figure the store already holds stands; a
            # disagreement is reported and the store keeps what it has.
            for name, figure in store_figures(quarter.figures)[0].items():
                current = existing.figures.get(name)
                if current is None or not current.present:
                    continue
                if abs(current.value - figure.value) > 1e-6:
                    out.conflicts.append(Conflict(
                        period=quarter.period, field=name,
                        held=current.value,
                        held_status=current.status_with_kind,
                        fetched=figure.value))
            continue
        if newest is not None and end <= newest:
            continue
        figures, dropped = store_figures(quarter.figures)
        if dropped:
            out.missing_concepts = sorted(set(out.missing_concepts) | {
                f"{quarter.period}: {name} has no field in the store's schema"
                for name in dropped})
        if not figures:
            continue
        block, count = _period_block(
            period=quarter.period, period_end=end,
            period_basis=quarter.period_basis,
            document=(f"SEC XBRL companyfacts, CIK "
                      f"{int(entry.cik):010d} -- tagged facts, no document "
                      f"was rendered or transcribed"),
            url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(entry.cik):010d}.json",
            figures=figures)
        blocks.append(block)
        out.periods_added.append(quarter.period)
        out.fields_added += count
        out.missing_concepts = sorted(set(out.missing_concepts)
                                      | set(quarter.missing))
    out.text = "\n".join(blocks)
    if not blocks and not out.conflicts:
        out.note = (f"nothing new: the newest quarter the filer has tagged is "
                    f"already on file, or ends on or before "
                    f"{newest.isoformat() if newest else 'the store''s newest entry'}.")
    return out


def _quarter_end(quarter, fy_end_month: int) -> date | None:
    """The period end of an XbrlQuarter, from the facts it carries."""
    for figure in quarter.figures.values():
        try:
            return date.fromisoformat(figure.end)
        except (TypeError, ValueError):
            continue
    return None


def assert_no_watchlist_write(before: str, after: str) -> None:
    """E92, mechanically: the refresh never writes the watchlist.

    Called with the watchlist's bytes either side of a refresh. It exists so
    that the rule is enforced by the code and not only by the tests -- if a
    future edit ever reaches the watchlist from this module, the run stops.
    """
    if before != after:
        raise RefreshError(
            "E92 VIOLATED: config/watchlist.yaml changed during a refresh. "
            "A refresh fetches, extracts and reports; it never writes "
            "fv_base, tier, mbp, stop, status -- or anything else -- to the "
            "watchlist. Nothing was reported and the run is stopped.")


class RefreshError(Exception):
    """A refresh could not complete. Never raised for a closed route."""


# --- the report -----------------------------------------------------------


def render_refresh(*, entry, due: Due, extraction: Extraction | None,
                   as_of: date, run_ts: datetime, written: Path | None,
                   store_path: Path, downloaded: Path | None = None) -> str:
    """`reports/REFRESH-<TICKER>-<date>.md`.

    THE STYLE IS A CONSTRAINT, not a preference (E92). The figures as filed,
    with their tag or page. Guidance and management statements as REFERAT
    with the source beside them. NO judgement, NO thesis language, and no
    "this strengthens / weakens" anywhere -- a refresh reports what the
    filing says and the owner decides what it means.
    """
    out: list[str] = []
    ticker = entry.ticker
    out.append(f"# REFRESH — {ticker} ({entry.name}) — {as_of.isoformat()}")
    out.append("")
    out.append(f"**Run:** {run_ts.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    out.append("")
    out.append(
        "*E92: this is a FETCH, an EXTRACT and a REPORT. Nothing here writes "
        "`fv_base`, `tier`, `mbp`, `stop_price` or `status` to the watchlist, "
        "and nothing here scores a gate. No figure below is a verdict.*")
    out.append("")
    out.append(f"- **Catalyst:** {due.catalyst.isoformat()}"
               + (f" — {entry.catalyst_event.strip().splitlines()[0]}"
                  if getattr(entry, "catalyst_event", None) else ""))
    out.append(f"- **Period expected:** {due.expects.isoformat()} "
               f"(calendar grid; a selector, not a verdict)")
    out.append(f"- **Newest on file before this run:** "
               f"{due.newest_on_file.isoformat() if due.newest_on_file else 'nothing'}")
    out.append(f"- **Route:** {due.route.kind} — {due.route.detail}")
    out.append(f"- **Store:** `{store_path}`")
    out.append("")

    if due.route.manual is not None and due.route.automatic:
        # The automatic route runs, AND something still has to be fetched by
        # hand -- a refusing IR host publishing what the tagged facts do not
        # carry. Both are true and the report says both.
        manual = due.route.manual
        out.append("## ALSO NEEDED BY HAND — the issuer's own host refuses us")
        out.append("")
        out.append(f"{manual.reason}")
        out.append("")
        out.append("| What is needed | Where |")
        out.append("|---|---|")
        out.append(f"| {manual.document or 'the issuer’s report for the period'} "
                   f"| {manual.url or '**URL not on record**'} |")
        out.append("")
        out.append("**Every figure read off that document enters UNVERIFIED "
                   "and waits for your read-back (E92).**")
        out.append("")

    if due.route.manual is not None and not due.route.automatic:
        manual = due.route.manual
        out.append("## THE ROUTE IS CLOSED — download by hand")
        out.append("")
        kind = ("The issuer's host REFUSES this tool"
                if manual.kind == REFUSED else
                "No adapter is built for this market's archive")
        out.append(f"**{kind}.** {manual.reason}")
        out.append("")
        out.append("**Nothing was fetched, and nothing was written to the "
                   "store** — a partial write from a route that did not "
                   "complete is worse than no write (E92).")
        out.append("")
        out.append("| What is needed | Where |")
        out.append("|---|---|")
        out.append(f"| {manual.document or 'the issuer’s report for the period'} "
                   f"| {manual.url or '**URL not on record** — the owner knows where this is published'} |")
        out.append("")
        out.append("Once downloaded, the ordinary paths take it: `vss nordic "
                   "--download` for a Nordic filing already on the feed, "
                   "`vss appendix` for a figures workbook, or a hand entry. "
                   "**Every figure read off a PDF enters UNVERIFIED and waits "
                   "for your read-back (E92).**")
        out.append("")
        return "\n".join(out) + "\n"

    if downloaded is not None:
        out.append("## FETCHED")
        out.append("")
        out.append(f"The document was downloaded to `{downloaded}` and recorded "
                   f"in the sources manifest.")
        out.append("")
        out.append("**No figure was transcribed from it by this run.** This "
                   "project has no automatic reader for a rendered PDF, and "
                   "E92 would put anything one produced at UNVERIFIED in any "
                   "case. The figures enter through the ordinary paths and "
                   "wait for your read-back.")
        out.append("")

    if extraction is None:
        out.append("*No extraction was attempted.*")
        out.append("")
        return "\n".join(out) + "\n"

    out.append("## THE FIGURES AS FILED")
    out.append("")
    if extraction.periods_added:
        out.append(f"{len(extraction.periods_added)} new period(s) — "
                   f"{', '.join('`' + p + '`' for p in extraction.periods_added)} — "
                   f"carrying {extraction.fields_added} figure(s).")
        out.append("")
        out.append(f"**Provenance:** every figure entered "
                   f"**VERIFIED / `tagged`** — E40 rule 1: a tagged SEC fact "
                   f"is verified BY PROVENANCE (tag + accession + filing "
                   f"date, on each figure's own `page:` line). Nothing was "
                   f"rendered, quoted or transcribed.")
        out.append("")
        if written is not None:
            out.append(f"Written to `{store_path}`"
                       f" (backup `{written.name}`)." if written.name.endswith(".bak")
                       else f"Written to `{store_path}`.")
        else:
            out.append("**Nothing was written** — this was a dry run.")
        out.append("")
    else:
        out.append("No new period. " + (extraction.note or ""))
        out.append("")

    if extraction.conflicts:
        out.append("## CONFLICTS — reported, not resolved")
        out.append("")
        out.append("The filing states a different value for a figure the "
                   "store already holds. **The store keeps what it has "
                   "(E92)**; which is right is yours to settle.")
        out.append("")
        for conflict in extraction.conflicts:
            out.append(f"- {conflict.line()}")
        out.append("")

    if extraction.missing_concepts:
        out.append("## CONCEPTS THE FILER DID NOT TAG")
        out.append("")
        out.append(", ".join(f"`{c}`" for c in extraction.missing_concepts))
        out.append("")
        out.append("**DATA MISSING, not NOT PRESENTED.** E85's state stands "
                   "on a whole report having been searched — document, scope, "
                   "date — and this run searched a tag map. If one of these "
                   "legs matters, the search is yours to make and to record.")
        out.append("")

    out.append("## WHAT A RE-STRIKE WOULD READ — information, not a write")
    out.append("")
    out.append(_restrike_note(entry, extraction))
    out.append("")
    out.append("---")
    out.append("")
    out.append("*E92. No fair value was struck, no tier scored, no gate read, "
               "and no watchlist field written. The next move is yours.*")
    return "\n".join(out) + "\n"


def _restrike_note(entry, extraction: Extraction) -> str:
    """What the added periods would do to the section 5 basis, if anything.

    Deliberately narrow: it states which WINDOW a re-strike would stand on,
    and never a fair value. E39/E87 are untouched -- the fair value on the
    entry stands until the owner re-strikes it.
    """
    if not extraction.periods_added:
        return ("Nothing was added, so nothing moves. The fair value on the "
                "entry stands as struck.")
    return (
        f"The store now holds {len(extraction.periods_added)} more quarter(s). "
        f"E19 puts section 5 on `periods:` ONLY where four CONSECUTIVE "
        f"quarters exist; below four the basis stays the newest `annual:` "
        f"entry, unchanged. **No fair value is re-struck here and none is "
        f"nulled** — E39 and E87 are untouched, and the `fv_base` on the "
        f"entry stands exactly as it was until you re-strike it. "
        f"`vss manual --ticker {entry.ticker}` prints which basis the store "
        f"resolves today.")


# --- state, and what each name waits on -----------------------------------


def load_state(path: Path = STATE_PATH) -> dict:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"version": STATE_VERSION, "refreshed": {}}
    if not isinstance(document, dict):
        return {"version": STATE_VERSION, "refreshed": {}}
    document.setdefault("refreshed", {})
    return document


def save_state(document: dict, path: Path = STATE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return path


def record_refresh(ticker: str, *, report: Path, as_of: date, route: str,
                   periods: Sequence[str], conflicts: int,
                   waiting: str = "", path: Path = STATE_PATH) -> dict:
    """Remember that a refresh happened. NOT a decision, and not the watchlist.

    The state file holds a POINTER and a date. What each name waits on is
    recomputed live by `needs_owner` off the store and the watchlist, so a
    stale state file can never claim an owner action that has been done.
    """
    document = load_state(path)
    document["refreshed"][ticker.upper()] = {
        "date": as_of.isoformat(),
        "report": str(report),
        "route": route,
        "periods": list(periods),
        "conflicts": int(conflicts),
        "waiting": waiting,
    }
    save_state(document, path)
    return document


@dataclass(frozen=True)
class NeedsOwner:
    ticker: str
    report: str
    waits: tuple[str, ...]
    refreshed: str

    def line(self) -> str:
        return (f"`{self.ticker}` — {', '.join(self.waits)} — "
                f"`{self.report}` ({self.refreshed})")


def waits_for(entry, *, manual_dir: Path | None = None,
              root: Path = PROJECT_ROOT) -> tuple[str, ...]:
    """What this name still waits on, computed from the live files.

    Never read from the state file: an owner who did the work should see the
    item disappear on the next run without touching anything.
    """
    from .config import ConfigError
    from .manual import load_manual

    waits: list[str] = []
    try:
        parsed = load_manual(entry.ticker, directory=manual_dir or MANUAL_DIR)
    except (ConfigError, OSError):
        parsed = None
    if parsed is not None:
        unverified = [f for f in parsed.unverified() if f.present]
        if unverified:
            waits.append(f"read-back ({len(unverified)} UNVERIFIED)")
    if getattr(entry, "tier", None) is None:
        waits.append("tier")
    # A store newer than the record the fair value stands on is the owner's
    # re-strike and write. Computed, never assumed.
    if parsed is not None and getattr(entry, "run_record", None):
        record_path = Path(entry.run_record)
        if not record_path.is_absolute():
            record_path = root / record_path
        basis_end = _record_basis_end(record_path)
        ends = [p.period_end for p in parsed.periods]
        ends += [a.period_end for a in parsed.annual]
        newest = max(ends) if ends else None
        if basis_end is not None and newest is not None and newest > basis_end:
            waits.append(f"re-strike + your write (store reaches "
                         f"{newest.isoformat()}, record stands on "
                         f"{basis_end.isoformat()})")
    return tuple(waits)


def _record_basis_end(path: Path) -> date | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    basis = document.get("basis")
    if isinstance(basis, dict):
        for key in ("end", "period_end"):
            try:
                return date.fromisoformat(str(basis[key])[:10])
            except (KeyError, TypeError, ValueError):
                continue
    dates = document.get("dates")
    if isinstance(dates, dict):
        for key in ("flows_to", "balance_sheet", "flows"):
            try:
                return date.fromisoformat(str(dates[key])[:10])
            except (KeyError, TypeError, ValueError):
                continue
    return None


def needs_owner(entries: Sequence, *, state_path: Path = STATE_PATH,
                manual_dir: Path | None = None,
                root: Path = PROJECT_ROOT) -> list[NeedsOwner]:
    """The NEEDS OWNER pointers for tonight's run.

    A POINTER, NOT A SUMMARY (E92): ticker, what it waits on, the report
    path. The figures are in the report and stay there.
    """
    state = load_state(state_path).get("refreshed", {})
    by_ticker = {e.ticker.upper(): e for e in entries}
    out: list[NeedsOwner] = []
    for ticker, record in sorted(state.items()):
        entry = by_ticker.get(ticker)
        if entry is None:
            continue
        waits = waits_for(entry, manual_dir=manual_dir, root=root)
        if record.get("waiting"):
            waits = (record["waiting"], *waits)
        if not waits:
            continue
        out.append(NeedsOwner(ticker=ticker,
                              report=str(record.get("report", "")),
                              waits=waits,
                              refreshed=str(record.get("date", ""))))
    return out


# --- the notification, outbound only --------------------------------------


def ntfy_url(topic: str | None = None) -> str | None:
    """The topic as a URL, or None when none is configured.

    A bare topic name is completed to ntfy.sh; a full URL is used as given,
    so a self-hosted server works without a second variable.
    """
    topic = topic or env.get(NTFY_ENV)
    if not topic:
        return None
    topic = topic.strip()
    if not topic:
        return None
    if topic.startswith(("http://", "https://")):
        return topic
    return f"{NTFY_DEFAULT_HOST}/{topic.lstrip('/')}"


def post_needs_owner(lines: Sequence[str], *, topic: str | None = None,
                     title: str | None = None,
                     opener: Callable | None = None) -> str:
    """POST the pointer. Silence when unset; NEVER raises, never blocks.

    E92: the notification is a convenience laid beside the report, and the
    report is the record. So every failure here -- no topic, a refused POST,
    a timeout, a DNS failure -- is logged and swallowed. A run that wrote its
    report has done its job.

    `title` overrides the notification title. The default names a count of
    names, which is right for the E92 pointer and wrong for anything that is
    not about names -- the dead man's switch, for one, which reports on the
    RUN and has no names in it at all.

    OUTBOUND ONLY. There is no read of this topic anywhere in the project.
    """
    if not lines:
        return "nothing to send"
    url = ntfy_url(topic)
    if url is None:
        log.info("%s is not set: no notification sent (E92: silence, not an "
                 "error)", NTFY_ENV)
        return f"not sent: {NTFY_ENV} is not set"
    body = "\n".join(lines).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Title": title or f"vss: {len(lines)} name(s) need you",
                 "Content-Type": "text/plain; charset=utf-8"})
    try:
        opener = opener or urllib.request.urlopen
        with opener(request, timeout=NTFY_TIMEOUT_SECONDS) as response:
            code = getattr(response, "status", None) or response.getcode()
        log.info("ntfy: sent %d line(s) (HTTP %s)", len(lines), code)
        return f"sent {len(lines)} line(s) (HTTP {code})"
    except Exception as exc:  # noqa: BLE001 -- logged, never raised (E92)
        log.warning("ntfy POST failed and the run continues: %s: %s",
                    type(exc).__name__, exc)
        return f"NOT SENT: {type(exc).__name__}: {exc}"


def notification_lines(items: Sequence[NeedsOwner], limit: int = 6) -> list[str]:
    """A few lines that read on a lock screen. Figures are allowed; length is not."""
    lines = [item.line().replace("`", "") for item in items[:limit]]
    if len(items) > limit:
        lines.append(f"...and {len(items) - limit} more — see tonight's report")
    return lines


# --- the command ----------------------------------------------------------


@dataclass
class RefreshResult:
    ticker: str
    route: str
    report_path: Path | None
    written: bool
    periods: list[str]
    conflicts: int
    manual_document: str = ""


def run_refresh(*, ticker: str | None = None, due: bool = False,
                dry_run: bool = False,
                watchlist_path: Path = WATCHLIST_PATH,
                manual_dir: Path | None = None,
                reports_dir: Path | None = None,
                state_path: Path = STATE_PATH,
                issuers_path: Path | None = None,
                now: datetime | None = None,
                fetcher: Callable | None = None) -> tuple[int, str]:
    """`vss refresh [TICKER|--due]`. Returns (exit_code, report_markdown)."""
    from .config import ConfigError, load_watchlist

    run_ts = now or datetime.now().astimezone()
    as_of = run_ts.date()
    manual_dir = manual_dir or MANUAL_DIR
    reports_dir = reports_dir or REPORTS_DIR

    entries = load_watchlist(watchlist_path)
    watchlist_before = Path(watchlist_path).read_bytes()

    if ticker:
        wanted = ticker.strip().upper()
        chosen = [e for e in entries if e.ticker.upper() == wanted]
        if not chosen:
            raise ConfigError(f"ticker {ticker} is not in {watchlist_path}")
        entry = chosen[0]
        catalyst = getattr(entry, "catalyst_date", None) or as_of
        frequency = getattr(entry, "reporting_frequency", "quarterly")
        expects = expected_period_end(catalyst, frequency)
        _, newest = store_covers(entry.ticker, expects, manual_dir=manual_dir)
        work = [Due(entry=entry, catalyst=catalyst, expects=expects,
                    newest_on_file=newest,
                    route=route_for(entry, issuers_path=issuers_path))]
    elif due:
        work = due_names(entries, as_of=as_of, manual_dir=manual_dir,
                         issuers_path=issuers_path)
    else:
        raise ConfigError("name a ticker or pass --due.")

    results: list[RefreshResult] = []
    out: list[str] = [f"# vss refresh — {as_of.isoformat()}", ""]
    if dry_run:
        out.append("> DRY RUN — nothing fetched, nothing written.")
        out.append("")
    if not work:
        out.append("Nothing is due: every name with a passed catalyst already "
                   "has that period in its store.")
        return 0, "\n".join(out) + "\n"

    out.append(f"{len(work)} name(s).")
    out.append("")
    out.append("| Ticker | Catalyst | Period | Route | Result |")
    out.append("|---|---|---|---|---|")

    for item in work:
        entry = item.entry
        store_path = Path(manual_dir) / f"{entry.ticker.upper()}.yaml"
        extraction: Extraction | None = None
        written: Path | None = None
        note = ""

        if item.route.manual is not None and not item.route.automatic:
            note = (f"**{item.route.manual.kind}** — "
                    f"{item.route.manual.document or 'report'} by hand")
        elif dry_run:
            note = "dry run: not fetched"
        elif item.route.kind == ROUTE_EDGAR:
            try:
                extraction = extract_edgar(entry, expects=item.expects,
                                           manual_dir=manual_dir,
                                           fetcher=fetcher)
            except Exception as exc:  # noqa: BLE001 -- reported, never fatal
                note = f"fetch failed: {type(exc).__name__}: {exc}"
                log.warning("%s refresh: %s", entry.ticker, note)
            else:
                if extraction.text and store_path.exists():
                    original = store_path.read_text(encoding="utf-8")
                    try:
                        text = validated_insert(original, extraction.text, store_path)
                    except RefreshError as exc:
                        note = str(exc)
                        log.error("%s refresh: %s", entry.ticker, note)
                    else:
                        store_path.write_text(text, encoding="utf-8")
                        written = store_path
                        note = (f"{len(extraction.periods_added)} period(s), "
                                f"{extraction.fields_added} figure(s)")
                else:
                    note = extraction.note or "nothing new"
        elif item.route.kind == ROUTE_NORDIC:
            note = ("on the Nordic feed — run `vss nordic --ticker "
                    f"{entry.ticker} --reports-only` to list, then "
                    "`--download` with the disclosure id and `--period`")

        report_path = None
        if not dry_run:
            report = render_refresh(entry=entry, due=item,
                                    extraction=extraction, as_of=as_of,
                                    run_ts=run_ts, written=written,
                                    store_path=store_path)
            reports_dir.mkdir(parents=True, exist_ok=True)
            report_path = reports_dir / f"REFRESH-{entry.ticker}-{as_of.isoformat()}.md"
            report_path.write_text(report, encoding="utf-8")
            waiting = ""
            if item.route.manual is not None and not item.route.automatic:
                waiting = (f"hand download: "
                           f"{item.route.manual.document or 'the report'}")
            record_refresh(entry.ticker, report=report_path, as_of=as_of,
                           route=item.route.kind,
                           periods=(extraction.periods_added
                                    if extraction else []),
                           conflicts=len(extraction.conflicts) if extraction else 0,
                           waiting=waiting, path=state_path)

        results.append(RefreshResult(
            ticker=entry.ticker, route=item.route.kind,
            report_path=report_path, written=written is not None,
            periods=extraction.periods_added if extraction else [],
            conflicts=len(extraction.conflicts) if extraction else 0,
            manual_document=(item.route.manual.document
                             if item.route.manual else "")))
        out.append(f"| `{entry.ticker}` | {item.catalyst.isoformat()} "
                   f"| {item.expects.isoformat()} | {item.route.kind} | {note} |")

    # E92, enforced and not merely intended.
    assert_no_watchlist_write(watchlist_before,
                              Path(watchlist_path).read_bytes())

    out.append("")
    for result in results:
        if result.report_path is not None:
            out.append(f"- `{result.ticker}` → `{result.report_path}`")
    out.append("")
    out.append("*E92: fetched, extracted, reported. No `fv_base`, `tier`, "
               "`mbp`, `stop_price` or `status` was written, and no gate was "
               "scored.*")
    return 0, "\n".join(out) + "\n"
