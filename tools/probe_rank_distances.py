"""HISTORICAL: reads the E5-era ranking.csv columns (roic, roic_rank), which
FRAMEWORK-EDITS E6 renamed on 2026-08-22. It runs against the stored
2026-08-21 artefacts it was written for, not against an E6 ranking.

PROBE: how far apart are the ranked names, really?

A rank sum is an ordering built from two orderings. It deliberately throws
away magnitude: the gap between first and second counts the same as the gap
between 200th and 201st, whether the underlying difference is a chasm or a
rounding error. That is Greenblatt's design and FRAMEWORK-EDITS E5 adopts it
knowingly -- but it means the ordering alone cannot say whether the top five
are meaningfully separated or effectively tied.

This measures the distances the ordering discards:

    1. What a "good" ROIC and a "good" earnings yield actually are in THIS
       candidate set, as percentiles.
    2. Where the real jumps are inside the top 20, and where names merely
       cluster.
    3. What the top 20 would look like ranked by z-score, and by percentile,
       instead of by place.
    4. Whether the first place survives weighting the two legs 60/40 and
       40/60 instead of evenly.
    5. The correlation between the two legs -- which decides whether the key
       rewards names that are good at both, or names that are middling at
       both because nothing can be good at both.

IT CHANGES NOTHING. Not E5, not the ranking code, not the watchlist.

    python tools/probe_rank_distances.py --asof 2026-08-21
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: The names phase 6 entered. Their relative order is the question this probe
#: exists to answer, so they are marked wherever they appear.
PIPELINE = ("TE.PA", "BATS.L", "RKT.L", "EVD.DE", "ERIC-B.ST")


def percentile(sorted_values, q: float) -> float:
    if not sorted_values:
        return float("nan")
    position = q * (len(sorted_values) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return sorted_values[int(position)]
    return (sorted_values[low] * (high - position)
            + sorted_values[high] * (position - low))


def pct_of(sorted_values, value: float) -> float:
    """Share of the set at or below ``value`` -- 1.0 is the best in the set."""
    below = sum(1 for v in sorted_values if v < value)
    equal = sum(1 for v in sorted_values if v == value)
    return (below + equal / 2) / len(sorted_values)


def spearman(a, b) -> float:
    def ranked(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            shared = (i + j) / 2 + 1
            for k in range(i, j + 1):
                out[order[k]] = shared
            i = j + 1
        return out

    ra, rb = ranked(a), ranked(b)
    n = len(a)
    ma, mb = statistics.mean(ra), statistics.mean(rb)
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((x - mb) ** 2 for x in rb))
    return num / den if den else float("nan")


def mark(ticker: str) -> str:
    return " *" if ticker in PIPELINE else "  "


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--asof", default="2026-08-21")
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args(argv)

    path = ROOT / "data" / "screener_runs" / args.asof / "ranking.csv"
    with path.open(encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if r["section"] == "ranked"]
    for row in rows:
        row["roic_v"] = float(row["roic"])
        row["ey_v"] = float(row["earnings_yield"])
        row["r1"] = int(row["roic_rank"])
        row["r2"] = int(row["ey_rank"])
        row["sum"] = int(row["combined_rank"])
    n = len(rows)
    roic_sorted = sorted(r["roic_v"] for r in rows)
    ey_sorted = sorted(r["ey_v"] for r in rows)
    order = list(rows)  # already sorted by the decided key

    print("=" * 78)
    print(f"RANK DISTANCES -- {n} names ranked on both components, {args.asof}")
    print("=" * 78)
    print("\nA MEASUREMENT. E5, the ranking code and the watchlist are untouched.")
    print("* marks a name phase 6 entered as PIPELINE.")

    # --- 1 -----------------------------------------------------------------
    print("\n1. WHAT A GOOD VALUE ACTUALLY IS IN THIS SET")
    print(f"\n  {'percentile':<14}{'ROIC':>12}{'earnings yield':>18}")
    print("  " + "-" * 42)
    for q in (0.10, 0.25, 0.50, 0.75, 0.90):
        print(f"  p{int(q*100):<13}{percentile(roic_sorted, q):>12.1%}"
              f"{percentile(ey_sorted, q):>18.1%}")
    print(f"  {'min':<14}{roic_sorted[0]:>12.1%}{ey_sorted[0]:>18.1%}")
    print(f"  {'max':<14}{roic_sorted[-1]:>12.1%}{ey_sorted[-1]:>18.1%}")
    print(f"\n  ROIC p90/p50 = {percentile(roic_sorted,0.9)/percentile(roic_sorted,0.5):.1f}x, "
          f"max/p90 = {roic_sorted[-1]/percentile(roic_sorted,0.9):.1f}x")
    print(f"  EY   p90/p50 = {percentile(ey_sorted,0.9)/percentile(ey_sorted,0.5):.1f}x, "
          f"max/p90 = {ey_sorted[-1]/percentile(ey_sorted,0.9):.1f}x")
    print("  A long right tail on ROIC means the top of that leg is a few extreme")
    print("  names, not a gentle slope. The earnings yield is far more compressed.")

    # --- 2 -----------------------------------------------------------------
    print(f"\n2. THE TOP {args.top}: PERCENTILE OF EACH LEG, AND THE STEP TO THE NEXT")
    print("   'step' is the drop in the sum of the two percentiles from the name")
    print("   above. A large step is a real separation; a run of small ones is a")
    print("   cluster the ordering is presenting as a sequence.")
    head = (f"  {'#':>3} {'ticker':<13}{'ROIC':>9}{'pct':>7}{'  EY':>8}{'pct':>7}"
            f"{'pct sum':>9}{'step':>8}")
    print("\n" + head)
    print("  " + "-" * (len(head) - 2))
    previous = None
    for place, row in enumerate(order[:args.top], 1):
        p1 = pct_of(roic_sorted, row["roic_v"])
        p2 = pct_of(ey_sorted, row["ey_v"])
        total = p1 + p2
        step = "" if previous is None else f"{previous - total:>8.3f}"
        print(f"  {place:>3} {row['ticker']:<13}{row['roic_v']:>9.1%}{p1:>7.2f}"
              f"{row['ey_v']:>8.1%}{p2:>7.2f}{total:>9.3f}{step}{mark(row['ticker'])}")
        previous = total

    steps = []
    for i in range(1, min(args.top, len(order))):
        a = order[i - 1]
        b = order[i]
        ta = pct_of(roic_sorted, a["roic_v"]) + pct_of(ey_sorted, a["ey_v"])
        tb = pct_of(roic_sorted, b["roic_v"]) + pct_of(ey_sorted, b["ey_v"])
        steps.append((ta - tb, i, i + 1, a["ticker"], b["ticker"]))
    big = sorted(steps, key=lambda s: -s[0])[:4]
    print("\n   the four largest separations inside the top 20:")
    for gap, i, j, a, b in big:
        print(f"      {i}->{j}  {a} to {b}: {gap:+.3f} of a combined percentile")
    tiny = [s for s in steps if abs(s[0]) < 0.02]
    print(f"   {len(tiny)} of the {len(steps)} steps are under 0.02 -- effectively ties:")
    for gap, i, j, a, b in tiny:
        print(f"      {i}->{j}  {a} / {b}  ({gap:+.3f})")

    # --- 3 -----------------------------------------------------------------
    print(f"\n3. THE SAME NAMES SCORED INSTEAD OF PLACED")
    mu1, sd1 = statistics.mean(roic_sorted), statistics.pstdev(roic_sorted)
    mu2, sd2 = statistics.mean(ey_sorted), statistics.pstdev(ey_sorted)
    for row in rows:
        row["z"] = (row["roic_v"] - mu1) / sd1 + (row["ey_v"] - mu2) / sd2
        row["pctsum"] = pct_of(roic_sorted, row["roic_v"]) + pct_of(ey_sorted, row["ey_v"])
    by_z = sorted(rows, key=lambda r: (-r["z"], r["ticker"]))
    by_pct = sorted(rows, key=lambda r: (-r["pctsum"], r["ticker"]))
    place_of = {r["ticker"]: i for i, r in enumerate(order, 1)}

    same = sum(1 for i, r in enumerate(by_pct, 1) if place_of[r["ticker"]] == i)
    moved = [(i, r["ticker"], place_of[r["ticker"]])
             for i, r in enumerate(by_pct, 1) if place_of[r["ticker"]] != i]
    top_same = ([r["ticker"] for r in by_pct[:args.top]]
                == [r["ticker"] for r in order[:args.top]])
    print("\n   PERCENTILE SUM is very nearly the same ordering as the rank sum, and")
    print("   for a reason worth knowing: percentile = (rank - 0.5) / n is a straight")
    print("   line in rank, so summing percentiles and summing ranks agree wherever")
    print("   the values are distinct. They part only on TIES, because E5 gives tied")
    print("   values the better rank while a mid-rank percentile splits them.")
    print(f"   measured: {same} of {n} names in the same place; {len(moved)} moved, "
          f"every one by a single place.")
    print(f"   the top {args.top} is {'identical' if top_same else 'NOT identical'}.")
    print("   So percentiles buy nothing here. Only a SCORE lets magnitude count.")

    print(f"\n   Z-SCORE top {args.top} (magnitude allowed to count):")
    head = f"  {'#':>3} {'ticker':<13}{'was':>5}{'move':>6}{'z':>8}{'ROIC':>10}{'EY':>8}"
    print("\n" + head)
    print("  " + "-" * (len(head) - 2))
    for place, row in enumerate(by_z[:args.top], 1):
        was = place_of[row["ticker"]]
        print(f"  {place:>3} {row['ticker']:<13}{was:>5}{was-place:>+6}{row['z']:>8.2f}"
              f"{row['roic_v']:>10.1%}{row['ey_v']:>8.1%}{mark(row['ticker'])}")
    print("\n   ROIC's tail runs to 1562% against a median near 30%, so a z-score on")
    print("   raw values is decided by a handful of names. That is not an argument")
    print("   for z-scores; it is the reason Greenblatt ranks instead of scoring.")

    # --- 4 -----------------------------------------------------------------
    print("\n4. IS THE FIRST PLACE ROBUST TO THE WEIGHTING?")
    for w in (0.6, 0.5, 0.4):
        weighted = sorted(rows, key=lambda r: (w * r["r1"] + (1 - w) * r["r2"],
                                               r["ticker"]))
        label = f"ROIC {w:.0%} / EY {1-w:.0%}"
        print(f"\n   {label}")
        for place, row in enumerate(weighted[:10], 1):
            was = place_of[row["ticker"]]
            print(f"      {place:>2} {row['ticker']:<13}was {was:>3}  "
                  f"({was-place:+d}){mark(row['ticker'])}")

    print("\n   TE.PA under each weighting:")
    for w in (0.6, 0.5, 0.4):
        weighted = sorted(rows, key=lambda r: (w * r["r1"] + (1 - w) * r["r2"],
                                               r["ticker"]))
        pos = next(i for i, r in enumerate(weighted, 1) if r["ticker"] == "TE.PA")
        print(f"      ROIC {w:.0%} / EY {1-w:.0%}: place {pos}")

    # --- 5 -----------------------------------------------------------------
    print("\n5. DO THE TWO LEGS PULL AGAINST EACH OTHER?")
    rho_rank = spearman([r["r1"] for r in rows], [r["r2"] for r in rows])
    rho_value = spearman([r["roic_v"] for r in rows], [r["ey_v"] for r in rows])
    print(f"\n   Spearman(ROIC place, EY place)  = {rho_rank:+.3f}")
    print(f"   Spearman(ROIC value, EY value)  = {rho_value:+.3f}")
    print("   Sign convention: place 1 is best on each leg. A POSITIVE correlation")
    print("   between the two PLACES means a name good on one tends to be good on")
    print("   the other. A NEGATIVE one means the legs trade off, and nothing can")
    print("   be excellent at both.")

    q = n // 4
    both_good = [r for r in rows if r["r1"] <= q and r["r2"] <= q]
    one_good = [r for r in rows if (r["r1"] <= q) != (r["r2"] <= q)]
    expected = q * q / n
    print(f"\n   top quartile ({q} names) on BOTH legs: {len(both_good)} "
          f"(chance alone would give {expected:.1f})")
    print(f"   top quartile on exactly one leg:      {len(one_good)}")
    if both_good:
        print("   the names that are top-quartile on both, and where they placed:")
        for row in sorted(both_good, key=lambda r: place_of[r["ticker"]])[:12]:
            print(f"      place {place_of[row['ticker']]:>3}  {row['ticker']:<13}"
                  f"ROIC {row['roic_v']:>8.1%}  EY {row['ey_v']:>6.1%}"
                  f"{mark(row['ticker'])}")

    print(f"\n   HOW THE TOP {args.top} GOT THERE:")
    balanced = extreme = 0
    for row in order[:args.top]:
        if abs(row["r1"] - row["r2"]) > n / 4:
            extreme += 1
        else:
            balanced += 1
    print(f"      {balanced} are within a quartile of the same place on both legs")
    print(f"      {extreme} are carried by one leg while lagging on the other")

    # --- the five ----------------------------------------------------------
    print("\nTHE FIVE PIPELINE NAMES, SIDE BY SIDE")
    head = (f"  {'ticker':<13}{'place':>6}{'sum':>6}{'ROIC':>10}{'pct':>6}"
            f"{'EY':>8}{'pct':>6}{'z':>7}")
    print("\n" + head)
    print("  " + "-" * (len(head) - 2))
    for row in [r for r in order if r["ticker"] in PIPELINE]:
        print(f"  {row['ticker']:<13}{place_of[row['ticker']]:>6}{row['sum']:>6}"
              f"{row['roic_v']:>10.1%}{pct_of(roic_sorted, row['roic_v']):>6.2f}"
              f"{row['ey_v']:>8.1%}{pct_of(ey_sorted, row['ey_v']):>6.2f}"
              f"{row['z']:>7.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
