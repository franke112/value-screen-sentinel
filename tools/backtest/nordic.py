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
  USD for the engine but is the TRADING currency: every figure is converted
  from its own report's `currency_symbol` (EVO reports EUR, EQNR USD, MOWI
  EUR; one in seven Nordic files) at the rate on the day it became known,
  so every per-share value and ratio is in the price's currency. A row with
  no currency takes the nearest-dated row's that has one; a label switch
  the revenue does not bear out is overruled by the later label
  (`correct_labels`: EODHD often stamps old periods with the trading
  currency); a switch that fits neither reading, a file with no currency
  at all, or a figure whose rate is missing, does not enter (refused,
  never assumed). Before 2026-11-07 nothing was converted -- the independent
  review's K1 (reference/reviews/method/2026-11-07-OBEROENDE-GRANSKNING.md);
- working capital: EODHD's `changeInWorkingCapital` IS the cash effect, so
  `IncreaseDecreaseInOperatingCapital` = minus it;
- DEBT INCLUDES LEASES (`shortLongTermDebtTotal`): under IFRS 16 the lease
  principal is a FINANCING flow, so rent is NOT in the operating cash flow
  and the lease liability is debt -- the opposite case to E117's US one;
  checked on ACAD.ST: total less leases = 2,656m, the borrowings its ESEF
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
8% below the entry (ACAD's 108.10 under 117.50 is that distance).
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
#: THE LOCK (reference/backtest/PREREG-NORDIC-CONFIRM-2026-11-07.md): dates
#: from here on are the CONFIRMATION, run once, with --confirm, into their
#: own directory; a second run is refused.
CONFIRM_FROM = date(2022, 1, 1)
CONFIRM_DATES = (date(2022, 4, 30), date(2023, 4, 30))
CONFIRM_OUT = ROOT / "data" / "backtest" / "nordic-confirm"
SIZE_MIN_USD = 300e6
STOP = 0.08
COUNTRY = {"ST": "SE", "OL": "NO", "CO": "DK", "HE": "FI"}
FX_TICKER = {"SEK": "SEKUSD=X", "NOK": "NOKUSD=X", "DKK": "DKKUSD=X", "EUR": "EURUSD=X"}
#: currencies fixed to the euro (old Finnish reports are in markka)
EUR_FIXED = {"FIM": 5.94573}
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


def report_currencies(d: dict) -> dict[str, str]:
    """period end -> the currency its statements are in; a period with no
    `currency_symbol` takes the nearest-dated period's that has one."""
    stated: dict[str, str] = {}
    ends: set[str] = set()
    for statement in ("Income_Statement", "Cash_Flow", "Balance_Sheet"):
        for freq in ("yearly", "quarterly"):
            for pe, e in (((d.get("Financials") or {}).get(statement) or {}).get(freq) or {}).items():
                if not isinstance(e, dict):
                    continue
                ends.add(pe)
                c = e.get("currency_symbol")
                if c:
                    stated.setdefault(pe, c)
    if not stated:
        return {}
    keyed = sorted(stated)
    out = {}
    for pe in ends:
        if pe in stated:
            out[pe] = stated[pe]
        else:
            near = min(keyed, key=lambda k: abs((date.fromisoformat(k) - date.fromisoformat(pe)).days))
            out[pe] = stated[near]
    return out


#: a label switch is believed only if converting makes the revenue series
#: at least this much smoother (in log terms) than leaving it as printed
SWITCH_EVIDENCE = 0.5
#: the walk back for the REAL switch (ATTEMPTS #14) looks only between
#: currencies at least this far apart (NOK or SEK against EUR or USD)
SWITCH_FLOOR_RATE = 3.0


def correct_labels(d: dict, currency_of: dict[str, str], fx) -> tuple[dict[str, str], list[str], str | None]:
    """EODHD's `currency_symbol` is not always right: older periods are often
    labelled in the TRADING currency while the figures are in the reporting
    one (Stora Enso's 2019-23 euro figures read SEK, Var Energi's and
    Maersk's dollar figures NOK/DKK, Ericsson's kronor EUR on Helsinki). So
    every switch of label between consecutive periods (yearly, then
    quarterly revenue, newest first) must show in the figures: converted at
    the switch, the series must be clearly smoother than as printed. A
    switch the figures do not bear out means the currency did NOT change,
    and the LATER label -- the one the vendor has kept current -- is carried
    back. Switches between currencies within 25% of each other (SEK/NOK)
    cannot be told apart and stand as labelled. A switch whose figures fit
    NEITHER reading (a merger in the same year, a broken vendor row) is a
    refusal of the whole file. Returns the corrected map, a note per
    relabelling, and the refusal or None."""
    import math
    out = dict(currency_of)
    notes: list[str] = []
    inc = (d.get("Financials") or {}).get("Income_Statement") or {}
    # quarterly FIRST (2026-11-08): a currency change falls inside a fiscal
    # year (Tomra: between Q3 and Q4 2024), which only the quarters can place
    for freq in ("quarterly", "yearly"):
        series = []
        for pe, e in sorted((inc.get(freq) or {}).items()):
            v = _num(e.get("totalRevenue")) if isinstance(e, dict) else None
            if v and v > 0 and pe in out:
                series.append((pe, v))
        for i in range(len(series) - 1, 0, -1):
            (p0, v0), (p1, v1) = series[i - 1], series[i]
            c0, c1 = out[p0], out[p1]
            if c0 == c1:
                continue
            k = fx(c1, c0, date.fromisoformat(p1))
            if k is None or abs(math.log(k)) < math.log(1.25):
                continue
            raw = abs(math.log(v1 / v0))
            conv = abs(math.log(v1 * k / v0))
            step = abs(math.log(k))
            if raw - conv >= SWITCH_EVIDENCE * step:
                continue                                  # borne out: a real switch
            if raw < SWITCH_EVIDENCE * step:              # continuous as printed: one currency
                # DEFECT FIX 2026-11-08 (wrez-devour, ATTEMPTS #14): carry the
                # later label back only as far as the figures stay in it. Walk
                # back over the periods still labelled c0; where the revenue
                # itself jumps by about the rate (converted, it is smooth), the
                # company really changed currency THERE, under one label --
                # Tomra: NOK to EUR for 2024 (14,756 -> 1,348), both labelled
                # NOK, then EUR from 2025. Before this, the EUR label was
                # carried over all of Tomra's NOK years (x8-11).
                floor = ""
                for j in range(i - 1, 0, -1):
                    (q0, w0), (q1, w1) = series[j - 1], series[j]
                    if out[q1] != c0:
                        floor = q1                        # the run of c0 labels ends here
                        break
                    if out[q0] != c0:
                        floor = q0
                        break
                    kj = fx(c1, c0, date.fromisoformat(q1))
                    if kj is None or abs(math.log(kj)) < math.log(SWITCH_FLOOR_RATE):
                        continue      # NOK/DKK, SEK/NOK: a switch cannot be told from a season
                    if (abs(math.log(w1 / w0)) - abs(math.log(w1 * kj / w0))
                            < SWITCH_EVIDENCE * abs(math.log(kj))):
                        continue
                    # the new level must HOLD: the median of up to three
                    # periods each side differs by about the rate (one noisy
                    # quarter of an investment company is not a switch -- VNV)
                    before = statistics.median(v for _, v in series[max(0, j - 3):j])
                    after = statistics.median(v for _, v in series[j:min(i + 1, j + 3)])
                    if abs(math.log(before / (after * kj))) < SWITCH_EVIDENCE * abs(math.log(kj)) \
                            and abs(math.log(before / after)) >= SWITCH_EVIDENCE * abs(math.log(kj)):
                        floor = q0                        # the real switch: after q0
                        break
                for pe in out:
                    if floor < pe <= p0 and out[pe] == c0:
                        out[pe] = c1
                notes.append(f"{c0} label before {p1} read as {c1} (revenue {v0:,.0f} -> {v1:,.0f})"
                             + (f", back to the real switch after {floor}" if floor else ""))
                continue
            return out, notes, (f"label {c0}->{c1} at {p1}: revenue {v0:,.0f} -> {v1:,.0f} "
                                f"fits neither one currency nor the switch")
    return out, notes, None


def fx_factor(frm: str, to: str, day: date) -> float | None:
    """Units of `to` per unit of `frm` on `day` (None if a rate is missing)."""
    peg = 1.0
    if frm in EUR_FIXED:
        frm, peg = "EUR", peg / EUR_FIXED[frm]
    if to in EUR_FIXED:
        to, peg = "EUR", peg * EUR_FIXED[to]
    if frm == to:
        return peg
    a, b = fx_usd(frm, day), fx_usd(to, day)
    return peg * a / b if a and b else None


#: (symbol, why) of every file or figure refused for want of a currency/rate
CURRENCY_REFUSED: list[tuple[str, str]] = []
#: (symbol, note) of every currency label the figures overruled
RELABELLED: list[tuple[str, str]] = []


def quarter_start(end: date) -> date:
    """The first day of the three months ending `end`. DEFECT FIX
    2026-11-08 (ATTEMPTS #17): the start was `(end.replace(day=1) - 62
    days).replace(day=1)`, right only for September (Jul 1 - Sep 30); Q4,
    Q1 and Q2 spanned ~120 days, `xbrl.build_quarters` (80-100 days) dropped
    them, and every Nordic quarterly kill was read on Q3s alone."""
    m, y = end.month - 2, end.year
    if m <= 0:
        m, y = m + 12, y - 1
    return date(y, m, 1)


def facts_from_eodhd(symbol: str, d: dict, fx=None) -> dict:
    """EODHD statements as companyfacts: each entry FILED on its known date,
    in the TRADING currency (`fx(frm, to, day)`, default `fx_factor`)."""
    fx = fx or fx_factor
    hist = (d.get("Earnings") or {}).get("History") or {}
    report_of = {v.get("date"): v.get("reportDate") for v in hist.values() if isinstance(v, dict)}
    gaap: dict = {}
    dei: dict = {}
    trading = (d.get("General") or {}).get("CurrencyCode") or ""
    currency_of = report_currencies(d)
    if not currency_of or not trading:
        CURRENCY_REFUSED.append((symbol, "no reporting or trading currency in the file"))
        return {"facts": {"us-gaap": gaap, "dei": dei}}
    currency_of, notes, problem = correct_labels(d, currency_of, fx)
    if problem:
        CURRENCY_REFUSED.append((symbol, problem))
        return {"facts": {"us-gaap": gaap, "dei": dei}}
    RELABELLED.extend((symbol, n) for n in notes)
    missing_rate: set[str] = set()

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
                         if months == 12 else quarter_start(end))
                k = fx(currency_of[pe], trading, date.fromisoformat(known))
                if k is None:
                    missing_rate.add(currency_of[pe])
                    k_ok = False
                else:
                    k_ok = True
                base = {"end": pe, "filed": known, "form": form,
                        "fp": "FY" if months == 12 else "Q", "accn": f"eodhd-{symbol}-{freq}-{pe}"}
                for field, tag in mapping.items():
                    v = _num(e.get(field))
                    if v is None or not k_ok:
                        continue
                    if tag in POSITIVE:
                        v = abs(v)
                    entry = dict(base, val=v * k)
                    if kind == "dur":
                        entry["start"] = start.isoformat()
                    put(tag, "USD", entry)
                if statement == "Cash_Flow" and k_ok:
                    cwc = _num(e.get("changeInWorkingCapital"))
                    if cwc is not None:
                        put(M.WC_WHOLE, "USD", dict(base, val=-cwc * k, start=start.isoformat()))
                if statement == "Balance_Sheet":
                    sh = _num(e.get("commonStockSharesOutstanding"))
                    if sh:
                        dei.setdefault("EntityCommonStockSharesOutstanding", {"units": {}})[
                            "units"].setdefault("shares", []).append(dict(base, val=sh))
    for c in sorted(missing_rate):
        CURRENCY_REFUSED.append((symbol, f"no {c}->{trading} rate for some figures (those left out)"))
    return {"facts": {"us-gaap": gaap, "dei": dei}}


