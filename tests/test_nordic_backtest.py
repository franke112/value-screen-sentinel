"""tools/backtest/nordic.py's translation guards. Synthetic data only."""
from __future__ import annotations

from datetime import date

import pytest
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
    # 100 -> 25 against a flat adjusted close: 4:1; 25 -> 18.25 (0.73): a spin-off
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


# ---- K1 (independent review 2026-11-07): reporting currency != trading currency

def _fx(frm, to, day):
    usd = {"USD": 1.0, "EUR": 1.1, "SEK": 0.1, "NOK": 0.1, "DKK": 0.15}
    return usd[frm] / usd[to]


def _file(trading, rows):
    """rows: (period end, label, revenue)."""
    hist = {pe: {"date": pe, "reportDate": pe} for pe, _, _ in rows}
    inc = {pe: {"currency_symbol": c, "totalRevenue": str(v),
                "filing_date": pe[:4] + "-12-31" if pe[5:] != "12-31" else str(int(pe[:4]) + 1) + "-02-10"}
           for pe, c, v in rows}
    return {"General": {"CurrencyCode": trading}, "Earnings": {"History": hist},
            "Financials": {"Income_Statement": {"yearly": inc}}}


def _revenue(facts):
    return {e["end"]: e["val"] for e in facts["facts"]["us-gaap"]["Revenues"]["units"]["USD"]}


def test_a_euro_reporting_krona_listed_company_is_converted_to_kronor():
    d = _file("SEK", [("2024-12-31", "EUR", 2000.0), ("2025-12-31", "EUR", 2100.0)])
    rev = _revenue(N.facts_from_eodhd("EVO.ST", d, fx=_fx))
    assert rev["2025-12-31"] == 2100.0 * 11            # EUR 1.1 / SEK 0.1


def test_the_same_currency_is_left_alone():
    d = _file("SEK", [("2025-12-31", "SEK", 20360.0)])
    assert _revenue(N.facts_from_eodhd("ACAD.ST", d, fx=_fx))["2025-12-31"] == 20360.0


def test_a_label_switch_the_figures_do_not_show_is_overruled_by_the_later_label():
    # Stora Enso: euro figures labelled SEK until 2023, EUR after; revenue continuous
    rows = [("2022-12-31", "SEK", 11680.0), ("2023-12-31", "SEK", 9396.0), ("2024-12-31", "EUR", 9049.0)]
    N.RELABELLED.clear()
    rev = _revenue(N.facts_from_eodhd("STE-R.ST", _file("SEK", rows), fx=_fx))
    assert rev["2022-12-31"] == 11680.0 * 11 and rev["2024-12-31"] == 9049.0 * 11
    assert N.RELABELLED and N.RELABELLED[0][0] == "STE-R.ST"


def test_a_relabel_is_carried_back_only_to_the_real_switch():
    # Tomra: NOK to EUR for 2024 under a NOK label, EUR label from 2025;
    # the EUR label must not reach the NOK years before 2024
    rows = [("2022-12-31", "NOK", 12188.0), ("2023-12-31", "NOK", 14756.0),
            ("2024-12-31", "NOK", 1348.0), ("2025-12-31", "EUR", 1318.0)]
    rev = _revenue(N.facts_from_eodhd("TOM.OL", _file("NOK", rows), fx=_fx))
    assert rev["2022-12-31"] == 12188.0 and rev["2023-12-31"] == 14756.0
    assert rev["2024-12-31"] == 1348.0 * 11 and rev["2025-12-31"] == 1318.0 * 11


def test_a_relabel_stops_at_a_switch_that_holds_and_not_at_noise():
    # Tomra's quarters: NOK to EUR in Q4 2024 under a NOK label, EUR label from Q3 2025
    rows = [("2023-12-31", "NOK", 4123.0), ("2024-03-31", "NOK", 3322.0), ("2024-12-31", "NOK", 397.6),
            ("2025-03-31", "NOK", 306.0), ("2025-06-30", "NOK", 325.0), ("2025-09-30", "EUR", 306.0)]
    d = _file("NOK", rows)
    fixed, _, problem = N.correct_labels(d, N.report_currencies(d), _fx)
    assert problem is None
    assert fixed["2023-12-31"] == fixed["2024-03-31"] == "NOK"
    assert all(fixed[p] == "EUR" for p in ("2024-12-31", "2025-03-31", "2025-06-30", "2025-09-30"))
    # an investment company's revenue: one dip by about the rate, not held -> no switch
    rows = [("2015-12-31", "SEK", 140.0), ("2016-12-31", "SEK", 150.0), ("2017-12-31", "SEK", 14.0),
            ("2018-12-31", "SEK", 160.0), ("2019-12-31", "SEK", 145.0), ("2020-12-31", "USD", 150.0)]
    d = _file("SEK", rows)
    fixed, _, _ = N.correct_labels(d, N.report_currencies(d), _fx)
    assert all(v == "USD" for v in fixed.values())


