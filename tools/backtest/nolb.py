"""TEST A1 (round 2, ATTEMPTS #15): the same rows with and without the
level-break guard (review 2026-11-08 M2, e816c76).

    .venv/bin/python -m tools.backtest.nolb --check   # guard ON must reproduce the stored returns
    .venv/bin/python -m tools.backtest.nolb           # writes the *-nolb directories

Nothing is re-valued: every return of the CURRENT rows (nordic-m6,
run-eodhd-bust-m5, run-eodhd-m5) is recomputed with
`eodhd_reprice.level_breaks` switched off, so the only difference between a
directory and its -nolb twin is the guard. The Nordic benchmark is
recomputed as the engine computes it (the equal-weighted mean of every
row's return on the date) and `returns_stop8` with it.
"""
from __future__ import annotations

import argparse
import copy
import json
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date

from . import eodhd_reprice as EP
from . import measure as MS
from . import nordic as N
from . import pilot as PL

BT = PL.ROOT
SOURCES = {"nordic-m6": "bust", "run-eodhd-bust-m5": "bust", "run-eodhd-m5": "last"}
_REAL_BREAKS = EP.level_breaks


def guard(on: bool, clean: bool = False) -> None:
    """lb: the guard as stored (no spike cleaning); nolb: no guard; clean:
    one-day spikes dropped (`eodhd_reprice.drop_spikes`), then the guard."""
    EP.level_breaks = _REAL_BREAKS if on else (lambda f, start, end: [])
    if EP.CLEAN_SPIKES != clean:
        EP.CLEAN_SPIKES = clean
        EP._FRAMES.clear()


MODES = {"lb": (True, False), "nolb": (False, False), "clean": (True, True)}


def recompute(src: str, d: str, on: bool, clean: bool = False) -> list[dict]:
    guard(on, clean)
    policy = SOURCES[src]
    rows = [json.loads(l) for l in (BT / src / f"{d}.jsonl").read_text().splitlines() if l.strip()]
    out = []
    for r in rows:
        r = copy.deepcopy(r)
        if "returns" not in r or r.get("price") is None and src != "nordic-m6":
            out.append(r)
            continue
        sym = r.get("eodhd_symbol") or r.get("symbol")
        f = EP.frame(sym) if sym else None
        day = date.fromisoformat(r["trading_day"])
        if f is None:
            out.append(r)
            continue
        for h in PL.HORIZONS:
            end = PL.years_after(day, h)
            ret, how = EP.total_return(f, day, end, policy)
            r["returns"][str(h)] = ret
            r.setdefault("exit", {})[str(h)] = how
            if src == "nordic-m6":
                r["returns_stop8"][str(h)] = N.stop_return(f, day, end)
        for k in ("returns", "exit", "returns_stop8", "index_returns"):
            if k in r:
                r[k] = {str(a): b for a, b in r[k].items()}
        out.append(r)
    if src == "nordic-m6":
        for h in map(str, PL.HORIZONS):
            rets = [x["returns"][h] for x in out if x.get("returns", {}).get(h) is not None]
            bench = statistics.mean(rets) if rets else None
            for x in out:
                if "returns" in x:
                    x.setdefault("index_returns", {})[h] = bench
    return out


def _norm(rows):
    out = {}
    for r in rows:
        if "returns" in r:
            key = str(r.get("cik"))
            out[key] = ({str(a): b for a, b in r["returns"].items()},
                        {str(a): b for a, b in (r.get("index_returns") or {}).items()})
    return out


def _check(args):
    src, d = args
    stored = _norm([json.loads(l) for l in (BT / src / f"{d}.jsonl").read_text().splitlines() if l.strip()])
    again = _norm(recompute(src, d, True, False))
    bad = []
    for k, (ret, idx) in stored.items():
        r2, i2 = again[k]
        for h in ret:
            a, b = ret[h], r2.get(h)
            if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-12):
                bad.append((src, d, k, h, a, b))
            a, b = idx.get(h), i2.get(h)
            if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-12):
                bad.append((src, d, k, "idx" + h, a, b))
    return len(stored), bad


def _write(args):
    src, d, mode = args
    rows = recompute(src, d, *MODES[mode])
    dest = BT / f"{src}-{mode}" / f"{d}.jsonl"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("".join(json.dumps(r, default=str) + "\n" for r in rows))
    return d


def jobs():
    # a source absent on this machine is skipped (the VPS has no nordic-m6;
    # round 3 reads nordic-m7, written cleaned by the engine itself)
    return [(s, p.stem) for s in SOURCES if (BT / s).exists()
            for p in sorted((BT / s).glob("*.jsonl"))]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--mode", default="nolb", choices=("nolb", "clean"))
    a = ap.parse_args(argv)
    with ProcessPoolExecutor(int(__import__("os").environ.get("BT_WORKERS", "22"))) as pool:
        if a.check:
            n, bad = 0, []
            for k, b in pool.map(_check, jobs()):
                n += k
                bad += b
            print(f"guard ON recomputed: {len(bad)} differences over {n} rows")
            for b in bad[:20]:
                print("  ", b)
        else:
            list(pool.map(_write, [(s, d, a.mode) for s, d in jobs()]))
            print("written:", ", ".join(f"{s}-{a.mode}" for s in SOURCES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
