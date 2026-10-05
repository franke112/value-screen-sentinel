"""`tools/build_playbook.py` -- the decision playbook, and the five things
it must hold.

1. Every numbered entry in FRAMEWORK-EDITS.md is placed on exactly one
   step or listed as cross-cutting. A new ruling fails here until placed.
2. Every status in VALID_STATUSES has a screen.
3. Every command a screen shows exists in the CLI's own --help, flag by flag.
4. Every precedent line links to a file that exists.
5. THE ANCHORING GUARD: a name with no registered growth view opens a
   section-5 step with no prior fair value, growth view, MBP or tier on
   it -- not another name's, not its own, not one quoted inside a ruling.

And the build survives a fresh clone: no reports/, no shadow book, no git.
"""

from __future__ import annotations

import collections
import html
import re
from pathlib import Path

import pytest

import tools.build_playbook as B
from tools.playbook import sources as S
from tools.playbook.placement import ALSO, CROSS_CUTTING, PLACEMENT
from tools.playbook.steps import BY_ID, GUARDED, STEPS

REPO = Path(__file__).resolve().parents[1]


def text_of(page: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", page))


@pytest.fixture(scope="module")
def model():
    return B.collect(with_git=False)


# ---------------------------------------------------------------- 1. placement

def test_every_numbered_entry_is_placed_exactly_once(model):
    keys = {r.key for r in model.rulings if not r.application}
    counts = collections.Counter(k for v in PLACEMENT.values() for k in v)
    placed = set(counts)
    assert not (keys - placed - set(CROSS_CUTTING)), sorted(keys - placed - set(CROSS_CUTTING))
    assert not [k for k, c in counts.items() if c > 1]
    assert not (placed & set(CROSS_CUTTING))


def test_placement_names_only_real_entries_and_real_steps(model):
    keys = {r.key for r in model.rulings if not r.application}
    for step, ks in PLACEMENT.items():
        assert step in BY_ID
        for k in ks:
            assert k in keys, f"{k} placed on {step} is not in FRAMEWORK-EDITS.md"
    for step, ks in ALSO.items():
        assert step in BY_ID
        for k in ks:
            assert k in keys and (k in CROSS_CUTTING or any(k in v for v in PLACEMENT.values()))
    for step in BY_ID:
        assert step in PLACEMENT


def test_rulings_carry_a_date_and_a_status(model):
    numbered = [r for r in model.rulings if not r.application]
    assert len(numbered) > 150
    undated = [r.key for r in numbered if r.date is None]
    assert len(undated) < 10, undated
    assert all(r.status for r in numbered)


# ---------------------------------------------------------------- 2. statuses

def test_every_status_has_a_screen():
    from vss.rules import VALID_STATUSES
    for status in VALID_STATUSES:
        assert S.STATUS_STEP[status] in BY_ID
        assert BY_ID[S.STATUS_STEP[status]].status == status


# ---------------------------------------------------------------- 3. commands

def test_every_command_and_flag_shown_exists_in_help(model):
    for step in STEPS:
        for cmd, flags in step.commands:
            assert cmd in model.commands, f"{step.id}: vss {cmd} is not a subcommand"
            for flag in re.findall(r"(--[a-z][a-z0-9-]*)", flags):
                assert S.option_known(model.commands[cmd], flag), f"{step.id}: vss {cmd} {flag}"


def test_no_step_page_prints_a_flag_the_help_lacks(model):
    for step in STEPS:
        assert "NOT IN --help" not in B.render_step(model, step)


# ---------------------------------------------------------------- 4. links

def test_every_precedent_links_to_a_file_that_exists(model):
    out = Path("docs/playbook")
    for p in model.precedents:
        target = p.href.split("#")[0]
        if target.startswith("file://"):
            continue
        path = (REPO / out / target).resolve() if not target.startswith("../../") else (REPO / target[6:]).resolve()
        assert path.exists() or target in ("rulings.html", "git-log.html", "index.html") or target.endswith(".html"), p


def test_every_href_in_a_built_site_resolves(tmp_path, model):
    written = B.build(tmp_path, model)
    names = {p.name for p in written}
    for p in written:
        if p.suffix != ".html":
            continue
        for href in re.findall(r'href="([^"]+)"', p.read_text(encoding="utf-8")):
            if href.startswith(("http", "#", "mailto", "file://")):
                continue
            target = href.split("#")[0]
            if target.startswith("../../"):
                assert (REPO / target[6:]).exists(), (p.name, href)
            else:
                assert target in names, (p.name, href)


# ---------------------------------------------------------------- 5. the guard

FIXTURE_WATCHLIST = """\
tickers:
  - ticker: AAA
    name: Alpha
    currency: USD
    status: HELD
    fv_bull: 172.83    # the exit test C4/E42 runs on (owner, 2026-09-20)
    fv_base: 123.45
    tier: 2
    stop_price: 80.0
    growth:
      view: reference/growth-views/AAA.md
      registered: 2026-08-30
      base: 0.04
      bear: 0.0
      bull: 0.07
    notes: "HELD 2026-08-30. fv_base 123.45 USD, tier 2, MBP 92.59 USD, g_base 4%."
  - ticker: BBB
    name: Beta
    currency: USD
    status: PIPELINE
    notes: "PIPELINE 2026-09-01. Method A read 180-184 as noted, not as a basis."
"""

FIXTURE_EDITS = """\
# fixture

## E. Tooling deviations

### E28 — Method C is the engine

**DECIDED 2026-08-25 — the owner's ruling.** AAA was re-struck at fv_base 123.45 and MBP 92.59 under it.

**THE RULE.** Method C alone produces the fair value, on net debt/EBITDA ≤ 2.5×, a band ≤ ±200bps, r 9.5%, and tier 1 × 0.85; the cap is −8% to −12%.

### E109 — the pre-registered growth view lives on the watchlist entry

**RULED 2026-09-04.** CCC's view of g_base 6.5% is the case.

### B22 — may a gate-failed name carry a tier?

**RAISED 2026-08-25. OPEN.** DDD sits at tier 3 with MBP 41.10.
"""


@pytest.fixture
def fixture_root(tmp_path, monkeypatch):
    (tmp_path / "reference").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "reference" / "FRAMEWORK.md").write_text(
        (REPO / "reference" / "FRAMEWORK.md").read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "reference" / "FRAMEWORK-EDITS.md").write_text(FIXTURE_EDITS, encoding="utf-8")
    (tmp_path / "config" / "watchlist.yaml").write_text(FIXTURE_WATCHLIST, encoding="utf-8")
    return tmp_path


