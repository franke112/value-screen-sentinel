"""`vss watch --sec` -- tell me when a US filer I am watching files something.

WHY THIS EXISTS. `vss watch` asks the Nasdaq Nordic disclosure feed, which
carries Copenhagen, Stockholm and Helsinki and nothing else. **Eleven
watched names file with the SEC and had no publication detection at all**
(2026-09-20): ACN, CTSH, GDDY, NVR, PHM, ULTA, LII, AOS, LOPE, HRB, DECK.
What stood in for it was a `catalyst_date` typed by hand on the entry.

WHAT IT DOES, AND THE LIMIT IS THE POINT. It reads the watched names'
CIKs, asks EDGAR's submissions API what each has filed, reports what is new
since the last run and pushes the same ntfy line the Nordic arm pushes.

**IT IS NOTIFY-ONLY. IT NEVER TOUCHES THE STORE.** Nothing here writes
`config/manual/`, and nothing here writes the watchlist. That is not an
oversight to be fixed later: `vss refresh` is UNSCHEDULED ON PURPOSE
because it writes into a git-tracked configuration directory, and a
detector that stayed on the notifying side of that line is the version
that can run unattended. A detector that fetched figures would need
`deploy/vss.service`'s `ReadWritePaths` widened, and that widening is the
owner's decision, not this module's.

**8-K ITEM 2.02 IS INCLUDED, and that is the whole point of the form
filter** (owner, 2026-09-20): "learning about the quarter days late because
the release is not a 10-Q defeats the purpose". A US filer publishes its
results as an **8-K Item 2.02 — Results of Operations and Financial
Condition** with the press release attached, typically days before the 10-Q
that follows. PulteGroup's Q2 2026: 8-K Item 2.02 on 2026-07-22, 10-Q the
same day; Q1 2026: 8-K Item 2.02 on 2026-04-23 with the 10-Q on 2026-04-23.
Any OTHER 8-K item is rejected with its number named -- a credit agreement
(1.01), a shareholder vote (5.07) and an officer change (5.02) are not the
event this watcher exists for.

**THE STATE IS KEYED ON THE ACCESSION NUMBER** (owner's instruction), in
its own namespace `sec` inside `data/watch_state.json`, beside the Nordic
arm's `seen`. An accession is EDGAR's own identifier for a filing, stable
and never reissued; a date is not, because a filer may file three documents
on one day and amend one of them next week.

**THE FIRST RUN ESTABLISHES A BASELINE AND REPORTS NOTHING**, exactly as
the Nordic arm does. The alternative is a first notification carrying a
year of filings, which is how a watcher gets muted on the day it is
installed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence

from .config import load_watchlist
from .watch import (STATE_PATH, STATE_VERSION, WATCHED_STATUSES, load_state,
                    post_ntfy, save_state)

log = logging.getLogger(__name__)

WATCHLIST_PATH = Path("config/watchlist.yaml")

#: The namespace this arm keeps inside the shared state file. The Nordic
#: arm owns `seen`; this owns `sec`. One file, two cursors, neither able to
#: overwrite the other.
STATE_KEY = "sec"

#: How many accessions to remember per name. EDGAR lists same-day filings
#: in an order that is not guaranteed stable, so a cursor of ONE accession
#: could re-notify a filing it had already reported. Forty is several
#: quarters of filings for an ordinary filer.
REMEMBER = 40

#: The forms asked for. 10-K and 10-Q are the reports; 8-K is asked for
#: because of Item 2.02 and filtered on it below. Amendments are included:
#: a 10-K/A restates something that was already read.
FORMS = ("10-K", "10-K/A", "10-Q", "10-Q/A", "8-K", "20-F", "20-F/A")

#: The 8-K item that carries results. "Results of Operations and Financial
#: Condition" -- the earnings release.
EARNINGS_ITEM = "2.02"


@dataclass(frozen=True)
class Decision:
    """One filing, and whether it passes, with the reason either way."""

    ticker: str
    filing: object
    passes: bool
    why: str

    def line(self) -> str:
        """One filing, one line, in the Nordic arm's shape."""
        f = self.filing
        what = f.form + (f" Item {EARNINGS_ITEM}" if f.form == "8-K" else "")
        period = f" for {f.period_end}" if f.period_end else ""
        return f"{self.ticker} {f.filed} {what}{period}"


