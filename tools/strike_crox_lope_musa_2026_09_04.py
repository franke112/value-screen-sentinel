"""CROX, LOPE and MUSA: first section 5 strikes, 2026-09-04.

The growth views are `reference/growth-views/CROX.md`, `LOPE.md` and
`MUSA.md`, pre-registered by the owner on 2026-09-04 in his own words --
BEFORE this script ran and before any implied growth was solved (E28) --
and carried in a machine-readable `growth:` block on each watchlist entry
under E109. **This script reads them off the watchlist rather than holding
a copy**, which is what E109 was for: until today every strike tool
hard-coded its own transcription of a number that lived in prose.

MUSA was tested against E96 FIRST -- `reference/E96-TEST-MUSA-2026-09-04.md`
-- because the owner had described it as oil and gas. It is OUTSIDE: the
world price is its COST and it sets its own retail price daily, which is
E96's mechanism inverted, and E96 already carves out "marketing margins
that move against the crude price" by name.

It WRITES TWO THINGS PER NAME ONLY: `reference/<TICKER>-STRIKE-2026-09-04.md`
and `reference/run-records/<TICKER>-2026-09-04.json`. It NEVER writes
fv_base, tier or mbp to config/watchlist.yaml -- these are INTAKE names
(E111) and the owner's write is what moves them.

    python tools/strike_crox_lope_musa_2026_09_04.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
from datetime import date, datetime
from zoneinfo import ZoneInfo

from vss import fx
from vss import manual as M
from vss import metrics as MT
from vss import runrecord as R
from vss import valuation as V
from vss.config import load_watchlist
from vss.fetch import get_history
from vss.runner import CACHE_DIR, PROJECT_ROOT, WATCHLIST_PATH

RUN_TS = datetime.now(ZoneInfo("America/New_York"))
STAMP = "2026-09-04"
AS_OF = date(2026, 9, 4)
RATE = R.Rate(core_expected_return=0.070, premium=0.025)
NAMES = ("CROX", "LOPE", "MUSA")

ENTRIES = {e.ticker: e for e in load_watchlist(WATCHLIST_PATH)}


def growth_view(ticker: str) -> R.Growth:
    """E109: the view OFF THE WATCHLIST, never a copy held here."""
    view = ENTRIES[ticker].growth
    if view is None:
        raise SystemExit(f"{ticker}: no growth view is registered on the "
                         f"watchlist entry. E28 forbids striking without one, "
                         f"and this tool will not invent it.")
    return R.Growth(base=view.base, bear=view.bear, bull=view.bull,
                    view_file=view.view, view_date=view.registered)


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
    return f"CROX/LOPE/MUSA first strikes, {STAMP}, {sha}"


def strike(ticker: str) -> dict:
    parsed = M.load_manual(ticker, directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    gate = M.section5_gate(
        parsed, as_of=AS_OF,
        measured_exempt=M.registered_view_sensitivity(parsed),
        tolerance=(lambda t: (t[0], t[2]))(
            M.registered_view_record(parsed).tolerance())
        if M.registered_view_record(parsed) is not None else None)
    growth = growth_view(ticker)
    price_minor, price_date = settled_close(ticker)
    price = price_minor / fx.minor_unit_divisor(parsed.quote_currency)
    record = R.from_store(parsed, basis, growth=growth, run_ts=RUN_TS,
                          hand_inputs=(), price_date=price_date, rate=RATE,
                          tool_commit=tool_commit())
    out = dict(ticker=ticker, parsed=parsed, basis=basis, gate=gate,
               growth=growth, price=price, price_date=price_date,
               record=record, currency=record.currency)
    if not record.complete:
        out["gaps"] = record.missing()
        return out
    legs = record.legs()
    args = dict(fcf0=legs.fcf0, net_cash=legs.net_cash, shares=legs.shares)
    out.update(
        legs=legs, fcf0=record.fcf0(), band=record.band(),
        bear=record.strike(growth.bear), bull=record.strike(growth.bull),
        implied=V.implied_growth(price=price, rate=RATE.rate, **args),
        # E90 (2026-08-30): the MBP is the BASE-case value times the tier
        # cushion, NOT the bear case -- the cushion covers model and input
        # error, and the pre-registered views carry scenario risk. The bear
        # and bull values stay printed above as information.
        mbp_by_tier={tier: V.maximum_buy_price(g_base=growth.base, tier=tier,
                                               rate=RATE.rate, **args)
                     for tier in (1, 2, 3)})
    return out


def report(s: dict) -> str:
    t, cur = s["ticker"], s["currency"]
    view = ENTRIES[t].growth
    lines = [
        f"# {t} — section 5 strike, {STAMP}",
        "",
        f"**Growth view registered {view.registered.isoformat()} by the owner, "
        f"in his own words, BEFORE this ran (E28).** bear {view.bear:.0%} / "
        f"base {view.base:.0%} / bull {view.bull:.0%}, from `{view.view}` and "
        f"read off the watchlist entry (E109).",
        "",
        f"Basis `{s['basis'].label}`, ending {s['basis'].end.isoformat()}. "
        f"Rate {RATE.rate:.1%} ({RATE.core_expected_return:.1%} core + "
        f"{RATE.premium:.1%} premium). Settled close "
        f"{s['price']:,.2f} {cur} on {s['price_date'].isoformat()}.",
        "",
    ]
    if "gaps" in s:
        lines += ["## NO FAIR VALUE IS PRINTED", "",
                  "The record is INCOMPLETE and section 5 does not strike from "
                  "one. Absent:", ""]
        lines += [f"- {gap}" for gap in s["gaps"]]
        return "\n".join(lines) + "\n"
    band, legs = s["band"], s["legs"]
    lines += [
        "## The value", "",
        f"| | {cur} |", "|---|---:|",
        f"| **fv_base** (g {view.base:.0%}) | **{band.mid:,.2f}** |",
        f"| E29 band, low (g {view.base:.0%} − 0.5pp) | {band.low:,.2f} |",
        f"| E29 band, high (g {view.base:.0%} + 0.5pp) | {band.high:,.2f} |",
        f"| FV_bear (g {view.bear:.0%}) | {s['bear']:,.2f} |",
        f"| FV_bull (g {view.bull:.0%}) | {s['bull']:,.2f} |",
        "",
        "## What the price implies", "",
        f"- settled close **{s['price']:,.2f} {cur}** on "
        f"{s['price_date'].isoformat()}",
        f"- **g\\*, the growth the price implies at r {RATE.rate:.1%}: "
        f"{s['implied']:.2%}** — against the owner's registered base of "
        f"{view.base:.0%}",
        f"- price vs fv_base: **{s['price'] / band.mid - 1:+.1%}**",
        f"- price vs FV_bear: **{s['price'] / s['bear'] - 1:+.1%}**",
        f"- price vs FV_bull: **{s['price'] / s['bull'] - 1:+.1%}**",
        "",
        "## The legs", "",
        f"- FCF0 **{legs.fcf0:,.0f} {cur}**",
        f"- net {'cash' if legs.net_cash >= 0 else 'debt'} "
        f"**{abs(legs.net_cash):,.0f} {cur}**",
        f"- divisor **{legs.shares:,.0f}** shares — {s['record'].shares.basis}",
        "",
        "## NO MBP, and that is E111 and B22 rather than an omission", "",
        "This name is **INTAKE**: read, not watched. It carries no tier, and "
        "`compute_mbp` is `fv_base` × the tier multiplier — so **no maximum "
        "buy price exists and none is written here.** What the MBP *would* be "
        "at each tier (E90's cushion on the BASE case) is printed so the "
        "owner sees the range before scoring; **none of them is the MBP.**",
        "",
        "| tier | MBP would be |", "|---|---:|",
    ]
    for tier, mbp in s["mbp_by_tier"].items():
        lines.append(f"| {tier} | {mbp.mid:,.2f} {cur} |")
    lines += ["", "## The run record", "",
              f"`reference/run-records/{t}-{STAMP}.json` — every leg, every "
              f"page, zero hand inputs.", ""]
    return "\n".join(lines) + "\n"


def main() -> int:
    out = PROJECT_ROOT / "reference"
    (out / "run-records").mkdir(parents=True, exist_ok=True)
    struck = []
    for ticker in NAMES:
        s = strike(ticker)
        (out / f"{ticker}-STRIKE-{STAMP}.md").write_text(report(s),
                                                         encoding="utf-8")
        if "gaps" not in s:
            (out / "run-records" / f"{ticker}-{STAMP}.json").write_text(
                json.dumps(s["record"].to_dict(), indent=2, default=str) + "\n",
                encoding="utf-8")
            struck.append(s)
            print(f"{ticker:<6} fv_base {s['band'].mid:>10,.2f} "
                  f"bear {s['bear']:>10,.2f} bull {s['bull']:>10,.2f}  "
                  f"price {s['price']:>9,.2f}  g* {s['implied']:>7.2%}  "
                  f"vs fv {s['price'] / s['band'].mid - 1:>+7.1%}")
        else:
            print(f"{ticker:<6} NO FAIR VALUE: {'; '.join(s['gaps'])[:90]}")
    return 0 if len(struck) == len(NAMES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
