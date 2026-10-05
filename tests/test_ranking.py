"""The ranking key: components, sections, ties, and the forbidden shortcuts."""

from __future__ import annotations

import ast
from datetime import date
from pathlib import Path

import pytest

from vss.fx import FxTable, build_table
from vss.fundamentals import FieldValue, TickerFundamentals
from vss.fundamentals import SeriesPoint as AnnualPoint


def SeriesPoint(ticker, line, period_end, value, statement="income",
                period_months=...):
    """A stored point from THE VENDOR PATH, which is annual by construction.

    Every fixture in this file stands in for what `default_reader` returns,
    and it asks for `income_stmt` and `balance_sheet` -- the ANNUAL
    statements. So a flow line here is twelve months, the same declaration
    `snapshot.read_fundamentals` and the acceptance fixture make about the
    same rows. FRAMEWORK-EDITS E13 refuses to rank a flow line whose length
    is unrecorded, and leaving it off here would make every fixture in the
    file unrankable for a reason that has nothing to do with what it tests.

    Pass `period_months` explicitly to build a quarterly or unlabelled
    point; E13's own tests do.
    """
    if period_months is ...:
        period_months = 12 if statement == "income" else None
    return AnnualPoint(ticker, line, period_end, value, statement, period_months)
from vss.prices import STATUS_OK, STATUS_STALE
from vss.ranking import (
    EBIT_ALIASES,
    EV_IMPOSSIBLE_NOTE,
    QUALITY_BASIS_UNKNOWN,
    QUALITY_MISSING,
    QUALITY_MIXED_PERIODS,
    QUALITY_STALE,
    QUALITY_NOT_MEANINGFUL,
    QUALITY_OK,
    QUALITY_SECTOR,
    competition_ranks,
    currency_pairs,
    rank,
    score,
)
from vss.ranking import extract_inputs as _extract_inputs
from vss.ranking import rank_candidates as _rank_candidates

ROOT = Path(__file__).resolve().parents[1]
YEAR = date(2025, 12, 31)
#: The run date every score() below is asked about. 233 days after YEAR,
#: so a record built from the default period is not stale (L4).
ASOF = date(2026, 8, 21)

#: THE SETTLED CLOSE every fixture below is priced at (rule 8). The vendor's
#: fetch-day quote in `record()` is the same figure, so the implied share
#: count re-priced at the close gives the vendor's market cap back and the
#: enterprise value a test asks for is the one it gets. The tests that are
#: ABOUT the two prices differing set them apart explicitly.
CLOSE = (ASOF, 10.0)


def extract_inputs(ticker, rec, *, close=CLOSE, fetched=ASOF):
    """`ranking.extract_inputs` with the settled close supplied, as the
    chain supplies it from the filter-1 row."""
    return _extract_inputs(ticker, rec, close=close, fetched=fetched)


def rank_candidates(candidates, fundamentals, fx, as_of, *, closes=None,
                    fetched=ASOF, **kw):
    if closes is None:
        closes = {c.ticker: CLOSE for c in candidates}
    return _rank_candidates(candidates, fundamentals, fx, as_of,
                            closes=closes, fetched=fetched, **kw)


def record(ticker="X", *, sector="Technology", ebit=100.0, ebit_line="EBIT",
           gross_profit=350.0, total_assets=1000.0, net_ppe=400.0,
           gross_profit_period=None, total_assets_period=None,
           ev=1000.0, market_cap=..., price=10.0, debt=300.0, cash=100.0,
           reporting="EUR", quote="EUR",
           extra_lines=(), status=STATUS_OK, error=None) -> TickerFundamentals:
    """One vendor record. ``ev`` is the ENTERPRISE VALUE THE PARTS BUILD TO:
    the market cap is derived as ``ev - debt + cash`` unless given, so a
    test that asks for an EV of 1,000 gets one from the parts (rule 8). The
    vendor's own ``enterpriseValue`` is written as the memo it is."""
    if market_cap is ...:
        market_cap = None if ev is None else ev - (debt or 0.0) + (cash or 0.0)
    fields = [
        FieldValue(ticker, "sector", "OK", text=sector),
        FieldValue(ticker, "financialCurrency", "OK", text=reporting),
        FieldValue(ticker, "currency", "OK", text=quote),
        FieldValue(ticker, "enterpriseValue", "OK" if ev is not None else "NO_DATA",
                   number=ev),
        FieldValue(ticker, "marketCap",
                   "OK" if market_cap is not None else "NO_DATA", number=market_cap),
        FieldValue(ticker, "regularMarketPrice",
                   "OK" if price is not None else "NO_DATA", number=price),
        FieldValue(ticker, "totalDebt",
                   "OK" if debt is not None else "NO_DATA", number=debt),
        FieldValue(ticker, "totalCash",
                   "OK" if cash is not None else "NO_DATA", number=cash),
    ]
    series = []
    if ebit is not None:
        series.append(SeriesPoint(ticker, ebit_line, YEAR, ebit, "income"))
    if gross_profit is not None:
        series.append(SeriesPoint(ticker, "Gross Profit", gross_profit_period or YEAR,
                                  gross_profit, "income"))
    for line, value, period in (("Total Assets", total_assets, total_assets_period),
                                ("Net PPE", net_ppe, None)):
        if value is not None:
            series.append(SeriesPoint(ticker, line, period or YEAR, value, "balance"))
    series.extend(extra_lines)
    return TickerFundamentals(ticker, status, 1, 3, tuple(fields), tuple(series),
                              error=error)


class Candidate:
    def __init__(self, ticker):
        self.ticker = ticker


def euro() -> FxTable:
    return FxTable()


# --- inputs ----------------------------------------------------------------


def test_the_ebit_alias_set_is_ordered_on_MEANING_not_on_coverage():
    """L3. The as-filed operating income first, the strict EBIT label last:
    measured against 32 US names' own 10-K filings the last one matches 6 of
    32 and the first 30 of 32."""
    assert EBIT_ALIASES == ("Total Operating Income As Reported",
                            "Operating Income", "EBIT")
    got = extract_inputs("X", record(ebit_line="Operating Income"))
    assert got.ebit == 100.0 and got.ebit_label == "Operating Income"


def test_the_as_filed_label_wins_over_the_strict_ebit_line():
    both = record(extra_lines=(
        SeriesPoint("X", "Total Operating Income As Reported", YEAR, 80.0, "income"),))
    got = extract_inputs("X", both)
    assert got.ebit_label == "Total Operating Income As Reported"
    assert got.ebit == 80.0, "the strict EBIT label was preferred on coverage again"


def test_ebitda_is_never_read_as_ebit():
    only_ebitda = record(ebit=None, extra_lines=(
        SeriesPoint("X", "EBITDA", YEAR, 500.0, "income"),))
    got = extract_inputs("X", only_ebitda)
    assert got.ebit is None, "EBITDA was substituted for EBIT"


