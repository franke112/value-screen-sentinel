"""FRAMEWORK 4.2 hard kills, each at its boundary.

Every rule is exercised exactly at its threshold and one step either
side, because a hard kill that fires one quarter late or one basis point
early is worse than no hard kill at all.
"""

from datetime import date, timedelta

import pytest

from vss import rules as R

AS_OF = date(2026, 8, 20)
PERIODS = [f"20{y}-Q{q}" for y in (24, 25, 26) for q in (1, 2, 3, 4)]


def quarters(n=8, **series):
    """n quarters oldest-first; each kwarg is a per-quarter list or scalar."""
    out = []
    for i in range(n):
        kw = {"basis": "reported", "accounting": "gaap"}
        for key, val in series.items():
            kw[key] = val[i] if isinstance(val, (list, tuple)) else val
        out.append(R.Quarter(period=PERIODS[i], **kw))
    return out


# =========================== 4.2.1 revenue (YoY) ==========================


def test_revenue_exactly_two_consecutive_yoy_declines_trips():
    qs = quarters(8, revenue_yoy=[0.05] * 6 + [-0.001, -0.001])
    assert R.revenue_decline_kill(qs).state == R.TRIP


def test_revenue_one_decline_does_not_trip():
    qs = quarters(8, revenue_yoy=[0.05] * 7 + [-0.02])
    assert R.revenue_decline_kill(qs).state == R.NO_TRIP


def test_revenue_exactly_flat_is_not_a_decline():
    """0.0% is flat, not declining. Strictly less than zero is required."""
    qs = quarters(8, revenue_yoy=[0.05] * 6 + [0.0, 0.0])
    assert R.revenue_decline_kill(qs).state == R.NO_TRIP


def test_revenue_decline_broken_by_a_positive_quarter():
    qs = quarters(8, revenue_yoy=[-0.05] * 6 + [0.01, -0.05])
    assert R.revenue_decline_kill(qs).state == R.NO_TRIP


def test_revenue_missing_yoy_cannot_evaluate():
    qs = quarters(8, revenue_yoy=[0.05] * 7 + [None])
    r = R.revenue_decline_kill(qs)
    assert r.state == R.CANNOT_EVALUATE and "revenue_yoy" in r.detail


def test_revenue_basis_mismatch_refuses_the_comparison():
    """Constant-currency against reported is neither; refuse it."""
    qs = quarters(8, revenue_yoy=-0.03)
    qs[-1] = R.Quarter(period=qs[-1].period, revenue_yoy=-0.03,
                       basis="constant_currency", accounting="gaap")
    r = R.revenue_decline_kill(qs)
    assert r.state == R.CANNOT_EVALUATE and "BASIS MISMATCH" in r.detail


def test_gaap_vs_non_gaap_is_also_a_basis_mismatch():
    qs = quarters(8, revenue_yoy=-0.03)
    qs[-1] = R.Quarter(period=qs[-1].period, revenue_yoy=-0.03,
                       basis="reported", accounting="non_gaap")
    assert R.revenue_decline_kill(qs).state == R.CANNOT_EVALUATE


def test_revenue_insufficient_history():
    assert R.revenue_decline_kill(quarters(1)).state == R.CANNOT_EVALUATE


# ===================== 4.3 soft flag: sequential run ======================


def test_exactly_three_sequential_declines_raises_the_soft_flag():
    qs = quarters(8, revenue=[100, 100, 100, 100, 100, 99, 98, 97])
    r = R.sequential_decline_soft_flag(qs)
    assert r.state == R.TRIP
    assert "SOFT FLAG" in r.detail and "not a 4.2 hard kill" in r.detail


def test_two_sequential_declines_does_not_raise_it():
    qs = quarters(8, revenue=[100, 100, 100, 100, 100, 100, 99, 98])
    assert R.sequential_decline_soft_flag(qs).state == R.NO_TRIP


def test_soft_flag_is_never_reported_as_a_hard_kill():
    """It must be distinguishable from 4.2 by rule id."""
    assert R.sequential_decline_soft_flag(quarters(8, revenue=100)).rule == "4.3.soft"
    for r in R.evaluate_hard_kills(quarters(8), None, AS_OF):
        assert r.rule.startswith("4.2.") or r.rule == "4.3.soft"


