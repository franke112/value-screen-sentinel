"""E142-E145: the history file, its read-back, and what is derived from it."""

from __future__ import annotations

import pytest

from vss import history as H
from vss import valuation as V


def _hist(rows, **extra):
    raw = {"ticker": "T.TEST", "currency": "SEK", "money_unit": "millions",
           "sources": {"a": {"file": "x.htm"}, "b": {"file": "y.htm"}},
           "rows": rows}
    raw.update(extra)
    return H.parse(raw, path="test")


def _row(field, source, years, values, quote="q", **kw):
    return {"field": field, "source": source, "years": years,
            "values": values, "quote": quote, **kw}


# --- the file -------------------------------------------------------------

def test_the_newer_report_wins_a_restated_year():
    h = _hist([_row("revenue", "a", [2020, 2019], [100, 90]),
               _row("revenue", "b", [2021, 2020], [120, 101])])
    assert h.series("revenue") == {2019: 90e6, 2020: 101e6, 2021: 120e6}


def test_capex_printed_as_two_lines_of_one_statement_is_summed():
    h = _hist([_row("capex", "a", [2020], [-10]),
               _row("capex", "a", [2020], [-5])])
    assert h.series("capex") == {2020: -15e6}


def test_a_row_marked_add_sums_into_the_same_source_figure():
    h = _hist([_row("operating_profit", "a", [2025], [1761]),
               _row("operating_profit", "a", [2025], [27], add=True),
               _row("operating_profit", "a", [2025], [1], add=True)])
    assert h.series("operating_profit") == {2025: 1789e6}
    h = _hist([_row("operating_profit", "a", [2025], [1761]),
               _row("operating_profit", "a", [2025], [27])])
    assert h.series("operating_profit") == {2025: 27e6}     # unmarked replaces


def test_a_tag_rewrite_keeps_the_hand_read_rows(tmp_path, monkeypatch):
    import yaml
    (tmp_path / "T.TEST.yaml").write_text(yaml.safe_dump(
        {"ticker": "T.TEST", "money_unit": "whole",
         "sources": {"xbrl": {"kind": "sec-xbrl"}, "a": {"file": "x.htm"}},
         "rows": [_row("revenue", "xbrl", [2020], [1], quote=""),
                  _row("organic_growth_pct", "a", [2020], [3])]}))
    monkeypatch.setattr(H, "from_companyfacts", lambda *a, **k: {
        "ticker": "T.TEST", "currency": "USD", "money_unit": "whole",
        "sources": {"xbrl": {"kind": "sec-xbrl"}},
        "rows": [_row("revenue", "xbrl", [2020], [2], quote="")]})
    monkeypatch.setattr("vss.xbrl.fetch_company_facts", lambda cik: {})
    rc, _ = H.run_history(ticker="T.TEST", xbrl=True, write=True, directory=tmp_path, cik=1)
    kept = yaml.safe_load((tmp_path / "T.TEST.yaml").read_text())
    assert rc == 0 and [r["source"] for r in kept["rows"]] == ["xbrl", "a"]
    assert "a" in kept["sources"]


def test_organic_growth_is_a_fraction_and_shares_take_their_own_unit():
    h = _hist([_row("organic_growth_pct", "a", [2020], [-4]),
               _row("shares", "a", [2020], [77036], unit="thousands")])
    assert h.series("organic_growth") == {2020: pytest.approx(-0.04)}
    assert h.series("shares") == {2020: 77_036_000}


def test_a_hand_read_row_without_its_quote_refuses():
    with pytest.raises(H.HistoryError, match="quote"):
        _hist([_row("revenue", "a", [2020], [1], quote="")])


def test_the_read_back_passes_a_true_row_and_fails_a_wrong_one(tmp_path, monkeypatch):
    doc = tmp_path / "r.htm"
    doc.write_text("<p>Net sales 12,854 13,323</p><p>Acquisitions &ndash; (5)</p>")
    monkeypatch.setattr(H, "PDF_TEXT_CACHE", tmp_path / "cache")
    raw = {"ticker": "T.TEST", "money_unit": "millions",
           "sources": {"a": {"file": str(doc)}},
           "rows": [_row("revenue", "a", [2025, 2024], [12854, 13323],
                         quote="Net sales 12,854 13,323")]}
    assert H.check(H.parse(raw)) == []
    raw["rows"][0]["values"] = [12854, 13324]
    fails = H.check(H.parse(raw))
    assert len(fails) == 1 and "13324" in fails[0]


