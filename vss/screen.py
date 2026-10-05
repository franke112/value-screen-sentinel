"""``python -m vss screen`` -- the candidate screener.

WHAT THIS TOOL PRODUCES IS REVIEW WORK, NEVER A PURCHASE. Its final output is
three to five names entered as PIPELINE in the watchlist WITHOUT an mbp and
WITHOUT an fv_base; the whole FRAMEWORK section 5 chain is then run by hand.
No code path in this module, or any module it calls, may set a buy price or a
fair value. Phase 1 does not even write to the watchlist -- it writes files
under data/ and prints to stdout.

Architecture, and the reason for it: bulk price history is cheap and
batchable, fundamentals are one call per ticker and do not scale to thirteen
thousand names. So:

    step 1  price the ENTIRE universe, in batches, with backoff and retry
    step 2  the price filter runs on that                      (phase 2)
    step 3  fundamentals for the SURVIVORS of step 2 only      (phase 3)
    step 4  the fundamentals filter runs on those              (phase 3)

Each step's raw data is snapshotted per run so any candidate list can be
reproduced later, exactly.

-----------------------------------------------------------------------------
RSI AND SMA50 ARE FIELDS. THEY ARE NEVER FILTERS.

They are reported next to every candidate and they never remove one. The
record, recomputed on the committed SAP.DE fixture rather than recalled:

    date                       close   drawdown   RSI(14)   vs SMA50
    2026-07-23  the low       128.32      49.6%      34.1     -10.9%
    2026-07-27  bought        151.28      40.6%      62.3      +5.0%
    2026-07-29                162.04      36.4%      69.3     +12.3%

An SMA50 filter discards SAP on one of those two days whichever way it is
pointed: "must be above the SMA50" rejects the low of 2026-07-23, "must be
below it" rejects the purchase of 2026-07-27, two sessions later. RSI 34.1
on the low against 62.3 on the buy -- and 75 later that summer -- means any
RSI band drawn to catch one of them misses the other.

(The purchase was four days after the low, on which SAP stood 5.0% ABOVE its
SMA50, not below: it had reclaimed the average two sessions earlier. The
conclusion is unchanged and, if anything, firmer -- no single momentum
threshold spans a low and its reclaim.)

Momentum answers WHEN to deploy (FRAMEWORK section 6), by hand, after the
fundamental work. It does not get to decide WHAT is worth looking at.

Any future phase that adds a filter must not read rsi14, sma50 or
pct_vs_sma50 as a pass/fail input. They travel as columns.

THE 52-WEEK LOW TRAVELS UNDER THE SAME RULE (FRAMEWORK-EDITS E63, ruled
2026-08-28 after CTSH). The band cannot tell a name that fell and stayed
down from one that fell and has since recovered: CTSH read 26.5% below its
high and 64.7% above its 2026-06-30 low on the same day. low_52w,
low_52w_date and pct_above_52w_low are carried on every candidate row,
printed beside the drawdown, and read by no filter and by nothing in the
ranking key. B41 asked whether a threshold would ever be drawn on them;
E127 (2026-09-28) decided it: NO threshold on the low. What the month of
record showed was answered by a DIFFERENT measure -- the 12-month return,
which filter 1 does read (`rules.fell_over_year`). The low stays a field.
-----------------------------------------------------------------------------

The dislocation band and the staleness gate are IMPORTED from rules.py, which
is the same code ``vss run`` uses on the live watchlist. Nothing here
reimplements a FRAMEWORK rule; if a rule is needed and rules.py has no
callable for it, it gets extracted there first.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Sequence

from . import fundamentals as fundamentals_step
from . import fx as fx_step
from . import pipeline as pipeline_step
from . import prices as price_step
from . import ranking as ranking_step
from . import series_sanity
from . import snapshot as snapshot_store
from . import vendorstrings
from .calendars import CALENDARS_PATH, load_market_calendars
from .fetch import AUTO_ADJUST, DEFAULT_PERIOD
from .metrics import settled_through
from .filters import (
    DATA_MISSING,
    EXCLUSIONS_PATH,
    FAIL,
    FILTER2_CONFIG_PATH,
    FLAG,
    LIMB_FCF,
    LIMB_LEVERAGE,
    LIMB_REVENUE,
    NOT_APPLICABLE,
    PASS,
    COMMODITY_PRICE_PATH,
    PHARMA_BIOTECH_PATH,
    STEP_COMMODITY_PRICE,
    Filter1Result,
    apply_circle_of_competence,
    apply_exclusions,
    limb_matrix,
    load_circle_of_competence,
    load_exclusions,
    load_filter2_config,
    run_filter1,
    run_filter2,
)
from .rules import (DISLOCATION_MAX, DISLOCATION_MIN,
                    MAX_CLOSE_AGE_TRADING_DAYS)
from .universe import (
    UniverseError,
    UniverseLoad,
    load_floors,
    load_type_rules,
    load_universe,
    reason_breakdown,
    yield_table,
)

log = logging.getLogger(__name__)

UNIVERSE_DIR = Path("config/universe")
TYPE_RULES_PATH = UNIVERSE_DIR / "instrument_types.yaml"
FLOORS_PATH = UNIVERSE_DIR / "floors.yaml"
RUNS_ROOT = Path("data/screener_runs")
#: The database that is never pruned. E51's and E96's string limbs read their
#: input from it (`vss/vendorstrings.py`), so the exclusion outlives E93's
#: snapshot retention -- CODE-REVIEW-2026-09-01 D3.
DB_PATH = Path("data/vss.sqlite")

RULE = "=" * 78
THIN = "-" * 78


def _heading(text: str) -> str:
    return f"\n{RULE}\n{text}\n{RULE}"


def _load(universe_dir: Path, tiers: Sequence[str]) -> UniverseLoad:
    rules = load_type_rules(universe_dir / TYPE_RULES_PATH.name)
    return load_universe(universe_dir, tiers=tiers, type_rules=rules)


# --- --universe-report -----------------------------------------------------


def universe_report(
    universe_dir: Path = UNIVERSE_DIR, tiers: Sequence[str] = ("A",)
) -> str:
    load = _load(universe_dir, tiers)
    floors = load_floors(universe_dir / FLOORS_PATH.name)
    lines: list[str] = []

    lines.append(_heading(f"UNIVERSE REPORT  tiers={','.join(t.upper() for t in tiers)}"))

    lines.append("\nSOURCE FILES")
    lines.append(f"  {'file':<38}{'rows':>7}  {'tiers':<14}{'provenance'}")
    lines.append("  " + THIN[:74])
    for source in load.files:
        meta = source.meta or {}
        tier_counts = ",".join(
            f"{tier}:{count}" for tier, count in sorted(source.tier_counts.items())
        ) or "-"
        marks = []
        if not meta:
            marks.append("NO METADATA")
        else:
            if meta.get("approximation"):
                marks.append("APPROXIMATION")
            if source.meta_sha_matches is False:
                marks.append("SHA MISMATCH -- file edited since it was built")
            expected = meta.get("expected_rows")
            if expected and expected != source.rows:
                marks.append(f"{source.rows}/{expected} of the named index")
        lines.append(
            f"  {source.path.name:<38}{source.rows:>7}  {tier_counts:<14}"
            f"{'; '.join(marks) if marks else 'ok'}"
        )

    lines.append("\nYIELD -- rows in and out of every step")
    lines.append("  " + yield_table(load.tallies).replace("\n", "\n  "))
    lines.append("\n  rejections, split by whether a VALUE or its ABSENCE did it:")
    lines.append(reason_breakdown(load.tallies))

    lines.append("\nCOUNT PER MARKET")
    for market, count in sorted(load.by_market.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"  {market:<24}{count:>6}")
    lines.append(f"  {'TOTAL':<24}{len(load.instruments):>6}")

    excluded = [r for r in load.rejections if r.step == "instrument_type"]
    lines.append("\nEXCLUDED PER REASON (instrument type, from the source list)")
    if excluded:
        per_reason: dict[str, int] = {}
        for rejection in excluded:
            per_reason[f"[{rejection.kind}] {rejection.reason}"] = (
                per_reason.get(f"[{rejection.kind}] {rejection.reason}", 0) + 1
            )
        for reason, count in sorted(per_reason.items(), key=lambda kv: -kv[1]):
            lines.append(f"  {count:>6}  {reason}")
    else:
        lines.append("       0  nothing excluded on instrument type")
    lines.append(
        f"  {len(load.unknown_type_kept):>6}  [missing] instrument type unknown -- KEPT and counted"
    )
    lines.append(
        "          ADR exclusion: NO DATA on Yahoo-typed lists. Yahoo reports an ADR\n"
        "          as quoteType EQUITY, so the rule has nothing to fire on. It is not\n"
        "          guessed from the name string. Stockholm preference and D-share\n"
        "          lines the source types as equity are excluded by TICKER rule\n"
        "          instead (instrument_types.yaml, exclude_tickers; item 4) -- the\n"
        "          list's own identifier for the line, still never its name. A German\n"
        "          Vorzugsaktie (VOW3.DE, HEN3.DE, ...) is an ordinary share without a\n"
        "          vote and is equity (E48)."
    )

    unmapped = [r for r in load.rejections if r.step == "yahoo_mapping"]
    lines.append("\nWITHOUT A VALID YAHOO MAPPING")
    lines.append(f"  {len(unmapped):>6}  constituents carry no Yahoo symbol and cannot be priced")
    for rejection in unmapped[:15]:
        lines.append(f"          {rejection.key}")
    if len(unmapped) > 15:
        lines.append(f"          ... and {len(unmapped) - 15} more")

    with_isin = sum(1 for i in load.instruments if i.isin)
    lines.append("\nDEDUP")
    lines.append(f"  isin coverage: {with_isin}/{len(load.instruments)} instruments carry an ISIN")
    ticker_merges = [m for m in load.merges if m.on == "ticker_yahoo"]
    isin_merges = [m for m in load.merges if m.on == "isin"]
    lines.append(f"  merged on ticker_yahoo (same listing in two lists): {len(ticker_merges)}")
    for merge in ticker_merges[:10]:
        lines.append(f"      {merge.kept:<16} {merge.detail}")
    if len(ticker_merges) > 10:
        lines.append(f"      ... and {len(ticker_merges) - 10} more")
    lines.append(f"  merged on isin (different listings of one security): {len(isin_merges)}")
    for merge in isin_merges:
        lines.append(f"      kept {merge.kept:<12} dropped {merge.dropped:<12} {merge.basis}")
    if not isin_merges:
        lines.append(
            "      none. With no ISIN populated this layer cannot fire -- it is\n"
            "      INERT, not clean. Cross-venue dual listings survive as two rows."
        )

    if load.dual_listing_candidates:
        lines.append(
            "\n  POSSIBLE dual listings, unresolved (same name, two markets, no ISIN).\n"
            "  REPORTED, NEVER MERGED: a name match is not evidence, and this list\n"
            "  shows why -- some of these are different companies that share a name."
        )
        for name, tickers in load.dual_listing_candidates:
            lines.append(f"      {name:<28}{', '.join(tickers)}")

    lines.append("\nTIER FLOORS (config, not code)")
    for tier in ("A", "B", "C"):
        spec = floors.for_tier(tier)
        lines.append(f"  tier {tier}: {spec if spec else 'index membership is the floor'}")
    lines.append(
        "  Every monetary floor carries its own currency. Applying them needs an FX\n"
        "  source, which phase 1 does not have and does not fake."
    )

    lines.append(
        f"\nFRAMEWORK constants in force (imported from rules.py, never redefined here):\n"
        f"  dislocation band {DISLOCATION_MIN:.0%}-{DISLOCATION_MAX:.0%} inclusive; "
        f"staleness gate {MAX_CLOSE_AGE_TRADING_DAYS} trading days on the exchange "
        f"calendar (E47)"
    )
    return "\n".join(lines)


# --- --snapshot-only -------------------------------------------------------


@dataclass
class SnapshotResult:
    path: Path
    load: UniverseLoad
    outcome: price_step.FetchOutcome
    report: str


def snapshot_only(
    *,
    as_of: date,
    universe_dir: Path = UNIVERSE_DIR,
    tiers: Sequence[str] = ("A",),
    snapshot_root: Path = snapshot_store.SNAPSHOT_ROOT,
    batch_size: int = price_step.BATCH_SIZE,
    limit: int | None = None,
    period: str = DEFAULT_PERIOD,
    download=price_step.default_download,
    sleep=None,
    now: datetime | None = None,
    calendars_path: Path = CALENDARS_PATH,
) -> SnapshotResult:
    """Fetch and store, filter NOTHING. Report coverage and fetch status."""
    import time as _time

    sleep = sleep or _time.sleep
    load = _load(universe_dir, tiers)

    instruments = load.instruments[:limit] if limit else load.instruments
    tickers = [i.ticker_yahoo for i in instruments if i.ticker_yahoo]
    market_of = {i.ticker_yahoo: i.marknad for i in instruments if i.ticker_yahoo}

    # Item 3 / E47: the fetch-time STALE status counts sessions on the
    # exchange calendar of each row's market, as filter 1 does. The window
    # is a month back from the run date -- the gate only counts days after
    # the newest close, so earlier closed days are harmless.
    calendars = load_market_calendars(calendars_path)
    holidays_of: dict[str, frozenset[date]] = {}
    for ticker, market in market_of.items():
        closed = calendars.closed_weekdays(market, as_of - timedelta(days=31), as_of)
        if closed is not None:
            holidays_of[ticker] = closed

    def progress(index: int, total: int, size: int) -> None:
        log.info("batch %d/%d (%d tickers)", index, total, size)

    outcome = price_step.fetch_universe(
        tickers, as_of=as_of, period=period, batch_size=batch_size,
        download=download, sleep=sleep, on_batch=progress, holidays_of=holidays_of,
    )

    path = snapshot_store.snapshot_path(as_of, snapshot_root)
    snapshot_store.write(
        path,
        as_of=as_of,
        created_at=now or datetime.now(),
        instruments=instruments,
        tallies=list(load.tallies) + [outcome.tally],
        rejections=load.rejections,
        merges=load.merges,
        files=load.files,
        statuses=outcome.statuses,
        frames=outcome.frames,
        extra_manifest={
            "tiers": ",".join(t.upper() for t in tiers),
            "period": period,
            "auto_adjust": str(AUTO_ADJUST),
            "batch_size": batch_size,
            "tickers_requested": len(tickers),
            "limit": "" if limit is None else str(limit),
            "universe_dir": str(universe_dir),
        },
    )

    report = _snapshot_report(as_of, path, load, outcome, market_of, universe_dir, limit)
    return SnapshotResult(path=path, load=load, outcome=outcome, report=report)


def _snapshot_report(
    as_of: date,
    path: Path,
    load: UniverseLoad,
    outcome: price_step.FetchOutcome,
    market_of: dict[str, str],
    universe_dir: Path,
    limit: int | None,
) -> str:
    counts = price_step.status_counts(outcome.statuses)
    requested = len(outcome.statuses)
    lines = [_heading(f"SNAPSHOT  asof={as_of.isoformat()}  (fetch and store only, no filtering)")]

    lines.append(f"\n  file        {path}")
    lines.append(f"  size        {snapshot_store.snapshot_size(path):,} bytes")
    lines.append(f"  price rows  {sum(s.rows for s in outcome.statuses):,}")
    if limit:
        lines.append(f"  LIMIT       {limit} -- this is a partial run, not the universe")
        lines.append(
            "              A limit slices the DEDUPED universe in load order, which\n"
            "              depends on file discovery and dedup outcomes. A limited run\n"
            "              is a smoke test: it does not reproduce across a universe\n"
            "              rebuild, and the manifest records the count, not the names."
        )

    lines.append("\nYIELD -- rows in and out of every step")
    lines.append("  " + yield_table(list(load.tallies) + [outcome.tally]).replace("\n", "\n  "))
    lines.append("\n  rejections, split by whether a VALUE or its ABSENCE did it:")
    lines.append(reason_breakdown(list(load.tallies) + [outcome.tally]))

    lines.append("\nFETCH STATUS")
    for status in price_step.ALL_STATUSES:
        count = counts.get(status, 0)
        share = f"{count / requested:.1%}" if requested else "-"
        lines.append(f"  {status:<12}{count:>7}{share:>9}")
    lines.append(f"  {'TOTAL':<12}{requested:>7}")
    lines.append(
        "  THROTTLED and NO_DATA are separate on purpose: the first means retry\n"
        "  later, the second means the symbol mapping is wrong."
    )

    lines.append("\nCOVERAGE PER MARKET")
    header = f"  {'market':<22}" + "".join(f"{s:>11}" for s in price_step.ALL_STATUSES) + f"{'total':>8}"
    lines.append(header)
    lines.append("  " + THIN[: len(header) - 2])
    table = price_step.coverage_by_market(outcome.statuses, market_of)
    for market, row in sorted(table.items(), key=lambda kv: (-sum(kv[1].values()), kv[0])):
        total = sum(row.values())
        lines.append(
            f"  {market:<22}"
            + "".join(f"{row.get(s, 0):>11}" for s in price_step.ALL_STATUSES)
            + f"{total:>8}"
        )

    failed = [s for s in outcome.statuses if s.status != price_step.STATUS_OK]
    if failed:
        lines.append("\nEVERY TICKER THAT IS NOT OK (no ticker is ever silently dropped)")
        for item in failed[:40]:
            lines.append(
                f"  {item.ticker:<16}{item.status:<11}attempts={item.attempts}  "
                f"{(item.error or '')[:70]}"
            )
        if len(failed) > 40:
            lines.append(f"  ... and {len(failed) - 40} more, all stored in fetch_status")

    problems = snapshot_store.verify(path, universe_dir)
    lines.append("\nREPRODUCIBILITY")
    if problems:
        for problem in problems:
            lines.append(f"  PROBLEM  {problem}")
    else:
        lines.append("  ok: universe files hash as recorded, and no close is dated after asof")
    lines.append(
        f"  replay with: python -m vss screen --snapshot-only --asof {as_of.isoformat()}"
    )
    return "\n".join(lines)


# --- --filter1 -------------------------------------------------------------


@dataclass
class Filter1Run:
    as_of: date
    snapshot_date: date
    snapshot_path: Path
    load: UniverseLoad
    result: Filter1Result
    tallies: list
    report: str
    candidates_path: Path | None
    #: The settlement cutoff filter 1 was run with: the newest date whose
    #: bar was read as a settled close, struck from the snapshot's own
    #: `created_at` (item 2). None when the manifest carries no clock.
    settled: date | None = None
    created_at: datetime | None = None
    #: E51's step-0 second limb: what it removed, what it could not see and
    #: what the owner exempted. None only where the chain did not run it.
    circle: object | None = None
    #: E96's step-0 limb, beside E51's: the commodity-price outcome,
    #: so a removal is reported with its own ruling and never folded
    #: into E51's. Two grounds, two blocks, never one number.
    commodity: object | None = None


def settlement_cutoff(manifest: Mapping[str, str]) -> tuple[date | None, datetime | None]:
    """The settled-close cutoff the snapshot's OWN clock implies.

    The snapshot manifest records `created_at` -- the local time the fetch
    finished. `metrics.settled_through` turns that into the newest date
    whose bar had settled by then: New York's 16:00 is the last close of
    the day, so a snapshot taken before it demotes every bar of that date,
    the European ones included, for the reason `metrics.py` states -- one
    rule never wrong in the dangerous direction. The stamp is naive local
    time (`datetime.now()` at write time); it is read as this machine's
    zone, which is the zone it was written in.
    """
    stamp = manifest.get("created_at")
    if not stamp:
        return None, None
    try:
        created = datetime.fromisoformat(str(stamp))
    except ValueError:
        return None, None
    if created.tzinfo is None:
        created = created.astimezone()
    return settled_through(created), created


def pick_snapshot(as_of: date, root: Path) -> date:
    """The oldest snapshot that could contain ``as_of``.

    A snapshot dated on or after the evaluation date holds the closes that
    existed by then; one dated before it does not, and no amount of
    truncation invents them.
    """
    available = snapshot_store.available_snapshots(root)
    if not available:
        raise UniverseError(f"{root}: no snapshots. Run --snapshot-only first")
    usable = [d for d in available if d >= as_of]
    if not usable:
        raise UniverseError(
            f"the newest snapshot is {available[-1].isoformat()}, which is before "
            f"asof {as_of.isoformat()}; it cannot hold that day's closes"
        )
    return usable[0]


def filter1(
    *,
    as_of: date,
    universe_dir: Path = UNIVERSE_DIR,
    tiers: Sequence[str] = ("A",),
    snapshot_root: Path = snapshot_store.SNAPSHOT_ROOT,
    snapshot_date: date | None = None,
    exclusions_path: Path = EXCLUSIONS_PATH,
    pharma_biotech_path: Path = PHARMA_BIOTECH_PATH,
    commodity_price_path: Path = COMMODITY_PRICE_PATH,
    runs_root: Path | None = RUNS_ROOT,
    write_candidates: bool = True,
    calendars_path: Path = CALENDARS_PATH,
    db_path: Path = DB_PATH,
) -> Filter1Run:
    """Step 0 then filter 1, against a stored snapshot. No live fetch."""
    load = _load(universe_dir, tiers)
    exclusions = load_exclusions(exclusions_path)
    kept, exclusion_rejections, exclusion_tally, unmatched = apply_exclusions(
        load.instruments, exclusions
    )

    chosen = snapshot_date or pick_snapshot(as_of, snapshot_root)
    path = snapshot_store.snapshot_path(chosen, snapshot_root)

    # E51, step 0's second limb. The vendor's strings come out of the
    # fundamentals stores dated at or before the snapshot -- newest wins,
    # and a later-dated store is never read backwards (E49's rule). A
    # ticker in none of them carries NO string, and the outcome counts it:
    # fundamentals are fetched for the survivors of filter 1 alone, so most
    # of the universe is invisible to the string limb and the report says so.
    circle_config = load_circle_of_competence(pharma_biotech_path)
    # E96: the SECOND circle-of-competence limb, applied at the same step
    # and on the same instruments. Two files, two grounds, one mechanism.
    commodity_config = load_circle_of_competence(
        commodity_price_path, ruling="E96", label="commodity price",
        step=STEP_COMMODITY_PRICE)
    # THE STRING LIMB READS THE DURABLE TABLE FIRST (CODE-REVIEW-2026-09-01
    # D3). Until 2026-09-01 it read ONLY the dated fundamentals stores, which
    # E93's `prune_snapshots(keep=4)` deletes and whose fields E49's retention
    # does not carry forward -- so E96, whose owner ticker list is empty, had
    # a four-week half-life, and the ranked list was saved only by this
    # function being called a SECOND time after the fetch had rewritten the
    # store. That accident is no longer the mechanism.
    #
    # The stores are still laid over the table, oldest-first and newest-wins:
    # a machine whose data/vss.sqlite was replaced still gets what is on disk,
    # and a fresh fetch's strings reach step 0 in their own run.
    durable = vendorstrings.read(db_path, before=chosen)
    on_disk: list[tuple[date, dict]] = []
    for store in snapshot_store.earlier_fundamentals_stores(
            snapshot_root, before=chosen + timedelta(days=1)):
        try:
            day = date.fromisoformat(store.parent.name)
        except ValueError:                     # not a dated directory
            continue
        on_disk.append((day, snapshot_store.read_sector_strings(store)))
    strings = vendorstrings.merge_with_stores(durable, on_disk)
    sector_of = {t: v[0] for t, v in strings.items()}
    industry_of = {t: v[1] for t, v in strings.items()}
    circle = apply_circle_of_competence(
        kept, circle_config, sector_of=sector_of, industry_of=industry_of)
    kept = circle.kept
    commodity = apply_circle_of_competence(
        kept, commodity_config, sector_of=sector_of, industry_of=industry_of)
    kept = commodity.kept

    frames = snapshot_store.read_all_prices(
        path, [i.ticker_yahoo for i in kept if i.ticker_yahoo]
    )
    # Item 2: the same settlement cutoff `vss run` applies, struck from the
    # clock the SNAPSHOT was taken by rather than this run's -- the bars
    # are the snapshot's, so its clock is the one that says which of them
    # had settled.
    settled, created_at = settlement_cutoff(snapshot_store.read_manifest(path))
    # Item 3 / E47: the staleness gate counts sessions on the EXCHANGE
    # CALENDAR of the universe row's market. A market the config does not
    # map is counted Monday to Friday and named in the report.
    calendars = load_market_calendars(calendars_path)
    result = run_filter1(kept, frames, as_of, settled,
                         holidays_for=calendars.closed_weekdays)

    tallies = (list(load.tallies) + [exclusion_tally, circle.tally,
                                     commodity.tally]
               + list(result.tallies))
    candidates_path = None
    if write_candidates and runs_root is not None:
        candidates_path = _write_candidates(runs_root, as_of, result)

    report = _filter1_report(
        as_of, chosen, path, load, exclusions, unmatched, exclusion_rejections,
        result, tallies, universe_dir, candidates_path, settled, created_at,
        circle, pharma_biotech_path, commodity, commodity_price_path,
        db_path=db_path,
    )
    return Filter1Run(
        as_of=as_of, snapshot_date=chosen, snapshot_path=path, load=load,
        result=result, tallies=tallies, report=report,
        candidates_path=candidates_path, settled=settled, created_at=created_at,
        circle=circle,
        commodity=commodity,
    )


CANDIDATE_COLUMNS = (
    "ticker", "marknad", "namn", "last_close", "last_close_date", "high_52w",
    "high_52w_date", "drawdown",
    # E63: the other end of the same window, beside the drawdown. Fields.
    "low_52w", "low_52w_date", "pct_above_52w_low",
    # E127: the close a year ago and the return since -- filter 1 reads it.
    "close_year_ago", "close_year_ago_date", "return_12m",
    "b1", "rsi14", "sma50", "sma200", "pct_vs_sma50",
    "pct_vs_sma200", "volume_ratio",
)


def _write_candidates(runs_root: Path, as_of: date, result: Filter1Result) -> Path:
    import csv
    from dataclasses import asdict

    directory = runs_root / as_of.isoformat()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "filter1-candidates.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CANDIDATE_COLUMNS),
                                lineterminator="\n")
        writer.writeheader()
        for candidate in result.candidates:
            row = asdict(candidate)
            row["last_close_date"] = candidate.last_close_date.isoformat()
            row["high_52w_date"] = (candidate.high_52w_date.isoformat()
                                    if candidate.high_52w_date else "")
            row["low_52w_date"] = (candidate.low_52w_date.isoformat()
                                   if candidate.low_52w_date else "")
            row["close_year_ago_date"] = (candidate.close_year_ago_date.isoformat()
                                          if candidate.close_year_ago_date else "")
            writer.writerow({k: row[k] for k in CANDIDATE_COLUMNS})
    return path


def _fmt(value, spec: str, width: int) -> str:
    if value is None:
        return f"{'--':>{width}}"
    return f"{value:>{width}{spec}}"


def _filter1_report(
    as_of: date,
    snapshot_date: date,
    snapshot_path: Path,
    load: UniverseLoad,
    exclusions,
    unmatched,
    exclusion_rejections,
    result: Filter1Result,
    tallies,
    universe_dir: Path,
    candidates_path: Path | None,
    settled: date | None = None,
    created_at: datetime | None = None,
    circle=None,
    circle_path=None,
    commodity=None,
    commodity_path=None,
    pharma_biotech_path: Path = PHARMA_BIOTECH_PATH,
    commodity_price_path: Path = COMMODITY_PRICE_PATH,
    db_path: Path = DB_PATH,
) -> str:
    lines = [_heading(f"FILTER 1 -- DISLOCATION BAND  asof={as_of.isoformat()}")]
    lines.append(f"\n  snapshot        {snapshot_path}  (asof {snapshot_date.isoformat()})")
    if settled is not None and created_at is not None:
        demoted = sorted({c.last_close_date for c in result.candidates})
        lines.append(
            f"  settled through {settled.isoformat()}  -- the snapshot was taken "
            f"{created_at.strftime('%Y-%m-%d %H:%M %Z')}; a bar dated after that\n"
            f"                  cutoff is a live print and was DEMOTED, so every close\n"
            f"                  read here had settled by then (metrics.settled_through,\n"
            f"                  the same rule vss run applies). Candidate close dates: "
            f"{', '.join(d.isoformat() for d in demoted) or '-'}"
        )
    else:
        lines.append(
            "  settled through --  the snapshot manifest carries no clock, so no\n"
            "                  cutoff was declared: a bar of the run date may be a live\n"
            "                  print. DATA MISSING about the close's standing."
        )
    if snapshot_date != as_of:
        lines.append(
            f"  REPLAY          evaluating {as_of.isoformat()} from a snapshot taken\n"
            f"                  {snapshot_date.isoformat()}. Prices are truncated to the\n"
            f"                  evaluation date, so they are honest. The UNIVERSE is the\n"
            f"                  one that existed when the snapshot was built -- a name\n"
            f"                  added to an index since then is present, one removed is\n"
            f"                  absent. That is survivorship, and it is not corrected."
        )
    lines.append(f"  band            {DISLOCATION_MIN:.0%}-{DISLOCATION_MAX:.0%} inclusive, "
                 f"from rules.in_dislocation_band")
    lines.append(f"  staleness gate  {MAX_CLOSE_AGE_TRADING_DAYS} trading days ON THE "
                 f"EXCHANGE CALENDAR of each row's market (E47; config/exchange_calendars.yaml),\n"
                 f"                  from rules.stale_close_blocker")
    naive = getattr(result, "naive_calendar", {}) or {}
    if naive:
        named = ", ".join(f"{market} ({count})" for market, count in sorted(naive.items()))
        lines.append(
            f"                  NO CALENDAR for {named}: counted Monday to Friday, which\n"
            f"                  over-blocks after a holiday. Map the market in the config."
        )
    if candidates_path:
        lines.append(f"  candidates      {candidates_path}")

    lines.append("\nYIELD -- rows in and out of every step")
    lines.append("  " + yield_table(tallies).replace("\n", "\n  "))
    lines.append("\n  rejections, split by whether a VALUE or its ABSENCE did it:")
    lines.append(reason_breakdown(tallies))
    lines.append(
        "\n  Reading the two columns: on the DISLOCATION row, rej(missing) is\n"
        "  structurally near-zero rather than empirically zero. Everything reaching\n"
        "  that step cleared price_coverage and series_sanity, so it has a close\n"
        "  inside the 365-day window and its drawdown computes. Missing data shows\n"
        "  up on the two rows above it. Those numbers ARE empirical."
    )

    lines.append(_series_sanity_block(result))

    lines.append("\nSTEP 0 -- THE EXCLUSION LIST")
    lines.append(f"  {len(exclusions)} entries in the list, {len(exclusion_rejections)} matched a "
                 f"name in this universe")
    for rejection in exclusion_rejections:
        lines.append(f"      {rejection.key:<14}{rejection.reason}")
    if unmatched:
        lines.append(
            f"  {len(unmatched)} entries matched NOTHING and are inert here. An inert entry\n"
            "  that reads as active is how an excluded name quietly comes back:"
        )
        for entry in unmatched:
            lines.append(f"      {entry.ticker_yahoo:<14}{entry.skal} "
                         f"({entry.datum.isoformat()}) -- not in this universe/tier")

    # WHERE THE STRING LIMB'S INPUT CAME FROM, stated rather than assumed.
    # Both limbs below are only as good as this, and an EMPTY table means
    # E96 is not being applied at all (D3).
    lines.append("\nSTEP 0 -- THE VENDOR STRINGS THE TWO LIMBS BELOW READ")
    lines.extend(vendorstrings.describe(db_path))
    lines.append(_circle_block(
        circle, circle_path or PHARMA_BIOTECH_PATH, ruling="E51",
        subject="pharmaceuticals and biotech"))
    lines.append(_circle_block(
        commodity, commodity_path or COMMODITY_PRICE_PATH, ruling="E96",
        subject="a world price the company does not set"))
    lines.append(_listing_age_block(as_of, result))

    lines.append(f"\nCANDIDATES -- {len(result.candidates)} names inside the band")
    lines.append(
        "  Ordered by ticker. This is an ORDER, not a ranking: the ranking key is\n"
        "  phase 5, it is approved as text before it is coded, and nothing here\n"
        "  stands in for it. RSI, SMA and vs52wL are FIELDS -- none removed a name."
    )
    header = (f"  {'ticker':<14}{'market':<12}{'close':>9}{'52wH':>9}{'dd':>8}"
              f"{'vs52wL':>9}{'B1':>8}{'RSI':>7}{'vs SMA50':>10}{'vs SMA200':>11}")
    lines.append("")
    lines.append(header)
    lines.append("  " + THIN[: len(header) - 2])
    for candidate in result.candidates:
        lines.append(
            f"  {candidate.ticker:<14}{candidate.marknad:<12}"
            f"{candidate.last_close:>9.2f}{candidate.high_52w:>9.2f}"
            f"{candidate.drawdown:>8.1%}"
            + _fmt(candidate.pct_above_52w_low, ".1%", 9)
            + _fmt(candidate.b1, ".2f", 8)
            + _fmt(candidate.rsi14, ".1f", 7)
            + _fmt(candidate.pct_vs_sma50, ".1%", 10)
            + _fmt(candidate.pct_vs_sma200, ".1%", 11)
        )
    lines.append(
        "\n  vs52wL is FRAMEWORK-EDITS E63: how far the close sits ABOVE its own\n"
        "  52-week closing low, (close - low) / low, on the same window and the\n"
        "  same coverage bar as the high. The band cannot tell a name that fell\n"
        "  and stayed down from one that has since recovered; this column can. A\n"
        "  FIELD -- reported, never applied; B41 is decided (E127): no threshold\n"
        "  on the low. Filter 1 reads the 12-month return instead, the step\n"
        "  trailing_year. The low and its date are in the CSV."
    )
    lines.append(
        "\n  B1 is FRAMEWORK-EDITS B1, reported as CONTEXT: the share of the\n"
        "  peak-to-current decline that happened in the trailing 180 days. Per B1\n"
        "  as decided 2026-08-22, Gate 1 measures today's position and this number\n"
        "  does not by itself fail it. '--' means there was no close old enough to\n"
        "  compare against, or the close IS the 52-week high."
    )

    problems = snapshot_store.verify(snapshot_path, universe_dir)
    lines.append("\nREPRODUCIBILITY")
    if problems:
        for problem in problems:
            lines.append(f"  PROBLEM  {problem}")
    else:
        lines.append("  ok: universe files hash as recorded, and no close is dated after "
                     "the snapshot's asof")
    lines.append(
        "  This run fetched nothing. Re-running it against the same snapshot and the\n"
        "  same universe files reproduces this candidate list exactly."
    )
    lines.append(
        "\nNOT DONE HERE: no ranking, no fundamentals, no watchlist write. Filter 2\n"
        "is phase 3, the ranking key is phase 5, PIPELINE writing is phase 6."
    )
    return "\n".join(lines)



def _circle_block(circle, path: Path, *, ruling: str = "E51",
                  subject: str = "pharmaceuticals and biotech") -> str:
    """One STEP 0 circle-of-competence limb -- E51's or E96's.

    BOTH ARE PRINTED, ALWAYS AND SEPARATELY. A name removed because its
    revenue is a world price must never read as a name removed for a
    clinical trial: they are different grounds, and this block is all a
    reader months later has to tell them apart."""
    lines = [f"\nSTEP 0 -- THE CIRCLE OF COMPETENCE ({ruling}): {subject}"]
    if circle is None:
        lines.append(f"  NOT RUN in this chain; nothing was removed "
                     f"on {ruling}'s ground.")
        return "\n".join(lines)
    ground = {
        "E51": ("  Pharmaceuticals and biotech: a company whose cash flow beyond the "
                "next\n  patent expiry depends on clinical trial outcomes and "
                "regulatory approval.\n  Section 5 cannot be run on it -- the "
                "pre-registered growth rate E28 asks\n  for would be a guess about "
                "drug approvals."),
        "E96": ("  A world price the company does not set, times a volume: for a price "
                "taker\n  the BEAR CASE IS NOT SLOWER GROWTH BUT A HALVED PRICE, which "
                "is a different\n  cash flow and not a lower g on the same one. Section "
                "5 discounts a durable\n  free cash flow such a company does not have. "
                "NOT a judgement about the\n  industry -- a limit of the method."),
    }.get(ruling, f"  {subject}")
    lines.append(
        f"{ground} Applies regardless of rank.\n"
        f"  The list that decides: {path}"
    )
    lines.append(f"\n  {len(circle.hits)} name(s) removed:")
    for hit in circle.hits:
        namn = (hit.namn or "")[:34]
        lines.append(f"      {hit.ticker:<14}{namn:<36}{hit.limb}: {hit.detail}")
    if not circle.hits:
        lines.append("      (none)")
    if circle.exempted:
        lines.append(
            f"\n  {len(circle.exempted)} name(s) the STRING limb caught and the owner "
            f"ruled back IN:"
        )
        for hit in circle.exempted:
            lines.append(f"      {hit.ticker:<14}{hit.detail}")
    if circle.unmatched:
        lines.append(
            f"\n  {len(circle.unmatched)} ticker(s) on the owner's list matched NOTHING "
            f"here and are inert:"
        )
        lines.append("      " + ", ".join(circle.unmatched))
    lines.append(
        f"\n  WHAT THE STRING LIMB COULD NOT SEE: {circle.without_string} of the "
        f"{circle.tally.count_in} names\n"
        "  offered to this step carry NO stored sector or industry string. Fundamentals\n"
        "  are fetched for the survivors of filter 1 ALONE, so most of the universe has\n"
        "  never been classified by the vendor at all. The limb's silence about those\n"
        "  names is a fact about the FETCH, not a finding that they are in the circle.\n"
        "  The owner's ticker list is the limb that does not depend on it."
    )
    return "\n".join(lines)


def _listing_age_block(as_of: date, result: Filter1Result) -> str:
    """FILTER 1's first step -- FRAMEWORK-EDITS E52, the listing-age floor."""
    from .filters import STEP_LISTING_AGE
    from .metrics import LISTING_AGE_YEARS, coverage_start, listing_age_start

    rejected = [r for r in result.rejections if r.step == STEP_LISTING_AGE]
    floor = listing_age_start(as_of)
    lines = [f"\nFILTER 1, STEP 1 -- THE LISTING-AGE FLOOR (E52)"]
    lines.append(
        f"  {len(rejected)} name(s) rejected ON MISSING DATA: the stored price series\n"
        f"  does not reach back {LISTING_AGE_YEARS} years, to {floor.isoformat()}. Not enough\n"
        f"  reported history to judge -- the name did not FAIL a limb, the limbs could\n"
        f"  not be evaluated on it. Measured on the oldest bar the SNAPSHOT carries,\n"
        f"  never on the universe CSV's listdatum, which is empty on most rows."
    )
    lines.append(
        f"\n  Against the 52-week coverage bar at {coverage_start(as_of).isoformat()} "
        f"(metrics.py:76-77): same\n"
        f"  quantity, same axis, longer demand. Every series failing that bar fails\n"
        f"  this one, and not the reverse. The bar is NOT deleted -- it governs what\n"
        f"  high_52w MEANS inside metrics.compute, which `vss run` reaches without\n"
        f"  passing filter 1 at all."
    )
    return "\n".join(lines)


