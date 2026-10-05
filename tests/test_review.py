"""`vss review` -- the review file, its refusals, the record, the playbook.

The five things held here: the schema round-trips and `config/review/
SCHEMA.md` is what the code prints; every refusal in SCHEMA.md refuses;
`--record` writes the note verbatim and nothing else; a review lands on
the playbook's step pages; and `.claude/commands/review.md` carries the
three clauses the code cannot enforce.
"""

from __future__ import annotations

import html
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from vss import review as V
from vss.config import load_watchlist

REPO = Path(__file__).resolve().parents[1]
DAY = "2026-09-13"
NOW = datetime(2026, 9, 13, 11, 0, 0).astimezone()
T = "2026-09-13T10:{:02d}:00+02:00"

WATCHLIST = """\
tickers:
  - ticker: AAA
    # a comment inside the block
    growth:
      base: 0.04
      bear: 0.0
      bull: 0.07
      view: reference/growth-views/AAA.md
      registered: 2026-08-30
    name: Alpha
    currency: USD
    status: PIPELINE
    fv_base: 123.45
    run_record: reference/run-records/AAA-2026-08-30.json
    notes: >-
      Screener 2026-08-26: rank 4 of 197. No fv_base, no tier and no mbp --
      section 5 has not been run. This entry is review work, not a buy.
  - ticker: BBB
    name: Beta
    currency: USD
    status: PIPELINE
    notes: "PIPELINE 2026-09-01."
  - ticker: CCC
    name: Gamma
    currency: USD
    status: HELD
    fv_bull: 70.0    # the exit test C4/E42 runs on (owner, 2026-09-20)
    fv_base: 50.0
    tier: 2
    stop_price: 40.0
    growth:
      view: reference/growth-views/CCC.md
      registered: 2026-08-30
      base: 0.03
      bear: 0.01
      bull: 0.05
    notes: "HELD 2026-08-30. fv_base 50.0 USD, tier 2, MBP 42.50 USD."
"""

VIEW_AAA = """\
# AAA — growth view
Set by the owner, 2026-08-30, pre-registered under FRAMEWORK-EDITS E28.

Base case FCF growth, 10 years: 4%
Bear: 0%
Bull: 7%

## The three rates, in the owner's words

**g_base 4%:** a steady business.
"""


def prepare_json(ticker: str, verification: list, stands: dict) -> str:
    import json
    return json.dumps({"ticker": ticker, "as_of": DAY, "status": "PIPELINE",
                       "verification": verification, "context": {"stands": stands}})


@pytest.fixture
def repo(tmp_path):
    for d in ("config", "reports/prepare", "reference/growth-views", "reference/reviews"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "config" / "watchlist.yaml").write_text(WATCHLIST, encoding="utf-8")
    (tmp_path / "reference" / "growth-views" / "AAA.md").write_text(VIEW_AAA, encoding="utf-8")
    (tmp_path / "reports" / "prepare" / f"AAA-{DAY}.json").write_text(prepare_json(
        "AAA", [{"order": 1, "field": "lease_liabilities", "period": "2026-Q2", "value": 62219.0,
                 "document": "interim", "page": "p.23", "status": "UNVERIFIED"}],
        {"fv_base": "fv_base 123.45 on the entry", "tier": "no tier", "resume_at": "tier-mbp"}))
    (tmp_path / "reports" / "prepare" / f"BBB-{DAY}.json").write_text(prepare_json(
        "BBB", [], {"fv_base": "no fv_base on the entry", "tier": "no tier", "resume_at": None}))
    (tmp_path / "reports" / "prepare" / f"CCC-{DAY}.json").write_text(prepare_json(
        "CCC", [], {"fv_base": "fv_base 50.0 on the entry", "tier": "tier 2", "resume_at": "verdict"}))
    return tmp_path


def step(sid, outcome="next", text="the owner's words", minute=0, **kw):
    d = {"step": sid, "outcome": outcome, "text": text, "answered_at": T.format(minute),
         "skipped": False, "skip_reason": None, "documents_opened": [], "rulings_cited": []}
    d.update(kw)
    return d