def test_a_dash_reads_as_a_nil():
    assert H._find_values("Acquisitions - (5)", (0.0, -5.0)) is None


# --- E144 -----------------------------------------------------------------

def test_the_proxy_takes_only_deal_free_years():
    h = _hist([_row("revenue", "a", [2018, 2019, 2020, 2021], [100, 110, 121, 140]),
               _row("acquisitions_paid", "a", [2018, 2019, 2020, 2021], [0, 0, 5, 0])])
    years = {o.year: o.growth for o in H.organic_years(h)}
    assert years == {2019: pytest.approx(0.10)}      # 2020 and 2021 carry a deal


def test_the_derived_base_is_the_lowest_of_ten_years_five_years_and_capped():
    rates = [10, 10, 10, 10, 10, 2, 2, 2, 2, 2]
    h = _hist([_row("organic_growth_pct", "a", list(range(2016, 2026)), rates)])
    g = H.derived_growth(h)
    assert g.base == pytest.approx(0.02)             # the last five
    assert g.bull == pytest.approx(0.04)             # capped: only 5 years > 4%
    assert g.bear <= g.base


def test_the_high_cap_needs_seven_years_above_four_percent():
    h = _hist([_row("organic_growth_pct", "a", list(range(2016, 2026)), [9] * 10)])
    assert H.derived_growth(h).base == pytest.approx(H.GROWTH_CAP_HIGH)


def test_fewer_than_five_organic_years_leaves_the_view():
    h = _hist([_row("organic_growth_pct", "a", [2021, 2022, 2023, 2024], [3, 3, 3, 3])])
    assert H.derived_growth(h) is None


# --- E142 -----------------------------------------------------------------

def test_roiic_takes_the_organic_part_out_and_divides_by_the_capital_added():
    years = list(range(2016, 2026))
    h = _hist([_row("operating_profit", "a", years, [100] * 3 + [150] * 4 + [200] * 3),
               _row("invested_capital", "a", years, [1000] * 3 + [1500] * 4 + [2000] * 3),
               _row("organic_growth_pct", "a", years, [0] * 10)])
    full, _ = H.roiic(h, 0.2, 0.0)
    assert full.value == pytest.approx(100 * 0.8 / 1000)


def test_the_programme_is_never_positive_and_a_negative_roiic_counts_as_zero():
    up = V.deal_programme_value(acquisitions_mean=100, roiic=0.30, growth=0.02)
    down = V.deal_programme_value(acquisitions_mean=100, roiic=-0.5, growth=0.02)
    zero = V.deal_programme_value(acquisitions_mean=100, roiic=0.0, growth=0.02)
    assert up == 0.0 and down == zero < 0
    assert zero == pytest.approx(-100 * V.growth_annuity(0.02))


def test_no_record_is_no_credit():
    assert V.roiic_fraction(None) == 0.0
    assert V.roiic_fraction(V.HURDLE_RATE * 2) == 1.0


# --- E143 -----------------------------------------------------------------

def test_a_margin_that_only_rose_is_not_a_cycle():
    years = list(range(2016, 2026))
    h = _hist([_row("revenue", "a", years, [100 + 5 * i for i in range(10)]),
               _row("operating_profit", "a", years, [2 + 2 * i for i in range(10)])])
    assert not H.cycle(h).cyclical


def test_a_margin_that_fell_below_half_its_peak_is_a_cycle():
    years = list(range(2016, 2026))
    h = _hist([_row("revenue", "a", years, [100] * 10),
               _row("operating_profit", "a", years, [20, 20, 20, 5, 20, 20, 20, 20, 20, 20])])
    assert H.cycle(h).cyclical


def test_a_pass_through_revenue_runs_neither_the_proxy_nor_the_margin_test():
    years = list(range(2016, 2026))
    h = _hist([_row("revenue", "a", years, [100, 80, 120, 70, 130, 90, 140, 100, 150, 110]),
               _row("acquisitions_paid", "a", years, [0] * 10),
               _row("operating_profit", "a", years, [10] * 10)],
              revenue_pass_through="fuel at the pump price")
    assert H.organic_years(h) == []
    assert not H.cycle(h).cyclical


