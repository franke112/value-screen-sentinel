#!/usr/bin/env python
"""Build docs/playbook/: the decision playbook, one HTML file per step.

    .venv/bin/python tools/build_playbook.py            # writes docs/playbook/
    .venv/bin/python tools/build_playbook.py --out DIR  # somewhere else

Idempotent: the same sources give the same bytes, the build date aside.
Reads FRAMEWORK.md, FRAMEWORK-EDITS.md, config/watchlist.yaml,
config/shadow_book.csv, reports/, reference/, the git log and the CLI's
own argparse help. Writes ONLY into the output directory. A missing
source is a sentence on the page, never a failed build.
"""

from __future__ import annotations

import argparse
import glob
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import date
from html import escape as esc
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from tools.playbook import sources as S  # noqa: E402
from tools.playbook import redact as X  # noqa: E402
from tools.playbook import render as R  # noqa: E402
from tools.playbook.placement import ALSO, CROSS_CUTTING, PLACEMENT, home_of  # noqa: E402
from tools.playbook.steps import (BY_ID, CHAIN, CYCLE, CYCLE_IDS, FUNNEL_ROWS,  # noqa: E402
                                  GUARDED, STEPS, Step, neighbours)

DEFAULT_OUT = ROOT / "docs" / "playbook"
GUARD_TEXT = "register your view first"


@dataclass
class Model:
    built: str
    sections: dict[str, S.Section]
    version: str | None
    rulings: list[S.Ruling]
    notes: list[str]
    names: list[S.Name]
    precedents: list[S.Precedent]
    commands: dict[str, S.Command]
    commits: list[S.Commit]
    ranked: list[str]
    ranked_from: str
    constants: dict
    problems: list[str] = field(default_factory=list)
    unplaced: list[Path] = field(default_factory=list)
    read_only: list[str] = field(default_factory=list)   # names the record knows, not on the watchlist
    redactor: X.Redactor = field(default_factory=lambda: X.Redactor(()))

    @property
    def by_key(self) -> dict[str, S.Ruling]:
        return {r.key: r for r in self.rulings if not r.application}

    def names_at(self, step_id: str) -> list[S.Name]:
        return [n for n in self.names if S.STATUS_STEP.get(n.status) == step_id]


def collect(*, root: Path = ROOT, watchlist: Path = S.WATCHLIST,
            built: str | None = None, with_git: bool = True) -> Model:
    problems: list[str] = []
    sections, p = S.framework_sections(root / "reference" / "FRAMEWORK.md"); problems += p
    names, p = S.watchlist_names(watchlist); problems += p
    shadow, p = S.precedents_from_shadow_book(root / "config" / "shadow_book.csv"); problems += p
    S.REPORTS = root / "reports"
    S.REFERENCE = root / "reference"
    on_list = {n.ticker for n in names}
    tickers = sorted(on_list | {x.ticker for x in shadow} | S.tickers_from_files())
    read_only = sorted(t for t in tickers if t not in on_list)
    rulings, notes, p = S.edits_rulings(root / "reference" / "FRAMEWORK-EDITS.md", tickers); problems += p
    commands, p = S.cli_commands(); problems += p
    commits: list[S.Commit] = []
    if with_git:
        commits, p = S.git_log(root); problems += p
    files, unplaced = S.precedents_from_files(tickers)
    reviews, p = S.precedents_from_reviews(root / "reference" / "reviews"); problems += p
    precedents = (S.precedents_from_names(names) + shadow + files + reviews
                  + S.precedents_from_git(commits, names, read_only))
    for r in rulings:
        step = home_of(r.key)
        for t in r.cases:
            precedents.append(S.Precedent(step or "cross-cutting", t, r.date, r.key,
                                          r.title, f"rulings.html#{anchor(r.key)}",
                                          "FRAMEWORK-EDITS case reference"))
    ranked, ranked_from = S.ranked_tonight(root / "reports")
    framework_text = "\n".join("\n".join(sec.lines) for sec in sections.values())
    redactor = X.Redactor(X.thresholds_from(framework_text))
    model = Model(built or date.today().isoformat(), sections, S.framework_version(root / "reference" / "FRAMEWORK.md"),
                 rulings, notes, names, precedents, commands, commits, ranked, ranked_from,
                 S.code_constants(), problems, unplaced, read_only)
    model.redactor = redactor
    return model


def _plain_title(r: S.Ruling) -> str:
    return re.sub(r"\*{1,2}", "", r.title)


def anchor(key: str) -> str:
    return "r-" + key.replace(".", "-")


def step_href(step_id: str) -> str:
    return f"{step_id}.html"


def name_href(ticker: str, step_id: str | None = None) -> str:
    base = "name-" + re.sub(r"[^A-Za-z0-9]+", "_", ticker)
    return base + (f"--{step_id}" if step_id else "") + ".html"


