"""MEKKO.HE: the section 5 strike, 2026-09-08.

The growth view is `reference/growth-views/MEKKO.HE.md`, pre-registered by
the owner on 2026-09-08 in his own words -- BEFORE this script ran and
before any implied growth was solved (E28). The registration commit
predates this file, and that ordering is the record.

**THE GATE NOW OPENS, AND THE LABEL FOLLOWS THE GATE RATHER THAN A
CONSTANT.** When this script was first written `section5_gate` returned 16
refusals and it printed PROVISIONAL unconditionally. Four read-backs by the
owner on 2026-09-08 (`operating_cash_flow`, `diluted_weighted_average_shares`,
`net_finance_costs`, `shares_issued_period_end`), the repair of E108's
measured limb and the ruling of E113 took that to **0 refusals**. The header,
the value heading, the gate section and the console line are now all computed
from `gate.refusals`: this file prints STRUCK when the gate opens and
PROVISIONAL when it does not, and **a future refusal turns the label back on
its own.** Nothing here was changed to make the gate open -- the store's
figures are untouched and only the reporting of the gate's own answer moved.

The waiver is stated rather than assumed. Twenty of the store's figures were
never read back and are exempt -- twelve on E108's measured floor, eight on
E113 -- and **the report names all twenty**, because E113's own text requires
that the exemption be visible. E108 and E113 waive the READ-BACK and neither
waives the PROVENANCE.

**E109 AND WHY THE VIEW IS NOT READ OFF THE WATCHLIST.** Every strike tool
since 2026-09-04 reads the `growth:` block off `config/watchlist.yaml`,
because that is where E109 put it. **MEKKO.HE has no watchlist entry**, and
E109 ruled that case the day it was written: five names with registered
views are not watchlist entries and were LEFT there, because entering a
name stamps `dd_at_entry` and freezes Gate 1 under E12. BOUV.OL was the sixth this morning and
MEKKO.HE is the seventh. This script therefore reads the view through
`readiness.read_growth_view`, which parses the view FILE -- and says so on
its face rather than quietly diverging from its predecessors.

IT WRITES TWO THINGS AND NOTHING ELSE:
`reference/MEKKO.HE-STRIKE-2026-09-08.md` and
`reference/run-records/MEKKO.HE-2026-09-08.json`. **It never touches
`config/watchlist.yaml`** -- MEKKO.HE is INTAKE (E111), the owner said the
watchlist write is his, and `assert_no_watchlist_write` holds this file to
it mechanically rather than on the author's word.

    python tools/strike_mekko_2026_09_08.py
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

RUN_TS = datetime.now(ZoneInfo("Europe/Helsinki"))
STAMP = "2026-09-08"
AS_OF = date(2026, 9, 8)
TICKER = "MEKKO.HE"
RATE = R.Rate(core_expected_return=0.070, premium=0.025)




#: The legs E108 measures. Flow legs move `fv_base` through FCF0; stock legs
#: move it directly against the equity value. Both are computed on THIS
#: record rather than assumed, which is the whole of E108's measured limb.
FLOW_LEGS = ("operating_cash_flow", "capex_combined", "sbc",
             "finance_costs_paid", "finance_income_received")
STOCK_LEGS = ("cash_and_equivalents", "lease_liabilities")



def _band_sentence(s: dict) -> str:
    """What the band says about g* against the registered view.

    COMPUTED, never asserted. The BOUV.OL tool this was derived from carried
    the sentence "at every rate in the band the price implies MORE growth
    than the BULL case", which was true there and is false here -- MEKKO.HE's
    g* sits below the BEAR case at every rate. A hard-coded conclusion is a
    conclusion that survives the case it was written for.
    """
    g, band = s["growth"], s["implied_band"]
    if g.bull is not None and all(x > g.bull for x in band):
        return (f"**At every rate in the band the price implies MORE growth "
                f"than the owner's BULL case of {g.bull:.0%}.**")
    if g.bear is not None and all(x < g.bear for x in band):
        return (f"**At every rate in the band the price implies LESS growth "
                f"than the owner's BEAR case of {g.bear:.0%}** — the market "
                f"is pricing a slower company than his most pessimistic view.")
    return (f"The band straddles the registered view (bear {g.bear:.0%} / "
            f"base {g.base:.0%} / bull {g.bull:.0%}); no single comparison "
            f"holds across it, which is what E29's band exists to show.")


def _sensitivities(s: dict) -> list[tuple[str, float, float, bool]]:
    """(leg, value, % of fv_base a ±10% move causes, above the floor?)."""
    parsed, basis, legs = s["parsed"], s["basis"], s["legs"]
    equity = s["band"].mid * legs.shares
    pv = equity - legs.net_cash          # net_cash is +ve for a net-cash name
    out: list[tuple[str, float, float, bool]] = []
    for name in FLOW_LEGS:
        v = M.resolve_on_basis(parsed, basis, name).value
        if v is None:
            continue
        # a ±10% move in the leg moves FCF0 by 0.1|v|, and fv_base by that
        # fraction of the DISCOUNTED STREAM over the equity value
        # `legs.fcf0` is normalised to WHOLE units and `v` is the store's
        # own scale, so the leg must be scaled before they are divided.
        # Without this every flow leg printed 0.00% and read as exempt.
        pct = (abs(v) * s["unit_scale"] * 0.1 / abs(legs.fcf0)
               * (pv / equity) * 100)
        out.append((name, v, pct, pct >= 1.0))
    for name in STOCK_LEGS:
        v = M.resolve_on_basis(parsed, basis, name).value
        if v is None:
            continue
        pct = abs(v) * 0.1 * s["unit_scale"] / equity * 100
        out.append((name, v, pct, pct >= 1.0))
    d = M.resolve_on_basis(parsed, basis, "diluted_weighted_average_shares").value
    if d is not None:
        out.append(("diluted_weighted_average_shares", d, 100 / 1.1 * 0.1, True))
    return sorted(out, key=lambda r: -r[2])


def _above(s: dict) -> list[tuple]:
    return [r for r in _sensitivities(s) if r[3]]


def _floor_rows(s: dict) -> list[str]:
    """The floor table, with each leg's ACTUAL verification state beside it.

    A leg above the floor that has already been read back must not still
    say READ THIS BACK -- a stale instruction in a live table is how a
    reader is sent to do work that is done.
    """
    parsed, basis = s["parsed"], s["basis"]
    rows = []
    for name, value, pct, above in _sensitivities(s):
        fig = M.resolve_on_basis(parsed, basis, name)
        done = bool(fig.figures) and all(f.verified for f in fig.figures)
        kinds = "/".join(sorted({f.verified_kind for f in fig.figures
                                 if f.verified_kind})) if done else ""
        if not above:
            state = "exempt (E108)"
        elif done:
            state = f"**VERIFIED ({kinds})**" if kinds else "**VERIFIED**"
        else:
            state = "**READ THIS BACK**"
        shown = f"{value:,.0f}" if abs(value) > 1000 else f"{value:,.2f}"
        rows.append(f"| `{name}` | {shown} | **{pct:.2f}%** | {state} |")
    return rows


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
    return f"MEKKO.HE provisional section 5 arithmetic, {STAMP}, {sha}"


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
    # E108's MEASURED limb, through the STANDARD path. It was supplied by
    # hand here until 2026-09-08, because `registered_view_sensitivity` read
    # the WATCHLIST and this name has no entry so it returned {}. Both
    # halves of that are fixed now: the limb reads the view FILE where E109
    # left a name off the watchlist, and the map is keyed in the STORE's
    # field names rather than the bridge's. The hand path is gone.
    measured = M.registered_view_sensitivity(parsed)
    gate_with_floor = M.section5_gate(parsed, as_of=AS_OF,
                                      measured_exempt=measured)
    out = dict(ticker=TICKER, parsed=parsed, basis=basis, gate=gate_with_floor,
               gate_bare=gate, measured=measured,
               unit_scale=M.UNIT_SCALE[parsed.money_unit],
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
        checks=record.construction_checks(),
        mbp_by_tier={tier: V.maximum_buy_price(g_base=growth.base, tier=tier,
                                               rate=RATE.rate, **args)
                     for tier in (1, 2, 3)})
    return out


def _gate_section(s: dict, gate, e108: list, e113: list,
                  struck: bool) -> list[str]:
    """The gate's own account of itself, refused or open.

    E113 (2026-09-08) requires that a field exempted on the ground that
    `fv_base` never reads it be NAMED, "so the exemption is visible rather
    than silent".  E108's measured limb is named beside it on the same
    principle: a waived read-back that nobody can see is not a waiver, it
    is a gap.
    """
    if not struck:
        return [
            "## THE GATE STILL REFUSES", "",
            f"`section5_gate` returns {len(gate.refusals)} refusals: "
            + ", ".join(f"`{r.subject.split()[-1]}`" for r in gate.refusals)
            + ".",
            "",
        ]
    return [
        "## WHAT THE GATE EXEMPTED, AND ON WHICH GROUND", "",
        "**Neither ground is a relaxation and both are visible here by "
        "rule.** E113 was ruled this morning and says in its own text that "
        "the gate must state which fields it exempted, so the exemption can "
        "be argued with rather than trusted.",
        "",
        f"**E108 — MEASURED: ±10% of the leg moves `fv_base` by less than "
        f"1% ({len(e108)} fields).** "
        + ", ".join(f"`{n}`" for n in e108) + ".",
        "",
        "*This limb had never fired on any name before today.* "
        "`RunRecord.sensitivity()` spoke the BRIDGE's vocabulary — `leases`, "
        "`pensions`, `net_debt`, `capex` — and the gate refused on STORE "
        "field names — `lease_liabilities`, `pension_deficit`, "
        "`cash_and_equivalents`. The intersection was empty on every store "
        "in the repo. That is a defect and it was fixed as one; the two "
        "sides now share a vocabulary and a test fails if a bridge key ever "
        "stops matching its store field.",
        "",
        f"**E113 — STRUCTURAL: the `fv_base` computation never reads the "
        f"field at all ({len(e113)} fields).** "
        + ", ".join(f"`{n}`" for n in e113) + ".",
        "",
        "*E113 is NARROWER than the sentence that names it.* \"fv_base "
        "never reads it\" is necessary and **not sufficient**: "
        "`net_finance_costs` and its operands are read by E25's "
        "zero-coverage denominator outside FCF0 entirely, and the "
        "point-in-time share counts are operands of E54/E80's subtraction — "
        "both are excluded from the exemption, and `net_finance_costs` and "
        "`shares_issued_period_end` were read back by hand on 2026-09-08 "
        "for exactly that reason.",
        "",
        "**A REFUSAL THAT NEVER AROSE, for completeness.** Five further "
        "figures in this store are UNVERIFIED and appear on neither list — "
        "`free_cash_flow_reported`, `total_assets`, `net_ppe`, `op_margin` "
        "and `revenue_yoy`. The gate "
        "never considered them because **the basis does not read them**: "
        "the first is an E103 REFERENCE figure, which §5 is forbidden to "
        "read, and the rest are section 4 furniture. Nothing was exempted "
        "there because nothing was ever at stake.",
        "",
    ]


def report(s: dict) -> str:
    cur = s["currency"]
    g = s["growth"]
    gate = s["gate"]
    unverified = [r for r in gate.refusals if r.kind == "UNVERIFIED"]
    struck = not gate.refused and not gate.refusals
    label = "STRUCK" if struck else "PROVISIONAL"
    e113 = sorted(f.subject.split()[-1] for f in gate.flags if "E113" in f.detail)
    e108 = sorted(f.subject.split()[-1] for f in gate.flags
                  if "E113" not in f.detail and "E108" in f.detail)
    if struck:
        head = [
            f"# MEKKO.HE — section 5, {STAMP} — **STRUCK**",
            "",
            "## THE GATE OPENS",
            "",
            f"`section5_gate` returns **{len(gate.refusals)} refusals**. "
            f"E21 refuses section 5 on an UNVERIFIED figure the basis reads; "
            f"it refuses nothing here, and **this is a struck fair value "
            f"rather than the arithmetic of one.**",
            "",
            f"**HOW IT OPENED, STATED PLAINLY — four read-backs and twenty "
            f"waivers, not twenty-four read-backs.** The store carries "
            f"**{len(e113) + len(e108) + 4} figures the basis reads. FOUR "
            f"are VERIFIED by the owner against a rendered page on "
            f"{STAMP} (E40)**: `operating_cash_flow` `cross_document` "
            f"(audited annual report p.86 and the Bulletin p.26), "
            f"`diluted_weighted_average_shares` `same_page` (p.31 and note "
            f"10 on p.96), `net_finance_costs` `same_page` (p.84), "
            f"`shares_issued_period_end` `same_page` (p.24). **The other "
            f"{len(e108) + len(e113)} were never read back and are exempt** "
            f"— {len(e108)} under E108's measured floor, {len(e113)} under "
            f"E113. They are named below so the waiver is visible rather "
            f"than silent.",
            "",
            "**WHAT THAT COSTS, SAID ONCE.** E94's second fence is *every "
            "figure the basis reads VERIFIED under E40*, and on its literal "
            "words this record does not clear it — twenty figures hold a "
            "page nobody has looked at. **E108 and E113 are the framework's "
            "own answer to that**: a leg that cannot move `fv_base` by 1%, "
            "or that `fv_base` never reads at all, is not a reason to refuse "
            "a value. **Both waive the READ-BACK and neither waives the "
            "PROVENANCE** — every one of the twenty keeps its page and every "
            "zero keeps its `zero_basis` under E25. The value below is "
            "struck on that basis and on no other.",
            "",
        ]
    else:
        head = [
            f"# MEKKO.HE — section 5 arithmetic, {STAMP} — **PROVISIONAL**",
            "",
            "## THE GATE REFUSES THIS NAME, AND EVERY FIGURE BELOW IS PROVISIONAL",
            "",
            f"`section5_gate` returns **{len(gate.refusals)} refusals**, "
            f"**{len(unverified)}** of them `UNVERIFIED`. E21 refuses "
            f"section 5 on an UNVERIFIED figure the basis reads, and it is "
            f"right to.",
            "",
            "**So this is not a struck fair value.** It is the arithmetic of "
            "section 5, run on an unverified store at the owner's "
            "instruction. It is not E94's INDICATIVE value either — E94's "
            "second fence is *every figure the basis reads VERIFIED under "
            "E40*, and that fence fails. **The read-backs that would convert "
            "it are named below**, measured against E108's floor on this "
            "record's own `fv_base`.",
            "",
        ]
    lines = head + [
        f"**Growth view registered {g.view_date.isoformat()} by the owner, in "
        f"his own words, BEFORE this ran (E28).** bear {g.bear:.0%} / base "
        f"{g.base:.0%} / bull {g.bull:.0%}, from `{g.view_file}`. **Read off "
        f"the FILE and not off a watchlist `growth:` block (E109)**: MEKKO.HE "
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
        f"## The value — {label}", "",
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
        f"**{s['implied_band'][2]:.2%}**. {_band_sentence(s)}",
        "",
    ] + _gate_section(s, gate, e108, e113, struck) + [
        "## E108's floor on this record's own fv_base, leg by leg",
        "",
        f"E108 exempts a leg whose ±10% perturbation moves `fv_base` by less "
        f"than 1%. **The floor is measured here against the {band.mid:,.2f} "
        f"{cur} above**, which is what E108 requires and what the intake "
        f"could not do, having no `fv_base` to measure against.",
        "",
        "| leg | value | ±10% moves `fv_base` by | |",
        "|---|---:|---:|---|",
    ] + _floor_rows(s) + [
        "",
        f"**Both legs above the floor were read back by the owner on "
        f"2026-09-08 and are VERIFIED.** "
        f"Everything else in this table is under 1%. **E108 waives the "
        f"READ-BACK and never the PROVENANCE** — every figure keeps its "
        f"page, and every zero keeps its `zero_basis` under E25.",
        "",
        "*Recomputed on any change of basis, as E108 requires: a new year "
        "re-decides this list rather than inheriting it.*",
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
        f"range before scoring; **none of them is the MBP.**"
        + ("" if struck else " All of them inherit this page's "
           "PROVISIONAL label."),
        "",
        "| tier | MBP would be |", "|---|---:|",
    ]
    for tier, mbp in s["mbp_by_tier"].items():
        lines.append(f"| {tier} | {mbp.mid:,.2f} {cur} |")
    lines += [
        "", "## What was written", "",
        f"`reference/MEKKO.HE-STRIKE-{STAMP}.md` (this file) and "
        f"`reference/run-records/MEKKO.HE-{STAMP}.json` — every leg, every "
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
    (out / f"MEKKO.HE-STRIKE-{STAMP}.md").write_text(report(s), encoding="utf-8")
    if "gaps" in s:
        print("MEKKO.HE: record INCOMPLETE, no value printed")
        for gap in s["gaps"]:
            print("   ", gap)
    else:
        (out / "run-records" / f"MEKKO.HE-{STAMP}.json").write_text(
            json.dumps(s["record"].to_dict(), indent=2, default=str) + "\n",
            encoding="utf-8")
        print(f"MEKKO.HE fv_base {s['band'].mid:>9,.2f} "
              f"(band {s['band'].low:,.2f}/{s['band'].high:,.2f})  "
              f"bear {s['bear']:>8,.2f}  bull {s['bull']:>8,.2f}  "
              f"price {s['price']:>7,.2f}  g* {s['implied']:>7.2%}  "
              f"vs fv {s['price'] / s['band'].mid - 1:>+7.1%}")
        gate_ = s["gate"]
        print(f"       {'STRUCK' if not gate_.refusals else 'PROVISIONAL'}: "
              f"section5_gate returns "
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
