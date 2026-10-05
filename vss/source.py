"""Primary-source retrieval for earnings extraction.

Primary source ONLY: a company IR release or a regulatory filing. Never a
news article about one. This module does not search, guess or follow
links -- the URL is supplied by the owner, so "primary source" is
guaranteed by construction rather than by heuristics about page layout.
"""

from __future__ import annotations

import io
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urlsplit

log = logging.getLogger(__name__)

USER_AGENT = "vss/1.0 (personal watchlist tool)"
TIMEOUT_SECONDS = 30
MAX_BYTES = 5_000_000
#: A filing is legitimately larger than a press release -- a 10-Q runs to
#: tens of pages -- so a PDF gets its own cap rather than being refused
#: for being the size a real report is.
MAX_PDF_BYTES = 20_000_000

PDF_MAGIC = b"%PDF-"

#: Text pulled out of a PDF is a RECONSTRUCTION, not the document. A PDF
#: stores glyphs at coordinates; rows and columns are inferred from where
#: they landed. Say so in every alert built on one.
PDF_WARNING = (
    "text was extracted from a PDF. A PDF stores glyphs at coordinates, not "
    "rows, so table rows are reconstructed and can come out merged, split or "
    "reordered. Verify every figure against the PDF itself."
)

#: Hosts that publish articles *about* releases rather than releases.
#: Not exhaustive -- a warning, never a silent substitution.
NEWS_HOSTS = (
    "reuters.com", "bloomberg.com", "ft.com", "cnbc.com", "marketwatch.com",
    "seekingalpha.com", "fool.com", "barrons.com", "wsj.com", "yahoo.com",
    "investing.com", "benzinga.com", "di.se", "privataaffarer.se",
)


class SourceError(Exception):
    """Raised when the primary source cannot be retrieved or read."""


@dataclass(frozen=True)
class PrimarySource:
    url: str
    text: str
    content_type: str
    warnings: tuple[str, ...] = ()


class _TextExtractor(HTMLParser):
    """Strip markup, keeping block structure so sentences stay intact.

    A TABLE ROW is kept on ONE LINE, cells separated by spaces. Both
    halves of that matter, and both were wrong:

      * Cells were concatenated with nothing between them, so an EDGAR
        statement row came out "1,3921,900-27%" -- and 1,392 is not a
        number in that string, under any reading. The figure could not
        be evidenced by the row that plainly contains it.
      * A cell holding a <div> broke the row across lines, leaving the
        label on one line and its numbers on the next. A quote of either
        half evidences nothing: the label has no number, the numbers
        have no name.

    The provenance rule asks the model to quote a row containing its
    figure. That is only possible if a row IS a row.
    """

    #: `ix:header` is inline XBRL's hidden block -- contexts, units, the
    #: facts a filer tags but does not display -- and every date and id in
    #: it reached the model as prose until 2026-09-13, when a 10-K fed
    #: through this path produced two readings of noise. The DISPLAYED
    #: `ix:nonFraction` figures are data inside ordinary cells and stay.
    SKIP = {"script", "style", "noscript", "svg", "head", "ix:header"}
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "table", "section"}
    CELL = {"td", "th"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0
        self._row_depth = 0

    def _break(self) -> str:
        """Inside a row, a block boundary is a space, not a line break."""
        return " " if self._row_depth else "\n"

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
        elif tag == "tr":
            self._row_depth += 1
            self.parts.append("\n")
        elif tag in self.CELL:
            self.parts.append(" ")
        elif tag in self.BLOCK:
            self.parts.append(self._break())

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "tr":
            self._row_depth = max(0, self._row_depth - 1)
            self.parts.append("\n")
        elif tag in self.CELL:
            self.parts.append(" ")
        elif tag in self.BLOCK:
            self.parts.append(self._break())

    def handle_data(self, data):
        if not self._skip_depth and data.strip():
            self.parts.append(data)

    def text(self) -> str:
        return collapse_whitespace("".join(self.parts))


def collapse_whitespace(text: str) -> str:
    """Normalise runs of space and blank lines, leaving NBSP alone.

    A non-breaking space is left as it is on purpose: it is a thousands
    separator in a Swedish report, and extract.candidate_numbers reads it
    as one. Flattening it to a plain space would not change the figure,
    but it would erase the evidence that it was a separator.
    """
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]*\n+", "\n\n", text)
    return text.strip()


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


#: A real tag, not a bare "<". A release saying "revenue grew <1%" is
#: not markup, and flattening it as if it were would eat the sentence.
_TAG_RE = re.compile(r"<\s*[A-Za-z!/][^>]*>")


def to_text(body: str) -> tuple[str, bool]:
    """Flatten markup, or take plain text as it stands.

    Both entry points go through this. They diverged once -- fetch()
    flattened HTML and read_text_file() did not -- so a saved EDGAR
    exhibit passed to --text-file reached the model as 286KB of tag
    soup, and the figures extracted from it were whatever survived.

    Returns (text, was_markup).
    """
    if _TAG_RE.search(body[:4000]):
        return html_to_text(body), True
    return body.strip(), False


def looks_like_pdf(target: str = "", content_type: str = "", raw: bytes = b"") -> bool:
    """Three independent signals, any one of which is enough.

    The magic bytes are included because IR hosts do serve reports as
    ``application/octet-stream`` from an extensionless URL, and a PDF that
    announces itself as neither is still a PDF.
    """
    return (
        raw[:5] == PDF_MAGIC
        or "pdf" in (content_type or "").lower()
        or urlsplit(target or "").path.lower().endswith(".pdf")
    )


