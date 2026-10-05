"""E93: the weekly screen — snapshot, rank, report, and a change-only pointer.

**NOT `vss/watch.py`.** That one watches DISCLOSURES for the handful of names
already on the watchlist. This one runs the whole screening chain over the
universe and reports what moved across the top of the ranked list.

**IT NEVER WRITES THE WATCHLIST AND NEVER ENTERS A NAME AS PIPELINE** (E93).
The scheduled unit does not pass `--write-pipeline`, and
`assert_no_watchlist_write` compares the file's bytes either side of the run.
The reason is E12: entering a name stamps `dd_at_entry` and `peak_date` and
**freezes Gate 1 at that moment**, so a timer would freeze a catalyst window
on an arbitrary Saturday at whatever the previous close happened to be — and
unlike a fair value, a frozen Gate 1 is not undone by re-striking.

**What is reported (E93), and what is deliberately not:**

* a name **entering** or **leaving the top 10**, by POSITION;
* a name crossing from **outside the top 20 into the top 10** in one step;
* an entrant that is **already on the watchlist** (a DROPPED one especially);
* a name **ranked before and now unrankable or stale** — a DATA event;
* **the run not completing** — which SUPPRESSES every one of the above.

E116 adds a status line on every run and one informational line of names
new to the top 20; the suppression above still withholds every name.

**Nothing fires on movement inside the top 20.** The key sums two placings
across ~200 candidates and a name moves several places on a price move
alone; that is E11's finding in different clothes, and a pointer that fires
on wobble trains its reader to ignore the pointer.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WATCHLIST_PATH = PROJECT_ROOT / "config" / "watchlist.yaml"
DB_PATH = PROJECT_ROOT / "data" / "vss.sqlite"
REPORTS_DIR = PROJECT_ROOT / "reports"

#: E93's two boundaries. TOP is the one changes are reported on; WATCH is the
#: outer ring, used ONLY to tell a one-step jump from ordinary movement.
#: Nothing is reported for moving inside WATCH.
TOP_N = 10
WATCH_N = 20

#: E93: how many price snapshots to keep. The rankings are kept forever --
#: they are kilobytes and every future comparison stands on them -- while a
#: snapshot is ~235MB and only the recent ones are ever re-read.
KEEP_SNAPSHOTS = 4

SECTION_RANKED = "ranked"
SECTION_EY_ONLY = "earnings_yield_only"

#: What produced a stored ranking. A real weekly run stamps SCHEDULED;
#: anything seeded from an artifact stamps BACKFILL, and a row written
#: before the column existed reads NULL.
#:
#: **A CHANGE IS ONLY NOTIFIED WHEN BOTH SIDES ARE SCHEDULED RUNS.** This is
#: a rule and not a one-off: a baseline that was regenerated, backfilled, or
#: simply cannot be vouched for was not computed the way the run diffing
#: against it was, and the differences that fall out are as likely to be the
#: CODE having moved as the market. That is exactly the phantom E93's
#: incomplete-run clause exists to prevent, arriving through a second door.
#:
#: The concrete case it was written for: the 2026-08-29 baseline is a
#: REGENERATION. The original artifact was destroyed on 2026-08-31 and the
#: snapshot re-ranked under later code, which ranks 216 names where the
#: original ranked 202 (commit d171724 changed filter 2's leverage limb).
#: So the run of 2026-09-05 reports and stores, and notifies NOTHING; real
#: change detection begins 2026-09-12, when both sides are genuine runs.
#: **Nothing expires on a date — the rule simply stops applying once the
#: previous run is a scheduled one.**
PROVENANCE_SCHEDULED = "scheduled"
PROVENANCE_BACKFILL = "backfill"


def baseline_is_genuine(previous: "Sequence[dict]") -> bool:
    """Was the ranking we are diffing against produced by a real run?

    An empty baseline is not genuine either -- but that path never reaches a
    notification, because a first run computes no changes at all.
    """
    if not previous:
        return False
    return all(row.get("provenance") == PROVENANCE_SCHEDULED
               for row in previous)


# --- THE COMPARISON BASIS -------------------------------------------------
#
# **A DIFF IS ONLY WORTH NOTIFYING WHEN BOTH SIDES WERE STRUCK THE SAME WAY.**
#
# The provenance rule above was the first instance of this and was written as
# a one-off. It is not one. It says: *the differences between two rankings are
# only about the market when everything ELSE about the two runs agrees* -- and
# "everything else" is a list that grows.
#
# What is on the list today, and why each one earned its place:
#
#   provenance  a baseline that was regenerated, backfilled, or cannot be
#               vouched for was not computed the way the run diffing against
#               it was; the differences are as likely to be the CODE having
#               moved (2026-08-31: a re-rank under later code ranked 216
#               where the original ranked 202).
#   tiers       a run over tier A+B places its names against 306 ranked
#               competitors where a tier-A run places them against 215.
#               Nothing about GDDY changed when it went from #14 to #21 on
#               2026-08-31; the field it was placed in did.
#
# THE OWNER'S RULING, 2026-09-01, on widening the scheduled run to tier B:
# *"mark the ranking's provenance on a tier change so the next diff refuses
# to compare across it, rather than me remembering to treat one Saturday as a
# baseline. Same rule as the seeded-baseline case; make it general."* This
# function is that ruling: a mismatch on ANY basis field withholds the
# pointer, prints the reason, and stops applying by itself as soon as two
# consecutive runs agree. **Nothing expires on a date and nobody has to
# remember anything.**
#
# Adding a condition later means adding a clause here and a column beside
# `tiers`. It does NOT mean another special case in `run_weekly`.


def _one(rows: "Sequence[dict]", key: str):
    """The value of `key` across a run's rows, or None if they disagree.

    Every row of one run carries the same run-level value. Disagreement
    means the rows are not one run, which is itself a reason to refuse.
    """
    values = {row.get(key) for row in rows}
    return values.pop() if len(values) == 1 else None


def basis_mismatches(previous: "Sequence[dict]",
                     current: "Sequence[dict]") -> list[str]:
    """Why these two rankings may NOT be diffed. Empty means they may.

    Each string is one reason, written to be read on a phone or in a report
    without further explanation.
    """
    if not previous:
        return ["there is no previous ranking to compare against"]
    reasons: list[str] = []

    if not baseline_is_genuine(previous):
        reasons.append(
            f"the baseline was not produced by a scheduled run (provenance "
            f"`{_one(previous, 'provenance') or 'unrecorded'}`), so a "
            f"difference cannot be told from a code change")
    if current and not baseline_is_genuine(current):
        reasons.append(
            f"THIS run is not a scheduled run (provenance "
            f"`{_one(current, 'provenance') or 'unrecorded'}`)")

    before, now = _one(previous, "tiers"), _one(current, "tiers")
    if before != now:
        reasons.append(
            f"the universe changed: the baseline was struck on tiers "
            f"`{before or 'unrecorded'}` and this run on `{now or 'unrecorded'}`, "
            f"so every crossing between them is the TIER CHANGE and not the "
            f"market")
    return reasons

#: A run is INCOMPLETE when its ranked coverage falls short of the previous
#: run's by more than this fraction.
#:
#: **0.98, ACCEPTED BY THE OWNER 2026-08-31 AND RULED AS HIS** — not merely
#: a number this file chose. E93 said a short run sends no pointer without
#: putting a figure on "short"; the owner put one on it at the read-back,
#: in his own terms: **2% of ~216 ranked names is four names — tight enough
#: to catch a throttled fetch, loose enough not to go silent on ordinary
#: attrition** (a delisting, accounts going stale). Recorded beneath E93.
#:
#: It remains his to move, and every run PRINTS the comparison it was
#: applied to, so a wrong threshold shows up in the report rather than
#: silently swallowing a week.
COVERAGE_TOLERANCE = 0.98


class ScreenWatchError(Exception):
    """The weekly run could not complete. Raised for a broken run, never for
    a run that merely found nothing to report."""


# --- turning a ranking into rows ------------------------------------------


def ranking_rows(result, *, run_ts: datetime, as_of: date,
                 snapshot_date: date | None, fx_source: str = "",
                 coverage_short: bool = False,
                 provenance: str = PROVENANCE_SCHEDULED,
                 tiers: Sequence[str] = ()) -> list[dict]:
    """One row per ranked name, plus a row for each name that cannot rank.

    POSITION is the index in the ordered list, 1-based, and it is what E93's
    top-10 is defined on -- never `combined`, which is a sum of two placings
    and ties freely. `ranking.py` breaks those ties alphabetically and says
    it is an arbitrary rule; because it is stated and deterministic, the
    boundary is reproducible.

    The unrankable and stale names are stored with a NULL position, so next
    week can see that a name which HAD a position no longer has one -- E93's
    data event. A name absent from the table entirely was never a candidate.
    """
    common = {
        "run_ts": run_ts.isoformat(timespec="seconds"),
        "as_of": as_of.isoformat(),
        "snapshot_date": snapshot_date.isoformat() if snapshot_date else None,
        "coverage_short": 1 if coverage_short else 0,
        "ranked_count": len(result.main),
        "fx_source": fx_source,
        "provenance": provenance,
        # The universe this ranking was struck on, part of the COMPARISON
        # BASIS. Written as the run gave it -- sorted and upper-cased so
        # `--tier B --tier A` and `--tier A --tier B` are the same run.
        "tiers": ",".join(sorted(t.upper() for t in tiers)) or None,
    }
    rows: list[dict] = []
    for index, ranked in enumerate(result.main, start=1):
        scored = ranked.scored
        rows.append({**common,
                     "ticker": ranked.ticker,
                     "position": index,
                     "section": SECTION_RANKED,
                     "combined": ranked.combined,
                     "quality_rank": ranked.quality_rank,
                     "ey_rank": ranked.ey_rank,
                     "operating_profitability": scored.operating_profitability,
                     "earnings_yield": scored.earnings_yield,
                     "quality_state": scored.quality_state})
    for index, ranked in enumerate(result.yield_only, start=1):
        scored = ranked.scored
        rows.append({**common,
                     "ticker": ranked.ticker,
                     "position": index,
                     "section": SECTION_EY_ONLY,
                     "combined": None,
                     "quality_rank": None,
                     "ey_rank": ranked.ey_rank,
                     "operating_profitability": scored.operating_profitability,
                     "earnings_yield": scored.earnings_yield,
                     "quality_state": scored.quality_state})
    for scored in list(result.unrankable) + list(result.stale):
        rows.append({**common,
                     "ticker": scored.ticker,
                     "position": None,
                     "section": ("stale" if scored in result.stale
                                 else "unrankable"),
                     "combined": None, "quality_rank": None, "ey_rank": None,
                     "operating_profitability": scored.operating_profitability,
                     "earnings_yield": scored.earnings_yield,
                     "quality_state": scored.quality_state})
    return rows


def positions(rows: Sequence[dict], section: str = SECTION_RANKED) -> dict[str, int]:
    """ticker -> position, for one section's rows that have a position."""
    return {row["ticker"]: row["position"] for row in rows
            if row.get("section") == section and row.get("position")}


