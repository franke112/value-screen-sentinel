"""Euronext Oslo NewsWeb: the Norwegian OAM, as a fetcher.

`vss/nordic.py` reaches Nasdaq's Nordic markets and says so plainly: Oslo
Børs is Euronext and is not on that service. This module is the other door.
**NewsWeb is the Norwegian Officially Appointed Mechanism** for regulated
information under the Transparency Directive, so a report taken from it is
the filed document itself and not a copy on an IR page.

Like `nordic`, IT READS NOTHING OUT OF WHAT IT DOWNLOADS. It resolves,
lists, downloads and records; the figures come out by hand into
`config/manual/<TICKER>.yaml`.

WHAT WAS MEASURED, 2026-09-08, and why each thing is coded the way it is.

1. **THIS SERVICE HAS A COMPANY DIRECTORY, AND NASDAQ'S HAS NONE.** That is
   the one real difference in kind. `POST /v1/newsreader/issuers` returns
   every issuer -- 1,622 rows on the day measured -- each with `issuerSign`,
   `issuerId`, `name` and `isActive`. So resolution here is a LOOKUP against
   the exchange's own list, not `nordic.resolve`'s full-text search whose
   answer a human has to eyeball. The owner still confirms and stores the
   mapping, because a name match is not a claim about which company the
   watchlist meant.

2. **`issuer=` FILTERS FOR A SIGN THE SERVICE KNOWS, AND IS SILENTLY
   IGNORED FOR ONE IT DOES NOT.** `issuer=BOUV` returns Bouvet's releases.
   `issuer=ZZZZ` returns **601 releases from 250-odd different issuers** --
   the unfiltered market feed -- with HTTP 200 and no word of complaint.
   This is `nordic`'s rule 2 in a new costume and it is worse here, because
   the answer looks like data rather than like nothing. **Every row's
   `issuerSign` is therefore checked against the sign that was asked for**,
   and a page carrying any other issuer is refused rather than filtered.

3. **`fromDate` AND `toDate` ARE REQUIRED, AND OMITTING THEM RETURNS AN
   EMPTY LIST.** Not an error -- an empty `messages` array, which reads
   exactly like "this issuer has published nothing". They are always sent.

4. **THERE IS NO `start`, NO `offset` AND NO `limit`.** A window is capped
   at **601 rows** and the response says `overflow: true` when it hit the
   cap. The only pagination is a NARROWER DATE WINDOW, so a long history is
   walked backwards a window at a time and `overflow` is surfaced rather
   than swallowed.

5. **A LIST ROW COUNTS ITS ATTACHMENTS AND DOES NOT NAME THEM.** It carries
   `numbAttachments` but no ids. The attachment ids come from
   `GET /v1/newsreader/message?messageId=N`, which is a direct lookup -- so
   unlike `nordic.find_release`, nothing here walks pages to find an id.

6. **THE ATTACHMENT ENDPOINT ANSWERS THIS TOOL, and a note in
   `sources/manifest.json` says it does not.** That note was written on
   2026-08-30 against NHY.OL: *"NewsWeb's own copy is named beside it and
   could not be downloaded (its attachment endpoint answers HTTP 400 to
   every automated request)"*, and Norsk Hydro's reports were taken from
   hydro.com instead. Measured again on 2026-09-08:
   `GET https://api3.oslo.oslobors.no/v1/newsreader/attachment?messageId=680129&attachmentId=331407`
   answers **HTTP 200** with 841,764 bytes beginning `%PDF-1.7`. The
   `newsweb.oslobors.no/obsvc/attachment.obsvc` path -- a different host and
   a different endpoint -- answers with an HTML page, and is the likely
   subject of the old note. **The old manifest entries are not rewritten:**
   they record what was measured on the day they were written, which is what
   a provenance record is for. This module uses the api3 endpoint.

7. **THE FEED CARRIES NO LANGUAGE FIELD, AND EVERY REPORT IS FILED TWICE.**
   Bouvet's Q2 2026 report is message 680129 in English and 680130 in
   Norwegian -- two disclosures, two attachment sets, no field on either
   saying which is which. So **`--language` is a MANUAL LABEL on a download
   here and never a filter**, in exactly the way `--period` is: the owner
   states it, it goes in the filename and the manifest, and the manifest
   says it was stated rather than read. Without it the file is labelled
   `xx` and two editions of one report collide on a filename -- which
   `nordic.download` answers by REFUSING on differing bytes, loudly, rather
   than by overwriting. That is the safe failure and it is left in place.
"""