def _series_sanity_block(result: Filter1Result) -> str:
    """K4: what the price-series check refused, by name and with the evidence.

    Named, never counted only. A data problem that grows can hide inside a
    column; it cannot hide inside a list of tickers and dates.
    """
    findings = list(getattr(result, "unmeasurable", []))
    lines = ["\nSERIES SANITY -- can the drawdown be measured at all?"]
    lines.append(
        f"  Two checks over the trailing {series_sanity.LOOKBACK_DAYS} days, the same\n"
        f"  window the 52-week high reads.\n"
        f"    scale switch    a move beyond {series_sanity.JUMP_FACTOR:.2f}x answered within\n"
        f"                    {series_sanity.ROUND_TRIP_WINDOW_DAYS} days by its near-reciprocal. A corporate\n"
        f"                    action happens ONCE; a feed quoting two scales goes back.\n"
        f"    uncorroborated  a move beyond {series_sanity.JUMP_FACTOR:.2f}x on under\n"
        f"                    {series_sanity.CORROBORATING_VOLUME_MULTIPLE:.0f}x the name's own median volume. A repricing of\n"
        f"                    that size trades; a split, a spin-off or a mis-scaled row\n"
        f"                    does not. Either way the high on the far side of the break\n"
        f"                    is not comparable with today's close."
    )
    lines.append(
        "  A flagged name is rejected ON MISSING DATA, never on value. It did not\n"
        "  fail the band -- the band could not be evaluated for it."
    )
    if not findings:
        lines.append("\n      nothing flagged on this run")
        return "\n".join(lines)
    lines.append(f"\n  {len(findings)} series refused:")
    for ticker, finding in findings:
        lines.append(f"      {ticker:<14}{finding.kind}")
        lines.append(f"           {finding.detail}")
    return "\n".join(lines)