def name_steps(n: S.Name) -> list[str]:
    """The steps a name has its own page for: where it sits, and the seven
    guarded section-5 steps, which only open with a name."""
    cur = S.STATUS_STEP.get(n.status)
    return ([cur] if cur else []) + [g for g in GUARDED if g != cur]


def name_page_for(n: S.Name | None, step_id: str) -> str:
    """The name's own page for a step when one exists, else the plain step."""
    if n and step_id in name_steps(n):
        cur = S.STATUS_STEP.get(n.status)
        return name_href(n.ticker) if step_id == cur else name_href(n.ticker, step_id)
    return step_href(step_id)


def ruling_link(m: Model, key: str) -> str:
    home = home_of(key)
    r = m.by_key.get(key)
    title = esc(r.title) if r else "not in FRAMEWORK-EDITS"
    where = f' <span class="src">(placed on <a href="{step_href(home)}">{esc(BY_ID[home].title)}</a>)</span>' if home else ""
    return f'<a href="rulings.html#{anchor(key)}"><code>{esc(key)}</code></a> {title}{where}'


# ---------------------------------------------------------------- stepper

def stepper(m: Model, step: Step, name: S.Name | None = None) -> str:
    prev, nxt = neighbours(step.id)
    part = "the chain" if step.part == CHAIN else "the cycle"
    crumb = f'<span class="crumb"><a href="index.html">Map</a> › {part} › {esc(step.title)}'
    if name:
        crumb += f' › <b>{esc(name.ticker)}</b>'
    crumb += "</span>"
    a = ""
    if prev:
        a += f'<a class="prev" href="{name_page_for(name, prev)}" rel="prev">← {esc(BY_ID[prev].title)}</a>'
    a += f'<span class="cur">{esc(step.title)}</span>'
    if nxt:
        a += f'<a class="next" href="{name_page_for(name, nxt)}" rel="next">{esc(BY_ID[nxt].title)} →</a>'
    a += '<span class="keys" hidden>← → keys move between steps</span>'
    return f'<nav class="stepper" aria-label="Stepper">{crumb}{a}</nav>'


# ---------------------------------------------------------------- sections

def sec_where(m: Model, step: Step, name: S.Name | None) -> str:
    prev, nxt = neighbours(step.id)
    exits = ", ".join(f'<a href="{step_href(e)}">{esc(BY_ID[e].title)}</a>' for e in step.exits) or "none: the last step of its line"
    cells = [
        f'<div><b>previous</b>{("<a href=%s>%s</a>" % (step_href(prev), esc(BY_ID[prev].title))) if prev else "the map"}</div>',
        f'<div><b>next</b>{("<a href=%s>%s</a>" % (step_href(nxt), esc(BY_ID[nxt].title))) if nxt else "the map"}</div>',
        f'<div><b>exits from here</b>{exits}</div>',
        f'<div><b>who acts</b>{R.tag(step.actor, R.ACTOR_CLASS.get(step.actor, ""))}</div>',
    ]
    if step.status:
        cells.append(f'<div><b>watchlist status</b>{R.tag(step.status, "status")}</div>')
    here = m.names_at(step.id)
    if step.status:
        links = " ".join(f'<a href="{name_href(n.ticker)}">{esc(n.ticker)}</a>' for n in here) or "no name tonight"
        cells.append(f'<div><b>names here today</b>{links}</div>')
    if step.id == "screen":
        links = ", ".join(esc(t) for t in m.ranked) or f"none listed ({esc(m.ranked_from)})"
        cells.append(f'<div><b>ranked list tonight</b>{links} <span class="src">{esc(m.ranked_from)}</span></div>')
    if step.units:
        rows = [(u, w, d) for u, w, d in S.deploy_units(ROOT) if u in step.units]
        txt = "<br>".join(f"<code>{esc(u)}</code> {esc(w)} <span class=src>{esc(d)}</span>" for u, w, d in rows) or "deploy/ units not on disk"
        cells.append(f'<div><b>scheduled by</b>{txt}</div>')
    return '<div class="where">' + "".join(cells) + "</div>"


