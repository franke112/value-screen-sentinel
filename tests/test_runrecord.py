"""The section 5 run record: every input and every choice, or no fair value.

REVIEW-4 report C Part 11 asked one question of four different records --
the store row, the watchlist entry, the `vss manual` report and the emitted
XBRL file -- and got the same answer from all four: **no record produced by
the code holds more than one of the nine input classes a fair value stands
on.** For the two HELD names the record is a prose paragraph; SAP.DE's
carries one date, LIAB.ST's carries none.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from vss import manual as M
from vss import runrecord as R

RUN_TS = datetime(2026, 8, 26, 22, 30, tzinfo=ZoneInfo("Europe/Stockholm"))

#: E25's `note` basis, and the reason it is a HAND input rather than a
#: fetched one: Deckers tags no `LongTermDebt*` element at all, and absence
#: of a tag is DATA MISSING -- inventing a zero from one is the substitution
#: the XBRL path exists not to make. So the zero is entered once, HERE, with
#: its page, and the record then needs no hand input to be replayed.
DECK_HAND_INPUTS = (
    R.Input("financial_liabilities_current", 0.0,
            "10-Q 0000910521-26-000022, Liquidity: \"we made no borrowings\" "
            "-- E25 `note` basis; Deckers tags no LongTermDebt element and "
            "absence of a tag is DATA MISSING, not zero", "hand"),
    R.Input("financial_liabilities_noncurrent", 0.0,
            "10-Q 0000910521-26-000022, Liquidity: \"we made no borrowings\" "
            "-- E25 `note` basis", "hand"),
    # E35.1: Deckers tags no defined-benefit liability, and absence of a tag
    # is DATA MISSING. The 10-K's employee-benefit note describes only
    # defined CONTRIBUTION plans, and that sentence is the evidence for the
    # zero -- E25's `note` form, the weakest of the three, and labelled so.
    R.Input("pension_deficit", 0.0,
            "10-K 0001628280-26-037664, Employee Benefit Plans: 'The Company "
            "has various defined contribution plans' and 'a 401(k) defined "
            "contribution plan'; no defined-benefit plan is described. E25 "
            "`note` basis on the absence of any DB disclosure in the plan "
            "note -- the weakest form, stated as such", "hand"),
    # E68 (2026-08-29): the asset-retirement leg is required on the pension
    # leg's terms. This was a TEST-FIXTURE zero while the store lacked the
    # leg. SUPERSEDED 2026-08-30: the store's FY2026 entry now carries
    # 36,790,000 -- the 10-K's ARO roll-forward closes at 'Ending balance
    # $ 36,790', which IS the tagged `AssetRetirementObligationsNoncurrent`
    # (the whole obligation is recorded in other long-term liabilities), so
    # the earlier doubt that the tag was "a part" is answered by the
    # filing. `from_store` takes the store's leg over this hand zero; the
    # zero stays here only so a store STRIPPED of the leg still completes.
    R.Input("asset_retirement_obligation", 0.0,
            "TEST FIXTURE (superseded by the store, 2026-08-30): E68 hand zero "
            "so a stripped DECK-shaped record completes", "hand"),
    R.Input("prepaid_delivery_obligation", 0.0, "TEST FIXTURE: E81's leg, a hand zero so the record completes", "hand"),
    R.Input("nci_dividends_paid", 0.0, "TEST FIXTURE: E105's leg, a hand zero so the record completes", "hand"),
    # E34.1 RETIRED THE HAND INPUT THAT STOOD HERE. The first build entered
    # interest PAID (2,492,000) as the net by hand, declared generous. The
    # ruling says interest paid alone is NEVER the net: the store now carries
    # the income statement's pair (`InterestExpenseNonoperating` 2,530,000
    # and `InvestmentIncomeInterest` 63,613,000) and E18 forms
    # `net_finance_costs` = -61,083,000 -- a net INCOME, REMOVED from FCF0
    # as an accrual proxy. Nothing about interest is entered by hand now.
)

DECK_GROWTH = R.Growth(base=0.035, view_file="reference/growth-views/DECK.md",
                       view_date=date(2026, 8, 25), bear=0.0, bull=0.08)


def deck_record(**overrides) -> R.RunRecord:
    """DECK's FY2026 store basis, as a record, under E34-E38."""
    parsed = M.load_manual("DECK", directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    kwargs = dict(growth=DECK_GROWTH, run_ts=RUN_TS,
                  hand_inputs=DECK_HAND_INPUTS,
                  rate=R.Rate(core_expected_return=0.070, premium=0.025),
                  tool_commit="REVIEW-4 build, 2026-08-26")
    kwargs.update(overrides)
    return R.from_store(parsed, basis, **kwargs)


# --- the test Phase 3 asks for --------------------------------------------


def test_DECK_131_74_REGENERATES_FROM_ITS_RECORD_ALONE():
    """The test Phase 3 asks for, and 131.74 is B36's figure.

    B36's 131.74 was struck on three choices three rulings have since moved:
    SBC ADDED BACK (E36 deducts it), NO interest add-back (E34 adds it), and
    LEASES OUT of net debt (E35 puts them in). A record holds a SUPERSEDED
    run as faithfully as a live one -- that is what E39 says history is for
    -- so the figure comes back out of one, from plain data, with no file
    opened and no hand input asked for.
    """
    live = deck_record()
    as_b36_struck_it = R.RunRecord.from_dict({
        **live.to_dict(),
        # E36: SBC was inside FCF0, added back as filed
        "sbc": {"treatment": R.SBC_ADDED_BACK, "amount": 44_835_000.0},
        # E34: no add-back was made, and this does NOT say interest was nil
        "interest": {"in_operating_cash_flow": True,
                     "page": "ASC 230-10-45-17(d); the B36 run made NO "
                             "add-back. Interest paid was 2,492,000, not nil",
                     "net_interest_paid": 0.0},
        # E35: leases were OUT, so net debt is cash alone, as net CASH
        "bridge": {**live.to_dict()["bridge"],
                   "net_debt": -1_907_249_000.0,
                   "note": "SUPERSEDED by E35: operating leases 375,194,000 "
                           "were OUT of the bridge"},
        # E70: the lease payments the flow bore stayed in it
        "lease": {"in_operating_cash_flow": None, "page": "the B36 run predates E70: no add-back, and this does NOT say the flow bore no lease", "principal_added_back": None, "leg": ""},
    })
    assert as_b36_struck_it.complete
    assert as_b36_struck_it.strike() == pytest.approx(131.74, abs=0.005)
    # from PLAIN DATA, round-tripped as a file would carry it
    assert R.replay(json.loads(json.dumps(as_b36_struck_it.to_dict()))) == \
        pytest.approx(131.74, abs=0.005)


def test_the_three_rulings_that_moved_it_each_move_it_by_a_stated_amount():
    """OLD VALUE, NEW VALUE, RULING -- from one record, one step at a time."""
    live = deck_record()
    data = live.to_dict()
    b36 = {"sbc": {"treatment": R.SBC_ADDED_BACK, "amount": 44_835_000.0},
           "interest": {"in_operating_cash_flow": True, "page": "ASC 230",
                        "net_interest_paid": 0.0},
           "bridge": {**data["bridge"], "net_debt": -1_907_249_000.0},
           "lease": {"in_operating_cash_flow": None, "page": "the B36 run predates E70: no add-back, and this does NOT say the flow bore no lease", "principal_added_back": None, "leg": ""}}

    start = R.RunRecord.from_dict({**data, **b36})
    assert start.strike() == pytest.approx(131.74, abs=0.005)

    # E68 (2026-08-30) put 36,790,000 of asset retirement obligations into
    # the live bridge. The four steps below are the chain AS IT STOOD before
    # that leg existed, so the bridge is taken without it; E68 is then the
    # last step, with its own stated amount.
    ARO = 36_790_000.0
    # E117 (2026-09-19) took the 375,194,000 operating lease liability back
    # OUT of the live bridge; every step before it stood with it in.
    OPL = 375_194_000.0
    e70_bridge = {**data["bridge"], "net_debt": data["bridge"]["net_debt"] + OPL,
                  "items": {**data["bridge"]["items"], "leases": OPL}}
    e70_lease = {"in_operating_cash_flow": True, "page": "ASC 842-20-45-5(a)",
                 "principal_added_back": 92_823_000.0,
                 "leg": "`operating_lease_payments`"}
    pre_e68 = {**e70_bridge, "net_debt": e70_bridge["net_debt"] - ARO}

    # E35: leases into the bridge -- 375,194,000 of them
    plus_e35 = R.RunRecord.from_dict(
        {**data, **b36, "bridge": pre_e68})
    assert plus_e35.strike() == pytest.approx(129.16, abs=0.005)

    # E36: share-based compensation deducted -- 44,835,000
    plus_e36 = R.RunRecord.from_dict({**data, **b36, "bridge": pre_e68,
                                      "sbc": data["sbc"]})
    assert plus_e36.strike() == pytest.approx(124.31, abs=0.005)

    # E34 / E34.1: the income statement's net, -61,083,000 -- an INCOME,
    # removed as an accrual proxy. The first build's 124.58 stood on the
    # 2,492,000 of interest PAID read as the net; E34.1 retired that.
    assert live.interest.accrual_proxy
    assert live.interest.net_interest_paid == pytest.approx(-61_083_000.0)
    pre_e70 = R.RunRecord.from_dict({**data, "bridge": pre_e68, "lease": {"in_operating_cash_flow": None, "page": "the B36 run predates E70: no add-back, and this does NOT say the flow bore no lease", "principal_added_back": None, "leg": ""}})
    assert pre_e70.strike() == pytest.approx(117.71, abs=0.005)

    # E70: the 92,823,000 of operating lease payments the flow bore are added
    # back -- the lease is already in the bridge (E35), so the flow does not
    # charge it a second time. The correction RAISES the value.
    e70 = R.RunRecord.from_dict({**data, "bridge": pre_e68, "lease": e70_lease})
    assert e70.strike() == pytest.approx(127.75, abs=0.005)

    # E68 (2026-08-30): the asset retirement obligation the 10-K states --
    # 36,790,000, the roll-forward's ending balance, tagged as
    # AssetRetirementObligationsNoncurrent -- enters the bridge (E68 via
    # the store, not a hand input). The leg LOWERS the value, by 0.25.
    e68 = R.RunRecord.from_dict({**data, "bridge": e70_bridge, "lease": e70_lease})
    assert e68.strike() == pytest.approx(127.49, abs=0.005)

    # E117 (2026-09-19): RENT IS AN OPERATING COST. The 92,823,000 add-back
    # is reversed and the 375,194,000 operating lease liability leaves net
    # debt. The value FALLS, to option B's figure in the E34 prep.
    assert live.lease.rule == "E117" and live.lease.in_operating_cash_flow
    assert live.lease.principal_added_back is None
    assert live.lease.liability_excluded == pytest.approx(OPL)
    assert live.bridge.net_debt == pytest.approx(e70_bridge["net_debt"] - OPL)
    assert live.strike() == pytest.approx(120.03, abs=0.005)


def test_the_record_is_INPUTS_not_a_stored_answer():
    """A convention change moves a replayed value instead of leaving every
    stored fv_base looking current (report C 11.2, defect vi)."""
    record = deck_record()
    at_ten = record.strike()
    at_five = R.RunRecord.from_dict(
        {**record.to_dict(),
         "conventions": {**record.to_dict()["conventions"],
                         "horizon_years": 5}}).strike()
    assert at_five != at_ten


# --- a run without a complete record does not print a fair value ----------


def test_an_incomplete_record_REFUSES_and_names_every_gap(tmp_path):
    # The committed DECK store has carried its five net-debt legs since
    # 2026-08-30, so it completes with no hand input at all. A store
    # STRIPPED of them (everything after the marker line the legs were
    # added under) is what this test is about: nothing entered by hand.
    text = (M.MANUAL_DIR / "DECK.yaml").read_text(encoding="utf-8")
    marker = "      # --- net debt legs the rulings of 2026-08-29/30 added"
    assert marker in text
    (tmp_path / "DECK.yaml").write_text(text.split(marker)[0], encoding="utf-8")
    parsed = M.load_manual("DECK", directory=tmp_path)
    record = R.from_store(parsed, M.section5_basis(parsed), growth=DECK_GROWTH,
                          run_ts=RUN_TS, hand_inputs=(),
                          rate=R.Rate(core_expected_return=0.070, premium=0.025))
    assert not record.complete
    with pytest.raises(R.RecordError, match="INCOMPLETE"):
        record.strike()
    with pytest.raises(R.RecordError):
        record.band()
    assert "NO FAIR VALUE IS PRINTED" in record.render()


@pytest.mark.parametrize("gap, patch", [
    ("share count", {"shares": {"count": None, "basis": "x",
                                "as_of": "2026-03-31"}}),
    ("share-based compensation amount",
     {"sbc": {"treatment": R.SBC_DEDUCTED, "amount": None}}),
    ("the growth view", {"growth": {"base": 0.035, "view_file": ""}}),
])
def test_each_missing_declaration_is_named_on_its_own(gap, patch):
    record = R.RunRecord.from_dict({**deck_record().to_dict(), **patch})
    assert any(gap in m for m in record.missing()), record.missing()
    with pytest.raises(R.RecordError, match="INCOMPLETE"):
        record.strike()


def test_provenance_is_required_of_every_input():
    with pytest.raises(R.RecordError, match="no provenance"):
        R.Input("operating_cash_flow", 1.0, "")
    with pytest.raises(R.RecordError, match="entered_by"):
        R.Input("operating_cash_flow", 1.0, "10-K", "guesswork")


def test_there_is_no_third_SBC_treatment():
    with pytest.raises(R.RecordError, match="not a treatment"):
        R.SbcTreatment("not stated", 44.8)


# --- what the record makes visible ----------------------------------------


def test_the_record_says_whether_the_three_dates_AGREE():
    """DECK's 140.95 paired a July divisor with June cash (+0.32); B36's
    140.81 paired a July divisor with MARCH cash (+3.59)."""
    agree = R.AsOfDates(date(2026, 3, 31), date(2026, 3, 31), date(2026, 3, 31))
    disagree = R.AsOfDates(date(2026, 6, 30), date(2026, 6, 30), date(2026, 7, 9))
    assert agree.agree and not disagree.agree
    assert "**THEY AGREE**" in deck_record().render()


def test_the_record_declares_every_bridge_item_including_the_absent_ones():
    """Every bridge item is named, and each one says WHICH KIND of absence
    it is rather than leaving a reader to notice (report A 4.1)."""
    rendered = deck_record().render()
    for item in R.BRIDGE_ITEMS:
        assert f"`{item}`" in rendered
    # THREE states now, and they are different facts. DATA MISSING is about
    # this basis. "no field in this schema" is about the vocabulary itself
    # -- and E105 (2026-09-04) emptied that state on the last item holding
    # it: the minority is no longer an absence in the bridge, it is an
    # ANSWER, given in the FLOW, and the bridge says where to look.
    assert R.NO_FIELD not in rendered
    assert R.NCI_IN_THE_FLOW in rendered
    assert "E105 deducts the dividends PAID to minorities in the FLOW" \
        in rendered
    assert deck_record().bridge.items["pensions"] == 0.0
    assert "**DATA MISSING** on this basis" in rendered  # the A1 line


def test_E105_a_record_struck_before_the_ruling_is_complete_as_struck():
    """A RECORD IS A STATEMENT MADE ON A DATE UNDER THE RULES OF THAT DATE.

    Every run record this project keeps was struck before 2026-09-04, none
    of them carries the leg, and none of them is INCOMPLETE for want of it.
    What DOES change is the store: a record struck TODAY carries the leg or
    refuses, and the affected names are re-struck rather than patched.
    """
    old = R.RunRecord.from_dict({**deck_record().to_dict(),
                                 "nci_dividends_paid": None})
    assert old.nci_predates_the_ruling
    assert not old.missing()
    assert old.strike() == pytest.approx(deck_record().strike())
    struck_today = R.RunRecord.from_dict({
        **deck_record().to_dict(), "nci_dividends_paid": None,
        "run_ts": datetime(2026, 9, 4, 12, 0,
                           tzinfo=ZoneInfo("Europe/Stockholm")).isoformat()})
    assert not struck_today.nci_predates_the_ruling
    assert any("non-controlling interests (E105)" in gap
               for gap in struck_today.missing())


def test_the_record_carries_E37_s_declaration_for_a_non_usd_run():
    from vss.valuation import NON_USD_BIAS_DECLARATION
    usd = deck_record()
    assert NON_USD_BIAS_DECLARATION not in usd.render()
    eur = R.RunRecord.from_dict({**usd.to_dict(), "currency": "EUR"})
    assert NON_USD_BIAS_DECLARATION in eur.render()


def test_a_declared_convention_that_is_not_wired_REFUSES():
    """The conventions are declared so a CHANGE fails loudly rather than
    moving every stored figure in silence (report C 11.2, defect vi)."""
    record = R.RunRecord.from_dict(
        {**deck_record().to_dict(),
         "conventions": {"horizon_years": 10, "terminal_growth": 0.025,
                         "mid_year": True, "first_year_flow": "FCF0 * (1 + g)"}})
    with pytest.raises(R.RecordError, match="MID-YEAR"):
        record.strike()


def test_the_hand_input_is_IN_the_record_and_is_marked_as_one():
    rendered = deck_record().render()
    assert "| hand |" in rendered
    assert "we made no borrowings" in rendered
    assert "E25 `note` basis" in rendered


def test_the_anchor_gap_is_stated_when_the_record_does_not_carry_one():
    bare = R.RunRecord.from_dict({**deck_record().to_dict(), "rate": {}})
    assert "anchor NOT RECORDED" in bare.rate.anchor_sentence
    assert "cannot fire" in bare.render()


# --- absent is never zero, and it is never `no` ---------------------------


def _bare_file(**extra):
    """A file with every FCF0 leg but CAPEX, so the sum has a hole in it."""
    fig = lambda v, **kw: {"value": v, "page": "1", "status": "VERIFIED", **kw}
    doc = {"ticker": "NOCAPEX.XX", "name": "No Capex",
           "reporting_currency": "EUR", "quote_currency": "EUR",
           "reporting_frequency": "half_yearly",
           "periods": [{"period": "2025-FY", "period_end": "2025-12-31",
                        "period_basis": "calendar", "document": "d",
                        "figures": {
                            "operating_cash_flow": fig(1000.0),
                            "sbc": fig(20.0),
                            "cash_and_equivalents": fig(100.0),
                            "financial_liabilities_current":
                                fig(0.0, zero_basis="caption"),
                            "financial_liabilities_noncurrent":
                                fig(0.0, zero_basis="caption"),
                            "lease_liabilities": fig(50.0),
                            "diluted_weighted_average_shares": fig(100.0)}}],
           **extra}
    parsed = M.parse_manual(doc, path=Path("NOCAPEX.XX.yaml"))
    return R.from_store(parsed, M.section5_basis(parsed),
                        growth=R.Growth(0.03, "views/X.md"), run_ts=RUN_TS)


def test_an_absent_capex_is_DATA_MISSING_and_never_a_zero():
    """It was a zero, and the record called itself complete.

    `manual.capex_legs` returns the SPLIT PAIR even when neither shape is on
    the basis, so summing `leg(name) or 0.0` over it produced a capex of
    nought for a file whose capital spending is DATA MISSING -- and
    `missing()` never saw it, because an absent leg records no input. The
    fair value that came out overstated FCF0 by the whole of a filer's
    capital spending.
    """
    record = _bare_file(interest_in_ocf={"value": False, "source": "x",
                                         "page": "1"})
    assert record.capex is None
    assert not record.complete
    assert any("capex" in gap for gap in record.missing())
    with pytest.raises(R.RecordError, match="INCOMPLETE"):
        record.strike()


def test_an_unrecorded_interest_classification_is_not_the_same_as_NO():
    """`bool(None)` is False, and saying interest sits OUTSIDE operating
    cash flow is a POSITIVE CLAIM about a filer."""
    record = _bare_file()
    assert record.interest.in_operating_cash_flow is None
    assert "NOT RECORDED" in record.interest.sentence
    assert any("where this filer books its interest" in gap
               for gap in record.missing())


def test_E40_the_record_prints_the_verification_kind_beside_every_input():
    record = deck_record()
    by_name = {i.name: i for i in record.inputs}
    assert by_name["operating_cash_flow"].verified == "VERIFIED (tagged)"
    assert by_name["financial_liabilities_current"].verified == "hand"
    assert by_name["net_finance_costs"].verified == "VERIFIED (tagged)"   # E18 pair
    assert "| verified (E40) |" in record.render()


def test_E41_the_record_dates_an_annual_only_count_on_its_own_year_end():
    """SAP's shape: flows to 2026-06-30, count and SBC from FY2025. The
    record says THEY DO NOT AGREE and names the date that differs."""
    from tests.test_manual import four_quarters, figure, parse, INTEREST_NO
    doc = four_quarters(each={"operating_cash_flow": figure(100.0),
                              "capex_combined": figure(-10.0),
                              "cash_and_equivalents": figure(50.0),
                              "financial_liabilities_current": figure(5.0),
                              "financial_liabilities_noncurrent": figure(20.0),
                              "lease_liabilities": figure(8.0)})
    doc["annual"] = [{"fiscal_year": 2025, "period_end": "2025-12-31",
                      "document": "20-F", "figures": {
                          "sbc": figure(40.0),
                          "diluted_weighted_average_shares": figure(1175.0)}}]
    doc["interest_in_ocf"] = INTEREST_NO
    parsed = parse(doc)
    basis = M.section5_basis(parsed)
    record = R.from_store(parsed, basis, run_ts=RUN_TS,
                          growth=R.Growth(base=0.05, view_file="x.md"))
    assert record.shares.as_of == date(2025, 12, 31)
    assert record.dates.share_count == date(2025, 12, 31)
    assert record.dates.flows_window_end == date(2026, 6, 30)
    assert not record.dates.agree
    assert "E41" in record.sbc.basis
    rendered = record.render()
    assert "THEY DO NOT AGREE** (share count 2025-12-31 against flows to 2026-06-30)" in rendered
    assert "for annual FY2025 (E41" in rendered


def test_E88_the_record_divides_by_the_annual_average_and_flags_the_mismatch():
    """Zinzino's shape under E88 (2026-08-30, reversing E75): the record
    divides by the ANNUAL average, dated on its own year end -- the share
    date now DISAGREES with the window end, which the record prints as
    E88's flag -- and the window-end count is memo in the why, never an
    input."""
    from tests.test_manual import four_quarters, figure, parse, INTEREST_NO
    # no per-quarter diluted set (that is E91's case, below) -- E88's
    # annual fall-back is what this record exercises
    doc = four_quarters(each={"operating_cash_flow": figure(100.0),
                              "capex_combined": figure(-10.0),
                              "cash_and_equivalents": figure(50.0),
                              "financial_liabilities_current": figure(5.0),
                              "financial_liabilities_noncurrent": figure(20.0),
                              "lease_liabilities": figure(8.0)})
    doc["periods"][-1]["figures"]["shares_outstanding_period_end"] = figure(39_165_998)
    doc["annual"] = [{"fiscal_year": 2025, "period_end": "2025-12-31",
                      "document": "AR", "figures": {
                          "sbc": figure(40.0),
                          "diluted_weighted_average_shares": figure(37_530_107)}}]
    doc["interest_in_ocf"] = INTEREST_NO
    parsed = parse(doc)
    basis = M.section5_basis(parsed)
    record = R.from_store(parsed, basis, run_ts=RUN_TS,
                          growth=R.Growth(base=0.05, view_file="x.md"))
    assert record.shares.count == 37_530_107
    assert record.shares.divisor_basis == "weighted_average"
    assert record.shares.prior_average is None and record.shares.drift is None
    assert record.shares.as_of == date(2025, 12, 31) == record.dates.share_count
    assert not record.dates.agree
    assert not any(i.name == "shares_outstanding_period_end" for i in record.inputs)
    assert "E88" in record.shares.basis and "MEMO" in record.shares.basis
    rendered = record.render()
    assert "divisor basis `weighted_average` (E75 / E75.1 / E88 / E91)" in rendered
    assert "mismatch" in rendered
    # a record round-trips with the declaration
    again = R.RunRecord.from_dict(record.to_dict())
    assert again.shares.divisor_basis == "weighted_average" and again.shares.as_of == record.shares.as_of
    # records struck under E75 STAND (E88): their labels still read back,
    # and E75's short-lived `period_end` maps to the basic kind it was
    raw_old = record.to_dict(); raw_old["shares"]["divisor_basis"] = "period_end_basic"
    assert R.RunRecord.from_dict(raw_old).shares.divisor_basis == "period_end_basic"
    raw_old["shares"]["divisor_basis"] = "period_end"
    assert R.RunRecord.from_dict(raw_old).shares.divisor_basis == "period_end_basic"
    raw = record.to_dict()
    for key in ("divisor_basis", "prior_average", "drift"):
        raw["shares"].pop(key)
    assert R.RunRecord.from_dict(raw).shares.divisor_basis == "weighted_average"


def test_E91_the_record_divides_by_the_day_weighted_window_average():
    """E91 (2026-08-30): four stated per-quarter diluted counts -> the
    record divides by the coded day-weighted average, the window's OWN
    average, so the three dates AGREE again; the four operands reach the
    record as one store input."""
    from tests.test_manual import four_quarters, figure, parse, INTEREST_NO
    doc = four_quarters(each={"operating_cash_flow": figure(100.0),
                              "capex_combined": figure(-10.0),
                              "cash_and_equivalents": figure(50.0),
                              "financial_liabilities_current": figure(5.0),
                              "financial_liabilities_noncurrent": figure(20.0),
                              "lease_liabilities": figure(8.0)})
    for q, count in zip(doc["periods"], (1_172e6, 1_172e6, 1_168e6, 1_158e6)):
        q["figures"]["diluted_weighted_average_shares"] = figure(count)
    doc["annual"] = [{"fiscal_year": 2025, "period_end": "2025-12-31",
                      "document": "AR", "figures": {
                          "sbc": figure(40.0),
                          "diluted_weighted_average_shares": figure(1_175_000_000)}}]
    doc["interest_in_ocf"] = INTEREST_NO
    parsed = parse(doc)
    basis = M.section5_basis(parsed)
    record = R.from_store(parsed, basis, run_ts=RUN_TS,
                          growth=R.Growth(base=0.05, view_file="x.md"))
    assert record.shares.count == pytest.approx(1_167_523_287.67, abs=0.5)
    assert record.shares.divisor_basis == "window_day_weighted"
    assert record.shares.as_of == date(2026, 6, 30) == record.dates.share_count
    assert record.dates.agree
    assert any(i.name == "diluted_weighted_average_shares" for i in record.inputs)
    assert "E91" in record.shares.basis and "x 92d" in record.shares.basis
    rendered = record.render()
    assert "divisor basis `window_day_weighted` (E75 / E75.1 / E88 / E91)" in rendered
    again = R.RunRecord.from_dict(record.to_dict())
    assert again.shares.divisor_basis == "window_day_weighted"
    assert again.shares.count == record.shares.count


# --- units: the store DECLARES them, the record divides on them -------------
#
# `from_store` divided raw store units. A file in millions with a whole-number
# share count (PNDORA.CO: DKK millions beside 77,189,151 shares; SYNSAM.ST the
# same shape) came out a millionfold too small per share, and LIAB.ST only
# divided correctly because its count had been typed in millions to match.
# The store now declares `money_unit` and `share_unit`; the record carries
# both and `legs()` normalises to whole units before any division.


def _unit_file(*, count, money_unit=None, share_unit=None):
    """A millions-scale year: OCF 1,000, capex -100, SBC nil, cash 500, no
    debt, no leases, no pension -- FCF0 900 and net cash 500, in millions --
    and a diluted count typed as ``count`` in ``share_unit``."""
    fig = lambda v, **kw: {"value": v, "page": "1", "status": "VERIFIED", **kw}
    doc = {"ticker": "UNITS.XX", "name": "Units", "reporting_currency": "DKK",
           "quote_currency": "DKK", "reporting_frequency": "half_yearly",
           "interest_in_ocf": {"value": False, "source": "x", "page": "1"},
           "periods": [{"period": "2025-FY", "period_end": "2025-12-31",
                        "period_basis": "calendar", "document": "d",
                        "figures": {
                            "operating_cash_flow": fig(1000.0),
                            "capex_combined": fig(-100.0),
                            "sbc": fig(0.0, zero_basis="note"),
                            "cash_and_equivalents": fig(500.0),
                            "financial_liabilities_current":
                                fig(0.0, zero_basis="caption"),
                            "financial_liabilities_noncurrent":
                                fig(0.0, zero_basis="caption"),
                            "lease_liabilities": fig(0.0, zero_basis="caption"),
                            "pension_deficit": fig(0.0, zero_basis="caption"),
                            "asset_retirement_obligation":
                                fig(0.0, zero_basis="caption"),
                            "prepaid_delivery_obligation":
                                fig(0.0, zero_basis="caption"),          # E81
                            "diluted_weighted_average_shares": fig(count)}}]}
    if money_unit is not None:
        doc["money_unit"] = money_unit
    if share_unit is not None:
        doc["share_unit"] = share_unit
    parsed = M.parse_manual(doc, path=Path("UNITS.XX.yaml"))
    return R.from_store(parsed, M.section5_basis(parsed),
                        growth=R.Growth(0.03, "views/X.md"), run_ts=RUN_TS)


#: THE HAND CALCULATION, in whole units: FCF0 900,000,000 growing 3% for ten
#: years at r 9.5%, terminal 2.5%, plus net cash 500,000,000, over 80,000,000
#: shares. `equity_value_per_share` on those whole figures gives 177.18; the
#: raw millions-over-whole division gave 0.000177.
HAND_PER_SHARE = 177.18


def test_units_a_PNDORA_shaped_file_divides_to_the_hand_calculation():
    """Money in millions, the count in WHOLE shares -- the shape that was
    out by 1e6."""
    from vss.valuation import equity_value_per_share
    record = _unit_file(count=80_000_000.0, money_unit="millions",
                        share_unit="whole")
    assert record.complete
    legs = record.legs()
    assert legs == R.Legs(fcf0=900e6, net_cash=500e6, shares=80e6)
    assert record.strike() == pytest.approx(HAND_PER_SHARE, abs=0.005)
    assert record.strike() == pytest.approx(equity_value_per_share(
        fcf0=900e6, growth=0.03, net_cash=500e6, shares=80e6))
    # and the record says which declarations it divided on
    rendered = record.render()
    assert "money stated in millions, the count in whole" in rendered
    assert "80,000,000" in rendered and "900 DKK millions" in rendered


def test_units_a_LIAB_shaped_file_divides_to_the_SAME_hand_calculation():
    """Money in millions, the count typed IN MILLIONS (77.036 for 77,036
    thousand) -- the shape that only divided right because the two scales
    happened to agree. It must give the same per-share value as the
    PNDORA shape, because it is the same company."""
    liab = _unit_file(count=80.0, money_unit="millions", share_unit="millions")
    pndora = _unit_file(count=80_000_000.0, money_unit="millions",
                        share_unit="whole")
    assert liab.strike() == pytest.approx(HAND_PER_SHARE, abs=0.005)
    assert liab.strike() == pytest.approx(pndora.strike(), rel=1e-12)
    assert liab.band().mid == pytest.approx(pndora.band().mid, rel=1e-12)
    assert liab.legs().shares == pndora.legs().shares == 80e6
    assert "80.000 millions" in liab.render()


@pytest.mark.parametrize("money_unit, share_unit, gap", [
    (None, "whole", "money_unit"),
    ("millions", None, "share_unit"),
    (None, None, "money_unit"),
])
def test_units_an_unstated_unit_is_DATA_MISSING_not_whole(money_unit, share_unit, gap):
    """The old behaviour was to divide anyway. Now the record is INCOMPLETE,
    names the declaration, and refuses to divide."""
    record = _unit_file(count=80_000_000.0, money_unit=money_unit,
                        share_unit=share_unit)
    assert not record.complete
    assert any(gap in g for g in record.missing()), record.missing()
    with pytest.raises(R.RecordError, match="INCOMPLETE"):
        record.strike()
    with pytest.raises(R.RecordError, match="cannot divide"):
        record.legs()
    assert "UNIT NOT STATED" in record.render()


def test_units_survive_the_round_trip_and_a_record_without_them_is_incomplete():
    record = _unit_file(count=80_000_000.0, money_unit="millions",
                        share_unit="whole")
    data = json.loads(json.dumps(record.to_dict()))
    assert data["money_unit"] == "millions" and data["shares"]["unit"] == "whole"
    assert R.replay(data) == pytest.approx(HAND_PER_SHARE, abs=0.005)
    # an OLDER record on disk, written before the schema carried units
    older = {**data, "shares": {k: v for k, v in data["shares"].items() if k != "unit"}}
    older.pop("money_unit")
    assert not R.RunRecord.from_dict(older).complete
    with pytest.raises(R.RecordError, match="INCOMPLETE"):
        R.replay(older)


def test_units_a_word_that_is_not_a_unit_is_refused_in_the_store_and_in_the_record():
    with pytest.raises(M.ManualError, match="money_unit must be one of"):
        _unit_file(count=1.0, money_unit="million", share_unit="whole")
    with pytest.raises(M.ManualError, match="share_unit must be one of"):
        _unit_file(count=1.0, money_unit="millions", share_unit="thousand")
    with pytest.raises(R.RecordError, match="share count unit"):
        R.ShareBasis(count=1.0, basis="x", as_of=date(2026, 6, 30), unit="million")
    record = _unit_file(count=80_000_000.0, money_unit="millions", share_unit="whole")
    with pytest.raises(R.RecordError, match="money unit"):
        R.RunRecord.from_dict({**record.to_dict(), "money_unit": "kilo"})


def test_units_the_shipped_store_files_declare_both_and_the_shipped_records_carry_them():
    """Every store file with figures says what it is stated in, and the two
    Build 2 records replay to their printed values THROUGH the
    declarations, not around them."""
    for ticker, money, shares in (("SAP.DE", "whole", "whole"),
                                  ("LIAB.ST", "millions", "millions"),
                                  ("PNDORA.CO", "millions", "whole"),
                                  ("SYNSAM.ST", "millions", "whole"),
                                  ("DECK", "whole", "whole")):
        parsed = M.load_manual(ticker, directory=M.MANUAL_DIR)
        assert (parsed.money_unit, parsed.share_unit) == (money, shares), ticker
    for ticker, fv in (("SAP.DE", 139.48), ("LIAB.ST", 133.48)):
        raw = json.loads(Path(f"reference/run-records/{ticker}-2026-08-26.json")
                         .read_text(encoding="utf-8"))
        record = R.RunRecord.from_dict(raw)
        assert record.money_unit and record.shares.unit
        assert record.strike() == pytest.approx(fv, abs=0.005)
    # LIAB.ST's count is stated in millions and normalises to whole shares
    liab = R.RunRecord.from_dict(json.loads(
        Path("reference/run-records/LIAB.ST-2026-08-26.json").read_text(encoding="utf-8")))
    assert liab.legs().shares == pytest.approx(77_036_000.0)



# --- E68 (2026-08-29): a record is a statement made under the rules of its date


def test_a_record_struck_before_E68_stays_complete_as_struck_and_says_so():
    """The four records on file were struck before the asset-retirement leg
    existed. They are complete AS STRUCK -- the item is not a gap in a
    declaration that could not have been made -- and their rendering says
    the leg postdates them. The same record re-dated to E68's day is
    incomplete on the item."""
    import json
    from dataclasses import replace
    from datetime import timezone
    from pathlib import Path
    raw = json.loads(Path("reference/run-records/LIAB.ST-2026-08-26.json").read_text())
    record = R.RunRecord.from_dict(raw)
    assert "asset_retirement_obligations" not in record.bridge.items
    assert record.run_ts.date() < R.BRIDGE_ITEMS_SINCE["asset_retirement_obligations"]
    assert record.complete, record.missing()
    assert "before the leg existed (2026-08-29, E68)" in record.render()
    later = replace(record, run_ts=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc))
    assert not later.complete
    assert any("asset_retirement_obligations" in gap for gap in later.missing())


