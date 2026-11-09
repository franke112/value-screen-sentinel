"""The four figures a reader can move (2026-11-09), in both languages.

    rdcf        the reverse DCF: move the price, move your own belief
    funnel      where every company stands: one square per company
    graveyard   every rule that was tested: what it claimed, what the test said
    shadow      the shadow book so far: refusals against the index, by horizon

Each is drawn here, complete, as plain HTML and SVG in its default state, so
it reads with scripts off and in print. site.js only moves what is already
on the page. Colour keeps the site's five meanings (style.css); the palette
order of the funnel was run through the data-viz validator (purple, orange,
green, vermillion: adjacent pairs pass for colour-blind readers) and no
group is told apart by colour alone: every one has its label and its count.

NO VENDOR FIGURE IS IN THIS FILE. The funnel's counts are the project's own
(the universe lists and the master list of 2026-11-09). The shadow book's
are counts of refusals, never a price or a return. The graveyard tells each
test in words (reference/backtest/WHAT-WE-TESTED.md).
"""

import json
from html import escape

P = dict(paper="#FBFAF7", ink="#1B1B1B", muted="#5A5A5A", rule="#C9C6BF", surface="#F1EFE9",
         value="#0072B2", price="#E69F00", price_t="#8A5A00", passc="#009E73", fail="#D55E00",
         miss="#767676", miss_f="#E6E6E6", owner="#CC79A7", owner_t="#8B4A70")


def _attr(obj):
    return escape(json.dumps(obj, ensure_ascii=False), quote=True)


def _num(x, lang, dp=1):
    s = f"{x:.{dp}f}"
    return s.replace(".", ",") if lang == "sv" else s


# ===========================================================================
# 1. the reverse DCF
# ===========================================================================
RATE, TERM, YEARS, FCF0 = 0.095, 0.025, 10, 10.0
GMIN, GMAX, VMAX = -8.0, 18.0, 500.0
X0, X1, Y0, Y1 = 64.0, 624.0, 22.0, 292.0


def value_at(g):
    """Ten years of cash flow growing at g, then 2.5 % for ever, at 9.5 %."""
    v, cf = 0.0, FCF0
    for t in range(1, YEARS + 1):
        cf *= 1 + g
        v += cf / (1 + RATE) ** t
    return v + cf * (1 + TERM) / (RATE - TERM) / (1 + RATE) ** YEARS


def implied_growth(price):
    lo, hi = -0.9, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if value_at(mid) < price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _x(g_pct):
    return X0 + (g_pct - GMIN) / (GMAX - GMIN) * (X1 - X0)


def _y(v):
    return Y1 - min(v, VMAX) / VMAX * (Y1 - Y0)


RDCF_T = {
    "en": dict(
        title="The reverse DCF, both ways",
        desc="A curve shows what a business with 10 per share of spare cash is worth at each growth rate. A horizontal line at the price meets the curve at the growth the price assumes. A vertical line at the growth you believe meets it at what the business is worth to you.",
        xaxis="growth per year, for ten years", yaxis="worth per share",
        price_label="The price", belief_label="The growth you believe",
        per_share="per share", per_year="% a year",
        leg_curve="what the business is worth at each growth rate",
        leg_price="the price, and the growth it assumes",
        leg_belief="your belief, and what it makes the business worth",
        assumes="At {p}, the price assumes cash flow growing {g} % a year for ten years.",
        worth="At your {b} %, the business is worth {v} per share.",
        below="The price is {d} % below that: on your belief there is a margin.",
        above="The price is {d} % above that: you would be paying for growth you do not expect.",
        equal="Price and belief say the same thing. There is no gap to buy.",
        plab="price {p}: assumes {g} %", blab="you believe {b} %: worth {v}",
        hover="at {g} % growth: worth {v}",
        caption="NAME A again: 10 per share of spare cash, ten years of growth, then 2.5 percent, all at a 9.5 percent required return. Move the price and the assumption moves. Move your belief and the value moves. The gap between the two is the only thing there is to decide. With scripts off, the table above is the figure.",
    ),
    "sv": dict(
        title="Den omvända kalkylen, åt båda hållen",
        desc="En kurva visar vad ett företag med 10 per aktie i fritt kassaflöde är värt vid varje tillväxttakt. En vågrät linje vid priset möter kurvan vid den tillväxt priset förutsätter. En lodrät linje vid den tillväxt du tror på möter den vid vad företaget är värt för dig.",
        xaxis="tillväxt per år, i tio år", yaxis="värde per aktie",
        price_label="Priset", belief_label="Tillväxten du tror på",
        per_share="per aktie", per_year="% per år",
        leg_curve="vad företaget är värt vid varje tillväxttakt",
        leg_price="priset, och tillväxten det förutsätter",
        leg_belief="din tro, och vad den gör företaget värt",
        assumes="Vid {p} förutsätter priset att kassaflödet växer {g} % per år i tio år.",
        worth="Med dina {b} % är företaget värt {v} per aktie.",
        below="Priset ligger {d} % under det: med din tro finns en marginal.",
        above="Priset ligger {d} % över det: du skulle betala för tillväxt du inte väntar dig.",
        equal="Pris och tro säger samma sak. Det finns inget glapp att köpa.",
        plab="pris {p}: förutsätter {g} %", blab="du tror {b} %: värt {v}",
        hover="vid {g} % tillväxt: värt {v}",
        caption="BOLAG A igen: 10 per aktie i fritt kassaflöde, tio års tillväxt, sedan 2,5 procent, allt med 9,5 procents avkastningskrav. Flytta priset så flyttar sig antagandet. Flytta din tro så flyttar sig värdet. Glappet mellan de två är det enda som finns att avgöra. Utan skript är tabellen ovan figuren.",
    ),
}


