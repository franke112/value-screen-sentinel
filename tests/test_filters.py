"""Filter step 0 (the exclusion list) and filter 1 (the dislocation band).

The acceptance test lives at the bottom. It runs filter 1 DIRECTLY, not the
chain, because SAP.DE is on the exclusion list and the chain would remove it
before the filter ever saw it.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest

from vss import snapshot as store
from vss.filters import (
    EXCLUSION_SCHEMA,
    STEP_DISLOCATION,
    STEP_SERIES_SANITY,
    STEP_EXCLUSION_LIST,
    STEP_PRICE_COVERAGE,
    STEP_LISTING_AGE,
    CircleError,
    Exclusion,
    ExclusionError,
    apply_circle_of_competence,
    apply_exclusions,
    b1_metric,
    load_circle_of_competence,
    load_exclusions,
    run_filter1,
)
from vss.metrics import compute
from vss.rules import DISLOCATION_MAX, DISLOCATION_MIN, in_dislocation_band
from vss.universe import ON_MISSING, ON_VALUE, Instrument, SCHEMA, Tally
from tests._vendor_data import need

FIXTURE_PRICES = (
    Path(__file__).resolve().parent / "fixtures" / "verdict-matrix" / "prices"
)
ROOT = Path(__file__).resolve().parents[1]


def instrument(ticker: str, **kw) -> Instrument:
    base = dict(
        ticker_yahoo=ticker, ticker_lokal=ticker.split(".")[0], isin=None,
        namn=f"{ticker} AB", marknad="Stockholm", tier="A", listdatum=None,
        valuta="SEK", instrumenttyp="Equity",
    )
    base.update(kw)
    return Instrument(**base)


def series(closes, last: date = date(2026, 8, 21)) -> pd.DataFrame:
    days = len(closes)
    index = pd.to_datetime([last - pd.Timedelta(days=days - 1 - i) for i in range(days)])
    return pd.DataFrame(
        {"Open": closes, "High": closes, "Low": closes, "Close": closes,
         "Volume": [1000.0] * days},
        index=index,
    )


def read_fixture(ticker: str) -> pd.DataFrame:
    need(FIXTURE_PRICES / f"{ticker}.csv")
    frame = pd.read_csv(FIXTURE_PRICES / f"{ticker}.csv", index_col=0)
    frame.index = pd.DatetimeIndex(
        [pd.Timestamp(v).tz_localize(None) if pd.Timestamp(v).tzinfo else pd.Timestamp(v)
         for v in frame.index]
    )
    return frame


def write_exclusions(path: Path, rows) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(EXCLUSION_SCHEMA)
        writer.writerows(rows)
    return path


GOOD_ROW = ["SAP.DE", "HELD", "2026-08-22", "Held position."]


# --- the exclusion list: loading ------------------------------------------


def test_a_well_formed_list_loads(tmp_path: Path):
    path = write_exclusions(tmp_path / "e.csv", [GOOD_ROW])
    (entry,) = load_exclusions(path)
    assert entry.ticker_yahoo == "SAP.DE"
    assert entry.skal == "HELD"
    assert entry.datum == date(2026, 8, 22)
    assert entry.source_line == 2


def test_a_wrong_header_is_rejected(tmp_path: Path):
    path = tmp_path / "e.csv"
    path.write_text("ticker,reason,date,source\n", encoding="utf-8")
    with pytest.raises(ExclusionError, match="header is"):
        load_exclusions(path)


@pytest.mark.parametrize("index", range(4))
def test_every_column_is_required(tmp_path: Path, index: int):
    row = list(GOOD_ROW)
    row[index] = ""
    path = write_exclusions(tmp_path / "e.csv", [row])
    with pytest.raises(ExclusionError, match="is empty and is required"):
        load_exclusions(path)


def test_a_bad_date_is_a_hard_error(tmp_path: Path):
    path = write_exclusions(tmp_path / "e.csv", [["X.ST", "HELD", "22/08/2026", "why"]])
    with pytest.raises(ExclusionError, match="datum"):
        load_exclusions(path)


def test_a_short_row_is_a_hard_error(tmp_path: Path):
    path = tmp_path / "e.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(EXCLUSION_SCHEMA)
        writer.writerow(["X.ST", "HELD"])
    with pytest.raises(ExclusionError, match="has 2 fields"):
        load_exclusions(path)


def test_one_name_one_reason(tmp_path: Path):
    path = write_exclusions(
        tmp_path / "e.csv",
        [["X.ST", "HELD", "2026-08-22", "a"], ["X.ST", "DROPPED", "2026-08-22", "b"]],
    )
    with pytest.raises(ExclusionError, match="already excluded on line 2"):
        load_exclusions(path)


def test_skal_is_free_text_and_not_validated(tmp_path: Path):
    """The reasons are the owner's. A new one must not need a code change."""
    path = write_exclusions(
        tmp_path / "e.csv", [["X.ST", "vantar pa rapport", "2026-08-22", "why"]]
    )
    (entry,) = load_exclusions(path)
    assert entry.skal == "vantar pa rapport"


def test_a_missing_list_is_an_error(tmp_path: Path):
    with pytest.raises(ExclusionError, match="no such exclusion list"):
        load_exclusions(tmp_path / "nope.csv")


# --- the exclusion list: applying -----------------------------------------


def test_excluded_names_are_removed_and_counted_on_value():
    instruments = [instrument("SAP.DE"), instrument("VOLV-B.ST"), instrument("AAK.ST")]
    exclusions = [Exclusion("SAP.DE", "HELD", date(2026, 8, 22), "held")]
    kept, rejections, tally, unmatched = apply_exclusions(instruments, exclusions)

    assert [i.ticker_yahoo for i in kept] == ["VOLV-B.ST", "AAK.ST"]
    assert tally.step == STEP_EXCLUSION_LIST
    assert tally.count_in == 3 and tally.count_out == 2
    # A recorded, dated decision is a VALUE, not missing data.
    assert tally.rejected_on_value == 1
    assert tally.rejected_on_missing == 0
    assert rejections[0].kind == ON_VALUE
    assert "HELD since 2026-08-22" in rejections[0].reason
    assert unmatched == []