def sec_trigger(m: Model, step: Step) -> str:
    out = []
    prev, _ = neighbours(step.id)
    if step.status:
        try:
            from vss.overview import STATUS_MEANING
            meaning = STATUS_MEANING.get(step.status, "")
        except Exception:
            meaning = ""
        if meaning:
            out.append(f'<blockquote class="quote code">{esc(meaning)}</blockquote><p class="src">vss/overview.py, STATUS_MEANING</p>')
    if prev:
        out.append(f'<p>Reached from <a href="{step_href(prev)}">{esc(BY_ID[prev].title)}</a>.</p>')
    else:
        out.append("<p>The first step of its line.</p>")
    for key in step.sections[:1]:
        sec = m.sections.get(key)
        if sec:
            paras = [q for q in S._paragraphs(sec.lines) if not q.startswith(("|", "- ", "* "))]
            if paras:
                out.append(f'<blockquote class="quote fw">{R.inline(paras[0])}</blockquote><p class="src">FRAMEWORK.md {esc(sec.heading)}</p>')
    entering = [e for e in STEPS if step.id in e.exits]
    if entering:
        out.append("<p>Steps that send a name here: " + ", ".join(f'<a href="{step_href(e.id)}">{esc(e.title)}</a>' for e in entering) + ".</p>")
    return "".join(out)


_REFUSAL = re.compile(r"refus|NEVER|never|DATA MISSING|blocks|blocked|rejects", re.I)


def sec_do(m: Model, step: Step) -> str:
    items = []
    for mod in step.modules:
        doc = S.module_doc(mod)
        if doc:
            items.append(f'<li>What the code says it does:<blockquote class="quote code">{R.md(doc)}</blockquote><p class="src">vss/{esc(mod)}.py, module docstring</p></li>')
    for cmd_name, flags in step.commands:
        cmd = m.commands.get(cmd_name)
        if not cmd:
            items.append(f'<li class="missing">command <code>{esc(cmd_name)}</code> is not in the CLI\'s help</li>')
            continue
        line = f"python -m vss {cmd_name} {flags}".strip()
        opts = []
        for flag in re.findall(r"(--[a-z][a-z0-9-]*)", flags):
            text = next((h for k, h in cmd.options.items() if flag in k.split(", ")), None)
            opts.append(f'<div class="opt"><code>{esc(flag)}</code> {esc(text) if text is not None else "<b>NOT IN --help</b>"}</div>')
        refusal = [h for h in cmd.options.values() if _REFUSAL.search(h)]
        ref_html = ""
        if refusal or _REFUSAL.search(cmd.help):
            ref_html = "<details><summary>what refusal looks like, in the help's words</summary><ul>" + "".join(
                f"<li>{esc(h)}</li>" for h in ([cmd.help] if _REFUSAL.search(cmd.help) else []) + refusal[:6]) + "</ul></details>"
        items.append(f'<li>Run <pre>{esc(line)}</pre><p class="src">{esc(cmd.help)}</p>{"".join(opts)}{ref_html}</li>')
    if step.scripts:
        found = sorted(glob.glob(str(ROOT / "tools" / step.scripts)))
        if found:
            rows = []
            for f in found:
                p = Path(f)
                first = ""
                try:
                    for l in p.read_text(encoding="utf-8").splitlines()[:5]:
                        if l.strip() and not l.startswith("#!"):
                            first = l.strip().strip('"').strip("'"); break
                except OSError:
                    pass
                rows.append(f'<li><a href="{S.rel(p)}"><code>{esc(p.name)}</code></a> <span class="src">{esc(first)}</span></li>')
            items.append(f'<li>The strike itself is a dated script under <code>tools/</code>, one per name and day, run by a Claude session. Those on disk: <ul>{"".join(rows)}</ul></li>')
        else:
            items.append(f'<li class="missing">no <code>tools/{esc(step.scripts)}</code> on disk</li>')
    if step.files:
        items.append("<li>Files this step reads or writes: " + ", ".join(f"<code>{esc(f)}</code>" for f in step.files) + "</li>")
    if step.id == "growth-view":
        items.append('<li>Write <code>reference/growth-views/&lt;TICKER&gt;.md</code> with g_bear, g_base, g_bull and the reason for each, then the <code>growth:</code> block on the watchlist entry with its <code>registered</code> date (E109). The section-5 steps of this playbook stay closed until that date exists.</li>')
    if not items:
        items.append("<li>A reading, not a command: the framework text below names the document and the figures.</li>")
    fw = []
    for key in step.sections:
        sec = m.sections.get(key)
        if sec:
            fw.append(f"<details open><summary>FRAMEWORK.md {esc(sec.heading)}</summary>{R.md(sec.lines)}</details>")
        else:
            fw.append(f'<p class="missing">FRAMEWORK.md section {esc(key)} was not found</p>')
    return '<ol class="do">' + "".join(items) + "</ol>" + "".join(fw)


