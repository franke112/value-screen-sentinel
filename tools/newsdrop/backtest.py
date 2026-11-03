"""Backtest of the news-drop track, both legs (design §8a and §9).

    .venv/bin/python -m tools.backtest.run  (first: its prices and universe)
    .venv/bin/python -m tools.newsdrop.backtest [--min-float 10e9] [--move 0.10]

THE EVENT. A large company (the filer's own public float >= `--min-float` in
the step-3 universe of the year) whose 5-day total return, less ^SP500TR's
over the same days, crosses -10% (the DROP leg) or +10% (the RISE leg).
After an event the name is not counted again for 20 trading days. Events are
taken from each universe date to the next (2016-04-29 .. 2021-04-30): the
float line is the one known when the window opened.

THE MECHANICAL CLASS (design §2, the part that can be done backwards). The
filer's own SEC filings ACCEPTED in the window -- from the close five trading
days before the event to the event day's close (after 16:00 New York counts
for the next day):

  B-report  an 8-K item 2.02 or a 10-Q/10-K: the move is the company's own
            figures (earnings, guidance)
  B-other   8-K item 1.03, 2.06, 4.01, 4.02 or 5.02: bankruptcy,
            impairment, auditor change, non-reliance, officer change
  own-other any other 8-K (7.01, 8.01, 1.01, 2.01 ...): the company said
            something, not a report
  no-news   nothing filed: the move carries no news OF THE COMPANY'S OWN
            (Chan 2003's no-news case; contagion and market noise land here)

What this cannot see: press releases with no 8-K, news about the company
from others, and whether a headline's cost is bounded (A3). The fine
classification is a forward test, not this one.

THE OUTCOME. Total return from the event day's close over 21, 63, 126 and 252
trading days, less ^SP500TR's over the same days.

SURVIVORS ONLY, as the method backtest: a name with no ticker today has no
prices and is not here.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from tools.backtest import pilot as PL
from tools.backtest import universe as U

ROOT = PL.ROOT.parent / "newsdrop"
WINDOW = 5
COOLDOWN = 20
#: THE SIZE CHECK THE FLOAT CANNOT GIVE. A filer's own float can be
#: mis-tagged (the pilot's AMEDICA, 19.4bn at $1.18) and a ticker today can
#: belong to another security (SPB for HRG); both put micro caps in a
#: large-cap test (first run: UAVS, FCEL, REEMF, PED topped the no-news
#: drops). A large company TRADES like one: the median daily dollar volume
#: of the 60 days before the event must reach this.
MIN_DOLLAR_VOLUME = 50e6
HORIZONS = (21, 63, 126, 252)
NEW_YORK = ZoneInfo("America/New_York")
B_OTHER_ITEMS = ("1.03", "2.06", "4.01", "4.02", "5.02")
REPORT_FORMS = ("10-Q", "10-K", "10-Q/A", "10-K/A", "10-KT")


# --- filings -----------------------------------------------------------------

def filings(cik: int) -> list[tuple[str, str, str]]:
    """(effective trading date, form, items) for every filing, cached. The
    effective date is the acceptance day, or the next day where accepted
    after the 16:00 close in New York."""
    cache = ROOT / "filings" / f"CIK{cik:010d}.json"
    if cache.exists():
        return [tuple(x) for x in json.loads(cache.read_text())]
    raw = json.loads(U.sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
    blocks = [raw["filings"]["recent"]]
    for f in raw["filings"].get("files", []):
        if f.get("filingTo", "") >= "2016-01-01":
            blocks.append(json.loads(U.sec_get(f"https://data.sec.gov/submissions/{f['name']}")))
    out = []
    for b in blocks:
        for form, filed, acc, items in zip(b["form"], b["filingDate"],
                                           b.get("acceptanceDateTime", b["filingDate"]),
                                           b.get("items", [""] * len(b["form"]))):
            if filed < "2016-01-01":
                continue
            day = filed
            try:
                t = datetime.fromisoformat(acc.replace("Z", "+00:00")).astimezone(NEW_YORK)
                day = (t.date() + timedelta(days=1)).isoformat() if t.hour >= 16 else t.date().isoformat()
            except ValueError:
                pass
            out.append((day, form, items or ""))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out))
    return out


def classify(own: list[tuple[str, str, str]]) -> str:
    items = {i.strip() for _, form, it in own if form.startswith("8-K") for i in it.split(",") if i.strip()}
    if "2.02" in items or any(form in REPORT_FORMS for _, form, _ in own):
        return "B-report"
    if items & set(B_OTHER_ITEMS):
        return "B-other"
    if any(form.startswith("8-K") for _, form, _ in own):
        return "own-other"
    return "no-news"


# --- events ------------------------------------------------------------------

def large_names(min_float: float) -> list[dict]:
    """(cik, ticker, window start, window end) per universe date."""
    out = []
    dates = list(U.TEST_DATES)
    for i, d in enumerate(dates):
        end = dates[i + 1] if i + 1 < len(dates) else date(d.year + 1, d.month, d.day)
        rows = json.loads((PL.ROOT / "universe" / f"{d.isoformat()}.json").read_text())["rows"]
        for r in rows:
            t = (r.get("tickers_today") or [None])[0]
            if t and r["frame_float"] >= min_float:
                out.append({"cik": r["cik"], "ticker": t, "company": r["company"],
                            "sic": r.get("sic"), "start": d, "end": end})
    return out


def _series(frame: pd.DataFrame) -> pd.Series:
    s = frame["Adj Close"].dropna()
    s.index = pd.to_datetime(s.index)
    return s[~s.index.duplicated()]


def events(name: dict, index: pd.Series, move: float) -> list[dict]:
    frame = PL.prices(name["ticker"])
    if frame is None or "Adj Close" not in frame.columns:
        return []
    s = _series(frame)
    dv = None
    if "Volume" in frame.columns and "Close" in frame.columns:
        dv = (frame["Close"] * frame["Volume"]).astype(float)
        dv.index = pd.to_datetime(dv.index)
        dv = dv[~dv.index.duplicated()].rolling(60).median().shift(1)
    both = pd.concat([s, index], axis=1, join="inner").dropna()
    both.columns = ["p", "i"]
    if len(both) < WINDOW + 2:
        return []
    r5 = both["p"] / both["p"].shift(WINDOW) - both["i"] / both["i"].shift(WINDOW)
    days = list(both.index)
    out, last = [], -10_000
    for k, day in enumerate(days):
        if day.date() < name["start"] or day.date() >= name["end"]:
            continue
        x = r5.iloc[k]
        if pd.isna(x) or abs(x) < move or k - last < COOLDOWN:
            continue
        if dv is None or pd.isna(dv.get(day)) or dv.get(day) < MIN_DOLLAR_VOLUME:
            continue
        last = k
        ev = {"ticker": name["ticker"], "cik": name["cik"], "company": name["company"],
              "sic": name["sic"], "date": day.date().isoformat(),
              "leg": "drop" if x < 0 else "rise", "move": float(x),
              "window_from": days[k - WINDOW].date().isoformat()}
        for h in HORIZONS:
            if k + h < len(days):
                p0, p1 = both["p"].iloc[k], both["p"].iloc[k + h]
                i0, i1 = both["i"].iloc[k], both["i"].iloc[k + h]
                ev[f"x{h}"] = float(p1 / p0 - i1 / i0)
        out.append(ev)
    return out


def run(min_float: float, move: float, workers: int = 4) -> list[dict]:
    names = large_names(min_float)
    index = _series(PL.prices(PL.INDEX))
    ciks = sorted({n["cik"] for n in names})
    print(f"{len(names)} name-windows, {len(ciks)} filers", flush=True)
    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(lambda c: _quiet(filings, c), ciks))
    evs = []
    for n in names:
        for ev in events(n, index, move):
            try:
                own = [f for f in filings(n["cik"]) if ev["window_from"] < f[0] <= ev["date"]]
            except Exception:  # noqa: BLE001
                own, ev["filings_missing"] = [], True
            ev["class"] = classify(own)
            ev["own"] = [f"{d} {form} {it}".strip() for d, form, it in own]
            evs.append(ev)
    dest = ROOT / f"events-{move:.2f}-{min_float / 1e9:.0f}bn.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(evs, indent=1))
    return evs


def _quiet(fn, arg):
    try:
        fn(arg)
    except Exception:  # noqa: BLE001
        pass


# --- the report ----------------------------------------------------------------

def _ci(xs, draws=5000, seed=20261029):
    if len(xs) < 5:
        return None
    rng = random.Random(seed)
    m = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(draws))
    return m[int(0.025 * draws)], m[int(0.975 * draws)]


def report(evs: list[dict], move: float, min_float: float) -> list[str]:
    L = [f"# Nyhetsfall — bakåttest, {date.today().isoformat()}", "",
         f"Händelse: 5-dagars totalavkastning minus ^SP500TR över ±{move:.0%}; "
         f"bolag med float ≥ {min_float / 1e9:.0f} mdr USD; 2016-04-29 till 2021-04-30. "
         "Utfall: överavkastning mot ^SP500TR efter 21/63/126/252 handelsdagar, "
         f"procentenheter. Median daglig omsättning ≥ {MIN_DOLLAR_VOLUME / 1e6:.0f} MUSD de 60 dagarna före. "
         "Covid-perioden 2020-02-15..2020-12-31 redovisas för sig: ett marknadsras är inte "
         "en nyhet om bolaget (design §5). **Bara överlevare.**", ""]
    crash = lambda e: "2020-02-15" <= e["date"] <= "2020-12-31"
    for leg, title in (("drop", "Fallbenet (köp efter fall), utan covid"),
                       ("rise", "Uppgångsbenet (köp efter uppgång), utan covid"),
                       ("drop-c", "Fallbenet, bara covid-perioden"),
                       ("rise-c", "Uppgångsbenet, bara covid-perioden")):
        pool = [e for e in evs if crash(e) == leg.endswith("-c")]
        leg = leg.removesuffix("-c")
        L += [f"## {title}", "",
              "| Klass | N | 1 mån medel (±50 % tak) / median | 3 mån | 6 mån | 12 mån | 12 mån > 0 | 12 mån 95 % (medel) |",
              "|---|---:|---|---|---|---|---:|---|"]
        for cls in ("no-news", "own-other", "B-other", "B-report", "alla"):
            sub = [e for e in pool if e["leg"] == leg and (cls == "alla" or e["class"] == cls)]
            cells = []
            for h in HORIZONS:
                xs = [e[f"x{h}"] for e in sub if f"x{h}" in e]
                # the mean with each event capped at +-50%: one 17x name is
                # not the class
                cells.append("–" if not xs else
                             f"{statistics.mean(max(-.5, min(.5, x)) for x in xs) * 100:+.1f} / "
                             f"{statistics.median(xs) * 100:+.1f}")
            x12 = [e["x252"] for e in sub if "x252" in e]
            ci = _ci([max(-.5, min(.5, x)) for x in x12])
            L.append(f"| {cls} | {len(sub)} | " + " | ".join(cells) + " | "
                     + ("–" if not x12 else f"{sum(x > 0 for x in x12) / len(x12):.0%}") + " | "
                     + ("–" if ci is None else f"{ci[0] * 100:+.1f} till {ci[1] * 100:+.1f}") + " |")
        L.append("")
    by_year = {}
    for e in evs:
        by_year.setdefault((e["leg"], e["date"][:4]), []).append(e)
    L += ["## Antal händelser per år", "", "| År | Fall | Uppgång |", "|---|---:|---:|"]
    for y in sorted({k[1] for k in by_year}):
        L.append(f"| {y} | {len(by_year.get(('drop', y), []))} | {len(by_year.get(('rise', y), []))} |")
    return L


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--min-float", type=float, default=10e9)
    ap.add_argument("--move", type=float, default=0.10)
    a = ap.parse_args(argv)
    evs = run(a.min_float, a.move)
    print("\n".join(report(evs, a.move, a.min_float)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