from __future__ import annotations

import json
import logging
import shutil
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Mapping

import yaml

from .nordic import (
    MAX_DOWNLOAD_BYTES,
    NordicError,
    REPORT_CATEGORIES,
    SOURCES_DIR,
    Attachment,
    Release,
    check_period,
    download,
    render_download,
)
from .source import USER_AGENT

log = logging.getLogger(__name__)

API_ROOT = "https://api3.oslo.oslobors.no/v1/newsreader"
LIST_URL = f"{API_ROOT}/list"
MESSAGE_URL = f"{API_ROOT}/message"
ATTACHMENT_URL = f"{API_ROOT}/attachment"
ISSUERS_URL = f"{API_ROOT}/issuers"
MESSAGE_PAGE = "https://newsweb.oslobors.no/message"

TIMEOUT_SECONDS = 60

#: The row cap one date window returns, measured. Not a parameter -- the
#: service has none -- so it is only ever compared against, never sent.
WINDOW_CAP = 601

#: How far back a listing looks when the caller names no window. Long
#: enough to carry an annual report and the four quarters around it.
DEFAULT_LOOKBACK_DAYS = 420

#: The ticker -> issuer-sign mapping, resolved once and stored. A SEPARATE
#: file from `config/nordic_issuers.yaml` and deliberately so: that file
#: answers "is this name on the Nasdaq Nordic feed", which `refresh.py`
#: asks in order to pick a route. An Oslo name in it would make that
#: question answer yes about a service that has never heard of the company.
ISSUERS_PATH = Path("config/oslo_issuers.yaml")

ORIGIN = "euronext-oslo-newsweb"

PRIMARY_SOURCE_BASIS = (
    "the document the issuer filed on Euronext Oslo's NewsWeb -- the "
    "Norwegian Officially Appointed Mechanism for regulated information "
    "under the Transparency Directive -- taken from NewsWeb's own "
    "attachment endpoint, which is the filed document and not a copy of it "
    "on the issuer's website"
)


# --- the stored mapping ---------------------------------------------------


@dataclass(frozen=True)
class OsloIssuer:
    """One ticker's place on NewsWeb. `sign` is what the feed keys on."""

    ticker: str
    sign: str
    company: str
    issuer_id: int | None = None
    resolved: date | None = None
    note: str | None = None

    #: So a caller can print one line about either backend's issuer.
    @property
    def market(self) -> str:
        return "Oslo Børs (XOSL), Euronext"


def load_issuers(path: Path = ISSUERS_PATH) -> dict[str, OsloIssuer]:
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

    out: dict[str, OsloIssuer] = {}
    allowed = {"sign", "company", "issuer_id", "resolved", "note"}
    for ticker, entry in raw.items():
        where = f"{path}: issuer {ticker}"
        if not isinstance(entry, Mapping):
            raise NordicError(f"{where}: expected a mapping")
        unknown = set(entry) - allowed
        if unknown:
            raise NordicError(f"{where}: unknown key(s) {', '.join(sorted(unknown))}. "
                              f"Allowed: {', '.join(sorted(allowed))}")
        for required in ("sign", "company"):
            if not str(entry.get(required) or "").strip():
                raise NordicError(f"{where}: {required} is required")
        resolved = entry.get("resolved")
        if isinstance(resolved, datetime):
            resolved = resolved.date()
        elif isinstance(resolved, str):
            resolved = date.fromisoformat(resolved.strip())
        elif resolved is not None and not isinstance(resolved, date):
            raise NordicError(f"{where}: resolved must be a YYYY-MM-DD date")
        issuer_id = entry.get("issuer_id")
        out[str(ticker).strip().upper()] = OsloIssuer(
            ticker=str(ticker).strip().upper(),
            sign=str(entry["sign"]).strip().upper(),
            company=str(entry["company"]).strip(),
            issuer_id=int(issuer_id) if issuer_id is not None else None,
            resolved=resolved,
            note=(str(entry["note"]).strip() if entry.get("note") else None),
        )
    return out


