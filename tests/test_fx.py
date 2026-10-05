"""Exchange rates, and the minor-unit trap that would poison the ranking."""

from __future__ import annotations

from datetime import date

import pytest

from vss.fx import (
    MINOR_UNITS,
    FxTable,
    Rate,
    build_table,
    describe,
    major_unit,
    pairs_needed,
    upper_safe_code,
)


# --- the GBp/GBP scaling ---------------------------------------------------
#
# The owner made this its own test. A silent factor of a hundred on British
# names would divide their enterprise value by 100, multiply their earnings
# yield by 100, and put every one of them at the top of the only ordering the
# tool produces. It is the bug that does the most damage and shows the least.


def test_gbp_pence_resolves_to_pounds():
    assert major_unit("GBp") == "GBP"
    assert major_unit("GBX") == "GBP"


def test_pounds_stay_pounds():
    assert major_unit("GBP") == "GBP"


def test_the_mapping_is_case_sensitive_because_the_codes_are():
    """"GBp" and "GBP" are different codes meaning different units."""
    assert "GBp" in MINOR_UNITS
    assert "GBP" not in MINOR_UNITS


def test_other_minor_units_resolve_too():
    assert major_unit("ZAc") == "ZAR"
    assert major_unit("ILA") == "ILS"


def test_an_ordinary_currency_is_returned_unchanged():
    for code in ("USD", "EUR", "SEK", "CHF", "NOK", "DKK", "PLN"):
        assert major_unit(code) == code


def test_whitespace_does_not_defeat_the_mapping():
    assert major_unit(" GBp ") == "GBP"


def test_no_currency_is_none_not_a_guess():
    assert major_unit(None) is None
    assert major_unit("") is None


def test_a_pence_quoted_name_needs_no_conversion_against_pounds():
    """The whole point: GBp and GBP are the same currency, not a 100x pair."""
    table = FxTable()
    rate = table.get("GBp", "GBP")
    assert rate is not None
    assert rate.value == 1.0
    assert rate.source == "identity"


def test_a_pence_to_dollars_pair_is_fetched_as_pounds_to_dollars():
    calls = []

    def lookup(base, quote):
        calls.append((base, quote))
        return 1.27, date(2026, 8, 21), f"{base}{quote}=X"

    table = build_table([("GBp", "USD")], lookup=lookup)
    assert calls == [("GBP", "USD")]
    assert table.get("GBp", "USD").value == 1.27


def test_pence_and_pounds_collapse_to_one_fetch():
    assert pairs_needed([("GBp", "USD"), ("GBP", "USD")]) == [("GBP", "USD")]


# --- pairs and fetching ----------------------------------------------------


def test_identity_pairs_are_never_fetched():
    assert pairs_needed([("EUR", "EUR"), ("SEK", "SEK")]) == []


def test_pairs_are_deduplicated_and_sorted():
    pairs = pairs_needed([("SEK", "USD"), ("EUR", "USD"), ("SEK", "USD")])
    assert pairs == [("EUR", "USD"), ("SEK", "USD")]


def test_a_pair_with_a_missing_side_is_dropped():
    assert pairs_needed([(None, "USD"), ("SEK", None)]) == []


def test_a_fetched_rate_carries_its_date_and_source():
    table = build_table([("SEK", "USD")],
                        lookup=lambda b, q: (0.105, date(2026, 8, 21), f"{b}{q}=X"))
    rate = table.get("SEK", "USD")
    assert rate.value == 0.105
    assert rate.as_of == date(2026, 8, 21)
    assert rate.source == "SEKUSD=X"


def test_conversion_applies_the_rate():
    rate = Rate("SEK->USD", 0.1, date(2026, 8, 21), "x")
    assert rate.convert(1000.0) == pytest.approx(100.0)


def test_a_failed_pair_is_recorded_and_never_becomes_parity():
    """A missing rate treated as 1.0 is an error the size of the rate."""
    def lookup(base, quote):
        raise RuntimeError("no rows")

    table = build_table([("SEK", "USD")], lookup=lookup)
    assert table.get("SEK", "USD") is None
    assert "SEK->USD" in table.failures


def test_a_non_positive_rate_is_refused():
    table = build_table([("SEK", "USD")], lookup=lambda b, q: (0.0, None, "x"))
    assert table.get("SEK", "USD") is None
    assert "non-positive" in table.failures["SEK->USD"]


def test_the_manifest_carries_every_rate_and_every_failure():
    def lookup(base, quote):
        if base == "SEK":
            return 0.105, date(2026, 8, 21), "SEKUSD=X"
        raise RuntimeError("boom")

    table = build_table([("SEK", "USD"), ("PLN", "USD")], lookup=lookup)
    manifest = table.as_manifest()
    assert any(k.startswith("fx:SEK->USD") for k in manifest)
    assert any(k.startswith("fx_failed:PLN->USD") for k in manifest)


def test_describe_reports_rates_and_failures():
    table = build_table([("SEK", "USD")],
                        lookup=lambda b, q: (0.105, date(2026, 8, 21), "SEKUSD=X"))
    text = describe(table)
    assert "SEK->USD" in text and "0.105" in text and "2026-08-21" in text
    assert describe(FxTable()) == "  (no conversion needed)"


