"""The two PRINTED columns: EBIT and free cash flow against their own
five-year medians (2026-09-04).

The property these tests exist to hold is the one the module's docstring
opens with: **PRINTED, NEVER FILTERED.** Nothing here may reach a gate.
"""

from __future__ import annotations

import ast
from datetime import date
from pathlib import Path

import pytest

from vss import medians as MD


def points(*pairs):
    return [(date(y, 12, 31), float(v)) for y, v in pairs]


def test_the_ratio_is_the_newest_year_over_the_median_OF_FIVE_INCLUDING_IT():
    """The numerator is INSIDE the median on purpose: the question is
    whether this year stands out among the last five, and excluding it
    would move the denominator every time the newest year moved."""
    got = MD.ratio_of(points((2021, 100), (2022, 110), (2023, 90),
                             (2024, 105), (2025, 200)),
                      source=MD.SOURCE_VENDOR, leg="EBIT")
    assert got.median == 105 and got.newest == 200
    assert got.ratio == pytest.approx(200 / 105)
    assert got.years == (2021, 2022, 2023, 2024, 2025)


def test_only_the_newest_five_years_are_taken():
    got = MD.ratio_of(points((2016, 1), (2017, 1), (2018, 1),
                             (2021, 100), (2022, 110), (2023, 90),
                             (2024, 105), (2025, 200)),
                      source=MD.SOURCE_VENDOR, leg="EBIT")
    assert got.years == (2021, 2022, 2023, 2024, 2025)


def test_a_year_filed_twice_is_ONE_year_and_the_later_dated_point_wins():
    """A restatement is not a second observation."""
    got = MD.ratio_of([(date(2025, 6, 30), 50.0), (date(2025, 12, 31), 60.0),
                       (date(2024, 12, 31), 40.0), (date(2023, 12, 31), 30.0)],
                      source=MD.SOURCE_VENDOR, leg="EBIT")
    assert got.years == (2023, 2024, 2025) and got.newest == 60.0


def test_fewer_than_three_years_is_NOT_a_median_and_says_how_many_it_found():
    got = MD.ratio_of(points((2024, 10), (2025, 12)),
                      source=MD.SOURCE_VENDOR, leg="EBIT")
    assert got.ratio is None and "2 annual EBIT observation(s)" in got.note
    assert got.provenance().startswith("DATA MISSING -- ")


@pytest.mark.parametrize("median_year_values, why", [
    ([(2023, -10), (2024, -20), (2025, 5)], "negative"),
    ([(2023, 0), (2024, -1), (2025, 5)], "zero"),
])
def test_a_median_that_is_not_positive_prints_no_ratio(median_year_values, why):
    """A ratio against zero is undefined; against a negative it INVERTS its
    own ordering -- a loss shrinking would read as a rise."""
    del why
    got = MD.ratio_of(points(*median_year_values),
                      source=MD.SOURCE_VENDOR, leg="EBIT")
    assert got.ratio is None and got.median is not None
    assert "not positive" in got.note and "E25" in got.note


# --- the three sources ----------------------------------------------------


def _facts(**elements):
    return {"facts": {"us-gaap": {
        tag: {"units": {"USD": [
            {"start": f"{y}-01-01", "end": f"{y}-12-31", "val": v,
             "form": "10-K"} for y, v in rows]}}
        for tag, rows in elements.items()}}}


def test_the_SEC_route_reads_ANNUAL_facts_only_and_never_a_quarter():
    document = {"facts": {"us-gaap": {"OperatingIncomeLoss": {"units": {"USD": [
        {"start": "2023-01-01", "end": "2023-12-31", "val": 100, "form": "10-K"},
        {"start": "2024-01-01", "end": "2024-12-31", "val": 110, "form": "10-K"},
        {"start": "2025-01-01", "end": "2025-12-31", "val": 300, "form": "10-K"},
        # a QUARTER of the same year, which must not become a fourth point
        {"start": "2025-10-01", "end": "2025-12-31", "val": 90, "form": "10-Q"},
    ]}}}}}
    ebit, _ = MD.from_sec(document)
    assert ebit.years == (2023, 2024, 2025) and ebit.newest == 300