def rule_card(m: Model, r: S.Ruling, step: Step, guarded: bool = False) -> str:
    """One ruling as a Y-statement. With `guarded` every case figure in its
    four parts reads [figure]: an entry's paragraphs quote prior names' fair
    values, and on a section-5 step without a registered view none may show.
    The thresholds the rule states stay (tools/playbook/redact.py)."""
    ctx = step.title + ("" if not step.sections else f" ({m.sections[step.sections[0]].heading})" if step.sections[0] in m.sections else "")
    when = r.date.isoformat() if r.date else "undated"
    how = "" if r.date_how == "stated" else f" ({r.date_how})"
    tags = R.tag("superseded by " + ", ".join(r.superseded_by), "super") if r.superseded else (
        R.tag("settled", "settled") if r.settled else R.tag("open", "open"))
    y = S.y_statement(r, ctx)
    if guarded:
        # THE ANCHORING GUARD, AS REDACTION: the paragraphs stay readable and
        # every case figure in them is [figure]; thresholds the rule states stay.
        red = m.redactor
        y = {k: (red(v) if k != "accepting_how" else v) for k, v in y.items()}
    refs = []
    if r.closed_by:
        refs.append("closed by " + ", ".join(f'<a href="rulings.html#{anchor(k)}">{esc(k)}</a>' for k in r.closed_by))
    if r.amends:
        refs.append("amends " + ", ".join(f'<a href="rulings.html#{anchor(k)}">{esc(k)}</a>' for k in dict.fromkeys(r.amends)))
    if r.amended_by:
        refs.append("amended by " + ", ".join(f'<a href="rulings.html#{anchor(k)}">{esc(k)}</a>' for k in dict.fromkeys(r.amended_by)))
    if r.supersede_phrase:
        refs.append(f"its head says: {esc(r.supersede_phrase)}")
    if r.cases:
        refs.append("names " + ", ".join(esc(c) for c in r.cases))
    refs.append(f'status words in its opening lines: {esc(r.status)}')
    refs.append(f'<a href="{S.rel(S.EDITS)}">FRAMEWORK-EDITS.md</a> line {r.line}')
    return (f'<div class="rule" id="{anchor(r.key)}"><div class="head"><span class="key">{esc(r.key)}</span>'
            f'<span class="date">{esc(when)}{esc(how)}</span>{tags}</div>'
            f'<dl><dt>in the context of</dt><dd>{esc(y["context"])}</dd>'
            f'<dt>facing</dt><dd>{R.inline(y["facing"])}</dd>'
            f'<dt>we decided</dt><dd>{R.inline(y["decided"])}</dd>'
            f'<dt>accepting</dt><dd>{R.inline(y["accepting"])}{" <span class=src>(a sentence found by its cost word)</span>" if y["accepting_how"] == "keyword" else ""}</dd></dl>'
            f'<div class="refs">{" · ".join(refs)}</div></div>')


def sec_decide(m: Model, step: Step, name: S.Name | None) -> str:
    q = step.question
    if "{section}" in q:
        key = step.sections[0] if step.sections else ""
        q = q.replace("{section}", m.sections[key].heading if key in m.sections else key)
    who = name.ticker if name else "the name"
    out = [f"<p><strong>{esc(q)}</strong> <span class=src>({esc(who)})</span></p>"]
    placed = [m.by_key[k] for k in PLACEMENT[step.id] if k in m.by_key]
    missing = [k for k in PLACEMENT[step.id] if k not in m.by_key]
    live = [r for r in placed if not r.superseded]
    gone = [r for r in placed if r.superseded]
    g = guard_blocks(step, name)
    if g:
        out.append(f'<p class="guard">{GUARD_TEXT}</p><p class=src>Every case figure below — a price, fair value, MBP, tier, growth rate, multiple or stop — reads <code>{X.FIGURE}</code> until the current name\'s growth view is registered. The thresholds the rules state stay.</p>')
    if live:
        out += [rule_card(m, r, step, g) for r in live if r.settled]
    open_here = [r for r in live if not r.settled]
    if not live and not gone:
        out.append('<p class="missing">No numbered ruling is placed on this step. The framework text above is what governs it.</p>')
    if gone:
        out.append("<details><summary>superseded rulings that once bound this step (" + str(len(gone)) + ")</summary>" +
                   "".join(rule_card(m, r, step, g) for r in gone) + "</details>")
    if missing:
        out.append('<p class="missing">Placed here but not found in FRAMEWORK-EDITS.md: ' + ", ".join(esc(k) for k in missing) + "</p>")
    also = ALSO.get(step.id, ())
    if also:
        out.append("<p class=src>See also, placed elsewhere: " + "; ".join(ruling_link(m, k) for k in also) + "</p>")
    # applications (second application entries) of rulings placed here
    apps = [r for r in m.rulings if r.application and home_of(r.key) == step.id]
    if apps:
        red = m.redactor if g else (lambda t: t)
        out.append("<p class=src>Later applications recorded in FRAMEWORK-EDITS: " + "; ".join(
            f'<a href="rulings.html#{anchor(r.key)}-app">{esc(r.key)}</a> {esc(red(_plain_title(r)))}' for r in apps) + "</p>")
    # checklist: one box per settled rule and per command, in memory only
    boxes = [f"applied {r.key}: {r.title}" for r in live if r.settled]
    boxes += [f"ran: python -m vss {c} {f}".strip() for c, f in step.commands]
    if step.part == CHAIN:
        boxes.append("the decision is written in the owner's words, dated, on the watchlist row")
    out.append("<h3>Checklist (ticks live in this tab only; nothing is saved)</h3><ul class=check>" + "".join(
        f'<li><label><input type="checkbox"> <span>{esc(b)}</span></label></li>' for b in boxes) + "</ul>")
    return "".join(out), open_here


