"""Backtest path 1: the method's own rules (tools/backtest/method.py)."""
from tools.backtest import method as M


def _fy(end, val, filed=None):
    return {"end": end, "start": f"{int(end[:4]) - 1}{end[4:]}", "val": val,
            "form": "10-K", "fp": "FY", "filed": filed or f"{int(end[:4]) + 1}-02-15"}


def _inst(end, val, form="10-Q", filed=None):
    return {"end": end, "val": val, "form": form, "fp": "Q1",
            "filed": filed or end[:8] + "28"}


def _cut(tags, dei=None):
    facts = {"us-gaap": {t: {"units": {"USD": rows}} for t, rows in tags.items()}}
    if dei:
        facts["dei"] = dei
    return {"facts": facts}


def test_combined_payables_tag_only_where_neither_part_is_tagged():
    both = _cut({"IncreaseDecreaseInAccountsPayable": [_fy("2017-12-31", 10.0)],
                 "IncreaseDecreaseInAccountsPayableAndAccruedLiabilities": [_fy("2017-12-31", 25.0)],
                 "IncreaseDecreaseInAccountsReceivable": [_fy("2017-12-31", 4.0)]})
    assert M.wc_cash_effect(both, 2017, None) == (6.0, 0)
    alone = _cut({"IncreaseDecreaseInAccountsPayableAndAccruedLiabilities": [_fy("2017-12-31", 25.0)]})
    assert M.wc_cash_effect(alone, 2017, None) == (25.0, 0)


def test_a_gross_presented_tag_is_dropped_not_counted():
    # MSFT: unearned revenue deferred, gross, larger than a quarter of revenue
    cut = _cut({"IncreaseDecreaseInDeferredRevenue": [_fy("2017-06-30", 52_876.0)],
                "IncreaseDecreaseInAccountsReceivable": [_fy("2017-06-30", 925.0)]})
    assert M.wc_cash_effect(cut, 2017, None, revenue=89_950.0) == (-925.0, 1)
    assert M.wc_cash_effect(cut, 2017, None) == (51_951.0, 0)


def test_a_homebuilder_keeps_inventory_in_the_flow():
    cut = _cut({"IncreaseDecreaseInInventories": [_fy("2017-12-31", 300.0)],
                "IncreaseDecreaseInAccountsPayable": [_fy("2017-12-31", 20.0)]})
    assert M.wc_cash_effect(cut, 2017, 1531) == (20.0, 0)
    assert M.wc_cash_effect(cut, 2017, 2000) == (-280.0, 0)


def test_nothing_tagged_is_none_not_zero():
    assert M.wc_cash_effect(_cut({}), 2017, None) == (None, 0)


def test_net_debt_at_the_newest_balance_sheet_with_the_combined_cash_tag():
    cut = _cut({"CashAndCashEquivalentsAtCarryingValue": [_inst("2017-12-31", 5.0, "10-K"),
                                                         _inst("2018-03-31", 7.0)],
                "CashCashEquivalentsAndShortTermInvestments": [_inst("2018-03-31", 130.0)],
                "LongTermDebt": [_inst("2018-03-31", 80.0)],
                "CommercialPaper": [_inst("2018-03-31", 4.0)],
                "MinorityInterest": [_inst("2018-03-31", 1.0)]})
    bs = M.balance_sheet(cut)
    assert bs["end"] == "2018-03-31"
    assert bs["net_debt"] == 80.0 + 4.0 - 130.0 + 1.0


def test_cover_shares_sum_the_classes_of_the_newest_filing():
    dei = {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
        {"end": "2018-04-20", "val": 80.0, "filed": "2018-04-25", "accn": "b"},
        {"end": "2018-04-20", "val": 10.0, "filed": "2018-04-25", "accn": "b"},
        {"end": "2018-01-20", "val": 95.0, "filed": "2018-02-01", "accn": "a"}]}}}
    assert M.cover_shares(_cut({}, dei)) == (90.0, "2018-04-25")


def test_tax_rate_follows_the_2018_reform():
    assert M.tax_for(2017) == M.TAX_BEFORE_2018
    assert M.tax_for(2018) == M.TAX_FROM_2018
