"""E94: g*, the §5 readiness assessment, and the four fences on INDICATIVE.

The fences are the point. An indicative value that leaked into the
watchlist, or acquired an MBP, or was struck off vendor figures, would be a
fair value nobody registered a growth view for — which is the one thing E28
exists to prevent.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from vss.readiness import (GROWTH_VIEWS_DIR, ROUTE_AUTOMATIC, ROUTE_HAND,
                           ROUTE_NEEDS_CIK, STATE_NEEDS_VIEW, STATE_NO_STORE,
                           STATE_READY, STATE_UNVERIFIED, VIEW_REGISTERED,
                           VIEW_UNREADABLE, Readiness, assess,
                           read_growth_view, render_readiness_table,
                           route_for_ticker)

AS_OF = date(2026, 8, 31)
RUN_TS = datetime(2026, 8, 31, 12, 0).astimezone()


# --- the growth view is read strictly, or not at all -----------------------


def test_a_plain_view_reads(tmp_path):
    (tmp_path / "X.md").write_text(
        "# X\n\nBase case FCF growth, 10 years: 4%\nBear: 0%\nBull: 7%\n")
    view = read_growth_view("X", directory=tmp_path)
    assert view.registered and view.base == 0.04
    assert view.bear == 0.0 and view.bull == 0.07


def test_a_unicode_minus_is_read_as_negative(tmp_path):
    """NVR's bear is `−3%` (U+2212). `float()` refuses it and a naive parser
    reads +3%, flipping the sign of a whole case."""
    (tmp_path / "X.md").write_text(
        "Base case FCF growth, 10 years: 2.5%\nBear: −3%\nBull: 6.5%\n")
    view = read_growth_view("X", directory=tmp_path)
    assert view.bear == -0.03


def test_the_real_nvr_view_reads_negative():
    view = read_growth_view("NVR")
    assert view is not None and view.registered
    assert view.base == 0.025 and view.bear == -0.03


def test_a_table_form_view_reads():
    """DECK's file states the three in a markdown table."""
    view = read_growth_view("DECK")
    assert view.registered and view.base == 0.035 and view.bull == 0.08


def test_an_absent_file_is_ABSENT_not_unreadable(tmp_path):
    assert read_growth_view("NOSUCH", directory=tmp_path) is None


def test_a_file_with_no_rates_is_UNREADABLE(tmp_path):
    (tmp_path / "X.md").write_text("# X\n\nSome prose, no rates.\n")
    view = read_growth_view("X", directory=tmp_path)
    assert view.state == VIEW_UNREADABLE
    assert "no base" in view.detail or "bear" in view.detail


def test_two_different_values_for_one_label_REFUSE(tmp_path):
    """Choosing one would be choosing the owner's judgement for him."""
    (tmp_path / "X.md").write_text(
        "Base case FCF growth, 10 years: 3%\nBear: 0%\nBull: 7%\n"
        "\n## An ordinary section\n\nBase case FCF growth, 10 years: 5%\n")
    view = read_growth_view("X", directory=tmp_path)
    assert view.state == VIEW_UNREADABLE
    assert "more than once" in view.detail


def test_the_real_gddy_view_reads_the_LIVE_rates_under_e95():
    """GDDY's file carries the live 3% AND the superseded 5% that E76
    requires be kept. E95's marker lets the parser read the first WITHOUT
    deleting the second."""
    view = read_growth_view("GDDY")
    assert view.registered
    assert view.base == 0.03 and view.bear == 0.01 and view.bull == 0.08
    text = view.path.read_text(encoding="utf-8")
    assert "## SUPERSEDED" in text
    assert "Base case FCF growth, 10 years: 5%" in text   # E76: still kept


