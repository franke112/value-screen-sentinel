"""The Nordic fetcher: the stored mapping, the listing, the download, the manifest.

Nothing here touches the network. The feed is replayed from fixtures shaped
like the real responses measured on 2026-08-24 -- including the two cases
that decide the design: Pandora's H1 2026 report filed under *Inside
information*, and Betsson's annual filing carrying an ESEF package at
attachment 0 with the PDF at 1.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml

from vss.nordic import (
    API_URL,
    ISSUERS_PATH,
    MANIFEST_NAME,
    MAX_LIMIT,
    NOT_SERVED,
    Attachment,
    Issuer,
    NordicError,
    Release,
    check_period,
    download,
    fetch_releases,
    filename_for,
    issuer_for,
    load_issuers,
    load_manifest,
    parse_releases,
    query_url,
    resolve,
    run_nordic,
    slug,
    sniff,
    write_issuer,
)

AS_OF = date(2026, 8, 24)
NOW = datetime(2026, 8, 24, 21, 0, 0)

PANDORA = Issuer(ticker="PNDORA.CO", market="Main Market, Copenhagen",
                 company="Pandora A/S", language="en")
BETSSON = Issuer(ticker="BETS-B.ST", market="Main Market, Stockholm",
                 company="Betsson AB", language="en")


def item(disclosure_id, category_id, category, headline, *, released,
         language="en", company="Pandora A/S", market="Main Market, Copenhagen",
         attachments=()):
    return {
        "disclosureId": disclosure_id,
        "categoryId": category_id,
        "cnsCategory": category,
        "headline": headline,
        "language": language,
        "languages": [language],
        "market": market,
        "company": company,
        "releaseTime": f"{released} 07:00:00 +0000",
        "published": f"{released} 07:00:00 +0000",
        "messageUrl": f"https://view.news.eu.nasdaq.com/view?id={disclosure_id}",
        "attachment": list(attachments),
    }


PDF = {"mimetype": "application/pdf", "fileName": "report.pdf",
       "attachmentUrl": "https://attachment.news.eu.nasdaq.com/aaa"}
ESEF = {"mimetype": "application/zip",
        "fileName": "549300W61XW8OFGBG077-2025-12-31-1-sv.xbri",
        "attachmentUrl": "https://attachment.news.eu.nasdaq.com/zzz"}

#: The two rows the whole design turns on, plus noise around them.
FEED = {"results": {"item": [
    # Filed as INSIDE INFORMATION, and it is the H1 2026 report.
    item(1457001, 428, "Inside information",
         "Pandora delivers 3% organic growth in Q2 - guidance upgraded",
         released="2026-08-12", attachments=[PDF]),
    item(1450002, 153, "Interim report (Q1 and Q3)",
         "2% ORGANIC GROWTH IN Q1 2026 - GUIDANCE UNCHANGED",
         released="2026-05-06", attachments=[PDF]),
    item(1440003, 270, "Annual Financial Report", "Pandora Annual Report 2025",
         released="2026-02-04", attachments=[PDF]),
    item(1459004, 66, "Managers' Transactions", "Trading in Pandora A/S shares",
         released="2026-08-17", attachments=[PDF]),
    item(1459005, 69, "Changes in company's own shares", "Buyback week 33",
         released="2026-08-18"),          # no attachment at all
]}, "count": 1027}

BETSSON_FEED = {"results": {"item": [
    item(2260001, 270, "Annual Financial Report",
         "Betsson AB publishes the annual report for 2025",
         released="2026-04-01", company="Betsson AB",
         market="Main Market, Stockholm", attachments=[ESEF, PDF]),
    item(2270002, 78, "Half Year financial report",
         "Betsson AB interim report January - June 2026",
         released="2026-07-17", company="Betsson AB",
         market="Main Market, Stockholm", attachments=[PDF]),
]}, "count": 737}


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
    API_URL: FEED,
    "https://attachment.news.eu.nasdaq.com/aaa": b"%PDF-1.7 pandora bytes",
    "https://attachment.news.eu.nasdaq.com/zzz": b"PK\x03\x04 esef package",
})


def issuers_file(tmp_path: Path, entries: dict) -> Path:
    path = tmp_path / "nordic_issuers.yaml"
    path.write_text(yaml.safe_dump({"issuers": entries}), encoding="utf-8")
    return path


# --- the request itself ----------------------------------------------------


def test_the_query_carries_market_company_and_nothing_that_lies():
    url = query_url(PANDORA, limit=50, start=0, language="en")
    q = parse_qs(urlsplit(url).query)
    assert q["market"] == ["Main Market, Copenhagen"]
    assert q["company"] == ["Pandora A/S"]
    assert q["limit"] == ["50"]
    assert q["language"] == ["en"]
    assert q["showAttachments"] == ["true"]


def test_the_query_never_sends_cnscategory_or_a_date_filter():
    """Both are accepted by the service and one of them lies.

    `cnscategory` with several ids returns the UNFILTERED feed, which reads
    as "every release is a report". `fromDate`/`toDate` are accepted and
    ignored outright. A parameter that silently does nothing is worse than
    no parameter, so neither is ever sent.
    """
    url = query_url(PANDORA, limit=MAX_LIMIT, start=0, language=None)
    q = parse_qs(urlsplit(url).query)
    assert "cnscategory" not in q
    assert "fromDate" not in q and "toDate" not in q
    assert "language" not in q


def test_pagination_is_start_and_only_appears_when_asked_for():
    assert "start=" not in query_url(PANDORA, limit=10, start=0, language=None)
    assert "start=200" in query_url(PANDORA, limit=200, start=200, language=None)


def test_asking_for_more_than_the_service_gives_fails_loudly():
    """It answers 400 with 200 rows and says nothing. Say something."""
    with pytest.raises(NordicError, match="ceiling of 200"):
        query_url(PANDORA, limit=400, start=0, language=None)


# --- parsing ---------------------------------------------------------------


def test_attachments_keep_their_index_and_their_declared_type():
    releases, count = parse_releases(BETSSON_FEED)
    assert count == 737
    annual = releases[0]
    assert [(a.index, a.mimetype) for a in annual.attachments] == [
        (0, "application/zip"), (1, "application/pdf")]


def test_a_single_item_is_not_read_as_a_list_of_its_keys():
    """The service returns a bare mapping when one row matches."""
    releases, _ = parse_releases({"results": {"item": item(
        1, 270, "Annual Financial Report", "x", released="2026-02-04",
        attachments=[PDF])}})
    assert len(releases) == 1 and releases[0].disclosure_id == 1


def test_an_empty_feed_is_named_rather_than_read_as_no_reports(tmp_path):
    empty = opener_for({API_URL: {"results": {"item": []}, "count": 0}})
    with pytest.raises(NordicError, match="Either the stored mapping is wrong"):
        fetch_releases(PANDORA, opener=empty)


# --- the stored mapping ----------------------------------------------------


def test_oslo_is_told_it_is_the_wrong_exchange_not_handed_nothing():
    """Oslo Børs is Euronext. An empty result would read as "no reports"."""
    assert ".OL" in NOT_SERVED
    with pytest.raises(NordicError, match="Euronext"):
        issuer_for("EQNR.OL", path=Path("does-not-exist.yaml"))


def test_an_unmapped_ticker_says_how_to_map_it(tmp_path):
    with pytest.raises(NordicError, match="vss nordic --resolve"):
        issuer_for("PNDORA.CO", path=tmp_path / "none.yaml")


def test_the_mapping_loads_and_rejects_a_key_it_does_not_know(tmp_path):
    path = issuers_file(tmp_path, {"PNDORA.CO": {
        "market": "Main Market, Copenhagen", "company": "Pandora A/S",
        "language": "en", "resolved": "2026-08-24"}})
    issuer = load_issuers(path)["PNDORA.CO"]
    assert issuer.company == "Pandora A/S" and issuer.resolved == AS_OF

    bad = issuers_file(tmp_path, {"X.ST": {"market": "m", "company": "c",
                                           "isin": "SE0000"}})
    with pytest.raises(NordicError, match="unknown key"):
        load_issuers(bad)


def test_a_mapping_without_a_company_is_refused(tmp_path):
    path = issuers_file(tmp_path, {"X.ST": {"market": "Main Market, Stockholm"}})
    with pytest.raises(NordicError, match="company is required"):
        load_issuers(path)


def test_writing_a_mapping_backs_up_and_never_replaces(tmp_path):
    from vss.nordic import Candidate

    path = tmp_path / "nordic_issuers.yaml"
    candidate = Candidate("Main Market, Copenhagen", "Pandora A/S", 42,
                          "2026-08-20", ("en",))
    write_issuer("PNDORA.CO", candidate, as_of=AS_OF, language="en", path=path)
    assert load_issuers(path)["PNDORA.CO"].company == "Pandora A/S"

    other = Candidate("Main Market, Copenhagen", "Something Else A/S", 1,
                      "2026-01-01", ("da",))
    with pytest.raises(NordicError, match="already has an entry"):
        write_issuer("PNDORA.CO", other, as_of=AS_OF, path=path)

    write_issuer("BETS-B.ST", Candidate("Main Market, Stockholm", "Betsson AB",
                                        7, "2026-07-17", ("en", "sv")),
                 as_of=AS_OF, path=path)
    assert (tmp_path / f"nordic_issuers.yaml.bak-{AS_OF.isoformat()}").exists()
    assert set(load_issuers(path)) == {"PNDORA.CO", "BETS-B.ST"}


def test_resolution_groups_on_the_feeds_own_company_field():
    """Full-text search returns issuers that merely MENTION the term.

    The watchlist calls PNDORA.CO "PANDORA" and the service calls it
    "Pandora A/S", so there is no name equality that would be safe -- the
    candidates are grouped and the owner picks.
    """
    noisy = {"results": {"item": [
        item(1, 428, "Inside information", "Pandora Q2", released="2026-08-12",
             company="Pandora A/S"),
        item(2, 270, "Annual Financial Report", "Pandora AR", released="2026-02-04",
             company="Pandora A/S"),
        item(3, 428, "Inside information", "GXO expands with Pandora",
             released="2026-04-02", company="GXO Logistics"),
    ]}, "count": 3}
    candidates = resolve("PNDORA.CO", "Pandora",
                         opener=opener_for({API_URL: noisy}))
    assert [(c.company, c.hits) for c in candidates][0] == ("Pandora A/S", 4)
    assert "GXO Logistics" in {c.company for c in candidates}


# --- the period label ------------------------------------------------------


def test_the_period_is_shape_checked_against_the_shared_vocabulary():
    assert check_period("2026-H1") == "2026-H1"
    assert check_period(" 2025-FY ") == "2025-FY"
    with pytest.raises(NordicError, match="not a label the schema knows"):
        check_period("H1 2026")


def test_a_quarterly_reporter_may_label_its_annual_report_FY():
    """`rules.period_kind_allowed` must NOT be applied here.

    That rule governs which labels a ticker may STORE in its quarters:
    history, where the overlap guard needs one resolution per ticker.
    PNDORA.CO reports quarterly and still publishes an annual report, and
    2025-FY is the only honest label for it.
    """
    from vss.rules import period_kind_allowed

    assert not period_kind_allowed("2025-FY", "quarterly")
    assert check_period("2025-FY") == "2025-FY"


# --- naming ----------------------------------------------------------------


def test_the_filename_leads_with_ticker_period_category_and_date():
    releases, _ = parse_releases(FEED)
    name = filename_for(ticker="PNDORA.CO", period="2026-H1",
                        release=releases[0],
                        attachment=releases[0].attachments[0], extension=".pdf")
    assert name == "PNDORA.CO_2026-H1_inside-information_2026-08-12_en_a0.pdf"


def test_the_filename_carries_the_category_the_exchange_filed_it_under():
    """Not a category this tool inferred. `inside-information` on an interim
    report is the fact, and putting it in the name keeps it visible."""
    releases, _ = parse_releases(FEED)
    assert "inside-information" in filename_for(
        ticker="PNDORA.CO", period="2026-H1", release=releases[0],
        attachment=releases[0].attachments[0], extension=".pdf")


def test_language_and_attachment_index_are_what_make_the_name_unique():
    """Betsson files every report twice and its annual filing carries two
    documents. Without both discriminators the four leading fields collide."""
    releases, _ = parse_releases(BETSSON_FEED)
    annual = releases[0]
    names = {filename_for(ticker="BETS-B.ST", period="2025-FY", release=annual,
                          attachment=a, extension=".pdf")
             for a in annual.attachments}
    assert len(names) == 2


def test_slug_is_filename_safe():
    assert slug("Interim report (Q1 and Q3)") == "interim-report-q1-and-q3"
    assert slug("Halvårsrapport") == "halvarsrapport"


# --- the bytes that actually arrived ---------------------------------------


def test_the_extension_follows_the_bytes_not_the_promise():
    kind, note = sniff(b"PK\x03\x04xxxx", "application/pdf")
    assert kind == "application/zip"
    assert note and "extension follows the bytes" in note


def test_a_matching_declaration_raises_no_note():
    assert sniff(b"%PDF-1.7", "application/pdf") == ("application/pdf", None)


# --- downloading and recording ---------------------------------------------


def one_release(feed=FEED, index=0):
    releases, _ = parse_releases(feed)
    return releases[index]


def test_a_download_lands_on_disk_and_in_the_manifest(tmp_path):
    release = one_release()
    result = download(release, release.attachments[0], ticker="PNDORA.CO",
                      period="2026-H1", directory=tmp_path, now=NOW,
                      opener=FEED_OPENER)
    payload = b"%PDF-1.7 pandora bytes"

    assert result.file.read_bytes() == payload
    record = result.record
    assert record["bytes"] == len(payload)
    assert record["sha256"] == hashlib.sha256(payload).hexdigest()
    assert record["url"] == release.attachments[0].url
    assert record["downloaded_at"].startswith("2026-08-24T21:00:00")
    assert record["origin"] == "nasdaq-nordic"
    assert record["primary_source"] is True
    assert record["disclosure_id"] == 1457001
    assert record["category"] == "Inside information"
    assert record["period"] == "2026-H1"

    stored = json.loads((tmp_path / MANIFEST_NAME).read_text())
    assert [r["file"] for r in stored["downloads"]] == [result.file.name]


def test_the_manifest_says_a_file_it_never_fetched_is_not_recorded(tmp_path):
    """Provenance NOT RECORDED is a third state, not "secondary".

    The sources/ documents that predate this module have no entry, and none
    of them is back-filled with a guess about where it came from.
    """
    document = load_manifest(tmp_path)
    assert "PROVENANCE NOT RECORDED" in document["note"]
    assert "not the same as being secondary" in document["note"]


def test_the_note_claims_only_what_the_flag_actually_means(tmp_path):
    """`figures_read` says nothing was taken INTO config/manual. It does not
    say nobody opened the file.

    The note claimed the stronger thing until 2026-08-24, when the ESEF
    measurement read tagged values out of a recorded package -- leaving the
    flag true and the sentence beside it false. A provenance record that
    overclaims is worse than one that claims less.
    """
    note = load_manifest(tmp_path)["note"]
    assert "THE FETCHER ITSELF NEVER PARSES" in note
    assert "config/manual/<TICKER>.yaml" in note
    assert "Reading a document is a separate act" in note
    assert "the row is not wrong" in note
    # The overclaim itself must be gone.
    assert "No figure has been read out of any of these documents" not in note


def test_a_saved_manifest_refreshes_the_note_from_the_constant(tmp_path):
    """So a reworded note reaches files written before the rewording."""
    from vss.nordic import MANIFEST_NOTE, save_manifest

    stale = {"schema": "vss/nordic manifest v1", "note": "something older",
             "downloads": []}
    save_manifest(stale, tmp_path)
    assert load_manifest(tmp_path)["note"] == MANIFEST_NOTE


def test_re_downloading_identical_bytes_is_a_skip_not_an_overwrite(tmp_path):
    release = one_release()
    first = download(release, release.attachments[0], ticker="PNDORA.CO",
                     period="2026-H1", directory=tmp_path, now=NOW,
                     opener=FEED_OPENER)
    again = download(release, release.attachments[0], ticker="PNDORA.CO",
                     period="2026-H1", directory=tmp_path, now=NOW,
                     opener=FEED_OPENER)
    assert again.skipped and "byte-identical" in again.note
    assert len(json.loads((tmp_path / MANIFEST_NAME).read_text())["downloads"]) == 1
    assert first.file == again.file


def test_a_changed_document_fails_rather_than_overwriting(tmp_path):
    """The issuer replaced the file, or two filings collided on one name.

    Either is an event to look at. Neither is an overwrite to perform.
    """
    release = one_release()
    download(release, release.attachments[0], ticker="PNDORA.CO",
             period="2026-H1", directory=tmp_path, now=NOW, opener=FEED_OPENER)
    changed = opener_for({"https://attachment.news.eu.nasdaq.com/aaa":
                          b"%PDF-1.7 DIFFERENT bytes"})
    with pytest.raises(NordicError, match="content DIFFERS"):
        download(release, release.attachments[0], ticker="PNDORA.CO",
                 period="2026-H1", directory=tmp_path, now=NOW, opener=changed)


def test_an_esef_package_is_saved_as_a_zip_not_as_a_pdf(tmp_path):
    release = one_release(BETSSON_FEED)
    result = download(release, release.attachments[0], ticker="BETS-B.ST",
                      period="2025-FY", directory=tmp_path, now=NOW,
                      opener=FEED_OPENER)
    assert result.file.suffix == ".zip"
    assert result.record["content_type"] == "application/zip"


def test_nothing_is_read_out_of_a_downloaded_document(tmp_path):
    """The line this module does not cross, asserted rather than asserted-to.

    `vss/source.py` can turn a PDF into text. This module must never call it:
    between downloading a report and deciding what it says lies the whole
    difference the manual schema exists to keep.
    """
    import inspect

    from vss import nordic

    body = inspect.getsource(nordic)
    assert "pdf_to_text" not in body
    assert "html_to_text" not in body
    record = download(one_release(), one_release().attachments[0],
                      ticker="PNDORA.CO", period="2026-H1", directory=tmp_path,
                      now=NOW, opener=FEED_OPENER).record
    assert record["figures_read"] is False


# --- the command -----------------------------------------------------------


def mapped(tmp_path):
    return issuers_file(tmp_path, {
        "PNDORA.CO": {"market": "Main Market, Copenhagen",
                      "company": "Pandora A/S", "language": "en"},
        "BETS-B.ST": {"market": "Main Market, Stockholm",
                      "company": "Betsson AB", "language": "en"},
    })


def test_the_default_listing_shows_every_release_carrying_a_document(tmp_path):
    code, report = run_nordic(ticker="PNDORA.CO", issuers_path=mapped(tmp_path),
                              directory=tmp_path, as_of=AS_OF,
                              opener=FEED_OPENER)
    assert code == 0
    assert "Inside information" in report          # the H1 2026 report
    assert "Managers' Transactions" in report      # not a report, still listed
    assert "Buyback week 33" not in report         # no attachment, nothing to fetch


def test_the_reports_filter_says_how_many_rows_it_hid_and_why(tmp_path):
    code, report = run_nordic(ticker="PNDORA.CO", reports_only=True,
                              issuers_path=mapped(tmp_path), directory=tmp_path,
                              as_of=AS_OF, opener=FEED_OPENER)
    assert "**2 release(s) in this window are NOT shown.**" in report
    assert "issuer's filing choice" in report
    # The point of the warning: this filter hides a real interim report.
    assert "Inside information" in report          # named in the warning
    assert "Annual Financial Report" in report


def test_a_multi_file_disclosure_refuses_to_guess_which_one(tmp_path):
    opener = opener_for({API_URL: BETSSON_FEED,
                         "https://attachment.news.eu.nasdaq.com/aaa": b"%PDF-x",
                         "https://attachment.news.eu.nasdaq.com/zzz": b"PK\x03\x04"})
    with pytest.raises(NordicError, match="--attachment 1"):
        run_nordic(ticker="BETS-B.ST", download_id=2260001, period="2025-FY",
                   issuers_path=mapped(tmp_path), directory=tmp_path,
                   as_of=AS_OF, opener=opener)


def test_a_download_without_a_period_is_refused(tmp_path):
    with pytest.raises(NordicError, match="--period is required and is MANUAL"):
        run_nordic(ticker="PNDORA.CO", download_id=1457001,
                   issuers_path=mapped(tmp_path), directory=tmp_path,
                   as_of=AS_OF, opener=FEED_OPENER)


def test_a_release_with_no_attachment_says_so_rather_than_scraping(tmp_path):
    with pytest.raises(NordicError, match="carries no attachment"):
        run_nordic(ticker="PNDORA.CO", download_id=1459005, period="2026-Q3",
                   issuers_path=mapped(tmp_path), directory=tmp_path,
                   as_of=AS_OF, opener=FEED_OPENER)


def test_an_id_the_feed_does_not_carry_says_how_much_was_read(tmp_path):
    with pytest.raises(NordicError) as exc:
        run_nordic(ticker="PNDORA.CO", download_id=999999, period="2026-Q3",
                   issuers_path=mapped(tmp_path), directory=tmp_path,
                   as_of=AS_OF, opener=FEED_OPENER)
    message = str(exc.value)
    assert "5 release(s) read of 1027" in message
    # And it names the filter the caller never typed.
    assert "stored default" in message


def test_the_download_report_names_the_url_the_bytes_and_the_digest(tmp_path):
    code, report = run_nordic(ticker="PNDORA.CO", download_id=1457001,
                              attachment_index=0, period="2026-H1",
                              issuers_path=mapped(tmp_path), directory=tmp_path,
                              as_of=AS_OF, now=NOW, opener=FEED_OPENER)
    assert code == 0
    assert "attachment.news.eu.nasdaq.com/aaa" in report
    assert "No figure has been read out of any of these" in report
    assert "PNDORA.CO_2026-H1_inside-information_2026-08-12_en_a0.pdf" in report


# --- reaching back through the feed ----------------------------------------


def paged_opener(pages: list[list[dict]], *, count: int):
    """Serve a different window per `start`, the way the service does."""
    def _open(request, timeout=None):
        url = request.full_url
        if url.startswith("https://attachment"):
            return FakeResponse(b"%PDF-1.7 old report")
        start = int(parse_qs(urlsplit(url).query).get("start", ["0"])[0])
        index = start // MAX_LIMIT
        window = pages[index] if index < len(pages) else []
        return FakeResponse(json.dumps(
            {"results": {"item": window}, "count": count}).encode("utf-8"))
    return _open


def full_page(first_id: int) -> list[dict]:
    return [item(first_id + n, 69, "Changes in company's own shares",
                 f"row {n}", released="2025-01-01", attachments=[PDF])
            for n in range(MAX_LIMIT)]


def test_a_download_reaches_a_report_several_pages_back(tmp_path):
    """Backfilling eight periods means reports the first page does not hold.

    Pandora's feed carries 1,027 releases and a page caps at 200, so the
    interim that closes a two-year history is three pages in. Making the
    caller guess --start until the id appears would turn the one thing this
    module exists for into a manual search.
    """
    buried = item(1200000, 153, "Interim report (Q1 and Q3)",
                  "Pandora delivers 18% organic growth in Q1",
                  released="2024-05-02", attachments=[PDF])
    pages = [full_page(1_500_000), full_page(1_400_000),
             full_page(1_300_000), [buried]]
    opener = paged_opener(pages, count=601)

    code, report = run_nordic(ticker="PNDORA.CO", download_id=1200000,
                              attachment_index=0, period="2024-Q1",
                              issuers_path=mapped(tmp_path), directory=tmp_path,
                              as_of=AS_OF, now=NOW, opener=opener)
    assert code == 0
    assert "PNDORA.CO_2024-Q1_interim-report-q1-and-q3_2024-05-02_en_a0.pdf" in report


def test_the_walk_stops_at_the_end_of_the_feed(tmp_path):
    """Bounded by the feed's own count, so a missing id terminates."""
    opener = paged_opener([full_page(1_500_000), full_page(1_400_000)],
                          count=400)
    with pytest.raises(NordicError, match="400 release\\(s\\) read of 400"):
        run_nordic(ticker="PNDORA.CO", download_id=1, period="2024-Q1",
                   issuers_path=mapped(tmp_path), directory=tmp_path,
                   as_of=AS_OF, opener=opener)