@dataclass
class TickerResult:
    ticker: str
    state: str                      # watched | no cik | error
    detail: str = ""
    passed: list[Decision] = field(default_factory=list)
    rejected: list[Decision] = field(default_factory=list)
    first_run: bool = False


def classify(filing, ticker: str) -> Decision:
    """Pass a filing, or reject it, naming why.

    A 10-K or 10-Q is a report and passes on its form alone. An 8-K passes
    ONLY on Item 2.02; every other item is named in the rejection, because
    "an 8-K arrived" is not information and "an 8-K Item 5.02 arrived" is.
    """
    form = filing.form
    if form.startswith(("10-K", "10-Q", "20-F")):
        return Decision(ticker, filing, True, f"{form}, a periodic report")
    if form == "8-K":
        items = [i.strip() for i in (filing.items or "").split(",") if i.strip()]
        if EARNINGS_ITEM in items:
            return Decision(ticker, filing, True,
                            f"8-K Item {EARNINGS_ITEM}, results of operations "
                            f"-- the earnings release, which arrives before "
                            f"the 10-Q")
        return Decision(ticker, filing, False,
                        f"8-K carrying item(s) {', '.join(items) or 'none listed'}"
                        f" -- not Item {EARNINGS_ITEM}")
    return Decision(ticker, filing, False, f"{form} is not a form this watches")


#: The SEC arm also watches INTAKE (owner, 2026-10-05): an INTAKE name paused
#: until its annual report -- ACN, waiting on its FY2026 10-K -- is exactly a
#: name whose next filing is the event. And HELD: a name the owner OWNS is
#: the one whose quarter matters most -- CTSH fell out of the watch the
#: morning it became HELD. The Nordic arm is unchanged.
SEC_WATCHED_STATUSES = (*WATCHED_STATUSES, "INTAKE", "HELD")


def watched_filers(watchlist_path: Path = WATCHLIST_PATH
                   ) -> list[tuple[str, int | None, str]]:
    """(ticker, cik, status) for every watched name. A name with no CIK is
    reported as such rather than skipped: it is a gap in the watchlist, not
    a fact about the filer."""
    return [(e.ticker, e.cik, e.status)
            for e in load_watchlist(watchlist_path)
            if e.status in SEC_WATCHED_STATUSES]


