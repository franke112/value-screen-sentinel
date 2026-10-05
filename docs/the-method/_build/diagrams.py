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
    b.append(text(250, 240, "time", "middle", 12, P["muted"]))
    b.append(text(14, 125, "worth", "middle", 12, P["muted"]).replace("<text", '<text transform="rotate(-90 14 125)"'))
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
    b.append(text(208, 165, "the gap", "start", 13, P["ink"], 600))
    b.append(text(208, 181, "price below value", "start", 11, P["muted"]))
    # gap the other way at 270
    b.append(f'<line x1="270" y1="70" x2="270" y2="126" stroke="{P["ink"]}" stroke-width="2" stroke-dasharray="3 3"/>')
    b.append(text(278, 84, "price above value", "start", 11, P["muted"]))
    # legend
    b.append(sq(62, 22))
    b.append(text(72, 26, "value: what the business is worth, moves slowly", "start", 12, P["value_t"]))
    b.append(circ(62, 42))
    b.append(text(72, 46, "price: what the market quotes, moves daily", "start", 12, P["price_t"]))
    return figure(fid, W, H,
                  "Price against value over time",
                  "A slowly rising blue line with square markers shows the value of a business. An orange zigzag with circle markers shows its quoted price crossing above and below the value line. Dashed vertical lines mark the gap where price is below value and where it is above.",
                  "".join(b),
                  "Two numbers for one business. The blue squares are what it is worth; the orange circles are what it is quoted at. The gap between them is the whole opportunity, and it opens in both directions.")



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
    b.append(text(x1, y - 14, "your estimate of value: 100", "end", 13, P["value_t"], 600))
    # tier lines
    for v, lab, tier in ((85, "85", "tier 1"), (75, "75", "tier 2"), (65, "65", "tier 3")):
        b.append(f'<line x1="{X(v)}" y1="{y-6}" x2="{X(v)}" y2="{y+34}" stroke="{P["value_t"]}" stroke-width="2"/>')
        b.append(text(X(v), y + 50, lab, "middle", 12, P["value_t"], 600))
        b.append(text(X(v), y + 64, tier, "middle", 10.5, P["muted"]))
    b.append(text(X(85), y + 82, "the most you would pay, by tier", "middle", 11.5, P["ink"]).replace(f'x="{X(85)}"', f'x="{X(75)}"'))
    # cushion label
    b.append(text(X(92.5), y - 40, "the cushion", "middle", 12, P["ink"], 600))
    b.append(text(X(92.5), y - 27, "room to be wrong", "middle", 10.5, P["muted"]))
    # price example
    b.append(circ(X(70), y + 14, 7))
    b.append(text(X(70), y - 40, "price today: 70", "end", 12, P["price_t"], 600))
    b.append(text(X(70), y - 27, "below every line", "end", 10.5, P["muted"]))
    b.append(f'<line x1="{X(70)}" y1="{y-22}" x2="{X(70)}" y2="{y+4}" stroke="{P["price_t"]}" stroke-width="1.5" stroke-dasharray="3 2"/>')
    b.append(text(x0, y + 50, "0", "middle", 12, P["muted"]))
    b.append(text(240, y + 108, "your estimate can be wrong by 15, 25 or 35 and you still paid less than it is worth", "middle", 10.5, P["muted"]))
    return figure(fid, W, H,
                  "Margin of safety as a cushion below the estimated value",
                  "A horizontal bar from 0 to 100 represents the estimated value. The part from 85 to 100 is drawn as an empty dashed region labelled the cushion, room to be wrong. Vertical lines at 85, 75 and 65 mark the most the owner would pay by tier. An orange circle at 70 marks today's price, below every line.",
                  "".join(b),
                  "Margin of safety. You think the business is worth 100. You refuse to pay more than 85, or 75, or 65, depending on how sure you are. The cushion is the room for your estimate to be wrong.")