def guard_blocks(step: Step, name: S.Name | None) -> bool:
    """True when the anchoring guard hides prior valuations on this page."""
    return step.guarded and not (name and name.view_registered_ok)


def sec_precedents(m: Model, step: Step, name: S.Name | None) -> str:
    g = guard_blocks(step, name)
    red = m.redactor if g else (lambda t: t)
    rows = [p for p in m.precedents if p.step == step.id and (not name or p.ticker != name.ticker)]
    rows.sort(key=lambda p: (p.when or date.min, p.ticker), reverse=True)
    verdicts = [p for p in rows if p.source != "git log"]
    commits = [p for p in rows if p.source == "git log"]
    banner = (f'<p class="guard">{GUARD_TEXT}</p><p class=src>Prior names are listed; every case figure in a line reads <code>{X.FIGURE}</code>'
              + (f" because {esc(name.ticker)} has no registered growth view." if name else " because this step was opened without a name.") + "</p>") if g else ""
    if not rows:
        return f"<details><summary>how we decided before</summary>{banner}<p class=missing>no prior name reached this step in the record</p></details>"

    def ul(ps):
        return "<ul class=prec>" + "".join(
            f'<li><span class=t>{esc(p.ticker)}</span><span class=d>{esc(p.when.isoformat() if p.when else "undated")} · {esc(red(p.verdict))}</span>'
            f'<span><a href="{esc(p.href)}">{esc(red(p.line))}</a> <span class=src>{esc(p.source)}</span></span></li>' for p in ps) + "</ul>"
    inner = ul(verdicts) if verdicts else "<p class=missing>no verdict or record file for a prior name at this step</p>"
    if commits:
        inner += f"<details><summary>commits that touched this step ({len(commits)})</summary>{ul(commits)}</details>"
    return f"<details><summary>how we decided before ({len(verdicts)} verdicts or records, {len(commits)} commits)</summary>{banner}{inner}</details>"


def sec_open(m: Model, step: Step, open_here: list[S.Ruling]) -> str:
    if not open_here:
        return "<p class=src>No open question is recorded against this step.</p>"
    return "<ul>" + "".join(
        f'<li><a href="rulings.html#{anchor(r.key)}"><code>{esc(r.key)}</code></a> {esc(r.title)} <span class=src>{esc(r.date.isoformat() if r.date else "undated")}</span></li>'
        for r in open_here) + "</ul>"


def sec_name_history(m: Model, step: Step, name: S.Name) -> str:
    out = [f"<h2>{esc(name.ticker)} — {esc(name.name)}</h2>",
           f"<p>{R.tag(name.status, 'status')} {esc(name.currency)}"
           + (f" · growth view registered {name.view_registered.isoformat()}" if name.view_registered else " · no registered growth view")
           + (f" · catalyst {esc(str(name.catalyst_date))} {esc(name.catalyst_event or '')}" if name.catalyst_date else "") + "</p>"]
    g = guard_blocks(step, name)
    red = m.redactor if g else (lambda t: t)
    if g:
        out.append(f'<p class="guard">{GUARD_TEXT}</p><p class=src>On a section-5 step every case figure in the notes and the record reads <code>{X.FIGURE}</code> until this name\'s growth view is registered on the watchlist entry.</p>')
        out.append("<h3>The owner's notes, verbatim, figures redacted</h3>")
    else:
        out.append("<h3>The owner's notes, verbatim</h3>")
    out.append(f'<div class="notes">{esc(red(name.notes)) or "(empty)"}</div><p class=src><a href="{S.rel(S.WATCHLIST)}">config/watchlist.yaml</a></p>')
    own = [p for p in m.precedents if p.ticker == name.ticker]
    own.sort(key=lambda p: (p.when or date.min), reverse=True)
    if own:
        out.append("<h3>This name's path through the chain</h3><ul class=prec>" + "".join(
            f'<li><span class=t><a href="{step_href(p.step) if p.step in BY_ID else "rulings.html"}">{esc(BY_ID[p.step].title if p.step in BY_ID else p.step)}</a></span>'
            f'<span class=d>{esc(p.when.isoformat() if p.when else "undated")} · {esc(red(p.verdict))}</span>'
            f'<span><a href="{esc(p.href)}">{esc(red(p.line))}</a> <span class=src>{esc(p.source)}</span></span></li>' for p in own) + "</ul>")
    return "".join(out)


