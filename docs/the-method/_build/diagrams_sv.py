"""Inline SVG figures for the site. Every figure answers one question a
reader would ask, is readable before its caption, and uses the five
meaning colours from RESEARCH-NOTES.md Track C, never as the only signal.

Design width is 480 units (portrait figures 420) so that at a 360 px phone
the 13-unit labels still render near 10 px. Wide screens enlarge them.
"""

from html import escape

P = dict(
    ink="#1B1B1B", muted="#5A5A5A", paper="#FBFAF7", rule="#C9C6BF", surface="#F1EFE9",
    value="#0072B2", value_t="#005A8E", value_f="#D1E6F1",
    price="#E69F00", price_t="#8A5A00", price_f="#FAEED1",
    pass_="#009E73", pass_t="#00714F", pass_f="#D1EEE6",
    fail="#D55E00", fail_t="#A34500", fail_f="#F7E2D1",
    miss="#767676", miss_t="#5C5C5C", miss_f="#E6E6E6",
    owner="#CC79A7", owner_t="#8B4A70", owner_f="#F6E7EF",
)

_counter = [0]


def svg(fid, w, h, title, desc, body):
    """Wrap a figure. role=img + title/desc referenced by aria-labelledby."""
    _counter[0] += 1
    defs = f"""<defs>
<pattern id="{fid}-hatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
<rect width="6" height="6" fill="{P['miss_f']}"/><line x1="0" y1="0" x2="0" y2="6" stroke="{P['miss']}" stroke-width="1.6"/></pattern>
<marker id="{fid}-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="{P['ink']}"/></marker>
<marker id="{fid}-arr-pass" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="{P['pass_t']}"/></marker>
<marker id="{fid}-arr-fail" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="{P['fail_t']}"/></marker>
<marker id="{fid}-arr-owner" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="{P['owner_t']}"/></marker>
</defs>"""
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-labelledby="{fid}-t {fid}-d" '
            f'font-size="13" fill="{P["ink"]}">'
            f'<title id="{fid}-t">{escape(title)}</title><desc id="{fid}-d">{escape(desc)}</desc>'
            f'{defs}{body}</svg>')


def figure(fid, w, h, title, desc, body, caption):
    return (f'<figure class="fig" id="{fid}">'
            f'{svg(fid, w, h, title, desc, body)}'
            f'<figcaption>{caption}</figcaption></figure>')


def text(x, y, s, anchor="start", size=13, color=None, weight=None, italic=False):
    attrs = f'x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}"'
    if color:
        attrs += f' fill="{color}"'
    if weight:
        attrs += f' font-weight="{weight}"'
    if italic:
        attrs += ' font-style="italic"'
    return f'<text {attrs}>{escape(s)}</text>'


def lines(x, y, rows, anchor="start", size=13, color=None, weight=None, lh=None):
    """Several lines of text, first at y, subsequent by line height."""
    lh = lh or round(size * 1.25)
    out = []
    for i, r in enumerate(rows):
        out.append(text(x, y + i * lh, r, anchor, size, color, weight))
    return "".join(out)


def box(x, y, w, h, rows, fill, stroke, size=13, weight=None, rx=5, sw=2, color=None, dash=None):
    """A labelled rounded box; label lines centred."""
    lh = round(size * 1.25)
    total = lh * len(rows)
    ty = y + h / 2 - total / 2 + size * 0.85
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'
            + lines(x + w / 2, ty, rows, "middle", size, color or P["ink"], weight, lh))


def hbox(fid, x, y, w, h, rows, size=13, weight=None, ow=124):
    """A hatched 'missing' box; ow is the width of the paper label plate."""
    lh = round(size * 1.25)
    total = lh * len(rows)
    ty = y + h / 2 - total / 2 + size * 0.85
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="url(#{fid}-hatch)" stroke="{P["miss"]}" stroke-width="2"/>'
            f'<rect x="{x + w/2 - ow/2}" y="{ty - size}" width="{ow}" height="{total + 4}" rx="3" fill="{P["paper"]}" opacity="0.94"/>'
            + lines(x + w / 2, ty, rows, "middle", size, P["miss_t"], weight, lh))


def arrow(fid, x1, y1, x2, y2, kind="", width=2, dash=None):
    m = f"{fid}-arr" + (f"-{kind}" if kind else "")
    col = {"": P["ink"], "pass": P["pass_t"], "fail": P["fail_t"], "owner": P["owner_t"]}[kind]
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{width}" marker-end="url(#{m})"{d}/>'


def path_arrow(fid, d, kind="", width=2, dash=None):
    m = f"{fid}-arr" + (f"-{kind}" if kind else "")
    col = {"": P["ink"], "pass": P["pass_t"], "fail": P["fail_t"], "owner": P["owner_t"]}[kind]
    dd = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{width}" marker-end="url(#{m})"{dd}/>'


def wall(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{P["ink"]}" stroke-width="5"/>'


def tick(x, y, size=14):
    s = size
    return (f'<path d="M{x - s*0.45},{y} L{x - s*0.1},{y + s*0.35} L{x + s*0.5},{y - s*0.4}" '
            f'fill="none" stroke="{P["pass_t"]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')


def cross(x, y, size=14):
    s = size * 0.42
    return (f'<path d="M{x - s},{y - s} L{x + s},{y + s} M{x + s},{y - s} L{x - s},{y + s}" '
            f'fill="none" stroke="{P["fail_t"]}" stroke-width="3" stroke-linecap="round"/>')


def qmark(x, y, size=15):
    return text(x, y + size * 0.36, "?", "middle", size, P["miss_t"], 700)


def sq(x, y, s=8, fill=None, stroke=None):
    return f'<rect x="{x - s/2}" y="{y - s/2}" width="{s}" height="{s}" fill="{fill or P["value_f"]}" stroke="{stroke or P["value"]}" stroke-width="2"/>'


def circ(x, y, r=4.5, fill=None, stroke=None):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill or P["price_f"]}" stroke="{stroke or P["price_t"]}" stroke-width="2"/>'


# ---------------------------------------------------------------------------
# PART ONE
# ---------------------------------------------------------------------------

def fig_price_vs_value():
    fid = "f-gap"
    W, H = 480, 260
    b = []
    # axes
    b.append(f'<line x1="40" y1="215" x2="460" y2="215" stroke="{P["rule"]}" stroke-width="1.5"/>')
    b.append(f'<line x1="40" y1="30" x2="40" y2="215" stroke="{P["rule"]}" stroke-width="1.5"/>')
    b.append(text(250, 240, "tid", "middle", 12, P["muted"]))
    b.append(text(14, 125, "värde", "middle", 12, P["muted"]).replace("<text", '<text transform="rotate(-90 14 125)"'))
    # value line (slow rise)
    vpts = [(60, 150), (160, 140), (260, 128), (360, 118), (440, 110)]
    b.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in vpts) +
             f'" fill="none" stroke="{P["value"]}" stroke-width="3"/>')
    for x, y in vpts:
        b.append(sq(x, y))
    # price line (zigzag)
    ppts = [(60, 120), (95, 165), (130, 95), (165, 150), (200, 180), (235, 130), (270, 70), (305, 120),
            (340, 160), (375, 95), (410, 135), (440, 80)]
    b.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in ppts) +
             f'" fill="none" stroke="{P["price"]}" stroke-width="2.5"/>')
    for x, y in ppts:
        b.append(circ(x, y))
    # the gap at x=200 (price 180 below value ~135)
    b.append(f'<line x1="200" y1="180" x2="200" y2="135" stroke="{P["ink"]}" stroke-width="2" stroke-dasharray="3 3"/>')
    b.append(text(208, 165, "gapet", "start", 13, P["ink"], 600))
    b.append(text(208, 181, "kurs under värde", "start", 11, P["muted"]))
    # gap the other way at 270
    b.append(f'<line x1="270" y1="70" x2="270" y2="126" stroke="{P["ink"]}" stroke-width="2" stroke-dasharray="3 3"/>')
    b.append(text(278, 84, "kurs över värde", "start", 11, P["muted"]))
    # legend
    b.append(sq(62, 22))
    b.append(text(72, 26, "värde: vad bolaget är värt, rör sig långsamt", "start", 12, P["value_t"]))
    b.append(circ(62, 42))
    b.append(text(72, 46, "kurs: vad marknaden noterar, rör sig dagligen", "start", 12, P["price_t"]))
    return figure(fid, W, H,
                  "Kurs mot värde över tid",
                  "En långsamt stigande blå linje med kvadratiska markörer visar ett bolags värde. En orange sicksackkurva med runda markörer visar dess noterade kurs som korsar värdelinjen uppåt och nedåt. Streckade lodräta linjer markerar gapet där kursen ligger under värdet och där den ligger över.",
                  "".join(b),
                  "Två tal för ett och samma bolag. De blå kvadraterna är vad det är värt; de orange cirklarna är vad det noteras till. Gapet mellan dem är hela möjligheten, och det öppnar sig åt båda hållen.")