# --- --fundamentals --------------------------------------------------------


@dataclass
class FundamentalsRun:
    as_of: date
    path: Path
    survivors: list
    outcome: fundamentals_step.FundamentalsOutcome
    report: str


def fetch_fundamentals(
    *,
    as_of: date,
    universe_dir: Path = UNIVERSE_DIR,
    tiers: Sequence[str] = ("A",),
    snapshot_root: Path = snapshot_store.SNAPSHOT_ROOT,
    snapshot_date: date | None = None,
    exclusions_path: Path = EXCLUSIONS_PATH,
    limit: int | None = None,
    reader=fundamentals_step.default_reader,
    sleep=None,
    now: datetime | None = None,
    db_path: Path = DB_PATH,
) -> FundamentalsRun:
    """Fetch fundamentals for the survivors of filter 1, and only those.

    The survivor list is recomputed from the stored snapshot rather than read
    from a file, so this cannot drift out of step with the filter that
    produced it.
    """
    import time as _time

    sleep = sleep or _time.sleep
    upstream = filter1(
        as_of=as_of, universe_dir=universe_dir, tiers=tiers,
        snapshot_root=snapshot_root, snapshot_date=snapshot_date,
        exclusions_path=exclusions_path, write_candidates=False,
        db_path=db_path,
    )
    survivors = upstream.result.candidates
    if limit:
        survivors = survivors[:limit]
    tickers = [c.ticker for c in survivors]

    def progress(index: int, total: int, record) -> None:
        if index % 25 == 0 or record.status != price_step.STATUS_OK:
            log.info("fundamentals %d/%d %s %s", index, total, record.ticker,
                     record.status)

    outcome = fundamentals_step.fetch_many(
        tickers, as_of=as_of, reader=reader, sleep=sleep,
        on_progress=progress, now=now,
    )

    path = snapshot_store.fundamentals_path(upstream.snapshot_date, snapshot_root)
    # E49: the store retains. Every earlier-dated store under the root is
    # carried in first, then this fetch is written over it -- a period the
    # vendor served once stays until the vendor serves it again.
    retain_from = snapshot_store.earlier_fundamentals_stores(
        snapshot_root, before=upstream.snapshot_date
    )
    snapshot_store.write_fundamentals(
        path, as_of=upstream.snapshot_date,
        fetched_at=outcome.fetched_at or datetime.now(),
        records=outcome.records, requests=outcome.requests,
        extra_manifest={
            "filter1_asof": as_of.isoformat(),
            "requests_per_ticker": fundamentals_step.REQUESTS_PER_TICKER,
            "limit": "" if limit is None else str(limit),
        },
        retain_from=retain_from,
    )
    # THE STRINGS GO SOMEWHERE PRUNING CANNOT REACH (D3). This is the only
    # moment they exist: an E51/E96 name is never a filter-1 survivor, so it
    # is never fetched again, so a string not kept now is a string lost when
    # this store is pruned four runs from here. E49 retains SERIES rows
    # between stores and not FIELDS, which is why the store itself does not
    # carry it forward.
    recorded = 0
    try:
        recorded = vendorstrings.record(
            db_path,
            {r.ticker: (r.text("sector"), r.text("industry"))
             for r in outcome.records},
            observed=upstream.snapshot_date)
    except Exception as exc:  # noqa: BLE001 -- reported below, never fatal
        log.warning("vendor strings not recorded (%s: %s); E51/E96's string "
                    "limb will fall back to the pruned stores",
                    type(exc).__name__, exc)
    report = _fundamentals_report(as_of, path, upstream, outcome, limit,
                                  retain_from, db_path=db_path,
                                  strings_recorded=recorded)
    return FundamentalsRun(as_of=as_of, path=path, survivors=survivors,
                           outcome=outcome, report=report)


