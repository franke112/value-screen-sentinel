"""Backtest step 1: the point-in-time cut of companyfacts (tools/backtest/pit.py).

Made-up facts only. The design's two required cases: a restatement filed
after the test date is not seen, and a figure filed the day after is not
seen. The rest pins the cut's other rules.
"""
from datetime import date

import pytest

from tools.backtest import pit as P

AS_OF = date(2018, 4, 30)
OCF = "NetCashProvidedByUsedInOperatingActivities"
SHARES = "WeightedAverageNumberOfDilutedSharesOutstanding"


def fy(year, val, filed, *, form="10-K", accn=None, frame=None):
    e = {"start": f"{year}-01-01", "end": f"{year}-12-31", "val": val,
         "fy": int(filed[:4]), "fp": "FY", "form": form, "filed": filed,
         "accn": accn or f"0000000000-{filed[2:4]}-{filed[5:7]}{filed[8:10]}"}
    if frame:
        e["frame"] = frame
    return e


def facts(tags, unit="USD"):
    return {"cik": 1, "entityName": "Made Up Inc",
            "facts": {"us-gaap": {t: {"label": t, "units": {unit: rows}}
                                  for t, rows in tags.items()}}}


def vals(cut, tag, unit="USD"):
    rows = cut["facts"].get("us-gaap", {}).get(tag, {}).get("units", {}).get(unit, [])
    return sorted((r["end"], r["val"], r["filed"]) for r in rows)


# --- the design's two cases -----------------------------------------------

@pytest.mark.parametrize("policy", P.POLICIES)
def test_a_restatement_after_the_test_date_is_not_seen(policy):
    f = facts({OCF: [fy(2016, 100, "2017-02-20"),
                     fy(2016, 90, "2019-02-20")]})          # restated a year later
    assert vals(P.clip(f, AS_OF, policy=policy), OCF) == [("2016-12-31", 100, "2017-02-20")]


@pytest.mark.parametrize("policy", P.POLICIES)
def test_a_figure_filed_the_day_after_is_not_seen(policy):
    f = facts({OCF: [fy(2016, 100, "2017-02-20"),
                     fy(2017, 120, "2018-05-01")]})
    assert [r[0] for r in vals(P.clip(f, AS_OF, policy=policy), OCF)] == ["2016-12-31"]


# --- the edges ------------------------------------------------------------

@pytest.mark.parametrize("policy", P.POLICIES)
def test_the_test_day_itself_is_out_and_the_day_before_is_in(policy):
    f = facts({OCF: [fy(2016, 100, "2018-04-29"), fy(2017, 120, "2018-04-30")]})
    assert [r[0] for r in vals(P.clip(f, AS_OF, policy=policy), OCF)] == ["2016-12-31"]


def test_first_policy_keeps_the_first_filing_even_when_restated_before_the_date():
    f = facts({OCF: [fy(2016, 100, "2017-02-20"), fy(2016, 90, "2018-02-20")]})
    assert vals(P.clip(f, AS_OF, policy="first"), OCF) == [("2016-12-31", 100, "2017-02-20")]
    assert len(vals(P.clip(f, AS_OF, policy="latest"), OCF)) == 2
    assert P.differences(f, AS_OF) == 1


def test_first_filed_is_chosen_among_statements_where_any_exist():
    # LOPE's proxy shape: a DEF 14A tags the year unscaled. Here the proxy is
    # the EARLIER filing and still loses, as the engine's `_pick` would rule.
    f = facts({OCF: [fy(2016, 100_000, "2017-01-15", form="DEF 14A"),
                     fy(2016, 100_000_000, "2017-02-20")]})
    assert vals(P.clip(f, AS_OF), OCF) == [("2016-12-31", 100_000_000, "2017-02-20")]


def test_share_counts_keep_every_visible_filing_so_a_split_can_show():
    rows = [fy(2015, 30e6, "2016-02-20"), fy(2016, 31e6, "2017-02-20"),
            fy(2016, 186e6, "2018-02-20"),               # 6-for-1, re-filed
            fy(2016, 999e6, "2019-02-20")]               # after the date: out
    cut = P.clip(facts({SHARES: rows}, unit="shares"), AS_OF)
    assert [r[1] for r in vals(cut, SHARES, "shares")] == [30e6, 31e6, 186e6]


