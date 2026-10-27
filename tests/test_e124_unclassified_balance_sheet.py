"""E124: an UNCLASSIFIED balance sheet states one debt caption and no
current / non-current split. The caption enters the non-current leg whole,
the current leg stays absent, and net debt adds the two -- so the absence
must not refuse net debt where the file declares the shape.

The case: PHM read `input missing -- financial_liabilities_current` on its
net debt row from 2026-09-20 until the declaration existed, against a
ruling that said nothing in section 5 reads the split.
"""
import dataclasses
from pathlib import Path

import pytest

from vss import manual as M

STORE = Path("config/manual")


@pytest.fixture(scope="module")
def phm():
    return M.load_manual("PHM", directory=STORE)


def _net_debt_state(parsed):
    return next(r for r in M.ratio_states(parsed) if r.name == "net debt")


def test_the_declaration_is_a_fact_with_a_page(phm):
    declared = phm.unclassified_balance_sheet
    assert declared.value is True
    assert "Notes payable 1,631,098" in declared.page
    assert declared.source.endswith(".htm")


def test_net_debt_forms_on_the_one_caption(phm):
    basis = M.section5_basis(phm)
    assert M.unsplit_current_leg(phm, basis) is True
    value, why = M.net_debt_on_basis(phm, basis)
    # Notes payable 1,631,098 - cash 1,980,869 ($000s): net CASH
    assert value == pytest.approx(-349_771_000)
    assert "E124" in why and "no current leg" in why
    assert _net_debt_state(phm).state == M.RATIO_OK


def test_it_agrees_with_E123s_measured_net_position(phm):
    """Two paths over the same store must not disagree."""
    basis = M.section5_basis(phm)
    cap = M.capitalisation(phm, basis)
    assert M.net_debt_on_basis(phm, basis)[0] == pytest.approx(cap.net_position)


def test_without_the_declaration_the_absence_is_DATA_MISSING(phm):
    classified = dataclasses.replace(phm, unclassified_balance_sheet=None)
    basis = M.section5_basis(classified)
    assert M.unsplit_current_leg(classified, basis) is False
    value, why = M.net_debt_on_basis(classified, basis)
    assert value is None and "financial_liabilities_current" in why
    assert _net_debt_state(classified).state == M.RATIO_MISSING


def test_a_declared_no_is_a_classified_filer(phm):
    said_no = dataclasses.replace(
        phm, unclassified_balance_sheet=M.UnclassifiedBalanceSheet(False, "s", "p"))
    assert M.net_debt_on_basis(said_no, M.section5_basis(said_no))[0] is None


def test_the_declaration_never_supplies_the_non_current_leg(phm):
    """Both legs absent is DATA MISSING, declared or not."""
    fy = [a for a in phm.annual if str(a.period_end) == "2025-12-31"][0]
    stripped = dataclasses.replace(fy, figures={
        k: v for k, v in fy.figures.items()
        if k != "financial_liabilities_noncurrent"})
    without = dataclasses.replace(
        phm, annual=tuple(stripped if a is fy else a for a in phm.annual))
    basis = M.section5_basis(without)
    assert M.unsplit_current_leg(without, basis) is False
    value, why = M.net_debt_on_basis(without, basis)
    assert value is None
    assert "financial_liabilities_current" in why
    assert "financial_liabilities_noncurrent" in why


def test_a_classified_filer_is_untouched():
    cprt = M.load_manual("CPRT", directory=STORE)
    assert cprt.unclassified_balance_sheet is None
    assert M.unsplit_current_leg(cprt, M.section5_basis(cprt)) is False


@pytest.mark.parametrize("raw, words", [
    ({"value": True, "source": "s"}, "source and page"),
    ({"value": "yes please", "source": "s", "page": "p"}, "yes or no"),
    ({"value": True, "source": "s", "page": "p", "split": 0}, "unknown key"),
    ("yes", "expected a mapping"),
])
def test_the_block_is_refused_without_its_evidence(raw, words):
    with pytest.raises(M.ManualError, match=words):
        M._parse_unclassified_balance_sheet(raw, Path("PHM.yaml"))
