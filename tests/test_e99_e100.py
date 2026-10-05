"""E99's rebase and E100's definition-caused crossing, ruled 2026-09-01.

E99 — Gate 4's data has never existed for any name, so it scores DATA
MISSING and leaves the gate count. §4.4 rebases to a denominator of four and
every threshold drops by one. **No score moves**; the bar does.

E100 — the cushion comes under E28's discipline. The multipliers stand; a
change to them is dated and applies at the next scheduled reassessment, and
an MBP crossing caused by the DEFINITION rather than the price is marked and
arms nothing.

**They are tested together because E99's first consequence is E100's first
case.** The rebase moves GDDY to tier 2, its MBP from 85.91 to 99.13, and a
close of 97.88 from 13.9% above the line to 1.3% below it with no price
movement at all.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from vss import rules as R
from vss.store import persist, previous_mbps

ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = (ROOT / "reference" / "FRAMEWORK.md").read_text(encoding="utf-8")


# --- E99: the scale rebased, and the gate is NOT deleted ------------------


def test_the_conviction_scale_counts_FOUR_gates():
    assert "`Score = (Gates passed: 0–4) + Σ(green flags) − Σ(soft flags)`" in FRAMEWORK
    assert "(Gates passed: 0–5)" not in FRAMEWORK


def test_every_threshold_moved_down_by_one():
    assert "- **≥ 6:** High conviction" in FRAMEWORK
    assert "- **4–5:** Medium" in FRAMEWORK
    assert "- **≤ 3:** Drop or watchlist" in FRAMEWORK


def test_gate_4_is_DATA_MISSING_and_NOT_DELETED():
    """A gate that is DATA MISSING is a gate waiting for data; a gate that
    is deleted is a judgement nobody can revisit."""
    assert "### Gate 4 — Valuation discount (at least 2 of 3) — **DATA MISSING (E99)**" in FRAMEWORK
    # its three limbs are still there, word for word
    assert "Forward P/E ≥ **20% below** its own 5-year median" in FRAMEWORK
    assert "EV/EBIT or P/S below peer median" in FRAMEWORK
    assert "FCF yield ≥ 1.5× sector median" in FRAMEWORK
    assert "returns to the denominator" in FRAMEWORK


def test_tier_1_keeps_its_other_two_conditions():
    """A score that clears the bar does not by itself make a tier 1 --
    UNA.AS scores 7 and is held at tier 2 on the fortress and domain
    conditions."""
    assert "Conviction **≥ 6** (E99), fortress balance sheet, secular tailwind" in FRAMEWORK


def test_the_tier_table_carries_E90s_cushions_and_says_E100_governs_them():
    assert "FV_base × **0.85**" in FRAMEWORK
    assert "FV_base × **0.75**" in FRAMEWORK
    assert "FV_base × **0.65**" in FRAMEWORK
    assert "governed by E100" in FRAMEWORK


def test_the_rebase_moves_no_name_GDDY_corrected_2026_09_19():
    """Measured, not asserted: of the five names carrying a tier, none is
    moved by the rebase. GDDY scored 6, which clears E99's tier-1 bar but
    not tier 1's other two conditions (fortress balance sheet, secular
    tailwind -- both found absent on 2026-08-30), so it is tier 2 on the
    new scale -> E77 -> tier 3, as it was on the old one. The 2026-09-01
    reading that took score 6 as tier 1 misapplied section 5.3 and was
    corrected by the owner on 2026-09-19 (GDDY back to tier 3)."""
    from vss.config import load_watchlist

    tiers = {e.ticker: e.tier for e in
             load_watchlist(ROOT / "config" / "watchlist.yaml")}
    assert tiers["GDDY"] == 3, "score 6 without fortress/tailwind is not tier 1"
    # unchanged by E99, each for its own recorded reason
    assert tiers["SAP.DE"] == 1      # score 7, tier 1 on both scales
    assert tiers["CTSH"] == 2        # score 5, tier 2 on both scales
    assert tiers["LIAB.ST"] == 2     # no score on file -- carried, not guessed
    assert tiers["UNA.AS"] == 2      # score 7, held on the other two conditions


def test_GDDYs_mbp_is_the_tier_2_cushion_on_its_unrounded_base():
    assert R.compute_mbp_e90(132.1752, 2) == pytest.approx(99.13)
    assert R.compute_mbp_e90(132.1752, 3) == pytest.approx(85.91)


# --- E100: the test, as a test and not a judgement ------------------------


def test_a_close_that_reaches_the_OLD_line_is_a_real_crossing():
    """The price did it. Nothing is marked."""
    assert not R.crossing_is_definition_caused(80.0, mbp=99.13, previous_mbp=85.91)


def test_a_close_that_only_the_NEW_line_reaches_is_definition_caused():
    """GDDY's own numbers: 97.88 is below 99.13 and above 85.91."""
    assert R.crossing_is_definition_caused(97.88, mbp=99.13, previous_mbp=85.91)


