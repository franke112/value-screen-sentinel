"""Tests for the SCOPE 4 staleness gate and SCOPE 5 verdicts.

Every rule is exercised at its boundary. ``as_of`` is always explicit -- the
rules module must never reach for the clock.
"""

from datetime import date

import pytest

from vss import rules as R

TODAY = date(2026, 8, 20)


def base(**overrides):
    """A healthy, unblocked, fully-populated ticker. Override to break one thing."""
    kwargs = dict(
        ticker="TEST",
        status="WATCH-GATED",
        last_close=100.0,
        last_close_date=TODAY,
        drawdown=0.25,
        fv_base=200.0,      # tier 2 -> mbp 140.00
        tier=2,
        stop_price=80.0,
        catalyst_date=None,
        catalyst_resolved=None,
        catalyst_event=None,
        as_of=TODAY,
    )
    kwargs.update(overrides)
    return kwargs


def codes(verdicts):
    return {v.code for v in verdicts}


# =========================================================================
# MBP is COMPUTED, never manual
# =========================================================================


@pytest.mark.parametrize("tier,expected", [(1, 80.0), (2, 70.0), (3, 60.0)])
def test_compute_mbp_tier_multipliers(tier, expected):
    assert R.compute_mbp(100.0, tier) == pytest.approx(expected)


def test_compute_mbp_rounds_to_2dp():
    assert R.compute_mbp(133.333, 3) == pytest.approx(80.0)
    assert R.compute_mbp(99.99, 1) == pytest.approx(79.99)


def test_compute_mbp_missing_inputs_is_data_missing():
    assert R.compute_mbp(None, 2) is None
    assert R.compute_mbp(100.0, None) is None
    assert R.compute_mbp(None, None) is None


def test_compute_mbp_rejects_unknown_tier():
    assert R.compute_mbp(100.0, 4) is None
    assert R.compute_mbp(100.0, 0) is None


# =========================================================================
# SCOPE 4 -- staleness gate
# =========================================================================


@pytest.mark.parametrize("age", [0, 1, 2, 3])
def test_close_within_3_trading_days_is_not_stale(age):
    """TODAY is Thursday 2026-08-20; three sessions back is Monday the 17th."""
    assert R.stale_close_blocker(date(2026, 8, 20 - age), TODAY) is None


def test_close_exactly_3_trading_days_old_passes_4_blocks():
    assert R.stale_close_blocker(date(2026, 8, 17), TODAY) is None
    # Friday the 14th: Mon, Tue, Wed, Thu -- four sessions.
    blocker = R.stale_close_blocker(date(2026, 8, 14), TODAY)
    assert blocker is not None and blocker.code == R.STALE_DATA
    assert "4 trading days" in blocker.reason


# --- C3: the gate counts SESSIONS, so a holiday is not a stale feed -------


@pytest.mark.parametrize("holiday, last_close, as_of, sessions", [
    # The Tuesday after US Memorial Day (2026-05-25). Friday's close is
    # 4 CALENDAR days old and was blocked; it is 2 sessions old.
    ("US Memorial Day", date(2026, 5, 22), date(2026, 5, 26), 2),
    # The Tuesday after Easter 2026 (Good Friday 04-03, Easter Monday
    # 04-06). Thursday's close was 5 calendar days old; 3 sessions.
    ("Easter Monday", date(2026, 4, 2), date(2026, 4, 7), 3),
    # The Monday after Midsommar (Midsummer Eve Friday 2026-06-19,
    # Stockholm shut). Thursday's close was 4 calendar days old; 2 sessions.
    ("Midsommar", date(2026, 6, 18), date(2026, 6, 22), 2),
])
def test_the_first_trading_day_after_a_holiday_is_not_stale(
        holiday, last_close, as_of, sessions):
    """REVIEW-4 report A 4.2: all three blocked every held name under the
    calendar-day rule -- no stop check, no verdict, on exactly the day the
    stop check matters most."""
    assert (as_of - last_close).days > R.MAX_CLOSE_AGE_TRADING_DAYS, holiday
    assert R.trading_days_between(last_close, as_of) == sessions
    assert R.stale_close_blocker(last_close, as_of) is None, holiday


def test_naming_the_exchange_holiday_tightens_the_count_further():
    """The caller may supply the closed days. Since 2026-08-26 the screener
    does (vss/calendars.py, tests/test_calendars.py); `vss run` still does
    not, because a watchlist entry names no market."""
    shut = {date(2026, 4, 3), date(2026, 4, 6)}
    assert R.trading_days_between(date(2026, 4, 2), date(2026, 4, 7)) == 3
    assert R.trading_days_between(date(2026, 4, 2), date(2026, 4, 7),
                                  holidays=shut) == 1


