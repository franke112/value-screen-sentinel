"""BOUV.OL: the section 5 arithmetic, 2026-09-08. NOT A CLEAN STRIKE.

The growth view is `reference/growth-views/BOUV.OL.md`, pre-registered by
the owner on 2026-09-08 in his own words -- BEFORE this script ran and
before any implied growth was solved (E28). The registration commit
predates this file, and that ordering is the record.

**READ ON: THE SECTION 5 GATE REFUSES THIS NAME, AND THE OWNER ASKED FOR
THE NUMBERS ANYWAY.** `config/manual/BOUV.OL.yaml` was built this morning
from five PDFs and **every figure in it is UNVERIFIED (E40)** -- no
read-back against a rendered page has happened. `section5_gate` returns
**53 refusals**, 52 of them `UNVERIFIED` and one `PERIODS DO NOT MATCH`
(2026-Q1's contested EBITDA, which no section 5 leg reads). E21 refuses
section 5 on an UNVERIFIED figure the current basis reads, and it is right
to.

So what this script prints is **the arithmetic of section 5 run on an
unverified store at the owner's instruction.** It is not a struck fair
value and it is NOT E94's INDICATIVE value either -- E94's second fence is
"every figure the basis reads VERIFIED under E40", and that fence fails.
**Seven read-backs would make it a strike**, and they are named in
`reference/INTAKE-BOUV.OL-2026-09-08.md` section 3. Every figure this
script prints carries the label PROVISIONAL for that reason.

**E109 AND WHY THE VIEW IS NOT READ OFF THE WATCHLIST.** Every strike tool
since 2026-09-04 reads the `growth:` block off `config/watchlist.yaml`,
because that is where E109 put it. **BOUV.OL has no watchlist entry**, and
E109 ruled that case the day it was written: five names with registered
views are not watchlist entries and were LEFT there, because entering a
name stamps `dd_at_entry` and freezes Gate 1 under E12. BOUV.OL is the
sixth. This script therefore reads the view through
`readiness.read_growth_view`, which parses the view FILE -- and says so on
its face rather than quietly diverging from its predecessors.

IT WRITES TWO THINGS AND NOTHING ELSE:
`reference/BOUV.OL-STRIKE-2026-09-08.md` and
`reference/run-records/BOUV.OL-2026-09-08.json`. **It never touches
`config/watchlist.yaml`** -- BOUV.OL is INTAKE (E111), the owner said the
watchlist write is his, and `assert_no_watchlist_write` holds this file to
it mechanically rather than on the author's word.

    python tools/strike_bouv_2026_09_08.py
"""

from __future__ import annotations

import hashlib
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
from vss.fetch import get_history
from vss.readiness import read_growth_view
from vss.runner import CACHE_DIR, PROJECT_ROOT, WATCHLIST_PATH

RUN_TS = datetime.now(ZoneInfo("Europe/Oslo"))
STAMP = "2026-09-08"
AS_OF = date(2026, 9, 8)
TICKER = "BOUV.OL"
RATE = R.Rate(core_expected_return=0.070, premium=0.025)

#: The close last night's run reported for this name, and it is NOT what the
#: vendor serves this morning. See `price_note` -- reported, never used.
LAST_RUN_CLOSE = 49.25
LAST_RUN_DATE = date(2026, 9, 7)


def watchlist_digest() -> str:
    return hashlib.sha256(WATCHLIST_PATH.read_bytes()).hexdigest()


def growth_view() -> R.Growth:
    """E28's view, off the FILE. See the module docstring for why not E109's
    watchlist block."""
    view = read_growth_view(TICKER)
    if view is None or not view.registered:
        raise SystemExit(
            f"{TICKER}: no registered growth view. E28 forbids striking "
            f"without one and this tool will not invent it. "
            f"({'no file' if view is None else view.detail})")
    return R.Growth(base=view.base, bear=view.bear, bull=view.bull,
                    view_file=str(view.path.relative_to(PROJECT_ROOT)),
                    view_date=date(2026, 9, 8))


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
    return f"BOUV.OL provisional section 5 arithmetic, {STAMP}, {sha}"


