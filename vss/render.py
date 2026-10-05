"""The overview page's HTML. Read `vss.overview` for what the figures are.

**AN INSTRUMENT PANEL, NOT A DOCUMENT.** The second draft answered the
right three questions in the right order and still read as prose in rows.
The shape here is the same three questions — *does anything need me*,
*where is everything against its value*, *what is coming* — rendered as
things to recognise rather than lines to read.

**A CARD PER NAME, NOT A ROW.** A table is for comparing forty things; a
card is for recognising one. Ticker and company small at the top, the
price large, fair value and the maximum buy price beside it in smaller
type, then the year as a picture and the value track under that. The grid
reflows to one column on a phone, which is where this is actually opened.

**TYPOGRAPHY DOES THE RANKING.** The number that matters is large and its
label is small and muted; every figure is monospace with tabular numerals
so digits line up down the grid. When everything is the same size the page
is noise, whatever it says.

**SURFACES, NOT RULES.** Things are separated by background and space. No
visible table grid, no row borders — a page ruled into boxes reads as a
form to be filled in.

**A PICTURE NEVER REPLACES A FIGURE.** Every sparkline and every track has
its numbers beside it, small but exact, and where a picture cannot be
drawn the card says why instead of drawing a lie.

**NO JAVASCRIPT AT ALL.** Disclosure is `<details>`/`<summary>`, which the
browser gives for free. There is no script tag, no form, no button and no
input on this page, and tests assert each of those — that is how *nothing
here writes, decides or accepts anything* is enforced rather than intended.

**ONE ACCENT COLOUR, AND IT MEANS EXACTLY ONE THING: THIS NEEDS YOU.** It
appears in the top block and nowhere else — a test counts its uses in the
stylesheet and fails at two. Everything else is greyscale on a dark
ground, and **no colour anywhere carries meaning on its own**: every
position states its band in words, every sparkline carries a text
description, and every refusal prints `DATA MISSING` with its reason.
"""

from __future__ import annotations

import html
import re
from typing import Sequence

from .overview import (ATTENTION_CHECKS, DISTANCE_TONES, SCALE_HIGH,
                       SCALE_LOW, SECTION_DROPPED, SECTION_OUTSIDE,
                       TONE_MUTED, Doc, NameRow, Overview, QueueItem,
                       RunStamp, Spark, tone)
from .sales import DATA_MISSING, pct
from .shadowbook import BENCHMARKS, INCOMPLETE

#: How many timeline events are shown before the disclosure. The record
#: holds 230; that is an ARCHIVE, and an archive printed in full is a
#: filing cabinet emptied onto a desk.
TIMELINE_SHOWN = 10

#: Statuses whose cards lead the grid. A holding first, then the two
#: halves of E27's WATCH, then review work, then E111's read-not-watched.
#: Within a status the CHEAPEST against fair value comes first.
STATUS_ORDER = ("HELD", "WATCH-PRICED", "WATCH-GATED", "PIPELINE", "INTAKE")

#: The sparkline's box, in its own user units. Drawn at this size and
#: allowed to stretch to the card's width; a sparkline has no axis whose
#: proportions mean anything, so stretching costs nothing and a fixed
#: width would leave a gap on a wide card and overflow a narrow one.
SPARK_W, SPARK_H = 120.0, 32.0
#: Keep the stroke inside the box: a polyline at y=0 is drawn half
#: outside it and reads as a clipped chart.
SPARK_PAD = 3.0


# --- text ------------------------------------------------------------------

_CODE = re.compile(r"`([^`]+)`")


def esc(text: object) -> str:
    return html.escape("" if text is None else str(text), quote=True)


def code_spans(text: object) -> str:
    """Escape, then let the record's own backticks become <code>.

    The sentences come from `rules`, `manual` and `refresh`, which write
    paths and field names in backticks. Rendering them as code is
    presentation; the words are unchanged.
    """
    return _CODE.sub(r"<code>\1</code>", esc(text))


def num(amount: float | None, dp: int = 2) -> str:
    """A figure, monospace and tabular. Never a picture's substitute."""
    if amount is None:
        return f'<span class="miss">{DATA_MISSING}</span>'
    return f'<span class="figure">{amount:,.{dp}f}</span>'


def money(amount: float | None, currency: str | None, dp: int = 2) -> str:
    if amount is None:
        return f'<span class="miss">{DATA_MISSING}</span>'
    return (f'<span class="figure">{amount:,.{dp}f}</span>'
            f'<span class="unit">{esc(currency or "?")}</span>')


def signed(value: float | None) -> str:
    """A signed percentage, UNTONED.

    **THE SHADOW BOOK USES THIS AND MUST.** Its columns are RETURNS since
    a verdict, not distances to a level, and the distance scale would say
    something about them it has no business saying: a dropped name that
    rose is not green. E114 has the whole book read once a year precisely
    so that nobody reads a signal off it, and a colour is a signal.
    """
    if value is None:
        return f'<span class="miss">{DATA_MISSING}</span>'
    return f'<span class="figure">{esc(pct(value))}</span>'


def toned(value: float | None, *, muted: bool = False) -> str:
    """A DISTANCE TO A LEVEL, toned. **THE NUMBER AND ITS SIGN ARE THE
    CARRIER.**

    The tone says how far and the figure says how far, and only the second
    of those survives a greyscale print or a red-green colourblind reader
    — so the figure is never dropped, shortened or replaced by the colour,
    and the band's own words ride along as the title.
    """
    if value is None:
        return f'<span class="miss">{DATA_MISSING}</span>'
    name, words = tone(value, muted=muted)
    title = f' title="{esc(words)}"' if words else ""
    return f'<span class="figure {name}"{title}>{esc(pct(value))}</span>'


#: `overview.STATUS_STORE_ONLY` is a sentence, because on a data class it
#: has to explain itself. On a card badge it is four wrapped lines, so the
#: badge shows the first clause and keeps the sentence in the title.
def short_status(status: str) -> tuple[str, str]:
    """(what the badge shows, what hovering says)."""
    if "—" in status:
        head, _, tail = status.partition("—")
        return head.strip(), tail.strip()
    return status, ""


def badge(status: str) -> str:
    shown, full = short_status(status)
    title = f' title="{esc(status)}"' if full else ""
    return f'<span class="badge"{title}>{esc(shown)}</span>'


def plural(count: int, one: str, many: str | None = None) -> str:
    return one if count == 1 else (many or one + "s")


def doc_links(docs: Sequence[Doc]) -> str:
    if not docs:
        return f'<span class="miss">{DATA_MISSING} — no document on disk</span>'
    return " ".join(
        f'<a class="doc" href="{esc(d.href)}" title="{esc(d.label)}">'
        f"{esc(d.kind)}</a>" for d in docs)


