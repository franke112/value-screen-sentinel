"""Hand-entered fundamentals: the schema, the four checks, and the gate.

Every fixture here is SYNTHETIC. No figure below was read from a real
report, and none may be: a test fixture that looks like a company's
accounts is a figure somebody eventually copies into a valuation.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from vss import ranking
from vss.manual import (
    FIELDS,
    FIELDS_BY_NAME,
    REFUSE_ZERO_DENOMINATOR,
    ZERO_NEEDS_BASIS,
    ZERO_REFUSED,
    capex_legs,
    QUALITY_BASIS_MISMATCH,
    SUBTRACTIONS,
    resolve_on_basis,
    section5_basis,
    newer_filed_periods,
    RATIO_MISSING,
    RATIO_MIXED_PERIODS,
    RATIO_OK,
    MANUAL_DIR,
    ORIGIN,
    STATUS_UNVERIFIED,
    STATUS_VERIFIED,
    TEMPLATE_PATH,
    ManualError,
    as_record,
    load_manual,
    parse_manual,
    ratio_states,
    render_report,
    run_manual,
    section5_gate,
    # E108's measured limb (2026-09-08): the gate's exemption is looked
    # up in this map, and the two must share a vocabulary.
    SENSITIVITY_FLOOR,
    registered_view_record,
    registered_view_sensitivity,
    subtracted_on_basis,
    # E113 (2026-09-08)
    NON_VALUATION_FIELDS,
    non_valuation_fields,
    staleness,
)
from vss.prices import STATUS_OK, STATUS_STALE
from vss.rules import VALID_SOURCES

AS_OF = date(2026, 8, 24)


def figure(value, *, status=STATUS_VERIFIED, page="1"):
    return {"value": value, "page": page, "status": status}


def zero_figure(*, zero_basis="caption"):
    """A stated zero on a field E25 makes name its evidence (E68's leg in
    every bridge fixture below: a company with no decommissioning line)."""
    return {"value": 0.0, "page": "1", "status": STATUS_VERIFIED,
            "zero_basis": zero_basis}


def market_figure(value, *, status=STATUS_VERIFIED):
    """A market figure has no period `document:` to inherit a source from."""
    return {"value": value, "page": "1", "status": status,
            "source": "exchange close"}


def document(periods=None, **overrides):
    """A file whose reporting_frequency FOLLOWS ITS PERIOD LABELS.

    Inferred rather than fixed because FRAMEWORK-EDITS E19 gave the default
    fixture a job: section 5 runs on ONE twelve-month basis, so a file with
    a single three-month entry has no basis and section 5 does not run.
    The default period below is therefore a YYYY-FY entry -- the year as
    filed, twelve months in one row -- and a test that wants quarters says
    so by passing them, which the inference then follows.
    """
    periods = periods if periods is not None else []
    kinds = {str(x.get("period", ""))[5:] for x in periods if isinstance(x, dict)}
    inferred = ("quarterly" if any(k.startswith("Q") for k in kinds)
                else "half_yearly" if kinds else "quarterly")
    doc = {
        "ticker": "TEST.XX",
        "name": "Test Company",
        "reporting_currency": "EUR",
        "quote_currency": "EUR",
        "sector": "Industrials",
        "reporting_frequency": inferred,
        "periods": periods,
        # E70 (2026-08-30): the fixture is an IFRS 16 shape -- the flow never
        # bore the lease principal -- so every older FCF0 test keeps its
        # meaning; a test about a US shape passes LEASES_YES.
        "operating_leases_in_ocf": LEASES_NO,
    }
    doc.update(overrides)
    return doc


LEASES_NO = {"value": False, "source": "IFRS 16.50(b)",
             "page": "TEST FIXTURE: principal in financing, the flow never bore it"}
LEASES_YES = {"value": True, "source": "ASC 842-20-45-5(a)",
              "page": "TEST FIXTURE: operating lease payments inside operating cash flow"}


def period(label="2025-FY", *, end="2025-12-31", figures=None, basis="calendar"):
    figures = dict(figures or {})
    # E117 (2026-09-19): the default fixture is an IFRS 16 filer, whose FCF0
    # DEDUCTS its principal and lease interest. A file with a flow states
    # both as NAMED ZEROS -- a company with no leases -- so every older FCF0
    # test keeps its arithmetic; a test about leases states them itself.
    if figures and "operating_cash_flow" in figures:
        figures.setdefault("lease_payments_capital", zero_figure())
        figures.setdefault("lease_interest_paid", zero_figure())
    return {
        "period": label,
        "period_end": end,
        "period_basis": basis,
        "document": "Interim report",
        "figures": figures,
    }


#: E34's block, in the two forms a file may carry it in.
INTEREST_NO = {"value": False, "source": "Interim report", "page": "17"}
INTEREST_YES = {"value": True, "source": "Interim report", "page": "17"}


def write(tmp_path: Path, doc, ticker="TEST.XX") -> Path:
    path = tmp_path / f"{ticker}.yaml"
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return path


def parse(doc, path=Path("memory.yaml")):
    return parse_manual(doc, path=path)



FOUR_Q = (("2025-Q3", "2025-09-30"), ("2025-Q4", "2025-12-31"),
          ("2026-Q1", "2026-03-31"), ("2026-Q2", "2026-06-30"))


def four_quarters(each=None, last=None, first=None):
    """Four consecutive quarters -- E19's TTM basis, ending 2026-06-30.

    `each` goes in every quarter (so a flow sums), `last` only in the
    newest (a stock at the window end), `first` only in the oldest.
    """
    entries = []
    for n, (label, end) in enumerate(FOUR_Q):
        figures = dict(each or {})
        if n == len(FOUR_Q) - 1:
            figures.update(last or {})
        if n == 0:
            figures.update(first or {})
        entries.append(period(label, end=end, figures=figures))
    return document(entries)


# --- the committed template ------------------------------------------------


def test_the_committed_template_loads_and_supplies_nothing():
    """The empty template is a VALID file, not a broken one.

    It is committed with no figures on purpose, so this is the case that
    proves an empty file loads rather than erroring -- and that it still
    refuses section 5, for having nothing to value.
    """
    parsed = load_manual("TEMPLATE", directory=MANUAL_DIR)
    assert not [f for f in parsed.all_figures() if f.present]
    assert parsed.unverified() == ()

    gate = section5_gate(parsed, as_of=AS_OF)
    assert gate.refused
    assert [r.kind for r in gate.refusals] == ["NO PERIODS"]


def test_the_template_is_where_the_loader_says_it_is():
    assert TEMPLATE_PATH.exists(), "the schema's own template must be committed"


def test_running_the_command_on_the_empty_template_exits_refused():
    code, report = run_manual(ticker="TEMPLATE", as_of=AS_OF, directory=MANUAL_DIR)
    assert code == 1
    assert "SECTION 5 IS REFUSED" in report
    assert "DATA MISSING" in report


# --- the schema ------------------------------------------------------------


def test_an_unknown_figure_name_fails_the_load():
    """The schema carries what the code reads. Nothing else gets in."""
    doc = document([period(figures={"ebit_margin_adjusted": figure(0.1)})])
    with pytest.raises(ManualError, match="unknown figure"):
        parse(doc)


def test_an_unknown_top_level_key_fails_the_load():
    with pytest.raises(ManualError, match="unknown key"):
        parse(document(peer_group=["A", "B"]))


def test_a_bare_number_is_not_a_figure():
    """`revenue: 1234` carries no page and no status, so it is refused."""
    doc = document([period(figures={"revenue": 1234})])
    with pytest.raises(ManualError, match="must be a mapping"):
        parse(doc)


def test_a_value_without_a_page_fails_the_load():
    doc = document([period(figures={"revenue": figure(1234, page=None)})])
    with pytest.raises(ManualError, match="no page reference"):
        parse(doc)


def test_a_value_without_any_source_fails_the_load():
    entry = period(figures={"revenue": figure(1234)})
    del entry["document"]
    with pytest.raises(ManualError, match="no source"):
        parse(document([entry]))


def test_the_period_document_is_the_default_source_for_its_figures():
    parsed = parse(document([period(figures={"revenue": figure(1234)})]))
    assert parsed.periods[0].figures["revenue"].source == "Interim report"


def test_a_figure_may_name_its_own_source_instead():
    entry = period(figures={"revenue": {"value": 1234, "page": "7",
                                        "status": STATUS_VERIFIED,
                                        "source": "Annual Report 2025"}})
    parsed = parse(document([entry]))
    assert parsed.periods[0].figures["revenue"].source == "Annual Report 2025"


def test_an_unknown_status_fails_the_load():
    doc = document([period(figures={"revenue": figure(1, status="PROBABLY")})])
    with pytest.raises(ManualError, match="status must be one of"):
        parse(doc)


def test_a_figure_is_unverified_unless_it_says_otherwise():
    doc = document([period(figures={"revenue": {"value": 1, "page": "1"}})])
    parsed = parse(doc)
    assert parsed.periods[0].figures["revenue"].status == STATUS_UNVERIFIED


def test_the_empty_template_needs_no_currency_but_a_figure_does():
    """Three placeholder strings in a committed template is fake data.

    So currency is demanded at the point where not knowing it matters --
    the moment a figure carries a value -- and not before.
    """
    parse(document(reporting_currency="", quote_currency="", sector=""))

    with pytest.raises(ManualError, match="reporting_currency is not stated"):
        parse(document([period(figures={"revenue": figure(1)})],
                       reporting_currency=""))


def test_a_market_figure_needs_the_quote_currency_and_a_date():
    with pytest.raises(ManualError, match="quote_currency is not stated"):
        parse(document(quote_currency="",
                       market={"as_of": "2026-08-21",
                               "enterprise_value": market_figure(100)}))
    with pytest.raises(ManualError, match="as_of is required"):
        parse(document(market={"enterprise_value": market_figure(100)}))


def test_a_market_figure_must_name_its_own_source():
    """There is no period `document:` above it to inherit one from."""
    with pytest.raises(ManualError, match="no `document:` to fall back on"):
        parse(document(market={"as_of": "2026-08-21",
                               "enterprise_value": figure(100)}))


# --- period labels ---------------------------------------------------------


def test_a_half_year_label_is_refused_on_a_quarterly_ticker():
    with pytest.raises(ManualError, match="stores Q1/Q2/Q3/Q4 periods only"):
        parse(document([period("2025-H1", end="2025-06-30")],
                       reporting_frequency="quarterly"))


def test_a_half_yearly_ticker_stores_half_years():
    parsed = parse(document([period("2025-H1", end="2025-06-30")],
                            reporting_frequency="half_yearly"))
    assert parsed.periods[0].period == "2025-H1"


def test_two_periods_may_not_cover_the_same_month():
    doc = document([period("2025-H1", end="2025-06-30"),
                    period("2025-FY", end="2025-12-31")],
                   reporting_frequency="half_yearly")
    with pytest.raises(ManualError, match="overlap"):
        parse(doc)


def test_periods_must_be_listed_oldest_first():
    doc = document([period("2025-Q4", end="2025-12-31"),
                    period("2025-Q3", end="2025-09-30")])
    with pytest.raises(ManualError, match="oldest first"):
        parse(doc)


def test_period_end_is_required_because_stale_is_measured_on_it():
    entry = period()
    del entry["period_end"]
    with pytest.raises(ManualError, match="period_end is required"):
        parse(document([entry]))


def test_a_calendar_period_end_must_fall_inside_its_label():
    doc = document([period("2025-Q1", end="2025-05-03", basis="calendar")])
    with pytest.raises(ManualError, match="falls outside"):
        parse(doc)


def test_a_fiscal_period_end_is_not_held_to_the_calendar_span():
    """Backlog B-3's trap, from the other side.

    A 52/53-week retail filer's fiscal Q1 ends in May. Holding a FISCAL
    label to the calendar months would reject a correct entry.
    """
    parsed = parse(document([period("2026-Q1", end="2026-05-03", basis="fiscal")]))
    assert parsed.periods[0].period_end == date(2026, 5, 3)


def test_a_file_may_not_mix_fiscal_and_calendar_periods():
    doc = document([period("2025-Q3", end="2025-09-30", basis="fiscal"),
                    period("2025-Q4", end="2025-12-31", basis="calendar")])
    with pytest.raises(ManualError, match="mix period_basis"):
        parse(doc)


# --- check 1: the unit -----------------------------------------------------


def test_a_percentage_where_a_fraction_belongs_fails_the_load():
    """6.6 is six hundred and sixty per cent. It is a unit error, not a value."""
    doc = document([period(figures={"op_margin": figure(6.6)})])
    with pytest.raises(ManualError, match="outside the plausible band"):
        parse(doc)


def test_E79_an_operating_income_with_no_margin_beside_it_loads():
    """E79: where the issuer states no margin the check has nothing to
    compare and does not fire (Norsk Hydro states none anywhere)."""
    parsed = parse(document([period(figures={"revenue": figure(1000),
                                             "operating_income": figure(66)})]))
    assert parsed.periods[0].value("operating_income") == 66


def test_E79_a_whole_percent_margin_is_compared_at_a_whole_percent():
    parsed = parse(document([period(figures={"revenue": figure(425129),
                                             "operating_income": figure(287874),
                                             "op_margin": figure(0.68)})]))
    assert parsed.periods[0].value("op_margin") == 0.68
    with pytest.raises(ManualError, match="stated to a whole percent"):
        parse(document([period(figures={"revenue": figure(425129),
                                        "operating_income": figure(287874),
                                        "op_margin": figure(0.67)})]))


def test_the_margin_must_agree_with_the_two_lines_it_reconciles():
    doc = document([period(figures={"revenue": figure(1000),
                                    "operating_income": figure(66),
                                    "op_margin": figure(0.12)})])
    with pytest.raises(ManualError, match="do not describe one measure"):
        parse(doc)


def test_a_reconciled_period_loads():
    parsed = parse(document([period(figures={"revenue": figure(1000),
                                             "operating_income": figure(66),
                                             "op_margin": figure(0.066)})]))
    assert parsed.periods[0].value("op_margin") == pytest.approx(0.066)


def test_the_manual_path_is_not_given_the_xbrl_reconciliation_exemption():
    """A tag says which line an operating income is. A pair of eyes does not.

    `config.unit_problem` waives the reconciliation for `source: xbrl`.
    Nothing on this path may set that key, or the check that exists to
    catch NIKE's income-before-taxes recorded as operating income would
    be switched off for the one source that most needs it.
    """
    import inspect

    from vss import manual

    body = inspect.getsource(manual._check_units)
    assert '"source"' not in body and "'source'" not in body


def test_manual_is_a_recognised_quarter_source_and_the_check_is_the_same_one():
    from vss.config import unit_problem

    assert "manual" in VALID_SOURCES
    # E79: no margin, nothing to compare; a disagreeing margin still refuses.
    assert unit_problem({"revenue": 1000, "op_income": 66, "op_margin": None,
                         "source": "manual"}) is None
    problem = unit_problem({"revenue": 1000, "op_income": 66, "op_margin": 0.12,
                            "source": "manual"})
    assert problem is not None and "do not describe one measure" in problem


# --- check 2: one unit across the whole file -------------------------------


def test_a_thousandfold_jump_between_periods_is_a_unit_mix():
    doc = document([period("2025-Q3", end="2025-09-30",
                           figures={"revenue": figure(1_000)}),
                    period("2025-Q4", end="2025-12-31",
                           figures={"revenue": figure(1_100_000)})])
    with pytest.raises(ManualError, match="UNIT MIX"):
        parse(doc)


def test_a_normal_seasonal_swing_is_not_a_unit_mix():
    parsed = parse(document([
        period("2025-Q3", end="2025-09-30", figures={"revenue": figure(1_000)}),
        period("2025-Q4", end="2025-12-31", figures={"revenue": figure(1_800)}),
    ]))
    assert len(parsed.periods) == 2


# --- check 3: STALE --------------------------------------------------------


def test_accounts_older_than_the_limit_are_stale_not_broken():
    """E19: the basis is a window, and a window is as old as the day it
    STOPS. One date, rather than a scan over whichever rows were read."""
    parsed = parse(document([period("2023-FY", end="2023-12-31",
                                    figures={"revenue": figure(1000)})]))
    status, detail = staleness(parsed, as_of=AS_OF)
    assert status == STATUS_STALE
    assert "2023-12-31" in detail

    gate = section5_gate(parsed, as_of=AS_OF)
    stale = [r for r in gate.refusals if r.kind == "STALE"]
    assert stale and "2023-FY" in stale[0].detail


def test_recent_accounts_are_not_stale():
    parsed = parse(document([period(figures={"revenue": figure(1000)})]))
    assert staleness(parsed, as_of=AS_OF)[0] == STATUS_OK


def test_staleness_reaches_the_record_the_ranking_key_reads():
    parsed = parse(document([period("2023-Q4", end="2023-12-31",
                                    figures={"revenue": figure(1000)})]))
    record = as_record(parsed, as_of=AS_OF)
    assert record.status == STATUS_STALE


# --- check 4: one fiscal period per ratio ----------------------------------


def test_a_ratio_whose_legs_sit_in_two_periods_is_data_missing():
    """The E6 quality leg's rule, applied to every ratio section 5 forms.

    Operating profit from one year over total assets from another is not a
    ratio, and the figure that would come out of it is about nothing.
    """
    parsed = parse(four_quarters(last={"total_assets": figure(5_000)},
                                 first={"operating_income": figure(400)}))
    states = {s.name: s for s in ratio_states(parsed)}
    quality = states["operating profitability"]
    assert not quality.computable
    assert quality.state == RATIO_MISSING
    # Three quarters of four is not a year, and the missing one is not zero.
    assert "operating_income is not on the basis" in quality.detail


def test_a_ratio_with_every_leg_on_the_basis_is_computable():
    doc = document([period(figures={"operating_income": figure(400),
                                    "total_assets": figure(5_000)})])
    states = {s.name: s for s in ratio_states(parse(doc))}
    assert states["operating profitability"].computable
    assert states["operating profitability"].period == "2025-FY"


def test_a_flow_is_summed_over_the_window_and_a_stock_taken_at_its_end():
    """E19, in one fixture: operating profit four times over, total assets once."""
    parsed = parse(four_quarters(each={"operating_income": figure(400)},
                                 last={"total_assets": figure(5_000)}))
    basis = section5_basis(parsed)
    assert basis.kind == "ttm" and basis.end == date(2026, 6, 30)
    assert resolve_on_basis(parsed, basis, "operating_income").value == 1_600.0
    assert resolve_on_basis(parsed, basis, "total_assets").value == 5_000.0
    assert states_of(parsed)["operating profitability"].computable


def states_of(parsed):
    return {s.name: s for s in ratio_states(parsed)}


def test_a_ratio_the_newest_period_lacks_is_not_taken_from_an_older_one():
    """Both legs sit together in an OLDER period; the newest is complete
    for one leg only. The newest complete period is the one used -- and
    where none is complete, the ratio is DATA MISSING rather than mixed."""
    parsed = parse(document([
        period("2025-Q3", end="2025-09-30", figures={"operating_income": figure(380),
                                                     "total_assets": figure(4_900)}),
        period("2025-Q4", end="2025-12-31", figures={"operating_income": figure(400)}),
    ]))
    # Two quarters is not a basis at all under E19, so nothing is formed
    # from an older complete period either.
    states = {s.name: s for s in ratio_states(parsed)}
    assert states["operating profitability"].state == RATIO_MISSING
    assert "no twelve-month basis" in states["operating profitability"].detail


# --- the gate --------------------------------------------------------------


def test_section_5_refuses_on_a_single_unverified_figure():
    """One figure the BASIS READS is enough to refuse (E21)."""
    # E113 (2026-09-08): the field was `ebitda` until fv_base's own
    # non-readers stopped blocking. The SUBJECT of this test is E21 -- one
    # figure the basis reads refuses -- so it now uses a leg the valuation
    # actually reads, and says the same thing it always did.
    doc = document([period(figures={
        "revenue": figure(1000),
        "operating_cash_flow": figure(80, status=STATUS_UNVERIFIED),
    })])
    gate = section5_gate(parse(doc), as_of=AS_OF)
    assert gate.refused
    unverified = [r for r in gate.refusals if r.kind == "UNVERIFIED"]
    assert len(unverified) == 1
    assert "2025-FY operating_cash_flow" == unverified[0].subject
    assert "READS it" in unverified[0].detail


def test_an_unverified_figure_section_5_never_reads_does_not_refuse():
    """E21: `op_margin` is a check field and no method of section 5 touches
    it. It is NAMED and does not block -- the shape E7 gave the ranking key.

    This is the case the old rule refused on, and the reason it gave --
    a half-checked file is one the reader audits by hand -- is kept for
    the figures a run reads and does not reach the figures it cannot.
    """
    doc = document([period(figures={
        "revenue": figure(1000),
        "operating_income": figure(66),
        "op_margin": figure(0.066, status=STATUS_UNVERIFIED),
    })])
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert not gate.refused
    assert [f.name for f in parsed.unverified()] == ["op_margin"]
    assert gate.blocking == ()
    assert [f.name for f, _ in gate.unread] == ["op_margin"]
    assert "does not read `op_margin`" in gate.unread[0][1]
    report = render_report(parsed, gate)
    assert "## UNVERIFIED, AND NOT READ AT THIS BASIS" in report
    assert "`2025-FY` `op_margin`" in report


FIVE_Q = (("2025-Q2", "2025-06-30"),) + FOUR_Q


def five_quarters(oldest=None, each=None):
    """Five consecutive quarters: the basis takes the newest FOUR, so the
    oldest is in the file and outside the window (E21)."""
    entries = []
    for n, (label, end) in enumerate(FIVE_Q):
        figures = dict(each or {})
        if n == 0:
            figures.update(oldest or {})
        entries.append(period(label, end=end, figures=figures))
    return document(entries)


def test_an_unverified_figure_OUTSIDE_the_window_does_not_refuse():
    """E21, measured on PNDORA.CO's shape: 186 of its 238 sat in quarters
    the window does not reach, where they cannot move a number section 5
    produces. Requiring them was work that bought nothing."""
    parsed = parse(five_quarters(
        oldest={"ebitda": figure(999, status=STATUS_UNVERIFIED)},
        each={"ebitda": figure(2000)}))
    gate = section5_gate(parsed, as_of=AS_OF)
    assert not gate.refused and gate.blocking == ()
    assert len(parsed.unverified()) == 1
    figure_, why = gate.unread[0]
    assert figure_.period == "2025-Q2"
    assert "not in the basis window" in why
    assert "`2025-Q2` `ebitda`" in render_report(parsed, gate)


def test_a_stock_from_an_older_window_quarter_is_not_read_and_does_not_block():
    """A stock is taken at the window's END (E19), so an unverified one in
    an earlier quarter OF the window is not read either -- E21 gates on
    what the resolver takes, not on which quarter a figure sits in."""
    doc = four_quarters(
        each={"ebitda": figure(2000)},
        last={"cash_and_equivalents": figure(900)})
    doc["periods"][0]["figures"]["cash_and_equivalents"] = figure(
        700, status=STATUS_UNVERIFIED)
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert not gate.refused
    assert "at the window's END" in gate.unread[0][1]


def test_the_same_flags_give_a_different_answer_on_a_different_basis():
    """E21 condition 3, and why the basis is printed every time: the file
    and its flags are unchanged and the verdict is not."""
    # E113 (2026-09-08): the field was `ebitda` until fv_base's own
    # non-readers stopped blocking. The subject here is E21 condition 3 --
    # a sliding window changes the verdict on an unchanged file -- so the
    # field is now one the valuation reads and the point is untouched.
    # `sbc` rather than `operating_cash_flow`: both are legs E113 must keep
    # refusing on, but an OCF with no `interest_in_ocf` block trips E34's
    # own INTEREST UNCLASSIFIED refusal and would test that instead.
    leg = "sbc"
    unread = parse(five_quarters(
        oldest={leg: figure(999, status=STATUS_UNVERIFIED)},
        each={leg: figure(2000)}))
    assert not section5_gate(unread, as_of=AS_OF).refused

    # the same five entries less the newest: the window slides BACK onto
    # the unverified quarter, which now refuses.
    doc = five_quarters(oldest={leg: figure(999, status=STATUS_UNVERIFIED)},
                        each={leg: figure(2000)})
    doc["periods"] = doc["periods"][:-1]
    slid = parse(doc)
    gate = section5_gate(slid, as_of=AS_OF)
    assert gate.refused
    assert [r.subject for r in gate.refusals] == [f"2025-Q2 {leg}"]
    # and BOTH reports say which window the answer stands on
    for parsed_, g in ((unread, section5_gate(unread, as_of=AS_OF)),
                       (slid, gate)):
        assert "VERIFICATION TESTED AGAINST THE BASIS" in render_report(parsed_, g)
        assert "A DIFFERENT BASIS TESTS A DIFFERENT SET" in render_report(parsed_, g)


def test_an_unverified_MARKET_figure_blocks_though_no_basis_reads_it():
    """E21 draws its line at what a run can be wrong about, not at the word
    "reads". A market figure belongs to a DATE rather than to the window, so
    no basis reads it in the resolver's sense, and section 5 divides it into
    its own results all the same."""
    doc = four_quarters(each={"ebitda": figure(2000)})
    doc["market"] = {"as_of": AS_OF.isoformat(),
                     "market_cap": market_figure(50_000,
                                                 status=STATUS_UNVERIFIED)}
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert gate.refused
    assert [f.name for f in gate.blocking] == ["market_cap"]
    assert gate.unread == ()


def test_the_gate_writes_no_status_back_and_a_flag_survives_the_window():
    """E21 condition 2: verification is a property of the FIGURE, not of
    the run. A quarter that leaves the window keeps its flags and is never
    re-verified when it returns."""
    doc = five_quarters(oldest={"ebitda": figure(999)},  # VERIFIED, outside
                        each={"ebitda": figure(2000)})
    parsed = parse(doc)
    before = {(f.period, f.name): f.status for f in parsed.all_figures()}
    section5_gate(parsed, as_of=AS_OF)
    after = {(f.period, f.name): f.status for f in parsed.all_figures()}
    assert before == after
    assert all(f.verified for f in parsed.all_figures() if f.present)
    assert parsed.unverified() == ()



def test_an_unverified_figure_is_named_not_hidden():
    """UNVERIFIED is not the same state as absent. The refusal names the
    page to go and read, or the flag gives no way to clear it."""
    # E113 (2026-09-08): the field was `revenue`. The subject is that an
    # UNVERIFIED figure NAMES ITS PAGE rather than being hidden, so the
    # field is now one the valuation reads. Note that E113 does not weaken
    # this even for the exempted fields: an exempted figure still carries
    # its page, printed on the flag instead of on the refusal.
    doc = document([period(figures={
        "operating_cash_flow": {"value": 1234.0, "page": "12",
                                "status": STATUS_UNVERIFIED,
                                "source": "Q4 report"},
    })])
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=AS_OF)
    detail = [r for r in gate.refusals if r.kind == "UNVERIFIED"][0].detail
    assert "Q4 report" in detail and "[12]" in detail
    assert "operating_cash_flow" not in gate.missing


def test_an_absent_figure_is_data_missing_and_not_an_unverified_one():
    parsed = parse(document([period(figures={"revenue": figure(1000)})]))
    assert "gross_profit" in parsed.missing()
    assert [f.name for f in parsed.unverified()] == []


def test_a_fully_verified_recent_complete_file_lets_section_5_run():
    """COMPLETE now includes E34's `interest_in_ocf`: a file that does not
    say where its filer books interest has no FCF0 to discount."""
    figures = {name: figure(1.0) for name in ("gross_profit", "total_assets",
                                              "operating_cash_flow", "capex_ppe",
                                              "capex_intangibles", "ebitda",
                                              "financial_liabilities_current",
                                              "financial_liabilities_noncurrent",
                                              "cash_and_equivalents",
                                              "free_cash_flow_reported",
                                              "sbc", "net_income")}
    figures["revenue"] = figure(1000.0)
    figures["operating_income"] = figure(66.0)
    figures["op_margin"] = figure(0.066)
    doc = document([period(figures=figures)], interest_in_ocf=INTEREST_NO)
    gate = section5_gate(parse(doc), as_of=AS_OF)
    assert not gate.refused, [r.detail for r in gate.refusals]


# --- the record, and the origin -------------------------------------------


def test_the_record_speaks_the_stores_own_line_names():
    """The whole prize: `ranking.py` runs unchanged on a manual record.

    A parallel vocabulary would make `record.latest("Gross Profit")`
    return None for every manual name with no error raised anywhere.
    """
    doc = document([period(figures={"revenue": figure(1000),
                                    "operating_income": figure(66),
                                    "op_margin": figure(0.066),
                                    "gross_profit": figure(400),
                                    "total_assets": figure(5_000),
                                    "net_ppe": figure(900)})],
                   market={"as_of": "2026-08-21",
                           "enterprise_value": market_figure(9_000),
                           "market_cap": market_figure(7_500)})
    record = as_record(parse(doc), as_of=AS_OF)

    assert record.latest("Gross Profit") == (date(2025, 12, 31), 400.0)
    assert record.latest("Total Assets") == (date(2025, 12, 31), 5_000.0)
    assert record.latest(*ranking.EBIT_ALIASES) == (date(2025, 12, 31), 66.0)
    assert record.value("enterpriseValue") == 9_000.0
    assert record.value("marketCap") == 7_500.0
    assert record.text("financialCurrency") == "EUR"
    assert record.text("sector") == "Industrials"


def quarterly(*quarters):
    """A file of consecutive quarters, oldest first. Figures scale with n."""
    entries = []
    for n, (label, end) in enumerate(quarters, start=1):
        entries.append(period(label, end=end, figures={
            "revenue": figure(1000 * n), "operating_income": figure(66 * n),
            "op_margin": figure(0.066), "gross_profit": figure(400 * n),
            "total_assets": figure(5_000 + n)}))
    return document(entries, market={"as_of": "2026-08-21",
                                     "enterprise_value": market_figure(1_000),
                                     "market_cap": market_figure(800)})


FOUR_QUARTERS = (("2025-Q3", "2025-09-30"), ("2025-Q4", "2025-12-31"),
                 ("2026-Q1", "2026-03-31"), ("2026-Q2", "2026-06-30"))


def test_the_ranking_key_scores_a_manual_record_without_changing_ranking_py():
    """FRAMEWORK-EDITS E13: flows summed over four quarters, stocks at the end."""
    record = as_record(parse(quarterly(*FOUR_QUARTERS)), as_of=AS_OF)
    inputs = ranking.extract_inputs("TEST.XX", record)

    assert inputs.ebit == 66.0 * (1 + 2 + 3 + 4)
    assert inputs.total_assets == 5_004.0, "a stock line takes the latest end"
    assert inputs.ebit_label == "Total Operating Income As Reported"
    assert inputs.basis == "ttm-4q"
    assert inputs.basis_periods == (date(2025, 9, 30), date(2025, 12, 31),
                                    date(2026, 3, 31), date(2026, 6, 30))
    assert inputs.quality_periods_agree is True


def test_a_manual_file_of_fewer_than_four_quarters_is_not_ranked():
    """E13: INPUT MISSING. Three quarters are not a trailing twelve months,
    and summing them anyway would be a figure about a window nobody named."""
    record = as_record(parse(quarterly(*FOUR_QUARTERS[1:])), as_of=AS_OF)
    inputs = ranking.extract_inputs("TEST.XX", record)
    assert inputs.ebit is None
    assert "3 quarter(s)" in inputs.basis_note
    assert ranking.score(inputs, ranking.FxTable(), AS_OF).quality_state \
        == ranking.QUALITY_MISSING


def test_a_manual_file_of_annual_periods_is_ranked_with_no_summing():
    """The escape hatch: a YYYY-FY period IS twelve months already."""
    doc = document([period("2025-FY", end="2025-12-31", figures={
        "revenue": figure(1000), "operating_income": figure(66),
        "op_margin": figure(0.066), "gross_profit": figure(400),
        "total_assets": figure(5_000)})], reporting_frequency="half_yearly")
    inputs = ranking.extract_inputs(
        "TEST.XX", as_record(parse(doc), as_of=AS_OF))
    assert inputs.ebit == 66.0
    assert inputs.basis == "annual"
    assert inputs.basis_periods == ()


def test_the_origin_rides_on_the_record_and_into_the_ranking_inputs():
    parsed = parse(document([period(figures={"revenue": figure(1000)})]))
    record = as_record(parsed, as_of=AS_OF)
    assert record.origin == ORIGIN == "manual"
    assert ranking.extract_inputs("TEST.XX", record).origin == "manual"


def test_a_vendor_record_still_reads_as_the_vendor():
    """The default must not move. Every stored run was a vendor run."""
    from vss.fundamentals import TickerFundamentals

    record = TickerFundamentals("X", STATUS_OK, 1, 3)
    assert record.origin == "yfinance"
    assert ranking.extract_inputs("X", record).origin == "yfinance"


def test_the_ranking_csv_carries_the_origin_column():
    from vss.screen import RANK_COLUMNS

    assert "origin" in RANK_COLUMNS


def test_the_report_states_the_origin_on_every_entered_figure():
    doc = document([period(figures={"revenue": figure(1000)})])
    parsed = parse(doc)
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "**ORIGIN: manual.**" in report
    assert report.count("`manual`") >= 2


# --- loading from disk -----------------------------------------------------


def test_a_missing_file_says_where_to_put_one(tmp_path):
    with pytest.raises(ManualError, match="no manual file at"):
        load_manual("NOPE.XX", directory=tmp_path)


def test_the_file_name_and_the_ticker_inside_it_must_agree(tmp_path):
    write(tmp_path, document(ticker="OTHER.XX"), ticker="TEST.XX")
    with pytest.raises(ManualError, match="names ticker"):
        load_manual("TEST.XX", directory=tmp_path)


def test_malformed_yaml_fails_the_load_loudly(tmp_path):
    (tmp_path / "TEST.XX.yaml").write_text("ticker: [unclosed", encoding="utf-8")
    with pytest.raises(ManualError, match="not valid YAML"):
        load_manual("TEST.XX", directory=tmp_path)


def test_every_schema_field_says_what_reads_it():
    """A field nothing reads is a wish, and this schema does not carry wishes."""
    for spec in FIELDS_BY_NAME.values():
        assert spec.reads, f"{spec.name} names no consumer"


# --- what section 5 may and may not be refused for -------------------------


def test_a_missing_leg_is_data_missing_and_does_not_refuse_section_5():
    """An absent line is the ordinary third state, not a fault.

    A company with no lease liabilities has none to report, and a fortress
    balance sheet is what section 5.3 tier 1 rewards. Refusing on it would
    make the gate fire hardest on the names the framework likes best.
    """
    doc = document([period(figures={"revenue": figure(1000),
                                    "operating_income": figure(66),
                                    "op_margin": figure(0.066)})])
    parsed = parse(doc)
    states = {s.name: s for s in ratio_states(parsed)}
    assert states["net debt"].state == RATIO_MISSING
    assert "is not on the basis" in states["net debt"].detail

    gate = section5_gate(parsed, as_of=AS_OF)
    assert not any(r.kind == "PERIODS DO NOT MATCH" for r in gate.refusals)
    assert not gate.refused, [r.detail for r in gate.refusals]


def test_a_leg_of_another_twelve_months_refuses_section_5():
    """Under E19 `periods do not match` means exactly one thing: an annual
    entry whose window ends elsewhere than the basis."""
    doc = with_annual(
        annual_entry(2024, "2024-12-31", net_income=figure(80)),
        periods=[period(figures={"free_cash_flow_reported": figure(90)})])
    gate = section5_gate(parse(doc), as_of=AS_OF)
    mixed = [r for r in gate.refusals if r.kind == "PERIODS DO NOT MATCH"]
    assert [r.subject for r in mixed] == ["FCF conversion"]
    assert "another twelve months" in mixed[0].detail


def test_a_bank_is_not_barred_from_section_5_by_the_ranking_keys_leg():
    """E6 exempts Financial Services from the quality leg BY DESIGN.

    The ranking key's quality leg (E43: EBIT / total assets) computes for a
    bank and is still not the concept its accounts present, which is why
    E6 exempts it. Gating section 5 on it would refuse every bank and every
    property company permanently, for a ratio no method of section 5 reads
    -- so it is REPORTED and never refused on, whatever its state.
    """
    doc = document([
        period(figures={"total_assets": figure(9_000), "revenue": figure(1000),
                        "operating_income": figure(66), "op_margin": figure(0.066)}),
    ], sector="Financial Services")
    parsed = parse(doc)
    states = {s.name: s for s in ratio_states(parsed)}
    assert "operating profitability" in states
    assert not section5_gate(parsed, as_of=AS_OF).refused
    bare = parse(document([period(figures={"revenue": figure(1000),
                                           "op_margin": figure(0.066)})],
                          sector="Financial Services"))
    assert {s.name: s for s in ratio_states(bare)}["operating profitability"].state \
        == RATIO_MISSING
    assert not section5_gate(bare, as_of=AS_OF).refused


def test_the_quality_legs_split_periods_are_reported_never_refused():
    """Even when the ranking key's two lines DO sit apart, section 5 stands.

    It is reported in the ratio table -- the owner still sees it -- and it
    is the ranking key's own business, which ranking.py already answers
    with QUALITY_MIXED_PERIODS.
    """
    parsed = parse(with_annual(
        annual_entry(2024, "2024-12-31", total_assets=figure(9_000)),
        periods=[period(figures={"revenue": figure(1000),
                                 "operating_income": figure(66),
                                 "op_margin": figure(0.066)})]))
    states = {s.name: s for s in ratio_states(parsed)}
    assert states["operating profitability"].state == RATIO_MIXED_PERIODS
    assert not any(r.subject == "operating profitability"
                   for r in section5_gate(parsed, as_of=AS_OF).refusals)


def test_a_period_carrying_only_a_ranking_line_cannot_make_an_old_file_fresh():
    """SHL.DE's shape, in a hand-entered file.

    ranking.py rule 5 spends a paragraph on it: `newest_period` is the MAX
    over every stored row, so a row no leg reads decides the age. Here the
    2026 entry carries `net_ppe` alone -- a fingerprint line, read by no
    method of section 5 -- while every figure section 5 would hand over
    comes out of 2023.
    """
    parsed = parse(document([
        period("2023-FY", end="2023-12-31", figures={"revenue": figure(1000),
                                                     "operating_income": figure(66),
                                                     "op_margin": figure(0.066)}),
    ]))
    # The file-level answer, which is fundamentals.py's: the newest entry.
    assert staleness(parsed, as_of=AS_OF)[0] == STATUS_STALE

    # The gate's answer, measured on the BASIS, which is where E19 put it.
    gate = section5_gate(parsed, as_of=AS_OF)
    assert gate.basis.end == date(2023, 12, 31)
    stale = [r for r in gate.refusals if r.kind == "STALE"]
    assert stale and "2023-12-31" in stale[0].detail


def test_a_stale_priced_figure_refuses_section_5():
    """BWY.L: an EBIT from 2024 divided into an enterprise value from 2026."""
    doc = document([period(figures={"revenue": figure(1000)})],
                   market={"as_of": "2026-01-05",
                           "enterprise_value": market_figure(9_000)})
    gate = section5_gate(parse(doc), as_of=AS_OF)
    priced = [r for r in gate.refusals if r.kind == "PRICED FIGURE STALE"]
    assert priced and "2026-01-05" in priced[0].detail


def test_a_freshly_priced_figure_does_not():
    doc = document([period(figures={"revenue": figure(1000)})],
                   market={"as_of": "2026-08-22",
                           "enterprise_value": market_figure(9_000)})
    gate = section5_gate(parse(doc), as_of=AS_OF)
    assert not [r for r in gate.refusals if r.kind == "PRICED FIGURE STALE"]


def test_the_section_5_field_set_is_read_off_the_schema_not_listed_twice():
    from vss.manual import SECTION5_FIELDS

    assert "diluted_eps" in SECTION5_FIELDS
    assert "net_ppe" not in SECTION5_FIELDS, "net PPE is a ranking-key line only"
    assert "gross_profit" not in SECTION5_FIELDS


# --- E13's exception is confined to the ranking key -------------------------



def test_the_ttm_sum_now_reaches_section_5_and_is_still_written_nowhere():
    """FRAMEWORK-EDITS E19 SUPERSEDED E13's clause confining the TTM to the
    ranking key: section 5 reads a twelve-month window too. The limit that
    stayed is the one that matters -- nothing is written back."""
    parsed = parse(four_quarters(each={"revenue": figure(1000)}))
    basis = section5_basis(parsed)
    assert basis.kind == "ttm"
    assert resolve_on_basis(parsed, basis, "revenue").value == 4000.0
    # ... and every entry still holds exactly what was filed.
    assert [x.value("revenue") for x in parsed.periods] == [1000.0] * 4


def test_no_summed_figure_is_ever_written_to_a_manual_file():
    """The per-period figures stay exactly as filed. Asserted structurally:
    neither writer imports the basis machinery, so neither can use it."""
    import inspect

    from vss import appendix, manual

    for module in (manual, appendix):
        body = inspect.getsource(module)
        assert "flow_figure" not in body, module.__name__
        assert "BASIS_TTM" not in body, module.__name__


# --- E15: the annual: block ------------------------------------------------


def annual_entry(year=2025, end="2025-12-31", **figures):
    return {"fiscal_year": year, "period_end": end,
            "document": "Annual Report 2025", "figures": figures}


def with_annual(*entries, periods=None, **overrides):
    doc = document(periods if periods is not None else [], **overrides)
    doc["annual"] = list(entries)
    return doc


def test_a_file_may_carry_an_annual_block_beside_periods():
    parsed = parse(with_annual(
        annual_entry(diluted_eps=figure(67.9),
                     shares_outstanding_period_end=figure(79_000_000)),
        periods=[period(figures={"revenue": figure(1000)})]))
    assert len(parsed.periods) == 1 and len(parsed.annual) == 1
    entry = parsed.annual[0]
    assert entry.fiscal_year == 2025 and entry.period_end == date(2025, 12, 31)
    assert entry.value("diluted_eps") == 67.9


def test_an_annual_entry_carries_the_same_shape_a_period_entry_does():
    parsed = parse(with_annual(annual_entry(
        diluted_eps={"value": 67.9, "page": "note 4.2, p.131",
                     "status": STATUS_VERIFIED, "source": "Annual Report 2025"})))
    f = parsed.annual[0].figures["diluted_eps"]
    assert (f.value, f.page, f.status, f.source) == (
        67.9, "note 4.2, p.131", STATUS_VERIFIED, "Annual Report 2025")


def test_an_annual_figure_still_needs_a_page():
    with pytest.raises(ManualError, match="no page reference"):
        parse(with_annual(annual_entry(diluted_eps=figure(67.9, page=None))))


def test_fiscal_year_and_period_end_are_both_required():
    e = annual_entry(); del e["fiscal_year"]
    with pytest.raises(ManualError, match="fiscal_year is required"):
        parse(with_annual(e))
    e = annual_entry(); del e["period_end"]
    with pytest.raises(ManualError, match="period_end is required"):
        parse(with_annual(e))


def test_a_fiscal_year_may_close_in_the_next_calendar_year():
    """A retailer's 2025 closing 2026-01-31 is an ordinary annual entry.

    Inside `periods:` that would be a label problem; the annual block
    carries no label, which is why it can hold it.
    """
    parsed = parse(with_annual(annual_entry(2025, "2026-01-31",
                                            diluted_eps=figure(1.0))))
    assert parsed.annual[0].period_end == date(2026, 1, 31)


def test_annual_entries_are_oldest_first_and_unique():
    with pytest.raises(ManualError, match="oldest first"):
        parse(with_annual(annual_entry(2025, "2025-12-31"),
                          annual_entry(2024, "2024-12-31")))
    with pytest.raises(ManualError, match="duplicate fiscal_year"):
        parse(with_annual(annual_entry(2025, "2025-12-31"),
                          annual_entry(2025, "2025-12-31")))


def test_an_unknown_key_or_figure_in_the_annual_block_fails():
    e = annual_entry(); e["period"] = "2025-FY"
    with pytest.raises(ManualError, match="unknown key"):
        parse(with_annual(e))
    with pytest.raises(ManualError, match="unknown figure"):
        parse(with_annual({"fiscal_year": 2025, "period_end": "2025-12-31",
                           "document": "x", "figures": {"ebit_margin": figure(1)}}))


def test_the_annual_block_obeys_the_same_unit_contract():
    """E15 gave the block a home, not an exemption."""
    with pytest.raises(ManualError, match="outside the plausible band"):
        parse(with_annual(annual_entry(op_margin=figure(6.6))))
    with pytest.raises(ManualError, match="do not describe one measure"):
        parse(with_annual(annual_entry(revenue=figure(1000),
                                       operating_income=figure(66),
                                       op_margin=figure(0.12))))


def test_a_unit_mix_between_the_blocks_is_caught():
    doc = with_annual(annual_entry(revenue=figure(4_000_000_000)),
                      periods=[period(figures={"revenue": figure(1000)})])
    with pytest.raises(ManualError, match="UNIT MIX"):
        parse(doc)


# --- the isolation E15 requires --------------------------------------------


def test_the_annual_block_never_reaches_the_ranking_key():
    """E13's TTM reads `periods:` alone. Not one series point comes from
    the annual block -- so it cannot be summed into a window, and cannot
    stand in for a quarter that is not there."""
    doc = with_annual(
        annual_entry(revenue=figure(4000), gross_profit=figure(1600),
                     total_assets=figure(20_000), operating_income=figure(264),
                     op_margin=figure(0.066)),
        periods=[period("2026-Q2", end="2026-06-30",
                        figures={"revenue": figure(1000)})])
    parsed = parse(doc)
    record = as_record(parsed, as_of=AS_OF)

    assert {p.line for p in record.series} == {"Total Revenue"}
    assert [p.value for p in record.series] == [1000.0]
    assert record.latest("Total Assets") is None, "annual must not supply it"
    inputs = ranking.extract_inputs("TEST.XX", record)
    assert inputs.ebit is None and inputs.total_assets is None



def test_a_ratio_never_straddles_two_twelve_month_windows():
    """E19: an annual entry fills only where its own end IS the basis end.
    Twelve months of a DIFFERENT twelve months is not the same figure."""
    doc = with_annual(
        annual_entry(2024, "2024-12-31", operating_income=figure(1600)),
        periods=[period(figures={"total_assets": figure(20_000)})])
    states = {s.name: s for s in ratio_states(parse(doc))}
    assert states["operating profitability"].state == RATIO_MIXED_PERIODS
    assert "another twelve months" in states["operating profitability"].detail


def four_quarters_with_annual(*entries, each=None, last=None):
    """PNDORA.CO's shape: a TTM basis ending 2026-06-30 beside an `annual:`
    block whose year closed 2025-12-31 -- six months earlier."""
    doc = four_quarters(each=each, last=last)
    doc["annual"] = list(entries)
    return doc


def test_an_annual_flow_from_another_window_end_does_not_fill_a_TTM_gap():
    """E20: a flow belongs to the window it was earned in.

    FY2025's finance lines are twelve months to 2025-12-31 and the basis is
    twelve months to 2026-06-30. Filling the gap with them would re-create
    B18's first measurement -- two twelve-month legs, six months apart --
    inside the very basis E19 built to remove it.
    """
    parsed = parse(four_quarters_with_annual(
        annual_entry(2025, "2025-12-31",
                     finance_costs_period=figure(1149),
                     finance_income_period=figure(279)),
        each={"operating_income": figure(1000)}))
    basis = section5_basis(parsed)
    assert basis.end == date(2026, 6, 30)
    leg = resolve_on_basis(parsed, basis, "finance_costs_period")
    assert leg.value is None and leg.state == QUALITY_BASIS_MISMATCH
    # BOTH ENDS NAMED -- the ruling requires the report to say which two
    # windows failed to meet, not merely that they did not.
    assert leg.end == date(2025, 12, 31)
    assert "2025-12-31" in leg.detail and "2026-06-30" in leg.detail


def test_the_net_of_two_refused_operands_is_DATA_MISSING_not_a_figure():
    """E20's second layer, and PNDORA.CO's actual §5 state: the operands are
    NOT MEANINGFUL where they sit, and the net E18 never writes to any file
    is simply absent, because the store cannot subtract off the basis."""
    parsed = parse(four_quarters_with_annual(
        annual_entry(2025, "2025-12-31",
                     finance_costs_period=figure(1149),
                     finance_income_period=figure(279)),
        each={"operating_income": figure(1000)}))
    basis = section5_basis(parsed)
    net = next(r for r in SUBTRACTIONS if r.net == "net_finance_costs")
    assert parsed.basis_subtraction(basis, net) is None
    assert resolve_on_basis(parsed, basis, "net_finance_costs").state == \
        RATIO_MISSING


def test_an_annual_entry_AT_the_basis_end_still_fills_a_TTM_gap():
    """E20 governs a different END, not a different block. E17's narrowing
    is untouched: where the annual entry closes ON the basis end, it fills
    what `periods:` cannot -- and this is the leg a one-line flip in the
    wrong direction would take away silently."""
    parsed = parse(four_quarters_with_annual(
        annual_entry(2026, "2026-06-30", diluted_eps=figure(67.9)),
        each={"operating_income": figure(1000)}))
    basis = section5_basis(parsed)
    filled = resolve_on_basis(parsed, basis, "diluted_eps")
    assert filled.value == 67.9 and filled.state == RATIO_OK
    assert filled.source == "annual FY2026" and filled.end == basis.end


def test_a_newer_annual_entry_off_the_basis_does_not_hide_one_on_it():
    """E20 asks which entry CLOSES ON the basis end, not which is newest.

    Two annual entries, the newer closing 2026-06-30 and the older closing
    2025-12-31, with a basis ending 2025-12-31: the older one fills. Before
    this, the first entry that HELD the field ended the search, so the newer
    mismatched one refused a leg the block could answer.
    """
    doc = document([period("2025-FY", end="2025-12-31",
                           figures={"revenue": figure(1000)})],
                   reporting_frequency="half_yearly")
    doc["annual"] = [annual_entry(2025, "2025-12-31", diluted_eps=figure(50.0)),
                     annual_entry(2026, "2026-06-30", diluted_eps=figure(67.9))]
    parsed = parse(doc)
    basis = section5_basis(parsed)
    assert basis.end == date(2025, 12, 31)
    filled = resolve_on_basis(parsed, basis, "diluted_eps")
    assert filled.value == 50.0 and filled.source == "annual FY2025"
    # and a field NO entry supplies at the basis end is still refused, with
    # the newest entry that holds it named.
    doc["annual"][1]["figures"]["ebitda"] = figure(10_316)
    refused = resolve_on_basis(parse(doc), basis, "ebitda")
    assert refused.value is None and refused.state == QUALITY_BASIS_MISMATCH
    assert refused.end == date(2026, 6, 30)


# --- E25: a zero is a claim about the company ------------------------------


def zero(basis=None, page="p.31"):
    fig = {"value": 0, "page": page, "status": STATUS_VERIFIED}
    if basis:
        fig["zero_basis"] = basis
    return fig


def one_period(**figures):
    return document([period(figures=figures)])


def test_a_gate_carrying_zero_needs_its_evidence():
    """The ten fields where a wrong zero walks a name through a gate."""
    for name in sorted(ZERO_NEEDS_BASIS):
        with pytest.raises(ManualError, match="carries no zero_basis"):
            parse(one_period(**{name: zero()}))


@pytest.mark.parametrize("form", ["caption", "note", "subtotal"])
def test_the_three_forms_are_accepted(form):
    parsed = parse(one_period(financial_liabilities_current=zero(form)))
    figure = parsed.periods[0].figures["financial_liabilities_current"]
    assert figure.value == 0 and figure.zero_basis == form


def test_a_form_the_schema_does_not_know_is_refused():
    with pytest.raises(ManualError, match="zero_basis must be one of"):
        parse(one_period(financial_liabilities_current=zero("i looked")))


def test_zero_basis_on_a_figure_that_is_not_zero_is_refused():
    fig = {"value": 12.0, "page": "p.9", "status": STATUS_VERIFIED,
           "zero_basis": "caption"}
    with pytest.raises(ManualError, match="says nothing about any other figure"):
        parse(one_period(financial_liabilities_current=fig))


def test_the_fields_that_may_not_be_zero_at_all():
    """Counts, concepts the issuer does not present, and non-GAAP memos."""
    for name in sorted(ZERO_REFUSED):
        with pytest.raises(ManualError, match="may not be zero"):
            parse(one_period(**{name: zero("caption")}))


def test_a_safe_direction_zero_needs_no_evidence():
    """A wrong zero in `proceeds_from_disposals_ppe` understates free cash
    flow: it fails a gate the name should pass, which costs an opportunity
    and not money. E25 does not spend friction on it."""
    parsed = parse(one_period(proceeds_from_disposals_ppe=zero()))
    assert parsed.periods[0].figures["proceeds_from_disposals_ppe"].value == 0


def test_the_subtotal_form_is_unavailable_where_a_combined_line_exists():
    """A combined line is a caption WITH ROOM IN IT -- the one thing the
    subtotal form exists to exclude (E25, Betsson's capex)."""
    with pytest.raises(ManualError, match="caption WITH ROOM IN IT"):
        parse(one_period(capex_ppe=zero("subtotal"),
                         capex_combined={"value": -14.6, "page": "p.17",
                                         "status": STATUS_VERIFIED}))
    # the caption form is still open to the reader who saw the line
    parsed = parse(one_period(capex_ppe=zero("caption"),
                              capex_combined={"value": -14.6, "page": "p.17",
                                              "status": STATUS_VERIFIED}))
    assert parsed.periods[0].figures["capex_ppe"].zero_basis == "caption"


def test_a_zero_coverage_denominator_refuses_section_5():
    """EBIT / 0 is undefined, not large. E19's failure mode, one gate over."""
    doc = four_quarters(each={"revenue": figure(1000),
                              "net_finance_costs": zero("note")})
    gate = section5_gate(parse(doc), as_of=AS_OF)
    assert gate.refused
    kinds = [r.kind for r in gate.refusals]
    assert REFUSE_ZERO_DENOMINATOR in kinds
    detail = [r.detail for r in gate.refusals if r.kind == REFUSE_ZERO_DENOMINATOR][0]
    assert "undefined, not large" in detail


def test_the_report_names_every_zero_and_its_form():
    doc = four_quarters(each={"revenue": figure(1000),
                              "lease_liabilities": zero("note")})
    parsed = parse(doc)
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "ZEROS, AND WHAT THE READER SAW (E25)" in report
    assert "| `lease_liabilities` | 2025-Q3 | note |" in report


def test_a_margin_is_not_summed_over_the_window():
    """op_margin was omitted from STATED_RATIO_FIELDS and resolved as a
    flow: four quarterly margins of ~0.14 summed to 0.66. A margin is not
    a quantity that accumulates."""
    from vss.manual import STATED_RATIO_FIELDS
    assert "op_margin" in STATED_RATIO_FIELDS
    parsed = parse(four_quarters(each={"revenue": figure(1000),
                                       "operating_income": figure(136),
                                       "op_margin": figure(0.136)}))
    r = resolve_on_basis(parsed, section5_basis(parsed), "op_margin")
    assert r.value == 0.136 and r.source == "2026-Q2"


def test_the_sweep_for_other_summable_non_flows():
    """Reported before changing more than op_margin: every field whose
    kind is a ratio, a per-share figure or a count and which still
    resolves as a flow. Four remain, and each is a decision, not a typo:
    a TTM EPS IS the sum of four quarters, a weighted-average count is
    NOT, and a year-on-year rate is neither."""
    from vss.manual import STATED_RATIO_FIELDS, STOCK_FIELDS
    summed = [f.name for f in FIELDS
              if f.kind in ("ratio", "per_share", "count", "multiple")
              and f.name not in STOCK_FIELDS
              and f.name not in STATED_RATIO_FIELDS]
    assert sorted(summed) == ["diluted_eps", "diluted_eps_adjusted",
                              "diluted_weighted_average_shares", "revenue_yoy"]


def test_a_total_the_issuer_never_totals_is_added_where_the_issuer_treats_it_as_one():
    """E71 (2026-08-30) narrowed E26: two presented captions and no stated
    total are ADDED where the issuer's own evidence says they are one
    quantity; without that evidence the field stays DATA MISSING (E26)."""
    note = FIELDS_BY_NAME["lease_liabilities"].note
    assert "TWO CAPTIONS AND STATES NO TOTAL" in note
    assert "E71" in note and "ONE QUANTITY" in note
    assert "E26" in note and "DATA MISSING" in note
    assert "E73" in note                       # the unsized finance lease
    assert "E74" in FIELDS_BY_NAME["pension_deficit"].note
    assert "E75" in FIELDS_BY_NAME["shares_outstanding_period_end"].note


def capex(**figures):
    """Four quarters carrying whatever capex lines the issuer prints."""
    return four_quarters(each={"operating_cash_flow": figure(1000),
                               **{k: figure(v) for k, v in figures.items()}})


def test_the_split_is_read_where_the_issuer_prints_it():
    parsed = parse(capex(capex_ppe=-100, capex_intangibles=-40))
    legs, why = capex_legs(parsed, section5_basis(parsed))
    assert legs == ("capex_ppe", "capex_intangibles")
    assert why.startswith("split")


def test_the_combined_line_is_read_where_the_split_is_absent():
    """E23: Betsson's interims print one line and never split it."""
    parsed = parse(capex(capex_combined=-140))
    legs, why = capex_legs(parsed, section5_basis(parsed))
    assert legs == ("capex_combined",)
    assert why.startswith("combined")
    state = {s.name: s for s in ratio_states(parsed)}["free cash flow, basis 1"]
    assert state.state == RATIO_OK


def test_the_split_wins_and_the_combined_line_is_named_as_unused():
    """A combined figure entered beside the split is the same money twice."""
    parsed = parse(capex(capex_ppe=-100, capex_intangibles=-40,
                         capex_combined=-140))
    legs, why = capex_legs(parsed, section5_basis(parsed))
    assert legs == ("capex_ppe", "capex_intangibles")
    assert "NOT used" in why and "the split wins" in why


def test_one_split_leg_is_never_added_to_the_combined_line():
    """NEVER A MIX: that would be one line added to a total containing it."""
    parsed = parse(capex(capex_ppe=-100, capex_combined=-140))
    legs, why = capex_legs(parsed, section5_basis(parsed))
    assert legs == ("capex_combined",)
    assert "capex_ppe" in why and "NOT added" in why


def test_neither_capex_leaves_fcf_basis_1_data_missing():
    parsed = parse(capex())
    legs, why = capex_legs(parsed, section5_basis(parsed))
    assert why.startswith("neither")
    state = {s.name: s for s in ratio_states(parsed)}["free cash flow, basis 1"]
    assert state.state == RATIO_MISSING


def test_the_report_names_which_capex_it_used_every_time():
    parsed = parse(capex(capex_combined=-140))
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "CAPEX ON THE BASIS (E23): combined" in report
    # -140 in each of the four quarters, summed on the basis (E19)
    assert "`capex_combined` -560.00" in report
    split = parse(capex(capex_ppe=-100, capex_intangibles=-40))
    assert "CAPEX ON THE BASIS (E23): split" in render_report(
        split, section5_gate(split, as_of=AS_OF))


def test_capex_combined_is_a_section_5_field_and_a_stated_one():
    spec = FIELDS_BY_NAME["capex_combined"]
    assert spec.reads == ("5.1C",)
    assert "STATED FIGURE, NOT A SUM" in spec.note
    assert "LEAVE THIS BLANK" in spec.note


def test_a_refused_STOCK_names_two_dates_and_claims_no_length():
    """E20: a stock has no length, so its refusal may not say it covers
    another twelve months. It names the two ENDS and stops.

    B18's fourth measurement is that a stock has no length; this is that
    measurement in the PROSE, where it survived E19 unnoticed.
    """
    parsed = parse(four_quarters_with_annual(
        annual_entry(2025, "2025-12-31", cash_and_equivalents=figure(908)),
        each={"ebitda": figure(2000)},
        last={"financial_liabilities_current": figure(1076),
              "financial_liabilities_noncurrent": figure(9184),
              # E35 made leases a leg of the net-debt ratio, and E35.1 the
              # pension deficit, so the fixture carries both -- otherwise
              # `input missing` pre-empts the wording under test, which is
              # about a MISMATCHED stock.
              "lease_liabilities": figure(6291),
              "pension_deficit": figure(100),
              "asset_retirement_obligation": zero_figure(),
        "prepaid_delivery_obligation": zero_figure(),     # E81
              "prepaid_delivery_obligation": zero_figure()}))
    basis = section5_basis(parsed)
    stock = resolve_on_basis(parsed, basis, "cash_and_equivalents")
    assert stock.value is None and stock.state == QUALITY_BASIS_MISMATCH
    assert "twelve months" not in stock.detail
    assert "2025-12-31" in stock.detail and "2026-06-30" in stock.detail
    # the ratio that reads it says the same
    detail = {s.name: s for s in ratio_states(parsed, basis)}["net debt"].detail
    assert "cash_and_equivalents is stated at 2025-12-31" in detail
    assert "twelve months" not in detail
    # and the report gives the two kinds two blocks
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "**NOT MEANINGFUL — another period end.**" in report
    assert "| `cash_and_equivalents` | NOT MEANINGFUL | -- | stated at " \
        "2025-12-31, not the window end |" in report
    assert "**NOT MEANINGFUL — another twelve months.**" not in report


def test_a_STATED_RATIO_from_another_year_keeps_the_flow_wording():
    """E20 draws the line at a STOCK, not at everything read from the
    newest entry. `net_debt_ebitda` is struck over a twelve-month EBITDA,
    so a figure from another year IS another year's ratio."""
    parsed = parse(four_quarters_with_annual(
        annual_entry(2025, "2025-12-31", net_debt_ebitda=figure(1.4)),
        each={"revenue": figure(1000)}))
    ratio = resolve_on_basis(parsed, section5_basis(parsed), "net_debt_ebitda")
    assert "covers the twelve months to 2025-12-31" in ratio.detail


def test_the_overlap_guard_on_periods_is_unchanged():
    """E15 changed nothing about it, and a 2025-FY label inside periods:
    beside its own quarters stays forbidden."""
    with pytest.raises(ManualError, match="stores Q1/Q2/Q3/Q4 periods only"):
        parse(document([period("2025-Q4", end="2025-12-31"),
                        period("2025-FY", end="2025-12-31")]))
    with pytest.raises(ManualError, match="overlap"):
        parse(document([period("2025-H1", end="2025-06-30"),
                        period("2025-FY", end="2025-12-31")],
                       reporting_frequency="half_yearly"))


# --- periods: wins ----------------------------------------------------------


def full_year_period(**figures):
    """A twelve-month entry inside `periods:`, which only a half_yearly
    ticker may hold. The one case where a period is the SAME LENGTH as an
    annual entry, and so the one case where E15's rule applies (E17)."""
    return with_annual(
        annual_entry(**{k: figure(v) for k, v in figures.items()}),
        periods=[period("2025-FY", end="2025-12-31",
                        figures={k: figure(v * 10) for k, v in figures.items()})],
        reporting_frequency="half_yearly")


def test_periods_wins_where_the_period_is_the_SAME_LENGTH():
    parsed = parse(full_year_period(revenue=1000))
    assert parsed.shadowed() == {"revenue": "2025-FY"}
    assert parsed.displaced() == {}
    assert parsed.annual_figure("revenue") is None, "ignored, not read"



def test_periods_answers_and_the_annual_entry_is_simply_not_used():
    """E17 as narrowed by E19: `periods:` answers whenever it can answer at
    the basis, and `annual:` fills only what it cannot."""
    parsed = parse(with_annual(
        annual_entry(revenue=figure(4000), diluted_eps=figure(67.9)),
        periods=[period(figures={"revenue": figure(1000)})]))
    basis = section5_basis(parsed)
    assert resolve_on_basis(parsed, basis, "revenue").value == 1000.0
    assert resolve_on_basis(parsed, basis, "revenue").source == "2025-FY"
    # and the annual entry answers what periods: does not
    assert resolve_on_basis(parsed, basis, "diluted_eps").value == 67.9


def test_an_ignored_annual_figure_is_still_in_the_file_and_still_counted():
    """Ignored is not absent. It keeps its status, so it still refuses
    section 5 while unverified -- the owner entered it and must check it."""
    parsed = parse(with_annual(
        annual_entry(revenue=figure(4000, status=STATUS_UNVERIFIED)),
        periods=[period("2025-FY", end="2025-12-31",
                        figures={"revenue": figure(10_000)})],
        reporting_frequency="half_yearly"))
    assert parsed.shadowed() == {"revenue": "2025-FY"}
    assert any(f.name == "revenue" and f.period == "FY2025"
               for f in parsed.unverified())


def test_section_5_reads_the_annual_block_where_periods_does_not_answer():
    doc = with_annual(
        annual_entry(diluted_eps=figure(67.9),
                     diluted_weighted_average_shares=figure(77_189_151)),
        periods=[period(figures={"revenue": figure(1000)})])
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert set(gate.annual_used) == {"diluted_eps",
                                     "diluted_weighted_average_shares"}
    assert "diluted_eps" not in gate.missing, "supplied, so not DATA MISSING"
    report = render_report(parsed, gate)
    assert "annual FY2025" in report


# --- a period entry with nothing in it -------------------------------------



def test_a_file_whose_periods_all_lack_figures_refuses_section_5():
    """The list is not empty; the entries are."""
    parsed = parse(document([period("2026-Q1", end="2026-03-31"),
                             period("2026-Q2", end="2026-06-30")]))
    gate = section5_gate(parsed, as_of=AS_OF)
    assert gate.refused
    kinds = [r.kind for r in gate.refusals]
    assert "NO TWELVE-MONTH BASIS" in kinds
    assert "NO PERIODS" not in kinds, "that is a different condition"



def test_the_refusal_says_how_many_quarters_short_the_file_is():
    parsed = parse(document([period("2026-Q1", end="2026-03-31"),
                             period("2026-Q2", end="2026-06-30")]))
    detail = [r for r in section5_gate(parsed, as_of=AS_OF).refusals
              if r.kind == "NO TWELVE-MONTH BASIS"][0].detail
    assert "2 quarter(s) where four CONSECUTIVE ones are needed" in detail
    assert "nothing is annualised" in detail


def test_a_basis_that_supplies_no_figure_refuses_too():
    """Four quarters, every one of them empty: a basis with nothing on it."""
    parsed = parse(four_quarters())
    kinds = [r.kind for r in section5_gate(parsed, as_of=AS_OF).refusals]
    assert "NO FIGURES IN ANY PERIOD" in kinds



def test_it_exits_1_like_every_other_refusal(tmp_path):
    (tmp_path / "EMPTY.CO.yaml").write_text(yaml.safe_dump(
        document([period("2026-Q2", end="2026-06-30")], ticker="EMPTY.CO")),
        encoding="utf-8")
    code, report = run_manual(ticker="EMPTY.CO", as_of=AS_OF, directory=tmp_path)
    assert code == 1
    assert "NO TWELVE-MONTH BASIS" in report


def test_a_period_with_SOME_figures_is_not_empty_and_does_not_refuse():
    """This is about a period whose every figure is null, not a partial one."""
    parsed = parse(document([period(figures={"revenue": figure(1000)})]))
    gate = section5_gate(parsed, as_of=AS_OF)
    assert "NO FIGURES IN ANY PERIOD" not in [r.kind for r in gate.refusals]
    assert not gate.refused



def test_an_empty_quarter_inside_the_window_is_not_a_basis():
    """A flow is summed over the WHOLE window. Three quarters of four is not
    a year, and the fourth is not zero."""
    parsed = parse(four_quarters(each={"revenue": figure(1000)},
                                 last={"revenue": None} if False else None))
    assert section5_basis(parsed).kind == "ttm"
    empty = parse(document([
        period("2026-Q1", end="2026-03-31", figures={"revenue": figure(1000)}),
        period("2026-Q2", end="2026-06-30")]))
    assert section5_basis(empty) is None, "two quarters is not four"



def test_a_basis_carrying_only_a_ranking_line_refuses_too():
    """`net_ppe` is read by the ranking key and by no method of section 5."""
    parsed = parse(document([period(figures={"net_ppe": figure(500)})]))
    detail = [r for r in section5_gate(parsed, as_of=AS_OF).refusals
              if r.kind == "NO FIGURES IN ANY PERIOD"][0].detail
    assert "supplies not one figure section 5 reads" in detail



def test_an_annual_block_is_a_basis_when_periods_cannot_supply_one():
    """E17 as narrowed: `annual:` fills what `periods:` cannot -- including
    the window itself, where `periods:` has no twelve months to give."""
    doc = with_annual(annual_entry(revenue=figure(4000), diluted_eps=figure(67.9)),
                      periods=[period("2026-Q2", end="2026-06-30")])
    parsed = parse(doc)
    basis = section5_basis(parsed)
    assert basis.annual is not None and basis.label == "annual FY2025"
    assert resolve_on_basis(parsed, basis, "revenue").value == 4000.0


# --- E31: the year as filed, and what it passed over -----------------------


def half_yearly_with_annual(*halves, entries=()):
    """A half-yearly file: H rows in `periods:` and a year in `annual:`.

    The two blocks do not overlap in the guard's sense -- an annual entry
    is keyed on the fiscal year and never enters that reasoning -- so a
    file may hold both, which is exactly the shape E31 is about.
    """
    doc = document(list(halves))
    doc["annual"] = list(entries)
    return doc


def test_e31_the_basis_stays_the_year_and_both_halves_are_named():
    """Shape (i): H2 2025 + H1 2026 -- twelve months to 2026-06-30 -- beside
    an FY2025 block. E31 does NOT move the basis: it stays FY2025, and the
    two halves the basis never read are named instead."""
    parsed = parse(half_yearly_with_annual(
        period("2025-H2", end="2025-12-31", figures={"revenue": figure(500)}),
        period("2026-H1", end="2026-06-30", figures={"revenue": figure(600)}),
        entries=[annual_entry(revenue=figure(900))]))

    basis = section5_basis(parsed)
    assert basis.label == "annual FY2025", "R0 is not R1: the basis does not move"
    assert basis.end == date(2025, 12, 31)
    assert resolve_on_basis(parsed, basis, "revenue").value == 900.0

    named = [x.period for x in newer_filed_periods(parsed, basis)]
    assert named == ["2025-H2", "2026-H1"], "both halves, in file order"

    gate = section5_gate(parsed, as_of=AS_OF)
    assert [x.period for x in gate.newer_filed] == ["2025-H2", "2026-H1"]
    report = render_report(parsed, gate)
    assert "## FILED, NEWER THAN THE BASIS, AND NOT READ" in report
    assert "| `2025-H2` | 2025-12-31 | **NOT READ** |" in report
    assert "| `2026-H1` | 2026-06-30 | **NOT READ** |" in report


def test_e31_four_tiling_halves_name_only_the_newest_twelve_months():
    """Shape (ii). The window is the twelve months ending at the newest
    filed end, so 2024-H2 is older than the basis and 2025-H1 sits inside
    the basis year -- neither is newer, and neither is named."""
    parsed = parse(half_yearly_with_annual(
        period("2024-H2", end="2024-12-31", figures={"revenue": figure(400)}),
        period("2025-H1", end="2025-06-30", figures={"revenue": figure(450)}),
        period("2025-H2", end="2025-12-31", figures={"revenue": figure(500)}),
        period("2026-H1", end="2026-06-30", figures={"revenue": figure(600)}),
        entries=[annual_entry(revenue=figure(900))]))

    basis = section5_basis(parsed)
    assert basis.label == "annual FY2025" and basis.end == date(2025, 12, 31)
    named = [x.period for x in newer_filed_periods(parsed, basis)]
    assert named == ["2025-H2", "2026-H1"]
    assert "2024-H2" not in named and "2025-H1" not in named


def test_e31_a_quarterly_file_on_a_ttm_basis_prints_nothing_new():
    """Shape (iii). A TTM basis reads the newest four quarters, so nothing
    in the file is newer than it and the section does not appear at all.

    The silence is the BASIS's, not the frequency's -- see the test below,
    where a quarterly file falls back to `annual:` and its quarters ARE
    named. E31 asks nothing about `reporting_frequency`."""
    parsed = parse(four_quarters(each={"revenue": figure(1000)}))
    basis = section5_basis(parsed)
    assert basis.kind == "ttm" and basis.end == date(2026, 6, 30)
    assert newer_filed_periods(parsed, basis) == ()

    gate = section5_gate(parsed, as_of=AS_OF)
    assert gate.newer_filed == ()
    assert "FILED, NEWER THAN THE BASIS" not in render_report(parsed, gate)


def test_e31_is_frequency_blind_and_names_unread_quarters_too():
    """A QUARTERLY file too early to have four quarters: the basis falls back
    to `annual:` FY2025, and the two filed quarters newer than it are named
    on exactly the same rule as two halves would be."""
    doc = document([period("2026-Q1", end="2026-03-31", figures={"revenue": figure(1)}),
                    period("2026-Q2", end="2026-06-30", figures={"revenue": figure(1)})])
    doc["annual"] = [annual_entry(revenue=figure(900))]
    parsed = parse(doc)
    basis = section5_basis(parsed)
    assert basis.label == "annual FY2025"
    assert [x.period for x in newer_filed_periods(parsed, basis)] == [
        "2026-Q1", "2026-Q2"]


def test_e31_the_refusal_names_the_half_years_it_found():
    """The refusal used to describe four filed half-years as `0 quarter(s)`.
    It still counts quarters -- that is what the basis rule needs -- and it
    now also says what the file actually holds."""
    parsed = parse(document([
        period("2024-H2", end="2024-12-31", figures={"revenue": figure(400)}),
        period("2025-H1", end="2025-06-30", figures={"revenue": figure(450)}),
        period("2025-H2", end="2025-12-31", figures={"revenue": figure(500)}),
        period("2026-H1", end="2026-06-30", figures={"revenue": figure(600)})]))
    assert section5_basis(parsed) is None, "R1 is not ruled: halves build nothing"
    detail = [r for r in section5_gate(parsed, as_of=AS_OF).refusals
              if r.kind == "NO TWELVE-MONTH BASIS"][0].detail
    assert "0 quarter(s) where four CONSECUTIVE ones are needed" in detail
    assert "The file DOES hold 4 filed period(s)" in detail
    assert "`2024-H2`, `2025-H1`, `2025-H2`, `2026-H1`" in detail


def shares(issued=None, treasury=None, net=None, trust=None, **extra):
    figures = dict(extra)
    if issued is not None:
        figures["shares_issued_period_end"] = figure(issued, page="note 4.1, p.130")
    if treasury is not None:
        figures["treasury_shares_period_end"] = figure(treasury, page="note 4.1, p.130")
    if net is not None:
        figures["shares_outstanding_period_end"] = figure(net, page="p.9")
    if trust is not None:
        figures["employee_trust_shares_period_end"] = figure(
            trust, page="note 4.2, p.131")
    return document([period(figures=figures)])


def test_the_schema_carries_all_three_share_count_fields():
    for name in ("shares_outstanding_period_end", "shares_issued_period_end",
                 "treasury_shares_period_end"):
        assert name in FIELDS_BY_NAME
        assert FIELDS_BY_NAME[name].kind == "count"
        assert FIELDS_BY_NAME[name].reads == ("5.1A", "5.1C")


def test_all_three_count_fields_say_a_count_must_be_STATED():
    """E22: share capital over a par value is not a count, and a treasury
    holding in money is not a count. The rule is written once and carried
    by all three fields, so no one of them can drift out of step."""
    for name in ("shares_outstanding_period_end", "shares_issued_period_end",
                 "treasury_shares_period_end"):
        note = FIELDS_BY_NAME[name].note
        assert "A COUNT IS THE COUNT, AS STATED (E22)" in note, name
        assert "par value is NOT a count" in note, name
        assert "stated in money is NOT a count" in note, name
    # and the schema still has no field a count could be derived FROM:
    # share capital is not in it, which is what makes E22 unenforceable by
    # code and a rule for the person entering figures.
    assert "share_capital" not in FIELDS_BY_NAME
    assert not [n for n in FIELDS_BY_NAME if "par" in n]


# --- E54: the employee-trust leg -------------------------------------------


def test_e54_the_schema_carries_the_fourth_share_field():
    assert "employee_trust_shares_period_end" in FIELDS_BY_NAME
    spec = FIELDS_BY_NAME["employee_trust_shares_period_end"]
    assert spec.kind == "count"
    assert spec.reads == ("5.1A", "5.1C")
    assert "A COUNT IS THE COUNT, AS STATED (E22)" in spec.note


def test_e54_the_trust_leg_is_optional_and_absence_does_not_block_the_net():
    """Most issuers carry no employee trust at all, and E16's issued-minus-
    treasury subtraction is unchanged for them."""
    parsed = parse(shares(issued=79_000_000, treasury=4_415_553))
    computed, _ = parsed.section5_subtractions()["shares_outstanding_period_end"]
    assert computed.value == 74_584_447
    assert computed.optional is None


def test_e54_present_the_trust_leg_subtracts_a_third_time():
    """AUTO.L's own shape: issued 884,700,426; treasury 4,412,082;
    employee trust 282,389 (AR p.125, notes 25 and 26)."""
    parsed = parse(shares(issued=884_700_426, treasury=4_412_082, trust=282_389))
    computed, where = parsed.section5_subtractions()["shares_outstanding_period_end"]
    assert computed.value == 880_005_955
    assert computed.optional is not None
    assert computed.optional.value == 282_389


def test_e54_the_report_prints_all_three_legs_when_the_trust_is_present():
    parsed = parse(shares(issued=884_700_426, treasury=4_412_082, trust=282_389))
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert ("`shares_outstanding_period_end` = 880,005,955.00 — "
            "shares_issued_period_end 884,700,426 [2025-FY] − "
            "treasury_shares_period_end 4,412,082 [2025-FY] − "
            "employee_trust_shares_period_end 282,389 [2025-FY]") in report


def test_e54_the_report_is_unchanged_when_no_trust_is_stated():
    """The two-operand format E16 always printed is not disturbed by E54's
    addition -- this is the exact string the pre-E54 test pinned."""
    parsed = parse(shares(issued=79_000_000, treasury=4_415_553))
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert ("`shares_outstanding_period_end` = 74,584,447.00 — "
            "shares_issued_period_end 79,000,000 [2025-FY] − "
            "treasury_shares_period_end 4,415,553 [2025-FY]") in report
    # A field the schema carries but this file does not state still shows
    # up once, in FIELD COVERAGE, as DATA MISSING -- that is not the
    # subtraction line, which is what this test actually pins.
    subtracted = report.split("SUBTRACTED ON THE BASIS", 1)[1]
    subtracted = subtracted.split("## ", 1)[0]
    assert "employee_trust_shares_period_end" not in subtracted


def test_e54_a_trust_count_folded_into_treasury_is_not_the_field_this_tests():
    """Pins the ruling's instruction not to fold ESOT into
    treasury_shares_period_end: the two fields must stay independently
    readable, each with its own operand in the printed net."""
    folded = parse(shares(issued=884_700_426, treasury=4_412_082 + 282_389))
    separate = parse(shares(issued=884_700_426, treasury=4_412_082, trust=282_389))
    folded_net, _ = folded.section5_subtractions()["shares_outstanding_period_end"]
    separate_net, _ = separate.section5_subtractions()["shares_outstanding_period_end"]
    assert folded_net.value == separate_net.value  # same arithmetic ...
    assert folded_net.treasury.value != separate_net.treasury.value  # ... different provenance
    assert separate_net.optional is not None and folded_net.optional is None


def test_e54_the_trust_field_is_never_written_back(tmp_path):
    doc = shares(issued=884_700_426, treasury=4_412_082, trust=282_389,
                revenue=figure(1000))
    doc["ticker"] = "TRUST.XX"
    path = tmp_path / "TRUST.XX.yaml"
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    before = path.read_text(encoding="utf-8")
    run_manual(ticker="TRUST.XX", as_of=AS_OF, directory=tmp_path)
    assert path.read_text(encoding="utf-8") == before
    assert "880005955" not in before and "880,005,955" not in before


def test_e54_zero_is_refused_outright_like_the_other_share_counts():
    doc = shares(issued=79_000_000, treasury=4_415_553, trust=0)
    with pytest.raises(ManualError, match="may not be zero"):
        parse(doc)


def test_e54_the_appendix_reader_never_computes_the_trust_leg():
    import inspect

    from vss import appendix

    body = inspect.getsource(appendix)
    assert "employee_trust_shares_period_end" not in body


def test_the_store_subtracts_issued_minus_treasury():
    parsed = parse(shares(issued=79_000_000, treasury=4_415_553))
    computed, where = parsed.section5_subtractions()["shares_outstanding_period_end"]
    assert computed.value == 74_584_447
    assert where == "2025-FY"


def test_it_computes_only_when_both_are_present():
    """Where either is absent and the net is not entered directly, all three
    are DATA MISSING. Nothing estimates the half that is not there."""
    for doc in (shares(issued=79_000_000), shares(treasury=4_415_553)):
        parsed = parse(doc)
        assert "shares_outstanding_period_end" not in parsed.section5_subtractions()
        assert "shares_outstanding_period_end" in parsed.missing()


def test_a_net_count_entered_directly_is_not_recomputed():
    parsed = parse(shares(net=74_584_447, issued=79_000_000,
                          treasury=4_415_553))
    assert "shares_outstanding_period_end" not in parsed.section5_subtractions()
    assert parsed.periods[-1].value("shares_outstanding_period_end") == 74_584_447


def test_a_computable_net_is_not_reported_as_data_missing():
    parsed = parse(shares(issued=79_000_000, treasury=4_415_553))
    assert "shares_outstanding_period_end" not in parsed.missing()
    assert "shares_issued_period_end" not in parsed.missing()


def test_the_computed_net_is_never_written_back_into_the_file(tmp_path):
    """It carries no page of its own and belongs in no file."""
    doc = shares(issued=79_000_000, treasury=4_415_553, revenue=figure(1000))
    path = tmp_path / "TEST.XX.yaml"
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    before = path.read_text(encoding="utf-8")

    run_manual(ticker="TEST.XX", as_of=AS_OF, directory=tmp_path)

    assert path.read_text(encoding="utf-8") == before
    assert "74584447" not in before and "74,584,447" not in before



def test_the_report_names_both_operands_and_their_pages():
    parsed = parse(shares(issued=79_000_000, treasury=4_415_553))
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "SUBTRACTED ON THE BASIS" in report
    assert ("`shares_outstanding_period_end` = 74,584,447.00 — "
            "shares_issued_period_end 79,000,000 [2025-FY] − "
            "treasury_shares_period_end 4,415,553 [2025-FY]") in report


def test_the_net_is_subtracted_ON_ONE_BASIS():
    """E19 turned "at one period" into "on one basis", which is what makes
    the operands and their net incapable of disagreeing. A stock resolves
    at the window END, so an issued count from an earlier quarter is not on
    the basis and there is nothing to subtract from."""
    parsed = parse(four_quarters(
        first={"shares_issued_period_end": figure(79_000_000)},
        last={"treasury_shares_period_end": figure(4_415_553)}))
    assert "shares_outstanding_period_end" not in parsed.section5_subtractions()



def test_the_annual_block_may_supply_the_pair(tmp_path):
    """`annual:` fills what `periods:` cannot -- here, both operands."""
    doc = with_annual(
        annual_entry(shares_issued_period_end=figure(79_000_000),
                     treasury_shares_period_end=figure(4_415_553)),
        periods=[period(figures={"revenue": figure(1000)})])
    got = parse(doc).section5_subtractions()
    assert got["shares_outstanding_period_end"][0].value == 74_584_447


def test_the_operands_still_refuse_section_5_while_unverified():
    """The computed net has no status; its operands do, and they are the
    thing a person has to check."""
    doc = shares(issued=79_000_000, treasury=4_415_553)
    doc["periods"][0]["figures"]["shares_issued_period_end"]["status"] = \
        STATUS_UNVERIFIED
    gate = section5_gate(parse(doc), as_of=AS_OF)
    assert any(r.kind == "UNVERIFIED" and "shares_issued_period_end" in r.subject
               for r in gate.refusals)


def test_the_appendix_reader_never_computes_the_net():
    """E16 leaves appendix.py forbidden: it fills only what the sheet states.
    If a sheet carries both components it fills both fields, and the store
    does the rest."""
    import inspect

    from vss import appendix

    body = inspect.getsource(appendix)
    for forbidden in ("net_shares", "NetShares", "shares_issued_period_end -",
                      "ISSUED_SHARES"):
        assert forbidden not in body, forbidden



def test_an_entered_but_empty_period_is_not_called_an_empty_template():
    """The list is not empty; the entries are."""
    parsed = parse(document([period("2025-FY", end="2025-12-31")]))
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "supplies not one figure section 5 reads" in report
    assert "valid empty template" not in report

    empty = parse(document([]))
    assert "valid empty template" in render_report(
        empty, section5_gate(empty, as_of=AS_OF))


def quarter_against_year(field="ebitda", quarter=2133.0, year=10316.0):
    return with_annual(
        annual_entry(**{field: figure(year)}),
        periods=[period("2026-Q2", end="2026-06-30",
                        figures={field: figure(quarter)})])


def test_a_quarter_does_not_displace_a_year():
    """PNDORA.CO's case: a three-month EBITDA of 2,133 was displacing a
    twelve-month one of 10,316, 4.84x apart, and nothing said so."""
    parsed = parse(quarter_against_year())
    assert parsed.shadowed() == {}, "a quarter shadows nothing"
    assert parsed.displaced() == {"ebitda": ("2026-Q2", 3, 2133.0)}
    assert parsed.annual_figure("ebitda").value == 10316.0


def test_a_half_year_does_not_displace_a_year_either():
    doc = with_annual(annual_entry(ebitda=figure(10316.0)),
                      periods=[period("2025-H2", end="2025-12-31",
                                      figures={"ebitda": figure(5000.0)})],
                      reporting_frequency="half_yearly")
    parsed = parse(doc)
    assert parsed.displaced() == {"ebitda": ("2025-H2", 6, 5000.0)}
    assert parsed.annual_figure("ebitda").value == 10316.0



def test_the_report_names_a_leg_of_another_twelve_months():
    """E19 replaced E17's "used / not used" pairing: a figure of another
    twelve months is NOT MEANINGFUL, and the report names both ends."""
    parsed = parse(with_annual(
        annual_entry(2024, "2024-12-31", ebitda=figure(10316.0)),
        periods=[period(figures={"revenue": figure(1000)})]))
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "NOT MEANINGFUL — another twelve months." in report
    assert "annual FY2024 covers the twelve months to 2024-12-31" in report
    assert "the basis ends 2025-12-31" in report



def test_the_input_block_names_the_window_every_summed_figure_came_from():
    """E19 limit 2: a section 5 figure the accounts do not print must say
    what it was built from, every time it appears."""
    parsed = parse(four_quarters(each={"ebitda": figure(2000)}))
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "BASIS: `TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2`" in report
    assert "| `ebitda` | 8,000.00 | TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2 |" in report
    assert "SUMMED" in report


def test_a_period_figure_with_no_annual_counterpart_is_untouched():
    """E17 is about a collision. A quarter that collides with nothing wins
    by default, as it always did."""
    parsed = parse(quarter_against_year(field="revenue", quarter=7219.0,
                                        year=None) if False else with_annual(
        annual_entry(diluted_eps=figure(67.9)),
        periods=[period("2026-Q2", end="2026-06-30",
                        figures={"ebitda": figure(2133.0)})]))
    assert parsed.displaced() == {} and parsed.shadowed() == {}
    gate = section5_gate(parsed, as_of=AS_OF)
    assert "ebitda" not in gate.annual_used


def test_e15_is_otherwise_unchanged_the_annual_block_reaches_no_record():
    """E17 changed which block answers, not what the annual block feeds."""
    parsed = parse(quarter_against_year())
    record = as_record(parsed, as_of=AS_OF)
    assert record.series == (), "no series point from either the year or a bare quarter"



def test_a_page_reference_is_never_prefixed():
    """The `page:` string says where it is in the words of whoever entered
    it. Prefixing `p.` produced `p.five-year summary, p.14`."""
    from vss.manual import cite_page

    assert cite_page("five-year summary, p.14") == " [five-year summary, p.14]"
    assert cite_page("note 4.2, p.131") == " [note 4.2, p.131]"
    assert cite_page(None) == "" and cite_page("") == ""

    doc = document([period(figures={"revenue": {
        "value": 1000.0, "page": "five-year summary, p.14",
        "status": STATUS_UNVERIFIED, "source": "Annual Report 2025"}})])
    parsed = parse(doc)
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "Annual Report 2025 [five-year summary, p.14]" in report
    assert "p.five-year summary" not in report


def finance(**figures):
    return document([period(figures={
        k: figure(v, page=f"{k}, p.100") for k, v in figures.items()})])


def test_the_schema_carries_both_pairs_and_both_nets():
    for name in ("net_finance_costs", "finance_costs_period",
                 "finance_income_period", "net_interest_paid",
                 "finance_costs_paid", "finance_income_received"):
        assert name in FIELDS_BY_NAME, name
    assert FIELDS_BY_NAME["finance_costs_period"].reads == ("5.3",)
    assert FIELDS_BY_NAME["finance_costs_paid"].reads == ("5.1C",)


def test_both_field_specs_say_what_the_field_IS_not_only_who_reads_it():
    income = FIELDS_BY_NAME["net_finance_costs"].note
    cash = FIELDS_BY_NAME["net_interest_paid"].note
    assert "FINANCE COSTS LESS FINANCE INCOME" in income
    assert "INTEREST PAID LESS INTEREST RECEIVED" in cash
    # and each says it is not the other
    assert "NOT the same figure as `net_interest_paid`" in income
    assert "NOT the same figure as `net_finance_costs`" in cash


def test_the_store_subtracts_the_income_statement_pair():
    parsed = parse(finance(finance_costs_period=1149, finance_income_period=279))
    computed, where = parsed.section5_subtractions()["net_finance_costs"]
    assert computed.value == 870.0 and where == "2025-FY"


def test_the_store_subtracts_the_cash_flow_pair():
    parsed = parse(finance(finance_costs_paid=1009, finance_income_received=174))
    assert parsed.section5_subtractions()["net_interest_paid"][0].value == 835.0


def test_the_two_nets_are_different_figures_and_both_are_computed():
    """Different statements, different consumers, neither substituting."""
    parsed = parse(finance(finance_costs_period=1149, finance_income_period=279,
                           finance_costs_paid=1009, finance_income_received=174))
    got = parsed.section5_subtractions()
    assert got["net_finance_costs"][0].value == 870.0
    assert got["net_interest_paid"][0].value == 835.0


def test_one_operand_alone_leaves_that_field_and_its_net_data_missing():
    parsed = parse(finance(finance_costs_period=1149))
    assert "net_finance_costs" not in parsed.section5_subtractions()
    assert "net_finance_costs" in parsed.missing()
    assert "finance_income_period" in parsed.missing()


def test_a_net_entered_directly_is_not_recomputed():
    parsed = parse(finance(net_finance_costs=870, finance_costs_period=1149,
                           finance_income_period=279))
    assert "net_finance_costs" not in parsed.section5_subtractions()


def test_neither_net_is_written_back_and_the_report_names_both_operands(tmp_path):
    doc = finance(finance_costs_period=1149, finance_income_period=279,
                  finance_costs_paid=1009, finance_income_received=174)
    doc["ticker"] = "FIN.XX"
    path = tmp_path / "FIN.XX.yaml"
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    before = path.read_text(encoding="utf-8")

    code, report = run_manual(ticker="FIN.XX", as_of=AS_OF, directory=tmp_path)

    assert path.read_text(encoding="utf-8") == before
    for absent in ("870", "835"):
        assert absent not in before
    assert ("`net_finance_costs` = 870.00 — finance_costs_period 1,149 "
            "[2025-FY] − finance_income_period 279 [2025-FY]") in report
    assert ("`net_interest_paid` = 835.00 — finance_costs_paid 1,009 "
            "[2025-FY] − finance_income_received 174 [2025-FY]") in report


def test_a_subtraction_happens_on_one_basis():
    """A flow is summed over the WHOLE window, so an operand present in one
    quarter of four is not on the basis and the net does not form."""
    parsed = parse(four_quarters(first={"finance_costs_period": figure(1149)},
                                 last={"finance_income_period": figure(279)}))
    assert "net_finance_costs" not in parsed.section5_subtractions()


def test_the_appendix_reader_computes_neither_finance_net():
    import inspect

    from vss import appendix

    body = inspect.getsource(appendix)
    for forbidden in ("subtract(", "SUBTRACTIONS", "net_finance_costs -",
                      "finance_income_period -"):
        assert forbidden not in body, forbidden


# =========================================================================
# A UNIT MIX ON A LEG SECTION 5 DIVIDES BY (REVIEW-4 report B 7.1)
# =========================================================================
#
# Report B ran the experiment on a copy of `config/manual/DECK.yaml`: an
# `operating_cash_flow` multiplied by a thousand LOADS, and with every
# figure of that year flagged VERIFIED the gate says MAY RUN on a
# trillion-dollar operating cash flow. The load-time guard reaches five
# fields -- revenue, total assets, gross profit, cash, net PP&E -- and not
# one of the legs the DCF divides and discounts.


def _four_quarters_with(field, values):
    """Four consecutive quarters carrying ``field`` at ``values``."""
    entries = []
    for (label, end), value in zip(FOUR_Q, values):
        entries.append(period(label, end=end, figures={field: figure(value)}))
    return document(entries)


@pytest.mark.parametrize("field", [
    "operating_cash_flow", "capex_ppe", "financial_liabilities_noncurrent",
    "lease_liabilities", "diluted_weighted_average_shares",
])
def test_a_thousandfold_step_on_a_section_5_leg_refuses_the_gate(field, tmp_path):
    """Not one of these five is on SCALE_STABLE_FIELDS, and every one of
    them is a leg `equity_value_per_share` divides or discounts."""
    from vss.manual import REFUSE_UNIT_MIX
    doc = _four_quarters_with(field, [100.0, 110.0, 120.0, 130_000.0])
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=date(2026, 8, 25))
    unit_mix = [r for r in gate.refusals if r.kind == REFUSE_UNIT_MIX]
    assert unit_mix, f"{field} passed the gate at 1,083x"
    assert unit_mix[0].subject == field
    assert "1,083x" in unit_mix[0].detail
    assert "2026-Q1" in unit_mix[0].detail and "2026-Q2" in unit_mix[0].detail


