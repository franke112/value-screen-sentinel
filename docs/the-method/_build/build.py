"""Build the site: one HTML file per chapter, an index, a ten-minute page, a
sources page -- in English (docs/the-method/) and Swedish (docs/the-method/sv/).

The order, the reading routes and the old addresses are in order.py; the
frame every chapter shares (claim, CENTA, test, try it, three lines) is in
frame.py; the chapters assembled or added in the redesign of 2026-11-09 are
in content3.py; the interactive figures are in figures.py.

Run from anywhere:  python3 docs/the-method/_build/build.py
Writes into docs/the-method/ and docs/the-method/sv/. The site needs nothing
from this folder to run; the generator exists so the chapter list stays
identical on every page, in both languages.

The Swedish chapters live in content1_sv.py / content2_sv.py / diagrams_sv.py,
translated with the terms in GLOSSARY-sv.md. Slugs are the same in both
languages, so the switch on every page lands on the same chapter.
"""

import importlib
import os
import re
import sys
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import content3  # noqa: E402
import figures   # noqa: E402
import frame     # noqa: E402
import order     # noqa: E402

BUILT = "2026-11-09"
REPO_URL = "https://github.com/franke112/value-screen-sentinel"

S = {
    "en": dict(
        html_lang="en",
        site="The slow way, made survivable",
        tagline="A value-investing method, and the machine that keeps it honest.",
        part1="Part One · The method", part2="Part Two · The machine",
        prologue="Prologue", tests="The tests", close="The close",
        ten_title="The book in ten minutes", ten_nav="In ten minutes",
        ten_lede="Every chapter's claim and its three lines, in order. Each heading leads to the chapter.",
        route_investor="the investor's route", route_builder="the builder's route",
        next_on="Next on {route}", end_of="End of {route}",
        this_chapter="this chapter", This_chapter="This chapter",
        the_prologue="the prologue", The_prologue="The prologue",
        chapter_word="chapter", Chapter_word="Chapter",
        moved="This page has moved.", moved_go="Go to the new page",
        appendix="Appendix", all_sources="All sources",
        start_map="Start here: the map", the_map="The map", start_here="Start here",
        short_tag="10-min route", contents="Contents", chapters_label="Chapters",
        skip="Skip to content",
        prev="Previous", next="Next", back_to="Back to",
        next_short="Next on the 10-minute route", end_short="End of the 10-minute route",
        back_map="Back to the map",
        keys="Keyboard: ← previous chapter, → next chapter.",
        pager_label="Previous and next chapter", pager_label_src="Previous and next",
        read_repo="read from this repository:",
        sources_h="Sources for this chapter",
        chapter_of="Chapter {i} of {n}", on_route=" · on the 10-minute route",
        about_min="About {m} minutes", about_min_short="About {m} min",
        chapter_n="chapter {c}",
        nfa="Not financial advice: one private investor&#x27;s method, shared as it is.",
        foot_chapter="{site}. Built {built} from the repository as it stood that day. NAME A and NAME B are "
                     "fictional. One real company, CENTA, is followed through the book, with figures from its "
                     "own filings and the owner's own trades.",
        switch_label="Svenska", switch_lang="sv",
        sources_desc="Every source for the site, external and from the repository.",
    ),
    "sv": dict(
        html_lang="sv",
        site="Den långsamma vägen, gjord uthärdlig",
        tagline="En metod för värdeinvestering, och maskinen som håller den ärlig.",
        part1="Del ett · Metoden", part2="Del två · Maskinen",
        prologue="Prolog", tests="Testerna", close="Avslutning",
        ten_title="Boken på tio minuter", ten_nav="På tio minuter",
        ten_lede="Varje kapitels påstående och dess tre rader, i ordning. Varje rubrik leder till kapitlet.",
        route_investor="investerarens väg", route_builder="byggarens väg",
        next_on="Nästa på {route}", end_of="Slut på {route}",
        this_chapter="det här kapitlet", This_chapter="Det här kapitlet",
        the_prologue="prologen", The_prologue="Prologen",
        chapter_word="kapitel", Chapter_word="Kapitel",
        moved="Den här sidan har flyttat.", moved_go="Gå till den nya sidan",
        appendix="Bilaga", all_sources="Alla källor",
        start_map="Börja här: kartan", the_map="Kartan", start_here="Börja här",
        short_tag="tiominutersvägen", contents="Innehåll", chapters_label="Kapitel",
        skip="Hoppa till innehållet",
        prev="Föregående", next="Nästa", back_to="Tillbaka till",
        next_short="Nästa på tiominutersvägen", end_short="Slut på tiominutersvägen",
        back_map="Tillbaka till kartan",
        keys="Tangentbord: ← föregående kapitel, → nästa kapitel.",
        pager_label="Föregående och nästa kapitel", pager_label_src="Föregående och nästa",
        read_repo="läst ur det här repot:",
        sources_h="Källor för det här kapitlet",
        chapter_of="Kapitel {i} av {n}", on_route=" · på tiominutersvägen",
        about_min="Ungefär {m} minuter", about_min_short="Ca {m} min",
        chapter_n="kapitel {c}",
        nfa="Inte finansiell rådgivning: en privatinvesterares metod, delad som den är.",
        foot_chapter="{site}. Byggd {built} ur repot som det såg ut den dagen. BOLAG A och BOLAG B är "
                     "påhittade. Ett verkligt bolag, CENTA, följs genom boken, med siffror ur dess egna "
                     "rapporter och ägarens egna affärer.",
        switch_label="English", switch_lang="en",
        sources_desc="Varje källa för sajten, externa och ur repot.",
    ),
}


