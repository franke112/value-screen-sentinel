"""The method's core on NORDIC companies, from EODHD (private data).

    .venv/bin/python -m tools.backtest.nordic                 # every test date, writes data/backtest/nordic/
    .venv/bin/python -m tools.backtest.measure --run-dir data/backtest/nordic --horizon 3

The US backtest reads SEC companyfacts. A Nordic issuer has none, so its
EODHD statements are TRANSLATED into the same shape and the SAME engine runs
on them unchanged (`method.evaluate`, `run.evaluate_caps`): a figure enters
on the day it became KNOWN -- the earnings report date + one weekday
(tools/eodhd_pit.py); a period with no known date never enters.

THE TRANSLATION (each a deliberate choice, named):
- statement lines map to the us-gaap tags `method` and `history` read
  (Revenues, OperatingIncomeLoss, NetIncomeLoss, NetCash...OperatingActivities,
  PaymentsToAcquirePropertyPlantAndEquipment, Assets, StockholdersEquity,
  Goodwill, CashAndCashEquivalentsAtCarryingValue, ...); the unit is labelled
  USD for the engine but is the issuer's own currency, and so is the price,
  so every per-share value and ratio is in one currency;
- working capital: EODHD's `changeInWorkingCapital` IS the cash effect, so
  `IncreaseDecreaseInOperatingCapital` = minus it;
- DEBT INCLUDES LEASES (`shortLongTermDebtTotal`): under IFRS 16 the lease
  principal is a FINANCING flow, so rent is NOT in the operating cash flow
  and the lease liability is debt -- the opposite case to E117's US one;
  checked on one held name against the borrowings its ESEF package tags.
  package tags;
- tax: the country's statutory rate (valuation.STATUTORY_TAX_RATE), not M3's
  US one;
- acquisitions: EODHD gives no line, so every name reads as no acquirer (Q4
  and the deal programme cannot fire): a stated gap;
- size: market cap (shares x close) >= 300 MUSD on the test day, at the
  day's exchange rate; financials and real estate (GICS) out, as Gate 3.

THE BENCHMARK is the EQUAL-WEIGHTED return of every valued Nordic name on the
date (local currency), so "excess" is against the Nordic market the method
chose from, not the S&P 500. Delisting: the `bust` policy of
`eodhd_reprice` (a collapse before delisting is a total loss).

A STOP VARIANT is written beside it: `returns_stop8` exits at the first close
8% below the entry (a typical stop distance).
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import statistics
import sys
import traceback
from datetime import date, timedelta
from pathlib import Path

from vss import valuation as VA

from . import eodhd_reprice as EP
from . import method as M
from . import pilot as PL
from . import run as R
from . import value as V

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import eodhd_pit as EPIT  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FUND = ROOT / "data" / "eodhd" / "fundamentals"
SYMBOLS = ROOT / "data" / "eodhd" / "symbols.csv"     # vss's own copy (2026-11-07)
OUT = ROOT / "data" / "backtest" / "nordic"
NORDIC = ("ST", "OL", "CO", "HE")
TEST_DATES = tuple(date(y, 4, 30) for y in range(2010, 2022))
#: THE LOCK (the private pre-registration): dates
#: from here on are the CONFIRMATION, run once, with --confirm, into their
#: own directory; a second run is refused.
CONFIRM_FROM = date(2022, 1, 1)
CONFIRM_DATES = (date(2022, 4, 30), date(2023, 4, 30))
CONFIRM_OUT = ROOT / "data" / "backtest" / "nordic-confirm"
SIZE_MIN_USD = 300e6
STOP = 0.08
COUNTRY = {"ST": "SE", "OL": "NO", "CO": "DK", "HE": "FI"}
FX_TICKER = {"SEK": "SEKUSD=X", "NOK": "NOKUSD=X", "DKK": "DKKUSD=X", "EUR": "EURUSD=X"}
EXCLUDED_GICS = ("Financials", "Real Estate")
EXCLUDED_SECTORS = ("Financial Services", "Real Estate")   # EODHD's own; banks often carry no GICS
#: IFRS 16: rent is NOT in the operating cash flow and EODHD gives no lease
#: payment line, so a company whose lease liability is a material part of
#: its balance sheet cannot be valued from these statements -- it is
#: refused, not valued high (the first screen put schools, hotels, gyms and
#: care homes at the top for exactly this reason).
LEASE_SHARE_MAX = 0.10


def excluded(g: dict, symbol: str) -> str | None:
    """Why a company is out of the universe, or None."""
    if (g.get("GicSector") or "") in EXCLUDED_GICS or (g.get("Sector") or "") in EXCLUDED_SECTORS:
        return "financials / real estate"
    primary = g.get("PrimaryTicker")
    if primary and primary != symbol:
        return f"secondary listing of {primary}"
    return None


def lease_heavy(d: dict, day: date) -> float | None:
    """The lease liability's share of total assets at the newest balance
    sheet known before `day`, where it is above LEASE_SHARE_MAX; else None."""
    hist = (d.get("Earnings") or {}).get("History") or {}
    report_of = {v.get("date"): v.get("reportDate") for v in hist.values() if isinstance(v, dict)}
    best = None
    bs = (d.get("Financials") or {}).get("Balance_Sheet") or {}
    for freq in ("quarterly", "yearly"):
        for pe, e in (bs.get(freq) or {}).items():
            known, _ = EPIT.known(pe, e.get("filing_date"), report_of.get(pe))
            if known and known < day.isoformat() and (best is None or pe > best[0]):
                best = (pe, e)
    if best is None:
        return None
    lease, assets = _num(best[1].get("capitalLeaseObligations")), _num(best[1].get("totalAssets"))
    if lease and assets and lease / assets > LEASE_SHARE_MAX:
        return lease / assets
    return None

INCOME = {"totalRevenue": "Revenues", "operatingIncome": "OperatingIncomeLoss",
          "netIncome": "NetIncomeLoss", "grossProfit": "GrossProfit",
          "incomeBeforeTax": "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
          "interestExpense": "InterestExpense"}
CASH = {"totalCashFromOperatingActivities": "NetCashProvidedByUsedInOperatingActivities",
        "capitalExpenditures": "PaymentsToAcquirePropertyPlantAndEquipment",
        "stockBasedCompensation": "ShareBasedCompensation"}
BALANCE = {"totalAssets": "Assets", "totalStockholderEquity": "StockholdersEquity",
           "cash": "CashAndCashEquivalentsAtCarryingValue",
           "cashAndShortTermInvestments": "CashCashEquivalentsAndShortTermInvestments",
           "shortLongTermDebtTotal": "LongTermDebt", "goodWill": "Goodwill",
           "propertyPlantAndEquipmentNet": "PropertyPlantAndEquipmentNet",
           "noncontrollingInterestInConsolidatedEntity": "MinorityInterest"}
POSITIVE = ("PaymentsToAcquirePropertyPlantAndEquipment", "InterestExpense", "ShareBasedCompensation")


def _num(v):
    try:
        return None if v in (None, "", "None") else float(v)
    except (TypeError, ValueError):
        return None


def facts_from_eodhd(symbol: str, d: dict) -> dict:
    """EODHD statements as companyfacts: each entry FILED on its known date."""
    hist = (d.get("Earnings") or {}).get("History") or {}
    report_of = {v.get("date"): v.get("reportDate") for v in hist.values() if isinstance(v, dict)}
    gaap: dict = {}
    dei: dict = {}

    def put(tag, unit, entry):
        gaap.setdefault(tag, {"units": {}})["units"].setdefault(unit, []).append(entry)

    fin = d.get("Financials") or {}
    for statement, mapping, kind in (("Income_Statement", INCOME, "dur"),
                                     ("Cash_Flow", CASH, "dur"),
                                     ("Balance_Sheet", BALANCE, "inst")):
        for freq, form, months in (("yearly", "10-K", 12), ("quarterly", "10-Q", 3)):
            for pe, e in ((fin.get(statement) or {}).get(freq) or {}).items():
                if not isinstance(e, dict):
                    continue
                known, _ = EPIT.known(pe, e.get("filing_date"), report_of.get(pe))
                if known is None:
                    continue
                end = date.fromisoformat(pe)
                start = (PL.years_after(end, -1) + timedelta(days=1)
                         if months == 12 else
                         (end.replace(day=1) - timedelta(days=62)).replace(day=1))
                base = {"end": pe, "filed": known, "form": form,
                        "fp": "FY" if months == 12 else "Q", "accn": f"eodhd-{symbol}-{freq}-{pe}"}
                for field, tag in mapping.items():
                    v = _num(e.get(field))
                    if v is None:
                        continue
                    if tag in POSITIVE:
                        v = abs(v)
                    entry = dict(base, val=v)
                    if kind == "dur":
                        entry["start"] = start.isoformat()
                    put(tag, "USD", entry)
                if statement == "Cash_Flow":
                    cwc = _num(e.get("changeInWorkingCapital"))
                    if cwc is not None:
                        put(M.WC_WHOLE, "USD", dict(base, val=-cwc, start=start.isoformat()))
                if statement == "Balance_Sheet":
                    sh = _num(e.get("commonStockSharesOutstanding"))
                    if sh:
                        dei.setdefault("EntityCommonStockSharesOutstanding", {"units": {}})[
                            "units"].setdefault("shares", []).append(dict(base, val=sh))
    return {"facts": {"us-gaap": gaap, "dei": dei}}


def universe() -> list[dict]:
    rows = list(csv.DictReader(SYMBOLS.open(encoding="utf-8")))
    return [r for r in rows if r["suffix"] in NORDIC and (r.get("Type") or "").lower() == "common stock"
            and (FUND / f"{r['symbol']}.json.gz").exists()]


SPLIT_NOISE_FLOOR = 0.05
DUPLICATES: list[tuple[str, str, str]] = []   # (date, symbol dropped or replaced, the other company)
DUP_WINDOW = 60          # trading days of returns compared for a duplicate


def return_signature(f, day: date) -> tuple | None:
    """CORRECTION 8 (2026-11-07, logged in the private attempt log): the last DUP_WINDOW daily
    returns before `day`, rounded. Two tickers with the same signature are
    ONE security listed twice (a renamed or re-registered ticker); compared
    on RETURNS, not levels, since two copies may be split-adjusted apart
    (DonkeyInvestor found 577 such pairs)."""
    w = f[f.index < day.isoformat()]["adjusted_close"].tail(DUP_WINDOW + 1)
    if len(w) < DUP_WINDOW // 2:
        return None
    r = (w / w.shift(1) - 1).dropna().round(5)
    if not len(r) or (r == 0).all():
        return None
    return tuple(r.tolist())


def splits(f) -> list[tuple[str, float]]:
    """(date, k) for every share split in the price file: the printed close
    jumps against the adjusted one by a near-whole factor (2:1 -> k 2,
    1:10 reverse -> k 0.1). A jump that is no whole factor -- a spin-off
    (a spin-off adjusts the price by a non-whole factor) -- changes no share count and is not one."""
    ratio = f["close"] / f["adjusted_close"]
    jump = ratio / ratio.shift(1)
    # CORRECTION 5 (2026-11-07, logged in the private attempt log): EODHD rounds adjusted_close to
    # four decimals, so where it is small the ratio is rounding noise and
    # "jumps" (DonkeyInvestor). A jump is read only where the adjusted close
    # is at least SPLIT_NOISE_FLOOR on both days.
    adj = f["adjusted_close"]
    trusted = (adj >= SPLIT_NOISE_FLOOR) & (adj.shift(1) >= SPLIT_NOISE_FLOOR)
    out = []
    for d, j in jump[((jump > 1.25) | (jump < 0.8)) & trusted].items():
        k = 1 / float(j)
        for whole in (2, 3, 4, 5, 6, 8, 10, 15, 20, 25, 50, 100):
            if abs(k - whole) / whole < 0.03:
                out.append((d, float(whole)))
            elif abs(1 / k - whole) / whole < 0.03:
                out.append((d, 1.0 / whole))
    return out


def shares_known(facts: dict, day: date, f=None) -> float | None:
    """The newest share count known before `day`, ON THE DAY'S SHARE BASIS.

    EODHD restates share counts for later splits (a 4:1 split shows up as four
    times the shares in every earlier period). Per split
    after `day`, the series itself decides: if the count jumps by about k
    across the split, it is as reported and is left; if it does not, it is
    restated and is divided by k."""
    rows = sorted((e for e in facts["facts"]["dei"].get("EntityCommonStockSharesOutstanding", {})
                   .get("units", {}).get("shares", [])), key=lambda e: e["end"])
    known = [e for e in rows if e["filed"] < day.isoformat()]
    if not known:
        return None
    val = max(known, key=lambda e: (e["end"], e["filed"]))["val"]
    if f is None:
        return val
    for when, k in splits(f):
        if when <= day.isoformat():
            continue
        before = [e["val"] for e in rows if e["end"] < when]
        after = [e["val"] for e in rows if e["end"] >= when]
        if before and after and before[-1] > 0:
            jumped = after[0] / before[-1]
            if abs(jumped / k - 1) < 0.25:
                continue            # as reported: the count already moved at the split
        val = val / k
    return val


_FX: dict = {}


def fx_usd(currency: str, day: date) -> float | None:
    if currency == "USD":
        return 1.0
    t = FX_TICKER.get(currency)
    if t is None:
        return None
    if t not in _FX:
        _FX[t] = PL.prices(t)
    got = PL.close_on(_FX[t], day) if _FX[t] is not None else None
    return got[1] if got else None


def stop_return(f, start: date, end: date) -> float | None:
    """Exit at the first close 8% below the entry close; else held to the end."""
    a = EP.on(f, start, "close")
    if a is None:
        return None
    window = f[(f.index > start.isoformat()) & (f.index <= end.isoformat())]
    hit = window[window["close"] <= a[1] * (1 - STOP)]
    if len(hit):
        when = hit.index[0]
        adj_a = EP.on(f, start, "adjusted_close")
        return float(window.loc[when, "adjusted_close"]) / adj_a[1] - 1 if adj_a else None
    ret, _ = EP.total_return(f, start, end, "bust")
    return ret


def evaluate_date(as_of: date, names: list[dict]) -> list[dict]:
    day = PL.trading_day(as_of)
    out, seen_company = [], {}
    seen_signature: dict[tuple, tuple[str, float]] = {}
    for r in names:
        sym = r["symbol"]
        f = EP.frame(sym)
        if f is None:
            continue
        got = EP.on(f, day)
        if got is None:
            continue
        d = json.loads(gzip.decompress((FUND / f"{sym}.json.gz").read_bytes()))
        g = d.get("General") or {}
        if excluded(g, sym):
            continue
        facts = facts_from_eodhd(sym, d)
        sh = shares_known(facts, day, f)
        rate = fx_usd(g.get("CurrencyCode") or r.get("Currency") or "", day)
        if not sh or rate is None or sh * got[1] * rate < SIZE_MIN_USD:
            continue
        # one row per company: the share class with the larger market cap
        company = g.get("Name") or sym
        cap = sh * got[1]
        sig = return_signature(f, day)
        if sig is not None and sig in seen_signature and seen_signature[sig][0] != company:
            other_company, other_cap = seen_signature[sig]
            DUPLICATES.append((as_of.isoformat(), sym, other_company))
            if other_cap >= cap:
                continue                      # a duplicate of a security already in
            out = [x for x in out if x.get("company") != other_company]
            seen_company.pop(other_company, None)
        if sig is not None:
            seen_signature[sig] = (company, cap)
        if company in seen_company and seen_company[company][0] >= cap:
            continue
        country = COUNTRY[r["suffix"]]
        M.tax_for = lambda y, c=country: VA.STATUTORY_TAX_RATE[c]
        base = {"symbol": sym, "company": company, "cik": sym, "country": country,
                "as_of": as_of.isoformat(), "trading_day": day.isoformat(),
                "currency": g.get("CurrencyCode"), "market_cap_usd": cap * rate}
        heavy = lease_heavy(d, day)
        if heavy is not None:
            out.append({**base, "status": f"leases {heavy:.0%} of assets: rent not in the data (refused)"})
            seen_company[company] = (cap, sym)
            continue
        try:
            row = R.evaluate_caps(facts, day, ticker=sym, cik=sym, sic=None)
            row.update(base)
            if row.get("shares") and sh and abs(row["shares"] / sh - 1) > 0.01:
                # M5 read the restated count; every per-share figure scales with it
                k = row["shares"] / sh
                row["shares"] = sh
                for key in ("fv_base", "fv_bear", "fv_ex_programme"):
                    if row.get(key) is not None:
                        row[key] *= k
                for c in row["caps"].values():
                    for key in ("fv_base", "fv_bear", "fv_ex_programme"):
                        if c.get(key) is not None:
                            c[key] *= k
                row["notes"] = list(row.get("notes") or []) + [f"shares rebased to the day's split basis (x{1 / k:.3f})"]
            M.with_price(row, got[1], None)
            row.pop("cap_check", None)   # no public-float check exists for a Nordic name
            for c in row["caps"].values():
                if c.get("fv_base") is not None and got[1] > 0:
                    c["fv_over_price"] = c["fv_base"] / got[1]
            row["returns"], row["returns_stop8"], row["exit"] = {}, {}, {}
            for h in PL.HORIZONS:
                end = PL.years_after(day, h)
                row["returns"][h], row["exit"][h] = EP.total_return(f, day, end, "bust")
                row["returns_stop8"][h] = stop_return(f, day, end)
            row["passes_quality"] = V.passes_quality(row) if row["quality"] else None
            row["measured_kill"] = V.measured_kill(row)
            row.pop("fcf_years", None)
        except Exception as exc:  # noqa: BLE001 -- one name never stops the run
            row = {**base, "skip": f"error: {type(exc).__name__}: {exc}"[:300],
                   "trace": traceback.format_exc()[-600:]}
        if company in seen_company:
            out = [x for x in out if x.get("company") != company]
        seen_company[company] = (cap, sym)
        out.append(row)
    # the benchmark: the equal-weighted Nordic market of the valued names
    for h in PL.HORIZONS:
        rets = [x["returns"][h] for x in out if x.get("returns", {}).get(h) is not None]
        bench = statistics.mean(rets) if rets else None
        for x in out:
            if "returns" in x:
                x.setdefault("index_returns", {})[h] = bench
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", action="append", type=date.fromisoformat)
    ap.add_argument("--confirm", action="store_true",
                    help="THE one pre-registered confirmation run (2022-04-30, 2023-04-30)")
    a = ap.parse_args(argv)
    dates = list(CONFIRM_DATES) if a.confirm else (a.date or list(TEST_DATES))
    out_dir = CONFIRM_OUT if a.confirm else OUT
    if not a.confirm and any(d >= CONFIRM_FROM for d in dates):
        raise SystemExit("dates from 2022 on are the locked confirmation: only --confirm, once")
    if a.confirm and CONFIRM_OUT.exists() and any(CONFIRM_OUT.glob("*.jsonl")):
        raise SystemExit(f"the confirmation has been run ({CONFIRM_OUT}); it is not run again")
    names = universe()
    out_dir.mkdir(parents=True, exist_ok=True)
    tax = M.tax_for
    try:
        for d in dates:
            rows = evaluate_date(d, names)
            (out_dir / f"{d.isoformat()}.jsonl").write_text(
                "".join(json.dumps(r, default=str) + "\n" for r in rows))
            ok = [r for r in rows if r.get("status") == "ok"]
            print(f"{d}: {len(rows)} companies over the size line, {len(ok)} valued, "
                  f"{sum(1 for r in ok if V.passes_quality(r))} pass Q1-Q4", flush=True)
        for dup in DUPLICATES:
            print(f"duplicate (identical returns): {dup}", flush=True)
    finally:
        M.tax_for = tax
    return 0


if __name__ == "__main__":
    sys.exit(main())
