"""CTSH, LII and AOS: re-struck under E70, 2026-08-30.

E70 (2026-08-30) counts a lease once, in net debt, never also in the flow:
where the operating cash flow bore the operating lease payments they are
added back, the leg named, and the run record carries declaration 3.1.
The three names were struck before the ruling existed (CTSH 2026-08-28,
LII and AOS 2026-08-30 03:14 EDT); this script strikes each again off
`config/manual/<TICKER>.yaml` as it stands, with the growth views already
registered (`reference/growth-views/<TICKER>.md`, UNCHANGED), and prints:

- fv_base with E29's r +/- 0.5% band, the bear and bull cases;
- FCF0 BEFORE and AFTER the lease add-back, the leg named, beside the
  prior strike's FCF0 (which must equal the BEFORE figure);
- g* at the last settled close; price against fv_base and FV_bull;
  whether S6.4 or C4 fires;
- CTSH: the MBP tier 2 implies against the new bear case (the tier was
  scored 2026-08-29 and is not re-scored here); LII and AOS: no tier, so
  the per-tier range and MBP DATA MISSING.

It WRITES `reference/<TICKER>-STRIKE-2026-08-30-e70.md` and
`reference/run-records/<TICKER>-2026-08-30-e70.json` per name. It does
NOT write config/watchlist.yaml -- the CTSH entry is the owner's write,
made by hand after this printout.

    python tools/restrike_e70_2026_08_30.py
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
STAMP = "2026-08-30-e70"
RECORDS = PROJECT_ROOT / "reference" / "run-records"
RATE = R.Rate(core_expected_return=0.070, premium=0.025)
CORE_EXPECTED_RETURN = 0.070                             # E29's anchor

#: The registered views, in the owner's numbers, UNCHANGED (E28: fixed
#: before any fair value and before g*); the tier where section 4.4 has
#: scored the name; and the run record each name was last struck on,
#: before E70 existed.
NAMES = {
    "CTSH": dict(base=0.04, bear=0.0, bull=0.07, view_date=date(2026, 8, 27),
                 tier=2, prior="2026-08-28"),
    "LII": dict(base=0.05, bear=0.0, bull=0.08, view_date=date(2026, 8, 30),
                tier=None, prior="2026-08-30"),
    "AOS": dict(base=0.04, bear=0.0, bull=0.07, view_date=date(2026, 8, 30),
                tier=None, prior="2026-08-30"),
}


def growth_view(ticker: str) -> R.Growth:
    v = NAMES[ticker]
    return R.Growth(base=v["base"], bear=v["bear"], bull=v["bull"],
                    view_file=f"reference/growth-views/{ticker}.md",
                    view_date=v["view_date"])


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
    return f"E70 re-strike, 2026-08-30, {sha}"


def prior_record(ticker: str) -> R.RunRecord:
    path = RECORDS / f"{ticker}-{NAMES[ticker]['prior']}.json"
    return R.RunRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))


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
    prior = prior_record(ticker)
    tier = NAMES[ticker]["tier"]
    out = dict(ticker=ticker, parsed=parsed, basis=basis, gate=gate,
               growth=growth, price=price, price_minor=price_minor,
               divisor=divisor, price_date=price_date, record=record,
               prior=prior, tier=tier,
               currency=record.currency, quote_currency=parsed.quote_currency)
    if not record.complete:
        out["gaps"] = record.missing()
        return out
    legs = record.legs()
    args = dict(fcf0=legs.fcf0, net_cash=legs.net_cash, shares=legs.shares)
    prior_legs = prior.legs()
    prior_args = dict(fcf0=prior_legs.fcf0, net_cash=prior_legs.net_cash,
                      shares=prior_legs.shares)
    out.update(
        fcf0=record.fcf0(),
        fcf0_before=record.fcf0() - (record.lease.principal_added_back or 0.0),
        legs=legs,
        band=record.band(),
        bear=record.strike(growth.bear), bull=record.strike(growth.bull),
        implied=V.implied_growth(price=price, rate=RATE.rate, **args),
        mbp_by_tier={t: V.maximum_buy_price(g_bear=growth.bear, tier=t,
                                            rate=RATE.rate, **args)
                     for t in (1, 2, 3)},
        prior_fcf0=prior.fcf0(), prior_band=prior.band(),
        prior_bear=prior.strike(growth.bear), prior_bull=prior.strike(growth.bull),
        prior_mbp=(V.maximum_buy_price(g_bear=growth.bear, tier=tier,
                                       rate=RATE.rate, **prior_args)
                   if tier else None),
        # the prior record with ONLY the lease declaration added: E70 alone
        e70_alone=R.RunRecord.from_dict({**prior.to_dict(),
                                         "lease": record.to_dict()["lease"]}).strike(),
        prior_net_debt=-prior_legs.net_cash,
        prior_leases=prior.bridge.items.get("leases"),
    )
    return out


def money(v: float, unit: float) -> str:
    return f"{v / unit:,.1f}"


def lease_lines(s: dict, unit: float) -> list[str]:
    """E70: the flow's lease payments, BEFORE and AFTER, the leg named."""
    rec, cur = s["record"], s["currency"]
    lease = rec.lease
    added = lease.principal_added_back or 0.0
    leg = (lease.leg or "operating_lease_payments").split(" ")[0].strip("`")
    standard = "ASC 842-20-45-5(a)" if "ASC 842-20-45-5(a)" in lease.page else lease.page
    agree = abs(s["fcf0_before"] - s["prior_fcf0"]) < 0.5
    return [
        f"- **FCF0 BEFORE the lease add-back: {money(s['fcf0_before'], unit)} {cur} m; "
        f"AFTER: {money(s['fcf0'], unit)} {cur} m** -- leg `{leg}` "
        f"{money(added, unit)} {cur} m added back (E70, declaration 3.1: the "
        f"operating cash flow bears the operating lease payments, {standard}; the "
        f"lease liability {rec.bridge.items.get('leases', 0.0) / unit:,.1f} {cur} m is "
        f"in net debt under E35, so the flow no longer charges it a second time). "
        f"The correction RAISES FCF0 by {added / s['fcf0_before']:+.1%}.",
        f"- prior strike ({NAMES[s['ticker']]['prior']}, before E70): FCF0 "
        f"{money(s['prior_fcf0'], unit)} {cur} m -- "
        + ("EQUALS the BEFORE figure: nothing but the add-back moved."
           if agree else
           f"DIFFERS from the BEFORE figure by "
           f"{money(s['fcf0_before'] - s['prior_fcf0'], unit)} {cur} m -- something "
           f"other than E70 moved; read the two records side by side."),
    ]


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


