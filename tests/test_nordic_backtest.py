"""tools/backtest/nordic.py's translation guards. Synthetic data only."""
from __future__ import annotations

from datetime import date

import pandas as pd

from tools.backtest import nordic as N


def test_who_is_out():
    assert N.excluded({"Sector": "Financial Services", "GicSector": None}, "SBNOR.OL")
    assert N.excluded({"GicSector": "Real Estate"}, "X.ST")
    assert "secondary" in N.excluded({"PrimaryTicker": "SSAB-A.ST", "Sector": "Basic Materials"}, "SSABAH.HE")
    assert N.excluded({"PrimaryTicker": "AFRY.ST", "Sector": "Industrials"}, "AFRY.ST") is None


def test_a_lease_heavy_balance_sheet_is_refused_once_known():
    d = {"Earnings": {"History": {"a": {"date": "2025-12-31", "reportDate": "2026-02-10"}}},
         "Financials": {"Balance_Sheet": {"quarterly": {"2025-12-31": {
             "filing_date": "2025-12-31", "capitalLeaseObligations": "12000", "totalAssets": "30000"}}}}}
    assert N.lease_heavy(d, date(2026, 3, 1)) == 0.4
    assert N.lease_heavy(d, date(2026, 2, 10)) is None          # not known yet
    d["Financials"]["Balance_Sheet"]["quarterly"]["2025-12-31"]["capitalLeaseObligations"] = "1000"
    assert N.lease_heavy(d, date(2026, 3, 1)) is None


def test_splits_are_whole_factors_and_a_spin_off_is_not_one():
    f = pd.DataFrame({"close": [100, 100, 25, 25, 18.25], "adjusted_close": [25, 25, 25, 25, 25]},
                     index=["2022-05-11", "2022-05-12", "2022-05-13", "2022-05-16", "2022-05-17"])
    # 100 -> 25 against a flat adjusted close: 4:1; 25 -> 18.25: a spin-off
    assert N.splits(f) == [("2022-05-13", 4.0)]


def test_a_restated_share_count_is_rebased_to_the_day():
    f = pd.DataFrame({"close": [200.0, 50.0], "adjusted_close": [50.0, 50.0]},
                     index=["2022-05-12", "2022-05-13"])
    def facts(vals):
        return {"facts": {"dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
            {"end": e, "filed": e, "val": v} for e, v in vals]}}}}}
    restated = facts([("2016-03-31", 4800.0), ("2023-03-31", 4800.0)])
    assert N.shares_known(restated, date(2016, 4, 30), f) == 1200.0
    as_reported = facts([("2016-03-31", 1200.0), ("2023-03-31", 4800.0)])
    assert N.shares_known(as_reported, date(2016, 4, 30), f) == 1200.0


def test_correction_5_a_tiny_adjusted_close_is_noise_not_a_split():
    f = pd.DataFrame({"close": [10.0, 10.0, 2.5], "adjusted_close": [0.01, 0.01, 0.0025]},
                     index=["2015-01-02", "2015-01-05", "2015-01-06"])
    # close/adjusted is flat here anyway; make the RATIO jump with a tiny adjusted close
    f.loc["2015-01-06", "adjusted_close"] = 0.01
    assert N.splits(f) == []                     # adjusted close under the floor: not read
    g = f.copy()
    g["adjusted_close"] = [1.0, 1.0, 1.0]
    assert N.splits(g) == [("2015-01-06", 4.0)]


def test_correction_8_identical_returns_are_one_security():
    idx = [f"2020-0{m}-{d:02d}" for m in (1, 2, 3) for d in range(1, 29)]
    import random
    rnd = random.Random(1)
    a = [100.0]
    for _ in idx[1:]:
        a.append(a[-1] * (1 + rnd.uniform(-0.03, 0.03)))
    one = pd.DataFrame({"adjusted_close": a}, index=idx)
    two = pd.DataFrame({"adjusted_close": [x / 20 for x in a]}, index=idx)   # split-adjusted apart
    other = pd.DataFrame({"adjusted_close": [x * (1 + 0.001 * i) for i, x in enumerate(a)]}, index=idx)
    day = date(2020, 4, 1)
    assert N.return_signature(one, day) == N.return_signature(two, day)
    assert N.return_signature(one, day) != N.return_signature(other, day)
