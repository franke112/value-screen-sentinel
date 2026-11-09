"""TEST A1 (a) and (b) (ATTEMPTS #15): every return the level-break guard
changed, where the row sat in the rankings, and whether the guard brought
survivorship back.

    .venv/bin/python -m tools.backtest.a1_guard > data/backtest/devour-a1-r2/ROWS.md
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

from . import devour as D
from . import measure as MS

import sys as _sys
#: compare the stored rows (guard as stored) with the -nolb twin (default)
#: or with the -clean twin (one-day spikes dropped, guard kept): argv[1]
TWIN = _sys.argv[1] if len(_sys.argv) > 1 else "nolb"
PAIRS = {"nordic": ("nordic-m6", f"nordic-m6-{TWIN}"),
         "us-bust": ("run-eodhd-bust-m5", f"run-eodhd-bust-m5-{TWIN}"),
         "us-last": ("run-eodhd-m5", f"run-eodhd-m5-{TWIN}")}


def fifth_of(rows, key, target, best_high=True):
    """1 (worst) .. 5 (best) of `target` among rows with the key, or None."""
    rs = sorted((r for r in rows if key(r) is not None), key=key, reverse=not best_high)
    k = len(rs)
    if k < 25 or target not in rs:
        return None
    i = rs.index(target)
    return min(5, i * 5 // k + 1)


def key_score(rows):
    ranks = D.key_rank(rows)
    return lambda r: None if id(r) not in ranks else -ranks[id(r)]


def main() -> int:
    out = []
    summary = []
    for market, (with_, without) in PAIRS.items():
        a = MS.load(D.BT / with_)
        b = MS.load(D.BT / without)
        if market == "nordic":
            D.fill_nordic_assets(a)
            D.fill_nordic_assets(b)
        changed = []
        for d in sorted(a):
            A = {str(r.get("cik")): r for r in a[d] if r.get("status") == "ok"}
            B = {str(r.get("cik")): r for r in b[d] if r.get("status") == "ok"}
            pool = [r for r in b[d] if r.get("status") == "ok" and r.get("price")]
            ks = key_score(pool)
            for cik, ra in A.items():
                rb = B[cik]
                for h in ("1", "3", "5"):
                    x, y = (rb.get("returns") or {}).get(h), (ra.get("returns") or {}).get(h)
                    ex_b, ex_a = (rb.get("exit") or {}).get(h), (ra.get("exit") or {}).get(h)
                    if x == y and ex_a == ex_b:
                        continue
                    if x is not None and y is not None and abs(x - y) < 1e-12 and ex_a == ex_b:
                        continue
                    idx = (rb.get("index_returns") or {}).get(h)
                    allx = [MS.excess(r, int(h)) for r in MS.usable(b[d], int(h))]
                    changed.append({
                        "market": market, "date": d, "name": D.symbol(rb) or rb.get("company"), "h": h,
                        "without": x, "with": y, "exit_without": ex_b, "exit_with": ex_a,
                        "excess_without": None if x is None or idx is None else x - idx,
                        "date_mean_excess": statistics.mean(allx) if allx else None,
                        "fvp": fifth_of(pool, MS.fv_ratio, rb),
                        "key": fifth_of(pool, ks, rb),
                        "ebit_ev": fifth_of(pool, lambda r: r.get("ebit_ev"), rb),
                    })
        refused = [c for c in changed if c["with"] is None and c["without"] is not None]
        cut = [c for c in changed if c["with"] is not None]
        gained = [c for c in changed if c["with"] is not None and c["without"] is None]
        rows_changed = {(c["date"], c["name"]) for c in changed}
        gap = [c["excess_without"] - c["date_mean_excess"] for c in refused
               if c["excess_without"] is not None and c["date_mean_excess"] is not None]
        delisted = sum(1 for c in refused if (c["exit_without"] or "").startswith("delisted"))
        summary.append(
            f"| {market} | {len(rows_changed)} | {len(changed)} | {len(refused)} | {len(cut)} | {len(gained)} | "
            f"{D.pp(statistics.mean(gap)) if gap else '–'} | {delisted} of {len(refused)} |")
        out += changed
    print(f"# A1: stored rows against the -{TWIN} twin (attempt #15); 'without' = the twin\n")
    print("| Market | rows changed | (row, horizon) changed | refused by the guard | cut to a delisting "
          "or other value | given a return by it | refused rows' excess without the guard minus "
          "their dates' mean | refused rows delisted without the guard |")
    print("|---|---:|---:|---:|---:|---:|---:|---|")
    print("\n".join(summary))
    print("\n## Every change\n")
    print("| Market | Date | Name | h | return without -> with | exit without -> with | "
          "fifth fv/price | fifth E43 | fifth EBIT/EV |")
    print("|---|---|---|---|---|---|---|---|---|")
    for c in sorted(out, key=lambda c: (c["market"], c["date"], c["name"], c["h"])):
        print(f"| {c['market']} | {c['date']} | {c['name']} | {c['h']} | {D.pp(c['without'], 0)} -> "
              f"{D.pp(c['with'], 0)} | {c['exit_without']} -> {c['exit_with']} | "
              f"{c['fvp'] or '–'} | {c['key'] or '–'} | {c['ebit_ev'] or '–'} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