def docstrings(tree) -> set:
    """Every docstring in a module, so prose can be excluded from a code check."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            text = ast.get_docstring(node, clean=False)
            if text is not None:
                out.add(text)
    return out


def test_the_ranking_module_never_names_an_ebitda_field():
    """FRAMEWORK-EDITS E5 forbids the substitution; this holds the line.

    Checked on string constants that are NOT docstrings: the module docstring
    states the prohibition and must be allowed to say the word.
    """
    source = (ROOT / "vss" / "ranking.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    prose = docstrings(tree)
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and n.value not in prose]
    offenders = [v for v in literals if "ebitda" in v.lower()]
    assert not offenders, f"ranking.py names an ebitda field: {offenders}"
    names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    names |= {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not any("ebitda" in n.lower() for n in names)


def test_an_absent_line_is_none_never_zero():
    assert extract_inputs("X", record(ebit=None)).ebit is None
    assert extract_inputs("X", record(total_assets=None)).total_assets is None


def test_the_denominator_is_read_under_its_exact_label():
    """E6 chose NO alias set for total assets, so a second spelling must NOT
    be picked up. Every name presents it under this label (394 of 394); if
    yfinance ever starts returning a variant, this test failing is how we
    find out -- rather than a silent DATA MISSING."""
    variant = record(total_assets=None, extra_lines=(
        SeriesPoint("X", "Total Assets Net", YEAR, 1000.0, "balance"),
    ))
    assert extract_inputs("X", variant).total_assets is None


def test_no_record_yields_all_none():
    got = extract_inputs("GHOST", None)
    assert got.ebit is None and got.enterprise_value_quoted is None


def test_currency_pairs_are_quote_to_reporting():
    inputs = [extract_inputs("X", record(quote="GBp", reporting="USD"))]
    assert currency_pairs(inputs) == [("GBp", "USD")]


# --- one period per quotient (K6) ------------------------------------------


EARLIER = date(2024, 12, 31)


def test_two_fiscal_year_ends_in_one_quotient_are_DATA_MISSING():
    """AUTO.L on the 2026-08-21 run under E6: gross profit from 2024-03-31
    against total assets from 2026-03-31 -- two years apart, in one ratio,
    silently. E43 reads EBIT instead, and the same guard holds for it."""
    got = score(extract_inputs("AUTO.L", record(total_assets_period=EARLIER)), euro(), ASOF)
    assert got.quality_state == QUALITY_MIXED_PERIODS
    assert got.operating_profitability is None, "a number was produced from two years"


def test_mixed_periods_are_counted_apart_from_a_missing_line():
    """'We have both and they do not belong together' is not 'one is absent'."""
    fundamentals = {
        "MIXED": record("MIXED", total_assets_period=EARLIER),
        "ABSENT": record("ABSENT", total_assets=None),
    }
    result = rank_candidates([Candidate("MIXED"), Candidate("ABSENT")],
                             fundamentals, euro(), ASOF)
    counts = result.reason_counts()
    assert counts[QUALITY_MIXED_PERIODS] == 1
    assert counts[QUALITY_MISSING] == 1


def test_the_newest_period_flag_cannot_catch_this_and_the_test_says_so():
    """SHL.DE is why the guard is here rather than in the staleness check.

    ``newest_period`` is the MAX over every stored row. A record whose ranked
    lines are a year apart still carries the newer date, so the record reads
    OK -- which is exactly what SHL.DE did while its denominator mixed two
    balance sheets.
    """
    from vss.fundamentals import newest_period
    mixed = record("SHL.DE", total_assets_period=EARLIER)
    assert newest_period(mixed.series) == YEAR, "the fixture lost the point"
    assert mixed.status == STATUS_OK
    assert score(extract_inputs("SHL.DE", mixed), euro(), ASOF).quality_state \
        == QUALITY_MIXED_PERIODS


def test_matching_periods_pass_and_the_periods_travel_with_the_figures():
    got = extract_inputs("X", record())
    assert got.ebit_period == got.total_assets_period == YEAR
    assert got.ebit_period == YEAR
    assert score(got, euro(), ASOF).quality_state == QUALITY_OK


def test_a_mixed_period_name_keeps_its_earnings_yield_and_its_own_section():
    """The price leg is one line divided by one quote -- there is nothing in
    it for two periods to disagree about, so it survives."""
    fundamentals = {"MIXED": record("MIXED", total_assets_period=EARLIER)}
    result = rank_candidates([Candidate("MIXED")], fundamentals, euro(), ASOF)
    assert result.main == []
    assert [r.ticker for r in result.yield_only] == ["MIXED"]
    assert result.yield_only[0].scored.earnings_yield is not None


def test_the_period_question_is_asked_after_the_line_is_known_to_exist():
    """An absent line has no period to disagree with; reporting it as a
    period mismatch would name the wrong repair."""
    got = score(extract_inputs("X", record(total_assets=None,
                                           gross_profit_period=EARLIER)), euro(), ASOF)
    assert got.quality_state == QUALITY_MISSING


# --- staleness (K5) --------------------------------------------------------


STALE_REASON = "newest reported period 2024-07-31 is 751 days before 2026-08-21"


def stale_record(ticker="BWY.L", **kw):
    return record(ticker, status=STATUS_STALE, error=STALE_REASON, **kw)


def test_a_stale_record_is_excluded_although_every_leg_would_compute():
    """That is exactly what makes it dangerous.

    BWY.L on the 2026-08-21 run: an EBIT from 2024-07-31 divided into an
    enterprise value from 2026-08-21. 751 days in one quotient, and until this
    was built neither the CSV nor the report said so.
    """
    live = score(extract_inputs("X", record()), euro(), ASOF)
    assert live.operating_profitability is not None and live.earnings_yield is not None

    got = score(extract_inputs("BWY.L", stale_record()), euro(), ASOF)
    assert got.quality_state == QUALITY_STALE
    assert got.operating_profitability is None
    assert got.earnings_yield is None, "a stale record was given an earnings yield"
    assert got.note == STALE_REASON, "the reason was reconstructed, not carried"


def test_a_stale_name_reaches_no_section_of_the_ranking():
    fundamentals = {"OPCO": record("OPCO"), "OLD": stale_record("OLD")}
    result = rank_candidates([Candidate("OPCO"), Candidate("OLD")], fundamentals, euro(), ASOF)
    assert [r.ticker for r in result.main] == ["OPCO"]
    assert [r.ticker for r in result.yield_only] == []
    assert [s.ticker for s in result.unrankable] == []
    assert [s.ticker for s in result.stale] == ["OLD"]


def test_stale_is_a_rejection_ON_VALUE_never_on_missing():
    """Figures we HAVE, judged too old -- the same shape prices.py gives a
    stale close and fundamentals.py gives a stale statement. Absent figures
    are a different fact and are counted in the other column."""
    fundamentals = {"OLD": stale_record("OLD"), "GHOST": None}
    result = rank_candidates([Candidate("OLD"), Candidate("GHOST")],
                             fundamentals, euro(), ASOF)
    assert result.tally.rejected_on_value == 1
    assert result.tally.rejected_on_missing == 1


def test_stale_is_never_folded_into_unrankable():
    """'We chose not to use them' is not 'they were not there'."""
    fundamentals = {"OLD": stale_record("OLD"), "GHOST": None}
    result = rank_candidates([Candidate("OLD"), Candidate("GHOST")],
                             fundamentals, euro(), ASOF)
    assert [s.ticker for s in result.stale] == ["OLD"]
    assert [s.ticker for s in result.unrankable] == ["GHOST"]


def test_staleness_outranks_the_sector_exemption_and_the_missing_line():
    """Whichever other gap it also has, the reason reported is the oldest one:
    a bank with two-year-old accounts is not 'sector exempt', it is stale."""
    for extra in (dict(sector="Financial Services"), dict(total_assets=None)):
        got = score(extract_inputs("X", stale_record(**extra)), euro(), ASOF)
        assert got.quality_state == QUALITY_STALE


def test_the_reason_counts_carry_the_stale_bucket():
    fundamentals = {"A": record("A"), "OLD": stale_record("OLD")}
    result = rank_candidates([Candidate("A"), Candidate("OLD")], fundamentals, euro(), ASOF)
    assert result.reason_counts()[QUALITY_STALE] == 1


# --- the components --------------------------------------------------------


def test_operating_profitability_is_ebit_over_total_assets():
    """E43: the same EBIT the price leg divides, over total assets."""
    got = score(extract_inputs("X", record()), euro(), ASOF)
    assert got.quality_state == QUALITY_OK
    assert got.operating_profitability == pytest.approx(100.0 / 1000.0)


def test_the_quality_leg_never_reads_gross_profit():
    """E43 retired the vendor's Gross Profit from the key: it reconciled to a
    line of the annual report for none of the five names measured. A record
    carrying any gross profit at all ranks exactly as one carrying none, and
    the module names the line nowhere outside its docstrings -- the same
    line the ebitda test holds."""
    with_line = score(extract_inputs("X", record(gross_profit=9999.0)), euro(), ASOF)
    without = score(extract_inputs("X", record(gross_profit=None)), euro(), ASOF)
    assert with_line.operating_profitability == pytest.approx(0.10)
    assert without.operating_profitability == pytest.approx(0.10)
    assert without.quality_state == QUALITY_OK

    source = (ROOT / "vss" / "ranking.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    prose = docstrings(tree)
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and n.value not in prose]
    offenders = [v for v in literals if "gross profit" in v.lower()]
    assert not offenders, f"ranking.py names the gross-profit line: {offenders}"
    names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    names |= {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not any("gross" in n.lower() for n in names), \
        sorted(n for n in names if "gross" in n.lower())


def test_both_legs_read_one_ebit_and_a_missing_ebit_withholds_both():
    """E43's stated cost: the legs share a numerator. A name with no EBIT has
    no quality leg AND no yield, and is unrankable -- counted apart."""
    no_ebit = score(extract_inputs("X", record(ebit=None)), euro(), ASOF)
    assert no_ebit.quality_state == QUALITY_MISSING
    assert no_ebit.operating_profitability is None and no_ebit.earnings_yield is None


def test_earnings_yield_is_ebit_over_enterprise_value():
    got = score(extract_inputs("X", record(ev=2000.0)), euro(), ASOF)
    assert got.earnings_yield == pytest.approx(0.05)


def test_a_sector_exempt_name_gets_no_quality_leg_but_keeps_its_yield():
    """E6 kept E3/E5's exemption on the ECONOMIC ground, not the mechanical one.

    Gross profit over total assets is computable for a bank -- the mechanical
    obstacle E5 cited (no classified balance sheet) is gone. It is still not
    comparable, so the exemption stands and the name is ranked on one leg in
    its own section.
    """
    for sector in ("Financial Services", "Real Estate"):
        got = score(extract_inputs("X", record(sector=sector)), euro(), ASOF)
        assert got.operating_profitability is None and got.quality_state == QUALITY_SECTOR
        assert got.earnings_yield is not None


def test_utilities_are_not_exempt():
    """Greenblatt excludes them; E6 did not import the exclusion without the
    reason for it, which is regulated return, not an unmeasurable denominator."""
    got = score(extract_inputs("X", record(sector="Utilities")), euro(), ASOF)
    assert got.quality_state == QUALITY_OK


def test_a_non_positive_denominator_is_not_meaningful_never_clamped():
    got = score(extract_inputs("X", record(total_assets=-400.0)), euro(), ASOF)
    assert got.quality_state == QUALITY_NOT_MEANINGFUL
    assert got.operating_profitability is None


def test_a_zero_denominator_is_not_meaningful():
    got = score(extract_inputs("X", record(total_assets=0.0)), euro(), ASOF)
    assert got.quality_state == QUALITY_NOT_MEANINGFUL


def test_a_negative_operating_profit_is_RANKED_not_excluded():
    """The distinction E6 turns on: a negative NUMERATOR is a fact about the
    business, a non-positive DENOMINATOR is a fact about the arithmetic.

    VEFAB.ST at -0.6% on the 2026-08-21 data is the measured case. It ranks
    last on the leg; it is not sent to the one-legged section, and it is not
    confused with a missing line.
    """
    got = score(extract_inputs("X", record(ebit=-6.0, total_assets=1000.0)),
                euro(), ASOF)
    assert got.quality_state == QUALITY_OK
    assert got.operating_profitability == pytest.approx(-0.006)


def test_a_missing_input_is_distinguished_from_the_sector_exemption():
    got = score(extract_inputs("X", record(total_assets=None)), euro(), ASOF)
    assert got.quality_state == QUALITY_MISSING
    assert got.quality_state != QUALITY_SECTOR
    assert score(extract_inputs("X", record(total_assets=None)),
                 euro(), ASOF).quality_state == QUALITY_MISSING


def test_negative_ebit_gives_a_negative_yield_and_ranks_last():
    got = score(extract_inputs("X", record(ebit=-50.0)), euro(), ASOF)
    assert got.earnings_yield == pytest.approx(-0.05)


# --- currency --------------------------------------------------------------


def test_enterprise_value_is_converted_into_the_reporting_currency():
    """The MARKET CAP is what converts: it is in the quote currency. The
    net-debt legs arrive from the quote summary already in the reporting
    currency and are added AFTER the rate, unconverted (rule 8)."""
    table = build_table([("SEK", "USD")], lookup=lambda b, q: (0.10, YEAR, "x"))
    got = score(extract_inputs("X", record(ev=10_000.0, debt=0.0, cash=0.0,
                                           quote="SEK", reporting="USD")),
                table, ASOF)
    assert got.market_cap_settled == pytest.approx(10_000.0)   # SEK
    assert got.enterprise_value == pytest.approx(1000.0)        # USD
    assert got.earnings_yield == pytest.approx(0.1)
    assert got.fx_pair == "SEK->USD" and got.fx_rate == 0.10

    legs = score(extract_inputs("X", record(ev=10_000.0, debt=300.0, cash=100.0,
                                            quote="SEK", reporting="USD")),
                 table, ASOF)
    # 9,800 SEK of market cap x 0.10 + 300 - 100 USD: the legs are not scaled.
    assert legs.enterprise_value == pytest.approx(980.0 + 200.0)


def test_a_pence_quoted_name_is_not_divided_by_a_hundred():
    """The bug that does the most damage and shows the least.

    EV comes back in GBP for a GBp-quoted name. Treating it as pence would
    multiply the earnings yield by 100 and float every British name to the
    top of the list.
    """
    table = build_table([("GBp", "GBP")], lookup=lambda b, q: (999.0, YEAR, "wrong"))
    got = score(extract_inputs("X", record(ev=1000.0, quote="GBp", reporting="GBP")),
                table, ASOF)
    assert got.fx_rate == 1.0, "GBp->GBP must be identity, not a fetched rate"
    assert got.enterprise_value == pytest.approx(1000.0)
    assert got.earnings_yield == pytest.approx(0.1)


def test_a_missing_rate_blocks_the_yield_rather_than_assuming_parity():
    got = score(extract_inputs("X", record(quote="SEK", reporting="USD")), FxTable(), ASOF)
    assert got.earnings_yield is None
    assert "no fx rate" in got.note and "SEK->USD" in got.note


def test_a_missing_market_cap_blocks_the_yield():
    """Rule 8: with no market cap there is no share count to re-price."""
    got = score(extract_inputs("X", record(market_cap=None)), euro(), ASOF)
    assert got.earnings_yield is None and got.note == "no market cap"


def test_the_vendors_enterprise_value_is_a_memo_and_decides_nothing():
    """The same record with the vendor's field ABSENT ranks exactly the same:
    the field is written to the CSV and read by no component."""
    with_memo = score(extract_inputs("X", record(ev=1000.0)), euro(), ASOF)
    without = score(extract_inputs("X", record(ev=None, market_cap=800.0)), euro(), ASOF)
    assert with_memo.enterprise_value == pytest.approx(1000.0)
    assert without.enterprise_value == pytest.approx(1000.0)
    assert with_memo.earnings_yield == without.earnings_yield
    assert without.inputs.enterprise_value_quoted is None


def test_a_missing_fetch_day_quote_blocks_the_yield_rather_than_guessing_a_count():
    """A store written before `regularMarketPrice` existed cannot say what
    price its marketCap embeds, so no share count is implied from it."""
    got = score(extract_inputs("X", record(price=None)), euro(), ASOF)
    assert got.earnings_yield is None
    assert "no fetch-day quote" in got.note and "regularMarketPrice" in got.note


def test_a_missing_settled_close_blocks_the_yield():
    got = score(extract_inputs("X", record(), close=None), euro(), ASOF)
    assert got.earnings_yield is None and "no settled close" in got.note


def test_missing_debt_or_cash_blocks_the_yield():
    for missing in (dict(debt=None), dict(cash=None)):
        got = score(extract_inputs("X", record(**missing)), euro(), ASOF)
        assert got.earnings_yield is None, missing
        assert "no total debt or total cash" in got.note


def test_the_yield_is_struck_on_the_settled_close_not_the_price_the_vendor_embeds():
    """FGR.PA on 2026-08-26, to the figures in the store (SCREENER-REVIEW-3
    Part 12.3). The vendor's enterpriseValue of 22,575m is 129.29 EUR -- the
    close of 2026-06-16 -- on its own 98.0m shares plus net debt; the settled
    close was 117.50. Same shares, same net debt, today's price."""
    fgr = record(
        "FGR.PA", ebit=2_545_000_000.0, ebit_line="Total Operating Income As Reported",
        ev=22_575_448_064.0, market_cap=11_514_999_808.0, price=117.50,
        debt=15_774_999_552.0, cash=5_870_000_128.0,
    )
    got = score(extract_inputs("FGR.PA", fgr, close=(date(2026, 8, 26), 117.50)),
                euro(), date(2026, 8, 26))
    assert got.implied_shares == pytest.approx(98.0e6, rel=1e-4)
    assert got.market_cap_settled == pytest.approx(11_515.0e6, rel=1e-4)
    assert got.enterprise_value == pytest.approx(21_420.0e6, rel=1e-4)
    assert got.earnings_yield == pytest.approx(2_545.0 / 21_420.0, abs=5e-4)
    assert got.earnings_yield != pytest.approx(2_545.0 / 22_575.4, abs=5e-4)
    # The vendor's figure would have been the close of 2026-06-16 on the
    # same count: (22,575.4 - 15,775.0 + 5,870.0) / 98.0 = 129.29.
    embedded = (fgr.value("enterpriseValue") - fgr.value("totalDebt")
                + fgr.value("totalCash")) / got.implied_shares
    assert embedded == pytest.approx(129.29, abs=0.01)