def mbp_lines(s: dict) -> list[str]:
    t, cur, band, tier = s["ticker"], s["currency"], s["band"], s["tier"]
    lo, hi = band.rate - band.delta, band.rate + band.delta
    if tier:
        m, pm = s["mbp_by_tier"][tier], s["prior_mbp"]
        return [
            f"- **tier {tier} (section 4.4, scored 2026-08-29, NOT re-scored here). "
            f"MBP (E28): {m.mid:,.2f} {cur}** = bear {s['bear']:,.2f} x "
            f"{V.TIER_MULTIPLIER[tier]:.2f} (band r {lo:.1%} {m.low:,.2f} / r {hi:.1%} "
            f"{m.high:,.2f}); prior MBP {pm.mid:,.2f} {cur} (band {pm.low:,.2f} / "
            f"{pm.high:,.2f}) against the prior bear {s['prior_bear']:,.2f}. Price "
            f"{s['price']:.2f} is {s['price'] / m.mid - 1:+.1%} against the new MBP.",
        ]
    out = [
        f"- **tier: NOT SCORED. MBP: DATA MISSING** -- E28's MBP is the bear-case value "
        f"times the tier cushion, and section 4.4 has not scored {t}, so there is no "
        f"tier to apply. **Not struck; not computed on a placeholder.** What it WOULD be "
        f"against the bear case {s['bear']:,.2f} {cur}, across E29's band:",
    ]
    for tr, m in s["mbp_by_tier"].items():
        out.append(f"  - tier {tr} (x{V.TIER_MULTIPLIER[tr]:.2f}): "
                   f"**{m.mid:,.2f} {cur}** (r {lo:.1%} {m.low:,.2f} / r {hi:.1%} "
                   f"{m.high:,.2f}); price {s['price']:.2f} is "
                   f"{s['price'] / m.mid - 1:+.1%} against it")
    return out