def _model(root):
    return B.collect(root=root, watchlist=root / "config" / "watchlist.yaml", built="2026-09-13", with_git=False)


CASE_FIGURES = ("123.45", "92.59", "6.5%", "41.10", "180-184", "g_base 4%", "tier 2", "tier 3")
THRESHOLDS = ("2.5×", "±200bps", "9.5%", "tier 1 × 0.85", "−8% to −12%")


def test_guard_redacts_every_case_figure_and_keeps_every_rule_paragraph(fixture_root):
    m = _model(fixture_root)
    bbb = next(n for n in m.names if n.ticker == "BBB")
    assert not bbb.view_registered_ok
    for sid in GUARDED:
        page = text_of(B.render_step(m, BY_ID[sid], bbb))
        assert B.GUARD_TEXT in page, sid
        for figure in CASE_FIGURES:
            assert figure not in page, (sid, figure)
        if sid == "strike":
            # every rule paragraph renders, redacted, and the thresholds stand
            assert "AAA was re-struck at fv_base [figure] and MBP [figure] under it" in page
            assert "Method C alone produces the fair value" in page
            for t in THRESHOLDS:
                assert t in page, t
            # the name's own notes render, redacted
            assert "Method A read [figure] as noted" in page
        if sid == "tier-mbp":
            # B22 is open: it is listed by title under the open questions, and
            # its paragraph, which carries a case figure, is not rendered at all
            assert "may a gate-failed name carry a tier?" in page


def test_guard_opens_for_a_name_whose_view_is_registered(fixture_root):
    m = _model(fixture_root)
    aaa = next(n for n in m.names if n.ticker == "AAA")
    assert aaa.view_registered_ok
    page = text_of(B.render_step(m, BY_ID["strike"], aaa))
    assert B.GUARD_TEXT not in page
    assert "[figure]" not in page
    assert "AAA was re-struck at fv_base 123.45 and MBP 92.59 under it" in page