# ======================= 4.2.2 margin compression =========================


def _margin_case(latest_margin, prior_margin=0.20, rev_yoy=-0.01, class_c=None,
                 revenue=None, prior_class_c=None):
    """Eight quarters; the latest and its year-ago base are set explicitly.

    ``revenue`` is what turns a one-off into margin points, so a case
    carrying a class_c_impact must give one.
    """
    qs = quarters(8, op_margin=prior_margin, revenue_yoy=rev_yoy)
    qs[-1] = R.Quarter(period=qs[-1].period, op_margin=latest_margin,
                       revenue_yoy=rev_yoy, class_c_impact=class_c,
                       revenue=revenue, basis="reported", accounting="gaap")
    qs[3] = R.Quarter(period=qs[3].period, op_margin=prior_margin,
                      revenue_yoy=rev_yoy, class_c_impact=prior_class_c,
                      revenue=revenue, basis="reported", accounting="gaap")
    return qs


def test_margin_exactly_150bps_does_not_trip():
    assert R.margin_compression_kill(_margin_case(0.1850)).state == R.NO_TRIP


def test_margin_just_over_150bps_trips():
    assert R.margin_compression_kill(_margin_case(0.1849)).state == R.TRIP


def test_margin_compression_with_growing_revenue_does_not_trip():
    r = R.margin_compression_kill(_margin_case(0.15, rev_yoy=0.05))
    assert r.state == R.NO_TRIP and "revenue growing" in r.detail


def test_margin_exactly_flat_revenue_still_counts_as_flat():
    assert R.margin_compression_kill(_margin_case(0.15, rev_yoy=0.0)).state == R.TRIP


# The Class C exemption is MAGNITUDE-AWARE. A one-off exempts the
# compression it actually explains and no more, so both margins are
# recomputed with their one-offs removed and the 150bps threshold reads
# what is left. 500bps of compression on 1,000 of revenue is explained
# by a one-off of 50 and not by one of 2.


def test_a_one_off_large_enough_to_explain_the_compression_exempts_it():
    """-50 on 1,000 of revenue is 500bps: exactly the compression."""
    r = R.margin_compression_kill(
        _margin_case(0.15, class_c=-50.0, revenue=1000.0))
    assert r.state == R.NO_TRIP
    assert "IS explained" in r.detail
    assert "+500bps reported" in " ".join(r.figures)
    assert "+0bps ex one-off" in " ".join(r.figures)


def test_a_token_one_off_no_longer_masks_a_collapse():
    """The case this rule was rewritten for: 2 MSEK against 400bps."""
    r = R.margin_compression_kill(
        _margin_case(0.16, class_c=-2.0, revenue=1000.0))
    assert r.state == R.TRIP
    assert "do NOT explain" in r.detail
    assert "+380bps ex one-off" in " ".join(r.figures)


def test_a_one_off_leaving_exactly_150bps_does_not_trip():
    """-35 on 1,000 leaves 150bps of the 500. The bound is inclusive."""
    r = R.margin_compression_kill(
        _margin_case(0.15, class_c=-35.0, revenue=1000.0))
    assert r.state == R.NO_TRIP
    assert "+150bps ex one-off" in " ".join(r.figures)


def test_a_one_off_leaving_just_over_150bps_trips():
    r = R.margin_compression_kill(
        _margin_case(0.15, class_c=-34.0, revenue=1000.0))
    assert r.state == R.TRIP
    assert "+160bps ex one-off" in " ".join(r.figures)


def test_a_one_off_in_the_year_ago_base_is_excluded_too():
    """A gain that flattered the base manufactures compression.

    Lindab's 2025-Q3 carries a +176 one-off. Comparing a later quarter
    against that inflated base would report compression the business
    never suffered.
    """
    r = R.margin_compression_kill(
        _margin_case(0.15, prior_class_c=50.0, revenue=1000.0))
    assert r.state == R.NO_TRIP
    assert "+500bps reported" in " ".join(r.figures)
    assert "+0bps ex one-off" in " ".join(r.figures)