def render(s: dict) -> str:
    t, cur, qcur = s["ticker"], s["currency"], s["quote_currency"]
    unit = 1e6          # every file declares money_unit: whole; shown in millions
    g = s["growth"]
    rec = s["record"]
    out = [f"# {t} -- section 5 strike under E70, {RUN_TS.strftime('%Y-%m-%d %H:%M %Z')}", "",
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
                + "; ".join(s["gaps"]), "",
                f"- prior strike ({NAMES[t]['prior']}, before E70): fv_base "
                f"{s['prior'].strike():,.2f} {cur} on FCF0 {money(s['prior'].fcf0(), unit)} "
                f"{cur} m -- it STANDS as struck (exempt from declaration 3.1 by its "
                f"date, RECORD_DECLARATIONS_SINCE); it is NOT re-struck, and no figure "
                f"is estimated to fill the leg.", ""]
        return "\n".join(out)
    band, pband = s["band"], s["prior_band"]
    if rec.interest.accrual_proxy:
        interest_note = f" -- {M.ACCRUAL_PROXY_LABEL}"
    elif rec.interest.interest_expense_only_proxy:
        interest_note = (f" -- {M.INTEREST_EXPENSE_ONLY_LABEL} (bound: "
                         f"{abs(rec.interest.net_interest_paid) / abs(rec.fcf0()):.1%} of FCF0, "
                         f"{rec.interest.net_interest_paid / unit:,.1f} {cur} m added back)")
    else:
        interest_note = " (interest_in_ocf: no -- nothing added back, E34)"
    net_debt = -s["legs"].net_cash
    out += [
        f"- record complete: **True** -- eight declarations and declaration 3.1 (E70)",
        f"- **FCF0: {money(s['fcf0'], unit)} {cur} m**{interest_note}",
        *lease_lines(s, unit),
        f"- **net debt: {money(net_debt, unit)} {cur} m** -- {rec.bridge.note.split('. Capex legs')[0]} "
        f"(UNCHANGED by E70: the lease was already in)",
        "",
        f"- **fv_base (Method C, E28): {band.mid:,.2f} {cur}** (prior {pband.mid:,.2f}: "
        f"**{band.mid / pband.mid - 1:+.1%}**). E70 alone on the prior record gives "
        f"{s['e70_alone']:,.2f}"
        + (f"; the rest is the bridge, which moved between the strikes from net debt "
           f"{money(s['prior_net_debt'], unit)} to {money(net_debt, unit)} {cur} m "
           f"(leases {(s['prior_leases'] or 0.0) / unit:,.1f} -> "
           f"{rec.bridge.items.get('leases', 0.0) / unit:,.1f}: E65's finance leases "
           f"beside operating, applied to the file after the prior strike)."
           if abs(s['prior_net_debt'] - net_debt) > 0.5 else
           " -- the whole move; the bridge is unchanged between the strikes."),
        f"- band across E29's +/-0.5% (r {band.rate - band.delta:.1%} / {band.rate:.1%} "
        f"/ {band.rate + band.delta:.1%}): **{band.low:,.2f} / {band.mid:,.2f} / "
        f"{band.high:,.2f} {cur}** (prior {pband.low:,.2f} / {pband.mid:,.2f} / "
        f"{pband.high:,.2f})",
        f"- bear (g {g.bear:.1%}): **{s['bear']:,.2f} {cur}** (prior {s['prior_bear']:,.2f})",
        f"- bull (g {g.bull:.1%}): **{s['bull']:,.2f} {cur}** (prior {s['prior_bull']:,.2f})",
        f"- implied growth g* at the settled close {s['price']:.2f} {cur}: "
        f"**{s['implied']:.2%}** (E28; the view in `{g.view_file}` was fixed "
        f"{g.view_date.isoformat()}, before any fair value and before g* -- UNCHANGED here)",
        f"- *{V.rate_declaration(cur)}* (E37)",
        "",
        *mbp_lines(s),
        "",
        "<details><summary>the run record -- every declaration, 3.1 among them, and "
        "every input with its provenance</summary>", "",
        rec.render(), "", "</details>", "",
    ]
    return "\n".join(out)


def report(s: dict) -> str:
    t = s["ticker"]
    writes = ("the CTSH entry in `config/watchlist.yaml` is the OWNER'S write, made by "
              "hand from this printout with a dated backup beside it"
              if t == "CTSH" else
              "`config/watchlist.yaml` IS NOT WRITTEN -- no tier is scored, so no "
              "fv_base or mbp goes there")
    return "\n".join([
        f"# {t} -- re-struck under E70, 2026-08-30",
        "",
        f"**{RUN_TS.strftime('%Y-%m-%d %H:%M %Z')}.** E70 (2026-08-30) counts a lease "
        "once, in net debt, never also in the flow. The prior strike "
        f"(`reference/run-records/{t}-{NAMES[t]['prior']}.json`) was made before the "
        "ruling existed and charged the lease twice; this strike carries declaration "
        f"3.1 and is written to `reference/run-records/{t}-{STAMP}.json`. {writes}.",
        "",
        f"Growth view: `reference/growth-views/{t}.md`, registered by the owner "
        f"{NAMES[t]['view_date'].isoformat()}, UNCHANGED (E28).",
        "",
        f"Tool: `tools/restrike_e70_2026_08_30.py` at `{tool_commit()}`. r 9.5% (7.0% "
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
        "- **It does not touch the growth view.** g_base, g_bear and g_bull are the "
        "registered ones.",
        "- **It does not score tier.** CTSH's tier 2 is section 4.4's score of "
        "2026-08-29, carried; LII and AOS have none, and MBP is DATA MISSING for them.",
        "- **It does not authorise a purchase.** S0 rule 4 stands: below price X, "
        "under conditions Y, with stop Z -- none of which this run sets.",
        "",
    ])


def main() -> int:
    RECORDS.mkdir(parents=True, exist_ok=True)
    for ticker in NAMES:
        s = strike(ticker)
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
