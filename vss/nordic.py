"""Report downloads from the Nordic exchange's own disclosure feed.

WHAT THIS IS. `api.news.eu.nasdaq.com` is the news service of the exchange
the companies are listed on, and it answers an anonymous request. Every
regulatory disclosure comes back with the issuer, the market, the
exchange's own category, the release timestamp and -- the part that makes
a fetcher possible at all -- a DIRECT URL to the document the company
filed. Not a link to a page about it. See reference/FETCHER-SURVEY.md for
what was measured, and against what.

WHAT THIS IS NOT. It downloads and it records. **It does not read a
single figure out of anything it downloads.** A PDF that arrives here is
put on disk with its provenance beside it and is never opened; the
figures come out of it BY HAND, into `config/manual/<TICKER>.yaml`, where
each one carries the page it was read from. Between an automatic
downloader and an automatic extractor lies the whole difference between
"the tool fetched the report" and "the tool decided what the report
says", and this module stays on the near side of it.

FIVE THINGS THE FEED DOES THAT A NAIVE CLIENT GETS WRONG, all measured on
2026-08-24 and all encoded below:

1. THE CATEGORY IS THE ISSUER'S FILING CHOICE, NOT A STATEMENT ABOUT
   CONTENT. Pandora's H1 2026 report -- "Pandora delivers 3% organic
   growth in Q2", 2026-08-12 -- is filed under category 428, *Inside
   information*, while its H1 2025 report is under 78, *Half Year
   financial report*. A category whitelist misses the newest interim
   report of one of the two names this was built for. So the default
   listing shows EVERY release carrying an attachment, and `--reports`
   says how many rows it hid.
2. `cnscategory` TAKES ONE VALUE AND SILENTLY IGNORES SEVERAL.
   `cnscategory=270` returns 14 rows, all category 270.
   `cnscategory=270,78,153` returns the unfiltered feed -- which reads
   exactly like "every release is a report". Filtering is therefore done
   HERE, on rows the caller can see, and never by that parameter.
3. `fromDate` AND `toDate` ARE ACCEPTED AND IGNORED. Same failure shape:
   a filter that quietly does nothing. Not used, and not offered.
4. `limit` CAPS AT 200 AND PAGINATION IS `start`, NOT `offset`.
   `offset=200` and `page=2` both return the first window again.
5. ONE DISCLOSURE CAN CARRY SEVERAL FILES, AND THE FIRST IS NOT THE
   REPORT. Betsson's annual report of 2026-04-01 carries an ESEF/iXBRL
   package at index 0 and the PDF at index 1; its 2025-04-04 filing
   carries two PDFs. Nothing here guesses which one was meant.

Oslo is not on this service. Oslo Børs is Euronext, and a `.OL` ticker is
handed to `vss/oslo.py` -- Euronext Oslo's own NewsWeb feed, the Norwegian
Officially Appointed Mechanism -- by `run_nordic`, which dispatches on the
suffix before it reads the Nasdaq mapping. The two feeds share this module's
`Release`, `filename_for`, `download` and manifest; they share no endpoint,
no parameter and no failure mode.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

from .config import ConfigError
from .rules import PERIOD_SPANS, period_parts
from .source import USER_AGENT

log = logging.getLogger(__name__)

API_URL = "https://api.news.eu.nasdaq.com/news/query.action"
TIMEOUT_SECONDS = 60

#: The service's own ceiling. Asking for 400 returns 200 and says nothing.
MAX_LIMIT = 200

#: Where downloaded documents land, and where the manifest sits beside them.
SOURCES_DIR = Path("sources")
MANIFEST_NAME = "manifest.json"

#: The ticker -> (market, company) mapping. RESOLVED ONCE and stored, not
#: worked out on every call: the service has no company directory to look a
#: ticker up in, so resolution is a full-text search whose answer a human
#: has to confirm. Doing that per call would mean re-deciding, silently and
#: possibly differently, which issuer the ticker means.
ISSUERS_PATH = Path("config/nordic_issuers.yaml")

#: Documents are capped rather than unbounded. An annual report is legitimately
#: large -- JD's 2026 accounts are 9 MB and an ESEF package 26 MB -- so the cap
#: is set where a real document still fits and a runaway response does not.
MAX_DOWNLOAD_BYTES = 64_000_000

#: Yahoo suffix -> the markets this service publishes under, most likely
#: first. Only used to narrow a RESOLVE search; the stored mapping names one
#: market exactly.
SUFFIX_MARKETS: dict[str, tuple[str, ...]] = {
    ".ST": ("Main Market, Stockholm", "First North Sweden"),
    ".CO": ("Main Market, Copenhagen", "First North Denmark"),
    ".HE": ("Main Market, Helsinki", "First North Finland"),
    ".IC": ("Main Market, Iceland", "First North Iceland"),
    ".TL": ("Main Market, Tallinn",),
    ".RG": ("Main Market, Riga",),
    ".VS": ("Main Market, Vilnius", "First North Lithuania"),
}

#: Suffixes this service does not serve, and what to say instead of nothing.
#: An empty result set reads as "this company published no reports", which is
#: a different and much worse answer than "wrong exchange".
NOT_SERVED: dict[str, str] = {
    ".OL": ("Oslo Børs is operated by Euronext, not by Nasdaq, and this "
            "service publishes no Oslo market. A Norwegian issuer is served "
            "by Euronext Oslo's own NewsWeb feed, which `vss/oslo.py` "
            "implements and `vss nordic --ticker <X>.OL` dispatches to; this "
            "function is the Nasdaq mapping and .OL is never in it."),
}

#: Categories under which the Nordic exchanges file periodic financial
#: reports, as observed on Pandora and Betsson. Used ONLY by `--reports`,
#: and never to decide what a document IS: see rule 1 in the module
#: docstring. Pandora's H1 2026 report is not in this set.
REPORT_CATEGORIES: frozenset[str] = frozenset({
    "annual financial report",
    "half year financial report",
    "half-year financial report",
    "half-yearly information",
    "interim report (q1 and q3)",
    "quarterly report",
    "financial statement release",
})

#: Extension by mime type. The extension follows the ACTUAL type of the
#: bytes that arrived, never the type the caller assumed: an ESEF package
#: saved as `.pdf` is a file whose name is a false statement about it.
EXTENSIONS: dict[str, str] = {
    "application/pdf": ".pdf",
    "application/zip": ".zip",
    # The feed uses both spellings for the same thing, and an ESEF package
    # has arrived under each.
    "application/x-zip-compressed": ".zip",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "application/vnd.ms-excel": ".xls",
    "text/html": ".html",
    "text/plain": ".txt",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

#: Magic bytes, so the recorded type is what arrived rather than what was
#: promised. A mismatch is REPORTED and the file is still kept -- the
#: discrepancy is itself provenance -- but the extension follows the bytes.
ZIP_TYPES = frozenset({"application/zip", "application/x-zip-compressed"})

MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"%PDF-", "application/pdf"),
    (b"PK\x03\x04", "application/zip"),
    (b"\xd0\xcf\x11\xe0", "application/msword"),
)

PERIOD_PATTERN = re.compile(r"^\d{4}-(Q[1-4]|H[12]|FY)$")

ORIGIN = "nasdaq-nordic"

#: What a document fetched by THIS module is. A second backend writing the
#: same manifest says its own (see `Release.primary_source_basis`).
PRIMARY_SOURCE_BASIS = (
    "the document the issuer filed with its exchange, taken from the "
    "exchange's own disclosure record"
)


class NordicError(ConfigError):
    """Any problem with the feed, the mapping or a download.

    A ConfigError so the CLI exits 2 on it, the way it does for a malformed
    watchlist: a fetch that cannot be trusted is not something to carry on past.
    """


# --- the stored mapping ---------------------------------------------------


@dataclass(frozen=True)
class Issuer:
    ticker: str
    market: str
    company: str
    #: Which language edition to prefer. Betsson files every report twice,
    #: in Swedish and English, and the two are separate disclosures with
    #: separate documents. Stated per issuer rather than assumed.
    language: str | None = None
    resolved: date | None = None
    note: str | None = None


def load_issuers(path: Path = ISSUERS_PATH) -> dict[str, Issuer]:
    if not path.exists():
        return {}
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise NordicError(f"{path} is not valid YAML: {exc}")
    if document is None:
        return {}
    if not isinstance(document, Mapping) or "issuers" not in document:
        raise NordicError(f"{path} must be a mapping with a top-level 'issuers:' key")
    raw = document["issuers"] or {}
    if not isinstance(raw, Mapping):
        raise NordicError(f"{path}: 'issuers:' must be a mapping of ticker to entry")

    out: dict[str, Issuer] = {}
    allowed = {"market", "company", "language", "resolved", "note"}
    for ticker, entry in raw.items():
        where = f"{path}: issuer {ticker}"
        if not isinstance(entry, Mapping):
            raise NordicError(f"{where}: expected a mapping")
        unknown = set(entry) - allowed
        if unknown:
            raise NordicError(f"{where}: unknown key(s) {', '.join(sorted(unknown))}. "
                              f"Allowed: {', '.join(sorted(allowed))}")
        for required in ("market", "company"):
            if not str(entry.get(required) or "").strip():
                raise NordicError(f"{where}: {required} is required")
        resolved = entry.get("resolved")
        if isinstance(resolved, datetime):
            resolved = resolved.date()
        elif isinstance(resolved, str):
            resolved = date.fromisoformat(resolved.strip())
        elif resolved is not None and not isinstance(resolved, date):
            raise NordicError(f"{where}: resolved must be a YYYY-MM-DD date")
        out[str(ticker).strip().upper()] = Issuer(
            ticker=str(ticker).strip().upper(),
            market=str(entry["market"]).strip(),
            company=str(entry["company"]).strip(),
            language=(str(entry["language"]).strip().lower()
                      if entry.get("language") else None),
            resolved=resolved,
            note=(str(entry["note"]).strip() if entry.get("note") else None),
        )
    return out


def issuer_for(ticker: str, *, path: Path = ISSUERS_PATH) -> Issuer:
    key = ticker.strip().upper()
    suffix = key[key.rfind("."):] if "." in key else ""
    if suffix in NOT_SERVED:
        raise NordicError(f"{key}: {NOT_SERVED[suffix]}")
    issuers = load_issuers(path)
    if key not in issuers:
        raise NordicError(
            f"{key} has no entry in {path}. This service has no company "
            f"directory to look a ticker up in, so the market and the "
            f"company string have to be established once and stored. Run "
            f"`vss nordic --resolve --ticker {key} --name <search text>` to "
            f"see the candidates, then re-run it with --write."
        )
    return issuers[key]


# --- the feed -------------------------------------------------------------


@dataclass(frozen=True)
class Attachment:
    index: int
    mimetype: str
    file_name: str
    url: str


@dataclass(frozen=True)
class Release:
    disclosure_id: int
    category_id: int
    category: str
    headline: str
    language: str
    market: str
    company: str
    released: str
    message_url: str
    attachments: tuple[Attachment, ...] = ()
    #: WHICH FEED THIS ROW CAME OFF, and the sentence that says what the
    #: bytes ARE. Both default to this module's own Nasdaq Nordic answer and
    #: are overridden by a second backend building the same shape --
    #: `vss/oslo.py` for Euronext Oslo's NewsWeb. A record must never say
    #: `nasdaq-nordic` about a document Nasdaq never carried.
    origin: str = ORIGIN
    primary_source_basis: str = PRIMARY_SOURCE_BASIS
    #: Feed-specific provenance, carried into the manifest entry unchanged.
    #: Pairs rather than a dict so the Release stays hashable and frozen.
    extra: tuple[tuple[str, Any], ...] = ()

    @property
    def released_date(self) -> str:
        return self.released[:10]

    @property
    def is_report_category(self) -> bool:
        return self.category.strip().lower() in REPORT_CATEGORIES


def _get(url: str, *, opener=None) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        opener = opener or urllib.request.urlopen
        with opener(request, timeout=TIMEOUT_SECONDS) as response:
            return response.read(MAX_DOWNLOAD_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise NordicError(f"HTTP {exc.code} fetching {url}") from exc
    except Exception as exc:  # noqa: BLE001 - reported, never swallowed
        raise NordicError(f"{type(exc).__name__} fetching {url}: {exc}") from exc


def query_url(issuer: Issuer, *, limit: int, start: int,
              language: str | None) -> str:
    """The exact request, built in one place so a test can assert on it.

    `cnscategory` is deliberately absent -- it silently ignores a multi-value
    argument and returns the unfiltered feed, which reads as "everything is a
    report". `fromDate`/`toDate` are absent for the same reason: accepted,
    ignored. Selection happens on rows the caller can see.
    """
    if limit > MAX_LIMIT:
        raise NordicError(
            f"limit {limit} is above the service's ceiling of {MAX_LIMIT}. It "
            f"does not error on a larger number -- it returns {MAX_LIMIT} rows "
            f"and says nothing -- so a page beyond that must be asked for with "
            f"start={MAX_LIMIT}."
        )
    params = {
        "type": "json",
        "showAttachments": "true",
        "showCnsSpecific": "true",
        "showCompany": "true",
        "countResults": "true",
        "market": issuer.market,
        "company": issuer.company,
        "limit": str(limit),
    }
    if start:
        params["start"] = str(start)
    if language:
        params["language"] = language
    return f"{API_URL}?{urllib.parse.urlencode(params)}"


def parse_releases(payload: Mapping) -> tuple[list[Release], int | None]:
    results = payload.get("results") or {}
    items = results.get("item") or []
    if isinstance(items, Mapping):
        items = [items]
    out: list[Release] = []
    for item in items:
        raw = item.get("attachment") or []
        if isinstance(raw, Mapping):
            raw = [raw]
        attachments = tuple(
            Attachment(index=n,
                       mimetype=str(a.get("mimetype") or "").strip(),
                       file_name=str(a.get("fileName") or "").strip(),
                       url=str(a.get("attachmentUrl") or "").strip())
            for n, a in enumerate(raw) if a.get("attachmentUrl")
        )
        out.append(Release(
            disclosure_id=int(item["disclosureId"]),
            category_id=int(item.get("categoryId") or 0),
            category=str(item.get("cnsCategory") or "").strip(),
            headline=str(item.get("headline") or "").strip(),
            language=str(item.get("language") or "").strip().lower(),
            market=str(item.get("market") or "").strip(),
            company=str(item.get("company") or "").strip(),
            released=str(item.get("releaseTime") or item.get("published") or "").strip(),
            message_url=str(item.get("messageUrl") or "").strip(),
            attachments=attachments,
        ))
    count = payload.get("count")
    return out, (int(count) if count is not None else None)


def fetch_releases(issuer: Issuer, *, limit: int = MAX_LIMIT, start: int = 0,
                   language: str | None = None,
                   opener=None) -> tuple[list[Release], int | None]:
    """One page of one issuer's disclosures, newest first."""
    url = query_url(issuer, limit=limit, start=start, language=language)
    raw = _get(url, opener=opener)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise NordicError(f"{url}: response is not JSON ({exc})") from exc
    releases, count = parse_releases(payload)
    # The service answers a company it does not recognise with an empty list
    # rather than an error, and an empty list reads as "this issuer published
    # nothing". Say which of the two it is.
    if not releases and not start:
        why = [
            "the stored mapping is wrong -- the company string must match the "
            "service's own spelling exactly",
        ]
        if language:
            why.append(
                f"this issuer files in no {language!r} edition. The filter came "
                + ("from its stored `language:` in the mapping, not from the "
                   "command line" if language == issuer.language
                   else "from --language") +
                "; drop it to see every edition"
            )
        why.append("this issuer has published nothing")
        raise NordicError(
            f"the feed returned no disclosure at all for company "
            f"{issuer.company!r} on market {issuer.market!r}. Either "
            + "; or ".join(why) + f". Re-run `vss nordic --resolve --ticker "
            f"{issuer.ticker}` to see what the service calls it."
        )
    return releases, count


