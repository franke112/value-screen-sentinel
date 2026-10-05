"""LIAB.ST: re-struck 2026-08-30 under the rulings made since 2026-08-26.

E34 (interest classification), E35/E35.1 (net debt legs, pension in),
E65-E68 (finance leases beside operating, several borrowing captions,
the asset-retirement leg) and E70 (the lease treatment declared -- for an
IFRS 16 filer the flow never bore the principal, so nothing is added back,
but declaration 3.1 must be on the record). The growth view is
`reference/growth-views/LIAB.ST.md`, registered 2026-08-26 -- base 2%,
bear 0%, bull 4% -- UNCHANGED.

Prints fv_base with E29's band, bear and bull, the basis line, the FULL
run record with every bridge leg named, g* at the last settled close,
price against fv_base and FV_bull, whether S6.4 or C4 fires, and the MBP
tier 2 implies against the bear case (the tier stands; not re-scored).

WRITES `reference/LIAB.ST-STRIKE-2026-08-30.md` and
`reference/run-records/LIAB.ST-2026-08-30.json`. Does NOT write
config/watchlist.yaml -- that entry is the owner's write, made by hand
from this printout with a dated backup beside it.

    python tools/restrike_liab_2026_08_30.py
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

TICKER = "LIAB.ST"
RUN_TS = datetime.now(ZoneInfo("Europe/Stockholm"))
AS_OF = RUN_TS.date()
STAMP = "2026-08-30"
PRIOR = "2026-08-26"
TIER = 2                                                 # stands; not re-scored
RECORDS = PROJECT_ROOT / "reference" / "run-records"
RATE = R.Rate(core_expected_return=0.070, premium=0.025)
CORE_EXPECTED_RETURN = 0.070                             # E29's anchor
GROWTH = R.Growth(base=0.02, bear=0.0, bull=0.04,
                  view_file="reference/growth-views/LIAB.ST.md",
                  view_date=date(2026, 8, 26))
RULINGS = "E34, E35/E35.1, E65-E68, E70"


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
    return f"LIAB.ST re-strike, {STAMP}, {sha}"


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
        prior_net_debt=-prior.legs().net_cash,
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
        f"(price {'>=' if trim else '<'} fv_base).",
        f"- **C4, 'exit when even the bull case does not beat the index': "
        f"{'FIRES' if c4_fires else 'does not fire'}.** "
        f"Expected return from {price:.2f} to FV_bull {bull:,.2f} is **{bull_gap:+.1%}**; "
        f"the index core's expected return is {CORE_EXPECTED_RETURN:.1%} a year (E29's "
        f"anchor). C4 states no horizon: on the reading applied to MSFT, UNA.AS and SAP.DE "
        f"(price above/below FV_bull, expected return positive or negative) it "
        f"{'fires' if c4_fires else 'does not fire'} outright here since price is "
        f"{'above' if c4_fires else 'below'} FV_bull; read as ONE year against "
        f"{CORE_EXPECTED_RETURN:.1%}, the bull-case gap is "
        f"{'BELOW' if bull_gap < CORE_EXPECTED_RETURN else 'ABOVE'} the index"
        f"{' and would also fire on that reading' if bull_gap < CORE_EXPECTED_RETURN and not c4_fires else ''}"
        f"{', though C4 already fires outright' if c4_fires else ''}. "
        f"Which horizon C4 means is the owner's to say.",
        "",
        "*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on "
        "the fragility, and nothing here does.*",
    ])


def render(s: dict) -> str:
    cur, qcur = s["currency"], s["quote_currency"]
    rec, prior = s["record"], s["prior"]
    stamp = RUN_TS.strftime('%Y-%m-%d %H:%M %Z')
    out = [f"# {TICKER} -- re-struck under {RULINGS}, {stamp}", "",
           f"**{stamp}.** The prior record (`reference/run-records/{TICKER}-{PRIOR}.json`, "
           f"RESTRIKE-2026-08-26-b) already stood under E34 and E35/E35.1; the rulings "
           f"since -- E65-E68 and E70 -- are applied here off the store file as it stands, "
           f"and the record is written to `reference/run-records/{TICKER}-{STAMP}.json`. "
           f"`config/watchlist.yaml` is the OWNER'S write, made by hand from this printout "
           f"with a dated backup beside it.",
           "",
           f"Growth view: `{GROWTH.view_file}`, registered by the owner "
           f"{GROWTH.view_date.isoformat()} -- base {GROWTH.base:.0%} (Euroconstruct's "
           f"~2%/yr to 2028), bear {GROWTH.bear:.0%}, bull {GROWTH.bull:.0%} -- UNCHANGED (E28).",
           "",
           f"Tool: `tools/restrike_liab_2026_08_30.py` at `{tool_commit()}`. r 9.5% (7.0% "
           f"core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year "
           f"discounting.",
           "",
           f"**BASIS: `{s['basis'].label}` -- the four consecutive quarters 2025-Q3, 2025-Q4, "
           f"2026-Q1 and 2026-Q2, the twelve months ending {s['basis'].end.isoformat()}** "
           f"(E19, named quarter by quarter under E41). Store: `config/manual/{TICKER}.yaml`, "
           f"money in {s['parsed'].money_unit} of {cur}. Price: last SETTLED close "
           f"**{s['price_minor']:.2f} {qcur}** on {s['price_date'].isoformat()} (tool fetch, "
           f"{stamp}).",
           ""]
    gate = s["gate"]
    if gate.refused:
        out += ["**The store's gate refuses:** " + "; ".join(
            f"`{r.kind}` {r.subject}" for r in gate.refusals) + ".", ""]
    else:
        out += ["**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure "
                "the basis reads is VERIFIED (E40).", ""]
    if "gaps" in s:
        out += ["**RECORD INCOMPLETE -- no fair value is printed.** Absent: "
                + "; ".join(s["gaps"]), ""]
        return "\n".join(out)
    band, pband = s["band"], s["prior_band"]
    net_debt = -s["legs"].net_cash
    unit = 1e6          # legs() are whole units; the file states millions
    lease = rec.lease
    out += [
        f"- record complete: **True** -- the eight declarations and declaration 3.1 (E70)",
        f"- **FCF0: {s['fcf0']:,.0f} {cur} m** -- interest INSIDE operating cash flow "
        f"(E34): net interest paid {rec.interest.net_interest_paid:,.0f} {cur} m "
        f"(paid 211 - received 10, R12M, Q2 2026 interim p.17) ADDED BACK, pre-tax, "
        f"and net debt subtracted once. Prior record: {s['prior_fcf0']:,.0f} {cur} m"
        + (" -- the same." if abs(s['prior_fcf0'] - s['fcf0']) < 0.05 else " -- MOVED."),
        f"- **lease treatment (E70, declaration 3.1): the flow did NOT bear the lease "
        f"principal** -- {'`no`' if lease.in_operating_cash_flow is False else lease.in_operating_cash_flow}, "
        f"IFRS 16.50(b): principal repayments are FINANCING outflows, so `operating_cash_flow` "
        f"never charged the 1,410 {cur} m lease liability that net debt carries; nothing is "
        f"added back, FCF0 before = after = {s['fcf0']:,.0f} {cur} m. The interest portion "
        f"sits inside the 211 of interest paid and follows E34 above. For this IFRS filer E70 "
        f"changes NOTHING and is DECLARED.",
        f"- **net debt: {net_debt / unit:,.0f} {cur} m** -- {rec.bridge.note.split('. Capex legs')[0]}. "
        f"Prior record: {s['prior_net_debt'] / unit:,.0f} {cur} m"
        + (" -- the same total; E65 names the finance leases as inside the stated lease "
           "total, E66/E67 the two borrowing captions (5 current + 3,378 non-current), "
           "E68 the asset-retirement leg at 0 (E68.1 caption zero) -- legs NAMED, nothing MOVED."
           if abs(s['prior_net_debt'] - net_debt) < 0.5 * unit else " -- MOVED."),
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
        f"- **tier {TIER} (carried; section 4.4 NOT re-scored). MBP (E28): "
        f"{s['mbp'].mid:,.2f} {cur}** = bear {s['bear']:,.2f} x {V.TIER_MULTIPLIER[TIER]:.2f} "
        f"(band r {band.rate - band.delta:.1%} {s['mbp'].low:,.2f} / r "
        f"{band.rate + band.delta:.1%} {s['mbp'].high:,.2f}). Price {s['price']:.2f} is "
        f"{s['price'] / s['mbp'].mid - 1:+.1%} against it. stop_price 112 -- UNTOUCHED.",
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
        "- **It does not touch the growth view** -- base 2%, bear 0%, bull 4% are the "
        "registered ones.",
        "- **It does not re-score tier.** Tier 2 is carried as the owner ruled it "
        "2026-08-26 (RULED A, Build 2 item 5).",
        "- **It does not touch stop_price.** 112 stands (E39: a stop is about the loss, "
        "not the worth).",
        "- **It does not authorise a purchase or a sale.** S0 rule 4 stands.",
        "",
    ]
    return "\n".join(out)


def main() -> int:
    RECORDS.mkdir(parents=True, exist_ok=True)
    s = strike()
    (RECORDS / f"{TICKER}-{STAMP}.json").write_text(
        json.dumps(s["record"].to_dict(), indent=1) + "\n", encoding="utf-8")
    text = render(s)
    (PROJECT_ROOT / "reference" / f"{TICKER}-STRIKE-{STAMP}.md").write_text(
        text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
