"""B9/E30's organic carve-out, made reachable — 2026-09-01.

**THE DEFECT, MEASURED BEFORE IT WAS FIXED.** B9 was ruled on 2026-08-22 on
the UNA.AS case: reported turnover fell in four consecutive quarters (−4.6,
−3.5, −2.7, −3.3%) on a demerger and a currency move, while underlying sales
growth ran 3.0–5.8% throughout. The verdict recorded was **4.2.1 = NOT
TRIGGERED**.

`rules.revenue_decline_kill` implements that correctly and always has. What
did not exist was any way to get the figure in: `extract.py` never asked the
model for it, `earnings._yaml_block` emitted no line for it, and
`xbrl.as_quarter` cannot supply one because us-gaap tags no organic measure.
Every quarter on the watchlist — 37 of them across five names on 2026-09-01 —
carried `revenue_yoy_organic = None`, so `on_organic` was always False and
**B9's own case TRIPS a hard kill when run through the code that was written
to spare it.**

`test_B9s_own_case_trips_without_the_figure_and_is_spared_with_it` is that
measurement, kept as a test.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from vss import earnings as E
from vss import rules as R
from vss.config import VALID_SOURCES, parse_watchlist
from vss.extract import EXTRACTABLE_FIELDS, FORBIDDEN_FIELDS, SYSTEM_PROMPT

FIXTURE = Path("tests/fixtures/earnings/acme-q2-2026-extraction.json")

#: B9's own figures, FRAMEWORK-EDITS line 383.
UNA_REPORTED = [("2025-Q2", -0.046), ("2025-Q3", -0.035),
                ("2025-Q4", -0.027), ("2026-Q1", -0.033)]
UNA_ORGANIC = [0.030, 0.058, 0.041, 0.035]


def _q(period, yoy, organic=None):
    return R.Quarter(period=period, revenue_yoy=yoy,
                     revenue_yoy_organic=organic, basis="reported",
                     accounting="gaap", period_basis="calendar")


# --- the measurement, kept ------------------------------------------------


def test_B9s_own_case_trips_without_the_figure_and_is_spared_with_it():
    """**THE ONE THAT MATTERS.** The same four quarters, read twice."""
    without = R.revenue_decline_kill([_q(p, y) for p, y in UNA_REPORTED])
    assert without.state == R.TRIP, (
        "B9's own case must trip when no organic figure is on file -- that "
        "is the defect this whole change exists to close")
    assert "reported" in without.name

    with_it = R.revenue_decline_kill(
        [_q(p, y, o) for (p, y), o in zip(UNA_REPORTED, UNA_ORGANIC)])
    assert with_it.state == R.NO_TRIP
    assert "organic" in with_it.name


def test_the_mixed_window_still_refuses_under_E30():
    """A run counted partly on organic and partly on reported is not a run."""
    quarters = [_q(p, y, o) for (p, y), o in zip(UNA_REPORTED, UNA_ORGANIC)]
    quarters[2] = _q("2025-Q4", -0.027, None)
    result = R.revenue_decline_kill(quarters)
    assert result.state == R.CANNOT_EVALUATE
    assert "partly on organic and partly on reported" in result.detail


# --- the absence is SAID, not implied -------------------------------------


def test_a_kill_on_reported_revenue_says_the_carve_out_could_not_apply():
    """E30's visibility clause. Until now the only sign that the carve-out
    had not been reached was the word 'reported' in the verdict name."""
    result = R.revenue_decline_kill([_q(p, y) for p, y in UNA_REPORTED])
    assert result.state == R.TRIP
    assert "No organic figure is on file" in result.detail
    assert "B9's carve-out could not be applied" in result.detail
    assert "revenue_yoy_organic" in result.detail


def test_it_names_the_XBRL_route_as_structurally_unable_to_supply_one():
    """`as_quarter` records the absence as by-construction; this is where a
    reader of the VERDICT learns it, rather than a reader of the source."""
    result = R.revenue_decline_kill([_q(p, y) for p, y in UNA_REPORTED])
    assert "no us-gaap tag exists" in result.detail


def test_a_CANNOT_EVALUATE_on_reported_carries_it_too():
    quarters = [_q("2025-Q3", -0.03), _q("2025-Q4", None)]
    result = R.revenue_decline_kill(quarters)
    assert result.state == R.CANNOT_EVALUATE
    assert "B9's carve-out could not be applied" in result.detail


def test_a_verdict_struck_ON_organic_carries_no_such_note():
    """It did apply. Saying it could not would be false."""
    result = R.revenue_decline_kill(
        [_q(p, y, o) for (p, y), o in zip(UNA_REPORTED, UNA_ORGANIC)])
    assert "could not be applied" not in result.detail
    assert "no us-gaap tag" not in result.detail


def test_an_organic_decline_still_trips_and_says_reported_did_not_rescue_it():
    """The carve-out spares a reported decline; it does not spare a real
    one. JD.L's shape, unchanged."""
    quarters = [_q("2025-Q3", 0.02, -0.03), _q("2025-Q4", 0.01, -0.02)]
    result = R.revenue_decline_kill(quarters)
    assert result.state == R.TRIP
    assert "organic" in result.name
    assert "reported revenue GREW throughout" in result.detail


# --- the model is asked for it, and told never to invent it ---------------


def test_the_extraction_schema_asks_for_the_organic_figure():
    assert "revenue_yoy_organic" in EXTRACTABLE_FIELDS
    assert "revenue_yoy" in EXTRACTABLE_FIELDS, "the reported figure stays"


def test_consensus_is_still_forbidden():
    """The one field that may never be extracted, at any prompt."""
    assert FORBIDDEN_FIELDS == ("eps_consensus",)
    assert "eps_consensus" not in EXTRACTABLE_FIELDS