def test_a_one_off_flattering_the_latest_quarter_no_longer_hides_compression():
    """The mirror case: reported margins look flat, the business is not."""
    r = R.margin_compression_kill(
        _margin_case(0.20, class_c=50.0, revenue=1000.0))
    assert r.state == R.TRIP
    assert "+0bps reported" in " ".join(r.figures)
    assert "+500bps ex one-off" in " ".join(r.figures)


@pytest.mark.parametrize("revenue", [None, 0.0])
def test_a_one_off_that_cannot_be_made_a_margin_is_not_an_exemption(revenue):
    """No revenue, no margin effect, no way to tell what it explains.

    The old rule exempted on presence alone, so an unquantifiable
    number bought a NO_TRIP. CANNOT EVALUATE is the honest answer.
    """
    r = R.margin_compression_kill(
        _margin_case(0.15, class_c=-50.0, revenue=revenue))
    assert r.state == R.CANNOT_EVALUATE
    assert "class_c_impact" in r.detail and "revenue" in r.detail


def test_both_margins_are_reported_when_a_one_off_is_excluded():
    figures = " ".join(R.margin_compression_kill(
        _margin_case(0.15, class_c=-50.0, revenue=1000.0)).figures)
    assert "15.00% reported, 20.00% ex one-off" in figures
    assert "20.00% reported, 20.00% ex one-off" in figures
    assert "class_c_impact -50.0 excluded" in figures


def test_a_quarter_with_no_one_off_reports_one_compression_figure():
    """No one-off, no ex-one-off noise: the two numbers are the same one."""
    figures = " ".join(R.margin_compression_kill(_margin_case(0.15)).figures)
    assert "compression +500bps" in figures
    assert "ex one-off" not in figures


def test_margin_missing_op_margin_cannot_evaluate():
    assert R.margin_compression_kill(_margin_case(None)).state == R.CANNOT_EVALUATE


# ========================= 4.2.3 guidance cuts ============================


def test_exactly_two_cuts_in_four_quarters_trips():
    qs = quarters(8, guidance_action=["none"] * 4 + ["cut", "maintained", "cut", "none"])
    assert R.guidance_cuts_kill(qs).state == R.TRIP


def test_one_cut_does_not_trip():
    qs = quarters(8, guidance_action=["cut"] + ["maintained"] * 7)
    assert R.guidance_cuts_kill(qs).state == R.NO_TRIP


def test_two_cuts_outside_the_window_do_not_trip():
    """Cuts five and six quarters back have aged out."""
    qs = quarters(8, guidance_action=["cut", "cut"] + ["maintained"] * 6)
    assert R.guidance_cuts_kill(qs).state == R.NO_TRIP


def test_unknown_guidance_cannot_evaluate():
    qs = quarters(8, guidance_action=["maintained"] * 7 + [None])
    r = R.guidance_cuts_kill(qs)
    assert r.state == R.CANNOT_EVALUATE and "guidance_action" in r.detail


# ============================ 4.2.4 EPS misses ============================


def test_exactly_three_eps_misses_trips():
    qs = quarters(8, eps=[1.0] * 5 + [0.9, 0.9, 0.9], eps_consensus=1.0)
    assert R.eps_misses_kill(qs).state == R.TRIP


def test_two_eps_misses_does_not_trip():
    qs = quarters(8, eps=[1.0] * 6 + [0.9, 0.9], eps_consensus=1.0)
    assert R.eps_misses_kill(qs).state == R.NO_TRIP


def test_eps_exactly_meeting_consensus_is_not_a_miss():
    qs = quarters(8, eps=1.0, eps_consensus=1.0)
    assert R.eps_misses_kill(qs).state == R.NO_TRIP


def test_missing_consensus_cannot_evaluate_and_says_manual_only():
    qs = quarters(8, eps=1.0, eps_consensus=[1.0] * 7 + [None])
    r = R.eps_misses_kill(qs)
    assert r.state == R.CANNOT_EVALUATE
    assert "MANUAL ONLY" in r.detail and "consensus" in r.detail


