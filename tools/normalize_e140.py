#!/usr/bin/env python
"""E140: re-value a struck name on a NORMALISED FCF0 and a PRO FORMA bridge.

    .venv/bin/python tools/normalize_e140.py --ticker CENTA [--price 39.13]
    .venv/bin/python tools/normalize_e140.py --all --prices prices.json

The owner's ruling of 2026-10-27 (FRAMEWORK-EDITS E140), three parts:

1. FCF0 is the MEAN OF THE LAST THREE FISCAL YEARS of operating cash flow
   with the change in operating working capital taken OUT (receivables,
   inventories, prepaid and other operating assets, payables, accrued
   liabilities, deferred revenue), less capex and SBC. Income-tax, lease
   and long-term lines stay in: a tax-reserve release is not working
   capital (HRB FY2026: the 84.1m discrete benefit is reversed on that line).
2. The interest add-back (E34/E34.1/E115) is taken AFTER TAX at the
   statutory rate of the filer's home country.
3. A deal after the basis enters the bridge at its price: cash paid,
   earn-out at its maximum, a put on a retained stake at its pro-rata value.
   The acquired business's cash flow enters only where the issuer has
   filed figures for it; an unknown price is a LOW-HIGH range, never left
   out. Deals are read from reference/events/<TICKER>.yaml.

Everything else is the record's own: growth view, rate, horizon, terminal,
the other bridge legs, the divisor. Nothing here writes the watchlist, a
store or a run record -- it prints, and with --write it writes
reference/normalized/<TICKER>-<date>.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vss.valuation import equity_value_per_share  # noqa: E402
from vss.xbrl import user_agent  # noqa: E402

# Statutory corporate rate by listing country (combined federal + typical
# state for the US). Part 2 of E140 names the rate as statutory, so it is a
# table, not a per-filer reading.
STATUTORY = {"US": 0.25, "SE": 0.206, "GB": 0.25, "DK": 0.22, "NO": 0.22,
             "FI": 0.20, "FR": 0.258, "DE": 0.30, "IE": 0.125}
SUFFIX_COUNTRY = {".ST": "SE", ".L": "GB", ".CO": "DK", ".OL": "NO",
                  ".HE": "FI", ".PA": "FR", ".DE": "DE"}

# Operating working-capital tags. sign = the cash-flow effect of a positive
# reported value: an INCREASE in an asset uses cash (-1), an increase in a
# liability provides it (+1). us-gaap tags these as the change itself.
WC_ASSETS = ["IncreaseDecreaseInAccountsReceivable", "IncreaseDecreaseInReceivables",
             "IncreaseDecreaseInAccountsAndOtherReceivables",
             "IncreaseDecreaseInAccountsAndNotesReceivable",
             "IncreaseDecreaseInInventories", "IncreaseDecreaseInRetailRelatedInventories",
             "IncreaseDecreaseInPrepaidDeferredExpenseAndOtherAssets",
             "IncreaseDecreaseInPrepaidExpense", "IncreaseDecreaseInOtherCurrentAssets",
             "IncreaseDecreaseInOtherOperatingAssets",
             "IncreaseDecreaseInPrepaidExpensesOther",
             "IncreaseDecreaseInContractWithCustomerAsset"]
WC_LIABS = ["IncreaseDecreaseInAccountsPayable", "IncreaseDecreaseInAccountsPayableTrade",
            "IncreaseDecreaseInAccruedLiabilities",
            "IncreaseDecreaseInAccountsPayableAndAccruedLiabilities",
            "IncreaseDecreaseInAccountsPayableAndOtherOperatingLiabilities",
            "IncreaseDecreaseInAccruedLiabilitiesAndOtherOperatingLiabilities",
            "IncreaseDecreaseInEmployeeRelatedLiabilities",
            "IncreaseDecreaseInContractWithCustomerLiability",
            "IncreaseDecreaseInDeferredRevenue",
            "IncreaseDecreaseInOtherCurrentLiabilities",
            "IncreaseDecreaseInOtherOperatingLiabilities",
            "IncreaseDecreaseInOtherAccruedLiabilities"]
WC_TOTAL = "IncreaseDecreaseInOperatingCapital"   # increase = use of cash

# A combined tag and its own components can BOTH be tagged for one year
# (Autoliv FY2023: AccountsPayable 255 + AccruedLiabilities 172 and their
# sum AccountsPayableAndAccruedLiabilities 426). Reading all three counts the
# movement twice, so a combined tag is dropped wherever a component of it
# is present for the same year.
COMBINED = {
    "IncreaseDecreaseInAccountsPayableAndAccruedLiabilities":
        ("IncreaseDecreaseInAccountsPayable", "IncreaseDecreaseInAccountsPayableTrade",
         "IncreaseDecreaseInAccruedLiabilities"),
    "IncreaseDecreaseInAccruedLiabilitiesAndOtherOperatingLiabilities":
        ("IncreaseDecreaseInAccruedLiabilities", "IncreaseDecreaseInOtherOperatingLiabilities"),
    "IncreaseDecreaseInAccountsPayableAndOtherOperatingLiabilities":
        ("IncreaseDecreaseInAccountsPayable", "IncreaseDecreaseInOtherOperatingLiabilities"),
    "IncreaseDecreaseInReceivables":
        ("IncreaseDecreaseInAccountsReceivable",),
    "IncreaseDecreaseInAccountsAndOtherReceivables":
        ("IncreaseDecreaseInAccountsReceivable",),
}

# E123's shape: where the OPERATING ASSET IS INVENTORY (a homebuilder's
# homes and land), buying it is the business, not a working-capital swing,
# so E140 leaves the inventory line IN the flow for these filers.
INVENTORY_IS_THE_BUSINESS = {"NVR", "PHM"}

# Struck names that are not on the watchlist carry no `cik` there.
OFF_WATCHLIST_CIK = {"PEP": 77476, "INGR": 1046257}


def country(ticker: str) -> str:
    for suf, c in SUFFIX_COUNTRY.items():
        if ticker.endswith(suf):
            return c
    return "US"


def latest_record(ticker: str) -> tuple[Path, dict]:
    paths = sorted(glob.glob(str(ROOT / f"reference/run-records/{ticker}-20*.json")))
    best = max(((p, json.load(open(p))) for p in paths), key=lambda t: t[1]["run_ts"])
    return Path(best[0]), best[1]


def companyfacts(cik: int) -> dict:
    u = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
    req = urllib.request.Request(u, headers={"User-Agent": user_agent()})
    for _ in range(3):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception:
            time.sleep(2)
    raise RuntimeError(f"companyfacts {cik} unreachable")


def annual(facts: dict, tag: str) -> dict[str, float]:
    """Fiscal-year duration values from 10-K filings, by period end; the
    latest filing wins for a restated year."""
    node = facts.get("us-gaap", {}).get(tag)
    if not node:
        return {}
    out: dict[str, tuple[str, float]] = {}
    for unit in node["units"].values():
        for x in unit:
            if x.get("form") not in ("10-K", "10-K/A") or not x.get("start"):
                continue
            s = dt.date.fromisoformat(x["start"])
            e = dt.date.fromisoformat(x["end"])
            if not 350 <= (e - s).days <= 380:
                continue
            k = x["end"]
            if k not in out or x["filed"] > out[k][0]:
                out[k] = (x["filed"], float(x["val"]))
    return {k: v for k, (_, v) in out.items()}


def first(facts, tags):
    for t in tags:
        a = annual(facts, t)
        if a:
            return t, a
    return None, {}


def working_capital(facts: dict, end: str, ticker: str = "") -> tuple[float, list[str]]:
    """Cash-flow effect of the operating working-capital change in the year
    ending `end`, and the tags it was read from."""
    total = annual(facts, WC_TOTAL).get(end)
    present = {t for t in WC_ASSETS + WC_LIABS if annual(facts, t).get(end) is not None}
    skip = {c for c, parts in COMBINED.items() if c in present and present & set(parts)}
    if ticker in INVENTORY_IS_THE_BUSINESS:
        skip |= {"IncreaseDecreaseInInventories", "IncreaseDecreaseInRetailRelatedInventories"}
    used, wc = [], 0.0
    for tags, sign in ((WC_ASSETS, -1.0), (WC_LIABS, +1.0)):
        for t in tags:
            v = annual(facts, t).get(end)
            if v is not None and t not in skip:
                wc += sign * v
                used.append(f"{t}={v / 1e6:,.1f}")
    if not used and total is not None:
        return -total, [f"{WC_TOTAL}={total / 1e6:,.1f}"]
    return wc, used


def normalised_fcf0(rec: dict, facts: dict, years: int = 3) -> dict:
    t_ocf, ocf = first(facts, ["NetCashProvidedByUsedInOperatingActivities"])
    t_cap, cap = first(facts, ["PaymentsToAcquirePropertyPlantAndEquipment",
                               "PaymentsToAcquireProductiveAssets"])
    t_sbc, sbc = first(facts, ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"])
    ends = sorted(ocf)[-years:]
    rows = []
    for e in ends:
        wc, used = working_capital(facts, e, rec["ticker"])
        row = {"end": e, "ocf": ocf[e], "wc": wc, "capex": cap.get(e),
               "sbc": sbc.get(e, 0.0) if rec["sbc"].get("treatment") == "deducted" else 0.0,
               "wc_tags": used}
        if not used:
            raise SystemExit(f"{rec['ticker']}: NO WORKING-CAPITAL TAGS for the year to {e} -- "
                             f"E140 cannot normalise from the tags; a hand reading is needed")
        # A receivable that is a LOAN BOOK (HRB's Emerald Advance) grows every
        # year by roughly the losses written off, and the provision for those
        # losses is added back above it. Taking the receivable change out
        # while leaving the provision in counts the credit loss as cash
        # earned, so where the receivable leg is stripped the provision is
        # deducted with it.
        prov = annual(facts, "ProvisionForDoubtfulAccounts").get(e) or \
            annual(facts, "ProvisionForLoanLeaseAndOtherLosses").get(e) or \
            annual(facts, "ProvisionForLoanAndLeaseLosses").get(e) or 0.0
        receivable_stripped = any(t.startswith(("IncreaseDecreaseInAccountsReceivable",
                                                "IncreaseDecreaseInReceivables",
                                                "IncreaseDecreaseInAccountsAndOtherReceivables",
                                                "IncreaseDecreaseInAccountsAndNotesReceivable"))
                                  for t in used)
        row["provision"] = prov if receivable_stripped else 0.0
        if row["capex"] is None:
            raise SystemExit(f"{rec['ticker']}: no capex tag for the year to {e}")
        row["fcf_ex_wc"] = (row["ocf"] - wc - row["capex"] - row["sbc"] - row["provision"])
        rows.append(row)
    rate = STATUTORY[country(rec["ticker"])]
    interest = rec["interest"].get("net_interest_paid") or 0.0
    addback = interest * (1 - rate) if rec["interest"].get("in_operating_cash_flow") else 0.0
    nci = abs(rec.get("nci_dividends_paid") or 0.0)  # E105: always deducted
    mean = statistics.mean(r["fcf_ex_wc"] for r in rows)
    return {"rows": rows, "mean_ex_wc": mean, "interest": interest, "tax_rate": rate,
            "addback": addback, "nci": nci, "fcf0": mean + addback - nci,
            "tags": {"ocf": t_ocf, "capex": t_cap, "sbc": t_sbc}}


def events(ticker: str) -> dict:
    p = ROOT / f"reference/events/{ticker}.yaml"
    if not p.exists():
        raise SystemExit(f"{ticker}: NO EVENTS LEDGER at {p} -- E140 refuses to value a "
                         f"name whose post-basis deals have not been listed")
    return yaml.safe_load(p.read_text()) or {}


def value(rr, fcf0: float, added_debt: float, growth: float) -> float:
    """The record's own arithmetic with FCF0 replaced and the bridge moved.
    Both arguments are in WHOLE units; the record's money unit must be whole
    (an XBRL store), which `run` checks."""
    return rr._strike_unchecked(growth, fcf0_adjustment=fcf0 - rr.fcf0(),
                                net_cash_adjustment=-added_debt)


def run(ticker: str, price: float | None, write: bool) -> dict:
    from vss.runrecord import RunRecord
    path, rec = latest_record(ticker)
    rr = RunRecord.from_dict(rec)
    if rr.money_unit != "whole":
        raise SystemExit(f"{ticker}: store money unit {rr.money_unit!r} -- not an XBRL store; hand reading")
    wl = {e["ticker"]: e for e in yaml.safe_load((ROOT / "config/watchlist.yaml").read_text())["tickers"]}
    cik = (wl.get(ticker) or {}).get("cik") or rec.get("cik") or OFF_WATCHLIST_CIK.get(ticker)
    if not cik:
        raise SystemExit(f"{ticker}: no CIK -- not a US XBRL filer; E140 needs a hand reading")
    facts = companyfacts(int(cik))["facts"]
    n = normalised_fcf0(rec, facts)
    ev = events(ticker)
    base_nd = rec["bridge"]["net_debt"]
    adds = [(d["name"], float(d["low"]), float(d["high"])) for d in ev.get("deals", [])]
    flows = sum(float(d.get("fcf", 0.0)) for d in ev.get("deals", []))
    nd_low = base_nd + sum(a[1] for a in adds)
    nd_high = base_nd + sum(a[2] for a in adds)
    g = rec["growth"]
    out = {"ticker": ticker, "record": path.name, "n": n, "base_nd": base_nd, "adds": adds,
           "flows": flows, "nd_low": nd_low, "nd_high": nd_high, "growth": g, "price": price,
           "old_fcf0": rr.fcf0(),
           "old": {k: rr._strike_unchecked(g[k]) for k in ("bear", "base", "bull")}}
    f0 = n["fcf0"] + flows
    out["new_fcf0"] = f0
    out["new_high_debt"] = {k: value(rr, f0, nd_high - base_nd, g[k]) for k in ("bear", "base", "bull")}
    out["new_low_debt"] = {k: value(rr, f0, nd_low - base_nd, g[k]) for k in ("bear", "base", "bull")}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--price", type=float)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    print(json.dumps(run(a.ticker, a.price, a.write), indent=1, default=str))
