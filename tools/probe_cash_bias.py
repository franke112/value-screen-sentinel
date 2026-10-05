"""HISTORICAL: reads the E5-era ranking.csv columns (roic, roic_rank), which
FRAMEWORK-EDITS E6 renamed on 2026-08-22. It runs against the stored
2026-08-21 artefacts it was written for, not against an E6 ranking.

PROBE: does the ranking key have a geographic tilt, and is cash the cause?

A BUILD-TIME measurement, like tools/build_universe.py and
tools/probe_ranking_fields.py. It reads a completed ranking run and answers
three questions with numbers.

    1. How the ranked names distribute across markets, and where each market
       sits in the ordering.
    2. The CASH-BIAS hypothesis. FRAMEWORK-EDITS E5 defines net working
       capital as current assets minus current liabilities, WITH cash in it.
       Greenblatt excludes the cash a business does not need to operate. A
       cash-rich company therefore shows a LOWER return on capital under E5
       than under Greenblatt's own definition. This recomputes the key with
       cash removed and shows what moves.
    3. Whether cash relative to enterprise value differs by market, which is
       what would turn a definitional bias into a geographic one.

IT CHANGES NOTHING. E5 is the decided key and this tool does not touch it,
does not write to the ranking, and does not write to the watchlist. It
measures an alternative so the owner can see whether the decided key has a
tilt that was not intended.

    python tools/probe_cash_bias.py --asof 2026-08-21

The fetch is cached to scratch/, so the analysis can be re-run without going
back to the network.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: In preference order. The broader line is used for the recomputation:
#: short-term investments are as non-operating as the cash beside them, and
#: Greenblatt's exclusion is about capital the business does not need to run.
#: The narrow line is measured too, so the choice can be seen to matter or not.
CASH_BROAD = "Cash Cash Equivalents And Short Term Investments"
CASH_NARROW = "Cash And Cash Equivalents"


def load_ranking(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fetch_cash(tickers, cache: Path, pause: float = 0.25) -> dict[str, dict]:
    """Annual balance-sheet cash, one request per ticker, cached to disk."""
    known = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    missing = [t for t in tickers if t not in known]
    if missing:
        import pandas as pd
        import yfinance as yf

        for index, ticker in enumerate(missing, 1):
            entry = {"broad": None, "narrow": None, "period": None}
            try:
                frame = yf.Ticker(ticker).balance_sheet
                if frame is not None and not frame.empty:
                    column = frame.columns[0]
                    entry["period"] = str(pd.Timestamp(column).date())
                    for key, line in (("broad", CASH_BROAD), ("narrow", CASH_NARROW)):
                        if line in frame.index:
                            value = frame.loc[line, column]
                            entry[key] = None if pd.isna(value) else float(value)
            except Exception as exc:  # noqa: BLE001 - a probe reports, never dies
                entry["error"] = f"{type(exc).__name__}: {exc}"
            known[ticker] = entry
            if index % 25 == 0:
                print(f"  cash {index}/{len(missing)}", file=sys.stderr)
                cache.write_text(json.dumps(known, indent=1), encoding="utf-8")
            time.sleep(pause)
        cache.write_text(json.dumps(known, indent=1), encoding="utf-8")
    return known


def number(row: dict, key: str):
    value = row.get(key)
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def competition_ranks(values):
    order = sorted(range(len(values)), key=lambda i: -values[i])
    ranks, previous = [0] * len(values), None
    for position, index in enumerate(order, start=1):
        ranks[index] = ranks[previous] if (previous is not None
                                           and values[index] == values[previous]) else position
        previous = index
    return ranks


def hyper_at_most(k: int, K: int, N: int, n: int) -> float:
    return sum(math.comb(K, i) * math.comb(N - K, n - i)
               for i in range(0, k + 1)) / math.comb(N, n)


def mann_whitney(a, b) -> tuple[float, float]:
    merged = sorted(a + b)
    ranks, i = {}, 0
    while i < len(merged):
        j = i
        while j + 1 < len(merged) and merged[j + 1] == merged[i]:
            j += 1
        shared = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[merged[k]] = shared
        i = j + 1
    n1, n2 = len(a), len(b)
    u = sum(ranks[v] for v in a) - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (u - mu) / sigma
    return z, 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--asof", default="2026-08-21")
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args(argv)

    run = ROOT / "data" / "screener_runs" / args.asof
    rows = load_ranking(run / "ranking.csv")
    ranked = [r for r in rows if r["section"] == "ranked"]
    priced = [r for r in rows if number(r, "enterprise_value_reporting")]

    cache = ROOT / "scratch" / f"cash-{args.asof}.json"
    cache.parent.mkdir(exist_ok=True)
    cash = fetch_cash([r["ticker"] for r in priced], cache)

    print("=" * 78)
    print(f"CASH BIAS AND GEOGRAPHY -- ranking of {args.asof}")
    print("=" * 78)
    print("\nThis probe MEASURES an alternative. It does not change the decided key,")
    print("does not rewrite the ranking, and does not touch the watchlist.")

    # --- 1 -----------------------------------------------------------------
    position = {r["ticker"]: i for i, r in enumerate(ranked, 1)}
    by_market = defaultdict(list)
    for row in ranked:
        by_market[row["marknad"]].append(position[row["ticker"]])

    print(f"\n1. WHERE EACH MARKET SITS  ({len(ranked)} ranked on both components)")
    header = (f"  {'market':<14}{'n':>5}{'share':>8}{'median':>8}{'mean':>7}"
              f"{'best':>6}{'top20':>7}{'top50':>7}")
    print("\n" + header)
    print("  " + "-" * (len(header) - 2))
    for market, places in sorted(by_market.items(), key=lambda kv: statistics.median(kv[1])):
        print(f"  {market:<14}{len(places):>5}{len(places)/len(ranked):>8.1%}"
              f"{statistics.median(places):>8.0f}{statistics.mean(places):>7.0f}"
              f"{min(places):>6}{sum(1 for p in places if p <= 20):>7}"
              f"{sum(1 for p in places if p <= 50):>7}")

    us = [p for p in by_market.get("US", [])]
    rest = [p for market, places in by_market.items() if market != "US" for p in places]
    if us:
        total, k = len(ranked), len(us)
        print(f"\n  US against chance, if placement were independent of market:")
        for cut in (5, 10, 20, 50, 100):
            observed = sum(1 for p in us if p <= cut)
            print(f"      top {cut:>3}: observed {observed:>3}, expected {k/total*cut:>5.1f}, "
                  f"P(<= observed) = {hyper_at_most(observed, k, total, cut):.3f}")
        z, p = mann_whitney(us, rest)
        print(f"  over the WHOLE ordering: Mann-Whitney z={z:+.2f}, two-sided p={p:.3f}")
        print(f"      median placement  US {statistics.median(us):.0f}  "
              f"non-US {statistics.median(rest):.0f}")

    # --- 2 -----------------------------------------------------------------
    print(f"\n2. THE CASH-BIAS HYPOTHESIS -- ROIC recomputed with cash removed")
    print("   E5:          ROIC = EBIT / ((current assets - current liabilities) + net PP&E)")
    print("   alternative: ROIC = EBIT / ((current assets - cash - current liabilities)"
          " + net PP&E)")
    print("   Cash is the broad line (cash, equivalents and short-term investments):")
    print("   short-term investments are as non-operating as the cash beside them.")

    usable, undefined = [], []
    for row in ranked:
        ebit = number(row, "ebit")
        nwc = number(row, "net_working_capital")
        ppe = number(row, "net_ppe")
        ey = number(row, "earnings_yield")
        held = (cash.get(row["ticker"]) or {}).get("broad")
        if None in (ebit, nwc, ppe, ey) or held is None:
            undefined.append((row["ticker"], "no cash line" if held is None else "no inputs"))
            continue
        denominator = (nwc - held) + ppe
        if denominator <= 0:
            undefined.append((row["ticker"], "denominator not positive without cash"))
            continue
        usable.append({**row, "roic_ex": ebit / denominator, "cash": held,
                       "ey": ey, "old_pos": position[row["ticker"]]})

    print(f"\n   {len(usable)} of {len(ranked)} recomputable; {len(undefined)} not")
    reasons = defaultdict(int)
    for _, why in undefined:
        reasons[why] += 1
    for why, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"      {count:>4}  {why}")
    print("   Removing all cash drives some denominators through zero. Those names")
    print("   are dropped from the comparison rather than clamped -- the same rule")
    print("   E5 applies, and the reason the alternative is not obviously better.")

    roic_ranks = competition_ranks([r["roic_ex"] for r in usable])
    ey_ranks = competition_ranks([r["ey"] for r in usable])
    for index, row in enumerate(usable):
        row["combined_ex"] = roic_ranks[index] + ey_ranks[index]
    alt = sorted(usable, key=lambda r: (r["combined_ex"], r["ticker"]))
    new_pos = {r["ticker"]: i for i, r in enumerate(alt, 1)}
    # Where the same names sit under E5, restricted to the comparable set.
    old_order = sorted(usable, key=lambda r: r["old_pos"])
    old_pos = {r["ticker"]: i for i, r in enumerate(old_order, 1)}

    print(f"\n   TOP {args.top} WITH CASH REMOVED (comparable set of {len(usable)})")
    head = (f"  {'#':>3} {'ticker':<13}{'market':<12}{'was':>5}{'move':>6}"
            f"{'ROIC E5':>10}{'ROIC ex-cash':>14}{'cash/EV':>9}")
    print("\n" + head)
    print("  " + "-" * (len(head) - 2))
    for place, row in enumerate(alt[:args.top], 1):
        was = old_pos[row["ticker"]]
        ev = number(row, "enterprise_value_reporting")
        print(f"  {place:>3} {row['ticker']:<13}{row['marknad']:<12}{was:>5}"
              f"{was - place:>+6}{number(row, 'roic'):>10.1%}{row['roic_ex']:>14.1%}"
              + (f"{row['cash']/ev:>9.1%}" if ev else f"{'--':>9}"))

    entered = [r for r in alt[:args.top] if old_pos[r["ticker"]] > args.top]
    left = [r for r in old_order[:args.top] if new_pos[r["ticker"]] > args.top]
    print(f"\n   entered the top {args.top}: "
          + (", ".join(f"{r['ticker']} ({r['marknad']}, was {old_pos[r['ticker']]})"
                       for r in entered) or "none"))
    print(f"   left the top {args.top}:     "
          + (", ".join(f"{r['ticker']} ({r['marknad']}, now {new_pos[r['ticker']]})"
                       for r in left) or "none"))

    us_alt = [new_pos[r["ticker"]] for r in usable if r["marknad"] == "US"]
    us_old = [old_pos[r["ticker"]] for r in usable if r["marknad"] == "US"]
    if us_alt:
        print(f"\n   US on the comparable set: median placement "
              f"{statistics.median(us_old):.0f} under E5 -> "
              f"{statistics.median(us_alt):.0f} with cash removed")
        print(f"      in the top {args.top}: "
              f"{sum(1 for p in us_old if p <= args.top)} -> "
              f"{sum(1 for p in us_alt if p <= args.top)}")

    # --- 3 -----------------------------------------------------------------
    print("\n3. CASH AGAINST ENTERPRISE VALUE, BY MARKET")
    print("   Both figures in the reporting currency, so no rate is involved.")
    ratios = defaultdict(list)
    for row in priced:
        held = (cash.get(row["ticker"]) or {}).get("broad")
        ev = number(row, "enterprise_value_reporting")
        if held is None or not ev or ev <= 0:
            continue
        ratios[row["marknad"]].append(held / ev)
    head = f"  {'market':<14}{'n':>5}{'median':>9}{'mean':>8}{'p90':>8}"
    print("\n" + head)
    print("  " + "-" * (len(head) - 2))
    for market, values in sorted(ratios.items(), key=lambda kv: -statistics.median(kv[1])):
        ordered = sorted(values)
        p90 = ordered[min(len(ordered) - 1, int(0.9 * len(ordered)))]
        print(f"  {market:<14}{len(values):>5}{statistics.median(values):>9.1%}"
              f"{statistics.mean(values):>8.1%}{p90:>8.1%}")
    us_ratio = ratios.get("US", [])
    rest_ratio = [v for market, vals in ratios.items() if market != "US" for v in vals]
    if us_ratio and rest_ratio:
        z, p = mann_whitney(us_ratio, rest_ratio)
        print(f"\n  US vs the rest: median {statistics.median(us_ratio):.1%} vs "
              f"{statistics.median(rest_ratio):.1%}; Mann-Whitney z={z:+.2f}, p={p:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
