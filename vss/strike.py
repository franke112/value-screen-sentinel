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
4. **NO EVENTS LEDGER, OR ONE OLDER THAN A WEEK -> REFUSE** (E140(4),
   2026-10-27). Every deal after the balance sheet enters the bridge from
   `reference/events/<TICKER>.yaml`, and a strike on a stale sweep is how
   CENTA's 2026-10-20 strike missed Burpee, announced the day before.

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
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

from . import events as EV
from . import fx
from . import history as HI
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
    #: E145's tests and the three anchors, printed and never valued.
    quality: tuple = ()
    history_check: tuple[str, ...] = ()

    # --- the four values, after and before -----------------------------
    @property
    def fv(self) -> float:
        return self.record.strike()

    @property
    def e142(self) -> bool:
        return self.record.e140 is not None and self.record.e140.e142 is not None

    @property
    def bear(self) -> float | None:
        g = self.record.growth.bear
        if g is None:
            return None
        return self.record.strike(g, case="bear") if self.e142 else self.record.strike(g)

    @property
    def bull(self) -> float | None:
        g = self.record.growth.bull
        if g is None:
            return None
        return self.record.strike(g, case="bull") if self.e142 else self.record.strike(g)

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
        if self.e142:
            return self.record.implied_growth(self.price)
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
                note=("E144: derived from the issuer's history"
                      if record.growth.view_file.startswith("E144") else
                      "E28: the view is the prior record's, unchanged by a strike")),
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
               db_path: Path | None = None,
               events_dir: Path | None = None,
               history_dir: Path | None = None) -> Strike:
    """Re-strike one name off its store. Raises StrikeError on a refusal."""
    prior_path, prior = latest_record(ticker, records_dir)
    growth = growth_for(entry, prior)
    # E144: the view is DERIVED from the issuer's own history where it can
    # be; the registered view stands, marked, where it cannot.
    history = HI.load(ticker, directory=history_dir or HI.HISTORY_DIR)
    derived = HI.derived_growth(history) if history is not None else None
    if derived is not None:
        growth = R.Growth(base=derived.base, bear=derived.bear, bull=derived.bull,
                          view_file=f"E144: derived from {history.path}",
                          view_date=as_of)
    growth_how = (derived.how if derived is not None else
                  "VIEW, NOT DERIVED (E144(4)): "
                  + ("no history file" if history is None else
                     "fewer than five organic years in " + history.path)
                  + f"; the registered view {growth.view_file or '(entry)'}")
    try:
        ledger = EV.load_ledger(ticker, directory=events_dir or EV.EVENTS_DIR)
        EV.check_fresh(ledger, as_of)
    except EV.EventsError as exc:
        raise StrikeError(f"{ticker}: {exc}. Nothing was written.") from exc

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
        tool_commit=tool_commit(stamp), notes=notes, ledger=ledger)
    record, quality, history_check = apply_e142(record, history, growth_how)
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
        legs=leg_moves(record, prior), quality=quality,
        history_check=history_check)


