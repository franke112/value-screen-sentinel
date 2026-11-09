"""A point-in-time index over the EODHD fundamentals (private; never published).

    .venv/bin/python tools/eodhd_pit.py --build              # data/eodhd/pit.sqlite from the fetched files
    .venv/bin/python tools/eodhd_pit.py --show VOLV-B.ST 2020-06-01

EODHD keeps ONE value per period -- the latest, restatements included -- so
this is point-in-time in TIMING only: a quarter enters on the day it became
known, never earlier, but with the value as last reported. That residual is
stated, not hidden.

WHEN A PERIOD BECAME KNOWN (`known_date`), in this order:
1. `filing_date`, where it is a REAL filing date -- later than the period end
   (US: the 10-Q/10-K). For Nordic issuers EODHD sets it equal to the period
   end, which is not a date anything was known, so it is not used.
2. the earnings report date for that period end (Earnings::History
   `reportDate`) PLUS ONE WEEKDAY: the before/after-market flag is unreliable
   for the Nordics, so the figures are taken as known the next trading day.
   A report date before the period end or more than 200 days after it is
   not believed.
3. otherwise NONE: the period is in the index but never visible to a
   point-in-time read. A guess would be the look-ahead this exists to remove.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "eodhd" / "fundamentals"
DB = ROOT / "data" / "eodhd" / "pit.sqlite"
MAX_REPORT_LAG = 200

FIELDS = {
    "Income_Statement": ("totalRevenue", "operatingIncome", "ebit", "netIncome",
                         "incomeBeforeTax", "interestExpense", "depreciationAndAmortization"),
    "Balance_Sheet": ("totalAssets", "totalStockholderEquity", "cash", "cashAndShortTermInvestments",
                      "shortLongTermDebtTotal", "longTermDebt", "shortTermDebt", "goodWill",
                      "intangibleAssets", "commonStockSharesOutstanding", "netDebt",
                      "capitalLeaseObligations", "totalCurrentAssets", "totalCurrentLiabilities"),
    "Cash_Flow": ("totalCashFromOperatingActivities", "capitalExpenditures", "freeCashFlow",
                  "depreciation", "stockBasedCompensation", "dividendsPaid", "changeInWorkingCapital"),
}

DDL = """
CREATE TABLE IF NOT EXISTS periods (
    symbol TEXT NOT NULL, freq TEXT NOT NULL, period_end TEXT NOT NULL,
    known_date TEXT, known_basis TEXT NOT NULL, currency TEXT,
    PRIMARY KEY (symbol, freq, period_end));
CREATE TABLE IF NOT EXISTS figures (
    symbol TEXT NOT NULL, freq TEXT NOT NULL, period_end TEXT NOT NULL,
    statement TEXT NOT NULL, field TEXT NOT NULL, value REAL,
    PRIMARY KEY (symbol, freq, period_end, field));
CREATE TABLE IF NOT EXISTS reports (
    symbol TEXT NOT NULL, period_end TEXT NOT NULL, report_date TEXT,
    eps_actual REAL, eps_estimate REAL, surprise_pct REAL,
    PRIMARY KEY (symbol, period_end));
CREATE INDEX IF NOT EXISTS idx_periods_known ON periods (symbol, freq, known_date);
"""


def next_weekday(d: date) -> date:
    d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def known(period_end: str, filing: str | None, report: str | None) -> tuple[str | None, str]:
    pe = date.fromisoformat(period_end)
    if filing:
        try:
            f = date.fromisoformat(filing[:10])
            if f > pe:
                return f.isoformat(), "filing_date"
        except ValueError:
            pass
    if report:
        try:
            r = date.fromisoformat(report[:10])
            if pe < r <= pe + timedelta(days=MAX_REPORT_LAG):
                return next_weekday(r).isoformat(), "report_date+1"
        except ValueError:
            pass
    return None, "unknown"


def _num(v) -> float | None:
    try:
        return None if v in (None, "", "None") else float(v)
    except (TypeError, ValueError):
        return None


def rows_for(symbol: str, d: dict) -> tuple[list, list, list]:
    hist = (d.get("Earnings") or {}).get("History") or {}
    report_of = {v.get("date"): v.get("reportDate") for v in hist.values() if isinstance(v, dict)}
    reports = [(symbol, v.get("date"), v.get("reportDate"), _num(v.get("epsActual")),
                _num(v.get("epsEstimate")), _num(v.get("surprisePercent")))
               for v in hist.values() if isinstance(v, dict) and v.get("date")]
    periods: dict = {}
    figures = []
    fin = d.get("Financials") or {}
    for statement, fields in FIELDS.items():
        block = fin.get(statement) or {}
        currency = block.get("currency_symbol")
        for freq in ("quarterly", "yearly"):
            for pe, e in (block.get(freq) or {}).items():
                if not isinstance(e, dict) or not pe:
                    continue
                key = (symbol, freq, pe)
                if key not in periods:
                    kd, basis = known(pe, e.get("filing_date"), report_of.get(pe))
                    periods[key] = (symbol, freq, pe, kd, basis, e.get("currency_symbol") or currency)
                for f in fields:
                    v = _num(e.get(f))
                    if v is not None:
                        figures.append((symbol, freq, pe, statement, f, v))
    return list(periods.values()), figures, reports


def build(src: Path = SRC, db: Path = DB) -> int:
    conn = sqlite3.connect(db)
    conn.executescript(DDL)
    n = 0
    for p in sorted(src.glob("*.json.gz")):
        symbol = p.name[:-len(".json.gz")]
        try:
            d = json.loads(gzip.decompress(p.read_bytes()))
        except Exception as exc:  # noqa: BLE001
            print(f"{symbol}: unreadable ({type(exc).__name__})")
            continue
        per, fig, rep = rows_for(symbol, d)
        for t in ("periods", "figures", "reports"):
            conn.execute(f"DELETE FROM {t} WHERE symbol = ?", (symbol,))
        conn.executemany("INSERT OR REPLACE INTO periods VALUES (?,?,?,?,?,?)", per)
        conn.executemany("INSERT OR REPLACE INTO figures VALUES (?,?,?,?,?,?)", fig)
        conn.executemany("INSERT OR REPLACE INTO reports VALUES (?,?,?,?,?,?)", rep)
        n += 1
        if n % 500 == 0:
            conn.commit()
    conn.commit()
    conn.close()
    return n


def known_at(symbol: str, as_of: str, *, freq: str = "quarterly", db: Path = DB) -> list[tuple]:
    """Every (period_end, statement, field, value) of the periods KNOWN on or
    before `as_of`, newest period first. A period with no known date never
    appears."""
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return conn.execute(
            "SELECT f.period_end, f.statement, f.field, f.value FROM figures f JOIN periods p "
            "USING (symbol, freq, period_end) WHERE f.symbol = ? AND f.freq = ? "
            "AND p.known_date IS NOT NULL AND p.known_date <= ? "
            "ORDER BY f.period_end DESC", (symbol, freq, as_of)).fetchall()
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true",
                    help="build data/eodhd/pit.sqlite from the fetched files")
    ap.add_argument("--show", nargs=2, metavar=("SYMBOL", "ASOF"),
                    help="print what was known about SYMBOL on ASOF (YYYY-MM-DD)")
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    if a.build:
        print(f"{build()} symbols indexed into {DB}")
    if a.show:
        rows = known_at(*a.show)
        newest = rows[0][0] if rows else None
        print(f"{a.show[0]} known on {a.show[1]}: newest quarter {newest}")
        for r in rows:
            if r[0] == newest:
                print(f"  {r[1]:16s} {r[2]:34s} {r[3]:>20,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