def test_a_real_switch_is_kept():
    # Pexip: NOK until 2025, USD from 2026, the revenue drops by the rate
    rows = [("2024-12-31", "NOK", 1100.0), ("2025-12-31", "NOK", 1230.0), ("2026-12-31", "USD", 130.0)]
    rev = _revenue(N.facts_from_eodhd("PEXIP.OL", _file("NOK", rows), fx=_fx))
    assert rev["2025-12-31"] == 1230.0 and rev["2026-12-31"] == 1300.0


def test_a_switch_that_fits_neither_reading_refuses_the_file():
    rows = [("2023-12-31", "DKK", 7462.0), ("2024-12-31", "EUR", 2002.0)]   # merger year
    N.CURRENCY_REFUSED.clear()
    facts = N.facts_from_eodhd("NSIS-B.CO", _file("DKK", rows), fx=_fx)
    assert facts["facts"]["us-gaap"] == {}
    assert "fits neither" in N.CURRENCY_REFUSED[0][1]


def test_no_currency_anywhere_is_refused_not_assumed():
    rows = [("2025-12-31", None, 100.0)]
    N.CURRENCY_REFUSED.clear()
    assert N.facts_from_eodhd("X.ST", _file("SEK", rows), fx=_fx)["facts"]["us-gaap"] == {}
    assert N.CURRENCY_REFUSED


def test_finnish_markka_goes_through_the_peg():
    assert abs(N.fx_factor("FIM", "EUR", date(1999, 6, 30)) - 1 / 5.94573) < 1e-12
    assert abs(N.fx_factor("EUR", "FIM", date(1999, 6, 30)) - 5.94573) < 1e-12


def test_the_screen_says_so_when_its_data_is_old_or_the_refresh_failed(tmp_path, monkeypatch):
    import os
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import nordic_screen as NS
    f = tmp_path / "X.ST.json.gz"
    f.write_bytes(b"")
    monkeypatch.setattr(NS.N, "FUND", tmp_path)
    assert NS.stale_warning(0) is None
    assert "misslyckades" in NS.stale_warning(1)
    old = f.stat().st_mtime - 30 * 86400
    os.utime(f, (old, old))
    assert "30 dagar" in NS.stale_warning(0)


def test_an_adjusted_close_that_jumps_alone_refuses_the_return():
    """M4 (review 2026-11-07): KOG.OL 2022-05-12, adjusted +36% on a close of -2.4%."""
    from tools.backtest import eodhd_reprice as EP
    f = pd.DataFrame({"close": [328.0, 320.0, 322.0], "adjusted_close": [31.47, 42.78, 43.05],
                      "volume": [1, 1, 1]}, index=["2022-05-11", "2022-05-12", "2022-05-13"])
    assert EP.suspect_days(f, date(2022, 5, 1), date(2022, 5, 31)) == ["2022-05-12"]
    ret, how = EP.total_return(f, date(2022, 5, 11), date(2022, 5, 13), "bust")
    assert ret is None and how.startswith("adjustment suspect")
    # a real 5:1 split: the printed close falls, the adjusted one does not
    g = pd.DataFrame({"close": [1797.5, 369.15], "adjusted_close": [289.43, 297.19], "volume": [1, 1]},
                     index=["2025-06-02", "2025-06-03"])
    assert EP.suspect_days(g, date(2025, 6, 1), date(2025, 6, 30)) == []