def test_the_file_wide_test_catches_what_the_consecutive_one_misses(tmp_path):
    """DECK's share count x 1000 reads 954x against its neighbour.

    That is the exact hair by which the ruled consecutive test misses a
    slip of a round thousand: the two neighbours are themselves unequal.
    Against the file's smallest entry the same slip reads 5,246x.
    """
    from vss.manual import REFUSE_UNIT_MIX
    doc = _four_quarters_with("diluted_weighted_average_shares",
                              [27.789, 150.0, 152.745, 145_805.0])
    from vss.manual import scale_jumps
    parsed = parse(doc)
    # the consecutive step is 954x -- under the bar, exactly as measured
    assert 145_805.0 / 152.745 == pytest.approx(954.56, abs=0.01)
    gate = section5_gate(parsed, as_of=date(2026, 8, 25))
    unit_mix = [r for r in gate.refusals if r.kind == REFUSE_UNIT_MIX]
    assert unit_mix, "a 954x neighbour hid a 5,247x file span"
    assert [j.span for j in scale_jumps(parsed)] == ["this file"]
    assert "this file" in unit_mix[0].detail
    assert "5,247x" in unit_mix[0].detail


def test_a_hundredfold_swing_is_a_business_event_and_passes():
    """PNDORA.CO's operating cash flow spans 136x between a weak first
    quarter and a Christmas one, honestly. The bar is set well above it."""
    from vss.manual import REFUSE_UNIT_MIX, scale_jumps
    doc = _four_quarters_with("operating_cash_flow",
                              [42.0, 500.0, 5725.0, 300.0])
    parsed = parse(doc)
    assert scale_jumps(parsed) == ()
    gate = section5_gate(parsed, as_of=date(2026, 8, 25))
    assert not [r for r in gate.refusals if r.kind == REFUSE_UNIT_MIX]