def rdcf(lang):
    t = RDCF_T[lang]
    price, belief = 130.0, 5.0      # a row of the table above, and a visible gap
    g = implied_growth(price) * 100
    v = value_at(belief / 100)
    pts = " ".join(f"{_x(gp / 2):.1f},{_y(value_at(gp / 200)):.1f}"
                   for gp in range(int(GMIN * 2), int(GMAX * 2) + 1))
    grid = "".join(
        f'<line x1="{X0}" y1="{_y(val):.1f}" x2="{X1}" y2="{_y(val):.1f}" stroke="{P["rule"]}" stroke-width="1"/>'
        f'<text x="{X0 - 8}" y="{_y(val) + 4:.1f}" text-anchor="end" fill="{P["muted"]}" font-size="12">{val}</text>'
        for val in (0, 100, 200, 300, 400, 500))
    ticks = "".join(
        f'<line x1="{_x(gp):.1f}" y1="{Y1}" x2="{_x(gp):.1f}" y2="{Y1 + 5}" stroke="{P["muted"]}" stroke-width="1"/>'
        f'<text x="{_x(gp):.1f}" y="{Y1 + 19}" text-anchor="middle" fill="{P["muted"]}" font-size="12">{gp} %</text>'
        for gp in (-8, -4, 0, 4, 8, 12, 16))
    px, py, bx, by = _x(g), _y(price), _x(belief), _y(v)
    fmt = lambda s, **k: s.format(**k)  # noqa: E731
    plab = fmt(t["plab"], p=f"{price:.0f}", g=_num(g, lang))
    blab = fmt(t["blab"], b=_num(belief, lang), v=f"{v:.0f}")
    d = (price / v - 1) * 100
    gap = (fmt(t["below"], d=_num(-d, lang, 0)) if d < -0.5
           else fmt(t["above"], d=_num(d, lang, 0)) if d > 0.5 else t["equal"])
    readout = (fmt(t["assumes"], p=f"{price:.0f}", g=_num(g, lang)) + " "
               + fmt(t["worth"], b=_num(belief, lang), v=f"{v:.0f}") + " " + gap)
    svg = f'''<svg viewBox="0 0 640 340" role="img" aria-labelledby="rdcf-t rdcf-d" font-size="13" fill="{P["ink"]}">
<title id="rdcf-t">{escape(t["title"])}</title><desc id="rdcf-d">{escape(t["desc"])}</desc>
{grid}{ticks}
<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="{P["muted"]}" stroke-width="1"/>
<text x="{X1}" y="{Y1 + 38}" text-anchor="end" fill="{P["muted"]}" font-size="12">{escape(t["xaxis"])}</text>
<text x="{X0}" y="12" fill="{P["muted"]}" font-size="12">{escape(t["yaxis"])}</text>
<polyline points="{pts}" fill="none" stroke="{P["value"]}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
<g id="rdcf-belief">
<line id="rdcf-bline" x1="{bx:.1f}" y1="{Y1}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{P["owner"]}" stroke-width="2"/>
<line id="rdcf-bh" x1="{X0}" y1="{by:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{P["owner"]}" stroke-width="1"/>
<rect id="rdcf-bsq" x="{bx - 6:.1f}" y="{by - 6:.1f}" width="12" height="12" fill="{P["value"]}" stroke="{P["paper"]}" stroke-width="2"/>
<text id="rdcf-blab" x="{bx + 12:.1f}" y="{by + 16:.1f}" font-size="13">{escape(blab)}</text>
</g>
<g id="rdcf-price-g">
<line id="rdcf-pline" x1="{X0}" y1="{py:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="{P["price"]}" stroke-width="2"/>
<line id="rdcf-pdrop" x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{Y1}" stroke="{P["price"]}" stroke-width="1"/>
<circle id="rdcf-pdot" cx="{px:.1f}" cy="{py:.1f}" r="6" fill="{P["price"]}" stroke="{P["paper"]}" stroke-width="2"/>
<text id="rdcf-plab" x="{px - 12:.1f}" y="{py - 10:.1f}" text-anchor="end" font-size="13">{escape(plab)}</text>
</g>
<g id="rdcf-hover" visibility="hidden" pointer-events="none">
<line id="rdcf-hline" x1="0" y1="{Y0}" x2="0" y2="{Y1}" stroke="{P["ink"]}" stroke-width="1"/>
<circle id="rdcf-hdot" cx="0" cy="0" r="4" fill="{P["ink"]}" stroke="{P["paper"]}" stroke-width="2"/>
<rect id="rdcf-hbg" x="0" y="0" width="10" height="22" rx="4" fill="{P["ink"]}"/>
<text id="rdcf-htxt" x="0" y="0" fill="{P["paper"]}" font-size="12"> </text>
</g>
<rect id="rdcf-plot" x="{X0}" y="{Y0}" width="{X1 - X0}" height="{Y1 - Y0}" fill="transparent"/>
</svg>'''
    legend = (f'<ul class="xlegend">'
              f'<li><span class="key key-line" style="background:{P["value"]}"></span>{t["leg_curve"]}</li>'
              f'<li><span class="key key-dot" style="background:{P["price"]}"></span>{t["leg_price"]}</li>'
              f'<li><span class="key key-sq" style="background:{P["value"]};outline-color:{P["owner"]}"></span>{t["leg_belief"]}</li>'
              f'</ul>')
    controls = (f'<div class="xcontrols js-only" hidden>'
                f'<label for="rdcf-price">{t["price_label"]}: <output id="rdcf-price-out" for="rdcf-price">{price:.0f}</output> {t["per_share"]}</label>'
                f'<input type="range" id="rdcf-price" min="80" max="400" step="5" value="{price:.0f}">'
                f'<label for="rdcf-belief-in">{t["belief_label"]}: <output id="rdcf-belief-out" for="rdcf-belief-in">{_num(belief, lang)}</output> {t["per_year"]}</label>'
                f'<input type="range" id="rdcf-belief-in" min="-6" max="16" step="0.5" value="{belief}">'
                f'</div>')
    i18n = {k: t[k] for k in ("assumes", "worth", "below", "above", "equal", "plab", "blab", "hover")}
    geo = dict(rate=RATE, term=TERM, years=YEARS, fcf0=FCF0, gmin=GMIN, gmax=GMAX, vmax=VMAX,
               x0=X0, x1=X1, y0=Y0, y1=Y1)
    return (f'<figure class="fig xfig" id="rdcf" data-i18n="{_attr(i18n)}" data-geo="{_attr(geo)}">'
            f'{controls}{svg}{legend}'
            f'<p class="readout" id="rdcf-read" aria-live="polite">{escape(readout)}</p>'
            f'<figcaption>{t["caption"]}</figcaption></figure>')


