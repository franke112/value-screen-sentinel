"""The method's core on one name and one date, without the engine's store
(backtest path 1, owner 2026-10-29).

The pilot (reference/backtest/PILOT-2018.md) found that the engine values 1
name of 50 off tags alone: live, a session completes the store by hand. This
module tests the IDEA, not that code path. It takes the facts cut at the
test date (`pit.clip`) and the history the engine would have built from them
(`pit.history_at`), and applies the rules below and nothing else. Every rule
the engine has and this lacks, or that is replaced, is named here; a figure
the rules cannot give is a refusal in `status`, never a silent default.

FROM THE ENGINE, UNCHANGED: E144's derived growth, E143's cycle levels,
E142's ROIIC and deal-programme value, E145's Q1-Q4, the ten-year DCF at
r 9.5% with 2.5% terminal growth (`valuation.equity_value_per_share`).

THE RULES THAT REPLACE A SESSION'S HAND (each a column on the row):

M1  FCF0 (E140(1)) = mean of the last three fiscal years of
    OCF - cash effect of operating working capital - capex - SBC
    + interest x (1 - t). OCF and capex must be tagged in all three years,
    or the name is refused. A year with no working-capital, SBC or interest
    tag takes zero for it, and the count of such zeros is on the row.
M2  Working capital per year: `IncreaseDecreaseInOperatingCapital` where
    tagged; else one tag per group (receivables, inventories, prepaid and
    other, payables, accrued, deferred revenue), the first of each group's
    list; the combined payables-and-accrued tag only where neither part is
    tagged (E140's combined-tag rule). Homebuilders (SIC 1531) keep
    inventory in the flow (E123). A tag larger than 25% of the year's
    revenue is a gross presentation, not a movement (MSFT tags 52bn of
    unearned revenue deferred and the 48bn recognised on its own line),
    and is left out; the count of such drops is `wc_dropped`.
M3  t is 38% for a fiscal year ending before 2018 and 25% after (federal
    35% / 21% plus a typical state); Q1 uses the rate at the test date.
M4  Net debt at the newest balance sheet filed before the test date:
    debt (LongTermDebt, else its parts, plus short-term borrowings and
    commercial paper) - cash and short-term investments (the combined tag
    where stated, else cash plus the investment tags) + minority
    interest. Lease liabilities are not debt (E117: rent is in FCF0).
    Pension deficits are NOT in (E146 is not applied).
M5  Shares: the cover-page count (dei) of the newest filing before the
    test date, all classes summed; the price is the unadjusted close of
    the same day, so both are on the share basis of the time.
M6  Growth where E144 gives none (fewer than five organic years): the
    lower of revenue CAGR over the years there are (at least three) and
    owner earnings per share CAGR, capped at 4% and floored at -3%; bear
    two points lower, floored at -3%; `growth_source` says FALLBACK.
    Fewer than three years: refused.
M7  No events ledger: deals after the basis are not in the bridge. A
    repeat buyer (acquisitions paid in two of the last three years, mean
    above 1% of revenue) carries E142's deal-programme value at its ROIIC.
M8  §4.2.1, .2, .5, .7 from the tagged quarters (`value.kills`), without
    Gate 3's derived leverage. §4.2.3 and §4.2.6 are not evaluated.

COMPARATORS on the same row (literature review, 2026-10-29): EBIT/EV,
mean FCF / market cap, gross profit / assets (Novy-Marx), Greenblatt's
return on capital, Piotroski's F-score. They need the price, so
`with_price` fills them.
"""
from __future__ import annotations

import statistics
from datetime import date

from vss import history as HI
from vss import valuation as VA

from . import pit as P
from . import value as V

