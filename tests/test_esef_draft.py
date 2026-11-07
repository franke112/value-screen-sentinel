"""HANDOFF A4: an ESEF draft (decision a), UNVERIFIED (c), merged by hand,
never verified by quotecheck (E149). Synthetic fixture only."""
from __future__ import annotations

import datetime as dt
import io
import zipfile
from pathlib import Path

import pytest
import yaml

from vss import draft, esef, quotecheck
from vss.manual import ManualError, parse_manual

FIX = Path(__file__).parent / "fixtures" / "esef" / "synthetic_report.xhtml"
LEI = "5299000000000000EX01"
NOW = dt.datetime(2026, 11, 7, 12, 0, tzinfo=dt.timezone.utc)


@pytest.fixture
def pkg(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("e/META-INF/taxonomyPackage.xml", "<tp/>")
        z.writestr("e/reports/exempel-2025.xhtml", FIX.read_bytes())
    p = tmp_path / "EXM.ST_2025-FY_annual-financial-report_2026-03-20_en_a0.zip"
    p.write_bytes(buf.getvalue())
    return esef.read_package(p, ticker="EXM.ST", expected_lei=LEI, filed="2026-03-20")


def _draft(pkg, tmp_path):
    text, left = esef.draft_yaml("EXM.ST", "Exempel AB", [pkg], run_ts=NOW)
    d = tmp_path / "manual" / "drafts"
    esef.write_draft("EXM.ST", text, directory=d)
    return text, left


def test_the_draft_is_unverified_traced_and_holds_no_zero(pkg, tmp_path):
    text, left = _draft(pkg, tmp_path)
    doc = yaml.safe_load(text)
    parsed = parse_manual(doc, path=Path("x.yaml"))
    assert parsed.origin == "esef-ixbrl" and doc["money_unit"] == "whole"
    figs = {(y["fiscal_year"], f): r for y in doc["annual"] for f, r in y["figures"].items()}
    assert all(r["status"] == "UNVERIFIED" for r in figs.values())
    rev = figs[(2025, "revenue")]
    assert rev["value"] == 1234500000
    assert rev["page"].startswith(f"ESEF {pkg.sha256[:8]} ifrs-full:Revenue ctx FY2025 2025-01-01..2025-12-31")
    assert "displayed '1 234,5'" in rev["page"] and "decimals -6" in rev["page"]
    assert rev["source"] == f"esef-ixbrl: sources/{pkg.path.name}"
    assert (2025, "capex_intangibles") not in figs       # the tagged dash: zero not emitted
    assert (2025, "acquisitions_paid") not in figs       # a searched zero: not emitted
    assert any("capex_intangibles: zero" in l for l in left)
    assert any("net_income: no tagged fact -- DATA MISSING" in l for l in left)
    for judgement in ("interest_in_ocf", "operating_leases_in_ocf", "not_presented", "bound"):
        assert judgement not in text.split("# Packages read")[1]


def _store(tmp_path, body):
    m = tmp_path / "manual"
    m.mkdir(exist_ok=True)
    (m / "EXM.ST.yaml").write_text(body)
    return m


LIVE = """# EXM.ST -- hand-read store
ticker: EXM.ST
name: Exempel AB
reporting_currency: SEK
money_unit: whole
share_unit: whole
origin: manual

annual:
  # FY2025 read by hand from the annual report
  - fiscal_year: 2025
    period_end: 2025-12-31
    document: "Exempel annual report 2025"
    url: "sources/EXM.ST_2025.pdf"
    figures:
      revenue:
        value: 1234500000
        page: "p.40 'Revenue 1 234,5'"
        status: VERIFIED
      operating_cash_flow:
        value: 281000000
        page: "p.44 'Cash flow from operating activities 281'"
        status: VERIFIED
"""


def test_merge_adds_what_is_missing_and_never_overwrites(pkg, tmp_path):
    _draft(pkg, tmp_path)
    m = _store(tmp_path, LIVE)
    res = draft.merge_draft("EXM.ST", manual_dir=m, backup_dir=tmp_path / "bak", now=NOW)
    out = draft.render(res, origin="esef-ixbrl")
    text = (m / "EXM.ST.yaml").read_text()
    doc = yaml.safe_load(text)
    years = {y["fiscal_year"]: y for y in doc["annual"]}
    assert res.added_years == [2024] and 2024 in years
    assert years[2025]["figures"]["operating_cash_flow"]["value"] == 281000000   # left
    assert years[2025]["figures"]["capex_ppe"]["status"] == "UNVERIFIED"          # added
    assert (2025, "revenue", 1234500000) in res.agreed
    assert any("operating_cash_flow: store 281000000 | draft 280000000" in c for c in res.conflicts)
    assert "# FY2025 read by hand from the annual report" in text                  # comments kept
    assert res.backup and res.backup.read_text() == LIVE
    assert "CONFLICTS" in out
    parse_manual(doc, path=m / "EXM.ST.yaml")
    # a second merge adds nothing and writes nothing
    again = draft.merge_draft("EXM.ST", manual_dir=m, backup_dir=tmp_path / "bak", now=NOW)
    assert again.added == [] and not again.written


def test_merge_refuses_another_money_unit(pkg, tmp_path):
    _draft(pkg, tmp_path)
    m = _store(tmp_path, LIVE.replace("money_unit: whole", "money_unit: millions"))
    with pytest.raises(ManualError, match="no silent scaling"):
        draft.merge_draft("EXM.ST", manual_dir=m, backup_dir=tmp_path / "bak", now=NOW)
    assert "money_unit: millions" in (m / "EXM.ST.yaml").read_text()


def test_merge_into_no_store_makes_the_draft_the_store(pkg, tmp_path):
    _draft(pkg, tmp_path)
    m = tmp_path / "manual"
    res = draft.merge_draft("EXM.ST", manual_dir=m, now=NOW)
    assert res.created and (m / "EXM.ST.yaml").exists()
    assert yaml.safe_load((m / "EXM.ST.yaml").read_text())["origin"] == "esef-ixbrl"


def test_e149_quotecheck_never_verifies_a_machine_chosen_line():
    assert quotecheck.machine_chose({"page": "p.4 'x'"}, "esef-ixbrl")
    assert quotecheck.machine_chose({"source": "esef-ixbrl: sources/x.zip", "page": "x"}, "manual")
    assert quotecheck.machine_chose({"page": "ESEF abcd1234 ifrs-full:Revenue ..."}, "manual")
    assert quotecheck.machine_chose({"source": "llm-pdf: sources/x.pdf"}, None)
    assert not quotecheck.machine_chose({"page": "p.4 'Revenue 1 234'"}, "manual")


def test_the_displayed_text_is_found_in_the_package(pkg, monkeypatch):
    quotecheck._CACHE.clear()
    doc = quotecheck.load_doc(str(pkg.path))
    assert doc is not None
    assert quotecheck.find_quote("1 234,5", doc) != quotecheck.MISSING
    assert ".xhtml" in quotecheck.TEXT_SUFFIXES