def test_a_feed_that_stopped_a_week_ago_still_blocks():
    """The gate did not become permissive: five sessions is five sessions."""
    blocker = R.stale_close_blocker(date(2026, 8, 13), TODAY)
    assert blocker is not None and blocker.code == R.STALE_DATA
    assert "5 trading days" in blocker.reason


def test_a_weekend_run_counts_no_sessions_after_fridays_close():
    assert R.trading_days_between(date(2026, 8, 21), date(2026, 8, 23)) == 0
    assert R.trading_days_between(date(2026, 8, 20), date(2026, 8, 20)) == 0


def test_missing_close_date_is_blocked():
    assert R.stale_close_blocker(None, TODAY).code == R.STALE_DATA


def test_stale_data_blocks_and_emits_no_verdict():
    a = R.assess(**base(last_close_date=date(2026, 8, 1)))
    assert a.blocked
    assert a.verdicts == ()
    assert R.STALE_DATA in {b.code for b in a.blockers}


# --- catalyst gate --------------------------------------------------------


def test_past_catalyst_without_resolution_blocks():
    b = R.catalyst_blocker(date(2026, 8, 1), None, TODAY)
    assert b is not None and b.code == R.CATALYST_UNRESOLVED
    assert "catalyst_resolved is not set" in b.reason


def test_past_catalyst_with_resolution_does_not_block():
    assert R.catalyst_blocker(date(2026, 8, 1), date(2026, 8, 5), TODAY) is None


def test_resolution_on_the_catalyst_date_itself_is_valid():
    assert R.catalyst_blocker(date(2026, 8, 1), date(2026, 8, 1), TODAY) is None


def test_gate_never_reads_notes():
    """Prose can no longer satisfy the gate -- only the structured date can.

    The old mechanism matched any line beginning "outcome:", so text
    saying the outcome was NOT ingested still unblocked the ticker. The
    exact placeholder below used to pass; it must now be irrelevant.
    """
    import ast
    import inspect

    # The prose matcher is gone entirely.
    assert not hasattr(R, "has_outcome_line")

    # The gate body references no parameter named "notes".
    tree = ast.parse(inspect.getsource(R.catalyst_blocker))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    args = {a.arg for a in tree.body[0].args.args}
    assert "notes" not in names | args

    # A passed catalyst blocks regardless of what any prose says.
    a = R.assess(**base(catalyst_date=date(2026, 7, 29)))
    assert R.CATALYST_UNRESOLVED in {b.code for b in a.blockers}
    assert a.verdicts == ()


def test_resolution_unblocks_where_prose_no_longer_can():
    a = R.assess(**base(catalyst_date=date(2026, 7, 29), catalyst_resolved=date(2026, 8, 3)))
    assert R.CATALYST_UNRESOLVED not in {b.code for b in a.blockers}


def test_future_catalyst_does_not_block():
    assert R.catalyst_blocker(date(2026, 12, 1), None, TODAY) is None


def test_absent_catalyst_date_never_blocks():
    assert R.catalyst_blocker(None, None, TODAY) is None
    assert R.assess(**base(catalyst_date=None)).blocked is False


def test_unresolved_catalyst_blocks_and_emits_no_verdict():
    a = R.assess(**base(catalyst_date=date(2026, 7, 1), catalyst_event="Q2", last_close=1.0))
    assert a.blocked and a.verdicts == ()


# --- missing stop is a blocker, per the framework -------------------------


def test_missing_stop_blocks_held_only():
    b = R.missing_stop_blocker("HELD", None)
    assert b is not None and b.code == R.NO_STOP
    assert "no stop defined" in b.reason


@pytest.mark.parametrize("status", ["WATCH-GATED", "PIPELINE"])
def test_missing_stop_does_not_block_unheld(status):
    """No position, nothing to exit -- a missing stop is not an emergency."""
    assert R.missing_stop_blocker(status, None) is None


def test_stop_present_never_blocks():
    assert R.missing_stop_blocker("HELD", 80.0) is None
    assert R.missing_stop_blocker("WATCH-GATED", 80.0) is None