def find_release(issuer: Issuer, disclosure_id: int, *, start: int = 0,
                 language: str | None = None, opener=None) -> Release:
    """One disclosure, looked for across as many pages as the feed holds.

    The service caps a page at 200 and Pandora's feed carries 1,027 releases,
    so the report that closes an eight-period history is several pages back.
    Requiring the caller to guess `--start 200`, `--start 400` until the id
    appears would make backfill -- the whole reason this module exists --
    a manual search. The walk is bounded by the feed's own `count`, and each
    page is logged so a long one is visible rather than silent.
    """
    seen = 0
    total: int | None = None
    while True:
        releases, count = fetch_releases(issuer, limit=MAX_LIMIT, start=start,
                                         language=language, opener=opener)
        if total is None:
            total = count
        seen += len(releases)
        for release in releases:
            if release.disclosure_id == disclosure_id:
                return release
        log.info("%s: disclosure %d not in rows %d-%d%s", issuer.ticker,
                 disclosure_id, start + 1, start + len(releases),
                 f" of {total}" if total else "")
        if not releases or len(releases) < MAX_LIMIT:
            break
        start += MAX_LIMIT
        if total is not None and start >= total:
            break

    filtered = (f" The feed was read with language={language!r}"
                + ("" if language is None else
                   ", which is this issuer's stored default"
                   if language == issuer.language else ", as asked for")
                + ", so an edition in another language was never fetched."
                ) if language else ""
    raise NordicError(
        f"disclosure {disclosure_id} is not in this issuer's feed: "
        f"{seen} release(s) read"
        + (f" of {total} the service reports" if total else "") + "."
        + filtered +
        f" Check the id against `vss nordic --ticker {issuer.ticker}`."
    )


