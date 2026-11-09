"""Shared engine for the wrez-devour tests of November 2026 (stops,
concentration, the band / momentum filter, F-score and accruals).

Nothing here values anything: it reads the rows the existing runs wrote
(data/backtest/run-eodhd-bust-m5, run-eodhd-m5, nordic-m5) and the EODHD
price files, and builds DAILY value paths for a position so a stop, a
re-entry, a drawdown or a rebalance can be measured. Every pre-registration
is in reference/backtest/ATTEMPTS.md.

A PATH is the adjusted close relative to the entry day, with exactly the
guards and delisting policies of `eodhd_reprice.total_return` (a level break
before the start refuses it; a break inside cuts the series there; a vendor
adjustment fault refuses it; a series ending before the horizon is a
delisting, judged by `last` or `bust`). `path(...)[-1] - 1` equals
`total_return(...)`, which `check_paths` verifies on every row.
"""
from __future__ import annotations

import json
import statistics
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from . import eodhd_reprice as EP
from . import measure as MS
from . import measure_key as MK
from . import pilot as PL

ROOT = Path(__file__).resolve().parents[2]
BT = ROOT / "data" / "backtest"
#: output directories carry the Nordic run they read (attempt #14 onward)
SUFFIX = "-m6"
#: ROUND 2 (ATTEMPTS #15): DEVOUR_LB=on|off picks the rows with or without
#: the level-break guard (the -nolb twins from `nolb.py`) and switches the
#: guard in the path engine to match; outputs go to *-r2-lb / *-r2-nolb.
#: Signals that do not depend on returns stay in devour-fscore-m6.
import os as _os
LB = _os.environ.get("DEVOUR_LB")
SIGNALS = BT / "devour-fscore-m6"
MARKETS = {
    "nordic": ("nordic-m6", "bust"),      # m5 until attempt #14 (Tomra's currency)
    "us-bust": ("run-eodhd-bust-m5", "bust"),
    "us-last": ("run-eodhd-m5", "last"),
}
#: the two halves each result must hold in (pre-registered)
HALVES = {
    "nordic": (("2010", "2011", "2012", "2013", "2014", "2015"),
               ("2016", "2017", "2018", "2019", "2020", "2021")),
    "us": (("2016", "2017", "2018"), ("2019", "2020")),
}


if LB in ("on", "off", "clean"):
    # on / off read the stored series as they were (no spike cleaning);
    # clean drops EODHD's one-day spikes and keeps the guard (ATTEMPTS #15)
    SUFFIX = f"-r2-{ {'on': 'lb', 'off': 'nolb', 'clean': 'clean'}[LB] }"
    EP.CLEAN_SPIKES = LB == "clean"
    if LB == "off":
        MARKETS = {k: (v[0] + "-nolb", v[1]) for k, v in MARKETS.items()}
        EP.level_breaks = lambda f, start, end: []
    if LB == "clean":
        MARKETS = {k: (v[0] + "-clean", v[1]) for k, v in MARKETS.items()}
        # nordic-m7 (ATTEMPTS #17): the engine re-run with the quarter-start
        # fix, on cleaned prices; its returns equal nordic-m6-clean's
        MARKETS["nordic"] = ("nordic-m7", "bust")
else:
    EP.CLEAN_SPIKES = False     # round 1's figures were made on uncleaned series


def half_of(market: str, d: str) -> int:
    first, _ = HALVES["nordic" if market == "nordic" else "us"]
    return 0 if d[:4] in first else 1


#: ATTEMPTS #22 (A8): DEVOUR_NOSCA=1 drops SCA's rows on 2011-2017 (a close
#: restated for the Essity spin-off); outputs get "-nosca"
NOSCA = _os.environ.get("DEVOUR_NOSCA") == "1"
if NOSCA:
    SUFFIX += "-nosca"


def load(market: str, fill: bool = True) -> dict[str, list[dict]]:
    run, _ = MARKETS[market]
    data = MS.load(BT / run)
    if NOSCA:
        for d in data:
            if "2011" <= d[:4] <= "2017":
                data[d] = [r for r in data[d] if (r.get("symbol") or "") not in ("SCA-A.ST", "SCA-B.ST")]
    if market == "nordic":
        assert not any(d >= "2022" for d in data), "the locked confirmation dates are not used"
        if fill:
            fill_nordic_assets(data)
    return data