def test_held_without_stop_produces_blocker_not_action():
    a = R.assess(**base(status="HELD", stop_price=None, last_close=1.0))
    assert a.blocked
    assert a.actionable is False
    assert a.verdicts == ()
    assert R.NO_STOP in {b.code for b in a.blockers}


@pytest.mark.parametrize("status", ["WATCH-GATED", "PIPELINE"])
def test_unheld_without_stop_is_flagged_not_blocked(status):
    """WATCH-GATED/PIPELINE keep their normal MBP verdicts, plus the flag."""
    a = R.assess(**base(status=status, stop_price=None, last_close=100.0, drawdown=0.25))
    assert not a.blocked
    assert R.NO_STOP_PRE_ENTRY in codes(a.verdicts)
    assert R.AT_BELOW_MBP in codes(a.verdicts)   # mbp is 140.0, close is 100.0
    assert a.actionable is True


def test_pre_entry_flag_wording_marks_it_as_a_prerequisite():
    v = R.pre_entry_stop_flag("WATCH-GATED", None)
    assert v is not None and v.label == "NO STOP DEFINED"
    assert "required before entry" in v.detail


def test_pre_entry_flag_absent_when_stop_is_set():
    assert R.pre_entry_stop_flag("WATCH-GATED", 80.0) is None


def test_pre_entry_flag_never_applies_to_held():
    """HELD without a stop is blocked, so it must not also be flagged."""
    assert R.pre_entry_stop_flag("HELD", None) is None


def test_unheld_missing_stop_reports_the_flag_not_data_missing():
    """One statement about the missing stop, not two."""
    a = R.assess(**base(status="WATCH-GATED", stop_price=None, last_close=100.0, drawdown=0.25))
    stop_related = [
        v for v in a.verdicts if "stop" in f"{v.label} {v.detail}".lower()
    ]
    assert len(stop_related) == 1
    assert stop_related[0].code == R.NO_STOP_PRE_ENTRY


def test_unheld_without_stop_still_gets_dislocation_verdict():
    a = R.assess(**base(status="WATCH-GATED", stop_price=None, last_close=100.0, drawdown=0.90))
    assert R.OUTSIDE_BAND in codes(a.verdicts)


def test_no_data_blocks():
    a = R.assess(**base(last_close=None, last_close_date=None, fetch_error="boom"))
    assert a.blocked and a.verdicts == ()
    assert R.NO_DATA in {b.code for b in a.blockers}


def test_multiple_blockers_are_all_reported():
    a = R.assess(
        **base(
            status="HELD",
            last_close_date=date(2026, 1, 1),
            catalyst_date=date(2026, 2, 1),
            stop_price=None,
        )
    )
    assert {b.code for b in a.blockers} == {R.STALE_DATA, R.CATALYST_UNRESOLVED, R.NO_STOP}
    assert a.verdicts == ()


# =========================================================================
# SCOPE 5 -- verdicts
# =========================================================================

# --- STOP BREACHED --------------------------------------------------------


def test_stop_breached_exactly_at_stop():
    v = R.stop_verdict("HELD", 80.0, 80.0)
    assert v is not None and v.code == R.STOP_BREACHED


def test_stop_breached_below_stop():
    assert R.stop_verdict("HELD", 79.99, 80.0).code == R.STOP_BREACHED


def test_no_stop_breach_just_above_stop():
    assert R.stop_verdict("HELD", 80.01, 80.0) is None


def test_stop_breach_only_applies_to_held():
    assert R.stop_verdict("WATCH-GATED", 50.0, 80.0) is None
    assert R.stop_verdict("PIPELINE", 50.0, 80.0) is None


def test_stop_check_without_stop_price_is_data_missing():
    v = R.stop_verdict("HELD", 50.0, None)
    assert v is not None and v.code == R.DATA_MISSING


# --- MBP ------------------------------------------------------------------


def test_at_below_mbp_exactly_at_mbp():
    v = R.mbp_verdict(140.0, 140.0)
    assert v is not None and v.code == R.AT_BELOW_MBP


def test_at_below_mbp_under_mbp():
    assert R.mbp_verdict(139.99, 140.0).code == R.AT_BELOW_MBP


def test_approaching_mbp_just_above_mbp():
    assert R.mbp_verdict(140.01, 140.0).code == R.APPROACHING_MBP


def test_approaching_mbp_exactly_at_5_percent_boundary():
    assert R.mbp_verdict(147.0, 140.0).code == R.APPROACHING_MBP


def test_no_mbp_verdict_above_5_percent_boundary():
    assert R.mbp_verdict(147.01, 140.0) is None


