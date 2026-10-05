"""E97: the ranked list's price watch — what fires, once, and what never does.

The hysteresis test is the one that matters. A pointer that repeats every
night while a name sits below a level is a pointer the owner stops reading,
and an unread pointer is worse than none.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from vss.pricewatch import (APPROACH_MULTIPLE, BAND_HIGH, BAND_LOW,
                            DEFAULT_TOP_N, EVENT_APPROACH, EVENT_REFERENCE,
                            KIND_DRAWDOWN, KIND_REFERENCE, KIND_SKIPPED,
                            REARM_MARGIN, REFERENCE_CUSHION, Watched,
                            convert_value, crossings, load_state,
                            notification_lines, reference_level, render_table,
                            save_state, watch_ranked)
from vss.readiness import (STATE_NEEDS_VIEW, STATE_OUT_OF_CIRCLE, STATE_READY,
                           Readiness)

AS_OF = date(2026, 8, 31)
RUN_TS = datetime(2026, 8, 31, 22, 30).astimezone()


class Metrics:
    def __init__(self, close=None, drawdown=None, high=None):
        self.last_close, self.drawdown, self.high_52w = close, drawdown, high


def rows(*tickers):
    return [{"ticker": t, "position": i, "section": "ranked"}
            for i, t in enumerate(tickers, start=1)]


def ready(ticker, indicative, currency="USD", quote=None):
    """E98: a store states BOTH currencies, and a conversion needs both."""
    return Readiness(ticker, STATE_READY, indicative=indicative,
                     currency=currency, quote_currency=quote or currency)


# --- the reference is a distance, not a buy line ---------------------------


def test_the_reference_is_the_tier_one_cushion():
    """E90's loosest cushion, chosen because it is the EARLIEST warning."""
    assert REFERENCE_CUSHION == 0.85
    assert reference_level(100.0) == 85.0


def test_a_name_with_a_value_is_watched_on_the_reference():
    watched = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=100.0)},
                           readiness={"AAA": ready("AAA", 100.0)}, as_of=AS_OF)
    item = watched[0]
    assert item.kind == KIND_REFERENCE
    assert item.reference == 85.0
    assert item.approach == pytest.approx(85.0 * APPROACH_MULTIPLE)
    assert item.distance == pytest.approx((100.0 - 85.0) / 85.0)
    assert "NOT A BUY LINE" in item.detail


def test_a_name_without_a_value_is_watched_on_the_drawdown():
    watched = watch_ranked(
        rows("BBB"), prices={"BBB": Metrics(close=80.0, drawdown=0.20)},
        readiness={"BBB": Readiness("BBB", STATE_NEEDS_VIEW)}, as_of=AS_OF)
    item = watched[0]
    assert item.kind == KIND_DRAWDOWN
    assert item.drawdown == 0.20 and item.in_band
    assert "Gate 1" in item.detail


def test_a_drawdown_outside_the_band_is_not_in_band():
    watched = watch_ranked(
        rows("BBB"), prices={"BBB": Metrics(close=99.0, drawdown=0.05)},
        readiness={"BBB": Readiness("BBB", STATE_NEEDS_VIEW)}, as_of=AS_OF)
    assert not watched[0].in_band


# --- a name outside the circle is NEVER watched ---------------------------


def test_a_name_outside_the_circle_is_not_watched_at_all():
    """E97: no level it crosses would mean anything (E51/E96)."""
    watched = watch_ranked(
        rows("EXE"), prices={"EXE": Metrics(close=10.0, drawdown=0.60)},
        readiness={"EXE": Readiness("EXE", STATE_OUT_OF_CIRCLE,
                                    detail="E96: industry 'Oil & Gas E&P'")},
        as_of=AS_OF)
    item = watched[0]
    assert item.kind == KIND_SKIPPED
    assert not item.watched
    assert "outside the circle" in item.detail
    # And it fires nothing, even at a 60% drawdown deep inside the band.
    assert crossings(item, {"fired": {}}, as_of=AS_OF) == []