def test_a_name_that_was_ALREADY_below_is_not_a_new_crossing_either_way():
    assert not R.crossing_is_definition_caused(80.0, mbp=85.91, previous_mbp=99.13)


def test_no_crossing_at_all_is_not_marked():
    assert not R.crossing_is_definition_caused(120.0, mbp=99.13, previous_mbp=85.91)


def test_an_unchanged_mbp_can_only_be_a_price_crossing():
    assert not R.crossing_is_definition_caused(97.88, mbp=99.13, previous_mbp=99.13)


def test_a_first_run_cannot_tell_and_does_not_pretend_to():
    """No previous MBP is not evidence that the price did it. Asserting
    either way would be inventing the answer."""
    assert not R.crossing_is_definition_caused(97.88, mbp=99.13, previous_mbp=None)


# --- and the verdict says so ---------------------------------------------


def test_the_verdict_names_both_lines_and_refuses_to_arm():
    verdict = R.mbp_verdict(97.88, 99.13, previous_mbp=85.91)
    assert verdict.code == R.DEFINITION_CROSSING
    assert verdict.label == "AT/BELOW MBP — DEFINITION-CAUSED"
    assert "99.13" in verdict.detail and "85.91" in verdict.detail
    assert "DENOMINATOR moving" in verdict.detail
    assert "no alert is armed" in verdict.detail


def test_a_real_crossing_still_reads_AT_BELOW_MBP():
    verdict = R.mbp_verdict(80.0, 99.13, previous_mbp=85.91)
    assert verdict.code == R.AT_BELOW_MBP
    assert "DEFINITION" not in verdict.detail


def test_a_definition_crossing_is_still_ACTIONABLE():
    """Marked is not hidden. The owner must SEE it -- what he must not do is
    arm an alert on it, and the line says so."""
    verdict = R.mbp_verdict(97.88, 99.13, previous_mbp=85.91)
    assert verdict.code not in (R.NO_ACTION, R.DROPPED)


def test_the_superseded_mark_and_the_definition_mark_compose():
    verdict = R.mbp_verdict(97.88, 99.13, superseded=True, previous_mbp=85.91)
    assert R.MBP_SUPERSEDED_MARK in verdict.detail
    assert R.MBP_DEFINITION_MARK in verdict.detail


def test_a_broken_series_still_wins_over_everything():
    """K4 first: the close being compared may be the phantom bar itself."""
    verdict = R.mbp_verdict(97.88, 99.13, previous_mbp=85.91,
                            series_finding="a 100x scale switch")
    assert verdict.code == R.DATA_MISSING


# --- the comparator comes out of the store -------------------------------


def _row(ticker: str, run_ts: str, mbp: float | None, *, scope=None) -> dict:
    return {"run_ts": run_ts, "as_of": run_ts[:10], "ticker": ticker,
            "mbp": mbp, "blocked": 0, "ticker_filter": scope}