# --- E70 (2026-08-30): the lease declaration, dated like E68's bridge item


def test_E70_a_record_struck_before_the_ruling_is_complete_as_struck_and_says_so():
    import json
    from dataclasses import replace
    from datetime import timezone
    from pathlib import Path
    for name in ("LIAB.ST-2026-08-26", "AUTO.L-2026-08-27", "CTSH-2026-08-28", "AOS-2026-08-30"):
        record = R.RunRecord.from_dict(json.loads(Path(f"reference/run-records/{name}.json").read_text()))
        assert record.lease.in_operating_cash_flow is None
        assert R.struck_before(record.run_ts, R.RECORD_DECLARATIONS_SINCE["lease"]), name
        assert record.complete, (name, record.missing())
        assert "before the declaration existed (E70, 2026-08-30)" in record.render()
        later = replace(record, run_ts=datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc))
        assert any("declaration 3.1, E70" in gap for gap in later.missing())


def test_E70_the_add_back_raises_fcf0_and_is_named_on_the_record():
    from datetime import timezone
    base = R.RunRecord.from_dict(__import__("json").loads(
        __import__("pathlib").Path("reference/run-records/LII-2026-08-30.json").read_text()))
    from dataclasses import replace
    # E81 (2026-08-30 15:00 UTC): a record re-struck after it must declare
    # the prepaid-delivery leg; LII's is a caption zero, declared here.
    base = replace(base, bridge=replace(base.bridge, items={
        **base.bridge.items, "prepaid_delivery_obligations": 0.0}))
    us = replace(base, run_ts=datetime(2026, 8, 31, tzinfo=timezone.utc),
                 lease=R.LeaseTreatment(True, "ASC 842-20-45-5(a)", 90_600_000.0,
                                        "`operating_lease_payments`"))
    assert us.complete, us.missing()
    assert us.fcf0() == pytest.approx(base.fcf0() + 90_600_000.0)
    assert "90,600,000 is ADDED BACK" in us.render()
    ifrs = replace(base, run_ts=datetime(2026, 8, 31, tzinfo=timezone.utc),
                   lease=R.LeaseTreatment(False, "IFRS 16.50(b)"))
    assert ifrs.complete and ifrs.fcf0() == base.fcf0()
    undeclared_yes = replace(us, lease=R.LeaseTreatment(True, "ASC 842", None))
    assert any("operating lease payments to add back" in g for g in undeclared_yes.missing())


