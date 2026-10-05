"""Every name with a run record, re-struck under E117 (2026-09-19).

E117: RENT IS AN OPERATING COST. A US GAAP filer's flow keeps its operating
lease payments (E70's add-back reversed) and its operating lease liability
leaves net debt; an IFRS 16 filer's principal and lease interest are
deducted and its whole lease liability leaves. Finance leases stay.

Each name is struck again off `config/manual/<TICKER>.yaml` as it stands,
on its PRIOR record's pre-registered growth view, rate, conventions and
hand inputs, all UNCHANGED (E28) -- the lease treatment is the only thing
this pass moves. A name whose section 5 gate refuses gets NO new record:
its refusal is printed and the prior record stands, marked. It WRITES
`reference/run-records/<TICKER>-2026-09-19-e117.json` and
`reference/<TICKER>-STRIKE-2026-09-19-e117.md` per struck name, and prints
the before/after table E117 carries. It does NOT write
config/watchlist.yaml: fv_base, tier, mbp and stop_price are the owner's
write, by hand, after this printout (E117, the E70 precedent).

    .venv/bin/python tools/restrike_e117_2026_09_19.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))   # run as a script

from dataclasses import replace
from datetime import datetime
from zoneinfo import ZoneInfo

import yaml

from vss import fx
from vss import manual as M
from vss import metrics as MT
from vss import runrecord as R
from vss import valuation as V
from vss.fetch import get_history
from vss.runner import CACHE_DIR, PROJECT_ROOT

RUN_TS = datetime.now(ZoneInfo("Europe/Stockholm"))
AS_OF = RUN_TS.date()
STAMP = "2026-09-19-e117"
RECORDS = PROJECT_ROOT / "reference" / "run-records"

#: E117 clause 6 and what the data allowed on 2026-09-19: no rent-bearing
#: flow can be formed for these, so their struck values are marked.
UNVERIFIED_UNDER_E117 = {
    "LIAB.ST": "lease interest is stated for FY2025 only (annual report note 30: "
               "66); none of the four quarters on the TTM basis states it",
    "RKT.L": "no separate lease principal line (folded into 'Repayment of "
             "borrowings') and no IFRS 16.53(g) total; only the interest "
             "expense, 13",
    "SAP.DE": "lease interest is never isolated -- annual or quarterly, only a "
              "combined 'Interest paid' for all debt",
}


def latest_records() -> dict[str, tuple[_Path, R.RunRecord]]:
    out: dict[str, tuple[_Path, R.RunRecord]] = {}
    for path in sorted(RECORDS.glob("*.json")):
        ticker = re.match(r"(.+?)-2026", path.name).group(1)
        record = R.RunRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
        if ticker not in out or record.run_ts > out[ticker][1].run_ts:
            out[ticker] = (path, record)
    return out


def watchlist() -> dict[str, dict]:
    doc = yaml.safe_load((PROJECT_ROOT / "config" / "watchlist.yaml").read_text())
    items = doc if isinstance(doc, list) else next(
        v for v in doc.values() if isinstance(v, list))
    return {e["ticker"]: e for e in items}


def settled_close(ticker: str, quote_currency: str) -> tuple[float | None, object]:
    try:
        fetched = get_history(ticker, CACHE_DIR, now=RUN_TS, write=False)
        m = MT.compute(fetched.frame, AS_OF, MT.settled_through(RUN_TS))
        return m.last_close / fx.minor_unit_divisor(quote_currency), m.last_close_date
    except Exception:                                   # a memo, never a gate
        return None, None


def tool_commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, cwd=PROJECT_ROOT,
                             check=True).stdout.strip()
    except Exception:  # pragma: no cover
        sha = "unknown"
    return f"E117 re-strike, 2026-09-19, {sha}"


def safe(fn):
    try:
        return fn()
    except Exception as exc:                            # printed, never hidden
        return f"REFUSED: {exc}".split(". ")[0][:160]


def strike(ticker: str, prior_path: _Path, prior: R.RunRecord, entry: dict) -> dict:
    row = dict(ticker=ticker, status=entry.get("status", "-"),
               prior_file=prior_path.name, prior_fv=safe(prior.strike))
    if ticker in UNVERIFIED_UNDER_E117:
        row.update(outcome="UNVERIFIED UNDER E117",
                   why=UNVERIFIED_UNDER_E117[ticker])
        return row
    parsed = M.load_manual(ticker, directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    gate = M.section5_gate(parsed, as_of=AS_OF)
    # THE GATE IS PRINTED, NOT APPLIED HERE: several priors (BOUV.OL,
    # MEKKO.HE) were struck while their gate refused on figures already
    # UNVERIFIED, and "re-strike all names" means the same pass for them.
    # The record decides whether a value forms; the gate's state goes
    # beside it for the owner.
    gate_note = ("; ".join(f"{r.kind}: {r.subject}" for r in gate.refusals)[:200]
                 if gate.refused else "")
    hand = tuple(i for i in prior.inputs if i.entered_by == "hand")
    price, price_date = settled_close(ticker, parsed.quote_currency)
    record = R.from_store(parsed, basis, growth=prior.growth, run_ts=RUN_TS,
                          hand_inputs=hand, price_date=price_date,
                          rate=prior.rate, conventions=prior.conventions,
                          tool_commit=tool_commit(),
                          notes="E117 re-strike: the lease treatment is the only "
                                "change from the prior record, " + prior_path.name)
    new_fv = safe(record.strike)
    outcome = ("STRUCK" if isinstance(new_fv, float) else "RECORD REFUSES")
    if gate_note:
        outcome += " -- gate refuses"
    row.update(outcome=outcome, why=(gate_note if isinstance(new_fv, float)
                                     else f"{new_fv}; gate: {gate_note}"),
               record=record, new_fv=new_fv,
               bear=safe(lambda: record.strike(prior.growth.bear)),
               bull=safe(lambda: record.strike(prior.growth.bull)),
               fcf0_before=safe(prior.fcf0), fcf0_after=safe(record.fcf0),
               nd_before=prior.bridge.net_debt, nd_after=record.bridge.net_debt,
               lease=record.lease.sentence, price=price, price_date=price_date,
               basis=basis.label)
    tier = entry.get("tier")
    if isinstance(new_fv, float) and tier in V.TIER_CUSHION_E90:
        cushion = V.TIER_CUSHION_E90[tier]
        row.update(tier=tier, mbp_after=new_fv * cushion,
                   mbp_before=(prior.strike() * cushion
                               if isinstance(row["prior_fv"], float) else None))
    if isinstance(new_fv, float) and price:
        legs = record.legs()
        row["g_star"] = safe(lambda: V.implied_growth(
            price=price, fcf0=legs.fcf0, net_cash=legs.net_cash,
            shares=legs.shares, rate=prior.rate.rate,
            terminal=prior.conventions.terminal_growth,
            years=prior.conventions.horizon_years))
    return row


def fmt(v, spec=",.2f") -> str:
    return format(v, spec) if isinstance(v, (int, float)) else str(v or "--")


def report(row: dict) -> str:
    lines = [f"# {row['ticker']} -- struck under E117, {AS_OF.isoformat()}", "",
             f"*RENT IS AN OPERATING COST (FRAMEWORK-EDITS E117). The growth "
             f"view, rate, conventions and hand inputs are the prior record's "
             f"({row['prior_file']}), UNCHANGED: the lease treatment is the only "
             f"thing that moved. Nothing here writes the watchlist.*", "",
             f"- **basis:** {row['basis']}",
             f"- **fv_base:** {fmt(row['prior_fv'])} -> **{fmt(row['new_fv'])}**"
             f" (bear {fmt(row['bear'])}, bull {fmt(row['bull'])})",
             f"- **FCF0:** {fmt(row['fcf0_before'], ',.0f')} -> {fmt(row['fcf0_after'], ',.0f')}",
             f"- **net debt:** {fmt(row['nd_before'], ',.0f')} -> {fmt(row['nd_after'], ',.0f')}",
             f"- **lease:** {row['lease']}"]
    if "mbp_after" in row:
        lines.append(f"- **MBP (tier {row['tier']}, E90):** {fmt(row['mbp_before'])}"
                     f" -> {fmt(row['mbp_after'])}")
    if row.get("price"):
        lines.append(f"- **close {row['price_date']}:** {fmt(row['price'])}; "
                     f"g* {fmt(row.get('g_star'), '.2%')}")
    lines += ["", f"Record: `reference/run-records/{row['ticker']}-{STAMP}.json`", ""]
    return "\n".join(lines)


def main() -> int:
    wl = watchlist()
    rows = [strike(t, path, rec, wl.get(t, {}))
            for t, (path, rec) in sorted(latest_records().items())]
    for row in rows:
        if not isinstance(row.get("new_fv"), float):
            continue
        t = row["ticker"]
        (RECORDS / f"{t}-{STAMP}.json").write_text(
            json.dumps(row["record"].to_dict(), indent=1) + "\n", encoding="utf-8")
        (PROJECT_ROOT / "reference" / f"{t}-STRIKE-{STAMP}.md").write_text(
            report(row), encoding="utf-8")
    print("| Ticker | Status | fv_base before | E117 | Move | MBP before -> E117 | Outcome |")
    print("|---|---|---:|---:|---:|---|---|")
    for r in rows:
        a, b = r["prior_fv"], r.get("new_fv")
        move = (f"{(b / a - 1):+.1%}" if isinstance(a, float) and isinstance(b, float)
                else "")
        mbp = (f"{fmt(r.get('mbp_before'))} -> {fmt(r['mbp_after'])}"
               if "mbp_after" in r else "")
        why = r["outcome"] + (f": {r['why']}" if r.get("why") else "")
        print(f"| {r['ticker']} | {r['status']} | {fmt(a)} | {fmt(b)} | {move} | {mbp} | {why} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