# --- 1: does anything need me today ----------------------------------------


def attention_block(ov: Overview) -> str:
    """The top line. **The only place the accent colour appears.**

    Empty is an ANSWER and is printed as one, with the checks named beside
    it: *nothing needs you* and *nobody looked* are the same silence
    otherwise, which is the dead man's switch's own argument applied to a
    sentence.
    """
    checks = ('<p class="checked">Checked '
              + ", ".join(esc(c) for c in ATTENTION_CHECKS) + ".</p>")
    if not ov.attention:
        return ('<section class="attention quiet-state">'
                "<h1>Nothing needs you today.</h1>"
                f"{checks}</section>")
    count = len(ov.attention)
    head = f"{count} {plural(count, 'thing needs', 'things need')} you today."
    items = "".join(
        f'<li><span class="what">{esc(item.kind)}</span>'
        f"{code_spans(item.sentence)}</li>" for item in ov.attention)
    return (f'<section class="attention needed">'
            f"<h1>{esc(head)}</h1>"
            f'<ul class="needs">{items}</ul>'
            f"{checks}</section>")


# --- 2: the cards -----------------------------------------------------------


def _svg_id(ticker: str) -> str:
    """A clip-path id that is unique per card and legal in a fragment."""
    return "below-" + re.sub(r"[^A-Za-z0-9]+", "-", ticker).strip("-")


def sparkline(sp: Spark, currency: str | None, *, ticker: str = "x",
              muted: bool = False) -> str:
    """The year as a picture, or the reason there is none.

    **THE DESCRIPTION IS PART OF THE PICTURE**, not decoration on it: the
    `aria-label` says in words what the drawing says in shape, so the card
    survives a screen reader, a greyscale print and a browser that will
    not render the SVG. The two level lines are told apart by DASH
    PATTERN, never by colour alone, and both are named in the text under
    the card.
    """
    if not sp.ok:
        return f'<p class="spark-missing">{code_spans(sp.why)}</p>'
    inner = SPARK_H - 2 * SPARK_PAD

    def y_at(y: float) -> float:
        # `Spark` counts y upward from the low; SVG counts down. The flip
        # lives here and nowhere else.
        return SPARK_PAD + (1.0 - y) * inner

    path = " ".join(f"{x * SPARK_W:.1f},{y_at(y):.1f}"
                    for x, y in sp.points)
    # THE PART OF THE YEAR THAT TRADED BELOW FAIR VALUE, drawn as the same
    # line a second time and CLIPPED to the region under the level. Pure
    # SVG: a `clipPath` and a fragment reference, no script and no second
    # request. A muted name gets none of it -- the tone is drained on a
    # gate-closed name whatever the prices did.
    below = ""
    if sp.below_fv_y is not None and not muted:
        edge = y_at(sp.below_fv_y)
        ident = _svg_id(ticker)
        below = (f'<defs><clipPath id="{ident}"><rect x="0" y="{edge:.1f}" '
                 f'width="{SPARK_W:.0f}" height="{SPARK_H - edge:.1f}"/>'
                 f"</clipPath></defs>"
                 f'<polyline class="under" clip-path="url(#{ident})" '
                 f'points="{path}"/>')
    levels = ""
    if sp.fv_y is not None:
        levels += (f'<line class="lvl fv" x1="0" x2="{SPARK_W:.0f}" '
                   f'y1="{y_at(sp.fv_y):.1f}" y2="{y_at(sp.fv_y):.1f}"/>')
    if sp.mbp_y is not None:
        levels += (f'<line class="lvl mbp" x1="0" x2="{SPARK_W:.0f}" '
                   f'y1="{y_at(sp.mbp_y):.1f}" y2="{y_at(sp.mbp_y):.1f}"/>')
    unit = f" {currency}" if currency else ""
    label = (f"52 weeks of closes, {sp.first.isoformat()} to "
             f"{sp.last.isoformat()}, ranging {sp.low:,.2f} to "
             f"{sp.high:,.2f}{unit}")
    if sp.fv_y is not None:
        label += "; the dashed line is the fair value"
    if sp.mbp_y is not None:
        label += "; the dotted line is the maximum buy price"
    if sp.below_fv_y is not None:
        label += ("; the whole year traded below fair value"
                  if sp.below_fv_y >= 1.0 else
                  "; the part drawn under that line traded below fair value")
    return (f'<svg class="spark" viewBox="0 0 {SPARK_W:.0f} {SPARK_H:.0f}" '
            f'preserveAspectRatio="none" role="img" '
            f'aria-label="{esc(label)}"><title>{esc(label)}</title>'
            f'{levels}<polyline points="{path}"/>{below}</svg>')


def track(row: NameRow) -> str:
    """The value scale: where the price sits between half and half again
    of fair value, on a track that never rescales per name.

    **THE DOT IS TONED BY THE LEVEL THAT MATTERS** -- the maximum buy
    price where one is struck, because that is the line a purchase is
    measured against, and the fair value where none is. The tone repeats
    what the dot's POSITION already says; position is the carrier and the
    colour is the second reading of it.
    """
    pos = row.pos
    if not pos.ok:
        return f'<div class="track-missing">{code_spans(pos.why)}</div>'
    ticks = ['<span class="tick fv" style="left:50%"></span>']
    if pos.mbp_at is not None:
        ticks.append(f'<span class="tick mbp" style="left:{pos.mbp_at:.4f}%">'
                     f"</span>")
    # THE DATUM IS 0 OR 100; THE PIXEL IS NOT. A dot centred on either end
    # of the track is half outside it and reads as a rendering fault. The
    # clipped dot is pulled just inside and changes SHAPE, and the card's
    # own words say which end it is past -- the shape is a hint, the
    # sentence is the fact.
    at = pos.price_at
    edge = ""
    if pos.clipped:
        edge = " clipped"
        at = 98.0 if at >= 100.0 else 2.0
    against = (row.dist_mbp.value if row.dist_mbp.value is not None
               else row.dist_fv.value)
    name, words = tone(against, muted=bool(row.gate_closed))
    title = f' title="{esc(words)}"' if words else ""
    ticks.append(f'<span class="dot {name}{edge}"{title} '
                 f'style="left:{at:.4f}%"></span>')
    return f'<div class="track">{"".join(ticks)}</div>'


