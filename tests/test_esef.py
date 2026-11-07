"""vss/esef.py: an ESEF report package read through vss/ixbrl.py, on a
SYNTHETIC fixture (tests/fixtures/esef/README.md); no real issuer document."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from vss import esef

FIX = Path(__file__).parent / "fixtures" / "esef" / "synthetic_report.xhtml"
LEI = "5299000000000000EX01"


def _package(tmp_path, *, report=None, name="exempel-2025-12-31-sv.zip", with_meta=True,
             reports=("reports/exempel-2025-12-31-sv.xhtml",)):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        if with_meta:
            z.writestr("exempel-2025/META-INF/taxonomyPackage.xml", "<tp/>")
        for r in reports:
            z.writestr(f"exempel-2025/{r}", report if report is not None else FIX.read_bytes())
    p = tmp_path / name
    p.write_bytes(buf.getvalue())
    return p


def _read(p, **kw):
    kw.setdefault("expected_lei", LEI)
    kw.setdefault("filed", "2026-03-20")
    return esef.read_package(p, ticker="EXM.ST", **kw)


def _one(pkg, tag, end):
    entries = [e for es in pkg.facts["facts"]["ifrs-full"][tag]["units"].values() for e in es
               if e["end"] == end]
    assert len(entries) == 1, entries
    return entries[0]


def test_the_facts_scaled_signed_and_placed(tmp_path):
    pkg = _read(_package(tmp_path))
    rev = _one(pkg, "Revenue", "2025-12-31")
    assert rev["val"] == pytest.approx(1_234_500_000)       # "1 234,5" at scale 6
    assert rev["start"] == "2025-01-01" and rev["ctx"] == "FY2025"
    assert rev["decimals"] == "-6" and rev["shown"] == "1 234,5"
    assert rev["form"] == "ESEF" and rev["filed"] == "2026-03-20"
    assert rev["accn"] == f"esef:{pkg.sha256[:12]}:exempel-2025-12-31-sv.xhtml"
    # the comparative year is its own fact
    assert _one(pkg, "Revenue", "2024-12-31")["val"] == pytest.approx(1_100_000_000)
    assert _one(pkg, "FinanceIncomeCost", "2025-12-31")["val"] == pytest.approx(-12_000_000)
    assert _one(pkg, "PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities",
                "2025-12-31")["val"] == 0.0
    assert "start" not in _one(pkg, "Assets", "2025-12-31")
    assert pkg.currencies == {"SEK": 9}


def test_the_dimensional_fact_is_skipped_and_the_extension_not_read(tmp_path):
    pkg = _read(_package(tmp_path))
    assert pkg.dimensional_skipped == 1 and pkg.numeric_facts == 11
    assert pkg.extensions == {"exm:AdjustedEBITA": 1}
    assert "exm" not in pkg.facts["facts"]
    assert "extension, not read" in esef.render(pkg)


def test_a_foreign_lei_fails_closed(tmp_path):
    with pytest.raises(esef.EsefError, match="Not this issuer"):
        _read(_package(tmp_path), expected_lei="5299000000000000ZZ99")


def test_no_recorded_lei_fails_closed(tmp_path):
    ent = tmp_path / "e.yaml"
    ent.write_text("EXM.ST: {slug: x}\n")
    with pytest.raises(esef.EsefError, match="no single LEI"):
        esef.read_package(_package(tmp_path), ticker="EXM.ST", filed="2026-03-20", entities=ent)


def test_the_lei_and_the_date_come_from_the_records(tmp_path):
    ent = tmp_path / "e.yaml"
    ent.write_text(f"EXM.ST: {{slug: x, leis: [{LEI}]}}\n")
    p = _package(tmp_path)
    man = tmp_path / "manifest.json"
    man.write_text('{"downloads": [{"file": "%s", "released": "2026-03-20T07:00:00Z"}]}' % p.name)
    pkg = esef.read_package(p, ticker="EXM.ST", entities=ent, manifest=man)
    assert pkg.lei == LEI and pkg.filed == "2026-03-20"
    man.write_text('{"downloads": []}')
    with pytest.raises(esef.EsefError, match="no release date"):
        esef.read_package(p, ticker="EXM.ST", entities=ent, manifest=man)


def test_not_a_package(tmp_path):
    with pytest.raises(esef.EsefError, match="taxonomyPackage"):
        _read(_package(tmp_path, with_meta=False))
    with pytest.raises(esef.EsefError, match="no reports"):
        _read(_package(tmp_path, reports=("other/x.xhtml",)))
    with pytest.raises(esef.EsefError, match="2 report documents"):
        _read(_package(tmp_path, reports=("reports/a.xhtml", "reports/b.xhtml")))


def test_a_formatted_looking_number_without_a_format_is_not_read():
    from lxml import etree
    from vss.ixbrl import _number
    ns = 'xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"'
    el = lambda body, fmt="": etree.fromstring(
        f'<ix:nonFraction {ns} name="ifrs-full:Revenue" {fmt}>{body}</ix:nonFraction>')
    assert _number(el("1 234,5")) is None                  # not 12345
    assert _number(el("1,234")) is None
    assert _number(el("1234.5")) == 1234.5 and _number(el(".10")) == 0.1
    assert _number(el("1 234,5", 'format="ixt4:num-comma-decimal"')) == 1234.5
    assert _number(el("1.234,5", 'format="ixt:numdotcomma"')) == 1234.5
    assert _number(el("1 234", 'format="ixt:unknown-format"')) is None


# --- A3: the same IFRS map a 20-F filer goes through -------------------------

def test_the_package_maps_through_the_unchanged_ifrs_map(tmp_path):
    from vss import xbrl
    years, passed = esef.annual(_read(_package(tmp_path)))
    assert [y.fiscal_year for y in years] == [2024, 2025] and passed == []
    y = years[-1]
    assert y.figures["revenue"].value == pytest.approx(1_234_500_000)
    assert y.figures["revenue"].taxonomy == "ifrs-full"
    assert y.figures["operating_cash_flow"].value == pytest.approx(280_000_000)
    assert y.figures["capex_ppe"].value == pytest.approx(-40_000_000)   # outflow sign, as for SAP
    assert y.figures["revenue"].accession.startswith("esef:")
    # untagged here -> DATA MISSING, never filled
    for name in ("net_income", "lease_liabilities", "shares_point_in_time", "sbc"):
        assert name in y.missing and name not in y.figures
    # the extension concept never reaches a field
    assert all(f.tag != "AdjustedEBITA" for yr in years for f in yr.figures.values())
    assert {f.field for f in xbrl.IFRS_ANNUAL_FIELDS} >= {"revenue", "operating_cash_flow"}


def test_a_wrapper_with_one_inner_package_is_opened_to_it(tmp_path):
    inner = _package(tmp_path, name="inner.zip").read_bytes()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("messages.json", "{}")
        z.writestr("Submission/exempel-2025.zip", inner)
    p = tmp_path / "wrapped.zip"
    p.write_bytes(buf.getvalue())
    pkg = _read(p)
    assert pkg.report_file == "exempel-2025-12-31-sv.xhtml"
    assert _one(pkg, "Revenue", "2025-12-31")["val"] == pytest.approx(1_234_500_000)
    buf2 = io.BytesIO()
    with zipfile.ZipFile(buf2, "w") as z:
        z.writestr("a.zip", inner)
        z.writestr("b.zip", inner)
    p.write_bytes(buf2.getvalue())
    with pytest.raises(esef.EsefError, match="not guessed"):
        _read(p)
