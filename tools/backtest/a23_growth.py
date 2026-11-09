"""ATTEMPTS #23 (pre-registered 2026-11-08, before any run): does E144's
derived growth OVERESTIMATE the growth later realised?

    .venv/bin/python -m tools.backtest.a23_growth > reports/attempts/A23-RESULT.md

Per company-date: the row's derived base growth (`g_base`, the engine's
E144: issuer organic where stated, else the deal-free PROXY, capped) against
the realised CAGR of the same flow E140 values -- the 3-year mean of
ex-working-capital FCF (`fcf_mean`) PER SHARE -- from the test date to the
row of the same company 5 (and 10) years later. A company with no row at the
later date (delisted, or out of the universe) is counted apart, never
dropped silently; a flow that is not positive at either end has no CAGR and
is counted apart.

Data: US -- data/backtest/run/<date>.jsonl (the engine's rows; the later
dates 2021-2025 are written by `tools.backtest.run --date ...` first);
Nordic -- data/backtest/nordic-m7/ (cleaned, quarter-start fixed). The
locked Nordic confirmation dates (2022-23) are never read.

THE DECISION RULE (owner, fixed 2026-11-08): "overestimates" holds only if
the mean of the dates' median errors (derived - realised) is > 0 AND > 0 on
at least 2/3 of the dates, at 5 years, in BOTH markets AND BOTH halves ->
E160 IN (a haircut is motivated). Otherwise -> E160 OUT (struck; its
commits on rules-round-3-pending are not merged).
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BT = ROOT / "data" / "backtest"
SOURCES = {"us": BT / "run", "nordic": BT / "nordic-m7"}
HALVES = {"us": (("2016", "2017", "2018"), ("2019", "2020")),
          "nordic": (("2010", "2011", "2012", "2013", "2014", "2015"),
                     ("2016", "2017", "2018", "2019", "2020", "2021"))}
HORIZONS = (5, 10)


def load(market: str) -> dict[str, dict[str, dict]]:
    """date -> company id -> row (only rows with the fields #23 reads)."""
    out: dict[str, dict[str, dict]] = {}
    d = SOURCES[market]
    if not d.exists():
        raise SystemExit(f"{d} is missing -- run the prerequisite step first (round3.sh)")
    for p in sorted(d.glob("*.jsonl")):
        day = p.stem
        if market == "nordic" and day >= "2022":
            continue                                    # the locked confirmation
        rows = {}
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            key = str(r.get("cik") or r.get("symbol"))
            rows[key] = r
        out[day] = rows
    return out


def per_share(r: dict) -> float | None:
    f, s = r.get("fcf_mean"), r.get("shares")
    if f is None or not s or s <= 0:
        return None
    return f / s


def later(day: str, h: int) -> str:
    return f"{int(day[:4]) + h}{day[4:]}"


def errors(data, h: int):
    """date -> (list of errors, counts of what could not be measured)."""
    res = {}
    for day, rows in sorted(data.items()):
        fut = data.get(later(day, h))
        if fut is None:
            continue
        errs, gone, nonpos, nobase = [], 0, 0, 0
        for k, r in rows.items():
            g = r.get("g_base")
            if g is None:
                nobase += 1
                continue
            r2 = fut.get(k)
            if r2 is None:
                gone += 1
                continue
            a, b = per_share(r), per_share(r2)
            if a is None or b is None or a <= 0 or b <= 0:
                nonpos += 1
                continue
            realised = (b / a) ** (1 / h) - 1
            errs.append(g - realised)
        res[day] = (errs, {"measured": len(errs), "no row later": gone,
                           "flow not positive": nonpos, "no derived base": nobase})
    return res


def verdict(res, market) -> tuple[bool | None, list[str]]:
    lines = []
    ok_halves = []
    for i, half in enumerate(HALVES[market]):
        meds = [statistics.median(e) for d, (e, _) in res.items() if d[:4] in half and e]
        if not meds:
            lines.append(f"half {i + 1}: no date with a {len(half)}-year realised window")
            ok_halves.append(None)
            continue
        mean = statistics.mean(meds)
        share = sum(m > 0 for m in meds) / len(meds)
        ok = mean > 0 and share >= 2 / 3
        ok_halves.append(ok)
        lines.append(f"half {i + 1}: mean of date medians {mean * 100:+.2f} pp, "
                     f"> 0 on {sum(m > 0 for m in meds)}/{len(meds)} dates -> "
                     f"{'OVERESTIMATES' if ok else 'does not'}")
    if None in ok_halves:
        return None, lines
    return all(ok_halves), lines


def main() -> int:
    print("# #23 -- E144's derived growth against realised FCF-per-share growth\n")
    print("Pre-registered 2026-11-08 (reference/backtest/ATTEMPTS.md #23); "
          "decision rule fixed by the owner the same day.\n")
    decision = {}
    for market in ("nordic", "us"):
        data = load(market)
        print(f"## {market}\n")
        for h in HORIZONS:
            res = errors(data, h)
            print(f"### {h} years\n")
            print("| date | measured | no row later | flow not positive | no derived base | median error (pp) |")
            print("|---|---:|---:|---:|---:|---:|")
            for d, (e, c) in res.items():
                med = f"{statistics.median(e) * 100:+.2f}" if e else "–"
                print(f"| {d} | {c['measured']} | {c['no row later']} | {c['flow not positive']} | "
                      f"{c['no derived base']} | {med} |")
            if not res:
                print("| – | no date has a realised window at this horizon | | | | |")
            ok, lines = verdict(res, market)
            print("\n" + "\n".join(f"- {x}" for x in lines) + "\n")
            if h == 5:
                decision[market] = ok
    print("## Decision (5 years, both markets, both halves)\n")
    if None in decision.values():
        print("**NOT DECIDABLE**: a market/half has no 5-year window "
              f"({decision}). E160 stays pending; nothing is merged.")
    elif all(decision.values()):
        print("**E160 IN**: derived growth overestimates in both markets and both halves.")
    else:
        print("**E160 OUT**: the overestimate does not hold in both markets and both halves "
              f"({decision}). E160 is struck; rules-round-3-pending's E160 commits are not merged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
