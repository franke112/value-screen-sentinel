"""Build the site: one HTML file per chapter, an index, a sources page.

Run from anywhere:  python3 docs/the-method/_build/build.py
Writes into docs/the-method/. The site needs nothing from this folder to run;
the generator exists so the chapter list stays identical on every page.
"""

import os
import re
import sys
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import content1  # noqa: E402  (registers chapters 1-12)
import content2  # noqa: E402  (registers chapters 13-23)
from content1 import CHAPTERS  # noqa: E402

SITE = "The slow way, made survivable"
TAGLINE = "A value-investing method, and the machine that keeps it honest."
BUILT = "2026-09-13"
PART1 = "Part One · The method"
PART2 = "Part Two · The machine"


def part_of(i):
    return 1 if i < 12 else 2


def chapter_list(current=None):
    """The sidebar / menu. Identical on every page."""
    items = ['<li class="home"><a href="index.html"%s><span class="n">&nbsp;</span>Start here: the map</a></li>'
             % (' aria-current="page"' if current == "index" else "")]
    for i, c in enumerate(CHAPTERS):
        if i == 0:
            items.append(f'<li class="part">{PART1}</li>')
        if i == 12:
            items.append(f'<li class="part">{PART2}</li>')
        cur = ' aria-current="page"' if c["slug"] == current else ""
        short = '<span class="short">10-min route</span>' if c["short"] else ""
        items.append(f'<li><a href="{c["slug"]}.html"{cur}><span class="n">{i+1}</span><span>{escape(c["title"])}</span>{short}</a></li>')
    items.append('<li class="part">Appendix</li>')
    items.append('<li><a href="sources.html"%s><span class="n">&nbsp;</span>All sources</a></li>' % (' aria-current="page"' if current == "sources" else ""))
    return ('<div class="chapters"><input type="checkbox" id="menu-toggle" class="menu-toggle">'
            '<label for="menu-toggle" class="menu-label">Contents</label>'
            '<nav aria-label="Chapters" id="contents"><ol>' + "".join(items) + "</ol></nav></div>")


