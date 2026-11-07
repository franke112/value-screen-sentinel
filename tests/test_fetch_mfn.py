"""tools/fetch_mfn.py: a report's kind and period come from MFN's tags and the title."""
from __future__ import annotations

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "fetch_mfn", Path(__file__).resolve().parents[1] / "tools" / "fetch_mfn.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

INT = [":regulatory", "sub:report", "sub:report:interim"]
ANN = [":regulatory", "sub:report", "sub:report:annual"]


def test_a_swedish_interim_is_not_an_annual_report():
    # "delårsrapport" contains "årsrapport": the trap that misnamed 56 files
    assert M.kind_of(INT, "ZINZINO AB (PUBL.): DELÅRSRAPPORT Q1 2026") == "interim-report-q1-and-q3"


def test_the_kinds():
    assert M.kind_of(INT, "INTERIM REPORT Q2 2026") == "half-year-financial-report"
    assert M.kind_of(ANN + ["sub:report:interim", "sub:report:interim:q4"],
                     "YEAR-END REPORT 2025") == "financial-statement-release"
    assert M.kind_of(ANN, "Year-End Report 1st January - 31st December 2015") == "financial-statement-release"
    assert M.kind_of(INT + ["sub:report:interim:q4"], "ANNUAL REPORT ENGLISH 2022") == "annual-financial-report"
    assert M.kind_of([":regulatory"], "Annual Report 2021 Zinzino AB (PUBL)") == "annual-financial-report"


def test_the_periods():
    assert M.period_of("INTERIM REPORT Q2 2026", "half-year-financial-report") == "2026-Q2"
    assert M.period_of("Interim Report for the third quarter of 2025", "interim-report-q1-and-q3") == "2025-Q3"
    assert M.period_of("Delårsrapport tredje kvartalet 2025", "interim-report-q1-and-q3") == "2025-Q3"
    assert M.period_of("ANNUAL REPORT 2024", "annual-financial-report") == "2024-FY"
    assert M.period_of("A strong quarter", "interim-report-q1-and-q3") == "UNKNOWN"


def test_local_symbol():
    assert M.local_symbol("ZZ-B.ST") == "ZZ B" and M.local_symbol("EVO.ST") == "EVO"


# --- A1: provenance (manifest entries) and ESEF packages ---------------------

import hashlib
import io
import json
import zipfile

import pytest


def _zip(names):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n in names:
            z.writestr(n, "<x/>")
    return buf.getvalue()


PKG = _zip(["evo-2025/META-INF/taxonomyPackage.xml", "evo-2025/reports/evo.xhtml"])
NOT_PKG = _zip(["word/document.xml"])
PDF = b"%PDF-1.7 a report"


def test_an_esef_package_is_known_by_its_bytes_not_its_name():
    assert M.is_esef_package(PKG) and M.classify(PKG) == "esef"
    assert not M.is_esef_package(NOT_PKG) and M.classify(NOT_PKG) is None
    assert M.classify(PDF) == "pdf"
    assert M.classify(b"PK\x03\x04 truncated") is None


def _item(date, lang, atts, title="Evolution - Annual Report 2025"):
    return {"news_id": f"n-{date}-{lang}", "url": f"https://mfn.se/x/{date}-{lang}",
            "source": "cis",
            "author": {"name": "Evolution", "tickers": ["XSTO:EVO"], "leis": ["549300SUH6ZR1RF6TA88"]},
            "properties": {"lang": lang, "tags": [":regulatory", "sub:report", "sub:report:annual"]},
            "content": {"title": title, "publish_date": f"{date}T21:30:00Z",
                        "attachments": atts}}


@pytest.fixture
def world(tmp_path, monkeypatch):
    src = tmp_path / "sources"
    src.mkdir()
    ent = tmp_path / "mfn_entities.yaml"
    ent.write_text("EVO.ST: {slug: evolution, name: Evolution, entity_id: x}\n")
    monkeypatch.setattr(M, "SOURCES", src)
    monkeypatch.setattr(M, "ENTITIES", ent)
    monkeypatch.setattr(M, "names_from_config", lambda: {})
    served = {}
    items = []

    class R:
        def __init__(self, b):
            self.content = b

    monkeypatch.setattr(M, "_get", lambda url, **kw: R(served[url]))
    monkeypatch.setattr(M, "feed", lambda slug, since: iter(items))
    return {"src": src, "served": served, "items": items, "ent": ent}


def _manifest(src):
    return {r["file"]: r for r in json.loads((src / "manifest.json").read_text())["downloads"]}