def test_E70_a_yes_with_no_payment_is_incomplete_whatever_the_date():
    """Declaring that the flow bore the lease and stating no payment can
    never compute; the date exemption covers NOT RECORDED only."""
    from dataclasses import replace
    from datetime import timezone
    record = deck_record()
    for ts in (datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
               datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)):
        r = replace(record, run_ts=ts, lease=R.LeaseTreatment(True, "ASC 842-20-45-5(a)"))
        assert not r.complete
        assert any("operating lease payments to add back" in g for g in r.missing())
    before = replace(record, run_ts=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
                     lease=R.LeaseTreatment(None, ""))
    assert before.complete


# --- E108's vocabulary: the bridge's names and the store's ----------------
#
# THE DEFECT THESE PIN, so the next reader knows what they are for.
# `RunRecord.sensitivity` is E108's measured limb and `manual.section5_gate`
# is the only consumer of it. The gate refuses on STORE FIELD NAMES and the
# map was keyed on the BRIDGE's reporting labels, so every lookup missed and
# the limb exempted nothing on any name -- silently, because a lookup that
# misses is indistinguishable from an exemption that was not earned. Found
# on MEKKO.HE 2026-09-08.


def test_every_bridge_leg_names_a_real_store_field():
    """BRIDGE_LEG_FIELDS must name fields the schema actually has.

    A typo or a renamed field here brings the silent failure straight back:
    the map would carry a key nothing looks up.
    """
    from vss.manual import FIELDS_BY_NAME
    from vss.runrecord import BRIDGE_ITEMS, BRIDGE_LEG_FIELDS

    for bridge_name, store_fields in BRIDGE_LEG_FIELDS.items():
        assert bridge_name in BRIDGE_ITEMS, bridge_name
        for field_name in store_fields:
            assert field_name in FIELDS_BY_NAME, (bridge_name, field_name)


