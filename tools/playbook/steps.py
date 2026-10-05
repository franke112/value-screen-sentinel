"""The step list: the chain, then the cycle.

A step names WHERE ITS TEXT COMES FROM and nothing else: which FRAMEWORK
sections are quoted, which vss module's docstring, which CLI commands
with which flags, which watchlist status sits here. The wording on the
page is the sources'. The `question` is a template filled with the
section's own heading; it is a prompt to the owner, never an answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

CHAIN = "chain"
CYCLE = "cycle"

#: The seven section-5 and pre-registration steps carry the anchoring
#: guard: no prior fair value, growth view, MBP or tier is shown on them
#: until the CURRENT name's own growth view is registered in the
#: watchlist (a `growth:` block with a `registered` date).
GUARDED = ("basis", "flow", "net-debt", "divisor", "growth-view", "strike", "tier-mbp")


@dataclass
class Step:
    id: str
    title: str
    part: str
    sections: tuple[str, ...] = ()        # FRAMEWORK section keys to quote
    status: str | None = None             # a VALID_STATUSES value that sits here
    modules: tuple[str, ...] = ()         # vss modules whose docstring is quoted
    commands: tuple[tuple[str, str], ...] = ()   # (subcommand, flags shown)
    scripts: str | None = None            # a glob under tools/
    exits: tuple[str, ...] = ()           # step ids a name can leave to from here
    actor: str = "owner"                  # owner | Claude session | LLM extraction | timer
    question: str = ""                    # {section} is the first quoted heading
    files: tuple[str, ...] = ()           # paths the step reads or writes
    units: tuple[str, ...] = ()           # deploy units (cycle steps)

    @property
    def guarded(self) -> bool:
        return self.id in GUARDED


STEPS: list[Step] = [
    Step("screen", "The screen: universe to ranked list", CHAIN,
         sections=("§3", "Gate 1"), modules=("screen", "screenwatch", "pricewatch"),
         commands=(("screen", "--weekly --tier A --tier B"),
                   ("screen", "--universe-report"),
                   ("screen", "--rank --asof YYYY-MM-DD --runs-root PATH"),
                   ("screen", "--rank --write-pipeline --dry-run")),
         exits=("intake", "pipeline"), actor="timer",
         question="Which ranked names does the owner read next, under {section}?",
         files=("config/universe", "config/screener_exclusions.csv", "data/screener_runs", "reports/SCREEN-<date>.md")),
    Step("intake", "INTAKE: read, not watched", CHAIN,
         sections=("§1", "1.1", "1.2"), status="INTAKE", modules=("briefing", "manual", "xbrl", "nordic", "appendix"),
         commands=(("prepare", "--ticker X --dry-run"),
                   ("prepare", "--ticker X"),
                   ("xbrl", "--ticker X --annual --write --quote-currency CCY"),
                   ("nordic", "--ticker X --resolve TEXT"),
                   ("nordic", "--ticker X --download ID --period YYYY-Qn"),
                   ("appendix", "--ticker X --xlsx PATH --write"),
                   ("manual", "--ticker X"),
                   ("reference-figures", "--ticker X --write"),
                   ("briefing", "--ticker X --write")),
         exits=("pipeline", "dropped"), actor="Claude session",
         question="Is the record complete enough that watching this name would be watching something?",
         files=("config/manual/<TICKER>.yaml", "reference/INTAKE-<TICKER>-<date>.md", "reports/BRIEFING-<TICKER>-<date>.md")),
    Step("pipeline", "PIPELINE: entered, Gate 1 frozen", CHAIN,
         sections=("§3",), status="PIPELINE", modules=("pipeline",),
         commands=(("screen", "--rank --write-pipeline --top N"),
                   ("prepare", "--all-pipeline"),
                   ("run", "--ticker X --dry-run")),
         exits=("gate-1", "dropped"),
         question="Does the owner start this name's clock now?",
         files=("config/watchlist.yaml",)),
    Step("gate-1", "Gate 1: dislocation", CHAIN, sections=("Gate 1",),
         commands=(("run", "--ticker X --dry-run"),), exits=("watch-gated", "dropped"),
         question="Does the name pass {section}?"),
    Step("gate-2", "Gate 2: disconnect classification", CHAIN, sections=("Gate 2",),
         exits=("watch-gated", "dropped"),
         question="Which one class does the decline fall into, under {section}?"),
    Step("gate-3", "Gate 3: quality floor", CHAIN, sections=("Gate 3",),
         commands=(("manual", "--ticker X"),), exits=("watch-gated", "dropped"),
         question="Does the name pass {section}?"),
    Step("gate-4", "Gate 4: valuation discount", CHAIN, sections=("Gate 4",),
         exits=("watch-gated", "dropped"),
         question="Can {section} be evaluated for this name at all?"),
    Step("gate-5", "Gate 5: dated catalyst", CHAIN, sections=("Gate 5",),
         commands=(("run", "--ticker X --dry-run"),), exits=("watch-gated", "dropped"),
         question="Is there a dated event within 90 days, under {section}?",
         files=("config/watchlist.yaml",)),
    Step("hard-kills", "§4.1–4.2: the reading and the hard kills", CHAIN,
         sections=("4.1", "4.2"), modules=("earnings",),
         commands=(("earnings", "--ticker X --url URL --compare"),
                   ("earnings", "--ticker X --text-file PATH --period YYYY-Qn")),
         exits=("dropped", "watch-gated"), actor="LLM extraction",
         question="Does any {section} hard kill trip on the issuer's own figures?",
         files=("config/watchlist.yaml (quarters:)", "reports/<TICKER>-reading-<date>.md")),
    Step("conviction", "§4.3–4.4: flags and the conviction score", CHAIN,
         sections=("4.3", "4.4"), exits=("dropped", "watch-gated"),
         question="What is the {section} score, and which flags carry it?"),
    Step("basis", "§5 basis: the store and its verification", CHAIN,
         sections=("§5",), modules=("manual", "refresh"),
         commands=(("manual", "--ticker X --asof YYYY-MM-DD"),
                   ("xbrl", "--ticker X --annual --write"),
                   ("reference-figures", "--ticker X --confirm --write")),
         exits=("dropped",), actor="Claude session",
         question="Is every figure the basis reads VERIFIED, on one twelve-month window?",
         files=("config/manual/<TICKER>.yaml",)),
    Step("flow", "§5 basis: free cash flow (FCF0)", CHAIN, sections=("5.1",),
         commands=(("manual", "--ticker X"),), exits=("dropped",), actor="Claude session",
         question="Which legs form FCF0, and is each one a stated figure?",
         files=("config/manual/<TICKER>.yaml",)),
    Step("net-debt", "§5 basis: net debt", CHAIN, sections=("5.1",),
         commands=(("manual", "--ticker X"),), exits=("dropped",), actor="Claude session",
         question="Which legs form net debt, and is each one a stated figure or a named zero?",
         files=("config/manual/<TICKER>.yaml",)),
    Step("divisor", "§5 basis: the share count", CHAIN, sections=("5.1",),
         commands=(("manual", "--ticker X"),), exits=("dropped",), actor="Claude session",
         question="Which stated count is the divisor, on which basis?",
         files=("config/manual/<TICKER>.yaml",)),
    Step("growth-view", "Pre-registration: the growth view", CHAIN, sections=("5.1",),
         exits=("dropped",),
         question="What are g_bear, g_base and g_bull, with reasons, BEFORE g* is solved?",
         files=("reference/growth-views/<TICKER>.md", "config/watchlist.yaml (growth:)")),
    Step("strike", "§5.1–5.2: the strike (reverse DCF)", CHAIN, sections=("5.1", "5.2"),
         commands=(("manual", "--ticker X"),), scripts="strike_*.py",
         exits=("dropped",), actor="Claude session",
         question="What is fv_base off the pre-registered view, and where does the band sit?",
         files=("reference/<TICKER>-STRIKE-<date>.md", "reference/run-records/<TICKER>-<date>.json")),
    Step("tier-mbp", "§5.3: tier and maximum buy price", CHAIN, sections=("5.3",),
         commands=(("briefing", "--ticker X --write"), ("run", "--ticker X --dry-run")),
         exits=("verdict",),
         question="Which tier, on which score and which reading, and what MBP follows?",
         files=("config/watchlist.yaml (fv_base, tier)",)),
    Step("verdict", "The verdict", CHAIN, sections=("5.3",),
         commands=(("run", "--ticker X --dry-run"), ("shadow", "--dry-run"),
                   ("review", "--validate reference/reviews/<TICKER>/<date>.yaml"),
                   ("review", "--record reference/reviews/<TICKER>/<date>.yaml")),
         exits=("watch-priced", "watch-gated", "entry", "dropped"),
         question="Which status does the owner write, and in which words?",
         files=("config/watchlist.yaml (status, notes)", "config/shadow_book.csv",
                "reference/reviews/<TICKER>/<date>.yaml")),
    Step("watch-priced", "WATCH-PRICED: too expensive, alert at MBP", CHAIN,
         sections=("5.3",), status="WATCH-PRICED", modules=("runner",),
         commands=(("run", ""), ("watch", "--no-send"), ("refresh", "--due --dry-run")),
         exits=("entry", "dropped", "verdict"), actor="timer",
         question="Has the price crossed MBP, and is the strike still current?"),
    Step("watch-gated", "WATCH-GATED: waiting on a named event", CHAIN,
         sections=("5.3",), status="WATCH-GATED",
         commands=(("watch", "--no-send"), ("refresh", "--ticker X")),
         exits=("gate-1", "dropped"), actor="timer",
         question="Has the named information event happened?"),
    Step("entry", "§6–§8: entry timing, sizing, execution", CHAIN,
         sections=("§6", "6.1", "6.2", "6.3", "§7", "§8"),
         commands=(("run", "--ticker X --dry-run"),), exits=("held", "watch-priced"),
         question="Is price at or below MBP with one §6.1 and one §6.2 trigger confirmed?",
         files=("config/watchlist.yaml (stop_price, dd_at_entry)",)),
    Step("held", "HELD: a position, with its stops", CHAIN, sections=("6.4",),
         status="HELD", modules=("runner",),
         commands=(("run", ""), ("refresh", "--due")), exits=("exit",), actor="timer",
         question="Has any {section} stop been hit, or the thesis changed?"),
    Step("exit", "Exit and the sales record", CHAIN, sections=("6.4",),
         commands=(("sales", "--dry-run"),), exits=("dropped",),
         question="Which stop or rule sells, at what fill, and is the fill recorded?",
         files=("config/watchlist.yaml (sales:)", "reports/SALES-RECORD-<date>.md")),
    Step("dropped", "DROPPED: refused, exited or killed", CHAIN, sections=("4.4",),
         status="DROPPED", commands=(("shadow", "--dry-run"),), exits=("shadow-book",),
         question="Is the refusal written in the owner's words, dated, with its reason?"),
    Step("shadow-book", "The shadow book", CHAIN, modules=("shadowbook",),
         commands=(("shadow", ""),), exits=(),
         question="What did the market do after each refusal, and is that read once a year, not as a signal?",
         files=("config/shadow_book.csv", "reports/SHADOW-BOOK-<date>.md")),
    # ---- the cycle ----
    Step("nightly", "Nightly: the watchlist run", CYCLE, sections=("1.2",),
         modules=("runner", "pricewatch"), commands=(("run", ""), ("run", "--dry-run")),
         actor="timer", units=("vss.timer", "vss.service", "vss-failure@.service"),
         question="Did tonight's run complete, and is anything waiting on the owner?",
         files=("reports/<date>.md", "data/vss.sqlite")),
    Step("checkin", "Daily: the dead man's switch", CYCLE, modules=("heartbeat",),
         commands=(("checkin", "--no-send"),), actor="timer",
         units=("vss-checkin.timer", "vss-checkin.service"),
         question="Is a completed run on record, and are the timers enabled?"),
    Step("weekly-screen", "Weekly: the unattended screen", CYCLE, modules=("screenwatch",),
         commands=(("screen", "--weekly --tier A --tier B"), ("screen", "--weekly --no-notify")),
         actor="timer", units=("vss-screen.timer", "vss-screen.service"),
         question="What crossed the top of the ranked list, and does any of it deserve an intake?",
         files=("reports/SCREEN-<date>.md", "data/screener_runs/<date>")),
    Step("disclosure-watch", "Disclosures: reports, guidance, warnings", CYCLE,
         modules=("watch",), commands=(("watch", "--no-send"), ("watch", "--cron")),
         actor="timer", question="Has a watched name filed or warned since the cursor?",
         files=("data/watch_state.json",)),
    Step("refresh", "Report-date refresh", CYCLE, modules=("refresh",),
         commands=(("refresh", "--due"), ("refresh", "--ticker X --dry-run")),
         actor="LLM extraction",
         question="Which names are due, what was fetched, and what now NEEDS OWNER?",
         files=("reports/REFRESH-<TICKER>-<date>.md", "config/manual/<TICKER>.yaml")),
    Step("overview-page", "The overview page", CYCLE, modules=("overview",),
         commands=(("overview", ""),), actor="timer",
         units=("vss-overview.service", "vss-tunnel.service"),
         question="Does the page state its age, and does every row that should be there appear?",
         files=("reports/OVERVIEW.html",)),
    Step("upkeep", "Upkeep: sales record, shadow book, strings", CYCLE,
         modules=("sales", "shadowbook"),
         commands=(("sales", ""), ("shadow", ""), ("backfill-vendor-strings", "")),
         question="Are the two standing records current, and read at their own cadence?",
         files=("reports/SALES-RECORD-<date>.md", "reports/SHADOW-BOOK-<date>.md")),
]

BY_ID: dict[str, Step] = {s.id: s for s in STEPS}
CHAIN_IDS = [s.id for s in STEPS if s.part == CHAIN]
CYCLE_IDS = [s.id for s in STEPS if s.part == CYCLE]


def neighbours(step_id: str) -> tuple[str | None, str | None]:
    ids = CHAIN_IDS if BY_ID[step_id].part == CHAIN else CYCLE_IDS
    i = ids.index(step_id)
    return (ids[i - 1] if i > 0 else None, ids[i + 1] if i + 1 < len(ids) else None)


#: The funnel's rows on the index: a row is one step or a pair shown side
#: by side (the two watch states).
FUNNEL_ROWS: list[tuple[str, ...]] = [
    ("screen",), ("intake",), ("pipeline",),
    ("gate-1", "gate-2", "gate-3", "gate-4", "gate-5"),
    ("hard-kills", "conviction"),
    ("basis", "flow", "net-debt", "divisor"),
    ("growth-view",), ("strike",), ("tier-mbp",), ("verdict",),
    ("watch-gated", "watch-priced"),
    ("entry",), ("held",), ("exit",), ("dropped",), ("shadow-book",),
]
