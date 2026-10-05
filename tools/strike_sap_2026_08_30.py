"""SAP.DE: struck 2026-08-30 from the store, end to end, ZERO hand inputs.

The 2026-08-26 record (RESTRIKE-2026-08-26-b) replayed to 139.48 but the
store could not rebuild it -- capex and the borrowing split were hand
inputs -- and E87 nulled the watchlist figures. This strike runs after
E84-E89 and the owner's read-back of 2026-08-30: capex is the code's
difference of E86's stated cumulative columns, the borrowing legs are note
(E.2)'s ex-lease operands (E84; E89 for FY2025), the ARO and prepaid legs
are E85's recorded NOT PRESENTED searches, the divisor is FY2025's
1,175,000,000 diluted average under E88 with the basis mismatch flagged,
and quarterly owners-only profit is on the file for FCF conversion.

The script REFUSES to print a fair value if the record is incomplete or if
ANY input was entered by hand. It confirms the written JSON replays to the
same figure before printing.

WRITES `reference/SAP.DE-STRIKE-2026-08-30.md` and
`reference/run-records/SAP.DE-2026-08-30.json`. Does NOT write
`config/watchlist.yaml` -- that entry is the owner's write, made by hand
from this printout with a dated backup beside it.

    python tools/strike_sap_2026_08_30.py
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
STAMP = "2026-08-30"
PRIOR = "2026-08-26"
TIER = 1                     # carried; RULED A 2026-08-26 (Build 2 item 5); NOT
                             # re-scored here -- E77's one-tier-stricter applies
                             # at the next section 4.4 re-score (the CTSH shape)
RECORDS = PROJECT_ROOT / "reference" / "run-records"
RATE = R.Rate(core_expected_return=0.070, premium=0.025)
CORE_EXPECTED_RETURN = 0.070                             # E29's anchor
GROWTH = R.Growth(base=0.08, bear=0.06, bull=0.11,
                  view_file="reference/growth-views/SAP.DE.md",
                  view_date=date(2026, 8, 26))
RULINGS = ("E84/E89 (ex-lease borrowing operands), E85 (NOT PRESENTED legs), "
           "E86 (capex from stated cumulative columns), E88 (the divisor is "
           "E41's annual diluted average; the E80 pair stays memo)")


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
    return f"SAP.DE strike, {STAMP}, {sha}"


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
        mbp=V.maximum_buy_price(g_bear=GROWTH.bear, tier=TIER, rate=RATE.rate, **args),
        prior_fcf0=prior.fcf0(), prior_band=prior.band(),
        prior_bear=prior.strike(GROWTH.bear), prior_bull=prior.strike(GROWTH.bull),
        prior_net_cash=prior.legs().net_cash,
    )
    return s


def framework_output(s: dict) -> str:
    """S6.4 and C4, printed as the framework's own output on the price --
    NOT a recommendation (E28 note; S0 rule 4 stands untouched)."""
    price, cur = s["price"], s["currency"]
    fv, bull = s["band"].mid, s["bull"]
    vs_fv = price / fv - 1
    vs_bull = price / bull - 1
    bull_gap = bull / price - 1
    trim = price >= fv
    c4_fires = price > bull
    return "\n".join([
        f"### {TICKER} -- the framework's own output on the price (NOT a recommendation)",
        "",
        f"- price {price:.2f} {cur} vs fv_base {fv:,.2f} {cur}: **{vs_fv:+.1%}**"
        + (" -- price is ABOVE fv_base" if vs_fv > 0 else " -- price is BELOW fv_base"),
        f"- price {price:.2f} {cur} vs FV_bull {bull:,.2f} {cur}: **{vs_bull:+.1%}**"
        + (" -- price is ABOVE the bull case" if vs_bull > 0 else " -- price is BELOW the bull case"),
        f"- **section 6.4, 'At FV_base, trim 25-50%; reassess': {'FIRES' if trim else 'does not fire'}** "
        f"(price {'>=' if trim else '<'} fv_base). A trim presupposes a position; none is "
        f"held -- the position was SOLD 2026-08-26 under C4 (E42, fourth application).",
        f"- **C4, 'exit when even the bull case does not beat the index': "
        f"{'FIRES' if c4_fires else 'does not fire'}.** "
        f"Expected return from {price:.2f} to FV_bull {bull:,.2f} is **{bull_gap:+.1%}**; "
        f"the index core's expected return is {CORE_EXPECTED_RETURN:.1%} a year (E29's "
        f"anchor). A sale presupposes a position; none is held. The WATCH-PRICED entry's "
        f"re-entry line is the MBP below.",
        "",
        "*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on "
        "the fragility, and nothing here does.*",
    ])


def render(s: dict) -> str:
    cur, qcur = s["currency"], s["quote_currency"]
    rec, prior = s["record"], s["prior"]
    stamp = RUN_TS.strftime('%Y-%m-%d %H:%M %Z')
    unit = 1e6          # the store is in whole EUR; printed here in millions
    out = [f"# {TICKER} -- struck from the store, end to end, {stamp}", "",
           f"**{stamp}. `config/watchlist.yaml` IS NOT WRITTEN by this tool** -- the "
           f"owner writes it from this printout with a dated backup beside it. The record "
           f"is written to `reference/run-records/{TICKER}-{STAMP}.json`.",
           "",
           f"The prior record (`reference/run-records/{TICKER}-{PRIOR}.json`, "
           f"RESTRIKE-2026-08-26-b) replayed to 139.48 but the store could not rebuild "
           f"it -- capex -735 and the consolidated borrowing line 10,507 were HAND "
           f"inputs -- and **E87 nulled `fv_base`, `tier` and the derived MBP** on "
           f"2026-08-30. This strike runs under {RULINGS}, after the owner's read-back "
           f"of all fifteen 2026-08-30 entries the same evening.",
           "",
           f"Growth view: `{GROWTH.view_file}`, registered by the owner "
           f"{GROWTH.view_date.isoformat()} (RULED A, Build 2 item 6) -- base "
           f"{GROWTH.base:.0%}, bear {GROWTH.bear:.0%}, bull {GROWTH.bull:.0%} -- "
           f"UNCHANGED (E28).",
           "",
           f"Tool: `tools/strike_sap_2026_08_30.py` at `{tool_commit()}`. r 9.5% (7.0% "
           f"core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year "
           f"discounting.",
           "",
           f"**BASIS: `{s['basis'].label}` -- the four consecutive quarters, the twelve "
           f"months ending {s['basis'].end.isoformat()}** (E19, named quarter by quarter "
           f"under E41). Store: `config/manual/{TICKER}.yaml`, money in "
           f"{s['parsed'].money_unit} {cur}. Price: last SETTLED close "
           f"**{s['price']:.2f} {qcur}** on {s['price_date'].isoformat()} (tool fetch, "
           f"{stamp}).",
           ""]
    gate = s["gate"]
    if gate.refused:
        out += ["**The store's gate refuses:** " + "; ".join(
            f"`{r.kind}` {r.subject}" for r in gate.refusals) + ".", ""]
    else:
        out += ["**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure "
                "the basis reads is VERIFIED (E40), confirmed one at a time at the "
                "owner's read-back of 2026-08-30.", ""]
    if s["hand"]:
        out += [f"**HAND INPUTS PRESENT ({', '.join(s['hand'])}) -- this strike is "
                f"REFUSED by its own terms.** E87's condition was a record with zero "
                f"hand inputs; nothing is printed.", ""]
        return "\n".join(out)
    if "gaps" in s:
        out += ["**RECORD INCOMPLETE -- no fair value is printed.** Absent: "
                + "; ".join(s["gaps"]), ""]
        return "\n".join(out)
    band, pband = s["band"], s["prior_band"]
    net_cash = s["legs"].net_cash
    out += [
        f"- record complete: **True**, with **ZERO hand inputs** -- every leg formed "
        f"off the store; the eight declarations and declaration 3.1 (E70) are in the "
        f"record below",
        f"- **FCF0: {s['fcf0'] / unit:,.0f} {cur} m** -- interest NOT in operating cash "
        f"flow (E34: the filer classifies interest paid/received OUTSIDE operating "
        f"activities from January 2025, `interest_in_ocf: no` -- no add-back), capex "
        f"the CODE'S difference of E86's stated cumulative columns "
        f"(-201, -180, -238, -116 = -735), equity-settled SBC 1,331 deducted (E36, "
        f"E41 annual fill). Prior record: {s['prior_fcf0'] / unit:,.0f} {cur} m"
        + (" -- the same figure, now formed without a hand input."
           if abs(s['prior_fcf0'] - s['fcf0']) < 0.5 * unit else " -- MOVED."),
        f"- **lease treatment (E70, declaration 3.1): the flow did NOT bear the lease "
        f"principal** -- IFRS 16.50(b), `operating_leases_in_ocf: no`; the 1,735 {cur} m "
        f"lease total (note (E.2), p.39) sits in net debt and nothing is added back.",
        f"- **net CASH: {net_cash / unit:,.0f} {cur} m** -- "
        f"{rec.bridge.note.split('. Capex legs')[0]}. Prior record: "
        f"{s['prior_net_cash'] / unit:,.0f} {cur} m"
        + (" -- the same bridge, now off the store: E84's ex-lease operands (1,478 + "
           "207 / 6,726 + 361), the lease total 1,735, pension 249, E85's NOT PRESENTED "
           "ARO and prepaid legs at nil on recorded searches, cash 10,511 and other "
           "current financial assets 1,114."
           if abs(s['prior_net_cash'] - net_cash) < 0.5 * unit else " -- MOVED."),
        f"- **divisor (E88): {s['legs'].shares:,.0f}** -- FY2025's weighted-average "
        f"diluted count under E41's annual-only rule, dated 2025-12-31, the basis "
        f"mismatch (annual average against R12M flows) FLAGGED in declaration 1; the "
        f"E80 pair at 6/30/2026 (1,228.5m - 74.3m = 1,154.2m) stays MEMO, never the "
        f"divisor.",
        "",
        f"- **fv_base (Method C, E28): {band.mid:,.2f} {cur}** (prior {pband.mid:,.2f}: "
        f"{band.mid / pband.mid - 1:+.2%})",
        f"- band across E29's +/-0.5% (r {band.rate - band.delta:.1%} / {band.rate:.1%} "
        f"/ {band.rate + band.delta:.1%}): **{band.low:,.2f} / {band.mid:,.2f} / "
        f"{band.high:,.2f} {cur}** (prior {pband.low:,.2f} / {pband.mid:,.2f} / {pband.high:,.2f})",
        f"- bear (g {GROWTH.bear:.1%}): **{s['bear']:,.2f} {cur}** (prior {s['prior_bear']:,.2f})",
        f"- bull (g {GROWTH.bull:.1%}): **{s['bull']:,.2f} {cur}** (prior {s['prior_bull']:,.2f})",
        f"- implied growth g* at the settled close {s['price']:.2f} {cur}: "
        f"**{s['implied']:.2%}** (E28; the view was fixed {GROWTH.view_date.isoformat()}, "
        f"before any fair value and before g* -- UNCHANGED here)",
        f"- *{V.rate_declaration(cur)}* (E37)",
        "",
        f"- **tier {TIER} (carried; section 4.4 NOT re-scored -- E77's one-tier-stricter "
        f"applies at the next re-score, catalyst 2026-10-21). MBP (E28): "
        f"{s['mbp'].mid:,.2f} {cur}** = bear {s['bear']:,.2f} x {V.TIER_MULTIPLIER[TIER]:.2f} "
        f"(band r {band.rate - band.delta:.1%} {s['mbp'].low:,.2f} / r "
        f"{band.rate + band.delta:.1%} {s['mbp'].high:,.2f}). Price {s['price']:.2f} is "
        f"{s['price'] / s['mbp'].mid - 1:+.1%} against it. stop_price null (sold "
        f"2026-08-26, E42) -- UNTOUCHED.",
        "",
        "## The run record, in full -- every declaration and every bridge leg named",
        "",
        rec.render(),
        "",
        framework_output(s),
        "",
        "---",
        "",
        "## What this run does NOT do",
        "",
        "- **It writes nothing to `config/watchlist.yaml`.** The owner writes fv_base "
        "and tier from this printout; `mbp` is derived by the tool (E28), never written "
        "by hand.",
        "- **It does not touch the growth view** -- base 8%, bear 6%, bull 11% are the "
        "registered ones (2026-08-26).",
        "- **It does not re-score tier.** Tier 1 is carried as the owner ruled it "
        "2026-08-26 (RULED A, Build 2 item 5); no E76 reading is on file, and E77 "
        "applies one tier stricter at the next section 4.4 re-score.",
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