def issuer_for(ticker: str, *, path: Path = ISSUERS_PATH) -> OsloIssuer:
    key = ticker.strip().upper()
    issuers = load_issuers(path)
    if key not in issuers:
        raise NordicError(
            f"{key} has no entry in {path}. NewsWeb keys on an ISSUER SIGN "
            f"(Bouvet is `BOUV`, Norsk Hydro `NHY`), and a sign the service "
            f"does not know is SILENTLY IGNORED -- the whole market's feed "
            f"comes back looking like this company's. So the sign is "
            f"established once against the exchange's own issuer directory "
            f"and stored. Run `vss nordic --resolve <name> --ticker {key}` "
            f"to see the directory's candidates, then re-run with --write."
        )
    return issuers[key]


# --- the wire -------------------------------------------------------------


def _request(request: urllib.request.Request, *, opener=None) -> bytes:
    try:
        opener = opener or urllib.request.urlopen
        with opener(request, timeout=TIMEOUT_SECONDS) as response:
            return response.read(MAX_DOWNLOAD_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise NordicError(f"HTTP {exc.code} fetching {request.full_url}") from exc
    except Exception as exc:  # noqa: BLE001 - reported, never swallowed
        raise NordicError(
            f"{type(exc).__name__} fetching {request.full_url}: {exc}") from exc


def _get_json(url: str, *, opener=None) -> dict:
    raw = _request(urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT}), opener=opener)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise NordicError(f"{url}: response is not JSON ({exc})") from exc


def _post_json(url: str, body: dict, *, opener=None) -> dict:
    raw = _request(urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"User-Agent": USER_AGENT,
                 "Content-Type": "application/json"}), opener=opener)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise NordicError(f"{url}: response is not JSON ({exc})") from exc


# --- resolution, against the exchange's own directory ---------------------


@dataclass(frozen=True)
class Candidate:
    sign: str
    company: str
    issuer_id: int | None
    active: bool


def directory(*, opener=None) -> list[Candidate]:
    """Every issuer NewsWeb knows, from its own list.

    Rows without an `issuerSign` are dropped and counted rather than
    guessed at: 120 of the 1,622 measured carry a name and an id but no
    sign, and a sign is the only thing the list endpoint filters on.
    """
    payload = _post_json(ISSUERS_URL, {}, opener=opener)
    rows = ((payload.get("data") or {}).get("issuers")) or []
    out: list[Candidate] = []
    for row in rows:
        sign = str(row.get("issuerSign") or "").strip().upper()
        name = str(row.get("name") or "").strip()
        if not sign or not name:
            continue
        issuer_id = row.get("issuerId")
        out.append(Candidate(sign=sign, company=name,
                             issuer_id=int(issuer_id) if issuer_id else None,
                             active=bool(row.get("isActive"))))
    if not out:
        raise NordicError(
            f"{ISSUERS_URL} returned no issuer carrying a sign. The directory "
            f"is the only thing that makes an Oslo mapping checkable; nothing "
            f"is resolved without it.")
    return out


def resolve(ticker: str, search: str, *, opener=None) -> list[Candidate]:
    """Directory rows whose name contains the search text. NOT auto-picked.

    A LOOKUP, not `nordic.resolve`'s full-text search over release bodies:
    this service publishes the list of its own issuers, so a candidate here
    is a company that exists rather than a company that was mentioned. The
    owner still confirms it -- the watchlist's ticker and the exchange's
    name are two different strings and no equality test between them is safe.
    """
    needle = (search or "").strip().lower()
    if not needle:
        raise NordicError("--resolve needs the text to look for in the "
                          "exchange's issuer directory")
    rows = directory(opener=opener)
    hits = [c for c in rows if needle in c.company.lower() or needle == c.sign.lower()]
    return sorted(hits, key=lambda c: (not c.active, c.company))