def fig_screen_filter():
    fid = "f-sieve"
    W, H = 420, 480
    b = []
    cx = 210
    rows = [
        (400, ["about 2,000 listed companies"], P["surface"], P["ink"]),
        (384, ["step 0: names already owned or", "already decided are removed"], P["surface"], P["ink"]),
        (368, ["filter 1: price 15–50% below its 52-week high;", "listed at least five years; inside the circle"], P["surface"], P["ink"]),
        (352, ["filter 2: cash flow positive; debt within a", "stated cap; revenue not falling two quarters"], P["surface"], P["ink"]),
        (320, ["ranked on two figures:", "profitability and earnings yield"], P["surface"], P["ink"]),
        (240, ["about 20 watched for price"], P["value_f"], P["value"]),
        (180, ["3 to 5 read by hand"], P["owner_f"], P["owner_t"]),
    ]
    y = 16
    for w, label, fill, stroke in rows:
        h = 46 if len(label) > 1 else 36
        b.append(box(cx - w / 2, y, w, h, label, fill, stroke, 12))
        y += h + 14
        if w != 180:
            b.append(arrow(fid, cx, y - 14, cx, y - 2))
    b.append(text(cx, y + 4, "The order of the cuts, not measured counts.", "middle", 11, P["muted"]))
    b.append(text(cx, y + 20, "What falls out has not been judged. It has not been read.", "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "The screen as a coarse filter",
                  "A stack of boxes narrowing from about two thousand companies at the top, through an exclusion step, two filters and a ranking, to about twenty names watched and three to five read by hand at the bottom.",
                  "".join(b),
                  "The screen only removes. Each step asks one coarse question and lets through whatever it cannot fault. Nothing that falls out has been judged; it has simply not been read.")


def fig_name_fails_gate():
    fid = "f-gate"
    W, H = 480, 290
    b = []
    b.append(lines(20, 26, ["only a named new fact reopens a failed gate: a filing,", "a guidance change, a profit warning. Never a level on a chart."], "start", 11, P["muted"]))
    b.append(box(20, 82, 90, 50, ["NAME A"], P["surface"], P["ink"], 13, 600))
    b.append(arrow(fid, 112, 107, 146, 107))
    b.append(box(148, 70, 116, 74, ["gate 1", "how far has", "the price fallen?"], P["pass_f"], P["pass_"], 12))
    b.append(tick(258, 76))
    b.append(arrow(fid, 266, 107, 300, 107, "pass"))
    b.append(box(302, 70, 158, 74, ["gate 2: why did it fall?", "class D:", "lasting damage"], P["fail_f"], P["fail"], 12))
    b.append(cross(452, 76))
    b.append(arrow(fid, 381, 146, 381, 182, "fail"))
    b.append(box(222, 184, 238, 46, ["out: WATCH-GATED or DROPPED"], P["surface"], P["ink"], 12, 600))
    # a lower price does not bring it back: dashed line along the bottom, crossed at NAME A
    b.append(f'<path d="M 222 207 L 65 207 L 65 140" fill="none" stroke="{P["fail_t"]}" stroke-width="2" stroke-dasharray="5 4"/>')
    b.append(cross(65, 140, 16))
    b.append(lines(20, 236, ["a lower price later does not bring it back:", "the gate failed on something other than price"], "start", 11, P["fail_t"]))
    return figure(fid, W, H,
                  "A name failing a gate",
                  "NAME A passes gate 1 with a tick and reaches gate 2, where the fall is classed as lasting damage and fails with a cross. An arrow leads down to a box reading out: WATCH-GATED or DROPPED. A dashed line from that box back toward NAME A ends in a cross, labelled: a lower price later does not bring it back.",
                  "".join(b),
                  "NAME A fell far enough to pass gate 1. Gate 2 asks why it fell; the answer is lasting damage, and that is a fail. It leaves. A cheaper price later does not bring it back; only a named new fact can.")


def fig_dcf_vs_reverse():
    fid = "f-inv"
    W, H = 480, 240
    b = []
    b.append(text(20, 30, "the usual way", "start", 13, P["muted"], 600))
    b.append(box(20, 40, 126, 56, ["a growth", "you assume"], P["owner_f"], P["owner_t"], 12))
    b.append(arrow(fid, 148, 68, 172, 68))
    b.append(box(174, 40, 126, 56, ["the arithmetic"], P["surface"], P["ink"], 12))
    b.append(arrow(fid, 302, 68, 326, 68))
    b.append(box(328, 40, 132, 56, ["a value, then", "compare to price"], P["value_f"], P["value"], 11.5))
    b.append(text(240, 118, '"what is it worth?" — your guess in, a number out', "middle", 11, P["muted"]))
    b.append(text(20, 150, "the reverse", "start", 13, P["muted"], 600))
    b.append(box(20, 160, 126, 56, ["the price", "as quoted today"], P["price_f"], P["price_t"], 12))
    b.append(arrow(fid, 148, 188, 172, 188))
    b.append(box(174, 160, 126, 56, ["the same arithmetic,", "run backwards"], P["surface"], P["ink"], 11.5))
    b.append(arrow(fid, 302, 188, 326, 188))
    b.append(box(328, 160, 132, 56, ["the growth the", "price is assuming"], P["value_f"], P["value"], 11.5))
    b.append(text(240, 236, '"do I believe that?" — a number in, a question you can judge out', "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "A normal valuation against a reverse one",
                  "Top row: a growth you assume goes into the arithmetic and a value comes out, to compare with price. Bottom row: the quoted price goes into the same arithmetic run backwards, and the growth the price assumes comes out.",
                  "".join(b),
                  "Same arithmetic, opposite direction. The usual way puts your guess in and gets a number out. The reverse puts the market's number in and gets the market's guess out, which you can then judge.")

def fig_two_orderings():
    fid = "f-order"
    W, H = 480, 270
    b = []
    # Wrong ordering
    b.append(text(20, 26, "ordering A: look, then write", "start", 13, P["fail_t"], 600))
    b.append(cross(240, 21))
    b.append(box(20, 40, 120, 56, ["solve the growth", "the price assumes"], P["price_f"], P["price_t"], 12))
    b.append(arrow(fid, 142, 68, 178, 68))
    b.append(box(180, 40, 120, 56, ["write your own", "growth view"], P["owner_f"], P["owner_t"], 12))
    b.append(path_arrow(fid, "M 240 98 C 240 120, 100 120, 90 100", "fail", 2, "4 3"))
    b.append(text(170, 128, "the view drifts toward the number just seen", "middle", 11, P["fail_t"]))
    b.append(box(320, 40, 140, 56, ["VOID for this name", "in this cycle"], P["fail_f"], P["fail"], 12, 600))
    b.append(arrow(fid, 302, 68, 318, 68, "fail"))
    # Right ordering
    b.append(text(20, 166, "ordering B: write, then look", "start", 13, P["pass_t"], 600))
    b.append(tick(240, 161))
    b.append(box(20, 180, 120, 56, ["write your growth", "view, with reasons,", "timestamped"], P["owner_f"], P["owner_t"], 11))
    b.append(arrow(fid, 142, 208, 178, 208))
    b.append(box(180, 180, 120, 56, ["solve the growth", "the price assumes"], P["price_f"], P["price_t"], 12))
    b.append(arrow(fid, 302, 208, 318, 208, "pass"))
    b.append(box(320, 180, 140, 56, ["compare: is the market", "asking more than", "you believe?"], P["value_f"], P["value"], 11))
    b.append(text(240, 258, "the timestamp is the proof of order", "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "The two orderings of pre-registration",
                  "Ordering A, marked with a cross: solve the growth the price assumes, then write your own view; a dashed arrow shows the view drifting toward the number just seen; the result is VOID. Ordering B, marked with a tick: write your view first with a timestamp, then solve, then compare.",
                  "".join(b),
                  "The same two steps in two orders. In A, the market's number is seen first and pulls the view toward it. In B, the view is on record before the number exists, and the record's timestamp is the proof.")


def fig_three_doors():
    fid = "f-doors"
    W, H = 480, 250
    b = []
    doors = [
        (30, "PASS", P["pass_f"], P["pass_"], ["the test ran", "and the figure", "cleared it"], "tick"),
        (180, "FAIL", P["fail_f"], P["fail"], ["the test ran", "and the figure", "did not"], "cross"),
        (330, "DATA MISSING", None, P["miss"], ["the test could", "not run: the", "figure is absent"], "q"),
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
        col = {"PASS": P["pass_t"], "FAIL": P["fail_t"], "DATA MISSING": P["miss_t"]}[label]
        b.append(text(x + 60, 104, label, "middle", 13, col, 700))
        b.append(lines(x + 60, 126, rows, "middle", 11, P["ink"]))
    # forbidden merge
    b.append(f'<path d="M 330 200 C 300 230, 330 230, 300 200" fill="none" stroke="none"/>')
    b.append(f'<line x1="326" y1="205" x2="304" y2="205" stroke="{P["fail_t"]}" stroke-width="2" stroke-dasharray="4 3"/>')
    b.append(cross(315, 205, 16))
    b.append(text(240, 230, "the third door is never quietly counted as the second", "middle", 12, P["ink"], 600))
    return figure(fid, W, H,
                  "PASS, FAIL and DATA MISSING as three doors",
                  "Three doors side by side: a green door with a tick labelled PASS, the test ran and the figure cleared it; a vermillion door with a cross labelled FAIL, the test ran and the figure did not; a grey hatched door with a question mark labelled DATA MISSING, the test could not run. A crossed-out dashed line between the third and second door says the third is never quietly counted as the second.",
                  "".join(b),
                  "Three outcomes, three doors. The third is not a weaker version of the second. A test that could not run has told you nothing about the company and something about your data.")



def fig_funnel():
    fid = "f-funnel"
    W, H = 420, 520
    b = []
    cx = 150
    b.append(box(cx - 90, 20, 180, 54, ["INTAKE", "read, not watched"], P["surface"], P["ink"], 12))
    b.append(arrow(fid, cx, 76, cx, 104, "owner"))
    b.append(text(cx + 8, 96, "the owner enters it", "start", 11, P["owner_t"]))
    b.append(box(cx - 90, 106, 180, 54, ["PIPELINE", "entered; gate 1 frozen"], P["surface"], P["ink"], 12))
    b.append(arrow(fid, cx, 162, cx, 190, "owner"))
    b.append(text(cx + 8, 182, "the owner reads and values it", "start", 11, P["owner_t"]))
    b.append(box(20, 192, 130, 92, ["WATCH-GATED", "failed on something", "other than price;", "back only on a named", "new fact, never a price"], P["fail_f"], P["fail"], 10.5))
    b.append(box(170, 192, 130, 92, ["WATCH-PRICED", "the reading is done;", "only price stands", "in the way"], P["value_f"], P["value"], 10.5))
    b.append(arrow(fid, 235, 286, 235, 318, "owner"))
    b.append(lines(227, 300, ["the price crosses the line:", "the owner buys"], "end", 11, P["owner_t"]))
    b.append(box(170, 320, 130, 54, ["HELD", "owned, with a stop"], P["owner_f"], P["owner_t"], 12, 600))
    # dropped column
    b.append(f'<rect x="330" y="20" width="70" height="354" rx="6" fill="url(#{fid}-hatch)" stroke="{P["miss"]}" stroke-width="2"/>')
    b.append(f'<rect x="338" y="164" width="54" height="60" rx="4" fill="{P["paper"]}" opacity="0.94"/>')
    b.append(lines(365, 186, ["DROPPED", "not", "watched"], "middle", 11, P["miss_t"], 600))
    for x1, y in ((240, 47), (240, 133), (302, 238), (302, 347)):
        b.append(arrow(fid, x1, y, 328, y, "fail", 1.5, "3 3"))
    b.append(lines(20, 402, ["What makes a name fall out: a failed gate, a class D reason",
                             "for the fall, a hard kill in the accounts, a business outside",
                             "the circle, a stop breached. The tool measures and points;",
                             "every move between boxes is the owner's act."],
                   "start", 10.5, P["muted"]))
    b.append(text(20, 476, "purple arrows: the owner acts", "start", 11, P["owner_t"]))
    b.append(text(20, 494, "dashed vermillion: a name falls out", "start", 11, P["fail_t"]))
    b.append(text(20, 512, "hatched grey: no longer watched", "start", 11, P["miss_t"]))
    return figure(fid, W, H,
                  "The funnel: six statuses and how a name moves between them",
                  "Boxes from top to bottom: INTAKE, PIPELINE, then a split into WATCH-GATED and WATCH-PRICED, then HELD. Purple arrows between them are labelled with the owner's acts. Dashed vermillion arrows lead from every box into a hatched grey column labelled DROPPED, not watched. The WATCH-GATED box says it comes back only on a named new fact, never a price.",
                  "".join(b),
                  "The six statuses a name can hold, from read to owned. Every downward move is the owner's decision. The tool never moves a name; it measures where each one stands and says so.")


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
    b.append(text(x + 24, Y(100) + 4, "value, base case: 100", "start", 12, P["value_t"], 600))
    b.append(text(x + 24, Y(100) + 18, "from the owner's own growth view", "start", 10.5, P["muted"]))
    b.append(f'<line x1="{x-16}" y1="{Y(85)}" x2="{x+16}" y2="{Y(85)}" stroke="{P["value_t"]}" stroke-width="3"/>')
    b.append(text(x + 24, Y(85) + 4, "the most the owner will pay: 85", "start", 12, P["value_t"], 600))
    b.append(text(x + 24, Y(85) + 18, "value × 0.85 (tier 1), 0.75 (tier 2), 0.65 (tier 3)", "start", 10.5, P["muted"]))
    b.append(circ(x, Y(93), 7))
    b.append(text(x - 24, Y(93) + 4, "price today: 93", "end", 12, P["price_t"], 600))
    b.append(text(x - 24, Y(93) + 18, "above the line: wait", "end", 10.5, P["muted"]))
    b.append(f'<line x1="{x-16}" y1="{Y(62)}" x2="{x+16}" y2="{Y(62)}" stroke="{P["fail"]}" stroke-width="3"/>')
    b.append(cross(x, Y(62), 14))
    b.append(text(x + 24, Y(62) + 4, "stop: sell if it falls here", "start", 12, P["fail_t"], 600))
    b.append(text(x + 24, Y(62) + 18, "set before entry, never after", "start", 10.5, P["muted"]))
    b.append(box(x + 24, Y(42), 236, 74, ["conditions, written down:", "the catalyst still dated,", "no hard kill in the latest figures,", "the stop entered first"], P["owner_f"], P["owner_t"], 11))
    b.append(text(x, 30, "price per share", "middle", 11, P["muted"]))
    b.append(text(20, 352, "a buy below X, under conditions Y, with stop Z", "start", 12.5, P["ink"], 600))
    b.append(text(20, 370, "the tool reports the distance to X and whether Z is breached;", "start", 10.5, P["muted"]))
    b.append(text(20, 385, "it never says buy", "start", 10.5, P["muted"]))
    return figure(fid, W, H,
                  "A buy price with its conditions and its stop",
                  "A vertical scale. At 100, a blue square marks the base-case value. Between 100 and 85 a light blue band marks the cushion, with a blue line at 85 labelled the most the owner will pay. An orange circle at 93 marks today's price, labelled above the line, wait. Lower down, a vermillion line with a cross marks the stop. A purple box lists the written conditions.",
                  "".join(b),
                  "Never 'a buy'. A buy below a stated price, under stated conditions, with a stated exit. All three are written before the money moves, and the tool only reports where today's price stands against them.")

def fig_refusal_tracked():
    fid = "f-shadow"
    W, H = 480, 240
    b = []
    b.append(f'<line x1="40" y1="190" x2="460" y2="190" stroke="{P["rule"]}" stroke-width="1.5"/>')
    b.append(text(60, 208, "verdict day", "middle", 11, P["muted"]))
    b.append(text(440, 208, "a year later", "middle", 11, P["muted"]))
    # verdict marker
    b.append(f'<line x1="60" y1="60" x2="60" y2="190" stroke="{P["ink"]}" stroke-width="2" stroke-dasharray="4 3"/>')
    b.append(box(70, 40, 190, 70, ["recorded that day:", "the date, the closing price,", "one line naming what decided it"], P["surface"], P["ink"], 11))
    b.append(box(270, 40, 190, 70, ["not recorded:", "a thesis, a target,", "an expectation, an argument"], P["surface"], P["rule"], 11, color=P["muted"], dash="4 3"))
    # lines
    npts = [(60, 150), (140, 160), (220, 135), (300, 145), (380, 120), (440, 125)]
    bpts = [(60, 150), (140, 148), (220, 144), (300, 140), (380, 136), (440, 132)]
    b.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in bpts) + f'" fill="none" stroke="{P["ink"]}" stroke-width="2" stroke-dasharray="5 4"/>')
    b.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in npts) + f'" fill="none" stroke="{P["price"]}" stroke-width="2.5"/>')
    for x, y in npts:
        b.append(circ(x, y))
    b.append(text(452, 128, "the refused name", "start", 11, P["price_t"]).replace('x="452"', 'x="300"').replace('y="128"', 'y="172"'))
    b.append(text(300, 186, "an index, same currency, same kind of return", "start", 11, P["muted"]).replace('x="300"', 'x="120"'))
    b.append(text(240, 230, "read once a year, on purpose, so a scoreboard cannot bend a rule", "middle", 11, P["ink"]))
    return figure(fid, W, H,
                  "A refusal tracked forward",
                  "A timeline from the verdict day to a year later. A box lists what is recorded on the day: the date, the closing price, one line naming what decided it. A dashed box lists what is not recorded: a thesis, a target, an expectation. An orange line with circles follows the refused name, a dashed black line follows an index.",
                  "".join(b),
                  "Every refusal is measured afterwards against the market, from the day it was written. What is recorded is deliberately thin: a date, a price, one reason. A row that argues is a row that will be re-argued.")