def test_a_uniformly_mis_scaled_file_still_passes_and_that_is_stated():
    """THE RESIDUAL, pinned so nobody reads the guard as complete.

    Every period agrees with every other, so no comparison ACROSS periods
    can see it. Only an absolute band on what a figure may be could, and
    no ruling sets one.
    """
    from vss.manual import scale_jumps
    doc = _four_quarters_with("operating_cash_flow",
                              [100_000.0, 110_000.0, 120_000.0, 130_000.0])
    assert scale_jumps(parse(doc)) == ()
    source = Path("vss/manual.py").read_text(encoding="utf-8")
    assert "a file mis-scaled\n#: UNIFORMLY" in source


def test_the_guarded_list_names_every_leg_method_c_reads():
    """The five load-time fields do not overlap the DCF's own inputs."""
    from vss.manual import SCALE_STABLE_FIELDS, SECTION5_SCALE_FIELDS
    for leg in ("operating_cash_flow", "capex_ppe", "capex_intangibles",
                "capex_combined", "financial_liabilities_current",
                "financial_liabilities_noncurrent", "lease_liabilities",
                "diluted_weighted_average_shares",
                "shares_outstanding_period_end"):
        assert leg in SECTION5_SCALE_FIELDS
        assert leg not in SCALE_STABLE_FIELDS