def test_at_and_approaching_are_mutually_exclusive():
    """Exactly at MBP is AT/BELOW only -- never both labels at once."""
    verdicts = R.collect_verdicts(
        status="WATCH-GATED", last_close=140.0, drawdown=0.25, mbp=140.0, stop_price=80.0
    )
    assert codes(verdicts) == {R.AT_BELOW_MBP}


def test_mbp_check_without_fv_base_is_data_missing():
    v = R.mbp_verdict(100.0, None)
    assert v is not None and v.code == R.DATA_MISSING
    assert "fv_base" in v.detail


# --- dislocation band -----------------------------------------------------


def test_drawdown_exactly_15_percent_is_inside_band():
    assert R.dislocation_verdict(0.15) is None


def test_drawdown_exactly_50_percent_is_inside_band():
    assert R.dislocation_verdict(0.50) is None


def test_drawdown_below_band_is_outside():
    v = R.dislocation_verdict(0.1499)
    assert v is not None and v.code == R.OUTSIDE_BAND


def test_drawdown_above_band_is_outside():
    v = R.dislocation_verdict(0.5001)
    assert v is not None and v.code == R.OUTSIDE_BAND


def test_drawdown_mid_band_is_inside():
    assert R.dislocation_verdict(0.30) is None


def test_missing_drawdown_is_data_missing():
    assert R.dislocation_verdict(None).code == R.DATA_MISSING


# --- collection semantics -------------------------------------------------


def test_no_action_when_nothing_fires():
    verdicts = R.collect_verdicts(
        status="WATCH-GATED", last_close=200.0, drawdown=0.25, mbp=140.0, stop_price=80.0
    )
    assert codes(verdicts) == {R.NO_ACTION}


def test_verdicts_are_collected_not_first_match_wins():
    """A HELD name under stop, under MBP and outside the band reports all three."""
    verdicts = R.collect_verdicts(
        status="HELD", last_close=70.0, drawdown=0.60, mbp=140.0, stop_price=80.0
    )
    assert codes(verdicts) == {R.STOP_BREACHED, R.AT_BELOW_MBP, R.OUTSIDE_BAND}


def test_stop_breach_is_never_masked_by_the_mbp_rule():
    a = R.assess(**base(status="HELD", last_close=70.0, drawdown=0.25))
    assert R.STOP_BREACHED in codes(a.verdicts)
    assert R.AT_BELOW_MBP in codes(a.verdicts)


# --- missing manual fields never silently skip a check --------------------


def test_missing_fv_base_does_not_suppress_the_stop_check():
    a = R.assess(**base(status="HELD", fv_base=None, last_close=70.0, drawdown=0.25))
    assert R.STOP_BREACHED in codes(a.verdicts)
    assert R.DATA_MISSING in codes(a.verdicts)
    assert a.mbp is None


def test_missing_tier_does_not_suppress_the_stop_check():
    a = R.assess(**base(status="HELD", tier=None, last_close=70.0, drawdown=0.25))
    assert R.STOP_BREACHED in codes(a.verdicts)
    assert R.DATA_MISSING in codes(a.verdicts)


def test_missing_fv_base_still_evaluates_the_dislocation_band():
    a = R.assess(**base(fv_base=None, drawdown=0.90))
    assert R.OUTSIDE_BAND in codes(a.verdicts)
    assert R.DATA_MISSING in codes(a.verdicts)


def test_data_missing_makes_a_ticker_actionable_never_silent():
    a = R.assess(**base(fv_base=None, drawdown=0.25, last_close=200.0))
    assert codes(a.verdicts) == {R.DATA_MISSING}
    assert a.actionable is True


def test_data_missing_is_never_treated_as_a_pass_or_a_fail():
    """An absent fv_base must not resolve to AT/BELOW MBP or to NO ACTION."""
    a = R.assess(**base(fv_base=None, tier=None, drawdown=0.25, last_close=1.0))
    assert R.AT_BELOW_MBP not in codes(a.verdicts)
    assert R.NO_ACTION not in codes(a.verdicts)


# --- assess() composition -------------------------------------------------


def test_healthy_ticker_is_no_action():
    a = R.assess(**base(last_close=200.0, drawdown=0.25))
    assert not a.blocked
    assert codes(a.verdicts) == {R.NO_ACTION}
    assert a.actionable is False


def test_assess_computes_mbp_from_fv_base_and_tier():
    assert R.assess(**base()).mbp == pytest.approx(150.0)   # E90: 200 x 0.75