def skipped(sid, reason="resumed later"):
    return {"step": sid, "outcome": None, "text": "", "skipped": True, "skip_reason": reason,
            "documents_opened": [], "rulings_cited": []}


def full_review(ticker="BBB", status="PIPELINE", *, view_minute=11, **top):
    """Every step answered in order; the view registered at the growth-view step."""
    steps = []
    for i, sid in enumerate(V.steps_for(status)):
        if sid == "verdict":
            steps.append(step(sid, "watch-priced", "WATCH-PRICED, alert at MBP", minute=i))
        else:
            steps.append(step(sid, minute=i))
    doc = {"schema": V.SCHEMA_VERSION, "ticker": ticker, "date": DAY, "status_at_start": status,
           "prepare_report": f"reports/prepare/{ticker}-{DAY}.json", "steps": steps,
           "growth_view": {"base": 0.05, "bear": 0.01, "bull": 0.08,
                           "reasons": "a business growing with its market",
                           "registered_at": T.format(view_minute)},
           "note": "Reviewed 2026-09-13: WATCH-PRICED."}
    doc.update(top)
    return doc


def write(repo, doc, ticker=None, day=DAY):
    ticker = ticker or doc["ticker"]
    d = repo / "reference" / "reviews" / ticker
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{day}.yaml"
    p.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return p


def validate(repo, path):
    return V.validate(path, root=repo, watchlist_path=repo / "config" / "watchlist.yaml")


def refusals(repo, doc, **kw):
    v = validate(repo, write(repo, doc, **kw))
    return v.refusals


# ------------------------------------------------------------- 1. the schema

def test_a_full_pipeline_review_round_trips_and_validates(repo):
    doc = full_review()
    p = write(repo, doc)
    v = validate(repo, p)
    assert v.ok, v.refusals
    assert yaml.safe_load(p.read_text()) == yaml.safe_load(yaml.safe_dump(doc, sort_keys=False))
    assert [s["step"] for s in v.steps] == list(V.steps_for("PIPELINE"))
    assert "VALID" in v.report()


def test_schema_md_is_what_the_code_prints():
    on_disk = (REPO / "config" / "review" / "SCHEMA.md").read_text(encoding="utf-8")
    assert on_disk.rstrip("\n") == V.schema_markdown().rstrip("\n"), "regenerate: vss review --schema > config/review/SCHEMA.md"


def test_every_status_has_a_step_list_of_playbook_steps():
    from tools.playbook.steps import BY_ID, CHAIN_IDS
    from vss.rules import VALID_STATUSES
    for status in VALID_STATUSES:
        ids = V.steps_for(status)
        assert ids and all(i in BY_ID for i in ids)
        assert [CHAIN_IDS.index(i) for i in ids] == sorted(CHAIN_IDS.index(i) for i in ids), status
        assert ids[-1] == "verdict"
        for sid in ids:
            assert V.outcomes_for(sid)


def test_outcome_vocabulary_is_the_steps_exits():
    from tools.playbook.steps import BY_ID
    assert V.outcomes_for("gate-1") == ("next",) + BY_ID["gate-1"].exits
    assert V.outcomes_for("verdict") == BY_ID["verdict"].exits + ("held",)
    assert "next" not in V.outcomes_for("verdict")


def test_resumed_review_validates_with_earlier_steps_skipped(repo):
    ids = V.steps_for("PIPELINE")
    steps = [skipped(s, "resumed at tier-mbp: struck 2026-08-30") for s in ids[:ids.index("tier-mbp")]]
    steps += [step("tier-mbp", text="tier 2 on the reading", minute=1),
              step("verdict", "watch-priced", "WATCH-PRICED at fv_base 123.45", minute=2)]
    doc = full_review("AAA", steps=steps, started_at="tier-mbp",
                      resume_reason="already struck 2026-08-30; verdict not recorded",
                      growth_view={"base": 0.04, "bear": 0.0, "bull": 0.07,
                                   "reasons": "standing view of 2026-08-30, reference/growth-views/AAA.md",
                                   "registered_at": "2026-08-30T00:00:00+02:00"})
    v = validate(repo, write(repo, doc))
    assert v.ok, v.refusals


