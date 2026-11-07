"""Re-price the full run with EODHD prices -- delisted companies included.

    .venv/bin/python -m tools.backtest.eodhd_reprice            # writes run-eodhd/ and run-eodhd-bust/
    .venv/bin/python -m tools.backtest.measure --run-dir data/backtest/run-eodhd --horizon 3

WHY. The full run (2026-10-29) was SURVIVORS ONLY: prices came from the
vendor by TODAY's ticker, so a company delisted since had no price and was
counted, never measured -- 849 of 1,985 valued names in 2016. The valuations
themselves were already point-in-time (SEC companyfacts clipped to the test
date) and are NOT redone; only the price-dependent columns are.

THE PRICES are the home machine's EODHD download (read only):
data/eodhd/eod/<SYMBOL>.csv.gz (vss's own copy) -- unadjusted `close` and
`adjusted_close` (splits and dividends), active and delisted, from 2007. A
CIK is matched to its EODHD symbol through the `General.CIK` field of the
EODHD fundamentals (data/eodhd/fundamentals/); where a CIK has several
symbols, the one trading on the test day with the larger volume wins.

A COMPANY THAT STOPPED TRADING BEFORE THE HORIZON. EODHD's series ends at
the last print (a failed bank's last trade), not at what the holders finally got. Two
policies, both written, so the result is shown under each:
- `last` (run-eodhd/): the last price stands and the money waits in cash --
  right for a takeover, kind to a failure;
- `bust` (run-eodhd-bust/): a company whose last close was under a third of
  its own high in the year before, or under 1 USD, is a TOTAL LOSS (-100%);
  any other ends at its last price as under `last`.
The index (^SP500TR) runs to the horizon end either way.

Nothing here changes a valuation, a test or a pass mark: `measure` reads the
new rows exactly as it read the old.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import io
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from . import method as M
from . import pilot as PL
from . import run as R
from . import universe as U

FUND = Path(__file__).resolve().parents[2] / "data" / "eodhd" / "fundamentals"
# vss's OWN copy (2026-11-07): the DonkeyInvestor directory it was read from
# was archived; extracted from ~/archive/donkey-eodhd-sec-2026-11-07.tar.zst
# (SHA256SUMS verified) into data/eodhd/eod/, gitignored, private
EOD = Path(__file__).resolve().parents[2] / "data" / "eodhd" / "eod"
CIK_MAP = U.ROOT / "eodhd_cik_map.json"
OUT = {"last": U.ROOT / "run-eodhd", "bust": U.ROOT / "run-eodhd-bust"}
STALE_DAYS = 7
BUST_FRACTION = 1 / 3
BUST_PRICE = 1.0


def cik_map() -> dict[int, list[str]]:
    if CIK_MAP.exists():
        return {int(k): v for k, v in json.loads(CIK_MAP.read_text()).items()}
    out: dict[int, list[str]] = {}
    for p in sorted(FUND.glob("*.US.json.gz")):
        g = (json.loads(gzip.decompress(p.read_bytes())).get("General") or {})
        cik = str(g.get("CIK") or "").strip()
        if cik.isdigit():
            out.setdefault(int(cik), []).append(p.name[:-len(".json.gz")])
    CIK_MAP.write_text(json.dumps(out))
    return out


_FRAMES: dict[str, pd.DataFrame | None] = {}


def frame(symbol: str) -> pd.DataFrame | None:
    if symbol not in _FRAMES:
        p = EOD / f"{symbol}.csv.gz"
        if not p.exists():
            _FRAMES[symbol] = None
        else:
            f = pd.read_csv(io.BytesIO(gzip.decompress(p.read_bytes())))
            if not {"date", "close", "adjusted_close", "volume"} <= set(f.columns):
                _FRAMES[symbol] = None          # an empty download: no price, not a guess
            else:
                f = f.dropna(subset=["close", "adjusted_close"]).set_index("date").sort_index()
                _FRAMES[symbol] = f if len(f) else None
    return _FRAMES[symbol]


def on(f: pd.DataFrame, day: date, col: str = "close") -> tuple[date, float] | None:
    rows = f[f.index <= day.isoformat()]
    if not len(rows):
        return None
    when = date.fromisoformat(rows.index[-1])
    if (day - when).days > STALE_DAYS:
        return None
    return when, float(rows[col].iloc[-1])


def symbol_for(cik: int, day: date, cmap: dict[int, list[str]]) -> str | None:
    best, vol = None, -1.0
    for s in cmap.get(cik, []):
        f = frame(s)
        if f is None or on(f, day) is None:
            continue
        window = f[(f.index <= day.isoformat()) &
                   (f.index > (day - timedelta(days=30)).isoformat())]
        v = float(window["volume"].median()) if len(window) else 0.0
        if v > vol:
            best, vol = s, v
    return best


def total_return(f: pd.DataFrame, start: date, end: date, policy: str) -> tuple[float | None, str]:
    """(return, how): how is 'held', 'delisted-last' or 'delisted-bust'."""
    a = on(f, start, "adjusted_close")
    if a is None or a[1] <= 0:
        return None, "no start"
    b = on(f, end, "adjusted_close")
    if b is not None:
        return b[1] / a[1] - 1, "held"
    last_day = date.fromisoformat(f.index[-1])
    if last_day >= end:      # traded past the end but a gap at it: not a delisting
        return None, "gap"
    last_adj = float(f["adjusted_close"].iloc[-1])
    if policy == "bust":
        year = f[f.index > (last_day - timedelta(days=365)).isoformat()]
        high = float(year["adjusted_close"].max()) if len(year) else last_adj
        if last_adj < BUST_FRACTION * high or float(f["close"].iloc[-1]) < BUST_PRICE:
            return -1.0, "delisted-bust"
    return last_adj / a[1] - 1, "delisted-last"


def reprice(row: dict, cmap, index, policy: str) -> dict:
    r = copy.deepcopy(row)
    day = date.fromisoformat(r["trading_day"])
    sym = symbol_for(int(r["cik"]), day, cmap)
    for k in ("price", "market_cap", "float_over_cap", "cap_check", "fv_over_price", "ev",
              "ebit_ev", "fcf_yield", "roc"):
        r.pop(k, None)
    r.update(price=None, returns={}, index_returns={}, price_source="eodhd",
             eodhd_symbol=sym, exit={})
    for c in (r.get("caps") or {}).values():
        c.pop("fv_over_price", None)
    if sym is None:
        return r
    f = frame(sym)
    got = on(f, day)
    if got is None:
        return r
    M.with_price(r, got[1], r.get("public_float"))
    for c in (r.get("caps") or {}).values():
        if c.get("fv_base") is not None and got[1] > 0:
            c["fv_over_price"] = c["fv_base"] / got[1]
    for h in PL.HORIZONS:
        end = PL.years_after(day, h)
        ret, how = total_return(f, day, end, policy)
        r["returns"][h] = ret
        r["exit"][h] = how
        r["index_returns"][h] = PL.total_return(index, day, end)
    return r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", action="append", type=date.fromisoformat)
    a = ap.parse_args(argv)
    cmap = cik_map()
    index = PL.prices(PL.INDEX)
    for policy, out in OUT.items():
        out.mkdir(parents=True, exist_ok=True)
        for d in a.date or list(U.TEST_DATES):
            src = R.OUT / f"{d.isoformat()}.jsonl"
            rows = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]
            new, priced, delisted = [], 0, 0
            for row in rows:
                if row.get("status") != "ok":
                    new.append(row)
                    continue
                r = reprice(row, cmap, index, policy)
                priced += r["price"] is not None
                delisted += any(v.startswith("delisted") for v in r["exit"].values())
                new.append(r)
            (out / f"{d.isoformat()}.jsonl").write_text(
                "".join(json.dumps(r, default=str) + "\n" for r in new))
            print(f"{policy} {d}: {sum(1 for r in rows if r.get('status') == 'ok')} valued, "
                  f"{priced} priced, {delisted} delisted before a horizon", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
