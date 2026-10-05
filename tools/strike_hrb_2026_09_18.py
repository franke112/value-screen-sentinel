"""HRB: the section 5 strike, 2026-09-18, on the review of 2026-09-17.

THE GROWTH VIEW IS THE OWNER'S AND WAS REGISTERED FIRST. It is READ FROM
`reference/reviews/HRB/2026-09-17.yaml` -- `growth_view.registered_at`
2026-09-18T20:03:01+02:00, written before this script existed and before
g* was solved anywhere (E28's order). Nothing here re-states the rates: if
the review file changes, this script strikes the changed view or fails.

WHAT IT PRINTS, and it prints the BIASES beside the value rather than under
it: fv_base with E29's band, the bear and bull cases, the basis line, the
full run record with every bridge leg named, g* at the settled close, SBC
as a percentage of FCF0, and MBP as DATA MISSING beside what it WOULD be at
tiers 1-3 against the bear case -- because tier is NOT scored (B22).

THE TWO UPWARD BIASES, on the owner's instruction (review, `strike` step):
E115's interest add-back (interest paid alone, the unstated interest income
missing from it) and the BASIS-YEAR FCF0 (FY2026 free cash flow is above
both prior years). E34 fixes FCF0 to the basis year and permits no
normalisation, so the bias is printed, with the three-year average as a
memo figure and nothing computed off it.

It WRITES TWO THINGS: `reference/HRB-STRIKE-2026-09-18.md` (the printout)
and `reference/run-records/HRB-2026-09-18.json` (the run record). It NEVER
writes fv_base, tier, mbp or stop to config/watchlist.yaml.

    python tools/strike_hrb_2026_09_18.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))   # run as a script
from datetime import date, datetime
from zoneinfo import ZoneInfo

import yaml

from vss import fx
from vss import manual as M
from vss import metrics as MT
from vss import runrecord as R
from vss import valuation as V
from vss.fetch import get_history
from vss.runner import CACHE_DIR, PROJECT_ROOT

TICKER = "HRB"
RUN_TS = datetime.now(ZoneInfo("America/New_York"))
AS_OF = RUN_TS.date()
STAMP = "2026-09-18"
REVIEW = PROJECT_ROOT / "reference" / "reviews" / "HRB" / "2026-09-17.yaml"
RECORDS = PROJECT_ROOT / "reference" / "run-records"
RATE = R.Rate(core_expected_return=0.070, premium=0.025)          # E29's anchor

#: The three-year stated free cash flow (operating cash flow − capex), the
#: memo figure beside the basis year. NOT an input to anything.
FCF_THREE_YEAR = {"FY2026": 756_081_000, "FY2025": 598_849_000, "FY2024": 657_182_000}


def growth_view() -> R.Growth:
    """The owner's pre-registered view, read from the review file (E28)."""
    doc = yaml.safe_load(REVIEW.read_text(encoding="utf-8"))
    gv = doc["growth_view"]
    if gv is None:
        raise SystemExit("HRB's review carries no registered growth view: "
                         "nothing may be struck (E28)")
    stamp = str(gv["registered_at"])
    return R.Growth(base=float(gv["base"]), bear=float(gv["bear"]),
                    bull=float(gv["bull"]),
                    view_file=f"{REVIEW.relative_to(PROJECT_ROOT)} (registered {stamp})",
                    view_date=date.fromisoformat(stamp[:10]))


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
    return f"HRB strike, {STAMP}, {sha}"