def page(slug, title, where, body, description):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · {SITE}</title>
<meta name="description" content="{escape(description)}">
<link rel="stylesheet" href="style.css">
</head>
<body data-page="{slug}" data-title="{escape(title)}">
<a class="skip" href="#main">Skip to content</a>
<header class="top">
<a class="brand" href="index.html">{SITE}</a>
<span class="where">{where}</span>
</header>
<div class="frame">
{chapter_list(slug)}
<main id="main">
<div class="article">
{body}
</div>
</main>
</div>
<script src="site.js"></script>
</body>
</html>
"""


def pager(i):
    prev_a = next_a = ""
    if i > 0:
        p = CHAPTERS[i - 1]
        prev_a = f'<a class="prev" href="{p["slug"]}.html" rel="prev"><span class="lab">Previous · {i}</span>{escape(p["title"])}</a>'
    else:
        prev_a = '<a class="prev" href="index.html" rel="prev"><span class="lab">Previous</span>Start here: the map</a>'
    if i < len(CHAPTERS) - 1:
        n = CHAPTERS[i + 1]
        next_a = f'<a class="next" href="{n["slug"]}.html" rel="next"><span class="lab">Next · {i+2}</span>{escape(n["title"])}</a>'
    else:
        next_a = '<a class="next" href="sources.html" rel="next"><span class="lab">Next</span>All sources</a>'
    short_a = ""
    if CHAPTERS[i]["short"]:
        later = [(j, c) for j, c in enumerate(CHAPTERS) if j > i and c["short"]]
        if later:
            j, c = later[0]
            short_a = f'<a class="short-next" href="{c["slug"]}.html"><span class="lab">Next on the 10-minute route · {j+1}</span>{escape(c["title"])}</a>'
        else:
            short_a = '<a class="short-next" href="index.html"><span class="lab">End of the 10-minute route</span>Back to the map</a>'
    return (f'<nav class="pager" aria-label="Previous and next chapter">{prev_a}{next_a}{short_a}'
            f'<span class="keys" hidden>Keyboard: ← previous chapter, → next chapter.</span></nav>')


def sources_block(c):
    if not c["sources"]:
        return ""
    lis = []
    for label, url in c["sources"]:
        if url.startswith("repo:"):
            lis.append(f'<li>{escape(label)} <span class="how">— read from this repository: {escape(url[5:].strip())}</span></li>')
        else:
            lis.append(f'<li>{escape(label)}<br><a href="{escape(url)}" rel="noopener">{escape(url)}</a></li>')
    return f'<section class="sources"><h2>Sources for this chapter</h2><ol>{"".join(lis)}</ol></section>'


def build_chapter(i, c):
    part = part_of(i)
    partname = PART1 if part == 1 else PART2
    where = f"Chapter {i+1} of {len(CHAPTERS)}"
    crumb = f'<p class="crumb"><a href="index.html">The map</a> · {partname} · Chapter {i+1} of {len(CHAPTERS)}</p>'
    route = ' · on the 10-minute route' if c["short"] else ""
    lede = f'<p class="lede">{escape(c["lede"])} <span class="time">About {c["minutes"]} minutes{route}.</span></p>'
    body = crumb + f"<h1>{escape(c['title'])}</h1>" + lede + c["body"] + sources_block(c) + pager(i)
    body += f'<p class="foot">{SITE}. Built {BUILT} from the repository as it stood that day. NAME A and NAME B are fictional; no company, price or holding appears on this site.</p>'
    html = page(c["slug"], c["title"], where, body, c["lede"])
    with open(os.path.join(OUT, c["slug"] + ".html"), "w", encoding="utf-8") as f:
        f.write(html)


def build_index():
    short = [c for c in CHAPTERS if c["short"]]
    short_min = sum(c["minutes"] for c in short)
    total_min = sum(c["minutes"] for c in CHAPTERS)
    first_short = short[0]["slug"]
    toc = []
    for i, c in enumerate(CHAPTERS):
        if i == 0:
            toc.append(f'<li class="part">{PART1}</li>')
        if i == 12:
            toc.append(f'<li class="part">{PART2}</li>')
        route = '<span class="short">10-min route</span>' if c["short"] else ""
        toc.append(f'<li><a href="{c["slug"]}.html"><span class="n">{i+1}</span><span class="t">{escape(c["title"])}</span>'
                   f'<span class="s">{escape(c["lede"])}</span><span class="m">About {c["minutes"]} min{route}</span></a></li>')
    body = f"""
<p class="crumb">Start here</p>
<h1>{SITE}</h1>
<p class="lede">{TAGLINE} Twenty-three short chapters in two parts, for a reader who has never heard of value investing and does not know what a scheduled job is. It sells nothing. If you finish it you will not know what to buy; you will know what it takes to find out.</p>

<div id="continue" hidden></div>

<div class="routes">
<div class="route"><h2>Ten minutes</h2><p>Seven chapters that carry the whole argument: the problem, what value is, the inversion, writing the belief first, why the machine cannot decide, the dead man's switch, and the close. About {short_min} minutes.</p><a class="go" href="{first_short}.html">Start the short route</a></div>
<div class="route"><h2>The whole thing</h2><p>All twenty-three chapters in order. Part One is the method; Part Two is the machine. About {total_min} minutes, in sittings. Each chapter says what it is about in its first line.</p><a class="go" href="{CHAPTERS[0]["slug"]}.html">Start at chapter 1</a></div>
</div>

<h2>How the site is built to be read</h2>
<p>Every page has the full chapter list, a line saying where you are, and previous and next links that name the neighbouring chapters. The left and right arrow keys move between chapters. Each chapter has at most one level of fold: "the exact rule" and "where this comes from" open on demand and can be ignored. Numbered notes sit in the margin beside their sentence on a wide screen, and directly after the sentence on a phone. Nothing needs a network connection, and everything works with scripts off; a script only adds the arrow keys, the "continue" link, and one movable figure in chapter 7.</p>