# --- resolution -----------------------------------------------------------


@dataclass(frozen=True)
class Candidate:
    market: str
    company: str
    hits: int
    newest: str
    languages: tuple[str, ...]


def resolve(ticker: str, search: str, *, opener=None) -> list[Candidate]:
    """Candidate (market, company) pairs for a ticker, measured not guessed.

    The search is FULL TEXT and matches the body of a release, so it returns
    issuers that merely MENTION the term -- a search for "Pandora" on the
    Copenhagen market returns Royal UNIBREW, Bang & Olufsen and, because the
    market parameter is applied loosely once `freeText` is present, Boozt AB
    from Stockholm. Candidates are therefore grouped on the feed's OWN
    `company` and `market` fields rather than on what was asked for, with the
    hit count and the newest release beside each, and the owner picks.
    Nothing is auto-selected: the watchlist calls PNDORA.CO "PANDORA" and the
    service calls it "Pandora A/S", so there is no equality test that would
    be safe.
    """
    key = ticker.strip().upper()
    suffix = key[key.rfind("."):] if "." in key else ""
    if suffix in NOT_SERVED:
        raise NordicError(f"{key}: {NOT_SERVED[suffix]}")
    markets = SUFFIX_MARKETS.get(suffix)
    if not markets:
        raise NordicError(
            f"{key}: the suffix {suffix or '(none)'} is not one this service "
            f"publishes. Known: {', '.join(sorted(SUFFIX_MARKETS))}."
        )

    found: dict[tuple[str, str], list[Release]] = {}
    for market in markets:
        params = {
            "type": "json", "showCompany": "true", "showAttachments": "true",
            "countResults": "true", "market": market, "freeText": search,
            "limit": str(MAX_LIMIT),
        }
        url = f"{API_URL}?{urllib.parse.urlencode(params)}"
        releases, _ = parse_releases(json.loads(_get(url, opener=opener).decode("utf-8")))
        for release in releases:
            found.setdefault((release.market, release.company), []).append(release)

    candidates = [
        Candidate(market=market, company=company, hits=len(rows),
                  newest=max(r.released for r in rows)[:10],
                  languages=tuple(sorted({r.language for r in rows if r.language})))
        for (market, company), rows in found.items()
    ]
    return sorted(candidates, key=lambda c: (-c.hits, c.company))