def test_an_empty_feed_names_the_language_filter_as_a_possibility(tmp_path):
    """An issuer that files only in English has no Swedish edition.

    "The stored mapping is wrong" would be the wrong diagnosis, and the
    filter came from the mapping rather than from anything the caller typed.
    """
    empty = opener_for({API_URL: {"results": {"item": []}, "count": 0}})
    with pytest.raises(NordicError) as exc:
        fetch_releases(PANDORA, language="en", opener=empty)
    assert "files in no 'en' edition" in str(exc.value)
    assert "not from the command line" in str(exc.value)


# --- the manifest as a record that repairs itself --------------------------


def test_a_file_on_disk_with_no_manifest_entry_gets_one(tmp_path):
    """Otherwise a document this tool fetched reads as PROVENANCE NOT
    RECORDED for ever -- the one thing the manifest exists to prevent."""
    release = one_release()
    first = download(release, release.attachments[0], ticker="PNDORA.CO",
                     period="2026-H1", directory=tmp_path, now=NOW,
                     opener=FEED_OPENER)
    (tmp_path / MANIFEST_NAME).unlink()

    again = download(release, release.attachments[0], ticker="PNDORA.CO",
                     period="2026-H1", directory=tmp_path, now=NOW,
                     opener=FEED_OPENER)
    assert again.skipped
    assert "manifest entry was missing and has been written" in again.note
    assert again.record["recorded_after_the_fact"]
    assert again.record["sha256"] == first.record["sha256"]
    assert again.record["url"] == first.record["url"]

    stored = json.loads((tmp_path / MANIFEST_NAME).read_text())
    assert [r["file"] for r in stored["downloads"]] == [first.file.name]