class Site:
    def __init__(self, lang, chapters, out, asset_prefix, other_prefix):
        self.lang, self.t, self.chapters = lang, S[lang], chapters
        self.out, self.asset, self.other = out, asset_prefix, other_prefix
        self.frame, self.lab = frame.FRAME[lang], frame.LABELS[lang]
        # the number a chapter carries; the prologue carries none
        self.num, n = {}, 0
        for c in chapters:
            if c["slug"] not in order.UNNUMBERED:
                n += 1
                self.num[c["slug"]] = n
        self.count = n
        self.index_of = {c["slug"]: i for i, c in enumerate(chapters)}

    # -- names and numbers -------------------------------------------------
    def label(self, slug):
        """What the margin shows beside a chapter: its number, or a dot."""
        return str(self.num[slug]) if slug in self.num else "·"

    def where(self, slug):
        t = self.t
        if slug not in self.num:
            return t["prologue"]
        return t["chapter_of"].format(i=self.num[slug], n=self.count)

    def resolve(self, html, current):
        """[[ch:slug]] -> "chapter 14"; [[Ch:slug]] capitalised; [[n:slug]] -> "14";
        [[fig:name]] -> the interactive figure. A reference to the chapter it
        stands in reads "this chapter"."""
        t = self.t

        def ref(m):
            kind, slug = m.group(1), m.group(2)
            if kind == "fig":
                return figures.FIGS[slug](self.lang)
            if slug not in self.index_of:
                raise KeyError(f"[[{kind}:{slug}]] in {current}: no such chapter")
            cap = kind == "Ch"
            if kind == "n":
                return self.label(slug)
            if slug == current:
                return t["This_chapter" if cap else "this_chapter"]
            if slug not in self.num:
                return t["The_prologue" if cap else "the_prologue"]
            return f'{t["Chapter_word" if cap else "chapter_word"]} {self.num[slug]}'

        return re.sub(r"\[\[(ch|Ch|n|fig):([a-z0-9-]+)\]\]", ref, html)

    def routes_of(self, slug):
        return [name for name, slugs in order.ROUTES.items() if slug in slugs]

    # -- shared pieces ---------------------------------------------------
    def part_label(self, key):
        return {"part1": self.t["part1"], "tests": self.t["tests"],
                "part2": self.t["part2"], "close": self.t["close"]}.get(key)

    def chapter_list(self, current=None):
        t = self.t
        cur = lambda name: ' aria-current="page"' if current == name else ""  # noqa: E731
        items = [f'<li class="home"><a href="index.html"{cur("index")}><span class="n">&nbsp;</span>{t["start_map"]}</a></li>',
                 f'<li class="home"><a href="ten-minutes.html"{cur("ten-minutes")}><span class="n">&nbsp;</span>{t["ten_nav"]}</a></li>']
        for key, slugs in order.PARTS:
            if self.part_label(key):
                items.append(f'<li class="part">{self.part_label(key)}</li>')
            for slug in slugs:
                c = self.chapters[self.index_of[slug]]
                items.append(f'<li><a href="{slug}.html"{cur(slug)}><span class="n">{self.label(slug)}</span>'
                             f'<span>{escape(c["title"])}</span></a></li>')
        items.append(f'<li class="part">{t["appendix"]}</li>')
        items.append(f'<li><a href="sources.html"{cur("sources")}><span class="n">&nbsp;</span>{t["all_sources"]}</a></li>')
        return ('<div class="chapters"><input type="checkbox" id="menu-toggle" class="menu-toggle">'
                f'<label for="menu-toggle" class="menu-label">{t["contents"]}</label>'
                f'<nav aria-label="{t["chapters_label"]}" id="contents"><ol>' + "".join(items) + "</ol></nav></div>")

    def page(self, slug, title, where, body, description):
        t = self.t
        file = "index.html" if slug == "index" else f"{slug}.html"
        alt = self.other + file
        here = file
        en_href, sv_href = (here, alt) if self.lang == "en" else (alt, here)
        return f"""<!DOCTYPE html>
<html lang="{t["html_lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · {t["site"]}</title>
<meta name="description" content="{escape(description)}">
<link rel="alternate" hreflang="en" href="{en_href}">
<link rel="alternate" hreflang="sv" href="{sv_href}">
<link rel="stylesheet" href="{self.asset}style.css">
</head>
<body data-page="{slug}" data-title="{escape(title)}">
<a class="skip" href="#main">{t["skip"]}</a>
<header class="top">
<a class="brand" href="index.html">{t["site"]}</a>
<span class="where">{where}</span>
<a class="lang" href="{alt}" hreflang="{t["switch_lang"]}" lang="{t["switch_lang"]}">{t["switch_label"]}</a>
</header>
<div class="frame">
{self.chapter_list(slug)}
<main id="main">
<div class="article">
{body}
</div>
</main>
</div>
<script src="{self.asset}site.js"></script>
</body>
</html>
"""

    def pager(self, i):
        t, C = self.t, self.chapters
        if i > 0:
            p = C[i - 1]
            prev_a = (f'<a class="prev" href="{p["slug"]}.html" rel="prev"><span class="lab">{t["prev"]} · '
                      f'{self.label(p["slug"])}</span>{escape(p["title"])}</a>')
        else:
            prev_a = f'<a class="prev" href="index.html" rel="prev"><span class="lab">{t["prev"]}</span>{t["start_map"]}</a>'
        if i < len(C) - 1:
            n = C[i + 1]
            next_a = (f'<a class="next" href="{n["slug"]}.html" rel="next"><span class="lab">{t["next"]} · '
                      f'{self.label(n["slug"])}</span>{escape(n["title"])}</a>')
        else:
            next_a = f'<a class="next" href="sources.html" rel="next"><span class="lab">{t["next"]}</span>{t["all_sources"]}</a>'
        # one line per route this chapter is on: where that route goes next
        route_as = ""
        slug = C[i]["slug"]
        for name in self.routes_of(slug):
            route, name_t = order.ROUTES[name], t["route_" + name]
            k = route.index(slug)
            if k + 1 < len(route):
                nxt = C[self.index_of[route[k + 1]]]
                if nxt is C[i + 1] if i + 1 < len(C) else False:
                    continue        # the ordinary "next" already goes there
                route_as += (f'<a class="short-next" href="{nxt["slug"]}.html"><span class="lab">'
                             f'{t["next_on"].format(route=name_t)} · {self.label(nxt["slug"])}</span>{escape(nxt["title"])}</a>')
        return (f'<nav class="pager" aria-label="{t["pager_label"]}">{prev_a}{next_a}{route_as}'
                f'<span class="keys" hidden>{t["keys"]}</span></nav>')

    def sources_block(self, c):
        t = self.t
        if not c["sources"]:
            return ""
        lis = []
        for label, url in c["sources"]:
            if url.startswith("repo:"):
                lis.append(f'<li>{escape(label)} <span class="how">— {t["read_repo"]} {escape(url[5:].strip())}</span></li>')
            else:
                lis.append(f'<li>{escape(label)}<br><a href="{escape(url)}" rel="noopener">{escape(url)}</a></li>')
        return f'<section class="sources"><h2>{t["sources_h"]}</h2><ol>{"".join(lis)}</ol></section>'

    def write(self, name, html):
        os.makedirs(self.out, exist_ok=True)
        with open(os.path.join(self.out, name), "w", encoding="utf-8") as f:
            f.write(html)

    # -- pages -----------------------------------------------------------
    def frame_blocks(self, slug):
        """(top, bottom): the claim above the chapter's text; CENTA, the test,
        the command and the three lines below it."""
        f, lab = self.frame.get(slug), self.lab
        if not f:
            return "", ""
        top = f'<p class="claim"><span class="tag">{lab["claim"]}</span>{f["claim"]}</p>'
        out = []
        if f["centa"]:
            out.append(f'<aside class="centa"><span class="tag">{lab["centa"]}</span><p>{f["centa"]}</p></aside>')
        if f["test"]:
            out.append(f'<div class="tested"><span class="tag">{lab["test"]}</span><p>{f["test"]}</p></div>')
        if f["tryit"]:
            cmd, note = f["tryit"]
            out.append(f'<div class="tryit"><span class="tag">{lab["tryit"]}</span>'
                       f'<pre><code>{escape(cmd)}</code></pre><p>{note} <span class="how">{lab["try_note"]}</span></p></div>')
        lis = "".join(f"<li>{line}</li>" for line in f["three"])
        out.append(f'<div class="three"><span class="tag">{lab["three"]}</span><ol>{lis}</ol></div>')
        return top, "".join(out)

    def build_chapter(self, i, c):
        t, slug = self.t, c["slug"]
        where = self.where(slug)
        part = self.part_label(order.part_of(slug))
        crumb = (f'<p class="crumb"><a href="index.html">{t["the_map"]}</a> · '
                 + (f"{part} · " if part else "") + f"{where}</p>")
        routes = "".join(f' · {t["route_" + name]}' for name in self.routes_of(slug))
        meta = f'<p class="meta">{t["about_min"].format(m=c["minutes"])}{routes}.</p>'
        top, bottom = self.frame_blocks(slug)
        body = (crumb + f"<h1>{escape(c['title'])}</h1>" + top + meta + c["body"] + bottom
                + self.sources_block(c) + self.pager(i))
        body += (f'<p class="foot">{t["foot_chapter"].format(site=t["site"], built=BUILT)} {t["nfa"]}</p>')
        body = self.resolve(body, slug)
        self.write(slug + ".html", self.page(slug, c["title"], where, body, c["lede"]))

    def build_index(self):
        t, C = self.t, self.chapters
        total_min = sum(c["minutes"] for c in C)
        toc = []
        for key, slugs in order.PARTS:
            if self.part_label(key):
                toc.append(f'<li class="part">{self.part_label(key)}</li>')
            for slug in slugs:
                c = C[self.index_of[slug]]
                tags = "".join(f'<span class="short">{t["route_" + name]}</span>' for name in self.routes_of(slug))
                toc.append(f'<li><a href="{slug}.html"><span class="n">{self.label(slug)}</span><span class="t">{escape(c["title"])}</span>'
                           f'<span class="s">{escape(c["lede"])}</span><span class="m">{t["about_min_short"].format(m=c["minutes"])}{tags}</span></a></li>')
        mins = {name: sum(C[self.index_of[s]]["minutes"] for s in slugs)
                for name, slugs in order.ROUTES.items()}
        body = INDEX_BODY[self.lang].format(
            site=t["site"], tagline=t["tagline"], total_min=total_min, n=self.count,
            investor_min=mins["investor"], builder_min=mins["builder"],
            investor_n=len(order.ROUTES["investor"]), builder_n=len(order.ROUTES["builder"]),
            first=C[0]["slug"], toc="".join(toc), built=BUILT, nfa=t["nfa"])
        body = self.resolve(body, "index")
        self.write("index.html", self.page("index", t["site"], t["start_here"], body, t["tagline"]))

    def build_ten(self):
        """Every chapter's claim and three lines on one page: the real ten minutes."""
        t, C = self.t, self.chapters
        blocks = []
        for key, slugs in order.PARTS:
            if self.part_label(key):
                blocks.append(f'<p class="tenpart">{self.part_label(key)}</p>')
            for slug in slugs:
                c, f = C[self.index_of[slug]], self.frame[slug]
                lis = "".join(f"<li>{line}</li>" for line in f["three"])
                blocks.append(f'<section class="ten"><h2><a href="{slug}.html"><span class="n">{self.label(slug)}</span> '
                              f'{escape(c["title"])}</a></h2><p class="tenclaim">{f["claim"]}</p><ol>{lis}</ol></section>')
        body = (f'<p class="crumb"><a href="index.html">{t["the_map"]}</a></p><h1>{t["ten_title"]}</h1>'
                f'<p class="lede">{t["ten_lede"]}</p>' + "".join(blocks)
                + f'<p class="foot">{t["foot_chapter"].format(site=t["site"], built=BUILT)} {t["nfa"]}</p>')
        body = self.resolve(body, "ten-minutes")
        self.write("ten-minutes.html", self.page("ten-minutes", t["ten_title"], t["ten_nav"], body, t["ten_lede"]))

    def build_redirects(self):
        """The old addresses: one line each, sending the reader on."""
        t = self.t
        for old, new in order.REDIRECTS.items():
            self.write(old + ".html", f"""<!DOCTYPE html>
<html lang="{t["html_lang"]}">
<head>
<meta charset="utf-8">
<title>{t["site"]}</title>
<meta http-equiv="refresh" content="0; url={new}.html">
<link rel="canonical" href="{new}.html">
</head>
<body>
<p>{t["moved"]} <a href="{new}.html">{t["moved_go"]} →</a></p>
</body>
</html>
""")

    def build_sources(self):
        t, C = self.t, self.chapters
        seen, first_seen = {}, []
        for i, c in enumerate(C):
            for label, url in c["sources"]:
                key = url if not url.startswith("repo:") else label
                if key not in seen:
                    seen[key] = (label, url, [])
                    first_seen.append(key)
                if c["slug"] in self.num and self.num[c["slug"]] not in seen[key][2]:
                    seen[key][2].append(self.num[c["slug"]])
        ext, repo = [], []
        for k in first_seen:
            label, url, chs = seen[k]
            chs_s = (t["chapter_n"].format(c=", ".join(str(n) for n in chs)) if chs
                     else t["the_prologue"])
            if url.startswith("repo:"):
                repo.append(f'<li>{escape(label)} <span class="how">— {escape(url[5:].strip())} ({chs_s})</span></li>')
            else:
                ext.append(f'<li>{escape(label)}<br><a href="{escape(url)}" rel="noopener">{escape(url)}</a> <span class="how">({chs_s})</span></li>')
        last = C[-1]
        pager = (f'<nav class="pager" aria-label="{t["pager_label_src"]}"><a class="prev" href="{last["slug"]}.html" rel="prev">'
                 f'<span class="lab">{t["prev"]} · {self.label(last["slug"])}</span>{escape(last["title"])}</a>'
                 f'<a class="next" href="index.html" rel="next"><span class="lab">{t["back_to"]}</span>{t["the_map"]}</a>'
                 f'<span class="keys" hidden>{t["keys"]}</span></nav>')
        body = SOURCES_BODY[self.lang].format(
            the_map=t["the_map"], appendix=t["appendix"], all_sources=t["all_sources"],
            ext="".join(ext), repo="".join(repo), repo_url=REPO_URL, pager=pager,
            site=t["site"], built=BUILT, nfa=t["nfa"])
        self.write("sources.html", self.page("sources", t["all_sources"], t["appendix"], body, t["sources_desc"]))

    def build(self):
        for i, c in enumerate(self.chapters):
            self.build_chapter(i, c)
        self.build_index()
        self.build_ten()
        self.build_sources()
        self.build_redirects()
        print(f"built the prologue + {self.count} chapters + index + ten minutes + sources "
              f"+ {len(order.REDIRECTS)} redirects ({self.lang}) into {self.out}")