# ---------------------------------------------------------- 2. the refusals

def test_refuses_an_unknown_step_and_a_wrong_order(repo):
    doc = full_review()
    doc["steps"][3]["step"] = "gate-9"
    r = refusals(repo, doc)
    assert any("unknown step 'gate-9'" in x for x in r)
    assert any("in that order" in x for x in r)
    doc = full_review()
    doc["steps"][0], doc["steps"][1] = doc["steps"][1], doc["steps"][0]
    assert any("in that order" in x for x in refusals(repo, doc))
    doc = full_review()
    del doc["steps"][-1]
    assert any("in that order" in x for x in refusals(repo, doc))


def test_refuses_a_step_neither_answered_nor_skipped_with_a_reason(repo):
    doc = full_review()
    doc["steps"][2]["text"] = ""
    assert any("gate-3" in x and "text is empty" in x for x in refusals(repo, doc))
    doc = full_review()
    doc["steps"][2]["outcome"] = None
    assert any("gate-3" in x and "outcome is None" in x for x in refusals(repo, doc))
    doc = full_review()
    doc["steps"][2]["outcome"] = "maybe"
    assert any("gate-3" in x and "'maybe'" in x for x in refusals(repo, doc))
    doc = full_review()
    doc["steps"][2] = skipped("gate-3", reason="")
    assert any("gate-3" in x and "without a skip_reason" in x for x in refusals(repo, doc))
    doc = full_review()
    del doc["steps"][2]["answered_at"]
    assert any("gate-3" in x and "answered_at" in x for x in refusals(repo, doc))


def test_refuses_a_section_5_step_answered_with_the_view_absent_or_later(repo):
    doc = full_review(growth_view=None)
    r = refusals(repo, doc)
    for sid in V.VIEW_BOUND:
        assert any(sid in x and "growth_view absent" in x for x in r), sid
    assert not any("gate-1" in x for x in r)
    # the strike is answered at minute 12; a view registered at minute 13 is later
    doc = full_review(view_minute=13)
    r = refusals(repo, doc)
    assert any("(strike)" in x and "later" in x for x in r)
    assert any("(growth-view)" in x and "later" in x for x in r)
    assert not any("(verdict)" in x for x in r)     # answered at minute 14


def test_refuses_a_machine_figure_quoted_before_the_strike(repo):
    ids = V.steps_for("PIPELINE")
    doc = full_review("AAA")
    doc["steps"][ids.index("basis")]["text"] = "the basis is fine; fv_base 123.45 stands"
    r = refusals(repo, doc)
    assert any("(basis)" in x and "fv_base" in x and "'123.45'" in x and "before the strike" in x for x in r)
    # the same figure after the strike is the owner's to quote
    doc = full_review("AAA")
    doc["steps"][ids.index("verdict")]["text"] = "WATCH-PRICED against fv_base 123.45"
    assert not any("fv_base" in x for x in refusals(repo, doc))
    # in the reasons for the view, never
    doc = full_review("AAA")
    doc["growth_view"]["reasons"] = "backs out of 123.45"
    assert any("growth_view.reasons" in x and "fv_base" in x for x in refusals(repo, doc))
    # a HELD name's tier, mbp and stop are anchors too
    doc = full_review("CCC", "HELD")
    ids = V.steps_for("HELD")
    from vss.rules import compute_mbp
    doc["steps"][ids.index("flow")]["text"] = f"tier 2 still, stop at 40, mbp {compute_mbp(50.0, 2)}"
    r = refusals(repo, doc)
    assert any("(flow)" in x and "tier" in x for x in r)
    assert any("(flow)" in x and "stop_price" in x for x in r)
    assert any("(flow)" in x and "mbp" in x for x in r)


