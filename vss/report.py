"""Markdown report rendering (SCOPE 6).

Section order is fixed: run timestamp + data freshness, BLOCKERS, ACTIONS,
then the full table of every ticker.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Sequence

from .fetch import SOURCE_CACHE, SOURCE_LIVE, SOURCE_NONE
from .rules import (MAX_CLOSE_AGE_TRADING_DAYS,
                    MAX_CLOSE_AGE_TRADING_DAYS_LEVEL, MBP_SUPERSEDED_MARK)
from .valuation import (NON_USD_BIAS_DECLARATION,
                        RATE_REFERENCE_CURRENCY)

DASH = "--"


def _num(value: float | None, dp: int = 2) -> str:
    return DASH if value is None else f"{value:,.{dp}f}"


def _pct(value: float | None, dp: int = 1) -> str:
    return DASH if value is None else f"{value * 100:+.{dp}f}%"


def _pct_abs(value: float | None, dp: int = 1) -> str:
    return DASH if value is None else f"{value * 100:.{dp}f}%"


def _int(value: float | None) -> str:
    return DASH if value is None else f"{value:,.0f}"


def _verdict_text(row) -> str:
    if row.assessment.blocked:
        return "BLOCKED"
    return ", ".join(v.label for v in row.assessment.verdicts)


def _mbp_cell(row) -> str:
    """The mbp as it prints, with E32's mark where it is superseded.

    ONE function for both tables, reading the SAME flag the verdict string
    reads, so the actions table, the full table and the sentence inside a
    verdict can never say different things about one number.
    """
    text = _num(row.assessment.mbp)
    if not row.assessment.mbp_superseded:
        return text
    struck = (row.entry.mbp_basis.struck
              if row.entry.mbp_basis is not None else "date not recorded")
    return f"{text} **{MBP_SUPERSEDED_MARK}** struck {struck}"


def _row_result(row) -> str:
    if row.error and not row.metrics.last_close:
        return "ERROR"
    return _verdict_text(row)


def _retained_mark(r) -> str:
    """E122(e): a close we kept after the vendor dropped or blanked it says
    so wherever it prints -- here, in the push, on the page and in a packet."""
    mark = getattr(r, "retained", None)
    if mark is None:
        return ""
    return f" **RETAINED** (first seen {mark.first_seen.isoformat()})"


def _close_date_cell(m) -> str:
    """The close's date, and whether it had settled when the run read it.

    `?` where the run declared no settlement cutoff -- DATA MISSING about
    the price's standing, which is not the same as a settled close.
    """
    if m.last_close_date is None:
        return DASH
    text = m.last_close_date.isoformat()
    if m.last_close_settled is None:
        return text + " ?"
    return text


#: E37's marker on a fair value struck in a currency the flat rate is not
#: least wrong in. A symbol rather than the sentence, because the sentence
#: is a footnote and a table cell is not the place for it.
NON_USD_MARK = "*"


def _fv_base_cell(entry) -> str:
    """`fv_base`, marked where E37's declaration applies to it."""
    if entry.fv_base is None:
        return DASH
    text = _num(entry.fv_base)
    if (entry.currency or "").strip().upper() != RATE_REFERENCE_CURRENCY:
        text += f" {NON_USD_MARK}"
    return text


def _printed_fv(row) -> float | None:
    """Item 9: the fair value the run may PRINT for this row.

    A row that carries `fv_base` (runner.TickerRow) has already been through
    `recorded_fair_value`; anything else (a test double) falls back to the
    entry's figure.
    """
    if hasattr(row, "fv_base"):
        return row.fv_base
    return row.entry.fv_base


def _fv_cell(row) -> str:
    """The fv_base column: the printed figure, or DATA MISSING with its mark."""
    refused = getattr(row, "fv_refused", None)
    if refused:
        return "**DATA MISSING** (no complete run record)"
    fv = _printed_fv(row)

    class _Entry:  # the formatter wants .fv_base and .currency
        fv_base = fv
        currency = row.entry.currency
    return _fv_base_cell(_Entry)