def run_secwatch(*, watchlist_path: Path = WATCHLIST_PATH,
                 state_path: Path = STATE_PATH,
                 send: bool = True,
                 ntfy_url: str | None = None,
                 fetch: Callable | None = None,
                 poster: Callable | None = None,
                 now: str | None = None,
                 reader: Callable | None = None) -> tuple[int, str]:
    """Check every watched US filer once. Returns (exit code, report)."""
    if fetch is None:
        from .reference_figures import list_filings

        def fetch(cik):
            return list_filings(int(cik), forms=FORMS)

    poster = poster or post_ntfy
    stamp = now or datetime.now(timezone.utc).isoformat(timespec="seconds")

    document = load_state(state_path)
    cursors = document.setdefault(STATE_KEY, {})

    results: list[TickerResult] = []
    ciks: dict[str, int] = {}
    for ticker, cik, _status in watched_filers(watchlist_path):
        if not cik:
            results.append(TickerResult(
                ticker, "no cik",
                "the entry carries no `cik:`, so EDGAR cannot be asked. A "
                "non-US listing has none and is not a gap; a US filer "
                "without one is (B-1)."))
            continue
        try:
            filings = list(fetch(cik))
        except Exception as exc:  # noqa: BLE001 -- named, never silent
            results.append(TickerResult(ticker, "error",
                                        f"{type(exc).__name__}: {exc}"))
            continue

        ciks[ticker] = cik
        cursor = cursors.get(ticker, {})
        seen: list[str] = list(cursor.get("accessions", []))
        result = TickerResult(ticker, "watched", first_run=not cursor)
        for filing in filings:
            if filing.accession in seen:
                continue
            decision = classify(filing, ticker)
            (result.passed if decision.passes else result.rejected).append(decision)
        # THE FIRST RUN IS A BASELINE AND REPORTS NOTHING (the Nordic arm's
        # rule, and for its reason).
        if result.first_run:
            result.passed, result.rejected = [], []
        fresh = [f.accession for f in filings]
        # EVERY ACCESSION EDGAR STILL LISTS IS KEPT (2026-10-05). The cap
        # used to cut the cursor to REMEMBER, but `list_filings` returns a
        # filer's whole recent list -- hundreds -- so everything past the
        # fortieth looked new on every run after the baseline (779 lines on
        # the first scheduled run). REMEMBER is now the FLOOR of what is
        # kept, for filings that have dropped off EDGAR's list.
        cursors[ticker] = {
            "accessions": (fresh + [a for a in seen if a not in fresh])
                          [:max(REMEMBER, len(fresh))],
            "last_filed": (filings[0].filed if filings else
                           cursor.get("last_filed", "")),
            "checked_at": stamp,
        }
        results.append(result)

    passed = [d for r in results for d in r.passed]
    lines = [d.line() for d in passed]
    sent = (poster(lines, url=ntfy_url) if send and lines else
            f"not sent: {len(lines)} line(s) withheld" if not send else
            "nothing to send")

    document["version"] = STATE_VERSION
    document[f"{STATE_KEY}_checked_at"] = stamp
    save_state(document, state_path)
    report = render(results, sent=sent, state_path=state_path, stamp=stamp)
    # THE READER RUNS AFTER THE POST AND AFTER THE CURSOR IS SAVED, so a
    # reading that fails or hangs can cost neither the notification nor
    # the record of what was seen (`vss.autoread`, shadow only).
    if reader is not None:
        try:
            report += "\n\n" + reader([(d, ciks[d.ticker]) for d in passed])
        except Exception as exc:  # noqa: BLE001 -- named, never silent
            report += f"\n\n## AUTO-READ FAILED -- {type(exc).__name__}: {exc}"
    return 0, report


def render(results: Iterable[TickerResult], *, sent: str, state_path: Path,
           stamp: str) -> str:
    results = list(results)
    passed = [d for r in results for d in r.passed]
    rejected = [d for r in results for d in r.rejected]
    out = [f"# vss watch --sec -- {stamp}", "",
           "**SOURCE:** EDGAR's submissions API, `data.sec.gov`. **NOTIFY "
           "ONLY: nothing here writes the store or the watchlist.**", "",
           f"- watched: {', '.join(r.ticker for r in results) or 'nothing'}",
           f"- state: `{state_path}` (namespace `{STATE_KEY}`, keyed on the "
           f"accession number)",
           f"- ntfy: {sent}", ""]

    first = [r.ticker for r in results if r.first_run]
    if first:
        out += [f"**FIRST RUN for {', '.join(first)}** -- a baseline was "
                f"recorded and nothing was reported for them. A first "
                f"notification carrying a year of filings is how a watcher "
                f"gets muted on the day it is installed.", ""]

    out.append(f"## PASSED -- {len(passed)}")
    out.append("")
    if passed:
        out.append("| Ticker | Filed | Form | Period | Why |")
        out.append("|---|---|---|---|---|")
        for d in passed:
            out.append(f"| `{d.ticker}` | {d.filing.filed} | {d.filing.form} | "
                       f"{d.filing.period_end or '--'} | {d.why} |")
    else:
        out.append("Nothing new that this watcher passes.")
    out.append("")

    if rejected:
        out.append(f"## REJECTED -- {len(rejected)}")
        out.append("")
        out.append("Reported so the filter can be argued with, never hidden.")
        out.append("")
        out.append("| Ticker | Filed | Form | Why not |")
        out.append("|---|---|---|---|")
        for d in rejected:
            out.append(f"| `{d.ticker}` | {d.filing.filed} | {d.filing.form} | "
                       f"{d.why} |")
        out.append("")

    problems = [r for r in results if r.state != "watched"]
    if problems:
        out.append("## NOT WATCHED")
        out.append("")
        for r in problems:
            out.append(f"- `{r.ticker}` — {r.state}: {r.detail}")
        out.append("")
    return "\n".join(out)