def test_every_bridge_item_is_mapped_or_deliberately_unmapped():
    """No bridge item may be simply forgotten.

    An item with no entry at all is the failure mode; an item mapped to an
    EMPTY tuple is the deliberate case (E105's minority, which is a flow
    deduction and not a bridge leg) and says so by being present.
    """
    from vss.runrecord import BRIDGE_ITEMS, BRIDGE_LEG_FIELDS

    assert set(BRIDGE_ITEMS) == set(BRIDGE_LEG_FIELDS), (
        set(BRIDGE_ITEMS) ^ set(BRIDGE_LEG_FIELDS))


def test_net_debt_store_legs_name_real_store_fields():
    from vss.manual import FIELDS_BY_NAME
    from vss.runrecord import NET_DEBT_STORE_LEGS

    for field_name in NET_DEBT_STORE_LEGS:
        assert field_name in FIELDS_BY_NAME, field_name


def test_sensitivity_speaks_the_store_s_field_names_not_the_bridge_s():
    """The map the gate looks up must be keyed as the gate refuses.

    `section5_gate` refuses on `figure.name`, which is a STORE field. Before
    2026-09-08 this map carried `leases` and `pensions` and the gate looked
    up `lease_liabilities` and `pension_deficit`, so the intersection was
    empty on every name.
    """
    got = deck_record().sensitivity()
    for field_name in ("lease_liabilities", "pension_deficit",
                       "asset_retirement_obligation",
                       "prepaid_delivery_obligation"):
        assert field_name in got, (field_name, sorted(got))