def test_a_download_is_recorded_and_an_esef_package_is_taken(world):
    w = world
    w["served"].update({"u/pdf": PDF, "u/xbri": PKG, "u/other": NOT_PKG})
    w["items"].append(_item("2026-04-01", "en", [
        {"file_title": "AR", "content_type": "application/pdf", "url": "u/pdf"},
        {"file_title": "EVO-2025-12-31-1-sv.xbri", "content_type": "application/octet-stream", "url": "u/xbri"},
        {"file_title": "notes.docx", "content_type": "application/octet-stream", "url": "u/other"}]))
    wrote, problems = M.run(["EVO.ST"], M.date(2015, 1, 1), {"annual"}, "en", False)
    assert problems == [] and wrote == 2          # the PDF and the package, not the docx
    m = _manifest(w["src"])
    pdf = m["EVO.ST_2025-FY_annual-financial-report_2026-04-01_en_a0.pdf"]
    pkg = m["EVO.ST_2025-FY_annual-financial-report_2026-04-01_en_a0.zip"]
    assert pdf["source"] == "mfn" and pdf["origin"] == "mfn"
    assert pdf["sha256"] == hashlib.sha256(PDF).hexdigest() and pdf["bytes"] == len(PDF)
    assert pdf["url"] == "u/pdf" and pdf["released"] == "2026-04-01T21:30:00Z"
    assert pdf["declared_type"] == pdf["content_type"] == "application/pdf"
    assert pdf["downloaded_at"] and "recorded_after_the_fact" not in pdf
    assert pkg["esef_package"] is True and pkg["content_type"] == "application/zip"
    assert pkg["declared_type"] == "application/octet-stream" and "type_note" in pkg
    assert pkg["lei"] == ["549300SUH6ZR1RF6TA88"] and pkg["attachment_index"] == 1
    assert "549300SUH6ZR1RF6TA88" in w["ent"].read_text()     # LEI cached for the ESEF reader
    # a second run fetches nothing
    assert M.run(["EVO.ST"], M.date(2015, 1, 1), {"annual"}, "en", False) == (0, [])


def test_a_file_on_disk_without_an_entry_is_recorded_only_if_byte_identical(world):
    w = world
    same = "EVO.ST_2025-FY_annual-financial-report_2026-04-01_en_a0.pdf"
    diff = "EVO.ST_2024-FY_annual-financial-report_2025-04-14_en_a0.pdf"
    (w["src"] / same).write_bytes(PDF)
    (w["src"] / diff).write_bytes(b"%PDF-1.7 something else")
    w["served"].update({"u/a": PDF, "u/b": PDF})
    w["items"] += [
        _item("2026-04-01", "en", [{"file_title": "a", "content_type": "application/pdf", "url": "u/a"}]),
        _item("2025-04-14", "en", [{"file_title": "b", "content_type": "application/pdf", "url": "u/b"}],
              title="Evolution AB (publ) Annual Report 2024")]
    wrote, problems = M.run(["EVO.ST"], M.date(2015, 1, 1), {"annual"}, "en", False)
    assert wrote == 0 and problems == [diff]
    m = _manifest(w["src"])
    assert "recorded_after_the_fact" in m[same] and m[same]["downloaded_at_basis"]
    assert diff not in m                           # fail closed
    assert (w["src"] / diff).read_bytes() == b"%PDF-1.7 something else"


def test_a_package_from_the_other_language_edition_when_this_one_has_none(world):
    w = world
    w["served"].update({"u/pdf": PDF, "u/sv": PKG})
    w["items"] += [
        _item("2026-04-01", "en", [{"file_title": "AR", "content_type": "application/pdf", "url": "u/pdf"}]),
        _item("2026-04-01", "sv", [{"file_title": "x.xbri", "content_type": "application/zip", "url": "u/sv"}],
              title="Evolution - Årsredovisning 2025")]
    M.run(["EVO.ST"], M.date(2015, 1, 1), {"annual"}, "en", False)
    pkg = _manifest(w["src"])["EVO.ST_2025-FY_annual-financial-report_2026-04-01_en_a0.zip"]
    assert pkg["language"] == "sv" and pkg["url"] == "u/sv"


def test_a_report_another_feed_already_has_is_skipped(world):
    w = world
    (w["src"] / "EVO.ST_2025-FY_annual-financial-report_2026-04-01_sv_a0.pdf").write_bytes(PDF)
    w["served"]["u/pdf"] = PDF
    w["items"].append(_item("2026-04-01", "en", [{"file_title": "AR", "content_type": "application/pdf", "url": "u/pdf"}]))
    assert M.run(["EVO.ST"], M.date(2015, 1, 1), {"annual"}, "en", False) == (0, [])
    assert not (w["src"] / "EVO.ST_2025-FY_annual-financial-report_2026-04-01_en_a0.pdf").exists()


