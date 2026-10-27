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