def strike() -> dict:
    parsed = M.load_manual(TICKER, directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    # E108's measured limb, fixed 2026-09-08: the map is now keyed in the
    # STORE's field names and reads the view FILE where E109 left a name
    # off the watchlist, so the gate can grant what E108's words allow.
    measured = M.registered_view_sensitivity(parsed)
    gate = M.section5_gate(parsed, as_of=AS_OF, measured_exempt=measured)
    growth = growth_view()
    price_minor, price_date = settled_close()
    price = price_minor / fx.minor_unit_divisor(parsed.quote_currency)
    record = R.from_store(parsed, basis, growth=growth, run_ts=RUN_TS,
                          hand_inputs=(), price_date=price_date, rate=RATE,
                          tool_commit=tool_commit())
    out = dict(ticker=TICKER, parsed=parsed, basis=basis, gate=gate,
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
        # E29 forbids reporting a middle alone, and g* is as much a
        # function of r as the value is. Same band, same reason.
        implied_band=tuple(
            V.implied_growth(price=price, rate=r, **args)
            for r in (RATE.rate - RATE.band, RATE.rate, RATE.rate + RATE.band)),
        implied_last_run=V.implied_growth(price=LAST_RUN_CLOSE,
                                          rate=RATE.rate, **args),
        checks=record.construction_checks(),
        mbp_by_tier={tier: V.maximum_buy_price(g_base=growth.base, tier=tier,
                                               rate=RATE.rate, **args)
                     for tier in (1, 2, 3)})
    return out


def report(s: dict) -> str:
    cur = s["currency"]
    g = s["growth"]
    gate = s["gate"]
    unverified = [r for r in gate.refusals if r.kind == "UNVERIFIED"]
    lines = [
        f"# BOUV.OL — section 5 arithmetic, {STAMP} — **PROVISIONAL**",
        "",
        "## THE GATE REFUSES THIS NAME, AND EVERY FIGURE BELOW IS PROVISIONAL",
        "",
        f"`section5_gate` returns **{len(gate.refusals)} refusals**, "
        f"**{len(unverified)}** of them `UNVERIFIED`. The store was built "
        f"this morning from five PDFs and **not one figure has been read "
        f"back against a rendered page (E40)**. E21 refuses section 5 on an "
        f"UNVERIFIED figure the basis reads, and it is right to.",
        "",
        "**So this is not a struck fair value.** It is the arithmetic of "
        "section 5, run on an unverified store at the owner's instruction. "
        "It is not E94's INDICATIVE value either — E94's second fence is "
        "*every figure the basis reads VERIFIED under E40*, and that fence "
        "fails. **Seven read-backs would make it a strike**, and they are "
        "named in `reference/INTAKE-BOUV.OL-2026-09-08.md` §3.",
        "",
        f"**Growth view registered {g.view_date.isoformat()} by the owner, in "
        f"his own words, BEFORE this ran (E28).** bear {g.bear:.0%} / base "
        f"{g.base:.0%} / bull {g.bull:.0%}, from `{g.view_file}`. **Read off "
        f"the FILE and not off a watchlist `growth:` block (E109)**: BOUV.OL "
        f"has no watchlist entry and E109 ruled that case — entering a name "
        f"stamps `dd_at_entry` and freezes Gate 1 under E12.",
        "",
        f"Basis `{s['basis'].label}`, ending {s['basis'].end.isoformat()}. "
        f"Rate {RATE.rate:.1%} ({RATE.core_expected_return:.1%} core + "
        f"{RATE.premium:.1%} premium, E29). Settled close "
        f"{s['price']:,.2f} {cur} on {s['price_date'].isoformat()}.",
        "",
    ]
    if "gaps" in s:
        lines += ["## NO VALUE IS PRINTED", "",
                  "The record is INCOMPLETE and nothing is computed from one. "
                  "Absent:", ""]
        lines += [f"- {gap}" for gap in s["gaps"]]
        return "\n".join(lines) + "\n"
    band, legs = s["band"], s["legs"]
    lines += [
        "## The value — PROVISIONAL", "",
        f"| | {cur} |", "|---|---:|",
        f"| **fv_base** (g {g.base:.0%}) | **{band.mid:,.2f}** |",
        f"| E29 band, low — r {RATE.rate - RATE.band:.1%} | {band.low:,.2f} |",
        f"| E29 band, high — r {RATE.rate + RATE.band:.1%} | {band.high:,.2f} |",
        f"| FV_bear (g {g.bear:.0%}) | {s['bear']:,.2f} |",
        f"| FV_bull (g {g.bull:.0%}) | {s['bull']:,.2f} |",
        "",
        f"**E29 forbids reporting the middle alone**, and the band above is "
        f"why: half a point of r moves this value by "
        f"{band.spread:,.2f} {cur}, "
        f"{band.spread / band.mid:.1%} of fv_base.",
        "",
        "## What the price implies", "",
        f"- settled close **{s['price']:,.2f} {cur}** on "
        f"{s['price_date'].isoformat()}",
        f"- **g\\*, the growth the price implies at r {RATE.rate:.1%}: "
        f"{s['implied']:.2%}** — against the owner's registered base of "
        f"{g.base:.0%}",
        f"- price vs fv_base: **{s['price'] / band.mid - 1:+.1%}**",
        f"- price vs FV_bear: **{s['price'] / s['bear'] - 1:+.1%}**",
        f"- price vs FV_bull: **{s['price'] / s['bull'] - 1:+.1%}**",
        "",
        f"**g\\* ACROSS E29's BAND, because the middle alone is not "
        f"reportable here either:** r {RATE.rate - RATE.band:.1%} → "
        f"**{s['implied_band'][0]:.2%}**, r {RATE.rate:.1%} → "
        f"**{s['implied_band'][1]:.2%}**, r {RATE.rate + RATE.band:.1%} → "
        f"**{s['implied_band'][2]:.2%}**. **At every rate in the band the "
        f"price implies more growth than the owner's BULL case of "
        f"{g.bull:.0%}.**",
        "",
        "### A price note, reported and not used", "",
        f"The nightly run of {LAST_RUN_DATE.isoformat()} reported a settled "
        f"close of **{LAST_RUN_CLOSE:,.2f}** for this name. The vendor now "
        f"serves that bar with its Open, High, Low and Volume intact and its "
        f"**Close as NaN**, so `metrics.compute` falls back to "
        f"{s['price_date'].isoformat()} and this run is struck on "
        f"{s['price']:,.2f}. At {LAST_RUN_CLOSE:,.2f} the implied growth "
        f"would be **{s['implied_last_run']:.2%}** instead of "
        f"{s['implied']:.2%}. Nothing is adjusted; both are printed.",
        "",
        "## The legs", "",
        f"- FCF0 **{legs.fcf0:,.0f} {cur}**",
        f"- net {'cash' if legs.net_cash >= 0 else 'debt'} "
        f"**{abs(legs.net_cash):,.0f} {cur}**",
        f"- divisor **{legs.shares:,.0f}** shares — {s['record'].shares.basis}",
        "",
    ]
    lines += s["record"].render_construction_checks()
    lines += [
        "",
        "## NO MBP, and that is E111 and B22 rather than an omission", "",
        "This name is **INTAKE**: read, not watched. It carries no tier, and "
        "the MBP is `fv_base` × the tier cushion — so **no maximum buy price "
        "exists and none is written here.** What it *would* be at each tier "
        "(E90's cushion on the BASE case) is printed so the owner sees the "
        "range before scoring; **none of them is the MBP, and all of them "
        "inherit this page's PROVISIONAL label.**",
        "",
        "| tier | MBP would be |", "|---|---:|",
    ]
    for tier, mbp in s["mbp_by_tier"].items():
        lines.append(f"| {tier} | {mbp.mid:,.2f} {cur} |")
    lines += [
        "", "## What was written", "",
        f"`reference/BOUV.OL-STRIKE-{STAMP}.md` (this file) and "
        f"`reference/run-records/BOUV.OL-{STAMP}.json` — every leg, every "
        f"page, zero hand inputs. **`config/watchlist.yaml` was not touched**, "
        f"and this script asserts its SHA-256 is unchanged before it exits.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    before = watchlist_digest()
    out = PROJECT_ROOT / "reference"
    (out / "run-records").mkdir(parents=True, exist_ok=True)
    s = strike()
    (out / f"BOUV.OL-STRIKE-{STAMP}.md").write_text(report(s), encoding="utf-8")
    if "gaps" in s:
        print("BOUV.OL: record INCOMPLETE, no value printed")
        for gap in s["gaps"]:
            print("   ", gap)
    else:
        (out / "run-records" / f"BOUV.OL-{STAMP}.json").write_text(
            json.dumps(s["record"].to_dict(), indent=2, default=str) + "\n",
            encoding="utf-8")
        print(f"BOUV.OL fv_base {s['band'].mid:>9,.2f} "
              f"(band {s['band'].low:,.2f}/{s['band'].high:,.2f})  "
              f"bear {s['bear']:>8,.2f}  bull {s['bull']:>8,.2f}  "
              f"price {s['price']:>7,.2f}  g* {s['implied']:>7.2%}  "
              f"vs fv {s['price'] / s['band'].mid - 1:>+7.1%}")
        print(f"       PROVISIONAL: section5_gate returns "
              f"{len(s['gate'].refusals)} refusals, "
              f"{sum(1 for r in s['gate'].refusals if r.kind == 'UNVERIFIED')} "
              f"UNVERIFIED")
    after = watchlist_digest()
    if before != after:
        raise SystemExit("config/watchlist.yaml CHANGED. This tool must never "
                         "write it; the change is a bug and is not committed.")
    print("       config/watchlist.yaml unchanged (sha256 " + before[:12] + "…)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