def test_prose_mentioning_bear_is_not_read_as_a_rate(tmp_path):
    """GDDY's file contains 'superseded view (fv_base 156.45, bear 111.36...)'
    and a looser pattern would read 111.36 as a growth rate."""
    (tmp_path / "X.md").write_text(
        "Base case FCF growth, 10 years: 3%\nBear: 1%\nBull: 8%\n"
        "\nthe superseded view (fv_base 156.45, bear 111.36, bull 200.58)\n")
    view = read_growth_view("X", directory=tmp_path)
    assert view.registered and view.bear == 0.01


# --- the route -------------------------------------------------------------


def test_a_store_already_on_the_sec_path_is_automatic():
    route, why = route_for_ticker("CTSH", store_origin="sec-xbrl")
    assert route == ROUTE_AUTOMATIC and "SEC XBRL" in why


def test_a_nordic_name_is_automatic():
    route, _ = route_for_ticker("LIAB.ST")
    assert route == ROUTE_AUTOMATIC


def test_a_refusing_host_is_a_hand_download():
    route, why = route_for_ticker("SAP.DE")
    assert route == ROUTE_HAND and "403" in why


def test_a_us_name_without_a_cik_names_the_gap_not_a_wall():
    route, why = route_for_ticker("MU")
    assert route == ROUTE_NEEDS_CIK
    assert "not a closed door" in why


def test_an_unadapted_market_is_a_hand_download():
    route, _ = route_for_ticker("WKL.AS")
    assert route == ROUTE_HAND


# --- readiness -------------------------------------------------------------


def test_a_name_with_no_store_says_so(tmp_path):
    result = assess("NOSUCH", manual_dir=tmp_path, views_dir=tmp_path,
                    as_of=AS_OF, run_ts=RUN_TS)
    assert result.state == STATE_NO_STORE
    assert result.indicative is None and result.g_star is None


def test_a_complete_verified_store_with_a_view_gives_an_indicative_value():
    """CTSH: every leg VERIFIED/tagged, and a view registered 2026-08-27."""
    result = assess("CTSH", price=64.04, quote_currency="USD",
                    as_of=AS_OF, run_ts=RUN_TS)
    assert result.state == STATE_READY
    assert result.zero_hand_inputs
    assert result.indicative is not None
    # The engine and the record are the real ones, so this is the struck
    # figure, not an approximation of it.
    # 84.14 under E117 (2026-09-19; 89.38 as struck under E70): the 192m
    # lease add-back reversed and the 576m operating liability out
    assert abs(result.indicative - 84.16) < 0.01   # 84.14 before the 13m of short-term investments went on file
    assert result.g_star is not None and abs(result.g_star - 0.0018) < 0.001
    assert "growth-views/CTSH.md" in result.indicative_on or \
           "CTSH.md" in result.indicative_on


def test_a_name_whose_view_cannot_be_read_gets_NEEDS_GROWTH_VIEW(tmp_path):
    """A complete, verified store whose VIEW FILE is ambiguous gets no
    indicative value -- and is told the file is the problem, not the store."""
    views = tmp_path / "views"
    views.mkdir()
    (views / "CTSH.md").write_text(
        "Base case FCF growth, 10 years: 4%\nBear: 0%\nBull: 7%\n"
        "\n## An ordinary section\n\nBase case FCF growth, 10 years: 6%\n")
    result = assess("CTSH", price=64.04, quote_currency="USD",
                    as_of=AS_OF, run_ts=RUN_TS, views_dir=views)
    assert result.state == STATE_NEEDS_VIEW
    assert result.indicative is None
    assert "more than once" in result.detail


def test_a_currency_mismatch_refuses_g_star_rather_than_guessing():
    """RMV.L quotes GBX and reports GBP. A g* off by 100x is worse than none."""
    result = assess("RMV.L", price=513.60, quote_currency="GBX",
                    as_of=AS_OF, run_ts=RUN_TS)
    assert result.g_star is None
    assert "NOT ATTEMPTED" in result.g_star_refused
    assert "GBX" in result.g_star_refused and "GBP" in result.g_star_refused


# --- THE FENCES ------------------------------------------------------------


