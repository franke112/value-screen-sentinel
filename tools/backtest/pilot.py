"""The pilot (backtest design, step 4): 50 random names, one test date.

    .venv/bin/python -m tools.backtest.pilot [--date 2018-04-30] [--n 50] [--seed 20261029]

Draws names from the step-3 candidates, fetches each one's companyfacts
(kept gzipped in data/backtest/companyfacts/), applies the exact float line
(`universe.pit_float`), runs `value.evaluate` under both cut policies, and
reads prices through the tool's own fetch (`vss.fetch.fetch_live`, period
"max", cached in data/backtest/prices/ -- never in data/cache/, which the
nightly owns). Writes reference/backtest/PILOT-<date>.md and the rows as
JSON beside the data.

THE PRICE DATE IS THE CLIP DATE. The test date is moved to the last
trading day on or before it, and facts are cut at that day (filed strictly
before it): a filing made on a Friday evening must not meet a Friday close
for a Sunday test date.
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from vss import fetch as F

from . import universe as U
from . import value as V

ROOT = U.ROOT
INDEX = "^SP500TR"
HORIZONS = (1, 3, 5)


# --- facts and prices -------------------------------------------------------

def company_facts(cik: int) -> dict | None:
    gz = ROOT / "companyfacts" / f"CIK{cik:010d}.json.gz"
    plain = gz.with_suffix("")
    if plain.exists():
        return json.loads(plain.read_text())
    if not gz.exists():
        try:
            raw = U.sec_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
        except Exception:  # noqa: BLE001 -- a filer with no XBRL facts at all
            return None
        gz.parent.mkdir(parents=True, exist_ok=True)
        gz.write_bytes(gzip.compress(raw))
    return json.loads(gzip.decompress(gz.read_bytes()))


def prices(ticker: str) -> pd.DataFrame | None:
    """Daily history, period max, through the tool's own fetch; cached."""
    path = ROOT / "prices" / f"{F.safe_name(ticker)}.csv"
    if path.exists():
        frame = pd.read_csv(path, index_col=0)
        return frame if len(frame) else None
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        frame = F.fetch_live(ticker, period="max")
    except Exception:  # noqa: BLE001 -- no price is a counted outcome
        pd.DataFrame().to_csv(path)
        return None
    frame.index = [pd.Timestamp(i).date().isoformat() for i in frame.index]
    frame.to_csv(path)
    return frame


def close_on(frame: pd.DataFrame, day: date, column: str = "Close"):
    """(date, value) of the last row on or before `day`, within 7 days."""
    rows = frame[frame.index <= day.isoformat()]
    if not len(rows) or column not in rows.columns:
        return None
    when = date.fromisoformat(rows.index[-1])
    if (day - when).days > 7:
        return None
    return when, float(rows[column].iloc[-1])


def unadjusted_close(frame: pd.DataFrame, day: date):
    """The close as printed on `day`: the vendor's split-adjusted Close
    times every split ratio after it (auto_adjust=False leaves dividends
    out of Close, so splits are all there is to undo)."""
    got = close_on(frame, day)
    if got is None:
        return None
    when, close = got
    factor = 1.0
    if "Stock Splits" in frame.columns:
        after = frame[(frame.index > when.isoformat()) & (frame["Stock Splits"] > 0)]
        for ratio in after["Stock Splits"]:
            factor *= float(ratio)
    return when, close * factor


def total_return(frame: pd.DataFrame, start: date, end: date):
    a, b = close_on(frame, start, "Adj Close"), close_on(frame, end, "Adj Close")
    if a is None or b is None or a[1] <= 0:
        return None
    return b[1] / a[1] - 1


def years_after(day: date, n: int) -> date:
    try:
        return day.replace(year=day.year + n)
    except ValueError:
        return day.replace(year=day.year + n, day=28)


def trading_day(day: date) -> date:
    """The last trading day on or before `day`, read off the index."""
    frame = prices(INDEX)
    got = close_on(frame, day) if frame is not None else None
    return got[0] if got else day


# --- the pilot --------------------------------------------------------------

def draw(as_of: date, n: int, seed: int) -> list[dict]:
    path = ROOT / "universe" / f"{as_of.isoformat()}.json"
    rows = json.loads(path.read_text())["rows"]
    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows


