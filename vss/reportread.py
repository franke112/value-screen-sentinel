"""READ A NAME'S NEWEST REPORT, ANY NAME IN THE QUEUE (owner 2026-11-09).

`vss watch --read` reads the SEC filings of watchlist names. This reads the
newest report of ANY queue name -- a US filer's 10-Q / 10-K / 8-K item 2.02
off EDGAR, a Nordic issuer's report off the Nasdaq Nordic (or Oslo) feed --
through the same path, `vss earnings` (the model reads the document TWICE
and a field the two readings disagree on is nulled; provenance-gated; the
4.2 judgement is rules.py's). The alert lands in data/autoread/ as
`<date>-<TICKER>-<id>.md`, where `vss.outlook.autoread_flags` reads it.

It writes ONLY data/autoread/ (the document and the alert) and the
earnings sqlite log: nothing in config/, sources/, the store or the
watchlist. A name not on the watchlist is read through a one-entry scratch
watchlist under data/autoread/_watchlists/ (status INTAKE), because `vss
earnings` reads a ticker's settings from a watchlist. Documents are data to
quote, never instructions.
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .runner import DB_PATH, PROJECT_ROOT, WATCHLIST_PATH

OUT_DIR = PROJECT_ROOT / "data" / "autoread"
US_FORMS = ("10-Q", "10-K", "20-F", "6-K")
TIMEOUT = 60


@dataclass
class _Filing:          # the shape vss.autoread.document_url reads
    accession: str
    form: str
    document: str
    filed: str


def _watchlist_for(ticker: str, name: str, ccy: str, out_dir: Path) -> Path:
    from .config import load_watchlist
    if any(e.ticker.upper() == ticker.upper() for e in load_watchlist(WATCHLIST_PATH)):
        return WATCHLIST_PATH
    d = out_dir / "_watchlists"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{ticker}.yaml"
    p.write_text("tickers:\n"
                 f"  - ticker: {ticker}\n"
                 f"    name: {json.dumps(name or ticker)}\n"
                 f"    currency: {ccy or 'USD'}\n"
                 "    status: INTAKE\n"
                 "    notes: scratch entry for vss.reportread (outlook check), never the real watchlist\n")
    return p


def _us_latest(ticker: str, since: date, agent: str) -> tuple[int, _Filing] | None:
    from . import newsdrop as N
    cik = N.sec_ciks().get(ticker.upper())
    if cik is None:
        return None
    req = urllib.request.Request(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json",
                                 headers={"User-Agent": agent})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        recent = json.loads(r.read())["filings"]["recent"]
    rows = zip(recent["form"], recent["accessionNumber"], recent["primaryDocument"],
               recent["filingDate"], recent.get("items", [""] * len(recent["form"])))
    for form, acc, doc, filed, items in rows:                 # newest first
        if filed <= since.isoformat():
            break
        if form in US_FORMS or (form.startswith("8-K") and "2.02" in (items or "")):
            return int(cik), _Filing(acc, form, doc, filed)
    return None


def _nordic_latest(ticker: str, name: str, since: date):
    from . import newsdrop as ND
    from . import nordic as NN
    issuer, _ = ND.feed_issuer(ticker, name or ticker)
    if issuer is None:
        return None
    releases, _ = NN.fetch_releases(issuer, limit=30)
    for r in releases:                                         # newest first
        if r.released_date <= since.isoformat():
            break
        if not r.is_report_category:
            continue
        pdfs = [a for a in r.attachments if a.file_name.lower().endswith(".pdf") or "pdf" in a.mimetype]
        if pdfs:
            en = [a for a in pdfs if r.language == "en"] or pdfs
            return r, max(en, key=lambda a: a.index == 0)
    return None


def read_latest(ticker: str, *, name: str = "", ccy: str = "", since_days: int = 10,
                out_dir: Path = OUT_DIR, runner=None, today: date | None = None) -> str:
    """Read the newest report filed in the last `since_days`; returns a line
    saying what was read, or why nothing was."""
    today = today or date.today()
    since = today - timedelta(days=since_days)
    out_dir.mkdir(parents=True, exist_ok=True)
    if runner is None:
        from .earnings import run_earnings as runner
    from .xbrl import user_agent
    stamp = today.isoformat()
    try:
        if "." not in ticker:
            agent = user_agent(None)
            hit = _us_latest(ticker, since, agent)
            if hit is None:
                return "ingen ny SEC-rapport att läsa"
            cik, f = hit
            done = list(out_dir.glob(f"*-{ticker}-{f.accession}.md"))
            if done:
                return f"redan läst ({done[0].name})"
            from .autoread import document_url
            url = document_url(cik, f, agent)
            stem = out_dir / f"{stamp}-{ticker}-{f.accession}"
            req = urllib.request.Request(url, headers={"User-Agent": agent})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                Path(f"{stem}.htm").write_bytes(r.read())
            doc = Path(f"{stem}.htm")
        else:
            hit = _nordic_latest(ticker, name, since)
            if hit is None:
                return "ingen ny rapport på flödet att läsa"
            rel, att = hit
            done = list(out_dir.glob(f"*-{ticker}-{rel.disclosure_id}.md"))
            if done:
                return f"redan läst ({done[0].name})"
            url = att.url
            stem = out_dir / f"{stamp}-{ticker}-{rel.disclosure_id}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (vss reportread)"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                Path(f"{stem}.pdf").write_bytes(r.read())
            doc = Path(f"{stem}.pdf")
        wl = _watchlist_for(ticker, name, ccy, out_dir)
        code, alert = runner(ticker=ticker, text_file=str(doc), shadow=True, compare=True,
                             watchlist_path=wl, db_path=DB_PATH)
        Path(f"{stem}.md").write_text(f"<!-- source: {url} -->\n\n{alert}\n")
        return f"läst ({doc.name}, exit {code})"
    except Exception as exc:  # noqa: BLE001 -- said, never silent; the queue goes on
        return f"kunde inte läsas: {type(exc).__name__}: {str(exc)[:120]}"