def _e28_line(rows: list) -> str:
    """Every mbp that prints WITHOUT E32's mark, and what it stands on."""
    from .rules import MBP_TIER_CUSHION_E90
    live = sorted(
        (r.entry.ticker, r.assessment.mbp, r.fv_base, r.entry.tier)
        for r in rows
        if getattr(r, "fv_base", None) is not None
        and r.assessment.mbp is not None and not r.assessment.mbp_superseded)
    if not live:
        return ""
    named = "; ".join(
        f"`{t}` {mbp:.2f} = base-case value {base:.2f} x tier {tier} cushion "
        f"{MBP_TIER_CUSHION_E90[tier]:.2f}" for t, mbp, base, tier in live)
    return (f"*MBP under E90 (BASE-case value x tier cushion; the cushion "
            f"covers model and input error, not scenario risk -- the bear "
            f"and bull values print as information beside every strike): "
            f"{named}. An mbp carrying E32's mark is the superseded "
            f"fv_base x tier.*")


def _run_record_line(rows: list) -> str:
    """Item 9: every fv_base the run REFUSED to print, and why."""
    refused = sorted((r.entry.ticker, r.fv_refused) for r in rows
                     if getattr(r, "fv_refused", None))
    if not refused:
        return ""
    named = "; ".join(f"`{t}` — {why}" for t, why in refused)
    return (f"*Run record (Phase 3, wired to `vss run` in Build 2): a fair "
            f"value is printed only from a complete section 5 run record "
            f"that replays to it. NOT PRINTED: {named}.*")


def _rate_declaration_line(rows: list) -> str:
    """E37: printed beside every non-USD fair value, and named per ticker."""
    marked = sorted({r.entry.ticker for r in rows
                     if _printed_fv(r) is not None
                     and (r.entry.currency or "").strip().upper()
                     != RATE_REFERENCE_CURRENCY})
    if not marked:
        return ""
    names = ", ".join(f"`{t}`" for t in marked)
    return (f"*{NON_USD_MARK} {NON_USD_BIAS_DECLARATION} — {names}. E37: a "
            f"single nominal rate is a HIGHER REAL hurdle for a "
            f"low-inflation, low-risk-free currency, so it understates a "
            f"non-USD name against a currency-matched rate, by a known and "
            f"one-directional amount. E29 accepted that knowingly; what it "
            f"did not record was the size.*")


def _settlement_line(rows: list) -> str:
    """What the run did with today's bar, said out loud.

    REVIEW-4 report A 4.2: a run made during the session reads the live
    partial bar as a close (DECK 88.55 against a settled 88.74). The bar is
    now dropped; this line is how a reader learns it existed.
    """
    live = sorted({r.metrics.live_bar_date for r in rows
                   if r.metrics.live_bar_date is not None})
    unknown = [r for r in rows if r.metrics.last_close_settled is None
               and r.metrics.last_close is not None]
    if live:
        dates = ", ".join(d.isoformat() for d in live)
        return (f"*Price basis: LAST SETTLED CLOSE. A live intraday bar dated "
                f"{dates} was read and NOT used -- a partial bar is not a "
                f"close (report A 4.2).*")
    if unknown:
        return ("*Price basis: the run declared no settlement cutoff, so "
                "whether these closes had settled is DATA MISSING (`?` "
                "beside the close date).*")
    return "*Price basis: LAST SETTLED CLOSE.*"


def freshness_line(rows: list, as_of: date) -> str:
    """One line describing how good the data behind this run is."""
    live = sum(1 for r in rows if r.source == SOURCE_LIVE)
    cached = sum(1 for r in rows if r.source == SOURCE_CACHE)
    failed = sum(1 for r in rows if r.source == SOURCE_NONE)

    dates = [r.metrics.last_close_date for r in rows if r.metrics.last_close_date]
    if dates:
        newest, oldest = max(dates), min(dates)
        # Lead with the OLDEST close. Reporting the newest would let one fresh
        # ticker describe a watchlist that is mostly stale.
        if newest == oldest:
            span = f"close {newest.isoformat()} ({(as_of - newest).days}d old)"
        else:
            span = (
                f"closes {oldest.isoformat()}..{newest.isoformat()} "
                f"(oldest {(as_of - oldest).days}d old, newest {(as_of - newest).days}d)"
            )
    else:
        span = "no price data for any ticker"

    parts = [span, f"{live} live", f"{cached} from cache", f"{failed} unavailable"]
    line = " | ".join(parts)
    if cached or failed:
        line += "  **degraded**"
    return line