def _fundamentals_report(as_of, path, upstream, outcome, limit,
                         retain_from: Sequence[Path] = (),
                         db_path: Path = DB_PATH,
                         strings_recorded: int = 0) -> str:
    records = outcome.records
    total = len(records)
    lines = [_heading(f"FUNDAMENTALS FETCH  filter-1 survivors  asof={as_of.isoformat()}")]
    lines.append(f"\n  store           {path}")
    lines.append(f"  tickers         {total} (the survivors of filter 1)")
    lines.append(f"  requests        {outcome.requests} "
                 f"({fundamentals_step.REQUESTS_PER_TICKER} per ticker: the quote "
                 f"summary, the annual income statement and balance sheet, and the\n"
                 f"                  quarterly income statement and balance sheet -- E13's "
                 f"four quarters, item 8)")
    fetched = outcome.fetched_at.isoformat(timespec="seconds") if outcome.fetched_at else "-"
    lines.append(f"  fetched at      {fetched}")
    if limit:
        lines.append(f"  LIMIT           {limit} -- a partial run, not the survivor list")

    lines.append("\n" + _look_ahead_block(as_of, outcome))

    counts = fundamentals_step.status_counts(records)
    lines.append("\nFETCH STATUS PER TICKER")
    for status in (price_step.STATUS_OK, price_step.STATUS_THROTTLED,
                   price_step.STATUS_NO_DATA, price_step.STATUS_STALE):
        count = counts.get(status, 0)
        share = f"{count / total:.1%}" if total else "-"
        lines.append(f"  {status:<12}{count:>7}{share:>9}")
    lines.append(f"  {'TOTAL':<12}{total:>7}")

    attempts = sum(r.attempts for r in records)
    retried = [r for r in records if r.attempts > 1]
    lines.append(f"\n  attempts {attempts} for {total} tickers; "
                 f"{len(retried)} needed a retry")
    if retried:
        for record in retried[:15]:
            lines.append(f"      {record.ticker:<14}attempts={record.attempts}  "
                         f"{(record.error or 'recovered')[:60]}")
    else:
        lines.append("      the retry and backoff path did not fire on this run")

    lines.append("\nFIELD COVERAGE -- a ticker counted OK can still be missing the one")
    lines.append("field a limb needs, so coverage is reported per FIELD, not per ticker.")
    header = f"  {'field':<22}{'OK':>8}{'NO_DATA':>10}{'THROTTLED':>11}{'covered':>10}"
    lines.append("")
    lines.append(header)
    lines.append("  " + THIN[: len(header) - 2])
    coverage = fundamentals_step.field_coverage(records)
    for name in fundamentals_step.ALL_FIELDS:
        row = coverage.get(name, {})
        ok = row.get(fundamentals_step.FIELD_OK, 0)
        lines.append(
            f"  {name:<22}{ok:>8}{row.get(fundamentals_step.FIELD_NO_DATA, 0):>10}"
            f"{row.get(fundamentals_step.FIELD_THROTTLED, 0):>11}"
            + (f"{ok / total:>10.1%}" if total else f"{'-':>10}")
        )

    lines.append("\nANNUAL REVENUE POINTS PER TICKER (the revenue limb's annual fallback)")
    for count, names in fundamentals_step.series_coverage(records).items():
        lines.append(f"  {count} year(s){'':<8}{names:>6} tickers")
    lines.append("\nQUARTERLY REVENUE POINTS PER TICKER, THIS FETCH (E13's basis and E45's")
    lines.append("kill; 0 is a half-yearly reporter or an empty quarterly endpoint -- yfinance")
    lines.append("#1345 -- and a hole inside the four newest is DATA MISSING for the basis,")
    lines.append("never zero)")
    for count, names in fundamentals_step.quarterly_coverage(records).items():
        lines.append(f"  {count} quarter(s){'':<5}{names:>6} tickers")

    lines.append("\n" + _retention_block(path, retain_from))
    # D3: what this fetch put somewhere pruning cannot reach.
    lines.append("\nVENDOR STRINGS KEPT FOR E51 / E96")
    lines.append(f"  recorded        {strings_recorded} ticker(s) from this "
                 f"fetch into {db_path}")
    lines.extend(vendorstrings.describe(db_path))

    sectors: dict[str, int] = {}
    for record in records:
        sectors[record.text("sector") or "(no sector)"] = (
            sectors.get(record.text("sector") or "(no sector)", 0) + 1
        )
    lines.append("\nSECTOR, AS THE SOURCE REPORTS IT")
    lines.append("  Relevant because FRAMEWORK Gate 3 excludes financials from the")
    lines.append("  net-debt/EBITDA limb, and a machine needs a discriminator for that.")
    for sector, count in sorted(sectors.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {sector:<30}{count:>6}")

    no_ebitda = [r for r in records
                 if r.status == price_step.STATUS_OK and r.value("ebitda") is None]
    fin_no_ebitda = [r for r in no_ebitda if (r.text("sector") or "") == "Financial Services"]
    lines.append(f"\n  tickers with no EBITDA at all: {len(no_ebitda)}, of which "
                 f"{len(fin_no_ebitda)} are Financial Services")
    other = sorted({r.text("sector") or "(no sector)" for r in no_ebitda}
                   - {"Financial Services"})
    if other:
        lines.append(f"  the rest sit in: {', '.join(other)}")

    lines.append(
        "\nCURRENCY: financialCurrency differs from the quote currency for some names\n"
        "(Equinor reports USD, trades NOK). Every filter 2 limb is a sign or a ratio\n"
        "of two figures from the same statement, so the currency cancels and phase 3\n"
        "needs no FX source. Tier C's floors still do -- they compare against an\n"
        "absolute amount."
    )
    lines.append(
        "\nNOT DONE HERE: filter 2 has not run. Its thresholds are a PROPOSAL awaiting\n"
        "the owner's decision -- see config/screener_filter2.yaml."
    )
    return "\n".join(lines)


def _retention_block(path: Path, retain_from: Sequence[Path]) -> str:
    """What the store holds AFTER this write (FRAMEWORK-EDITS E49)."""
    summary = snapshot_store.fundamentals_store_summary(path)
    lines = ["RETENTION (E49) -- the store keeps every period it has ever fetched"]
    lines.append(
        "  A write never unlinks the store. A period this fetch returned replaced\n"
        "  the stored one; a period it did not return stayed, stamped with the fetch\n"
        "  that supplied it; a hole never overwrote a figure. Earlier-dated stores\n"
        "  under the same root were carried in first, so E45's eight-quarter window\n"
        "  fills over time from a vendor that serves five."
    )
    if retain_from:
        lines.append(f"  carried in from  {len(retain_from)} earlier store(s): "
                     + ", ".join(p.parent.name for p in retain_from))
    else:
        lines.append("  carried in from  no earlier store under this root")
    lines.append(f"  fetches held     {len(summary['fetches'])} "
                 f"(first {summary['first_fetched_at'] or '-'}, latest {summary['fetched_at'] or '-'})")
    lines.append(f"  tickers          {summary['tickers']} with a status row from some fetch")
    lines.append(f"  series rows      {summary['series_rows']}")
    for stamp, count in summary["rows_by_fetch"].items():
        lines.append(f"      {stamp or '(unstamped)':<22}{count:>8} rows")
    only = summary["series_only_tickers"]
    if only:
        lines.append(
            f"  {len(only)} ticker(s) carry series and no status row -- periods carried in\n"
            f"  for a name this store's fetch never visited. The chain does not see them\n"
            f"  until a fetch does: "
            + ", ".join(only[:12]) + (" ..." if len(only) > 12 else "")
        )
    stored = snapshot_store.read_fundamentals(path)
    lines.append("\n  QUARTERLY REVENUE POINTS PER TICKER, THE STORE AFTER RETENTION")
    for count, names in fundamentals_step.quarterly_coverage(stored).items():
        lines.append(f"    {count} quarter(s){'':<5}{names:>6} tickers")
    return "\n".join(lines)


def _look_ahead_block(as_of: date, outcome) -> str:
    fetched = outcome.fetched_at.date() if outcome.fetched_at else None
    stamp = fetched.isoformat() if fetched else "the fetch date"
    warning = [
        "  " + "!" * 74,
        "  LOOK-AHEAD WARNING -- READ BEFORE INTERPRETING ANY FILTER 2 RESULT",
        "  " + "!" * 74,
        "  yfinance serves historical PRICES but only the LATEST fundamentals. There",
        f"  is no as-of-date on the figures below: they are the accounts as published",
        f"  by {stamp}, whatever date this run is labelled with.",
        "",
        "  TWO OF THESE 'FUNDAMENTALS' CARRY A PRICE. marketCap is the vendor's",
        f"  share count at its {stamp} quote (regularMarketPrice, stored beside it),",
        "  and enterpriseValue is a precomputed figure the vendor refreshes on its",
        "  own cadence -- measured on 2026-08-26, it embedded closes from June for",
        "  eleven of the twenty head names. The ranking reads NEITHER as a price:",
        "  it recovers the share count from marketCap / regularMarketPrice and",
        "  re-prices it at the SETTLED close of the run date; enterpriseValue is",
        "  a memo column and decides nothing. totalDebt and totalCash are the",
        f"  vendor's latest balance sheet as of {stamp}, and that date is written",
        "  beside them in ranking.csv.",
    ]
    if fetched and fetched != as_of:
        warning.append(
            f"  This run pairs fundamentals as of {stamp} with the price of "
            f"{as_of.isoformat()}."
        )
        warning.append(
            "  A name that looks like a filter 2 pass here may have been failing on the"
        )
        warning.append(
            "  accounts that actually existed on the price date, and the reverse. The"
        )
        warning.append(
            "  result is therefore NOT evidence about what a screener would have found"
        )
        warning.append(
            "  on that day. No retroactive reading may be placed on it."
        )
    else:
        warning.append(
            "  Fundamentals and price carry the same date on this run, so the pairing"
        )
        warning.append(
            "  is contemporaneous. Any REPLAY of an earlier date is not."
        )
    warning.append("  " + "!" * 74)
    return "\n".join(warning)


# --- --filter2 -------------------------------------------------------------


@dataclass
class Filter2Run:
    as_of: date
    upstream: Filter1Run
    result: object
    report: str


def filter2(
    *,
    as_of: date,
    universe_dir: Path = UNIVERSE_DIR,
    tiers: Sequence[str] = ("A",),
    snapshot_root: Path = snapshot_store.SNAPSHOT_ROOT,
    snapshot_date: date | None = None,
    exclusions_path: Path = EXCLUSIONS_PATH,
    config_path: Path = FILTER2_CONFIG_PATH,
    runs_root: Path | None = RUNS_ROOT,
    db_path: Path = DB_PATH,
) -> Filter2Run:
    """The whole chain: step 0, filter 1, filter 2. Fetches nothing."""
    upstream = filter1(
        as_of=as_of, universe_dir=universe_dir, tiers=tiers,
        snapshot_root=snapshot_root, snapshot_date=snapshot_date,
        exclusions_path=exclusions_path, runs_root=runs_root,
        write_candidates=False, db_path=db_path,
    )
    config = load_filter2_config(config_path)
    store_path = snapshot_store.fundamentals_path(upstream.snapshot_date, snapshot_root)
    if not store_path.exists():
        raise UniverseError(
            f"{store_path}: no fundamentals stored. "
            f"Run --fundamentals --asof {as_of.isoformat()} first"
        )
    records = snapshot_store.read_fundamentals(store_path)
    manifest = snapshot_store.read_fundamentals_manifest(store_path)
    by_ticker = {r.ticker: r for r in records}
    result = run_filter2(upstream.result.candidates, by_ticker, config)

    candidates_path = None
    if runs_root is not None:
        candidates_path = _write_filter2_candidates(runs_root, as_of, result)

    report = _filter2_report(as_of, upstream, result, manifest, store_path,
                             config_path, candidates_path, by_ticker)
    return Filter2Run(as_of=as_of, upstream=upstream, result=result, report=report)


FILTER2_COLUMNS = ("ticker", "marknad", "last_close", "drawdown", "rsi14",
                   "fcf", "leverage", "revenue_trend", "detail")


def _write_filter2_candidates(runs_root: Path, as_of: date, result) -> Path:
    import csv

    directory = runs_root / as_of.isoformat()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "filter2-candidates.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FILTER2_COLUMNS),
                                lineterminator="\n")
        writer.writeheader()
        for candidate in result.survivors:
            verdict = result.assessed[candidate.ticker]
            writer.writerow({
                "ticker": candidate.ticker, "marknad": candidate.marknad,
                "last_close": candidate.last_close, "drawdown": candidate.drawdown,
                "rsi14": candidate.rsi14,
                "fcf": verdict.state(LIMB_FCF),
                "leverage": verdict.state(LIMB_LEVERAGE),
                "revenue_trend": verdict.state(LIMB_REVENUE),
                "detail": " | ".join(f"{l.name}: {l.detail}" for l in verdict.limbs),
            })
    return path