def test_the_prompt_says_ABSENT_NEVER_ZERO():
    """'The company disclosed no organic figure' and 'the company disclosed
    flat organic growth' are opposite facts and only one is ever true."""
    assert "never put 0" in SYSTEM_PROMPT
    assert "Do not\n   derive it" in SYSTEM_PROMPT
    assert "WHERE THE REPORT STATES NO SUCH FIGURE, THE VALUE IS null" in SYSTEM_PROMPT
    assert "an absent organic figure means the company did not" in SYSTEM_PROMPT


def test_the_prompt_exempts_the_organic_field_from_the_adjusted_rule():
    """Rule 5 tells the model to prefer the UNADJUSTED figure. Without an
    exemption it would suppress the very figure rule 4b asks for."""
    assert "DOES NOT APPLY" in SYSTEM_PROMPT
    assert "revenue_yoy_organic" in SYSTEM_PROMPT


def test_the_prompt_lists_it_as_a_FRACTION():
    assert "revenue_yoy_organic" in SYSTEM_PROMPT.split("FRACTIONS:")[1][:120]


def test_the_unit_band_for_it_already_existed():
    assert R.FRACTION_BANDS["revenue_yoy_organic"] == (-1.0, 1.0)


# --- it reaches the quarter and the block --------------------------------


class _Extraction:
    period = "2026-Q1"
    guidance_action = "maintained"
    basis = "reported"
    accounting = "gaap"
    period_basis = "calendar"

    def __init__(self, **figures):
        self.figures = figures


def test_the_organic_figure_reaches_the_provisional_quarter():
    quarter = E.provisional_quarter(
        _Extraction(revenue_yoy=-0.033, revenue_yoy_organic=0.041), "2026-Q1")
    assert quarter.revenue_yoy == -0.033
    assert quarter.revenue_yoy_organic == 0.041


def test_an_absent_organic_figure_stays_ABSENT_and_is_never_zeroed():
    quarter = E.provisional_quarter(_Extraction(revenue_yoy=-0.033), "2026-Q1")
    assert quarter.revenue_yoy_organic is None, (
        "a zero here would mean the company disclosed flat organic growth")


def test_the_block_emits_a_line_for_it_beside_the_reported_figure():
    lines = E._yaml_block(E.provisional_quarter(
        _Extraction(revenue_yoy=-0.033, revenue_yoy_organic=0.041), "2026-Q1"))
    assert "    revenue_yoy: -0.033" in lines
    assert "    revenue_yoy_organic: 0.041" in lines
    assert (lines.index("    revenue_yoy: -0.033")
            < lines.index("    revenue_yoy_organic: 0.041"))


def test_the_block_still_parses_under_the_current_watchlist_schema():
    """End to end: what the alert prints is what the loader accepts."""
    lines = E._yaml_block(E.provisional_quarter(
        _Extraction(revenue_yoy=-0.033, revenue_yoy_organic=0.041,
                    op_margin=0.12, revenue=1000.0), "2026-Q1"))
    document = yaml.safe_load(
        "tickers:\n  - ticker: T\n    name: T\n    currency: USD\n"
        "    status: HELD\n    fv_bull: 140.0\n    quarters:\n"
        + "\n".join("    " + line for line in lines))
    quarter = parse_watchlist(document)[0].quarters[0]
    assert quarter.revenue_yoy_organic == 0.041
    assert quarter.revenue_yoy == -0.033


def test_an_empty_organic_line_parses_as_absent():
    lines = E._yaml_block(E.provisional_quarter(
        _Extraction(revenue_yoy=-0.033), "2026-Q1"))
    assert "    revenue_yoy_organic: " in lines
    document = yaml.safe_load(
        "tickers:\n  - ticker: T\n    name: T\n    currency: USD\n"
        "    status: HELD\n    fv_bull: 140.0\n    quarters:\n"
        + "\n".join("    " + line for line in lines))
    assert parse_watchlist(document)[0].quarters[0].revenue_yoy_organic is None


# --- finding (b): the provenance the path already knew -------------------


def test_the_earnings_path_states_its_own_provenance():
    """It read a press release and knows it. It used to emit the field blank
    and leave the owner to supply from memory a value the tool had in hand."""
    quarter = E.provisional_quarter(_Extraction(revenue=1.0), "2026-Q1")
    assert quarter.source == "release"
    assert quarter.source in VALID_SOURCES
    assert "    source: release" in E._yaml_block(quarter)


def test_the_two_routes_now_agree_that_provenance_is_the_tools_job():
    """`xbrl.as_quarter` has always set `source="xbrl"` through the same
    renderer; the earnings half left it blank."""
    from vss.earnings import SOURCE_RELEASE

    assert SOURCE_RELEASE in VALID_SOURCES
    source = Path("vss/xbrl.py").read_text(encoding="utf-8")
    assert 'source="xbrl",' in source


def test_the_fixture_round_trips_with_both_new_fields():
    from vss.extract import parse_response

    extraction = parse_response(FIXTURE.read_text(encoding="utf-8"), "u", "m")
    quarter = E.provisional_quarter(extraction, extraction.period)
    lines = E._yaml_block(quarter)
    document = yaml.safe_load(
        "tickers:\n  - ticker: T\n    name: T\n    currency: USD\n"
        "    status: HELD\n    fv_bull: 140.0\n    quarters:\n"
        + "\n".join("    " + line for line in lines))
    parsed = parse_watchlist(document)[0].quarters[0]
    assert parsed.source == "release"
    assert parsed.revenue_yoy_organic is None      # the fixture states none
