"""`vss watch` -- tell me when a name I am watching files something that
would make me re-run section 5. Nothing else.

WHAT IT DOES. Reads the tickers in `config/watchlist.yaml` whose status is
WATCH-PRICED, WATCH-GATED or PIPELINE, asks the Nordic disclosure feed for
each one that `config/nordic_issuers.yaml` already resolves, and reports the
disclosures published since the last run. It downloads nothing, opens nothing and
decides nothing about what a document says.

THE FILTER PASSES THREE KINDS AND NO OTHERS:

  1. PERIODIC REPORTS -- interim, half-year, annual. Recognised by the
     exchange's own category, IMPORTED from `nordic.REPORT_CATEGORIES`
     rather than restated here.
  2. GUIDANCE CHANGES, including pre-announcements.
  3. PROFIT WARNINGS.

Leadership changes, M&A, buybacks, managers' transactions, shareholder
notices, AGM material and everything else are REJECTED. The bar is the
owner's: *would this make me re-run section 5?* Only new figures or a
changed outlook do.

THE HARD CASE, AND THE HONEST LIMIT. Pandora's pre-announcement of
2026-01-09 -- company announcement 995, "Pandora expects to deliver 6%
organic growth and around 24% EBIT margin in 2025" -- is the case this
filter exists for. It carries the category *Inside information*, which is
also the category of a CFO appointment, and the word "guidance" appears
nowhere in its title. **Title matching catches it**, on two independent
patterns: `expects to deliver` and `organic growth`. It is caught because
the issuer put the substance in the headline.

**What title matching cannot do, stated rather than papered over:** a
guidance change published under a bland title -- "Company announcement no.
1004", "Notice to the market" -- is invisible to it, and this filter does
NOT widen to catch that, because a filter that passes every *Inside
information* release passes CFO appointments, litigation updates and
share-capital notices too, which is the same as no filter. The mitigation
is that EVERY REJECTED DISCLOSURE IS PRINTED, with its category and title,
so the run says in a few lines what it did not tell you about.

NO AI ANYWHERE. Categories, regular expressions and a state file.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence

from . import rules as R
from .config import ConfigError, load_watchlist
from .nordic import (
    ISSUERS_PATH,
    NordicError,
    REPORT_CATEGORIES,
    Release,
    fetch_releases,
    load_issuers,
)
from .runner import WATCHLIST_PATH
from . import env

log = logging.getLogger(__name__)

#: Where the watcher remembers what it has already reported. NOT the
#: watchlist: the watchlist holds decisions a person made, and a cursor is
#: not a decision. A deleted state file costs one silent run, not a wrong
#: one -- see `run_watch`'s first-run behaviour.
STATE_PATH = Path("data/watch_state.json")
STATE_VERSION = 1

#: The topic URL to POST to. Read from the environment so the topic -- which
#: is the only secret ntfy has -- is never committed.
NTFY_ENV = "VSS_NTFY_URL"
NTFY_TIMEOUT_SECONDS = 15

#: The statuses this command watches. A HELD position is monitored by the
#: main run and a DROPPED name is not watched at all.
#:
#: BOTH halves of E27's split are watched, and the reason is worth stating
#: because E27 makes their TRIGGERS opposite. A WATCH-GATED name is woken
#: BY an event -- that is its only route back. A WATCH-PRICED name is woken
#: by its limit alert, not by this command; it is watched anyway because a
#: periodic report or a changed outlook moves the FAIR VALUE the MBP is
#: computed from, and an alert armed at a stale MBP is the failure E27's
#: "an alert level is NOT an MBP" clause exists to prevent. So: for a gated
#: name a hit here is the trigger, for a priced name it is notice that the
#: trigger's level may be wrong.
WATCHED_STATUSES = (*R.WATCH_STATUSES, "PIPELINE")

#: How many releases to ask for per ticker. The feed caps a page at 200 and
#: a watched name files a few dozen a year, so one page is a wide margin.
PAGE_LIMIT = 60

PASS_PERIODIC = "periodic report"
PASS_GUIDANCE = "guidance change"
PASS_WARNING = "profit warning"

#: Title patterns, each with the kind it establishes. Ordered: the first
#: match decides, so a "profit warning" that also says "guidance" is
#: reported as the warning it is.
#:
#: These are TITLE patterns and match nothing but the headline. The list is
#: deliberately short: every entry here is a phrase an issuer uses when it
#: is changing what it expects to earn, and none of them is a phrase used
#: to announce a person, a purchase or a share transaction.
TITLE_RULES: tuple[tuple[str, str], ...] = (
    (PASS_WARNING, r"\bprofit warning\b"),
    (PASS_WARNING, r"\bearnings warning\b"),
    (PASS_WARNING, r"\bwarning\b.*\b(profit|earnings|result)"),
    (PASS_GUIDANCE, r"\bguidance\b"),
    (PASS_GUIDANCE, r"\boutlook\b"),
    (PASS_GUIDANCE, r"\bexpects? to (deliver|report|end|achieve)\b"),
    (PASS_GUIDANCE, r"\bpreliminary\b.*\b(result|figure|number)"),
    (PASS_GUIDANCE, r"\btrading (update|statement)\b"),
    (PASS_GUIDANCE, r"\b(raises?|lifts?|lowers?|cuts?|upgrades?|downgrades?|"
                    r"revises?|adjusts?|reiterates?|confirms?|narrows?|widens?)\b"
                    r".{0,40}\b(guidance|outlook|expectations?|forecast|targets?)\b"),
    (PASS_GUIDANCE, r"\bfinancial (targets?|ambitions?)\b"),
    (PASS_GUIDANCE, r"\borganic growth\b"),
    (PASS_GUIDANCE, r"\bebit(da)? margin\b"),
    (PASS_GUIDANCE, r"\brevenue growth\b"),
)

_COMPILED: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (kind, re.compile(pattern, re.IGNORECASE)) for kind, pattern in TITLE_RULES
)


@dataclass(frozen=True)
class Decision:
    """One disclosure, and whether it would make the owner re-run §5."""

    release: Release
    ticker: str
    passes: bool
    kind: str
    why: str


def classify(release: Release, ticker: str) -> Decision:
    """Pass a disclosure, or reject it, with the reason either way.

    The category decides a periodic report because the exchange's own
    category is a fact about the filing. Everything else is decided on the
    HEADLINE, because the category cannot: Pandora's H1 2026 report and its
    CFO appointment share the category *Inside information*.
    """
    if release.is_report_category:
        return Decision(release, ticker, True, PASS_PERIODIC,
                        f"exchange category {release.category!r}")
    for kind, pattern in _COMPILED:
        found = pattern.search(release.headline)
        if found:
            return Decision(release, ticker, True, kind,
                            f"title matches {found.re.pattern!r}")
    return Decision(release, ticker, False, "",
                    f"category {release.category!r}, no guidance or warning "
                    f"phrase in the title")


# --- state ------------------------------------------------------------------


def load_state(path: Path = STATE_PATH) -> dict:
    """The cursor, or an empty one. A malformed file is an error, not a
    silent reset: resetting would re-report every disclosure a name has."""
    if not path.exists():
        return {"version": STATE_VERSION, "seen": {}}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f"{path}: state file is not readable JSON ({exc}). "
                          f"Delete it to start a fresh baseline, knowing that "
                          f"the next run reports nothing and re-baselines.") from exc
    if not isinstance(document, dict) or "seen" not in document:
        raise ConfigError(f"{path}: state file has no 'seen' map.")
    return document


def save_state(document: dict, path: Path = STATE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")
    return path


# --- the notifier -----------------------------------------------------------


def notify_line(decision: Decision) -> str:
    """One disclosure, one line: ticker, date, title."""
    return (f"{decision.ticker} {decision.release.released_date} "
            f"{decision.release.headline}")


def post_ntfy(lines: Sequence[str], *, url: str | None = None,
              opener: Callable | None = None) -> str:
    """POST the lines to the ntfy topic. Returns what happened, in words.

    No message is sent for an empty list -- a watcher that pings to say
    nothing happened trains its reader to ignore it.
    """
    if not lines:
        return "nothing to send"
    url = url or env.get(NTFY_ENV)
    if not url:
        return (f"NOT SENT: {NTFY_ENV} is not set. The topic URL is the only "
                f"secret ntfy has, so it is read from the environment and "
                f"never stored here.")
    body = "\n".join(lines).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Title": f"vss watch: {len(lines)} disclosure(s)",
                 "Content-Type": "text/plain; charset=utf-8"})
    try:
        opener = opener or urllib.request.urlopen
        with opener(request, timeout=NTFY_TIMEOUT_SECONDS) as response:
            code = getattr(response, "status", None) or response.getcode()
        return f"sent {len(lines)} line(s) to ntfy (HTTP {code})"
    except urllib.error.HTTPError as exc:
        raise ConfigError(f"ntfy refused the POST: HTTP {exc.code}") from exc
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f"{type(exc).__name__} posting to ntfy: {exc}") from exc


# --- the run ----------------------------------------------------------------


@dataclass
class TickerResult:
    ticker: str
    state: str                      # watched | not on this feed | error
    detail: str = ""
    passed: list[Decision] = field(default_factory=list)
    rejected: list[Decision] = field(default_factory=list)
    first_run: bool = False


def watched_tickers(watchlist_path: Path = WATCHLIST_PATH) -> list[tuple[str, str]]:
    """(ticker, status) for every watched name, in file order.

    Watched = WATCH-PRICED, WATCH-GATED or PIPELINE (``WATCHED_STATUSES``).
    """
    return [(entry.ticker, entry.status)
            for entry in load_watchlist(watchlist_path)
            if entry.status in WATCHED_STATUSES]


def run_watch(*, watchlist_path: Path = WATCHLIST_PATH,
              issuers_path: Path = ISSUERS_PATH,
              state_path: Path = STATE_PATH,
              send: bool = True,
              ntfy_url: str | None = None,
              fetch: Callable | None = None,
              poster: Callable | None = None,
              now: str | None = None) -> tuple[int, str]:
    """Check every watched name once. Returns (exit code, report)."""
    fetch = fetch or (lambda issuer: fetch_releases(issuer, limit=PAGE_LIMIT,
                                                    language=issuer.language)[0])
    poster = poster or post_ntfy
    stamp = now or datetime.now(timezone.utc).isoformat(timespec="seconds")

    issuers = load_issuers(issuers_path)
    document = load_state(state_path)
    seen = document.setdefault("seen", {})

    results: list[TickerResult] = []
    for ticker, status in watched_tickers(watchlist_path):
        issuer = issuers.get(ticker)
        if issuer is None:
            results.append(TickerResult(
                ticker, "not on this feed",
                "no entry in config/nordic_issuers.yaml. The Nordic feed "
                "carries Copenhagen, Stockholm and Helsinki; a US or Paris "
                "listing is not on it and this command does not pretend "
                "otherwise."))
            continue
        try:
            releases = fetch(issuer)
        except NordicError as exc:
            results.append(TickerResult(ticker, "error", str(exc)))
            continue

        cursor = seen.get(ticker, {})
        last_id = int(cursor.get("last_id", 0))
        result = TickerResult(ticker, "watched", first_run=not cursor)
        for release in releases:
            if release.disclosure_id <= last_id:
                continue
            decision = classify(release, ticker)
            (result.passed if decision.passes else result.rejected).append(decision)
        # FIRST RUN ESTABLISHES A BASELINE AND REPORTS NOTHING. The
        # alternative is a first notification carrying a year of history,
        # which is how a watcher gets muted on the day it is installed.
        if result.first_run:
            result.passed, result.rejected = [], []
        newest = max([r.disclosure_id for r in releases] + [last_id])
        seen[ticker] = {"last_id": newest,
                        "last_released": releases[0].released_date if releases else
                                         cursor.get("last_released", ""),
                        "checked_at": stamp}
        results.append(result)

    passed = [d for r in results for d in r.passed]
    lines = [notify_line(d) for d in passed]
    sent = poster(lines, url=ntfy_url) if send else (
        f"not sent (--no-send): {len(lines)} line(s) withheld")

    document["version"] = STATE_VERSION
    document["checked_at"] = stamp
    save_state(document, state_path)
    return 0, render(results, sent=sent, state_path=state_path, stamp=stamp)


def render(results: Iterable[TickerResult], *, sent: str, state_path: Path,
           stamp: str) -> str:
    results = list(results)
    passed = [d for r in results for d in r.passed]
    rejected = [d for r in results for d in r.rejected]
    out = [f"# vss watch -- {stamp}", ""]
    out.append(f"- watched: {', '.join(r.ticker for r in results) or 'nothing'}")
    out.append(f"- state: `{state_path}`")
    out.append(f"- ntfy: {sent}")
    out.append("")

    if passed:
        out.append(f"## {len(passed)} DISCLOSURE(S) WORTH A RE-RUN")
        out.append("")
        out.append("| ticker | date | category | headline | why it passed |")
        out.append("|---|---|---|---|---|")
        for d in passed:
            out.append(f"| {d.ticker} | {d.release.released_date} | "
                       f"{d.release.category} | {d.release.headline} | "
                       f"{d.kind}: {d.why} |")
        out.append("")
    else:
        out.append("## NOTHING NEW WORTH A RE-RUN")
        out.append("")
        out.append("No periodic report, guidance change or profit warning "
                   "since the last run. Nothing was sent.")
        out.append("")

    out.append(f"## REJECTED: {len(rejected)} disclosure(s) the filter did NOT "
               f"tell you about")
    out.append("")
    if rejected:
        for d in rejected:
            out.append(f"- `{d.ticker}` {d.release.released_date} "
                       f"[{d.release.category}] {d.release.headline}")
    else:
        out.append("- none")
    out.append("")
    out.append("**A rejected row is a filing this run decided would not change "
               "a section 5 answer.** The filter reads the exchange's category "
               "and the headline and nothing else; a guidance change published "
               "under a bland title would sit in this list. That is why the "
               "list is printed in full rather than counted.")
    out.append("")

    quiet = [r for r in results if r.state != "watched"]
    if quiet:
        out.append("## NOT CHECKED")
        out.append("")
        for r in quiet:
            out.append(f"- `{r.ticker}` — {r.state}: {r.detail}")
        out.append("")
    first = [r.ticker for r in results if r.first_run]
    if first:
        out.append(f"**First run for {', '.join(first)}** — the cursor was "
                   f"empty, so this run recorded where the feed stands and "
                   f"reported nothing. The next run reports what arrives "
                   f"after it.")
        out.append("")
    return "\n".join(out)


def cron_line(python: str = str(Path(__file__).resolve().parents[1] / ".venv" / "bin" / "python"),
              repo: str = str(Path(__file__).resolve().parents[1])) -> str:
    """The line to add by hand. This command installs nothing."""
    return (f"7 7,17 * * 1-5 cd {repo} && VSS_NTFY_URL=\"$VSS_NTFY_URL\" "
            f"{python} -m vss watch >> {repo}/data/watch.log 2>&1")