def test_the_reason_is_carried_into_the_tally_so_it_can_be_grouped():
    instruments = [instrument("A.ST"), instrument("B.ST"), instrument("C.ST")]
    exclusions = [
        Exclusion("A.ST", "HELD", date(2026, 8, 22), "x"),
        Exclusion("B.ST", "DROPPED", date(2026, 8, 22), "y"),
        Exclusion("C.ST", "DROPPED", date(2026, 8, 22), "z"),
    ]
    _, _, tally, _ = apply_exclusions(instruments, exclusions)
    assert tally.reasons["value:HELD"] == 1
    assert tally.reasons["value:DROPPED"] == 2


def test_an_entry_matching_nothing_is_reported_as_inert():
    """An inert entry that reads as active is how a name quietly comes back."""
    instruments = [instrument("SAP.DE")]
    exclusions = [
        Exclusion("SAP.DE", "HELD", date(2026, 8, 22), "held"),
        Exclusion("UNA.AS", "SELLING", date(2026, 8, 22), "selling Monday"),
    ]
    kept, _, _, unmatched = apply_exclusions(instruments, exclusions)
    assert kept == []
    assert [e.ticker_yahoo for e in unmatched] == ["UNA.AS"]


def test_matching_is_on_ticker_never_on_name():
    instruments = [instrument("ULVR.L", namn="UNILEVER PLC", marknad="London")]
    exclusions = [Exclusion("UNA.AS", "SELLING", date(2026, 8, 22), "same company")]
    kept, _, tally, unmatched = apply_exclusions(instruments, exclusions)
    assert [i.ticker_yahoo for i in kept] == ["ULVR.L"]
    assert tally.rejected == 0
    assert len(unmatched) == 1


def test_an_empty_exclusion_list_removes_nothing():
    instruments = [instrument("A.ST"), instrument("B.ST")]
    kept, rejections, tally, unmatched = apply_exclusions(instruments, [])
    assert len(kept) == 2 and rejections == [] and tally.rejected == 0


# --- filter 1 --------------------------------------------------------------


def flat_then_drop(high: float, low: float, days: int = 2000,
                   over: int = 20) -> pd.DataFrame:
    """A series that peaks early and sits at ``low`` at the end.

    The decline is spread over ``over`` sessions rather than taken in one
    step. A one-session cliff from 100 to 50 is what the K4 sanity check is
    built to refuse, so a fixture shaped that way would be testing the band
    against a series the screener has decided it cannot measure.

    ``days`` is CALENDAR days, one row each, and defaults to 2000 -- past
    E52's five-year listing-age floor. It was 400 until 2026-08-27, which
    is now short of that floor, so every band fixture was rejected before
    the band was reached. A fixture testing the BAND must clear the steps
    above it; a fixture testing E52 passes a smaller number on purpose.
    """
    # The peak must sit INSIDE the trailing 365 days or `high_52w` never
    # sees it: with days=2000 a peak at the midpoint would be three years
    # old. So the series is flat at ``high`` for its whole life, ramps down
    # near the END, and sits at ``low`` for the last ``tail`` rows. The one
    # break in it is the ramp, which is what the K4 check tolerates.
    tail = 120
    ramp = [high + (low - high) * (i + 1) / over for i in range(over)]
    closes = [high] * (days - over - tail) + ramp + [low] * tail
    return series(closes)


def test_a_name_inside_the_band_becomes_a_candidate():
    frames = {"A.ST": flat_then_drop(100.0, 75.0)}      # 25% off the high
    result = run_filter1([instrument("A.ST")], frames, date(2026, 8, 21))
    assert [c.ticker for c in result.candidates] == ["A.ST"]
    assert result.candidates[0].drawdown == pytest.approx(0.25)


def test_an_unmeasurable_series_is_rejected_ON_MISSING_never_on_value():
    """K4. The name did not fail the band -- the band could not be evaluated.

    Putting it in the value column would say the market did something it did
    not do. The series here halves and comes straight back, which is two
    scales in one column rather than a price.
    """
    # Halves, comes straight back to the scale it left, then declines
    # ordinarily to 22% off the high -- squarely inside the band.
    ramp = [100.0 - 22.0 * (i + 1) / 20 for i in range(20)]
    # 1800 rows before the break, so the series clears E52's five-year floor
    # and the K4 check is what removes it rather than its length.
    closes = ([100.0] * 1800 + [50.0] * 5 + [100.0] * 100 + ramp + [78.0] * 75)
    result = run_filter1([instrument("A.ST")], {"A.ST": series(closes)},
                         date(2026, 8, 21))
    assert result.candidates == []
    sanity = {t.step: t for t in result.tallies}[STEP_SERIES_SANITY]
    assert sanity.rejected_on_missing == 1
    assert sanity.rejected_on_value == 0
    band = {t.step: t for t in result.tallies}[STEP_DISLOCATION]
    assert band.count_in == 0, "an unmeasurable series reached the band anyway"
    (ticker, finding), = result.unmeasurable
    assert ticker == "A.ST" and "scale" in finding.kind


def test_the_unmeasurable_name_would_otherwise_have_been_a_candidate():
    """Without the halving-and-back the same shape passes, so the test above
    is measuring the check and not some other rejection."""
    ramp = [100.0 - 22.0 * (i + 1) / 20 for i in range(20)]
    closes = [100.0] * 1905 + ramp + [78.0] * 75
    result = run_filter1([instrument("A.ST")], {"A.ST": series(closes)},
                         date(2026, 8, 21))
    assert [c.ticker for c in result.candidates] == ["A.ST"]


