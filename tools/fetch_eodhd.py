"""Fetch EODHD fundamentals ONCE, for private use only -- never published.

    .venv/bin/python tools/fetch_eodhd.py --check            # quota and one Nordic test, nothing stored
    .venv/bin/python tools/fetch_eodhd.py --budget 50000     # fetch until this many calls are spent today
    .venv/bin/python tools/fetch_eodhd.py --status           # how far it has come

WHAT AND WHY. The owner bought one month of EODHD "Equity analyst"
(2026-11-07) to get, once, statements with dates for every US and Nordic
common stock, active AND delisted: a backtest without survivorship and long
Nordic histories for the screener. EODHD is a SECONDARY source: it never
enters config/manual and never verifies a figure (E21, E151); it screens,
backtests and flags.

WHERE. data/eodhd/fundamentals/<SYMBOL>.json.gz (data/ is gitignored and is
never copied to ~/vss-public). The symbol list is read, not fetched, from
data/eodhd/symbols.csv (vss's own copy of the home machine's list).

THE QUOTA is SHARED with the home machine: 100,000 calls a day, 1,000 a
minute. A fundamentals call costs 10. Before every batch the tool asks
EODHD's /api/user how many calls today has used and stops when the next
batch would leave less than --reserve for the home machine. It keeps under
~8 REQUESTS a second (the minute limit counts requests; a fundamentals request costs 10 of the day's calls), 30 in flight, Retry-After honoured on a 429. A 402/429 stops the run; the next run resumes, skipping
every file already on disk.

THE KEY is read from ~/.config/eodhd/env (EODHD_API_KEY=...), never printed,
never logged; every error message has it removed.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "eodhd" / "fundamentals"
STATUS = ROOT / "data" / "eodhd" / "fundamentals_status.csv"
SYMBOLS = ROOT / "data" / "eodhd" / "symbols.csv"     # vss's own copy (2026-11-07)
KEY_FILE = Path.home() / ".config" / "eodhd" / "env"
API = "https://eodhd.com/api"
COST = 10                    # calls per fundamentals request
WORKERS = 70                 # requests in flight; each answer takes ~4-5 s
# EODHD's MINUTE limit counts REQUESTS (1,000-1,200 a minute, shared with the
# home machine), not calls: a fundamentals request is ONE request costing 10
# of the DAY's calls (EODHD "API Limits", 2026-11-07). 8 a second is 480 a
# minute and leaves more than half the minute to the home machine.
MAX_REQUESTS_PER_SECOND = 15   # 900 a minute of the 1,000; the X-RateLimit brake covers the home machine
MIN_MINUTE_LEFT = 150        # below this many requests left in the minute: wait it out
NORDIC = ("ST", "OL", "CO", "HE")


def key() -> str:
    for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("EODHD_API_KEY="):
            k = line.split("=", 1)[1].strip().strip('"').strip("'")
            if k:
                return k
    raise SystemExit(f"no EODHD_API_KEY in {KEY_FILE}")


_MINUTE_LEFT = [10_000]
_RETRY_AFTER = [30]


def _get(url: str, k: str, timeout: int = 90) -> tuple[int, bytes]:
    req = urllib.request.Request(url + ("&" if "?" in url else "?") + f"api_token={k}&fmt=json",
                                 headers={"User-Agent": "vss-private/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            left = r.headers.get("X-RateLimit-Remaining")
            if left and left.isdigit():
                _MINUTE_LEFT[0] = int(left)
            return r.status, r.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            wait = exc.headers.get("Retry-After") or "30"
            _RETRY_AFTER[0] = int(wait) if str(wait).isdigit() else 30
        return exc.code, b""
    except Exception as exc:  # noqa: BLE001 -- reported without the key
        raise RuntimeError(str(exc).replace(k, "***")) from None


def used_today(k: str) -> tuple[int, int]:
    """(calls used today, daily limit) from /api/user."""
    code, body = _get(f"{API}/user", k)
    if code != 200:
        raise RuntimeError(f"/api/user answered HTTP {code}")
    d = json.loads(body)
    # bought calls (extraLimit) add to the day's ceiling
    return (int(d.get("apiRequests") or 0),
            int(d.get("dailyRateLimit") or 100000) + int(d.get("extraLimit") or 0))


def queue() -> list[str]:
    """Common stocks, Nordic first, then US active, then US delisted."""
    rows = list(csv.DictReader(SYMBOLS.open(encoding="utf-8")))
    rows = [r for r in rows if (r.get("Type") or "").lower() == "common stock"]

    def rank(r):
        nordic = r["suffix"] in NORDIC
        delisted = r["delisted"] == "True"
        return (0 if nordic else 1 if not delisted else 2, r["symbol"])
    return [r["symbol"] for r in sorted(rows, key=rank)]


def have(symbol: str) -> bool:
    return (OUT / f"{symbol}.json.gz").exists()


import threading
_LOCK = threading.Lock()


def log(symbol: str, code: int, size: int) -> None:
    with _LOCK:
        _log(symbol, code, size)


def _log(symbol: str, code: int, size: int) -> None:
    new = not STATUS.exists()
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    with STATUS.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["symbol", "fetched_at", "http", "bytes"])
        w.writerow([symbol, datetime.now().isoformat(timespec="seconds"), code, size])


def fetch_one(symbol: str, k: str) -> int:
    if _MINUTE_LEFT[0] < MIN_MINUTE_LEFT:      # the shared minute is nearly spent
        time.sleep(15)
        _MINUTE_LEFT[0] = 10_000
    for _ in range(4):              # 429: the minute is full -- wait as told, then again
        code, body = _get(f"{API}/fundamentals/{symbol}", k)
        if code != 429:
            break
        time.sleep(_RETRY_AFTER[0])
    if code == 200 and body.strip() not in (b"", b"{}", b"[]"):
        OUT.mkdir(parents=True, exist_ok=True)
        tmp = OUT / f"{symbol}.json.gz.part"
        tmp.write_bytes(gzip.compress(body))
        tmp.rename(OUT / f"{symbol}.json.gz")
    log(symbol, code, len(body))
    return code


def refresh_queue(max_age_days: float) -> list[str]:
    """ACTIVE Nordic common stocks whose file is older than `max_age_days`:
    the weekly Nordic screen re-reads them (tools/nordic_screen.py)."""
    rows = list(csv.DictReader(SYMBOLS.open(encoding="utf-8")))
    cut = time.time() - max_age_days * 86400
    out = []
    for r in rows:
        if r["suffix"] in NORDIC and r["delisted"] != "True" and (r.get("Type") or "").lower() == "common stock":
            f = OUT / f"{r['symbol']}.json.gz"
            if not f.exists() or f.stat().st_mtime < cut:
                out.append(r["symbol"])
    return out


def run(budget: int, reserve: int, refresh_days: float | None = None) -> int:
    k = key()
    if refresh_days is not None:
        todo = refresh_queue(refresh_days)
        print(f"refresh: {len(todo)} active Nordic files older than {refresh_days} days", flush=True)
        if todo:
            # Between subscription months the key has no fundamentals access:
            # one probe says so, and the files on disk are used as they are
            # (owner 2026-11-07: subscribe one month after each report season).
            code, _ = _get(f"{API}/fundamentals/VOLV-B.ST", k)
            if code != 200:
                print(f"no fundamentals access now (HTTP {code}): the files on disk are used "
                      f"as they are; subscribe a month after the next report season", flush=True)
                return 0
        return _fetch(todo, k, budget, reserve)
    todo = [s for s in queue() if not have(s)]
    done_codes = {}
    if STATUS.exists():   # a symbol EODHD answered 404/empty for is not asked again
        for r in csv.DictReader(STATUS.open(encoding="utf-8")):
            done_codes[r["symbol"]] = r["http"]
    todo = [s for s in todo if done_codes.get(s) not in ("404", "200")]
    return _fetch(todo, k, budget, reserve)


def _fetch(todo: list[str], k: str, budget: int, reserve: int) -> int:
    print(f"{len(todo)} symbols to fetch", flush=True)
    spent = 0
    from concurrent.futures import ThreadPoolExecutor
    batch = 150                     # quota checked before every batch (/api/user costs nothing)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for start in range(0, len(todo), batch):
            chunk = todo[start:start + batch]
            used, limit = used_today(k)
            if used + COST * len(chunk) > limit - reserve:
                print(f"stopping: {used:,} of {limit:,} calls used today, "
                      f"{reserve:,} kept for the home machine", flush=True)
                break
            if spent + COST * len(chunk) > budget:
                print(f"stopping: this run's budget of {budget:,} calls is spent", flush=True)
                break
            t0 = time.monotonic()
            codes = list(pool.map(lambda s: (s, fetch_one(s, k)), chunk))
            spent += COST * len(chunk)
            for s, code in codes:
                if code != 200:
                    print(f"{s}: HTTP {code}", flush=True)
            if any(code == 402 for _, code in codes):
                print("stopping: HTTP 402 -- the day's calls and the extra calls are spent", flush=True)
                break
            print(f"{start + len(chunk):>6} {chunk[-1]} ({spent:,} calls this run)", flush=True)
            # never faster than MAX_REQUESTS_PER_SECOND, whatever the latency
            floor = len(chunk) / MAX_REQUESTS_PER_SECOND
            time.sleep(max(0.0, floor - (time.monotonic() - t0)))
    print(f"done: {spent:,} calls this run; {sum(1 for _ in OUT.glob('*.json.gz')):,} files on disk")
    return 0


def check() -> int:
    k = key()
    used, limit = used_today(k)
    print(f"quota: {used:,} of {limit:,} calls used today")
    code, body = _get(f"{API}/fundamentals/VOLV-B.ST", k)
    d = json.loads(body) if code == 200 else {}
    q = (d.get("Financials", {}).get("Income_Statement", {}).get("quarterly") or {})
    h = (d.get("Earnings", {}).get("History") or {})
    print(f"VOLV-B.ST: HTTP {code}, {len(q)} quarters, {len(h)} earnings dates "
          f"(nothing stored by --check)")
    return 0 if code == 200 else 1


def status() -> int:
    total = len(queue())
    got = sum(1 for _ in OUT.glob("*.json.gz")) if OUT.exists() else 0
    size = sum(p.stat().st_size for p in OUT.glob("*.json.gz")) if OUT.exists() else 0
    print(f"{got:,} of {total:,} common stocks fetched, {size / 1e9:.2f} GB")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--budget", type=int, default=50000, help="calls this run may spend")
    ap.add_argument("--refresh-nordic", type=float, default=None, metavar="DAYS",
                    help="re-fetch ACTIVE Nordic files older than DAYS (the weekly screen)")
    ap.add_argument("--reserve", type=int, default=10000,
                    help="calls a day left for the home machine")
    a = ap.parse_args(argv)
    if a.check:
        return check()
    if a.status:
        return status()
    return run(a.budget, a.reserve, a.refresh_nordic)


if __name__ == "__main__":
    sys.exit(main())