def _levels(row: NameRow) -> str:
    """Fair value and MBP, beside the price, small and exact."""
    cells = []
    if row.fv.amount is not None:
        tag = (f' <span class="tag">{esc(row.fv.label)}</span>'
               if row.fv.label else "")
        cells.append(f"<div><dt>fair value{tag}</dt>"
                     f"<dd>{money(row.fv.amount, row.fv.currency)}</dd></div>")
    else:
        cells.append(f"<div><dt>fair value</dt>"
                     f'<dd class="miss">{code_spans(row.fv.why)}</dd></div>')
    if row.mbp is not None:
        mark = (' <span class="tag">E32</span>' if row.mbp_superseded else "")
        cells.append(f"<div><dt>max buy price{mark}</dt>"
                     f"<dd>{money(row.mbp, row.currency)}</dd></div>")
    else:
        cells.append('<div><dt>max buy price</dt>'
                     f'<dd class="miss">none struck — a tier is what makes '
                     f"one (E90)</dd></div>")
    return f'<dl class="levels">{"".join(cells)}</dl>'


def _distances(row: NameRow) -> str:
    muted = bool(row.gate_closed)
    bits = []
    if row.dist_fv.value is not None:
        bits.append(f"{toned(row.dist_fv.value, muted=muted)} to fair value")
    if row.dist_mbp.value is not None:
        bits.append(f"{toned(row.dist_mbp.value, muted=muted)} "
                    f"to max buy price")
    return " &middot; ".join(bits)


def _waiting(row: NameRow) -> str:
    """The re-entry event and the scheduled re-score, ON THE CARD.

    **THESE ARE THE WHOLE REASON A CROSSING CAN MEAN NOTHING**, so they
    sit on the card of every name with an unresolved catalyst rather than
    only on a gated one: CTSH is WATCH-PRICED and its buy line is
    scheduled to fall below its own close on the day the event lands.

    THE RE-SCORE IS READ FROM THE ENTRY AND NEVER DERIVED. Three states
    and each is printed as itself: the entry states a move, the entry
    mentions the MBP and states no move this page could reconcile
    (DATA MISSING, with the reason), or the entry states no move at all —
    which is a fact about the record and not a gap in it.
    """
    if row.catalyst_date is None or row.catalyst_resolved is not None:
        return ""
    rows = [f"<div><dt>waiting on</dt><dd>"
            f"{_decides(row.catalyst_event or DATA_MISSING)}"
            f'<span class="asof">{esc(row.catalyst_date.isoformat())}</span>'
            f"</dd></div>"]
    move = row.rescore
    if move.ok:
        against = ""
        if row.price is not None and move.to is not None:
            against = (" The close is ABOVE that — this crossing would not "
                       "exist after the re-score."
                       if row.price > move.to else
                       " The close is below that too.")
        rows.append(
            "<div><dt>scheduled re-score</dt><dd>max buy price "
            f"{num(move.frm)} &rarr; {num(move.to)}"
            f'<span class="asof">'
            f"{esc(move.when.isoformat() if move.when else DATA_MISSING)}"
            f"</span>{esc(against)}</dd></div>")
    elif move.why:
        rows.append("<div><dt>scheduled re-score</dt>"
                    f'<dd class="miss">{code_spans(move.why)}</dd></div>')
    else:
        rows.append("<div><dt>scheduled re-score</dt>"
                    '<dd class="quiet-dd">the entry states no scheduled '
                    "move of the maximum buy price</dd></div>")
    return f'<dl class="waiting">{"".join(rows)}</dl>'


def card(row: NameRow) -> str:
    muted = bool(row.gate_closed)
    band = row.pos.band or ""
    if row.pos.clipped:
        band = f"{band} — {row.pos.clipped}" if band else row.pos.clipped
    off = " ".join(part for part in (row.spark.fv_off, row.spark.mbp_off)
                   if part)
    price = (money(row.price, row.currency) if row.price is not None
             else f'<span class="miss">{code_spans(row.price_why)}</span>')
    when = (f'<span class="asof">{esc(row.price_date.isoformat())}</span>'
            if row.price_date else "")
    return (
        '<article class="card">'
        f'<header class="card-head"><b class="tick">{esc(row.ticker)}</b>'
        f'<span class="co">{esc(row.name or DATA_MISSING)}</span>'
        f"{badge(row.status)}</header>"
        f'<div class="card-body">'
        f'<div class="price-block"><div class="price">{price}</div>{when}'
        f"{_levels(row)}</div>"
        f'<div class="spark-box">'
        f"{sparkline(row.spark, row.currency, ticker=row.ticker, muted=muted)}"
        "</div></div>"
        f"{track(row)}"
        f'<p class="band">{esc(band)}</p>'
        f'<p class="dists">{_distances(row)}</p>'
        # THE MUTE SAYS WHY, IN WORDS, ON THE CARD. A drained colour is a
        # colour, and a colour cannot say "the gate is closed" on its own.
        # ONLY WHERE SOMETHING IS ACTUALLY MUTED. PNDORA.CO is
        # WATCH-GATED with no fair value at all, so it has no distance and
        # no dot; a card announcing a drained colour it does not carry is
        # a sentence about nothing.
        + (f'<p class="closed">Distance shown muted: {esc(row.gate_closed)}. '
           f"The figure is a measurement, not an invitation.</p>"
           if muted and (row.pos.ok or row.dist_fv.value is not None
                         or row.dist_mbp.value is not None) else "")
        + (f'<p class="off">{esc(off)}</p>' if off else "")
        + _waiting(row)
        + "</article>")


def _card_sort(row: NameRow) -> tuple:
    rank = (STATUS_ORDER.index(row.status)
            if row.status in STATUS_ORDER else len(STATUS_ORDER))
    return (rank, row.pos.price_at if row.pos.price_at is not None else 1e9,
            row.ticker)


def _scale_key() -> str:
    return (
        '<div class="key">'
        '<div class="track key-track">'
        '<span class="tick fv" style="left:50%"></span></div>'
        f'<div class="key-labels"><span>{SCALE_LOW:.0%} of fair value</span>'
        f"<span>fair value</span><span>{SCALE_HIGH:.0%}</span></div>"
        '<p class="note">On every card: the large figure is the last '
        'settled close. The picture is 52 weeks of closes — a dashed line '
        'across it is the fair value and a dotted line the maximum buy '
        'price, drawn only where they fall inside the year\'s range, and '
        'said in words underneath where they do not. The bar beneath is '
        'the same scale on every card, from half the fair value to half '
        'again; a price past either end sits on the end and the card says '
        'so. Every picture has its figures beside it.</p>'
        + _tone_key() + "</div>")


