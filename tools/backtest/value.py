"""One name on one test date through the engine's mechanical core.

Every figure is the engine's: the store and history come from the cut facts
(`pit`), the growth is E144's derived one, E142's parameters and E145's
tests come from `strike.apply_e142`, the value from `RunRecord.strike`, the
kills from `rules.evaluate_hard_kills` on the tagged quarters. Nothing is
written anywhere.

WHAT A LIVE STRIKE HAS AND THIS DOES NOT (design §2, "Mänskliga
bedömningar"; each is a column or a refusal, never a silent default):

- no events ledger: deals closed after the basis are not in the bridge;
- no registered view: a name with fewer than five organic years has no
  growth and no value (E144(4) would fall back to a view);
- no hand legs: a leg the tags do not give stays missing and the record
  refuses where it would refuse live;
- §4.2.3 (guidance) and §4.2.6 (executives) are not evaluated;
- the interest shape is chosen by `pit.interest_shape` from the tags.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

from vss import events as EV
from vss import history as HI
from vss import manual as M
from vss import rules as RU
from vss import runrecord as R
from vss import strike as S
from vss import xbrl as X

from . import pit as P

#: §4.2 rules the backtest can measure from tagged quarters (design §2).
MEASURED_KILLS = ("4.2.1", "4.2.2", "4.2.5", "4.2.7")


def empty_ledger(ticker: str, as_of: date) -> EV.Ledger:
    """No deals after the basis: the backtest has no ledger to read."""
    return EV.Ledger(ticker=ticker, path="<backtest: no events ledger>",
                     dated=as_of, money_unit="whole", deals=(), none_found=True,
                     searched=())


def with_ratios(quarters: list) -> list:
    """`revenue_yoy` and `op_margin` filled in by plain division.

    THE ENGINE NEVER COMPUTES THESE (`xbrl.as_quarter`: "the one thing this
    project never does"); live, a session reads them off the release. The
    backtest has no release, so §4.2.1, 4.2.2 and 4.2.7 would all be
    CANNOT EVALUATE without this. The year-ago quarter is matched by label,
    as `rules._year_ago` matches it. A quarter whose revenue EQUALS its
    year-ago revenue to the unit is left without a ratio: that is the
    signature of a filer that re-dated last year's quarters (CENTA's FY2018
    10-K), not of flat demand.
    """
    by_label = {q.period: q for q in quarters}
    out = []
    for q in quarters:
        yoy = margin = None
        parts = RU.period_parts(q.period)
        prior = by_label.get(f"{parts[0] - 1}-{parts[1]}") if parts else None
        if (prior is not None and q.revenue and prior.revenue and prior.revenue > 0
                and q.revenue != prior.revenue):
            yoy = q.revenue / prior.revenue - 1
        if q.revenue and q.revenue > 0 and q.op_income is not None:
            margin = q.op_income / q.revenue
        out.append(replace(q, revenue_yoy=yoy, op_margin=margin))
    return out


def kills(facts_cut: dict, parsed, as_of: date) -> list[dict]:
    """§4.2 on the last twelve tagged quarters, as the engine evaluates them
    once the two ratios are in (`with_ratios`)."""
    try:
        quarters = with_ratios([X.as_quarter(q)
                                for q in X.build_quarters(facts_cut, limit=12)])
    except Exception as exc:  # noqa: BLE001 -- no quarters is CANNOT EVALUATE
        quarters, why = [], f"{type(exc).__name__}: {exc}"
    else:
        why = ""
    leverage = None
    if parsed is not None:
        try:
            reading = M.gate3_leverage(parsed, M.section5_basis(parsed))
            leverage = (reading.state(M.KILL_LEVERAGE_MAX),
                        reading.line(M.KILL_LEVERAGE_MAX))
        except Exception:  # noqa: BLE001
            leverage = None
    out = []
    for k in RU.evaluate_hard_kills(quarters, None, as_of, derived_leverage=leverage):
        out.append({"rule": k.rule, "state": k.state,
                    "detail": (why + " " if why and not quarters else "") + k.detail})
    return out


def evaluate(facts: dict, as_of: date, *, ticker: str, cik: int,
             policy: str = "first") -> dict:
    """The row for one name on one date. `status` is "ok" or why not."""
    row: dict = {"ticker": ticker, "cik": cik, "as_of": as_of.isoformat(),
                 "policy": policy, "status": "", "fv_base": None, "fv_bear": None,
                 "g_base": None, "g_bear": None, "quality": {}, "kills": [],
                 "interest_source": "", "lease_transition": False,
                 "basis_end": None, "roll_end": None, "shares": None,
                 "fcf0": None, "net_cash": None, "notes": []}
    try:
        store = P.store_at(facts, as_of, ticker=ticker, cik=cik, policy=policy)
    except Exception as exc:  # noqa: BLE001
        row["status"] = f"no store: {type(exc).__name__}: {exc}"[:300]
        return row
    row["interest_source"] = store.interest_source
    row["lease_transition"] = store.lease_transition
    row["searched_zeros"] = list(store.searched_zeros)
    if store.parsed is None:
        row["status"] = f"store refused: {store.refused}"[:300]
        return row
    parsed = store.parsed
    basis = M.section5_basis(parsed)
    row["basis_end"] = basis.end.isoformat() if basis is not None else None
    rf = getattr(parsed, "roll_forward", None)
    row["roll_end"] = rf.period_end.isoformat() if rf is not None else None
    cut = P.clip(facts, as_of, policy=policy)
    row["kills"] = kills(cut, parsed, as_of)
    if basis is None:
        row["status"] = "no twelve-month basis (E19)"
        return row
    if store.gate is not None and store.gate.refused:
        row["status"] = "gate refused: " + "; ".join(
            f"{r.kind}: {r.detail}" for r in store.gate.refusals)[:300]
        return row
    try:
        history = P.history_at(facts, as_of, ticker=ticker, policy=policy)
    except Exception as exc:  # noqa: BLE001
        row["status"] = f"no history: {type(exc).__name__}: {exc}"[:300]
        return row
    derived = HI.derived_growth(history)
    if derived is None:
        row["status"] = "no growth: fewer than five organic years (E144(4) needs a view)"
        return row
    growth = R.Growth(base=derived.base, bear=derived.bear, bull=derived.bull,
                      view_file="E144: derived (backtest)", view_date=as_of)
    row["g_base"], row["g_bear"] = derived.base, derived.bear
    try:
        record = R.from_store(parsed, basis, growth=growth, run_ts=P.run_ts(as_of),
                              price_date=as_of, tool_commit="backtest",
                              notes="backtest", ledger=empty_ledger(ticker, as_of))
        record, quality, _ = S.apply_e142(record, history, derived.how)
    except Exception as exc:  # noqa: BLE001
        row["status"] = f"record will not form: {type(exc).__name__}: {exc}"[:300]
        return row
    row["quality"] = {t.name.split()[0]: t.passed for t in quality}
    try:
        row["fv_base"] = record.strike()
        row["fv_bear"] = record.strike(growth.bear, case="bear")
        legs = record.legs()
        row["shares"], row["net_cash"] = legs.shares, legs.net_cash
        row["fcf0"] = record.e142_parts()["fcf0"]
    except Exception as exc:  # noqa: BLE001
        row["status"] = f"no value: {type(exc).__name__}: {exc}"[:300]
        return row
    row["status"] = "ok"
    return row


def passes_quality(row: dict) -> bool | None:
    """E145 Q1-Q4 all passed (None where any is undeterminable)."""
    q = [row["quality"].get(k) for k in ("Q1", "Q2", "Q3", "Q4")]
    if any(v is False for v in q):
        return False
    return None if any(v is None for v in q) else True


def measured_kill(row: dict) -> bool:
    """Any of the four measurable §4.2 kills tripped."""
    return any(k["state"] == RU.TRIP and k["rule"].startswith(MEASURED_KILLS)
               for k in row["kills"])