def render_step(m: Model, step: Step, name: S.Name | None = None) -> str:
    decide, open_here = sec_decide(m, step, name)
    body = [f"<h1>{esc(step.title)}" + (f" · {esc(name.ticker)}" if name else "") + "</h1>"]
    if name:
        cur = S.STATUS_STEP.get(name.status)
        sits = "sits at this step today" if step.id == cur else f"is {esc(name.status)} today; this is its own view of a section-5 step"
        nav = " · ".join(
            (f"<b>{esc(BY_ID[sid].title)}</b>" if sid == step.id else f'<a href="{name_page_for(name, sid)}">{esc(BY_ID[sid].title)}</a>')
            for sid in name_steps(name))
        body.append(f'<p class=lede>{esc(name.ticker)} {sits}. <a href="{step_href(step.id)}">The step without a name</a>.</p>'
                    f'<p class=src>{esc(name.ticker)} at: {nav}</p>')
    body += [
        '<h2><span class=n>1</span>Where you are</h2>', sec_where(m, step, name),
        '<h2><span class=n>2</span>Trigger</h2>', sec_trigger(m, step),
        '<h2><span class=n>3</span>Do</h2>', sec_do(m, step),
        '<h2><span class=n>4</span>Decide</h2>', decide,
        '<h2><span class=n>5</span>Precedents</h2>', sec_precedents(m, step, name),
        '<h2><span class=n>6</span>Open questions that bind this step</h2>', sec_open(m, step, open_here),
    ]
    if name:
        body.append(sec_name_history(m, step, name))
    slug = name_page_for(name, step.id)[:-5] if name else step.id
    return R.page(slug=slug, title=(f"{name.ticker} · " if name else "") + step.title, body="".join(body),
                  built=m.built, stepper=stepper(m, step, name), description=step.question)


# ---------------------------------------------------------------- index

def disagreements(m: Model) -> str:
    rows = []
    # 1. sequence
    fw_order = [m.sections[k].heading for k in ("§3", "§4", "§5", "§6") if k in m.sections]
    code_steps = []
    try:
        from vss import screen
        for l in (screen.__doc__ or "").splitlines():
            mm = re.match(r"\s*step (\d)\s+(.+?)\s{2,}", l + "  ")
            if mm:
                code_steps.append(f"step {mm.group(1)}: {mm.group(2).strip()}")
    except Exception:
        pass
    e2 = m.by_key.get("E2"); e44 = m.by_key.get("E44"); e45 = m.by_key.get("E45"); e5 = m.by_key.get("E5")
    rows.append("<li><b>Sequence.</b> FRAMEWORK.md runs " + " → ".join(esc(h) for h in fw_order) +
                ". The screener's own docstring runs: " + ("; ".join(esc(s) for s in code_steps) or "(docstring not read)") +
                ". Its filter 2 is " + (f"E44 ({esc(e44.title)})" if e44 else "E44") + " and " + (f"E45 ({esc(e45.title)})" if e45 else "E45") +
                " — a Gate 3 limb and a §4.2 hard kill applied BEFORE Gates 2, 4 and 5, which the code never scores; and it ranks on " +
                (f"E5/E6 ({esc(e5.title)})" if e5 else "E5/E6") + ", a key FRAMEWORK.md §3 does not contain. <b>Flagged, not picked.</b></li>")
    # 2. multipliers
    fw53 = m.sections.get("5.3")
    fw_mult = re.findall(r"× \*\*(0\.\d+)\*\*", "\n".join(fw53.lines)) if fw53 else []
    live = m.constants.get("mbp_live", {}); kept = m.constants.get("mbp_kept", {})
    readme = ""
    rp = ROOT / "README.md"
    if rp.exists():
        mm = re.search(r"tier 1 = (0\.\d+), tier 2 = (0\.\d+), tier 3 = (0\.\d+)", rp.read_text(encoding="utf-8"))
        readme = ", ".join(mm.groups()) if mm else ""
    same = [float(x) for x in fw_mult] == [live.get(1), live.get(2), live.get(3)]
    rows.append(f"<li><b>Tier multipliers.</b> FRAMEWORK.md §5.3 table: {esc(', '.join(fw_mult) or 'not found')}. "
                f"vss/rules.py MBP_TIER_CUSHION_E90 (the live definition): {esc(', '.join(str(v) for v in live.values()))}; "
                f"MBP_TIER_MULTIPLIER (kept for superseded figures): {esc(', '.join(str(v) for v in kept.values()))}. "
                + (f"README.md still prints {esc(readme)}. " if readme else "") +
                ("Framework and live code agree." if same else "<b>Framework and live code DISAGREE. Flagged, not picked.</b>") + "</li>")
    # 3. staleness
    s12 = m.sections.get("1.2")
    fw_stale = next((l for l in (s12.lines if s12 else []) if "Prices" in l), "")
    rows.append(f"<li><b>Staleness.</b> FRAMEWORK.md §1.2: {R.inline(fw_stale.lstrip('- ').strip()) or 'not found'}. "
                f"vss/rules.py MAX_CLOSE_AGE_TRADING_DAYS = {esc(str(m.constants.get('stale_days')))}. Both are shown; §1.2's own amendment names E47.</li>")
    # 4. statuses the framework never names
    fw_text = "\n".join("\n".join(s.lines) for s in m.sections.values())
    unnamed = [s for s in m.constants.get("statuses", ()) if s not in fw_text]
    rows.append("<li><b>Statuses.</b> vss/rules.py VALID_STATUSES: " + ", ".join(esc(s) for s in m.constants.get("statuses", ())) +
                ". Never named in FRAMEWORK.md's text: " + (", ".join(esc(s) for s in unnamed) or "none") +
                ". Their meaning comes from FRAMEWORK-EDITS (E27, E111, E12) and vss/overview.py STATUS_MEANING.</li>")
    return '<div class="disagree"><h3>Where FRAMEWORK.md and the code disagree</h3><ul>' + "".join(rows) + "</ul></div>"


