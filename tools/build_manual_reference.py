"""Generate docs/REFERENCE.md -- the command reference -- from the code.

    .venv/bin/python tools/build_manual_reference.py > docs/REFERENCE.md
    .venv/bin/python -m pytest tests/test_manual_reference.py -q

WHAT IS GENERATED, so it cannot drift:

* every `vss` subcommand and its flags, read off `vss.__main__.build_parser()`;
* every tools/*.py script and its flags, read off the tool's own
  `build_parser()`;
* every timer, read off deploy/*.timer and its service's ExecStart;
* the modules under vss/ and the backtest modules, one line each from
  their docstrings.

WHAT IS WRITTEN BY HAND, in this file: what each command reads, writes,
calls on the network and sends, its exit codes and the form of it that
changes nothing (COMMANDS, TOOLS), the environment variables (ENV) and the
file table (FILES). tests/test_manual_reference.py fails when a subcommand
or a tool has no entry here, when an entry names something that is gone,
and when docs/REFERENCE.md is not what this tool prints.

The same-commit rule (CLAUDE.md): a change to a parser, to a timer or to
this file lands with the regenerated docs/REFERENCE.md.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUTPUT = ROOT / "docs" / "REFERENCE.md"

#: What a command may touch, most harmless first. A command carries every
#: class that applies to ANY of its forms; `safe` names the form that
#: carries none of them.
READ_ONLY = "read-only"
LOCAL = "local"            # data/ and reports/: regenerable, gitignored
RECORD = "record"          # config/, reference/, sources/: the record
WATCHLIST = "watchlist"    # config/watchlist.yaml itself
SENDS = "sends"            # a POST to ntfy: the phone

CLASS_MEANING = (
    (READ_ONLY, "prints; writes no file and sends nothing"),
    (LOCAL, "writes under `data/` or `reports/` -- regenerable, gitignored"),
    (RECORD, "writes under `config/`, `reference/` or `sources/` -- the "
             "record, tracked in git; a backup is taken first where a file "
             "is replaced"),
    (WATCHLIST, "may write `config/watchlist.yaml`"),
    (SENDS, "may POST to ntfy, i.e. reach the owner's phone"),
)


@dataclass(frozen=True)
class Facts:
    #: One line for the at-a-glance table.
    what: str
    classes: tuple[str, ...]
    reads: str
    writes: str
    network: str
    sends: str
    exits: str = ""
    #: The invocation that writes nothing and sends nothing; "" where the
    #: command has no such form, "always" where every form is one.
    safe: str = ""
    #: Documented only where the file exists (a public-only helper).
    optional: bool = False


GENERAL_EXITS = ("`0` completed; `2` the watchlist or a configuration file "
                 "is missing or malformed; `130` interrupted")

COMMANDS: dict[str, Facts] = {
    "run": Facts(
        "The nightly report: fetch prices, apply the staleness gate, print every verdict",
        (LOCAL, SENDS),
        reads="`config/watchlist.yaml`; `data/cache/` where a fetch fails; "
              "the newest stored ranking (the E97 ranked watch); "
              "`data/refresh_state.json`",
        writes="`reports/<date>.md` (`reports/<date>.<TICKER>.md` with "
               "`--ticker`); `data/vss.sqlite`; `data/cache/`; "
               "`data/pricewatch_state.json`; `data/block_push_state.json`; "
               "`reports/OVERVIEW.html` after a full run",
        network="Yahoo (yfinance) daily prices; ntfy",
        sends="to `NTFY_TOPIC`: the NEEDS OWNER pointer (E92), a ranked-watch "
              "crossing (E97), every HELD or MBP name blocked on a stale "
              "close, and the dead man's switch's gap line",
        exits="`0` completed -- a ticker that errored is an ERROR row, not a "
              "failure; `1` coverage short: too few names were priced, the "
              "run does not reset the staleness clock and no healthcheck "
              "ping goes; `2` the watchlist is missing or malformed, or "
              "`--ticker` is not on it; `3` a `--dry-run` REFUSED because a "
              "HELD name or one with an MBP has a close more than one "
              "session old (no trigger was checked, so no report is "
              "printed); `130` interrupted",
        safe="`vss run --dry-run` (it still fetches prices, and the "
             "vendor library keeps its own cache under `data/yf-cache/`)"),
    "earnings": Facts(
        "Read one primary-source report and test it against the hard kills (section 4.2)",
        (LOCAL,),
        reads="`config/watchlist.yaml`; the URL or the file given",
        writes="`data/vss.sqlite` (table `earnings_runs`). Never `quarters:` "
               "-- the figures are PROPOSED in the alert as a YAML block",
        network="the source URL; OpenRouter (the extraction model)",
        sends="nothing, with or without `--shadow`",
        exits="`0` read; `1` the source could not be fetched or read; `2` "
              "watchlist error"),
    "xbrl": Facts(
        "A US filer's tagged figures straight from SEC; `--annual --write` fills a store",
        (LOCAL, RECORD),
        reads="`config/watchlist.yaml` (the `cik:`); with `--e140-fill` the "
              "existing store",
        writes="every form logs its run in `data/vss.sqlite`; no store is "
               "touched without `--write`. With `--annual --write`: "
               "`config/manual/<TICKER>.yaml`. With `--e140-fill --write`: "
               "two fields per year and `roll_forward:` in that store, the "
               "old file backed up",
        network="`data.sec.gov` (needs `VSS_SEC_CONTACT`)",
        sends="nothing",
        exits="`0` fetched; `1` SEC could not be read or the write was "
              "refused; `2` watchlist error, or `--write` without `--annual`",
        safe="none strictly: the run is logged. Without `--write` no store "
             "and no record is touched"),
    "manual": Facts(
        "Validate a store and say whether section 5 may read it; merge a draft into it",
        (RECORD,),
        reads="`config/manual/<TICKER>.yaml`; with `--merge-draft` also "
              "`config/manual/drafts/<TICKER>.<origin>.yaml`",
        writes="nothing. With `--merge-draft` (and no `--dry-run`): the "
               "store, the old file backed up to `arkiv/config-bak/`",
        network="none",
        sends="nothing",
        exits="`0` the store loads and section 5 may read it; `1` section 5 "
              "REFUSES (an UNVERIFIED figure, a stale file, legs from two "
              "periods); `2` the file is malformed",
        safe="`vss manual --ticker X`; `--merge-draft --dry-run`"),
    "pdfdraft": Facts(
        "A model reads a report's statement pages twice into a DRAFT, never the store",
        (RECORD,),
        reads="the PDF under `sources/`; the live store (its currency)",
        writes="nothing without `--write`. With it: "
               "`config/manual/drafts/<TICKER>.llm-pdf.yaml` and its run "
               "record. Never the live store",
        network="OpenRouter (the model reads the statement pages twice)",
        sends="nothing",
        exits="`0` read; `2` no `--currency` and no live store to take it from",
        safe="without `--write` (the model is still called)"),
    "esef": Facts(
        "Read a Nordic issuer's ESEF report packages; `--draft` writes a DRAFT",
        (RECORD,),
        reads="the ESEF report packages (`.zip`) under `sources/`; "
              "`config/mfn_entities.yaml` (the LEI)",
        writes="nothing without `--draft`. With it: "
               "`config/manual/drafts/<TICKER>.esef-ixbrl.yaml`. Never the "
               "live store",
        network="none",
        sends="nothing",
        exits="`0` read; `1` no readable package in `sources/`",
        safe="`vss esef --ticker X`"),
    "appendix": Facts(
        "Read an issuer's figures workbook (xlsx) through a committed cell map",
        (RECORD,),
        reads="the workbook; `config/manual/maps/<TICKER>.yaml`",
        writes="nothing without `--write`. With it: "
               "`config/manual/<TICKER>.yaml` -- refused where the file "
               "exists unless `--force`, which backs it up first",
        network="none",
        sends="nothing",
        exits="`0` emitted; `1` the emitted file does not validate; `2` the "
              "map is missing or a label does not match",
        safe="without `--write`"),
    "nordic": Facts(
        "List and download reports from the Nordic exchange feed (Oslo: NewsWeb)",
        (RECORD,),
        reads="`config/nordic_issuers.yaml` (`config/oslo_issuers.yaml` for "
              "a `.OL` ticker); `sources/manifest.json`",
        writes="nothing when listing. With `--download`: the document under "
               "`sources/` and its `sources/manifest.json` entry. With "
               "`--resolve --write`: the issuer file, backed up first",
        network="the Nasdaq Nordic disclosure feed; Euronext Oslo NewsWeb "
                "for `.OL`",
        sends="nothing",
        exits="`0` done; `1` `--resolve` found no candidate",
        safe="`vss nordic --ticker X` and `--reports` (a listing)"),
    "watch": Facts(
        "Tell the phone when a watched name files a report, a guidance change or a warning",
        (LOCAL, SENDS),
        reads="`config/watchlist.yaml`; `config/nordic_issuers.yaml`; "
              "`data/watch_state.json`",
        writes="`data/watch_state.json` -- the cursor is advanced EVEN WITH "
               "`--no-send`; with `--read` also `data/autoread/`",
        network="the Nasdaq Nordic feed; EDGAR (`data.sec.gov`); ntfy; with "
                "`--read` OpenRouter",
        sends="to `VSS_NTFY_URL`: a new periodic report, a guidance change "
              "or a profit warning on a watched name. `--no-send` prints "
              "instead",
        exits="`0`",
        safe="`vss watch --cron` only (prints a crontab line). `--no-send` "
             "sends nothing but still moves the cursor, so the next real "
             "run will not repeat what it showed"),
    "refresh": Facts(
        "On a name's report date: fetch the filing, fill the store, write a report (E92)",
        (RECORD, SENDS),
        reads="`config/watchlist.yaml`; the stores; `data/refresh_state.json`",
        writes="the name's store under `config/manual/` (UNVERIFIED figures); "
               "`reports/REFRESH-<TICKER>-<date>.md`; "
               "`data/refresh_state.json`. Never `fv_base`, `tier`, `mbp`, "
               "`stop_price` or `status`",
        network="EDGAR; the Nordic feeds; OpenRouter",
        sends="nothing itself; the nightly `vss run` sends the NEEDS OWNER "
              "pointer for what a refresh left waiting",
        exits="`0`",
        safe="`vss refresh --due --dry-run`"),
    "doctor": Facts(
        "Can this machine run vss? Checks the install, the settings and the timers",
        (READ_ONLY,),
        reads="the Python environment; `~/.config/vss/vss.env` (mode and "
              "owner); `data/vss.sqlite` opened read-only; the newest "
              "snapshot; the user-level systemd timers (enabled, active); the units' "
              "`WorkingDirectory`",
        writes="nothing",
        network="none",
        sends="nothing",
        exits="`0` every check passed or only warned; `1` any FAIL",
        safe="always"),
    "sales": Facts(
        "Every closed position against the indices since its sale; reconcile fills (E165)",
        (LOCAL, RECORD),
        reads="the `sales:` blocks in `config/watchlist.yaml`; with "
              "`--reconcile` the account export CSV",
        writes="`reports/SALES-RECORD-<date>.md` and `data/cache/`. With "
               "`--reconcile`: `config/sales_reconciled.yaml`, and no prices "
               "are read",
        network="Yahoo (prices and the two indices); none with `--reconcile`",
        sends="nothing",
        exits="`0`; with `--reconcile` `1` on any difference between the "
              "export and the booked fills",
        safe="`vss sales --dry-run`"),
    "newsdrop": Facts(
        "The news-drop screen, shadow mode: large names that fell hard on their own news",
        (LOCAL, SENDS),
        reads="the S&P 500 and Stockholm large-cap lists under "
              "`config/universe/`",
        writes="`data/newsdrop/`; `reports/NEWSDROP-<date>.md`. Never the "
               "watchlist (shadow mode)",
        network="Yahoo (prices); EDGAR and the Nordic feed (the company's "
                "own filings in the window); a news RSS search; ntfy",
        sends="to `NTFY_TOPIC`: one message, only when a name survives the "
              "sorting. `--no-notify` sends nothing",
        exits="`0`",
        safe="none -- `--no-notify` still writes its files"),
    "shadow": Facts(
        "The shadow book: every refusal against the indices since its verdict",
        (LOCAL,),
        reads="`config/shadow_book.csv`",
        writes="`reports/SHADOW-BOOK-<date>.md` and `data/cache/`",
        network="Yahoo (prices, dividends and the two indices)",
        sends="nothing",
        exits="`0`",
        safe="`vss shadow --dry-run`"),
    "overview": Facts(
        "Regenerate `reports/OVERVIEW.html`, the read-only page",
        (LOCAL,),
        reads="`config/`, `reference/` and `data/` (the price cache: it "
              "never fetches)",
        writes="`reports/OVERVIEW.html`, or the `--output` path, and "
               "nothing else",
        network="none",
        sends="nothing",
        exits="`0`",
        safe="`vss overview --output <a scratch path>`"),
    "checkin": Facts(
        "The dead man's switch: is a completed run on record, are the timers alive?",
        (SENDS,),
        reads="`data/vss.sqlite` (the completed runs); the user-level "
              "systemd timers (enabled, active)",
        writes="nothing",
        network="ntfy, and only when something is wrong",
        sends="to `NTFY_TOPIC`: no completed nightly run within the window, "
              "or a timer not enabled and active. Silence when healthy",
        exits="`0` always -- a finding is not an error; a non-zero exit "
              "means the check-in itself is broken",
        safe="`vss checkin --no-send`"),
    "queue": Facts(
        "Every valued name against its lines; read each new report; send only a change",
        (LOCAL, SENDS),
        reads="`config/queue.yaml`; `config/watchlist.yaml`; "
              "`data/queue_state.json`; `data/outlook_state.json`",
        writes="`reports/QUEUE-<date>.md`; `data/queue_state.json`; "
               "`data/outlook_state.json`; `data/autoread/` (each new report "
               "and its reading); `reports/HUVUDLISTA.md`. Never the "
               "watchlist and never `config/queue.yaml`",
        network="Yahoo (prices, quarterly statements); EDGAR and the Nordic "
                "/ Oslo feeds (new reports); a news RSS search (headlines); "
                "OpenRouter (the reading); ntfy",
        sends="to `NTFY_TOPIC`, one message and only on a CHANGE: `UNDER "
              "MBP`, `TITTA`, `SÄLJ`, `SPÄRR`, `UTSIKT`, `RÄTTELSE`, "
              "`RAPPORTKONTROLL FELADE`; weekly while it lasts: `STORLEK` "
              "and `SÄLJ EJ UTFÖRD`",
        exits="`0`",
        safe="`vss queue --dry-run` writes no report and no state and sends "
             "nothing. One thing it still does: a NEW report found for a "
             "name is fetched into `data/autoread/` and read (the model is "
             "called), and the real run will read it again"),
    "backfill-vendor-strings": Facts(
        "Seed the database with the vendor's sector strings (once per machine)",
        (LOCAL,),
        reads="every `fundamentals.sqlite` under `data/screener_snapshots/`",
        writes="`data/vss.sqlite` (the vendor's sector and industry "
               "strings). Idempotent",
        network="none",
        sends="nothing",
        exits="`0`"),
    "reference-figures": Facts(
        "Fetch the issuer's own free cash flow and net debt as reference figures (E103)",
        (RECORD,),
        reads="the stores under `config/manual/`",
        writes="nothing without `--write`. With it: the issuer's own free "
               "cash flow and net debt into the store as UNVERIFIED "
               "REFERENCE figures; `--confirm --write` withdraws a figure "
               "two readings do not agree on",
        network="EDGAR; OpenRouter",
        sends="nothing",
        exits="`0`",
        safe="without `--write` (the plan is printed; the model is still "
             "called)"),
    "briefing": Facts(
        "Assemble the research a reading stands on; no judgement, no value",
        (LOCAL,),
        reads="`config/watchlist.yaml`; the name's store",
        writes="nothing without `--write`. With it: "
               "`reports/BRIEFING-<TICKER>-<date>.md`",
        network="EDGAR; OpenRouter with web search unless `--no-web`",
        sends="nothing",
        exits="`0` assembled; `2` no CIK, no complete store, or the "
              "briefing refused itself (it carried a judgement)",
        safe="without `--write`"),
    "prepare": Facts(
        "Everything the machine can do before a review, ending in a readiness report",
        (LOCAL, RECORD),
        reads="`config/watchlist.yaml`; the stores; `sources/`",
        writes="`reports/prepare/<TICKER>-<date>.{json,md}`; stores under "
               "`config/manual/` (backed up first); documents under "
               "`sources/`. Never the watchlist",
        network="EDGAR; the Nordic feeds; OpenRouter",
        sends="nothing",
        exits="`0` ready; `1` at least one name is blocked on a step the "
              "machine could not do",
        safe="`vss prepare --ticker X --dry-run`"),
    "strike": Facts(
        "Value one name off its store: run record, strike document, before/after table",
        (RECORD,),
        reads="the store; the watchlist entry's registered `growth:` view; "
              "`config/history/<TICKER>.yaml`; the previous run record; "
              "`data/vss.sqlite` (the tier in force, for the memo column)",
        writes="`reference/run-records/<TICKER>-<stamp>.json` and "
               "`reference/<TICKER>-STRIKE-<stamp>.md`. Never the watchlist: "
               "`fv_base`, `tier`, `mbp`, `stop_price` and `status` stay "
               "the owner's act",
        network="none",
        sends="nothing",
        exits="`0` struck; `2` REFUSED, and nothing was written: no store, "
              "no registered growth view, an events ledger dated more than "
              "seven days ago (E140(4): search the news and the filings "
              "again, then date it), or the section 5 gate refuses and "
              "`--ignore-gate` was not given",
        safe="`vss strike --ticker X --dry-run`"),
    "history": Facts(
        "Build, check or print the issuer's multi-year history (E143)",
        (RECORD,),
        reads="`config/history/<TICKER>.yaml`; with `--esef` the report "
              "packages under `sources/`; with `--check` the PDFs the rows cite",
        writes="nothing without `--write`. With `--xbrl --write` or `--esef "
               "--write`: `config/history/<TICKER>.yaml`",
        network="`data.sec.gov` with `--xbrl`; otherwise none",
        sends="nothing",
        exits="`0`; `1` `--check` found a row that does not stand in its "
              "PDF; `2` no history file, or no CIK for `--xbrl`",
        safe="`vss history --ticker X` (prints what E142 / E144 / E145 "
             "derive)"),
    "review": Facts(
        "Validate or record a review session's file; print the review schema",
        (WATCHLIST,),
        reads="the review file under `reference/reviews/<TICKER>/`; "
              "`config/watchlist.yaml`",
        writes="nothing with `--validate` or `--schema`. With `--record`: "
               "the owner's note appended verbatim to the entry's `notes` "
               "(backup first) and the growth view registered; the file is "
               "re-read afterwards and restored if anything else moved. "
               "Never `status`, `fv_base`, `tier`, `mbp` or `stop_price`",
        network="none",
        sends="nothing",
        exits="`0` valid (or recorded); `2` a refusal -- every one is printed",
        safe="`vss review --validate <file>`; `--schema`; `--record <file> "
             "--dry-run`"),
    "screen": Facts(
        "The screener: universe, snapshot, filters, seeded order; `--weekly` for the chain",
        (LOCAL, WATCHLIST, SENDS),
        reads="`config/universe/`; `config/screener_exclusions.csv`; "
              "`config/screener_filter2.yaml`; the stored snapshots",
        writes="`data/screener_snapshots/<asof>/`; "
               "`data/screener_runs/<asof>/` (`filter1-candidates.csv`, "
               "`ranking.csv`, `ranking-manifest.json`); with `--weekly` "
               "also `reports/SCREEN-<date>.md` and the ranked order in "
               "`data/vss.sqlite`. ONLY `--rank --write-pipeline` writes "
               "`config/watchlist.yaml`: new PIPELINE entries, backup first, "
               "never an existing entry",
        network="Yahoo (prices, fundamentals, exchange rates); "
                "`data.sec.gov` with `--sec-shadow` and `--weekly`; ntfy "
                "with `--weekly`",
        sends="`--weekly` posts a pointer to `NTFY_TOPIC` when the first "
              "ten changed; `--no-notify` sends nothing",
        exits="`0`; `2` a universe file is malformed, no step flag was "
              "given, or the newest stored snapshot is older than `--asof`",
        safe="`--universe-report`, `--filter1` and `--filter2` fetch "
             "nothing and write only under `data/screener_runs/`; "
             "`--write-pipeline --dry-run` shows what would be entered"),
}

TOOLS: dict[str, Facts] = {
    "warren.py": Facts(
        "Quality tests and the method's value for any US filer, straight from EDGAR; a screen",
        (READ_ONLY,),
        reads="nothing on disk", writes="nothing",
        network="`data.sec.gov`; Yahoo (the price)",
        sends="nothing", safe="always"),
    "rough_fv.py": Facts(
        "Rough bear / base / bull for any listing Yahoo covers; a screen, not a strike",
        (READ_ONLY,),
        reads="nothing on disk", writes="nothing",
        network="Yahoo (statements, price, exchange rate)",
        sends="nothing", safe="always"),
    "build_queue.py": Facts(
        "Rebuild `config/queue.yaml` from the newest strikes, keeping hand fields",
        (RECORD,),
        reads="`reference/<TICKER>-STRIKE-*.md`; `config/watchlist.yaml`; "
              "the existing `config/queue.yaml`",
        writes="nothing without `--write`. With it: `config/queue.yaml`",
        network="none", sends="nothing", safe="without `--write`"),
    "master_list.py": Facts(
        "The master list: every company looked at, on one page",
        (LOCAL,),
        reads="`config/watchlist.yaml`; `config/queue.yaml`; "
              "`data/queue_state.json`; `config/shadow_book.csv`; "
              "`reference/screens/*.yaml` where present",
        writes="`reports/HUVUDLISTA.md`; nothing with `--short`",
        network="none", sends="nothing", safe="`--short`"),
    "quotecheck.py": Facts(
        "The mechanical read-back: does each figure's quote stand in its document?",
        (RECORD,),
        reads="every store under `config/manual/` and the documents under "
              "`sources/` they cite",
        writes="nothing without `--apply`. With `--apply X`: `status: "
               "VERIFIED` on X's passing UNVERIFIED figures (E131), never "
               "on a figure whose line a machine chose (E149)",
        network="none", sends="nothing", safe="without `--apply`"),
    "cross_verify.py": Facts(
        "Verify a machine-read figure by a second, independent reading (E151)",
        (LOCAL, RECORD),
        reads="the stores; the PDFs under `sources/`; `data/cross-verify/` "
              "(cached readings)",
        writes="`data/cross-verify/`. With `--apply`: `status: VERIFIED` "
               "(`two_source`) where a second, independent reading prints "
               "the same digits. The value is never changed",
        network="OpenRouter", sends="nothing", safe="without `--apply`"),
    "rule_impact.py": Facts(
        "What a rule change does to every name: save a snapshot, then diff",
        (LOCAL,),
        reads="every store, history and run record (it re-values every name)",
        writes="`--save PATH` writes the snapshot file; `--diff PATH` "
               "writes nothing",
        network="none", sends="nothing", safe="`--diff PATH`"),
    "fetch_mfn.py": Facts(
        "Fetch Nordic report PDFs and ESEF packages from MFN's public feed",
        (RECORD,),
        reads="`config/queue.yaml` with `--queue`; "
              "`config/mfn_entities.yaml`; `sources/manifest.json`",
        writes="report PDFs and ESEF packages under `sources/`; "
               "`sources/manifest.json`; `config/mfn_entities.yaml` (the "
               "ticker-to-issuer mapping and the LEI)",
        network="`mfn.se` (public feed, no login)",
        sends="nothing",
        exits="`0`; `1` a file on disk differs from the feed's bytes",
        safe="`--dry-run`"),
    "build_universe.py": Facts(
        "Build the static, dated universe lists under `config/universe/`",
        (RECORD,),
        reads="the exchanges' and index providers' published lists",
        writes="the dated CSVs under `config/universe/` (or `--out`)",
        network="the list providers", sends="nothing"),
    "seed_fields_history.py": Facts(
        "Seed the point-in-time fields history from the VERIFIED stores",
        (LOCAL,),
        reads="the VERIFIED figures in the stores; `sources/manifest.json`",
        writes="nothing without `--write`. With it: appends to "
               "`fundamentals_fields_history` in `data/vss.sqlite`",
        network="none", sends="nothing", safe="without `--write`"),
    "fetch_fx_manifest.py": Facts(
        "Build tool: fetch the exchange rates of a named date for a replay",
        (LOCAL,),
        reads="a stored ranking manifest (its pair list only)",
        writes="the `--out` manifest", network="Yahoo (exchange rates)",
        sends="nothing"),
    "freeze_ranking_acceptance.py": Facts(
        "Build tool: freeze the ranking acceptance fixture (vendor data)",
        (RECORD,),
        reads="a stored screener run under `data/`",
        writes="`tests/fixtures/ranking-acceptance/` (vendor data: never "
               "published)",
        network="none", sends="nothing"),
    "replay_e166.py": Facts(
        "A dated one-off: replay the US records with working capital tied (E166)",
        (RECORD,),
        reads="each US queue name's latest run record and its store",
        writes="nothing without `--write`. With it: new records under "
               "`reference/run-records/`",
        network="none", sends="nothing", safe="without `--write`"),
    "fetch_eodhd.py": Facts(
        "Fetch EODHD statements under your own licence (private, never published)",
        (LOCAL,),
        reads="`~/.config/eodhd/env` (`EODHD_API_KEY`); "
              "`data/eodhd/symbols.csv`",
        writes="`data/eodhd/fundamentals/` -- licensed vendor data, private, "
               "never published",
        network="EODHD (your own licence)", sends="nothing",
        safe="`--check`, `--status`"),
    "eodhd_pit.py": Facts(
        "Index when each EODHD period became known (point in time)",
        (LOCAL,),
        reads="`data/eodhd/fundamentals/`",
        writes="`data/eodhd/pit.sqlite` with `--build`; nothing with `--show`",
        network="none", sends="nothing", safe="`--show SYMBOL ASOF`"),
    "nordic_screen.py": Facts(
        "The weekly Nordic screen on EODHD data: value and rank every active name",
        (LOCAL, SENDS),
        reads="`data/eodhd/` (your own licence)",
        writes="`data/nordic-screen/`; `reports/NORDIC-SCREEN-<date>.md`",
        network="EODHD unless `--no-refresh`; Yahoo (prices); ntfy with "
                "`--notify`",
        sends="with `--notify`: the summary to `NTFY_TOPIC`",
        safe="none -- `--no-refresh` without `--notify` fetches nothing "
             "from the vendor and sends nothing, but writes its report"),
    "build_manual_reference.py": Facts(
        "Print this page as the code defines it",
        (READ_ONLY,),
        reads="the parsers, `deploy/` and this file's tables",
        writes="nothing: it prints, and the caller redirects into "
               "`docs/REFERENCE.md`",
        network="none", sends="nothing", safe="always"),
    "fetch_test_fixtures.py": Facts(
        "Fetch the Yahoo price fixtures the tests read (not shipped)",
        (LOCAL,),
        reads="`tests/fixtures/VENDOR-DATA.json`",
        writes="the price fixtures the tests read, under `tests/fixtures/` "
               "(not shipped: the vendor's terms allow personal use only)",
        network="Yahoo", sends="nothing", optional=True),
}

#: (variable, read by, meaning). Read from the environment first, then from
#: ~/.config/vss/vss.env (vss/env.py); the environment wins.
ENV = (
    ("VSS_SEC_CONTACT", "`xbrl`, `history --xbrl`, `watch`, `queue`, "
     "`briefing`, `refresh`, `prepare`, `newsdrop`, `tools/warren.py`",
     "The contact address SEC asks every automated caller to declare, e.g. "
     "`yourtool/1.0 (you@example.com)`. Without it SEC is not called"),
    ("VSS_OPENROUTER_KEY", "`earnings`, `pdfdraft`, `briefing`, "
     "`reference-figures`, `prepare`, `refresh`, `watch --read`, `queue`, "
     "`tools/cross_verify.py`",
     "The model key. Never in the repository. Without it a reading says so "
     "and nothing is guessed"),
    ("VSS_OPENROUTER_MODEL", "the same", "Optional: the model id. Defaults "
     "to the one named in `vss/extract.py`"),
    ("NTFY_TOPIC", "`run`, `queue`, `checkin`, `newsdrop`, `screen "
     "--weekly`, `tools/nordic_screen.py --notify`",
     "Where pointers are POSTed. A bare topic name is completed to "
     "`https://ntfy.sh/<topic>`; a full URL is used as given. Unset is "
     "silence, not an error. Outbound only"),
    ("VSS_NTFY_URL", "`watch`", "`vss watch`'s own topic URL, separate on "
     "purpose: a disclosure alert is not a refresh pointer"),
    ("HEALTHCHECK_URL", "`deploy/vss-ping-healthcheck.sh`",
     "A healthchecks.io ping URL, fetched only after a nightly run that "
     "SUCCEEDED: the one alarm a powered-off machine can still raise"),
    ("EODHD_API_KEY", "`tools/fetch_eodhd.py`, `tools/nordic_screen.py`",
     "Your own EODHD licence, in `~/.config/eodhd/env` (mode 600). Only the "
     "Nordic screen and the backtests need it"),
    ("BT_WORKERS", "`tools/backtest/`", "Optional: how many processes a "
     "backtest uses"),
)

#: (path, written by, what it is). Tracked = in git; the rest is gitignored.
FILES = (
    ("config/watchlist.yaml", "the owner by hand; `screen --rank "
     "--write-pipeline` (new PIPELINE entries); `review --record` (a note)",
     "TRACKED. One entry per name: status, `fv_base`, `tier`, notes, "
     "hand-entered quarters. Every field is manual; `mbp` is computed and "
     "may not be written"),
    ("config/queue.yaml", "`tools/build_queue.py --write`; hand fields by "
     "the owner",
     "TRACKED. Every valued name with bear / base / bull, its kind "
     "(`strike`, `machine`, `rough`), tier, gate and the hand fields "
     "`sell_at`, `look_at`, `note`, `exit_pending`, `override`; "
     "`portfolio_sek` for the 6 % size ceiling"),
    ("config/manual/<TICKER>.yaml", "`xbrl --annual --write`, `appendix "
     "--write`, `manual --merge-draft`, `refresh`, `prepare`, by hand",
     "TRACKED. The store: every figure with its source, page and status "
     "(`UNVERIFIED` / `VERIFIED`)"),
    ("config/manual/drafts/", "`esef --draft`, `pdfdraft --write`",
     "TRACKED. Machine pre-fills, every figure UNVERIFIED; never read as "
     "the store"),
    ("config/history/<TICKER>.yaml", "`history --xbrl --write`, `history "
     "--esef --write`, by hand",
     "TRACKED. The issuer's multi-year history E142-E145 read"),
    ("config/shadow_book.csv", "by hand", "TRACKED. One row per refusal, "
     "nine columns"),
    ("config/sales_reconciled.yaml", "`sales --reconcile`",
     "TRACKED. The booked fills matched against the account export (E165)"),
    ("config/universe/", "`tools/build_universe.py`",
     "TRACKED. Static, dated constituent lists; never fetched at run time"),
    ("reference/run-records/", "`strike`", "TRACKED. Every input and every "
     "choice of a valuation; a value with no record is not a value"),
    ("reference/<TICKER>-STRIKE-<stamp>.md", "`strike`",
     "TRACKED. The strike document: the before/after table and the waterfall"),
    ("reference/reviews/<TICKER>/", "the `/review` session",
     "TRACKED. One review file per session, validated by `review --validate`"),
    ("sources/", "`nordic --download`, `tools/fetch_mfn.py`, `prepare`",
     "The documents themselves are gitignored (large, re-downloadable); "
     "`sources/manifest.json` is TRACKED: URL, SHA-256, bytes and fetch "
     "time per file"),
    ("reports/<date>.md", "`run`", "The nightly report"),
    ("reports/OVERVIEW.html", "`run` (full runs), `overview`",
     "The read-only page: one file, no script"),
    ("reports/QUEUE-<date>.md", "`queue`", "The night's queue table"),
    ("reports/HUVUDLISTA.md", "`queue`, `tools/master_list.py`",
     "The master list: every company looked at, in five groups"),
    ("reports/SCREEN-<date>.md", "`screen --weekly`", "The weekly screen"),
    ("reports/NEWSDROP-<date>.md", "`newsdrop`", "The news-drop screen "
     "(shadow)"),
    ("reports/SALES-RECORD-<date>.md", "`sales`", "Every closed position "
     "against the indices"),
    ("reports/SHADOW-BOOK-<date>.md", "`shadow`", "Every refusal against "
     "the indices"),
    ("reports/REFRESH-<TICKER>-<date>.md", "`refresh`", "What a report-date "
     "refresh fetched and left for the owner"),
    ("reports/BRIEFING-<TICKER>-<date>.md", "`briefing --write`",
     "Research for a reading; carries no judgement"),
    ("reports/prepare/", "`prepare`", "Readiness reports, json and md"),
    ("data/vss.sqlite", "`run`, `earnings`, `screen --weekly`, "
     "`backfill-vendor-strings`, `tools/seed_fields_history.py`",
     "Tables `runs`, `run_metrics` (one row per ticker per run), "
     "`earnings_runs`, the stored rankings, the vendor strings, "
     "`fundamentals_fields_history`. New columns arrive by a migration on "
     "connect"),
    ("data/cache/", "`run`, `sales`, `shadow`", "Daily prices per ticker, "
     "CSV plus a JSON sidecar"),
    ("data/queue_state.json", "`queue`", "Which zone each name was in last "
     "night, so a change is said once; the last closes"),
    ("data/outlook_state.json", "`queue`", "Each name's last four-quarter "
     "value and the reports and headlines already handled"),
    ("data/autoread/", "`queue`, `watch --read`", "Every fetched report and "
     "its reading (two runs, compared). Shadow: nothing here is sent"),
    ("data/watch_state.json", "`watch`", "The disclosure cursor per name"),
    ("data/refresh_state.json", "`refresh`", "What each refresh fetched and "
     "what waits for the owner"),
    ("data/pricewatch_state.json", "`run`", "The ranked watch's crossings "
     "(E97), so each is said once"),
    ("data/block_push_state.json", "`run`", "Whether last night's blocked-"
     "level push went, and each name's streak"),
    ("data/screener_snapshots/<asof>/", "`screen`", "Raw daily OHLCV for "
     "the whole universe, plus `fundamentals.sqlite`"),
    ("data/screener_runs/<asof>/", "`screen`", "`filter1-candidates.csv`, "
     "`ranking.csv`, `ranking-manifest.json`"),
    ("data/sec-cache/", "`screen --rank --sec-shadow`, `screen --weekly`",
     "SEC companyfacts as fetched"),
    ("data/newsdrop/", "`newsdrop`", "The screen's own files"),
    ("data/cross-verify/", "`tools/cross_verify.py`", "Cached second "
     "readings"),
    ("data/eodhd/", "`tools/fetch_eodhd.py`, `tools/eodhd_pit.py`",
     "Licensed vendor data under your own licence; never published"),
)


# --------------------------------------------------------------------------
# reading the parsers


def _cell(text: str | None) -> str:
    """One table cell: single line, pipes escaped, `<x>` kept visible.

    Angle brackets outside a code span would be read as HTML and vanish
    from the rendered page, so they are escaped there and only there.
    """
    text = " ".join((text or "").split())
    parts = text.split("`")
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].replace("<", "&lt;").replace(">", "&gt;")
    return "`".join(parts).replace("|", "\\|")


def _help(parser: argparse.ArgumentParser, action: argparse.Action) -> str:
    if not action.help or action.help is argparse.SUPPRESS:
        return ""
    params = dict(vars(action), prog=parser.prog)
    for key, value in list(params.items()):
        if value is argparse.SUPPRESS:
            del params[key]
    try:
        text = action.help % params
    except (KeyError, TypeError, ValueError):
        text = action.help
    return text.replace(str(ROOT), ".")


def _value(action: argparse.Action) -> str:
    if action.nargs == 0:
        return ""
    if action.metavar is not None:
        meta = (" ".join(action.metavar) if isinstance(action.metavar, tuple)
                else str(action.metavar))
    elif action.choices is not None:
        meta = "|".join(str(c) for c in action.choices)
    elif action.option_strings:
        meta = action.dest.upper()
    else:
        meta = action.dest
    if action.nargs in ("+", "*"):
        meta += " ..."
    return meta


def _flag(action: argparse.Action) -> str:
    if not action.option_strings:
        return f"`{_value(action)}`"
    longs = [s for s in action.option_strings if s.startswith("--")]
    name = " / ".join(longs or action.option_strings)
    value = _value(action)
    return f"`{name} {value}`" if value else f"`{name}`"


def flag_rows(parser: argparse.ArgumentParser) -> list[tuple[str, str]]:
    """(flag, meaning) per argument, in the parser's own order."""
    exclusive = {}
    for group in parser._mutually_exclusive_groups:
        names = [_flag(a) for a in group._group_actions]
        for action in group._group_actions:
            others = [n for n in names if n != _flag(action)]
            exclusive[id(action)] = (others, group.required)
    rows = []
    for action in parser._actions:
        if isinstance(action, (argparse._HelpAction,
                               argparse._SubParsersAction)):
            continue
        notes = []
        if action.required and action.option_strings:
            notes.append("REQUIRED")
        if id(action) in exclusive:
            others, required = exclusive[id(action)]
            notes.append(("one of these is required: " if required
                          else "not together with ") + ", ".join(others))
        text = _help(parser, action)
        if notes:
            text = (text + " " if text else "") + "(" + "; ".join(notes) + ")"
        rows.append((_flag(action), text))
    return rows