# --- basis 3 must not charge the same interest twice ----------------------
#
# REVIEW-4 report B Part 8 #1 and report C 9.3 #8. The field's own next
# sentence said "FCF basis 3 deducts it" with no precondition, and the tests
# above pin that subtraction ON PANDORA'S FIGURES -- a filer whose "Finance
# costs paid -1,009" and "Finance income received 174" sit INSIDE its
# operating cash flow (annual report p.103). The arithmetic is right; the
# stated USE of it was wrong for exactly the filer type the tests use.


def test_the_field_note_states_the_precondition_basis_3_needs():
    note = FIELDS_BY_NAME["net_interest_paid"].note
    assert "ONLY WHERE THE FILER'S OPERATING CASH FLOW IS PRE-INTEREST" in note
    assert "a second time" in note
    # and it still says what it is and what it is not
    assert "INTEREST PAID LESS INTEREST RECEIVED" in note
    assert "NOT the same figure as `net_finance_costs`" in note


def test_no_ratio_forms_basis_3_so_nothing_can_deduct_interest_twice():
    """The guard that holds today: basis 3 is not formed anywhere.

    `RATIOS` names basis 1 alone. A basis-3 ratio may exist only once the
    file records where the filer books its interest -- until then there is
    no way for the gate to tell a legitimate deduction from a double one.
    """
    from vss.manual import RATIOS
    names = [name for name, _legs, _reads in RATIOS]
    assert "free cash flow, basis 1" in names
    assert not [n for n in names if "basis 3" in n]
    for _name, legs, _reads in RATIOS:
        assert "net_interest_paid" not in legs


def test_the_size_of_the_double_count_on_a_post_interest_filer():
    """Lindab's R12M to 2026-06-30: interest 211 paid, 10 received, both
    inside operating cash flow (interim p.17). Deducting the net again."""
    from vss.valuation import equity_value_per_share as ev
    lindab = dict(growth=0.02, net_cash=-4497.0, shares=77.036)
    as_struck = ev(fcf0=879.0, **lindab)
    basis_3_on_the_issuer_kpi = ev(fcf0=879.0 - 201.0, **lindab)
    basis_3_on_schema_basis_1 = ev(fcf0=849.0 - 201.0, **lindab)
    assert as_struck == pytest.approx(102.66, abs=0.005)
    assert basis_3_on_the_issuer_kpi == pytest.approx(65.83, abs=0.005)
    assert basis_3_on_schema_basis_1 == pytest.approx(60.34, abs=0.005)


# --- a share split inside one file is FLAGGED, never rescaled -------------


def test_a_share_count_that_steps_by_six_is_flagged_and_does_not_refuse():
    """REVIEW-4 report B 7.1 / report C golden case G9.

    `config/manual/DECK.yaml` holds FY2022 `diluted_eps` 16.26 and
    27,789,000 shares -- filed before the 6-for-1 split of 2024-09-13, and
    no later 10-K carries FY2022, so nothing restated it -- beside FY2023's
    3.23 and 160,111,000. `SCALE_STABLE_FIELDS` reaches neither field and
    the factor there is a thousand, so no check saw a 5.8x step in a count.
    """
    from vss.manual import FLAG_SHARE_BASIS_STEP
    doc = document([
        period("2022-FY", end="2022-03-31", figures={
            "diluted_eps": figure(16.26),
            "diluted_weighted_average_shares": figure(27_789_000)}),
        period("2023-FY", end="2023-03-31", figures={
            "diluted_eps": figure(3.23),
            "diluted_weighted_average_shares": figure(160_111_000)}),
    ])
    gate = section5_gate(parse(doc), as_of=date(2023, 6, 1))
    kinds = {f.kind for f in gate.flags}
    assert kinds == {FLAG_SHARE_BASIS_STEP}
    subjects = {f.subject for f in gate.flags}
    assert subjects == {"diluted_eps", "diluted_weighted_average_shares"}
    detail = next(f.detail for f in gate.flags
                  if f.subject == "diluted_weighted_average_shares")
    assert "5.76x" in detail and "NOTHING IS RESCALED" in detail
    # A FLAG, NOT A REFUSAL. Section 5 reads the newest year and is fine.
    assert FLAG_SHARE_BASIS_STEP not in {r.kind for r in gate.refusals}


def test_an_ordinary_buyback_is_not_flagged():
    """DECK bought back 10.5m of 156m shares in FY2026. Two is the bar
    because a split is six and a year of buybacks is a few per cent."""
    from vss.manual import share_basis_steps
    doc = document([
        period("2025-FY", end="2025-03-31", figures={
            "diluted_weighted_average_shares": figure(152_670_000)}),
        period("2026-FY", end="2026-03-31", figures={
            "diluted_weighted_average_shares": figure(145_805_000)}),
    ])
    assert share_basis_steps(parse(doc)) == ()


def test_the_committed_DECK_file_is_flagged_and_the_flag_does_not_refuse():
    parsed = load_manual("DECK", directory=MANUAL_DIR)
    gate = section5_gate(parsed, as_of=date(2026, 8, 26))
    # Three SHARE-BASIS fields, not two: E38's `shares_point_in_time` memo
    # crosses the same split, which is the flag doing exactly what it is
    # for. E108 (2026-09-04) adds a flag of a DIFFERENT KIND beside them --
    # the E105 leg, VERIFIED-EXEMPT on the zero limb -- so the set is
    # taken per kind rather than whole.
    from vss.manual import FLAG_EXEMPT
    assert {f.subject for f in gate.flags
            if f.kind != FLAG_EXEMPT} == {
        "diluted_eps", "diluted_weighted_average_shares",
        "shares_point_in_time"}
    assert {f.subject for f in gate.flags if f.kind == FLAG_EXEMPT} == {
        "FY2026 nci_dividends_paid"}
    # A FLAG IS NOT A REFUSAL: the share-basis step is nowhere in the
    # refusal list, whatever else is (E34 puts `FCF0 DATA MISSING` there
    # for a US filer -- see tests/test_manual.py's E34 section).
    from vss.manual import FLAG_SHARE_BASIS_STEP
    assert FLAG_SHARE_BASIS_STEP not in {r.kind for r in gate.refusals}


# =========================================================================
# E34 -- WHERE A FILER BOOKS ITS INTEREST, AND WHAT FCF0 IS
# =========================================================================


def _fcf0_file(interest, **figures):
    base = {"operating_cash_flow": figure(1000.0), "capex_ppe": figure(-60.0),
            "capex_intangibles": figure(-40.0), "sbc": figure(20.0)}
    base.update({k: figure(v) for k, v in figures.items()})
    return document([period(figures=base)], interest_in_ocf=interest)


def test_a_file_that_does_not_say_has_no_FCF0_and_section_5_does_not_run():
    from vss.manual import REFUSE_INTEREST_UNCLASSIFIED, FCF0_RATIO
    gate = section5_gate(parse(_fcf0_file(None)), as_of=AS_OF)
    assert REFUSE_INTEREST_UNCLASSIFIED in {r.kind for r in gate.refusals}
    detail = next(r.detail for r in gate.refusals
                  if r.kind == REFUSE_INTEREST_UNCLASSIFIED)
    assert "charges the same interest twice" in detail
    state = next(r for r in gate.ratios if r.name == FCF0_RATIO)
    assert state.state == RATIO_MISSING
    assert "NOT RECORDED" in state.detail
    # basis 1 is unaffected -- it never depended on the classification
    assert next(r for r in gate.ratios
                if r.name == "free cash flow, basis 1").state == RATIO_OK


def test_interest_in_ocf_no_leaves_FCF0_as_operating_cash_flow_less_capex():
    from vss.manual import FCF0_RATIO, interest_legs
    parsed = parse(_fcf0_file(INTEREST_NO))
    assert interest_legs(parsed) == ()
    gate = section5_gate(parsed, as_of=AS_OF)
    assert next(r for r in gate.ratios if r.name == FCF0_RATIO).state == RATIO_OK


def test_interest_in_ocf_yes_makes_the_add_back_a_required_leg():
    from vss.manual import FCF0_RATIO, REFUSE_NO_FCF0, interest_legs
    parsed = parse(_fcf0_file(INTEREST_YES))
    assert interest_legs(parsed) == ("net_interest_paid",)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert next(r for r in gate.ratios if r.name == FCF0_RATIO).state == RATIO_MISSING
    assert REFUSE_NO_FCF0 in {r.kind for r in gate.refusals}

    with_it = parse(_fcf0_file(INTEREST_YES, net_interest_paid=50.0))
    gate = section5_gate(with_it, as_of=AS_OF)
    assert next(r for r in gate.ratios if r.name == FCF0_RATIO).state == RATIO_OK


def test_the_add_back_may_come_from_E18_s_two_halves():
    """A filer that prints interest paid and interest received separately
    -- the usual IFRS presentation -- states the net twice over."""
    from vss.manual import FCF0_RATIO, resolve_or_subtract, section5_basis
    parsed = parse(_fcf0_file(INTEREST_YES, finance_costs_paid=211.0,
                              finance_income_received=10.0))
    basis = section5_basis(parsed)
    assert resolve_or_subtract(parsed, basis, "net_interest_paid") == 201.0
    gate = section5_gate(parsed, as_of=AS_OF)
    assert next(r for r in gate.ratios if r.name == FCF0_RATIO).state == RATIO_OK


def test_the_block_refuses_a_bare_bool_and_a_missing_page():
    with pytest.raises(ManualError, match="value must be yes or no"):
        parse(_fcf0_file({"value": "maybe", "source": "x", "page": "1"}))
    with pytest.raises(ManualError, match="source and page are both required"):
        parse(_fcf0_file({"value": True}))
    with pytest.raises(ManualError, match="expected a mapping"):
        parse(_fcf0_file(True))


# =========================================================================
# E35 -- LEASES ARE IN NET DEBT, ALWAYS
# =========================================================================
#
# LINDAB-SHAPED, from its Q2 2026 interim (p.25): total interest-bearing
# provisions and liabilities 5,073 = borrowings 3,383 + leases 1,410 +
# pension provisions 280; total interest-bearing assets 576 = cash 506 +
# 70 of other current financial assets; stated net debt 4,497. (These are
# the components the FIRST re-strike used; the store file written in Build
# 2 reads the page as cash 527, other current 10, current borrowings 5 --
# same 576 of assets, and 4,536 with the 39 of non-current assets omitted.)
# E35.1 (2026-08-26) made the 280 a LEG, so the fixture carries it.


def _lindab_shaped(**overrides):
    figures = {
        "operating_cash_flow": figure(1176.0),
        "capex_ppe": figure(-327.0),
        "financial_liabilities_current": figure(600.0),
        "financial_liabilities_noncurrent": figure(2783.0),   # 3,383 in total
        "lease_liabilities": figure(1410.0),
        "pension_deficit": figure(280.0),
        # E68 (2026-08-29): a required leg; Lindab-shaped means none.
        "asset_retirement_obligation": zero_figure(),
        # E81 (2026-08-30): the same -- no stream, a caption zero.
        "prepaid_delivery_obligation": zero_figure(),
        "cash_and_equivalents": figure(506.0),
        "other_current_financial_assets": figure(70.0),
    }
    figures.update({k: figure(v) for k, v in overrides.items()})
    return document([period(figures=figures)], interest_in_ocf=INTEREST_YES)


def test_the_five_legs_give_4497_and_the_280_is_the_pension_leg():
    """E35's four legs gave 4,217 and named the 280 as the pension provision
    this schema had NO FIELD for -- not plugged. E35.1 (2026-08-26) made it
    a leg, and the formula reaches Lindab's own 4,497 on the same page."""
    from vss.manual import net_debt_on_basis, section5_basis
    parsed = parse(_lindab_shaped())
    basis = section5_basis(parsed)
    value, why = net_debt_on_basis(parsed, basis)
    # E117 (2026-09-19): the 1,410 IFRS 16 liability LEAVES net debt, its
    # rent now in the flow -- 4,497 with it, 3,087 without, which is
    # Lindab's own "adjusted net debt" on the same page.
    assert value == pytest.approx(3087.0)
    assert "LEAVES net debt whole (E117" in why and "pension deficit 280 (E35.1)" in why
    assert "No NCI, associate, preferred or convertible leg" in why
    # and without the leg it is not 4,217 any more -- it is DATA MISSING
    doc = _lindab_shaped()
    del doc["periods"][0]["figures"]["pension_deficit"]
    without = parse(doc)
    value, why = net_debt_on_basis(without, section5_basis(without))
    assert value is None and "pension_deficit is not on the basis" in why


def test_leases_in_against_leases_out_is_what_E35_is_ABOUT():
    """1,410 of leases, and the two answers it gives on the held name."""
    from vss.manual import net_debt_on_basis, section5_basis
    from vss.valuation import equity_value_per_share as ev
    parsed = parse(_lindab_shaped())
    # E117 (2026-09-19): the bridge now stands LEASES-OUT; leases-in is the
    # E35 figure it replaced, formed here by adding the liability back.
    without, _ = net_debt_on_basis(parsed, section5_basis(parsed))
    with_leases = without + 1410.0
    # E35.1: the pension leg is in, so leases-in IS Lindab's own 4,497 and
    # leases-out IS its own "adjusted net debt" 3,087
    assert (with_leases, without) == (4497.0, 3087.0)
    liab = dict(fcf0=879.0, growth=0.02, shares=77.036)
    assert ev(net_cash=-with_leases, **liab) == pytest.approx(102.66, abs=0.005)
    assert ev(net_cash=-without, **liab) == pytest.approx(120.96, abs=0.005)
    # HISTORY, kept: E35's four legs alone gave 4,217 / 2,807, which were
    # 106.29 / 124.59 on the same flow -- the 280 was the gap E35 named
    # and E35.1 closed (REVIEW-4 report B #2).
    assert ev(net_cash=-4217.0, **liab) == pytest.approx(106.29, abs=0.005)
    assert ev(net_cash=-2807.0, **liab) == pytest.approx(124.59, abs=0.005)
    assert with_leases - 4217.0 == pytest.approx(280.0)


def test_a_missing_lease_liability_stops_net_debt_rather_than_omitting_it():
    """The asymmetry E35 rests on: omitting a LIABILITY raises the value."""
    from vss.manual import net_debt_on_basis, section5_basis
    doc = _lindab_shaped()
    del doc["periods"][0]["figures"]["lease_liabilities"]
    parsed = parse(doc)
    value, why = net_debt_on_basis(parsed, section5_basis(parsed))
    assert value is None and "lease_liabilities is not on the basis" in why
    state = {r.name: r for r in ratio_states(parsed)}["net debt"]
    assert state.state == RATIO_MISSING
    assert "lease_liabilities" in state.detail


def test_a_missing_financial_asset_is_simply_not_subtracted():
    """Omitting an ASSET lowers the value, so it may be absent -- and the
    sentence says which direction that is."""
    from vss.manual import net_debt_on_basis, section5_basis
    doc = _lindab_shaped()
    del doc["periods"][0]["figures"]["other_current_financial_assets"]
    parsed = parse(doc)
    value, why = net_debt_on_basis(parsed, section5_basis(parsed))
    assert value == pytest.approx(3157.0)   # 3,087 + the 70 (E117: 1,410 leases out)
    assert "which is the safe direction" in why
    assert {r.name: r for r in ratio_states(parsed)}["net debt"].state == RATIO_OK


def test_leases_are_a_leg_of_the_ratio_the_gate_prints():
    """`RATIOS` said borrowings - cash and NOTHING ELSE, so the gate called
    net debt computable for a file whose lease liability is DATA MISSING and
    threw A2 to N every time it printed the table (REVIEW-4 report B 6.1)."""
    from vss.manual import NET_DEBT_LEGS, RATIOS
    assert "lease_liabilities" in NET_DEBT_LEGS
    for name, legs, _reads in RATIOS:
        if name.startswith("net debt"):
            assert "lease_liabilities" in legs, name


# =========================================================================
# E38 -- THE DIVISOR IS THE WEIGHTED-AVERAGE DILUTED COUNT FOR THE WINDOW
# =========================================================================


def test_the_committed_DECK_store_reproduces_131_74_on_E38_s_divisor():
    """The store basis, end to end: file -> basis -> divisor -> value."""
    from vss.manual import share_count_on_basis
    from vss.valuation import equity_value_per_share as ev
    parsed = load_manual("DECK", directory=MANUAL_DIR)
    basis = section5_basis(parsed)
    count, why = share_count_on_basis(parsed, basis)
    assert count == 145_805_000
    assert "weighted-average DILUTED count for annual FY2026" in why
    store = dict(fcf0=1097.332, growth=0.035, net_cash=1907.249)
    assert ev(shares=count / 1e6, **store) == pytest.approx(131.74, abs=0.005)


def test_the_point_in_time_count_is_STORED_and_is_never_the_divisor():
    """B36 said neither the balance-sheet count nor the cover count was a
    tagged fact. Both are. E38 keeps one as a MEMO and divides by neither.

    The three answers, on one set of flows, so the size of the choice is on
    the record: the weighted average 131.74, the balance-sheet count at the
    window end 137.22, the cover count nine days later 140.81.
    """
    from vss.manual import share_count_on_basis
    from vss.valuation import equity_value_per_share as ev
    parsed = load_manual("DECK", directory=MANUAL_DIR)
    basis = section5_basis(parsed)
    memo = resolve_on_basis(parsed, basis, "shares_point_in_time")
    assert memo.value == 139_978_000
    assert "[as of 2026-03-31]" in memo.figures[0].page      # its date, on the page
    _count, why = share_count_on_basis(parsed, basis)
    assert "is on the file as a MEMO and is NOT the divisor" in why

    store = dict(fcf0=1097.332, growth=0.035, net_cash=1907.249)
    assert ev(shares=145.805, **store) == pytest.approx(131.74, abs=0.005)
    assert ev(shares=memo.value / 1e6, **store) == pytest.approx(137.22, abs=0.005)
    assert ev(shares=136.414227, **store) == pytest.approx(140.81, abs=0.005)


def test_the_memo_is_a_STOCK_and_is_never_summed_across_quarters():
    """A count outside STOCK_FIELDS resolves as a flow, which for four
    quarters means four counts added together (B27, SYNSAM's 572,025,536)."""
    from vss.manual import STOCK_FIELDS
    assert "shares_point_in_time" in STOCK_FIELDS
    parsed = parse(four_quarters(each={"shares_point_in_time": figure(100.0)}))
    got = resolve_on_basis(parsed, section5_basis(parsed), "shares_point_in_time")
    assert got.value == 100.0


def test_E38_admits_no_substitute_when_the_average_is_absent():
    from vss.manual import share_count_on_basis
    doc = document([period(figures={"shares_point_in_time": figure(136_414_227)})],
                   interest_in_ocf=INTEREST_NO)
    parsed = parse(doc)
    count, why = share_count_on_basis(parsed, section5_basis(parsed))
    assert count is None
    assert "E38 admits no substitute" in why
    assert "136,414,227" in why


# --- E34.1: the US sub-case -- the income statement's net as an accrual proxy


INTEREST_YES_ACCRUAL = {**INTEREST_YES, "interest_source": "income_statement_net"}


def test_E34_1_an_accrual_proxy_expands_to_the_income_statement_net():
    from vss.manual import FCF0_RATIO, interest_legs
    parsed = parse(_fcf0_file(INTEREST_YES_ACCRUAL, net_finance_costs=-50.0))
    assert parsed.interest_in_ocf.accrual_proxy
    assert interest_legs(parsed) == ("net_finance_costs",)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert next(r for r in gate.ratios if r.name == FCF0_RATIO).state == RATIO_OK


def test_E34_1_interest_paid_alone_is_never_the_net():
    """A file that states interest PAID and no interest RECEIVED forms no
    cash net (E18), so a `cash_flow_statement` filer with only the paid
    figure has no FCF0 -- and nothing quietly reads the 323 as the 45."""
    from vss.manual import FCF0_RATIO, resolve_or_subtract
    parsed = parse(_fcf0_file(INTEREST_YES, finance_costs_paid=323.0))
    basis = section5_basis(parsed)
    assert resolve_or_subtract(parsed, basis, "net_interest_paid") is None
    state = next(r for r in section5_gate(parsed, as_of=AS_OF).ratios
                 if r.name == FCF0_RATIO)
    assert state.state == RATIO_MISSING and "net_interest_paid" in state.detail


def test_E34_1_the_pair_forms_the_net_where_the_net_is_not_stated():
    """Deckers' shape: interest expense 2.53 and interest income 63.6 tagged,
    no net -- E18 subtracts, and the net is an INCOME, negative."""
    from vss.manual import resolve_or_subtract
    parsed = parse(_fcf0_file(INTEREST_YES_ACCRUAL, finance_costs_period=2.53,
                              finance_income_period=63.61))
    basis = section5_basis(parsed)
    assert resolve_or_subtract(parsed, basis, "net_finance_costs") == pytest.approx(-61.08)


def test_E34_1_an_accrual_proxy_with_interest_in_ocf_no_is_refused():
    with pytest.raises(ManualError, match="nothing to add back"):
        parse(_fcf0_file({**INTEREST_NO, "interest_source": "income_statement_net"}))


def test_E34_1_an_unknown_interest_source_is_refused():
    with pytest.raises(ManualError, match="interest_source must be one of"):
        parse(_fcf0_file({**INTEREST_YES, "interest_source": "the vibe"}))


# --- E40: what VERIFIED means, in three kinds -----------------------------


def test_E40_a_verified_figure_that_names_no_kind_is_same_page():
    """The migration rule: every flag set before E40 was a read-back against
    the page it came from, the weakest of the three claims."""
    from vss.manual import KIND_SAME_PAGE
    parsed = parse(document([period(figures={"revenue": figure(100.0)})]))
    fig = parsed.periods[0].figures["revenue"]
    assert fig.verified and fig.verified_kind == KIND_SAME_PAGE
    assert fig.status_with_kind == "VERIFIED (same_page)"
    assert "VERIFIED (same_page)" in fig.provenance()


@pytest.mark.parametrize("kind", ["tagged", "cross_document", "same_page"])
def test_E40_the_gate_accepts_all_three_kinds_and_the_report_prints_each(kind):
    from vss.manual import REFUSE_UNVERIFIED
    doc = document([period(figures={
        "revenue": {"value": 100.0, "page": "1", "status": STATUS_VERIFIED,
                    "verified_kind": kind}})])
    parsed = parse(doc)
    assert parsed.periods[0].figures["revenue"].verified_kind == kind
    gate = section5_gate(parsed, as_of=AS_OF)
    assert not any(r.kind == REFUSE_UNVERIFIED for r in gate.refusals)
    assert f"VERIFIED ({kind})" in render_report(parsed, gate)


