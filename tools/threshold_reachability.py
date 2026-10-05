#!/usr/bin/env python3
"""Threshold reachability -- has a price at or below today's MBP ever existed?

Measurement for reports/THRESHOLD-REACHABILITY-2026-08-30.md. READ-ONLY: it
fetches ten years of prices fresh from yfinance and writes nothing to the
store, the watchlist or any config. Its only output is markdown on stdout (or
the --out path) and an optional CSV cache of the fetched series in --cache.

What it does, per name:

  1. takes the maximum buy price AS IT STANDS TODAY (the strike records and
     the watchlist, hard-coded below with their provenance), reproduces it from
     the linked run record through vss.valuation as a check, and holds it
     FIXED;
  2. walks that fixed figure back through ten years of split-adjusted,
     dividend-UNADJUSTED closes;
  3. counts EPISODES (consecutive closes at or below the MBP are one), takes
     the forward 1/3/5-year return from each first touch, and compares it with
     the S&P 500 (total return, ^SP500TR) and OMXS30 (price index, ^OMX -- no
     gross-index series is available on Yahoo, so that comparison understates
     the index by its dividend yield, roughly 2-4pp/year);
  4. records the deepest the price ever got below the threshold, and the
     drawdown from the trailing 52-week high at each first touch (Gate 1's
     15-50% band);
  5. (second half) the annual return from buying at the MBP if the base case
     is realised and the exit multiple equals the entry multiple after ten
     years, for a subscription business, a cyclical and a services business.

The fair values were struck on today's accounts and today's growth views.
Applying them to a 2018 price is anachronistic. This is NOT a backtest.

Usage:
    .venv/bin/python tools/threshold_reachability.py [--cache DIR] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from statistics import median

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vss.valuation import equity_value_per_share  # noqa: E402

TODAY = date(2026, 8, 30)
HORIZONS = (1, 3, 5)
REARM_DAYS = 20          # supplementary count: episodes separated by >= 20 trading days above
TIER_MULT = {1: 0.80, 2: 0.70, 3: 0.60}
MONEY_MULT = {"whole": 1.0, "thousands": 1e3, "millions": 1e6}


@dataclass
class Name:
    ticker: str
    yahoo: str
    currency: str            # unit of fv_base / MBP
    quote_unit: str          # unit Yahoo quotes in
    fv_base: float
    tier: int
    tier_assumed: bool       # True: §4.4 has not scored it; tier 2 is the assumption
    mbp: float               # the figure AS IT STANDS TODAY, from the record named in `source`
    source: str
    status: str              # "struck" | "pre-ruling" | "superseded"
    run_record: str | None
    bear_stated: float | None = None
    fcf0_stated: float | None = None   # in record currency, whole units (for the check)
    # filled in by the engine check
    fcf0_ps: float | None = None
    net_cash_ps: float | None = None
    g_base: float | None = None
    g_bear: float | None = None
    bear_engine: float | None = None
    check_note: str = ""
    series_note: str = ""
    px: pd.DataFrame | None = field(default=None, repr=False)


def names_as_they_stand() -> list[Name]:
    """The MBP as it stands today, per name, with its provenance.

    E28: MBP = bear-case value x tier cushion (T1 0.80 / T2 0.70 / T3 0.60).
    Where §4.4 has not scored a tier the record prints the per-tier range and
    MBP is DATA MISSING; this measurement takes the TIER 2 figure and says so.
    E77 (2026-08-30) makes the regime ELEVATED, one tier stricter at the next
    re-score; that adjustment is NOT applied here ("as it stands today").
    """
    rr = "reference/run-records/"
    return [
        Name("ACN", "ACN", "USD", "USD", 255.10, 2, True, 128.63,
             "reference/ACN-STRIKE-2026-08-30.md (tier 2 line of the printed range)",
             "struck", rr + "ACN-2026-08-30.json", fcf0_stated=9_417_407_000.0),
        Name("AUTO.L", "AUTO.L", "GBP", "GBX", 4.82, 2, True, 2.68,
             "reference/AUTO.L-STRIKE-2026-08-27.md (bear 3.83 GBP x 0.70; no per-tier line printed)",
             "struck", rr + "AUTO.L-2026-08-27.json", bear_stated=3.83),
        Name("CTSH", "CTSH", "USD", "USD", 89.38, 2, False, 46.78,
             "config/watchlist.yaml + reference/CTSH-STRIKE-2026-08-30-e70.md (tier 2 scored 2026-08-29)",
             "struck", rr + "CTSH-2026-08-30-e70.json", bear_stated=66.83, fcf0_stated=2_643_000_000.0),
        Name("DECK", "DECK", "USD", "USD", 127.49, 2, True, 70.62,
             "reference/DECK-STRIKE-2026-08-30.md (tier 2 line of the printed range)",
             "struck", rr + "DECK-2026-08-30.json"),
        Name("GDDY", "GDDY", "USD", "USD", 132.18, 3, False, 66.82,
             "config/watchlist.yaml (tier 3, MBP 66.82 = bear 111.36 x 0.60)",
             "struck", rr + "GDDY-2026-08-30-restrike.json", bear_stated=111.36, fcf0_stated=1_406_400_000.0),
        Name("LIAB.ST", "LIAB.ST", "SEK", "SEK", 133.48, 2, False, 75.06,
             "reference/LIAB.ST-STRIKE-2026-08-30.md (tier 2 carried; MBP 75.06 = bear 107.23 x 0.70)",
             "struck", rr + "LIAB.ST-2026-08-30.json", bear_stated=107.23),
        Name("LII", "LII", "USD", "USD", 319.37, 2, True, 143.92,
             "reference/LII-STRIKE-2026-08-30-e70.md (tier 2 line of the printed range)",
             "struck", rr + "LII-2026-08-30-e70.json"),
        Name("NVR", "NVR", "USD", "USD", 4978.10, 2, True, 2395.94,
             "reference/NVR-STRIKE-2026-08-30.md (tier 2 line of the printed range)",
             "struck", rr + "NVR-2026-08-30.json", fcf0_stated=987_320_000.0),
        Name("RMV.L", "RMV.L", "GBP", "GBX", 4.27, 2, True, 2.40,
             "reference/RMV.L-STRIKE-2026-08-30.md (tier 2 line of the printed range)",
             "struck", rr + "RMV.L-2026-08-30.json"),
        Name("RKT.L", "RKT.L", "GBP", "GBX", 32.20, 2, True, 16.72,
             "reference/RKT.L-STRIKE-2026-08-30.md (tier 2 line of the printed range)",
             "struck", rr + "RKT.L-2026-08-30.json"),
        Name("ULTA", "ULTA", "USD", "USD", 476.45, 2, True, 251.60,
             "reference/ULTA-STRIKE-2026-08-30.md (tier 2 line of the printed range)",
             "struck", rr + "ULTA-2026-08-30.json"),
        # --- pre-ruling / superseded records ---------------------------------
        Name("AOS", "AOS", "USD", "USD", 62.66, 2, True, 32.63,
             "reference/AOS-STRIKE-2026-08-30.md -- PRE-E70 strike (lease charged twice); "
             "the E70 re-strike carries a declaration and no figure; tier 2 line of the printed range",
             "pre-ruling", rr + "AOS-2026-08-30.json", bear_stated=46.61),
        Name("SAP.DE", "SAP.DE", "EUR", "EUR", 139.48, 1, False, 96.21,
             "config/watchlist.yaml -- E87-NULLED 2026-08-30; last recorded fv_base 139.48 / tier 1 / "
             "re-entry line 96.21 EUR (bear 120.27 x 0.80, struck 2026-08-26)",
             "superseded", rr + "SAP.DE-2026-08-26.json", bear_stated=120.27),
        Name("UNA.AS", "UNA.AS", "EUR", "EUR", 43.5, 2, False, 30.45,
             "config/watchlist.yaml -- PRE-E28 definition (fv_base x 0.70, struck 2026-08-22, "
             "superseded by E32; no bear case, no run record); position SOLD 2026-08-24",
             "superseded", None),
    ]


# ----------------------------------------------------------------------------
# engine check: reproduce bear / MBP from the linked run record
# ----------------------------------------------------------------------------

def multiple(g: float, r: float, terminal: float, years: int) -> float:
    """Value per unit of FCF0 -- equity_value_per_share with fcf0=1, net_cash=0, shares=1."""
    return equity_value_per_share(fcf0=1.0, growth=g, net_cash=0.0, shares=1.0,
                                  rate=r, terminal=terminal, years=years)


def engine_check(n: Name) -> None:
    if n.run_record is None:
        n.check_note = "no run record (pre-E28 workbook figure); FCF yield not computable"
        return
    d = json.loads((ROOT / n.run_record).read_text())
    r = d["rate"]["rate"]
    conv = d["conventions"]
    if conv.get("mid_year"):
        n.check_note = "record uses mid-year discounting; engine check skipped"
        return
    money = MONEY_MULT[d.get("money_unit", "whole")]
    sh = d["shares"]
    shares = sh["count"] * MONEY_MULT[sh.get("unit", "whole")]
    net_cash = -d["bridge"]["net_debt"] * money
    n.g_base, n.g_bear = d["growth"]["base"], d["growth"]["bear"]
    n.net_cash_ps = net_cash / shares
    # back FCF0 out of the stated fv_base through the engine
    m_base = multiple(n.g_base, r, conv["terminal_growth"], conv["horizon_years"])
    n.fcf0_ps = (n.fv_base - n.net_cash_ps) / m_base
    n.bear_engine = equity_value_per_share(
        fcf0=n.fcf0_ps, growth=n.g_bear, net_cash=n.net_cash_ps, shares=1.0,
        rate=r, terminal=conv["terminal_growth"], years=conv["horizon_years"])
    mbp_engine = n.bear_engine * TIER_MULT[n.tier]
    notes = []
    if n.fcf0_stated is not None:
        gap = n.fcf0_ps * shares / n.fcf0_stated - 1
        notes.append(f"FCF0 backed out {n.fcf0_ps * shares / 1e6:,.1f}m vs stated "
                     f"{n.fcf0_stated / 1e6:,.1f}m ({gap:+.2%})")
    if n.bear_stated is not None:
        notes.append(f"bear engine {n.bear_engine:.2f} vs stated {n.bear_stated:.2f}")
    notes.append(f"MBP engine {mbp_engine:.2f} vs taken {n.mbp:.2f}")
    if abs(mbp_engine / n.mbp - 1) > 0.01:
        notes.append("**MISMATCH > 1%**")
    n.check_note = "; ".join(notes)


# ----------------------------------------------------------------------------
# prices
# ----------------------------------------------------------------------------

def fetch(symbol: str, cache: Path | None) -> pd.DataFrame:
    """Ten years of daily closes, dividend-UNADJUSTED (auto_adjust=False).

    Returns columns close, adj (dividend+split adjusted, for the stock's own
    total return), split. Index is a tz-naive date.
    """
    f = cache / f"{symbol.replace('^', '_')}.csv" if cache else None
    if f and f.exists():
        return pd.read_csv(f, index_col=0, parse_dates=True)
    import yfinance as yf
    h = yf.Ticker(symbol).history(period="10y", auto_adjust=False, actions=True)
    if h is None or h.empty:
        raise SystemExit(f"{symbol}: no data from yfinance")
    h.index = pd.DatetimeIndex(h.index.tz_localize(None).normalize())
    out = pd.DataFrame({"close": h["Close"], "adj": h["Adj Close"],
                        "split": h.get("Stock Splits", 0.0)}).dropna(subset=["close"])
    out = out[~out.index.duplicated(keep="last")].sort_index()
    if f:
        out.to_csv(f)
    return out


def apply_splits(px: pd.DataFrame, ticker: str) -> tuple[pd.DataFrame, list[str]]:
    """Put every close into TODAY's share units.

    Yahoo's raw closes are normally already split-adjusted; the check compares
    the close on the last day before each split with the split day. If the
    ratio matches the split factor the series is raw and the closes before the
    split are divided by the factor; if it is ~1 nothing is done. Either way
    the verdict is printed so a wrong adjustment cannot pass silently.
    """
    notes = []
    px = px.copy()
    for d, ratio in px.loc[px["split"] != 0, "split"].items():
        before = px.loc[:d].iloc[:-1]
        if before.empty:
            continue
        jump = before["close"].iloc[-1] / px.loc[d, "close"]
        # nearer hypothesis wins: jump ~ ratio means the closes before the
        # split are still in old units; jump ~ 1 means Yahoo adjusted them.
        # A factor within 15% of 1 is inside one day's noise -- flagged.
        small = abs(ratio - 1) < 0.15
        if abs(jump - ratio) < abs(jump - 1):
            px.loc[before.index, "close"] = before["close"] / ratio
            notes.append(f"{ticker}: split {ratio:g} on {d.date()} -- series was RAW "
                         f"(jump {jump:.2f}x); closes before it divided by {ratio:g}"
                         + (" -- SMALL FACTOR, verdict within daily noise" if small else ""))
        else:
            notes.append(f"{ticker}: split {ratio:g} on {d.date()} -- series ALREADY "
                         f"split-adjusted by Yahoo (jump {jump:.2f}x); nothing applied"
                         + (f" -- SMALL FACTOR, verdict within daily noise; the difference is {abs(ratio - 1):.0%} of price either way" if small else ""))
    return px, notes


def to_mbp_unit(px: pd.DataFrame, n: Name) -> pd.DataFrame:
    if n.quote_unit == "GBX" and n.currency == "GBP":
        px = px.copy()
        px["close"] = px["close"] / 100.0
        px["adj"] = px["adj"] / 100.0
        n.series_note = "Yahoo quotes GBX; closes divided by 100 -> GBP, the MBP's unit"
    elif n.quote_unit != n.currency:
        raise SystemExit(f"{n.ticker}: quote unit {n.quote_unit} vs MBP unit {n.currency}")
    else:
        n.series_note = f"quoted and struck in {n.currency}"
    return px


# ----------------------------------------------------------------------------
# episodes and forward returns
# ----------------------------------------------------------------------------

def episodes(mask: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Runs of consecutive True closes -> [(first, last)]."""
    out, start, prev = [], None, None
    for d, v in mask.items():
        if v and start is None:
            start = d
        elif not v and start is not None:
            out.append((start, prev))
            start = None
        prev = d
    if start is not None:
        out.append((start, prev))
    return out