def fig_margin_of_safety():
    fid = "f-mos"
    W, H = 480, 230
    b = []
    x0, x1 = 40, 440
    y = 110

    def X(v):
        return x0 + (x1 - x0) * v / 100

    # value bar 0..100, solid tint up to 85, cushion 85..100 as paper with dashed blue edge
    b.append(f'<rect x="{x0}" y="{y}" width="{X(85)-x0}" height="28" fill="{P["value_f"]}" stroke="none"/>')
    b.append(f'<rect x="{X(85)}" y="{y}" width="{x1-X(85)}" height="28" fill="{P["paper"]}" stroke="{P["value"]}" stroke-width="2" stroke-dasharray="4 3"/>')
    b.append(f'<rect x="{x0}" y="{y}" width="{x1-x0}" height="28" fill="none" stroke="{P["value"]}" stroke-width="2"/>')
    # value end
    b.append(sq(x1, y + 14, 10))
    b.append(text(x1, y - 14, "din värdeuppskattning: 100", "end", 13, P["value_t"], 600))
    # tier lines
    for v, lab, tier in ((85, "85", "nivå 1"), (75, "75", "nivå 2"), (65, "65", "nivå 3")):
        b.append(f'<line x1="{X(v)}" y1="{y-6}" x2="{X(v)}" y2="{y+34}" stroke="{P["value_t"]}" stroke-width="2"/>')
        b.append(text(X(v), y + 50, lab, "middle", 12, P["value_t"], 600))
        b.append(text(X(v), y + 64, tier, "middle", 10.5, P["muted"]))
    b.append(text(X(85), y + 82, "högsta pris du betalar, per nivå", "middle", 11.5, P["ink"]).replace(f'x="{X(85)}"', f'x="{X(75)}"'))
    # cushion label
    b.append(text(X(92.5), y - 40, "bufferten", "middle", 12, P["ink"], 600))
    b.append(text(X(92.5), y - 27, "utrymme för fel", "middle", 10.5, P["muted"]))
    # price example
    b.append(circ(X(70), y + 14, 7))
    b.append(text(X(70), y - 40, "kurs i dag: 70", "end", 12, P["price_t"], 600))
    b.append(text(X(70), y - 27, "under varje linje", "end", 10.5, P["muted"]))
    b.append(f'<line x1="{X(70)}" y1="{y-22}" x2="{X(70)}" y2="{y+4}" stroke="{P["price_t"]}" stroke-width="1.5" stroke-dasharray="3 2"/>')
    b.append(text(x0, y + 50, "0", "middle", 12, P["muted"]))
    b.append(text(240, y + 108, "din uppskattning kan ha fel med 15, 25 eller 35 och du betalade ändå under värdet", "middle", 10.5, P["muted"]))
    return figure(fid, W, H,
                  "Säkerhetsmarginal som en buffert under det uppskattade värdet",
                  "Ett vågrätt fält från 0 till 100 föreställer det uppskattade värdet. Delen från 85 till 100 är ritad som ett tomt streckat område med texten bufferten, utrymme för fel. Lodräta linjer vid 85, 75 och 65 markerar det högsta ägaren skulle betala per nivå. En orange cirkel vid 70 markerar dagens kurs, under varje linje.",
                  "".join(b),
                  "Säkerhetsmarginal. Du tror att bolaget är värt 100. Du vägrar betala mer än 85, eller 75, eller 65, beroende på hur säker du är. Bufferten är utrymmet för att din uppskattning ska ha fel.")