def _tone_key() -> str:
    """The third scale, named. **GREEN AND RED MEASURE DISTANCE AND DECIDE
    NOTHING.**

    They are not the accent and must never be read as it: a name can be
    green and need nothing, and the thing that needs the owner can be red.
    The separation is structural rather than remembered -- **the accent is
    a SURFACE, filling the block at the top of the page, and this scale is
    INK, colouring figures and marks on cards.** Neither ever appears in
    the other's role.
    """
    chips = "".join(
        f'<span class="chip {name}">{esc(words)}</span>'
        for _, name, words in DISTANCE_TONES)
    return (f'<p class="note tone-key">Distance to a level, coloured: '
            f'{chips}<span class="chip {TONE_MUTED}">the gate is closed — '
            f"drawn muted whatever the number says</span></p>"
            f'<p class="note">It measures HOW FAR and decides nothing. A '
            f"name can be green and need nothing; the thing that needs you "
            f"can be red — that block is at the top of the page and is the "
            f"only thing wearing the accent. **Every coloured figure keeps "
            f"its sign and its number**, and every card keeps its band in "
            f"words, so nothing here is lost to a reader who cannot "
            f"separate red from green.</p>".replace("**", ""))


def _brief(rows: Sequence[NameRow], why: str) -> str:
    """A name reduced to a line, for a bucket that is not being measured."""
    return "".join(
        f'<div class="brief"><b>{esc(r.ticker)}</b>{badge(r.status)}'
        f'<span class="why">{code_spans(why(r))}</span></div>' for r in rows)


def cards_section(ov: Overview) -> str:
    # THREE BUCKETS AND A NAME IS IN EXACTLY ONE. E51/E96 names were
    # falling through to the live list whenever they were also DROPPED --
    # NOVO-B.CO is both -- which put a name the framework cannot value
    # among the names it is measuring. Outside is tested first because it
    # is a fact about the METHOD and outranks a status.
    outside = sorted((r for r in ov.rows if r.section == SECTION_OUTSIDE),
                     key=lambda r: r.ticker)
    dropped = sorted((r for r in ov.rows if r.section == SECTION_DROPPED),
                     key=lambda r: r.ticker)
    live = [r for r in ov.rows
            if r.section not in (SECTION_OUTSIDE, SECTION_DROPPED)]
    placed = sorted((r for r in live if r.pos.ok), key=_card_sort)
    unplaced = sorted((r for r in live if not r.pos.ok), key=_card_sort)

    out = ['<section id="value">',
           "<h2>Where everything sits against its value</h2>",
           _scale_key(),
           f'<div class="cards">{"".join(card(r) for r in placed)}</div>']

    out.append(
        f'<details class="rest"><summary>{len(unplaced)} '
        f'{plural(len(unplaced), "name")} '
        f"{plural(len(unplaced), 'carries', 'carry')} no position — each "
        f"says why</summary>"
        f'<div class="cards">{"".join(card(r) for r in unplaced)}</div>'
        "</details>")

    out.append(
        f'<details class="rest"><summary>{len(outside)} '
        f'{plural(len(outside), "name")} outside the circle of competence — '
        f"E51, E96</summary>"
        f'<p class="note">Section 5 cannot be run on these: the '
        f"pre-registered growth rate E28 requires would be a guess about "
        f"drug approvals (E51) or about a world price the company does not "
        f"set (E96). They are here so their absence from the grid above is "
        f"visible.</p>"
        + _brief(outside, lambda r: r.circle[1] if r.circle else DATA_MISSING)
        + "</details>")

    out.append(
        f'<details class="rest"><summary>{len(dropped)} dropped '
        f'{plural(len(dropped), "name")} — refused, exited or killed at a '
        f"gate</summary>"
        + _brief(dropped, lambda r: (
            f"last close {r.price:,.2f} {r.currency}. What it has done since "
            f"the verdict is in the shadow book below."
            if r.price is not None else
            f"{DATA_MISSING}: {r.price_why}"))
        + "</details>")
    out.append("</section>")
    return "\n".join(out)


# --- 3: what is coming -----------------------------------------------------

#: How much of a `catalyst_event` the forward list shows before folding
#: the rest. CTSH's note is four hundred characters of tier arithmetic --
#: correct, and not a line anyone scans. The FIRST SENTENCE goes on the
#: row and the remainder goes behind a nested disclosure; nothing is cut.
CALENDAR_LEAD = 160


def _decides(text: str) -> str:
    """The first sentence, then the rest behind a disclosure. NEVER a
    truncation: an ellipsis on a record is a record nobody can read."""
    body = str(text)
    if len(body) <= CALENDAR_LEAD:
        return code_spans(body)
    cut = body.find(". ")
    lead, rest = ((body[:cut + 1], body[cut + 2:]) if 0 < cut <= CALENDAR_LEAD
                  else (body[:CALENDAR_LEAD], body[CALENDAR_LEAD:]))
    return (f"{code_spans(lead)}"
            f'<details class="inline"><summary>the rest of the note'
            f"</summary>{code_spans(rest)}</details>")


def calendar_section(ov: Overview) -> str:
    # A DROPPED NAME'S UNRESOLVED DATE IS NOT SOMETHING THAT IS COMING.
    # UNA.AS was sold in August and its entry still carries a Q3 date; in
    # the forward list it reads as a report the owner is waiting for.
    ahead = [c for c in ov.calendar if c.resolved is None
             and c.when >= ov.as_of and c.status != "DROPPED"]
    behind = [c for c in ov.calendar if c not in ahead]
    out = ['<section id="ahead">', "<h2>What is coming</h2>"]
    if ahead:
        rows = []
        for item in ahead:
            days = (item.when - ov.as_of).days
            when = ("today" if days == 0 else
                    "tomorrow" if days == 1 else f"in {days} days")
            # NO ACCENT ON A NEAR DATE. Anything inside the horizon is
            # already named in the top block, and a second thing wearing
            # the accent teaches the reader it means "notable" -- which is
            # how an accent stops meaning "this needs you".
            rows.append(
                f'<div class="crow">'
                f'<div class="cwhen"><b class="figure">'
                f"{esc(item.when.isoformat())}</b>"
                f'<span class="asof">{esc(when)}</span></div>'
                f'<div class="cwhat"><b>{esc(item.ticker)}</b>'
                f"{badge(item.status)}"
                f"<div>{_decides(item.decides)}</div></div>"
                "</div>")
        out.append(f'<div class="calendar">{"".join(rows)}</div>')
    else:
        out.append('<p class="note">No unresolved <code>catalyst_date</code> '
                   "on the watchlist falls on or after today.</p>")
    if behind:
        out.append(
            f'<details class="rest"><summary>{len(behind)} '
            f'{plural(len(behind), "date")} past, resolved, or on a dropped '
            f"name</summary>"
            + "".join(
                f'<div class="brief"><b class="figure">'
                f"{esc(c.when.isoformat())}</b>"
                f'<span class="badge" title="{esc(c.status)}">'
                f"{esc(c.ticker)} — {esc(short_status(c.status)[0])}</span>"
                f'<span class="why">{code_spans(c.decides)} '
                + (f"Resolved {esc(c.resolved.isoformat())}."
                   if c.resolved else "Not recorded as resolved.")
                + "</span></div>" for c in behind)
            + "</details>")
    out.append("</section>")
    return "\n".join(out)


