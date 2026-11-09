"""The pre-registered evaluation of the Nordic backtest
(reference/backtest/PREREG-NORDIC-CONFIRM-2026-11-07.md). Every number and
rule here was fixed and committed BEFORE the confirmation dates were run.

    .venv/bin/python -m tools.backtest.confirm_nordic --dev       # 2010-2021 (informational)
    .venv/bin/python -m tools.backtest.confirm_nordic --confirm   # 2022, 2023: THE result

S_d, per date: mean 3-year excess return of the cheaper two fifths by
fv/price (fifths 4 and 5) minus that of the dearer two (1 and 2). Excess is
against the equal-weighted return of every company over the size line that
date (delisted included; a collapse before delisting is -100%).

RANDOM TEST: within each date the fv/price labels are shuffled across the
valued names (10,000 draws, seed 20261107) and the mean of S_d over the
dates is recomputed; p = share of draws at least as large as the observed.

EXTERNAL FACIT (informational, decides nothing): Ken French's country
portfolios (F-F_International_Countries, value-weighted USD returns), BE/ME
High minus Low, compounded over the same months as each test window and
averaged over Sweden, Norway, Denmark and Finland; the sign is compared
with S_d.
"""
from __future__ import annotations

import argparse
import io
import json
import random
import re
import statistics as st
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

from . import nordic as N

H = "3"
DRAWS = 10_000
SEED = 20261107
MIN_VALUED = 25
FRENCH_URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
              "F-F_International_Countries.zip")
COUNTRIES = ("Sweden", "Norway", "Denmark", "Finland")


def usable(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("status") == "ok" and r.get("fv_over_price") is not None
            and r.get("returns", {}).get(H) is not None and r.get("index_returns", {}).get(H) is not None]


def spread(rs: list[dict], key=lambda r: r["fv_over_price"]) -> float:
    u = sorted(rs, key=key)
    k = len(u)
    fifth = [u[i * k // 5:(i + 1) * k // 5] for i in range(5)]
    ex = lambda part: st.mean(r["returns"][H] - r["index_returns"][H] for r in part)
    return (ex(fifth[3]) + ex(fifth[4])) / 2 - (ex(fifth[0]) + ex(fifth[1])) / 2


def fifths(rs: list[dict]) -> list[float]:
    u = sorted(rs, key=lambda r: r["fv_over_price"])
    k = len(u)
    return [st.mean(r["returns"][H] - r["index_returns"][H] for r in u[i * k // 5:(i + 1) * k // 5])
            for i in range(5)]


def random_test(by_date: dict[str, list[dict]], observed: float) -> float:
    rnd = random.Random(SEED)
    hits = 0
    for _ in range(DRAWS):
        vals = []
        for rs in by_date.values():
            labels = [r["fv_over_price"] for r in rs]
            rnd.shuffle(labels)
            order = dict(zip((id(r) for r in rs), labels))
            vals.append(spread(rs, key=lambda r: order[id(r)]))
        hits += st.mean(vals) >= observed
    return hits / DRAWS


_ZIP: list[bytes] = []


def _french_zip() -> bytes:
    if not _ZIP:
        req = urllib.request.Request(FRENCH_URL, headers={"User-Agent": "vss-research/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            _ZIP.append(r.read())
    return _ZIP[0]


def french_value_spread(start: date, months: int = 36) -> tuple[float | None, int]:
    """(mean over the four countries of compounded High-minus-Low BE/ME,
    months covered) for the window starting the month after `start`."""
    z = zipfile.ZipFile(io.BytesIO(_french_zip()))
    first = (start.year * 12 + start.month)          # May of the year = start month + 1
    want = [((first + i) // 12, (first + i) % 12 + 1) for i in range(months)]
    out, covered = [], 0
    for c in COUNTRIES:
        text = z.read(f"{c}.Dat").decode("latin-1").splitlines()
        # the FIRST block is value-weighted monthly returns
        rows = {}
        for line in text:
            m = re.match(r"^\s*(\d{4})(\d{2})\s+(.*)$", line)
            if m:
                key = (int(m.group(1)), int(m.group(2)))
                if key in rows:
                    break            # the next block begins
                vals = m.group(3).split()
                rows[key] = (float(vals[1]), float(vals[2]))     # BE/ME High, Low
        hi = lo = 1.0
        n = 0
        for ym in want:
            if ym in rows:
                h, l = rows[ym]
                if h > -99 and l > -99:
                    hi *= 1 + h / 100
                    lo *= 1 + l / 100
                    n += 1
        if n:
            out.append(hi - lo)
            covered = max(covered, n)
    return (st.mean(out) if out else None), covered


def evaluate(directory: Path, label: str) -> dict:
    by_date = {}
    for f in sorted(directory.glob("*.jsonl")):
        rs = usable([json.loads(l) for l in f.read_text().splitlines() if l.strip()])
        if len(rs) >= MIN_VALUED:
            by_date[f.stem] = rs
    per = {d: spread(rs) for d, rs in by_date.items()}
    observed = st.mean(per.values())
    p = random_test(by_date, observed)
    lines = [f"## {label}", "",
             "| Test date | valued | fifth 1 | 2 | 3 | 4 | 5 | S_d (pp) | Ken French HML BE/ME (pp, months) |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    agree = n_f = 0
    for d, rs in by_date.items():
        fv = fifths(rs)
        try:
            kf, months = french_value_spread(date.fromisoformat(d))
        except Exception as exc:  # noqa: BLE001 -- informational only
            kf, months = None, 0
            print(f"Ken French not read for {d}: {type(exc).__name__}")
        if kf is not None:
            n_f += 1
            agree += (kf > 0) == (per[d] > 0)
        lines.append(f"| {d} | {len(rs)} | " + " | ".join(f"{x * 100:+.1f}" for x in fv)
                     + f" | {per[d] * 100:+.1f} | "
                     + (f"{kf * 100:+.1f} ({months} mo)" if kf is not None else "–") + " |")
    lines += ["", f"Mean S_d: **{observed * 100:+.1f} pp**; S_d > 0 on "
                  f"{sum(v > 0 for v in per.values())} of {len(per)} dates; random test "
                  f"(shuffled fv/price, {DRAWS:,} draws, seed {SEED}): **p = {p:.4f}**; "
                  f"Ken French sign agreement {agree} of {n_f}."]
    return {"per": per, "mean": observed, "p": p, "lines": lines}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args(argv)
    if a.dev:
        r = evaluate(N.OUT, "Development 2010-2021 (informational; already seen)")
        print("\n".join(r["lines"]))
    if a.confirm:
        r = evaluate(N.CONFIRM_OUT, "CONFIRMATION 2022-04-30 and 2023-04-30 (the one run)")
        both = all(v > 0 for v in r["per"].values()) and len(r["per"]) == 2
        sig = r["p"] < 0.05
        verdict = ("CONFIRMED" if both and sig else
                   "REFUTED" if r["mean"] <= 0 else "NOT CONFIRMED, NOT REFUTED")
        print("\n".join(r["lines"]))
        print(f"\nVERDICT (pre-registered rule): {verdict} -- S_d > 0 on both dates: {both}; p < 0.05: {sig}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