def universe() -> list[dict]:
    rows = list(csv.DictReader(SYMBOLS.open(encoding="utf-8")))
    return [r for r in rows if r["suffix"] in NORDIC and (r.get("Type") or "").lower() == "common stock"
            and (FUND / f"{r['symbol']}.json.gz").exists()]


SPLIT_NOISE_FLOOR = 0.05
DUPLICATES: list[tuple[str, str, str]] = []   # (date, symbol dropped or replaced, the other company)
DUP_WINDOW = 60          # trading days of returns compared for a duplicate


def return_signature(f, day: date) -> tuple | None:
    """CORRECTION 8 (2026-11-07, ATTEMPTS #5): the last DUP_WINDOW daily
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
    (Atlas Copco's Epiroc, 0.73) -- changes no share count and is not one."""
    ratio = f["close"] / f["adjusted_close"]
    jump = ratio / ratio.shift(1)
    # CORRECTION 5 (2026-11-07, ATTEMPTS #5): EODHD rounds adjusted_close to
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

    EODHD restates share counts for later splits (Atlas Copco 2016: 4,862m on
    today's basis against ~1,215m then; Novo Nordisk the same). Per split
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
    if not currency or not currency.isalpha():
        return None
    t = FX_TICKER.get(currency, f"{currency}USD=X")
    if t not in _FX:
        _FX[t] = PL.prices(t)
    got = PL.close_on(_FX[t], day) if _FX[t] is not None else None
    return got[1] if got else None


def stop_return(f, start: date, end: date) -> float | None:
    """Exit at the first close 8% below the entry close; else held to the end."""
    a = EP.on(f, start, "close")
    if a is None or EP.level_breaks(f, start - timedelta(days=EP.BREAK_GAP_DAYS), start):
        return None
    brk = EP.level_breaks(f, start, end)
    if brk:
        f = f[f.index < brk[0]]       # review 2026-11-08 M2: the company ended at the break
    if EP.suspect_days(f, start, end):
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
    ap.add_argument("--out", type=Path, default=None,
                    help="another output directory for a development run (never the confirmation)")
    a = ap.parse_args(argv)
    dates = list(CONFIRM_DATES) if a.confirm else (a.date or list(TEST_DATES))
    if a.confirm and a.out:
        raise SystemExit("the confirmation writes only to its own directory")
    out_dir = CONFIRM_OUT if a.confirm else (a.out or OUT)
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
        print(f"currency: {len(CURRENCY_REFUSED)} refusals, {len(RELABELLED)} labels overruled", flush=True)
    finally:
        M.tax_for = tax
    return 0


if __name__ == "__main__":
    sys.exit(main())