def test_a_pence_quoted_name_implies_its_count_in_pounds():
    """HWDN.L's shape: marketCap in GBP, regularMarketPrice and the close in
    pence. Both prices are divided to pounds before the count is implied
    and the cap re-struck -- 4,475m GBP / 8.20 = 545.8m shares, not 5.5m."""
    got = score(extract_inputs("HWDN.L", record(
        "HWDN.L", market_cap=4_475_390_976.0, price=820.0, debt=0.0, cash=0.0,
        reporting="GBP", quote="GBp"), close=(ASOF, 800.0)), euro(), ASOF)
    assert got.implied_shares == pytest.approx(545_779_382, rel=1e-4)
    assert got.market_cap_settled == pytest.approx(545_779_382 * 8.00, rel=1e-4)
    assert got.enterprise_value == pytest.approx(545_779_382 * 8.00, rel=1e-4)


# --- ranking ---------------------------------------------------------------


def test_competition_ranking_shares_the_better_rank():
    assert competition_ranks([10, 5, 5, 1]) == [1, 2, 2, 4]


def test_highest_value_is_rank_one():
    assert competition_ranks([1, 3, 2]) == [3, 1, 2]


def test_the_two_placings_are_summed_and_sorted_ascending():
    """B wins both legs, C loses both, A is in between -- no tie to resolve."""
    fundamentals = {
        # EBIT/TA: A 10%, B 20%, C 1%
        "A": record("A", ebit=100.0, total_assets=1000.0, ev=1000.0),   # EY 10%
        "B": record("B", ebit=100.0, total_assets=500.0, ev=500.0),     # EY 20%
        "C": record("C", ebit=10.0, total_assets=1000.0, ev=1000.0),    # EY 1%
    }
    result = rank_candidates([Candidate(t) for t in "ABC"], fundamentals, euro(), ASOF)
    assert [r.ticker for r in result.main] == ["B", "A", "C"]
    assert [r.combined for r in result.main] == [2, 4, 6]
    for row in result.main:
        assert row.combined == row.quality_rank + row.ey_rank


def test_an_equal_sum_breaks_alphabetically():
    fundamentals = {
        # Z beats A on the quality leg, A beats Z on yield: sums equal.
        "A": record("A", ebit=100.0, total_assets=1000.0, ev=500.0),
        "Z": record("Z", ebit=100.0, total_assets=500.0, ev=2000.0),
    }
    result = rank_candidates([Candidate("Z"), Candidate("A")], fundamentals, euro(), ASOF)
    assert [r.combined for r in result.main] == [3, 3]
    assert [r.ticker for r in result.main] == ["A", "Z"]