INDEX_BODY = {
    "en": """
<p class="crumb">Start here</p>
<h1>{site}</h1>
<p class="lede">{tagline} A prologue and {n} short chapters, for a reader who has never heard of value investing and does not know what a scheduled job is. It sells nothing. The method in it was tested and mostly did not hold, and the book says so first. If you finish it you will not know what to buy; you will know what it takes to find out.</p>

<div id="continue" hidden></div>

<div class="routes">
<div class="route"><h2>Ten minutes</h2><p>One page: every chapter's claim in one sentence, and its three lines. Read that, then open the chapters you doubt.</p><a class="go" href="ten-minutes.html">The book in ten minutes</a></div>
<div class="route"><h2>The investor's route</h2><p>{investor_n} chapters on what the method is and whether it works: the problem, value, the screen, refusal, the inversion, writing the belief first, the decision, the shadow book and the tests. About {investor_min} minutes.</p><a class="go" href="prologue.html">Start the investor's route</a></div>
<div class="route"><h2>The builder's route</h2><p>{builder_n} chapters on how a tool is kept honest: what gets read, the three outcomes, the statuses, how the machine reads and watches, the bug museum and the limits. About {builder_min} minutes.</p><a class="go" href="prologue.html">Start the builder's route</a></div>
<div class="route"><h2>The whole thing</h2><p>The prologue and all {n} chapters in order. Part One is the method as it stands now, the tests are in the middle, Part Two is the machine. About {total_min} minutes, in sittings.</p><a class="go" href="{first}.html">Start at the prologue</a></div>
</div>

<h2>How every chapter is built</h2>
<p>The same six parts, in the same order. <strong>The claim</strong>, in one sentence. <strong>The story and the rule</strong>, with a made-up company called NAME A wherever arithmetic is needed. <strong>CENTA at this step</strong>: one real company, followed through the whole book. <strong>What the test said</strong>, where the rule was tested. <strong>Try it</strong>: one command you can run. <strong>In three lines</strong>: what to take away.</p>
<p>Every page has the full chapter list, a line saying where you are, and previous and next links that name the neighbouring chapters. On a chapter that belongs to a route, a third link says where that route goes next. The left and right arrow keys move between chapters. Each chapter has at most one level of fold: "the exact rule" and "where this comes from" open on demand and can be ignored. Numbered notes sit in the margin beside their sentence on a wide screen, and directly after the sentence on a phone. Nothing needs a network connection, and everything works with scripts off; a script only adds the arrow keys, the "continue" link, and the four figures you can move, in chapters [[n:07-reverse-dcf]], [[n:10-the-funnel]], [[n:12-shadow-book]] and [[n:tested]]. With scripts off, each of those still shows its figures.</p>

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
<ol class="toc">{toc}</ol>

<h2>Two made-up names, and one real one</h2>
<p>Every worked example uses NAME A, and occasionally NAME B, which are fictional companies with round numbers. One real company runs through the book: Central Garden &amp; Pet, ticker CENTA, which the owner bought and sold in October 2026. Its figures are from its own filings and his own trades, and it is an example with its mistakes left in, not a recommendation. Where another real fault is described, a company is named only where the project's public records already name it.</p>
<p class="foot">{site}. Built {built}. The research behind the design and the sources for every borrowed idea are in <a href="sources.html">All sources</a>. {nfa}</p>
""",
    "sv": """
<p class="crumb">Börja här</p>
<h1>{site}</h1>
<p class="lede">{tagline} En prolog och {n} korta kapitel, för en läsare som aldrig har hört talas om värdeinvestering och inte vet vad ett schemalagt jobb är. Den säljer ingenting. Metoden i den prövades och höll för det mesta inte, och boken säger det först. När du har läst klart vet du inte vad du ska köpa; du vet vad som krävs för att ta reda på det.</p>

<div id="continue" hidden></div>

<div class="routes">
<div class="route"><h2>Tio minuter</h2><p>En sida: varje kapitels påstående i en mening, och dess tre rader. Läs den, och öppna sedan de kapitel du tvivlar på.</p><a class="go" href="ten-minutes.html">Boken på tio minuter</a></div>
<div class="route"><h2>Investerarens väg</h2><p>{investor_n} kapitel om vad metoden är och om den fungerar: problemet, värde, screeningen, nejen, omvändningen, att skriva ned tron först, beslutet, skuggboken och testerna. Ungefär {investor_min} minuter.</p><a class="go" href="prologue.html">Börja investerarens väg</a></div>
<div class="route"><h2>Byggarens väg</h2><p>{builder_n} kapitel om hur ett verktyg hålls ärligt: vad som läses, de tre utfallen, statusarna, hur maskinen läser och vakar, buggmuseet och gränserna. Ungefär {builder_min} minuter.</p><a class="go" href="prologue.html">Börja byggarens väg</a></div>
<div class="route"><h2>Hela vägen</h2><p>Prologen och alla {n} kapitel i ordning. Del ett är metoden som den ser ut nu, testerna står i mitten, del två är maskinen. Ungefär {total_min} minuter, i flera omgångar.</p><a class="go" href="{first}.html">Börja med prologen</a></div>
</div>

<h2>Hur varje kapitel är byggt</h2>
<p>Samma sex delar, i samma ordning. <strong>Påståendet</strong>, i en mening. <strong>Berättelsen och regeln</strong>, med ett påhittat bolag som heter BOLAG A överallt där det behövs räkning. <strong>CENTA i det här steget</strong>: ett verkligt bolag, följt genom hela boken. <strong>Vad testet sade</strong>, där regeln testades. <strong>Prova själv</strong>: ett kommando du kan köra. <strong>På tre rader</strong>: vad du ska ta med dig.</p>
<p>Varje sida har hela kapitellistan, en rad som säger var du är, och länkar bakåt och framåt som namnger grannkapitlen. På ett kapitel som hör till en väg säger en tredje länk vart den vägen går härnäst. Vänster- och högerpilen flyttar mellan kapitel. Varje kapitel har högst en nivå av utfällbara rutor: "den exakta regeln" och "var det här kommer ifrån" öppnas när du vill och kan hoppas över. Numrerade fotnoter står i marginalen bredvid sin mening på en bred skärm, och direkt efter meningen på en telefon. Inget kräver nätuppkoppling, och allt fungerar utan skript; ett skript lägger bara till piltangenterna, "fortsätt"-länken och de fyra figurer du kan röra, i kapitel [[n:07-reverse-dcf]], [[n:10-the-funnel]], [[n:12-shadow-book]] och [[n:tested]]. Utan skript visar var och en av dem fortfarande sina siffror.</p>

<h2>Färgerna, och vad var och en betyder</h2>
<p>Fem betydelser, en färg var, likadana i varje figur, aldrig den enda signalen.</p>
<ul>
<li><span class="sw sw-value"></span><strong>Värde</strong>, blått: vad ett företag är värt, och ägarens uppskattning av det. Fyrkantiga markörer.</li>
<li><span class="sw sw-price"></span><strong>Pris</strong>, orange: vad marknaden noterar. Runda markörer.</li>
<li><span class="sw sw-pass"></span><strong>Godkänt</strong>, grönt: ett test klarades, en signal kom fram. Bock.</li>
<li><span class="sw sw-fail"></span><strong>Underkänt eller larm</strong>, cinnoberrött: ett test föll, ett stopp, en varning. Kryss.</li>
<li><span class="sw sw-miss"></span><strong>Saknas</strong>, streckat grått: kunde inte kontrolleras. Frågetecken.</li>
<li><span class="sw sw-owner"></span><strong>Ägaren</strong>, lila: ett mänskligt beslut.</li>
</ul>

<h2>Kapitlen</h2>
<ol class="toc">{toc}</ol>

<h2>Två påhittade namn, och ett verkligt</h2>
<p>Varje räkneexempel använder BOLAG A, och ibland BOLAG B, som är påhittade företag med jämna siffror. Ett verkligt bolag går genom boken: Central Garden &amp; Pet, ticker CENTA, som ägaren köpte och sålde i oktober 2026. Siffrorna kommer ur bolagets egna rapporter och hans egna affärer, och det är ett exempel med misstagen kvar, ingen rekommendation. Där ett annat verkligt fel beskrivs namnges ett bolag bara där projektets offentliga protokoll redan namnger det.</p>
<p class="foot">{site}. Byggd {built}. Forskningen bakom utformningen och källorna för varje lånad idé finns under <a href="sources.html">Alla källor</a>. {nfa}</p>
""",
}