def test_confirmed_misses_trip_even_with_gaps_elsewhere():
    """Three confirmed misses cannot be un-missed by better data."""
    qs = quarters(8, eps=[0.9, 0.9, 0.9] + [1.0] * 5,
                  eps_consensus=[1.0, 1.0, 1.0] + [None] * 5)
    assert R.eps_misses_kill(qs).state == R.TRIP


# =========================== 4.2.5 leverage ===============================


def test_net_debt_ebitda_exactly_at_limit_does_not_trip():
    assert R.leverage_kill(quarters(8, net_debt_ebitda=3.5)).state == R.NO_TRIP


def test_net_debt_ebitda_just_over_limit_trips():
    assert R.leverage_kill(quarters(8, net_debt_ebitda=3.51)).state == R.TRIP


def test_covenant_headroom_exactly_at_threshold_trips():
    qs = quarters(8, net_debt_ebitda=1.0, covenant_headroom=0.10)
    r = R.leverage_kill(qs)
    assert r.state == R.TRIP and "covenant" in r.detail


def test_covenant_headroom_above_threshold_does_not_trip():
    qs = quarters(8, net_debt_ebitda=1.0, covenant_headroom=0.11)
    assert R.leverage_kill(qs).state == R.NO_TRIP


def test_leverage_missing_both_inputs_cannot_evaluate():
    assert R.leverage_kill(quarters(8)).state == R.CANNOT_EVALUATE


# ======================== 4.2.6 exec departures ===========================


def test_ceo_and_cfo_within_twelve_months_trips():
    changes = [R.ExecChange("CEO", AS_OF - timedelta(days=30)),
               R.ExecChange("CFO", AS_OF - timedelta(days=200))]
    assert R.exec_departure_kill(changes, AS_OF).state == R.TRIP


def test_exactly_365_days_is_inside_the_window():
    changes = [R.ExecChange("CEO", AS_OF - timedelta(days=365)),
               R.ExecChange("CFO", AS_OF - timedelta(days=10))]
    assert R.exec_departure_kill(changes, AS_OF).state == R.TRIP


def test_366_days_has_aged_out():
    changes = [R.ExecChange("CEO", AS_OF - timedelta(days=366)),
               R.ExecChange("CFO", AS_OF - timedelta(days=10))]
    assert R.exec_departure_kill(changes, AS_OF).state == R.NO_TRIP


def test_ceo_alone_does_not_trip():
    changes = [R.ExecChange("CEO", AS_OF - timedelta(days=30))]
    assert R.exec_departure_kill(changes, AS_OF).state == R.NO_TRIP


def test_absent_exec_changes_cannot_evaluate():
    r = R.exec_departure_kill(None, AS_OF)
    assert r.state == R.CANNOT_EVALUATE and "MANUAL" in r.detail


def test_empty_exec_changes_means_checked_and_none():
    """Absent is unknown; empty is an affirmative 'no departures'."""
    assert R.exec_departure_kill([], AS_OF).state == R.NO_TRIP


# ======================= 4.2.7 working capital ============================


def _wc_case(rec_growth, rev_yoy=0.10, n_flagged=2):
    """Build receivables that grow rec_growth YoY for the last n quarters."""
    base = 100.0
    rec = [base] * 8
    for i in range(8 - n_flagged, 8):
        rec[i] = rec[i - 4] * (1 + rec_growth)
    return quarters(8, revenue_yoy=rev_yoy, receivables=rec, inventory=base)


def test_receivables_exactly_1_5x_revenue_growth_does_not_trip():
    assert R.working_capital_kill(_wc_case(0.15, rev_yoy=0.10)).state == R.NO_TRIP


def test_receivables_just_over_1_5x_trips():
    assert R.working_capital_kill(_wc_case(0.1501, rev_yoy=0.10)).state == R.TRIP


def test_one_quarter_over_the_line_does_not_trip():
    assert R.working_capital_kill(_wc_case(0.50, rev_yoy=0.10, n_flagged=1)).state == R.NO_TRIP