def test_frame_is_stripped_and_the_input_is_not_touched():
    f = facts({OCF: [fy(2016, 100, "2017-02-20", frame="CY2016")]})
    cut = P.clip(f, AS_OF)
    assert "frame" not in cut["facts"]["us-gaap"][OCF]["units"]["USD"][0]
    assert f["facts"]["us-gaap"][OCF]["units"]["USD"][0]["frame"] == "CY2016"


def test_a_tag_with_nothing_visible_is_gone():
    f = facts({OCF: [fy(2016, 100, "2017-02-20")], "Goodwill": [fy(2017, 5, "2018-06-01")]})
    assert "Goodwill" not in P.clip(f, AS_OF)["facts"]["us-gaap"]


def test_an_unknown_policy_refuses():
    with pytest.raises(ValueError):
        P.clip(facts({}), AS_OF, policy="newest")


# --- through the engine's own history builder ------------------------------

def test_history_at_sees_only_the_cut():
    f = facts({OCF: [fy(2014, 80, "2015-02-20"), fy(2015, 90, "2016-02-20"),
                     fy(2016, 100, "2017-02-20"), fy(2016, 50, "2019-02-20"),
                     fy(2017, 120, "2018-05-01")]})
    h = P.history_at(f, AS_OF, ticker="MADE")
    assert h.series("operating_cash_flow") == {2014: 80, 2015: 90, 2016: 100}


def test_history_at_applies_a_split_filed_before_the_date_only():
    ocf = [fy(y, 100, f"{y + 1}-02-20") for y in (2014, 2015, 2016)]
    shares = [fy(2014, 30e6, "2015-02-20"), fy(2015, 30e6, "2016-02-20"),
              fy(2015, 60e6, "2017-02-20"), fy(2016, 60e6, "2017-02-20")]
    f = facts({OCF: ocf})
    f["facts"]["us-gaap"][SHARES] = {"units": {"shares": shares}}
    h = P.history_at(f, AS_OF, ticker="MADE")
    assert h.series("shares") == {2014: 60e6, 2015: 60e6, 2016: 60e6}
    # the same split filed after the test date leaves the old counts alone
    late = [dict(s, filed="2019-02-20") if s["val"] == 60e6 else s for s in shares]
    f["facts"]["us-gaap"][SHARES]["units"]["shares"] = late
    h = P.history_at(f, AS_OF, ticker="MADE")
    assert h.series("shares") == {2014: 30e6, 2015: 30e6}


# --- step 2's stand-ins for hand work ---------------------------------------

class _Fig:
    def __init__(self, tag=""):
        self.tag = tag


class _Year:
    def __init__(self, *names, gross_tag="InterestExpense"):
        self.figures = {n: _Fig(gross_tag if n == "finance_costs_period" else "")
                        for n in names}


@pytest.mark.parametrize("names,tag,shape", [
    (("finance_costs_paid", "finance_income_received"), "", ""),
    (("net_finance_costs", "finance_costs_paid"), "", "income_statement_net"),
    (("finance_costs_period", "finance_income_period"), "", "income_statement_net"),
    (("finance_costs_period", "finance_costs_paid"), "InterestExpenseNonoperating",
     "interest_expense_only"),
    (("finance_costs_period", "finance_costs_paid"), "InterestExpense", "cash_paid_only"),
    (("finance_costs_paid",), "", "cash_paid_only"),
    ((), "", ""),
])
def test_the_interest_shape_follows_the_rulings_order(names, tag, shape):
    assert P.interest_shape(_Year(*names, gross_tag=tag)) == shape


def test_ratios_by_label_and_none_where_a_filer_redated_a_year():
    from tools.backtest import value as BV
    from vss import rules as RU
    qs = [RU.Quarter(period="2017-Q1", revenue=100.0, op_income=10.0),
          RU.Quarter(period="2017-Q2", revenue=120.0, op_income=12.0),
          RU.Quarter(period="2018-Q1", revenue=110.0, op_income=11.0),
          RU.Quarter(period="2018-Q2", revenue=120.0, op_income=6.0)]
    out = BV.with_ratios(qs)
    assert out[0].revenue_yoy is None and out[0].op_margin == pytest.approx(0.10)
    assert out[2].revenue_yoy == pytest.approx(0.10)
    assert out[3].revenue_yoy is None          # equal to the unit: re-dated
    assert out[3].op_margin == pytest.approx(0.05)