def ranked_count(rows: Sequence[dict]) -> int:
    return len(positions(rows))


# --- what counts as a change ----------------------------------------------


ENTERED = "ENTERED TOP 10"
LEFT = "LEFT TOP 10"
JUMPED = "JUMPED INTO TOP 10"
UNRANKABLE = "NO LONGER RANKABLE"
INCOMPLETE = "RUN INCOMPLETE"


@dataclass(frozen=True)
class Change:
    kind: str
    ticker: str
    detail: str
    #: The watchlist status where the name is already on it, else "".
    on_watchlist: str = ""

    def line(self) -> str:
        where = f" [{self.on_watchlist} on the watchlist]" if self.on_watchlist else ""
        return f"{self.kind}: {self.ticker}{where} — {self.detail}"


@dataclass
class Coverage:
    """Whether this run may report changes at all (E93)."""

    short: bool
    reason: str = ""
    previous_ranked: int = 0
    current_ranked: int = 0
    throttled: int = 0

    @property
    def line(self) -> str:
        return (f"ranked {self.current_ranked} against {self.previous_ranked} "
                f"last run ({self.current_ranked / self.previous_ranked:.1%} "
                f"of it); {self.throttled} ticker(s) throttled"
                if self.previous_ranked else
                f"ranked {self.current_ranked}; no previous run to compare")