def test_any_working_capital_growth_trips_when_revenue_is_shrinking():
    """1.5x a negative growth rate is meaningless; growth alone is the signal."""
    assert R.working_capital_kill(_wc_case(0.02, rev_yoy=-0.05)).state == R.TRIP


def test_working_capital_missing_fields_cannot_evaluate():
    qs = quarters(8, revenue_yoy=0.1, receivables=None, inventory=None)
    assert R.working_capital_kill(qs).state == R.CANNOT_EVALUATE


# ============================ composition =================================


def test_absent_history_evaluates_every_rule_as_cannot_evaluate():
    """Absent history is not silence: each rule still reports."""
    results = R.evaluate_hard_kills(None, None, AS_OF)
    assert len(results) == 8
    assert all(r.state == R.CANNOT_EVALUATE for r in results)
    assert all(r.detail for r in results)


def test_every_framework_rule_is_covered_exactly_once():
    ids = [r.rule for r in R.evaluate_hard_kills(quarters(8), [], AS_OF)]
    assert ids == ["4.2.1", "4.2.2", "4.2.3", "4.2.4", "4.2.5",
                   "4.2.6", "4.2.7", "4.3.soft"]


def test_no_rule_ever_recommends_an_action():
    """The engine flags; it never advises."""
    banned = ("sell", "buy", "exit", "recommend", "should")
    for r in R.evaluate_hard_kills(quarters(8), [], AS_OF):
        assert not any(w in f"{r.name} {r.detail}".lower() for w in banned)


# --- E30: 4.2.1 reads ORGANIC where the issuer discloses it ---------------


def _q(period, reported, organic=None):
    return R.Quarter(period=period, revenue_yoy=reported,
                     revenue_yoy_organic=organic, basis="reported")


def test_e30_reads_organic_and_names_the_basis():
    """B20 asked which measure the limb means. E30's answer is organic, and
    the result must SAY which it read -- that was B20's actual requirement."""
    got = R.revenue_decline_kill([_q("2025-Q1", -0.05, 0.03),
                                  _q("2025-Q2", -0.04, 0.02)])
    assert got.state == R.NO_TRIP
    assert "organic" in got.name
    assert "organic" in got.detail
    assert any("reported" in f for f in got.figures)   # shown beside it


def test_e30_b9s_direction_still_holds_reported_down_organic_up():
    """UNA.AS's shape: currency and disposals are not demand loss."""
    got = R.revenue_decline_kill([_q("2025-Q1", -0.046, 0.030),
                                  _q("2025-Q2", -0.035, 0.058)])
    assert got.state == R.NO_TRIP


def test_e30_the_jdl_mirror_reported_up_organic_down_is_a_kill():
    """JD.L: reported +10.5%, organic -0.1% then -1.3%.

    Under the deleted Gate 3 revenue limb JD.L PASSED. E30 is the ruling
    that the reported figure does not rescue it.
    """
    got = R.revenue_decline_kill([_q("2027-Q1", 0.105, -0.001),
                                  _q("2027-Q2", 0.105, -0.013)])
    assert got.state == R.TRIP
    assert "reported revenue GREW" in got.detail


def test_e30_falls_back_to_reported_when_no_organic_is_disclosed():
    got = R.revenue_decline_kill([_q("2025-Q1", -0.05), _q("2025-Q2", -0.04)])
    assert got.state == R.TRIP
    assert "reported" in got.name and "organic" not in got.name


def test_e30_a_window_mixing_the_two_measures_cannot_evaluate():
    """A run counted partly on organic and partly on reported is not a run."""
    got = R.revenue_decline_kill([_q("2025-Q1", -0.05, -0.02),
                                  _q("2025-Q2", -0.04)])
    assert got.state == R.CANNOT_EVALUATE
    assert "not a run" in got.detail


def test_e30_pndora_quarter_does_not_trip_on_a_currency_movement():
    """-3.2% reported, +2% organic in the same quarter -- B20's own case."""
    got = R.revenue_decline_kill([_q("2026-Q1", -0.032, 0.02),
                                  _q("2026-Q2", 0.020, 0.03)])
    assert got.state == R.NO_TRIP