def issuer_block(ticker: str, candidate: Candidate, *, as_of: date,
                 language: str | None = None) -> str:
    """The YAML to paste, or to write with --write. One entry, nothing else."""
    lines = [f"  {ticker.strip().upper()}:",
             f'    market: "{candidate.market}"',
             f'    company: "{candidate.company}"']
    if language:
        lines.append(f"    language: {language}")
    lines.append(f"    resolved: {as_of.isoformat()}")
    lines.append(f'    note: "matched {candidate.hits} release(s) on the feed, '
                 f'newest {candidate.newest}"')
    return "\n".join(lines)


def write_issuer(ticker: str, candidate: Candidate, *, as_of: date,
                 language: str | None = None,
                 path: Path = ISSUERS_PATH) -> Path:
    """Append ONE entry, backing the file up first, never replacing one.

    The same contract phase 6 has with the watchlist: this file is the
    owner's, a backup exists before it is touched, and an entry already
    there is never overwritten by a tool.
    """
    key = ticker.strip().upper()
    existing = load_issuers(path)
    if key in existing:
        raise NordicError(
            f"{path} already has an entry for {key} "
            f"({existing[key].company} on {existing[key].market}). It is not "
            f"replaced: edit the file yourself if the mapping is wrong."
        )
    backup = None
    if path.exists():
        backup = path.with_suffix(path.suffix + f".bak-{as_of.isoformat()}")
        shutil.copy2(path, backup)
        text = path.read_text(encoding="utf-8").rstrip("\n") + "\n"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = ("# ticker -> the market and company string "
                "api.news.eu.nasdaq.com needs.\n"
                "# Resolved once by `vss nordic --resolve` and stored; never "
                "worked out per call.\n"
                "issuers:\n")
    path.write_text(text + issuer_block(key, candidate, as_of=as_of,
                                        language=language) + "\n",
                    encoding="utf-8")
    log.info("wrote %s to %s%s", key, path,
             f" (backup {backup})" if backup else "")
    return path