def rearmed(eps, index: pd.DatetimeIndex, gap: int) -> int:
    """Episodes separated by at least `gap` trading days above the threshold."""
    if not eps:
        return 0
    pos = {d: i for i, d in enumerate(index)}
    count, last_end = 1, eps[0][1]
    for s, e in eps[1:]:
        if pos[s] - pos[last_end] - 1 >= gap:
            count += 1
        last_end = e
    return count


def fwd(series: pd.Series, t0: pd.Timestamp, years: int, last: pd.Timestamp):
    """Return from t0 to the first date >= t0 + years, or None if INCOMPLETE."""
    target = t0 + pd.DateOffset(years=years)
    if target > last:
        return None
    i0 = series.index.searchsorted(t0)
    i1 = series.index.searchsorted(target)
    if i1 >= len(series):
        return None
    return series.iloc[i1] / series.iloc[i0] - 1


def drawdown_from_52w_high(close: pd.Series, t0: pd.Timestamp) -> float:
    i = close.index.get_loc(t0)
    window = close.iloc[max(0, i - 251): i + 1]
    return close.loc[t0] / window.max() - 1


# ----------------------------------------------------------------------------
# implied return (second half)
# ----------------------------------------------------------------------------

def irr(cfs: list[float]) -> float:
    lo, hi = -0.99, 5.0
    npv = lambda r: sum(c / (1 + r) ** t for t, c in enumerate(cfs))  # noqa: E731
    for _ in range(300):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def implied_returns(n: Name, price: float, r: float = 0.095, terminal: float = 0.025,
                    years: int = 10) -> dict:
    """Annual return from buying at `price` if the base case is realised.

    Three exits after ten years, FCF distributed each year and NOT reinvested:
      same_pfcf : exit at the ENTRY price/FCF multiple      (P10 = P0 (1+g)^10)
      same_evfcf: exit at the ENTRY EV/FCF multiple, net debt held constant
      engine    : exit at the engine's own terminal value, FCF10 (1+t)/(r-t)
    """
    g, f0 = n.g_base, n.fcf0_ps
    flows = [f0 * (1 + g) ** t for t in range(1, years + 1)]
    f10 = flows[-1]
    out = {"fcf_yield_at_price": f0 / price, "g_base": g}
    p10 = price * (1 + g) ** years
    out["same_pfcf"] = irr([-price] + flows[:-1] + [f10 + p10])
    ev0 = price - n.net_cash_ps
    p10_ev = (ev0 / f0) * f10 + n.net_cash_ps
    out["same_evfcf"] = irr([-price] + flows[:-1] + [f10 + p10_ev])
    # the engine's terminal value is an ENTERPRISE figure and the engine
    # credits net cash at face on day one, so the flows are bought for
    # (price - net cash); an entry at fv_base then returns exactly r -- the
    # check that this arithmetic is the engine's own.
    tv = f10 * (1 + terminal) / (r - terminal)
    out["engine"] = irr([-(price - n.net_cash_ps)] + flows[:-1] + [f10 + tv])
    out["exit_multiple_engine"] = (1 + terminal) / (r - terminal)
    # and if the BEAR case is what comes true -- the case the cushion is for
    gb = n.g_bear
    bflows = [f0 * (1 + gb) ** t for t in range(1, years + 1)]
    out["bear_same_pfcf"] = irr([-price] + bflows[:-1] + [bflows[-1] + price * (1 + gb) ** years])
    out["bear_engine"] = irr([-(price - n.net_cash_ps)] + bflows[:-1] + [bflows[-1] + bflows[-1] * (1 + terminal) / (r - terminal)])
    return out