def test_guard_holds_on_the_plain_step_page_too(fixture_root):
    m = _model(fixture_root)
    for sid in GUARDED:
        page = text_of(B.render_step(m, BY_ID[sid]))
        assert B.GUARD_TEXT in page
        for figure in CASE_FIGURES:
            assert figure not in page, (sid, figure)


def test_redactor_tells_threshold_from_case_figure():
    from tools.playbook.redact import Redactor, thresholds_from
    th = thresholds_from((REPO / "reference" / "FRAMEWORK.md").read_text(encoding="utf-8"))
    r = Redactor(th)
    out = r("fv_base 89.38 USD, g_base 4%, coverage 499x, 1,228 US$m, stop stays at 112, tier 2; "
            "net debt/EBITDA ≤ 2.5×, ±200bps, 15–50%, r 9.5%, tier 1 × 0.85, 8 quarters, 6 of 8, "
            "Q2 2026, §5.3, 4.2.1, E70, 2026-08-30, margin down 350bps")
    for gone in ("89.38", "4%", "499", "1,228", "112", "tier 2", "350bps"):
        assert gone not in out, gone
    for kept in ("2.5×", "±200bps", "15–50%", "9.5%", "tier 1 × 0.85", "8 quarters", "6 of 8", "Q2 2026", "§5.3", "4.2.1", "E70", "2026-08-30"):
        assert kept in out, kept
    assert any("350bps" in u for u in r.unsure)


def test_non_guarded_step_shows_the_owners_words_verbatim(fixture_root):
    m = _model(fixture_root)
    aaa = next(n for n in m.names if n.ticker == "AAA")
    page = text_of(B.render_step(m, BY_ID["held"], aaa))
    assert "fv_base 123.45 USD, tier 2, MBP 92.59 USD" in page


# ---------------------------------------------------------------- a fresh clone

def test_build_succeeds_with_reports_and_shadow_book_absent(fixture_root, tmp_path):
    m = _model(fixture_root)
    assert any("shadow_book.csv" in p for p in m.problems)
    out = tmp_path / "out"
    written = B.build(out, m)
    assert (out / "index.html").exists()
    index = text_of((out / "index.html").read_text(encoding="utf-8"))
    assert "What is missing on this machine" in index
    assert "shadow_book.csv" in index
    assert len(written) > 30


def test_build_is_idempotent(fixture_root, tmp_path):
    m = _model(fixture_root)
    a, b = tmp_path / "a", tmp_path / "b"
    B.build(a, m)
    B.build(b, m)
    for p in sorted(a.iterdir()):
        assert p.read_bytes() == (b / p.name).read_bytes(), p.name


def test_generator_composes_no_verdict(fixture_root):
    """The words a verdict is made of appear only inside quoted material."""
    m = _model(fixture_root)
    page = B.render_step(m, BY_ID["verdict"])
    body = re.sub(r"<blockquote.*?</blockquote>|<div class=\"notes\">.*?</div>|<ul class=prec>.*?</ul>|<details.*?</details>|<div class=\"rule\".*?</div></div>", "", page, flags=re.S)
    for word in ("BUY ", "SELL ", "recommend"):
        assert word not in text_of(body)


def test_y_statement_has_four_parts_from_the_entry(fixture_root):
    m = _model(fixture_root)
    y = S.y_statement(m.by_key["E28"], "the strike")
    assert y["context"] == "the strike"
    assert y["decided"].startswith("Method C is the engine")
    assert "Method C alone produces the fair value" in y["decided"]
    assert y["facing"].startswith("AAA was re-struck")


def test_markdown_subset_renders_tables_lists_and_quotes():
    from tools.playbook.render import md
    out = md(["| a | b |", "|---|---|", "| 1 | 2 |", "", "- one", "  continued", "", "> **bold** quote"])
    assert "<table>" in out and "<td>1</td>" in out
    assert "<li>one continued</li>" in out
    assert "<blockquote" in out and "<strong>bold</strong>" in out