def assess_coverage(previous: Sequence[dict], current: Sequence[dict],
                    *, throttled: int = 0,
                    tolerance: float = COVERAGE_TOLERANCE) -> Coverage:
    """Is this run complete enough for its changes to mean anything? (E93)

    TWO SIGNALS, and the direct one is trusted first. **Any throttling at all
    makes the run incomplete**: the fundamentals step fetches one ticker at a
    time with backoff, and a throttle is the endpoint telling us outright
    that we did not get everything. The count comparison is the indirect
    signal, for a shortfall that arrives some other way.

    A first run -- nothing stored before it -- is NOT short. It has nothing
    to diff and reports no changes for that reason, not this one.
    """
    before, now = ranked_count(previous), ranked_count(current)
    if throttled:
        return Coverage(True, (f"{throttled} ticker(s) were THROTTLED during "
                               f"the fundamentals fetch, so the ranking is "
                               f"missing names for a reason that has nothing "
                               f"to do with the market"),
                        before, now, throttled)
    if before and now < before * tolerance:
        return Coverage(True, (f"ranked {now} names against {before} last run "
                               f"-- {before - now} fewer, past the "
                               f"{1 - tolerance:.0%} tolerance"),
                        before, now, throttled)
    return Coverage(False, "", before, now, throttled)