SOURCES_BODY = {
    "en": """
<p class="crumb"><a href="index.html">{the_map}</a> · {appendix}</p>
<h1>{all_sources}</h1>
<p class="lede">Every borrowed idea with the place it was borrowed from, and every claim about the system with the file it was read from. Nothing in the method was invented here.</p>
<section class="sources">
<h2>Ideas and evidence outside the project</h2>
<ol>{ext}</ol>
<h2>Read from the repository</h2>
<p>These are files in the project's own repository, which is public at <a href="{repo_url}">{repo_url}</a>. They are named so that anyone can check each claim against the line it came from.</p>
<ol>{repo}</ol>
<h2>How the site itself was designed</h2>
<p>The choice of a chaptered site over a single page, the pattern used for each kind of content, the colour system and the accessibility checks are recorded with their sources and their costs in the file <code>RESEARCH-NOTES.md</code> that ships beside these pages.</p>
</section>
{pager}
<p class="foot">{site}. Built {built}. {nfa}</p>
""",
    "sv": """
<p class="crumb"><a href="index.html">{the_map}</a> · {appendix}</p>
<h1>{all_sources}</h1>
<p class="lede">Varje lånad idé med platsen den lånades från, och varje påstående om systemet med filen det lästes ur. Inget i metoden uppfanns här.</p>
<section class="sources">
<h2>Idéer och belägg utanför projektet</h2>
<ol>{ext}</ol>
<h2>Läst ur repot</h2>
<p>Det här är filer i projektets eget repo, som är publikt på <a href="{repo_url}">{repo_url}</a>. De namnges så att vem som helst kan kontrollera varje påstående mot raden det kom ifrån.</p>
<ol>{repo}</ol>
<h2>Hur själva sajten utformades</h2>
<p>Valet av en sajt i kapitel i stället för en enda sida, mönstret för varje typ av innehåll, färgsystemet och tillgänglighetskontrollerna är dokumenterade med sina källor och sina kostnader i filen <code>RESEARCH-NOTES.md</code> som ligger bredvid de här sidorna (på engelska).</p>
</section>
{pager}
<p class="foot">{site}. Byggd {built}. {nfa}</p>
""",
}


