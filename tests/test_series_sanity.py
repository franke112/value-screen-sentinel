"""K4: the price-series sanity check, against real stored data and against
synthetic series built to sit on each side of every threshold.

Three of the fixtures are NOT hand-built. ``tests/fixtures/series-sanity/``
holds the closes and volumes actually stored in the 2026-08-21 snapshot for
MNST (a feed alternating between two scales), MRNA (a real +177% session) and
ELUX-A.ST (a spin-off day). The review of 2026-08-22 observed that every
fixture in this suite was hand-built and well-formed, and that the MNST
corruption would have passed 954 of 954 tests. These three are the answer to
that: the check is held against the exact rows that fooled the screener.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

from vss.metrics import compute, drawdown, high_52w
from vss.series_sanity import (
    CORROBORATING_VOLUME_MULTIPLE,
    JUMP_FACTOR,
    KIND_SCALE_SWITCH,
    KIND_UNCORROBORATED,
    MIN_SESSIONS,
    ROUND_TRIP_WINDOW_DAYS,
    check,
    find_jumps,
)
from tests._vendor_data import need

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "series-sanity"
AS_OF = date(2026, 8, 21)


def stored(ticker: str) -> pd.DataFrame:
    """The rows the snapshot actually holds for this name."""
    need(FIXTURES / f"{ticker}.csv")
    frame = pd.read_csv(FIXTURES / f"{ticker}.csv", index_col=0)
    frame.index = pd.DatetimeIndex([pd.Timestamp(v) for v in frame.index])
    return frame


def synthetic(closes, volumes=None, last: date = AS_OF) -> pd.DataFrame:
    days = len(closes)
    index = pd.to_datetime([last - timedelta(days=days - 1 - i) for i in range(days)])
    return pd.DataFrame(
        {"Close": closes, "Volume": volumes or [1000.0] * days}, index=index
    )


# --- the real cases --------------------------------------------------------


def test_the_mnst_series_that_fooled_the_screener_is_refused():
    """The case K4 exists for, on the rows that produced it.

    The stored series alternates between the split-adjusted and unadjusted
    scale for four weeks. Read straight, it gives a 52-week high of 99.94 on
    one scale against a last close of 47.79 on the other -- a 52.2% drawdown
    where the true figure is about -4%.
    """
    frame = stored("MNST")
    # The fabricated figure, struck the way the screener struck it -- off
    # the primitives, which is where the 52.2% came from.
    closes = frame["Close"]
    fabricated = drawdown(float(closes.to_numpy()[-1]), high_52w(closes, AS_OF))
    assert fabricated == pytest.approx(0.522, abs=0.01), \
        "the fixture no longer reproduces the fabricated drawdown"

    # TWO INDEPENDENT GUARDS, and this fixture happens to trip both. The
    # 250-row fixture spans a bare 52 weeks, so `compute` now returns DATA
    # MISSING for the drawdown on coverage grounds alone (REVIEW-4 report
    # B 7.2) -- which does NOT make K4 redundant: a 500-row series carrying
    # the same scale switch clears coverage and still has to be refused.
    measured = compute(frame, AS_OF)
    assert measured.drawdown is None and measured.covers_52_weeks is False

    finding = check(frame, AS_OF)
    assert finding is not None, "the corrupt series passed the check"
    assert finding.kind == KIND_SCALE_SWITCH
    assert "returns to a scale it left" in finding.detail


def test_a_real_repricing_that_the_tape_confirms_is_NOT_refused():
    """MRNA closed +177% on 2026-08-19, on 23.8x its own median volume.

    A check that threw this away would be trading one silent error for a
    louder one. Whether a two-day-old peak should count as a 52-week high is
    a different question -- it is K3, the band, and it is not this module's.
    """
    frame = stored("MRNA")
    jumps = find_jumps([
        (day, close, volume) for day, close, volume in zip(
            [d.date() for d in frame.index], frame["Close"], frame["Volume"])
    ])
    assert any(j.move > 1.5 for j in jumps), "the fixture lost the +177% session"
    assert check(frame, AS_OF) is None


def test_a_spin_off_day_is_refused_as_uncorroborated_not_as_a_scale_switch():
    """ELUX-A.ST fell 48% on 2026-05-19 on 0.2x its median volume.

    The price is correct and the company is fine. The claim is narrower: the
    52-week high on the other side of that break is not comparable with
    today's close, so the drawdown across it is not a measurement.
    """
    finding = check(stored("ELUX-A.ST"), AS_OF)
    assert finding is not None
    assert finding.kind == KIND_UNCORROBORATED
    assert "2026-05-19" in finding.detail


# --- the scale switch ------------------------------------------------------


def flat(n: int, value: float = 100.0) -> list[float]:
    return [value] * n


def test_a_split_that_stays_split_is_not_a_scale_switch():
    """A corporate action happens once. Halving and STAYING halved is a
    corporate action; only a feed quoting two scales goes back."""
    closes = flat(200) + flat(160, 50.0)
    volumes = [1000.0] * 360
    volumes[200] = 5000.0            # a real event trades
    assert check(synthetic(closes, volumes), AS_OF) is None


def test_halving_and_coming_back_is_a_scale_switch():
    closes = flat(200) + flat(5, 50.0) + flat(155, 100.0)
    finding = check(synthetic(closes), AS_OF)
    assert finding is not None and finding.kind == KIND_SCALE_SWITCH


def test_a_round_trip_of_ordinary_volatility_is_not_a_scale_switch():
    """Up 30% and back down 23% is a small cap having a week, not two scales.

    Measured: lowering the jump factor to 1.3 starts flagging SIVE.ST and
    ELTEL.ST, both of which are simply volatile.
    """
    closes = flat(200) + flat(5, 130.0) + flat(155, 100.0)
    assert check(synthetic(closes), AS_OF) is None


def test_the_two_halves_must_point_in_opposite_directions():
    """Two doublings are a name that quadrupled, not a series that flipped."""
    closes = flat(120) + flat(120, 200.0) + flat(120, 400.0)
    volumes = [1000.0] * 360
    volumes[120] = volumes[240] = 9000.0
    assert check(synthetic(closes, volumes), AS_OF) is None


def test_a_return_trip_outside_the_window_is_not_paired():
    far = ROUND_TRIP_WINDOW_DAYS + 40
    closes = flat(200) + flat(far, 50.0) + flat(400 - 200 - far, 100.0)
    finding = check(synthetic(closes), AS_OF)
    # It is still refused -- the jumps are uncorroborated -- but NOT on the
    # stronger claim, which the evidence does not support at that distance.
    assert finding is not None and finding.kind == KIND_UNCORROBORATED


# --- the volume witness ----------------------------------------------------


def test_a_big_move_the_volume_confirms_passes():
    closes = flat(200) + flat(160, 55.0)
    volumes = [1000.0] * 360
    volumes[200] = 1000.0 * CORROBORATING_VOLUME_MULTIPLE
    assert check(synthetic(closes, volumes), AS_OF) is None


def test_the_same_move_one_notch_below_the_volume_bar_is_refused():
    """The threshold is a threshold, and the test says which side is which."""
    closes = flat(200) + flat(160, 55.0)
    volumes = [1000.0] * 360
    volumes[200] = 1000.0 * CORROBORATING_VOLUME_MULTIPLE * 0.99
    finding = check(synthetic(closes, volumes), AS_OF)
    assert finding is not None and finding.kind == KIND_UNCORROBORATED


def test_a_missing_volume_is_absence_of_corroboration_never_corroboration():
    closes = flat(200) + flat(160, 55.0)
    frame = synthetic(closes)
    frame = frame.drop(columns=["Volume"])
    finding = check(frame, AS_OF)
    assert finding is not None
    assert "no volume was reported" in finding.detail


def test_a_move_just_inside_the_jump_factor_is_not_examined_at_all():
    """Below the factor the volume is never consulted: an ordinary session on
    ordinary volume is what most sessions are."""
    closes = flat(200) + flat(160, 100.0 / (JUMP_FACTOR * 0.99))
    assert check(synthetic(closes), AS_OF) is None


# --- what the check refuses to answer --------------------------------------


def test_a_series_too_short_to_hold_a_median_gets_no_verdict():
    """Silence, not a verdict. A series this short has no 52-week high worth
    the name either, and the steps above decide what to do with it."""
    closes = flat(MIN_SESSIONS - 5) + [10.0]
    assert check(synthetic(closes), AS_OF) is None


def test_a_break_older_than_the_window_is_not_examined():
    """The check reads the window the drawdown reads. Refusing a name for a
    break the run never looks at would be rejecting on unused evidence."""
    closes = flat(60, 50.0) + flat(400)
    frame = synthetic(closes, last=AS_OF)
    assert check(frame, AS_OF) is None


def test_an_empty_frame_is_not_a_finding():
    assert check(pd.DataFrame(), AS_OF) is None
    assert check(None, AS_OF) is None