def test_refuses_a_verification_figure_the_report_did_not_list(repo):
    ids = V.steps_for("PIPELINE")
    doc = full_review("AAA")
    doc["steps"][ids.index("basis")]["verification"] = [
        {"field": "lease_liabilities", "period": "2026-Q2", "value": 62219.0, "outcome": "VERIFIED"}]
    assert not any("verification" in x for x in refusals(repo, doc))
    doc["steps"][ids.index("basis")]["verification"] = [
        {"field": "revenue", "period": "2026-Q2", "value": 1.0, "outcome": "VERIFIED"}]
    assert any("did not list" in x for x in refusals(repo, doc))
    doc["steps"][ids.index("basis")]["verification"] = [
        {"field": "lease_liabilities", "period": "2026-Q2", "value": 62000.0, "outcome": "VERIFIED"}]
    assert any("CORRECTED, not VERIFIED" in x for x in refusals(repo, doc))
    doc["steps"][ids.index("basis")]["verification"] = [
        {"field": "lease_liabilities", "period": "2026-Q2", "value": 62219.0, "outcome": "CORRECTED"}]
    assert any("without a corrected_value" in x for x in refusals(repo, doc))
    doc["steps"][ids.index("basis")]["verification"] = []
    doc["steps"][ids.index("flow")]["verification"] = [
        {"field": "lease_liabilities", "period": "2026-Q2", "value": 62219.0, "outcome": "VERIFIED"}]
    assert any("belongs on the basis step" in x for x in refusals(repo, doc))


def test_refuses_unknown_keys_anywhere(repo):
    doc = full_review(fv_base=99.0)
    assert any("unknown top-level key(s): fv_base" in x for x in refusals(repo, doc))
    doc = full_review()
    doc["steps"][0]["fair_value"] = 99.0
    assert any("(gate-1)" in x and "unknown key(s) fair_value" in x for x in refusals(repo, doc))
    doc = full_review()
    doc["growth_view"]["implied"] = 0.03
    assert any("growth_view has unknown key(s) implied" in x for x in refusals(repo, doc))


def test_refuses_a_missing_prepare_report_unless_waived(repo):
    doc = full_review(prepare_report=None)
    assert any("prepare_waived carries no words" in x for x in refusals(repo, doc))
    doc = full_review(prepare_report=None, prepare_waived="proceed without it -- the owner, 2026-09-13")
    v = validate(repo, write(repo, doc))
    assert v.ok and any("waived" in n for n in v.notices)
    doc = full_review(prepare_report="reports/prepare/BBB-2020-01-01.json")
    assert any("not on disk" in x for x in refusals(repo, doc))
    doc = full_review(prepare_report=f"reports/prepare/AAA-{DAY}.json")
    assert any("is for AAA, not BBB" in x for x in refusals(repo, doc))


def test_refuses_a_resume_without_reason_or_with_answers_before_it(repo):
    doc = full_review(started_at="strike")
    assert any("resume_reason says nothing" in x for x in refusals(repo, doc))
    doc = full_review(started_at="strike", resume_reason="struck already")
    assert any("started_at strike but" in x and "carry answers" in x for x in refusals(repo, doc))


def test_refuses_held_as_a_verdict_off_a_name_not_held(repo):
    doc = full_review()
    doc["steps"][-1]["outcome"] = "held"
    assert any("`held` is the verdict of a HELD name" in x for x in refusals(repo, doc))
    doc = full_review("CCC", "HELD")
    doc["steps"][-1]["outcome"] = "held"
    assert not any("held" in x for x in refusals(repo, doc))


def test_refuses_a_bad_growth_view(repo):
    doc = full_review()
    doc["growth_view"]["base"] = 5
    assert any("growth_view.base is 5, outside" in x for x in refusals(repo, doc))
    doc = full_review()
    doc["growth_view"]["bear"] = 0.09
    assert any("bear <= base <= bull" in x for x in refusals(repo, doc))
    doc = full_review()
    doc["growth_view"]["reasons"] = ""
    assert any("reasons is empty" in x for x in refusals(repo, doc))
    doc = full_review()
    doc["growth_view"]["base"] = "four percent"
    assert any("growth_view.base must be a number" in x for x in refusals(repo, doc))


