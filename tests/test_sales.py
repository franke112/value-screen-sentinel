"""`vss sales` (FRAMEWORK-EDITS B45): fills against the index from their own
sale date, fixed marks, and the one thing it must never do -- read a price
off a bar for a fill the owner has not entered."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from vss import sales as S
from vss.config import parse_entry
from vss.fetch import FetchResult


def frame(closes: dict[str, float]):
    """A daily frame keyed by ISO date -> Close."""
    index = pd.to_datetime(list(closes))
    return pd.DataFrame({"Close": list(closes.values()),
                         "Volume": [1000.0] * len(closes)}, index=index)


def closes(mapping: dict[str, float], settled: date = date(2026, 8, 29)):
    return S.settled_closes(frame(mapping), settled)


NAME = {"2026-08-20": 100.0, "2026-08-21": 101.0, "2026-08-24": 103.0,
        "2026-08-26": 104.0, "2026-08-28": 110.0}
OMX = {"2026-08-20": 3000.0, "2026-08-21": 3010.0, "2026-08-24": 3020.0,
       "2026-08-26": 3030.0, "2026-08-28": 3040.0}
SPX = {"2026-08-20": 7000.0, "2026-08-21": 7010.0, "2026-08-24": 7020.0,
       "2026-08-26": 7030.0, "2026-08-28": 7050.0}
SETTLED = date(2026, 8, 29)


def entry(**overrides):
    raw = {"ticker": "MSFT", "name": "Microsoft", "currency": "USD",
           "status": "DROPPED"}
    raw.update(overrides)
    return parse_entry(raw, 0)


def index_closes():
    return {"OMXS30": closes(OMX), "S&P 500": closes(SPX)}


# --- settled closes --------------------------------------------------------------


def test_settled_closes_drops_unsettled_bars_and_nan_closes():
    f = frame({"2026-08-27": 1.0, "2026-08-28": float("nan"), "2026-08-31": 3.0})
    got = S.settled_closes(f, date(2026, 8, 29))
    assert list(got.index) == [date(2026, 8, 27)]


def test_close_on_or_before_takes_the_prior_bar_when_the_day_has_none():
    got = S.close_on_or_before(closes(NAME), date(2026, 8, 22))  # a Saturday
    assert got == (101.0, date(2026, 8, 21))


def test_close_on_or_before_is_none_before_the_first_bar():
    assert S.close_on_or_before(closes(NAME), date(2026, 8, 1)) is None


# --- one fill ---------------------------------------------------------------------


def test_a_priced_fill_is_set_against_the_last_settled_close_and_both_indices():
    e = entry(sales=[{"date": "2026-08-21", "price": 100.0, "shares": 4, "rule": "C4"}])
    row = S.fill_row(e, e.sales[0], closes(NAME), index_closes(), SETTLED)
    assert row.priced
    assert row.last == 110.0 and row.last_date == date(2026, 8, 28)
    assert row.price_change == pytest.approx(0.10)
    legs = {leg.label: leg for leg in row.index_legs}
    assert legs["OMXS30"].at_sale == 3010.0 and legs["OMXS30"].at_sale_date == date(2026, 8, 21)
    assert legs["OMXS30"].change == pytest.approx(3040.0 / 3010.0 - 1)
    assert legs["S&P 500"].change == pytest.approx(7050.0 / 7010.0 - 1)


def test_a_fill_with_no_price_is_data_missing_and_the_index_legs_still_form():
    e = entry(sales=[{"date": "2026-08-24", "shares": 42, "rule": "C4"}])
    row = S.fill_row(e, e.sales[0], closes(NAME), index_closes(), SETTLED)
    assert not row.priced
    assert row.price_change is None
    assert row.last == 110.0  # the close is known; the FILL is not
    legs = {leg.label: leg for leg in row.index_legs}
    assert legs["OMXS30"].change == pytest.approx(3040.0 / 3020.0 - 1)
    text = S.render([row], run_ts=datetime(2026, 8, 30, 12, tzinfo=ZoneInfo("Europe/Stockholm")),
                    settled=SETTLED, written_to=None)
    assert "DATA MISSING" in text
    assert "never read off a bar" in text or "nothing here reads it off a bar" in text


def test_a_sale_on_a_day_with_no_index_bar_starts_from_the_prior_index_close():
    e = entry(sales=[{"date": "2026-08-22", "price": 101.0, "shares": 1, "rule": "owner"}])
    row = S.fill_row(e, e.sales[0], closes(NAME), index_closes(), SETTLED)
    leg = next(l for l in row.index_legs if l.label == "OMXS30")
    assert leg.at_sale_date == date(2026, 8, 21) and leg.at_sale == 3010.0


# --- the fixed marks -----------------------------------------------------------------


def test_marks_are_not_yet_until_the_mark_date_has_settled():
    e = entry(sales=[{"date": "2026-08-21", "price": 100.0, "shares": 1, "rule": "C4"}])
    row = S.fill_row(e, e.sales[0], closes(NAME), index_closes(), SETTLED)
    assert [m.days for m in row.marks] == list(S.MARK_DAYS)
    assert all(not m.reached for m in row.marks)
    assert row.marks[0].mark_date == date(2026, 9, 20)
    text = S.render([row], run_ts=datetime(2026, 8, 30, 12, tzinfo=ZoneInfo("Europe/Stockholm")),
                    settled=SETTLED, written_to=None)
    assert "not yet (2026-09-20)" in text


def test_a_reached_mark_reads_the_close_on_or_before_the_mark_date():
    long_name = {(date(2026, 1, 1) + timedelta(days=i)).isoformat(): 100.0 + i
                 for i in range(0, 200, 1)}
    long_omx = {(date(2026, 1, 1) + timedelta(days=i)).isoformat(): 3000.0 + i
                for i in range(0, 200, 1)}
    settled = date(2026, 7, 15)
    e = entry(sales=[{"date": "2026-02-01", "price": 120.0, "shares": 1, "rule": "C1"}])
    row = S.fill_row(e, e.sales[0], closes(long_name, settled),
                     {"OMXS30": closes(long_omx, settled)}, settled)
    m30, m90, m365 = row.marks
    assert m30.reached and m30.mark_date == date(2026, 3, 3)
    # 2026-03-03 is day index 61 -> close 161.0
    assert m30.name_close == 161.0 and m30.name_change == pytest.approx(161.0 / 120.0 - 1)
    omx = dict(m30.index_changes)["OMXS30"]
    assert omx == pytest.approx(3061.0 / 3031.0 - 1)  # 02-01 is index 31
    assert m90.reached and not m365.reached


# --- the command -----------------------------------------------------------------------


def test_run_sales_reads_only_entries_with_a_sales_block_and_writes_the_record(tmp_path):
    watchlist = tmp_path / "watchlist.yaml"
    watchlist.write_text(
        "tickers:\n"
        "  - ticker: MSFT\n    name: Microsoft\n    currency: USD\n    status: DROPPED\n"
        "    sales:\n      - date: 2026-08-21\n        price: 100.0\n        shares: 4\n"
        "        rule: C4\n        proceeds_sek: 18185.66\n        account: 'ACCOUNT-B'\n"
        "  - ticker: SAP.DE\n    name: SAP SE\n    currency: EUR\n    status: WATCH-PRICED\n"
        "    sales:\n      - date: 2026-08-26\n        shares: 6\n        rule: C4\n"
        "  - ticker: NKE\n    name: Nike\n    currency: USD\n    status: DROPPED\n",
        encoding="utf-8")
    frames = {"MSFT": frame(NAME), "SAP.DE": frame(NAME), "^OMX": frame(OMX),
              "^GSPC": frame(SPX)}
    asked = []

    def fetch(ticker):
        asked.append(ticker)
        return FetchResult(ticker, frames[ticker], "live", None)

    now = datetime(2026, 8, 30, 12, tzinfo=ZoneInfo("Europe/Stockholm"))
    code, text = S.run_sales(watchlist_path=watchlist, reports_dir=tmp_path / "reports",
                             now=now, fetch=fetch)
    assert code == 0
    assert "NKE" not in asked and set(asked) == {"MSFT", "SAP.DE", "^OMX", "^GSPC"}
    assert "`MSFT`" in text and "`SAP.DE`" in text
    assert "+10.0%" in text            # MSFT 100 -> 110
    assert "18,185.66" in text
    assert "DATA MISSING" in text      # SAP.DE has no fill price
    written = tmp_path / "reports" / "SALES-RECORD-2026-08-30.md"
    assert written.exists() and written.read_text(encoding="utf-8").startswith("# vss sales")
    assert "3 fill" not in text and "2 fill(s) across 2 position(s), 1 priced" in text


def test_run_sales_dry_run_writes_nothing(tmp_path):
    watchlist = tmp_path / "watchlist.yaml"
    watchlist.write_text(
        "tickers:\n  - ticker: MSFT\n    name: Microsoft\n    currency: USD\n"
        "    status: DROPPED\n    sales:\n      - date: 2026-08-21\n        price: 100.0\n"
        "        shares: 1\n        rule: C4\n", encoding="utf-8")
    frames = {"MSFT": frame(NAME), "^OMX": frame(OMX), "^GSPC": frame(SPX)}
    now = datetime(2026, 8, 30, 12, tzinfo=ZoneInfo("Europe/Stockholm"))
    code, text = S.run_sales(watchlist_path=watchlist, reports_dir=tmp_path / "reports",
                             now=now, dry_run=True,
                             fetch=lambda t: FetchResult(t, frames[t], "live", None))
    assert code == 0 and "DRY RUN" in text
    assert not (tmp_path / "reports").exists()


def test_a_name_whose_prices_cannot_be_fetched_is_named_not_dropped(tmp_path):
    watchlist = tmp_path / "watchlist.yaml"
    watchlist.write_text(
        "tickers:\n  - ticker: XXX.ST\n    name: Gone AB\n    currency: SEK\n"
        "    status: DROPPED\n    sales:\n      - date: 2026-08-21\n        price: 10.0\n"
        "        shares: 1\n        rule: C2\n", encoding="utf-8")
    frames = {"^OMX": frame(OMX), "^GSPC": frame(SPX)}

    def fetch(t):
        if t in frames:
            return FetchResult(t, frames[t], "live", None)
        return FetchResult(t, None, "none", None, "delisted")

    now = datetime(2026, 8, 30, 12, tzinfo=ZoneInfo("Europe/Stockholm"))
    code, text = S.run_sales(watchlist_path=watchlist, reports_dir=tmp_path / "reports",
                             now=now, dry_run=True, fetch=fetch)
    assert code == 0 and "`XXX.ST`" in text and "delisted" in text
