"""E126: the coverage limb reads a STAIRCASE where a filer states no
subtotal before financing cost, and below four evaluable gates a name
carries no tier.

Ruled 2026-09-20 on B-15. The staircase: the stated subtotal; else INCOME
BEFORE INCOME TAXES plus THAT STATED INTEREST EXPENSE, both printed lines
in the same column; else DATA MISSING with the denominator rebasing.
"""
from datetime import date
from pathlib import Path

import pytest

from vss import manual as M

STORE = Path("config/manual")
AS_OF = date(2026, 9, 20)


def load(ticker):
    parsed = M.load_manual(ticker, directory=STORE)
    return parsed, M.section5_basis(parsed)


# --- step 1: the stated subtotal, unchanged ------------------------------

def test_step_1_uses_the_stated_subtotal_and_says_nothing_about_E126():
    parsed, basis = load("CTSH")
    cov = M.interest_coverage(parsed, basis)
    assert cov.ebit == M.resolve_on_basis(parsed, basis, "operating_income").value
    assert "E126" not in (cov.why or "")


# --- step 2: pre-tax income plus the stated interest expense -------------

def test_step_2_forms_NVRs_numerator_from_two_printed_lines():
    """NVR states no subtotal: its statement runs to 'Income before taxes
    1,761,932' with each segment's interest expense above it."""
    parsed, basis = load("NVR")
    pre_tax = M.resolve_on_basis(parsed, basis, "income_before_taxes").value
    charged = M.resolve_on_basis(parsed, basis, "finance_costs_period").value
    cov = M.interest_coverage(parsed, basis)
    assert pre_tax == 1_761_932_000 and charged == 28_835_000
    assert cov.ebit == pytest.approx(pre_tax + charged)


def test_step_2_names_both_lines_in_what_it_prints():
    parsed, basis = load("NVR")
    cov = M.interest_coverage(parsed, basis)
    detail = (cov.why or "") + (cov.note or "" if hasattr(cov, "note") else "")
    assert "E126 step 2" in detail
    assert "income before income taxes" in detail and "stated interest expense" in detail


def test_NVRs_coverage_now_PASSES_where_the_wall_stood():
    """B-15 blocked this name entirely: no Gate 3, so no score, no tier, no
    MBP at any price."""
    parsed, basis = load("NVR")
    cov = M.interest_coverage(parsed, basis)
    assert cov.net_income_case                    # E118: finance income exceeds costs
    assert cov.gross_cover > 5                    # and the gross cover clears 5x


def test_step_2_is_not_taken_when_step_1_can_be():
    """A step is taken only where the step above it cannot be."""
    parsed, basis = load("GDDY")
    cov = M.interest_coverage(parsed, basis)
    assert "E126 step 2" not in (cov.why or "")


# --- what step 2 may NOT be built from -----------------------------------

def test_the_only_operands_are_the_two_named_lines():
    """E126 forbids every other reconstruction in its own sentence: not
    EBITDA (E5 stands), not gross profit less SG&A, not revenue less cost of
    sales, not segment subtotals, not a note's interest INCURRED."""
    import inspect
    src = inspect.getsource(M.interest_coverage)
    step2 = src[src.index("E126 STEP 2"):src.index("denominator = resolve_or_subtract")]
    assert '"income_before_taxes"' in step2 and '"finance_costs_period"' in step2
    for forbidden in ('"ebitda"', '"gross_profit"', '"revenue"', '"net_income"',
                      '"finance_costs_paid"', '"operating_income_adjusted"'):
        assert forbidden not in step2, forbidden


def test_the_field_is_read_by_gate_3_and_by_nothing_in_section_5():
    spec = M.FIELDS_BY_NAME["income_before_taxes"]
    assert spec.reads == ("5.3",)
    section5 = {s.name for s in M.FIELDS if any(r.startswith("5.1") for r in s.reads)}
    assert "income_before_taxes" not in section5


# --- step 3: DATA MISSING, and what prints instead -----------------------

def test_step_3_is_PHM_and_it_says_which_step_ran_out():
    parsed, basis = load("PHM")
    cov = M.interest_coverage(parsed, basis)
    assert cov.ebit is None
    assert "E126" in cov.why and "no subtotal before financing cost" in cov.why
    assert "OUT OF THE GATE COUNT" in cov.why


def test_step_3_prints_the_interest_figures_with_their_own_citation():
    parsed, basis = load("PHM")
    block = M.step3_block(parsed, basis, notes="")
    joined = " ".join(block)
    assert "net_interest_paid 17,248,000" in joined
    assert "Interest paid (capitalized), net" in joined      # the citation, verbatim
    assert "capitalizes all Homebuilding interest" in joined or "capitalised" in joined.lower()


def test_the_maturity_wall_comes_from_the_entry_and_falls_back_to_the_document():
    parsed, basis = load("PHM")
    from vss.config import load_watchlist
    entry = next(e for e in load_watchlist(Path("config/watchlist.yaml"))
                 if e.ticker == "PHM")
    with_entry = " ".join(M.step3_block(parsed, basis, notes=entry.notes))
    assert "maturity wall (from the entry)" in with_entry
    assert "251.9" in with_entry and "892.9" in with_entry
    without = " ".join(M.step3_block(parsed, basis, notes=""))
    assert "NOT in the store and not on the entry" in without
    assert "liquidity paragraph" in without


# --- the tier hold -------------------------------------------------------

def test_the_hold_fires_below_four_evaluable_gates():
    parsed, basis = load("PHM")
    count, why = M.evaluable_gates(parsed, basis)
    assert count == 3
    held = M.tier_hold(parsed, basis)
    assert "TIER HELD (E126)" in held and "NO TIER" in held and "NO MBP" in held
    assert "HOLD, not a threshold" in held and "B50" in held


def test_the_hold_does_not_fire_at_four():
    for ticker in ("CTSH", "GDDY", "NVR", "LIAB.ST"):
        parsed, basis = load(ticker)
        assert M.evaluable_gates(parsed, basis)[0] >= 4, ticker
        assert M.tier_hold(parsed, basis) == "", ticker


def test_gate_4_is_always_out_of_the_count():
    parsed, basis = load("CTSH")
    count, why = M.evaluable_gates(parsed, basis)
    assert count == 4                                   # five, less Gate 4
    assert any("E99" in r for r in why)


def test_no_name_on_the_watchlist_carries_a_tier_against_a_short_denominator():
    """The case E126 says must not exist. The nightly prints it; this proves
    it is not true today."""
    from vss.config import load_watchlist
    offenders = []
    for entry in load_watchlist(Path("config/watchlist.yaml")):
        if entry.tier is None:
            continue
        try:
            parsed, basis = load(entry.ticker)
        except Exception:
            continue
        if M.tier_hold(parsed, basis):
            offenders.append(entry.ticker)
    assert offenders == []