# --- naming ---------------------------------------------------------------


def slug(text: str) -> str:
    """A filename-safe form of the exchange's own category string."""
    normalised = unicodedata.normalize("NFKD", text)
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", ascii_only)).strip("-") or "uncategorised"


def check_period(period: str) -> str:
    """The period label a document COVERS. MANUAL, and shape-checked only.

    The label is the owner's to state and is never inferred. Nothing in the
    feed says which fiscal period a document covers -- the category is the
    issuer's filing choice (Pandora's H1 2026 report is filed as *Inside
    information*), the headline is prose, and the release date is when it was
    published, not what it covers.

    ONLY THE SHAPE IS CHECKED. `rules.period_kind_allowed` is deliberately
    NOT applied: it governs which labels a ticker may hold in its `quarters:`
    history, where the overlap guard needs one resolution per ticker. A
    QUARTERLY reporter still publishes an ANNUAL report, so `2025-FY` is the
    right label for PNDORA.CO's annual accounts and that rule would reject it.
    Two different questions; do not merge them.
    """
    label = (period or "").strip()
    if not PERIOD_PATTERN.match(label):
        raise NordicError(
            f"period {period!r} is not a label the schema knows. Use "
            f"YYYY-Qn, YYYY-H1, YYYY-H2 or YYYY-FY -- the same vocabulary as "
            f"the watchlist's quarters: and config/manual/<TICKER>.yaml, so a "
            f"downloaded document and the figures read out of it carry one "
            f"period label between them."
        )
    return label


def filename_for(*, ticker: str, period: str, release: Release,
                 attachment: Attachment, extension: str) -> str:
    """`TICKER_PERIOD_category_YYYY-MM-DD_lang_aN.ext` -- deterministic.

    The four fields asked for lead: ticker, period, category, publication
    date. Language and attachment index follow because without them the name
    is NOT unique -- Betsson files every report twice, in Swedish and in
    English, and its 2026 annual filing carries two documents whose four
    leading fields are identical.
    """
    parts = [ticker.strip().upper(), period, slug(release.category),
             release.released_date]
    parts.append(release.language or "xx")
    parts.append(f"a{attachment.index}")
    return "_".join(parts) + extension


# --- the manifest ---------------------------------------------------------
#
# The record of what a file on disk IS. It answers one question: is this
# document the thing the company filed with its exchange, or something
# somebody put in the directory? A file with no entry here is NOT recorded
# as secondary -- it is PROVENANCE NOT RECORDED, the same third state
# DATA MISSING is everywhere else in this project. The `sources/` files
# that predate this module are exactly that, and none of them is
# back-filled with a guess about where it came from.
#
# WHAT `figures_read` MEANS, exactly one thing: nothing has been taken from
# this document into `config/manual/<TICKER>.yaml`. It is NOT a claim that
# nobody ever opened the file. Reading a document is a SEPARATE ACT from
# fetching it -- a person reading a page, or another tool measuring a
# package -- and this flag does not record it. The note said otherwise
# until 2026-08-24, when the ESEF measurement read tagged values out of a
# recorded package and made the old wording false while the flag itself
# stayed true.

MANIFEST_SCHEMA = "vss/nordic manifest v1"
MANIFEST_NOTE = (
    "Each entry records a document downloaded from the issuer's own exchange "
    "disclosure feed: the URL it came from, when, how many bytes arrived and "
    "the SHA-256 of those bytes. A file in this directory with NO entry here "
    "has PROVENANCE NOT RECORDED -- that is not the same as being secondary, "
    "and nothing here guesses about a file it did not fetch. "
    "THE FETCHER ITSELF NEVER PARSES: it downloads and records, and opens "
    "nothing it has downloaded. "
    "`figures_read` means one thing and only that: nothing has been taken "
    "from this document into config/manual/<TICKER>.yaml. Reading a document "
    "is a separate act -- by a person, or by another tool -- and this flag "
    "does not record it. A figure may have been read out of a file whose row "
    "still says false, and the row is not wrong."
)


def manifest_path(directory: Path = SOURCES_DIR) -> Path:
    return Path(directory) / MANIFEST_NAME


def load_manifest(directory: Path = SOURCES_DIR) -> dict:
    path = manifest_path(directory)
    if not path.exists():
        return {"schema": MANIFEST_SCHEMA, "note": MANIFEST_NOTE, "downloads": []}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise NordicError(f"{path} is not readable JSON ({exc}). It is the "
                          f"provenance record; it is not rewritten over.")
    document.setdefault("downloads", [])
    return document