def _filter2_report(as_of, upstream, result, manifest, store_path, config_path,
                    candidates_path, records) -> str:
    config = result.config
    lines = [_heading(f"FILTER 2 -- COARSE QUALITY  asof={as_of.isoformat()}")]

    if not config.decided:
        lines.append(
            "\n  " + "*" * 74 +
            f"\n  THRESHOLDS ARE A PROPOSAL. {config_path} carries status "
            f"{config.status}\n"
            f"  (proposed {config.proposed}), which the owner has not decided. Every\n"
            "  number below is provisional and this run is not a result -- it is what\n"
            "  the proposed values would do.\n  " + "*" * 74
        )

    lines.append(f"\n  price snapshot   {upstream.snapshot_path}")
    lines.append(f"  fundamentals     {store_path}")
    lines.append(f"  config           {config_path}  [{config.status}]")
    if candidates_path:
        lines.append(f"  survivors        {candidates_path}")

    lines.append("\n" + _filter2_look_ahead(as_of, manifest))

    lines.append("\nSURVIVOR SET AGAINST THE STORE")
    lines.append(f"  {len(result.assessed)} names entered filter 2; the fundamentals store "
                 f"holds {result.store_size}.")
    if result.not_fetched:
        lines.append(
            f"  {len(result.not_fetched)} have NO record in it -- they were never fetched,\n"
            "  which is a fact about the fetch and not about the company. Re-run\n"
            "  --fundamentals: the universe or the exclusion list has changed since."
        )
        for ticker in result.not_fetched[:20]:
            lines.append(f"      {ticker}")
    else:
        lines.append("  Every name entering filter 2 has a record. No drift.")

    lines.append("\nTHRESHOLDS IN FORCE (from the config, never hardcoded)")
    if config.decided:
        lines.append(f"  decided {config.raw.get('decided')} -- see FRAMEWORK-EDITS E2, E3, E4; "
                     f"the leverage cap as amended by E44 (2026-08-26)")
    lines.append(f"  {LIMB_FCF:<22}TTM free cash flow > {config.fcf_min:,.0f}")
    lines.append(f"  {LIMB_LEVERAGE:<22}net debt/EBITDA <= {config.leverage_max}x, "
                 f"NOT APPLICABLE for {', '.join(sorted(config.leverage_na_sectors))}")
    lines.append(f"  {LIMB_REVENUE:<22}{config.revenue_kill_action} at "
                 f"{config.revenue_kill_after} consecutive quarterly YoY declines from "
                 f"the newest of {config.revenue_quarters} quarters (4.2.1, E45); "
                 f"annual fallback {config.revenue_action} at "
                 f"{config.revenue_flag_after} consecutive annual declines over "
                 f"{config.revenue_lookback_years} years")
    lines.append(f"  {'missing data':<22}{config.on_missing_action}")

    tallies = list(upstream.tallies) + [result.tally]
    lines.append("\nYIELD -- rows in and out of every step")
    lines.append("  " + yield_table(tallies).replace("\n", "\n  "))
    lines.append("\n  rejections, split by whether a VALUE or its ABSENCE did it:")
    lines.append(reason_breakdown(tallies))

    lines.append("\nPER LIMB")
    header = (f"  {'limb':<22}{'PASS':>8}{'FAIL':>8}{'MISSING':>10}"
              f"{'N/A':>8}{'FLAG':>8}")
    lines.append("")
    lines.append(header)
    lines.append("  " + THIN[: len(header) - 2])
    matrix = limb_matrix(result.assessed)
    for name in (LIMB_FCF, LIMB_LEVERAGE, LIMB_REVENUE):
        row = matrix[name]
        lines.append(
            f"  {name:<22}{row[PASS]:>8}{row[FAIL]:>8}{row[DATA_MISSING]:>10}"
            f"{row[NOT_APPLICABLE]:>8}{row[FLAG]:>8}"
        )
    lines.append(
        "\n  ON THE FCF LIMB, WHAT A PASS MEANS. FRAMEWORK Gate 3 asks for free cash\n"
        "  flow positive in at least 6 of 8 quarters. That test is not computable\n"
        "  from this source -- quarterly cash-flow history comes back with 5 to 7\n"
        "  columns for most names and none at all for some -- so the limb tests the\n"
        "  sign of trailing-twelve-month free cash flow instead. Therefore:\n"
        "\n"
        "      a name passing here has NOT passed Gate 3's FCF limb. It has failed\n"
        "      to fail it, on one year rather than eight quarters.\n"
        "\n"
        "  The manual chain still runs the real test."
    )
    lines.append(
        f"\n  ON THE LEVERAGE LIMB, WHICH CAP. This filter rejects above Gate 3's own\n"
        f"  {config.leverage_max}x, per FRAMEWORK-EDITS E44 (2026-08-26), which amends E2's\n"
        "  choice of 4.2.5's 3.5x hard kill: the screener FEEDS Gate 3, and a name\n"
        "  at 3.3x fails the hand chain regardless -- 72 names passed at 3.5x and\n"
        "  failed the framework's own number on 2026-08-26, FGR.PA and AFRY.ST\n"
        "  among them. The ratio is the vendor's net debt over the vendor's EBITDA,\n"
        "  a coarse reading of the gate and not the gate; the number is printed\n"
        "  with every rejection so the owner can override it by hand in section 3."
    )
    untested = [t for t, v in result.assessed.items() if v.untested]
    survived_untested = [c.ticker for c in result.survivors
                         if result.assessed[c.ticker].untested]
    lines.append(
        "\n  MISSING is the column that decides whether this filter is measuring the\n"
        "  market or its own coverage. A name there was NOT tested and was NOT\n"
        "  failed; under on_missing_action=" + config.on_missing_action + " it "
        + ("passes through, marked." if config.on_missing_action == "pass_through"
           else "is dropped, counted apart.")
    )
    lines.append(
        f"\n  THE COUNTERFACTUAL, so the choice can be checked against a number:\n"
        f"  {len(untested)} of the {len(result.assessed)} names entering filter 2 carry at least\n"
        f"  one untested limb. Of the {len(result.survivors)} survivors, {len(survived_untested)} "
        f"are here with a limb\n"
        f"  that could not be evaluated -- under on_missing_action=reject those "
        f"{len(survived_untested)}\n"
        f"  would have been dropped on the source's coverage rather than on anything\n"
        f"  the company did. FRAMEWORK-EDITS E4 is the decision that they are not."
    )
    listed = sorted(t for t, v in result.assessed.items()
                    if any(l.name == LIMB_LEVERAGE and "E46" in l.detail for l in v.limbs))
    inert = sorted(config.investment_companies - set(result.assessed))
    lines.append(
        "  N/A is neither: FRAMEWORK Gate 3 excludes financials from the leverage\n"
        "  limb and sends the analyst to sector norms, which a machine has none of,\n"
        "  and FRAMEWORK-EDITS E3 adds Real Estate on the same logic -- property is\n"
        "  borrowed against asset value, not against EBITDA. The precedent for a\n"
        "  third outcome is B7. FRAMEWORK-EDITS E46 adds the owner's LIST of\n"
        f"  investment companies ({len(config.investment_companies)} tickers in\n"
        "  config/screener_investment_companies.yaml), which decides whatever the\n"
        f"  vendor's string says: {len(listed)} of them entered filter 2 here"
        + (f" ({', '.join(listed)})." if listed else ".")
    )
    if inert:
        lines.append(
            f"  {len(inert)} listed tickers are not among this run's entrants (outside the\n"
            f"  band, or not in the universe) and were inert here: {', '.join(inert)}"
        )
    lines.append(
        "  THE REVENUE LIMB KILLS ON QUARTERS (FRAMEWORK 4.2.1 as written, per\n"
        "  FRAMEWORK-EDITS E45): two or more consecutive year-on-year declines\n"
        "  counted from the newest quarter FAIL the name on value, and the changes\n"
        "  are printed. Where the vendor has no quarters for a name -- a half-yearly\n"
        "  reporter, an empty endpoint, a hole at the newest end -- the limb reads\n"
        "  the ANNUAL series and there only FLAGS (B9's reading), and the detail\n"
        "  says which basis it read. B9's organic carve-out (UNA.AS: four reported\n"
        "  declines, organic growth in all eight) governs the hand chain; the\n"
        "  screener cannot read the organic series, and E45 states that cost."
    )

    stale = sorted(
        (t, records[t]) for t in result.assessed
        if t in records and records[t].status == price_step.STATUS_STALE
    )
    if stale:
        lines.append(
            f"\nSTALE ANNUAL STATEMENTS -- {len(stale)} names\n"
            "  The quote summary's figures are current for these, so the FCF and\n"
            "  leverage limbs are measured on today's numbers. The revenue-trend limb\n"
            "  reads the annual statement and is therefore measured on an older\n"
            "  window.\n"
            "  THIS PARAGRAPH USED TO STOP AT 'only the revenue-trend limb reads the\n"
            "  annual statement'. Phase 5 made that untrue: the ENTIRE ranking key --\n"
            "  gross profit, total assets and EBIT -- is read from the same annual\n"
            "  statement. Since 2026-08-22 a STALE name is EXCLUDED from the ranking\n"
            "  outright (K5), so it survives filter 2 and is then not ranked. It is\n"
            "  passed through here rather than dropped because filter 2's own limbs\n"
            "  are mostly measured on current figures, and the decision belongs at\n"
            "  the step that would use the old ones. Named rather than netted away:"
        )
        for ticker, record in stale:
            period = record.newest_period.isoformat() if record.newest_period else "?"
            lines.append(f"      {ticker:<14}newest annual period {period}")

    survivors = result.survivors
    lines.append(f"\nSURVIVORS -- {len(survivors)} names")
    lines.append(
        "  Ordered by ticker. An ORDER, not a ranking. No fair value, no buy price,\n"
        "  nothing written to the watchlist."
    )
    header = (f"  {'ticker':<14}{'market':<12}{'dd':>8}{'RSI':>7}  "
              f"{'fcf':<13}{'leverage':<15}{'revenue':<14}")
    lines.append("")
    lines.append(header)
    lines.append("  " + THIN[: len(header) - 2])
    for candidate in survivors[:60]:
        verdict = result.assessed[candidate.ticker]
        lines.append(
            f"  {candidate.ticker:<14}{candidate.marknad:<12}"
            f"{candidate.drawdown:>8.1%}"
            + _fmt(candidate.rsi14, ".1f", 7) + "  "
            + f"{verdict.state(LIMB_FCF):<13}{verdict.state(LIMB_LEVERAGE):<15}"
            + f"{verdict.state(LIMB_REVENUE):<14}"
        )
    if len(survivors) > 60:
        lines.append(f"  ... and {len(survivors) - 60} more, all in the CSV")

    lines.append(
        "\nNOT DONE HERE: no ranking, no fair value, no maximum buy price, no\n"
        "watchlist write. The ranking key is phase 5 and is approved as text before\n"
        "it is coded; PIPELINE writing is phase 6."
    )
    return "\n".join(lines)