# ===========================================================================
# 2. where every company stands
# ===========================================================================
UNIVERSE = 2011                  # the screening lists, 2026-09-10 (config/universe/)
COLS, PITCH, SQ = 61, 10, 8
#: the master list of 2026-11-09, in the order the squares are laid
#: (purple, orange, green, hatched, vermillion: every adjacent pair passes)
GROUPS = [("owned", 3, P["owner"]), ("watched", 14, P["price"]), ("candidates", 2, P["passc"]),
          ("review", 13, None), ("no", 74, P["fail"])]

FUNNEL_T = {
    "en": dict(
        title="Where every company stands, 9 November 2026",
        desc="A field of 2,011 small squares, one per company in the screening lists. 106 of them are coloured: 3 owned, 14 watched, 2 candidates, 13 to review and 74 refused. The rest were never read by a person.",
        names=dict(owned="Owned", watched="Watched", candidates="Candidates", review="To review",
                   no="No", unread="Never read"),
        means=dict(
            owned="bought, on a written decision. The tool holds each against its value and its exit every night.",
            watched="valued and waiting: too dear, or behind a gate that only a named event can lift.",
            candidates="valued, and priced under the value. Each still needs a full reading before any order.",
            review="a rough or machine value only. Not yet read by hand.",
            no="refused, each with its reason and what would change it. Measured against the index afterwards.",
            unread="screened by the machine, never opened by a person."),
        all="106 companies looked at, of about two thousand in the lists. Three are owned.",
        caption="Each square is one company. The grey field is the screening lists: 2,011 companies. The 106 coloured squares are every company the method has looked at, drawn on the same field for scale; some of them came from outside these lists. Point at a group below, or tab to it.",
    ),
    "sv": dict(
        title="Var varje bolag står, 9 november 2026",
        desc="Ett fält med 2 011 små rutor, en per bolag i screeninglistorna. 106 av dem är färgade: 3 ägda, 14 bevakade, 2 kandidater, 13 att granska och 74 nej. Resten har aldrig lästs av en människa.",
        names=dict(owned="Ägda", watched="Bevakas", candidates="Kandidater", review="Att granska",
                   no="Nej", unread="Aldrig lästa"),
        means=dict(
            owned="köpta, på ett nedskrivet beslut. Verktyget håller vart och ett mot sitt värde och sin utgång varje natt.",
            watched="värderade och väntande: för dyra, eller bakom en spärr som bara en namngiven händelse kan lyfta.",
            candidates="värderade, och prissatta under värdet. Vart och ett behöver fortfarande en full läsning före en order.",
            review="bara ett grovt värde eller ett maskinvärde. Ännu inte lästa för hand.",
            no="nej, vart och ett med sitt skäl och vad som skulle ändra det. Mäts mot index efteråt.",
            unread="screenade av maskinen, aldrig öppnade av en människa."),
        all="106 bolag har vi tittat på, av omkring tvåtusen i listorna. Tre ägs.",
        caption="Varje ruta är ett bolag. Det grå fältet är screeninglistorna: 2 011 bolag. De 106 färgade rutorna är varje bolag metoden har tittat på, ritade på samma fält för skalans skull; några av dem kom utifrån listorna. Peka på en grupp nedan, eller tabba till den.",
    ),
}


