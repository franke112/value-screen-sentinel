"""CLI entrypoint: ``python -m vss run``.

The report goes to stdout, every log line goes to stderr, so cron can split
them with a plain shell redirect.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import ConfigError
from .prices import BATCH_SIZE as PRICE_BATCH_SIZE
from .runner import DB_PATH, WATCHLIST_PATH, run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vss", description="Value-screen sentinel: watchlist monitor."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="fetch, evaluate and report the watchlist")
    run_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="print the report but write nothing: no report file, no cache, no database",
    )
    run_cmd.add_argument(
        "--config",
        metavar="PATH",
        default=None,
        help="use an alternate watchlist instead of config/watchlist.yaml",
    )
    run_cmd.add_argument(
        "--ticker",
        metavar="X",
        default=None,
        help="restrict the run to a single ticker from the watchlist",
    )
    earnings_cmd = sub.add_parser(
        "earnings",
        help="read a primary-source report and flag FRAMEWORK 4.2 trips",
    )
    earnings_cmd.add_argument("--ticker", required=True, metavar="X",
                              help="any ticker from the watchlist, whatever its status")
    source_group = earnings_cmd.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--url", metavar="URL",
        help="primary source: company IR release or filing. NEVER a news article",
    )
    source_group.add_argument(
        "--text-file", metavar="PATH",
        help="a locally saved primary source: text, HTML or a downloaded PDF",
    )
    earnings_cmd.add_argument(
        "--shadow", action=argparse.BooleanOptionalAction, default=True,
        help="log to sqlite and send nothing (default: on)",
    )
    earnings_cmd.add_argument(
        "--period", metavar="YYYY-Qn", default=None,
        help="extract this period, reading it from a comparative column if "
             "the document is about another quarter",
    )
    earnings_cmd.add_argument(
        "--compare", action="store_true",
        help="read the source twice and null any field the two runs disagree on",
    )
    earnings_cmd.add_argument("--config", metavar="PATH", default=None,
                              help="use an alternate watchlist")

    xbrl_cmd = sub.add_parser(
        "xbrl",
        help="pull a US filer's tagged facts from SEC XBRL -- no HTML, no PDF",
    )
    xbrl_cmd.add_argument("--ticker", required=True, metavar="X",
                          help="any ticker from the watchlist, whatever its status")
    xbrl_cmd.add_argument("--cik", type=int, default=None, metavar="N",
                          help="override the watchlist's cik for this run")
    xbrl_cmd.add_argument("--limit", type=int, default=None, metavar="N",
                          help="how many recent periods to pull "
                               "(default: 8 quarters, or 5 years with --annual)")
    xbrl_cmd.add_argument("--config", metavar="PATH", default=None,
                          help="use an alternate watchlist")
    xbrl_cmd.add_argument(
        "--annual", action="store_true",
        help="fetch the ANNUAL facts section 5 needs -- cash flow, capex, "
             "share count and net debt -- and emit "
             "config/manual/<TICKER>.yaml. Filers stopped tagging discrete "
             "fourth quarters in 2021, so the quarter shape cannot reach a "
             "current twelve-month basis and this can")
    xbrl_cmd.add_argument(
        "--write", action="store_true",
        help="with --annual: write config/manual/<TICKER>.yaml. Refuses a "
             "file of any other origin -- a history mixing whole units with "
             "millions is a history in which no comparison means anything")
    xbrl_cmd.add_argument(
        "--force", action="store_true",
        help="with --write: replace a file this path itself wrote, backing it "
             "up first. Discards every VERIFIED flag it holds. It does NOT "
             "open the mixed-origin refusal")
    xbrl_cmd.add_argument("--manual-dir", metavar="PATH", default=None,
                          help="write into an alternate directory instead of "
                               "config/manual")
    xbrl_cmd.add_argument(
        "--quote-currency", metavar="CCY", default=None,
        help="INTAKE only -- the listing currency of a ticker that is NOT "
             "on the watchlist. Entering a name on the watchlist stamps "
             "dd_at_entry and freezes Gate 1 (E12), so a candidate is read "
             "BEFORE it is entered; the quote currency is a fact about a "
             "LISTING and not a tagged fact, so it is stated here or the "
             "intake refuses")
    xbrl_cmd.add_argument(
        "--name", metavar="NAME", default=None,
        help="INTAKE only -- override the filer name. Left out, the SEC's "
             "own `entityName` is used, which is the filer's own")

    manual_cmd = sub.add_parser(
        "manual",
        help="validate a hand-entered fundamentals file and gate section 5 on it",
    )
    manual_cmd.add_argument("--ticker", required=True, metavar="X",
                            help="the ticker whose file to read: "
                                 "config/manual/<TICKER>.yaml")
    manual_cmd.add_argument("--asof", metavar="YYYY-MM-DD", default=None,
                            help="the date the accounts are judged against, so "
                                 "STALE is reproducible (default: today)")
    manual_cmd.add_argument("--dir", metavar="PATH", default=None,
                            help="read from an alternate directory instead of "
                                 "config/manual")

    appendix_cmd = sub.add_parser(
        "appendix",
        help="read an issuer's figures appendix (xlsx) through a committed "
             "cell map and emit a filled config/manual/<TICKER>.yaml",
    )
    appendix_cmd.add_argument("--ticker", required=True, metavar="X",
                              help="the ticker whose map to use: "
                                   "config/manual/maps/<TICKER>.yaml")
    appendix_cmd.add_argument("--xlsx", required=True, metavar="PATH",
                              help="the appendix workbook, normally one that "
                                   "`vss nordic` downloaded into sources/")
    appendix_cmd.add_argument("--write", action="store_true",
                              help="write config/manual/<TICKER>.yaml. Refuses "
                                   "when the file exists: overwriting would "
                                   "reset every VERIFIED figure in it")
    appendix_cmd.add_argument("--force", action="store_true",
                              help="with --write: replace an existing file, "
                                   "backing it up first. Discards every "
                                   "VERIFIED flag it holds")
    appendix_cmd.add_argument("--maps-dir", metavar="PATH", default=None,
                              help="alternate map directory")
    appendix_cmd.add_argument("--manual-dir", metavar="PATH", default=None,
                              help="alternate output directory")

    nordic_cmd = sub.add_parser(
        "nordic",
        help="list and download report documents from the Nordic exchange's "
             "own disclosure feed. Downloads and records; reads nothing",
    )
    nordic_cmd.add_argument("--ticker", required=True, metavar="X",
                            help="the ticker, as config/nordic_issuers.yaml keys it")
    nordic_cmd.add_argument("--resolve", metavar="TEXT", default=None,
                            help="search the feed for this text and show the "
                                 "(market, company) candidates for --ticker. "
                                 "The service has no company directory, so the "
                                 "mapping is established once and stored")
    nordic_cmd.add_argument("--write", action="store_true",
                            help="with --resolve: append the top candidate to "
                                 "config/nordic_issuers.yaml. Backs the file up "
                                 "first and never replaces an existing entry")
    nordic_cmd.add_argument("--download", type=int, default=None, metavar="ID",
                            help="download the document of this disclosure id")
    nordic_cmd.add_argument("--attachment", type=int, default=None, metavar="N",
                            help="which file of the disclosure. Required when "
                                 "it carries more than one -- never guessed")
    nordic_cmd.add_argument("--period", metavar="YYYY-Qn", default=None,
                            help="MANUAL, and required to download: the fiscal "
                                 "period the document COVERS. YYYY-Qn, "
                                 "YYYY-H1, YYYY-H2 or YYYY-FY")
    nordic_cmd.add_argument("--reports", action="store_true",
                            help="show only report categories. The category is "
                                 "the issuer's filing choice, so this HIDES "
                                 "real reports; the count hidden is printed")
    nordic_cmd.add_argument("--language", metavar="XX", default=None,
                            help="restrict to one language edition, e.g. en. "
                                 "Defaults to the issuer's stored preference")
    nordic_cmd.add_argument("--limit", type=int, default=None, metavar="N",
                            help="rows per page (the service caps at 200)")
    nordic_cmd.add_argument("--start", type=int, default=0, metavar="N",
                            help="first row of the window. Pagination is start, "
                                 "not offset -- offset is accepted and ignored")
    nordic_cmd.add_argument("--sources-dir", metavar="PATH", default=None,
                            help="where documents and the manifest go "
                                 "(default: sources)")

    watch_cmd = sub.add_parser(
        "watch",
        help="check the WATCH-PRICED, WATCH-GATED and PIPELINE names for "
             "new periodic reports, "
             "guidance changes and profit warnings, and notify via ntfy",
    )
    watch_cmd.add_argument("--state", metavar="PATH", default=None,
                           help="where the cursor is kept (default: "
                                "data/watch_state.json). NOT the watchlist: a "
                                "cursor is not a decision")
    watch_cmd.add_argument("--no-send", action="store_true",
                           help="check and print, POST nothing. The state file "
                                "is still advanced")
    watch_cmd.add_argument("--ntfy-url", metavar="URL", default=None,
                           help="override the topic URL (default: the "
                                "VSS_NTFY_URL environment variable)")
    watch_cmd.add_argument("--cron", action="store_true",
                           help="print the crontab line to add BY HAND and "
                                "exit. This command installs nothing")
    watch_arm = watch_cmd.add_mutually_exclusive_group()
    watch_arm.add_argument("--sec-only", action="store_true",
                           help="ask EDGAR only: the SEC arm, which covers "
                                "every watched US filer with a `cik:` and "
                                "passes 10-K, 10-Q and 8-K ITEM 2.02 (the "
                                "earnings release, which arrives before the "
                                "10-Q). NOTIFY ONLY -- it never writes the "
                                "store or the watchlist")
    watch_arm.add_argument("--nordic-only", action="store_true",
                           help="ask the Nasdaq Nordic feed only. Without "
                                "either flag BOTH arms run, each reporting "
                                "the names it covers")
    watch_cmd.add_argument("--read", action="store_true",
                           help="SEC arm: read each passed filing through "
                                "`vss earnings` IN SHADOW (read twice, "
                                "compared), writing the alert to "
                                "data/autoread/ and SENDING IT NOWHERE. Runs "
                                "after the notification, so it cannot cost it")

    refresh_cmd = sub.add_parser(
        "refresh",
        help="E92: fetch a name's filing on its catalyst date, extract into "
             "the store and write reports/REFRESH-<TICKER>-<date>.md. It "
             "NEVER writes fv_base, tier, mbp, stop or status, and NEVER "
             "scores a gate",
    )
    refresh_target = refresh_cmd.add_mutually_exclusive_group(required=True)
    refresh_target.add_argument("--ticker", metavar="X", default=None,
                                help="one ticker from the watchlist")
    refresh_target.add_argument(
        "--due", action="store_true",
        help="every watchlist name whose catalyst date has passed and whose "
             "store holds no data for the period that catalyst reports on")
    refresh_cmd.add_argument(
        "--dry-run", action="store_true",
        help="say what would be fetched and from where; fetch nothing, write "
             "no store entry, no report and no state")
    refresh_cmd.add_argument("--config", metavar="PATH", default=None,
                             help="use an alternate watchlist")
    refresh_cmd.add_argument("--manual-dir", metavar="PATH", default=None,
                             help="read and write stores in an alternate "
                                  "directory instead of config/manual")

    sales_cmd = sub.add_parser(
        "sales",
        help="every closed position against OMXS30 and the S&P 500 from its "
             "own sale date, plus fixed 30/90/365-day marks (FRAMEWORK-EDITS "
             "B45). Reads the watchlist's sales: blocks; a fill with no "
             "price is DATA MISSING, never read off a bar",
    )
    sales_cmd.add_argument(
        "--dry-run", action="store_true",
        help="print the record but write no report file and no price cache",
    )
    sales_cmd.add_argument("--config", metavar="PATH", default=None,
                           help="use an alternate watchlist")

    shadow_cmd = sub.add_parser(
        "shadow",
        help="THE SHADOW BOOK (FRAMEWORK-EDITS E114): every refusal against "
             "OMXS30 and the S&P 500 from the day its verdict was written, "
             "at 1/3/6/12 months. Reads config/shadow_book.csv; a verdict "
             "date with no settled close is DATA MISSING, never the nearest "
             "bar. NOT A SIGNAL -- read once a year",
    )
    shadow_cmd.add_argument(
        "--dry-run", action="store_true",
        help="print the book but write no report file and no price cache",
    )
    shadow_cmd.add_argument("--book", metavar="PATH", default=None,
                            help="use an alternate shadow book")

    overview_cmd = sub.add_parser(
        "overview",
        help="regenerate reports/OVERVIEW.html -- the READ-ONLY page: where "
             "things stand, what is outstanding, what has happened. Reads "
             "config/, reference/ and data/ and NEVER the network; writes "
             "one file under reports/ and nothing else, anywhere",
    )
    overview_cmd.add_argument(
        "--output", metavar="PATH", default=None,
        help="write somewhere other than reports/OVERVIEW.html")

    checkin_cmd = sub.add_parser(
        "checkin",
        help="THE DEAD MAN'S SWITCH's independent leg: is a completed run on "
             "record, and are the timers still enabled? Silence when healthy",
    )
    checkin_cmd.add_argument(
        "--no-send", action="store_true",
        help="print the findings, POST nothing")
    checkin_cmd.add_argument(
        "--hours", type=int, default=None, metavar="N",
        help="how many hours without a completed nightly run counts as a gap "
             "(default: 72)")

    backfill_cmd = sub.add_parser(
        "backfill-vendor-strings",
        help="seed data/vss.sqlite with the vendor SECTOR and INDUSTRY "
             "strings from every fundamentals store still on disk, so "
             "E51's and E96's string limbs outlive E93's snapshot pruning "
             "(CODE-REVIEW-2026-09-01 D3). Idempotent; run once per machine",
    )
    backfill_cmd.add_argument(
        "--snapshot-root", metavar="DIR", default=None,
        help="where the dated fundamentals stores live "
             "(default: data/screener_snapshots)")

    refs_cmd = sub.add_parser(
        "reference-figures",
        help="E103: fetch the issuer's OWN free cash flow and net debt for "
             "E101's construction checks, and enter them UNVERIFIED. They "
             "are REFERENCE figures -- compared against a valuation, never "
             "used to build one -- which is why no read-back is required "
             "first and why the section 5 gate refuses if one is ever wired "
             "into a basis",
    )
    refs_cmd.add_argument("--ticker", metavar="TICKER", default=None,
                          help="one name (default: every store)")
    refs_cmd.add_argument(
        "--confirm", action="store_true",
        help="E104: re-extract every DISAGREEING check's comparator on a "
             "narrow excerpt around the line the first pass quoted, and "
             "withdraw any figure two independent readings do not agree on. "
             "A figure the owner has VERIFIED is never re-read")
    refs_cmd.add_argument("--write", action="store_true",
                          help="write what was obtained into the store "
                               "(UNVERIFIED). Without it, nothing is written "
                               "and the plan is printed")

    briefing_cmd = sub.add_parser(
        "briefing",
        help="E76's BRIEFING: the research a reading stands on, assembled "
             "from the filings on EDGAR plus web search where a filing "
             "cannot answer. RESEARCH AND NOT A VERDICT -- it carries no "
             "judgement, no growth rate and no fair value, and refuses "
             "itself if it does. The E76 reading stays the owner's",
    )
    briefing_cmd.add_argument("--ticker", required=True, metavar="X",
                              help="a ticker with a complete store")
    briefing_cmd.add_argument("--cik", type=int, default=None, metavar="N",
                              help="override the CIK from the watchlist or "
                                   "the store")
    briefing_cmd.add_argument("--asof", metavar="YYYY-MM-DD", default=None,
                              help="the date the briefing is dated and the "
                                   "twelve insider months are counted back "
                                   "from (default: today)")
    briefing_cmd.add_argument("--write", action="store_true",
                              help="write reports/BRIEFING-<TICKER>-<date>.md")
    briefing_cmd.add_argument(
        "--no-web", dest="web", action="store_false", default=True,
        help="do not call out. The sections a filing cannot answer then say "
             "NOT FILLED, which is the honest answer and not a hole")

    prepare_cmd = sub.add_parser(
        "prepare",
        help="everything that can happen before the owner sits down to "
             "review a name, run by the machine, ending in a readiness "
             "report under reports/prepare/. Route, fetch, fill, compute, "
             "verification list, human-step context -- each an EXISTING "
             "path; where none exists the report says so. NEVER writes "
             "fv_base, tier, mbp, stop_price or status; never writes the "
             "watchlist; backs up before any write to config/manual/")
    prepare_target = prepare_cmd.add_mutually_exclusive_group(required=True)
    prepare_target.add_argument("--ticker", metavar="X", default=None,
                                help="one ticker from the watchlist")
    prepare_target.add_argument("--all-pipeline", action="store_true",
                                help="every PIPELINE name on the watchlist")
    prepare_cmd.add_argument("--dry-run", action="store_true",
                             help="route, list the manifest, compute and verify from "
                                  "what is on disk; fetch nothing from a feed, read "
                                  "nothing with a model, write nothing anywhere")
    prepare_cmd.add_argument("--force", action="store_true",
                             help="re-fill a store that is already on file and "
                                  "re-extract a period already entered. The file is "
                                  "backed up first and the VERIFIED figures being "
                                  "discarded are named (appendix.py's semantics)")
    prepare_cmd.add_argument("--config", metavar="PATH", default=None,
                             help="use an alternate watchlist")
    prepare_cmd.add_argument("--manual-dir", metavar="PATH", default=None,
                             help="read and write stores in an alternate directory")
    strike_cmd = sub.add_parser(
        "strike",
        help="re-strike one name off its store on the record's PRE-REGISTERED "
             "growth view, write the run record and the strike doc, and print "
             "the before/after table -- fv_base, bear, bull, the MBP with the "
             "tier on both sides, g*, and which leg moved. One front door for "
             "what the dated scripts in tools/ do. It NEVER writes the "
             "watchlist: fv_base, tier, mbp, stop_price and status stay the "
             "owner's act")
    strike_cmd.add_argument("--ticker", metavar="X", required=True,
                            help="the name to strike; it needs a store and a "
                                 "registered growth view")
    strike_cmd.add_argument("--asof", metavar="YYYY-MM-DD", default=None,
                            help="the date the accounts are judged against "
                                 "(default: today)")
    strike_cmd.add_argument("--dry-run", action="store_true",
                            help="print the table and the document; write nothing")
    strike_cmd.add_argument("--stamp", metavar="TEXT", default=None,
                            help="the record's filename stamp (default: the "
                                 "as-of date). Use it where a ruling names the "
                                 "pass, e.g. 2026-09-19-e117")
    strike_cmd.add_argument("--note", metavar="TEXT", default="",
                            help="one sentence into the record's notes and the "
                                 "document's header")
    strike_cmd.add_argument("--ignore-gate", action="store_true",
                            help="strike although the section 5 gate REFUSES "
                                 "(E21). The refusal is printed, written into "
                                 "the record's notes and into the strike doc")
    strike_cmd.add_argument("--config", metavar="PATH", default=None,
                            help="use an alternate watchlist")
    strike_cmd.add_argument("--manual-dir", metavar="PATH", default=None,
                            help="read stores from an alternate directory")
    strike_cmd.add_argument("--records-dir", metavar="PATH", default=None,
                            help="read and write run records elsewhere")

    review_cmd = sub.add_parser(
        "review",
        help="the review session's record: validate a "
             "reference/reviews/<TICKER>/<date>.yaml against the playbook's "
             "step list and E28's ordering, or record one -- the owner's note "
             "appended verbatim to the watchlist entry (backup first) and the "
             "growth view registered where the code keeps growth views. "
             "NEVER writes status, fv_base, tier, mbp or stop_price; the file "
             "is re-read after the write and restored if anything else moved")
    review_what = review_cmd.add_mutually_exclusive_group(required=True)
    review_what.add_argument("--validate", metavar="PATH", default=None,
                             help="check the review file and print every refusal; writes nothing")
    review_what.add_argument("--record", metavar="PATH", default=None,
                             help="validate, then append the note and register the view")
    review_what.add_argument("--schema", action="store_true",
                             help="print config/review/SCHEMA.md as the code defines it")
    review_cmd.add_argument("--dry-run", action="store_true",
                            help="with --record: validate and say what would be written, write nothing")
    review_cmd.add_argument("--config", metavar="PATH", default=None,
                            help="use an alternate watchlist")

    screen_cmd = sub.add_parser(
        "screen",
        help="build the screening universe and snapshot its prices "
             "(phase 1: no filtering, no ranking, no watchlist writing)",
    )
    screen_cmd.add_argument(
        "--weekly", action="store_true",
        help="E93: the WHOLE chain unattended -- snapshot, fundamentals, "
             "rank -- then store the ranked order, compare it with the "
             "previous stored run, write reports/SCREEN-<date>.md and post a "
             "pointer if anything crossed the top 10. NEVER writes the "
             "watchlist and NEVER enters a name as PIPELINE: that stamps "
             "dd_at_entry and freezes Gate 1 (E12), which a clock may not do")
    screen_cmd.add_argument(
        "--keep", type=int, default=None, metavar="N",
        help="with --weekly: how many price snapshots to keep (default: 4). "
             "Every ranking is kept forever whatever this says")
    screen_cmd.add_argument(
        "--no-notify", action="store_true",
        help="with --weekly: compute and report, POST nothing")
    screen_cmd.add_argument(
        "--universe-report", action="store_true",
        help="what the committed universe lists contain: count per market, "
             "count excluded per reason, count without a valid yahoo mapping",
    )
    screen_cmd.add_argument(
        "--snapshot-only", action="store_true",
        help="fetch prices for the whole universe and store them, filtering nothing",
    )
    screen_cmd.add_argument(
        "--filter1", action="store_true",
        help="run the exclusion list and the dislocation band against a stored "
             "snapshot. Fetches nothing",
    )
    screen_cmd.add_argument(
        "--fundamentals", action="store_true",
        help="fetch fundamentals for the survivors of filter 1, one ticker at a "
             "time, and store them beside the price snapshot",
    )
    screen_cmd.add_argument(
        "--filter2", action="store_true",
        help="run the whole chain against stored data: step 0, filter 1, then "
             "coarse quality. Fetches nothing",
    )
    screen_cmd.add_argument(
        "--rank", action="store_true",
        help="the whole chain plus the two-component ranking key "
             "(FRAMEWORK-EDITS E6). Fetches only the exchange rates it needs",
    )
    screen_cmd.add_argument(
        "--fx-from-manifest", metavar="PATH", default=None,
        help="with --rank: replay the exchange rates recorded in a stored "
             "ranking-manifest.json instead of fetching. Without it the rates "
             "are the LATEST close whatever --asof says, so a re-run of an old "
             "date is auditable but NOT reproducible. A pair the manifest does "
             "not carry fails and is named; it is never quietly fetched",
    )
    screen_cmd.add_argument(
        "--write-pipeline", action="store_true",
        help="with --rank: enter the top names in config/watchlist.yaml as "
             "PIPELINE. Backs the file up first and never touches an existing "
             "entry. No mbp, no fv_base, no tier",
    )
    screen_cmd.add_argument(
        "--top", type=int, default=5, metavar="N",
        help="how many of the BOTH-legs list --write-pipeline enters (default: 5)",
    )
    screen_cmd.add_argument(
        "--dry-run", action="store_true",
        help="with --write-pipeline: show what would be written, write nothing",
    )
    screen_cmd.add_argument(
        "--from-snapshot", metavar="YYYY-MM-DD", default=None,
        help="which stored snapshot to read (default: the oldest one dated on "
             "or after --asof)",
    )
    screen_cmd.add_argument(
        "--exclusions", metavar="PATH", default=None,
        help="use an alternate exclusion list instead of config/screener_exclusions.csv",
    )
    screen_cmd.add_argument(
        "--asof", metavar="YYYY-MM-DD", default=None,
        help="the session to snapshot. Rows dated after it are DROPPED, so a "
             "re-run reproduces that day rather than today (default: today)",
    )
    screen_cmd.add_argument(
        "--tier", action="append", choices=["A", "B", "C"], metavar="A|B|C",
        help="which tier to load; repeatable (default: A)",
    )
    screen_cmd.add_argument(
        "--universe-dir", metavar="PATH", default=None,
        help="use an alternate universe directory instead of config/universe",
    )
    screen_cmd.add_argument(
        "--snapshot-root", metavar="PATH", default=None,
        help="where snapshots are written (default: data/screener_snapshots)",
    )
    screen_cmd.add_argument(
        "--runs-root", metavar="PATH", default=None,
        help="where filter1-candidates.csv, ranking.csv and the ranking "
             "manifest are written (default: data/screener_runs). A "
             "comparison run MUST set this: pointing only --snapshot-root at "
             "a scratch directory leaves the run writing its ranking over the "
             "real one for that date, which happened on 2026-08-31 to the "
             "2026-08-29 file",
    )
    screen_cmd.add_argument(
        "--batch-size", type=int, default=None, metavar="N",
        help=f"tickers per price request (default: {PRICE_BATCH_SIZE})",
    )
    screen_cmd.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="stop after N instruments -- a smoke test, never a real run",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    overrides = {}
    if getattr(args, "config", None):
        overrides["watchlist_path"] = Path(args.config)

    try:
        if args.command == "reference-figures":
            from .reference_figures import report_reference_figures

            if args.confirm:
                from .reference_figures import report_confirmations

                code, text = report_confirmations(ticker=args.ticker,
                                                  write=args.write)
                print(text)
                return code
            code, text = report_reference_figures(
                ticker=args.ticker, write=args.write)
            print(text)
            return code

        if args.command == "backfill-vendor-strings":
            from . import snapshot as snapshot_store
            from . import vendorstrings

            root = (Path(args.snapshot_root) if args.snapshot_root
                    else snapshot_store.SNAPSHOT_ROOT)
            outcome = vendorstrings.backfill_from_stores(
                vendorstrings.DB_PATH, root)
            for name, written in outcome["stores"]:
                print(f"  {name}: {written} ticker(s) offered")
            before, after = outcome["before"], outcome["after"]
            print(f"\ntickers: {before['tickers']} -> {after['tickers']}; "
                  f"classifications: {before['rows']} -> {after['rows']}")
            for line in vendorstrings.describe(vendorstrings.DB_PATH,
                                               backfill_hint=False):
                print(line)
            return 0

        if args.command == "checkin":
            from .heartbeat import STALE_AFTER_HOURS, checkin

            result = checkin(notify=not args.no_send,
                             threshold_hours=(args.hours if args.hours
                                              else STALE_AFTER_HOURS))
            if result.healthy:
                print("HEALTHY — a completed run is on record and the timers "
                      "are enabled and active.")
                return 0
            for line in result.lines:
                print(f"- {line}")
            print()
            print(f"notification: {result.posted}")
            # A finding is NOT an error. The check-in exits 0 so that its own
            # OnFailure= hook stays reserved for the check-in itself being
            # broken -- which is a different fact from the run being stale,
            # and must not be reported as the same one.
            return 0
        if args.command == "screen" and args.weekly:
            from datetime import date

            from .screenwatch import KEEP_SNAPSHOTS, run_weekly
            from .snapshot import SNAPSHOT_ROOT
            from .screen import UNIVERSE_DIR

            weekly = run_weekly(
                as_of=date.fromisoformat(args.asof) if args.asof else None,
                dry_run=args.dry_run,
                notify=not args.no_notify,
                keep_snapshots=args.keep if args.keep is not None else KEEP_SNAPSHOTS,
                snapshot_root=(Path(args.snapshot_root) if args.snapshot_root
                               else SNAPSHOT_ROOT),
                universe_dir=(Path(args.universe_dir) if args.universe_dir
                              else UNIVERSE_DIR),
                tiers=tuple(args.tier) if args.tier else ("A",),
                limit=args.limit,
            )
            print(weekly.report)
            return 0
        if args.command == "screen":
            from datetime import date

            from .filters import EXCLUSIONS_PATH
            from .screen import UNIVERSE_DIR, run_screen
            from .snapshot import SNAPSHOT_ROOT

            return run_screen(
                universe_report_only=args.universe_report,
                snapshot_only_flag=args.snapshot_only,
                filter1_flag=args.filter1,
                fundamentals_flag=args.fundamentals,
                filter2_flag=args.filter2,
                rank_flag=args.rank,
                write_pipeline_flag=args.write_pipeline,
                top=args.top,
                dry_run=args.dry_run,
                as_of=date.fromisoformat(args.asof) if args.asof else date.today(),
                universe_dir=Path(args.universe_dir) if args.universe_dir else UNIVERSE_DIR,
                tiers=tuple(args.tier) if args.tier else ("A",),
                snapshot_root=Path(args.snapshot_root) if args.snapshot_root else SNAPSHOT_ROOT,
                batch_size=args.batch_size or PRICE_BATCH_SIZE,
                limit=args.limit,
                runs_root=Path(args.runs_root) if args.runs_root else None,
                snapshot_date=(date.fromisoformat(args.from_snapshot)
                               if args.from_snapshot else None),
                exclusions_path=(Path(args.exclusions) if args.exclusions
                                 else EXCLUSIONS_PATH),
                fx_from_manifest=(Path(args.fx_from_manifest)
                                  if args.fx_from_manifest else None),
            )
        if args.command == "appendix":
            from datetime import date

            from .appendix import MAPS_DIR, run_appendix
            from .manual import MANUAL_DIR

            code, report = run_appendix(
                ticker=args.ticker,
                workbook=Path(args.xlsx),
                write=args.write,
                force=args.force,
                maps_dir=Path(args.maps_dir) if args.maps_dir else MAPS_DIR,
                manual_dir=(Path(args.manual_dir) if args.manual_dir
                            else MANUAL_DIR),
                as_of=date.today(),
            )
            print(report)
            return code
        if args.command == "nordic":
            from .nordic import MAX_LIMIT, SOURCES_DIR, run_nordic

            code, report = run_nordic(
                ticker=args.ticker,
                resolve_name=args.resolve,
                write=args.write,
                download_id=args.download,
                attachment_index=args.attachment,
                period=args.period,
                reports_only=args.reports,
                limit=args.limit or MAX_LIMIT,
                start=args.start,
                language=args.language,
                directory=(Path(args.sources_dir) if args.sources_dir
                           else SOURCES_DIR),
            )
            print(report)
            return code
        if args.command == "prepare":
            from .prepare import run_prepare
            code, report = run_prepare(
                ticker=args.ticker, all_pipeline=args.all_pipeline,
                dry_run=args.dry_run, force=args.force,
                manual_dir=Path(args.manual_dir) if args.manual_dir else None,
                **overrides,
            )
            print(report)
            return code
        if args.command == "strike":
            from datetime import date as _date
            from pathlib import Path as _Path
            from .strike import RECORDS_DIR, run_strike
            code, report = run_strike(
                ticker=args.ticker,
                as_of=(_date.fromisoformat(args.asof) if args.asof else None),
                dry_run=args.dry_run, stamp=args.stamp, note=args.note,
                ignore_gate=args.ignore_gate,
                watchlist_path=(_Path(args.config) if args.config
                                else _Path("config/watchlist.yaml")),
                manual_dir=(_Path(args.manual_dir) if args.manual_dir else None),
                records_dir=(_Path(args.records_dir) if args.records_dir
                             else RECORDS_DIR))
            print(report)
            return code
        if args.command == "review":
            from .review import run_review
            code, report = run_review(
                validate_path=args.validate, record_path=args.record, schema=args.schema,
                dry_run=args.dry_run, **overrides)
            print(report)
            return code
        if args.command == "refresh":
            from .manual import MANUAL_DIR
            from .refresh import run_refresh

            code, report = run_refresh(
                ticker=args.ticker,
                due=args.due,
                dry_run=args.dry_run,
                manual_dir=(Path(args.manual_dir) if args.manual_dir
                            else MANUAL_DIR),
                **overrides,
            )
            print(report)
            return code
        if args.command == "watch":
            from .nordic import ISSUERS_PATH
            from .watch import STATE_PATH, cron_line, run_watch

            if args.cron:
                print(cron_line())
                return 0
            state_path = Path(args.state) if args.state else STATE_PATH
            reports, codes = [], []
            if not args.sec_only:
                code, report = run_watch(
                    watchlist_path=overrides.get("watchlist_path", WATCHLIST_PATH),
                    issuers_path=ISSUERS_PATH,
                    state_path=state_path,
                    send=not args.no_send,
                    ntfy_url=args.ntfy_url,
                )
                reports.append(report)
                codes.append(code)
            if not args.nordic_only:
                from .secwatch import run_secwatch
                reader = None
                if args.read:
                    from .autoread import read_passed
                    reader = lambda items: read_passed(  # noqa: E731
                        items, watchlist_path=overrides.get(
                            "watchlist_path", WATCHLIST_PATH))
                code, report = run_secwatch(
                    watchlist_path=overrides.get("watchlist_path", WATCHLIST_PATH),
                    state_path=state_path,
                    send=not args.no_send,
                    ntfy_url=args.ntfy_url,
                    reader=reader,
                )
                reports.append(report)
                codes.append(code)
            print("\n\n---\n\n".join(reports))
            return max(codes) if codes else 0
        if args.command == "overview":
            from .overview import OUTPUT_PATH, write_overview

            written = write_overview(
                output=Path(args.output) if args.output else OUTPUT_PATH,
                watchlist_path=overrides.get("watchlist_path", WATCHLIST_PATH),
            )
            print(f"wrote {written}")
            return 0
        if args.command == "shadow":
            from .shadowbook import SHADOW_BOOK_PATH, run_shadow

            code, report = run_shadow(
                book_path=Path(args.book) if args.book else SHADOW_BOOK_PATH,
                dry_run=args.dry_run,
            )
            print(report)
            return code
        if args.command == "sales":
            from .sales import run_sales

            code, report = run_sales(
                watchlist_path=overrides.get("watchlist_path", WATCHLIST_PATH),
                dry_run=args.dry_run,
            )
            print(report)
            return code
        if args.command == "manual":
            from datetime import date

            from .manual import MANUAL_DIR, run_manual

            code, report = run_manual(
                ticker=args.ticker,
                as_of=date.fromisoformat(args.asof) if args.asof else date.today(),
                directory=Path(args.dir) if args.dir else MANUAL_DIR,
            )
            print(report)
            return code
        if args.command == "briefing":
            from datetime import date as _date

            from .briefing import run_briefing

            code, report = run_briefing(
                ticker=args.ticker, cik=args.cik,
                as_of=_date.fromisoformat(args.asof) if args.asof else None,
                write=args.write,
                watchlist_path=overrides.get("watchlist_path", WATCHLIST_PATH),
                web=args.web)
            print(report)
            return code
        if args.command == "xbrl":
            watchlist = overrides.get("watchlist_path", WATCHLIST_PATH)
            if args.annual:
                from .xbrl import ANNUAL_LIMIT, run_xbrl_annual

                code, report = run_xbrl_annual(
                    ticker=args.ticker, cik=args.cik,
                    limit=args.limit if args.limit is not None else ANNUAL_LIMIT,
                    watchlist_path=watchlist, db_path=DB_PATH,
                    manual_dir=(Path(args.manual_dir) if args.manual_dir
                                else None),
                    write=args.write, force=args.force,
                    name=args.name, quote_currency=args.quote_currency,
                )
                print(report)
                return code
            if args.write or args.force or args.manual_dir:
                raise ConfigError(
                    "--write, --force and --manual-dir belong to --annual. "
                    "The quarter shape is NEVER written: it carries no "
                    "cash-flow line, so it cannot supply section 5, and it is "
                    "printed for you to copy into config/watchlist.yaml after "
                    "verifying it.")
            from .xbrl import run_xbrl

            code, report = run_xbrl(
                ticker=args.ticker, cik=args.cik,
                limit=args.limit if args.limit is not None else 8,
                watchlist_path=watchlist, db_path=DB_PATH,
            )
            print(report)
            return code
        if args.command == "earnings":
            from .earnings import run_earnings

            code, alert = run_earnings(
                ticker=args.ticker,
                url=args.url,
                text_file=args.text_file,
                shadow=args.shadow,
                compare=args.compare,
                target_period=args.period,
                watchlist_path=overrides.get("watchlist_path", WATCHLIST_PATH),
                db_path=DB_PATH,
            )
            print(alert)
            return code
        return run(dry_run=args.dry_run, only_ticker=args.ticker, **overrides)
    except ConfigError as exc:
        logging.getLogger("vss").error("watchlist error: %s", exc)
        return 2
    except KeyboardInterrupt:  # pragma: no cover
        logging.getLogger("vss").error("interrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
