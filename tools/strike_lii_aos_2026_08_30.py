"""LII and AOS: first section 5 strikes on the tool path, 2026-08-30.

The growth views are `reference/growth-views/LII.md` and `AOS.md`,
pre-registered by the owner 2026-08-30, before this script ran and before
g* was solved. This script builds each run record off
`config/manual/<TICKER>.yaml`, prints fv_base with E29's band, the bear
and bull cases, g* at the settled close, whether S6.4 or C4 fire, and --
because tier is NOT scored for either name -- MBP as DATA MISSING beside
what it WOULD be at tier 1, 2 and 3 against the bear case. It WRITES
FOUR THINGS ONLY: `reference/<TICKER>-STRIKE-2026-08-30.md` (the printout)
and `reference/run-records/<TICKER>-2026-08-30.json` (the run record),
per name. It NEVER writes fv_base, tier or mbp to config/watchlist.yaml.

    python tools/strike_lii_aos_2026_08_30.py
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
    "LII": dict(base=0.05, bear=0.0, bull=0.08),
    "AOS": dict(base=0.04, bear=0.0, bull=0.07),
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
    return f"LII/AOS first strikes, {STAMP}, {sha}"


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
    rule = "E68.2" if "E68.2" in (aro.provenance or "") else "E68.1"
    return (f"- **asset-retirement leg (E68): {aro.value:,.0f} -- a CAPTION ZERO under "
            f"{rule}, not a figure.** "
            + ("The filer discloses environmental remediation accruals inside "
               "captions with room and states no balance-sheet amount; Note 5 and "
               "the 10.9m charged in 2025 are named on the field (E68.2)."
               if rule == "E68.2" else
               "The balance sheet presents no asset-retirement or decommissioning "
               "caption and the business owns nothing requiring decommissioning "
               "(E68.1); the remediation accrual behind the deferred tax asset "
               "'Environmental liabilities 1.3' is named on the field, not included.")
            + " Every other leg of the bridge is a tagged figure (declaration 8).")


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
        f"(price {'>=' if trim else '<'} fv_base).",
        f"- **C4, 'exit when even the bull case does not beat the index': "
        f"{'FIRES' if c4_fires else 'does not fire'}.** "
        f"Expected return from {price:.2f} to FV_bull {bull:,.2f} is **{bull_gap:+.1%}**; "
        f"the index core's expected return is {CORE_EXPECTED_RETURN:.1%} a year (E29's "
        f"anchor). C4 states no horizon: on the reading applied to MSFT and UNA.AS (price "
        f"above/below FV_bull, expected return positive or negative) it "
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
    t, cur, qcur = s["ticker"], s["currency"], s["quote_currency"]
    unit = 1e6          # both files declare money_unit: whole; shown in millions
    g = s["growth"]
    rec = s["record"]
    out = [f"# {t} -- section 5 strike, {RUN_TS.strftime('%Y-%m-%d %H:%M %Z')}", "",
           f"Store: `config/manual/{t}.yaml`. **BASIS: `{s['basis'].label}`, the twelve "
           f"months ending {s['basis'].end.isoformat()}** (E19). Price: last SETTLED "
           f"close **{s['price_minor']:.2f} {qcur}** ({s['price']:.2f} {cur} at "
           f"{s['divisor']:.0f}:1) on {s['price_date'].isoformat()} (tool fetch, "
           f"{RUN_TS.strftime('%Y-%m-%d %H:%M %Z')}).",
           ""]
    gate = s["gate"]
    if gate.refused:
        out += ["**The store's gate refuses:** " + "; ".join(
            f"`{r.kind}` {r.subject}" for r in gate.refusals) + ".", ""]
    else:
        out += ["**The store's gate refuses nothing (SECTION 5 MAY RUN):** every figure "
                "the basis reads is VERIFIED.", ""]
        if gate.unread:
            out += ["| Figure | Value | Why it does not block |", "|---|---:|---|"]
            for figure, why in gate.unread:
                out.append(f"| `{figure.name}` | {figure.value:,.4g} | {why} |")
            out += [""]
    if "gaps" in s:
        out += ["**RECORD INCOMPLETE -- no fair value is printed.** Absent: "
                + "; ".join(s["gaps"]), ""]
        return "\n".join(out)
    band = s["band"]
    if rec.interest.accrual_proxy:
        interest_note = (f" -- {M.ACCRUAL_PROXY_LABEL}: E18's pair, `finance_costs_period` "
                         f"less `finance_income_period` on the basis, "
                         f"{rec.interest.net_interest_paid / unit:,.1f} {cur} m added back")
    elif rec.interest.interest_expense_only_proxy:
        interest_note = (f" -- {M.INTEREST_EXPENSE_ONLY_LABEL} (E61.1, applied by hand after "
                         f"the filing was read: bound "
                         f"**{abs(rec.interest.net_interest_paid) / abs(rec.fcf0()):.1%} of FCF0**, "
                         f"{rec.interest.net_interest_paid / unit:,.1f} {cur} m added back)")
    else:
        interest_note = " (interest_in_ocf: no -- nothing added back, E34)"
    net_debt = -s["legs"].net_cash
    out += [
        f"- record complete: **True**",
        f"- **FCF0: {money(s['fcf0'], unit)} {cur} m**{interest_note}",
        f"- **net debt: {money(net_debt, unit)} {cur} m** -- {rec.bridge.note.split('. Capex legs')[0]}",
        aro_leg_line(s),
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
        "the caption zero on the asset-retirement leg</summary>", "",
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
        f"Tool: `tools/strike_lii_aos_2026_08_30.py` at `{tool_commit()}`. r 9.5% (7.0% "
        f"core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year "
        f"discounting.",
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