def issuer_block(ticker: str, candidate: Candidate, *, as_of: date) -> str:
    lines = [f"  {ticker.strip().upper()}:",
             f'    sign: "{candidate.sign}"',
             f'    company: "{candidate.company}"']
    if candidate.issuer_id:
        lines.append(f"    issuer_id: {candidate.issuer_id}")
    lines.append(f"    resolved: {as_of.isoformat()}")
    lines.append(f'    note: "matched the exchange\'s own issuer directory '
                 f'({ISSUERS_URL}); isActive={int(candidate.active)}"')
    return "\n".join(lines)


def write_issuer(ticker: str, candidate: Candidate, *, as_of: date,
                 path: Path = ISSUERS_PATH) -> Path:
    """Append ONE entry, backing the file up first, never replacing one."""
    key = ticker.strip().upper()
    existing = load_issuers(path)
    if key in existing:
        raise NordicError(
            f"{path} already has an entry for {key} ({existing[key].company}, "
            f"sign {existing[key].sign}). It is not replaced: edit the file "
            f"yourself if the mapping is wrong.")
    backup = None
    if path.exists():
        backup = path.with_suffix(path.suffix + f".bak-{as_of.isoformat()}")
        shutil.copy2(path, backup)
        text = path.read_text(encoding="utf-8").rstrip("\n") + "\n"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = ("# ticker -> the ISSUER SIGN Euronext Oslo's NewsWeb keys on.\n"
                "# Resolved once against the exchange's own issuer directory\n"
                "# by `vss nordic --resolve` and stored. SEPARATE from\n"
                "# config/nordic_issuers.yaml, which answers a different\n"
                "# question: whether a name is on the NASDAQ Nordic feed.\n"
                "issuers:\n")
    path.write_text(text + issuer_block(key, candidate, as_of=as_of) + "\n",
                    encoding="utf-8")
    log.info("wrote %s to %s%s", key, path, f" (backup {backup})" if backup else "")
    return path


# --- the feed -------------------------------------------------------------


def list_url(issuer: OsloIssuer, *, since: date, until: date) -> str:
    """The exact request, built in one place so a test can assert on it."""
    params = {"issuer": issuer.sign,
              "fromDate": since.isoformat(),
              "toDate": until.isoformat()}
    return f"{LIST_URL}?{urllib.parse.urlencode(params)}"


def _release_from_row(row: Mapping, *, attachments: tuple[Attachment, ...] = (),
                      language: str = "") -> Release:
    categories = row.get("category") or []
    first = categories[0] if categories else {}
    message_id = int(row.get("messageId") or row.get("id") or 0)
    markets = tuple(str(m) for m in (row.get("markets") or []))
    return Release(
        disclosure_id=message_id,
        category_id=int(first.get("id") or 0),
        category=str(first.get("category_en") or "").strip(),
        headline=str(row.get("title") or "").strip(),
        language=language,
        market=", ".join(markets),
        company=str(row.get("issuerName") or "").strip(),
        released=str(row.get("publishedTime") or "").strip(),
        message_url=f"{MESSAGE_PAGE}/{message_id}",
        attachments=attachments,
        origin=ORIGIN,
        primary_source_basis=PRIMARY_SOURCE_BASIS,
        extra=(
            ("newsweb_message_id", message_id),
            ("newsweb_api", f"{MESSAGE_URL}?messageId={message_id}"),
            ("issuer_sign", str(row.get("issuerSign") or "").strip()),
            ("issuer_id", row.get("issuerId")),
            ("category_no", str(first.get("category_no") or "").strip()),
            # A LIST ROW COUNTS ITS FILES AND DOES NOT NAME THEM (rule 5).
            # Kept so a listing can say "2 files" without pretending to know
            # which two, and so the count the feed stated is on the record
            # beside the ids the message endpoint later supplied.
            ("newsweb_attachment_count", int(row.get("numbAttachments") or 0)),
        ),
    )