# ----------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------

def pct(x, blank="INCOMPLETE"):
    return blank if x is None else f"{x:+.1%}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", type=Path, default=None, help="CSV cache dir for the fetched series (scratch only)")
    ap.add_argument("--out", type=Path, default=None, help="write the markdown here instead of stdout")
    a = ap.parse_args()
    warnings.filterwarnings("ignore")
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    if a.cache:
        a.cache.mkdir(parents=True, exist_ok=True)

    names = names_as_they_stand()
    for n in names:
        engine_check(n)

    idx = {s: fetch(s, a.cache) for s in ("^SP500TR", "^GSPC", "^OMX")}
    split_notes: list[str] = []
    for n in names:
        px, notes = apply_splits(fetch(n.yahoo, a.cache), n.ticker)
        split_notes += notes
        n.px = to_mbp_unit(px, n)

    L: list[str] = []
    w = L.append
    w(f"<!-- generated by tools/threshold_reachability.py on {TODAY} -- read-only; nothing written to the store -->")
    w("")

    # --- inputs -------------------------------------------------------------
    w("### Table 1 -- the threshold as it stands today, and the engine's reproduction of it")
    w("")
    w("| name | status | fv_base | bear (stated / engine) | tier | MBP taken | unit | last close | fall to MBP | g_base / g_bear | FCF0/share | FCF yield at MBP | FCF yield at last close | check |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for n in names:
        last = n.px["close"].iloc[-1]
        tier = f"{n.tier}{' (ASSUMED)' if n.tier_assumed else ''}"
        bear = (f"{n.bear_stated:.2f}" if n.bear_stated else "-") + " / " + (f"{n.bear_engine:.2f}" if n.bear_engine else "-")
        g = f"{n.g_base:.1%} / {n.g_bear:.1%}" if n.g_base is not None else "-"
        fps = f"{n.fcf0_ps:.2f}" if n.fcf0_ps else "-"
        y_mbp = f"{n.fcf0_ps / n.mbp:.1%}" if n.fcf0_ps else "-"
        y_now = f"{n.fcf0_ps / last:.1%}" if n.fcf0_ps else "-"
        w(f"| {n.ticker} | {n.status} | {n.fv_base:,.2f} | {bear} | {tier} | {n.mbp:,.2f} | {n.currency} | {last:,.2f} ({n.px.index[-1].date()}) | {n.mbp / last - 1:+.0%} | {g} | {fps} | {y_mbp} | {y_now} | {n.check_note} |")
    w("")
    m0 = multiple(0.0, 0.095, 0.025, 10)
    w(f"Zero-growth multiple in this engine (10 explicit years at g 0, terminal 2.5%, r 9.5%, end-of-year): "
      f"**{m0:.2f}x FCF0** (the review's 10.5x is 1/r, a flat perpetuity). "
      f"Tier 2 on the zero-growth value is {0.7 * m0:.2f}x = FCF yield {1 / (0.7 * m0):.1%}; "
      f"tier 3 is {0.6 * m0:.2f}x = {1 / (0.6 * m0):.1%}. The MBP is not on the zero-growth value but on the "
      f"pre-registered bear case (E28), whose g_bear is above zero for GDDY and below it for NVR.")
    w("")

    # --- series and splits ---------------------------------------------------
    w("### Table 2 -- the series")
    w("")
    w("| name | Yahoo symbol | first close | last close | trading days | unit note |")
    w("|---|---|---|---|---|---|")
    for n in names:
        w(f"| {n.ticker} | {n.yahoo} | {n.px.index[0].date()} | {n.px.index[-1].date()} | {len(n.px)} | {n.series_note} |")
    for s, df in idx.items():
        w(f"| {s} | {s} | {df.index[0].date()} | {df.index[-1].date()} | {len(df)} | "
          f"{'TOTAL RETURN index' if s == '^SP500TR' else 'PRICE index -- understates total return by the dividend yield, ~2-4pp/yr'} |")
    w("")
    w("Split handling (Yahoo closes checked across every split date):")
    w("")
    for s in split_notes:
        w(f"- {s}")
    deck = next(n for n in names if n.ticker == "DECK")
    d23 = deck.px.loc[:"2023-12-29", "close"].iloc[-1]
    d_pre = deck.px.loc[:"2024-09-16", "close"].iloc[-1]
    d_post = deck.px.loc["2024-09-17":, "close"].iloc[0]
    w(f"- DECK sanity check: series close on 2023-12-29 = **{d23:.2f}** in today's (post-split) units, "
      f"i.e. {d23 * 6:.2f} pre-split -- the press reported DECK closing 2023 at about 668 pre-split. "
      f"Close 2024-09-16 = {d_pre:.2f}, 2024-09-17 = {d_post:.2f} (a 6:1 split with no 6x jump: adjusted once, not twice). "
      f"The 2023 closes ARE about 1/6 of the press figures, which is what a post-split MBP of {deck.mbp:.2f} needs on the other side of the comparison; "
      f"the failure mode guarded against is a double adjustment (1/36), which would have put 2023 closes near {d23 / 6:.0f}.")
    w("")

    # --- episodes -----------------------------------------------------------
    w("### Table 3 -- episodes at or below the MBP, per name")
    w("")
    w("Forward returns are from the FIRST close of each episode. Stock TR = the stock's own total return "
      "(Yahoo Adj Close, dividends reinvested); stock PR = price return on the unadjusted closes. "
      "S&P 500 is TOTAL return (^SP500TR); OMXS30 is the PRICE index (^OMX) and understates its total return by roughly 2-4pp/yr. "
      "All returns in the local currency of each series -- no FX applied. A window ending after the last close is INCOMPLETE.")
    w("")
    all_touches = []   # (ticker, date, {h: (stock_tr, spx_tr, omx_pr)})
    summary_rows = []
    for n in names:
        close, adj = n.px["close"], n.px["adj"]
        last = close.index[-1]
        eps = episodes(close <= n.mbp)
        depth = close / n.mbp - 1
        dmin_d = depth.idxmin()
        min_bear = (close.min() / n.bear_engine) if n.bear_engine else None
        touched = {t: bool((close <= n.bear_engine * TIER_MULT[t]).any()) if n.bear_engine else None for t in (1, 2, 3)}
        first_cross = next((s for s, _ in eps if s != close.index[0]), None)
        summary_rows.append((n, len(eps), rearmed(eps, close.index, REARM_DAYS), depth.min(), dmin_d,
                             close.min() / n.fv_base, min_bear, touched, first_cross,
                             bool(eps) and eps[0][0] == close.index[0]))
        w(f"**{n.ticker}** -- MBP {n.mbp:,.2f} {n.currency} ({n.status}; tier {n.tier}{', assumed' if n.tier_assumed else ''}); "
          f"series {close.index[0].date()} to {last.date()}; "
          f"episodes at or below: **{len(eps)}**" + (f" ({rearmed(eps, close.index, REARM_DAYS)} with a {REARM_DAYS}-day re-arm)" if len(eps) > 1 else "") +
          f"; deepest below threshold **{depth.min():+.1%}** on {dmin_d.date()} (close {close.loc[dmin_d]:,.2f})"
          + (f"; lowest close ever = {close.min() / n.fv_base:.0%} of fv_base, {min_bear:.0%} of the bear value" if min_bear else f"; lowest close ever = {close.min() / n.fv_base:.0%} of fv_base"))
        w("")
        if not eps:
            w(f"- never at or below {n.mbp:,.2f} in the series. Lowest close {close.min():,.2f} on {close.idxmin().date()} "
              f"({close.min() / n.mbp - 1:+.1%} against the MBP).")
            w("")
            continue
        w("| # | first touch | last day | days | close | vs MBP | from 52w high | 1y stock TR (PR) | 1y S&P TR / OMX PR | 3y stock TR (PR) | 3y S&P TR / OMX PR | 5y stock TR (PR) | 5y S&P TR / OMX PR |")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for k, (s, e) in enumerate(eps, 1):
            ndays = len(close.loc[s:e])
            at_start = s == close.index[0]      # already below on the first day fetched: not a crossing
            dd = drawdown_from_52w_high(close, s)
            cells, rec = [], {}
            for h in HORIZONS:
                tr, pr = fwd(adj, s, h, last), fwd(close, s, h, last)
                spx = fwd(idx["^SP500TR"]["close"], s, h, idx["^SP500TR"].index[-1])
                omx = fwd(idx["^OMX"]["close"], s, h, idx["^OMX"].index[-1])
                rec[h] = (tr, spx, omx)
                cells.append(f"{pct(tr)} ({pct(pr, '')})" if tr is not None else "INCOMPLETE")
                cells.append(f"{pct(spx)} / {pct(omx)}" if tr is not None else "-")
            all_touches.append((n.ticker, s, rec, at_start))
            w(f"| {k} | {s.date()}{' (SERIES START)' if at_start else ''} | {e.date()} | {ndays} | {close.loc[s]:,.2f} | {close.loc[s] / n.mbp - 1:+.1%} | "
              f"{'n/a -- already below on the first day fetched' if at_start else f'{dd:+.1%}'} | " + " | ".join(cells) + " |")
        w("")

    # --- across the set ------------------------------------------------------
    w("### Table 4 -- across the set")
    w("")
    w("| name | status | episodes (strict) | episodes (20-day re-arm) | below at series start? | first crossing | deepest below MBP | lowest close / fv_base | lowest close / bear | would have touched at tier 1 / 2 / 3 |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for n, k, k2, dmin, dmin_d, lo_fv, lo_bear, touched, first, at_start in summary_rows:
        tch = " / ".join("yes" if touched[t] else "no" for t in (1, 2, 3)) if touched[1] is not None else "n/a (no bear case)"
        w(f"| {n.ticker} | {n.status} | {k} | {k2} | {'YES' if at_start else 'no'} | {first.date() if first else 'never'} | "
          f"{dmin:+.1%} ({dmin_d.date()}) | {lo_fv:.0%} | {f'{lo_bear:.0%}' if lo_bear else '-'} | {tch} |")
    ever = [r for r in summary_rows if r[1] > 0]
    w("")
    w(f"Names that ever traded at or below their threshold: **{len(ever)} of {len(names)}** "
      f"({', '.join(r[0].ticker for r in ever) or 'none'}). Never: {', '.join(r[0].ticker for r in summary_rows if r[1] == 0) or 'none'}.")
    w("")
    w("Median forward return from first touches (complete windows only; N in brackets):")
    w("")
    crossings = [x for x in all_touches if not x[3]]   # episodes that BEGAN inside the series
    first_per_name = {}
    for t, d, rec, _ in crossings:
        first_per_name.setdefault(t, (d, rec))
    w(f"Episodes already in progress on the first day fetched are NOT crossings and are excluded here: "
      f"{', '.join(f'{t} ({d.date()})' for t, d, _, st in all_touches if st) or 'none'}.")
    w("")
    w("| horizon | all crossings: stock TR | S&P 500 TR same dates | OMXS30 PR same dates | first crossing per name: stock TR | S&P TR | OMX PR |")
    w("|---|---|---|---|---|---|---|")
    for h in HORIZONS:
        comp = [rec[h] for _, _, rec, _ in crossings if rec[h][0] is not None]
        comp1 = [rec[h] for _, rec in first_per_name.values() if rec[h][0] is not None]
        def med(rows, i):
            vals = [r[i] for r in rows if r[i] is not None]
            return f"{median(vals):+.1%} [{len(vals)}]" if vals else "-"
        w(f"| {h}y | {med(comp, 0)} | {med(comp, 1)} | {med(comp, 2)} | {med(comp1, 0)} | {med(comp1, 1)} | {med(comp1, 2)} |")
    w("")
    w("First-touch dates by quarter (clustering):")
    w("")
    by_q: dict[str, list[str]] = {}
    for t, d, _, st in all_touches:
        by_q.setdefault(f"{d.year}Q{(d.month - 1) // 3 + 1}", []).append(f"{t} {d.date()}{' (series start)' if st else ''}")
    for q in sorted(by_q):
        w(f"- {q}: {', '.join(by_q[q])}")
    w("")
    w("Drawdown from the trailing 52-week high at first touch, against Gate 1's 15-50% band:")
    w("")
    for n, k, *_ in summary_rows:
        if k == 0:
            continue
        close = n.px["close"]
        dds = [drawdown_from_52w_high(close, s) for s, _ in episodes(close <= n.mbp) if s != close.index[0]]
        if not dds:
            w(f"- {n.ticker}: no crossing inside the series (below from the first day fetched only)")
            continue
        w(f"- {n.ticker}: " + ", ".join(f"{x:+.0%}" for x in dds) +
          f" -- {sum(1 for x in dds if -0.50 <= x <= -0.15)} of {len(dds)} first touches inside the band, "
          f"{sum(1 for x in dds if x < -0.50)} beyond the 50% ceiling, {sum(1 for x in dds if x > -0.15)} shallower than 15%")
    w("")

    # --- second half -----------------------------------------------------------
    w("### Table 5 -- the implied return at the MBP if the base case comes true")
    w("")
    w("Buy at the MBP, hold ten years, FCF per share grows at g_base and is paid out (not reinvested), "
      "sell at year 10. Three exits: the ENTRY price/FCF multiple; the ENTRY EV/FCF multiple with net debt held constant; "
      "and the engine's own terminal value (FCF10 x 1.025 / 0.070 = 14.64x FCF10, net cash credited at face on day one as the engine does). "
      "Same arithmetic at fv_base for reference -- the engine's exit at fv_base returns r = 9.5% by construction.")
    w("")
    w("| name | character | g_base | buy at | FCF yield at entry | entry P/FCF | IRR, exit at entry P/FCF | IRR, exit at entry EV/FCF | IRR, engine exit (14.64x) | if g_bear instead: IRR same P/FCF | g_bear, engine exit |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for tk, ch in (("GDDY", "subscription (domains, hosting)"), ("NVR", "cyclical (US homebuilder)"),
                   ("ACN", "services (IT consulting)"), ("CTSH", "services -- the one name with a SCORED tier")):
        n = next(x for x in names if x.ticker == tk)
        for label, price in (("MBP", n.mbp), ("fv_base", n.fv_base)):
            o = implied_returns(n, price)
            w(f"| {tk} | {ch} | {o['g_base']:.1%} | {label} {price:,.2f} | {o['fcf_yield_at_price']:.1%} | {price / n.fcf0_ps:.1f}x | "
              f"**{o['same_pfcf']:.1%}** | {o['same_evfcf']:.1%} | {o['engine']:.1%} | {o['bear_same_pfcf']:.1%} (g {n.g_bear:+.1%}) | {o['bear_engine']:.1%} |")
    w("")
    out = "\n".join(L)
    if a.out:
        a.out.write_text(out)
        print(f"wrote {a.out}")
    else:
        print(out)


if __name__ == "__main__":
    main()