def test_an_indicative_value_never_reaches_the_watchlist(tmp_path):
    """The whole point. Nothing in this path writes config/watchlist.yaml."""
    watchlist = Path("config/watchlist.yaml")
    before = watchlist.read_bytes()

    results = [assess(t, price=p, quote_currency="USD", as_of=AS_OF,
                      run_ts=RUN_TS)
               for t, p in (("CTSH", 64.04), ("GDDY", 97.70), ("ACN", 189.61))]

    assert watchlist.read_bytes() == before
    assert any(r.indicative is not None for r in results), \
        "the fixture must include at least one name that DOES produce one"


def test_an_indicative_value_never_produces_an_mbp():
    """A tier follows a §4.4 score, which follows the E76 reading. A screen
    has done none of them, so there is no tier and no MBP (E28/E90)."""
    result = assess("CTSH", price=64.04, quote_currency="USD", as_of=AS_OF,
                    run_ts=RUN_TS)
    assert result.indicative is not None
    assert not hasattr(result, "mbp")
    assert not hasattr(result, "tier")
    # And the rendered block never prints one.
    text = "\n".join(render_readiness_table([result]))
    assert "MBP" in text          # only in the caveat, saying it never gets one
    assert "never gets an MBP" in text


def test_the_rendered_block_says_it_is_not_a_strike():
    result = assess("CTSH", price=64.04, quote_currency="USD", as_of=AS_OF,
                    run_ts=RUN_TS)
    text = "\n".join(render_readiness_table([result]))
    assert "never written to the watchlist" in text
    assert "is not a strike" in text
    assert "ever formed from screener or Yahoo fundamentals" in text


def test_an_indicative_value_is_never_formed_from_screener_fundamentals(monkeypatch):
    """It comes off the STORE or it does not exist (E94).

    Proved by removing the store: with the manual file gone the name has no
    indicative value at all, even though the screener's own fundamentals for
    it are sitting in the snapshot database untouched.
    """
    result = assess("CTSH", price=64.04, quote_currency="USD", as_of=AS_OF,
                    run_ts=RUN_TS, manual_dir=Path("/nonexistent"))
    assert result.state == STATE_NO_STORE
    assert result.indicative is None
    assert result.g_star is None


def test_the_probe_record_is_never_presented_as_a_view(tmp_path):
    """Where no view is registered the probe uses a placeholder base ONLY to
    reach the legs -- and no value is struck off it."""
    store = Path("config/manual/CTSH.yaml")
    views = tmp_path / "views"
    views.mkdir()
    result = assess("CTSH", price=64.04, quote_currency="USD", as_of=AS_OF,
                    run_ts=RUN_TS, views_dir=views)
    assert result.state == STATE_NEEDS_VIEW
    assert result.indicative is None
    assert store.exists()          # the store itself was not touched


# --- rendering -------------------------------------------------------------


def test_the_table_renders_every_state():
    items = [
        Readiness("A", STATE_READY, route=ROUTE_AUTOMATIC, indicative=89.38,
                  g_star=-0.0059, currency="USD"),
        Readiness("B", STATE_NEEDS_VIEW, route=ROUTE_AUTOMATIC, g_star=0.03),
        Readiness("C", STATE_NO_STORE, route=ROUTE_HAND),
        Readiness("D", STATE_UNVERIFIED, route=ROUTE_AUTOMATIC,
                  blocking=("cash_and_equivalents", "sbc")),
    ]
    text = "\n".join(render_readiness_table(items))
    assert "`A`" in text and "89.38" in text and "-0.59%" in text
    assert "a growth view" in text
    assert "2 UNVERIFIED" in text


def test_a_readiness_line_is_one_line():
    item = Readiness("A", STATE_READY, route=ROUTE_AUTOMATIC, indicative=89.38,
                     g_star=-0.0059, currency="USD")
    assert "\n" not in item.line()
    assert "INDICATIVE 89.38 USD" in item.line()


# --- pence is not pounds ---------------------------------------------------