# --- E145 -----------------------------------------------------------------

def test_the_quality_tests_read_their_figures():
    years = list(range(2016, 2026))
    h = _hist([_row("operating_profit", "a", years, [100] * 10),
               _row("invested_capital", "a", years, [400] * 10),
               _row("operating_cash_flow", "a", years, [90] * 10),
               _row("capex", "a", years, [-20] * 10)],
              business={"text": "sells x to y"})
    tests = {t.name[:2]: t for t in H.quality(
        h, tax=0.2, fcf0=70e6, net_debt=400e6, roiic_base=0.05,
        repeat_buyer=True, rate=0.095)}
    assert tests["Q1"].passed                      # 80 / 400 = 20%
    assert tests["Q2"].passed
    assert tests["Q3"].passed is False
    assert tests["Q4"].passed is False
    assert tests["Q5"].passed


def test_q1_takes_goodwill_out_and_reads_only_the_years_it_covers():
    years = list(range(2016, 2026))
    h = _hist([_row("operating_profit", "a", years, [100] * 10),
               _row("invested_capital", "a", years, [1000] * 10),
               _row("goodwill", "a", [2024, 2025], [800, 800])])
    q1 = H.quality(h, tax=0.2, fcf0=1, net_debt=0, roiic_base=None,
                   repeat_buyer=False, rate=0.095)[0]
    assert q1.passed and "over 2 years (goodwill taken out)" in q1.figure  # 80 / 200


# --- the pilot's facit (method review section 6) ---------------------------

@pytest.mark.parametrize("ticker", ["LIAB.ST", "RBREW.CO"])
def test_the_two_names_struck_below_zero_are_positive_under_E142(ticker):
    from datetime import date, datetime, timezone

    from vss import strike as S
    struck = S.strike_one(ticker, as_of=date(2026, 10, 27),
                          run_ts=datetime(2026, 10, 27, 15, tzinfo=timezone.utc),
                          stamp="test")
    assert struck.fv > 0
    assert struck.record.e140.e142 is not None


def test_a_share_split_scales_the_years_filed_before_it():
    def fy(end, filed, val):
        return {"end": end, "start": end[:4] + "-01-01", "filed": filed,
                "val": val, "form": "10-K", "fp": "FY"}
    tag = {"units": {"shares": [
        fy("2022-12-31", "2023-02-01", 30.0),
        fy("2023-12-31", "2024-02-01", 29.0),
        fy("2023-12-31", "2025-02-01", 174.0),   # restated after 6-for-1
        fy("2024-12-31", "2025-02-01", 170.0)]}}
    got = H._annual_facts({"S": tag}, "S", duration=True)
    assert got == {"2022-12-31": 180.0, "2023-12-31": 174.0, "2024-12-31": 170.0}
    raw = H._annual_facts({"S": tag}, "S", duration=True, splits=False)
    assert raw["2022-12-31"] == 30.0


def test_two_splits_of_the_same_ratio_both_apply():
    # NKE: 2-for-1 in Dec 2012 and again in Dec 2015; the first was once
    # merged into the second and only one ratio reached the oldest years
    def fy(end, filed, val):
        return {"end": end, "start": f"{int(end[:4]) - 1}-06-01", "filed": filed,
                "val": val, "form": "10-K", "fp": "FY"}
    tag = {"units": {"shares": [
        fy("2011-05-31", "2011-07-20", 100.0),
        fy("2012-05-31", "2012-07-20", 98.0),
        fy("2012-05-31", "2013-07-20", 196.0),   # restated after the 2012 split
        fy("2013-05-31", "2013-07-20", 194.0),
        fy("2014-05-31", "2014-07-20", 190.0),
        fy("2014-05-31", "2016-07-20", 380.0),   # restated after the 2015 split
        fy("2016-05-31", "2016-07-20", 370.0)]}}
    got = H._annual_facts({"S": tag}, "S", duration=True)
    assert got["2011-05-31"] == 400.0
    assert got["2012-05-31"] == 392.0
    assert got["2013-05-31"] == 388.0
    assert got["2014-05-31"] == 380.0
    assert got["2016-05-31"] == 370.0