def earnings_nags(rows: list, as_of: date) -> list[str]:
    """HELD tickers whose catalyst has passed with no outcome ingested.

    The tool never notices that a report exists -- it has no news feed and
    does not guess at IR pages. But the watchlist already knows a catalyst
    date has passed unresolved, so it can say so and hand over the exact
    command. Never rely on the tool to spot the report; never rely on
    memory to feed it either.
    """
    nags = []
    for r in rows:
        e = r.entry
        if e.status != "HELD":
            continue
        if e.catalyst_date is None or e.catalyst_resolved is not None:
            continue
        if e.catalyst_date >= as_of:
            continue
        event = f" ({e.catalyst_event})" if e.catalyst_event else ""
        nags.append(
            f"`{e.ticker}` -- catalyst {e.catalyst_date.isoformat()}{event} passed, "
            f"unresolved.<br>Run: `python -m vss earnings --ticker {e.ticker} "
            f"--url <primary source>`"
        )
    return nags


def _e12_line(rows: list) -> str | None:
    """FRAMEWORK-EDITS E12: which PIPELINE names read Gate 1 as frozen.

    The DD column above is today's reading for every row. For a PIPELINE
    name that carries the pair, the dislocation verdict was struck on the
    FROZEN reading and today's figure is context; for one that does not,
    the band was read on today's level and this line says so, because a
    PIPELINE entry written before the pair existed has nothing frozen.
    """
    pipeline = [r for r in rows if r.entry.status == "PIPELINE"]
    if not pipeline:
        return None
    frozen, unfrozen = [], []
    for r in pipeline:
        e = r.entry
        today = _pct_abs(r.metrics.drawdown)
        if e.dd_at_entry is not None and e.peak_date is not None:
            frozen.append(f"`{e.ticker}` {e.dd_at_entry:.1%} against the 52-week "
                          f"closing high of {e.peak_date.isoformat()} (today {today})")
        else:
            unfrozen.append(f"`{e.ticker}` (today {today})")
    parts = []
    if frozen:
        parts.append(f"Gate 1 FROZEN AT ENTRY for {'; '.join(frozen)} -- the "
                     f"dislocation verdict is struck on the frozen reading and the "
                     f"band is not re-read; leaving PIPELINE takes an information "
                     f"event.")
    if unfrozen:
        parts.append(f"No `dd_at_entry`/`peak_date` recorded for "
                     f"{'; '.join(unfrozen)}: Gate 1 was read on today's level.")
    return "*E12: " + " ".join(parts) + "*"


def _e63_line(rows: list) -> str | None:
    """FRAMEWORK-EDITS E63: how far each HELD and WATCH-PRICED name sits
    above its own 52-week closing low, and the session that low was set.

    The DD column says how far a name has fallen from its high; it cannot
    say whether the name is still falling or has already turned. For a name
    approaching its MBP that is the question, so it is named here for the
    statuses that carry one. REPORTED, NEVER APPLIED -- no verdict reads it,
    and none ever will: B41 was decided by E127, no threshold on the low.
    """
    named = [r for r in rows if r.entry.status in ("HELD", "WATCH-PRICED")]
    if not named:
        return None
    parts = []
    for r in named:
        m = r.metrics
        if m.pct_above_52w_low is None:
            parts.append(f"`{r.entry.ticker}` DATA MISSING")
            continue
        when = m.low_52w_date.isoformat() if m.low_52w_date else "date not recorded"
        parts.append(f"`{r.entry.ticker}` {m.pct_above_52w_low:.1%} above its "
                     f"52-week closing low of {_num(m.low_52w)} ({when})")
    return ("*E63, HELD and WATCH-PRICED -- distance above the 52-week closing "
            "low: " + "; ".join(parts) + ". Reported, never applied: the "
            "drawdown cannot say whether a name is still falling or has already "
            "turned, and this can. DATA MISSING where the series does not cover "
            "52 weeks.*")


def _failure(failures: "Sequence", name: str):
    """The recorded failure for ``name``, or None if that component ran.

    Matched on the NAME the producer used, so `report.py` needs no import of
    `heartbeat` and a component that is never wrapped simply never appears.
    """
    return next((f for f in failures if getattr(f, "name", None) == name), None)