# --- below the fold --------------------------------------------------------


def _queue_rows(items: Sequence[QueueItem]) -> str:
    return "".join(
        '<div class="qrow"><div class="qcount">'
        + (f'<span class="figure">{item.actions}</span>'
           if item.actions is not None else f'<span class="miss">?</span>')
        + f'<span class="asof">{plural(item.actions or 0, "action")}</span>'
          f"</div>"
          f'<div class="qwhat"><b>{esc(item.ticker)}</b>'
          f'<span class="badge">{esc(item.kind)}</span>'
          f"<div>{code_spans(item.unblocks)}</div>"
          f'<div class="why">{code_spans(item.detail)}</div>'
          f'<div class="docs">{doc_links(item.docs)}</div></div></div>'
        for item in items)


def queue_section(ov: Overview) -> str:
    one = [i for i in ov.queue if i.actions == 1]
    rest = [i for i in ov.queue if i.actions != 1]
    total = len(ov.queue)
    summary = (f"What is outstanding — {total} {plural(total, 'item')}, "
               f"{len(one)} of {plural(len(one), 'it', 'them')} a single "
               f"action")
    out = [f'<details id="queue" class="fold"><summary>{esc(summary)}'
           f"</summary>",
           '<p class="note">Read from the record, never written by hand: '
           "every row is computed from a file that already exists, so an "
           "owner who does the work sees the row disappear the next time "
           "this page is generated. Ordered by how many owner actions "
           "would clear it.</p>"]
    if one:
        out.append("<h3>One action each</h3>")
        out.append(_queue_rows(one))
    if rest:
        counted = [i.actions for i in rest if i.actions is not None]
        out.append(
            f'<details class="rest"><summary>{len(rest)} '
            f'{plural(len(rest), "item")} needing more than one action'
            + (f" — {min(counted)} to {max(counted)}" if counted else "")
            + "</summary>" + _queue_rows(rest) + "</details>")
    if not ov.queue:
        out.append('<p class="note">The queue is empty. Every store has a '
                   "growth view, no read-back is outstanding above E108's "
                   "floor, no stop is missing and nothing is recorded as "
                   "NEEDS OWNER.</p>")
    out.append("</details>")
    return "\n".join(out)


def _event_rows(events) -> str:
    rows = []
    for event in events:
        when = (f'<b class="figure">{esc(event.when.isoformat())}</b>'
                if event.when else f'<span class="miss">{DATA_MISSING}</span>')
        note = ("" if event.dated_by == "stated" else
                '<span class="asof">'
                + ("the section states no date"
                   if event.dated_by == DATA_MISSING
                   else f"date {esc(event.dated_by)}")
                + "</span>")
        link = (f'<a class="doc" href="{esc(event.href)}">open</a>'
                if event.href else
                f'<span class="miss">{DATA_MISSING}</span>')
        detail = (f'<div class="why">{code_spans(event.detail)}</div>'
                  if event.detail else "")
        rows.append(
            f'<div class="erow"><div class="ewhen">{when}{note}</div>'
            f'<div class="ewhat"><span class="badge">{esc(event.kind)}</span> '
            f"{esc(event.title)}{detail}</div>"
            f'<div class="docs">{link}</div></div>')
    return "".join(rows)


def shadow_table(ov: Overview) -> str:
    if not ov.shadow:
        return f'<p class="miss">{code_spans(ov.shadow_note or DATA_MISSING)}</p>'
    labels = [b.label for b in BENCHMARKS]
    head = "".join(f"<th>{esc(c)}</th>" for c in
                   ["Name", "Verdict", "Standing", "Verdict date",
                    "Close at verdict", "Last settled close",
                    "Since verdict (TR)"] + labels + ["1m", "3m", "6m", "12m"])
    body = []
    for row in ov.shadow:
        v = row.verdict
        baseline = (money(v.close, v.currency) if v.close is not None
                    else f'<span class="miss">{DATA_MISSING}</span>')
        if row.last is not None:
            last = (f"{num(row.last)}"
                    f'<span class="asof">'
                    f"{esc(row.last_date.isoformat() if row.last_date else DATA_MISSING)}"
                    f"</span>")
        else:
            last = f'<span class="miss">{DATA_MISSING}</span>'
        if row.since is not None:
            since = signed(row.since)
        else:
            why = row.total_why or row.baseline_why or row.error or ""
            since = (f'<span class="miss" title="{esc(why)}">'
                     f"{DATA_MISSING}</span>")
        legs = []
        for label in labels:
            leg = next((l for l in row.since_legs if l.label == label), None)
            legs.append(signed(leg.change)
                        if leg is not None and leg.change is not None
                        else f'<span class="miss">{DATA_MISSING}</span>')
        windows = []
        for window in row.windows:
            if not window.elapsed:
                windows.append(f'<span class="badge">{INCOMPLETE}</span>'
                               f'<span class="asof">'
                               f"{esc(window.ends.isoformat())}</span>")
            elif window.name_change is None:
                windows.append(f'<span class="miss">{DATA_MISSING}</span>')
            else:
                parts = [pct(window.name_change)]
                for leg in window.legs:
                    parts.append(f"{leg.label} " + (
                        pct(leg.change) if leg.change is not None
                        else DATA_MISSING))
                windows.append('<span class="figure">'
                               + " / ".join(esc(p) for p in parts)
                               + "</span>")
        body.append(
            f"<tr><td><b>{esc(v.ticker)}</b></td>"
            f"<td>{esc(v.verdict)}</td><td>{esc(v.standing)}</td>"
            f'<td class="n"><span class="figure">'
            f"{esc(v.verdict_date.isoformat())}</span></td>"
            f'<td class="n">{baseline}</td><td class="n">{last}</td>'
            f'<td class="n">{since}</td>'
            + "".join(f'<td class="n">{leg}</td>' for leg in legs)
            + "".join(f'<td class="n">{w}</td>' for w in windows)
            + "</tr>")
    return (f'<div class="scroll"><table><thead><tr>{head}</tr></thead>'
            f"<tbody>{''.join(body)}</tbody></table></div>")