def test_blocked_ticker_never_receives_a_verdict_even_when_rules_would_fire():
    """Stale + at MBP + stop breached: the blocker wins, verdicts stay empty."""
    a = R.assess(
        **base(
            status="HELD",
            last_close=10.0,
            last_close_date=date(2026, 1, 1),
            drawdown=0.99,
        )
    )
    assert a.blocked
    assert a.verdicts == ()
    assert a.actionable is False


def test_rules_module_is_pure_no_io_imports():
    """rules.py may only import stdlib value types -- no pandas, yaml, os or net."""
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(R))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= {"__future__", "dataclasses", "datetime", "typing"}


def test_rules_module_never_reads_the_clock():
    """as_of is always a parameter -- no now()/today() call anywhere in rules.py."""
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(R))
    clock_calls = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"now", "today", "utcnow", "time"}
    ]
    assert clock_calls == []


def test_no_data_does_not_also_report_a_redundant_stale_blocker():
    """With no series at all, 'no data' is the reason -- not 'no close date'."""
    a = R.assess(**base(last_close=None, last_close_date=None, fetch_error="boom"))
    assert {b.code for b in a.blockers} == {R.NO_DATA}


def test_no_data_still_reports_other_independent_blockers():
    a = R.assess(
        **base(
            status="HELD",
            last_close=None,
            last_close_date=None,
            fetch_error="boom",
            stop_price=None,
            catalyst_date=date(2026, 1, 1),
        )
    )
    assert {b.code for b in a.blockers} == {R.NO_DATA, R.NO_STOP, R.CATALYST_UNRESOLVED}


# --- DROPPED: a record, not a stage --------------------------------------
#
# A rejected name is kept so it is not screened again from scratch and so
# the reason survives. It is neither a position nor a candidate, so the
# checks that serve those two answer questions nobody is asking.


def test_dropped_is_a_valid_status():
    assert "DROPPED" in R.VALID_STATUSES


def test_a_dropped_name_collects_one_verdict_and_no_checks():
    verdicts = R.collect_verdicts(status="DROPPED", last_close=41.06, drawdown=0.492,
                                  mbp=None, stop_price=None)
    assert [v.code for v in verdicts] == [R.DROPPED]
    assert "kept as a record" in verdicts[0].detail


def test_a_dropped_name_is_not_told_it_needs_a_stop_before_entry():
    """There is no entry. The flag would be advice about a decision made."""
    verdicts = R.collect_verdicts(status="DROPPED", last_close=41.06, drawdown=0.492,
                                  mbp=None, stop_price=None)
    assert not any(v.code == R.NO_STOP_PRE_ENTRY for v in verdicts)
    assert not any(v.code == R.DATA_MISSING for v in verdicts)


def test_the_same_name_as_a_candidate_still_gets_both_flags():
    """The suppression is the status's doing, not a change to the checks."""
    verdicts = R.collect_verdicts(status="WATCH-GATED", last_close=41.06, drawdown=0.492,
                                  mbp=None, stop_price=None)
    codes = [v.code for v in verdicts]
    assert R.NO_STOP_PRE_ENTRY in codes and R.DATA_MISSING in codes


def test_a_dropped_name_stays_out_of_the_actions_table():
    assessment = R.TickerAssessment(
        ticker="NKE",
        verdicts=R.collect_verdicts(status="DROPPED", last_close=41.06,
                                    drawdown=0.492, mbp=None, stop_price=None))
    assert assessment.actionable is False
    assert assessment.blocked is False


def test_a_dropped_name_is_still_blocked_by_stale_data():
    """The record is kept honest about its own freshness."""
    from datetime import date
    blocker = R.stale_close_blocker(date(2026, 8, 1), date(2026, 8, 21))
    assert blocker is not None


def test_a_dropped_name_has_no_position_to_exit():
    assert R.missing_stop_blocker("DROPPED", None) is None
    assert R.stop_verdict("DROPPED", 41.06, 50.0) is None


# --- in_dislocation_band: the predicate behind the verdict -----------------


def test_in_dislocation_band_is_true_inside():
    assert R.in_dislocation_band(0.223) is True
    assert R.in_dislocation_band(0.30) is True


def test_in_dislocation_band_bounds_are_inclusive():
    assert R.in_dislocation_band(R.DISLOCATION_MIN) is True
    assert R.in_dislocation_band(R.DISLOCATION_MAX) is True