def test_a_repaired_record_says_the_same_things_as_a_fresh_one(tmp_path):
    """One definition of an entry, so the two paths cannot disagree."""
    release = one_release()
    fresh = download(release, release.attachments[0], ticker="PNDORA.CO",
                     period="2026-H1", directory=tmp_path, now=NOW,
                     opener=FEED_OPENER).record
    (tmp_path / MANIFEST_NAME).unlink()
    repaired = download(release, release.attachments[0], ticker="PNDORA.CO",
                        period="2026-H1", directory=tmp_path, now=NOW,
                        opener=FEED_OPENER).record
    assert {k: v for k, v in repaired.items()
            if k != "recorded_after_the_fact"} == fresh


# --- two documents can honestly share a period -----------------------------


def test_the_year_end_release_and_the_annual_report_do_not_collide(tmp_path):
    """Betsson files BOTH for 2025, and both are honestly `2025-FY`.

    The year-end report (category 73, 2026-02-05) carries the Q4 and
    full-year figures; the annual report (category 270, 2026-04-01) is the
    audited accounts. Two different documents about one period, separated in
    the filename by the category the exchange filed each under.
    """
    year_end = item(1417957, 73, "Financial Statement Release",
                    "Betsson AB year-end report 1 January - 31 December 2025",
                    released="2026-02-05", company="Betsson AB",
                    market="Main Market, Stockholm", attachments=[PDF])
    annual, _ = parse_releases(BETSSON_FEED)[0], None
    releases, _ = parse_releases({"results": {"item": [year_end]}})

    names = {
        filename_for(ticker="BETS-B.ST", period="2025-FY", release=r,
                     attachment=r.attachments[0], extension=".pdf")
        for r in (releases[0], parse_releases(BETSSON_FEED)[0][0])
    }
    assert len(names) == 2
    assert any("financial-statement-release" in n for n in names)
    assert any("annual-financial-report" in n for n in names)


# --- the committed issuer map ---------------------------------------------


def test_the_committed_map_holds_every_nordic_name_section_5_has_priced():
    """REVIEW-4 report B 5.1 / #5: LIAB.ST was absent from the map.

    Its feed resolves cleanly -- Lindab AB, Main Market Stockholm, 186 hits
    -- and Session A reached the Q2 2026 interim through `vss.nordic` by
    hand without the mapping ever being written. A held name whose only
    route to a primary source is the Nordic feed, and no route recorded.
    """
    issuers = load_issuers(ISSUERS_PATH)
    entry = issuers["LIAB.ST"]
    assert entry.company == "Lindab AB"
    assert entry.market == "Main Market, Stockholm"
    assert entry.resolved is not None


def test_every_mapped_issuer_states_where_and_when_it_was_resolved():
    for ticker, issuer in load_issuers(ISSUERS_PATH).items():
        assert issuer.company and issuer.market, ticker
        assert issuer.resolved is not None, ticker