def history_section(ov: Overview) -> str:
    shown = ov.events[:TIMELINE_SHOWN]
    rest = ov.events[TIMELINE_SHOWN:]
    out = [f'<details id="history" class="fold">'
           f"<summary>What has happened — the last {len(shown)} of "
           f"{len(ov.events)} strikes, rulings and verdicts, and the shadow "
           f"book</summary>",
           _event_rows(shown)]
    if rest:
        out.append(f'<details class="rest"><summary>The other {len(rest)} — '
                   f"an archive, not a view</summary>"
                   f"{_event_rows(rest)}</details>")
    out.append("<h3>The shadow book</h3>")
    out.append('<p class="note"><b>This is not a signal.</b> It measures '
               "what happened, never whether the verdict was right: a "
               "dropped name that rose may have risen for the reasons the "
               "verdict refused to underwrite. Every comparison is a total "
               "return on both sides; a window that has not elapsed is "
               f"marked {INCOMPLETE} with the date it ends, and is never "
               "filled with the figure so far. " + code_spans(ov.shadow_note)
               + "</p>")
    out.append(shadow_table(ov))
    out.append("</details>")
    return "\n".join(out)


def documents_section(ov: Overview) -> str:
    rows = "".join(
        f'<div class="brief"><b>{esc(row.ticker)}</b>{badge(row.status)}'
        f'<span class="docs">{doc_links(row.docs)}</span></div>'
        for row in sorted(ov.rows, key=lambda r: r.ticker))
    return (f'<details id="docs" class="fold"><summary>Documents, by name — '
            f"the briefing, the reading, the strike, the run record, the "
            f"growth view and the store</summary>"
            f'<p class="note">The page shows the state; these carry the '
            f"evidence. Nothing here summarises one — a summary of a "
            f"sourced document is a judgement without its sources.</p>"
            f"{rows}</details>")


def problems_section(ov: Overview) -> str:
    """What could not be read. The COUNT is always visible, never folded.

    A source that could not be read is the one thing a state page must not
    be silent about, so the summary line states it whether or not anyone
    opens the disclosure.
    """
    if not ov.problems:
        return ('<p class="note">Every source below was read. Nothing on '
                "this page is missing because something failed to load.</p>")
    count = len(ov.problems)
    items = "".join(f"<li>{code_spans(p)}</li>" for p in ov.problems)
    return (f'<details class="fold problems"><summary>{count} '
            f'{plural(count, "source")} could not be read — every row that '
            f"needed one prints {DATA_MISSING}</summary>"
            f"<ul>{items}</ul></details>")


# --- the footer ------------------------------------------------------------


def footer(ov: Overview) -> str:
    """WHEN, and FROM WHICH RUN. Never one without the other.

    A page generated by hand at noon on a machine whose timer died on
    Tuesday is a Tuesday page with today's timestamp on it, and reading it
    as current is the failure this block exists to prevent.
    """
    stamp: RunStamp = ov.stamp
    # F1 limb (c) requirement 1: ISO 8601 WITH TIMEZONE. The earlier
    # strftime('%Z') rendered EMPTY for an aware datetime built by
    # astimezone(), so the page carried no zone at all; isoformat() carries
    # the offset. ONE FACT, TWO PLACES: the header stamp in render() shows
    # the same ov.generated the same way. They must never be computed
    # differently -- if one is edited the other follows.
    lines = ["Page generated <b>"
             f"{esc(ov.generated.isoformat(timespec='seconds'))}</b>."]
    if stamp.completion is not None and stamp.completion.finished is not None:
        # TWO FACTS, NOT ONE. The run below is the last COMPLETED nightly
        # one; the cache stamp is when the bars this page read were
        # written, and a hand fetch moves the second without moving the
        # first. Saying "prices come from the run of X" would be a claim
        # about causation the page cannot check.
        lines.append(
            "The last completed nightly run finished <b>"
            f"{esc(stamp.completion.finished.strftime('%Y-%m-%d %H:%M'))}</b> "
            f"(as of {esc(stamp.completion.as_of)}, "
            f"{esc(stamp.completion.coverage_line)}).")
    else:
        lines.append(f'<span class="miss">{DATA_MISSING} — '
                     f'{esc(stamp.why or "no completed nightly run is on record")}'
                     f".</span>")
    if stamp.cache_written is not None:
        lines.append("The prices on this page were cached <b>"
                     f"{esc(stamp.cache_written.strftime('%Y-%m-%d %H:%M'))}"
                     "</b>; closes are settled through <b>"
                     f"{esc(ov.settled.isoformat())}</b>.")
    else:
        lines.append(f'<span class="miss">{DATA_MISSING} — the price cache '
                     "carries no write time, so this page cannot say how "
                     "old its prices are.</span>")
    if stamp.stale:
        lines.append(f'<span class="miss">{code_spans(stamp.stale)}</span>')
    sources = " &middot; ".join(
        f'<a href="{esc(href)}">{esc(label)}</a>' for label, href in ov.sources)
    return (
        "<footer>"
        f"<p>{' '.join(lines)}</p>"
        "<p>Read-only. Nothing on this page writes, decides or accepts "
        "anything, and no figure on it is stored twice — every one is read "
        f"from {sources} at generation time. Every decision this project "
        "makes is a dictated ruling in a session.</p>"
        "<p>Regenerate with <code>python -m vss overview</code>. The "
        "nightly run rewrites it to <code>reports/OVERVIEW.html</code>, "
        "and nowhere else.</p>"
        "</footer>")


# --- the page --------------------------------------------------------------


def generated_stamp(ov: Overview) -> str:
    """The generation timestamp, visible without scrolling on a phone.

    F1 limb (c) requirement 1: ISO 8601 with timezone, in the header. It is
    PROVENANCE, NOT A FINDING -- rendered in the existing muted `.note`
    style so it does not compete with the first card.

    ONE FACT, TWO PLACES. This and the footer's first sentence render the
    same ov.generated, formatted the same way. They must never be computed
    differently -- if one is edited the other follows.
    """
    when = esc(ov.generated.isoformat(timespec="seconds"))
    return (f'<p class="note">Generated <time datetime="{when}">{when}</time>'
            "</p>")


