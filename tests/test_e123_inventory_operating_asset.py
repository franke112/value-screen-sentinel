"""E123: where the operating asset is inventory and its purchase runs
through operating cash flow, Gate 3's FCF and leverage limbs are DATA
MISSING and §4.4 rebases (E99's treatment). Two measured figures print in
their place, and neither decides anything.

The case: PHM and NVR were blocked together. PulteGroup's own five years
show the inversion -- the strongest free cash flow year, 2,104.6m in
FY2023, follows the 2022 rate shock; the weakest, 555.8m, is the boom year.
"""
from pathlib import Path

import pytest

from vss import manual as M

STORE = Path("config/manual")


@pytest.fixture(scope="module")
def phm():
    return M.load_manual("PHM", directory=STORE)


def test_the_declaration_is_the_trigger_and_it_is_a_fact_with_a_page(phm):
    assert M.inventory_operating_asset(phm) is True
    declared = phm.operating_asset_is_inventory
    assert "House and land inventory" in declared.page
    assert "operating activities" in declared.page
    assert declared.source.endswith(".htm")


def test_a_file_without_the_declaration_is_an_ordinary_filer():
    acn = M.load_manual("ACN", directory=STORE)
    assert M.inventory_operating_asset(acn) is False


def test_the_leverage_limb_is_DATA_MISSING_and_says_why(phm):
    basis = M.section5_basis(phm)
    lev = M.gate3_leverage(phm, basis)
    assert lev.ratio is None
    assert "E123" in lev.why and "Out of the gate count" in lev.why
    assert "inventory" in lev.why


def test_the_declaration_beats_legs_that_would_otherwise_form():
    """Even a file with every leg present goes DATA MISSING when declared."""
    lii = M.load_manual("LII", directory=STORE)
    basis = M.section5_basis(lii)
    assert M.gate3_leverage(lii, basis).ratio is not None      # forms today
    declared = M.InventoryOperatingAsset(True, "s", "p")
    import dataclasses
    as_builder = dataclasses.replace(lii, operating_asset_is_inventory=declared)
    assert M.gate3_leverage(as_builder, basis).ratio is None


def test_both_capitalisation_figures_and_both_net_positions(phm):
    cap = M.capitalisation(phm, M.section5_basis(phm))
    assert round(cap.ratio * 100, 2) == 11.16          # the issuer states 11.2%
    assert round(cap.ratio_with_finance * 100, 2) == 14.28
    assert cap.net_position == pytest.approx(-349_771_000)   # net CASH
    assert cap.net_position_with_finance == pytest.approx(182_567_000)
    lines = " ".join(cap.lines())
    assert "DECIDES ANYTHING" in lines and "SPREAD" in lines
    assert "%" in lines and "information, not a ratio" in lines


def test_the_second_line_is_DATA_MISSING_AND_NEVER_OMITTED_without_the_figure(phm):
    """An omitted line and a zero look identical in a packet (owner)."""
    import dataclasses
    fy = [a for a in phm.annual if str(a.period_end) == "2025-12-31"][0]
    stripped = dataclasses.replace(fy, figures={
        k: v for k, v in fy.figures.items() if k != "captive_finance_debt"})
    without = dataclasses.replace(
        phm, annual=tuple(stripped if a is fy else a for a in phm.annual))
    cap = M.capitalisation(without, M.section5_basis(without))
    assert cap.ratio is not None                       # the first line still prints
    assert cap.ratio_with_finance is None
    lines = cap.lines()
    assert any("including captive finance debt: DATA MISSING" in l for l in lines)
    assert any("cannot be reached by tag" in l for l in lines)


def test_no_threshold_is_attached_to_any_of_it(phm):
    """It can neither pass nor fail: E7's shape, and E63's."""
    cap = M.capitalisation(phm, M.section5_basis(phm))
    assert not hasattr(cap, "state")
    assert not any(w in " ".join(cap.lines()) for w in ("PASS", "FAIL", "limit", "against"))


def test_interest_coverage_is_UNTOUCHED_for_a_declared_filer():
    """The ruling names two limbs. Coverage forms for a builder and stays."""
    import inspect
    src = inspect.getsource(M.interest_coverage)
    assert "inventory_operating_asset" not in src
