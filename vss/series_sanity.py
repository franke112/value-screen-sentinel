"""Is a price series a measurement, or a number the feed made up? (K4)

``snapshot.verify()`` proves the RIGHT FILE was read -- sha256 on every
universe file, no row dated after ``as_of``. It says nothing about whether the
contents are plausible, and nothing anywhere else did either. This module is
that missing question, and it exists because of one measured case:

    MNST, July-August 2026, the closes actually stored:
        07-30  97.65   07-31  48.19   08-03  93.55   08-05  94.46
        08-06  47.08   08-07  90.36   08-11  45.53   ...  08-21  47.79

    The series alternates between the split-adjusted and the unadjusted scale
    for four weeks. The screener read a 52-week high of 99.94 on one scale
    against a last close of 47.79 on the other, called it a 52.2% drawdown,
    and rejected the name as structurally damaged. The true figure is about
    -4%. Had the split been 3:2 rather than 2:1 the same corruption would have
    produced a drawdown INSIDE the band and sent fabricated data to the
    fundamentals fetch and to the ranking key.

TWO CHECKS, and they answer different questions.

**A scale switch is PROVEN by a round trip.** A corporate action happens once
and the series stays on the new scale: a split does not un-split, a spin-off
does not re-merge. Only a feed quoting two scales goes back. So a large jump
followed within the window by a large jump the other way whose product returns
to the old scale is not volatility -- it is two scales in one column.

**A lone discontinuity is not proven, so it needs a second witness, and the
witness is the tape.** A real repricing of forty per cent in one session
trades: measured over the whole 1,370-name universe, MRNA's +177% came on 23.8
times its own median volume, ABVX.PA's -44% on 14.2, VPLAY-A.ST's -46% on
30.8. A discontinuity that is NOT a repricing does not trade: Electrolux's
spin-off day on 0.2, Orsted's rights issue on 1.1, MNST's fabricated halvings
on 0.7 to 2.6. The volume test is what separates the two, and it is the review
of 2026-08-22's own suggestion.

WHAT THE SECOND CHECK CLAIMS, AND WHAT IT DOES NOT. It does not claim the
data is corrupt. A spin-off and a rights issue are real events correctly
priced. The claim is narrower and holds for all three causes at once: **the
52-week high on the far side of such a break is not comparable with today's
close, so the drawdown measured across it is not a measurement.** That is
DATA MISSING, and it is the third state this project keeps everywhere else.

A FLAGGED NAME IS REJECTED ON MISSING DATA, NEVER ON VALUE. It did not fail
the band; the band could not be evaluated for it. Putting it in the value
column would say the market did something it did not do.

Measured cost, over the 1,370-ticker snapshot of 2026-08-21 and the 536 names
that reached the band:

    round trip           1 ticker  (MNST)                     0 in the band
    uncorroborated       4 tickers (MNST, ELUX-A.ST,          1 in the band
                                    ELUX-B.ST, ORSTED.CO)       (ORSTED.CO)

Nothing else in the universe is touched. Every genuinely violent repricing in
the window -- INTRUM.ST -81%, SUS.ST -60%, VOLO.ST -62%, MRNA +177% -- is
corroborated by its own volume and passes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence

import pandas as pd

from .metrics import LOOKBACK_DAYS, index_dates

#: How large a close-to-close move must be to count as a jump at all. 1.6 is
#: +60% up or -37.5% down in one session. Measured: at this factor the round
#: trip flags exactly one ticker in 1,370, and lowering it to 1.3 starts
#: catching ordinary two-day volatility in small caps (SIVE.ST, ELTEL.ST).
JUMP_FACTOR = 1.6

#: How far apart the two halves of a round trip may sit. A feed quoting two
#: scales flips within days; MNST's flips were 1 to 11 sessions apart.
ROUND_TRIP_WINDOW_DAYS = 90

#: How close to 1.0 the product of the two jumps must land for the series to
#: have RETURNED to the scale it left. MNST's pairs came in at 0.939 to 0.986:
#: not exactly reciprocal, because the market also moved between the flips.
ROUND_TRIP_TOLERANCE = 0.15

#: Session volume, as a multiple of the name's own median in the window, above
#: which a large move is taken as a real repricing rather than a break. The
#: measured gap is wide -- corroborated moves came in at 8.8x to 96.7x, the
#: four breaks at 0.2x to 2.6x -- so the exact value between 3 and 8 changes
#: nothing on this universe. 3.0 is the conservative end of that gap.
CORROBORATING_VOLUME_MULTIPLE = 3.0

#: Below this many sessions in the window there is no median to compare a
#: volume against, and a short series is already handled upstream.
MIN_SESSIONS = 30

KIND_SCALE_SWITCH = "scale switch"
KIND_UNCORROBORATED = "uncorroborated discontinuity"

STEP_SERIES_SANITY = "series_sanity"


@dataclass(frozen=True)
class Jump:
    """One close-to-close move large enough to be worth explaining."""

    day: date
    previous_day: date
    previous_close: float
    close: float
    ratio: float
    #: Session volume over the name's median for the window. None when the
    #: feed carried no volume -- which is an ABSENCE of corroboration, never
    #: corroboration.
    volume_multiple: float | None

    @property
    def move(self) -> float:
        return self.ratio - 1.0


@dataclass(frozen=True)
class Finding:
    """Why a series cannot be measured. Never a verdict on the company."""

    kind: str
    detail: str
    jumps: tuple[Jump, ...]

    def __str__(self) -> str:
        return self.detail


def closes_and_volumes(
    frame: pd.DataFrame, as_of: date, lookback_days: int = LOOKBACK_DAYS
) -> list[tuple[date, float, float | None]]:
    """The window the drawdown is measured over, oldest first.

    The same 365 calendar days ``metrics.high_52w`` reads. A break older than
    that cannot affect the number this check protects, and rejecting a name
    for it would be rejecting on something the run does not use.
    """
    if frame is None or len(frame) == 0 or "Close" not in frame.columns:
        return []
    cutoff = as_of - timedelta(days=lookback_days)
    volumes = (frame["Volume"].to_numpy() if "Volume" in frame.columns
               else [None] * len(frame))
    out = []
    for day, close, volume in zip(index_dates(frame.index),
                                  frame["Close"].to_numpy(), volumes):
        if not (cutoff < day <= as_of) or pd.isna(close):
            continue
        usable = None if volume is None or pd.isna(volume) else float(volume)
        out.append((day, float(close), usable))
    return out


def median(values: Sequence[float]) -> float | None:
    usable = sorted(v for v in values if v is not None and v > 0)
    if not usable:
        return None
    middle = len(usable) // 2
    if len(usable) % 2:
        return usable[middle]
    return (usable[middle - 1] + usable[middle]) / 2


def find_jumps(rows: Sequence[tuple[date, float, float | None]],
               factor: float = JUMP_FACTOR) -> list[Jump]:
    """Every close-to-close move beyond ``factor``, either direction."""
    reference = median([volume for _, _, volume in rows])
    out: list[Jump] = []
    for index in range(1, len(rows)):
        (previous_day, previous_close, _) = rows[index - 1]
        (day, close, volume) = rows[index]
        if previous_close <= 0:
            continue
        ratio = close / previous_close
        if 1 / factor < ratio < factor:
            continue
        multiple = (volume / reference
                    if reference and volume is not None else None)
        out.append(Jump(day, previous_day, previous_close, close, ratio, multiple))
    return out


def scale_switch(jumps: Sequence[Jump]) -> Finding | None:
    """A jump answered by its near-reciprocal: two scales in one column.

    Not "the price moved a lot and moved back" -- the two moves must be large
    ENOUGH that no ordinary session explains either, opposite in direction,
    and their product must land back on the scale the series left.
    """
    for i, first in enumerate(jumps):
        for second in jumps[i + 1:]:
            if (second.day - first.day).days > ROUND_TRIP_WINDOW_DAYS:
                break
            if (first.ratio > 1) == (second.ratio > 1):
                continue
            product = first.ratio * second.ratio
            if abs(math.log(product)) > math.log(1 + ROUND_TRIP_TOLERANCE):
                continue
            return Finding(
                KIND_SCALE_SWITCH,
                f"the series returns to a scale it left: {first.day.isoformat()} "
                f"{first.move:+.0%} then {second.day.isoformat()} "
                f"{second.move:+.0%}, product {product:.3f}. A corporate action "
                f"happens once; a feed quoting two scales goes back",
                (first, second),
            )
    return None


def uncorroborated(jumps: Sequence[Jump]) -> Finding | None:
    """A large move the tape does not confirm.

    A real repricing of this size trades. A split, a spin-off, a rights issue
    or a mis-scaled row does not. The claim is not that the price is wrong --
    it is that the 52-week high on the far side of the break is not comparable
    with today's close, so the drawdown across it is not a measurement.
    """
    for jump in jumps:
        if (jump.volume_multiple is not None
                and jump.volume_multiple >= CORROBORATING_VOLUME_MULTIPLE):
            continue
        volume = ("no volume was reported for the session"
                  if jump.volume_multiple is None
                  else f"on {jump.volume_multiple:.1f}x the median volume")
        return Finding(
            KIND_UNCORROBORATED,
            f"{jump.day.isoformat()} closed {jump.move:+.0%} "
            f"({jump.previous_close:g} -> {jump.close:g}) {volume}; a repricing "
            f"of that size trades, so the high on the far side of it is not "
            f"comparable with today's close",
            (jump,),
        )
    return None


def check(frame: pd.DataFrame, as_of: date,
          lookback_days: int = LOOKBACK_DAYS) -> Finding | None:
    """None when the series can be measured, a Finding when it cannot.

    The round trip is tested first because it is the stronger claim: it PROVES
    two scales, where the volume test only says a break was not corroborated.
    """
    rows = closes_and_volumes(frame, as_of, lookback_days)
    if len(rows) < MIN_SESSIONS:
        # Not enough sessions to hold a median. A series this short has no
        # 52-week high worth the name either, and metrics/staleness upstream
        # already decide what to do with it. Silence here, not a verdict.
        return None
    jumps = find_jumps(rows)
    if not jumps:
        return None
    return scale_switch(jumps) or uncorroborated(jumps)