def test_an_excluded_name_never_reaches_the_pointer():
    watched = watch_ranked(
        rows("EXE"), prices={"EXE": Metrics(close=10.0, drawdown=0.60)},
        readiness={"EXE": Readiness("EXE", STATE_OUT_OF_CIRCLE)}, as_of=AS_OF)
    state = {"fired": {}}
    for item in watched:
        crossings(item, state, as_of=AS_OF)
    assert notification_lines(watched) == []
    assert state == {"fired": {}}


# --- crossings, and ONCE PER CROSSING -------------------------------------


def test_the_approach_rung_fires_at_25_percent_above():
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=106.0)},
                        readiness={"AAA": ready("AAA", 100.0)},
                        as_of=AS_OF)[0]
    # reference 85, approach 106.25 -- a close of 106 is inside it
    assert crossings(item, {"fired": {}}, as_of=AS_OF) == [EVENT_APPROACH]


def test_above_the_approach_nothing_fires():
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=120.0)},
                        readiness={"AAA": ready("AAA", 100.0)},
                        as_of=AS_OF)[0]
    assert crossings(item, {"fired": {}}, as_of=AS_OF) == []


def test_at_the_reference_both_rungs_fire_together_the_first_time():
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=80.0)},
                        readiness={"AAA": ready("AAA", 100.0)},
                        as_of=AS_OF)[0]
    fired = crossings(item, {"fired": {}}, as_of=AS_OF)
    assert set(fired) == {EVENT_REFERENCE, EVENT_APPROACH}


def test_a_level_fires_ONCE_and_not_again_the_next_night():
    """THE ONE THAT MATTERS. A pointer that repeats is one he stops reading."""
    state = {"fired": {}}
    for night in range(5):
        item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=80.0)},
                            readiness={"AAA": ready("AAA", 100.0)},
                            as_of=AS_OF)[0]
        fired = crossings(item, state, as_of=AS_OF)
        if night == 0:
            assert set(fired) == {EVENT_REFERENCE, EVENT_APPROACH}
        else:
            assert fired == [], f"re-fired on night {night}"


def test_a_level_does_not_rearm_on_a_tick_back_over_it():
    """The oscillation the rule exists to prevent, arriving one day later."""
    state = {"fired": {}}
    # night 1: below the reference, fires.
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=84.0)},
                        readiness={"AAA": ready("AAA", 100.0)}, as_of=AS_OF)[0]
    assert EVENT_REFERENCE in crossings(item, state, as_of=AS_OF)
    # night 2: a hair above 85 -- inside the re-arm margin, so still fired.
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=85.5)},
                        readiness={"AAA": ready("AAA", 100.0)}, as_of=AS_OF)[0]
    assert crossings(item, state, as_of=AS_OF) == []
    # night 3: back below -- and it must STILL not re-fire.
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=84.0)},
                        readiness={"AAA": ready("AAA", 100.0)}, as_of=AS_OF)[0]
    assert crossings(item, state, as_of=AS_OF) == []


def test_a_level_rearms_once_the_price_clears_the_margin_and_fires_again():
    state = {"fired": {}}
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=84.0)},
                        readiness={"AAA": ready("AAA", 100.0)}, as_of=AS_OF)[0]
    assert EVENT_REFERENCE in crossings(item, state, as_of=AS_OF)
    # clears 85 * 1.03 = 87.55
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=90.0)},
                        readiness={"AAA": ready("AAA", 100.0)}, as_of=AS_OF)[0]
    assert crossings(item, state, as_of=AS_OF) == []
    # and now a genuine second crossing DOES fire
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=84.0)},
                        readiness={"AAA": ready("AAA", 100.0)}, as_of=AS_OF)[0]
    assert EVENT_REFERENCE in crossings(item, state, as_of=AS_OF)


