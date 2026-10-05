"""ACN, GDDY, NVR and ULTA: first section 5 strikes on the tool path, 2026-08-30.

The growth views are `reference/growth-views/ACN.md`, `GDDY.md`, `NVR.md`
and `ULTA.md`, pre-registered by the owner 2026-08-30, before this script
ran and before g* was solved. This script builds each run record off
`config/manual/<TICKER>.yaml`, prints fv_base with E29's band, the bear and
bull cases, the basis line with the period and its end date, the full run
record with every bridge leg named and every proxy's bound stated, g* at
the settled close, price against fv_base and FV_bull, whether S6.4 or C4
fire as the framework's own output, SBC as a percentage of FCF0 (E36's
deduction is doing visible work), and -- because tier is NOT scored for any
of them -- MBP as DATA MISSING beside what it WOULD be at tier 1, 2 and 3
against the bear case. It WRITES TWO THINGS PER NAME ONLY:
`reference/<TICKER>-STRIKE-2026-08-30.md` (the printout) and
`reference/run-records/<TICKER>-2026-08-30.json` (the run record). It
NEVER writes fv_base, tier or mbp to config/watchlist.yaml.

    python tools/strike_acn_gddy_nvr_ulta_2026_08_30.py
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

RUN_TS = datetime.now(ZoneInfo("America/New_York"))
AS_OF = RUN_TS.date()
STAMP = "2026-08-30"
RECORDS = PROJECT_ROOT / "reference" / "run-records"
RATE = R.Rate(core_expected_return=0.070, premium=0.025)
CORE_EXPECTED_RETURN = 0.070                             # E29's anchor
GROWTH_VIEW_DATE = date(2026, 8, 30)

#: The pre-registered views, in the owner's numbers (the words are in the
#: view files). Set 2026-08-30, before this script ran (E28's order).
VIEWS = {
    "ACN": dict(base=0.045, bear=0.0, bull=0.075),
    "GDDY": dict(base=0.05, bear=0.01, bull=0.08),
    "NVR": dict(base=0.025, bear=-0.03, bull=0.065),
    "ULTA": dict(base=0.035, bear=0.0, bull=0.065),
}

#: What a reader should see about the accounts' age, per name (E19, B24).
STALENESS = {
    "ACN": ("**THE ACCOUNTS ARE 364 DAYS OLD.** The basis is FY2025, the twelve "
            "months to 2025-08-31, and FY2026 CLOSES TOMORROW, 2026-08-31; its "
            "10-K is due about 2026-10-09 and will supersede this basis. The "
            "three FY2026 10-Qs (to 2025-11-30, 2026-02-28 and 2026-05-31) are "
            "passed over by the annual path. Inside `MAX_REPORT_AGE_DAYS` 550; "
            "B24 (the basis-to-price distance) is open, and this is the widest "
            "gap on the books."),
    "GDDY": ("The basis is FY2025, the twelve months to 2025-12-31, 242 days old; "
             "the Q1 and Q2 2026 10-Qs are passed over by the annual path."),
    "NVR": ("The basis is FY2025, the twelve months to 2025-12-31, 242 days old; "
            "the Q1 and Q2 2026 10-Qs are passed over by the annual path."),
    "ULTA": ("The basis is the twelve months to 2026-01-31 -- the filer's FISCAL "
             "2025, which the store keys FY2026 on the calendar year of its end "
             "-- 211 days old; the Q1 and Q2 fiscal-2026 10-Qs (to 2026-05-02 and "
             "2026-08-01) are passed over by the annual path."),
}


def growth_view(ticker: str) -> R.Growth:
    v = VIEWS[ticker]
    return R.Growth(base=v["base"], bear=v["bear"], bull=v["bull"],
                    view_file=f"reference/growth-views/{ticker}.md",
                    view_date=GROWTH_VIEW_DATE)


def settled_close(ticker: str) -> tuple[float, date]:
    """Last settled close in the quote currency (USD, no minor unit)."""
    fetched = get_history(ticker, CACHE_DIR, now=RUN_TS, write=False)
    m = MT.compute(fetched.frame, AS_OF, MT.settled_through(RUN_TS))
    return m.last_close, m.last_close_date


def tool_commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, cwd=PROJECT_ROOT,
                             check=True).stdout.strip()
    except Exception:  # pragma: no cover
        sha = "unknown"
    return f"ACN/GDDY/NVR/ULTA first strikes, {STAMP}, {sha}"


def strike(ticker: str) -> dict:
    parsed = M.load_manual(ticker, directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    gate = M.section5_gate(parsed, as_of=AS_OF)
    growth = growth_view(ticker)
    price_minor, price_date = settled_close(ticker)
    divisor = fx.minor_unit_divisor(parsed.quote_currency)
    price = price_minor / divisor
    record = R.from_store(parsed, basis, growth=growth, run_ts=RUN_TS,
                          hand_inputs=(), price_date=price_date, rate=RATE,
                          tool_commit=tool_commit())
    out = dict(ticker=ticker, parsed=parsed, basis=basis, gate=gate,
               growth=growth, price=price, price_minor=price_minor,
               divisor=divisor, price_date=price_date, record=record,
               currency=record.currency, quote_currency=parsed.quote_currency)
    if not record.complete:
        out["gaps"] = record.missing()
        return out
    legs = record.legs()
    args = dict(fcf0=legs.fcf0, net_cash=legs.net_cash, shares=legs.shares)
    out.update(
        fcf0=record.fcf0(),
        legs=legs,
        band=record.band(),
        bear=record.strike(growth.bear), bull=record.strike(growth.bull),
        implied=V.implied_growth(price=price, rate=RATE.rate, **args),
        # E28's MBP at each tier, against the PRE-REGISTERED bear case,
        # across E29's band -- printed so the owner sees the range before
        # scoring; NONE of them is the MBP, because there is no tier.
        mbp_by_tier={tier: V.maximum_buy_price(g_bear=growth.bear, tier=tier,
                                               rate=RATE.rate, **args)
                     for tier in (1, 2, 3)},
    )
    return out


def money(v: float, unit: float) -> str:
    return f"{v / unit:,.1f}"


def aro_leg_line(s: dict) -> str:
    """Which legs are FIGURES and which are CAPTION ZEROS, named."""
    rec = s["record"]
    aro = next((i for i in rec.inputs if i.name == "asset_retirement_obligation"), None)
    if aro is None:
        return "- asset-retirement leg: NOT IN THE RECORD"
    if aro.value:
        return (f"- **asset-retirement leg (E68): {aro.value:,.0f}**, a stated figure "
                f"(declaration 8).")
    return (f"- **asset-retirement leg (E68): 0 -- a CAPTION ZERO under E68.1, not a "
            f"figure.** The balance sheet presents no asset-retirement or "
            f"decommissioning caption, neither term appears anywhere in the filing, "
            f"and the business owns nothing requiring decommissioning; the captions "
            f"with room are named on the field. Every other leg of the bridge is a "
            f"tagged figure or a hand-read stated figure (declaration 8).")


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
        f"### {s['ticker']} -- the framework's own output on the price (NOT a recommendation)",
        "",
        f"- price {price:.2f} {cur} vs fv_base {fv:,.2f} {cur}: **{vs_fv:+.1%}**"
        + (" -- price is ABOVE fv_base" if vs_fv > 0 else " -- price is BELOW fv_base"),
        f"- price {price:.2f} {cur} vs FV_bull {bull:,.2f} {cur}: **{vs_bull:+.1%}**"
        + (" -- price is ABOVE the bull case" if vs_bull > 0 else " -- price is BELOW the bull case"),
        f"- **section 6.4, 'At FV_base, trim 25-50%; reassess': {'FIRES' if trim else 'does not fire'}** "
        f"(price {'>=' if trim else '<'} fv_base). A trim presupposes a position; none is held.",
        f"- **C4 (E42: no horizon -- above FV_bull the full position is sold at the next "
        f"session): {'FIRES' if c4_fires else 'does not fire'}.** Price is "
        f"{'above' if c4_fires else 'below'} FV_bull. Expected return from {price:.2f} to "
        f"FV_bull {bull:,.2f} is **{bull_gap:+.1%}** against the index core's "
        f"{CORE_EXPECTED_RETURN:.1%} a year (E29's anchor)"
        + (f"; read as ONE year, the bull-case gap is "
           f"{'BELOW' if bull_gap < CORE_EXPECTED_RETURN else 'ABOVE'} the index."
           if not c4_fires else "."),
        "",
        "*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on "
        "the fragility, and nothing here does.*",
    ])


def interest_line(rec, unit: float, cur: str) -> str:
    net = rec.interest.net_interest_paid
    if rec.interest.accrual_proxy:
        direction = "ADDED BACK" if net >= 0 else "REMOVED (a net interest INCOME)"
        return (f" -- {M.ACCRUAL_PROXY_LABEL}: the income statement's net, "
                f"{net / unit:,.1f} {cur} m {direction}. Pre-tax, as E34 accepts.")
    if rec.interest.interest_expense_only_proxy:
        return (f" -- {M.INTEREST_EXPENSE_ONLY_LABEL}: bound "
                f"**{abs(net) / abs(rec.fcf0()):.1%} of FCF0**, "
                f"{net / unit:,.1f} {cur} m added back")
    if rec.interest.in_operating_cash_flow:
        return f" -- net interest paid {net / unit:,.1f} {cur} m added back (E34)"
    return " (interest_in_ocf: no -- nothing added back, E34)"


def render(s: dict) -> str:
    t, cur, qcur = s["ticker"], s["currency"], s["quote_currency"]
    unit = 1e6          # every file declares money_unit: whole; shown in millions
    g = s["growth"]
    rec = s["record"]
    out = [f"# {t} -- section 5 strike, {RUN_TS.strftime('%Y-%m-%d %H:%M %Z')}", "",
           f"Store: `config/manual/{t}.yaml`. **BASIS: `{s['basis'].label}`, the twelve "
           f"months ending {s['basis'].end.isoformat()}** (E19). {STALENESS[t]} Price: "
           f"last SETTLED close **{s['price_minor']:.2f} {qcur}** on "
           f"{s['price_date'].isoformat()} (tool fetch, "
           f"{RUN_TS.strftime('%Y-%m-%d %H:%M %Z')}).",
           ""]
    gate = s["gate"]
    if gate.refused:
        out += ["**The store's gate refuses:** " + "; ".join(
            f"`{r.kind}` {r.subject}" for r in gate.refusals) + ".", ""]
    else:
        out += ["**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure "
                "the basis reads is VERIFIED.", ""]
    if "gaps" in s:
        out += ["**RECORD INCOMPLETE -- no fair value is printed.** Absent: "
                + "; ".join(s["gaps"]), ""]
        return "\n".join(out)
    band = s["band"]
    net_debt = -s["legs"].net_cash
    sbc = rec.sbc.amount or 0.0
    lease = rec.lease.principal_added_back or 0.0
    out += [
        f"- record complete: **True**",
        f"- **FCF0: {money(s['fcf0'], unit)} {cur} m**{interest_line(rec, unit, cur)}",
        f"- **share-based compensation (E36): {money(sbc, unit)} {cur} m deducted = "
        f"{sbc / s['fcf0']:.1%} of FCF0** ({sbc / (s['fcf0'] + sbc):.1%} of the flow "
        f"before the deduction)",
        f"- lease principal (E70): {money(lease, unit)} {cur} m added back "
        f"({lease / s['fcf0']:.1%} of FCF0); the lease liability stays in net debt",
        f"- **net debt: {money(net_debt, unit)} {cur} m"
        + (" (NET CASH)" if net_debt < 0 else "")
        + f"** -- {rec.bridge.note.split('. Capex legs')[0]}",
        aro_leg_line(s),
        f"- divisor: {rec.shares.count:,.0f} shares -- {rec.shares.basis.split(';')[0]} "
        f"(`divisor_basis: {rec.shares.divisor_basis}`)",
        "",
        f"- **fv_base (Method C, E28): {band.mid:,.2f} {cur}**",
        f"- band across E29's +/-0.5% (r {band.rate - band.delta:.1%} / {band.rate:.1%} "
        f"/ {band.rate + band.delta:.1%}): **{band.low:,.2f} / {band.mid:,.2f} / "
        f"{band.high:,.2f} {cur}**",
        f"- bear (g {g.bear:.1%}): **{s['bear']:,.2f} {cur}**",
        f"- bull (g {g.bull:.1%}): **{s['bull']:,.2f} {cur}**",
        f"- implied growth g* at the settled close {s['price']:.2f} {cur}: "
        f"**{s['implied']:.2%}** (E28; the view in `{g.view_file}` was fixed "
        f"{g.view_date.isoformat()}, before this was solved)",
        f"- *{V.rate_declaration(cur)}* (E37)",
        "",
        f"- **tier: NOT SCORED. MBP: DATA MISSING** -- E28's MBP is the bear-case value "
        f"times the tier cushion, and section 4.4 has not scored {t}, so there is no "
        f"tier to apply. **Not struck; not computed on a placeholder.** What it WOULD be "
        f"against the bear case {s['bear']:,.2f} {cur}, across E29's band, so the range "
        f"is visible before scoring:",
    ]
    for tier, m in s["mbp_by_tier"].items():
        out.append(f"  - tier {tier} (x{V.TIER_MULTIPLIER[tier]:.2f}): "
                   f"**{m.mid:,.2f} {cur}** (r {band.rate - band.delta:.1%} "
                   f"{m.low:,.2f} / r {band.rate + band.delta:.1%} {m.high:,.2f}); "
                   f"price {s['price']:.2f} is {s['price'] / m.mid - 1:+.1%} against it")
    out += [
        "",
        "<details><summary>the run record -- every leg of the bridge (declaration 4, "
        "item by item) and every input with its provenance (declaration 8), including "
        "every proxy and every caption zero</summary>", "",
        rec.render(), "", "</details>", "",
    ]
    return "\n".join(out)


def report(s: dict) -> str:
    t = s["ticker"]
    return "\n".join([
        f"# {t} -- first section 5 strike on the tool path, {STAMP}",
        "",
        f"**{RUN_TS.strftime('%Y-%m-%d %H:%M %Z')}. `config/watchlist.yaml` IS NOT "
        "WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a "
        "stop.** The section 5 run record is written to "
        f"`reference/run-records/{t}-{STAMP}.json` so that linking it to a "
        "watchlist entry (`run_record:`) remains the owner's write.",
        "",
        f"Growth view: `reference/growth-views/{t}.md`, pre-registered by the owner "
        f"{GROWTH_VIEW_DATE.isoformat()}, BEFORE this script ran and before g* was "
        f"solved (E28's binding order).",
        "",
        f"Tool: `tools/strike_acn_gddy_nvr_ulta_2026_08_30.py` at `{tool_commit()}`. "
        f"r 9.5% (7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; "
        f"end-of-year discounting.",
        "",
        render(s),
        framework_output(s) if "band" in s else "",
        "",
        "---",
        "",
        "## What this run does NOT do",
        "",
        "- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp are "
        "not written there.",
        f"- **It does not score tier.** Section 4.4 has not run for {t}; MBP is "
        "printed as DATA MISSING, and the per-tier figures are the range, not a choice.",
        "- **It does not authorise a purchase.** S0 rule 4 stands: below price X, "
        "under conditions Y, with stop Z -- none of which this run sets.",
        "",
    ])


def main() -> int:
    RECORDS.mkdir(parents=True, exist_ok=True)
    for ticker in VIEWS:
        s = strike(ticker)
        if "record" in s:
            (RECORDS / f"{ticker}-{STAMP}.json").write_text(
                json.dumps(s["record"].to_dict(), indent=1) + "\n", encoding="utf-8")
        text = report(s)
        (PROJECT_ROOT / "reference" / f"{ticker}-STRIKE-{STAMP}.md").write_text(
            text, encoding="utf-8")
        print(text)
        print("\n\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