def test_a_shallow_decline_is_rejected_on_a_value():
    frames = {"A.ST": flat_then_drop(100.0, 95.0)}      # 5% off
    result = run_filter1([instrument("A.ST")], frames, date(2026, 8, 21))
    assert result.candidates == []
    band = {t.step: t for t in result.tallies}[STEP_DISLOCATION]
    assert band.rejected_on_value == 1
    assert band.rejected_on_missing == 0


def test_a_collapse_beyond_the_band_is_rejected_too():
    frames = {"A.ST": flat_then_drop(100.0, 40.0)}      # 60% off
    result = run_filter1([instrument("A.ST")], frames, date(2026, 8, 21))
    assert result.candidates == []


def test_both_bounds_are_inclusive_through_the_imported_predicate():
    for low in (85.0, 50.0):                            # exactly 15% and 50%
        frames = {"A.ST": flat_then_drop(100.0, low)}
        result = run_filter1([instrument("A.ST")], frames, date(2026, 8, 21))
        assert [c.ticker for c in result.candidates] == ["A.ST"], low


def test_no_series_is_rejected_on_missing_data_not_on_a_value():
    result = run_filter1([instrument("A.ST")], {}, date(2026, 8, 21))
    coverage = {t.step: t for t in result.tallies}[STEP_PRICE_COVERAGE]
    assert coverage.rejected_on_missing == 1
    assert coverage.rejected_on_value == 0
    assert result.rejections[0].kind == ON_MISSING


def test_a_series_that_starts_after_the_run_date_is_missing_not_failing():
    frames = {"A.ST": series([100.0] * 30, last=date(2026, 8, 21))}
    result = run_filter1([instrument("A.ST")], frames, date(2026, 1, 1))
    coverage = {t.step: t for t in result.tallies}[STEP_PRICE_COVERAGE]
    assert coverage.rejected_on_missing == 1
    assert result.candidates == []


def test_a_stale_series_is_rejected_on_a_value():
    frames = {"A.ST": flat_then_drop(100.0, 75.0)}
    result = run_filter1([instrument("A.ST")], frames, date(2026, 9, 30))
    coverage = {t.step: t for t in result.tallies}[STEP_PRICE_COVERAGE]
    assert coverage.rejected_on_value == 1
    assert coverage.rejected_on_missing == 0


def test_a_single_close_is_DATA_MISSING_not_a_drawdown_of_zero():
    """RE-RULED TWICE, and the rejection has moved a step earlier each time.

    It was `..._is_its_own_52_week_high_and_fails_on_a_value`: one close made
    a 52-week high of itself, the drawdown computed to 0.0, and the name was
    rejected on a VALUE -- as though the market had been measured. REVIEW-4
    (report B 7.2) made that DATA MISSING at the dislocation step. E52 now
    removes it a step earlier still, at the listing-age floor, because one
    row does not reach five years back either.

    THE COLUMN IS WHAT THIS TEST IS ABOUT and it has never changed: missing,
    never value. Which step owns the rejection is the part E52 moved.
    """
    frames = {"A.ST": pd.DataFrame(
        {"Close": [100.0], "Volume": [1.0]},
        index=pd.to_datetime([date(2026, 8, 21)]),
    )}
    result = run_filter1([instrument("A.ST")], frames, date(2026, 8, 21))
    assert result.candidates == []
    tallies = {t.step: t for t in result.tallies}
    age = tallies[STEP_LISTING_AGE]
    assert age.rejected_on_value == 0
    assert age.rejected_on_missing == 1
    # And the band never saw it, so it cannot have failed there on a value.
    assert tallies[STEP_DISLOCATION].count_in == 0


def test_a_fresh_close_says_nothing_about_how_far_back_the_series_reaches():
    """RE-RULED after REVIEW-4 (report B 7.2), then again by E52.

    The original invariant -- that the dislocation step CANNOT report missing
    data -- was false: a FRESH close says nothing about how far BACK a series
    reaches, and the maximum of a short one is not a 52-week high. REVIEW-4
    moved `D.ST` into the band's missing column. E52 now takes it one step
    earlier, at the listing-age floor, and the CLAIM the test makes is
    unchanged: a short series is missing data, and it is never a failed band.
    """
    frames = {
        "A.ST": flat_then_drop(100.0, 75.0),
        "B.ST": flat_then_drop(100.0, 99.0),
        "C.ST": flat_then_drop(100.0, 10.0),
        "D.ST": series([100.0] * 5),
    }
    instruments = [instrument(t) for t in ("A.ST", "B.ST", "C.ST", "D.ST", "E.ST")]
    result = run_filter1(instruments, frames, date(2026, 8, 21))
    tallies = {t.step: t for t in result.tallies}
    assert tallies[STEP_LISTING_AGE].rejected_on_missing == 1    # D.ST, 5 rows
    assert tallies[STEP_LISTING_AGE].rejected_on_value == 0
    assert tallies[STEP_DISLOCATION].rejected_on_value == 2      # B.ST and C.ST
    assert tallies[STEP_PRICE_COVERAGE].rejected_on_missing == 1   # E.ST, no series
    reason, = {r.reason for r in result.rejections
               if r.step == STEP_LISTING_AGE and r.kind == ON_MISSING}
    assert "5-year floor" in reason and "2021-08-21" in reason


