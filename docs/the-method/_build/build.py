"""Build the site: one HTML file per chapter, an index, a sources page --
in English (docs/the-method/) and Swedish (docs/the-method/sv/).

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
import sys
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

BUILT = "2026-09-13"
REPO_URL = "https://github.com/franke112/value-screen-sentinel"

S = {
    "en": dict(
        html_lang="en",
        site="The slow way, made survivable",
        tagline="A value-investing method, and the machine that keeps it honest.",
        part1="Part One · The method", part2="Part Two · The machine",
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
                     "fictional; no company, price or holding appears on this site.",
        switch_label="Svenska", switch_lang="sv",
        sources_desc="Every source for the site, external and from the repository.",
    ),
    "sv": dict(
        html_lang="sv",
        site="Den långsamma vägen, gjord uthärdlig",
        tagline="En metod för värdeinvestering, och maskinen som håller den ärlig.",
        part1="Del ett · Metoden", part2="Del två · Maskinen",
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
                     "påhittade; inget bolag, ingen kurs och inget innehav förekommer på den här sajten.",
        switch_label="English", switch_lang="en",
        sources_desc="Varje källa för sajten, externa och ur repot.",
    ),
}


def part_of(i):
    return 1 if i < 12 else 2


class Site:
    def __init__(self, lang, chapters, out, asset_prefix, other_prefix):
        self.lang, self.t, self.chapters = lang, S[lang], chapters
        self.out, self.asset, self.other = out, asset_prefix, other_prefix

    # -- shared pieces ---------------------------------------------------
    def chapter_list(self, current=None):
        t, C = self.t, self.chapters
        items = ['<li class="home"><a href="index.html"%s><span class="n">&nbsp;</span>%s</a></li>'
                 % (' aria-current="page"' if current == "index" else "", t["start_map"])]
        for i, c in enumerate(C):
            if i == 0:
                items.append(f'<li class="part">{t["part1"]}</li>')
            if i == 12:
                items.append(f'<li class="part">{t["part2"]}</li>')
            cur = ' aria-current="page"' if c["slug"] == current else ""
            short = f'<span class="short">{t["short_tag"]}</span>' if c["short"] else ""
            items.append(f'<li><a href="{c["slug"]}.html"{cur}><span class="n">{i+1}</span><span>{escape(c["title"])}</span>{short}</a></li>')
        items.append(f'<li class="part">{t["appendix"]}</li>')
        items.append('<li><a href="sources.html"%s><span class="n">&nbsp;</span>%s</a></li>'
                     % (' aria-current="page"' if current == "sources" else "", t["all_sources"]))
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
<script src="site.js"></script>
</body>
</html>
"""

    def pager(self, i):
        t, C = self.t, self.chapters
        if i > 0:
            p = C[i - 1]
            prev_a = f'<a class="prev" href="{p["slug"]}.html" rel="prev"><span class="lab">{t["prev"]} · {i}</span>{escape(p["title"])}</a>'
        else:
            prev_a = f'<a class="prev" href="index.html" rel="prev"><span class="lab">{t["prev"]}</span>{t["start_map"]}</a>'
        if i < len(C) - 1:
            n = C[i + 1]
            next_a = f'<a class="next" href="{n["slug"]}.html" rel="next"><span class="lab">{t["next"]} · {i+2}</span>{escape(n["title"])}</a>'
        else:
            next_a = f'<a class="next" href="sources.html" rel="next"><span class="lab">{t["next"]}</span>{t["all_sources"]}</a>'
        short_a = ""
        if C[i]["short"]:
            later = [(j, c) for j, c in enumerate(C) if j > i and c["short"]]
            if later:
                j, c = later[0]
                short_a = f'<a class="short-next" href="{c["slug"]}.html"><span class="lab">{t["next_short"]} · {j+1}</span>{escape(c["title"])}</a>'
            else:
                short_a = f'<a class="short-next" href="index.html"><span class="lab">{t["end_short"]}</span>{t["back_map"]}</a>'
        return (f'<nav class="pager" aria-label="{t["pager_label"]}">{prev_a}{next_a}{short_a}'
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
    def build_chapter(self, i, c):
        t, n = self.t, len(self.chapters)
        partname = t["part1"] if part_of(i) == 1 else t["part2"]
        where = t["chapter_of"].format(i=i + 1, n=n)
        crumb = f'<p class="crumb"><a href="index.html">{t["the_map"]}</a> · {partname} · {where}</p>'
        route = t["on_route"] if c["short"] else ""
        lede = (f'<p class="lede">{escape(c["lede"])} <span class="time">'
                f'{t["about_min"].format(m=c["minutes"])}{route}.</span></p>')
        body = crumb + f"<h1>{escape(c['title'])}</h1>" + lede + c["body"] + self.sources_block(c) + self.pager(i)
        body += (f'<p class="foot">{t["foot_chapter"].format(site=t["site"], built=BUILT)} {t["nfa"]}</p>')
        self.write(c["slug"] + ".html", self.page(c["slug"], c["title"], where, body, c["lede"]))

    def build_index(self):
        t, C = self.t, self.chapters
        short = [c for c in C if c["short"]]
        short_min = sum(c["minutes"] for c in short)
        total_min = sum(c["minutes"] for c in C)
        toc = []
        for i, c in enumerate(C):
            if i == 0:
                toc.append(f'<li class="part">{t["part1"]}</li>')
            if i == 12:
                toc.append(f'<li class="part">{t["part2"]}</li>')
            route = f'<span class="short">{t["short_tag"]}</span>' if c["short"] else ""
            toc.append(f'<li><a href="{c["slug"]}.html"><span class="n">{i+1}</span><span class="t">{escape(c["title"])}</span>'
                       f'<span class="s">{escape(c["lede"])}</span><span class="m">{t["about_min_short"].format(m=c["minutes"])}{route}</span></a></li>')
        body = INDEX_BODY[self.lang].format(
            site=t["site"], tagline=t["tagline"], short_min=short_min, total_min=total_min,
            first_short=short[0]["slug"], first=C[0]["slug"], toc="".join(toc), built=BUILT,
            nfa=t["nfa"])
        self.write("index.html", self.page("index", t["site"], t["start_here"], body, t["tagline"]))

    def build_sources(self):
        t, C = self.t, self.chapters
        seen, order = {}, []
        for i, c in enumerate(C):
            for label, url in c["sources"]:
                key = url if not url.startswith("repo:") else label
                if key not in seen:
                    seen[key] = (label, url, [])
                    order.append(key)
                seen[key][2].append(i + 1)
        ext, repo = [], []
        for k in order:
            label, url, chs = seen[k]
            chs_s = t["chapter_n"].format(c=", ".join(str(n) for n in chs))
            if url.startswith("repo:"):
                repo.append(f'<li>{escape(label)} <span class="how">— {escape(url[5:].strip())} ({chs_s})</span></li>')
            else:
                ext.append(f'<li>{escape(label)}<br><a href="{escape(url)}" rel="noopener">{escape(url)}</a> <span class="how">({chs_s})</span></li>')
        last = C[-1]
        pager = (f'<nav class="pager" aria-label="{t["pager_label_src"]}"><a class="prev" href="{last["slug"]}.html" rel="prev">'
                 f'<span class="lab">{t["prev"]} · {len(C)}</span>{escape(last["title"])}</a>'
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
        self.build_sources()
        print(f"built {len(self.chapters)} chapters + index + sources ({self.lang}) into {self.out}")


INDEX_BODY = {
    "en": """
<p class="crumb">Start here</p>
<h1>{site}</h1>
<p class="lede">{tagline} Twenty-three short chapters in two parts, for a reader who has never heard of value investing and does not know what a scheduled job is. It sells nothing. If you finish it you will not know what to buy; you will know what it takes to find out.</p>

<div id="continue" hidden></div>

<div class="routes">
<div class="route"><h2>Ten minutes</h2><p>Seven chapters that carry the whole argument: the problem, what value is, the inversion, writing the belief first, why the machine cannot decide, the dead man's switch, and the close. About {short_min} minutes.</p><a class="go" href="{first_short}.html">Start the short route</a></div>
<div class="route"><h2>The whole thing</h2><p>All twenty-three chapters in order. Part One is the method; Part Two is the machine. About {total_min} minutes, in sittings. Each chapter says what it is about in its first line.</p><a class="go" href="{first}.html">Start at chapter 1</a></div>
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
<ol class="toc">{toc}</ol>

<h2>Two names</h2>
<p>Every worked example uses NAME A, and occasionally NAME B, which are fictional companies with round numbers. No real company, price, holding or address appears anywhere on this site; where a real defect is described, the name has been removed.</p>
<p class="foot">{site}. Built {built}. The research behind the design and the sources for every borrowed idea are in <a href="sources.html">All sources</a>. {nfa}</p>
""",
    "sv": """
<p class="crumb">Börja här</p>
<h1>{site}</h1>
<p class="lede">{tagline} Tjugotre korta kapitel i två delar, för en läsare som aldrig har hört talas om värdeinvestering och inte vet vad ett schemalagt jobb är. Den säljer ingenting. När du har läst klart vet du inte vad du ska köpa; du vet vad som krävs för att ta reda på det.</p>

<div id="continue" hidden></div>

<div class="routes">
<div class="route"><h2>Tio minuter</h2><p>Sju kapitel som bär hela resonemanget: problemet, vad värde är, omvändningen, att skriva ner tron först, varför maskinen inte kan bestämma, dödmansgreppet och avslutningen. Ungefär {short_min} minuter.</p><a class="go" href="{first_short}.html">Börja den korta vägen</a></div>
<div class="route"><h2>Hela vägen</h2><p>Alla tjugotre kapitel i ordning. Del ett är metoden; del två är maskinen. Ungefär {total_min} minuter, i flera omgångar. Varje kapitel säger vad det handlar om i sin första rad.</p><a class="go" href="{first}.html">Börja med kapitel 1</a></div>
</div>

<h2>Hur sajten är byggd för att läsas</h2>
<p>Varje sida har hela kapitellistan, en rad som säger var du är, och länkar bakåt och framåt som namnger grannkapitlen. Vänster- och högerpilen flyttar mellan kapitel. Varje kapitel har högst en nivå av utfällbara rutor: "den exakta regeln" och "var det här kommer ifrån" öppnas när du vill och kan hoppas över. Numrerade fotnoter står i marginalen bredvid sin mening på en bred skärm, och direkt efter meningen på en telefon. Inget kräver nätuppkoppling, och allt fungerar utan skript; ett skript lägger bara till piltangenterna, "fortsätt"-länken och en rörlig figur i kapitel 7.</p>

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

<h2>Två namn</h2>
<p>Varje räkneexempel använder BOLAG A, och ibland BOLAG B, som är påhittade företag med jämna siffror. Inget verkligt bolag, ingen kurs, inget innehav och ingen adress förekommer någonstans på sajten; där ett verkligt fel beskrivs har namnet tagits bort.</p>
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
    if lang == "en":
        import content1  # noqa: F401  (registers chapters 1-12)
        import content2  # noqa: F401  (registers chapters 13-23)
        return content1.CHAPTERS
    c1 = importlib.import_module("content1_sv")
    importlib.import_module("content2_sv")
    return c1.CHAPTERS


def main():
    Site("en", chapters_for("en"), ROOT_OUT, "", "sv/").build()
    if os.path.exists(os.path.join(HERE, "content1_sv.py")) and os.path.exists(os.path.join(HERE, "content2_sv.py")):
        Site("sv", chapters_for("sv"), os.path.join(ROOT_OUT, "sv"), "../", "../").build()
    else:
        print("Swedish content not present yet -- built English only")


if __name__ == "__main__":
    main()
