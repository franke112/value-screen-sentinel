"""Build 2, item 10: SAP.DE and LIAB.ST re-struck on the TOOL PATH.

PRINTS, AND WRITES TWO THINGS ONLY: `reference/RESTRIKE-2026-08-26-b.md`
(the printout) and the two section 5 run records under
`reference/run-records/`. It NEVER writes fv_base, tier or mbp to
config/watchlist.yaml -- linking a record to an entry is the owner's write.

    python tools/restrike_2026_08_26_b.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))   # run as a script
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from vss import manual as M
from vss import metrics as MT
from vss import runrecord as R
from vss import valuation as V
from vss.fetch import get_history
from vss.runner import CACHE_DIR, PROJECT_ROOT

RUN_TS = datetime(2026, 8, 26, 9, 0, tzinfo=ZoneInfo("Europe/Stockholm"))
AS_OF = RUN_TS.date()
OUT = PROJECT_ROOT / "reference" / "RESTRIKE-2026-08-26-b.md"
RECORDS = PROJECT_ROOT / "reference" / "run-records"
RATE = R.Rate(core_expected_return=0.070, premium=0.025)
TIERS = {"SAP.DE": 1, "LIAB.ST": 2}                      # item 5, carried
STOPS = {"SAP.DE": 165, "LIAB.ST": 112}                   # E39: untouched
CORE_EXPECTED_RETURN = 0.070                            # E29's anchor

# --- the first re-strike, for the delta ------------------------------------
FIRST = {
    "SAP.DE": dict(fv=133.20, bear=114.80, bull=166.55, g=(0.08, 0.06, 0.11),
                   fcf0=9_156e6 - 739e6 - 1_331e6, net_cash=386e6, shares=1_175e6),
    "LIAB.ST": dict(fv=137.62, bear=123.99, bull=None, g=(0.02, 0.01, None),
                    fcf0=1050.0, net_cash=-4217.0, shares=77.036),
}

# --- SAP's two hand inputs, each E41-declared -------------------------------
SAP_HAND = (
    R.Input("capex_combined", -735_000_000.0,
            "R12M to 2026-06-30 = FY2025 -739 [Quarterly Statement Q4 2025 "
            "p.19] - Q1-Q2 2025 -358 [Q2 2026 statement p.15, comparative "
            "column] + Q1-Q2 2026 -354 [Q2 2026 p.15]. Per quarter: Q3 2025 "
            "-201 (Q1-Q3 2025 -559 [Q3 2025 p.18] less Q1-Q2 2025 -358); Q4 "
            "2025 -180 (FY -739 less Q1-Q3 -559); Q1 2026 -238 [Q1 2026 p.12, "
            "STATED]; Q2 2026 -116 (Q1-Q2 -354 less Q1 -238). SAP prints "
            "'Purchase of intangible assets and property, plant, and "
            "equipment' CUMULATIVELY and never as a standalone quarter, so "
            "the window's figure is four stated columns netted -- E19's "
            "summation read backwards -- and enters the record BY HAND (E41). "
            "EUR millions as printed, entered in whole EUR. The workbook's "
            "own R12M capex was the same 735", "hand"),
    R.Input("financial_liabilities_consolidated", 10_507_000_000.0,
            "Quarterly Statement Q2 2026 p.10, Consolidated Statements of "
            "Financial Position as at 6/30/2026: 'Financial liabilities' "
            "1,966 (current) + 8,541 (non-current) = 10,507 EUR millions -- "
            "ONE consolidated line per side, leases AND derivatives inside, "
            "and no note that splits it. E14 keeps it out of the borrowing "
            "fields; E35 needs only the SUM; so it enters the record by hand "
            "(E41). For scale: at 2025-12-31 the 20-F split the same lines "
            "(2,050 + 6,021 = 8,071) into borrowings 1,600 + 4,550, leases "
            "1,684 and 237 of derivatives and other -- the derivatives are "
            "hedges, not borrowings, and counting them understates by about "
            "0.2-0.4 EUR a share (report A 4.1)", "hand"),
)


def growth_view(ticker: str) -> R.Growth:
    text = (PROJECT_ROOT / "reference" / "growth-views" / f"{ticker}.md").read_text(
        encoding="utf-8")
    base = re.search(r"Base case FCF growth, 10 years: (\d+(?:\.\d+)?)%", text)
    bear = re.search(r"^Bear: (\d+(?:\.\d+)?)%", text, flags=re.M)
    bull = re.search(r"^Bull: (\d+(?:\.\d+)?)%", text, flags=re.M)
    return R.Growth(base=float(base.group(1)) / 100,
                    view_file=f"reference/growth-views/{ticker}.md",
                    view_date=date(2026, 8, 26),
                    bear=float(bear.group(1)) / 100, bull=float(bull.group(1)) / 100)


def settled_close(ticker: str) -> tuple[float, date]:
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
    return f"Build 2 after REVIEW-4, 2026-08-26, {sha}"


def strike(ticker: str, hand=()) -> dict:
    parsed = M.load_manual(ticker, directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    gate = M.section5_gate(parsed, as_of=AS_OF)
    growth = growth_view(ticker)
    price, price_date = settled_close(ticker)
    record = R.from_store(parsed, basis, growth=growth, run_ts=RUN_TS,
                          hand_inputs=hand, price_date=price_date, rate=RATE,
                          tool_commit=tool_commit())
    out = dict(ticker=ticker, parsed=parsed, basis=basis, gate=gate,
               growth=growth, price=price, price_date=price_date, record=record,
               currency=record.currency, tier=TIERS[ticker])
    if not record.complete:
        out["gaps"] = record.missing()
        return out
    fcf0 = record.fcf0()
    # The three legs NORMALISED TO WHOLE UNITS on the store's own
    # `money_unit` / `share_unit` declarations -- never the raw store
    # figures, which divide wrongly wherever the two scales differ.
    legs = record.legs()
    args = dict(fcf0=legs.fcf0, net_cash=legs.net_cash, shares=legs.shares)
    out.update(
        fcf0=fcf0,
        band=record.band(),
        bear=record.strike(growth.bear), bull=record.strike(growth.bull),
        implied=V.implied_growth(price=price, **args),
        mbp=V.maximum_buy_price(g_bear=growth.bear, tier=TIERS[ticker], **args),
    )
    return out


def money(v: float, unit: float) -> str:
    return f"{v / unit:,.0f}"


def sap_delta(s: dict) -> list[tuple[str, float, str]]:
    f = FIRST["SAP.DE"]
    ev = lambda fcf0, nc: V.equity_value_per_share(fcf0=fcf0, growth=0.08,
                                                   net_cash=nc, shares=1_175e6)
    v1 = ev(9_465e6 - 735e6 - 1_331e6, 386e6)
    v2 = ev(9_465e6 - 735e6 - 1_331e6, 10_511e6 + 1_114e6 - 10_507e6)
    v3 = ev(9_465e6 - 735e6 - 1_331e6, 10_511e6 + 1_114e6 - 10_507e6 - 249e6)
    return [
        ("stored (RESTRIKE-2026-08-26, FY2025 basis)", f["fv"], ""),
        ("E41 (item 3): the WINDOW -- flows R12M to 2026-06-30, OCF 9,465 and "
         "capex 735 (hand, four cumulative columns) for FY2025's 9,156 / 739; "
         "the FY2025 bridge still", v1, "item 3"),
        ("E41 (item 3): the BALANCE SHEET at 2026-06-30 -- consolidated financial "
         "liabilities 10,507 (hand), cash 10,511, other current financial assets "
         "1,114 -> net CASH 1,118 for the 20-F's 386 (which had no current "
         "financial assets at all)", v2, "item 3"),
        ("E35.1 (item 8): pension deficit 249 (20-F, 2025-12-31, E41 annual-only) "
         "-> net cash 869", v3, "item 8"),
        ("E40 (item 2): every tagged figure VERIFIED -- moves NOTHING, and is what "
         "makes the run ADMISSIBLE (the first re-strike was refused on 12 "
         "UNVERIFIED)", v3, "item 2"),
        ("item 6: g 8% base -- the SAME g the first re-strike used; nothing moves", v3, "item 6"),
        ("this run", s["band"].mid, ""),
    ]


def liab_delta(s: dict) -> list[tuple[str, float, str]]:
    f = FIRST["LIAB.ST"]
    ev = lambda fcf0, nc, sh: V.equity_value_per_share(fcf0=fcf0, growth=0.02,
                                                       net_cash=nc, shares=sh)
    v1 = ev(1050.0, -4497.0, 77.036)
    v2 = ev(1050.0, -4536.0, 77.036)
    v3 = v2
    return [
        ("stored (RESTRIKE-2026-08-26, hand inputs, SBC entered as a placeholder "
         "zero, borrowings split a HYPOTHESIS; struck on 77.036m shares)", f["fv"], ""),
        ("E35.1 (item 8): pension deficit 280 -> net debt 4,497, Lindab's own", v1, "item 8"),
        ("item 7: the STORE FILE reads the page -- cash 527 (the first re-strike's "
         "506 was Sep 30, 2025's), other interest-bearing receivables 10, "
         "borrowings 5 + 3,378 STATED (no hypothesis); Lindab's 39 of non-current "
         "interest-bearing assets omitted -> net debt 4,536", v2, "item 7"),
        ("item 7 / E41: share count 77.036m -- FY2025's average = the R12M average "
         "to 2026-06-30 (both 77,036 thousand); the same count, nothing moves", v3, "item 7"),
        ("E36 (item 7): SBC ZERO on E25's note form (AR 2025 p.96, p.112) for the "
         "placeholder zero -- the same 0, and the run now STANDS", v3, "item 7"),
        ("item 6: g 2% base -- the same; bear 0% for the 1% the first re-strike "
         "read from the prose; bull 4% struck for the first time", v3, "item 6"),
        ("this run", s["band"].mid, ""),
    ]


def render(s: dict, delta_rows) -> str:
    t, cur = s["ticker"], s["currency"]
    unit = 1e6 if cur == "EUR" else 1.0
    g = s["growth"]
    first = FIRST[t]
    out = [f"## {t}", "",
           f"Store: `config/manual/{t}.yaml`. Basis **{s['basis'].label}** "
           f"(R12M to {s['basis'].end.isoformat()}), named quarter by quarter "
           f"(E41). Price: last SETTLED close **{s['price']:.2f} {cur}** on "
           f"{s['price_date'].isoformat()} (tool fetch, {RUN_TS.strftime('%Y-%m-%d %H:%M %Z')}).",
           ""]
    gate = s["gate"]
    if gate.refused:
        out += ["**The store's gate refuses:** " + "; ".join(
            f"`{r.kind}` {r.subject}" for r in gate.refusals)
            + ". The record below fills what the store cannot hold BY HAND, each "
              "input with its page, and says so in declaration 4 and 8.", ""]
    else:
        out += ["**The store's gate refuses nothing** (E40: every figure the basis "
                "reads is VERIFIED, and its kind is printed).", ""]
    if "gaps" in s:
        out += ["**RECORD INCOMPLETE -- no fair value is printed.** Absent: "
                + "; ".join(s["gaps"]), ""]
        return "\n".join(out)
    band, mbp = s["band"], s["mbp"]
    out += [
        f"- record complete: **True** (and ADMISSIBLE: E40)",
        f"- **FCF0: {money(s['fcf0'], unit)} {cur} m**"
        + (" -- " + M.ACCRUAL_PROXY_LABEL if s["record"].interest.accrual_proxy else ""),
        f"- **fv_base (Method C, E28): {band.mid:,.2f} {cur}**",
        f"- band across E29's +/-0.5%: {band.low:,.2f} / {band.mid:,.2f} / {band.high:,.2f}",
        f"- bear (g {g.bear:.1%}): **{s['bear']:,.2f}**",
        f"- bull (g {g.bull:.1%}): **{s['bull']:,.2f}**",
        f"- implied growth g* at {s['price']:.2f}: **{s['implied']:.2%}** (E28; the view "
        f"was fixed on 2026-08-26 before this was solved)",
        f"- *{V.rate_declaration(cur)}* (E37)",
        "",
        f"- **tier: {s['tier']}** -- item 5, carried from pre-REVIEW-4 scoring; "
        f"section 4.4 untouched by the review",
        f"- **mbp (E28: bear-case value x tier cushion {V.TIER_MULTIPLIER[s['tier']]:.2f}): "
        f"{mbp.mid:,.2f} {cur}** (band {mbp.low:,.2f} / {mbp.mid:,.2f} / {mbp.high:,.2f})",
        f"- stop_price {STOPS[t]} -- UNTOUCHED (E39)",
        "",
        "### The g each run used (item 6)",
        "",
        "| | base | bear | bull |", "|---|---:|---:|---:|",
        f"| RESTRIKE-2026-08-26 | {first['g'][0]:.1%} | {first['g'][1]:.1%} | "
        f"{'--' if first['g'][2] is None else f'{first[chr(103)][2]:.1%}'} |",
        f"| this run, from `{g.view_file}` | {g.base:.1%} | {g.bear:.1%} | {g.bull:.1%} |",
        "",
        f"### The delta against {first['fv']:.2f}", "",
        "| step | value | item |", "|---|---:|---|",
    ]
    for label, value, item in delta_rows:
        out.append(f"| {label} | {value:,.2f} | {item} |")
    out += ["", f"<details><summary>the run record</summary>", "",
            s["record"].render(), "", "</details>", ""]
    return "\n".join(out)


def sap_framework_output(s: dict) -> str:
    price, cur = s["price"], s["currency"]
    fv, bull = s["band"].mid, s["bull"]
    vs_fv = price / fv - 1
    vs_bull = price / bull - 1
    bull_gap = bull / price - 1
    trim = price >= fv
    c4_fires = price > bull
    return "\n".join([
        "### SAP.DE -- the framework's own output on the price (NOT a recommendation)",
        "",
        f"- price {price:.2f} vs fv_base {fv:,.2f}: **{vs_fv:+.1%}**"
        + (" -- price is ABOVE fv_base" if vs_fv > 0 else " -- price is BELOW fv_base"),
        f"- price {price:.2f} vs FV_bull {bull:,.2f}: **{vs_bull:+.1%}**"
        + (" -- price is ABOVE the bull case" if vs_bull > 0 else " -- price is BELOW the bull case"),
        f"- **section 6.4, 'At FV_base, trim 25-50%; reassess': {'FIRES' if trim else 'does not fire'}** "
        f"(price {'>=' if trim else '<'} fv_base).",
        f"- **C4, 'exit when even the bull case does not beat the index': "
        f"{'FIRES' if c4_fires else 'does not fire on its MSFT reading'}.** "
        f"Expected return from {price:.2f} to FV_bull {bull:,.2f} is **{bull_gap:+.1%}**; "
        f"the index core's expected return is {CORE_EXPECTED_RETURN:.1%} a year (E29's "
        f"anchor). C4 states no horizon: on the reading applied to MSFT (price above "
        f"FV_bull, expected return negative) it {'fires' if c4_fires else 'does not fire'}; "
        f"read as ONE year against {CORE_EXPECTED_RETURN:.1%}, the bull-case gap is "
        f"{'BELOW' if bull_gap < CORE_EXPECTED_RETURN else 'ABOVE'} the index"
        f"{' and would fire' if bull_gap < CORE_EXPECTED_RETURN and not c4_fires else ''}. "
        f"Which horizon C4 means is the owner's to say.",
        "",
        "*The band across E29's +/-0.5% is printed above; E29 forbids adjudicating on "
        "the fragility, and nothing here does.*",
    ])


def main() -> int:
    sap = strike("SAP.DE", SAP_HAND)
    liab = strike("LIAB.ST")
    RECORDS.mkdir(parents=True, exist_ok=True)
    for s in (sap, liab):
        (RECORDS / f"{s['ticker']}-2026-08-26.json").write_text(
            json.dumps(s["record"].to_dict(), indent=1) + "\n", encoding="utf-8")
    parts = [
        "# Build 2 -- SAP.DE and LIAB.ST re-struck on the TOOL PATH, after the eight rulings of 2026-08-26",
        "",
        f"**{RUN_TS.strftime('%Y-%m-%d %H:%M %Z')}. `config/watchlist.yaml` IS NOT WRITTEN -- "
        "no fv_base, tier or mbp is written; this is a printout and a stop.** The two "
        "section 5 run records are written to `reference/run-records/` so that item 9's "
        "gate can be satisfied by linking them (`run_record:`), which is the owner's write.",
        "",
        f"Tool: `tools/restrike_2026_08_26_b.py` at `{tool_commit()}`. r 9.5% "
        f"(7.0% core + 2.5% premium, E29); terminal 2.5%; 10 explicit years; end-of-year "
        f"discounting (declaration 5).",
        "",
        render(sap, sap_delta(sap) if "band" in sap else []),
        sap_framework_output(sap) if "band" in sap else "",
        "",
        render(liab, liab_delta(liab) if "band" in liab else []),
        "",
        "---",
        "",
        "## What this run does NOT do",
        "",
        "- **It writes nothing to `config/watchlist.yaml`.** fv_base, tier and mbp stay as "
        "item 4 and item 5 left them (null / 1 and 2 / null).",
        "- **It does not link the records.** `run_record:` on each entry, with the fv_base "
        "beside it, is the owner's write; until then `vss run` prints DATA MISSING for "
        "both fair values (item 9), which is the rule working.",
        "- **SAP.DE stands on two HAND inputs** the store cannot hold -- the R12M capex "
        "(four cumulative columns) and the consolidated financial-liabilities line -- "
        "both declared in the record with their pages (E41). Whether either may live in "
        "the store is open.",
        "- **The share counts are E41 fills**: SAP's 1,175m is FY2025's (the interim states "
        "1,163m diluted for H1 2026 and 1,158m for Q2 2026; the R12M average is not "
        "stated), Lindab's 77.036m is FY2025's and equals the R12M average the interim "
        "states. The as-of line says THEY DO NOT AGREE for SAP, and that is inside the number.",
        "",
    ]
    text = "\n".join(parts)
    OUT.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