def test_E40_a_kind_on_an_unverified_figure_is_refused():
    with pytest.raises(ManualError, match="A kind is a property of a VERIFIED"):
        parse(document([period(figures={
            "revenue": {"value": 100.0, "page": "1", "status": STATUS_UNVERIFIED,
                        "verified_kind": "same_page"}})]))


def test_E40_an_unknown_kind_is_refused():
    with pytest.raises(ManualError, match="verified_kind must be one of"):
        parse(document([period(figures={
            "revenue": {"value": 100.0, "page": "1", "status": STATUS_VERIFIED,
                        "verified_kind": "vibes"}})]))


def test_E40_a_summed_flow_names_every_kind_it_stands_on():
    """Four quarters, two kinds: the input block says which."""
    doc = four_quarters()
    for i, p in enumerate(doc["periods"]):
        p["figures"]["operating_cash_flow"] = dict(figure(10.0))
        if i < 2:
            p["figures"]["operating_cash_flow"]["verified_kind"] = "cross_document"
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert "SUMMED, all VERIFIED (cross_document/same_page)" in render_report(parsed, gate)


def test_E40_synsam_carries_twenty_cross_document_flags_and_fifty_two_same_page():
    parsed = load_manual("SYNSAM.ST", directory=MANUAL_DIR)
    verified = [f for f in parsed.all_figures() if f.present and f.verified]
    kinds = {}
    for f in verified:
        kinds[f.verified_kind] = kinds.get(f.verified_kind, 0) + 1
    assert kinds == {"cross_document": 20, "same_page": 52}
    crossed = {f.name for f in verified if f.verified_kind == "cross_document"}
    assert crossed == {"revenue", "operating_income", "net_income",
                       "op_margin", "diluted_eps"}
    # the four cash-flow lines Method C reads are among the fifty-two
    for name in ("operating_cash_flow", "capex_ppe", "capex_intangibles",
                 "lease_payments_capital"):
        assert all(f.verified_kind == "same_page" for f in verified if f.name == name)


# --- E41: annual-only fields on a TTM basis, and a count never summed ------


def _annual(fy, end, **figures):
    return {"fiscal_year": fy, "period_end": end, "document": "Annual report",
            "figures": {k: figure(v) for k, v in figures.items()}}


def test_E41_an_annual_only_field_fills_from_a_year_end_inside_the_window():
    """SAP's shape: four quarters of flows, and FY2025 (ending inside the
    R12M to 2026-06-30) stating the diluted count and the equity-settled SBC
    that no interim states."""
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    doc["annual"] = [_annual(2025, "2025-12-31", sbc=40.0,
                             diluted_weighted_average_shares=1175.0)]
    parsed = parse(doc)
    basis = section5_basis(parsed)
    assert basis.kind == "ttm"
    assert basis.label == "TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2"   # the four, named
    shares = resolve_on_basis(parsed, basis, "diluted_weighted_average_shares")
    assert shares.value == 1175.0 and shares.state == RATIO_OK
    assert shares.end == date(2025, 12, 31) and "E41" in shares.source
    sbc = resolve_on_basis(parsed, basis, "sbc")
    assert sbc.value == 40.0 and "E41" in sbc.source
    # the basis READS the annual figure, so E21 gates on it too
    from vss.manual import basis_reads
    assert any(f.name == "sbc" for f in basis_reads(parsed, basis))


def test_E41_a_year_end_outside_the_window_is_still_another_twelve_months():
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    doc["annual"] = [_annual(2024, "2024-12-31", sbc=40.0)]
    parsed = parse(doc)
    got = resolve_on_basis(parsed, section5_basis(parsed), "sbc")
    assert got.value is None and got.state == QUALITY_BASIS_MISMATCH


def test_E41_a_flow_that_is_not_annual_only_is_not_filled():
    """E20 stands for everything but the named fields: an FY operating cash
    flow from a year inside the window is still another twelve months."""
    doc = four_quarters(each={"sbc": figure(1.0)})
    doc["annual"] = [_annual(2025, "2025-12-31", operating_cash_flow=1000.0)]
    parsed = parse(doc)
    got = resolve_on_basis(parsed, section5_basis(parsed), "operating_cash_flow")
    assert got.value is None and got.state == QUALITY_BASIS_MISMATCH


def test_E41_periods_first_still_governs_where_the_quarters_carry_the_field():
    """Pandora's shape: SBC in every quarter of the window is summed as the
    flow it is, and the annual entry is not consulted (E17)."""
    doc = four_quarters(each={"sbc": figure(10.0)})
    doc["annual"] = [_annual(2025, "2025-12-31", sbc=103.0)]
    parsed = parse(doc)
    got = resolve_on_basis(parsed, section5_basis(parsed), "sbc")
    assert got.value == 40.0 and len(got.components) == 4


def test_E41_B27_four_quarterly_averages_are_never_summed():
    """SYNSAM's 572,025,536: four quarterly averages added by HAND. Still
    never -- the resolver refuses the sum. What E91 (2026-08-30) licenses
    is different in kind: the CODED day-weighted average of the four
    stated operands, the window's own figure. Where the four are not all
    stated, E88's annual fall-back stands, dated and mismatch-flagged."""
    from vss.manual import (DIVISOR_WINDOW_DAY_WEIGHTED, share_count_on_basis,
                            share_divisor_on_basis)
    doc = four_quarters(each={"diluted_weighted_average_shares": figure(143_000_000)})
    parsed = parse(doc)
    basis = section5_basis(parsed)
    got = resolve_on_basis(parsed, basis, "diluted_weighted_average_shares")
    assert got.value is None and got.state == RATIO_MISSING
    assert "NOT their sum" in got.detail
    # E91: the coded day-weighted average of the stated operands -- not a
    # sum of averages, and not the resolver's doing
    divisor = share_divisor_on_basis(parsed, basis)
    assert divisor.count == pytest.approx(143_000_000)
    assert divisor.divisor_basis == DIVISOR_WINDOW_DAY_WEIGHTED
    # with one operand absent E91 cannot form; the annual entry inside the
    # window supplies the divisor, dated (E41 / E88)
    del doc["periods"][0]["figures"]["diluted_weighted_average_shares"]
    doc["annual"] = [_annual(2025, "2025-12-31",
                             diluted_weighted_average_shares=142_000_000)]
    parsed = parse(doc)
    count, why = share_count_on_basis(parsed, section5_basis(parsed))
    assert count == 142_000_000 and "E41" in why and "mismatch" in why   # E88


# =========================================================================
# E88 -- WHERE NO WEIGHTED AVERAGE EXISTS FOR THE WINDOW, THE MOST RECENT
# ANNUAL DILUTED AVERAGE IS THE DIVISOR; A WINDOW-END COUNT IS NEVER
# PROMOTED (2026-08-30; E75 / E75.1 REVERSED THE SAME DAY)
# =========================================================================


def test_E88_the_annual_average_stands_and_the_period_end_count_stays_memo():
    """Zinzino's shape under E88 (2026-08-30, reversing E75): an annual
    average from the year end inside the window and a stated count at the
    window end 4.36% higher after share issues -- no four-quarter diluted
    set, so E91 does not fire. The ANNUAL average is the divisor, dated on
    its own year end with the basis mismatch flagged; the window-end count
    is named as memo, never promoted."""
    from vss.manual import DIVISOR_WEIGHTED, share_count_on_basis, share_divisor_on_basis
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    doc["periods"][-1]["figures"]["shares_outstanding_period_end"] = figure(39_165_998)
    doc["annual"] = [_annual(2025, "2025-12-31",
                             diluted_weighted_average_shares=37_530_107)]
    parsed = parse(doc)
    basis = section5_basis(parsed)
    divisor = share_divisor_on_basis(parsed, basis)
    assert divisor.count == 37_530_107
    assert divisor.divisor_basis == DIVISOR_WEIGHTED
    assert divisor.as_of == date(2025, 12, 31) != basis.end
    assert divisor.prior_average is None and divisor.drift is None
    count, why = share_count_on_basis(parsed, basis)
    assert count == 37_530_107
    assert "E88" in why and "mismatch" in why
    assert "39,165,998" in why and "MEMO" in why and "never promoted" in why
    # the quarterly averages are still never summed, and the memo is never it
    got = resolve_on_basis(parsed, basis, "diluted_weighted_average_shares")
    assert got.value == 37_530_107 and "E41" in got.source


def test_E88_the_E16_pair_is_memo_and_no_annual_average_is_DATA_MISSING():
    """Betsson's shape at 2026-06-30: 139,635,838 issued less 4,330,556 in
    treasury, no net printed, no average anywhere. E88: the pair is never
    promoted, and with no annual average either the divisor is DATA
    MISSING -- the why names the pair as the memo it is."""
    from vss.manual import share_divisor_on_basis
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    doc["periods"][-1]["figures"]["shares_issued_period_end"] = figure(139_635_838)
    doc["periods"][-1]["figures"]["treasury_shares_period_end"] = figure(4_330_556)
    parsed = parse(doc)
    divisor = share_divisor_on_basis(parsed, section5_basis(parsed))
    assert divisor.count is None and divisor.divisor_basis is None
    assert "135,305,282" in divisor.why and "MEMO" in divisor.why
    assert "never promoted (E88)" in divisor.why


def test_E88_neither_a_basic_nor_a_diluted_period_end_count_is_promoted():
    """E88 (2026-08-30, reversing E75 / E75.1): a count at the window end,
    basic or diluted, is memo. With no annual average on the file the
    divisor is DATA MISSING; the why names what it refused to take."""
    from vss.manual import share_divisor_on_basis
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    doc["periods"][-1]["figures"]["shares_outstanding_period_end"] = figure(39_165_998)
    parsed = parse(doc)
    basic = share_divisor_on_basis(parsed, section5_basis(parsed))
    assert basic.count is None and basic.divisor_basis is None
    assert "39,165,998" in basic.why and "MEMO" in basic.why
    doc["periods"][-1]["figures"]["shares_diluted_period_end"] = figure(42_459_312)
    parsed = parse(doc)
    diluted = share_divisor_on_basis(parsed, section5_basis(parsed))
    assert diluted.count is None and diluted.divisor_basis is None
    assert "DILUTED count stated at the window end" in diluted.why
    assert "42,459,312" in diluted.why and "never promoted (E88)" in diluted.why
    # the fields remain counts: a zero is refused outright (E22, E25)
    from vss.manual import ZERO_REFUSED, STOCK_FIELDS
    assert "shares_diluted_period_end" in ZERO_REFUSED
    assert "shares_diluted_period_end" in STOCK_FIELDS


def test_E75_E38_still_governs_a_window_that_states_its_own_average():
    """A twelve-month period entry, or an annual entry closing on the basis
    end, keeps E38's weighted average even where a period-end count is
    stated beside it."""
    from vss.manual import DIVISOR_WEIGHTED, share_divisor_on_basis
    doc = document([period("2025-FY", figures={
        "diluted_weighted_average_shares": figure(1481.0),
        "shares_outstanding_period_end": figure(1500.0)})])
    parsed = parse(doc)
    divisor = share_divisor_on_basis(parsed, section5_basis(parsed))
    assert divisor.count == 1481.0 and divisor.divisor_basis == DIVISOR_WEIGHTED
    assert "E38" in divisor.why and "E75" not in divisor.why


def test_E88_the_annual_average_is_the_divisor_and_names_the_mismatch():
    """Pandora's and SAP's shape: the annual average stands, declared on
    its own date, the basis mismatch flagged (E88; before E88 this was
    E75's fallback case and gave the same answer)."""
    from vss.manual import DIVISOR_WEIGHTED, share_divisor_on_basis
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    doc["annual"] = [_annual(2025, "2025-12-31",
                             diluted_weighted_average_shares=1_175_000_000)]
    parsed = parse(doc)
    basis = section5_basis(parsed)
    divisor = share_divisor_on_basis(parsed, basis)
    assert divisor.count == 1_175_000_000
    assert divisor.divisor_basis == DIVISOR_WEIGHTED
    assert divisor.as_of == date(2025, 12, 31) != basis.end
    assert "E41" in divisor.why and "E88" in divisor.why
    assert "mismatch" in divisor.why


def test_E88_the_memo_is_still_never_the_divisor():
    from vss.manual import share_divisor_on_basis
    doc = four_quarters(each={"shares_point_in_time": figure(136_414_227)})
    parsed = parse(doc)
    divisor = share_divisor_on_basis(parsed, section5_basis(parsed))
    assert divisor.count is None and divisor.divisor_basis is None
    assert "E88" in divisor.why and "E38 admits no substitute" in divisor.why


def test_E91_four_stated_quarterly_diluted_counts_give_the_day_weighted_average():
    """SAP's shape (E91, 2026-08-30): the EPS footnotes state a diluted
    weighted average PER QUARTER; the divisor is the coded day-weighted
    average of the four stated operands -- the window's own average --
    superseding E88's annual fall-back for such issuers."""
    from vss.manual import DIVISOR_WINDOW_DAY_WEIGHTED, share_divisor_on_basis
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    for q, count in zip(doc["periods"], (1_172e6, 1_172e6, 1_168e6, 1_158e6)):
        q["figures"]["diluted_weighted_average_shares"] = figure(count)
    doc["annual"] = [_annual(2025, "2025-12-31",
                             diluted_weighted_average_shares=1_175_000_000)]
    parsed = parse(doc)
    basis = section5_basis(parsed)
    divisor = share_divisor_on_basis(parsed, basis)
    # (1,172 x 92d + 1,172 x 92d + 1,168 x 90d + 1,158 x 91d) / 365d
    assert divisor.count == pytest.approx(1_167_523_287.67, abs=0.5)
    assert divisor.divisor_basis == DIVISOR_WINDOW_DAY_WEIGHTED
    assert divisor.as_of == basis.end
    assert "E91" in divisor.why and "x 92d" in divisor.why
    assert len(divisor.figures) == 4


def test_E91_an_unverified_operand_refuses_the_gate():
    """The four quarterly counts are figures the divisor READS (E21/E40):
    an unverified one refuses section 5 -- the read set follows the chain,
    not the resolver's annual fill."""
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    counts = (1_172e6, 1_172e6, 1_168e6, 1_158e6)
    for q, count in zip(doc["periods"], counts):
        q["figures"]["diluted_weighted_average_shares"] = figure(count)
    doc["periods"][-1]["figures"]["diluted_weighted_average_shares"] = \
        figure(1_158e6, status="UNVERIFIED")
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert any(r.kind == "UNVERIFIED"
               and "diluted_weighted_average_shares" in r.subject
               for r in gate.refusals)


def test_E91_needs_all_four_quarters_else_E88_stands():
    from vss.manual import DIVISOR_WEIGHTED, share_divisor_on_basis
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    for q, count in zip(doc["periods"][:3], (1_172e6, 1_172e6, 1_168e6)):
        q["figures"]["diluted_weighted_average_shares"] = figure(count)
    doc["annual"] = [_annual(2025, "2025-12-31",
                             diluted_weighted_average_shares=1_175_000_000)]
    parsed = parse(doc)
    divisor = share_divisor_on_basis(parsed, section5_basis(parsed))
    assert divisor.count == 1_175_000_000
    assert divisor.divisor_basis == DIVISOR_WEIGHTED and "E88" in divisor.why


def test_E91_a_non_calendar_quarter_refuses_the_day_weighting():
    """A fiscal-basis quarter's bounds are not calendar month arithmetic;
    E91 does not guess them, and E88's annual fall-back stands."""
    from vss.manual import DIVISOR_WEIGHTED, share_divisor_on_basis
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    for q, count in zip(doc["periods"], (1_172e6, 1_172e6, 1_168e6, 1_158e6)):
        q["figures"]["diluted_weighted_average_shares"] = figure(count)
        q["period_basis"] = "fiscal"
    doc["annual"] = [_annual(2025, "2025-12-31",
                             diluted_weighted_average_shares=1_175_000_000)]
    parsed = parse(doc)
    divisor = share_divisor_on_basis(parsed, section5_basis(parsed))
    assert divisor.count == 1_175_000_000
    assert divisor.divisor_basis == DIVISOR_WEIGHTED and "E88" in divisor.why


def test_E41_a_twelve_month_period_entry_still_answers_with_its_own_count():
    doc = document([period("2025-FY", figures={
        "diluted_weighted_average_shares": figure(1481.0)})])
    parsed = parse(doc)
    got = resolve_on_basis(parsed, section5_basis(parsed),
                           "diluted_weighted_average_shares")
    assert got.value == 1481.0


def test_E41_synsam_no_longer_sums_its_four_quarterly_averages():
    """The B27 case on disk: 141,994,156-ish per quarter, and NO annual
    entry, so the divisor is DATA MISSING rather than 572,025,536."""
    parsed = load_manual("SYNSAM.ST", directory=MANUAL_DIR)
    got = resolve_on_basis(parsed, section5_basis(parsed),
                           "diluted_weighted_average_shares")
    assert got.value is None
    assert "NOT their sum" in got.detail


def test_E41_sap_de_stands_on_the_R12M_to_2026_06_30_named_quarter_by_quarter():
    parsed = load_manual("SAP.DE", directory=MANUAL_DIR)
    basis = section5_basis(parsed)
    assert basis.kind == "ttm" and basis.end == date(2026, 6, 30)
    assert basis.label == "TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2"
    ocf = resolve_on_basis(parsed, basis, "operating_cash_flow")
    assert ocf.value == 9_465_000_000 and len(ocf.components) == 4   # the workbook's R12M
    assert resolve_on_basis(parsed, basis, "cash_and_equivalents").value == 10_511_000_000
    assert resolve_on_basis(parsed, basis, "other_current_financial_assets").value == 1_114_000_000
    # the 20-F fills ONLY the annual-only fields, each dated 2025-12-31
    for name, value in (("diluted_weighted_average_shares", 1_175_000_000),
                        ("sbc", 1_331_000_000)):
        got = resolve_on_basis(parsed, basis, name)
        assert got.value == value and got.end == date(2025, 12, 31) and "E41" in got.source
    assert parsed.interest_in_ocf.value is False
    # 2026-08-30: what the statements state only cumulatively is on the
    # store as OPERANDS and the quarter is the code's difference (E86) --
    # the four quarters sum to the window's -735,000,000; the borrowing legs
    # are note (E.2)'s ex-lease operands (E84)
    capex = resolve_on_basis(parsed, basis, "capex_combined")
    assert capex.value == -735_000_000 and len(capex.components) == 4
    assert parsed.periods[0].figures["capex_combined"].cumulative == -559_000_000
    assert resolve_on_basis(parsed, basis, "financial_liabilities_noncurrent").value == 7_087_000_000
    # the 2026-08-30 entries were confirmed at the owner's read-back the
    # same evening, so the gate refused nothing -- until E117 (2026-09-19):
    # SAP never isolates its lease interest, so FCF0 is DATA MISSING on the
    # lease legs (UNVERIFIED UNDER E117) and E108's measured exemption of the
    # minority-dividend quarters lapses with it; the report names every kind
    gate = section5_gate(parsed, as_of=AS_OF)
    # A3 (2026-09-19): lease interest E106-bounded -- the tolerance is the refusal
    assert {r.kind for r in gate.refusals} == {"UNDETERMINED LEGS PAST E106"}
    report = render_report(parsed, gate)
    assert "BASIS: `TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2`" in report
    assert "VERIFIED (cross_document)" in report and "VERIFIED (tagged)" in report


# --- Build 2 item 7: the three Nordic files, filled ------------------------


def test_item_7_sbc_zero_needs_evidence_like_any_flattering_zero():
    from vss.manual import ZERO_NEEDS_BASIS
    assert "sbc" in ZERO_NEEDS_BASIS
    with pytest.raises(ManualError, match="sbc is zero and carries no zero_basis"):
        parse(document([period(figures={"sbc": figure(0)})]))
    parsed = parse(document([period(figures={
        "sbc": {"value": 0, "page": "p.96", "status": STATUS_VERIFIED,
                "zero_basis": "note"}})]))
    assert parsed.periods[0].figures["sbc"].value == 0


def test_item_7_pandora_is_post_interest_and_its_sbc_sits_on_the_window():
    from vss.manual import FCF0_RATIO, resolve_or_subtract
    parsed = load_manual("PNDORA.CO", directory=MANUAL_DIR)
    assert parsed.interest_in_ocf.value is True
    assert "p.103" in parsed.interest_in_ocf.page
    basis = section5_basis(parsed)
    sbc = resolve_on_basis(parsed, basis, "sbc")
    assert sbc.value == 48.0 and len(sbc.components) == 4          # 51 - 11 - 11 + 19
    assert all(f.verified_kind == "cross_document" for f in sbc.figures)
    assert resolve_or_subtract(parsed, basis, "net_interest_paid") == 861.0   # 1,028 - 167
    gate = section5_gate(parsed, as_of=AS_OF)
    # E117 (2026-09-19): Pandora's lease interest is not on the store, so
    # FCF0 is input missing ON THE LEASE LEGS ALONE -- post-interest and SBC
    # on the window, as above, are untouched
    # B1 (2026-09-19): Pandora's lease interest is on file (E86 differences
    # of the stated year-to-date "Interest payments"), so FCF0 forms
    fcf0 = next(r for r in gate.ratios if r.name == FCF0_RATIO)
    assert fcf0.state != RATIO_MISSING
    # 2026-09-04, the E110 sweep: Pandora's net-debt legs were read and the
    # gate's answer CHANGED FROM "absent" TO "too big". `prepaid_delivery_
    # obligation` is now the stated 225 (its own interim caption, refund
    # liabilities shown apart) and `pension_deficit` is an E106 clause 3
    # BOUND at 556 -- total provisions -- which moves fv_base by 9.27%,
    # past the 3.5%. The name refuses, and it refuses on SIZE.
    from vss.manual import REFUSE_TOLERANCE
    assert gate.refused
    assert REFUSE_TOLERANCE in {r.kind for r in gate.refusals}
    # the annual 103 = the appendix's four 2025 quarters, and E17 keeps the
    # quarters first: the annual figure is not what the basis reads
    assert parsed.annual[-1].figures["sbc"].value == 103.0


def test_item_7_betsson_is_post_interest_but_its_interest_pair_is_annual_only():
    """Filled as ruled; and honest about what it does not reach. The AR
    states the pair beneath the cash flow statement; on the quarterly basis
    it is another twelve months and E41 does not list interest, so FCF0 is
    DATA MISSING with that reason -- not zero, not the annual figure."""
    from vss.manual import FCF0_RATIO, REFUSE_NO_FCF0, resolve_or_subtract
    parsed = load_manual("BETS-B.ST", directory=MANUAL_DIR)
    assert parsed.interest_in_ocf.value is True and "p.117" in parsed.interest_in_ocf.page
    basis = section5_basis(parsed)
    assert resolve_on_basis(parsed, basis, "sbc").value == 1.3       # E41, equity-settled
    assert resolve_or_subtract(parsed, basis, "net_interest_paid") is None
    gate = section5_gate(parsed, as_of=AS_OF)
    assert REFUSE_NO_FCF0 in {r.kind for r in gate.refusals}
    state = next(r for r in gate.ratios if r.name == FCF0_RATIO)
    assert state.state == RATIO_MISSING and "net_interest_paid" in state.detail


def test_item_7_lindab_has_a_store_file_and_it_reaches_FCF0():
    """No store file existed for LIAB.ST before Build 2; the first
    re-strike ran on hand inputs. Now the four quarters, the interest
    classification and the FY2025 annual-only fields are on the file."""
    from vss.manual import FCF0_RATIO, resolve_or_subtract, share_count_on_basis
    parsed = load_manual("LIAB.ST", directory=MANUAL_DIR)
    assert parsed.origin == "manual" and parsed.reporting_currency == "SEK"
    assert parsed.interest_in_ocf.value is True and "p.17" in parsed.interest_in_ocf.page
    basis = section5_basis(parsed)
    assert basis.label == "TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2"
    assert resolve_on_basis(parsed, basis, "operating_cash_flow").value == 1176.0
    assert resolve_or_subtract(parsed, basis, "net_interest_paid") == 201.0     # 211 - 10
    assert resolve_on_basis(parsed, basis, "capex_intangibles").value == -142.0
    assert resolve_on_basis(parsed, basis, "capex_ppe").value == -185.0
    sbc = resolve_on_basis(parsed, basis, "sbc")
    assert sbc.value == 0.0 and sbc.figures[0].zero_basis == "note" and "E41" in sbc.source
    # E88 (2026-08-30, reversing E75): the ANNUAL average is the divisor;
    # Lindab's FY2025 average 77.036 equals the count at 2026-06-30, so the
    # value is unchanged and the window-end count is named as memo.
    from vss.manual import DIVISOR_WEIGHTED, share_divisor_on_basis
    count, why = share_count_on_basis(parsed, basis)
    assert count == 77.036 and "E88" in why and "MEMO" in why
    divisor = share_divisor_on_basis(parsed, basis)
    assert divisor.divisor_basis == DIVISOR_WEIGHTED
    assert divisor.prior_average is None and divisor.drift is None
    assert divisor.as_of == date(2025, 12, 31) != basis.end
    assert resolve_on_basis(parsed, basis, "cash_and_equivalents").value == 527.0  # not 506
    assert resolve_on_basis(parsed, basis, "lease_liabilities").value == 1410.0
    # E117 (2026-09-19): Lindab states no quarterly lease interest. The
    # owner's A2 ruling bounds each quarter's by its stated interest paid
    # (E106): FCF0 FORMS with the leg at zero, and the gate refuses on the
    # TOLERANCE -- 211 of bound moves fv_base far past 3.5%
    # E120 (2026-09-19): note 30's FY2025 lease interest (66) STANDS IN for
    # the window, the bound is dropped, and the gate refuses NOTHING
    gate = section5_gate(parsed, as_of=AS_OF)
    assert not gate.refused, [r.kind for r in gate.refusals]
    fcf0 = next(r for r in gate.ratios if r.name == FCF0_RATIO)
    assert fcf0.state != RATIO_MISSING
    from vss.valuation import free_cash_flow_zero
    assert free_cash_flow_zero(operating_cash_flow=1176.0, capex=-327.0,
                               interest_in_ocf=True, net_interest_paid=201.0,
                               sbc=0.0,
                               # E105: Lindab's leg is a searched zero on
                               # every quarter of the window.
                               nci_dividends_paid=0.0) == 1050.0
    # E35's legs plus E35.1's pension leg (item 8): 5 + 3,378 + 1,410 + 280
    # - 527 - 10 = 4,536. Lindab's own 4,497 also nets 39 of non-current
    # assets. E68 (2026-08-29) added the asset-retirement leg; E68.1 the
    # same day put a caption-based zero on the file's FY2025 annual entry
    # (no decommissioning provision on the balance sheet), so the leg
    # resolves through E41 and the store reaches 4,536 again.
    # E117 (2026-09-19): the 1,410 IFRS 16 liability LEAVES net debt -- 3,126
    assert M_net_debt(parsed, basis) == 3126.0
    assert resolve_on_basis(parsed, basis, "asset_retirement_obligation").value == 0.0


def M_net_debt(parsed, basis):
    from vss.manual import net_debt_on_basis
    return net_debt_on_basis(parsed, basis)[0]


def test_item_7_every_figure_the_basis_reads_carries_a_page_and_a_kind():
    """Every present figure has a page; every figure THE BASIS READS is
    VERIFIED with its E40 kind, OR is VERIFIED-EXEMPT under E108 -- in
    which case IT STILL CARRIES ITS PAGE, because the floor waives the
    READ-BACK and never the provenance. Pandora's quarters outside the
    window stay UNVERIFIED by design (E21 names them and does not gate)."""
    from vss.manual import (FLAG_EXEMPT, basis_reads,
                            registered_view_sensitivity, section5_gate)
    for ticker in ("PNDORA.CO", "BETS-B.ST", "LIAB.ST"):
        parsed = load_manual(ticker, directory=MANUAL_DIR)
        for fig in parsed.all_figures():
            if fig.present:
                assert fig.page, (ticker, fig.name, fig.period)
        basis = section5_basis(parsed)
        gate = section5_gate(
            parsed, as_of=date(2026, 9, 4),
            measured_exempt=registered_view_sensitivity(parsed))
        exempt = {f.subject for f in gate.flags if f.kind == FLAG_EXEMPT}
        for fig in basis_reads(parsed, basis):
            if f"{fig.period or 'market'} {fig.name}" in exempt:
                # E108: no read-back, and the page is still required.
                assert fig.page, (ticker, fig.name, fig.period)
                continue
            if fig.source and "2026-09-04" in fig.source:
                # ENTERED TODAY and not yet read back. E21 names it and the
                # gate refuses on it; what this test holds is that nothing
                # OLDER slipped in unverified.
                assert fig.page, (ticker, fig.name, fig.period)
                continue
            assert fig.verified and fig.verified_kind, (ticker, fig.name, fig.period)


# --- E35.1: the pension deficit is a leg of net debt ----------------------


def _bridge_file(**figures):
    base = {"financial_liabilities_current": 600.0,
            "financial_liabilities_noncurrent": 2783.0,
            "lease_liabilities": 1410.0, "cash_and_equivalents": 506.0,
            "other_current_financial_assets": 70.0}
    base.update(figures)
    figs = {k: figure(v) for k, v in base.items()}
    figs.setdefault("asset_retirement_obligation", zero_figure())    # E68
    figs.setdefault("prepaid_delivery_obligation", zero_figure())    # E81
    return document([period(figures=figs)], interest_in_ocf=INTEREST_YES)


def test_E35_1_lindab_shaped_inputs_reach_4497():
    """The components the first re-strike used: E35's four legs gave 4,217
    and Lindab's own net debt was 4,497; the 280 was the pension provision."""
    from vss.manual import net_debt_on_basis
    parsed = parse(_bridge_file(pension_deficit=280.0))
    total, why = net_debt_on_basis(parsed, section5_basis(parsed))
    # E117 (2026-09-19): 4,497 with the 1,410 IFRS 16 liability, 3,087 out.
    assert total == 3087.0
    assert "pension deficit 280 (E35.1)" in why