def test_gbp_and_gbx_are_not_the_same_unit():
    """Case is the WHOLE of the signal in the vendor's label."""
    from vss.readiness import comparable_currencies, currency_unit

    assert currency_unit("GBP") == ("GBP", False)
    assert currency_unit("GBp") == ("GBP", True)
    assert currency_unit("GBX") == ("GBP", True)
    assert currency_unit("USD") == ("USD", False)

    assert not comparable_currencies("GBp", "GBP")
    assert not comparable_currencies("GBX", "GBP")
    assert comparable_currencies("GBP", "GBP")
    assert comparable_currencies("USD", "USD")
    assert not comparable_currencies("USD", "EUR")


def test_a_pence_price_never_reaches_a_pound_value():
    """AUTO.L, RMV.L, RKT.L and IMB.L all read g* +72% to +75% before this:
    a 536p close divided into a 4.82 GBP per-share value."""
    for ticker, price in (("AUTO.L", 536.20), ("RMV.L", 513.60),
                          ("RKT.L", 5116.0), ("IMB.L", 2523.0)):
        result = assess(ticker, price=price, quote_currency="GBp",
                        as_of=AS_OF, run_ts=RUN_TS)
        assert result.g_star is None, f"{ticker} solved a g* it must refuse"
        # E117 (2026-09-19): RKT.L and IMB.L state no lease interest, so no
        # value forms and there is no g* to refuse -- still no pence g*.
        if ticker in ("AUTO.L", "RMV.L"):
            assert "NOT ATTEMPTED" in result.g_star_refused


def test_the_indicative_value_survives_the_currency_refusal():
    """The value needs no price, so a refused g* must not suppress it."""
    result = assess("AUTO.L", price=536.20, quote_currency="GBp",
                    as_of=AS_OF, run_ts=RUN_TS)
    assert result.state == STATE_READY
    assert result.indicative is not None
    assert abs(result.indicative - 4.84) < 0.01      # E117's GBP figure (4.82 under E70)
    assert result.g_star is None


# --- E95: a superseded block is skipped, not deleted -----------------------


def test_a_superseded_block_is_skipped(tmp_path):
    (tmp_path / "X.md").write_text(
        "Base case FCF growth, 10 years: 3%\nBear: 1%\nBull: 8%\n"
        "\n## SUPERSEDED — the first view\n\n"
        "Base case FCF growth, 10 years: 5%\nBear: 0%\nBull: 9%\n")
    view = read_growth_view("X", directory=tmp_path)
    assert view.registered
    assert view.base == 0.03 and view.bear == 0.01 and view.bull == 0.08


def test_the_skip_ends_at_the_next_heading(tmp_path):
    """E95: 'until the next `##` heading' -- rates after it are read again."""
    (tmp_path / "X.md").write_text(
        "## SUPERSEDED\n\nBase case FCF growth, 10 years: 5%\n"
        "\n## The live view\n\n"
        "Base case FCF growth, 10 years: 3%\nBear: 1%\nBull: 8%\n")
    view = read_growth_view("X", directory=tmp_path)
    assert view.registered and view.base == 0.03


def test_the_marker_may_carry_trailing_text(tmp_path):
    """GDDY's reads '## SUPERSEDED — the first view, 2026-08-30 (kept...)'."""
    (tmp_path / "X.md").write_text(
        "Base case FCF growth, 10 years: 3%\nBear: 1%\nBull: 8%\n"
        "\n## SUPERSEDED — the first view, 2026-08-30 (kept, never edited)\n\n"
        "Base case FCF growth, 10 years: 5%\n")
    assert read_growth_view("X", directory=tmp_path).base == 0.03


def test_a_third_level_heading_does_not_open_a_skip(tmp_path):
    (tmp_path / "X.md").write_text(
        "### SUPERSEDED\n\nBase case FCF growth, 10 years: 5%\n"
        "\nBear: 1%\nBull: 8%\n")
    view = read_growth_view("X", directory=tmp_path)
    assert view.registered and view.base == 0.05      # not skipped


