"""`total_equity` enters the store's vocabulary (owner, 2026-09-20).

Added as its own step, BEFORE E123's build, and for one purpose: E123
prints DEBT TO TOTAL CAPITALISATION where Gate 3's FCF and leverage limbs
are DATA MISSING because the operating asset is inventory. The figure
decides nothing, so the field must stay OUT of the section 5 chain.
"""
import pytest

from vss import manual as M


def test_the_field_exists_and_is_money():
    spec = M.FIELDS_BY_NAME["total_equity"]
    assert spec.kind == "money"


def test_it_is_a_STOCK_and_never_summed_across_quarters():
    assert "total_equity" in M.STOCK_FIELDS


def test_NOTHING_IN_SECTION_5_READS_IT():
    spec = M.FIELDS_BY_NAME["total_equity"]
    assert spec.reads == ("measured",)
    assert not any(r.startswith("5.") for r in spec.reads)
    section5 = {s.name for s in M.FIELDS if any(r.startswith("5.") for r in s.reads)}
    assert "total_equity" not in section5


def test_the_loader_accepts_it_with_provenance(tmp_path):
    path = tmp_path / "TEST.yaml"
    path.write_text(
        "ticker: TEST\nname: Test Inc\nreporting_currency: USD\n"
        "money_unit: whole\nshare_unit: whole\nquote_currency: USD\n"
        "origin: manual\nperiods: []\nannual:\n"
        "  - period_end: '2025-12-31'\n    fiscal_year: 2025\n"
        "    document: sources/TEST_FY2025_10k.htm\n"
        "    figures:\n"
        "      total_equity:\n        value: 12985442000\n"
        "        page: 'consolidated balance sheet: Total shareholders equity'\n"
        "        status: VERIFIED\n", encoding="utf-8")
    parsed = M.load_manual("TEST", directory=tmp_path)
    fig = parsed.annual[0].figures["total_equity"]
    assert fig.value == 12_985_442_000


def test_an_unknown_field_is_still_refused(tmp_path):
    path = tmp_path / "TEST.yaml"
    path.write_text(
        "ticker: TEST\nname: Test Inc\nreporting_currency: USD\n"
        "money_unit: whole\nshare_unit: whole\nquote_currency: USD\n"
        "origin: manual\nperiods: []\nannual:\n"
        "  - period_end: '2025-12-31'\n    fiscal_year: 2025\n    figures:\n"
        "      total_equityy:\n        value: 1\n        page: 'x'\n"
        "        status: VERIFIED\n", encoding="utf-8")
    with pytest.raises(Exception):
        M.load_manual("TEST", directory=tmp_path)