def test_the_divisor_is_a_leg_and_is_measured_above_the_floor():
    """E108 says perturb EACH leg, and the divisor is one.

    It was absent from `leg_values` until 2026-09-08, so the leg most
    certain to sit above the floor could not be measured at all. A 10%
    perturbation moves `fv_base` by 1/0.9 - 1 = 11.1% on any record, so
    this is a fact about arithmetic rather than about DECK.
    """
    from vss.manual import SENSITIVITY_FLOOR

    got = deck_record().sensitivity()
    assert "diluted_weighted_average_shares" in got
    assert got["diluted_weighted_average_shares"] == pytest.approx(1 / 0.9 - 1,
                                                                   rel=1e-6)
    assert got["diluted_weighted_average_shares"] > SENSITIVITY_FLOOR


def test_a_net_cash_leg_moves_the_value_less_than_a_flow_leg_of_the_same_size():
    """The measurement is real, not a constant handed back.

    A stock leg enters after discounting and a flow leg before it, so equal
    perturbations cannot move `fv_base` equally. If this ever passes with
    the two equal, `sensitivity` has stopped valuing the record.
    """
    got = deck_record().sensitivity()
    assert got["operating_cash_flow"] != got["net_debt"]
    assert got["operating_cash_flow"] > 0


# --- serialisation: EVERY field, not the ones somebody remembered ---------
#
# `to_dict` writes every field of the record; `from_dict` restored twenty of
# twenty-four. `nci_dividends_paid` was one of the four dropped, so from E105
# (2026-09-04) every record written under the ruling replayed as though its
# own JSON did not state the leg -- BOUV.OL, CROX, LOPE, MEKKO.HE and MUSA
# each carried `"nci_dividends_paid": 0.0` on disk and each refused to strike
# from it. Records older than the ruling passed only because
# `struck_before` exempts them, which is why nothing showed for five days.
#
# THE GAP WAS INVISIBLE TO EVERY TEST IN THIS FILE because each of them
# round-trips the fields it is about. The test below round-trips the record
# by ENUMERATING ITS FIELDS, so a field added tomorrow and forgotten in
# `from_dict` fails here rather than in a replay months later.

