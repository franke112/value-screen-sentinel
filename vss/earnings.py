"""`vss earnings` -- read a primary source and flag FRAMEWORK 4.2 trips.

Pipeline: primary source -> LLM figure extraction -> deterministic 4.2
evaluation -> alert. The LLM contributes figures and quotes; every
judgement is made by pure functions in rules.py.

Nothing here writes to the watchlist. Extracted figures are PROPOSED in
the alert and entered by the owner. That is the point: the quarters:
block is the owner's record, not the model's.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path

from . import rules as R
from .config import ConfigError, load_watchlist, unit_problem
from .extract import PROVENANCE_UNVERIFIABLE as PROVENANCE_LABEL
from .extract import UNIT_ERROR as UNIT_LABEL
from .extract import EXTRACTION_DISAGREEMENT as DISAGREEMENT_LABEL
from .extract import Extraction, agreement, extract
from .source import PrimarySource, SourceError, fetch, read_text_file
from .store import persist_earnings

log = logging.getLogger(__name__)

#: What this path's figures came from, for the `source:` line of the
#: proposed quarter. `vss earnings` reads a PRIMARY SOURCE -- a press
#: release or an interim report -- which is `release` in the watchlist's
#: vocabulary (`config.VALID_SOURCES`). The XBRL route sets its own
#: `xbrl` in `xbrl.as_quarter`; `manual` is the owner's, for a figure he
#: typed himself.
SOURCE_RELEASE = "release"

#: FRAMEWORK 4.2 is one set of rules read in two situations. On a name
#: you HOLD it is Phase 3 thesis invalidation; on a candidate it is the
#: Phase 2 VALIDATION gate that decides whether the name can become a
#: position at all. Same rules, same figures, same arithmetic -- what
#: differs is what a trip MEANS, so only the framing changes.
TRIP_HEADLINE = "4.2 POSSIBLE TRIP - VERIFY AGAINST SOURCE"
VALIDATION_HEADLINE = "4.2 FAILS VALIDATION - VERIFY AGAINST SOURCE"
UNCERTAIN_HEADLINE = "EXTRACTION UNCERTAIN"

#: Statuses whose 4.2 reading is candidate rejection rather than thesis
#: invalidation. Derived from the schema rather than listed, so a status
#: added later cannot silently fall into the HELD framing: HELD is the
#: exception, everything else is a candidate.
CANDIDATE_STATUSES = tuple(s for s in R.VALID_STATUSES if s != "HELD")


def provisional_quarter(extraction: Extraction, period: str | None) -> R.Quarter:
    """Build an in-memory quarter from the extraction.

    Never persisted. ``eps_consensus`` is absent by construction -- it is
    MANUAL ONLY, so rule 4.2.4 will report CANNOT EVALUATE until the
    owner enters it.
    """
    figures = extraction.figures
    return R.Quarter(
        period=period or extraction.period or "PROVISIONAL",
        revenue=figures.get("revenue"),
        revenue_yoy=figures.get("revenue_yoy"),
        # B9/E30's carve-out leg. ABSENT where the release states none --
        # `.get` returns None and nothing here substitutes a zero, because
        # "the company disclosed no organic figure" and "the company
        # disclosed flat organic growth" are opposite facts.
        revenue_yoy_organic=figures.get("revenue_yoy_organic"),
        op_income=figures.get("op_income"),
        op_margin=figures.get("op_margin"),
        eps=figures.get("eps"),
        eps_consensus=None,                       # MANUAL ONLY, never extracted
        net_debt_ebitda=figures.get("net_debt_ebitda"),
        guidance_action=extraction.guidance_action,
        receivables=figures.get("receivables"),
        inventory=figures.get("inventory"),
        class_c_impact=figures.get("class_c_impact"),
        covenant_headroom=figures.get("covenant_headroom"),
        basis=extraction.basis,
        accounting=extraction.accounting,
        period_basis=extraction.period_basis,
        # THE PROVENANCE THIS PATH ALREADY KNOWS. `source` is one of
        # release|xbrl|manual, and this path read a PRESS RELEASE -- the
        # primary source it was pointed at. It used to emit the field blank
        # and leave the owner to supply from memory a value the tool had in
        # hand; `xbrl.as_quarter` has always set its own `source="xbrl"`
        # through the same renderer, so the two halves of one block
        # disagreed about whether provenance was the tool's job.
        source=SOURCE_RELEASE,
    )


def _yaml_block(quarter: R.Quarter) -> list[str]:
    lines = [f"  - period: {quarter.period}"]
    for key in ("revenue", "revenue_yoy", "revenue_yoy_organic",
                "op_income", "op_margin", "eps",
                "net_debt_ebitda", "receivables", "inventory",
                "class_c_impact", "covenant_headroom"):
        value = getattr(quarter, key)
        lines.append(f"    {key}: {value if value is not None else ''}")
    lines.append(f"    eps_consensus:        # MANUAL ONLY - vss never fills this")
    for key in ("guidance_action", "basis", "accounting", "period_basis", "source"):
        value = getattr(quarter, key)
        lines.append(f"    {key}: {value or ''}")
    return lines


def render_alert(
    *,
    ticker: str,
    name: str,
    source: PrimarySource | None,
    extraction: Extraction | None,
    results: tuple[R.KillResult, ...],
    quarter: R.Quarter | None,
    as_of: date,
    shadow: bool,
    status: str = "HELD",
    catalyst_date: date | None = None,
    error: str | None = None,
    admission: R.Admission | None = None,
    reporting_frequency: str = R.DEFAULT_REPORTING_FREQUENCY,
) -> str:
    out: list[str] = []
    url = source.url if source else (extraction.url if extraction else "unavailable")
    candidate = status in CANDIDATE_STATUSES
    rejected = admission is not None and not admission.admitted

    out.append(f"# vss earnings -- {ticker} ({name}) -- {as_of.isoformat()}")
    out.append("")
    if shadow:
        out.append("> **SHADOW MODE** -- logged to sqlite, nothing sent. "
                   "Run with `--no-shadow` to leave shadow mode.")
        out.append("")
    # The primary source URL is always the first fact in the alert.
    out.append(f"**PRIMARY SOURCE:** {url}")
    out.append("")
    out.append("*Every figure below must be verified against that source before "
               "any action. This tool flags; it does not advise.*")
    out.append("")
    if candidate:
        out.append(f"**STATUS:** {status} -- read as FRAMEWORK Phase 2 VALIDATION. "
                   f"A 4.2 rule that fires REJECTS THE CANDIDATE; it does not "
                   f"invalidate a thesis, because there is no position here yet.")
    else:
        out.append(f"**STATUS:** {status} -- read as thesis invalidation. A 4.2 "
                   f"rule that fires puts an existing position in question.")
    out.append("")

    if error:
        out.append(f"## {UNCERTAIN_HEADLINE}")
        out.append("")
        out.append(f"- {error}")
        out.append("")
        return "\n".join(out)

    if admission is not None:
        # The guard's decision is the first thing said about the period,
        # because everything below it -- the evaluation, the proposal --
        # depends on whether the period was admitted at all.
        out.append("## OVERLAP GUARD")
        out.append("")
        unit = R.period_unit(R.PERIODS_PER_YEAR[reporting_frequency])
        out.append(f"This ticker reports **{reporting_frequency}**; FRAMEWORK 4.2 windows "
                   f"are counted in {unit}.")
        if rejected:
            out.append(f"- **PERIOD REJECTED -- NOT PROPOSED, NOT EVALUATED:** "
                       f"{admission.reason}. The figures read are shown below for "
                       f"the record only.")
        elif admission.displaced:
            out.append(f"- Period {admission.period} admitted: {admission.reason}.")
            out.append(f"- Displaced for this evaluation: "
                       f"{', '.join(admission.displaced)}.")
        else:
            out.append(f"- Period {admission.period} admitted: {admission.reason}.")
        out.append("")

    trips = [r for r in results if r.state == R.TRIP and r.rule.startswith("4.2.")]
    soft = [r for r in results if r.state == R.TRIP and not r.rule.startswith("4.2.")]
    unknown = [r for r in results if r.state == R.CANNOT_EVALUATE]
    clear = [r for r in results if r.state == R.NO_TRIP]

    out.append(f"## {VALIDATION_HEADLINE if candidate else TRIP_HEADLINE}")
    out.append("")
    if not trips:
        if candidate:
            out.append("No 4.2 rule failed on the figures extracted. That clears one "
                       "gate of FRAMEWORK Phase 2. It is not a decision, and it is "
                       "not the other gates.")
        else:
            out.append("No 4.2 hard-kill rule tripped on the figures extracted.")
    else:
        for r in trips:
            out.append(f"### {r.rule} -- {r.name}")
            out.append("")
            out.append(f"- **Finding:** {r.detail}")
            for fig in r.figures:
                out.append(f"- Figure: {fig}")
            if extraction:
                for field, sentence in sorted(extraction.sentences.items()):
                    if field.split("_")[0] in r.name.lower() or field in r.detail:
                        out.append(f"- Source sentence ({field}): \"{sentence}\"")
            out.append(f"- Source: {url}")
            out.append("")
    out.append("")

    if soft:
        out.append("## SOFT FLAGS (FRAMEWORK 4.3, -1 each) -- NOT hard kills")
        out.append("")
        for r in soft:
            out.append(f"- **{r.rule}** {r.name}: {r.detail}")
            for fig in r.figures:
                out.append(f"  - {fig}")
        out.append("")

    if extraction and extraction.disagreements:
        out.append(f"## {DISAGREEMENT_LABEL} -- TWO RUNS, ONE SOURCE")
        out.append("")
        out.append("The same text was read twice and the readings differ. Each "
                   "field below is set to null: two readings that disagree are "
                   "not a figure, and neither one is more true for having been "
                   "produced first.")
        out.append("")
        out.append("| Field | First run | Second run |")
        out.append("|---|---|---|")
        for field, both in sorted(extraction.disagreements.items()):
            first = "null" if both["first"] is None else both["first"]
            second = "null" if both["second"] is None else both["second"]
            out.append(f"| `{field}` | {first} | {second} |")
        out.append("")
    elif extraction and extraction.compared:
        out.append("## TWO RUNS AGREED ON EVERY FIGURE")
        out.append("")
        out.append("The source was read twice and every figure and claim matched. "
                   "That is corroboration, not verification -- both runs read the "
                   "same text with the same model, and both can be wrong together.")
        out.append("")
        if extraction.attribution_differences:
            out.append("They did not agree on WHERE some of those figures were "
                       "read. The number is corroborated; its attribution is not:")
            out.append("")
            for difference in extraction.attribution_differences:
                out.append(
                    f"- `{difference['field']}` = {difference['value']}: "
                    f"{difference['kind']} read as `{difference['first']}` on the "
                    f"first run, `{difference['second']}` on the second"
                )
            out.append("")

    if extraction and extraction.uncertain:
        out.append(f"## {UNCERTAIN_HEADLINE}")
        out.append("")
        out.append("Treat every figure in this alert as unconfirmed:")
        for reason in extraction.uncertainty_reasons():
            out.append(f"- {reason}")
        out.append("")

    if source and source.warnings:
        out.append("## SOURCE WARNINGS")
        out.append("")
        for w in source.warnings:
            out.append(f"- {w}")
        out.append("")

    if unknown:
        out.append("## CANNOT EVALUATE")
        out.append("")
        for r in unknown:
            out.append(f"- **{r.rule}** {r.name}: {r.detail}")
        out.append("")

    if clear:
        out.append("## NO TRIP")
        out.append("")
        for r in clear:
            out.append(f"- **{r.rule}** {r.name}: {r.detail}")
        out.append("")

    if extraction and extraction.sentences:
        out.append("## EXTRACTED FIGURES AND THEIR SOURCE SENTENCES")
        out.append("")
        out.append("| Field | Value | Measure | Column read | Verbatim sentence |")
        out.append("|---|---|---|---|---|")
        for field in sorted(extraction.figures):
            value = extraction.figures[field]
            sentence = extraction.sentences.get(field, "-- not stated --")
            column = extraction.period_columns.get(field)
            if field in extraction.unverifiable:
                shown = f"**null ({PROVENANCE_LABEL})**"
            elif field in extraction.out_of_band:
                shown = f"**null ({UNIT_LABEL})**"
            elif value is None:
                shown = "**null (not stated)**"
            else:
                shown = str(value)
            source_type = extraction.source_types.get(field)
            if column:
                col = f"`{column}`"
            elif source_type == "table":
                col = "**NOT RECORDED**"
            else:
                col = "--"
            measure = extraction.measures.get(field)
            shown_measure = (
                "**adjusted**" if measure == "adjusted" else (measure or "--")
            )
            out.append(f"| `{field}` | {shown} | {shown_measure} | {col} | {sentence} |")
        out.append("")

    if extraction and extraction.unverifiable:
        out.append(f"## {PROVENANCE_LABEL}")
        out.append("")
        out.append("These figures were dropped: the quoted sentence does not contain "
                   "the number, so the quote does not evidence it. A balance-sheet "
                   "label is not provenance.")
        out.append("")
        for field, dropped in sorted(extraction.unverifiable.items()):
            out.append(f"- `{field}`: model reported **{dropped['value']}** quoting "
                       f"\"{dropped['sentence'] or 'nothing'}\" -- set to null")
        out.append("")

    if extraction and extraction.out_of_band:
        out.append(f"## {UNIT_LABEL}")
        out.append("")
        out.append("These figures were dropped: the value is not in the units "
                   "this schema uses. A ratio is a FRACTION -- 6.6 per cent is "
                   "0.066, not 6.6. They are NOT scaled to fit: 6.6 could be a "
                   "misreported 6.6% or a genuine 660%, and choosing between "
                   "them would be vss deciding what the source said.")
        out.append("")
        for field, dropped in sorted(extraction.out_of_band.items()):
            out.append(f"- `{field}`: model reported **{dropped['value']}** quoting "
                       f"\"{dropped['sentence'] or 'nothing'}\" -- set to null")
        out.append("")

    adjusted = sorted(k for k, v in (extraction.measures if extraction else {}).items()
                      if v == "adjusted")
    if adjusted:
        out.append("## ADJUSTED MEASURES TAKEN")
        out.append("")
        out.append("FRAMEWORK 4.2 is written against the REPORTED figure. Where a "
                   "report states both, vss takes the unadjusted one; these fields "
                   "came from an adjusted measure, so the source states no other:")
        out.append("")
        for field in adjusted:
            out.append(f"- `{field}` = {extraction.figures.get(field)} "
                       f"(**adjusted**) -- \"{extraction.sentences.get(field, '')}\"")
        out.append("")

    if quarter and rejected:
        out.append("## PROPOSED quarters: ENTRY -- REJECTED BY THE OVERLAP GUARD")
        out.append("")
        out.append(f"No entry is proposed for {quarter.period}: {admission.reason}. "
                   f"The extracted figures stand above as the record of what the "
                   f"document states; they are not offered for pasting.")
        out.append("")
    elif quarter:
        out.append("## PROPOSED quarters: ENTRY -- NOT WRITTEN")
        out.append("")
        out.append("vss will never write this. Copy it into "
                   "`config/watchlist.yaml` yourself after verifying every "
                   "figure against the primary source.")
        out.append("")
        if admission is not None and admission.displaced:
            out.append(f"> **OVERLAP GUARD:** {admission.reason}.")
            out.append("")
        # The loader's own contract, asked before proposing rather than
        # discovered after pasting. A tool whose output its own loader
        # rejects has two definitions of valid.
        problem = unit_problem(quarter)
        if problem:
            out.append(f"> **THIS ENTRY WILL NOT LOAD.** {problem}")
            out.append("")
            out.append("> Do not fix it by editing the number. The figures came "
                       "out of the source that way, so the source is where the "
                       "answer is.")
            out.append("")
        out.append("```yaml")
        out.extend(_yaml_block(quarter))
        out.append("```")
        out.append("")

    if extraction and extraction.proposed_exec_changes:
        out.append("## PROPOSED exec_changes: ENTRIES -- NOT WRITTEN")
        out.append("")
        for change in extraction.proposed_exec_changes:
            out.append(f"- `{change['role']}` departed {change['departed']}")
            if change.get("sentence"):
                out.append(f"  - \"{change['sentence']}\"")
        out.append("")

    if catalyst_date is not None:
        out.append("## PROPOSED catalyst_resolved -- NOT WRITTEN")
        out.append("")
        out.append(f"The catalyst dated {catalyst_date.isoformat()} appears addressed "
                   f"by this release. If you agree, set:")
        out.append("")
        out.append("```yaml")
        out.append(f"    catalyst_resolved: {as_of.isoformat()}")
        out.append("```")
        out.append("")

    return "\n".join(out)


def run_earnings(
    *,
    ticker: str,
    url: str | None = None,
    text_file: str | None = None,
    shadow: bool = True,
    compare: bool = False,
    target_period: str | None = None,
    watchlist_path: Path,
    db_path: Path,
    now: datetime | None = None,
    transport=None,
    fetcher=None,
    on_extraction=None,
) -> tuple[int, str]:
    """Returns (exit_code, alert_markdown).

    ``on_extraction``, when given, is called once with the Extraction this
    run made (after --compare has been applied) and the provisional
    Quarter. `vss prepare` uses it to carry the one-offs and their quoted
    sentences into its report without reading the source a second time.
    """
    run_ts = now or datetime.now().astimezone()
    as_of = run_ts.date()

    entries = {e.ticker.upper(): e for e in load_watchlist(watchlist_path)}
    entry = entries.get(ticker.strip().upper())
    if entry is None:
        raise ConfigError(f"ticker {ticker} is not in {watchlist_path}")
    # Every status is allowed. FRAMEWORK Phase 2 VALIDATION runs 4.2
    # against a CANDIDATE, before it is a position -- refusing the
    # WATCH statuses and PIPELINE made it impossible to work a name up
    # to a buy decision,
    # which is the step 4.2 exists to inform.

    source, extraction, quarter, results, error = None, None, None, (), None
    admission = None
    if target_period is not None and R.period_parts(target_period) is None:
        raise ConfigError(
            f"--period must look like 2025-Q4, 2025-H1, 2025-H2 or 2025-FY, "
            f"got {target_period!r}"
        )
    try:
        if text_file:
            source = read_text_file(text_file)
        elif url:
            source = (fetcher or fetch)(url)
        else:
            raise SourceError("no --url or --text-file given")
    except SourceError as exc:
        error = f"primary source unavailable: {exc}"
        log.error("%s: %s", entry.ticker, error)

    if source is not None:
        extraction = extract(source, transport=transport,
                             target_period=target_period)
        if compare:
            # A second reading of the same text. Not a retry -- the first
            # result is kept and contradicted, not replaced.
            extraction = agreement(extraction, extract(
                source, transport=transport, target_period=target_period))
        quarter = provisional_quarter(extraction, target_period or extraction.period)
        if on_extraction is not None:
            on_extraction(extraction, quarter)
        # The OVERLAP GUARD decides whether the provisional period may sit
        # in the history at all, and which stored periods it stands in for.
        # A re-read of a loaded period replaces the stored row for the
        # evaluation -- appending it beside the stored row counted one
        # guidance cut twice (SAP Q2 2026, 2026-08-22). A coarser period
        # over a finer one is rejected; a finer one displaces the coarser.
        stored = [q.period for q in entry.quarters]
        admission = R.admit_period(stored, quarter.period, entry.reporting_frequency)
        combined = [q for q in entry.quarters if q.period not in admission.displaced]
        if admission.admitted:
            combined.append(quarter)
            combined.sort(key=lambda q: R.period_sort_key(q.period))
        # The provisional quarter is evaluated but never persisted.
        from .manual import kill_leverage_reading
        results = R.evaluate_hard_kills(
            combined, entry.exec_changes, as_of, entry.reporting_frequency,
            derived_leverage=kill_leverage_reading(entry.ticker))

    unresolved_catalyst = (
        entry.catalyst_date
        if entry.catalyst_date and entry.catalyst_resolved is None
        else None
    )
    alert = render_alert(
        ticker=entry.ticker, name=entry.name, source=source, extraction=extraction,
        results=results, quarter=quarter, as_of=as_of, shadow=shadow,
        status=entry.status, catalyst_date=unresolved_catalyst, error=error,
        admission=admission, reporting_frequency=entry.reporting_frequency,
    )

    trips = [r for r in results if r.state == R.TRIP and r.rule.startswith("4.2.")]
    persist_earnings(db_path, {
        "run_ts": run_ts.isoformat(timespec="seconds"),
        "as_of": as_of.isoformat(),
        "ticker": entry.ticker,
        "source_url": source.url if source else (url or text_file),
        "model": extraction.model if extraction else None,
        "shadow": 1 if shadow else 0,
        "trips": "; ".join(r.rule for r in trips) or None,
        "cannot_evaluate": "; ".join(
            r.rule for r in results if r.state == R.CANNOT_EVALUATE) or None,
        "extraction_uncertain": 1 if (extraction is None or extraction.uncertain) else 0,
        "uncertainty_reasons": "; ".join(
            extraction.uncertainty_reasons()) if extraction else error,
        "error": error,
        "alert": alert,
        "raw_response": extraction.raw_response if extraction else None,
    })
    if shadow:
        log.warning("%s: SHADOW MODE -- logged to sqlite, nothing sent", entry.ticker)
    log.info("%s: %d 4.2 trip(s), extraction uncertain=%s",
             entry.ticker, len(trips),
             extraction.uncertain if extraction else True)
    return (0 if error is None else 1), alert