def pdf_to_text(raw: bytes, *, where: str) -> str:
    """Flatten a PDF to text, page by page, in reading order.

    Best-effort by nature, and deliberately not compensated for: a row
    that reconstructs badly produces a quote that does not contain its
    figure, and extract.py drops that figure as PROVENANCE UNVERIFIABLE.
    Garbled input must reach the provenance check, not be repaired ahead
    of it -- a repaired row is the tool's reading of the report, not the
    report.
    """
    try:
        import pypdf
    except ImportError as exc:  # pragma: no cover -- pypdf is a requirement
        raise SourceError(
            f"{where} is a PDF and pypdf is not installed: pip install pypdf"
        ) from exc

    try:
        reader = pypdf.PdfReader(io.BytesIO(raw))
        if reader.is_encrypted:
            # IR PDFs are routinely permissions-encrypted with an empty
            # password: readable by anyone, flagged all the same. Only a
            # PDF that wants a password we do not have is refused.
            if not reader.decrypt(""):
                raise SourceError(
                    f"{where}: PDF is password-protected and cannot be read"
                )
        pages = [page.extract_text() or "" for page in reader.pages]
    except SourceError:
        raise
    except Exception as exc:
        raise SourceError(
            f"{where}: cannot read PDF ({type(exc).__name__}: {exc})"
        ) from exc

    text = collapse_whitespace("\n\n".join(p for p in pages if p.strip()))
    if not text:
        raise SourceError(
            f"{where}: the PDF contains no extractable text -- it is a scan or "
            f"an image. vss will not guess at figures it cannot read."
        )
    return text


def looks_like_news(url: str) -> str | None:
    """Warn when a URL points at an aggregator rather than a primary source.

    Matches on the HOSTNAME at a label boundary, never as a substring of
    the whole URL. A naive substring test reports "ft.com" for
    www.micro-soft.com, because "microsoft.com" literally contains
    "ft.com" -- and a matcher that fires on the wrong domain cannot be
    trusted to fire on the right one.
    """
    host = (urlsplit(url).hostname or "").lower().strip(".")
    if not host:
        return None
    for domain in NEWS_HOSTS:
        if host == domain or host.endswith("." + domain):
            return (
                f"{domain} publishes articles ABOUT releases. FRAMEWORK requires the "
                f"primary source -- the company IR release or the filing itself."
            )
    return None


def fetch(url: str, *, opener=None) -> PrimarySource:
    """Retrieve and flatten a primary source. Fails loudly, never silently."""
    if not url.lower().startswith(("http://", "https://")):
        raise SourceError(f"not an http(s) URL: {url!r}")

    warnings = []
    news = looks_like_news(url)
    if news:
        warnings.append(news)
        log.warning("%s: %s", url, news)

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        opener = opener or urllib.request.urlopen
        with opener(request, timeout=TIMEOUT_SECONDS) as response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            # Read to the larger cap and pick the applicable one after
            # sniffing, so a PDF served without a content type or an
            # extension is still judged as a PDF rather than truncated.
            raw = response.read(MAX_PDF_BYTES + 1)
    except urllib.error.HTTPError as exc:
        hint = ""
        if exc.code in (401, 403, 429):
            # Some IR hosts (sap.com among them) refuse automated requests
            # outright. That is not a reason to dress vss up as a browser
            # -- it is a reason to say which door is still open.
            hint = (
                " -- the host refused an automated request. Download the "
                "report in a browser and pass it with --text-file."
            )
        raise SourceError(f"HTTP {exc.code} fetching {url}{hint}") from exc
    except Exception as exc:
        raise SourceError(f"{type(exc).__name__} fetching {url}: {exc}") from exc

    is_pdf = looks_like_pdf(url, content_type, raw)
    limit = MAX_PDF_BYTES if is_pdf else MAX_BYTES
    if len(raw) > limit:
        raise SourceError(f"{url}: response exceeds {limit} bytes")

    if is_pdf:
        warnings.append(PDF_WARNING)
        log.warning("%s: %s", url, PDF_WARNING)
        return PrimarySource(
            url=url, text=pdf_to_text(raw, where=url),
            content_type=content_type or "application/pdf",
            warnings=tuple(warnings),
        )

    try:
        body = raw.decode("utf-8", errors="replace")
    except Exception as exc:
        raise SourceError(f"{url}: undecodable response ({exc})") from exc

    text, _ = to_text(body)
    if not text:
        raise SourceError(f"{url}: no readable text extracted")
    return PrimarySource(url=url, text=text, content_type=content_type,
                         warnings=tuple(warnings))


def read_text_file(path) -> PrimarySource:
    """Escape hatch for a locally saved release -- text, HTML or a PDF.

    A downloaded PDF goes through the same extractor as a fetched one and
    carries the same warning, on top of the local-file one: where the file
    came from and how its text was recovered are two separate facts.
    """
    from pathlib import Path

    # Resolved up front, before anything reads it or names it. as_uri()
    # refuses a relative path -- `--text-file q3.htm` crashed on it --
    # and resolving here also means the error messages, the source
    # warning and the recorded URL all name the same absolute file
    # rather than whatever the caller happened to type.
    p = Path(path).resolve()
    if not p.exists():
        raise SourceError(f"no such file: {p}")
    raw = p.read_bytes()
    warnings = [f"read from local file {p}, not fetched"]

    if looks_like_pdf(p.name, raw=raw):
        text = pdf_to_text(raw, where=str(p))
        warnings.append(PDF_WARNING)
        content_type = "application/pdf"
    else:
        text, was_markup = to_text(raw.decode("utf-8", errors="replace"))
        content_type = "text/html" if was_markup else "text/plain"

    if not text:
        raise SourceError(f"{p}: file is empty")
    return PrimarySource(url=p.as_uri(), text=text, content_type=content_type,
                         warnings=tuple(warnings))