def _fully_populated_record() -> R.RunRecord:
    """A record with EVERY field set away from its default.

    Not a valuation of anything -- the figures are chosen to be distinct, so
    that a field silently replaced by its default is a visible inequality.
    """
    return R.RunRecord(
        ticker="RT.TEST", currency="EUR",
        run_ts=datetime(2026, 9, 8, 13, 18, 55, tzinfo=ZoneInfo("Europe/Helsinki")),
        basis="annual FY2025",
        shares=R.ShareBasis(
            count=40_571_380.0, basis="ROUND-TRIP FIXTURE",
            as_of=date(2026, 6, 30), point_in_time=40_500_000.0,
            point_in_time_as_of=date(2026, 6, 30), unit="whole",
            divisor_basis="period_end_basic", prior_average=40_000_000.0,
            drift=0.014),
        sbc=R.SbcTreatment(R.SBC_DEDUCTED, 1_100_000.0, "ROUND-TRIP FIXTURE"),
        interest=R.InterestTreatment(True, "p.84", 1_400_000.0, "note"),
        bridge=R.Bridge(net_debt=-6_900_000.0,
                        items={item: 1.0 for item in R.BRIDGE_ITEMS},
                        note="ROUND-TRIP FIXTURE"),
        dates=R.AsOfDates(date(2025, 12, 31), date(2025, 12, 31),
                          date(2026, 6, 30), date(2026, 9, 4)),
        growth=R.Growth(base=0.05, view_file="reference/growth-views/RT.md",
                        view_date=date(2026, 9, 8), bear=0.03, bull=0.07),
        operating_cash_flow=34_500_000.0, capex=-2_600_000.0,
        # `mid_year` is True so that it is not its own default. The
        # fixture is round-tripped and never struck; `strike` refuses a
        # mid-year record by design and that refusal is tested elsewhere.
        conventions=R.Conventions(horizon_years=9, terminal_growth=0.02,
                                  mid_year=True,
                                  first_year_flow="ROUND-TRIP FIXTURE"),
        rate=R.Rate(rate=0.101, core_expected_return=0.08, premium=0.021,
                    band=0.006),
        inputs=(R.Input("operating_cash_flow", 34_500_000.0,
                        "ROUND-TRIP FIXTURE", "hand", "same_page"),),
        tool_commit="0" * 40, notes="ROUND-TRIP FIXTURE", money_unit="whole",
        nci_dividends_paid=-30_000.0,
        undetermined=(R.Undetermined("operating_lease_payments", 250_000.0,
                                     "p.12", R.BOUND_RAISES),),
        fcf_reported=R.Comparator(31_600_000.0, "p.7", True),
        net_debt_reported=R.Comparator(-6_400_000.0, "p.9", True),
        net_income=R.Comparator(24_100_000.0, "p.5", True),
        lease=R.LeaseTreatment(False, "IFRS 16.50(b)", None, "none",
                               rule="E117", lease_cash_deducted=31.5,
                               principal_paid=27.0, interest_paid=4.5,
                               liability_excluded=210.0))