def test_E35_1_an_absent_pension_deficit_is_DATA_MISSING_for_net_debt():
    from vss.manual import NET_DEBT_LEGS, net_debt_on_basis
    assert "pension_deficit" in NET_DEBT_LEGS
    parsed = parse(_bridge_file())
    total, why = net_debt_on_basis(parsed, section5_basis(parsed))
    assert total is None and "pension_deficit" in why
    gate = section5_gate(parsed, as_of=AS_OF)
    assert next(r for r in gate.ratios if r.name == "net debt").state == RATIO_MISSING


def test_E35_1_a_zero_pension_deficit_needs_evidence():
    with pytest.raises(ManualError, match="pension_deficit is zero and carries no zero_basis"):
        parse(_bridge_file(pension_deficit=0))


def test_E35_1_pension_deficit_is_a_stock_and_annual_only():
    from vss.manual import ANNUAL_ONLY_FIELDS, STOCK_FIELDS, ZERO_NEEDS_BASIS
    assert "pension_deficit" in STOCK_FIELDS
    assert "pension_deficit" in ANNUAL_ONLY_FIELDS
    assert "pension_deficit" in ZERO_NEEDS_BASIS


def test_E68_1_lindab_store_file_reaches_4536_through_a_caption_zero_on_the_new_leg():
    """E68 (2026-08-29) made the asset-retirement obligation a required leg
    and, for a few hours, this file's net debt was DATA MISSING on it. E68.1
    the same day: a business that owns nothing requiring decommissioning
    takes a caption-based zero, cited to the balance sheet and note 27 --
    entered on the FY2025 annual entry, reached through E41 -- and the
    store reaches 4,536 again (5 + 3,378 + 1,410 + 280 + 0 - 527 - 10),
    with the leg named in the sentence."""
    from vss.manual import net_debt_on_basis
    parsed = load_manual("LIAB.ST", directory=MANUAL_DIR)
    total, why = net_debt_on_basis(parsed, section5_basis(parsed))
    assert total == 3126.0      # E117: 4,536 less the 1,410 of leases that left
    assert "asset retirement obligations 0 (E68)" in why
    assert "pension ASSET is not netted" in why
    text = Path(MANUAL_DIR / "LIAB.ST.yaml").read_text(encoding="utf-8")
    assert "Lindab's own 4,497 also nets 39 of non-current" in text
    assert "zero_basis: caption" in text and "E68.1" in text


# --- E68: the asset retirement obligation is a leg of net debt ------------


def test_E68_an_absent_asset_retirement_obligation_is_DATA_MISSING_for_net_debt():
    from vss.manual import NET_DEBT_LEGS, net_debt_on_basis
    assert "asset_retirement_obligation" in NET_DEBT_LEGS
    doc = _bridge_file(pension_deficit=280.0)
    del doc["periods"][0]["figures"]["asset_retirement_obligation"]
    parsed = parse(doc)
    total, why = net_debt_on_basis(parsed, section5_basis(parsed))
    assert total is None and "asset_retirement_obligation" in why
    gate = section5_gate(parsed, as_of=AS_OF)
    assert next(r for r in gate.ratios if r.name == "net debt").state == RATIO_MISSING


def test_E68_the_leg_adds_to_net_debt_and_the_sentence_names_it():
    from vss.manual import net_debt_on_basis
    parsed = parse(_bridge_file(pension_deficit=280.0, asset_retirement_obligation=724.0))
    total, why = net_debt_on_basis(parsed, section5_basis(parsed))
    assert total == 3087.0 + 724.0   # E117: the 1,410 of leases are out
    assert "asset retirement obligations 724 (E68)" in why


def test_E68_a_zero_asset_retirement_obligation_needs_evidence():
    with pytest.raises(ManualError, match="asset_retirement_obligation is zero and carries no zero_basis"):
        parse(_bridge_file(pension_deficit=280.0, asset_retirement_obligation=0))


def test_E68_the_leg_is_a_stock_and_annual_only():
    from vss.manual import ANNUAL_ONLY_FIELDS, STOCK_FIELDS, ZERO_NEEDS_BASIS
    assert "asset_retirement_obligation" in STOCK_FIELDS
    assert "asset_retirement_obligation" in ANNUAL_ONLY_FIELDS
    assert "asset_retirement_obligation" in ZERO_NEEDS_BASIS


def test_E35_1_sap_carries_the_tagged_pension_liability_and_E41_dates_it():
    parsed = load_manual("SAP.DE", directory=MANUAL_DIR)
    basis = section5_basis(parsed)
    got = resolve_on_basis(parsed, basis, "pension_deficit")
    assert got.value == 249_000_000 and got.end == date(2025, 12, 31)
    assert "E41" in got.source
    fig = got.figures[0]
    assert fig.verified_kind == "tagged" and "RecognisedLiabilitiesDefinedBenefitPlan" in fig.page


# =========================================================================
# E60 -- A FIELD NO METHOD READS DOES NOT BLOCK SECTION 5
# =========================================================================
#
# AUTO.L's shape: `interest_in_ocf: no`, and `finance_costs_paid` /
# `income_tax_paid` / `proceeds_from_disposals_ppe` all UNVERIFIED. The
# refusal table used to be built from FieldSpec.reads alone (unconditional);
# `basis_reads` now asks `interest_legs` / `unread_by_e60` which legs THIS
# file's chain actually builds, the same functions E23/E34 already use to
# choose a ratio's legs.


def test_income_tax_paid_and_disposal_proceeds_never_block_section_5():
    """Neither field is a parameter of `free_cash_flow_zero` under any
    `interest_in_ocf` value -- confirmed by search, not merely declared --
    so an UNVERIFIED entry for either is named and never refuses."""
    from vss.manual import NEVER_A_SECTION5_LEG
    assert NEVER_A_SECTION5_LEG == {"income_tax_paid", "proceeds_from_disposals_ppe"}
    doc = _fcf0_file(INTEREST_NO, income_tax_paid=-95.2,
                     proceeds_from_disposals_ppe=4.5)
    for name in ("income_tax_paid", "proceeds_from_disposals_ppe"):
        doc["periods"][0]["figures"][name]["status"] = STATUS_UNVERIFIED
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert not gate.refused
    assert gate.blocking == ()
    assert {f.name for f, _ in gate.unread} == {
        "income_tax_paid", "proceeds_from_disposals_ppe"}
    for _, why in gate.unread:
        assert "no live code path ever resolves it" in why


def test_finance_costs_paid_does_not_block_where_interest_sits_outside_ocf():
    """AUTO.L's own case: `interest_in_ocf: no` means FCF0 never forms
    `net_interest_paid`, so `finance_costs_paid` -- one of its two E18
    operands -- is not something a run relying on FCF0 can be wrong about."""
    from vss.manual import FCF0_RATIO
    doc = _fcf0_file(INTEREST_NO, finance_costs_paid=2.8)
    doc["periods"][0]["figures"]["finance_costs_paid"]["status"] = STATUS_UNVERIFIED
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert not gate.refused
    assert gate.blocking == ()
    assert [f.name for f, _ in gate.unread] == ["finance_costs_paid"]
    assert "interest_in_ocf: no" in gate.unread[0][1]
    assert next(r for r in gate.ratios if r.name == FCF0_RATIO).state == RATIO_OK


def test_flipping_interest_in_ocf_to_yes_puts_finance_costs_paid_back_in_the_read_set():
    """E60's guard: the read set follows the arithmetic, not a fixed
    excused list. The SAME unverified `finance_costs_paid` that does not
    block above blocks HERE, because `interest_in_ocf: yes` makes
    `net_interest_paid` -- and `finance_costs_paid`, its own E18 operand --
    a leg FCF0 actually needs (E34, `test_the_add_back_may_come_from_E18_s_
    two_halves` above)."""
    from vss.manual import FCF0_RATIO
    doc = _fcf0_file(INTEREST_YES, finance_costs_paid=2.8,
                     finance_income_received=1.3)
    doc["periods"][0]["figures"]["finance_costs_paid"]["status"] = STATUS_UNVERIFIED
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert gate.refused
    assert [f.name for f in gate.blocking] == ["finance_costs_paid"]
    detail = next(r for r in gate.refusals if r.kind == "UNVERIFIED").detail
    assert "READS it" in detail
    assert next(r for r in gate.ratios if r.name == FCF0_RATIO).state == RATIO_OK


def test_the_accrual_proxy_shape_reads_its_own_operands_not_the_cash_ones():
    """E34.1: an accrual-proxy filer's FCF0 add-back is `net_finance_costs`,
    off `finance_costs_period` / `finance_income_period` -- never
    `finance_costs_paid` / `finance_income_received`, which such a filer
    cannot form. An unverified cash-side operand entered anyway (e.g. from
    a different note) does not block; an unverified income-statement-side
    operand does."""
    doc = _fcf0_file(INTEREST_YES_ACCRUAL, finance_costs_period=1149.0,
                     finance_income_period=279.0, finance_costs_paid=1009.0)
    doc["periods"][0]["figures"]["finance_costs_paid"]["status"] = STATUS_UNVERIFIED
    parsed = parse(doc)
    gate = section5_gate(parsed, as_of=AS_OF)
    assert not gate.refused
    assert gate.blocking == ()

    doc2 = _fcf0_file(INTEREST_YES_ACCRUAL, finance_costs_period=1149.0,
                      finance_income_period=279.0)
    doc2["periods"][0]["figures"]["finance_costs_period"]["status"] = STATUS_UNVERIFIED
    gate2 = section5_gate(parse(doc2), as_of=AS_OF)
    assert gate2.refused
    assert [f.name for f in gate2.blocking] == ["finance_costs_period"]


def test_net_finance_costs_and_its_own_operands_always_read_for_the_coverage_gate():
    """Regardless of which shape FCF0 chose -- or whether interest is
    classified at all -- E25's zero-coverage-denominator gate reads
    `net_finance_costs` directly, outside FCF0 entirely, so it and its own
    E18 operands never drop out of the read set."""
    from vss.manual import interest_read_names
    for interest in (INTEREST_NO, INTEREST_YES, None):
        doc = _fcf0_file(interest, net_finance_costs=3.9)
        names = interest_read_names(parse(doc))
        assert {"net_finance_costs", "finance_costs_period",
                "finance_income_period"} <= names
    doc = _fcf0_file(INTEREST_NO, net_finance_costs=3.9)
    doc["periods"][0]["figures"]["net_finance_costs"]["status"] = STATUS_UNVERIFIED
    gate = section5_gate(parse(doc), as_of=AS_OF)
    assert gate.refused
    assert [f.name for f in gate.blocking] == ["net_finance_costs"]


# --- E68.1 / E69 (2026-08-29): the applications on the committed files ---


def test_E68_1_and_E69_applications_on_the_committed_files():
    """AUTO.L carries a dilapidations provision (E69, 3.7); CTSH, LIAB.ST and
    AOS carry caption-based zeros (E68.1); LII stays refused as heavy
    industrial. AOS's stated interest expense is on the file and its
    interest income is nowhere in the filing, so FCF0 stays refused."""
    from vss.manual import net_debt_on_basis
    # E117 (2026-09-19): each less the lease liability that LEFT net debt --
    # AUTO.L 42.6 and LIAB.ST 1,410 (IFRS 16, whole), AOS 47.9m and CTSH
    # 576m (US operating; CTSH's 22m of finance leases stay). E68 / E69's
    # own legs are untouched: 191.5 / 4,536 / 35.8m / -467m before.
    # C3 (2026-09-19): AOS's short-term investments 18.7m now on file -> -30.8m
    expect = {"AUTO.L": 148.9, "LIAB.ST": 3126.0, "AOS": -30_800_000.0,
              "CTSH": -1_056_000_000.0}   # 2026-09-19: + short-term investments 13m on file
    for ticker, total in expect.items():
        parsed = load_manual(ticker, directory=MANUAL_DIR)
        basis = section5_basis(parsed)
        got, why = net_debt_on_basis(parsed, basis)
        assert got == pytest.approx(total), (ticker, why)
        aro = resolve_on_basis(parsed, basis, "asset_retirement_obligation")
        fig = aro.figures[0]
        assert fig.verified_kind == "same_page", ticker
        if ticker == "AUTO.L":
            assert aro.value == 3.7 and "Dilapidations provision" in fig.page
        else:
            assert aro.value == 0 and fig.zero_basis == "caption", ticker
    parsed = load_manual("AOS", directory=MANUAL_DIR)
    basis = section5_basis(parsed)
    costs = resolve_on_basis(parsed, basis, "finance_costs_period")
    assert costs.value == 13_500_000 and "'Interest expense | 13.5'" in costs.figures[0].page
    assert resolve_on_basis(parsed, basis, "finance_income_period").value is None
    assert resolve_on_basis(parsed, basis, "net_finance_costs").value is None



# --- E68.2 / E61.1 (2026-08-30): LII's named zero, AOS's hand-applied proxy


def test_E68_2_lii_takes_a_caption_zero_with_the_remediation_accrual_named_and_the_bridge_completes():
    from vss.manual import FCF0_RATIO, RATIO_OK, net_debt_on_basis
    parsed = load_manual("LII", directory=MANUAL_DIR)
    basis = section5_basis(parsed)
    aro = resolve_on_basis(parsed, basis, "asset_retirement_obligation")
    fig = aro.figures[0]
    assert aro.value == 0 and fig.zero_basis == "caption" and fig.verified_kind == "same_page"
    assert "Note 5" in fig.page and "10.9" in fig.page and "asbestos" in fig.page
    assert "E68.2" in fig.page
    total, why = net_debt_on_basis(parsed, basis)
    # 244.3 + 1,144.1 + 18.7 + 0 - 34.2: the 382.3 operating lease liability
    # LEAVES net debt (E117, 2026-09-19); 1,755.2 with it
    assert total == pytest.approx(1_372_400_000)   # C3: - short-term investments 0.5m
    assert "asset retirement obligations 0 (E68)" in why
    states = {r.name: r.state for r in section5_gate(parsed, as_of=AS_OF).ratios}
    assert states["net debt"] == RATIO_OK and states[FCF0_RATIO] == RATIO_OK


def test_E61_1_aos_takes_the_interest_expense_only_proxy_by_hand_and_prints_the_bound():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from vss import runrecord as R
    from vss.manual import FCF0_RATIO, RATIO_MISSING, RATIO_OK
    parsed = load_manual("AOS", directory=MANUAL_DIR)
    assert parsed.interest_in_ocf.interest_expense_only_proxy
    basis = section5_basis(parsed)
    gate = section5_gate(parsed, as_of=AS_OF)
    # E70: the flow bears the lease payments and the 10-K states no cash
    # paid. Until 2026-09-04 the gate refused on FCF0 DATA MISSING; under
    # E106 clause 3 the leg is now BOUNDED at the issuer's own total lease
    # expense, the ratio forms, and the refusal was the TOLERANCE -- 23.2m
    # moved fv_base by 4.27%, past E106's 3.5%. E117 (2026-09-19): rent is
    # an operating cost, the payment is no longer read, its bound bounds
    # nothing, and the gate REFUSES NOTHING. The interest proxy is
    # unaffected throughout, which is what this test is about.
    assert gate.refusals == ()
    states = {r.name: r.state for r in gate.ratios}
    assert states[FCF0_RATIO] != RATIO_MISSING and states["net debt"] == RATIO_OK
    record = R.from_store(
        parsed, basis, run_ts=datetime(2026, 8, 30, tzinfo=ZoneInfo("UTC")),
        growth=R.Growth(base=0.03, view_file="TEST FIXTURE: no growth view is registered for AOS"),
        hand_inputs=(R.Input("operating_lease_payments", 0.0,
                             "TEST FIXTURE: a hand zero so the interest proxy can "
                             "be read; AOS's payment is NOT nil (E70)", "hand"),))
    # OCF 616.8 - capex 70.8 - SBC 13.8 + interest expense 13.5 (+ lease 0 by the fixture)
    assert record.fcf0() == pytest.approx(545_700_000)
    assert record.interest.net_interest_paid == 13_500_000
    # E117: the 47.9m operating lease liability LEAVES net debt (35.8m with it)
    assert record.bridge.net_debt == pytest.approx(-30_800_000)   # C3: - short-term investments 18.7m
    rendered = record.render()
    assert "E61" in rendered and "bound: 2.5% of FCF0" in rendered



# --- E70 (2026-08-30): a lease is counted once, in net debt, never also in the flow


def test_E70_the_lease_declaration_is_parsed_and_absent_is_DATA_MISSING_not_no():
    from vss.manual import (FCF0_RATIO, LEASE_UNCLASSIFIED, lease_legs,
                            REFUSE_LEASES_UNCLASSIFIED)
    parsed = parse(_bridge_file(pension_deficit=280.0, operating_cash_flow=1000.0,
                                capex_combined=-100.0, sbc=1.0))
    # E117 (2026-09-19): an IFRS 16 file's FCF0 reads its principal AND its
    # lease interest -- E70's `()` (nothing added back) is gone
    assert parsed.operating_leases_in_ocf.value is False
    assert lease_legs(parsed) == ("lease_payments_capital", "lease_interest_paid")
    doc = _bridge_file(pension_deficit=280.0, operating_cash_flow=1000.0,
                       capex_combined=-100.0, sbc=1.0)
    del doc["operating_leases_in_ocf"]
    silent = parse(doc)
    assert silent.operating_leases_in_ocf is None
    assert lease_legs(silent) == (LEASE_UNCLASSIFIED,)
    gate = section5_gate(silent, as_of=AS_OF)
    assert any(r.kind == REFUSE_LEASES_UNCLASSIFIED for r in gate.refusals)
    assert {r.name: r for r in gate.ratios}[FCF0_RATIO].state == RATIO_MISSING
    bad = _bridge_file()
    bad["operating_leases_in_ocf"] = {"value": "maybe", "source": "x", "page": "1"}
    with pytest.raises(ManualError, match="value must be yes or no"):
        parse(bad)
    bad["operating_leases_in_ocf"] = {"value": True}
    with pytest.raises(ManualError, match="source and page are both required"):
        parse(bad)


def test_E117_a_us_shape_reads_no_lease_flow_and_takes_its_operating_liability_out():
    """E117 (2026-09-19), replacing E70's add-back test: a US filer's flow
    already bears the rent, so FCF0 reads NO lease field; its operating
    lease liability LEAVES net debt and the finance part of the lease line
    STAYS. Without the operating figure net debt is DATA MISSING, never the
    whole liability by default."""
    from vss.manual import FCF0_RATIO, lease_legs, net_debt_on_basis
    doc = _bridge_file(pension_deficit=280.0, operating_cash_flow=1000.0,
                       capex_combined=-100.0, sbc=1.0, net_interest_paid=10.0,
                       operating_lease_liabilities=1300.0)
    doc["operating_leases_in_ocf"] = LEASES_YES
    parsed = parse(doc)
    assert lease_legs(parsed) == ()
    states = {r.name: r for r in section5_gate(parsed, as_of=AS_OF).ratios}
    assert states[FCF0_RATIO].state == RATIO_OK
    total, why = net_debt_on_basis(parsed, section5_basis(parsed))
    # 600 + 2,783 + (1,410 - 1,300 finance leases kept) + 280 - 506 - 70
    assert total == pytest.approx(3197.0)
    assert "finance leases 110" in why and "LEAVES net debt" in why
    del doc["periods"][0]["figures"]["operating_lease_liabilities"]
    states = {r.name: r for r in section5_gate(parse(doc), as_of=AS_OF).ratios}
    assert states["net debt"].state == RATIO_MISSING
    assert "operating_lease_liabilities" in states["net debt"].detail


def test_E117_an_ifrs_shape_deducts_principal_and_lease_interest_and_refuses_without_either():
    from vss.manual import FCF0_RATIO
    from vss.valuation import ValuationError, free_cash_flow_zero
    common = dict(operating_cash_flow=1000.0, capex=-100.0, interest_in_ocf=True,
                  net_interest_paid=10.0, sbc=1.0, nci_dividends_paid=0.0,
                  operating_leases_in_ocf=False, lease_rule="E117")
    # 1,000 - 100 - 1 + 10 - (27 principal + 4.5 lease interest)
    assert free_cash_flow_zero(**common, lease_cash_paid=31.5) == pytest.approx(877.5)
    with pytest.raises(ValuationError, match="upper bound"):
        free_cash_flow_zero(**common, lease_cash_paid=None)
    # E70's replay path is untouched: nothing deducted
    assert free_cash_flow_zero(**{**common, "lease_rule": "E70"}) == pytest.approx(909.0)
    doc = _bridge_file(pension_deficit=280.0, operating_cash_flow=1000.0,
                       capex_combined=-100.0, sbc=1.0, net_interest_paid=10.0,
                       lease_payments_capital=-27.0)
    doc["periods"][0]["figures"].pop("lease_interest_paid", None)
    states = {r.name: r for r in section5_gate(parse(doc), as_of=AS_OF).ratios}
    assert states[FCF0_RATIO].state == RATIO_MISSING
    assert "lease_interest_paid" in states[FCF0_RATIO].detail


def test_E70_applications_on_the_committed_files():
    """Every file declares the treatment; the five US filers that tag the
    payment carry it; AOS declares `yes` and tags no payment, so its FCF0
    is DATA MISSING on that leg; every IFRS file is unchanged."""
    from vss.manual import FCF0_RATIO
    for t, expect in (("LII", 90_600_000.0), ("CTSH", 192_000_000.0), ("NKE", 668_000_000.0),
                      ("DECK", 92_823_000.0), ("EXE", 32_000_000.0)):
        parsed = load_manual(t, directory=MANUAL_DIR)
        assert parsed.operating_leases_in_ocf.value is True
        basis = section5_basis(parsed)
        got = resolve_on_basis(parsed, basis, "operating_lease_payments")
        assert got.value == expect, (t, got.value)
        assert "us-gaap:OperatingLeasePayments" in got.figures[0].page
    # AOS declares `yes` and tags no payment. Until 2026-09-04 that made
    # its FCF0 INPUT MISSING; under E106 clause 3 the leg is now BOUNDED
    # from the issuer's own lease note, so the RATIO forms -- and the gate
    # refuses on the TOLERANCE instead, which is a different and better
    # refusal: it says how much is at stake rather than that something is
    # absent.
    # E117 (2026-09-19): the payment is no longer read, so the bound on it
    # bounds nothing and AOS's gate REFUSES NOTHING -- the stated payments
    # above stay on the files as memo of what E70 added back.
    aos = load_manual("AOS", directory=MANUAL_DIR)
    assert aos.operating_leases_in_ocf.value is True
    gate = section5_gate(aos, as_of=AS_OF)
    states = {r.name: r for r in gate.ratios}
    assert states[FCF0_RATIO].state != RATIO_MISSING
    assert not gate.refused, [r.kind for r in gate.refusals]
    for t in ("AUTO.L", "LIAB.ST", "PNDORA.CO", "BETS-B.ST", "SYNSAM.ST", "SAP.DE"):
        parsed = load_manual(t, directory=MANUAL_DIR)
        assert parsed.operating_leases_in_ocf.value is False, t


# --- E78 (2026-08-30): a caption zero standing on a clear sentence is
# VERIFIED as `caption_statement`, without a second document


def _statement_zero(*, value=0.0, zero_basis="note", statement="The Group companies only have defined contribution pension plans.", kind="caption_statement"):
    fig = {"value": value, "page": "note 2.7.2, p.91", "status": STATUS_VERIFIED,
           "verified_kind": kind}
    if zero_basis is not None:
        fig["zero_basis"] = zero_basis
    if statement is not None:
        fig["statement"] = statement
    return fig


def test_E78_a_zero_on_the_issuers_sentence_is_verified_as_caption_statement():
    from vss.manual import KIND_CAPTION_STATEMENT, VERIFIED_KINDS
    assert KIND_CAPTION_STATEMENT in VERIFIED_KINDS
    parsed = parse(document([period(figures={"pension_deficit": _statement_zero()})]))
    fig = parsed.periods[0].figures["pension_deficit"]
    assert fig.verified and fig.verified_kind == KIND_CAPTION_STATEMENT
    assert fig.statement.startswith("The Group companies only have")
    assert fig.status_with_kind == "VERIFIED (caption_statement)"
    assert not parsed.unverified()


def test_E78_the_kind_is_refused_on_a_number():
    with pytest.raises(ManualError, match=r"not zero \(E78\)"):
        parse(document([period(figures={"pension_deficit": _statement_zero(value=280.0, zero_basis=None)})]))


def test_E78_the_kind_is_refused_without_the_sentence():
    with pytest.raises(ManualError, match="carries no statement"):
        parse(document([period(figures={"pension_deficit": _statement_zero(statement=None)})]))
    with pytest.raises(ManualError, match="carries no statement"):
        parse(document([period(figures={"pension_deficit": _statement_zero(statement="  ")})]))


def test_E78_the_kind_is_refused_on_a_subtotal_zero():
    """A subtotal is arithmetic, not a sentence (E59's shape)."""
    with pytest.raises(ManualError, match="zero form 'subtotal'"):
        parse(document([period(figures={"lease_liabilities": _statement_zero(zero_basis="subtotal")})]))


def test_E78_a_statement_on_any_other_kind_is_refused():
    with pytest.raises(ManualError, match="is not verified as caption_statement"):
        parse(document([period(figures={"pension_deficit": _statement_zero(kind="same_page")})]))
    with pytest.raises(ManualError, match="is not verified as caption_statement"):
        doc = document([period(figures={"pension_deficit": {"value": 0.0, "page": "1", "status": "UNVERIFIED",
                                                            "zero_basis": "note", "statement": "none"}})])
        parse(doc)


def test_E78_the_gate_accepts_the_kind_and_the_zeros_table_quotes_the_sentence():
    from vss.manual import REFUSE_UNVERIFIED, render_report, section5_gate
    figs = {"revenue": figure(1000), "operating_cash_flow": figure(100),
            "capex_combined": figure(-10), "sbc": figure(1), "cash_and_equivalents": figure(50),
            "financial_liabilities_current": _statement_zero(zero_basis="caption", statement="no external debt"),
            "financial_liabilities_noncurrent": _statement_zero(zero_basis="caption", statement="no external debt"),
            "lease_liabilities": figure(20), "pension_deficit": _statement_zero(),
            "asset_retirement_obligation": zero_figure(),
            "prepaid_delivery_obligation": zero_figure(),
            "diluted_weighted_average_shares": figure(1_000_000)}
    parsed = parse(document([period(figures=figs)]))
    gate = section5_gate(parsed, as_of=AS_OF)
    assert not any(r.kind == REFUSE_UNVERIFIED for r in gate.refusals)
    report = render_report(parsed, gate)
    assert "VERIFIED (caption_statement, E78) on the issuer's words: \"no external debt\"" in report


def test_E78_the_kind_on_disk():
    """ZZ-B.ST's pension zero stands on note 2.7.2's sentence; RKT.L's
    decommissioning caption has no sentence, so E78 does not reach it and
    none of its entries carries caption_statement. (Its 2025-FY entry was
    settled cross_document on 2026-08-30 by a DIFFERENT route -- E59, the
    tagged provision captions summing exactly to note 18's two classes --
    which is why this test asserts the KIND and not UNVERIFIED; the
    2026-H1 entry, outside the ESEF package, is still UNVERIFIED.)"""
    from vss.manual import KIND_CAPTION_STATEMENT, KIND_CROSS_DOCUMENT
    parsed = load_manual("ZZ-B.ST", directory=MANUAL_DIR)
    pension = next(f for f in parsed.all_figures() if f.name == "pension_deficit")
    assert pension.verified_kind == KIND_CAPTION_STATEMENT
    assert "defined contribution" in pension.statement
    parsed = load_manual("RKT.L", directory=MANUAL_DIR)
    aro = [f for f in parsed.all_figures() if f.name == "asset_retirement_obligation"]
    assert aro and all(f.verified_kind != KIND_CAPTION_STATEMENT for f in aro)
    assert all(f.statement is None for f in aro)
    assert all("E68.2" in f.page for f in aro)
    by_period = {f.period: f for f in aro}
    assert by_period["2025-FY"].verified_kind == KIND_CROSS_DOCUMENT
    assert not by_period["2026-H1"].verified


# --- E80 (2026-08-30): a net share count is issued less treasury where both
# are stated -- E16's subtraction confirmed against E22, on the committed files


def test_E80_the_pair_is_subtracted_on_disk_and_a_printed_net_is_entered_as_printed():
    from vss.manual import net_shares
    rkt = load_manual("RKT.L", directory=MANUAL_DIR)
    fy = next(p for p in rkt.periods if p.period == "2025-FY")
    h1 = next(p for p in rkt.periods if p.period == "2026-H1")
    # 2025-12-31: the directors' report prints the net -- entered as printed (E22)
    assert fy.value("shares_outstanding_period_end") == 672_380_209
    assert fy.value("shares_issued_period_end") is None
    # 2026-06-30: only the pair is printed -- the store subtracts (E16, E80)
    net = net_shares(h1)
    assert net is not None and net.value == 674_005_752 - 38_950_759 == 635_054_993
    imb = load_manual("IMB.L", directory=MANUAL_DIR)
    fy = next(p for p in imb.periods if p.period == "2025-FY")
    net = net_shares(fy)
    # the trusts' 3.0 million come out too (E54): 869,890,634 - 62,600,000 - 3,000,000
    assert net is not None and net.value == 804_290_634
    h1 = next(p for p in imb.periods if p.period == "2026-H1")
    assert net_shares(h1) is None          # treasury not stated in the interim


# --- E81 (2026-08-30): a prepaid delivery obligation is net debt


def test_E81_the_prepaid_delivery_leg_is_a_required_stock_leg_and_not_annual_only():
    from vss.manual import ANNUAL_ONLY_FIELDS, NET_DEBT_LEGS, STOCK_FIELDS, ZERO_NEEDS_BASIS
    assert "prepaid_delivery_obligation" in NET_DEBT_LEGS
    assert "prepaid_delivery_obligation" in STOCK_FIELDS
    assert "prepaid_delivery_obligation" in ZERO_NEEDS_BASIS
    assert "prepaid_delivery_obligation" not in ANNUAL_ONLY_FIELDS