def vss_commands() -> list[tuple[str, str, argparse.ArgumentParser]]:
    """(name, help, parser) per subcommand, in the order the CLI defines."""
    from vss.__main__ import build_parser

    parser = build_parser()
    sub = next(a for a in parser._actions
               if isinstance(a, argparse._SubParsersAction))
    helps = {c.dest: c.help or "" for c in sub._choices_actions}
    return [(name, helps.get(name, "").replace("%%", "%"), p)
            for name, p in sub.choices.items()]


def tool_files() -> list[Path]:
    return sorted(p for p in (ROOT / "tools").glob("*.py")
                  if p.name != "__init__.py")


def _load(path: Path):
    name = f"_tool_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # registered before it runs: a dataclass under `from __future__ import
    # annotations` looks its own module up in sys.modules
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def tool_parser(path: Path) -> argparse.ArgumentParser | None:
    """The tool's own parser, or None where it takes no arguments."""
    if "def build_parser" not in path.read_text(encoding="utf-8"):
        return None
    parser = _load(path).build_parser()
    parser.prog = f"tools/{path.name}"
    return parser


def _docline(path: Path, limit: int = 170) -> str:
    """The first sentence of a module's docstring, cut at a word."""
    doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    first = " ".join(doc.split("\n\n")[0].split())
    cut = re.search(r"(?<=[a-z0-9)\]`'\"])\.(?=\s|$)", first)
    first = (first[:cut.start()] if cut else first).strip().rstrip(".")
    if len(first) > limit:
        first = first[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-") + " ..."
    return first


# --------------------------------------------------------------------------
# reading deploy/

_PY = re.compile(r"\S*/\.venv/bin/python")
_DEPLOY = re.compile(r"\S*/deploy/")


def _command(line: str) -> str:
    line = line.split("=", 1)[1].lstrip("-")
    line = _DEPLOY.sub("deploy/", _PY.sub(".venv/bin/python", line))
    return line if len(line) <= 96 else line[:93].rstrip() + "..."


def timers() -> list[tuple[str, str, list[str], bool]]:
    """(unit, when, commands, has a failure hook) per timer, off deploy/."""
    out = []
    for timer in sorted((ROOT / "deploy").glob("*.timer")):
        when = [line.split("=", 1)[1].strip()
                for line in timer.read_text(encoding="utf-8").splitlines()
                if line.startswith("OnCalendar=")]
        service = timer.with_suffix(".service")
        unit = service.read_text(encoding="utf-8").splitlines()
        commands = [_command(line) for line in unit
                    if line.startswith(("ExecStart=", "ExecStartPost="))]
        hooked = any(line.startswith("OnFailure=vss-failure@") for line in unit)
        out.append((timer.name, "; ".join(when), commands, hooked))
    return out


# --------------------------------------------------------------------------
# the page


def _facts_block(facts: Facts, default_exits: str = GENERAL_EXITS) -> list[str]:
    rows = [("Reads", facts.reads), ("Writes", facts.writes),
            ("Network", facts.network), ("Sends", facts.sends),
            ("Exit codes", facts.exits or default_exits)]
    if facts.safe:
        rows.append(("Changes nothing", facts.safe))
    out = ["| | |", "|---|---|"]
    out += [f"| **{k}** | {_cell(v)} |" for k, v in rows]
    return out


def _flags_block(parser: argparse.ArgumentParser | None) -> list[str]:
    rows = flag_rows(parser) if parser is not None else []
    if not rows:
        return ["No arguments.", ""]
    out = ["| Argument | Meaning |", "|---|---|"]
    out += [f"| {flag} | {_cell(text)} |" for flag, text in rows]
    return out + [""]


def _anchor(text: str) -> str:
    return re.sub(r"[^a-z0-9_ -]", "", text.lower()).replace(" ", "-")


def render() -> str:
    out = [
        "# vss -- command reference",
        "",
        "<!-- GENERATED by tools/build_manual_reference.py. Do not edit by "
        "hand:",
        "     change the parser, the timer or the tool's tables, then run",
        "     .venv/bin/python tools/build_manual_reference.py > "
        "docs/REFERENCE.md",
        "     tests/test_manual_reference.py holds this file equal to the "
        "code. -->",
        "",
        "Every command, every flag, what it reads, writes, calls and sends. "
        "The flags are read off the argument parsers and the timers off "
        "`deploy/`, and a test fails when this page and the code differ. "
        "How to *use* the commands is in [the manual](MANUAL.md).",
        "",
        "Run everything from the repository root:",
        "",
        "```bash",
        ".venv/bin/python -m vss <command> [flags]",
        ".venv/bin/python tools/<tool>.py [flags]",
        "```",
        "",
        "## What a command may touch",
        "",
        "| Class | Meaning |",
        "|---|---|",
    ]
    out += [f"| `{name}` | {_cell(meaning)} |" for name, meaning in CLASS_MEANING]
    out += [
        "",
        "A command carries every class that applies to any of its forms. "
        "**Changes nothing** names the form that writes no file and sends "
        "nothing; where a command has none, the row says so.",
        "",
        "Unless a command's table says otherwise its exit codes are: "
        + GENERAL_EXITS + ".",
        "",
        "## Commands at a glance",
        "",
        "| Command | Class | What it does |",
        "|---|---|---|",
    ]
    commands = vss_commands()
    for name, text, _ in commands:
        facts = COMMANDS[name]
        out.append(f"| [`vss {name}`](#{_anchor('vss ' + name)}) "
                   f"| {', '.join(facts.classes)} | {_cell(facts.what)} |")
    out += ["", "## Tools at a glance", "",
            "| Tool | Class | What it does |", "|---|---|---|"]
    tools = [(p, TOOLS[p.name]) for p in tool_files()]
    for path, facts in tools:
        out.append(f"| [`tools/{path.name}`](#{_anchor('tools' + path.name)}) "
                   f"| {', '.join(facts.classes)} | {_cell(facts.what)} |")
    out.append("")

    out += ["## The `vss` commands", ""]
    for name, text, parser in commands:
        out += [f"### `vss {name}`", "", _cell(COMMANDS[name].what) + ".", "",
                "> " + _cell(text).rstrip(".") + ".", ""]
        out += _flags_block(parser)
        out += _facts_block(COMMANDS[name])
        out.append("")

    out += ["## The tools", "",
            "Scripts under `tools/`. They are not part of the nightly "
            "contract unless a timer below names them.", ""]
    for path, facts in tools:
        out += [f"### `tools/{path.name}`", "", _cell(facts.what) + ".", ""]
        out += _flags_block(tool_parser(path))
        out += _facts_block(facts, default_exits="`0` completed")
        out.append("")

    out += ["## The backtests", "",
            "Modules under `tools/backtest/` and `tools/newsdrop/`, run as "
            "`.venv/bin/python -m tools.backtest.<name>`. They read licensed "
            "vendor data that you fetch under your own licence "
            "(`tools/fetch_eodhd.py`); none of it, and nothing computed "
            "from it, is in the repository. Every run is registered in "
            "`reference/backtest/ATTEMPTS.md` before it starts (E164).", "",
            "| Module | What it is |", "|---|---|"]
    for folder in ("backtest", "newsdrop"):
        for path in sorted((ROOT / "tools" / folder).glob("*.py")):
            if path.name == "__init__.py":
                continue
            out.append(f"| `tools.{folder}.{path.stem}` | {_cell(_docline(path))} |")
    out.append("")

    out += ["## Modules", "",
            "Every module under `vss/`, with the opening of its own "
            "docstring. `rules.py` and `valuation.py` are pure: no I/O and "
            "no clock, `as_of` is always passed in. `runner.py` holds the "
            "nightly run's I/O; `pipeline.py` and `review.py` are the only "
            "modules that write the watchlist.", "",
            "| Module | What it is |", "|---|---|"]
    for path in sorted((ROOT / "vss").glob("*.py")):
        if path.name == "__init__.py":
            continue
        out.append(f"| `vss/{path.name}` | {_cell(_docline(path))} |")
    out.append("")

    out += ["## Timers", "",
            "User-level systemd units under `deploy/`, read off the files. "
            "Times are the machine's local time unless the expression says "
            "UTC. **Failure hook** says whether the service names "
            "`vss-failure@.service` as its `OnFailure=`, which posts to "
            "`NTFY_TOPIC` that the unit failed. `vss-overview.service` has "
            "no timer: it serves `reports/OVERVIEW.html` on loopback.", "",
            "| Timer | When (`OnCalendar`) | Runs | Failure hook |",
            "|---|---|---|---|"]
    for unit, when, commands_, hooked in timers():
        runs = "<br>then ".join(f"`{c}`" for c in commands_)
        out.append(f"| `{unit}` | `{when}` | {runs} | {'yes' if hooked else 'no'} |")
    out.append("")

    out += ["## Environment variables", "",
            "Read from the environment first, then from "
            "`~/.config/vss/vss.env` (`vss/env.py`) -- the file the systemd "
            "units name in `EnvironmentFile=`. The environment wins; the "
            "file is never written, logged or printed.", "",
            "| Variable | Read by | Meaning |", "|---|---|---|"]
    out += [f"| `{name}` | {_cell(by)} | {_cell(meaning)} |"
            for name, by, meaning in ENV]
    out.append("")

    out += ["## Files", "",
            "TRACKED means in git. Everything under `data/` and `reports/` "
            "is gitignored and regenerable.", "",
            "| Path | Written by | What it is |", "|---|---|---|"]
    out += [f"| `{path}` | {_cell(by)} | {_cell(what)} |"
            for path, by, what in FILES]
    out.append("")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Print docs/REFERENCE.md as the code defines it. "
                    "Redirect it into the file; a test holds the two equal.")


def main(argv=None) -> int:
    build_parser().parse_args(argv)
    sys.stdout.write(render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