def fill_nordic_assets(data) -> None:
    """The Nordic run's rows carry total assets on 11 of 2,037 usable rows:
    EODHD's yearly balance sheet seldom has a known date, so
    `method.annual_instant` finds none and the E43 key cannot rank. The
    assets AT the EBIT year's end, read from a 10-K or 10-Q entry of that
    day (`fscore_accruals.signals_cut`), are filled in where the row has
    none, and the row is marked `_assets_filled`. Found 2026-11-08 before
    any Nordic E43 result was read."""
    p = SIGNALS / "signals-nordic.jsonl"
    if not p.exists():
        raise SystemExit("run `python -m tools.backtest.fscore_accruals --signals` first (Nordic assets)")
    sig = {}
    for line in p.read_text().splitlines():
        x = json.loads(line)
        sig[(x["date"], str(x["id"]))] = x.get("assets_fy")
    for d, rows in data.items():
        for r in rows:
            if not r.get("assets") and sig.get((d, str(r.get("cik")))):
                r["assets"] = sig[(d, str(r.get("cik")))]
                r["_assets_filled"] = True


def symbol(r: dict) -> str | None:
    return r.get("eodhd_symbol") or r.get("symbol")


def start_day(r: dict) -> date:
    return date.fromisoformat(r.get("trading_day") or r["as_of"])


# --- selections -------------------------------------------------------------