def _q2(oe):
    years = list(range(2016, 2016 + len(oe)))
    h = _hist([_row("operating_profit", "a", years, [100] * len(oe)),
               _row("operating_cash_flow", "a", years, oe),
               _row("capex", "a", years, [0] * len(oe))])
    return {t.name[:2]: t for t in H.quality(
        h, tax=0.2, fcf0=70e6, net_debt=0, roiic_base=None,
        repeat_buyer=False, rate=0.095)}["Q2"]


def test_e148_one_repaired_negative_year_is_forgiven():
    assert _q2([50, 60, -10, 40, 65, 70]).passed            # regained 60 by year 3
    assert not _q2([50, 60, -10, 40, 50, 55]).passed        # never regained
    assert not _q2([-5, 60, 70, 80, 90, 95]).passed         # a first year: nothing to regain
    assert not _q2([50, -1, 60, -2, 70, 80]).passed         # two: not a shut-down year


def _q2_pre(oe, before):
    import dataclasses
    years = list(range(2016, 2016 + len(oe)))
    h = _hist([_row("operating_profit", "a", years, [100] * len(oe)),
               _row("operating_cash_flow", "a", years, oe),
               _row("capex", "a", years, [0] * len(oe))])
    h = dataclasses.replace(h, owner_earnings_before_window=before)
    return {t.name[:2]: t for t in H.quality(
        h, tax=0.2, fcf0=70e6, net_debt=0, roiic_base=None,
        repeat_buyer=False, rate=0.095)}["Q2"]


def test_e148_1_the_earlier_best_may_lie_before_the_window():
    # PHM: the window opens on 2015, the one negative year; 2013 is the best before it
    assert _q2_pre([-5, 60, 70, 80, 90, 95], {2013: 50e6, 2014: 40e6}).passed
    assert not _q2_pre([-5, 30, 40, 45, 48, 49], {2013: 50e6, 2014: 40e6}).passed  # never regained
    # LOPE and CROX: the year before the window was negative too -- two years, a pattern
    q = _q2_pre([-5, 60, 70, 80, 90, 95], {2013: 50e6, 2014: -1e6})
    assert not q.passed and "before the window" in q.figure
    # no earlier record at all: E148's first-year rule stands
    assert not _q2_pre([-5, 60, 70, 80, 90, 95], {}).passed


def test_from_companyfacts_carries_three_years_before_the_window():
    def fy(end, val):
        return {"start": f"{int(end[:4])}-01-01", "end": end, "val": val, "fy": int(end[:4]),
                "fp": "FY", "form": "10-K", "filed": f"{int(end[:4]) + 1}-02-20"}
    years = range(2010, 2026)
    gaap = {"NetCashProvidedByUsedInOperatingActivities":
                {"units": {"USD": [fy(f"{y}-12-31", 100.0 + y) for y in years]}},
            "PaymentsToAcquirePropertyPlantAndEquipment":
                {"units": {"USD": [fy(f"{y}-12-31", 10.0) for y in years]}}}
    raw = H.from_companyfacts("XX", {"facts": {"us-gaap": gaap}})
    assert sorted(raw["owner_earnings_before_window"]) == [2012, 2013, 2014]
    assert raw["owner_earnings_before_window"][2014] == 100.0 + 2014 - 10.0
    h = H.parse(raw)
    assert min(h.years) == 2015 and 2014 not in h.years   # the window itself is unchanged


def test_organic_growth_printed_as_its_parts_is_checked_on_the_parts():
    with pytest.raises(H.HistoryError):
        _hist([_row("organic_growth_pct", "a", [2021], [6.8], quote="10.0% ... 320 basis points",
                    organic_from={"constant_currency_pct": 10.0, "acquisitions_bps": 300})])
    h = _hist([_row("organic_growth_pct", "a", [2022], [7.1], quote="7.5% ... 100 basis points ... 60 basis points",
                    organic_from={"constant_currency_pct": 7.5, "acquisitions_bps": 100, "disposals_bps": 60})])
    assert h.rows[0].stated == (7.5, 100.0, 60.0)
    assert H._find_values(h.rows[0].quote, h.rows[0].stated) is None