def test_the_band_event_NEVER_FIRES_under_e97_1():
    """E97.1: filter 1 already rejects anything outside 15-50%, so every
    ranked name is in the band by construction and the event announced what
    the ranking had already said -- fourteen of eighteen on night one.

    A deeper line was offered and REFUSED: a deeper fall is still just a
    price, and this framework does not act on price without a named event.
    THE FIGURE STAYS AND THE POINTER GOES."""
    state = {"fired": {}}
    for drawdown in (0.16, 0.20, 0.35, 0.49, 0.05, 0.16):
        item = watch_ranked(
            rows("BBB"), prices={"BBB": Metrics(close=80.0, drawdown=drawdown)},
            readiness={"BBB": Readiness("BBB", STATE_NEEDS_VIEW)},
            as_of=AS_OF)[0]
        assert crossings(item, state, as_of=AS_OF) == []
    assert state == {"fired": {}}, "the band event touched the cursor"


def test_the_drawdown_figure_is_still_computed_and_printed():
    """E97.1 removes the pointer, not the information."""
    item = watch_ranked(
        rows("BBB"), prices={"BBB": Metrics(close=80.0, drawdown=0.312)},
        readiness={"BBB": Readiness("BBB", STATE_NEEDS_VIEW)}, as_of=AS_OF)[0]
    assert item.drawdown == 0.312 and item.in_band
    assert "31.2%" in "\n".join(render_table([item]))


def test_the_rearm_margin_is_named_as_chosen():
    assert REARM_MARGIN == 0.03


# --- the guards ------------------------------------------------------------


def test_nothing_here_writes_the_watchlist():
    watchlist = Path("config/watchlist.yaml")
    before = watchlist.read_bytes()
    watched = watch_ranked(
        rows("AAA", "BBB"),
        prices={"AAA": Metrics(close=80.0), "BBB": Metrics(close=80.0, drawdown=0.3)},
        readiness={"AAA": ready("AAA", 100.0),
                   "BBB": Readiness("BBB", STATE_NEEDS_VIEW)}, as_of=AS_OF)
    state = {"fired": {}}
    for item in watched:
        crossings(item, state, as_of=AS_OF)
    render_table(watched)
    notification_lines(watched)
    assert watchlist.read_bytes() == before


def test_an_indicative_value_never_becomes_fv_tier_or_mbp():
    """E94's fences are carried here and a price move loosens none of them."""
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=10.0)},
                        readiness={"AAA": ready("AAA", 100.0)},
                        as_of=AS_OF)[0]
    assert item.indicative == 100.0
    for forbidden in ("fv_base", "tier", "mbp"):
        assert not hasattr(item, forbidden)
    text = "\n".join(render_table([item]))
    assert "not a buy line" in text.lower()
    assert "indicative value stays indicative" in text.lower()


def test_the_table_prints_even_when_nothing_fires():
    """A watcher visible only when it fires cannot be checked for being wrong."""
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=200.0)},
                        readiness={"AAA": ready("AAA", 100.0)},
                        as_of=AS_OF)[0]
    assert crossings(item, {"fired": {}}, as_of=AS_OF) == []
    text = "\n".join(render_table([item]))
    assert "`AAA`" in text and "85.00" in text


def test_top_n_is_honoured():
    many = rows(*[f"T{i:02d}" for i in range(1, 41)])
    assert len(watch_ranked(many, prices={}, as_of=AS_OF)) == DEFAULT_TOP_N
    assert len(watch_ranked(many, prices={}, top_n=5, as_of=AS_OF)) == 5


def test_the_state_file_is_a_cursor_and_holds_no_decision(tmp_path):
    path = tmp_path / "pricewatch_state.json"
    state = load_state(path)
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=80.0)},
                        readiness={"AAA": ready("AAA", 100.0)}, as_of=AS_OF)[0]
    crossings(item, state, as_of=AS_OF)
    save_state(state, path)

    reloaded = load_state(path)
    entry = reloaded["fired"]["AAA"][EVENT_REFERENCE]
    assert set(entry) == {"date", "level"}
    for forbidden in ("fv_base", "tier", "mbp", "status", "verdict"):
        assert forbidden not in entry


def test_the_pointer_is_a_pointer_not_a_valuation():
    item = watch_ranked(rows("AAA"), prices={"AAA": Metrics(close=80.0)},
                        readiness={"AAA": ready("AAA", 100.0)}, as_of=AS_OF)[0]
    crossings(item, {"fired": {}}, as_of=AS_OF)
    lines = notification_lines([item])
    assert lines and all(len(line) < 120 for line in lines)
    assert any("not a buy line" in line for line in lines)