def strike() -> dict:
    parsed = M.load_manual(TICKER, directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    gate = M.section5_gate(parsed, as_of=AS_OF)
    growth = growth_view()
    price_minor, price_date = settled_close()
    price = price_minor / fx.minor_unit_divisor(parsed.quote_currency)
    record = R.from_store(parsed, basis, growth=growth, run_ts=RUN_TS,
                          hand_inputs=(), price_date=price_date, rate=RATE,
                          tool_commit=tool_commit())
    out = dict(parsed=parsed, basis=basis, gate=gate, growth=growth, price=price,
               price_date=price_date, record=record, currency=record.currency)
    if not record.complete:
        out["gaps"] = record.missing()
        return out
    legs = record.legs()
    args = dict(fcf0=legs.fcf0, net_cash=legs.net_cash, shares=legs.shares)
    out.update(fcf0=record.fcf0(), legs=legs, band=record.band(),
               bear=record.strike(growth.bear), bull=record.strike(growth.bull),
               base=record.strike(growth.base),
               implied=V.implied_growth(price=price, rate=RATE.rate, **args),
               # E90: MBP is the BASE-case value x the tier cushion, across
               # E29's band. The bear case stays printed as information.
               mbp_by_tier={t: V.maximum_buy_price(g_base=growth.base, tier=t,
                                                   rate=RATE.rate, **args)
                            for t in (1, 2, 3)})
    return out


def report(s: dict) -> str:
    L = [f"# HRB — section 5 strike, {STAMP}", "",
         f"**Basis:** {s['basis'].label}. **Price:** {s['price']:,.2f} "
         f"{s['currency']} settled {s['price_date']}.", ""]
    gv = s["growth"]
    L += [f"**The pre-registered view (E28), read from `{REVIEW.relative_to(PROJECT_ROOT)}`:** "
          f"bear {gv.bear:+.2%}, base {gv.base:+.2%}, bull {gv.bull:+.2%}, "
          f"registered {gv.view_file}.", ""]
    if "gaps" in s:
        return "\n".join(L + ["## NOTHING IS STRUCK", ""] +
                         [f"- {g}" for g in s["gaps"]] + [""])
    band = s["band"]
    L += ["## THE VALUE", "",
          f"- **fv_base: {s['base']:,.2f} {s['currency']}** at g {gv.base:+.2%}, "
          f"r {RATE.rate:.2%}",
          f"- E29 band (r ±0.5%): {band.high:,.2f} – {band.low:,.2f} "
          f"(mid {band.mid:,.2f})",
          f"- bear case ({gv.bear:+.2%}): {s['bear']:,.2f}",
          f"- bull case ({gv.bull:+.2%}): {s['bull']:,.2f}",
          f"- **g\\* at {s['price']:,.2f}: {s['implied']:+.2%}** — the growth the "
          f"market is paying for",
          f"- FCF0: {s['fcf0']:,.0f} {s['currency']}",
          f"- SBC as a share of FCF0: {s['parsed'] and ''}"
          f"{abs(M.resolve_on_basis(s['parsed'], s['basis'], 'sbc').value or 0) / abs(s['fcf0']):.1%}",
          ""]
    L += ["## THE TWO UPWARD BIASES, PRINTED BESIDE THE VALUE", "",
          "**Both inflate fv_base and understate g\\*. The owner registered his "
          "reading rule before this ran: a margin of safety that depends on the "
          "last ~11% is not a margin.**", "",
          "1. **E115, the interest add-back.** FCF0 adds back interest PAID ALONE "
          f"({M.resolve_on_basis(s['parsed'], s['basis'], 'finance_costs_paid').value:,.0f}), "
          "because this filer states no interest received anywhere in the filing "
          "or the taxonomy. Interest income is never negative, so FCF0 is "
          "overstated by the unstated income, never understated. The only "
          "container it could sit in is *Other income (expense), net* = "
          "26,813,000, itself an aggregate of undisclosed composition — a ceiling "
          "on the visible container, not a bound on the amount.",
          "2. **The basis year is the high year.** Stated free cash flow "
          "(operating cash flow − capex): "
          + ", ".join(f"{k} {v/1e6:,.1f}m" for k, v in FCF_THREE_YEAR.items())
          + f". **Three-year average {sum(FCF_THREE_YEAR.values())/3/1e6:,.1f}m, "
            f"{1 - (sum(FCF_THREE_YEAR.values())/3) / FCF_THREE_YEAR['FY2026']:.1%} "
            "below the basis year** — a MEMO FIGURE, nothing is computed off it. "
            "The 10-K attributes the rise to *\"higher net income, accrued wages "
            "and deferred revenue, partially offset by the release of income tax "
            "reserves associated with the settlement of the IRS examination\"*, so "
            "part of it is working capital, **which cannot be assumed to recur**. "
            "E34 fixes FCF0 to the basis year and permits no normalisation "
            "(E19, E20, E22, and E112's refusal of a normalised basis), so the "
            "value is struck on FY2026 and the bias is printed rather than fixed.",
          "", "**Net debt is also overstated by 19,195,000** — restricted cash is "
          "left out of cash, on the owner's instruction, no stated purpose having "
          "been found in the filing. That bias runs the other way, against the "
          "value.", ""]
    L += ["## MBP — DATA MISSING (B22: no tier is scored)", ""]
    for tier, mbp in s["mbp_by_tier"].items():
        L += [f"- at tier {tier}: {mbp.mid:,.2f} {s['currency']} "
              f"(band {mbp.high:,.2f} – {mbp.low:,.2f})"]
    L += ["", "*None of these is the MBP. Tier is the owner's, at the next step.*", "",
          "## THE RUN RECORD", "", s["record"].sentence() if hasattr(s["record"], "sentence")
          else "", ""]
    return "\n".join(L)


def main() -> int:
    RECORDS.mkdir(parents=True, exist_ok=True)
    s = strike()
    if "record" in s and s["record"].complete:
        (RECORDS / f"{TICKER}-{STAMP}.json").write_text(
            json.dumps(s["record"].to_dict(), indent=1) + "\n", encoding="utf-8")
    text = report(s)
    (PROJECT_ROOT / "reference" / f"{TICKER}-STRIKE-{STAMP}.md").write_text(
        text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
