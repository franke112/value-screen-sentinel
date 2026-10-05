"""Universe loading: schema validation, exclusions, dedup, floors."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pytest

from vss.universe import (
    EXCLUDE,
    INCLUDE,
    ON_MISSING,
    ON_VALUE,
    SCHEMA,
    UNKNOWN,
    Instrument,
    UniverseError,
    apply_type_exclusions,
    dedupe,
    dual_listing_candidates,
    isin_check_digit_ok,
    load_floors,
    load_type_rules,
    load_universe,
    read_list,
    require_yahoo_mapping,
    yield_table,
)

ROW = {
    "ticker_yahoo": "SAP.DE",
    "ticker_lokal": "SAP",
    "isin": "DE0007164600",
    "namn": "SAP SE",
    "marknad": "Xetra",
    "tier": "A",
    "listdatum": "1998-04-09",
    "valuta": "EUR",
    "instrumenttyp": "Equity",
}

TYPE_RULES_YAML = """
include:
  equity: [EQUITY, Equity, Aktien]
exclude:
  etf: [ETF]
  fund: [MUTUALFUND]
  cash_and_derivatives: [Cash, FX, Futures]
exclude_tickers:
  preferred:
    tickers: [XPREF.HE]
    patterns: ['-PREF\\.ST$', '-D\\.ST$']