def render(ov: Overview) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>vss — {esc(ov.as_of.isoformat())}</title>
<style>{CSS}</style>
</head>
<body>
{generated_stamp(ov)}
{attention_block(ov)}
{cards_section(ov)}
{calendar_section(ov)}
{queue_section(ov)}
{history_section(ov)}
{documents_section(ov)}
{problems_section(ov)}
{footer(ov)}
</body>
</html>
"""


#: The whole stylesheet, inline: the page must open from a `file://` URL
#: with no second request. DARK, and committed to it -- the owner opens
#: this on a phone. One accent, used only by `.needed`.
#:
#: SURFACES, NOT RULES. Nothing here draws a border to separate two
#: things: cards, panels and rows are told apart by background and space.
#: The one hairline left is under the footer, which is a boundary rather
#: than a division.
CSS = """
:root {
  --bg: #0c0e11;
  --card: #171a1f;
  --card-2: #1c2027;
  --groove: #24282f;
  --ink: #eceae5;
  --quiet: #9096a0;
  --faint: #666c76;
  --accent: #ffb454;
  --accent-ink: #161106;
  --miss: #cfa878;
  /* THE THIRD SCALE: distance, diverging through the neutral grey. It is
     never the accent and never a verdict. The two ends differ in
     LIGHTNESS as well as hue (green ~78, red ~62 in perceived terms), so
     the ladder still reads as a ladder to someone who cannot separate
     the hues -- and every figure wearing one keeps its sign and its
     number, which is the carrier that never fails. */
  --d-at: #63d29a;
  --d-near: #8fc4ab;
  --d-mid: #9096a0;
  --d-far: #cf8f89;
  --d-remote: #ef7d73;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
          "Liberation Mono", monospace;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0 auto; padding: 0 1rem 5rem; max-width: 72rem;
  background: var(--bg); color: var(--ink);
  font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        "Helvetica Neue", Arial, sans-serif;
}
h1 { font-size: 1.5rem; line-height: 1.25; margin: 0 0 .75rem; }
h2 { font-size: .72rem; text-transform: uppercase; letter-spacing: .12em;
     color: var(--faint); font-weight: 600; margin: 3rem 0 1rem; }
h3 { font-size: .7rem; text-transform: uppercase; letter-spacing: .1em;
     color: var(--faint); font-weight: 600; margin: 1.75rem 0 .6rem; }
p { margin: .5rem 0; }
b { font-weight: 600; }
a { color: var(--ink); }
code { font-family: var(--mono); font-size: .88em; color: var(--quiet); }

/* EVERY FIGURE, EVERYWHERE. Monospace and tabular, so digits line up
   down the grid however the cards wrap. */
.figure { font-family: var(--mono); font-variant-numeric: tabular-nums;
          font-feature-settings: "tnum"; }
.unit { font-family: var(--mono); font-size: .55em; color: var(--faint);
        margin-left: .3em; letter-spacing: .04em; }
.miss { color: var(--miss); }

/* Ink, never a surface -- see `_tone_key`. The accent fills a block and
   these colour figures and marks; neither takes the other's role. */
.d-at { color: var(--d-at); }
.d-near { color: var(--d-near); }
.d-mid { color: var(--d-mid); }
.d-far { color: var(--d-far); }
.d-remote { color: var(--d-remote); }
.d-muted, .d-none { color: var(--faint); }
.tone-key .chip { display: inline-block; margin: .15rem .35rem .15rem 0;
                  padding: .1rem .45rem; border-radius: 4px;
                  background: var(--card); font-size: .7rem; }
.tone-key .chip::before { content: "\2014\a0"; }

/* Small, muted, and never the thing being read first. */
.badge, .asof, dt {
  font-size: .62rem; text-transform: uppercase; letter-spacing: .09em;
  color: var(--faint); font-weight: 500;
}
.badge { background: var(--groove); color: var(--quiet);
         padding: .1rem .4rem; border-radius: 4px; white-space: nowrap; }
.tag { font-size: .55rem; text-transform: uppercase; letter-spacing: .08em;
       background: var(--groove); color: var(--quiet);
       padding: .05rem .3rem; border-radius: 3px; }
.note { font-size: .8rem; color: var(--quiet); margin: .5rem 0 0;
        max-width: 52rem; }
.why { color: var(--quiet); font-size: .78rem; }

/* --- 1: the only accent on the page ------------------------------------ */
.attention { margin: 2rem 0 1rem; padding: 1.25rem 1.35rem 1.1rem;
             border-radius: 14px; background: var(--card); }
.attention.needed { background: var(--accent); color: var(--accent-ink); }
.attention.needed a, .attention.needed code { color: var(--accent-ink); }
.attention.quiet-state h1 { color: var(--ink); font-weight: 500; }
ul.needs { list-style: none; margin: 0; padding: 0; }
ul.needs li { margin: 0 0 .85rem; font-size: 1.02rem; line-height: 1.5; }
ul.needs li:last-child { margin-bottom: 0; }
/* THE WORD, ALWAYS. The accent block is the only colour that means
   anything, and this label is what it means -- so the meaning survives a
   greyscale print, a colour-blind reader and a screenshot. */
.what { display: block; font-size: .66rem; text-transform: uppercase;
        letter-spacing: .11em; opacity: .72; margin-bottom: .1rem; }
.checked { font-size: .78rem; opacity: .72; margin: 1rem 0 0; }
.attention.quiet-state .checked { color: var(--quiet); opacity: 1; }

/* --- 2: the cards ------------------------------------------------------- */
.key { margin-bottom: 1.5rem; }
.key-track { margin-bottom: .3rem; }
.key-labels { display: flex; justify-content: space-between;
              font-size: .66rem; color: var(--faint);
              font-family: var(--mono); }

.cards { display: grid; gap: .75rem; margin-top: 1rem;
         grid-template-columns: repeat(auto-fill, minmax(min(20rem, 100%), 1fr)); }
.card { background: var(--card); border-radius: 12px;
        padding: .95rem 1rem 1rem; }
.card-head { display: flex; align-items: baseline; gap: .5rem;
             flex-wrap: wrap; margin-bottom: .55rem; }
.card-head .tick { font-size: .82rem; letter-spacing: .04em;
                   font-family: var(--mono); }
.card-head .co { font-size: .72rem; color: var(--faint); flex: 1 1 auto;
                 overflow: hidden; text-overflow: ellipsis;
                 white-space: nowrap; }
.card-body { display: grid; grid-template-columns: 1fr auto;
             gap: .5rem .9rem; align-items: start; }
.price { font-size: 1.9rem; line-height: 1.05; font-weight: 600;
         letter-spacing: -.02em; }
.price .miss { font-size: .8rem; font-weight: 400; line-height: 1.4;
               display: block; }
.price-block > .asof { display: block; margin-top: .1rem; }
dl.levels { margin: .6rem 0 0; display: flex; gap: 1.1rem; flex-wrap: wrap; }
dl.levels > div { min-width: 0; }
dl.levels dt { margin-bottom: .05rem; }
dl.levels dd { margin: 0; font-size: .92rem; }
dl.levels dd.miss { font-size: .7rem; line-height: 1.35; max-width: 11rem; }