def cell(m: Model, step: Step, cyc: bool = False) -> str:
    here = m.names_at(step.id)
    names = ""
    if step.status:
        names = '<div class="names">' + "".join(
            f'<a href="{name_href(n.ticker)}" class="{"g" if step.guarded and not n.view_registered_ok else ""}">{esc(n.ticker)}</a>' for n in here) + "</div>"
        names += f'<div class="cnt">{len(here)} name{"s" if len(here) != 1 else ""}</div>'
    elif step.id == "screen":
        names = f'<div class="cnt">{len(m.ranked)} ranked tonight ({esc(m.ranked_from)})</div>'
    if step.id == "intake" and m.read_only:
        names += '<div class="cnt">read, never entered: ' + ", ".join(esc(t) for t in m.read_only) + "</div>"
    n_rules = len([k for k in PLACEMENT[step.id] if k in m.by_key and not m.by_key[k].superseded])
    tags = R.tag(step.actor, R.ACTOR_CLASS.get(step.actor, ""))
    return (f'<div class="cell{" cyc" if cyc else ""}"><a class="s" href="{step_href(step.id)}">{esc(step.title)}</a>'
            f'{tags} <span class=cnt>{n_rules} ruling{"s" if n_rules != 1 else ""}</span>{names}</div>')


def render_index(m: Model) -> str:
    body = [f"<h1>The map</h1><p class=lede>The chain, top to bottom, with every name at its step. Click a step to open it; click a name to open the step it is at with its own history. FRAMEWORK.md {esc(m.version or '')}; {len([r for r in m.rulings if not r.application])} numbered entries in FRAMEWORK-EDITS.md; {len(m.names)} names on the watchlist.</p>"]
    body.append('<ol class="funnel">')
    for row in FUNNEL_ROWS:
        body.append('<li><div class="row">' + "".join(cell(m, BY_ID[s]) for s in row) + "</div></li>")
    body.append("</ol>")
    body.append("<h2>The cycle: nightly, daily, weekly</h2><ol class=funnel><li><div class=row>" +
                "".join(cell(m, BY_ID[s], True) for s in CYCLE_IDS) + "</div></li></ol>")
    body.append(disagreements(m))
    cc = [m.by_key[k] for k in CROSS_CUTTING if k in m.by_key]
    body.append("<h2>Cross-cutting rulings</h2><ul>" + "".join(
        f'<li><a href="rulings.html#{anchor(r.key)}"><code>{esc(r.key)}</code></a> {esc(r.title)}</li>' for r in cc) + "</ul>")
    if m.notes:
        body.append("<p class=src>Unnumbered notes in FRAMEWORK-EDITS: " + "; ".join(esc(n) for n in m.notes) + "</p>")
    if m.unplaced:
        body.append(f"<h2>Records the build could not place ({len(m.unplaced)})</h2><p class=src>Files under reports/ and reference/ that name no watchlist ticker, or a kind the placement table does not know. Listed, not hidden.</p><ul>" +
                    "".join(f'<li><a href="{S.rel(p)}">{esc(S._name(p))}</a></li>' for p in m.unplaced) + "</ul>")
    if m.problems:
        body.append("<h2>What is missing on this machine</h2><ul>" + "".join(f"<li class=missing>{esc(p)}</li>" for p in m.problems) + "</ul>")
    return R.page(slug="index", title="The map", body="".join(body), built=m.built,
                  description="The decision chain as navigation, with every name at its step.")