def run(as_of: date, n: int, seed: int) -> dict:
    day = trading_day(as_of)
    index = prices(INDEX)
    out, drawn, below_line, no_facts = [], 0, [], []
    for cand in draw(as_of, n, seed):
        if len(out) >= n:
            break
        drawn += 1
        facts = company_facts(cand["cik"])
        if facts is None:
            no_facts.append(cand["company"])
            continue
        pf = U.pit_float(facts, day)
        if pf is None or pf[0] < U.FLOAT_MIN:
            below_line.append((cand["company"], None if pf is None else pf[0]))
            continue
        ticker = (cand.get("tickers_today") or [None])[0]
        label = ticker or f"CIK{cand['cik']}"
        row = V.evaluate(facts, day, ticker=label, cik=cand["cik"])
        alt = V.evaluate(facts, day, ticker=label, cik=cand["cik"], policy="latest")
        row.update(company=cand["company"], sic=cand.get("sic"),
                   ticker_today=ticker, public_float=pf[0], float_date=pf[1],
                   fv_base_latest=alt["fv_base"], status_latest=alt["status"],
                   price=None, price_date=None, fv_over_price=None,
                   returns={}, index_returns={}, last_price_date=None)
        frame = prices(ticker) if ticker else None
        if frame is not None:
            got = unadjusted_close(frame, day)
            if got is not None:
                row["price_date"], row["price"] = got[0].isoformat(), got[1]
                if row["fv_base"] is not None and got[1] > 0:
                    row["fv_over_price"] = row["fv_base"] / got[1]
            row["last_price_date"] = frame.index[-1]
            for h in HORIZONS:
                end = years_after(day, h)
                row["returns"][h] = total_return(frame, day, end)
                row["index_returns"][h] = total_return(index, day, end)
        out.append(row)
    result = {"as_of": as_of.isoformat(), "trading_day": day.isoformat(),
              "seed": seed, "drawn": drawn, "below_line": below_line,
              "no_facts": no_facts, "rows": out}
    dest = ROOT / "pilot" / f"PILOT-{as_of.isoformat()}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=1, default=str))
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", type=date.fromisoformat, default=date(2018, 4, 30))
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20261029)
    args = ap.parse_args(argv)
    r = run(args.date, args.n, args.seed)
    md = ROOT / "pilot" / f"PILOT-{args.date.isoformat()}-table.md"
    md.write_text("\n".join(table(r) + ["", "## Varför inget värde", ""] + reasons(r)) + "\n")
    ok = sum(1 for x in r["rows"] if x["status"] == "ok")
    print(f"{args.date}: drawn {r['drawn']}, rows {len(r['rows'])}, valued {ok}, "
          f"below the float line {len(r['below_line'])}, no facts {len(r['no_facts'])}")
    return 0



# --- the report -------------------------------------------------------------

def _pct(x, digits=0):
    return "" if x is None else f"{x * 100:+.{digits}f}"


def _num(x, spec=",.2f"):
    return "" if x is None else format(x, spec)


def _status(row) -> str:
    s = row["status"]
    if s == "ok":
        return "ok"
    for key, short in (("no growth", "ingen tillväxt (E144)"),
                       ("gate refused: FCF0", "grind: FCF0"),
                       ("gate refused", "grind"),
                       ("no store", "ingen store"),
                       ("store refused", "store vägrad"),
                       ("no history", "ingen historik"),
                       ("record will not form", "record bildas ej"),
                       ("no value", "inget värde"),
                       ("no twelve-month", "ingen tolvmånadersbas")):
        if s.startswith(key):
            return short
    return s[:30]


def table(result: dict) -> list[str]:
    head = ("| # | Ticker | Bolag | SIC | Float M | Status | Kurs | fv_base | fv_bear | "
            "fv/kurs | g_base | Q1 Q2 Q3 Q4 | Stopp | Ränta | Nollor | 842 | "
            "fv senast % | 1 år | 3 år | 5 år |")
    out = [head, "|" + "|".join("---" for _ in range(head.count("|") - 1)) + "|"]
    for i, r in enumerate(result["rows"], 1):
        q = " ".join({True: "✓", False: "✗", None: "?"}[r["quality"].get(k)]
                     for k in ("Q1", "Q2", "Q3", "Q4")) if r["quality"] else ""
        tripped = [k["rule"][:5] for k in r["kills"] if k["state"] == "TRIP"
                   and k["rule"].startswith(V.MEASURED_KILLS)]
        cannot = sum(1 for k in r["kills"] if k["state"] == "CANNOT_EVALUATE"
                     and k["rule"].startswith(V.MEASURED_KILLS))
        kills = (",".join(tripped) or "–") + (f" ({cannot}?)" if cannot else "")
        diff = None
        if r["fv_base"] and r.get("fv_base_latest"):
            diff = r["fv_base_latest"] / r["fv_base"] - 1
        rel = []
        for h in HORIZONS:
            a, b = r["returns"].get(h), r["index_returns"].get(h)
            rel.append("" if a is None else f"{a * 100:+.0f} ({(a - b) * 100:+.0f})" if b is not None else f"{a * 100:+.0f}")
        shape = {"": "E34", "income_statement_net": "E34.1",
                 "interest_expense_only": "E61", "cash_paid_only": "E115"}.get(
                     r["interest_source"], r["interest_source"])
        out.append(
            f"| {i} | {r['ticker_today'] or '–'} | {r['company'][:28]} | {r.get('sic') or ''} | "
            f"{r['public_float'] / 1e6:,.0f} | {_status(r)} | {_num(r['price'])} | "
            f"{_num(r['fv_base'])} | {_num(r['fv_bear'])} | {_num(r['fv_over_price'], '.2f')} | "
            f"{_pct(r['g_base'], 1)} | {q} | {kills} | {shape} | "
            f"{len(r.get('searched_zeros') or [])} | {'J' if r['lease_transition'] else ''} | "
            f"{_pct(diff, 1)} | {' | '.join(rel)} |")
    return out


def reasons(result: dict) -> list[str]:
    out = []
    for i, r in enumerate(result["rows"], 1):
        if r["status"] != "ok":
            out.append(f"- **{i} {r['ticker_today'] or r['company']}**: {r['status']}")
    return out


if __name__ == "__main__":
    sys.exit(main())