def test_the_previous_mbp_comes_from_the_newest_FULL_run(tmp_path: Path):
    db = tmp_path / "vss.sqlite"
    persist(db, [_row("GDDY", "2026-08-30T22:30:00", 85.91)])
    persist(db, [_row("GDDY", "2026-08-31T22:30:00", 85.91)])
    assert previous_mbps(db) == {"GDDY": 85.91}


def test_a_scoped_run_is_not_THE_PREVIOUS_RUN_for_the_others(tmp_path: Path):
    """A `--ticker` run examined one name. Letting it stand as the previous
    run for the rest would compare tonight against a night that never
    looked at them."""
    db = tmp_path / "vss.sqlite"
    persist(db, [_row("GDDY", "2026-08-31T22:30:00", 85.91),
                 _row("CTSH", "2026-08-31T22:30:00", 67.04)])
    persist(db, [_row("GDDY", "2026-09-01T10:00:00", 99.13, scope="GDDY")])
    assert previous_mbps(db) == {"GDDY": 85.91, "CTSH": 67.04}


def test_nothing_stored_is_an_empty_comparator_not_a_zero(tmp_path: Path):
    assert previous_mbps(tmp_path / "nothing.sqlite") == {}


# --- end to end: two runs, a tier change between them ---------------------


def test_a_tier_change_between_two_runs_is_marked_on_the_second(tmp_path: Path):
    """**THE ONE THAT MATTERS.** Night one at tier 3, night two at tier 2,
    the same close on both. Before E100 the second night printed a plain
    AT/BELOW MBP -- a buy signal manufactured by the denominator, which is
    what happened to CTSH on 2026-08-30."""
    db = tmp_path / "vss.sqlite"
    close = 97.88
    base = 132.1752

    night_one = R.assess(
        ticker="GDDY", status="WATCH-PRICED", last_close=close,
        last_close_date=date(2026, 8, 31), drawdown=0.34, fv_base=base,
        tier=3, stop_price=None, catalyst_date=None, catalyst_resolved=None,
        catalyst_event=None, as_of=date(2026, 8, 31))
    assert night_one.mbp == pytest.approx(85.91)
    assert not any(v.code in (R.AT_BELOW_MBP, R.DEFINITION_CROSSING)
                   for v in night_one.verdicts), "not below the old line"
    persist(db, [_row("GDDY", "2026-08-31T22:30:00", night_one.mbp)])

    night_two = R.assess(
        ticker="GDDY", status="WATCH-PRICED", last_close=close,
        last_close_date=date(2026, 9, 1), drawdown=0.34, fv_base=base,
        tier=2, stop_price=None, catalyst_date=None, catalyst_resolved=None,
        catalyst_event=None, as_of=date(2026, 9, 1),
        previous_mbp=previous_mbps(db)["GDDY"])
    assert night_two.mbp == pytest.approx(99.13)
    codes = [v.code for v in night_two.verdicts]
    assert R.DEFINITION_CROSSING in codes
    assert R.AT_BELOW_MBP not in codes, (
        "a rule change produced an unmarked buy signal")


def test_the_same_move_caused_by_a_PRICE_FALL_is_not_marked(tmp_path: Path):
    """The other half of the test: the tier stays put and the price falls
    through the line. That is a real crossing and must read as one."""
    db = tmp_path / "vss.sqlite"
    persist(db, [_row("GDDY", "2026-08-31T22:30:00", 85.91)])
    verdict = R.assess(
        ticker="GDDY", status="WATCH-PRICED", last_close=80.0,
        last_close_date=date(2026, 9, 1), drawdown=0.46, fv_base=132.1752,
        tier=3, stop_price=None, catalyst_date=None, catalyst_resolved=None,
        catalyst_event=None, as_of=date(2026, 9, 1),
        previous_mbp=previous_mbps(db)["GDDY"])
    codes = [v.code for v in verdict.verdicts]
    assert R.AT_BELOW_MBP in codes
    assert R.DEFINITION_CROSSING not in codes
