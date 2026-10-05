"""AUTO.L: the first section 5 strike on the tool path, 2026-08-27.

Registers nothing new here -- the growth view is `reference/growth-views/
AUTO.L.md`, pre-registered by the owner BEFORE this script ran. This
script builds the run record off `config/manual/AUTO.L.yaml`, prints
fv_base, the bear/bull cases, g* at the settled close, and whether S6.4 or
C4 fire -- and WRITES TWO THINGS ONLY: `reference/AUTO.L-STRIKE-2026-08-27.md`
(the printout) and `reference/run-records/AUTO.L-2026-08-27.json` (the run
record). It NEVER writes fv_base, tier or mbp to config/watchlist.yaml --
linking a record to an entry is the owner's write.

Tier has not been scored for AUTO.L, so MBP is not struck here -- E28 makes
MBP the bear-case value times the tier cushion, and there is no tier to
apply one with. Printed as DATA MISSING, not computed.

    python tools/strike_auto_l_2026_08_27.py
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

TICKER = "AUTO.L"
RUN_TS = datetime.now(ZoneInfo("Europe/London"))
AS_OF = RUN_TS.date()
OUT = PROJECT_ROOT / "reference" / "AUTO.L-STRIKE-2026-08-27.md"
RECORDS = PROJECT_ROOT / "reference" / "run-records"
RATE = R.Rate(core_expected_return=0.070, premium=0.025)
CORE_EXPECTED_RETURN = 0.070                             # E29's anchor
GROWTH_VIEW_DATE = date(2026, 8, 27)


def growth_view() -> R.Growth:
    """The pre-registered view, `reference/growth-views/AUTO.L.md` -- set
    by the owner 2026-08-27, before this script ran and before g* was
    solved for (E28's binding pre-registration order)."""
    return R.Growth(base=0.03, bear=0.0, bull=0.06,
                    view_file=f"reference/growth-views/{TICKER}.md",
                    view_date=GROWTH_VIEW_DATE)


def settled_close() -> tuple[float, date]:
    """Last settled close, in the quote currency's MINOR unit (GBX, pence
    for AUTO.L -- fx.py's own note: London quotes in pence, and the daily
    price series carries the minor unit even though enterprise value and
    market cap would not)."""
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
    return f"AUTO.L first strike, 2026-08-27, {sha}"


def strike() -> dict:
    parsed = M.load_manual(TICKER, directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    gate = M.section5_gate(parsed, as_of=AS_OF)
    growth = growth_view()
    price_minor, price_date = settled_close()
    # E5(b)/fx.py: the price SERIES is in the quote currency's MINOR unit;
    # fv_base is struck in money_unit (GBP, the reporting currency's major
    # unit). Divide the price by the minor-unit factor -- do NOT multiply
    # fv_base -- or every comparison below is off by 100x.
    divisor = fx.minor_unit_divisor(parsed.quote_currency)
    price = price_minor / divisor
    record = R.from_store(parsed, basis, growth=growth, run_ts=RUN_TS,
                          hand_inputs=(), price_date=price_date, rate=RATE,
                          tool_commit=tool_commit())
    out = dict(ticker=TICKER, parsed=parsed, basis=basis, gate=gate,
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
    )
    return out


def money(v: float, unit: float) -> str:
    return f"{v / unit:,.0f}"


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
    # AUTO.L declares money_unit: millions (config/manual/AUTO.L.yaml), so
    # record.fcf0() already returns a millions-scale number -- unlike
    # SAP.DE's money_unit: whole, unit stays 1.0 here, not 1e6.
    unit = 1.0
    g = s["growth"]
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
                "the basis reads is VERIFIED; six remain UNVERIFIED but unread at this "
                "basis (E21, E60), named below.", ""]
        out += ["| Figure | Value | Why it does not block |", "|---|---:|---|"]
        for figure, why in gate.unread:
            out.append(f"| `{figure.name}` | {figure.value:,.4g} | {why} |")
        out += [""]
    if "gaps" in s:
        out += ["**RECORD INCOMPLETE -- no fair value is printed.** Absent: "
                + "; ".join(s["gaps"]), ""]
        return "\n".join(out)
    band = s["band"]
    out += [
        f"- record complete: **True**",
        f"- **FCF0: {money(s['fcf0'], unit)} {cur} m**"
        + (" -- " + M.ACCRUAL_PROXY_LABEL if s["record"].interest.accrual_proxy else
           " (interest_in_ocf: no -- nothing added back, E34)"),
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
        f"- **tier: NOT SCORED.** Section 4.4 has not scored AUTO.L, so E28's MBP -- "
        f"the bear-case value times the tier cushion -- has no tier to apply. **MBP is "
        f"not struck here; this is DATA MISSING, not a computed absence.**",
        "",
        "<details><summary>the run record</summary>", "",
        s["record"].render(), "", "</details>", "",
    ]
    return "\n".join(out)


def main() -> int:
    s = strike()
    RECORDS.mkdir(parents=True, exist_ok=True)
    if "record" in s:
        (RECORDS / f"{s['ticker']}-2026-08-27.json").write_text(
            json.dumps(s["record"].to_dict(), indent=1) + "\n", encoding="utf-8")
    parts = [
        "# AUTO.L -- first section 5 strike on the tool path, 2026-08-27",
        "",
        f"**{RUN_TS.strftime('%Y-%m-%d %H:%M %Z')}. `config/watchlist.yaml` IS NOT "
        "WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a "
        "stop.** The section 5 run record is written to "
        "`reference/run-records/AUTO.L-2026-08-27.json` so that linking it to a "
        "watchlist entry (`run_record:`) remains the owner's write.",
        "",
        f"Growth view: `reference/growth-views/AUTO.L.md`, pre-registered by the owner "
        f"2026-08-27, BEFORE this script ran and before g* was solved (E28's binding "
        f"order).",
        "",
        f"Tool: `tools/strike_auto_l_2026_08_27.py` at `{tool_commit()}`. r 9.5% (7.0% "
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
        "- **It does not score tier.** Section 4.4 has not run for AUTO.L; MBP is "
        "printed as DATA MISSING rather than computed on a placeholder tier.",
        "- **It does not authorise a purchase.** S0 rule 4 stands: below price X, "
        "under conditions Y, with stop Z -- none of which this run sets.",
        "",
    ]
    text = "\n".join(parts)
    OUT.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
