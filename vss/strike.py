"""`vss strike` -- ONE FRONT DOOR for a re-strike off the store.

WHAT THIS IS. Sixteen dated scripts in `tools/` already do this work --
`restrike_e117_2026_09_19.py`, `strike_acn_gddy_nvr_ulta_2026_08_30.py` and
their kind. Each was written for one pass, each re-strikes a name off
`config/manual/<TICKER>.yaml` on the PRIOR RECORD's pre-registered growth
view, each writes a run record and a strike doc, and each prints a
before/after table. **This is a front door on that behaviour, not a
rewrite**: the record is still built by `runrecord.from_store`, the value
is still `record.strike()`, and the dated scripts stay where they are as
the history of what was struck when.

WHAT IT NEVER DOES. It does not write `config/watchlist.yaml` -- no
`fv_base`, no `tier`, no `mbp`, no `stop_price`, no `status`. Those are the
owner's act. `assert_no_watchlist_write` is the mechanical guarantee, on
`vss refresh`'s pattern, and a test holds it.

THE THREE REFUSALS (owner, 2026-09-20):

1. **NO REGISTERED GROWTH VIEW -> REFUSE.** E28: a view written after the
   solve is void, so a strike may not invent one. The view comes from the
   prior record; on a FIRST strike, from the entry's machine-readable
   `growth:` block (E109). Neither present is a refusal, not a default.
2. **THE SECTION 5 GATE IS BINDING BY DEFAULT.** E21: an UNVERIFIED figure
   the basis reads refuses section 5. `--ignore-gate` exists for the sweep
   case the dated scripts served -- and **prints its use in the strike doc
   and in the record's notes**, because a front door gets used routinely
   and a sweep's behaviour as the default would go silent within a few
   quarters (the owner's words, deciding it).
3. **A RECORD THAT WILL NOT FORM -> REFUSE**, naming the leg.

WHAT IT PRINTS, and this is link 5 of the chain: fv_base, bear, bull, the
MBP **with the tier on both sides**, g*, and WHICH LEG MOVED against the
previous record -- with the store's newest period and the settled close on
each side, so a value that moved only because the price moved cannot be
read as a re-strike.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

from . import fx
from . import manual as M
from . import metrics as MT
from . import runrecord as R
from . import valuation as V

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECORDS_DIR = PROJECT_ROOT / "reference" / "run-records"
WATCHLIST_PATH = PROJECT_ROOT / "config" / "watchlist.yaml"
DOCS_DIR = PROJECT_ROOT / "reference"

#: What `--ignore-gate` writes into the record and the doc. It is a
#: SENTENCE, not a flag name, because whoever reads the record next is not
#: reading this module.
IGNORE_GATE_NOTE = (
    "STRUCK WITH --ignore-gate: the section 5 gate REFUSED and the strike "
    "was made anyway. E21's refusal stands against this value -- a figure "
    "the basis reads is UNVERIFIED. The refusals are listed in this record "
    "and in the strike doc.")


class StrikeError(Exception):
    """A refusal. Nothing is written when one is raised."""


def assert_no_watchlist_write(before: str, after: str) -> None:
    """Mechanically: a strike never writes the watchlist (E92's pattern)."""
    if before != after:
        raise StrikeError(
            "VIOLATED: config/watchlist.yaml changed during a strike. A "
            "strike reads the store and the prior record, writes a run "
            "record and a doc, and prints -- it never writes fv_base, tier, "
            "mbp, stop_price or status. Nothing was written and the run is "
            "stopped.")


def latest_record(ticker: str, records_dir: Path = RECORDS_DIR
                  ) -> tuple[Path, R.RunRecord] | tuple[None, None]:
    """The newest run record for this ticker, by the record's own run_ts.

    The filename is not trusted for ordering -- `<TICKER>-<stamp>.json`
    carries a stamp a ruling chose, and two stamps on one day sort by
    string rather than by time.
    """
    best: tuple[Path, R.RunRecord] | tuple[None, None] = (None, None)
    for path in sorted(records_dir.glob(f"{ticker}-*.json")):
        stem = path.name[len(ticker) + 1:]
        if not re.match(r"\d{4}-\d{2}-\d{2}", stem):
            continue                      # not a dated record for this name
        try:
            record = R.RunRecord.from_dict(
                json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:  # noqa: BLE001 -- a corrupt record is named
            log.warning("%s: unreadable run record (%s)", path.name, exc)
            continue
        if record.ticker != ticker:
            continue
        if best[1] is None or record.run_ts > best[1].run_ts:
            best = (path, record)
    return best


def growth_for(entry, prior: R.RunRecord | None) -> R.Growth:
    """The PRE-REGISTERED view, from the prior record or the entry (E28).

    Never invented, never defaulted: a name with neither is a refusal.
    """
    if prior is not None:
        return prior.growth
    view = getattr(entry, "growth", None) if entry is not None else None
    if view is None or getattr(view, "base", None) is None:
        raise StrikeError(
            "NO REGISTERED GROWTH VIEW (E28). There is no prior run record "
            "to take one from, and the watchlist entry carries no `growth:` "
            "block. A growth view written AFTER a value is solved is VOID, "
            "so this command will not invent, default or infer one. Register "
            "the view in reference/growth-views/<TICKER>.md and on the entry "
            "first; then strike.")
    return R.Growth(base=float(view.base), view_file=str(view.view or ""),
                    view_date=getattr(view, "registered", None),
                    bear=(None if view.bear is None else float(view.bear)),
                    bull=(None if view.bull is None else float(view.bull)))


def tool_commit(stamp: str) -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True,
                             cwd=PROJECT_ROOT, check=True).stdout.strip()
    except Exception:  # pragma: no cover -- a memo, never a gate
        sha = "unknown"
    return f"vss strike {stamp}, {sha}"


def settled_close(ticker: str, quote_currency: str, *, run_ts: datetime,
                  as_of: date, cache_dir: Path | None = None
                  ) -> tuple[float | None, date | None]:
    """The settled close, in the RECORD's unit. A memo, never a gate."""
    from .fetch import get_history
    from .runner import CACHE_DIR
    try:
        fetched = get_history(ticker, cache_dir or CACHE_DIR, now=run_ts,
                              write=False)
        m = MT.compute(fetched.frame, as_of, MT.settled_through(run_ts))
        if m.last_close is None:
            return None, None
        return m.last_close / fx.minor_unit_divisor(quote_currency), m.last_close_date
    except Exception:  # noqa: BLE001 -- a memo, never a gate
        return None, None


def _tier_in_force(ticker: str, db_path: Path | None = None) -> int | None:
    """The tier the LAST NIGHTLY RUN recorded for this name.

    The tier is not in a run record -- it is a section 4.4 score on the
    watchlist -- so "the tier that was in force when the prior value was
    struck" is read from the run the tool itself made. None where the
    database has nothing, which prints as `--` rather than as a guess.
    """
    import sqlite3
    from .runner import DB_PATH
    try:
        connection = sqlite3.connect(db_path or DB_PATH)
        row = connection.execute(
            "select tier from run_metrics where ticker = ? and tier is not null "
            "order by as_of desc limit 1", (ticker,)).fetchone()
        return int(row[0]) if row and row[0] is not None else None
    except Exception:  # noqa: BLE001 -- provenance for a memo column
        return None


@dataclass(frozen=True)
class LegMove:
    """One leg, before and after. `moved` is what the table sorts on."""

    name: str
    before: object
    after: object
    note: str = ""

    @property
    def moved(self) -> bool:
        if isinstance(self.before, float) and isinstance(self.after, float):
            return abs(self.before - self.after) > 1e-9
        return self.before != self.after


@dataclass
class Strike:
    """One strike, with everything the table and the doc print."""

    ticker: str
    as_of: date
    stamp: str
    record: R.RunRecord
    prior: R.RunRecord | None = None
    prior_path: Path | None = None
    tier_before: int | None = None
    tier_after: int | None = None
    price: float | None = None
    price_date: date | None = None
    prior_price_date: date | None = None
    store_period: date | None = None
    prior_store_period: date | None = None
    gate_refusals: tuple[str, ...] = ()
    ignored_gate: bool = False
    legs: tuple[LegMove, ...] = ()

    # --- the four values, after and before -----------------------------
    @property
    def fv(self) -> float:
        return self.record.strike()

    @property
    def bear(self) -> float | None:
        g = self.record.growth.bear
        return None if g is None else self.record.strike(g)

    @property
    def bull(self) -> float | None:
        g = self.record.growth.bull
        return None if g is None else self.record.strike(g)

    def prior_value(self, growth: float | None = None) -> float | None:
        if self.prior is None:
            return None
        try:
            return self.prior.strike(growth)
        except Exception:  # noqa: BLE001 -- a prior that no longer replays
            return None

    def mbp(self, tier: int | None, value: float | None) -> float | None:
        """E90: the BASE-case value times the tier cushion."""
        if tier is None or value is None or tier not in V.TIER_CUSHION_E90:
            return None
        return round(value * V.TIER_CUSHION_E90[tier], 2)

    @property
    def g_star(self) -> float | None:
        if self.price is None:
            return None
        try:
            legs = self.record.legs()
            return V.implied_growth(
                price=self.price, fcf0=legs.fcf0, net_cash=legs.net_cash,
                shares=legs.shares, rate=self.record.rate.rate,
                terminal=self.record.conventions.terminal_growth,
                years=self.record.conventions.horizon_years)
        except Exception:  # noqa: BLE001 -- a memo
            return None


def leg_moves(record: R.RunRecord, prior: R.RunRecord | None) -> tuple[LegMove, ...]:
    """Every leg of the division, before and after. Nothing is re-derived:
    both sides are read off the records themselves."""
    def legs_of(rec):
        if rec is None:
            return None
        try:
            return rec.legs()
        except Exception:  # noqa: BLE001
            return None

    now, was = legs_of(record), legs_of(prior)
    out = [
        LegMove("FCF0", getattr(was, "fcf0", None), getattr(now, "fcf0", None)),
        LegMove("net debt", None if prior is None else prior.bridge.net_debt,
                record.bridge.net_debt),
        LegMove("divisor (shares)", None if prior is None else prior.shares.count,
                record.shares.count),
        LegMove("basis", None if prior is None else prior.basis, record.basis),
        LegMove("growth view",
                None if prior is None else _growth_text(prior.growth),
                _growth_text(record.growth),
                note="E28: the view is the prior record's, unchanged by a strike"),
        LegMove("discount rate", None if prior is None else prior.rate.rate,
                record.rate.rate),
        LegMove("lease treatment", None if prior is None else _first_sentence(prior.lease),
                _first_sentence(record.lease)),
    ]
    return tuple(out)


def _growth_text(growth: R.Growth) -> str:
    def pct(v):
        return "--" if v is None else f"{v:.2%}"
    return f"{pct(growth.base)} / {pct(growth.bear)} / {pct(growth.bull)}"


def _first_sentence(lease) -> str:
    text = getattr(lease, "sentence", "") or ""
    return text.split(".")[0][:90]


def strike_one(ticker: str, *, as_of: date, run_ts: datetime, stamp: str,
               entry=None, manual_dir: Path | None = None,
               records_dir: Path = RECORDS_DIR, ignore_gate: bool = False,
               note: str = "", cache_dir: Path | None = None,
               db_path: Path | None = None) -> Strike:
    """Re-strike one name off its store. Raises StrikeError on a refusal."""
    prior_path, prior = latest_record(ticker, records_dir)
    growth = growth_for(entry, prior)

    try:
        parsed = M.load_manual(ticker, directory=manual_dir or M.MANUAL_DIR)
    except Exception as exc:  # noqa: BLE001
        raise StrikeError(f"no store to strike from: {exc}") from exc
    basis = M.section5_basis(parsed)
    if basis is None:
        raise StrikeError(
            f"{ticker}: the store supplies no twelve-month basis (E19), so "
            f"there is nothing to strike.")

    gate = M.section5_gate(parsed, as_of=as_of)
    refusals = tuple(f"{r.kind}: {r.subject}" for r in gate.refusals)
    if gate.refused and not ignore_gate:
        raise StrikeError(
            f"{ticker}: THE SECTION 5 GATE REFUSES and --ignore-gate was not "
            f"given (E21). Nothing was written. Refusals: "
            + "; ".join(refusals))

    hand = tuple(i for i in (prior.inputs if prior else ()) if i.entered_by == "hand")
    price, price_date = settled_close(ticker, parsed.quote_currency,
                                      run_ts=run_ts, as_of=as_of,
                                      cache_dir=cache_dir)
    notes = note or (f"vss strike {stamp}: re-struck off the store on the "
                     f"record's pre-registered growth view"
                     + (f", after {prior_path.name}" if prior_path else
                        " (first strike: the view is the entry's)"))
    if ignore_gate and gate.refused:
        notes = f"{notes}. {IGNORE_GATE_NOTE}"

    record = R.from_store(
        parsed, basis, growth=growth, run_ts=run_ts, hand_inputs=hand,
        price_date=price_date,
        rate=(prior.rate if prior else None),
        conventions=(prior.conventions if prior else None),
        tool_commit=tool_commit(stamp), notes=notes)
    try:
        record.strike()
    except Exception as exc:  # noqa: BLE001 -- the leg is named, nothing written
        raise StrikeError(f"{ticker}: the record will not form -- {exc}") from exc

    tier_after = getattr(entry, "tier", None) if entry is not None else None
    return Strike(
        ticker=ticker, as_of=as_of, stamp=stamp, record=record, prior=prior,
        prior_path=prior_path,
        tier_before=_tier_in_force(ticker, db_path), tier_after=tier_after,
        price=price, price_date=price_date,
        prior_price_date=(prior.dates.price if prior else None),
        store_period=parsed.newest_period_end,
        prior_store_period=(prior.dates.flows_window_end if prior else None),
        gate_refusals=refusals, ignored_gate=bool(ignore_gate and gate.refused),
        legs=leg_moves(record, prior))


# --- what it prints ------------------------------------------------------

def _num(value, spec=",.2f") -> str:
    return format(value, spec) if isinstance(value, (int, float)) else "--"


def _move(before, after) -> str:
    if not (isinstance(before, float) and isinstance(after, float)) or not before:
        return ""
    return f"{after / before - 1:+.1%}"


def table(s: Strike) -> str:
    """The before/after table -- link 5 of the chain."""
    prior_fv = s.prior_value()
    head = (f"{s.ticker} — strike {s.as_of.isoformat()}"
            + (f"   against {s.prior_path.name}" if s.prior_path
               else "   (first strike: no prior record)"))
    rows = [
        ("fv_base", _num(prior_fv), _num(s.fv), _move(prior_fv, s.fv)),
        ("  bear", _num(s.prior_value(s.record.growth.bear)), _num(s.bear),
         _move(s.prior_value(s.record.growth.bear), s.bear)),
        ("  bull", _num(s.prior_value(s.record.growth.bull)), _num(s.bull),
         _move(s.prior_value(s.record.growth.bull), s.bull)),
    ]
    mbp_before = s.mbp(s.tier_before, prior_fv)
    mbp_after = s.mbp(s.tier_after, s.fv)
    rows.append((
        f"MBP (E90)  tier {s.tier_before if s.tier_before is not None else '--'}"
        f" -> {s.tier_after if s.tier_after is not None else '--'}",
        _num(mbp_before), _num(mbp_after), _move(mbp_before, mbp_after)))
    if s.tier_before != s.tier_after and mbp_before and mbp_after:
        rows.append(("  of which the tier",
                     "", "", _move(s.mbp(s.tier_before, s.fv), mbp_after)))
    rows.append(("g*", "", _num(s.g_star, ".2%"), ""))

    width = max(len(r[0]) for r in rows)
    out = [head, ""]
    out.append(f"{'':<{width}}  {'before':>14}  {'after':>14}  {'move':>7}")
    for name, before, after, move in rows:
        out.append(f"{name:<{width}}  {before:>14}  {after:>14}  {move:>7}")

    out += ["", "WHICH LEG MOVED"]
    moved = [l for l in s.legs if l.moved]
    for leg in moved:
        before = _num(leg.before, ",.0f") if isinstance(leg.before, float) else (
            "--" if leg.before is None else str(leg.before))
        after = _num(leg.after, ",.0f") if isinstance(leg.after, float) else str(leg.after)
        pct = _move(leg.before, leg.after)
        out.append(f"  {leg.name:<18} {before:>22} -> {after:<22} {pct:>7}"
                   + (f"   {leg.note}" if leg.note else ""))
    unchanged = [l.name for l in s.legs if not l.moved]
    if unchanged:
        out.append(f"  unchanged: {', '.join(unchanged)}")

    out += ["", "WHAT THE TWO SIDES STAND ON"]
    # The BASIS WINDOW END is the comparable quantity: both records have
    # one. The store's newest period is a fact about the store TODAY and
    # belongs on its own line -- printing it opposite the prior record's
    # window end would compare two different things and read as movement.
    out.append(f"  basis window end        "
               f"{s.prior_store_period or '--'} -> "
               f"{s.record.dates.flows_window_end or '--'}")
    out.append(f"  settled close           "
               f"{s.prior_price_date or '--'} -> "
               f"{s.price_date or '--'}  ({_num(s.price)})")
    out.append(f"  store's newest period, today: {s.store_period or '--'}"
               + ("   <- NEWER THAN THE BASIS: a quarter has landed that this "
                  "strike did not read (E19 chooses ONE window)"
                  if (s.store_period and s.record.dates.flows_window_end
                      and s.store_period > s.record.dates.flows_window_end)
                  else ""))
    if s.ignored_gate:
        out += ["", "  *** --ignore-gate: " + "; ".join(s.gate_refusals) + " ***"]
    return "\n".join(out)


def document(s: Strike) -> str:
    """The strike doc, in the shape the dated scripts wrote."""
    prior_fv = s.prior_value()
    lines = [f"# {s.ticker} -- struck {s.as_of.isoformat()}", "",
             f"*Struck by `vss strike` off `config/manual/{s.ticker}.yaml` on "
             f"the pre-registered growth view "
             f"{_growth_text(s.record.growth)}"
             + (f", carried from {s.prior_path.name}" if s.prior_path
                else " (first strike, from the entry)")
             + ". Nothing here writes the watchlist: fv_base, tier, mbp and "
               "stop_price are the owner's.*", "",
             f"- **basis:** {s.record.basis}",
             f"- **fv_base:** {_num(prior_fv)} -> **{_num(s.fv)}** "
             f"(bear {_num(s.bear)}, bull {_num(s.bull)})",
             f"- **FCF0:** {_num(s.record.fcf0(), ',.0f')}",
             f"- **net debt:** {_num(s.record.bridge.net_debt, ',.0f')}",
             f"- **divisor:** {_num(s.record.shares.count, ',.0f')}",
             f"- **lease:** {getattr(s.record.lease, 'sentence', '')}"]
    mbp_after = s.mbp(s.tier_after, s.fv)
    if mbp_after is not None:
        lines.append(f"- **MBP (E90, tier {s.tier_after}):** "
                     f"{_num(s.mbp(s.tier_before, prior_fv))} -> {_num(mbp_after)}"
                     + (f"  -- THE TIER MOVED {s.tier_before} -> {s.tier_after}"
                        if s.tier_before != s.tier_after else ""))
    if s.price is not None:
        lines.append(f"- **close {s.price_date}:** {_num(s.price)}; "
                     f"g* {_num(s.g_star, '.2%')}")
    lines.append(f"- **store's newest period:** {s.store_period or '--'}")
    if s.ignored_gate:
        lines += ["", f"> **{IGNORE_GATE_NOTE}**", "",
                  *[f"> - {r}" for r in s.gate_refusals]]
    lines += ["", "```", table(s), "```", "",
              f"Record: `reference/run-records/{s.ticker}-{s.stamp}.json`", ""]
    return "\n".join(lines)


def write_outputs(s: Strike, *, records_dir: Path = RECORDS_DIR,
                  docs_dir: Path = DOCS_DIR) -> tuple[Path, Path]:
    records_dir.mkdir(parents=True, exist_ok=True)
    record_path = records_dir / f"{s.ticker}-{s.stamp}.json"
    record_path.write_text(json.dumps(s.record.to_dict(), indent=1) + "\n",
                           encoding="utf-8")
    doc_path = docs_dir / f"{s.ticker}-STRIKE-{s.stamp}.md"
    doc_path.write_text(document(s), encoding="utf-8")
    return record_path, doc_path


def run_strike(*, ticker: str, as_of: date | None = None,
               dry_run: bool = False, stamp: str | None = None,
               note: str = "", ignore_gate: bool = False,
               watchlist_path: Path = WATCHLIST_PATH,
               manual_dir: Path | None = None,
               records_dir: Path = RECORDS_DIR,
               docs_dir: Path = DOCS_DIR,
               now: datetime | None = None) -> tuple[int, str]:
    """The CLI's entry point. Returns (exit code, what to print)."""
    from .config import load_watchlist
    run_ts = now or datetime.now().astimezone()
    as_of = as_of or run_ts.date()
    stamp = stamp or as_of.isoformat()

    entry = None
    watchlist_before = ""
    if watchlist_path.exists():
        watchlist_before = watchlist_path.read_text(encoding="utf-8")
        wanted = ticker.strip().upper()
        entry = next((e for e in load_watchlist(watchlist_path)
                      if e.ticker.upper() == wanted), None)
    if entry is None:
        log.warning("%s is not on the watchlist: the growth view must come "
                    "from a prior run record, and no tier is available for "
                    "the MBP line", ticker)

    try:
        struck = strike_one(ticker, as_of=as_of, run_ts=run_ts, stamp=stamp,
                            entry=entry, manual_dir=manual_dir,
                            records_dir=records_dir, ignore_gate=ignore_gate,
                            note=note)
    except StrikeError as exc:
        return 2, f"REFUSED -- {exc}"

    out = [table(struck), ""]
    if dry_run:
        out.append("DRY RUN -- no record written, no strike doc written.")
        out += ["", "The document it would write:", "", document(struck)]
    else:
        record_path, doc_path = write_outputs(struck, records_dir=records_dir,
                                              docs_dir=docs_dir)
        for written in (record_path, doc_path):
            # A scratch directory outside the repo is how the tests run; a
            # path that is not under the project prints whole.
            try:
                shown = written.relative_to(PROJECT_ROOT)
            except ValueError:
                shown = written
            out.append(f"Wrote {shown}")
        out.append("The watchlist was NOT written: fv_base, tier, mbp and "
                   "stop_price stay the owner's act.")
    if watchlist_before:
        assert_no_watchlist_write(watchlist_before,
                                  watchlist_path.read_text(encoding="utf-8"))
    return 0, "\n".join(out)