def test_a_level_break_ends_the_company_there():
    """M2 (review 2026-11-08): HIQ.ST was bought out at ~72 and the ticker then
    carried another security at 0.09; both series fell together, so M4 could
    not see it, and the takeover read as a total loss."""
    from tools.backtest import eodhd_reprice as EP
    days = pd.bdate_range("2017-05-01", "2021-12-31").strftime("%Y-%m-%d")
    cut = list(days).index("2020-11-09")
    px = [54.5 + 17.6 * i / cut for i in range(cut)] + [0.0945] * (len(days) - cut)
    f = pd.DataFrame({"close": px, "adjusted_close": px, "volume": 1}, index=days)
    assert EP.level_breaks(f, date(2017, 5, 1), date(2022, 5, 1)) == ["2020-11-09"]
    ret, how = EP.total_return(f, date(2017, 5, 1), date(2022, 5, 2), "bust")
    assert how == "delisted-last" and ret == pytest.approx(72.1 / 54.5 - 1, abs=0.01)
    # a series that came back after more than a year away is another security
    g = pd.DataFrame({"close": [39.9, 1665.0], "adjusted_close": [39.83, 1665.0], "volume": 1},
                     index=["2017-10-30", "2020-01-24"])
    assert EP.level_breaks(g, date(2017, 1, 1), date(2021, 1, 1)) == ["2020-01-24"]
    # a break in the year before the start: the start price itself is suspect
    h = pd.DataFrame({"close": [1102.2, 0.0206, 0.0133], "adjusted_close": [66132.0, 1.236, 0.8],
                      "volume": 1}, index=["2016-12-15", "2016-12-16", "2017-05-01"])
    ret, how = EP.total_return(h, date(2017, 5, 1), date(2020, 5, 1), "bust")
    assert ret is None and "before the start" in how
    # an ordinary fall of 60% in a day is not a break
    k = pd.DataFrame({"close": [10.0, 4.0], "adjusted_close": [10.0, 4.0], "volume": 1},
                     index=["2019-01-02", "2019-01-03"])
    assert EP.level_breaks(k, date(2019, 1, 1), date(2019, 2, 1)) == []


def test_a_quarter_starts_three_months_before_its_end():
    from datetime import date as _d
    for end, start in (("2018-03-31", "2018-01-01"), ("2018-06-30", "2018-04-01"),
                       ("2018-09-30", "2018-07-01"), ("2017-12-31", "2017-10-01"),
                       ("2019-02-28", "2018-12-01")):
        assert N.quarter_start(_d.fromisoformat(end)) == _d.fromisoformat(start)


def _screen():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import nordic_screen as NS
    return NS


def _sfile(capex_by_year, revenue=1000.0, lease=None, total=None):
    cf = {f"{y}-12-31": {"capitalExpenditures": str(-c)} for y, c in capex_by_year.items()}
    inc = {f"{y}-12-31": {"totalRevenue": str(revenue)} for y in capex_by_year}
    bs = {f"{y}-12-31": {"capitalLeaseObligations": None if lease is None else str(lease),
                         "shortLongTermDebtTotal": None if total is None else str(total)}
          for y in capex_by_year}
    return {"Financials": {"Cash_Flow": {"yearly": cf, "quarterly": {}},
                           "Income_Statement": {"yearly": inc, "quarterly": {}},
                           "Balance_Sheet": {"yearly": bs, "quarterly": {}}}}


def test_a_capex_that_vanishes_in_the_newest_year_is_a_vendor_gap_not_a_saving():
    NS = _screen()
    assert "capex fault" in NS.capex_gap(_sfile({2022: 400, 2023: 380, 2024: 410, 2025: 27}))
    assert NS.capex_gap(_sfile({2022: 400, 2023: 380, 2024: 410, 2025: 300})) is None
    # a company with almost no capex is not flagged for having less
    assert NS.capex_gap(_sfile({2022: 3, 2023: 4, 2024: 3, 2025: 0.5})) is None


def test_the_screen_charges_rent_once_capex_up_and_the_lease_out_of_debt():
    NS = _screen()
    d = _sfile({2025: 100}, lease=1000, total=3000)
    NS.charge_leases(d)
    capex = float(d["Financials"]["Cash_Flow"]["yearly"]["2025-12-31"]["capitalExpenditures"])
    debt = float(d["Financials"]["Balance_Sheet"]["yearly"]["2025-12-31"]["shortLongTermDebtTotal"])
    assert capex == 100 + NS.LEASE_PAYMENT_RATE * 1000
    assert debt == 2000


def test_an_empty_debt_total_is_read_from_its_parts_not_as_no_debt():
    assert N.BALANCE["longTermDebt"] == "LongTermDebtNoncurrent"
    assert N.BALANCE["shortTermDebt"] == "DebtCurrent"