def test_E81_an_absent_prepaid_delivery_obligation_is_DATA_MISSING_for_net_debt():
    from vss.manual import net_debt_on_basis
    doc = _bridge_file(pension_deficit=280.0)
    del doc["periods"][0]["figures"]["prepaid_delivery_obligation"]
    parsed = parse(doc)
    total, why = net_debt_on_basis(parsed, section5_basis(parsed))
    assert total is None and "prepaid_delivery_obligation" in why


def test_E81_a_zero_prepaid_delivery_obligation_needs_evidence():
    with pytest.raises(ManualError, match="prepaid_delivery_obligation is zero and carries no zero_basis"):
        parse(_bridge_file(pension_deficit=280.0, prepaid_delivery_obligation=0))


def test_E81_the_stream_adds_to_net_debt():
    from vss.manual import net_debt_on_basis
    base = parse(_bridge_file(pension_deficit=280.0))
    with_stream = parse(_bridge_file(pension_deficit=280.0, prepaid_delivery_obligation=690_345.0))
    a, _ = net_debt_on_basis(base, section5_basis(base))
    b, why = net_debt_on_basis(with_stream, section5_basis(with_stream))
    assert b == pytest.approx(a + 690_345.0) and "(E81)" in why


def test_E81_on_disk_lundin_gold_carries_the_stream_and_the_rest_carry_caption_zeros():
    from vss.manual import resolve_on_basis
    lug = load_manual("LUG.ST", directory=MANUAL_DIR)
    basis = section5_basis(lug)
    r = resolve_on_basis(lug, basis, "prepaid_delivery_obligation")
    assert r.value == 690_345.0 and "26,355" in r.figures[0].page and "663,990" in r.figures[0].page
    for ticker in ("CTSH", "LII", "RKT.L", "ZZ-B.ST", "EXE"):
        parsed = load_manual(ticker, directory=MANUAL_DIR)
        r = resolve_on_basis(parsed, section5_basis(parsed), "prepaid_delivery_obligation")
        assert r.value == 0 and r.figures[0].zero_basis == "caption", ticker


# --- E82 (2026-08-30): depreciation mixed with impairment is DATA MISSING,
# not the line -- a NAMED ABSENCE the report prints


def test_E82_a_value_less_figure_with_a_page_is_a_named_absence():
    from vss.manual import named_absences, render_report, section5_gate
    doc = document([period(figures={
        "revenue": figure(1000), "operating_cash_flow": figure(100),
        "depreciation_amortisation": {"value": None, "status": "UNVERIFIED",
                                      "page": "E82: p.22 'Depreciation, amortisation, impairment and remeasurement 391' -- combined, not decomposed"}})])
    parsed = parse(doc)
    fig = parsed.periods[0].figures["depreciation_amortisation"]
    assert not fig.present and fig.page.startswith("E82")
    assert fig not in parsed.unverified()
    assert "depreciation_amortisation" in parsed.missing()
    assert [f.page for f in named_absences(parsed, "depreciation_amortisation")] == [fig.page]
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "named (E82) -- 2025-FY: E82: p.22 'Depreciation, amortisation, impairment and remeasurement 391'" in report


def test_E82_on_disk_reckitt_decomposes_its_year_and_names_its_half():
    from vss.manual import named_absences
    rkt = load_manual("RKT.L", directory=MANUAL_DIR)
    fy = next(p for p in rkt.periods if p.period == "2025-FY")
    assert fy.value("depreciation_amortisation") == 499
    assert "143" in fy.figures["depreciation_amortisation"].page and "356" in fy.figures["depreciation_amortisation"].page
    h1 = next(p for p in rkt.periods if p.period == "2026-H1")
    assert h1.value("depreciation_amortisation") is None
    named = named_absences(rkt, "depreciation_amortisation")
    assert [f.period for f in named] == ["2026-H1"] and "391" in named[0].page
    from vss.manual import render_report, section5_gate
    report = render_report(rkt, section5_gate(rkt, as_of=AS_OF))
    assert "## NAMED ABSENCES (E82)" in report and "| `2026-H1` | `depreciation_amortisation` |" in report
    imb = load_manual("IMB.L", directory=MANUAL_DIR)
    # E72 second application (2026-08-30): the year's right-of-use line is
    # read whole and 675 enters; only the half-year stays a named absence.
    fy = next(p for p in imb.periods if p.period == "2025-FY")
    assert fy.value("depreciation_amortisation") == 675
    assert "574-675" in fy.figures["depreciation_amortisation"].page
    named = named_absences(imb, "depreciation_amortisation")
    assert {f.period for f in named} == {"2026-H1"}
    assert all(f.value is None for f in named) and "326" in named[0].page


# --- E83 (2026-08-30): a stated margin outside the band, explained, is accepted


def test_E83_a_stated_margin_above_100pc_enters_with_its_cause_and_is_refused_without():
    """Karnov Q4 2025: EBIT 895.7 on net sales 664.9, a divestment gain inside."""
    figs = {"revenue": figure(664.9), "operating_income": figure(895.7),
            "op_margin": {**figure(1.347), "cause": "'Other operating income and expenses 723.6', the EHS divestment gain"}}
    parsed = parse(document([period(figures=figs)]))
    assert parsed.periods[0].value("op_margin") == 1.347
    assert parsed.periods[0].figures["op_margin"].cause.startswith("'Other operating income")
    figs["op_margin"] = figure(1.347)
    with pytest.raises(ManualError, match="outside the plausible band"):
        parse(document([period(figures=figs)]))
    with pytest.raises(ManualError, match="belong to `op_margin` alone"):
        parse(document([period(figures={"revenue": {**figure(1000), "cause": "x"}})]))


# --- E79.1 (2026-08-30): a stated tenth keeps its precision


def test_E79_1_the_precision_key_keeps_a_printed_tenth():
    """RVRC Q1: 75 / 392 = 19.13% against a printed 19.0% -- typed 0.19."""
    from vss.config import margin_precision
    assert margin_precision(0.19, 0.1) == 3 and margin_precision(0.19, 1) == 2 and margin_precision(0.19, 0.01) == 3
    with pytest.raises(ManualError, match="stated to a tenth of a percent"):
        parse(document([period(figures={"revenue": figure(392), "operating_income": figure(75),
                                        "op_margin": {**figure(0.19), "precision": 0.1}})]))
    parsed = parse(document([period(figures={"revenue": figure(392), "operating_income": figure(75),
                                             "op_margin": {**figure(0.19), "precision": 1}})]))
    assert parsed.periods[0].figures["op_margin"].precision == 1
    with pytest.raises(ManualError, match="precision must be 1, 0.1 or 0.01"):
        parse(document([period(figures={"op_margin": {**figure(0.19), "precision": 0.5}})]))


# --- E85 (2026-08-30): NOT PRESENTED -- a recorded search, not a zero ------


def _not_presented(page="p.25: liabilities presented are trade and other "
                        "payables, tax liabilities, financial liabilities, "
                        "other non-financial liabilities, provisions, "
                        "contract liabilities"):
    return {"page": page,
            "not_presented": {"document": "Half-Year Report 2026 (sources/x.pdf)",
                              "scope": "all 50 pages: the statement of financial "
                                       "position and notes A.1-G.4",
                              "date": "2026-08-30"}}


def test_E85_a_not_presented_leg_enters_the_bridge_at_nil_and_the_gate_does_not_refuse():
    from vss.manual import REFUSE_UNVERIFIED, STATUS_NOT_PRESENTED, net_debt_on_basis
    doc = _bridge_file(pension_deficit=280.0)
    doc["periods"][0]["figures"]["asset_retirement_obligation"] = _not_presented()
    parsed = parse(doc)
    f = parsed.periods[0].figures["asset_retirement_obligation"]
    assert f.value == 0.0 and f.status == STATUS_NOT_PRESENTED and not f.verified
    assert f.zero_basis is None                      # not an E25 zero
    assert f.not_presented.date == date(2026, 8, 30)
    assert f.status_with_kind.startswith("NOT PRESENTED (E85: searched Half-Year Report 2026")
    assert f not in parsed.unverified()              # nothing to read back
    total, why = net_debt_on_basis(parsed, section5_basis(parsed))
    assert total == 3087.0   # the same bridge as E35.1's case, leases out (E117)
    assert ("NOT PRESENTED (E85), entered at nil on a recorded search: "
            "asset_retirement_obligation") in why
    gate = section5_gate(parsed, as_of=AS_OF)
    assert not [r for r in gate.refusals if r.kind == REFUSE_UNVERIFIED]
    report = render_report(parsed, gate)
    assert "NOT PRESENTED (E85): searched Half-Year Report 2026" in report
    assert "not a zero the issuer states" in report


def test_E85_the_record_carries_the_search_on_the_leg():
    from datetime import datetime
    from vss import runrecord as R
    doc = _bridge_file(pension_deficit=280.0)
    doc["periods"][0]["figures"]["prepaid_delivery_obligation"] = _not_presented()
    parsed = parse(doc)
    record = R.from_store(parsed, section5_basis(parsed),
                          growth=R.Growth(base=0.03, view_file="x.md"),
                          run_ts=datetime(2026, 8, 30, 21, 0))
    leg = next(i for i in record.inputs if i.name == "prepaid_delivery_obligation")
    assert leg.value == 0.0 and leg.entered_by == "store"
    assert leg.verified == "NOT PRESENTED (E85)"
    assert "searched Half-Year Report 2026 (sources/x.pdf)" in leg.provenance
    assert "on 2026-08-30" in leg.provenance and "p.25" in leg.provenance
    assert "NOT PRESENTED (E85)" in record.bridge.note


def test_E85_the_form_is_refused_where_it_is_not_a_recorded_search_on_a_leg():
    doc = _bridge_file(pension_deficit=280.0)
    figs = doc["periods"][0]["figures"]
    figs["asset_retirement_obligation"] = {**_not_presented(), "value": 0.0}
    with pytest.raises(ManualError, match="stands alone \\(E85\\)"):
        parse(doc)
    figs["asset_retirement_obligation"] = _not_presented()
    del figs["asset_retirement_obligation"]["not_presented"]["scope"]
    with pytest.raises(ManualError, match="exactly document, scope and date"):
        parse(doc)
    figs["asset_retirement_obligation"] = zero_figure()
    figs["revenue"] = _not_presented()
    with pytest.raises(ManualError, match="revenue cannot be NOT PRESENTED"):
        parse(doc)
    del figs["revenue"]
    figs["asset_retirement_obligation"] = {"not_presented": _not_presented()["not_presented"]}
    with pytest.raises(ManualError, match="names no page"):
        parse(doc)


# --- E86 (2026-08-30): a cumulative column is stored as operands ------------


def _column(cumulative, prior=None, *, page="Q p.13", prior_page="prior p.15",
            status=STATUS_VERIFIED):
    out = {"cumulative": cumulative, "page": page, "status": status}
    if prior is not None:
        out.update(cumulative_prior=prior, cumulative_prior_page=prior_page)
    return out


def test_E86_a_quarter_is_the_codes_difference_of_two_stated_columns():
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    doc["interest_in_ocf"] = INTEREST_NO
    columns = [_column(-30.0, -10.0), _column(-45.0, -30.0),
               figure(-8.0, page="Q1 p.9"), _column(-20.0, -8.0)]
    for entry, col in zip(doc["periods"], columns):
        entry["figures"]["capex_combined"] = col
    parsed = parse(doc)
    q3 = parsed.periods[0].figures["capex_combined"]
    assert q3.value == -20.0 and q3.cumulative == -30.0 and q3.cumulative_prior == -10.0
    assert q3.page_provenance == ("E86: -30 [Q p.13] - -10 [prior p.15] = -20 -- "
                                  "the difference is the code's, both columns printed")
    q1 = parsed.periods[2].figures["capex_combined"]
    assert q1.value == -8.0 and q1.cumulative is None and q1.page_provenance == "Q1 p.9"
    r = resolve_on_basis(parsed, section5_basis(parsed), "capex_combined")
    assert r.value == -20.0 + -15.0 + -8.0 + -12.0 and r.verified
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "CUMULATIVE COLUMNS (E86)" in report and "-45 [Q p.13] - -30 [prior p.15] = -15" in report


def test_E86_a_column_without_its_prior_is_an_operand_on_file_and_no_quarter():
    doc = four_quarters(each={"operating_cash_flow": figure(100.0),
                              "capex_combined": figure(-5.0)},
                        last={"sbc": _column(706.0)})
    doc["interest_in_ocf"] = INTEREST_NO
    parsed = parse(doc)
    f = parsed.periods[-1].figures["sbc"]
    assert f.value is None and f.cumulative == 706.0 and not f.present
    assert "prior column NOT STATED, so no quarter (E86)" in f.page_provenance
    assert resolve_on_basis(parsed, section5_basis(parsed), "sbc").value is None
    report = render_report(parsed, section5_gate(parsed, as_of=AS_OF))
    assert "706 [Q p.13] - prior column NOT STATED" in report


def test_E86_the_form_is_refused_off_a_quarterly_flow_or_beside_a_value():
    doc = four_quarters(each={"operating_cash_flow": figure(100.0)})
    figs = doc["periods"][0]["figures"]
    figs["capex_combined"] = {**_column(-30.0, -10.0), "value": -20.0}
    with pytest.raises(ManualError, match="cumulative: beside value: \\(E86\\)"):
        parse(doc)
    figs["capex_combined"] = {"cumulative": -30.0, "page": "p", "cumulative_prior": -10.0}
    with pytest.raises(ManualError, match="come together \\(E86\\)"):
        parse(doc)
    del figs["capex_combined"]
    figs["cash_and_equivalents"] = _column(-30.0, -10.0)
    with pytest.raises(ManualError, match="is not a flow"):
        parse(doc)
    annual = document([period(figures={"capex_combined": _column(-30.0, -10.0)})])
    with pytest.raises(ManualError, match="QUARTERLY periods: entry \\(E86\\)"):
        parse(annual)


# =========================================================================
# E108 -- THE SENSITIVITY FLOOR, in three limbs
# =========================================================================


#: E117 (2026-09-19): LIAB.ST, SAP.DE and RKT.L state no lease interest on
#: their basis, so their FCF0 is DATA MISSING (UNVERIFIED UNDER E117). The
#: tests below are about E106 / E108, not leases: they run on a COPY whose
#: basis periods carry both lease legs as NAMED ZEROS, labelled as fixtures.
E117_BASIS = {"LIAB.ST": ("2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"),
              "SAP.DE": ("2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"),
              "RKT.L": ("2025-FY",)}


def _e117_fixture(tmp_path, ticker):
    from vss import reference_figures as RF
    import re
    text = (MANUAL_DIR / f"{ticker}.yaml").read_text(encoding="utf-8")
    # a bounded lease interest already on the store is replaced by the
    # fixture's named zero; a stated principal already there is kept
    text = re.sub(r"      lease_interest_paid:\n(?:        .*\n)+", "", text)
    for period in E117_BASIS[ticker]:
        for name in ("lease_payments_capital", "lease_interest_paid"):
            try:
                RF.insert_figure(text, period, f"      {name}:\n        value: 0\n")
            except RF.ReferenceError:
                continue            # already stated on the store
            text = RF.insert_figure(text, period, (
                f"      {name}:\n"
                f"        value: 0\n"
                f'        page: "TEST FIXTURE: a named zero so FCF0 forms -- '
                f'this test is about E106/E108, not E117"\n'
                f"        status: VERIFIED\n"
                f"        verified_kind: same_page\n"
                f"        zero_basis: note\n"))
    directory = tmp_path / "manual-e117"
    directory.mkdir(exist_ok=True)
    (directory / f"{ticker}.yaml").write_text(text, encoding="utf-8")
    return directory


def test_E108_the_zero_limb_needs_no_valuation_and_no_growth_view(tmp_path):
    """+/-10% of zero is zero, on any fv_base there is."""
    from vss.manual import FLAG_EXEMPT, basis_reads, floor_exempt_zeros
    parsed = load_manual("LIAB.ST", directory=_e117_fixture(tmp_path, "LIAB.ST"))
    basis = section5_basis(parsed)
    figures = [f for f in parsed.unverified() if f in set(basis_reads(parsed, basis))]
    assert figures and all(f.name == "nci_dividends_paid" for f in figures)
    assert set(floor_exempt_zeros(figures)) == set(figures)
    gate = section5_gate(parsed, as_of=date(2026, 9, 4))
    assert not gate.refused
    exempt = [f for f in gate.flags if f.kind == FLAG_EXEMPT]
    assert len(exempt) == 4
    # THE PROVENANCE IS NOT WAIVED: every exempt figure still cites its page
    assert all("E107 SEARCHED ABSENCE" in f.detail for f in exempt)
    assert all("THE READ-BACK IS WAIVED AND THE PROVENANCE IS NOT" in f.detail
               for f in exempt)


def test_E108_the_bound_limb_is_growth_free_and_only_where_the_bridge_is_NET_CASH(tmp_path):
    """fv x shares = D(g) x FCF0 + net_cash. Where net_cash >= 0 the ratio
    D/(D + net_cash/FCF0) is at most 1 for EVERY D, so a flow leg cannot
    move fv_base by more than its own share of FCF0. Where the bridge is
    net DEBT the same factor exceeds 1 without limit and NO growth-free
    bound exists -- the empty answer is the honest one."""
    from vss.manual import floor_bound_flow_legs
    sap = load_manual("SAP.DE", directory=_e117_fixture(tmp_path, "SAP.DE"))
    bound = floor_bound_flow_legs(sap, section5_basis(sap))
    # 10% of 30,000,000 over FCF0 7,091,000,000 -- 7,369m less the 278m of
    # lease principal E117 deducts since A3 put it on file (2026-09-19)
    assert bound["nci_dividends_paid"] == pytest.approx(0.10 * 30e6 / 7_091e6,
                                                        rel=1e-9)
    assert bound["nci_dividends_paid"] < 0.01
    # and it IS a bound: the measured move is smaller, never larger
    rkt = load_manual("RKT.L", directory=_e117_fixture(tmp_path, "RKT.L"))
    assert floor_bound_flow_legs(rkt, section5_basis(rkt)) == {}


def test_E108_a_leg_ABOVE_the_floor_still_refuses(tmp_path):
    """The floor exempts; it never excuses. A leg big enough to move the
    answer is read back like any other."""
    from vss.manual import FLAG_EXEMPT, REFUSE_UNVERIFIED
    parsed = load_manual("SAP.DE", directory=_e117_fixture(tmp_path, "SAP.DE"))
    gate = section5_gate(parsed, as_of=date(2026, 9, 4),
                         measured_exempt={"nci_dividends_paid": 0.04})
    assert REFUSE_UNVERIFIED in {r.kind for r in gate.refusals}
    assert not [f for f in gate.flags if f.kind == FLAG_EXEMPT]


def test_E108_the_measured_limb_comes_off_the_record_and_wins_over_no_bound(tmp_path):
    from datetime import datetime as _dt
    from zoneinfo import ZoneInfo as _Z

    from vss import runrecord as R
    from vss.manual import FLAG_EXEMPT
    parsed = load_manual("RKT.L", directory=_e117_fixture(tmp_path, "RKT.L"))
    basis = section5_basis(parsed)
    record = R.from_store(
        parsed, basis, growth=R.Growth(base=0.03, bear=0.0, bull=0.05,
                                       view_file="reference/growth-views/RKT.L.md"),
        run_ts=_dt(2026, 9, 4, 12, tzinfo=_Z("Europe/Stockholm")),
        rate=R.Rate(core_expected_return=0.070, premium=0.025))
    moves = record.sensitivity()
    # RKT.L's bridge is NET DEBT, so the growth-free bound limb returns
    # nothing for it and only the record can answer.
    from vss.manual import floor_bound_flow_legs
    assert floor_bound_flow_legs(parsed, basis) == {}
    assert 0 < moves["nci_dividends_paid"] < 0.01
    # The owner read the -6 back on 2026-09-04, so the figure is VERIFIED
    # and nothing on this name needs the exemption any more. The limb is
    # tested where it still bites: a leg entered UNVERIFIED.
    from dataclasses import replace as _replace
    figure = parsed.periods[0].figures["nci_dividends_paid"]
    assert figure.verified
    unread = _replace(parsed, periods=(_replace(
        parsed.periods[0], figures={**parsed.periods[0].figures,
                                    "nci_dividends_paid": _replace(
                                        figure, status="UNVERIFIED",
                                        verified_kind=None)}),
        ) + parsed.periods[1:])
    assert section5_gate(unread, as_of=date(2026, 9, 4)).refused
    with_limb = section5_gate(unread, as_of=date(2026, 9, 4),
                              measured_exempt=moves)
    assert not with_limb.refused
    assert any(f.kind == FLAG_EXEMPT and "MEASURED on the record" in f.detail
               for f in with_limb.flags)


# =========================================================================
# E106 clause 3 in the STORE -- a leg that is ABSENT but BOUNDED
# (2026-09-04), and E28's growth view, machine-readable at last
# =========================================================================


def _bound_file(**bound):
    base = _bridge_file(pension_deficit=280.0, operating_cash_flow=1000.0,
                        capex_combined=-100.0, sbc=1.0)
    base["periods"][0]["figures"]["operating_lease_payments"] = bound
    return base


def test_E106_a_bound_is_not_a_value_and_may_not_sit_beside_one():
    with pytest.raises(ManualError, match="bound BESIDE a value"):
        parse(_bound_file(value=5.0, bound=10.0, page="p.1"))


def test_E106_a_bound_with_no_page_is_an_assertion_and_is_REFUSED():
    """*A bound is itself a figure and needs its evidence like any other.*"""
    with pytest.raises(ManualError, match="bounded and carries no page"):
        parse(_bound_file(bound=10.0))


def test_E106_a_bound_is_a_MAGNITUDE_and_zero_is_not_a_bound():
    with pytest.raises(ManualError, match="a bound is a MAGNITUDE"):
        parse(_bound_file(bound=0.0, page="p.1"))
    with pytest.raises(ManualError, match="a bound is a MAGNITUDE"):
        parse(_bound_file(bound=-10.0, page="p.1"))


def test_E106_the_direction_defaults_to_reduces_and_is_checked():
    from vss.manual import BOUND_RAISES, BOUND_REDUCES
    parsed = parse(_bound_file(bound=10.0, page="p.1"))
    figure = parsed.periods[0].figures["operating_lease_payments"]
    assert figure.bounded and figure.value is None
    assert figure.bound_direction == BOUND_REDUCES
    parsed = parse(_bound_file(bound=10.0, page="p.1", bound_direction="raises"))
    assert parsed.periods[0].figures["operating_lease_payments"].bound_direction \
        == BOUND_RAISES
    with pytest.raises(ManualError, match="bound_direction must be one of"):
        parse(_bound_file(bound=10.0, page="p.1", bound_direction="upwards"))


def test_E106_AOS_is_bounded_at_the_issuers_own_total_lease_expense_and_STILL_REFUSES():
    """The bound machinery works, and the answer it gives is NO.

    A. O. Smith tags no `us-gaap:OperatingLeasePayments` and prints no
    supplemental cash-flow lease line, so E70's leg cannot be made present
    by any search. Note 4 DOES bound it: operating lease expense 6.4 (cost
    of products sold) + 16.8 (SG&A) = 23.2, which strictly EXCEEDS what E70
    adds back because it also contains the 1.8 short-term and 5.8 variable
    that ASC 842 keeps out of the lease liability.

    23.2 moves fv_base by 4.27%, past E106's 3.5%. E106 clause 2: A LEG
    ABOVE THE BOUND REFUSES, EXACTLY AS BEFORE.
    """
    from datetime import datetime as _dt, timezone as _tz

    from dataclasses import replace as _replace
    from vss import runrecord as R
    from vss.manual import BOUND_RAISES, REFUSE_TOLERANCE, basis_bounds
    parsed = load_manual("AOS", directory=MANUAL_DIR)
    basis = section5_basis(parsed)
    # E117 (2026-09-19): rent is an operating cost, the payment is no longer
    # read, and its bound BOUNDS NOTHING -- neither the gate nor the record
    # carries it, and both let AOS run.
    assert basis_bounds(parsed, basis) == ()
    kept = [f for f in parsed.all_figures()
            if f.name == "operating_lease_payments" and f.bounded]
    assert kept[0].bound == 23_200_000 and kept[0].bound_direction == BOUND_RAISES
    assert not section5_gate(parsed, as_of=AS_OF).refused
    record = R.from_store(
        parsed, basis, run_ts=_dt(2026, 9, 4, tzinfo=_tz.utc),
        growth=R.Growth(base=0.04, bear=0.0, bull=0.07,
                        view_file="reference/growth-views/AOS.md"),
        rate=R.Rate(core_expected_return=0.070, premium=0.025))
    assert record.undetermined == () and record.complete
    # THE MACHINERY, on the same bound put back by hand: 23.2m still moves
    # fv_base past E106's 3.5% (4.25% on E117's bridge; 4.27% on E70's).
    bounded = _replace(record, undetermined=(R.Undetermined(
        name="operating_lease_payments", bound=23_200_000.0,
        page="AOS 10-K note 4, total operating lease expense",
        direction=BOUND_RAISES),))
    fraction, _move, named = bounded.tolerance()
    assert fraction == pytest.approx(0.0425, abs=0.0005)
    assert fraction > R.INCOMPLETE_LEG_TOLERANCE
    assert "can only RAISE fv_base" in named
    assert any("past E106" in gap for gap in bounded.missing())


def test_E106_an_ADD_BACK_leg_is_perturbed_UPWARD_and_a_deduction_downward():
    """E106 clause 1 says "on ANY PLAUSIBLE VALUE", and the plausible values
    of a leg struck at zero are one-sided. An add-back's are all ABOVE it."""
    from datetime import datetime as _dt, timezone as _tz

    from vss import runrecord as R
    from vss.manual import BOUND_RAISES, BOUND_REDUCES
    parsed = load_manual("AOS", directory=MANUAL_DIR)
    basis = section5_basis(parsed)
    kwargs = dict(run_ts=_dt(2026, 9, 4, tzinfo=_tz.utc),
                  growth=R.Growth(base=0.04, view_file="reference/growth-views/AOS.md"),
                  rate=R.Rate(core_expected_return=0.070, premium=0.025))
    from dataclasses import replace as _replace
    # E117 (2026-09-19) retired AOS's bound (the leg is no longer read); the
    # same 23.2m is put back by hand, since this test is about E106's sides.
    record = _replace(R.from_store(parsed, basis, **kwargs), undetermined=(
        R.Undetermined(name="operating_lease_payments", bound=23_200_000.0,
                       page="AOS 10-K note 4", direction=BOUND_RAISES),))
    assert record.undetermined[0].direction == BOUND_RAISES
    bound = record.undetermined[0].bound
    base = record._strike_unchecked()
    higher = record._strike_unchecked(fcf0_adjustment=+bound)
    lower = record._strike_unchecked(fcf0_adjustment=-bound)
    # The two ends are on OPPOSITE SIDES of the struck value, which is what
    # makes the direction matter at all.
    assert lower < base < higher
    # A `raises` leg is measured against the HIGHER end -- the only one its
    # plausible values can reach. Flipping the direction measures the other.
    assert record.tolerance()[1] == pytest.approx(higher - base)
    flipped = _replace(record, undetermined=tuple(
        _replace(u, direction=BOUND_REDUCES) for u in record.undetermined))
    assert flipped.tolerance()[1] == pytest.approx(base - lower)


def test_E106_two_bounds_pointing_opposite_ways_are_summed_SEPARATELY():
    """Netting them would let two unknowns cancel. Two unknowns that happen
    to point opposite ways are not one smaller unknown -- they are two."""
    from vss import runrecord as R
    from vss.manual import BOUND_RAISES, BOUND_REDUCES
    from tests._records import synthetic_record
    base = synthetic_record("X", "USD", 100.0)
    from dataclasses import replace as _replace
    one_way = _replace(base, undetermined=(
        R.Undetermined("a", 10.0, "p", BOUND_RAISES),
        R.Undetermined("b", 10.0, "p", BOUND_REDUCES)))
    netted_would_be_zero = one_way.tolerance()[1]
    assert netted_would_be_zero > 0


def test_E28_the_growth_view_is_machine_readable_on_the_watchlist_entry():
    from pathlib import Path

    from vss.config import load_watchlist
    entries = {e.ticker: e for e in load_watchlist(Path("config/watchlist.yaml"))}
    sap = entries["SAP.DE"].growth
    assert sap is not None
    assert (sap.base, sap.bear, sap.bull) == (0.08, 0.06, 0.11)
    assert sap.view == "reference/growth-views/SAP.DE.md"
    assert sap.registered == date(2026, 8, 26) and sap.has_band
    # E28's ORDERING stays checkable: the file the words are in, and the
    # day they were written, are both required.
    assert Path(sap.view).exists()


@pytest.mark.parametrize("block, message", [
    ({"base": 0.08}, "growth is missing"),
    ({"base": 8, "view": "reference/growth-views/X.md",
      "registered": "2026-01-01"}, "outside -50%"),
    ({"base": 0.08, "bull": 0.11, "view": "reference/growth-views/X.md",
      "registered": "2026-01-01"}, "come TOGETHER or not at all"),
    ({"base": 0.20, "bear": 0.06, "bull": 0.11,
      "view": "reference/growth-views/X.md",
      "registered": "2026-01-01"}, "outside its own range"),
    ({"base": 0.08, "view": "X.md", "registered": "2026-01-01"},
     "must name the file"),
])
def test_E28_a_growth_block_that_cannot_be_checked_is_REFUSED(block, message):
    import yaml as _yaml

    from vss.config import ConfigError, load_watchlist
    raw = {"tickers": [{"ticker": "X", "name": "X", "currency": "USD",
                          "status": "PIPELINE", "growth": block}]}
    path = Path(__file__).resolve().parent / "_growth_tmp.yaml"
    path.write_text(_yaml.safe_dump(raw), encoding="utf-8")
    try:
        with pytest.raises(ConfigError, match=message):
            load_watchlist(path)
    finally:
        path.unlink()