def apply_e142(record: R.RunRecord, history: "HI.History | None",
               growth_how: str) -> tuple[R.RunRecord, tuple, tuple[str, ...]]:
    """E142-E145 onto a freshly built record: the parameters the history
    gives, and the quality tests. A record the E140 block could not form
    is returned as it is, and refuses where it would have."""
    if record.e140 is None:
        return record, (), ()
    try:
        flow = record.normalised_flow()
    except V.ValuationError:
        return record, (), ()
    tax = record.e140.tax_rate
    fallback = record.growth.base
    full = worst = None
    if history is not None and tax is not None:
        full, worst = HI.roiic(history, tax, fallback)
    cyc = HI.cycle(history) if history is not None else HI.Cycle(
        False, 1.0, None, "no history file: no cycle test (E143(3))")
    flows = list(flow.years)
    mean = sum(flows) / len(flows) if flows else 0.0
    if cyc.level_bear is not None:
        bear_level, bear_how = cyc.level_bear, ""
    elif mean > 0:
        bear_level = max(0.0, min(flows) / mean)
        bear_how = (f"; bear level x{bear_level:.3f}: the weakest E140 year "
                    f"{min(flows):,.0f} over the mean {mean:,.0f} (E143(4))")
    else:
        bear_level, bear_how = 0.0, "; bear level x0: the mean is not positive"
    params = R.E142Params(
        history=history.path if history is not None else "",
        repeat_buyer=flow.repeat_buyer,
        acquisitions_mean=flow.acquisitions_mean,
        roiic_base=None if full is None else full.value,
        roiic_bear=None if worst is None else max(0.0, worst.value),
        roiic_base_how="" if full is None else full.how,
        roiic_bear_how="" if worst is None else worst.how,
        cyclical=cyc.cyclical, level_base=cyc.level_base, level_bear=bear_level,
        level_how=cyc.how + bear_how, growth_how=growth_how)
    record = replace(record, e140=replace(record.e140, e142=params))
    if params.repeat_buyer and (params.roiic_base is None or params.roiic_bear is None):
        # E142(6) with E106's floor: an absent ROIIC that cannot move the
        # value 3.5% is struck at zero, the conservative end.
        try:
            neutral = replace(record, e140=replace(record.e140, e142=replace(
                params, roiic_base=record.rate.rate, roiic_bear=record.rate.rate)))
            zero = replace(record, e140=replace(record.e140, e142=replace(
                params, roiic_base=0.0, roiic_bear=0.0)))
            a, b = neutral._strike_unchecked(), zero._strike_unchecked()
            move = abs(a - b) / abs(a) if a else float("inf")
        except Exception:  # noqa: BLE001 -- refuses below as it would have
            move = float("inf")
        if move < R.INCOMPLETE_LEG_TOLERANCE:
            why = (f"ROIIC NOT DERIVABLE ({'no history file' if history is None else 'the history has no profit and capital pair'}); "
                   f"struck at ZERO, the conservative end: the programme at zero moves "
                   f"the value {move:.1%}, inside E106's 3.5% (E142(6))")
            params = replace(params,
                             roiic_base=0.0 if params.roiic_base is None else params.roiic_base,
                             roiic_bear=0.0 if params.roiic_bear is None else params.roiic_bear,
                             roiic_base_how=params.roiic_base_how or why,
                             roiic_bear_how=params.roiic_bear_how or why)
            record = replace(record, e140=replace(record.e140, e142=params))
    quality: tuple = ()
    checks: tuple[str, ...] = ()
    if history is not None:
        checks = tuple(HI.check(history))
        try:
            legs = record.legs()
            parts = record.e142_parts()
            quality = HI.quality(history, tax=tax or 0.0, fcf0=parts["fcf0"],
                                 net_debt=-legs.net_cash,
                                 roiic_base=params.roiic_base,
                                 repeat_buyer=params.repeat_buyer,
                                 rate=record.rate.rate)
        except Exception:  # noqa: BLE001 -- the record refuses elsewhere
            quality = ()
    return record, quality, checks


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
    if s.record.e140 is not None and s.record.e140.deals:
        try:
            low_end = s.record.at_deal_end("low")
        except Exception:  # noqa: BLE001 -- a memo
            low_end = None
        rows.append(("  fv_base, deals at LOW end (E140(3))", "",
                     _num(low_end), ""))

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


def e140_lines(record: R.RunRecord) -> list[str]:
    """E140 / E140.1's parts, one bullet each, for the strike doc."""
    b = record.e140
    if b is None:
        return []
    try:
        flow = record.normalised_flow()
    except Exception as exc:  # noqa: BLE001 -- the record refuses elsewhere
        return [f"- **E140:** the normalised flow will not form -- {exc}"]
    years = "; ".join(f"{y.label} {v:,.0f}" for y, v in zip(b.years, flow.years))
    out = [f"- **E140 FCF0:** mean of {years} = {flow.mean:,.0f}"
           + (f"; acquisitions mean {flow.acquisitions_mean:,.0f} NOT deducted "
              f"-- valued as the deal programme (E142)" if b.e142 is not None else
              f"; LESS acquisitions mean {flow.acquisitions_mean:,.0f} "
              f"(E140.1(1): a repeat buyer)" if flow.repeat_buyer else
              f"; acquisitions mean {flow.acquisitions_mean:,.0f} NOT deducted "
              f"(paid in fewer than two of three years)")
           + f"; + interest after tax {flow.interest_added_back:,.0f} at "
             f"{b.tax_rate if b.tax_rate is not None else 'DATA MISSING'} "
             f"({b.tax_country}); - minority dividends {flow.nci:,.0f}"
           + (f"; + acquired FCF filed {b.deal_fcf:,.0f}" if b.deal_fcf else "")]
    if b.rolled_from is not None:
        out.append(f"- **bridge rolled (E140.1(3)):** {b.rolled_from} -> "
                   f"{record.dates.balance_sheet}; year-to-date working capital "
                   f"{_num(b.wc_since_year_end, ',.0f')} neutralised (added to "
                   f"net debt)")
    added = b.added_debt("high")
    if added is not None and record.bridge.net_debt is not None:
        out.append(f"- **bridge (E140(3), deals at the HIGH end):** net debt "
                   f"{record.bridge.net_debt:,.0f} on the balance sheet + deals "
                   f"{added - (b.wc_since_year_end or 0.0):,.0f} + working capital "
                   f"neutralised {(b.wc_since_year_end or 0.0):,.0f} = "
                   f"{record.bridge.net_debt + added:,.0f}")
    if b.e142 is not None:
        out += e142_lines(record)
    deals = "; ".join(f"{d.name} {d.low:,.0f}..{d.high:,.0f}" for d in b.deals)
    out.append(f"- **events ledger** `{b.ledger}` dated {b.ledger_dated}, cut at "
               f"{b.cut}: " + (deals if deals else "no deal in the bridge")
               + (f"; already in the balance sheet: "
                  f"{'; '.join(b.deals_in_balance_sheet)}"
                  if b.deals_in_balance_sheet else ""))
    return out


