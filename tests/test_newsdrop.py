"""The news-drop screen (vss/newsdrop.py): the mechanical class and the move."""
from datetime import date

import pandas as pd
import pytest

from vss import newsdrop as N


@pytest.mark.parametrize("own,cls", [
    ([("2026-10-29", "8-K", "2.02,9.01")], "B-report"),
    ([("2026-10-29", "10-Q", "")], "B-report"),
    ([("2026-10-28", "8-K", "5.02,9.01")], "B-other"),
    ([("2026-10-28", "8-K", "4.02")], "B-other"),
    ([("2026-10-28", "8-K", "1.01,9.01")], "own-other"),
    ([("2026-10-28", "8-K", "1.01,2.02,7.01,9.01")], "B-report"),     # CSGP: a report wins
    ([], "no-news"),
])
def test_the_mechanical_class(own, cls):
    assert N.sec_class(own) == cls


def _frame(closes, volume=1e7):
    idx = pd.bdate_range("2026-08-01", periods=len(closes))
    return pd.DataFrame({"Close": closes, "Volume": [volume] * len(closes)}, index=idx)


def test_the_move_is_against_the_index_and_the_turnover_is_before_the_day():
    stock = _frame([100.0] * 70 + [80.0])                 # -20% on the last day
    index = _frame([100.0] * 70 + [95.0])["Close"]        # index -5%
    day, r5, r1, turnover = N.moves(stock, index, date(2027, 1, 1))
    assert r5 == pytest.approx(-0.15) and r1 == pytest.approx(-0.15)
    assert turnover == pytest.approx(100.0 * 1e7)         # the drop day not in it


def test_a_short_series_is_none():
    assert N.moves(_frame([100.0] * 4), _frame([100.0] * 4)["Close"], date(2027, 1, 1)) is None


def test_the_universe_reads_both_lists():
    names = N.universe()
    markets = {m for _, _, m, _ in names}
    assert markets == {"US", "Stockholm"} and len(names) > 700


def test_a_disposition_8k_is_a_series_question_not_news():
    assert N.sec_class([("2026-10-01", "8-K", "2.01,9.01")]) == "series"


def test_a_spin_off_sized_day_and_a_split_are_named():
    f = _frame([100.0] * 10 + [16.0])                     # CTVA's -84%
    f["Stock Splits"] = 0.0
    f.iloc[-3, f.columns.get_loc("Stock Splits")] = 2.0
    note = N.series_note(f, f.index[-1].date())
    assert "split 2" in note and "-84%" in note


def test_a_plain_drop_has_no_series_note():
    f = _frame([100.0] * 10 + [85.0])
    assert N.series_note(f, f.index[-1].date()) == ""


@pytest.mark.parametrize("a,b", [("Intrum AB (publ)", "Intrum AB"),
                                 ("Volvo Car AB (publ.)", "Volvo Car AB"),
                                 ("AAK AB (publ.)", "AAK AB")])
def test_publ_and_punctuation_do_not_separate_one_company(a, b):
    assert N._norm(a) == N._norm(b)


def test_the_legal_form_is_not_part_of_the_name():
    assert N._norm("Intrum AB (publ)") == N._norm("Intrum")


def _flag(kind, mclass, ticker="X", verdict=""):
    return N.Flag(ticker, "Name", "US", kind, "2026-10-29", -0.12, -0.02, 1e9, mclass=mclass,
                  close=40.0, verdict=verdict)


def test_only_what_survives_the_sorting_is_worth_a_look():
    flags = [_flag("drop", "B-report"), _flag("drop", "B-pre-report"),
             _flag("drop", "no-news", "CTVA"), _flag("early", "unread", "PSKY"),
             _flag("rise", "no-news")]
    assert [f.ticker for f in N.worth_a_look(flags)] == ["CTVA", "PSKY"]


def test_a_day_of_report_drops_sends_nothing():
    assert N.notify_lines(date(2026, 10, 29), [_flag("drop", "B-report")]) == []


def test_the_message_names_the_file():
    lines = N.notify_lines(date(2026, 10, 29), [_flag("drop", "no-news", "CTVA", "under-fv")])
    assert lines[0].startswith("CTVA") and "reports/NEWSDROP-2026-10-29.md" in lines[-1]


def test_a_fall_over_its_fv_reaches_the_paper_but_not_the_phone():
    flags = [_flag("drop", "no-news", "MRVL", "over-fv"), _flag("drop", "no-news", "ZZ", "quality-fails")]
    assert N.notify_lines(date(2026, 10, 29), flags) == []
    assert "MRVL" in "\n".join(N.today(flags))


def _m(fv, q=True, kills=()):
    return {"status": "ok", "fv_base": fv, "quality": {"Q1": q, "Q2": True}, "kills": list(kills)}


def test_the_verdict_reads_the_buy_line_quality_and_kills():
    assert N.verdict(_m(100), 79) == "under-buy-line"
    assert N.verdict(_m(100), 90) == "under-fv"
    assert N.verdict(_m(100), 110) == "over-fv"
    assert N.verdict(_m(100, q=False), 50) == "quality-fails"
    assert N.verdict(_m(100, kills=["4.2.1"]), 50) == "hard-kill"
    assert N.verdict({"status": "no FCF0"}, 50) == "no-fv"


def test_an_fv_many_times_the_price_is_read_by_a_person_not_bought():
    m = _m(50.72)
    assert N.verdict(m, 11.47) == "no-fv" and "series" in m["status"]


def test_8k_items_are_put_in_words():
    assert N.items_in_words(["2026-10-28 8-K 5.02,9.01"]) == ["2026-10-28 8-K: VD/CFO/styrelse"]


def test_the_morning_summary_says_what_to_read_and_what_was_sorted_away():
    text = "\n".join(N.today([_flag("drop", "B-report", "NOW"),
                              _flag("drop", "no-news", "CTVA", "under-fv")]))
    assert "1 av 1 under maskin-fv" in text and "CTVA" in text and "rapport i fönstret: NOW" in text


def test_a_quiet_day_says_so():
    assert any("Inget att titta på" in l for l in N.today([_flag("drop", "B-report")]))


def test_the_run_writes_the_morning_paper_into_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(N, "scan", lambda asof, limit=None: ([_flag("drop", "no-news", "CTVA")],
                        {"names": 1, "no_prices": 0, "short": 0, "too_small": 0}))
    N.run_newsdrop(asof=date(2026, 10, 29), notify=False, out_dir=tmp_path / "d",
                   reports_dir=tmp_path / "r")
    assert "CTVA" in (tmp_path / "r" / "NEWSDROP-2026-10-29.md").read_text()