def fig_screen_filter():
    fid = "f-sieve"
    W, H = 420, 480
    b = []
    cx = 210
    rows = [
        (400, ["cirka 2 000 börsnoterade bolag"], P["surface"], P["ink"]),
        (384, ["steg 0: bolag du redan äger eller", "redan avgjorda tas bort"], P["surface"], P["ink"]),
        (368, ["filter 1: kurs 15–50 % under 52-veckorshögsta;", "noterat minst fem år; inom cirkeln"], P["surface"], P["ink"]),
        (352, ["filter 2: positivt kassaflöde; skuld under ett", "angivet tak; omsättning ej fallande två kvartal"], P["surface"], P["ink"]),
        (320, ["rankas på två tal:", "lönsamhet och vinstavkastning"], P["surface"], P["ink"]),
        (240, ["cirka 20 bevakas för kursen"], P["value_f"], P["value"]),
        (180, ["3–5 läses för hand"], P["owner_f"], P["owner_t"]),
    ]
    y = 16
    for w, label, fill, stroke in rows:
        h = 46 if len(label) > 1 else 36
        b.append(box(cx - w / 2, y, w, h, label, fill, stroke, 12))
        y += h + 14
        if w != 180:
            b.append(arrow(fid, cx, y - 14, cx, y - 2))
    b.append(text(cx, y + 4, "Ordningen på gallringen, inte uppmätta antal.", "middle", 11, P["muted"]))
    b.append(text(cx, y + 20, "Det som faller bort är inte bedömt. Det är inte läst.", "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "Screeningen som ett grovt filter",
                  "En stapel rutor som smalnar av från cirka tvåtusen bolag överst, via ett uteslutningssteg, två filter och en rangordning, till cirka tjugo bevakade bolag och tre till fem som läses för hand underst.",
                  "".join(b),
                  "Screeningen tar bara bort. Varje steg ställer en grov fråga och släpper igenom det som det inte kan hitta fel på. Inget som faller bort har bedömts; det har helt enkelt inte lästs.")


def fig_name_fails_gate():
    fid = "f-gate"
    W, H = 480, 290
    b = []
    b.append(lines(20, 26, ["bara ett namngivet nytt faktum öppnar en fallerad spärr:", "en rapport, ändrad prognos, vinstvarning. Aldrig en nivå i en graf."], "start", 11, P["muted"]))
    b.append(box(20, 82, 90, 50, ["BOLAG A"], P["surface"], P["ink"], 13, 600))
    b.append(arrow(fid, 112, 107, 146, 107))
    b.append(box(148, 70, 116, 74, ["spärr 1", "hur mycket har", "kursen fallit?"], P["pass_f"], P["pass_"], 12))
    b.append(tick(258, 76))
    b.append(arrow(fid, 266, 107, 300, 107, "pass"))
    b.append(box(302, 70, 158, 74, ["spärr 2: varför föll?", "klass D:", "bestående skada"], P["fail_f"], P["fail"], 12))
    b.append(cross(452, 76))
    b.append(arrow(fid, 381, 146, 381, 182, "fail"))
    b.append(box(222, 184, 238, 46, ["ut: WATCH-GATED eller DROPPED"], P["surface"], P["ink"], 12, 600))
    # a lower price does not bring it back: dashed line along the bottom, crossed at NAME A
    b.append(f'<path d="M 222 207 L 65 207 L 65 140" fill="none" stroke="{P["fail_t"]}" stroke-width="2" stroke-dasharray="5 4"/>')
    b.append(cross(65, 140, 16))
    b.append(lines(20, 236, ["en lägre kurs senare för det inte tillbaka:", "spärren föll på något annat än kursen"], "start", 11, P["fail_t"]))
    return figure(fid, W, H,
                  "Ett bolag som faller på en spärr",
                  "BOLAG A passerar spärr 1 med en bock och når spärr 2, där fallet klassas som bestående skada och faller med ett kryss. En pil leder ner till en ruta med texten ut: WATCH-GATED eller DROPPED. En streckad linje från den rutan tillbaka mot BOLAG A slutar i ett kryss, med texten: en lägre kurs senare för det inte tillbaka.",
                  "".join(b),
                  "BOLAG A föll tillräckligt långt för att passera spärr 1. Spärr 2 frågar varför det föll; svaret är bestående skada, och det är ett underkännande. Bolaget lämnar. En lägre kurs senare för det inte tillbaka; bara ett namngivet nytt faktum kan det.")


def fig_dcf_vs_reverse():
    fid = "f-inv"
    W, H = 480, 240
    b = []
    b.append(text(20, 30, "vanliga vägen", "start", 13, P["muted"], 600))
    b.append(box(20, 40, 126, 56, ["en tillväxt", "du antar"], P["owner_f"], P["owner_t"], 12))
    b.append(arrow(fid, 148, 68, 172, 68))
    b.append(box(174, 40, 126, 56, ["uträkningen"], P["surface"], P["ink"], 12))
    b.append(arrow(fid, 302, 68, 326, 68))
    b.append(box(328, 40, 132, 56, ["ett värde, sedan", "jämför med kursen"], P["value_f"], P["value"], 11.5))
    b.append(text(240, 118, '"vad är det värt?" — din gissning in, ett tal ut', "middle", 11, P["muted"]))
    b.append(text(20, 150, "det omvända", "start", 13, P["muted"], 600))
    b.append(box(20, 160, 126, 56, ["kursen", "som noteras i dag"], P["price_f"], P["price_t"], 12))
    b.append(arrow(fid, 148, 188, 172, 188))
    b.append(box(174, 160, 126, 56, ["samma uträkning,", "körd baklänges"], P["surface"], P["ink"], 11.5))
    b.append(arrow(fid, 302, 188, 326, 188))
    b.append(box(328, 160, 132, 56, ["tillväxten som", "kursen antar"], P["value_f"], P["value"], 11.5))
    b.append(text(240, 236, '"tror jag på det?" — ett tal in, en fråga du kan bedöma ut', "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "En vanlig värdering mot en omvänd",
                  "Övre raden: en tillväxt du antar går in i uträkningen och ett värde kommer ut, att jämföra med kursen. Nedre raden: den noterade kursen går in i samma uträkning körd baklänges, och tillväxten som kursen antar kommer ut.",
                  "".join(b),
                  "Samma uträkning, motsatt riktning. Det vanliga sättet stoppar in din gissning och får ett tal ut. Det omvända stoppar in marknadens tal och får marknadens gissning ut, som du sedan kan bedöma.")

def fig_two_orderings():
    fid = "f-order"
    W, H = 480, 270
    b = []
    # Wrong ordering
    b.append(text(20, 26, "ordning A: titta, sedan skriv", "start", 13, P["fail_t"], 600))
    b.append(cross(240, 21))
    b.append(box(20, 40, 120, 56, ["lös ut tillväxten", "som kursen antar"], P["price_f"], P["price_t"], 12))
    b.append(arrow(fid, 142, 68, 178, 68))
    b.append(box(180, 40, 120, 56, ["skriv din egen", "tillväxtbedömning"], P["owner_f"], P["owner_t"], 12))
    b.append(path_arrow(fid, "M 240 98 C 240 120, 100 120, 90 100", "fail", 2, "4 3"))
    b.append(text(170, 128, "bedömningen glider mot talet du just sett", "middle", 11, P["fail_t"]))
    b.append(box(320, 40, 140, 56, ["VOID för bolaget", "i den här cykeln"], P["fail_f"], P["fail"], 12, 600))
    b.append(arrow(fid, 302, 68, 318, 68, "fail"))
    # Right ordering
    b.append(text(20, 166, "ordning B: skriv, sedan titta", "start", 13, P["pass_t"], 600))
    b.append(tick(240, 161))
    b.append(box(20, 180, 120, 56, ["skriv din tillväxt-", "bedömning med skäl,", "tidsstämplad"], P["owner_f"], P["owner_t"], 11))
    b.append(arrow(fid, 142, 208, 178, 208))
    b.append(box(180, 180, 120, 56, ["lös ut tillväxten", "som kursen antar"], P["price_f"], P["price_t"], 12))
    b.append(arrow(fid, 302, 208, 318, 208, "pass"))
    b.append(box(320, 180, 140, 56, ["jämför: begär marknaden", "mer än vad du", "tror på?"], P["value_f"], P["value"], 11))
    b.append(text(240, 258, "tidsstämpeln bevisar ordningen", "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "De två ordningarna i förregistrering",
                  "Ordning A, markerad med ett kryss: lös ut tillväxten som kursen antar, skriv sedan din egen bedömning; en streckad pil visar bedömningen som glider mot talet du just sett; resultatet är VOID. Ordning B, markerad med en bock: skriv din bedömning först med tidsstämpel, lös sedan ut, jämför därefter.",
                  "".join(b),
                  "Samma två steg i två ordningar. I A ses marknadens tal först och drar bedömningen mot sig. I B finns bedömningen i registret innan talet existerar, och registrets tidsstämpel är beviset.")


def fig_three_doors():
    fid = "f-doors"
    W, H = 480, 250
    b = []
    doors = [
        (30, "PASS", P["pass_f"], P["pass_"], ["testet kördes", "och siffran", "klarade det"], "tick"),
        (180, "FAIL", P["fail_f"], P["fail"], ["testet kördes", "och siffran", "klarade det inte"], "cross"),
        (330, "DATA SAKNAS", None, P["miss"], ["testet kunde", "inte köras:", "siffran saknas"], "q"),
    ]
    for x, label, fill, stroke, rows, mark in doors:
        if fill:
            b.append(f'<rect x="{x}" y="30" width="120" height="150" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>')
        else:
            b.append(f'<rect x="{x}" y="30" width="120" height="150" rx="8" fill="url(#{fid}-hatch)" stroke="{stroke}" stroke-width="2.5"/>')
            b.append(f'<rect x="{x+10}" y="40" width="100" height="130" rx="5" fill="{P["paper"]}" opacity="0.9"/>')
        if mark == "tick":
            b.append(tick(x + 60, 66, 26))
        elif mark == "cross":
            b.append(cross(x + 60, 66, 26))
        else:
            b.append(qmark(x + 60, 66, 30))
        col = {"PASS": P["pass_t"], "FAIL": P["fail_t"], "DATA SAKNAS": P["miss_t"]}[label]
        b.append(text(x + 60, 104, label, "middle", 13, col, 700))
        b.append(lines(x + 60, 126, rows, "middle", 11, P["ink"]))
    # forbidden merge
    b.append(f'<path d="M 330 200 C 300 230, 330 230, 300 200" fill="none" stroke="none"/>')
    b.append(f'<line x1="326" y1="205" x2="304" y2="205" stroke="{P["fail_t"]}" stroke-width="2" stroke-dasharray="4 3"/>')
    b.append(cross(315, 205, 16))
    b.append(text(240, 230, "den tredje dörren räknas aldrig tyst som den andra", "middle", 12, P["ink"], 600))
    return figure(fid, W, H,
                  "PASS, FAIL och DATA SAKNAS som tre dörrar",
                  "Tre dörrar sida vid sida: en grön dörr med en bock märkt PASS, testet kördes och siffran klarade det; en rödorange dörr med ett kryss märkt FAIL, testet kördes och siffran klarade det inte; en grå snedstreckad dörr med ett frågetecken märkt DATA SAKNAS, testet kunde inte köras. En överkryssad streckad linje mellan den tredje och andra dörren säger att den tredje aldrig tyst räknas som den andra.",
                  "".join(b),
                  "Tre utfall, tre dörrar. Den tredje är inte en svagare version av den andra. Ett test som inte kunde köras har inte sagt dig något om bolaget, men något om din data.")



def fig_funnel():
    fid = "f-funnel"
    W, H = 420, 520
    b = []
    cx = 150
    b.append(box(cx - 90, 20, 180, 54, ["INTAKE", "läst, inte bevakat"], P["surface"], P["ink"], 12))
    b.append(arrow(fid, cx, 76, cx, 104, "owner"))
    b.append(text(cx + 8, 96, "ägaren för in det", "start", 11, P["owner_t"]))
    b.append(box(cx - 90, 106, 180, 54, ["PIPELINE", "införd; spärr 1 fryst"], P["surface"], P["ink"], 12))
    b.append(arrow(fid, cx, 162, cx, 190, "owner"))
    b.append(text(cx + 8, 182, "ägaren läser och värderar", "start", 11, P["owner_t"]))
    b.append(box(20, 192, 130, 92, ["WATCH-GATED", "föll på något annat", "än kursen; åter bara", "vid ett namngivet nytt", "faktum, aldrig en kurs"], P["fail_f"], P["fail"], 10.5))
    b.append(box(170, 192, 130, 92, ["WATCH-PRICED", "läsningen är klar;", "bara kursen står", "i vägen"], P["value_f"], P["value"], 10.5))
    b.append(arrow(fid, 235, 286, 235, 318, "owner"))
    b.append(lines(227, 300, ["kursen når linjen:", "ägaren köper"], "end", 11, P["owner_t"]))
    b.append(box(170, 320, 130, 54, ["HELD", "ägd, med stopp"], P["owner_f"], P["owner_t"], 12, 600))
    # dropped column
    b.append(f'<rect x="330" y="20" width="70" height="354" rx="6" fill="url(#{fid}-hatch)" stroke="{P["miss"]}" stroke-width="2"/>')
    b.append(f'<rect x="338" y="164" width="54" height="60" rx="4" fill="{P["paper"]}" opacity="0.94"/>')
    b.append(lines(365, 186, ["DROPPED", "inte", "bevakat"], "middle", 11, P["miss_t"], 600))
    for x1, y in ((240, 47), (240, 133), (302, 238), (302, 347)):
        b.append(arrow(fid, x1, y, 328, y, "fail", 1.5, "3 3"))
    b.append(lines(20, 402, ["Det som får ett bolag att falla bort: en fallerad spärr, en",
                             "klass D-orsak till fallet, en hård diskvalificering i bokslutet,",
                             "ett bolag utanför cirkeln, ett brutet stopp. Verktyget mäter",
                             "och pekar; varje flytt mellan rutorna är ägarens handling."],
                   "start", 10.5, P["muted"]))
    b.append(text(20, 476, "lila pilar: ägaren agerar", "start", 11, P["owner_t"]))
    b.append(text(20, 494, "streckad rödorange: bolag faller bort", "start", 11, P["fail_t"]))
    b.append(text(20, 512, "snedstreckad grå: ej längre bevakad", "start", 11, P["miss_t"]))
    return figure(fid, W, H,
                  "Tratten: sex statusar och hur ett bolag rör sig mellan dem",
                  "Rutor uppifrån och ned: INTAKE, PIPELINE, sedan en delning i WATCH-GATED och WATCH-PRICED, därefter HELD. Lila pilar mellan dem är märkta med ägarens handlingar. Streckade rödorange pilar leder från varje ruta in i en snedstreckad grå kolumn märkt DROPPED, inte bevakat. Rutan WATCH-GATED säger att bolaget kommer tillbaka bara vid ett namngivet nytt faktum, aldrig en kurs.",
                  "".join(b),
                  "De sex statusar ett bolag kan ha, från läst till ägt. Varje steg nedåt är ägarens beslut. Verktyget flyttar aldrig ett bolag; det mäter var vart och ett står och säger det.")


def fig_buy_price():
    fid = "f-buy"
    W, H = 420, 400
    b = []
    x = 140
    top, bot = 44, 318
    b.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bot}" stroke="{P["rule"]}" stroke-width="2"/>')

    def Y(v):
        return bot - (bot - top) * v / 120

    b.append(f'<rect x="{x-8}" y="{Y(100)}" width="16" height="{Y(85)-Y(100)}" fill="{P["value_f"]}" stroke="none"/>')
    b.append(f'<line x1="{x-16}" y1="{Y(100)}" x2="{x+16}" y2="{Y(100)}" stroke="{P["value"]}" stroke-width="3"/>')
    b.append(sq(x, Y(100), 10))
    b.append(text(x + 24, Y(100) + 4, "värde, basfall: 100", "start", 12, P["value_t"], 600))
    b.append(text(x + 24, Y(100) + 18, "från ägarens egen tillväxtbedömning", "start", 10.5, P["muted"]))
    b.append(f'<line x1="{x-16}" y1="{Y(85)}" x2="{x+16}" y2="{Y(85)}" stroke="{P["value_t"]}" stroke-width="3"/>')
    b.append(text(x + 24, Y(85) + 4, "högsta pris ägaren betalar: 85", "start", 12, P["value_t"], 600))
    b.append(text(x + 24, Y(85) + 18, "värde × 0.85 (nivå 1), 0.75 (nivå 2), 0.65 (nivå 3)", "start", 10.5, P["muted"]))
    b.append(circ(x, Y(93), 7))
    b.append(text(x - 24, Y(93) + 4, "kurs i dag: 93", "end", 12, P["price_t"], 600))
    b.append(text(x - 24, Y(93) + 18, "över linjen: vänta", "end", 10.5, P["muted"]))
    b.append(f'<line x1="{x-16}" y1="{Y(62)}" x2="{x+16}" y2="{Y(62)}" stroke="{P["fail"]}" stroke-width="3"/>')
    b.append(cross(x, Y(62), 14))
    b.append(text(x + 24, Y(62) + 4, "stopp: sälj om den faller hit", "start", 12, P["fail_t"], 600))
    b.append(text(x + 24, Y(62) + 18, "satt före köpet, aldrig efter", "start", 10.5, P["muted"]))
    b.append(box(x + 24, Y(42), 236, 74, ["villkor, nedskrivna:", "katalysator med datum kvar,", "ingen hård diskvalificering i siffrorna,", "stoppet infört först"], P["owner_f"], P["owner_t"], 11))
    b.append(text(x, 30, "kurs per aktie", "middle", 11, P["muted"]))
    b.append(text(20, 352, "ett köp under X, på villkor Y, med stopp Z", "start", 12.5, P["ink"], 600))
    b.append(text(20, 370, "verktyget anger avståndet till X och om Z är brutet;", "start", 10.5, P["muted"]))
    b.append(text(20, 385, "det säger aldrig köp", "start", 10.5, P["muted"]))
    return figure(fid, W, H,
                  "Ett köppris med villkor och stopp",
                  "En lodrät skala. Vid 100 markerar en blå kvadrat värdet i basfallet. Mellan 100 och 85 markerar ett ljusblått band bufferten, med en blå linje vid 85 märkt högsta pris ägaren betalar. En orange cirkel vid 93 markerar dagens kurs, märkt över linjen, vänta. Längre ned markerar en rödorange linje med ett kryss stoppet. En lila ruta listar de nedskrivna villkoren.",
                  "".join(b),
                  "Aldrig 'ett köp'. Ett köp under en angiven kurs, på angivna villkor, med en angiven utgång. Alla tre skrivs ner innan pengarna rör sig, och verktyget visar bara var dagens kurs står mot dem.")

def fig_refusal_tracked():
    fid = "f-shadow"
    W, H = 480, 240
    b = []
    b.append(f'<line x1="40" y1="190" x2="460" y2="190" stroke="{P["rule"]}" stroke-width="1.5"/>')
    b.append(text(60, 208, "beslutsdagen", "middle", 11, P["muted"]))
    b.append(text(440, 208, "ett år senare", "middle", 11, P["muted"]))
    # verdict marker
    b.append(f'<line x1="60" y1="60" x2="60" y2="190" stroke="{P["ink"]}" stroke-width="2" stroke-dasharray="4 3"/>')
    b.append(box(70, 40, 190, 70, ["noterat den dagen:", "datum, slutkursen,", "en rad som anger vad som avgjorde"], P["surface"], P["ink"], 11))
    b.append(box(270, 40, 190, 70, ["inte noterat:", "en tes, ett mål,", "en förväntan, ett argument"], P["surface"], P["rule"], 11, color=P["muted"], dash="4 3"))
    # lines
    npts = [(60, 150), (140, 160), (220, 135), (300, 145), (380, 120), (440, 125)]
    bpts = [(60, 150), (140, 148), (220, 144), (300, 140), (380, 136), (440, 132)]
    b.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in bpts) + f'" fill="none" stroke="{P["ink"]}" stroke-width="2" stroke-dasharray="5 4"/>')
    b.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in npts) + f'" fill="none" stroke="{P["price"]}" stroke-width="2.5"/>')
    for x, y in npts:
        b.append(circ(x, y))
    b.append(text(452, 128, "avvisat bolag", "start", 11, P["price_t"]).replace('x="452"', 'x="300"').replace('y="128"', 'y="172"'))
    b.append(text(300, 186, "ett index, samma valuta, samma slags avkastning", "start", 11, P["muted"]).replace('x="300"', 'x="120"'))
    b.append(text(240, 230, "läses en gång om året, med flit: ingen resultattavla böjer en regel", "middle", 11, P["ink"]))
    return figure(fid, W, H,
                  "Ett nej följt framåt",
                  "En tidslinje från beslutsdagen till ett år senare. En ruta listar vad som noteras den dagen: datum, slutkursen, en rad som anger vad som avgjorde. En streckad ruta listar vad som inte noteras: en tes, ett mål, en förväntan. En orange linje med cirklar följer det avvisade bolaget, en streckad svart linje följer ett index.",
                  "".join(b),
                  "Varje nej mäts i efterhand mot marknaden, från den dag det skrevs. Det som noteras är medvetet tunt: ett datum, en kurs, en orsak. En rad som argumenterar är en rad som kommer att argumenteras om.")


