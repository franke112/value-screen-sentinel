"""The full run (backtest design, step 5): the method's core (`method`) on
every candidate of every test date.

    .venv/bin/python -m tools.backtest.run [--date 2018-04-30 ...] [--workers 4]

Three phases, each resumable -- a name already on disk is not fetched or
evaluated again, so a run that stops is started again with the same line:

1. companyfacts for every candidate CIK of the dates asked for (cached
   gzipped in data/backtest/companyfacts/, as the pilot does);
2. prices for every candidate's first ticker today (data/backtest/prices/);
3. one row per candidate that clears the exact float line, appended to
   data/backtest/run/<date>.jsonl.

THE GROWTH CAP (design §4 point 6). The row is evaluated at the rule's cap
(E144, 4%). Where the growth landed ON a cap -- the only case another cap
can change -- it is evaluated again at 6% and 8% (`GROWTH_CAP` raised, and
the seven-year high cap never below it), and the fv columns of each are kept
under `caps`. Everything else on the row is the 4% evaluation.

Survivors only (owner 2026-10-29): a name with no ticker today has no price
and stays on the row with `price` None; the measure counts them.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from vss import history as HI

from . import method as M
from . import pilot as PL
from . import universe as U
from . import value as V

OUT = PL.ROOT / "run"
CAPS = (0.06, 0.08)
CAP_COLUMNS = ("g_base", "g_bear", "fv_base", "fv_bear", "fv_ex_programme", "status")


def candidates(as_of: date) -> list[dict]:
    return json.loads((PL.ROOT / "universe" / f"{as_of.isoformat()}.json").read_text())["rows"]


def _ticker(cand: dict) -> str | None:
    return (cand.get("tickers_today") or [None])[0]


def _quiet(fn, arg):
    try:
        fn(arg)
    except Exception:  # noqa: BLE001 -- a miss is counted in phase 3
        pass


def prefetch(dates, workers: int) -> None:
    ciks = sorted({c["cik"] for d in dates for c in candidates(d)})
    todo = [c for c in ciks if not (PL.ROOT / "companyfacts" / f"CIK{c:010d}.json.gz").exists()]
    print(f"facts: {len(ciks)} CIKs, {len(todo)} to fetch", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(workers) as pool:
        for i, _ in enumerate(pool.map(lambda c: _quiet(PL.company_facts, c), todo), 1):
            if i % 200 == 0:
                print(f"  facts {i}/{len(todo)} {time.time() - t0:.0f}s", flush=True)
    tickers = sorted({t for d in dates for c in candidates(d) if (t := _ticker(c))} | {PL.INDEX})
    from vss import fetch as F
    todo = [t for t in tickers if not (PL.ROOT / "prices" / f"{F.safe_name(t)}.csv").exists()]
    print(f"prices: {len(tickers)} tickers, {len(todo)} to fetch", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(workers) as pool:
        for i, _ in enumerate(pool.map(lambda t: _quiet(PL.prices, t), todo), 1):
            if i % 200 == 0:
                print(f"  prices {i}/{len(todo)} {time.time() - t0:.0f}s", flush=True)


def _at_cap(row: dict) -> bool:
    g = row.get("g_base")
    return g is not None and any(abs(g - c) < 1e-9 for c in (HI.GROWTH_CAP, HI.GROWTH_CAP_HIGH))


def evaluate_caps(facts, day, *, ticker, cik, sic) -> dict:
    row = M.evaluate(facts, day, ticker=ticker, cik=cik, sic=sic)
    row["caps"] = {}
    if not _at_cap(row):
        return row
    base, high = HI.GROWTH_CAP, HI.GROWTH_CAP_HIGH
    try:
        for cap in CAPS:
            HI.GROWTH_CAP, HI.GROWTH_CAP_HIGH = cap, max(high, cap)
            alt = M.evaluate(facts, day, ticker=ticker, cik=cik, sic=sic)
            row["caps"][f"{cap:.2f}"] = {k: alt.get(k) for k in CAP_COLUMNS}
    finally:
        HI.GROWTH_CAP, HI.GROWTH_CAP_HIGH = base, high
    return row


def run_date(as_of: date) -> None:
    day = PL.trading_day(as_of)
    index = PL.prices(PL.INDEX)
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"{as_of.isoformat()}.jsonl"
    done = set()
    if dest.exists():
        done = {json.loads(l)["cik"] for l in dest.read_text().splitlines() if l.strip()}
    cands = candidates(as_of)
    print(f"{as_of} (trading day {day}): {len(cands)} candidates, {len(done)} done", flush=True)
    t0, n = time.time(), 0
    with dest.open("a") as out:
        for cand in cands:
            if cand["cik"] in done:
                continue
            n += 1
            base = {"cik": cand["cik"], "company": cand["company"], "sic": cand.get("sic"),
                    "ticker_today": _ticker(cand), "as_of": as_of.isoformat(),
                    "trading_day": day.isoformat()}
            try:
                facts = PL.company_facts(cand["cik"])
                if facts is None:
                    out.write(json.dumps({**base, "skip": "no facts"}) + "\n")
                    continue
                pf = U.pit_float(facts, day)
                if pf is None or pf[0] < U.FLOAT_MIN:
                    out.write(json.dumps({**base, "skip": "below float line",
                                          "public_float": None if pf is None else pf[0]}) + "\n")
                    continue
                ticker = base["ticker_today"]
                row = evaluate_caps(facts, day, ticker=ticker or f"CIK{cand['cik']}",
                                    cik=cand["cik"], sic=cand.get("sic"))
                row.update(base, public_float=pf[0], price=None, returns={}, index_returns={})
                frame = PL.prices(ticker) if ticker else None
                got = PL.unadjusted_close(frame, day) if frame is not None else None
                if got is not None:
                    M.with_price(row, got[1], pf[0])
                    for c in row["caps"].values():
                        if c.get("fv_base") is not None and got[1] > 0:
                            c["fv_over_price"] = c["fv_base"] / got[1]
                    for h in PL.HORIZONS:
                        end = PL.years_after(day, h)
                        row["returns"][h] = PL.total_return(frame, day, end)
                        row["index_returns"][h] = PL.total_return(index, day, end)
                row["passes_quality"] = V.passes_quality(row) if row["quality"] else None
                row["measured_kill"] = V.measured_kill(row)
                row.pop("fcf_years", None)
                out.write(json.dumps(row, default=str) + "\n")
            except Exception as exc:  # noqa: BLE001 -- one name never stops the run
                out.write(json.dumps({**base, "skip": f"error: {type(exc).__name__}: {exc}"[:300],
                                      "trace": traceback.format_exc()[-800:]}) + "\n")
            out.flush()
            if n % 100 == 0:
                print(f"  {as_of}: {n} evaluated {time.time() - t0:.0f}s", flush=True)
    print(f"{as_of}: finished, {n} new rows", flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", action="append", type=date.fromisoformat)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--no-prefetch", action="store_true")
    a = ap.parse_args(argv)
    dates = a.date or list(U.TEST_DATES)
    if not a.no_prefetch:
        prefetch(dates, a.workers)
    for d in dates:
        run_date(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
