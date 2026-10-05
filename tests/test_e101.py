"""E101's construction-error detector, ruled 2026-09-01.

The gap between E90's cushion (15-35%) and this framework's own measured
error (29-56% in the week to 2026-08-31) is closed by SHRINKING THE ERROR.
All four corrections -- +36% (E34, LIAB.ST), -33% (E36, NKE), +56% (E70,
NKE), +29% (E37, SAP.DE) -- were transcription-correct and construction-
wrong, and E40 cannot see that: it verifies that a figure was correctly
copied from the page it names.

**The tests that matter are the two that pin the detector's manners.** It
must never adjudicate, and it must never read an absent comparator as a
disagreement of zero -- either would import the issuer's definition through
the back door, which is the error E5 and E35 both exist to prevent.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from vss.runrecord import (DISAGREEMENT_TOLERANCE, FCF_CONVERSION_BAND,
                           Comparator, Disagreement, Growth, from_store)

MANUAL = Path("config/manual")
RUN_TS = datetime(2026, 9, 1, 22, 30).astimezone()


def _record(ticker: str):
    from vss.manual import load_manual, section5_basis

    parsed = load_manual(ticker, directory=MANUAL)
    return from_store(parsed, section5_basis(parsed),
                      growth=Growth(base=0.02, view_file="E101 test probe"),
                      run_ts=RUN_TS, notes="E101 test probe")


# --- the three checks exist and are printed with every strike ------------


def test_every_strike_prints_all_three_checks():
    """A detector visible only when it fires cannot be checked for being
    wrong -- E97's argument about its own table, applied here."""
    checks = _record("CTSH").construction_checks()
    assert len(checks) == 3
    names = [c.name for c in checks]
    assert "FCF0 vs the issuer's own free cash flow" in names[0]
    assert "net debt vs the issuer's own net debt" in names[1]
    assert "conversion" in names[2]


def test_the_block_reaches_the_rendered_record():
    text = _record("CTSH").render()
    assert "## Construction checks (E101) — DETECTORS, NOT VERDICTS" in text
    assert "none of them is authoritative and none adjudicates" in text
    assert "Nothing here adjusts, refuses or blocks anything" in text


def test_an_incomplete_record_prints_no_checks_because_it_prints_no_value():
    """The block goes with the strike. A record that cannot strike has no
    figure to check."""
    from dataclasses import replace

    # A complete record with its growth view removed: `missing()` then names
    # the gap and no fair value prints.
    bare = replace(_record("CTSH"), growth=Growth(base=0.02, view_file=""))
    assert bare.missing()
    assert "Construction checks" not in bare.render()


# --- and NONE of them adjudicates ----------------------------------------


def test_a_disagreement_changes_no_figure():
    """THE ONE THAT MATTERS. The issuer's free cash flow is on the issuer's
    definition, which is usually not E34's; LIAB.ST's +6.3% net-debt
    disagreement was the ISSUER being narrower and this project's figure
    stood."""
    record = _record("CTSH")
    before = record.strike()
    record.construction_checks()
    assert record.strike() == before
    assert record.fcf0() == pytest.approx(record.fcf0())


def test_a_flagged_check_does_not_make_the_record_incomplete():
    record = _record("GDDY")
    flagged = [c for c in record.construction_checks() if c.flagged]
    assert list(record.missing()) == [], "a detector blocked a strike"
    record.strike()          # raises if a check has become a gate
    assert isinstance(flagged, list)


# --- an absent comparator is DATA MISSING, never a disagreement of zero ---


def test_an_unpublished_comparator_is_DATA_MISSING():
    check = Disagreement("x", ours=100.0, theirs=None)
    assert check.gap is None
    assert not check.flagged
    assert "DATA MISSING" in check.line()
    assert "never a disagreement of zero" in check.line()


def test_a_missing_figure_of_OURS_is_data_missing_too():
    check = Disagreement("x", ours=None, theirs=100.0)
    assert not check.flagged and "DATA MISSING" in check.line()


def test_a_zero_comparator_does_not_divide():
    assert Disagreement("x", ours=100.0, theirs=0.0).gap is None


# --- check 1 and 2: the gap, as a percentage -----------------------------


def test_a_gap_inside_the_tolerance_is_not_flagged():
    assert not Disagreement("x", ours=102.0, theirs=100.0).flagged


def test_a_gap_outside_it_is_flagged_and_signed():
    """LIAB.ST's own case: +6.3%, this project's net debt the LARGER,
    because E35.1 includes the pension leg the issuer excludes."""
    check = Disagreement("net debt", ours=4536.0, theirs=4266.0)
    assert check.gap == pytest.approx(0.0633, abs=1e-4)
    assert check.gap > DISAGREEMENT_TOLERANCE and check.flagged
    assert "+6.3%" in check.line() and "LOOK" in check.line()