def render_rulings(m: Model) -> str:
    body = ["<h1>Every ruling, where it binds</h1><p class=lede>One card per numbered entry in FRAMEWORK-EDITS.md, as a Y-statement quoted from the entry's own labelled paragraphs. Superseded entries are struck through. Grouped by the step that carries them.</p>"]
    groups: dict[str, list[S.Ruling]] = {}
    for r in m.rulings:
        if r.application:
            continue
        groups.setdefault(home_of(r.key) or ("cross-cutting" if r.key in CROSS_CUTTING else "UNPLACED"), []).append(r)
    order = [s.id for s in STEPS] + ["cross-cutting", "UNPLACED"]
    for g in order:
        rs = groups.get(g)
        if not rs:
            continue
        title = BY_ID[g].title if g in BY_ID else g
        body.append(f'<h2 id="s-{esc(g)}">{esc(title)}' + (f' <a href="{step_href(g)}" class=src>open the step</a>' if g in BY_ID else "") + "</h2>")
        step = BY_ID.get(g) or Step(g, title, CHAIN)
        body += [rule_card(m, r, step) for r in rs]
    apps = [r for r in m.rulings if r.application]
    if apps:
        body.append("<h2>Later applications</h2>")
        for r in apps:
            body.append(f'<div class="rule" id="{anchor(r.key)}-app"><div class=head><span class=key>{esc(r.key)}</span><span class=date>{esc(r.date.isoformat() if r.date else "undated")}</span></div><p>{esc(r.title)}</p><div class=refs><a href="{S.rel(S.EDITS)}">FRAMEWORK-EDITS.md</a> line {r.line}</div></div>')
    return R.page(slug="rulings", title="Rulings", body="".join(body), built=m.built,
                  description="Every FRAMEWORK-EDITS entry as a Y-statement, grouped by the step it binds.")


def render_gitlog(m: Model) -> str:
    body = [f"<h1>The git log</h1><p class=lede>{len(m.commits)} commits, subjects only, newest first. Precedent lines that cite a commit link here.</p><ul>"]
    for c in m.commits:
        body.append(f'<li id="{esc(c.sha)}"><code>{esc(c.sha)}</code> <span class=src>{esc(c.when.isoformat() if c.when else "")}</span> {esc(c.subject)}</li>')
    body.append("</ul>")
    return R.page(slug="git-log", title="Git log", body="".join(body), built=m.built, description="The repository's commit subjects.")


# ---------------------------------------------------------------- build

def build(out: Path, m: Model) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = []

    def put(name: str, text: str) -> None:
        p = out / name
        p.write_text(text, encoding="utf-8")
        written.append(p)

    put("style.css", R.CSS)
    put("site.js", R.JS)
    put("index.html", render_index(m))
    put("rulings.html", render_rulings(m))
    put("git-log.html", render_gitlog(m))
    for step in STEPS:
        put(step_href(step.id), render_step(m, step))
    for n in m.names:
        for sid in name_steps(n):
            put(name_page_for(n, sid), render_step(m, BY_ID[sid], n))
    put("redactions.txt", "figures the guard redacted because it could not tell threshold from case figure\n"
        "(an integer percentage or a small multiple the framework never states, with no case word before it)\n\n"
        + "\n".join(dict.fromkeys(m.redactor.unsure)) + "\n")
    # remove stale pages from an earlier build
    keep = {p.name for p in written}
    for p in out.iterdir():
        if p.is_file() and p.suffix in (".html", ".css", ".js", ".txt") and p.name not in keep:
            p.unlink()
    return written


def summary(m: Model, written: list[Path]) -> str:
    lines = [f"playbook: {len(written)} files written",
             f"  rulings: {len([r for r in m.rulings if not r.application])} numbered, {len([r for r in m.rulings if r.application])} later applications",
             f"  precedents: {len(m.precedents)} placed, {len(m.unplaced)} files not placed",
             f"  names: {len(m.names)}; ranked tonight: {len(m.ranked)} ({m.ranked_from})",
             f"  guard: {m.redactor.count} figures redacted, {len(set(m.redactor.unsure))} of them unsure (docs/playbook/redactions.txt)"]
    for p in m.problems:
        lines.append(f"  MISSING: {p}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory (default: docs/playbook)")
    ap.add_argument("--watchlist", type=Path, default=S.WATCHLIST, help="an alternate watchlist")
    ap.add_argument("--no-git", action="store_true", help="do not read the git log")
    ap.add_argument("--built", default=None, help="the build date to print (default: today)")
    a = ap.parse_args(argv)
    m = collect(watchlist=a.watchlist, built=a.built, with_git=not a.no_git)
    written = build(a.out, m)
    print(summary(m, written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