# ---------------------------------------------------------------------------
# PART TWO
# ---------------------------------------------------------------------------

def fig_measure_decide():
    fid = "f-line"
    W, H = 480, 230
    b = []
    b.append(text(120, 26, "verktyget får", "middle", 13, P["ink"], 600))
    b.append(text(360, 26, "bara ägaren får", "middle", 13, P["owner_t"], 600))
    b.append(wall(240, 10, 240, 200))
    left = ["hämta kurser och rapporter", "räkna ut en fast uppsättning tal", "jämföra en kurs med en linje", "skriva rapport och sida", "peka på det som behöver ses", "säga DATA SAKNAS"]
    right = ["föra in ett bolag", "tilldela en nivå", "skriva tillväxtbedömning", "sätta värde, köplinje, stopp", "flytta bolag mellan statusar", "besluta"]
    for i, s in enumerate(left):
        b.append(text(20, 56 + i * 24, s, "start", 12.5, P["ink"]))
    for i, s in enumerate(right):
        b.append(text(260, 56 + i * 24, s, "start", 12.5, P["owner_t"]))
    b.append(text(240, 222, "väggen är kod: en skrivning över den stoppar körningen", "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "Gränsen verktyget aldrig korsar",
                  "Två kolumner åtskilda av en tjock lodrät vägg. Till vänster vad verktyget får göra: hämta, räkna ut, jämföra, skriva en rapport, peka, säga data saknas. Till höger, i lila, vad bara ägaren får göra: föra in ett bolag, tilldela en nivå, skriva en tillväxtbedömning, sätta ett värde eller stopp, flytta ett bolag, besluta.",
                  "".join(b),
                  "Den styrande regeln som en vägg. Allt till vänster är mätning. Allt till höger är beslut, och koden som skriver mätningar är byggd så att den inte kan skriva ett beslut.")



def fig_pieces_walls():
    fid = "f-pieces"
    W, H = 480, 410
    b = []
    b.append(text(20, 24, "utanför maskinen", "start", 11, P["muted"]))
    b.append(box(20, 30, 130, 40, ["kurskällor, rapporter"], P["surface"], P["rule"], 11))
    b.append(arrow(fid, 85, 72, 85, 100))
    b.append(box(20, 102, 130, 44, ["FETCH", "hämtar in siffror"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 152, 124, 178, 124))
    b.append(box(180, 102, 130, 44, ["REGISTRET", "sparar varje siffra"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 312, 124, 338, 124))
    b.append(box(340, 102, 120, 44, ["COMPUTE", "inga filer, inget nät"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 400, 148, 400, 176))
    b.append(box(340, 178, 120, 44, ["REPORT och PAGE", "anger, ger aldrig råd"], P["surface"], P["ink"], 11))
    b.append(box(20, 178, 130, 44, ["SCREEN", "2 000 till en kortlista"], P["surface"], P["ink"], 11))
    b.append(box(180, 178, 130, 44, ["WATCH", "rapporter och kurser"], P["surface"], P["ink"], 11))
    b.append(box(180, 248, 130, 44, ["HEARTBEAT", "visar att den kördes"], P["surface"], P["ink"], 11))
    # compute wall
    b.append(wall(326, 84, 326, 164))
    b.append(text(322, 80, "vägg: räkningen hämtar aldrig", "end", 10, P["ink"], 600))
    # watchlist wall
    b.append(wall(12, 318, 330, 318))
    b.append(text(12, 336, "vägg: inget som körs på schema får skriva under linjen", "start", 10, P["ink"], 600))
    b.append(box(20, 346, 240, 54, ["BEVAKNINGSLISTAN: ägarens fil", "statusar, nivåer, värden, stopp;", "varje beslut, skrivet för hand"], P["owner_f"], P["owner_t"], 10.5))
    b.append(path_arrow(fid, "M 100 346 C 100 300, 85 260, 85 224", "", 1.5, "4 3"))
    b.append(text(104, 300, "läses bara", "start", 10, P["muted"]))
    b.append(text(340, 262, "hela pilar: siffror flödar", "start", 10, P["muted"]))
    b.append(text(340, 278, "streckat: läses, skrivs ej", "start", 10, P["muted"]))
    b.append(text(340, 294, "tjocka linjer: väggar i kod", "start", 10, P["muted"]))
    b.append(text(280, 372, "ägaren", "start", 10.5, P["owner_t"], 600))
    b.append(text(280, 386, "skriver här", "start", 10.5, P["owner_t"], 600))
    return figure(fid, W, H,
                  "Programmets delar och väggarna mellan dem",
                  "Rutor för FETCH, REGISTRET, COMPUTE, REPORT och PAGE, SCREEN, WATCH och HEARTBEAT, med pilar som visar siffror som flödar från externa källor genom fetch och registret till compute och rapporten. En lila ruta längst ned, BEVAKNINGSLISTAN, ägarens fil, skiljs från delarna av en tjock vägg med texten: inget som körs på schema får skriva under linjen. En andra vägg skiljer compute från hämtning.",
                  "".join(b),
                  "Sju slags delar och två väggar. Siffror flödar från vänster till höger och nedåt. Ägarens fil ligger under en vägg som ingen schemalagd del kan skriva över, och räkningen ligger bakom en vägg som håller den borta från nätverket och klockan.")


def fig_figure_journey():
    fid = "f-journey"
    W, H = 420, 560
    b = []
    steps = [
        ("emittentens rapport", "bolagets egen rapport, daterad", P["surface"], P["ink"]),
        ("läst från sidan", "siffra, period, källa, sidnummer", P["surface"], P["ink"]),
        ("införd som UNVERIFIED", "angiven siffra, ej kontrollerad än", None, P["miss"]),
        ("återläst av ägaren", "mot sidan som anges bredvid", P["owner_f"], P["owner_t"]),
        ("VERIFIED, och vilken sort", "märkt · tvärdokument · samma sida", P["pass_f"], P["pass_"]),
        ("körningsprotokollet", "åtta deklarationer, annars inget värde", P["surface"], P["ink"]),
        ("ett värde, sedan avstånd", "sidan visar hur långt kursen är", P["value_f"], P["value"]),
    ]
    y = 16
    for i, (t, s, fill, stroke) in enumerate(steps):
        if fill is None:
            b.append(hbox(fid, 30, y, 260, 50, [t, s], 11, ow=232))
        else:
            b.append(box(30, y, 260, 50, [t, s], fill, stroke, 11))
        if i >= 1:
            b.append(f'<rect x="300" y="{y+8}" width="100" height="34" rx="3" fill="{P["paper"]}" stroke="{P["rule"]}" stroke-width="1.5" stroke-dasharray="3 2"/>')
            b.append(lines(350, y + 22, ["källa · period", "sida · datum"], "middle", 9.5, P["muted"]))
        if i < len(steps) - 1:
            b.append(arrow(fid, 160, y + 52, 160, y + 68))
        y += 70
    b.append(text(210, y + 8, "märkningen följer siffran och skrivs ut bredvid den", "middle", 11, P["ink"], 600))
    b.append(text(210, y + 26, "en siffra utan märkning, eller för fel period, är DATA SAKNAS", "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "En siffras resa från rapport till sida, med ursprunget kvar",
                  "Sju rutor uppifrån och ned: emittentens rapport; läst från sidan; införd som UNVERIFIED, snedstreckad; återläst av ägaren, lila; VERIFIED och vilken sort, grön; körningsprotokollet; ett värde och sedan ett avstånd, blå. Bredvid varje steg från det andra och framåt står en liten streckad etikett: källa, period, sida, datum.",
                  "".join(b),
                  "Ett tals väg. Det kommer in som overifierat, läses tillbaka av en människa, och först då bär det en verifieringsmärkning som säger vilken sorts kontroll det klarade. Dess ursprung följer med ända till sidan.")

def fig_nightly_cycle():
    fid = "f-night"
    W, H = 480, 260
    b = []
    # clock
    b.append(f'<circle cx="60" cy="70" r="30" fill="{P["surface"]}" stroke="{P["ink"]}" stroke-width="2"/>')
    b.append(f'<line x1="60" y1="70" x2="60" y2="48" stroke="{P["ink"]}" stroke-width="2.5"/>')
    b.append(f'<line x1="60" y1="70" x2="74" y2="78" stroke="{P["ink"]}" stroke-width="2.5"/>')
    b.append(text(60, 118, "22:30 varje natt", "middle", 11, P["muted"]))
    b.append(arrow(fid, 92, 70, 126, 70))
    b.append(box(128, 40, 130, 60, ["körningen", "hämtar kurser, jämför", "med redan satta linjer"], P["surface"], P["ink"], 11))
    # success branch
    b.append(arrow(fid, 260, 58, 300, 40, "pass"))
    b.append(box(302, 14, 158, 52, ["rapport och sida skrivna;", "en ping utåt"], P["pass_f"], P["pass_"], 11))
    b.append(tick(450, 20, 14))
    # failure branch
    b.append(arrow(fid, 260, 84, 300, 104, "fail"))
    b.append(box(302, 92, 158, 52, ["en notis till telefonen:", "vad stoppade, senaste loggen"], P["fail_f"], P["fail"], 11))
    b.append(cross(450, 98, 14))
    b.append(text(240, 168, "lyckad körning är tyst på telefonen men hörs hos observatören;", "middle", 11.5, P["ink"]))
    b.append(text(240, 184, "misslyckad körning hörs på telefonen. Tystnad betyder något annat.", "middle", 11.5, P["ink"]))
    b.append(text(240, 214, "körningen kan inte skriva ett beslut: bara de två mapparna", "middle", 11, P["muted"]))
    b.append(text(240, 230, "för data och rapporter är skrivbara för den", "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "Nattkörningen med båda utgångarna",
                  "En klocka vid 22:30 leder till en ruta, körningen. En grön pil leder till en ruta med en bock: rapport och sida skrivna, en ping utåt. En rödorange pil leder till en ruta med ett kryss: en notis till telefonen som säger vad som stoppade.",
                  "".join(b),
                  "En klocka går av, kurser kontrolleras mot beslut som redan fattats, och filer skrivs. Två utgångar: vid lyckad körning talar maskinen om för en observatör utanför att den lever; vid misslyckande talar den om för ägarens telefon vad som stoppade.")



def fig_two_observers():
    fid = "f-obs"
    W, H = 480, 320
    b = []
    b.append(text(120, 22, "maskinen går, körningen föll", "middle", 12, P["ink"], 600))
    b.append(f'<rect x="20" y="32" width="200" height="120" rx="8" fill="{P["surface"]}" stroke="{P["ink"]}" stroke-width="2"/>')
    b.append(box(34, 46, 80, 40, ["körningen"], P["fail_f"], P["fail"], 11))
    b.append(cross(106, 52, 12))
    b.append(arrow(fid, 116, 66, 150, 66, "fail"))
    b.append(box(152, 46, 58, 40, ["observatör", "ett"], P["surface"], P["ink"], 10))
    b.append(arrow(fid, 181, 88, 181, 118, "fail"))
    b.append(text(181, 140, "telefon: vad stoppade", "middle", 10.5, P["fail_t"], 600))
    b.append(text(120, 174, "ingen ping lämnar maskinen", "middle", 10.5, P["muted"]))
    b.append(text(360, 22, "maskinen är av", "middle", 12, P["ink"], 600))
    b.append(f'<rect x="260" y="32" width="200" height="120" rx="8" fill="url(#{fid}-hatch)" stroke="{P["miss"]}" stroke-width="2"/>')
    b.append(f'<rect x="300" y="72" width="120" height="40" rx="4" fill="{P["paper"]}" opacity="0.94"/>')
    b.append(lines(360, 88, ["inget körs,", "inget kan larma"], "middle", 11, P["miss_t"]))
    b.append(text(360, 174, "ingen ping lämnar maskinen", "middle", 10.5, P["muted"]))
    b.append(wall(10, 196, 470, 196))
    b.append(text(20, 214, "utanför maskinen", "start", 11, P["muted"]))
    b.append(box(150, 224, 180, 46, ["observatör två", "väntar en ping per dag"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 120, 152, 200, 222, "", 1.5, "4 3"))
    b.append(arrow(fid, 360, 152, 280, 222, "", 1.5, "4 3"))
    b.append(text(240, 292, "ingen ping i tid: den larmar.", "middle", 11, P["fail_t"], 600))
    b.append(text(240, 308, "Frånvaro är den enda signal en död maskin ännu kan sända.", "middle", 11, P["fail_t"], 600))
    return figure(fid, W, H,
                  "Två observatörer: en på maskinen, en utanför",
                  "Vänster panel: maskinen går och körningen föll; observatör ett, på maskinen, skickar en notis till telefonen om vad som stoppade. Höger panel: maskinen är av, ritad snedstreckad; inget körs och inget kan larma. Under en tjock vägg, utanför maskinen, väntar observatör två en ping per dag. Streckade pilar från båda panelerna leder dit. Texten lyder: ingen ping i tid, den larmar.",
                  "".join(b),
                  "Två observatörer för två slags haverier. Den på maskinen kan beskriva vad som gick sönder, men bara så länge maskinen lever och kan köra den. Den utanför vet ingenting utom om den dagliga pingen kom, och det är det enda larm en död maskin kan ge.")

def fig_tunnel():
    fid = "f-tunnel"
    W, H = 480, 280
    b = []
    # machine
    b.append(f'<rect x="20" y="30" width="190" height="210" rx="8" fill="{P["surface"]}" stroke="{P["ink"]}" stroke-width="2"/>')
    b.append(text(115, 52, "maskinen", "middle", 12, P["ink"], 600))
    b.append(box(36, 66, 158, 46, ["en liten server, lyssnar", "bara på sig själv"], P["surface"], P["ink"], 11))
    b.append(text(115, 128, "sidan", "middle", 11, P["muted"]))
    b.append(arrow(fid, 115, 114, 115, 150))
    b.append(box(36, 152, 158, 46, ["tunnelklienten", "ringer UT och håller linjen"], P["surface"], P["ink"], 11))
    # wall
    b.append(wall(226, 20, 226, 250))
    b.append(text(226, 266, "brandvägg: ingen port öppnad inåt", "middle", 11, P["ink"], 600))
    # outbound arrow crossing
    b.append(arrow(fid, 196, 175, 262, 175, "", 3))
    b.append(text(232, 166, "ut", "middle", 10, P["ink"], 600).replace('x="232"', 'x="229"'))
    # inbound attempts blocked
    for y in (80, 110):
        b.append(f'<line x1="300" y1="{y}" x2="240" y2="{y}" stroke="{P["fail_t"]}" stroke-width="2" stroke-dasharray="4 3"/>')
        b.append(cross(238, y, 14))
    b.append(text(304, 84, "allt som ringer in", "start", 10.5, P["fail_t"]))
    b.append(text(304, 114, "nekas vid väggen", "start", 10.5, P["fail_t"]))
    # relay and front door
    b.append(box(264, 152, 90, 46, ["reläet", "utanför"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 356, 175, 380, 175))
    b.append(box(382, 140, 84, 70, ["ytterdörr:", "vem är du?", "en adress,", "engångskod"], P["owner_f"], P["owner_t"], 10))
    b.append(arrow(fid, 424, 212, 424, 236, "owner"))
    b.append(text(424, 252, "telefonen", "middle", 11, P["owner_t"], 600))
    return figure(fid, W, H,
                  "Tunneln: en utgående pil som korsar väggen",
                  "Inuti en ruta märkt maskinen: en liten server som bara lyssnar på sig själv, och en tunnelklient som ringer ut. En tjock lodrät vägg märkt brandvägg, ingen port öppnad inåt. En tjock pil korsar väggen utåt till ett relä. Två streckade inkommande pilar är överkryssade vid väggen. Efter reläet frågar en lila ytterdörr vem är du, sedan telefonen.",
                  "".join(b),
                  "Inget ringer in. Maskinen öppnar en linje utåt och håller den. En läsare kommer till en ytterdörr utanför maskinen, bevisar vem hen är, och först då hämtas sidan tillbaka nedför linjen som maskinen öppnade.")



def fig_boundary():
    fid = "f-bound"
    W, H = 480, 270
    b = []
    b.append(text(20, 24, "rapportmappen: dussintals filer", "start", 10.5, P["ink"], 600))
    cols, rows = 8, 5
    for r in range(rows):
        for c in range(cols):
            x = 20 + c * 24
            y = 34 + r * 22
            if r == 2 and c == 3:
                b.append(f'<rect x="{x}" y="{y}" width="20" height="18" rx="2" fill="{P["value_f"]}" stroke="{P["value"]}" stroke-width="2"/>')
            else:
                b.append(f'<rect x="{x}" y="{y}" width="20" height="18" rx="2" fill="url(#{fid}-hatch)" stroke="{P["miss"]}" stroke-width="1"/>')
    b.append(text(20, 162, "en fil serveras: översiktssidan", "start", 10.5, P["value_t"], 600))
    b.append(text(20, 178, "alla andra filer: analyser, register,", "start", 10.5, P["muted"]))
    b.append(text(20, 192, "dagliga körningar — bakom linjen", "start", 10.5, P["muted"]))
    b.append(wall(230, 20, 230, 210))
    b.append(box(246, 40, 170, 60, ["serverns enda regel:", '"/" → sidan', "allt annat → hittas inte"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 470, 70, 420, 70, "pass"))
    b.append(text(468, 122, "en begäran om /", "end", 10.5, P["pass_t"]))
    b.append(f'<line x1="470" y1="160" x2="426" y2="160" stroke="{P["fail_t"]}" stroke-width="2" stroke-dasharray="4 3"/>')
    b.append(cross(422, 160, 14))
    b.append(text(468, 184, "en begäran om allt annat", "end", 10.5, P["fail_t"]))
    b.append(text(240, 236, "regeln är ett block konfiguration; tas det bort serveras varje", "middle", 10.5, P["ink"]))
    b.append(text(240, 252, "fil i mappen, och inget skulle larma", "middle", 10.5, P["ink"]))
    return figure(fid, W, H,
                  "Gränsen med en enda sökväg",
                  "Till vänster: ett rutnät med fyrtio små snedstreckade filikoner med en blå ikon bland dem, märkt: en fil serveras, alla andra filer stannar bakom linjen. En tjock vägg. Till höger: serverns enda regel, snedstreck går till sidan, allt annat går till hittas inte. En grön pil för en begäran om snedstreck når servern; en streckad rödorange pil för allt annat är överkryssad framför den.",
                  "".join(b),
                  "Servern känner till en adress och svarar 'hittas inte' på alla andra. Mappen bakom den rymmer dussintals privata filer. Skillnaden mellan en exponerad fil och alla är ett enda block konfiguration.")

ALL = {
    "price_vs_value": fig_price_vs_value,
    "margin_of_safety": fig_margin_of_safety,
    "screen_filter": fig_screen_filter,
    "name_fails_gate": fig_name_fails_gate,
    "dcf_vs_reverse": fig_dcf_vs_reverse,
    "two_orderings": fig_two_orderings,
    "three_doors": fig_three_doors,
    "funnel": fig_funnel,
    "buy_price": fig_buy_price,
    "refusal_tracked": fig_refusal_tracked,
    "measure_decide": fig_measure_decide,
    "pieces_walls": fig_pieces_walls,
    "figure_journey": fig_figure_journey,
    "nightly_cycle": fig_nightly_cycle,
    "two_observers": fig_two_observers,
    "tunnel": fig_tunnel,
    "boundary": fig_boundary,
}