# --- M2: working-capital groups -------------------------------------------
WC_WHOLE = "IncreaseDecreaseInOperatingCapital"
WC_ASSETS = (
    ("IncreaseDecreaseInAccountsReceivable", "IncreaseDecreaseInAccountsAndOtherReceivables",
     "IncreaseDecreaseInReceivables", "IncreaseDecreaseInAccountsAndNotesReceivable"),
    ("IncreaseDecreaseInInventories", "IncreaseDecreaseInRetailRelatedInventories"),
    ("IncreaseDecreaseInPrepaidDeferredExpenseAndOtherAssets", "IncreaseDecreaseInPrepaidExpense",
     "IncreaseDecreaseInOtherCurrentAssets", "IncreaseDecreaseInPrepaidExpensesOther"),
)
WC_PAYABLES = ("IncreaseDecreaseInAccountsPayable", "IncreaseDecreaseInAccountsPayableTrade")
WC_ACCRUED = ("IncreaseDecreaseInAccruedLiabilities", "IncreaseDecreaseInOtherAccruedLiabilities",
              "IncreaseDecreaseInOtherCurrentLiabilities")
WC_COMBINED = "IncreaseDecreaseInAccountsPayableAndAccruedLiabilities"
WC_DEFERRED = ("IncreaseDecreaseInContractWithCustomerLiability", "IncreaseDecreaseInDeferredRevenue")
INVENTORY_IS_THE_BUSINESS_SIC = (1531,)

SBC_TAGS = ("ShareBasedCompensation", "AllocatedShareBasedCompensationExpense")
INTEREST_TAGS = ("InterestPaidNet", "InterestPaid") + HI.XBRL_INTEREST

