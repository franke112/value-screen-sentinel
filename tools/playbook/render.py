"""HTML for the playbook. Plain files, relative links, no network.

Everything works with the script absent: the stepper is links, the folds
are <details>, the checklists are plain checkboxes that persist nowhere.
The script adds arrow-key navigation and nothing else.
"""

from __future__ import annotations

import re
from html import escape as esc

SITE = "The decision playbook"

CSS = """/* The decision playbook -- shares its palette with docs/the-method/style.css.
   Colour is meaning: value blue, price amber, pass green, fail orange,
   missing grey, owner mauve. */
:root {
  --paper:#FBFAF7; --ink:#1B1B1B; --muted:#5A5A5A; --rule:#C9C6BF; --surface:#F1EFE9;
  --value:#0072B2; --value-t:#005A8E; --value-f:#D1E6F1;
  --price:#E69F00; --price-t:#8A5A00; --price-f:#FAEED1;
  --pass:#009E73;  --pass-t:#00714F;  --pass-f:#D1EEE6;
  --fail:#D55E00;  --fail-t:#A34500;  --fail-f:#F7E2D1;
  --miss:#767676;  --miss-t:#5C5C5C;  --miss-f:#E6E6E6;
  --owner:#CC79A7; --owner-t:#8B4A70; --owner-f:#F6E7EF;
  --font:"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html{color-scheme:light}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--font);font-size:16px;line-height:1.5;-webkit-text-size-adjust:100%}
@media(min-width:1000px){body{font-size:17px}}
:focus-visible{outline:3px solid var(--value-t);outline-offset:2px}
.skip{position:absolute;left:8px;top:-60px;padding:10px 14px;background:var(--ink);color:var(--paper);z-index:10;text-decoration:none}
.skip:focus{top:8px}
a{color:var(--value-t)}
code,pre,kbd{font-family:var(--mono);font-size:.92em}
pre{background:var(--surface);border:1px solid var(--rule);padding:10px 12px;overflow-x:auto;margin:.4em 0}
.top{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px 16px;padding:8px 16px;border-bottom:1px solid var(--rule);background:var(--paper);position:sticky;top:0;z-index:5}
.top .brand{color:var(--ink);text-decoration:none;font-weight:600;min-height:44px;display:inline-flex;align-items:center}
.top .built{color:var(--muted);font-size:.85em}
.stepper{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:8px 16px;border-bottom:1px solid var(--rule);background:var(--surface)}
.stepper a,.stepper span.cur{min-height:44px;display:inline-flex;align-items:center;padding:0 12px;border:1px solid var(--rule);border-radius:6px;background:var(--paper);text-decoration:none;color:var(--ink)}
.stepper span.cur{background:var(--value-f);border-color:var(--value);font-weight:600}
.stepper .crumb{color:var(--muted);font-size:.9em;flex:1 1 100%}
.stepper .keys{margin-left:auto;color:var(--muted);font-size:.85em}
main{padding:16px;max-width:60em;margin:0 auto}
h1{font-size:1.55em;line-height:1.2;margin:.2em 0 .4em}
h2{font-size:1.15em;margin:1.4em 0 .4em;padding-top:.6em;border-top:1px solid var(--rule)}
h2 .n{display:inline-block;min-width:1.6em;color:var(--muted);font-weight:400}
h3{font-size:1em;margin:1em 0 .3em}
.lede{color:var(--muted);margin:0 0 .6em}
.tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:.8em;border:1px solid var(--rule);background:var(--surface);margin-right:4px;white-space:nowrap}
.tag.owner{background:var(--owner-f);border-color:var(--owner);color:var(--owner-t)}
.tag.session{background:var(--value-f);border-color:var(--value);color:var(--value-t)}
.tag.llm{background:var(--price-f);border-color:var(--price);color:var(--price-t)}
.tag.timer{background:var(--miss-f);border-color:var(--miss);color:var(--miss-t)}
.tag.open{background:var(--price-f);border-color:var(--price);color:var(--price-t)}
.tag.settled{background:var(--pass-f);border-color:var(--pass);color:var(--pass-t)}
.tag.super{background:var(--miss-f);color:var(--miss-t);text-decoration:line-through}
.tag.status{background:var(--value-f);border-color:var(--value);color:var(--value-t)}
.where{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(14em,1fr))}
.where div{border:1px solid var(--rule);background:var(--surface);padding:8px 12px;border-radius:6px}
.where b{display:block;color:var(--muted);font-weight:400;font-size:.85em}
.quote{border-left:4px solid var(--rule);padding:4px 12px;margin:.4em 0;background:var(--surface)}
.quote.fw{border-color:var(--value)}
.quote.code{border-color:var(--miss)}
.src{color:var(--muted);font-size:.85em}
ol.do>li{margin:.5em 0}
.opt{margin:.2em 0 .2em 1em;color:var(--muted);font-size:.92em}
.opt code{color:var(--ink)}
.rule{border:1px solid var(--rule);border-radius:6px;padding:8px 12px;margin:.6em 0;background:#fff}
.rule .head{display:flex;flex-wrap:wrap;gap:6px;align-items:baseline}
.rule .key{font-weight:700;font-family:var(--mono)}
.rule .date{color:var(--muted);font-size:.85em}
.rule dl{margin:.4em 0 0;display:grid;grid-template-columns:auto 1fr;gap:2px 10px}
.rule dt{color:var(--muted);font-size:.85em;text-transform:uppercase;letter-spacing:.03em}
.rule dd{margin:0}
.rule .refs{font-size:.85em;color:var(--muted);margin-top:.3em}
.check{list-style:none;padding:0;margin:.4em 0}
.check li{margin:.3em 0}
.check label{display:flex;gap:10px;align-items:flex-start;min-height:44px;padding:4px 0}
.check input{width:22px;height:22px;flex:none;margin-top:4px}
details{border:1px solid var(--rule);border-radius:6px;padding:6px 12px;margin:.6em 0;background:var(--surface)}
summary{cursor:pointer;min-height:36px;display:flex;align-items:center;font-weight:600}
.prec{list-style:none;padding:0;margin:.4em 0}
.prec li{padding:6px 0;border-top:1px solid var(--rule);display:grid;grid-template-columns:6.5em 7em 1fr;gap:6px 10px;align-items:baseline}
.prec li:first-child{border-top:0}
.prec .t{font-family:var(--mono);font-weight:600}
.prec .d{color:var(--muted);font-size:.85em}
@media(max-width:600px){.prec li{grid-template-columns:1fr}}
.guard{border:2px solid var(--owner);background:var(--owner-f);padding:10px 14px;border-radius:6px;font-weight:600}
.missing{border:1px dashed var(--miss);color:var(--miss-t);padding:8px 12px;border-radius:6px;background:var(--miss-f)}
.funnel{list-style:none;padding:0;margin:1em 0;counter-reset:s}
.funnel>li{position:relative;padding:0 0 18px 0}
.funnel>li::after{content:"";position:absolute;left:24px;bottom:2px;width:0;height:14px;border-left:2px solid var(--rule)}
.funnel>li:last-child::after{display:none}
.row{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(12em,1fr))}
.cell{border:1px solid var(--rule);border-radius:8px;background:#fff;padding:8px 12px;min-height:44px}
.cell.cyc{background:var(--surface)}
.cell a.s{font-weight:600;text-decoration:none;color:var(--ink);display:block;min-height:32px}
.cell .names{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.cell .names a{font-family:var(--mono);font-size:.85em;text-decoration:none;padding:2px 6px;border-radius:4px;background:var(--value-f);color:var(--value-t);min-height:28px;display:inline-flex;align-items:center}
.cell .names a.g{background:var(--owner-f);color:var(--owner-t)}
.cell .cnt{color:var(--muted);font-size:.85em}
.disagree{border:2px solid var(--fail);background:var(--fail-f);padding:8px 12px;border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:.95em}
th,td{text-align:left;padding:4px 8px;border-bottom:1px solid var(--rule);vertical-align:top}
.tablewrap{overflow-x:auto}
.foot{color:var(--muted);font-size:.85em;border-top:1px solid var(--rule);margin-top:2em;padding-top:8px}
.notes{white-space:pre-wrap;font-size:.95em}
"""