# --- codes that must survive being upper-cased -----------------------------
#
# The watchlist loader upper-cases whatever currency it stores. "GBp" comes
# back "GBP", and a price of 4161 pence then reads as 4161 pounds -- a
# hundredfold error on any stop entered against it, in the file that holds
# real positions.


def test_pence_is_written_as_gbx_not_gbp():
    assert upper_safe_code("GBp") == "GBX"
    assert upper_safe_code("GBX") == "GBX"


def test_the_safe_code_is_a_fixed_point_under_upper():
    for code in ("GBp", "GBX", "ZAc", "ILA", "SEK", "EUR", "usd"):
        safe = upper_safe_code(code)
        assert safe == safe.upper(), code


def test_the_safe_code_never_promotes_a_minor_unit_to_its_major():
    """The whole point: GBp must not become GBP by any route."""
    from vss.fx import major_unit

    assert upper_safe_code("GBp") != major_unit("GBp")
    assert upper_safe_code("ZAc") != major_unit("ZAc")


def test_an_ordinary_code_is_simply_upper_cased():
    assert upper_safe_code("sek") == "SEK"
    assert upper_safe_code("EUR") == "EUR"


def test_no_currency_stays_none():
    assert upper_safe_code(None) is None
    assert upper_safe_code("") is None


# --- K7: replay, and the difference between auditable and reproducible ------


MANIFEST = {
    "asof": "2026-08-21",
    "fx": {
        "SEK->USD": {"rate": 0.10568, "as_of": "2026-08-22", "source": "SEKUSD=X"},
        "GBP->EUR": {"rate": 1.1676, "as_of": "2026-08-21", "source": "GBPEUR=X"},
    },
    "fx_failed": {},
}


def _manifest(tmp_path):
    import json
    path = tmp_path / "ranking-manifest.json"
    path.write_text(json.dumps(MANIFEST), encoding="utf-8")
    return path


def test_a_stored_run_can_be_replayed_rate_for_rate(tmp_path):
    from vss.fx import build_table, lookup_from_manifest

    table = build_table([("SEK", "USD"), ("GBp", "EUR")],
                        lookup=lookup_from_manifest(_manifest(tmp_path)))
    assert table.get("SEK", "USD").value == 0.10568
    assert table.get("GBp", "EUR").value == 1.1676
    assert table.failures == {}


def test_the_replayed_rate_keeps_its_OWN_date_not_the_replay_date(tmp_path):
    """The 2026-08-21 run carries two pairs dated 08-22. Stamping the replay
    date onto them would erase exactly the evidence this flag exists to show."""
    from vss.fx import read_manifest_rates

    rates = read_manifest_rates(_manifest(tmp_path))
    assert rates["SEK->USD"].as_of == date(2026, 8, 22)
    assert rates["GBP->EUR"].as_of == date(2026, 8, 21)
    assert len({r.as_of for r in rates.values()}) == 2, \
        "one run, two currency dates -- and it must stay visible"


def test_a_pair_the_manifest_lacks_FAILS_and_is_never_quietly_fetched(tmp_path):
    """A reproduction that is partly a new run is neither."""
    from vss.fx import build_table, lookup_from_manifest

    table = build_table([("SEK", "USD"), ("JPY", "USD")],
                        lookup=lookup_from_manifest(_manifest(tmp_path)))
    assert table.get("SEK", "USD") is not None
    assert table.get("JPY", "USD") is None, "an unrecorded pair was invented"
    assert "JPY->USD" in table.failures
    assert "cannot be reproduced" in table.failures["JPY->USD"]


def test_the_replayed_source_says_it_was_replayed(tmp_path):
    """A report that could not tell a replay from a fetch would let one be
    mistaken for the other, which is the whole finding."""
    from vss.fx import read_manifest_rates

    rates = read_manifest_rates(_manifest(tmp_path))
    assert "replayed from manifest" in rates["SEK->USD"].source


def test_the_default_lookup_takes_the_LATEST_close_whatever_asof_says():
    """Checked on the source, because the behaviour is a network call.

    This is the whole of K7: the flag exists because the default cannot be
    made asof-aware -- yfinance's FX series is asked for a PERIOD, not a date.
    """
    import ast
    from pathlib import Path as _P

    source = _P("vss/fx.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "default_lookup")
    body = ast.get_source_segment(source, function)
    assert 'period="5d"' in body
    assert "iloc[-1]" in body
    assert "as_of" not in body, \
        "default_lookup now takes a date; K7's premise changed and the docs must too"


# --- L5: the manifest's own date, read rather than ignored -----------------


def test_a_manifest_says_which_day_its_rates_belong_to(tmp_path):
    import json
    from datetime import date

    from vss.fx import manifest_asof

    path = tmp_path / "m.json"
    path.write_text(json.dumps({"asof": "2026-08-21", "fx": {}}), encoding="utf-8")
    assert manifest_asof(path) == date(2026, 8, 21)


def test_a_manifest_without_the_field_answers_None_not_a_guess(tmp_path):
    import json

    from vss.fx import manifest_asof

    path = tmp_path / "m.json"
    path.write_text(json.dumps({"fx": {}}), encoding="utf-8")
    assert manifest_asof(path) is None