# ---------------------------------------------------------------------------
# PART TWO
# ---------------------------------------------------------------------------

def fig_measure_decide():
    fid = "f-line"
    W, H = 480, 230
    b = []
    b.append(text(120, 26, "the tool may", "middle", 13, P["ink"], 600))
    b.append(text(360, 26, "only the owner may", "middle", 13, P["owner_t"], 600))
    b.append(wall(240, 10, 240, 200))
    left = ["fetch prices and filings", "compute a fixed set of figures", "compare a price to a line", "write a report and a page", "point at what needs a look", "say DATA MISSING"]
    right = ["enter a name", "assign a tier", "write a growth view", "set a value, a buy line, a stop", "move a name between statuses", "decide"]
    for i, s in enumerate(left):
        b.append(text(20, 56 + i * 24, s, "start", 12.5, P["ink"]))
    for i, s in enumerate(right):
        b.append(text(260, 56 + i * 24, s, "start", 12.5, P["owner_t"]))
    b.append(text(240, 222, "the wall is code: a write across it fails the run", "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "The line the tool never crosses",
                  "Two columns separated by a thick vertical wall. Left, what the tool may do: fetch, compute, compare, write a report, point, say data missing. Right, in purple, what only the owner may do: enter a name, assign a tier, write a growth view, set a value or stop, move a name, decide.",
                  "".join(b),
                  "The governing rule as a wall. Everything on the left is measurement. Everything on the right is a decision, and the code that writes measurements is built so it cannot write a decision.")



def fig_pieces_walls():
    fid = "f-pieces"
    W, H = 480, 410
    b = []
    b.append(text(20, 24, "outside the machine", "start", 11, P["muted"]))
    b.append(box(20, 30, 130, 40, ["price feeds, filings"], P["surface"], P["rule"], 11))
    b.append(arrow(fid, 85, 72, 85, 100))
    b.append(box(20, 102, 130, 44, ["FETCH", "brings figures in"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 152, 124, 178, 124))
    b.append(box(180, 102, 130, 44, ["THE RECORD", "keeps every figure"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 312, 124, 338, 124))
    b.append(box(340, 102, 120, 44, ["COMPUTE", "no files, no network"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 400, 148, 400, 176))
    b.append(box(340, 178, 120, 44, ["REPORT and PAGE", "state, never advice"], P["surface"], P["ink"], 11))
    b.append(box(20, 178, 130, 44, ["SCREEN", "2,000 to a shortlist"], P["surface"], P["ink"], 11))
    b.append(box(180, 178, 130, 44, ["WATCH", "filings and prices"], P["surface"], P["ink"], 11))
    b.append(box(180, 248, 130, 44, ["HEARTBEAT", "says the run happened"], P["surface"], P["ink"], 11))
    # compute wall
    b.append(wall(326, 84, 326, 164))
    b.append(text(322, 80, "wall: the arithmetic never fetches", "end", 10, P["ink"], 600))
    # watchlist wall
    b.append(wall(12, 318, 330, 318))
    b.append(text(12, 336, "wall: nothing that runs on a schedule may write below this line", "start", 10, P["ink"], 600))
    b.append(box(20, 346, 240, 54, ["THE WATCHLIST: the owner's file", "statuses, tiers, values, stops;", "every decision, written by hand"], P["owner_f"], P["owner_t"], 10.5))
    b.append(path_arrow(fid, "M 100 346 C 100 300, 85 260, 85 224", "", 1.5, "4 3"))
    b.append(text(104, 300, "read only", "start", 10, P["muted"]))
    b.append(text(340, 262, "solid arrows: figures flow", "start", 10, P["muted"]))
    b.append(text(340, 278, "dashed: read, never written", "start", 10, P["muted"]))
    b.append(text(340, 294, "thick lines: walls in code", "start", 10, P["muted"]))
    b.append(text(280, 372, "the owner", "start", 10.5, P["owner_t"], 600))
    b.append(text(280, 386, "writes here", "start", 10.5, P["owner_t"], 600))
    return figure(fid, W, H,
                  "The program's pieces and the walls between them",
                  "Boxes for FETCH, THE RECORD, COMPUTE, REPORT and PAGE, SCREEN, WATCH and HEARTBEAT, with arrows showing figures flowing from outside feeds through fetch and the record to compute and the report. A purple box at the bottom, THE WATCHLIST, the owner's file, is separated from the pieces by a thick wall labelled: nothing that runs on a schedule may write below this line. A second wall separates compute from fetching.",
                  "".join(b),
                  "Seven kinds of piece and two walls. Figures flow left to right and down. The owner's file sits below a wall that no scheduled piece can write across, and the arithmetic sits behind a wall that keeps it away from the network and the clock.")


def fig_figure_journey():
    fid = "f-journey"
    W, H = 420, 560
    b = []
    steps = [
        ("the issuer's filing", "the company's own report, dated", P["surface"], P["ink"]),
        ("read from the page", "figure, period, source, page number", P["surface"], P["ink"]),
        ("entered UNVERIFIED", "a stated figure, not yet checked", None, P["miss"]),
        ("read back by the owner", "against the page named beside it", P["owner_f"], P["owner_t"]),
        ("VERIFIED, and which kind", "tagged · cross-document · same page", P["pass_f"], P["pass_"]),
        ("the run record", "eight declarations, or no value at all", P["surface"], P["ink"]),
        ("a value, then a distance", "the page shows how far the price is", P["value_f"], P["value"]),
    ]
    y = 16
    for i, (t, s, fill, stroke) in enumerate(steps):
        if fill is None:
            b.append(hbox(fid, 30, y, 260, 50, [t, s], 11, ow=232))
        else:
            b.append(box(30, y, 260, 50, [t, s], fill, stroke, 11))
        if i >= 1:
            b.append(f'<rect x="300" y="{y+8}" width="100" height="34" rx="3" fill="{P["paper"]}" stroke="{P["rule"]}" stroke-width="1.5" stroke-dasharray="3 2"/>')
            b.append(lines(350, y + 22, ["source · period", "page · date"], "middle", 9.5, P["muted"]))
        if i < len(steps) - 1:
            b.append(arrow(fid, 160, y + 52, 160, y + 68))
        y += 70
    b.append(text(210, y + 8, "the tag travels with the figure and is printed beside it", "middle", 11, P["ink"], 600))
    b.append(text(210, y + 26, "a figure with no tag, or of the wrong period, is DATA MISSING", "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "A figure's journey from filing to page, with its provenance attached",
                  "Seven boxes top to bottom: the issuer's filing; read from the page; entered UNVERIFIED, hatched; read back by the owner, purple; VERIFIED and which kind, green; the run record; a value then a distance, blue. Beside each step from the second on, a small dashed tag reads source, period, page, date.",
                  "".join(b),
                  "One number's path. It enters as unverified, is read back by a person, and only then carries a verified mark that says what kind of check it survived. Its origin rides with it to the page.")

def fig_nightly_cycle():
    fid = "f-night"
    W, H = 480, 260
    b = []
    # clock
    b.append(f'<circle cx="60" cy="70" r="30" fill="{P["surface"]}" stroke="{P["ink"]}" stroke-width="2"/>')
    b.append(f'<line x1="60" y1="70" x2="60" y2="48" stroke="{P["ink"]}" stroke-width="2.5"/>')
    b.append(f'<line x1="60" y1="70" x2="74" y2="78" stroke="{P["ink"]}" stroke-width="2.5"/>')
    b.append(text(60, 118, "22:30 every night", "middle", 11, P["muted"]))
    b.append(arrow(fid, 92, 70, 126, 70))
    b.append(box(128, 40, 130, 60, ["the run", "fetch prices, compare", "to lines already set"], P["surface"], P["ink"], 11))
    # success branch
    b.append(arrow(fid, 260, 58, 300, 40, "pass"))
    b.append(box(302, 14, 158, 52, ["report and page written;", "one ping to the outside"], P["pass_f"], P["pass_"], 11))
    b.append(tick(450, 20, 14))
    # failure branch
    b.append(arrow(fid, 260, 84, 300, 104, "fail"))
    b.append(box(302, 92, 158, 52, ["a push to the phone:", "what stopped, last log lines"], P["fail_f"], P["fail"], 11))
    b.append(cross(450, 98, 14))
    b.append(text(240, 168, "success is quiet on the phone and loud to the observer;", "middle", 11.5, P["ink"]))
    b.append(text(240, 184, "failure is loud on the phone. Silence means something else.", "middle", 11.5, P["ink"]))
    b.append(text(240, 214, "the run cannot write a decision: only the two folders", "middle", 11, P["muted"]))
    b.append(text(240, 230, "for data and reports are writable to it", "middle", 11, P["muted"]))
    return figure(fid, W, H,
                  "The nightly cycle with both exits",
                  "A clock at 22:30 leads to a box, the run. A green arrow leads to a box with a tick: report and page written, one ping to the outside. A vermillion arrow leads to a box with a cross: a push to the phone saying what stopped.",
                  "".join(b),
                  "A clock fires, prices are checked against decisions already made, and files are written. Two exits: on success the machine tells an outside observer it is alive; on failure it tells the owner's phone what stopped.")



def fig_two_observers():
    fid = "f-obs"
    W, H = 480, 320
    b = []
    b.append(text(120, 22, "the machine is up, the run broke", "middle", 12, P["ink"], 600))
    b.append(f'<rect x="20" y="32" width="200" height="120" rx="8" fill="{P["surface"]}" stroke="{P["ink"]}" stroke-width="2"/>')
    b.append(box(34, 46, 80, 40, ["the run"], P["fail_f"], P["fail"], 11))
    b.append(cross(106, 52, 12))
    b.append(arrow(fid, 116, 66, 150, 66, "fail"))
    b.append(box(152, 46, 58, 40, ["observer", "one"], P["surface"], P["ink"], 10))
    b.append(arrow(fid, 181, 88, 181, 118, "fail"))
    b.append(text(181, 140, "phone: what stopped", "middle", 10.5, P["fail_t"], 600))
    b.append(text(120, 174, "no ping leaves the machine", "middle", 10.5, P["muted"]))
    b.append(text(360, 22, "the machine is off", "middle", 12, P["ink"], 600))
    b.append(f'<rect x="260" y="32" width="200" height="120" rx="8" fill="url(#{fid}-hatch)" stroke="{P["miss"]}" stroke-width="2"/>')
    b.append(f'<rect x="300" y="72" width="120" height="40" rx="4" fill="{P["paper"]}" opacity="0.94"/>')
    b.append(lines(360, 88, ["nothing runs,", "nothing can shout"], "middle", 11, P["miss_t"]))
    b.append(text(360, 174, "no ping leaves the machine", "middle", 10.5, P["muted"]))
    b.append(wall(10, 196, 470, 196))
    b.append(text(20, 214, "outside the machine", "start", 11, P["muted"]))
    b.append(box(150, 224, 180, 46, ["observer two", "expects one ping a day"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 120, 152, 200, 222, "", 1.5, "4 3"))
    b.append(arrow(fid, 360, 152, 280, 222, "", 1.5, "4 3"))
    b.append(text(240, 292, "no ping by the deadline: it alarms.", "middle", 11, P["fail_t"], 600))
    b.append(text(240, 308, "Absence is the one signal a dead machine can still send.", "middle", 11, P["fail_t"], 600))
    return figure(fid, W, H,
                  "Two observers: one on the machine, one outside it",
                  "Left panel: the machine is up and the run broke; observer one, on the machine, pushes to the phone what stopped. Right panel: the machine is off, drawn hatched; nothing runs and nothing can shout. Below a thick wall, outside the machine, observer two expects one ping a day. Dashed arrows from both panels lead to it. Text reads: no ping by the deadline, it alarms.",
                  "".join(b),
                  "Two observers for two failures. The one on the machine can describe what broke, but only while the machine is alive to run it. The one outside knows nothing except whether the daily ping arrived, and that is the only alarm a dead machine can raise.")

def fig_tunnel():
    fid = "f-tunnel"
    W, H = 480, 280
    b = []
    # machine
    b.append(f'<rect x="20" y="30" width="190" height="210" rx="8" fill="{P["surface"]}" stroke="{P["ink"]}" stroke-width="2"/>')
    b.append(text(115, 52, "the machine", "middle", 12, P["ink"], 600))
    b.append(box(36, 66, 158, 46, ["a small server, listening", "only to itself"], P["surface"], P["ink"], 11))
    b.append(text(115, 128, "the page", "middle", 11, P["muted"]))
    b.append(arrow(fid, 115, 114, 115, 150))
    b.append(box(36, 152, 158, 46, ["the tunnel client", "dials OUT and holds the line"], P["surface"], P["ink"], 11))
    # wall
    b.append(wall(226, 20, 226, 250))
    b.append(text(226, 266, "firewall: no inbound port opened", "middle", 11, P["ink"], 600))
    # outbound arrow crossing
    b.append(arrow(fid, 196, 175, 262, 175, "", 3))
    b.append(text(232, 166, "out", "middle", 10, P["ink"], 600).replace('x="232"', 'x="229"'))
    # inbound attempts blocked
    for y in (80, 110):
        b.append(f'<line x1="300" y1="{y}" x2="240" y2="{y}" stroke="{P["fail_t"]}" stroke-width="2" stroke-dasharray="4 3"/>')
        b.append(cross(238, y, 14))
    b.append(text(304, 84, "anything dialling in", "start", 10.5, P["fail_t"]))
    b.append(text(304, 114, "is refused at the wall", "start", 10.5, P["fail_t"]))
    # relay and front door
    b.append(box(264, 152, 90, 46, ["the relay", "outside"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 356, 175, 380, 175))
    b.append(box(382, 140, 84, 70, ["front door:", "who are you?", "one address,", "one-time code"], P["owner_f"], P["owner_t"], 10))
    b.append(arrow(fid, 424, 212, 424, 236, "owner"))
    b.append(text(424, 252, "the phone", "middle", 11, P["owner_t"], 600))
    return figure(fid, W, H,
                  "The tunnel: one outbound arrow crossing the wall",
                  "Inside a box labelled the machine: a small server listening only to itself, and a tunnel client that dials out. A thick vertical wall labelled firewall, no inbound port opened. One thick arrow crosses the wall outward to a relay. Two dashed inbound arrows are crossed out at the wall. After the relay, a purple front door asks who are you, then the phone.",
                  "".join(b),
                  "Nothing dials in. The machine opens one line outward and holds it. A reader arrives at a front door outside the machine, proves who they are, and only then is the page fetched back down the line the machine opened.")



def fig_boundary():
    fid = "f-bound"
    W, H = 480, 270
    b = []
    b.append(text(20, 24, "the reports folder: dozens of files", "start", 10.5, P["ink"], 600))
    cols, rows = 8, 5
    for r in range(rows):
        for c in range(cols):
            x = 20 + c * 24
            y = 34 + r * 22
            if r == 2 and c == 3:
                b.append(f'<rect x="{x}" y="{y}" width="20" height="18" rx="2" fill="{P["value_f"]}" stroke="{P["value"]}" stroke-width="2"/>')
            else:
                b.append(f'<rect x="{x}" y="{y}" width="20" height="18" rx="2" fill="url(#{fid}-hatch)" stroke="{P["miss"]}" stroke-width="1"/>')
    b.append(text(20, 162, "one file served: the overview page", "start", 10.5, P["value_t"], 600))
    b.append(text(20, 178, "every other file: research, records,", "start", 10.5, P["muted"]))
    b.append(text(20, 192, "daily runs — stays behind the line", "start", 10.5, P["muted"]))
    b.append(wall(230, 20, 230, 210))
    b.append(box(246, 40, 170, 60, ["the server's one rule:", '"/" → the page', "anything else → not found"], P["surface"], P["ink"], 11))
    b.append(arrow(fid, 470, 70, 420, 70, "pass"))
    b.append(text(468, 122, "a request for /", "end", 10.5, P["pass_t"]))
    b.append(f'<line x1="470" y1="160" x2="426" y2="160" stroke="{P["fail_t"]}" stroke-width="2" stroke-dasharray="4 3"/>')
    b.append(cross(422, 160, 14))
    b.append(text(468, 184, "a request for anything else", "end", 10.5, P["fail_t"]))
    b.append(text(240, 236, "the rule is one block of configuration; remove it and every file", "middle", 10.5, P["ink"]))
    b.append(text(240, 252, "in the folder is served, and nothing would alarm", "middle", 10.5, P["ink"]))
    return figure(fid, W, H,
                  "The one-path boundary",
                  "Left: a grid of forty small hatched file icons with one blue icon among them, labelled: one file is served, every other file stays behind the line. A thick wall. Right: the server's one rule, slash goes to the page, anything else goes to not found. A green arrow for a request for slash reaches the server; a dashed vermillion arrow for anything else is crossed out before it.",
                  "".join(b),
                  "The server knows one address and answers every other with 'not found'. The folder behind it holds dozens of private files. The difference between one file exposed and all of them is a single block of configuration.")

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