def render(
    rows: list,
    *,
    run_ts: datetime,
    as_of: date,
    dry_run: bool = False,
    ticker_filter: str | None = None,
    watchlist_size: int | None = None,
    needs_owner: "Sequence" = (),
    price_watch: "Sequence" = (),
    continuity: "Sequence[str]" = (),
    coverage: "object | None" = None,
    failures: "Sequence" = (),
    price_watch_ran: bool = False,
    previous_push: "list | dict | None" = None,
    corrections: "Sequence[str]" = (),
    tier_holds: "Sequence[str]" = (),
) -> str:
    """Render the report.

    ``ticker_filter`` marks a --ticker run. A scoped report must never read
    like a clean full-watchlist run: it says so in the title, in a banner and
    in its section headings, and it never generalises about "every ticker".
    """
    out: list[str] = []
    scoped = ticker_filter is not None

    title = f"# vss report {as_of.isoformat()}"
    if scoped:
        title += f" -- SCOPED to {ticker_filter}"
    out.append(title)
    out.append("")
    if dry_run:
        out.append("> DRY RUN -- nothing written.")
        out.append("")
    if scoped:
        others = ""
        if watchlist_size:
            n = watchlist_size - 1
            others = f" The other {n} watchlist entr{'y' if n == 1 else 'ies'} "
            others += "was" if n == 1 else "were"
            others += " not fetched and not evaluated."
        out.append(
            f"> **PARTIAL RUN — 1 of {watchlist_size or '?'} tickers.** "
            f"Only `{ticker_filter}` was examined.{others} "
            f"This report says nothing about the rest of the watchlist."
        )
        out.append("")
    out.append(f"**Run:** {run_ts.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    out.append("")
    # --- E126: A TIER CARRIED BELOW FOUR EVALUABLE GATES --------------------
    if tier_holds:
        out.append("## TIER HELD (E126)")
        out.append("")
        out.append("A tier requires at least FOUR evaluable gates. These names "
                   "carry one against a shorter denominator, which is the case "
                   "the ruling says must not exist. A section 4.4 score may "
                   "stand; the tier and its MBP may not.")
        out.append("")
        for line in tier_holds:
            out.append(f"- {line}")
        out.append("")

    # --- E122(c): WHAT THE VENDOR RESTATED TONIGHT -------------------------
    if corrections:
        out.append("## PRICE CORRECTIONS")
        out.append("")
        out.append("The vendor states a close differently from the one held. "
                   "Both values and both dates are here by E122(c); one that "
                   "crosses a level is NOT applied and blocks the name.")
        out.append("")
        for line in corrections:
            out.append(f"- {line}")
        out.append("")

    # --- THE PREVIOUS NIGHT'S BLOCK PUSH, WHEN IT DID NOT GO ----------------
    # (owner, 2026-09-19) A push that did not send is a failure to surface;
    # this is where it surfaces, with what it would have said.
    if previous_push:
        nights = previous_push if isinstance(previous_push, list) else [previous_push]
        out.append(f"## {len(nights)} BLOCK PUSH(ES) DID NOT GO")
        out.append("")
        out.append("Every night below was due a push and did not send. The "
                   "backlog clears only when one sends.")
        out.append("")
        for night in nights:
            out.append(f"**{night.get('as_of')}** — not sent: {night.get('outcome')}. "
                       f"It would have said:")
            out.append("")
            for line in night.get("lines") or ["(no lines recorded)"]:
                out.append(f"- {line}")
            out.append("")

    # --- RUN CONTINUITY ---------------------------------------------------
    # The dead man's switch. It goes FIRST, above NEEDS OWNER, because it is
    # not a finding about a name -- it is a statement about whether this
    # report can be read as one of a continuous series at all. A reader who
    # learns three nights are missing should learn it before, not after, the
    # numbers those nights would have moved.
    if continuity:
        out.append(f"## RUN CONTINUITY — {len(continuity)}")
        out.append("")
        for line in continuity:
            out.append(f"- {line}")
        out.append("")
        out.append("*The dead man's switch. A run that does not happen must "
                   "not look like a run with nothing to say.*")
        out.append("")
    # --- RUN COVERAGE -----------------------------------------------------
    # D2: whether this run GOT anything, not merely whether it happened. It
    # sits beside the continuity block because it answers the other half of
    # the same question, and it is printed when SHORT -- a healthy run says
    # so in the freshness line below and does not need a banner.
    if coverage is not None and getattr(coverage, "short", False):
        out.append("## RUN COVERAGE — SHORT")
        out.append("")
        out.append(f"**{coverage.reason}.**")
        out.append("")
        out.append("*A run that reaches its end and prices nothing is not a "
                   "run that worked. This one did NOT reset the staleness "
                   "clock, exits non-zero, and therefore sends no healthcheck "
                   "ping — so the outside observer will alarm on the ping's "
                   "absence rather than being told the run succeeded. Every "
                   "figure below is struck on whatever did arrive.*")
        out.append("")

    # --- COMPONENTS THAT DID NOT RUN --------------------------------------
    # D1: a part of the run that RAISED is named here, and the section it
    # would have filled says DATA MISSING below rather than vanishing. A
    # component that fails must never be indistinguishable from a component
    # with nothing to say -- that is the dead man's switch's own argument,
    # applied inside the report it prints.
    if failures:
        out.append(f"## COMPONENTS THAT DID NOT RUN — {len(failures)}")
        out.append("")
        for failure in failures:
            out.append(f"- {failure.line()}")
        out.append("")
        out.append("*Each of these was wrapped so it could not cost the "
                   "report, which is right. What is NOT right is a wrapped "
                   "failure that reads as silence, so it is named here and "
                   "its own section below says DATA MISSING.*")
        out.append("")

    # --- NEEDS OWNER ------------------------------------------------------
    # E92: a refresh fetched, extracted and reported, and nothing downstream
    # moves until the owner acts. This is a POINTER, NOT A SUMMARY -- ticker,
    # what it waits on, where the report is. The figures are in the report
    # and they stay there.
    needs_owner_failed = _failure(failures, "NEEDS OWNER (E92)")
    if needs_owner_failed is not None:
        out.append("## NEEDS OWNER — DATA MISSING")
        out.append("")
        out.append(f"**The check did not run: {needs_owner_failed.detail}.** "
                   f"{needs_owner_failed.consequence}")
        out.append("")
    elif needs_owner:
        out.append(f"## NEEDS OWNER — {len(needs_owner)}")
        out.append("")
        for item in needs_owner:
            out.append(f"- {item.line()}")
        out.append("")
        out.append("*E92: refreshed, reported, and waiting. No fair value, "
                   "tier, MBP, stop or status was written by the refresh.*")
        out.append("")
    out.append(f"**Data freshness:** {freshness_line(rows, as_of)}")
    out.append("")
    out.append(
        f"*Staleness gate: a close older than {MAX_CLOSE_AGE_TRADING_DAYS_LEVEL} "
        f"trading day(s) blocks a ticker CARRYING A LEVEL (HELD, an MBP or a "
        f"stop); {MAX_CLOSE_AGE_TRADING_DAYS} for every other ticker. The "
        f"exchange's own closed days are not counted. Blocked tickers "
        f"receive no verdict.*"
    )
    out.append("")
    out.append(_settlement_line(rows))
    # E39: a HELD name whose fair value has been NULLED is a name whose
    # method was superseded, not a name with no analysis. Say so, so the
    # bare dash in the fv_base column reads as the decision it records:
    # the stop is live, the fair value is pending a re-strike.
    nulled = sorted(r.entry.ticker for r in rows
                    if r.entry.status == "HELD" and r.entry.fv_base is None)
    if nulled:
        out.append("")
        out.append(
            f"*E39: {', '.join('`' + t + '`' for t in nulled)} — HELD with "
            f"`fv_base` NULLED: superseded by REVIEW-4, re-strike pending. "
            f"The stop is LIVE and is checked below; no fair value, MBP or "
            f"section 6.4 comparison is printed from a dead calculation.*")
    short = sorted({r.entry.ticker for r in rows
                    if r.metrics.covers_52_weeks is False})
    if short:
        out.append("")
        out.append(
            f"*52-week coverage: {', '.join('`' + t + '`' for t in short)} "
            f"carry a series that does not reach back 52 weeks plus five "
            f"trading days, so the 52-week high, the drawdown, the 52-week "
            f"low and the distance above it (E63) are DATA MISSING for them "
            f"— never a smaller number struck off a shorter window.*")
    flagged = sorted((r.entry.ticker, getattr(r, "series_finding", None))
                     for r in rows if getattr(r, "series_finding", None))
    if flagged:
        out.append("")
        named = "; ".join(f"`{t}` — {f}" for t, f in flagged)
        out.append(
            f"*Series sanity (K4): {named}. The stop, MBP and dislocation "
            f"checks are DATA MISSING for these — a verdict struck across a "
            f"break in the series is not a verdict, and a phantom halving "
            f"must never read as a breach of the stop.*")
    out.append("")

    # --- E97: THE RANKED LIST'S PRICE WATCH -------------------------------
    # Printed EVERY NIGHT, fired or not: the pointer is for a crossing, the
    # state is for reading, and a watcher visible only when it fires cannot
    # be checked for being wrong.
    # THREE STATES, AND AN ABSENCE IS NOT ONE OF THEM (D1). It ran and has
    # rows; it ran and had no ranking to watch; it RAISED. Until 2026-09-01
    # the last two were both "the section is not there", so a watcher broken
    # for a month read exactly like a month of quiet nights.
    watch_failed = _failure(failures, "RANKED WATCH (E97)")
    if watch_failed is not None:
        out.append("## RANKED WATCH (E97) — DATA MISSING")
        out.append("")
        out.append(f"**The watcher did not run: {watch_failed.detail}.** "
                   f"{watch_failed.consequence}")
        out.append("")
        out.append("*E97's table is printed every night, fired or not, "
                   "because a watcher visible only when it fires cannot be "
                   "checked for being wrong. A watcher that DIED is the same "
                   "argument: it says so here rather than leaving a gap.*")
        out.append("")
    elif price_watch:
        from .pricewatch import render_table

        fired = [i for i in price_watch if getattr(i, "events", None)]
        out.append(f"## RANKED WATCH (E97) — {len(price_watch)} name(s), "
                   f"{len(fired)} crossing(s) tonight")
        out.append("")
        out.extend(render_table(price_watch))
        out.append("")
    elif price_watch_ran and not scoped:
        # THE THIRD STATE, and it is CLAIMED BY THE CALLER, never inferred
        # from an empty list: "the watcher ran and found nothing to watch" is
        # a statement about the watcher, and only the code that called it
        # knows whether it was called at all.
        out.append("## RANKED WATCH (E97) — no ranked names to watch")
        out.append("")
        out.append("*The watcher ran and found no stored ranking to read "
                   "(`screen_rankings`). That is what the first run before "
                   "any weekly screen looks like; it is NOT what a broken "
                   "watcher looks like, which is the section above.*")
        out.append("")

    # --- BLOCKERS ---------------------------------------------------------
    blocked = [r for r in rows if r.assessment.blocked]
    out.append("## BLOCKERS")
    out.append("")
    if not blocked:
        out.append(
            f"None -- `{ticker_filter}` cleared the staleness gate."
            if scoped
            else "None. Every ticker cleared the staleness gate."
        )
    else:
        out.append(
            f"{len(blocked)} ticker(s) blocked. **No verdict is issued for these.**"
        )
        out.append("")
        out.append("| Ticker | Name | Status | Blocker |")
        out.append("|---|---|---|---|")
        for r in blocked:
            reasons = "<br>".join(b.reason for b in r.assessment.blockers)
            out.append(f"| `{r.entry.ticker}` | {r.entry.name} | {r.entry.status} | {reasons} |")
    out.append("")

    # --- EARNINGS TO INGEST ---------------------------------------------
    nags = earnings_nags(rows, as_of)
    if nags:
        out.append("## EARNINGS TO INGEST")
        out.append("")
        out.append(f"{len(nags)} HELD ticker(s) have an unresolved passed catalyst. "
                   f"Supply the primary source; vss does not go looking for it.")
        out.append("")
        for nag in nags:
            out.append(f"- {nag}")
        out.append("")

    # --- ACTIONS ----------------------------------------------------------
    actions = [r for r in rows if r.assessment.actionable]
    out.append("## ACTIONS")
    out.append("")
    if not actions:
        out.append(
            f"None -- `{ticker_filter}` is NO ACTION."
            if scoped
            else "None. Every unblocked ticker is NO ACTION."
        )
    else:
        out.append("| Ticker | Name | Status | Close | MBP | Stop | Verdicts |")
        out.append("|---|---|---|---|---|---|---|")
        for r in actions:
            verdicts = "<br>".join(
                f"**{v.label}** {v.detail}".strip() for v in r.assessment.verdicts
            )
            out.append(
                f"| `{r.entry.ticker}` | {r.entry.name} | {r.entry.status} "
                f"| {_num(r.metrics.last_close)} {r.entry.currency}{_retained_mark(r)} "
                f"| {_mbp_cell(r)} | {_num(r.entry.stop_price)} | {verdicts} |"
            )
    out.append("")

    # --- E24: THE RATE A CONVERTED VERDICT WAS STRUCK AT ------------------
    converted = [r for r in rows if r.entry.fx is not None]
    if converted:
        out.append("## CONVERTED PRICE LEGS (FRAMEWORK-EDITS E24)")
        out.append("")
        out.append("`fv_base`, `mbp` and `stop_price` are in the QUOTE "
                   "currency, because that is what they are compared "
                   "against and nothing in the code converts. The rate below "
                   "is FROZEN WITH THE VERDICT, not re-struck each run. **It "
                   "ages, and nothing here says when it has aged enough to "
                   "re-strike the verdict** -- that question is open (E24).")
        out.append("")
        out.append("| Ticker | Legs in | Pair | Rate | Rate as of | Age | "
                   "Converted | Priced against | Source |")
        out.append("|---|---|---|---|---:|---:|---|---|---|")
        for r in converted:
            fx = r.entry.fx
            out.append(
                f"| `{r.entry.ticker}` | {r.entry.currency} | {fx.pair} "
                f"| {fx.rate:.6f} | {fx.rate_as_of.isoformat()} "
                f"| {fx.age_days(as_of)}d | {fx.converted} "
                f"| {fx.price_date.isoformat()} | {fx.source} |")
        out.append("")

    # --- FULL TABLE -------------------------------------------------------
    out.append(f"## TICKER {ticker_filter}" if scoped else "## ALL TICKERS")
    out.append("")
    out.append(
        "| Ticker | Name | Status | Ccy | Close | Close date | 52w high | DD "
        "| 52w low | vs 52wL | RSI(14) "
        "| SMA50 | vs SMA50 | SMA200 | vs SMA200 | Avg vol 20d | Vol ratio "
        "| Tier | fv_base | MBP | to MBP | Stop | to Stop | Src | Result |"
    )
    out.append("|" + "---|" * 25)
    for r in rows:
        m = r.metrics
        e = r.entry
        out.append(
            f"| `{e.ticker}` | {e.name} | {e.status} | {e.currency} "
            f"| {_num(m.last_close)}{_retained_mark(r)} "
            f"| {_close_date_cell(m)} "
            f"| {_num(m.high_52w)} | {_pct_abs(m.drawdown)} "
            f"| {_num(m.low_52w)} | {_pct_abs(m.pct_above_52w_low)} | {_num(m.rsi14, 1)} "
            f"| {_num(m.sma50)} | {_pct(m.pct_vs_sma50)} "
            f"| {_num(m.sma200)} | {_pct(m.pct_vs_sma200)} "
            f"| {_int(m.avg_volume_20)} | {_num(m.volume_ratio, 2)} "
            f"| {e.tier if e.tier is not None else DASH} | {_fv_cell(r)} "
            f"| {_mbp_cell(r)} | {_pct(r.pct_to_mbp)} "
            f"| {_num(e.stop_price)} | {_pct(r.pct_to_stop)} "
            f"| {r.source} | {_row_result(r)} |"
        )
    out.append("")
    declaration = _rate_declaration_line(rows)
    if declaration:
        out.append(declaration)
        out.append("")
    refusals = _run_record_line(rows)
    if refusals:
        out.append(refusals)
        out.append("")
    e28 = _e28_line(rows)
    if e28:
        out.append(e28)
        out.append("")
    e12 = _e12_line(rows)
    if e12:
        out.append(e12)
        out.append("")
    e63 = _e63_line(rows)
    if e63:
        out.append(e63)
        out.append("")

    errored = [r for r in rows if r.error]
    if errored:
        out.append("## ERRORS")
        out.append("")
        for r in errored:
            served = "served from cache" if r.source == SOURCE_CACHE else "no data available"
            out.append(f"- `{r.entry.ticker}`: {r.error} ({served})")
        out.append("")

    return "\n".join(out)