def test_e52_subsumes_the_52_week_bar_in_one_direction_only():
    """E52 vs the coverage bar: same axis, longer demand, and the bar stays.

    Three years of history clears `covers_52_weeks` and fails E52 -- so the
    two rules are NOT the same rule, and E52 is the stricter one. Going the
    other way, nothing that fails the bar can pass E52, which is why the
    `series does not cover 52 weeks` branch in `run_filter1` is unreachable
    from the screener. It is kept anyway: reachability is a property of
    E52's constant, not of the code.
    """
    from vss import metrics as M

    as_of = date(2026, 8, 21)
    three_years = date(2023, 8, 21)
    assert M.covers_52_weeks(three_years, as_of) is True
    assert M.covers_listing_age(three_years, as_of) is False
    # Nothing can fail the bar and pass E52.
    assert M.listing_age_start(as_of) < M.coverage_start(as_of)

    # And a three-year series is removed at the listing-age step, not the band.
    frames = {"A.ST": flat_then_drop(100.0, 75.0, days=1100)}
    result = run_filter1([instrument("A.ST")], frames, as_of)
    tallies = {t.step: t for t in result.tallies}
    assert result.candidates == []
    assert tallies[STEP_LISTING_AGE].rejected_on_missing == 1
    assert tallies[STEP_DISLOCATION].count_in == 0

    # The bar itself still does its own job inside metrics.compute, which
    # `vss run` reaches without passing filter 1 at all.
    short = series([100.0] * 200)
    assert M.compute(short, as_of).high_52w is None