<h2>The colours, and what each one means</h2>
<p>Five meanings, one colour each, the same in every figure, never the only signal.</p>
<ul>
<li><span class="sw sw-value"></span><strong>Value</strong>, blue: what a business is worth, and the owner's estimate of it. Square markers.</li>
<li><span class="sw sw-price"></span><strong>Price</strong>, orange: what the market quotes. Circle markers.</li>
<li><span class="sw sw-pass"></span><strong>Pass</strong>, green: a test passed, a signal arrived. Tick.</li>
<li><span class="sw sw-fail"></span><strong>Fail or alarm</strong>, vermillion: a test failed, a stop, an alert. Cross.</li>
<li><span class="sw sw-miss"></span><strong>Missing</strong>, hatched grey: could not be checked. Question mark.</li>
<li><span class="sw sw-owner"></span><strong>The owner</strong>, purple: a human decision.</li>
</ul>

<h2>The chapters</h2>
<ol class="toc">{"".join(toc)}</ol>

<h2>Two names</h2>
<p>Every worked example uses NAME A, and occasionally NAME B, which are fictional companies with round numbers. No real company, price, holding or address appears anywhere on this site; where a real defect is described, the name has been removed.</p>
<p class="foot">{SITE}. Built {BUILT}. The research behind the design and the sources for every borrowed idea are in <a href="sources.html">All sources</a>.</p>
"""
    html = page("index", SITE, "Start here", body, TAGLINE)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def build_sources():
    seen = {}
    order = []
    for i, c in enumerate(CHAPTERS):
        for label, url in c["sources"]:
            key = url if not url.startswith("repo:") else label
            if key not in seen:
                seen[key] = (label, url, [])
                order.append(key)
            seen[key][2].append(i + 1)
    ext, repo = [], []
    for k in order:
        label, url, chs = seen[k]
        chs_s = ", ".join(str(n) for n in chs)
        if url.startswith("repo:"):
            repo.append(f'<li>{escape(label)} <span class="how">— {escape(url[5:].strip())} (chapter {chs_s})</span></li>')
        else:
            ext.append(f'<li>{escape(label)}<br><a href="{escape(url)}" rel="noopener">{escape(url)}</a> <span class="how">(chapter {chs_s})</span></li>')
    body = f"""
<p class="crumb"><a href="index.html">The map</a> · Appendix</p>
<h1>All sources</h1>
<p class="lede">Every borrowed idea with the place it was borrowed from, and every claim about the system with the file it was read from. Nothing in the method was invented here.</p>
<section class="sources">
<h2>Ideas and evidence outside the project</h2>
<ol>{"".join(ext)}</ol>
<h2>Read from the repository</h2>
<p>These are files in the project's own repository, which is private. They are named so that the owner, or anyone the owner shows the repository to, can check each claim against the line it came from.</p>
<ol>{"".join(repo)}</ol>
<h2>How the site itself was designed</h2>
<p>The choice of a chaptered site over a single page, the pattern used for each kind of content, the colour system and the accessibility checks are recorded with their sources and their costs in the file <code>RESEARCH-NOTES.md</code> that ships beside these pages.</p>
</section>
{'<nav class="pager" aria-label="Previous and next"><a class="prev" href="' + CHAPTERS[-1]["slug"] + '.html" rel="prev"><span class="lab">Previous · 23</span>' + escape(CHAPTERS[-1]["title"]) + '</a><a class="next" href="index.html" rel="next"><span class="lab">Back to</span>The map</a><span class="keys" hidden>Keyboard: ← previous chapter, → next chapter.</span></nav>'}
<p class="foot">{SITE}. Built {BUILT}.</p>
"""
    html = page("sources", "All sources", "Appendix", body, "Every source for the site, external and from the repository.")
    with open(os.path.join(OUT, "sources.html"), "w", encoding="utf-8") as f:
        f.write(html)


def main():
    for i, c in enumerate(CHAPTERS):
        build_chapter(i, c)
    build_index()
    build_sources()
    print(f"built {len(CHAPTERS)} chapters + index + sources into {OUT}")


if __name__ == "__main__":
    main()