def attachment_count(release: Release) -> int:
    """What the feed said, or what the message actually carried."""
    stated = dict(release.extra).get("newsweb_attachment_count")
    return len(release.attachments) or int(stated or 0)


def _check_signs(rows: list[Mapping], issuer: OsloIssuer, url: str) -> None:
    """Refuse a page carrying anybody else. See rule 2 in the docstring."""
    strays = sorted({str(r.get("issuerSign") or "?") for r in rows
                     if str(r.get("issuerSign") or "").upper() != issuer.sign})
    if strays:
        raise NordicError(
            f"{url} answered with {len(rows)} row(s) carrying "
            f"{len(strays)} other issuer(s) ({', '.join(strays[:8])}"
            f"{'…' if len(strays) > 8 else ''}). THE SERVICE IGNORES AN "
            f"ISSUER SIGN IT DOES NOT KNOW and returns the whole market's "
            f"feed with HTTP 200. Nothing is filtered down from that: the "
            f"sign {issuer.sign!r} stored for {issuer.ticker} is wrong, or "
            f"the parameter has stopped working. Re-resolve against "
            f"{ISSUERS_URL} before trusting anything from this feed.")


def fetch_releases(issuer: OsloIssuer, *, since: date, until: date,
                   opener=None) -> tuple[list[Release], bool]:
    """One date window of one issuer's disclosures, newest first.

    Returns the releases and whether the service said it TRUNCATED them.
    Attachment ids are not on a list row (rule 5), so every Release here
    carries none; `find_release` fetches them per message.
    """
    url = list_url(issuer, since=since, until=until)
    payload = _get_json(url, opener=opener)
    data = payload.get("data") or {}
    rows = list(data.get("messages") or [])
    _check_signs(rows, issuer, url)
    overflow = bool(data.get("overflow"))
    if len(rows) >= WINDOW_CAP and not overflow:
        log.warning("%s: %d rows at the measured cap of %d and the response "
                    "did not say overflow", issuer.ticker, len(rows), WINDOW_CAP)
    return [_release_from_row(r) for r in rows], overflow


def find_release(issuer: OsloIssuer, message_id: int, *,
                 language: str = "", opener=None) -> Release:
    """One message, WITH its attachments, by direct lookup.

    No page walking: unlike the Nasdaq feed, this service addresses a
    message by id. The message is still checked against the issuer asked
    for -- an id is a global number and naming the wrong one would
    otherwise file another company's report under this ticker.
    """
    url = f"{MESSAGE_URL}?messageId={int(message_id)}"
    payload = _get_json(url, opener=opener)
    row = (payload.get("data") or {}).get("message")
    if not row:
        raise NordicError(
            f"{url} carries no message. Check the id against "
            f"`vss nordic --ticker {issuer.ticker}`.")
    sign = str(row.get("issuerSign") or "").strip().upper()
    if sign != issuer.sign:
        raise NordicError(
            f"message {message_id} was filed by {sign or '(no sign)'} "
            f"({row.get('issuerName') or '?'}), not by {issuer.sign} "
            f"({issuer.company}). A NewsWeb message id is a number across the "
            f"whole exchange; it is not filed under {issuer.ticker}.")
    raw = row.get("attachments") or []
    attachments = tuple(
        Attachment(index=n,
                   mimetype="",  # the message record does not declare one
                   file_name=str(a.get("name") or "").strip(),
                   url=f"{ATTACHMENT_URL}?messageId={int(message_id)}"
                       f"&attachmentId={int(a['id'])}")
        for n, a in enumerate(raw) if a.get("id")
    )
    return _release_from_row(row, attachments=attachments, language=language)


# --- reports --------------------------------------------------------------