def test_refuses_a_file_out_of_place(repo):
    doc = full_review()
    p = write(repo, doc, ticker="ZZZ")
    assert any("sits at ZZZ/" in x for x in validate(repo, p).refusals)


# ------------------------------------------------------------- 3. --record

NOTE = ('Reviewed 2026-09-13: WATCH-PRICED.\n'
        '  an indented line, with: a colon, # a hash, "quotes" and \'ticks\'\n'
        '\n'
        'after a blank line, trailing spaces   \n'
        '- a dash line\n'
        'key: value-looking text')


def record(repo, path, **kw):
    return V.record(path, root=repo, watchlist_path=repo / "config" / "watchlist.yaml",
                    views_dir=repo / "reference" / "growth-views", now=NOW, **kw)


def entries(repo):
    return load_watchlist(repo / "config" / "watchlist.yaml")


def test_record_appends_the_note_verbatim_and_nothing_else(repo):
    before = entries(repo)
    wl = repo / "config" / "watchlist.yaml"
    text_before = wl.read_text()
    p = write(repo, full_review("AAA", note=NOTE, growth_view={
        "base": 0.04, "bear": 0.0, "bull": 0.07, "reasons": "standing view",
        "registered_at": "2026-08-30T00:00:00+02:00"}))
    r = record(repo, p)
    assert r.note_appended and r.backup and r.backup.exists()
    assert r.backup.read_text() == text_before
    assert r.backup.name.startswith("watchlist.yaml.bak-2026-09-13-") and r.backup.name.endswith("-pre-review-aaa")
    assert r.view_written is None and not r.view_block_written and "unchanged" in r.view_kept
    after = entries(repo)
    a0 = next(e for e in before if e.ticker == "AAA")
    a1 = next(e for e in after if e.ticker == "AAA")
    assert a1.notes == a0.notes + "\n\n" + NOTE
    da, db = asdict(a1), asdict(a0)
    da.pop("notes"); db.pop("notes")
    assert da == db, "something other than notes moved on AAA"
    for b, a in zip(before, after):
        if b.ticker != "AAA":
            assert asdict(a) == asdict(b), b.ticker
    # the comment inside the block survives; the growth-views file is untouched
    assert "# a comment inside the block" in wl.read_text()
    assert (repo / "reference" / "growth-views" / "AAA.md").read_text() == VIEW_AAA
    # a second run writes nothing
    with pytest.raises(V.ReviewError, match="already recorded"):
        record(repo, p)
    assert entries(repo)[0].notes == a1.notes


def test_record_never_writes_status_fv_tier_mbp_or_stop(repo):
    p = write(repo, full_review("CCC", "HELD", note="Reviewed; still HELD.", growth_view={
        "base": 0.03, "bear": 0.01, "bull": 0.05, "reasons": "standing view",
        "registered_at": "2026-08-30T00:00:00+02:00"}))
    doc = yaml.safe_load(p.read_text()); doc["steps"][-1]["outcome"] = "dropped"
    doc["steps"][-1]["text"] = "DROPPED, in the owner's words"
    p.write_text(yaml.safe_dump(doc, sort_keys=False))
    before = next(e for e in entries(repo) if e.ticker == "CCC")
    record(repo, p)
    after = next(e for e in entries(repo) if e.ticker == "CCC")
    assert (after.status, after.fv_base, after.tier, after.stop_price) == \
        (before.status, before.fv_base, before.tier, before.stop_price) == ("HELD", 50.0, 2, 40.0)
    assert after.notes.endswith("Reviewed; still HELD.")