# --- M4 -------------------------------------------------------------------
DEBT_WHOLE = ("LongTermDebt", "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities")
DEBT_LONG = ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations", "SeniorNotes")
DEBT_CURRENT = ("LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent", "DebtCurrent")
DEBT_SHORT = ("ShortTermBorrowings", "CommercialPaper")
CASH_TAGS = ("CashAndCashEquivalentsAtCarryingValue",
             "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "Cash")
INVESTMENT_TAGS = ("ShortTermInvestments", "MarketableSecuritiesCurrent",
                   "AvailableForSaleSecuritiesDebtSecuritiesCurrent")
#: one tag for both, where the filer states it (MSFT: 7.7bn cash, 132bn with investments)
CASH_AND_INVESTMENTS = "CashCashEquivalentsAndShortTermInvestments"
MINORITY_TAGS = ("MinorityInterest",)

# --- M3, M6, M7 -----------------------------------------------------------
TAX_BEFORE_2018, TAX_FROM_2018 = 0.38, 0.25
FALLBACK_MIN_YEARS = 3
REPEAT_BUYER_SHARE = 0.01
RATE = VA.HURDLE_RATE


def tax_for(year_end: int | date) -> float:
    y = year_end if isinstance(year_end, int) else year_end.year
    return TAX_BEFORE_2018 if y < 2018 else TAX_FROM_2018


# --- reading the cut facts ------------------------------------------------
def _gaap(cut: dict) -> dict:
    return cut.get("facts", {}).get("us-gaap", {})


def annual(cut: dict, tag: str) -> dict[int, float]:
    """Fiscal-year label -> value, 10-K FY durations, as `history` labels."""
    return {int(e[:4]): v for e, v in
            HI._annual_facts(_gaap(cut), tag, duration=True, splits=False).items()}


def annual_instant(cut: dict, tag: str) -> dict[int, float]:
    return {int(e[:4]): v for e, v in
            HI._annual_facts(_gaap(cut), tag, duration=False, splits=False).items()}


def first_of(cut: dict, tags, year: int):
    for t in tags:
        v = annual(cut, t).get(year)
        if v is not None:
            return v, t
    return None, None


def instants(cut: dict, tag: str) -> dict[str, float]:
    """Balance-sheet end -> value from 10-K and 10-Q, newest filing of an end."""
    best: dict[str, tuple[str, float]] = {}
    for unit, rows in _gaap(cut).get(tag, {}).get("units", {}).items():
        if unit != "USD":
            continue
        for r in rows:
            if "start" in r or r.get("form") not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
                continue
            prev = best.get(r["end"])
            if prev is None or r["filed"] > prev[0]:
                best[r["end"]] = (r["filed"], float(r["val"]))
    return {e: v for e, (_, v) in best.items()}


WC_GROSS_SHARE = 0.25


def wc_cash_effect(cut: dict, year: int, sic, revenue: float | None = None
                   ) -> tuple[float | None, int]:
    """M2. (cash effect, tags dropped as gross). Positive = working capital
    released cash. None = nothing tagged."""
    limit = None if not revenue else WC_GROSS_SHARE * abs(revenue)
    dropped = 0

    def ok(v):
        nonlocal dropped
        if v is not None and limit is not None and abs(v) > limit:
            dropped += 1
            return None
        return v

    whole = ok(annual(cut, WC_WHOLE).get(year))
    if whole is not None:
        return -whole, dropped
    total, found = 0.0, False
    groups = list(WC_ASSETS)
    if sic is not None and int(sic) in INVENTORY_IS_THE_BUSINESS_SIC:
        groups = [g for g in groups if "IncreaseDecreaseInInventories" not in g]
    for g in groups:
        v = ok(first_of(cut, g, year)[0])
        if v is not None:
            total, found = total - v, True
    ap, _ = first_of(cut, WC_PAYABLES, year)
    ac, _ = first_of(cut, WC_ACCRUED, year)
    if ap is None and ac is None:
        ap, _ = first_of(cut, (WC_COMBINED,), year)
    for v in (ok(ap), ok(ac), ok(first_of(cut, WC_DEFERRED, year)[0])):
        if v is not None:
            total, found = total + v, True
    return (total if found else None), dropped


def balance_sheet(cut: dict) -> dict | None:
    """M4 at the newest end that tags cash."""
    cash_by_end: dict[str, float] = {}
    for t in CASH_TAGS:
        for e, v in instants(cut, t).items():
            cash_by_end.setdefault(e, v)
    if not cash_by_end:
        return None
    end = max(cash_by_end)

    def at(tags):
        for t in tags:
            v = instants(cut, t).get(end)
            if v is not None:
                return v
        return None

    whole = at(DEBT_WHOLE)
    if whole is not None:
        debt = whole
    else:
        debt = (at(DEBT_LONG) or 0.0) + (at(DEBT_CURRENT) or 0.0)
    debt += sum(instants(cut, t).get(end, 0.0) for t in DEBT_SHORT)
    together = instants(cut, CASH_AND_INVESTMENTS).get(end)
    cash = together if together is not None else (
        cash_by_end[end] + sum(instants(cut, t).get(end, 0.0) for t in INVESTMENT_TAGS))
    minority = at(MINORITY_TAGS) or 0.0
    return {"end": end, "debt": debt, "cash": cash, "minority": minority,
            "net_debt": debt - cash + minority, "debt_tagged": whole is not None
            or at(DEBT_LONG) is not None or at(DEBT_CURRENT) is not None}


def cover_shares(cut: dict) -> tuple[float, str] | None:
    """M5: dei EntityCommonStockSharesOutstanding of the newest filing."""
    by_accn: dict[tuple[str, str], float] = {}
    for unit, rows in (cut.get("facts", {}).get("dei", {})
                       .get("EntityCommonStockSharesOutstanding", {}).get("units", {}).items()):
        if unit != "shares":
            continue
        for r in rows:
            k = (r["filed"], r.get("accn", ""))
            by_accn[k] = by_accn.get(k, 0.0) + float(r["val"])
    if not by_accn:
        return None
    k = max(by_accn)
    return by_accn[k], k[0]


# --- the method -----------------------------------------------------------
def fallback_growth(h: HI.History) -> tuple[float, str] | None:
    """M6."""
    rev = h.series("revenue")
    ys = sorted(y for y in rev if rev[y] > 0)
    if len(ys) < FALLBACK_MIN_YEARS:
        return None
    n = ys[-1] - ys[0]
    cagr = (rev[ys[-1]] / rev[ys[0]]) ** (1 / n) - 1 if n > 0 else 0.0
    oe = HI.oe_per_share_cagr(h)
    raw = cagr if oe is None else min(cagr, oe)
    g = max(HI.GROWTH_FLOOR, min(HI.GROWTH_CAP, raw))
    return g, (f"FALLBACK (M6): revenue {cagr:.2%}/yr {ys[0]}-{ys[-1]}"
               + ("" if oe is None else f", owner earnings/share {oe:.2%}/yr"))


def evaluate(facts: dict, as_of: date, *, ticker: str, cik: int, sic=None,
             policy: str = "first") -> dict:
    row: dict = {"ticker": ticker, "cik": cik, "as_of": as_of.isoformat(), "sic": sic,
                 "status": "", "fcf0": None, "fcf_mean": None, "fcf_years": [],
                 "zeros": 0, "g_base": None, "g_bear": None, "growth_source": "",
                 "cyclical": None, "level_base": 1.0, "net_debt": None, "bs_end": None,
                 "shares": None, "shares_filed": None, "programme": 0.0,
                 "repeat_buyer": False, "roiic": None, "fv_base": None, "fv_bear": None,
                 "fv_ex_programme": None, "wc_dropped": 0,
                 "quality": {}, "quality_figures": {}, "kills": [], "ebit": None, "gross_profit": None,
                 "assets": None, "roc_capital": None, "fscore": None, "notes": []}
    cut = P.clip(facts, as_of, policy=policy)
    try:
        h = P.history_at(facts, as_of, ticker=ticker, policy=policy)
    except Exception as exc:  # noqa: BLE001
        row["status"] = f"no history: {type(exc).__name__}: {exc}"[:200]
        return row
    ocf, capex = h.series("operating_cash_flow"), h.series("capex")
    years = sorted(y for y in ocf if y in capex)[-3:]
    if len(years) < 3 or years[-1] - years[0] != 2:
        row["status"] = f"no FCF0: OCF and capex in {years} (M1 needs three consecutive years)"
        return row
    flows, zeros, dropped = [], 0, 0
    revenue = h.series("revenue")
    for y in years:
        wc, d = wc_cash_effect(cut, y, sic, revenue.get(y))
        dropped += d
        sbc, _ = first_of(cut, SBC_TAGS, y)
        intr, _ = first_of(cut, INTEREST_TAGS, y)
        zeros += sum(v is None for v in (wc, sbc, intr))
        f = (ocf[y] - (wc or 0.0) - abs(capex[y]) - abs(sbc or 0.0)
             + abs(intr or 0.0) * (1 - tax_for(y)))
        flows.append(f)
        row["fcf_years"].append({"year": y, "ocf": ocf[y], "wc": wc, "capex": capex[y],
                                 "sbc": sbc, "interest": intr, "fcf": f})
    row["zeros"], row["wc_dropped"] = zeros, dropped
    mean = statistics.mean(flows)
    row["fcf_mean"] = mean

    derived = HI.derived_growth(h)
    if derived is not None:
        g_base, g_bear, how = derived.base, derived.bear, "E144"
    else:
        fb = fallback_growth(h)
        if fb is None:
            row["status"] = "no growth: fewer than three revenue years (M6)"
            return row
        g_base, how = fb
        g_bear = max(HI.GROWTH_FLOOR, g_base - 0.02)
    row["g_base"], row["g_bear"], row["growth_source"] = g_base, g_bear, how

    cyc = HI.cycle(h)
    row["cyclical"], row["level_base"] = cyc.cyclical, cyc.level_base
    level_bear = cyc.level_bear if cyc.level_bear is not None else (
        max(0.0, min(flows) / mean) if mean > 0 else 0.0)
    fcf0 = mean * cyc.level_base * (1 + g_base)
    row["fcf0"] = fcf0

    bs = balance_sheet(cut)
    if bs is None:
        row["status"] = "no balance sheet: no cash tagged (M4)"
        return row
    row["net_debt"], row["bs_end"] = bs["net_debt"], bs["end"]
    if not bs["debt_tagged"]:
        row["notes"].append("no long-term debt tag at the balance sheet: debt read as short-term only")
    sh = cover_shares(cut)
    if sh is None or sh[0] <= 0:
        row["status"] = "no shares: no cover-page count (M5)"
        return row
    row["shares"], row["shares_filed"] = sh

    rev = h.series("revenue")
    acq = h.series("acquisitions_paid")
    recent_acq = [abs(acq.get(y, 0.0)) for y in years]
    rev_mean = statistics.mean(rev[y] for y in years if y in rev) if any(y in rev for y in years) else None
    tax = tax_for(as_of)
    full, _ = HI.roiic(h, tax, g_base)
    row["roiic"] = None if full is None else full.value
    acq_mean = statistics.mean(recent_acq)
    repeat = (sum(a > 0 for a in recent_acq) >= 2 and rev_mean is not None
              and acq_mean > REPEAT_BUYER_SHARE * rev_mean)
    row["repeat_buyer"] = repeat
    if repeat:
        row["programme"] = VA.deal_programme_value(
            acquisitions_mean=acq_mean, roiic=row["roiic"], growth=g_base)

    net_cash = -bs["net_debt"] + row["programme"]
    if mean <= 0:
        row["status"] = "FCF0 not positive"
    else:
        try:
            row["fv_base"] = VA.equity_value_per_share(
                fcf0=fcf0, growth=g_base, net_cash=net_cash, shares=sh[0])
            row["fv_bear"] = VA.equity_value_per_share(
                fcf0=mean * level_bear * (1 + g_bear), growth=g_bear,
                net_cash=net_cash, shares=sh[0]) if level_bear > 0 else net_cash / sh[0]
            # E142's deal-programme charge left out: the test of that rule
            row["fv_ex_programme"] = VA.equity_value_per_share(
                fcf0=fcf0, growth=g_base, net_cash=-bs["net_debt"], shares=sh[0])
        except VA.ValuationError as exc:
            row["status"] = f"no value: {exc}"[:200]
            return row
        row["status"] = "ok"

    tests = HI.quality(h, tax=tax, fcf0=fcf0, net_debt=bs["net_debt"],
                       roiic_base=row["roiic"], repeat_buyer=repeat, rate=RATE)
    row["quality"] = {t.name.split()[0]: t.passed for t in tests if not t.name.startswith("Q5")}
    row["quality_figures"] = {t.name.split()[0]: t.figure for t in tests if not t.name.startswith("Q5")}
    try:
        row["kills"] = V.kills(cut, None, as_of)
    except Exception as exc:  # noqa: BLE001
        row["notes"].append(f"kills not evaluated: {type(exc).__name__}")
    _comparators(row, cut, h)
    return row


def _comparators(row: dict, cut: dict, h: HI.History) -> None:
    profit, _ = HI._profit_series(h)
    if not profit:
        return
    y = max(profit)
    row["ebit"] = profit[y]
    gp, _ = first_of(cut, ("GrossProfit",), y)
    if gp is None:
        rev, _ = first_of(cut, HI.XBRL_TAGS["revenue"], y)
        cogs, _ = first_of(cut, ("CostOfRevenue", "CostOfGoodsAndServicesSold",
                                 "CostOfGoodsSold"), y)
        gp = None if rev is None or cogs is None else rev - cogs
    row["gross_profit"] = gp
    inst = {t: annual_instant(cut, t) for t in
            ("Assets", "AssetsCurrent", "LiabilitiesCurrent", "PropertyPlantAndEquipmentNet",
             "LongTermDebtNoncurrent", "LongTermDebt")}
    row["assets"] = inst["Assets"].get(y)
    ca, cl, ppe = (inst[t].get(y) for t in ("AssetsCurrent", "LiabilitiesCurrent",
                                            "PropertyPlantAndEquipmentNet"))
    cash = next((annual_instant(cut, t).get(y) for t in CASH_TAGS
                 if annual_instant(cut, t).get(y) is not None), 0.0)
    if None not in (ca, cl, ppe):
        row["roc_capital"] = max(0.0, ca - cash - cl) + ppe
    row["fscore"] = fscore(cut, h, y, inst)


def fscore(cut: dict, h: HI.History, y: int, inst: dict) -> int | None:
    """Piotroski's nine signals on fiscal year y against y-1; None where a
    signal cannot be read (no partial scores)."""
    a = inst["Assets"]
    ni = annual(cut, "NetIncomeLoss")
    ocf = h.series("operating_cash_flow")
    rev = h.series("revenue")
    sh = h.series("shares")
    gp = {}
    for z in (y, y - 1):
        g, _ = first_of(cut, ("GrossProfit",), z)
        if g is None:
            cogs, _ = first_of(cut, ("CostOfRevenue", "CostOfGoodsAndServicesSold",
                                     "CostOfGoodsSold"), z)
            g = None if cogs is None or z not in rev else rev[z] - cogs
        gp[z] = g
    ltd = inst["LongTermDebtNoncurrent"] or inst["LongTermDebt"]
    ca, cl = inst["AssetsCurrent"], inst["LiabilitiesCurrent"]
    need = [a.get(y), a.get(y - 1), a.get(y - 2), ni.get(y), ni.get(y - 1), ocf.get(y),
            rev.get(y), rev.get(y - 1), sh.get(y), sh.get(y - 1), gp[y], gp[y - 1],
            ca.get(y), ca.get(y - 1), cl.get(y), cl.get(y - 1)]
    if any(v is None for v in need) or not cl.get(y) or not cl.get(y - 1) or not rev[y] or not rev[y - 1]:
        return None
    roa, roa0 = ni[y] / a[y - 1], ni[y - 1] / a[y - 2]
    lev = ltd.get(y, 0.0) / ((a[y] + a[y - 1]) / 2)
    lev0 = ltd.get(y - 1, 0.0) / ((a[y - 1] + a[y - 2]) / 2)
    return sum((
        roa > 0, ocf[y] > 0, roa > roa0, ocf[y] / a[y - 1] > roa,
        gp[y] / rev[y] > gp[y - 1] / rev[y - 1],
        rev[y] / a[y - 1] > rev[y - 1] / a[y - 2],
        lev < lev0 or (lev == 0 and lev0 == 0),
        ca[y] / cl[y] > ca[y - 1] / cl[y - 1],
        sh[y] <= sh[y - 1],
    ))


def with_price(row: dict, price: float, public_float: float | None) -> dict:
    """The price-dependent columns. `cap_check` compares the market cap
    (cover shares x unadjusted close) with the filer's own public float: a
    float far above the cap is a mis-tagged float or a ticker that now
    belongs to another security (pilot: AMEDICA, SPB for HRG, MTCH for IAC)."""
    row["price"] = price
    if row["shares"]:
        cap = row["shares"] * price
        row["market_cap"] = cap
        if public_float:
            ratio = public_float / cap
            row["float_over_cap"] = ratio
            row["cap_check"] = 0.15 <= ratio <= 1.6
        if row["fv_base"] is not None and price > 0:
            row["fv_over_price"] = row["fv_base"] / price
        ev = cap + (row["net_debt"] or 0.0)
        row["ev"] = ev
        if row["ebit"] is not None and ev > 0:
            row["ebit_ev"] = row["ebit"] / ev
        if row["fcf_mean"] is not None and cap > 0:
            row["fcf_yield"] = row["fcf_mean"] / cap
        if row["roc_capital"] and row["ebit"] is not None:
            row["roc"] = row["ebit"] / row["roc_capital"]
    if row["gross_profit"] is not None and row["assets"]:
        row["gp_assets"] = row["gross_profit"] / row["assets"]
    return row