def fifth(rows: list[dict], key, best: bool = True) -> list[dict]:
    """The fifth with the HIGHEST key (best=True) among rows with a key, as
    `measure.quintiles` cuts it (sorted ascending, the top k//5 slice)."""
    rs = sorted((r for r in rows if key(r) is not None), key=key)
    k = len(rs)
    if k < 25:
        return []
    return rs[4 * k // 5:] if best else rs[:k // 5]


def key_rank(rows: list[dict]) -> dict[int, int]:
    """E43 rank sum (lower = better) by id(row), as `measure_key.key_order`."""
    rs = [r for r in rows if r.get("ebit") is not None and r.get("assets") and r.get("ebit_ev") is not None]
    op = {id(r): i for i, r in enumerate(sorted(rs, key=lambda r: -r["ebit"] / r["assets"]))}
    ey = {id(r): i for i, r in enumerate(sorted(rs, key=lambda r: -r["ebit_ev"]))}
    return {id(r): op[id(r)] + ey[id(r)] for r in rs}


def key_best_fifth(rows: list[dict]) -> list[dict]:
    """The best fifth by the key, sliced as `measure_key.fifths` slices it."""
    rs = MK.key_order(rows)
    if len(rs) < 25:
        return []
    return rs[:len(rs) // 5]


def top_key(rows: list[dict], n: int) -> list[dict]:
    return MK.key_order(rows)[:n]


def top_fvp(rows: list[dict], n: int) -> list[dict]:
    return MS.top(rows, n, MS.fv_ratio)


# --- paths -------------------------------------------------------------------

def path(sym: str | None, start: date, end: date, policy: str) -> pd.Series | None:
    """Daily value relative to the entry close (1.0 on the entry day), index
    the trading days from start to `end` (ISO strings). After a delisting
    the value is flat at its last level (`last`, or `bust` when the collapse
    test fails) or 0 from the day after the last print (`bust`). None where
    `total_return` gives no return."""
    if not sym:
        return None
    f = EP.frame(sym)
    if f is None:
        return None
    a = EP.on(f, start, "adjusted_close")
    if a is None or a[1] <= 0:
        return None
    if EP.level_breaks(f, start - timedelta(days=EP.BREAK_GAP_DAYS), start):
        return None
    brk = EP.level_breaks(f, start, end)
    if brk:
        f = f[f.index < brk[0]]
    if EP.suspect_days(f, start, end):
        return None
    w = f[(f.index > start.isoformat()) & (f.index <= end.isoformat())]["adjusted_close"] / a[1]
    s = pd.concat([pd.Series([1.0], index=[start.isoformat()]), w])
    b = EP.on(f, end, "adjusted_close")
    if b is not None:
        return s
    last_day = date.fromisoformat(f.index[-1])
    if last_day >= end:
        return None                      # a gap at the end, not a delisting
    if policy == "bust":
        year = f[f.index > (last_day - timedelta(days=365)).isoformat()]
        high = float(year["adjusted_close"].max()) if len(year) else float(f["adjusted_close"].iloc[-1])
        last_adj = float(f["adjusted_close"].iloc[-1])
        if last_adj < EP.BUST_FRACTION * high or float(f["close"].iloc[-1]) < EP.BUST_PRICE:
            nxt = (last_day + timedelta(days=1)).isoformat()
            s = pd.concat([s, pd.Series([0.0], index=[nxt])])
    s = pd.concat([s, pd.Series([s.iloc[-1]], index=[end.isoformat()])])
    return s[~s.index.duplicated(keep="last")]


def month_ends(s: pd.Series) -> set[str]:
    idx = pd.Index(s.index)
    months = idx.str[:7]
    return set(pd.Series(idx, index=idx).groupby(months.values).max().values)


#: ATTEMPTS #18 (A4): cost per trade, ASSUMPTIONS stated there. Avanza
#: courtage Mini 0.25 % (min 1 SEK) or Small max(39 SEK, 0.15 %) at a
#: position of 11,400 SEK (6 % of 190,000, E157); currency exchange 0.25 %
#: on every non-SEK trade; half the bid-ask spread by market cap (USD).
#: KEPT at 11,400 so #18 reproduces: the 190,000 base was corrected on
#: 2026-11-08 to 248,476 (Avanza overview), 6 % = 14,909 SEK. A rerun of
#: #18 on the new base is a new attempt, not an edit of this constant.
POSITION_SEK = 11_400
COURTAGE = {"mini": 0.0025, "small": max(39 / POSITION_SEK, 0.0015)}
FX_FEE = 0.0025
HALF_SPREAD = {"nordic": ((10e9, 0.0005), (2e9, 0.0010), (0, 0.0030)),
               "us": ((10e9, 0.0002), (2e9, 0.0005), (0, 0.0015))}
COST = _os.environ.get("DEVOUR_COST")          # None, "mini" or "small"
if COST:
    SUFFIX += f"-cost-{COST}"


def trade_cost(r: dict, market: str, broker: str | None = None) -> float:
    broker = broker or COST
    if not broker:
        return 0.0
    m = "nordic" if market == "nordic" else "us"
    cap = r.get("market_cap_usd") if m == "nordic" else r.get("market_cap")
    spread = next(v for floor, v in HALF_SPREAD[m] if (cap or 0) >= floor)
    fx = FX_FEE if (m == "us" or (r.get("currency") or "SEK") != "SEK") else 0.0
    return COURTAGE[broker] + fx + spread


def with_stop(s: pd.Series, stop: float | None, requalify=None, cost: float = 0.0) -> tuple[pd.Series, int]:
    """As `_with_stop`, with `cost` charged on every trade: the first buy,
    each stop sale, each re-entry and the sale at the horizon (nothing is
    left to sell after a bust)."""
    out, n = _with_stop(s, stop, requalify, cost)
    return out, n


def _with_stop(s: pd.Series, stop: float | None, requalify=None, cost: float = 0.0) -> tuple[pd.Series, int]:
    """Apply a stop to a path: out at the first close at or below entry x
    (1 - stop), then cash. With `requalify(value)` the position is bought
    back at the first month-end close after the exit at which
    `requalify(value_relative_to_first_entry)` is true, the stop reset at the
    new entry. Returns (the sleeve's value path, number of stops)."""
    if s is None:
        return s, 0
    if stop is None:
        if not cost:
            return s, 0
        out = s * (1 - cost)
        if out.iloc[-1] > 0:
            out.iloc[-1] *= 1 - cost
        return out, 0
    vals, idx = s.values, list(s.index)
    me = month_ends(s) if requalify else set()
    out = [1.0 - cost]
    sleeve, entry, held, stops, last = 1.0 - cost, 1.0, True, 0, 1.0
    for i in range(1, len(vals)):
        v = vals[i]
        if held:
            sleeve_now = sleeve * (v / last) if last > 0 else 0.0
            if v <= entry * (1 - stop) and v > 0:
                held, stops = False, stops + 1
                sleeve_now *= 1 - cost                   # the stop sale
            sleeve, last = sleeve_now, v
            if v == 0:
                held = False             # a delisting at zero: the sleeve is gone
        elif requalify and idx[i] in me and v > 0 and requalify(v) and i < len(vals) - 1:
            held, entry, last = True, v, v
            sleeve *= 1 - cost                           # the re-entry buy
        out.append(sleeve)
    if held and out[-1] > 0:
        out[-1] *= 1 - cost                              # the sale at the horizon
    return pd.Series(out, index=idx), stops


def max_drawdown(p: pd.Series) -> float:
    peak = p.cummax()
    return float((p / peak - 1).min())


def portfolio_path(paths: list[pd.Series]) -> pd.Series | None:
    """Equal weight at the start, then buy and hold (each sleeve its own)."""
    paths = [p for p in paths if p is not None and len(p)]
    if not paths:
        return None
    df = pd.concat(paths, axis=1).sort_index().ffill()
    return df.mean(axis=1)


def index_path(start: date, end: date) -> pd.Series | None:
    f = PL.prices(PL.INDEX)
    w = f[(f.index >= start.isoformat()) & (f.index <= end.isoformat())]["Adj Close"]
    return None if not len(w) else w / w.iloc[0]


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else None


def pp(x, d=1):
    return "–" if x is None else f"{100 * x:+.{d}f}"


def write_jsonl(path_: Path, rows) -> None:
    path_.parent.mkdir(parents=True, exist_ok=True)
    path_.write_text("".join(json.dumps(r, default=str) + "\n" for r in rows))
