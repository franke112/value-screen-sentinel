"""HANDOFF C1: vss/sec_pit.py -- the clip (moved from the backtest) and the
screener's SEC shadow. Synthetic companyfacts only."""
from __future__ import annotations

from datetime import date

from vss import ranking as R
from vss import sec_pit as SP
from vss.fundamentals import STATUS_OK, SeriesPoint, TickerFundamentals


def _d(start, end, val, filed, form="10-K", fp="FY"):
    return {"start": start, "end": end, "val": val, "filed": filed, "form": form, "fp": fp,
            "accn": f"acc-{filed}", "frame": "CY2025"}


def _i(end, val, filed, form="10-K"):
    return {"end": end, "val": val, "filed": filed, "form": form, "fp": "FY", "accn": f"acc-{filed}"}


FACTS = {"facts": {"us-gaap": {
    "OperatingIncomeLoss": {"units": {"USD": [
        _d("2024-01-01", "2024-12-31", 90.0, "2025-02-10"),
        _d("2025-01-01", "2025-12-31", 100.0, "2026-02-10"),
        # restated in a filing AFTER the replay date
        _d("2025-01-01", "2025-12-31", 80.0, "2026-09-01")]}},
    "Revenues": {"units": {"USD": [_d("2025-01-01", "2025-12-31", 1000.0, "2026-02-10")]}},
    "Assets": {"units": {"USD": [_i("2025-12-31", 2000.0, "2026-02-10")]}},
}}}


def test_the_backtest_reads_the_same_clip():
    from tools.backtest import pit
    assert pit.clip is SP.clip and pit.visible is SP.visible


def test_a_restatement_filed_after_asof_is_not_seen():
    cut = SP.clip(FACTS, date(2026, 3, 1), policy="latest")
    vals = [e["val"] for e in cut["facts"]["us-gaap"]["OperatingIncomeLoss"]["units"]["USD"]]
    assert 80.0 not in vals and "frame" not in cut["facts"]["us-gaap"]["Revenues"]["units"]["USD"][0]
    rec = SP.sec_record(FACTS, ticker="EXM", as_of=date(2026, 3, 1))
    ebit = [p for p in rec.series if p.line == SP.EBIT_LINE and p.period_end == date(2025, 12, 31)]
    assert [p.value for p in ebit] == [100.0] and ebit[0].period_months == 12
    later = SP.sec_record(FACTS, ticker="EXM", as_of=date(2026, 10, 1))
    assert [p.value for p in later.series if p.line == SP.EBIT_LINE
            and p.period_end == date(2025, 12, 31)] == [80.0]


def _vendor(ebit, assets=2000.0):
    return TickerFundamentals(
        ticker="EXM", status=STATUS_OK, attempts=1, requests=1,
        series=(SeriesPoint("EXM", SP.EBIT_LINE, date(2025, 12, 31), ebit, "income", 12),
                SeriesPoint("EXM", SP.REVENUE_LINE, date(2025, 12, 31), 1000.0, "income", 12),
                SeriesPoint("EXM", SP.ASSETS_LINE, date(2025, 12, 31), assets, "balance", None)))


def test_the_check_cell():
    sec = R.extract_inputs("EXM", SP.sec_record(FACTS, ticker="EXM", as_of=date(2026, 3, 1),
                                                like=_vendor(100.0)))
    same = R.extract_inputs("EXM", _vendor(100.0))
    assert SP.check(same, sec, _vendor(100.0)) == "ebit: agree; assets: agree"
    off = R.extract_inputs("EXM", _vendor(120.0))
    assert "ebit: vendor 120 vs SEC 100 (20.0%)" in SP.check(off, sec, _vendor(120.0))


def test_the_cache_is_used_within_the_day(tmp_path):
    calls = []

    def fetch(cik):
        calls.append(cik)
        return FACTS
    SP.cached_facts(123, cache=tmp_path, fetch=fetch)
    SP.cached_facts(123, cache=tmp_path, fetch=fetch)
    assert calls == [123] and (tmp_path / "123.json").exists()