def test_one_legged_names_go_to_their_own_section_never_interleaved():
    fundamentals = {
        "BANK": record("BANK", sector="Financial Services", ebit=100.0, ev=500.0),
        "OPCO": record("OPCO", ebit=100.0, ev=1000.0),
    }
    result = rank_candidates([Candidate("BANK"), Candidate("OPCO")], fundamentals, euro(), ASOF)
    assert [r.ticker for r in result.main] == ["OPCO"]
    assert [r.ticker for r in result.yield_only] == ["BANK"]
    assert all(r.combined is None for r in result.yield_only)
    assert all(r.quality_rank is None for r in result.yield_only)


def test_the_yield_only_section_is_ranked_on_its_own_yields():
    fundamentals = {
        "L": record("L", sector="Real Estate", ebit=10.0, ev=1000.0),
        "H": record("H", sector="Real Estate", ebit=100.0, ev=1000.0),
    }
    result = rank_candidates([Candidate("L"), Candidate("H")], fundamentals, euro(), ASOF)
    assert [r.ticker for r in result.yield_only] == ["H", "L"]
    assert [r.ey_rank for r in result.yield_only] == [1, 2]


def test_a_name_with_neither_component_is_unrankable_and_named():
    result = rank_candidates([Candidate("GHOST")], {}, euro(), ASOF)
    assert result.main == [] and result.yield_only == []
    assert [s.ticker for s in result.unrankable] == ["GHOST"]
    assert result.tally.rejected_on_missing == 1


def test_the_reason_counts_keep_the_three_causes_apart():
    fundamentals = {
        "A": record("A"),
        "B": record("B", sector="Real Estate"),
        "C": record("C", total_assets=0.0),
        "D": record("D", total_assets=None),
    }
    result = rank_candidates([Candidate(t) for t in "ABCD"], fundamentals, euro(), ASOF)
    counts = result.reason_counts()
    assert counts[QUALITY_OK] == 1
    assert counts[QUALITY_SECTOR] == 1
    assert counts[QUALITY_NOT_MEANINGFUL] == 1
    assert counts[QUALITY_MISSING] == 1