def funnel(lang):
    t = FUNNEL_T[lang]
    rows = -(-UNIVERSE // COLS)
    last = UNIVERSE - (rows - 1) * COLS
    w, h = COLS * PITCH + 8, rows * PITCH + 8
    cells, k = [], 0
    for key, count, colour in GROUPS:
        fill = colour or "url(#funnel-hatch)"
        squares = "".join(
            f'<rect x="{4 + (i % COLS) * PITCH}" y="{4 + (i // COLS) * PITCH}" width="{SQ}" height="{SQ}" rx="1.5" fill="{fill}"'
            + (f' stroke="{P["miss"]}" stroke-width="1"' if colour is None else "") + "/>"
            for i in range(k, k + count))
        cells.append(f'<g class="fgroup" data-group="{key}">{squares}</g>')
        k += count
    looked = k
    # the field: every cell as a pale square, by a pattern; the looked-at cells are painted over it
    field = (f'<rect x="4" y="4" width="{COLS * PITCH}" height="{(rows - 1) * PITCH}" fill="url(#funnel-cell)"/>'
             f'<rect x="4" y="{4 + (rows - 1) * PITCH}" width="{last * PITCH}" height="{PITCH}" fill="url(#funnel-cell)"/>')
    cover = "".join(
        f'<rect x="{4 + (i % COLS) * PITCH - 1}" y="{4 + (i // COLS) * PITCH - 1}" width="{PITCH}" height="{PITCH}" fill="{P["paper"]}"/>'
        for i in range(looked))
    svg = f'''<svg viewBox="0 0 {w} {h}" role="img" aria-labelledby="funnel-t funnel-d">
<title id="funnel-t">{escape(t["title"])}</title><desc id="funnel-d">{escape(t["desc"])}</desc>
<defs>
<pattern id="funnel-cell" patternUnits="userSpaceOnUse" x="4" y="4" width="{PITCH}" height="{PITCH}">
<rect x="0" y="0" width="{SQ}" height="{SQ}" rx="1.5" fill="{P["rule"]}"/></pattern>
<pattern id="funnel-hatch" patternUnits="userSpaceOnUse" width="4" height="4" patternTransform="rotate(45)">
<rect width="4" height="4" fill="{P["miss_f"]}"/><line x1="0" y1="0" x2="0" y2="4" stroke="{P["miss"]}" stroke-width="1.4"/></pattern>
</defs>
<g class="fgroup" data-group="unread">{field}</g>{cover}{"".join(cells)}
</svg>'''
    order = ["owned", "candidates", "watched", "review", "no", "unread"]      # the master list's own order
    count_of = {key: n for key, n, _ in GROUPS}
    count_of["unread"] = UNIVERSE - looked
    colour_of = {key: c for key, _, c in GROUPS}
    items = []
    for key in order:
        if key == "review":
            sw = '<span class="key key-sq key-hatch"></span>'
        elif key == "unread":
            sw = f'<span class="key key-sq" style="background:{P["rule"]}"></span>'
        else:
            sw = f'<span class="key key-sq" style="background:{colour_of[key]}"></span>'
        n = f"{count_of[key]:,}".replace(",", " " if lang == "sv" else ",")
        items.append(f'<li><button type="button" class="fbtn" data-group="{key}">{sw}'
                     f'<span class="fname">{t["names"][key]}</span> <span class="fcount">{n}</span></button>'
                     f'<span class="fmean">{t["means"][key]}</span></li>')
    return (f'<figure class="fig xfig" id="funnel" data-all="{escape(t["all"], quote=True)}">'
            f'{svg}<p class="readout" id="funnel-read" aria-live="polite">{t["all"]}</p>'
            f'<ul class="flist">{"".join(items)}</ul>'
            f'<figcaption>{t["caption"]}</figcaption></figure>')


# ===========================================================================
# 3. the rules graveyard
# ===========================================================================
# (group, name, test, claim, found). Groups: died | kept | hand | open.
GRAVE = {
    "en": dict(
        intro="Open a rule to see what it claimed and what the test found. A rule held only if it helped in both markets and in both halves of each period.",
        groups=dict(died="Removed", kept="Tested and kept", hand="Could not be tested: done by hand",
                    open="Still open"),
        chips=dict(all="All"),
        labels=("It claimed", "The test found"),
        rules=[
            ("died", "The price stop", "attempts 10 and 18 · ruling E162",
             "Selling at a fixed fall under the buy price limits the damage.",
             "No stop level helped any selection, in either market or half. Without buying back, every stop cost heavily. With real trading costs even the mildest one lost money."),
            ("died", "The 15 to 50 percent band", "attempts 8, 12 and 21 · ruling E161",
             "The bargains are among companies that have fallen 15 to 50 percent from their high.",
             "The companies inside the band did no better than the ones outside it, in either market."),
            ("died", "The ranking of the screen", "attempts 8 and 24 · ruling E167",
             "Operating profit against assets, added to operating profit against the price of the whole business, puts the best companies first.",
             "It did not sort later returns by tenths in both markets, and its best fifth trailed the index. The list is now in a fixed random order."),
            ("died", "Warning sign: falling sales", "attempts 17 and 24 · ruling E163",
             "Two quarters of falling sales end the reading.",
             "It did not separate the companies that did well from the ones that did not. It is now information for the growth view."),
            ("died", "Warning sign: a squeezed margin", "attempts 17 and 24 · ruling E163",
             "A sharp fall in the operating margin on flat sales ends the reading.",
             "It did not separate returns."),
            ("died", "Warning sign: swelling invoices and stock", "attempts 17 and 24 · ruling E163",
             "Unpaid invoices or stock growing much faster than sales ends the reading.",
             "It did not separate returns."),
            ("died", "Warning sign: debt above 3.5 times earnings", "attempt 25 · ruling E168",
             "A company that deep in debt is uninvestable.",
             "It did not lift the average outcome. Whether it trims the worst losses is the open question below."),
            ("died", "The screen's debt limit", "attempt 25 · ruling E168",
             "Net debt of at most 2.5 times yearly operating earnings.",
             "It did not separate returns."),
            ("died", "The screen's falling-sales test", "after round 2 · with ruling E163",
             "A company whose sales fall two quarters running is not worth reading.",
             "It went with the warning sign it copied."),
            ("died", "Lower than a year ago", "attempt 25 · ruling E168",
             "Only read a company whose price is below where it stood a year ago.",
             "It did not separate returns."),
            ("died", "The run of falling quarters", "attempt 25 · ruling E168",
             "Three quarters of falling sales in a row is a soft warning.",
             "It did not separate returns."),
            ("died", "The quality tests as a reason to drop", "attempt 25 · ruling E168",
             "A company that fails the first three quality tests is dropped, or sold at its base value.",
             "The tests did not separate the companies that did well. They are still printed, as information. This is the rule that sold CENTA."),
            ("died", "The fourth quality test as a step in confidence", "attempt 25 · ruling E168",
             "A buyer of companies whose purchases earn too little gets a larger cushion.",
             "It did not separate returns."),
            ("died", "The cushion as a binding buy line", "attempt 25 · ruling E168",
             "Buy only at or under 85 percent of the value.",
             "Companies bought under the line did not do better in both markets and both halves. The line is still computed, as information."),
            ("died", "Two green flags", "attempt 25 · ruling E168",
             "Cash flow at least as large as profit, and a rising margin, each raise confidence in a company.",
             "Neither separated returns. They are out of the score."),
            ("died", "The planned cut to growth", "attempt 23 · ruling E160, struck",
             "Growth derived from a company's own history is too high and should be cut.",
             "It was not too high: the growth that followed was above the derived figure. The cut was struck before it was ever used."),
            ("kept", "Three earnings misses in eight reports", "attempt 17",
             "A company that keeps missing its own numbers is one to leave.",
             "The only warning sign with data that separated returns. It stays."),
            ("kept", "At most six percent in one company", "attempt 11 · ruling E157",
             "Spreading the money matters more than picking the best three.",
             "Fewer names did not raise the typical outcome. They only widened the spread: three names are a lottery ticket on the same average."),
            ("kept", "Growth derived from the company's own history", "attempt 23 · ruling E144",
             "A company's own organic growth, capped, is a fair base for its future.",
             "It did not overestimate what followed, on any date or in either half."),
            ("kept", "Positive spare cash", "attempt 25",
             "A business that does not produce cash cannot be valued on its cash.",
             "It could not be tested: every company the method can value has it. It stays, as a condition of the arithmetic."),
            ("hand", "Cuts to the company's own forecast", "no data",
             "Two cuts in four quarters end the reading.",
             "There is no history of forecasts to test it on. It stays, by hand."),
            ("hand", "Both top executives leaving", "no data",
             "The chief executive and the finance chief both gone within a year ends the reading.",
             "No data. It stays, by hand."),
            ("hand", "The sentence on what the company sells", "by hand",
             "If the company's own words cannot say what it sells, to whom, and why they come back, it is not valued.",
             "No history can test a reading. Its test is the shadow book."),
            ("hand", "The belief written before the price", "by hand",
             "A growth view written after seeing the market's number is void.",
             "It cannot be tested on history. The same discipline was applied to these tests themselves."),
            ("open", "Do the debt limits trim the worst losses?", "attempt 26 · April 2027, on new data",
             "The debt limits and the first three quality tests may cut the share of companies that lose most of their value, even if they do not lift the average.",
             "Registered, not yet run. It is measured on the middle outcome and on the share of names losing more than three quarters, on dates no earlier test has read. If it holds, those filters come back."),
            ("open", "The nine-point accounting score", "a candidate, for new data",
             "A known score of nine accounting signals separates strong companies from weak.",
             "It passed once, and later checks weakened it. It is not a rule. It waits for new data."),
        ],
    ),
    "sv": dict(
        intro="Öppna en regel för att se vad den påstod och vad testet fann. En regel höll bara om den hjälpte på båda marknaderna och i båda halvorna av varje period.",
        groups=dict(died="Borttagna", kept="Testade och behållna", hand="Gick inte att testa: görs för hand",
                    open="Fortfarande öppna"),
        chips=dict(all="Alla"),
        labels=("Den påstod", "Testet fann"),
        rules=[
            ("died", "Kursstoppet", "försök 10 och 18 · beslut E162",
             "Att sälja vid ett fast fall under köpkursen begränsar skadan.",
             "Ingen stoppnivå hjälpte något urval, på någon marknad eller i någon halva. Utan återköp kostade varje stopp mycket. Med verkliga handelskostnader förlorade även det mildaste pengar."),
            ("died", "Bandet på 15 till 50 procent", "försök 8, 12 och 21 · beslut E161",
             "Fynden finns bland bolag som har fallit 15 till 50 procent från sin topp.",
             "Bolagen inom bandet gick inte bättre än de utanför, på någon av marknaderna."),
            ("died", "Screeningens rangordning", "försök 8 och 24 · beslut E167",
             "Rörelseresultat mot tillgångar, plus rörelseresultat mot priset på hela företaget, sätter de bästa bolagen först.",
             "Den sorterade inte senare avkastning i tiondelar på båda marknaderna, och dess bästa femtedel låg efter index. Listan står nu i fast slumpordning."),
            ("died", "Varningstecken: fallande försäljning", "försök 17 och 24 · beslut E163",
             "Två kvartal med fallande försäljning avslutar läsningen.",
             "Det skilde inte bolagen som gick bra från dem som inte gjorde det. Det är nu information till tillväxtbedömningen."),
            ("died", "Varningstecken: pressad marginal", "försök 17 och 24 · beslut E163",
             "Ett kraftigt fall i rörelsemarginalen vid oförändrad försäljning avslutar läsningen.",
             "Det skilde inte avkastningen åt."),
            ("died", "Varningstecken: svällande fakturor och lager", "försök 17 och 24 · beslut E163",
             "Obetalda fakturor eller lager som växer mycket snabbare än försäljningen avslutar läsningen.",
             "Det skilde inte avkastningen åt."),
            ("died", "Varningstecken: skuld över 3,5 gånger resultatet", "försök 25 · beslut E168",
             "Ett så skuldsatt bolag går inte att investera i.",
             "Det höjde inte det genomsnittliga utfallet. Om det kapar de värsta förlusterna är den öppna frågan nedan."),
            ("died", "Screeningens skuldgräns", "försök 25 · beslut E168",
             "Nettoskuld på högst 2,5 gånger årets rörelseresultat.",
             "Den skilde inte avkastningen åt."),
            ("died", "Screeningens test för fallande försäljning", "efter omgång 2 · med beslut E163",
             "Ett bolag vars försäljning faller två kvartal i rad är inte värt att läsa.",
             "Det försvann med varningstecknet det kopierade."),
            ("died", "Lägre än för ett år sedan", "försök 25 · beslut E168",
             "Läs bara ett bolag vars kurs ligger under där den stod för ett år sedan.",
             "Det skilde inte avkastningen åt."),
            ("died", "Raden av fallande kvartal", "försök 25 · beslut E168",
             "Tre kvartal i rad med fallande försäljning är en mjuk varning.",
             "Det skilde inte avkastningen åt."),
            ("died", "Kvalitetstesten som skäl att stryka", "försök 25 · beslut E168",
             "Ett bolag som faller på de tre första kvalitetstesten stryks, eller säljs vid sitt basvärde.",
             "Testen skilde inte ut bolagen som gick bra. De skrivs fortfarande ut, som information. Det här är regeln som sålde CENTA."),
            ("died", "Det fjärde kvalitetstestet som steg i förtroende", "försök 25 · beslut E168",
             "En uppköpare vars köp tjänar för lite får en större kudde.",
             "Det skilde inte avkastningen åt."),
            ("died", "Kudden som bindande köplinje", "försök 25 · beslut E168",
             "Köp bara vid eller under 85 procent av värdet.",
             "Bolag köpta under linjen gick inte bättre på båda marknaderna och i båda halvorna. Linjen räknas fortfarande ut, som information."),
            ("died", "Två gröna flaggor", "försök 25 · beslut E168",
             "Kassaflöde minst lika stort som vinsten, och stigande marginal, höjer var för sig förtroendet för ett bolag.",
             "Ingen av dem skilde avkastningen åt. De är ute ur poängen."),
            ("died", "Det planerade avdraget på tillväxten", "försök 23 · beslut E160, struket",
             "Tillväxt härledd ur ett bolags egen historia är för hög och bör kapas.",
             "Den var inte för hög: tillväxten som följde låg över den härledda siffran. Avdraget ströks innan det någonsin användes."),
            ("kept", "Tre vinstmissar på åtta rapporter", "försök 17",
             "Ett bolag som gång på gång missar sina egna tal är ett att lämna.",
             "Det enda varningstecknet med data som skilde avkastningen åt. Det står kvar."),
            ("kept", "Högst sex procent i ett bolag", "försök 11 · beslut E157",
             "Att sprida pengarna betyder mer än att välja de tre bästa.",
             "Färre namn höjde inte det typiska utfallet. De vidgade bara spridningen: tre namn är en lott på samma genomsnitt."),
            ("kept", "Tillväxt härledd ur bolagets egen historia", "försök 23 · beslut E144",
             "Ett bolags egen organiska tillväxt, med tak, är en rimlig grund för dess framtid.",
             "Den överskattade inte vad som följde, vid något datum eller i någon halva."),
            ("kept", "Positivt fritt kassaflöde", "försök 25",
             "En verksamhet som inte ger pengar kan inte värderas på sina pengar.",
             "Det gick inte att testa: varje bolag metoden kan värdera har det. Det står kvar, som ett villkor för räkningen."),
            ("hand", "Sänkta egna prognoser", "ingen data",
             "Två sänkningar på fyra kvartal avslutar läsningen.",
             "Det finns ingen historik över prognoser att testa mot. Det står kvar, för hand."),
            ("hand", "Båda toppcheferna lämnar", "ingen data",
             "Vd och finanschef båda borta inom ett år avslutar läsningen.",
             "Ingen data. Det står kvar, för hand."),
            ("hand", "Meningen om vad bolaget säljer", "för hand",
             "Om bolagets egna ord inte kan säga vad det säljer, till vem och varför de kommer tillbaka, värderas det inte.",
             "Ingen historia kan pröva en läsning. Dess test är skuggboken."),
            ("hand", "Tron nedskriven före priset", "för hand",
             "En tillväxtbedömning som skrivs efter att man sett marknadens tal är ogiltig.",
             "Den går inte att testa mot historien. Samma disciplin tillämpades på de här testerna själva."),
            ("open", "Kapar skuldgränserna de värsta förlusterna?", "försök 26 · april 2027, på ny data",
             "Skuldgränserna och de tre första kvalitetstesten kan minska andelen bolag som förlorar det mesta av sitt värde, även om de inte höjer genomsnittet.",
             "Registrerat, ännu inte kört. Det mäts på det mittersta utfallet och på andelen namn som förlorar mer än tre fjärdedelar, vid datum som inget tidigare test har läst. Håller det, kommer de filtren tillbaka."),
            ("open", "Niopoängaren ur bokföringen", "en kandidat, för ny data",
             "En känd poäng av nio bokföringssignaler skiljer starka bolag från svaga.",
             "Den klarade sig en gång, och senare kontroller försvagade den. Den är ingen regel. Den väntar på ny data."),
        ],
    ),
}

_MARK = dict(died=("✗", "g-died"), kept=("✓", "g-kept"), hand=("?", "g-hand"), open=("…", "g-open"))


def graveyard(lang):
    t = GRAVE[lang]
    counts = {}
    for group, *_ in t["rules"]:
        counts[group] = counts.get(group, 0) + 1
    chips = [f'<button type="button" class="chip" data-show="all" aria-pressed="true">{t["chips"]["all"]} · {len(t["rules"])}</button>']
    blocks = []
    for group in ("died", "kept", "hand", "open"):
        mark, cls = _MARK[group]
        chips.append(f'<button type="button" class="chip" data-show="{group}" aria-pressed="false">'
                     f'<span class="gmark {cls}" aria-hidden="true">{mark}</span>{t["groups"][group]} · {counts[group]}</button>')
        cards = "".join(
            f'<details class="grave"><summary><span class="gmark {cls}" aria-hidden="true">{mark}</span>'
            f'<span class="gname">{name}</span><span class="gtest">{test}</span></summary>'
            f'<dl><dt>{t["labels"][0]}</dt><dd>{claim}</dd><dt>{t["labels"][1]}</dt><dd>{found}</dd></dl></details>'
            for g, name, test, claim, found in t["rules"] if g == group)
        blocks.append(f'<section class="gsection" data-group="{group}"><h3>{t["groups"][group]} '
                      f'<span class="fcount">{counts[group]}</span></h3>{cards}</section>')
    return (f'<div class="xfig graveyard" id="graveyard"><p class="gintro">{t["intro"]}</p>'
            f'<div class="chips js-only" hidden>{"".join(chips)}</div>{"".join(blocks)}</div>')


# ===========================================================================
# 4. the shadow book so far
# ===========================================================================
#: refusals (DROPPED and WATCH-GATED rows of config/shadow_book.csv), counted
#: from `vss shadow --dry-run` on 2026-11-09 against the S&P 500 total return
#: in each name's own currency: (horizon in months, behind, ahead, too early).
REFUSALS = 32
SHADOW = [(1, 12, 5, 15), (3, 0, 0, 32), (6, 0, 0, 32), (12, 0, 0, 32)]

SHADOW_T = {
    "en": dict(
        title="The shadow book so far, 9 November 2026",
        desc="Four bars, one per horizon, each for the same 32 refusals. At one month, 12 had done worse than the index, 5 better, and 15 were not yet a month old or had no starting price. At three, six and twelve months all 32 are still too early to measure.",
        horizon={1: "after 1 month", 3: "after 3 months", 6: "after 6 months", 12: "after 12 months"},
        behind="did worse than the index", ahead="did better than the index",
        wait="too early, or no settled starting price",
        tip="{h}: {n} of 32 refusals {what}.",
        default="32 refusals since August 2026. Only the one-month mark has begun to fill.",
        caption="Each bar is the same 32 refusals. The dark part did worse than the index over that horizon, the pale part did better, the hatched part cannot be measured yet. A refusal that did worse than the index is not thereby right, and one that did better is not thereby wrong: the book measures what happened, never why. It is read once a year, and this is why: there is almost nothing in it yet.",
    ),
    "sv": dict(
        title="Skuggboken hittills, 9 november 2026",
        desc="Fyra staplar, en per horisont, var och en för samma 32 nej. Efter en månad hade 12 gått sämre än index, 5 bättre, och 15 var ännu inte en månad gamla eller saknade startkurs. Efter tre, sex och tolv månader är alla 32 fortfarande för tidiga att mäta.",
        horizon={1: "efter 1 månad", 3: "efter 3 månader", 6: "efter 6 månader", 12: "efter 12 månader"},
        behind="gick sämre än index", ahead="gick bättre än index",
        wait="för tidigt, eller ingen fastställd startkurs",
        tip="{h}: {n} av 32 nej {what}.",
        default="32 nej sedan augusti 2026. Bara enmånadsmärket har börjat fyllas.",
        caption="Varje stapel är samma 32 nej. Den mörka delen gick sämre än index över den horisonten, den ljusa gick bättre, den streckade går inte att mäta ännu. Ett nej som gick sämre än index har inte därmed rätt, och ett som gick bättre har inte därmed fel: boken mäter vad som hände, aldrig varför. Den läses en gång om året, och det här är skälet: det står nästan ingenting i den ännu.",
    ),
}


def shadow(lang):
    t = SHADOW_T[lang]
    left, width, bar_h, gap = 150, 470, 26, 16
    unit = width / REFUSALS
    rows, y = [], 12
    for months, behind, ahead, wait in SHADOW:
        x = left
        segs = []
        for n, kind, fill, ink in ((behind, "behind", P["muted"], P["paper"]),
                                   (ahead, "ahead", P["rule"], P["ink"]),
                                   (wait, "wait", "url(#shadow-hatch)", P["ink"])):
            if not n:
                continue
            wseg = n * unit
            tip = t["tip"].format(h=t["horizon"][months], n=n, what=t[kind])
            label = ""
            if kind == "wait" and wseg >= 40:
                label = (f'<rect x="{x + 5:.1f}" y="{y + 4:.1f}" width="26" height="{bar_h - 8}" rx="3" fill="{P["paper"]}" pointer-events="none"/>'
                         f'<text x="{x + 18:.1f}" y="{y + bar_h / 2 + 4.5:.1f}" text-anchor="middle" fill="{P["ink"]}" font-size="13" '
                         f'font-weight="600" pointer-events="none">{n}</text>')
            elif kind != "wait" and wseg >= 26:
                label = (f'<text x="{x + 8:.1f}" y="{y + bar_h / 2 + 4.5:.1f}" fill="{ink}" font-size="13" '
                         f'font-weight="600" pointer-events="none">{n}</text>')
            segs.append(f'<g class="sseg" tabindex="0" role="img" aria-label="{escape(tip, quote=True)}" data-tip="{escape(tip, quote=True)}">'
                        f'<rect x="{x + 1:.1f}" y="{y}" width="{wseg - 2:.1f}" height="{bar_h}" rx="4" fill="{fill}"/>{label}</g>')
            x += wseg
        rows.append(f'<text x="{left - 10}" y="{y + bar_h / 2 + 4.5:.1f}" text-anchor="end" font-size="13">{t["horizon"][months]}</text>'
                    + "".join(segs))
        y += bar_h + gap
    h = y
    svg = f'''<svg viewBox="0 0 640 {h}" role="img" aria-labelledby="shadow-t shadow-d" font-size="13" fill="{P["ink"]}">
<title id="shadow-t">{escape(t["title"])}</title><desc id="shadow-d">{escape(t["desc"])}</desc>
<defs><pattern id="shadow-hatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
<rect width="6" height="6" fill="{P["miss_f"]}"/><line x1="0" y1="0" x2="0" y2="6" stroke="{P["miss"]}" stroke-width="1.6"/></pattern></defs>
{"".join(rows)}
</svg>'''
    legend = (f'<ul class="xlegend">'
              f'<li><span class="key key-sq" style="background:{P["muted"]}"></span>{t["behind"]}</li>'
              f'<li><span class="key key-sq" style="background:{P["rule"]}"></span>{t["ahead"]}</li>'
              f'<li><span class="key key-sq key-hatch"></span>{t["wait"]}</li></ul>')
    return (f'<figure class="fig xfig" id="shadow" data-default="{escape(t["default"], quote=True)}">'
            f'{svg}{legend}<p class="readout" id="shadow-read" aria-live="polite">{t["default"]}</p>'
            f'<figcaption>{t["caption"]}</figcaption></figure>')


FIGS = {"rdcf": rdcf, "funnel": funnel, "graveyard": graveyard, "shadow": shadow}