def test_the_SEC_route_builds_free_cash_flow_from_the_TWO_tags_a_filer_HAS():
    """There is no free cash flow element in any taxonomy -- it is a
    non-GAAP APM -- so the leg is OCF less capex or it is DATA MISSING."""
    document = _facts(
        NetCashProvidedByUsedInOperatingActivities=[
            (2023, 1000), (2024, 1100), (2025, 1200)],
        PaymentsToAcquirePropertyPlantAndEquipment=[
            (2023, 100), (2024, 100), (2025, 200)])
    _, fcf = MD.from_sec(document)
    assert fcf.newest == 1000 and fcf.median == 1000
    assert fcf.source == MD.SOURCE_SEC


def test_the_SEC_route_names_WHICH_leg_is_absent_rather_than_going_quiet():
    document = _facts(NetCashProvidedByUsedInOperatingActivities=[
        (2023, 1000), (2024, 1100), (2025, 1200)])
    _, fcf = MD.from_sec(document)
    assert fcf.ratio is None and "capital expenditure" in fcf.note
    document = _facts(PaymentsToAcquirePropertyPlantAndEquipment=[
        (2023, 100), (2024, 100), (2025, 200)])
    _, fcf = MD.from_sec(document)
    assert fcf.ratio is None and "operating cash flow" in fcf.note


def test_a_filer_that_tags_NO_operating_income_element_says_which_it_looked_for():
    """NVR's shape: pre-tax income only. A pre-tax element is NOT read in
    an operating line's place -- it is a different quantity."""
    ebit, _ = MD.from_sec(_facts(
        IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic=[
            (2023, 1), (2024, 2), (2025, 3)]))
    assert ebit.ratio is None
    assert "OperatingIncomeLoss" in ebit.note and "different quantity" in ebit.note


def test_EACH_LEG_takes_the_first_source_that_answers_IT():
    """A filer may tag its operating income and not its capex. Settling
    both legs from whichever source answered first would throw away an
    EBIT history that was there."""
    class _Vendor:
        def annual_series(self, *aliases):
            del aliases
            return points((2023, 10), (2024, 20), (2025, 30))
    ebit, fcf = MD.medians_for(
        "X", fundamentals=_Vendor(),
        facts=lambda: _facts(OperatingIncomeLoss=[
            (2023, 100), (2024, 110), (2025, 300)]))
    assert ebit.source == MD.SOURCE_SEC and ebit.newest == 300
    # the vendor has no cash flow rows, so the FCF leg keeps the SEC note
    assert fcf.ratio is None


def test_a_source_that_RAISES_is_that_names_note_and_never_the_runs():
    def boom():
        raise RuntimeError("EDGAR said no")
    ebit, fcf = MD.medians_for("X", facts=boom)
    assert ebit.ratio is None and "EDGAR said no" in ebit.note
    assert fcf.ratio is None


def test_the_columns_reach_NO_gate_no_kill_and_no_ranking_key():
    """PRINTED, NEVER FILTERED -- held by search over the source, not by
    inspection. `vss/screen.py` may name the module (it writes the CSV);
    nothing that decides anything may."""
    root = Path(__file__).resolve().parent.parent / "vss"
    allowed = {"medians.py", "screen.py"}
    for path in sorted(root.glob("*.py")):
        if path.name in allowed:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # CODE, not prose: a comment saying which module reads a stored
        # line is exactly the provenance this repo wants, and must not be
        # what this test trips on.
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, ast.alias):
                names.add(node.name.split(".")[-1])
                if node.asname:
                    names.add(node.asname)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[-1])
        # `median_turnover_major` predates this module and is filter 1's
        # liquidity leg -- a different median entirely. What must be absent
        # is THIS module and THESE columns.
        forbidden = {"medians", "medians_for", "MedianRatio", "from_sec",
                     "from_vendor", "from_manual", "ratio_of",
                     "five_year_medians", "ebit_vs_5y_median",
                     "fcf_vs_5y_median"}
        assert not (names & forbidden), (path.name, sorted(names & forbidden))
    # and inside screen.py it is only ever written into a row
    screen = (root / "screen.py").read_text(encoding="utf-8")
    tree = ast.parse(screen)
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) or isinstance(node, ast.If):
            segment = ast.get_source_segment(screen, node) or ""
            assert "vs_5y_median" not in segment, segment[:120]