def _filter2_look_ahead(as_of: date, manifest: Mapping[str, str]) -> str:
    fundamentals_asof = manifest.get("fundamentals_asof", "unknown")
    price_asof = as_of.isoformat()
    lines = [
        "  " + "!" * 74,
        "  LOOK-AHEAD WARNING -- READ BEFORE INTERPRETING THIS RESULT",
        "  " + "!" * 74,
        "  yfinance serves historical PRICES but only the LATEST fundamentals. The",
        f"  figures below are the accounts as published by {fundamentals_asof}.",
        f"  The price they are paired with is that of {price_asof}.",
    ]
    first = (manifest.get("first_fetched_at") or "")[:10]
    if first and first != (manifest.get("fetched_at") or "")[:10]:
        lines += [
            f"  The store holds more than one fetch (E49): the first {first}, the",
            f"  latest {fundamentals_asof}. Each row carries the fetch that supplied it,",
            "  and the net-debt date in ranking.csv is each name's own.",
        ]
    if fundamentals_asof != price_asof:
        lines += [
            "",
            f"  THESE TWO DATES DIFFER. This run scores {fundamentals_asof} accounts",
            f"  against the {price_asof} price. A name shown passing may have been",
            "  failing on the accounts that actually existed then, and the reverse.",
            "  It is NOT evidence of what a screener would have found on that day and",
            "  no retroactive reading may be placed on it.",
        ]
    else:
        lines += [
            "",
            "  The two dates agree, so this run is contemporaneous. Any replay of an",
            "  earlier date is not, and will say so here.",
        ]
    lines += [
        "",
        "  AND THE ENTERPRISE VALUE IS BUILT HERE, NOT READ. The vendor's",
        "  enterpriseValue is a precomputed figure refreshed on its own cadence,",
        "  not on the price's (SCREENER-REVIEW-3 Part 12: marketCap moved for 450",
        "  of 473 names between two fetches of one day, enterpriseValue for 3),",
        "  so it is carried as a memo and read by nothing. The yield divides EBIT",
        f"  by [the vendor's share count x the SETTLED close of {price_asof}]",
        f"  + totalDebt - totalCash, where the two balance-sheet legs are the",
        f"  vendor's latest as of {fundamentals_asof}. ONE price date per row,",
        "  and the net-debt date is printed beside it in ranking.csv.",
        "",
        "  Exchange rates are the third date. Without --fx-from-manifest they are",
        "  fetched at run time and are the LATEST close, whatever --asof says.",
    ]
    lines.append("  " + "!" * 74)
    return "\n".join(lines)


# --- --rank ----------------------------------------------------------------


@dataclass
class RankRun:
    as_of: date
    upstream: "Filter2Run"
    result: ranking_step.RankingResult
    report: str
    ranking_path: Path | None
    manifest_path: Path | None
    write_result: object | None = None


TOP_N = 20


def rank(
    *,
    as_of: date,
    universe_dir: Path = UNIVERSE_DIR,
    tiers: Sequence[str] = ("A",),
    snapshot_root: Path = snapshot_store.SNAPSHOT_ROOT,
    snapshot_date: date | None = None,
    exclusions_path: Path = EXCLUSIONS_PATH,
    config_path: Path = FILTER2_CONFIG_PATH,
    runs_root: Path | None = RUNS_ROOT,
    db_path: Path = DB_PATH,
    fx_lookup=fx_step.default_lookup,
    fx_from_manifest: Path | None = None,
    write_pipeline: bool = False,
    top: int = 5,
    watchlist_path: Path = pipeline_step.WATCHLIST_PATH,
    dry_run: bool = False,
    now: datetime | None = None,
) -> RankRun:
    """The whole chain, then the ranking key. FRAMEWORK-EDITS E5."""
    upstream = filter2(
        as_of=as_of, universe_dir=universe_dir, tiers=tiers,
        snapshot_root=snapshot_root, snapshot_date=snapshot_date,
        exclusions_path=exclusions_path, config_path=config_path,
        runs_root=None, db_path=db_path,
    )
    store_path = snapshot_store.fundamentals_path(
        upstream.upstream.snapshot_date, snapshot_root
    )
    records = {r.ticker: r for r in snapshot_store.read_fundamentals(store_path)}
    manifest = snapshot_store.read_fundamentals_manifest(store_path)
    candidates = upstream.result.survivors

    # Rule 8 of the ranking: every yield is struck on the SETTLED close the
    # filter-1 row carries, not on whatever price the vendor's
    # enterpriseValue happens to embed. The close date travels with it, and
    # the fetch date is what totalDebt / totalCash are dated.
    closes = {c.ticker: (c.last_close_date, c.last_close) for c in candidates}
    # E49: one store, several fetches. The net-debt date is each record's
    # own fetch; the manifest's latest stands in only where a record does
    # not carry one.
    latest = _fetch_date(manifest)
    fetched = {
        ticker: (record.fetched_at.date() if record.fetched_at else latest)
        for ticker, record in records.items()
    }
    inputs = [ranking_step.extract_inputs(c.ticker, records.get(c.ticker),
                                          close=closes.get(c.ticker),
                                          fetched=fetched.get(c.ticker, latest))
              for c in candidates]
    # Two pair sets. Enterprise value converts from the quote currency into
    # the reporting one; turnover converts from every quote currency into a
    # single one so two listings of one company can be compared at all.
    pairs = list(ranking_step.currency_pairs(inputs))
    pairs += [(i.quote_currency, ranking_step.TURNOVER_CURRENCY) for i in inputs]
    # --fx-from-manifest (K7). Without it the lookup asks the network for the
    # LATEST close whatever --asof says, so a re-run of an old date is not the
    # same run. With it the rates come back out of a stored manifest and a
    # pair that manifest lacks FAILS rather than being quietly fetched.
    fx_replayed_from = fx_manifest_asof = None
    if fx_from_manifest is not None:
        fx_lookup = fx_step.lookup_from_manifest(fx_from_manifest)
        fx_replayed_from = str(fx_from_manifest)
        # L5: the manifest says which day its rates belong to. Reading it is
        # what turns "REPRODUCIBLE" into "REPRODUCIBLE, AND CROSS-DATED".
        fx_manifest_asof = fx_step.manifest_asof(fx_from_manifest)
    table = fx_step.build_table(pairs, lookup=fx_lookup)

    quote_of = {i.ticker: i.quote_currency for i in inputs}
    turnover = {}
    for candidate in candidates:
        frame = snapshot_store.read_prices(
            snapshot_store.snapshot_path(upstream.upstream.snapshot_date, snapshot_root),
            candidate.ticker,
        )
        turnover[candidate.ticker] = ranking_step.median_turnover_major(
            frame, as_of, quote_of.get(candidate.ticker)
        )

    kept, merges, share_class_tally = ranking_step.collapse_share_classes(
        candidates, records, turnover, quote_of, table
    )
    # E46: the same owner-maintained list filter 2 read, on the quality leg.
    result = ranking_step.rank_candidates(
        kept, records, table, as_of, closes=closes, fetched=fetched,
        investment_companies=upstream.result.config.investment_companies)
    result.share_class_merges = merges
    result.share_class_tally = share_class_tally

    markets = {c.ticker: c.marknad for c in candidates}
    ranking_path = manifest_path = None
    if runs_root is not None:
        ranking_path, manifest_path = _write_ranking(
            runs_root, as_of, result, table, markets,
            fx_replayed_from=fx_replayed_from,
            candidates={c.ticker: c for c in candidates},
            fundamentals=records,
        )

    write_result = None
    if write_pipeline:
        names = {i.ticker_yahoo: (i.namn or i.ticker_yahoo)
                 for i in upstream.upstream.load.instruments if i.ticker_yahoo}
        drawdowns = {c.ticker: c.drawdown for c in upstream.upstream.result.candidates}
        # E12: the drawdown AND the date of the peak it was struck against
        # are written on the entry, as a pair, and frozen there.
        peaks = {c.ticker: c.high_52w_date
                 for c in upstream.upstream.result.candidates if c.high_52w_date}
        entries = pipeline_step.entries_from_ranking(
            result.main, asof=as_of, top=top, names=names, markets=markets,
            drawdowns=drawdowns, total=len(result.main), peak_dates=peaks,
        )
        write_result = pipeline_step.write(
            entries, path=watchlist_path, now=now or datetime.now(),
            dry_run=dry_run, validate=pipeline_step.validate_watchlist,
        )

    report = _rank_report(as_of, upstream, result, table, manifest,
                          ranking_path, manifest_path, write_result, top,
                          fx_replayed_from, fx_manifest_asof)
    return RankRun(as_of=as_of, upstream=upstream, result=result, report=report,
                   ranking_path=ranking_path, manifest_path=manifest_path,
                   write_result=write_result)


def _fetch_date(manifest: Mapping[str, str]) -> date | None:
    """The date the fundamentals store was fetched, or None if it cannot say."""
    stamp = manifest.get("fetched_at") or manifest.get("fundamentals_asof")
    if not stamp:
        return None
    try:
        return date.fromisoformat(str(stamp)[:10])
    except ValueError:
        return None


RANK_COLUMNS = (
    "section", "combined_rank", "quality_rank", "ey_rank", "ticker", "marknad",
    "sector",
    # E63: the filter-1 row's drawdown and its distance above the 52-week
    # closing low, beside each other. FIELDS -- read by nothing in the key.
    "drawdown", "pct_above_52w_low", "low_52w", "low_52w_date",
    # E127: the 12-month return filter 1 admitted the name on.
    "return_12m",
    "operating_profitability", "earnings_yield",
    "total_assets", "total_assets_period",
    "ebit", "ebit_label", "ebit_period", "enterprise_value_reporting",
    # Rule 8: the parts the enterprise value was BUILT from, each with its
    # date, so a reader sees which day's price sits in the denominator.
    "settled_close", "settled_close_date", "fetch_day_price", "implied_shares",
    "market_cap_settled_quote", "total_debt", "total_cash", "net_debt_date",
    "enterprise_value_vendor_memo",
    "reporting_currency", "quote_currency", "fx_pair", "fx_rate",
    "quality_state", "note", "origin", "basis", "basis_periods", "basis_note",
    # 2026-09-04: this year against its own five-year median, both legs.
    # PRINTED, NEVER FILTERED -- no gate, no kill, no ranking key and no
    # verdict reads either. They answer the one question a ranked row
    # cannot otherwise be asked: is the figure the key ranked on a NORMAL
    # year for this company, or the top of a cycle? Each carries its own
    # provenance column, because a ratio whose source nobody can name is a
    # number nobody can check -- and where it is DATA MISSING that column
    # says WHY, which is the more useful half of it.
    "ebit_vs_5y_median", "ebit_vs_5y_median_source",
    "fcf_vs_5y_median", "fcf_vs_5y_median_source",
)


def _rank_row(section: str, item, marknad: str, candidate=None,
              medians=None) -> dict:
    scored = item.scored if hasattr(item, "scored") else item
    inputs = scored.inputs
    low_date = getattr(candidate, "low_52w_date", None)
    from .medians import MedianRatio
    ebit_median, fcf_median = (medians or {}).get(
        scored.ticker,
        (MedianRatio(note="not computed for this row"),) * 2)
    return {
        "ebit_vs_5y_median": ebit_median.column(),
        "ebit_vs_5y_median_source": ebit_median.provenance(),
        "fcf_vs_5y_median": fcf_median.column(),
        "fcf_vs_5y_median_source": fcf_median.provenance(),
        "section": section,
        "combined_rank": getattr(item, "combined", None),
        "quality_rank": getattr(item, "quality_rank", None),
        "ey_rank": getattr(item, "ey_rank", None),
        "ticker": scored.ticker,
        "marknad": marknad,
        "sector": inputs.sector,
        # E63: copied from the filter-1 candidate row so the ordering's own
        # record shows, beside each name, how far it has fallen AND how far
        # it sits above its own low. Fields; B41 was decided by E127 -- no
        # threshold on the low -- and filter 1 reads return_12m instead.
        "drawdown": getattr(candidate, "drawdown", None),
        "pct_above_52w_low": getattr(candidate, "pct_above_52w_low", None),
        "low_52w": getattr(candidate, "low_52w", None),
        "low_52w_date": low_date.isoformat() if low_date else None,
        "return_12m": getattr(candidate, "return_12m", None),
        # E43: EBIT / total assets. The numerator is the `ebit` column below,
        # on the `basis` the same row names; no gross-profit column exists.
        "operating_profitability": scored.operating_profitability,
        "earnings_yield": scored.earnings_yield,
        "total_assets": inputs.total_assets,
        "total_assets_period": (inputs.total_assets_period.isoformat()
                                if inputs.total_assets_period else None),
        "ebit": inputs.ebit,
        "ebit_label": inputs.ebit_label,
        "ebit_period": (inputs.ebit_period.isoformat()
                        if inputs.ebit_period else None),
        "enterprise_value_reporting": scored.enterprise_value,
        "settled_close": inputs.settled_close,
        "settled_close_date": (inputs.settled_close_date.isoformat()
                               if inputs.settled_close_date else None),
        "fetch_day_price": inputs.fetch_day_price,
        "implied_shares": scored.implied_shares,
        "market_cap_settled_quote": scored.market_cap_settled,
        "total_debt": inputs.total_debt,
        "total_cash": inputs.total_cash,
        "net_debt_date": (inputs.net_debt_date.isoformat()
                          if inputs.net_debt_date else None),
        # The vendor's own figure, carried so a reader can see what it said.
        # It is read by NOTHING: rule 8.
        "enterprise_value_vendor_memo": inputs.enterprise_value_quoted,
        "reporting_currency": inputs.reporting_currency,
        "quote_currency": inputs.quote_currency,
        "fx_pair": scored.fx_pair,
        "fx_rate": scored.fx_rate,
        "quality_state": scored.quality_state,
        "note": scored.note,
        # WHICH PATH the figures in this row came from. Uniformly the quote
        # vendor today; a name whose fundamentals were entered by hand
        # (vss/manual.py) reads `manual`, and a reader never has to work out
        # which by looking at the ticker.
        "origin": inputs.origin,
        # WHICH PERIOD BASIS the flow figures were struck on (E13):
        # `annual` where the statements are already twelve months, `ttm`
        # where four consecutive quarters were summed. Without it the CSV
        # cannot be read -- a quarter and a year in one ordering differ by
        # a factor of four, which is what backlog B-8 found.
        "basis": inputs.basis,
        # And for a `ttm` row, WHICH FOUR PERIODS were summed: the audit
        # trail for a figure no filing states, joined the way it was formed.
        "basis_periods": "+".join(d.isoformat() for d in inputs.basis_periods),
        # WHY a row is on the basis it is on -- for an `annual` row, why the
        # four quarters could not be formed (item 8): no quarterly statement
        # from the vendor, a hole in it, or a newer filed year.
        "basis_note": inputs.basis_note,
    }


