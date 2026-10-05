"""Gate 1's catalyst limb as dated facts (vss/catalyst.py).

The fixtures are HRB's own closes and filings around the 2026-08-12 peak.
"""

from __future__ import annotations

from datetime import date

from vss import catalyst as C
from vss.briefing import Filing

PEAK = date(2026, 8, 12)
TO = date(2026, 9, 17)

CLOSES = [(date(2026, 8, 11), 46.67), (date(2026, 8, 12), 54.18),
          (date(2026, 8, 13), 53.34), (date(2026, 8, 14), 53.92),
          (date(2026, 8, 17), 50.13), (date(2026, 9, 3), 51.10),
          (date(2026, 9, 4), 49.06), (date(2026, 9, 8), 45.89),
          (date(2026, 9, 16), 45.11)]


def test_down_days_are_those_at_or_past_the_threshold_after_the_peak():
    facts = C.price_facts(CLOSES, PEAK, TO)
    assert [d["date"] for d in facts["down_days"]] == [
        "2026-08-17", "2026-09-04", "2026-09-08"]
    assert facts["sessions"] == 7                 # the peak day is not after the peak
    assert facts["largest"]["date"] == "2026-08-17"
    assert round(facts["largest"]["change"], 4) == -0.0703


def test_the_peak_days_own_move_is_reported_and_not_counted_as_a_session():
    facts = C.price_facts(CLOSES, PEAK, TO)
    assert facts["peak_day"]["date"] == "2026-08-12"
    assert round(facts["peak_day"]["change"], 4) == 0.1609


def test_a_session_past_the_window_end_is_not_read():
    facts = C.price_facts(CLOSES, PEAK, date(2026, 9, 7))
    assert [d["date"] for d in facts["down_days"]] == ["2026-08-17", "2026-09-04"]


def test_8k_items_are_decoded_and_the_exhibits_item_dropped():
    assert C.decode_items("2.02,9.01") == ["2.02 Results of Operations and Financial Condition"]
    assert C.decode_items("5.02") == ["5.02 Departure or Appointment of Directors or Certain Officers"]
    assert C.decode_items("9.99") == ["9.99"]          # unknown: kept bare, not guessed
    assert C.decode_items("") == []


def _filing(form, filed, items=""):
    return Filing(form=form, filed=filed, period="", accession=f"0000012659-26-{filed[-2:]}",
                  document="x.htm", cik=12659, items=items)


def test_filings_are_the_news_forms_from_just_before_the_peak_through_the_end():
    filings = [_filing("8-K", "2026-08-01", "8.01"),          # well before the peak
               _filing("8-K", "2026-08-11", "2.02,9.01"),     # the evening before: kept
               _filing("4", "2026-08-20"),                     # insider form: not news
               _filing("10-K", "2026-08-14"),
               _filing("8-K", "2026-09-30", "8.01")]           # after the window
    got = C.filings_in_window(filings, PEAK, TO)
    assert [(f["date"], f["form"]) for f in got] == [("2026-08-11", "8-K"), ("2026-08-14", "10-K")]
    assert got[0]["items"] == ["2.02 Results of Operations and Financial Condition"]
    assert got[0]["url"].startswith("https://www.sec.gov/Archives/edgar/data/12659/")


def test_the_timeline_puts_both_side_by_side_by_date_and_names_no_cause():
    price = C.price_facts(CLOSES, PEAK, TO)
    filings = C.filings_in_window([_filing("8-K", "2026-08-17", "7.01,9.01")], PEAK, TO)
    rows = C.timeline(price, filings)
    assert rows[0].startswith("2026-08-12 PEAK SET")
    assert rows[1].startswith("2026-08-17 DOWN DAY")
    assert rows[2].startswith("2026-08-17 FILED 8-K — 7.01 Regulation FD Disclosure")
    text = " ".join(rows).lower()
    for word in ("catalyst", "because", "caused", "due to", "driven"):
        assert word not in text