def test_in_dislocation_band_is_false_outside():
    assert R.in_dislocation_band(0.112) is False
    assert R.in_dislocation_band(0.51) is False
    assert R.in_dislocation_band(0.0) is False
    assert R.in_dislocation_band(-0.05) is False


def test_in_dislocation_band_returns_none_for_data_missing():
    """Not False. An untested name has not failed the gate."""
    assert R.in_dislocation_band(None) is None


def test_the_verdict_and_the_predicate_cannot_disagree():
    values = [None, -0.10, 0.0, 0.1499, 0.15, 0.2, 0.50, 0.5001, 0.9]
    for drawdown in values:
        inside = R.in_dislocation_band(drawdown)
        verdict = R.dislocation_verdict(drawdown)
        if inside is None:
            assert verdict is not None and verdict.code == R.DATA_MISSING
        elif inside:
            assert verdict is None
        else:
            assert verdict is not None and verdict.code == R.OUTSIDE_BAND


# --- E27: the split changed the vocabulary, not the entry arithmetic ------


@pytest.mark.parametrize("status", ["WATCH-PRICED", "WATCH-GATED"])
def test_e27_both_waiting_statuses_behave_as_the_old_watch_did(status):
    """FRAMEWORK-EDITS E27 split WATCH by WHY a name waits, not by what
    the entry checks do to it.

    Neither half is a position, so neither is blocked for a missing stop
    and both carry the pre-entry flag instead. The difference between them
    is what may WAKE the name -- a price for the priced half, an
    information event for the gated half -- and that is a decision the
    owner makes, not a verdict this module issues. If a future rule ever
    does treat them differently, it should fail here first.
    """
    assert R.missing_stop_blocker(status, None) is None
    assert R.missing_stop_blocker(status, 80.0) is None
    assert R.stop_verdict(status, 50.0, 80.0) is None

    flag = R.pre_entry_stop_flag(status, None)
    assert flag is not None and flag.code == R.NO_STOP_PRE_ENTRY
    assert R.pre_entry_stop_flag(status, 80.0) is None


def test_e27_the_two_waiting_statuses_collect_identical_verdicts():
    """Same inputs, same verdicts -- the split is not a behaviour change."""
    kwargs = dict(last_close=140.0, drawdown=0.25, mbp=140.0, stop_price=80.0)
    priced = R.collect_verdicts(status="WATCH-PRICED", **kwargs)
    gated = R.collect_verdicts(status="WATCH-GATED", **kwargs)
    assert [v.code for v in priced] == [v.code for v in gated]



# --- E32: the superseded MBP definition, marked wherever it is named -------


def test_e32_mbp_verdicts_carry_the_mark_when_superseded():
    """Both sentences that NAME the number say it is superseded, and the
    mark is APPENDED -- the old text is still there and still true."""
    at = R.mbp_verdict(140.0, 140.0, superseded=True)
    approaching = R.mbp_verdict(145.0, 140.0, superseded=True)
    assert at.code == R.AT_BELOW_MBP and approaching.code == R.APPROACHING_MBP
    for v in (at, approaching):
        assert R.MBP_SUPERSEDED_MARK in v.detail
    assert "close 140.00 <= mbp 140.00" in at.detail
    assert "close 145.00 within 5% of mbp 140.00" in approaching.detail


def test_e32_an_e28_struck_mbp_is_not_marked():
    v = R.mbp_verdict(140.0, 140.0, superseded=False)
    assert R.MBP_SUPERSEDED_MARK not in v.detail


def test_e90_assess_is_base_times_cushion_and_unmarked():
    """E90 (2026-08-30): the MBP is the BASE-case value x the cushion
    (tier 2: 0.75), record-backed by construction (the runner passes
    fv_base only off a replaying record), so it carries no mark. The E28
    marked fallback is retired with E28's arithmetic; E32's mark remains
    on the stored-basis table rows it always marked."""
    a = R.assess(
        ticker="AAA", status="HELD", last_close=140.0,
        last_close_date=date(2026, 8, 24), drawdown=0.25,
        fv_base=200.0, tier=2, stop_price=80.0,
        catalyst_date=None, catalyst_resolved=None, catalyst_event=None,
        as_of=date(2026, 8, 24),
    )
    assert a.mbp == 150.0 and a.mbp_superseded is False
    detail = [v.detail for v in a.verdicts if v.code == R.AT_BELOW_MBP][0]
    assert R.MBP_SUPERSEDED_MARK not in detail