def detect_changes(previous: Sequence[dict], current: Sequence[dict], *,
                   watchlist: dict[str, str] | None = None,
                   top_n: int = TOP_N,
                   watch_n: int = WATCH_N) -> list[Change]:
    """E93's change set. Returns [] where nothing crossed a boundary.

    **Nothing here fires on movement inside the top 20.** A name at 14 that
    moves to 6 produces one ENTERED, not a movement report; a name at 6 that
    moves to 14 produces one LEFT. A name that moves from 12 to 18 produces
    NOTHING, and that is the ruling, not an omission.
    """
    watchlist = watchlist or {}
    before, now = positions(previous), positions(current)
    if not before:
        return []                    # a first run has nothing to compare to

    before_top = {t for t, p in before.items() if p <= top_n}
    now_top = {t for t, p in now.items() if p <= top_n}
    changes: list[Change] = []

    for ticker in sorted(now_top - before_top):
        was = before.get(ticker)
        # E93's one-step jump: outside the OUTER ring last week, inside the
        # inner one now. Reported as its own kind because a move that size
        # is not the same event as drifting across the boundary.
        if was is None or was > watch_n:
            where = f"was #{was}" if was else "was not ranked"
            changes.append(Change(JUMPED, ticker,
                                  f"{where}, now #{now[ticker]} "
                                  f"(outside {watch_n} → inside {top_n})",
                                  watchlist.get(ticker, "")))
        else:
            changes.append(Change(ENTERED, ticker,
                                  f"#{was} → #{now[ticker]}",
                                  watchlist.get(ticker, "")))

    for ticker in sorted(before_top - now_top):
        if ticker in now:
            detail = f"#{before[ticker]} → #{now[ticker]}"
        elif ticker in {r["ticker"] for r in current}:
            state = next((r for r in current if r["ticker"] == ticker), {})
            detail = (f"#{before[ticker]} → no longer ranked "
                      f"({state.get('section', 'absent')})")
        else:
            detail = f"#{before[ticker]} → absent from the run entirely"
        changes.append(Change(LEFT, ticker, detail, watchlist.get(ticker, "")))

    # The DATA event: ranked before, present now but unable to rank. Reported
    # for any previously ranked name, not only a top-10 one -- this is how a
    # feed or tag-map breakage announces itself, and it does not announce
    # itself politely at the top of the list.
    unrankable_now = {r["ticker"]: r for r in current
                      if r.get("position") is None}
    for ticker in sorted(set(before) & set(unrankable_now)):
        row = unrankable_now[ticker]
        changes.append(Change(
            UNRANKABLE, ticker,
            f"was #{before[ticker]}, now {row.get('section', 'unrankable')}"
            + (f" ({row['quality_state']})" if row.get("quality_state") else ""),
            watchlist.get(ticker, "")))
    return changes


def load_watchlist_statuses(path: Path = WATCHLIST_PATH) -> dict[str, str]:
    """ticker -> status, for annotating an entrant already on the list."""
    from .config import ConfigError, load_watchlist

    try:
        return {e.ticker.upper(): e.status for e in load_watchlist(path)}
    except (ConfigError, OSError) as exc:
        log.warning("watchlist statuses unavailable (%s); entrants will not "
                    "be annotated", exc)
        return {}


# --- retention -------------------------------------------------------------


def prune_snapshots(root: Path, *, keep: int = KEEP_SNAPSHOTS,
                    dry_run: bool = False) -> list[Path]:
    """Delete all but the newest ``keep`` snapshot directories (E93).

    DELETES ONLY `<root>/<YYYY-MM-DD>/` directories. It never touches a
    ranking, a manifest, `config/` or `reports/` -- the rankings are what
    every future comparison stands on and are kept forever.
    """
    if not root.exists():
        return []
    dated = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        try:
            date.fromisoformat(child.name)
        except ValueError:
            continue                 # not a dated snapshot; leave it alone
        dated.append(child)
    dated.sort(key=lambda p: p.name, reverse=True)
    doomed = dated[keep:]
    for path in doomed:
        if dry_run:
            log.info("would prune %s", path)
            continue
        shutil.rmtree(path)
        log.info("pruned %s", path)
    return doomed


# --- the report ------------------------------------------------------------


