"""SAP.DE: re-struck 2026-08-30 (evening) under E90 and E91, from the store,
end to end, ZERO hand inputs.

The same-day prior record (`SAP.DE-2026-08-30.json`, the first store-formed
strike) divided by E88's annual FY2025 average 1,175m and struck 139.48.
E91 (ruled the same evening, operands read back by the owner) takes the
four stated per-quarter diluted counts -- 1,172 / 1,172 / 1,168 / 1,158m,
the EPS footnotes -- as the coded day-weighted window average 1,167.5m, the
window's own figure, so the three as-of dates agree. E90 (same evening)
makes the MBP the BASE-case value x the tier cushion (tier 1: 0.85).

The script REFUSES to print a fair value if the record is incomplete or if
ANY input was entered by hand, and confirms the written JSON replays to the
same figure before printing.

WRITES `reference/SAP.DE-STRIKE-2026-08-30-e91.md` and
`reference/run-records/SAP.DE-2026-08-30-e91.json`. Does NOT write
`config/watchlist.yaml` -- that entry is the owner's write, made by hand
from this printout with a dated backup beside it.

    python tools/restrike_sap_2026_08_30_e91.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))   # run as a script
from datetime import date, datetime
from zoneinfo import ZoneInfo

from vss import fx
from vss import manual as M
from vss import metrics as MT
from vss import runrecord as R
from vss import valuation as V
from vss.fetch import get_history
from vss.runner import CACHE_DIR, PROJECT_ROOT

TICKER = "SAP.DE"
RUN_TS = datetime.now(ZoneInfo("Europe/Stockholm"))
AS_OF = RUN_TS.date()
STAMP = "2026-08-30-e91"
PRIOR = "2026-08-30"
TIER = 1                     # carried; RULED A 2026-08-26; NOT re-scored --
                             # E77's one-tier-stricter applies at the next
                             # section 4.4 re-score (catalyst 2026-10-21)
RECORDS = PROJECT_ROOT / "reference" / "run-records"
RATE = R.Rate(core_expected_return=0.070, premium=0.025)
CORE_EXPECTED_RETURN = 0.070                             # E29's anchor
GROWTH = R.Growth(base=0.08, bear=0.06, bull=0.11,
                  view_file="reference/growth-views/SAP.DE.md",
                  view_date=date(2026, 8, 26))
RULINGS = ("E90 (MBP = BASE-case value x tier cushion, 0.85 at tier 1) and "
           "E91 (the divisor is the coded day-weighted average of the four "
           "stated per-quarter diluted counts), on the store as it stands "
           "after E84-E89 and the owner's two read-backs of 2026-08-30")


def settled_close() -> tuple[float, date]:
    fetched = get_history(TICKER, CACHE_DIR, now=RUN_TS, write=False)
    m = MT.compute(fetched.frame, AS_OF, MT.settled_through(RUN_TS))
    return m.last_close, m.last_close_date


def tool_commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, cwd=PROJECT_ROOT,
                             check=True).stdout.strip()
    except Exception:  # pragma: no cover
        sha = "unknown"
    return f"SAP.DE e90/e91 re-strike, 2026-08-30, {sha}"


def strike() -> dict:
    parsed = M.load_manual(TICKER, directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    gate = M.section5_gate(parsed, as_of=AS_OF)
    price_minor, price_date = settled_close()
    divisor = fx.minor_unit_divisor(parsed.quote_currency)
    price = price_minor / divisor
    record = R.from_store(parsed, basis, growth=GROWTH, run_ts=RUN_TS,
                          hand_inputs=(), price_date=price_date, rate=RATE,
                          tool_commit=tool_commit())
    prior = R.RunRecord.from_dict(json.loads(
        (RECORDS / f"{TICKER}-{PRIOR}.json").read_text(encoding="utf-8")))
    s = dict(parsed=parsed, basis=basis, gate=gate, price=price,
             price_minor=price_minor, divisor=divisor, price_date=price_date,
             record=record, prior=prior, currency=record.currency,
             quote_currency=parsed.quote_currency)
    s["hand"] = [i.name for i in record.inputs if i.entered_by == "hand"]
    if not record.complete:
        s["gaps"] = record.missing()
        return s
    legs = record.legs()
    args = dict(fcf0=legs.fcf0, net_cash=legs.net_cash, shares=legs.shares)
    s.update(
        fcf0=record.fcf0(), legs=legs, band=record.band(),
        bear=record.strike(GROWTH.bear), bull=record.strike(GROWTH.bull),
        implied=V.implied_growth(price=price, rate=RATE.rate, **args),
        mbp=V.maximum_buy_price(g_base=GROWTH.base, tier=TIER,
                                rate=RATE.rate, **args),
        prior_band=prior.band(), prior_shares=prior.legs().shares,
    )
    return s


def render(s: dict) -> str:
    cur, qcur = s["currency"], s["quote_currency"]
    rec = s["record"]
    stamp = RUN_TS.strftime('%Y-%m-%d %H:%M %Z')
    unit = 1e6
    out = [f"# {TICKER} -- re-struck under E90 / E91, {stamp}", "",
           f"**{stamp}. `config/watchlist.yaml` IS NOT WRITTEN by this tool** -- the "
           f"owner writes it from this printout with a dated backup beside it. The "
           f"record is written to `reference/run-records/{TICKER}-{STAMP}.json`.",
           "",
           f"Rulings applied: {RULINGS}. The same-day prior record "
           f"(`{TICKER}-{PRIOR}.json`) divided by E88's annual 1,175m and struck "
           f"139.48; it stays on disk as history and still replays.",
           "",
           f"Growth view: `{GROWTH.view_file}`, registered {GROWTH.view_date.isoformat()} "
           f"-- base {GROWTH.base:.0%}, bear {GROWTH.bear:.0%}, bull {GROWTH.bull:.0%} -- "
           f"UNCHANGED (E28's pre-registration order stands under E90).",
           "",
           f"Tool: `tools/restrike_sap_2026_08_30_e91.py` at `{tool_commit()}`. r 9.5% "
           f"(7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; "
           f"end-of-year discounting.",
           "",
           f"**BASIS: `{s['basis'].label}`, the twelve months ending "
           f"{s['basis'].end.isoformat()}** (E19 / E41). Store: "
           f"`config/manual/{TICKER}.yaml`. Price: last SETTLED close "
           f"**{s['price']:.2f} {qcur}** on {s['price_date'].isoformat()} "
           f"(tool fetch, {stamp}).",
           ""]
    gate = s["gate"]
    if gate.refused:
        out += ["**The store's gate refuses:** " + "; ".join(
            f"`{r.kind}` {r.subject}" for r in gate.refusals) + ".", ""]
    else:
        out += ["**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure "
                "the basis reads is VERIFIED (E40) -- the four E91 divisor operands "
                "confirmed one at a time at the owner's read-back of this evening.", ""]
    if s["hand"]:
        out += [f"**HAND INPUTS PRESENT ({', '.join(s['hand'])}) -- this strike is "
                f"REFUSED by its own terms.** Nothing is printed.", ""]
        return "\n".join(out)
    if "gaps" in s:
        out += ["**RECORD INCOMPLETE -- no fair value is printed.** Absent: "
                + "; ".join(s["gaps"]), ""]
        return "\n".join(out)
    band, pband = s["band"], s["prior_band"]
    out += [
        f"- record complete: **True**, with **ZERO hand inputs** -- every leg off the "
        f"store; the eight declarations and declaration 3.1 (E70) in the record below",
        f"- **FCF0: {s['fcf0'] / unit:,.0f} {cur} m** and **net CASH "
        f"{s['legs'].net_cash / unit:,.0f} {cur} m** -- both UNCHANGED from the prior "
        f"record (E86 capex columns; E84/E89 ex-lease legs; E85 NOT PRESENTED legs; "
        f"interest outside OCF, no add-back; SBC 1,331 deducted).",
        f"- **divisor (E91): {s['legs'].shares:,.0f}** -- the coded day-weighted "
        f"average of the four stated per-quarter diluted counts "
        f"(1,172m x 92d; 1,172m x 92d; 1,168m x 90d; 1,158m x 91d, over 365d), "
        f"the window's OWN average: the three as-of dates AGREE. Prior record: "
        f"{s['prior_shares']:,.0f} (E88's annual FY2025 fall-back) -- the divisor "
        f"is the WHOLE of the move below.",
        "",
        f"- **fv_base (Method C, E28 engine): {band.mid:,.2f} {cur}** (prior "
        f"{pband.mid:,.2f}: {band.mid / pband.mid - 1:+.2%})",
        f"- band across E29's +/-0.5% (r {band.rate - band.delta:.1%} / {band.rate:.1%} "
        f"/ {band.rate + band.delta:.1%}): **{band.low:,.2f} / {band.mid:,.2f} / "
        f"{band.high:,.2f} {cur}** (prior {pband.low:,.2f} / {pband.mid:,.2f} / {pband.high:,.2f})",
        f"- bear (g {GROWTH.bear:.1%}): **{s['bear']:,.2f} {cur}** and bull "
        f"(g {GROWTH.bull:.1%}): **{s['bull']:,.2f} {cur}** -- INFORMATION under E90, "
        f"not the buy line",
        f"- implied growth g* at the settled close {s['price']:.2f} {cur}: "
        f"**{s['implied']:.2%}** (E28; the view was fixed {GROWTH.view_date.isoformat()})",
        f"- *{V.rate_declaration(cur)}* (E37)",
        "",
        f"- **tier {TIER} (carried; NOT re-scored -- E77 applies at the next 4.4 "
        f"re-score, catalyst 2026-10-21). MBP (E90): {s['mbp'].mid:,.2f} {cur}** = "
        f"base {band.mid:,.2f} x {V.TIER_CUSHION_E90[TIER]:.2f} (band r "
        f"{band.rate - band.delta:.1%} {s['mbp'].low:,.2f} / r "
        f"{band.rate + band.delta:.1%} {s['mbp'].high:,.2f}); the cushion covers "
        f"model and input error, not scenario risk. Price {s['price']:.2f} is "
        f"{s['price'] / s['mbp'].mid - 1:+.1%} against it. stop_price null (sold "
        f"2026-08-26, E42) -- UNTOUCHED; NO STOP DEFINED flags until one is set.",
        "",
        "## The run record, in full",
        "",
        rec.render(),
        "",
        "---",
        "",
        "## What this run does NOT do",
        "",
        "- **It writes nothing to `config/watchlist.yaml`.** The owner writes fv_base "
        "and tier from this printout; `mbp` is derived by the tool (E90), never by hand.",
        "- **It does not touch the growth view, the tier, or stop_price.**",
        "- **It does not authorise a purchase or a sale.** S0 rule 4 stands.",
        "",
    ]
    return "\n".join(out)


def main() -> int:
    RECORDS.mkdir(parents=True, exist_ok=True)
    s = strike()
    text = render(s)
    if s["hand"] or "gaps" in s:
        print(text)
        return 1
    path = RECORDS / f"{TICKER}-{STAMP}.json"
    path.write_text(json.dumps(s["record"].to_dict(), indent=1) + "\n",
                    encoding="utf-8")
    replayed = R.RunRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
    assert replayed.band().mid == s["band"].mid, \
        f"REPLAY MISMATCH: {replayed.band().mid} != {s['band'].mid}"
    text += (f"\n*Replay check: `{path.name}` reloaded and replayed to "
             f"{replayed.band().mid:,.2f} {s['currency']} -- the same figure.*\n")
    (PROJECT_ROOT / "reference" / f"{TICKER}-STRIKE-{STAMP}.md").write_text(
        text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