def test_ambiguity_OUTSIDE_a_superseded_block_still_refuses(tmp_path):
    """E95 licenses the skip and nothing else. E94's rule is untouched."""
    (tmp_path / "X.md").write_text(
        "Base case FCF growth, 10 years: 3%\nBear: 1%\nBull: 8%\n"
        "\n## Another section\n\nBase case FCF growth, 10 years: 5%\n")
    view = read_growth_view("X", directory=tmp_path)
    assert view.state == VIEW_UNREADABLE
    assert "more than once" in view.detail


def test_gddy_now_produces_an_indicative_value_matching_its_strike():
    result = assess("GDDY", price=97.70, quote_currency="USD", as_of=AS_OF,
                    run_ts=RUN_TS)
    assert result.state == STATE_READY
    # E117 (2026-09-19): 129.03 (132.18 as struck under E70)
    assert abs(result.indicative - 129.03) < 0.01
    assert abs(result.g_star - -0.0023) < 0.0005


# --- E51 / E96: outside the circle beats every other state -----------------


def test_a_commodity_name_is_outside_the_circle_and_gets_no_view_prompt():
    """EXE's store is complete and fully VERIFIED. Before E96 it read
    READY — NEEDS GROWTH VIEW, which asked the owner for the one thing the
    ruling says nobody can write."""
    from vss.readiness import STATE_OUT_OF_CIRCLE

    result = assess("EXE", price=98.16, quote_currency="USD",
                    industry="Oil & Gas E&P", as_of=AS_OF, run_ts=RUN_TS)
    assert result.state == STATE_OUT_OF_CIRCLE
    assert "E96" in result.detail
    assert result.indicative is None
    assert result.g_star is None
    assert "GROWTH VIEW" not in result.state


def test_the_circle_check_runs_before_the_store_is_opened():
    """A name outside the circle needs no store to be judged."""
    from vss.readiness import STATE_OUT_OF_CIRCLE

    result = assess("NOSUCHTICKER", industry="Steel", as_of=AS_OF,
                    run_ts=RUN_TS, manual_dir=Path("/nonexistent"))
    assert result.state == STATE_OUT_OF_CIRCLE
    assert "E96" in result.detail


def test_a_pharma_name_is_caught_by_e51_not_e96():
    from vss.readiness import STATE_OUT_OF_CIRCLE

    result = assess("PFE", as_of=AS_OF, run_ts=RUN_TS)
    assert result.state == STATE_OUT_OF_CIRCLE
    assert "E51" in result.detail and "E96" not in result.detail


def test_an_ordinary_name_is_untouched_by_either_limb():
    result = assess("CTSH", price=64.04, quote_currency="USD",
                    industry="Information Technology Services",
                    as_of=AS_OF, run_ts=RUN_TS)
    assert result.state == STATE_READY
    assert result.indicative is not None


def test_semiconductors_are_not_in_the_commodity_limb():
    """MU is rank 20 and stays in until the owner rules separately (E96)."""
    from vss.readiness import circle_of_competence

    assert circle_of_competence("MU", "Semiconductors") is None
    assert circle_of_competence("MU", "Semiconductor Equipment & Materials") is None


def test_utilities_and_specialty_chemicals_are_not_in_the_commodity_limb():
    from vss.readiness import circle_of_competence

    for industry in ("Utilities - Renewable", "Utilities - Regulated Electric",
                     "Specialty Chemicals", "Building Materials",
                     "Oil & Gas Integrated", "Oil & Gas Midstream"):
        assert circle_of_competence("X", industry) is None, industry


def test_without_an_industry_string_only_the_owner_list_limb_applies():
    """The same blindness E51 and E96 both record: silence is a fact about
    the fetch, not about the company."""
    from vss.readiness import circle_of_competence

    assert circle_of_competence("EXE", None) is None       # string limb blind
    assert circle_of_competence("PFE", None) is not None    # owner list reaches