def e142_lines(record: R.RunRecord) -> list[str]:
    """E142-E144's chain, case by case, in the store's money unit."""
    p = record.e140.e142
    money = M.UNIT_SCALE[record.money_unit]
    count = M.UNIT_SCALE[record.shares.unit]
    shares = record.shares.count * count
    out = [f"- **growth (E144):** {p.growth_how}",
           f"- **cycle and level (E143):** {p.level_how}",
           "- **deal programme (E142):** "
           + (f"repeat buyer, A = {p.acquisitions_mean:,.0f}/yr; ROIIC base "
              f"{_num(p.roiic_base, '.2%')} -- {p.roiic_base_how or 'not derivable'}; "
              f"bear {_num(p.roiic_bear, '.2%')} -- {p.roiic_bear_how or 'not derivable'}"
              if p.repeat_buyer else "not a repeat buyer: no programme")]
    for case, g in (("bear", record.growth.bear), ("base", record.growth.base),
                    ("bull", record.growth.bull)):
        if g is None:
            continue
        try:
            parts = record.e142_parts(g, case)
            value = record._strike_unchecked(g, case=case)
        except Exception as exc:  # noqa: BLE001 -- the record refuses elsewhere
            out.append(f"- **{case}:** will not form -- {exc}")
            continue
        out.append(
            f"- **{case}:** flow {parts['flow'] / money:,.0f} x level "
            f"{parts['level']:.3f} x (1 + {g:.2%}) = FCF0 {parts['fcf0'] / money:,.0f}; "
            f"programme {parts['programme'] / money:,.0f} "
            f"({parts['programme'] / shares:+.2f}/sh); deals "
            f"{parts['deal_price'] / money:,.0f} credited back "
            f"{parts['deal_credit'] / money:,.0f} at ROIIC "
            f"{_num(parts['roiic'], '.2%')} ({parts['deal_credit'] / shares:+.2f}/sh)"
            f" -> **{value:,.2f}**")
    return out


def quality_lines(s: Strike) -> list[str]:
    if not s.quality:
        return ["- **would Warren own it (E145):** no history file -- not tested"]
    out = ["- **would Warren own it (E145):**"]
    for t in s.quality:
        mark = "PASS" if t.passed else ("FAIL" if t.passed is False else "n/a")
        out.append(f"  - {t.name}: **{mark}** -- {t.figure}")
    return out


def anchor_lines(s: Strike) -> list[str]:
    """The three anchors (method review section 6): g*, the owner-earnings
    yield at today's price plus base growth, and the tangible ROIC."""
    if not s.e142 or s.price is None:
        return []
    try:
        parts = s.record.e142_parts()
        legs = s.record.legs()
        ev = s.price * legs.shares - legs.net_cash
        y = parts["fcf0"] / ev if ev > 0 else None
    except Exception:  # noqa: BLE001
        return []
    q1 = next((t.figure for t in s.quality if t.name.startswith("Q1")), "no history")
    return [f"- **anchors:** g* {_num(s.g_star, '.2%')}; owner-earnings yield on EV "
            f"{_num(y, '.2%')} + base growth {s.record.growth.base:.2%} = expected "
            f"return ~{_num(None if y is None else y + s.record.growth.base, '.1%')} "
            f"against r {s.record.rate.rate:.1%}; tangible ROIC {q1}"]


def document(s: Strike) -> str:
    """The strike doc, in the shape the dated scripts wrote."""
    prior_fv = s.prior_value()
    lines = [f"# {s.ticker} -- struck {s.as_of.isoformat()}", "",
             f"*Struck by `vss strike` off `config/manual/{s.ticker}.yaml` on "
             + ("the growth DERIVED from the issuer's history (E144) "
                if s.record.growth.view_file.startswith("E144") else
                "the pre-registered growth view ")
             + f"{_growth_text(s.record.growth)}"
             + (f", carried from {s.prior_path.name}" if s.prior_path
                else " (first strike, from the entry)")
             + ". Nothing here writes the watchlist: fv_base, tier, mbp and "
               "stop_price are the owner's.*", "",
             f"- **basis:** {s.record.basis}",
             f"- **fv_base:** {_num(prior_fv)} -> **{_num(s.fv)}** "
             f"(bear {_num(s.bear)}, bull {_num(s.bull)})",
             f"- **FCF0:** {_num(s.record.fcf0(), ',.0f')}",
             f"- **net debt:** {_num(s.record.bridge.net_debt, ',.0f')}"
             + (f" on the balance sheet of {s.record.dates.balance_sheet}"
                if s.record.e140 is not None else ""),
             *e140_lines(s.record),
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
    if s.e142:
        lines += anchor_lines(s) + quality_lines(s)
        if s.history_check:
            lines.append(f"- **history read-back: {len(s.history_check)} FAIL** -- "
                         + "; ".join(s.history_check[:5]))
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