JS = """/* Progressive enhancement only: arrow keys move between steps. */
(function(){
  "use strict";
  var prev=document.querySelector('.stepper a.prev'), next=document.querySelector('.stepper a.next');
  document.addEventListener('keydown',function(ev){
    var t=ev.target, tag=t&&t.tagName?t.tagName.toLowerCase():'';
    if(tag==='input'||tag==='textarea'||tag==='select'||(t&&t.isContentEditable))return;
    if(ev.altKey||ev.ctrlKey||ev.metaKey||ev.shiftKey)return;
    if(ev.key==='ArrowRight'&&next){location.href=next.getAttribute('href');}
    if(ev.key==='ArrowLeft'&&prev){location.href=prev.getAttribute('href');}
  });
  var k=document.querySelector('.stepper .keys'); if(k)k.hidden=false;
})();
"""

_INLINE = [
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*(.+?)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"~~(.+?)~~"), r"<s>\1</s>"),
    (re.compile(r"(?<![\w*])\*([^*\n]+?)\*(?!\w)"), r"<em>\1</em>"),
]


def inline(text: str) -> str:
    out = esc(text)
    for pat, rep in _INLINE:
        out = pat.sub(rep, out)
    return out


def md(lines) -> str:
    """A small Markdown subset: paragraphs, lists, tables, quotes, headings."""
    if isinstance(lines, str):
        lines = lines.splitlines()
    html, para, inlist, intable, inquote = [], [], False, False, False

    def flush():
        nonlocal para
        if para:
            html.append("<p>" + inline(" ".join(para)) + "</p>")
            para = []

    def close():
        nonlocal inlist, intable, inquote
        flush()
        if inlist:
            html.append("</ul>"); inlist = False
        if intable:
            html.append("</table></div>"); intable = False
        if inquote:
            html.append("</blockquote>"); inquote = False

    for raw in lines:
        line = raw.rstrip()
        quoted = line.startswith(">")
        if quoted:
            if not inquote:
                close(); html.append('<blockquote class="quote fw">'); inquote = True
            line = line[1:]
            if line.startswith(" "):
                line = line[1:]
        elif inquote and line.strip() == "":
            close(); continue
        elif inquote:
            close()
        if line.strip() == "" or line.strip() == "---":
            flush()
            if inlist:
                html.append("</ul>"); inlist = False
            if intable:
                html.append("</table></div>"); intable = False
            continue
        if line.startswith("#"):
            flush(); level = min(len(line) - len(line.lstrip("#")), 4)
            html.append(f"<h{level + 1}>{inline(line.lstrip('#').strip())}</h{level + 1}>")
            continue
        if line.lstrip().startswith(("- ", "* ")) or re.match(r"^\s*\d+\.\s", line):
            flush()
            if not inlist:
                html.append("<ul>"); inlist = True
            html.append("<li>" + inline(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", line)) + "</li>")
            continue
        if line.startswith("|"):
            flush()
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            if not intable:
                html.append('<div class="tablewrap"><table>'); intable = True
                html.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>")
            else:
                html.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
            continue
        if inlist and line.startswith("  "):
            html[-1] = html[-1][:-5] + " " + inline(line.strip()) + "</li>"
            continue
        para.append(line.strip())
    close()
    return "\n".join(html)


def page(*, slug: str, title: str, body: str, built: str, stepper: str = "",
         description: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {SITE}</title>
<meta name="description" content="{esc(description)}">
<link rel="stylesheet" href="style.css">
</head>
<body data-page="{esc(slug)}">
<a class="skip" href="#main">Skip to content</a>
<header class="top">
<a class="brand" href="index.html">{SITE}</a>
<span class="built">built {esc(built)} · <a href="rulings.html">rulings</a> · <a href="git-log.html">git log</a></span>
</header>
{stepper}
<main id="main">
{body}
<p class="foot">Generated by <code>tools/build_playbook.py</code> from the repository's own files. Nothing on this page was written by the generator: verdicts are the owner's, quoted; rules are FRAMEWORK-EDITS entries, quoted; commands are the CLI's own help. Rebuild after any ruling, verdict or CLI change: <code>python tools/build_playbook.py</code>.</p>
</main>
<script src="site.js"></script>
</body>
</html>
"""


def tag(text: str, cls: str = "") -> str:
    return f'<span class="tag {cls}">{esc(text)}</span>'


ACTOR_CLASS = {"owner": "owner", "Claude session": "session",
               "LLM extraction": "llm", "timer": "timer"}