def save_manifest(document: dict, directory: Path = SOURCES_DIR) -> Path:
    path = manifest_path(directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    document["schema"] = MANIFEST_SCHEMA
    document["note"] = MANIFEST_NOTE
    # `or ""` and not a default: the EDGAR and issuer-website routes write
    # `released: null` where the source states no publication date, and 16
    # such records were in this manifest by 2026-09-08. `dict.get(k, "")`
    # returns the None that IS there, and sorting str against None raises --
    # so every `vss nordic --download` failed AFTER writing the file and
    # BEFORE writing its entry, which is precisely how a document ends up on
    # disk reading as PROVENANCE NOT RECORDED. Found 2026-09-08 on the first
    # Oslo download; the repair path in `download` writes those entries back.
    document["downloads"] = sorted(
        document["downloads"],
        key=lambda r: (r.get("ticker") or "", r.get("released") or "",
                       r.get("file") or ""),
    )
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return path


def manifest_entry(document: dict, file_name: str) -> dict | None:
    for record in document.get("downloads", []):
        if record.get("file") == file_name:
            return record
    return None


# --- the download ---------------------------------------------------------


def sniff(head: bytes, declared: str) -> tuple[str, str | None]:
    """(type of the bytes that arrived, a note when it is not what was declared)."""
    for magic, kind in MAGIC:
        if head.startswith(magic):
            # An xlsx and an ESEF .xbri are both ZIP containers, so the
            # magic agreeing with a more specific declared type is not a
            # disagreement -- it is the same fact at two resolutions.
            if declared and kind != declared and not (
                kind == "application/zip" and (
                    declared.startswith("application/vnd.openxmlformats")
                    or declared in ZIP_TYPES)
            ):
                return kind, (f"the feed declared {declared} and the bytes are "
                              f"{kind}; the extension follows the bytes")
            return declared or kind, None
    return declared, None


@dataclass(frozen=True)
class Download:
    file: Path
    record: dict
    skipped: bool = False
    note: str | None = None


def download(release: Release, attachment: Attachment, *, ticker: str,
             period: str, directory: Path = SOURCES_DIR,
             now: datetime | None = None, opener=None) -> Download:
    """Fetch one document, name it, record it. Reads nothing out of it.

    A file already on disk is NOT silently replaced. Where the bytes are
    identical the download is skipped and said so; where they DIFFER the run
    fails and names both digests -- the issuer replaced the document, or two
    filings collided, and either is an event to look at rather than an
    overwrite to perform.
    """
    period = check_period(period)
    stamp = now or datetime.now().astimezone()

    raw = _get(attachment.url, opener=opener)
    if len(raw) > MAX_DOWNLOAD_BYTES:
        raise NordicError(f"{attachment.url}: response exceeds "
                          f"{MAX_DOWNLOAD_BYTES} bytes")
    if not raw:
        raise NordicError(f"{attachment.url}: the response was empty")

    kind, mismatch = sniff(raw[:8], attachment.mimetype)
    extension = EXTENSIONS.get(kind) or Path(attachment.file_name).suffix or ".bin"
    name = filename_for(ticker=ticker, period=period, release=release,
                        attachment=attachment, extension=extension)
    digest = hashlib.sha256(raw).hexdigest()

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    document = load_manifest(directory)

    if target.exists():
        on_disk = hashlib.sha256(target.read_bytes()).hexdigest()
        if on_disk == digest:
            record = manifest_entry(document, name)
            if record is not None:
                return Download(target, record, skipped=True,
                                note=f"already on disk, byte-identical "
                                     f"({digest[:12]}…)")
            # On disk, fetched by this tool, and NOT in the manifest: the
            # record was deleted, or a run died between writing the file and
            # writing the record. Leaving it would make a document this tool
            # fetched read as PROVENANCE NOT RECORDED for ever, which is the
            # one thing the manifest exists to prevent. Everything the entry
            # needs is in hand, so it is written.
            record = _record_for(release, attachment, ticker=ticker,
                                 period=period, name=name, kind=kind,
                                 size=len(raw), digest=digest, stamp=stamp,
                                 mismatch=mismatch)
            record["recorded_after_the_fact"] = (
                "the file was already on disk and byte-identical, with no "
                "manifest entry; the entry was written from the feed record "
                "and the bytes on disk"
            )
            document["downloads"].append(record)
            save_manifest(document, directory)
            log.info("%s: repaired the manifest entry for %s", ticker, name)
            return Download(target, record, skipped=True,
                            note=f"already on disk, byte-identical "
                                 f"({digest[:12]}…); its manifest entry was "
                                 f"missing and has been written")
        raise NordicError(
            f"{target} already exists and its content DIFFERS from what the "
            f"feed serves now.\n  on disk: sha256 {on_disk}\n  fetched: sha256 "
            f"{digest}\nNothing is overwritten. Either the issuer replaced the "
            f"document or two filings landed on one name; look at both before "
            f"deciding which is the record."
        )

    target.write_bytes(raw)
    record = _record_for(release, attachment, ticker=ticker, period=period,
                         name=name, kind=kind, size=len(raw), digest=digest,
                         stamp=stamp, mismatch=mismatch)
    document["downloads"].append(record)
    save_manifest(document, directory)
    log.info("%s: saved %s (%d bytes) from %s", ticker, name, len(raw),
             attachment.url)
    return Download(target, record, note=mismatch)


def _record_for(release: Release, attachment: Attachment, *, ticker: str,
                period: str, name: str, kind: str, size: int, digest: str,
                stamp: datetime, mismatch: str | None) -> dict:
    """The manifest entry. ONE definition, so a repaired record and a fresh
    one cannot say different things about the same file."""
    record = {
        "file": name,
        "ticker": ticker.strip().upper(),
        "period": period,
        "origin": release.origin,
        "primary_source": True,
        "primary_source_basis": release.primary_source_basis,
        "market": release.market,
        "company": release.company,
        "disclosure_id": release.disclosure_id,
        "category_id": release.category_id,
        "category": release.category,
        "headline": release.headline,
        "language": release.language,
        "released": release.released,
        "message_url": release.message_url,
        "attachment_index": attachment.index,
        "attachment_file_name": attachment.file_name,
        "url": attachment.url,
        "declared_type": attachment.mimetype,
        "content_type": kind,
        "bytes": size,
        "sha256": digest,
        "downloaded_at": stamp.isoformat(timespec="seconds"),
        "figures_read": False,
    }
    if mismatch:
        record["type_note"] = mismatch
    # Feed-specific provenance last, and it may not quietly rewrite a key
    # this function has already stated: a second backend adds to the record,
    # it does not edit it.
    for key, value in release.extra:
        if key in record:
            raise NordicError(
                f"the feed backend tried to overwrite manifest key {key!r} "
                f"through Release.extra. The common keys are this function's; "
                f"a backend adds its own beside them."
            )
        record[key] = value
    return record


# --- reports --------------------------------------------------------------


def render_listing(issuer: Issuer, releases: Sequence[Release], *,
                   count: int | None, reports_only: bool, hidden: int,
                   start: int, language: str | None) -> str:
    out = [f"# vss nordic -- {issuer.ticker} ({issuer.company}) -- "
           f"{issuer.market}", ""]
    out.append(f"**SOURCE:** `{API_URL}` — the exchange's own disclosure feed. "
               f"Free, no account. Nothing below has been opened or read; this "
               f"is a list of documents, not of figures.")
    out.append("")
    total = f"{count:,}" if count is not None else "unknown"
    out.append(f"- releases carried by the feed for this issuer: {total}")
    out.append(f"- window shown: rows {start + 1}–{start + len(releases)} "
               f"(the service caps a page at {MAX_LIMIT}; ask for the next with "
               f"`--start {start + MAX_LIMIT}`)")
    out.append(f"- language filter: {language or 'none — every edition shown'}")
    out.append("")

    if reports_only:
        out.append("## FILTERED TO REPORT CATEGORIES")
        out.append("")
        out.append(f"**{hidden} release(s) in this window are NOT shown.** The "
                   f"filter is on the EXCHANGE'S CATEGORY, which is the "
                   f"issuer's filing choice and not a statement about what a "
                   f"document contains. Pandora's H1 2026 report — *\"Pandora "
                   f"delivers 3% organic growth in Q2\"*, 2026-08-12 — is filed "
                   f"under `Inside information`, and this filter hides it. Run "
                   f"without `--reports` before concluding a report does not "
                   f"exist.")
        out.append("")

    out.append("## RELEASES CARRYING A DOCUMENT")
    out.append("")
    if not releases:
        out.append("None in this window.")
        out.append("")
        return "\n".join(out)

    out.append("| Released | id | Category | Lang | Headline | Files |")
    out.append("|---|---|---|---|---|---|")
    for release in releases:
        files = ", ".join(f"`a{a.index}` {a.mimetype.split('/')[-1]}"
                          for a in release.attachments) or "—"
        out.append(f"| {release.released_date} | `{release.disclosure_id}` | "
                   f"{release.category} | {release.language} | "
                   f"{release.headline[:64]} | {files} |")
    out.append("")
    out.append("## TO DOWNLOAD ONE")
    out.append("")
    out.append("The PERIOD IS YOURS TO STATE. Nothing in the feed says which "
               "fiscal period a document covers: the category is a filing "
               "choice, the headline is prose and the release date is when it "
               "was published. Use the same labels the watchlist and "
               "`config/manual/<TICKER>.yaml` use, so a document and the "
               "figures read out of it carry one label between them.")
    out.append("")
    out.append("```")
    example = releases[0]
    index = example.attachments[0].index if example.attachments else 0
    out.append(f"vss nordic --ticker {issuer.ticker} "
               f"--download {example.disclosure_id} --attachment {index} "
               f"--period YYYY-Qn")
    out.append("```")
    out.append("")
    return "\n".join(out)


def render_download(ticker: str, results: Sequence[Download]) -> str:
    out = [f"# vss nordic -- downloaded for {ticker.strip().upper()}", ""]
    out.append("**No figure has been read out of any of these.** They are on "
               "disk with their provenance recorded beside them; the numbers "
               "come out by hand, into `config/manual/<TICKER>.yaml`, each one "
               "carrying the page it was read from.")
    out.append("")
    out.append("| File | Period | Category | Released | Bytes | SHA-256 | From |")
    out.append("|---|---|---|---|---|---|---|")
    for item in results:
        r = item.record
        out.append(f"| `{r.get('file', item.file.name)}` | {r.get('period', '')} | "
                   f"{r.get('category', '')} | {r.get('released', '')[:10]} | "
                   f"{r.get('bytes', 0):,} | `{str(r.get('sha256', ''))[:16]}…` | "
                   f"{r.get('url', '')} |")
    out.append("")
    for item in results:
        if item.skipped:
            out.append(f"- `{item.file.name}`: {item.note}")
        elif item.note:
            out.append(f"- `{item.file.name}`: {item.note}")
    out.append("")
    out.append(f"Manifest: `{manifest_path()}`")
    out.append("")
    return "\n".join(out)


def render_resolve(ticker: str, search: str, candidates: Sequence[Candidate],
                   *, as_of: date, written: Path | None) -> str:
    out = [f"# vss nordic --resolve -- {ticker.strip().upper()}", ""]
    out.append(f"Searched the feed for `{search}` across the markets the "
               f"ticker's suffix belongs to. **The search is FULL TEXT**: it "
               f"matches the body of a release, so an issuer that merely "
               f"mentions the term appears here. Candidates are grouped on the "
               f"feed's own `company` and `market` fields, not on what was "
               f"asked for -- alongside `freeText` the market parameter is "
               f"applied loosely and a row from another market does come "
               f"back, so the market column below is the row's own and is "
               f"what the mapping must be written from.")
    out.append("")
    if not candidates:
        out.append("No candidate at all. Try a different search term — the "
                   "service's spelling of a company is frequently not the "
                   "watchlist's (PNDORA.CO is `PANDORA` in the watchlist and "
                   "`Pandora A/S` here).")
        out.append("")
        return "\n".join(out)

    out.append("| Company (the string the API needs) | Market | Hits | Newest | Languages |")
    out.append("|---|---|---|---|---|")
    for c in candidates:
        out.append(f"| `{c.company}` | {c.market} | {c.hits} | {c.newest} | "
                   f"{', '.join(c.languages) or '—'} |")
    out.append("")
    if written:
        out.append(f"## WRITTEN to `{written}`")
        out.append("")
        out.append("The top candidate was written. An entry already present is "
                   "never replaced, and the file was backed up first.")
    else:
        out.append("## PROPOSED — NOT WRITTEN")
        out.append("")
        out.append("Check that the top row is the company you mean, then re-run "
                   "with `--write`, or paste this into "
                   f"`{ISSUERS_PATH}` yourself:")
    out.append("")
    out.append("```yaml")
    out.append("issuers:")
    out.append(issuer_block(ticker, candidates[0], as_of=as_of))
    out.append("```")
    out.append("")
    return "\n".join(out)


# --- the command ----------------------------------------------------------


def run_nordic(*, ticker: str, resolve_name: str | None = None,
               write: bool = False, download_id: int | None = None,
               attachment_index: int | None = None, period: str | None = None,
               reports_only: bool = False, limit: int = MAX_LIMIT,
               start: int = 0, language: str | None = None,
               issuers_path: Path = ISSUERS_PATH,
               directory: Path = SOURCES_DIR,
               as_of: date | None = None, now: datetime | None = None,
               opener=None) -> tuple[int, str]:
    """Returns (exit_code, report_markdown)."""
    as_of = as_of or date.today()
    key = ticker.strip().upper()

    # Oslo Børs is Euronext and has nothing to do with this feed. The
    # dispatch is on the SUFFIX and happens before the Nasdaq mapping is
    # read, so an Oslo ticker never touches `nordic_issuers.yaml` and
    # `_on_nordic_feed` keeps telling the truth about what Nasdaq carries.
    if key.endswith(".OL"):
        from .oslo import run_oslo
        return run_oslo(ticker=key, resolve_name=resolve_name, write=write,
                        download_id=download_id,
                        attachment_index=attachment_index, period=period,
                        reports_only=reports_only, language=language,
                        directory_path=directory, as_of=as_of, now=now,
                        opener=opener)

    if resolve_name is not None:
        candidates = resolve(key, resolve_name, opener=opener)
        written = None
        if write and candidates:
            written = write_issuer(key, candidates[0], as_of=as_of,
                                   language=language, path=issuers_path)
        return (0 if candidates else 1), render_resolve(
            key, resolve_name, candidates, as_of=as_of, written=written)

    issuer = issuer_for(key, path=issuers_path)
    language = language or issuer.language

    if download_id is not None:
        # The id is looked for across the WHOLE feed, not just the page a
        # listing would show. Backfilling an eight-period history means
        # reaching reports several pages back, and making the caller guess
        # --start until the id appears would turn that into a manual search.
        chosen = find_release(issuer, download_id, start=start,
                              language=language, opener=opener)
        if not chosen.attachments:
            raise NordicError(
                f"disclosure {download_id} ({chosen.headline!r}) carries no "
                f"attachment. The text of the release is at {chosen.message_url}; "
                f"this command downloads filed documents and does not scrape a "
                f"page."
            )
        if attachment_index is None:
            if len(chosen.attachments) > 1:
                listing = "\n".join(
                    f"    --attachment {a.index}   {a.mimetype:52} {a.file_name}"
                    for a in chosen.attachments)
                raise NordicError(
                    f"disclosure {download_id} carries "
                    f"{len(chosen.attachments)} files and none was named. "
                    f"Which one is the report is not something to guess at: "
                    f"Betsson's 2026 annual filing puts an ESEF package at "
                    f"index 0 and the PDF at index 1.\n{listing}"
                )
            attachment_index = chosen.attachments[0].index
        attachment = next((a for a in chosen.attachments
                           if a.index == attachment_index), None)
        if attachment is None:
            raise NordicError(
                f"disclosure {download_id} has no attachment {attachment_index}; "
                f"it carries {len(chosen.attachments)} "
                f"(0–{len(chosen.attachments) - 1})."
            )
        if period is None:
            raise NordicError(
                "--period is required and is MANUAL. Nothing in the feed says "
                "which fiscal period a document covers -- the category is the "
                "issuer's filing choice, the headline is prose, and the "
                "release date is when it was published. State it: "
                "YYYY-Qn, YYYY-H1, YYYY-H2 or YYYY-FY."
            )
        result = download(chosen, attachment, ticker=key, period=period,
                          directory=directory, now=now, opener=opener)
        return 0, render_download(key, [result])

    releases, count = fetch_releases(issuer, limit=limit, start=start,
                                     language=language, opener=opener)
    with_files = [r for r in releases if r.attachments]
    shown = [r for r in with_files if r.is_report_category] if reports_only else with_files
    hidden = len(with_files) - len(shown)
    return 0, render_listing(issuer, shown, count=count,
                             reports_only=reports_only, hidden=hidden,
                             start=start, language=language)