def test_from_dict_reads_back_EVERY_field_to_dict_writes():
    """The round trip, enumerated rather than remembered.

    This is the test that would have caught the `nci_dividends_paid` gap on
    the day E105 was wired. It asks the dataclass what its fields are; it
    does not ask the author of the last commit what they changed.
    """
    from dataclasses import fields as dataclass_fields

    original = _fully_populated_record()
    back = R.RunRecord.from_dict(json.loads(json.dumps(original.to_dict())))

    dropped = [f.name for f in dataclass_fields(R.RunRecord)
               if getattr(back, f.name) != getattr(original, f.name)]
    assert not dropped, (
        f"`from_dict` did not read these back: {', '.join(dropped)}")
    assert back == original


def test_the_round_trip_fixture_leaves_no_field_at_its_default():
    """The fixture polices itself.

    A round-trip test is worthless where the value written and the default
    are the same figure -- the field reads back correctly while being
    dropped. So every field of the record, and of every dataclass nested in
    it, must differ from what it would be if `from_dict` ignored it.
    """
    from dataclasses import MISSING, fields as dataclass_fields, is_dataclass

    def check(obj, path: str) -> list[str]:
        same: list[str] = []
        for f in dataclass_fields(obj):
            value = getattr(obj, f.name)
            if f.default is not MISSING and value == f.default:
                same.append(f"{path}.{f.name}")
            if is_dataclass(value):
                same.extend(check(value, f"{path}.{f.name}"))
            elif isinstance(value, tuple):
                for i, item in enumerate(value):
                    if is_dataclass(item):
                        same.extend(check(item, f"{path}.{f.name}[{i}]"))
        return same

    # `lease.principal_added_back` is None BY THE STANDARD on an IFRS 16.50(b)
    # filer -- there is no principal inside operating cash flow to add back --
    # so it is the one field whose default IS its correct value here.
    assert check(_fully_populated_record(), "record") == [
        "record.lease.principal_added_back"]


def test_every_run_record_on_disk_still_replays():
    """The records this project keeps, replayed from their own JSON.

    THE POINT IS THE SWEEP. A record that cannot be replayed is a fair
    value nobody can check, and E39/E87 null a stored figure for exactly
    that. Two records refuse on their own CONTENT and always have -- they
    are named here so a later reader does not read their absence as this
    test having been narrowed to what passes.
    """
    # Struck INCOMPLETE and kept as history: AOS's E70 restrike states
    # `lease.in_operating_cash_flow` true with no payment to add back and no
    # E106 bound; PNDORA.CO's states no net debt. Neither is a
    # serialisation gap -- the JSON on disk does not carry the figure.
    incomplete_as_struck = {"AOS-2026-08-30-e70.json",
                            "PNDORA.CO-2026-08-30.json"}

    records = sorted(Path("reference/run-records").glob("*.json"))
    assert len(records) > 20, "the run-record directory did not load"

    refused: list[str] = []
    for path in records:
        raw = json.loads(path.read_text(encoding="utf-8"))
        try:
            R.replay(raw)
        except R.RecordError:
            refused.append(path.name)
    assert sorted(refused) == sorted(incomplete_as_struck)