def five_year_medians(result, fundamentals: Mapping | None) -> dict:
    """The two printed columns for every row the ranking file will hold.

    THE SEC ROUTE IS ASKED ONLY WHERE A CIK IS KNOWN, and a CIK is known for
    the handful of names somebody has already entered by hand -- there is no
    lookup here and none is attempted, because guessing a filer's identity
    from a ticker is exactly the mistake E103 was built to avoid. Every
    other row is answered from the fundamentals store, which is the source
    that exists for the universe.

    A FAILURE ON ONE NAME IS THAT NAME'S NOTE AND NEVER THE RUN'S. The SEC
    call is inside `medians.medians_for`, which degrades to the next source
    and writes the reason into the provenance column.
    """
    from . import manual as manual_step
    from . import medians as medians_step

    ciks: dict[str, int] = {}
    stores: dict[str, object] = {}
    for path in sorted(manual_step.MANUAL_DIR.glob("*.yaml")):
        if path.name == "TEMPLATE.yaml":
            continue
        try:
            parsed = manual_step.load_manual(path.stem,
                                             directory=manual_step.MANUAL_DIR)
        except Exception:            # noqa: BLE001 -- a broken store is not this step's business
            continue
        stores[parsed.ticker] = parsed
        if getattr(parsed, "cik", None):
            ciks[parsed.ticker] = int(parsed.cik)

    def facts_for(ticker):
        cik = ciks.get(ticker)
        if cik is None:
            return None
        from .xbrl import fetch_company_facts
        return lambda: fetch_company_facts(cik)

    rows = ([r.scored for r in result.main] + [r.scored for r in result.yield_only]
            + list(result.unrankable) + list(result.stale))
    out = {}
    for scored in rows:
        out[scored.ticker] = medians_step.medians_for(
            scored.ticker, fundamentals=(fundamentals or {}).get(scored.ticker),
            parsed=stores.get(scored.ticker), facts=facts_for(scored.ticker))
    return out