unknown_action: keep
"""


def write_csv(path: Path, rows, header=SCHEMA) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow([row.get(column, "") for column in SCHEMA]
                            if isinstance(row, dict) else row)
    return path


def row(**overrides) -> dict:
    merged = dict(ROW)
    merged.update(overrides)
    return merged


@pytest.fixture()
def rules(tmp_path: Path):
    path = tmp_path / "instrument_types.yaml"
    path.write_text(TYPE_RULES_YAML, encoding="utf-8")
    return load_type_rules(path)


# --- schema validation -----------------------------------------------------


def test_reads_a_well_formed_row(tmp_path: Path):
    path = write_csv(tmp_path / "a.csv", [row()])
    (instrument,) = read_list(path)
    assert instrument.ticker_yahoo == "SAP.DE"
    assert instrument.isin == "DE0007164600"
    assert instrument.listdatum == date(1998, 4, 9)
    assert instrument.source_file == "a.csv"
    assert instrument.source_line == 2


def test_reordered_header_is_rejected(tmp_path: Path):
    header = list(SCHEMA)
    header[0], header[1] = header[1], header[0]
    path = write_csv(tmp_path / "a.csv", [], header=header)
    with pytest.raises(UniverseError, match="header is"):
        read_list(path)


def test_extra_column_is_rejected(tmp_path: Path):
    path = write_csv(tmp_path / "a.csv", [], header=list(SCHEMA) + ["extra"])
    with pytest.raises(UniverseError, match="header is"):
        read_list(path)


def test_short_row_is_a_hard_error_not_a_skip(tmp_path: Path):
    path = tmp_path / "a.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(SCHEMA)
        writer.writerow(["A", "B"])
    with pytest.raises(UniverseError, match="a.csv:2: has 2 fields"):
        read_list(path)


def test_blank_row_is_a_broken_row(tmp_path: Path):
    path = tmp_path / "a.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(SCHEMA)
        writer.writerow([""] * len(SCHEMA))
    with pytest.raises(UniverseError, match="blank row"):
        read_list(path)


def test_missing_required_field_names_the_column_and_the_line(tmp_path: Path):
    path = write_csv(tmp_path / "a.csv", [row(), row(ticker_lokal="")])
    with pytest.raises(UniverseError, match="a.csv:3: column 'ticker_lokal' is empty"):
        read_list(path)


@pytest.mark.parametrize("bad", ["DE000716460", "DE0007164601", "1E0007164600", "DE00071646OO"])
def test_malformed_isin_is_a_hard_error(tmp_path: Path, bad: str):
    path = write_csv(tmp_path / "a.csv", [row(isin=bad)])
    with pytest.raises(UniverseError, match="isin"):
        read_list(path)


def test_isin_check_digit():
    assert isin_check_digit_ok("DE0007164600")
    assert isin_check_digit_ok("US5949181045")
    assert not isin_check_digit_ok("US5949181044")


def test_bad_date_and_bad_currency_and_bad_tier(tmp_path: Path):
    for field, value, message in (
        ("listdatum", "1998-13-09", "listdatum"),
        ("valuta", "EURO", "valuta"),
        ("tier", "D", "tier"),
        ("ticker_yahoo", "SAP DE", "whitespace"),
    ):
        path = write_csv(tmp_path / f"{field}.csv", [row(**{field: value})])
        with pytest.raises(UniverseError, match=message):
            read_list(path)


def test_optional_columns_may_be_empty(tmp_path: Path):
    path = write_csv(
        tmp_path / "a.csv",
        [row(ticker_yahoo="", isin="", namn="", listdatum="", valuta="", instrumenttyp="")],
    )
    (instrument,) = read_list(path)
    assert instrument.ticker_yahoo is None
    assert instrument.isin is None
    assert instrument.namn is None
    assert instrument.instrumenttyp is None


def test_missing_file_is_an_error(tmp_path: Path):
    with pytest.raises(UniverseError, match="no such universe file"):
        read_list(tmp_path / "nope.csv")


def test_empty_file_without_a_header_is_an_error(tmp_path: Path):
    path = tmp_path / "a.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(UniverseError, match="not even a header"):
        read_list(path)


def test_header_only_file_loads_as_zero_rows(tmp_path: Path):
    path = write_csv(tmp_path / "tier-b.csv", [])
    assert read_list(path) == []


# --- instrument type exclusions -------------------------------------------


def instrument(**overrides) -> Instrument:
    base = dict(
        ticker_yahoo="X.ST", ticker_lokal="X", isin=None, namn="X AB",
        marknad="Stockholm", tier="A", listdatum=None, valuta="SEK",
        instrumenttyp="Equity",
    )
    base.update(overrides)
    return Instrument(**base)


def test_classification_is_case_and_space_insensitive(rules):
    assert rules.classify("  eQuItY ")[0] == INCLUDE
    assert rules.classify("etf")[0] == EXCLUDE
    assert rules.classify("")[0] == UNKNOWN
    assert rules.classify(None)[0] == UNKNOWN


def test_exclusion_reads_the_type_never_the_name(rules):
    # A name stuffed with every excluded word, typed as an equity by the
    # source list, must survive.
    trap = instrument(namn="ETF Trust Preferred SPAC Fund ADR Holdings",
                      instrumenttyp="Equity")
    kept, rejections, unknown, tally = apply_type_exclusions([trap], rules)
    assert [i.namn for i in kept] == [trap.namn]
    assert rejections == []
    assert tally.rejected == 0


def test_excluded_types_are_counted_on_value(rules):
    rows = [instrument(instrumenttyp=t) for t in ("ETF", "MUTUALFUND", "Cash", "Equity")]
    kept, rejections, unknown, tally = apply_type_exclusions(rows, rules)
    assert len(kept) == 1
    assert tally.rejected_on_value == 3
    assert tally.rejected_on_missing == 0
    assert {r.kind for r in rejections} == {ON_VALUE}
    assert set(tally.reasons) == {"value:etf", "value:fund", "value:cash_and_derivatives"}


# --- ticker rules (item 4, SCREENER-REVIEW-3 Part 14.3) --------------------


def test_preference_and_d_share_lines_are_excluded_by_ticker_on_value(rules):
    """Ten Stockholm lines the source types as equity are preference or
    D-share lines; the `preferred` type exclusion never had anything to act
    on. The ticker rule classifies them ON VALUE with the same reason -- by
    pattern, or by a ticker named in the list (the fixture's XPREF.HE). A
    German Vorzugsaktie such as VOW3.DE is an ordinary share without a vote
    and is KEPT (FRAMEWORK-EDITS E48)."""
    rows = [instrument(ticker_yahoo=t, instrumenttyp="EQUITY")
            for t in ("SBB-D.ST", "SBB-B.ST", "XPREF.HE", "VOW3.DE", "NP3-PREF.ST")]
    kept, rejections, unknown, tally = apply_type_exclusions(rows, rules)
    assert [i.ticker_yahoo for i in kept] == ["SBB-B.ST", "VOW3.DE"]
    assert {r.key for r in rejections} == {"SBB-D.ST", "XPREF.HE", "NP3-PREF.ST"}
    assert {r.reason for r in rejections} == {"preferred"}
    assert tally.rejected_on_value == 3 and tally.rejected_on_missing == 0
    assert set(tally.reasons) == {"value:preferred"}


def test_a_ticker_rule_reads_the_ticker_never_the_name(rules):
    trap = instrument(ticker_yahoo="SBB-B.ST", namn="SBB D-share Preferred",
                      instrumenttyp="EQUITY")
    assert rules.classify(trap.instrumenttyp, trap.ticker_yahoo)[0] == INCLUDE
    assert rules.classify("EQUITY", "SBB-D.ST") == (EXCLUDE, "preferred")


def test_a_type_exclusion_wins_over_a_ticker_rule(rules):
    """An ETF that happens to carry a listed ticker is still an ETF."""
    assert rules.classify("ETF", "XPREF.HE") == (EXCLUDE, "etf")


def test_a_ticker_rule_wins_over_an_unknown_type(rules):
    assert rules.classify(None, "XPREF.HE") == (EXCLUDE, "preferred")
    assert rules.classify("Bearer Share", "CORE-PREF.ST") == (EXCLUDE, "preferred")
    assert rules.classify(None, "VOW3.DE")[0] == UNKNOWN


def test_a_pattern_that_does_not_compile_is_a_config_error(tmp_path: Path):
    path = tmp_path / "types.yaml"
    path.write_text("include:\n  equity: [Equity]\nexclude: {}\n"
                    "exclude_tickers:\n  preferred:\n    patterns: ['(']\n",
                    encoding="utf-8")
    with pytest.raises(UniverseError, match="pattern"):
        load_type_rules(path)


def test_the_committed_ticker_rules_drop_exactly_the_ten_stockholm_lines():
    """The five -PREF and five -D lines the OMXS file types EQUITY (report
    14.3). Their ordinary or B lines, where the file carries them, stay."""
    universe_dir = Path(__file__).resolve().parents[1] / "config" / "universe"
    load = load_universe(universe_dir, tiers=("A",),
                         type_rules=load_type_rules(universe_dir / "instrument_types.yaml"))
    preferred = sorted(r.key for r in load.rejections
                       if r.step == "instrument_type" and r.reason == "preferred")
    assert preferred == sorted([
        "VOLO-PREF.ST", "CORE-PREF.ST", "NAVIGO-PREF.ST", "NP3-PREF.ST", "ALM-PREF.ST",
        "SAGA-D.ST", "CORE-D.ST", "FPAR-D.ST", "SBB-D.ST", "INTEA-D.ST",
    ])
    kept = {i.ticker_yahoo for i in load.instruments}
    for survivor in ("SBB-B.ST", "SAGA-B.ST", "CORE-B.ST", "FPAR-A.ST", "INTEA-B.ST"):
        assert survivor in kept, survivor
    assert not any(t.endswith(("-D.ST", "-PREF.ST")) for t in kept)


def test_e48_german_vorzugsaktien_are_equity_and_nordic_pref_and_d_lines_are_not():
    """FRAMEWORK-EDITS E48: a German Vorzugsaktie -- the "3"-suffix Xetra
    line -- is an ordinary share without a vote, not a fixed-dividend
    preference share, and item 4 over-reached in excluding the six by name.
    HEN3.DE is in the universe; SBB-D.ST is not."""
    universe_dir = Path(__file__).resolve().parents[1] / "config" / "universe"
    load = load_universe(universe_dir, tiers=("A",),
                         type_rules=load_type_rules(universe_dir / "instrument_types.yaml"))
    kept = {i.ticker_yahoo for i in load.instruments}
    assert "HEN3.DE" in kept
    assert "SBB-D.ST" not in kept
    for vorzug in ("VOW3.DE", "HEN3.DE", "SRT3.DE", "P911.DE", "PAH3.DE", "FPE3.DE"):
        assert vorzug in kept, vorzug
    rejected = {r.key for r in load.rejections if r.step == "instrument_type"}
    assert not any(t.endswith("3.DE") for t in rejected)


def test_unknown_type_is_kept_and_counted_by_default(rules):
    rows = [instrument(instrumenttyp=None), instrument(instrumenttyp="Bearer Share")]
    kept, rejections, unknown, tally = apply_type_exclusions(rows, rules)
    assert len(kept) == 2
    assert len(unknown) == 2
    assert tally.rejected == 0


def test_unknown_type_can_be_excluded_and_lands_in_the_missing_column(tmp_path: Path):
    path = tmp_path / "types.yaml"
    path.write_text(TYPE_RULES_YAML.replace("unknown_action: keep",
                                            "unknown_action: exclude"), encoding="utf-8")
    strict = load_type_rules(path)
    kept, rejections, unknown, tally = apply_type_exclusions(
        [instrument(instrumenttyp=None)], strict
    )
    assert kept == []
    assert tally.rejected_on_missing == 1
    assert tally.rejected_on_value == 0
    assert rejections[0].kind == ON_MISSING


def test_a_type_in_both_lists_is_a_config_error(tmp_path: Path):
    path = tmp_path / "types.yaml"
    path.write_text("include:\n  equity: [ETF]\nexclude:\n  etf: [ETF]\n", encoding="utf-8")
    with pytest.raises(UniverseError, match="both included and excluded"):
        load_type_rules(path)


def test_unknown_action_must_be_valid(tmp_path: Path):
    path = tmp_path / "types.yaml"
    path.write_text("include: {}\nexclude: {}\nunknown_action: maybe\n", encoding="utf-8")
    with pytest.raises(UniverseError, match="unknown_action"):
        load_type_rules(path)


# --- yahoo mapping ---------------------------------------------------------


def test_missing_yahoo_symbol_is_a_missing_data_rejection():
    rows = [instrument(), instrument(ticker_yahoo=None, ticker_lokal="Y")]
    kept, rejections, tally = require_yahoo_mapping(rows)
    assert len(kept) == 1
    assert tally.rejected_on_missing == 1
    assert tally.rejected_on_value == 0
    assert rejections[0].kind == ON_MISSING


# --- dedup -----------------------------------------------------------------


def test_same_ticker_in_two_lists_collapses_to_one():
    rows = [
        instrument(ticker_yahoo="VOLV-B.ST", source_file="omxs.csv"),
        instrument(ticker_yahoo="VOLV-B.ST", source_file="stoxx.csv"),
    ]
    kept, merges, tally = dedupe(rows)
    assert [i.source_file for i in kept] == ["omxs.csv"]
    assert len(merges) == 1
    assert merges[0].on == "ticker_yahoo"
    # The two symbols are identical here -- it is one listing named twice --
    # so the record is only useful if it says which FILE won.
    assert merges[0].kept_source == "omxs.csv"
    assert merges[0].dropped_source == "stoxx.csv"
    assert merges[0].kept_source != merges[0].dropped_source
    assert tally.count_out == 1


def test_same_isin_on_two_venues_keeps_the_higher_turnover():
    rows = [
        instrument(ticker_yahoo="ABB.ST", isin="CH0012221716", marknad="Stockholm"),
        instrument(ticker_yahoo="ABBN.SW", isin="CH0012221716", marknad="Zurich"),
    ]
    kept, merges, _ = dedupe(rows, turnover={"ABB.ST": 1_000, "ABBN.SW": 9_000})
    assert [i.ticker_yahoo for i in kept] == ["ABBN.SW"]
    assert merges[0].on == "isin"
    assert merges[0].basis == "highest turnover"
    assert merges[0].kept == "ABBN.SW"
    assert merges[0].dropped == "ABB.ST"


def test_isin_dedup_without_turnover_says_so():
    rows = [
        instrument(ticker_yahoo="ABB.ST", isin="CH0012221716", marknad="Stockholm"),
        instrument(ticker_yahoo="ABBN.SW", isin="CH0012221716", marknad="Zurich"),
    ]
    kept, merges, tally = dedupe(rows)
    assert len(kept) == 1
    assert "no turnover data" in merges[0].basis
    # Decided by the ABSENCE of turnover, so it is counted as such.
    assert tally.rejected_on_missing == 1
    assert tally.rejected_on_value == 0


def test_rows_without_isin_are_never_merged():
    rows = [
        instrument(ticker_yahoo="EQT", namn="EQT Corporation", marknad="US"),
        instrument(ticker_yahoo="EQT.ST", namn="EQT AB", marknad="Stockholm"),
    ]
    kept, merges, _ = dedupe(rows)
    assert len(kept) == 2
    assert merges == []


def test_dual_listing_candidates_are_reported_not_merged():
    rows = [
        instrument(ticker_yahoo="HUM", namn="Humana Inc.", marknad="US"),
        instrument(ticker_yahoo="HUM.ST", namn="Humana AB", marknad="Stockholm"),
        instrument(ticker_yahoo="SAND.ST", namn="Sandvik AB", marknad="Stockholm"),
    ]
    candidates = dual_listing_candidates(rows)
    assert candidates == [("humana", ("HUM", "HUM.ST"))]


def test_same_name_on_one_market_is_not_a_dual_listing():
    rows = [
        instrument(ticker_yahoo="ATCO-A.ST", namn="Atlas Copco AB", marknad="Stockholm"),
        instrument(ticker_yahoo="ATCO-B.ST", namn="Atlas Copco AB", marknad="Stockholm"),
    ]
    assert dual_listing_candidates(rows) == []


# --- floors ----------------------------------------------------------------


def test_floors_load_and_expose_currency(tmp_path: Path):
    path = tmp_path / "floors.yaml"
    path.write_text(
        "tiers:\n  A: {}\n  C:\n    market_cap:\n      min: 300000000\n"
        "      currency: EUR\n",
        encoding="utf-8",
    )
    floors = load_floors(path)
    assert floors.for_tier("A") == {}
    assert floors.for_tier("C")["market_cap"]["currency"] == "EUR"


def test_a_money_floor_without_a_currency_is_rejected(tmp_path: Path):
    path = tmp_path / "floors.yaml"
    path.write_text("tiers:\n  C:\n    market_cap:\n      min: 300000000\n", encoding="utf-8")
    with pytest.raises(UniverseError, match="no currency"):
        load_floors(path)


def test_unknown_tier_in_floors_is_rejected(tmp_path: Path):
    path = tmp_path / "floors.yaml"
    path.write_text("tiers:\n  D: {}\n", encoding="utf-8")
    with pytest.raises(UniverseError, match="unknown tier"):
        load_floors(path)


# --- composition -----------------------------------------------------------


def test_load_universe_selects_tiers_and_reports_every_step(tmp_path: Path, rules):
    write_csv(tmp_path / "a.csv", [
        row(),
        row(ticker_yahoo="ISHR.DE", ticker_lokal="ISHR", isin="", namn="An ETF",
            instrumenttyp="ETF"),
        row(ticker_yahoo="", ticker_lokal="NOMAP", isin="", namn="Unmapped"),
    ])
    write_csv(tmp_path / "b.csv", [
        row(ticker_yahoo="AAK.ST", ticker_lokal="AAK", isin="", namn="AAK AB",
            marknad="Stockholm", tier="B", valuta="SEK"),
    ])
    load = load_universe(tmp_path, tiers=("A",), type_rules=rules)

    assert [i.ticker_yahoo for i in load.instruments] == ["SAP.DE"]
    steps = {t.step: t for t in load.tallies}
    assert steps["read"].count_in == 4
    assert steps["tier_select"].rejected_on_value == 1
    assert steps["instrument_type"].rejected_on_value == 1
    assert steps["yahoo_mapping"].rejected_on_missing == 1
    assert len(load.files) == 2


def test_load_universe_rejects_an_unknown_tier(tmp_path: Path, rules):
    write_csv(tmp_path / "a.csv", [row()])
    with pytest.raises(UniverseError, match="unknown tier"):
        load_universe(tmp_path, tiers=("Z",), type_rules=rules)


def test_yield_table_never_sums_the_two_rejection_kinds(tmp_path: Path, rules):
    write_csv(tmp_path / "a.csv", [
        row(),
        row(ticker_yahoo="E.DE", ticker_lokal="E", isin="", instrumenttyp="ETF"),
        row(ticker_yahoo="", ticker_lokal="N", isin=""),
    ])
    load = load_universe(tmp_path, tiers=("A",), type_rules=rules)
    table = yield_table(load.tallies)
    assert "rej(value)" in table and "rej(missing)" in table
    header, _, *rows_out = table.splitlines()
    by_step = {line.split()[0]: line.split() for line in rows_out}
    assert by_step["instrument_type"][-2:] == ["1", "0"]
    assert by_step["yahoo_mapping"][-2:] == ["0", "1"]


def test_committed_lists_load_cleanly():
    """The real files in config/universe/ must parse.

    Structural assertions only. It deliberately does NOT assert a row count:
    the universe is rebuilt whenever an index changes, and a test that
    breaks on a constituent change would be reporting the market, not a bug.
    The path is resolved from this file so the test does not depend on the
    working directory.
    """
    directory = Path(__file__).resolve().parents[1] / "config" / "universe"
    rules = load_type_rules(directory / "instrument_types.yaml")
    load = load_universe(directory, tiers=("A",), type_rules=rules)
    assert load.instruments
    assert all(i.ticker_yahoo for i in load.instruments)
    assert {i.tier for i in load.instruments} == {"A"}
    assert len({i.ticker_yahoo for i in load.instruments}) == len(load.instruments)
    load_floors(directory / "floors.yaml")
