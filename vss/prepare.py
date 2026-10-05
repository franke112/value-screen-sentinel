"""`vss prepare` -- everything that can happen before the owner sits down.

Six steps, each independent: a failure in one is reported and the rest
run. Every step is an EXISTING path called by name; where no path exists
the report says so and nothing is invented here.

    1. ROUTE     refresh.route_for, readiness.route_for_ticker, the Oslo
                 registry (config/oslo_issuers.yaml).
    2. FETCH     the manifest the fetchers already keep (sources/manifest
                 .json); the Nordic / Oslo feed listing (nordic.fetch_
                 releases, oslo.fetch_releases) classified by watch.classify.
                 A Nordic download needs a MANUAL --period (the fetcher's
                 own rule), so nothing is downloaded unattended: the command
                 to run is printed.
    3. FILL      xbrl.run_xbrl_annual (creates a sec-xbrl store),
                 refresh.extract_edgar (appends new quarters), appendix
                 .run_appendix (an xlsx with a committed cell map),
                 earnings.run_earnings --compare (the LLM 4.2 extraction,
                 which PROPOSES a quarters: block and writes no store),
                 reference_figures.obtain (E103 reference figures,
                 UNVERIFIED, into the store).
    4. COMPUTE   rules.evaluate_hard_kills; runner.build_row (Gate 1 level
                 leg, frozen under E12 for a PIPELINE name; the staleness
                 and catalyst blockers); manual.gate_on_registered_view,
                 ratio_states, scale_jumps, share_basis_steps, staleness;
                 filters' three limbs on manual.as_record.
    5. VERIFY    the section-5 gate's own `blocking` (E21): the UNVERIFIED
                 figures the current basis reads.
    6. CONTEXT   the drawdown window's disclosures (watch.classify over
                 the feed, else the manifest by date); the one-offs the
                 extraction proposed with their sentences; the auditor's
                 section (NOT IMPLEMENTED: the manifest does not know it);
                 the circle (nothing -- it is the owner's).

IT NEVER WRITES fv_base, tier, mbp, stop_price or status. It never opens
config/watchlist.yaml for writing (refresh.assert_no_watchlist_write is
the mechanical guarantee). Every write to config/manual/ goes through a
path that backs the file up first. --dry-run writes nothing anywhere.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Sequence

from . import rules as R
from .config import ConfigError, WatchlistEntry, load_watchlist
from .refresh import (ROUTE_EDGAR, ROUTE_MANUAL, ROUTE_NORDIC, Route,
                      assert_no_watchlist_write, expected_period_end,
                      route_for, store_covers)
from .runner import CACHE_DIR, DB_PATH, PROJECT_ROOT, REPORTS_DIR, WATCHLIST_PATH

log = logging.getLogger(__name__)

PREPARE_DIR = REPORTS_DIR / "prepare"
SOURCES_DIR = PROJECT_ROOT / "sources"

#: Step outcomes.
OK = "ok"
REFUSED = "refused"          # the path ran and said no, in its own words
FAILED = "failed"            # the path raised; reported, the rest ran
NOT_BUILT = "no implementation"
SKIPPED = "skipped"          # nothing to do on this route
DRY = "dry run"

#: Outcomes of a computed check.
PASS, FAIL, MISSING = "PASS", "FAIL", "DATA MISSING"
#: The gate's own non-blocking observations (Section5Gate.flags). Printed,
#: never counted against the name.
FLAG = "FLAG (non-blocking)"
#: E123 (2026-09-20): a figure that is REPORTED AND DECIDES NOTHING -- no
#: threshold is attached to it and it can neither pass nor fail. E7's shape,
#: and E63's. The packet prints it; the score never reads it.
MEASURED = "MEASURED (no threshold)"

#: Which ruling decides each computed check. Metadata about the code's own
#: rules, not a judgement: the check itself is imported.
RULING_FOR = {
    "4.2.1": "FRAMEWORK §4.2.1; B9, E30 (organic basis), E45",
    "4.2.2": "FRAMEWORK §4.2.2; E9",
    "4.2.3": "FRAMEWORK §4.2.3",
    "4.2.4": "FRAMEWORK §4.2.4",
    "4.2.5": "FRAMEWORK §4.2.5",
    "4.2.6": "FRAMEWORK §4.2.6",
    "4.2.7": "FRAMEWORK §4.2.7; B7, B10",
    "4.3": "FRAMEWORK §4.3 (soft flag)",
    "gate-1": "FRAMEWORK §3 Gate 1; B2 (inclusive band), E12 (frozen for PIPELINE), E11",
    "staleness-price": "FRAMEWORK §1.2 as amended; C3, E47",
    "catalyst": "FRAMEWORK §3 Gate 5",
    "store-staleness": "FRAMEWORK §1.2; manual.staleness (fundamentals.MAX_REPORT_AGE_DAYS)",
    "basis": "E19, E20, E31 (one twelve-month window)",
    "unit-mix": "E19; B38 (a file in one unit)",
    "gate-3-leverage": "FRAMEWORK §3 Gate 3; E44 (2.5× at filter 2), E112 (numerator)",
    "gate-3-revenue": "FRAMEWORK §4.2.1 at filter 2; E45",
    "gate-3-fcf": "FRAMEWORK §3 Gate 3 (FCF positive); E4 (no data passes through)",
    "coverage": "FRAMEWORK §3 Gate 3 (interest coverage ≥ 5×); E16, E18, E20, E112, E126",
    "conviction": "FRAMEWORK §4.4; E99 (Gate 4), E123 (the cash limbs), E126 (coverage, and the tier hold)",
    "net-debt": "E14, E35, E35.1, E65, E68, E81 (the legs of net debt)",
    "fcf0": "E23, E33, E34, E36, E70, E105 (the legs of FCF0)",
    "zero-basis": "E25, E78, E85, E107 (a zero is a claim)",
    "share-count": "E22, E38, E53, E54, E75, E88, E91 (the divisor)",
    "share-basis": "B36; manual.share_basis_steps (a ≥2× step in a per-share figure)",
    "scale-jump": "B38; manual.scale_jumps (a ≥1000× step in one leg)",
    "interest-net": "E16, E18, E34, E34.1, E61 (the finance nets)",
    "gate-refusal": "E21 (the §5 gate), E103, E106, E108",
    "op-margin": "FRAMEWORK §4.2.2 check; E79, E83 (the stated margin)",
    "fcf-conversion": "E101, E103 (the issuer's own free cash flow as a reference figure)",
    "profitability": "E43 (the ranking key's quality leg, EBIT / total assets)",
}


@dataclass
class Step:
    name: str
    status: str = OK
    lines: list[str] = field(default_factory=list)
    reused: list[str] = field(default_factory=list)   # the existing paths called
    data: dict = field(default_factory=dict)

    def note(self, text: str) -> None:
        self.lines.append(text)


@dataclass
class Check:
    name: str
    outcome: str          # PASS | FAIL | DATA MISSING
    detail: str
    ruling: str


@dataclass
class Verification:
    order: int
    field: str
    period: str
    value: float | None
    document: str
    page: str
    status: str


@dataclass
class Prepared:
    ticker: str
    name: str
    status: str
    as_of: str
    dry_run: bool
    summary: str = ""
    blocked_on: int = 0
    steps: list[Step] = field(default_factory=list)
    documents: list[dict] = field(default_factory=list)
    filled: list[dict] = field(default_factory=list)
    data_missing: list[dict] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    verification: list[Verification] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    refused: list[str] = field(default_factory=list)
    llm_calls: int = 0
    llm_calls_earnings: int = 0
    llm_calls_reference: int = 0
    written: list[str] = field(default_factory=list)
    report_md: str | None = None
    report_json: str | None = None

    def step(self, name: str) -> Step:
        s = Step(name)
        self.steps.append(s)
        return s


class CountingTransport:
    """Wraps the LLM transport so the report can say how many calls it cost."""

    def __init__(self, inner: Callable | None):
        import urllib.request
        self.inner = inner or urllib.request.urlopen
        self.calls = 0

    def __call__(self, request, timeout=None):
        self.calls += 1
        return self.inner(request, timeout=timeout)


# --------------------------------------------------------------------- 0 stands

#: Which playbook step a watchlist status sits at (tools/playbook/steps.py
#: holds the screens; this is the same table, so the report can name the
#: step without importing the site generator into the tool).
STATUS_STEP = {"HELD": "held", "WATCH-PRICED": "watch-priced", "WATCH-GATED": "watch-gated",
               "PIPELINE": "pipeline", "INTAKE": "intake", "DROPPED": "dropped"}
VERDICT_STATUSES = ("HELD", "WATCH-PRICED", "WATCH-GATED", "DROPPED")


def _readings(docs, root: Path) -> list[dict]:
    """The text of every document of kind `reading`, for the report (C1)."""
    out = []
    for d in docs:
        if d.kind != "reading":
            continue
        path = (root / "reports" / d.href).resolve()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            text = f"(could not be read: {exc})"
        out.append({"label": d.label, "path": str(path.relative_to(root.resolve()))
                    if path.is_relative_to(root.resolve()) else str(path), "text": text})
    return out


def step_stands(entry: WatchlistEntry, out: Prepared, *, root: Path, views_dir: Path | None) -> None:
    """Where the name already is in the review, from the record on disk.

    RATES ONLY IF REGISTERED. The anchoring guard: a growth view's rates
    are shown only when the entry's own `growth:` block carries a
    `registered` date; otherwise the date's absence is what is shown.
    """
    step = out.step("stands")
    g = getattr(entry, "growth", None)
    registered = getattr(g, "registered", None) if g else None
    view_line = "no growth view registered on the watchlist entry (E109)"
    if registered:
        view_line = (f"growth view registered {registered.isoformat()}: g_base {g.base:.1%}, "
                     f"g_bear {g.bear:.1%}, g_bull {g.bull:.1%} ({g.view})")
    else:
        try:
            from .readiness import read_growth_view
            v = read_growth_view(entry.ticker, directory=views_dir)
            if v is not None:
                view_line += (f"; reference/growth-views/{entry.ticker}.md exists ({v.state}) "
                              f"-- rates not shown until the entry carries a registered date")
        except Exception:  # noqa: BLE001
            pass
    step.reused.append("readiness.read_growth_view")
    record = getattr(entry, "run_record", None)
    record_path = (root / record) if record else None
    struck = None
    if record_path is not None and record_path.exists():
        import re
        m = re.search(r"(\d{4}-\d{2}-\d{2})", record_path.name)
        struck = m.group(1) if m else None
    fv_line = (f"fv_base {entry.fv_base} on the entry" if entry.fv_base is not None
               else "no fv_base on the entry")
    rr_line = (f"run record {record} ({'on disk' if record_path and record_path.exists() else 'NOT on disk'})"
               if record else "no run record named on the entry")
    tier_line = f"tier {entry.tier}" if entry.tier is not None else "no tier"
    try:
        from .overview import documents
        docs = documents(entry.ticker, root=root)
        step.reused.append("overview.documents")
    except Exception:  # noqa: BLE001
        docs = ()
    reviews_dir = root / "reference" / "reviews"
    # `vss review` keeps one file per session at reviews/<TICKER>/<date>.yaml
    reviews = (sorted(f"{entry.ticker}/{p.name}" for p in (reviews_dir / entry.ticker).glob("*.yaml"))
               if reviews_dir.is_dir() else None)
    step_id = STATUS_STEP.get(entry.status, "verdict")
    inconsistent = entry.fv_base is not None and entry.status == "PIPELINE"
    resume = None
    if struck or entry.fv_base is not None:
        resume = "verdict" if entry.tier is not None else "tier-mbp"
    stands = {
        "status": entry.status, "playbook_step": step_id, "growth_view": view_line,
        "fv_base": fv_line, "tier": tier_line, "run_record": rr_line, "struck": struck,
        "verdict_recorded": entry.status in VERDICT_STATUSES,
        "reviews": reviews if reviews is not None else "reference/reviews/ does not exist",
        "documents": [{"kind": d.kind, "label": d.label, "href": d.href} for d in docs],
        "inconsistent_e27": inconsistent, "resume_at": resume,
        # C1 (owner, 2026-09-19): the entry's own words and every linked
        # READING, IN FULL -- a link alone let the 2026-08-31 CTSH reading
        # go unread before a verdict.
        "notes": getattr(entry, "notes", None) or "",
        "readings": _readings(docs, root),
    }
    out.context["stands"] = stands
    step.note(f"status {entry.status} — playbook step `{step_id}`")
    step.note(view_line)
    step.note(f"{fv_line}; {tier_line}; {rr_line}")
    step.note("reviews under reference/reviews/: " + (", ".join(reviews) if reviews else
              ("none naming this ticker" if reviews is not None else "the directory does not exist")))
    step.note(f"{len(docs)} document(s) naming the ticker: " + ", ".join(f"{d.kind} {d.label}" for d in docs))
    if inconsistent:
        step.note("INCONSISTENT WITH E27: fv_base is set but the status is PIPELINE. A name that "
                  "has been through section 5 is WATCH-PRICED, WATCH-GATED, HELD or DROPPED; "
                  "PIPELINE is review work before the strike.")
    if resume:
        step.note(f"already struck{(' ' + struck) if struck else ''}; "
                  + ("verdict not recorded" if not stands["verdict_recorded"] else f"verdict {entry.status}")
                  + f" -- resume at `{resume}`")


# --------------------------------------------------------------------- 1 route

def step_route(entry: WatchlistEntry, out: Prepared, *, issuers_path, oslo_issuers_path) -> Route:
    step = out.step("route")
    route = route_for(entry, issuers_path=issuers_path)
    step.reused.append("refresh.route_for")
    step.note(f"refresh.route_for: **{route.kind}** — {route.detail}")
    if route.manual is not None:
        step.note(f"beside it, {route.manual.kind}: {route.manual.reason}"
                  + (f" — {route.manual.document}" if route.manual.document else "")
                  + (f" — {route.manual.url}" if route.manual.url else ""))
    try:
        from .readiness import route_for_ticker
        origin = None
        try:
            from .manual import load_manual
            origin = load_manual(entry.ticker, directory=out.context.get("_manual_dir")).origin
        except Exception:  # noqa: BLE001 -- no store is a fact for step 3
            pass
        kind, why = route_for_ticker(entry.ticker, cik=entry.cik, store_origin=origin)
        step.reused.append("readiness.route_for_ticker")
        step.note(f"readiness.route_for_ticker: {kind} — {why}")
    except Exception as exc:  # noqa: BLE001
        step.note(f"readiness.route_for_ticker did not answer: {type(exc).__name__}: {exc}")
    # The Oslo registry, which refresh.route_for does not consult. Where
    # the two disagree both are shown; nothing here picks.
    if entry.ticker.upper().endswith(".OL"):
        try:
            from .oslo import issuer_for as oslo_issuer_for
            issuer = oslo_issuer_for(entry.ticker, path=oslo_issuers_path)
            step.reused.append("oslo.issuer_for")
            step.note(f"config/oslo_issuers.yaml lists the issuer (sign {issuer.sign}); "
                      f"`vss nordic --ticker {entry.ticker}` dispatches to NewsWeb "
                      f"(vss/oslo.py). refresh.route_for does not consult this "
                      f"registry: the two answers are shown, not reconciled.")
            step.data["oslo"] = True
        except Exception as exc:  # noqa: BLE001
            step.note(f"not in config/oslo_issuers.yaml: {exc}")
    if entry.ticker.upper().endswith(".L"):
        step.note("UK NSM: NOT IMPLEMENTED. No module fetches from the National "
                  "Storage Mechanism; documents for a London listing reach "
                  "sources/ by hand.")
    step.data["route"] = route.kind
    return route


# --------------------------------------------------------------------- 2 fetch

def _manifest_documents(ticker: str, sources_root: Path) -> list[dict]:
    from .nordic import load_manifest
    try:
        document = load_manifest(sources_root)
    except Exception:  # noqa: BLE001
        return []
    out = []
    for rec in document.get("downloads", []):
        if str(rec.get("ticker", "")).upper() != ticker.upper():
            continue
        out.append({
            "file": rec.get("file"),
            "type": rec.get("form") or rec.get("category") or rec.get("content_type") or "",
            "period": rec.get("period") or "",
            "date": rec.get("filed") or rec.get("released", "")[:10] or rec.get("document_date") or "",
            "origin": rec.get("origin") or "",
            "figures_read": rec.get("figures_read"),
            "url": rec.get("url") or "",
        })
    return sorted(out, key=lambda d: (d["date"], d["file"] or ""), reverse=True)


def step_fetch(entry: WatchlistEntry, route: Route, out: Prepared, *, sources_root: Path,
               issuers_path, oslo_issuers_path, opener, as_of: date, dry_run: bool) -> None:
    step = out.step("fetch")
    out.documents = _manifest_documents(entry.ticker, sources_root)
    step.reused.append("nordic.load_manifest")
    step.note(f"{len(out.documents)} document(s) in {sources_root.name}/manifest.json for "
              f"{entry.ticker}, listed under Documents.")
    releases = []
    if route.kind == ROUTE_NORDIC or out.steps[1].data.get("oslo"):
        if dry_run:
            step.status = DRY
            step.note("dry run: the disclosure feed is not queried.")
        else:
            try:
                if out.steps[1].data.get("oslo"):
                    from .oslo import fetch_releases as oslo_fetch, issuer_for as oslo_issuer_for
                    issuer = oslo_issuer_for(entry.ticker, path=oslo_issuers_path)
                    releases, truncated = oslo_fetch(issuer, since=as_of - timedelta(days=400),
                                                     until=as_of, opener=opener)
                    step.reused.append("oslo.fetch_releases")
                else:
                    from .nordic import fetch_releases, issuer_for
                    issuer = issuer_for(entry.ticker, path=issuers_path)
                    releases, _count = fetch_releases(issuer, language=issuer.language,
                                                      opener=opener)
                    step.reused.append("nordic.fetch_releases")
            except Exception as exc:  # noqa: BLE001
                step.status = FAILED
                step.note(f"the feed did not answer: {type(exc).__name__}: {exc}")
        if releases:
            from .watch import classify
            step.reused.append("watch.classify")
            have = {(d.get("file") or "") for d in out.documents}
            ids_on_file = set()
            from .nordic import load_manifest
            try:
                for rec in load_manifest(sources_root).get("downloads", []):
                    if str(rec.get("ticker", "")).upper() == entry.ticker.upper():
                        ids_on_file.add(rec.get("disclosure_id"))
            except Exception:  # noqa: BLE001
                pass
            reports = [r for r in releases if classify(r, entry.ticker).passes and r.attachments]
            step.data["releases"] = [
                {"id": r.disclosure_id, "released": r.released_date, "category": r.category,
                 "headline": r.headline, "on_file": r.disclosure_id in ids_on_file}
                for r in reports]
            step.note(f"{len(reports)} report-category or guidance disclosure(s) with a file on the feed; "
                      f"{sum(1 for r in reports if r.disclosure_id in ids_on_file)} already in the manifest.")
            horizon = (as_of - timedelta(days=400)).isoformat()
            older = 0
            for r in reports:
                if r.disclosure_id in ids_on_file:
                    continue
                if r.released_date < horizon:
                    older += 1
                    continue
                step.note(f"NOT FETCHED — the period is MANUAL (the fetcher's own rule): "
                          f"`python -m vss nordic --ticker {entry.ticker} --download "
                          f"{r.disclosure_id} --period YYYY-Qn`  ({r.released_date}, "
                          f"{r.category}: {r.headline})")
            if older:
                step.note(f"{older} older report(s) on the feed, released before {horizon}, not listed; "
                          f"`python -m vss nordic --ticker {entry.ticker} --reports` shows them.")
            del have
    elif route.kind == ROUTE_EDGAR:
        step.note("SEC XBRL: the tagged facts are fetched by the fill step "
                  "(xbrl.run_xbrl_annual / refresh.extract_edgar); the filed "
                  "documents reach the manifest through reference_figures' EDGAR "
                  "route when a reference figure is wanted.")
    else:
        step.status = SKIPPED
        if route.manual is not None:
            step.note(f"manual route: {route.manual.document or 'the issuer report'}"
                      + (f" at {route.manual.url}" if route.manual.url else "")
                      + " — nothing is fetched by a machine.")


# --------------------------------------------------------------------- 3 fill

def _read_verified_count(ticker: str, manual_dir: Path) -> int:
    from .manual import KIND_TAGGED, load_manual
    try:
        parsed = load_manual(ticker, directory=manual_dir)
    except Exception:  # noqa: BLE001
        return 0
    return sum(1 for f in parsed.all_figures()
               if f.present and f.verified and f.verified_kind != KIND_TAGGED)


def _xlsx_for(ticker: str, sources_root: Path) -> Path | None:
    if not sources_root.is_dir():
        return None
    found = sorted(sources_root.glob(f"{ticker}_*.xlsx"))
    return found[-1] if found else None


def _newest_report_document(ticker: str, sources_root: Path, documents: Sequence[dict]) -> tuple[Path | None, str]:
    for d in documents:
        name = d.get("file") or ""
        if name.lower().endswith((".pdf", ".html", ".htm")) and (sources_root / name).exists():
            return sources_root / name, d.get("period") or ""
    return None, ""


def step_fill(entry: WatchlistEntry, route: Route, out: Prepared, *, manual_dir: Path,
              sources_root: Path, maps_dir: Path, watchlist_path: Path, db_path: Path,
              dry_run: bool, force: bool, now: datetime, fetcher, transport, reader, opener) -> None:
    step = out.step("fill")
    store = manual_dir / f"{entry.ticker.upper()}.yaml"
    exists = store.exists()
    counting = CountingTransport(transport)

    if exists and force and not dry_run:
        discarded = _read_verified_count(entry.ticker, manual_dir)
        step.note(f"--force: {store.name} is backed up first; {discarded} figure(s) "
                  f"VERIFIED by a reading will be DISCARDED by a re-fill.")

    # --- the store: SEC XBRL --------------------------------------------
    if route.kind == ROUTE_EDGAR:
        from .xbrl import run_xbrl_annual
        if not exists or force:
            if dry_run:
                step.status = DRY
                step.note("dry run: xbrl.run_xbrl_annual would " + ("create" if not exists else "re-fill") + f" {store.name}; not run.")
            else:
                try:
                    code, report = run_xbrl_annual(
                        ticker=entry.ticker, cik=entry.cik, watchlist_path=watchlist_path,
                        db_path=db_path, manual_dir=manual_dir, write=True, force=force,
                        now=now, fetcher=fetcher)
                    step.reused.append("xbrl.run_xbrl_annual")
                    step.note(f"xbrl.run_xbrl_annual exit {code}: "
                              f"{'wrote' if store.exists() else 'did not write'} {store.name}")
                    if store.exists():
                        out.written.append(str(store))
                    if code != 0:
                        step.status = REFUSED
                        out.refused.append("xbrl.run_xbrl_annual: " + _first_refusal(report))
                except Exception as exc:  # noqa: BLE001
                    step.status = FAILED
                    step.note(f"xbrl.run_xbrl_annual raised {type(exc).__name__}: {exc}")
        else:
            step.note(f"{store.name} is on file; not re-filled (pass --force). "
                      f"New quarters are appended by refresh.extract_edgar:")
            try:
                from .refresh import extract_edgar
                catalyst = getattr(entry, "catalyst_date", None) or now.date()
                expects = expected_period_end(catalyst, getattr(entry, "reporting_frequency", "quarterly"))
                extraction = extract_edgar(entry, expects=expects, manual_dir=manual_dir, fetcher=fetcher)
                step.reused.append("refresh.extract_edgar")
                if extraction.text and not dry_run:
                    import shutil
                    from .xbrl import backup_name
                    original = store.read_text(encoding="utf-8")
                    # THE STORE'S OWN VALIDATION, BEFORE THE WRITE LANDS. A
                    # block the loader refuses is reported and not written.
                    from .refresh import RefreshError, validated_insert
                    try:
                        text = validated_insert(original, extraction.text, store)
                    except RefreshError as exc:
                        step.status = REFUSED
                        out.refused.append(f"refresh.validated_insert: {exc}")
                        step.note(str(exc))
                    else:
                        backup = backup_name(store, now)
                        shutil.copy2(store, backup)
                        store.write_text(text, encoding="utf-8")
                        out.written.append(str(store))
                        step.note(f"appended {len(extraction.periods_added)} period(s), "
                                  f"{extraction.fields_added} figure(s) (backup {backup.name})")
                if extraction.missing_concepts:
                    step.note("not written (no field in the store's schema, or not tagged): "
                              + "; ".join(extraction.missing_concepts[:8]))
                elif extraction.text:
                    step.status = DRY
                    step.note(f"dry run: {len(extraction.periods_added)} period(s) would be appended; nothing written.")
                else:
                    step.note(extraction.note or "nothing new")
                for c in extraction.conflicts:
                    step.note(f"conflict, store kept: {c.period} {c.field} held {c.held} "
                              f"({c.held_status}) vs fetched {c.fetched}")
            except Exception as exc:  # noqa: BLE001
                step.status = FAILED
                step.note(f"refresh.extract_edgar raised {type(exc).__name__}: {exc}")

    # --- the store: an xlsx appendix with a committed cell map ----------
    workbook = _xlsx_for(entry.ticker.upper(), sources_root)
    has_map = (maps_dir / f"{entry.ticker.upper()}.yaml").exists()
    if route.kind != ROUTE_EDGAR:
        if has_map and workbook is not None:
            from .appendix import run_appendix
            write = (not exists or force) and not dry_run
            try:
                code, report = run_appendix(ticker=entry.ticker, workbook=workbook, write=write,
                                            force=force, maps_dir=maps_dir, manual_dir=manual_dir,
                                            as_of=now.date())
                step.reused.append("appendix.run_appendix")
                if write and store.exists():
                    out.written.append(str(store))
                step.note(f"appendix.run_appendix on {workbook.name}: exit {code}; "
                          + ("wrote " + store.name if write and code == 0 else
                             ("dry run: not written" if dry_run else
                              (f"{store.name} on file; not re-filled (pass --force)" if exists
                               else "not written"))))
                if code != 0:
                    step.status = REFUSED
                    out.refused.append("appendix.run_appendix: " + _first_refusal(report))
            except Exception as exc:  # noqa: BLE001
                step.status = FAILED
                step.note(f"appendix.run_appendix raised {type(exc).__name__}: {exc}")
        elif has_map:
            step.note(f"a cell map exists (config/manual/maps/{entry.ticker}.yaml) but no "
                      f"{entry.ticker}_*.xlsx is under sources/; nothing to fill from.")
        else:
            step.note("no xlsx cell map for this ticker; the appendix path does not apply.")

    # --- the LLM: the earnings path, --compare, on the newest report -----
    document, period = _newest_report_document(entry.ticker.upper(), sources_root, out.documents)
    if route.kind == ROUTE_EDGAR:
        step.note("LLM extraction SKIPPED on the sec-xbrl route: the tagged facts are the "
                  "figures, and the filed .htm is inline XBRL whose text is not a press "
                  "release. On 2026-09-13 the 10-K through the earnings path produced two "
                  "readings of noise; the route does not read it.")
        document = None
    if document is None and route.kind == ROUTE_EDGAR:
        pass
    elif document is None:
        step.note("no report document (pdf/html) for this ticker under sources/, so the "
                  "earnings extraction has nothing to read.")
    else:
        target_period = period if R.period_parts(period) is not None else None
        held = {q.period for q in (entry.quarters or ())}
        if target_period and target_period in held and not force:
            step.note(f"{target_period} is already in the watchlist's quarters: block; "
                      f"not re-extracted (pass --force).")
        elif dry_run:
            step.status = DRY if step.status == OK else step.status
            step.note(f"dry run: earnings.run_earnings --compare would read {document.name}; not run.")
        else:
            from .earnings import run_earnings
            captured: dict = {}

            def keep(extraction, quarter):
                captured["extraction"] = extraction
                captured["quarter"] = quarter
            try:
                code, alert = run_earnings(
                    ticker=entry.ticker, text_file=str(document), shadow=True, compare=True,
                    target_period=target_period, watchlist_path=watchlist_path, db_path=db_path,
                    now=now, transport=counting, on_extraction=keep)
                step.reused.append("earnings.run_earnings (--compare)")
                step.data["earnings_alert"] = alert
                step.note(f"earnings.run_earnings --compare on {document.name}: exit {code}. "
                          f"The path PROPOSES a quarters: block for the watchlist and writes no "
                          f"store: no existing path writes LLM-read figures into "
                          f"config/manual/ for the section-5 legs.")
                ex = captured.get("extraction")
                if ex is not None:
                    for name, value in sorted(ex.figures.items()):
                        entry_ = {"field": name, "period": captured["quarter"].period,
                                  "value": value, "origin": f"LLM extraction ({ex.model}), --compare",
                                  "status": "PROPOSED (never a store figure)",
                                  "sentence": ex.sentences.get(name)}
                        (out.filled if value is not None else out.data_missing).append(
                            entry_ if value is not None else
                            {"field": name, "period": captured["quarter"].period,
                             "reason": ("the two readings disagreed" if name in ex.disagreements
                                        else "not stated in the document, or unevidenced")})
                    out.context["one_offs"] = {
                        "class_c_impact": ex.figures.get("class_c_impact"),
                        "sentence": ex.sentences.get("class_c_impact"),
                        "disagreement": ex.disagreements.get("class_c_impact"),
                    }
            except Exception as exc:  # noqa: BLE001
                step.status = FAILED
                step.note(f"earnings.run_earnings raised {type(exc).__name__}: {exc}")

    # --- E103 reference figures, UNVERIFIED, into the store ---------------
    if store.exists():
        try:
            from .reference_figures import obtain, read_document, write_proposals
            read_count = {"n": 0}
            inner_reader = reader or read_document

            def counted_reader(path, **kw):
                read_count["n"] += 1
                return inner_reader(path, **kw)
            plan_, proposals = obtain(entry.ticker.upper(), manual_dir=manual_dir,
                                      sources_root=sources_root, cik=entry.cik,
                                      reader=counted_reader if not dry_run else _refuse_reader,
                                      opener=opener)
            step.reused.append("reference_figures.obtain")
            out.llm_calls_reference = read_count["n"]
            obtained = [p for p in proposals if p.obtained]
            if plan_.complete:
                step.note("reference figures (E103): the store already holds every one the basis wants.")
            elif dry_run:
                step.status = DRY if step.status == OK else step.status
                step.note(f"dry run: reference_figures.obtain wants {sum(len(v) for v in plan_.wanted.values())} figure(s); nothing read or written.")
            else:
                step.note(f"reference_figures.obtain: {len(obtained)} obtained, "
                          f"{len(proposals) - len(obtained)} not; route {plan_.route}.")
                if obtained:
                    # write_proposals never overwrites a held figure, and it
                    # does not back the file up; this command's rule is that
                    # every write to config/manual/ is preceded by a backup.
                    import shutil
                    from .xbrl import backup_name
                    backup = backup_name(store, now)
                    shutil.copy2(store, backup)
                    step.note(f"backup {backup.name} taken before reference figures are written")
                    written = write_proposals(entry.ticker.upper(), obtained, manual_dir=manual_dir)
                    step.reused.append("reference_figures.write_proposals")
                    out.written.append(str(store))
                    step.note(f"wrote {len(obtained)} UNVERIFIED reference figure(s) into {store.name}: {written}")
                for p in proposals:
                    if p.obtained:
                        out.filled.append({"field": p.field, "period": p.period, "value": p.value,
                                           "origin": f"E103 reference figure via {p.route}: {p.page}",
                                           "status": "UNVERIFIED", "sentence": p.quote})
                    else:
                        out.data_missing.append({"field": p.field, "period": p.period, "reason": p.detail})
        except Exception as exc:  # noqa: BLE001
            step.note(f"reference_figures.obtain raised {type(exc).__name__}: {exc}")
    out.llm_calls_earnings = counting.calls
    out.llm_calls = out.llm_calls_earnings + out.llm_calls_reference
    step.note(f"LLM calls made: {out.llm_calls} (earnings extraction {out.llm_calls_earnings}, "
              f"E103 reference figures {out.llm_calls_reference})")


def _refuse_reader(path, **kw):
    from .reference_figures import ReferenceError
    raise ReferenceError("dry run: no document is read")


def _first_refusal(report: str) -> str:
    for line in report.splitlines():
        if "REFUSED" in line or "NOT WRITTEN" in line or "does not load" in line.lower():
            return line.strip("# ").strip()[:200]
    return (report.strip().splitlines() or ["(no text)"])[-1][:200]


# --------------------------------------------------------------------- 4 compute

def _state(kill: R.KillResult) -> str:
    return {R.TRIP: FAIL, R.NO_TRIP: PASS}.get(kill.state, MISSING)


def step_compute(entry: WatchlistEntry, out: Prepared, *, manual_dir: Path, cache_dir: Path,
                 now: datetime, as_of: date) -> None:
    step = out.step("compute")
    # 4a. hard kills on the owner's own quarters: block
    try:
        from .manual import kill_leverage_reading
        results = R.evaluate_hard_kills(
            entry.quarters, entry.exec_changes, as_of, entry.reporting_frequency,
            derived_leverage=kill_leverage_reading(entry.ticker, directory=manual_dir))
        step.reused += ["rules.evaluate_hard_kills", "manual.gate3_leverage (E119)"]
        for k in results:
            out.checks.append(Check(f"{k.rule} {k.name}", _state(k), k.detail,
                                    RULING_FOR.get(k.rule, RULING_FOR["4.3"] if k.rule.startswith("4.3") else "FRAMEWORK §4.2")))
        step.note(f"hard kills on {len(entry.quarters or ())} stored period(s): "
                  f"{sum(1 for k in results if k.tripped)} trip(s), "
                  f"{sum(1 for k in results if k.uncertain)} cannot evaluate.")
    except Exception as exc:  # noqa: BLE001
        step.note(f"rules.evaluate_hard_kills raised {type(exc).__name__}: {exc}")

    # 4b. Gate 1 level leg, staleness and catalyst: the nightly's own row
    try:
        from .fetch import get_history
        from .metrics import settled_through
        from .runner import build_row
        fetched = get_history(entry.ticker, cache_dir, now=now, allow_network=False, write=False)
        # The nightly's own judgement, exchange calendar included, so the
        # prepare report and the report never disagree about a block.
        from .calendars import load_market_calendars
        try:
            calendars = load_market_calendars()
        except Exception:  # noqa: BLE001 -- Monday-Friday count, and it says so
            calendars = None
        row = build_row(entry, fetched, as_of, settled_through(now),
                        calendars=calendars, use_calendar=True)
        step.reused += ["fetch.get_history (cache only)", "runner.build_row", "rules.assess"]
        frozen = R.frozen_gate_1(entry.status, entry.dd_at_entry, entry.peak_date)
        outside = [v for v in row.assessment.verdicts if v.code in (R.OUTSIDE_BAND, R.DATA_MISSING)
                   and "dislocation" in v.detail.lower()]
        if frozen:
            # E12: the frozen reading is on the entry and needs no price.
            today = (f"; today's drawdown {row.metrics.drawdown:.1%}" if row.metrics.drawdown is not None
                     else "; no cached price series for today's reading")
            out.checks.append(Check("Gate 1 level leg (frozen, E12)",
                                    PASS if R.in_dislocation_band(entry.dd_at_entry) else FAIL,
                                    f"dd_at_entry {entry.dd_at_entry:.1%} on {entry.peak_date}{today}",
                                    RULING_FOR["gate-1"]))
        elif fetched.frame is None:
            out.checks.append(Check("Gate 1 level leg", MISSING,
                                    f"no cached price series ({fetched.error or 'no cache'}); the nightly run fetches it",
                                    RULING_FOR["gate-1"]))
        else:
            dd = row.metrics.drawdown
            inside = R.in_dislocation_band(dd)
            out.checks.append(Check("Gate 1 level leg (today)",
                                    MISSING if inside is None else (PASS if inside else FAIL),
                                    (f"drawdown {dd:.1%} from the 52-week high" if dd is not None else "drawdown not computable")
                                    + (f"; {outside[0].detail}" if outside else ""),
                                    RULING_FOR["gate-1"]))
        for b in row.assessment.blockers:
            # `Blocker` carries `code` and `reason` -- never `label` or
            # `detail` (2026-09-20: the same misread that crashed the
            # overview page, found by grepping every blocker read).
            key = "staleness-price" if b.code == R.STALE_DATA else ("catalyst" if "catalyst" in b.reason.lower() else "gate-1")
            out.checks.append(Check(f"blocker {b.code}", FAIL, b.reason, RULING_FOR.get(key, "")))
        out.context["price"] = {"last_close": row.metrics.last_close,
                                "retained": (row.retained.line() if row.retained else None),
                                "last_close_date": row.metrics.last_close_date.isoformat() if row.metrics.last_close_date else None,
                                "high_52w_date": row.metrics.high_52w_date.isoformat() if row.metrics.high_52w_date else None,
                                "drawdown": row.metrics.drawdown}
    except Exception as exc:  # noqa: BLE001
        step.note(f"runner.build_row raised {type(exc).__name__}: {exc}")

    # 4c. the store: basis, staleness, unit mix, Gate 3 legs, zero_basis, share count, nets
    try:
        from .manual import (gate_on_registered_view, load_manual, ratio_states, scale_jumps,
                             section5_basis, share_basis_steps, share_divisor_on_basis, staleness)
        parsed = load_manual(entry.ticker, directory=manual_dir)
    except Exception as exc:  # noqa: BLE001
        out.checks.append(Check("store", MISSING, f"config/manual/{entry.ticker.upper()}.yaml: {type(exc).__name__}: {exc}", RULING_FOR["basis"]))
        step.note("no store loads; the store checks did not run.")
        return
    step.reused += ["manual.load_manual", "manual.section5_basis", "manual.gate_on_registered_view",
                    "manual.ratio_states", "manual.scale_jumps", "manual.share_basis_steps", "manual.staleness"]
    basis = section5_basis(parsed)
    out.checks.append(Check("period basis (E19)", PASS if basis else MISSING,
                            basis.label if basis else "no twelve-month window: fewer than four consecutive quarters and no annual entry",
                            RULING_FOR["basis"]))
    status, detail = staleness(parsed, as_of=as_of)
    if parsed.newest_period_end is None:
        out.checks.append(Check("store staleness", MISSING,
                                "no periods: entry -- manual.staleness judges periods only, so an "
                                "annual-only store is not aged by it (B39)", RULING_FOR["store-staleness"]))
    else:
        out.checks.append(Check("store staleness", PASS if detail is None else FAIL,
                                detail or f"newest period {parsed.newest_period_end}", RULING_FOR["store-staleness"]))
    gate = gate_on_registered_view(parsed, as_of=as_of)
    out.context["_gate"] = gate
    for r in gate.refusals:
        key = {"UNIT MIX": "unit-mix", "STALE": "store-staleness", "INTEREST UNCLASSIFIED": "interest-net",
               "LEASES UNCLASSIFIED": "fcf0", "NO TWELVE-MONTH BASIS": "basis"}.get(r.kind, "gate-refusal")
        out.checks.append(Check(f"§5 gate: {r.kind}", FAIL if r.kind != "UNVERIFIED" else MISSING,
                                f"{r.subject}: {r.detail}", RULING_FOR[key]))
    if not gate.refusals:
        out.checks.append(Check("§5 gate", PASS, f"may run on {gate.basis.label if gate.basis else '?'}", RULING_FOR["gate-refusal"]))
    for rs in ratio_states(parsed, basis):
        out.checks.append(Check(f"leg: {rs.name}", PASS if rs.computable else MISSING, rs.detail,
                                RULING_FOR[_ratio_key(rs.name)]))
    for j in scale_jumps(parsed):
        out.checks.append(Check(f"unit mix: {j.field}", FAIL, f"{j.low_label} {j.low:,.0f} → {j.high_label} {j.high:,.0f} ({j.factor:,.0f}×)", RULING_FOR["scale-jump"]))
    for j in share_basis_steps(parsed):
        # A quarter's per-share figure beside a year's is a ≥2x step that
        # is not a split; the gate itself lists these as flags, not
        # refusals, and so does this.
        out.checks.append(Check(f"share basis: {j.field}", FLAG, f"{j.low_label} {j.low:,.2f} → {j.high_label} {j.high:,.2f} ({j.factor:.1f}×)", RULING_FOR["share-basis"]))
    if basis is not None:
        try:
            divisor = share_divisor_on_basis(parsed, basis)
            out.checks.append(Check("share count (divisor)", PASS if divisor.count else MISSING,
                                    f"{divisor.divisor_basis or 'no basis'}: {divisor.why}"[:240], RULING_FOR["share-count"]))
        except Exception as exc:  # noqa: BLE001
            out.checks.append(Check("share count (divisor)", MISSING, f"{type(exc).__name__}: {exc}", RULING_FOR["share-count"]))
    zeros = [f for f in parsed.all_figures() if f.present and f.value == 0]
    named = [f for f in zeros if f.zero_basis]
    out.checks.append(Check("zero_basis", PASS if len(named) == len(zeros) else FAIL,
                            f"{len(zeros)} zero(s), {len(named)} with a named basis"
                            + ("" if len(named) == len(zeros) else ": " + ", ".join(f"{f.period} {f.name}" for f in zeros if not f.zero_basis)),
                            RULING_FOR["zero-basis"]))
    # E112 / E118 and E119: Gate 3's two limbs, formed off the store.
    if basis is not None:
        from .manual import (GATE3_LEVERAGE_MAX, INVENTORY_LIMB_WHY, capitalisation,
                             gate3_leverage, interest_coverage,
                             inventory_operating_asset)
        # E123 (2026-09-20): where the operating asset is inventory and its
        # purchase runs through operating cash flow, BOTH of Gate 3's cash
        # limbs are DATA MISSING and out of the count -- and the measured
        # capitalisation figures print in their place, deciding nothing.
        inventory_asset = inventory_operating_asset(parsed)
        if inventory_asset:
            declared = parsed.operating_asset_is_inventory
            out.checks.append(Check("Gate 3 FCF positive (E123)", MISSING,
                                    f"{INVENTORY_LIMB_WHY}. Declared: {declared.page}",
                                    RULING_FOR["gate-3-fcf"]))
            for line in capitalisation(parsed, basis).lines():
                out.checks.append(Check("debt to total capitalisation (E123)",
                                        MEASURED, line, RULING_FOR["gate-3-leverage"]))
        cov = interest_coverage(parsed, basis)
        detail = (cov.why if cov.ratio is None else
                  f"operating income {cov.ebit:,.0f} / net finance costs "
                  f"{cov.denominator:,.0f} = {cov.ratio:.1f}x against 5x")
        if cov.bound_end is not None:
            detail += f"; at the lease-interest BOUND end: {cov.bound_end.state}" + (
                f" {cov.bound_end.ratio:.1f}x" if cov.bound_end.ratio is not None else "")
        out.checks.append(Check("Gate 3 interest coverage (E112, E118, P2, E126)",
                                {"PASS": PASS, "FAIL": FAIL, "REVIEW": FLAG}.get(cov.state, MISSING),
                                detail, RULING_FOR["coverage"]))
        # E126 STEP 3 (2026-09-20): no subtotal before financing cost and no
        # interest line to add back. What prints instead is MEASURED and
        # decides nothing -- the interest figures with their own page
        # citations, and the maturity wall, which is what actually says
        # whether such a filer can service its debt.
        if cov.ebit is None and "E126" in cov.why:
            from .manual import step3_block
            for line in step3_block(parsed, basis, notes=getattr(entry, "notes", "")):
                out.checks.append(Check("E126 step 3, measured", MEASURED, line,
                                        RULING_FOR["coverage"]))
        lev = gate3_leverage(parsed, basis)
        state = lev.state(GATE3_LEVERAGE_MAX)
        out.checks.append(Check("Gate 3 net debt / EBITDA (E119)",
                                {"PASS": PASS, "FAIL": FAIL, "REVIEW": FLAG}.get(state, MISSING),
                                lev.line(GATE3_LEVERAGE_MAX), RULING_FOR["gate-3-leverage"]))
        # E126's hold: below four evaluable gates a name may carry a score
        # but NO TIER, and therefore no MBP. Printed on every packet, not
        # only where it bites, so the denominator is always visible.
        from .manual import evaluable_gates, tier_hold
        count, why = evaluable_gates(parsed, basis)
        held = tier_hold(parsed, basis)
        out.checks.append(Check(
            "section 4.4 denominator (E99, E123, E126)",
            FLAG if held else MEASURED,
            (held or f"{count} evaluable gate(s); a tier requires 4 (E126). "
                     + " | ".join(why)),
            RULING_FOR.get("conviction", "FRAMEWORK §4.4; E99, E123, E126")))
    out.checks.append(Check("finance-net operands (interest_in_ocf)", PASS if parsed.interest_in_ocf else MISSING,
                            "declared" if parsed.interest_in_ocf else "not declared in the store", RULING_FOR["interest-net"]))
    # 4d. filter 2's three limbs on the store, as filter 2 would read it
    try:
        from .filters import fcf_limb, leverage_limb, load_filter2_config, revenue_limb
        from .manual import as_record, inventory_operating_asset
        record = as_record(parsed, as_of=as_of)
        config = load_filter2_config()
        step.reused += ["manual.as_record", "filters.fcf_limb", "filters.leverage_limb", "filters.revenue_limb"]
        limbs = [(revenue_limb(record, config), "gate-3-revenue")]
        # E123: the two cash limbs are out of the count for this filer, so
        # filter 2's echo of them would re-assert what the ruling removed.
        if not inventory_operating_asset(parsed):
            limbs = [(fcf_limb(record, config), "gate-3-fcf"),
                     (leverage_limb(record, config), "gate-3-leverage")] + limbs
        for limb, key in limbs:
            out.checks.append(Check(f"filter 2: {limb.name}", {"PASS": PASS, "FAIL": FAIL}.get(limb.state, MISSING), limb.detail, RULING_FOR[key]))
    except Exception as exc:  # noqa: BLE001
        step.note(f"filter 2 limbs did not run: {type(exc).__name__}: {exc}")


def _ratio_key(name: str) -> str:
    n = name.lower()
    if "coverage" in n:
        return "coverage"
    if "ebitda" in n:
        return "gate-3-leverage"
    if "net debt" in n:
        return "net-debt"
    if "conversion" in n:
        return "fcf-conversion"
    if "margin" in n:
        return "op-margin"
    if "profitability" in n:
        return "profitability"
    return "fcf0"


# --------------------------------------------------------------------- 5 verify

def step_verify(entry: WatchlistEntry, out: Prepared) -> None:
    step = out.step("verify")
    gate = out.context.pop("_gate", None)
    if gate is None:
        step.status = SKIPPED
        step.note("no store, so no basis and nothing to verify.")
        return
    from .manual import SECTION5_FIELDS
    order = {name: i for i, name in enumerate(SECTION5_FIELDS)}
    step.reused.append("manual.section5_gate.blocking (E21)")
    figures = sorted(gate.blocking, key=lambda f: (order.get(f.name, 999), f.period_end or date.min, f.name))
    for i, f in enumerate(figures, 1):
        out.verification.append(Verification(i, f.name, f.period, f.value, f.source or "", f.page or "", f.status_with_kind))
    step.note(f"{len(figures)} UNVERIFIED figure(s) the basis {gate.basis.label if gate.basis else ''} reads; "
              f"{len(gate.unread)} UNVERIFIED it does not read (named by the gate, never a refusal).")


# --------------------------------------------------------------------- 6 context

def step_context(entry: WatchlistEntry, route: Route, out: Prepared, *, sources_root: Path, as_of: date,
                 cache_dir: Path | None = None, now: datetime | None = None, opener=None,
                 dry_run: bool = False) -> None:
    step = out.step("context")
    price = out.context.get("price") or {}
    start = entry.peak_date.isoformat() if entry.peak_date else price.get("high_52w_date")
    window = {"from": start, "to": as_of.isoformat()}
    disclosures = []
    releases = out.steps[2].data.get("releases") if len(out.steps) > 2 else None
    if releases:
        disclosures = [r for r in releases if not start or r["released"] >= start]
        source = "the disclosure feed, classified by watch.classify"
    else:
        disclosures = [{"released": d["date"], "category": d["type"], "headline": d["file"]}
                       for d in out.documents if not start or (d["date"] and d["date"] >= start)]
        source = "sources/manifest.json by date (no feed on this route)"
    out.context["gate1_catalyst"] = {"window": window, "source": source, "disclosures": disclosures,
                                     "note": None if start else "no peak date: the window starts nowhere (no cached series, no peak_date on the entry)"}
    if start:
        _catalyst_facts(entry, out, step, peak=date.fromisoformat(start), to=as_of,
                        cache_dir=cache_dir, now=now, opener=opener, dry_run=dry_run)
    if "one_offs" not in out.context:
        out.context["one_offs"] = {"note": "no extraction ran this pass (no document, dry run, or already extracted)"}
    out.context["going_concern"] = {"note": "NOT IMPLEMENTED: the manifest records documents, not their auditor sections; open the annual report's auditor's report by hand."}
    out.context["circle"] = {"note": "nothing prepared: the circle of competence is the owner's (E51, E96)."}
    step.reused.append("watch.classify" if releases else "nordic.load_manifest")
    step.note(f"drawdown window {window['from'] or '?'} → {window['to']}: {len(disclosures)} disclosure(s) from {source}.")


def _catalyst_facts(entry: WatchlistEntry, out: Prepared, step, *, peak: date, to: date,
                    cache_dir: Path | None, now: datetime | None, opener, dry_run: bool) -> None:
    """Gate 1's catalyst limb, laid out as dated facts (vss/catalyst.py).

    The price from the cache only; the issuer's filings from EDGAR, and not
    on a dry run, which fetches nothing from a feed. Each half fails alone
    and says so: a missing half is a note, never a crash of the step.
    """
    from . import catalyst as C
    g = out.context["gate1_catalyst"]
    g["price"], g["filings"], g["timeline"] = None, [], []
    try:
        from .fetch import get_history
        fetched = get_history(entry.ticker, cache_dir or CACHE_DIR, now=now or datetime.now().astimezone(),
                              allow_network=False, write=False)
        if fetched.frame is None:
            g["price_note"] = f"no cached price series ({fetched.error or 'no cache'})"
        else:
            closes = [(stamp.date(), float(close)) for stamp, close in zip(fetched.frame.index, fetched.frame["Close"])]
            closes = [(d, c) for d, c in closes if d <= to]
            g["price"] = C.price_facts(closes, peak, to)
            step.reused.append("catalyst.price_facts")
    except Exception as exc:  # noqa: BLE001
        g["price_note"] = f"price facts raised {type(exc).__name__}: {exc}"
    if not entry.cik:
        g["filings_note"] = "no CIK on the entry: EDGAR's filing list is not read"
    elif dry_run:
        g["filings_note"] = "dry run: EDGAR's filing list is not fetched"
    else:
        try:
            from .briefing import submissions
            g["filings"] = C.filings_in_window(submissions(int(entry.cik), opener=opener), peak, to)
            g["filings_source"] = f"data.sec.gov submissions, CIK {int(entry.cik)}"
            step.reused.append("briefing.submissions")
        except Exception as exc:  # noqa: BLE001
            g["filings_note"] = f"EDGAR's filing list could not be read: {type(exc).__name__}: {exc}"
    g["timeline"] = C.timeline(g["price"], g["filings"])


# --------------------------------------------------------------------- render

def _md(p: Prepared) -> str:
    L = [f"# vss prepare — {p.ticker} ({p.name}) — {p.as_of}", "",
         f"**{p.summary}**", ""]
    if p.dry_run:
        L += ["> DRY RUN — nothing fetched from a feed, nothing read by a model, nothing written.", ""]
    st = p.context.get("stands") or {}
    L += ["## Where this name stands", ""] + [f"- {l}" for l in p.steps[0].lines]
    for d in st.get("documents", []):
        L.append(f"  - {d['kind']}: {d['label']}")
    L += ["", "## The entry's notes and readings, in full (C1)", "",
          "*Read before any step is answered: the owner's own earlier words on this name.*", "",
          "### Notes on the watchlist entry", ""]
    L += [st.get("notes") or "(the entry carries no notes)", ""]
    for r in st.get("readings", []):
        L += [f"### Reading: {r['label']} (`{r['path']}`)", "", r["text"].rstrip(), ""]
    L += ["## Route", ""] + [f"- {l}" for l in p.steps[1].lines] + [""]
    L += ["## Documents", ""]
    if p.documents:
        L += ["| date | type | period | file | figures_read |", "|---|---|---|---|---|"]
        L += [f"| {d['date']} | {d['type']} | {d['period']} | `{d['file']}` | {d['figures_read']} |" for d in p.documents]
    else:
        L.append("none in the manifest for this ticker.")
    L += [""] + [f"- {l}" for l in p.steps[2].lines] + [""]
    L += ["## Filled figures, by origin", ""]
    if p.filled:
        L += ["| field | period | value | status | origin |", "|---|---|---|---|---|"]
        L += [f"| {f['field']} | {f['period']} | {f['value']} | {f['status']} | {f['origin']} |" for f in p.filled]
    else:
        L.append("no figure was filled by this pass.")
    L += [""] + [f"- {l}" for l in p.steps[3].lines] + [""]
    L += ["## DATA MISSING", ""]
    L += [f"- {m['field']} {m['period']}: {m['reason']}" for m in p.data_missing] or ["none recorded by the fill step."]
    L += ["", "## Computed outcomes", "", "| check | outcome | detail | decided by |", "|---|---|---|---|"]
    L += [f"| {c.name} | **{c.outcome}** | {c.detail} | {c.ruling} |" for c in p.checks]
    L += [""] + [f"- {l}" for l in p.steps[4].lines] + [""]
    L += ["## Verification list (E21: what the §5 gate refuses on, in order)", ""]
    if p.verification:
        L += ["| # | field | period | value | document | page | status |", "|---|---|---|---|---|---|---|"]
        L += [f"| {v.order} | {v.field} | {v.period} | {v.value} | {v.document} | {v.page} | {v.status} |" for v in p.verification]
    else:
        L.append("nothing: " + "; ".join(p.steps[5].lines))
    L += ["", "## Human-step context", ""]
    g = p.context.get("gate1_catalyst", {})
    L += [f"**Gate 1 catalyst** — window {g.get('window', {}).get('from') or '?'} → {g.get('window', {}).get('to')}; source: {g.get('source')}"]
    for d in g.get("disclosures", [])[:40]:
        L.append(f"- {d.get('released')} {d.get('category')}: {d.get('headline')}")
    if g.get("note"):
        L.append(f"- {g['note']}")
    price = g.get("price")
    if price or g.get("filings") or g.get("price_note") or g.get("filings_note"):
        L += ["", "*The window as dated facts, side by side. Nothing here says which event, if any, "
                  "carries the decline: that is the owner's reading (B1).*", ""]
        if price:
            largest = price.get("largest")
            L.append(f"- price: {price['sessions']} session(s) after the peak; "
                     f"{len(price['down_days'])} fell {price['threshold']:.0%} or more"
                     + (f"; largest {largest['change']:+.2%} on {largest['date']}" if largest else ""))
        if g.get("filings_source"):
            L.append(f"- filings: {len(g.get('filings', []))} news-bearing filing(s) from {g['filings_source']}")
        for key in ("price_note", "filings_note"):
            if g.get(key):
                L.append(f"- {g[key]}")
        L += [f"  - {row}" for row in g.get("timeline", [])]
    o = p.context.get("one_offs", {})
    L += ["", f"**Class C one-offs** — " + (o.get("note") or
          f"class_c_impact {o.get('class_c_impact')}; sentence: {o.get('sentence') or '(none quoted)'}"
          + (f"; disagreement: {o.get('disagreement')}" if o.get('disagreement') else ""))]
    L += ["", f"**Going concern** — {p.context.get('going_concern', {}).get('note')}"]
    L += ["", f"**Circle** — {p.context.get('circle', {}).get('note')}", ""]
    alert = p.steps[3].data.get("earnings_alert")
    if alert:
        L += ["<details><summary>the earnings alert, verbatim</summary>", "", alert, "", "</details>", ""]
    L += ["## What refused, and why", ""]
    L += [f"- {r}" for r in p.refused] or ["nothing refused."]
    for s in p.steps:
        if s.status in (FAILED, NOT_BUILT):
            L.append(f"- step {s.name}: {s.status} — " + "; ".join(s.lines[-1:]))
    L += ["", "## Steps and the code each reused", ""]
    L += [f"- **{s.name}** ({s.status}): " + (", ".join(f"`{r}`" for r in s.reused) or "nothing called") for s in p.steps]
    L += ["", f"LLM calls made: {p.llm_calls} (earnings extraction {p.llm_calls_earnings}, E103 reference figures {p.llm_calls_reference}). Written: {', '.join(p.written) or 'nothing'}.",
          "", "*Never written by this command: fv_base, tier, mbp, stop_price, status. "
          "config/watchlist.yaml was read and never opened for writing.*", ""]
    return "\n".join(L)


def _json(p: Prepared) -> str:
    d = asdict(p)
    d["context"].pop("_gate", None)
    for s in d["steps"]:
        s["data"].pop("earnings_alert", None)
    return json.dumps(d, indent=2, default=str) + "\n"


def _summary(p: Prepared) -> tuple[str, int]:
    stands = p.context.get("stands") or {}
    n = 0
    n += len(p.verification)
    n += sum(1 for c in p.checks if c.outcome == FAIL)
    n += sum(1 for c in p.checks if c.name in ("store", "period basis (E19)") and c.outcome == MISSING)
    n += len(p.refused)
    n += sum(1 for s in p.steps if s.status == FAILED)
    if stands.get("resume_at"):
        struck = stands.get("struck")
        head = (f"already struck {struck}" if struck else "already struck (fv_base on the entry)")
        verdict = ("verdict not recorded" if not stands.get("verdict_recorded")
                   else f"verdict {stands.get('status')}")
        line = f"{head}; {verdict} -- resume at {stands['resume_at']}"
        if stands.get("inconsistent_e27"):
            line += "; INCONSISTENT WITH E27 (fv_base set, status PIPELINE)"
        if n:
            line += f"; blocked on {n} item(s)"
        return line, n
    return ("ready for review" if n == 0 else f"blocked on {n} item(s)"), n


# --------------------------------------------------------------------- run

def prepare_one(entry: WatchlistEntry, *, as_of: date, now: datetime, dry_run: bool, force: bool,
                manual_dir: Path, sources_root: Path, maps_dir: Path, reports_dir: Path,
                watchlist_path: Path, db_path: Path, cache_dir: Path, issuers_path, oslo_issuers_path,
                fetcher, opener, transport, reader, root: Path = PROJECT_ROOT,
                views_dir: Path | None = None) -> Prepared:
    out = Prepared(entry.ticker, entry.name or entry.ticker, entry.status, as_of.isoformat(), dry_run)
    out.context["_manual_dir"] = manual_dir
    try:
        step_stands(entry, out, root=root, views_dir=views_dir)
    except Exception as exc:  # noqa: BLE001
        out.steps[-1].status = FAILED
        out.steps[-1].note(f"{type(exc).__name__}: {exc}")
    steps = (
        ("route", lambda: step_route(entry, out, issuers_path=issuers_path, oslo_issuers_path=oslo_issuers_path)),
    )
    route = Route(ROUTE_MANUAL, "route step failed")
    try:
        route = steps[0][1]()
    except Exception as exc:  # noqa: BLE001
        out.steps[-1].status = FAILED
        out.steps[-1].note(f"{type(exc).__name__}: {exc}")
    for name, fn in (
        ("fetch", lambda: step_fetch(entry, route, out, sources_root=sources_root, issuers_path=issuers_path,
                                     oslo_issuers_path=oslo_issuers_path, opener=opener, as_of=as_of, dry_run=dry_run)),
        ("fill", lambda: step_fill(entry, route, out, manual_dir=manual_dir, sources_root=sources_root, maps_dir=maps_dir,
                                   watchlist_path=watchlist_path, db_path=db_path, dry_run=dry_run, force=force, now=now,
                                   fetcher=fetcher, transport=transport, reader=reader, opener=opener)),
        ("compute", lambda: step_compute(entry, out, manual_dir=manual_dir, cache_dir=cache_dir, now=now, as_of=as_of)),
        ("verify", lambda: step_verify(entry, out)),
        ("context", lambda: step_context(entry, route, out, sources_root=sources_root, as_of=as_of,
                                         cache_dir=cache_dir, now=now, opener=opener, dry_run=dry_run)),
    ):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 -- independent steps: reported, the rest run
            if not out.steps or out.steps[-1].name != name:
                out.step(name)
            out.steps[-1].status = FAILED
            out.steps[-1].note(f"{type(exc).__name__}: {exc}")
            log.warning("%s prepare/%s: %s", entry.ticker, name, exc)
    out.context.pop("_manual_dir", None)
    out.summary, out.blocked_on = _summary(out)
    if not dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        md = reports_dir / f"{entry.ticker}-{as_of.isoformat()}.md"
        js = reports_dir / f"{entry.ticker}-{as_of.isoformat()}.json"
        md.write_text(_md(out), encoding="utf-8")
        out.report_md = str(md)
        js.write_text(_json(out), encoding="utf-8")
        out.report_json = str(js)
    return out


def run_prepare(*, ticker: str | None = None, all_pipeline: bool = False, dry_run: bool = False,
                force: bool = False, watchlist_path: Path = WATCHLIST_PATH,
                manual_dir: Path | None = None, sources_root: Path | None = None,
                maps_dir: Path | None = None, reports_dir: Path | None = None,
                db_path: Path = DB_PATH, cache_dir: Path = CACHE_DIR,
                issuers_path=None, oslo_issuers_path=None, now: datetime | None = None,
                fetcher=None, opener=None, transport=None, reader=None,
                root: Path = PROJECT_ROOT, views_dir: Path | None = None) -> tuple[int, str]:
    """`vss prepare`. Returns (exit_code, markdown). Exit 1 when any name is blocked."""
    from .appendix import MAPS_DIR
    from .manual import MANUAL_DIR
    from .nordic import ISSUERS_PATH as NORDIC_ISSUERS
    from .oslo import ISSUERS_PATH as OSLO_ISSUERS

    run_ts = now or datetime.now().astimezone()
    as_of = run_ts.date()
    manual_dir = Path(manual_dir or MANUAL_DIR)
    sources_root = Path(sources_root or SOURCES_DIR)
    maps_dir = Path(maps_dir or MAPS_DIR)
    reports_dir = Path(reports_dir or PREPARE_DIR)
    entries = load_watchlist(watchlist_path)
    before = Path(watchlist_path).read_bytes()
    if ticker:
        wanted = ticker.strip().upper()
        chosen = [e for e in entries if e.ticker.upper() == wanted]
        if not chosen:
            raise ConfigError(f"ticker {ticker} is not in {watchlist_path}; prepare reads the entry "
                              f"(route, CIK, quarters) and never creates one")
    elif all_pipeline:
        chosen = [e for e in entries if e.status == "PIPELINE"]
    else:
        raise ConfigError("name a ticker or pass --all-pipeline.")

    results: list[Prepared] = []
    out = [f"# vss prepare — {as_of.isoformat()}", ""]
    if dry_run:
        out += ["> DRY RUN — nothing fetched, nothing read by a model, nothing written.", ""]
    for entry in chosen:
        results.append(prepare_one(
            entry, as_of=as_of, now=run_ts, dry_run=dry_run, force=force, manual_dir=manual_dir,
            sources_root=sources_root, maps_dir=maps_dir, reports_dir=reports_dir,
            watchlist_path=Path(watchlist_path), db_path=db_path, cache_dir=cache_dir,
            issuers_path=issuers_path or NORDIC_ISSUERS, oslo_issuers_path=oslo_issuers_path or OSLO_ISSUERS,
            fetcher=fetcher, opener=opener, transport=transport, reader=reader,
            root=root, views_dir=views_dir))
    assert_no_watchlist_write(before, Path(watchlist_path).read_bytes())
    out += ["| ticker | status | route | summary | LLM calls | report |", "|---|---|---|---|---|---|"]
    for p in results:
        out.append(f"| `{p.ticker}` | {p.status} | {p.steps[1].data.get('route', '?')} | {p.summary} | {p.llm_calls} | "
                   f"{p.report_md or '(dry run)'} |")
    out.append("")
    if dry_run:
        for p in results:
            out += ["---", "", _md(p)]
    return (1 if any(p.blocked_on for p in results) else 0), "\n".join(out) + "\n"