def test_a_PROXY_may_not_outrank_the_FINANCIAL_STATEMENTS_on_the_same_element():
    """LOPE's intake, 2026-09-04, and the store was 1,000x wrong.

    Grand Canyon Education tags `us-gaap:NetIncomeLoss` for FY2025 twice:
    216,170,000 in the 10-K and 216,170 in the DEF 14A, which tagged the
    number as its own table PRINTS it -- *(In thousands, except per share
    data)* -- without scaling. `_pick` took the LATEST filing, so the proxy
    won, and a net income three orders too small sat beside a revenue in
    whole units where 5.1C reads it.
    """
    from vss import xbrl as X
    ten_k = {"start": "2025-01-01", "end": "2025-12-31", "val": 216_170_000,
             "form": "10-K", "accn": "0001104659-26-017047", "filed": "2026-02-18"}
    proxy = {"start": "2025-01-01", "end": "2025-12-31", "val": 216_170,
             "form": "DEF 14A", "accn": "0001104659-26-047719",
             "filed": "2026-04-23"}
    chosen, restated = X._pick([ten_k, proxy])
    assert chosen["val"] == 216_170_000 and chosen["form"] == "10-K"
    # and the proxy is not recorded as a restatement of the statement: it
    # was never in the pool at all
    assert restated is None
    # WITH NO STATEMENT IN THE POOL nothing changes -- the rule narrows,
    # it does not discard.
    assert X._pick([proxy])[0]["val"] == 216_170


def test_a_round_power_of_a_thousand_is_a_UNIT_SLIP_and_not_a_restatement():
    from vss import xbrl as X
    assert X._is_unit_slip(216_170_000, 216_170)
    assert X._is_unit_slip(216_170, 216_170_000)
    assert X._is_unit_slip(5.0, 5_000_000.0)
    # a real restatement is not a round power of a thousand
    assert not X._is_unit_slip(216_170_000, 214_000_000)
    assert not X._is_unit_slip(216_170_000, 216_170_000)
    assert not X._is_unit_slip(216_170_000, None)
    assert not X._is_unit_slip(0.0, 0.0)


def test_LOPE_carries_the_10K_net_income_and_it_agrees_with_its_own_revenue():
    """The check that would have caught it without knowing the cause: a
    margin of 0.02% on an education business is not a margin."""
    parsed = load_manual("LOPE", directory=MANUAL_DIR)
    basis = section5_basis(parsed)
    revenue = resolve_on_basis(parsed, basis, "revenue").value
    net_income = resolve_on_basis(parsed, basis, "net_income").value
    assert net_income == 216_170_000 and revenue == 1_106_070_000
    assert 0.10 < net_income / revenue < 0.40


# =========================================================================
# E110 (2026-09-04) -- the issuer's own words that an item is IMMATERIAL
# =========================================================================


def test_E110_CROX_and_MUSA_are_resolved_by_a_SENTENCE_and_not_by_a_bound():
    """Two records that refused on a leg the issuer had already answered.

    Crocs: "Asset retirement obligations were NOT SIGNIFICANT to the
    consolidated balance sheets". Murphy USA: the loyalty "deferred revenue
    balances at December 31, 2025 and 2024 were IMMATERIAL". Neither is a
    stated nil and neither is a number -- but both are CLAIMS the company
    made about its own accounts, which is what E25 rests on.
    """
    from datetime import datetime as _dt, timezone as _tz

    from vss import runrecord as R
    for ticker, leg, word in (("CROX", "asset_retirement_obligation",
                               "NOT SIGNIFICANT"),
                              ("MUSA", "prepaid_delivery_obligation",
                               "IMMATERIAL")):
        parsed = load_manual(ticker, directory=MANUAL_DIR)
        basis = section5_basis(parsed)
        figure = resolve_on_basis(parsed, basis, leg).figures[0]
        assert figure.value == 0 and figure.zero_basis == "note"
        assert word in figure.page and "E110" in (figure.source or "")
        record = R.from_store(
            parsed, basis, run_ts=_dt(2026, 9, 4, tzinfo=_tz.utc),
            growth=R.Growth(base=0.0, view_file="TEST: no view is registered"))
        assert [g for g in record.missing() if "growth" not in g] == []


def test_E110_does_not_reach_a_filer_that_says_NOTHING():
    """AOS is the control: it states figures rather than immateriality.
    Its E70 leg was BOUNDED at 23.2m and refused on the tolerance; E117
    (2026-09-19) stopped reading that leg, so nothing is refused -- and E110
    has turned none of AOS's stated figures into a nil either way."""
    from vss.manual import REFUSE_TOLERANCE
    parsed = load_manual("AOS", directory=MANUAL_DIR)
    gate = section5_gate(parsed, as_of=date(2026, 9, 4))
    assert REFUSE_TOLERANCE not in {r.kind for r in gate.refusals}
    assert not [f for f in parsed.all_figures()
                if f.zero_basis == "note" and "E110" in (f.source or "")]


def test_E110_leaves_E25s_rule_about_an_ABSENT_figure_standing():
    """The whole ruling turns on the difference between a SILENCE and a
    CLAIM. An absent figure is still never read as zero."""
    with pytest.raises(ManualError, match="zero_basis"):
        parse(_bridge_file(pension_deficit=280.0, operating_cash_flow=1000.0,
                           capex_combined=-100.0, sbc=1.0,
                           lease_liabilities=0.0))


# =========================================================================
# E111 (2026-09-04) -- INTAKE: read, not watched
# =========================================================================


def _entry(**over):
    base = {"ticker": "X", "name": "X", "currency": "USD", "status": "INTAKE"}
    base.update(over)
    return {"tickers": [base]}


def _load(raw):
    import yaml as _yaml

    from vss.config import load_watchlist
    path = Path(__file__).resolve().parent / "_intake_tmp.yaml"
    path.write_text(_yaml.safe_dump(raw), encoding="utf-8")
    try:
        return load_watchlist(path)
    finally:
        path.unlink()


@pytest.mark.parametrize("key, value", [
    ("dd_at_entry", 0.34), ("peak_date", "2025-08-27"),
    ("stop_price", 120.0), ("tier", 2),
])
def test_E111_an_INTAKE_may_not_carry_an_ENTRY_FACT(key, value):
    """The whole point of the status is that READING a company does not
    start E12's clock by accident -- and a stamp written by mistake is
    exactly an accident, so it is refused rather than ignored."""
    from vss.config import ConfigError
    with pytest.raises(ConfigError, match="status INTAKE carries"):
        _load(_entry(**{key: value}))


def test_E111_an_INTAKE_MAY_carry_a_growth_view_a_store_and_a_value():
    """What it is FOR: a growth view where a machine can read it, so E108's
    floor and E106 clause 4 can run without the name being watched."""
    entries = _load(_entry(fv_base=300.0, growth={
        "base": 0.05, "bear": 0.0, "bull": 0.08,
        "view": "reference/growth-views/LII.md", "registered": "2026-08-30"}))
    assert entries[0].status == "INTAKE"
    assert entries[0].growth.base == 0.05 and entries[0].fv_base == 300.0


def test_E111_an_INTAKE_collects_NO_verdicts_and_is_not_ACTIONABLE():
    from vss import rules as R
    verdicts = R.collect_verdicts(
        status="INTAKE", last_close=100.0, stop_price=None, mbp=None,
        mbp_superseded=False, drawdown=-0.40, series_finding=None,
        dd_at_entry=None, peak_date=None)
    assert [v.code for v in verdicts] == [R.INTAKE]
    assert "read, not watched" in verdicts[0].detail
    assert not R.TickerAssessment("X", verdicts=tuple(verdicts)).actionable


def test_E111_an_INTAKE_name_carries_no_entry_stamp():
    from vss.config import load_watchlist
    from vss.rules import INTAKE_REFUSED_KEYS
    entries = {e.ticker: e for e in
               load_watchlist(Path("config/watchlist.yaml"))}
    # CROX was PROMOTED to PIPELINE on 2026-09-04, which is the transition
    # this status exists to make possible and is what stamped E12's entry.
    # The test holds the RULE over whoever is INTAKE, not a fixed list --
    # a list would fail every time the owner promoted a name, which is the
    # opposite of what a test is for.
    intaken = {t for t, e in entries.items() if e.status == "INTAKE"}
    assert intaken and intaken <= {"ACN", "AOS", "CPRT", "CROX", "LII",
                                   "LOPE", "MUSA", "RKT.L", "ULTA"}
    # CROX went INTAKE -> PIPELINE (2026-09-04) -> DROPPED (2026-09-08, on
    # Gate 2). BOTH STAMPS ARE KEPT through the drop: a dropped name is a
    # RECORD, and the reading Gate 1 was frozen on is part of what the
    # record says. What must NEVER appear on it is a value or a tier.
    crox = entries["CROX"]
    assert crox.status in ("PIPELINE", "DROPPED")
    assert crox.dd_at_entry is not None and crox.peak_date is not None
    assert crox.fv_base is None and crox.tier is None
    assert crox.stop_price is None
    for ticker in sorted(intaken):
        entry = entries[ticker]
        for key in INTAKE_REFUSED_KEYS:
            assert getattr(entry, key, None) is None, (ticker, key)
    # AND EVERY ONE NOW CARRIES A VIEW. CROX, LOPE and MUSA carried none
    # when the status was built -- the owner writes those after reading the
    # business -- and he registered all three later the same day. What the
    # test holds is the RULE, not the morning: an INTAKE entry may carry a
    # view and may not carry an entry stamp.
    for ticker in sorted(intaken):
        view = entries[ticker].growth
        assert view is not None, ticker
        assert view.view.startswith("reference/growth-views/"), ticker
        assert view.bear <= view.base <= view.bull, ticker


# =========================================================================
# E112 (2026-09-08) -- Gate 3's coverage numerator is OPERATING INCOME AS
# STATED, impairments included
# =========================================================================


def _coverage_file(operating_income, net_finance_costs):
    base = _bridge_file(pension_deficit=280.0, operating_cash_flow=1000.0,
                        capex_combined=-100.0, sbc=1.0)
    figures = base["periods"][0]["figures"]
    # E117 clause 5: the IFRS fixture is rent-bearing; a named-zero ROU
    # depreciation beside its named-zero lease legs leaves the arithmetic
    # of every E112 / E118 test unchanged
    figures["rou_depreciation"] = zero_figure()
    figures["operating_income"] = {"value": operating_income, "page": "p.1",
                                   "status": STATUS_VERIFIED,
                                   "verified_kind": "same_page"}
    figures["net_finance_costs"] = {"value": net_finance_costs, "page": "p.1",
                                    "status": STATUS_VERIFIED,
                                    "verified_kind": "same_page"}
    return base


def test_E112_the_numerator_is_the_STATED_operating_income():
    """CROX's own figures: 149,515 over 88,287 is 1.69x and the limb FAILS.
    The numerator carries 738,115 of HEYDUDE impairments and NOTHING IS
    ADDED BACK -- adjusting would substitute a reader's judgement of what is
    recurring for the accounts' own figure."""
    from vss.manual import interest_coverage
    parsed = parse(_coverage_file(149_515.0, 88_287.0))
    got = interest_coverage(parsed, section5_basis(parsed),
                            impairments=738_115.0)
    assert got.ebit == 149_515.0 and got.denominator == 88_287.0
    assert got.ratio == pytest.approx(1.6935, abs=0.0005)
    assert got.passes is False
    # the adjusted figure is INFORMATION and is on the other side
    assert got.adjusted == pytest.approx(10.0539, abs=0.0005)
    assert got.material is True
    line = got.line()
    assert "AS STATED" in line and "FAILS" in line
    assert "not the verdict" in line and "OTHER SIDE of the limit" in line


def test_E112_an_impairment_never_enters_the_verdict():
    """`passes` reads the STATED ratio and nothing else, whatever is passed
    in for information."""
    from vss.manual import interest_coverage
    parsed = parse(_coverage_file(149_515.0, 88_287.0))
    without = interest_coverage(parsed, section5_basis(parsed))
    withit = interest_coverage(parsed, section5_basis(parsed),
                               impairments=738_115.0)
    assert without.ratio == withit.ratio
    assert without.passes is withit.passes is False
    assert without.adjusted is None


def test_E112_the_rule_can_only_move_a_name_DOWN_through_the_limit():
    """Not adjusting can only make the numerator smaller, so a name above
    5x on stated operating income is above it on any adjusted basis. The
    rule can change no verdict except for a name already failing."""
    from vss.manual import COVERAGE_MINIMUM, interest_coverage
    parsed = parse(_coverage_file(600.0, 100.0))
    got = interest_coverage(parsed, section5_basis(parsed), impairments=900.0)
    assert got.ratio == 6.0 and got.passes is True
    assert got.adjusted == 15.0 and got.adjusted > got.ratio
    assert not got.material          # both sides of 5x are the same side
    assert COVERAGE_MINIMUM == 5.0


def test_E118_a_NET_FINANCE_INCOME_passes_and_is_never_divided():
    """AUTO.L, RMV.L and CTSH earn more interest than they pay. E112 made
    that NOT MEANINGFUL; E118 (2026-09-19) makes it PASS -- no interest
    burden -- and still never divides by a negative."""
    from vss.manual import interest_coverage
    parsed = parse(_coverage_file(300.0, -50.0))
    got = interest_coverage(parsed, section5_basis(parsed))
    assert got.ratio is None and got.net_income_case and got.passes is True
    assert "no interest burden (E118)" in got.why and "PASS" in got.why


def test_E118_a_ZERO_net_passes_too_amending_E25_for_coverage():
    """A zero still needs `zero_basis` before the file will LOAD (E25); on
    the arithmetic, E118 reads it as no burden rather than undefined."""
    from vss.manual import interest_coverage
    raw = _coverage_file(300.0, 0.0)
    raw["periods"][0]["figures"]["net_finance_costs"]["zero_basis"] = "caption"
    parsed = parse(raw)
    got = interest_coverage(parsed, section5_basis(parsed))
    assert got.ratio is None and got.passes is True and "ZERO" in got.why


def test_E118_gross_interest_on_file_must_still_clear_5x():
    from vss.manual import interest_coverage
    raw = _coverage_file(300.0, -50.0)
    raw["periods"][0]["figures"]["finance_costs_period"] = figure(100.0)
    got = interest_coverage(parse(raw), section5_basis(parse(raw)))
    assert got.gross_expense == 100.0 and got.gross_cover == pytest.approx(3.0)
    assert got.passes is False and "FAIL" in got.why
    raw["periods"][0]["figures"]["finance_costs_period"] = figure(37.0)
    got = interest_coverage(parse(raw), section5_basis(parse(raw)))
    assert got.passes is True and got.gross_cover == pytest.approx(300 / 37)


def test_E119_derives_EBITDA_on_one_window_and_the_information_line_can_REVIEW():
    """CTSH, 2026-09-19: no stated EBITDA, so operating income + D&A, on the
    section 5 basis against E117's net debt on that basis; the newest
    quarter's net debt over the same EBITDA is the information line."""
    from vss.manual import (GATE3_LEVERAGE_MAX, KILL_LEVERAGE_MAX, Leverage,
                            gate3_leverage)
    parsed = load_manual("CTSH", directory=MANUAL_DIR)
    got = gate3_leverage(parsed, section5_basis(parsed))
    assert got.ebitda == 3_389_000_000 + 550_000_000 and "DERIVED" in got.ebitda_source
    assert got.net_debt == -1_056_000_000 and got.basis_label == "annual FY2025"
    assert got.latest_period == "2026-Q2"
    assert got.latest_net_debt == pytest.approx(791_000_000)
    assert round(got.latest_ratio, 2) == 0.20
    assert got.state(GATE3_LEVERAGE_MAX) == "PASS" == got.state(KILL_LEVERAGE_MAX)
    assert any("pension_deficit" in c for c in got.carried)
    # the information line alone crossing the threshold records REVIEW
    review = Leverage(ebitda=100.0, ebitda_source="DERIVED", net_debt=200.0,
                      ratio=2.0, latest_net_debt=300.0, latest_ratio=3.0)
    assert review.state(GATE3_LEVERAGE_MAX) == "REVIEW"
    assert review.state(KILL_LEVERAGE_MAX) == "PASS"


def test_E119_the_kill_reads_the_derived_ratio_only_where_nothing_is_stated():
    from vss import rules as RU
    derived = ("FAIL", "net debt 400 / EBITDA 100 = 4.00x")
    assert RU.leverage_kill([], derived).state == RU.TRIP
    assert RU.leverage_kill([], ("PASS", "x")).state == RU.NO_TRIP
    assert RU.leverage_kill([], None).state == RU.CANNOT_EVALUATE


def test_E112_a_missing_leg_is_DATA_MISSING_and_never_a_FAIL():
    from vss.manual import interest_coverage
    parsed = parse(_bridge_file(pension_deficit=280.0,
                                operating_cash_flow=1000.0,
                                capex_combined=-100.0, sbc=1.0))
    got = interest_coverage(parsed, section5_basis(parsed))
    assert got.ratio is None and got.passes is None
    assert "operating_income" in got.why


def test_E112_the_stored_names_that_form_coverage_and_the_one_below_the_limit():
    """Applied across every store 2026-09-08. TEN can form the ratio; the
    rest carry no `operating_income`, because the SEC XBRL path writes none.
    Only SYNSAM.ST is below 5x, and it carries no impairment in EBIT -- so
    NO STORED NAME CHANGES SIDE under this rule.

    The count was NINE that morning. BOUV.OL's intake added a tenth
    (71.9x) and MEKKO.HE's an eleventh (22.7x) the same day; both clear,
    and CRUS -- intaken between them -- does NOT form the ratio at all,
    because the SEC annual path tags no `finance_income_period` and E18
    refuses a net formed from one half. The census is deliberately exact
    rather than a lower bound: a new store that can form this ratio is a
    name whose side under E112 somebody has to have looked at, and a `>=`
    here would let one land unexamined."""
    from vss.manual import COVERAGE_MINIMUM, interest_coverage
    below, formed = [], []
    for path in sorted(MANUAL_DIR.glob("*.yaml")):
        if "bak" in path.name or path.stem == "TEMPLATE":
            continue
        parsed = load_manual(path.stem, directory=MANUAL_DIR)
        got = interest_coverage(parsed, section5_basis(parsed))
        if got.ratio is None:
            continue
        formed.append(path.stem)
        if got.ratio < COVERAGE_MINIMUM:
            below.append(path.stem)
    # E117 clause 5 (2026-09-19): an IFRS store forms coverage only RENT-
    # BEARING, which needs `rou_depreciation`; until the non-US backfill only
    # LIAB.ST carries it (4.87x rent-bearing, below 5x). SYNSAM.ST and the
    # other IFRS names drop out as DATA MISSING, not as passes.
    # C3 (2026-09-19) put LII's and ULTA's operating income and finance
    # lines on file: both form, both above 5x
    # AUTO.L joined 2026-09-19 with its ROU depreciation on file (rent-bearing 101x)
    # MC.PA joined 2026-09-19 (store built for A4; rent-bearing, above 5x)
    assert sorted(formed) == ["AUTO.L", "GDDY", "LIAB.ST", "LII", "MC.PA", "ULTA"], formed
    # E120 (2026-09-19): with note 30's 66 standing in, LIAB.ST is 6.72x
    # rent-bearing -- no stored name is below the limit
    assert below == [], below


# --- E108's measured limb, end to end (2026-09-08) -------------------------
#
# E108's words: perturb each leg by +/-10%, and a leg whose larger move is
# below 1% of `fv_base` is VERIFIED-EXEMPT. The gate implemented that
# correctly from the day it was written -- and it never fired once, because
# the map it looked up was keyed in the BRIDGE's vocabulary. These pin the
# limb end to end so the silence cannot come back.


def test_E108_measured_limb_exempts_a_below_floor_leg_by_its_store_name():
    """MEKKO.HE: cash and leases are under 1% and must be exempt.

    A LIVE-STORE TEST, deliberately, and of the same kind as E112's census:
    the defect was that the two halves of a lookup disagreed, and only a
    real store exercises both halves. `registered_view_sensitivity` reads
    the view FILE here -- MEKKO.HE has no watchlist entry, which is E109's
    own arrangement -- so this covers that path too.
    """
    parsed = load_manual("MEKKO.HE", directory=MANUAL_DIR)
    measured = registered_view_sensitivity(parsed)
    assert measured, "no measured limb at all -- the view was not read"

    for field_name in ("cash_and_equivalents", "lease_liabilities",
                       "finance_costs_paid", "finance_income_received"):
        assert field_name in measured, (field_name, sorted(measured))
        assert measured[field_name] < SENSITIVITY_FLOOR, field_name

    gate = section5_gate(parsed, as_of=date(2026, 9, 8),
                         measured_exempt=measured)
    blocking = {r.subject.split(" ", 1)[-1] for r in gate.refusals}
    for field_name in ("cash_and_equivalents", "lease_liabilities",
                       "finance_costs_paid", "finance_income_received"):
        assert field_name not in blocking, (field_name, sorted(blocking))


def test_E108_measured_limb_still_refuses_a_leg_above_the_floor():
    """The exemption must not become a blanket pass.

    MEKKO.HE's operating cash flow moves `fv_base` by about 10.7%. If the
    limb ever exempts it, the floor has stopped measuring.
    """
    parsed = load_manual("MEKKO.HE", directory=MANUAL_DIR)
    measured = registered_view_sensitivity(parsed)
    assert measured["operating_cash_flow"] > SENSITIVITY_FLOOR
    assert measured["diluted_weighted_average_shares"] > SENSITIVITY_FLOOR


def test_E108_reads_the_view_FILE_when_there_is_no_watchlist_entry():
    """E109's arrangement, not a new rule.

    E109 put the block on the watchlist entry and ruled in the same breath
    that a name with a registered view and no entry stays off the watchlist
    (E12 freezes Gate 1 at entry). Those names' views are real and dated and
    live in the file; without this the measured limb is dark for exactly the
    names E109 chose not to enter.

    THE FIXTURE MOVED FROM MEKKO.HE TO BOUV.OL ON 2026-09-08, and the move
    is the test working rather than the test breaking. MEKKO.HE was ruled
    WATCH-GATED that afternoon, which gave it its first watchlist entry and
    with it an E109 block -- so it stopped being an instance of the case
    this test guards, and the premise assertion said so out loud instead of
    letting the test pass on a path it was no longer exercising. BOUV.OL is
    now the only name in the repo with a registered view, a store and NO
    watchlist entry; if it ever gains one, this assertion fires again and
    the fixture moves again rather than the guard being deleted.
    """
    from vss.config import load_watchlist

    parsed = load_manual("BOUV.OL", directory=MANUAL_DIR)
    on_watchlist = any(e.ticker == "BOUV.OL"
                       for e in load_watchlist(Path("config/watchlist.yaml")))
    assert not on_watchlist, "the premise of this test has changed"
    assert registered_view_record(parsed) is not None


def test_E108_scales_E18_halves_off_the_net_exactly():
    """The record holds the net; the gate refuses on the two halves.

    The scaling is exact because the valuation is linear in FCF0: a half
    perturbed by 10% moves the net by 10% of the HALF, so its share of the
    net's move is |half| / |net|.
    """
    parsed = load_manual("MEKKO.HE", directory=MANUAL_DIR)
    basis = section5_basis(parsed)
    measured = registered_view_sensitivity(parsed)

    net = subtracted_on_basis(parsed, basis, "net_interest_paid")
    for half in ("finance_costs_paid", "finance_income_received"):
        value = resolve_on_basis(parsed, basis, half).value
        assert measured[half] == pytest.approx(
            measured["net_interest_paid"] * abs(value) / abs(net), rel=1e-9)


# --- E113 (2026-09-08): a field fv_base never reads cannot block ----------


def test_no_field_that_ever_reaches_a_valuation_is_exempt_under_E113():
    """THE GUARD E113's OWN TEXT NAMES, and the one that matters most.

    E113 exempts a field the arithmetic never reads. If a field on the list
    ever DOES reach `fv_base`, the gate would stop refusing on a leg that
    moves the answer -- the one failure mode this whole area must not have.
    Checked against every committed store, so a schema change that wires a
    listed field into the valuation fails here.
    """
    from datetime import datetime, timezone

    from vss import runrecord as R

    reached: set[str] = set()
    for path in sorted(MANUAL_DIR.glob("*.yaml")):
        if "bak" in path.name or path.stem == "TEMPLATE":
            continue
        parsed = load_manual(path.stem, directory=MANUAL_DIR)
        basis = section5_basis(parsed)
        if basis is None:
            continue
        record = R.from_store(parsed, basis, run_ts=datetime.now(timezone.utc),
                              growth=R.Growth(base=0.03, view_file="test"))
        reached |= set(record.leg_values())
    assert reached, "no record built -- the test proves nothing"
    assert NON_VALUATION_FIELDS & reached == set(), (
        NON_VALUATION_FIELDS & reached)


def test_E113_does_not_list_a_field_that_participates_for_some_filer_shape():
    """The list is REASONED, never derived from what was observed.

    Each of these is absent from every record built on 2026-09-08 and each
    reaches `fv_base` for a filer shape no committed store happens to have.
    A list built by subtracting what was seen would have swallowed all of
    them, and the gate would then stop refusing on a real leg the day such
    a filer arrived.
    """
    for field_name in ("net_finance_costs",          # E34.1's interest leg
                       "finance_costs_period",       # E61's
                       "finance_costs_paid",         # E18's halves of E34's
                       "finance_income_received",
                       "income_tax_paid",            # a pre-tax OCF pair
                       "operating_cash_flow_pretax",
                       "noncurrent_derivative_assets_on_debt"):
        assert field_name not in NON_VALUATION_FIELDS, field_name


def test_E113_exempts_and_the_gate_SAYS_SO():
    """An exemption nobody can see is the failure this area already had."""
    parsed = load_manual("MEKKO.HE", directory=MANUAL_DIR)
    gate = section5_gate(parsed, as_of=date(2026, 9, 8),
                         measured_exempt=registered_view_sensitivity(parsed))
    named = [f for f in gate.flags if "E113" in f.detail]
    assert named, "E113 exempted nothing, or exempted it silently"
    subjects = {f.subject.split(" ", 1)[-1] for f in named}
    assert "revenue" in subjects and "net_income" in subjects, subjects
    assert all("NEVER READS" in f.detail for f in named)


def test_E113_conditional_half_follows_the_file_s_own_declarations():
    """E117 (E70 before it) and E34 settle these per file, not per schema.

    Since E117 (2026-09-19) an IFRS 16 filer's `lease_payments_capital` and
    `lease_interest_paid` are DEDUCTED and must NOT be exempt; a US GAAP
    filer's flow bears the rent, so neither is read and both are.
    """
    ifrs = load_manual("MEKKO.HE", directory=MANUAL_DIR)
    assert ifrs.operating_leases_in_ocf.value is False
    assert "lease_payments_capital" not in non_valuation_fields(ifrs)
    assert "lease_interest_paid" not in non_valuation_fields(ifrs)
    assert "operating_lease_payments" in non_valuation_fields(ifrs)
    # THE INTEREST FIELDS FOLLOW E60, NOT E34's chosen leg. This filer's
    # FCF0 reads `net_interest_paid`, so the OTHER shape's own operand
    # `finance_income_period` is out of the arithmetic -- but
    # `net_finance_costs` and its operands are read REGARDLESS, by E25's
    # zero-coverage-denominator gate, outside FCF0 entirely. A field
    # another gate limb reads is not one E113 may excuse.
    assert "net_interest_paid" not in non_valuation_fields(ifrs)
    assert "net_finance_costs" not in non_valuation_fields(ifrs)
    assert "finance_costs_period" not in non_valuation_fields(ifrs)

    us = load_manual("DECK", directory=MANUAL_DIR)
    assert us.operating_leases_in_ocf.value is True
    assert "lease_payments_capital" in non_valuation_fields(us)
    assert "operating_lease_payments" in non_valuation_fields(us)


def test_E113_leaves_every_real_valuation_leg_refusing_on_BOUV_OL():
    """The exemption must not become a blanket pass.

    BOUV.OL's store is entirely UNVERIFIED. After E108 and E113 the legs
    still refused must be exactly the ones that MOVE the value -- the flow
    legs, the capex pair and the divisor.
    """
    parsed = load_manual("BOUV.OL", directory=MANUAL_DIR)
    gate = section5_gate(parsed, as_of=date(2026, 9, 8),
                         measured_exempt=registered_view_sensitivity(parsed))
    still = {r.subject.split(" ", 1)[-1]
             for r in gate.refusals if r.kind == "UNVERIFIED"}
    assert still == {"operating_cash_flow", "diluted_weighted_average_shares",
                     "capex_ppe", "capex_intangibles", "sbc",
                     # E117 (2026-09-19): the lease principal is now DEDUCTED
                     "lease_payments_capital",
                     # read by E25's coverage gate, outside FCF0 (E60)
                     "net_finance_costs",
                     # E80's pair: operands of a count the gate computes
                     "shares_issued_period_end", "treasury_shares_period_end",
                     }, still


def test_E115_hrb_adds_back_interest_paid_alone_as_a_named_one_sided_proxy():
    """E115 (2026-09-18): the fourth interest shape.

    HRB states interest PAID as cash (76,728,000), states no interest
    received anywhere in the filing or the taxonomy, states no
    income-statement net, and files its gross expense under
    `InterestExpenseDebt`, which `finance_costs_period` does not read. So
    E34's pair, E34.1's accrual net and E61's gross leg all fail to form
    and FCF0 refused. The add-back is interest paid ALONE -- and it is NOT
    the net: E34.1's sentence stands and the collision is named.
    """
    from vss.manual import FCF0_RATIO, RATIO_OK, interest_legs
    parsed = load_manual("HRB", directory=MANUAL_DIR)
    assert parsed.interest_in_ocf.cash_paid_only_proxy
    assert not parsed.interest_in_ocf.accrual_proxy
    assert not parsed.interest_in_ocf.interest_expense_only_proxy
    # THE LEG IS THE CASH FIGURE, not `net_interest_paid` (which this filer
    # can never form) and not `finance_costs_period` (never tagged).
    assert interest_legs(parsed) == ("finance_costs_paid",)
    basis = section5_basis(parsed)
    assert basis.label == "annual FY2026"
    states = {r.name: r.state for r in section5_gate(parsed, as_of=AS_OF).ratios}
    assert states[FCF0_RATIO] == RATIO_OK
    # E68.1 / E35.1: both legs are caption zeros, so net debt forms.
    assert states["net debt"] == RATIO_OK