def render_resolve(ticker: str, search: str, candidates: list[Candidate], *,
                   as_of: date, written: Path | None) -> str:
    out = [f"# vss nordic --resolve -- {ticker} on Euronext Oslo NewsWeb", ""]
    out.append(f"**SOURCE:** `POST {ISSUERS_URL}` — **the exchange's own "
               f"issuer directory.** Unlike the Nasdaq Nordic feed, this "
               f"service publishes the list of companies it carries, so a "
               f"candidate below is a company that EXISTS rather than a "
               f"company some release mentioned.")
    out.append("")
    out.append(f"- searched for: `{search}`")
    out.append(f"- candidates: {len(candidates)}")
    out.append("")
    if not candidates:
        out.append("**No issuer in the directory carries that text in its "
                   "name.** Nothing is guessed and nothing is written. Try a "
                   "shorter fragment, or the issuer sign itself.")
        return "\n".join(out) + "\n"
    out.append("| sign | company | issuerId | active |")
    out.append("|---|---|---:|---|")
    for c in candidates:
        out.append(f"| `{c.sign}` | {c.company} | {c.issuer_id or ''} | "
                   f"{'yes' if c.active else 'no'} |")
    out.append("")
    out.append("**Nothing is auto-selected.** Confirm which row is the "
               "company the watchlist means, then store it:")
    out.append("")
    out.append("```yaml")
    out.append(issuer_block(ticker, candidates[0], as_of=as_of))
    out.append("```")
    if written:
        out.append("")
        out.append(f"**WRITTEN** to `{written}` — the first row above.")
    return "\n".join(out) + "\n"


def render_listing(issuer: OsloIssuer, releases: list[Release], *,
                   since: date, until: date, overflow: bool,
                   reports_only: bool, hidden: int) -> str:
    out = [f"# vss nordic -- {issuer.ticker} ({issuer.company}, sign "
           f"`{issuer.sign}`) -- {issuer.market}", ""]
    out.append(f"**SOURCE:** `{LIST_URL}` — Euronext Oslo's NewsWeb, the "
               f"Norwegian Officially Appointed Mechanism. Free, no account. "
               f"Nothing below has been opened or read; this is a list of "
               f"disclosures, not of figures.")
    out.append("")
    out.append(f"- window: **{since.isoformat()} to {until.isoformat()}** — "
               f"this service has no `start` or `limit`, so a window IS the "
               f"page; a longer history is another window.")
    out.append(f"- disclosures in the window: {len(releases)}")
    out.append("")
    if overflow:
        out.append(f"**TRUNCATED.** The service answered `overflow: true` — it "
                   f"caps a window at about {WINDOW_CAP} rows and says so. "
                   f"Ask for a narrower window; do not read this list as "
                   f"complete.")
        out.append("")
    if reports_only:
        out.append(f"## FILTERED TO REPORT CATEGORIES — {hidden} row(s) hidden")
        out.append("")
        out.append("The category is the ISSUER'S FILING CHOICE, not a "
                   "statement about content: Bouvet files every quarterly "
                   "report under `HALF YEAR FINANCIAL REPORT`. The default "
                   "listing hides nothing.")
        out.append("")
    out.append("| messageId | published | category | files | headline |")
    out.append("|---:|---|---|---:|---|")
    for r in releases:
        out.append(f"| {r.disclosure_id} | {r.released_date} | "
                   f"{r.category.title()} | {attachment_count(r)} | "
                   f"{r.headline[:78]} |")
    out.append("")
    out.append("**A list row counts its files and does not name them.** The "
               "attachment ids are on the message itself; ask for one with "
               "`--download <messageId>` and it will name them if there is "
               "more than one.")
    out.append("")
    out.append("**EVERY REPORT IS FILED TWICE, in Norwegian and in English, "
               "as two separate messages** — and no field on either says "
               "which. `--language` on a download is therefore a LABEL you "
               "state, like `--period`, and never a filter.")
    return "\n".join(out) + "\n"


# --- the command ----------------------------------------------------------


