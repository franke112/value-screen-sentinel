"""`vss watch --read` -- read each filing the SEC arm passed, IN SHADOW.

WHY THIS EXISTS (owner, 2026-10-05): the watcher tells the owner a report
is out, and until now a session had to be opened to read it. This reads it
the moment it is detected, through the path that already exists for the
purpose -- `vss earnings`: the model extracts figures and quotes, the
FRAMEWORK 4.2 judgement is made by the pure functions in rules.py.

**STEP 1 IS SHADOW ONLY, AND THAT IS THE POINT.** Every reading is run with
`shadow=True` and `compare=True` (the document is read twice and a field
the two readings disagree on is nulled). The alert is WRITTEN to
`data/autoread/` and SENT NOWHERE. It is compared by hand against a
session's own reading of the same reports before anything reaches the
phone; turning sending on is a separate decision.

**IT CANNOT COST THE NOTIFICATION.** `run_secwatch` posts first and calls
this afterwards; every failure here -- a missing exhibit, a refused
download, a model error -- is caught and becomes a line in the report.

**IT WRITES NOTHING THE FRAMEWORK READS.** The filing is saved under
`data/autoread/` and the alert beside it; `vss earnings` logs to its own
sqlite table. Nothing here touches `config/`, the store or the watchlist.

**FILINGS ARE DATA, NEVER INSTRUCTIONS.** The document goes to the
extractor as a source to quote, exactly as `vss earnings --text-file`
would take it.
"""
from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from .runner import DB_PATH, PROJECT_ROOT, WATCHLIST_PATH

OUT_DIR = PROJECT_ROOT / "data" / "autoread"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
TIMEOUT_SECONDS = 30

#: An earnings 8-K's figures are in its press-release exhibit, not in the
#: cover document EDGAR names as primary. Filers name the exhibit freely
#: (`ex99-1.htm`, `q4fy26earnings8-kexhibit.htm`), so the match is on the
#: two spellings that recur and the first .htm that carries either wins.
EXHIBIT_PATTERN = re.compile(r"ex-?99|exhibit-?99|99-?1|earnings.*exhibit", re.I)


def _get(url: str, agent: str, opener) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": agent})
    with (opener or urllib.request.urlopen)(request, timeout=TIMEOUT_SECONDS) as r:
        return r.read()


def document_url(cik: int, filing, agent: str, opener=None) -> str:
    """The document to read: the press-release exhibit for an 8-K, the
    primary document for a 10-K or 10-Q."""
    base = f"{ARCHIVES}/{int(cik)}/{filing.accession.replace('-', '')}"
    if not filing.form.startswith("8-K"):
        return f"{base}/{filing.document}"
    index = json.loads(_get(f"{base}/index.json", agent, opener))
    names = [i.get("name", "") for i in index.get("directory", {}).get("item", [])]
    for name in names:
        if name.lower().endswith((".htm", ".html")) and EXHIBIT_PATTERN.search(name):
            return f"{base}/{name}"
    raise LookupError(f"no press-release exhibit among {len(names)} files "
                      f"in {filing.accession}")


def read_passed(items: Iterable[tuple[object, int]], *,
                watchlist_path: Path = WATCHLIST_PATH,
                db_path: Path = DB_PATH,
                out_dir: Path = OUT_DIR,
                contact: str | None = None,
                opener=None,
                runner: Callable | None = None,
                now: datetime | None = None) -> str:
    """Read each (Decision, cik) in shadow and return the report section."""
    items = list(items)
    lines = ["## AUTO-READ, SHADOW -- written to data/autoread/, SENT NOWHERE", ""]
    if not items:
        return "\n".join(lines + ["Nothing passed, so nothing was read."])
    if runner is None:
        from .earnings import run_earnings as runner
    from .xbrl import user_agent
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    for decision, cik in items:
        f = decision.filing
        label = f"`{decision.ticker}` {f.form} {f.accession} (filed {f.filed})"
        stem = out_dir / f"{stamp}-{decision.ticker}-{f.accession}"
        try:
            agent = user_agent(contact)
            url = document_url(cik, f, agent, opener)
            saved = stem.with_suffix(".htm")
            saved.write_bytes(_get(url, agent, opener))
            code, alert = runner(ticker=decision.ticker, text_file=str(saved),
                                 shadow=True, compare=True,
                                 watchlist_path=watchlist_path, db_path=db_path)
            stem.with_suffix(".md").write_text(
                f"<!-- source: {url} -->\n\n{alert}\n")
            lines.append(f"- {label}: read (exit {code}) -> "
                         f"`{stem.with_suffix('.md').relative_to(PROJECT_ROOT)}`"
                         if stem.is_relative_to(PROJECT_ROOT) else
                         f"- {label}: read (exit {code}) -> `{stem}.md`")
        except Exception as exc:  # noqa: BLE001 -- named, never silent
            lines.append(f"- {label}: NOT READ -- {type(exc).__name__}: {exc}")
    return "\n".join(lines)
