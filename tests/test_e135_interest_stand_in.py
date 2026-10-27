"""E135: net interest paid stated only in the ANNUAL cash flow statement
stands in for a TTM window, on E120's terms. The case: BETS-B.ST, whose
interim reports state no interest paid or received."""
import dataclasses
from datetime import datetime
from pathlib import Path

import pytest

from vss import manual as M
from vss import runrecord as R

STORE = Path("config/manual")


@pytest.fixture(scope="module")
def bets():
    return M.load_manual("BETS-B.ST", directory=STORE)


def _record(parsed):
    return R.from_store(parsed, M.section5_basis(parsed),
                        growth=R.Growth(base=0.03, view_file="x.md"),
                        run_ts=datetime(2026, 10, 13, 21, 0))


def test_the_annual_net_stands_in_with_its_date(bets):
    basis = M.section5_basis(bets)
    assert M.stand_in(bets, basis, "net_interest_paid").value == pytest.approx(12.1)
    record = _record(bets)
    assert record.interest.net_interest_paid == pytest.approx(12.1)
    leg = next(i for i in record.inputs if i.name == "net_interest_paid")
    assert "STAND-IN (E135)" in leg.provenance
    assert "net interest paid (declaration 3)" not in " ".join(record.missing())


def test_without_the_flag_the_leg_is_still_missing(bets):
    annual = []
    for entry in bets.annual:
        figures = dict(entry.figures)
        figures["net_interest_paid"] = dataclasses.replace(
            figures["net_interest_paid"], stand_in=False)
        annual.append(dataclasses.replace(entry, figures=figures))
    plain = dataclasses.replace(bets, annual=tuple(annual))
    assert M.stand_in(plain, M.section5_basis(plain), "net_interest_paid") is None
    assert "net interest paid (declaration 3)" in " ".join(_record(plain).missing())


def test_stand_in_reaches_the_two_named_fields_only():
    with pytest.raises(M.ManualError, match="stand_in"):
        M._parse_stand_in({"stand_in": True}, "sbc", Path("X.yaml"), "annual")
    assert M._parse_stand_in({"stand_in": True}, "net_interest_paid",
                             Path("X.yaml"), "annual") is True