def test_filter1_does_not_know_the_exclusion_list_exists():
    """Structural: the acceptance test depends on this separation.

    Checked on the parsed function, not the text, so the docstring may
    explain the separation without breaking the assertion about the code.
    """
    import ast

    source = (ROOT / "vss" / "filters.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    (func,) = [n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "run_filter1"]
    names = {n.id for n in ast.walk(func) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(func) if isinstance(n, ast.Attribute)}
    for forbidden in ("apply_exclusions", "load_exclusions", "Exclusion",
                      "exclusions", "EXCLUSIONS_PATH"):
        assert forbidden not in names, f"run_filter1 touches {forbidden}"


def test_rsi_and_sma_are_carried_but_never_decide():
    frames = {"A.ST": flat_then_drop(100.0, 75.0)}
    result = run_filter1([instrument("A.ST")], frames, date(2026, 8, 21))
    candidate = result.candidates[0]
    assert candidate.rsi14 is not None
    assert candidate.sma50 is not None
    assert candidate.pct_vs_sma50 is not None
    source = (ROOT / "vss" / "filters.py").read_text(encoding="utf-8")
    body = source[source.index("def run_filter1("):]
    for name in ("rsi14", "sma50", "sma200"):
        assert f"metrics.{name}" not in body.split("Candidate(")[0]


def test_the_band_comes_from_rules_and_is_not_restated():
    """Not as a number, and not as prose either.

    A message reading "outside 15%-50%" is a second copy of the rule: change
    the band and the report describes the old one. The text is built from the
    imported constants.
    """
    source = (ROOT / "vss" / "filters.py").read_text(encoding="utf-8")
    assert "in_dislocation_band" in source
    assert "0.15" not in source and "0.50" not in source
    for restated in ("15%-50%", "15% - 50%", "15-50%", "0.15 <=", "<= 0.50"):
        assert restated not in source, f"filters.py restates the band as {restated!r}"


def test_the_band_text_tracks_the_constants(monkeypatch):
    from vss import filters, rules

    assert filters.BAND_TEXT == f"{rules.DISLOCATION_MIN:.0%}-{rules.DISLOCATION_MAX:.0%}"


def test_a_rejection_message_quotes_the_live_band():
    frames = {"A.ST": flat_then_drop(100.0, 95.0)}
    result = run_filter1([instrument("A.ST")], frames, date(2026, 8, 21))
    from vss.filters import BAND_TEXT

    assert BAND_TEXT in result.rejections[0].reason


# --- B1, reported as context ----------------------------------------------


def test_b1_measures_the_share_of_the_decline_in_the_last_180_days():
    # 100 for a year, then straight to 60: the whole decline is recent.
    frame = series([100.0] * 300 + [60.0] * 100)
    metrics = compute(frame, date(2026, 8, 21))
    assert b1_metric(frame, metrics, date(2026, 8, 21)) == pytest.approx(1.0)


def test_b1_is_none_when_the_close_is_the_high():
    frame = series([100.0] * 400)
    metrics = compute(frame, date(2026, 8, 21))
    assert b1_metric(frame, metrics, date(2026, 8, 21)) is None


def test_b1_is_none_without_an_old_enough_close():
    frame = series([100.0] * 30 + [70.0] * 10)
    metrics = compute(frame, date(2026, 8, 21))
    assert b1_metric(frame, metrics, date(2026, 8, 21)) is None


def test_b1_can_be_negative_when_the_last_180_days_are_net_up():
    """SAP's own case in FRAMEWORK-EDITS B1: metric -0.27, gate still PASS."""
    frame = series([200.0] * 100 + [100.0] * 200 + [150.0] * 100)
    metrics = compute(frame, date(2026, 8, 21))
    assert b1_metric(frame, metrics, date(2026, 8, 21)) < 0


# --- ACCEPTANCE ------------------------------------------------------------


@pytest.fixture()
def fixture_snapshot(tmp_path: Path) -> tuple[Path, list[Instrument]]:
    """A snapshot built from the committed, frozen price fixtures.

    Offline and deterministic: the CSVs were captured 2026-08-20 and never
    move, so only a code change can alter this test's answer.
    """
    universe = tmp_path / "universe"
    universe.mkdir()
    tickers = ["SAP.DE", "MSFT", "NKE", "UNA.AS", "MC.PA", "HNSA.ST"]
    markets = {"SAP.DE": "Xetra", "MSFT": "US", "NKE": "US",
               "UNA.AS": "Amsterdam", "MC.PA": "Paris", "HNSA.ST": "Stockholm"}
    with (universe / "fixture.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(SCHEMA)
        for ticker in tickers:
            writer.writerow([ticker, ticker.split(".")[0], "", ticker,
                             markets[ticker], "A", "", "EUR", "Equity"])
    instruments = [instrument(t, marknad=markets[t], namn=t) for t in tickers]

    path = store.snapshot_path(date(2026, 8, 21), tmp_path / "snaps")
    store.write(
        path, as_of=date(2026, 8, 21), created_at=datetime(2026, 8, 22, 9, 0),
        instruments=instruments, tallies=[Tally("read", 6, 6)], rejections=[],
        merges=[], files=[], statuses=[],
        frames={t: read_fixture(t) for t in tickers},
    )
    return path, instruments


def test_acceptance_filter1_replayed_on_2026_07_27_contains_sap(fixture_snapshot):
    """THE PHASE 2 ACCEPTANCE TEST.

    Filter 1 is called DIRECTLY, on the whole universe. It is not the chain:
    SAP.DE sits on the exclusion list as a held position, so a chain run
    would remove it at step 0 and this test could not tell a broken filter
    from a working exclusion. What is under test here is the dislocation
    band and nothing else.
    """
    path, instruments = fixture_snapshot
    frames = store.read_all_prices(path)
    result = run_filter1(instruments, frames, date(2026, 7, 27))

    tickers = {c.ticker for c in result.candidates}
    assert "SAP.DE" in tickers, (
        "filter 1 dropped SAP.DE on 2026-07-27. The filter is wrong, not SAP."
    )

    sap = next(c for c in result.candidates if c.ticker == "SAP.DE")
    assert sap.last_close_date == date(2026, 7, 27)
    assert sap.last_close == pytest.approx(151.28, abs=0.01)
    assert sap.high_52w == pytest.approx(254.75, abs=0.01)
    assert sap.drawdown == pytest.approx(0.406, abs=0.001)
    assert DISLOCATION_MIN <= sap.drawdown <= DISLOCATION_MAX
    assert in_dislocation_band(sap.drawdown) is True


def test_acceptance_is_measured_at_the_replay_date_not_the_snapshot_edge(fixture_snapshot):
    """Guards the reason the acceptance test could pass falsely.

    The snapshot runs to 2026-08-20. If truncation regressed, SAP would be
    scored at 185.64 and a 23.3% drawdown -- still inside the band, so the
    acceptance test above would still pass while measuring the wrong day.
    """
    path, instruments = fixture_snapshot
    frames = store.read_all_prices(path)
    july = run_filter1(instruments, frames, date(2026, 7, 27))
    august = run_filter1(instruments, frames, date(2026, 8, 21))

    sap_july = next(c for c in july.candidates if c.ticker == "SAP.DE")
    sap_august = next(c for c in august.candidates if c.ticker == "SAP.DE")
    assert sap_july.last_close != sap_august.last_close
    assert sap_july.drawdown != sap_august.drawdown
    assert sap_july.rsi14 != sap_august.rsi14


def test_the_chain_removes_sap_because_it_is_held(fixture_snapshot):
    """The complement: step 0 works, which is why the acceptance test
    bypasses it."""
    path, instruments = fixture_snapshot
    exclusions = load_exclusions(ROOT / "config" / "screener_exclusions.csv")
    kept, rejections, tally, _ = apply_exclusions(instruments, exclusions)
    assert "SAP.DE" not in {i.ticker_yahoo for i in kept}

    frames = store.read_all_prices(path)
    result = run_filter1(kept, frames, date(2026, 7, 27))
    assert "SAP.DE" not in {c.ticker for c in result.candidates}
    assert tally.rejected_on_value >= 1


def test_the_committed_exclusion_list_is_well_formed_and_covers_the_book():
    entries = {e.ticker_yahoo: e for e in
               load_exclusions(ROOT / "config" / "screener_exclusions.csv")}
    for ticker in ("LIAB.ST", "SAP.DE", "MSFT", "NKE", "HNSA.ST", "ULVR.L"):
        assert ticker in entries, ticker
        assert entries[ticker].skal and entries[ticker].kalla
    # Item 6 (SCREENER-REVIEW-3 Part 13): SAP.DE was sold 2026-08-26 under
    # C4/E42 and the row says so; the UNA.AS row matched nothing in any
    # universe file and was replaced by the London line the universe carries.
    assert entries["SAP.DE"].skal == "WATCH-PRICED"
    assert "E42" in entries["SAP.DE"].kalla
    assert "UNA.AS" not in entries


def test_the_committed_exclusion_list_has_no_inert_row():
    """An inert entry that reads as active is how a name quietly comes back
    (the UNA.AS row until 2026-08-26). Every committed row must match a
    name in the committed universe THE SCREENER ACTUALLY LOADS.

    THE TIERS ARE A AND B, and this was `("A",)` until 2026-09-08. It was
    right when tier B was empty and became wrong when the S&P MidCap 400 and
    the Nordic mid caps were added, but nothing failed until an exclusion row
    first pointed at a tier B name -- CRUS, dropped 2026-09-08 and carried in
    `sp400-2026-08-31.csv` at tier B. The live screener runs on A,B: the
    2026-09-05 run says so in its own report ("this run on `A,B`") and it
    ranked CRUS at #78 on that same run, so the row bites. Testing a
    NARROWER universe than production loads makes a live row read as inert,
    which is this test's own failure mode pointed the other way."""
    from vss.universe import load_type_rules, load_universe

    universe_dir = ROOT / "config" / "universe"
    load = load_universe(universe_dir, tiers=("A", "B"),
                         type_rules=load_type_rules(universe_dir / "instrument_types.yaml"))
    exclusions = load_exclusions(ROOT / "config" / "screener_exclusions.csv")
    _, _, _, unmatched = apply_exclusions(load.instruments, exclusions)
    assert [e.ticker_yahoo for e in unmatched] == []


def test_the_committed_exclusion_list_carries_no_position_figures():
    """A reason column names the decision and its date, never its price.

    THE ORIGINAL REASON IS GONE and the rule is kept anyway. Until
    2026-08-25 the argument was that this file is committed while
    config/watchlist.yaml is not, so the reason column was a place to leak
    a stop or a fair value back into git. The watchlist is now tracked --
    the owner's decision, a private repository -- so that argument no
    longer holds.

    What holds: an exclusion says WHY a name may not be proposed, and a
    price is not a why. A figure here is also a figure nothing updates, in
    a file the screener reads on every run. If the owner wants prices in
    exclusion reasons, that is a ruling to make deliberately, not a test to
    delete quietly.
    """
    import re

    text = (ROOT / "config" / "screener_exclusions.csv").read_text(encoding="utf-8")
    for field in ("fv_base", "mbp", "stop_price", "MBP"):
        assert field not in text, f"the exclusion list mentions {field}"
    for entry in load_exclusions(ROOT / "config" / "screener_exclusions.csv"):
        assert not re.search(r"\d+[.,]\d", entry.kalla), (
            f"{entry.ticker_yahoo}: kalla carries a figure -- {entry.kalla!r}"
        )


# --- E51: the circle of competence -----------------------------------------


def circle_file(tmp_path: Path, **blocks) -> Path:
    import yaml
    path = tmp_path / "pharma.yaml"
    document = {"industries": [], "sectors": [], "tickers": [], "exempt": []}
    document.update(blocks)
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    return path


def test_e51_the_committed_list_is_the_one_the_ruling_names():
    """The file the screener actually reads, not a fixture of it."""
    config = load_circle_of_competence()
    assert "Biotechnology" in config.industries
    assert "Drug Manufacturers - General" in config.industries
    assert "Drug Manufacturers - Specialty & Generic" in config.industries
    # E51 does NOT reach a whole sector: `Healthcare` would take the medical
    # device, diagnostics and care-facility businesses with it.
    assert config.sectors == frozenset()


def test_e51_the_industry_string_removes_a_name_at_step_0(tmp_path: Path):
    path = circle_file(tmp_path, industries=["Drug Manufacturers - General"])
    instruments = [instrument("NOVO-B.CO", namn="NOVO NORDISK CLASS B"),
                   instrument("AUTO.L", namn="AUTOTRADER GROUP PLC")]
    outcome = apply_circle_of_competence(
        instruments, load_circle_of_competence(path),
        sector_of={"NOVO-B.CO": "Healthcare", "AUTO.L": "Communication Services"},
        industry_of={"NOVO-B.CO": "Drug Manufacturers - General",
                     "AUTO.L": "Internet Content & Information"},
    )
    assert [i.ticker_yahoo for i in outcome.kept] == ["AUTO.L"]
    assert [h.ticker for h in outcome.hits] == ["NOVO-B.CO"]
    assert outcome.hits[0].limb == "industry"
    # A ruling about what the company IS: recorded, dated, on a VALUE.
    assert outcome.tally.rejected_on_value == 1
    assert outcome.tally.rejected_on_missing == 0
    assert outcome.without_string == 0


def test_e51_a_name_with_no_stored_string_is_counted_never_removed(tmp_path: Path):
    """The string limb is blind to a name the fundamentals fetch never
    visited, and its silence is a fact about the FETCH."""
    path = circle_file(tmp_path, industries=["Biotechnology"])
    instruments = [instrument("X.ST"), instrument("Y.ST")]
    outcome = apply_circle_of_competence(instruments, load_circle_of_competence(path))
    assert len(outcome.kept) == 2 and outcome.hits == []
    assert outcome.without_string == 2


def test_e51_the_owner_list_reaches_a_name_the_vendor_never_classified(tmp_path: Path):
    path = circle_file(tmp_path, tickers=[{"ticker": "X.ST", "company": "X AB"}])
    outcome = apply_circle_of_competence(
        [instrument("X.ST"), instrument("Y.ST")], load_circle_of_competence(path))
    assert [i.ticker_yahoo for i in outcome.kept] == ["Y.ST"]
    assert outcome.hits[0].limb == "owner list"


def test_e51_an_owner_entry_matching_nothing_is_reported_as_inert(tmp_path: Path):
    path = circle_file(tmp_path, tickers=[{"ticker": "GONE.ST", "company": "Gone AB"}])
    outcome = apply_circle_of_competence([instrument("X.ST")],
                                         load_circle_of_competence(path))
    assert outcome.unmatched == ["GONE.ST"]
    assert outcome.hits == []


def test_e51_an_exemption_lets_a_string_match_through_and_is_printed(tmp_path: Path):
    path = circle_file(tmp_path, industries=["Biotechnology"],
                       exempt=[{"ticker": "TUB.BR", "reason": "a holding company"}])
    outcome = apply_circle_of_competence(
        [instrument("TUB.BR")], load_circle_of_competence(path),
        industry_of={"TUB.BR": "Biotechnology"})
    assert [i.ticker_yahoo for i in outcome.kept] == ["TUB.BR"]
    assert outcome.hits == []
    assert [h.ticker for h in outcome.exempted] == ["TUB.BR"]
    assert outcome.exempted[0].detail == "a holding company"


def test_e51_an_exemption_does_not_reach_the_owners_own_list(tmp_path: Path):
    """The escape hatch is for the VENDOR's string. A name the owner named
    is out, and a file that says both is refused before it can be read."""
    with pytest.raises(CircleError, match="disagrees with itself"):
        load_circle_of_competence(circle_file(
            tmp_path,
            tickers=[{"ticker": "X.ST", "company": "X AB"}],
            exempt=[{"ticker": "X.ST", "reason": "changed my mind"}]))


def test_e51_an_exemption_without_a_reason_is_refused(tmp_path: Path):
    with pytest.raises(CircleError, match="exempt with no reason"):
        load_circle_of_competence(circle_file(
            tmp_path, exempt=[{"ticker": "X.ST"}]))


def test_e51_a_missing_list_is_an_error_never_an_empty_config(tmp_path: Path):
    with pytest.raises(CircleError, match="no circle-of-competence list"):
        load_circle_of_competence(tmp_path / "absent.yaml")


def test_e51_the_committed_list_catches_novo_and_spares_the_device_makers():
    """The ruling's own table, against the file the screener reads."""
    config = load_circle_of_competence()
    # SFZN.SW was here until E51.1 exempted it (a CDMO); ALVO-SDB.ST is the
    # Specialty & Generic name that stands, and the ruling names it as one
    # of the two nearer the line than the rest.
    caught = {"NOVO-B.CO": "Drug Manufacturers - General",
              "ZEAL.CO": "Biotechnology",
              "ALVO-SDB.ST": "Drug Manufacturers - Specialty & Generic"}
    spared = {"SYK": "Medical Devices", "ISRG": "Medical Instruments & Supplies",
              "QIA.DE": "Diagnostics & Research", "HCA": "Medical Care Facilities"}
    industry_of = {**caught, **spared}
    outcome = apply_circle_of_competence(
        [instrument(t) for t in industry_of],
        config,
        sector_of={t: "Healthcare" for t in industry_of},
        industry_of=industry_of,
    )
    assert {h.ticker for h in outcome.hits} == set(caught)
    assert {i.ticker_yahoo for i in outcome.kept} == set(spared)


# --- E52: the listing-age floor --------------------------------------------


def test_e52_five_calendar_years_and_a_leap_day_lands_earlier():
    from vss import metrics as M

    assert M.LISTING_AGE_YEARS == 5
    assert M.listing_age_start(date(2026, 8, 27)) == date(2021, 8, 27)
    # 29 February with no 29 February five years back: the EARLIER reading,
    # which is the stricter one.
    assert M.listing_age_start(date(2028, 2, 29)) == date(2023, 2, 28)
    assert M.covers_listing_age(None, date(2026, 8, 27)) is False


def test_e52_is_measured_on_the_series_not_on_the_universe_listdatum():
    """The universe CSV's listdatum is empty on most rows; a rule reading it
    would reject the whole universe. Filter 1 takes instruments and frames
    and nothing else, so it CANNOT read that field -- asserted structurally."""
    old = instrument("OLD.ST")
    assert old.listdatum is None                     # as most rows are
    frames = {"OLD.ST": flat_then_drop(100.0, 75.0)}  # 2000 rows of history
    result = run_filter1([old], frames, date(2026, 8, 21))
    assert [c.ticker for c in result.candidates] == ["OLD.ST"]


def test_e52_1_a_spin_off_is_a_new_listing_and_there_is_no_exemption():
    """FRAMEWORK-EDITS E52.1, ruled 2026-08-27.

    A spin-off's business is older than its tape and the floor does not care:
    what is missing is the MARKET's record of pricing this security, and a
    carve-out is missing it exactly as a first-time IPO is. The guard here is
    structural -- `run_filter1` takes instruments and frames and nothing
    else, so there is nowhere for a per-name exemption to enter, and this
    test fails the day someone adds one.
    """
    from vss import metrics as M

    as_of = date(2026, 8, 21)
    # GE Vernova's shape: first bar 2024-03-27, a business decades old.
    gev = flat_then_drop(100.0, 75.0, days=878)
    assert M.compute(gev, as_of).first_bar_date == date(2024, 3, 27)
    result = run_filter1([instrument("GEV")], {"GEV": gev}, as_of)
    assert result.candidates == []
    tallies = {t.step: t for t in result.tallies}
    assert tallies[STEP_LISTING_AGE].rejected_on_missing == 1
    # E52.1: no exemption list, and no argument from the age of the business.
    assert not hasattr(run_filter1, "exemptions")
    import inspect
    signature = inspect.signature(run_filter1).parameters
    assert "exempt" not in signature and "listing_age_exempt" not in signature


def test_e51_1_the_two_exemptions_are_in_the_committed_file_with_reasons():
    """FRAMEWORK-EDITS E51.1, ruled 2026-08-27. The file the screener reads."""
    config = load_circle_of_competence()
    assert config.exempt == frozenset({"SFZN.SW", "FLERIE.ST"})
    assert "CDMO" in config.exempt_reasons["SFZN.SW"]
    assert "INVESTMENT company" in config.exempt_reasons["FLERIE.ST"]


def test_e51_1_the_exemptions_return_the_two_names_to_the_chain():
    config = load_circle_of_competence()
    industry_of = {"SFZN.SW": "Drug Manufacturers - Specialty & Generic",
                   "FLERIE.ST": "Biotechnology",
                   "TUB.BR": "Biotechnology",
                   "UCB.BR": "Biotechnology"}
    outcome = apply_circle_of_competence(
        [instrument(t) for t in industry_of], config,
        sector_of={t: "Healthcare" for t in industry_of}, industry_of=industry_of)
    assert {i.ticker_yahoo for i in outcome.kept} == {"SFZN.SW", "FLERIE.ST"}
    assert {h.ticker for h in outcome.exempted} == {"SFZN.SW", "FLERIE.ST"}
    # TUB.BR is NOT exempt -- the owner sent it to E46's list instead.
    assert {h.ticker for h in outcome.hits} == {"TUB.BR", "UCB.BR"}


def test_e51_1_tubize_is_on_e46s_list_and_e51_still_removes_it_first():
    """E51.1's ordering fact, and it is the point of the ruling.

    Step 0's second limb runs before anything reads the investment-company
    list, so the E46 entry is INERT today. Recorded now so the
    classification is not made under pressure the day E51's catch is lifted.
    """
    from vss.filters import load_investment_companies

    assert "TUB.BR" in load_investment_companies()
    outcome = apply_circle_of_competence(
        [instrument("TUB.BR")], load_circle_of_competence(),
        sector_of={"TUB.BR": "Healthcare"},
        industry_of={"TUB.BR": "Biotechnology"})
    assert [h.ticker for h in outcome.hits] == ["TUB.BR"]
    assert outcome.kept == []


def test_e51_2_the_owner_list_carries_the_twenty_that_resolve():
    """FRAMEWORK-EDITS E51.2, ruled 2026-08-27."""
    config = load_circle_of_competence()
    expected = {"PFE", "MRK", "MRK.DE", "LLY", "NOVN.SW", "SAN.PA", "BAYN.DE",
                "ABBV", "AMGN", "GILD", "BIIB", "REGN", "VRTX", "GMAB.CO",
                "ARGX.BR", "SOBI.ST", "HIK.L", "IPN.PA", "REC.MI", "ORNBV.HE"}
    assert expected <= config.tickers


def test_e51_2_rog_sw_is_carried_as_the_owner_wrote_it_and_is_inert():
    """E51.2: ROG.SW is Roche's REGISTERED share and is in no universe file.

    It is kept as written and reported inert. ROP.SW -- the Genussschein,
    the only Roche line this universe carries -- was NOT substituted, and
    this test pins that: the day someone 'fixes' the list by swapping the
    ticker, the file starts saying something the owner did not.
    """
    config = load_circle_of_competence()
    assert "ROG.SW" in config.tickers
    assert "ROP.SW" not in config.tickers
    outcome = apply_circle_of_competence([instrument("ROP.SW")], config)
    assert [i.ticker_yahoo for i in outcome.kept] == ["ROP.SW"]   # not caught
    assert "ROG.SW" in outcome.unmatched                           # and inert


def test_e51_2_a_pharma_major_with_no_vendor_string_is_now_caught():
    """The gap the list closes: no string, and removed anyway."""
    config = load_circle_of_competence()
    outcome = apply_circle_of_competence(
        [instrument("PFE"), instrument("AUTO.L")], config)   # no strings at all
    assert [h.ticker for h in outcome.hits] == ["PFE"]
    assert outcome.hits[0].limb == "owner list"
    assert [i.ticker_yahoo for i in outcome.kept] == ["AUTO.L"]
    assert outcome.without_string == 2


def test_e63_the_52_week_low_is_carried_but_never_decides():
    """FRAMEWORK-EDITS E63: the other end of the window travels under the
    same standing rule as RSI and the SMAs. The row carries the low, its
    session and the distance above it; nothing in filter 1 reads them
    before the row is built, and nothing in filter 2 reads them at all."""
    import ast

    frames = {"A.ST": flat_then_drop(100.0, 75.0)}
    result = run_filter1([instrument("A.ST")], frames, date(2026, 8, 21))
    candidate = result.candidates[0]
    assert candidate.low_52w == pytest.approx(75.0)
    assert candidate.low_52w_date == date(2026, 8, 21)
    assert candidate.pct_above_52w_low == pytest.approx(0.0)

    source = (ROOT / "vss" / "filters.py").read_text(encoding="utf-8")
    body = source[source.index("def run_filter1("):]
    for name in ("low_52w", "low_52w_date", "pct_above_52w_low"):
        assert f"metrics.{name}" not in body.split("Candidate(")[0], \
            f"run_filter1 reads {name} before the row is built"

    tree = ast.parse(source)
    (filter2,) = [n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "run_filter2"]
    touched = {n.attr for n in ast.walk(filter2) if isinstance(n, ast.Attribute)}
    touched |= {n.id for n in ast.walk(filter2) if isinstance(n, ast.Name)}
    assert not {"low_52w", "low_52w_date", "pct_above_52w_low"} & touched, \
        "run_filter2 reads an E63 field"


# --- E127: the trailing year -------------------------------------------------


def run_up_then_pullback(base: float, peak: float, end: float,
                         days: int = 2000, rise: int = 300,
                         fall: int = 20) -> pd.DataFrame:
    """HUNT.OL's shape: flat for years, a long climb, a short pullback.

    Inside the band at the end, and far ABOVE its close of a year ago.
    Both moves are ramps so the K4 sanity check measures the series.
    """
    up = [base + (peak - base) * (i + 1) / rise for i in range(rise)]
    down = [peak + (end - peak) * (i + 1) / fall for i in range(fall)]
    return series([base] * (days - rise - fall) + up + down)


def test_e127_a_pullback_after_a_run_up_is_rejected_on_value():
    """In the band, and up on the year: rejected at the trailing-year step,
    never at the band -- the funnel says which of the two removed it."""
    from vss.filters import STEP_TRAILING_YEAR

    frames = {"UP.OL": run_up_then_pullback(10.0, 100.0, 84.0)}
    result = run_filter1([instrument("UP.OL")], frames, date(2026, 8, 21))
    assert result.candidates == []
    tallies = {t.step: t for t in result.tallies}
    assert tallies[STEP_DISLOCATION].count_out == 1
    assert tallies[STEP_TRAILING_YEAR].rejected_on_value == 1
    (rejection,) = [r for r in result.rejections if r.step == STEP_TRAILING_YEAR]
    assert rejection.kind == ON_VALUE
    assert "E127" in rejection.reason


def test_e127_a_name_below_its_close_of_a_year_ago_passes_and_carries_it():
    frames = {"A.ST": flat_then_drop(100.0, 75.0)}
    result = run_filter1([instrument("A.ST")], frames, date(2026, 8, 21))
    (candidate,) = result.candidates
    assert candidate.close_year_ago == pytest.approx(100.0)
    assert candidate.close_year_ago_date == date(2025, 8, 21)
    assert candidate.return_12m == pytest.approx(-0.25)


def test_e127_zero_is_not_a_fall_and_no_close_a_year_back_is_missing():
    from vss.rules import fell_over_year

    assert fell_over_year(-0.001) is True
    assert fell_over_year(0.0) is False
    assert fell_over_year(0.25) is False
    assert fell_over_year(None) is None
    # Below the coverage bar there is no year-ago close, never a later one.
    short = compute(flat_then_drop(100.0, 75.0, days=200), date(2026, 8, 21))
    assert short.return_12m is None and short.close_year_ago is None
