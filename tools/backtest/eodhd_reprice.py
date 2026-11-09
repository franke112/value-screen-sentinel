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
the last print (SVB: 106 USD), not at what the holders finally got. Two
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
                if CLEAN_SPIKES:
                    f = drop_spikes(f, symbol)
                _FRAMES[symbol] = f if len(f) else None
    return _FRAMES[symbol]


#: ROUND 2, ATTEMPTS #15 (found 2026-11-08 reading A1's rows): EODHD prints
#: one-day spikes -- NOLA-B.ST 4,858 between 476 and 492 on 2019-06-10,
#: BUFAB.ST 331,250 between 104 and 109, FAG.ST 199,125 on 2013-05-10; 98 in
#: the backtest's 2,145 series, 81 of them on four Stockholm days
#: (2013-05-10, 2019-06-10, 2019-06-17, 2019-08-05). The level-break guard
#: (M2) read each as the company ENDING, cut the series there and refused
#: every return whose prior year held one. A day on which the close AND the
#: adjusted close move more than SPIKE_FACTOR and the next day moves back,
#: its neighbours within 2x of each other, is a bad print and is dropped
#: before anything reads the series. A real level break does not come back
#: the next day and still reaches the guard.
SPIKE_FACTOR = 5.0
CLEAN_SPIKES = True
DROPPED_SPIKES: list[tuple[str, str]] = []


def drop_spikes(f: pd.DataFrame, symbol: str = "") -> pd.DataFrame:
    if len(f) < 3:
        return f
    bad = []
    for col in ("close", "adjusted_close"):
        x = f[col]
        up, back = x / x.shift(1), x.shift(-1) / x
        around = (x.shift(-1) / x.shift(1))
        hit = (((up > SPIKE_FACTOR) & (back < 1 / SPIKE_FACTOR)) |
               ((up < 1 / SPIKE_FACTOR) & (back > SPIKE_FACTOR))) & (around < 2) & (around > 0.5)
        bad.append(hit.fillna(False))
    drop = bad[0] & bad[1]
    if drop.any():
        DROPPED_SPIKES.extend((symbol, d) for d in f.index[drop])
        f = f[~drop]
    return f


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


#: M4 of the independent review 2026-11-07: a day on which the vendor's
#: ADJUSTED close moves more than this AND this far from the printed close is
#: an adjustment error (KOG.OL 2022-05-12: adjusted +36% on a close of -2.4%;
#: SAS.ST's 2020 rights issue: adjusted +46% on a close of -61%). A real
#: split, dividend or rights issue moves the printed close, never only the
#: adjusted one. A window holding such a day has no return (refused).
SUSPECT_MOVE = 0.15
SUSPECT_GAP = 0.10


def suspect_days(f: pd.DataFrame, start: date, end: date) -> list[str]:
    w = f[(f.index >= start.isoformat()) & (f.index <= end.isoformat())]
    w = w[(w["close"] > 0) & (w["adjusted_close"] > 0)]
    cr, ar = w["close"].pct_change(), w["adjusted_close"].pct_change()
    return list(w.index[(ar.abs() > SUSPECT_MOVE) & ((ar - cr).abs() > SUSPECT_GAP)])


#: Review 2026-11-08 M2: a LEVEL BREAK -- the close AND the adjusted close
#: moving together by more than this factor in one step, or a gap of more
#: than BREAK_GAP_DAYS between two trading days -- is another security under
#: the same ticker (COH.US after Coach became TPR, NCS.US, HIQ.ST), a
#: listing carried through a bankruptcy (HK.US) or a broken series
#: (ASRT.US at 0.0133). M4 cannot see it: the two series agree. The series
#: is cut at the break and judged as a delisting there; a break in the year
#: before the start refuses the return (the start price is suspect).
BREAK_FACTOR = 5.0
BREAK_GAP_DAYS = 365


def level_breaks(f: pd.DataFrame, start: date, end: date) -> list[str]:
    w = f[(f.index >= start.isoformat()) & (f.index <= end.isoformat())]
    w = w[(w["close"] > 0) & (w["adjusted_close"] > 0)]
    if len(w) < 2:
        return []
    c, a = w["close"], w["adjusted_close"]
    cr, ar = c / c.shift(1), a / a.shift(1)
    jump = ((cr > BREAK_FACTOR) | (cr < 1 / BREAK_FACTOR)) & ((ar > BREAK_FACTOR) | (ar < 1 / BREAK_FACTOR))
    days = pd.to_datetime(pd.Series(w.index, index=w.index))
    gap = days.diff().dt.days > BREAK_GAP_DAYS
    return list(w.index[jump | gap])


def total_return(f: pd.DataFrame, start: date, end: date, policy: str) -> tuple[float | None, str]:
    """(return, how): how is 'held', 'delisted-last' or 'delisted-bust';
    None with 'adjustment suspect' where `suspect_days` finds one."""
    a = on(f, start, "adjusted_close")
    if a is None or a[1] <= 0:
        return None, "no start"
    if level_breaks(f, start - timedelta(days=BREAK_GAP_DAYS), start):
        return None, "level break before the start: the start price is suspect"
    brk = level_breaks(f, start, end)
    if brk:
        # The series is another security, or a listing carried through a
        # bankruptcy, from the break on: the company ENDED there, and the
        # delisting policy below judges how.
        f = f[f.index < brk[0]]
    bad = suspect_days(f, start, end)
    if bad:
        return None, f"adjustment suspect ({bad[0]})"
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
    ap.add_argument("--suffix", default="",
                    help="write run-eodhd<suffix>/ and run-eodhd-bust<suffix>/ (a new attempt beside the old)")
    a = ap.parse_args(argv)
    cmap = cik_map()
    index = PL.prices(PL.INDEX)
    for policy, out in OUT.items():
        out = out.with_name(out.name + a.suffix) if a.suffix else out
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