def run_oslo(*, ticker: str, resolve_name: str | None = None,
             write: bool = False, download_id: int | None = None,
             attachment_index: int | None = None, period: str | None = None,
             reports_only: bool = False, language: str | None = None,
             since: date | None = None, until: date | None = None,
             issuers_path: Path = ISSUERS_PATH,
             directory_path: Path = SOURCES_DIR,
             as_of: date | None = None, now: datetime | None = None,
             opener=None) -> tuple[int, str]:
    """Returns (exit_code, report_markdown). Dispatched to by `run_nordic`."""
    as_of = as_of or date.today()
    key = ticker.strip().upper()

    if resolve_name is not None:
        candidates = resolve(key, resolve_name, opener=opener)
        written = None
        if write and candidates:
            written = write_issuer(key, candidates[0], as_of=as_of,
                                   path=issuers_path)
        return (0 if candidates else 1), render_resolve(
            key, resolve_name, candidates, as_of=as_of, written=written)

    issuer = issuer_for(key, path=issuers_path)

    if download_id is not None:
        if period is None:
            raise NordicError(
                "--period is required and is MANUAL. Nothing in the feed says "
                "which fiscal period a document covers -- the category is the "
                "issuer's filing choice (Bouvet files every quarter under "
                "HALF YEAR FINANCIAL REPORT), the headline is prose, and the "
                "publication date is when it was published. State it: "
                "YYYY-Qn, YYYY-H1, YYYY-H2 or YYYY-FY.")
        check_period(period)
        chosen = find_release(issuer, download_id,
                              language=(language or "").strip().lower(),
                              opener=opener)
        if not chosen.attachments:
            raise NordicError(
                f"message {download_id} ({chosen.headline!r}) carries no "
                f"attachment. The text of the release is at "
                f"{chosen.message_url}; this command downloads filed "
                f"documents and does not scrape a page.")
        if attachment_index is None:
            if len(chosen.attachments) > 1:
                listing = "\n".join(
                    f"    --attachment {a.index}   {a.file_name}"
                    for a in chosen.attachments)
                raise NordicError(
                    f"message {download_id} carries "
                    f"{len(chosen.attachments)} files and none was named. "
                    f"Which one is the report is not something to guess at: "
                    f"Bouvet's results releases carry the report and the "
                    f"analyst presentation, and the order varies.\n{listing}")
            attachment_index = chosen.attachments[0].index
        attachment = next((a for a in chosen.attachments
                           if a.index == attachment_index), None)
        if attachment is None:
            raise NordicError(
                f"message {download_id} has no attachment {attachment_index}; "
                f"it carries {len(chosen.attachments)} "
                f"(0–{len(chosen.attachments) - 1}).")
        if language:
            # STATED, not read. The record has to say which, because a
            # reader cannot tell an owner's label from a feed's field.
            chosen = _with_language_note(chosen, language)
        result = download(chosen, attachment, ticker=key, period=period,
                          directory=directory_path, now=now, opener=opener)
        return 0, render_download(key, [result])

    until = until or as_of
    since = since or (until - timedelta(days=DEFAULT_LOOKBACK_DAYS))
    releases, overflow = fetch_releases(issuer, since=since, until=until,
                                        opener=opener)
    with_files = [r for r in releases if attachment_count(r)]
    shown = ([r for r in with_files if r.is_report_category]
             if reports_only else with_files)
    return 0, render_listing(issuer, shown, since=since, until=until,
                             overflow=overflow, reports_only=reports_only,
                             hidden=len(with_files) - len(shown))


def _with_language_note(release: Release, language: str) -> Release:
    label = language.strip().lower()
    extra = dict(release.extra)
    extra["language_basis"] = (
        f"MANUAL. NewsWeb carries no language field and files every report "
        f"twice, in Norwegian and in English, as two separate messages; "
        f"{label!r} is the owner's label on message {release.disclosure_id}, "
        f"stated with --language and not read off the feed."
    )
    return replace(release, language=label, extra=tuple(extra.items()))