def test_the_ranking_sets_no_price_and_no_fair_value():
    """Checked on the code, not the prose: the docstring must be able to say
    that PIPELINE names carry no mbp and no fv_base."""
    source = (ROOT / "vss" / "ranking.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    prose = docstrings(tree)
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and n.value not in prose]
    names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    names |= {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    for forbidden in ("mbp", "fv_base", "stop_price", "compute_mbp"):
        assert forbidden not in names, f"ranking.py touches {forbidden}"
        assert not any(forbidden in v.lower() for v in literals)
    assert not any("watchlist" in v.lower() for v in literals)


# --- one company, two listings ---------------------------------------------


class Listing:
    def __init__(self, ticker, marknad="Stockholm"):
        self.ticker = ticker
        self.marknad = marknad


def statement_record(ticker, *, ebit=100.0, revenue=1000.0, ppe=400.0,
                     assets=2000.0, currency="SEK", sector="Technology"):
    fields = [
        FieldValue(ticker, "sector", "OK", text=sector),
        FieldValue(ticker, "financialCurrency", "OK", text=currency),
        FieldValue(ticker, "currency", "OK", text=currency),
    ]
    series = [
        SeriesPoint(ticker, "EBIT", YEAR, ebit, "income"),
        SeriesPoint(ticker, "Total Revenue", YEAR, revenue, "income"),
        SeriesPoint(ticker, "Net PPE", YEAR, ppe, "balance"),
        SeriesPoint(ticker, "Total Assets", YEAR, assets, "balance"),
    ]
    return TickerFundamentals(ticker, STATUS_OK, 1, 3, tuple(fields), tuple(series))


def test_two_share_classes_are_identified_by_identical_accounts():
    from vss.ranking import collapse_share_classes

    fundamentals = {"ERIC-A.ST": statement_record("ERIC-A.ST"),
                    "ERIC-B.ST": statement_record("ERIC-B.ST")}
    kept, merges, tally = collapse_share_classes(
        [Listing("ERIC-A.ST"), Listing("ERIC-B.ST")], fundamentals,
        {"ERIC-A.ST": 241_683.0, "ERIC-B.ST": 78_197_843.0},
        {"ERIC-A.ST": "SEK", "ERIC-B.ST": "SEK"},
        FxTable(),
    )
    assert [c.ticker for c in kept] == ["ERIC-B.ST"]
    assert len(merges) == 1
    assert merges[0].kept == "ERIC-B.ST" and merges[0].dropped == "ERIC-A.ST"
    assert "turnover" in merges[0].basis
    assert tally.rejected_on_value == 1
    # L6: two Stockholm lines are already in one unit. With an EMPTY rate
    # table this contest is still decided, and it is decided in SEK.
    assert merges[0].basis.endswith("(SEK)")
    assert merges[0].detail.endswith("SEK/day")


def test_identity_is_not_a_ticker_string_guess():
    """EQT (US gas) and EQT.ST (Swedish private equity) share a stem and are
    not the same company. Different accounts keep them apart."""
    from vss.ranking import collapse_share_classes

    fundamentals = {
        "EQT": statement_record("EQT", ebit=900.0, revenue=5000.0, currency="USD"),
        "EQT.ST": statement_record("EQT.ST", ebit=100.0, revenue=1000.0),
    }
    kept, merges, _ = collapse_share_classes(
        [Listing("EQT"), Listing("EQT.ST")], fundamentals, {}, {}, euro())
    assert sorted(c.ticker for c in kept) == ["EQT", "EQT.ST"]
    assert merges == []


def test_a_partial_fingerprint_never_matches():
    """An absent line must not make two companies look alike."""
    from vss.ranking import collapse_share_classes, company_fingerprint

    thin = statement_record("A")
    thin = TickerFundamentals(
        "A", STATUS_OK, 1, 3, thin.fields,
        tuple(p for p in thin.series if p.line != "Total Assets"))
    assert company_fingerprint(thin) is None
    kept, merges, _ = collapse_share_classes(
        [Listing("A"), Listing("B")],
        {"A": thin, "B": statement_record("B")}, {}, {}, euro())
    assert len(kept) == 2 and merges == []


def test_a_different_sector_or_currency_breaks_the_group():
    from vss.ranking import company_fingerprint

    a = company_fingerprint(statement_record("A"))
    assert a != company_fingerprint(statement_record("B", sector="Industrials"))
    assert a != company_fingerprint(statement_record("C", currency="EUR"))


def test_without_turnover_the_fallback_says_so():
    from vss.ranking import collapse_share_classes

    fundamentals = {"A-A.ST": statement_record("A-A.ST"),
                    "A-B.ST": statement_record("A-B.ST")}
    kept, merges, _ = collapse_share_classes(
        [Listing("A-A.ST"), Listing("A-B.ST")], fundamentals, {"A-A.ST": 5.0},
        {"A-A.ST": "SEK", "A-B.ST": "SEK"}, euro())
    assert len(kept) == 1
    assert "no turnover" in merges[0].basis
    assert merges[0].detail == ""


def test_a_lone_listing_is_untouched():
    from vss.ranking import collapse_share_classes

    kept, merges, tally = collapse_share_classes(
        [Listing("SAND.ST")], {"SAND.ST": statement_record("SAND.ST")}, {}, {},
        euro())
    assert [c.ticker for c in kept] == ["SAND.ST"]
    assert merges == [] and tally.rejected == 0


# --- turnover, and the minor unit ------------------------------------------


def turnover_frame(close, volume, days=100, last=date(2026, 8, 21)):
    import pandas as pd

    index = pd.to_datetime([last - pd.Timedelta(days=days - 1 - i) for i in range(days)])
    return pd.DataFrame({"Close": [close] * days, "Volume": [volume] * days}, index=index)


def test_turnover_is_close_times_volume_in_the_target_currency():
    from vss.fx import build_table
    from vss.ranking import median_turnover

    table = build_table([("SEK", "EUR")], lookup=lambda b, q: (0.09, YEAR, "x"))
    got = median_turnover(turnover_frame(100.0, 1000.0), date(2026, 8, 21), "SEK", table)
    assert got == pytest.approx(100.0 * 1000.0 * 0.09)


def test_a_pence_quoted_series_is_divided_to_pounds_first():
    """Without the divisor a London line looks a hundred times the size it is
    and wins every share-class contest it enters."""
    from vss.fx import build_table
    from vss.ranking import median_turnover

    table = build_table([("GBp", "EUR")], lookup=lambda b, q: (1.17, YEAR, "x"))
    got = median_turnover(turnover_frame(3905.0, 1000.0), date(2026, 8, 21), "GBp", table)
    assert got == pytest.approx(3905.0 / 100.0 * 1000.0 * 1.17)


def test_a_missing_rate_yields_no_turnover_rather_than_a_wrong_one():
    from vss.fx import FxTable
    from vss.ranking import median_turnover

    assert median_turnover(turnover_frame(100.0, 10.0), date(2026, 8, 21),
                           "SEK", FxTable()) is None


def test_turnover_ignores_sessions_outside_the_window():
    from vss.fx import FxTable
    from vss.ranking import median_turnover

    frame = turnover_frame(100.0, 1000.0, days=400)
    got = median_turnover(frame, date(2026, 8, 21), "EUR", FxTable(), window_days=90)
    assert got == pytest.approx(100_000.0)


def test_an_empty_series_has_no_turnover():
    import pandas as pd

    from vss.fx import FxTable
    from vss.ranking import median_turnover

    assert median_turnover(pd.DataFrame(), date(2026, 8, 21), "EUR", FxTable()) is None


# --- the enterprise-value bound (L2), now on the PARTS -----------------------
#
# The enterprise value is built here from marketCap / regularMarketPrice x
# the settled close + totalDebt - totalCash (rule 8), so the vendor's
# precomputed field can no longer smuggle an impossible figure in. What the
# bound guards now is the parts: no company holds more net cash
# (totalCash - totalDebt) than it holds assets. Not a threshold: the one
# comparison the arithmetic forbids.


def rate_table(pair_from, pair_to, value, day=YEAR) -> FxTable:
    from vss.fx import Rate

    table = FxTable()
    table.rates[f"{pair_from}->{pair_to}"] = Rate(
        f"{pair_from}->{pair_to}", value, day, "test")
    return table


#: LISP.SW's shape as the VENDOR field carried it on 2026-08-21: 17.6bn CHF
#: of net cash against 9.1bn of total assets. Written here as the parts that
#: would have to be wrong for the built enterprise value to imply it.
IMPOSSIBLE = dict(debt=0.0, cash=17_639.3, total_assets=9_098.7)


def test_net_cash_implying_more_than_total_assets_loses_the_yield():
    got = score(extract_inputs("X", record(**IMPOSSIBLE)), euro(), ASOF)
    assert got.earnings_yield is None
    assert EV_IMPOSSIBLE_NOTE in got.note
    assert "1.9x" in got.note


def test_a_refused_enterprise_value_keeps_its_quality_leg_and_records_the_figure():
    """The bound judges the parts, not the business -- and the number it
    refused is written down rather than merely alleged."""
    got = score(extract_inputs("X", record(**IMPOSSIBLE)), euro(), ASOF)
    assert got.quality_state == QUALITY_OK
    assert got.operating_profitability is not None
    assert got.enterprise_value == pytest.approx(1000.0)
    assert got.fx_rate is not None


def test_net_cash_exactly_equal_to_total_assets_still_passes():
    """The bound is generous BY CONSTRUCTION and is not a tolerance: it fires
    only where the arithmetic is impossible, never where it is merely odd."""
    got = score(extract_inputs("X", record(
        debt=0.0, cash=1000.0, total_assets=1000.0)), euro(), ASOF)
    assert got.earnings_yield is not None, "the bound fired on equality"


def test_net_debt_never_trips_the_bound():
    """Net debt buries a name instead of promoting it, and this check is not
    the one that would find it."""
    got = score(extract_inputs("X", record(debt=5000.0, cash=0.0)), euro(), ASOF)
    assert got.earnings_yield is not None


def test_the_vendors_impossible_enterprise_value_no_longer_reaches_the_yield():
    """LISP.SW on 2026-08-21, to the store's figures: vendor enterpriseValue
    3,539.8m CHF against a market cap of 21,179.2m -- and totalCash 410.7m,
    totalDebt 1,846.2m. The parts build 22,614.7m, the figure the review
    computed by hand, and the vendor's number is a memo."""
    got = score(extract_inputs("LISP.SW", record(
        "LISP.SW", ev=3_539.8, market_cap=21_179.2, debt=1_846.2, cash=410.7,
        total_assets=9_098.7, reporting="CHF", quote="CHF")), euro(), ASOF)
    assert got.earnings_yield is not None
    assert EV_IMPOSSIBLE_NOTE not in got.note
    assert got.enterprise_value == pytest.approx(22_614.7, abs=0.1)


def test_the_bound_needs_no_rate_because_the_parts_share_a_currency():
    """PLUS.L's shape: quoted in pence, reporting in USD. totalCash,
    totalDebt and total assets are all in the REPORTING currency, so the
    comparison is made in one unit without a rate -- 838 of net cash under
    944 of assets. The rate is applied ONCE, to the market cap alone, on
    its way into the enterprise value."""
    inputs = extract_inputs("PLUS.L", record(
        "PLUS.L", market_cap=2_521.9, price=100.0, debt=23.1, cash=861.3,
        total_assets=944.1, reporting="USD", quote="GBp"), close=(ASOF, 100.0))
    got = score(inputs, rate_table("GBP", "USD", 1.3647964), ASOF)
    assert got.earnings_yield is not None
    assert EV_IMPOSSIBLE_NOTE not in got.note
    assert got.market_cap_settled == pytest.approx(2_521.9)
    assert got.enterprise_value == pytest.approx(2_521.9 * 1.3647964 + 23.1 - 861.3)


def test_a_missing_total_assets_asks_no_question_either():
    """DATA MISSING is a third state here too: with nothing to bound against,
    the check neither convicts nor acquits -- it does not run."""
    got = score(extract_inputs("X", record(
        market_cap=6000.0, debt=0.0, cash=5000.0, total_assets=None)), euro(), ASOF)
    assert got.earnings_yield is not None
    assert EV_IMPOSSIBLE_NOTE not in got.note


def test_a_refused_yield_is_counted_on_MISSING_data_never_on_value():
    """The owner's binding condition on this check, executed."""
    from vss.universe import ON_MISSING

    refused = score(extract_inputs("X", record(**IMPOSSIBLE)), euro(), ASOF)
    result = rank([refused])
    assert result.main == [] and result.yield_only == []
    assert [s.ticker for s in result.unrankable] == ["X"]
    assert result.tally.rejected_on_value == 0
    assert result.tally.rejected_on_missing == 1
    assert result.tally.reasons[
        f"{ON_MISSING}:quality leg computed, no earnings yield"] == 1


# --- the staleness gate reads the rows the key reads (L4) ------------------
#
# fundamentals.py sets STALE from newest_period, which is the MAX over every
# stored row. SHL.DE's whole ranking key was 690 days old and the record read
# OK, because Net PPE and Ordinary Shares Number carried a date a year newer.
# COLO-B.CO was the same 690 days old and was excluded.

OLD = date(2024, 9, 30)          # 690 days before ASOF, SHL.DE's own date
ANCIENT = date(2024, 3, 31)      # 873 days before ASOF, AUTO.L's older line


def shl_de_shape(**kw) -> TickerFundamentals:
    """Every ranked line 690 days old; Net PPE fresh. Status OK, as it was."""
    return record(
        "SHL.DE", ebit=None, total_assets_period=OLD,
        net_ppe=4_715.0,
        extra_lines=(SeriesPoint("SHL.DE", "EBIT", OLD, 100.0, "income"),
                     SeriesPoint("SHL.DE", "Ordinary Shares Number", YEAR,
                                 1_116.0, "balance")),
        **kw,
    )


def test_a_key_read_entirely_from_old_rows_is_stale_although_the_record_is_OK():
    from vss.fundamentals import newest_period

    fundamentals = shl_de_shape()
    assert fundamentals.status == STATUS_OK
    assert newest_period(fundamentals.series) == YEAR, \
        "the fixture lost the point: newest_period must still look fresh"

    got = score(extract_inputs("SHL.DE", fundamentals), euro(), ASOF)
    assert got.quality_state == QUALITY_STALE
    assert got.operating_profitability is None and got.earnings_yield is None
    assert "2024-09-30" in got.note and "690 days" in got.note


def test_two_names_of_the_same_age_are_treated_the_same_way():
    """The whole of L4 in one assertion. Before the fix one was ranked and the
    other excluded, decided by a row neither leg touches."""
    fundamentals = {
        "SHL.DE": shl_de_shape(),
        "COLO-B.CO": record("COLO-B.CO", status=STATUS_STALE,
                            error="newest reported period 2024-09-30 is 690 days "
                                  "before 2026-08-21"),
    }
    result = rank_candidates([Candidate("SHL.DE"), Candidate("COLO-B.CO")],
                             fundamentals, euro(), ASOF)
    assert [s.ticker for s in result.stale] == ["COLO-B.CO", "SHL.DE"]
    assert result.main == [] and result.yield_only == []


def test_a_one_legged_name_is_judged_on_the_one_row_it_was_ranked_on():
    """ERIE's shape: sector exempt, so only EBIT is read -- and its newest EBIT
    row is empty, so the yield was formed from a 2024 figure."""
    erie = record("ERIE", sector="Financial Services", ebit=None,
                  extra_lines=(SeriesPoint("ERIE", "EBIT", OLD, 100.0, "income"),))
    got = score(extract_inputs("ERIE", erie), euro(), ASOF)
    assert got.quality_state == QUALITY_STALE
    assert "690 days" in got.note


def test_a_quality_leg_the_exemption_never_evaluated_does_not_make_a_name_stale():
    """The mirror of the test above: a bank whose EBIT is current is not
    excluded because of two lines its ranking never read."""
    bank = record("BANK", sector="Financial Services",
                  total_assets_period=OLD)
    got = score(extract_inputs("BANK", bank), euro(), ASOF)
    assert got.quality_state == QUALITY_SECTOR
    assert got.earnings_yield is not None


def test_the_gate_does_not_swallow_the_mixed_period_finding():
    """AUTO.L's shape. Two year-ends in one quotient is a statement about the
    LINES; measuring the age of a line that fed nothing would report it as
    stale instead and K6's finding would vanish behind this one."""
    auto = record("AUTO.L", total_assets_period=ANCIENT)
    got = score(extract_inputs("AUTO.L", auto), euro(), ASOF)
    assert got.quality_state == QUALITY_MIXED_PERIODS
    assert "days before" not in got.note


def test_an_old_row_the_key_never_reads_does_not_make_a_name_stale():
    """The other direction of the same rule: a fresh key with a stale
    neighbour is not stale. Net PPE is a fingerprint line, not a ranked one."""
    got = score(extract_inputs("X", record(
        extra_lines=(SeriesPoint("X", "Long Term Debt", ANCIENT, 5.0, "balance"),))),
        euro(), ASOF)
    assert got.quality_state == QUALITY_OK
    assert got.earnings_yield is not None


def test_rank_candidates_will_not_rank_without_a_run_date():
    """No default: a caller that drops the run date gets an error, not a
    ranking with the staleness gate silently skipped."""
    with pytest.raises(TypeError):
        rank_candidates([Candidate("X")], {"X": record()}, euro())    # type: ignore[call-arg]


def test_the_limit_is_the_one_fundamentals_uses_and_is_not_restated():
    """One number, one place. A second copy is how two gates drift apart."""
    from vss import ranking
    from vss.fundamentals import MAX_REPORT_AGE_DAYS

    assert ranking.MAX_REPORT_AGE_DAYS is MAX_REPORT_AGE_DAYS
    source = (ROOT / "vss" / "ranking.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and n.value == MAX_REPORT_AGE_DAYS]
    assert not literals, "the staleness limit is restated as a literal in ranking.py"


def test_the_stale_note_is_measured_not_asserted():
    """The sentence carries the date and the age, so the report names both."""
    from vss.ranking import stale_note

    assert stale_note(ASOF, [YEAR]) is None
    assert stale_note(ASOF, []) is None, "no rows read is not an accusation"
    said = stale_note(ASOF, [OLD, YEAR])
    assert said is not None and "2024-09-30" in said and "690" in said, \
        "the OLDEST row that was read is the one that decides"


# --- the EBIT label, the year, and the unit (L3) ---------------------------


def test_the_year_is_settled_before_the_label():
    """The preferred label is two years older; the fallback is current.

    Nine of the 394 candidates look like this, and taking the first label
    present at whatever year IT ends in would hand them a stale figure with a
    current one beside it in the same store. NVR is one of them, at place 20.
    """
    older = date(2023, 12, 31)
    got = extract_inputs("NVR", record(
        "NVR", ebit=None, extra_lines=(
            SeriesPoint("NVR", "Total Operating Income As Reported", older, 70.0, "income"),
            SeriesPoint("NVR", "Operating Income", YEAR, 95.0, "income"),
        )))
    assert got.ebit_period == YEAR
    assert (got.ebit_label, got.ebit) == ("Operating Income", 95.0)


def test_meaning_still_decides_within_the_newest_year():
    got = extract_inputs("X", record(
        "X", ebit=None, extra_lines=(
            SeriesPoint("X", "EBIT", YEAR, 120.0, "income"),
            SeriesPoint("X", "Operating Income", YEAR, 100.0, "income"),
            SeriesPoint("X", "Total Operating Income As Reported", YEAR, 90.0, "income"),
        )))
    assert (got.ebit_label, got.ebit) == ("Total Operating Income As Reported", 90.0)


def test_the_strict_label_is_used_when_it_is_the_only_one_for_the_newest_year():
    """The reorder is a preference, not an exclusion: coverage becomes a
    fallback chain rather than disappearing."""
    got = extract_inputs("X", record())
    assert (got.ebit_label, got.ebit) == ("EBIT", 100.0)


def test_two_labels_that_are_one_figure_in_two_units_are_DATA_MISSING():
    """MONC.MI's shape, to the digit."""
    got = extract_inputs("MONC.MI", record(
        "MONC.MI", ebit=None, extra_lines=(
            SeriesPoint("MONC.MI", "Operating Income", YEAR, 913_356_000.0, "income"),
            SeriesPoint("MONC.MI", "Total Operating Income As Reported", YEAR,
                        913_356.0, "income"),
        )))
    assert got.ebit is None, "a figure was picked although the unit is unknown"
    assert got.ebit_label is None
    assert got.ebit_period == YEAR, "the year is known even when the unit is not"
    assert "one figure in two units" in (got.ebit_unit_conflict or "")
    assert score(got, euro(), ASOF).note == got.ebit_unit_conflict


def test_the_unit_conflict_is_not_resolved_by_preferring_the_larger_figure():
    """Revenue would tell us which unit is meant. Inferring it is a choice,
    and this key does not make choices about numbers it cannot read."""
    got = extract_inputs("X", record(
        "X", ebit=None, extra_lines=(
            SeriesPoint("X", "Operating Income", YEAR, 913_356_000.0, "income"),
            SeriesPoint("X", "Total Operating Income As Reported", YEAR, 913_356.0,
                        "income"),
            SeriesPoint("X", "Total Revenue", YEAR, 3_132_128_000.0, "income"),
        )))
    assert got.ebit is None


def test_an_ordinary_economic_gap_between_two_labels_is_not_a_unit_slip():
    """IP carries EBIT -2,817M against Operating Income -10M -- 281.7x, the
    largest real gap in the whole candidate set and a factor of 3.6 below the
    boundary. It is a difference between two measures, not two units."""
    got = extract_inputs("IP", record(
        "IP", ebit=None, extra_lines=(
            SeriesPoint("IP", "EBIT", YEAR, -2_817_000_000.0, "income"),
            SeriesPoint("IP", "Operating Income", YEAR, -10_000_000.0, "income"),
        )))
    assert got.ebit == -10_000_000.0
    assert got.ebit_unit_conflict is None


def test_the_unit_check_only_compares_figures_from_one_year_end():
    """Two labels a thousand apart in DIFFERENT years are not one figure in
    two units -- they are not one figure at all, and only the newest year is
    read anyway."""
    got = extract_inputs("X", record(
        "X", ebit=None, extra_lines=(
            SeriesPoint("X", "Operating Income", YEAR, 913_356_000.0, "income"),
            SeriesPoint("X", "Total Operating Income As Reported",
                        date(2023, 12, 31), 913_356.0, "income"),
        )))
    assert got.ebit == 913_356_000.0
    assert got.ebit_unit_conflict is None


@pytest.mark.parametrize("first,second,slipped", [
    (913_356_000.0, 913_356.0, True),          # MONC.MI, exactly 1000x
    (913_356.0, 913_356_000.0, True),          # and the other way round
    (1e9, 1e3, True),                          # a million: 1000 squared
    (-2_817_000_000.0, -10_000_000.0, False),  # IP, 281.7x -- economic
    (100.0, 100.0, False),
    (1_005_000.0, 1_000.0, True),              # 1005x, inside the 1% band
    (1_100_000.0, 1_000.0, False),             # 1100x, outside it
    (0.0, 1_000.0, False),                     # a zero decides nothing
])
def test_is_unit_slip_on_the_cases_that_define_it(first, second, slipped):
    from vss.ranking import is_unit_slip

    assert is_unit_slip(first, second) is slipped


def test_the_unit_tolerance_is_stated_and_the_answer_does_not_depend_on_it():
    from vss.ranking import UNIT_TOLERANCE, is_unit_slip

    assert UNIT_TOLERANCE == 0.01
    for tolerance in (1e-9, 1e-6, 1e-3, 1e-2):
        assert is_unit_slip(913_356_000.0, 913_356.0, tolerance=tolerance)
        assert not is_unit_slip(-2_817_000_000.0, -10_000_000.0, tolerance=tolerance)


# --- L6: the rate is asked for only where the contest needs one ------------


def test_a_single_currency_group_is_decided_without_any_rate():
    """Six of the eight groups on 2026-08-21 are two Stockholm lines of one
    Swedish company. Turning two SEK figures into two EUR figures cannot
    change which is larger, so requiring a rate there made six computable
    comparisons fail whenever one Swedish rate happened to be missing."""
    from vss.ranking import collapse_share_classes

    fundamentals = {"T-A.ST": statement_record("T-A.ST"),
                    "T-B.ST": statement_record("T-B.ST")}
    kept, merges, _ = collapse_share_classes(
        [Listing("T-A.ST"), Listing("T-B.ST")], fundamentals,
        {"T-A.ST": 1_000.0, "T-B.ST": 90_000.0},
        {"T-A.ST": "SEK", "T-B.ST": "SEK"},
        FxTable(),                       # no rates at all
    )
    assert [c.ticker for c in kept] == ["T-B.ST"]
    assert merges[0].basis == "highest median daily turnover (SEK)"


def test_the_alphabetical_fallback_would_have_reversed_that_contest():
    """The direction of the fallback, executed. For a Nordic A/B pair the A
    line is almost always the illiquid voting class and sorts first."""
    from vss.ranking import collapse_share_classes

    fundamentals = {"T-A.ST": statement_record("T-A.ST"),
                    "T-B.ST": statement_record("T-B.ST")}
    kept, merges, _ = collapse_share_classes(
        [Listing("T-A.ST"), Listing("T-B.ST")], fundamentals,
        {"T-A.ST": 1_000.0},             # one listing has no turnover at all
        {"T-A.ST": "SEK", "T-B.ST": "SEK"},
        FxTable(),
    )
    assert [c.ticker for c in kept] == ["T-A.ST"], \
        "the fallback no longer picks the first ticker, so the test above " \
        "is not measuring what it claims"
    assert "first by ticker" in merges[0].basis


def test_a_cross_currency_group_still_needs_a_rate_and_says_so():
    """AZN.L against AZN.ST, NOKIA.HE against NOKIA-SEK.ST. Two of eight."""
    from vss.fx import Rate
    from vss.ranking import collapse_share_classes

    fundamentals = {"X.L": statement_record("X.L"),
                    "X.ST": statement_record("X.ST")}
    quotes = {"X.L": "GBp", "X.ST": "SEK"}
    turnover = {"X.L": 100.0, "X.ST": 900.0}

    without = collapse_share_classes(
        [Listing("X.L"), Listing("X.ST")], fundamentals, turnover, quotes,
        FxTable())
    assert "first by ticker" in without[1][0].basis

    table = FxTable()
    table.rates["GBP->EUR"] = Rate("GBP->EUR", 1.1676, YEAR, "test")
    table.rates["SEK->EUR"] = Rate("SEK->EUR", 0.0899, YEAR, "test")
    with_rates = collapse_share_classes(
        [Listing("X.L"), Listing("X.ST")], fundamentals, turnover, quotes, table)
    assert [c.ticker for c in with_rates[0]] == ["X.L"], \
        "100 GBP/day beats 900 SEK/day once both are in one currency"
    assert with_rates[1][0].basis == "highest median daily turnover (EUR)"


def test_a_pence_line_is_divided_before_it_is_compared_with_a_pound_one():
    """Same major unit, different quote unit -- no rate needed, but the minor
    unit still has to go."""
    from vss.ranking import collapse_share_classes

    fundamentals = {"P.L": statement_record("P.L"), "Q.L": statement_record("Q.L")}
    kept, merges, _ = collapse_share_classes(
        [Listing("P.L"), Listing("Q.L")], fundamentals,
        # already in the MAJOR unit, as median_turnover_major returns them
        {"P.L": 500.0, "Q.L": 700.0},
        {"P.L": "GBp", "Q.L": "GBP"},
        FxTable(),
    )
    assert [c.ticker for c in kept] == ["Q.L"]
    assert merges[0].basis == "highest median daily turnover (GBP)"


def test_median_turnover_major_applies_no_rate_and_still_divides_the_minor_unit():
    from vss.ranking import median_turnover_major

    assert median_turnover_major(
        turnover_frame(3905.0, 1000.0), date(2026, 8, 21), "GBp"
    ) == pytest.approx(39_050.0)
    assert median_turnover_major(
        turnover_frame(100.0, 1000.0), date(2026, 8, 21), "SEK"
    ) == pytest.approx(100_000.0)


# --- E13: one period basis -------------------------------------------------
#
# The key compares figures ACROSS COMPANIES, so a quarter's gross profit
# against a year's is a factor of four with nothing saying so (backlog B-8).
# These fixtures use the REAL SeriesPoint, not this file's annual wrapper,
# because what is under test is exactly the length declaration.


def q(ticker, line, end, value, statement="income", months=3):
    return AnnualPoint(ticker, line, end, value, statement, months)


def quarterly_record(ticker="Q.CO", *, ends=None, gross=(100.0, 110.0, 120.0, 130.0),
                     ebit=(10.0, 11.0, 12.0, 13.0), months=3, assets=1000.0):
    ends = ends or [date(2025, 9, 30), date(2025, 12, 31),
                    date(2026, 3, 31), date(2026, 6, 30)]
    series = []
    for end, g, e in zip(ends, gross, ebit):
        series.append(q(ticker, "Gross Profit", end, g, months=months))
        series.append(q(ticker, "Total Operating Income As Reported", end, e,
                        months=months))
    series.append(q(ticker, "Total Assets", ends[-1], assets, "balance", None))
    return TickerFundamentals(
        ticker, STATUS_OK, 1, 3,
        fields=(FieldValue(ticker, "financialCurrency", "OK", text="EUR"),
                FieldValue(ticker, "currency", "OK", text="EUR"),
                FieldValue(ticker, "sector", "OK", text="Industrials"),
                FieldValue(ticker, "enterpriseValue", "OK", number=500.0),
                FieldValue(ticker, "marketCap", "OK", number=400.0),
                FieldValue(ticker, "regularMarketPrice", "OK", number=10.0),
                FieldValue(ticker, "totalDebt", "OK", number=300.0),
                FieldValue(ticker, "totalCash", "OK", number=200.0)),
        series=tuple(series), newest_period=ends[-1])


def test_four_consecutive_quarters_are_summed_and_the_stock_line_is_not():
    got = extract_inputs("Q.CO", quarterly_record())
    assert got.ebit == 46.0                   # 10 + 11 + 12 + 13
    assert got.total_assets == 1000.0
    assert got.basis == "ttm-4q"
    assert got.basis_periods[-1] == date(2026, 6, 30)


def test_an_annual_figure_is_taken_as_it_stands_and_nothing_is_summed():
    """Nothing is derived that does not need to be. The vendor path is here."""
    got = extract_inputs("X", record())
    assert got.basis == "annual"
    assert got.basis_periods == ()


def test_a_gap_in_the_four_quarters_is_input_missing(tmp_path=None):
    """`2025-Q2, 2025-Q4, 2026-Q1, 2026-Q2` overlaps nothing and is not four
    consecutive quarters. The overlap guard cannot see a HOLE; this does."""
    holed = quarterly_record(ends=[date(2025, 6, 30), date(2025, 12, 31),
                                   date(2026, 3, 31), date(2026, 6, 30)])
    got = extract_inputs("Q.CO", holed)
    assert got.ebit is None
    assert got.basis is None
    assert "a quarter is missing" in got.basis_note


def test_a_flow_line_of_unrecorded_length_is_not_meaningful():
    """E13: never ranked on an ASSUMED basis. Distinct from an absent line."""
    unknown = quarterly_record(months=None)
    got = extract_inputs("Q.CO", unknown)
    assert got.ebit_state == QUALITY_BASIS_UNKNOWN
    assert "does not record how long a period it covers" in got.basis_note
    assert score(got, euro(), ASOF).quality_state == QUALITY_BASIS_UNKNOWN


def test_not_meaningful_is_counted_apart_from_an_absent_line():
    absent = extract_inputs("X", record(ebit=None))
    assert score(absent, euro(), ASOF).quality_state == QUALITY_MISSING
    assert score(extract_inputs("Q.CO", quarterly_record(months=None)),
                 euro(), ASOF).quality_state == QUALITY_BASIS_UNKNOWN


def test_a_half_yearly_series_is_not_ranked_and_says_why():
    """E13 taken literally: a half-yearly reporter has no quarters, so it has
    fewer than four of them. Whether the rules should be restated in TIME for
    such a reporter is B12's open question and is not decided here."""
    halves = quarterly_record(
        ends=[date(2025, 6, 30), date(2025, 12, 31), date(2026, 6, 30)],
        gross=(200.0, 220.0, 240.0), ebit=(20.0, 22.0, 24.0), months=6)
    got = extract_inputs("Q.CO", halves)
    assert got.ebit is None
    assert "6-month periods" in got.basis_note


def test_staleness_is_measured_on_the_end_of_the_window():
    """A trailing twelve months is as old as the day it STOPS. Its oldest
    component is twelve months older, and rule 5 asks about what was read."""
    got = score(extract_inputs("Q.CO", quarterly_record()), euro(),
                date(2026, 8, 24))
    assert got.quality_state == QUALITY_OK, got.note
    assert got.operating_profitability == pytest.approx(0.046)


def test_the_ranking_csv_names_the_basis_and_the_periods_summed():
    from vss.screen import RANK_COLUMNS, _rank_row

    assert "basis" in RANK_COLUMNS and "basis_periods" in RANK_COLUMNS
    scored = score(extract_inputs("Q.CO", quarterly_record()), euro(), ASOF)
    row = _rank_row("ranked", scored, "Copenhagen")
    assert row["basis"] == "ttm-4q"
    assert row["basis_periods"] == "2025-09-30+2025-12-31+2026-03-31+2026-06-30"


def test_an_annual_row_names_its_basis_and_summs_nothing():
    from vss.screen import _rank_row

    row = _rank_row("ranked", score(extract_inputs("X", record()), euro(), ASOF),
                    "Stockholm")
    assert row["basis"] == "annual"
    assert row["basis_periods"] == ""


# --- item 8: E13 on the vendor's quarters, annual as the fallback -------------

TOI = "Total Operating Income As Reported"


def _quarters(ticker, line, ends_values, statement="income_quarterly"):
    return [q(ticker, line, end, value, statement) for end, value in ends_values]


def _nrest():
    """NREST.ST as the vendor carried it on 2026-08-26: FY2025 operating
    profit 265.6; quarters 47.0, 59.4, 50.2, 109.0, 59.0 to 2026-03-31
    (SCREENER-REVIEW-3 A 4.3 summed the same four by hand to 277.7)."""
    ends = [(date(2025, 3, 31), 47.0), (date(2025, 6, 30), 59.4),
            (date(2025, 9, 30), 50.2), (date(2025, 12, 31), 109.0),
            (date(2026, 3, 31), 59.0)]
    extra = _quarters("NREST.ST", TOI, ends)
    extra += _quarters("NREST.ST", "Gross Profit", [(e, v * 3) for e, v in ends])
    extra += [q("NREST.ST", "Total Assets", date(2026, 3, 31), 1000.0, "balance_quarterly", None),
              q("NREST.ST", "Total Assets", date(2025, 12, 31), 900.0, "balance_quarterly", None)]
    return record("NREST.ST", ebit=265.6, ebit_line=TOI, gross_profit=888.4,
                  total_assets=900.0, extra_lines=tuple(extra))


def test_four_vendor_quarters_are_the_basis_and_the_column_says_ttm_4q():
    got = extract_inputs("NREST.ST", _nrest())
    assert got.basis == "ttm-4q"
    assert got.ebit == pytest.approx(59.4 + 50.2 + 109.0 + 59.0)      # 277.6
    assert got.ebit_period == date(2026, 3, 31)
    assert got.basis_periods == (date(2025, 6, 30), date(2025, 9, 30),
                                 date(2025, 12, 31), date(2026, 3, 31))
    assert got.basis_note == ""
    # The denominator is total assets AT the window's end, not the newest
    # balance sheet and not the fiscal year's.
    assert (got.total_assets_period, got.total_assets) == (date(2026, 3, 31), 1000.0)
    assert score(got, euro(), ASOF).quality_state == QUALITY_OK


def test_a_half_yearly_reporter_falls_back_to_the_annual_figure_and_says_why():
    """BUCN.SW: the vendor's quarterly income statement is EMPTY -- Bucher
    reports half-yearly -- while its quarterly balance sheet carries
    2026-06-30. The EBIT is FY2025's 281.4, the basis column says annual
    and the note says why, and the denominator is total assets AT
    2025-12-31, not the newer 2026-06-30 figure (K6)."""
    extra = (q("BUCN.SW", "Total Assets", date(2026, 6, 30), 2641.7, "balance_quarterly", None),
             q("BUCN.SW", "Total Assets", date(2025, 12, 31), 2715.8, "balance_quarterly", None))
    rec = record("BUCN.SW", ebit=281.4, ebit_line=TOI, gross_profit=1472.6,
                 total_assets=2715.8, extra_lines=extra)
    got = extract_inputs("BUCN.SW", rec)
    assert got.basis == "annual"
    assert got.ebit == 281.4 and got.ebit_period == YEAR
    assert f"annual fallback: no quarterly {TOI} from the vendor" in got.basis_note
    assert (got.total_assets_period, got.total_assets) == (YEAR, 2715.8)
    assert rec.latest("Total Assets") == (date(2026, 6, 30), 2641.7), "the newest is not the one read"
    assert score(got, euro(), ASOF).quality_state == QUALITY_OK


def test_a_hole_in_the_vendors_quarters_is_data_missing_for_the_basis_and_falls_back():
    """KEMIRA.HE on 2026-08-26: quarters 2025-03-31, 06-30, 12-31, 2026-03-31,
    06-30 -- 2025-09-30 is simply absent (yfinance #1345). Four rows with a
    hole are not a trailing twelve months; the annual figure is used and
    the note names the jump. Nothing is filled with a zero."""
    ends = [date(2025, 3, 31), date(2025, 6, 30), date(2025, 12, 31),
            date(2026, 3, 31), date(2026, 6, 30)]
    extra = _quarters("KEMIRA.HE", TOI, [(e, 50.0) for e in ends])
    extra += _quarters("KEMIRA.HE", "Gross Profit", [(e, 150.0) for e in ends])
    got = extract_inputs("KEMIRA.HE", record("KEMIRA.HE", ebit=200.0, ebit_line=TOI,
                                             extra_lines=tuple(extra)))
    assert got.basis == "annual" and got.ebit == 200.0
    assert "annual fallback" in got.basis_note
    assert "jumps 184 days from 2025-06-30 to 2025-12-31" in got.basis_note
    assert "a quarter is missing" in got.basis_note


def test_a_nan_quarter_is_the_same_hole():
    """TRUE-B.ST's shape: the 2025-09-30 column is there and its revenue is
    NaN. A point with no value is absent from the four, and the neighbours
    it left show the jump."""
    ends = [date(2025, 3, 31), date(2025, 6, 30), date(2025, 9, 30),
            date(2025, 12, 31), date(2026, 3, 31), date(2026, 6, 30)]
    values = [(e, None if e == date(2025, 9, 30) else 50.0) for e in ends]
    extra = _quarters("TRUE-B.ST", TOI, values) + _quarters("TRUE-B.ST", "Gross Profit", values)
    got = extract_inputs("TRUE-B.ST", record("TRUE-B.ST", ebit=523.0, ebit_line=TOI,
                                             extra_lines=tuple(extra)))
    assert got.basis == "annual" and got.ebit == 523.0
    assert "a quarter is missing" in got.basis_note


def test_fewer_than_four_quarters_falls_back_and_counts_them():
    ends = [(date(2026, 3, 31), 50.0), (date(2026, 6, 30), 55.0)]
    extra = _quarters("X", TOI, ends) + _quarters("X", "Gross Profit", ends)
    got = extract_inputs("X", record("X", ebit_line=TOI, extra_lines=tuple(extra)))
    assert got.basis == "annual"
    assert "has 2 quarter(s) at the end of its history" in got.basis_note


def test_an_annual_figure_newer_than_the_quarterly_window_is_taken_over_it():
    ends = [(date(2024, 12, 31), 10.0), (date(2025, 3, 31), 10.0),
            (date(2025, 6, 30), 10.0), (date(2025, 9, 30), 10.0)]
    extra = _quarters("X", TOI, ends) + _quarters("X", "Gross Profit", ends)
    got = extract_inputs("X", record("X", ebit=100.0, ebit_line=TOI, extra_lines=tuple(extra)))
    assert got.basis == "annual" and got.ebit == 100.0 and got.ebit_period == YEAR
    assert "annual 2025-12-31 is newer than the quarterly window ending 2025-09-30" in got.basis_note


def test_quarters_only_with_a_hole_and_no_annual_are_still_input_missing():
    """The pre-item-8 rule, unchanged where there is nothing to fall back to."""
    ends = [(date(2025, 6, 30), 1.0), (date(2025, 12, 31), 1.0),
            (date(2026, 3, 31), 1.0), (date(2026, 6, 30), 1.0)]
    rec = record("X", ebit=None,
                 extra_lines=tuple(_quarters("X", TOI, ends)))
    got = extract_inputs("X", rec)
    assert got.ebit is None
    assert "a quarter is missing" in got.ebit_note


def test_a_denominator_absent_at_the_window_end_is_mixed_periods_never_the_newest():
    """TTM to 2026-03-31 with balance sheets at 2026-06-30 and 2025-12-31
    only: the newest is NOT taken. K6 refuses the pair, as it always has."""
    ends = [(date(2025, 6, 30), 10.0), (date(2025, 9, 30), 10.0),
            (date(2025, 12, 31), 10.0), (date(2026, 3, 31), 10.0)]
    extra = _quarters("X", TOI, ends) + _quarters("X", "Gross Profit", ends)
    extra.append(q("X", "Total Assets", date(2026, 6, 30), 500.0, "balance_quarterly", None))
    got = extract_inputs("X", record("X", ebit_line=TOI, extra_lines=tuple(extra)))
    assert got.basis == "ttm-4q" and got.ebit_period == date(2026, 3, 31)
    assert got.total_assets_period == date(2026, 6, 30)
    assert score(got, euro(), ASOF).quality_state == QUALITY_MIXED_PERIODS


# --- E46: investment companies are exempt on the quality leg by LIST ---------


def test_a_listed_investment_company_has_no_quality_leg_whatever_its_string():
    """Latour: vendor string Industrials, ranked at 263 on 2026-08-26 until
    E46. Listed, it keeps its yield and goes to the yield-only section --
    never written -- with its own reason, apart from the string exemption."""
    from vss.ranking import QUALITY_INVESTMENT

    listed = frozenset({"LATO-B.ST"})
    latour = score(extract_inputs("LATO-B.ST", record("LATO-B.ST", sector="Industrials")),
                   euro(), ASOF, listed)
    assert latour.quality_state == QUALITY_INVESTMENT
    assert latour.operating_profitability is None and latour.earnings_yield is not None
    lifco = score(extract_inputs("LIFCO-B.ST", record("LIFCO-B.ST", sector="Industrials")),
                  euro(), ASOF, listed)
    assert lifco.quality_state == QUALITY_OK, "an industrial with the same string is ranked"
    result = rank_candidates([Candidate("LATO-B.ST"), Candidate("LIFCO-B.ST")],
                             {"LATO-B.ST": record("LATO-B.ST", sector="Industrials"),
                              "LIFCO-B.ST": record("LIFCO-B.ST", sector="Industrials")},
                             euro(), ASOF, investment_companies=listed)
    assert [r.ticker for r in result.main] == ["LIFCO-B.ST"]
    assert [r.ticker for r in result.yield_only] == ["LATO-B.ST"]
    assert result.reason_counts()[QUALITY_INVESTMENT] == 1


def test_the_list_is_read_before_the_string_and_counted_apart():
    from vss.ranking import QUALITY_INVESTMENT

    investor = score(extract_inputs("INVE-B.ST", record("INVE-B.ST", sector="Financial Services")),
                     euro(), ASOF, frozenset({"INVE-B.ST"}))
    assert investor.quality_state == QUALITY_INVESTMENT
    bank = score(extract_inputs("HSBA.L", record("HSBA.L", sector="Financial Services")),
                 euro(), ASOF, frozenset({"INVE-B.ST"}))
    assert bank.quality_state == QUALITY_SECTOR