def render_screen_report(*, as_of: date, run_ts: datetime,
                         coverage: Coverage, changes: Sequence[Change],
                         current: Sequence[dict],
                         previous_as_of: str | None,
                         pruned: Sequence[Path] = (),
                         rank_report: str = "",
                         genuine_baseline: bool = True,
                         baseline_provenance: str | None = None,
                         basis_reasons: "Sequence[str]" = (),
                         readiness: "Sequence" = ()) -> str:
    out: list[str] = [f"# SCREEN — {as_of.isoformat()}", ""]
    out.append(f"**Run:** {run_ts.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    out.append("")
    out.append("*E93: this run snapshots, ranks and reports. It does not "
               "write `config/watchlist.yaml` and it enters no name as "
               "PIPELINE — that stamps `dd_at_entry` and freezes Gate 1 "
               "(E12), and a clock may not make an irreversible stamp.*")
    out.append("")
    out.append(f"- **Ranked:** {coverage.current_ranked}")
    out.append(f"- **Compared against:** "
               f"{previous_as_of or 'nothing — this is the first stored run'}")
    out.append(f"- **Coverage:** {coverage.line}")
    if pruned:
        out.append(f"- **Pruned:** {', '.join(p.name for p in pruned)} "
                   f"(keeping the last {KEEP_SNAPSHOTS} snapshots; every "
                   f"ranking is kept)")
    out.append("")

    if previous_as_of and basis_reasons and not coverage.short:
        out.append("## THE TWO RUNS WERE NOT STRUCK THE SAME WAY "
                   "— NO POINTER SENT")
        out.append("")
        out.append(f"**This run may not be diffed against `{previous_as_of}`, "
                   f"for {'this reason' if len(basis_reasons) == 1 else 'these reasons'}:**")
        out.append("")
        for reason in basis_reasons:
            out.append(f"- {reason}")
        out.append("")
        if not genuine_baseline:
            # The concrete case the provenance clause was written for. It
            # prints only while that clause is the one firing.
            out.append(
                f"On the baseline's provenance in particular: "
                f"`{previous_as_of}` (provenance "
                f"`{baseline_provenance or 'unrecorded'}`) was regenerated on "
                f"2026-08-31 from that date's stored snapshot after the "
                f"original artifact was destroyed, and re-ranked under LATER "
                f"CODE than the original ever used — commit `d171724` changed "
                f"filter 2's leverage limb, which is why it ranks 216 names "
                f"where the original ranked 202.")
            out.append("")
        out.append("**So anything below could be an artefact of that rather "
                   "than market movement, and the notification carried only the "
                   "run's status and why nothing was compared (E116).** The "
                   "changes are still printed: they are the best available "
                   "reading and worth your eye. What is withheld is the "
                   "*pointer*, because a pointer asserts *this is a market "
                   "move* and that is the one thing these cannot be trusted "
                   "to be.")
        out.append("")
        out.append("**Real change detection resumes with the next run**, once "
                   "two consecutive runs were struck the same way. Nothing "
                   "expires on a date and nobody has to remember anything — "
                   "the rule stops applying by itself.")
        out.append("")

    if coverage.short:
        out.append("## RUN INCOMPLETE — NO CHANGE POINTER SENT")
        out.append("")
        out.append(f"**{coverage.reason}.**")
        out.append("")
        out.append("E93: a run whose ranked coverage falls short of the "
                   "previous run's reports the shortfall and stops. Any "
                   "crossing this run appears to show would be an artefact "
                   "of the names that are missing, not a fact about the "
                   "market — and a phantom *\"eight names left the top 10\"* "
                   "would cost the whole chain its credibility.")
        out.append("")
        out.append("**No change was computed, and the notification said only "
                   "that the run was incomplete (E116).** The "
                   "ranking IS stored, so next week compares against it.")
        out.append("")
    elif not previous_as_of:
        out.append("## FIRST STORED RUN — nothing to compare")
        out.append("")
        out.append("The ranking is stored. From the next run on, changes are "
                   "computed against it.")
        out.append("")
    elif not changes:
        out.append("## NO CHANGE")
        out.append("")
        out.append(f"No name entered or left the top {TOP_N}, none jumped in "
                   f"from outside {WATCH_N}, and no previously ranked name "
                   f"became unrankable.")
        out.append("")
        out.append(f"*Movement INSIDE the top {WATCH_N} is not reported and "
                   f"is not an omission (E93): the key sums two placings "
                   f"across ~{coverage.current_ranked} candidates and a name "
                   f"moves several places on a price move alone.*")
        out.append("")
    else:
        out.append(f"## CHANGES — {len(changes)}")
        out.append("")
        for change in changes:
            out.append(f"- {change.line()}")
        out.append("")

    top = [r for r in current if r.get("section") == SECTION_RANKED
           and r.get("position") and r["position"] <= WATCH_N]
    if top:
        out.append(f"## THE TOP {WATCH_N}")
        out.append("")
        out.append("| # | Ticker | Combined | Quality | Yield | Op prof | Earn yld |")
        out.append("|---:|---|---:|---:|---:|---:|---:|")
        for row in top:
            op = row.get("operating_profitability")
            ey = row.get("earnings_yield")
            out.append(
                f"| {row['position']} | `{row['ticker']}` | "
                f"{row.get('combined') if row.get('combined') is not None else '--'} | "
                f"{row.get('quality_rank') if row.get('quality_rank') is not None else '--'} | "
                f"{row.get('ey_rank') if row.get('ey_rank') is not None else '--'} | "
                f"{op:.1%} | {ey:.1%} |"
                if op is not None and ey is not None else
                f"| {row['position']} | `{row['ticker']}` | -- | -- | -- | -- | -- |")
        out.append("")

    if readiness:
        # E94: what it would take to value each of these. The ranked list
        # says which names are cheap; this says which are CHEAP TO VALUE,
        # which is a different and more actionable fact.
        from .readiness import render_readiness_table

        out.append(f"## WHAT IT WOULD TAKE TO VALUE THE TOP {len(readiness)} (E94)")
        out.append("")
        out.extend(render_readiness_table(readiness))
        out.append("")

    if rank_report:
        out.append("<details><summary>the ranking run's own report</summary>")
        out.append("")
        out.append(rank_report)
        out.append("")
        out.append("</details>")
        out.append("")

    out.append("---")
    out.append("")
    out.append("*E93. Nothing was written to `config/watchlist.yaml`, no name "
               "was entered as PIPELINE, and no gate was scored.*")
    return "\n".join(out) + "\n"


def notification_lines(changes: Sequence[Change], report: Path,
                       limit: int = 6) -> list[str]:
    """A few lines that read on a lock screen. Same shape as E92's pointer."""
    lines = [change.line() for change in changes[:limit]]
    if len(changes) > limit:
        lines.append(f"...and {len(changes) - limit} more")
    lines.append(str(report))
    return lines


def new_in_watch_band(previous: Sequence[dict], current: Sequence[dict], *,
                      changes: Sequence[Change] = (),
                      watch_n: int = WATCH_N) -> list[tuple[str, int]]:
    """E116: names inside the top `watch_n` now and not last run, best first.

    A name E93 already carries as a change is left out -- it is on the
    message once, under its own kind. A first run has nothing to compare to.
    """
    before, now = positions(previous), positions(current)
    if not before:
        return []
    carried = {change.ticker for change in changes}
    return sorted(((t, p) for t, p in now.items()
                   if p <= watch_n and before.get(t, watch_n + 1) > watch_n
                   and t not in carried),
                  key=lambda item: item[1])


def weekly_message(*, as_of: date, coverage: Coverage, changes: Sequence[Change],
                   also_new: Sequence[tuple[str, int]], basis_reasons: Sequence[str],
                   first_run: bool, report: Path,
                   limit: int = 6) -> tuple[str, list[str]]:
    """E116: the Saturday message, sent on EVERY run that reaches its end.

    Its title says whether the run worked. The E93 suppressions still hold:
    an incomplete run and a run struck differently from its baseline name
    no name at all -- only why nothing was compared.
    """
    if coverage.short:
        return (f"vss weekly screen {as_of}: INCOMPLETE",
                [f"{coverage.reason}.", "Nothing was compared (E93).", str(report)])
    title = f"vss weekly screen {as_of}: OK"
    lines = [f"Ranked {coverage.current_ranked}."]
    if first_run:
        lines.append("First stored run: nothing to compare.")
    elif basis_reasons:
        lines.append("Comparison withheld: " + "; ".join(basis_reasons))
    else:
        lines.extend(notification_lines(changes, report, limit=limit)[:-1])
        if also_new:
            lines.append(f"Also new in top {WATCH_N}: "
                         + ", ".join(f"{t} #{p}" for t, p in also_new))
        if not changes and not also_new:
            lines.append(f"Nothing new in the top {WATCH_N}.")
    lines.append(str(report))
    return title, lines


# --- the weekly run --------------------------------------------------------


@dataclass
class WeeklyRun:
    as_of: date
    coverage: Coverage
    changes: list[Change] = field(default_factory=list)
    report_path: Path | None = None
    rows: list[dict] = field(default_factory=list)
    pruned: list[Path] = field(default_factory=list)
    notified: str = ""
    report: str = ""
    genuine_baseline: bool = True
    #: Why this run's changes may not be diffed against the baseline, or
    #: empty. Non-empty withholds the POINTER and never the report.
    basis_reasons: list[str] = field(default_factory=list)


def run_weekly(*, as_of: date | None = None, now: datetime | None = None,
               db_path: Path = DB_PATH,
               reports_dir: Path | None = None,
               watchlist_path: Path = WATCHLIST_PATH,
               snapshot_root: Path | None = None,
               universe_dir: Path | None = None,
               runs_root: Path | None = None,
               tiers: Sequence[str] = ("A",),
               keep_snapshots: int = KEEP_SNAPSHOTS,
               dry_run: bool = False,
               notify: bool = True,
               limit: int | None = None) -> WeeklyRun:
    """The whole chain, then the diff, the report and the pointer (E93).

    snapshot -> fundamentals -> rank -> store -> compare -> report -> prune
    -> notify. `--write-pipeline` IS NEVER PASSED and the watchlist's bytes
    are compared either side of the run.
    """
    from . import heartbeat as HB
    from . import screen as screen_mod
    from . import snapshot as snapshot_store
    from .fundamentals import STATUS_THROTTLED, status_counts
    from .refresh import assert_no_watchlist_write, post_needs_owner
    from .store import persist_ranking, previous_ranking, ranking_run_dates

    run_ts = now or datetime.now().astimezone()
    as_of = as_of or run_ts.date()
    reports_dir = reports_dir or REPORTS_DIR
    snapshot_root = snapshot_root or screen_mod.snapshot_store.SNAPSHOT_ROOT
    universe_dir = universe_dir or screen_mod.UNIVERSE_DIR
    watchlist_before = Path(watchlist_path).read_bytes()

    # runs_root IS PASSED EXPLICITLY, and it is not decoration. `rank()`
    # defaults it to data/screener_runs and WRITES ranking.csv there; a run
    # pointed at a scratch snapshot root but left on the default runs_root
    # overwrites the real ranking file for that date with its own. That
    # happened once, on 2026-08-31, to the 2026-08-29 file. A caller that
    # isolates one path must be able to isolate both.
    runs_root = runs_root if runs_root is not None else screen_mod.RUNS_ROOT
    common = dict(as_of=as_of, universe_dir=universe_dir, tiers=tiers,
                  snapshot_root=snapshot_root)

    # The dead man's switch, leg 1. A weekly run is a four-hour chain over a
    # thousand names; the failure that matters most here is the one that
    # dies at hour three, and a row written NOW is the only thing that can
    # tell that apart from a Saturday nobody looked at.
    completion_id = None
    if not dry_run:
        completion_id = HB.begin(db_path, kind=HB.KIND_WEEKLY,
                                 started_at=run_ts, as_of=as_of,
                                 dry_run=False)

    log.info("weekly screen %s: snapshotting the universe", as_of.isoformat())
    screen_mod.snapshot_only(**common, limit=limit)

    log.info("weekly screen %s: fetching fundamentals", as_of.isoformat())
    fundamentals = screen_mod.fetch_fundamentals(**common, limit=limit)
    counts = status_counts(fundamentals.outcome.records)
    throttled = counts.get(STATUS_THROTTLED, 0)

    log.info("weekly screen %s: ranking", as_of.isoformat())
    # write_pipeline is NOT passed. E93: this run enters no name.
    ranked = screen_mod.rank(**common, runs_root=runs_root)

    previous = previous_ranking(db_path, as_of.isoformat())
    previous_dates = [d for d in ranking_run_dates(db_path)
                      if d < as_of.isoformat()]
    rows = ranking_rows(ranked.result, run_ts=run_ts, as_of=as_of,
                        snapshot_date=ranked.upstream.upstream.snapshot_date,
                        fx_source=("replayed" if False else "fetched at run time"),
                        tiers=tiers)
    coverage = assess_coverage(previous, rows, throttled=throttled)
    for row in rows:
        row["coverage_short"] = 1 if coverage.short else 0

    # E93: an incomplete run reports the shortfall and computes NO changes.
    # Not "computes them and withholds the pointer" -- a number nobody may
    # act on should not be printed beside numbers they may.
    changes: list[Change] = []
    if not coverage.short:
        changes = detect_changes(previous, rows,
                                 watchlist=load_watchlist_statuses(watchlist_path))
    # The changes ARE computed and reported against a non-genuine baseline --
    # they are the best available reading and the owner may want to look at
    # them. Only the POINTER is withheld, because a pointer asserts "this is
    # a market move" and that is the one thing they cannot be trusted to be.
    genuine_baseline = baseline_is_genuine(previous)
    # The general rule, of which `genuine_baseline` is now one clause: a
    # pointer goes out only when the two runs were struck the same way.
    # Empty on the ordinary week, and it empties itself as soon as two
    # consecutive runs agree -- nothing expires on a date.
    basis_reasons = basis_mismatches(previous, rows) if previous else []

    pruned: list[Path] = []
    report_path = None
    if not dry_run:
        persist_ranking(db_path, rows)
        pruned = prune_snapshots(snapshot_root, keep=keep_snapshots)

    # E94: the readiness pass, over the top WATCH_N only -- it opens a store
    # and builds a probe record per name, which is far too much work to do
    # for 216. It reads and writes nothing.
    readiness = assess_top(ranked.result, limit=WATCH_N, as_of=as_of,
                           run_ts=run_ts)

    report = render_screen_report(
        as_of=as_of, run_ts=run_ts, coverage=coverage, changes=changes,
        current=rows, previous_as_of=(previous_dates[0] if previous_dates else None),
        pruned=pruned, rank_report=ranked.report,
        genuine_baseline=genuine_baseline,
        baseline_provenance=(previous[0].get("provenance") if previous else None),
        basis_reasons=basis_reasons,
        readiness=readiness)

    if not dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"SCREEN-{as_of.isoformat()}.md"
        report_path.write_text(report, encoding="utf-8")
        log.info("wrote %s", report_path)

    # E116: a message on EVERY run that reaches its end, saying whether it
    # worked. The E93 suppressions withhold the NAMES, never the status line.
    also_new = ([] if coverage.short or basis_reasons else
                new_in_watch_band(previous, rows, changes=changes))
    title, lines = weekly_message(
        as_of=as_of, coverage=coverage, changes=changes, also_new=also_new,
        basis_reasons=basis_reasons, first_run=not previous,
        report=report_path or Path("reports/"))
    sent = "not sent (dry run or --no-notify)"
    if notify and not dry_run:
        sent = post_needs_owner(lines, title=title)
        log.info("ntfy: %s", sent)
    notified = sent
    if coverage.short:
        notified = f"SUPPRESSED: the run was incomplete (E93); status line {sent}"
    elif basis_reasons:
        notified = f"SUPPRESSED: {'; '.join(basis_reasons)}; status line {sent}"
    log.info("notification: %s", notified)

    # E93, enforced and not merely intended.
    assert_no_watchlist_write(watchlist_before, Path(watchlist_path).read_bytes())

    # The run reached its end. RANKED coverage is what is recorded, because
    # it is the number E93 already judges the run on -- a chain that
    # completed while ranking a third of the names is not a run that worked.
    HB.finish(db_path, completion_id, finished_at=datetime.now().astimezone(),
              expected=coverage.previous_ranked or coverage.current_ranked,
              covered=coverage.current_ranked, errors=coverage.throttled,
              detail=("coverage SHORT: " + coverage.reason) if coverage.short
                     else coverage.line)

    return WeeklyRun(as_of=as_of, coverage=coverage, changes=changes,
                     report_path=report_path, rows=rows, pruned=pruned,
                     notified=notified, report=report,
                     genuine_baseline=genuine_baseline,
                     basis_reasons=basis_reasons)


def assess_top(result, *, limit: int = WATCH_N, as_of: date | None = None,
               run_ts: datetime | None = None,
               manual_dir: Path | None = None,
               views_dir: Path | None = None) -> list:
    """E94's readiness assessment over the top `limit` ranked names.

    Read-only, and defensive: one name whose store is malformed must not
    cost the whole weekly report. A failure there is reported as that name's
    state, not raised.
    """
    from .readiness import STATE_NO_STORE, Readiness, assess

    out = []
    for ranked in list(result.main)[:limit]:
        scored = ranked.scored
        inputs = getattr(scored, "inputs", None)
        try:
            out.append(assess(
                ranked.ticker,
                price=getattr(inputs, "settled_close", None),
                quote_currency=getattr(inputs, "quote_currency", None),
                # E51/E96: the vendor's industry string, where the fetch
                # reached this name. Absent, only the owner-list limbs apply.
                industry=getattr(inputs, "industry", None),
                as_of=as_of, run_ts=run_ts,
                manual_dir=manual_dir, views_dir=views_dir))
        except Exception as exc:  # noqa: BLE001 -- one name never breaks the run
            log.warning("readiness for %s failed: %s: %s",
                        ranked.ticker, type(exc).__name__, exc)
            out.append(Readiness(ranked.ticker, STATE_NO_STORE,
                                 detail=f"assessment failed: "
                                        f"{type(exc).__name__}: {exc}"))
    return out