def test_bytes_that_are_not_what_was_wanted_are_not_written(world):
    w = world
    w["served"]["u/pdf"] = b"<html>error</html>"
    w["items"].append(_item("2026-04-01", "en", [{"file_title": "AR", "content_type": "application/pdf", "url": "u/pdf"}]))
    assert M.run(["EVO.ST"], M.date(2015, 1, 1), {"annual"}, "en", False) == (0, [])
    assert list(w["src"].glob("EVO*")) == []


def test_a_report_another_feed_has_still_gives_its_esef_package(world):
    w = world
    (w["src"] / "EVO.ST_2025-FY_annual-financial-report_2026-04-01_sv_a0.pdf").write_bytes(PDF)
    w["served"].update({"u/pdf": PDF, "u/x": PKG})
    w["items"].append(_item("2026-04-01", "en", [
        {"file_title": "AR", "content_type": "application/pdf", "url": "u/pdf"},
        {"file_title": "x.xbri", "content_type": "application/octet-stream", "url": "u/x"}]))
    assert M.run(["EVO.ST"], M.date(2015, 1, 1), {"annual"}, "en", False) == (1, [])
    assert (w["src"] / "EVO.ST_2025-FY_annual-financial-report_2026-04-01_en_a0.zip").exists()
    assert not (w["src"] / "EVO.ST_2025-FY_annual-financial-report_2026-04-01_en_a0.pdf").exists()
    # and not when that feed already holds a package for the date
    (w["src"] / "EVO.ST_2025-FY_annual-financial-report_2026-04-01_en_a0.zip").unlink()
    (w["src"] / "EVO.ST_2025-FY_annual-financial-report_2026-04-01_sv_a1.zip").write_bytes(PKG)
    assert M.run(["EVO.ST"], M.date(2015, 1, 1), {"annual"}, "en", False) == (0, [])


def test_two_mfn_reports_on_one_date_are_not_another_feed(world):
    w = world
    w["served"].update({"u/ar": PDF, "u/q4": PDF + b" q4"})
    w["items"] += [
        _item("2022-10-25", "en", [{"file_title": "AR", "content_type": "application/pdf", "url": "u/ar"}],
              title="Annual Report 2022"),
        dict(_item("2022-10-25", "en", [{"file_title": "Q4", "content_type": "application/pdf", "url": "u/q4"}],
                   title="Interim report Q4 2022"),
             properties={"lang": "en", "tags": [":regulatory", "sub:report", "sub:report:interim"]})]
    ann = "EVO.ST_2022-FY_annual-financial-report_2022-10-25_en_a0.pdf"
    (w["src"] / ann).write_bytes(PDF)          # fetched before entries existed
    wrote, problems = M.run(["EVO.ST"], M.date(2015, 1, 1), {"annual", "interim"}, "en", False)
    m = _manifest(w["src"])
    assert problems == [] and wrote == 1 and "recorded_after_the_fact" in m[ann]
    assert "EVO.ST_2022-Q4_interim-report-q1-and-q3_2022-10-25_en_a0.pdf" in m


def test_the_other_language_edition_on_disk_is_recorded_too(world):
    w = world
    sv = "EVO.ST_2025-FY_annual-financial-report_2026-04-01_sv_a0.pdf"
    (w["src"] / sv).write_bytes(PDF + b" sv")
    w["served"].update({"u/en": PDF, "u/sv": PDF + b" sv"})
    w["items"] += [
        _item("2026-04-01", "en", [{"file_title": "AR", "content_type": "application/pdf", "url": "u/en"}]),
        _item("2026-04-01", "sv", [{"file_title": "AR", "content_type": "application/pdf", "url": "u/sv"}],
              title="Evolution - Årsredovisning 2025")]
    assert M.run(["EVO.ST"], M.date(2015, 1, 1), {"annual"}, "en", False, record_only=True) == (0, [])
    m = _manifest(w["src"])
    assert m[sv]["language"] == "sv" and m[sv]["url"] == "u/sv"
    assert not (w["src"] / "EVO.ST_2025-FY_annual-financial-report_2026-04-01_en_a0.pdf").exists()


def test_a_wrapper_holding_one_package_is_a_package():
    wrapper = _zip(["messages.json", "Read_This_First.pdf"])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("messages.json", "{}")
        z.writestr("Submission/evo-2024.zip", PKG)
    assert M.classify(buf.getvalue()) == "esef"
    assert M.classify(wrapper) is None
    two = io.BytesIO()
    with zipfile.ZipFile(two, "w") as z:
        z.writestr("a.zip", PKG)
        z.writestr("b.zip", PKG)
    assert M.classify(two.getvalue()) is None