# --- the two defects the first live run exposed ---------------------------


def test_a_pence_price_is_CONVERTED_not_refused_under_e98():
    """AUTO.L read +12,791% before the fence, then fell back to its drawdown.
    E98 says a MINOR UNIT IS NOT A RATE: GBX and GBP are the same currency,
    exactly 100 to 1, for ever. So the value converts exactly and the name
    gets its reference back."""
    assessed = Readiness("AUTO.L", STATE_READY, indicative=4.82,
                         currency="GBP", quote_currency="GBX")
    item = watch_ranked(rows("AUTO.L"),
                        prices={"AUTO.L": Metrics(close=528.0, drawdown=0.34)},
                        readiness={"AUTO.L": assessed}, as_of=AS_OF)[0]
    assert item.kind == KIND_REFERENCE
    assert item.indicative == pytest.approx(482.0)          # 4.82 GBP in pence
    assert item.reference == pytest.approx(482.0 * 0.85)
    assert item.distance == pytest.approx((528.0 - 409.7) / 409.7, rel=1e-3)
    # E98: the arithmetic is printed so it can be checked by hand.
    assert "100" in item.conversion and "GBX" in item.conversion


def test_a_cross_currency_value_is_REFUSED_without_a_dated_rate():
    """E98: never a stale rate, and never interpolated."""
    assessed = Readiness("XXX", STATE_READY, indicative=100.0,
                         currency="USD", quote_currency="EUR")
    item = watch_ranked(rows("XXX"),
                        prices={"XXX": Metrics(close=90.0, drawdown=0.30)},
                        readiness={"XXX": assessed}, as_of=AS_OF)[0]
    assert item.kind == KIND_DRAWDOWN
    assert item.reference is None
    assert "could not be converted" in item.detail
    assert "USD->EUR" in item.detail


def test_a_cross_currency_value_converts_with_a_dated_rate():
    from vss.fx import Rate

    seen = {}

    def lookup(base, quote, price_date):
        seen["args"] = (base, quote, price_date)
        return Rate(f"{base}->{quote}", 0.90, date(2026, 8, 28), "test")

    assessed = Readiness("XXX", STATE_READY, indicative=100.0,
                         currency="USD", quote_currency="EUR")
    metrics = Metrics(close=80.0)
    metrics.last_close_date = date(2026, 8, 28)
    item = watch_ranked(rows("XXX"), prices={"XXX": metrics},
                        readiness={"XXX": assessed}, as_of=AS_OF,
                        rate_lookup=lookup)[0]
    assert item.kind == KIND_REFERENCE
    assert item.indicative == pytest.approx(90.0)           # 100 USD x 0.90
    # E98: the rate is asked for THE PRICE'S OWN DATE, never the latest.
    assert seen["args"] == ("USD", "EUR", date(2026, 8, 28))
    # ...and the figure prints the rate and the date it used.
    assert "0.900000" in item.conversion
    assert "2026-08-28" in item.conversion and "test" in item.conversion


def test_a_matching_currency_still_uses_the_reference():
    assessed = Readiness("CTSH", STATE_READY, indicative=89.38,
                         currency="USD", quote_currency="USD")
    item = watch_ranked(rows("CTSH"), prices={"CTSH": Metrics(close=64.58)},
                        readiness={"CTSH": assessed}, as_of=AS_OF)[0]
    assert item.kind == KIND_REFERENCE
    assert item.reference == pytest.approx(89.38 * 0.85)