def _write_ranking(runs_root: Path, as_of: date, result, table,
                   markets: Mapping[str, str],
                   fx_replayed_from: str | None = None,
                   candidates: Mapping[str, object] | None = None,
                   fundamentals: Mapping | None = None) -> tuple[Path, Path]:
    import csv
    import json

    fields = candidates or {}
    # `table` is the FX table; the fundamentals are their own argument. The
    # five-year medians read the SECOND -- naming it rather than reaching
    # for whichever mapping was to hand.
    medians = five_year_medians(result, fundamentals or {})
    directory = runs_root / as_of.isoformat()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "ranking.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(RANK_COLUMNS),
                                lineterminator="\n")
        writer.writeheader()
        for item in result.main:
            writer.writerow(_rank_row("ranked", item, markets.get(item.ticker, ""),
                                      fields.get(item.ticker), medians))
        for item in result.yield_only:
            writer.writerow(_rank_row("earnings_yield_only", item,
                                      markets.get(item.ticker, ""),
                                      fields.get(item.ticker), medians))
        for scored in result.unrankable:
            writer.writerow(_rank_row("unrankable", scored,
                                      markets.get(scored.ticker, ""),
                                      fields.get(scored.ticker), medians))
        # Written into the same file, in their own section. A name excluded
        # from an ordering has to be findable in the ordering's own record.
        for scored in result.stale:
            writer.writerow(_rank_row("stale", scored,
                                      markets.get(scored.ticker, ""),
                                      fields.get(scored.ticker), medians))

    manifest_path = directory / "ranking-manifest.json"
    manifest = {
        "asof": as_of.isoformat(),
        "key": "FRAMEWORK-EDITS E6 -- gross profitability and earnings yield, "
               "rank sum",
        "ranked": len(result.main),
        "earnings_yield_only": len(result.yield_only),
        "unrankable": len(result.unrankable),
        "stale_excluded": len(result.stale),
        "quality_states": result.reason_counts(),
        "fx": {
            pair: {"rate": rate.value,
                   "as_of": rate.as_of.isoformat() if rate.as_of else None,
                   "source": rate.source}
            for pair, rate in table.rates.items()
        },
        "fx_failed": dict(table.failures),
        # Which of the two things this run was. A manifest that did not say
        # would let a replay be mistaken for the original, and vice versa.
        "fx_source": (f"replayed from {fx_replayed_from}" if fx_replayed_from
                      else "fetched at run time (LATEST close, not --asof's)"),
        "fx_rate_dates": sorted({rate.as_of.isoformat()
                                 for rate in table.rates.values() if rate.as_of}),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path, manifest_path



def _fx_reproducibility(as_of: date, table, fx_replayed_from: str | None,
                        fx_manifest_asof: date | None = None) -> str:
    """K7: say which of AUDITABLE and REPRODUCIBLE this run actually is.

    They are not the same, and SCREENER.md claimed the stronger one until
    2026-08-22. The evidence was already inside the run's own manifest.

    L5: and say when the two are TRUE AT ONCE AND STILL WRONG TOGETHER. A
    replay of one day's rates into a run priced on another is reproducible --
    it repeats exactly -- and it is also the cross-dating the look-ahead
    banner exists to warn about, for a quantity that banner does not cover.
    The manifest knows which day it is; until 2026-08-23 nothing asked it.
    The answer is to NAME it, not to refuse: replaying one rate set across
    dates deliberately, to hold a variable still, is how E6's own measurement
    was made.
    """
    dates = sorted({rate.as_of for rate in table.rates.values() if rate.as_of})
    lines = [""]
    if fx_replayed_from:
        crossed = fx_manifest_asof is not None and fx_manifest_asof != as_of
        headline = ("REPRODUCIBLE, AND CROSS-DATED" if crossed else "REPRODUCIBLE")
        lines.append(f"  {headline} -- rates replayed from {fx_replayed_from}.")
        if crossed:
            lines.append(
                f"  THE MANIFEST SAYS ITS RATES ARE OF "
                f"{fx_manifest_asof.isoformat()}. THIS RUN IS PRICED AT\n"
                f"  {as_of.isoformat()}. The result repeats exactly and is still a\n"
                "  pairing of two dates: the same cross-dating the look-ahead banner\n"
                "  warns about for the accounts, applied to the exchange rate, which\n"
                "  that banner does not cover. Nothing is refused -- holding one rate\n"
                "  set still across dates is a legitimate way to isolate a variable,\n"
                "  and E6's own measurement was made that way. It is said, not netted\n"
                "  away."
            )
        elif fx_manifest_asof is None:
            lines.append(
                "  The manifest carries no 'asof' field, so whether its rates belong\n"
                "  to this run's date could not be checked. That is a reason to say\n"
                "  so, not a reason to assume they agree."
            )
        lines.append(
            "  Nothing was fetched. A pair that manifest did not carry FAILS and is\n"
            "  listed above rather than being quietly fetched, because a reproduction\n"
            "  that is partly a new run is neither."
        )
    else:
        lines.append(
            "  AUDITABLE, NOT REPRODUCIBLE. Every rate above is on the record, so it\n"
            "  can be checked afterwards. It cannot be RE-RUN to the same answer:\n"
            "  the lookup asks for the last five days and takes the LATEST close,\n"
            "  whatever --asof says, so this run tomorrow gives other rates and\n"
            "  potentially another top 5.\n"
            "  Pass --fx-from-manifest PATH to replay a stored run's rates instead."
        )
    if len(dates) > 1:
        stamps = ", ".join(d.isoformat() for d in dates)
        lines.append(
            f"\n  NOTE: this run carries {len(dates)} different rate dates -- {stamps}.\n"
            f"  The run is dated {as_of.isoformat()}. A pair whose market had not closed\n"
            "  when the run started carries the previous session; a pair fetched after\n"
            "  midnight carries the next one. The 2026-08-21 run had ten pairs at\n"
            "  08-21 and two at 08-22 and said nothing about it."
        )
    elif dates and dates[0] != as_of:
        lines.append(
            f"\n  NOTE: every rate is dated {dates[0].isoformat()} against a run dated "
            f"{as_of.isoformat()}."
        )
    return "\n".join(lines)


def _pct(value, width=9):
    return f"{'--':>{width}}" if value is None else f"{value:>{width}.1%}"


def _rank_report(as_of, upstream, result, table, fundamentals_manifest,
                 ranking_path, manifest_path, write_result=None, top=5,
                 fx_replayed_from=None, fx_manifest_asof=None) -> str:
    lines = [_heading(f"RANKING -- TWO COMPONENTS  asof={as_of.isoformat()}")]
    lines.append(
        "\n  operating profitability = EBIT / total assets   (FRAMEWORK-EDITS E43)\n"
        "  EY                      = EBIT / enterprise value\n"
        "  Ranked separately on each, the two placings summed, sorted ascending.\n"
        "  No weighting, no thresholds, no score. FRAMEWORK-EDITS E6 as amended\n"
        "  by E43."
    )
    lines.append(
        "\n  E43 REPLACED THE QUALITY LEG'S NUMERATOR on 2026-08-26. E6 used\n"
        "  Gross Profit / Total Assets (Novy-Marx 2013), and SCREENER-REVIEW-3\n"
        "  measured the vendor's Gross Profit against the annual reports of the\n"
        "  five names section 5 would have received: it reconciled to a line of\n"
        "  the report for NONE of them. The vendor manufactures a gross profit\n"
        "  for a by-nature filer -- net sales less whatever it calls cost of\n"
        "  revenue -- so AFRY.ST read 75.7% with 15,817m of personnel below the\n"
        "  line. Operating profit is a line every filer states, and it is the\n"
        "  SAME figure the price leg divides, on the same E13 basis: the two legs\n"
        "  share a numerator now, and the rank sum is not two independent\n"
        "  readings (Ball, Gerakos, Linnainmaa & Nissim, JFE 2016, for the leg).\n"
        "  Gross Profit is read by nothing in the ranking."
    )
    lines.append(
        "\n  E6 REPLACED THE QUALITY LEG on 2026-08-22. E5 used Greenblatt's\n"
        "  EBIT / (net working capital + net PP&E). That denominator is a difference\n"
        "  between large numbers, so it goes to zero for float-funded, asset-light\n"
        "  businesses: on the 2026-08-21 run the thirteen names whose capital\n"
        "  employed was under half a year's EBIT held quality placings 1 to 13,\n"
        "  without exception. Total assets cannot go to zero, so that pole is gone\n"
        "  and the question of which cash is 'excess' no longer decides anything.\n"
        "  The price leg's DEFINITION is unchanged; its rank NUMBERS are not,\n"
        "  because the two-legged population it is ranked within changed size."
    )
    lines.append(
        "\n  THIS IS THE ONLY ORDERING THE TOOL PRODUCES. It is still not a\n"
        "  recommendation: the output is review work. A high rank means the name is\n"
        "  worth the hours, and the whole section 5 chain -- fair value, margin of\n"
        "  safety, maximum buy price -- is run by hand afterwards."
    )
    if ranking_path:
        lines.append(f"\n  full list      {ranking_path}")
        lines.append(f"  fx manifest    {manifest_path}")

    lines.append("\n" + _filter2_look_ahead(as_of, fundamentals_manifest))

    lines.append("\nENTERPRISE VALUE IS BUILT FROM ONE DATE, NOT READ FROM THE VENDOR")
    lines.append(
        "  The vendor's enterpriseValue is NOT the denominator. SCREENER-REVIEW-3\n"
        "  measured it: between two fetches of one day, eleven hours apart,\n"
        "  marketCap moved for 450 of 473 names and enterpriseValue for 3, and the\n"
        "  price the field embedded matched a close of 2026-06-16 for FGR.PA, the\n"
        "  #1 name, against a settled close of 2026-08-26. Gate 1 admits names that\n"
        "  fell recently, which is exactly when the embedded price is the pre-fall\n"
        "  one and the yield is understated. So the yield divides EBIT by\n"
        "\n"
        "      [marketCap / regularMarketPrice]  the vendor's own share count\n"
        "      x the SETTLED close of the run date, converted to the reporting\n"
        "      currency, + totalDebt - totalCash as the vendor last had them.\n"
        "\n"
        "  Every part and its date is in ranking.csv; the vendor's figure travels\n"
        "  as enterprise_value_vendor_memo and decides nothing.\n"
        "\n"
        "  THE BOUND OF L2 STAYS, ON THE PARTS. A company cannot hold more net cash\n"
        "  (totalCash - totalDebt) than it holds ASSETS. That is not a threshold\n"
        "  or a tolerance: it is the one comparison the arithmetic forbids, and it\n"
        "  is generous by construction. A name that fails it keeps its quality leg\n"
        "  and LOSES ITS YIELD, listed under NOT RANKED with the figures named. It\n"
        "  is a rejection on MISSING data -- a number we refused to form -- and\n"
        "  never on value: nothing here judges the business. The case that found\n"
        "  it: LISP.SW's VENDOR enterprise value implied 17.6bn CHF of net cash\n"
        "  against 9.1bn CHF of total assets and gave the highest yield in the\n"
        "  2026-08-21 list, 27.6%, where the parts give 4.3%."
    )
    lines.append("\nEXCHANGE RATES USED (once per run, per pair)")
    lines.append(
        "  EBIT is in the reporting currency; enterprise value comes from the quote\n"
        "  summary in the MAJOR unit of the quote currency -- a London name quoted in\n"
        "  GBp carries an EV in GBP, not in pence. EV is converted into the reporting\n"
        "  currency before the yield is formed."
    )
    lines.append("")
    lines.append(fx_step.describe(table))
    lines.append(_fx_reproducibility(as_of, table, fx_replayed_from,
                                     fx_manifest_asof))

    merges = getattr(result, "share_class_merges", []) or []
    tally = getattr(result, "share_class_tally", None)
    lines.append("\nONE COMPANY, TWO LISTINGS")
    if tally is not None:
        lines.append(f"  {tally.count_in} candidates in, {tally.count_out} out; "
                     f"{len(merges)} folded in")
    lines.append(
        "  Identity is MEASURED, never guessed from the ticker string: two share\n"
        "  classes of one issuer file one set of accounts, so their EBIT, revenue,\n"
        "  net PP&E and total assets agree exactly. The survivor is the most traded\n"
        "  listing, by median daily turnover out of the stored price series --\n"
        "  divided to the major unit first, so a pence-quoted London line is not\n"
        "  counted a hundred times over."
    )
    if merges:
        lines.append("")
        for merge in merges:
            lines.append(
                f"      kept {merge.kept:<14}({merge.kept_source}) "
                f"dropped {merge.dropped:<14}({merge.dropped_source})"
            )
            lines.append(f"           {merge.basis}"
                         + (f": {merge.detail}" if merge.detail else ""))
    else:
        lines.append("      nothing folded in on this run")

    lines.append("\nSECTIONS")
    counts = result.reason_counts()
    total = len(result.scored)
    lines.append(f"  {len(result.main):>5}  ranked on both components")
    lines.append(f"  {len(result.yield_only):>5}  ranked on earnings yield ALONE -- "
                 f"their own section, never interleaved")
    lines.append(f"  {len(result.unrankable):>5}  NOT RANKED -- neither section will take them")
    lines.append(f"  {len(result.stale):>5}  EXCLUDED -- accounts too old to rank on")
    lines.append(f"  {total:>5}  candidates in")
    lines.append("\n  why a candidate has no quality leg:")
    for state in (ranking_step.QUALITY_OK, ranking_step.QUALITY_SECTOR,
                  ranking_step.QUALITY_INVESTMENT,
                  ranking_step.QUALITY_NOT_MEANINGFUL, ranking_step.QUALITY_MISSING,
                  ranking_step.QUALITY_MIXED_PERIODS, ranking_step.QUALITY_STALE):
        lines.append(f"      {counts.get(state, 0):>5}  {state}")
    lines.append(
        "\n  'investment company (E46)' is the owner's list\n"
        "  (config/screener_investment_companies.yaml), which decides the exemption\n"
        "  for an investment company whatever the vendor's sector string says --\n"
        "  Latour and Lundbergs come back Industrials and were ranked on their\n"
        "  consolidated subsidiaries until 2026-08-26. Listed names sit in the\n"
        "  yield-only section and are never written."
    )
    lines.append(
        "\n  'denominator not positive' is NOT MEANINGFUL, not a low score, and it\n"
        "  is never clamped or sign-flipped. Under E6 the denominator is total\n"
        "  assets, which did not go non-positive for a single candidate measured;\n"
        "  the state is kept because a balance sheet that reported it would be\n"
        "  saying something this key cannot rank.\n"
        "  A NEGATIVE operating profit is a different thing and is RANKED, last: an\n"
        "  operating loss is a fact about the business, not the arithmetic."
    )
    lines.append(
        "\n  'periods do not match' is K6: EBIT and total assets are fetched as\n"
        "  separate lines, and two period ends in one quotient is not a ratio of\n"
        "  anything -- the denominator is read AT the EBIT window's end, and where\n"
        "  no balance sheet carries that date the pair is refused. The record's\n"
        "  own newest_period cannot catch it -- that is the MAX over every stored\n"
        "  row. The periods are written into ranking.csv beside their figures, so\n"
        "  the check is auditable and not merely asserted."
    )

    lines.append(f"\nTOP {TOP_N} -- RANKED ON BOTH COMPONENTS")
    header = (f"  {'#':>3} {'ticker':<13}{'sector':<24}{'sum':>5}{'EBIT/TA':>8}"
              f"{'EY':>7}{'EBIT/TA%':>10}{'EY%':>9}{'dd':>7}{'vs52wL':>8}")
    lines.append("")
    lines.append(header)
    lines.append("  " + THIN[: len(header) - 2])
    # E63: the filter-1 row's drawdown and its distance above the 52-week
    # closing low, printed beside the placings. Read by nothing in the key.
    fields = {c.ticker: c for c in getattr(getattr(upstream, "result", None),
                                            "survivors", []) or []}
    for position, item in enumerate(result.main[:TOP_N], start=1):
        scored = item.scored
        field = fields.get(item.ticker)
        lines.append(
            f"  {position:>3} {item.ticker:<13}{(scored.inputs.sector or '-')[:23]:<24}"
            f"{item.combined:>5}{item.quality_rank:>8}{item.ey_rank:>7}"
            + _pct(scored.operating_profitability, 10) + _pct(scored.earnings_yield, 9)
            + _pct(getattr(field, "drawdown", None), 7)
            + _pct(getattr(field, "pct_above_52w_low", None), 8)
        )
    if len(result.main) > TOP_N:
        lines.append(f"  ... and {len(result.main) - TOP_N} more in {ranking_path}")
    lines.append(
        "\n  dd and vs52wL are the filter-1 row's drawdown from the 52-week closing\n"
        "  high and its distance ABOVE the 52-week closing low (FRAMEWORK-EDITS\n"
        "  E63), on one window and one coverage bar. The band cannot tell a name\n"
        "  that fell and stayed down from one that has since recovered; the second\n"
        "  column can. FIELDS: read by nothing in the key; B41 is decided (E127),\n"
        "  no threshold on the low. Every ranked name is BELOW its close of a\n"
        "  year ago -- filter 1's trailing_year step, return_12m in the CSV."
    )

    lines.append(f"\nEARNINGS YIELD ONLY -- {len(result.yield_only)} names, "
                 f"ranked on ONE leg")
    lines.append(
        "  A separate section by decision, not by accident (E5(a)). Interleaving\n"
        "  them would need an invented quality placing, and an invented number in\n"
        "  the one ordering this tool produces is exactly what must not exist. These\n"
        "  names are LESS WELL JUDGED than the ones above; the section says so."
    )
    header = f"  {'#':>3} {'ticker':<13}{'sector':<24}{'EY%':>9}   why no quality leg"
    lines.append("")
    lines.append(header)
    lines.append("  " + THIN[: len(header) - 2])
    for position, item in enumerate(result.yield_only[:TOP_N], start=1):
        scored = item.scored
        lines.append(
            f"  {position:>3} {item.ticker:<13}{(scored.inputs.sector or '-')[:23]:<24}"
            + _pct(scored.earnings_yield, 9) + f"   {scored.quality_state}"
        )
    if len(result.yield_only) > TOP_N:
        lines.append(f"  ... and {len(result.yield_only) - TOP_N} more in {ranking_path}")

    lines.append(f"\nEXCLUDED ON STALE ACCOUNTS -- {len(result.stale)} names (K5, L4)")
    lines.append(
        f"  Two questions, asked in this order, both at {fundamentals_step.MAX_REPORT_AGE_DAYS} days.\n"
        "  FIRST, the record's own flag: fundamentals.py marks a ticker STALE when its\n"
        "  newest reported period is older than the limit. Until 2026-08-22 that flag\n"
        "  was computed, printed and read by nothing -- BWY.L was ranked on an EBIT\n"
        "  from 2024-07-31 against an enterprise value from 2026-08-21, 751 days in\n"
        "  one quotient, and neither the CSV nor this report said a word about it.\n"
        "  SECOND, and this is the one the flag CANNOT answer: how old are the rows\n"
        "  THIS KEY ACTUALLY READ? newest_period is the MAX over every stored row,\n"
        "  including rows no component touches. SHL.DE's gross profit, total assets\n"
        "  and EBIT were all from 2024-09-30, 690 days before the run, and it read OK\n"
        "  at rank 246 because Net PPE and Ordinary Shares Number carried 2025-09-30.\n"
        "  COLO-B.CO is the same 690 days old and was excluded. Same age, opposite\n"
        "  treatment, decided by a row no leg touches.\n"
        "  Only periods that fed a component that COMPUTED are measured. A quality\n"
        "  leg the sector exemption never evaluated does not count, and neither does\n"
        "  a pair of lines already refused for disagreeing -- AUTO.L's gross profit is\n"
        "  873 days old and is 'periods do not match', which is a fact about the two\n"
        "  lines and not about their age.\n"
        "  A stale record is DANGEROUS because every leg computes. It is excluded\n"
        "  here, counted as a rejection ON VALUE -- figures we have, judged too old\n"
        "  -- and never mixed with the names whose figures were absent."
    )
    if result.stale:
        lines.append("")
        for scored in result.stale:
            lines.append(f"      {scored.ticker:<14}{scored.note}")
    else:
        lines.append("\n      nothing excluded on this run")

    if result.unrankable:
        lines.append(f"\nNOT RANKED -- {len(result.unrankable)} names, named not netted away")
        lines.append(
            "  Neither section will take these: without an earnings yield a name is\n"
            "  not on the two-legged list, and the one-legged section is the EARNINGS\n"
            "  YIELD one. Some of them have a quality leg that computed perfectly\n"
            "  well; the reason is printed per name and the two are counted apart in\n"
            "  the tally. Every one of them is a rejection on MISSING data -- a\n"
            "  number we could not form -- and never on value."
        )
        for scored in result.unrankable[:20]:
            lines.append(f"  {scored.ticker:<14}{scored.note or 'no components'}")

    lines.append(
        f"\n  THE {len(result.yield_only)} NAMES ABOVE ARE NOT WRITTEN TO THE WATCHLIST.\n"
        "  For the sector-exempt majority of them, enterprise value is not a\n"
        "  meaningful construct either -- a bank's cash and debt are operating\n"
        "  items, not financing -- so the one leg they are ranked on is itself\n"
        "  compromised, and they are in practice not ranked. Only the names ranked\n"
        "  on BOTH components are eligible for PIPELINE."
    )
    lines.append(
        "  Enterprise value is not a meaningful construct for a bank: its cash and\n"
        "  its debt are what it trades in, not how it is financed."
    )

    if write_result is None:
        lines.append(
            "\nNOT DONE HERE: nothing was written to config/watchlist.yaml. Add\n"
            "--write-pipeline to run phase 6 and enter the top names as PIPELINE."
        )
        return "\n".join(lines)

    lines.append(_heading(f"PIPELINE WRITE -- top {top} of the BOTH-legs list"))
    if write_result.dry_run:
        lines.append("\n  DRY RUN -- nothing was written.")
    if write_result.backup:
        lines.append(f"\n  backup     {write_result.backup}")
    lines.append(f"  watchlist  {write_result.path}")
    lines.append(
        "\n  Written as PIPELINE with no mbp, no fv_base, no tier and no stop.\n"
        "  The one-line note per name is assembled from figures this run measured;\n"
        "  it carries no assessment. Section 5 is run by hand."
    )
    lines.append(f"\n  WRITTEN -- {len(write_result.written)}")
    for entry in write_result.written:
        lines.append(f"      {entry.ticker:<14}{entry.name}")
    if write_result.skipped:
        lines.append(f"\n  SKIPPED -- {len(write_result.skipped)}, never overwritten")
        for ticker, why in write_result.skipped:
            lines.append(f"      {ticker:<14}{why}")
    lines.append(
        "\n  The file was re-parsed after the write. Had it stopped loading, the\n"
        "  backup would have been restored and this run would have failed."
    )
    return "\n".join(lines)


# --- CLI entry -------------------------------------------------------------


def run_screen(
    *,
    universe_report_only: bool,
    snapshot_only_flag: bool,
    filter1_flag: bool,
    fundamentals_flag: bool = False,
    filter2_flag: bool = False,
    rank_flag: bool = False,
    write_pipeline_flag: bool = False,
    top: int = 5,
    dry_run: bool = False,
    as_of: date,
    universe_dir: Path,
    tiers: Sequence[str],
    snapshot_root: Path,
    batch_size: int,
    limit: int | None,
    snapshot_date: date | None = None,
    exclusions_path: Path = EXCLUSIONS_PATH,
    fx_from_manifest: Path | None = None,
    runs_root: Path | None = None,
) -> int:
    # None means "the default"; an explicit path isolates a comparison run's
    # artifacts from the real ones for that date.
    runs = runs_root if runs_root is not None else RUNS_ROOT
    try:
        if universe_report_only:
            print(universe_report(universe_dir, tiers))
            return 0
        if rank_flag:
            run = rank(
                as_of=as_of, universe_dir=universe_dir, tiers=tiers,
                snapshot_root=snapshot_root, snapshot_date=snapshot_date,
                exclusions_path=exclusions_path,
                fx_from_manifest=fx_from_manifest,
                write_pipeline=write_pipeline_flag, top=top,
                dry_run=dry_run, runs_root=runs,
            )
            print(run.report)
            return 0
        if filter2_flag:
            run = filter2(
                as_of=as_of, universe_dir=universe_dir, tiers=tiers,
                snapshot_root=snapshot_root, snapshot_date=snapshot_date,
                exclusions_path=exclusions_path,
            )
            print(run.report)
            return 0
        if fundamentals_flag:
            run = fetch_fundamentals(
                as_of=as_of, universe_dir=universe_dir, tiers=tiers,
                snapshot_root=snapshot_root, snapshot_date=snapshot_date,
                exclusions_path=exclusions_path, limit=limit,
            )
            print(run.report)
            return 0
        if filter1_flag:
            run = filter1(
                as_of=as_of, universe_dir=universe_dir, tiers=tiers,
                snapshot_root=snapshot_root, snapshot_date=snapshot_date,
                exclusions_path=exclusions_path, runs_root=runs,
            )
            print(run.report)
            return 0
        if snapshot_only_flag:
            result = snapshot_only(
                as_of=as_of, universe_dir=universe_dir, tiers=tiers,
                snapshot_root=snapshot_root, batch_size=batch_size, limit=limit,
            )
            print(result.report)
            return 0
    except UniverseError as exc:
        log.error("universe error: %s", exc)
        return 2
    print(
        "Pick one of:\n"
        "  --universe-report   what the committed lists contain, and what was excluded\n"
        "  --snapshot-only     fetch prices for the whole universe and store them\n"
        "  --filter1           run the exclusion list and the dislocation band against\n"
        "                      a stored snapshot; fetches nothing\n"
        "  --fundamentals      fetch fundamentals for the survivors of filter 1, one\n"
        "                      ticker at a time, and store them beside the snapshot\n"
        "  --filter2           run the whole chain against stored data: step 0,\n"
        "                      filter 1, then coarse quality. Fetches nothing\n"
        "  --rank              the whole chain plus the two-component ranking key.\n"
        "                      Fetches only the exchange rates it needs\n"
        "Ranking and PIPELINE writing are phases 5 and 6 and do not exist yet.",
        file=sys.stderr,
    )
    return 2
