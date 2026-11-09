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


















# ===================== 4.3 soft flag: sequential run ======================








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










# The Class C exemption is MAGNITUDE-AWARE. A one-off exempts the
# compression it actually explains and no more, so both margins are
# recomputed with their one-offs removed and the 150bps threshold reads
# what is left. 500bps of compression on 1,000 of revenue is explained
# by a one-off of 50 and not by one of 2.






















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






def test_covenant_headroom_exactly_at_threshold_trips():
    qs = quarters(8, net_debt_ebitda=1.0, covenant_headroom=0.10)
    r = R.covenant_kill(qs)
    assert r.state == R.TRIP and "covenant" in r.detail


def test_covenant_headroom_above_threshold_does_not_trip():
    qs = quarters(8, net_debt_ebitda=1.0, covenant_headroom=0.11)
    assert R.covenant_kill(qs).state == R.NO_TRIP


def test_a_high_stated_leverage_no_longer_trips():
    """E168 (attempt #25): only covenant proximity is left in 4.2.5."""
    qs = quarters(8, net_debt_ebitda=9.0, covenant_headroom=0.50)
    assert R.covenant_kill(qs).state == R.NO_TRIP
    assert R.covenant_kill(quarters(8, net_debt_ebitda=9.0)).state == R.CANNOT_EVALUATE




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












# ============================ composition =================================


def test_absent_history_evaluates_every_rule_as_cannot_evaluate():
    """Absent history is not silence: each rule still reports."""
    results = R.evaluate_hard_kills(None, None, AS_OF)
    assert len(results) == 4      # E163 removed 4.2.1, 4.2.2, 4.2.7; E168 the 4.3 flag
    assert all(r.state == R.CANNOT_EVALUATE for r in results)
    assert all(r.detail for r in results)


def test_every_framework_rule_is_covered_exactly_once():
    ids = [r.rule for r in R.evaluate_hard_kills(quarters(8), [], AS_OF)]
    assert ids == ["4.2.3", "4.2.4", "4.2.5", "4.2.6"]   # E163, E168


def test_no_rule_ever_recommends_an_action():
    """The engine flags; it never advises."""
    banned = ("sell", "buy", "exit", "recommend", "should")
    for r in R.evaluate_hard_kills(quarters(8), [], AS_OF):
        assert not any(w in f"{r.name} {r.detail}".lower() for w in banned)


# --- E30: 4.2.1 reads ORGANIC where the issuer discloses it ---------------


def _q(period, reported, organic=None):
    return R.Quarter(period=period, revenue_yoy=reported,
                     revenue_yoy_organic=organic, basis="reported")