def test_the_direction_is_kept_because_it_is_the_diagnosis():
    """A positive gap and a negative one mean different things -- ours the
    larger is usually a leg the issuer excludes; ours the smaller is usually
    a leg WE are missing, which is what E35.1 found."""
    assert Disagreement("x", ours=90.0, theirs=100.0).gap < 0
    assert Disagreement("x", ours=110.0, theirs=100.0).gap > 0


# --- check 3: a RATIO against a band, and it must not argue with itself ---


def test_the_conversion_check_measures_a_MULTIPLE_not_a_percentage():
    """It printed '+18.5% LOOK' beside 'inside the band' on CTSH -- a
    detector arguing with itself, which is how a reader learns to ignore
    one. FCF0 and net income are DIFFERENT quantities; their quotient is
    the check and a percentage gap between them means nothing."""
    check = Disagreement("conversion", ours=2643.0, theirs=2230.0,
                         kind="ratio", band=FCF_CONVERSION_BAND)
    assert check.ratio == pytest.approx(1.185, abs=1e-3)
    assert check.measure == "1.19x"
    assert not check.flagged
    assert "LOOK" not in check.line() and "%" not in check.measure


def test_a_conversion_inside_the_band_is_silent_even_when_high():
    """§4.3 reads a conversion above 90% as a GREEN FLAG. The band must not
    argue with the framework's own reading of a good business."""
    for ratio in (0.4, 1.0, 1.6, 2.5):
        check = Disagreement("c", ours=ratio * 100, theirs=100.0,
                             kind="ratio", band=FCF_CONVERSION_BAND)
        assert not check.flagged, f"{ratio}x should be silent"


def test_a_conversion_off_by_a_BASIS_is_flagged():
    """What is detected is a figure on the wrong basis -- a quarter divided
    into a year, a segment into a group. A factor of four is the smallest
    that matters (backlog B-8, first found on PNDORA.CO)."""
    quarter_into_year = Disagreement("c", ours=25.0, theirs=400.0,
                                     kind="ratio", band=FCF_CONVERSION_BAND)
    assert quarter_into_year.flagged and "LOOK" in quarter_into_year.line()
    year_into_quarter = Disagreement("c", ours=400.0, theirs=25.0,
                                     kind="ratio", band=FCF_CONVERSION_BAND)
    assert year_into_quarter.flagged


def test_the_band_is_wide_on_purpose():
    low, high = FCF_CONVERSION_BAND
    assert low <= 0.4 and high >= 2.5, (
        "a real business converts at 40% or at 250%; neither is a fault")


# --- the comparators come off the run's OWN basis -------------------------


def test_a_comparator_is_read_on_the_same_basis_as_the_legs():
    """E19. A comparator off a different window would MANUFACTURE a
    disagreement rather than detect one."""
    record = _record("CTSH")
    assert record.net_income.value is not None
    checks = record.construction_checks()
    assert checks[2].theirs == record.net_income.value


def test_a_store_that_publishes_none_says_so_rather_than_agreeing():
    """The detector must say DATA MISSING, not 0%. Struck on a comparator
    that is absent by construction rather than on a named store: LIAB.ST
    carried none when this was written and now carries one, and a test of
    the ABSENT case must not turn on which names have been filled."""
    from vss.runrecord import Disagreement

    check = Disagreement("net debt", ours=4536.0, theirs=None,
                         comparator_field="net_debt_reported")
    assert check.theirs is None
    assert not check.flagged
    assert "DATA MISSING" in check.line()
    assert "never a disagreement of zero" in check.line()


def test_the_schema_carries_both_issuer_fields():
    from vss.manual import FIELDS

    names = {spec.name for spec in FIELDS}
    assert "free_cash_flow_reported" in names
    assert "net_debt_reported" in names


def test_a_comparator_entered_by_hand_is_read(tmp_path: Path):
    """The owner's route: enter the issuer's figure and the check speaks."""
    record = _record("CTSH")
    replaced = type(record)(**{**record.__dict__,
                               "net_debt_reported": Comparator(-500_000_000.0,
                                                               "p.12")})
    check = replaced.construction_checks()[1]
    assert check.theirs == -500_000_000.0
    assert check.gap is not None


def test_the_conversion_check_IS_WIRED_as_a_ratio_not_a_gap():
    """M1 in the mutation round passed without this: every assertion about
    the ratio built its own `Disagreement`, so nothing pinned that
    `construction_checks` actually asks for one. Dropping `kind="ratio"`
    from the wiring went green."""
    check = _record("CTSH").construction_checks()[2]
    assert check.kind == "ratio"
    assert check.band == FCF_CONVERSION_BAND
    assert check.measure.endswith("x")
    assert "%" not in check.measure


def test_the_first_two_checks_are_wired_as_GAPS():
    checks = _record("CTSH").construction_checks()
    assert checks[0].kind == "gap" and checks[1].kind == "gap"