def test_the_industry_limb_reaches_the_watcher_or_e97_is_broken(
        tmp_path: Path, isolated_vendor_strings: Path):
    """Without an industry string, `assess` applies only the OWNER ticker
    limb -- and NHY.OL and EXE, both caught by E96's strings, were watched
    and fired on the first live run. The watcher supplies the strings.

    THE STRINGS COME FROM THE DURABLE TABLE, NOT FROM A STORE ON DISK. E96
    removes both names at step 0, so no fetch after 2026-08-29 carries
    their strings, and E93 prunes the stores that did; the table exists
    (2026-09-01) so the string limb outlives that pruning. As first written
    on 2026-08-31 this test read the live stores on this machine and passed
    only while one still carried NHY.OL -- it failed the day the last one
    was pruned, with the code correct. `conftest` isolates the table, so
    seed it, and point the store root at an empty directory so nothing on
    this machine is read either way.
    """
    from vss import vendorstrings
    from vss.pricewatch import industry_strings

    vendorstrings.record(isolated_vendor_strings,
                         {"NHY.OL": ("Basic Materials", "Aluminum"),
                          "EXE": ("Energy", "Oil & Gas E&P")},
                         observed=date(2026, 8, 21))
    strings = industry_strings(snapshot_root=tmp_path / "no-stores")
    assert strings, "the durable table was seeded and reads empty"
    assert strings.get("NHY.OL") == "Aluminum"
    assert strings.get("EXE") == "Oil & Gas E&P"


def test_an_e96_name_with_its_string_is_not_watched():
    from datetime import date as _date

    from vss.readiness import assess

    assessed = assess("EXE", industry="Oil & Gas E&P", as_of=AS_OF,
                      run_ts=RUN_TS)
    assert assessed.state == STATE_OUT_OF_CIRCLE
    item = watch_ranked(rows("EXE"),
                        prices={"EXE": Metrics(close=98.16, drawdown=0.20)},
                        readiness={"EXE": assessed}, as_of=AS_OF)[0]
    assert item.kind == KIND_SKIPPED
    assert crossings(item, {"fired": {}}, as_of=AS_OF) == []


# --- E98: the two cases are different things ------------------------------


def test_a_minor_unit_is_exact_dateless_and_sourceless():
    """E98's first half: GBX and GBP are the same currency, 100 to 1, for
    ever. There is no rate to fetch and no staleness to worry about."""
    value, how, refused = convert_value(4.82, reporting="GBP", quote="GBX")
    assert refused == ""
    assert value == pytest.approx(482.0)
    assert how.kind == "unit"
    assert how.as_of is None and how.source == ""
    assert "100" in how.describe()


def test_a_minor_unit_conversion_is_never_refused_for_want_of_a_rate():
    """No price date, no lookup -- and it still converts, because it is
    arithmetic and not a rate."""
    value, how, refused = convert_value(4.82, reporting="GBP", quote="GBX",
                                        price_date=None, rate_lookup=None)
    assert refused == "" and value == pytest.approx(482.0)


def test_the_same_currency_and_unit_is_an_identity():
    value, how, refused = convert_value(89.38, reporting="USD", quote="USD")
    assert value == 89.38 and how.kind == "identity" and how.describe() == ""


def test_a_missing_rate_for_the_date_REFUSES_rather_than_stepping_back():
    """E98: not interpolated, not carried forward from the previous session.
    A rate invented for a date is E25's invented zero in another costume."""
    value, how, refused = convert_value(
        100.0, reporting="USD", quote="EUR", price_date=date(2026, 8, 28),
        rate_lookup=lambda b, q, d: None)
    assert value is None and how is None
    assert "REFUSED" in refused and "not interpolated" in refused
    assert "2026-08-28" in refused


def test_a_lookup_that_raises_is_reported_not_raised():
    def boom(base, quote, price_date):
        raise RuntimeError("network down")

    value, how, refused = convert_value(
        100.0, reporting="USD", quote="EUR", price_date=date(2026, 8, 28),
        rate_lookup=boom)
    assert value is None and "network down" in refused


def test_a_cross_currency_AND_minor_unit_composes_both_factors():
    """A USD-reporting name quoted in pence needs the rate AND the divisor."""
    from vss.fx import Rate

    value, how, refused = convert_value(
        10.0, reporting="USD", quote="GBX", price_date=date(2026, 8, 28),
        rate_lookup=lambda b, q, d: Rate(f"{b}->{q}", 0.80,
                                         date(2026, 8, 28), "test"))
    assert refused == ""
    assert value == pytest.approx(10.0 * 0.80 * 100)     # 800 pence
    assert how.kind == "rate" and how.as_of == date(2026, 8, 28)
    assert "then" in how.detail