def test_record_registers_a_new_view_in_the_file_and_on_the_entry(repo):
    from vss.readiness import read_growth_view
    p = write(repo, full_review("BBB", note="Reviewed."))
    r = record(repo, p)
    assert r.view_written == repo / "reference" / "growth-views" / "BBB.md" and r.view_block_written
    e = next(x for x in entries(repo) if x.ticker == "BBB")
    assert (e.growth.base, e.growth.bear, e.growth.bull) == (0.05, 0.01, 0.08)
    assert e.growth.view == "reference/growth-views/BBB.md" and e.growth.registered.isoformat() == DAY
    v = read_growth_view("BBB", directory=repo / "reference" / "growth-views")
    assert (v.base, v.bear, v.bull) == (0.05, 0.01, 0.08)
    text = r.view_written.read_text()
    assert "a business growing with its market" in text and "## SUPERSEDED" not in text
    assert e.notes == "PIPELINE 2026-09-01.\n\nReviewed."
    assert e.status == "PIPELINE" and e.fv_base is None and e.tier is None


def test_record_supersedes_a_changed_view_and_the_reader_reads_the_new_rates(repo):
    from vss.readiness import read_growth_view
    p = write(repo, full_review("AAA", note="Reviewed; view changed."))
    r = record(repo, p)
    assert r.view_written and r.view_block_written
    text = r.view_written.read_text()
    assert text.index("Base case FCF growth, 10 years: 5%") < text.index("## SUPERSEDED")
    assert "**g_base 4%:** a steady business." in text         # the old file is kept, verbatim
    assert not re.search(r"^## (?!SUPERSEDED)", text.split("## SUPERSEDED")[1], re.M)
    v = read_growth_view("AAA", directory=repo / "reference" / "growth-views")
    assert v.state == "REGISTERED" or (v.base, v.bear, v.bull) == (0.05, 0.01, 0.08)
    assert (v.base, v.bear, v.bull) == (0.05, 0.01, 0.08)
    e = next(x for x in entries(repo) if x.ticker == "AAA")
    assert (e.growth.base, e.growth.bear, e.growth.bull) == (0.05, 0.01, 0.08)
    assert e.growth.registered.isoformat() == DAY and e.fv_base == 123.45
    backups = list((repo / "reference" / "growth-views").glob("AAA.md.bak-*"))
    assert len(backups) == 1 and backups[0].read_text() == VIEW_AAA


def test_record_dry_run_writes_nothing(repo):
    wl = repo / "config" / "watchlist.yaml"
    before = wl.read_bytes()
    p = write(repo, full_review("BBB", note="Reviewed."))
    r = record(repo, p, dry_run=True)
    assert r.backup is None and wl.read_bytes() == before
    assert not (repo / "reference" / "growth-views" / "BBB.md").exists()
    assert not list(repo.glob("config/watchlist.yaml.bak-*"))


def test_record_refuses_an_invalid_file_a_missing_entry_and_a_moved_status(repo):
    doc = full_review("BBB"); doc["steps"][0]["text"] = ""
    with pytest.raises(V.ReviewError, match="refusing to record"):
        record(repo, write(repo, doc))
    (repo / "reports" / "prepare" / f"DDD-{DAY}.json").write_text(prepare_json("DDD", [], {}))
    with pytest.raises(V.ReviewError, match="no watchlist entry"):
        record(repo, write(repo, full_review("DDD")))
    with pytest.raises(V.ReviewError, match="entry now reads PIPELINE"):
        record(repo, write(repo, full_review("BBB", "WATCH-GATED")))
    with pytest.raises(V.ReviewError, match="note is empty"):
        record(repo, write(repo, full_review("BBB", note="  ")))


def test_the_cli_wires_validate_record_and_schema(repo, capsys):
    from vss.__main__ import main
    p = write(repo, full_review("BBB", prepare_report=None, prepare_waived="proceed -- the owner"))
    assert main(["review", "--validate", str(p), "--config", str(repo / "config" / "watchlist.yaml")]) == 0
    assert "VALID" in capsys.readouterr().out
    assert main(["review", "--schema"]) == 0
    assert "## The steps a review walks" in capsys.readouterr().out