.spark-box { width: 120px; }
svg.spark { display: block; width: 120px; height: 32px; }
svg.spark polyline { fill: none; stroke: var(--ink); stroke-width: 1.25;
                     stroke-linejoin: round; stroke-linecap: round;
                     vector-effect: non-scaling-stroke; }
/* TOLD APART BY DASH PATTERN, never by colour alone. */
svg.spark .lvl { stroke: var(--faint); stroke-width: 1;
                 vector-effect: non-scaling-stroke; }
svg.spark .lvl.fv { stroke-dasharray: 5 3; }
svg.spark .lvl.mbp { stroke-dasharray: 1 3; }
/* The stretch of the year that traded below fair value. Same line, drawn
   again and clipped -- the shape is unchanged and only the ink differs,
   and the card's own figures say the same thing in numbers. */
svg.spark polyline.under { stroke: var(--d-at); }
.spark-missing { font-size: .68rem; color: var(--miss); margin: 0;
                 width: 120px; line-height: 1.35; }

.track { position: relative; height: 8px; border-radius: 4px;
         background: var(--groove); margin: .85rem 0 .5rem; }
.track .tick { position: absolute; top: -3px; width: 2px; height: 14px;
               margin-left: -1px; border-radius: 1px; background: var(--faint); }
.track .tick.mbp { height: 11px; top: -1.5px; background: var(--quiet); }
.track .dot { position: absolute; top: 50%; width: 11px; height: 11px;
              margin: -5.5px 0 0 -5.5px; border-radius: 50%;
              background: currentColor; color: var(--ink);
              box-shadow: 0 0 0 2px var(--card); }
.track .dot.clipped { border-radius: 2px; width: 7px; margin-left: -3.5px; }
.track-missing { font-size: .72rem; color: var(--miss); margin: .85rem 0 .5rem;
                 line-height: 1.4; }
.band { font-size: .74rem; color: var(--quiet); margin: 0; }
.closed { font-size: .7rem; color: var(--faint); margin: .3rem 0 0;
          line-height: 1.4; }
/* The re-entry event and the scheduled re-score. On its own surface: it
   qualifies everything above it and must not read as a footnote to the
   distances. */
dl.waiting { margin: .7rem 0 0; padding: .55rem .7rem; border-radius: 8px;
             background: var(--card-2); font-size: .74rem; }
dl.waiting > div + div { margin-top: .45rem; }
dl.waiting dd { margin: .1rem 0 0; color: var(--quiet); line-height: 1.45; }
dl.waiting dd .asof { display: block; }
dl.waiting .quiet-dd { color: var(--faint); }
.dists { font-size: .74rem; color: var(--faint); margin: .15rem 0 0; }
.off { font-size: .7rem; color: var(--faint); margin: .3rem 0 0;
       font-style: italic; }

.brief { background: var(--card); border-radius: 9px;
         padding: .55rem .75rem; margin-bottom: .4rem; font-size: .85rem;
         display: flex; flex-wrap: wrap; align-items: baseline; gap: .5rem; }
.brief .why { flex: 1 1 100%; }

/* --- 3: what is coming -------------------------------------------------- */
.calendar { display: grid; gap: .5rem; }
.crow { background: var(--card); border-radius: 10px; padding: .7rem .85rem;
        display: grid; grid-template-columns: 1fr; gap: .25rem; }
.cwhen { display: flex; align-items: baseline; gap: .5rem; }
.cwhen b { font-size: .95rem; }
.cwhat { font-size: .85rem; color: var(--quiet);
         display: flex; flex-wrap: wrap; align-items: baseline; gap: .45rem; }
.cwhat b { color: var(--ink); }
.cwhat > div { flex: 1 1 100%; }

/* --- below the fold ----------------------------------------------------- */
details.fold { margin: 1rem 0; border-radius: 12px; background: var(--card); }
details.fold > summary { padding: .95rem 1.1rem; cursor: pointer;
                         font-size: .85rem; color: var(--ink); }
details.fold > *:not(summary) { padding-left: 1.1rem;
                                padding-right: 1.1rem; }
details.fold[open] > summary { padding-bottom: .35rem; }
details.problems > summary { color: var(--miss); }
details.rest { margin: 1rem 0; }
details.rest > summary { font-size: .8rem; color: var(--quiet);
                         cursor: pointer; padding: .55rem 0; }
details.inline > summary { font-size: .7rem; color: var(--faint);
                           cursor: pointer; padding: .15rem 0; }
summary::marker { color: var(--faint); }
details.fold .brief, details.fold .qrow, details.fold .erow {
  background: var(--card-2); }

.qrow, .erow { border-radius: 9px; padding: .7rem .85rem;
               margin-bottom: .4rem; display: grid;
               grid-template-columns: 3.4rem 1fr; gap: .2rem .85rem; }
.qcount { text-align: right; font-weight: 600; }
.qcount .asof { display: block; font-weight: 400; }
.qwhat, .ewhat { font-size: .88rem; }
.qwhat > b, .ewhat > b { margin-right: .4rem; }
.ewhen { font-size: .78rem; }
.ewhen .asof { display: block; }
.erow { grid-template-columns: 6.5rem 1fr auto; }
.docs { font-size: .74rem; margin-top: .35rem; }
a.doc { display: inline-block; margin: 0 .3rem .25rem 0;
        padding: .12rem .45rem; border-radius: 5px; text-decoration: none;
        color: var(--quiet); background: var(--groove); }
a.doc:hover { color: var(--ink); }

/* NO VISIBLE GRID. Rows are told apart by an alternating surface. */
.scroll { overflow-x: auto; margin: .5rem 0 1rem; }
table { border-collapse: collapse; font-size: .78rem; min-width: 62rem; }
th { text-align: left; font-weight: 600; color: var(--faint);
     font-size: .62rem; text-transform: uppercase; letter-spacing: .07em;
     padding: .5rem .65rem; white-space: nowrap; }
td { padding: .55rem .65rem; vertical-align: top; }
tbody tr:nth-child(odd) { background: var(--card-2); }
tbody tr td:first-child { border-radius: 7px 0 0 7px; }
tbody tr td:last-child { border-radius: 0 7px 7px 0; }
td.n { text-align: right; white-space: nowrap; }
td .asof { display: block; }

footer { margin-top: 3.5rem; padding-top: 1.35rem;
         border-top: 1px solid var(--groove); color: var(--faint);
         font-size: .78rem; }
footer a { color: var(--quiet); }

@media (min-width: 46rem) {
  body { padding: 0 2rem 5rem; }
  .crow { grid-template-columns: 9rem 1fr; align-items: baseline; }
  .cwhen { flex-direction: column; align-items: flex-start; gap: 0; }
}
"""