def test_e90_the_bear_value_no_longer_sets_the_figure():
    """E90 (2026-08-30, superseding E28's wiring of 2026-08-26): the MBP
    is base x cushion whether or not a bear value is supplied -- the bear
    value stays on the row as information, and the figure is unmarked."""
    common = dict(
        ticker="AAA", status="HELD", last_close=140.0,
        last_close_date=date(2026, 8, 24), drawdown=0.25,
        fv_base=200.0, tier=2, stop_price=80.0,
        catalyst_date=None, catalyst_resolved=None, catalyst_event=None,
        as_of=date(2026, 8, 24),
    )
    without = R.assess(**common)
    assert without.mbp == 150.0 and without.mbp_superseded is False
    with_bear = R.assess(**common, bear_value=150.0)
    assert with_bear.mbp == 150.0 and with_bear.mbp_superseded is False   # 200 x 0.75; the 150 bear is ignored
    assert not any(R.MBP_SUPERSEDED_MARK in v.detail for v in with_bear.verdicts)
    # no tier is no MBP at all -- and no mark
    none = R.assess(**{**common, "tier": None}, bear_value=150.0)
    assert none.mbp is None and none.mbp_superseded is False


def test_e90_compute_mbp_e90_is_the_unrounded_base_times_the_cushion():
    assert R.compute_mbp_e90(139.48, 1) == 118.56       # SAP.DE's shape
    assert R.compute_mbp_e90(133.48, 2) == 100.11       # LIAB.ST's
    assert R.compute_mbp_e90(None, 1) is None
    assert R.compute_mbp_e90(139.48, None) is None
    assert R.compute_mbp_e90(139.48, 4) is None


def test_e28_compute_mbp_e28_is_the_unrounded_bear_times_the_cushion():
    assert R.compute_mbp_e28(120.2678, 1) == 96.21      # SAP.DE's shape: not 96.22
    assert R.compute_mbp_e28(107.2312, 2) == 75.06      # LIAB.ST's
    assert R.compute_mbp_e28(None, 1) is None
    assert R.compute_mbp_e28(120.27, None) is None
    assert R.compute_mbp_e28(120.27, 4) is None


def test_e32_no_mbp_is_not_superseded_it_is_absent():
    """DATA MISSING is its own state and must not gain a mark: there is no
    number to be superseded."""
    a = R.assess(
        ticker="AAA", status="HELD", last_close=140.0,
        last_close_date=date(2026, 8, 24), drawdown=0.25,
        fv_base=None, tier=None, stop_price=80.0,
        catalyst_date=None, catalyst_resolved=None, catalyst_event=None,
        as_of=date(2026, 8, 24),
    )
    assert a.mbp is None and a.mbp_superseded is False
    detail = [v.detail for v in a.verdicts if v.code == R.DATA_MISSING][0]
    assert R.MBP_SUPERSEDED_MARK not in detail


# --- E39: a nulled fair value leaves the stop working ---------------------


def test_a_nulled_fair_value_produces_no_mbp_and_leaves_the_stop_alive():
    """E39, as arithmetic. `fv_base` and `tier` go to null; `stop_price`
    does not, because a stop is a statement about how much the owner will
    lose and not about what the company is worth. The one thing that must
    not happen while a fair value is being re-struck is that the position
    goes unwatched.
    """
    assert R.compute_mbp(None, None) is None
    assert R.compute_mbp(None, 1) is None
    assert R.compute_mbp(185.0, None) is None
    # and the stop is untouched by any of it
    assert R.stop_verdict("HELD", 100.0, 112.0).code == R.STOP_BREACHED
    assert R.stop_verdict("HELD", 126.30, 112.0) is None


def test_a_held_name_with_no_fair_value_is_DATA_MISSING_not_a_verdict():
    """It must not read as HOLD and it must not read as TRIM. Section 6.4
    compared a price with `fv_base`; LIAB.ST's 102.66 sat 19% BELOW the
    close and read as a name to trim, off a calculation that charged its
    interest twice."""
    a = R.assess(**base(fv_base=None, tier=None, last_close=126.30,
                        stop_price=112.0))
    assert not a.blocked
    assert [v.code for v in a.verdicts] == [R.DATA_MISSING]


# --- K4: a series that cannot be measured never prints STOP BREACHED ------

PHANTOM = ("2026-08-20 closed -50% (100 -> 50) on 1.0x the median volume; a "
           "repricing of that size trades, so the high on the far side of it "
           "is not comparable with today's close")


