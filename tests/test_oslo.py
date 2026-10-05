"""Euronext Oslo's NewsWeb: the directory, the silently-ignored sign, the record.

Nothing here touches the network. The feed is replayed from fixtures shaped
like the real responses measured on 2026-09-08 against Bouvet ASA -- including
the three that decide the design: an unknown issuer sign returning the WHOLE
MARKET with HTTP 200, a results release whose first attachment is the
PRESENTATION and not the report, and a report filed twice with no field
saying which edition is which.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml

from vss.nordic import MANIFEST_NAME, NordicError, Release, load_manifest, save_manifest
from vss.oslo import (
    ATTACHMENT_URL,
    ISSUERS_URL,
    LIST_URL,
    MESSAGE_URL,
    Candidate,
    OsloIssuer,
    directory,
    fetch_releases,
    find_release,
    issuer_for,
    list_url,
    load_issuers,
    resolve,
    run_oslo,
    write_issuer,
)

AS_OF = date(2026, 9, 8)
NOW = datetime(2026, 9, 8, 6, 30, 0)

BOUVET = OsloIssuer(ticker="BOUV.OL", sign="BOUV", company="Bouvet ASA",
                    issuer_id=8307)


def message(message_id, category_en, title, *, published, sign="BOUV",
            issuer_id=8307, name="Bouvet ASA", attachments=(),
            category_no="HALVÅRSRAPPORT", category_id=1002):
    return {
        "id": message_id,
        "messageId": message_id,
        "title": title,
        "category": [{"id": category_id, "category_no": category_no,
                      "category_en": category_en}],
        "markets": ["XOSL"],
        "issuerId": issuer_id,
        "issuerSign": sign,
        "issuerName": name,
        "publishedTime": f"{published}T04:00:22.848Z",
        "numbAttachments": len(attachments),
        "attachments": list(attachments),
    }


#: Q3 2025: the PRESENTATION is attachment 0 and the REPORT is attachment 1.
Q3_ATTACHMENTS = [{"id": 314311, "name": "Presentasjon Q3 2025.pdf"},
                  {"id": 314314, "name": "Bouvet Q3 report 2025 EN web.pdf"}]

Q3_EN = message(659260, "HALF YEAR FINANCIAL REPORT", "Strong results for Bouvet",
                published="2025-11-11", attachments=Q3_ATTACHMENTS)
Q3_NO = message(659259, "HALF YEAR FINANCIAL REPORT", "Solide resultater for Bouvet",
                published="2025-11-11", attachments=Q3_ATTACHMENTS)
CALENDAR = message(662136, "ADDITIONAL REGULATED INFORMATION", "Financial calendar",
                   published="2025-12-16", category_id=1010,
                   category_no="ANNEN INFORMASJONSPLIKTIG", attachments=[])

LIST_OK = {"header": {"http.code": 200},
           "data": {"messages": [CALENDAR, Q3_EN, Q3_NO], "overflow": False}}

#: What an unknown sign returns: HTTP 200 and somebody else's feed.
LIST_UNFILTERED = {"header": {"http.code": 200}, "data": {"messages": [
    message(681792, "INSIDE INFORMATION", "Interoil Exploration & Production ASA:",
            published="2026-09-01", sign="IOX", issuer_id=8135,
            name="Interoil Exploration and Prod. ASA"),
    Q3_EN,
], "overflow": True}}

MESSAGE_Q3 = {"header": {"http.code": 200}, "data": {"message": Q3_EN}}
MESSAGE_FOREIGN = {"header": {"http.code": 200}, "data": {"message": message(
    681792, "INSIDE INFORMATION", "Interoil", published="2026-09-01",
    sign="IOX", issuer_id=8135, name="Interoil Exploration and Prod. ASA",
    attachments=[{"id": 999, "name": "whatever.pdf"}])}}

DIRECTORY = {"header": {"http.code": 200}, "data": {"issuers": [
    {"issuerId": 8307, "id": "BOUV", "symbol": "BOUV", "issuerSign": "BOUV",
     "name": "Bouvet ASA", "isActive": 1},
    {"issuerId": 1114, "id": "NHY", "symbol": "NHY", "issuerSign": "NHY",
     "name": "Norsk Hydro ASA", "isActive": 1},
    {"issuerId": 12871, "id": "ACH", "symbol": "ACH", "issuerSign": "ACH",
     "name": "Aker Clean Hydrogen AS", "isActive": 0},
    # 120 of the 1,622 measured rows carry no sign at all. Dropped, never guessed.
    {"issuerId": 4242, "name": "Something Without A Sign AS", "isActive": 1},
]}}


class FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self, n=None):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener_for(routes: dict):
    """Replay by URL prefix. An unrouted URL is a test bug, said out loud."""
    def _open(request, timeout=None):
        url = request.full_url if hasattr(request, "full_url") else str(request)
        for prefix, payload in routes.items():
            if url.startswith(prefix):
                if isinstance(payload, (dict, list)):
                    payload = json.dumps(payload).encode("utf-8")
                return FakeResponse(payload)
        raise AssertionError(f"no fixture routed for {url}")
    return _open


FEED_OPENER = opener_for({
    ISSUERS_URL: DIRECTORY,
    MESSAGE_URL: MESSAGE_Q3,
    LIST_URL: LIST_OK,
    ATTACHMENT_URL: b"%PDF-1.7 bouvet q3 bytes",
})


def issuers_file(tmp_path: Path, entries: dict) -> Path:
    path = tmp_path / "oslo_issuers.yaml"
    path.write_text(yaml.safe_dump({"issuers": entries}), encoding="utf-8")
    return path


BOUV_ENTRY = {"BOUV.OL": {"sign": "BOUV", "company": "Bouvet ASA",
                          "issuer_id": 8307, "resolved": "2026-09-08"}}


# --- the request -----------------------------------------------------------


def test_the_window_is_always_sent_because_omitting_it_returns_nothing():
    """Measured: no fromDate/toDate returns an empty list, not an error."""
    url = list_url(BOUVET, since=date(2025, 7, 15), until=date(2026, 9, 8))
    q = parse_qs(urlsplit(url).query)
    assert q["issuer"] == ["BOUV"]
    assert q["fromDate"] == ["2025-07-15"]
    assert q["toDate"] == ["2026-09-08"]


# --- rule 2: the sign the service ignores ----------------------------------


def test_a_page_carrying_another_issuer_is_refused_not_filtered():
    opener = opener_for({LIST_URL: LIST_UNFILTERED})
    with pytest.raises(NordicError) as exc:
        fetch_releases(BOUVET, since=date(2026, 9, 1), until=date(2026, 9, 8),
                       opener=opener)
    said = str(exc.value)
    assert "IOX" in said
    assert "IGNORES AN ISSUER SIGN IT DOES NOT KNOW" in said
    # The point of the refusal: it must not quietly hand back the one row
    # that happened to match.
    assert "Nothing is filtered down from that" in said


def test_a_clean_page_comes_back_with_overflow_reported():
    releases, overflow = fetch_releases(
        BOUVET, since=date(2025, 7, 15), until=date(2026, 9, 8),
        opener=FEED_OPENER)
    assert [r.disclosure_id for r in releases] == [662136, 659260, 659259]
    assert overflow is False
    assert all(r.origin == "euronext-oslo-newsweb" for r in releases)


def test_a_message_filed_by_someone_else_is_refused():
    opener = opener_for({MESSAGE_URL: MESSAGE_FOREIGN})
    with pytest.raises(NordicError) as exc:
        find_release(BOUVET, 681792, opener=opener)
    assert "was filed by IOX" in str(exc.value)


# --- rule 1: the directory -------------------------------------------------


def test_the_directory_drops_rows_with_no_sign_rather_than_guessing():
    rows = directory(opener=FEED_OPENER)
    assert [c.sign for c in rows] == ["BOUV", "NHY", "ACH"]
    assert Candidate("BOUV", "Bouvet ASA", 8307, True) in rows


def test_resolve_matches_the_directory_and_picks_nothing():
    hits = resolve("BOUV.OL", "bouvet", opener=FEED_OPENER)
    assert [c.sign for c in hits] == ["BOUV"]
    code, report = run_oslo(ticker="BOUV.OL", resolve_name="hydro",
                            as_of=AS_OF, opener=FEED_OPENER,
                            issuers_path=Path("nope.yaml"))
    assert code == 0
    # Two hydro candidates; the inactive one sorts last and NEITHER is written.
    assert "Norsk Hydro ASA" in report and "Aker Clean Hydrogen AS" in report
    assert "Nothing is auto-selected" in report
    assert "**WRITTEN**" not in report


def test_resolve_finding_nothing_exits_1_and_writes_nothing(tmp_path):
    path = tmp_path / "oslo_issuers.yaml"
    code, report = run_oslo(ticker="XXXX.OL", resolve_name="no such company",
                            write=True, as_of=AS_OF, opener=FEED_OPENER,
                            issuers_path=path)
    assert code == 1
    assert not path.exists()


def test_an_existing_entry_is_never_replaced(tmp_path):
    path = issuers_file(tmp_path, BOUV_ENTRY)
    with pytest.raises(NordicError) as exc:
        write_issuer("BOUV.OL", Candidate("WRONG", "Wrong AS", 1, True),
                     as_of=AS_OF, path=path)
    assert "already has an entry" in str(exc.value)
    assert load_issuers(path)["BOUV.OL"].sign == "BOUV"


def test_an_unmapped_ticker_says_why_a_sign_has_to_be_stored(tmp_path):
    with pytest.raises(NordicError) as exc:
        issuer_for("EQNR.OL", path=tmp_path / "absent.yaml")
    assert "SILENTLY IGNORED" in str(exc.value)


# --- the download ----------------------------------------------------------


def test_the_period_is_required_and_is_never_inferred(tmp_path):
    with pytest.raises(NordicError) as exc:
        run_oslo(ticker="BOUV.OL", download_id=659260, attachment_index=1,
                 issuers_path=issuers_file(tmp_path, BOUV_ENTRY),
                 directory_path=tmp_path, opener=FEED_OPENER)
    assert "--period is required and is MANUAL" in str(exc.value)


def test_two_files_and_the_first_is_the_presentation(tmp_path):
    """The real Q3 2025 release. Guessing index 0 would file the deck."""
    with pytest.raises(NordicError) as exc:
        run_oslo(ticker="BOUV.OL", download_id=659260, period="2025-Q3",
                 issuers_path=issuers_file(tmp_path, BOUV_ENTRY),
                 directory_path=tmp_path, opener=FEED_OPENER)
    said = str(exc.value)
    assert "carries 2 files and none was named" in said
    assert "--attachment 0   Presentasjon Q3 2025.pdf" in said
    assert "--attachment 1   Bouvet Q3 report 2025 EN web.pdf" in said


def test_the_record_says_newsweb_and_carries_the_ids(tmp_path):
    code, report = run_oslo(
        ticker="BOUV.OL", download_id=659260, attachment_index=1,
        period="2025-Q3", language="en",
        issuers_path=issuers_file(tmp_path, BOUV_ENTRY),
        directory_path=tmp_path, now=NOW, opener=FEED_OPENER)
    assert code == 0

    name = "BOUV.OL_2025-Q3_half-year-financial-report_2025-11-11_en_a1.pdf"
    assert (tmp_path / name).read_bytes() == b"%PDF-1.7 bouvet q3 bytes"
    record = load_manifest(tmp_path)["downloads"][0]
    assert record["file"] == name
    assert record["origin"] == "euronext-oslo-newsweb"
    assert record["primary_source"] is True
    assert "Officially Appointed Mechanism" in record["primary_source_basis"]
    assert record["newsweb_message_id"] == 659260
    assert record["issuer_sign"] == "BOUV"
    assert record["issuer_id"] == 8307
    assert record["market"] == "XOSL"
    assert record["attachment_file_name"] == "Bouvet Q3 report 2025 EN web.pdf"
    assert "attachmentId=314314" in record["url"]
    # The endpoint declares application/octet-stream (here: nothing at all);
    # the type recorded is what the BYTES are.
    assert record["content_type"] == "application/pdf"
    assert record["figures_read"] is False


def test_the_language_is_the_owners_label_and_the_record_says_so(tmp_path):
    """NewsWeb has no language field. The label must not read as a fact."""
    run_oslo(ticker="BOUV.OL", download_id=659260, attachment_index=1,
             period="2025-Q3", language="en",
             issuers_path=issuers_file(tmp_path, BOUV_ENTRY),
             directory_path=tmp_path, now=NOW, opener=FEED_OPENER)
    record = load_manifest(tmp_path)["downloads"][0]
    assert record["language"] == "en"
    assert record["language_basis"].startswith("MANUAL.")
    assert "not read off the feed" in record["language_basis"]


def test_without_a_language_the_file_is_labelled_xx(tmp_path):
    run_oslo(ticker="BOUV.OL", download_id=659260, attachment_index=1,
             period="2025-Q3",
             issuers_path=issuers_file(tmp_path, BOUV_ENTRY),
             directory_path=tmp_path, now=NOW, opener=FEED_OPENER)
    record = load_manifest(tmp_path)["downloads"][0]
    assert record["file"].endswith("_xx_a1.pdf")
    assert "language_basis" not in record


def test_a_backend_may_not_overwrite_a_common_manifest_key():
    from vss.nordic import Attachment, _record_for
    bad = Release(disclosure_id=1, category_id=1, category="x", headline="x",
                  language="en", market="XOSL", company="Bouvet ASA",
                  released="2025-11-11", message_url="u",
                  extra=(("origin", "something-else"),))
    with pytest.raises(NordicError) as exc:
        _record_for(bad, Attachment(0, "application/pdf", "r.pdf", "u"),
                    ticker="BOUV.OL", period="2025-Q3", name="n.pdf",
                    kind="application/pdf", size=1, digest="d", stamp=NOW,
                    mismatch=None)
    assert "tried to overwrite manifest key 'origin'" in str(exc.value)


# --- the regression that stranded two documents ----------------------------


def test_the_manifest_sorts_past_a_record_with_no_release_date(tmp_path):
    """Found 2026-09-08 on the first Oslo download.

    The EDGAR and issuer-website routes write `released: null`, and
    `r.get("released", "")` returns that None rather than the default. The
    sort then raised AFTER the file was written and BEFORE its entry was --
    which is exactly how a fetched document comes to read as PROVENANCE NOT
    RECORDED.
    """
    document = {"downloads": [
        {"file": "b.htm", "ticker": "CTSH", "released": None},
        {"file": "a.pdf", "ticker": "BOUV.OL", "released": "2026-08-19"},
    ]}
    save_manifest(document, tmp_path)
    order = [r["file"] for r in load_manifest(tmp_path)["downloads"]]
    assert order == ["a.pdf", "b.htm"]