def chapters_for(lang):
    """The chapters in the book's order, for one language."""
    suffix = "" if lang == "en" else "_sv"
    for name in ("content1", "content2"):
        sys.modules.pop(name + suffix, None)
    c1 = importlib.import_module("content1" + suffix)   # registers the old 1-12
    importlib.import_module("content2" + suffix)        # ... and the old 13-24
    lib = {}
    for c in c1.CHAPTERS:
        slug = order.RENAMED.get(c["slug"], c["slug"])
        lib[slug] = dict(c, slug=slug)
    content3.register(lang, lib, c1, figures)
    missing = [s for s in order.ordered_slugs() if s not in lib or s not in frame.FRAME[lang]]
    if missing:
        raise SystemExit(f"{lang}: no chapter or no frame for {missing}")
    return [lib[s] for s in order.ordered_slugs()]


def main():
    Site("en", chapters_for("en"), ROOT_OUT, "", "sv/").build()
    if os.path.exists(os.path.join(HERE, "content1_sv.py")) and os.path.exists(os.path.join(HERE, "content2_sv.py")):
        Site("sv", chapters_for("sv"), os.path.join(ROOT_OUT, "sv"), "../", "../").build()
    else:
        print("Swedish content not present yet -- built English only")


if __name__ == "__main__":
    main()