def test_a_flagged_series_makes_the_stop_check_DATA_MISSING_never_a_breach():
    """Build 2 item 0. Both held names carry live stops; a feed quoting two
    scales must print DATA MISSING for the stop check, not a breach."""
    v = R.stop_verdict("HELD", 50.0, 80.0, series_finding=PHANTOM)
    assert v is not None and v.code == R.DATA_MISSING
    assert "K4" in v.detail and "50%" in v.detail
    # the same close with NO finding is a breach -- the finding is the gate
    assert R.stop_verdict("HELD", 50.0, 80.0).code == R.STOP_BREACHED


def test_a_flagged_series_withholds_the_mbp_and_dislocation_checks_too():
    assert R.mbp_verdict(50.0, 140.0, series_finding=PHANTOM).code == R.DATA_MISSING
    assert R.dislocation_verdict(0.52, series_finding=PHANTOM).code == R.DATA_MISSING
    # a missing stop_price still says so first: the finding does not hide it
    assert "stop_price not set" in R.stop_verdict("HELD", 50.0, None, PHANTOM).detail


def test_assess_carries_the_finding_and_strikes_no_breach_on_it():
    a = R.assess(
        ticker="X", status="HELD", last_close=50.0,
        last_close_date=date(2026, 8, 20), drawdown=0.52,
        fv_base=200.0, tier=2, stop_price=80.0,
        catalyst_date=None, catalyst_resolved=None, catalyst_event=None,
        as_of=date(2026, 8, 20), series_finding=PHANTOM,
    )
    codes = [v.code for v in a.verdicts]
    assert R.STOP_BREACHED not in codes and R.AT_BELOW_MBP not in codes
    assert codes == [R.DATA_MISSING] * 3
    assert not a.blocked            # K4 is not a blocker: the row still prints


# --- E12: Gate 1 is frozen at entry for a PIPELINE name (build item 5) ------


def test_a_pipeline_name_with_a_frozen_reading_is_not_re_read():
    """PNDORA.CO, E11's own case: written at 15.64% against the 2025-08-22
    peak, reading 13.0% two days later once the peak aged out. Under E12
    the band verdict is struck on the frozen 15.64% and the name stays."""
    a = R.assess(**base(status="PIPELINE", stop_price=None, drawdown=0.130,
                        dd_at_entry=0.1564, peak_date=date(2025, 8, 22)))
    assert R.OUTSIDE_BAND not in codes(a.verdicts)


def test_without_the_frozen_pair_a_pipeline_name_reads_todays_level():
    a = R.assess(**base(status="PIPELINE", stop_price=None, drawdown=0.130))
    assert R.OUTSIDE_BAND in codes(a.verdicts)


def test_a_frozen_reading_outside_the_band_says_it_is_frozen():
    a = R.assess(**base(status="PIPELINE", stop_price=None, drawdown=0.25,
                        dd_at_entry=0.60, peak_date=date(2025, 8, 22)))
    (band,) = [v for v in a.verdicts if v.code == R.OUTSIDE_BAND]
    assert "60.0%" in band.detail
    assert "FROZEN AT ENTRY per E12" in band.detail
    assert "2025-08-22" in band.detail and "today's reading 25.0%" in band.detail


def test_only_a_pipeline_name_freezes_gate_1():
    """A holding reads today's level (B1); a WATCH name has E27's rule."""
    for status in ("HELD", "WATCH-GATED", "WATCH-PRICED"):
        a = R.assess(**base(status=status, drawdown=0.130,
                            dd_at_entry=0.1564, peak_date=date(2025, 8, 22)))
        assert R.OUTSIDE_BAND in codes(a.verdicts), status
    assert R.frozen_gate_1("PIPELINE", 0.2, date(2026, 1, 1))
    assert not R.frozen_gate_1("PIPELINE", 0.2, None)
    assert not R.frozen_gate_1("HELD", 0.2, date(2026, 1, 1))


def test_a_series_finding_does_not_reach_a_frozen_reading():
    """The frozen figure is a stored number, not a measurement across
    today's series, so K4's DATA MISSING does not replace it."""
    a = R.assess(**base(status="PIPELINE", stop_price=None, drawdown=0.130,
                        dd_at_entry=0.1564, peak_date=date(2025, 8, 22),
                        series_finding="scale switch on 2026-07-20"))
    band = [v for v in a.verdicts if "dislocation" in v.detail.lower()]
    assert band == []
    assert R.OUTSIDE_BAND not in codes(a.verdicts)