# ------------------------------------------------------------ 4. the playbook

def test_a_review_lands_on_the_playbook_step_pages(tmp_path):
    import tools.build_playbook as B
    from tools.playbook.steps import BY_ID
    from test_playbook import FIXTURE_EDITS, FIXTURE_WATCHLIST, text_of
    root = tmp_path
    (root / "reference" / "reviews" / "BBB").mkdir(parents=True)
    (root / "config").mkdir()
    (root / "reference" / "FRAMEWORK.md").write_text(
        (REPO / "reference" / "FRAMEWORK.md").read_text(encoding="utf-8"), encoding="utf-8")
    (root / "reference" / "FRAMEWORK-EDITS.md").write_text(FIXTURE_EDITS, encoding="utf-8")
    (root / "config" / "watchlist.yaml").write_text(FIXTURE_WATCHLIST, encoding="utf-8")
    doc = full_review("BBB")
    doc["steps"][0]["text"] = "Gate 1 passes: the drawdown is real and dated by the owner"
    doc["steps"][2] = skipped("gate-3", "nothing new since the intake")
    doc["growth_view"]["reasons"] = "a business growing with its market at 6.5%"
    (root / "reference" / "reviews" / "BBB" / f"{DAY}.yaml").write_text(
        yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    m = B.collect(root=root, watchlist=root / "config" / "watchlist.yaml", built=DAY, with_git=False)
    reviews = [p for p in m.precedents if p.source == "review session"]
    assert {p.step for p in reviews} == set(V.steps_for("PIPELINE")) - {"gate-3"}
    g1 = next(p for p in reviews if p.step == "gate-1")
    assert g1.ticker == "BBB" and g1.when.isoformat() == DAY and g1.verdict == "next"
    assert g1.line.startswith("Gate 1 passes")
    assert g1.href.endswith(f"reviews/BBB/{DAY}.yaml#gate-1")
    # the step page shows the owner's words; the guarded page redacts the figure
    page = text_of(B.render_step(m, BY_ID["gate-1"]))
    assert "Gate 1 passes: the drawdown is real and dated by the owner" in page
    guarded = text_of(B.render_step(m, BY_ID["growth-view"]))
    assert "a business growing with its market at [figure]" in guarded and "6.5%" not in guarded
    # the name page carries its path
    bbb = next(n for n in m.names if n.ticker == "BBB")
    own = text_of(B.render_step(m, BY_ID["verdict"], bbb))
    assert "WATCH-PRICED, alert at MBP" in own


def test_prepare_lists_the_reviews_a_name_has(repo):
    from vss.prepare import step_stands, Prepared  # noqa: F401 -- the module's own listing
    (repo / "reference" / "reviews" / "AAA").mkdir()
    (repo / "reference" / "reviews" / "AAA" / f"{DAY}.yaml").write_text("ticker: AAA\n")
    import vss.prepare as P
    src = Path(P.__file__).read_text(encoding="utf-8")
    assert 'glob("*.yaml")' in src and '(reviews_dir / entry.ticker)' in src


# ------------------------------------------------------------ 5. the command

def test_the_command_file_carries_the_three_clauses():
    text = (REPO / ".claude" / "commands" / "review.md").read_text(encoding="utf-8")
    assert "Never propose, draft, suggest or hint at a verdict, a tier, a fair" in text
    assert "This is the owner's step." in text
    assert "BEFORE any implied" in text and "registered_at" in text
    assert "Start where the name stands" in text and "resume at" in text.lower()
    assert "INCONSISTENT WITH E27" in text and "verdict" in text
    assert "Refuse to start without today's prepare report" in text
    assert "ONE STEP AT A TIME" in text
    assert "vss review --validate" in text and "vss review --record" in text
    assert "The owner runs it" in text
    for step_source in ("tools/playbook/steps.py", "tools/playbook/placement.py", "config/review/SCHEMA.md"):
        assert step_source in text
